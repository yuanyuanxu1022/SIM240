from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


def _positive_finite(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0, got {value!r}")


@dataclass(frozen=True)
class SqueezeProblem:
    length_m: float
    width_m: float
    mu_pa_s: float
    vp_m_s: float
    p_out_pa: float
    n_cells: int

    def __post_init__(self) -> None:
        _positive_finite("length_m", self.length_m)
        _positive_finite("width_m", self.width_m)
        _positive_finite("mu_pa_s", self.mu_pa_s)
        _positive_finite("vp_m_s", self.vp_m_s)
        if not math.isfinite(self.p_out_pa):
            raise ValueError("p_out_pa must be finite")
        if self.n_cells != 401:
            raise ValueError(f"n_cells must equal frozen value 401, got {self.n_cells}")


@dataclass(frozen=True)
class AnalyticMetrics:
    pmax_pa: float
    force_n: float
    impedance_n_s_m: float
    q_displaced_m3_s: float


@dataclass(frozen=True)
class NumericalSolution:
    centers_m: np.ndarray
    pressure_pa: np.ndarray
    face_flux_m2_s: np.ndarray
    dx_m: float


@dataclass(frozen=True)
class CaseMetrics:
    pmax_pa: float
    force_n: float
    impedance_n_s_m: float
    q_out_m3_s: float
    q_displaced_m3_s: float
    pmax_relative_error: float
    force_relative_error: float
    mass_relative_error: float
    symmetry_relative_error: float


def smooth_mobility(height_m: float) -> float:
    _positive_finite("height_m", height_m)
    return height_m**3 / 12.0


def analytic_pressure(s_m: np.ndarray, problem: SqueezeProblem, K_m3: float) -> np.ndarray:
    _positive_finite("K_m3", K_m3)
    s = np.asarray(s_m, dtype=float)
    if not np.all(np.isfinite(s)):
        raise ValueError("s_m contains non-finite values")
    half = problem.length_m / 2.0
    if np.any(np.abs(s) > half * (1.0 + 1.0e-14)):
        raise ValueError("s_m lies outside the strip")
    return problem.p_out_pa + problem.mu_pa_s * problem.vp_m_s * (half**2 - s**2) / (2.0 * K_m3)


def analytic_metrics(problem: SqueezeProblem, K_m3: float) -> AnalyticMetrics:
    _positive_finite("K_m3", K_m3)
    pmax = problem.mu_pa_s * problem.vp_m_s * problem.length_m**2 / (8.0 * K_m3)
    force = (
        problem.mu_pa_s
        * problem.vp_m_s
        * problem.width_m
        * problem.length_m**3
        / (12.0 * K_m3)
    )
    return AnalyticMetrics(
        pmax_pa=pmax,
        force_n=force,
        impedance_n_s_m=force / problem.vp_m_s,
        q_displaced_m3_s=problem.width_m * problem.length_m * problem.vp_m_s,
    )


def _relative_error(value: float, reference: float) -> float:
    if reference == 0.0:
        return abs(value - reference)
    return abs(value - reference) / abs(reference)


def solve_uniform_k(problem: SqueezeProblem, K_m3: float) -> NumericalSolution:
    _positive_finite("K_m3", K_m3)
    n = problem.n_cells
    dx = problem.length_m / n
    centers = -problem.length_m / 2.0 + (np.arange(n, dtype=float) + 0.5) * dx
    a = K_m3 / problem.mu_pa_s

    matrix = np.zeros((n, n), dtype=float)
    rhs = np.full(n, problem.vp_m_s, dtype=float)
    scale = a / dx**2

    # Boundary rows use a one-sided quadratic derivative at the half-cell
    # Dirichlet outlet. This is exact for the quadratic analytic solution, so
    # the discrete pressure reproduces p(s) to machine precision (unlike the
    # first-order "(3, -1)" half-cell stencil, which errs by ~4/N^2).
    matrix[0, 0] = 4.0 * scale
    matrix[0, 1] = -(4.0 / 3.0) * scale
    rhs[0] += (8.0 / 3.0) * scale * problem.p_out_pa
    for i in range(1, n - 1):
        matrix[i, i - 1] = -scale
        matrix[i, i] = 2.0 * scale
        matrix[i, i + 1] = -scale
    matrix[-1, -2] = -(4.0 / 3.0) * scale
    matrix[-1, -1] = 4.0 * scale
    rhs[-1] += (8.0 / 3.0) * scale * problem.p_out_pa

    pressure = np.linalg.solve(matrix, rhs)
    # Face fluxes consistent with the stencils above, so the mass audit
    # (faces[-1] - faces[0] == Vp*L) closes to machine precision.
    faces = np.empty(n + 1, dtype=float)
    faces[0] = -a * (9.0 * pressure[0] - pressure[1] - 8.0 * problem.p_out_pa) / (3.0 * dx)
    faces[1:-1] = -a * np.diff(pressure) / dx
    faces[-1] = -a * (8.0 * problem.p_out_pa - 9.0 * pressure[-1] + pressure[-2]) / (3.0 * dx)
    return NumericalSolution(centers, pressure, faces, dx)


def evaluate_solution(
    problem: SqueezeProblem,
    K_m3: float,
    solution: NumericalSolution,
) -> CaseMetrics:
    exact = analytic_metrics(problem, K_m3)
    gauge_pressure = solution.pressure_pa - problem.p_out_pa
    pmax = float(np.max(gauge_pressure))
    force = float(problem.width_m * np.sum(gauge_pressure) * solution.dx_m)
    q_out = float(problem.width_m * (solution.face_flux_m2_s[-1] - solution.face_flux_m2_s[0]))
    symmetry_scale = max(float(np.max(np.abs(gauge_pressure))), 1.0)
    symmetry = float(np.max(np.abs(gauge_pressure - gauge_pressure[::-1])) / symmetry_scale)
    return CaseMetrics(
        pmax_pa=pmax,
        force_n=force,
        impedance_n_s_m=force / problem.vp_m_s,
        q_out_m3_s=q_out,
        q_displaced_m3_s=exact.q_displaced_m3_s,
        pmax_relative_error=_relative_error(pmax, exact.pmax_pa),
        force_relative_error=_relative_error(force, exact.force_n),
        mass_relative_error=_relative_error(q_out, exact.q_displaced_m3_s),
        symmetry_relative_error=symmetry,
    )
