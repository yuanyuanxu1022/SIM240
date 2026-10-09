# G3-h EX240 height-sweep protocol (framework, not yet frozen for production)

## Scientific question

For the fixed EX240 unit cell, how does the mesa-to-substrate liquid-film gap
`h` affect the principal effective mobilities

`K_parallel(h)` and `K_perpendicular(h)`?

At each height, retain the G2 definition

`J_i = integral_fluid(u_i dV) / A_plan`,
`Keff = mu J_main / (rho a)`,

with `A_plan = (240 nm)^2`.  `H_ref(h) = h + 50 nm` is recorded only as a
geometrical reporting quantity; it must not replace the mesa gap in the smooth
reference.  The corresponding same-gap smooth reference is
`K0(h) = h^3 / 12`.

## Geometry and candidate matrix

- EX240: period `P=240 nm`; mesa / groove / mesa = `60/120/60 nm`.
- Fixed groove depth `D=100 nm`; only the mesa gap `h` changes.
- Candidate production heights: `25, 50, 75, 100, 125 nm`.
- Functional grid: `dx=2.5 nm`, so every height has exactly `10, 20, 30,
  40, 50` cells.  The existing G2 point is retained at `h=75 nm`.
- The 25 nm endpoint is numerically resolved by 10 cells but is the most
  sensitive point to continuum/no-slip and grid error; it is not a claim of
  continuum validity by construction.

The sweep deliberately does not vary period, width, depth, material model,
or wall treatment.  Thus it isolates height at fixed topology, but cannot by
itself identify a universal `Keff=f(h/P,D/P,Wg/P)` response surface.

## Inherited G2 numerical protocol

- D3Q19 `<FORCE>`, `double`, ForcedBGK, `tau=1.0`.
- `rho=1000 kg/m3`, `nu=1e-6 m2/s`, `mu=1e-3 Pa s`.
- `dx=2.5 nm`, with `dt=(tau-0.5)dx^2/(3nu)=1.0416666666666667e-12 s`.
- In-plane `x/y` periodicity; periodic body force `a=1e5 m/s2`.
- P drive is `+y`; T drive is `+x`.
- Exact EX240 zero-velocity link-wise Bouzidi wall, with all analytical
  half-links stored as `q=0.5`.
- Single MPI rank and no overwrite of a completed run directory.

## Required gates for any future steady point

Use the G2 gates unchanged: exact material/volume, candidate links equal
installed links, valid installed distances, zero fallback/unresolved links,
material-1 mass error `<1e-10`, density deviation `<=1e-6`, Mach `<0.05`,
section mismatch `<=1e-5`, cross flux `<=1e-12 m2/s`, 1000-sample relative
standard deviation `<=1e-6`, relative span `<=5e-6`, finite fields,
unchanged material, convergence and independently recorded normal exit.

For each height, run both P and T.  Report `NUMERICAL_GATE`, `geometry_PASS`,
and `RESULT_PASS` independently.  No post-hoc velocity correction, height
change, pressure-range substitution, or threshold adjustment is permitted.

## Evidence and promotion conditions

This framework inherits the G2 source SHA-256
`4acd63db67e273f87fed487fa7d1866f18dc82c018aaba1151f44882bd021002` and
permits only the mechanical substitutions recorded by the generator:
mesa gap, geometry-dependent expected node count, case labels and output
stem.  The generated source hash must be saved in every run manifest.

Because G1 remains analytically unresolved and the G2 three-grid GCI evidence
is incomplete, any later height-sweep output is candidate numerical evidence,
not final quantitative closure.  Endpoint and representative-midpoint grid
checks are required before fitting or publishing a height trend.
