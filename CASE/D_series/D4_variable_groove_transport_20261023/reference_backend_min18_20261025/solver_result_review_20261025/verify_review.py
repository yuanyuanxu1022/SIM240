"""Backend-free independent verification of the unexecuted solver review."""

import ast
import csv
import hashlib
import json
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


def verify():
    evidence = json.loads((HERE / "evidence/static_review.json").read_text())
    assert evidence["status"] == "STATIC_REVIEW_PASS_NOT_SOLVE_PERMISSION"
    assert evidence["solver_object_created"] is False and evidence["solver_called"] is False
    assert evidence["formal_run_id"] is None and evidence["NUMERICAL_GATE"] == "NOT_EVALUATED"
    assert evidence["RESULT_PASS"] is False and evidence["geometry_PASS"] is None
    for relative, expected in evidence["source_sha256"].items():
        assert sha256(ROOT / relative) == expected, relative
    rows = list(csv.DictReader((ROOT / "protocol/benchmarks18.csv").open(
        encoding="utf-8-sig", newline="")))
    mixed = [r["planned_id"] for r in rows if r["direction_or_field"] in {"T", "mixed"}]
    assert len(mixed) == 9 and all(r["authorized_to_execute"] == "False" for r in rows)
    align = evidence["pressure_dof_alignment"]
    assert [r["planned_id"] for r in align] == mixed
    assert all(r["original_vs_MPC_pressure_coord_max_difference"] == 0
               and r["frozen_plan_denies_solve"] for r in align)
    assert evidence["frozen_plan_rejections"] == 9
    assert evidence["synthetic_release_guard_checked_without_KSP"] is True
    assert all(evidence["petsc_api_present_without_KSP_instantiation"].values())
    contract = json.loads((HERE / "record_contract.json").read_text())
    assert contract["status"] == "DRAFT_NOT_APPROVED_NOT_A_RESULT"
    assert contract["current_values"]["formal_run_id"] is None
    assert contract["current_values"]["solver_exit_code"] is None
    assert contract["current_values"]["NUMERICAL_GATE"] == "NOT_EVALUATED"
    assert len(contract["required_before_solve"]) >= 10
    assert len(contract["required_after_solve"]) >= 15
    assert len(contract["required_on_failure"]) >= 5

    tree = ast.parse((HERE / "candidate_solver.py").read_text())
    names = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    callable_node = names["solve_prepared_mixed_system"]
    body = [node for node in callable_node.body if not isinstance(node, ast.Expr)
            or not isinstance(node.value, ast.Constant)]
    assert isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Call)
    assert isinstance(body[0].value.func, ast.Name)
    assert body[0].value.func.id == "check_release"
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == "solve"]
    assert len(calls) == 1
    assert any(node is calls[0] for node in ast.walk(callable_node))
    assert all(not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "solve") for node in tree.body)
    ast.parse((HERE / "audit_static.py").read_text())

    protected = json.loads((REPO / "docs/reports/G4_derivation_source_audit_20261025/"
                            "protected_inputs.json").read_text())
    altered = [p for p, expected in protected.items() if not Path(p).is_file() or sha256(p) != expected]
    prior = ROOT / "mesh_periodic_pressure_20261025"
    prior_hashes = json.loads((prior / "evidence/artifact_hashes.json").read_text())
    prior_altered = [p for p, expected in prior_hashes.items()
                     if not (prior / p).is_file() or sha256(prior / p) != expected]
    verdict = {"status": "PASS" if not altered and not prior_altered else "FAIL",
               "pressure_mapping_cases": 9, "frozen_whitelist_rejections": 9,
               "one_gated_dormant_solve_call": True,
               "record_plan_before_fields": len(contract["required_before_solve"]),
               "record_plan_after_fields": len(contract["required_after_solve"]),
               "record_plan_failure_fields": len(contract["required_on_failure"]),
               "protected_paths_checked": len(protected), "protected_altered": altered,
               "prior_interface_files_checked": len(prior_hashes),
               "prior_interface_altered": prior_altered,
               "solver_called": False, "run_permission": "HOLD"}
    (HERE / "evidence/independent_review.json").write_text(json.dumps(
        verdict, indent=2, ensure_ascii=False) + "\n")
    if verdict["status"] != "PASS":
        raise RuntimeError("INDEPENDENT_STATIC_REVIEW_FAILED")
    return verdict


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False))
