# G1-V3 fine-grid hydraulic-mobility validation protocol

## Purpose

G1-V3 is an independent confirmation batch for the production-grid candidate
identified by the completed G1-V2 grid study.  It does not amend, overwrite,
or reclassify the protected G1-V2 baseline at `dx=5 nm`, `tau=1.7`.

## Frozen numerical definition

- Geometry: `Lx=Ly=240 nm`, `H=75 nm`; periodic in x/y and stationary
  no-slip planes at `z=0` and `z=H`.
- Lattice: D3Q19 with `descriptors::FORCE`, `ForcedBGK`, double precision,
  and the existing exact-planar zero-velocity Bouzidi boundary treatment.
- Physical fluid: `rho=1000 kg/m3`, `nu=1e-6 m2/s`.
- Production-grid candidate: `dx=2.5 nm`, `tau=1.7`,
  `dt=2.5e-12 s`, derived from
  `dt=(tau-0.5)*dx^2/(3*nu)`.
- Analytical reference remains `K=H^3/12`; no height change, force rescaling,
  velocity-offset subtraction, or acceptance-threshold change is permitted.

## Required matrix

| Case | Acceleration (m/s2) |
|---|---:|
| G1V3-a1 | `5e4` |
| G1V3-a2 | `1e5` |
| G1V3-a3 | `2e5` |

## Evidence and decision rules

Each case must retain a unique run directory, precheck, source/binary hashes,
diagnostics, velocity profile, boundary audit, result files, full log, and an
independent exit code.

`G1-V3` is PASS only when all three steady runs have independent exit code 0,
their own numerical and geometry evidence passes, and the fitted force-response
has `R2 >= 0.999999` with `|intercept|/max(|J|) <= 1%`.

The locked G1-V2 grid evidence remains an upstream requirement: at fixed
`tau=1.7`, errors decrease monotonically from 10 to 5 to 2.5 nm, the
2.5-nm point has mobility error below 2%, and the reported fine-grid GCI is
1.323053%.  This v3 batch supplies the missing independent three-force check
at that selected resolution; it does not use `tau=1.0` as an after-the-fact
replacement for the `tau=1.7` scheme.

## Scope boundary

Only the existing G1 solver is compiled and run.  No OpenLB core file,
G1-V2 source, G1-V2 result, EX240 case, G5A input, or acceptance threshold is
modified by this protocol.
