"""Fig 7 / Fig 8 — closure error over the sampled matrix.

Fig 7 (B): error versus gap, one curve per groove depth. Shows *why* the
           closure fails: along and across the grooves the error moves in
           OPPOSITE directions with h.
Fig 8 (A): the full h x d matrix as a heat map. Shows *how much*.

Data: 36 resolved cases, dx = 5 nm.
        summary.csv (dx=5): 9 P + 9 T
        d75/h25/d120_summary.csv: 3 P + 3 T each
"""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

BASE = "/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results/"
OUT = "/home/dell/yuanyuanxu/SIM240/figures/paper/"

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


def K_modelled(h, d, along):
    """Stripe average of the cubic conductance, per unit width."""
    hg, hl = h + d, h
    if along:
        return (hg ** 3 + hl ** 3) / 2 / 12 * 1e-27
    return 2 / (1 / hg ** 3 + 1 / hl ** 3) / 12 * 1e-27


E = {}
for h, d, dr, K in rows:
    Km = K_modelled(h, d, dr == "P")
    E[(h, d, dr)] = (Km - K) / K * 100.0

HS = [25, 50, 75, 125]
DS = [25, 50, 75, 100, 120]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8.5,
    "axes.linewidth": 0.6,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "mathtext.fontset": "dejavusans",
})

DCOL = {25: "#F0997B", 50: "#D85A30", 75: "#993C1D", 100: "#712B13", 120: "#4A1B0C"}
DMARK = {25: "o", 50: "s", 75: "^", 100: "D", 120: "v"}

# ----------------------------------------------------------------- Fig 7 (B)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.95), dpi=400)

for ax, dr, ylim, lab in ((ax1, "P", (8, 340), r"along the grooves  $K_\parallel$"),
                          (ax2, "T", (6, 100), r"across the grooves  $K_\perp$")):
    for d in DS:
        xs = [h for h in HS if (h, d, dr) in E]
        if len(xs) < 2:
            continue
        ys = [E[(h, d, dr)] for h in xs]
        ax.plot(xs, ys, marker=DMARK[d], ms=3.2, lw=1.0,
                color=DCOL[d], mfc=DCOL[d], mec="white", mew=0.4,
                label=rf"$d={d}$")
    ax.set_yscale("log")
    ax.set_ylim(*ylim)
    ax.set_xlim(14, 138)
    ax.set_xticks(HS)
    ax.set_xlabel(r"gap $h$ (nm)", fontsize=8.2)
    ax.set_ylabel(r"error of Eqs. (1)  (%)", fontsize=8.2)
    ax.set_title(lab, fontsize=8.6, pad=5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=7.4, length=2.4, width=0.6)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())

# Trend annotations removed 2026-10-19. The previous labels ("falls as the gap
# opens" / "rises as the gap opens") asserted a global monotonic trend that the
# sampled data contradict: at d=100 nm the along-groove error rises from 139% to
# 154% between h=25 and 50 nm, and the across-groove error falls between h=75 and
# 125 nm at d=25 and d=50 nm. The qualified statement now lives in the caption.

leg = ax2.legend(fontsize=6.2, frameon=False, loc="upper left", ncol=1,
                 handlelength=1.2, labelspacing=0.18, borderpad=0.1,
                 handletextpad=0.5,
                 title=r"groove depth $d$ (nm)", title_fontsize=6.2)
leg._legend_box.align = "left"

ax1.text(-0.17, 1.10, "(a)", transform=ax1.transAxes, fontsize=10)
ax2.text(-0.17, 1.10, "(b)", transform=ax2.transAxes, fontsize=10)

fig.tight_layout(pad=0.4, w_pad=1.8)
for ext in ("png", "pdf", "svg"):
    fig.savefig(OUT + f"Fig7_error_vs_gap.{ext}", dpi=400, bbox_inches="tight")
print("saved Fig7_error_vs_gap.{png,pdf,svg}")

# ----------------------------------------------------------------- Fig 8 (A)
def grid(dr):
    G = np.full((len(HS), len(DS)), np.nan)
    for i, h in enumerate(HS):
        for j, d in enumerate(DS):
            if (h, d, dr) in E:
                G[i, j] = E[(h, d, dr)]
    return np.ma.masked_invalid(G)


amps = LinearSegmentedColormap.from_list(
    "amp", ["#FDF3E3", "#FAC775", "#EF9F27", "#BA7517", "#854F0B", "#412402"])
cool = LinearSegmentedColormap.from_list(
    "cool", ["#EAF3F8", "#B5D4F4", "#85B7EB", "#378ADD", "#185FA5", "#042C53"])

fig2, axes = plt.subplots(1, 2, figsize=(7.0, 2.62), dpi=400)

for ax, dr, cmap, ttl, vmax in (
        (axes[0], "P", amps, r"along the grooves  $K_\parallel$", 220),
        (axes[1], "T", cool, r"across the grooves  $K_\perp$", 60)):
    G = grid(dr)
    im = ax.imshow(G, cmap=cmap, vmin=0, vmax=vmax, aspect="auto",
                   origin="lower", interpolation="nearest")
    mask = np.ma.getmaskarray(G)
    for i in range(len(HS)):
        for j in range(len(DS)):
            if mask[i, j]:
                ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, facecolor="#F7F6F1",
                                           edgecolor="#D3D1C7", lw=0.35, hatch="////",
                                           zorder=2))
                continue
            v = float(G[i, j])
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=6.4,
                    color="white" if v > 0.55 * vmax else "#2C2C2A")
    ax.set_xticks(range(len(DS)))
    ax.set_xticklabels([str(d) for d in DS], fontsize=7.4)
    ax.set_yticks(range(len(HS)))
    ax.set_yticklabels([str(h) for h in HS], fontsize=7.4)
    ax.set_xlabel(r"groove depth $d$ (nm)", fontsize=8.2)
    ax.set_ylabel(r"gap $h$ (nm)", fontsize=8.2)
    ax.set_title(ttl, fontsize=8.6, pad=5)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig2.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cb.ax.tick_params(labelsize=6.6, length=2.0, width=0.5)
    cb.ax.set_title("error (%)", fontsize=6.8, pad=4)
    cb.outline.set_linewidth(0.4)
    ax.text(-0.19, 1.13, "(a)" if dr == "P" else "(b)", transform=ax.transAxes, fontsize=10)

fig2.text(0.5, -0.045,
          "hatched cells: not sampled.  18 geometries, 36 principal-direction cases, dx = 5 nm.",
          fontsize=6.4, color="#5F5E5A", ha="center", va="center")

fig2.tight_layout(pad=0.4, w_pad=3.0)
for ext in ("png", "pdf", "svg"):
    fig2.savefig(OUT + f"Fig8_error_map.{ext}", dpi=400, bbox_inches="tight")
print("saved Fig8_error_map.{png,pdf,svg}")

# ------------------------------------------------------------------ numbers
print("\nsanity:")
for dr, lab in (("P", "along"), ("T", "across")):
    v = [E[(h, d, dr)] for h in HS for d in DS if (h, d, dr) in E]
    print(f"  {lab:7s} n={len(v):2d}  min={min(v):+7.1f}%  max={max(v):+7.1f}%  all positive={all(x > 0 for x in v)}")
