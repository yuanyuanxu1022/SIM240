#!/usr/bin/env python3
"""Assemble the assessment table and, optionally, the 19-geometry pair table.

Nothing here changes a verdict. The assessor re-reads receipts, checks that the
solve receipt still has the digest the verifier consumed, and reports the
classification that ``acceptance_rule.json`` implies. A case with no receipt is
reported as NOT_RUN rather than being omitted.

Usage
    python3 assess.py
    python3 assess.py --pairs
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys

import receipt

ASSESS_JSON = receipt.PACKAGE / "ASSESSMENT.json"
ASSESS_CSV = receipt.PACKAGE / "ASSESSMENT.csv"
PAIR_CSV = receipt.PACKAGE / "PAIR_TABLE_v2.csv"
DEFAULT_POINT_TABLE = (receipt.PACKAGE.parent.parent / "docs" / "reports"
                       / "PAPER1_reference_table_20261113" / "POINT_TABLE.csv")

FIELDS = ["case", "h_nm", "d_nm", "direction", "run_id", "solve_state",
          "wall_seconds", "peak_rss_kb", "K_fine_m3", "mid_to_fine_percent",
          "power_fine_percent", "section_fine_percent", "gate_scope",
          "receipt_intact", "reference_status", "numeric_verdict",
          "assess_problems", "multiple_attempts", "attempt_count",
          "actual_stop_reason"]


def classify(case: str, solve, verify, directory) -> tuple:
    """Recompute the label from the saved fields and the frozen rule.

    Returns (label, numeric_verdict, problems). The verifier's own word is never
    the label; it is only cross-checked. A receipt without reconstructible fields
    can never reach REFERENCE_CANDIDATE.
    """
    problems = []
    solved = [lvl for lvl in solve.get("levels", []) if lvl.get("state") == "SOLVED"]
    planned = solve.get("planned_levels_nm", [])
    if solve.get("state") != "SOLVED":
        return "SOLVE_INCOMPLETE", "NOT_EVALUATED", [f"solve state {solve.get('state')}"]
    if not solved or len(solved) != len(planned):
        return "SOLVE_INCOMPLETE", "NOT_EVALUATED", ["planned levels not all solved"]
    if verify is None:
        return "SOLVED_NOT_VERIFIED", "NOT_EVALUATED", ["no verification receipt"]
    if not (receipt.RESULTS / case).is_dir():
        return "NOT_RECONSTRUCTIBLE", "NOT_EVALUATED", [
            "results directory is absent, so no gate can be recomputed from fields"]
    import verify_results
    import verify_one
    try:
        verification = verify_results.verify_case(case)
    except Exception as error:  # noqa: BLE001 - one bad case must not void the table
        return "NOT_RECONSTRUCTIBLE", "NOT_EVALUATED", [
            f"fields under results/{case} could not be re-integrated: "
            f"{type(error).__name__}: {error}"]
    gates = verify_one.additive_problems(verification) + list(
        verification.get("problems", []))
    if gates:
        return "LOCAL_CHECKS_FAIL", "FAIL", gates
    # numeric pass; now the provenance chain, item by item
    if verify.get("schema") != receipt.SCHEMA_VERIFY:
        problems.append("verification receipt schema mismatch")
    if verify.get("solve_receipt_sha256") != receipt.sha256_file(
            directory / "SOLVE_RECEIPT.json"):
        problems.append("solve receipt digest differs from the verified one")
    if verify.get("solve_receipt_unchanged") is not True:
        problems.append("verifier did not confirm an unchanged solve receipt")
    if verify.get("release_sha256") != receipt.release_digest():
        problems.append("verification was done under a different release")
    if verify.get("numeric_verdict") != "PASS":
        problems.append("verifier did not record a numeric pass")
    if solve.get("exit_code") != 0:
        problems.append(f"solve exit_code is {solve.get('exit_code')}, not 0")
    for level in solved:
        if not receipt.level_json_matches(case, level):
            problems.append(f"dx={level['dx_nm']:g}: mesh JSON hash differs")
    # the verifier's numbers must match the recomputation
    by_dx = {row["dx_nm"]: row for row in verification.get("levels", [])}
    for row in verify.get("levels", []):
        again = by_dx.get(row["dx_nm"])
        if again is None:
            problems.append(f"dx={row['dx_nm']:g}: verified level is not reproducible")
            continue
        for key in ("K_recomputed_m3", "power_balance_recomputed_percent",
                    "section_flux_spread_percent"):
            theirs, mine = row.get(key), again.get(key)
            if theirs is None or mine is None:
                continue
            if abs(float(theirs) - float(mine)) > 1e-9 * max(1.0, abs(float(mine))):
                problems.append(f"dx={row['dx_nm']:g}: {key} differs from recomputation")
    if verify.get("gate_scope_version") != verification.get("gate_scope_version"):
        problems.append("gate scope version differs from the recomputed one")
    if problems:
        return "PROVENANCE_INCOMPLETE", "PASS", problems
    return "REFERENCE_CANDIDATE", "PASS", []


def collect(case: str, point: dict) -> dict:
    row = {"case": case, "h_nm": point.get("h_nm"), "d_nm": point.get("d_nm"),
           "direction": point.get("direction", "T"), "run_id": None,
           "solve_state": "NOT_RUN", "receipt_intact": None,
           "reference_status": "NOT_RUN", "numeric_verdict": "NOT_EVALUATED",
           "assess_problems": "", "multiple_attempts": False, "attempt_count": 0}
    directories = receipt.case_run_dirs(case)
    if not directories:
        return row
    row["attempt_count"] = len(directories)
    row["multiple_attempts"] = len(directories) > 1
    directory = directories[-1]
    try:
        solve = json.loads((directory / "SOLVE_RECEIPT.json").read_text())
    except Exception as error:  # noqa: BLE001 - a corrupt receipt is a real outcome
        row["reference_status"] = "SOLVE_INCOMPLETE"
        row["numeric_verdict"] = "NOT_EVALUATED"
        row["assess_problems"] = (f"solve receipt unreadable: "
                                  f"{type(error).__name__}: {error}")
        row["actual_stop_reason"] = row["assess_problems"]
        return row
    row.update({"run_id": solve.get("run_id"), "solve_state": solve.get("state"),
                "wall_seconds": solve.get("wall_seconds"),
                "peak_rss_kb": solve.get("peak_rss_kb")})

    solved = [lvl for lvl in solve.get("levels", []) if lvl.get("state") == "SOLVED"]
    if solved:
        fine = min(solved, key=lambda lvl: lvl["dx_nm"])
        row["K_fine_m3"] = fine["K_m3"]
        row["power_fine_percent"] = fine.get("power_balance_percent")
        row["section_fine_percent"] = max(fine.get("section_flux_spread_percent") or 0.0,
                                          fine.get("section_vs_volume_percent") or 0.0)
        ordered = sorted(solved, key=lambda lvl: -lvl["dx_nm"])
        if len(ordered) > 1:
            row["mid_to_fine_percent"] = abs(
                ordered[-1]["K_m3"] / ordered[-2]["K_m3"] - 1) * 100

    verify_path = directory / "VERIFY_RECEIPT.json"
    verify = None
    if verify_path.exists():
        try:
            verify = json.loads(verify_path.read_text())
        except Exception:  # noqa: BLE001 - treated as absent, never as a pass
            verify = None
    if verify is not None:
        row["gate_scope"] = verify.get("gate_scope_version")
        row["receipt_intact"] = (receipt.sha256_file(directory / "SOLVE_RECEIPT.json")
                                 == verify.get("solve_receipt_sha256"))
    label, verdict, problems = classify(case, solve, verify, directory)
    row["reference_status"] = label
    row["numeric_verdict"] = verdict
    row["assess_problems"] = "; ".join(problems)
    row["actual_stop_reason"] = problems[0] if problems else ""
    return row


def assessment() -> int:
    points = receipt.load_points()
    rows = [collect(p["case"], p) for p in points["points"]]
    counts = {}
    for row in rows:
        counts[row["reference_status"]] = counts.get(row["reference_status"], 0) + 1
    payload = {
        "assembled_at": receipt.utcnow(),
        "release_sha256": (receipt.release_digest()
                           if receipt.MANIFEST_PATH.exists() else None),
        "counts": counts,
        "rows": rows,
        "note": "Every label except NOT_RUN is recomputed by this assessor from the "
                "saved fields and the frozen rule; the verifier's own label is only "
                "cross-checked. No label here grants a formal reference.",
    }
    receipt.atomic_write_json(ASSESS_JSON, payload)
    temporary = ASSESS_CSV.with_name(ASSESS_CSV.name + ".tmp")
    with temporary.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction="ignore",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(ASSESS_CSV)
    print(json.dumps({"counts": counts, "csv": str(ASSESS_CSV)}, indent=2,
                     ensure_ascii=False))
    return 0


def load_point_table(path) -> dict:
    table = {}
    with open(path, newline="") as stream:
        for row in csv.DictReader(stream):
            key = (int(float(row["h_nm"])), int(float(row["d_nm"])), row["direction"])
            table[key] = row
    return table


def as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def beta_deg(k_along: float, k_cross: float) -> float:
    """Reconstructed 45-degree mean-flow angle: beta = atan(K_T / K_P)."""
    return math.degrees(math.atan(k_cross / k_along))


def pairs() -> int:
    parser_path = DEFAULT_POINT_TABLE
    if not parser_path.exists():
        print(f"point table not found: {parser_path}")
        return receipt.EXIT_BAD_INPUT
    table = load_point_table(parser_path)
    geometries = sorted({(h, d) for (h, d, _direction) in table})
    new_runs = {}
    for point in receipt.load_points()["points"]:
        row = collect(point["case"], point)
        if row.get("K_fine_m3"):
            new_runs[(int(point["h_nm"]), int(point["d_nm"]))] = row

    out = []
    for h, d in geometries:
        p = table.get((h, d, "P"), {})
        t = table.get((h, d, "T"), {})
        k_p = as_float(p.get("Kref_m3"))
        k_t = as_float(t.get("Kref_m3"))
        source_t = "POINT_TABLE reference" if k_t else ""
        if (h, d) in new_runs:
            k_t = new_runs[(h, d)]["K_fine_m3"]
            source_t = f"FEM v2 run {new_runs[(h, d)]['run_id']}"
        source_p = p.get("reference_kind", "")
        o_p, o_t = as_float(p.get("OpenLB_m3")), as_float(t.get("OpenLB_m3"))
        lc_p, lc_t = as_float(p.get("LC_m3")), as_float(t.get("LC_m3"))
        v2_p, v2_t = as_float(p.get("V2_m3")), as_float(t.get("V2_m3"))

        row = {
            "geometry": f"h{h}/d{d}",
            "K_P_m3": k_p, "K_P_source": source_p,
            "K_T_m3": k_t, "K_T_source": source_t,
            "A_ref": (k_p / k_t) if (k_p and k_t) else None,
            "beta_ref_deg": (beta_deg(k_p, k_t) if (k_p and k_t) else None),
            "A_OpenLB": (o_p / o_t) if (o_p and o_t) else None,
            "A_LC": (lc_p / lc_t) if (lc_p and lc_t) else None,
            "A_V2": (v2_p / v2_t) if (v2_p and v2_t) else None,
            "P_LC_vs_ref_percent": (as_float(p.get("LC_vs_ref_percent"))),
            "P_V2_vs_ref_percent": (as_float(p.get("V2_vs_ref_percent"))),
            "T_LC_vs_ref_percent": (None if not (lc_t and k_t)
                                    else (lc_t / k_t - 1) * 100),
            "T_V2_vs_ref_percent": (None if not (v2_t and k_t)
                                    else (v2_t / k_t - 1) * 100),
            "T_OpenLB_vs_ref_percent": (None if not (o_t and k_t)
                                        else (o_t / k_t - 1) * 100),
        }
        if row["A_ref"] and row["A_LC"]:
            row["LC_A_vs_ref_percent"] = (row["A_LC"] / row["A_ref"] - 1) * 100
        if row["A_ref"] and row["A_V2"]:
            row["V2_A_vs_ref_percent"] = (row["A_V2"] / row["A_ref"] - 1) * 100
        if row["beta_ref_deg"] is not None and row["A_LC"] and row["A_V2"]:
            row["LC_beta_vs_ref_deg"] = beta_deg(1.0, 1.0 / row["A_LC"]) - row["beta_ref_deg"]
            row["V2_beta_vs_ref_deg"] = beta_deg(1.0, 1.0 / row["A_V2"]) - row["beta_ref_deg"]
        out.append(row)

    fields = ["geometry", "K_P_m3", "K_P_source", "K_T_m3", "K_T_source",
              "A_ref", "beta_ref_deg", "A_OpenLB", "A_LC", "A_V2",
              "P_LC_vs_ref_percent", "P_V2_vs_ref_percent",
              "T_LC_vs_ref_percent", "T_V2_vs_ref_percent",
              "T_OpenLB_vs_ref_percent", "LC_A_vs_ref_percent",
              "V2_A_vs_ref_percent", "LC_beta_vs_ref_deg", "V2_beta_vs_ref_deg"]
    temporary = PAIR_CSV.with_name(PAIR_CSV.name + ".tmp")
    with temporary.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(out)
    temporary.replace(PAIR_CSV)

    complete = sum(1 for row in out if row["A_ref"])
    print(json.dumps({
        "geometries": len(out),
        "with_both_directions": complete,
        "direction_comparisons": len(out) * 2,
        "point_table_sha256": receipt.sha256_file(parser_path),
        "csv": str(PAIR_CSV),
        "note": "A_ref and beta are only filled where both directions have a "
                "reference; formula predictions are reported without being called "
                "correct. P and T may come from different packages; see the source "
                "columns.",
    }, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", action="store_true")
    args = parser.parse_args()
    return pairs() if args.pairs else assessment()


if __name__ == "__main__":
    sys.exit(main())
