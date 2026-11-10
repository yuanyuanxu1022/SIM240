# -*- coding: utf-8 -*-
"""模型各向异性比随 d/h 的爆炸 vs DNS —— 用于"深间隙段模型失效"页"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.family"] = "DejaVu Sans"

# 模型：A_model = (1+r^3)^2/(4 r^3), r = 1+d/h
def A_model(dh):
    r = 1 + dh
    return (1 + r**3) ** 2 / (4 * r**3)

# DNS 实测（项目 error_table.csv，d=100nm 系列）
dns_dh = np.array([0.80, 1.33, 2.00, 4.00])
dns_A = np.array([1.4319, 2.2104, 3.9158, 15.45])

fig, ax = plt.subplots(figsize=(6.6, 3.5), dpi=300)
fig.subplots_adjust(left=0.11, right=0.97, top=0.90, bottom=0.15)

x = np.linspace(0.3, 10, 400)
ax.plot(x, A_model(x), lw=2.0, color="#C0392B", label="Jain / Ban model")
ax.plot(dns_dh, dns_A, "o", ms=8, mfc="white", mew=2.0, color="#1F4E79",
        label="DNS (this work)", zorder=5)

# Ban 2020 模拟的实际跨度（d/h 0.1→10）
ax.axvspan(2, 10, color="#E8A0A0", alpha=0.16, zorder=0)
ax.axvline(2, color="#B05A5A", lw=1.0, ls="--", alpha=0.7, zorder=1)
ax.text(6.0, 1.35, "Ban 2020 later stage  (gap < 50 nm)", fontsize=8.5,
        color="#8B2E2E", ha="center")

# 标注关键偏差
ax.annotate("", xy=(4.0, 31.75), xytext=(4.0, 15.45),
            arrowprops=dict(arrowstyle="<->", color="#444444", lw=1.0))
ax.text(4.15, 22, "+106%", fontsize=10, color="#C0392B", fontweight="bold")

ax.set_xlabel(r"$d/h$   (groove depth / gap)", fontsize=10.5)
ax.set_ylabel(r"anisotropy  $K_\parallel/K_\perp$", fontsize=10.5)
ax.set_yscale("log")
ax.set_xlim(0.3, 10)
ax.set_ylim(1, 500)
ax.grid(True, which="both", ls=":", lw=0.5, alpha=0.5)
ax.legend(fontsize=9, loc="upper left", frameon=False)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.tick_params(labelsize=9)

out = "/home/dell/yuanyuanxu/SIM240/docs/reports/第一篇进展组会汇报_20261017/assets/dh_scaling.png"
fig.savefig(out, facecolor="white")
print("saved:", out)
print(f"d/h=1: model={A_model(1):.2f}   d/h=4: model={A_model(4):.1f} dns={15.45}")
print(f"d/h=10: model={A_model(10):.0f}")
