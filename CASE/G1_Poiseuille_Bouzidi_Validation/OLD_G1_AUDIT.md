# Old G1 evidence audit

## Audited files

- `../Case01_Poiseuille/run_config.md`
- `../Case01_Poiseuille/src/case01_poiseuille.cpp`
- `../Case01_Poiseuille/results/gate1_case01_dx5_a1e5_20260915T210323p0800/validation_report.md`
- the complete `diagnostics.csv`, `velocity_profile.csv`, `result.txt`, `run.log`, manifest and exit code in that result directory
- the independent same-parameter Bouzidi comparison in `../Case01-Bouzidi-steady/`

## Frozen parameters and old result

| Item | Evidence |
|---|---:|
| Geometry | Lx=Ly=240 nm, H=75 nm |
| Grid/time | dx=5 nm, dt=1e-11 s |
| Lattice/collision | D3Q19 FORCE / ForcedBGK |
| tau | 1.7 |
| Driving | uniform ay=1e5 m/s2 |
| Wall boundary | `boundary::BounceBack` |
| Converged step | 1704 |
| Maximum Mach | 2.508009558e-7 |
| Maximum material-1 mass drift | 0 |
| J | 3.679999984e-12 m2/s |
| K_LBM | 3.679999984e-23 m3 |
| K_theory | 3.515625000e-23 m3 |
| K relative error | +4.675555104% |
| Velocity-profile L2 error | 4.065282994% |
| Independent exit code | 3 (frozen accuracy FAIL) |

The numerical minus analytic velocity is an almost constant positive offset of
`2.087499788e-6 m/s`; its span is only `2.935178600e-13 m/s`.

## Causal boundary

The existing same-parameter Bouzidi run installed all 23,040 expected links,
reported `q=0.5`, zero fallback/unresolved links, and reproduced exactly the
same J, K error and profile error. Thus the available evidence **does not**
support the statement that the 4.7% error comes from use of the BounceBack API.
For this geometry, Bouzidi at `q=0.5` degenerates to halfway link bounce-back.

The geometry height, body-force conversion, velocity sampling and SI-unit
conversion are internally consistent with the frozen protocol; however, their
consistency does not by itself identify the remaining error mechanism. The
working hypothesis is a grid- and tau-dependent discrete offset associated
with ForcedBGK + forcing + halfway reflection. G1-V2 tests this hypothesis;
it does not assume the outcome.
