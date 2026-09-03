#!/usr/bin/env python3
"""Body-force linearity sweep for the SIM-EC1XT240 straight-groove DNS.

Runs the case at three prescribed accelerations a_y = 1e6, 1e7, 1e8 m/s^2,
keeping geometry / mesh / viscosity / boundary conditions unchanged, and checks
whether the equivalent conductance B_yy stays constant (=> B_yy is a linear
parameter).  Outputs:

  tmp/force_linearity.csv   one row per a_y
  tmp/force_linearity.png   qy vs a_y (linearity) + B_yy vs a_y (constancy)

Definitions (matching case.h):
  qy   = Qy / A_cell , A_cell = Lx * Hfluid                 [m/s]
  B_yy = mu * qy / (rho * a_y)                              [m^2]
  Re   = rho * u_y_fluid_average * D_h / mu , D_h = 2*g*H/(g+H)  [-]
"""
import os
import subprocess
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.join(os.path.dirname(__file__), "..")
TMP = os.path.join(ROOT, "tmp")
BIN = os.path.join(ROOT, "grooveDns")
FLOW = os.path.join(TMP, "flowrate.dat")

# physical constants of the case
LX     = 600e-9       # m
HFLUID = 65e-9        # m
GROOVE = 120e-9       # m
A_CELL = LX * HFLUID              # 3.9e-14 m^2
RHO    = 1000.0                   # kg/m^3
NU     = 1.0e-6                   # m^2/s
MU     = RHO * NU                 # 1e-3 Pa.s
D_H    = 2.0 * GROOVE * HFLUID / (GROOVE + HFLUID)   # hydraulic diameter [m]

AY_LIST = [1e6, 1e7, 1e8]         # m/s^2

def run_case(ay):
    """Run one DNS at acceleration ay; return dict of converged quantities."""
    tag = f"{ay:.0e}".replace("+0", "").replace("e", "e")
    cmd = [BIN, "--BODY_FORCE_ACCEL", f"{ay:g}"]
    print(f"\n>>> running {cmd}")
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"grooveDns failed for ay={ay:g}:\n"
                         f"--- stdout ---\n{proc.stdout}\n"
                         f"--- stderr ---\n{proc.stderr}")

    d = np.loadtxt(FLOW, comments="#")
    # columns: iT  t  Qy  qy  u_avg  u_max  Byy
    iT, t, Qy, qy, u_avg, u_max, Byy = d[-1, 0], d[-1, 1], d[-1, 2], d[-1, 3], d[-1, 4], d[-1, 5], d[-1, 6]

    # preserve this case's full time series
    dst = os.path.join(TMP, f"flowrate_ay{ay:g}.dat".replace("+", ""))
    with open(FLOW) as f, open(dst, "w") as g:
        g.write(f.read())

    # derived + verification
    qy_check = Qy / A_CELL
    Byy_check = MU * qy / (RHO * ay)
    Re = RHO * u_avg * D_H / MU

    qy_ok = np.isclose(qy, qy_check, rtol=1e-9, atol=0.0)
    byy_ok = np.isclose(Byy, Byy_check, rtol=1e-9, atol=0.0)

    print(f"  converged at iT={int(iT):d}  t={t:.3e} s")
    print(f"    Qy={Qy:.6e} m^3/s   qy={qy:.6e} m/s   u_avg={u_avg:.6e} m/s")
    print(f"    Re={Re:.3e}   B_yy={Byy:.6e} m^2 = {Byy*1e18:.4f} nm^2")
    print(f"    qy==Qy/A_cell: {qy_ok}   B_yy==mu*qy/(rho*ay): {byy_ok}")

    return dict(ay=ay, Qy=Qy, qy=qy, u_avg=u_avg, u_max=u_max,
                Re=Re, Byy=Byy, Byy_nm2=Byy * 1e18,
                qy_ok=qy_ok, byy_ok=byy_ok)

def main():
    os.makedirs(TMP, exist_ok=True)
    rows = [run_case(ay) for ay in AY_LIST]

    # ---- write CSV ----
    csv_path = os.path.join(TMP, "force_linearity.csv")
    with open(csv_path, "w") as f:
        f.write("ay_m_per_s2,Qy_m3_per_s,qy_m_per_s,"
                "u_y_fluid_average_m_per_s,u_y_fluid_max_m_per_s,Re,"
                "B_yy_m2,B_yy_nm2\n")
        for r in rows:
            f.write(f"{r['ay']:.6e},{r['Qy']:.8e},{r['qy']:.8e},"
                    f"{r['u_avg']:.8e},{r['u_max']:.8e},{r['Re']:.6e},"
                    f"{r['Byy']:.8e},{r['Byy_nm2']:.6f}\n")
    print(f"\nsaved {csv_path}")

    # ---- constancy check ----
    ay   = np.array([r["ay"] for r in rows])
    qy   = np.array([r["qy"] for r in rows])
    byy  = np.array([r["Byy"] for r in rows])
    Re   = np.array([r["Re"] for r in rows])

    bmin, bmax, bmean = byy.min(), byy.max(), byy.mean()
    spread = (bmax - bmin) / bmean * 100.0        # % of mean
    ratio  = bmax / bmin
    print("\n" + "=" * 64)
    print("B_yy constancy across a_y = {1e6, 1e7, 1e8} m/s^2")
    print(f"  B_yy [nm^2] = {[f'{b:.4f}' for b in byy*1e18]}")
    print(f"  spread (max-min)/mean = {spread:.4f} %")
    print(f"  max/min ratio         = {ratio:.6f}")
    print(f"  Re range              = [{Re.min():.3e}, {Re.max():.3e}]")
    linear = spread < 5.0
    print(f"  LINEAR (spread < 5 %) : {linear}")
    print("=" * 64)

    # ---- plot ----
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3.8))

    ax1.loglog(ay, qy, "o-", color="#2563eb", lw=1.5, ms=6)
    # reference slope-1 line anchored at the lowest point
    ax1.loglog(ay, qy[0] * (ay / ay[0]), "--", color="#9ca3af", lw=1.0,
               label="slope 1 (linear)")
    ax1.set_xlabel(r"$a_y$ [m/s$^2$]")
    ax1.set_ylabel(r"$q_y = Q_y/A_{\rm cell}$ [m/s]")
    ax1.set_title("superficial velocity vs body force")
    ax1.grid(True, which="both", lw=0.4, alpha=0.5)
    ax1.legend(frameon=False, fontsize=8)

    ax2.semilogx(ay, byy * 1e18, "o-", color="#059669", lw=1.5, ms=6)
    ax2.axhline(byy.mean() * 1e18, color="#9ca3af", ls="--", lw=1.0,
                label=f"mean = {byy.mean()*1e18:.3f} nm$^2$")
    ax2.set_xlabel(r"$a_y$ [m/s$^2$]")
    ax2.set_ylabel(r"$B_{yy}$ [nm$^2$]")
    ax2.set_title(r"$B_{yy}$ constancy (linear-equivalence check)")
    ax2.grid(True, which="both", lw=0.4, alpha=0.5)
    ax2.legend(frameon=False, fontsize=8)

    fig.suptitle(f"Body-force linearity — B_yy spread = {spread:.3f} %  "
                 f"({'LINEAR' if linear else 'NONLINEAR'})", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    png_path = os.path.join(TMP, "force_linearity.png")
    fig.savefig(png_path, dpi=150)
    plt.close(fig)
    print(f"saved {png_path}")

    # ---- verdict ----
    if linear:
        print("\nCONCLUSION: B_yy spread < 5 %  =>  B_yy is a valid linear "
              "equivalent conductance parameter.")
    else:
        print("\nCONCLUSION: B_yy spread >= 5 %  =>  inertial effects matter. "
              "Use the lowest-Re case (a_y = 1e6 m/s^2) as authoritative and "
              "note the high-force deviation in README.")

if __name__ == "__main__":
    main()
