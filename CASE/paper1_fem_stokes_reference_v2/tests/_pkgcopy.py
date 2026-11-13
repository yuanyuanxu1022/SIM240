#!/usr/bin/env python3
"""A throw-away copy of the package for tests that need to write files.

The real package must never be written by a test: not its manifest, not its
``runs/``, not its ``results/`` and certainly not an ``authorization.json``.
Each test that needs a writable package gets its own copy in a temporary
directory, and ``receipt``'s module-level paths are pointed at that copy for
the duration of the ``with`` block.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path
from unittest import mock

REAL_PACKAGE = Path(__file__).resolve().parent.parent
if str(REAL_PACKAGE) not in sys.path:
    sys.path.insert(0, str(REAL_PACKAGE))

IGNORE = shutil.ignore_patterns("results", "runs", "__pycache__", "tmp",
                                "STOP", "queue.pid", "queue.log",
                                "authorization.json")


class PackageCopy:
    """Copy the package, redirect ``receipt`` at it, clean up afterwards.

    ``authorization.json`` is deliberately *not* copied: a test that needs a
    grant writes its own. Copying the live grant would silently authorise cases
    the suite believes are refused.

    The solver modules carry their own ``ROOT`` constants, so pointing
    ``receipt`` at the copy is not enough on its own. Both are patched here, and
    the real tree is snapshotted so that any test which still finds a way to
    write into it fails loudly instead of leaving artefacts behind.
    """

    def __init__(self):
        import fem_pilot
        import receipt
        import verify_results

        self._receipt = receipt
        self._temporary = tempfile.TemporaryDirectory(prefix="fem_copy_")
        self.root = Path(self._temporary.name) / REAL_PACKAGE.name
        shutil.copytree(REAL_PACKAGE, self.root, ignore=IGNORE)
        (self.root / "results").mkdir()
        (self.root / "runs").mkdir()
        self._patches = [
            mock.patch.object(receipt, "PACKAGE", self.root),
            mock.patch.object(receipt, "MANIFEST_PATH",
                              self.root / "release_manifest.json"),
            mock.patch.object(receipt, "POINTS_PATH", self.root / "points.json"),
            mock.patch.object(receipt, "RULE_PATH",
                              self.root / "acceptance_rule.json"),
            mock.patch.object(receipt, "AUTHORIZATION_PATH",
                              self.root / "authorization.json"),
            mock.patch.object(receipt, "RESULTS", self.root / "results"),
            mock.patch.object(receipt, "RUNS", self.root / "runs"),
            mock.patch.object(receipt, "PROTOCOL_PATH", self.root / "PROTOCOL.md"),
            mock.patch.object(fem_pilot, "ROOT", self.root),
            mock.patch.object(verify_results, "ROOT", self.root),
        ]
        self._real_before = real_tree()

    def __enter__(self) -> Path:
        for patch in self._patches:
            patch.start()
        return self.root

    def __exit__(self, exc_type, exc, traceback) -> bool:
        after = real_tree()
        for patch in reversed(self._patches):
            patch.stop()
        self._temporary.cleanup()
        if after != self._real_before:
            raise AssertionError(
                "this test wrote into the real package's results/ or runs/: "
                f"before={self._real_before} after={after}")
        return False


def real_tree() -> dict:
    """Names and sizes under the real results/ and runs/, for the guard above."""
    listing = {}
    for name in ("results", "runs"):
        directory = REAL_PACKAGE / name
        listing[name] = sorted(
            (str(path.relative_to(REAL_PACKAGE)), path.stat().st_size)
            for path in directory.rglob("*") if path.is_file()) \
            if directory.is_dir() else []
    return listing
