#!/usr/bin/env python3
"""Build a paper-oriented G2 data archive from completed CSV results."""

from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "CASE/03_grid_convergence/G2_EX240_grid_convergence/results/g2_grid_20260917T165045+0800"
OUT = ROOT / "paper_database/G2"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def f(value: str) -> float:
    return float(value)


def fmt(value: float) -> str:
    return f"{value:.17g}"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "figures").mkdir(exist_ok=True)

    summary = read_csv(RUN / "g2_grid_summary.csv")
    gci = read_csv(RUN / "g2_richardson_gci.csv")
    gci_by_metric = {row["metric"]: row for row in gci}
    ex = [row for row in summary if row["case"] == "EX240_parallel"]
    ex += [row for row in summary if row["case"] == "EX240_perpendicular"]
    smooth = [row for row in summary if row["case"] == "Smooth75"]
    ex.sort(key=lambda row: (f(row["dx"]), row["direction"]))
    smooth.sort(key=lambda row: f(row["dx"]))

    transport_fields = [
        "run_id", "dx_nm", "case", "direction", "K", "K_smooth", "anisotropy",
        "R_eff", "mass_error", "run_gate_PASS", "exit_code", "convergence_PASS",
        "boundary_audit_PASS", "normal_exit_PASS",
    ]
    transport_rows = []
    for row in summary:
        metric = "K_parallel" if row["direction"] == "parallel" else (
            "K_perpendicular" if row["direction"] == "perpendicular" else "K_smooth")
        transport_rows.append({
            "run_id": row["run_id"], "dx_nm": fmt(f(row["dx"]) * 1e9),
            "case": row["case"], "direction": row["direction"],
            "K": row["Keff"], "K_smooth": row["K_smooth"],
            "anisotropy": row["anisotropy"] if row["direction"] != "smooth" else "", "R_eff": row["R_eff"],
            "mass_error": row["mass_error"], "run_gate_PASS": row["run_gate_PASS"],
            "exit_code": row["exit_code"], "convergence_PASS": row["convergence_PASS"],
            "boundary_audit_PASS": row["boundary_audit_PASS"],
            "normal_exit_PASS": row["normal_exit_PASS"],
        })
    write_csv(OUT / "G2_transport_summary.csv", transport_fields, transport_rows)

    grid_fields = ["dx_nm", "K_smooth", "K_parallel", "K_perpendicular", "anisotropy", "parallel_gate", "perpendicular_gate", "GCI_parallel_fine_percent", "GCI_parallel_medium_percent", "GCI_perpendicular_fine_percent", "GCI_perpendicular_medium_percent", "asymptotic_PASS"]
    by_dx = {}
    for row in summary:
        by_dx.setdefault(f(row["dx"]) * 1e9, {})[row["direction"]] = row
    grid_rows = []
    for dx in sorted(by_dx):
        group = by_dx[dx]
        grid_rows.append({
            "dx_nm": fmt(dx),
            "K_smooth": group["smooth"]["Keff"],
            "K_parallel": group["parallel"]["Keff"],
            "K_perpendicular": group["perpendicular"]["Keff"],
            "anisotropy": group["parallel"]["anisotropy"],
            "parallel_gate": group["parallel"]["run_gate_PASS"],
            "perpendicular_gate": group["perpendicular"]["run_gate_PASS"],
            "GCI_parallel_fine_percent": gci_by_metric["K_parallel"]["GCI_fine_percent"],
            "GCI_parallel_medium_percent": gci_by_metric["K_parallel"]["GCI_medium_percent"],
            "GCI_perpendicular_fine_percent": gci_by_metric["K_perpendicular"]["GCI_fine_percent"],
            "GCI_perpendicular_medium_percent": gci_by_metric["K_perpendicular"]["GCI_medium_percent"],
            "asymptotic_PASS": gci_by_metric["K_parallel"]["asymptotic_PASS"] and gci_by_metric["K_perpendicular"]["asymptotic_PASS"],
        })
    write_csv(OUT / "G2_grid_convergence.csv", grid_fields, grid_rows)

    resistance_fields = ["dx_nm", "K_parallel", "K_perpendicular", "R_parallel", "R_perpendicular", "R_ratio"]
    resistance_rows = []
    for dx in sorted(by_dx):
        kp = f(by_dx[dx]["parallel"]["Keff"])
        kt = f(by_dx[dx]["perpendicular"]["Keff"])
        rp, rt = 1.0 / kp, 1.0 / kt
        resistance_rows.append({
            "dx_nm": fmt(dx), "K_parallel": fmt(kp), "K_perpendicular": fmt(kt),
            "R_parallel": fmt(rp), "R_perpendicular": fmt(rt), "R_ratio": fmt(rt / rp),
        })
    write_csv(OUT / "G2_resistance.csv", resistance_fields, resistance_rows)

    validation_lines = [
        "# G2 validation status", "", 
        "Source: `g2_grid_summary.csv`; no simulation was rerun during archiving.", "",
        "| dx (nm) | direction | run_gate_PASS | exit_code | mass_error | convergence_PASS | boundary_audit_PASS | normal_exit_PASS |",
        "|---:|---|---|---:|---:|---|---|---|",
    ]
    for row in sorted(ex, key=lambda x: (f(x["dx"]), x["direction"])):
        validation_lines.append(
            f"| {f(row['dx'])*1e9:g} | {row['direction']} | {row['run_gate_PASS']} | {row['exit_code']} | "
            f"{row['mass_error']} | {row['convergence_PASS']} | {row['boundary_audit_PASS']} | {row['normal_exit_PASS']} |"
        )
    validation_lines += [
        "", "The `dx=1.25 nm` EX240 perpendicular point has `run_gate_PASS=false` and `exit_code=3` because its recorded mass error is `1.1967043900362632e-10`. This status is preserved unchanged.",
        "", "The Smooth75 reference rows have `run_gate_PASS=true` for all three grids.",
    ]
    (OUT / "G2_validation_status.md").write_text("\n".join(validation_lines) + "\n")

    readme = """# G2 paper database\n\nThis directory is a derived, paper-oriented archive of completed OpenLB G2 EX240 grid-convergence results. The source data remain under `CASE/03_grid_convergence/G2_EX240_grid_convergence/results/`.\n\n- `G2_transport_summary.csv`: run-level transport and gate fields.\n- `G2_grid_convergence.csv`: Smooth75, parallel and perpendicular coefficients by grid.\n- `G2_resistance.csv`: reciprocal resistance, `R=1/K`, and resistance ratio.\n- `G2_validation_status.md`: preserved gate and exit status.\n- `G2_paper_summary.md`: manuscript-style interpretation.\n- `figures/`: 600-dpi PNG and PDF figures generated from the two source CSV files.\n\nNo LBM calculation, OpenLB source, raw result, or PASS/FAIL threshold is changed by this archive.\n"""
    (OUT / "README.md").write_text(readme)

    # Figures
    plt.rcParams.update({"font.size": 10, "axes.labelsize": 11, "axes.titlesize": 11, "legend.fontsize": 9})
    dxs = sorted(by_dx)
    k_s = [f(by_dx[x]["smooth"]["Keff"]) for x in dxs]
    k_p = [f(by_dx[x]["parallel"]["Keff"]) for x in dxs]
    k_t = [f(by_dx[x]["perpendicular"]["Keff"]) for x in dxs]
    ani = [f(by_dx[x]["parallel"]["anisotropy"]) for x in dxs]
    for ext in ("png", "pdf"):
        fig, ax = plt.subplots(figsize=(5.2, 3.6))
        ax.plot(dxs, k_s, "o-", label="Smooth75")
        ax.plot(dxs, k_p, "s-", label="EX240 parallel")
        ax.plot(dxs, k_t, "^-", label="EX240 perpendicular")
        ax.set_xscale("log"); ax.invert_xaxis(); ax.set_yscale("log")
        ax.set_xlabel("Grid spacing, dx (nm)"); ax.set_ylabel("Effective mobility, K (m$^3$)")
        ax.grid(True, which="both", alpha=.25); ax.legend(frameon=False); fig.tight_layout()
        fig.savefig(OUT / "figures" / f"Figure1_K_grid_convergence.{ext}", dpi=600)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(5.2, 3.6))
        ax.plot(dxs, ani, "o-", color="tab:purple")
        ax.set_xscale("log"); ax.invert_xaxis(); ax.set_xlabel("Grid spacing, dx (nm)"); ax.set_ylabel("Anisotropy, K_parallel/K_perpendicular")
        ax.grid(True, which="both", alpha=.25); fig.tight_layout(); fig.savefig(OUT / "figures" / f"Figure2_anisotropy.{ext}", dpi=600); plt.close(fig)

        metrics = ["K_parallel", "K_perpendicular"]
        fig, ax = plt.subplots(figsize=(5.2, 3.6))
        x = range(len(metrics)); fine = [f(gci_by_metric[m]["GCI_fine_percent"]) for m in metrics]; medium = [f(gci_by_metric[m]["GCI_medium_percent"]) for m in metrics]
        width = .36; ax.bar([i-width/2 for i in x], fine, width, label="Fine-grid GCI"); ax.bar([i+width/2 for i in x], medium, width, label="Medium-grid GCI")
        ax.set_xticks(list(x), ["K_parallel", "K_perpendicular"]); ax.set_ylabel("GCI (%)"); ax.set_yscale("log"); ax.grid(True, axis="y", alpha=.25); ax.legend(frameon=False); fig.tight_layout(); fig.savefig(OUT / "figures" / f"Figure3_GCI.{ext}", dpi=600); plt.close(fig)

        rp = [1.0 / x for x in k_p]; rt = [1.0 / x for x in k_t]
        fig, ax = plt.subplots(figsize=(5.2, 3.6)); ax.plot(dxs, rp, "s-", label="R_parallel"); ax.plot(dxs, rt, "^-", label="R_perpendicular")
        ax.set_xscale("log"); ax.invert_xaxis(); ax.set_yscale("log"); ax.set_xlabel("Grid spacing, dx (nm)"); ax.set_ylabel("Hydraulic resistance, R=1/K (m$^{-3}$)"); ax.grid(True, which="both", alpha=.25); ax.legend(frameon=False); fig.tight_layout(); fig.savefig(OUT / "figures" / f"Figure4_resistance_direction.{ext}", dpi=600); plt.close(fig)

    # Manuscript-style summary.
    fine_kp = gci_by_metric["K_parallel"]; fine_kt = gci_by_metric["K_perpendicular"]
    summary_md = f"""# G2 EX240 grid-convergence paper summary

## 1. Research objective

G2 verifies hydraulic transport through the explicitly resolved periodic EX240 nanogroove geometry using OpenLB LBM. The analysis compares transport parallel and perpendicular to the groove direction and quantifies sensitivity to `dx=5`, `2.5`, and `1.25 nm` grids.

## 2. Model parameters

The archived results use the recorded G2 configuration: D3Q19 forced lattice, Forced BGK collision, and Bouzidi wall treatment. This archive does not alter or reinterpret the recorded physical parameters.

## 3. Grid verification

`K_parallel` is `9.834075958643652e-23`, `9.782423697043172e-23`, and `9.764325526249012e-23 m^3` at `dx=5`, `2.5`, and `1.25 nm`, respectively. `K_perpendicular` is `4.4490220210459354e-23`, `4.3852935121144107e-23`, and `4.358613368821741e-23 m^3` on the same grids. Both sequences are monotonic under refinement; the perpendicular coefficient has the larger grid sensitivity.

## 4. Richardson and GCI

The recorded Richardson analysis reports apparent orders `p={fine_kp['apparent_order_p']}` for `K_parallel` and `p={fine_kt['apparent_order_p']}` for `K_perpendicular`. Fine-grid GCI values are `{fine_kp['GCI_fine_percent']}%` and `{fine_kt['GCI_fine_percent']}%`, respectively. The corresponding medium-grid GCI values are `{fine_kp['GCI_medium_percent']}%` and `{fine_kt['GCI_medium_percent']}%`. The mathematical asymptotic indicators are marked true in the source GCI file.

## 5. Driving-force linearity

No independent multi-force linearity table is present in the supplied G2 grid-convergence directory. Therefore this archive does not claim an R² or force-linearity result; that evidence must be cited from a separate validated dataset if used in a manuscript.

## 6. Directional transport and resistance

The recorded anisotropy `K_parallel/K_perpendicular` is `2.210390488544205`, `2.2307340819991053`, and `2.2402366762089274` for `dx=5`, `2.5`, and `1.25 nm`. Thus the parallel mobility is higher than the perpendicular mobility across the three grids. The reciprocal resistance ratio `R_perpendicular/R_parallel` is the same directional contrast expressed in resistance form.

## 7. Numerical limitations

The `dx=1.25 nm` EX240 perpendicular result has `run_gate_PASS=false`, `exit_code=3`, and recorded mass error `1.1967043900362632e-10`. Its numerical status is preserved in `G2_validation_status.md`; a mathematically valid GCI sequence does not convert this point into a full result PASS. The archive also contains no new grid or force-linearity calculations.

## 8. Input to later G3(h) studies

The archived GCI/cost balance supports using `dx=2.5 nm` as the production candidate for subsequent height-sweep studies, while retaining `dx=1.25 nm` as a reference grid. Endpoint or representative height cases should still be checked at the fine grid before treating a height trend as fully grid independent.
"""
    (OUT / "G2_paper_summary.md").write_text(summary_md)


if __name__ == "__main__":
    main()
