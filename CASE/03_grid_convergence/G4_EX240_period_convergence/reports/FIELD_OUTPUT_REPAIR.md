# G4 parallel field output repair — fields_v1

The original Nx=2 batch `g4_period_nx2_20261011T133304+0800` is retained
unchanged. Its numerical gates passed, but all six field CSVs contain only
their header. Existing numerical success reports do not certify field coverage.
The Nx=4 batch `g4_period_nx4_20261011T201010+0800` was already running when
this repair started; its original build and postprocessor are kept intact.

Root cause: the old writer iterates rank-local core cells but redirects every
non-main rank to `/dev/null`. With multiple ranks, the selected mid-y plane is
outside the main rank's cells. Serial and 1-rank MPI exports have 9600 rows;
4/8/16-rank exports contain only a header.

## Scope

`generate_period_source_fields.py` derives sources from the original SHA-pinned
generator. The F-series changes only field collection/writing and a diagnostic
`fieldcheck` branch. Applying their exact inverse must reproduce the original
generated source. Geometry, boundaries, collision, drive, measurement, maximum
steps, convergence windows and all frozen numerical thresholds stay identical.
The frozen protocol file is retained unchanged.

MPI ranks fill a global-coordinate field buffer from core fluid cells at
`iy=48`. Allreduce collects the double-precision values and ownership counts;
the main rank writes one CSV in deterministic x/z order. Duplicate ownership,
incorrect row count and write failures terminate the run. Buffer summation has
one nonzero owner per coordinate; overlap cells are excluded.

For Nx periods, expected slice rows are
`Nx * (96*30 + 48*40) = 4800*Nx`: the 75 nm gap has 30 cells, and the
120 nm-wide recess adds 48*40 cells at dx=2.5 nm. At Nx=2 the CSV must have
9600 data rows plus its header. The Python checker verifies every expected
coordinate, duplicates, finite values, material, density and speed components.
Header-only files block success reporting before numerical postprocessing.

## Isolation and validation

- New binaries: `build_fields_v1/`, built with `src/Makefile.fields`.
- Original generator, runner, numerical postprocessor and `build/` are retained.
- Short `fieldcheck`: initialized state, zero collideAndStream calls, both P/T,
  serial-1 and MPI-1/4/8/16; compare all exported columns to serial and bind the
  results to source and binary hashes. This is output validation only.
- Fresh full scaling: serial-1 and MPI-1/4/8/16, precheck plus complete steady
  runs, original numerical scaling thresholds plus complete field evidence.
- Fresh Nx=2: all six prechecks, then six steady points at 8 ranks each, original
  numerical gates and linearity plus field completeness. No automatic Nx=4.
- New outputs use `g4_scaling_nx2_fields_v1_*` and `g4_period_nx2_fields_v1_*`
  and independent latest-fields pointers. No historical batch is overwritten.
- The long workflow refuses to start while any existing G4 solver is running.

## Verified preparation (2026-10-11)

- Four required binaries compiled successfully at the original production flags:
  serial a1e5 and MPI a5e4/a1e5/a2e5; independent build exit code 0.
- Five regression tests pass. The header-only regression was first observed
  failing against the original postprocessor (it incorrectly returned success).
- Ten initialized-state exports pass: P/T each with serial-1 and MPI-1/4/8/16.
  Every export has exactly 9600 unique fluid points, full coordinate coverage,
  finite fields, and numerical agreement with the serial reference.
- Zero collideAndStream calls in these probes. Fresh full numerical scaling
  and the new six-point Nx=2 steady batch remain to be run by the user.
- SHA comparisons confirm the original Nx=2 batch and original scripts/Nx=4
  binaries were preserved. Short-check details and artifact hashes are in
  `build_fields_v1/OUTPUT_CHAIN_CHECK.json`.

## User-started workflow

After the existing Nx=4 job finishes, use the isolated long workflow. It first
performs fresh full scaling and starts the fresh Nx=2 production batch only if
scaling and field checks pass. Every phase saves its own log, manifest and shell
exit code. A new batch still requires human review of T mass trajectories and
the evidence chain before a new Nx=4 release.

```bash
tmux new-session -d -s g4-nx2-fields 'cd /home/dell/yuanyuanxu/SIM240/CASE/03_grid_convergence/G4_EX240_period_convergence && exec python3 -u scripts/run_field_repair_nx2.py'
```
