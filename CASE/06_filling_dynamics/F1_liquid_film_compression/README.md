# G3-h EX240 liquid-film-height sweep

## Scope and status

This is a **framework-only, pre-formal** fixed-geometry EX240 height-sweep
case.  It measures the two principal entries of the effective mobility tensor,
`K_parallel(h)` and `K_perpendicular(h)`, under the frozen G2 numerical
family.  It does not start or authorize any steady calculation.

The current project context names tensor-angle validation as G3 and reserves
geometry/height parameterization for G4.  To preserve that published routing,
this directory uses the explicit label **G3-h**: a proposed prerequisite data
set, not a redefinition of the existing G3 gate.  Formal promotion requires a
roadmap/context decision after G1 and G2 numerical uncertainty are closed.

## Layout

- `HEIGHT_SWEEP_PROTOCOL.md` — scientific scope, frozen definitions and gates.
- `height_matrix.csv` — candidate height matrix, including resolution checks.
- `scripts/generate_height_source.py` — derives one source variant from the
  SHA-256-pinned G2 source by mechanical substitutions only.
- `scripts/preflight_height.py` — validates the matrix and optionally records
  a preflight table.  It never runs OpenLB.
- `src/Makefile` — builds a selected generated variant; it never runs it.
- `scripts/run_precheck.sh` — explicitly performs one zero-step boundary test.

`results/` and `build/` are local runtime products and are intentionally not
created by the framework.

## Allowed small test

The only test prepared here is a zero-step `precheck` for one height and one
principal direction.  It validates material counts, exact geometry, Bouzidi
links and `q` distances, and makes no `collideAndStream` call.  A successful
precheck is only `geometry_PASS`; it is not a transport result or G3/G4 PASS.

## Candidate formal order (not executed)

1. Re-confirm G1 analytical validation and the G2 grid/GCI decision.
2. Freeze whether this sweep is G3-h or G4 in the project roadmap.
3. Run all matrix prechecks, then P/T steady cases using separate immutable
   run IDs and the inherited G2 gates.
4. Independently repeat grid uncertainty at least at the two height endpoints
   before interpreting a height trend as physical.
