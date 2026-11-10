"""Review-only solver v2 with failure snapshot callback; never solved here.

The frozen 18-case whitelist denies every KSP call. This independent version
preserves the previous candidate untouched and adds pre-backsub failure data.
"""

from dataclasses import dataclass
import math
from typing import Mapping

import numpy as np


class CandidateRejected(ValueError):
    pass


class CandidateSolveFailure(RuntimeError):
    def __init__(self, diagnostics):
        self.diagnostics = diagnostics
        super().__init__("CANDIDATE_SOLVE_FAILED: " + str(diagnostics))


@dataclass(frozen=True)
class DiagnosticGMRES:
    """Unpreconditioned diagnostic only; no production resource claim."""

    ksp_rtol: float
    true_residual_target: float
    max_iterations: int
    restart: int

    def validate(self):
        if (not math.isfinite(self.ksp_rtol) or not 0 < self.ksp_rtol < 1
                or not math.isfinite(self.true_residual_target)
                or not 0 < self.true_residual_target < 1
                or isinstance(self.max_iterations, bool)
                or not isinstance(self.max_iterations, int)
                or self.max_iterations < 1
                or isinstance(self.restart, bool)
                or not isinstance(self.restart, int)
                or not 1 <= self.restart <= self.max_iterations):
            raise CandidateRejected("INVALID_DIAGNOSTIC_GMRES_SETTINGS")


def check_release(system, config, release):
    """Fail closed before any PETSc solver object is created."""
    if not isinstance(config, DiagnosticGMRES):
        raise CandidateRejected("SOLVER_SETTINGS_REQUIRED")
    config.validate()
    if not isinstance(system, dict) or "item" not in system:
        raise CandidateRejected("PRECHECKED_SYSTEM_REQUIRED")
    item = system["item"]
    plan = item["plan"]
    if plan.get("execution_authorized") is not True:
        raise CandidateRejected("FROZEN_WHITELIST_DENIES_SOLVE")
    if not isinstance(release, Mapping) or release.get("status") != "APPROVED_FOR_RECTANGLE_SOLVE":
        raise CandidateRejected("REVIEWED_RELEASE_REQUIRED")
    if (release.get("planned_id") != plan["planned_id"]
            or release.get("matrix_csr_sha256") != system.get("matrix_csr_sha256")
            or release.get("rhs_sha256_before_projection") != system.get("rhs_sha256_before_projection")):
        raise CandidateRejected("RELEASE_INPUT_BINDING_MISMATCH")
    if not system["gauge"]["right_and_transpose_nullspaces_attached"]:
        raise CandidateRejected("PRESSURE_NULLSPACE_NOT_ATTACHED")


def solve_prepared_mixed_system(system, config, release, failure_sink):
    """Future callable path; requires a new plan/release and was not run.

    A future worker must supply a durable failure_sink(stage, error, vector,
    diagnostics, binding). It must save the vector before this function returns
    or raises. The current whitelist rejects before creating any KSP object.
    """
    check_release(system, config, release)
    if not callable(failure_sink):
        raise CandidateRejected("DURABLE_FAILURE_SINK_REQUIRED")
    from petsc4py import PETSc

    A, b = system["matrix"], system["rhs"]
    item = system["item"]
    ksp = PETSc.KSP().create(comm=PETSc.COMM_SELF)
    x = None
    algebraic_x = None
    diagnostics = {}
    stage = "KSP_CONFIGURATION"
    try:
        ksp.setType(PETSc.KSP.Type.GMRES)
        ksp.getPC().setType(PETSc.PC.Type.NONE)
        ksp.setNormType(PETSc.KSP.NormType.UNPRECONDITIONED)
        ksp.setGMRESRestart(config.restart)
        ksp.setTolerances(rtol=config.ksp_rtol, atol=0.0,
                          max_it=config.max_iterations)
        ksp.setConvergenceHistory(length=config.max_iterations + 1, reset=True)
        ksp.setErrorIfNotConverged(False)
        ksp.setOperators(A)
        x = A.createVecRight()
        x.set(0.0)
        stage = "KSP_SOLVE"
        ksp.solve(b, x)
        stage = "RESIDUAL_CHECK"
        reason = int(ksp.getConvergedReason())
        iterations = int(ksp.getIterationNumber())
        reported_history = np.asarray(ksp.getConvergenceHistory(), dtype=np.float64).copy()
        algebraic_x = x.copy()
        residual = A.createVecLeft()
        A.mult(algebraic_x, residual)
        residual.axpy(-1.0, b)
        rhs_norm = b.norm()
        true_relative = float(residual.norm() / rhs_norm) if rhs_norm > 0 else math.inf
        diagnostics = {"ksp_type": "gmres", "pc_type": "none",
                       "ksp_reason": reason, "ksp_iterations": iterations,
                       "true_unpreconditioned_relative_residual": true_relative,
                       "true_residual_target": config.true_residual_target,
                       "ksp_rtol": config.ksp_rtol, "max_iterations": config.max_iterations,
                       "restart": config.restart,
                       "ksp_reported_residual_history": reported_history.tolist()}
        if reason <= 0 or not math.isfinite(true_relative) or true_relative > config.true_residual_target:
            raise CandidateSolveFailure(diagnostics)

        # Physical pressure is read only after restoring periodic slave values.
        stage = "MPC_AND_PRESSURE_POSTPROCESS"
        item["mpc"].backsubstitution(x)
        Q_original, _ = item["space"].sub(1).collapse()
        Q_reconstructed, pressure_map = item["mpc"].function_space.sub(1).collapse()
        original_coordinates = Q_original.tabulate_dof_coordinates()
        reconstructed_coordinates = Q_reconstructed.tabulate_dof_coordinates()
        if (original_coordinates.shape != reconstructed_coordinates.shape
                or np.max(np.abs(original_coordinates-reconstructed_coordinates)) > 1e-11):
            raise CandidateSolveFailure({"reason": "PRESSURE_WEIGHT_DOF_ORDER_MISMATCH",
                                         **diagnostics})
        weights = np.asarray(item["pressure"]["nodal_area_weights"], dtype=np.float64)
        pressure_raw = np.asarray(x.array[np.asarray(pressure_map[0], dtype=np.int64)],
                                  dtype=np.float64).copy()
        if len(weights) != len(pressure_raw) or not np.all(np.isfinite(pressure_raw)):
            raise CandidateSolveFailure({"reason": "INVALID_PRESSURE_POSTPROCESS",
                                         **diagnostics})
        area = float(np.sum(weights))
        removed_mean = float(np.dot(weights, pressure_raw) / area)
        pressure_zero_mean = pressure_raw - removed_mean
        return {"status": "CANDIDATE_SOLUTION_NOT_INDEPENDENTLY_ACCEPTED",
                "algebraic_solution_before_backsubstitution": algebraic_x,
                "periodic_reconstructed_solution": x,
                "pressure_raw_P1": pressure_raw,
                "pressure_zero_area_mean_P1": pressure_zero_mean,
                "pressure_removed_area_mean": removed_mean,
                "pressure_area_integral_after_shift": float(np.dot(weights, pressure_zero_mean)),
                "diagnostics": diagnostics,
                "NUMERICAL_GATE": "NOT_EVALUATED", "RESULT_PASS": False,
                "geometry_PASS": None}
    except Exception as exc:
        # Preserve an already computed algebraic vector, never a backsubstituted
        # vector mislabeled as algebraic. Before the copy exists, x is still
        # algebraic because MPC backsubstitution has not yet been reached.
        source = algebraic_x if algebraic_x is not None else x
        snapshot = None if source is None else np.asarray(source.array, dtype=np.float64).copy()
        failure_details = dict(diagnostics)
        if isinstance(exc, CandidateSolveFailure):
            failure_details.update(exc.diagnostics)
        for label, get in (("ksp_reason_if_available", ksp.getConvergedReason),
                           ("ksp_iterations_if_available", ksp.getIterationNumber),
                           ("ksp_history_if_available", ksp.getConvergenceHistory)):
            try:
                value = get()
                failure_details[label] = (np.asarray(value, dtype=np.float64).tolist()
                                          if label.endswith("history_if_available") else int(value))
            except Exception as query_exc:
                failure_details[label] = "UNAVAILABLE:" + type(query_exc).__name__
        binding = {"planned_id": item["plan"]["planned_id"],
                   "matrix_csr_sha256": system["matrix_csr_sha256"],
                   "rhs_sha256_before_projection": system["rhs_sha256_before_projection"]}
        try:
            failure_sink(stage, exc, snapshot, failure_details, binding)
        except Exception as archive_exc:
            raise RuntimeError("FAILURE_ARCHIVE_FAILED; original=" + repr(exc)) from archive_exc
        raise
    finally:
        ksp.destroy()
