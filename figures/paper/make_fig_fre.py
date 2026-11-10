import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

P, W = 240.0, 120.0
EPS = W / P

rows = []
for r in csv.DictReader(open("/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results/summary.csv")):
    if r.get("dx_nm") != "5":
        continue
    rows.append((int(r["h_nm"]), int(r["d_nm"]), r["direction"], float(r["Keff_m3"])))
for f in ("d75_summary.csv", "h25_summary.csv", "d120_summary.csv"):
    for r in csv.DictReader(open("/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results/" + f)):
        cid = r["case_id"]
        dr = "P" if cid.split("-")[1] == "P" else "T"
        rows.append((int(r["h_nm"]), int(r["d_nm"]), dr, float(r["Keff_m3"])))

Kp = {(h, d): K for h, d, dr, K in rows if dr == "P"}

data = {}
for (h, d), K in Kp.items():
    K_m2 = K / (P * 1e-9)
    rh = 2 * W * d / (W + 2 * d)
    fRe = 2 * EPS * (rh * 1e-9) ** 2 / K_m2
    data.setdefault(d, []).append((h, fRe))

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.linewidth": 0.6,
    "xtick.direction": "out",
    "ytick.direction": "out",
})

fig, ax = plt.subplots(figsize=(4.2, 3.0), dpi=400)

colors = {25: "#B5D4F4", 50: "#85B7EB", 75: "#378ADD", 100: "#185FA5", 120: "#0C447C"}
markers = {25: "o", 50: "s", 75: "^", 100: "D", 120: "v"}

for d in sorted(data):
    pts = sorted(data[d])
    hs = [p[0] for p in pts]
    fs = [p[1] for p in pts]
    ax.plot(hs, fs, marker=markers[d], markersize=3.4, linewidth=0.9,
            color=colors[d], markerfacecolor=colors[d], markeredgecolor="white",
            markeredgewidth=0.4, label=rf"$d={d}$ nm")

ax.axhspan(13, 16, color="#D3D1C7", alpha=0.55, zorder=0)
ax.text(102, 14.5, r"typical tube value $f\,Re\approx14$", fontsize=6.6,
        color="#5F5E5A", va="center", ha="left")

ax.set_xlabel(r"residual gap $h$ (nm)", fontsize=9)
ax.set_ylabel(r"$f\,Re$ inferred from DNS", fontsize=9)
ax.set_yscale("log")
ax.set_xlim(15, 140)
ax.set_ylim(1, 90)
ax.set_xticks([25, 50, 75, 100, 125])

ax.legend(fontsize=6.6, frameon=False, loc="upper right", ncol=1,
          handlelength=1.4, labelspacing=0.3)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.tick_params(labelsize=8, length=2.5, width=0.6)

fig.tight_layout(pad=0.35)
for ext in ("png", "pdf", "svg"):
    fig.savefig(f"/home/dell/yuanyuanxu/SIM240/figures/paper/Fig_fRe_collapse.{ext}",
                dpi=400, bbox_inches="tight")
print("saved Fig_fRe_collapse.{png,pdf,svg}")

for d in sorted(data):
    pts = sorted(data[d])
    print(f"d={d:3d} (alpha={W/d:4.2f}): " + "  ".join(f"h={h}:{f:6.2f}" for h, f in pts))
