#!/usr/bin/env python3
"""Manually launched Nx=4 only, bound to reviewed Nx=2; no auto-advance."""
import argparse
import csv
import fcntl
import hashlib
import json
import math
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path

from check_field_slice import check_field_slice
from postprocess_period import check_gates, parse_kv

CASE = Path(__file__).resolve().parents[1]
BUILD = CASE / "build_fields_nx4"
PREVIOUS = CASE / "results/g4_period_nx2_fields_v1_20261012T001316+0800"
RELEASE = CASE / "reports/NX2_FIELDS_RELEASE_20261012.json"
TAGS = {"a5e4": 5e4, "a1e5": 1e5, "a2e5": 2e5}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_hashes(hashes):
    for path, digest in hashes.items():
        require(sha(path) == digest, f"SHA mismatch: {path}")


def source_for(tag):
    return BUILD / "generated" / ("g4_nx4_mpi.cpp" if tag == "a1e5"
                                    else f"g4_nx4_mpi_{tag}.cpp")


def e_ratio(previous, current):
    require(math.isfinite(previous) and math.isfinite(current) and previous > 0 and current > 0,
            "nonfinite/nonpositive resistance")
    error = abs(current - previous) / previous
    require(error <= 0.01, f"E(2->4)={error:.17g} exceeds frozen 1%")
    return error


def audit_run(dest, nx, steady=True):
    exit_code = int((dest / "exit_code.txt").read_text())
    require(exit_code == 0, f"independent exit={exit_code}: {dest}")
    values = parse_kv(dest / "result.txt")
    boundary = parse_kv(dest / "boundary_audit.txt")
    for key in ("geometry_PASS", "q_audit_PASS"):
        require(boundary.get(key) == "true", f"{key}: {dest}")
    for key in ("candidate_links", "valid_distance_links", "installed_links"):
        require(int(boundary[key]) == 130176 * nx, f"boundary count {key}: {dest}")
    for key in ("geometric_fallback_count", "missing_fluid_neighbour_fallback_count",
                "unresolved_link_count"):
        require(int(boundary[key]) == 0, f"boundary {key}: {dest}")
    if not steady:
        require(values.get("converter_PASS") == "true", f"converter: {dest}")
        return values, None
    for key in ("max_mass_abs_relative", "max_density_deviation", "max_Mach",
                "section_relative_difference", "window_cross_abs_max", "window_main_rel_std",
                "window_main_rel_span", "q_min", "q_max", "J_main_m2_s", "Keff_m3",
                "R_eff_Pa_s_per_m3"):
        require(math.isfinite(float(values[key])), f"nonfinite result {key}: {dest}")
    require(not check_gates(values, nx, exit_code), f"numerical gate failure: {dest}")
    require(values.get("converged") == "true" and values.get("exit_code") == "0",
            f"missing convergence/internal exit: {dest}")
    volume, nominal = float(values["fluid_volume_m3"]), float(values["nominal_volume_m3"])
    require(nominal > 0 and math.isfinite(volume) and abs(volume - nominal) / nominal <= 1e-10,
            f"geometry volume: {dest}")
    field = check_field_slice(dest / "field_slice.csv", nx)
    field["sha256"] = sha(dest / "field_slice.csv")
    with (dest / "diagnostics.csv").open(newline="") as fh:
        reader = csv.DictReader(fh)
        last_step = -1
        peak_mass = 0.0
        for row in reader:
            require(None not in row and all(v is not None for v in row.values()),
                    f"truncated diagnostic row: {dest}")
            numbers = {key: float(value) for key, value in row.items()}
            require(all(math.isfinite(v) for v in numbers.values()), f"nonfinite diagnostics: {dest}")
            step = numbers["step"]
            require(step == int(step) and step == last_step + 1, f"missing/repeated step: {dest}")
            last_step = int(step)
            peak_mass = max(peak_mass, abs(numbers["mass_error"]))
            require(peak_mass <= 1e-10 and numbers["Mach"] < 0.05
                    and numbers["max_density_deviation"] <= 1e-6
                    and numbers["finite"] == 1, f"diagnostic gate: {dest}")
        require(last_step == int(values["steps_completed"]), f"diagnostic coverage: {dest}")
    # Preserve all required final profile/summary and VTK output, not just flags.
    for filename in ("result_summary.csv", "pressure_profile.csv", "velocity_profile.csv",
                     "energy_dissipation.csv"):
        path = dest / filename
        require(path.is_file() and path.stat().st_size > 0, f"missing output: {path}")
        with path.open(newline="") as fh:
            table = csv.reader(fh)
            header = next(table)
            count = 0
            for row in table:
                numeric = row[2:] if filename == "result_summary.csv" else row
                require(len(row) == len(header) and all(math.isfinite(float(v)) for v in numeric),
                        f"malformed/nonfinite final CSV: {path}")
                count += 1
            require(count > 0, f"header-only final CSV: {path}")
    require(any((dest / "vtkData").rglob("*.vti")), f"missing VTK field: {dest}")
    return values, field


def readiness():
    release = json.loads(RELEASE.read_text())
    require(release.get("release_PASS") is True and release["batch"] == str(PREVIOUS),
            "reviewed Nx=2 release missing")
    verify_hashes(release["sha256"])
    verify_hashes(json.loads((PREVIOUS / "SOURCE_MANIFEST.json").read_text())["sha256"])
    probe = json.loads((BUILD / "PREPARATION_CHECK.json").read_text())
    require(probe.get("preparation_PASS") is True, "Nx=4 short checks not passed")
    verify_hashes(probe["artifact_sha256"])
    expected = {(d, "mpi", tag, phase) for d in ("P", "T") for tag in TAGS
                for phase in ("precheck", "fieldcheck")}
    actual = {(c["direction"], c["mode"], c["force"], c["phase"])
              for c in probe["checks"] if c["mode"] == "mpi"}
    require(actual == expected, "incomplete Nx=4 preparation matrix")
    for check in probe["checks"]:
        require(check["exit_code"] == 0, "short check exit failure")
        if check["phase"] == "fieldcheck":
            require(sha(check["path"]) == check["field_sha256"], "probe field changed")
    for tag in TAGS:
        for direction in ("P", "T"):
            audit_run(PREVIOUS / "runs" / f"nx2_{direction}_{tag}" / "steady", 2)
    require(shutil.disk_usage(CASE).free >= 10 * 1024**3, "less than 10 GiB free disk")
    return probe


def active_solvers():
    pids = []
    for proc in Path("/proc").glob("[0-9]*"):
        try:
            exe = (proc / "cmdline").read_bytes().split(b"\0", 1)[0].decode()
        except (OSError, UnicodeError):
            continue
        if any(exe.startswith(str(CASE / folder / "g4_nx"))
               for folder in ("build", "build_fields_v1", "build_fields_nx4")):
            pids.append(int(proc.name))
    return pids


def run_phase(batch, tag, direction, phase):
    dest = batch / "runs" / f"nx4_{direction}_{tag}" / phase
    dest.mkdir(parents=True, exist_ok=False)
    binary = BUILD / f"g4_nx4_mpi_{tag}"
    data = {"run_id": f"{batch.name}_nx4_{direction}_{tag}_{phase}", "nx_periods": 4,
            "phase": phase, "direction": direction, "ranks": 16,
            "acceleration_m_s2": TAGS[tag], "binary_sha256": sha(binary),
            "source_sha256": sha(source_for(tag)), "previous_batch": PREVIOUS.name,
            "protocol_sha256": sha(CASE / "PERIOD_CONVERGENCE_PROTOCOL.md")}
    (dest / "run_manifest.txt").write_text("".join(f"{k}={v}\n" for k, v in data.items()))
    print(f"launch nx4_{direction}_{tag}/{phase} ranks=16", flush=True)
    with (dest / "run.log").open("w") as log:
        run = subprocess.run(["mpirun", "-np", "16", "-x", "G4_EXPECTED_RANKS=16",
                              str(binary), phase, direction, str(dest)],
                             cwd=dest, stdout=log, stderr=subprocess.STDOUT)
    (dest / "exit_code.txt").write_text(f"{run.returncode}\n")
    audit_run(dest, 4, phase == "steady")
    print(f"finished nx4_{direction}_{tag}/{phase}", flush=True)


def postprocess(batch):
    rows, fields = [], []
    for tag in TAGS:
        for direction in ("P", "T"):
            values, field = audit_run(batch / "runs" / f"nx4_{direction}_{tag}" / "steady", 4)
            rows.append({"nx": 4, "direction": direction, "acceleration": TAGS[tag],
                         "J": float(values["J_main_m2_s"]), "K": float(values["Keff_m3"]),
                         "R": float(values["R_eff_Pa_s_per_m3"]),
                         "steps": int(values["steps_completed"]), "gates_pass": True})
            fields.append(field)
    with (batch / "postprocess_summary.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    linearity, ratios, errors = [], [], []
    for direction in ("P", "T"):
        points = [r for r in rows if r["direction"] == direction]
        xs, ys, ks = ([r[key] for r in points] for key in ("acceleration", "J", "K"))
        mx, my = sum(xs) / 3, sum(ys) / 3
        slope = sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / sum((x-mx)**2 for x in xs)
        intercept = my - slope * mx
        r2 = 1 - sum((y-slope*x-intercept)**2 for x, y in zip(xs, ys)) / sum((y-my)**2 for y in ys)
        span = (max(ks)-min(ks)) / (max(ks)+min(ks))
        if not (math.isfinite(r2) and math.isfinite(span) and r2 >= 0.9999 and span <= 0.01):
            errors.append(f"linearity failure: {direction}")
        linearity.append(dict(direction=direction, slope=slope, intercept=intercept,
                              R2=r2, K_max_relative_spread=span))
        previous = float(parse_kv(PREVIOUS / "runs" / f"nx2_{direction}_a1e5/steady/result.txt")
                         ["R_eff_Pa_s_per_m3"])
        current = next(r["R"] for r in points if r["acceleration"] == 1e5)
        try:
            error = e_ratio(previous, current)
        except RuntimeError as failure:
            error = abs(current - previous) / previous
            errors.append(str(failure))
        ratios.append(dict(pair="2->4", direction=direction, R_prev=previous, R_curr=current,
                           E_relative=error, previous_batch=PREVIOUS.name))
    for filename, records in (("linearity.csv", linearity), ("E_ratios.csv", ratios)):
        with (batch / filename).open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    (batch / "FIELD_OUTPUT_AUDIT.json").write_text(json.dumps(
        {"field_outputs_PASS": True, "checks": fields}, indent=2) + "\n")
    require(not errors, "; ".join(errors))
    (batch / "G4_LEVEL_REPORT.md").write_text(
        f"# G4 Nx=4\n\nBatch: {batch.name}\nPrevious: {PREVIOUS.name}\n\n"
        "Numerical, geometry, q, convergence, independent exit, fields, linearity and E: PASS.\n"
        "Human T mass trajectory/release review: pending.\n\n"
        "Evidence boundary: numerical invariance / seam integrity only; "
        "not physical representative-scale convergence.\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    probe = readiness()
    require(not active_solvers(), "another G4 simulation is active")
    print("readiness PASS; reviewed Nx=2 SHA-bound; concurrency=1; ranks=16; no automatic Nx=8", flush=True)
    if args.check_only:
        return
    with (CASE / "results/.nx4_fields_runner.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not active_solvers(), "another G4 simulation started")
        stamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
        batch = CASE / "results" / f"g4_period_nx4_fields_v1_{stamp}"
        batch.mkdir(exist_ok=False)
        hashes = dict(probe["artifact_sha256"])
        for path in (Path(__file__).resolve(), RELEASE, BUILD / "PREPARATION_CHECK.json",
                     CASE / "PERIOD_CONVERGENCE_PROTOCOL.md", CASE / "scripts/postprocess_period.py",
                     CASE / "scripts/generate_period_source.py",
                     Path("/home/dell/openlb/build/lib/libolbcore.a")):
            hashes[str(path)] = sha(path)
        manifest = {"batch_id": batch.name, "previous_batch": str(PREVIOUS), "sha256": hashes,
                    "repository_commit": subprocess.check_output(["git", "-C", str(CASE), "rev-parse", "HEAD"], text=True).strip(),
                    "git_status": subprocess.check_output(["git", "-C", str(CASE), "status", "--short"], text=True),
                    "OpenLB_commit": subprocess.check_output(["git", "-C", "/home/dell/openlb", "rev-parse", "HEAD"], text=True).strip(),
                    "OpenLB_compile_version": "5953d8a-dirty", "concurrency": 1, "ranks_per_point": 16,
                    "parameters": {**json.loads((PREVIOUS / "SOURCE_MANIFEST.json").read_text())["parameters"],
                                   "nx_periods": 4, "maximum_steps": 960000}, "automatic_next_level": False}
        (batch / "SOURCE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
        shutil.copy2(RELEASE, batch / "PREVIOUS_RELEASE.json")
        (CASE / "results/latest_fields_nx4.txt").write_text(batch.name + "\n")
        print(f"batch={batch}", flush=True)
        try:
            for tag in TAGS:
                for direction in ("P", "T"):
                    verify_hashes(hashes)
                    run_phase(batch, tag, direction, "precheck")
            (batch / "batch_status.txt").write_text("PRECHECK_MATRIX=PASS\n")
            for tag in TAGS:
                for direction in ("P", "T"):
                    verify_hashes(hashes)
                    run_phase(batch, tag, direction, "steady")
            try:
                verify_hashes(hashes)
                verify_hashes(json.loads(RELEASE.read_text())["sha256"])
                postprocess(batch)
            except Exception:
                (batch / "postprocess.log").write_text(traceback.format_exc())
                (batch / "postprocess_exit_code.txt").write_text("1\n")
                raise
            (batch / "postprocess.log").write_text("Numerical, field, linearity and bound E(2->4) checks PASS\n")
            (batch / "postprocess_exit_code.txt").write_text("0\n")
            with (batch / "batch_status.txt").open("a") as fh:
                fh.write("NUMERICAL_AND_FIELD_OUTPUTS_PASS=true\nHUMAN_RELEASE_REVIEW=pending\n")
        except Exception as error:
            with (batch / "batch_status.txt").open("a") as fh:
                fh.write(f"WORKFLOW_FAIL=true\nerror={error}\n")
            (batch / "workflow_exit_code.txt").write_text("1\n")
            raise
        (batch / "workflow_exit_code.txt").write_text("0\n")
        print(f"Nx=4 finished; review evidence before Nx=8: {batch}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError) as error:
        print(f"BLOCKED/FAIL: {error}", file=sys.stderr)
        sys.exit(1)
