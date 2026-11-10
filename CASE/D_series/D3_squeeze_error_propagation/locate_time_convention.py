# -*- coding: utf-8 -*-
"""Locate the integration convention behind the audit's corrected time ratio.

The audit reports 0.960996-1.004658 for the corrected time ratio and 0.874690
for d=25 un-corrected, while a straightforward log-log PCHIP over the sampled
stroke gives 0.9588-0.9920 and 0.8650. This script tries the plausible variants
to identify which one reproduces the audit, so the manuscript can state one
convention and name it, instead of quoting a number nobody can retrace.
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

hs_all = {d: np.array(sorted({h for (h, dd, dr) in K if dd == d and dr == "P"}), float)
          for d in (25, 50, 75, 100, 120)}
for d, hs in hs_all.items():
    print(f"d={d:>3}: h 样点 {list(hs.astype(int))}")

variants = {
    "V1 全行程 hs[0]..hs[-1], log-PCHIP": dict(grid=None, logK=True, logS=True),
    "V2 全行程, 线性插值 K": dict(grid=None, logK=False, logS=True),
    "V3 固定 50..125, log-PCHIP": dict(grid=(50, 125), logK=True, logS=True),
    "V4 全行程, 对 S 直接线性": dict(grid=None, logK=False, logS=False),
}

print("\n" + "=" * 86)
print(f"{'口径':>34}{'d25 未修正':>12}{'d120 未修正':>13}{'修正后范围':>20}")
for name, cfg in variants.items():
    tu, tc = [], []
    per = {}
    for d in (25, 50, 75, 100, 120):
        hs = hs_all[d]
        Sr = np.array([load(K[(int(h), d, "P")], K[(int(h), d, "T")]) for h in hs])
        Sm = np.array([load(stripe(h, d, True), stripe(h, d, False)) for h in hs])
        Sc = np.array([load(stripe(h, d, True) * FP(d),
                            stripe(h, d, False) * FT(d)) for h in hs])
        g = hs if cfg["grid"] is None else np.linspace(cfg["grid"][0], cfg["grid"][1], 400)

        def up(y):
            if cfg["logK"]:
                return np.exp(PchipInterpolator(np.log(hs), np.log(y))(np.log(g)))
            if cfg["logS"]:
                return PchipInterpolator(hs, y)(g)
            return np.interp(g, hs, y)

        A, R, C = up(Sm), up(Sr), up(Sc)
        per[d] = (np.trapezoid(A, g) / np.trapezoid(R, g),
                  np.trapezoid(C, g) / np.trapezoid(R, g))
        tu.append(per[d][0])
        tc.append(per[d][1])
    print(f"{name:>34}{per[25][0]:>12.6f}{per[120][0]:>13.6f}"
          f"{f'{min(tc):.6f}-{max(tc):.6f}':>20}")

print("\n审查报告值：d25 未修正 0.874690 | d120 未修正 0.404987 | 修正后 0.960996-1.004658")
