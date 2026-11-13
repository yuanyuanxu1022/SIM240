#!/usr/bin/env python3
"""Mechanics self-tests: no physics, no solver, no reference values.

Every case that needs to write a file works on a temporary copy of the package
(``tests/_pkgcopy.py``); the real package is never modified.

Run from the package directory:
    python -m unittest discover -s tests -v
"""
from __future__ import annotations

import io
import json
import shutil
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

TESTS = Path(__file__).resolve().parent
PACKAGE = TESTS.parent
for _path in (str(PACKAGE), str(TESTS)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import _pkgcopy  # noqa: E402
import assess  # noqa: E402
import receipt  # noqa: E402
import run_one  # noqa: E402


class ReleaseTests(unittest.TestCase):
    def test_manifest_present_and_verifies(self):
        self.assertTrue(receipt.MANIFEST_PATH.exists(),
                        "freeze_release.py --write must run before the tests")
        manifest = receipt.verify_release()
        self.assertEqual(len(manifest["release_sha256"]), 64)

    def test_drift_is_detected_and_recovered(self):
        with _pkgcopy.PackageCopy() as root:
            target = root / "README.md"
            original = target.read_bytes()
            try:
                target.write_bytes(original + b"\ndrift probe\n")
                with self.assertRaises(receipt.ReleaseDrift) as caught:
                    receipt.verify_release()
                self.assertIn("content drift", str(caught.exception))
            finally:
                target.write_bytes(original)
            receipt.verify_release()

    def test_added_file_is_detected(self):
        with _pkgcopy.PackageCopy() as root:
            target = root / "smuggled_helper.py"
            try:
                target.write_text("x = 1\n")
                with self.assertRaises(receipt.ReleaseDrift) as caught:
                    receipt.verify_release()
                self.assertIn("file added after freeze", str(caught.exception))
            finally:
                target.unlink(missing_ok=True)
            receipt.verify_release()

    def test_dependency_drift_is_detected(self):
        with _pkgcopy.PackageCopy() as root:
            manifest_path = root / "release_manifest.json"
            manifest = json.loads(manifest_path.read_text())
            original = manifest["environment"]["scipy"]
            try:
                manifest["environment"]["scipy"] = "0.0.0"
                body = {k: v for k, v in manifest.items() if k != "release_sha256"}
                manifest["release_sha256"] = receipt.digest_of(body)
                receipt.atomic_write_json(manifest_path, manifest)
                with self.assertRaises(receipt.ReleaseDrift) as caught:
                    receipt.verify_release()
                self.assertIn("dependency drift: scipy", str(caught.exception))
            finally:
                manifest["environment"]["scipy"] = original
                body = {k: v for k, v in manifest.items() if k != "release_sha256"}
                manifest["release_sha256"] = receipt.digest_of(body)
                receipt.atomic_write_json(manifest_path, manifest)
            receipt.verify_release()


class AuthorizationTests(unittest.TestCase):
    def test_missing_authorization_is_refused(self):
        with _pkgcopy.PackageCopy():
            receipt.AUTHORIZATION_PATH.unlink(missing_ok=True)
            with self.assertRaises(PermissionError):
                receipt.check_authorization("h50_d25_T")

    def test_non_eligible_point_is_refused(self):
        """Any status other than ELIGIBLE must be refused, whatever it is called.

        The assertion deliberately does not name the status: the h25 points moved
        from "pending scope" to "excluded by author decision" and the gate must
        not depend on which of those words is current.
        """
        with _pkgcopy.PackageCopy():
            receipt.atomic_write_json(receipt.AUTHORIZATION_PATH, {
                "schema": "sim240_fem_authorization/1",
                "release_sha256": receipt.release_digest(),
                "granted_cases": ["h25_d25_T"],
            })
            with self.assertRaises(PermissionError) as caught:
                receipt.check_authorization("h25_d25_T")
            message = str(caught.exception)
            self.assertIn("h25_d25_T", message)
            point = receipt.point_for_case("h25_d25_T")
            self.assertNotEqual(point["status"], "ELIGIBLE")
            self.assertIn(point["status"], message)

    def test_authorization_bound_to_other_release_is_refused(self):
        with _pkgcopy.PackageCopy():
            receipt.atomic_write_json(receipt.AUTHORIZATION_PATH, {
                "schema": "sim240_fem_authorization/1",
                "release_sha256": "0" * 64,
                "granted_cases": ["h50_d25_T"],
            })
            with self.assertRaises(PermissionError) as caught:
                receipt.check_authorization("h50_d25_T")
            self.assertIn("different release", str(caught.exception))

    def test_matching_authorization_passes(self):
        with _pkgcopy.PackageCopy():
            receipt.atomic_write_json(receipt.AUTHORIZATION_PATH, {
                "schema": "sim240_fem_authorization/1",
                "release_sha256": receipt.release_digest(),
                "granted_cases": ["h50_d25_T"],
            })
            clearance = receipt.check_authorization("h50_d25_T")
            self.assertEqual(clearance["point"]["case"], "h50_d25_T")


class EndToEndRefusalTests(unittest.TestCase):
    """Run the real entry point; it must refuse before any physics."""

    def setUp(self):
        self.saved_argv = sys.argv

    def tearDown(self):
        sys.argv = self.saved_argv

    def _run(self, case):
        sys.argv = ["run_one.py", "--case", case, "--execute"]
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = run_one.main()
        return code, stream.getvalue()

    def test_unauthorized_case_exits_5_and_writes_nothing(self):
        with _pkgcopy.PackageCopy() as root:
            code, output = self._run("h50_d25_T")
            self.assertEqual(code, receipt.EXIT_UNAUTHORIZED)
            self.assertIn("REFUSED not authorized", output)
            self.assertFalse((root / "results" / "h50_d25_T").exists())
            self.assertFalse(list((root / "runs").glob("h50_d25_T_*")))

    def test_blocked_scope_case_exits_5(self):
        with _pkgcopy.PackageCopy() as root:
            receipt.atomic_write_json(receipt.AUTHORIZATION_PATH, {
                "schema": "sim240_fem_authorization/1",
                "release_sha256": receipt.release_digest(),
                "granted_cases": ["h25_d25_T", "h25_d50_T"],
            })
            code, output = self._run("h25_d25_T")
            self.assertEqual(code, receipt.EXIT_UNAUTHORIZED)
            self.assertIn("h25_d25_T", output)
            self.assertIn(receipt.point_for_case("h25_d25_T")["status"], output)
            self.assertFalse((root / "results" / "h25_d25_T").exists())

    def test_existing_results_directory_is_refused(self):
        with _pkgcopy.PackageCopy() as root:
            receipt.atomic_write_json(receipt.AUTHORIZATION_PATH, {
                "schema": "sim240_fem_authorization/1",
                "release_sha256": receipt.release_digest(),
                "granted_cases": ["h50_d25_T"],
            })
            case_dir = root / "results" / "h50_d25_T"
            case_dir.mkdir()
            (case_dir / "stale.txt").write_text("marker\n")
            code, output = self._run("h50_d25_T")
            self.assertEqual(code, receipt.EXIT_REFUSED_OVERWRITE)
            self.assertIn("already exists", output)
            self.assertFalse(list((root / "runs").glob("h50_d25_T_*")))


class PrimitiveTests(unittest.TestCase):
    def test_atomic_write_digest_matches_bytes(self):
        with _pkgcopy.PackageCopy() as root:
            target = root / "tests" / "_probe.json"
            try:
                digest = receipt.atomic_write_json(target, {"b": 1, "a": [2, 3]})
                self.assertEqual(digest, receipt.sha256_file(target))
                self.assertEqual(json.loads(target.read_text()), {"b": 1, "a": [2, 3]})
                self.assertFalse(target.with_name("_probe.json.tmp").exists())
            finally:
                target.unlink(missing_ok=True)

    def test_mesh_fingerprint_is_order_stable(self):
        import numpy as np

        with _pkgcopy.PackageCopy() as root:
            path = root / "tests" / "_mesh.npz"
            try:
                points = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
                triangles = np.array([[0], [1], [2]])
                np.savez_compressed(path, p=points, t=triangles)
                first = receipt.mesh_fingerprint(path)
                second = receipt.mesh_fingerprint(path)
                self.assertEqual(first["mesh_sha256"], second["mesh_sha256"])
                self.assertEqual(first["mesh_vertices"], 3)
                self.assertEqual(first["mesh_triangles"], 1)
            finally:
                path.unlink(missing_ok=True)

    def test_run_ids_are_unique(self):
        ids = {receipt.new_run_id("h50_d25_T") for _ in range(50)}
        self.assertEqual(len(ids), 50)

    def test_beta_is_the_reconstructed_angle(self):
        self.assertAlmostEqual(assess.beta_deg(2.2472000768, 1.0), 23.988978, places=5)
        self.assertAlmostEqual(assess.beta_deg(16.4815390457, 1.0), 3.472105, places=5)


class ReceiptIntegrityTests(unittest.TestCase):
    def test_edited_solve_receipt_is_never_a_candidate(self):
        run_id = "zz_fake_case_20260101T000000Z_deadbeef"
        with _pkgcopy.PackageCopy() as root:
            directory = root / "runs" / run_id
            directory.mkdir(parents=True)
            try:
                levels = [{"dx_nm": dx, "state": "SOLVED", "K_m3": 1e-24,
                           "json_file": f"dx_{dx:g}nm.json", "json_sha256": "a" * 64,
                           "field_file": f"dx_{dx:g}nm_fields.npz",
                           "field_sha256_solver": "b" * 64}
                          for dx in (5.0, 2.5, 1.25)]
                solve = {"schema": receipt.SCHEMA_SOLVE, "run_id": run_id,
                         "case": "zz_fake_case", "state": "SOLVED", "exit_code": 0,
                         "release_sha256": receipt.release_digest(),
                         "planned_levels_nm": [5.0, 2.5, 1.25], "levels": levels,
                         "wall_seconds": 1.0, "peak_rss_kb": 1}
                receipt.atomic_write_json(directory / "SOLVE_RECEIPT.json", solve)
                receipt.atomic_write_json(directory / "VERIFY_RECEIPT.json", {
                    "schema": receipt.SCHEMA_VERIFY,
                    "solve_receipt_sha256": "0" * 64,
                    "numeric_verdict": "PASS",
                    "reference_status": "REFERENCE_CANDIDATE",
                    "actual_stop_reason": None,
                    "gate_scope_version": "probe",
                })
                row = assess.collect("zz_fake_case", {"h_nm": 1.0, "d_nm": 1.0})
                self.assertFalse(row["receipt_intact"])
                self.assertNotEqual(row["reference_status"], receipt.CANDIDATE)
                self.assertEqual(row["reference_status"], "NOT_RECONSTRUCTIBLE")
            finally:
                shutil.rmtree(directory, ignore_errors=True)

    def test_missing_run_is_reported_not_omitted(self):
        with _pkgcopy.PackageCopy():
            row = assess.collect("zz_never_ran", {"h_nm": 1.0, "d_nm": 1.0})
            self.assertEqual(row["reference_status"], "NOT_RUN")
            self.assertIsNone(row["run_id"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
