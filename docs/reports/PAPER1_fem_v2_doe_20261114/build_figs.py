#!/usr/bin/env python3
"""Figures for the descriptive trends on the FEM/FVM reference set.

FIG5: fixed d, sweep h.  FIG6: fixed h, sweep d.
Rows: original local-cubic law deviation / fixed-V2 signed residual.
Columns: along-groove P / transverse T.

Only sampled points are connected; h = 25 nm points are drawn as open markers
because that gap has no full d sweep.
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path("/home/dell/yuanyuanxu/SIM240")
SRC = ROOT / "docs/reports/PAPER1_fem_v2_results_20261114/PAIR_TABLE_v2.csv"
OUT = ROOT / "docs/reports/PAPER1_fem_v2_doe_20261114"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Noto Sans CJK SC", "WenQuanYi Micro Hei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "legend.fontsize": 8,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "axes.edgecolor": "#888780",
    "axes.linewidth": 0.7,
    "grid.color": "#D3D1C7",
    "grid.linewidth": 0.5,
    "grid.alpha": 0.55,
})

D_LEVELS = [25, 50, 75, 100, 120]
H_LEVELS = [50, 75, 125]
D_COLORS = {25: "#C0504D", 50: "#E8A33D", 75: "#4F81BD", 100: "#5B9E6B", 120: "#8064A2"}
H_COLORS = {50: "#C0504D", 75: "#4F81BD", 125: "#5B9E6B"}

rows = {}
for r in csv.DictReader(SRC.open()):
    h, d = r["geometry"].split("/")
    rows[(int(h[1:]), int(d[1:]))] = r


def val(h, d, col):
    r = rows.get((h, d))
    if r is None:
        return None
    v = r[col]
    return float(v) if v not in ("", None) else None


PANELS = [
    ("P_LC_vs_ref_percent", "沿槽 P：原公式偏差"),
    ("P_V2_vs_ref_percent", "沿槽 P：固定 V2 有符号残差"),
    ("T_LC_vs_ref_percent", "横槽 T：原公式偏差"),
    ("T_V2_vs_ref_percent", "横槽 T：固定 V2 有符号残差"),
]


def decorate(ax, title, ylabel):
    ax.set_title(title, loc="left", fontsize=10.5, pad=6)
    ax.set_ylabel(ylabel)
    ax.grid(True, which="major")
    ax.axhline(0.0, color="#444444", linewidth=0.8, zorder=1)


def fig_fixed_d():
    fig, axes = plt.subplots(2, 2, figsize=(9.6, 6.6), sharex=True)
    for ax, (col, title) in zip(axes.ravel(), PANELS):
        for d in D_LEVELS:
            xs = [h for h in H_LEVELS if val(h, d, col) is not None]
            ys = [val(h, d, col) for h in xs]
            if len(xs) >= 2:
                ax.plot(xs, ys, "-", color=D_COLORS[d], linewidth=1.3,
                        marker="o", markersize=4, zorder=3)
            elif len(xs) == 1:
                ax.plot(xs, ys, "o", color=D_COLORS[d], markersize=4, zorder=3)
        # h = 25 nm: open markers, no connecting line (incomplete sweep)
        for d in D_LEVELS:
            v = val(25, d, col)
            if v is not None:
                ax.plot([25], [v], "o", markerfacecolor="white", markeredgewidth=1.2,
                        markeredgecolor=D_COLORS[d], markersize=5, zorder=4)
        ax.set_xscale("log")
        ax.set_xticks([25, 50, 75, 125])
        ax.set_xticklabels(["25", "50", "75", "125"])
        ax.set_xlim(21, 145)
        decorate(ax, title, "相对偏差 (%)")
    for ax in axes[1]:
        ax.set_xlabel("间隙 h (nm)，对数刻度（仅辅助阅读已采样点）")
    handles = [Line2D([0], [0], color=D_COLORS[d], marker="o", markersize=4,
                      linewidth=1.3, label=f"d={d} nm") for d in D_LEVELS]
    handles.append(Line2D([0], [0], color="#777777", marker="o", markersize=5,
                          markerfacecolor="white", linewidth=0, label="h=25（空心，采样不全）"))
    fig.legend(handles=handles, loc="lower center", ncol=6, frameon=False,
               bbox_to_anchor=(0.5, -0.005))
    fig.suptitle("图 5  固定槽深、改变间隙：FEM/FVM 独立参考下的偏差（15 点平衡矩阵 + h25 单列）",
                 fontsize=11.5, y=0.985)
    fig.tight_layout(rect=(0, 0.05, 1, 0.96))
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"FIG5_DOE_new_reference_fixed_d.{ext}", bbox_inches="tight")
    plt.close(fig)


def fig_fixed_h():
    fig, axes = plt.subplots(2, 2, figsize=(9.6, 6.6), sharex=True)
    for ax, (col, title) in zip(axes.ravel(), PANELS):
        for h in H_LEVELS:
            xs = [d for d in D_LEVELS if val(h, d, col) is not None]
            ys = [val(h, d, col) for d in xs]
            ax.plot(xs, ys, "-", color=H_COLORS[h], linewidth=1.3,
                    marker="o", markersize=4, zorder=3)
        ax.set_xticks(D_LEVELS)
        ax.set_xlim(18, 127)
        decorate(ax, title, "相对偏差 (%)")
    for ax in axes[1]:
        ax.set_xlabel("槽深 d (nm)，连线仅辅助阅读已采样点")
    handles = [Line2D([0], [0], color=H_COLORS[h], marker="o", markersize=4,
                      linewidth=1.3, label=f"h={h} nm") for h in H_LEVELS]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, -0.005))
    fig.suptitle("图 6  固定间隙、改变槽深：FEM/FVM 独立参考下的偏差（15 点平衡矩阵）",
                 fontsize=11.5, y=0.985)
    fig.tight_layout(rect=(0, 0.05, 1, 0.96))
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"FIG6_DOE_new_reference_fixed_h.{ext}", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_fixed_d()
    fig_fixed_h()
    print("wrote FIG5/FIG6")
