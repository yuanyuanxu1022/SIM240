#!/usr/bin/env python3
"""Read-only integrity/static evidence audit; writes its report, never solves."""
import datetime
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from contract import REPO, bound_inputs, load_plan, sha256
from records import future_record_template


def audit():
    def read(p):
        return json.loads(p.read_text())
    checks = {}
    protected = read(ROOT / "evidence/protected_inputs.json")
    changed = [p for p,h in protected.items() if not Path(p).is_file() or sha256(p) != h]
    checks["protected_files_unchanged"] = not changed
    base_before = read(ROOT / "evidence/base_environment_before.json")
    base_now = {str(p):sha256(p) for p in Path("/home/dell/miniconda3/conda-meta").iterdir() if p.is_file()}
    checks["base_package_metadata_and_history_unchanged"] = base_now == base_before
    plans = load_plan()
    checks["whitelist_18_no_run_or_execution"] = len(plans)==18 and all(p["actual_run_id"] is None and not p["execution_authorized"] for p in plans.values())
    probe = read(ROOT / "evidence/backend_probe.json")
    checks["backend_import_check_ok"] = probe["ok"] and probe["PETSc_real_float64"] and probe["MPI_size"]==1
    module_files = [(e["path"],e["file_sha256"]) for e in probe["modules"].values()]
    module_files += [(e["path"],e["sha256"]) for e in probe["extension_binaries"].values()]
    checks["backend_probed_module_and_extension_hashes_match"] = all(sha256(p)==h for p,h in module_files)
    checks["actual_loaded_core_libraries_bound"] = all(sha256(p)==h for p,h in probe["actual_loaded_core_shared_libraries"].items())
    lock = read(ROOT / "environment/backend.lock.json")
    checks["dependency_exports_bound"] = (
        sha256(ROOT / "environment/conda-linux-64.explicit.txt")==lock["explicit_export_sha256"]
        and sha256(ROOT / "environment/package_metadata.json")==lock["package_metadata_sha256"])
    metadata = read(ROOT / "environment/package_metadata.json")
    installed = [read(p) for p in (ROOT/".backend/conda-meta").glob("*.json")]
    checks["dependency_inventory_matches_installation"] = sorted((p["name"],p["version"],p["build"]) for p in metadata)==sorted((p["name"],p["version"],p["build"]) for p in installed)
    linkage = read(ROOT / "evidence/backend_linkage.json")
    checks["no_missing_linkage_in_ldd_snapshot"] = all(e["exit_code"]==0 and "not found" not in e["output"] for e in linkage.values())
    for label in ("static_tests", "symbolic_ufl_check"):
        checks[label+"_exit_zero"] = read(ROOT/"evidence"/(label+"_record.json"))["exit_code"]==0
    symbolic = read(ROOT / "evidence/symbolic_ufl_check.stdout.txt")
    checks["symbolic_only_no_computational_mesh_assembly_or_solve"] = symbolic["ok"] and not any(symbolic[k] for k in ("computational_mesh_created","matrix_assembled","JIT_called","solver_called"))
    current = read(ROOT/"evidence/current_preparation.json")["prep_id"]
    stage = ROOT / "prepared_records" / current
    preparation = read(stage/"PREPARATION.json")
    checks["record_preparation_inputs_unchanged"] = preparation["inputs_before"]==preparation["inputs_after"]==bound_inputs()
    checks["record_preparation_only"] = preparation["kind"]=="PREPARATION_ONLY" and preparation["preparation_complete"] and not preparation["solver_called"] and preparation["actual_run_id"] is None
    items = [p for p in stage.iterdir() if p.is_dir()]
    checks["18_static_input_template_pairs"] = len(items)==18 and {p.name for p in items}==set(plans)
    checks["all_records_are_empty_templates"] = all(read(item/"input.json")==plans[item.name] and read(item/"future_record_template.json")==future_record_template(plans[item.name]) for item in items)
    checks["no_actual_solver_output_in_prepared_records"] = not any(p.suffix.lower() in {"vtu","vti","vtm","pvd","xdmf","h5"} or p.name in {"result.json","result.txt","completion.json"} for p in (ROOT/"prepared_records").rglob("*") if p.is_file())
    state_sync_path = ROOT/"evidence/state_sync.json"
    if state_sync_path.is_file():
        sync = read(state_sync_path)
        checks["state_entries_match_recorded_changes"] = all(sha256(REPO/"docs/reports"/n)==v["after_sha256"] and v["other_sections_unchanged"] for n,v in sync.items())
    return {"kind":"STATIC_PREPARATION_AUDIT_NOT_NUMERICAL_ACCEPTANCE",
            "verified_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "ok":all(checks.values()), "checks":checks,
            "protected_paths":len(protected),"changed_protected_paths":changed,
            "base_metadata_files":len(base_before),"installed_backend_packages":len(installed),
            "planned_problems":len(plans),"actual_solver_runs":0,
            "actual_run_id":None,"execution_authorized":False,
            "NUMERICAL_GATE":"NOT_EVALUATED","RESULT_PASS":False,
            "geometry_PASS":None,"budget_validated":False,
            "old_grid_FAIL_and_G4_preserved":not changed,
            "pending_implementation":["actual computational meshes and boundary tags",
                                      "MPC elimination on real P2/P1 spaces",
                                      "one pressure nullspace and rhs compatibility tests",
                                      "matrix assembly, solver and raw field/functional output",
                                      "actual run-record schema and independent numerical acceptance"],
            "prediction_permission":"HOLD"}


if __name__=="__main__":
    result=audit()
    (ROOT/"evidence/verification.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    sys.exit(0 if result["ok"] else 1)
