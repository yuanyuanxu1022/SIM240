import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

P, W, PHI = 240.0, 120.0, 0.5

rows = []
for r in csv.DictReader(open("/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results/summary.csv")):
    if r.get("dx_nm") != "5":
        continue
    rows.append((int(r["h_nm"]), int(r["d_nm"]), r["direction"], float(r["Keff_m3"])))
for f in ("d75_summary.csv", "h25_summary.csv", "d120_summary.csv"):
    for r in csv.DictReader(open("/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results/" + f)):
        rows.append((int(r["h_nm"]), int(r["d_nm"]),
                     "P" if r["case_id"].split("-")[1] == "P" else "T",
                     float(r["Keff_m3"])))

Kp = {(h, d): K for h, d, dr, K in rows if dr == "P"}
Kt = {(h, d): K for h, d, dr, K in rows if dr == "T"}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8.5,
    "axes.linewidth": 0.6,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "mathtext.fontset": "dejavusans",
})

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.9), dpi=400)

hcol = {25: "#B5D4F4", 50: "#85B7EB", 75: "#378ADD", 125: "#0C447C"}
hmark = {25: "o", 50: "s", 75: "^", 125: "D"}

for ax, key, ttl in ((ax1, Kp, r"$K_\parallel$"), (ax1, None, None)):
    pass

for h in (25, 50, 75, 125):
    ds = [d for d in (25, 50, 75, 100, 120) if (h, d) in Kp]
    if not ds:
        continue
    ax1.plot(ds, [Kp[(h, d)] * 1e23 for d in ds], marker=hmark[h], ms=3.2, lw=0.9,
             color=hcol[h], mfc=hcol[h], mec="white", mew=0.4,
             ls="-", label=rf"$h={h}$")
    ax1.plot(ds, [Kt[(h, d)] * 1e23 for d in ds], marker=hmark[h], ms=3.0, lw=0.9,
             color=hcol[h], mfc="white", mec=hcol[h], mew=0.7,
             ls="--")

ax1.set_xlabel(r"groove depth $d$ (nm)", fontsize=8.5)
ax1.set_ylabel(r"$K$  ($10^{-23}\,$m$^3$)", fontsize=8.5)
ax1.set_xlim(15, 130)
ax1.set_ylim(0, 30)
ax1.set_xticks([25, 50, 75, 100, 120])

ax1.text(126, 12.5, r"$K_\parallel$", fontsize=9.5, color="#0C447C", ha="right", va="center")
ax1.text(126, 3.3, r"$K_\perp$", fontsize=9.5, color="#0C447C", ha="right", va="center")

ax1.text(78, 24.2, r"$K_\perp$ varies $<4\%$ over the sampled depths",
         fontsize=6.3, color="#5F5E5A", ha="left", va="center")

leg = ax1.legend(fontsize=6.4, frameon=False, loc="upper left", ncol=2,
                 handlelength=1.6, columnspacing=0.9, labelspacing=0.25,
                 title="gap $h$ (nm)", title_fontsize=6.4)
leg._legend_box.align = "left"

for h in (25, 50, 75, 125):
    ds = [d for d in (25, 50, 75, 100, 120) if (h, d) in Kp and (h, d) in Kt]
    if len(ds) < 2:
        continue
    A = [Kp[(h, d)] / Kt[(h, d)] for d in ds]
    ax2.plot(ds, A, marker=hmark[h], ms=3.2, lw=0.9, color=hcol[h],
             mfc=hcol[h], mec="white", mew=0.4, label=rf"$h={h}$")

ax2.set_xlabel(r"groove depth $d$ (nm)", fontsize=8.5)
ax2.set_ylabel(r"anisotropy  $A=K_\parallel/K_\perp$", fontsize=8.5)
ax2.set_xlim(15, 130)
ax2.set_ylim(0.8, 17)
ax2.set_yscale("log")
ax2.set_xticks([25, 50, 75, 100, 120])
ax2.set_yticks([1, 2, 5, 10, 15])
ax2.set_yticklabels(["1", "2", "5", "10", "15"])
ax2.axhline(1.0, color="#B4B2A9", lw=0.7, ls=":")

ax2.legend(fontsize=6.4, frameon=False, loc="upper left", ncol=2,
           handlelength=1.4, columnspacing=0.8, labelspacing=0.25,
           title="gap $h$ (nm)", title_fontsize=6.4)._legend_box.align = "left"

for ax in (ax1, ax2):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=7.4, length=2.4, width=0.6)
    ax.xaxis.label.set_size(8.2)
    ax.yaxis.label.set_size(8.2)

ax1.text(-0.16, 1.06, "(a)", transform=ax1.transAxes, fontsize=10)
ax2.text(-0.16, 1.06, "(b)", transform=ax2.transAxes, fontsize=10)

fig.tight_layout(pad=0.4, w_pad=1.6)
for ext in ("png", "pdf", "svg"):
    fig.savefig(f"/home/dell/yuanyuanxu/SIM240/figures/paper/Fig4_K_and_anisotropy.{ext}",
                dpi=400, bbox_inches="tight")
print("saved Fig4_K_and_anisotropy.{png,pdf,svg}")
