#!/usr/bin/env python3
"""Export small, reviewable pilot evidence without committing raw fields."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT = ROOT.parent.parent / "docs/reports/PAPER1_conclusion_FVM_FEM_pilot_20261113"
CASES = ["flat_h75_P", "flat_h75_T", "h75_d100_P", "h75_d100_T", "h50_d120_T"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cases = []
    levels = []
    for case in CASES:
        path = ROOT / "results" / case / "VERIFICATION.json"
        if not path.exists():
            raise FileNotFoundError(path)
        data = json.loads(path.read_text())
        cases.append({"case_id": case, "status": data["status"],
                      "problems": data["problems"],
                      "reference_qualification": data["reference_qualification"]})
        for row in data["levels"]:
            levels.append(row)
    overall = all(c["status"] == "PILOT_NUMERICAL_CHECKS_PASS" for c in cases)
    sources = {name: sha(ROOT / name) for name in
               ["PROTOCOL.md", "fem_pilot.py", "verify_results.py", "compare_pairs.py"]}
    summary = {
        "overall_pilot_status": "ALL_PLANNED_PILOT_CHECKS_PASS" if overall else "PILOT_INCOMPLETE_OR_FAIL",
        "reference_qualified": False,
        "strict_error_bound_established": False,
        "submission_ready": False,
        "automatic_followup_authorized": False,
        "cases": cases,
        "source_sha256": sources,
        "raw_fields_location": str(ROOT / "results"),
        "raw_fields_in_git": False,
    }
    REPORT.mkdir(parents=True, exist_ok=True)
    (REPORT / "FEM_PILOT_VERIFICATION.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    fields = ["case_id", "dx_nm", "K_recomputed_m3",
              "K_change_from_coarser_recomputed_percent", "area_relative_error",
              "K_vs_solver_relative_difference", "direct_relative_residual_recomputed",
              "solver_reported_direct_relative_residual",
              "power_balance_recomputed_percent", "section_flux_spread_percent",
              "section_vs_volume_percent", "wall_velocity_relative_max",
              "periodic_velocity_relative_max_difference",
              "pressure_periodic_relative_max_difference", "pressure_mean_normalized",
              "divergence_L2_relative",
              "flat_K_error_recomputed_percent", "flat_profile_L2_recomputed_percent",
              "FVM_difference_recomputed_percent"]
    with (REPORT / "FEM_PILOT_LEVELS.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(levels)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
