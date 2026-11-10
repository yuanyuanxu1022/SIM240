# -*- coding: utf-8 -*-
"""Recompute the drainage-time ratio under two integration conventions.

Purpose: the corrected time ratio quoted in the manuscript (0.958-0.987) was not
reproducible from a single stated chain. This script quantifies how much of the
discrepancy comes from the integration convention, because K(h) is sampled at
only three to four gaps per groove depth.

Convention A: trapezoidal rule on the sampled gaps only (no interpolation).
Convention B: log-log shape-preserving (PCHIP) interpolation of K(h), 400 points.

Both use the same coefficients, the same stroke, and the same series solution.
"""
import csv
import numpy as np
from scipy.interpolate import PchipInterpolator

B = "/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results/"
W = 120.0
FP = lambda d: 1.0 / (1.0 + 1.7685 * (d / W) ** 1.6331)
FT = lambda d: 1.0 / (1.0 + 0.4900 * (d / W) ** 0.6990)


def load(Kx, Ky, a=1.0, b=1.0, nmax=201):
    m = np.arange(1, nmax + 1, 2, dtype=float)[:, None]
    n = np.arange(1, nmax + 1, 2, dtype=float)[None, :]
    s = (-1.0) ** ((m + n - 2) / 2)
    D = Kx * (m * np.pi / (2 * a)) ** 2 + Ky * (n * np.pi / (2 * b)) ** 2
    c = -(16.0 / (np.pi ** 2 * m * n)) * s / D
    return np.abs(np.sum(c * (16 * a * b / (np.pi ** 2 * m * n)) * s))


def stripe(h, d, along):
    hg = h + d
    if along:
        return ((hg ** 3 + h ** 3) / 2) / 12 * 1e-27
    return (2 / (1 / hg ** 3 + 1 / h ** 3)) / 12 * 1e-27


K = {}
for r in csv.DictReader(open(B + "summary.csv")):
    if r.get("dx_nm") != "5":
        continue
    K[(int(r["h_nm"]), int(r["d_nm"]), r["direction"])] = float(r["Keff_m3"])
for f in ("d75_summary.csv", "h25_summary.csv", "d120_summary.csv"):
    for r in csv.DictReader(open(B + f)):
        K[(int(r["h_nm"]), int(r["d_nm"]),
           "P" if r["case_id"].split("-")[1] == "P" else "T")] = float(r["Keff_m3"])


def run(interp):
    rows = []
    for d in (25, 50, 75, 100, 120):
        hs = np.array(sorted({h for (h, dd, dr) in K if dd == d and dr == "P"}), float)
        Sr = np.array([load(K[(int(h), d, "P")], K[(int(h), d, "T")]) for h in hs])
        Sm = np.array([load(stripe(h, d, True), stripe(h, d, False)) for h in hs])
        Sc = np.array([load(stripe(h, d, True) * FP(d),
                            stripe(h, d, False) * FT(d)) for h in hs])
        if interp == "trapz":
            g, A, R, C = hs, Sm, Sr, Sc
        else:
            g = np.linspace(hs[0], hs[-1], 400)

            def up(y):
                return np.exp(PchipInterpolator(np.log(hs), np.log(y))(np.log(g)))

            A, R, C = up(Sm), up(Sr), up(Sc)
        rows.append((d, np.trapezoid(A, g) / np.trapezoid(R, g),
                     np.trapezoid(C, g) / np.trapezoid(R, g),
                     float((A / R).min()), float((A / R).max()),
                     float(A[-1] / R[-1] / (np.trapezoid(A, g) / np.trapezoid(R, g)) - 1) * 100))
    return rows


for tag, label in (("trapz", "A 采样点梯形，无插值"), ("pchip", "B log-log PCHIP，400 点")):
    rows = run(tag)
    tu = [r[1] for r in rows]
    tc = [r[2] for r in rows]
    print("=" * 78)
    print(f"[{label}]")
    print(f"  未修正时间比 {min(tu):.6f}-{max(tu):.6f}"
          f"  ({(min(tu)-1)*100:+.2f}% .. {(max(tu)-1)*100:+.2f}%)")
    print(f"  修正后时间比 {min(tc):.6f}-{max(tc):.6f}"
          f"  ({(min(tc)-1)*100:+.2f}% .. {(max(tc)-1)*100:+.2f}%)")
    print(f"  {'d':>4}{'未修正':>10}{'修正后':>10}{'Sm/Sref@h0':>12}{'积分比':>10}"
          f"{'冻结/积分-1':>13}")
    for d, a, c, lo, hi, fz in rows:
        print(f"  {d:>4}{a:>10.6f}{c:>10.6f}{lo:>12.6f}{a:>10.6f}{fz:>12.2f}%")
