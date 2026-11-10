"""Independent, backend-free review of the preflight records and no-solve boundary."""

import ast
import csv
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = ROOT.parents[3]


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def check_no_solve_calls():
    for name in ("entry.py", "run_preflight.py"):
        source = (HERE / name).read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                function = node.func
                attr = (function.attr if isinstance(function, ast.Attribute)
                        else function.id if isinstance(function, ast.Name) else "")
                assert attr not in {"solve", "createKSP", "KSP", "LinearProblem"}, (name, attr)


def verify():
    check_no_solve_calls()
    rows = list(csv.DictReader((ROOT / "protocol/benchmarks18.csv").open(
        encoding="utf-8-sig", newline="")))
    wanted = [r["planned_id"] for r in rows if r["direction_or_field"] in {"T", "mixed"}]
    assert len(wanted) == 9 and all(r["authorized_to_execute"] == "False" for r in rows)
    previous = json.loads((ROOT / "pressure_assembly_audit_20261025/evidence/assembly_all9.json").read_text())
    old = {r["planned_id"]: r["result"] for r in previous["records"] if r["exit_code"] == 0}
    data = json.loads((HERE / "evidence/preflight_all9.json").read_text())
    assert data["status"] == "PREFLIGHT_COMPLETE" and data["planned_ids"] == wanted
    assert len(data["records"]) == 9 and data["solver_called"] is False
    for relative, expected in data["source_sha256"].items():
        assert sha256(ROOT / relative) == expected, relative
    max_right = max_left = max_backsub = 0.0
    for ident, record in zip(wanted, data["records"]):
        assert record["planned_id"] == ident and record["exit_code"] == 0
        assert record["stderr"] == ""
        x = record["preflight"]
        assert x["planned_id"] == ident and x["status"] == "PREFLIGHT_ONLY_NOT_SOLVE_PERMISSION"
        assert x["formal_run_id"] is None and x["prediction_permission"] == "HOLD"
        assert x["NUMERICAL_GATE"] == "NOT_EVALUATED" and x["RESULT_PASS"] is False
        assert x["geometry_PASS"] is None
        assert x["solver_object_created"] is False and x["solver_called"] is False
        assert x["physical_field_generated"] is False and x["prior_assembly_hashes_match"]
        assert x["matrix_csr_sha256"] == old[ident]["matrix_csr_sha256"]
        assert x["rhs_sha256_before_projection"] == old[ident]["rhs_sha256_before_projection"]
        assert x["mesh_sha256"] == old[ident]["mesh_sha256"]
        assert x["periodic_mapping_sha256"] == old[ident]["periodic_mapping_sha256"]
        support, gauge = x["pressure_support"], x["gauge_check"]
        assert support["pressure_slave_dofs_removed"] == old[ident]["pressure_slave_dofs"]
        assert support["algebraic_nonzero_dofs"] + support["pressure_slave_dofs_removed"] == support["physical_pressure_dofs"]
        assert support["algebraic_slave_entries_zero"] and support["algebraic_velocity_entries_zero"]
        assert gauge["petsc_nullspace_test"] and gauge["right_and_transpose_nullspaces_attached"]
        assert gauge["rhs_compatibility_relative_before_projection"] <= 1e-10
        assert gauge["rhs_projection_change_L2"] <= 1e-10
        assert math.isfinite(gauge["right_kernel_relative"] + gauge["left_kernel_relative"])
        assert gauge["right_kernel_relative"] <= 1e-10 and gauge["left_kernel_relative"] <= 1e-10
        assert x["pressure_backsubstitution_max_error"] <= 1e-12
        max_right = max(max_right, gauge["right_kernel_relative"])
        max_left = max(max_left, gauge["left_kernel_relative"])
        max_backsub = max(max_backsub, x["pressure_backsubstitution_max_error"])
    negative = json.loads((HERE / "evidence/negative_controls.json").read_text())
    assert negative["status"] == "PASS" and negative["negative_controls_passed"] == 6
    assert negative["solver_called"] is False
    protected = json.loads((REPO / "docs/reports/G4_derivation_source_audit_20261025/"
                            "protected_inputs.json").read_text())
    altered = [p for p, expected in protected.items() if not Path(p).is_file() or sha256(p) != expected]
    prior = ROOT / "mesh_periodic_pressure_20261025"
    prior_hashes = json.loads((prior / "evidence/artifact_hashes.json").read_text())
    prior_altered = [p for p, expected in prior_hashes.items()
                     if not (prior / p).is_file() or sha256(prior / p) != expected]
    verdict = {"status": "PASS" if not altered and not prior_altered else "FAIL",
               "nine_preflights_checked": 9, "max_right_kernel_relative": max_right,
               "max_left_kernel_relative": max_left,
               "max_pressure_backsubstitution_error": max_backsub,
               "negative_controls_passed": 6,
               "protected_paths_checked": len(protected), "protected_altered": altered,
               "prior_interface_files_checked": len(prior_hashes),
               "prior_interface_altered": prior_altered,
               "solver_called": False, "numerical_gate": "NOT_EVALUATED"}
    (HERE / "evidence/independent_review.json").write_text(json.dumps(
        verdict, indent=2, ensure_ascii=False) + "\n")
    if verdict["status"] != "PASS":
        raise RuntimeError("PREFLIGHT_RECORD_REVIEW_FAILED")
    return verdict


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False))
