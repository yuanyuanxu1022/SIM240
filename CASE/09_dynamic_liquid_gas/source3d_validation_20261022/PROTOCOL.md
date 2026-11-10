# D3 source consistency and prescribed-advection diagnostic v1, 2026-10-22

Scope: independent implementation and compile preparation authorized by the user.
No shared OpenLB/old CASE edit, no new static-drop, wetting, groove K or GHY claim.
Collision-only unit checks may execute as preparation; spatial time integration is
prepared for a separate user-started run. Neither check releases a physical Gate.

## Reviewed correction

Let S = 1.5 (u dot grad(phi))_n - 0.5 (u dot grad(phi))_(n-1).
The source coefficient from Ju et al. arXiv:2311.10827, Eq. 2.18 is
`w_i S [-(d+2)/2 + |c_i|^2/(2 cs^2)]`.
For D3Q19, zeroth/first/second source moments must be `-S, 0, 0`.
The upstream constant -2 gives `-S/2, 0, S I/6`; D2Q9 remains correct.
The fix changes only this constant in a locally named combination rule. No multiplication
of the whole source by two (which would leave an erroneous second moment), no changes
to chemical potential, mobility, NS force, pressure gauge, or physical input values.
Local type has no old generated CSE specialization; its CSE wrapper falls back to
the new generic collision. Existing generic AND generated old implementations are controls.

## A. Actual collision checks (frozen before execution)

Call OpenLB dynamics on real CellD objects, both generic and CSE paths, D2Q9/D3Q19.
tau = 0.6,1,1.4; phi = .2,.5,.8; chemical potential = -.004,0,.003;
S = -.0002,0,.0002; equilibrium and zero-sum nonequilibrium populations.
Subtract a collision with S=0 from the identical input with S!=0; measure population
increments and all zero/first/second moments. This isolates the source from BGK.
Tolerance: absolute 1e-12, finite values required. Verify generic/CSE agreement,
D2 unchanged, S=0 unchanged, corrected moments, and old D3 defect reproduced.
These are local collision operations without streaming, not a simulation run.

## B. Periodic prescribed-advection test (NOT run during preparation)

Use the actual OpenLB SuperLattice collideAndStream and periodic communications,
one CPU_SISD MPI rank; D3Q19 phase lattice, tau=1. No NS lattice or wall.
Chemical potential is set to zero deliberately: this is an operator test of prescribed
advection, not a physical free-energy/two-phase solution. Velocity is prescribed and constant.
The gradient uses the same D3Q19 isotropic neighbor stencil as phaseFieldCoupling.h.
SOURCE uses the same 1.5/-0.5 extrapolation. At first update use S_old=S_initial
(first-order startup); output includes step 0 and all subsequent steps.

N=16,32 periodic nodes per axis; coordinates 0..N-1; phase initial field:
phi(x,y,z,0)=0.5+(0.05/3)[cos(2pi x/N)+cos(2pi y/N)+cos(2pi z/N)].
Velocity components in lattice units: +x,-x,+y,-y,+z,-z,+xyz,-xyz; nonzero
components have magnitude .008. Each run lasts N/(4*.008)=500 or 1000 steps.
Also include U=0 at both N for both implementations. Total 36 independent runs.
The exact advected solution replaces each coordinate by x_a-U_a t.
Common dimensionless domain/time under refinement: x/N and t/N, U_lu fixed.
No real GHY/SI interpretation. Maximum prescribed Mach is .024.

Output full-step phase means, extrema, Fourier complex coefficients for all axes,
normalized fluctuation L2 error versus exact solution, amplitude and unwrapped phase,
endpoint 3D scalar fields, numerical source/sum diagnostics, node counts and config.
For each moving Fourier component derive U_measured from its full-series phase slope.
Zero-mode and initial .5 mean are not included in the L2 denominator.

Thresholds fixed BEFORE any translation result:
- Corrected relative speed error <=5% (N16), <=2% (N32).
- Corrected endpoint amplitude relative error <=2% (N16), <=1% (N32).
- Corrected endpoint fluctuation L2 relative error <=.10 (N16), <=.04 (N32).
- All-run max absolute relative phase-amount drift <=1e-9 and every output finite.
- Stationary Fourier components phase change <=1e-6 rad; U=0 field L2 <=1e-10.
- x/y/z measured speed-ratio spread <=.002 at a given N/sign.
- Fine-grid moving phase-speed error lower than coarse, unless both <=1e-6.
- Old implementation is a negative control: moving speed ratio in [.45,.55].
  Report old physical-advection FAIL separately from successful defect reproduction.
No threshold revision after results, no automatic rerun or later physics stage.
Two grids test error reduction, not GCI/asymptotic convergence proof.
Solver safety stop (distinct from acceptance): any nonfinite population/phase/source,
phi outside [.2,.8], absolute relative phase drift >1e-6, or invalid node count.
The acceptance drift threshold remains 1e-9; a safe exit alone is not test PASS.

## Limitations and subsequent work

Collision PASS does not imply advection PASS; prescribed-advection PASS does not imply
coupled NS/CH, MPI multi-rank, Laplace, wetting or K PASS. Repairing this source alone
does not resolve pressure gauge, chemical relaxation, equilibrium density shift,
finite interface-width or residual velocity issues found in the 2000-step review.
Subsequent work requires actual translation results, then separate coupling/diffusion
and equilibrium audits. Freeze any new physics protocol before execution.

Reference checked 2026-10-22: https://arxiv.org/pdf/2311.10827 (v1), Eqs. 2.18–2.20.
Local library version/source hashes take precedence over online API versions.
