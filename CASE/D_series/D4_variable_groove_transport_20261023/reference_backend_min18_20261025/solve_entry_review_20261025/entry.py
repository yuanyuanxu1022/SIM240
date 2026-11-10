"""Reviewed Stokes assembly seam. No KSP, solve, execution flag or field output."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mesh_periodic_pressure_20261025"))
sys.path.insert(0, str(ROOT / "src"))
from contract import Rejected  # noqa: E402
from interface import build_interface  # noqa: E402
from symbolic_forms import manufactured_fields, stokes_forms  # noqa: E402


def digest(*arrays):
    h = hashlib.sha256()
    for values in arrays:
        h.update(np.ascontiguousarray(values).tobytes())
    return h.hexdigest()


def reduced_pressure_candidate(item):
    """Represent constant physical pressure in the MPC matrix's free DOFs."""
    pressure = item["pressure"]
    if pressure is None:
        raise Rejected("PRESSURE_GAUGE_REQUIRES_MIXED_CASE")
    old = np.asarray(pressure["constant_vector"], dtype=np.float64)
    slaves = np.asarray(item["mpc"].slaves, dtype=np.int64)
    if old.ndim != 1 or len(old) != item["mpc"].function_space.dofmap.index_map.size_local:
        raise Rejected("PRESSURE_CANDIDATE_SIZE_MISMATCH")
    pressure_slaves = slaves[old[slaves] != 0]
    if len(pressure_slaves) != item["stats"]["trace"]["P1_pressure_slaves_including_endpoints"]:
        raise Rejected("PRESSURE_SLAVE_COUNT_MISMATCH")
    for slave in pressure_slaves:
        masters = item["mpc"].masters.links(int(slave))
        if len(masters) != 1 or old[int(masters[0])] == 0:
            raise Rejected("PRESSURE_SLAVE_MASTER_NOT_CONSTANT")
    reduced = old.copy()
    reduced[slaves] = 0.0
    if np.count_nonzero(reduced) != np.count_nonzero(old) - len(pressure_slaves):
        raise Rejected("PRESSURE_REDUCTION_SUPPORT_MISMATCH")
    reduced /= np.linalg.norm(reduced)
    return reduced, {"physical_pressure_dofs": int(np.count_nonzero(old)),
                     "pressure_slave_dofs_removed": int(len(pressure_slaves)),
                     "algebraic_nonzero_dofs": int(np.count_nonzero(reduced)),
                     "algebraic_slave_entries_zero": bool(np.all(reduced[slaves] == 0)),
                     "algebraic_velocity_entries_zero": bool(np.all(reduced[old == 0] == 0))}


def attach_checked_gauge(matrix, rhs, candidate, tol=1e-10):
    """Refuse a wrong/incompatible gauge before attaching it; never solve."""
    from petsc4py import PETSc

    if not np.isfinite(tol) or tol <= 0 or tol >= 1:
        raise Rejected("INVALID_GAUGE_CHECK_TOLERANCE")
    c = np.asarray(candidate, dtype=np.float64)
    rows, cols = matrix.getSize()
    if rows != cols or rows != rhs.getSize() or len(c) != cols or not np.all(np.isfinite(c)):
        raise Rejected("GAUGE_DIMENSION_OR_VALUE_MISMATCH")
    if np.linalg.norm(c) == 0 or rhs.norm() == 0:
        raise Rejected("ZERO_GAUGE_OR_RHS")
    vec = matrix.createVecRight()
    vec.array[:] = c
    vec.normalize()
    image = matrix.createVecLeft()
    left_image = matrix.createVecRight()
    matrix.mult(vec, image)
    matrix.multTranspose(vec, left_image)
    frobenius = matrix.norm(PETSc.NormType.FROBENIUS)
    if frobenius <= 0:
        raise Rejected("ZERO_MATRIX")
    right_relative = image.norm() / frobenius
    left_relative = left_image.norm() / frobenius
    compatibility_relative = abs(vec.dot(rhs)) / rhs.norm()
    if (not np.isfinite(right_relative + left_relative + compatibility_relative)
            or max(right_relative, left_relative, compatibility_relative) > tol):
        raise Rejected("PRESSURE_GAUGE_OR_RHS_INCOMPATIBLE")
    if not matrix.isSymmetric(tol=1e-11):
        raise Rejected("EXPECTED_SYMMETRIC_MATRIX_NOT_FOUND")
    nullspace = PETSc.NullSpace().create(vectors=[vec], comm=PETSc.COMM_SELF)
    if not nullspace.test(matrix):
        raise Rejected("PETSC_NULLSPACE_TEST_FAILED")
    rhs_before = rhs.copy()
    matrix.setNullSpace(nullspace)
    matrix.setTransposeNullSpace(nullspace)
    nullspace.remove(rhs)
    removed = (rhs-rhs_before).norm()
    if removed > tol * rhs_before.norm() or abs(vec.dot(rhs)) > tol * rhs_before.norm():
        raise Rejected("RHS_PROJECTION_UNEXPECTED")
    return {"vector": vec, "nullspace": nullspace,
            "right_kernel_relative": float(right_relative),
            "left_kernel_relative": float(left_relative),
            "rhs_compatibility_relative_before_projection": float(compatibility_relative),
            "rhs_projection_change_L2": float(removed),
            "petsc_nullspace_test": True,
            "right_and_transpose_nullspaces_attached": bool(
                matrix.getNullSpace() is not None and matrix.getTransposeNullSpace() is not None)}


def prepare_bound_mixed_system(planned_id):
    """Return a checked, assembled system for later review, with no solver object."""
    import ufl
    from dolfinx import fem
    from dolfinx_mpc import assemble_matrix, assemble_vector, apply_lifting
    from petsc4py import PETSc

    item = build_interface(planned_id)
    if item["pressure"] is None:
        raise Rejected("MIXED_PRESSURE_CASE_REQUIRED")
    plan = item["plan"]
    W, mpc, bc = item["space"], item["mpc"], item["wall_bc"]
    trial_u, trial_p = ufl.TrialFunctions(W)
    test_u, test_q = ufl.TestFunctions(W)
    forcing = (manufactured_fields(ufl.SpatialCoordinate(item["domain"]))["mixed_forcing"]
               if plan["problem"] == "MMS" else ufl.as_vector((1.0, 0.0)))
    dx = ufl.Measure("dx", domain=item["domain"],
                     metadata={"quadrature_degree": plan["quadrature_degree"]})
    a, L = stokes_forms(trial_u, trial_p, test_u, test_q, forcing, dx)
    a_form, L_form = fem.form(a), fem.form(L)
    matrix = assemble_matrix(a_form, mpc, bcs=[bc])
    rhs = assemble_vector(L_form, mpc)
    apply_lifting(rhs, [a_form], bcs=[[bc]], constraint=mpc)
    rhs.ghostUpdate(addv=PETSc.InsertMode.ADD, mode=PETSc.ScatterMode.REVERSE)
    fem.petsc.set_bc(rhs, [bc])
    rhs.ghostUpdate(addv=PETSc.InsertMode.INSERT, mode=PETSc.ScatterMode.FORWARD)
    rowptr, columns, values = matrix.getValuesCSR()
    if not np.all(np.isfinite(values)) or not np.all(np.isfinite(rhs.array)):
        raise Rejected("NONFINITE_ASSEMBLED_SYSTEM")
    matrix_hash, rhs_hash = digest(rowptr, columns, values), digest(rhs.array)
    candidate, support = reduced_pressure_candidate(item)
    gauge = attach_checked_gauge(matrix, rhs, candidate)
    reconstructed = gauge["vector"].copy()
    mpc.backsubstitution(reconstructed)
    old = item["pressure"]["constant_vector"]
    expected = old * (candidate[np.flatnonzero(candidate)[0]] / old[np.flatnonzero(old)[0]])
    reconstruction_max_error = float(np.max(np.abs(reconstructed.array-expected)))
    if reconstruction_max_error > 1e-12:
        raise Rejected("PRESSURE_BACKSUBSTITUTION_NOT_CONSTANT")
    return {"item": item, "matrix": matrix, "rhs": rhs, "candidate": candidate,
            "gauge": gauge, "support": support,
            "pressure_backsubstitution_max_error": reconstruction_max_error,
            "matrix_csr_sha256": matrix_hash, "rhs_sha256_before_projection": rhs_hash}


def preflight(planned_id):
    from importlib.metadata import version

    system = prepare_bound_mixed_system(planned_id)
    item = system["item"]
    previous = json.loads((ROOT / "pressure_assembly_audit_20261025/evidence/assembly_all9.json").read_text())
    if previous["status"] != "COMPLETE":
        raise Rejected("PRIOR_ASSEMBLY_AUDIT_INCOMPLETE")
    for relative, expected in previous["input_sha256"].items():
        source = ROOT / relative
        if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise Rejected("PRIOR_ASSEMBLY_SOURCE_HASH_MISMATCH")
    by_id = {r["planned_id"]: r["result"] for r in previous["records"] if r["exit_code"] == 0}
    old = by_id.get(planned_id)
    if old is None or any(system[key] != old[key] for key in (
            "matrix_csr_sha256", "rhs_sha256_before_projection")):
        raise Rejected("ASSEMBLED_SYSTEM_DIFFERS_FROM_PRIOR_AUDIT")
    return {"planned_id": planned_id, "status": "PREFLIGHT_ONLY_NOT_SOLVE_PERMISSION",
            "preparation_version": item["plan"]["preparation_version"],
            "geometry": item["plan"]["geometry"], "planned_mesh": item["plan"]["mesh"],
            "actual_mesh": {key: item["stats"][key] for key in (
                "actual_triangles", "actual_vertices", "actual_raw_dofs")},
            "forcing": item["plan"]["forcing"],
            "pressure_sign": item["plan"]["pressure_sign"],
            "periodic": item["plan"]["periodic"],
            "physical_constants": item["plan"]["physical_constants"],
            "body_force_and_pressure_drop_together": item["plan"]["explicit_body_force_and_pressure_drop_together"],
            "quadrature_degree": item["plan"]["quadrature_degree"],
            "backend_versions": {name: version(name) for name in (
                "fenics-dolfinx", "dolfinx_mpc", "petsc4py", "mpi4py")},
            "mesh_sha256": item["stats"]["actual_mesh_sha256"],
            "periodic_mapping_sha256": item["stats"]["periodic_link_audit"]["mapping_sha256"],
            "matrix_shape": list(system["matrix"].getSize()),
            "matrix_csr_sha256": system["matrix_csr_sha256"],
            "rhs_sha256_before_projection": system["rhs_sha256_before_projection"],
            "pressure_support": system["support"],
            "pressure_backsubstitution_max_error": system["pressure_backsubstitution_max_error"],
            "gauge_check": {key: value for key, value in system["gauge"].items()
                            if key not in {"vector", "nullspace"}},
            "prior_assembly_hashes_match": True,
            "solver_object_created": False, "solver_called": False,
            "physical_field_generated": False, "formal_run_id": None,
            "prediction_permission": "HOLD",
            "NUMERICAL_GATE": "NOT_EVALUATED", "RESULT_PASS": False,
            "geometry_PASS": None}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Preflight only; no solve mode exists")
    parser.add_argument("--mode", choices=["preflight"], default="preflight")
    parser.add_argument("--planned-id", required=True)
    args = parser.parse_args(argv)
    print(json.dumps(preflight(args.planned_id), indent=2, ensure_ascii=False,
                     allow_nan=False))


if __name__ == "__main__":
    main()
