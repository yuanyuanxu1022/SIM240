#!/usr/bin/env python3
import csv
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def read_key_values(path):
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def load_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def save(fig, figure_dir, name):
    fig.tight_layout()
    fig.savefig(figure_dir / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(figure_dir / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def field_array(rows, field):
    xs = sorted({float(row["x"]) * 1e9 for row in rows})
    zs = sorted({float(row["z"]) * 1e9 for row in rows})
    xi = {value: index for index, value in enumerate(xs)}
    zi = {value: index for index, value in enumerate(zs)}
    values = np.full((len(zs), len(xs)), np.nan)
    for row in rows:
        x = float(row["x"]) * 1e9
        z = float(row["z"]) * 1e9
        values[zi[z], xi[x]] = float(row[field])
    return np.array(xs), np.array(zs), values


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: postprocess_g2.py BATCH_DIRECTORY")
    batch = Path(sys.argv[1]).resolve()
    figure_dir = batch / "figures"
    figure_dir.mkdir(exist_ok=True)
    cases = {}
    for case_id in ("G2-P", "G2-T"):
        steady = batch / case_id / "steady"
        if not (steady / "result.txt").exists():
            raise SystemExit(f"missing formal result: {steady}")
        cases[case_id] = {
            "steady": steady,
            "result": read_key_values(steady / "result.txt"),
            "summary": load_csv(steady / "result_summary.csv")[0],
            "field": load_csv(steady / "field_slice.csv"),
        }

    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    ax.fill_between([0, 60], [75, 75], [175, 175], color="0.45", label="Mesa solid")
    ax.fill_between([180, 240], [75, 75], [175, 175], color="0.45")
    ax.plot([0, 60, 60, 180, 180, 240], [75, 75, 175, 175, 75, 75], "k-", lw=2)
    ax.axhline(0, color="k", lw=2)
    ax.annotate("groove: 120 nm", xy=(120, 150), ha="center")
    ax.annotate("depth: 100 nm", xy=(184, 125), va="center", rotation=90)
    ax.annotate("mesa gap h: 75 nm", xy=(30, 38), ha="center", rotation=90)
    ax.set_xlim(0, 240)
    ax.set_ylim(-5, 185)
    ax.set_xlabel("x (nm)")
    ax.set_ylabel("z (nm)")
    ax.set_title("Figure G2-1. EX240 single-period geometry")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.2)
    save(fig, figure_dir, "Figure_G2_1_geometry")

    fig = plt.figure(figsize=(10.5, 4.2), layout="constrained")
    grid = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.045])
    axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])]
    axes[1].sharex(axes[0])
    axes[1].sharey(axes[0])
    color_axis = fig.add_subplot(grid[0, 2])
    speed_max = max(float(row["speed"]) for case in cases.values() for row in case["field"])
    for ax, case_id in zip(axes, ("G2-P", "G2-T")):
        x, z, values = field_array(cases[case_id]["field"], "speed")
        image = ax.pcolormesh(x, z, values, shading="nearest", cmap="viridis", vmin=0, vmax=speed_max)
        ax.set_title("Parallel" if case_id == "G2-P" else "Perpendicular")
        ax.set_xlabel("x (nm)")
        ax.set_aspect("equal", adjustable="box")
    axes[0].set_ylabel("z (nm)")
    fig.colorbar(image, cax=color_axis, label="Speed (m/s)")
    fig.suptitle("Figure G2-2. Velocity magnitude at the periodic mid-plane")
    fig.savefig(figure_dir / "Figure_G2_2_velocity_field.png", dpi=300, bbox_inches="tight")
    fig.savefig(figure_dir / "Figure_G2_2_velocity_field.pdf", bbox_inches="tight")
    plt.close(fig)

    fig = plt.figure(figsize=(10.5, 4.2), layout="constrained")
    grid = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.045])
    axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])]
    axes[1].sharex(axes[0])
    axes[1].sharey(axes[0])
    color_axis = fig.add_subplot(grid[0, 2])
    pressure_limit = max(abs(float(row["pressure"])) for case in cases.values() for row in case["field"])
    for ax, case_id in zip(axes, ("G2-P", "G2-T")):
        x, z, values = field_array(cases[case_id]["field"], "pressure")
        image = ax.pcolormesh(x, z, values, shading="nearest", cmap="coolwarm", vmin=-pressure_limit, vmax=pressure_limit)
        ax.set_title("Parallel" if case_id == "G2-P" else "Perpendicular")
        ax.set_xlabel("x (nm)")
        ax.set_aspect("equal", adjustable="box")
    axes[0].set_ylabel("z (nm)")
    fig.colorbar(image, cax=color_axis, label="Local pressure perturbation (Pa)")
    fig.suptitle("Figure G2-3. Periodic local pressure disturbance")
    fig.savefig(figure_dir / "Figure_G2_3_pressure_distribution.png", dpi=300, bbox_inches="tight")
    fig.savefig(figure_dir / "Figure_G2_3_pressure_distribution.pdf", bbox_inches="tight")
    plt.close(fig)

    k0 = float(cases["G2-P"]["result"]["K0_smooth_h75_m3"])
    kp = float(cases["G2-P"]["summary"]["Keff"])
    kt = float(cases["G2-T"]["summary"]["Keff"])
    fig, ax = plt.subplots(figsize=(6.4, 4.5))
    labels = [r"$K_0$ smooth", r"$K_{\parallel}$", r"$K_{\perp}$"]
    values = np.array([k0, kp, kt]) / k0
    bars = ax.bar(labels, values, color=["0.55", "tab:blue", "tab:orange"])
    ax.axhline(1.0, color="k", ls="--", lw=1)
    ax.set_ylabel(r"Mobility normalized by $K_0=h^3/12$")
    ax.set_title("Figure G2-4. Directional effective mobility")
    ax.grid(axis="y", alpha=0.25)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, value, f"{value:.3f}", ha="center", va="bottom")
    save(fig, figure_dir, "Figure_G2_4_directional_K")

    ratio = kp / kt
    rows = []
    for case_id in ("G2-P", "G2-T"):
        summary = cases[case_id]["summary"]
        result = cases[case_id]["result"]
        rows.append({
            **summary,
            "Keff_over_K0": result["Keff_over_K0"],
            "max_density_deviation": result["max_density_deviation"],
            "candidate_links": result["candidate_links"],
            "installed_links": result["installed_links"],
            "q_min": result["q_min"],
            "q_max": result["q_max"],
            "fallback_count": result["fallback_count"],
            "PASS": result["PASS"],
        })
    with (batch / "g2_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    all_pass = all(row["PASS"] == "true" for row in rows)
    report = [
        "# G2 EX240 single-period transport report",
        "",
        f"- Overall Gate: **{'PASS' if all_pass else 'FAIL'}**",
        f"- K_parallel = `{kp:.12e}` m3",
        f"- K_perpendicular = `{kt:.12e}` m3",
        f"- K_parallel / K_perpendicular = `{ratio:.8f}`",
        f"- Smooth reference K0(h=75 nm) = `{k0:.12e}` m3",
        f"- K_parallel / K0 = `{kp/k0:.8f}`",
        f"- K_perpendicular / K0 = `{kt/k0:.8f}`",
        "",
        "The pressure figure is a local periodic pressure disturbance. It is not an inlet-outlet pressure drop; R_eff is computed as rho*a/J = mu/Keff.",
        "",
        "All figures were regenerated from the formal per-run CSV files.",
    ]
    (batch / "G2_VALIDATION_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
