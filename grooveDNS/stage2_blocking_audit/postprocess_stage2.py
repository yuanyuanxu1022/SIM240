#!/usr/bin/env python3
"""Post-process the independent stage-2 transverse-blocking audit."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
RUN_ID = "stage2_bxx_formal_20260906"
RUN_DIR = ROOT / "runs" / RUN_ID
DATA_FILE = RUN_DIR / "blocking_diagnostic.csv"
LAST_N = 5000
QX_TOLERANCE = 1.0e-13


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def slope(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.polyfit(x, y, 1)[0])


def load() -> np.ndarray:
    data = np.genfromtxt(DATA_FILE, delimiter=",", names=True, dtype=float)
    if len(data) != 20000 or not np.array_equal(data["step"], np.arange(20000)):
        raise RuntimeError("formal CSV is not a contiguous 20000-step record")
    if int(np.sum(data["nonfinite_count"])) != 0 or not np.all(data["all_finite"] == 1):
        raise RuntimeError("formal CSV contains non-finite diagnostics")
    return data


def read_key_values(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def verify_short_test() -> dict[str, float]:
    on = np.genfromtxt(ROOT / "runs/short_audit_on/blocking_diagnostic.csv", delimiter=",", names=True)
    off = np.genfromtxt(ROOT / "runs/short_audit_off/blocking_diagnostic.csv", delimiter=",", names=True)
    common = (
        "time_s", "fluid_nodes", "fluid_volume_m3", "volume_mean_ux_m_s", "max_abs_ux_m_s",
        "Qx_legacy_m3_s", "qx_legacy_m_s", "Bxx_numerical_residual_m2",
        "Qx_plane_groove1_m3_s", "Qx_plane_groove2_m3_s", "nonfinite_count", "all_finite",
    )
    differences = {name: float(np.max(np.abs(on[name] - off[name]))) for name in common}
    if len(on) != 200 or len(off) != 200 or any(value != 0 for value in differences.values()):
        raise RuntimeError("short-test audit-on/off equivalence failed")
    return differences


def metrics(data: np.ndarray) -> dict[str, float | int | bool | str]:
    window = data[-LAST_N:]
    x = window["step"]
    result: dict[str, float | int | bool | str] = {
        "run_id": RUN_ID,
        "completed_steps": len(data),
        "final_step": int(data["step"][-1]),
        "final_time_s": float(data["time_s"][-1]),
        "fluid_nodes": int(data["fluid_nodes"][-1]),
        "fluid_volume_m3": float(data["fluid_volume_m3"][-1]),
        "max_fluid_mass_abs_relative_drift_all_steps": float(np.max(data["fluid_mass_abs_rel"])),
        "max_density_deviation_all_steps": float(np.max(data["max_density_deviation"])),
        "nonfinite_count_all_steps": int(np.sum(data["nonfinite_count"])),
        "last_window_start_step": int(window["step"][0]),
        "last_window_end_step": int(window["step"][-1]),
        "max_abs_ux_min_last5000_m_s": float(np.min(window["max_abs_ux_m_s"])),
        "max_abs_ux_max_last5000_m_s": float(np.max(window["max_abs_ux_m_s"])),
        "max_abs_ux_slope_last5000_m_s_per_step": slope(x, window["max_abs_ux_m_s"]),
        "volume_mean_ux_min_last5000_m_s": float(np.min(window["volume_mean_ux_m_s"])),
        "volume_mean_ux_max_last5000_m_s": float(np.max(window["volume_mean_ux_m_s"])),
        "qx_legacy_min_last5000_m_s": float(np.min(window["qx_legacy_m_s"])),
        "qx_legacy_max_last5000_m_s": float(np.max(window["qx_legacy_m_s"])),
        "qx_legacy_slope_last5000_m_s_per_step": slope(x, window["qx_legacy_m_s"]),
        "Bxx_residual_min_last5000_m2": float(np.min(window["Bxx_numerical_residual_m2"])),
        "Bxx_residual_max_last5000_m2": float(np.max(window["Bxx_numerical_residual_m2"])),
        "Bxx_residual_slope_last5000_m2_per_step": slope(x, window["Bxx_numerical_residual_m2"]),
        "plane1_flux_min_last5000_m3_s": float(np.min(window["Qx_plane_groove1_m3_s"])),
        "plane1_flux_max_last5000_m3_s": float(np.max(window["Qx_plane_groove1_m3_s"])),
        "plane2_flux_min_last5000_m3_s": float(np.min(window["Qx_plane_groove2_m3_s"])),
        "plane2_flux_max_last5000_m3_s": float(np.max(window["Qx_plane_groove2_m3_s"])),
        "fluid_mass_abs_drift_min_last5000": float(np.min(window["fluid_mass_abs_rel"])),
        "fluid_mass_abs_drift_max_last5000": float(np.max(window["fluid_mass_abs_rel"])),
        "qx_threshold_m_s": QX_TOLERANCE,
        "qx_threshold_pass_every_step_last5000": bool(np.all(np.abs(window["qx_legacy_m_s"]) < QX_TOLERANCE)),
        "final_volume_mean_ux_m_s": float(data["volume_mean_ux_m_s"][-1]),
        "final_max_abs_ux_m_s": float(data["max_abs_ux_m_s"][-1]),
        "final_Qx_legacy_m3_s": float(data["Qx_legacy_m3_s"][-1]),
        "final_qx_legacy_m_s": float(data["qx_legacy_m_s"][-1]),
        "final_Bxx_numerical_residual_m2": float(data["Bxx_numerical_residual_m2"][-1]),
        "final_Qx_plane_groove1_m3_s": float(data["Qx_plane_groove1_m3_s"][-1]),
        "final_Qx_plane_groove2_m3_s": float(data["Qx_plane_groove2_m3_s"][-1]),
    }
    return result


def write_csv(result: dict, run_summary: dict[str, str]) -> None:
    extra = {
        "source_version": "5953d8a-dirty",
        "source_cpp_sha256": sha256(ROOT / "stage2BlockingAudit.cpp"),
        "executable_sha256": sha256(ROOT / "stage2BlockingAudit"),
        "original_case_h_sha256": sha256(ROOT.parent / "case.h"),
        "diagnostic_csv_sha256": sha256(DATA_FILE),
        "dx_nm": 5.0,
        "dt_s": 4.166666666666666e-12,
        "tau": 1.0,
        "body_accel_x_m_s2": float(run_summary["body_accel_x_m_s2"]),
        "body_accel_y_applied_m_s2": float(run_summary["body_accel_y_applied_m_s2"]),
        "body_accel_z_applied_m_s2": float(run_summary["body_accel_z_applied_m_s2"]),
        "lattice_force_x": float(run_summary["lattice_force_x"]),
        "lattice_force_y": float(run_summary["lattice_force_y"]),
        "lattice_force_z": float(run_summary["lattice_force_z"]),
        "density_kg_m3": 1000.0,
        "kinematic_viscosity_m2_s": 1.0e-6,
        "wall_width_nm": 120.0,
        "groove_width_nm": 120.0,
        "num_grooves": 2,
        "domain_Lx_nm": 600.0,
        "domain_Ly_nm": 240.0,
        "channel_height_nm": 65.0,
        "exit_code": int((RUN_DIR / "exit_code.txt").read_text().strip()),
        "end_reason": (RUN_DIR / "end_reason.txt").read_text().strip(),
        "short_test_read_only_equivalence": True,
    }
    row = {**extra, **result}
    with (ROOT / "stage2_blocking_summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=row.keys())
        writer.writeheader()
        writer.writerow(row)


def plots(data: np.ndarray) -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9, "axes.labelsize": 10,
        "axes.titlesize": 11, "legend.fontsize": 8.5, "figure.dpi": 160,
        "savefig.dpi": 320, "axes.spines.top": False, "axes.spines.right": False,
    })
    t_ns = data["time_s"] * 1e9
    fig, axes = plt.subplots(2, 1, figsize=(6.4, 6.0), sharex=True)
    axes[0].plot(t_ns, data["max_abs_ux_m_s"], color="#0072B2", lw=1.0, label=r"max $|u_x|$")
    axes[0].axhline(QX_TOLERANCE, color="#D55E00", ls="--", lw=0.9, label=r"original $|q_x|$ threshold")
    axes[0].set_yscale("log")
    axes[0].set_ylabel(r"Local velocity residual (m s$^{-1}$)")
    axes[0].legend(frameon=False)
    axes[0].set_title("Transverse velocity and flux residuals")
    axes[1].plot(t_ns, data["volume_mean_ux_m_s"], color="#009E73", lw=0.9, label=r"volume mean $u_x$")
    axes[1].plot(t_ns, data["qx_legacy_m_s"], color="#E69F00", lw=0.9, label=r"legacy $q_x$")
    axes[1].set_yscale("symlog", linthresh=1e-14)
    axes[1].set_ylabel(r"Signed diagnostic (m s$^{-1}$)")
    axes[1].set_xlabel("Physical time (ns)")
    axes[1].legend(frameon=False)
    for ax in axes: ax.grid(alpha=0.25)
    fig.savefig(ROOT / "stage2_velocity_residual.png", bbox_inches="tight")
    fig.savefig(ROOT / "stage2_velocity_residual.pdf", bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(6.4, 6.0), sharex=True)
    axes[0].plot(t_ns, data["fluid_mass_signed_rel"], color="#0072B2", lw=0.9)
    axes[0].axhline(0, color="black", lw=0.6)
    axes[0].set_ylabel("Fluid-mass relative drift")
    axes[0].set_title("Fluid-mass and density diagnostics")
    axes[0].ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    axes[1].plot(t_ns, data["max_density_deviation"], color="#CC79A7", lw=0.9)
    axes[1].set_ylabel("Maximum density deviation")
    axes[1].set_xlabel("Physical time (ns)")
    axes[1].ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    for ax in axes: ax.grid(alpha=0.25)
    fig.savefig(ROOT / "stage2_fluid_mass_drift.png", bbox_inches="tight")
    fig.savefig(ROOT / "stage2_fluid_mass_drift.pdf", bbox_inches="tight")
    plt.close(fig)


def write_report(m: dict, run_summary: dict[str, str]) -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT.parent, text=True).strip()
    report = f"""# 阶段二 Bxx 横向阻断补充验证报告

## 结论

独立正式运行 `{RUN_ID}` 已按原工况完成 20000 步，保存退出码 `0`，结束原因为 `fixed_step_limit_completed`。最后5000步中原定义 `|qx|` 每一步都低于原阈值 `1e-13 m/s`，局部 `max|ux|`、两个 x 法向离散截面通量以及非有限值检查均未显示持续横向输运。结论仅限于当前全充液、连续实体墙隔断的理想直槽模型：横向输运在指定数值容差内被阻断。

## 独立实现与来源

程序位于 `stage2_blocking_audit/stage2BlockingAudit.cpp`，只读调用原 `case.h` 的参数、建模、格点初始化函数，并在独立时间循环中统计。运行日志报告版本 `5953d8a-dirty`；仓库 HEAD 为 `{head}`。独立源文件 SHA-256 为 `{sha256(ROOT/'stage2BlockingAudit.cpp')}`，可执行文件 SHA-256 为 `{sha256(ROOT/'stage2BlockingAudit')}`，所读取原 `case.h` SHA-256 为 `{sha256(ROOT.parent/'case.h')}`。

首次编译因辅助函数名与系统函数冲突而失败；修复仅为局部改名，详见 `failure_records.md`，没有改变物理模型。后续编译成功。

## 工况、几何与体力核对

- 网格：`dx=5 nm`，`dt=4.1666666667e-12 s`，`tau=1`，单 MPI rank。
- 几何：x 向 `wall | groove | wall | groove | wall`，每段120 nm，总宽600 nm；y 长240 nm且周期；z 高65 nm；x/z实体无滑移反弹。
- 流体：`rho=1000 kg/m³`，`nu=1e-6 m²/s`。
- 驱动：仅施加 `a_x=1e6 m/s²`。程序逐个读取 material=1/core 格点的实际 FORCE 字段，得到 lattice force `(3.4722222222e-9, 0, 0)`；y/z 分量严格为零。参数表中保留的默认 `BODY_FORCE_ACCEL=1e8` 没有在 `CHECK_BXX=1` 分支中施加。
- 长度与验收：固定20000步，不使用 ValueTracer，不改变原 `|qx|<1e-13 m/s` 阈值。

## 统计定义

质量统计只遍历各 block 的 core spatial locations 且仅接受 `material=1`，排除实体与 overlap。离散流体共有 `{m['fluid_nodes']:,}` 个节点，体积 `{m['fluid_volume_m3']:.10e} m³`。质量为 `sum(rho_lattice × rho_phys × dx³)`；最大密度偏差是局部可压缩性诊断，不能称为质量守恒误差。

y 周期格点同时存储 `y=0` 和 `y=Ly`。旧体积积分定义本来包含这两个存储端点，并以 `Ly+dx` 归一化，因此复现旧 `Qx` 时没有盲目去重。另算 x 法向平面通量时，`y=Ly` 是 `y=0` 的周期像，物理截面只计一次，故仅对此平面积分排除已知的 `y=Ly` 像。

## Qx 定义审查

旧定义为 `Qx_legacy = integral(u_x dV)/(Ly+dx)`，随后 `qx_legacy=Qx_legacy/(600 nm×65 nm)`，`Bxx_num=mu*qx_legacy/(rho*a_x)`。因为体积分除以 y 长度不会自动构成 x 法向截面积分，`Qx_legacy` 是为复现原结果保留的归一化诊断量，不应称为真实 x 截面穿流量。`Bxx_num` 只是数值残差，不能取倒数解释为宏观横向阻力。

本报告另外给出：流体节点体积平均 `ux`、局部 `max|ux|`，以及两条槽中心 x 平面的离散法向通量。后两者用于避免把正负速度相互抵消后的平均值作为唯一阻断证据。

## 短测试和统计只读性

启用与关闭质量审计的两次200步独立短测均以退出码0完成。两次运行的时间、节点数、体积平均速度、局部最大速度、旧 Qx/qx/Bxx、两平面通量和非有限检查共12列逐步完全一致，最大绝对差为0。因此接入的质量统计未改变流场演化。

## 正式结果

- 最终 step/time：`19999` / `{m['final_time_s']:.10e} s`。
- 最终体积平均 `ux`：`{m['final_volume_mean_ux_m_s']:.10e} m/s`。
- 最终 `max|ux|`：`{m['final_max_abs_ux_m_s']:.10e} m/s`。
- 最终旧 `Qx`：`{m['final_Qx_legacy_m3_s']:.10e} m³/s`。
- 最终旧 `qx`：`{m['final_qx_legacy_m_s']:.10e} m/s`。
- 最终 `Bxx` 数值残差：`{m['final_Bxx_numerical_residual_m2']:.10e} m²`。
- 最终两槽中心离散平面通量：`{m['final_Qx_plane_groove1_m3_s']:.10e}`、`{m['final_Qx_plane_groove2_m3_s']:.10e} m³/s`。
- 全过程流体质量最大绝对相对漂移：`{m['max_fluid_mass_abs_relative_drift_all_steps']:.10e}`。
- 全过程最大密度偏差：`{m['max_density_deviation_all_steps']:.10e}`。
- 所有输出的非有限值总数：`{m['nonfinite_count_all_steps']}`。

## 最后5000步审查

分析窗口为 step `{m['last_window_start_step']}–{m['last_window_end_step']}`：

- `max|ux|` 范围 `{m['max_abs_ux_min_last5000_m_s']:.10e}–{m['max_abs_ux_max_last5000_m_s']:.10e} m/s`，线性斜率 `{m['max_abs_ux_slope_last5000_m_s_per_step']:.3e} m/s/step`。最大值略高于 `1e-13 m/s`，但该阈值原本定义给 `qx`，不能移用于局部最大速度；其量级和斜率表明处于浮点残差平台。
- 旧 `qx` 范围 `{m['qx_legacy_min_last5000_m_s']:.10e}–{m['qx_legacy_max_last5000_m_s']:.10e} m/s`，斜率 `{m['qx_legacy_slope_last5000_m_s_per_step']:.3e} m/s/step`；全部5000步持续满足原阈值。
- `Bxx_num` 范围 `{m['Bxx_residual_min_last5000_m2']:.10e}–{m['Bxx_residual_max_last5000_m2']:.10e} m²`，斜率 `{m['Bxx_residual_slope_last5000_m2_per_step']:.3e} m²/step`。
- 两槽中心平面通量范围分别为 `{m['plane1_flux_min_last5000_m3_s']:.10e}–{m['plane1_flux_max_last5000_m3_s']:.10e}` 和 `{m['plane2_flux_min_last5000_m3_s']:.10e}–{m['plane2_flux_max_last5000_m3_s']:.10e} m³/s`，两槽结果一致且处于数值残差量级。
- 流体质量绝对相对漂移在最后5000步恒为 `{m['fluid_mass_abs_drift_max_last5000']:.10e}`。全过程峰值略高，为 `{m['max_fluid_mass_abs_relative_drift_all_steps']:.10e}`。

这里没有使用近零均值的标准差比作为停止或验收判据，也没有因平均速度抵消而单独宣布阻断。

## 图件

- `stage2_velocity_residual.png/.pdf`：完整20000步的局部最大速度、体积平均速度和旧 qx 残差；包含初始瞬态。
- `stage2_fluid_mass_drift.png/.pdf`：完整流体质量相对漂移与最大密度偏差；两者分面显示，避免混同。

## 结论范围和剩余限制

当前验证对象是全充液、单相、连续实体墙隔断、y周期且x/z无滑移的理想直槽模型。在该模型与原5 nm网格、原体力及原数值阈值下，横向输运被阻断。不能据此宣称所有 EX240 压印间隙下 `Bxx` 均为零，也不能推广到液滴、接触线、动态压印或几何缺口。

剩余限制包括：只有单一5 nm网格；平面通量采用格点求和而非高阶曲面积分；局部残差受双精度与离散边界影响；没有实验或完整 EX240 几何验证；本次没有进行网格扫描或阶段三计算。
"""
    (ROOT / "stage2_blocking_validation_report.md").write_text(report, encoding="utf-8")


def main() -> None:
    data = load()
    verify_short_test()
    result = metrics(data)
    summary = read_key_values(RUN_DIR / "run_summary.txt")
    if (RUN_DIR / "exit_code.txt").read_text().strip() != "0":
        raise RuntimeError("formal process exit code is not zero")
    if summary.get("force_audit_pass") != "1":
        raise RuntimeError("force audit did not pass")
    write_csv(result, summary)
    plots(data)
    write_report(result, summary)
    print("stage-2 post-processing complete")


if __name__ == "__main__":
    main()
