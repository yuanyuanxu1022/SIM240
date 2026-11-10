#!/usr/bin/env python3
"""Correction figure for the group-meeting slide deck (V2 factors).

Panel (a): the withheld depth d = 75 nm, before and after correction.
Panel (b): every sampled geometry, corrected residual against d/w, with the
two quoted bounds drawn.  Panel (b) is what shows that the correction collapses
the 18 points into a band rather than merely shifting them.

Data are read from the result CSVs; no numbers are typed in.
Output: assets/correction_validation.png
"""

import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "..", "..", "CASE", "D_series",
                   "D2_groove_error_map", "results")
OUT = os.path.join(HERE, "assets", "correction_validation.png")

W = 120.0
A_P, B_P = 1.7685, 1.6331
A_T, B_T = 0.4900, 0.6990


def closure(h, d, along):
    hg, hl = h + d, h
    v = (hg ** 3 + hl ** 3) / 2 if along else 2 / (1 / hg ** 3 + 1 / hl ** 3)
    return v / 12 * 1e-27


def factor(d, a, b):
    return 1 / (1 + a * (d / W) ** b)


def load():
    K = {}
    with open(os.path.join(RES, "summary.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("dx_nm") == "5":
                K[(float(r["h_nm"]), float(r["d_nm"]), r["direction"])] = float(r["Keff_m3"])
    for fn in ("d75_summary.csv", "h25_summary.csv", "d120_summary.csv"):
        with open(os.path.join(RES, fn), encoding="utf-8") as f:
            for r in csv.DictReader(f):
                dr = "P" if r["case_id"].split("-")[1] == "P" else "T"
                K[(float(r["h_nm"]), float(r["d_nm"]), dr)] = float(r["Keff_m3"])
    return K


def resid(h, d, dr, K, corrected):
    Km = closure(h, d, dr == "P")
    if corrected:
        Km *= factor(d, A_P, B_P) if dr == "P" else factor(d, A_T, B_T)
    return (Km - K[(h, d, dr)]) / K[(h, d, dr)] * 100


def main():
    K = load()
    plt.rcParams.update({
        "font.size": 7.4, "axes.linewidth": 0.7, "xtick.major.width": 0.7,
        "ytick.major.width": 0.7, "mathtext.fontset": "dejavusans",
    })
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.55),
                                   gridspec_kw={"width_ratios": [1.02, 1.0],
                                                "wspace": 0.30})

    # ---------------- (a) hold-out, before vs after ----------------
    hs = [50, 75, 125]
    labels, e0, e1 = [], [], []
    for dr, tag in (("P", "along"), ("T", "across")):
        for h in hs:
            labels.append(f"{tag}\nh={h}")
            e0.append(resid(h, 75, dr, K, False))
            e1.append(resid(h, 75, dr, K, True))

    x = np.arange(len(labels))
    bw = 0.36
    ax1.bar(x - bw / 2, e0, bw, color="#D9534F", label="closure, uncorrected")
    ax1.bar(x + bw / 2, e1, bw, color="#2E7D5B", label="with correction")
    ax1.axhline(0, color="black", lw=0.7)
    ax1.axhline(10.5, color="#1F5E8C", lw=0.7, ls="--", alpha=0.8)
    ax1.axhline(-10.5, color="#1F5E8C", lw=0.7, ls="--", alpha=0.8)
    ax1.axhline(6.9, color="#B36B00", lw=0.7, ls=":", alpha=0.85)
    ax1.axhline(-6.9, color="#B36B00", lw=0.7, ls=":", alpha=0.85)

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=5.9, linespacing=1.25)
    ax1.set_ylabel("relative error vs DNS (%)", labelpad=2)
    ax1.set_ylim(-24, 118)
    ax1.set_xlim(-0.62, 5.58)
    ax1.set_title("(a) held-out depth  $d=75$ nm", fontsize=7.8, pad=4)
    ax1.legend(frameon=False, fontsize=6.2, loc="upper right", handlelength=1.0,
               bbox_to_anchor=(1.005, 1.02))

    # annotate the two extremes
    for xi, v in zip(x, e1):
        ax1.text(xi + bw / 2, v + (2.0 if v >= 0 else -2.0), f"{v:+.1f}",
                 ha="center", va="bottom" if v >= 0 else "top",
                 fontsize=5.4, color="#17603F", fontweight="bold")

    # ---------------- (b) all geometries ----------------
    keys = sorted({(h, d) for (h, d, _) in K})
    for dr, mk, col, lab in (("P", "o", "#1F5E8C", r"$K_\parallel$"),
                             ("T", "s", "#B36B00", r"$K_\perp$")):
        xs, ys = [], []
        for h, d in keys:
            if (h, d, dr) not in K:
                continue
            xs.append(d / W)
            ys.append(resid(h, d, dr, K, True))
        ax2.scatter(xs, ys, s=15, marker=mk, facecolors="none", edgecolors=col,
                    linewidths=0.85, label=lab, zorder=3)
    ax2.axhline(0, color="black", lw=0.7)
    ax2.axhline(10.5, color="#1F5E8C", lw=0.7, ls="--", alpha=0.75)
    ax2.axhline(-10.5, color="#1F5E8C", lw=0.7, ls="--", alpha=0.75)
    ax2.axhline(6.9, color="#B36B00", lw=0.7, ls=":", alpha=0.85)
    ax2.axhline(-6.9, color="#B36B00", lw=0.7, ls=":", alpha=0.85)
    ax2.text(0.965, 11.4, r"$\pm10.5\%$", fontsize=6.2, color="#1F5E8C",
             ha="right", va="bottom")
    ax2.text(0.965, -7.6, r"$\pm6.9\%$", fontsize=6.2, color="#B36B00",
             ha="right", va="top")
    ax2.set_xlabel("aspect ratio  $d/w$", labelpad=2)
    ax2.set_ylabel("residual after correction (%)", labelpad=2)
    ax2.set_xlim(0.10, 1.06)
    ax2.set_ylim(-22, 16)
    ax2.set_title("(b) all 18 sampled geometries", fontsize=7.8, pad=4)
    ax2.legend(frameon=False, fontsize=6.3, loc="lower left", handletextpad=0.4)

    for ax in (ax1, ax2):
        ax.tick_params(direction="out", length=2.4, pad=1.8)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    fig.text(0.5, 0.035,
             "bands:  dashed $\\pm10.5\\%$ (along grooves)    "
             "dotted $\\pm6.9\\%$ (across grooves)",
             fontsize=6.0, color="#444444", ha="center", va="center")
    fig.subplots_adjust(left=0.085, right=0.985, top=0.885, bottom=0.225)
    fig.savefig(OUT, dpi=400)
    fig.savefig(OUT.replace(".png", ".pdf"))
    print("written:", OUT)
    print("\nhold-out check:")
    for lab, a, b in zip(labels, e0, e1):
        print(f"  {lab:12s} {a:+7.2f}%  ->  {b:+6.2f}%")
    all1 = [resid(h, d, dr, K, True) for (h, d, dr) in K]
    print(f"\nall 18 corrected: {min(all1):+.2f}% .. {max(all1):+.2f}%")


if __name__ == "__main__":
    main()
