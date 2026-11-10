"""Versioned assembly adapter; immutable physical input stays preparation-only.

This code has not assembled or solved a PDE. It reuses the reviewed physical
interface and gauge helpers, adding a separate execution contract and b snapshot.
"""
import hashlib
import importlib.util
import inspect
from pathlib import Path
import sys
import numpy as np
from common import ROOT, validate, Rejected


def _previous():
    spec=importlib.util.spec_from_file_location("d4_pilot_physical_entry",ROOT/"solve_entry_review_20261025/entry.py")
    module=importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    finally:
        meshpath=str(ROOT/"mesh_periodic_pressure_20261025")
        sys.path[:]=[p for p in sys.path if p!=meshpath]
    return module


# Only the function below loads the physical backend, after the new gate.
def prepare_bound_mixed_system(contract):
    validate(contract, execution=True)
    planned_id = contract["planned_id"]
    """Return a checked, assembled system for later review, with no solver object."""
    previous = _previous()
    build_interface = previous.build_interface
    stokes_forms, manufactured_fields = previous.stokes_forms, previous.manufactured_fields
    reduced_pressure_candidate, attach_checked_gauge = previous.reduced_pressure_candidate, previous.attach_checked_gauge
    digest = previous.digest
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
    rhs_before_projection = rhs.copy()
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
            "execution_contract": contract, "rhs_before_projection": rhs_before_projection,
            "pressure_backsubstitution_max_error": reconstruction_max_error,
            "matrix_csr_sha256": matrix_hash, "rhs_sha256_before_projection": rhs_hash}

