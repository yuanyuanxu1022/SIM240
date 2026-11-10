#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成中文版可行区间图（供 PPT 第 7 页使用）。

横条左端 = 下界 h³/12，右端 = 上界（局部立方律），圆点 = 实测 K。
数据与论文附录 E.1 同源：36 条 5 nm 主结果 + h=100 nm 新增 2 条 = 38 条。
本脚本只做数据搬运与绘图，不改任何数值口径。
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FixedFormatter, FixedLocator

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

MAP36 = os.path.join(ROOT, "docs/reports/SIM240_manuscript_revision_20261018/map36_evidence.csv")
BOUND = os.path.join(ROOT, "docs/reports/PAPER1_闭环方案_20261105/bound_check_44_points.csv")

# 中文字体（思源黑体）
for cand in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
             "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"):
    if os.path.exists(cand):
        font_manager.fontManager.addfont(cand)
        CJK = font_manager.FontProperties(fname=cand).get_name()
        break
else:
    CJK = "DejaVu Sans"

plt.rcParams.update({
    "font.family": CJK,
    "font.size": 9,
    "axes.linewidth": 0.7,
    "axes.unicode_minus": False,
})

BLUE = "#1E4FA8"
NAVY = "#0E3F8C"
TEAL = "#0F6E56"
PALE_B = "#C5DDF7"
PALE_T = "#9FE1CB"
GREY = "#5F5E5A"
TXT = "#1A2230"

LB = lambda h: (h * 1e-9) ** 3 / 12.0
UB_PAR = lambda h, d: ((h * 1e-9) ** 3 + ((h + d) * 1e-9) ** 3) / 24.0
UB_PERP = lambda h, d: (h * 1e-9) ** 3 * ((h + d) * 1e-9) ** 3 / (
    6 * ((h * 1e-9) ** 3 + ((h + d) * 1e-9) ** 3))


def load_rows():
    rows = []
    with open(MAP36, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append((float(r["h_nm"]), float(r["d_nm"]), r["direction"],
                         float(r["K_DNS_m3"])))
    with open(BOUND, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if abs(float(r["h_nm"]) - 100) < 1e-9:
                rows.append((float(r["h_nm"]), float(r["d_nm"]), r["direction"],
                             float(r["K_reference_m3"])))
    return rows


def series(rows, direction):
    sel = [x for x in rows if x[2] == direction]
    sel.sort(key=lambda x: (x[0], x[1]))
    out = []
    for h, d, _, k in sel:
        lb = LB(h)
        ub = UB_PAR(h, d) if direction == "P" else UB_PERP(h, d)
        out.append((h, d, k / lb, ub / lb))
    return out


def main():
    rows = load_rows()
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 4.55))

    panels = [
        ("沿槽方向  $K_\\parallel$", "P", BLUE, PALE_B),
        ("横槽方向  $K_\\perp$", "T", TEAL, PALE_T),
    ]
    for ax, (title, direction, dot, bar) in zip(axes, panels):
        ser = series(rows, direction)
        n = len(ser)
        for i, (h, d, kk, ww) in enumerate(ser):
            y = n - 1 - i
            ax.plot([1, ww], [y, y], color=bar, lw=5.2,
                    solid_capstyle="round", zorder=2)
            ax.plot([kk], [y], "o", ms=4.0, color=dot, zorder=3)
            ax.text(0.97, y, f"{int(h)}/{int(d)}", ha="right", va="center",
                    fontsize=7.4, color=TXT, zorder=4)
            ax.text(78, y, f"{ww:.2f}", ha="right", va="center",
                    fontsize=7.2, color=GREY, zorder=4)

        ax.set_xscale("log")
        ax.set_xlim(0.90, 85)
        ax.set_ylim(-1.2, n)
        ax.xaxis.set_major_locator(FixedLocator([1, 2, 5, 10, 20, 50]))
        ax.xaxis.set_major_formatter(FixedFormatter(["1", "2", "5", "10", "20", "50"]))
        ax.set_yticks([])
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(axis="x", labelsize=7.6, colors=GREY, length=3)
        ax.set_xlabel("相对下界 h³/12 的倍数（对数）", fontsize=8.2, color=GREY, labelpad=3)
        ax.set_title(title, fontsize=10.5, color=NAVY, loc="left", pad=6)
        ax.grid(axis="x", color="#D6DCE5", lw=0.5, alpha=0.8, zorder=0)
        ax.axvline(1, color="#8B97A8", lw=0.9, ls=(0, (3, 2)), zorder=1)

    axes[0].text(0.01, -0.155, "h/d", transform=axes[0].transAxes,
                 fontsize=7.4, color=GREY, ha="left")
    axes[0].text(0.985, -0.155, "区间宽度", transform=axes[0].transAxes,
                 fontsize=7.4, color=GREY, ha="right")
    axes[1].text(0.01, -0.155, "h/d", transform=axes[1].transAxes,
                 fontsize=7.4, color=GREY, ha="left")
    axes[1].text(0.985, -0.155, "区间宽度", transform=axes[1].transAxes,
                 fontsize=7.4, color=GREY, ha="right")

    fig.tight_layout(pad=0.6)
    out = os.path.join(HERE, "interval_cn.png")
    fig.savefig(out, dpi=220, bbox_inches="tight", facecolor="white")
    print("saved", out)

    # 顺带打印闭式核对，供报告引用
    for direction, name in (("P", "沿槽"), ("T", "横槽")):
        ser = series(rows, direction)
        wmax = max(s[-1] for s in [(x[2], x[3]) for x in ser])
        print(f"{name}: 区间宽度 {min(x[3] for x in ser):.4f}~{wmax:.4f}")


if __name__ == "__main__":
    main()
