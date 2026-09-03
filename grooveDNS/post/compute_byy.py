#!/usr/bin/env python3
"""Convergence + B_yy summary for the SIM-EC1XT240 straight-groove DNS.

Reads tmp/flowrate.dat (time series written by the case) and:
  - checks the superficial velocity qy = Qy / (Lx * Hfluid)  [m/s]
  - checks the permeability  B_yy = mu * qy / (rho * ay)      [m^2]
  - plots B_yy vs time (convergence)  ->  tmp/byy_convergence.png
  - prints the final B_yy in m^2 and nm^2

Physical definitions (matching case.h):
  Lx = 600 nm, Hfluid = 65 nm, A_cell = Lx * Hfluid
  qy  = Qy / A_cell                          (superficial / Darcy velocity, m/s)
  dpdy = -rho * ay,  ay = prescribed BODY_FORCE_ACCEL (physical acceleration, m/s^2)
  B_yy = mu * qy / (rho * ay) = -mu * qy / dpdy   [m^2]
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.join(os.path.dirname(__file__), "..")
TMP = os.path.join(ROOT, "tmp")
FLOW = os.path.join(TMP, "flowrate.dat")

# physical constants of the case
LX      = 600e-9     # m
HFLUID  = 65e-9      # m
A_CELL  = LX * HFLUID          # 3.9e-14 m^2
RHO     = 1000.0               # kg/m^3
NU      = 1.0e-6               # m^2/s
MU      = RHO * NU             # 1e-3 Pa.s

def read_flow():
    d = np.loadtxt(FLOW, comments="#")
    # columns: iT  t  Qy  qy  u_avg  u_max  Byy
    iT, t, Qy, qy, u_avg, u_max, Byy = d[:, 0], d[:, 1], d[:, 2], d[:, 3], d[:, 4], d[:, 5], d[:, 6]
    return iT, t, Qy, qy, u_avg, u_max, Byy

def main():
    iT, t, Qy, qy, u_avg, u_max, Byy = read_flow()

    # converged = last recorded state
    Qy_f, qy_f, Byy_f = Qy[-1], qy[-1], Byy[-1]

    # ---- verification: qy must equal Qy / A_cell ----
    qy_expected = Qy_f / A_CELL
    print("=" * 64)
    print("SIM-EC1XT240 straight-groove DNS — B_yy summary")
    print("-" * 64)
    print(f"  Qy                = {Qy_f:.6e}  m^3/s")
    print(f"  A_cell = Lx*Hfluid = {A_CELL:.3e}  m^2  (600 nm x 65 nm)")
    print(f"  qy (from file)    = {qy_f:.6e}  m/s")
    print(f"  qy = Qy/A_cell    = {qy_expected:.6e}  m/s")
    print(f"  qy match          = {np.isclose(qy_f, qy_expected, rtol=1e-9)}")
    print(f"  u_y_fluid_average = {u_avg[-1]:.6e}  m/s")
    print(f"  u_y_fluid_max     = {u_max[-1]:.6e}  m/s")
    print(f"  B_yy (from file)  = {Byy_f:.6e}  m^2")
    print(f"  B_yy              = {Byy_f*1e18:.6f}  nm^2")
    # convergence: relative change of B_yy over the last 10% of the run
    n = max(10, len(Byy) // 10)
    drift = abs(Byy[-1] - Byy[-n]) / abs(Byy[-1])
    print(f"  B_yy rel. drift (last {n} steps) = {drift:.3e}")
    print("=" * 64)

    # ---- B_yy vs time (convergence) ----
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.plot(t * 1e9, Byy * 1e18, color="#2563eb", lw=1.5)
    ax.set_xlabel("physical time t [ns]")
    ax.set_ylabel(r"$B_{yy}$ [nm$^2$]")
    ax.set_title(r"$B_{yy}$ convergence (superficial-velocity Darcy definition)")
    ax.grid(True, lw=0.4, alpha=0.5)
    fig.tight_layout()
    fig.savefig(os.path.join(TMP, "byy_convergence.png"), dpi=150)
    plt.close(fig)
    print("saved byy_convergence.png")

    # ---- qy vs time (secondary check) ----
    fig, ax = plt.subplots(figsize=(7, 3.0))
    ax.plot(t * 1e9, qy, color="#059669", lw=1.5)
    ax.set_xlabel("physical time t [ns]")
    ax.set_ylabel(r"$q_y = Q_y/A_{\rm cell}$ [m/s]")
    ax.set_title("Superficial (Darcy) velocity $q_y$ convergence")
    ax.grid(True, lw=0.4, alpha=0.5)
    fig.tight_layout()
    fig.savefig(os.path.join(TMP, "qy_convergence.png"), dpi=150)
    plt.close(fig)
    print("saved qy_convergence.png")

    # ---- write a compact summary file ----
    with open(os.path.join(TMP, "byy_summary.txt"), "w") as f:
        f.write("SIM-EC1XT240 straight-groove DNS — B_yy summary\n")
        f.write(f"Qy_m3_per_s            = {Qy_f:.8e}\n")
        f.write(f"qy_cell_m_per_s        = {qy_f:.8e}\n")
        f.write(f"u_y_fluid_average_m/s  = {u_avg[-1]:.8e}\n")
        f.write(f"u_y_fluid_max_m/s      = {u_max[-1]:.8e}\n")
        f.write(f"B_yy_m2                = {Byy_f:.8e}\n")
        f.write(f"B_yy_nm2               = {Byy_f*1e18:.6f}\n")
    print(f"saved byy_summary.txt")

if __name__ == "__main__":
    main()
