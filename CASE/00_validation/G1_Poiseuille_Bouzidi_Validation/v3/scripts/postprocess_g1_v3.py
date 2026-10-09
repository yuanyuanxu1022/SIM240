#!/usr/bin/env python3
import csv
import math
import sys
from pathlib import Path


R2_MIN = 0.999999
INTERCEPT_FRACTION_MAX = 0.01


def parse_key_values(path: Path):
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def evaluate_force_response(rows):
    if len(rows) != 3:
        return {
            "slope": math.nan,
            "intercept": math.nan,
            "r2": math.nan,
            "intercept_fraction": math.nan,
            "pass": False,
        }
    x_values = [row["force"] for row in rows]
    y_values = [row["J"] for row in rows]
    x_mean = sum(x_values) / len(x_values)
    y_mean = sum(y_values) / len(y_values)
    variance_x = sum((x - x_mean) ** 2 for x in x_values)
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values)) / variance_x
    intercept = y_mean - slope * x_mean
    residual = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_values, y_values))
    total = sum((y - y_mean) ** 2 for y in y_values)
    r2 = 1.0 if total == 0.0 else 1.0 - residual / total
    intercept_fraction = abs(intercept) / max(abs(value) for value in y_values)
    return {
        "slope": slope,
        "intercept": intercept,
        "r2": r2,
        "intercept_fraction": intercept_fraction,
        "pass": r2 >= R2_MIN and intercept_fraction <= INTERCEPT_FRACTION_MAX,
    }


def load_rows(batch_dir: Path):
    rows = []
    with (batch_dir / "matrix_definition.csv").open(newline="", encoding="utf-8") as handle:
        definitions = list(csv.DictReader(handle))
    for definition in definitions:
        case_id = definition["case_id"]
        steady = batch_dir / case_id / "steady"
        summary_path = steady / "result_summary.csv"
        result_path = steady / "result.txt"
        exit_path = steady / "exit_code.txt"
        row = {
            "case_id": case_id,
            "force": float(definition["acceleration_m_s2"]),
            "status": "MISSING",
        }
        if not (summary_path.exists() and result_path.exists() and exit_path.exists()):
            rows.append(row)
            continue
        with summary_path.open(newline="", encoding="utf-8") as handle:
            summary = next(csv.DictReader(handle))
        result = parse_key_values(result_path)
        row.update({
            "J": float(summary["J"]),
            "K_relative_error": float(summary["relative_error"]),
            "profile_L2": float(result["velocity_profile_L2_relative_error"]),
            "offset_relative": float(result["velocity_offset_relative_to_analytic_max"]),
            "geometry_PASS": result.get("geometry_PASS") == "true",
            "q_audit_PASS": result.get("q_audit_PASS") == "true",
            "solver_PASS": result.get("PASS") == "true",
            "exit_code": int(exit_path.read_text(encoding="utf-8").strip()),
            "status": "COMPLETE",
        })
        rows.append(row)
    return rows


def write_outputs(batch_dir: Path, rows, metrics):
    fields = [
        "case_id", "force", "J", "K_relative_error", "profile_L2",
        "offset_relative", "geometry_PASS", "q_audit_PASS", "solver_PASS",
        "exit_code", "status",
    ]
    with (batch_dir / "matrix_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{key: row.get(key, "") for key in fields} for row in rows])

    completed = [row for row in rows if row["status"] == "COMPLETE"]
    cases_pass = len(completed) == 3 and all(
        row["solver_PASS"] and row["geometry_PASS"] and row["q_audit_PASS"] and row["exit_code"] == 0
        for row in completed
    )
    overall_pass = cases_pass and metrics["pass"]
    lines = [
        "# G1-V3 fine-grid force-linearity validation",
        "",
        f"NUMERICAL_GATE: {'PASS' if cases_pass else 'FAIL'}",
        f"LINEARITY_GATE: {'PASS' if metrics['pass'] else 'FAIL'}",
        f"RESULT_PASS: {'true' if overall_pass else 'false'}",
        "",
        f"R2: {metrics['r2']:.16g}",
        f"intercept_m2_s: {metrics['intercept']:.16e}",
        f"intercept_fraction: {metrics['intercept_fraction']:.16g}",
        "",
        "The G1-V2 5-nm baseline remains a retained FAIL record. This report only evaluates the independently run G1-V3 fine-grid matrix.",
    ]
    (batch_dir / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (batch_dir / "exit_code.txt").write_text("0\n" if overall_pass else "3\n", encoding="utf-8")
    return overall_pass


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: postprocess_g1_v3.py BATCH_DIRECTORY")
    batch_dir = Path(sys.argv[1]).resolve()
    rows = load_rows(batch_dir)
    metrics = evaluate_force_response([row for row in rows if row["status"] == "COMPLETE"])
    passed = write_outputs(batch_dir, rows, metrics)
    raise SystemExit(0 if passed else 3)


if __name__ == "__main__":
    main()
