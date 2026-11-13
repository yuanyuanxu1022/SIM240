#!/usr/bin/env python3
"""Run-receipt primitives for the Paper 1 FEM reference package v2.

This module is deliberately separate from the solver. The solver
(``fem_pilot.py``) is a byte-identical copy of the v1 pilot and is not edited
here; everything that makes a run traceable lives in this layer.

Design rules, taken from the FVM v2 review lessons:

1. A receipt can only be written by the process that actually did the work.
   It is opened as ``STARTED`` before the first mesh level is solved and
   updated after every level, so a crash leaves a truthful partial record.
2. The release manifest is checked *before* any output directory is created.
   If any packaged file or dependency version has drifted, the run is refused
   with exit code 3 and no files are produced.
3. The verifier re-hashes the receipt bytes it read. If the receipt changes
   after verification, the assessor flags it. Receipts are never backfilled.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
MANIFEST_PATH = PACKAGE / "release_manifest.json"
POINTS_PATH = PACKAGE / "points.json"
RULE_PATH = PACKAGE / "acceptance_rule.json"
AUTHORIZATION_PATH = PACKAGE / "authorization.json"
RESULTS = PACKAGE / "results"
RUNS = PACKAGE / "runs"
PROTOCOL_PATH = PACKAGE / "PROTOCOL.md"

SCHEMA_RELEASE = "sim240_fem_release/1"
SCHEMA_SOLVE = "sim240_fem_solve_receipt/1"
SCHEMA_VERIFY = "sim240_fem_verify_receipt/1"

EXIT_RELEASE_DRIFT = 3
EXIT_BAD_INPUT = 4
EXIT_UNAUTHORIZED = 5
EXIT_REFUSED_OVERWRITE = 6
EXIT_SOLVE_FAILED = 7
EXIT_VERIFY_FAILED = 8

SCHEMA_LEDGER = "sim240_fem_ledger/1"

CLASSIFICATIONS = ("NOT_RUN", "SOLVE_INCOMPLETE", "SOLVED_NOT_VERIFIED",
                   "NOT_RECONSTRUCTIBLE", "LOCAL_CHECKS_FAIL",
                   "PROVENANCE_INCOMPLETE", "REFERENCE_CANDIDATE")
CANDIDATE = "REFERENCE_CANDIDATE"

EXCLUDED_DIRS = {"results", "runs", "__pycache__", ".git", "tmp"}
EXCLUDED_FILES = {"release_manifest.json", "authorization.json", "FREEZE_LOG.md",
                  "ASSESSMENT.json", "QUEUE_STATUS.json"}
INCLUDED_SUFFIXES = {".py", ".json", ".md"}


class ReleaseDrift(RuntimeError):
    """Raised when the packaged release no longer matches its manifest."""


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(payload) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def digest_of(payload) -> str:
    return sha256_bytes(canonical(payload))


def atomic_write_json(path: Path, payload) -> str:
    """Write JSON atomically and return the sha256 of the bytes written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    try:
        directory = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError:
        pass
    return sha256_bytes(body)


def environment_snapshot() -> dict:
    import numpy
    import scipy
    import skfem

    return {
        "python": sys.version.split()[0],
        "interpreter": sys.executable,
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "scikit_fem": getattr(skfem, "__version__", "unknown"),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "hostname": platform.node(),
    }


GATED_ENV_KEYS = ("python", "numpy", "scipy", "scikit_fem")


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        raise ReleaseDrift(
            f"no release manifest at {MANIFEST_PATH}; run freeze_release.py first")
    return json.loads(MANIFEST_PATH.read_text())


def collect_files() -> list:
    """Every file that belongs to the frozen package, in a stable order."""
    files = []
    for path in sorted(PACKAGE.rglob("*")):
        if not path.is_file():
            continue
        relatives = path.relative_to(PACKAGE).parts
        if any(part in EXCLUDED_DIRS for part in relatives[:-1]):
            continue
        if path.name in EXCLUDED_FILES or path.suffix not in INCLUDED_SUFFIXES:
            continue
        files.append(path)
    return files


def verify_release() -> dict:
    """Recompute every packaged hash and the gated dependency versions.

    Returns the manifest. Raises ReleaseDrift with a full list of differences.
    Must be called before any directory is created or any physics is solved.
    """
    manifest = load_manifest()
    problems = []
    listed = set()

    for entry in manifest.get("files", []):
        listed.add(entry["path"])
        path = PACKAGE / entry["path"]
        if not path.exists():
            problems.append(f"missing file: {entry['path']}")
            continue
        actual = sha256_file(path)
        if actual != entry["sha256"]:
            problems.append(
                f"content drift: {entry['path']} {entry['sha256'][:12]} -> {actual[:12]}")
        size = path.stat().st_size
        if size != entry.get("bytes"):
            problems.append(f"size drift: {entry['path']} {entry.get('bytes')} -> {size}")

    present = {str(path.relative_to(PACKAGE)) for path in collect_files()}
    for extra in sorted(present - listed):
        problems.append(f"file added after freeze: {extra}")
    for absent in sorted(listed - present):
        problems.append(f"packaged file no longer collected: {absent}")

    current = environment_snapshot()
    recorded = manifest.get("environment", {})
    for key in GATED_ENV_KEYS:
        if recorded.get(key) != current.get(key):
            problems.append(
                f"dependency drift: {key} {recorded.get(key)} -> {current.get(key)}")

    body = {k: v for k, v in manifest.items() if k != "release_sha256"}
    recomputed = digest_of(body)
    if recomputed != manifest.get("release_sha256"):
        problems.append(
            f"manifest self-digest mismatch: {manifest.get('release_sha256', '')[:12]}"
            f" -> {recomputed[:12]}")

    if problems:
        raise ReleaseDrift("; ".join(problems))
    return manifest


def release_digest() -> str:
    return load_manifest()["release_sha256"]


def load_points() -> dict:
    return json.loads(POINTS_PATH.read_text())


def point_for_case(case: str) -> dict:
    for point in load_points()["points"]:
        if point["case"] == case:
            return point
    raise KeyError(f"{case} is not in the frozen point set")


def load_authorization():
    if not AUTHORIZATION_PATH.exists():
        return None
    return json.loads(AUTHORIZATION_PATH.read_text())


def check_authorization(case: str) -> dict:
    """Refuse unless this exact case is authorized against this exact release."""
    point = point_for_case(case)
    if point.get("status") != "ELIGIBLE":
        raise PermissionError(
            f"{case} is {point.get('status')}: {point.get('scope_note') or 'not eligible'}")
    authorization = load_authorization()
    if not authorization:
        raise PermissionError(
            "no authorization.json; the author must record an authorization first")
    if case not in authorization.get("granted_cases", []):
        raise PermissionError(f"{case} is not in the granted case list")
    current = release_digest()
    if authorization.get("release_sha256") != current:
        raise PermissionError(
            "authorization was recorded against a different release; "
            "re-freeze and re-authorize")
    return {"point": point, "authorization": authorization}


def new_run_id(case: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{case}_{stamp}_{uuid.uuid4().hex[:8]}"


def run_dir(run_id: str) -> Path:
    return RUNS / run_id


def case_run_dirs(case: str) -> list:
    """Every run directory for this case, oldest first. Used to forbid silent retries."""
    return sorted(p for p in RUNS.glob(f"{case}_*") if (p / "SOLVE_RECEIPT.json").exists())


def level_json_matches(case: str, level: dict) -> bool:
    """The mesh JSON recorded by the solver must still hash to the recorded value."""
    path = RESULTS / case / level.get("json_file", "")
    return path.is_file() and sha256_file(path) == level.get("json_sha256")


def peak_rss_kb() -> int:
    try:
        import resource

        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    except Exception:  # noqa: BLE001 - diagnostic only
        return -1


def mesh_fingerprint(field_path: Path) -> dict:
    """Hash the mesh arrays exactly as the solver saved them."""
    import numpy as np

    with np.load(field_path) as data:
        points = np.ascontiguousarray(data["p"], dtype=np.float64)
        triangles = np.ascontiguousarray(data["t"], dtype=np.int64)
    return {
        "mesh_sha256": sha256_bytes(points.tobytes() + triangles.tobytes()),
        "mesh_vertices": int(points.shape[1]),
        "mesh_triangles": int(triangles.shape[1]),
    }
