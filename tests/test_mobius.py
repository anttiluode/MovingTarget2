"""Analytic checks for Möbius pings. Each test states the identity it checks."""
import unittest

import numpy as np

from mobius import (
    Odometer, act, apply_mobius_ping, constellation_change, cross_ratios, shape_angles,
    frozen_pulse, from_coordinates, halfway_identity_error, harmonic_pulse,
    mobius_pulse, pulse_matrix, pulses_for, to_coordinates, wrap,
)
from moving_target import apply_ping, phase_moments


class MobiusPulseTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(11)
        self.theta = rng.uniform(-np.pi, np.pi, 400)
        self.rng = rng

    def test_pulse_is_the_tangent_half_angle_solution_of_the_flow(self):
        # d theta/dt = sin(phi - theta)  =>  tan((theta-phi)/2) decays as exp(-t).
        phi, tau = .9, .37
        expected = wrap(phi + 2*np.arctan(np.tan(wrap(self.theta - phi)/2)*np.exp(-tau)))
        np.testing.assert_allclose(wrap(mobius_pulse(self.theta, phi, tau) - expected), 0, atol=1e-12)
        integrated = harmonic_pulse(self.theta, phi, tau, 0., substeps=256)
        np.testing.assert_allclose(wrap(mobius_pulse(self.theta, phi, tau) - integrated), 0, atol=1e-12)

    def test_frozen_law_matches_the_flow_only_to_first_order(self):
        phi = .4
        gaps = [np.max(np.abs(wrap(frozen_pulse(self.theta, phi, a) - mobius_pulse(self.theta, phi, a))))
                for a in (.04, .02)]
        self.assertLess(gaps[0], .04**2)
        self.assertGreater(gaps[0]/gaps[1], 3.8)
        self.assertLess(gaps[0]/gaps[1], 4.2)

    def test_frozen_pulse_is_the_angular_midpoint_of_a_mobius_map(self):
        # arg(z + c) = (theta + arg((z + c)/(1 + conj(c) z)))/2 for |z| = 1, |c| < 1.
        phis = self.rng.uniform(-np.pi, np.pi, 400)
        amplitudes = self.rng.uniform(-.95, .95, 400)
        errors = [halfway_identity_error(t, p, a) for t, p, a in zip(self.theta, phis, amplitudes)]
        self.assertLess(max(errors), 1e-13)

    def test_matches_frozen_ping_layout(self):
        phases = self.rng.uniform(-np.pi, np.pi, (3, 5))
        wavevectors = np.array([[1., 0.], [0., 1.], [1., 1.]])
        query = np.array([.3, -.8])
        frozen = apply_ping(phases, wavevectors, query, .05)
        flow = apply_mobius_ping(phases, wavevectors, query, .05)
        self.assertEqual(flow.shape, phases.shape)
        self.assertLess(np.max(np.abs(wrap(flow - frozen))), .05**2)


class GroupTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(5)
        self.theta = rng.uniform(-np.pi, np.pi, 300)
        self.phis = rng.uniform(-np.pi, np.pi, 40)
        self.rng = rng

    def test_any_sequence_of_pings_is_one_two_by_two_matrix(self):
        sequential, matrix = self.theta.copy(), np.eye(2, dtype=complex)
        for phi in self.phis:
            sequential = mobius_pulse(sequential, phi, .07)
            matrix = pulse_matrix(phi, .07) @ matrix
        np.testing.assert_allclose(wrap(act(matrix, self.theta) - sequential), 0, atol=1e-12)

    def test_odometer_keeps_three_numbers_and_loses_nothing(self):
        odometer, sequential = Odometer(1), self.theta.copy()
        for phi in self.phis:
            odometer.record([phi], -.11)
            sequential = mobius_pulse(sequential, phi, -.11)
        self.assertEqual(odometer.real_scalars, 3)
        restored = act(odometer.inverse_matrices()[0], sequential)
        np.testing.assert_allclose(wrap(restored - self.theta), 0, atol=1e-12)

    def test_coordinates_round_trip_up_to_matrix_sign(self):
        matrix = pulse_matrix(.3, .5) @ pulse_matrix(-1.2, .8) @ pulse_matrix(2.1, -.4)
        back = from_coordinates(to_coordinates(matrix))
        np.testing.assert_allclose(wrap(act(back, self.theta) - act(matrix, self.theta)), 0, atol=1e-12)
        with self.assertRaises(ValueError):
            from_coordinates([1., 0., 0.])

    def test_same_port_reversed_pulse_is_an_exact_inverse(self):
        there = mobius_pulse(self.theta, .8, .3)
        back = mobius_pulse(there, .8, -.3)
        np.testing.assert_allclose(wrap(back - self.theta), 0, atol=1e-13)

    def test_large_translations_decompose_without_overflow(self):
        with np.errstate(over='raise', invalid='raise'):
            pulses, error = pulses_for(pulse_matrix(.3, 30.), max_pulses=3)
        self.assertLess(error, 1e-10)
        self.assertTrue(all(np.isfinite(tau) for _, tau in pulses))

    def test_three_pulses_write_any_element_needed_and_two_cannot_rotate(self):
        rotation = np.diag([np.exp(.05j), np.exp(-.05j)])
        pulses, error = pulses_for(rotation, max_pulses=2, starts=30)
        self.assertGreater(error, 1e-6)
        pulses, error = pulses_for(rotation, max_pulses=3, starts=60)
        self.assertLess(error, 1e-12)
        self.assertEqual(len(pulses), 3)
        x = self.theta.copy()
        for phi, tau in pulses:
            x = mobius_pulse(x, phi, tau)
        np.testing.assert_allclose(wrap(x - act(rotation, self.theta)), 0, atol=1e-11)


class ConstellationTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(23)
        self.phases = rng.uniform(-np.pi, np.pi, (2, 9))
        self.phis = rng.uniform(-np.pi, np.pi, 50)

    def test_cross_ratios_match_the_complex_definition(self):
        # CR(z0, z1, z2, zj) = (z0 - z2)(z1 - zj) / ((z0 - zj)(z1 - z2)), real on a circle.
        z = np.exp(1j*self.phases)
        complex_ratio = (z[:, :1] - z[:, 2:3])*(z[:, 1:2] - z[:, 3:])/((z[:, :1] - z[:, 3:])*(z[:, 1:2] - z[:, 2:3]))
        self.assertLess(np.max(np.abs(complex_ratio.imag)), 1e-12*np.max(np.abs(complex_ratio.real)))
        ratio = cross_ratios(self.phases)
        self.assertEqual(ratio.shape, (2, 6))
        np.testing.assert_allclose(ratio, complex_ratio.real, rtol=1e-12)
        # A 2 pi relabelling of one phase must not change anything.
        shifted = self.phases.copy()
        shifted[0, 1] += 2*np.pi
        np.testing.assert_allclose(cross_ratios(shifted), ratio, rtol=1e-12)

    def test_cross_ratios_keep_precision_for_nearly_coincident_points(self):
        phases = np.array([[0., 1e-9, 2.0, 1e-9 + 3e-12, -1.]])
        exact = (np.sin(-1.0)*np.sin(-1.5e-12)) / (np.sin(-(1e-9 + 3e-12)/2)*np.sin((1e-9 - 2.0)/2))
        self.assertAlmostEqual(cross_ratios(phases)[0, 0]/exact, 1, places=9)
        self.assertTrue(np.all(np.isfinite(cross_ratios(phases))))

    def test_shape_angles_stay_defined_when_points_collapse(self):
        phases = np.array([[0., .4, 1.1, 0., 2.0, .4]])   # unit 3 sits on unit 0, unit 5 on unit 1
        with np.errstate(all='raise'):
            angles = shape_angles(phases)
        self.assertTrue(np.all(np.isfinite(angles)))
        self.assertAlmostEqual(abs(angles[0, 0]), np.pi/2, places=12)   # CR infinite
        self.assertAlmostEqual(angles[0, 2], 0., places=12)              # CR zero
        regular = np.arctan(cross_ratios(phases)[0, 1])
        self.assertAlmostEqual(angles[0, 1], regular, places=12)

    def test_mobius_pings_never_change_the_constellation(self):
        x = self.phases.copy()
        for phi in self.phis:
            x = mobius_pulse(x, phi, .25)
        self.assertLess(np.max(constellation_change(self.phases, x)), 1e-11)

    def test_frozen_pings_and_second_harmonics_rewrite_it(self):
        frozen, harmonic = self.phases.copy(), self.phases.copy()
        for phi in self.phis:
            frozen = frozen_pulse(frozen, phi, .25)
            harmonic = harmonic_pulse(harmonic, phi, .25, .05)
        self.assertGreater(np.median(constellation_change(self.phases, frozen)), 1e-4)
        self.assertGreater(np.median(constellation_change(self.phases, harmonic)), 1e-4)

    def test_same_first_moment_states_part_under_the_same_mobius_ping(self):
        # MATH.md section 5 pair. Same m1 = 1/2, different arrangements.
        first = np.array([[np.pi/3, -np.pi/3, np.pi/3, -np.pi/3]])
        second = np.array([[0., 0., 0., np.pi]])
        self.assertAlmostEqual(phase_moments(frozen_pulse(first, 0., .25), 1)[0, 0].real,
                               (.25 + .5)/np.sqrt(1 + .25 + .25**2), places=14)
        after_first = phase_moments(mobius_pulse(first, 0., .25), 1)[0, 0]
        after_second = phase_moments(mobius_pulse(second, 0., .25), 1)[0, 0]
        self.assertGreater(abs(after_first - after_second), .1)


class OrderAndLoopTests(unittest.TestCase):
    def setUp(self):
        self.theta = np.random.default_rng(31).uniform(-np.pi, np.pi, 500)

    def test_swapping_two_pings_leaves_a_common_rotation(self):
        # [sin(p1 - x) d/dx, sin(p2 - x) d/dx] = sin(p2 - p1) d/dx: uniform in x.
        a, p1, p2 = .01, .3, 1.7
        forward = mobius_pulse(mobius_pulse(self.theta, p1, a), p2, a)
        backward = mobius_pulse(mobius_pulse(self.theta, p2, a), p1, a)
        twist = wrap(forward - backward)
        self.assertAlmostEqual(twist.mean()/(a*a*np.sin(p2 - p1)), 1, delta=.01)
        self.assertLess(twist.std(), .02*abs(twist.mean()))

    def test_closed_loop_of_pings_rotates_by_its_area(self):
        a, b = .02, .03
        x = mobius_pulse(self.theta, 0., a)
        x = mobius_pulse(x, np.pi/2, b)
        x = mobius_pulse(x, 0., -a)
        x = mobius_pulse(x, np.pi/2, -b)
        twist = wrap(x - self.theta)
        self.assertAlmostEqual(twist.mean()/(a*b), 1, delta=.01)
        self.assertLess(twist.std(), .05*abs(twist.mean()))


class ValidationTests(unittest.TestCase):
    def test_invalid_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            frozen_pulse(np.zeros(3), 0., 1.)
        with self.assertRaises(ValueError):
            mobius_pulse(np.zeros(3), 0., float('nan'))
        with self.assertRaises(ValueError):
            harmonic_pulse(np.zeros(3), 0., .1, 0., substeps=0)
        with self.assertRaises(ValueError):
            cross_ratios(np.zeros((1, 3)))
        with self.assertRaises(ValueError):
            Odometer(2).record([0.], .1)


if __name__ == '__main__':
    unittest.main()
