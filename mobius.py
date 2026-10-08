"""Möbius pings: the exact flow behind the frozen read law, and its group.

The frozen read law, theta -> arg(exp(i theta) + a exp(i phi)), agrees to first
order in a with the flow d theta/dt = sin(phi - theta). Run for time tau, that
flow is a Möbius transformation of the unit circle. Such maps form a
three-parameter group (PSU(1,1), equivalently PSL(2,R)), so any sequence of
these pings is one group element and the N - 3 cross-ratios of a population
never change (Watanabe & Strogatz 1993-94; Marvel, Mirollo & Strogatz 2009).

Everything here is deterministic and depends only on NumPy.
"""
from __future__ import annotations

import numpy as np


def wrap(angle):
    """Wrap to [-pi, pi), the convention of moving_target.wrapped_difference."""
    return (np.asarray(angle) + np.pi) % (2*np.pi) - np.pi


# ---------------------------------------------------------------------------
# Pulse laws
# ---------------------------------------------------------------------------

def pulse_matrix(phi, tau):
    """SU(1,1) matrix of the time-tau flow of d theta/dt = sin(phi - theta)."""
    if not np.isfinite(phi) or not np.isfinite(tau):
        raise ValueError('pulse phase and duration must be finite')
    c, s = np.cosh(tau/2), np.sinh(tau/2)
    return np.array([[c, np.exp(1j*phi)*s], [np.exp(-1j*phi)*s, c]], dtype=complex)


def act(matrix, theta):
    """Apply a circle Möbius map z -> (A z + B)/(C z + D) to phases."""
    z = np.exp(1j*np.asarray(theta, dtype=float))
    image = (matrix[0, 0]*z + matrix[0, 1])/(matrix[1, 0]*z + matrix[1, 1])
    return wrap(np.angle(image))


def mobius_pulse(theta, phi, tau):
    """Exact time-tau flow toward phase phi. Broadcasts theta against phi."""
    theta, phi = np.broadcast_arrays(np.asarray(theta, dtype=float), np.asarray(phi, dtype=float))
    if not np.all(np.isfinite(theta)) or not np.all(np.isfinite(phi)) or not np.isfinite(tau):
        raise ValueError('phases, pulse phase and duration must be finite')
    z = np.exp(1j*theta)
    c, s = np.cosh(tau/2), np.sinh(tau/2)
    image = (c*z + np.exp(1j*phi)*s)/(np.exp(-1j*phi)*s*z + c)
    return wrap(np.angle(image))


def frozen_pulse(theta, phi, amplitude):
    """The frozen MovingTarget2 read law for one pulse phase per row."""
    if not np.isfinite(amplitude) or abs(amplitude) >= 1:
        raise ValueError('pulse amplitude must be finite and |a| < 1')
    theta, phi = np.broadcast_arrays(np.asarray(theta, dtype=float), np.asarray(phi, dtype=float))
    return wrap(theta + np.angle(1 + amplitude*np.exp(1j*(phi - theta))))


def harmonic_pulse(theta, phi, tau, epsilon, substeps=64):
    """Time-tau RK4 flow of sin(phi - theta) + epsilon sin(2 (phi - theta)).

    epsilon = 0 is the Möbius flow up to RK4 roundoff. Any epsilon != 0 leaves
    the Möbius group.
    """
    if not isinstance(substeps, (int, np.integer)) or substeps < 1:
        raise ValueError('substeps must be a positive integer')
    theta, phi = np.broadcast_arrays(np.asarray(theta, dtype=float), np.asarray(phi, dtype=float))
    field = lambda x: np.sin(phi - x) + epsilon*np.sin(2*(phi - x))
    h = tau/substeps
    x = theta.copy()
    for _ in range(substeps):
        k1 = field(x)
        k2 = field(x + h*k1/2)
        k3 = field(x + h*k2/2)
        k4 = field(x + h*k3)
        x = x + h*(k1 + 2*k2 + 2*k3 + k4)/6
    return wrap(x)


def group_phases(wavevectors, query):
    """Pulse phase of every group for one 2-D query, phi_g = k_g . q."""
    return np.asarray(wavevectors, dtype=float) @ np.asarray(query, dtype=float)


def apply_mobius_ping(phases, wavevectors, query, tau):
    """Möbius counterpart of moving_target.apply_ping, one query port."""
    phases = np.asarray(phases, dtype=float)
    return mobius_pulse(phases, group_phases(wavevectors, query)[:, None], tau)


# ---------------------------------------------------------------------------
# Three-number group coordinates and the odometer
# ---------------------------------------------------------------------------

def to_coordinates(matrix):
    """Three real numbers for a group element: w = image of 0, psi = rotation.

    w = B / conj(A) lies in the unit disk and psi = 2 arg(A) is defined modulo
    2 pi, so the pair is independent of the matrix sign ambiguity.
    """
    alpha, beta = matrix[0, 0], matrix[0, 1]
    w = beta/np.conj(alpha)
    return np.array([w.real, w.imag, wrap(2*np.angle(alpha))])


def from_coordinates(coordinates):
    w = coordinates[0] + 1j*coordinates[1]
    if abs(w) >= 1:
        raise ValueError('group coordinate w must lie inside the unit disk')
    scale = 1/np.sqrt(1 - abs(w)**2)
    alpha = np.exp(0.5j*coordinates[2])*scale
    beta = w*np.conj(alpha)
    return np.array([[alpha, beta], [np.conj(beta), np.conj(alpha)]], dtype=complex)


class Odometer:
    """Per-group record of every Möbius ping, held as three real numbers.

    It needs the pulse phases and durations it applied, never the oscillator
    phases. Composing two group elements and rewriting the result as three
    numbers is the whole update.
    """

    def __init__(self, groups):
        self.coordinates = np.zeros((groups, 3))

    def record(self, phis, tau):
        phis = np.asarray(phis, dtype=float)
        if phis.shape != (len(self.coordinates),):
            raise ValueError('one pulse phase per group is required')
        for g, phi in enumerate(phis):
            current = from_coordinates(self.coordinates[g])
            self.coordinates[g] = to_coordinates(pulse_matrix(phi, tau) @ current)

    def inverse_matrices(self):
        return [np.linalg.inv(from_coordinates(c)) for c in self.coordinates]

    @property
    def real_scalars(self):
        return int(self.coordinates.size)


# ---------------------------------------------------------------------------
# Writing a group element as a few pulses
# ---------------------------------------------------------------------------

def _word(parameters):
    matrix = np.eye(2, dtype=complex)
    for k in range(0, len(parameters), 2):
        matrix = pulse_matrix(parameters[k], parameters[k+1]) @ matrix
    return matrix


def _word_residual_and_jacobian(parameters, target):
    pulses = [pulse_matrix(parameters[k], parameters[k+1]) for k in range(0, len(parameters), 2)]
    derivatives = []
    for k in range(0, len(parameters), 2):
        phi, tau = parameters[k], parameters[k+1]
        c, s = np.cosh(tau/2), np.sinh(tau/2)
        d_phi = np.array([[0, 1j*np.exp(1j*phi)*s], [-1j*np.exp(-1j*phi)*s, 0]])
        d_tau = 0.5*np.array([[s, np.exp(1j*phi)*c], [np.exp(-1j*phi)*c, s]])
        derivatives.append((d_phi, d_tau))
    n = len(pulses)
    prefix = [np.eye(2, dtype=complex)]      # P_k ... P_1
    for pulse in pulses:
        prefix.append(pulse @ prefix[-1])
    suffix = [np.eye(2, dtype=complex)]*(n+1)  # P_n ... P_{k+1}
    for k in range(n-1, -1, -1):
        suffix[k] = suffix[k+1] @ pulses[k]
    word = prefix[-1]
    alpha, beta = word[0, 0], word[0, 1]
    w, psi = beta/np.conj(alpha), 2*np.angle(alpha)
    t_w = target[0] + 1j*target[1]
    residual = np.array([(w - t_w).real, (w - t_w).imag, wrap(psi - target[2])])
    jacobian = np.empty((3, len(parameters)))
    for k in range(n):
        for j, derivative in enumerate(derivatives[k]):
            d_word = suffix[k+1] @ derivative @ prefix[k]
            d_alpha, d_beta = d_word[0, 0], d_word[0, 1]
            d_w = d_beta/np.conj(alpha) - beta*np.conj(d_alpha)/np.conj(alpha)**2
            jacobian[:, 2*k+j] = [d_w.real, d_w.imag, 2*np.imag(d_alpha/alpha)]
    return residual, jacobian


def _levenberg_marquardt(function, start, iterations=200, tolerance=1e-28):
    x = np.array(start, dtype=float)
    residual, jacobian = function(x)
    cost, damping = residual @ residual, 1e-3
    for _ in range(iterations):
        if cost < tolerance:
            break
        normal = jacobian.T @ jacobian
        gradient = jacobian.T @ residual
        improved = False
        while damping < 1e12:
            step = np.linalg.solve(normal + damping*(np.diag(np.diag(normal)) + 1e-12*np.eye(len(x))), -gradient)
            trial = x + step
            trial_residual, trial_jacobian = function(trial)
            trial_cost = trial_residual @ trial_residual
            if trial_cost < cost:
                x, residual, jacobian, cost = trial, trial_residual, trial_jacobian, trial_cost
                damping = max(damping/3, 1e-15)
                improved = True
                break
            damping *= 4
        if not improved:
            break
    return x, float(np.sqrt(cost))


def pulses_for(matrix, max_pulses=3, starts=40, seed=0, tolerance=1e-13):
    """Fewest pulses (phi, tau) whose composition equals a Möbius map.

    One pulse suffices only without rotation; two can carry a limited
    rotation; three reach the elements needed here. Returns the pulse list in
    application order and the coordinate residual.
    """
    target = to_coordinates(matrix)
    rng = np.random.default_rng(seed)
    w = target[0] + 1j*target[1]
    best = (None, np.inf)
    for count in range(1, max_pulses+1):
        for start in range(starts):
            if start == 0:
                guess = np.ravel([[np.angle(w) if abs(w) > 0 else 0., 2*np.arctanh(min(abs(w), .999))/count]
                                  for _ in range(count)])
            else:
                guess = np.ravel([[rng.uniform(-np.pi, np.pi), rng.normal(0, .5)] for _ in range(count)])
            x, error = _levenberg_marquardt(lambda p: _word_residual_and_jacobian(p, target), guess)
            if error < best[1]:
                best = (x, error)
            if error < tolerance:
                return [(float(x[k]), float(x[k+1])) for k in range(0, len(x), 2)], error
    x, error = best
    return [(float(x[k]), float(x[k+1])) for k in range(0, len(x), 2)], error


# ---------------------------------------------------------------------------
# The constellation: cross-ratios that Möbius pings cannot change
# ---------------------------------------------------------------------------

def cross_ratios(phases):
    """Per group, CR(z0, z1, z2, zj) for j >= 3: U - 3 real numbers per group."""
    phases = np.asarray(phases, dtype=float)
    if phases.ndim != 2 or phases.shape[1] < 4:
        raise ValueError('cross-ratios need a (groups, units >= 4) phase matrix')
    z = np.exp(1j*phases)
    z0, z1, z2, zj = z[:, :1], z[:, 1:2], z[:, 2:3], z[:, 3:]
    ratio = (z0 - z2)*(z1 - zj)/((z0 - zj)*(z1 - z2))
    return ratio.real, ratio.imag


def constellation_change(before, after):
    """|atan X' - atan X| per cross-ratio: bounded, scale-free, order preserving."""
    return np.abs(np.arctan(cross_ratios(after)[0]) - np.arctan(cross_ratios(before)[0]))


def halfway_identity_error(theta, phi, amplitude):
    """Frozen pulse versus the angular midpoint of the Möbius map with |c| = a."""
    frozen = wrap(frozen_pulse(theta, phi, amplitude) - theta)
    full = wrap(mobius_pulse(theta, phi, 2*np.arctanh(amplitude)) - theta)
    return np.abs(wrap(frozen - full/2))
