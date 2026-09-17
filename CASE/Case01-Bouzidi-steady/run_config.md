# Case01-Bouzidi Steady Validation Configuration

## Scope

- Independent Case01 steady Poiseuille validation using the audited Bouzidi wall.
- Original `Case01_Poiseuille`, its results, and the Frozen Protocol are protected.
- Case01a, Case01b and Case02 are outside this run.

## Frozen parameters

- D3Q19 with `descriptors::FORCE`.
- `ForcedBGK` collision.
- `Lx = Ly = 240 nm`, `H = 75 nm`.
- `dx = 5 nm`, `dt = 1e-11 s`, `tau = 1.7`.
- `ay = 1e5 m/s2`; other force components zero.
- x/y periodic; z non-periodic.
- material 1 only for physical mass, volume, velocity and flux integrals.
- convergence window 1000; maximum 30000 steps.

## Boundary gate

- Exact analytical planes at `z=0` and `z=75 nm`.
- `setBouzidiBoundary<T,DESCRIPTOR,BouzidiPostProcessor>`.
- Expected D3Q19 wall links: `2 * 48 * 48 * 5 = 23040`.
- q tolerance: `64 * epsilon(double)`.
- No geometric fallback, missing-neighbor fallback, or unresolved installed link allowed.
- A separate `precheck` process must exit 0 before `steady` may be launched.

## Acceptance

- frozen-window sample `std/abs(mean) <= 1e-6`;
- frozen-window `span/abs(mean) <= 5e-6`;
- section-flux relative difference `<= 1e-5`;
- material-1 maximum mass relative drift `<= 1e-10`;
- maximum density deviation `<= 1e-6`;
- maximum Mach `<= 0.05`;
- maximum transverse flux `<= 1e-12 m2/s`;
- velocity-profile relative L2 error `<= 2%`;
- `abs(Jy relative analytic error) <= 2%`;
- material field unchanged, all values finite, and independent shell exit code 0.

