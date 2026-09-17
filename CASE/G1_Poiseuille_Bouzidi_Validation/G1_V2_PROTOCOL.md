# G1 Poiseuille Bouzidi Validation Protocol

## Scientific question

Can OpenLB D3Q19 + ForcedBGK + an exact-planar Bouzidi wall predict the hydraulic mobility of a 75 nm smooth channel with controlled force, grid and relaxation-time errors?

## Protected baseline

- `Lx = Ly = 240 nm`, `H = 75 nm`.
- D3Q19 with `descriptors::FORCE` and `ForcedBGK`.
- Baseline `dx = 5 nm`, `dt = 1e-11 s`, `tau = 1.7`, `ay = 1e5 m/s2`.
- x/y periodic; exact no-slip planes at `z=0` and `z=75 nm`.
- The analytic formula, physical height, sampled velocity and acceptance limits are frozen.

The only baseline boundary change relative to the original Case01 is
`boundary::BounceBack` to
`setBouzidiBoundary<T,DESCRIPTOR,BouzidiPostProcessor>`.

For a controlled grid study, physical viscosity and `tau=1.7` are fixed, so

$$
dt=\frac{(\tau-0.5)dx^2}{3\nu}.
$$

Consequently, `dt=1e-11 s` is retained exactly at the baseline `dx=5 nm`, while grid-study time steps scale with `dx^2`. Keeping both `dt` and `tau` fixed while changing `dx` is mathematically impossible for the same physical viscosity.

## Matrix

| Group | Cases |
|---|---|
| Force | `G1-a1: 5e4`, `G1-a2: 1e5`, `G1-a3: 2e5 m/s2` at dx=5 nm, tau=1.7 |
| Grid | `G1-dx10`, `G1-dx5`, `G1-dx2p5` at ay=1e5 m/s2, tau=1.7 |
| Tau | `G1-tau0p8`, `G1-tau1p0`, `G1-tau1p7` at dx=5 nm, ay=1e5 m/s2 |

Repeated baseline points are run independently to retain one evidence directory per requested Case.

## Outputs and gates

Each steady directory contains `diagnostics.csv`, `velocity_profile.csv`,
`result_summary.csv`, `result.txt`, `boundary_audit.txt`, `run.log`,
`run_manifest.txt` and `exit_code.txt`.

- material-1 maximum mass relative error `< 1e-10`;
- maximum Mach `< 0.05`;
- velocity-profile L2 error `< 2%`;
- mean constant offset / analytic maximum `< 2%`;
- mobility error `< 2%`;
- force linearity `R2 >= 0.999999` and intercept / maximum J `<= 1%`;
- grid error must decrease monotonically as dx decreases, and the finest grid must be below 2%.

A nonzero exit code caused by a frozen acceptance failure is retained as FAIL evidence. No velocity offset is subtracted.
