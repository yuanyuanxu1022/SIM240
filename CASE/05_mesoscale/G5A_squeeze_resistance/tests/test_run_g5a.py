import csv
import json
import math
from pathlib import Path
import tempfile
import unittest

from run_g5a import main


VALID_ROWS = [
    [50.0, 1.7524577489058236e19, 6.973942793067436e19, 5.706271666888214e-23, 1.433909095144954e-23, 3.9795212166579965],
    [75.0, 1.022241553800475e19, 2.280349074098442e19, 9.782423697043172e-23, 4.3852935121144107e-23, 2.2307340819991053],
    [125.0, 3.7632838400903424e18, 5.410847947764791e18, 2.6572537243855455e-22, 1.8481391634985746e-22, 1.4377995861281876],
]


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "transport_database").mkdir()
        self.csv_path = self.root / "transport_database" / "G3_height_resistance.csv"
        self.config_path = self.root / "g5a.json"
        self.results_root = self.root / "results"
        self.write_rows(VALID_ROWS)
        config = {
            "schema_version": 1,
            "source_grid_dx_nm": 2.5,
            "transport_database": "transport_database/G3_height_resistance.csv",
            "heights_nm": [50.0, 75.0, 125.0],
            "length_m": 1e-3,
            "width_m": 1e-3,
            "mu_pa_s": 1e-3,
            "vp_m_s": 75e-9,
            "p_out_pa": 0.0,
            "n_cells": 401,
            "linearity_multipliers": [0.5, 1.0, 2.0],
            "thresholds": {
                "input_identity_relative": 1e-10,
                "symmetry_relative": 1e-12,
                "pmax_relative": 1e-6,
                "load_relative": 1e-4,
                "mass_relative": 1e-10,
                "linearity_relative": 1e-10,
                "direction_ratio_relative": 1e-4,
            },
        }
        self.config_path.write_text(json.dumps(config), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def write_rows(self, rows):
        fields = ["height_nm", "R_parallel", "R_perp", "K_parallel", "K_perp", "anisotropy"]
        with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(fields)
            writer.writerows(rows)

    def run_cli(self, run_id):
        return main([
            "--config", str(self.config_path),
            "--repo-root", str(self.root),
            "--results-root", str(self.results_root),
            "--run-id", run_id,
        ])

    def test_successful_run_writes_complete_evidence(self):
        self.assertEqual(self.run_cli("unit-test-pass"), 0)
        run_dir = self.results_root / "unit-test-pass"
        required = {
            "run.log", "exit_code.txt", "input_manifest.json", "case_results.csv",
            "pressure_profiles.csv", "validation_report.md",
            "Figure_G5_pressure_profiles.png", "Figure_G5_squeeze_impedance_vs_h.png",
            "Figure_G5_directional_ratio_vs_h.png",
        }
        self.assertTrue(required.issubset({path.name for path in run_dir.iterdir()}))
        with (run_dir / "case_results.csv").open(newline="", encoding="utf-8") as handle:
            self.assertEqual(len(list(csv.DictReader(handle))), 9)
        self.assertIn("RESULT_PASS: true", (run_dir / "validation_report.md").read_text(encoding="utf-8"))
        self.assertEqual((run_dir / "exit_code.txt").read_text(encoding="utf-8"), "0\n")

    def test_manifest_contains_input_hash_and_fixed_grid(self):
        self.assertEqual(self.run_cli("unit-test-manifest"), 0)
        manifest = json.loads((self.results_root / "unit-test-manifest" / "input_manifest.json").read_text(encoding="utf-8"))
        self.assertRegex(manifest["transport_database_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(manifest["source_grid_dx_nm"], 2.5)
        self.assertEqual(manifest["n_cells"], 401)
        self.assertEqual(manifest["heights_nm"], [50.0, 75.0, 125.0])

    def test_failed_input_gate_writes_nonzero_exit_and_no_pass(self):
        self.write_rows(VALID_ROWS + [VALID_ROWS[1]])
        code = self.run_cli("unit-test-fail")
        run_dir = self.results_root / "unit-test-fail"
        self.assertNotEqual(code, 0)
        self.assertNotEqual((run_dir / "exit_code.txt").read_text(encoding="utf-8"), "0\n")
        report = (run_dir / "validation_report.md").read_text(encoding="utf-8")
        self.assertNotIn("RESULT_PASS: true", report)

    def test_csv_outputs_are_finite_and_direction_ratios_close(self):
        self.assertEqual(self.run_cli("unit-test-ratios"), 0)
        with (self.results_root / "unit-test-ratios" / "case_results.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        numeric = ["K_m3", "pmax_num_Pa", "Fz_num_N", "CF_num_N_s_m", "Qout_m3_s", "mass_rel_error"]
        for row in rows:
            self.assertTrue(all(math.isfinite(float(row[key])) for key in numeric))
        by_key = {(float(row["height_nm"]), row["direction"]): row for row in rows}
        for height in (50.0, 75.0, 125.0):
            parallel = by_key[(height, "parallel")]
            perpendicular = by_key[(height, "perpendicular")]
            cf_ratio = float(perpendicular["CF_num_N_s_m"]) / float(parallel["CF_num_N_s_m"])
            k_ratio = float(parallel["K_m3"]) / float(perpendicular["K_m3"])
            self.assertLess(abs(cf_ratio / k_ratio - 1.0), 1e-4)


if __name__ == "__main__":
    unittest.main()
