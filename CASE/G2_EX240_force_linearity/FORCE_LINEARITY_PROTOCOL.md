# SIM240 G2 Step 2: EX240 force-linearity protocol

## Scope

This case verifies the linear response of the frozen EX240 single-period model in the two principal directions. It does not change the EX240 geometry and does not enter grid uncertainty, moving-boundary, or two-phase work.

## Frozen numerical and physical parameters

- Geometry: EX240, `P = 240 nm`, `60 nm mesa + 120 nm groove + 60 nm mesa`, `D = 100 nm`
- Mesa gap: `h = 75 nm`
- Grid: `dx = 2.5 nm`
- Collision: D3Q19, ForcedBGK, `tau = 1.0`
- Wall: zero-velocity Bouzidi
- Driving: periodic body force
- Directions: parallel (`P`) and perpendicular (`T`)
- Accelerations: `5e4`, `1e5`, `2e5 m/s^2`
- Statistics, convergence tests, material semantics, and boundary gates: inherited unchanged from the formal G2 protocol and source

The `1e5 m/s^2` formal G2-P/G2-T runs are reused only after exact source, executable, protocol, parameter, boundary, and statistics audit. The two new executable variants are mechanically generated from the frozen G2 source by changing only the acceleration constant.

## Definitions

For each direction,

```text
J = c a + b
K = mu J / (rho a)
K_CV = sample_standard_deviation(K) / mean(K)
K_max_relative_spread = (max(K) - min(K)) / mean(K)
```

The standard deviation uses the sample definition (`n-1`).

## Frozen gates

- `R^2 >= 0.9999`
- `K_max_relative_spread <= 0.01`
- `Mach < 0.05`
- `mass_error <= 1e-10`
- convergence PASS
- finite PASS
- normal exit PASS
- inherited geometry/material/periodic/Bouzidi precheck PASS

No gate or definition may be changed after inspecting the results.
