#!/usr/bin/env python3
"""User-started long workflow: fresh full scaling, then fresh Nx=2, then stop.

The original runner/postprocessor/build and historical batches are untouched.
The initialized-state output check is not a numerical validation substitute.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from check_field_slice import check_field_slice
from postprocess_period import check_gates, parse_kv

CASE = Path(__file__).resolve().parents[1]
BUILD = CASE / "build_fields_v1"
SCRIPTS = CASE / "scripts"
TAGS = {"a5e4": 5e4, "a1e5": 1e5, "a2e5": 2e5}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def active_solver_pids():
    prefixes = (str(CASE / "build" / "g4_nx"), str(BUILD / "g4_nx"))
    pids = []
    for proc in Path("/proc").glob("[0-9]*"):
        try:
            executable = (proc / "cmdline").read_bytes().split(b"\0", 1)[0].decode()
        except (OSError, UnicodeError):
            continue
        if executable.startswith(prefixes):
            pids.append(int(proc.name))
    return sorted(pids)


def readiness():
    report = json.loads((BUILD / "OUTPUT_CHAIN_CHECK.json").read_text())
    if report.get("output_chain_PASS") is not True:
        raise SystemExit("initialized output check has not passed")
    expected = {(d, m, n) for d in ("P", "T")
                for m, n in [("serial", 1), ("mpi", 1), ("mpi", 4), ("mpi", 8), ("mpi", 16)]}
    actual = {(c["direction"], c["mode"], c["ranks"]) for c in report["checks"]}
    if actual != expected:
        raise SystemExit("output check coverage must include P/T and 1/4/8/16 MPI ranks")
    for path, digest in report["artifact_sha256"].items():
        if sha(Path(path)) != digest:
            raise SystemExit(f"artifact changed since short output check: {path}")
    for check in report["checks"]:
        path = Path(check["path"])
        if sha(path) != check["field_sha256"]:
            raise SystemExit(f"probe field changed: {path}")
    print("static readiness PASS; short output checks remain SHA-bound", flush=True)


def new_batch(prefix):
    stamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    batch = CASE / "results" / f"{prefix}_{stamp}"
    batch.mkdir(exist_ok=False)
    hashes = {str(path): sha(path) for path in [
        CASE / "PERIOD_CONVERGENCE_PROTOCOL.md", CASE / "src/Makefile.fields",
        SCRIPTS / "generate_period_source.py", SCRIPTS / "generate_period_source_fields.py",
        SCRIPTS / "check_field_slice.py", SCRIPTS / "postprocess_period.py",
        SCRIPTS / "postprocess_period_fields.py", SCRIPTS / "check_scaling.py",
        SCRIPTS / "run_field_repair_nx2.py", BUILD / "OUTPUT_CHAIN_CHECK.json",
        Path("/home/dell/openlb/build/lib/libolbcore.a")]}
    git_commit = subprocess.check_output(["git", "-C", str(CASE), "rev-parse", "HEAD"], text=True).strip()
    olb_commit = subprocess.check_output(["git", "-C", "/home/dell/openlb", "rev-parse", "HEAD"], text=True).strip()
    manifest = {"batch_id": batch.name, "output_revision": "fields_v1",
                "repository_commit": git_commit, "OpenLB_commit": olb_commit,
                "OpenLB_compile_version": "5953d8a-dirty",
                "sha256": hashes, "original_batches_preserved": True,
                "git_status": subprocess.check_output(
                    ["git", "-C", str(CASE), "status", "--short"], text=True),
                "parameters": {"nx_periods": 2, "ny_periods": 1, "dx_m": 2.5e-9,
                    "dt_s": 1.0416666666666667e-12, "tau": 1.0, "h_m": 75e-9,
                    "period_m": 240e-9, "groove_depth_m": 100e-9, "groove_width_m": 120e-9,
                    "rho_kg_m3": 1000, "nu_m2_s": 1e-6, "mu_Pa_s": 1e-3,
                    "maximum_steps": 240000, "lattice": "D3Q19_FORCE",
                    "collision": "ForcedBGK", "periodicity": "x_y",
                    "wall": "Bouzidi_zero_velocity_exact_EX240"}}
    (batch / "SOURCE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"batch={batch}", flush=True)
    return batch


def run_phase(dest, mode, nrank, tag, direction, phase):
    dest.mkdir(parents=True, exist_ok=False)
    binary = BUILD / f"g4_nx2_{mode}_{tag}"
    source = BUILD / "generated" / (f"g4_nx2_{mode}.cpp" if tag == "a1e5"
                                    else f"g4_nx2_{mode}_{tag}.cpp")
    manifest = {
        "run_id": f"{next(p.name for p in dest.parents if (p / 'SOURCE_MANIFEST.json').is_file())}_{dest.parent.name}_{phase}",
        "output_revision": "fields_v1", "nx_periods": 2, "ranks": nrank,
        "mode": mode, "phase": phase, "direction": direction,
        "acceleration_m_s2": TAGS[tag], "binary_sha256": sha(binary),
        "generated_source_sha256": sha(source),
        "protocol_sha256": sha(CASE / "PERIOD_CONVERGENCE_PROTOCOL.md")}
    (dest / "run_manifest.txt").write_text(
        "".join(f"{key}={value}\n" for key, value in manifest.items()))
    command = ["mpirun", "-np", str(nrank), "-x", f"G4_EXPECTED_RANKS={nrank}",
               str(binary), phase, direction, str(dest)]
    print(f"launch {dest.parent.name}/{phase} ranks={nrank}", flush=True)
    with (dest / "run.log").open("w") as log:
        run = subprocess.run(command, cwd=dest, stdout=log, stderr=subprocess.STDOUT)
    (dest / "exit_code.txt").write_text(f"{run.returncode}\n")
    if run.returncode:
        raise RuntimeError(f"exit={run.returncode}: {dest / 'run.log'}")
    if phase == "steady":
        result = parse_kv(dest / "result.txt")
        problems = check_gates(result, 2, run.returncode)
        if problems:
            raise RuntimeError(f"numeric gates failed: {dest}: {problems}")
        check_field_slice(dest / "field_slice.csv", 2)
    print(f"finished {dest.parent.name}/{phase}", flush=True)


def run_check(script, batch):
    with (batch / "postprocess.log").open("w") as log:
        run = subprocess.run([sys.executable, str(SCRIPTS / script), str(batch)],
                             stdout=log, stderr=subprocess.STDOUT)
    (batch / "postprocess_exit_code.txt").write_text(f"{run.returncode}\n")
    if run.returncode:
        raise RuntimeError(f"postprocess exit={run.returncode}: {batch / 'postprocess.log'}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    readiness()
    active = active_solver_pids()
    if args.check_only:
        print(f"active G4 solver ranks={len(active)}; long launch "
              f"{'blocked until they finish' if active else 'ready'}", flush=True)
        return
    if active:
        raise SystemExit("Existing G4 solvers are running; start this workflow after they finish.")
    # New full scaling is required for repaired binaries, not just the short probe.
    scaling = new_batch("g4_scaling_nx2_fields_v1")
    (CASE / "results/latest_fields_scaling.txt").write_text(scaling.name + "\n")
    for label, mode, nrank in [("serial_1rank", "serial", 1), ("mpi_1rank", "mpi", 1),
                              ("mpi_4rank", "mpi", 4), ("mpi_8rank", "mpi", 8),
                              ("mpi_16rank", "mpi", 16)]:
        for phase in ("precheck", "steady"):
            run_phase(scaling / label / phase, mode, nrank, "a1e5", "P", phase)
    run_check("check_scaling.py", scaling)
    # No truncated zip comparison: trajectories must cover identical step indices.
    import csv
    trajectories = []
    for label in ("serial_1rank", "mpi_1rank", "mpi_4rank", "mpi_8rank", "mpi_16rank"):
        with (scaling / label / "steady/diagnostics.csv").open(newline="") as fh:
            trajectories.append([int(r["step"]) for r in csv.DictReader(fh)])
    if any(t != trajectories[0] for t in trajectories[1:]):
        (scaling / "batch_status.txt").write_text("SCALING_TRAJECTORY_COVERAGE_FAIL=true\n")
        raise RuntimeError("scaling trajectory step coverage mismatch; production blocked")
    field_checks = [check_field_slice(scaling / label / "steady/field_slice.csv", 2)
                    for label in ("serial_1rank", "mpi_1rank", "mpi_4rank", "mpi_8rank", "mpi_16rank")]
    (scaling / "FIELD_OUTPUT_AUDIT.json").write_text(
        json.dumps({"field_outputs_PASS": True, "checks": field_checks}, indent=2) + "\n")
    (scaling / "batch_status.txt").write_text("SCALING_NUMERIC_AND_FIELDS_PASS=true\n")

    batch = new_batch("g4_period_nx2_fields_v1")
    (CASE / "results/latest_fields_batch.txt").write_text(batch.name + "\n")
    configs = [(tag, direction) for tag in TAGS for direction in ("P", "T")]
    for tag, direction in configs:
        run_phase(batch / "runs" / f"nx2_{direction}_{tag}" / "precheck",
                  "mpi", 8, tag, direction, "precheck")
    (batch / "batch_status.txt").write_text("PRECHECK_MATRIX=PASS\n")
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(run_phase, batch / "runs" / f"nx2_{direction}_{tag}" / "steady",
                               "mpi", 8, tag, direction, "steady") for tag, direction in configs]
        errors = []
        for future in futures:
            try:
                future.result()
            except Exception as error:
                errors.append(str(error))
    if errors:
        with (batch / "batch_status.txt").open("a") as fh:
            fh.write("STEADY_OR_FIELDS_FAIL=true\n" + "\n".join(errors) + "\n")
        raise SystemExit("production failed; raw evidence preserved: " + "; ".join(errors))
    run_check("postprocess_period_fields.py", batch)
    with (batch / "batch_status.txt").open("a") as fh:
        fh.write("NUMERICAL_AND_FIELD_OUTPUTS_PASS=true\nHUMAN_RELEASE_REVIEW=pending\n")
    print(f"new Nx=2 finished: {batch}; review T mass trajectories before Nx=4", flush=True)


if __name__ == "__main__":
    main()
