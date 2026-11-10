"""Versioned pilot contract, independent of the immutable preparation flags."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VERSION = "D4_PILOT_RECORD_V3_20261026_PREPARATION"
FIRST = "B0MIN_MMS_mixed_N8"
SETTINGS = dict(ksp_rtol=1e-10, true_residual_target=1e-10,
                max_iterations=2000, restart=50)
LIMITS = dict(wall_seconds=600, grace_seconds=5, memory_bytes=4*1024**3,
              output_bytes=512*1024**2, minimum_available_memory_bytes=6*1024**3,
              minimum_record_disk_bytes=2*1024**3)
ENV_KEYS = ("PATH", "LD_LIBRARY_PATH", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
            "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "PYTHONDONTWRITEBYTECODE",
            "XDG_CACHE_HOME", "XDG_CONFIG_HOME", "TMPDIR", "HOME")


class Rejected(ValueError):
    pass


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def read_json(path):
    def pairs(values):
        result = {}
        for k, v in values:
            if k in result:
                raise Rejected("DUPLICATE_JSON_KEY:"+k)
            result[k] = v
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(Rejected("NONFINITE_JSON:"+x)))


def write_json(path, value):
    with Path(path).open("x") as f:
        json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
        f.flush();os.fsync(f.fileno())
    fd=os.open(Path(path).parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def load_old_plan():
    # Import only the stdlib-only contract and physics. Its False flags stay true
    # historical facts. No patching or replacing of its globals is performed.
    src = str(ROOT / "src")
    sys.path.insert(0, src)
    try:
        spec = importlib.util.spec_from_file_location("d4_immutable_contract", ROOT / "src/contract.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.select(planned_id=FIRST)[0]
    finally:
        sys.path.remove(src)


def canonical_paths(c):
    for key in ("work_dir", "record_dir", "cgroup_parent"):
        p = Path(c[key])
        if not p.is_absolute() or str(p.resolve()) != str(p):
            raise Rejected("CANONICAL_ABSOLUTE_PATH_REQUIRED:"+key)
    if Path(c["work_dir"]) == Path(c["record_dir"]) or (
            Path(c["work_dir"]).is_relative_to(Path(c["record_dir"])) or
            Path(c["record_dir"]).is_relative_to(Path(c["work_dir"]))):
        raise Rejected("SEPARATE_WORK_AND_RECORD_VOLUMES_REQUIRED")
    if Path(c["work_dir"]).name != c["run_id"] or Path(c["record_dir"]).name != c["run_id"]:
        raise Rejected("RUN_OUTPUT_BINDING_MISMATCH")


def expected_argv(c):
    return [str(ROOT / ".backend/bin/python"), "-B", str(HERE / "worker.py"),
            "--record-dir", c["record_dir"]]


def expected_environment(c):
    work = Path(c["work_dir"])
    return {"PATH": str(ROOT / ".backend/bin")+":/usr/bin:/bin",
            "LD_LIBRARY_PATH": str(ROOT / ".backend/lib"),
            "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1", "PYTHONDONTWRITEBYTECODE": "1",
            "XDG_CACHE_HOME": str(work / "cache"), "TMPDIR": str(work / "tmp"),
            "XDG_CONFIG_HOME": str(work / "config"),
            "HOME": os.environ.get("HOME", "")}


def validate(c, *, execution=False, check_files=True):
    required = {"version", "planned_id", "run_id", "work_dir", "record_dir", "cgroup_parent",
                "status", "authorized_to_execute", "approval", "source_lock_sha256",
                "physical_plan", "solver_settings", "resource_limits", "argv", "environment"}
    if not isinstance(c, dict) or set(c) != required:
        raise Rejected("CONTRACT_FIELDS_MISMATCH")
    if c["version"] != VERSION or c["planned_id"] != FIRST:
        raise Rejected("PILOT_VERSION_OR_CASE_REJECTED")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", c["run_id"]):
        raise Rejected("INVALID_RUN_ID")
    canonical_paths(c)
    if digest(c["solver_settings"]) != digest(SETTINGS) or digest(c["resource_limits"]) != digest(LIMITS):
        raise Rejected("SETTINGS_OR_LIMITS_CHANGED")
    if c["argv"] != expected_argv(c) or c["environment"] != expected_environment(c):
        raise Rejected("COMMAND_OR_ENVIRONMENT_MISMATCH")
    if digest(c["physical_plan"]) != digest(load_old_plan()):
        raise Rejected("PHYSICAL_PLAN_CHANGED")
    if check_files:
        lock_file = HERE / "source_lock.json"
        if c["source_lock_sha256"] != sha(lock_file):
            raise Rejected("SOURCE_LOCK_MISMATCH")
        verify_lock(read_json(lock_file))
    if execution:
        a = c["approval"]
        if (c["status"] != "APPROVED_DIAGNOSTIC_ONLY" or c["authorized_to_execute"] is not True
                or not isinstance(a, dict) or set(a) != {"authorization_text", "protocol_sha256"}
                or not isinstance(a["authorization_text"], str) or not a["authorization_text"].strip()
                or a["protocol_sha256"] != sha(HERE / "DIAGNOSTIC_CONTRACT.md")):
            raise Rejected("DIAGNOSTIC_RUN_NOT_AUTHORIZED")
    else:
        if c["status"] != "DRAFT_NOT_AUTHORIZED" or c["authorized_to_execute"] is not False or c["approval"] is not None:
            raise Rejected("PREPARATION_EXPECTS_DRAFT")
    return c


def verify_lock(lock):
    if set(lock) != {"version", "files", "required_python"} or lock["version"] != VERSION:
        raise Rejected("INVALID_SOURCE_LOCK")
    # The manifest is itself hash-bound by the contract, and the current code
    # additionally requires all package modules and the immutable physical seam.
    must = {str(p.resolve()) for p in HERE.glob("*.py")}
    must |= {str((ROOT / p).resolve()) for p in (
        "src/contract.py", "src/physics.py", "src/symbolic_forms.py", "protocol/benchmarks18.csv",
        "protocol/review_input_hashes.json", "mesh_periodic_pressure_20261025/interface.py",
        "solve_entry_review_20261025/entry.py", "result_adapter_review_20261026/bridge.py",
        "raw_capture_review_20261025/raw_writer.py", "environment/backend.lock.json",
        "environment/package_metadata.json", "environment/conda-linux-64.explicit.txt")}
    if not must <= set(lock["files"]) or lock["required_python"] != str(ROOT / ".backend/bin/python"):
        raise Rejected("MANDATORY_DEPENDENCY_MISSING")
    for name, expected in lock["files"].items():
        p = Path(name)
        if not p.is_absolute() or not p.is_file() or sha(p) != expected:
            raise Rejected("SOURCE_CHANGED:"+name)
    return True


def expected_system():
    path=ROOT/"solve_entry_review_20261025/evidence/preflight_all9.json"
    old=read_json(path)
    records=[r['preflight'] for r in old['records'] if r['planned_id']==FIRST and r['exit_code']==0]
    if len(records)!=1: raise Rejected('PRIOR_ASSEMBLY_RECORD_MISSING')
    return records[0]


def template(work_parent, record_parent, cgroup_parent):
    c = dict(version=VERSION, planned_id=FIRST, run_id="PILOT_UNRELEASED_N8_v3",
             work_dir=str(Path(work_parent).resolve()/"PILOT_UNRELEASED_N8_v3"),
             record_dir=str(Path(record_parent).resolve()/"PILOT_UNRELEASED_N8_v3"),
             cgroup_parent=str(Path(cgroup_parent).resolve()), status="DRAFT_NOT_AUTHORIZED",
             authorized_to_execute=False, approval=None, source_lock_sha256=sha(HERE/"source_lock.json"),
             physical_plan=load_old_plan(), solver_settings=SETTINGS.copy(), resource_limits=LIMITS.copy())
    c["argv"], c["environment"] = expected_argv(c), expected_environment(c)
    return c
