#!/usr/bin/env python3
"""Reproducible fit of the V2 correction factors for the groove closure error.

Purpose
-------
The manuscript reports two dimensionless correction factors applied to the
arithmetic/harmonic closure of Eq. (1):

    F_parallel = 1 / (1 + a_p * (d/w)^b_p)
    F_perp     = 1 / (1 + a_t * (d/w)^b_t)

Both are functions of the groove aspect ratio d/w alone.  This script
regenerates every coefficient and every residual quoted in the paper, so the
fit does not have to be taken on trust.

Data
----
Read from the result CSVs written by run_matrix.sh / run_d75_validation.sh /
run_h25_path.sh / run_d120_aspect.sh.  Only dx = 5 nm production runs are used.

Calibration set (fixed before fitting, never changed):
    d in {25, 50, 100} nm  x  h in {50, 75, 125} nm   -> 9 geometries,
    both principal directions -> 18 residuals.

Everything else is a hold-out and is reported but never enters the objective:
    d = 75 nm  (3 gaps)  : withheld depth, never in the calibration set
    d = 120 nm (3 gaps)  : aspect-ratio boundary, d/w = 1
    h = 25 nm  (3 depths) : lower-gap boundary

Objective
---------
The paper quotes a bound on the absolute residual, so the fit minimises the
maximum absolute residual (minimax), not the sum of squares.  The RMS fit is
also computed and reported, as a check that the improvement comes from the
change of independent variable rather than from the choice of objective.

Outputs
-------
  results/analysis/v2_fit_params.csv        fitted coefficients, both objectives
  results/analysis/v2_residuals.csv         per-geometry residual, all 18 + hold-outs
  results/analysis/V2_FIT_REPORT.md         human-readable summary

Run:  python3 analysis_fit_v2.py
"""

import csv
import os
import sys

import numpy as np
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
ANA = os.path.join(RES, "analysis")

W = 120.0  # groove width, nm (fixed by the mask; P = 240 nm, w = 120 nm)
P = 240.0

CALIB_D = (25.0, 50.0, 100.0)
CALIB_H = (50.0, 75.0, 125.0)


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------
def closure_K(h, d, along):
    """Arithmetic (along) / harmonic (across) average of the cubic conductance."""
    hg, hl = h + d, h
    if along:
        v = (hg ** 3 + hl ** 3) / 2.0
    else:
        v = 2.0 / (1.0 / hg ** 3 + 1.0 / hl ** 3)
    return v / 12.0 * 1e-27  # m^3 per unit width


def load_runs():
    """Return {(h, d, 'P'|'T'): K_DNS in m^3} for all dx = 5 nm production runs."""
    K = {}

    with open(os.path.join(RES, "summary.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("dx_nm") != "5":
                continue
            K[(float(r["h_nm"]), float(r["d_nm"]), r["direction"])] = float(r["Keff_m3"])

    for fn in ("d75_summary.csv", "h25_summary.csv", "d120_summary.csv"):
        path = os.path.join(RES, fn)
        if not os.path.exists(path):
            sys.exit(f"missing {path}")
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                # these files carry case_id, not direction
                dr = "P" if r["case_id"].split("-")[1] == "P" else "T"
                K[(float(r["h_nm"]), float(r["d_nm"]), dr)] = float(r["Keff_m3"])

    if len(K) != 36:
        sys.exit(f"expected 36 principal-direction runs, found {len(K)}")
    return K


# --------------------------------------------------------------------------
# model
# --------------------------------------------------------------------------
def factor(d, a, b):
    return 1.0 / (1.0 + a * (d / W) ** b)


def residuals(K, a, b, along, keys):
    out = []
    for key in keys:
        h, d = key[0], key[1]
        Km = closure_K(h, d, along)
        Kd = K[key]
        out.append((Km * factor(d, a, b) - Kd) / Kd * 100.0)
    return np.array(out)


def fit(K, along):
    """Fit (a, b) on the calibration set.  Returns dict of both objectives."""
    keys = [(h, d, "P" if along else "T")
            for d in CALIB_D for h in CALIB_H]
    missing = [k for k in keys if k not in K]
    if missing:
        sys.exit(f"calibration keys missing from data: {missing}")

    def obj_minimax(p):
        if p[0] <= 0 or p[1] <= 0:
            return 1e6
        return float(np.max(np.abs(residuals(K, p[0], p[1], along, keys)))) 

    def obj_rms(p):
        if p[0] <= 0 or p[1] <= 0:
            return 1e9
        return float(np.sum(residuals(K, p[0], p[1], along, keys) ** 2))

    def best_of(objective, starts):
        best = None
        for a0, b0 in starts:
            r = minimize(objective, [a0, b0], method="Nelder-Mead",
                         options={"xatol": 1e-10, "fatol": 1e-12,
                                  "maxiter": 40000, "maxfev": 40000})
            if best is None or r.fun < best.fun:
                best = r
        # refine from the best point
        r = minimize(objective, best.x, method="Nelder-Mead",
                     options={"xatol": 1e-12, "fatol": 1e-14,
                              "maxiter": 40000, "maxfev": 40000})
        return r.x if r.fun <= best.fun else best.x

    starts = [(a0, b0) for a0 in (0.2, 0.5, 1.0, 1.8, 3.0)
              for b0 in (0.6, 1.0, 1.5, 2.0, 2.5)]
    p_mm = best_of(obj_minimax, starts)
    p_rms = best_of(obj_rms, starts)
    return {"minimax": p_mm, "rms": p_rms, "keys": keys}


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    K = load_runs()

    # every principal-direction geometry present, split into sets
    all_keys = sorted({(k[0], k[1]) for k in K})
    calib_set = {(h, d) for d in CALIB_D for h in CALIB_H}
    groups = {
        "calibration (fit)": [(h, d) for (h, d) in all_keys if (h, d) in calib_set],
        "holdout d=75": [(h, d) for (h, d) in all_keys if d == 75.0],
        "boundary d=120": [(h, d) for (h, d) in all_keys if d == 120.0],
        "lower gap h=25": [(h, d) for (h, d) in all_keys if h == 25.0],
    }

    # The two factors are quoted over different gap ranges: the perp residual
    # degrades sharply at h = 25 nm (thin-film resistance dominates there), so
    # the perp factor is restricted to h >= 50 nm.  Report the bound over the
    # range each factor is actually claimed for, separately from the raw
    # all-geometry maximum, so the two cannot be confused.
    H_MIN = {"parallel": 25.0, "perp": 50.0}

    rows_params = []
    rows_resid = []

    for along, label in ((True, "parallel"), (False, "perp")):
        fits = fit(K, along)
        dom_keys = [(h, d, "P" if along else "T") for h, d in all_keys
                    if h >= H_MIN[label]]
        for objective in ("minimax", "rms"):
            a, b = fits[objective]
            rows_params.append({
                "direction": label,
                "objective": objective,
                "a": f"{a:.6f}",
                "b": f"{b:.6f}",
                "h_min_nm": f"{H_MIN[label]:.0f}",
                "max_abs_resid_calib_pct":
                    f"{np.max(np.abs(residuals(K, a, b, along, fits['keys']))):.4f}",
                "max_abs_resid_domain_pct":
                    f"{max(abs(v) for v in residuals(K, a, b, along, dom_keys)):.4f}",
                "max_abs_resid_all_pct":
                    f"{max(abs(v) for v in residuals(K, a, b, along,
                                                     [(h, d, 'P' if along else 'T')
                                                      for h, d in all_keys])):.4f}",
            })

    # per-geometry residuals for the minimax fit (the one the paper uses)
    params = {}
    for along, label in ((True, "parallel"), (False, "perp")):
        params[label] = fit(K, along)["minimax"]

    for h, d in all_keys:
        row = {"h_nm": int(h), "d_nm": int(d), "d_over_w": f"{d / W:.4f}"}
        for along, label, dr in ((True, "parallel", "P"), (False, "perp", "T")):
            a, b = params[label]
            Km = closure_K(h, d, along)
            Kd = K[(h, d, dr)]
            E0 = (Km - Kd) / Kd * 100.0
            E1 = (Km * factor(d, a, b) - Kd) / Kd * 100.0
            row[f"E0_{dr}_pct"] = f"{E0:+.3f}"
            row[f"E1_{dr}_pct"] = f"{E1:+.3f}"
        rows_resid.append(row)

    os.makedirs(ANA, exist_ok=True)
    with open(os.path.join(ANA, "v2_fit_params.csv"), "w", newline="", encoding="utf-8") as f:
        wtr = csv.DictWriter(f, fieldnames=list(rows_params[0].keys()))
        wtr.writeheader()
        wtr.writerows(rows_params)
    with open(os.path.join(ANA, "v2_residuals.csv"), "w", newline="", encoding="utf-8") as f:
        wtr = csv.DictWriter(f, fieldnames=list(rows_resid[0].keys()))
        wtr.writeheader()
        wtr.writerows(rows_resid)

    # ---------------- console + markdown report ----------------
    lines = []
    def say(s=""):
        print(s)
        lines.append(s)

    say("# V2 correction factors — reproducible fit")
    say()
    say("Generated by `analysis_fit_v2.py`. Every number in this file is")
    say("regenerated from the result CSVs; nothing is hard-coded.")
    say()
    say("## Fitted coefficients")
    say()
    say("| direction | objective | a | b | h_min | max abs, calibration | **max abs, claimed domain** | max abs, all 18 |")
    say("|---|---|---|---|---|---|---|---|")
    for r in rows_params:
        say(f"| {r['direction']} | {r['objective']} | {r['a']} | {r['b']} | "
            f"{r['h_min_nm']} nm | {r['max_abs_resid_calib_pct']}% | "
            f"**{r['max_abs_resid_domain_pct']}%** | {r['max_abs_resid_all_pct']}% |")
    say()
    say("The paper uses the **minimax** row: the quoted accuracy is a bound on")
    say("the absolute residual, so the fit is made against that same quantity.")
    say("The RMS row is reported as a sensitivity check.")
    say()
    say("The **claimed domain** column is the bound over the gap range each")
    say("factor is actually quoted for: `h >= 25 nm` along the grooves and")
    say("`h >= 50 nm` across them. The `all 18` column additionally includes")
    say("the `h = 25 nm` across-groove cases, which lie outside the across-")
    say("groove domain and are the reason that column is larger; the two")
    say("numbers must not be substituted for one another.")
    say()
    say("## Residuals by hold-out group (minimax fit)")
    say()
    say("| group | n | parallel: min / max | perp: min / max |")
    say("|---|---|---|---|")
    for gname, pts in groups.items():
        if not pts:
            continue
        cells = []
        for along, label, dr in ((True, "parallel", "P"), (False, "perp", "T")):
            a, b = params[label]
            vals = residuals(K, a, b, along, [(h, d, dr) for h, d in pts])
            cells.append(f"{vals.min():+.2f}% / {vals.max():+.2f}%")
        say(f"| {gname} | {len(pts)} | {cells[0]} | {cells[1]} |")
    say()
    say("## Per-geometry residual table")
    say()
    say("| h (nm) | d (nm) | d/w | E0 par | E1 par | E0 perp | E1 perp |")
    say("|---|---|---|---|---|---|---|")
    for row in rows_resid:
        say(f"| {row['h_nm']} | {row['d_nm']} | {row['d_over_w']} | "
            f"{row['E0_P_pct']} | {row['E1_P_pct']} | {row['E0_T_pct']} | {row['E1_T_pct']} |")
    say()
    say("E0 = closure error before correction, E1 = after. All values in percent.")

    with open(os.path.join(ANA, "V2_FIT_REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print()
    print("written:", os.path.join(ANA, "v2_fit_params.csv"))
    print("written:", os.path.join(ANA, "v2_residuals.csv"))
    print("written:", os.path.join(ANA, "V2_FIT_REPORT.md"))


if __name__ == "__main__":
    main()
