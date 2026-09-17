# G2 Step 3 run configuration

- grids_nm: `5.0, 2.5, 1.25`
- cases: `Smooth75, parallel, perpendicular`
- acceleration_m_s2: `1.0e5`
- tau: `1.0`
- density_kg_m3: `1000`
- kinematic_viscosity_m2_s: `1.0e-6`
- collision: `ForcedBGK`
- descriptor: `D3Q19<FORCE>`
- wall: `Bouzidi zero velocity, exact geometry`
- periodicity: `x,y`
- ranks: `1`
- overwrite: `forbidden`
- output_root: `results/g2_grid_<timestamp>/`

The EX240 convergence window and stopping criteria are inherited from
`G2_EX240_single_period_transport`. Smooth75 inherits the current G1-V2
statistics/convergence definitions, while its Step 3 exit gate excludes the
analytical-accuracy threshold so the coarse grid remains a valid uncertainty
sample.
