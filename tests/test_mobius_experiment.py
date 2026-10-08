"""Harness checks for the Möbius addendum: it must reuse the frozen protocol exactly."""
import json
from pathlib import Path
import unittest

import numpy as np

from experiment import Config, WAVEVECTORS, calibration_data
from mobius import frozen_pulse
from mobius_experiment import MobiusConfig, burst_protocol, frozen_pulse_sequence, sequential_protocol
from moving_target import exact_response

ROOT = Path(__file__).resolve().parents[1]


class MobiusHarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = Config()
        split = calibration_data(4100, base)
        cls.initial, cls.held_out = split['phases'], split['held_out']
        cls.references = {a: exact_response(cls.initial, WAVEVECTORS, cls.held_out, a) for a in (.05, .6)}

    def test_frozen_law_branch_reproduces_the_frozen_receipt(self):
        receipt = json.loads((ROOT/'results'/'receipt.json').read_text())
        frozen = next(run['metrics'] for run in receipt['seeds'] if run['seed'] == 4100)
        result = sequential_protocol(4100, self.initial, self.held_out, self.references[.05])
        for name in ['no_read', 'read_only', 'flip']:
            self.assertAlmostEqual(result['frozen'][f'{name}_response_change'],
                                   frozen[f'{name}_response_change'], places=12)
        # A same-port reversed Möbius pulse is an exact inverse.
        self.assertLess(result['mobius']['flip_vs_no_read_max_phase_rms'], 1e-12)

    def test_odometer_undoes_a_burst_without_reading_phases(self):
        config = MobiusConfig(burst_reads=8, oracle_starts=0)
        result = burst_protocol(4100, self.initial, self.held_out, self.references, .05, config)
        self.assertLess(result['mobius_odometer_correction']['phase_rms_error'], 1e-12)
        self.assertEqual(result['odometer']['phase_reads'], 0)
        self.assertEqual(result['odometer']['observer_real_scalars'], 18)
        self.assertLessEqual(max(result['odometer']['correction_pulses_per_group']), 3)
        self.assertGreater(result['frozen_per_read_flip']['phase_rms_error'], 1e-8)
        self.assertGreater(result['mobius_uncorrected']['phase_rms_error'], .1)

    def test_fast_frozen_sequence_equals_frozen_pulses(self):
        theta = np.random.default_rng(2).uniform(-np.pi, np.pi, 50)
        parameters = np.array([.4, .2, -1.3, -.7, 2.2, .05])
        expected = theta
        for k in range(0, 6, 2):
            expected = frozen_pulse(expected, parameters[k], .99*np.tanh(parameters[k+1]))
        np.testing.assert_allclose(np.angle(np.exp(1j*(frozen_pulse_sequence(parameters, theta) - expected))),
                                   0, atol=1e-13)


if __name__ == '__main__':
    unittest.main()
