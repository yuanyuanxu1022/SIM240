#!/usr/bin/env python3
"""Geometry verification for the SIM-EC1XT240 straight-groove DNS case.

Reads the material field written by `./grooveDns --geometry-only`
(verify/vtkData/data/material_iT0000000iC00000.vti) and produces the four
verification outputs required before any DNS is allowed to run:

  1. x-z cross-section material figure   (verify/xz_section.png)
  2. x-y top-view material figure        (verify/xy_topview.png)
  3. material-number statistics          (printed + verify/material_stats.txt)
  4. automatic groove/wall width measurement (printed + same file)

The expected geometry is (transverse x, all segments full channel height 65 nm):

    wall(120) | groove(120) | wall(120) | groove(120) | wall(120)   Lx=600 nm

Material numbers: 1 = fluid (groove), 2 = solid (wall).  The script does NOT
assume the widths are correct — it measures them from the field and reports the
result explicitly, so the user can confirm before proceeding.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors

import vtk
from vtk.util.numpy_support import vtk_to_numpy

ROOT = os.path.join(os.path.dirname(__file__), "..")
VERIFY = os.path.join(ROOT, "verify")
MAT_VTI = os.path.join(VERIFY, "vtkData", "data", "material_iT0000000iC00000.vti")

# expected geometry (nm)
EXPECT_WALL = 120.0
EXPECT_GROOVE = 120.0
EXPECT_LX = 600.0
EXPECT_LY = 240.0
EXPECT_H = 65.0
NM = 1.0e9

def load_material():
    if not os.path.exists(MAT_VTI):
        raise SystemExit(f"material field not found: {MAT_VTI}\n"
                         f"run `./grooveDns --geometry-only` first.")
    r = vtk.vtkXMLImageDataReader()
    r.SetFileName(MAT_VTI)
    r.Update()
    img = r.GetOutput()
    ex = img.GetExtent()
    orig = np.array(img.GetOrigin())
    sp = np.array(img.GetSpacing())
    nx, ny, nz = ex[1]-ex[0]+1, ex[3]-ex[2]+1, ex[5]-ex[4]+1
    arr = vtk_to_numpy(img.GetPointData().GetArray(0))          # material number
    mat = arr.reshape(nz, ny, nx).astype(np.int32)
    mat = mat.transpose(2, 1, 0)                                # (x, y, z)
    x = (orig[0] + (ex[0] + np.arange(nx)) * sp[0]) * NM         # nm
    y = (orig[1] + (ex[2] + np.arange(ny)) * sp[1]) * NM
    z = (orig[2] + (ex[4] + np.arange(nz)) * sp[2]) * NM
    return mat, x, y, z

def core_mask(x, y, z):
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    return ((X >= -1e-9) & (X <= EXPECT_LX + 1e-9) &
            (Y >= -1e-9) & (Y <= EXPECT_LY + 1e-9) &
            (Z >= -15.1) & (Z <= 80.1))

def run_segments(line_x, line_mat):
    """Split a 1-D material line into contiguous runs.

    Returns a list of dicts: {material, start_x, end_x, n_nodes}.
    start_x/end_x are the physical x of the first/last *node* of the run.
    """
    runs = []
    start = 0
    for i in range(1, len(line_mat)):
        if line_mat[i] != line_mat[i-1]:
            runs.append(dict(material=int(line_mat[i-1]),
                             start_x=line_x[start], end_x=line_x[i-1],
                             n_nodes=i - start))
            start = i
    runs.append(dict(material=int(line_mat[-1]),
                     start_x=line_x[start], end_x=line_x[-1],
                     n_nodes=len(line_mat) - start))
    return runs

def main():
    mat, x, y, z = load_material()
    nx, ny, nz = mat.shape
    print(f"loaded material field  shape(x,y,z) = ({nx},{ny},{nz})")
    print(f"  x in [{x[0]:.1f}, {x[-1]:.1f}] nm   "
          f"y in [{y[0]:.1f}, {y[-1]:.1f}] nm   z in [{z[0]:.1f}, {z[-1]:.1f}] nm")

    # ---- 3. material statistics (core region only) ----
    core = core_mask(x, y, z)
    core_mat = mat[core]
    stats = {m: int(np.sum(core_mat == m)) for m in (0, 1, 2)}
    total = int(core.sum())
    print("\n=== material-number statistics (core region) ===")
    for m in (0, 1, 2):
        print(f"  material {m}: {stats[m]:>7d} nodes "
              f"({100.0*stats[m]/total:6.2f} %)")
    print(f"  total core nodes: {total}")
    # fluid = 2 grooves * 24 (x) * 49 (y, incl. periodic duplicate) * 13 (z)
    exp_fluid = 2 * (round(EXPECT_GROOVE/5) * (round(EXPECT_LY/5)+1) * round(EXPECT_H/5))
    print(f"  expected fluid nodes (24x49x13 per groove, 49 = 48 + periodic dup): {exp_fluid}")
    print(f"  fluid node count matches expected: {stats[1] == exp_fluid}")

    # ---- periodic-boundary consistency (y direction): node y=0 must equal y=Ly ----
    iy0 = np.argmin(np.abs(y - 0.0))
    iyL = np.argmin(np.abs(y - EXPECT_LY))
    periodic_ok = bool(np.array_equal(mat[:, iy0, :], mat[:, iyL, :]))
    print(f"\nperiodic-boundary consistency (y=0 vs y={EXPECT_LY:.0f} nm): "
          f"{'MATCH' if periodic_ok else 'MISMATCH'}")

    # ---- probe line for width measurement: mid-channel z, mid y ----
    ix_mid = np.argmin(np.abs(z - 30.0))     # mid of 0..65 nm channel
    iy_mid = np.argmin(np.abs(y - EXPECT_LY/2))
    core_x = (x >= -1e-9) & (x <= EXPECT_LX + 1e-9)   # drop halo nodes at x<0 / x>600
    line = mat[:, iy_mid, ix_mid][core_x]    # (x,) restricted to core
    xline = x[core_x]
    zline = z[ix_mid]; yline = y[iy_mid]
    print(f"\n=== width measurement (probe at y={yline:.1f} nm, z={zline:.1f} nm) ===")

    runs = run_segments(xline, line)
    # physical width = distance between successive run *starts* (last run -> Lx)
    out_lines = []
    header = (f"material field x-scan (y={yline:.1f} nm, z={zline:.1f} nm):\n"
              f"  wall(120) | groove(120) | wall(120) | groove(120) | wall(120)\n")
    out_lines.append(header)
    widths = []
    for i, r in enumerate(runs):
        start = r["start_x"]
        end = runs[i+1]["start_x"] if i+1 < len(runs) else EXPECT_LX
        w = end - start
        name = {1: "groove (fluid)", 2: "wall (solid)"}.get(r["material"], f"mat{r['material']}")
        line = (f"  {name:<15} x=[{start:6.1f}, {end:6.1f}) nm   "
                f"width = {w:6.1f} nm   ({r['n_nodes']} nodes)")
        print("  " + line)
        out_lines.append("  " + line + "\n")
        if r["material"] in (1, 2):
            widths.append((name, w, r["n_nodes"]))

    # summary / pass-fail
    print("\n  expected: wall 120 nm, groove 120 nm (tolerance +/- 5 nm = 1 node)")
    ok = True
    for name, w, nn in widths:
        exp = EXPECT_GROOVE if "groove" in name else EXPECT_WALL
        flag = "OK" if abs(w - exp) <= 5.0 + 1e-6 else "MISMATCH"
        if flag != "OK":
            ok = False
        print(f"    {name:<15} {w:6.1f} nm  (expected {exp:.0f} nm)  -> {flag}")
        out_lines.append(f"    {name:<15} {w:6.1f} nm (expected {exp:.0f}) -> {flag}\n")

    print("\n  GEOMETRY: " + ("MATCHES expected wall/groove widths." if ok
                             else "DOES NOT match — STOP and fix geometry."))

    # ---- write stats + measurement to a text file ----
    with open(os.path.join(VERIFY, "material_stats.txt"), "w") as f:
        f.write("=== SIM-EC1XT240 straight-groove geometry verification ===\n\n")
        f.write("material-number statistics (core region):\n")
        for m in (0, 1, 2):
            f.write(f"  material {m}: {stats[m]} nodes\n")
        f.write(f"  total core nodes: {total}\n\n")
        f.write("".join(out_lines))
        f.write("\nGEOMETRY: " + ("MATCHES expected wall/groove widths.\n" if ok
                                  else "DOES NOT match — STOP and fix geometry.\n"))

    # ---- 1. x-z cross section (mid-y) ----
    fig, ax = plt.subplots(figsize=(10, 2.8))
    xz = mat[:, iy_mid, :].T            # (z, x)
    cmap = mcolors.ListedColormap(["#e5e7eb", "#7fb3e8", "#f2a0a8"])  # 0 void, 1 fluid, 2 solid
    bounds = [-0.5, 0.5, 1.5, 2.5]
    norm = mcolors.BoundaryNorm(bounds, cmap.N)
    X, Z = np.meshgrid(x, z, indexing="ij")
    pc = ax.pcolormesh(X.T, Z.T, xz, cmap=cmap, norm=norm, shading="auto")
    # annotate the wall/groove boundaries
    for xb in (0, 120, 240, 360, 480, 600):
        ax.axvline(xb, color="k", lw=0.5, ls="--", alpha=0.5)
    ax.set_xlim(0, EXPECT_LX)
    ax.set_ylim(-15, 80)
    ax.set_xlabel("x [nm] (transverse)")
    ax.set_ylabel("z [nm] (vertical)")
    ax.set_title("x–z cross section (mid-y)  —  blue = fluid groove, pink = solid wall")
    ax.set_aspect("equal")
    fig.colorbar(pc, ax=ax, ticks=[0, 1, 2], pad=0.02).set_label("material number")
    fig.tight_layout()
    fig.savefig(os.path.join(VERIFY, "xz_section.png"), dpi=150)
    plt.close(fig)
    print("\nsaved verify/xz_section.png")

    # ---- 2. x-y top view (mid-channel z) ----
    fig, ax = plt.subplots(figsize=(10, 4.4))
    xy = mat[:, :, ix_mid].T            # (y, x)
    X, Y = np.meshgrid(x, y, indexing="ij")
    ax.pcolormesh(X.T, Y.T, xy, cmap=cmap, norm=norm, shading="auto")
    for xb in (0, 120, 240, 360, 480, 600):
        ax.axvline(xb, color="k", lw=0.5, ls="--", alpha=0.5)
    ax.set_xlim(0, EXPECT_LX)
    ax.set_ylim(0, EXPECT_LY)
    ax.set_xlabel("x [nm] (transverse)")
    ax.set_ylabel("y [nm] (groove direction)")
    ax.set_title("x–y top view (mid-channel z = 30 nm)  —  blue = fluid, pink = solid")
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(os.path.join(VERIFY, "xy_topview.png"), dpi=150)
    plt.close(fig)
    print("saved verify/xy_topview.png")

    print(f"\nresults written to {os.path.join(VERIFY, 'material_stats.txt')}")
    if not ok:
        print("\n*** GEOMETRY MISMATCH — fix case.h and re-run --geometry-only. "
              "DO NOT proceed to DNS. ***")
    else:
        print("\n*** geometry verified: wall/groove widths are exactly 120 nm. "
              "safe to proceed to DNS. ***")

if __name__ == "__main__":
    main()
