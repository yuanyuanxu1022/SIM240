#!/usr/bin/env python3
"""Offline STEP 6-D analysis of converged STEP 6-C OpenLB VTI fields."""

from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy


HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "right_angle_groove"
FIG = HERE / "figures"
DATA = HERE / "data"
DX = 5e-9
GAPS = (75, 65)
MODES = ("x", "y")
THRESHOLDS = (0.01, 0.05, 0.10)


def run_dir(gap: int, mode: str) -> Path:
    return BASE / "output" / f"sim_ec1xt240_right_angle_h{gap}_dx5_a1e5_{mode}_20260909"


def parse_result(path: Path) -> dict:
    result = {}
    for line in path.read_text().splitlines():
        if "=" not in line:
            continue
        key, raw = line.split("=", 1)
        if "," in raw:
            try:
                result[key] = tuple(float(v) for v in raw.split(","))
            except ValueError:
                result[key] = raw
        elif raw in {"true", "false"}:
            result[key] = raw == "true"
        else:
            try:
                result[key] = float(raw)
            except ValueError:
                result[key] = raw
    return result


def final_vti(run: Path) -> Path:
    result = parse_result(run / "result.txt")
    step = int(result["steps_completed"])
    files = sorted((run / "vtkData" / "data").glob(f"*iT{step:07d}iC*.vti"))
    if len(files) != 1:
        raise RuntimeError(f"Expected one final VTI for {run}, got {files}")
    return files[0]


def read_core(path: Path) -> dict:
    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(str(path))
    reader.Update()
    image = reader.GetOutput()
    extent = image.GetExtent()
    dims = image.GetDimensions()
    arrays = {}
    for name in ("material", "velocity_m_s", "pressure_Pa"):
        raw = vtk_to_numpy(image.GetPointData().GetArray(name))
        shape = (dims[2], dims[1], dims[0]) + (() if raw.ndim == 1 else (raw.shape[1],))
        arrays[name] = raw.reshape(shape)
    x0, y0 = -extent[0], -extent[2]
    z_indices = np.arange(max(0, extent[4]), extent[5] + 1)
    zoff = z_indices - extent[4]
    ys, xs = slice(y0, y0 + 48), slice(x0, x0 + 48)
    return {
        "material": arrays["material"][zoff, ys, xs].astype(np.int16),
        "velocity": arrays["velocity_m_s"][zoff, ys, xs, :].astype(float),
        "pressure": arrays["pressure_Pa"][zoff, ys, xs].astype(float),
        "x": (np.arange(48) + 0.5) * DX,
        "y": (np.arange(48) + 0.5) * DX,
        # The source cuboid starts at z=-dx/2: core iz=0 is the material-2
        # base node at -2.5 nm and core iz=1 is the first fluid node at 2.5 nm.
        "z": (z_indices - 0.5) * DX,
        "vti": path,
    }


def periodic_gradient(field: np.ndarray, fluid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    gx = np.full_like(field, np.nan, dtype=float)
    gy = np.full_like(field, np.nan, dtype=float)
    valid_x = fluid & np.roll(fluid, -1, axis=2) & np.roll(fluid, 1, axis=2)
    valid_y = fluid & np.roll(fluid, -1, axis=1) & np.roll(fluid, 1, axis=1)
    dx_field = (np.roll(field, -1, axis=2) - np.roll(field, 1, axis=2)) / (2 * DX)
    dy_field = (np.roll(field, -1, axis=1) - np.roll(field, 1, axis=1)) / (2 * DX)
    gx[valid_x] = dx_field[valid_x]
    gy[valid_y] = dy_field[valid_y]
    return gx, gy


def describe_case(gap: int, mode: str, data: dict, result: dict) -> tuple[dict, list[dict]]:
    material, velocity, pressure = data["material"], data["velocity"], data["pressure"]
    x, y, z = data["x"], data["y"], data["z"]
    fluid = material == 1
    speed = np.linalg.norm(velocity, axis=3)
    xx, yy = np.meshgrid(x, y, indexing="xy")
    x_strip = (xx >= 60e-9) & (xx < 180e-9)
    y_strip = (yy >= 60e-9) & (yy < 180e-9)
    plan_groove = x_strip | y_strip
    intersection = x_strip & y_strip
    recess = fluid & (z[:, None, None] >= gap * 1e-9) & plan_groove[None, :, :]
    gap_region = fluid & (z[:, None, None] < gap * 1e-9)
    junction = recess & intersection[None, :, :]
    arms = recess & (plan_groove & ~intersection)[None, :, :]
    umax = float(speed[fluid].max())
    gx, gy = periodic_gradient(pressure, fluid)
    gmag = np.sqrt(gx * gx + gy * gy)
    valid_grad = np.isfinite(gmag) & fluid
    grad_index = np.unravel_index(np.nanargmax(np.where(valid_grad, gmag, np.nan)), gmag.shape)
    recess_speed = np.where(recess, speed, np.inf)
    slow_index = np.unravel_index(np.argmin(recess_speed), recess_speed.shape)

    metrics = {
        "run_id": result["run_id"], "gap_nm": gap, "mode": mode,
        "source_vti": str(data["vti"]), "fluid_nodes": int(fluid.sum()),
        "recess_nodes": int(recess.sum()), "junction_nodes": int(junction.sum()),
        "arm_nodes": int(arms.sum()), "max_speed_m_s": umax,
        "mean_speed_fluid_m_s": float(speed[fluid].mean()),
        "mean_speed_gap_m_s": float(speed[gap_region].mean()),
        "mean_speed_recess_m_s": float(speed[recess].mean()),
        "mean_speed_junction_m_s": float(speed[junction].mean()),
        "mean_speed_arms_m_s": float(speed[arms].mean()),
        "max_abs_cross_velocity_m_s": float(np.max(np.abs(velocity[..., 1 if mode == "x" else 0][fluid]))),
        "max_abs_vertical_velocity_m_s": float(np.max(np.abs(velocity[..., 2][fluid]))),
        "pressure_min_Pa": float(pressure[fluid].min()),
        "pressure_max_Pa": float(pressure[fluid].max()),
        "pressure_disturbance_Pa": float(np.ptp(pressure[fluid])),
        "applied_pressure_gradient_Pa_m": float(result["applied_pressure_gradient_Pa_m"]),
        "local_pressure_gradient_rms_Pa_m": float(np.sqrt(np.nanmean(gmag[valid_grad] ** 2))),
        "local_pressure_gradient_max_Pa_m": float(np.nanmax(gmag[valid_grad])),
        "gradient_max_x_nm": float(x[grad_index[2]] * 1e9),
        "gradient_max_y_nm": float(y[grad_index[1]] * 1e9),
        "gradient_max_z_nm": float(z[grad_index[0]] * 1e9),
        "recess_min_speed_m_s": float(speed[slow_index]),
        "recess_min_speed_x_nm": float(x[slow_index[2]] * 1e9),
        "recess_min_speed_y_nm": float(y[slow_index[1]] * 1e9),
        "recess_min_speed_z_nm": float(z[slow_index[0]] * 1e9),
        "mass_drift": float(result["max_mass_abs_relative"]),
        "Mach_max": float(result["Mach_max"]),
    }
    for threshold in THRESHOLDS:
        tag = f"below_{int(threshold * 100):02d}pct_umax"
        metrics[f"low_speed_fraction_{tag}"] = float(np.count_nonzero(fluid & (speed < threshold * umax)) / fluid.sum())
        metrics[f"low_speed_fraction_{tag}_recess"] = float(np.count_nonzero(recess & (speed < threshold * umax)) / recess.sum())
        metrics[f"low_speed_fraction_{tag}_junction"] = float(np.count_nonzero(junction & (speed < threshold * umax)) / junction.sum())
        metrics[f"low_speed_fraction_{tag}_arms"] = float(np.count_nonzero(arms & (speed < threshold * umax)) / arms.sum())

    drive = 0 if mode == "x" else 1
    profile = []
    for i in range(48):
        if drive == 0:
            mask, vel, p = fluid[:, :, i], velocity[:, :, i, 0], pressure[:, :, i]
            gap_mask, recess_mask = gap_region[:, :, i], recess[:, :, i]
        else:
            mask, vel, p = fluid[:, i, :], velocity[:, i, :, 1], pressure[:, i, :]
            gap_mask, recess_mask = gap_region[:, i, :], recess[:, i, :]
        q_total = float(vel[mask].sum() * DX * DX)
        q_gap = float(vel[gap_mask].sum() * DX * DX)
        q_recess = float(vel[recess_mask].sum() * DX * DX)
        profile.append({
            "run_id": result["run_id"], "gap_nm": gap, "mode": mode,
            "coordinate_nm": (i + 0.5) * 5,
            "fluid_area_m2": float(mask.sum() * DX * DX),
            "pressure_section_mean_Pa": float(p[mask].mean()),
            "Q_total_m3_s": q_total, "Q_gap_m3_s": q_gap,
            "Q_recess_m3_s": q_recess,
            "recess_fraction_of_Q": q_recess / q_total if q_total else math.nan,
        })
    pmean = np.array([row["pressure_section_mean_Pa"] for row in profile])
    dp = (np.roll(pmean, -1) - np.roll(pmean, 1)) / (2 * DX)
    for row, grad in zip(profile, dp):
        row["periodic_section_pressure_gradient_Pa_m"] = float(grad)
    q = np.array([row["Q_total_m3_s"] for row in profile])
    metrics["section_Q_mean_m3_s"] = float(q.mean())
    metrics["section_Q_relative_span"] = float(np.ptp(q) / abs(q.mean()))
    recess_fraction = np.array([row["recess_fraction_of_Q"] for row in profile])
    metrics["recess_Q_fraction_mean"] = float(np.mean(recess_fraction))
    metrics["recess_Q_fraction_min"] = float(np.min(recess_fraction))
    metrics["recess_Q_fraction_max"] = float(np.max(recess_fraction))
    return metrics, profile


def path_map(gap: int, mode: str, data: dict) -> None:
    material, velocity, pressure = data["material"], data["velocity"], data["pressure"]
    x, y, z = data["x"] * 1e9, data["y"] * 1e9, data["z"] * 1e9
    iz = int(np.argmin(abs(z - (gap + 50))))
    fluid = material[iz] == 1
    u, v = velocity[iz, :, :, 0], velocity[iz, :, :, 1]
    speed = np.sqrt(u * u + v * v)
    um, vm = np.ma.masked_where(~fluid, u), np.ma.masked_where(~fluid, v)
    sm = np.ma.masked_where(~fluid, speed)
    pm = np.ma.masked_where(~fluid, pressure[iz])
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.25), constrained_layout=True)
    im0 = axes[0].pcolormesh(x, y, sm * 1e6, shading="nearest", cmap="viridis")
    axes[0].streamplot(x, y, um, vm, color="white", density=1.45, linewidth=.6, arrowsize=.7)
    global_umax = np.linalg.norm(velocity, axis=3)[material == 1].max()
    ratio = np.ma.masked_where(~fluid, speed / global_umax)
    contours = axes[0].contour(x, y, ratio, levels=[.05, .10], colors=["cyan", "magenta"], linewidths=.8)
    axes[0].clabel(contours, fmt={.05:"5%", .10:"10%"}, fontsize=7)
    fig.colorbar(im0, ax=axes[0], label=r"In-plane speed ($\mu$m/s)")
    im1 = axes[1].pcolormesh(x, y, pm, shading="nearest", cmap="coolwarm")
    axes[1].streamplot(x, y, um, vm, color="black", density=1.45, linewidth=.55, arrowsize=.7)
    fig.colorbar(im1, ax=axes[1], label="Pressure disturbance (Pa)")
    for ax, title in zip(axes, ("Velocity paths", "Pressure and paths")):
        ax.set(xlabel="x (nm)", ylabel="y (nm)", aspect="equal", title=title)
        ax.set_xlim(0, 240); ax.set_ylim(0, 240)
    fig.suptitle(f"SIM-EC1XT240 cross junction, h={gap} nm, {mode.upper()} drive, z={z[iz]:.1f} nm")
    stem = FIG / f"path_map_h{gap}_{mode}"
    fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def profile_figure(gap: int, mode: str, profile: list[dict]) -> None:
    x = np.array([row["coordinate_nm"] for row in profile])
    p = np.array([row["pressure_section_mean_Pa"] for row in profile])
    grad = np.array([row["periodic_section_pressure_gradient_Pa_m"] for row in profile])
    q = np.array([row["Q_total_m3_s"] for row in profile]) * 1e18
    q_gap = np.array([row["Q_gap_m3_s"] for row in profile]) * 1e18
    q_recess = np.array([row["Q_recess_m3_s"] for row in profile]) * 1e18
    fig, axes = plt.subplots(3, 1, figsize=(6.8, 7.5), sharex=True, constrained_layout=True)
    axes[0].plot(x, p); axes[0].set(ylabel="Section mean p (Pa)")
    axes[1].plot(x, grad * 1e-6); axes[1].axhline(0, color="0.5", lw=.7)
    axes[1].set(ylabel=r"Periodic local dp/ds ($10^6$ Pa/m)")
    axes[2].plot(x, q, label="total"); axes[2].plot(x, q_gap, "--", label="gap")
    axes[2].plot(x, q_recess, ":", label="recess")
    axes[2].set(xlabel=f"{mode} coordinate (nm)", ylabel=r"Section flow ($10^{-18}$ m$^3$/s)")
    axes[2].legend(ncol=3)
    fig.suptitle(f"h={gap} nm, {mode.upper()} drive: pressure and flow distribution")
    stem = FIG / f"pressure_flow_profile_h{gap}_{mode}"
    fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def vertical_path_map(gap: int, mode: str, data: dict) -> None:
    material, velocity, pressure = data["material"], data["velocity"], data["pressure"]
    x, y, z = data["x"] * 1e9, data["y"] * 1e9, data["z"] * 1e9
    center = int(np.argmin(abs(x - 120)))
    if mode == "x":
        coordinate = x; plane_material = material[:, center, :]
        tangential, vertical = velocity[:, center, :, 0], velocity[:, center, :, 2]
        plane_pressure = pressure[:, center, :]; axis_name = "x"; fixed_name = "y"; fixed_value = y[center]
    else:
        coordinate = y; plane_material = material[:, :, center]
        tangential, vertical = velocity[:, :, center, 1], velocity[:, :, center, 2]
        plane_pressure = pressure[:, :, center]; axis_name = "y"; fixed_name = "x"; fixed_value = x[center]
    fluid = plane_material == 1
    speed = np.sqrt(tangential*tangential + vertical*vertical)
    tm = np.ma.masked_where(~fluid, tangential); wm = np.ma.masked_where(~fluid, vertical)
    sm = np.ma.masked_where(~fluid, speed); pm = np.ma.masked_where(~fluid, plane_pressure)
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.2), constrained_layout=True)
    im0 = axes[0].pcolormesh(coordinate, z, sm*1e6, shading="nearest", cmap="viridis")
    axes[0].streamplot(coordinate, z, tm, wm, color="white", density=1.25, linewidth=.55, arrowsize=.7)
    fig.colorbar(im0, ax=axes[0], label=r"Section speed ($\mu$m/s)")
    im1 = axes[1].pcolormesh(coordinate, z, pm, shading="nearest", cmap="coolwarm")
    axes[1].streamplot(coordinate, z, tm, wm, color="black", density=1.25, linewidth=.5, arrowsize=.7)
    fig.colorbar(im1, ax=axes[1], label="Pressure disturbance (Pa)")
    for ax, title in zip(axes, ("Vertical velocity paths", "Vertical pressure and paths")):
        ax.set(xlabel=f"{axis_name} (nm)", ylabel="z (nm)", title=title)
        ax.set_xlim(0,240); ax.set_ylim(0,gap+110)
    fig.suptitle(f"h={gap} nm, {mode.upper()} drive, {fixed_name}={fixed_value:.1f} nm")
    stem = FIG / f"vertical_path_h{gap}_{mode}"
    fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    metrics_rows, profile_rows = [], []
    for gap in GAPS:
        for mode in MODES:
            run = run_dir(gap, mode)
            result = parse_result(run / "result.txt")
            data = read_core(final_vti(run))
            metrics, profile = describe_case(gap, mode, data, result)
            metrics_rows.append(metrics); profile_rows.extend(profile)
            path_map(gap, mode, data)
            profile_figure(gap, mode, profile)
            vertical_path_map(gap, mode, data)

    with (DATA / "path_metrics.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(metrics_rows[0]))
        writer.writeheader(); writer.writerows(metrics_rows)
    with (DATA / "pressure_flow_profiles.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(profile_rows[0]))
        writer.writeheader(); writer.writerows(profile_rows)

    labels = [f"h={r['gap_nm']}, {r['mode'].upper()}" for r in metrics_rows]
    positions = np.arange(len(labels)); width = .24
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.7), constrained_layout=True)
    for j, threshold in enumerate(THRESHOLDS):
        key = f"low_speed_fraction_below_{int(threshold*100):02d}pct_umax_recess"
        axes[0].bar(positions + (j-1)*width, [r[key]*100 for r in metrics_rows], width,
                    label=f"<{int(threshold*100)}% Umax")
    axes[0].set(xticks=positions, xticklabels=labels, ylabel="Recess low-speed volume (%)")
    axes[0].tick_params(axis="x", rotation=25); axes[0].legend()
    axes[1].bar(positions-width/2, [r["mean_speed_junction_m_s"]*1e6 for r in metrics_rows],
                width, label="junction")
    axes[1].bar(positions+width/2, [r["mean_speed_arms_m_s"]*1e6 for r in metrics_rows],
                width, label="arms")
    axes[1].set(xticks=positions, xticklabels=labels, ylabel=r"Mean speed ($\mu$m/s)")
    axes[1].tick_params(axis="x", rotation=25); axes[1].legend()
    fig.savefig(FIG / "low_speed_and_region_comparison.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "low_speed_and_region_comparison.pdf", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
