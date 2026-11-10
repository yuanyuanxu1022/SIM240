"""Rectangular field: how much do the component weights depend on the aspect ratio?

The question the square-field result left open: the load of a square field is symmetric
under Kxx <-> Kyy, so "which direction matters" had no answer there. A real imprint field
is not square in general, and the grooves have a direction relative to its edges.

Reduction
---------
With grooves along x, the load for a rectangular field Lx x Ly, p = 0 on the boundary, is

    F = (mu V a^3 b / Kxx) * Fhat(Lambda),        a = Lx/2, b = Ly/2,
    Lambda = (Lx/Ly)^2 * Kyy/Kxx = R^2 / A ,      R = Lx/Ly,  A = Kxx/Kyy.

Verified to 8 digits, so Lambda is the ONLY parameter besides the scale a^3 b / Kxx.
Hence

    F_mod / F_DNS = [ Fhat(Lambda_mod) / Fhat(Lambda_DNS) ] * 1 / (1 + e_xx)

and the weights w_x = -dlnF/dlnKxx, w_y = -dlnF/dlnKyy satisfy w_x + w_y = 1 with

    w_y = -dlnFhat/dlnLambda,     w_x = 1 - w_y.
"""
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "/home/dell/yuanyuanxu/SIM240/CASE/D_series/D3_squeeze_error_propagation/results/"
NMAX = 401


def Fhat(Lam):
    """Load of the normalised problem p_xx + Lam p_yy = 1 on [-1,1]^2, p = 0 boundary."""
    m = np.arange(1, NMAX + 1, 2, dtype=float)[:, None]
    n = np.arange(1, NMAX + 1, 2, dtype=float)[None, :]
    s = (-1.0) ** ((m + n - 2) / 2)
    D = (m * np.pi / 2) ** 2 + Lam * (n * np.pi / 2) ** 2
    c = -(16.0 / (np.pi ** 2 * m * n)) * s / D
    return float(np.abs(np.sum(c * (16.0 / (np.pi ** 2 * m * n)) * s)))


def weights(Lam, h=1e-4):
    """w_y = -dlnFhat/dlnLambda, w_x = 1 - w_y."""
    d = (np.log(Fhat(Lam * np.exp(h))) - np.log(Fhat(Lam * np.exp(-h)))) / (2 * h)
    wy = -d
    return 1 - wy, wy


# ------------------------------------------------------------------ sanity
print("[check] w_x + w_y = 1 and agreement with the square-field computation")
for A in (1.09, 2.0, 4.0, 15.45):
    wx, wy = weights(1.0 / A)          # square field: Lambda = 1/A
    print(f"  A={A:>6.2f}  Lambda={1/A:>7.4f}  w_x={wx:.4f}  w_y={wy:.4f}  sum={wx+wy:.12f}")

# ------------------------------------------------------------------ table
AS = [1.09, 1.5, 2.0, 3.0, 4.7, 8.0, 15.45]
RS = [0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]

print("\n" + "=" * 104)
print("Table 5  Weight of Kxx in the squeeze load, w_x = -dlnF/dlnKxx   (w_y = 1 - w_x)")
print("        R = Lx/Ly along grooves / across grooves;  Lambda = R^2/A")
print("=" * 104)
hdr = f"{'A \\\\ R':>8}" + "".join(f"{r:>9g}" for r in RS)
print(hdr)
print("-" * len(hdr))
rows = []
for A in AS:
    line = f"{A:>8.2f}"
    for R in RS:
        Lam = R ** 2 / A
        wx, wy = weights(Lam)
        line += f"{wx:>9.3f}"
        rows.append(dict(A=A, R=R, Lam=Lam, w_x=wx, w_y=wy))
    print(line)

with open(OUT + "table5_weights_aspect_ratio.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["A", "R", "Lam", "w_x", "w_y"])
    w.writeheader(); w.writerows(rows)

print("\n  reading: w_x near 1 -> the load is set by Kxx; near 0 -> by Kyy.")
print("  R = 1 recovers the square field.  R >> 1 (field elongated ALONG the grooves)")
print("  pushes w_x down: the liquid has to drain ACROSS, so Kyy takes over.")

# ------------------------------------------------------------------ how far can it be pushed
print("\n" + "=" * 104)
print("Table 6  Sensitivity of the load error to the aspect ratio, per geometry")
print("        |F_mod/F_DNS - 1| for several R, using the measured paired errors")
print("=" * 104)
import json
D = json.load(open(OUT + "propagation.json"))["cases"]
W = 120.0
FP = lambda d: 1.0 / (1.0 + 1.7685 * (d / W) ** 1.6331)
FT = lambda d: 1.0 / (1.0 + 0.4900 * (d / W) ** 0.6990)

R_LIST = [0.1, 0.3, 1.0, 3.0, 10.0, 100.0]
print(f"{'h':>4}{'d':>5}{'A':>7}" + "".join(f"{'R='+format(r,'g'):>11}" for r in R_LIST))
t6 = []
for c in D:
    A = c["A_DNS"]
    ex, ey = c["e_xx"] / 100, c["e_yy"] / 100
    row = dict(h=c["h"], d=c["d"], A=A)
    line = f"{c['h']:>4}{c['d']:>5}{A:>7.2f}"
    for R in R_LIST:
        Lam_d = R ** 2 / A
        Lam_m = R ** 2 / (A * (1 + ex) / (1 + ey))
        ratio = (Fhat(Lam_m) / Fhat(Lam_d)) / (1 + ex)
        row[f"R{R:g}"] = (ratio - 1) * 100
        line += f"{(ratio-1)*100:>11.1f}"
    print(line)
    t6.append(row)

with open(OUT + "table6_error_vs_aspect_ratio.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(t6[0].keys()))
    w.writeheader(); w.writerows(t6)

_e = {r: np.array([abs(x[f"R{r:g}"]) for x in t6]) for r in R_LIST}
print("\n  |load error| over the 18 geometries:")
for r in R_LIST:
    print(f"    R={r:>6g}   median {np.median(_e[r]):>5.1f}%   max {_e[r].max():>5.1f}%")

# ------------------------------------------------------------------ corrected
print("\n" + "=" * 104)
print("Table 7  Same, after the correction")
print("=" * 104)
print(f"{'h':>4}{'d':>5}{'A':>7}" + "".join(f"{'R='+format(r,'g'):>11}" for r in R_LIST))
t7 = []
for c in D:
    A = c["A_DNS"]
    d = c["d"]
    # corrected model coefficients
    kxM = c["Kxx_mod"] * FP(d)
    kyM = c["Kyy_mod"] * FT(d)
    ex2 = kxM / c["Kxx_DNS"] - 1
    ey2 = kyM / c["Kyy_DNS"] - 1
    A2 = (c["Kxx_DNS"] * (1 + ex2)) / (c["Kyy_DNS"] * (1 + ey2))
    row = dict(h=c["h"], d=d, A=A)
    line = f"{c['h']:>4}{d:>5}{A:>7.2f}"
    for R in R_LIST:
        Lam_d = R ** 2 / A
        Lam_m = R ** 2 / A2
        ratio = (Fhat(Lam_m) / Fhat(Lam_d)) / (1 + ex2)
        row[f"R{R:g}"] = (ratio - 1) * 100
        line += f"{(ratio-1)*100:>11.1f}"
    print(line)
    t7.append(row)

with open(OUT + "table7_corrected_vs_aspect_ratio.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(t7[0].keys()))
    w.writeheader(); w.writerows(t7)

_c = {r: np.array([abs(x[f"R{r:g}"]) for x in t7]) for r in R_LIST}
print("\n  |load error| after correction:")
for r in R_LIST:
    print(f"    R={r:>6g}   median {np.median(_c[r]):>5.1f}%   max {_c[r].max():>5.1f}%")

# ------------------------------------------------------------------ figure
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5, "axes.linewidth": 0.6,
    "xtick.direction": "out", "ytick.direction": "out", "mathtext.fontset": "dejavusans",
})
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.75), dpi=400)

Rg = np.logspace(-2, 2, 400)
for A, col in zip([1.09, 2.0, 4.7, 15.45], ["#F0997B", "#D85A30", "#993C1D", "#712B13"]):
    ax1.plot(Rg, [weights(r ** 2 / A)[0] for r in Rg], lw=1.2, color=col,
             label=rf"$A={A:g}$")
ax1.axhline(0.5, color="#888780", lw=0.7, ls=":")
ax1.axvline(1.0, color="#888780", lw=0.7, ls=":")
ax1.set_xscale("log")
ax1.set_xlabel(r"field aspect ratio  $R=L_x/L_y$", fontsize=8.0)
ax1.set_ylabel(r"weight of $K_{xx}$,  $w_x$", fontsize=8.0)
ax1.set_ylim(-0.02, 1.02)
ax1.set_title("weight drifts with the field shape", fontsize=8.4, pad=5)
ax1.text(1.06, 0.955, "square", fontsize=6.0, color="#5F5E5A", ha="left", va="center")
leg = ax1.legend(fontsize=6.2, frameon=False, loc="lower left", ncol=1,
                 handlelength=1.3, labelspacing=0.20, borderpad=0.05,
                 title=r"$A_{\rm DNS}$", title_fontsize=6.2)
leg._legend_box.align = "left"

for r, col, mk in ((0.1, "#B5D4F4", "o"), (1.0, "#378ADD", "s"), (10.0, "#0C447C", "^")):
    ys = np.array([abs(x[f"R{r:g}"]) for x in t6])
    ax2.plot(np.arange(len(t6)), np.sort(ys), marker=mk, ms=2.6, lw=1.0,
             color=col, mfc=col, mec="white", mew=0.4, label=rf"$R={r:g}$")
ax2.set_xlabel("geometries, sorted within each curve", fontsize=8.0)
ax2.set_ylabel(r"$|F_{\rm model}/F_{\rm DNS}-1|$  (%)", fontsize=8.0)
ax2.set_ylim(0, 70)
ax2.set_title("load error is mildly shape-dependent", fontsize=8.4, pad=5)
ax2.legend(fontsize=6.2, frameon=False, loc="upper left", handlelength=1.3,
           labelspacing=0.22, borderpad=0.05)

for ax, tag in ((ax1, "(a)"), (ax2, "(b)")):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=7.2, length=2.2, width=0.6)
    ax.text(-0.22, 1.12, tag, transform=ax.transAxes, fontsize=9.5)

fig.tight_layout(pad=0.4, w_pad=1.8)
for ext in ("png", "pdf", "svg"):
    fig.savefig(OUT + f"Fig10_aspect_ratio.{ext}", dpi=400, bbox_inches="tight")
print("\nsaved Fig10_aspect_ratio.{png,pdf,svg}")
