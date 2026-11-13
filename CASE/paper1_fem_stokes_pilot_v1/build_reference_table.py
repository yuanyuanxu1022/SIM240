#!/usr/bin/env python3
"""Build the "claim - reference - deviation" tables for Paper 1 closeout.

Every row carries four numbers for the same geometry and direction:

    OpenLB  : the LBM/OpenLB discrete result used by the manuscript
    LC      : the original local cubic law
    V2      : the fixed four-coefficient empirical correction (coefficients frozen)
    Kref    : an independent reference (FEM pilot if it passed internal checks,
              otherwise a qualified FVM value)

Nothing here re-fits, re-runs or re-grades anything.  V2 coefficients are used
as published.  The 36-row manuscript statistics are NOT recomputed: these tables
are a new, separately labelled comparison set.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
MAP36 = PROJECT / "docs/reports/SIM240_manuscript_revision_20261018/map36_evidence.csv"
FOUR_NEW = PROJECT / "docs/reports/PAPER1_new_four_cases_acceptance_20261107/comparison.csv"
OUT = PROJECT / "docs/reports/PAPER1_reference_table_20261113"

QUALIFIED_FVM_P = {
    (75, 100): 9.755622669730348e-23,
    (50, 120): 6.838617932100589e-23,
    (125, 120): 2.7840399124225664e-22,
}
QUALIFIED_FVM_T = {(75, 100): 4.340041663047474e-23}


def load_manuscript_rows():
    rows = {}
    with MAP36.open() as stream:
        for row in csv.DictReader(stream):
            key = (int(row["h_nm"]), int(row["d_nm"]), row["direction"])
            dns = float(row["K_DNS_m3"])
            rows[key] = {
                "OpenLB": dns,
                "LC": float(row["K_model_m3"]),
                "V2": dns * (1 + float(row["V2_rounded_residual_pct"]) / 100),
                "source": "map36_evidence.csv",
            }
    with FOUR_NEW.open() as stream:
        for row in csv.DictReader(stream):
            if row["role"] != "four_new":
                continue
            h, d = int(float(row["h_nm"])), int(float(row["d_nm"]))
            direction = "P" if row["component"] == "Kyy" else "T"
            key = (h, d, direction)
            if key in rows:
                continue
            rows[key] = {
                "OpenLB": float(row["K_LB_m3"]),
                "LC": float(row["K_LC_m3"]),
                "V2": float(row["K_V2_m3"]),
                "source": "comparison.csv (four_new)",
            }
    return rows


def fem_reference(h, d, direction):
    """Return (K, status) from the saved independent re-integration."""
    case = f"h{h}_d{d}_{direction}"
    path = ROOT / "results" / case / "VERIFICATION.json"
    if not path.exists():
        return None, "NO_FEM_RESULT"
    record = json.loads(path.read_text())
    fine = min(record["levels"], key=lambda r: r["dx_nm"])
    return fine["K_recomputed_m3"], record["status"]


def main():
    manuscript = load_manuscript_rows()
    OUT.mkdir(parents=True, exist_ok=True)

    point_rows = []
    for (h, d, direction), values in sorted(manuscript.items(), key=lambda kv: (kv[0][2], kv[0][0], kv[0][1])):
        k_fem, fem_status = fem_reference(h, d, direction)
        if k_fem is not None and fem_status == "PILOT_NUMERICAL_CHECKS_PASS":
            kref, ref_kind = k_fem, "FEM_pilot_internal_pass"
        elif direction == "P" and (h, d) in QUALIFIED_FVM_P:
            kref, ref_kind = QUALIFIED_FVM_P[(h, d)], "qualified_FVM"
        elif direction == "T" and (h, d) in QUALIFIED_FVM_T:
            kref, ref_kind = QUALIFIED_FVM_T[(h, d)], "qualified_FVM"
        else:
            kref, ref_kind = None, fem_status
        record = {
            "h_nm": h, "d_nm": d, "direction": direction,
            "reference_kind": ref_kind,
            "Kref_m3": "" if kref is None else f"{kref:.16e}",
            "OpenLB_m3": f"{values['OpenLB']:.16e}",
            "LC_m3": f"{values['LC']:.16e}",
            "V2_m3": f"{values['V2']:.16e}",
            "source": values["source"],
            "OpenLB_vs_ref_percent": "", "LC_vs_ref_percent": "", "V2_vs_ref_percent": "",
        }
        if kref is not None:
            for method in ("OpenLB", "LC", "V2"):
                record[f"{method}_vs_ref_percent"] = f"{(values[method] / kref - 1) * 100:.4f}"
        point_rows.append(record)

    fields = ["h_nm", "d_nm", "direction", "reference_kind", "Kref_m3",
              "OpenLB_m3", "LC_m3", "V2_m3",
              "OpenLB_vs_ref_percent", "LC_vs_ref_percent", "V2_vs_ref_percent", "source"]
    with (OUT / "POINT_TABLE.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(point_rows)

    pair_rows = []
    for h, d in sorted({(r["h_nm"], r["d_nm"]) for r in point_rows}):
        values = {direction: manuscript.get((h, d, direction)) for direction in ("P", "T")}
        if not all(values.values()):
            continue
        candidates = []
        k_fem_p, status_p = fem_reference(h, d, "P")
        k_fem_t, status_t = fem_reference(h, d, "T")
        if (k_fem_p is not None and status_p == "PILOT_NUMERICAL_CHECKS_PASS"
                and k_fem_t is not None and status_t == "PILOT_NUMERICAL_CHECKS_PASS"):
            candidates.append((k_fem_p, k_fem_t, "FEM-P + FEM-T (pilot; not qualified)"))
        if (h, d) in QUALIFIED_FVM_P and (h, d) in QUALIFIED_FVM_T:
            candidates.append((QUALIFIED_FVM_P[(h, d)], QUALIFIED_FVM_T[(h, d)],
                               "FVM-P + FVM-T (both qualified)"))
        if (h, d) in QUALIFIED_FVM_P and k_fem_t is not None \
                and status_t == "PILOT_NUMERICAL_CHECKS_PASS":
            candidates.append((QUALIFIED_FVM_P[(h, d)], k_fem_t,
                               "FVM-P (qualified) + FEM-T (pilot)"))
        for kp_ref, kt_ref, label in candidates:
            row = {
                "geometry": f"h{h}/d{d}",
                "reference_kind": label,
                "Kref_P_m3": f"{kp_ref:.16e}", "Kref_T_m3": f"{kt_ref:.16e}",
                "A_ref": f"{kp_ref / kt_ref:.10f}",
                "beta_ref_deg": f"{math.degrees(math.atan2(kt_ref, kp_ref)):.6f}",
            }
            ref_a = kp_ref / kt_ref
            ref_beta = math.degrees(math.atan2(kt_ref, kp_ref))
            for method in ("OpenLB", "LC", "V2"):
                kp_m = values["P"][method]
                kt_m = values["T"][method]
                a = kp_m / kt_m
                beta = math.degrees(math.atan2(kt_m, kp_m))
                row[f"A_{method}"] = f"{a:.10f}"
                row[f"beta_{method}_deg"] = f"{beta:.6f}"
                row[f"{method}_A_vs_ref_percent"] = f"{(a / ref_a - 1) * 100:.4f}"
                row[f"{method}_beta_vs_ref_deg"] = f"{beta - ref_beta:.4f}"
            pair_rows.append(row)

    pair_fields = ["geometry", "reference_kind", "Kref_P_m3", "Kref_T_m3", "A_ref", "beta_ref_deg"]
    for method in ("OpenLB", "LC", "V2"):
        pair_fields += [f"A_{method}", f"beta_{method}_deg",
                        f"{method}_A_vs_ref_percent", f"{method}_beta_vs_ref_deg"]
    with (OUT / "PAIR_TABLE.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=pair_fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(pair_rows)

    with_reference = [r for r in point_rows if r["OpenLB_vs_ref_percent"]]
    print(f"points with a reference: {len(with_reference)} / {len(point_rows)}")
    for direction in ("P", "T"):
        group = [r for r in with_reference if r["direction"] == direction]
        if not group:
            continue
        for method in ("OpenLB", "LC", "V2"):
            vals = [float(r[f"{method}_vs_ref_percent"]) for r in group]
            abss = [abs(v) for v in vals]
            print(f"  {direction} {method:<7} n={len(vals):>3} "
                  f"max|d|={max(abss):>8.4f}%  mean|d|={sum(abss)/len(abss):>8.4f}%  "
                  f">2%={sum(1 for v in abss if v > 2):>3}  "
                  f"all_positive={all(v > 0 for v in vals)}")
    print(f"pairs: {len(pair_rows)}")


if __name__ == "__main__":
    main()
