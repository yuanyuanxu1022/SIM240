import csv
import json
import math
from pathlib import Path
import tempfile
import unittest

from g5a_inputs import build_nine_cases, load_config, load_transport_cases


VALID_ROWS = [
    {"height_nm": 50.0, "R_parallel": 1.7524577489058236e19, "R_perp": 6.973942793067436e19,
     "K_parallel": 5.706271666888214e-23, "K_perp": 1.433909095144954e-23,
     "anisotropy": 3.9795212166579965},
    {"height_nm": 75.0, "R_parallel": 1.022241553800475e19, "R_perp": 2.280349074098442e19,
     "K_parallel": 9.782423697043172e-23, "K_perp": 4.3852935121144107e-23,
     "anisotropy": 2.2307340819991053},
    {"height_nm": 125.0, "R_parallel": 3.7632838400903424e18, "R_perp": 5.410847947764791e18,
     "K_parallel": 2.6572537243855455e-22, "K_perp": 1.8481391634985746e-22,
     "anisotropy": 1.4377995861281876},
]


class InputAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config_path = self.root / "g5a.json"
        self.csv_path = self.root / "G3_height_resistance.csv"
        self.config = {
            "schema_version": 1,
            "source_grid_dx_nm": 2.5,
            "transport_database": str(self.csv_path),
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

    def tearDown(self):
        self.tmp.cleanup()

    def write_config(self, **overrides):
        payload = dict(self.config)
        payload.update(overrides)
        self.config_path.write_text(json.dumps(payload), encoding="utf-8")

    def write_rows(self, rows):
        fields = ["height_nm", "R_parallel", "R_perp", "K_parallel", "K_perp", "anisotropy"]
        with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_config_rejects_wrong_source_grid_or_n(self):
        self.write_config(source_grid_dx_nm=5.0)
        with self.assertRaisesRegex(ValueError, "source_grid_dx_nm"):
            load_config(self.config_path)
        self.write_config(n_cells=201)
        with self.assertRaisesRegex(ValueError, "n_cells"):
            load_config(self.config_path)

    def test_valid_database_builds_exactly_nine_cases(self):
        self.write_config()
        self.write_rows(VALID_ROWS)
        config = load_config(self.config_path)
        rows = load_transport_cases(self.csv_path, config)
        cases = build_nine_cases(config, rows)
        self.assertEqual(len(cases), 9)
        self.assertEqual([case.model for case in cases].count("smooth"), 3)
        self.assertEqual([case.model for case in cases].count("ex240"), 6)

    def test_parallel_and_perpendicular_use_the_correct_columns(self):
        self.write_config()
        self.write_rows(VALID_ROWS)
        config = load_config(self.config_path)
        cases = build_nine_cases(config, load_transport_cases(self.csv_path, config))
        by_key = {(case.height_nm, case.direction): case for case in cases}
        self.assertEqual(by_key[(75.0, "parallel")].K_m3, VALID_ROWS[1]["K_parallel"])
        self.assertEqual(by_key[(75.0, "perpendicular")].K_m3, VALID_ROWS[1]["K_perp"])

    def test_duplicate_missing_extra_or_nonfinite_rows_fail(self):
        self.write_config()
        bad_nonfinite = [dict(row) for row in VALID_ROWS]
        bad_nonfinite[1]["K_parallel"] = float("nan")
        extra = dict(VALID_ROWS[0])
        extra["height_nm"] = 100.0
        fixtures = {
            "duplicate": VALID_ROWS + [dict(VALID_ROWS[1])],
            "missing": [VALID_ROWS[0], VALID_ROWS[2]],
            "extra": VALID_ROWS + [extra],
            "nonfinite": bad_nonfinite,
        }
        config = load_config(self.config_path)
        for name, rows in fixtures.items():
            with self.subTest(name=name):
                self.write_rows(rows)
                with self.assertRaises(ValueError):
                    load_transport_cases(self.csv_path, config)

    def test_rk_and_anisotropy_identity_failures_are_detected(self):
        self.write_config()
        config = load_config(self.config_path)
        bad_rk = [dict(row) for row in VALID_ROWS]
        bad_rk[0]["R_parallel"] *= 1.000001
        self.write_rows(bad_rk)
        with self.assertRaisesRegex(ValueError, "R_parallel.*K_parallel"):
            load_transport_cases(self.csv_path, config)
        bad_a = [dict(row) for row in VALID_ROWS]
        bad_a[2]["anisotropy"] *= 1.000001
        self.write_rows(bad_a)
        with self.assertRaisesRegex(ValueError, "anisotropy"):
            load_transport_cases(self.csv_path, config)


if __name__ == "__main__":
    unittest.main()
