#!/usr/bin/env python3
"""One attempt per case per release, unless a reason is written.

Nothing is solved: the first "attempt" is a hand-written run directory and the
second attempt's solver is stubbed to fail immediately, so the test proves the
guard rather than any physics.
"""
from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
PACKAGE = TESTS.parent
for _path in (str(PACKAGE), str(TESTS)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import _pkgcopy  # noqa: E402
import fem_pilot  # noqa: E402
import receipt  # noqa: E402
import run_one  # noqa: E402

CASE = "h50_d25_T"


def prior_attempt(root: Path) -> Path:
    directory = root / "runs" / f"{CASE}_20260101T000000Z_aaaaaaaa"
    directory.mkdir(parents=True)
    receipt.atomic_write_json(directory / "SOLVE_RECEIPT.json", {
        "schema": receipt.SCHEMA_SOLVE, "run_id": directory.name, "case": CASE,
        "state": "FAILED", "exit_code": receipt.EXIT_SOLVE_FAILED,
        "release_sha256": receipt.release_digest(),
        "planned_levels_nm": [5.0, 2.5, 1.25], "levels": [],
        "wall_seconds": 0.0, "peak_rss_kb": 1})
    return directory


class SingleAttemptTests(unittest.TestCase):
    def setUp(self):
        self.saved_argv = sys.argv
        self.authorization = mock.patch.object(
            receipt, "load_authorization",
            return_value={"release_sha256": receipt.release_digest(),
                          "granted_cases": [CASE]})
        self.authorization.start()

    def tearDown(self):
        self.authorization.stop()
        sys.argv = self.saved_argv

    def _run(self, *extra):
        sys.argv = ["run_one.py", "--case", CASE, "--execute", *extra]
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = run_one.main()
        return code, stream.getvalue()

    def test_second_attempt_is_refused_and_writes_nothing(self):
        with _pkgcopy.PackageCopy() as root:
            prior_attempt(root)
            before = sorted(path.name for path in (root / "runs").iterdir())
            code, output = self._run()
            self.assertEqual(code, receipt.EXIT_REFUSED_OVERWRITE)
            self.assertIn("one attempt per case per release", output)
            after = sorted(path.name for path in (root / "runs").iterdir())
            self.assertEqual(before, after)
            self.assertFalse((root / "results" / CASE).exists())

    def test_new_attempt_needs_a_reason_and_records_it(self):
        with _pkgcopy.PackageCopy() as root:
            prior_attempt(root)
            with mock.patch.object(fem_pilot, "run_level",
                                   side_effect=RuntimeError("stub solver")):
                code, _output = self._run("--new-attempt", "instrument repair")
            self.assertEqual(code, receipt.EXIT_SOLVE_FAILED)
            created = [path for path in (root / "runs").iterdir()
                       if path.name != f"{CASE}_20260101T000000Z_aaaaaaaa"]
            self.assertEqual(len(created), 1)
            record = __import__("json").loads(
                (created[0] / "SOLVE_RECEIPT.json").read_text())
            self.assertEqual(record["attempt"],
                             {"index": 2, "reason": "instrument repair"})
            self.assertEqual(record["exit_code"], receipt.EXIT_SOLVE_FAILED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
