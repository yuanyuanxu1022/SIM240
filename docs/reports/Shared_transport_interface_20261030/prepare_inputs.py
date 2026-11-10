"""Prepare shared inputs and check coefficient arithmetic; never run a flow solver.

Reads original files without importing their scripts. Writes only beside this file.
The resulting JSON is deliberately incomplete and is not a run configuration.
"""
from pathlib import Path
import hashlib
import json
import math


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STATUS = "PREPARATION_ONLY_NOT_FROZEN_NOT_RUN"
MANUSCRIPT = "docs/reports/SIM240_中文稿_导师审阅版_20261022.md"
CPP = "CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp"
RAW = {
    "parallel": "CASE/D_series/D2_groove_error_map/results/h75_d100_dx5_P/steady/result.txt",
    "perpendicular": "CASE/D_series/D2_groove_error_map/results/h75_d100_dx5_T/steady/result.txt",
}
SOURCES = {
    "E01": (MANUSCRIPT, "sections 2.1-2.3, 4.4, 5.2; published rounded V2"),
    "E02": (CPP, "definitions only; does not establish historical build binding"),
    "E03": (RAW["parallel"], "saved 5 nm parallel discrete coefficient"),
    "E04": (RAW["perpendicular"], "saved 5 nm transverse discrete coefficient"),
    "E05": ("CASE/D_series/D3_squeeze_error_propagation/squeeze_error_propagation.py", "existing reduced-model code; not imported or run"),
    "E06": ("CASE/05_mesoscale/G5A_squeeze_resistance/config/g5a_baseline.json", "historical configuration; no transfer of its length/speed authorization"),
    "E07": ("docs/reports/NanrPrint_reference_review_20261030/REPORT.md", "previous inspection snapshot; not a new remote check"),
    "E08": ("docs/reports/NanrPrint_reference_review_20261030/sources/git_template_3r5cBoard_350/constant/fvModels", "reference drag configuration only"),
    "E09": ("/home/dell/OpenFOAM/OpenFOAM-13/src/finiteVolume/cfdTools/general/porosityModel/DarcyForchheimer/DarcyForchheimer.H", "Darcy source and units"),
    "E10": ("/home/dell/OpenFOAM/OpenFOAM-13/src/finiteVolume/cfdTools/general/porosityModel/DarcyForchheimer/DarcyForchheimerTemplates.C", "volume source versus momentum assembly"),
    "E11": ("docs/reports/Teacher_briefing_20261029/arithmetic.json", "comparison object only; raw results remain coefficient source"),
}


def write_json(name, obj):
    (HERE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def read_raw(rel):
    return dict(line.split("=", 1) for line in (ROOT / rel).read_text().splitlines() if "=" in line)


def close(a, b):
    # Arithmetic consistency tolerance; not a scientific acceptance threshold.
    return math.isclose(a, b, rel_tol=2e-12, abs_tol=0.0)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def tensor(kp, kt, along):
    return [[kp, 0.0], [0.0, kt]] if along == "x" else [[kt, 0.0], [0.0, kp]]


def main():
    initial_hashes = {name: hashlib.sha256((Path(name) if Path(name).is_absolute() else ROOT / name).read_bytes()).hexdigest()
                      for name, _ in SOURCES.values()}
    text = (ROOT / MANUSCRIPT).read_text()
    for token in ("1.7685", "1.6331", "0.4900", "0.6990"):
        require(token in text, "Published V2 token missing: " + token)
    raw = {direction: read_raw(path) for direction, path in RAW.items()}
    h, depth, width, period = 75e-9, 100e-9, 120e-9, 240e-9
    fraction = width / period
    H = h + fraction * depth
    mu, rho = 1e-3, 1000.0  # proposals from existing baseline, not adopted new inputs
    for direction, record in raw.items():
        require(record["direction"] == direction, "Raw direction mismatch")
        for key, expected in (("mesa_gap_m", h), ("groove_depth_m", depth),
                              ("groove_width_m", width), ("H_ref_m", H), ("dx_m", 5e-9)):
            require(close(float(record[key]), expected), "Raw geometry mismatch: " + key)
        require(close(mu / float(record["Keff_m3"]), float(record["R_eff_Pa_s_per_m3"])),
                "Recorded resistance versus proposed viscosity mismatch")
        measured_H = float(record["fluid_volume_m3"]) / (float(record["Lx_m"]) * float(record["Ly_m"]))
        require(close(measured_H, H), "Measured volume/plan area differs from nominal H")

    kp = ((h + depth)**3 + h**3) / 24.0
    kt = (h + depth)**3 * h**3 / (6.0 * ((h + depth)**3 + h**3))
    fp = 1.0 / (1.0 + 1.7685 * (depth / width)**1.6331)
    ft = 1.0 / (1.0 + 0.4900 * (depth / width)**0.6990)
    models = {
        "original_local_cubic": (kp, kt),
        "V2_published_rounded": (kp * fp, kt * ft),
        "OpenLB_dx5_diagnostic_only": tuple(float(raw[k]["Keff_m3"]) for k in ("parallel", "perpendicular")),
    }
    orientations = [
        {"id": "groove_along_long_y", "groove_axis": "y", "theta_from_positive_x_deg": 90,
         "t_parallel": [0, 1], "n_perpendicular": [-1, 0]},
        {"id": "groove_along_short_x", "groove_axis": "x", "theta_from_positive_x_deg": 0,
         "t_parallel": [1, 0], "n_perpendicular": [0, 1]},
    ]
    blockers = ["absolute_Lx_Ly_and_period_count", "closing_speed_or_static_pressure_gradient",
                "physical_properties_adoption", "wall_dissipation_route_and_OpenFOAM_source_definition",
                "mesh_or_volume_source_coupling", "pressure_and_force_boundary_equivalence",
                "numerical_resolution_solver_controls_and_resource_budget", "predeclared_acceptance_criteria",
                "final_scientific_interface_review"]
    common = {
        "schema_version": 1, "document_id": "SIM240_shared_transport_input_draft_20261030",
        "status": STATUS, "launch_ready": False, "solver_run_id": None,
        "simulation_authorized_by_this_document": False,
        "units": "SI", "coordinate_frame": {"x": "fixed short edge", "y": "fixed long edge", "z": "upward from substrate", "groove_axis_is_not_always_y": True},
        "geometry_baseline_candidate": {"h_m": h, "groove_depth_m": depth, "groove_width_m": width,
            "period_m": period, "groove_plan_fraction": fraction,
            "H_store_nominal_m": H, "H_envelope_m": h + depth,
            "envelope_fluid_volume_fraction": H / (h + depth),
            "status": "EXISTING_GEOMETRY_FOR_INTERFACE_CHECK_NOT_HOLDOUT"},
        "domain_candidate": {"Lx_m": None, "Ly_m": None, "Ly_over_Lx": 2.0,
            "aspect_ratio_status": "PROPOSED_NOT_FROZEN", "projected_area_m2": None,
            "period_counts": None, "edge_phase": None},
        "fluid_candidate": {"model": "incompressible_single_phase_newtonian_isothermal",
            "mu_Pa_s": mu, "rho_kg_m3": rho, "nu_m2_s": mu / rho,
            "status": "PROPOSED_FROM_EXISTING_D2_BASELINE_NOT_ADOPTED", "gravity_m_s2": [0.0, 0.0, 0.0]},
        "pressure_candidate": {"p_gauge_definition": "p_physical_Pa - p_environment_Pa",
            "p_environment_absolute_Pa": None, "four_macro_outer_edges_gauge_Pa": 0.0,
            "four_zero_edges_apply_to": "instantaneous_squeeze_only_not_static_pressure_drive",
            "status": "PROPOSED_BOUNDARY_NOT_IMPLEMENTED", "force_definition_status": "PENDING_STRESS_AND_PROJECTION_REVIEW"},
        "drives": {
            "static_interface_check": {"V_m_s": 0.0, "G_Pa_per_m": None,
                "boundary_implementation": None,
                "G_definition": "negative pressure gradient; select pressure-drop or periodic body-force implementation, never both",
                "four_zero_pressure_edges_not_applicable": True},
            "instantaneous_squeeze": {"V_m_s": None, "sign": "V = -dh/dt > 0", "dH_store_dt": "-V", "motion_implementation": None}},
        "averaging_interface_candidate": {"Ubar_definition": "J / H_store_nominal; intrinsic fluid-volume average in this convention",
            "H_for_conditional_total_drag_example_m": H, "mapping": "D_2D = H * inverse(K_2D)",
            "applies_only_if": "all unresolved resistance is carried by this total drag with the same averaging and pressure-gradient convention",
            "resolved_wall_route": "NOT_SELECTED; total drag cannot be added blindly to no-slip-wall solution",
            "Dzz_m_minus2": None, "out_of_plane_model": None,
            "Forchheimer_in_plane_m_minus1": [0.0, 0.0]},
        "formula_version": {"id": "V2_published_rounded_eq6", "parallel": {"a": 1.7685, "b": 1.6331},
            "perpendicular": {"a": 0.4900, "b": 0.6990}, "rule": "K_corrected = K_original / (1 + a*(depth/width)**b)",
            "source": "E01", "new_fit": False, "alternative_candidates_included": False},
        "orientations": orientations,
        "primary_comparison_inputs": ["original_local_cubic", "V2_published_rounded"],
        "optional_diagnostic_input": "OpenLB_dx5_diagnostic_only",
        "outputs_required": ["F_pressure_N", "F_total_stress_N_if_available", "R_pressure_N_s_per_m", "R_total_N_s_per_m_if_comparable", "chi_short_over_long", "p_gauge_Pa", "Q_each_outer_edge_m3_s", "volume_balance_residual"],
        "formal_acceptance_thresholds": None, "launch_blockers": blockers,
        "accuracy_claim_blockers": ["qualified_same_condition_explicit_squeeze_reference", "holdout_design_and_evaluation"],
        "scientific_state": {"NUMERICAL_GATE": "NOT_EVALUATED", "RESULT_PASS": None, "geometry_PASS": None,
            "reference_qualified": False, "submission_ready": False},
    }
    coefficients = []
    for model, (parallel, perpendicular) in models.items():
        require(parallel > 0 and perpendicular > 0, "Nonpositive K")
        for orientation in orientations:
            K = tensor(parallel, perpendicular, orientation["groove_axis"])
            kappa = [[v / H for v in row] for row in K]
            D = [[H / K[0][0], 0.0], [0.0, H / K[1][1]]]
            for i in (0, 1):
                require(close(kappa[i][i] * D[i][i], 1.0), "Reciprocal mapping failed")
                require(close(H / (mu * D[i][i]), K[i][i] / mu), "Unit-gradient flux identity failed")
            coefficients.append({"input_id": model, "orientation_id": orientation["id"],
                "K_parallel_m3": parallel, "K_perpendicular_m3": perpendicular,
                "K_global_m3": K, "kappa_global_m2_conditional": kappa,
                "D_global_m_minus2_conditional_total_drag": D,
                "in_plane_resistance_mu_over_K_Pa_s_per_m3": [mu / K[0][0], mu / K[1][1]],
                "arithmetic_example_only": True, "openfoam_dictionary_ready": False,
                "independent_squeeze_reference": False})
    briefing = json.loads((ROOT / SOURCES["E11"][0]).read_text())["example"]
    for direction, value, factor in (("parallel", kp * fp, fp), ("perpendicular", kt * ft, ft)):
        require(close(value, briefing[direction]["corrected"]), "Prior arithmetic comparison mismatch")
        require(close(factor, briefing[direction]["F"]), "Prior V2 factor mismatch")
    # Independent forms for original model and flat endpoint: no solver execution.
    shallow, deep = h**3 / 12.0, (h + depth)**3 / 12.0
    require(close(kp, (shallow + deep) / 2.0), "Arithmetic mean failed")
    require(close(kt, 2.0 / (1.0 / shallow + 1.0 / deep)), "Harmonic mean failed")
    require(close((2 * h**3) / 24.0, h**3 / 12.0), "Flat endpoint failed")
    require(close(H / (H / kp), kp), "Conductance round-trip failed")
    for model in models:
        pair = [r for r in coefficients if r["input_id"] == model]
        require(pair[0]["K_global_m3"][0][0] == pair[1]["K_global_m3"][1][1]
                and pair[0]["K_global_m3"][1][1] == pair[1]["K_global_m3"][0][0],
                "0/90 degree global axis swap failed")
    rows = ["# 条件性系数换算示例", "", "状态：准备算术；不是 OpenFOAM 可运行字典，也不是新流动结果。", "",
            "采用 H=125 nm，且假定该 Darcy 项承担全部平均阻力；不适用于直接叠加到已解析无滑移壁面。", "",
            "|输入|槽向|Kxx (m³)|Kyy (m³)|Dx (m⁻²)|Dy (m⁻²)|", "|---|---|---:|---:|---:|---:|"]
    for r in coefficients:
        K, D = r["K_global_m3"], r["D_global_m_minus2_conditional_total_drag"]
        rows.append(f"|{r['input_id']}|{r['orientation_id']}|{K[0][0]:.10e}|{K[1][1]:.10e}|{D[0][0]:.10e}|{D[1][1]:.10e}|")
    rows += ["", f"V2 因子：沿槽 {fp:.12g}；跨槽 {ft:.12g}。", "",
             "OpenLB 行来自现存两个 5 nm result.txt，只作已见输入诊断；不是显式挤压参照。完整数值及矩阵见 coefficient_examples.json。",
             "原始 run_id：h75_d100_dx5_P、h75_d100_dx5_T；来源哈希见 source_manifest.json。", ""]
    write_json("common_inputs.json", common)
    write_json("coefficient_examples.json", {"status": STATUS, "H_m": H, "V2_factors": {"parallel": fp, "perpendicular": ft}, "rows": coefficients})
    (HERE / "COEFFICIENT_EXAMPLES.md").write_text("\n".join(rows))
    entries = []
    for eid, (name, purpose) in SOURCES.items():
        source = Path(name) if Path(name).is_absolute() else ROOT / name
        require(hashlib.sha256(source.read_bytes()).hexdigest() == initial_hashes[name],
                "Source changed during preparation: " + name)
        entries.append({"id": eid, "path": name, "purpose": purpose,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "bytes": source.stat().st_size,
            "inspection": "AI_READ_OR_ARITHMETIC_COMPARISON_NOT_INDEPENDENT_HUMAN_ACCEPTANCE"})
    write_json("source_manifest.json", {"date": "2026-10-30", "files": entries,
        "historical_build_binding_reestablished": False,
        "external_primary_sources": ["https://cpp.openfoam.org/v13/DarcyForchheimer_8H_source.html", "https://arxiv.org/abs/2609.00065"]})
    write_json("verification.json", {"scope": "INPUT_AND_ALGEBRA_ONLY_NOT_FLOW_VALIDATION", "checks_completed": [
        "raw_direction_geometry_H_and_viscosity_resistance_consistency", "nominal_vs_measured_volume_height",
        "original_formula_two_equivalent_forms", "published_V2_arithmetic_against_prior_comparison_object",
        "principal_axis_swap_0_90_deg", "K_kappa_D_reciprocal_and_unit_gradient_flux_identities", "positive_coefficients", "flat_endpoint_original_model"],
        "all_arithmetic_checks_satisfied": True, "arithmetic_relative_tolerance": 2e-12,
        "scientific_acceptance_tolerance_set": False, "coefficient_rows": len(coefficients),
        "source_files_unchanged": True, "new_fit": False, "solver_execution": False, "launch_ready": False,
        "launch_blockers": blockers, "formal_gates": common["scientific_state"]})
    print("Prepared shared draft and 6 conditional coefficient rows; arithmetic checks satisfied; launch_ready=false; no solver run.")


if __name__ == "__main__":
    main()
