# G2 EX240 single-period transport protocol

## Scope

- Single-phase, fully filled, fixed EX240 periodic RVE only.
- No moving punch, interface, wetting, capillarity or air.
- Geometry: `240 nm` period; `60 nm mesa + 120 nm groove + 60 nm mesa`;
  groove depth `100 nm`; mesa gap `h=75 nm`; groove total height `175 nm`.
- Both in-plane directions remain periodic. Direction is changed only through
  the body-force vector.

## Frozen numerical parameters

- D3Q19 with `descriptors::FORCE` and `ForcedBGK`.
- `dx=2.5 nm`, `tau=1.0`, `a=1e5 m/s2`.
- Physical viscosity is fixed, therefore
  `dt=(tau-0.5)dx^2/(3 nu)=1.0416666666667e-12 s`.
- Exact EX240 solid surface with zero-velocity Bouzidi links.
- `rho=1000 kg/m3`, `nu=1e-6 m2/s`, `mu=1e-3 Pa s`.

The exact combination `dx=2.5 nm, tau=1.0` was not directly included in the
previous G1 matrix. G2 therefore reports this limitation explicitly; passing
G1 separately at fine dx and at tau=1.0 is not treated as a mathematical proof
that their combination is validated.

## Directions

- `G2-P`: body force in y, parallel to the groove, gives `K_parallel`.
- `G2-T`: body force in x, perpendicular to the groove, gives
  `K_perpendicular`.

## Definitions

`J_i = integral_fluid(u_i dV)/A_plan` and
`Keff = mu J/(rho a)`. The periodic resistance is
`R_eff = rho a/J = mu/Keff`.

The primary smooth reference is `K0=(75 nm)^3/12`, because 75 nm is the mesa
gap shared with G1. The equal-volume height is `H_ref=125 nm`; it is recorded
but is not substituted into K0.

## Frozen gates

- exact fluid nodes and volume;
- all candidate Bouzidi links have valid installed distances;
- zero geometric/missing-neighbour fallback and zero unresolved links;
- material-1 mass error `<1e-10`;
- maximum density deviation `<=1e-6`;
- Mach `<0.05`;
- two section fluxes differ by `<=1e-5`;
- cross flux `<=1e-12 m2/s`;
- latest 1000 main-J samples: sample std/mean `<=1e-6` and span/mean `<=5e-6`;
- finite values, unchanged material field and normal exit.

No velocity correction, geometry adjustment or pressure-range substitution is
allowed after seeing results.

For the Bouzidi audit, a second fluid-side neighbour is required and counted
only for the OpenLB `q>0.5` branch. Exact analytical half-link intersections
are stored as `q=0.5`; this prevents floating-point round-off from changing the
branch at EX240 step corners and does not alter the physical wall location.
