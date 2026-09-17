#!/usr/bin/env python3
"""Static exact-geometry and physical-similarity audit for G2 Step 3."""

from __future__ import annotations

import argparse
import csv
import math
from fractions import Fraction
from pathlib import Path


CASE_ROOT = Path(__file__).resolve().parents[1]
TAU = 1.0
NU_PHYS = 1.0e-6
RHO_PHYS = 1000.0
A_PHYS = 1.0e5
GRIDS_NM = (Fraction(5), Fraction(5, 2), Fraction(5, 4))
DIMENSIONS_NM = {
    "period_nodes": Fraction(240),
    "mesa_nodes": Fraction(60),
    "groove_nodes": Fraction(120),
    "depth_nodes": Fraction(100),
    "gap_nodes": Fraction(75),
}


def audit_rows() -> list[dict[str, object]]:
    rows = []
    for dx_nm in GRIDS_NM:
        counts = {name: value / dx_nm for name, value in DIMENSIONS_NM.items()}
        exact = all(value.denominator == 1 for value in counts.values())
        if not exact:
            raise RuntimeError(f"dx={float(dx_nm)} nm does not exactly represent all nominal dimensions")
        dx = float(dx_nm) * 1.0e-9
        dt = (TAU - 0.5) * dx * dx / (3.0 * NU_PHYS)
        nu_lattice = NU_PHYS * dt / (dx * dx)
        tau_reconstructed = 0.5 + 3.0 * NU_PHYS * dt / (dx * dx)
        a_lattice = A_PHYS * dt * dt / dx
        velocity_conversion = dx / dt
        similarity_pass = (
            math.isclose(tau_reconstructed, TAU, rel_tol=0.0, abs_tol=1.0e-14)
            and math.isclose(nu_lattice, 1.0 / 6.0, rel_tol=0.0, abs_tol=1.0e-14)
        )
        rows.append({
            "dx_nm": float(dx_nm),
            "dx_m": dx,
            "dt_s": dt,
            "tau": TAU,
            "tau_reconstructed": tau_reconstructed,
            "rho_phys_kg_m3": RHO_PHYS,
            "nu_phys_m2_s": NU_PHYS,
            "nu_lattice": nu_lattice,
            "a_phys_m_s2": A_PHYS,
            "a_lattice": a_lattice,
            "velocity_conversion_m_s_per_lattice": velocity_conversion,
            **{name: int(value) for name, value in counts.items()},
            "geometry_exact": exact,
            "similarity_PASS": similarity_pass,
        })
    return rows


def write_outputs(rows: list[dict[str, object]]) -> None:
    csv_path = CASE_ROOT / "grid_similarity_audit.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    report = [
        "# G2 Step 3 grid preflight",
        "",
        "Status: **PASS**",
        "",
        "All nominal dimensions are represented by exact integer cell counts. "
        "Physical density, viscosity, acceleration, and tau are fixed; dt and "
        "lattice acceleration are recomputed per grid.",
        "",
        "| dx (nm) | P | mesa | groove | D | h | dt (s) | nu_lattice | a_lattice | dx/dt (m/s) |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        report.append(
            f"| {row['dx_nm']:.2f} | {row['period_nodes']} | {row['mesa_nodes']} | "
            f"{row['groove_nodes']} | {row['depth_nodes']} | {row['gap_nodes']} | "
            f"{row['dt_s']:.16e} | {row['nu_lattice']:.16e} | "
            f"{row['a_lattice']:.16e} | {row['velocity_conversion_m_s_per_lattice']:.8g} |"
        )
    report.extend([
        "",
        "Identity checked: `tau = 0.5 + 3 nu_phys dt / dx^2 = 1.0` on every grid.",
        "",
    ])
    (CASE_ROOT / "GRID_PREFLIGHT.md").write_text("\n".join(report))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    rows = audit_rows()
    if not all(bool(row["geometry_exact"]) and bool(row["similarity_PASS"]) for row in rows):
        raise SystemExit(3)
    if args.write:
        write_outputs(rows)
    for row in rows:
        print(
            f"dx_nm={row['dx_nm']:.2f} dt_s={row['dt_s']:.16e} "
            f"a_lattice={row['a_lattice']:.16e} exact={row['geometry_exact']} "
            f"similarity_PASS={row['similarity_PASS']}"
        )


if __name__ == "__main__":
    main()
