import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import run_fields_nx4 as runner


class RunnerTests(unittest.TestCase):
    def test_changed_hash_blocks_launch(self):
        with patch.object(runner, "sha", return_value="changed"):
            with self.assertRaises(RuntimeError):
                runner.verify_hashes({"/example": "approved"})

    def test_e_threshold(self):
        self.assertAlmostEqual(runner.e_ratio(100.0, 100.5), 0.005)
        with self.assertRaises(RuntimeError):
            runner.e_ratio(100.0, 102.0)

    def test_nonfinite_e_rejected(self):
        with self.assertRaises(RuntimeError):
            runner.e_ratio(100.0, float("nan"))

    def test_force_source_mapping(self):
        self.assertEqual(runner.source_for("a5e4").name, "g4_nx4_mpi_a5e4.cpp")
        self.assertEqual(runner.source_for("a1e5").name, "g4_nx4_mpi.cpp")

    def test_independent_failed_exit_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch = Path(tmp)
            with patch.object(runner.subprocess, "run", return_value=SimpleNamespace(returncode=3)):
                with self.assertRaises(RuntimeError):
                    runner.run_phase(batch, "a1e5", "P", "steady")
            self.assertEqual((batch / "runs/nx4_P_a1e5/steady/exit_code.txt").read_text(), "3\n")

    def test_bound_previous_batch_and_e_failure(self):
        def fixture(dest, nx):
            name = dest.parent.name.replace("nx4_", "nx2_")
            values = runner.parse_kv(runner.PREVIOUS / "runs" / name / "steady/result.txt")
            values["R_eff_Pa_s_per_m3"] = str(float(values["R_eff_Pa_s_per_m3"]) * 1.02)
            return values, {"data_rows": 19200}
        with tempfile.TemporaryDirectory() as tmp:
            batch = Path(tmp)
            with patch.object(runner, "audit_run", side_effect=fixture):
                with self.assertRaises(RuntimeError):
                    runner.postprocess(batch)
            self.assertTrue((batch / "E_ratios.csv").exists())
            self.assertIn(runner.PREVIOUS.name, (batch / "E_ratios.csv").read_text())
            self.assertFalse((batch / "G4_LEVEL_REPORT.md").exists())

    def test_success_report_retains_human_review_boundary(self):
        def fixture(dest, nx):
            name = dest.parent.name.replace("nx4_", "nx2_")
            values = runner.parse_kv(runner.PREVIOUS / "runs" / name / "steady/result.txt")
            return values, {"data_rows": 19200}
        with tempfile.TemporaryDirectory() as tmp:
            batch = Path(tmp)
            with patch.object(runner, "audit_run", side_effect=fixture):
                runner.postprocess(batch)
            report = (batch / "G4_LEVEL_REPORT.md").read_text()
            self.assertIn("review: pending", report)
            self.assertIn("not physical representative-scale convergence", report)
            self.assertTrue((batch / "FIELD_OUTPUT_AUDIT.json").exists())


if __name__ == "__main__":
    unittest.main()
