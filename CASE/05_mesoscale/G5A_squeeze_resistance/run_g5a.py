from __future__ import annotations

import argparse
from dataclasses import replace
import logging
import math
from pathlib import Path
import time

import numpy as np

from g5a_solver import analytic_metrics, evaluate_solution, solve_uniform_k
from g5a_inputs import build_nine_cases, load_config, load_transport_cases
from g5a_reporting import (
    make_direction_ratio_figure,
    make_impedance_figure,
    make_pressure_figure,
    sha256_file,
    write_case_results,
    write_manifest,
    write_profiles,
    write_validation_report,
)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="G5A quasi-static squeeze resistance model")
    parser.add_argument("--config", required=True, help="path to g5a_baseline.json")
    parser.add_argument("--repo-root", default=".", help="repository root for resolving the transport CSV")
    parser.add_argument(
        "--results-root",
        default=str(Path(__file__).resolve().parent / "results"),
        help="root directory for run output",
    )
    parser.add_argument("--run-id", default=time.strftime("run_%Y%m%d_%H%M%S"))
    return parser.parse_args(argv)


def prepare_run_directory(results_root: str, run_id: str) -> Path:
    run_dir = Path(results_root) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _spread(values: list[float]) -> float:
    ref = values[len(values) // 2]
    if ref == 0.0:
        return float(max(values) - min(values))
    return float(max(values) - min(values)) / abs(ref)


def _check_linearity(config, case) -> bool:
    pmax_over_vp: list[float] = []
    force_over_vp: list[float] = []
    for multiplier in config.linearity_multipliers:
        problem = replace(config.problem, vp_m_s=config.problem.vp_m_s * multiplier)
        solution = solve_uniform_k(problem, case.K_m3)
        metrics = evaluate_solution(problem, case.K_m3, solution)
        pmax_over_vp.append(metrics.pmax_pa / problem.vp_m_s)
        force_over_vp.append(metrics.force_n / problem.vp_m_s)
    tol = config.thresholds["linearity_relative"]
    return _spread(pmax_over_vp) < tol and _spread(force_over_vp) < tol


def run_model(config_path, repo_root, results_root, run_id) -> Path:
    config_path = Path(config_path)
    repo_root = Path(repo_root)
    results_root = Path(results_root)
    run_dir = Path(results_root) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    config = load_config(config_path)
    csv_path = repo_root / config.transport_database
    rows = load_transport_cases(csv_path, config)
    cases = build_nine_cases(config, rows)

    gates: dict[str, bool] = {"INPUT_GATE": True}

    case_rows: list[dict[str, object]] = []
    profile_rows: list[dict[str, object]] = []
    numerical_flags: list[bool] = []
    analytic_flags: list[bool] = []
    mass_flags: list[bool] = []
    linearity_flags: list[bool] = []

    for case in cases:
        solution = solve_uniform_k(config.problem, case.K_m3)
        metrics = evaluate_solution(config.problem, case.K_m3, solution)
        exact = analytic_metrics(config.problem, case.K_m3)

        finite = (
            math.isfinite(metrics.pmax_pa)
            and math.isfinite(metrics.force_n)
            and math.isfinite(metrics.impedance_n_s_m)
            and math.isfinite(metrics.q_out_m3_s)
            and bool(np.all(np.isfinite(solution.pressure_pa)))
            and bool(np.all(np.isfinite(solution.face_flux_m2_s)))
        )
        pressure_ok = bool(np.all(solution.pressure_pa >= config.problem.p_out_pa))
        symmetry_ok = metrics.symmetry_relative_error < config.thresholds["symmetry_relative"]
        pmax_ok = metrics.pmax_relative_error < config.thresholds["pmax_relative"]
        force_ok = metrics.force_relative_error < config.thresholds["load_relative"]
        mass_ok = metrics.mass_relative_error < config.thresholds["mass_relative"]
        linearity_ok = _check_linearity(config, case)

        numerical_flags.append(finite and pressure_ok and symmetry_ok)
        analytic_flags.append(pmax_ok and force_ok)
        mass_flags.append(mass_ok)
        linearity_flags.append(linearity_ok)

        case_pass = finite and pressure_ok and symmetry_ok and pmax_ok and force_ok and mass_ok and linearity_ok

        case_rows.append(
            {
                "run_id": run_id,
                "height_nm": case.height_nm,
                "model": case.model,
                "direction": case.direction,
                "K_m3": case.K_m3,
                "R_input_pa_s_m3": case.R_input_pa_s_m3,
                "Vp_m_s": config.problem.vp_m_s,
                "N": config.problem.n_cells,
                "pmax_num_Pa": metrics.pmax_pa,
                "pmax_exact_Pa": exact.pmax_pa,
                "pmax_rel_error": metrics.pmax_relative_error,
                "Fz_num_N": metrics.force_n,
                "Fz_exact_N": exact.force_n,
                "Fz_rel_error": metrics.force_relative_error,
                "CF_num_N_s_m": metrics.impedance_n_s_m,
                "CF_exact_N_s_m": exact.impedance_n_s_m,
                "Qout_m3_s": metrics.q_out_m3_s,
                "Qdisplaced_m3_s": metrics.q_displaced_m3_s,
                "mass_rel_error": metrics.mass_relative_error,
                "status": "PASS" if case_pass else "FAIL",
            }
        )

        for center, pressure in zip(solution.centers_m, solution.pressure_pa):
            profile_rows.append(
                {
                    "run_id": run_id,
                    "height_nm": case.height_nm,
                    "model": case.model,
                    "direction": case.direction,
                    "centers_m": float(center),
                    "pressure_pa": float(pressure),
                }
            )

    direction_flags: list[bool] = []
    case_by_key = {(row["height_nm"], row["direction"]): row for row in case_rows}
    case_def_by_key = {(c.height_nm, c.direction): c for c in cases}
    for height in config.heights_nm:
        k_parallel = case_def_by_key[(height, "parallel")].K_m3
        k_perp = case_def_by_key[(height, "perpendicular")].K_m3
        cf_parallel = float(case_by_key[(height, "parallel")]["CF_num_N_s_m"])
        cf_perp = float(case_by_key[(height, "perpendicular")]["CF_num_N_s_m"])
        cf_ratio = cf_perp / cf_parallel
        k_ratio = k_parallel / k_perp
        direction_flags.append(
            abs(cf_ratio / k_ratio - 1.0) < config.thresholds["direction_ratio_relative"]
        )

    gates["NUMERICAL_GATE"] = all(numerical_flags)
    gates["ANALYTIC_GATE"] = all(analytic_flags)
    gates["MASS_GATE"] = all(mass_flags)
    gates["LINEARITY_GATE"] = all(linearity_flags) and all(direction_flags)
    gates["RESULT_PASS"] = all(gates.values()) and all(row["status"] == "PASS" for row in case_rows)

    write_case_results(run_dir / "case_results.csv", case_rows)
    write_profiles(run_dir / "pressure_profiles.csv", profile_rows)

    manifest = {
        "run_id": run_id,
        "transport_database": config.transport_database,
        "transport_database_sha256": sha256_file(csv_path),
        "source_grid_dx_nm": config.source_grid_dx_nm,
        "n_cells": config.problem.n_cells,
        "heights_nm": list(config.heights_nm),
        "length_m": config.problem.length_m,
        "width_m": config.problem.width_m,
        "mu_pa_s": config.problem.mu_pa_s,
        "vp_m_s": config.problem.vp_m_s,
        "p_out_pa": config.problem.p_out_pa,
        "schema_version": 1,
        "run_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    write_manifest(run_dir / "input_manifest.json", manifest)

    make_pressure_figure(run_dir / "Figure_G5_pressure_profiles.png", profile_rows)
    make_impedance_figure(run_dir / "Figure_G5_squeeze_impedance_vs_h.png", case_rows)
    make_direction_ratio_figure(run_dir / "Figure_G5_directional_ratio_vs_h.png", case_rows)

    write_validation_report(
        run_dir / "validation_report.md",
        gates,
        {
            "input_closure_status": "CANDIDATE_FIXED_GRID",
            "source_grid_dx_nm": config.source_grid_dx_nm,
            "n_cells": config.problem.n_cells,
        },
    )

    logging.info("G5A run complete: %d cases, RESULT_PASS=%s", len(case_rows), gates["RESULT_PASS"])
    return run_dir


def write_failed_report_if_missing(run_dir: Path) -> None:
    report_path = Path(run_dir) / "validation_report.md"
    if not report_path.exists():
        write_validation_report(report_path, {}, {})


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_dir = prepare_run_directory(args.results_root, args.run_id)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(run_dir / "run.log", mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)

    exit_code = 1
    try:
        run_model(args.config, args.repo_root, args.results_root, args.run_id)
        exit_code = 0
    except Exception:
        logger.exception("G5A run failed")
        write_failed_report_if_missing(run_dir)
        exit_code = 3
    finally:
        (run_dir / "exit_code.txt").write_text(f"{exit_code}\n", encoding="utf-8")
        handler.close()
        logger.removeHandler(handler)
    print(f"G5A exit_code={exit_code} run_dir={run_dir}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
