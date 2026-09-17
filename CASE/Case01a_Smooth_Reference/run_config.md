# Case01a Smooth Reference H75

## Scope and naming

This is an independent H=75 nm smooth-reference case requested after Case01c. It does not modify the Frozen Protocol or authorize EX240.

Important: Frozen Protocol v2.1 defines its formal Case01a as H=175 nm. Therefore this directory is labeled Case01a_Smooth_Reference_H75 in run evidence and must not be substituted for the protocol's H=175 nm Case01a.

## Model

- OpenLB 1.8r1 local revision 5953d8a-dirty
- D3Q19 with FORCE field
- ForcedBGK
- exact planar Bouzidi boundary, q=0.5 halfway limit
- no-slip walls at z=0 and z=75 nm
- x/y periodic body-force drive
- Lx=Ly=240 nm
- dx=5 nm, dt=1e-11 s, tau=1.7
- rho=1000 kg/m3, nu=1e-6 m2/s
- ay=1e5 m/s2
- one MPI rank

## Pre-run gate

The separate zero-step precheck must pass geometry, exact material-1 count, theoretical/candidate/valid/installed wall-link counts, q distribution, and zero fallback/unresolved links.

## Outputs

- result.txt
- validation_report.md
- diagnostics.csv
- velocity_profile.csv
- pressure_profile.csv
- vtk/

Pressure is the OpenLB physical gauge pressure from density. Under periodic body-force driving, the expected streamwise pressure profile is spatially constant; the imposed driving is rho*a, not a resolved inlet-outlet pressure drop.

