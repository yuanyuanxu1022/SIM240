import math
from dataclasses import replace
import unittest

import numpy as np

from g5a_solver import (
    SqueezeProblem,
    analytic_metrics,
    analytic_pressure,
    evaluate_solution,
    smooth_mobility,
    solve_uniform_k,
)


class AnalyticModelTests(unittest.TestCase):
    def setUp(self):
        self.problem = SqueezeProblem(
            length_m=1.0e-3,
            width_m=1.0e-3,
            mu_pa_s=1.0e-3,
            vp_m_s=75.0e-9,
            p_out_pa=0.0,
            n_cells=401,
        )

    def test_smooth_mobility_is_h_cubed_over_twelve(self):
        self.assertAlmostEqual(smooth_mobility(75.0e-9), (75.0e-9) ** 3 / 12.0)

    def test_analytic_metrics_match_closed_form(self):
        K = 9.782423697043172e-23
        result = analytic_metrics(self.problem, K)
        expected_pmax = self.problem.mu_pa_s * self.problem.vp_m_s * self.problem.length_m**2 / (8.0 * K)
        expected_force = (
            self.problem.mu_pa_s
            * self.problem.vp_m_s
            * self.problem.width_m
            * self.problem.length_m**3
            / (12.0 * K)
        )
        self.assertAlmostEqual(result.pmax_pa, expected_pmax)
        self.assertAlmostEqual(result.force_n, expected_force)
        self.assertAlmostEqual(result.impedance_n_s_m, expected_force / self.problem.vp_m_s)
        self.assertAlmostEqual(
            result.q_displaced_m3_s,
            self.problem.width_m * self.problem.length_m * self.problem.vp_m_s,
        )

    def test_pressure_is_symmetric_and_zero_at_outlets(self):
        K = 9.782423697043172e-23
        s = np.array([-self.problem.length_m / 2.0, 0.0, self.problem.length_m / 2.0])
        p = analytic_pressure(s, self.problem, K)
        self.assertAlmostEqual(p[0], self.problem.p_out_pa)
        self.assertAlmostEqual(p[2], self.problem.p_out_pa)
        self.assertGreater(p[1], p[0])
        self.assertAlmostEqual(p[0], p[2])

    def test_invalid_problem_or_mobility_is_rejected(self):
        with self.assertRaises(ValueError):
            SqueezeProblem(1e-3, 1e-3, 1e-3, 75e-9, 0.0, 201)
        with self.assertRaises(ValueError):
            analytic_metrics(self.problem, 0.0)
        with self.assertRaises(ValueError):
            smooth_mobility(float("nan"))


class FiniteVolumeTests(unittest.TestCase):
    def setUp(self):
        self.problem = SqueezeProblem(1e-3, 1e-3, 1e-3, 75e-9, 0.0, 401)
        self.K = 9.782423697043172e-23

    def test_fv_solution_matches_pressure_load_and_mass_gates(self):
        solution = solve_uniform_k(self.problem, self.K)
        metrics = evaluate_solution(self.problem, self.K, solution)
        self.assertLess(metrics.pmax_relative_error, 1e-6)
        self.assertLess(metrics.force_relative_error, 1e-4)
        self.assertLess(metrics.mass_relative_error, 1e-10)
        self.assertLess(metrics.symmetry_relative_error, 1e-12)
        self.assertTrue(np.all(solution.pressure_pa >= self.problem.p_out_pa))

    def test_face_flux_has_correct_outward_signs(self):
        solution = solve_uniform_k(self.problem, self.K)
        self.assertLess(solution.face_flux_m2_s[0], 0.0)
        self.assertGreater(solution.face_flux_m2_s[-1], 0.0)

    def test_impedance_is_independent_of_reference_speed(self):
        impedances = []
        for factor in (0.5, 1.0, 2.0):
            p = replace(self.problem, vp_m_s=self.problem.vp_m_s * factor)
            s = solve_uniform_k(p, self.K)
            impedances.append(evaluate_solution(p, self.K, s).impedance_n_s_m)
        spread = (max(impedances) - min(impedances)) / impedances[1]
        self.assertLess(spread, 1e-10)


if __name__ == "__main__":
    unittest.main()
