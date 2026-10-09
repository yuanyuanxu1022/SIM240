#!/usr/bin/env python3

import unittest

from extract_g3_height_resistance import canonical_resistance, pair_by_height


class PairByHeightTests(unittest.TestCase):
    def test_recorded_resistance_precedes_section_flow_fallback(self) -> None:
        values = {"R_eff_Pa_s_per_m3": "2.5"}

        resistance = canonical_resistance(values, pressure_drop=10.0, flow_rate=2.0)

        self.assertEqual(resistance, 2.5)

    def test_pairs_directions_and_computes_mobility_anisotropy(self) -> None:
        rows = [
            {
                "height_nm": 50.0,
                "direction": "parallel",
                "resistance_Pa_s_per_m3": 2.0,
                "mobility_m3": 8.0,
            },
            {
                "height_nm": 50.0,
                "direction": "perpendicular",
                "resistance_Pa_s_per_m3": 8.0,
                "mobility_m3": 2.0,
            },
        ]

        paired = pair_by_height(rows)

        self.assertEqual(
            paired,
            [
                {
                    "height_nm": 50.0,
                    "R_parallel": 2.0,
                    "R_perp": 8.0,
                    "K_parallel": 8.0,
                    "K_perp": 2.0,
                    "anisotropy": 4.0,
                }
            ],
        )

    def test_rejects_height_without_both_directions(self) -> None:
        rows = [
            {
                "height_nm": 75.0,
                "direction": "parallel",
                "resistance_Pa_s_per_m3": 2.0,
                "mobility_m3": 8.0,
            }
        ]

        with self.assertRaisesRegex(ValueError, "missing perpendicular"):
            pair_by_height(rows)


if __name__ == "__main__":
    unittest.main()
