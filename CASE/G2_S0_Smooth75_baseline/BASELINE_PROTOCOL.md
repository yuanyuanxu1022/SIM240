# G2-S0 Smooth75 numerical baseline protocol

## Scope

- One smooth, fully filled, fixed planar channel only.
- `Lx=Ly=240 nm`, `H=75 nm`.
- No EX240 rerun, parameter scan, moving wall or two-phase physics.

## Frozen parameters

- D3Q19 with `descriptors::FORCE` and `ForcedBGK`.
- `dx=2.5 nm`, `tau=1.0`, `a=1.0e5 m/s2`.
- `dt=(tau-0.5)dx^2/(3 nu)=1.0416666666667e-12 s`.
- `rho=1000 kg/m3`, `nu=1e-6 m2/s`, `mu=1e-3 Pa s`.
- Periodic in x and y; body force is applied in y.
- Exact planar, zero-velocity Bouzidi walls at `z=0` and `z=75 nm`.

## Definitions

- `J = integral_fluid(u_y dV)/(Lx Ly)`.
- `K_smooth,num = mu J/(rho a)`.
- `K_smooth,analytic = H^3/12`.
- `E_smooth = abs(K_smooth,num-K_smooth,analytic)/K_smooth,analytic`.
- EX240 ratios use the existing formal G2-P/G2-T `Keff` values and do not
  overwrite their analytical-reference ratios.

## Frozen gates

- exact geometry/material count and volume;
- all Bouzidi candidate links installed, `q` approximately 0.5;
- fallback and unresolved links equal zero;
- material-1 mass error `<1e-10`;
- maximum density deviation `<=1e-6`;
- Mach `<0.05`;
- section flux difference `<=1e-5`;
- cross flux `<=1e-12 m2/s`;
- latest 1000 J samples: sample std/mean `<=1e-6`, span/mean `<=5e-6`;
- velocity-profile L2 error `<2%`, velocity offset/analytic maximum `<2%`;
- absolute mobility error `<2%`;
- finite values, unchanged material field and normal exit.

No change to H, force, tau, analytical formula or velocity is allowed after
observing the result.
