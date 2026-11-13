#!/usr/bin/env python3
"""Fail if the test suite has touched the real package.

The suite copies the package into a temporary directory before writing
anything. This module records the real ``release_sha256`` and the contents of
``runs/`` and ``results/`` when it is first imported, and asserts all three are
unchanged both at the start and at the end of its own tests, so damage done by
an earlier module is caught rather than hidden.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
if str(PACKAGE) not in sys.path:
    sys.path.insert(0, str(PACKAGE))


def snapshot() -> dict:
    manifest = json.loads((PACKAGE / "release_manifest.json").read_text())
    listing = {}
    for name in ("runs", "results"):
        directory = PACKAGE / name
        listing[name] = sorted(
            str(path.relative_to(PACKAGE)) for path in directory.rglob("*")) \
            if directory.is_dir() else []
    return {"release_sha256": manifest["release_sha256"], **listing}


SNAPSHOT = snapshot()


def check() -> None:
    current = snapshot()
    if current != SNAPSHOT:
        raise AssertionError(
            "the real package changed during the tests: "
            f"before={SNAPSHOT} after={current}")


class IsolationTests(unittest.TestCase):
    def test_real_package_is_untouched_since_import(self):
        check()

    def test_manifest_digest_still_verifies(self):
        import receipt
        self.assertEqual(receipt.verify_release()["release_sha256"],
                         SNAPSHOT["release_sha256"])

    def test_solver_roots_follow_the_copy(self):
        """The solver carries its own ROOT, so patching receipt is not enough.

        A test that lets run_one reach the real solver must land in the copy.
        Otherwise an "unauthorised" case can solve physics into the real
        evidence tree while the assertion it was written for still looks like a
        mere exit-code mismatch.
        """
        import fem_pilot
        import receipt
        import verify_results
        import _pkgcopy

        with _pkgcopy.PackageCopy() as root:
            self.assertEqual(Path(fem_pilot.ROOT), root)
            self.assertEqual(Path(verify_results.ROOT), root)
            self.assertEqual(Path(receipt.RESULTS), root / "results")

    def test_copy_carries_no_live_authorization(self):
        import receipt
        import _pkgcopy

        with _pkgcopy.PackageCopy():
            self.assertFalse(receipt.AUTHORIZATION_PATH.exists())


def setUpModule():
    check()


def tearDownModule():
    check()
