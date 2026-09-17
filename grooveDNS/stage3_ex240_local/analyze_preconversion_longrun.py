#!/usr/bin/env python3
"""Postprocess the immutable Zou/He pre-conversion long-run output."""

from __future__ import annotations

import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUN = ROOT / "output/zouhe_preconversion_longrun2000_20260908"


def rows(name: str) -> list[dict[str, str]]:
    with (RUN / name).open(newline="") as stream:
        return list(csv.DictReader(stream))


global_rows = rows("preconversion_longrun_global_history.csv")
watch_rows = rows("preconversion_longrun_population_watch.csv")


def f(row: dict[str, str], field: str) -> float:
    return float(row[field])


watch_by_step: dict[int, list[dict[str, str]]] = {}
for row in watch_rows:
    watch_by_step.setdefault(int(row["step"]), []).append(row)

series: dict[str, list[float]] = {
    "max_Mach": [abs(f(row, "max_Mach")) for row in global_rows],
    "max_velocity_m_s": [abs(f(row, "max_velocity_m_s")) for row in global_rows],
    "rho_deviation": [
        max(abs(f(row, "min_rho") - 1), abs(f(row, "max_rho") - 1))
        for row in global_rows
    ],
    "relative_mass_residual": [abs(f(row, "relative_mass_balance_residual")) for row in global_rows],
}
for population in ("f3", "f8", "f17"):
    series[population] = [
        max(abs(f(row, population)) for row in watch_by_step[step])
        for step in range(len(global_rows))
    ]


def trend(values: list[float]) -> dict[str, float | bool]:
    window = values[-min(600, len(values)):]
    points = [(i, value) for i, value in enumerate(window) if value > 0]
    xs = [point[0] for point in points]
    ys = [math.log(point[1]) for point in points]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    ss_x = sum((x - x_mean) ** 2 for x in xs)
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / ss_x
    fitted = [y_mean + slope * (x - x_mean) for x in xs]
    ss_total = sum((y - y_mean) ** 2 for y in ys)
    ss_error = sum((y - estimate) ** 2 for y, estimate in zip(ys, fitted))
    r_squared = 1 - ss_error / ss_total if ss_total else 1.0
    ratio = window[-1] / window[0] if window[0] else math.inf
    e_folding = 1 / slope if slope > 0 else math.inf
    monotone_fraction = sum(
        window[index] >= window[index - 1] for index in range(1, len(window))
    ) / (len(window) - 1)
    flagged = ratio >= 10 and r_squared >= 0.98 and e_folding <= 300
    return {
        "window_steps": len(window),
        "end_to_start_ratio": ratio,
        "log_linear_r_squared": r_squared,
        "e_folding_steps": e_folding,
        "nondecreasing_step_fraction": monotone_fraction,
        "frozen_exponential_flag": flagged,
    }


trend_results = {name: trend(values) for name, values in series.items()}

with (RUN / "preconversion_longrun_trend_analysis.csv").open("w", newline="") as stream:
    fields = ["quantity", *next(iter(trend_results.values())).keys()]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for name, result in trend_results.items():
        writer.writerow({"quantity": name, **result})

phase_ranges = [("initial_transient", 0, 200), ("moving_early", 201, 650),
                ("moving_extended", 651, int(global_rows[-1]["step"]))]
with (RUN / "preconversion_longrun_phase_summary.csv").open("w", newline="") as stream:
    fields = ["phase", "first_step", "last_step", "max_Mach", "max_velocity_m_s",
              "max_rho_deviation", "max_abs_relative_mass_residual",
              "min_net_outlet_flux_kg_s", "max_net_outlet_flux_kg_s"]
    writer = csv.DictWriter(stream, fieldnames=fields);writer.writeheader()
    for name, first, last in phase_ranges:
        selected = global_rows[first:last + 1]
        writer.writerow({
            "phase": name, "first_step": first, "last_step": last,
            "max_Mach": max(f(row, "max_Mach") for row in selected),
            "max_velocity_m_s": max(f(row, "max_velocity_m_s") for row in selected),
            "max_rho_deviation": max(max(abs(f(row, "min_rho") - 1),
                                             abs(f(row, "max_rho") - 1)) for row in selected),
            "max_abs_relative_mass_residual": max(abs(f(row, "relative_mass_balance_residual"))
                                                    for row in selected),
            "min_net_outlet_flux_kg_s": min(f(row, "outlet_flux_kg_s") for row in selected),
            "max_net_outlet_flux_kg_s": max(f(row, "outlet_flux_kg_s") for row in selected),
        })

for output_name, source_rows in (
    ("preconversion_longrun_last20_global.csv", global_rows[-20:]),
    (
        "preconversion_longrun_last20_population.csv",
        [row for row in watch_rows if int(row["step"]) >= int(global_rows[-1]["step"]) - 19],
    ),
):
    with (RUN / output_name).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(source_rows[0]))
        writer.writeheader();writer.writerows(source_rows)

low = [f(row, "low_outward_flux_kg_s") for row in global_rows]
high = [f(row, "high_outward_flux_kg_s") for row in global_rows]
asymmetry = [
    abs(a - b) / max(abs(a), abs(b))
    for a, b in zip(low, high)
    if max(abs(a), abs(b)) > 0
]
threshold_pass = False
trend_pass = not any(result["frozen_exponential_flag"] for result in trend_results.values())
overall_pass = threshold_pass and trend_pass and int(global_rows[-1]["step"]) == 2000

with (RUN / "final_assessment.txt").open("w") as stream:
    stream.write("verdict=STEP 4 LONG-RUN PASS\n" if overall_pass else "verdict=STEP 4 LONG-RUN FAIL\n")
    stream.write(f"steps_completed={global_rows[-1]['step']}\n")
    stream.write("stop_reason=mass_residual\n")
    stream.write("threshold_checks_PASS=false\n")
    stream.write(f"trend_checks_PASS={str(trend_pass).lower()}\n")
    stream.write(f"rho_deviation_exponential_flag={str(trend_results['rho_deviation']['frozen_exponential_flag']).lower()}\n")
    stream.write(f"max_flux_relative_asymmetry={max(asymmetry):.17g}\n")
    stream.write("hold_phase=not_applicable_because_conversion_prediction_allowed_continuous_motion\n")
    stream.write("allow_step5_single_conversion_ledger=false\n")

print(RUN / "preconversion_longrun_trend_analysis.csv")
print(RUN / "preconversion_longrun_phase_summary.csv")
print(RUN / "final_assessment.txt")
