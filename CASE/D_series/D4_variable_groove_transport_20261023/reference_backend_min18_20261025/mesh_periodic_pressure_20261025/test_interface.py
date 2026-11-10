"""Focused interface checks. PETSc 3x3 matrix below is synthetic, no PDE solve."""

import ast
import copy
from pathlib import Path
import unittest

import numpy as np

from . import (attach_checked_pressure_nullspace, build_interface,
               remove_pressure_area_mean)
from .interface import Rejected, _exact_periodic_mpc, select


class InterfaceChecks(unittest.TestCase):
    def test_finest_actual_mixed_mesh_and_gauge(self):
        case = build_interface("B0MIN_FLAT_T_d1p25")
        stats = case["stats"]
        self.assertEqual(stats["actual_triangles"], 2*192*60)
        self.assertEqual(stats["actual_raw_dofs"], 104943)
        self.assertEqual(stats["trace"]["free_P2_velocity_slaves"], 238)
        self.assertEqual(stats["trace"]["P1_pressure_slaves_including_endpoints"], 61)
        self.assertEqual(stats["periodic_link_audit"]["slave_count"], 299)
        self.assertEqual(len(stats["periodic_link_audit"]["pairs"]), 299)
        self.assertLess(stats["periodic_link_audit"]["max_pair_coordinate_error"], 1e-11)
        self.assertFalse(stats["matrix_assembled"])
        self.assertFalse(stats["solver_called"])
        pressure = case["pressure"]
        self.assertEqual(np.count_nonzero(pressure["constant_vector"]), 11773)
        self.assertAlmostEqual(np.linalg.norm(pressure["constant_vector"]), 1.)
        self.assertAlmostEqual(pressure["area"], 3.2)
        self.assertFalse(pressure["matrix_kernel_checked"])

    def test_pressure_mean_and_periodic_endpoints(self):
        case = build_interface("B0MIN_MMS_mixed_N8")
        pressure = case["pressure"]
        weights = pressure["nodal_area_weights"]
        values = np.sin(np.arange(len(weights))) + 11.
        zero, mean = remove_pressure_area_mean(values, weights)
        self.assertAlmostEqual(float(weights @ zero), 0., delta=1e-12)
        zero_shifted, mean_shifted = remove_pressure_area_mean(values + 13., weights)
        np.testing.assert_allclose(zero_shifted, zero, atol=1e-13)
        self.assertAlmostEqual(mean_shifted-mean, 13.)
        self.assertEqual(case["stats"]["trace"]["P1_pressure_slaves_including_endpoints"], 9)
        self.assertEqual(case["stats"]["trace"]["free_P2_velocity_slaves"], 30)

    def test_missing_periodic_master_is_rejected(self):
        case = build_interface("B0MIN_MMS_scalar_N8")
        W = case["space"]
        coords = {i: (x[:2], 0) for i, x in enumerate(W.tabulate_dof_coordinates())}
        pair = case["stats"]["periodic_link_audit"]["pairs"][0]
        del coords[pair["master_dof"]]
        with self.assertRaisesRegex(Rejected, "PERIODIC_MASTER_MISSING"):
            _exact_periodic_mpc(W, type(case["mpc"]), coords,
                                set(case["mpc"].slaves), 2.)

    def test_synthetic_nullspace_accept_and_reject(self):
        from petsc4py import PETSc
        operator = PETSc.Mat().createAIJ([3, 3], nnz=1, comm=PETSc.COMM_SELF)
        operator.setUp()
        operator.setValue(0, 0, 2.)
        operator.setValue(1, 1, 3.)
        operator.assemble()
        rhs = operator.createVecLeft()
        rhs.array[:] = [1., 2., 0.]
        result = attach_checked_pressure_nullspace(operator, rhs, [0., 0., 1.])
        self.assertEqual(result["kernel_relative"], 0.)
        self.assertEqual(result["rhs_dot_null_after_projection"], 0.)
        rhs.array[:] = [1., 2., 1.]
        with self.assertRaisesRegex(Rejected, "COMPATIBILITY_FAILED"):
            attach_checked_pressure_nullspace(operator, rhs, [0., 0., 1.])
        rhs.array[:] = [1., 2., 0.]
        with self.assertRaisesRegex(Rejected, "COMPATIBILITY_FAILED"):
            attach_checked_pressure_nullspace(operator, rhs, [1., 0., 0.])

    def test_whitelist_and_no_solver_entrypoint(self):
        with self.assertRaises(Rejected):
            build_interface("not_a_planned_case")
        altered = copy.deepcopy(select(planned_id="B0MIN_MMS_scalar_N8")[0])
        altered["mesh"]["nx"] = 17
        with self.assertRaises(Rejected):
            select(supplied=altered)
        for path in (Path(__file__).with_name("interface.py"),
                     Path(__file__).with_name("inspect.py")):
            tree = ast.parse(path.read_text())
            for call in (n for n in ast.walk(tree) if isinstance(n, ast.Call)):
                name = call.func.attr if isinstance(call.func, ast.Attribute) else getattr(call.func, "id", "")
                self.assertNotIn(name, {"solve", "assemble_matrix", "assemble_vector",
                                        "LinearProblem", "NonlinearProblem"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
