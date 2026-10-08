import unittest

import numpy as np

from moving_target import apply_ping, drift_step, phase_moments, wrapped_difference


class DriftTests(unittest.TestCase):
    def test_coordinates_move_while_each_group_moment_stays_fixed(self):
        rng = np.random.default_rng(20)
        initial = rng.uniform(-np.pi, np.pi, (3, 16))
        phases = initial.copy()
        for _ in range(80):
            phases = drift_step(phases, rng.normal(size=phases.shape), .06)
        np.testing.assert_allclose(phase_moments(phases, 1), phase_moments(initial, 1), atol=1e-9)
        self.assertGreater(np.sqrt(np.mean(wrapped_difference(phases, initial)**2)), .25)

    def test_drift_preserves_current_moment_after_read_not_old_memory(self):
        initial = np.array([[-1., -.4, .2, .8, 1.3, 2.0]])
        after_read = apply_ping(initial, np.array([[1., 0.]]), np.array([1., 0.]), .2)
        after_drift = drift_step(after_read, np.array([[1., -1., .4, -.5, .2, .8]]), .05)
        np.testing.assert_allclose(phase_moments(after_drift, 1),
                                   phase_moments(after_read, 1), atol=1e-10)
        self.assertGreater(abs((phase_moments(after_drift, 1)-phase_moments(initial, 1))[0, 0]), .02)

    def test_fully_coherent_boundary_has_no_internal_phase_freedom(self):
        initial = np.zeros((2, 8))
        after = drift_step(initial, np.arange(16).reshape(2, 8), .1)
        np.testing.assert_array_equal(after, initial)

    def test_zero_velocity_is_a_noop_without_mutating_input(self):
        initial = np.array([[.1, .5, 1., 2.]])
        snapshot = initial.copy()
        after = drift_step(initial, np.zeros_like(initial), .1)
        np.testing.assert_array_equal(after, snapshot)
        np.testing.assert_array_equal(initial, snapshot)


if __name__ == '__main__':
    unittest.main()
