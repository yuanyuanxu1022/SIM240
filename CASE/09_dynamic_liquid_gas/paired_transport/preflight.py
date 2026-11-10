"""Read-only preparation audit. Never imports or invokes an OpenLB executable.

Exit 0: required preparation evidence present, not a numerical PASS or run approval.
Exit 2: preparation incomplete. Exit 3: invalid configuration / inconsistent pair.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def angle(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 < value < 180


def material_issues(material):
    missing = []
    properties = {
        "liquid_density": "kg/m3", "liquid_dynamic_viscosity": "Pa.s",
        "liquid_gas_surface_tension": "N/m", "gas_density": "kg/m3",
        "gas_dynamic_viscosity": "Pa.s", "ambient_pressure": "Pa",
    }
    for name, unit in properties.items():
        item = material.get(name, {})
        if (not positive(item.get("value")) or item.get("unit") != unit
                or item.get("status") != "verified" or not item.get("source")):
            missing.append(f"material.{name}: finite positive SI value and verified source required")
    for name in ("substrate", "mold"):
        surface = material.get(name, {})
        item = surface.get("contact_angle_through_liquid", {})
        if not surface.get("material") or surface.get("coating_or_treatment") is None:
            missing.append(f"material.{name}: material and actual surface treatment unknown")
        if (not angle(item.get("value")) or item.get("unit") != "degree"
                or item.get("status") != "verified" or not item.get("source")):
            missing.append(f"material.{name}.contact_angle: verified liquid-side angle required")
    if not material.get("constant_viscosity_model_accepted", False):
        missing.append("material.constant_viscosity_model: 12mPa.s remains a candidate")
    if not material.get("specimen_batch_matching_verified", False):
        missing.append("material.specimen_batch_matching: link property tests to the GHY specimen")
    if not material.get("formal_GHY_material_ready", False):
        missing.append("material.formal_GHY_material_ready: complete material record not established")
    return missing


def pair_issues(shared, xcase, ycase):
    errors = []
    expected_keys = {"case_id", "shared_configuration", "drive_axis", "drive_unit_vector",
                     "primary_response_component", "reported_coefficient"}
    for case, axis, vector, coefficient in (
        (xcase, "x", [1, 0, 0], "Kxx"), (ycase, "y", [0, 1, 0], "Kyy")
    ):
        if set(case) != expected_keys:
            errors.append(f"{coefficient}: unrecognized per-case override; shared physics must stay common")
        if (case.get("drive_axis") != axis or case.get("drive_unit_vector") != vector
                or case.get("primary_response_component") != axis
                or case.get("reported_coefficient") != coefficient):
            errors.append(f"{coefficient}: axis/response/coefficient mapping inconsistent")
        if case.get("shared_configuration") != "../shared_case.json":
            errors.append(f"{coefficient}: must reference the same shared configuration")
    if xcase.get("case_id") == ycase.get("case_id"):
        errors.append("x/y case ids must differ")
    if shared.get("coordinate_convention") != {
        "x": "across_grooves", "y": "along_grooves", "z": "gap_normal"
    }:
        errors.append("shared axis convention inconsistent with project Kxx/Kyy")
    return errors


def mapping_issues(shared, material):
    n = shared.get("numerics", {})
    if not all(positive(n.get(k)) for k in ("dx_m", "dt_s", "tau_liquid", "tau_gas", "surface_tension_lattice")):
        return ["numerics: physical/lattice mapping incomplete"]
    required = ["liquid_density", "liquid_dynamic_viscosity", "gas_density", "gas_dynamic_viscosity", "liquid_gas_surface_tension"]
    if not all(positive(material.get(k, {}).get("value")) for k in required):
        return ["numerics: cannot check mapping before physical properties are known"]
    dx, dt = n["dx_m"], n["dt_s"]
    rho_l = material["liquid_density"]["value"]
    expected = {
        "tau_liquid": 0.5 + 3 * material["liquid_dynamic_viscosity"]["value"] / rho_l * dt / dx**2,
        "tau_gas": 0.5 + 3 * material["gas_dynamic_viscosity"]["value"] / material["gas_density"]["value"] * dt / dx**2,
        "surface_tension_lattice": material["liquid_gas_surface_tension"]["value"] * dt**2 / (rho_l * dx**3),
    }
    return [f"numerics.{k}: mismatch to declared BGK mapping (liquid reference density)"
            for k, value in expected.items() if not math.isclose(n[k], value, rel_tol=1e-6, abs_tol=0)]


def audit(root):
    def read(path):
        return json.loads(path.read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    shared = read(root / "shared_case.json")
    xcase, ycase = read(root / "Kxx/case.json"), read(root / "Kyy/case.json")
    material = read(root / shared["material_profile"])
    invalid = pair_issues(shared, xcase, ycase)
    missing = material_issues(material) + mapping_issues(shared, material)
    p, initial, measurement = shared["physics"], shared["initial_state"], shared["measurement"]
    water_record = material.get("process_water", {})
    if (p.get("water_presence_during_flow") != "absent_verified"
            or water_record.get("water_present_during_transport") is not False
            or water_record.get("status") != "verified"):
        missing.append("physics.water_presence: water-assisted demolding timing unknown; two-fluid scope unresolved")
    if not positive(p.get("drive_gradient_magnitude_Pa_per_m")):
        missing.append("physics.drive: shared gradient magnitude not defined")
    if p.get("drive_signs") != [-1, 1] or not p.get("shared_zero_drive_baseline_required"):
        invalid.append("physics: require paired signs and a shared zero-drive baseline")
    if not p.get("body_force_implementation_verified"):
        missing.append("physics.drive: backend force convention not verified")
    checkpoint = initial.get("shared_checkpoint")
    if not checkpoint or not initial.get("checkpoint_and_loading_history_verified"):
        missing.append("initial_state: no verified common checkpoint and loading history")
    elif not (root / checkpoint).is_file():
        missing.append("initial_state: referenced checkpoint missing")
    else:
        digest = hashlib.sha256((root / checkpoint).read_bytes()).hexdigest()
        if digest != initial.get("checkpoint_sha256"):
            invalid.append("initial_state: checkpoint hash mismatch")
    start, end = measurement.get("window_start_s"), measurement.get("window_end_s")
    if (type(start) not in (int, float) or not math.isfinite(start) or start < 0
            or not positive(end) or start >= end):
        missing.append("measurement.window: no finite physical sampling window")
    if not measurement.get("timescale_separation_verified") or not measurement.get("measurement_definition_frozen"):
        missing.append("measurement: response window/definition not verified and frozen")
    for flag in ("protocol_frozen", "prerequisites_verified"):
        if not shared["validation"].get(flag):
            missing.append(f"validation.{flag}: not established")
    if not shared["numerics"].get("mapping_verified"):
        missing.append("numerics.mapping_verified: not established")
    backend = shared["backend"]
    if not backend.get("compiled_and_bound_to_manifest") or not backend.get("source_manifest"):
        missing.append("backend: no implemented/compiled solver bound to a source manifest")
    elif not (root / backend["source_manifest"]).is_file():
        missing.append("backend.source_manifest: referenced file missing")
    binary = backend.get("executable")
    if not binary or not (root / binary).is_file():
        missing.append("backend.executable: missing")
    elif hashlib.sha256((root / binary).read_bytes()).hexdigest() != backend.get("sha256"):
        invalid.append("backend.executable: hash mismatch")
    return {
        "pair_structure_consistent": not invalid,
        "preparation_complete": not invalid and not missing,
        "invalid_configuration": invalid,
        "missing_preparation_evidence": missing,
        "shared_config_sha256": hashlib.sha256((root / "shared_case.json").read_bytes()).hexdigest(),
        "NUMERICAL_GATE": "NOT_EVALUATED", "RESULT_PASS": "NOT_EVALUATED", "geometry_PASS": "NOT_EVALUATED",
        "simulation_started": False,
        "scope": "configuration audit only; no solver run or numerical validation",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, help="Optional preparation report path; no simulation output is created")
    options = parser.parse_args()
    try:
        result = audit(Path(__file__).resolve().parent)
    except (KeyError, TypeError, ValueError, OSError) as exc:
        result = {"invalid_configuration": [str(exc)], "preparation_complete": False, "simulation_started": False}
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if options.report:
        options.report.write_text(rendered)
    print(rendered, end="")
    raise SystemExit(3 if result.get("invalid_configuration") else 0 if result["preparation_complete"] else 2)
