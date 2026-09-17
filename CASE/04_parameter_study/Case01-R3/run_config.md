# Case01-R3 configuration

Independent relaxation-time diagnostic. D3Q19 ForcedBGK, periodic x/y body-force drive, exact planar Bouzidi walls at z=0 and z=75 nm.

- dx = 5e-9 m
- target tau = 1.0
- dt = 4.166666666666667e-12 s, derived from tau=0.5+3*nu*dt/dx^2
- nu = 1e-6 m2/s
- ay = 1e5 m/s2
- grid = 48 x 48 x 15 fluid cells
- expected wall links = 2*48*48*5 = 23040
- one MPI rank
- zero-step geometry/converter/q precheck required before steady execution

