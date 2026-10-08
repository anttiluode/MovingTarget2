import unittest
from dataclasses import replace

import numpy as np

from experiment import Config, calibration_data, run_experiment, run_seed


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.config = replace(Config(), seeds=(19,), checkpoints=2, steps_per_checkpoint=2,
                              held_out_queries=32, sequential_reads=4, sequential_drift_steps=1)

    def test_same_seed_and_configuration_reproduce_the_receipt(self):
        self.assertEqual(run_seed(19, self.config), run_seed(19, self.config))

    def test_calibration_is_separate_from_held_out_queries(self):
        split = calibration_data(19, self.config)
        self.assertEqual(split['queries'].shape, (64, 2))
        self.assertEqual(split['held_out'].shape, (32, 2))
        train_set = {tuple(q) for q in split['queries']}
        self.assertFalse(any(tuple(q) in train_set for q in split['held_out']))
        # Changing the evaluation sample count cannot change training data.
        longer = calibration_data(19, replace(self.config, held_out_queries=51))
        np.testing.assert_array_equal(longer['queries'], split['queries'])
        np.testing.assert_array_equal(longer['answers'], split['answers'])

    def test_receipt_separates_fitted_predictions_from_oracle_reconstruction(self):
        result = run_seed(19, self.config)
        self.assertIn('fitted_weak_code_nrmse', result['metrics'])
        self.assertIn('strong_current_order4_nrmse', result['metrics'])
        self.assertEqual(len(result['fitted_code_real']), 6)
        self.assertEqual(result['access']['fit_hidden_phase_coordinates'], 0)

    def test_sequential_read_actually_changes_memory(self):
        result = run_seed(19, self.config)
        self.assertGreater(result['metrics']['read_only_response_change'], .005)
        self.assertLess(result['metrics']['no_read_response_change'], .03)
        self.assertLess(result['metrics']['flip_response_change'],
                        result['metrics']['read_only_response_change'])

    def test_smoke_run_is_not_reported_as_a_full_gate_evaluation(self):
        result = run_experiment(self.config)
        self.assertEqual(result['evaluation_status'], 'partial_run_no_gate_claims')
        self.assertEqual(result['gates'], {})
        self.assertEqual(len(result['seeds']), 1)
        self.assertEqual(result['costs']['object_code_real_scalars'], 12)
        self.assertEqual(result['costs']['physical_phase_real_scalars'], 96)

    def test_cost_receipt_counts_controller_state_and_reset_access(self):
        costs = run_experiment(self.config)['costs']
        self.assertEqual(costs['calibration_reset_snapshot_float64_bytes'], 768)
        self.assertEqual(costs['drift_controller_allocations']['result_state_float64_bytes'], 768)
        self.assertEqual(costs['drift_controller_allocations']['velocity_float64_bytes'], 768)
        self.assertEqual(costs['drift_controller_allocations']['group_jacobian_float64_bytes'], 256)
        self.assertFalse(costs['drift_controller_allocations']['is_total_peak_memory'])


if __name__ == '__main__':
    unittest.main()
