"""Independent child-process capture primitive; no executable CLI or solver call."""
from __future__ import annotations

import hashlib
import json
import os
import re
import resource
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


class CaptureRejected(ValueError):
    pass


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def capture_child(parent: Path, record_id: str, argv: list[str], inputs: dict[str, str],
                  *, kind: str, approved_release: dict | None = None) -> Path:
    """Capture a child exit independent of its self-report. No retry or cleanup.

    Current real-case plans are denied. A future approved release and adapter
    must be reviewed separately before using this primitive for a solver.
    """
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", record_id):
        raise CaptureRejected("INVALID_RECORD_ID")
    if not argv or any(not isinstance(a, str) or not a for a in argv):
        raise CaptureRejected("INVALID_ARGV")
    if kind != "SYNTHETIC_CAPTURE_TEST_NOT_RESULT":
        if kind != "FUTURE_UNVERIFIED_SOLVER_PROCESS" or not isinstance(approved_release, dict):
            raise CaptureRejected("REVIEWED_RELEASE_REQUIRED")
        if approved_release.get("status") != "APPROVED_FOR_RECTANGLE_SOLVE":
            raise CaptureRejected("REVIEWED_RELEASE_REQUIRED")
        # This review package deliberately has no real-run adapter or CLI.
        raise CaptureRejected("REAL_PROCESS_ADAPTER_NOT_IMPLEMENTED")
    if not isinstance(inputs, dict) or not inputs:
        raise CaptureRejected("INPUT_HASHES_REQUIRED")
    source_paths = {str(Path(p).resolve()): expected for p, expected in inputs.items()}
    if len(source_paths) != len(inputs) or any(
        not re.fullmatch(r"[0-9a-f]{64}", expected) or not Path(p).is_file()
        or _hash(Path(p)) != expected for p, expected in source_paths.items()
    ):
        raise CaptureRejected("INPUT_HASH_MISMATCH_BEFORE_CHILD")
    parent = Path(parent)
    if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
        raise CaptureRejected("INVALID_OUTPUT_PARENT")
    dest = parent / record_id
    if dest.exists() or dest.is_symlink():
        raise CaptureRejected("OUTPUT_ALREADY_EXISTS")
    parent.mkdir(parents=True, exist_ok=True)
    dest.mkdir(exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()
    rss_before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    exit_code = None
    error = None
    with (dest / "stdout.log").open("xb") as out, (dest / "stderr.log").open("xb") as err:
        try:
            proc = subprocess.Popen(argv, stdout=out, stderr=err, shell=False,
                                    close_fds=True, start_new_session=True)
            exit_code = proc.wait()
        except OSError as exc:
            error = str(exc)
    (dest / "independent_exit_code.txt").write_text(
        (str(exit_code) if exit_code is not None else "START_FAILED") + "\n", encoding="ascii")
    inputs_after = {p: (_hash(Path(p)) if Path(p).is_file() else None)
                    for p in source_paths}
    log_files = {name: {"sha256": _hash(dest / name), "bytes": (dest / name).stat().st_size}
                 for name in ("stdout.log", "stderr.log", "independent_exit_code.txt")}
    manifest = {"kind": kind, "status": "CHILD_EXITED_UNVERIFIED" if exit_code is not None
                else "CHILD_START_FAILED", "record_id": record_id, "argv": argv,
                "started_utc": started, "ended_utc": datetime.now(timezone.utc).isoformat(),
                "wall_seconds": time.monotonic() - t0,
                "child_peak_RSS_KiB_cumulative": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                "prior_child_peak_RSS_KiB_cumulative": rss_before,
                "independent_exit_code": exit_code, "start_error": error,
                "inputs_before_sha256": source_paths, "inputs_after_sha256": inputs_after,
                "inputs_unchanged": source_paths == inputs_after, "files": log_files,
                "NUMERICAL_GATE": "NOT_EVALUATED", "RESULT_PASS": False,
                "geometry_PASS": None}
    (dest / "capture_manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return dest
