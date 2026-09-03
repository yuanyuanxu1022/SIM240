#!/usr/bin/env python3
"""Post-process the SIM-EC1XT240 straight-groove DNS: field plots + geometry schematic.

Reads the converged OpenLB VTI snapshot (velocity + pressure) and produces:
  - tmp/velocity_field.png   (x-z cross section, |u|, solid masked)
  - tmp/pressure_field.png   (x-z cross section, pressure)
  - tmp/geometry_schematic.png (annotated cross-section diagram)
"""
import os, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import patches

import vtk
from vtk.util.numpy_support import vtk_to_numpy

ROOT = os.path.join(os.path.dirname(__file__), "..")
TMP = os.path.join(ROOT, "tmp")
VTK_GLOB = os.path.join(TMP, "vtkData", "data", "grooveDns_iT*.vti")

# --- physical geometry (nm) ---
WALL, GROOVE, PERIOD = 120.0, 120.0, 240.0
DEPTH, FILM = 100.0, 65.0
H = DEPTH + FILM          # 165 nm

def load_latest_vti():
    files = sorted(glob.glob(VTK_GLOB), key=os.path.getmtime)
    files = [f for f in files if "iT0000000" not in f]  # skip initial state
    assert files, "no converged vti found"
    path = files[-1]
    r = vtk.vtkXMLImageDataReader()
    r.SetFileName(path)
    r.Update()
    img = r.GetOutput()
    ex = img.GetExtent()          # (x0,x1,y0,y1,z0,z1)
    orig = np.array(img.GetOrigin())
    sp = np.array(img.GetSpacing())
    nx = ex[1]-ex[0]+1; ny = ex[3]-ex[2]+1; nz = ex[5]-ex[4]+1
    pd = img.GetPointData()
    vel = vtk_to_numpy(pd.GetArray("physVelocity")).reshape(nz, ny, nx, 3)
    vel = vel.transpose(2, 1, 0, 3)          # (x, y, z, 3)
    pre = vtk_to_numpy(pd.GetArray("physPressure")).reshape(nz, ny, nx)
    pre = pre.transpose(2, 1, 0)             # (x, y, z)
    x = (orig[0] + (ex[0] + np.arange(nx)) * sp[0]) * 1e9   # nm
    z = (orig[2] + (ex[4] + np.arange(nz)) * sp[2]) * 1e9   # nm
    print(f"loaded {os.path.basename(path)}  shape xyz={nx}x{ny}x{nz}, x=[{x[0]:.1f},{x[-1]:.1f}]nm z=[{z[0]:.1f},{z[-1]:.1f}]nm")
    return vel, pre, x, z

def solid_mask(x, z):
    """analytic solid mask (True = solid) on the x-z plane."""
    X, Z = np.meshgrid(x, z, indexing="ij")
    wall = (np.mod(X, PERIOD) < WALL)
    solid = (Z < 0) | (Z > H) | ((Z < DEPTH) & wall)
    return solid

def main():
    vel, pre, x, z = load_latest_vti()
    ny = vel.shape[1]
    iy = ny // 2              # mid-y slice (flow is y-invariant)

    umag = np.linalg.norm(vel[:, iy, :, :], axis=-1)      # (x, z)
    p    = pre[:, iy, :]
    solid = solid_mask(x, z)

    X, Z = np.meshgrid(x, z, indexing="ij")
    solid_rgba = np.where(solid, 0.85, np.nan)

    # ---------- velocity field ----------
    fig, ax = plt.subplots(figsize=(7, 3.4))
    um = np.ma.masked_where(solid, umag)
    pc = ax.pcolormesh(X, Z, um, cmap="viridis", shading="auto")
    ax.pcolormesh(X, Z, solid_rgba, cmap="Greys", vmin=0, vmax=1, shading="auto")
    cb = fig.colorbar(pc, ax=ax, pad=0.02)
    cb.set_label("velocity magnitude  |u|  [m/s]")
    ax.set_xlabel("x [nm] (transverse)")
    ax.set_ylabel("z [nm] (vertical)")
    ax.set_title("Velocity field, x–z cross section (flow along groove ⊥ plane)")
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(os.path.join(TMP, "velocity_field.png"), dpi=150)
    plt.close(fig)
    print("saved velocity_field.png  |u|max =", float(um.max()), "m/s")

    # ---------- pressure field ----------
    pm = np.ma.masked_where(solid, p)
    vmax = np.nanmax(np.abs(pm - np.nanmean(pm)))
    fig, ax = plt.subplots(figsize=(7, 3.4))
    pc = ax.pcolormesh(X, Z, pm, cmap="RdBu_r",
                       vmin=np.nanmean(pm)-vmax, vmax=np.nanmean(pm)+vmax,
                       shading="auto")
    ax.pcolormesh(X, Z, solid_rgba, cmap="Greys", vmin=0, vmax=1, shading="auto")
    cb = fig.colorbar(pc, ax=ax, pad=0.02)
    cb.set_label("pressure p  [Pa]")
    ax.set_xlabel("x [nm] (transverse)")
    ax.set_ylabel("z [nm] (vertical)")
    ax.set_title("Pressure field, x–z cross section (body-force driven, periodic)")
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(os.path.join(TMP, "pressure_field.png"), dpi=150)
    plt.close(fig)
    print(f"saved pressure_field.png  p range = [{np.nanmin(pm):.3e}, {np.nanmax(pm):.3e}] Pa")

    # ---------- geometry schematic ----------
    fig, ax = plt.subplots(figsize=(8, 4.6))
    for k in range(-1, 3):
        x0 = k * PERIOD
        # wall
        ax.add_patch(patches.Rectangle((x0, 0), WALL, DEPTH,
                     facecolor="#f2a0a8", edgecolor="#8a3b47", lw=1.2, zorder=2))
        # groove (fluid)
        ax.add_patch(patches.Rectangle((x0 + WALL, 0), GROOVE, DEPTH,
                     facecolor="#dbeafe", edgecolor="#2b6cb0", lw=1.0, zorder=2))
    # film (fluid)
    ax.add_patch(patches.Rectangle((-PERIOD, DEPTH), 4*PERIOD, FILM,
                 facecolor="#dbeafe", edgecolor="#2b6cb0", lw=1.0, zorder=2))
    # top / bottom solid
    ax.add_patch(patches.Rectangle((-PERIOD, H), 4*PERIOD, 30, facecolor="#f2a0a8",
                 edgecolor="#8a3b47", lw=1.2, zorder=2))
    ax.add_patch(patches.Rectangle((-PERIOD, -30), 4*PERIOD, 30, facecolor="#f2a0a8",
                 edgecolor="#8a3b47", lw=1.2, zorder=2))

    # labels
    ax.annotate("", xy=(WALL, H+18), xytext=(0, H+18),
                arrowprops=dict(arrowstyle="<->", color="k", lw=1))
    ax.text(WALL/2, H+22, f"wall {WALL:.0f} nm", ha="center", va="bottom", fontsize=9)
    ax.annotate("", xy=(PERIOD, H+18), xytext=(WALL, H+18),
                arrowprops=dict(arrowstyle="<->", color="k", lw=1))
    ax.text((WALL+PERIOD)/2, H+22, f"groove {GROOVE:.0f} nm", ha="center", va="bottom", fontsize=9)
    ax.annotate("", xy=(PERIOD, -26), xytext=(0, -26),
                arrowprops=dict(arrowstyle="<->", color="k", lw=1))
    ax.text(PERIOD/2, -34, f"period {PERIOD:.0f} nm", ha="center", va="top", fontsize=9)
    ax.annotate("", xy=(PERIOD+10, DEPTH), xytext=(PERIOD+10, H),
                arrowprops=dict(arrowstyle="<->", color="k", lw=1))
    ax.text(PERIOD+13, (DEPTH+H)/2, f"film {FILM:.0f} nm", va="center", fontsize=9)
    ax.annotate("", xy=(WALL/2, 0), xytext=(WALL/2, DEPTH),
                arrowprops=dict(arrowstyle="<->", color="k", lw=1))
    ax.text(WALL/2+3, DEPTH/2, f"depth {DEPTH:.0f} nm", va="center", fontsize=9)
    ax.text(-PERIOD+8, -46, "solid wall = no-slip (pink)    groove/film = fluid (blue)", fontsize=9)
    ax.set_xlim(-PERIOD, 2*PERIOD)
    ax.set_ylim(-52, H+34)
    ax.set_xlabel("x [nm] (transverse)  —  groove direction y ⊥ plane")
    ax.set_ylabel("z [nm] (vertical)")
    ax.set_title("Straight-groove unit cell (cross section), flow driven along groove")
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(os.path.join(TMP, "geometry_schematic.png"), dpi=150)
    plt.close(fig)
    print("saved geometry_schematic.png")

if __name__ == "__main__":
    main()
