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
                                "STOP", "queue.pid", "queue.log")


class PackageCopy:
    """Copy the package, redirect ``receipt`` at it, clean up afterwards."""

    def __init__(self):
        import receipt

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
        ]

    def __enter__(self) -> Path:
        for patch in self._patches:
            patch.start()
        return self.root

    def __exit__(self, exc_type, exc, traceback) -> bool:
        for patch in reversed(self._patches):
            patch.stop()
        self._temporary.cleanup()
        return False
