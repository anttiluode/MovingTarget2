"""Oscillator responses and controlled drift on a fixed first-moment surface.

The constrained drift is a synthetic intervention, not neuronal dynamics.
All query responses below assume unit radius and instantaneous relaxation.
"""
from __future__ import annotations

import numpy as np


def _matrix(value, name):
    array = np.asarray(value, dtype=float)
    if array.ndim != 2 or 0 in array.shape or not np.all(np.isfinite(array)):
        raise ValueError(f'{name} must be a nonempty finite matrix')
    return array


def _amplitude(amplitude):
    if not np.isfinite(amplitude) or abs(amplitude) >= 1:
        raise ValueError('pulse amplitude must be finite and |a| < 1')


def _order(order):
    if not isinstance(order, (int, np.integer)) or order < 1:
        raise ValueError('moment order must be a positive integer')


def _query_phases(wavevectors, queries):
    wavevectors = _matrix(wavevectors, 'wavevectors')
    queries = _matrix(queries, 'queries')
    if wavevectors.shape[1] != queries.shape[1]:
        raise ValueError('query and wavevector dimensions differ')
    return queries @ wavevectors.T


def wrapped_difference(first, second):
    """Signed shortest angular difference, in [-pi, pi)."""
    return (np.asarray(first) - np.asarray(second) + np.pi) % (2*np.pi) - np.pi


def exact_response(phases, wavevectors, queries, amplitude):
    """Mean unit phase advance after a simultaneous additive complex pulse."""
    _amplitude(amplitude)
    phases = _matrix(phases, 'phases')
    query_phases = _query_phases(wavevectors, queries)
    if query_phases.shape[1] != phases.shape[0]:
        raise ValueError('one query wavevector is required per phase group')
    relative = query_phases[:, :, None] - phases[None, :, :]
    return np.angle(1 + amplitude*np.exp(1j*relative)).mean(axis=(1, 2))


def apply_ping(phases, wavevectors, query, amplitude):
    """Perform a read; return the changed phases, never mutate the input."""
    _amplitude(amplitude)
    phases = _matrix(phases, 'phases')
    query_phases = _query_phases(wavevectors, np.asarray(query)[None, :])
    if query_phases.shape[1] != phases.shape[0]:
        raise ValueError('one query wavevector is required per phase group')
    relative = query_phases[0, :, None] - phases
    return (phases + np.angle(1 + amplitude*np.exp(1j*relative)) + np.pi) % (2*np.pi) - np.pi


def phase_moments(phases, order):
    """Group-wise mean exp(-i*l*theta), for l=1..order."""
    _order(order)
    phases = _matrix(phases, 'phases')
    harmonics = np.arange(1, order+1)
    return np.exp(-1j*phases[:, :, None]*harmonics).mean(axis=1)


def tail_bound(amplitude, order):
    """Uniform absolute error bound for the order-L phase-response series."""
    _amplitude(amplitude)
    _order(order)
    return abs(amplitude)**(order+1) / ((order+1)*(1-abs(amplitude)))


def response_features(wavevectors, queries, amplitude, order):
    """Linear map from real/imaginary moments to finite-pulse responses."""
    _amplitude(amplitude)
    _order(order)
    phi = _query_phases(wavevectors, queries)
    harmonics = np.arange(1, order+1)
    coefficients = (-1.)**(harmonics+1)*amplitude**harmonics/harmonics/phi.shape[1]
    angles = phi[:, :, None]*harmonics
    features = np.stack((np.sin(angles), np.cos(angles)), axis=-1)
    return (features*coefficients[None, None, :, None]).reshape(len(phi), -1)


def coded_response(code, wavevectors, queries, amplitude):
    code = np.asarray(code, dtype=complex)
    if code.ndim != 2 or 0 in code.shape or not np.all(np.isfinite(code)):
        raise ValueError('code must be a nonempty finite complex matrix')
    if np.asarray(wavevectors).shape[0] != code.shape[0]:
        raise ValueError('one query wavevector is required per moment group')
    coordinates = np.stack((code.real, code.imag), axis=-1).ravel()
    return response_features(wavevectors, queries, amplitude, code.shape[1]) @ coordinates


def fit_code(wavevectors, queries, answers, amplitude, order):
    """Fit from observed responses only. No hidden-state argument exists."""
    if amplitude == 0:
        raise ValueError('zero-amplitude calibration contains no information')
    features = response_features(wavevectors, queries, amplitude, order)/amplitude
    answers = np.asarray(answers, dtype=float)
    if answers.shape != (features.shape[0],) or not np.all(np.isfinite(answers)):
        raise ValueError('one finite answer is required per calibration query')
    coordinates, _, rank, _ = np.linalg.lstsq(features, answers/amplitude, rcond=None)
    if rank != features.shape[1]:
        raise ValueError('calibration feature matrix is rank deficient')
    pairs = coordinates.reshape(np.asarray(wavevectors).shape[0], order, 2)
    return pairs[:, :, 0] + 1j*pairs[:, :, 1]


def drift_step(phases, velocity, step=0.06):
    """Projected random motion followed by a first-moment-preserving retraction.

    Targets are recomputed from the current phases each call. Consequently a
    preceding read's damage is preserved, not silently repaired. A fully
    coherent group is a stationary boundary: its fixed unit-modulus mean
    permits no internal phase motion. Retraction halves a failed trial step,
    and raises if it cannot preserve the constraint.
    """
    phases = _matrix(phases, 'phases')
    velocity = _matrix(velocity, 'velocity')
    if velocity.shape != phases.shape or not np.isfinite(step) or step < 0:
        raise ValueError('velocity shape must match phases; step must be finite and nonnegative')
    result = phases.copy()
    for group, theta in enumerate(phases):
        target = np.array([np.cos(theta).mean(), np.sin(theta).mean()])
        rms = np.sqrt(np.mean(velocity[group]**2))
        if rms == 0 or step == 0 or np.linalg.norm(target) > 1-1e-12:
            continue
        jacobian = np.array([-np.sin(theta), np.cos(theta)])/len(theta)
        displacement = velocity[group]*step/rms
        displacement -= jacobian.T @ np.linalg.pinv(jacobian @ jacobian.T) @ (jacobian @ displacement)
        for shrink in range(10):
            candidate = theta + displacement/(2**shrink)
            for _ in range(30):
                residual = np.array([np.cos(candidate).mean(), np.sin(candidate).mean()])-target
                if np.linalg.norm(residual) < 2e-14:
                    break
                local = np.array([-np.sin(candidate), np.cos(candidate)])/len(theta)
                correction = local.T @ np.linalg.pinv(local @ local.T) @ residual
                candidate -= correction
            error = abs(np.mean(np.exp(1j*candidate)) - (target[0]+1j*target[1]))
            if error < 5e-14:
                result[group] = (candidate+np.pi) % (2*np.pi)-np.pi
                break
        else:
            raise RuntimeError('phase drift retraction did not preserve the first moment')
    return result
