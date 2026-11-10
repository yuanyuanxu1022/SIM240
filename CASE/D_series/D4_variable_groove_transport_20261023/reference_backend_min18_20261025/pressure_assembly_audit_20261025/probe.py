"""Assemble one bound mixed Stokes system and inspect it; never solve it."""

import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mesh_periodic_pressure_20261025"))
sys.path.insert(0, str(ROOT / "src"))
from interface import build_interface  # noqa: E402
from symbolic_forms import manufactured_fields, stokes_forms  # noqa: E402


def audit(planned_id):
    import ufl
    from dolfinx import fem
    from dolfinx_mpc import assemble_matrix, assemble_vector, apply_lifting
    from petsc4py import PETSc

    item = build_interface(planned_id)
    plan = item["plan"]
    if item["pressure"] is None:
        raise ValueError("MIXED_PRESSURE_CASE_REQUIRED")
    W, mpc, bc = item["space"], item["mpc"], item["wall_bc"]
    u, pressure = ufl.TrialFunctions(W)
    test_u, test_q = ufl.TestFunctions(W)
    if plan["problem"] == "MMS":
        forcing = manufactured_fields(ufl.SpatialCoordinate(item["domain"]))["mixed_forcing"]
    else:
        forcing = ufl.as_vector((1.0, 0.0))
    dx = ufl.Measure("dx", domain=item["domain"],
                     metadata={"quadrature_degree": plan["quadrature_degree"]})
    a, L = stokes_forms(u, pressure, test_u, test_q, forcing, dx)
    a_form, L_form = fem.form(a), fem.form(L)
    A = assemble_matrix(a_form, mpc, bcs=[bc])
    b = assemble_vector(L_form, mpc)
    apply_lifting(b, [a_form], bcs=[[bc]], constraint=mpc)
    b.ghostUpdate(addv=PETSc.InsertMode.ADD, mode=PETSc.ScatterMode.REVERSE)
    fem.petsc.set_bc(b, [bc])
    b.ghostUpdate(addv=PETSc.InsertMode.INSERT, mode=PETSc.ScatterMode.FORWARD)

    rowptr, columns, values = A.getValuesCSR()
    if not (np.all(np.isfinite(values)) and np.all(np.isfinite(b.array))):
        raise ValueError("NONFINITE_ASSEMBLED_SYSTEM")

    def digest(*arrays):
        h = hashlib.sha256()
        for x in arrays:
            h.update(np.ascontiguousarray(x).tobytes())
        return h.hexdigest()

    def check(candidate, rhs):
        n = A.createVecRight()
        n.array[:] = candidate
        n.normalize()
        an = A.createVecLeft()
        A.mult(n, an)
        return {"An_L2": float(an.norm()), "An_max": float(np.max(np.abs(an.array))),
                "An_over_A_Frobenius": float(an.norm()/A.norm(PETSc.NormType.FROBENIUS)),
                "n_dot_b": float(n.dot(rhs)),
                "n_dot_b_over_b_L2": float(abs(n.dot(rhs))/rhs.norm()) if rhs.norm() else 0.0}

    original = item["pressure"]["constant_vector"]
    reduced = original.copy()
    reduced[np.asarray(mpc.slaves, dtype=np.int64)] = 0
    n = A.createVecRight()
    n.array[:] = reduced
    n.normalize()
    nullspace = PETSc.NullSpace().create(vectors=[n], comm=PETSc.COMM_SELF)
    nullspace_test = bool(nullspace.test(A))
    b_before = b.copy()
    nullspace.remove(b)
    rhs_projection_change = float((b-b_before).norm())
    if not nullspace_test:
        raise ValueError("REDUCED_PRESSURE_NULLSPACE_TEST_FAILED")
    # The collapsed pressure space has a different map; use the nonzero gauge
    # positions in the parent mixed vector to inspect its continuity RHS.
    pressure_parent_indices = np.flatnonzero(original)
    return {"planned_id": planned_id, "quadrature_degree": plan["quadrature_degree"],
            "mesh_sha256": item["stats"]["actual_mesh_sha256"],
            "periodic_mapping_sha256": item["stats"]["periodic_link_audit"]["mapping_sha256"],
            "periodic_slave_count": item["stats"]["periodic_link_audit"]["slave_count"],
            "matrix_shape": list(A.getSize()), "matrix_nnz": int(A.getInfo()["nz_used"]),
            "matrix_csr_sha256": digest(rowptr, columns, values),
            "rhs_sha256_before_projection": digest(b_before.array),
            "matrix_values_finite": True, "rhs_values_finite": True,
            "matrix_symmetric_1e-11": bool(A.isSymmetric(tol=1e-11)),
            "matrix_Frobenius": float(A.norm(PETSc.NormType.FROBENIUS)),
            "rhs_L2": float(b_before.norm()),
            "pressure_rhs_max_abs": float(np.max(np.abs(b_before.array[pressure_parent_indices]))),
            "pressure_dofs": int(np.count_nonzero(original)),
            "pressure_slave_dofs": int(np.count_nonzero(original-reduced)),
            "original_full_pressure_candidate": check(original, b_before),
            "reduced_pressure_candidate": check(reduced, b_before),
            "petsc_nullspace_test_reduced": nullspace_test,
            "rhs_projection_change_L2": rhs_projection_change,
            "solver_called": False, "field_computed": False}


if __name__ == "__main__":
    print(json.dumps(audit(sys.argv[1]), indent=2, allow_nan=False))
