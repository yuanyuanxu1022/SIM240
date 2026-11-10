"""Small negative controls for the reviewed no-solve seam."""

import os
import json
from pathlib import Path
import subprocess
import sys

from petsc4py import PETSc

from entry import attach_checked_gauge, prepare_bound_mixed_system, Rejected

HERE = Path(__file__).resolve().parent


def must_reject(function, reason):
    try:
        function()
    except Rejected as exc:
        if str(exc) != reason:
            raise AssertionError((str(exc), reason)) from exc
    else:
        raise AssertionError("EXPECTED_REJECTION: " + reason)


def main():
    system = prepare_bound_mixed_system("B0MIN_MMS_mixed_N8")
    A, b = system["matrix"], system["rhs"]
    old = system["item"]["pressure"]["constant_vector"]
    must_reject(lambda: attach_checked_gauge(A, b.copy(), old),
                "PRESSURE_GAUGE_OR_RHS_INCOMPATIBLE")
    b_bad = b.copy()
    index = int(next(i for i, value in enumerate(system["candidate"]) if value))
    b_bad.setValue(index, 1., addv=PETSc.InsertMode.ADD_VALUES)
    b_bad.assemblyBegin()
    b_bad.assemblyEnd()
    must_reject(lambda: attach_checked_gauge(A, b_bad, system["candidate"]),
                "PRESSURE_GAUGE_OR_RHS_INCOMPATIBLE")
    must_reject(lambda: prepare_bound_mixed_system("B0MIN_MMS_scalar_N8"),
                "MIXED_PRESSURE_CASE_REQUIRED")
    for forbidden in ("--solve", "--execute", "--mode solve"):
        result = subprocess.run([sys.executable, "-B", str(HERE / "entry.py"),
                                 "--planned-id", "B0MIN_MMS_mixed_N8", *forbidden.split()],
                                env=os.environ.copy(), capture_output=True, text=True)
        if result.returncode != 2:
            raise AssertionError((forbidden, result.returncode))
    outcome = {"status": "PASS", "wrong_old_gauge_rejected": True,
               "incompatible_pressure_rhs_rejected": True,
               "scalar_case_rejected": True,
               "forbidden_cli_modes_rejected": ["--solve", "--execute", "--mode solve"],
               "negative_controls_passed": 6, "solver_called": False}
    target = HERE / "evidence/negative_controls.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(outcome, indent=2) + "\n")
    print("negative_controls=6 PASS; solver_called=false")


if __name__ == "__main__":
    main()
