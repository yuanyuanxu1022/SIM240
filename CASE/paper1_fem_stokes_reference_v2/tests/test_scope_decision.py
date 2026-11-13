#!/usr/bin/env python3
"""The author's 2026-11-13 scope decision must stay visible and enforced.

Decision: "no further h25 work" means the whole thin-gap tier (h = 25 nm),
not only that h25/d100 is not refined further. Consequences asserted here:

  * exactly 12 points are ELIGIBLE and 2 are excluded;
  * the excluded pair is h25/d25_T and h25_d50_T;
  * h125/d25_T and h125/d50_T stay ELIGIBLE (d = 25 there is groove depth,
    not the gap, so they are not part of the thin-gap tier);
  * the decision text is recorded in points.json, not only in prose.

No physics runs.
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

import receipt  # noqa: E402

THIN_GAP = {"h25_d25_T", "h25_d50_T"}
GROOVE_DEPTH_25 = {"h125_d25_T", "h50_d25_T"}


class ScopeDecisionTests(unittest.TestCase):
    def setUp(self):
        self.points = receipt.load_points()

    def test_twelve_eligible_two_excluded(self):
        eligible = [p["case"] for p in self.points["points"] if p["status"] == "ELIGIBLE"]
        excluded = [p["case"] for p in self.points["points"] if p["status"] != "ELIGIBLE"]
        self.assertEqual(len(eligible), 12)
        self.assertEqual(sorted(excluded), sorted(THIN_GAP))
        self.assertEqual(len(self.points["points"]), 14)

    def test_thin_gap_points_are_not_eligible(self):
        for case in THIN_GAP:
            point = receipt.point_for_case(case)
            self.assertEqual(point["status"], "EXCLUDED_BY_AUTHOR_DECISION")
            self.assertIn("whole thin-gap", point["scope_note"])
            self.assertEqual(point["scope_decision"]["decided"], "2026-11-13")

    def test_groove_depth_25_is_not_confused_with_thin_gap(self):
        """d = 25 nm at h = 125 or h = 50 nm is groove depth, not a thin gap."""
        for case in GROOVE_DEPTH_25:
            self.assertEqual(receipt.point_for_case(case)["status"], "ELIGIBLE")
        for case in GROOVE_DEPTH_25:
            self.assertNotIn(receipt.point_for_case(case)["h_nm"], (25.0,))

    def test_decision_is_recorded_at_top_level(self):
        decision = self.points.get("scope_decision")
        self.assertIsNotNone(decision, "the decision must be machine-readable in points.json")
        self.assertEqual(decision["recorded"], "2026-11-13")
        self.assertIn("whole thin-gap", decision["answer"])
        self.assertIn("12 of its 14", decision["consequence"])

    def test_counting_note_matches_the_twelve_run_arithmetic(self):
        note = self.points["counting_note"]
        self.assertIn("22 + 12 = 34", note)
        self.assertIn("36 direction comparisons", note)
        self.assertIn("17 geometries, not 19", note)
        self.assertNotIn("22 + 14 = 36", note)


if __name__ == "__main__":
    unittest.main(verbosity=2)
