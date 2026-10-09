#!/usr/bin/env python3
"""Reframe the verified Parallel velocity raster with publication labels.

The velocity field itself is copied from the original ParaView export without
altering its colours or inventing/interpolating simulation data.  This script
only replaces the surrounding layout, axes, title, and colour bar.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle
from matplotlib.ticker import FormatStrFormatter
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "output" / "Figure3_parallel_v1.png"
OUTPUT_PNG = ROOT / "figures" / "velocity" / "Figure3_3_Parallel_velocity_magnitude_final.png"
OUTPUT_PDF = ROOT / "figures" / "velocity" / "Figure3_3_Parallel_velocity_magnitude_final.pdf"

# Pixel bounds of the ParaView-rendered field in the source image.  PIL uses
# an exclusive right/lower edge, so this retains exactly 517 x 354 pixels.
FIELD_BOUNDS = (203, 40, 720, 394)


def main() -> None:
    field = Image.open(SOURCE).convert("RGB").crop(FIELD_BOUNDS)

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.linewidth": 0.8,
        }
    )

    fig, ax = plt.subplots(figsize=(8.0, 5.25), constrained_layout=True)
    ax.imshow(
        field,
        extent=(0.0, 240.0, 0.0, 175.0),
        origin="upper",
        interpolation="none",
        aspect="equal",
    )

    # Make the physical domain explicit without adding streamlines.
    ax.add_patch(
        Rectangle((0.0, 0.0), 240.0, 175.0, fill=False, edgecolor="black", linewidth=0.9)
    )
    ax.set_xlim(0.0, 240.0)
    ax.set_ylim(0.0, 175.0)
    ax.set_xticks([0, 60, 120, 180, 240])
    ax.set_yticks([0, 50, 100, 150, 175])
    ax.set_xlabel(r"Along-groove coordinate, $y$ (nm)")
    ax.set_ylabel(r"Wall-normal coordinate, $z$ (nm)")
    ax.tick_params(direction="out", length=4, width=0.8)

    ax.text(
        0.0,
        1.075,
        "(a) Parallel",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=12,
        fontweight="bold",
    )
    ax.text(
        0.5,
        1.075,
        "Main flow (+y)  →",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=12,
    )
    ax.text(
        1.0,
        1.075,
        r"Groove centre: $x=120$ nm",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=10,
    )

    sm = plt.cm.ScalarMappable(norm=Normalize(vmin=0.0, vmax=1.7e-4), cmap="viridis")
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.047, pad=0.045, shrink=0.82)
    cbar.set_label(r"Velocity magnitude, $|\mathbf{u}|$ (m s$^{-1}$)")
    cbar.set_ticks([0.0, 5.0e-5, 1.0e-4, 1.5e-4, 1.7e-4])
    cbar.ax.yaxis.set_major_formatter(FormatStrFormatter("%.1e"))
    cbar.outline.set_linewidth(0.8)

    OUTPUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PNG, dpi=300, facecolor="white")
    fig.savefig(OUTPUT_PDF, facecolor="white")
    plt.close(fig)

    print(OUTPUT_PNG)
    print(OUTPUT_PDF)


if __name__ == "__main__":
    main()
