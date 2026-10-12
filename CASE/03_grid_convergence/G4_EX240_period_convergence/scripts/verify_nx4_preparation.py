#!/usr/bin/env python3
"""Nx=4 isolated preparation checks; never runs a steady simulation."""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from check_field_slice import check_field_slice
from generate_period_source_fields import generate
from verify_field_output_chain import read_values

CASE = Path(__file__).resolve().parents[1]
BUILD = CASE / "build_fields_nx4"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sources = {}
    for mode in ("serial", "mpi"):
        path = BUILD / "generated" / f"g4_nx4_{mode}.cpp"
        assert path.read_text() == generate(4, mode), f"stale source: {path}"
        sources[str(path)] = sha(path)
    for tag, acceleration in (("a5e4", "5.0e4"), ("a2e5", "2.0e5")):
        path = BUILD / "generated" / f"g4_nx4_mpi_{tag}.cpp"
        expected = generate(4, "mpi").replace("constexpr T acceleration = 1.0e5;",
                                              f"constexpr T acceleration = {acceleration};")
        assert path.read_text() == expected, f"unexpected force variant: {path}"
        sources[str(path)] = sha(path)
    binaries = [BUILD / "g4_nx4_serial_a1e5"] + [
        BUILD / f"g4_nx4_mpi_{tag}" for tag in ("a5e4", "a1e5", "a2e5")]
    digests = {str(path): sha(path) for path in binaries}
    digests.update(sources)
    for path in (Path(__file__).resolve(), CASE / "src/Makefile.fields_nx4",
                 CASE / "scripts/check_field_slice.py",
                 CASE / "scripts/generate_period_source_fields.py"):
        digests[str(path)] = sha(path)
    work = Path(tempfile.mkdtemp(prefix="preparation_", dir=BUILD))
    checks = []
    for direction in ("P", "T"):
        reference = None
        jobs = [("serial", "a1e5", 1, "fieldcheck")]
        jobs += [("mpi", tag, 16, phase) for tag in ("a5e4", "a1e5", "a2e5")
                 for phase in ("precheck", "fieldcheck")]
        for mode, tag, ranks, phase in jobs:
            dest = work / f"{direction}_{mode}_{tag}_{phase}"
            dest.mkdir()
            binary = BUILD / f"g4_nx4_{mode}_{tag}"
            source_name = (f"g4_nx4_{mode}.cpp" if tag == "a1e5"
                           else f"g4_nx4_{mode}_{tag}.cpp")
            (dest / "run_manifest.txt").write_text(
                f"formal_simulation=false\nmode={phase}\nnx=4\nranks={ranks}\n"
                f"binary_sha256={sha(binary)}\n"
                f"source_sha256={sha(BUILD / 'generated' / source_name)}\n")
            command = ["mpirun", "-np", str(ranks), "-x", f"G4_EXPECTED_RANKS={ranks}",
                       str(binary), phase, direction, str(dest)]
            print(dest.name, flush=True)
            with (dest / "run.log").open("w") as log:
                run = subprocess.run(command, cwd=dest, stdout=log,
                                     stderr=subprocess.STDOUT, timeout=180)
            (dest / "exit_code.txt").write_text(f"{run.returncode}\n")
            assert run.returncode == 0, f"failed: {dest}"
            record = {"direction": direction, "mode": mode, "force": tag,
                      "ranks": ranks, "phase": phase, "exit_code": run.returncode}
            if phase == "fieldcheck":
                record.update(check_field_slice(dest / "field_slice.csv", 4))
                record["field_sha256"] = sha(dest / "field_slice.csv")
                if tag == "a1e5":
                    values = read_values(dest / "field_slice.csv")
                    if mode == "serial":
                        reference = values
                    else:
                        assert values == reference, "initialized MPI/serial fields differ"
                        record["exact_serial_match"] = True
            else:
                result = dict(line.split("=", 1) for line in
                              (dest / "result.txt").read_text().splitlines() if "=" in line)
                assert all(result.get(key) == "true" for key in
                           ("geometry_PASS", "converter_PASS", "q_audit_PASS")), dest
                assert int(result["fluid_nodes"]) == 1843200, dest
                assert int(result["candidate_links"]) == int(result["installed_links"]) == 520704, dest
            checks.append(record)
    report = {"preparation_PASS": True, "formal_simulation": False,
              "collide_and_stream_calls": 0, "work_directory": str(work),
              "artifact_sha256": digests, "checks": checks}
    (BUILD / "PREPARATION_CHECK.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Nx=4 preparation PASS: 6 prechecks, 8 initialized exports of 19200 rows; no steady run")


if __name__ == "__main__":
    main()
