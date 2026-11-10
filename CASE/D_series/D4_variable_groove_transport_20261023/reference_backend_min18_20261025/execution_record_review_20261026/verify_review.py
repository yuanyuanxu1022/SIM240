"""Independent stdlib-only source and evidence audit; never imports backend."""
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


def function(tree, name):
    return next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == name)


def main():
    tests = json.loads((HERE / "evidence/synthetic_tests.json").read_text())
    assert tests["status"] == "PASS_SYNTHETIC_AND_DENIAL_ONLY"
    assert tests["real_solver_called"] is False and tests["formal_run_id"] is None
    rows = list(csv.DictReader((ROOT / "protocol/benchmarks18.csv").open(
        encoding="utf-8-sig", newline="")))
    assert len(rows) == 18 and all(x["authorized_to_execute"] == "False" for x in rows)
    solver = ast.parse((HERE / "recorded_solver.py").read_text())
    calls = [n for n in ast.walk(solver) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == "solve"]
    assert len(calls) == 1
    solve_func = function(solver, "solve_prepared_mixed_system")
    assert calls[0] in ast.walk(solve_func)
    first_call = next(n for n in solve_func.body if isinstance(n, ast.Expr)
                      and isinstance(n.value, ast.Call))
    assert isinstance(first_call.value.func, ast.Name)
    assert first_call.value.func.id == "check_release"
    solver_source = (HERE / "recorded_solver.py").read_text()
    assert "algebraic_x if algebraic_x is not None else x" in solver_source
    assert "failure_sink(stage, exc, snapshot, failure_details, binding)" in solver_source
    child = ast.parse((HERE / "child_record.py").read_text())
    capture = function(child, "capture_reviewed_case")
    first = (capture.body[1] if isinstance(capture.body[0], ast.Expr)
             and isinstance(capture.body[0].value, ast.Constant) else capture.body[0])
    assert isinstance(first, ast.Expr) and isinstance(first.value, ast.Call)
    assert isinstance(first.value.func, ast.Name) and first.value.func.id == "check_real_release"
    worker = ast.parse((HERE / "reviewed_worker.py").read_text())
    run = function(worker, "run_one")
    assert isinstance(run.body[0], ast.Expr) and isinstance(run.body[0].value, ast.Call)
    assert isinstance(run.body[0].value.func, ast.Name)
    assert run.body[0].value.func.id == "check_frozen_gate"
    prior = json.loads((ROOT / "result_adapter_review_20261026/evidence/independent_review.json").read_text())
    assert prior["status"] == "PASS_REVIEW_ONLY"
    protected = json.loads((REPO / "docs/reports/G4_derivation_source_audit_20261025/"
                            "protected_inputs.json").read_text())
    changed = [p for p, expected in protected.items() if not Path(p).is_file() or sha(p) != expected]
    files = [p for p in HERE.glob("*.py")]
    source_hashes = {p.name: sha(p) for p in files}
    verdict = {"status": "PASS_PREPARATION_ONLY" if not changed else "FAIL",
               "source_sha256": source_hashes,
               "protected_paths_checked": len(protected), "protected_changed": changed,
               "frozen_plan_denials": len(rows), "dormant_gated_KSP_solve_calls": len(calls),
               "synthetic_checks": tests["checks"],
               "real_KSP_created": False, "real_PDE_solve_called": False,
               "formal_run_id": None, "NUMERICAL_GATE": "NOT_EVALUATED",
               "RESULT_PASS": False, "geometry_PASS": None,
               "prediction_permission": "HOLD"}
    (HERE / "evidence/independent_review.json").write_text(
        json.dumps(verdict, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in verdict.items() if k != "source_sha256"},
                     ensure_ascii=False))
    if changed:
        raise RuntimeError("PROTECTED_SOURCE_CHANGED")


if __name__ == "__main__":
    main()
