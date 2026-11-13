#!/usr/bin/env python3
"""One unreadable or malformed case must not void the whole assessment table.

The stop rule requires every authorized point to carry a conclusion. A case
whose saved fields cannot be re-integrated therefore has to land in
NOT_RECONSTRUCTIBLE, and the remaining rows must still be written.

No physics runs here: the fixtures are hand-written JSON without fields.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
PACKAGE = TESTS.parent
for _path in (str(PACKAGE), str(TESTS)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import _pkgcopy  # noqa: E402
import assess  # noqa: E402
import receipt  # noqa: E402

CASE = "h50_d25_T"


def solve_receipt(case: str) -> dict:
    return {"schema": receipt.SCHEMA_SOLVE, "run_id": f"{case}_probe", "case": case,
            "state": "SOLVED", "exit_code": 0,
            "release_sha256": receipt.release_digest(),
            "planned_levels_nm": [5.0, 2.5, 1.25],
            "levels": [{"dx_nm": dx, "state": "SOLVED", "K_m3": 1e-24,
                        "json_file": f"dx_{dx:g}nm.json", "json_sha256": "a" * 64}
                       for dx in (5.0, 2.5, 1.25)],
            "wall_seconds": 1.0, "peak_rss_kb": 1}


class MalformedFieldsTests(unittest.TestCase):
    def test_unreintegratable_fields_do_not_raise(self):
        with _pkgcopy.PackageCopy() as root:
            directory = root / "runs" / f"{CASE}_20260101T000000Z_deadbeef"
            directory.mkdir(parents=True)
            solve = solve_receipt(CASE)
            receipt.atomic_write_json(directory / "SOLVE_RECEIPT.json", solve)
            verify = {"schema": receipt.SCHEMA_VERIFY, "case": CASE,
                      "solve_receipt_sha256": receipt.sha256_file(
                          directory / "SOLVE_RECEIPT.json"),
                      "solve_receipt_unchanged": True,
                      "release_sha256": receipt.release_digest(),
                      "numeric_verdict": "PASS", "gate_scope_version": "probe",
                      "levels": [], "reference_status": "REFERENCE_CANDIDATE"}
            receipt.atomic_write_json(directory / "VERIFY_RECEIPT.json", verify)
            # fields exist as metadata only: no arrays, no field_file key
            case_dir = root / "results" / CASE
            case_dir.mkdir(parents=True)
            for dx in (5.0, 2.5, 1.25):
                (case_dir / f"dx_{dx:g}nm.json").write_text(
                    json.dumps({"direction": "T", "h_nm": 50.0, "d_nm": 25.0}))
            label, verdict, problems = assess.classify(CASE, solve, verify, directory)
            self.assertEqual(label, "NOT_RECONSTRUCTIBLE")
            self.assertNotEqual(label, receipt.CANDIDATE)
            self.assertEqual(verdict, "NOT_EVALUATED")
            self.assertIn("could not be re-integrated", problems[0])

    def test_corrupt_solve_receipt_becomes_a_row_not_a_crash(self):
        with _pkgcopy.PackageCopy() as root:
            directory = root / "runs" / f"{CASE}_20260101T000000Z_deadbeef"
            directory.mkdir(parents=True)
            (directory / "SOLVE_RECEIPT.json").write_text("{not json")
            row = assess.collect(CASE, {"h_nm": 50.0, "d_nm": 25.0, "direction": "T"})
            self.assertEqual(row["reference_status"], "SOLVE_INCOMPLETE")
            self.assertIn("unreadable", row["assess_problems"])
            self.assertEqual(row["attempt_count"], 1)

    def test_corrupt_verify_receipt_is_treated_as_absent(self):
        with _pkgcopy.PackageCopy() as root:
            directory = root / "runs" / f"{CASE}_20260101T000000Z_deadbeef"
            directory.mkdir(parents=True)
            receipt.atomic_write_json(directory / "SOLVE_RECEIPT.json",
                                      solve_receipt(CASE))
            (directory / "VERIFY_RECEIPT.json").write_text("{not json")
            row = assess.collect(CASE, {"h_nm": 50.0, "d_nm": 25.0, "direction": "T"})
            self.assertEqual(row["reference_status"], "SOLVED_NOT_VERIFIED")
            self.assertNotEqual(row["reference_status"], receipt.CANDIDATE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
