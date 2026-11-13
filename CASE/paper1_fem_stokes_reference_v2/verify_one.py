#!/usr/bin/env python3
"""Independently re-read a finished run and write a verification receipt.

This runs as a separate process from the solver. It re-hashes the saved fields,
rebuilds K and the diagnostics from the mesh and the fields, applies the frozen
acceptance rule, and records the digest of the solve receipt *as read*. If the
solve receipt changes afterwards, the assessor sees it.

Two fields are kept apart on purpose:
  actual_stop_reason   the first measured gate that was exceeded (a fact)
  post_hoc_acceptance  the classification that follows from the rule

Usage
    python3 verify_one.py --run h50_d25_T_20261114T010203Z_ab12cd34
    python3 verify_one.py --case h50_d25_T
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import receipt
import verify_results


def latest_run_for(case: str):
    candidates = receipt.case_run_dirs(case)
    if not candidates:
        return None
    return candidates[-1]


def additive_problems(verification: dict) -> list:
    """Checks this v2 layer adds on top of the unchanged v1 verifier.

    Two protocol statements were not enforced by v1's ``evaluate_gates``:

    * every output must be finite. A NaN silently passes comparisons such as
      ``value > 1e-10``, so finiteness has to be asserted, not implied.
    * the cross-groove protocol asks for the flux spread over "at least nine
      non-wall sections". v1 checked the spread but never the count.

    Both live here rather than in ``verify_results.py`` so that the verifier
    stays byte-identical to the one used for the existing 22 records.
    """
    problems = []
    levels = verification.get("levels", [])
    if not levels:
        return ["no level data to check"]
    fine_dx = min(row["dx_nm"] for row in levels)
    for row in levels:
        for key, value in row.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            if not math.isfinite(float(value)):
                problems.append(f"dx={row['dx_nm']:g}: non-finite value in {key}")
    for row in levels:
        if row["dx_nm"] != fine_dx:
            continue
        if row.get("direction") != "T":
            continue
        count = row.get("section_count")
        if count is None:
            problems.append(f"dx={fine_dx:g}: section count missing")
        elif int(count) < 9:
            problems.append(f"dx={fine_dx:g}: only {int(count)} non-wall sections, "
                            f"protocol requires at least 9")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default=None)
    parser.add_argument("--run-dir", default=None)
    parser.add_argument("--case", default=None)
    parser.add_argument("--replace", action="store_true",
                        help="overwrite an existing verification receipt")
    args = parser.parse_args()

    if args.run_dir:
        directory = Path(args.run_dir)
        case = directory.name.split("_2026")[0]
    elif args.run:
        directory = receipt.run_dir(args.run)
        case = directory.name.split("_2026")[0]
    elif args.case:
        candidates = receipt.case_run_dirs(args.case)
        if not candidates:
            print(f"REFUSED no solve receipt for {args.case}")
            return receipt.EXIT_BAD_INPUT
        if len(candidates) > 1:
            print(f"REFUSED {args.case} has {len(candidates)} attempts; "
                  f"pass --run-dir to choose")
            return receipt.EXIT_BAD_INPUT
        directory = candidates[0]
        case = args.case
    else:
        parser.error("choose --run or --case")

    solve_path = directory / "SOLVE_RECEIPT.json"
    if not solve_path.exists():
        print(f"no solve receipt at {solve_path}")
        return receipt.EXIT_BAD_INPUT

    try:
        manifest = receipt.verify_release()
    except receipt.ReleaseDrift as error:
        print(f"REFUSED release drift: {error}")
        return receipt.EXIT_RELEASE_DRIFT

    solve_bytes = solve_path.read_bytes()
    solve_digest = receipt.sha256_bytes(solve_bytes)
    solve = json.loads(solve_bytes)
    if solve.get("case") != case:
        print(f"REFUSED receipt case {solve.get('case')} is not the directory case {case}")
        return receipt.EXIT_BAD_INPUT

    problems = []
    if solve.get("state") != "SOLVED":
        problems.append(f"solve state is {solve.get('state')}, not SOLVED")
    if solve.get("exit_code") != 0:
        problems.append(f"solve exit_code is {solve.get('exit_code')}, not 0")
    if solve.get("release_sha256") != manifest["release_sha256"]:
        problems.append("solve receipt was produced by a different release")
    planned = solve.get("planned_levels_nm", [])
    solved_levels = [lvl["dx_nm"] for lvl in solve.get("levels", [])
                     if lvl.get("state") == "SOLVED"]
    if sorted(planned, reverse=True) != sorted(solved_levels, reverse=True):
        problems.append(f"solved levels {solved_levels} do not cover planned {planned}")

    # independent re-integration of every level from the saved fields
    case_dir = receipt.RESULTS / case
    frozen = receipt.point_for_case(case)
    for name in sorted(case_dir.glob("dx_*nm.json")):
        meta = json.loads(name.read_text())
        if meta.get("direction") != "T":
            problems.append(f"{name.name}: direction {meta.get('direction')} is not the "
                            f"frozen cross-groove direction")
        if (float(meta.get("h_nm", -1)), float(meta.get("d_nm", -1))) != (
                float(frozen["h_nm"]), float(frozen["d_nm"])):
            problems.append(f"{name.name}: geometry does not match the frozen point")
    for level in solve.get("levels", []):
        if level.get("state") != "SOLVED":
            continue
        field_path = case_dir / level["field_file"]
        if not field_path.exists():
            problems.append(f"missing field file {field_path.name}")
            continue
        actual = receipt.sha256_file(field_path)
        if actual != level.get("field_sha256_solver"):
            problems.append(f"dx={level['dx_nm']:g}: field hash differs from the "
                            f"solver-reported value")
        fingerprint = receipt.mesh_fingerprint(field_path)
        if fingerprint["mesh_sha256"] != level.get("mesh_sha256"):
            problems.append(f"dx={level['dx_nm']:g}: mesh fingerprint changed")
        if not receipt.level_json_matches(case, level):
            problems.append(f"dx={level['dx_nm']:g}: mesh JSON hash differs from the "
                            f"solver-recorded value")

    verification = verify_results.verify_case(case)
    additive = additive_problems(verification)
    gate_problems = additive + list(verification.get("problems", []))
    actual_stop_reason = gate_problems[0] if gate_problems else None
    solver_K = {lvl["dx_nm"]: lvl.get("K_m3") for lvl in solve.get("levels", [])}

    provenance_ok = not problems
    numerical_ok = not gate_problems
    if not numerical_ok:
        status = "LOCAL_CHECKS_FAIL"
    elif not provenance_ok:
        status = "PROVENANCE_INCOMPLETE"
    else:
        status = "REFERENCE_CANDIDATE"

    solve_after = receipt.sha256_file(solve_path)
    receipt_unchanged = solve_after == solve_digest
    if not receipt_unchanged:
        status = "PROVENANCE_INCOMPLETE"
        problems.append("solve receipt changed while verification was running")

    payload = {
        "schema": receipt.SCHEMA_VERIFY,
        "verify_run_id": receipt.new_run_id(case).replace(case, f"verify_{case}"),
        "case": case,
        "solve_run_id": solve["run_id"],
        "solve_receipt_sha256": solve_digest,
        "solve_receipt_unchanged": receipt_unchanged,
        "release_sha256": manifest["release_sha256"],
        "acceptance_rule_sha256": manifest["acceptance_rule_sha256"],
        "verified_at": receipt.utcnow(),
        "command": {"argv": sys.argv, "pid": __import__("os").getpid()},
        "environment": receipt.environment_snapshot(),
        "levels": [
            {"dx_nm": row["dx_nm"],
             "K_recomputed_m3": row["K_recomputed_m3"],
             "K_solver_m3": solver_K.get(row["dx_nm"]),
             "K_vs_solver_relative_difference": row["K_vs_solver_relative_difference"],
             "power_balance_recomputed_percent": row["power_balance_recomputed_percent"],
             "section_flux_spread_percent": row["section_flux_spread_percent"],
             "section_vs_volume_percent": row["section_vs_volume_percent"],
             "direct_relative_residual_recomputed": row["direct_relative_residual_recomputed"],
             "wall_velocity_relative_max": row["wall_velocity_relative_max"],
             "periodic_velocity_relative_max_difference":
                 row["periodic_velocity_relative_max_difference"],
             "pressure_periodic_relative_max_difference":
                 row["pressure_periodic_relative_max_difference"],
             "pressure_mean_normalized": row["pressure_mean_normalized"],
             "power_gate_applied": row.get("power_gate_applied"),
             "section_flux_gate_applied": row.get("section_flux_gate_applied"),
             "K_change_from_coarser_recomputed_percent":
                 row.get("K_change_from_coarser_recomputed_percent")}
            for row in verification.get("levels", [])
        ],
        "gate_scope_version": verification.get("gate_scope_version"),
        "gate_problems": gate_problems,
        "additive_gate_problems": additive,
        "additive_gates": ["all reported numbers finite",
                           "cross-groove finest level has at least 9 non-wall sections"],
        "diagnostics": verification.get("diagnostics", []),
        "provenance_problems": problems,
        "numeric_verdict": "PASS" if numerical_ok else "FAIL",
        "actual_stop_reason": actual_stop_reason,
        "post_hoc_acceptance": "PILOT_NUMERICAL_CHECKS_PASS" if numerical_ok
                              else "PILOT_CHECKS_FAIL",
        "reference_status": status,
        "reference_grant": "NOT_GRANTED_REQUIRES_SEPARATE_METHOD_REVIEW",
        "note": "REFERENCE_CANDIDATE is the highest label these scripts can set. "
                "It is not a formal reference qualification.",
    }
    out = directory / "VERIFY_RECEIPT.json"
    if out.exists() and not args.replace:
        print(f"REFUSED {out} already exists; a verification receipt is written once "
              f"(use --replace only with a written reason)")
        return receipt.EXIT_REFUSED_OVERWRITE
    if args.replace and out.exists():
        payload["replaces_sha256"] = receipt.sha256_file(out)
    digest = receipt.atomic_write_json(out, payload)
    print(json.dumps({"case": case, "status": status,
                      "actual_stop_reason": actual_stop_reason,
                      "provenance_problems": problems,
                      "verify_receipt_sha256": digest}, indent=2, ensure_ascii=False))
    return 0 if status == "REFERENCE_CANDIDATE" else receipt.EXIT_VERIFY_FAILED


if __name__ == "__main__":
    sys.exit(main())
