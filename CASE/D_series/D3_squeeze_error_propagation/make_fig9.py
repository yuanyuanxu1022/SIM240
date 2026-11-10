"""Figures for the squeeze-film error propagation (D3)."""
import csv
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "/home/dell/yuanyuanxu/SIM240/CASE/D_series/D3_squeeze_error_propagation/results/"
D = json.load(open(OUT + "propagation.json"))
cases, times = D["cases"], D["times"]
T4 = {}
for r in csv.DictReader(open(OUT + "table4_corrected_closure.csv", encoding="utf-8-sig")):
    T4[(int(r["h"]), int(r["d"]))] = (float(r["F_uncorrected"]), float(r["F_corrected"]))

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8.5,
    "axes.linewidth": 0.6,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "mathtext.fontset": "dejavusans",
})

HS = [25, 50, 75, 125]
DS = [25, 50, 75, 100, 120]
HCOL = {25: "#F0997B", 50: "#D85A30", 75: "#993C1D", 125: "#712B13"}
HMARK = {25: "o", 50: "s", 75: "^", 125: "D"}
C = {(c["h"], c["d"]): c for c in cases}

fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, figsize=(7.0, 2.5), dpi=400)

# ---------------------------------------------------------------- (a) load ratio
for h in HS:
    xs = [d for d in DS if (h, d) in C]
    if len(xs) < 2:
        continue
    ys = [C[(h, d)]["F_B_ratio"] for d in xs]
    ax1.plot(xs, ys, marker=HMARK[h], ms=3.0, lw=1.0, color=HCOL[h],
             mfc=HCOL[h], mec="white", mew=0.4, label=rf"$h={h}$")
ax1.axhline(1.0, color="#888780", lw=0.8, ls=":")
ax1.set_xlabel(r"groove depth $d$ (nm)", fontsize=8.0)
ax1.set_ylabel(r"$F_{\rm mod}/F_{\rm ref}$", fontsize=8.0)
ax1.set_ylim(0.30, 1.10)
ax1.set_xlim(12, 132)
ax1.set_xticks(DS)
ax1.set_title("squeeze load", fontsize=8.2, pad=5)
ax1.text(130, 1.005, "no error", fontsize=6.0, color="#5F5E5A", ha="right", va="bottom")

# ---------------------------------------------------------------- (b) time ratio
ds_t = [t["d"] for t in times if t["h0"] == 125 and t["hf"] == 50]
for key, mk, lab, mew, fc in (("t_B_ratio", "o", "integrated", 0.4, None),
                              ("t_B_if_frozen", "o", r"frozen at $h_0$", 0.9, "white")):
    ys = [next(t[key] for t in times if t["d"] == d and t["h0"] == 125 and t["hf"] == 50)
          for d in ds_t]
    ax2.plot(ds_t, ys, marker=mk, ms=3.4, lw=1.0, color="#378ADD",
             mfc=("#378ADD" if fc is None else fc), mec="#378ADD", mew=mew, label=lab)
ax2.axhline(1.0, color="#888780", lw=0.8, ls=":")
ax2.set_xlabel(r"groove depth $d$ (nm)", fontsize=8.0)
ax2.set_ylabel(r"$t_{\rm mod}/t_{\rm ref}$", fontsize=8.0)
ax2.set_ylim(0.30, 1.08)
ax2.set_xlim(12, 132)
ax2.set_xticks(ds_t)
ax2.set_title(r"drainage time, $F$ const.", fontsize=8.2, pad=5)
ax2.legend(fontsize=6.2, frameon=False, loc="upper right", handlelength=1.3,
           labelspacing=0.25, borderpad=0.1)

# ---------------------------------------------------------------- (c) weights
for h in HS:
    xs = [C[(h, d)]["A_DNS"] for d in DS if (h, d) in C]
    ys = [C[(h, d)]["w_x"] for d in DS if (h, d) in C]
    ax3.plot(xs, ys, marker=HMARK[h], ms=3.0, lw=0.9, color=HCOL[h],
             mfc=HCOL[h], mec="white", mew=0.4)
ax3.axhline(0.5, color="#888780", lw=0.8, ls=":")
ax3.set_xscale("log")
ax3.set_xlabel(r"anisotropy  $A=K_\parallel/K_\perp$", fontsize=8.0)
ax3.set_ylabel(r"weight of $K_\parallel$ in the load, $w_\parallel$", fontsize=8.0)
ax3.set_ylim(0.42, 0.96)
ax3.set_title(r"weight of $K_\parallel$", fontsize=8.2, pad=5)
ax3.annotate("equal split at $A=1$", xy=(1.02, 0.505), xytext=(2.2, 0.455),
             fontsize=6.0, color="#5F5E5A", ha="left", va="center",
             arrowprops=dict(arrowstyle="-", lw=0.6, color="#888780",
                             shrinkA=2, shrinkB=2))

# ---------------------------------------------------------------- (d) correction
for h in HS:
    xs = [d for d in DS if (h, d) in T4]
    if len(xs) < 2:
        continue
    ax4.plot(xs, [T4[(h, d)][0] for d in xs], marker=HMARK[h], ms=2.6, lw=0.9,
             color=HCOL[h], mfc="white", mec=HCOL[h], mew=0.8, ls="--")
    ax4.plot(xs, [T4[(h, d)][1] for d in xs], marker=HMARK[h], ms=2.6, lw=0.9,
             color=HCOL[h], mfc=HCOL[h], mec="white", mew=0.4, ls="-")
ax4.axhline(1.0, color="#888780", lw=0.8, ls=":")
ax4.set_xlabel(r"groove depth $d$ (nm)", fontsize=8.0)
ax4.set_ylabel(r"$F_{\rm mod}/F_{\rm ref}$", fontsize=8.0)
ax4.set_ylim(0.30, 1.12)
ax4.set_xlim(12, 132)
ax4.set_xticks(DS)
ax4.set_title("after correction", fontsize=8.2, pad=5)
ax4.text(20, 1.075, "open: Eq. (1)\nfilled: corrected", fontsize=5.4,
         color="#5F5E5A", ha="left", va="top", linespacing=1.35)

for ax, tag in ((ax1, "(a)"), (ax2, "(b)"), (ax3, "(c)"), (ax4, "(d)")):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=7.0, length=2.2, width=0.6)
    ax.text(-0.22, 1.11, tag, transform=ax.transAxes, fontsize=9.5)

leg = ax1.legend(fontsize=5.8, frameon=False, loc="lower left", ncol=1,
                 handlelength=1.3, labelspacing=0.20, borderpad=0.05,
                 handletextpad=0.5, title=r"gap $h$ (nm)", title_fontsize=6.2)
leg._legend_box.align = "left"

fig.tight_layout(pad=0.4, w_pad=1.0)
for ext in ("png", "pdf", "svg"):
    fig.savefig(OUT + f"Fig9_error_propagation.{ext}", dpi=400, bbox_inches="tight")
print("saved Fig9_error_propagation.{png,pdf,svg}")
