#!/usr/bin/env python3
"""Compare paired principal conductances without changing the 36-row statistics."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT = ROOT.parent.parent / "docs/reports/PAPER1_conclusion_FVM_FEM_pilot_20261113"
MAP36 = ROOT.parent.parent / "docs/reports/SIM240_manuscript_revision_20261018/map36_evidence.csv"
FVM_P = {
    (75, 100): 9.755622669730348e-23,
    (50, 120): 6.838617932100589e-23,
}
FVM_T = {(75, 100): 4.340041663047474e-23}


def load_map():
    with MAP36.open() as stream:
        rows = list(csv.DictReader(stream))
    out = {}
    for row in rows:
        key = (int(row["h_nm"]), int(row["d_nm"]), row["direction"])
        dns = float(row["K_DNS_m3"])
        out[key] = {
            "OpenLB": dns,
            "LC": float(row["K_model_m3"]),
            "V2": dns * (1 + float(row["V2_rounded_residual_pct"]) / 100),
            "result_path": row["result_path"],
            "result_sha256": row["result_sha256"],
        }
    return out


def one_pair(h, d, kp, kt, reference_kind, map36):
    p, t = map36[(h, d, "P")], map36[(h, d, "T")]
    ref = {"P": kp, "T": kt}
    out = {"geometry": f"h{h}/d{d}", "reference_kind": reference_kind,
           "Kref_P_m3": kp, "Kref_T_m3": kt, "Aref": kp / kt}
    for method in ["OpenLB", "LC", "V2"]:
        for direction in ["P", "T"]:
            value = (p if direction == "P" else t)[method]
            out[f"{method}_{direction}_m3"] = value
            out[f"{method}_{direction}_delta_percent"] = (value / ref[direction] - 1) * 100
        kp_m, kt_m = p[method], t[method]
        out[f"A_{method}"] = kp_m / kt_m
        out[f"beta_{method}_deg"] = math.degrees(math.atan2(kt_m, kp_m))
    out["beta_ref_deg"] = math.degrees(math.atan2(kt, kp))
    out["LC_A_overestimate_percent"] = (out["A_LC"] / out["Aref"] - 1) * 100
    out["LC_beta_difference_deg"] = out["beta_LC_deg"] - out["beta_ref_deg"]
    out["source_P"] = p
    out["source_T"] = t
    return out


def main():
    map36 = load_map()
    rows = [one_pair(75, 100, FVM_P[(75, 100)], FVM_T[(75, 100)],
                     "qualified_FVM_pair", map36)]
    verification_path = ROOT / "results/h50_d120_T/VERIFICATION.json"
    if verification_path.exists():
        verification = json.loads(verification_path.read_text())
        if verification["status"] != "PILOT_NUMERICAL_CHECKS_PASS":
            raise ValueError("h50T has not passed independent pilot checks")
        fine = min(verification["levels"], key=lambda r: r["dx_nm"])
        rows.append(one_pair(50, 120, FVM_P[(50, 120)], fine["K_recomputed_m3"],
                             "FEM_T_pilot_plus_qualified_FVM_P_NOT_FORMALLY_QUALIFIED", map36))
    REPORT.mkdir(parents=True, exist_ok=True)
    (REPORT / "PAIR_COMPARISON.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    fields = ["geometry", "reference_kind", "Kref_P_m3", "Kref_T_m3", "Aref",
              "A_OpenLB", "A_LC", "A_V2", "beta_ref_deg", "beta_OpenLB_deg",
              "beta_LC_deg", "beta_V2_deg", "LC_A_overestimate_percent",
              "LC_beta_difference_deg", "OpenLB_P_delta_percent",
              "OpenLB_T_delta_percent", "LC_P_delta_percent", "LC_T_delta_percent",
              "V2_P_delta_percent", "V2_T_delta_percent"]
    with (REPORT / "PAIR_COMPARISON.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(rows, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
