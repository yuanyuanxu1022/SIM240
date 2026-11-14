#!/usr/bin/env python3
"""Descriptive two-factor trend analysis on the FEM/FVM reference set (19 geometries).

Purpose
-------
The 2026-11-13 descriptive-trends report used the original 36-record set whose
reference is the 5 nm OpenLB discretisation itself. The 2026-11-14 FEM package
gives 36 direction comparisons against an independent discretisation for
19 geometries, of which 15 form a balanced 3x5 matrix with BOTH directions.

This script recomputes exactly the same descriptive quantities on the new set,
using the same equal-weight sums-of-squares wording as the earlier report, and
first re-produces the published old-set shares as a check on the method.

No simulation is started, no threshold is changed, no V2 coefficient is refitted.
"""

import csv
import json
import math
from pathlib import Path

ROOT = Path("/home/dell/yuanyuanxu/SIM240")
OLD = ROOT / "docs/reports/PAPER1_V2_coefficient_choice_audit_20261110/fixed_V2_primary36_checked.csv"
NEW = ROOT / "docs/reports/PAPER1_fem_v2_results_20261114/PAIR_TABLE_v2.csv"
OUT = ROOT / "docs/reports/PAPER1_fem_v2_doe_20261114"

H_LEVELS = [50.0, 75.0, 125.0]
D_LEVELS = [25.0, 50.0, 75.0, 100.0, 120.0]


def ss_shares(cells):
    """Equal-weight descriptive decomposition on a complete 3x5 grid.

    cells: {(h, d): value}.  Returns shares of SS_h, SS_d, interaction remainder.
    """
    vals = list(cells.values())
    n = len(vals)
    grand = sum(vals) / n
    ss_tot = sum((v - grand) ** 2 for v in vals)
    ss_h = sum(
        len(D_LEVELS) * (sum(cells[(h, d)] for d in D_LEVELS) / len(D_LEVELS) - grand) ** 2
        for h in H_LEVELS
    )
    ss_d = sum(
        len(H_LEVELS) * (sum(cells[(h, d)] for h in H_LEVELS) / len(H_LEVELS) - grand) ** 2
        for d in D_LEVELS
    )
    ss_int = ss_tot - ss_h - ss_d
    return {
        "grand_mean": grand,
        "ss_total": ss_tot,
        "share_h_percent": 100.0 * ss_h / ss_tot,
        "share_d_percent": 100.0 * ss_d / ss_tot,
        "share_interaction_percent": 100.0 * ss_int / ss_tot,
        "marginal_h": {h: sum(cells[(h, d)] for d in D_LEVELS) / len(D_LEVELS) for h in H_LEVELS},
        "marginal_d": {d: sum(cells[(h, d)] for h in H_LEVELS) / len(H_LEVELS) for d in D_LEVELS},
    }


def old_cells():
    """Old set: V2 signed residual, balanced h>=50 matrix."""
    rows = list(csv.DictReader(OLD.open()))
    out = {}
    for r in rows:
        h, d = float(r["h_nm"]), float(r["d_nm"])
        if h in H_LEVELS and d in D_LEVELS:
            out[(r["direction"], h, d)] = float(r["V2_residual_percent"])
    return out


def new_rows():
    return list(csv.DictReader(NEW.open()))


def parse_geom(g):
    h, d = g.split("/")
    return float(h[1:]), float(d[1:])


def main():
    result = {}

    # --- 1. reproduce the published old-set decomposition -------------------
    oc = old_cells()
    old_pub = {}
    for direction, pub in (("P", (87.65, 0.77, 11.58)), ("T", (40.08, 30.52, 29.40))):
        cells = {(h, d): oc[(direction, h, d)] for h in H_LEVELS for d in D_LEVELS}
        res = ss_shares(cells)
        old_pub[direction] = {
            "recomputed": [round(res["share_h_percent"], 2),
                           round(res["share_d_percent"], 2),
                           round(res["share_interaction_percent"], 2)],
            "published": list(pub),
        }
    result["old_set_reproduction"] = old_pub

    # --- 2. new set: build cells -------------------------------------------
    rows = new_rows()
    table = {}
    for r in rows:
        h, d = parse_geom(r["geometry"])
        row = {}
        for k, v in r.items():
            if k == "geometry":
                row[k] = v
                continue
            try:
                row[k] = float(v) if v not in ("", None) else None
            except ValueError:
                row[k] = v  # source labels such as qualified_FVM
        table[(h, d)] = row

    balanced = [k for k in table if k[0] in H_LEVELS and k[1] in D_LEVELS]
    result["counts"] = {
        "geometries_total": len(table),
        "balanced_15": len(balanced),
        "balanced_with_both_directions": sum(
            1 for k in balanced
            if table[k]["P_LC_vs_ref_percent"] is not None and table[k]["T_LC_vs_ref_percent"] is not None
        ),
        "h25_points": sorted(k[1] for k in table if k[0] == 25.0),
        "h100_points": sorted(k[1] for k in table if k[0] == 100.0),
    }

    # --- 3. new set: four decompositions -----------------------------------
    responses = {
        "LC_P": "P_LC_vs_ref_percent",
        "V2_P": "P_V2_vs_ref_percent",
        "LC_T": "T_LC_vs_ref_percent",
        "V2_T": "T_V2_vs_ref_percent",
    }
    new_dec = {}
    for name, key in responses.items():
        cells = {k: table[k][key] for k in balanced}
        assert all(v is not None for v in cells.values()), name
        new_dec[name] = ss_shares(cells)
    result["new_set_decomposition"] = new_dec

    # --- 4. new set: per-h and per-d profile tables ------------------------
    profile = {}
    for name, key in responses.items():
        profile[name] = {
            "by_h": {
                str(int(h)): [table[(h, d)][key] for d in D_LEVELS] for h in H_LEVELS
            },
            "by_d": {
                str(int(d)): [table[(h, d)][key] for h in H_LEVELS] for d in D_LEVELS
            },
        }
    result["profiles"] = profile

    # --- 5. checks that the earlier report made ----------------------------
    checks = {}

    # 5a LC along-groove deviation rises with d at fixed h
    rise = {}
    for h in H_LEVELS:
        seq = [table[(h, d)]["P_LC_vs_ref_percent"] for d in D_LEVELS]
        rise[str(int(h))] = {
            "sequence": seq,
            "monotone_increasing": all(seq[i] < seq[i + 1] for i in range(len(seq) - 1)),
        }
    checks["LC_P_increases_with_d"] = rise

    # 5b the h25 -> h50 reversal at d = 100 (the counter-example kept in the paper)
    d100 = {str(int(h)): table[(h, 100.0)]["P_LC_vs_ref_percent"]
            for h in (25.0, 50.0, 75.0, 125.0)}
    checks["LC_P_d100_sequence_h25_to_h125"] = d100
    checks["LC_P_d100_reversal_holds"] = d100["25"] < d100["50"] > d100["75"] > d100["125"]

    # 5c V2 along-groove marginal sign change between h=75 and h=125
    mh = new_dec["V2_P"]["marginal_h"]
    checks["V2_P_marginal_h"] = {str(int(k)): mh[k] for k in H_LEVELS}
    checks["V2_P_sign_change_between_75_125"] = mh[75.0] > 0 > mh[125.0]
    checks["V2_P_all_d_positive_at_75"] = all(
        table[(75.0, d)]["P_V2_vs_ref_percent"] > 0 for d in D_LEVELS
    )
    checks["V2_P_all_d_negative_at_125"] = all(
        table[(125.0, d)]["P_V2_vs_ref_percent"] < 0 for d in D_LEVELS
    )

    # 5d V2 transverse residual has no clean monotone relation
    checks["V2_T_by_d_ranges"] = {
        str(int(d)): [table[(h, d)]["T_V2_vs_ref_percent"] for h in H_LEVELS]
        for d in D_LEVELS
    }

    # 5e LC transverse increases with d at fixed h?
    trise = {}
    for h in H_LEVELS:
        seq = [table[(h, d)]["T_LC_vs_ref_percent"] for d in D_LEVELS]
        trise[str(int(h))] = {
            "sequence": seq,
            "monotone_increasing": all(seq[i] < seq[i + 1] for i in range(len(seq) - 1)),
            "non_decreasing": all(seq[i] <= seq[i + 1] for i in range(len(seq) - 1)),
        }
    checks["LC_T_increases_with_d"] = trise

    # 5f sign counts on the 15 balanced points
    counts = {}
    for name, key in responses.items():
        vals = [table[k][key] for k in balanced]
        counts[name] = {"positive": sum(1 for v in vals if v > 0),
                        "negative": sum(1 for v in vals if v < 0),
                        "min": min(vals), "max": max(vals),
                        "mean": sum(vals) / len(vals)}
    checks["balanced_sign_counts"] = counts

    # 5g how much of the reference is FEM vs FVM inside the balanced matrix
    src = {}
    for d in D_LEVELS:
        for h in H_LEVELS:
            key = (h, d)
            for col in ("K_P_source", "K_T_source"):
                src.setdefault(col, {}).setdefault(table[key][col], 0)
                src[col][table[key][col]] += 1
    checks["reference_sources_in_balanced_matrix"] = src

    result["checks"] = checks

    # --- 6. parameter sweep if the print tolerance is chosen --------------
    sweep = {}
    for pa in (1e-12, 1e-11, 1e-10, 5e-10):
        row = {}
        for name, key in responses.items():
            vals = [table[k][key] for k in balanced]
            row[name] = sum(1 for v in vals if abs(v) <= pa * 100.0)
        sweep[f"abs_le_{pa:g}"] = row
    result["tolerance_sweep"] = sweep

    # write
    (OUT / "DOE_V2_NEW_REFERENCE.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # machine-readable per-point table for the balanced matrix
    with (OUT / "DOE_V2_NEW_REFERENCE_15.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["h_nm", "d_nm", "d_over_h", "source_P", "source_T",
                    "LC_P_percent", "V2_P_percent", "LC_T_percent", "V2_T_percent",
                    "OpenLB_T_vs_ref_percent"])
        for h in H_LEVELS:
            for d in D_LEVELS:
                t = table[(h, d)]
                w.writerow([f"{h:.0f}", f"{d:.0f}", f"{d / h:.4f}",
                            t["K_P_source"], t["K_T_source"],
                            f"{t['P_LC_vs_ref_percent']:.6f}",
                            f"{t['P_V2_vs_ref_percent']:.6f}",
                            f"{t['T_LC_vs_ref_percent']:.6f}",
                            f"{t['T_V2_vs_ref_percent']:.6f}",
                            f"{t['T_OpenLB_vs_ref_percent']:.6f}"])

    # console summary
    print("== old-set reproduction (h share, d share, interaction) ==")
    for k, v in old_pub.items():
        print(f"  {k}: recomputed {v['recomputed']}  published {v['published']}")
    print("== new-set decomposition ==")
    for k, v in new_dec.items():
        print(f"  {k}: h {v['share_h_percent']:.2f}  d {v['share_d_percent']:.2f}  "
              f"int {v['share_interaction_percent']:.2f}  grand {v['grand_mean']:+.4f}")
        print(f"      marginal h: " + "  ".join(f"{h:.0f}:{v['marginal_h'][h]:+.4f}" for h in H_LEVELS))
        print(f"      marginal d: " + "  ".join(f"{d:.0f}:{v['marginal_d'][d]:+.4f}" for d in D_LEVELS))
    print("== checks ==")
    for k, v in checks.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
