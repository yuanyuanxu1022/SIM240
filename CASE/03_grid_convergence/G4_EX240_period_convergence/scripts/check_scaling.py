#!/usr/bin/env python3
"""G4 scaling-test verdict against the frozen criteria (protocol section 7).

Usage: check_scaling.py SCALING_BATCH_DIR
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

CONFIGS = ("serial_1rank", "mpi_1rank", "mpi_4rank", "mpi_8rank", "mpi_16rank")
EXPECT_LINKS = 260352
JTOL = 1e-10
MASSTOL = 1e-12


def kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            out[key.strip()] = value.strip()
    return out


def mass_trajectory(path: Path) -> list[float]:
    with path.open() as fh:
        rows = list(csv.DictReader(fh))
    return [float(row["mass_error"]) for row in rows]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_scaling.py BATCH_DIR")
    batch = Path(sys.argv[1]).resolve()
    errors: list[str] = []
    results: dict[str, dict] = {}

    for label in CONFIGS:
        steady = batch / label / "steady"
        if not steady.exists():
            errors.append(f"missing config: {label}")
            continue
        exit_code = int((steady / "exit_code.txt").read_text().strip())
        values = kv(steady / "result.txt")
        results[label] = values
        if exit_code != 0 or values.get("PASS") != "true":
            errors.append(f"{label}: gates FAIL (exit={exit_code}, PASS={values.get('PASS')})")
            continue
        if int(values.get("candidate_links", "-1")) != EXPECT_LINKS:
            errors.append(f"{label}: candidate_links != {EXPECT_LINKS}")
        if abs(float(values["q_min"]) - 0.5) > 1e-10 or abs(float(values["q_max"]) - 0.5) > 1e-10:
            errors.append(f"{label}: q != 0.5")
        if float(values["max_mass_abs_relative"]) >= 1e-10:
            errors.append(f"{label}: mass gate")

    ref = results.get("serial_1rank", {})
    if ref and not errors:
        ref_j = float(ref["J_main_m2_s"])
        ref_mass = mass_trajectory(batch / "serial_1rank" / "steady" / "diagnostics.csv")
        for label in ("mpi_1rank", "mpi_4rank", "mpi_8rank", "mpi_16rank"):
            values = results[label]
            j = float(values["J_main_m2_s"])
            rel = abs(j - ref_j) / abs(ref_j)
            mass = mass_trajectory(batch / label / "steady" / "diagnostics.csv")
            diff = max(abs(m - r) for m, r in zip(mass, ref_mass))
            if rel > JTOL:
                errors.append(f"{label}: |dJ|/J = {rel:.3e} > {JTOL}")
            if diff > MASSTOL:
                errors.append(f"{label}: mass trajectory diff = {diff:.3e} > {MASSTOL}")
            print(f"{label}: J={j:.17g} |dJ|/J={rel:.3e}  mass_diff={diff:.3e}")

    report = batch / "scaling_report.txt"
    if errors:
        report.write_text("scaling FAIL\n" + "\n".join(f"- {e}" for e in errors) + "\n")
        print(f"scaling FAIL: {errors}")
        raise SystemExit(1)
    report.write_text("scaling PASS: all configs meet frozen criteria\n")
    print("scaling PASS")


if __name__ == "__main__":
    main()
