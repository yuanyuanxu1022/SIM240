import subprocess
import unittest
import importlib.util
import os
from pathlib import Path


V3_ROOT = Path(__file__).resolve().parents[1]


class G1V3DefinitionTest(unittest.TestCase):
    def test_dry_run_freezes_fine_grid_three_force_matrix(self):
        result = subprocess.run(
            ["bash", str(V3_ROOT / "scripts" / "run_v3_force_matrix.sh"), "--dry-run"],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(
            result.stdout.splitlines(),
            [
                "case_id,dx_nm,tau,acceleration_m_s2",
                "G1V3-a1,2.5,1.7,5e4",
                "G1V3-a2,2.5,1.7,1e5",
                "G1V3-a3,2.5,1.7,2e5",
            ],
        )

    def test_force_evaluator_accepts_exact_three_point_response(self):
        module_path = V3_ROOT / "scripts" / "postprocess_g1_v3.py"
        spec = importlib.util.spec_from_file_location("g1_v3_postprocess", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        metrics = module.evaluate_force_response([
            {"force": 5.0e4, "J": 1.0e-12},
            {"force": 1.0e5, "J": 2.0e-12},
            {"force": 2.0e5, "J": 4.0e-12},
        ])
        self.assertTrue(metrics["pass"])
        self.assertAlmostEqual(metrics["r2"], 1.0)
        self.assertAlmostEqual(metrics["intercept_fraction"], 0.0, places=12)

    def test_precheck_only_propagates_a_precheck_failure(self):
        env = os.environ.copy()
        env["G1V3_BINARY"] = "/bin/false"
        result = subprocess.run(
            ["bash", str(V3_ROOT / "scripts" / "run_v3_force_matrix.sh"), "--precheck-only"],
            text=True,
            capture_output=True,
            env=env,
        )
        self.assertEqual(result.returncode, 3)


if __name__ == "__main__":
    unittest.main()
