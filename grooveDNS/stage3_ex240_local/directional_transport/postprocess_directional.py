#!/usr/bin/env python3
"""Reproducible post-processing for the SIM-EC1XT240 STEP 6-B runs."""

from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
FIG = ROOT / "figures"
ANGLES = (0, 45, 90)
MODES = ("x", "y")


def parse_value(value: str):
    if "," in value:
        return tuple(float(item) for item in value.split(","))
    if value in {"true", "false"}:
        return value == "true"
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def load_result(angle: int, mode: str) -> dict:
    run_id = f"sim_ec1xt240_angle{angle}_h65_dx5_a1e5_{mode}_20260909"
    path = OUT / run_id / "result.txt"
    data = {"result_path": str(path), "run_id_expected": run_id}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            data[key] = parse_value(value)
    if data["run_id"] != run_id or not data["PASS"]:
        raise RuntimeError(f"Unexpected or failed result: {path}")
    return data


def load_history(result: dict) -> list[dict[str, float]]:
    path = Path(result["result_path"]).with_name("diagnostics.csv")
    with path.open(newline="") as handle:
        return [{k: float(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def save_both(fig, stem: str):
    fig.savefig(FIG / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    FIG.mkdir(exist_ok=True)
    runs = {(a, m): load_result(a, m) for a in ANGLES for m in MODES}

    fields = [
        "run_id", "angle_deg", "mode", "nx", "ny", "Lx_m", "Ly_m",
        "normal_pitch_nm", "groove_width_nm", "gap_nm", "dt_s", "tau",
        "steps_completed", "fluid_nodes", "fluid_volume_m3",
        "max_mass_abs_relative", "max_density_deviation", "pressure_min_Pa",
        "pressure_max_Pa", "pressure_disturbance_Pa", "max_speed_m_s",
        "Re_max_Href", "Mach_max", "mean_ux_m_s", "mean_uy_m_s",
        "Jx_m2_s", "Jy_m2_s", "Kxj_m3", "Kyj_m3",
        "flow_rate_mean_m3_s", "R_main_Pa_s_per_m3",
        "section_relative_difference", "finite", "material_unchanged", "PASS",
    ]
    with (ROOT / "directional_transport_database.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for angle in ANGLES:
            for mode in MODES:
                r = runs[(angle, mode)]
                row = {
                    "run_id": r["run_id"], "angle_deg": angle, "mode": mode,
                    "nx": r["nx_ny"][0], "ny": r["nx_ny"][1],
                    "Lx_m": r["Lx_Ly_m"][0], "Ly_m": r["Lx_Ly_m"][1],
                    "normal_pitch_nm": r["normal_pitch_nm"],
                    "groove_width_nm": r["groove_width_nm"], "gap_nm": r["gap_nm"],
                    "dt_s": r["dt_s"], "tau": r["tau"],
                    "steps_completed": r["steps_completed"], "fluid_nodes": r["fluid_nodes"],
                    "fluid_volume_m3": r["fluid_volume_m3"],
                    "max_mass_abs_relative": r["max_mass_abs_relative"],
                    "max_density_deviation": r["max_density_deviation"],
                    "pressure_min_Pa": r["pressure_range_Pa"][0],
                    "pressure_max_Pa": r["pressure_range_Pa"][1],
                    "pressure_disturbance_Pa": r["pressure_range_Pa"][1] - r["pressure_range_Pa"][0],
                    "max_speed_m_s": r["max_speed_m_s"], "Re_max_Href": r["Re_max_Href"],
                    "Mach_max": r["Mach_max"], "mean_ux_m_s": r["mean_u_m_s"][0],
                    "mean_uy_m_s": r["mean_u_m_s"][1], "Jx_m2_s": r["J_m2_s"][0],
                    "Jy_m2_s": r["J_m2_s"][1],
                    "Kxj_m3": r["K_response_column_m3"][0],
                    "Kyj_m3": r["K_response_column_m3"][1],
                    "flow_rate_mean_m3_s": r["flow_rate_mean_m3_s"],
                    "R_main_Pa_s_per_m3": r["R_main_Pa_s_per_m3"],
                    "section_relative_difference": r["section_relative_difference"],
                    "finite": r["finite"], "material_unchanged": r["material_unchanged"],
                    "PASS": r["PASS"],
                }
                writer.writerow(row)

    tensor_fields = [
        "angle_deg", "Kxx_m3", "Kxy_m3", "Kyx_m3", "Kyy_m3",
        "reciprocity_abs_m3", "reciprocity_relative", "principal_max_m3",
        "principal_min_m3", "anisotropy_ratio",
    ]
    tensor_rows = []
    for angle in ANGLES:
        rx, ry = runs[(angle, "x")], runs[(angle, "y")]
        kxx, kyx = rx["K_response_column_m3"][:2]
        kxy, kyy = ry["K_response_column_m3"][:2]
        trace = kxx + kyy
        disc = math.sqrt((kxx - kyy) ** 2 + 4 * (0.5 * (kxy + kyx)) ** 2)
        pmax, pmin = 0.5 * (trace + disc), 0.5 * (trace - disc)
        reciprocity_scale = max(abs(kxy), abs(kyx))
        tensor_rows.append({
            "angle_deg": angle, "Kxx_m3": kxx, "Kxy_m3": kxy,
            "Kyx_m3": kyx, "Kyy_m3": kyy,
            "reciprocity_abs_m3": abs(kxy - kyx),
            # A relative error is undefined when both cross terms are numerical zero.
            "reciprocity_relative": (
                abs(kxy - kyx) / reciprocity_scale if reciprocity_scale >= 1e-30 else ""
            ),
            "principal_max_m3": pmax, "principal_min_m3": pmin,
            "anisotropy_ratio": pmax / pmin,
        })
    with (ROOT / "directional_tensor_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=tensor_fields)
        writer.writeheader()
        writer.writerows(tensor_rows)

    plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.25})
    angles = list(ANGLES)
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    for key, marker in (("Kxx_m3", "o"), ("Kyy_m3", "s"), ("Kxy_m3", "^"), ("Kyx_m3", "v")):
        ax.plot(angles, [row[key] * 1e23 for row in tensor_rows], marker=marker, label=key.replace("_m3", ""))
    ax.set(xlabel="Groove-axis rotation angle (deg)", ylabel=r"Transport coefficient $K_{ij}$ ($10^{-23}$ m$^3$)", xticks=angles)
    ax.legend(ncol=2)
    save_both(fig, "K_tensor_vs_angle")

    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    for mode, marker in (("x", "o"), ("y", "s")):
        ax.plot(angles, [runs[(a, mode)]["R_main_Pa_s_per_m3"] / 1e19 for a in angles], marker=marker, label=f"{mode.upper()} drive")
    ax.set(xlabel="Groove-axis rotation angle (deg)", ylabel=r"Directional resistance ($10^{19}$ Pa s m$^{-3}$)", xticks=angles)
    ax.legend()
    save_both(fig, "resistance_vs_angle")

    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    for mode, marker in (("x", "o"), ("y", "s")):
        ax.plot(angles, [runs[(a, mode)]["flow_rate_mean_m3_s"] * 1e18 for a in angles], marker=marker, label=f"{mode.upper()} drive")
    ax.set(xlabel="Groove-axis rotation angle (deg)", ylabel=r"Mean-direction flow rate ($10^{-18}$ m$^3$/s)", xticks=angles)
    ax.legend()
    save_both(fig, "flow_rate_vs_angle")

    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    for mode, marker in (("x", "o"), ("y", "s")):
        values = [runs[(a, mode)]["pressure_range_Pa"][1] - runs[(a, mode)]["pressure_range_Pa"][0] for a in angles]
        ax.plot(angles, values, marker=marker, label=f"{mode.upper()} drive")
    ax.set(xlabel="Groove-axis rotation angle (deg)", ylabel=r"Pressure disturbance $p_{max}-p_{min}$ (Pa)", xticks=angles)
    ax.legend()
    save_both(fig, "pressure_disturbance_vs_angle")

    fig, axes = plt.subplots(2, 1, figsize=(6.5, 6.2), sharex=False)
    for angle in ANGLES:
        for mode, ls in (("x", "-"), ("y", "--")):
            hist = load_history(runs[(angle, mode)])
            main = "Jx_m2_s" if mode == "x" else "Jy_m2_s"
            axes[0].plot([r["time_s"] * 1e9 for r in hist], [r[main] * 1e12 for r in hist], ls=ls, label=f"{angle}°, {mode.upper()}")
            axes[1].plot([r["time_s"] * 1e9 for r in hist], [r["mass_abs_relative"] for r in hist], ls=ls, label=f"{angle}°, {mode.upper()}")
    axes[0].set(ylabel=r"Main $J$ ($10^{-12}$ m$^2$/s)")
    axes[1].set(xlabel="Physical time (ns)", ylabel="Absolute relative mass drift")
    axes[0].legend(ncol=3, fontsize=8)
    save_both(fig, "convergence_and_mass_history")


if __name__ == "__main__":
    main()
