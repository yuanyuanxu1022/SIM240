# Case01-R2 configuration

Independent spatial-refinement diagnostic. D3Q19 ForcedBGK, periodic x/y body-force drive, exact planar Bouzidi walls at z=0 and z=75 nm.

- dx = 2.5e-9 m
- target tau = 1.7
- dt = 2.5e-12 s, derived from tau=0.5+3*nu*dt/dx^2
- nu = 1e-6 m2/s
- ay = 1e5 m/s2
- grid = 96 x 96 x 30 fluid cells
- expected wall links = 2*96*96*5 = 92160
- one MPI rank
- zero-step geometry/converter/q precheck required before steady execution

