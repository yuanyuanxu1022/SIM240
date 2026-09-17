# Case01c Smooth Thin-Film Lubrication Benchmark

## Scope

Independent smooth parallel-plate benchmark comparing OpenLB-LBM with the classical Reynolds lubrication solution. This directory does not modify or authorize the Frozen Protocol, EX240, or any prior Case01/R2/R3 result.

## Frozen parameters for this independent benchmark

- OpenLB 1.8r1 local revision: 5953d8a-dirty
- D3Q19 with FORCE field
- ForcedBGK
- exact planar Bouzidi boundary; all physical wall links expected at q=0.5 (halfway limit)
- no-slip walls at z=0 and z=75 nm
- x/y periodic body-force drive
- Lx=Ly=240 nm; H=75 nm
- dx=5 nm; dt=1e-11 s; tau=1.7
- rho=1000 kg/m3; nu=1e-6 m2/s
- ay=1e5 m/s2
- one MPI rank

## Theory

- J_Reynolds = ay*H^3/(12*nu)
- R_Reynolds = rho*ay/J_Reynolds
- R_LBM = rho*ay/J_LBM
- relative_error_R = (R_LBM-R_Reynolds)/R_Reynolds

## Pre-run gate

A separate zero-step process must pass geometry, exact material-1 fluid count (48*48*15=34560), theoretical/candidate/valid/installed wall links (23040), q=0.5 within 64*epsilon(double), and zero fallback/unresolved links. Failure blocks the steady run.

## Validation thresholds

- converged 1000-sample flux window: relative sample std <=1e-6 and relative span <=5e-6
- maximum material-1 mass drift <=1e-10
- maximum Mach <=0.05
- abs(relative_error_R) <=2%
- velocity-profile relative L2 <=2%

The numerical result, not the intended benchmark label, determines PASS/FAIL.

