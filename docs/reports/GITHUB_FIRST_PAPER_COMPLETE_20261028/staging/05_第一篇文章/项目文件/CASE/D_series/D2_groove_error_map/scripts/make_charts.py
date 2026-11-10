#!/usr/bin/env python3
"""D2 误差地图出图：热力图 + 敏感性 + 效率（论文级 matplotlib）"""
import csv, os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results/analysis"
HS, DS = [50, 75, 125], [25, 50, 100]

rows = {}
for r in csv.DictReader(open(os.path.join(OUT, "error_table.csv"))):
    key = (int(r["h_nm"]), int(r["d_nm"]), r["dir"])
    rows[key] = {"K": float(r["K_dns_m3"]), "E": float(r["E_pct"]),
                 "A_dns": float(r["A_dns"]), "A_mod": float(r["A_model"]),
                 "eta": float(r["eta"])}

def grid(fn):
    return np.array([[fn(rows[(h, d, "P")], rows[(h, d, "T")]) for d in DS] for h in HS])

Epar = np.array([[rows[(h, d, "P")]["E"] for d in DS] for h in HS])
Eper = np.array([[rows[(h, d, "T")]["E"] for d in DS] for h in HS])
eta_par = np.array([[rows[(h, d, "P")]["eta"] for d in DS] for h in HS])
eta_per = np.array([[rows[(h, d, "T")]["eta"] for d in DS] for h in HS])

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})

fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
for ax, M, title in ((axes[0], Epar, "E_parallel = (K_model-K_dns)/K_dns (%)"),
                     (axes[1], Eper, "E_perpendicular (%)")):
    im = ax.imshow(M, cmap="YlOrRd", aspect="auto", origin="lower")
    ax.set_xticks(range(3)); ax.set_xticklabels([f"d={d}" for d in DS])
    ax.set_yticks(range(3)); ax.set_yticklabels([f"h={h}" for h in HS])
    ax.set_title(title)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center",
                    color="black", fontsize=9)
    fig.colorbar(im, ax=ax)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "error_map.png"), dpi=200)
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
for ax, M, title in ((axes[0], eta_par, "eta_parallel = K_par / K_flat,V"),
                     (axes[1], eta_per, "eta_perpendicular")):
    im = ax.imshow(M, cmap="RdYlGn", aspect="auto", origin="lower", vmin=0.15, vmax=1.0)
    ax.set_xticks(range(3)); ax.set_xticklabels([f"d={d}" for d in DS])
    ax.set_yticks(range(3)); ax.set_yticklabels([f"h={h}" for h in HS])
    ax.set_title(title)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center",
                    color="black", fontsize=9)
    fig.colorbar(im, ax=ax)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "efficiency_map.png"), dpi=200)
plt.close(fig)

# 弹性散点
el = [r for r in csv.DictReader(open(os.path.join(OUT, "elasticity.csv")))]
h_P = [float(r["S_hat"]) for r in el if r["swept"] == "h" and r["dir"] == "P"]
h_T = [float(r["S_hat"]) for r in el if r["swept"] == "h" and r["dir"] == "T"]
d_P = [float(r["S_hat"]) for r in el if r["swept"] == "d" and r["dir"] == "P"]
d_T = [float(r["S_hat"]) for r in el if r["swept"] == "d" and r["dir"] == "T"]
fig, ax = plt.subplots(figsize=(6, 4.2))
labels = ["S_h (P)", "S_h (T)", "S_d (P)", "S_d (T)"]
bp = ax.boxplot([h_P, h_T, d_P, d_T], tick_labels=labels, patch_artist=True)
colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]
for patch, c in zip(bp["boxes"], colors):
    patch.set_facecolor(c); patch.set_alpha(0.7)
ax.axhline(0, color="gray", lw=0.5)
ax.set_ylabel("interval elasticity S_hat")
ax.set_title("which knob matters: gap h vs groove depth d")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "elasticity.png"), dpi=200)
plt.close(fig)

# 各向异性 模型 vs DNS
A_dns = np.array([[rows[(h, d, "P")]["A_dns"] for d in DS] for h in HS])
A_mod = np.array([[rows[(h, d, "P")]["A_mod"] for d in DS] for h in HS])
fig, ax = plt.subplots(figsize=(5.4, 4.2))
ax.plot(A_dns.flatten(), A_mod.flatten(), "o", color="#C44E52")
lim = [1, 8]
ax.plot(lim, lim, "k--", lw=0.8, label="perfect")
ax.set_xlabel("DNS anisotropy A = K_par/K_per")
ax.set_ylabel("model anisotropy (Jain / local cubic law)")
ax.legend(); ax.set_title("anisotropy: model vs DNS (9 geometries)")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "anisotropy.png"), dpi=200)
plt.close(fig)

print("charts written to", OUT)
