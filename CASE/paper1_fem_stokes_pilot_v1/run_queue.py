#!/usr/bin/env python3
"""Unattended queue runner for the Paper 1 FEM pilot.

Runs a fixed list of geometries in sequence, one mesh level at a time, then
runs the independent verifier on every finished case.  It is restartable: a
case whose VERIFICATION.json already passed is skipped, and a mesh level whose
JSON already exists is not recomputed.  A single failing case never stops the
queue, because a documented FAIL is a result, not a crash.

The queue only writes inside results/<case>/.  It never edits the manuscripts,
never changes a threshold and never promotes a case to paper reference status.

Usage
    python3 run_queue.py                 # run the default queue, resume
    python3 run_queue.py --dry-run       # print the plan and exit
    python3 run_queue.py --cases h100_d100_T h25_d100_T
    python3 run_queue.py --redo h25_d100_T
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import signal
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import fem_pilot
import verify_results

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
STATUS_JSON = ROOT / "QUEUE_STATUS.json"
STATUS_CSV = ROOT / "QUEUE_STATUS.csv"
LOG_PATH = ROOT / "queue_run.log"
LEVELS = [5.0, 2.5, 1.25]

# Teacher work order: 19 along-groove geometries, 4 cross-groove geometries.
# Already covered by this pilot or by a qualified FVM reference:
#   P: h50/d120, h75/d100, h125/d120      T: h50/d120, h75/d100
# Everything below is the remaining part of that list.  Cross-groove cases run
# first because they are the actual bottleneck of the paper.
DEFAULT_QUEUE = [
    "h100_d100_T",
    "h25_d100_T",
    "h25_d25_P",
    "h25_d50_P",
    "h25_d100_P",
    "h50_d25_P",
    "h50_d50_P",
    "h50_d75_P",
    "h50_d100_P",
    "h75_d25_P",
    "h75_d50_P",
    "h75_d75_P",
    "h75_d120_P",
    "h100_d100_P",
    "h125_d25_P",
    "h125_d50_P",
    "h125_d75_P",
    "h125_d100_P",
]


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(message: str) -> None:
    line = f"[{now()}] {message}"
    print(line, flush=True)
    with LOG_PATH.open("a") as stream:
        stream.write(line + "\n")


class LevelTimeout(RuntimeError):
    pass


def _alarm(signum, frame):
    raise LevelTimeout("mesh level exceeded its time budget")


def json_path(case: str, dx: float) -> Path:
    return RESULTS / case / f"dx_{dx:g}nm.json"


def verification_path(case: str) -> Path:
    return RESULTS / case / "VERIFICATION.json"


def load_verification(case: str):
    path = verification_path(case)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def fine_K(case: str):
    """Finest-level K straight from the saved JSON, not from the summary."""
    available = [dx for dx in LEVELS if json_path(case, dx).exists()]
    if not available:
        return None, None
    dx = min(available)
    try:
        return float(json.loads(json_path(case, dx).read_text())["K_m3"]), dx
    except (json.JSONDecodeError, OSError, KeyError):
        return None, None


def write_status(state: dict) -> None:
    payload = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    temporary = STATUS_JSON.with_suffix(".json.tmp")
    temporary.write_text(payload)
    os.replace(temporary, STATUS_JSON)
    fields = ["case", "direction", "status", "levels_run", "levels_reused",
              "fine_dx_nm", "fine_K_m3", "grid_change_percent", "problems",
              "seconds", "finished_at"]
    temporary_csv = STATUS_CSV.with_suffix(".csv.tmp")
    with temporary_csv.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore",
                                lineterminator="\n")
        writer.writeheader()
        for row in state["cases"]:
            row = dict(row)
            if isinstance(row.get("problems"), list):
                row["problems"] = "; ".join(row["problems"])
            writer.writerow(row)
    os.replace(temporary_csv, STATUS_CSV)


def run_case(case: str, levels, timeout: float, redo: bool, state: dict,
             index: int, total: int) -> dict:
    started = time.time()
    row = {"case": case, "status": "PENDING", "levels_run": [],
           "levels_reused": [], "problems": [], "seconds": None,
           "finished_at": None}

    try:
        h, d, direction = fem_pilot.parse_case(case)
    except ValueError as error:
        row["status"] = "BAD_CASE_NAME"
        row["problems"] = [str(error)]
        row["seconds"] = round(time.time() - started, 1)
        row["finished_at"] = now()
        log(f"[{index}/{total}] {case} BAD_CASE_NAME: {error}")
        return row

    row["direction"] = direction
    log(f"[{index}/{total}] {case} start  h={h:g} d={d:g} {direction}  levels={levels}")

    if redo:
        for dx in levels:
            stale = json_path(case, dx)
            if stale.exists():
                stale.unlink()
                log(f"          {case} dx{dx:g} existing output removed for --redo")
        old_verification = verification_path(case)
        if old_verification.exists():
            old_verification.unlink()

    level_error = None
    for dx in levels:
        path = json_path(case, dx)
        if path.exists() and not redo:
            row["levels_reused"].append(dx)
            log(f"          {case} dx{dx:g} already present, reuse")
            continue
        try:
            if timeout:
                signal.signal(signal.SIGALRM, _alarm)
                signal.setitimer(signal.ITIMER_REAL, timeout)
            result = fem_pilot.run_level(case, h, d, direction, dx, False)
            signal.setitimer(signal.ITIMER_REAL, 0)
            row["levels_run"].append(dx)
            log(f"          {case} dx{dx:g} done  K={result['K_m3']:.10e}  "
                f"tri={result['mesh_triangles']}  "
                f"power={result['power_balance_percent']:.3e}  "
                f"res={result['direct_relative_residual']:.2e}")
        except LevelTimeout:
            signal.setitimer(signal.ITIMER_REAL, 0)
            level_error = f"dx{dx:g} timed out after {timeout:.0f}s"
            log(f"          {case} dx{dx:g} TIMEOUT")
            break
        except Exception as error:  # noqa: BLE001 - a failure must not stop the queue
            signal.setitimer(signal.ITIMER_REAL, 0)
            level_error = f"dx{dx:g} failed: {type(error).__name__}: {error}"
            log(f"          {case} dx{dx:g} FAILED {type(error).__name__}: {error}")
            log(traceback.format_exc().rstrip())
            break

    if level_error:
        row["status"] = "SOLVE_FAILED"
        row["problems"] = [level_error]

    available = [dx for dx in LEVELS if json_path(case, dx).exists()]
    if not level_error and len(available) < len(LEVELS):
        row["status"] = "INCOMPLETE_LEVELS"
        row["problems"] = [f"only {len(available)}/{len(LEVELS)} levels present"]

    if not row["problems"]:
        try:
            fem_pilot.summarize(case)
            verification = verify_results.verify_case(case)
            row["status"] = verification["status"]
            row["problems"] = list(verification["problems"])
            for entry in verification["levels"]:
                if entry["K_change_from_coarser_recomputed_percent"] is not None:
                    row["grid_change_percent"] = round(
                        entry["K_change_from_coarser_recomputed_percent"], 8)
        except Exception as error:  # noqa: BLE001
            row["status"] = "VERIFY_FAILED"
            row["problems"] = [f"{type(error).__name__}: {error}"]
            log(f"          {case} VERIFY FAILED {type(error).__name__}: {error}")
            log(traceback.format_exc().rstrip())

    K, dx = fine_K(case)
    row["fine_dx_nm"] = dx
    row["fine_K_m3"] = K
    row["seconds"] = round(time.time() - started, 1)
    row["finished_at"] = now()
    log(f"[{index}/{total}] {case} {row['status']}  K_fine={K}  "
        f"{row['seconds']:.1f}s  problems={row['problems']}")
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", nargs="+", default=None,
                        help="override the default queue")
    parser.add_argument("--levels", nargs="+", type=float, default=LEVELS)
    parser.add_argument("--timeout", type=float, default=3600.0,
                        help="per mesh-level wall clock limit in seconds, 0 disables")
    parser.add_argument("--redo", nargs="*", default=[],
                        help="case names to recompute even if outputs exist")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="run even if another queue process looks active")
    args = parser.parse_args()

    queue = args.cases or DEFAULT_QUEUE
    levels = sorted(args.levels, reverse=True)
    redo = set(args.redo or [])

    for case in queue:
        fem_pilot.parse_case(case)

    backlog = []
    for case in queue:
        verification = load_verification(case)
        if verification and verification.get("status") == "PILOT_NUMERICAL_CHECKS_PASS" \
                and case not in redo:
            backlog.append(("skip", case))
            continue
        missing = [dx for dx in levels if not json_path(case, dx).exists()]
        backlog.append(("run", case, missing))

    if args.dry_run:
        print(f"queue: {len(queue)} cases, levels {levels}")
        for entry in backlog:
            if entry[0] == "skip":
                print(f"  skip  {entry[1]}  (already passed verification)")
            else:
                print(f"  run   {entry[1]}  missing {entry[2] or 'none, verify only'}")
        return 0

    lock = ROOT / "queue_run.pid"
    if lock.exists() and not args.force:
        try:
            other = int(lock.read_text().strip())
            os.kill(other, 0)
        except (ValueError, ProcessLookupError, OSError):
            other = None
        if other:
            print(f"queue already running as pid {other}; use --force to override")
            return 2
    lock.write_text(str(os.getpid()))

    state = {
        "queue_started": now(),
        "pid": os.getpid(),
        "levels": levels,
        "timeout_seconds": args.timeout,
        "note": "PILOT_NUMERICAL_CHECKS_PASS is an internal check only; it does "
                "not grant paper reference qualification.",
        "cases": [],
        "queue_finished": None,
    }
    log(f"queue start pid={os.getpid()} cases={len(queue)} levels={levels}")

    try:
        for index, case in enumerate(queue, start=1):
            verification = load_verification(case)
            if verification and verification.get("status") == "PILOT_NUMERICAL_CHECKS_PASS" \
                    and case not in redo:
                K, dx = fine_K(case)
                state["cases"].append({
                    "case": case, "status": "ALREADY_PASSED", "levels_run": [],
                    "levels_reused": [d for d in levels if json_path(case, d).exists()],
                    "fine_dx_nm": dx, "fine_K_m3": K, "problems": [],
                    "seconds": 0.0, "finished_at": now(),
                    "direction": fem_pilot.parse_case(case)[2],
                })
                write_status(state)
                log(f"[{index}/{len(queue)}] {case} ALREADY_PASSED, skipped")
                continue
            row = run_case(case, levels, args.timeout, case in redo,
                           state, index, len(queue))
            state["cases"].append(row)
            write_status(state)
    finally:
        state["queue_finished"] = now()
        write_status(state)
        try:
            lock.unlink()
        except FileNotFoundError:
            pass

    passed = sum(1 for r in state["cases"] if r["status"] == "PILOT_NUMERICAL_CHECKS_PASS")
    failed = sum(1 for r in state["cases"]
                 if r["status"] not in ("PILOT_NUMERICAL_CHECKS_PASS", "ALREADY_PASSED"))
    log(f"queue done: {passed} passed, {failed} not passed, total {len(state['cases'])}")
    log(f"status written to {STATUS_JSON} and {STATUS_CSV}")
    print(f"\n{passed} passed / {failed} not passed out of {len(state['cases'])}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
