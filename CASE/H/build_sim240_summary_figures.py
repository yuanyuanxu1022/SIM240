#!/usr/bin/env python3
"""Create presentation-ready SIM240 summary figures from existing post-processing tables."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "results" / "tables"
FIG = ROOT / "results" / "figures"
CASES = (
    ("flat", "Flat", "#4C78A8"),
    ("along", "Along groove", "#59A14F"),
    ("across", "Across groove", "#E15759"),
)


def sweep_path(case: str) -> Path:
    return TABLE / f"sim240_{case if case == 'flat' else case + '_groove'}_sweep.csv"


def load_sweep(case: str) -> tuple[np.ndarray, np.ndarray]:
    with sweep_path(case).open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    q = np.array([float(row["q_in_m3_s"]) for row in rows])
    dp = np.array([float(row["delta_p_pa"]) for row in rows])
    return q, dp


def dp_q_comparison() -> None:
    fig, ax = plt.subplots(figsize=(7.8, 5.0))
    for case, label, color in CASES:
        q, dp = load_sweep(case)
        slope, intercept = np.polyfit(q, dp, 1)
        q_fit = np.linspace(0, q.max() * 1.05, 100)
        ax.plot(q * 1e17, dp / 1e3, "o", color=color, ms=6, label=f"{label} data")
        ax.plot(q_fit * 1e17, (slope * q_fit + intercept) / 1e3, "-", color=color, lw=2)
    ax.set(
        xlabel=r"Inlet flow rate, $Q_{in}$ ($10^{-17}$ m$^3$/s)",
        ylabel=r"Boundary pressure drop, $\Delta p$ (kPa)",
        title="SIM240 hydraulic response: boundary pressure drop versus inlet flow",
    )
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False, ncol=1)
    fig.tight_layout()
    fig.savefig(FIG / "sim240_dp_q_comparison.png", dpi=220)
    plt.close(fig)


def normalized_resistance() -> None:
    values = np.array([1.0, 0.37503405829586867, 0.8065940876696878])
    labels = ["Flat\n(R₀)", "Along\ngroove", "Across\ngroove"]
    colors = [case[2] for case in CASES]
    fig, ax = plt.subplots(figsize=(6.6, 5.0))
    bars = ax.bar(labels, values, color=colors, width=0.62)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.035, f"{value:.3f}", ha="center", va="bottom", fontsize=12, fontweight="bold")
    ax.axhline(1.0, color="#555555", lw=0.9, ls="--")
    ax.set(
        ylim=(0, 1.18),
        ylabel=r"Normalized fitted resistance, $R/R_0$",
        title="SIM240 normalized hydraulic resistance",
    )
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "sim240_normalized_resistance.png", dpi=220)
    plt.close(fig)


def velocity_comparison() -> None:
    panels = []
    for case, label, _ in CASES:
        image = Image.open(FIG / f"sim240_{case}_velocity.png").convert("RGB")
        panels.append((label, image))
    target_height = min(image.height for _, image in panels)
    resized = []
    for label, image in panels:
        width = round(image.width * target_height / image.height)
        resized.append((label, image.resize((width, target_height), Image.Resampling.LANCZOS)))
    gap = 16
    canvas = Image.new("RGB", (sum(image.width for _, image in resized) + gap * 2, target_height), "white")
    x = 0
    for _, image in resized:
        canvas.paste(image, (x, 0))
        x += image.width + gap
    canvas = ImageOps.expand(canvas, border=6, fill="white")
    canvas.save(FIG / "sim240_velocity_comparison.png")


def main() -> None:
    dp_q_comparison()
    normalized_resistance()
    velocity_comparison()
    print("Created sim240_dp_q_comparison.png, sim240_normalized_resistance.png, sim240_velocity_comparison.png")


if __name__ == "__main__":
    main()
