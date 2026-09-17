#!/usr/bin/env python3
"""Reproduce the numerical comparisons for the Zou/He pressure candidate.

This script is read-only with respect to simulation outputs.  It writes only
derived CSV/text files in stage3_ex240_local.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read_result(relative: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in (ROOT / relative / "result.txt").read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            data[key] = value
    return data


def read_csv(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open(newline="") as stream:
        return list(csv.DictReader(stream))


def as_float(value: str) -> float:
    return float(value)


cases = {
    "Z0_ZouHe_fixed_zero": "output/zouhe_pressure_Z0_zero_fixed_650_20260908",
    "Z1_ZouHe_fixed_nonzero": "output/zouhe_pressure_Z1_nonzero_fixed_650_20260908",
    "Z1_LocalPressure_fixed_nonzero": "output/localpressure_fixed_nonzero_profile_650_20260908",
    "S_ZouHe_separated_moving": "output/zouhe_pressure_separated_moving_650_20260908",
    "S_LocalPressure_separated_moving": "output/moving_piston_pressure_separated_C650_20260908",
    "C_ZouHe_patch": "output/zouhe_pressure_Cpatch_650_20260908",
    "C_ZouHe_no_patch": "output/zouhe_pressure_Cnopatch_650_20260908",
    "C_LocalPressure_periodic_links": "output/boundary_intersection_periodic_link_fix_C650_20260907",
}

summary_fields = [
    "case",
    "run_id",
    "PASS",
    "steps_completed",
    "max_Mach",
    "first_Mach_over_threshold_step",
    "rho_min",
    "rho_max",
    "first_rho_threshold_step",
    "first_nonfinite_step",
    "max_speed_m_s",
    "max_speed_location",
    "initial_mass_kg",
    "final_mass_kg",
    "final_low_outward_flux_kg_s",
    "final_high_outward_flux_kg_s",
    "final_net_outward_flux_kg_s",
    "cumulative_outward_mass_kg",
    "max_abs_relative_mass_balance_residual",
    "max_invalid_links",
    "material_conversions",
    "material_field_unchanged",
]

with (ROOT / "zouhe_pressure_candidate_summary.csv").open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=summary_fields)
    writer.writeheader()
    for label, path in cases.items():
        result = read_result(path)
        rho = result.get("rho_range", ",").split(",")
        low = result.get("final_low_outward_flux_kg_s", result.get("low_outward_flux_final_kg_s", ""))
        high = result.get("final_high_outward_flux_kg_s", result.get("high_outward_flux_final_kg_s", ""))
        net = result.get("final_net_outward_flux_kg_s", "")
        if not net and low and high:
            net = f"{as_float(low) + as_float(high):.17g}"
        row = {
            "case": label,
            "run_id": result.get("run_id", ""),
            "PASS": result.get("PASS", ""),
            "steps_completed": result.get("steps_completed", ""),
            "max_Mach": result.get("max_Mach", ""),
            "first_Mach_over_threshold_step": result.get(
                "first_Mach_over_0.05_step", result.get("first_Mach_over_0.01_step", "")
            ),
            "rho_min": rho[0],
            "rho_max": rho[1] if len(rho) > 1 else "",
            "first_rho_threshold_step": result.get(
                "first_rho_outside_0.8_1.2_step", result.get("first_rho_outside_0.99_1.01_step", "")
            ),
            "first_nonfinite_step": result.get("first_nonfinite_step", ""),
            "max_speed_m_s": result.get("max_speed_m_s", ""),
            "max_speed_location": result.get("max_speed_location", ""),
            "initial_mass_kg": result.get("initial_mass_kg", result.get("initial_raw_fluid_mass_kg", "")),
            "final_mass_kg": result.get("final_mass_kg", result.get("final_raw_fluid_mass_kg", "")),
            "final_low_outward_flux_kg_s": low,
            "final_high_outward_flux_kg_s": high,
            "final_net_outward_flux_kg_s": net,
            "cumulative_outward_mass_kg": result.get("cumulative_outward_mass_kg", ""),
            "max_abs_relative_mass_balance_residual": result.get(
                "max_abs_relative_mass_balance_residual", ""
            ),
            "max_invalid_links": result.get("max_invalid_links", ""),
            "material_conversions": result.get("material_conversions", ""),
            "material_field_unchanged": result.get("material_field_unchanged", ""),
        }
        writer.writerow(row)


def max_numeric_csv_difference(path_a: str, path_b: str, ignored: set[str]) -> tuple[float, str, int]:
    rows_a = read_csv(path_a)
    rows_b = read_csv(path_b)
    if len(rows_a) != len(rows_b):
        raise RuntimeError(f"row mismatch: {path_a} vs {path_b}")
    maximum = 0.0
    field = ""
    row_number = 0
    for index, (row_a, row_b) in enumerate(zip(rows_a, rows_b), start=2):
        for key in row_a:
            if key in ignored:
                continue
            try:
                delta = abs(float(row_a[key]) - float(row_b[key]))
            except ValueError:
                if row_a[key] != row_b[key]:
                    raise RuntimeError(f"nonnumeric mismatch at row {index}, {key}")
                continue
            if not math.isfinite(delta):
                raise RuntimeError(f"nonfinite comparison at row {index}, {key}")
            if delta > maximum:
                maximum, field, row_number = delta, key, index
    return maximum, field, row_number


diagnostic_diff = max_numeric_csv_difference(
    "output/zouhe_pressure_Cpatch_650_20260908/diagnostics.csv",
    "output/zouhe_pressure_Cnopatch_650_20260908/diagnostics.csv",
    {"max_material"},
)
tracked_diff = max_numeric_csv_difference(
    "output/zouhe_pressure_Cpatch_650_20260908/tracked_cells.csv",
    "output/zouhe_pressure_Cnopatch_650_20260908/tracked_cells.csv",
    {"material"},
)
profile_diff = max_numeric_csv_difference(
    "output/zouhe_pressure_Z1_nonzero_fixed_650_20260908/velocity_profile_final.csv",
    "output/localpressure_fixed_nonzero_profile_650_20260908/velocity_profile_final.csv",
    set(),
)
(ROOT / "zouhe_patch_ablation_diff.txt").write_text(
    "Cpatch_vs_Cnopatch\n"
    f"diagnostics_max_abs_numeric_difference={diagnostic_diff[0]:.17g}\n"
    f"diagnostics_field={diagnostic_diff[1]}\n"
    f"diagnostics_csv_row={diagnostic_diff[2]}\n"
    f"tracked_physical_and_population_max_abs_difference={tracked_diff[0]:.17g}\n"
    f"tracked_field={tracked_diff[1]}\n"
    f"tracked_csv_row={tracked_diff[2]}\n"
    f"Z1_velocity_profile_max_abs_difference={profile_diff[0]:.17g}\n"
    f"Z1_velocity_profile_field={profile_diff[1]}\n"
    f"Z1_velocity_profile_csv_row={profile_diff[2]}\n"
    "ignored_diagnostics_field=max_material (the label-only ablation changes 4/5 to 1)\n"
    "ignored_tracked_field=material (the ablation intentionally changes only labels 4/5 to 1)\n"
)


old_selected = {
    int(row["step"]): row
    for row in read_csv("output/f3_reverse_causal_trace_C_v3_20260908/f3_causal_selected_steps.csv")
}
new_rows = read_csv("output/zouhe_pressure_Cnopatch_650_20260908/tracked_cells.csv")
new_by_step_cell = {(int(row["step"]), row["cell_name"]): row for row in new_rows}
selected_steps = [3, 4, 20, 40, 52, 100, 160, 180, 200, 209, 650]

history_fields = [
    "step",
    "LocalPressure_donor_f3_after_collision",
    "LocalPressure_donor_f8_pre_collision",
    "LocalPressure_donor_f17_after_collision",
    "LocalPressure_source_f8_after_Bouzidi",
    "ZouHe_cell_0_0_14_f3_end_step",
    "ZouHe_cell_0_0_14_f8_end_step",
    "ZouHe_cell_0_0_14_f17_end_step",
    "ZouHe_cell_0_1_15_f3_end_step",
    "ZouHe_cell_0_1_15_f8_end_step",
    "ZouHe_cell_0_1_15_f17_end_step",
    "ZouHe_cell_0_0_14_Mach_end_step",
]
with (ROOT / "zouhe_f3_f8_f17_history_comparison.csv").open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=history_fields)
    writer.writeheader()
    for step in selected_steps:
        old = old_selected.get(step, {})
        donor = new_by_step_cell[(step, "cell_0_0_14")]
        source = new_by_step_cell[(step, "cell_0_1_15")]
        writer.writerow(
            {
                "step": step,
                "LocalPressure_donor_f3_after_collision": old.get("donor_f3_after_LP_collision", ""),
                "LocalPressure_donor_f8_pre_collision": old.get("donor_f8_pre_LP", ""),
                "LocalPressure_donor_f17_after_collision": old.get("donor_f17_after_LP_collision", ""),
                "LocalPressure_source_f8_after_Bouzidi": old.get("source_f8_after_Bouzidi", ""),
                "ZouHe_cell_0_0_14_f3_end_step": donor["f3"],
                "ZouHe_cell_0_0_14_f8_end_step": donor["f8"],
                "ZouHe_cell_0_0_14_f17_end_step": donor["f17"],
                "ZouHe_cell_0_1_15_f3_end_step": source["f3"],
                "ZouHe_cell_0_1_15_f8_end_step": source["f8"],
                "ZouHe_cell_0_1_15_f17_end_step": source["f17"],
                "ZouHe_cell_0_0_14_Mach_end_step": donor["Mach"],
            }
        )

print("wrote zouhe_pressure_candidate_summary.csv")
print("wrote zouhe_patch_ablation_diff.txt")
print("wrote zouhe_f3_f8_f17_history_comparison.csv")
