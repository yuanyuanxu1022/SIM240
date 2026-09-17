# G2 Step 3 grid preflight

Status: **PASS**

All nominal dimensions are represented by exact integer cell counts. Physical density, viscosity, acceleration, and tau are fixed; dt and lattice acceleration are recomputed per grid.

| dx (nm) | P | mesa | groove | D | h | dt (s) | nu_lattice | a_lattice | dx/dt (m/s) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5.00 | 48 | 12 | 24 | 20 | 15 | 4.1666666666666668e-12 | 1.6666666666666666e-01 | 3.4722222222222225e-10 | 1200 |
| 2.50 | 96 | 24 | 48 | 40 | 30 | 1.0416666666666667e-12 | 1.6666666666666666e-01 | 4.3402777777777781e-11 | 2400 |
| 1.25 | 192 | 48 | 96 | 80 | 60 | 2.6041666666666668e-13 | 1.6666666666666666e-01 | 5.4253472222222226e-12 | 4800 |

Identity checked: `tau = 0.5 + 3 nu_phys dt / dx^2 = 1.0` on every grid.
