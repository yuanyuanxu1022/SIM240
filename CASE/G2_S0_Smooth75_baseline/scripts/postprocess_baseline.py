#!/usr/bin/env python3
import csv
import math
import sys
from pathlib import Path


def key_values(path):
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def first_row(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return next(csv.DictReader(handle))


def all_diagnostics_finite(path):
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return bool(rows) and all(row["finite"].strip().lower() in ("1", "true") for row in rows)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: postprocess_baseline.py RUN_DIRECTORY G2_BATCH")
    run_dir = Path(sys.argv[1]).resolve()
    g2_batch = Path(sys.argv[2]).resolve()
    steady = run_dir / "steady"
    result = key_values(steady / "result.txt")
    summary = first_row(steady / "result_summary.csv")
    exit_code = int((steady / "exit_code.txt").read_text().strip())

    k_num = float(summary["K_LBM"])
    k_analytic = float(summary["K_theory"])
    relative_error = abs(k_num - k_analytic) / k_analytic
    mass_error = float(result["max_mass_abs_relative"])
    mach = float(result["max_Mach"])
    run_id = run_dir.name
    diagnostics_finite = all_diagnostics_finite(steady / "diagnostics.csv")

    with (run_dir / "smooth_result.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["run_id", "dx", "tau", "force", "J", "K_smooth_num",
                  "K_smooth_analytic", "relative_error", "mass_error", "Mach"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow({
            "run_id": run_id,
            "dx": summary["dx"],
            "tau": summary["tau"],
            "force": summary["force"],
            "J": summary["J"],
            "K_smooth_num": f"{k_num:.17g}",
            "K_smooth_analytic": f"{k_analytic:.17g}",
            "relative_error": f"{relative_error:.17g}",
            "mass_error": f"{mass_error:.17g}",
            "Mach": f"{mach:.17g}",
        })

    g2_rows = {
        "parallel": first_row(g2_batch / "G2-P/steady/result_summary.csv"),
        "perpendicular": first_row(g2_batch / "G2-T/steady/result_summary.csv"),
    }
    kp = float(g2_rows["parallel"]["Keff"])
    kt = float(g2_rows["perpendicular"]["Keff"])
    anisotropy = kp / kt
    comparison = []
    for direction in ("parallel", "perpendicular"):
        row = g2_rows[direction]
        k_ex240 = float(row["Keff"])
        comparison.append({
            "direction": direction,
            "K_EX240": f"{k_ex240:.17g}",
            "K_smooth_num": f"{k_num:.17g}",
            "eta_K": f"{k_ex240 / k_num:.17g}",
            "R_eff": row["R_eff"],
            "anisotropy_ratio": f"{anisotropy:.17g}",
        })
    with (run_dir / "comparison_with_g2.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["direction", "K_EX240", "K_smooth_num", "eta_K", "R_eff",
                  "anisotropy_ratio"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(comparison)

    pass_value = (result.get("PASS", "false").lower() == "true"
                  and exit_code == 0 and diagnostics_finite)
    audit = key_values(steady / "boundary_audit.txt")
    report = f"""# G2-S0 Smooth75 numerical baseline validation

## Decision

- Smooth75: **{'PASS' if pass_value else 'FAIL'}**
- Normal application exit: `{exit_code == 0}`
- Converged: `{result.get('converged')}`
- All diagnostics finite: `{diagnostics_finite}`

## Frozen parameters

- dx = `{float(summary['dx']) * 1e9:.6g} nm`
- tau = `{summary['tau']}`
- acceleration = `{summary['force']} m/s2`
- D3Q19 + FORCE; ForcedBGK; planar zero-velocity Bouzidi; x/y periodic.

## Boundary and conservation audit

- fluid nodes: `{result.get('fluid_nodes')}`
- candidate/installed links: `{result.get('candidate_links')}/{result.get('installed_links')}`
- q range: `{result.get('q_min')} ... {result.get('q_max')}`
- fallback: `{result.get('fallback_count')}`
- unresolved: `{audit.get('unresolved_link_count', '0')}`
- maximum mass error: `{mass_error:.12e}`
- maximum density deviation: `{float(result['max_density_deviation']):.12e}`
- maximum Mach: `{mach:.12e}`

## Mobility result

- J_smooth = `{float(summary['J']):.12e} m2/s`
- K_smooth,num = `{k_num:.12e} m3`
- K_smooth,analytic = `{k_analytic:.12e} m3`
- absolute relative error = `{relative_error:.8%}`
- eta_parallel = `{kp / k_num:.12g}`
- eta_perpendicular = `{kt / k_num:.12g}`
- anisotropy = `{anisotropy:.12g}`

The existing analytical-reference ratios in the formal G2 result files were not
modified. The numerical-reference ratios are stored separately in
`comparison_with_g2.csv`.
"""
    (run_dir / "validation_report.md").write_text(report, encoding="utf-8")
    if not all(math.isfinite(v) for v in (k_num, k_analytic, relative_error,
                                           mass_error, mach, kp, kt)):
        raise SystemExit("non-finite postprocessed value")
    return 0 if pass_value else 3


if __name__ == "__main__":
    raise SystemExit(main())
