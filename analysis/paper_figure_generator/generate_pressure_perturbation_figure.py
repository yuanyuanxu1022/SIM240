#!/usr/bin/env python3
"""Generate the paired Fig. 3-5 pressure-perturbation panels.

The source is the solver-written x-z mid-plane CSV, not a re-run or a
hard-coded pressure offset.  Both directions are centered with the fluid-node
mean of the same slice and share one dimensional color scale.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize


FIELD_COLUMNS = ("x", "z", "pressure", "material")
DEFAULT_VLIM_PA = 11.0
PRESSURE_CMAP = plt.get_cmap("coolwarm").copy()
PRESSURE_CMAP = PRESSURE_CMAP.with_extremes(bad="white")


def load_field_slice(path: Path) -> dict[str, np.ndarray]:
    """Load fluid rows from a solver ``field_slice.csv``."""
    rows: list[tuple[float, float, float, int]] = []
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        missing = set(FIELD_COLUMNS) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"missing columns in {path}: {sorted(missing)}")
        for row in reader:
            if int(float(row["material"])) != 1:
                continue
            rows.append(
                (
                    float(row["x"]),
                    float(row["z"]),
                    float(row["pressure"]),
                    1,
                )
            )
    if not rows:
        raise ValueError(f"no material=1 rows in {path}")
    values = np.asarray(rows, dtype=float)
    return {
        "x": values[:, 0],
        "z": values[:, 1],
        "pressure": values[:, 2],
    }


def center_pressure(data: dict[str, np.ndarray]) -> tuple[float, np.ndarray]:
    """Return the fluid-slice mean and ``p' = p - <p>``."""
    pressure = np.asarray(data["pressure"], dtype=float)
    mean = float(np.mean(pressure))
    return mean, pressure - mean


def validate_common_grid(
    parallel: dict[str, np.ndarray], perpendicular: dict[str, np.ndarray]
) -> None:
    """Ensure both panels are sampled on the same x-z coordinates."""
    parallel_grid = np.column_stack((parallel["x"], parallel["z"]))
    perpendicular_grid = np.column_stack((perpendicular["x"], perpendicular["z"]))
    if parallel_grid.shape != perpendicular_grid.shape or not np.allclose(
        parallel_grid, perpendicular_grid, rtol=0.0, atol=1.0e-15
    ):
        raise ValueError("Parallel and Perpendicular do not share a common x-z grid")


def _edges(values: np.ndarray) -> np.ndarray:
    unique = np.unique(values)
    if unique.size < 2:
        raise ValueError("a pressure slice needs at least two coordinates per axis")
    spacing = np.diff(unique)
    if not np.allclose(spacing, spacing[0], rtol=1.0e-10, atol=1.0e-18):
        raise ValueError("pressure slice coordinates are not uniformly spaced")
    half = spacing[0] / 2.0
    return np.concatenate(([unique[0] - half], unique + half))


def _grid(data: dict[str, np.ndarray], perturbation: np.ndarray):
    xs = np.unique(data["x"])
    zs = np.unique(data["z"])
    field = np.full((zs.size, xs.size), np.nan)
    x_index = {value: i for i, value in enumerate(xs)}
    z_index = {value: i for i, value in enumerate(zs)}
    for x, z, value in zip(data["x"], data["z"], perturbation):
        field[z_index[z], x_index[x]] = value
    return xs, zs, field


def _draw_panel(ax, data, perturbation, title, direction, norm):
    xs, zs, field = _grid(data, perturbation)
    mesh = ax.pcolormesh(
        _edges(xs) * 1e9,
        _edges(zs) * 1e9,
        field,
        cmap=PRESSURE_CMAP,
        norm=norm,
        shading="flat",
        rasterized=True,
    )
    ax.set_aspect("equal")
    ax.set_xlim(0, 240)
    ax.set_ylim(0, 175)
    ax.set_xlabel("x (nm)")
    ax.set_ylabel("z (nm)")
    ax.set_title(title, loc="left", fontweight="bold")
    ax.text(
        0.98,
        0.96,
        direction,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=10,
        bbox={"facecolor": "white", "edgecolor": "0.3", "alpha": 0.85, "pad": 3},
    )
    ax.text(
        0.02,
        0.04,
        rf"$\max |p'|={np.nanmax(np.abs(perturbation)):.3g}\ \mathrm{{Pa}}$",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 2},
    )
    return mesh


def generate_figure(
    parallel_csv: Path,
    perpendicular_csv: Path,
    combined_png: Path,
    parallel_png: Path,
    combined_pdf: Path | None = None,
    vlim_pa: float = DEFAULT_VLIM_PA,
) -> dict[str, float]:
    parallel = load_field_slice(parallel_csv)
    perpendicular = load_field_slice(perpendicular_csv)
    validate_common_grid(parallel, perpendicular)
    parallel_mean, parallel_perturbation = center_pressure(parallel)
    perpendicular_mean, perpendicular_perturbation = center_pressure(perpendicular)

    norm = Normalize(vmin=-vlim_pa, vmax=vlim_pa)
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 5.0), constrained_layout=False)
    _draw_panel(
        axes[0], parallel, parallel_perturbation, "(a) Parallel", "main flow: +y (out of plane)", norm
    )
    _draw_panel(
        axes[1],
        perpendicular,
        perpendicular_perturbation,
        "(b) Perpendicular",
        "main flow: +x  →",
        norm,
    )
    fig.suptitle(
        r"Local pressure perturbation in one periodic unit cell, $p'=p-\langle p\rangle_{x\text{-}z\,\mathrm{slice}}$",
        y=0.99,
        fontsize=13,
    )
    cbar = fig.colorbar(
        plt.cm.ScalarMappable(norm=norm, cmap=PRESSURE_CMAP),
        ax=axes,
        fraction=0.046,
        pad=0.04,
    )
    cbar.set_label("local pressure perturbation $p'$ (Pa)")
    fig.text(
        0.5,
        0.005,
        "Periodic-cell local redistribution only; p' range is not a macroscopic pressure drop.",
        ha="center",
        va="bottom",
        fontsize=9,
    )
    combined_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(combined_png, dpi=300, facecolor="white", bbox_inches="tight")
    if combined_pdf is not None:
        combined_pdf.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(combined_pdf, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.6, 5.0), constrained_layout=False)
    _draw_panel(ax, parallel, parallel_perturbation, "Parallel local pressure perturbation", "main flow: +y (out of plane)", norm)
    fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=PRESSURE_CMAP), ax=ax, fraction=0.046, pad=0.04).set_label(
        "local pressure perturbation $p'$ (Pa)"
    )
    fig.text(
        0.5,
        0.005,
        "Periodic-cell local redistribution only; p' range is not a macroscopic pressure drop.",
        ha="center",
        va="bottom",
        fontsize=9,
    )
    parallel_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(parallel_png, dpi=300, facecolor="white", bbox_inches="tight")
    plt.close(fig)

    return {
        "parallel_mean_pa": parallel_mean,
        "parallel_max_abs_perturbation_pa": float(np.max(np.abs(parallel_perturbation))),
        "perpendicular_mean_pa": perpendicular_mean,
        "perpendicular_max_abs_perturbation_pa": float(np.max(np.abs(perpendicular_perturbation))),
        "shared_vlim_pa": float(vlim_pa),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parallel-csv", type=Path, required=True)
    parser.add_argument("--perpendicular-csv", type=Path, required=True)
    parser.add_argument("--combined-png", type=Path, required=True)
    parser.add_argument("--parallel-png", type=Path, required=True)
    parser.add_argument("--combined-pdf", type=Path)
    parser.add_argument("--vlim-pa", type=float, default=DEFAULT_VLIM_PA)
    args = parser.parse_args()
    stats = generate_figure(**vars(args))
    for key, value in stats.items():
        print(f"{key}={value:.12g}")


if __name__ == "__main__":
    main()
