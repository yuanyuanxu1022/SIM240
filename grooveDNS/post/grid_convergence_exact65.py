#!/usr/bin/env python3
"""Strict isogeometric grid-convergence study (exact-65 nm height).

Refines the lattice spacing dx while keeping the physical liquid height EXACTLY
65 nm at every grid (65 nm is divided by dx into an integer number of cells):

    dx = 5.0 nm  ->  5.0  x 13 = 65 nm   (RESOLUTION = 48)
    dx = 2.5 nm  ->  2.5  x 26 = 65 nm   (RESOLUTION = 96)
    dx = 1.25 nm ->  1.25 x 52 = 65 nm   (RESOLUTION = 192)

Fixed physical parameters:
    wall = groove = 120 nm, Lx = 600 nm, rho = 1000 kg/m^3,
    mu = 1e-3 Pa.s, BODY_FORCE_ACCEL = 1e6 m/s^2, y periodic, no-slip walls.

Note on Ly (groove direction): the flow is exactly y-invariant (uniform +y body
force, y-uniform geometry, y-periodic BC), so B_yy = mu*qy/(rho*ay) is
INDEPENDENT of Ly.  The DNS is therefore run at a reduced Ly = 20 nm (still a
multiple of every dx: 5/2.5/1.25 nm -> 4/8/16 cells) to make the dx = 1.25 nm
grid (481 x 17 x 59 ~ 4.8e5 nodes) tractable; this gives the identical B_yy as
Ly = 240 nm (verified: 112.437 nm^2 at dx = 5 nm for both Ly).

For each dx it:
  1. runs `--geometry-only` (single process) and measures the ACTUAL discrete
     grid (Nx,Ny,Nz, discrete wall/groove width and discrete liquid height);
  2. runs the DNS to steady state (MPI-parallel) and reads Qy/qy/u_avg/Re/B_yy.

Outputs:
  tmp/grid_convergence_exact65.csv
  tmp/grid_convergence_exact65.png

B_yy uses:  B_yy = mu * qy / (rho * BODY_FORCE_ACCEL)   [m^2]
(no m^3 units, no hEff = cbrt(12*B_yy)).
"""
import os
import subprocess
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import vtk
from vtk.util.numpy_support import vtk_to_numpy

ROOT   = os.path.join(os.path.dirname(__file__), "..")
TMP    = os.path.join(ROOT, "tmp")
VERIFY = os.path.join(ROOT, "verify")
BIN    = os.path.join(ROOT, "grooveDns")
FLOW   = os.path.join(TMP, "flowrate.dat")
MAT_VTI = os.path.join(VERIFY, "vtkData", "data", "material_iT0000000iC00000.vti")

NPROC = int(os.environ.get("NPROC", "1"))    # MPI ranks for the DNS runs (reduced Ly -> single process)

# fixed physical parameters
LX     = 600e-9     # m
LY     = 20e-9      # m (reduced groove-direction length; B_yy is y-invariant, see docstring)
WALL   = 120e-9     # m
GROOVE = 120e-9     # m
HNOM   = 65e-9      # m (liquid height; must equal the discrete height exactly)
RHO    = 1000.0     # kg/m^3
MU     = 1.0e-3     # Pa.s  (rho*nu = 1000 * 1e-6)
AY     = 1.0e6      # m/s^2  (BODY_FORCE_ACCEL)
A_CELL = LX * HNOM              # cell cross-section = 3.9e-14 m^2
D_H    = 2.0 * GROOVE * HNOM / (GROOVE + HNOM)   # hydraulic diameter [m]

# dx -> resolution (dx = PHYS_CHAR_LENGTH / RESOLUTION = 240 nm / RESOLUTION)
DX_LIST = [5.0e-9, 2.5e-9, 1.25e-9]
RES_OF  = {5.0e-9: 48, 2.5e-9: 96, 1.25e-9: 192}

def run(cmd):
    print(f">>> {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit(f"command failed:\n{' '.join(cmd)}\n"
                         f"--- stdout ---\n{p.stdout}\n--- stderr ---\n{p.stderr}")

def load_material():
    r = vtk.vtkXMLImageDataReader()
    r.SetFileName(MAT_VTI)
    r.Update()
    img = r.GetOutput()
    ex = img.GetExtent()
    orig = np.array(img.GetOrigin())
    sp = np.array(img.GetSpacing())
    nx, ny, nz = ex[1]-ex[0]+1, ex[3]-ex[2]+1, ex[5]-ex[4]+1
    arr = vtk_to_numpy(img.GetPointData().GetArray(0))
    mat = arr.reshape(nz, ny, nx).astype(np.int32).transpose(2, 1, 0)  # (x,y,z)
    NM = 1e9
    x = (orig[0] + (ex[0] + np.arange(nx)) * sp[0]) * NM   # nm
    y = (orig[1] + (ex[2] + np.arange(ny)) * sp[1]) * NM
    z = (orig[2] + (ex[4] + np.arange(nz)) * sp[2]) * NM
    return mat, x, y, z, sp[0]  # sp[0] = dx in m

def run_segments(xline, line):
    runs, start = [], 0
    for i in range(1, len(line)):
        if line[i] != line[i-1]:
            runs.append((int(line[i-1]), xline[start], xline[i-1], i - start))
            start = i
    runs.append((int(line[-1]), xline[start], xline[-1], len(line) - start))
    return runs

def measure_geometry(dx):
    """Run --geometry-only and measure the actual discrete grid."""
    run([BIN, "--geometry-only", "--RESOLUTION", str(RES_OF[dx]),
         "--DOMAIN_LY", f"{LY:.8e}"])
    mat, x, y, z, dx_actual = load_material()

    iy = int(np.argmin(np.abs(y - LY*1e9/2)))          # mid-y
    ix_g = int(np.argmin(np.abs(x - 180.0)))           # mid of groove 1
    zf = z[mat[ix_g, iy, :] == 1]                       # fluid z at groove center
    height = zf.max() - zf.min()                        # discrete liquid height [nm]
    iz_mid = int(np.argmin(np.abs(z - (zf.min() + height/2))))

    core = (x >= -0.01) & (x <= 600.01)
    line = mat[:, iy, iz_mid][core]
    xline = x[core]
    runs = run_segments(xline, line)

    walls, grooves = [], []
    for i, (m, sx, ex, nn) in enumerate(runs):
        end = runs[i+1][1] if i+1 < len(runs) else 600.0
        w = end - sx
        if m == 2:
            walls.append((w, nn))
        elif m == 1:
            grooves.append((w, nn))

    wall_w = np.mean([w for w, _ in walls])
    groove_w = np.mean([w for w, _ in grooves])
    n_wall = np.mean([nn for _, nn in walls])
    n_groove = np.mean([nn for _, nn in grooves])

    # core mesh dimensions (drop the VTK overlap halo by cropping to the domain)
    dx_nm = dx * 1e9
    core_x = (x >= -1e-6) & (x <= 600.0 + 1e-6)
    core_y = (y >= -1e-6) & (y <= LY*1e9 + 1e-6)
    core_z = (z >= -3*dx_nm - 1e-6) & (z <= 65.0 + 3*dx_nm + 1e-6)
    Nx, Ny, Nz = int(core_x.sum()), int(core_y.sum()), int(core_z.sum())

    return dict(Nx=Nx, Ny=Ny, Nz=Nz,
                dx_actual=dx_actual, wall_nm=wall_w, groove_nm=groove_w,
                height_nm=height, n_wall=n_wall, n_groove=n_groove,
                nz_fluid=int(np.sum(mat[ix_g, iy, :] == 1)))

def run_dns(dx):
    run(["mpirun", "-np", str(NPROC), BIN,
         "--RESOLUTION", str(RES_OF[dx]), "--BODY_FORCE_ACCEL", "1e6",
         "--DOMAIN_LY", f"{LY:.8e}"])
    d = np.loadtxt(FLOW, comments="#")
    # columns: iT  t  Qy  qy  u_avg  u_max  Byy
    return dict(iT=int(d[-1, 0]), Qy=d[-1, 2], qy=d[-1, 3],
                u_avg=d[-1, 4], u_max=d[-1, 5], Byy=d[-1, 6])

def main():
    os.makedirs(TMP, exist_ok=True)
    rows = []
    for dx in DX_LIST:
        g = measure_geometry(dx)
        f = run_dns(dx)

        qy_check = f["Qy"] / A_CELL
        byy_check = MU * f["qy"] / (RHO * AY)
        Re = RHO * f["u_avg"] * D_H / MU
        qy_ok = np.isclose(f["qy"], qy_check, rtol=1e-9)
        byy_ok = np.isclose(f["Byy"], byy_check, rtol=1e-9)
        h_ok = np.isclose(g["height_nm"], 65.0, atol=1e-6)

        rows.append(dict(dx=dx, **g, **f, Re=Re,
                         qy_ok=qy_ok, byy_ok=byy_ok, h_ok=h_ok))

        print(f"\ndx = {dx*1e9:.2f} nm  (Nx,Ny,Nz) = ({g['Nx']},{g['Ny']},{g['Nz']})")
        print(f"  discrete wall = {g['wall_nm']:.3f} nm ({g['n_wall']:.0f} nodes), "
              f"groove = {g['groove_nm']:.3f} nm ({g['n_groove']:.0f} nodes), "
              f"height = {g['height_nm']:.3f} nm ({g['nz_fluid']} nodes)  [exact65: {h_ok}]")
        print(f"  Qy={f['Qy']:.6e} m^3/s  qy={f['qy']:.6e} m/s  "
              f"u_avg={f['u_avg']:.6e} m/s  Re={Re:.3e}")
        print(f"  B_yy={f['Byy']:.6e} m^2 = {f['Byy']*1e18:.4f} nm^2")
        print(f"  qy==Qy/A_cell: {qy_ok}   B_yy==mu*qy/(rho*ay): {byy_ok}")

    # ---- CSV ----
    csv_path = os.path.join(TMP, "grid_convergence_exact65.csv")
    with open(csv_path, "w") as fh:
        fh.write("dx_m,Nx,Ny,Nz,wall_width_nm,groove_width_nm,height_nm,"
                 "Qy_m3_per_s,qy_m_per_s,u_y_fluid_average_m_per_s,Re,"
                 "B_yy_m2,B_yy_nm2\n")
        for r in rows:
            fh.write(f"{r['dx']:.3e},{r['Nx']},{r['Ny']},{r['Nz']},"
                     f"{r['wall_nm']:.3f},{r['groove_nm']:.3f},{r['height_nm']:.3f},"
                     f"{r['Qy']:.8e},{r['qy']:.8e},{r['u_avg']:.8e},{r['Re']:.6e},"
                     f"{r['Byy']:.8e},{r['Byy']*1e18:.6f}\n")
    print(f"\nsaved {csv_path}")

    # ---- relative errors vs finest grid ----
    dxv = np.array([r["dx"] for r in rows]) * 1e9       # nm
    byy = np.array([r["Byy"] for r in rows]) * 1e18     # nm^2
    fine = byy[-1]                                       # dx = 1.25 nm
    err = np.abs(byy - fine) / np.abs(fine) * 100.0

    print("\n" + "=" * 64)
    print("Grid-convergence (B_yy vs dx), reference = finest grid dx=1.25 nm")
    for i, r in enumerate(rows):
        tag = "  <-- finest" if i == len(rows)-1 else ""
        print(f"  dx={dxv[i]:5.2f} nm  B_yy={byy[i]:10.4f} nm^2  "
              f"error={err[i]:7.3f} %{tag}")
    print(f"  coarse(dx=5.0)    vs fine(dx=1.25): {err[0]:.3f} %")
    print(f"  medium(dx=2.5)    vs fine(dx=1.25): {err[1]:.3f} %")
    print(f"  B_yy stabilizes as dx -> 0: {bool(err[0] > err[1] and err[1] > 0)}")
    print("=" * 64)

    # ---- plot ----
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3.8))

    ax1.semilogx(dxv, byy, "o-", color="#2563eb", lw=1.5, ms=7)
    ax1.axhline(fine, color="#9ca3af", ls="--", lw=1.0,
                label=f"finest (dx=1.25 nm) = {fine:.3f} nm$^2$")
    ax1.set_xlabel("dx [nm]")
    ax1.set_ylabel(r"$B_{yy}$ [nm$^2$]")
    ax1.set_title(r"$B_{yy}$ vs grid spacing")
    ax1.grid(True, which="both", lw=0.4, alpha=0.5)
    ax1.legend(frameon=False, fontsize=8)
    ax1.invert_xaxis()

    ax2.loglog(dxv, err, "s-", color="#059669", lw=1.5, ms=7)
    ax2.set_xlabel("dx [nm]")
    ax2.set_ylabel(r"relative error $|B_{yy}-B_{\rm fine}|/B_{\rm fine}$ [%]")
    ax2.set_title("grid error vs spacing (finest-grid reference)")
    ax2.grid(True, which="both", lw=0.4, alpha=0.5)
    ax2.invert_xaxis()

    fig.suptitle("SIM-EC1XT240 grid convergence (exact-65 nm height)  "
                 f"(coarse error {err[0]:.2f}%, medium error {err[1]:.2f}%)", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    png_path = os.path.join(TMP, "grid_convergence_exact65.png")
    fig.savefig(png_path, dpi=150)
    plt.close(fig)
    print(f"saved {png_path}")

    # ---- hard gate: every row must have height exactly 65 nm ----
    if all(r["h_ok"] for r in rows):
        print("\nPASS: all three rows have discrete liquid height = 65.000 nm")
    else:
        print("\nFAIL: not all rows have height = 65.000 nm — do NOT report results.")

if __name__ == "__main__":
    main()
