"""Independent stdlib review of preparation evidence and protected inputs."""
import ast
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
    synthetic = json.loads((HERE / "evidence/synthetic_checks.json").read_text())
    resource = json.loads((HERE / "evidence/resource_review.json").read_text())
    assert synthetic["status"] == "PASS_SYNTHETIC_ONLY"
    assert synthetic["solver_called"] is False
    assert resource["solver_called"] is False and resource["exit_code"] == 0
    assert resource["proposal_validation"] == "NOT_VALIDATED_BY_ASSEMBLY_ONLY"
    preflight = json.loads((HERE / "evidence/assembly_only_stdout.json").read_text())
    assert preflight["solver_called"] is False
    assert preflight["matrix_csr_sha256"] == resource["matrix_csr_sha256"]
    assert preflight["rhs_sha256_before_projection"] == resource["rhs_sha256_before_projection"]
    assert resource["input_sha256_before"] == resource["input_sha256_after"]
    for rel, expected in resource["input_sha256_before"].items():
        assert sha(ROOT / rel) == expected, rel
    assert "PEAK_RSS_KiB=" in (HERE / "evidence/assembly_only_stderr.log").read_text()
    for name in ("raw_writer.py", "process_capture.py"):
        tree = ast.parse((HERE / name).read_text())
        assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                       and node.func.attr == "solve" for node in ast.walk(tree))
    # Current frozen benchmark whitelist still denies execution.
    rows = (ROOT / "protocol/benchmarks18.csv").read_text(encoding="utf-8-sig")
    assert rows.count(",False") == 18
    protected = json.loads((REPO / "docs/reports/G4_derivation_source_audit_20261025/"
                            "protected_inputs.json").read_text())
    changed = [p for p, expected in protected.items() if not Path(p).is_file() or sha(p) != expected]
    previous = ROOT / "solver_result_review_20261025/evidence/independent_review.json"
    old_review = json.loads(previous.read_text())
    assert old_review["status"] == "PASS"
    verdict = {"status": "PASS_PREPARATION_ONLY" if not changed else "FAIL",
               "synthetic_checks": synthetic["checks"],
               "assembly_only_peak_RSS_KiB": resource["assembly_preflight_peak_RSS_KiB"],
               "protected_paths_checked": len(protected), "protected_changed": changed,
               "previous_review_status": old_review["status"],
               "real_solver_capture_adapter": "NOT_IMPLEMENTED",
               "raw_solver_adapter": "NOT_IMPLEMENTED",
               "solver_called": False, "formal_run_id": None,
               "NUMERICAL_GATE": "NOT_EVALUATED", "RESULT_PASS": False,
               "geometry_PASS": None, "prediction_permission": "HOLD"}
    (HERE / "evidence/independent_preparation_review.json").write_text(
        json.dumps(verdict, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(verdict, indent=2, ensure_ascii=False))
    if changed:
        raise RuntimeError("PROTECTED_INPUT_CHANGED")


if __name__ == "__main__":
    main()
