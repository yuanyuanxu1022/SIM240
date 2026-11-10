#!/usr/bin/env python3
"""Audit actual 18-case rectangular interfaces, without matrix assembly."""

import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

from .interface import PACKAGE_ROOT, Rejected, build_interface, select


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--planned-id", help="one of the bound 18 IDs; omitted audits all")
    args = parser.parse_args(argv)
    begin = time.monotonic()
    plans = select(planned_id=args.planned_id)
    records = []
    for plan in plans:
        # Keep only the small audit record. The live mesh/MPC is scoped to one
        # case at a time; no mesh is mistaken for a completed numerical result.
        record = build_interface(plan["planned_id"])["stats"]
        records.append(record)
    input_paths = [PACKAGE_ROOT/"protocol/benchmarks18.csv",
                   PACKAGE_ROOT/"protocol/review_input_hashes.json",
                   PACKAGE_ROOT/"protocol/method_contract.json",
                   PACKAGE_ROOT/"src/contract.py",
                   PACKAGE_ROOT/"mesh_periodic_pressure_20261025/interface.py"]
    result = {"kind": "ACTUAL_RECTANGULAR_MESH_PERIODIC_GAUGE_INTERFACE_AUDIT",
              "status": "STATIC_INTERFACE_CHECK_ONLY", "planned_count": len(plans),
              "accepted_count": len(records), "cases": records,
              "input_sha256": {str(p.relative_to(PACKAGE_ROOT)): digest(p) for p in input_paths},
              "elapsed_seconds": time.monotonic()-begin,
              "peak_RSS_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "matrix_assembled": False, "rhs_assembled": False,
              "solver_called": False, "actual_run_id": None,
              "NUMERICAL_GATE": "NOT_EVALUATED", "RESULT_PASS": False,
              "geometry_PASS": None, "prediction_permission": "HOLD"}
    return result


if __name__ == "__main__":
    try:
        print(json.dumps(main(), ensure_ascii=False, indent=2, allow_nan=False))
    except (Rejected, ValueError, RuntimeError) as exc:
        print(json.dumps({"kind": "INTERFACE_AUDIT_REJECTED", "reason": str(exc),
                          "solver_called": False, "NUMERICAL_GATE": "NOT_EVALUATED"}),
              file=sys.stderr)
        sys.exit(1)
