#!/usr/bin/env python3
"""Tests for the two additive checks applied by verify_one.py.

Synthetic level dicts only; no fields are read.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PACKAGE))

import verify_one  # noqa: E402


def level(dx, direction="T", count=10, power=1e-10):
    return {"dx_nm": dx, "direction": direction, "section_count": count,
            "power_balance_recomputed_percent": power,
            "K_recomputed_m3": 1e-23}


class AdditiveGateTests(unittest.TestCase):
    def test_clean_case_passes(self):
        problems = verify_one.additive_problems(
            {"levels": [level(5.0), level(2.5), level(1.25)]})
        self.assertEqual(problems, [])

    def test_nan_is_not_silently_accepted(self):
        rows = [level(5.0), level(2.5), level(1.25, power=float("nan"))]
        problems = verify_one.additive_problems({"levels": rows})
        self.assertEqual(len(problems), 1)
        self.assertIn("non-finite", problems[0])
        self.assertIn("power_balance_recomputed_percent", problems[0])

    def test_infinite_value_is_rejected(self):
        rows = [level(5.0), level(2.5), level(1.25)]
        rows[2]["K_recomputed_m3"] = float("inf")
        problems = verify_one.additive_problems({"levels": rows})
        self.assertEqual(len(problems), 1)
        self.assertIn("K_recomputed_m3", problems[0])

    def test_section_count_is_checked_on_the_finest_level_only(self):
        rows = [level(5.0, count=4), level(2.5, count=4), level(1.25, count=10)]
        self.assertEqual(verify_one.additive_problems({"levels": rows}), [])

    def test_too_few_sections_fails(self):
        rows = [level(5.0), level(2.5), level(1.25, count=8)]
        problems = verify_one.additive_problems({"levels": rows})
        self.assertEqual(len(problems), 1)
        self.assertIn("at least 9", problems[0])

    def test_along_groove_case_is_not_subject_to_section_count(self):
        rows = [level(5.0, direction="P", count=0),
                level(2.5, direction="P", count=0),
                level(1.25, direction="P", count=0)]
        self.assertEqual(verify_one.additive_problems({"levels": rows}), [])

    def test_missing_section_count_fails(self):
        rows = [level(5.0), level(2.5), level(1.25, count=None)]
        problems = verify_one.additive_problems({"levels": rows})
        self.assertEqual(len(problems), 1)
        self.assertIn("section count missing", problems[0])

    def test_no_levels_is_reported(self):
        self.assertEqual(verify_one.additive_problems({"levels": []}),
                         ["no level data to check"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
