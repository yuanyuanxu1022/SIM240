#!/usr/bin/env python3
"""Build the per-point reference-qualification table for the FEM pilot.

This script only READS saved evidence.  It does not solve, re-integrate,
re-grade or re-fit anything.  Every threshold it compares against is quoted
from CASE/paper1_fem_stokes_pilot_v1/PROTOCOL.md section 4; nothing here
invents a new criterion.

Inputs
    CASE/paper1_fem_stokes_pilot_v1/results/<case>/VERIFICATION.json
    CASE/paper1_fem_stokes_pilot_v1/results/<case>/dx_*nm.npz   (existence only)
    docs/reports/PAPER1_reference_table_20261113/POINT_TABLE.csv

Outputs
    POINT_VERDICTS.csv                one row per FEM geometry point
    FEM_COVERAGE_scope_v2.csv         refreshed coverage table (supersedes the
                                      scope-v1 table built before the gate-scope
                                      fix, in which h25/d100 T still read FAIL)

Exit code is non-zero if any gate is out of limits, so this cannot silently
publish a table that contradicts the verification records.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CASE = ROOT / "CASE/paper1_fem_stokes_pilot_v1"
POINT_TABLE = ROOT / "docs/reports/PAPER1_reference_table_20261113/POINT_TABLE.csv"
OUT = Path(__file__).resolve().parent

# PROTOCOL.md section 4, quoted verbatim as limits.
LIMIT_GRID_COARSE_TO_MID = 1.0     # coarse->mid K change <= 1%
LIMIT_GRID_MID_TO_FINE = 0.5       # mid->fine   K change <= 0.5%
LIMIT_FINE_POWER = 0.1             # groove fine power difference <= 0.1%
LIMIT_FINE_SECTION = 0.01          # transverse fine section flux <= 0.01%
LIMIT_FLAT_ANALYTIC = 0.1          # flat K error / profile L2 <= 0.1%
LIMIT_FVM_ANCHOR = 0.5             # h75 fine K vs qualified FVM <= 0.5%
LIMIT_TIGHT = 1e-10                # wall / periodic / pressure-mean / residual
LIMIT_K_MISMATCH = 1e-9            # independent K vs solver K

# What each point is load-bearing for.  Kept as a label only; it does not
# change any number.
ROLE = {
    ("h75", "d100", "P"): "baseline anchor; cross-checked against qualified FVM",
    ("h75", "d100", "T"): "baseline anchor; cross-checked against qualified FVM",
    ("h25", "d100", "T"): "thin-gap lower bound; carries the largest OpenLB/FEM gap",
    ("h50", "d120", "T"): "fixed-depth deviation maximum",
    ("h100", "d100", "T"): "intermediate transition; outside the original 18 geometries",
    ("h125", "d120", "T"): "deep-gap pair partner; single-point review already filed",
}


def load_point_table():
    rows = {}
    with POINT_TABLE.open() as stream:
        for row in csv.DictReader(stream):
            key = (row["h_nm"], row["d_nm"], row["direction"])
            rows[key] = row
    return rows


def read_verifications():
    out = []
    for path in sorted(CASE.glob("results/*/VERIFICATION.json")):
        case = path.parent.name
        record = json.loads(path.read_text())
        levels = sorted(record["levels"], key=lambda r: -r["dx_nm"])
        fine = levels[-1]
        npz = sorted(path.parent.glob("dx_*nm_fields.npz"))
        key = (str(int(float(fine["h_nm"]))), str(int(float(fine["d_nm"]))), fine["direction"])
        out.append(
            {
                "case": case,
                "key": key,
                "status": record["status"],
                "gate_scope_version": record.get("gate_scope_version", "unknown"),
                "n_problems": len(record.get("problems", [])),
                "n_diagnostics": len(record.get("diagnostics", [])),
                "n_levels": len(levels),
                "n_npz": len(npz),
                "fine_dx": fine["dx_nm"],
                "K_fine": fine["K_recomputed_m3"],
                "c2m": levels[1]["K_change_from_coarser_recomputed_percent"],
                "m2f": fine["K_change_from_coarser_recomputed_percent"],
                "power_fine": fine["power_balance_recomputed_percent"],
                "section_fine": max(
                    fine["section_flux_spread_percent"], fine["section_vs_volume_percent"]
                ),
                "fvm_diff": fine.get("FVM_difference_recomputed_percent"),
                "flat_K": fine.get("flat_K_error_recomputed_percent"),
                "flat_L2": fine.get("flat_profile_L2_recomputed_percent"),
                "worst_tight": max(
                    max(row[k] for row in levels)
                    for k in (
                        "area_relative_error",
                        "wall_velocity_relative_max",
                        "periodic_velocity_relative_max_difference",
                        "pressure_periodic_relative_max_difference",
                        "pressure_mean_normalized",
                        "direct_relative_residual_recomputed",
                    )
                ),
                "worst_K_mismatch": max(
                    row["K_vs_solver_relative_difference"] for row in levels
                ),
            }
        )
    return out


def main():
    table = load_point_table()
    records = read_verifications()
    problems = []

    rows = []
    for rec in records:
        key = rec["key"]
        is_flat = key[1] == "0"
        pt = table.get(key, {})

        # Protocol limits, applied as written (finest-level scoping already
        # baked into m2f / power_fine / section_fine by the verifier).
        checks = [
            ("mid->fine grid change", rec["m2f"], LIMIT_GRID_MID_TO_FINE),
            ("fine power", rec["power_fine"], LIMIT_FINE_POWER),
        ]
        if not is_flat:
            checks.append(("coarse->mid grid change", rec["c2m"], LIMIT_GRID_COARSE_TO_MID))
        if key[2] == "T":
            checks.append(("fine section flux", rec["section_fine"], LIMIT_FINE_SECTION))
        if is_flat:
            checks.append(("flat analytic K", rec["flat_K"], LIMIT_FLAT_ANALYTIC))
            checks.append(("flat profile L2", rec["flat_L2"], LIMIT_FLAT_ANALYTIC))
        if rec["fvm_diff"] is not None:
            checks.append(("FVM anchor difference", rec["fvm_diff"], LIMIT_FVM_ANCHOR))
        checks.append(("wall/periodic/pressure/residual", rec["worst_tight"], LIMIT_TIGHT))
        checks.append(("independent K vs solver", rec["worst_K_mismatch"], LIMIT_K_MISMATCH))

        for label, value, limit in checks:
            if value is None:
                problems.append(f"{rec['case']}: {label} unavailable")
            elif value > limit:
                problems.append(f"{rec['case']}: {label} {value:.6g} > {limit:g}")

        margins_complete = (
            rec["n_levels"] == 3
            and rec["n_npz"] == 3
            and rec["status"].endswith("PASS")
            and rec["n_problems"] == 0
        )
        if not margins_complete:
            problems.append(
                f"{rec['case']}: incomplete evidence "
                f"(levels={rec['n_levels']}, npz={rec['n_npz']}, "
                f"status={rec['status']}, problems={rec['n_problems']})"
            )

        rows.append(
            {
                "geometry": f"{key[0]}/{key[1]}",
                "direction": key[2],
                "case": rec["case"],
                "status": rec["status"],
                "gate_scope_version": rec["gate_scope_version"],
                "levels": rec["n_levels"],
                "saved_fields": rec["n_npz"],
                "fine_dx_nm": rec["fine_dx"],
                "K_fine_m3": f"{rec['K_fine']:.16e}",
                "coarse_to_mid_percent": f"{rec['c2m']:.8f}",
                "mid_to_fine_percent": f"{rec['m2f']:.8f}",
                "mid_to_fine_share_of_0.5pct": f"{100 * rec['m2f'] / LIMIT_GRID_MID_TO_FINE:.2f}",
                "fine_power_percent": f"{rec['power_fine']:.3e}",
                "fine_section_percent": f"{rec['section_fine']:.3e}",
                "fvm_anchor_percent": "" if rec["fvm_diff"] is None else f"{rec['fvm_diff']:.6f}",
                "openlb_vs_ref_percent": pt.get("OpenLB_vs_ref_percent", ""),
                "lc_vs_ref_percent": pt.get("LC_vs_ref_percent", ""),
                "v2_vs_ref_percent": pt.get("V2_vs_ref_percent", ""),
                "reference_role": ROLE.get(key, "survey grid point"),
                "verdict": "RECOMMEND_LIMITED_ADOPTION",
                "formal_status": "NOT_GRANTED",
            }
        )

    OUT.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with (OUT / "POINT_VERDICTS.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    with (OUT / "FEM_COVERAGE_scope_v2.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "h_nm", "d_nm", "direction", "case", "fem_status",
                "gate_scope_version", "fine_dx_nm", "fine_K_m3",
                "mid_to_fine_percent", "openlb_vs_fem_percent",
                "original_vs_fem_percent", "reference_role",
            ]
        )
        for row in sorted(rows, key=lambda r: (r["direction"], float(r["geometry"].split("/")[0]))):
            writer.writerow(
                [
                    row["geometry"].split("/")[0], row["geometry"].split("/")[1],
                    row["direction"], row["case"], row["status"],
                    row["gate_scope_version"], row["fine_dx_nm"], row["K_fine_m3"],
                    row["mid_to_fine_percent"], row["openlb_vs_ref_percent"],
                    row["lc_vs_ref_percent"], row["reference_role"],
                ]
            )

    print(f"wrote {len(rows)} point rows")
    groove = [r for r in rows if r["geometry"].split("/")[1] != "0"]
    print(f"groove points: {len(groove)}  flat self-tests: {len(rows) - len(groove)}")
    print(f"max mid->fine: {max(float(r['mid_to_fine_percent']) for r in groove):.8f}%")
    print("gate failures:", problems if problems else "none")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
