#!/usr/bin/env python3
"""Validate the candidate G3-h matrix without running OpenLB."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


DX_NM = 2.5
EXPECTED_HEIGHTS = (50, 75, 125)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write preflight.csv under this case")
    args = parser.parse_args()
    case_root = Path(__file__).resolve().parents[1]
    matrix = case_root / "height_matrix.csv"
    rows = list(csv.DictReader(matrix.open()))
    heights = tuple(int(row["height_nm"]) for row in rows)
    if heights != EXPECTED_HEIGHTS:
        raise SystemExit(f"unexpected height matrix: {heights}")
    for row in rows:
        height = int(row["height_nm"])
        cells = height / DX_NM
        if not cells.is_integer() or int(cells) != int(row["cells_at_dx2p5"]):
            raise SystemExit(f"height representation failure at h={height} nm")
        h_ref = height + 50
        if h_ref != int(row["H_ref_nm"]):
            raise SystemExit(f"reference-height mismatch at h={height} nm")
    if args.write:
        output = case_root / "preflight.csv"
        with output.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=("height_nm", "cells_at_dx2p5", "H_ref_nm", "preflight_PASS"))
            writer.writeheader()
            for row in rows:
                writer.writerow({"height_nm": row["height_nm"], "cells_at_dx2p5": row["cells_at_dx2p5"], "H_ref_nm": row["H_ref_nm"], "preflight_PASS": "true"})
        print(f"PASS wrote {output}")
    else:
        print("PASS height matrix is exactly represented at dx=2.5 nm")


if __name__ == "__main__":
    main()
