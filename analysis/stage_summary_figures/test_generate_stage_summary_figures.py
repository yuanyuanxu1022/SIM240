#!/usr/bin/env python3
"""Behavior tests for the stage-summary figure generator."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

import generate_stage_summary_figures as figures


class TransportDataTests(unittest.TestCase):
    def test_resistance_uses_dynamic_viscosity_over_mobility(self) -> None:
        source = pd.DataFrame(
            {
                "height_nm": [75.0],
                "K_parallel": [1.0e-22],
                "K_perp": [4.0e-23],
                "R_parallel": [1.0e19],
                "R_perp": [2.5e19],
                "anisotropy": [2.5],
            }
        )

        checked = figures.validate_transport_data(source, viscosity_pa_s=1.0e-3)

        self.assertAlmostEqual(checked.loc[0, "R_parallel"], 1.0e19)
        self.assertAlmostEqual(checked.loc[0, "R_perp"], 2.5e19)
        self.assertAlmostEqual(checked.loc[0, "anisotropy"], 2.5)

    def test_inconsistent_resistance_is_rejected(self) -> None:
        source = pd.DataFrame(
            {
                "height_nm": [75.0],
                "K_parallel": [1.0e-22],
                "K_perp": [4.0e-23],
                "R_parallel": [1.0e22],
                "R_perp": [2.5e22],
                "anisotropy": [2.5],
            }
        )

        with self.assertRaisesRegex(ValueError, "R_parallel"):
            figures.validate_transport_data(source, viscosity_pa_s=1.0e-3)


class FigureOutputTests(unittest.TestCase):
    def test_generator_writes_five_png_and_five_pdf_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            figures.generate_all(output)

            expected_stems = {
                "Figure_1_research_chain",
                "Figure_2_EX240_geometry_directions",
                "Figure_3_1_G2_force_flux_linearity",
                "Figure_3_2_height_resistance_anisotropy",
                "Figure_3_boundary_and_data_transfer",
            }
            self.assertEqual(
                {path.stem for path in output.glob("*.png")}, expected_stems
            )
            self.assertEqual(
                {path.stem for path in output.glob("*.pdf")}, expected_stems
            )
            for path in output.glob("*.*"):
                self.assertGreater(path.stat().st_size, 10_000)


if __name__ == "__main__":
    unittest.main()
