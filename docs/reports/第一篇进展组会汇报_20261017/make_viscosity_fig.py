# -*- coding: utf-8 -*-
"""黏度无关性对照图：左 K（不变），右 J（按 1/μ 缩放）——归一化显示"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.family"] = "DejaVu Sans"

K_base, K_mu15 = 9.834076e-23, 9.834013e-23
J_base, J_mu15 = 9.834076e-12, 6.556008e-13

fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0), dpi=300)
fig.subplots_adjust(left=0.10, right=0.97, top=0.82, bottom=0.17, wspace=0.30)

x = np.arange(2)
labels = ["mu = 1", "mu = 15"]

# ---- 左：K 归一化到 mu=1 ----
ax = axes[0]
vals = [K_base/K_base, K_mu15/K_base]
ax.bar(x, vals, width=0.46, color=["#378ADD", "#85B7EB"], edgecolor="#1F4E79", lw=0.8)
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=10)
ax.set_ylabel("normalised  $K_\\parallel$", fontsize=10)
ax.set_title("Permeability: identical", fontsize=11, pad=8)
ax.set_ylim(0, 1.30)
ax.axhline(1.0, ls=":", lw=1.0, color="#888888")
ax.text(0, 1.02, "1.0000", ha="center", va="bottom", fontsize=9)
ax.text(1, 1.02, "1.0000", ha="center", va="bottom", fontsize=9)
ax.text(0.5, 1.19, "diff 0.0006%", ha="center", fontsize=10,
        color="#C0392B", fontweight="bold")
ax.tick_params(labelsize=9)
for s in ("top", "right"): ax.spines[s].set_visible(False)

# ---- 右：J 归一化 ----
ax = axes[1]
vals2 = [J_base/J_base, J_mu15/J_base]
ax.bar(x, vals2, width=0.46, color=["#C0392B", "#E8A0A0"], edgecolor="#7B241C", lw=0.8)
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=10)
ax.set_ylabel("normalised  $J_\\parallel$", fontsize=10)
ax.set_title("Flow rate: 1/15", fontsize=11, pad=8)
ax.set_ylim(0, 1.30)
ax.axhline(1.0, ls=":", lw=1.0, color="#888888")
ax.text(0, 1.02, "1.000", ha="center", va="bottom", fontsize=9)
ax.text(1, vals2[1]+0.03, "0.0667", ha="center", va="bottom", fontsize=9)
ax.annotate("15x slower", xy=(1.0, 0.30), ha="center", fontsize=10,
            color="#7B241C", fontweight="bold")
ax.tick_params(labelsize=9)
for s in ("top", "right"): ax.spines[s].set_visible(False)

out = "/home/dell/yuanyuanxu/SIM240/docs/reports/第一篇进展组会汇报_20261017/assets/viscosity_check.png"
fig.savefig(out, facecolor="white")
print("saved:", out)
