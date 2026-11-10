"""Read-only source/evidence audit. Stdlib only; never import project modules."""
import ast
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BACKEND = REPO / "CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    protected_file = REPO / "docs/reports/G4_derivation_source_audit_20261025/protected_inputs.json"
    protected = json.loads(protected_file.read_text())
    changed = [p for p, expected in protected.items()
               if not Path(p).is_file() or sha(p) != expected]
    execution = BACKEND / "execution_record_review_20261026"
    previous = json.loads((execution / "evidence/independent_review.json").read_text())
    reviewed_changed = [p for p, expected in previous["source_sha256"].items()
                        if sha(execution / p) != expected]
    rows = list(csv.DictReader((BACKEND / "protocol/benchmarks18.csv").open(encoding="utf-8-sig")))
    assert len(rows) == 18 and all(r["authorized_to_execute"] == "False" for r in rows)
    assert all(not r["actual_run_id"] for r in rows)
    # These checks anchor the manual control-flow review, not execute its paths.
    contract = (BACKEND / "src/contract.py").read_text()
    worker = (execution / "reviewed_worker.py").read_text()
    child = (execution / "child_record.py").read_text()
    assert 'r["authorized_to_execute"] != "False"' in contract
    assert '"execution_authorized": False' in contract
    assert 'selected[0]["authorized_to_execute"] != "True"' in worker
    assert 'plans[0]["authorized_to_execute"] != "True"' in child
    assert 'system = entry.prepare_bound_mixed_system(planned_id)' in worker
    solver_tree = ast.parse((execution / "recorded_solver.py").read_text())
    solves = [n.lineno for n in ast.walk(solver_tree) if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Attribute) and n.func.attr == "solve"]
    assert len(solves) == 1
    raw_tree = ast.parse((BACKEND / "raw_capture_review_20261025/raw_writer.py").read_text())
    required = next(n.value for n in raw_tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "REQUIRED" for t in n.targets))
    raw_keys = sorted(ast.literal_eval(required))
    assert len(raw_keys) == 16
    bridge = json.loads((BACKEND / "result_adapter_review_20261026/evidence/bridge_audit.json").read_text())
    assert bridge["solver_called"] is False
    pilot_cases = [r for r in bridge["cases"] if r["planned_id"] in
                   {"B0MIN_MMS_mixed_N8", "B0MIN_FLAT_T_d5"}]
    files = {protected_file, REPO / "AGENTS.md"}
    for directory in ("src", "protocol", "environment", "mesh_periodic_pressure_20261025",
                      "pressure_assembly_audit_20261025", "solve_entry_review_20261025",
                      "solver_result_review_20261025", "raw_capture_review_20261025",
                      "result_adapter_review_20261026", "execution_record_review_20261026"):
        files.update(p for p in (BACKEND / directory).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts)
    for directory in ("D4_reference_protocol_draft_20261025", "D4_reference_protocol_review_20261025"):
        files.update(p for p in (REPO / "docs/reports" / directory).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts)
    inputs = {str(p.relative_to(REPO)): sha(p) for p in sorted(files)}
    binding = HERE / "review_inputs_sha256.json"
    if binding.exists():
        assert json.loads(binding.read_text()) == inputs, "REVIEW_INPUTS_CHANGED"
    else:
        binding.write_text(json.dumps(inputs, indent=2, ensure_ascii=False) + "\n")
    report = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "status": "STATIC_REVIEW_EVIDENCE_CONSISTENT" if not changed and not reviewed_changed else "FAIL",
        "review_verdict": "HOLD_NO_RUN_PERMISSION",
        "protected_paths_checked": len(protected), "protected_changed": changed,
        "execution_source_hashes_checked": len(previous["source_sha256"]),
        "execution_source_changed": reviewed_changed,
        "review_inputs_bound": len(inputs),
        "frozen_csv_false_rows": len(rows),
        "new_runtime_denial_tests": 0,
        "new_synthetic_process_tests": 0,
        "new_backend_imports_meshes_assemblies_solves": 0,
        "incompatible_execution_flags_confirmed_by_source": True,
        "dormant_solve_source_lines": solves,
        "current_raw_array_keys": raw_keys,
        "historical_pilot_mesh_records_not_new_runs": pilot_cases,
        "formal_run_id": None, "NUMERICAL_GATE": "NOT_EVALUATED",
        "RESULT_PASS": False, "geometry_PASS": None, "prediction_permission": "HOLD"
    }
    (HERE / "static_evidence.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in
                     {"current_raw_array_keys", "historical_pilot_mesh_records_not_new_runs"}}, ensure_ascii=False))
    assert not changed and not reviewed_changed


if __name__ == "__main__":
    main()
