#!/usr/bin/env python3
"""Minimal 2-D FEM pilot for SIM240 Paper 1.

Solves the same non-dimensional P/T problems defined in PROTOCOL.md.
No OpenFOAM invocation, no fitting, no automatic expansion beyond one named case.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
import scipy
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import skfem
from numpy.polynomial.legendre import leggauss
from skfem import (Basis, BilinearForm, ElementTriP1, ElementTriP2,
                   Functional, LinearForm, MeshTri, asm)
from skfem.helpers import dot, grad

ROOT = Path(__file__).resolve().parent
P_NM = 240.0
W_NM = 120.0
L0_M = 1e-9
NU = 1e-6
ACCEL = 1e5
U0 = ACCEL * L0_M**2 / NU
FVM_REF = {
    "h75_d100_P": 9.755622669730348e-23,
    "h75_d100_T": 4.340041663047474e-23,
    "h50_d120_P": 6.838617932100589e-23,
    "h125_d120_P": 2.7840399124225664e-22,
}


@BilinearForm
def laplace(u, v, w):
    return dot(grad(u), grad(v))


@BilinearForm
def divergence_x(u, v, w):
    return grad(u)[0] * v


@BilinearForm
def divergence_z(u, v, w):
    return grad(u)[1] * v


@LinearForm
def force_x(v, w):
    return v


@LinearForm
def unit_integral(v, w):
    return v


@Functional
def area_functional(w):
    return 1.0


@Functional
def main_integral(w):
    return w.u


@Functional
def grad_square(w):
    return dot(grad(w.u), grad(w.u))


@Functional
def flat_error_square(w):
    z = w.x[1]
    exact = z * (w.H - z) / 2.0
    return (w.u - exact) ** 2


@Functional
def flat_exact_square(w):
    z = w.x[1]
    return (z * (w.H - z) / 2.0) ** 2


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def axis(start: float, stop: float, dx: float) -> np.ndarray:
    n = int(round((stop - start) / dx))
    if not math.isclose((stop - start) / dx, n, rel_tol=0, abs_tol=1e-10):
        raise ValueError(f"grid {dx} does not divide interval {start},{stop}")
    return np.linspace(start, stop, n + 1)


def build_mesh(h: float, d: float, dx: float):
    # A common z axis preserves conformity at the groove shoulder.
    z = axis(0.0, h + d, dx)
    x = np.concatenate((axis(0.0, W_NM, dx), axis(W_NM, P_NM, dx)[1:]))
    base = MeshTri.init_tensor(x, z)
    if d > 0:
        centroids = base.p[:, base.t].mean(axis=1)
        solid = centroids[0] > W_NM
        solid &= centroids[1] < d
        base = base.remove_elements(np.flatnonzero(solid))
    facets = base.boundary_facets()
    centers = base.p[:, base.facets].mean(axis=1)[:, facets]
    left = facets[(np.abs(centers[0]) < 1e-9) & (centers[1] > d + 1e-9)]
    right = facets[(np.abs(centers[0] - P_NM) < 1e-9) & (centers[1] > d + 1e-9)]
    periodic = set(left.tolist()) | set(right.tolist())
    walls = np.array([f for f in facets if f not in periodic], dtype=int)
    mesh = base.with_boundaries({
        "periodic_left": left,
        "periodic_right": right,
        "walls": walls,
    })
    return mesh, x, z


def periodic_transform(basis: Basis, left: str, right: str):
    """Return sparse full<-reduced map and reduced index of every full DOF."""
    n = basis.N
    parent = np.arange(n, dtype=int)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    dl = np.sort(basis.get_dofs(left).all())
    dr = np.sort(basis.get_dofs(right).all())
    loc = basis.doflocs
    left_order = sorted(dl, key=lambda i: loc[1, i])
    right_order = sorted(dr, key=lambda i: loc[1, i])
    if len(left_order) != len(right_order) or not left_order:
        raise ValueError("periodic DOF counts differ or are empty")
    zl = np.array([loc[1, i] for i in left_order])
    zr = np.array([loc[1, i] for i in right_order])
    if not np.allclose(zl, zr, rtol=0, atol=1e-9):
        raise ValueError("periodic DOF heights do not match")
    for a, b in zip(left_order, right_order):
        if abs(loc[0, a]) > 1e-8 or abs(loc[0, b] - P_NM) > 1e-8:
            raise ValueError("unexpected periodic DOF location")
        union(a, b)
    roots = np.array([find(i) for i in range(n)])
    unique, reduced = np.unique(roots, return_inverse=True)
    transform = sp.coo_matrix((np.ones(n), (np.arange(n), reduced)),
                              shape=(n, len(unique))).tocsr()
    return transform, reduced, len(left_order)


def direct_solve(matrix, rhs):
    solution = spla.spsolve(matrix.tocsc(), rhs, permc_spec="MMD_AT_PLUS_A")
    residual = np.linalg.norm(rhs - matrix @ solution) / max(np.linalg.norm(rhs), 1e-300)
    if not np.all(np.isfinite(solution)) or not math.isfinite(residual):
        raise ValueError("nonfinite direct solution or residual")
    return solution, float(residual)


def flat_metrics(basis, solution, h):
    exact = h**3 * P_NM / 12.0  # dimensionless integral
    interp = basis.interpolate(solution)
    integral = float(asm(main_integral, basis, u=interp))
    err2 = float(asm(flat_error_square, basis, u=interp, H=h))
    ref2 = float(asm(flat_exact_square, basis, u=interp, H=h))
    return {
        "flat_integral_error_percent": abs(integral / exact - 1) * 100,
        "flat_profile_L2_percent": math.sqrt(err2 / ref2) * 100,
    }


def section_fluxes(basis, ux, xgrid, zgrid, h, d):
    interpolate = basis.interpolator(ux)
    # Avoid periodic ends and the step plane; 4-point Gauss is exact for P2
    # restricted to each straight grid interval.
    stations = P_NM * np.array([0.07, 0.13, 0.21, 0.31, 0.43,
                                0.57, 0.69, 0.79, 0.87, 0.93])
    nodes, weights = leggauss(4)
    fluxes = []
    for x0 in stations:
        zlo = 0.0 if x0 < W_NM else d
        valid = np.flatnonzero((zgrid[:-1] >= zlo - 1e-10) &
                               (zgrid[1:] <= h + d + 1e-10) &
                               (zgrid[1:] > zlo + 1e-10))
        q = 0.0
        for i in valid:
            a, b = zgrid[i], zgrid[i + 1]
            zz = (a + b) / 2 + (b - a) / 2 * nodes
            pts = np.vstack((np.full_like(zz, x0), zz))
            vals = np.asarray(interpolate(pts)).reshape(-1)
            q += (b - a) / 2 * float(weights @ vals)
        fluxes.append(q)
    fluxes = np.array(fluxes)
    mean = float(np.mean(fluxes))
    return {
        "section_count": len(fluxes),
        "section_fluxes_dimensionless": fluxes.tolist(),
        "section_flux_mean_dimensionless": mean,
        "section_flux_spread_percent": float((fluxes.max() - fluxes.min()) / mean * 100),
    }


def run_level(case: str, h: float, d: float, direction: str, dx: float,
              overwrite: bool = False):
    outdir = ROOT / "results" / case
    outdir.mkdir(parents=True, exist_ok=True)
    tag = f"dx_{dx:g}nm"
    json_path = outdir / f"{tag}.json"
    field_path = outdir / f"{tag}_fields.npz"
    if json_path.exists() and not overwrite:
        raise FileExistsError(f"refusing overwrite: {json_path}")
    mesh, xgrid, zgrid = build_mesh(h, d, dx)
    basis2 = Basis(mesh, ElementTriP2(), intorder=6)
    area = float(asm(area_functional, basis2))
    exact_area = P_NM * (h + d) - (P_NM - W_NM) * d
    area_error = abs(area / exact_area - 1)
    if area_error > 1e-10:
        raise ValueError(f"fluid area error {area_error}")

    if direction == "P":
        matrix = asm(laplace, basis2)
        rhs = asm(force_x, basis2)
        transform, reduced, pairs = periodic_transform(
            basis2, "periodic_left", "periodic_right")
        matrix_r = transform.T @ matrix @ transform
        rhs_r = transform.T @ rhs
        wall_full = basis2.get_dofs("walls").all()
        wall_reduced = np.unique(reduced[wall_full])
        free = np.ones(matrix_r.shape[0], dtype=bool)
        free[wall_reduced] = False
        solution_r, residual = direct_solve(matrix_r[free][:, free], rhs_r[free])
        full_r = np.zeros(matrix_r.shape[0])
        full_r[free] = solution_r
        solution = transform @ full_r
        interp = basis2.interpolate(solution)
        integral = float(asm(main_integral, basis2, u=interp))
        grad_integral = float(asm(grad_square, basis2, u=interp))
        pressure_mean = 0.0
        ux, uz, pressure = solution, np.zeros_like(solution), np.array([])
        ndof = matrix_r.shape[0]
        section = {"section_count": 0, "section_flux_spread_percent": 0.0,
                   "section_vs_volume_percent": 0.0}
    elif direction == "T":
        basis1 = Basis(mesh, ElementTriP1(), intorder=6)
        stiff = asm(laplace, basis2)
        bx = asm(divergence_x, basis2, basis1)
        bz = asm(divergence_z, basis2, basis1)
        load = asm(force_x, basis2)
        mean_vector = asm(unit_integral, basis1)
        zero_uu = sp.csr_matrix((basis2.N, basis2.N))
        zero_pp = sp.csr_matrix((basis1.N, basis1.N))
        full_matrix = sp.bmat([
            [stiff, zero_uu, -bx.T, None],
            [zero_uu, stiff, -bz.T, None],
            [bx, bz, zero_pp, mean_vector.reshape(-1, 1)],
            [None, None, mean_vector.reshape(1, -1), sp.csr_matrix((1, 1))],
        ], format="csr")
        full_rhs = np.concatenate((load, np.zeros(basis2.N),
                                   np.zeros(basis1.N), [0.0]))
        t2, r2, pairs2 = periodic_transform(basis2, "periodic_left", "periodic_right")
        t1, r1, pairs1 = periodic_transform(basis1, "periodic_left", "periodic_right")
        transform = sp.block_diag((t2, t2, t1, sp.csr_matrix([[1.0]])), format="csr")
        matrix_r = transform.T @ full_matrix @ transform
        rhs_r = transform.T @ full_rhs
        wall_full = basis2.get_dofs("walls").all()
        wall_x = np.unique(r2[wall_full])
        wall_z = t2.shape[1] + wall_x
        free = np.ones(matrix_r.shape[0], dtype=bool)
        free[np.concatenate((wall_x, wall_z))] = False
        solution_r, residual = direct_solve(matrix_r[free][:, free], rhs_r[free])
        full_r = np.zeros(matrix_r.shape[0])
        full_r[free] = solution_r
        full_solution = transform @ full_r
        ux = full_solution[:basis2.N]
        uz = full_solution[basis2.N:2 * basis2.N]
        pressure = full_solution[2 * basis2.N:2 * basis2.N + basis1.N]
        interp_x = basis2.interpolate(ux)
        interp_z = basis2.interpolate(uz)
        integral = float(asm(main_integral, basis2, u=interp_x))
        grad_integral = float(asm(grad_square, basis2, u=interp_x) +
                              asm(grad_square, basis2, u=interp_z))
        pressure_mean = float(asm(main_integral, basis1, u=basis1.interpolate(pressure)))
        ndof = matrix_r.shape[0]
        pairs = pairs2
        section = section_fluxes(basis2, ux, xgrid, zgrid, h, d)
        section["section_vs_volume_percent"] = abs(
            section["section_flux_mean_dimensionless"] / (integral / P_NM) - 1) * 100
    else:
        raise ValueError(direction)

    K = 1e-27 / P_NM * integral
    result = {
        "case_id": case,
        "status": "PILOT_OUTPUT",
        "h_nm": h,
        "d_nm": d,
        "w_nm": W_NM,
        "P_nm": P_NM,
        "direction": direction,
        "dx_nm": dx,
        "mesh_triangles": int(mesh.t.shape[1]),
        "mesh_vertices": int(mesh.p.shape[1]),
        "p2_dofs": int(basis2.N),
        "matrix_dofs_before_wall_elimination": int(ndof),
        "periodic_paired_dofs_p2": int(pairs),
        "area_m2_dimensionless": area,
        "area_exact_dimensionless": exact_area,
        "area_relative_error": area_error,
        "direct_relative_residual": residual,
        "integral_main_dimensionless": integral,
        "K_m3": K,
        "gradient_integral_dimensionless": grad_integral,
        "power_balance_percent": abs(grad_integral / integral - 1) * 100,
        "pressure_mean_integral": pressure_mean,
        "max_abs_Uz": float(np.max(np.abs(uz))) if len(uz) else 0.0,
        "nu_m2_s": NU,
        "acceleration_m_s2": ACCEL,
        "U0_m_s": U0,
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit_fem": skfem.__version__,
        },
        **section,
    }
    if d == 0:
        exact_K = (h * 1e-9) ** 3 / 12
        result.update(flat_metrics(basis2, ux, h))
        result["K_exact_m3"] = exact_K
        result["flat_K_error_percent"] = abs(K / exact_K - 1) * 100
    if case in FVM_REF:
        result["FVM_reference_m3"] = FVM_REF[case]
        result["FVM_difference_percent"] = abs(K / FVM_REF[case] - 1) * 100
    np.savez_compressed(field_path, p=mesh.p, t=mesh.t, ux=ux, uz=uz,
                        pressure=pressure, h=np.array(h), d=np.array(d),
                        direction=np.array(direction), dx_nm=np.array(dx))
    result["field_file"] = field_path.name
    result["field_sha256"] = sha256(field_path)
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    result["json_file"] = json_path.name
    return result


def summarize(case: str):
    outdir = ROOT / "results" / case
    paths = sorted(outdir.glob("dx_*nm.json"), key=lambda p: json.loads(p.read_text())["dx_nm"])
    rows = [json.loads(p.read_text()) for p in paths]
    if not rows:
        raise ValueError("no results")
    rows.sort(key=lambda r: -r["dx_nm"])
    for i, row in enumerate(rows):
        row["previous_coarser_K_change_percent"] = None
        if i:
            row["previous_coarser_K_change_percent"] = abs(
                row["K_m3"] / rows[i - 1]["K_m3"] - 1) * 100
    fields = ["case_id", "dx_nm", "mesh_triangles", "matrix_dofs_before_wall_elimination",
              "direct_relative_residual", "K_m3", "previous_coarser_K_change_percent",
              "power_balance_percent", "section_flux_spread_percent",
              "section_vs_volume_percent", "flat_K_error_percent",
              "flat_profile_L2_percent", "FVM_difference_percent", "field_sha256"]
    with (outdir / "SUMMARY.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (outdir / "SUMMARY.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    return rows


def parse_case(case: str):
    """Return (h_nm, d_nm, direction) for a case name.

    Accepted forms are the flat reference cases ``flat_h75_P``/``flat_h75_T``
    and any rectangular geometry ``h{H}_d{D}_{P|T}`` with H > 0 and D >= 0.
    The geometry is taken from the name only; nothing is inferred or clamped.
    """
    parts = case.split("_")
    if case.startswith("flat"):
        if len(parts) != 3 or parts[2] not in ("P", "T"):
            raise ValueError(f"bad flat case name: {case}")
        return 75.0, 0.0, parts[2]
    if len(parts) != 3:
        raise ValueError(f"case name must be h{{H}}_d{{D}}_{{P|T}}: {case}")
    if parts[0][:1] != "h" or parts[1][:1] != "d" or parts[2] not in ("P", "T"):
        raise ValueError(f"case name must be h{{H}}_d{{D}}_{{P|T}}: {case}")
    h = float(parts[0][1:])
    d = float(parts[1][1:])
    if not math.isfinite(h) or h <= 0:
        raise ValueError(f"gap height must be positive: {case}")
    if not math.isfinite(d) or d < 0:
        raise ValueError(f"groove depth must be non-negative: {case}")
    return h, d, parts[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--levels", nargs="+", type=float, default=[5.0, 2.5, 1.25])
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    h, d, direction = parse_case(args.case)
    for dx in args.levels:
        result = run_level(args.case, h, d, direction, dx, args.overwrite)
        print(json.dumps({k: result[k] for k in
                          ["case_id", "dx_nm", "K_m3", "direct_relative_residual",
                           "power_balance_percent"]}, ensure_ascii=False))
    rows = summarize(args.case)
    print(f"SUMMARY {ROOT / 'results' / args.case / 'SUMMARY.csv'} ({len(rows)} levels)")


if __name__ == "__main__":
    main()
