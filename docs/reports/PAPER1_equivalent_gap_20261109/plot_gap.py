#!/usr/bin/env python3
"""等效缝高比 H/h 随槽深比 d/w 的变化，沿槽与横槽分列。"""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "Noto Serif CJK SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

SRC = "/home/dell/yuanyuanxu/SIM240/docs/reports/PAPER1_equivalent_gap_20261109/equivalent_gap_table.csv"
OUT = "/home/dell/yuanyuanxu/SIM240/docs/reports/PAPER1_equivalent_gap_20261109/equivalent_gap.png"

rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
data = {}
for r in rows:
    data.setdefault((float(r["h_nm"]), r["direction"]), []).append(
        (float(r["d_over_w"]), float(r["H_ratio"])))

hs = sorted({k[0] for k in data})
# 单色系深浅：薄隙深、厚隙浅
colors = {25: "#B3261E", 50: "#D4641A", 75: "#1F6FB2", 100: "#4C9A2A", 125: "#6B5B95"}
markers = {25: "o", 50: "s", 75: "^", 100: "D", 125: "v"}

fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.4))

for ax, dirn, title in [(axes[0], "沿槽", "沿槽方向：槽深直接加流道"),
                        (axes[1], "横槽", "横槽方向：最窄处说了算")]:
    for h in hs:
        if (h, dirn) not in data:
            continue
        pts = sorted(data[(h, dirn)])
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        ax.plot(xs, ys, marker=markers[h], ms=6.5, lw=1.8, color=colors[h],
                label=f"h = {h:.0f} nm", alpha=0.92,
                markerfacecolor="white" if h >= 100 else colors[h],
                markeredgewidth=1.6 if h >= 100 else 1.0)
    ax.axhline(1.0, color="#888888", lw=1.0, ls=":")
    ax.set_xlabel("槽深比  d / w   （w = 120 nm 恒定）", fontsize=10.5)
    ax.set_title(title, fontsize=12.5, pad=9)
    ax.grid(alpha=0.28, lw=0.7)
    ax.set_xlim(0.13, 1.05)
    ax.set_ylim(0.95, 3.18 if dirn == "沿槽" else 1.32)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

axes[0].set_ylabel("等效缝高比   H / h", fontsize=11)
axes[0].text(0.16, 1.02, "H/h = 1：与名义平板缝完全相同", fontsize=9, color="#666666")
axes[0].legend(frameon=False, fontsize=9, loc="upper left", ncol=1, handlelength=1.6)

# 右图注：横槽饱和
axes[1].annotate("同一条水平带：横槽流量由最小间隙 h 决定\n加深槽几乎无效（H/h 只从 1.04 走到 1.20）",
                 xy=(0.62, 1.14), xytext=(0.22, 1.26), fontsize=9.2, color="#333333",
                 arrowprops=dict(arrowstyle="->", color="#777777", lw=0.9,
                                 connectionstyle="arc3,rad=0.16"))

fig.suptitle("等效缝高比：把导度翻译成“相当于多厚的平板缝”", fontsize=13.5, y=0.985)
fig.tight_layout(rect=[0, 0.02, 1, 0.94])
fig.savefig(OUT, dpi=190, facecolor="white")
print("saved", OUT)
