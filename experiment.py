"""Frozen, deterministic MovingTarget2 experiment. Run with --help."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path
import platform

import numpy as np

from moving_target import (
    apply_ping, coded_response, drift_step, exact_response, fit_code,
    phase_moments, response_features, wrapped_difference,
)

ROOT = Path(__file__).resolve().parent
WAVEVECTORS = np.array([[1, 0], [0, 1], [1, 1], [1, -1], [2, 1], [1, 2]])
READ_QUERIES = np.array([[-.7, .9], [-.2, .4], [.3, -.1], [1.1, -.6]])


@dataclass(frozen=True)
class Config:
    seeds: tuple[int, ...] = tuple(range(4100, 4120))
    units_per_group: int = 16
    calibration_queries: int = 64
    held_out_queries: int = 512
    checkpoints: int = 16
    steps_per_checkpoint: int = 8
    phase_step: float = .06
    listener_noise_per_amplitude: float = .005
    amplitudes: tuple[float, ...] = (.05, .25, .6)
    orders: tuple[int, ...] = (1, 2, 4, 8)
    sequential_reads: int = 32
    sequential_drift_steps: int = 4


def _rng(seed, stream):
    return np.random.default_rng(np.random.SeedSequence([seed, stream]))


def _digest(array):
    return hashlib.sha256(np.asarray(array, dtype='<f8').tobytes()).hexdigest()


def calibration_data(seed, config):
    """Distinct streams prevent any held-out data dependence in calibration."""
    initial_rng = _rng(seed, 0)
    position = initial_rng.uniform(-np.pi, np.pi, 2)
    concentrations = initial_rng.uniform(.7, 2., len(WAVEVECTORS))
    phases = (WAVEVECTORS @ position)[:, None] + initial_rng.vonmises(
        0., concentrations[:, None], (len(WAVEVECTORS), config.units_per_group))
    phases = (phases+np.pi) % (2*np.pi)-np.pi
    queries = _rng(seed, 1).uniform(-np.pi, np.pi, (config.calibration_queries, 2))
    held_out = _rng(seed, 2).uniform(-np.pi, np.pi, (config.held_out_queries, 2))
    amplitude = config.amplitudes[0]
    clean = exact_response(phases, WAVEVECTORS, queries, amplitude)
    answers = clean + amplitude*config.listener_noise_per_amplitude*_rng(seed, 4).normal(size=len(queries))
    return {'phases': phases, 'queries': queries, 'held_out': held_out, 'answers': answers}


def _nrmse(predicted, actual, reference):
    denominator = float(np.sqrt(np.mean(np.asarray(reference)**2)))
    if denominator < 1e-14:
        raise ValueError('reference response lies at the numerical noise floor')
    return float(np.sqrt(np.mean((np.asarray(predicted)-actual)**2))/denominator)


def run_seed(seed, config):
    split = calibration_data(seed, config)
    initial, queries, held_out, answers = (split[key] for key in ['phases', 'queries', 'held_out', 'answers'])
    weak, _, strong = config.amplitudes
    fitted = fit_code(WAVEVECTORS, queries, answers, weak, 1)
    initial_code = phase_moments(initial, max(config.orders))
    references = {str(a): exact_response(initial, WAVEVECTORS, held_out, a) for a in config.amplitudes}
    frozen = {str(a): {str(order): coded_response(initial_code[:, :order], WAVEVECTORS, held_out, a)
                       for order in config.orders} for a in config.amplitudes}
    fit_prediction = coded_response(fitted, WAVEVECTORS, held_out, weak)
    distances = wrapped_difference(held_out[:, None, :], queries[None, :, :])
    table_prediction = answers[np.argmin(np.sum(distances**2, axis=-1), axis=1)]
    state, unrestricted = initial.copy(), initial.copy()
    drift_rng = _rng(seed, 3)
    trajectory, max_moment_error = [], 0.
    for checkpoint in range(config.checkpoints+1):
        if checkpoint:
            for _ in range(config.steps_per_checkpoint):
                velocity = drift_rng.normal(size=state.shape)
                state = drift_step(state, velocity, config.phase_step)
                unrestricted = (unrestricted + config.phase_step*velocity/
                                np.sqrt(np.mean(velocity**2, axis=1))[:, None]+np.pi) % (2*np.pi)-np.pi
        current_code = phase_moments(state, max(config.orders))
        moment_error = float(np.max(abs(current_code[:, 0]-initial_code[:, 0])))
        max_moment_error = max(max_moment_error, moment_error)
        at_amplitude = {}
        for amplitude in config.amplitudes:
            key = str(amplitude)
            actual = exact_response(state, WAVEVECTORS, held_out, amplitude)
            unguarded = exact_response(unrestricted, WAVEVECTORS, held_out, amplitude)
            reference = references[key]
            at_amplitude[key] = {
                'response_change': _nrmse(actual, reference, reference),
                'unrestricted_response_change': _nrmse(unguarded, reference, reference),
                'frozen_exact_code_error': {
                    str(order): _nrmse(frozen[key][str(order)], actual, reference)
                    for order in config.orders},
                'current_exact_code_error': {
                    str(order): _nrmse(coded_response(current_code[:, :order], WAVEVECTORS,
                                                    held_out, amplitude), actual, reference)
                    for order in config.orders},
            }
        actual_weak = exact_response(state, WAVEVECTORS, held_out, weak)
        trajectory.append({
            'step': checkpoint*config.steps_per_checkpoint,
            'phase_rms': float(np.sqrt(np.mean(wrapped_difference(state, initial)**2))),
            'first_moment_error': moment_error,
            'fitted_code_error': _nrmse(fit_prediction, actual_weak, references[str(weak)]),
            'at_amplitude': at_amplitude,
        })
    shuffled = _rng(seed, 5).permutation(initial.ravel()).reshape(initial.shape)
    shuffled_response = exact_response(shuffled, WAVEVECTORS, held_out, weak)
    # These are real state updates: no copies of old phases are reinstated.
    sequential = {name: initial.copy() for name in ['no_read', 'read_only', 'flip']}
    sequential_rng = _rng(seed, 6)
    sequential_trajectory = []
    for read in range(config.sequential_reads):
        query = READ_QUERIES[read % len(READ_QUERIES)]
        sequential['read_only'] = apply_ping(sequential['read_only'], WAVEVECTORS, query, weak)
        sequential['flip'] = apply_ping(sequential['flip'], WAVEVECTORS, query, weak)
        sequential['flip'] = apply_ping(sequential['flip'], WAVEVECTORS, query, -weak)
        for _ in range(config.sequential_drift_steps):
            velocity = sequential_rng.normal(size=initial.shape)
            for name in sequential:
                sequential[name] = drift_step(sequential[name], velocity, config.phase_step)
        sequential_trajectory.append({
            'read': read+1,
            **{name: _nrmse(exact_response(theta, WAVEVECTORS, held_out, weak),
                           references[str(weak)], references[str(weak)])
               for name, theta in sequential.items()},
        })
    final, weak_final, strong_final = trajectory[-1], trajectory[-1]['at_amplitude'][str(weak)], trajectory[-1]['at_amplitude'][str(strong)]
    final_weak = exact_response(state, WAVEVECTORS, held_out, weak)
    metrics = {
        'phase_rms': final['phase_rms'], 'first_moment_max_error': max_moment_error,
        'weak_response_change': weak_final['response_change'],
        'strong_response_change': strong_final['response_change'],
        'unrestricted_weak_response_change': weak_final['unrestricted_response_change'],
        'fitted_weak_code_nrmse': final['fitted_code_error'],
        'fitted_weak_initial_nrmse': trajectory[0]['fitted_code_error'],
        'table_weak_code_nrmse': _nrmse(table_prediction, final_weak, references[str(weak)]),
        'zero_weak_code_nrmse': _nrmse(np.zeros_like(final_weak), final_weak, references[str(weak)]),
        'strong_current_order1_nrmse': strong_final['current_exact_code_error']['1'],
        'strong_current_order4_nrmse': strong_final['current_exact_code_error']['4'],
        'strong_frozen_order8_nrmse': strong_final['frozen_exact_code_error']['8'],
        'shuffle_weak_response_change': _nrmse(shuffled_response, references[str(weak)], references[str(weak)]),
        **{f'{name}_response_change': sequential_trajectory[-1][name] for name in sequential},
    }
    return {
        'seed': seed, 'metrics': metrics, 'trajectory': trajectory,
        'sequential_trajectory': sequential_trajectory,
        'split': {
            'calibration_queries': len(queries), 'held_out_queries': len(held_out),
            'calibration_query_sha256': _digest(queries), 'held_out_query_sha256': _digest(held_out),
            'calibration_design_condition': float(np.linalg.cond(response_features(WAVEVECTORS, queries, weak, 1))),
        },
        'access': {'fit_hidden_phase_coordinates': 0, 'fit_held_out_answers': 0,
                   'calibration_reset_copies': len(queries), 'listener': 'software mean of per-unit phase advances'},
        'calibration_queries': queries.tolist(), 'calibration_answers': answers.tolist(),
        'fitted_code_real': fitted.real.tolist(), 'fitted_code_imag': fitted.imag.tolist(),
        'initial_phases': initial.tolist(), 'final_phases': state.tolist(),
    }


def _costs(config):
    phases = len(WAVEVECTORS)*config.units_per_group
    code = len(WAVEVECTORS)*2
    return {
        'object_code_real_scalars': code, 'object_code_float64_bytes': code*8,
        'physical_phase_real_scalars': phases, 'physical_phase_float64_bytes': phases*8,
        'per_object_scalar_ratio': phases/code,
        'shared_wavevector_int64_scalars': int(WAVEVECTORS.size),
        'shared_wavevector_int64_bytes': int(WAVEVECTORS.nbytes),
        'calibration_queries': config.calibration_queries,
        'calibration_queries_and_answers_float64_bytes': config.calibration_queries*3*8,
        'query_table_float64_bytes': config.calibration_queries*3*8,
        'calibration_design_float64_bytes': config.calibration_queries*code*8,
        'calibration_reset_snapshot_float64_bytes': phases*8,
        'calibration_least_squares_work_scaling': 'O(P K^2), P=calibration queries, K=12',
        'calibration_noise_only': True,
        'held_out_targets': 'noiseless analytic phase responses',
        'weak_code_terms_per_query': len(WAVEVECTORS),
        'exact_phase_terms_per_query': phases,
        'higher_order_real_scalars': {str(order): code*order for order in config.orders},
        'restore_pulses_per_query': 1,
        'drift_constraint_values_real_scalars': code,
        'drift_controller_allocations': {
            'result_state_float64_bytes': phases*8,
            'velocity_float64_bytes': phases*8,
            'group_jacobian_float64_bytes': config.units_per_group*2*8,
            'group_local_jacobian_float64_bytes': config.units_per_group*2*8,
            'group_vector_float64_bytes': config.units_per_group*8,
            'additional_workspace': 'multiple group vectors, residuals and NumPy/linalg temporaries',
            'is_total_peak_memory': False,
        },
        'physical_state_removed': False,
    }


def run_experiment(config=Config()):
    seeds = [run_seed(seed, config) for seed in config.seeds]
    summaries = {}
    for metric in seeds[0]['metrics']:
        values = np.array([run['metrics'][metric] for run in seeds])
        q25, median, q75 = np.quantile(values, [.25, .5, .75])
        summaries[metric] = {'median': float(median), 'q25': float(q25), 'q75': float(q75),
                             'min': float(values.min()), 'max': float(values.max())}
    median = lambda key: summaries[key]['median']
    gates = {}
    if config == Config():
        gates = {
            'H1_coordinates_move_moment_preserved': median('phase_rms') >= .35 and
                summaries['first_moment_max_error']['max'] < 1e-8,
            'H2_fitted_12_number_code': median('fitted_weak_code_nrmse') <= .06 and
                sum(run['metrics']['fitted_weak_code_nrmse'] <= .08 for run in seeds) >= 15,
            'H3_strong_probes_break_weak_equivalence': median('strong_response_change') >=
                2*median('weak_response_change') and median('strong_current_order4_nrmse') <=
                median('strong_current_order1_nrmse')/3,
            'H4_semantic_group_assignment_matters': median('shuffle_weak_response_change') >= .4 and
                median('shuffle_weak_response_change') >= 5*median('weak_response_change'),
            'H5_sign_flip_reduces_repeated_read_damage': median('flip_response_change') <=
                median('read_only_response_change')/2,
        }
    files = ['PROTOCOL.md', 'moving_target.py', 'experiment.py']
    return {
        'schema': 1, 'config': asdict(config), 'wavevectors': WAVEVECTORS.tolist(),
        'sequential_queries': READ_QUERIES.tolist(),
        'source_sha256': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files},
        'environment': {'python': platform.python_version(), 'numpy': np.__version__},
        'evaluation_status': 'full_frozen_evaluation' if config == Config() else 'partial_run_no_gate_claims',
        'summary': summaries, 'gates': gates, 'costs': _costs(config), 'seeds': seeds,
    }


def make_figure(receipt, destination):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matplotlib.rcParams['svg.hashsalt'] = 'MovingTarget2'
    colors = ['#136f63', '#cd532e', '#525fb5']
    figure, axes = plt.subplots(1, 3, figsize=(13.5, 3.8), constrained_layout=True)
    runs = receipt['seeds']
    steps = [row['step'] for row in runs[0]['trajectory']]
    for amplitude, color in zip(receipt['config']['amplitudes'], colors):
        values = np.array([[row['at_amplitude'][str(amplitude)]['response_change'] for row in run['trajectory']] for run in runs])
        low, mid, high = np.quantile(values, [.25, .5, .75], axis=0)
        axes[0].plot(steps, mid, color=color, label=f'a={amplitude}')
        axes[0].fill_between(steps, low, high, color=color, alpha=.15)
    axes[0].set(xlabel='Constrained drift steps', ylabel='Response change (NRMSE)', title='Weak answers survive internal motion')
    orders = receipt['config']['orders']
    for code_type, color, label in [('frozen_exact_code_error', colors[1], 'Code frozen before drift'),
                                  ('current_exact_code_error', colors[0], 'Code recomputed after drift (oracle)')]:
        values = np.array([[run['trajectory'][-1]['at_amplitude']['0.6'][code_type][str(order)] for order in orders] for run in runs])
        axes[1].plot(np.array(orders)*12, np.median(values, axis=0), 'o-', color=color, label=label)
    axes[1].set(xlabel='Retained real scalars', ylabel='Strong-probe prediction NRMSE', title='More detail predicts; it does not preserve')
    reads = [row['read'] for row in runs[0]['sequential_trajectory']]
    for name, label, color in [('read_only', 'Read only', colors[1]), ('flip', 'Read + sign flip', colors[0]), ('no_read', 'Drift only', colors[2])]:
        values = np.array([[row[name] for row in run['sequential_trajectory']] for run in runs])
        axes[2].plot(reads, np.median(values, axis=0), color=color, label=label)
    axes[2].set(xlabel='Reads performed', ylabel='Later weak-response change', title='Reading changes the retained behavior')
    for ax in axes:
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
    figure.savefig(destination, metadata={'Date': None})
    plt.close(figure)


def _close_receipts(left, right, path='root'):
    """Cross-runtime comparison permits roundoff, never omitted result fields."""
    if path == 'root.environment':
        return
    if isinstance(left, dict):
        if not isinstance(right, dict) or left.keys() != right.keys():
            raise AssertionError(f'receipt keys differ at {path}')
        for key in left:
            _close_receipts(left[key], right[key], f'{path}.{key}')
    elif isinstance(left, (list, tuple)):
        if len(left) != len(right):
            raise AssertionError(f'receipt lengths differ at {path}')
        for index, (first, second) in enumerate(zip(left, right)):
            _close_receipts(first, second, f'{path}[{index}]')
    elif isinstance(left, float):
        if not np.isclose(left, right, rtol=1e-9, atol=1e-11):
            raise AssertionError(f'receipt values differ at {path}: {left} != {right}')
    elif left != right:
        raise AssertionError(f'receipt values differ at {path}: {left} != {right}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke', action='store_true', help='one seed, shortened run; no gate claims')
    parser.add_argument('--output', type=Path, default=ROOT/'results'/'receipt.json')
    parser.add_argument('--verify', type=Path, help='rerun and compare a full receipt without overwriting it')
    arguments = parser.parse_args()
    if arguments.smoke and arguments.verify:
        parser.error('--smoke cannot verify a full receipt')
    config = replace(Config(), seeds=(4100,), checkpoints=2, sequential_reads=4) if arguments.smoke else Config()
    receipt = run_experiment(config)
    if arguments.verify:
        _close_receipts(json.loads(arguments.verify.read_text()), receipt)
        print('Full receipt reproduced; every numeric result agrees within the stated roundoff tolerance.')
    else:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(json.dumps(receipt, indent=2, allow_nan=False)+'\n')
        make_figure(receipt, arguments.output.with_suffix('.svg'))
        print(json.dumps({'evaluation': receipt['evaluation_status'], 'gates': receipt['gates'],
                          'summary': receipt['summary']}, indent=2))


if __name__ == '__main__':
    main()
