# Case01-Bouzidi Short-Test Configuration

## Scope

- Purpose: isolated boundary implementation diagnostic derived from Case01.
- Formal simulation: **NO**.
- Time integration: exactly 20 short-test steps; no convergence or acceptance claim.
- Frozen protocol modification: **NO**.
- Existing Case01 source/results modification: **NO**.

## Frozen parameters retained

- Geometry: `Lx = Ly = 240 nm`, `H = 75 nm`.
- Lattice: `D3Q19<FORCE>`.
- Collision: `ForcedBGK`.
- `dx = 5 nm`.
- `dt = 1.0e-11 s`.
- `tau = 1.7` (`omega = 0.5882352941176471`).
- Body acceleration: `ay = 1.0e5 m/s²`; `ax = az = 0`.
- Fluid: `rho = 1000 kg/m³`, `nu = 1.0e-6 m²/s`.
- Periodicity: x and y periodic; z non-periodic.

## Boundary diagnostic change

- Lower and upper z walls use OpenLB 1.8r1
  `setBouzidiBoundary<T, DESCRIPTOR, BouzidiPostProcessor>`.
- Analytical channel surfaces are exactly `z = 0` and `z = H`.
- Wall-link intersections are computed by an exact planar distance override;
  the default `IndicatorCuboid3D` bisection tolerance is not used.
- In-plane margins in the analytical cuboid prevent periodic x/y side faces from
  being selected by diagonal wall links.
- Material overlap is explicitly synchronized after direct core assignment so
  diagonal wall links crossing the x/y periodic seams see wrapped materials.
- Expected valid wall-link distance: `q = 0.5` for every fluid-solid link.
- A pre-installation audit distinguishes legitimate `q=0.5` from OpenLB
  fallback-to-0.5 paths.

## Required short-test outputs

- `boundary_audit.txt`: q range, q=0.5 counts, installed-link counts, fallback counts.
- `boundary_anomalies.csv`: resolved pre-sync seam evidence and any unresolved
  post-install link, including coordinates, directions, materials and q values.
- `boundary_direction_summary.csv`: theoretical, seam, installed and fallback
  counts for each D3Q19 wall-crossing direction.
- `diagnostics.csv`: 0--20 step history, Jy, RJ, wall-adjacent velocity, Mach,
  density and material-1 mass.
- `velocity_profile.csv`: numerical short-test and steady analytical profiles.
- `result.txt`: compact q, wall-adjacent velocity, Jy, RJ and analytical errors.
- `run.log`, `exit_code.txt`, `run_manifest.txt`: execution provenance.

Analytical errors after 20 steps are transient diagnostic values only and must
not be interpreted as steady-state validation or Gate1 acceptance evidence.
