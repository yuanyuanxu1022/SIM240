#!/usr/bin/env python3
"""Reproduce the stage-1 validation archive from the three converged CSV files."""

from __future__ import annotations

import csv
import hashlib
import math
import re
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ARCHIVE_DIR = Path(__file__).resolve().parent
BASE_DIR = ARCHIVE_DIR.parent
FIGURE_DIR = ARCHIVE_DIR / "figures"
EPSILON = 1.0e-6
CHECK_INTERVAL_S = 1.2e-8
SAFETY_FACTOR = 1.25

RUNS = (
    {
        "label": "dx = 5 nm",
        "run_id": "dx5_formal_20260905",
        "log": "formal_run.log",
        "resolution": 48,
    },
    {
        "label": "dx = 2.5 nm",
        "run_id": "dx2p5_persistent_20260905",
        "log": "dx2p5_persistent.log",
        "resolution": 96,
    },
    {
        "label": "dx = 1.25 nm",
        "run_id": "dx1p25_persistent_20260905",
        "log": "dx1p25_persistent.log",
        "resolution": 192,
    },
)

COLORS = ("#0072B2", "#E69F00", "#009E73")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> dict[str, np.ndarray]:
    data = np.genfromtxt(path, delimiter=",", names=True, dtype=float)
    return {name: np.atleast_1d(data[name]) for name in data.dtype.names}


def parse_log(path: Path) -> tuple[dict[str, float], str, bool]:
    text = path.read_text(encoding="utf-8", errors="replace")
    params: dict[str, float] = {}
    wanted = (
        "PHYS_DELTA_X",
        "LATTICE_RELAXATION_TIME",
        "WALL_WIDTH",
        "PHYS_CHAR_DENSITY",
        "GROOVE_WIDTH",
        "CHANNEL_HEIGHT",
        "DOMAIN_LY",
        "PHYS_CHAR_VISCOSITY",
        "BODY_FORCE_ACCEL",
        "NUM_GROOVES",
        "RESOLUTION",
        "INTERVAL_CONVERGENCE_CHECK",
        "CONVERGENCE_PRECISION",
        "MAX_PHYS_T",
    )
    for key in wanted:
        match = re.search(rf"^\[Case\]\s+{key}\s+=\s+([^\s]+)", text, re.MULTILINE)
        if not match:
            raise RuntimeError(f"Missing {key} in {path}")
        params[key] = float(match.group(1))
    version_match = re.search(r"^\[initialize\]\s+Version\s+:\s+(\S+)", text, re.MULTILINE)
    if not version_match:
        raise RuntimeError(f"Missing source version in {path}")
    completion = "integrated diagnostic written to" in text
    return params, version_match.group(1), completion


def sample_ratio(values: np.ndarray) -> float:
    average = float(np.mean(values))
    stddev = float(np.std(values, ddof=1))
    return abs(stddev / average)


def relative_difference(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    denom = np.maximum(np.abs(a), np.abs(b))
    out = np.zeros_like(denom)
    np.divide(np.abs(a - b), denom, out=out, where=denom > 0)
    return out


def load_runs() -> list[dict]:
    loaded = []
    for spec in RUNS:
        csv_path = BASE_DIR / "output" / spec["run_id"] / "mass_flux_diagnostic.csv"
        log_path = BASE_DIR / spec["log"]
        data = read_csv(csv_path)
        params, version, completion = parse_log(log_path)
        if int(params["RESOLUTION"]) != spec["resolution"]:
            raise RuntimeError(f"Resolution mismatch for {spec['run_id']}")
        steps = data["step"].astype(np.int64)
        if not np.array_equal(steps, np.arange(steps.size)):
            raise RuntimeError(f"Non-contiguous steps in {csv_path}")
        dt = float(data["time_s"][-1] / steps[-1])
        window = int(CHECK_INTERVAL_S / dt + 0.5)
        if data["Qy_volume_m3_s"].size < window:
            raise RuntimeError(f"Incomplete tracer window for {spec['run_id']}")
        final_ratio = sample_ratio(data["Qy_volume_m3_s"][-window:])
        previous_ratio = sample_ratio(data["Qy_volume_m3_s"][-window - 1 : -1])
        if not (final_ratio < EPSILON and previous_ratio >= EPSILON):
            raise RuntimeError(f"Final-step tracer reproduction failed for {spec['run_id']}")
        q_section_mean = 0.5 * (data["Qy_sec1_m3_s"] + data["Qy_sec2_m3_s"])
        section_volume_rel = relative_difference(q_section_mean, data["Qy_volume_m3_s"])
        loaded.append(
            {
                **spec,
                "csv_path": csv_path,
                "log_path": log_path,
                "csv_sha256": sha256(csv_path),
                "log_sha256": sha256(log_path),
                "params": params,
                "version": version,
                "completion_line": completion,
                "data": data,
                "dt_s": dt,
                "window_steps": window,
                "tracer_ratio": final_ratio,
                "previous_tracer_ratio": previous_ratio,
                "section_volume_rel": section_volume_rel,
                "max_section_volume_rel": float(np.max(section_volume_rel)),
                "max_mass_abs_rel": float(np.max(data["fluid_mass_abs_rel"])),
                "max_density_deviation": float(np.max(data["max_density_deviation"])),
                "max_section_rel": float(np.max(data["Qy_section_rel_diff"])),
                "exit_evidence": "tracer pass + final write; exit code not saved",
            }
        )
    return loaded


def richardson(runs: list[dict]) -> dict[str, float]:
    coarse, medium, fine = (float(run["data"]["Byy_nm2"][-1]) for run in runs)
    ratio = 2.0
    p = math.log((coarse - medium) / (medium - fine)) / math.log(ratio)
    extrapolated = fine + (fine - medium) / (ratio**p - 1.0)
    gci_fine = SAFETY_FACTOR * abs((fine - medium) / fine) / (ratio**p - 1.0)
    gci_medium = SAFETY_FACTOR * abs((medium - coarse) / medium) / (ratio**p - 1.0)
    asymptotic_ratio = gci_medium / (ratio**p * gci_fine)
    return {
        "r": ratio,
        "p": p,
        "extrapolated_nm2": extrapolated,
        "gci_fine": gci_fine,
        "gci_medium": gci_medium,
        "asymptotic_ratio": asymptotic_ratio,
    }


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=BASE_DIR, text=True
    ).strip()


def write_summary_csv(runs: list[dict]) -> None:
    columns = (
        "grid_order_coarse_to_fine",
        "run_id",
        "source_version",
        "executable_sha256",
        "source_cpp_sha256",
        "audit_case_h_sha256",
        "dx_nm",
        "dt_s",
        "tau",
        "body_force_accel_m_s2",
        "density_kg_m3",
        "kinematic_viscosity_m2_s",
        "wall_width_nm",
        "groove_width_nm",
        "num_grooves",
        "domain_Lx_nm",
        "domain_Ly_nm",
        "channel_height_nm",
        "fluid_nodes",
        "discrete_fluid_volume_m3",
        "converged_step",
        "physical_time_s",
        "tracer_window_steps",
        "tracer_epsilon",
        "tracer_final_stddev_over_mean",
        "tracer_previous_stddev_over_mean",
        "tracer_pass",
        "Byy_nm2",
        "max_fluid_mass_abs_relative_drift",
        "max_fluid_density_deviation",
        "max_two_section_flux_relative_difference",
        "max_section_mean_vs_volume_flux_relative_difference",
        "final_Qy_section_1_m3_s",
        "final_Qy_section_2_m3_s",
        "final_Qy_volume_m3_s",
        "completion_line_present",
        "exit_code_saved",
        "exit_evidence",
        "source_csv",
        "source_csv_sha256",
        "source_log",
        "source_log_sha256",
    )
    exe_hash = sha256(BASE_DIR / "dx5Integrated")
    cpp_hash = sha256(BASE_DIR / "dx5Integrated.cpp")
    case_hash = sha256(BASE_DIR / "auditCase.h")
    with (ARCHIVE_DIR / "stage1_grid_summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for order, run in enumerate(runs, 1):
            p, d = run["params"], run["data"]
            writer.writerow(
                {
                    "grid_order_coarse_to_fine": order,
                    "run_id": run["run_id"],
                    "source_version": run["version"],
                    "executable_sha256": exe_hash,
                    "source_cpp_sha256": cpp_hash,
                    "audit_case_h_sha256": case_hash,
                    "dx_nm": p["PHYS_DELTA_X"] * 1e9,
                    "dt_s": format(run["dt_s"], ".16g"),
                    "tau": p["LATTICE_RELAXATION_TIME"],
                    "body_force_accel_m_s2": p["BODY_FORCE_ACCEL"],
                    "density_kg_m3": p["PHYS_CHAR_DENSITY"],
                    "kinematic_viscosity_m2_s": p["PHYS_CHAR_VISCOSITY"],
                    "wall_width_nm": p["WALL_WIDTH"] * 1e9,
                    "groove_width_nm": p["GROOVE_WIDTH"] * 1e9,
                    "num_grooves": int(p["NUM_GROOVES"]),
                    "domain_Lx_nm": ((p["NUM_GROOVES"] + 1) * p["WALL_WIDTH"] + p["NUM_GROOVES"] * p["GROOVE_WIDTH"]) * 1e9,
                    "domain_Ly_nm": p["DOMAIN_LY"] * 1e9,
                    "channel_height_nm": p["CHANNEL_HEIGHT"] * 1e9,
                    "fluid_nodes": int(d["fluid_nodes"][-1]),
                    "discrete_fluid_volume_m3": format(float(d["fluid_volume_m3"][-1]), ".16g"),
                    "converged_step": int(d["step"][-1]),
                    "physical_time_s": format(float(d["time_s"][-1]), ".16g"),
                    "tracer_window_steps": run["window_steps"],
                    "tracer_epsilon": EPSILON,
                    "tracer_final_stddev_over_mean": format(run["tracer_ratio"], ".16g"),
                    "tracer_previous_stddev_over_mean": format(run["previous_tracer_ratio"], ".16g"),
                    "tracer_pass": True,
                    "Byy_nm2": format(float(d["Byy_nm2"][-1]), ".16g"),
                    "max_fluid_mass_abs_relative_drift": format(run["max_mass_abs_rel"], ".16g"),
                    "max_fluid_density_deviation": format(run["max_density_deviation"], ".16g"),
                    "max_two_section_flux_relative_difference": format(run["max_section_rel"], ".16g"),
                    "max_section_mean_vs_volume_flux_relative_difference": format(run["max_section_volume_rel"], ".16g"),
                    "final_Qy_section_1_m3_s": format(float(d["Qy_sec1_m3_s"][-1]), ".16g"),
                    "final_Qy_section_2_m3_s": format(float(d["Qy_sec2_m3_s"][-1]), ".16g"),
                    "final_Qy_volume_m3_s": format(float(d["Qy_volume_m3_s"][-1]), ".16g"),
                    "completion_line_present": run["completion_line"],
                    "exit_code_saved": False,
                    "exit_evidence": run["exit_evidence"],
                    "source_csv": str(run["csv_path"].relative_to(BASE_DIR)),
                    "source_csv_sha256": run["csv_sha256"],
                    "source_log": str(run["log_path"].relative_to(BASE_DIR)),
                    "source_log_sha256": run["log_sha256"],
                }
            )


def configure_plot() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.labelsize": 10,
            "axes.titlesize": 11,
            "legend.fontsize": 8.5,
            "figure.dpi": 160,
            "savefig.dpi": 320,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def save_figure(fig: plt.Figure, stem: str) -> None:
    fig.savefig(FIGURE_DIR / f"{stem}.png", bbox_inches="tight")
    fig.savefig(FIGURE_DIR / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def make_figures(runs: list[dict], gci: dict[str, float]) -> None:
    configure_plot()
    FIGURE_DIR.mkdir(exist_ok=True)

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for color, run in zip(COLORS, runs):
        d = run["data"]
        ax.plot(d["time_s"] * 1e9, d["Byy_nm2"], color=color, lw=1.25, label=run["label"])
    ax.set(xlabel="Physical time (ns)", ylabel=r"$B_{yy}$ (nm$^2$)", title=r"Convergence of $B_{yy}$")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    save_figure(fig, "fig1_Byy_time_convergence")

    dx = np.array([run["params"]["PHYS_DELTA_X"] * 1e9 for run in runs])
    byy = np.array([run["data"]["Byy_nm2"][-1] for run in runs])
    curve_x = np.linspace(0.0, dx.max() * 1.08, 300)
    coefficient = (byy[-1] - gci["extrapolated_nm2"]) / dx[-1] ** gci["p"]
    curve_y = gci["extrapolated_nm2"] + coefficient * curve_x ** gci["p"]
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    ax.plot(curve_x, curve_y, color="#555555", lw=1.3, label=rf"Richardson fit ($p={gci['p']:.3f}$)")
    ax.scatter(dx, byy, c=COLORS, s=48, edgecolor="black", linewidth=0.45, zorder=3)
    for x, y, run in zip(dx, byy, runs):
        ax.annotate(run["label"], (x, y), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.scatter([0], [gci["extrapolated_nm2"]], marker="x", color="black", s=48, label="Extrapolated value")
    ax.set(xlabel="Grid spacing dx (nm)", ylabel=r"$B_{yy}$ (nm$^2$)", title="Grid-spacing dependence and Richardson fit")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    save_figure(fig, "fig2_Byy_Richardson")

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for color, run in zip(COLORS, runs):
        d = run["data"]
        ax.plot(d["time_s"] * 1e9, d["fluid_mass_signed_rel"], color=color, lw=1.05, label=run["label"])
    ax.axhline(0.0, color="black", lw=0.65)
    ax.set(xlabel="Physical time (ns)", ylabel="Fluid-mass relative drift", title="Fluid-mass conservation history")
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    save_figure(fig, "fig3_fluid_mass_drift")

    fig, axes = plt.subplots(2, 1, figsize=(6.4, 6.0), sharex=True)
    for color, run in zip(COLORS, runs):
        d = run["data"]
        t_ns = d["time_s"] * 1e9
        axes[0].plot(t_ns, d["Qy_section_rel_diff"], color=color, lw=1.0, label=run["label"])
        axes[1].plot(t_ns, run["section_volume_rel"], color=color, lw=1.0, label=run["label"])
    axes[0].set_ylabel("Two-section relative difference")
    axes[0].set_title("Flux-consistency histories (linear axes; exact zeros retained)")
    axes[1].set_ylabel("Section mean vs volume\nrelative difference")
    axes[1].set_xlabel("Physical time (ns)")
    for ax in axes:
        ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        ax.grid(alpha=0.25)
    axes[0].legend(frameon=False, ncol=3)
    save_figure(fig, "fig4_flux_consistency")


def fmt(value: float, digits: int = 6) -> str:
    return f"{value:.{digits}g}"


def write_report(runs: list[dict], gci: dict[str, float]) -> None:
    exe_hash = sha256(BASE_DIR / "dx5Integrated")
    cpp_hash = sha256(BASE_DIR / "dx5Integrated.cpp")
    case_hash = sha256(BASE_DIR / "auditCase.h")
    rows = []
    for run in runs:
        d = run["data"]
        rows.append(
            "| {run_id} | {dx:g} | {dt:.9e} | {step:d} | {time:.9e} | {ratio:.6e} | {byy:.9f} | {mass:.3e} | {rho:.3e} | {sec:.3e} | {sv:.3e} |".format(
                run_id=run["run_id"], dx=run["params"]["PHYS_DELTA_X"] * 1e9,
                dt=run["dt_s"], step=int(d["step"][-1]), time=float(d["time_s"][-1]),
                ratio=run["tracer_ratio"], byy=float(d["Byy_nm2"][-1]), mass=run["max_mass_abs_rel"],
                rho=run["max_density_deviation"], sec=run["max_section_rel"], sv=run["max_section_volume_rel"]
            )
        )
    volume_rows = "\n".join(
        f"- {run['label']}：{int(run['data']['fluid_nodes'][-1]):,} 个流体节点，离散流体体积 `{run['data']['fluid_volume_m3'][-1]:.10e} m³`。"
        for run in runs
    )
    source_rows = "\n".join(
        f"- `{run['run_id']}`：`{run['log_path'].name}` 与 `output/{run['run_id']}/mass_flux_diagnostic.csv`；CSV SHA-256 `{run['csv_sha256']}`，日志 SHA-256 `{run['log_sha256']}`。"
        for run in runs
    )
    report = f"""# 阶段一三网格质量、通量与离散不确定度归档

## 归档结论

本归档仅使用三组本次实际收敛运行：`dx5_formal_20260905`、`dx2p5_persistent_20260905` 和 `dx1p25_persistent_20260905`。未使用被中断的 `dx2p5_formal_20260905`、`dx2p5_persist_20260905` 或历史参考值。三组完整 CSV 均按实际 OpenLB `ValueTracer` 算法复核通过；所得细网格 GCI 为 `{100*gci['gci_fine']:.4f}%`。

## 数据来源与代码身份

{source_rows}

- 日志报告 OpenLB/源码版本：`{runs[0]['version']}`（三组一致）。
- 仓库 HEAD：`{git_head()}`；运行日志中的 `-dirty` 表明构建时工作树含未提交变化，因此不能只用 HEAD 代表实际二进制。
- `dx5Integrated` SHA-256：`{exe_hash}`。
- `dx5Integrated.cpp` SHA-256：`{cpp_hash}`。
- `auditCase.h` SHA-256：`{case_hash}`。

## 参数、几何和边界条件

三组仅改变分辨率。`dx=5, 2.5, 1.25 nm`，对应 `dt={runs[0]['dt_s']:.15e}, {runs[1]['dt_s']:.15e}, {runs[2]['dt_s']:.15e} s`；`tau=1`，`a_y=1.0e8 m/s²`，`rho=1000 kg/m³`，`nu=1.0e-6 m²/s`。

实际几何为 x 向 `wall | groove | wall | groove | wall`，每段 120 nm，总宽 600 nm；y 向长度 240 nm并采用周期边界；z 向通道高度 65 nm。材料 1 为流体，材料 2 为实体；x 外侧及 z 上下实体采用无滑移反弹边界。当前问题是理想直沟槽条带中的单相稳态流动。`B_yy` 使用完整 `600 nm × 65 nm` 截面的表观速度，而不是仅用两条流体槽面积定义。

## 三网格结果

表中质量漂移只统计材料 1 的流体节点，不包含实体节点密度。截面/体积差异定义为 `|mean(Q_sec1,Q_sec2)-Q_volume| / max(|mean(Q_sec1,Q_sec2)|,|Q_volume|)`。

| run-id | dx (nm) | dt (s) | 收敛step | 物理时间(s) | tracer比值 | B_yy (nm²) | 最大流体质量漂移 | 最大密度偏差 | 最大两截面差异 | 最大截面/体积差异 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

三组 tracer 窗口分别为 `{runs[0]['window_steps']}`、`{runs[1]['window_steps']}` 和 `{runs[2]['window_steps']}` 步。算法保留最近一个完整窗口，计算样本标准差 `s=sqrt(sum((Q_i-Q_bar)^2)/(n-1))`，以 `|s/Q_bar| < 1e-6` 判定。三组最终一步的前一窗口比值分别为 `{runs[0]['previous_tracer_ratio']:.6e}`、`{runs[1]['previous_tracer_ratio']:.6e}` 和 `{runs[2]['previous_tracer_ratio']:.6e}`，均未通过；最终一步均通过，和程序提前结束位置一致。

日志均包含最终 step 及 `integrated diagnostic written`。程序在最大物理时间之前结束，源码中的循环仅在 `tr.hasConverged()` 为真时提前 `break`，故数据满足 tracer 判据且完成文件写出。但是启动方式没有保存 shell/MPI 退出码，不能把“tracer 判据通过”表述为“已保存退出码 0”。

## Richardson 外推与 GCI

按粗到细排序为 `5 -> 2.5 -> 1.25 nm`，细化比 `r=h_coarse/h_fine=2`。结果单调下降。对三网格标量 `phi_3`（粗）、`phi_2`（中）、`phi_1`（细）：

- 观测阶数：`p = ln[(phi_3-phi_2)/(phi_2-phi_1)] / ln(r) = {gci['p']:.9f}`。
- Richardson 外推：`phi_ext = phi_1 + (phi_1-phi_2)/(r^p-1) = {gci['extrapolated_nm2']:.9f} nm²`。
- 采用安全系数 `F_s={SAFETY_FACTOR}`：`GCI_12 = F_s |(phi_1-phi_2)/phi_1|/(r^p-1) = {100*gci['gci_fine']:.4f}%`。
- 中网格 GCI 为 `{100*gci['gci_medium']:.4f}%`。
- 渐近比定义为 `GCI_23/(r^p GCI_12) = {gci['asymptotic_ratio']:.4f}`。其接近 1 表明这组三点与渐近收敛关系相容，但三点证据本身不足以严格证明已进入渐近区。

约 `{100*gci['gci_fine']:.2f}%` 的细网格 GCI 是本数值量的离散不确定度估计，不是实验误差、统计置信区间，也不是严格网格无关证明。

## 离散体积与有效壁面

{volume_rows}

流体节点位于格点，非周期 x/z 边界通过将流体指示区域端点扩展半个格距，使材料分界位于相邻流体/实体格点之间。反弹边界的有效无滑移壁面也位于这类流体/实体节点之间。CSV 中的 `fluid_volume_m3` 按“流体节点数 × dx³”计数，因此会包含节点计数和周期 y 端点表示的离散效应，不等同于连续几何体积；它随 dx 改变并不直接说明几何定义改变。现有 CSV 没有独立的亚格点壁面定位或几何积分验证，因此不能声称各网格有效壁面位置“完全一致”。

## 图件

1. `figures/fig1_Byy_time_convergence.*`：三网格完整物理时间历程，包含初始瞬态。
2. `figures/fig2_Byy_Richardson.*`：三点结果、外推点和 `B_ext + C dx^p` 拟合。
3. `figures/fig3_fluid_mass_drift.*`：材料 1 流体质量有符号相对漂移完整时序。
4. `figures/fig4_flux_consistency.*`：两截面差异及截面均值/体积积分差异完整时序。图采用线性纵轴，CSV 中的精确零保持为零，未替换为人为小正数。

## 论文可用结论

在 600 nm × 65 nm 完整截面表观速度定义下，理想直沟槽条带的 `B_yy` 随网格从 5 nm 细化到 1.25 nm 单调下降至 `{runs[2]['data']['Byy_nm2'][-1]:.9f} nm²`。三组运行均满足原 `ValueTracer` 判据；全过程流体质量漂移、密度偏差及独立通量积分核对未显示守恒异常。三网格 Richardson 分析给出 `p={gci['p']:.3f}`、外推值 `{gci['extrapolated_nm2']:.3f} nm²` 和细网格 GCI `{100*gci['gci_fine']:.2f}%`。该 GCI 应报告为离散不确定度估计。

适用范围仅限 y 周期、x/z 实体无滑移的理想直沟槽单相稳态问题。本结果不代表完整 EX240 几何、液滴填充状态或动态压印过程。

## 老师汇报摘要（约200字）

阶段一已完成 5、2.5 和 1.25 nm 三网格质量与通量验证。三组完整诊断数据均按 OpenLB 原 ValueTracer 样本标准差判据复核通过，最终 B_yy 分别为 `{runs[0]['data']['Byy_nm2'][-1]:.3f}`、`{runs[1]['data']['Byy_nm2'][-1]:.3f}` 和 `{runs[2]['data']['Byy_nm2'][-1]:.3f} nm²`。全过程流体质量最大相对漂移不超过 `{max(run['max_mass_abs_rel'] for run in runs):.2e}`，两截面通量在输出精度内一致。Richardson 外推为 `{gci['extrapolated_nm2']:.3f} nm²`，细网格 GCI 约 `{100*gci['gci_fine']:.2f}%`，表示离散不确定度，不是实验误差或严格网格无关证明。当前结论仅适用于理想直沟槽、y 周期、x/z 无滑移的单相稳态模型，尚不能外推到完整 EX240、液滴填充或动态压印。

## 已完成项与剩余限制

已完成：三组来源隔离与哈希记录、完整 CSV tracer 复核、流体质量/密度/三种通量一致性统计、四组论文候选图、Richardson/GCI 复算和适用范围界定。

剩余限制：未保存三次进程退出码；仅有三个等比网格点；有效壁面位置缺少独立亚格点验证；未覆盖完整 EX240 几何、多相液滴填充、接触线效应或动态压印；本归档不提供实验验证。
"""
    (ARCHIVE_DIR / "stage1_validation_summary.md").write_text(report, encoding="utf-8")


def main() -> None:
    runs = load_runs()
    gci = richardson(runs)
    write_summary_csv(runs)
    make_figures(runs, gci)
    write_report(runs, gci)
    print(f"Archive generated in {ARCHIVE_DIR}")


if __name__ == "__main__":
    main()
