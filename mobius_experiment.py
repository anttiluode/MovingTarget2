"""Frozen Möbius-ping addendum to MovingTarget2 (MOBIUS_PROTOCOL.md).

Run with --help. The original experiment, receipt and gates are untouched;
this file reuses the frozen seeds, initial states, held-out queries, read
queries, drift streams and software listener.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import platform

import numpy as np

from experiment import (
    Config, READ_QUERIES, WAVEVECTORS, _close_receipts, _nrmse, _rng, calibration_data,
)
from mobius import (
    Odometer, _levenberg_marquardt, act, apply_mobius_ping, constellation_change,
    from_coordinates, group_phases, harmonic_pulse, mobius_pulse,
    pulses_for, to_coordinates, wrap,
)
from moving_target import apply_ping, drift_step, exact_response, wrapped_difference

ROOT = Path(__file__).resolve().parent
BASE = Config()


@dataclass(frozen=True)
class MobiusConfig:
    seeds: tuple[int, ...] = BASE.seeds
    burst_reads: int = 32
    burst_amplitudes: tuple[float, ...] = (.05, .25)
    harmonic_epsilons: tuple[float, ...] = (0., 1e-4, 1e-3, 1e-2, 1e-1)
    harmonic_amplitude: float = .05
    harmonic_substeps: int = 64
    loop_amplitude: float = .05
    loop_offsets: tuple[float, ...] = (np.pi/6, np.pi/2, 5*np.pi/6)
    oracle_starts: int = 12
    max_correction_pulses: int = 3


def _phase_rms(state, reference):
    return float(np.sqrt(np.mean(wrapped_difference(state, reference)**2)))


def _numeric_jacobian(function):
    """Central-difference Jacobian for the oracle fits."""
    def wrapped(x):
        residual = function(x)
        jacobian = np.empty((len(residual), len(x)))
        for j in range(len(x)):
            h = 1e-6*max(1., abs(x[j]))
            up, down = x.copy(), x.copy()
            up[j] += h
            down[j] -= h
            jacobian[:, j] = (function(up) - function(down))/(2*h)
        return residual, jacobian
    return wrapped


def _disk(u):
    """Unconstrained pair -> point strictly inside the unit disk."""
    value = u[0] + 1j*u[1]
    return value/np.sqrt(1 + abs(value)**2)


def _undisk(w):
    scale = 1/np.sqrt(1 - abs(w)**2)
    return np.array([(w*scale).real, (w*scale).imag])


def _best_fit(apply, after, initial, start_points):
    best = (None, np.inf)
    for start in start_points:
        x, _ = _levenberg_marquardt(_numeric_jacobian(lambda p: wrap(apply(p, after) - initial)), start)
        error = _phase_rms(apply(x, after), initial)
        if error < best[1]:
            best = (x, error)
    return apply(best[0], after)


def oracle_best_mobius_map(after, initial, guess_matrix, starts, seed):
    """Best single Möbius map for one group, fitted against hidden initial phases."""
    def apply(p, theta):
        w = _disk(p[:2])
        return act(from_coordinates([w.real, w.imag, p[2]]), theta)
    rng = np.random.default_rng(seed)
    guess = to_coordinates(guess_matrix)
    start_points = [np.r_[_undisk(guess[0] + 1j*guess[1]), guess[2]], np.zeros(3)]
    start_points += [np.r_[rng.normal(0, .3, 2), rng.uniform(-np.pi, np.pi)] for _ in range(starts)]
    return _best_fit(apply, after, initial, start_points)


def frozen_pulse_sequence(parameters, theta):
    """Frozen-law pulses (phi, raw) with amplitude .99 tanh(raw), wrapped once."""
    x = np.asarray(theta, dtype=float)
    for k in range(0, len(parameters), 2):
        x = x + np.angle(1 + .99*np.tanh(parameters[k+1])*np.exp(1j*(parameters[k] - x)))
    return wrap(x)


def oracle_best_frozen_pulses(after, initial, guess_pulses, count, starts, seed):
    """Best `count` frozen-law pulses for one group, fitted against hidden initial phases."""
    rng = np.random.default_rng(seed)
    start_points = []
    if len(guess_pulses) <= count:
        padded = list(guess_pulses) + [(0., 0.)]*(count - len(guess_pulses))
        start_points.append(np.ravel([[phi, np.arctanh(np.clip(tau, -.98, .98)/.99)] for phi, tau in padded]))
    start_points += [np.ravel([[rng.uniform(-np.pi, np.pi), rng.normal(0, .3)] for _ in range(count)])
                     for _ in range(starts)]
    return _best_fit(frozen_pulse_sequence, after, initial, start_points)


def _listener(state, held_out, reference, amplitude):
    return _nrmse(exact_response(state, WAVEVECTORS, held_out, amplitude), reference, reference)


def _state_metrics(state, initial, held_out, references):
    weak, strong = sorted(references)
    change = constellation_change(initial, state)
    return {
        'phase_rms_error': _phase_rms(state, initial),
        'weak_response_change': _listener(state, held_out, references[weak], weak),
        'strong_response_change': _listener(state, held_out, references[strong], strong),
        'constellation_change_median': float(np.median(change)),
        'constellation_change_max': float(np.max(change)),
    }


LAWS = {'frozen': lambda s, q, a: apply_ping(s, WAVEVECTORS, q, a),
        'mobius': lambda s, q, a: apply_mobius_ping(s, WAVEVECTORS, q, a)}


def sequential_protocol(seed, initial, held_out, reference):
    """M1: the frozen sequential protocol with only the read law swapped."""
    weak = BASE.amplitudes[0]
    results = {}
    for law, ping in LAWS.items():
        states = {name: initial.copy() for name in ['no_read', 'read_only', 'flip']}
        drift_rng = _rng(seed, 6)
        odometer = Odometer(len(WAVEVECTORS))
        flip_gap = 0.
        for read in range(BASE.sequential_reads):
            query = READ_QUERIES[read % len(READ_QUERIES)]
            states['read_only'] = ping(states['read_only'], query, weak)
            states['flip'] = ping(ping(states['flip'], query, weak), query, -weak)
            odometer.record(group_phases(WAVEVECTORS, query), weak)
            for _ in range(BASE.sequential_drift_steps):
                velocity = drift_rng.normal(size=initial.shape)
                for name in states:
                    states[name] = drift_step(states[name], velocity, BASE.phase_step)
            flip_gap = max(flip_gap, _phase_rms(states['flip'], states['no_read']))
        row = {f'{name}_response_change': _listener(state, held_out, reference, weak)
               for name, state in states.items()}
        row['flip_vs_no_read_max_phase_rms'] = flip_gap
        if law == 'mobius':
            # Descriptive only: one end correction cannot know the interleaved drift.
            corrected = np.stack([act(matrix, states['read_only'][g])
                                  for g, matrix in enumerate(odometer.inverse_matrices())])
            row['interleaved_odometer_response_change'] = _listener(corrected, held_out, reference, weak)
            row['interleaved_odometer_phase_rms_vs_no_read'] = _phase_rms(corrected, states['no_read'])
        results[law] = row
    return results


def burst_protocol(seed, initial, held_out, references, amplitude, config):
    """M2/M3: reads without drift, then every correction strategy."""
    groups = len(WAVEVECTORS)
    frozen, flipped, flow = initial.copy(), initial.copy(), initial.copy()
    odometer = Odometer(groups)
    for read in range(config.burst_reads):
        query = READ_QUERIES[read % len(READ_QUERIES)]
        frozen = apply_ping(frozen, WAVEVECTORS, query, amplitude)
        flipped = apply_ping(apply_ping(flipped, WAVEVECTORS, query, amplitude), WAVEVECTORS, query, -amplitude)
        flow = apply_mobius_ping(flow, WAVEVECTORS, query, amplitude)
        odometer.record(group_phases(WAVEVECTORS, query), amplitude)
    corrected, pulse_counts, durations, solve_errors = flow.copy(), [], [], []
    oracle_map, oracle_pulses = frozen.copy(), frozen.copy()
    for g, inverse in enumerate(odometer.inverse_matrices()):
        pulses, error = pulses_for(inverse, max_pulses=config.max_correction_pulses, seed=1000*seed+g)
        for phi, tau in pulses:
            corrected[g] = mobius_pulse(corrected[g], phi, tau)
        pulse_counts.append(len(pulses))
        durations += [abs(tau) for _, tau in pulses]
        solve_errors.append(error)
        oracle_map[g] = oracle_best_mobius_map(frozen[g], initial[g], inverse, config.oracle_starts, 7919*seed+g)
        oracle_pulses[g] = oracle_best_frozen_pulses(frozen[g], initial[g], pulses, 3,
                                                     config.oracle_starts, 7907*seed+g)
    states = {
        'frozen_uncorrected': frozen,
        'mobius_uncorrected': flow,
        'frozen_per_read_flip': flipped,
        'frozen_oracle_best_mobius_map': oracle_map,
        'frozen_oracle_best_three_frozen_pulses': oracle_pulses,
        'mobius_odometer_correction': corrected,
    }
    return {
        **{name: _state_metrics(state, initial, held_out, references) for name, state in states.items()},
        'odometer': {
            'observer_real_scalars': odometer.real_scalars,
            'phase_reads': 0,
            'correction_pulses_per_group': pulse_counts,
            'max_correction_pulse_duration': float(max(durations)),
            'max_coordinate_solve_residual': float(max(solve_errors)),
        },
    }


def drift_constellation(seed, initial):
    """M3: the frozen constrained drift (128 steps, stream 3) and the constellation."""
    state, drift_rng = initial.copy(), _rng(seed, 3)
    for _ in range(BASE.checkpoints*BASE.steps_per_checkpoint):
        state = drift_step(state, drift_rng.normal(size=state.shape), BASE.phase_step)
    change = constellation_change(initial, state)
    return state, {'constellation_change_median': float(np.median(change)),
                   'constellation_change_max': float(np.max(change)),
                   'phase_rms': _phase_rms(state, initial)}


def harmonic_protocol(initial, config):
    """M4: a second harmonic in the ping writes the constellation."""
    results = {}
    for epsilon in config.harmonic_epsilons:
        x, odometer = initial.copy(), Odometer(len(WAVEVECTORS))
        for read in range(config.burst_reads):
            phis = group_phases(WAVEVECTORS, READ_QUERIES[read % len(READ_QUERIES)])
            x = harmonic_pulse(x, phis[:, None], config.harmonic_amplitude, epsilon, config.harmonic_substeps)
            odometer.record(phis, config.harmonic_amplitude)
        corrected = np.stack([act(matrix, x[g]) for g, matrix in enumerate(odometer.inverse_matrices())])
        change = constellation_change(initial, x)
        results[repr(epsilon)] = {
            'constellation_change_median': float(np.median(change)),
            'constellation_change_max': float(np.max(change)),
            'odometer_corrected_phase_rms_error': _phase_rms(corrected, initial),
        }
    return results


def loop_protocol(initial, config):
    """M5: the order of two pings and a closed loop of pings."""
    a, rows = config.loop_amplitude, []
    for g, theta in enumerate(initial):
        phi1 = float(np.angle(np.mean(np.exp(1j*theta))))
        for offset in config.loop_offsets:
            phi2 = phi1 + offset
            forward = mobius_pulse(mobius_pulse(theta, phi1, a), phi2, a)
            backward = mobius_pulse(mobius_pulse(theta, phi2, a), phi1, a)
            swap = wrap(forward - backward)
            loop = mobius_pulse(mobius_pulse(mobius_pulse(mobius_pulse(theta, phi1, a), phi2, a), phi1, -a), phi2, -a)
            loop = wrap(loop - theta)
            rows.append({
                'group': g, 'offset': float(offset), 'theory': float(a*a*np.sin(offset)),
                'swap_common': float(swap.mean()), 'swap_spread': float(swap.std()),
                'loop_common': float(loop.mean()), 'loop_spread': float(loop.std()),
            })
    return rows


def run_seed(seed, config=MobiusConfig()):
    split = calibration_data(seed, BASE)
    initial, held_out = split['phases'], split['held_out']
    weak, _, strong = BASE.amplitudes
    references = {weak: exact_response(initial, WAVEVECTORS, held_out, weak),
                  strong: exact_response(initial, WAVEVECTORS, held_out, strong)}
    _, drift = drift_constellation(seed, initial)
    return {
        'seed': seed,
        'sequential': sequential_protocol(seed, initial, held_out, references[weak]),
        'bursts': {str(a): burst_protocol(seed, initial, held_out, references, a, config)
                   for a in config.burst_amplitudes},
        'drift': drift,
        'harmonic': harmonic_protocol(initial, config),
        'loops': loop_protocol(initial, config),
    }


def _summary(values):
    values = np.asarray(values, dtype=float)
    q25, median, q75 = np.quantile(values, [.25, .5, .75])
    return {'median': float(median), 'q25': float(q25), 'q75': float(q75),
            'min': float(values.min()), 'max': float(values.max())}


def summarize(seeds):
    summary = {'sequential': {}, 'bursts': {}, 'harmonic': {}}
    for law in ['frozen', 'mobius']:
        summary['sequential'][law] = {key: _summary([run['sequential'][law][key] for run in seeds])
                                      for key in seeds[0]['sequential'][law]}
    for amplitude, block in seeds[0]['bursts'].items():
        summary['bursts'][amplitude] = {
            name: {key: _summary([run['bursts'][amplitude][name][key] for run in seeds]) for key in metrics}
            for name, metrics in block.items() if name != 'odometer'}
        odometers = [run['bursts'][amplitude]['odometer'] for run in seeds]
        summary['bursts'][amplitude]['odometer'] = {
            'max_correction_pulses_per_group': int(max(max(o['correction_pulses_per_group']) for o in odometers)),
            'pulse_count_histogram': {str(n): int(sum(o['correction_pulses_per_group'].count(n) for o in odometers))
                                      for n in (1, 2, 3)},
            'max_correction_pulse_duration': float(max(o['max_correction_pulse_duration'] for o in odometers)),
            'max_coordinate_solve_residual': float(max(o['max_coordinate_solve_residual'] for o in odometers)),
            'observer_real_scalars': odometers[0]['observer_real_scalars'],
            'phase_reads': 0,
        }
    summary['drift'] = {key: _summary([run['drift'][key] for run in seeds]) for key in seeds[0]['drift']}
    pooled = {}
    for epsilon in seeds[0]['harmonic']:
        summary['harmonic'][epsilon] = {key: _summary([run['harmonic'][epsilon][key] for run in seeds])
                                        for key in seeds[0]['harmonic'][epsilon]}
        pooled[float(epsilon)] = summary['harmonic'][epsilon]['constellation_change_median']['median']
    positive = sorted(e for e in pooled if e > 0)
    summary['harmonic_log_log_slope'] = float(np.polyfit(np.log10(positive),
                                                         np.log10([pooled[e] for e in positive]), 1)[0])
    rows = [row for run in seeds for row in run['loops']]
    summary['loops'] = {
        'swap_relative_error': _summary([abs(r['swap_common']/r['theory'] - 1) for r in rows]),
        'loop_relative_error': _summary([abs(r['loop_common']/r['theory'] - 1) for r in rows]),
        'swap_spread_ratio': _summary([r['swap_spread']/abs(r['swap_common']) for r in rows]),
        'loop_spread_ratio': _summary([r['loop_spread']/abs(r['loop_common']) for r in rows]),
        'cases': len(rows),
    }
    frozen_receipt = json.loads((ROOT/'results'/'receipt.json').read_text())
    frozen_metrics = {run['seed']: run['metrics'] for run in frozen_receipt['seeds']}
    summary['frozen_harness_max_seed_gap'] = float(max(
        abs(run['sequential']['frozen'][f'{name}_response_change'] - frozen_metrics[run['seed']][f'{name}_response_change'])
        for run in seeds for name in ['no_read', 'read_only', 'flip'] if run['seed'] in frozen_metrics))
    return summary


def evaluate_gates(summary):
    burst, harmonic, loops = summary['bursts']['0.05'], summary['harmonic'], summary['loops']
    return {
        'G1_mobius_flip_equals_drift_only':
            summary['sequential']['mobius']['flip_vs_no_read_max_phase_rms']['max'] < 1e-9
            and summary['frozen_harness_max_seed_gap'] < 1e-9,
        'G2_three_number_odometer_undoes_burst':
            burst['mobius_odometer_correction']['phase_rms_error']['max'] < 1e-9
            and burst['odometer']['max_correction_pulses_per_group'] <= 3,
        'G3_frozen_law_has_no_small_exact_correction': all(
            burst[name]['phase_rms_error']['median'] > 1e-6 for name in
            ['frozen_per_read_flip', 'frozen_oracle_best_mobius_map', 'frozen_oracle_best_three_frozen_pulses']),
        'G4_pings_cannot_write_drift_can':
            burst['mobius_uncorrected']['constellation_change_max']['max'] < 1e-9
            and burst['frozen_uncorrected']['constellation_change_median']['median'] > 1e-6
            and summary['drift']['constellation_change_median']['median'] > 1e-2,
        'G5_second_harmonic_writes_in_proportion':
            harmonic['0.0']['constellation_change_max']['max'] < 1e-9
            and .9 <= summary['harmonic_log_log_slope'] <= 1.1,
        'G6_order_and_loops_rotate':
            loops['swap_relative_error']['median'] < .02 and loops['loop_relative_error']['median'] < .02
            and loops['swap_spread_ratio']['median'] < .05 and loops['loop_spread_ratio']['median'] < .05,
    }


def run_experiment(config=MobiusConfig()):
    seeds = [run_seed(seed, config) for seed in config.seeds]
    summary = summarize(seeds)
    files = ['MOBIUS_PROTOCOL.md', 'mobius.py', 'mobius_experiment.py', 'moving_target.py', 'experiment.py']
    return {
        'schema': 1, 'config': asdict(config),
        'source_sha256': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files},
        'environment': {'python': platform.python_version(), 'numpy': np.__version__},
        'evaluation_status': 'full_frozen_evaluation' if config == MobiusConfig() else 'partial_run_no_gate_claims',
        'summary': summary,
        'gates': evaluate_gates(summary) if config == MobiusConfig() else {},
        'costs': {
            'odometer_observer_real_scalars': 3*len(WAVEVECTORS),
            'odometer_needs': 'the applied query sequence and amplitude; no oscillator phases',
            'odometer_correction_port': 'one pulse phase and duration per group (stronger than the query port)',
            'per_read_flip_extra_pulses': BASE.sequential_reads,
            'oracle_fits_use_hidden_initial_phases': True,
        },
        'seeds': seeds,
    }


# Validated categorical slots (dataviz reference palette, light surface).
SURFACE, INK, MUTED, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
MOBIUS_COLOR, FROZEN_COLOR, HARMONIC_COLOR = '#2a78d6', '#eb6834', '#1baf7a'


def make_figure(receipt, destination):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matplotlib.rcParams.update({'svg.hashsalt': 'MovingTarget2-mobius', 'font.size': 9,
                                'axes.edgecolor': GRID, 'axes.labelcolor': MUTED,
                                'xtick.color': MUTED, 'ytick.color': MUTED, 'text.color': INK})
    summary = receipt['summary']
    figure, axes = plt.subplots(1, 3, figsize=(14, 4.4), constrained_layout=True, facecolor=SURFACE)
    for ax in axes:
        ax.set_facecolor(SURFACE)
        ax.grid(color=GRID, linewidth=.8)
        ax.set_axisbelow(True)
        for side in ['top', 'right']:
            ax.spines[side].set_visible(False)

    # A. The frozen sequential protocol, two read laws.
    ax = axes[0]
    rows = [('Drift only', 'no_read_response_change'), ('Read + reversed pulse', 'flip_response_change'),
            ('Read only', 'read_only_response_change')]
    for offset, (law, color, label) in zip([-.12, .12], [('frozen', FROZEN_COLOR, 'Frozen law'),
                                                          ('mobius', MOBIUS_COLOR, 'Möbius law')]):
        for y, (_, key) in enumerate(rows):
            s = summary['sequential'][law][key]
            ax.plot([100*s['q25'], 100*s['q75']], [y+offset]*2, color=color, linewidth=2, solid_capstyle='round')
            ax.plot(100*s['median'], y+offset, 'o', color=color, markersize=7,
                    markeredgecolor=SURFACE, markeredgewidth=1.5, label=label if y == 0 else None)
    for y, (_, key) in enumerate(rows):
        for law, offset in [('frozen', -.12), ('mobius', .12)]:
            value = 100*summary['sequential'][law][key]['median']
            ax.annotate(f'{value:.2f}%', (value, y+offset), xytext=(7, -3), textcoords='offset points',
                        color=MUTED, fontsize=8)
    ax.set_xscale('log')
    ax.set_yticks(range(len(rows)), [name for name, _ in rows])
    ax.set_ylim(-.6, len(rows) - .4)
    ax.set_xlim(.4, 400)
    ax.set_xlabel('Later weak-answer change after 32 reads (%, median and IQR)')
    ax.set_title('Same reads and drift, two read laws', loc='left', fontsize=10)
    ax.legend(frameon=False, loc='lower right')

    # B. Undoing a burst of 32 reads.
    ax = axes[1]
    burst = summary['bursts']['0.05']
    strategies = [
        ('No correction', 'frozen_uncorrected', FROZEN_COLOR),
        ('Reversed pulse after each read', 'frozen_per_read_flip', FROZEN_COLOR),
        ('Best 3 frozen pulses (oracle)', 'frozen_oracle_best_three_frozen_pulses', FROZEN_COLOR),
        ('Best Möbius map (oracle)', 'frozen_oracle_best_mobius_map', FROZEN_COLOR),
        ('No correction', 'mobius_uncorrected', MOBIUS_COLOR),
        ('Odometer: 18 numbers, ≤3 pulses/group', 'mobius_odometer_correction', MOBIUS_COLOR),
    ]
    floor = 1e-16
    for y, (name, key, color) in enumerate(strategies):
        s = burst[key]['phase_rms_error']
        low, mid, high = (max(s[k], floor) for k in ('q25', 'median', 'q75'))
        ax.plot([low, high], [y, y], color=color, linewidth=2, solid_capstyle='round')
        ax.plot(mid, y, 'o', color=color, markersize=7, markeredgecolor=SURFACE, markeredgewidth=1.5)
        ax.annotate(f'{mid:.1e} rad', (mid, y), xytext=(7, -3), textcoords='offset points', color=MUTED, fontsize=8)
    ax.axhline(3.5, color=GRID, linewidth=.8)
    ax.set_xscale('log')
    ax.set_xlim(1e-16, 1e2)
    ax.set_yticks(range(len(strategies)), [name for name, _, _ in strategies])
    ax.set_ylim(-.6, len(strategies) - .4)
    ax.invert_yaxis()
    ax.text(1.5e-16, 1.5, 'frozen law', color=MUTED, fontsize=8, va='center')
    ax.text(1.5e-16, 4.5, 'Möbius law', color=MUTED, fontsize=8, va='center')
    ax.set_xlabel('RMS phase error after correction, radians (a = 0.05)')
    ax.set_title('Undoing 32 reads with no phase access', loc='left', fontsize=10)

    # C. What can rewrite the constellation.
    ax = axes[2]
    epsilons = [e for e in summary['harmonic'] if float(e) > 0]
    xs = [float(e) for e in epsilons]
    mids = [summary['harmonic'][e]['constellation_change_median']['median'] for e in epsilons]
    ax.plot(xs, mids, '-o', color=HARMONIC_COLOR, linewidth=2, markersize=7,
            markeredgecolor=SURFACE, markeredgewidth=1.5)
    ax.annotate(f'second-harmonic pings\nslope {summary["harmonic_log_log_slope"]:.2f}', (xs[1], mids[1]),
                xytext=(10, -26), textcoords='offset points', color=INK, fontsize=8)
    references = [
        ('Frozen constrained drift, 128 steps', summary['drift']['constellation_change_median']['median'], MUTED),
        ('Frozen-law reads', burst['frozen_uncorrected']['constellation_change_median']['median'], FROZEN_COLOR),
        ('Möbius reads', max(burst['mobius_uncorrected']['constellation_change_median']['median'], floor), MOBIUS_COLOR),
    ]
    for label, value, color in references:
        ax.axhline(value, color=color, linewidth=1.5)
        ax.text(1.1e-4, value*1.8, f'{label}: {value:.1e}', color=INK, fontsize=8)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlim(8e-5, 1.3e-1)
    ax.set_ylim(1e-16, 10)
    ax.set_xlabel('Second-harmonic share ε of the ping')
    ax.set_ylabel('Cross-ratio change, median |Δ atan X|')
    ax.set_title('What can rewrite the hidden shape', loc='left', fontsize=10)

    figure.savefig(destination, metadata={'Date': None}, facecolor=SURFACE)
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke', action='store_true', help='one seed; no gate claims')
    parser.add_argument('--output', type=Path, default=ROOT/'results'/'mobius_receipt.json')
    parser.add_argument('--verify', type=Path, help='rerun and compare a full receipt without overwriting it')
    arguments = parser.parse_args()
    if arguments.smoke and arguments.verify:
        parser.error('--smoke cannot verify a full receipt')
    config = MobiusConfig(seeds=(4100,)) if arguments.smoke else MobiusConfig()
    receipt = run_experiment(config)
    if arguments.verify:
        _close_receipts(json.loads(arguments.verify.read_text()), receipt)
        print('Möbius receipt reproduced within the stated roundoff tolerance.')
    else:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(json.dumps(receipt, indent=2, allow_nan=False)+'\n')
        make_figure(receipt, arguments.output.with_suffix('.svg'))
        print(json.dumps({'evaluation': receipt['evaluation_status'], 'gates': receipt['gates']}, indent=2))


if __name__ == '__main__':
    main()
