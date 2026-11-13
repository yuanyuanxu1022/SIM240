#!/usr/bin/env python3
"""A fabricated pair of receipts must never become a reference candidate.

No fields are read and no physics runs: the point is only that the assessor
recomputes and therefore cannot be talked into a label by a receipt that says
so itself.
"""
from __future__ import annotations

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


def synthetic(case: str, digest: str):
    levels = [{"dx_nm": dx, "state": "SOLVED", "K_m3": 1e-24,
               "json_file": f"dx_{dx:g}nm.json", "json_sha256": "a" * 64,
               "field_file": f"dx_{dx:g}nm_fields.npz",
               "field_sha256_solver": "b" * 64}
              for dx in (5.0, 2.5, 1.25)]
    solve = {"schema": receipt.SCHEMA_SOLVE, "run_id": f"{case}_probe", "case": case,
             "state": "SOLVED", "exit_code": 0,
             "release_sha256": receipt.release_digest(),
             "planned_levels_nm": [5.0, 2.5, 1.25], "levels": levels,
             "wall_seconds": 1.0, "peak_rss_kb": 1}
    verify = {"schema": receipt.SCHEMA_VERIFY, "case": case,
              "solve_receipt_sha256": digest, "solve_receipt_unchanged": True,
              "release_sha256": receipt.release_digest(),
              "numeric_verdict": "PASS", "gate_scope_version": "probe",
              "levels": [], "reference_status": "REFERENCE_CANDIDATE",
              "actual_stop_reason": None}
    return solve, verify


class FabricatedReceiptTests(unittest.TestCase):
    def test_self_declared_candidate_is_not_a_candidate(self):
        with _pkgcopy.PackageCopy() as root:
            directory = root / "runs" / f"{CASE}_20260101T000000Z_deadbeef"
            directory.mkdir(parents=True)
            solve, verify = synthetic(CASE, "0" * 64)
            receipt.atomic_write_json(directory / "SOLVE_RECEIPT.json", solve)
            receipt.atomic_write_json(directory / "VERIFY_RECEIPT.json", verify)
            self.assertFalse((root / "results" / CASE).exists(),
                             "this test must not create a results directory")
            label, verdict, problems = assess.classify(CASE, solve, verify, directory)
            self.assertEqual(label, "NOT_RECONSTRUCTIBLE")
            self.assertNotEqual(label, receipt.CANDIDATE)
            self.assertEqual(verdict, "NOT_EVALUATED")
            self.assertIn("results directory is absent", problems[0])

    def test_wrong_solve_digest_is_not_a_candidate(self):
        with _pkgcopy.PackageCopy() as root:
            directory = root / "runs" / f"{CASE}_20260101T000000Z_deadbeef"
            directory.mkdir(parents=True)
            solve, verify = synthetic(CASE, "0" * 64)
            receipt.atomic_write_json(directory / "SOLVE_RECEIPT.json", solve)
            receipt.atomic_write_json(directory / "VERIFY_RECEIPT.json", verify)
            verify["solve_receipt_sha256"] = receipt.sha256_file(
                directory / "SOLVE_RECEIPT.json")
            label, _verdict, _problems = assess.classify(CASE, solve, verify, directory)
            self.assertNotEqual(label, receipt.CANDIDATE)
            self.assertEqual(label, "NOT_RECONSTRUCTIBLE")

    def test_solve_incomplete_and_unverified_are_labelled_honestly(self):
        with _pkgcopy.PackageCopy() as root:
            directory = root / "runs" / f"{CASE}_20260101T000000Z_deadbeef"
            directory.mkdir(parents=True)
            solve, verify = synthetic(CASE, "0" * 64)
            solve["state"] = "FAILED"
            receipt.atomic_write_json(directory / "SOLVE_RECEIPT.json", solve)
            label, _verdict, _problems = assess.classify(CASE, solve, None, directory)
            self.assertEqual(label, "SOLVE_INCOMPLETE")

            solve["state"] = "SOLVED"
            label, _verdict, problems = assess.classify(CASE, solve, None, directory)
            self.assertEqual(label, "SOLVED_NOT_VERIFIED")
            self.assertNotEqual(label, "NOT_RUN")


if __name__ == "__main__":
    unittest.main(verbosity=2)
