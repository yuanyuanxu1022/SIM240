# -*- coding: utf-8 -*-
"""Authoritative numbers for the revised Sec. V C.

Fixes three defects:
  (i)   the stroke was not common: d = 25 nm was integrated from 25 nm while the
        text and every other depth used 125 -> 50 nm;
  (ii)  the field S_ratio_min/max in the old chain was the reciprocal of the
        model-A conductance ratio, not the model-B S_model/S_ref;
  (iii) the corrected closure must be applied to the MODEL coefficients
        (the stripe closure), not to the discrete reference coefficients.

Convention: one stroke h = 125 -> 50 nm, 201-term series, and two integration
conventions reported so the interpolation sensitivity is visible.
"""
import csv
import numpy as np
from scipy.interpolate import PchipInterpolator

B = "/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results/"
OUT = "results/"
W = 120.0
STROKE = (50.0, 125.0)
FP = lambda d: 1.0 / (1.0 + 1.7685 * (d / W) ** 1.6331)
FT = lambda d: 1.0 / (1.0 + 0.4900 * (d / W) ** 0.6990)


def load(Kx, Ky, a=1.0, b=1.0, nmax=201):
    m = np.arange(1, nmax + 1, 2, dtype=float)[:, None]
    n = np.arange(1, nmax + 1, 2, dtype=float)[None, :]
    s = (-1.0) ** ((m + n - 2) / 2)
    D = Kx * (m * np.pi / (2 * a)) ** 2 + Ky * (n * np.pi / (2 * b)) ** 2
    c = -(16.0 / (np.pi ** 2 * m * n)) * s / D
    return np.abs(np.sum(c * (16 * a * b / (np.pi ** 2 * m * n)) * s))


def load_and_peak(Kx, Ky, nmax=401):
    m = np.arange(1, nmax + 1, 2, dtype=float)[:, None]
    n = np.arange(1, nmax + 1, 2, dtype=float)[None, :]
    s = (-1.0) ** ((m + n - 2) / 2)
    D = Kx * (m * np.pi / 2) ** 2 + Ky * (n * np.pi / 2) ** 2
    c = -(16.0 / (np.pi ** 2 * m * n)) * s / D
    return (np.abs(np.sum(c * (16 / (np.pi ** 2 * m * n)) * s)), np.abs(np.sum(c)))


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


def model(h, d, corrected):
    mP, mT = stripe(h, d, True), stripe(h, d, False)
    return (mP * FP(d), mT * FT(d)) if corrected else (mP, mT)


# ---- A. discrete load ratios, every geometry ----
print("=" * 96)
print("A. Load ratio relative to the discrete reference coefficients (sample points)")
print("=" * 96)
rows = []
for (h, d, dr) in sorted(K):
    if dr != "P" or (h, d, "T") not in K:
        continue
    kP, kT = K[(h, d, "P")], K[(h, d, "T")]
    f0 = load(*model(h, d, False)) / load(kP, kT)
    f1 = load(*model(h, d, True)) / load(kP, kT)
    p0 = load_and_peak(*model(h, d, False))[1] / load_and_peak(kP, kT)[1]
    rows.append(dict(h=h, d=d, load_unc=f0, load_cor=f1, peak_unc=p0))
print(f"{'h':>4}{'d':>5}{'load unc':>10}{'load cor':>10}{'peak unc':>10}{'peak-load':>11}")
for r in rows:
    print(f"{r['h']:>4}{r['d']:>5}{r['load_unc']:>10.6f}{r['load_cor']:>10.6f}"
          f"{r['peak_unc']:>10.6f}{(r['peak_unc'] - r['load_unc']) * 100:>10.4f}pp")
lu = np.array([r["load_unc"] for r in rows])
lc = np.array([r["load_cor"] for r in rows])
pk = np.array([r["peak_unc"] for r in rows])
print(f"\n  未修正 {lu.min():.6f}-{lu.max():.6f}  中位 {np.median(lu) - 1:+.4%}")
print(f"  修正后 {lc.min():.6f}-{lc.max():.6f}  中位 {np.median(lc) - 1:+.4%}")
print(f"  峰值/荷载最大差 {np.max(np.abs(pk - lu)) * 100:.4f} pp")

# ---- B. time on the common stroke ----
print("\n" + "=" * 96)
print("B. Drainage time, common stroke 125 -> 50 nm, two integration conventions")
print("=" * 96)
table = []
for tag in ("trapz", "pchip"):
    print(f"\n[{tag}]")
    print(f"  {'d':>4}{'t unc':>10}{'t cor':>10}{'Sm/Sr min':>11}{'Sm/Sr max':>11}"
          f"{'@h0':>9}{'frozen/int-1':>14}")
    for d in (25, 50, 75, 100, 120):
        hs = np.array(sorted({h for (h, dd, dr) in K if dd == d and dr == "P"}), float)
        keep = (hs >= STROKE[0]) & (hs <= STROKE[1])
        hss = hs[keep]
        g = hss if tag == "trapz" else np.linspace(*STROKE, 400)

        def up(y):
            if tag == "trapz":
                return y[keep]
            return np.exp(PchipInterpolator(np.log(hss), np.log(y[keep]))(np.log(g)))

        Sr = up(np.array([load(K[(int(h), d, "P")], K[(int(h), d, "T")]) for h in hs]))
        Sm = up(np.array([load(*model(h, d, False)) for h in hs]))
        Sc = up(np.array([load(*model(h, d, True)) for h in hs]))
        tu = np.trapezoid(Sm, g) / np.trapezoid(Sr, g)
        tc = np.trapezoid(Sc, g) / np.trapezoid(Sr, g)
        r = Sm / Sr
        fz = r[-1] / tu - 1
        print(f"  {d:>4}{tu:>10.6f}{tc:>10.6f}{r.min():>11.6f}{r.max():>11.6f}"
              f"{r[-1]:>9.6f}{fz * 100:>13.2f}%")
        table.append(dict(convention=tag, d=d, t_unc=tu, t_cor=tc,
                          Sm_Sr_min=r.min(), Sm_Sr_max=r.max(),
                          Sm_Sr_at_h0=r[-1], frozen_vs_integrated_pct=fz * 100))

with open(OUT + "table2b_time_common_stroke.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(table[0].keys()))
    w.writeheader()
    w.writerows(table)
print(f"\nwritten {OUT}table2b_time_common_stroke.csv")
