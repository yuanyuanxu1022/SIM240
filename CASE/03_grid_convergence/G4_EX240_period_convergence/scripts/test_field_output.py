#!/usr/bin/env python3
"""Regression: numeric PASS must not hide a header-only field export."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from check_field_slice import check_field_slice

SCRIPTS = Path(__file__).resolve().parent
CASE = SCRIPTS.parent
ARCHIVE = CASE / "results/g4_period_nx2_20261011T133304+0800"


class OutputEvidenceTests(unittest.TestCase):
    def test_header_only_fields_block_batch_acceptance(self):
        processor = Path(os.environ.get(
            "G4_POSTPROCESSOR", SCRIPTS / "postprocess_period_fields.py"))
        with tempfile.TemporaryDirectory(prefix="g4_field_regression_") as tmp:
            batch = Path(tmp) / "g4_period_nx2_test"
            for source in sorted((ARCHIVE / "runs").glob("*/steady")):
                dest = batch / "runs" / source.parent.name / "steady"
                dest.mkdir(parents=True)
                for name in ("result.txt", "exit_code.txt", "field_slice.csv"):
                    shutil.copyfile(source / name, dest / name)
            run = subprocess.run([sys.executable, str(processor), str(batch)],
                                 capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0,
                                "numeric PASS incorrectly accepted empty field CSVs")
            self.assertFalse((batch / "G4_LEVEL_REPORT.md").exists(),
                             "incomplete output produced a success report")

    def test_single_rank_reference_has_complete_9600_point_slice(self):
        reference = CASE / ("results/g4_scaling_nx2_20261010T201006+0800/"
                            "serial_1rank/steady/field_slice.csv")
        self.assertEqual(check_field_slice(reference, 2)["data_rows"], 9600)

    def test_duplicate_point_is_rejected_even_with_correct_row_count(self):
        reference = CASE / ("results/g4_scaling_nx2_20261010T201006+0800/"
                            "serial_1rank/steady/field_slice.csv")
        lines = reference.read_text().splitlines()
        with tempfile.TemporaryDirectory(prefix="g4_duplicate_") as tmp:
            bad = Path(tmp) / "field_slice.csv"
            bad.write_text("\n".join(lines[:-1] + [lines[1]]) + "\n")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                check_field_slice(bad, 2)

    def test_nonfinite_field_value_is_rejected(self):
        reference = CASE / ("results/g4_scaling_nx2_20261010T201006+0800/"
                            "serial_1rank/steady/field_slice.csv")
        lines = reference.read_text().splitlines()
        row = lines[1].split(",")
        row[7] = "nan"
        with tempfile.TemporaryDirectory(prefix="g4_nonfinite_") as tmp:
            bad = Path(tmp) / "field_slice.csv"
            bad.write_text("\n".join([lines[0], ",".join(row)] + lines[2:]) + "\n")
            with self.assertRaisesRegex(ValueError, "nonfinite"):
                check_field_slice(bad, 2)

    def test_one_missing_point_fails_exact_row_count(self):
        reference = CASE / ("results/g4_scaling_nx2_20261010T201006+0800/"
                            "serial_1rank/steady/field_slice.csv")
        with tempfile.TemporaryDirectory(prefix="g4_truncated_") as tmp:
            bad = Path(tmp) / "field_slice.csv"
            bad.write_text("\n".join(reference.read_text().splitlines()[:-1]) + "\n")
            with self.assertRaisesRegex(ValueError, "data_rows=9599, expected=9600"):
                check_field_slice(bad, 2)


if __name__ == "__main__":
    unittest.main()
