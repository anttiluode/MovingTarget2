"""Tests use analytic answers, not another copy of the implementation."""
import unittest

import numpy as np

from moving_target import (
    apply_ping, coded_response, exact_response, fit_code,
    phase_moments, response_features, tail_bound, wrapped_difference,
)


class ResponseMathTests(unittest.TestCase):
    def test_quadrature_ping_has_arctangent_phase_advance(self):
        answer = exact_response(np.zeros((1, 2)), np.array([[1., 0.]]),
                                np.array([[np.pi / 2, 0.]]), 0.5)
        self.assertAlmostEqual(float(answer[0]), np.arctan(0.5), places=14)

    def test_second_moment_reads_antipodal_state_when_first_is_zero(self):
        code = phase_moments(np.array([[0., np.pi]]), 2)
        np.testing.assert_allclose(code, [[0., 1.]], atol=1e-15)
        query = np.array([[np.pi / 4, 0.]])
        answer = coded_response(code, np.array([[1., 0.]]), query, 0.5)
        self.assertAlmostEqual(float(answer[0]), -0.125, places=14)

    def test_same_first_moment_does_not_determine_finite_ping_response(self):
        first = np.array([[np.pi/3, -np.pi/3, np.pi/3, -np.pi/3]])
        second = np.array([[0., 0., 0., np.pi]])
        np.testing.assert_allclose(phase_moments(first, 1), [[0.5]], atol=1e-15)
        np.testing.assert_allclose(phase_moments(second, 1), [[0.5]], atol=1e-15)
        wavevectors, query = np.array([[1., 0.]]), np.array([[np.pi/4, 0.]])
        weak_difference = abs(exact_response(first, wavevectors, query, .01)[0]
                              - exact_response(second, wavevectors, query, .01)[0])
        strong_difference = abs(exact_response(first, wavevectors, query, .6)[0]
                                - exact_response(second, wavevectors, query, .6)[0])
        self.assertLess(weak_difference, 0.0001)
        self.assertGreater(strong_difference, 0.15)

    def test_same_weak_answer_code_is_not_a_closed_state_for_future_reads(self):
        first = np.array([[np.pi/3, -np.pi/3, np.pi/3, -np.pi/3]])
        second = np.array([[0., 0., 0., np.pi]])
        wavevectors, query = np.array([[1., 0.]]), np.array([np.pi/4, 0.])
        after_first = phase_moments(apply_ping(first, wavevectors, query, .01), 1)
        after_second = phase_moments(apply_ping(second, wavevectors, query, .01), 1)
        # The first-order update depends on m2=-.5 versus m2=1.
        self.assertGreater(abs((after_first-after_second)[0, 0]), .007)
        self.assertLess(abs((after_first-after_second)[0, 0]), .008)

    def test_truncated_series_respects_uniform_remainder_bound(self):
        rng = np.random.default_rng(50)
        phases = rng.uniform(-np.pi, np.pi, (3, 11))
        queries = rng.uniform(-np.pi, np.pi, (150, 2))
        wavevectors = np.array([[1., 0.], [0., 1.], [1., 1.]])
        for amplitude in [-.6, .05, .25, .6]:
            exact = exact_response(phases, wavevectors, queries, amplitude)
            for order in [1, 2, 4, 8]:
                approximation = coded_response(phase_moments(phases, order),
                                                wavevectors, queries, amplitude)
                self.assertLessEqual(np.max(abs(approximation-exact)),
                                     tail_bound(amplitude, order) + 1e-14)

    def test_fitted_code_generalizes_to_queries_not_used_for_fit(self):
        # Hand-selected complex first moments, one independent Fourier mode/group.
        truth = np.array([[.3+.2j], [-.4+.1j]])
        wavevectors = np.array([[1., 0.], [0., 1.]])
        rng = np.random.default_rng(3)
        train = rng.uniform(-np.pi, np.pi, (40, 2))
        held_out = rng.uniform(-np.pi, np.pi, (70, 2))
        answers = .05 / 2 * (.3*np.sin(train[:, 0])+.2*np.cos(train[:, 0])
                             -.4*np.sin(train[:, 1])+.1*np.cos(train[:, 1]))
        fitted = fit_code(wavevectors, train, answers, .05, 1)
        np.testing.assert_allclose(fitted, truth, atol=1e-13)
        expected = .05/2*(.3*np.sin(held_out[:, 0])+.2*np.cos(held_out[:, 0])
                          -.4*np.sin(held_out[:, 1])+.1*np.cos(held_out[:, 1]))
        np.testing.assert_allclose(coded_response(fitted, wavevectors, held_out, .05),
                                   expected, atol=1e-14)

    def test_rank_deficient_calibration_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'rank'):
            fit_code(np.array([[1., 0.]]), np.zeros((5, 2)), np.zeros(5), .05, 1)

    def test_ping_updates_state_and_sign_flip_leaves_second_order_residue(self):
        phases, wavevectors, query = np.array([[.3, -.7]]), np.array([[1., 0.]]), np.array([1., 0.])
        residues = []
        for amplitude in [.04, .02]:
            after_read = apply_ping(phases, wavevectors, query, amplitude)
            restored = apply_ping(after_read, wavevectors, query, -amplitude)
            self.assertGreater(np.linalg.norm(wrapped_difference(after_read, phases)), amplitude/2)
            residues.append(np.linalg.norm(wrapped_difference(restored, phases)))
        self.assertGreater(residues[0] / residues[1], 3.8)
        self.assertLess(residues[0] / residues[1], 4.3)

    def test_wrap_is_small_across_pi_boundary(self):
        result = wrapped_difference(np.array([[-np.pi+.01]]), np.array([[np.pi-.01]]))
        np.testing.assert_allclose(result, [[.02]], atol=1e-14)

    def test_unsupported_pulse_and_invalid_order_are_rejected(self):
        for amplitude in [1., -1., float('nan')]:
            with self.assertRaises(ValueError):
                exact_response(np.zeros((1, 2)), np.ones((1, 2)), np.ones((1, 2)), amplitude)
        with self.assertRaises(ValueError):
            phase_moments(np.zeros((1, 2)), 0)
        with self.assertRaises(ValueError):
            response_features(np.ones((1, 2)), np.empty((0, 2)), .05, 1)


if __name__ == '__main__':
    unittest.main()
