#!/usr/bin/env python3
"""Sequential queue over the frozen, authorized point set.

Each case is solved by a separate ``run_one.py`` process so that the recorded
exit status is a real process exit status, and then verified by a separate
``verify_one.py`` process. A failing case is recorded and the queue continues;
nothing is retried, refined or re-thresholded.

A stop file is honoured between cases:
    touch STOP
makes the queue finish the current case and stop before the next one.

Usage
    python3 run_queue.py --plan
    python3 run_queue.py --execute
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time

import receipt

QUEUE_STATUS = receipt.PACKAGE / "QUEUE_STATUS.json"
QUEUE_CSV = receipt.PACKAGE / "QUEUE_STATUS.csv"
LOCK = receipt.PACKAGE / "queue.pid"
STOP = receipt.PACKAGE / "STOP"
LOG = receipt.PACKAGE / "queue.log"
FIELDS = ["case", "solve_exit", "verify_exit", "state", "K_fine_m3",
          "wall_seconds", "reference_status", "stop_reason", "finished_at"]


def log(message: str) -> None:
    line = f"[{receipt.utcnow()}] {message}"
    print(line, flush=True)
    with LOG.open("a") as stream:
        stream.write(line + "\n")


def write_status(payload: dict) -> None:
    receipt.atomic_write_json(QUEUE_STATUS, payload)
    temporary = QUEUE_CSV.with_name(QUEUE_CSV.name + ".tmp")
    with temporary.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction="ignore",
                                lineterminator="\n")
        writer.writeheader()
        for row in payload["cases"]:
            writer.writerow(row)
    os.replace(temporary, QUEUE_CSV)


def fine_K(case: str):
    directory = receipt.RESULTS / case
    values = []
    for path in sorted(directory.glob("dx_*nm.json")):
        payload = json.loads(path.read_text())
        values.append((payload["dx_nm"], payload["K_m3"]))
    if not values:
        return None
    return min(values)[1]


def reference_status_of(case: str) -> str:
    for directory in sorted(receipt.RUNS.glob(f"{case}_*")):
        path = directory / "VERIFY_RECEIPT.json"
        if path.exists():
            return json.loads(path.read_text()).get("reference_status", "UNKNOWN")
    return "NOT_RUN"


def stop_reason_of(case: str) -> str:
    for directory in sorted(receipt.RUNS.glob(f"{case}_*")):
        path = directory / "VERIFY_RECEIPT.json"
        if path.exists():
            return json.loads(path.read_text()).get("actual_stop_reason") or ""
    return ""


def run(cmd: list) -> int:
    process = subprocess.run(cmd, cwd=str(receipt.PACKAGE))
    return process.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--cases", nargs="*", default=None)
    parser.add_argument("--level-budget", type=float, default=1800.0)
    parser.add_argument("--total-budget", type=float, default=7200.0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    points = receipt.load_points()["points"]
    eligible = [p["case"] for p in points if p.get("status") == "ELIGIBLE"]
    blocked = [p["case"] for p in points if p.get("status") != "ELIGIBLE"]
    selected = args.cases or eligible
    unknown = [c for c in selected if c not in eligible]
    if unknown:
        print(f"not eligible: {unknown}")
        return receipt.EXIT_UNAUTHORIZED

    authorization = receipt.load_authorization()
    granted = authorization.get("granted_cases", []) if authorization else []
    todo = [c for c in selected if c in granted]

    if args.plan:
        print(json.dumps({
            "release": (receipt.release_digest()
                        if receipt.MANIFEST_PATH.exists() else "NOT_FROZEN"),
            "eligible": eligible,
            "blocked_by_scope": blocked,
            "granted": granted,
            "would_run": todo,
            "would_skip_not_granted": [c for c in selected if c not in granted],
            "level_budget_seconds": args.level_budget,
            "total_budget_seconds": args.total_budget,
            "cases_requested": len(todo),
            "wall_clock_estimate_note": "no estimate is a commitment; the measured "
                                        "figure must come from the receipts",
        }, indent=2, ensure_ascii=False))
        return 0
    if not args.execute:
        parser.error("choose --plan or --execute")

    try:
        receipt.verify_release()
    except receipt.ReleaseDrift as error:
        print(f"REFUSED release drift: {error}")
        return receipt.EXIT_RELEASE_DRIFT

    if not todo:
        print("nothing authorized to run; record an authorization first")
        return receipt.EXIT_UNAUTHORIZED

    if LOCK.exists() and not args.force:
        try:
            other = int(LOCK.read_text().strip())
            os.kill(other, 0)
        except (ValueError, ProcessLookupError, OSError):
            other = None
        if other:
            print(f"queue already running as pid {other}; use --force to override")
            return 2
    LOCK.write_text(str(os.getpid()))

    payload = {"queue_started": receipt.utcnow(), "pid": os.getpid(),
               "release_sha256": receipt.release_digest(),
               "granted": granted, "blocked_by_scope": blocked,
               "note": "no retry, no refinement, no threshold change; the queue "
                       "finishes the authorized list and stops",
               "cases": []}
    write_status(payload)
    log(f"queue start pid={os.getpid()} cases={len(todo)}")
    started = time.monotonic()

    try:
        for index, case in enumerate(todo, start=1):
            if STOP.exists():
                log(f"STOP file present before {case}; queue ends here")
                payload["stopped_early"] = True
                break
            row = {"case": case, "state": "RUNNING"}
            log(f"[{index}/{len(todo)}] {case} solve")
            row["solve_exit"] = run([sys.executable, "run_one.py", "--case", case,
                                     "--execute",
                                     "--level-budget", f"{args.level_budget:g}",
                                     "--total-budget", f"{args.total_budget:g}"])
            log(f"[{index}/{len(todo)}] {case} verify")
            row["verify_exit"] = run([sys.executable, "verify_one.py", "--case", case])
            row["state"] = ("OK" if row["solve_exit"] == 0 and row["verify_exit"] == 0
                            else "ATTENTION")
            row["K_fine_m3"] = fine_K(case)
            row["reference_status"] = reference_status_of(case)
            row["stop_reason"] = stop_reason_of(case)
            row["finished_at"] = receipt.utcnow()
            payload["cases"].append(row)
            write_status(payload)
            log(f"[{index}/{len(todo)}] {case} {row['state']} "
                f"solve={row['solve_exit']} verify={row['verify_exit']} "
                f"{row['reference_status']}")
    finally:
        payload["queue_finished"] = receipt.utcnow()
        payload["wall_seconds"] = round(time.monotonic() - started, 1)
        write_status(payload)
        LOCK.unlink(missing_ok=True)
        log(f"queue done in {payload['wall_seconds']:.0f}s")

    return 0


if __name__ == "__main__":
    sys.exit(main())
