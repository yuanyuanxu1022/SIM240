#!/usr/bin/env python3
"""Reproducible plots and summary for the two frozen FreeSurface runs."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy

ROOT = Path(__file__).resolve().parent
RUNS = {
    "droplet": ROOT / "output/droplet_formal_dx5_dt1ps_sigma00309_20260910/history.csv",
    "capillary": ROOT / "output/capillary_formal_dx5_dt1ps_sigma00309_20260910/history.csv",
}


def load(path: Path) -> dict[str, np.ndarray]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {key: np.asarray([float(row[key]) for row in rows]) for key in rows[0]}


def first_index(mask: np.ndarray) -> int | None:
    indices = np.flatnonzero(mask)
    return int(indices[0]) if len(indices) else None


data = {name: load(path) for name, path in RUNS.items()}
figures = ROOT / "figures"
figures.mkdir(exist_ok=True)

plt.rcParams.update({"font.size": 9, "figure.dpi": 140, "savefig.dpi": 300})

d = data["droplet"]
fig, axes = plt.subplots(2, 1, figsize=(6.6, 5.5), sharex=True)
axes[0].plot(d["time_s"] * 1e9, d["liquid_mass_relative_drift"], lw=1.1)
axes[0].axhline(5e-3, color="0.5", ls="--", lw=0.8)
axes[0].axhline(-5e-3, color="0.5", ls="--", lw=0.8)
axes[0].set_ylabel("Liquid mass drift")
axes[0].grid(alpha=0.25)
radius0 = d["equivalent_radius_nm"][0]
axes[1].plot(d["time_s"] * 1e9, (d["equivalent_radius_nm"] - radius0) / radius0, lw=1.1, label="Equivalent radius")
axes[1].plot(d["time_s"] * 1e9, d["max_Mach"], lw=1.0, label="Max Mach")
axes[1].set(xlabel="Time (ns)", ylabel="Relative change / Mach")
axes[1].legend(frameon=False)
axes[1].grid(alpha=0.25)
fig.suptitle("Static droplet: mass, radius and velocity response")
fig.tight_layout()
for ext in ("png", "pdf"):
    fig.savefig(figures / f"static_droplet_stability.{ext}", bbox_inches="tight")
plt.close(fig)

c = data["capillary"]
fig, axes = plt.subplots(2, 1, figsize=(6.6, 5.5), sharex=True)
axes[0].plot(c["time_s"] * 1e9, c["slot_fill_fraction"], lw=1.1, label="Slot fill fraction")
axes[0].set_ylabel("Fill fraction")
axes[0].legend(frameon=False)
axes[0].grid(alpha=0.25)
axes[1].plot(c["time_s"] * 1e9, c["capillary_rise_nm"], lw=1.1, label="Slot − reservoir interface")
axes[1].set(xlabel="Time (ns)", ylabel="Interface rise (nm)")
axes[1].legend(frameon=False)
axes[1].grid(alpha=0.25)
fig.suptitle("Rectangular capillary: filling and wetting response")
fig.tight_layout()
for ext in ("png", "pdf"):
    fig.savefig(figures / f"rectangular_capillary_response.{ext}", bbox_inches="tight")
plt.close(fig)

fig, axes = plt.subplots(2, 1, figsize=(6.6, 5.5), sharex=False)
for name, series in data.items():
    axes[0].plot(series["time_s"] * 1e9, series["epsilon_max"], lw=1.0, label=name)
axes[0].axhline(1.00100001, color="tab:red", ls="--", lw=0.9, label="frozen upper limit")
axes[0].set(ylabel="Maximum liquid fraction")
axes[0].legend(frameon=False)
axes[0].grid(alpha=0.25)
for name, series in data.items():
    axes[1].plot(series["time_s"] * 1e9, series["liquid_mass_relative_drift"], lw=1.0, label=name)
axes[1].set(xlabel="Time (ns)", ylabel="Liquid mass drift")
axes[1].legend(frameon=False)
axes[1].grid(alpha=0.25)
fig.suptitle("FreeSurface acceptance diagnostics")
fig.tight_layout()
for ext in ("png", "pdf"):
    fig.savefig(figures / f"combined_acceptance_diagnostics.{ext}", bbox_inches="tight")
plt.close(fig)

epsilon_limit = 1.00100001
droplet_violation = first_index(d["epsilon_max"] > epsilon_limit)
summary = ROOT / "minimal_freesurface_validation_summary.csv"
with summary.open("w", newline="", encoding="utf-8") as handle:
    fields = [
        "case", "steps_completed", "max_abs_mass_drift", "rho_min", "rho_max",
        "max_Mach", "epsilon_min", "epsilon_max", "first_epsilon_violation_step",
        "initial_fill_fraction", "final_fill_fraction", "final_capillary_rise_nm", "verdict",
    ]
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    for name, series in data.items():
        fill0 = float(series["slot_fill_fraction"][0])
        fill1 = float(series["slot_fill_fraction"][-1])
        violation = first_index(series["epsilon_max"] > epsilon_limit)
        verdict = "FAIL_epsilon_overshoot" if violation is not None else ("FAIL_no_wetting_response" if name == "capillary" and fill1 < fill0 + 0.01 else "PASS")
        writer.writerow({
            "case": name,
            "steps_completed": int(series["step"][-1]),
            "max_abs_mass_drift": float(np.max(np.abs(series["liquid_mass_relative_drift"]))),
            "rho_min": float(np.min(series["rho_min"])),
            "rho_max": float(np.max(series["rho_max"])),
            "max_Mach": float(np.max(series["max_Mach"])),
            "epsilon_min": float(np.min(series["epsilon_min"])),
            "epsilon_max": float(np.max(series["epsilon_max"])),
            "first_epsilon_violation_step": "" if violation is None else int(series["step"][violation]),
            "initial_fill_fraction": fill0,
            "final_fill_fraction": fill1,
            "final_capillary_rise_nm": float(series["capillary_rise_nm"][-1]),
            "verdict": verdict,
        })

print(f"droplet_first_epsilon_violation={None if droplet_violation is None else int(d['step'][droplet_violation])}")
print(f"droplet_max_epsilon={float(np.max(d['epsilon_max'])):.12g}")
print(f"capillary_fill_delta={float(c['slot_fill_fraction'][-1]-c['slot_fill_fraction'][0]):.12g}")
print(f"capillary_max_abs_mass_drift={float(np.max(np.abs(c['liquid_mass_relative_drift']))):.12g}")

# The gas-side pressure array is retained for visualization but is not treated
# as resolved gas dynamics.  This audit therefore compares bulk-liquid gauge
# pressure with the Laplace scale 2*sigma/R only.
pressure_audit = ROOT / "droplet_laplace_pressure_audit.csv"
with pressure_audit.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["step", "time_s", "bulk_liquid_mean_pressure_Pa", "bulk_liquid_pressure_std_Pa", "laplace_2sigma_over_R_Pa", "relative_difference"])
    for step in (0, 200, 1000, 1600, 1711):
        path = ROOT / f"output/droplet_formal_dx5_dt1ps_sigma00309_20260910/vtkData/data/minimal_static_droplet_iT{step:07d}iC00000.vti"
        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(str(path))
        reader.Update()
        image = reader.GetOutput()
        dims = image.GetDimensions()
        cell_type = vtk_to_numpy(image.GetPointData().GetArray("free_surface_cell_type")).reshape(dims[::-1])
        pressure = vtk_to_numpy(image.GetPointData().GetArray("pressure_Pa")).reshape(dims[::-1])
        # The writer includes the three-cell overlap in every direction.
        core = (slice(3, -3),) * 3
        bulk = pressure[core][cell_type[core] == 2]
        laplace = 2 * 0.0309 / 60e-9
        mean = float(np.mean(bulk))
        writer.writerow([step, step * 1e-12, mean, float(np.std(bulk)), laplace, (mean - laplace) / laplace])
