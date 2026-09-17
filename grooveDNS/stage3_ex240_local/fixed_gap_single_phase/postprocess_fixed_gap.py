#!/usr/bin/env python3
"""Postprocess the frozen SIM-EC1XT240 fixed-gap single-phase runs."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
GAPS = (75, 70, 65)
MODES = ("x", "y")


def read_result(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def run_dir(gap: int, mode: str) -> Path:
    return ROOT / "output" / f"sim_ec1xt240_h{gap}_dx5_a1e5_{mode}_20260909"


rows: list[dict[str, str | float | int]] = []
for gap in GAPS:
    for mode in MODES:
        values = read_result(run_dir(gap, mode) / "result.txt")
        j = [float(v) for v in values["J_m2_s"].split(",")]
        q = [float(v) for v in values["Q_sections_m3_s"].split(",")]
        pressure = [float(v) for v in values["pressure_range_Pa"].split(",")]
        rows.append(
            {
                "run_id": values["run_id"],
                "gap_nm": gap,
                "direction": mode.upper(),
                "steps": int(values["steps_completed"]),
                "fluid_nodes": int(values["fluid_nodes"]),
                "fluid_volume_m3": float(values["fluid_volume_m3"]),
                "H_ref_nm": float(values["H_ref_m"]) * 1e9,
                "J_main_m2_s": j[0 if mode == "x" else 1],
                "K_main_m3": float(values["K_main_m3"]),
                "B_main_nm2": float(values["B_main_m2"]) * 1e18,
                "R_J_Pa_s_per_m3": float(values["R_J_Pa_s_per_m3"]),
                "R_U_Pa_s_per_m2": float(values["R_U_Pa_s_per_m2"]),
                "pressure_min_Pa": pressure[0],
                "pressure_max_Pa": pressure[1],
                "max_mass_abs_relative": float(values["max_mass_abs_relative"]),
                "max_density_deviation": float(values["max_density_deviation"]),
                "max_speed_m_s": float(values["max_speed_m_s"]),
                "Re_max_Href": float(values["Re_max_Href"]),
                "Mach_max": float(values["Mach_max"]),
                "Q_section1_m3_s": q[0],
                "Q_section2_m3_s": q[1],
                "section_relative_difference": float(values["section_relative_difference"]),
                "PASS": values["PASS"],
            }
        )

summary = ROOT / "fixed_gap_single_phase_summary.csv"
with summary.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

figures = ROOT / "figures"
figures.mkdir(exist_ok=True)


def save_figure(name: str) -> None:
    plt.tight_layout()
    plt.savefig(figures / f"{name}.png", dpi=300)
    plt.savefig(figures / f"{name}.pdf")
    plt.close()


fig, ax = plt.subplots(figsize=(6.2, 4.2))
for mode, marker in (("X", "o"), ("Y", "s")):
    selected = sorted((r for r in rows if r["direction"] == mode), key=lambda r: r["gap_nm"])
    ax.plot([r["gap_nm"] for r in selected], [r["R_J_Pa_s_per_m3"] for r in selected], marker=marker, label=mode)
ax.set_xlabel("Fixed mesa gap h (nm)")
ax.set_ylabel(r"Depth-integrated resistance $R_J$ (Pa s m$^{-3}$)")
ax.grid(alpha=0.25)
ax.legend(title="Drive")
save_figure("fixed_gap_flow_resistance")

fig, axes = plt.subplots(3, 1, figsize=(6.4, 7.2), sharex=True)
for mode, marker in (("X", "o"), ("Y", "s")):
    selected = sorted((r for r in rows if r["direction"] == mode), key=lambda r: r["gap_nm"])
    x = [r["gap_nm"] for r in selected]
    axes[0].plot(x, [r["max_mass_abs_relative"] for r in selected], marker=marker, label=mode)
    axes[1].plot(x, [r["max_density_deviation"] for r in selected], marker=marker)
    axes[2].plot(x, [r["Mach_max"] for r in selected], marker=marker)
axes[0].set_ylabel("Max mass drift")
axes[1].set_ylabel(r"Max $|\rho-1|$")
axes[2].set_ylabel("Max Mach")
axes[2].set_xlabel("Fixed mesa gap h (nm)")
for ax in axes:
    ax.grid(alpha=0.25)
axes[0].legend(title="Drive")
save_figure("fixed_gap_numerical_checks")

fig, ax = plt.subplots(figsize=(6.2, 4.2))
for gap in GAPS:
    for mode, linestyle in (("x", "-"), ("y", "--")):
        path = run_dir(gap, mode) / "diagnostics.csv"
        with path.open(newline="") as handle:
            data = list(csv.DictReader(handle))
        component = "Jx_m2_s" if mode == "x" else "Jy_m2_s"
        ax.plot(
            [float(r["time_s"]) * 1e9 for r in data],
            [float(r[component]) * 1e12 for r in data],
            linestyle=linestyle,
            label=f"h={gap} nm, {mode.upper()}",
        )
ax.set_xlabel("Physical time (ns)")
ax.set_ylabel(r"Main $J$ ($10^{-12}$ m$^2$/s)")
ax.grid(alpha=0.25)
ax.legend(fontsize=8, ncol=2)
save_figure("fixed_gap_J_convergence")

fig, ax = plt.subplots(figsize=(6.2, 4.2))
for mode, marker in (("X", "o"), ("Y", "s")):
    selected = sorted((r for r in rows if r["direction"] == mode), key=lambda r: r["gap_nm"])
    ax.plot(
        [r["gap_nm"] for r in selected],
        [r["pressure_max_Pa"] - r["pressure_min_Pa"] for r in selected],
        marker=marker,
        label=mode,
    )
ax.set_xlabel("Fixed mesa gap h (nm)")
ax.set_ylabel("Local pressure range (Pa)")
ax.grid(alpha=0.25)
ax.legend(title="Drive")
save_figure("fixed_gap_pressure_range")

print(summary)
