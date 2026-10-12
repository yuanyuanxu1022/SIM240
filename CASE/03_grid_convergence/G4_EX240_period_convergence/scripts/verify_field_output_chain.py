#!/usr/bin/env python3
"""Initialized-state export check. No collideAndStream or steady calculation."""
import argparse
import csv
import hashlib
import json
import math
import subprocess
from datetime import datetime
from pathlib import Path

from check_field_slice import DX, check_field_slice
from generate_period_source_fields import generate

CASE = Path(__file__).resolve().parents[1]
BUILD = CASE / "build_fields_v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifacts():
    paths = [BUILD / "g4_nx2_serial_a1e5"]
    paths += [BUILD / f"g4_nx2_mpi_{tag}" for tag in ("a5e4", "a1e5", "a2e5")]
    paths += [BUILD / "generated" / f"g4_nx2_{mode}.cpp" for mode in ("serial", "mpi")]
    paths += [BUILD / "generated" / f"g4_nx2_mpi_{tag}.cpp" for tag in ("a5e4", "a2e5")]
    paths += [CASE / "src/Makefile.fields", CASE / "scripts/generate_period_source_fields.py",
              CASE / "scripts/generate_period_source.py", CASE / "scripts/check_field_slice.py",
              CASE / "scripts/verify_field_output_chain.py"]
    return {str(path): sha(path) for path in paths}


def read_values(path):
    with path.open(newline="") as fh:
        return {(round(float(r["x"]) / DX - 0.5), round(float(r["z"]) / DX - 0.5)):
                [float(r[k]) for k in ("ux", "uy", "uz", "speed", "rho", "pressure", "Phi")]
                for r in csv.DictReader(fh)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ranks", default="1,4,8,16")
    args = parser.parse_args()
    ranks = [int(v) for v in args.ranks.split(",")]
    for mode in ("serial", "mpi"):
        source = BUILD / "generated" / f"g4_nx2_{mode}.cpp"
        if source.read_text() != generate(2, mode):
            raise SystemExit(f"stale generated source: {source}")
    for tag, acceleration in (("a5e4", "5.0e4"), ("a2e5", "2.0e5")):
        variant = BUILD / "generated" / f"g4_nx2_mpi_{tag}.cpp"
        expected = generate(2, "mpi").replace("constexpr T acceleration = 1.0e5;",
                                               f"constexpr T acceleration = {acceleration};")
        if variant.read_text() != expected:
            raise SystemExit(f"unexpected force-variant change: {variant}")
    digests = artifacts()
    work = BUILD / ("fieldcheck_" + datetime.now().strftime("%Y%m%dT%H%M%S%z"))
    work.mkdir(exist_ok=False)
    checks = []
    for direction in ("P", "T"):
        reference = None
        for mode, nrank in [("serial", 1)] + [("mpi", n) for n in ranks]:
            dest = work / f"{direction}_{mode}_{nrank}rank"
            dest.mkdir()
            binary = BUILD / f"g4_nx2_{mode}_a1e5"
            (dest / "run_manifest.txt").write_text(
                f"formal_simulation=false\nmode=fieldcheck\nranks={nrank}\n"
                f"binary_sha256={sha(binary)}\nsource_sha256="
                f"{sha(BUILD / 'generated' / f'g4_nx2_{mode}.cpp')}\n")
            command = ["mpirun", "-np", str(nrank), "-x", f"G4_EXPECTED_RANKS={nrank}",
                       str(binary), "fieldcheck", direction, str(dest)]
            print(f"fieldcheck {direction} {mode} {nrank}rank", flush=True)
            with (dest / "run.log").open("w") as log:
                run = subprocess.run(command, cwd=dest, stdout=log, stderr=subprocess.STDOUT,
                                     timeout=180)
            (dest / "exit_code.txt").write_text(f"{run.returncode}\n")
            if run.returncode:
                raise SystemExit(f"fieldcheck exit {run.returncode}: {dest / 'run.log'}")
            check = check_field_slice(dest / "field_slice.csv", 2)
            values = read_values(dest / "field_slice.csv")
            if reference is None:
                reference = values
            if values.keys() != reference.keys():
                raise SystemExit("MPI/serial coordinate coverage mismatch")
            max_diff = [0.0] * 7
            for point, row in values.items():
                for k, (value, expected) in enumerate(zip(row, reference[point])):
                    max_diff[k] = max(max_diff[k], abs(value - expected))
                    if not math.isclose(value, expected, rel_tol=1e-12, abs_tol=1e-18):
                        raise SystemExit(f"initialized field mismatch at {point}, column {k}")
            check.update({"direction": direction, "mode": mode, "ranks": nrank,
                          "max_abs_diff_vs_serial": max_diff,
                          "field_sha256": sha(dest / "field_slice.csv")})
            checks.append(check)
    report = {"output_chain_PASS": True, "formal_simulation": False,
              "collide_and_stream_calls": 0, "work_directory": str(work),
              "artifact_sha256": digests, "checks": checks,
              "scope": "initialized-state output only; full numerical scaling still required"}
    (BUILD / "OUTPUT_CHAIN_CHECK.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"output chain PASS: {len(checks)} exports, each 9600 rows; "
          "full initialized fields match serial reference", flush=True)


if __name__ == "__main__":
    main()
