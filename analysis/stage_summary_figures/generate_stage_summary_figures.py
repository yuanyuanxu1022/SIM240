#!/usr/bin/env python3
"""Generate reproducible figures for the SIM240 three-page stage summary."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[2]
FORCE_CSV = (
    PROJECT
    / "CASE/05_mechanism_analysis/G2_EX240_force_linearity/results"
    / "g2_force_linearity_20260917T120627+0800/g2_force_linearity.csv"
)
TRANSPORT_CSV = PROJECT / "transport_database/G3_height_resistance.csv"
DEFAULT_OUTPUT = PROJECT / "CASE/reports/figures/stage_summary"

BLUE = "#2166AC"
RED = "#B2182B"
GREEN = "#4D9221"
FLUID = "#B9E3F5"
SOLID = "#707070"


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Noto Sans CJK SC", "DejaVu Sans"],
            "font.size": 10,
            "axes.labelsize": 11,
            "axes.titlesize": 11,
            "legend.fontsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.unicode_minus": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def save_figure(fig: plt.Figure, output: Path, stem: str) -> None:
    output.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output / f"{stem}.png", dpi=600, bbox_inches="tight")
    fig.savefig(output / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def validate_transport_data(
    data: pd.DataFrame, viscosity_pa_s: float = 1.0e-3
) -> pd.DataFrame:
    required = {
        "height_nm",
        "K_parallel",
        "K_perp",
        "R_parallel",
        "R_perp",
        "anisotropy",
    }
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"missing transport columns: {sorted(missing)}")
    checked = data.copy().sort_values("height_nm").reset_index(drop=True)
    if not np.isfinite(checked[list(required)].to_numpy(dtype=float)).all():
        raise ValueError("transport data contain non-finite values")
    if (checked[["K_parallel", "K_perp", "R_parallel", "R_perp"]] <= 0).any().any():
        raise ValueError("transport coefficients must be positive")

    expected_parallel = viscosity_pa_s / checked["K_parallel"]
    expected_perp = viscosity_pa_s / checked["K_perp"]
    expected_anisotropy = checked["K_parallel"] / checked["K_perp"]
    for column, expected in (
        ("R_parallel", expected_parallel),
        ("R_perp", expected_perp),
        ("anisotropy", expected_anisotropy),
    ):
        if not np.allclose(checked[column], expected, rtol=2.0e-9, atol=0.0):
            raise ValueError(f"{column} is inconsistent with K and viscosity")
    return checked


def load_transport_data() -> pd.DataFrame:
    checked = validate_transport_data(pd.read_csv(TRANSPORT_CSV))
    expected_heights = np.array([50.0, 75.0, 125.0])
    if not np.array_equal(checked["height_nm"].to_numpy(), expected_heights):
        raise ValueError("expected transport heights 50, 75, and 125 nm")
    return checked


def load_force_data() -> pd.DataFrame:
    data = pd.read_csv(FORCE_CSV)
    required = {"direction", "acceleration", "J", "R2", "direction_gate"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"missing force-linearity columns: {sorted(missing)}")
    data = data[data["direction"].isin(["parallel", "perpendicular"])].copy()
    counts = data.groupby("direction").size().to_dict()
    if counts != {"parallel": 3, "perpendicular": 3}:
        raise ValueError(f"expected three force points per direction, got {counts}")
    if not data["direction_gate"].astype(bool).all():
        raise ValueError("force-linearity input contains a failed direction gate")
    return data


def plot_research_chain(output: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.2, 3.1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    panels = (
        (0.02, "周期沟槽 RVE", "真实 EX240 几何", "#E8EEF5", "#345B7E"),
        (0.27, "OpenLB 单相 LBM", "速度・压力・通量", "#E7F2FA", BLUE),
        (0.52, "面内输运闭合", r"$K_{\parallel},K_{\perp}$  /  $R_{\parallel},R_{\perp}$", "#EDF6E9", GREEN),
        (0.77, r"$z$ 向加载响应", r"$p(s)$  /  $F_z$  /  $C_F$", "#F8ECEE", RED),
    )
    panel_width = 0.205
    panel_y, panel_height = 0.36, 0.42
    for x, title, subtitle, face, edge in panels:
        ax.add_patch(
            FancyBboxPatch(
                (x, panel_y),
                panel_width,
                panel_height,
                boxstyle="round,pad=0.012,rounding_size=0.018",
                facecolor=face,
                edgecolor=edge,
                linewidth=1.5,
            )
        )
        ax.text(x + panel_width / 2, 0.66, title, ha="center", va="center", weight="bold", color=edge)
        ax.text(x + panel_width / 2, 0.51, subtitle, ha="center", va="center", color="#24313C")

    for x in (0.235, 0.485, 0.735):
        ax.annotate("", xy=(x + 0.027, 0.57), xytext=(x, 0.57), arrowprops=dict(arrowstyle="-|>", lw=1.8, color="#52606D"))

    # A small groove symbol grounds the workflow in the actual periodic geometry.
    ax.plot([0.055, 0.085, 0.085, 0.16, 0.16, 0.19], [0.405, 0.405, 0.465, 0.465, 0.405, 0.405], color="#345B7E", lw=2)
    ax.annotate("", xy=(0.18, 0.385), xytext=(0.065, 0.385), arrowprops=dict(arrowstyle="->", color=RED, lw=1.4))
    ax.text(0.122, 0.325, r"$x/y$ 面内输运", ha="center", color=RED, fontsize=9)

    ax.add_patch(
        FancyBboxPatch(
            (0.12, 0.08),
            0.76,
            0.14,
            boxstyle="round,pad=0.012,rounding_size=0.015",
            facecolor="#F4F6F8",
            edgecolor="#AAB4BE",
            linewidth=1.0,
        )
    )
    ax.text(
        0.5,
        0.15,
        r"物理含义：$z$ 向压头加载引起液体沿 $x/y$ 面内排出，并非液体沿 $z$ 方向贯穿固壁",
        ha="center",
        va="center",
        color="#263238",
        weight="bold",
    )
    ax.set_title("SIM240 当前阶段研究链条", pad=10, weight="bold")
    save_figure(fig, output, "Figure_1_research_chain")


def plot_geometry(output: Path) -> None:
    h_nm, depth_nm, period_nm = 75.0, 100.0, 240.0
    groove_left, groove_width = 60.0, 120.0
    fig, ax = plt.subplots(figsize=(9.2, 4.2))

    # Geometry is kept separate from the direction legend so dimensions remain readable.
    ax.add_patch(Rectangle((0, 0), period_nm, h_nm, color=FLUID, ec="none"))
    ax.add_patch(
        Rectangle((groove_left, h_nm), groove_width, depth_nm, color=FLUID, ec="none")
    )
    ax.add_patch(Rectangle((0, h_nm), groove_left, 110, color=SOLID, alpha=0.9))
    ax.add_patch(
        Rectangle((groove_left + groove_width, h_nm), groove_left, 110, color=SOLID, alpha=0.9)
    )
    ax.add_patch(
        Rectangle((groove_left, h_nm + depth_nm), groove_width, 10, color=SOLID, alpha=0.9)
    )
    ax.plot([0, period_nm], [0, 0], color="black", lw=2)
    ax.plot([0, 0], [0, h_nm + 110], color="0.45", lw=1, ls="--")
    ax.plot([period_nm, period_nm], [0, h_nm + 110], color="0.45", lw=1, ls="--")

    ax.annotate("", xy=(period_nm, -16), xytext=(0, -16), arrowprops=dict(arrowstyle="<->"))
    ax.text(period_nm / 2, -27, r"$P=240$ nm", ha="center", va="top")
    ax.annotate(
        "", xy=(groove_left + groove_width, h_nm + depth_nm - 16),
        xytext=(groove_left, h_nm + depth_nm - 16), arrowprops=dict(arrowstyle="<->")
    )
    ax.text(period_nm / 2, h_nm + depth_nm - 29, r"$W_g=120$ nm", ha="center", va="top")
    ax.annotate("", xy=(-12, h_nm), xytext=(-12, 0), arrowprops=dict(arrowstyle="<->"))
    ax.text(-18, h_nm / 2, r"$h=75$ nm", ha="right", va="center", rotation=90)
    ax.annotate(
        "", xy=(groove_left + groove_width - 10, h_nm + depth_nm),
        xytext=(groove_left + groove_width - 10, h_nm),
        arrowprops=dict(arrowstyle="<->")
    )
    ax.text(groove_left + groove_width - 3, h_nm + depth_nm / 2, r"$D=100$ nm", ha="left", va="center")

    ax.text(120, 33, "单相液体", color="#075985", ha="center", weight="bold")
    ax.text(30, 135, "模具台面", color="white", ha="center")
    ax.text(120, 180, "模具", color="white", ha="center", va="center")

    # Direction key: placed outside the dimensioned section to avoid label collisions.
    ax.text(292, 170, "方向定义", ha="center", weight="bold", color="#263238")
    ax.annotate("", xy=(330, 135), xytext=(270, 135), arrowprops=dict(arrowstyle="->", color=RED, lw=2))
    ax.text(300, 146, r"$+x$ 横槽", color=RED, ha="center")
    ax.text(300, 102, r"$\odot$  $+y$ 沿槽", color=BLUE, ha="center", weight="bold")
    ax.annotate("", xy=(300, 40), xytext=(300, 82), arrowprops=dict(arrowstyle="-|>", color="black", lw=2))
    ax.text(310, 60, r"$-z$ 加载", ha="left", va="center")

    ax.text(0, 198, "周期边界", color="0.35", ha="center", fontsize=9)
    ax.text(period_nm, 198, "周期边界", color="0.35", ha="center", fontsize=9)
    ax.set(xlim=(-38, 355), ylim=(-38, 210))
    ax.axis("off")
    ax.set_title("EX240 周期沟槽截面（尺寸与方向分区标注）", pad=8, weight="bold")
    ax.set_aspect("equal", adjustable="box")
    save_figure(fig, output, "Figure_2_EX240_geometry_directions")


def plot_force_linearity(output: Path) -> None:
    data = load_force_data()
    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    for direction, label, color, marker in (
        ("parallel", "沿槽 Parallel", BLUE, "o"),
        ("perpendicular", "横槽 Perpendicular", RED, "s"),
    ):
        subset = data[data["direction"] == direction].sort_values("acceleration")
        x = subset["acceleration"].to_numpy() / 1.0e5
        y = subset["J"].to_numpy() / 1.0e-12
        slope, intercept = np.polyfit(x, y, 1)
        x_fit = np.linspace(0.4, 2.1, 100)
        ax.plot(x_fit, slope * x_fit + intercept, color=color, lw=1.8)
        ax.scatter(x, y, color=color, marker=marker, s=42, zorder=3, label=label)
        r2 = float(subset["R2"].iloc[0])
        ax.text(
            0.98,
            0.32 if direction == "parallel" else 0.18,
            f"{label}: $R^2={r2:.6f}$",
            color=color,
            ha="right",
            transform=ax.transAxes,
        )
    ax.set(
        xlabel=r"体力加速度 $a/(10^5\ \mathrm{m\,s^{-2}})$",
        ylabel=r"深度积分通量 $J/(10^{-12}\ \mathrm{m^2\,s^{-1}})$",
        title="EX240 两个主方向的驱动力—通量线性关系",
    )
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False, loc="upper left")
    save_figure(fig, output, "Figure_3_1_G2_force_flux_linearity")


def plot_height_resistance(output: Path) -> None:
    data = load_transport_data()
    h = data["height_nm"]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8))

    axes[0].plot(h, data["R_parallel"] / 1.0e19, "o-", color=BLUE, lw=1.8, label=r"$R_{\parallel}$")
    axes[0].plot(h, data["R_perp"] / 1.0e19, "s-", color=RED, lw=1.8, label=r"$R_{\perp}$")
    axes[0].set(
        xlabel=r"液层高度 $h$ (nm)",
        ylabel=r"水力阻力 $R/(10^{19}\ \mathrm{Pa\,s\,m^{-3}})$",
        title="(a) 面内水力阻力",
    )
    axes[0].legend(frameon=False)
    axes[0].grid(True, alpha=0.25)

    axes[1].plot(h, data["anisotropy"], "D-", color=GREEN, lw=1.8)
    for x, y in zip(h, data["anisotropy"]):
        axes[1].annotate(f"{y:.3f}", (x, y), xytext=(0, 7), textcoords="offset points", ha="center")
    axes[1].axhline(1.0, color="0.45", lw=1, ls="--")
    axes[1].set(
        xlabel=r"液层高度 $h$ (nm)",
        ylabel=r"方向阻力比 $R_{\perp}/R_{\parallel}$",
        title="(b) 输运各向异性",
    )
    axes[1].grid(True, alpha=0.25)
    fig.suptitle(r"EX240 高度依赖输运结果（固定网格 $\Delta x=2.5$ nm）", y=1.02)
    save_figure(fig, output, "Figure_3_2_height_resistance_anisotropy")


def plot_boundary_and_data_transfer(output: Path) -> None:
    """Show the boundary conditions and one-way G2-to-G5A data transfer."""
    fig, ax = plt.subplots(figsize=(11.2, 4.8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Two model panels: microscopic periodic RVE and mesoscale squeeze closure.
    for x, width, face, edge in (
        (0.025, 0.38, "#F4F8FC", BLUE),
        (0.595, 0.38, "#FCF6F7", RED),
    ):
        ax.add_patch(
            FancyBboxPatch(
                (x, 0.12),
                width,
                0.76,
                boxstyle="round,pad=0.012,rounding_size=0.018",
                facecolor=face,
                edgecolor=edge,
                linewidth=1.5,
            )
        )

    # Left: EX240 periodic cell and the two independent body-force directions.
    ax.text(0.215, 0.82, "OpenLB：周期沟槽 RVE", ha="center", weight="bold", color="#263238")
    ax.add_patch(Rectangle((0.075, 0.26), 0.28, 0.19, facecolor=FLUID, edgecolor="none"))
    ax.add_patch(Rectangle((0.145, 0.45), 0.14, 0.20, facecolor=FLUID, edgecolor="none"))
    ax.add_patch(Rectangle((0.075, 0.45), 0.07, 0.23, facecolor=SOLID, edgecolor="none"))
    ax.add_patch(Rectangle((0.285, 0.45), 0.07, 0.23, facecolor=SOLID, edgecolor="none"))
    ax.add_patch(Rectangle((0.145, 0.65), 0.14, 0.03, facecolor=SOLID, edgecolor="none"))
    ax.plot([0.075, 0.355], [0.26, 0.26], color="black", lw=1.5)
    ax.plot([0.075, 0.075], [0.24, 0.70], color="0.45", ls="--", lw=1.0)
    ax.plot([0.355, 0.355], [0.24, 0.70], color="0.45", ls="--", lw=1.0)
    ax.text(0.075, 0.72, "周期", ha="center", color="0.35", fontsize=9)
    ax.text(0.355, 0.72, "周期", ha="center", color="0.35", fontsize=9)
    ax.text(0.215, 0.29, "单相液体", ha="center", color="#075985", weight="bold", fontsize=9)

    ax.annotate("", xy=(0.335, 0.36), xytext=(0.095, 0.36), arrowprops=dict(arrowstyle="->", color=RED, lw=2.0))
    ax.text(0.215, 0.325, r"$+x$ 横槽：$G_x=\rho a_x$", ha="center", color=RED, fontsize=9)
    ax.text(0.215, 0.54, r"$\odot$  $+y$ 沿槽：$G_y=\rho a_y$", ha="center", color=BLUE, weight="bold", fontsize=9)
    ax.text(0.215, 0.18, r"周期体力驱动 → 提取 $J_i$ 与 $K_i$", ha="center", color="#263238", fontsize=9)

    # Centre: only the transport closure is passed downstream.
    ax.add_patch(
        FancyBboxPatch(
            (0.425, 0.35),
            0.145,
            0.28,
            boxstyle="round,pad=0.012,rounding_size=0.015",
            facecolor="#EDF6E9",
            edgecolor=GREEN,
            linewidth=1.5,
        )
    )
    ax.text(0.4975, 0.575, "数据传递", ha="center", weight="bold", color=GREEN)
    ax.text(0.4975, 0.495, r"$K_{\parallel},\ K_{\perp}$", ha="center", fontsize=12)
    ax.text(0.4975, 0.425, r"$R_i=\mu/K_i$", ha="center", fontsize=10)
    ax.annotate("", xy=(0.592, 0.49), xytext=(0.572, 0.49), arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=2.0))
    ax.annotate("", xy=(0.423, 0.49), xytext=(0.407, 0.49), arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=2.0))

    # Right: quasi-static squeeze model with prescribed vertical speed and open ends.
    ax.text(0.785, 0.82, r"G5A：$z$ 向恒速加载", ha="center", weight="bold", color="#263238")
    ax.add_patch(Rectangle((0.645, 0.29), 0.28, 0.17, facecolor=FLUID, edgecolor="#5AA6C8", linewidth=0.8))
    ax.add_patch(Rectangle((0.645, 0.55), 0.28, 0.07, facecolor=SOLID, edgecolor="none"))
    ax.plot([0.645, 0.925], [0.29, 0.29], color="black", lw=1.5)
    ax.annotate("", xy=(0.785, 0.635), xytext=(0.785, 0.75), arrowprops=dict(arrowstyle="-|>", color="black", lw=2.0))
    ax.text(0.802, 0.69, r"$V_p$，$-z$", ha="left", va="center", fontsize=9)
    ax.text(0.632, 0.375, r"$p=0$", ha="right", va="center", color="0.25", fontsize=9)
    ax.text(0.938, 0.375, r"$p=0$", ha="left", va="center", color="0.25", fontsize=9)
    ax.annotate("", xy=(0.647, 0.405), xytext=(0.785, 0.405), arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.8))
    ax.annotate("", xy=(0.923, 0.405), xytext=(0.785, 0.405), arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.8))
    ax.annotate("", xy=(0.647, 0.345), xytext=(0.785, 0.345), arrowprops=dict(arrowstyle="->", color=RED, lw=1.8))
    ax.annotate("", xy=(0.923, 0.345), xytext=(0.785, 0.345), arrowprops=dict(arrowstyle="->", color=RED, lw=1.8))
    ax.text(0.785, 0.475, r"两端零表压；分别沿 $parallel/\perp$ 排液", ha="center", fontsize=9, color="#263238")
    ax.text(0.785, 0.22, r"输出：$p(s)$、$F_z$、$C_F=F_z/V_p$", ha="center", fontsize=10, weight="bold")

    ax.add_patch(
        FancyBboxPatch(
            (0.245, 0.015),
            0.51,
            0.065,
            boxstyle="round,pad=0.008,rounding_size=0.012",
            facecolor="#F4F6F8",
            edgecolor="#AAB4BE",
            linewidth=1.0,
        )
    )
    ax.text(
        0.5,
        0.047,
        "模型边界：单相、全充液、准静态固定网格闭合；不是移动边界 OpenLB 或两相填充",
        ha="center",
        va="center",
        fontsize=9,
        color="#263238",
    )
    ax.set_title("微尺度输运参数向准静态挤压模型的数据传递", pad=10, weight="bold")
    save_figure(fig, output, "Figure_3_boundary_and_data_transfer")


def generate_all(output: Path) -> None:
    configure_style()
    plot_research_chain(output)
    plot_geometry(output)
    plot_force_linearity(output)
    plot_height_resistance(output)
    plot_boundary_and_data_transfer(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    generate_all(args.output)
    print(f"generated=5 output={args.output}")


if __name__ == "__main__":
    main()
