# Case01 Poiseuille Run Configuration

> Scope: Gate 0 preparation only. This configuration does not authorize a formal simulation.

## Geometry

- H = 75 nm
- Lx = 240 nm
- Ly = 240 nm
- W = 240 nm
- dx = 5 nm
- Coordinate convention: x = width, y = flow/length, z = channel height
- Fluid material: material 1 only

## LBM

- Lattice: D3Q19
- Descriptor: `descriptors::D3Q19<descriptors::FORCE>`
- Collision: ForcedBGK
- Floating-point type: `double`
- tau: 1.7
- omega: 0.5882352941176471
- dt: 1.0e-11 s
- Physical density: 1000 kg/m^3
- Physical kinematic viscosity: 1.0e-6 m^2/s
- Physical dynamic viscosity: 1.0e-3 Pa s

## Driving

- Method: uniform body acceleration
- Direction: +y
- Body force: a = 1.0e5 m/s^2
- Other acceleration components: exactly zero
- Lattice acceleration: 2.0e-9

The Gate 0 executable stores the force field but performs zero `collideAndStream` calls.

## Boundary

- x direction boundary: periodic; confirmed by the frozen protocol and `src/case01_geometry_check.cpp`
- y direction boundary: periodic; confirmed by the frozen protocol and `src/case01_geometry_check.cpp`
- z direction boundary: fixed halfway bounce-back no-slip walls; material 2 at the lower wall and material 3 at the upper wall
- Status: CONFIRMED_FOR_GATE0

There is no velocity inlet or pressure outlet in this periodic body-force protocol.

## Output

Formal Case01 runs must record:

- `J_y` [m^2/s]
- `K_yy` [m^3]
- `B_yy` [m^2]
- `R_J,y` [Pa s/m^3]
- maximum Mach number
- maximum density variation
- material-1 fluid mass conservation
- same-direction section flux consistency
- convergence-window metrics
- independent normal process-exit evidence

Gate 0 records only geometry/material initialization, converter values, boundary flags, and the fact that no time step was executed.

## Gate 0 / Frozen Document Consistency Note

The Case01 in-plane domain is `Lx = Ly = 240 nm`, consistent with the frozen v2.1 periodic-cell definition. The frozen document was not modified.
