"""Error propagation from the transport coefficients into a squeeze-film prediction.

Two reduced models are used, deliberately:

  Model A  axisymmetric, K_eff = (Kxx+Kyy)/2   -- the schematic model; reproduces the
           relation p ~ 1/(Kxx+Kyy) used in the handwritten estimate. Kept because it is
           transparent, and because it makes the algebra checkable by hand.

  Model B  exact 2-D anisotropic lubrication on a square field, pattern along x,
           Kxx p_xx + Kyy p_yy = mu*V, p = 0 on the boundary. No averaging of the two
           components is assumed; the anisotropy enters exactly. This is the model whose
           numbers should be quoted.

Both see the same pair (Kxx, Kyy) from the same geometry and the same gap. No quantity is
ever assembled from different cases.

Usage: python squeeze_error_propagation.py
Outputs: results/*.csv, results/PROPAGATION_REPORT.md, figures
"""
import csv
import json
import numpy as np
from scipy.interpolate import PchipInterpolator

BASE = "/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results/"
OUT = "/home/dell/yuanyuanxu/SIM240/CASE/D_series/D3_squeeze_error_propagation/results/"
W, PHI = 120.0, 0.5

# ----------------------------------------------------------------- data
rows = []
for r in csv.DictReader(open(BASE + "summary.csv")):
    if r.get("dx_nm") != "5":
        continue
    rows.append((int(r["h_nm"]), int(r["d_nm"]), r["direction"], float(r["Keff_m3"])))
for f in ("d75_summary.csv", "h25_summary.csv", "d120_summary.csv"):
    for r in csv.DictReader(open(BASE + f)):
        rows.append((int(r["h_nm"]), int(r["d_nm"]),
                     "P" if r["case_id"].split("-")[1] == "P" else "T",
                     float(r["Keff_m3"])))

KD = {(h, d, dr): v for h, d, dr, v in rows}


def stripe(h, d, along):
    """Eq. (1): the closure being tested."""
    hg = h + d
    if along:
        return (hg ** 3 + h ** 3) / 2 / 12 * 1e-27
    return 2 / (1 / hg ** 3 + 1 / h ** 3) / 12 * 1e-27


def pair(h, d):
    """Paired coefficients from one geometry at one gap. Returns (DNS, model)."""
    if (h, d, "P") not in KD or (h, d, "T") not in KD:
        return None
    return ((KD[(h, d, "P")], KD[(h, d, "T")]),
            (stripe(h, d, True), stripe(h, d, False)))


# ------------------------------------------------- Model B: exact 2-D anisotropic
def squeeze_load_2d(Kxx, Kyy, a=1.0, b=1.0, nmax=201, mu=1.0, V=1.0):
    """Load for uniform closing of a rectangular field with p = 0 on the boundary.

    Solves  Kxx p_xx + Kyy p_yy = mu V  on [-a,a] x [-b,b],  p = 0 on the boundary.
    Double cosine series, odd modes only. Returns (load, peak_pressure).
    Load = integral of p over the area; peak = p at the centre.
    """
    m = np.arange(1, nmax + 1, 2, dtype=float)[:, None]
    n = np.arange(1, nmax + 1, 2, dtype=float)[None, :]
    sign = (-1.0) ** ((m + n - 2) / 2)
    D = Kxx * (m * np.pi / (2 * a)) ** 2 + Kyy * (n * np.pi / (2 * b)) ** 2
    c = -(16.0 / (np.pi ** 2 * m * n)) * sign / D
    load = mu * V * np.abs(np.sum(c * (16 * a * b / (np.pi ** 2 * m * n)) * sign))
    peak = mu * V * np.abs(np.sum(c))          # cos(0)*cos(0) = 1 at the centre
    return load, peak


# validation against an INDEPENDENT finite-difference solve (not against itself)
def load_fd(Kxx, Kyy, a=1.0, b=1.0, N=400, mu=1.0, V=1.0):
    import scipy.sparse as sp
    import scipy.sparse.linalg as spl
    x = np.linspace(-a, a, N + 2)[1:-1]
    y = np.linspace(-b, b, N + 2)[1:-1]
    dx, dy = x[1] - x[0], y[1] - y[0]
    nx, ny = len(x), len(y)
    idx = lambda i, j: i * ny + j
    rows, cols, vals = [], [], []
    rhs = np.full(nx * ny, mu * V)
    for i in range(nx):
        for j in range(ny):
            k = idx(i, j)
            cx, cy = Kxx / dx ** 2, Kyy / dy ** 2
            rows.append(k); cols.append(k); vals.append(-2 * cx - 2 * cy)
            for di, dj, c in ((-1, 0, cx), (1, 0, cx), (0, -1, cy), (0, 1, cy)):
                ii, jj = i + di, j + dj
                if 0 <= ii < nx and 0 <= jj < ny:
                    rows.append(k); cols.append(idx(ii, jj)); vals.append(c)
    A = sp.csr_matrix((vals, (rows, cols)), shape=(nx * ny, nx * ny))
    p = spl.spsolve(A, rhs).reshape(nx, ny)
    return float(-p.sum() * dx * dy)


print("[validate] Model B, series vs independent finite differences (square field)")
print(f"  {'Kxx':>7}{'Kyy':>7}{'series':>14}{'FD (N=400)':>14}{'rel.diff':>11}")
_worst = 0.0
for kx, ky in [(1, 1), (4, 1), (1, 4), (10, 1), (1.08, 3.05), (3.05, 1.08)]:
    Ls, _ = squeeze_load_2d(kx, ky)
    Lf = load_fd(kx, ky, N=400)
    rel = abs(Ls - Lf) / Ls
    _worst = max(_worst, rel)
    print(f"  {kx:>7.2f}{ky:>7.2f}{Ls:>14.8f}{Lf:>14.8f}{rel:>11.1e}")
print(f"  worst relative difference = {_worst:.1e} (finite-difference truncation, O(dx^2))")

print("\n[validate] Model B is symmetric under Kxx <-> Kyy on a square field (expected from the geometry)")
for kx, ky in [(4, 1), (10, 1)]:
    a, _ = squeeze_load_2d(kx, ky)
    b, _ = squeeze_load_2d(ky, kx)
    print(f"  ({kx},{ky}) {a:.10f}   ({ky},{kx}) {b:.10f}   identical={abs(a-b) < 1e-12}")


# ------------------------------------------------- Model A: axisymmetric schematic
def load_axisym(Kxx, Kyy, R=1.0, mu=1.0, V=1.0):
    """F = pi mu V R^4 / (4 (Kxx+Kyy));  returns (load, peak pressure)."""
    S = Kxx + Kyy
    load = np.pi * mu * V * R ** 4 / (4 * S)
    peak = mu * V * R ** 2 / (2 * S)     # = 2 * mean, paraboloid
    return load, peak


# ----------------------------------------------------------------- comparisons
def compare(h, d):
    """All load/peak ratios for one geometry at one gap."""
    pr = pair(h, d)
    if pr is None:
        return None
    (kxD, kyD), (kxM, kyM) = pr
    e_x = (kxM - kxD) / kxD * 100
    e_y = (kyM - kyD) / kyD * 100

    FA_D, pA_D = load_axisym(kxD, kyD)
    FA_M, pA_M = load_axisym(kxM, kyM)
    FB_D, pB_D = squeeze_load_2d(kxD, kyD)
    FB_M, pB_M = squeeze_load_2d(kxM, kyM)

    # sensitivity: replace one component only
    FB_x, _ = squeeze_load_2d(kxM, kyD)
    FB_y, _ = squeeze_load_2d(kxD, kyM)
    FA_x, _ = load_axisym(kxM, kyD)
    FA_y, _ = load_axisym(kxD, kyM)

    # log-derivative weights: share of the load error carried by each component
    # (F is homogeneous of degree -1 in K, so w_x + w_y = 1 by construction)
    def _w(kxx, kyy, eps=1e-4):
        dlnF_x = (np.log(squeeze_load_2d(kxx * np.exp(eps), kyy)[0])
                  - np.log(squeeze_load_2d(kxx * np.exp(-eps), kyy)[0])) / (2 * eps)
        dlnF_y = (np.log(squeeze_load_2d(kxx, kyy * np.exp(eps))[0])
                  - np.log(squeeze_load_2d(kxx, kyy * np.exp(-eps))[0])) / (2 * eps)
        return -dlnF_x, -dlnF_y

    wx, wy = _w(kxD, kyD)

    return dict(
        h=h, d=d, d_over_w=d / W,
        w_x=wx, w_y=wy,
        Kxx_DNS=kxD, Kyy_DNS=kyD, Kxx_mod=kxM, Kyy_mod=kyM,
        A_DNS=kxD / kyD, A_mod=kxM / kyM,
        e_xx=e_x, e_yy=e_y,
        F_A_ratio=FA_M / FA_D, F_B_ratio=FB_M / FB_D,
        peak_A_ratio=pA_M / pA_D, peak_B_ratio=pB_M / pB_D,
        F_B_only_x=FB_x / FB_D, F_B_only_y=FB_y / FB_D,
        F_A_only_x=FA_x / FA_D, F_A_only_y=FA_y / FA_D,
    )


cases = []
for d in (25, 50, 75, 100, 120):
    for h in (25, 50, 75, 125):
        c = compare(h, d)
        if c:
            cases.append(c)

hdr = ("h", "d", "d/w", "A_DNS", "e_xx", "e_yy",
       "F_A_r", "F_B_r", "peak_A_r", "peak_B_r",
       "B_only_x", "B_only_y", "A_only_x", "A_only_y")
print("\n" + "=" * 118)
print("Table 1  Load and peak-pressure ratios, model / DNS, uniform closing velocity")
print("=" * 118)
print(f"{'h':>4}{'d':>5}{'d/w':>7}{'A':>7}{'e_xx%':>8}{'e_yy%':>8}"
      f"{'F_A':>8}{'F_B':>8}{'p_A':>8}{'p_B':>8}{'w_x':>7}{'B:x':>8}{'B:y':>8}")
for c in cases:
    print(f"{c['h']:>4}{c['d']:>5}{c['d_over_w']:>7.2f}{c['A_DNS']:>7.2f}"
          f"{c['e_xx']:>8.1f}{c['e_yy']:>8.1f}"
          f"{c['F_A_ratio']:>8.3f}{c['F_B_ratio']:>8.3f}"
          f"{c['peak_A_ratio']:>8.3f}{c['peak_B_ratio']:>8.3f}"
          f"{c['w_x']:>7.2f}"
          f"{c['F_B_only_x']:>8.3f}{c['F_B_only_y']:>8.3f}")

with open(OUT + "table1_load_and_peak.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(cases[0].keys()))
    w.writeheader()
    w.writerows(cases)
print(f"\n-> {OUT}table1_load_and_peak.csv")


# ---------------------------------------------------------------- time, constant load
def K_of_h(d, along):
    """DNS K(h) at fixed d, log-log PCHIP through the sampled gaps."""
    hs = sorted(h for (h, dd, dr) in KD if dd == d and dr == ("P" if along else "T"))
    ks = [KD[(h, d, "P" if along else "T")] for h in hs]
    if len(hs) < 3:
        return None
    f = PchipInterpolator(np.log(hs), np.log(ks))
    return lambda h: np.exp(f(np.log(h))), hs


def time_ratio(d, h0, hf, nmid=400):
    """t_model / t_DNS at constant load. Returns dict or None."""
    fx, fy = K_of_h(d, True), K_of_h(d, False)
    if fx is None or fy is None:
        return None
    gx, hs = fx
    gy, _ = fy
    if hf < min(hs) or h0 > max(hs):
        return None
    hs_grid = np.linspace(hf, h0, nmid)
    kx = np.array([gx(h) for h in hs_grid])
    ky = np.array([gy(h) for h in hs_grid])
    sx = np.array([stripe(h, d, True) for h in hs_grid])
    sy = np.array([stripe(h, d, False) for h in hs_grid])

    def S2(kxx, kyy):
        return np.array([squeeze_load_2d(a, b)[0] for a, b in zip(kxx, kyy)])

    # Model B: t = (1/F) * int S(K(h)) dh
    tB_D = np.trapezoid(S2(kx, ky), hs_grid)
    tB_M = np.trapezoid(S2(sx, sy), hs_grid)
    # Model A: t = C * int dh/(Kxx+Kyy)
    tA_D = np.trapezoid(1.0 / (kx + ky), hs_grid)
    tA_M = np.trapezoid(1.0 / (sx + sy), hs_grid)

    # if the error were frozen at its value at h0 (no integration)
    i0 = 0 if h0 == hs_grid[-1] else len(hs_grid) - 1
    return dict(
        d=d, h0=h0, hf=hf,
        t_A_ratio=tA_M / tA_D, t_B_ratio=tB_M / tB_D,
        err_t_A=(tA_M / tA_D - 1) * 100, err_t_B=(tB_M / tB_D - 1) * 100,
        Kx_ratio_range=(sx / kx).min(), Kx_ratio_max=(sx / kx).max(),
        Ky_ratio_range=(sy / ky).min(), Ky_ratio_max=(sy / ky).max(),
        S_ratio_at_h0=(sx[-1] + sy[-1]) / (kx[-1] + ky[-1]),
        S_ratio_min=((sx + sy) / (kx + ky)).min(),
        S_ratio_max=((sx + sy) / (kx + ky)).max(),
        t_B_if_frozen=1.0 / ((sx[-1] + sy[-1]) / (kx[-1] + ky[-1])),
        frozen_vs_integrated_pct=(
            (1.0 / ((sx[-1] + sy[-1]) / (kx[-1] + ky[-1]))) / (tA_M / tA_D) - 1) * 100,
    )


print("\n" + "=" * 100)
print("Table 2  Drainage time at constant load, integrated over the closing stroke")
print("=" * 100)
print(f"{'d':>5}{'h0->hf':>12}{'t_A/t_D':>10}{'t_B/t_D':>10}{'err_t_B%':>10}"
      f"{'frozen@h0':>11}{'冻/积 差':>10}{'(S_m/S_D)范围':>16}")
times = []
for d in (25, 50, 75, 100, 120):
    for (h0, hf) in ((125, 50),):
        t = time_ratio(d, h0, hf)
        if t:
            times.append(t)
            print(f"{d:>5}{f'{h0}->{hf}':>12}{t['t_A_ratio']:>10.3f}{t['t_B_ratio']:>10.3f}"
                  f"{t['err_t_B']:>10.1f}{t['t_B_if_frozen']:>11.3f}"
                  f"{t['frozen_vs_integrated_pct']:>9.1f}%"
                  f"{f'{t['S_ratio_min']:.2f}-{t['S_ratio_max']:.2f}':>16}")
# extended stroke where the data allow it
for d in (25, 50, 100):
    t = time_ratio(d, 125, 25)
    if t:
        times.append(t)
        print(f"{d:>5}{'125->25':>12}{t['t_A_ratio']:>10.3f}{t['t_B_ratio']:>10.3f}"
              f"{t['err_t_B']:>10.1f}{t['t_B_if_frozen']:>11.3f}"
              f"{t['frozen_vs_integrated_pct']:>9.1f}%"
              f"{f'{t['S_ratio_min']:.2f}-{t['S_ratio_max']:.2f}':>16}")

with open(OUT + "table2_time_constant_load.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(times[0].keys()))
    w.writeheader()
    w.writerows(times)
print(f"\n-> {OUT}table2_time_constant_load.csv")

# ---------------------------------------------------------------- summary statistics
print("\n" + "=" * 100)
print("Summary")
print("=" * 100)


def stat(key):
    v = np.array([c[key] for c in cases])
    return v.min(), v.max(), np.median(v)


for key, lab in (("F_A_ratio", "load, model A"), ("F_B_ratio", "load, model B"),
                 ("peak_A_ratio", "peak p, model A"), ("peak_B_ratio", "peak p, model B")):
    lo, hi, md = stat(key)
    print(f"  {lab:18s} ratio {lo:.3f}-{hi:.3f}  -> error {(lo-1)*100:+.1f}% to {(hi-1)*100:+.1f}%  (median {(md-1)*100:+.1f}%)")

print("\n  sensitivity, model B (replace one component):")
for key, lab in (("F_B_only_x", "  only Kxx"), ("F_B_only_y", "  only Kyy")):
    lo, hi, md = stat(key)
    print(f"{lab:18s} ratio {lo:.3f}-{hi:.3f}  -> error {(lo-1)*100:+.1f}% to {(hi-1)*100:+.1f}%  (median {(md-1)*100:+.1f}%)")

print("\n  worst case (largest |load error|, model B):")
worst = min(cases, key=lambda c: c["F_B_ratio"])
print(f"    h={worst['h']} d={worst['d']}  A={worst['A_DNS']:.2f}  e_xx={worst['e_xx']:+.1f}% e_yy={worst['e_yy']:+.1f}%"
      f"  -> F/F_DNS = {worst['F_B_ratio']:.3f}")
best = max(cases, key=lambda c: c["F_B_ratio"])
print(f"    mildest: h={best['h']} d={best['d']}  A={best['A_DNS']:.2f}  e_xx={best['e_xx']:+.1f}% e_yy={best['e_yy']:+.1f}%"
      f"  -> F/F_DNS = {best['F_B_ratio']:.3f}")

json.dump({"cases": cases, "times": times}, open(OUT + "propagation.json", "w"), indent=1, default=float)
print(f"\n-> {OUT}propagation.json")

# ---------------------------------------------------------------- decomposition
def shape_factor(A, a=1.0, b=1.0):
    """h(A) = F * sqrt(Kxx*Kyy) for the square field, normalised to A = 1.

    Because F is homogeneous of degree -1 in K, F = h(A)/sqrt(Kxx*Kyy) exactly,
    with h depending only on the anisotropy ratio. This separates the load error into
    a mean-conductance part and an anisotropy-shape part.
    """
    return squeeze_load_2d(A, 1.0, a, b)[0] * np.sqrt(A)


H1 = shape_factor(1.0)

print("\n" + "=" * 112)
print("Table 3  Decomposition of the load error:  F_mod/F_DNS = [h(A_mod)/h(A_DNS)] / sqrt[(1+e_x)(1+e_y)]")
print("=" * 112)
print(f"{'h':>4}{'d':>5}{'A_DNS':>7}{'A_mod':>7}{'g=sqrt..':>10}"
      f"{'mean项':>9}{'shape项':>9}{'乘积':>8}{'实际':>8}{'swap误差':>10}")
print("-" * 112)
decomp = []
for c in cases:
    g = np.sqrt((1 + c["e_xx"] / 100) * (1 + c["e_yy"] / 100))
    sh = shape_factor(c["A_mod"]) / shape_factor(c["A_DNS"])
    # counterfactual: same two error magnitudes, attached to the other components
    kxD, kyD = c["Kxx_DNS"], c["Kyy_DNS"]
    kxS = kxD * (1 + c["e_yy"] / 100)
    kyS = kyD * (1 + c["e_xx"] / 100)
    F_swap = squeeze_load_2d(kxS, kyS)[0] / squeeze_load_2d(kxD, kyD)[0]
    decomp.append(dict(h=c["h"], d=c["d"], A_DNS=c["A_DNS"], A_mod=c["A_mod"],
                       g=g, mean_term=1 / g, shape_term=sh,
                       product=(1 / g) * sh, actual=c["F_B_ratio"], swap=F_swap))
    print(f"{c['h']:>4}{c['d']:>5}{c['A_DNS']:>7.2f}{c['A_mod']:>7.2f}{g:>10.3f}"
          f"{1/g:>9.3f}{sh:>9.3f}{(1/g)*sh:>8.3f}{c['F_B_ratio']:>8.3f}{F_swap:>10.3f}")

with open(OUT + "table3_decomposition.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(decomp[0].keys()))
    w.writeheader(); w.writerows(decomp)

print("\n  mean term = 1/sqrt((1+e_x)(1+e_y)): what the load error would be if only the")
print("  overall conductance were wrong. shape term = h(A_mod)/h(A_DNS): the extra effect of")
print("  getting the anisotropy ratio wrong. Their product reproduces the computed ratio.")
sw = np.array([d_["swap"] for d_ in decomp])
ac = np.array([d_["actual"] for d_ in decomp])
print(f"\n  counterfactual (errors swapped onto the other component):")
print(f"    actual    F/F_DNS = {ac.min():.3f}-{ac.max():.3f}   ({(ac.min()-1)*100:+.1f}% to {(ac.max()-1)*100:+.1f}%)")
print(f"    swapped   F/F_DNS = {sw.min():.3f}-{sw.max():.3f}   ({(sw.min()-1)*100:+.1f}% to {(sw.max()-1)*100:+.1f}%)")
print(f"    mean |1 - ratio|: actual {np.mean(np.abs(1-ac))*100:.1f}%   swapped {np.mean(np.abs(1-sw))*100:.1f}%")
print("    -> the larger coefficient also carries the larger error, so the two effects add.")

# ---------------------------------------------------------------- corrected closure
FP = lambda d: 1.0 / (1.0 + 1.7685 * (d / W) ** 1.6331)
FT = lambda d: 1.0 / (1.0 + 0.4900 * (d / W) ** 0.6990)

print("\n" + "=" * 104)
print("Table 4  What the published correction buys: same load chain, corrected closure")
print("        K_corrected = K_model x F(d/w)   (F applied to the model, NOT to the DNS value)")
print("=" * 104)
print(f"{'h':>4}{'d':>5}{'F uncorr':>10}{'|err|%':>9}{'F corr':>9}{'|err|%':>9}{'gain':>8}"
      f"{'  resid K_xx':>13}{'resid K_yy':>12}")
t4 = []
for c in cases:
    kxD, kyD, kxM, kyM, d = c["Kxx_DNS"], c["Kyy_DNS"], c["Kxx_mod"], c["Kyy_mod"], c["d"]
    r1 = c["F_B_ratio"]
    kx2, ky2 = kxM * FP(d), kyM * FT(d)
    r2 = squeeze_load_2d(kx2, ky2)[0] / squeeze_load_2d(kxD, kyD)[0]
    t4.append(dict(h=c["h"], d=d, F_uncorrected=r1, err_uncorrected_pct=(r1 - 1) * 100,
                   F_corrected=r2, err_corrected_pct=(r2 - 1) * 100,
                   gain_pp=(abs(1 - r1) - abs(1 - r2)) * 100,
                   resid_Kxx_pct=(kx2 - kxD) / kxD * 100,
                   resid_Kyy_pct=(ky2 - kyD) / kyD * 100))
    x = t4[-1]
    print(f"{x['h']:>4}{x['d']:>5}{r1:>10.3f}{abs(1-r1)*100:>9.1f}{r2:>9.3f}{abs(1-r2)*100:>9.1f}"
          f"{x['gain_pp']:>8.1f}{x['resid_Kxx_pct']:>13.1f}{x['resid_Kyy_pct']:>12.1f}")

with open(OUT + "table4_corrected_closure.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(t4[0].keys()))
    w.writeheader(); w.writerows(t4)

_e1 = np.array([abs(x["err_uncorrected_pct"]) for x in t4])
_e2 = np.array([abs(x["err_corrected_pct"]) for x in t4])
print(f"\n  load |error|:  uncorrected median {np.median(_e1):.1f}%, max {_e1.max():.1f}%")
print(f"                 corrected   median {np.median(_e2):.1f}%, max {_e2.max():.1f}%")

in_dom = [x for x in t4 if x["d"] / W <= 1.0 and x["h"] >= 50]
_d1 = np.array([abs(x["err_uncorrected_pct"]) for x in in_dom])
_d2 = np.array([abs(x["err_corrected_pct"]) for x in in_dom])
print(f"  inside the declared domain (d/w<=1, h>=50, n={len(in_dom)}):"
      f"  max {_d1.max():.1f}%  ->  {_d2.max():.1f}%")
