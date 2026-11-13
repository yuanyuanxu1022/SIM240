#!/usr/bin/env python3
"""Control-flow tests for run_one.py with a stubbed solver.

These tests prove the receipt machinery (started-before-solve, per-level append,
failure recording, exit codes) without solving any physics and without writing
into the real results/ or runs/ trees. They do not prove that a real solve
completes; that can only be shown by an authorized run.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

PACKAGE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PACKAGE))

import fem_pilot  # noqa: E402
import receipt  # noqa: E402
import run_one  # noqa: E402

CASE = "h50_d25_T"


def fake_run_level(case, h, d, direction, dx, overwrite=False):
    target = receipt.RESULTS / case
    target.mkdir(parents=True, exist_ok=True)
    points = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    triangles = np.array([[0], [1], [2]])
    field = target / f"dx_{dx:g}nm_fields.npz"
    np.savez_compressed(field, p=points, t=triangles, ux=np.zeros(3),
                        uz=np.zeros(3), pressure=np.array([]),
                        h=np.array(h), d=np.array(d),
                        direction=np.array(direction), dx_nm=np.array(dx))
    payload = {"case_id": case, "dx_nm": dx, "K_m3": 1.0e-23 * dx,
               "direct_relative_residual": 1e-13, "power_balance_percent": 1e-11,
               "section_flux_spread_percent": 1e-5,
               "section_vs_volume_percent": 1e-5, "section_count": 10,
               "mesh_triangles": 1, "p2_dofs": 3,
               "field_file": field.name,
               "field_sha256": receipt.sha256_file(field)}
    (target / f"dx_{dx:g}nm.json").write_text(json.dumps(payload) + "\n")
    return payload


class PlumbingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fem_plumbing_"))
        self.patches = [
            mock.patch.object(receipt, "RESULTS", self.tmp / "results"),
            mock.patch.object(receipt, "RUNS", self.tmp / "runs"),
            mock.patch.object(receipt, "load_authorization",
                              return_value={"release_sha256": receipt.release_digest(),
                                            "granted_cases": [CASE]}),
            mock.patch.object(fem_pilot, "summarize", return_value=[]),
        ]
        for patch in self.patches:
            patch.start()
        self.saved_argv = sys.argv

    def tearDown(self):
        sys.argv = self.saved_argv
        for patch in reversed(self.patches):
            patch.stop()
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_success_path_records_three_levels(self):
        sys.argv = ["run_one.py", "--case", CASE, "--execute"]
        with mock.patch.object(fem_pilot, "run_level", side_effect=fake_run_level):
            code = run_one.main()
        self.assertEqual(code, 0)
        receipts = list((self.tmp / "runs").glob(f"{CASE}_*/SOLVE_RECEIPT.json"))
        self.assertEqual(len(receipts), 1)
        record = json.loads(receipts[0].read_text())
        self.assertEqual(record["state"], "SOLVED")
        self.assertEqual([lvl["dx_nm"] for lvl in record["levels"]], [5.0, 2.5, 1.25])
        self.assertEqual(record["levels"][0]["dx_nm"], 5.0)
        for level in record["levels"]:
            self.assertEqual(level["state"], "SOLVED")
            self.assertIn("mesh_sha256", level)
            self.assertEqual(level["field_sha256_solver"], level["field_sha256_rehashed"])
            self.assertIsNotNone(level["json_sha256"])
        self.assertIsNotNone(record["peak_rss_kb"])
        self.assertEqual(record["command"]["argv"][0], "run_one.py")
        self.assertEqual(record["release_sha256"], receipt.release_digest())

    def test_started_state_precedes_any_level(self):
        seen = {}

        def probe(case, h, d, direction, dx, overwrite=False):
            if not seen:
                path = next((self.tmp / "runs").glob(f"{CASE}_*/SOLVE_RECEIPT.json"))
                payload = json.loads(path.read_text())
                seen["state_on_first_level"] = payload["state"]
                seen["levels_on_first_level"] = len(payload["levels"])
            return fake_run_level(case, h, d, direction, dx, overwrite)

        sys.argv = ["run_one.py", "--case", CASE, "--execute"]
        with mock.patch.object(fem_pilot, "run_level", side_effect=probe):
            self.assertEqual(run_one.main(), 0)
        self.assertEqual(seen["state_on_first_level"], "STARTED")
        self.assertEqual(seen["levels_on_first_level"], 0)

    def test_failure_is_recorded_and_not_retried(self):
        calls = []

        def exploding(case, h, d, direction, dx, overwrite=False):
            calls.append(dx)
            if dx == 2.5:
                raise RuntimeError("synthetic solver failure")
            return fake_run_level(case, h, d, direction, dx, overwrite)

        sys.argv = ["run_one.py", "--case", CASE, "--execute"]
        with mock.patch.object(fem_pilot, "run_level", side_effect=exploding):
            code = run_one.main()
        self.assertEqual(code, receipt.EXIT_SOLVE_FAILED)
        self.assertEqual(calls, [5.0, 2.5])
        record = json.loads(next((self.tmp / "runs").glob(
            f"{CASE}_*/SOLVE_RECEIPT.json")).read_text())
        self.assertEqual(record["state"], "FAILED")
        self.assertEqual(record["levels"][0]["state"], "SOLVED")
        self.assertEqual(record["levels"][1]["state"], "FAILED")
        self.assertIn("synthetic solver failure", record["error"]["message"])
        self.assertEqual(len(record["levels"]), 2)

    def test_level_budget_marks_timeout(self):
        def slow(case, h, d, direction, dx, overwrite=False):
            import time

            time.sleep(0.4)
            return fake_run_level(case, h, d, direction, dx, overwrite)

        sys.argv = ["run_one.py", "--case", CASE, "--execute",
                    "--level-budget", "0.05"]
        with mock.patch.object(fem_pilot, "run_level", side_effect=slow):
            code = run_one.main()
        self.assertEqual(code, receipt.EXIT_SOLVE_FAILED)
        record = json.loads(next((self.tmp / "runs").glob(
            f"{CASE}_*/SOLVE_RECEIPT.json")).read_text())
        self.assertEqual(record["state"], "TIMEOUT")
        self.assertEqual(record["levels"][0]["state"], "TIMEOUT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
