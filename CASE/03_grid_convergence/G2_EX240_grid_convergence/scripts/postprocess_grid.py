#!/usr/bin/env python3
"""Create the formal G2 Step-3 grid-convergence evidence package."""

from __future__ import annotations

import csv
import math
import shutil
import subprocess
import sys
from pathlib import Path


MASS_GATE = 1.0e-10
MACH_GATE = 0.05
Q_TOLERANCE = 1.0e-10
R = 2.0
SAFETY_FACTOR = 1.25
ASYMPTOTIC_MIN = 0.95
ASYMPTOTIC_MAX = 1.05
FINE_GCI_TARGET_PERCENT = 2.0
RELATIVE_STABILITY_TARGET = 0.01

GRIDS = (("5", 5.0), ("2p5", 2.5), ("1p25", 1.25))
CASES = (
    ("Smooth75", "smooth"),
    ("EX240_parallel", "parallel"),
    ("EX240_perpendicular", "perpendicular"),
)


def parse_key_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def parse_bool(value: str | None) -> bool:
    return str(value).strip().lower() == "true"


def load_run(batch_dir: Path, tag: str, dx_nm: float, case_name: str, direction: str) -> dict[str, object]:
    run_id = f"dx{tag}_{case_name}"
    run_root = batch_dir / "runs" / f"dx{tag}" / case_name
    steady_dir = run_root / "steady"
    precheck_dir = run_root / "precheck"
    result = parse_key_values(steady_dir / "result.txt")
    precheck = parse_key_values(precheck_dir / "result.txt")
    exit_code = int((steady_dir / "exit_code.txt").read_text().strip())
    precheck_exit = int((precheck_dir / "exit_code.txt").read_text().strip())

    if direction == "smooth":
        j_value = float(result["J_m2_s"])
        k_value = float(result["K_LBM_m3"])
        analytic_k = float(result["K_theory_m3"])
    else:
        j_value = float(result["J_main_m2_s"])
        k_value = float(result["Keff_m3"])
        analytic_k = float("nan")

    candidate_links = int(result["candidate_links"])
    installed_links = int(result["installed_links"])
    q_min = float(result["q_min"])
    q_max = float(result["q_max"])
    fallback = int(result["fallback_count"])
    unresolved = int(result["unresolved_links"])
    boundary_pass = (
        precheck_exit == 0
        and parse_bool(precheck.get("geometry_PASS"))
        and parse_bool(precheck.get("q_audit_PASS"))
        and candidate_links == installed_links
        and math.isclose(q_min, 0.5, rel_tol=0.0, abs_tol=Q_TOLERANCE)
        and math.isclose(q_max, 0.5, rel_tol=0.0, abs_tol=Q_TOLERANCE)
        and fallback == 0
        and unresolved == 0
    )
    mass_error = float(result["max_mass_abs_relative"])
    mach = float(result["max_Mach"])
    finite = parse_bool(result.get("finite"))
    converged = parse_bool(result.get("converged"))
    material_unchanged = parse_bool(result.get("material_unchanged"))
    normal_exit = exit_code == 0 and int(result.get("exit_code", "1")) == 0
    result_pass = parse_bool(result.get("PASS"))
    run_gate = (
        mass_error <= MASS_GATE
        and mach < MACH_GATE
        and finite
        and converged
        and material_unchanged
        and normal_exit
        and boundary_pass
        and result_pass
    )
    rho_min = float(result["rho_min"])
    rho_max = float(result["rho_max"])

    return {
        "run_id": run_id,
        "dx": float(result["dx_m"]),
        "dx_nm": dx_nm,
        "dt": float(result["dt_s"]),
        "tau": float(result["tau"]),
        "case": case_name,
        "direction": direction,
        "J": j_value,
        "Keff": k_value,
        "K_analytic": analytic_k,
        "K_smooth": float("nan"),
        "eta_K": float("nan"),
        "anisotropy": float("nan"),
        "R_eff": 1000.0 * 1.0e5 / j_value,
        "mass_error": mass_error,
        "rho_min": rho_min,
        "rho_max": rho_max,
        "rho_range": rho_max - rho_min,
        "Mach": mach,
        "convergence_step": int(result["steps_completed"]),
        "exit_code": exit_code,
        "fluid_nodes": int(result["fluid_nodes"]),
        "candidate_links": candidate_links,
        "installed_links": installed_links,
        "q_min": q_min,
        "q_max": q_max,
        "fallback": fallback,
        "unresolved": unresolved,
        "nu_phys": float(result["nu_phys_m2_s"]),
        "nu_lattice": float(result["nu_lattice"]),
        "a_phys": 1.0e5,
        "a_lattice": float(result["a_lattice"]),
        "velocity_conversion": float(result["velocity_conversion_m_s_per_lattice"]),
        "convergence_PASS": converged,
        "finite_PASS": finite,
        "material_unchanged": material_unchanged,
        "normal_exit_PASS": normal_exit,
        "boundary_audit_PASS": boundary_pass,
        "run_gate_PASS": run_gate,
    }


def relative_span(values: list[float]) -> float:
    mean = sum(values) / len(values)
    return (max(values) - min(values)) / abs(mean)


def richardson(metric: str, values_by_dx: dict[float, float]) -> dict[str, object]:
    fine = values_by_dx[1.25]
    medium = values_by_dx[2.5]
    coarse = values_by_dx[5.0]
    result: dict[str, object] = {
        "metric": metric,
        "fine_dx_nm": 1.25,
        "medium_dx_nm": 2.5,
        "coarse_dx_nm": 5.0,
        "fine_value": fine,
        "medium_value": medium,
        "coarse_value": coarse,
        "relative_span": relative_span([fine, medium, coarse]),
        "convergence_type": "undetermined",
        "apparent_order_p": "",
        "richardson_extrapolated": "",
        "GCI_fine": "",
        "GCI_medium": "",
        "GCI_fine_percent": "",
        "GCI_medium_percent": "",
        "asymptotic_ratio": "",
        "asymptotic_PASS": False,
        "mathematical_valid": False,
        "diagnosis": "",
    }
    if not all(math.isfinite(value) for value in (fine, medium, coarse)):
        result["diagnosis"] = "non-finite grid value"
        return result
    d21 = medium - fine
    d32 = coarse - medium
    scale = max(abs(fine), abs(medium), abs(coarse), 1.0e-300)
    difference_tolerance = 1.0e-14 * scale
    if abs(d21) <= difference_tolerance or abs(d32) <= difference_tolerance:
        result["diagnosis"] = "grid difference is near zero"
        return result
    if d21 * d32 <= 0.0:
        result["convergence_type"] = "oscillatory_or_non_monotonic"
        result["diagnosis"] = "successive grid differences have opposite signs"
        return result
    result["convergence_type"] = "monotonic"
    ratio = abs(d32 / d21)
    p_value = math.log(ratio) / math.log(R)
    if not math.isfinite(p_value) or p_value <= 0.0:
        result["diagnosis"] = "apparent order is non-positive or non-finite"
        return result
    denominator = R**p_value - 1.0
    if abs(denominator) <= 1.0e-12:
        result["diagnosis"] = "Richardson denominator is near zero"
        return result
    extrapolated = fine + (fine - medium) / denominator
    if abs(fine) <= 1.0e-300 or abs(medium) <= 1.0e-300:
        result["diagnosis"] = "relative-error denominator is near zero"
        return result
    ea_fine = abs((fine - medium) / fine)
    ea_medium = abs((medium - coarse) / medium)
    gci_fine = SAFETY_FACTOR * ea_fine / denominator
    gci_medium = SAFETY_FACTOR * ea_medium / denominator
    if gci_fine <= 0.0:
        result["diagnosis"] = "fine-grid GCI is zero or negative"
        return result
    asymptotic_ratio = gci_medium / (R**p_value * gci_fine)
    asymptotic_pass = ASYMPTOTIC_MIN <= asymptotic_ratio <= ASYMPTOTIC_MAX
    result.update({
        "apparent_order_p": p_value,
        "richardson_extrapolated": extrapolated,
        "GCI_fine": gci_fine,
        "GCI_medium": gci_medium,
        "GCI_fine_percent": 100.0 * gci_fine,
        "GCI_medium_percent": 100.0 * gci_medium,
        "asymptotic_ratio": asymptotic_ratio,
        "asymptotic_PASS": asymptotic_pass,
        "mathematical_valid": True,
        "diagnosis": "asymptotic range confirmed" if asymptotic_pass else "asymptotic-range check failed",
    })
    return result


def fmt(value: object, spec: str = ".8e") -> str:
    if value == "" or value is None:
        return "n.a."
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    return format(float(value), spec)


def save_figures(batch_dir: Path, grid_values: dict[float, dict[str, float]], gci_rows: list[dict[str, object]]) -> None:
    figures = batch_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    dxs = sorted(grid_values)
    if shutil.which("gnuplot") is None:
        raise RuntimeError("gnuplot is required for Step 3 figure generation")

    def quote(path: Path) -> str:
        return str(path).replace("'", "''")

    def render(stem: str, body: str) -> None:
        png = quote(figures / f"{stem}.png")
        pdf = quote(figures / f"{stem}.pdf")
        common = (
            "set encoding utf8\n"
            "set datafile separator ','\n"
            "set border linewidth 1.2\n"
            "set grid back lc rgb '#d9d9d9'\n"
            "set key opaque\n"
        )
        script = (
            common
            + "set terminal pngcairo size 1800,1200 enhanced font 'DejaVu Sans,20'\n"
            + f"set output '{png}'\n"
            + body
            + "unset output\n"
            + "set terminal pdfcairo size 6.5in,4.4in enhanced font 'DejaVu Sans,11'\n"
            + f"set output '{pdf}'\n"
            + "replot\n"
            + "unset output\n"
        )
        subprocess.run(["gnuplot"], input=script, text=True, check=True)

    data_paths: list[Path] = []
    try:
        for metric, label, stem, color in (
            ("K_parallel", "K_parallel (m^3)", "Figure_G2_grid_K_parallel", "#2166ac"),
            ("K_perpendicular", "K_perpendicular (m^3)", "Figure_G2_grid_K_perpendicular", "#b2182b"),
        ):
            data = figures / f".{stem}.csv"
            data_paths.append(data)
            data.write_text("\n".join(f"{dx},{grid_values[dx][metric]:.17g}" for dx in dxs) + "\n")
            body = (
                "set xlabel 'Grid spacing dx (nm)'\n"
                f"set ylabel '{label}'\n"
                "set key off\n"
                f"plot '{quote(data)}' using 1:2 with linespoints lw 2.5 pt 7 ps 1.2 lc rgb '{color}'\n"
            )
            render(stem, body)

        eta_data = figures / ".Figure_G2_grid_eta.csv"
        data_paths.append(eta_data)
        eta_data.write_text(
            "\n".join(
                f"{dx},{grid_values[dx]['eta_parallel']:.17g},{grid_values[dx]['eta_perpendicular']:.17g}"
                for dx in dxs
            ) + "\n"
        )
        render(
            "Figure_G2_grid_eta",
            "set xlabel 'Grid spacing dx (nm)'\n"
            "set ylabel 'Same-grid smooth-normalized mobility'\n"
            "set key top left\n"
            f"plot '{quote(eta_data)}' using 1:2 with linespoints lw 2.5 pt 7 ps 1.2 title 'eta_parallel', "
            f"'{quote(eta_data)}' using 1:3 with linespoints lw 2.5 pt 5 ps 1.2 title 'eta_perpendicular'\n",
        )

        anisotropy_data = figures / ".Figure_G2_grid_anisotropy.csv"
        data_paths.append(anisotropy_data)
        anisotropy_data.write_text(
            "\n".join(f"{dx},{grid_values[dx]['anisotropy']:.17g}" for dx in dxs) + "\n"
        )
        render(
            "Figure_G2_grid_anisotropy",
            "set xlabel 'Grid spacing dx (nm)'\n"
            "set ylabel 'K_parallel / K_perpendicular'\n"
            "set key off\n"
            f"plot '{quote(anisotropy_data)}' using 1:2 with linespoints lw 2.5 pt 7 ps 1.2 lc rgb '#4d9221'\n",
        )

        absolute = [row for row in gci_rows if row["metric"] in ("K_smooth", "K_parallel", "K_perpendicular")]
        gci_data = figures / ".Figure_G2_grid_GCI_summary.csv"
        data_paths.append(gci_data)
        gci_data.write_text(
            "\n".join(
                f"{str(row['metric']).replace('K_', '')},"
                f"{float(row['GCI_fine_percent']) if row['GCI_fine_percent'] != '' else 0.0},"
                f"{float(row['GCI_medium_percent']) if row['GCI_medium_percent'] != '' else 0.0}"
                for row in absolute
            ) + "\n"
        )
        render(
            "Figure_G2_grid_GCI_summary",
            "set style data histograms\n"
            "set style histogram clustered gap 1\n"
            "set style fill solid 0.85 border -1\n"
            "set boxwidth 0.85\n"
            "set ylabel 'GCI (%)'\n"
            "set xlabel 'Mobility metric'\n"
            f"set arrow from graph 0, first {FINE_GCI_TARGET_PERCENT} to graph 1, first {FINE_GCI_TARGET_PERCENT} nohead dt 2 lw 1.5\n"
            "set key top right\n"
            f"plot '{quote(gci_data)}' using 2:xtic(1) title 'GCI fine', '' using 3 title 'GCI medium'\n",
        )
    finally:
        for path in data_paths:
            path.unlink(missing_ok=True)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: postprocess_grid.py BATCH_DIR")
    batch_dir = Path(sys.argv[1]).resolve()
    rows: list[dict[str, object]] = []
    for tag, dx_nm in GRIDS:
        for case_name, direction in CASES:
            rows.append(load_run(batch_dir, tag, dx_nm, case_name, direction))

    grid_values: dict[float, dict[str, float]] = {}
    for _, dx_nm in GRIDS:
        subset = {str(row["direction"]): row for row in rows if float(row["dx_nm"]) == dx_nm}
        smooth = float(subset["smooth"]["Keff"])
        parallel = float(subset["parallel"]["Keff"])
        perpendicular = float(subset["perpendicular"]["Keff"])
        anisotropy = parallel / perpendicular
        grid_values[dx_nm] = {
            "K_smooth": smooth,
            "K_parallel": parallel,
            "K_perpendicular": perpendicular,
            "eta_parallel": parallel / smooth,
            "eta_perpendicular": perpendicular / smooth,
            "anisotropy": anisotropy,
        }
        for row in rows:
            if float(row["dx_nm"]) != dx_nm:
                continue
            row["K_smooth"] = smooth
            row["anisotropy"] = anisotropy
            if row["direction"] == "smooth":
                row["eta_K"] = 1.0
            elif row["direction"] == "parallel":
                row["eta_K"] = parallel / smooth
            else:
                row["eta_K"] = perpendicular / smooth

    summary_columns = [
        "run_id", "dx", "dt", "tau", "case", "direction", "J", "Keff", "K_smooth",
        "eta_K", "anisotropy", "R_eff", "mass_error", "rho_min", "rho_max", "rho_range",
        "Mach", "convergence_step", "exit_code", "fluid_nodes", "candidate_links", "installed_links",
        "q_min", "q_max", "fallback", "unresolved", "nu_phys", "nu_lattice", "a_phys",
        "a_lattice", "velocity_conversion", "convergence_PASS", "finite_PASS", "material_unchanged",
        "normal_exit_PASS", "boundary_audit_PASS", "run_gate_PASS",
    ]
    with (batch_dir / "g2_grid_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=summary_columns)
        writer.writeheader()
        for row in sorted(rows, key=lambda item: (-float(item["dx_nm"]), str(item["direction"]))):
            writer.writerow({column: row[column] for column in summary_columns})

    metric_names = (
        "K_smooth", "K_parallel", "K_perpendicular",
        "eta_parallel", "eta_perpendicular", "anisotropy",
    )
    gci_rows = [
        richardson(metric, {dx: values[metric] for dx, values in grid_values.items()})
        for metric in metric_names
    ]
    gci_columns = list(gci_rows[0])
    with (batch_dir / "g2_richardson_gci.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=gci_columns)
        writer.writeheader()
        writer.writerows(gci_rows)

    gci_by_metric = {str(row["metric"]): row for row in gci_rows}
    run_gate_pass = all(bool(row["run_gate_PASS"]) for row in rows)
    absolute_math_pass = all(
        bool(gci_by_metric[metric]["mathematical_valid"])
        and bool(gci_by_metric[metric]["asymptotic_PASS"])
        for metric in ("K_smooth", "K_parallel", "K_perpendicular")
    )
    fine_uncertainty_pass = all(
        gci_by_metric[metric]["GCI_fine_percent"] != ""
        and float(gci_by_metric[metric]["GCI_fine_percent"]) <= FINE_GCI_TARGET_PERCENT
        for metric in ("K_parallel", "K_perpendicular")
    )
    step3_pass = run_gate_pass and absolute_math_pass and fine_uncertainty_pass

    recommendation = "none: Step 3 gate failed or is inconclusive"
    recommendation_basis = "Production-grid selection is blocked until the Step 3 gate passes."
    if step3_pass:
        extrapolated = {
            metric: float(gci_by_metric[metric]["richardson_extrapolated"])
            for metric in ("K_parallel", "K_perpendicular")
        }
        fine_relative = grid_values[1.25]
        eligible: list[float] = []
        for dx_nm in (5.0, 2.5, 1.25):
            values = grid_values[dx_nm]
            absolute_ok = all(
                abs(values[metric] - extrapolated[metric]) / abs(extrapolated[metric])
                <= FINE_GCI_TARGET_PERCENT / 100.0
                for metric in ("K_parallel", "K_perpendicular")
            )
            relative_ok = all(
                abs(values[metric] - fine_relative[metric]) / abs(fine_relative[metric])
                <= RELATIVE_STABILITY_TARGET
                for metric in ("eta_parallel", "eta_perpendicular", "anisotropy")
            )
            if absolute_ok and relative_ok:
                eligible.append(dx_nm)
        if eligible:
            selected = max(eligible)
            recommendation = f"dx={selected:g} nm"
            recommendation_basis = (
                "Coarsest grid meeting <=2% extrapolated error for both principal mobilities "
                "and <=1% deviation from fine-grid eta/anisotropy."
            )
        else:
            recommendation = "none: even the fine grid misses the frozen production criteria"
            recommendation_basis = "A finer grid is required before production selection."

    save_figures(batch_dir, grid_values, gci_rows)

    report = [
        "# SIM240 G2 Step 3 grid-convergence report",
        "",
        f"Step 3 status: **{'PASS' if step3_pass else 'FAIL / INCONCLUSIVE'}**",
        "",
        f"- nine-run numerical gate: {'PASS' if run_gate_pass else 'FAIL'}",
        f"- absolute-mobility asymptotic GCI: {'PASS' if absolute_math_pass else 'FAIL / NOT APPLICABLE'}",
        f"- EX240 fine-grid GCI <= 2%: {'PASS' if fine_uncertainty_pass else 'FAIL / NOT APPLICABLE'}",
        f"- recommended production grid: **{recommendation}**",
        f"- basis: {recommendation_basis}",
        "",
        "## Three-grid transport results",
        "",
        "| dx (nm) | K_smooth (m3) | K_parallel (m3) | K_perpendicular (m3) | eta_parallel | eta_perpendicular | anisotropy |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for dx_nm in (5.0, 2.5, 1.25):
        values = grid_values[dx_nm]
        report.append(
            f"| {dx_nm:g} | {values['K_smooth']:.16e} | {values['K_parallel']:.16e} | "
            f"{values['K_perpendicular']:.16e} | {values['eta_parallel']:.12g} | "
            f"{values['eta_perpendicular']:.12g} | {values['anisotropy']:.12g} |"
        )
    report.extend([
        "",
        "## Richardson and GCI",
        "",
        "| Metric | Type | p | extrapolated | GCI fine (%) | GCI medium (%) | asymptotic ratio | Check | Diagnosis |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ])
    for item in gci_rows:
        check = "PASS" if item["mathematical_valid"] and item["asymptotic_PASS"] else "FAIL / n.a."
        report.append(
            f"| {item['metric']} | {item['convergence_type']} | {fmt(item['apparent_order_p'], '.6g')} | "
            f"{fmt(item['richardson_extrapolated'], '.16e')} | {fmt(item['GCI_fine_percent'], '.6g')} | "
            f"{fmt(item['GCI_medium_percent'], '.6g')} | {fmt(item['asymptotic_ratio'], '.6g')} | "
            f"{check} | {item['diagnosis']} |"
        )
    report.extend([
        "",
        "## Relative-metric three-grid spans",
        "",
        f"- eta_parallel: {100.0 * float(gci_by_metric['eta_parallel']['relative_span']):.8g}%",
        f"- eta_perpendicular: {100.0 * float(gci_by_metric['eta_perpendicular']['relative_span']):.8g}%",
        f"- anisotropy: {100.0 * float(gci_by_metric['anisotropy']['relative_span']):.8g}%",
        "",
        "Orders and GCI values marked `n.a.` were intentionally not forced. See the diagnosis column.",
        "",
        "## Gate boundaries",
        "",
        "This report closes only G2 Step 3. It does not start G3, dynamic-punch, or two-phase work.",
        "",
    ])
    (batch_dir / "G2_GRID_CONVERGENCE_REPORT.md").write_text("\n".join(report))
    print(f"STEP3={'PASS' if step3_pass else 'FAIL_OR_INCONCLUSIVE'}")
    print(f"production_grid={recommendation}")
    return 0 if step3_pass else 3


if __name__ == "__main__":
    raise SystemExit(main())
