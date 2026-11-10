"""Guarded future process capture with per-child wait4 resources; no CLI."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time


ROOT = Path(__file__).resolve().parents[1]
PLAN_CSV = ROOT / "protocol/benchmarks18.csv"


class ChildRejected(ValueError):
    pass


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _available_memory():
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    raise ChildRejected("MEMAVAILABLE_UNKNOWN")


def _inventory(path: Path):
    files = {}
    for base, _, names in os.walk(path, followlinks=False):
        for name in names:
            file = Path(base) / name
            if file.is_file() and not file.is_symlink():
                files[str(file.relative_to(path))] = {"sha256": _hash(file),
                                                      "bytes": file.stat().st_size}
    return files


def check_real_release(planned_id: str, release: dict, argv: list[str], inputs: dict):
    """Read the on-disk whitelist before a child or output directory exists."""
    rows = list(csv.DictReader(PLAN_CSV.open(encoding="utf-8-sig", newline="")))
    plans = [r for r in rows if r["planned_id"] == planned_id]
    if len(plans) != 1 or plans[0]["authorized_to_execute"] != "True":
        raise ChildRejected("FROZEN_PLAN_DENIES_EXECUTION")
    if not isinstance(release, dict) or release.get("status") != "APPROVED_FOR_RECTANGLE_SOLVE":
        raise ChildRejected("REVIEWED_RELEASE_REQUIRED")
    if (not isinstance(release.get("release_id"), str) or not release["release_id"]
            or release.get("planned_id") != planned_id
            or release.get("plan_csv_sha256") != _hash(PLAN_CSV)):
        raise ChildRejected("PLAN_RELEASE_BINDING_MISMATCH")
    if release.get("argv") != argv or release.get("inputs_sha256") != inputs:
        raise ChildRejected("COMMAND_OR_INPUT_BINDING_MISMATCH")


def _capture(parent: Path, run_id: str, argv: list[str], inputs: dict[str, str],
             *, record_kind: str, release_id: str | None,
             planned_id: str | None = None, release_sha256: str | None = None) -> Path:
    """Run one child, store independent exit and direct-child wait4 usage."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id):
        raise ChildRejected("INVALID_RUN_ID")
    if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x for x in argv):
        raise ChildRejected("EXACT_ARGV_REQUIRED")
    if not isinstance(inputs, dict) or not inputs:
        raise ChildRejected("INPUTS_REQUIRED")
    bound = {}
    for name, expected in inputs.items():
        path = Path(name).resolve(strict=True)
        if (not path.is_file() or not isinstance(expected, str)
                or not re.fullmatch(r"[0-9a-f]{64}", expected)
                or _hash(path) != expected):
            raise ChildRejected("PRE_RUN_INPUT_HASH_MISMATCH")
        bound[str(path)] = expected
    if len(bound) != len(inputs):
        raise ChildRejected("DUPLICATE_RESOLVED_INPUT")
    parent = Path(parent)
    if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
        raise ChildRejected("INVALID_OUTPUT_PARENT")
    dest = parent / run_id
    if dest.exists() or dest.is_symlink():
        raise ChildRejected("RUN_ID_ALREADY_EXISTS")
    stat = os.statvfs(parent if parent.exists() else parent.parent)
    snapshot = {"MemAvailable_bytes": _available_memory(),
                "disk_available_bytes": stat.f_bavail * stat.f_frsize}
    parent.mkdir(parents=True, exist_ok=True)
    dest.mkdir(exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    (dest / "STARTED.json").write_text(json.dumps({
        "record_kind": record_kind, "run_id": run_id, "argv": argv,
        "release_id": release_id, "release_sha256": release_sha256,
        "planned_id": planned_id, "started_utc": started,
        "inputs_sha256": bound, "resource_before": snapshot,
        "independent_exit_code": None, "NUMERICAL_GATE": "NOT_EVALUATED"
    }, indent=2) + "\n")
    start = time.monotonic()
    code = None
    usage = None
    start_error = None
    with (dest / "stdout.log").open("xb") as out, (dest / "stderr.log").open("xb") as err:
        try:
            proc = subprocess.Popen(argv, cwd=dest, stdout=out, stderr=err,
                                    shell=False, close_fds=True, start_new_session=True)
            while True:
                try:
                    _, status, usage = os.wait4(proc.pid, 0)
                    break
                except InterruptedError:
                    continue
            code = os.waitstatus_to_exitcode(status)
            proc.returncode = code
        except OSError as exc:
            start_error = str(exc)
    (dest / "independent_exit_code.txt").write_text(
        ("START_FAILED" if code is None else str(code)) + "\n")
    after = {p: (_hash(Path(p)) if Path(p).is_file() else None) for p in bound}
    files = {}
    for name in ("STARTED.json", "stdout.log", "stderr.log", "independent_exit_code.txt"):
        path = dest / name
        files[name] = {"sha256": _hash(path), "bytes": path.stat().st_size}
    output_files = _inventory(dest)
    rusage = None if usage is None else {
        "direct_child_peak_RSS_KiB": usage.ru_maxrss,
        "direct_child_user_seconds": usage.ru_utime,
        "direct_child_system_seconds": usage.ru_stime,
        "direct_child_minor_faults": usage.ru_minflt,
        "direct_child_major_faults": usage.ru_majflt,
    }
    record = {"record_kind": record_kind, "run_id": run_id,
              "status": "CHILD_START_FAILED" if code is None else "CHILD_EXITED_UNVERIFIED",
              "release_id": release_id, "release_sha256": release_sha256,
              "planned_id": planned_id, "argv": argv,
              "started_utc": started, "ended_utc": datetime.now(timezone.utc).isoformat(),
              "wall_seconds": time.monotonic() - start,
              "independent_exit_code": code, "start_error": start_error,
              "resource_before": snapshot, "per_direct_child_rusage": rusage,
              "output_dir_bytes_before_manifest": sum(x["bytes"] for x in output_files.values()),
              "all_output_files_before_manifest": output_files,
              "inputs_sha256_before": bound, "inputs_sha256_after": after,
              "inputs_unchanged": bound == after, "files": files,
              "NUMERICAL_GATE": "NOT_EVALUATED", "RESULT_PASS": False,
              "geometry_PASS": None}
    (dest / "capture_manifest.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    return dest


def capture_reviewed_case(parent: Path, run_id: str, planned_id: str,
                          argv: list[str], inputs: dict[str, str], release: dict) -> Path:
    check_real_release(planned_id, release, argv, inputs)
    release_digest = hashlib.sha256(json.dumps(release, sort_keys=True,
                                  separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return _capture(parent, run_id, argv, inputs,
                    record_kind="FUTURE_SOLVER_CHILD_UNVERIFIED",
                    release_id=release["release_id"], planned_id=planned_id,
                    release_sha256=release_digest)


def capture_synthetic_fixture(parent: Path, run_id: str, fixture: Path) -> Path:
    """Only a fixed, short, local test script; cannot select a solver command."""
    import sys
    fixture = Path(fixture).resolve(strict=True)
    if fixture.parent != Path(__file__).resolve().parent or fixture.name != "synthetic_child.py":
        raise ChildRejected("ONLY_FIXED_SYNTHETIC_FIXTURE_ALLOWED")
    return _capture(parent, run_id, [sys.executable, "-B", str(fixture)],
                    {str(fixture): _hash(fixture)},
                    record_kind="SYNTHETIC_CHILD_TEST_NOT_RESULT", release_id=None)
