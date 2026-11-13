#!/usr/bin/env python3
"""Independent field, equation and section-flux verification for the FEM pilot.

K, power, divergence, section fluxes, pressure periodicity and algebraic residuals
are reconstructed from saved fields.  Solver-reported diagnostics are not gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from numpy.polynomial.legendre import leggauss
from skfem import (Basis, BilinearForm, ElementTriP1, ElementTriP2,
                   LinearForm, MeshTri, asm)
from skfem.helpers import dot, grad

ROOT = Path(__file__).resolve().parent
EXPECTED_LEVELS = [5.0, 2.5, 1.25]
FVM_REF = {
    "h75_d100_P": 9.755622669730348e-23,
    "h75_d100_T": 4.340041663047474e-23,
}

Q1 = 0.445948490915965
Q2 = 0.091576213509771
W1 = 0.223381589678011
W2 = 0.109951743655322
BARY = np.array([
    [Q1, Q1, 1 - 2 * Q1], [1 - 2 * Q1, Q1, Q1], [Q1, 1 - 2 * Q1, Q1],
    [Q2, Q2, 1 - 2 * Q2], [1 - 2 * Q2, Q2, Q2], [Q2, 1 - 2 * Q2, Q2],
])
QW = np.array([W1, W1, W1, W2, W2, W2])


@BilinearForm
def residual_laplace(u, v, w):
    return dot(grad(u), grad(v))


@BilinearForm
def residual_divergence_x(u, v, w):
    return grad(u)[0] * v


@BilinearForm
def residual_divergence_z(u, v, w):
    return grad(u)[1] * v


@LinearForm
def residual_force(v, w):
    return v


@LinearForm
def residual_mean(v, w):
    return v


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def p2_basis(L):
    return np.column_stack((
        L[:, 0] * (2 * L[:, 0] - 1), L[:, 1] * (2 * L[:, 1] - 1),
        L[:, 2] * (2 * L[:, 2] - 1), 4 * L[:, 0] * L[:, 1],
        4 * L[:, 1] * L[:, 2], 4 * L[:, 2] * L[:, 0],
    ))


def p2_gradients(L, grads):
    out = np.empty((6, L.shape[0], 2))
    for i in range(3):
        out[i] = (4 * L[:, i:i+1] - 1) * grads[i]
    out[3] = 4 * (L[:, 0:1] * grads[1] + L[:, 1:2] * grads[0])
    out[4] = 4 * (L[:, 1:2] * grads[2] + L[:, 2:3] * grads[1])
    out[5] = 4 * (L[:, 2:3] * grads[0] + L[:, 0:1] * grads[2])
    return out


def local_dofs(ids, nv, edge_lookup):
    eids = [edge_lookup[tuple(sorted((ids[0], ids[1])))],
            edge_lookup[tuple(sorted((ids[1], ids[2])))],
            edge_lookup[tuple(sorted((ids[2], ids[0])))]]
    return ids + [nv + e for e in eids]


def reduced_segment(values, left, right, wall=()):
    """Apply T^T to a residual segment without using solver metadata."""
    right_set = set(int(i) for i in right)
    wall_set = set(int(i) for i in wall)
    left_to_right = {int(a): int(b) for a, b in zip(left, right)}
    out = []
    for i, value in enumerate(values):
        if i in right_set or i in wall_set:
            continue
        out.append(float(value) + (float(values[left_to_right[i]]) if i in left_to_right else 0.0))
    return np.array(out)


def equation_residual(meta, data, basis, left, right, wall_dofs):
    """Reassemble the discrete equations and test the saved field, not a JSON scalar."""
    ux, uz, pressure = data["ux"], data["uz"], data["pressure"]
    stiff = asm(residual_laplace, basis)
    load = asm(residual_force, basis)
    if meta["direction"] == "P":
        residual = reduced_segment(stiff @ ux - load, left, right, wall_dofs)
        rhs = reduced_segment(load, left, right, wall_dofs)
        return float(np.linalg.norm(residual) / max(np.linalg.norm(rhs), 1e-300))
    basis1 = Basis(basis.mesh, ElementTriP1(), intorder=6)
    bx = asm(residual_divergence_x, basis, basis1)
    bz = asm(residual_divergence_z, basis, basis1)
    mean = asm(residual_mean, basis1)
    continuity = bx @ ux + bz @ uz
    # P1 pressure DOFs live at vertices. Select through boundary facets so
    # shoulder vertices at z=d are included exactly as in the solver.
    bf = basis1.mesh.boundary_facets()
    centers = basis1.mesh.p[:, basis1.mesh.facets].mean(axis=1)[:, bf]
    plf = bf[(np.abs(centers[0]) < 1e-9) &
             (centers[1] > float(meta["d_nm"]) + 1e-9)]
    prf = bf[(np.abs(centers[0] - float(meta["P_nm"])) < 1e-9) &
             (centers[1] > float(meta["d_nm"]) + 1e-9)]
    pl = sorted(basis1.get_dofs(plf).all(), key=lambda i: basis1.doflocs[1, i])
    pr = sorted(basis1.get_dofs(prf).all(), key=lambda i: basis1.doflocs[1, i])
    if len(pl) != len(pr) or not pl:
        raise ValueError("pressure periodic pairing failed")
    if "pressure_multiplier" in data:
        multiplier = float(data["pressure_multiplier"])
    else:
        # Legacy pilot fields omitted this single scalar. Recover the unique
        # least-squares value from the saved continuity equation; the residual
        # still tests all remaining momentum/continuity/mean-pressure rows.
        cm = reduced_segment(mean, pl, pr)
        cr = reduced_segment(continuity, pl, pr)
        multiplier = -float(cm @ cr) / max(float(cm @ cm), 1e-300)
    segments = [reduced_segment(stiff @ ux - bx.T @ pressure - load, left, right, wall_dofs),
                reduced_segment(stiff @ uz - bz.T @ pressure, left, right, wall_dofs),
                reduced_segment(bx @ ux + bz @ uz + multiplier * mean, pl, pr),
                np.array([mean @ pressure])]
    rhs = [reduced_segment(load, left, right, wall_dofs),
           np.zeros(1), np.zeros(1), np.zeros(1)]
    numerator = math.sqrt(sum(float(r @ r) for r in segments))
    denominator = math.sqrt(sum(float(r @ r) for r in rhs))
    return numerator / max(denominator, 1e-300)


def independent_sections(meta, data, p, t, nv, edge_lookup):
    if meta["direction"] == "P":
        return {"section_count": 0, "section_flux_spread_percent": 0.0,
                "section_vs_volume_percent": 0.0}
    ux = data["ux"]
    d, h = float(data["d"]), float(data["h"])
    stations = meta["P_nm"] * np.array([0.07, 0.13, 0.21, 0.31, 0.43,
                                        0.57, 0.69, 0.79, 0.87, 0.93])
    nodes, weights = leggauss(4)
    fluxes = []
    for x0 in stations:
        q = 0.0
        for tri in t.T:
            ids = [int(i) for i in tri]
            xy = p[:, ids]
            if x0 < xy[0].min() - 1e-10 or x0 > xy[0].max() + 1e-10:
                continue
            hits = []
            for i, j in [(0, 1), (1, 2), (2, 0)]:
                xa, xb = xy[0, i], xy[0, j]
                if abs(xa - xb) < 1e-12:
                    continue
                s = (x0 - xa) / (xb - xa)
                if s < -1e-10 or s > 1 + 1e-10:
                    continue
                s = min(1.0, max(0.0, s))
                L = np.zeros(3)
                L[i], L[j] = 1 - s, s
                z = float(xy[1, i] * (1 - s) + xy[1, j] * s)
                if not any(abs(z - old[0]) < 1e-9 for old in hits):
                    hits.append((z, L))
            if not hits:
                continue
            if len(hits) != 2:
                raise ValueError(f"vertical section does not cut triangle in two points: x={x0}")
            hits.sort(key=lambda item: item[0])
            (za, La), (zb, Lb) = hits
            ss = (nodes + 1) / 2
            LL = (1 - ss[:, None]) * La + ss[:, None] * Lb
            values = p2_basis(LL) @ ux[local_dofs(ids, nv, edge_lookup)]
            q += (zb - za) / 2 * float(weights @ values)
        fluxes.append(q)
    fluxes = np.array(fluxes)
    mean = float(np.mean(fluxes))
    # The volume integral is independently recomputed below; this temporary
    # value is replaced before gating.
    return {"section_count": len(fluxes), "section_fluxes_dimensionless": fluxes.tolist(),
            "section_flux_mean_dimensionless": mean,
            "section_flux_spread_percent": float((fluxes.max() - fluxes.min()) / mean * 100)}


def reintegrate(json_path: Path):
    meta = json.loads(json_path.read_text())
    field_path = json_path.parent / meta["field_file"]
    if sha256(field_path) != meta["field_sha256"]:
        raise ValueError(f"field hash mismatch: {field_path}")
    data = np.load(field_path)
    p, t = data["p"], data["t"]
    ux, uz, pressure = data["ux"], data["uz"], data["pressure"]
    mesh = MeshTri(p, t)
    # Match the solver's quadrature for the load and divergence blocks.
    # Lower-order integration changes those blocks and creates a false residual.
    basis = Basis(mesh, ElementTriP2(), intorder=6)
    facets = mesh.facets
    nv = p.shape[1]
    edge_lookup = {tuple(sorted((int(a), int(b)))): i for i, (a, b) in enumerate(facets.T)}
    N = p2_basis(BARY)
    area = integral = grad_integral = pmean = divergence2 = 0.0
    err2 = ref2 = 0.0
    h, d = float(data["h"]), float(data["d"])
    boundary = mesh.boundary_facets()
    centers = p[:, facets].mean(axis=1)[:, boundary]
    left = boundary[(np.abs(centers[0]) < 1e-9) & (centers[1] > d + 1e-9)]
    right = boundary[(np.abs(centers[0] - meta["P_nm"]) < 1e-9) & (centers[1] > d + 1e-9)]
    periodic = set(left.tolist()) | set(right.tolist())
    wall = np.array([f for f in boundary if f not in periodic], dtype=int)
    wall_dofs = basis.get_dofs(wall).all()
    scale = max(float(np.max(np.abs(ux))), 1e-300)
    wall_relative = max(float(np.max(np.abs(ux[wall_dofs]))),
                        float(np.max(np.abs(uz[wall_dofs])))) / scale
    dl = sorted(basis.get_dofs(left).all(), key=lambda i: basis.doflocs[1, i])
    dr = sorted(basis.get_dofs(right).all(), key=lambda i: basis.doflocs[1, i])
    if len(dl) != len(dr) or not dl:
        raise ValueError("independent periodic pairing failed")
    periodic_relative = max(max(abs(float(ux[a] - ux[b])) for a, b in zip(dl, dr)),
                            max(abs(float(uz[a] - uz[b])) for a, b in zip(dl, dr))) / scale
    for tri in t.T:
        ids = [int(i) for i in tri]
        xy = p[:, ids]
        centroid = xy.mean(axis=1)
        if d > 0 and centroid[0] > meta["w_nm"] and centroid[1] < d:
            raise ValueError("triangle occupies solid ridge")
        det = float(np.linalg.det(np.column_stack((xy[:, 1] - xy[:, 0], xy[:, 2] - xy[:, 0]))))
        tri_area = abs(det) / 2
        if tri_area <= 0:
            raise ValueError("degenerate triangle")
        grads = np.array([[xy[1, 1] - xy[1, 2], xy[0, 2] - xy[0, 1]],
                          [xy[1, 2] - xy[1, 0], xy[0, 0] - xy[0, 2]],
                          [xy[1, 0] - xy[1, 1], xy[0, 1] - xy[0, 0]]]) / det
        local = local_dofs(ids, nv, edge_lookup)
        u_local, uz_local = ux[local], uz[local]
        u_q = N @ u_local
        gu = p2_gradients(BARY, grads)
        gux = np.einsum("i,iqj->qj", u_local, gu)
        guz = np.einsum("i,iqj->qj", uz_local, gu)
        area += tri_area
        integral += tri_area * float(QW @ u_q)
        grad_integral += tri_area * float(QW @ (np.sum(gux**2, axis=1) + np.sum(guz**2, axis=1)))
        divergence2 += tri_area * float(QW @ ((gux[:, 0] + guz[:, 1])**2))
        if len(pressure):
            pmean += tri_area * float(QW @ (BARY @ pressure[ids]))
        if d == 0:
            zz = BARY @ xy[1]
            exact = zz * (h - zz) / 2
            err2 += tri_area * float(QW @ ((u_q - exact)**2))
            ref2 += tri_area * float(QW @ (exact**2))
    K = 1e-27 / float(meta["P_nm"]) * integral
    residual = equation_residual(meta, data, basis, dl, dr, wall_dofs)
    section = independent_sections(meta, data, p, t, nv, edge_lookup)
    if meta["direction"] == "T":
        section["section_vs_volume_percent"] = abs(
            section["section_flux_mean_dimensionless"] / (integral / meta["P_nm"]) - 1) * 100
    pressure_scale = max(float(np.max(np.abs(pressure))), 1e-300) if len(pressure) else 1.0
    if len(pressure):
        left_nodes = sorted(set(int(i) for i in mesh.facets[:, left].ravel()), key=lambda i: p[1, i])
        right_nodes = sorted(set(int(i) for i in mesh.facets[:, right].ravel()), key=lambda i: p[1, i])
        if len(left_nodes) != len(right_nodes) or not left_nodes:
            raise ValueError("pressure vertex pairing failed")
        pressure_periodic = max(abs(float(pressure[a] - pressure[b]))
                                for a, b in zip(left_nodes, right_nodes)) / pressure_scale
    else:
        pressure_periodic = 0.0
    out = {
        "case_id": meta["case_id"], "dx_nm": meta["dx_nm"],
        "area_recomputed": area, "area_relative_error": abs(area / meta["area_exact_dimensionless"] - 1),
        "K_recomputed_m3": K, "K_vs_solver_relative_difference": abs(K / meta["K_m3"] - 1),
        "power_balance_recomputed_percent": abs(grad_integral / integral - 1) * 100,
        "divergence_L2_relative": math.sqrt(divergence2 / grad_integral),
        "pressure_mean_recomputed": pmean,
        "pressure_mean_normalized": abs(pmean) / (pressure_scale * area),
        "pressure_periodic_relative_max_difference": pressure_periodic,
        "wall_velocity_relative_max": wall_relative,
        "periodic_velocity_relative_max_difference": periodic_relative,
        "direct_relative_residual_recomputed": residual,
        "solver_reported_direct_relative_residual": meta["direct_relative_residual"],
        **section,
    }
    if d == 0:
        exact_K = (h * 1e-9)**3 / 12
        out["flat_K_error_recomputed_percent"] = abs(K / exact_K - 1) * 100
        out["flat_profile_L2_recomputed_percent"] = math.sqrt(err2 / ref2) * 100
    if meta["case_id"] in FVM_REF:
        out["FVM_difference_recomputed_percent"] = abs(K / FVM_REF[meta["case_id"]] - 1) * 100
    return out


def verify_case(case: str):
    case_dir = ROOT / "results" / case
    rows, problems = [], []
    for dx in EXPECTED_LEVELS:
        path = case_dir / f"dx_{dx:g}nm.json"
        if not path.exists():
            problems.append(f"missing {path.name}")
            continue
        rows.append(reintegrate(path))
    for row in rows:
        prefix = f"{case} dx{row['dx_nm']}"
        if row["area_relative_error"] > 1e-10: problems.append(f"{prefix}: area")
        if row["K_vs_solver_relative_difference"] > 1e-9: problems.append(f"{prefix}: independent K mismatch")
        if row["wall_velocity_relative_max"] > 1e-10: problems.append(f"{prefix}: wall no-slip")
        if row["periodic_velocity_relative_max_difference"] > 1e-10: problems.append(f"{prefix}: periodic velocity")
        if row["pressure_periodic_relative_max_difference"] > 1e-10: problems.append(f"{prefix}: periodic pressure")
        if row["pressure_mean_normalized"] > 1e-10: problems.append(f"{prefix}: pressure mean")
        # P2/P1 enforces incompressibility weakly, not pointwise. The
        # reconstructed divergence is diagnostic; the algebraic continuity
        # residual above is the actual gate.
        if row["direct_relative_residual_recomputed"] > 1e-10: problems.append(f"{prefix}: direct residual")
        if row["power_balance_recomputed_percent"] > 0.1: problems.append(f"{prefix}: power")
        if row["section_flux_spread_percent"] > 0.01 or row["section_vs_volume_percent"] > 0.01:
            problems.append(f"{prefix}: section flux")
        if "flat_K_error_recomputed_percent" in row:
            if row["flat_K_error_recomputed_percent"] > 0.1 or row["flat_profile_L2_recomputed_percent"] > 0.1:
                problems.append(f"{prefix}: analytical flat check")
    rows.sort(key=lambda r: -r["dx_nm"])
    for i, row in enumerate(rows):
        row["K_change_from_coarser_recomputed_percent"] = None
        if i:
            change = abs(row["K_recomputed_m3"] / rows[i-1]["K_recomputed_m3"] - 1) * 100
            row["K_change_from_coarser_recomputed_percent"] = change
            limit = 1.0 if i == 1 else 0.5
            if change > limit: problems.append(f"{case} dx{row['dx_nm']}: grid change {change}>{limit}")
    if case in FVM_REF and rows:
        fine = min(rows, key=lambda r: r["dx_nm"])
        if fine["FVM_difference_recomputed_percent"] > 0.5: problems.append(f"{case}: FVM difference >0.5%")
    result = {"case_id": case,
              "status": "PILOT_NUMERICAL_CHECKS_PASS" if not problems else "PILOT_CHECKS_FAIL",
              "problems": problems, "levels": rows,
              "reference_qualification": "NOT_GRANTED_REQUIRES_INDEPENDENT_SCIENTIFIC_REVIEW",
              "automatic_followup_authorized": False}
    (case_dir / "VERIFICATION.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cases", nargs="+", choices=["flat_h75_P", "flat_h75_T",
                        "h75_d100_P", "h75_d100_T", "h50_d120_T", "h125_d120_T"])
    args = parser.parse_args()
    failed = False
    for case in args.cases:
        result = verify_case(case)
        print(case, result["status"], result["problems"])
        failed |= bool(result["problems"])
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
