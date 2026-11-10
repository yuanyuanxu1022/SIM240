"""Independent source/evidence check; standard library only, no backend import."""
import ast
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = ROOT.parents[3]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def main():
    audit = json.loads((HERE / "evidence/bridge_audit.json").read_text())
    decision = json.loads((HERE / "review_decision.json").read_text())
    assert audit["status"] == "PASS_REAL_MESH_SYNTHETIC_FIELD_ONLY"
    assert len(audit["cases"]) == 9 and all(x["raw_files_readback"] == 16 for x in audit["cases"])
    assert audit["ksp_created"] is False and audit["solver_called"] is False
    for rel, expected in audit["source_sha256"].items():
        assert sha(ROOT / rel) == expected, rel
    tests = json.loads((ROOT / "raw_capture_review_20261025/evidence/synthetic_checks.json").read_text())
    assert tests["status"] == "PASS_SYNTHETIC_ONLY"
    assert "16_RAW_ARRAYS_EXACT_READBACK_AND_HASH" in tests["checks"]
    assert decision["execution_authorized"] is False
    assert decision["candidate_solver_convergence"] == "NOT_TESTED"
    rows = list(csv.DictReader((ROOT / "protocol/benchmarks18.csv").open(
        encoding="utf-8-sig", newline="")))
    assert len(rows) == 18 and all(row["authorized_to_execute"] == "False" for row in rows)
    for name in ("bridge.py", "audit_no_solve.py"):
        tree = ast.parse((HERE / name).read_text())
        assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                       and n.func.attr == "solve" for n in ast.walk(tree))
    candidate = (ROOT / "solver_result_review_20261025/candidate_solver.py").read_text()
    assert "ksp.getConvergedReason()" in candidate
    assert "A.mult(algebraic_x, residual)" in candidate
    assert "if reason <= 0" in candidate
    assert "raise CandidateSolveFailure(diagnostics)" in candidate
    assert "ksp.getPC().setType(PETSc.PC.Type.NONE)" in candidate
    capture = (ROOT / "raw_capture_review_20261025/process_capture.py").read_text()
    assert "REAL_PROCESS_ADAPTER_NOT_IMPLEMENTED" in capture
    protected = json.loads((REPO / "docs/reports/G4_derivation_source_audit_20261025/"
                            "protected_inputs.json").read_text())
    changed = [p for p, expected in protected.items() if not Path(p).is_file() or sha(p) != expected]
    verdict = {"status": "PASS_REVIEW_ONLY" if not changed else "FAIL",
               "actual_geometry_synthetic_field_cases": len(audit["cases"]),
               "raw_arrays_readback_per_case": 16,
               "protected_paths_checked": len(protected), "protected_changed": changed,
               "candidate_solve_called": False, "formal_run_id": None,
               "resource_budget_validated": False,
               "NUMERICAL_GATE": "NOT_EVALUATED", "RESULT_PASS": False,
               "geometry_PASS": None, "prediction_permission": "HOLD"}
    (HERE / "evidence/independent_review.json").write_text(
        json.dumps(verdict, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(verdict, ensure_ascii=False))
    if changed:
        raise RuntimeError("PROTECTED_INPUTS_CHANGED")


if __name__ == "__main__":
    main()
