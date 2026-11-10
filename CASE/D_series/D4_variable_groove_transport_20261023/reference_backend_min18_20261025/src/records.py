"""Preparation records and an explicitly incomplete future record template."""
import datetime
import json
import re
from pathlib import Path

from contract import ROOT, Rejected, bound_inputs, select


def future_record_template(plan):
    mixed = plan["field"] in {"T", "mixed"}
    return {"record_kind": "TEMPLATE_NOT_A_RESULT", "planned_id": plan["planned_id"],
            "actual_run_id": None, "execution_authorized": False,
            "source_dependency_and_input_hashes": None,
            "input_hashes_before_after": None,
            "independent_solver_exit_code": None, "complete_log_path": None,
            "raw_mesh_field_integral_and_periodic_map_hashes": None,
            "measurements": {"J_hat": None, "J_m2_s": None, "K_m3": None,
                             "R_Pa_s_m3": None, "true_unpreconditioned_relative_residual": None,
                             "velocity_L2_error": None, "pressure_L2_error": None,
                             "pressure_gauge_nullspace_rhs_checks": None,
                             "periodic_trace_errors": None, "area_and_boundary_audit": None,
                             "divergence_and_section_flux": None, "energy_balance": None,
                             "wall_time_seconds": None, "peak_RSS_KiB": None},
            "applicability": {"physical_K_J_R": plan["problem"] == "flat75",
                              "pressure_divergence": mixed,
                              "MMS_forcing_work_not_uniform_acceleration": plan["problem"] == "MMS"},
            "NUMERICAL_GATE": "NOT_EVALUATED", "RESULT_PASS": False,
            "geometry_PASS": None, "REFERENCE_DISCRETIZATION": "NOT_EVALUATED",
            "STOKES_MODEL_GAP": "NOT_EVALUATED", "LBM_STOP_COMPARISON": "NOT_EVALUATED"}


def stage(plans, prep_id, parent=None):
    if not plans or len({p["planned_id"] for p in plans}) != len(plans):
        raise Rejected("EMPTY_OR_DUPLICATE_SELECTION")
    for plan in plans:
        select(supplied=plan)
    if not isinstance(prep_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", prep_id):
        raise Rejected("INVALID_PREPARATION_ID")
    # Only a new direct child of this package's prepared_records is permitted.
    allowed = ROOT / "prepared_records"
    parent = Path(parent) if parent is not None else allowed
    if parent.is_symlink() or parent.absolute() != allowed.absolute():
        raise Rejected("OUTPUT_OUTSIDE_PREPARATION_ROOT")
    if allowed.exists() and not allowed.is_dir():
        raise Rejected("OUTPUT_PARENT_NOT_DIRECTORY")
    destination = allowed / prep_id
    if destination.exists() or destination.is_symlink():
        raise Rejected("OUTPUT_ALREADY_EXISTS")
    before = bound_inputs()
    allowed.mkdir(exist_ok=True)
    destination.mkdir(exist_ok=False)
    status = {"kind": "PREPARATION_ONLY", "prep_id": prep_id,
              "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "problem_count": len(plans), "planned_ids": [p["planned_id"] for p in plans],
              "actual_run_id": None, "execution_authorized": False,
              "solver_called": False, "numerical_acceptance": "NOT_EVALUATED",
              "inputs_before": before, "preparation_complete": False}
    def write(name, value):
        with (destination / name).open("x") as f:
            json.dump(value, f, indent=2, allow_nan=False)
            f.write("\n")
    try:
        for plan in plans:
            item = destination / plan["planned_id"]
            item.mkdir()
            (item / "input.json").write_text(json.dumps(plan, indent=2, allow_nan=False) + "\n")
            (item / "future_record_template.json").write_text(json.dumps(future_record_template(plan), indent=2) + "\n")
        status["inputs_after"] = bound_inputs()
        if before != status["inputs_after"]:
            raise Rejected("INPUTS_CHANGED_DURING_PREPARATION")
        status["preparation_complete"] = True
        write("PREPARATION.json", status)
        write("events.json", [{"event": "STATIC_RECORDS_PREPARED", "solver_called": False}])
        (destination / "preparation_exit_code.txt").write_text("0\n")
    except Exception as exc:
        (destination / "preparation_failure.json").write_text(json.dumps({"error": str(exc), "solver_called": False}) + "\n")
        (destination / "preparation_exit_code.txt").write_text("1\n")
        raise
    return destination, status
