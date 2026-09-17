#!/usr/bin/env python3
import csv
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def read_key_values(path: Path):
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def as_float(values, key, default=math.nan):
    try:
        return float(values[key])
    except (KeyError, ValueError):
        return default


def load_rows(batch_dir: Path):
    definitions = {}
    with (batch_dir / "matrix_definition.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            definitions[row["case_id"]] = row

    rows = []
    for case_id, definition in definitions.items():
        steady = batch_dir / case_id / "steady"
        summary_path = steady / "result_summary.csv"
        result_path = steady / "result.txt"
        exit_path = steady / "exit_code.txt"
        if not summary_path.exists() or not result_path.exists():
            rows.append({
                "case_id": case_id,
                "group": definition["group"],
                "dx_nm": float(definition["dx_nm"]),
                "tau": float(definition["tau"]),
                "force": float(definition["acceleration_m_s2"]),
                "status": "MISSING",
            })
            continue
        with summary_path.open(newline="", encoding="utf-8") as handle:
            summary = next(csv.DictReader(handle))
        result = read_key_values(result_path)
        rows.append({
            "case_id": case_id,
            "group": definition["group"],
            "dx_nm": float(summary["dx"]) * 1e9,
            "tau": float(summary["tau"]),
            "force": float(summary["force"]),
            "J": float(summary["J"]),
            "K_LBM": float(summary["K_LBM"]),
            "K_theory": float(summary["K_theory"]),
            "relative_error": float(summary["relative_error"]),
            "mass_error": as_float(result, "max_mass_abs_relative"),
            "Mach": as_float(result, "max_Mach"),
            "profile_L2": as_float(result, "velocity_profile_L2_relative_error"),
            "offset_relative": as_float(result, "velocity_offset_relative_to_analytic_max"),
            "q_min": as_float(result, "q_min"),
            "q_max": as_float(result, "q_max"),
            "steps": int(float(result.get("steps_completed", "0"))),
            "case_PASS": result.get("PASS", "false") == "true",
            "exit_code": int(exit_path.read_text().strip()) if exit_path.exists() else -1,
            "status": "COMPLETE",
        })
    return rows


def write_matrix_summary(batch_dir: Path, rows):
    fields = [
        "case_id", "group", "dx_nm", "tau", "force", "J", "K_LBM",
        "K_theory", "relative_error", "mass_error", "Mach", "profile_L2",
        "offset_relative", "q_min", "q_max", "steps", "case_PASS",
        "exit_code", "status",
    ]
    with (batch_dir / "matrix_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def force_metrics(rows):
    force_rows = sorted((r for r in rows if r["group"] == "force" and r["status"] == "COMPLETE"), key=lambda r: r["force"])
    if len(force_rows) != 3:
        return force_rows, math.nan, math.nan, math.nan, False
    x = np.array([r["force"] for r in force_rows], dtype=float)
    y = np.array([r["J"] for r in force_rows], dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    prediction = slope * x + intercept
    ss_res = float(np.sum((y - prediction) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    intercept_fraction = abs(intercept) / max(abs(y))
    passed = r2 >= 0.999999 and intercept_fraction <= 0.01
    return force_rows, slope, intercept, r2, passed


def grid_metrics(rows):
    grid_rows = sorted((r for r in rows if r["group"] == "grid" and r["status"] == "COMPLETE"), key=lambda r: r["dx_nm"], reverse=True)
    errors = [abs(r["relative_error"]) for r in grid_rows]
    monotonic = len(errors) == 3 and all(errors[i] > errors[i + 1] for i in range(len(errors) - 1))
    finest_pass = len(grid_rows) == 3 and errors[-1] < 0.02
    richardson = None
    if len(grid_rows) == 3:
        coarse, medium, fine = (r["K_LBM"] for r in grid_rows)
        refinement_ratio = grid_rows[0]["dx_nm"] / grid_rows[1]["dx_nm"]
        ratio = abs((coarse - medium) / (medium - fine))
        observed_order = math.log(ratio) / math.log(refinement_ratio)
        denominator = refinement_ratio ** observed_order - 1.0
        extrapolated = fine + (fine - medium) / denominator
        fine_gci = 1.25 * abs((fine - medium) / fine) / denominator
        richardson = {
            "refinement_ratio": refinement_ratio,
            "observed_order": observed_order,
            "K_extrapolated": extrapolated,
            "extrapolated_error_vs_theory": (extrapolated - grid_rows[-1]["K_theory"]) / grid_rows[-1]["K_theory"],
            "fine_GCI": fine_gci,
        }
    return grid_rows, monotonic, finest_pass, richardson


def write_richardson_summary(batch_dir: Path, richardson):
    if richardson is None:
        return
    with (batch_dir / "richardson_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=richardson.keys())
        writer.writeheader()
        writer.writerow(richardson)


def make_figures(batch_dir: Path, rows, force_rows, grid_rows):
    figure_dir = batch_dir / "figures"
    figure_dir.mkdir(exist_ok=True)

    base_profile = batch_dir / "G1-a2" / "steady" / "velocity_profile.csv"
    with base_profile.open(newline="", encoding="utf-8") as handle:
        profile = list(csv.DictReader(handle))
    z_nm = np.array([float(r["z"]) * 1e9 for r in profile])
    u_lbm = np.array([float(r["u_LBM"]) for r in profile])
    u_analytic = np.array([float(r["u_analytic"]) for r in profile])
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    ax.plot(u_analytic, z_nm, "k-", label="Analytical")
    ax.plot(u_lbm, z_nm, "o", markerfacecolor="none", label="LBM")
    ax.set_xlabel("Velocity $u_y$ (m/s)")
    ax.set_ylabel("$z$ (nm)")
    ax.set_title("Figure 1. Poiseuille velocity profile")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(figure_dir / "Figure1_velocity_profile.png", dpi=300)
    fig.savefig(figure_dir / "Figure1_velocity_profile.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    x = np.array([r["force"] for r in force_rows])
    y = np.array([r["J"] for r in force_rows])
    slope, intercept = np.polyfit(x, y, 1)
    xx = np.linspace(0.0, 1.05 * max(x), 100)
    ax.plot(x, y, "o", label="LBM")
    ax.plot(xx, slope * xx + intercept, "-", label="Linear fit")
    ax.set_xlabel("Acceleration $a$ (m/s$^2$)")
    ax.set_ylabel("Depth-integrated flux $J$ (m$^2$/s)")
    ax.set_title("Figure 2. Force linearity")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(figure_dir / "Figure2_J_vs_acceleration.png", dpi=300)
    fig.savefig(figure_dir / "Figure2_J_vs_acceleration.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    dx_values = np.array([r["dx_nm"] for r in sorted(grid_rows, key=lambda r: r["dx_nm"])])
    errors = np.array([100.0 * abs(r["relative_error"]) for r in sorted(grid_rows, key=lambda r: r["dx_nm"])])
    ax.plot(dx_values, errors, "o-")
    ax.axhline(2.0, color="tab:red", linestyle="--", label="2% target")
    ax.set_xlabel("Grid spacing $dx$ (nm)")
    ax.set_ylabel("$|K_{LBM}-K_{theory}|/K_{theory}$ (%)")
    ax.set_title("Figure 3. Grid sensitivity")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(figure_dir / "Figure3_error_vs_dx.png", dpi=300)
    fig.savefig(figure_dir / "Figure3_error_vs_dx.pdf")
    plt.close(fig)

    complete = [r for r in rows if r["status"] == "COMPLETE"]
    table_data = [[
        r["case_id"], f'{r["dx_nm"]:g}', f'{r["tau"]:g}', f'{r["force"]:.1e}',
        f'{r["K_LBM"]:.6e}', f'{100*r["relative_error"]:+.4f}%',
        "PASS" if r["case_PASS"] else "FAIL",
    ] for r in complete]
    fig, ax = plt.subplots(figsize=(11.5, 3.8))
    ax.axis("off")
    table = ax.table(
        cellText=table_data,
        colLabels=["Case", "dx (nm)", "tau", "a", "K_LBM (m$^3$)", "K error", "Gate"],
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    table.scale(1.0, 1.28)
    ax.set_title("Figure 4. Hydraulic mobility error summary", pad=8)
    fig.tight_layout(pad=0.6)
    fig.savefig(figure_dir / "Figure4_K_error_summary.png", dpi=300, bbox_inches="tight")
    fig.savefig(figure_dir / "Figure4_K_error_summary.pdf", bbox_inches="tight")
    plt.close(fig)


def write_report(batch_dir: Path, rows, slope, intercept, r2, force_pass, grid_monotonic, finest_pass, richardson):
    complete = [r for r in rows if r["status"] == "COMPLETE"]
    base = next((r for r in rows if r["case_id"] == "G1-a2"), None)
    mandatory_complete = len(complete) == 9
    base_complete = bool(base and base.get("status") == "COMPLETE")
    base_pass = bool(base_complete and base.get("case_PASS"))
    overall_pass = mandatory_complete and force_pass and grid_monotonic and finest_pass and base_pass

    lines = [
        "# G1-V2 LBM hydraulic transport validation",
        "",
        "## Overall decision",
        "",
        f"- **G1-V2: {'PASS' if overall_pass else 'FAIL'}**",
        f"- All 9 requested/optional matrix runs completed: `{mandatory_complete}`",
        f"- Force linearity: `{'PASS' if force_pass else 'FAIL'}`; R2 = `{r2:.12g}`, intercept = `{intercept:.12e}` m2/s",
        f"- Grid error decreases with dx: `{'PASS' if grid_monotonic else 'FAIL'}`",
        f"- Finest-grid K error below 2%: `{'PASS' if finest_pass else 'FAIL'}`",
        f"- Baseline dx=5 nm, tau=1.7, a=1e5 case: `{'PASS' if base_pass else 'FAIL'}`",
        "",
        "The overall Gate requires the frozen baseline as well as the matrix-level checks. A converged run with exit code 3 is a completed FAIL, not a normal PASS.",
        "",
        "## Old G1 versus G1-V2",
        "",
        "| Item | Old BounceBack G1 | G1-V2 Bouzidi baseline |",
        "|---|---:|---:|",
        "| K relative error | +4.675555% | " + (f'{100*base["relative_error"]:+.6f}%' if base_complete else "missing") + " |",
        "| Mass relative error | 0 | " + (f'{base["mass_error"]:.6e}' if base_complete else "missing") + " |",
        "| Maximum Mach | 2.508010e-7 | " + (f'{base["Mach"]:.6e}' if base_complete else "missing") + " |",
        "| Velocity-profile L2 | 4.065283% | " + (f'{100*base["profile_L2"]:.6f}%' if base_complete else "missing") + " |",
        "| Boundary | halfway BounceBack | exact-plane Bouzidi |",
        "",
        "## Evidence-based interpretation",
        "",
        "The pre-existing same-parameter Bouzidi run already showed q=0.5 and exactly the same +4.675555% mobility error as BounceBack. Therefore the old error cannot be attributed solely to the boundary API. The force, grid and tau matrices in this batch must be used to distinguish forcing/relaxation/halfway-boundary discretization effects. No analytic formula, physical H, velocity offset or acceptance threshold was altered.",
        "",
        "## Grid uncertainty",
        "",
        (f'- Three-grid apparent order: `{richardson["observed_order"]:.6f}`' if richardson else "- Three-grid apparent order: unavailable"),
        (f'- Richardson-extrapolated K: `{richardson["K_extrapolated"]:.12e}` m3' if richardson else "- Richardson-extrapolated K: unavailable"),
        (f'- Extrapolated K error versus theory: `{100*richardson["extrapolated_error_vs_theory"]:+.6f}%`' if richardson else "- Extrapolated K error versus theory: unavailable"),
        (f'- Fine-grid GCI (Fs=1.25): `{100*richardson["fine_GCI"]:.6f}%`' if richardson else "- Fine-grid GCI: unavailable"),
        "",
        "## Case results",
        "",
        "| Case | Group | dx (nm) | tau | a (m/s2) | J (m2/s) | K error | Profile L2 | Offset/max analytic | Mass error | Mach | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        if row["status"] != "COMPLETE":
            lines.append(f'| {row["case_id"]} | {row["group"]} | {row["dx_nm"]:g} | {row["tau"]:g} | {row["force"]:.3e} | — | — | — | — | — | — | MISSING |')
            continue
        lines.append(
            f'| {row["case_id"]} | {row["group"]} | {row["dx_nm"]:g} | {row["tau"]:g} | {row["force"]:.3e} | '
            f'{row["J"]:.9e} | {100*row["relative_error"]:+.6f}% | {100*row["profile_L2"]:.6f}% | '
            f'{100*row["offset_relative"]:.6f}% | {row["mass_error"]:.3e} | {row["Mach"]:.3e} | '
            f'{"PASS" if row["case_PASS"] else "FAIL"} |'
        )
    lines.extend([
        "",
        "## Figures",
        "",
        "- `figures/Figure1_velocity_profile.png` / `.pdf`",
        "- `figures/Figure2_J_vs_acceleration.png` / `.pdf`",
        "- `figures/Figure3_error_vs_dx.png` / `.pdf`",
        "- `figures/Figure4_K_error_summary.png` / `.pdf`",
        "",
        "All tables and figures were regenerated from the per-run CSV files in this batch.",
    ])
    (batch_dir / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: postprocess_g1_v2.py BATCH_DIRECTORY")
    batch_dir = Path(sys.argv[1]).resolve()
    rows = load_rows(batch_dir)
    write_matrix_summary(batch_dir, rows)
    force_rows, slope, intercept, r2, force_pass = force_metrics(rows)
    grid_rows, grid_monotonic, finest_pass, richardson = grid_metrics(rows)
    write_richardson_summary(batch_dir, richardson)
    if len(force_rows) == 3 and len(grid_rows) == 3:
        make_figures(batch_dir, rows, force_rows, grid_rows)
    write_report(batch_dir, rows, slope, intercept, r2, force_pass, grid_monotonic, finest_pass, richardson)


if __name__ == "__main__":
    main()
