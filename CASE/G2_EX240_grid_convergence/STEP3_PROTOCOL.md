# SIM240 G2 Step 3 protocol

## Scope

Quantify grid convergence and numerical uncertainty for Smooth75,
`K_parallel`, `K_perpendicular`, the same-grid smooth-normalized mobilities,
and anisotropy. This is fixed-gap, single-phase G2 work only.

## Frozen physical problem

- EX240: `P=240 nm`, `mesa=60 nm`, `groove=120 nm`, `D=100 nm`, mesa gap
  `h=75 nm`.
- Smooth75: `Lx=Ly=240 nm`, `H=75 nm`.
- `rho=1000 kg/m3`, `nu=1.0e-6 m2/s`, `mu=1.0e-3 Pa s`.
- `a_phys=1.0e5 m/s2`, `tau=1.0`.
- D3Q19 with force field, ForcedBGK, exact-geometry zero-velocity Bouzidi,
  x-y periodicity, periodic body-force driving.
- Frozen statistics and convergence windows are inherited from the current
  G1-V2 Smooth75 and formal G2 sources.

## Grid and similarity matrix

| dx (nm) | P/dx | mesa/dx | groove/dx | D/dx | h/dx | dt (s) | nu_lattice | a_lattice | dx/dt (m/s) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5.0 | 48 | 12 | 24 | 20 | 15 | 4.166666666666667e-12 | 1/6 | 3.472222222222222e-10 | 1200 |
| 2.5 | 96 | 24 | 48 | 40 | 30 | 1.041666666666667e-12 | 1/6 | 4.340277777777778e-11 | 2400 |
| 1.25 | 192 | 48 | 96 | 80 | 60 | 2.604166666666667e-13 | 1/6 | 5.425347222222222e-12 | 4800 |

Here `dt=(tau-0.5) dx^2/(3 nu_phys)` and
`a_lattice=a_phys dt^2/dx`. Holding lattice acceleration fixed is prohibited.

## Formal matrix

Nine points: three grids times Smooth75, EX240 parallel, and EX240
perpendicular. All nine are newly run because the earlier 2.5 nm output does
not contain the requested final `rho_min` and `rho_max`; changing the diagnostic
source also invalidates exact source-version reuse.

All zero-step prechecks must pass before any steady run begins.

## Run gates

Each point requires:

- mass error `<= 1.0e-10`;
- Mach `< 0.05`;
- convergence and finite values PASS;
- material unchanged;
- normal shell and in-program exit code zero;
- candidate links equal installed links;
- `q_min` and `q_max` equal 0.5 within `1.0e-10`;
- fallback and unresolved counts zero.

Smooth analytical error is reported but is not an individual coarse-grid run
gate; otherwise a deliberately coarse member of a convergence study could be
rejected before its truncation error is measured.

## Richardson and GCI

Use `r=2`, fine/medium/coarse values at `1.25/2.5/5.0 nm`, and safety factor
`Fs=1.25`. A result is eligible only when both differences are finite and
nonzero, convergence is monotonic, and the apparent order is positive and
finite. The asymptotic indicator is
`GCI_medium/(r^p GCI_fine)` and passes in `[0.95,1.05]`.

No order or GCI is forced for oscillatory/non-monotonic data, a near-zero
denominator, or non-positive apparent order. The raw values, relative span,
and diagnostic reason remain in the report.

The pre-frozen paper uncertainty target is `GCI_fine <= 2%` for both EX240
principal mobilities. Relative metrics must vary by no more than 1% between a
candidate production grid and the fine grid. The production recommendation is
the coarsest grid supported by the available GCI/extrapolation evidence and
these relative-metric checks; 2.5 nm is not assumed in advance.

## Step 3 decision

Step 3 PASS requires all nine run gates, valid asymptotic Richardson/GCI for
the three absolute mobilities, and fine-grid GCI within 2% for both EX240
principal directions. If the mathematical conditions fail, the result is
reported as FAIL/inconclusive rather than assigned a cosmetic convergence
order.
