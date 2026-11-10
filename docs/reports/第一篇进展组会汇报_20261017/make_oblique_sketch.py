# -*- coding: utf-8 -*-
"""斜槽几何示意：槽轴与驱动方向夹角 θ，液流实际流向偏转 φ"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, Arc, FancyArrowPatch

plt.rcParams["font.family"] = "DejaVu Sans"

fig, ax = plt.subplots(figsize=(4.4, 2.9), dpi=300)

oy, ox = 0.0, 0.22          # 原点
th = np.radians(45.0)
ph = np.radians(24.34)

# 槽：水平灰带，上下虚线壁
ax.add_patch(Rectangle((0.0, -0.115), 1.62, 0.23, facecolor="#ECECEC",
                       edgecolor="none", zorder=1))
for y in (-0.115, 0.115):
    ax.plot([0.0, 1.62], [y, y], ls=(0, (4.5, 3)), lw=1.0, color="#8A8A8A", zorder=2)

# 驱动方向
L1 = 0.80
ax.add_patch(FancyArrowPatch((ox, oy), (ox + L1*np.cos(th), L1*np.sin(th)),
                             arrowstyle="-|>", mutation_scale=12,
                             lw=1.7, color="#2B2B2B", zorder=4))
# 实际流向
L2 = 0.86
ax.add_patch(FancyArrowPatch((ox, oy), (ox + L2*np.cos(ph), L2*np.sin(ph)),
                             arrowstyle="-|>", mutation_scale=12,
                             lw=1.7, color="#C0392B", zorder=5))

# 角度弧
ax.add_patch(Arc((ox, oy), 0.46, 0.46, theta1=0, theta2=45, lw=0.9, color="#2B2B2B"))
ax.add_patch(Arc((ox, oy), 0.30, 0.30, theta1=0, theta2=24.34, lw=0.9, color="#C0392B"))

# 角度标签（放在两箭头之间的空档）
ax.text(ox + 0.31*np.cos(np.radians(37)), 0.31*np.sin(np.radians(37)),
        r"$\theta$", fontsize=12, color="#2B2B2B", ha="center", va="center")
ax.text(ox + 0.21*np.cos(np.radians(11.5)), 0.21*np.sin(np.radians(11.5)),
        r"$\phi$", fontsize=12, color="#C0392B", ha="center", va="center")

# 说明
ax.text(0.02, -0.245, r"groove axis  ($K_\parallel$)", fontsize=9.2, color="#5A5A5A")
ax.text(ox + L1*np.cos(th) + 0.02, L1*np.sin(th) + 0.02,
        r"drive  $\theta$ = 45$^\circ$", fontsize=9, color="#2B2B2B", va="bottom")
ax.text(ox + L2*np.cos(ph) + 0.03, L2*np.sin(ph) - 0.01,
        r"actual flow  $\phi$ = 24.3$^\circ$", fontsize=9, color="#C0392B", va="top")

ax.set_xlim(-0.03, 1.66)
ax.set_ylim(-0.31, 0.70)
ax.set_aspect("equal")
ax.axis("off")
fig.subplots_adjust(0.005, 0.005, 0.995, 0.995)

out = "/home/dell/yuanyuanxu/SIM240/docs/reports/第一篇进展组会汇报_20261017/assets/oblique_geometry.png"
fig.savefig(out, facecolor="white")
print("saved:", out)
