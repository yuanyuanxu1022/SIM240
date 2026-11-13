#!/usr/bin/env python3
"""Solve one frozen point and write a run receipt as it goes.

The solver itself (``fem_pilot.py``) is unchanged from the v1 pilot. This
wrapper adds, in this order and nothing else:

1. release check (refuses before creating any directory);
2. authorization check against the current release digest;
3. refusal to reuse an existing results directory;
4. a run directory with a receipt opened as STARTED;
5. one mesh level at a time, receipt rewritten atomically after each level;
6. a truthful FAILED / TIMEOUT receipt on any error, with no retry.

Usage
    python3 run_one.py --case h50_d25_T --plan
    python3 run_one.py --case h50_d25_T --execute
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import signal
import sys
import time
import traceback
from pathlib import Path

import fem_pilot
import receipt


class BudgetExceeded(RuntimeError):
    pass


def _alarm(signum, frame):
    raise BudgetExceeded("mesh level exceeded its wall-clock budget")


def plan(case: str) -> dict:
    point = receipt.point_for_case(case)
    return {
        "case": case,
        "point": point,
        "release": (receipt.release_digest()
                    if receipt.MANIFEST_PATH.exists() else "NOT_FROZEN"),
        "authorized": bool(receipt.load_authorization()
                           and case in receipt.load_authorization().get("granted_cases", [])),
        "results_dir_exists": (receipt.RESULTS / case).exists(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--levels", nargs="+", type=float, default=[5.0, 2.5, 1.25])
    parser.add_argument("--level-budget", type=float, default=1800.0,
                        help="wall-clock cap per mesh level, seconds")
    parser.add_argument("--total-budget", type=float, default=7200.0,
                        help="wall-clock cap for the whole case, seconds")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--new-attempt", metavar="REASON", default=None,
                        help="explicitly record why a case is attempted again")
    args = parser.parse_args()

    if args.plan:
        print(json.dumps(plan(args.case), indent=2, ensure_ascii=False))
        return 0
    if not args.execute:
        parser.error("choose --plan or --execute")

    # 1. package integrity, before anything is written
    try:
        manifest = receipt.verify_release()
    except receipt.ReleaseDrift as error:
        print(f"REFUSED release drift: {error}")
        return receipt.EXIT_RELEASE_DRIFT

    # 2. authorization against this exact release
    try:
        clearance = receipt.check_authorization(args.case)
    except (PermissionError, KeyError) as error:
        print(f"REFUSED not authorized: {error}")
        return receipt.EXIT_UNAUTHORIZED
    point = clearance["point"]

    # 3. never reuse an existing case directory
    case_dir = receipt.RESULTS / args.case
    if case_dir.exists():
        print(f"REFUSED {case_dir} already exists; a run must start from a clean "
              f"case directory so the receipt cannot mix two attempts")
        return receipt.EXIT_REFUSED_OVERWRITE

    previous = receipt.case_run_dirs(args.case)
    if previous and not args.new_attempt:
        print(f"REFUSED {args.case} already has an attempt at {previous[-1].name}; "
              f"this package performs one attempt per case per release. A further "
              f"attempt needs --new-attempt with a written reason")
        return receipt.EXIT_REFUSED_OVERWRITE

    levels = sorted(args.levels, reverse=True)
    run_id = receipt.new_run_id(args.case)
    directory = receipt.run_dir(run_id)
    directory.mkdir(parents=True, exist_ok=False)
    receipt_path = directory / "SOLVE_RECEIPT.json"

    record = {
        "schema": receipt.SCHEMA_SOLVE,
        "run_id": run_id,
        "case": args.case,
        "geometry": {"h_nm": point["h_nm"], "d_nm": point["d_nm"],
                     "w_nm": receipt.load_points()["constants"]["w_nm"],
                     "P_nm": receipt.load_points()["constants"]["P_nm"],
                     "direction": "T"},
        "package": receipt.PACKAGE.name,
        "release_sha256": manifest["release_sha256"],
        "acceptance_rule_sha256": manifest["acceptance_rule_sha256"],
        "point_set_sha256": manifest["point_set_sha256"],
        "command": {"argv": sys.argv, "cwd": os.getcwd(),
                    "interpreter": sys.executable, "pid": os.getpid(),
                    "hostname": platform.node()},
        "environment": receipt.environment_snapshot(),
        "planned_levels_nm": levels,
        "level_budget_seconds": args.level_budget,
        "total_budget_seconds": args.total_budget,
        "attempt": {"index": len(previous) + 1, "reason": args.new_attempt},
        "state": "STARTED",
        "started_at": receipt.utcnow(),
        "finished_at": None,
        "wall_seconds": None,
        "peak_rss_kb": None,
        "levels": [],
        "error": None,
        "notes": [
            "state STARTED is written before the first mesh level is solved",
            "each level is appended and the receipt rewritten atomically afterwards",
            "no retry, no refinement and no threshold change is performed by this wrapper",
            "exit_code is written by the solving process itself",
        ],
    }
    receipt.atomic_write_json(receipt_path, record)
    started = time.monotonic()
    print(f"RUN {run_id} release={manifest['release_sha256'][:12]} "
          f"levels={levels} level_budget={args.level_budget:g}s", flush=True)

    exit_code = 0
    for dx in levels:
        if time.monotonic() - started > args.total_budget:
            record["state"] = "TIMEOUT"
            record["error"] = {"stage": "total_budget",
                               "detail": f"total budget {args.total_budget:g}s exhausted "
                                         f"before dx={dx:g} nm"}
            exit_code = receipt.EXIT_SOLVE_FAILED
            break
        level = {"dx_nm": dx, "state": "RUNNING", "started_at": receipt.utcnow()}
        level_started = time.monotonic()
        try:
            if args.level_budget:
                signal.signal(signal.SIGALRM, _alarm)
                signal.setitimer(signal.ITIMER_REAL, args.level_budget)
            result = fem_pilot.run_level(args.case, point["h_nm"], point["d_nm"],
                                         "T", dx, overwrite=False)
            signal.setitimer(signal.ITIMER_REAL, 0)
        except BaseException as error:  # noqa: BLE001 - a failure must be recorded
            signal.setitimer(signal.ITIMER_REAL, 0)
            level["state"] = "TIMEOUT" if isinstance(error, BudgetExceeded) else "FAILED"
            level["seconds"] = round(time.monotonic() - level_started, 2)
            level["finished_at"] = receipt.utcnow()
            level["error"] = {"type": type(error).__name__, "message": str(error),
                             "traceback": traceback.format_exc()[-4000:]}
            record["levels"].append(level)
            record["state"] = "TIMEOUT" if isinstance(error, BudgetExceeded) else "FAILED"
            record["error"] = {"stage": f"dx={dx:g} nm", **level["error"]}
            exit_code = receipt.EXIT_SOLVE_FAILED
            break

        level["seconds"] = round(time.monotonic() - level_started, 2)
        level["finished_at"] = receipt.utcnow()
        level["state"] = "SOLVED"
        json_path = case_dir / f"dx_{dx:g}nm.json"
        field_path = case_dir / result["field_file"]
        fingerprint = receipt.mesh_fingerprint(field_path)
        level.update(fingerprint)
        level.update({
            "K_m3": result["K_m3"],
            "json_file": json_path.name,
            "json_sha256": receipt.sha256_file(json_path),
            "field_file": field_path.name,
            "field_sha256_solver": result["field_sha256"],
            "field_sha256_rehashed": receipt.sha256_file(field_path),
            "direct_relative_residual": result["direct_relative_residual"],
            "power_balance_percent": result["power_balance_percent"],
            "section_flux_spread_percent": result.get("section_flux_spread_percent"),
            "section_vs_volume_percent": result.get("section_vs_volume_percent"),
            "section_count": result.get("section_count"),
            "mesh_triangles": result["mesh_triangles"],
            "p2_dofs": result.get("p2_dofs"),
        })
        record["levels"].append(level)
        receipt.atomic_write_json(receipt_path, record)
        print(f"  dx={dx:g} nm  K={result['K_m3']:.12e}  "
              f"{level['seconds']:.1f}s  mesh={fingerprint['mesh_sha256'][:12]}", flush=True)

    if exit_code == 0:
        try:
            fem_pilot.summarize(args.case)
            record["state"] = "SOLVED"
        except BaseException as error:  # noqa: BLE001
            record["state"] = "FAILED"
            record["error"] = {"stage": "summarize", "type": type(error).__name__,
                               "message": str(error),
                               "traceback": traceback.format_exc()[-4000:]}
            exit_code = receipt.EXIT_SOLVE_FAILED

    record["finished_at"] = receipt.utcnow()
    record["exit_code"] = exit_code
    record["wall_seconds"] = round(time.monotonic() - started, 2)
    record["peak_rss_kb"] = receipt.peak_rss_kb()
    digest = receipt.atomic_write_json(receipt_path, record)
    print(f"DONE {record['state']} run={run_id} wall={record['wall_seconds']:.1f}s "
          f"peak_rss={record['peak_rss_kb']}kB receipt_sha256={digest[:12]}", flush=True)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
