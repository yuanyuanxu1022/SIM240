#!/usr/bin/env python3
"""A verification receipt is written once; rewriting needs ``--replace``.

The re-integration step is stubbed with a synthetic verification dict, so no
fields are integrated here and no physics runs.
"""
from __future__ import annotations

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import numpy as np

TESTS = Path(__file__).resolve().parent
PACKAGE = TESTS.parent
for _path in (str(PACKAGE), str(TESTS)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import _pkgcopy  # noqa: E402
import receipt  # noqa: E402
import verify_one  # noqa: E402

CASE = "h50_d25_T"
RUN_ID = f"{CASE}_20260101T000000Z_bbbbbbbb"


def synthetic_verification() -> dict:
    rows = [{"dx_nm": dx, "direction": "T", "section_count": 10,
             "K_recomputed_m3": 1.0e-23, "K_vs_solver_relative_difference": 0.0,
             "power_balance_recomputed_percent": 1e-3,
             "section_flux_spread_percent": 1e-3,
             "section_vs_volume_percent": 1e-3,
             "direct_relative_residual_recomputed": 1e-13,
             "wall_velocity_relative_max": 0.0,
             "periodic_velocity_relative_max_difference": 0.0,
             "pressure_periodic_relative_max_difference": 0.0,
             "pressure_mean_normalized": 0.0,
             "K_change_from_coarser_recomputed_percent": 0.0}
            for dx in (5.0, 2.5, 1.25)]
    return {"levels": rows, "problems": [], "diagnostics": [],
            "gate_scope_version": "test-scope"}


def build_case(root: Path) -> Path:
    case_dir = root / "results" / CASE
    case_dir.mkdir(parents=True)
    directory = root / "runs" / RUN_ID
    directory.mkdir(parents=True)
    levels = []
    points = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    triangles = np.array([[0], [1], [2]])
    for dx in (5.0, 2.5, 1.25):
        field = case_dir / f"dx_{dx:g}nm_fields.npz"
        np.savez_compressed(field, p=points, t=triangles)
        meta = {"case_id": CASE, "dx_nm": dx, "h_nm": 50.0, "d_nm": 25.0,
                "direction": "T", "P_nm": 240.0, "w_nm": 120.0, "K_m3": 1.0e-23,
                "field_file": field.name, "field_sha256": receipt.sha256_file(field)}
        json_path = case_dir / f"dx_{dx:g}nm.json"
        json_path.write_text(json.dumps(meta) + "\n")
        levels.append({"dx_nm": dx, "state": "SOLVED", "K_m3": 1.0e-23,
                       "json_file": json_path.name,
                       "json_sha256": receipt.sha256_file(json_path),
                       "field_file": field.name,
                       "field_sha256_solver": receipt.sha256_file(field),
                       **receipt.mesh_fingerprint(field)})
    receipt.atomic_write_json(directory / "SOLVE_RECEIPT.json", {
        "schema": receipt.SCHEMA_SOLVE, "run_id": RUN_ID, "case": CASE,
        "state": "SOLVED", "exit_code": 0,
        "release_sha256": receipt.release_digest(),
        "planned_levels_nm": [5.0, 2.5, 1.25], "levels": levels,
        "wall_seconds": 1.0, "peak_rss_kb": 1})
    return directory


class VerifyReceiptOnceTests(unittest.TestCase):
    def setUp(self):
        self.saved_argv = sys.argv

    def tearDown(self):
        sys.argv = self.saved_argv

    def _verify(self, directory, *extra):
        sys.argv = ["verify_one.py", "--run-dir", str(directory), *extra]
        stream = io.StringIO()
        with mock.patch.object(verify_one.verify_results, "verify_case",
                               return_value=synthetic_verification()):
            with redirect_stdout(stream):
                code = verify_one.main()
        return code, stream.getvalue()

    def test_second_verification_is_refused_unless_replaced(self):
        with _pkgcopy.PackageCopy() as root:
            directory = build_case(root)
            out = directory / "VERIFY_RECEIPT.json"

            code, _ = self._verify(directory)
            self.assertEqual(code, 0)
            self.assertTrue(out.exists())
            first_digest = receipt.sha256_file(out)
            first_bytes = out.read_bytes()

            code, output = self._verify(directory)
            self.assertEqual(code, receipt.EXIT_REFUSED_OVERWRITE)
            self.assertIn("written once", output)
            self.assertEqual(receipt.sha256_file(out), first_digest)
            self.assertEqual(out.read_bytes(), first_bytes)

            code, _ = self._verify(directory, "--replace")
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text())
            self.assertEqual(payload["replaces_sha256"], first_digest)
            self.assertNotEqual(receipt.sha256_file(out), first_digest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
