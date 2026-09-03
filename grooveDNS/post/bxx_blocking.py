#!/usr/bin/env python3
"""Post-processing for the SIM-EC1XT240 transverse blocking check (B_xx).

Reads the CHECK_BXX run output and produces the formal deliverables:

  bxx_blocking.png            Qx / B_xx numerical residual vs iteration
  final_velocity_bxx.vti      velocity field (single merged VTK, physVelocity)
  final_velocity_field_bxx.png  x-z slice of u_x (blocked -> ~0)

(bxx_blocking_results.txt and flowrate_bxx.dat are written directly by case.h.)

Physics: straight grooves separated by continuous (y-invariant) solid walls, so
x-flow is blocked and the exact steady state is u_x = 0 -> B_xx = 0.
"""
import os
import re
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
PVD = os.path.join(TMP, "vtkData", "grooveDnsBxx.pvd")
FLOW = os.path.join(TMP, "flowrate_bxx.dat")

# geometry + fluid (must match case.h defaults)
WALL_NM = 120.0
GROOVE_NM = 120.0
N_GROOVES = 2
HF_NM = 65.0
LX_NM = (N_GROOVES + 1) * WALL_NM + N_GROOVES * GROOVE_NM   # 600 nm
MU = 1.0e-3          # Pa.s (rho=1000, nu=1e-6)
RHO = 1000.0
AX = 1.0e6           # m/s^2

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
    """Write a single-array VTI (inline base64, matching OpenLB's own output)."""
    out = vtk.vtkImageData()
    out.DeepCopy(img)
    out.GetPointData().RemoveArray(drop_name)
    w = vtk.vtkXMLImageDataWriter()
    w.SetDataModeToBinary()   # inline base64, not appended
    w.SetFileName(path)
    w.SetInputData(out)
    w.Write()


def load_flowrate(path):
    """Parse flowrate_bxx.dat, skipping any partial (mid-write) trailing line."""
    rows = []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split()
            if len(parts) == 5:
                rows.append([float(p) for p in parts])
    return np.array(rows)


def fluid_mask(x, z):
    """Bool mask (nx, nz) True where fluid, from the known wall|groove layout."""
    X, Z = np.meshgrid(x, z)          # (nz, nx)
    xf = np.zeros_like(X, dtype=bool)
    for g in range(N_GROOVES):
        x0 = (g + 1) * WALL_NM + g * GROOVE_NM
        xf |= (X >= x0) & (X < x0 + GROOVE_NM)
    zf = (Z >= 0.0) & (Z <= HF_NM)
    return (xf & zf).T               # (nx, nz)


def main():
    # ---- locate the final timestep ----
    step = find_converged_step(PVD)
    conv_vti = os.path.join(VTK_DIR, f"grooveDnsBxx_iT{step:07d}iC00000.vti")
    print(f"final timestep = {step} -> {conv_vti}")

    img, arrs, x, y, z, (nx, ny, nz) = load_vti(conv_vti)
    vel_raw = arrs["physVelocity"]    # (npoints, 3) VTK order

    vel = vel_raw.reshape(nz, ny, nx, 3).transpose(2, 1, 0, 3)   # (nx, ny, nz, 3)

    iy = int(np.argmin(np.abs(y - y.mean())))     # mid-y
    print(f"mid-y slice index iy={iy} (y={y[iy]:.2f} nm)")

    ux = vel[:, iy, :, 0]     # (nx, nz) x-velocity

    # ---- crop the 1-node VTK overlap halo to the core physical domain ----
    core_x = (x >= -1e-6) & (x <= LX_NM + 1e-6)
    core_z = (z >= -1e-6) & (z <= HF_NM + 1e-6)
    xc, zc = x[core_x], z[core_z]
    ux_c = ux[np.ix_(core_x, core_z)]
    Xc, Zc = np.meshgrid(xc, zc)          # (nz, nx)
    fluid = fluid_mask(xc, zc)            # (nx, nz)

    # ---- write single-field velocity VTK ----
    write_field_vti(os.path.join(TMP, "final_velocity_bxx.vti"), img, "physPressure")
    print("wrote final_velocity_bxx.vti")

    def draw_solid(ax):
        solid = np.where(fluid.T, np.nan, 1.0)
        ax.pcolormesh(Xc, Zc, solid, cmap=SOLID_GRAY, vmin=0, vmax=1, shading="nearest")

    # ---- transverse velocity field figure (u_x, x-z slice) ----
    fig, ax = plt.subplots(figsize=(12.0, 3.0))
    draw_solid(ax)
    C = np.where(fluid.T, ux_c.T, np.nan)      # (nz, nx) fluid only
    vmax = np.nanmax(np.abs(C))
    if not np.isfinite(vmax) or vmax == 0.0:
        vmax = 1.0
    pcm = ax.pcolormesh(Xc, Zc, C, cmap="RdBu_r", shading="nearest", vmin=-vmax, vmax=vmax)
    ax.contour(Xc, Zc, fluid.T.astype(float), levels=[0.5], colors="black", linewidths=0.6)
    cb = fig.colorbar(pcm, ax=ax, pad=0.02)
    cb.set_label(r"$u_x$ [m/s]")
    ax.set_xlabel("x [nm]")
    ax.set_ylabel("z [nm]")
    ax.set_title(r"Transverse velocity $u_x$ (x-z slice, mid-y) — blocked $\Rightarrow u_x\approx0$")
    fig.tight_layout()
    fig.savefig(os.path.join(TMP, "final_velocity_field_bxx.png"), dpi=150)
    plt.close(fig)
    print(f"wrote final_velocity_field_bxx.png  (|u_x| max = {vmax:.3e} m/s)")

    # ---- convergence figure (Qx and B_xx numerical residual vs iteration) ----
    d = load_flowrate(FLOW)
    iT, Qx, qx = d[:, 0], d[:, 2], d[:, 3]
    Bxx = MU * qx / (RHO * AX) * 1e18   # nm^2 (numerical residual)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 3.2))
    ax1.plot(iT, Qx, lw=1.2, color="#2563eb")
    ax1.set_xlabel("iteration iT")
    ax1.set_ylabel(r"$Q_x$ [m$^3$/s]")
    ax1.set_title(r"$Q_x \rightarrow 0$ (blocked)")
    ax1.grid(True, lw=0.4, alpha=0.5)
    ax2.plot(iT, Bxx, lw=1.2, color="#dc2626")
    ax2.set_xlabel("iteration iT")
    ax2.set_ylabel(r"$B_{xx}^{\rm num}$ [nm$^2$]")
    ax2.set_title(r"$B_{xx}$ numerical residual")
    ax2.grid(True, lw=0.4, alpha=0.5)
    fig.suptitle("Transverse blocking check — $Q_x$ / $B_{xx}$ vs iteration", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(os.path.join(TMP, "bxx_blocking.png"), dpi=150)
    plt.close(fig)
    print("wrote bxx_blocking.png")

    print("\nAll CHECK_BXX deliverables written to tmp/")


if __name__ == "__main__":
    main()
