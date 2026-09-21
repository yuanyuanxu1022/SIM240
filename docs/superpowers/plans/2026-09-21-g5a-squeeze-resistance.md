# G5A Quasi-static Squeeze Resistance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and run a small, independently verified Python solver that converts the existing \(\Delta x=2.5\ \mathrm{nm}\) G3 transport closure into pressure, vertical load, and normalized squeeze impedance for nine discrete-height G5A cases.

**Architecture:** A pure numerical core will own the analytic and conservative one-dimensional finite-volume equations. A separate input layer will audit the frozen G3 CSV and construct the nine cases, while a reporting layer will write auditable CSV/Markdown/PNG artifacts. The command-line runner will orchestrate these units, write an independent exit code, and never invoke or modify OpenLB.

**Tech Stack:** Python 3.11, standard library (`csv`, `json`, `hashlib`, `logging`, `pathlib`, `unittest`), NumPy 2.4, Matplotlib 3.11; existing `sim240-analysis` Conda environment.

**Spec:** `docs/superpowers/specs/2026-09-21-g5a-squeeze-resistance-design.md`

## Global Constraints

- Read EX240 closure data only from `transport_database/G3_height_resistance.csv` and record its SHA-256.
- Accept only the micro-scale source grid `dx_nm = 2.5`; do not read, generate, or rerun 5.0 nm or 1.25 nm OpenLB cases.
- Evaluate only `height_nm = 50, 75, 125`; do not interpolate or extrapolate `K(h)`.
- Assume a locally uniform gap: at each frozen height the film thickness is a single constant `h` across the strip (no tilt, roughness, elastic deformation, or wedge), so the drainage gap is a parallel, height-uniform film whose height depends only on indenter displacement, not on strip coordinate `s`.
- Assume spatially uniform `K(h)`: at each height the mobility depends only on `h`, not on strip position `s`, so each height contributes a single scalar `K` per direction (`K_parallel`, `K_perp`) rather than an `s`-dependent field.
- Use the coordinate convention parallel = `+y`, perpendicular = `+x`, and wall-normal/downward loading = `z`.
- Use `L = W = 1.0e-3 m`, `mu = 1.0e-3 Pa s`, `Vp = 75.0e-9 m/s`, `p_out = 0 Pa`, and exactly `N = 401` control volumes.
- Compare exactly three models at each height: Smooth, EX240 parallel, and EX240 perpendicular.
- Keep constant-speed and constant-load studies separate; this plan implements constant speed only.
- Do not modify OpenLB core, G2/G3 outputs, or existing extraction scripts.
- Do not claim G5A mesh independence or micro-scale grid independence.
- Store generated run artifacts under `CASE/05_mesoscale/G5A_squeeze_resistance/results/<run_id>/`; do not stage result directories by default.

## Review Focus

- A CSV with a missing, duplicate, extra, or non-exact target height must fail `INPUT_GATE` rather than silently select a row; Task 3 adds these tests.
- Non-finite, zero, or negative `K`, `R`, geometry, viscosity, or speed values must raise a clear `ValueError`; Tasks 1 and 3 add these tests.
- Parallel/perpendicular columns must never be swapped; Task 3 pins the direction-to-column mapping and anisotropy identity in tests.
- A configuration using a source grid other than 2.5 nm, a height outside the frozen set, or `N != 401` must fail before solving; Tasks 1 and 3 add these tests.
- A failed mandatory gate or an output-writing error must produce a nonzero `exit_code.txt` and must never emit `RESULT_PASS: true`; Tasks 4 and 5 add these tests.

---

## File Map

Create the following focused subsystem:

```text
CASE/05_mesoscale/G5A_squeeze_resistance/
├── README.md                     # scope, equations, run command, evidence limits
├── config/
│   └── g5a_baseline.json         # frozen inputs and gate thresholds
├── g5a_solver.py                 # dataclasses, analytic solution, FV solution, metrics
├── g5a_inputs.py                 # config/CSV audit and nine-case construction
├── g5a_reporting.py              # CSV, manifest, report, log, and PNG generation
├── run_g5a.py                    # CLI orchestration and independent exit code
└── tests/
    ├── test_g5a_solver.py        # physics/numerics unit tests
    ├── test_g5a_inputs.py        # provenance and input-gate unit tests
    └── test_run_g5a.py           # output and end-to-end failure-path tests
```

No existing source file is modified. The only external runtime input is the frozen G3 transport CSV.

### Task 1: Frozen configuration and analytic reference model

**Files:**
- Create: `CASE/05_mesoscale/G5A_squeeze_resistance/config/g5a_baseline.json`
- Create: `CASE/05_mesoscale/G5A_squeeze_resistance/g5a_solver.py`
- Create: `CASE/05_mesoscale/G5A_squeeze_resistance/tests/test_g5a_solver.py`

**Interfaces:**
- Consumes: no code from later tasks.
- Produces: `SqueezeProblem`, `AnalyticMetrics`, `smooth_mobility(height_m)`, `analytic_pressure(s_m, problem, K_m3)`, and `analytic_metrics(problem, K_m3)`.

- [ ] **Step 1: Create the frozen JSON configuration**

Write exactly these physical values and thresholds:

```json
{
  "schema_version": 1,
  "source_grid_dx_nm": 2.5,
  "transport_database": "transport_database/G3_height_resistance.csv",
  "heights_nm": [50.0, 75.0, 125.0],
  "length_m": 0.001,
  "width_m": 0.001,
  "mu_pa_s": 0.001,
  "vp_m_s": 7.5e-8,
  "p_out_pa": 0.0,
  "n_cells": 401,
  "linearity_multipliers": [0.5, 1.0, 2.0],
  "thresholds": {
    "input_identity_relative": 1e-10,
    "symmetry_relative": 1e-12,
    "pmax_relative": 1e-6,
    "load_relative": 1e-4,
    "mass_relative": 1e-10,
    "linearity_relative": 1e-10,
    "direction_ratio_relative": 1e-4
  }
}
```

- [ ] **Step 2: Write failing analytic and validation tests**

Create `test_g5a_solver.py` with tests that pin units, formulas, and rejected inputs:

```python
import math
import unittest

import numpy as np

from g5a_solver import SqueezeProblem, analytic_metrics, analytic_pressure, smooth_mobility


class AnalyticModelTests(unittest.TestCase):
    def setUp(self):
        self.problem = SqueezeProblem(
            length_m=1.0e-3,
            width_m=1.0e-3,
            mu_pa_s=1.0e-3,
            vp_m_s=75.0e-9,
            p_out_pa=0.0,
            n_cells=401,
        )

    def test_smooth_mobility_is_h_cubed_over_twelve(self):
        self.assertAlmostEqual(smooth_mobility(75.0e-9), (75.0e-9) ** 3 / 12.0)

    def test_analytic_metrics_match_closed_form(self):
        K = 9.782423697043172e-23
        result = analytic_metrics(self.problem, K)
        expected_pmax = self.problem.mu_pa_s * self.problem.vp_m_s * self.problem.length_m**2 / (8.0 * K)
        expected_force = (
            self.problem.mu_pa_s
            * self.problem.vp_m_s
            * self.problem.width_m
            * self.problem.length_m**3
            / (12.0 * K)
        )
        self.assertAlmostEqual(result.pmax_pa, expected_pmax)
        self.assertAlmostEqual(result.force_n, expected_force)
        self.assertAlmostEqual(result.impedance_n_s_m, expected_force / self.problem.vp_m_s)
        self.assertAlmostEqual(result.q_displaced_m3_s, self.problem.width_m * self.problem.length_m * self.problem.vp_m_s)

    def test_pressure_is_symmetric_and_zero_at_outlets(self):
        K = 9.782423697043172e-23
        s = np.array([-self.problem.length_m / 2.0, 0.0, self.problem.length_m / 2.0])
        p = analytic_pressure(s, self.problem, K)
        self.assertAlmostEqual(p[0], self.problem.p_out_pa)
        self.assertAlmostEqual(p[2], self.problem.p_out_pa)
        self.assertGreater(p[1], p[0])
        self.assertAlmostEqual(p[0], p[2])

    def test_invalid_problem_or_mobility_is_rejected(self):
        with self.assertRaises(ValueError):
            SqueezeProblem(1e-3, 1e-3, 1e-3, 75e-9, 0.0, 201)
        with self.assertRaises(ValueError):
            analytic_metrics(self.problem, 0.0)
        with self.assertRaises(ValueError):
            smooth_mobility(float("nan"))
```

- [ ] **Step 3: Run the test and verify the expected failure**

Run:

```bash
cd CASE/05_mesoscale/G5A_squeeze_resistance
conda run --no-capture-output -n sim240-analysis python -m unittest tests.test_g5a_solver -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'g5a_solver'`.

- [ ] **Step 4: Implement the analytic model and strict problem validation**

Implement immutable dataclasses and formula functions in `g5a_solver.py`:

```python
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
```

- [ ] **Step 5: Run the analytic unit tests**

Run the same `unittest` command from Step 3.

Expected: all `AnalyticModelTests` PASS.

- [ ] **Step 6: Commit Task 1 only**

Before committing, run `git status --short` and `git diff --check`. Then stage only:

```bash
git add CASE/05_mesoscale/G5A_squeeze_resistance/config/g5a_baseline.json
git add CASE/05_mesoscale/G5A_squeeze_resistance/g5a_solver.py
git add CASE/05_mesoscale/G5A_squeeze_resistance/tests/test_g5a_solver.py
git commit -m "feat: add G5A analytic squeeze model"
```

### Task 2: Conservative finite-volume pressure solver and physics gates

**Files:**
- Modify: `CASE/05_mesoscale/G5A_squeeze_resistance/g5a_solver.py`
- Modify: `CASE/05_mesoscale/G5A_squeeze_resistance/tests/test_g5a_solver.py`

**Interfaces:**
- Consumes: `SqueezeProblem`, `analytic_pressure()`, and `analytic_metrics()` from Task 1.
- Produces: `NumericalSolution`, `CaseMetrics`, `solve_uniform_k(problem, K_m3)`, and `evaluate_solution(problem, K_m3, solution)`.

- [ ] **Step 1: Add failing finite-volume, mass, symmetry, and linearity tests**

Append tests that require a conservative solution and frozen numerical gates:

```python
from dataclasses import replace

from g5a_solver import evaluate_solution, solve_uniform_k


class FiniteVolumeTests(unittest.TestCase):
    def setUp(self):
        self.problem = SqueezeProblem(1e-3, 1e-3, 1e-3, 75e-9, 0.0, 401)
        self.K = 9.782423697043172e-23

    def test_fv_solution_matches_pressure_load_and_mass_gates(self):
        solution = solve_uniform_k(self.problem, self.K)
        metrics = evaluate_solution(self.problem, self.K, solution)
        self.assertLess(metrics.pmax_relative_error, 1e-6)
        self.assertLess(metrics.force_relative_error, 1e-4)
        self.assertLess(metrics.mass_relative_error, 1e-10)
        self.assertLess(metrics.symmetry_relative_error, 1e-12)
        self.assertTrue(np.all(solution.pressure_pa >= self.problem.p_out_pa))

    def test_face_flux_has_correct_outward_signs(self):
        solution = solve_uniform_k(self.problem, self.K)
        self.assertLess(solution.face_flux_m2_s[0], 0.0)
        self.assertGreater(solution.face_flux_m2_s[-1], 0.0)

    def test_impedance_is_independent_of_reference_speed(self):
        impedances = []
        for factor in (0.5, 1.0, 2.0):
            p = replace(self.problem, vp_m_s=self.problem.vp_m_s * factor)
            s = solve_uniform_k(p, self.K)
            impedances.append(evaluate_solution(p, self.K, s).impedance_n_s_m)
        spread = (max(impedances) - min(impedances)) / impedances[1]
        self.assertLess(spread, 1e-10)
```

- [ ] **Step 2: Run only the new test class and verify failure**

```bash
cd CASE/05_mesoscale/G5A_squeeze_resistance
conda run --no-capture-output -n sim240-analysis python -m unittest tests.test_g5a_solver.FiniteVolumeTests -v
```

Expected: FAIL because `solve_uniform_k` and `evaluate_solution` do not exist.

- [ ] **Step 3: Implement the cell-centred conservative finite-volume solve**

Add these dataclasses and operations to `g5a_solver.py`. The first and last matrix rows use a one-sided quadratic flux at the half-cell Dirichlet outlet, which is exact for the quadratic analytic solution so the discrete pressure reproduces `p(s)` to machine precision (the simpler `(3, -1)` half-cell stencil errs by ~`4/N^2`, which fails the `1e-6` pmax gate at `N=401`):

```python
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
```

- [ ] **Step 4: Run all solver tests and inspect numerical values**

```bash
cd CASE/05_mesoscale/G5A_squeeze_resistance
conda run --no-capture-output -n sim240-analysis python -m unittest tests.test_g5a_solver -v
```

Expected: all tests PASS; no NaN/Inf; left outlet flux negative, right outlet flux positive.

- [ ] **Step 5: Commit Task 2 only**

```bash
git status --short
git diff --check
git add CASE/05_mesoscale/G5A_squeeze_resistance/g5a_solver.py
git add CASE/05_mesoscale/G5A_squeeze_resistance/tests/test_g5a_solver.py
git commit -m "feat: solve conservative G5A pressure field"
```

### Task 3: G3 provenance audit and nine-case construction

**Files:**
- Create: `CASE/05_mesoscale/G5A_squeeze_resistance/g5a_inputs.py`
- Create: `CASE/05_mesoscale/G5A_squeeze_resistance/tests/test_g5a_inputs.py`

**Interfaces:**
- Consumes: `SqueezeProblem` and `smooth_mobility()` from Task 1.
- Produces: `ModelConfig`, `CaseDefinition`, `load_config(path)`, `load_transport_cases(csv_path, config)`, and `build_nine_cases(config, transport_rows)`.

- [ ] **Step 1: Write failing input-audit and direction-mapping tests**

Use `tempfile.TemporaryDirectory()` and write fixture CSVs with `csv.DictWriter`. Pin exact source grid, heights, identity checks, and column mapping:

```python
import csv
import json
import math
from pathlib import Path
import tempfile
import unittest

from g5a_inputs import build_nine_cases, load_config, load_transport_cases


VALID_ROWS = [
    {"height_nm": 50.0, "R_parallel": 1.7524577489058236e19, "R_perp": 6.973942793067436e19,
     "K_parallel": 5.706271666888214e-23, "K_perp": 1.433909095144954e-23,
     "anisotropy": 3.9795212166579965},
    {"height_nm": 75.0, "R_parallel": 1.022241553800475e19, "R_perp": 2.280349074098442e19,
     "K_parallel": 9.782423697043172e-23, "K_perp": 4.3852935121144107e-23,
     "anisotropy": 2.2307340819991053},
    {"height_nm": 125.0, "R_parallel": 3.7632838400903424e18, "R_perp": 5.410847947764791e18,
     "K_parallel": 2.6572537243855455e-22, "K_perp": 1.8481391634985746e-22,
     "anisotropy": 1.4377995861281876},
]


class InputAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config_path = self.root / "g5a.json"
        self.csv_path = self.root / "G3_height_resistance.csv"
        self.config = {
            "schema_version": 1,
            "source_grid_dx_nm": 2.5,
            "transport_database": str(self.csv_path),
            "heights_nm": [50.0, 75.0, 125.0],
            "length_m": 1e-3,
            "width_m": 1e-3,
            "mu_pa_s": 1e-3,
            "vp_m_s": 75e-9,
            "p_out_pa": 0.0,
            "n_cells": 401,
            "linearity_multipliers": [0.5, 1.0, 2.0],
            "thresholds": {
                "input_identity_relative": 1e-10,
                "symmetry_relative": 1e-12,
                "pmax_relative": 1e-6,
                "load_relative": 1e-4,
                "mass_relative": 1e-10,
                "linearity_relative": 1e-10,
                "direction_ratio_relative": 1e-4,
            },
        }

    def tearDown(self):
        self.tmp.cleanup()

    def write_config(self, **overrides):
        payload = dict(self.config)
        payload.update(overrides)
        self.config_path.write_text(json.dumps(payload), encoding="utf-8")

    def write_rows(self, rows):
        fields = ["height_nm", "R_parallel", "R_perp", "K_parallel", "K_perp", "anisotropy"]
        with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_config_rejects_wrong_source_grid_or_n(self):
        self.write_config(source_grid_dx_nm=5.0)
        with self.assertRaisesRegex(ValueError, "source_grid_dx_nm"):
            load_config(self.config_path)
        self.write_config(n_cells=201)
        with self.assertRaisesRegex(ValueError, "n_cells"):
            load_config(self.config_path)

    def test_valid_database_builds_exactly_nine_cases(self):
        self.write_config()
        self.write_rows(VALID_ROWS)
        config = load_config(self.config_path)
        rows = load_transport_cases(self.csv_path, config)
        cases = build_nine_cases(config, rows)
        self.assertEqual(len(cases), 9)
        self.assertEqual([case.model for case in cases].count("smooth"), 3)
        self.assertEqual([case.model for case in cases].count("ex240"), 6)

    def test_parallel_and_perpendicular_use_the_correct_columns(self):
        self.write_config()
        self.write_rows(VALID_ROWS)
        config = load_config(self.config_path)
        cases = build_nine_cases(config, load_transport_cases(self.csv_path, config))
        by_key = {(case.height_nm, case.direction): case for case in cases}
        self.assertEqual(by_key[(75.0, "parallel")].K_m3, VALID_ROWS[1]["K_parallel"])
        self.assertEqual(by_key[(75.0, "perpendicular")].K_m3, VALID_ROWS[1]["K_perp"])

    def test_duplicate_missing_extra_or_nonfinite_rows_fail(self):
        self.write_config()
        bad_nonfinite = [dict(row) for row in VALID_ROWS]
        bad_nonfinite[1]["K_parallel"] = float("nan")
        extra = dict(VALID_ROWS[0])
        extra["height_nm"] = 100.0
        fixtures = {
            "duplicate": VALID_ROWS + [dict(VALID_ROWS[1])],
            "missing": [VALID_ROWS[0], VALID_ROWS[2]],
            "extra": VALID_ROWS + [extra],
            "nonfinite": bad_nonfinite,
        }
        config = load_config(self.config_path)
        for name, rows in fixtures.items():
            with self.subTest(name=name):
                self.write_rows(rows)
                with self.assertRaises(ValueError):
                    load_transport_cases(self.csv_path, config)

    def test_rk_and_anisotropy_identity_failures_are_detected(self):
        self.write_config()
        config = load_config(self.config_path)
        bad_rk = [dict(row) for row in VALID_ROWS]
        bad_rk[0]["R_parallel"] *= 1.000001
        self.write_rows(bad_rk)
        with self.assertRaisesRegex(ValueError, "R_parallel.*K_parallel"):
            load_transport_cases(self.csv_path, config)
        bad_a = [dict(row) for row in VALID_ROWS]
        bad_a[2]["anisotropy"] *= 1.000001
        self.write_rows(bad_a)
        with self.assertRaisesRegex(ValueError, "anisotropy"):
            load_transport_cases(self.csv_path, config)
```

- [ ] **Step 2: Run the input tests and verify failure**

```bash
cd CASE/05_mesoscale/G5A_squeeze_resistance
conda run --no-capture-output -n sim240-analysis python -m unittest tests.test_g5a_inputs -v
```

Expected: FAIL because `g5a_inputs` does not exist.

- [ ] **Step 3: Implement strict configuration and CSV loading**

Implement these immutable interfaces in `g5a_inputs.py`:

```python
@dataclass(frozen=True)
class ModelConfig:
    source_grid_dx_nm: float
    transport_database: str
    heights_nm: tuple[float, ...]
    problem: SqueezeProblem
    linearity_multipliers: tuple[float, ...]
    thresholds: dict[str, float]


@dataclass(frozen=True)
class CaseDefinition:
    height_nm: float
    model: str
    direction: str
    K_m3: float
    R_input_pa_s_m3: float


def load_config(path: Path) -> ModelConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw["schema_version"] != 1:
        raise ValueError("schema_version must equal 1")
    if float(raw["source_grid_dx_nm"]) != 2.5:
        raise ValueError("source_grid_dx_nm must equal 2.5")
    heights = tuple(float(x) for x in raw["heights_nm"])
    if heights != (50.0, 75.0, 125.0):
        raise ValueError("heights_nm must equal [50.0, 75.0, 125.0]")
    problem = SqueezeProblem(
        float(raw["length_m"]),
        float(raw["width_m"]),
        float(raw["mu_pa_s"]),
        float(raw["vp_m_s"]),
        float(raw["p_out_pa"]),
        int(raw["n_cells"]),
    )
    return ModelConfig(
        source_grid_dx_nm=2.5,
        transport_database=str(raw["transport_database"]),
        heights_nm=heights,
        problem=problem,
        linearity_multipliers=tuple(float(x) for x in raw["linearity_multipliers"]),
        thresholds={str(k): float(v) for k, v in raw["thresholds"].items()},
    )
```

`load_transport_cases()` must:

1. require the six named CSV columns;
2. parse every number with `float()` and reject non-finite values;
3. require the exact height set `{50.0, 75.0, 125.0}` with no duplicates;
4. require positive `K` and `R`;
5. check `abs(R*K/mu - 1) <= input_identity_relative` for both directions;
6. check the database anisotropy against `K_parallel/K_perp`;
7. return typed rows without changing their values.

`build_nine_cases()` must create cases in deterministic order: height ascending, then `smooth`, `parallel`, `perpendicular`. For Smooth use `K=h^3/12` and set `R_input_pa_s_m3=mu/K`; for EX240 map parallel only to `K_parallel/R_parallel` and perpendicular only to `K_perp/R_perp`.

- [ ] **Step 4: Run all input tests and the complete unit suite**

```bash
cd CASE/05_mesoscale/G5A_squeeze_resistance
conda run --no-capture-output -n sim240-analysis python -m unittest discover -s tests -v
```

Expected: all Task 1–3 tests PASS.

- [ ] **Step 5: Commit Task 3 only**

```bash
git status --short
git diff --check
git add CASE/05_mesoscale/G5A_squeeze_resistance/g5a_inputs.py
git add CASE/05_mesoscale/G5A_squeeze_resistance/tests/test_g5a_inputs.py
git commit -m "feat: audit G5A transport inputs"
```

### Task 4: Evidence writer, gates, figures, and failure-safe exit code

**Files:**
- Create: `CASE/05_mesoscale/G5A_squeeze_resistance/g5a_reporting.py`
- Create: `CASE/05_mesoscale/G5A_squeeze_resistance/run_g5a.py`
- Create: `CASE/05_mesoscale/G5A_squeeze_resistance/tests/test_run_g5a.py`

**Interfaces:**
- Consumes: `ModelConfig`, `CaseDefinition`, `load_config()`, `load_transport_cases()`, `build_nine_cases()`, `solve_uniform_k()`, and `evaluate_solution()`.
- Produces: `run_model(config_path, repo_root, results_root, run_id) -> Path`, three CSV/reporting functions, three figure functions, `main(argv=None) -> int`, and the complete run evidence directory.

- [ ] **Step 1: Write failing reporting and failure-path tests**

Create temporary config/CSV fixtures and test the externally visible contract:

```python
import csv
import json
import math
from pathlib import Path
import tempfile
import unittest

from run_g5a import main


VALID_ROWS = [
    [50.0, 1.7524577489058236e19, 6.973942793067436e19, 5.706271666888214e-23, 1.433909095144954e-23, 3.9795212166579965],
    [75.0, 1.022241553800475e19, 2.280349074098442e19, 9.782423697043172e-23, 4.3852935121144107e-23, 2.2307340819991053],
    [125.0, 3.7632838400903424e18, 5.410847947764791e18, 2.6572537243855455e-22, 1.8481391634985746e-22, 1.4377995861281876],
]


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "transport_database").mkdir()
        self.csv_path = self.root / "transport_database" / "G3_height_resistance.csv"
        self.config_path = self.root / "g5a.json"
        self.results_root = self.root / "results"
        self.write_rows(VALID_ROWS)
        config = {
            "schema_version": 1,
            "source_grid_dx_nm": 2.5,
            "transport_database": "transport_database/G3_height_resistance.csv",
            "heights_nm": [50.0, 75.0, 125.0],
            "length_m": 1e-3,
            "width_m": 1e-3,
            "mu_pa_s": 1e-3,
            "vp_m_s": 75e-9,
            "p_out_pa": 0.0,
            "n_cells": 401,
            "linearity_multipliers": [0.5, 1.0, 2.0],
            "thresholds": {
                "input_identity_relative": 1e-10,
                "symmetry_relative": 1e-12,
                "pmax_relative": 1e-6,
                "load_relative": 1e-4,
                "mass_relative": 1e-10,
                "linearity_relative": 1e-10,
                "direction_ratio_relative": 1e-4,
            },
        }
        self.config_path.write_text(json.dumps(config), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def write_rows(self, rows):
        fields = ["height_nm", "R_parallel", "R_perp", "K_parallel", "K_perp", "anisotropy"]
        with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(fields)
            writer.writerows(rows)

    def run_cli(self, run_id):
        return main([
            "--config", str(self.config_path),
            "--repo-root", str(self.root),
            "--results-root", str(self.results_root),
            "--run-id", run_id,
        ])

    def test_successful_run_writes_complete_evidence(self):
        self.assertEqual(self.run_cli("unit-test-pass"), 0)
        run_dir = self.results_root / "unit-test-pass"
        required = {
            "run.log", "exit_code.txt", "input_manifest.json", "case_results.csv",
            "pressure_profiles.csv", "validation_report.md",
            "Figure_G5_pressure_profiles.png", "Figure_G5_squeeze_impedance_vs_h.png",
            "Figure_G5_directional_ratio_vs_h.png",
        }
        self.assertTrue(required.issubset({path.name for path in run_dir.iterdir()}))
        with (run_dir / "case_results.csv").open(newline="", encoding="utf-8") as handle:
            self.assertEqual(len(list(csv.DictReader(handle))), 9)
        self.assertIn("RESULT_PASS: true", (run_dir / "validation_report.md").read_text(encoding="utf-8"))
        self.assertEqual((run_dir / "exit_code.txt").read_text(encoding="utf-8"), "0\n")

    def test_manifest_contains_input_hash_and_fixed_grid(self):
        self.assertEqual(self.run_cli("unit-test-manifest"), 0)
        manifest = json.loads((self.results_root / "unit-test-manifest" / "input_manifest.json").read_text(encoding="utf-8"))
        self.assertRegex(manifest["transport_database_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(manifest["source_grid_dx_nm"], 2.5)
        self.assertEqual(manifest["n_cells"], 401)
        self.assertEqual(manifest["heights_nm"], [50.0, 75.0, 125.0])

    def test_failed_input_gate_writes_nonzero_exit_and_no_pass(self):
        self.write_rows(VALID_ROWS + [VALID_ROWS[1]])
        code = self.run_cli("unit-test-fail")
        run_dir = self.results_root / "unit-test-fail"
        self.assertNotEqual(code, 0)
        self.assertNotEqual((run_dir / "exit_code.txt").read_text(encoding="utf-8"), "0\n")
        report = (run_dir / "validation_report.md").read_text(encoding="utf-8")
        self.assertNotIn("RESULT_PASS: true", report)

    def test_csv_outputs_are_finite_and_direction_ratios_close(self):
        self.assertEqual(self.run_cli("unit-test-ratios"), 0)
        with (self.results_root / "unit-test-ratios" / "case_results.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        numeric = ["K_m3", "pmax_num_Pa", "Fz_num_N", "CF_num_N_s_m", "Qout_m3_s", "mass_rel_error"]
        for row in rows:
            self.assertTrue(all(math.isfinite(float(row[key])) for key in numeric))
        by_key = {(float(row["height_nm"]), row["direction"]): row for row in rows}
        for height in (50.0, 75.0, 125.0):
            parallel = by_key[(height, "parallel")]
            perpendicular = by_key[(height, "perpendicular")]
            cf_ratio = float(perpendicular["CF_num_N_s_m"]) / float(parallel["CF_num_N_s_m"])
            k_ratio = float(parallel["K_m3"]) / float(perpendicular["K_m3"])
            self.assertLess(abs(cf_ratio / k_ratio - 1.0), 1e-4)
```

- [ ] **Step 2: Run the runner tests and verify failure**

```bash
cd CASE/05_mesoscale/G5A_squeeze_resistance
MPLCONFIGDIR=/tmp/sim240-mpl-cache conda run --no-capture-output -n sim240-analysis \
  python -m unittest tests.test_run_g5a -v
```

Expected: FAIL because the reporting and runner modules do not exist.

- [ ] **Step 3: Implement deterministic case evaluation and gate aggregation**

In `run_g5a.py`, implement a pure orchestration function before the CLI. For each of nine cases:

1. call `solve_uniform_k()`;
2. call `evaluate_solution()`;
3. calculate exact analytic values;
4. evaluate finite, pressure, symmetry, pmax, force, mass, and direction-ratio gates;
5. repeat at `0.5Vp`, `Vp`, and `2Vp` for the linearity gate;
6. store one flat result row plus the 401-point profile rows.

Use a result record with stable keys matching the spec:

```python
{
    "run_id": run_id,
    "height_nm": case.height_nm,
    "model": case.model,
    "direction": case.direction,
    "K_m3": case.K_m3,
    "R_input_pa_s_m3": case.R_input_pa_s_m3,
    "Vp_m_s": config.problem.vp_m_s,
    "N": config.problem.n_cells,
    "pmax_num_Pa": metrics.pmax_pa,
    "pmax_exact_Pa": exact.pmax_pa,
    "pmax_rel_error": metrics.pmax_relative_error,
    "Fz_num_N": metrics.force_n,
    "Fz_exact_N": exact.force_n,
    "Fz_rel_error": metrics.force_relative_error,
    "CF_num_N_s_m": metrics.impedance_n_s_m,
    "CF_exact_N_s_m": exact.impedance_n_s_m,
    "Qout_m3_s": metrics.q_out_m3_s,
    "Qdisplaced_m3_s": metrics.q_displaced_m3_s,
    "mass_rel_error": metrics.mass_relative_error,
    "status": "PASS" if case_pass else "FAIL",
}
```

Aggregate named gates exactly as `INPUT_GATE`, `NUMERICAL_GATE`, `ANALYTIC_GATE`, `MASS_GATE`, `LINEARITY_GATE`, and `RESULT_PASS`. `RESULT_PASS` is true only if all mandatory named gates and all nine case rows pass.

- [ ] **Step 4: Implement evidence files and 600 dpi figures**

In `g5a_reporting.py`, provide narrowly scoped functions:

```python
import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


CASE_RESULT_FIELDS = [
    "run_id", "height_nm", "model", "direction", "K_m3", "R_input_pa_s_m3",
    "Vp_m_s", "N", "pmax_num_Pa", "pmax_exact_Pa", "pmax_rel_error",
    "Fz_num_N", "Fz_exact_N", "Fz_rel_error",
    "CF_num_N_s_m", "CF_exact_N_s_m", "Qout_m3_s", "Qdisplaced_m3_s",
    "mass_rel_error", "status",
]

PROFILE_FIELDS = ["run_id", "height_nm", "model", "direction", "centers_m", "pressure_pa"]

GATE_ORDER = ["INPUT_GATE", "NUMERICAL_GATE", "ANALYTIC_GATE", "MASS_GATE", "LINEARITY_GATE", "RESULT_PASS"]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_case_results(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CASE_RESULT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_profiles(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROFILE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_validation_report(path: Path, gates: dict[str, bool], metadata: dict[str, object]) -> None:
    lines = ["# G5A Validation Report", ""]
    for gate in GATE_ORDER:
        lines.append(f"{gate}: {str(bool(gates.get(gate, False))).lower()}")
    lines += [
        "",
        f"INPUT_CLOSURE_STATUS: {metadata.get('input_closure_status', 'CANDIDATE_FIXED_GRID')}",
        f"SOURCE_GRID_DX_NM: {metadata.get('source_grid_dx_nm', 2.5)}",
        f"G5A_N_CELLS: {metadata.get('n_cells', 401)}",
        "FINAL_GRID_INDEPENDENT_CLOSURE: false",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_pressure_figure(path: Path, profile_rows: list[dict[str, object]]) -> None:
    import itertools

    fig, ax = plt.subplots()
    key = lambda row: (row["model"], row["height_nm"], row["direction"])
    for (model, height_nm, direction), group in itertools.groupby(
        sorted(profile_rows, key=key), key=key
    ):
        rows = list(group)
        ax.plot(
            [row["centers_m"] for row in rows],
            [row["pressure_pa"] for row in rows],
            label=f"{model} {direction} h={height_nm} nm",
        )
    ax.set_xlabel("s (m)")
    ax.set_ylabel("pressure (Pa)")
    ax.legend()
    fig.savefig(path, dpi=600, bbox_inches="tight")
    plt.close(fig)


def make_impedance_figure(path: Path, case_rows: list[dict[str, object]]) -> None:
    fig, ax = plt.subplots()
    for model in sorted({row["model"] for row in case_rows}):
        xs = [row["height_nm"] for row in case_rows if row["model"] == model]
        ys = [row["CF_num_N_s_m"] for row in case_rows if row["model"] == model]
        ax.plot(xs, ys, marker="o", label=model)
    ax.set_xlabel("height (nm)")
    ax.set_ylabel("CF (N s / m)")
    ax.legend()
    fig.savefig(path, dpi=600, bbox_inches="tight")
    plt.close(fig)


def make_direction_ratio_figure(path: Path, case_rows: list[dict[str, object]]) -> None:
    fig, ax = plt.subplots()
    by_key = {(row["height_nm"], row["direction"]): row for row in case_rows}
    heights = sorted({row["height_nm"] for row in case_rows})
    ratios = [
        float(by_key[(h, "perpendicular")]["CF_num_N_s_m"]) / float(by_key[(h, "parallel")]["CF_num_N_s_m"])
        for h in heights
    ]
    ax.plot(heights, ratios, marker="o")
    ax.set_xlabel("height (nm)")
    ax.set_ylabel("CF_perp / CF_parallel")
    fig.savefig(path, dpi=600, bbox_inches="tight")
    plt.close(fig)
```

Required files in every successful run directory:

```text
run.log
exit_code.txt
input_manifest.json
case_results.csv
pressure_profiles.csv
validation_report.md
Figure_G5_pressure_profiles.png
Figure_G5_squeeze_impedance_vs_h.png
Figure_G5_directional_ratio_vs_h.png
```

Call `figure.savefig(path, dpi=600, bbox_inches="tight")`, close every figure, and derive every plotted number from the in-memory rows that are also written to CSV.

The validation report must include:

```text
INPUT_CLOSURE_STATUS: CANDIDATE_FIXED_GRID
SOURCE_GRID_DX_NM: 2.5
G5A_N_CELLS: 401
FINAL_GRID_INDEPENDENT_CLOSURE: false
```

- [ ] **Step 5: Implement independent exit-code behavior**

`main()` must create the run directory and logging target before input validation. Use `try/except` only at the command boundary:

```python
def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_dir = prepare_run_directory(args.results_root, args.run_id)
    exit_code = 1
    try:
        run_model(args.config, args.repo_root, args.results_root, args.run_id)
        exit_code = 0
    except Exception:
        logging.exception("G5A run failed")
        write_failed_report_if_missing(run_dir)
        exit_code = 3
    finally:
        (run_dir / "exit_code.txt").write_text(f"{exit_code}\n", encoding="utf-8")
    return exit_code
```

End the module with `raise SystemExit(main())`. Never report `RESULT_PASS: true` in an exception path.

- [ ] **Step 6: Run runner tests and the full suite**

```bash
cd CASE/05_mesoscale/G5A_squeeze_resistance
MPLCONFIGDIR=/tmp/sim240-mpl-cache conda run --no-capture-output -n sim240-analysis \
  python -m unittest discover -s tests -v
```

Expected: all tests PASS and temporary output directories contain complete evidence.

- [ ] **Step 7: Commit Task 4 only**

```bash
git status --short
git diff --check
git add CASE/05_mesoscale/G5A_squeeze_resistance/g5a_reporting.py
git add CASE/05_mesoscale/G5A_squeeze_resistance/run_g5a.py
git add CASE/05_mesoscale/G5A_squeeze_resistance/tests/test_run_g5a.py
git commit -m "feat: add auditable G5A model runner"
```

### Task 5: User documentation, real nine-case run, and final evidence audit

**Files:**
- Create: `CASE/05_mesoscale/G5A_squeeze_resistance/README.md`
- Runtime only: `CASE/05_mesoscale/G5A_squeeze_resistance/results/<run_id>/` (the nine evidence files listed in Task 4, Step 4)

**Interfaces:**
- Consumes: all Task 1–4 interfaces and the real `transport_database/G3_height_resistance.csv`.
- Produces: beginner-readable instructions and one complete real G5A evidence directory.

- [ ] **Step 1: Write the beginner-readable README**

Document, without assuming LBM knowledge:

1. `z` is wall-normal loading, not a D3Q19 population direction;
2. `dx=2.5 nm` belongs to the input OpenLB closure, while `N=401` belongs to the 1 mm G5A strip;
3. the equations \(q=-(K/\mu)dp/ds\), \(dq/ds=V_p\), and \(C_F=F_z/V_p\);
4. the nine cases and constant-speed interpretation;
5. the exact run command;
6. every output file and gate;
7. the fixed-grid and single-phase evidence limits.

Use this run command from the repository root:

```bash
MPLCONFIGDIR=/tmp/sim240-mpl-cache \
conda run --no-capture-output -n sim240-analysis \
python CASE/05_mesoscale/G5A_squeeze_resistance/run_g5a.py \
  --config CASE/05_mesoscale/G5A_squeeze_resistance/config/g5a_baseline.json \
  --repo-root .
```

- [ ] **Step 2: Run the complete automated test suite one final time**

```bash
cd CASE/05_mesoscale/G5A_squeeze_resistance
MPLCONFIGDIR=/tmp/sim240-mpl-cache conda run --no-capture-output -n sim240-analysis \
  python -m unittest discover -s tests -v
```

Expected: zero failures and zero errors.

- [ ] **Step 3: Run the real nine-case model once**

From the repository root, execute the README command exactly. This is a short Python calculation, not an OpenLB simulation and not a long-running job.

Expected: the CLI prints the run directory and exits 0.

- [ ] **Step 4: Audit the real evidence without trusting console output**

Resolve the printed run directory, then verify:

```bash
test "$(cat CASE/05_mesoscale/G5A_squeeze_resistance/results/<run_id>/exit_code.txt)" = "0"
grep -E '^(INPUT_GATE|NUMERICAL_GATE|ANALYTIC_GATE|MASS_GATE|LINEARITY_GATE|RESULT_PASS):' \
  CASE/05_mesoscale/G5A_squeeze_resistance/results/<run_id>/validation_report.md
```

Expected: all six gates print `true`. Then read `case_results.csv` with Python and assert exactly 9 rows, finite numeric columns, all row statuses `PASS`, and all three figure files are non-empty PNG files.

- [ ] **Step 5: Perform the scientific sanity check**

Using `case_results.csv`, verify all three statements directly from computed values:

1. `CF_perpendicular > CF_parallel` at 50, 75, and 125 nm;
2. both directional impedances decrease monotonically with height;
3. `CF_perpendicular/CF_parallel` matches 3.9795212167, 2.2307340820, and 1.4377995861 within the frozen direction-ratio threshold.

Also verify that all models at fixed height have the same `Qdisplaced_m3_s`; do not interpret constant-speed output as different total drainage volume.

- [ ] **Step 6: Commit documentation only; leave results local**

```bash
git status --short
git diff --check
git add CASE/05_mesoscale/G5A_squeeze_resistance/README.md
git commit -m "docs: explain G5A squeeze resistance workflow"
```

Do not stage `CASE/05_mesoscale/G5A_squeeze_resistance/results/`.

- [ ] **Step 7: Final handoff checks**

Record in the final report:

- completed cases: 9/9 or the exact failed subset;
- real result directory and run ID;
- all named gate values;
- pressure/load/impedance trends;
- direction ratios;
- `INPUT_CLOSURE_STATUS: CANDIDATE_FIXED_GRID`;
- `FINAL_GRID_INDEPENDENT_CLOSURE: false`;
- an explicit statement that no OpenLB case was rerun and no OpenLB core file was modified.

Before any completion claim, run `git status --short`, inspect the scoped diff, and invoke `superpowers:verification-before-completion`.
