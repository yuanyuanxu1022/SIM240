#!/usr/bin/env python3
"""Final formal results for the SIM-EC1XT240 straight-groove DNS (fine grid).

Reads the converged dx = 1.25 nm DNS output (velocity + pressure VTK and the
flowrate.dat time series) and produces the formal deliverables:

  final_velocity_fine.vti      velocity field (single merged VTK, physVelocity)
  final_pressure_fine.vti      pressure field (single merged VTK, physPressure)
  final_velocity_field_fine.png   x-z slice of u_y (solid walls -> no flow)
  final_pressure_field_fine.png   x-z slice of pressure [Pa]
  final_convergence_fine.png      Qy / B_yy vs iteration (convergence)
  final_flowrate_fine.dat         copy of the flow-rate time series

(final_results_fine.txt is written directly by case.h.)

Physics: dx = 1.25 nm, a_y = 1e6 m/s^2, Ly = 20 nm (y-invariant), wall|groove|wall|groove|wall.
"""
import os
import re
import shutil
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import vtk
from vtk.util.numpy_support import vtk_to_numpy

ROOT = os.path.join(os.path.dirname(__file__), "..")
TMP = os.path.join(ROOT, "tmp")
VTK_DIR = os.path.join(TMP, "vtkData", "data")
PVD = os.path.join(TMP, "vtkData", "grooveDns.pvd")
MAT_VTI = os.path.join(ROOT, "verify", "vtkData", "data", "material_iT0000000iC00000.vti")
FLOW = os.path.join(TMP, "flowrate.dat")

DX_NM = 1.25
AY = 1e6
SOLID_GRAY = ListedColormap(["#cbd5e1"])   # light gray for solid walls


def load_vti(path):
    r = vtk.vtkXMLImageDataReader()
    r.SetFileName(path)
    r.Update()
    img = r.GetOutput()
    ex = img.GetExtent()
    orig = np.array(img.GetOrigin())
    sp = np.array(img.GetSpacing())
    nx, ny, nz = ex[1] - ex[0] + 1, ex[3] - ex[2] + 1, ex[5] - ex[4] + 1
    x = (orig[0] + (ex[0] + np.arange(nx)) * sp[0]) * 1e9   # nm
    y = (orig[1] + (ex[2] + np.arange(ny)) * sp[1]) * 1e9
    z = (orig[2] + (ex[4] + np.arange(nz)) * sp[2]) * 1e9
    pd = img.GetPointData()
    arrays = {pd.GetArrayName(i): vtk_to_numpy(pd.GetArray(i))
              for i in range(pd.GetNumberOfArrays())}
    return img, arrays, x, y, z, (nx, ny, nz)


def find_converged_step(pvd_path):
    with open(pvd_path) as f:
        text = f.read()
    steps = [int(s) for s in re.findall(r'timestep="(\d+)"', text)]
    return max(steps)


def write_field_vti(path, img, drop_name):
    """Write a single-array VTI by deep-copying the source and dropping the other array.

    The system's vtkXMLImageDataWriter defaults to format="appended", which this VTK
    build's own reader cannot parse back.  Force inline base64 ("binary") instead,
    matching OpenLB's own VTI output.
    """
    out = vtk.vtkImageData()
    out.DeepCopy(img)
    out.GetPointData().RemoveArray(drop_name)
    w = vtk.vtkXMLImageDataWriter()
    w.SetDataModeToBinary()   # inline base64, not appended
    w.SetFileName(path)
    w.SetInputData(out)
    w.Write()


def load_flowrate(path):
    """Parse flowrate.dat, skipping any partial (mid-write) trailing line."""
    rows = []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split()
            if len(parts) == 7:
                rows.append([float(p) for p in parts])
    return np.array(rows)


def main():
    # ---- locate the converged timestep ----
    step = find_converged_step(PVD)
    conv_vti = os.path.join(VTK_DIR, f"grooveDns_iT{step:07d}iC00000.vti")
    print(f"converged timestep = {step} -> {conv_vti}")

    img, arrs, x, y, z, (nx, ny, nz) = load_vti(conv_vti)
    vel_raw = arrs["physVelocity"]    # (npoints, 3) VTK order
    pres_raw = arrs["physPressure"]   # (npoints,)

    # reshape to (x, y, z[, comp]) for slicing
    vel = vel_raw.reshape(nz, ny, nx, 3).transpose(2, 1, 0, 3)   # (nx, ny, nz, 3)
    pres = pres_raw.reshape(nz, ny, nx).transpose(2, 1, 0)       # (nx, ny, nz)

    # ---- material field (solid/fluid) for the overlay ----
    _, mat_arrs, xm, ym, zm, _ = load_vti(MAT_VTI)
    mat = mat_arrs["geometry"].reshape(nz, ny, nx).transpose(2, 1, 0).astype(int)

    iy = int(np.argmin(np.abs(y - 10.0)))     # mid-y = 10 nm
    print(f"mid-y slice index iy={iy} (y={y[iy]:.2f} nm)")

    uy = vel[:, iy, :, 1]     # (nx, nz) y-velocity
    p  = pres[:, iy, :]       # (nx, nz) pressure [Pa]
    m  = mat[:, iy, :]        # (nx, nz) material (1=fluid, 2=solid)

    # ---- crop the 1-node VTK overlap halo to the core physical domain ----
    core_x = (x >= -1e-6) & (x <= 600.0 + 1e-6)
    core_z = (z >= -3.0 * DX_NM - 1e-6) & (z <= 65.0 + 3.0 * DX_NM + 1e-6)
    xc, zc = x[core_x], z[core_z]
    uy_c = uy[np.ix_(core_x, core_z)]
    p_c  = p[np.ix_(core_x, core_z)]
    m_c  = m[np.ix_(core_x, core_z)]
    Xc, Zc = np.meshgrid(xc, zc)          # (nz, nx)
    fluid = (m_c == 1)                    # (nx, nz)

    # ---- write single-field VTKs ----
    write_field_vti(os.path.join(TMP, "final_velocity_fine.vti"), img, "physPressure")
    write_field_vti(os.path.join(TMP, "final_pressure_fine.vti"), img, "physVelocity")
    print("wrote final_velocity_fine.vti / final_pressure_fine.vti")

    def draw_solid(ax):
        # shade solid (non-fluid) cells light gray; returns mask in (nz,nx)
        solid = np.where(fluid.T, np.nan, 1.0)
        ax.pcolormesh(Xc, Zc, solid, cmap=SOLID_GRAY, vmin=0, vmax=1, shading="nearest")

    # ---- velocity field figure (u_y, x-z slice) ----
    fig, ax = plt.subplots(figsize=(12.0, 3.0))
    draw_solid(ax)
    C = np.where(fluid.T, uy_c.T, np.nan)      # (nz, nx) fluid only
    vmax = np.nanmax(np.abs(C))
    pcm = ax.pcolormesh(Xc, Zc, C, cmap="viridis", shading="nearest", vmin=0.0, vmax=vmax)
    ax.contour(Xc, Zc, fluid.T.astype(float), levels=[0.5], colors="white", linewidths=0.6)
    cb = fig.colorbar(pcm, ax=ax, pad=0.02)
    cb.set_label(r"$u_y$ [m/s]")
    ax.set_xlabel("x [nm]")
    ax.set_ylabel("z [nm]")
    ax.set_title(f"Velocity field $u_y$ (x-z slice, mid-y) — dx = {DX_NM} nm, "
                 f"$a_y$ = {AY:.0e} m/s$^2$")
    fig.tight_layout()
    fig.savefig(os.path.join(TMP, "final_velocity_field_fine.png"), dpi=150)
    plt.close(fig)
    print(f"wrote final_velocity_field_fine.png  (u_y max = {vmax:.3e} m/s)")

    # ---- pressure field figure (x-z slice, Pa) ----
    fig, ax = plt.subplots(figsize=(12.0, 3.0))
    draw_solid(ax)
    Cp = np.where(fluid.T, p_c.T, np.nan)
    pmax = np.nanmax(np.abs(Cp))
    if not np.isfinite(pmax) or pmax == 0.0:
        pmax = 1.0
    pcm = ax.pcolormesh(Xc, Zc, Cp, cmap="RdBu_r", shading="nearest",
                        vmin=-pmax, vmax=pmax)
    ax.contour(Xc, Zc, fluid.T.astype(float), levels=[0.5], colors="black", linewidths=0.6)
    cb = fig.colorbar(pcm, ax=ax, pad=0.02)
    cb.set_label(r"pressure [Pa]")
    ax.set_xlabel("x [nm]")
    ax.set_ylabel("z [nm]")
    ax.set_title(f"Pressure field (x-z slice, mid-y) — dx = {DX_NM} nm, "
                 f"$a_y$ = {AY:.0e} m/s$^2$")
    fig.tight_layout()
    fig.savefig(os.path.join(TMP, "final_pressure_field_fine.png"), dpi=150)
    plt.close(fig)
    print(f"wrote final_pressure_field_fine.png  (|p| max = {pmax:.3e} Pa)")

    # ---- convergence figure (Qy and B_yy vs iteration) ----
    d = load_flowrate(FLOW)
    iT, Qy, Byy = d[:, 0], d[:, 2], d[:, 6]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 3.2))
    ax1.plot(iT, Qy, lw=1.2, color="#2563eb")
    ax1.set_xlabel("iteration iT")
    ax1.set_ylabel(r"$Q_y$ [m$^3$/s]")
    ax1.set_title(r"$Q_y$ convergence")
    ax1.grid(True, lw=0.4, alpha=0.5)
    ax2.plot(iT, Byy * 1e18, lw=1.2, color="#059669")
    ax2.set_xlabel("iteration iT")
    ax2.set_ylabel(r"$B_{yy}$ [nm$^2$]")
    ax2.set_title(r"$B_{yy}$ convergence")
    ax2.grid(True, lw=0.4, alpha=0.5)
    fig.suptitle(f"Convergence to steady state — dx = {DX_NM} nm, "
                 f"$a_y$ = {AY:.0e} m/s$^2$", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(os.path.join(TMP, "final_convergence_fine.png"), dpi=150)
    plt.close(fig)
    print("wrote final_convergence_fine.png")

    # ---- copy flow-rate time series ----
    shutil.copy(FLOW, os.path.join(TMP, "final_flowrate_fine.dat"))
    print("wrote final_flowrate_fine.dat")

    print("\nAll final deliverables written to tmp/")


if __name__ == "__main__":
    main()
