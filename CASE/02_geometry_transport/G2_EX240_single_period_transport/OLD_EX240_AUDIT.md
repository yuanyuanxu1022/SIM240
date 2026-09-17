# Existing EX240 audit and reuse decision

## Audited implementations

- `grooveDNS/ex240_homogenization/`
- `grooveDNS/stage3_ex240_local/fixed_gap_single_phase/`
- `grooveDNS/stage3_ex240_local/directional_transport/`

## Reused

- exact `60+120+60 nm` periodic material definition and 100 nm groove depth;
- fixed fully filled single-phase RVE with x/y periodicity;
- material-1-only volume, mass and depth-integrated flux statistics;
- `J=integral(u dV)/A_plan`, `K=mu*J/(rho*a)`;
- convergence window, cross-flux, section-flux, density and Mach evidence.

## Replaced or excluded

- old `dx=5 nm`, `tau=1.7` values remain historical functional samples;
- old material BounceBack is replaced by exact-surface zero-velocity Bouzidi;
- no old K value is copied into the new summary;
- pressure range is not interpreted as an inlet-outlet pressure drop;
- dynamic punch, FreeSurface, wetting and two-phase directories are excluded.

The old h=75 nm functional result used the same physical geometry and found a
finite directional response, but it had no G1-qualified grid/tau combination
and no Bouzidi link audit. It is therefore useful only as an implementation
cross-check, not as the formal G2 result.

