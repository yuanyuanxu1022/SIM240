#!/usr/bin/env python3
"""Audit the frozen EX240 mid-y fluid slice, including coordinate coverage."""
import argparse
import csv
import math
from pathlib import Path

HEADER = ["x", "z", "ux", "uy", "uz", "speed", "rho", "pressure", "Phi", "material"]
DX = 2.5e-9


def check_field_slice(path: Path, nx_periods: int) -> dict:
    expected = {
        (ix, iz)
        for ix in range(96 * nx_periods)
        for iz in range(70 if 24 <= ix % 96 < 72 else 30)
    }
    seen = set()
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != HEADER:
            raise ValueError(f"{path}: incorrect field header")
        for line, row in enumerate(reader, 2):
            try:
                values = [float(row[key]) for key in HEADER]
            except (ValueError, TypeError, KeyError) as error:
                raise ValueError(f"{path}:{line}: malformed numeric row") from error
            if None in row or not all(math.isfinite(v) for v in values):
                raise ValueError(f"{path}:{line}: nonfinite or malformed row")
            lattice = [values[0] / DX - 0.5, values[1] / DX - 0.5]
            point = tuple(round(v) for v in lattice)
            if any(abs(v - i) > 1e-7 for v, i in zip(lattice, point)):
                raise ValueError(f"{path}:{line}: off-grid coordinate")
            if point not in expected:
                raise ValueError(f"{path}:{line}: unexpected fluid coordinate {point}")
            if point in seen:
                raise ValueError(f"{path}:{line}: duplicate coordinate {point}")
            if values[9] != 1 or values[6] <= 0:
                raise ValueError(f"{path}:{line}: invalid material or density")
            if not math.isclose(values[5], math.sqrt(sum(v*v for v in values[2:5])),
                                rel_tol=1e-12, abs_tol=1e-18):
                raise ValueError(f"{path}:{line}: speed/component mismatch")
            seen.add(point)
    if seen != expected:
        raise ValueError(f"{path}: data_rows={len(seen)}, expected={len(expected)}; "
                         f"missing={len(expected - seen)}")
    return {"path": str(path), "data_rows": len(seen),
            "expected_rows": 4800 * nx_periods, "coordinate_coverage_PASS": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--nx", type=int, choices=[1, 2, 4, 8], required=True)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    print(check_field_slice(args.path, args.nx))


if __name__ == "__main__":
    main()
