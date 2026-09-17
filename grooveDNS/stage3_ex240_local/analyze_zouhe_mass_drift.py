#!/usr/bin/env python3
"""Build the step-4 mass-drift comparison from immutable run CSV files."""

from __future__ import annotations

import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
RUNS = {
    "M0_fixed_zero": OUTPUT / "mass_drift_M0_zouhe_fixed_zero_2000_20260908",
    "M1_fixed_weak_nonzero": OUTPUT / "mass_drift_M1_zouhe_fixed_nonzero_2000_v2_20260908",
    "M2_moving_closed": OUTPUT / "mass_drift_M2_moving_closed_2000_20260908",
}
HISTORICAL = OUTPUT / "zouhe_preconversion_longrun2000_20260908/preconversion_longrun_global_history.csv"
COMPARISON = ROOT / "mass_drift_source_comparison.csv"
SUMMARY = ROOT / "mass_drift_source_analysis.txt"
RHO_PHYS = 1000.0
DX = 5e-9
LX = LY = 240e-9
INITIAL_CONTINUOUS_VOLUME = 7.2e-21


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def value(row: dict[str, str], field: str) -> float:
    return float(row[field])


rows: list[dict[str, str]] = []
for case, run in RUNS.items():
    source = read_csv(run / "mass_drift_history.csv")
    for row in source:
        row["source_run_id"] = run.name
        rows.append(row)

historical = read_csv(HISTORICAL)
previous_cumulative = 0.0
for row in historical:
    displacement = value(row, "total_displacement_nm") * 1e-9
    cumulative = value(row, "cumulative_out_mass_kg") - value(row, "cumulative_in_mass_kg")
    macro_step = cumulative - previous_cumulative
    previous_cumulative = cumulative
    mass = value(row, "total_fluid_mass_kg")
    fluid_cells = int(row["number_of_fluid_cells"])
    lattice_volume = fluid_cells * DX**3
    continuous_volume = INITIAL_CONTINUOUS_VOLUME - LX * LY * displacement
    rows.append({
        "case": "existing_moving_zouhe_open",
        "step": row["step"],
        "physical_time_s": row["physical_time_s"],
        "displacement_nm": row["total_displacement_nm"],
        "wall_velocity_m_s": row["wall_velocity_m_s"],
        "total_lattice_mass_kg": row["total_fluid_mass_kg"],
        "average_rho": f"{mass/(RHO_PHYS*lattice_volume):.17g}",
        "min_rho": row["min_rho"],
        "max_rho": row["max_rho"],
        "max_Mach": row["max_Mach"],
        "macro_out_mass_step_kg": f"{macro_step:.17g}",
        "macro_out_mass_cumulative_kg": f"{cumulative:.17g}",
        "population_out_mass_step_kg": "",
        "population_out_mass_cumulative_kg": "",
        "R_macro_kg": row["raw_mass_balance_residual_kg"],
        "R_macro_relative": row["relative_mass_balance_residual"],
        "R_population_kg": "",
        "R_population_relative": "",
        "mass_pre_collision_kg": "",
        "mass_post_collision_kg": "",
        "mass_post_full_step_kg": row["total_fluid_mass_kg"],
        "collision_mass_increment_kg": "",
        "stream_bouzidi_mass_increment_kg": "",
        "continuous_fluid_volume_m3": f"{continuous_volume:.17g}",
        "swept_volume_m3": f"{(INITIAL_CONTINUOUS_VOLUME-continuous_volume):.17g}",
        "nominal_lattice_fluid_volume_m3": f"{lattice_volume:.17g}",
        "fluid_material_cell_count": row["number_of_fluid_cells"],
        "illegal_links": row["illegal_link_count"],
        "material_conversions": row["material_conversion_count"],
        "finite": row["finite"],
        "source_run_id": "zouhe_preconversion_longrun2000_20260908",
    })

fields = list(rows[0])
with COMPARISON.open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)


def pearson(x: list[float], y: list[float]) -> float:
    xm = sum(x) / len(x)
    ym = sum(y) / len(y)
    xx = sum((v-xm)**2 for v in x)
    yy = sum((v-ym)**2 for v in y)
    if xx == 0 or yy == 0:
        return math.nan
    return sum((a-xm)*(b-ym) for a, b in zip(x, y)) / math.sqrt(xx*yy)


def linear_fit(x: list[float], y: list[float]) -> tuple[float, float, float]:
    xm = sum(x) / len(x)
    ym = sum(y) / len(y)
    xx = sum((v-xm)**2 for v in x)
    slope = sum((a-xm)*(b-ym) for a, b in zip(x, y)) / xx
    intercept = ym - slope*xm
    fitted = [intercept+slope*v for v in x]
    total = sum((v-ym)**2 for v in y)
    error = sum((v-f)**2 for v, f in zip(y, fitted))
    return slope, intercept, 1-error/total if total else 1.0


history_residual = [value(row, "relative_mass_balance_residual") for row in historical]
history_time = [value(row, "physical_time_s") for row in historical]
history_displacement = [value(row, "total_displacement_nm") for row in historical]
history_outflow = [value(row, "cumulative_out_mass_kg")-value(row, "cumulative_in_mass_kg") for row in historical]
history_swept = [LX*LY*d*1e-9*RHO_PHYS/value(historical[0], "total_fluid_mass_kg")
                 for d in history_displacement]
history_avg_rho = [value(row, "total_fluid_mass_kg") /
                   (RHO_PHYS*int(row["number_of_fluid_cells"])*DX**3)
                   for row in historical]

correlations = {
    "time": pearson(history_time, history_residual),
    "displacement": pearson(history_displacement, history_residual),
    "cumulative_outflow": pearson(history_outflow, history_residual),
    "swept_mass_fraction": pearson(history_swept, history_residual),
    "average_rho": pearson(history_avg_rho, history_residual),
}

increments = [history_residual[i]-history_residual[i-1]
              for i in range(1, len(history_residual))]
strictly_monotone_from_start = all(increment > 0 for increment in increments)

with SUMMARY.open("w") as stream:
    stream.write("SIM-EC1XT240 step-4 mass-drift source analysis\n")
    stream.write(f"comparison_rows={len(rows)}\n")
    stream.write(f"existing_longrun_steps={historical[-1]['step']}\n")
    stream.write(f"residual_strictly_monotone_from_step_1={str(strictly_monotone_from_start).lower()}\n")
    for name, correlation in correlations.items():
        stream.write(f"pearson_residual_vs_{name}={correlation:.17g}\n")
    for name, series in (("time", history_time),
                         ("displacement_nm", history_displacement),
                         ("cumulative_outflow_kg", history_outflow),
                         ("swept_mass_fraction", history_swept),
                         ("average_rho", history_avg_rho)):
        slope, intercept, r_squared = linear_fit(series, history_residual)
        stream.write(f"linear_{name}_slope={slope:.17g}\n")
        stream.write(f"linear_{name}_intercept={intercept:.17g}\n")
        stream.write(f"linear_{name}_r_squared={r_squared:.17g}\n")
    for case, run in RUNS.items():
        data = read_csv(run / "mass_drift_history.csv")
        last = data[-1]
        max_collision = max(abs(value(row, "collision_mass_increment_kg")) for row in data)
        max_post = max(abs(value(row, "stream_bouzidi_mass_increment_kg")) for row in data)
        stream.write(f"{case}_final_mass_relative_change="
                     f"{(value(last,'total_lattice_mass_kg')-value(data[0],'total_lattice_mass_kg'))/value(data[0],'total_lattice_mass_kg'):.17g}\n")
        stream.write(f"{case}_final_R_macro_relative={last['R_macro_relative']}\n")
        stream.write(f"{case}_final_R_population_relative={last['R_population_relative']}\n")
        stream.write(f"{case}_max_abs_collision_mass_increment_kg={max_collision:.17g}\n")
        stream.write(f"{case}_max_abs_stream_bouzidi_mass_increment_kg={max_post:.17g}\n")
        stream.write(f"{case}_final_average_rho={last['average_rho']}\n")
        stream.write(f"{case}_final_swept_volume_m3={last['swept_volume_m3']}\n")
    m2 = read_csv(RUNS["M2_moving_closed"] / "mass_drift_history.csv")
    m2_initial = m2[0]
    m2_final = m2[-1]
    full_mass_change = ((value(m2_final,"total_lattice_mass_kg")-
                         value(m2_initial,"total_lattice_mass_kg")) /
                        value(m2_initial,"total_lattice_mass_kg"))
    swept_fraction = value(m2_final,"swept_volume_m3") / value(m2_initial,"continuous_fluid_volume_m3")
    continuous_mass_proxy = (value(m2_final,"average_rho") *
                             value(m2_final,"continuous_fluid_volume_m3"))
    initial_proxy = (value(m2_initial,"average_rho") *
                     value(m2_initial,"continuous_fluid_volume_m3"))
    stream.write(f"M2_final_swept_volume_fraction={swept_fraction:.17g}\n")
    stream.write(f"M2_full_cell_mass_change_to_swept_fraction_ratio={full_mass_change/swept_fraction:.17g}\n")
    stream.write(f"M2_continuous_volume_mass_proxy_relative_change={continuous_mass_proxy/initial_proxy-1:.17g}\n")
    hist_initial_mass=value(historical[0],"total_fluid_mass_kg")
    hist_final_mass=value(historical[-1],"total_fluid_mass_kg")
    hist_final_volume=INITIAL_CONTINUOUS_VOLUME-LX*LY*history_displacement[-1]*1e-9
    hist_geom_mass_proxy=hist_final_mass*hist_final_volume/INITIAL_CONTINUOUS_VOLUME
    hist_final_out=history_outflow[-1]
    stream.write(f"existing_open_final_domain_mass_change_relative={(hist_final_mass-hist_initial_mass)/hist_initial_mass:.17g}\n")
    stream.write(f"existing_open_final_outflow_relative={hist_final_out/hist_initial_mass:.17g}\n")
    stream.write(f"existing_open_final_macro_residual_relative={history_residual[-1]:.17g}\n")
    stream.write(f"existing_open_final_swept_mass_fraction={history_swept[-1]:.17g}\n")
    stream.write(f"existing_open_residual_to_swept_fraction_ratio={history_residual[-1]/history_swept[-1]:.17g}\n")
    stream.write(f"existing_open_continuous_volume_proxy_balance_relative={(hist_geom_mass_proxy-hist_initial_mass+hist_final_out)/hist_initial_mass:.17g}\n")

print(COMPARISON)
print(SUMMARY)
