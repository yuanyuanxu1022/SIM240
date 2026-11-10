"""Dormant single-case worker. Current whitelist denies before any backend import."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import inspect  # Prevent older project inspect.py shadowing stdlib inspect.
import json
from pathlib import Path
import sys
import traceback

import numpy as np

from failure_archive import save_failure
from recorded_solver import DiagnosticGMRES, solve_prepared_mixed_system

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "result_adapter_review_20261026"))
sys.path.insert(0, str(ROOT / "raw_capture_review_20261025"))
from bridge import build_raw_bundle  # noqa: E402
from raw_writer import write_raw_arrays  # noqa: E402


class WorkerRejected(ValueError):
    pass


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_frozen_gate(planned_id, release):
    """Fail before matrix assembly, KSP creation, or result directory writes."""
    plan_csv = ROOT / "protocol/benchmarks18.csv"
    rows = list(csv.DictReader(plan_csv.open(encoding="utf-8-sig", newline="")))
    selected = [r for r in rows if r["planned_id"] == planned_id]
    if len(selected) != 1 or selected[0]["authorized_to_execute"] != "True":
        raise WorkerRejected("FROZEN_PLAN_DENIES_EXECUTION")
    if not isinstance(release, dict) or release.get("status") != "APPROVED_FOR_RECTANGLE_SOLVE":
        raise WorkerRejected("REVIEWED_RELEASE_REQUIRED")
    if release.get("planned_id") != planned_id or release.get("plan_csv_sha256") != _hash(plan_csv):
        raise WorkerRejected("PLAN_RELEASE_BINDING_MISMATCH")


def _load_entry():
    path = ROOT / "solve_entry_review_20261025/entry.py"
    spec = importlib.util.spec_from_file_location("d4_recorded_worker_entry", path)
    module = importlib.util.module_from_spec(spec)
    mesh_path = str(ROOT / "mesh_periodic_pressure_20261025")
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = [p for p in sys.path if p != mesh_path]
    if mesh_path in str(Path(inspect.__file__).resolve()):
        raise WorkerRejected("STDLIB_INSPECT_SHADOWED")
    return module


def run_one(planned_id: str, release: dict, run_id: str, case_dir: Path):
    check_frozen_gate(planned_id, release)
    if release.get("run_id") != run_id or not case_dir.is_dir() or case_dir.is_symlink():
        raise WorkerRejected("RUN_BINDING_OR_CASE_DIR_MISMATCH")
    settings = release.get("solver_settings")
    if not isinstance(settings, dict):
        raise WorkerRejected("SOLVER_SETTINGS_REQUIRED")
    config = DiagnosticGMRES(**settings)
    config.validate()
    limits = release.get("resource_limits")
    if (not isinstance(limits, dict) or type(limits.get("max_iterations_cap")) is not int
            or type(limits.get("restart_cap")) is not int
            or config.max_iterations > limits["max_iterations_cap"]
            or config.restart > limits["restart_cap"]):
        raise WorkerRejected("CONFIG_EXCEEDS_REVIEWED_RESOURCE_LIMITS")
    input_hashes = release.get("source_sha256")
    if not isinstance(input_hashes, dict) or not input_hashes:
        raise WorkerRejected("SOURCE_HASH_BINDING_REQUIRED")
    for relative, expected in input_hashes.items():
        source = ROOT / relative
        if not source.is_file() or _hash(source) != expected:
            raise WorkerRejected("SOURCE_HASH_MISMATCH:" + relative)
    entry = _load_entry()
    system = entry.prepare_bound_mixed_system(planned_id)
    # Candidate release still binds exact assembled A and b before KSP exists.
    release_id = release.get("release_id")
    if not isinstance(release_id, str) or not release_id:
        raise WorkerRejected("RELEASE_ID_REQUIRED")

    def failure_sink(stage, error, vector, diagnostics, binding):
        save_failure(case_dir / "failures", run_id, stage, error, vector,
                     diagnostics, {**binding, "release_id": release_id,
                                   "source_sha256": input_hashes})

    result = solve_prepared_mixed_system(system, config, release, failure_sink)
    try:
        bundle = build_raw_bundle(system["item"], result)
        provenance = {"kind": "FUTURE_UNVERIFIED_SOLVER_RAW", "planned_id": planned_id,
                      "source_sha256": input_hashes,
                      "mesh_sha256": system["item"]["stats"]["actual_mesh_sha256"],
                      "matrix_csr_sha256": system["matrix_csr_sha256"],
                      "rhs_sha256_before_projection": system["rhs_sha256_before_projection"],
                      "release_id": release_id, "run_id": run_id}
        raw_dir = write_raw_arrays(case_dir / "raw", run_id, bundle, provenance)
        (case_dir / "solver_diagnostics.json").write_text(
            json.dumps(result["diagnostics"], indent=2, allow_nan=False) + "\n")
        (case_dir / "worker_stage.json").write_text(json.dumps({
            "status": "SOLVER_EXITED_UNVERIFIED", "raw_manifest": str(raw_dir / "raw_manifest.json"),
            "NUMERICAL_GATE": "NOT_EVALUATED", "RESULT_PASS": False,
            "geometry_PASS": None}, indent=2) + "\n")
    except Exception as exc:
        # Preserve the pre-backsub algebraic vector even if output mapping fails.
        failure_sink("POST_SOLVE_RECORD", exc,
                     np.asarray(result["algebraic_solution_before_backsubstitution"].array).copy(),
                     result["diagnostics"],
                     {"planned_id": planned_id,
                      "matrix_csr_sha256": system["matrix_csr_sha256"],
                      "rhs_sha256_before_projection": system["rhs_sha256_before_projection"]})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description="Reviewed future worker; current plans deny")
    parser.add_argument("--planned-id", required=True)
    parser.add_argument("--release-json", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--case-dir", type=Path)
    args = parser.parse_args(argv)
    release = json.loads(args.release_json.read_text()) if args.release_json else None
    try:
        check_frozen_gate(args.planned_id, release)
        if args.release_json is None or args.run_id is None or args.case_dir is None:
            raise WorkerRejected("EXPLICIT_RELEASE_RUN_AND_DIR_REQUIRED")
        run_one(args.planned_id, release, args.run_id, args.case_dir)
    except Exception:
        traceback.print_exc()
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
