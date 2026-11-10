"""Review callable solver source and pressure output mapping without solving."""

import ast
import csv
import hashlib
import importlib.util
import inspect  # Load the stdlib module before any project module named inspect.py.
import json
from pathlib import Path
import sys

import numpy as np

from candidate_solver import (CandidateRejected, DiagnosticGMRES, check_release,
                              solve_prepared_mixed_system)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_previous_entry():
    source = ROOT / "solve_entry_review_20261025/entry.py"
    spec = importlib.util.spec_from_file_location("d4_preflight_entry_review", source)
    module = importlib.util.module_from_spec(spec)
    mesh_path = str(ROOT / "mesh_periodic_pressure_20261025")
    try:
        spec.loader.exec_module(module)
    finally:
        # The former entry imports its mesh interface from a directory that
        # also contains inspect.py. Do not leave it before the stdlib path.
        sys.path[:] = [p for p in sys.path if p != mesh_path]
    if mesh_path in str(Path(inspect.__file__).resolve()):
        raise RuntimeError("STDLIB_INSPECT_SHADOWED")
    return module


def assert_only_reviewed_solve_call():
    tree = ast.parse((HERE / "candidate_solver.py").read_text())
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "solve":
            calls.append(node.lineno)
    if len(calls) != 1:
        raise RuntimeError("EXPECTED_ONE_DORMANT_SOLVE_CALL")
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == "solve_prepared_mixed_system")
    if not any(n.lineno in calls for n in ast.walk(function) if hasattr(n, "lineno")):
        raise RuntimeError("SOLVE_CALL_OUTSIDE_GATED_FUNCTION")
    return calls[0]


def main():
    solve_line = assert_only_reviewed_solve_call()
    from petsc4py import PETSc

    api = {"GMRES": hasattr(PETSc.KSP.Type, "GMRES"),
           "PC_NONE": hasattr(PETSc.PC.Type, "NONE"),
           "UNPRECONDITIONED_NORM": hasattr(PETSc.KSP.NormType, "UNPRECONDITIONED"),
           "GMRES_RESTART": hasattr(PETSc.KSP, "setGMRESRestart"),
           "CONVERGENCE_REASON": hasattr(PETSc.KSP, "getConvergedReason"),
           "ITERATION_NUMBER": hasattr(PETSc.KSP, "getIterationNumber")}
    if not all(api.values()):
        raise RuntimeError("CANDIDATE_PETSC_API_MISSING")
    try:
        solve_prepared_mixed_system(None, None, None)
    except CandidateRejected as exc:
        if str(exc) != "SOLVER_SETTINGS_REQUIRED":
            raise
    else:
        raise RuntimeError("UNGUARDED_SOLVE_CALL")
    try:
        DiagnosticGMRES(0, 1e-10, 100, 20).validate()
    except CandidateRejected as exc:
        if str(exc) != "INVALID_DIAGNOSTIC_GMRES_SETTINGS":
            raise
    else:
        raise RuntimeError("INVALID_SOLVER_SETTINGS_ACCEPTED")

    old = load_previous_entry()
    rows = list(csv.DictReader((ROOT / "protocol/benchmarks18.csv").open(
        encoding="utf-8-sig", newline="")))
    ids = [r["planned_id"] for r in rows if r["direction_or_field"] in {"T", "mixed"}]
    if len(ids) != 9:
        raise RuntimeError("EXPECTED_NINE_PRESSURE_CASES")
    settings = DiagnosticGMRES(1e-10, 1e-10, 100, 20)
    settings.validate()  # Structural example only, never an approved value.
    synthetic = {"item": {"plan": {"execution_authorized": True,
                                      "planned_id": "SYNTHETIC_ONLY"}},
                 "matrix_csr_sha256": "synthetic-matrix",
                 "rhs_sha256_before_projection": "synthetic-rhs",
                 "gauge": {"right_and_transpose_nullspaces_attached": True}}
    synthetic_release = {"status": "APPROVED_FOR_RECTANGLE_SOLVE",
                         "planned_id": "SYNTHETIC_ONLY",
                         "matrix_csr_sha256": "synthetic-matrix",
                         "rhs_sha256_before_projection": "synthetic-rhs"}
    check_release(synthetic, settings, synthetic_release)  # Only guard logic; no KSP.
    try:
        check_release(synthetic, settings, {**synthetic_release,
                                           "rhs_sha256_before_projection": "wrong"})
    except CandidateRejected as exc:
        if str(exc) != "RELEASE_INPUT_BINDING_MISMATCH":
            raise
    else:
        raise RuntimeError("WRONG_SYNTHETIC_RELEASE_ACCEPTED")
    alignment = []
    for ident in ids:
        item = old.build_interface(ident)
        try:
            check_release({"item": item}, settings, release=None)
        except CandidateRejected as exc:
            if str(exc) != "FROZEN_WHITELIST_DENIES_SOLVE":
                raise
        else:
            raise RuntimeError("FROZEN_CASE_COULD_SOLVE")
        q0, _ = item["space"].sub(1).collapse()
        q1 = item["pressure"]["space"]
        a, b = q0.tabulate_dof_coordinates(), q1.tabulate_dof_coordinates()
        if a.shape != b.shape:
            raise RuntimeError("PRESSURE_DOF_COUNT_MISMATCH")
        difference = float(np.max(np.abs(a-b)))
        weights = item["pressure"]["nodal_area_weights"]
        if difference > 1e-11 or len(weights) != len(a):
            raise RuntimeError("PRESSURE_WEIGHT_ORDER_MISMATCH")
        alignment.append({"planned_id": ident, "P1_dofs": len(a),
                          "original_vs_MPC_pressure_coord_max_difference": difference,
                          "triangle_area_weight_sum": float(np.sum(weights)),
                          "frozen_plan_denies_solve": True})
    previous = json.loads((ROOT / "solve_entry_review_20261025/evidence/independent_review.json").read_text())
    if previous["status"] != "PASS" or previous["nine_preflights_checked"] != 9:
        raise RuntimeError("PREVIOUS_PREFLIGHT_NOT_CONFIRMED")
    contract = json.loads((HERE / "record_contract.json").read_text())
    if (contract["status"] != "DRAFT_NOT_APPROVED_NOT_A_RESULT"
            or contract["current_values"]["formal_run_id"] is not None
            or contract["current_values"]["solver_exit_code"] is not None
            or contract["current_values"]["NUMERICAL_GATE"] != "NOT_EVALUATED"):
        raise RuntimeError("RECORD_PLAN_MISREPRESENTS_RESULT")
    if len(set(contract["required_before_solve"])) != len(contract["required_before_solve"]):
        raise RuntimeError("DUPLICATE_PRE_SOLVE_FIELD")
    if len(set(contract["required_after_solve"])) != len(contract["required_after_solve"]):
        raise RuntimeError("DUPLICATE_POST_SOLVE_FIELD")
    sources = [ROOT / "protocol/benchmarks18.csv", ROOT / "protocol/method_contract.json",
               ROOT / "solve_entry_review_20261025/entry.py",
               ROOT / "solve_entry_review_20261025/evidence/independent_review.json",
               HERE / "candidate_solver.py", HERE / "record_contract.json",
               HERE / "audit_static.py", HERE / "verify_review.py"]
    outcome = {"status": "STATIC_REVIEW_PASS_NOT_SOLVE_PERMISSION",
               "previous_preflight_confirmed": True,
               "pressure_dof_alignment": alignment,
               "frozen_plan_rejections": len(alignment),
               "synthetic_release_guard_checked_without_KSP": True,
               "candidate_function_signature": str(inspect.signature(solve_prepared_mixed_system)),
               "dormant_solve_call_line": solve_line,
               "petsc_api_present_without_KSP_instantiation": api,
               "record_plan_before_fields": len(contract["required_before_solve"]),
               "record_plan_after_fields": len(contract["required_after_solve"]),
               "source_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in sources},
               "solver_object_created": False, "solver_called": False,
               "formal_run_id": None, "NUMERICAL_GATE": "NOT_EVALUATED",
               "RESULT_PASS": False, "geometry_PASS": None}
    target = HERE / "evidence/static_review.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(outcome, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print("static_review=PASS pressure_cases=9 frozen_rejections=9 solver_called=false")


if __name__ == "__main__":
    main()
