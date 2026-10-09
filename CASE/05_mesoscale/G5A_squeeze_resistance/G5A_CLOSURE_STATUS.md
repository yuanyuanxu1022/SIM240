# G5A closure status — frozen candidate application

## Frozen record

- Run ID: `run_20260921_190046`.
- Raw evidence: `results/run_20260921_190046/`.
- Input table: `transport_database/G3_height_resistance.csv`.
- Input-table SHA-256: `33c7a4bbc40d90c842e03ed22e864fc9778fc46f661ee1982684d9d5bdae2462`.
- Input micro-grid: `dx = 2.5 nm`.
- Independent application exit code: `0`.
- G5A internal gates: `INPUT_GATE`, `NUMERICAL_GATE`, `ANALYTIC_GATE`,
  `MASS_GATE`, `LINEARITY_GATE`, and `RESULT_PASS` are all `true`.

## Scientific status

G5A is frozen as a **candidate-closure mesoscale application**.  Its result
demonstrates that the one-dimensional, constant-velocity squeeze model
preserves its specified candidate directional transport input, satisfies the
analytic solution, and closes mass for the nine configured cases.

It is not a final, grid-independent EX240 closure, nor a direct moving-boundary
LBM, two-phase filling, wetting, trapped-gas, or universal imprint-resistance
result.  The mandatory labels remain:

```text
INPUT_CLOSURE_STATUS: CANDIDATE_FIXED_GRID
FINAL_GRID_INDEPENDENT_CLOSURE: false
```

No additional G5A calculation is authorized by this record.  Re-running G5A
is only meaningful after a newly frozen upstream transport table has replaced
the candidate input.

## Upstream release condition

The candidate label can be upgraded only after all of the following are
separately evidenced:

1. G1 passes its frozen analytical-accuracy gate, including its baseline
   mobility, velocity-profile, and offset limits.
2. The force-linearity and three-grid/GCI evidence are complete and linked to
   independent normal-result files.
3. The EX240 extraction protocol is frozen with its direction convention,
   reference height, forcing range, grid policy, cross-term definition,
   provenance manifest, and acceptance gates.

Until then, G5A figures and tables may be used only as a conditional
demonstration of the candidate closure.

## G1 evidence handoff

The currently authoritative G1-V2 batch is
`CASE/00_validation/G1_Poiseuille_Bouzidi_Validation/results/g1_v2_20260916T202853+0800/`.
It contains all nine requested matrix cases.  The matrix established force
linearity (`R2 = 1`), monotonic grid-error reduction, a finest-grid mobility
error of `1.168883%`, and a fine-grid GCI of `1.323053%`.  Nevertheless,
the frozen baseline at `dx = 5 nm`, `tau = 1.7`, and
`a = 1e5 m/s2` remains FAIL: mobility error `+4.675555%`, velocity-profile
L2 error `4.065283%`, and offset ratio `2.968889%`.

The `tau = 0.8` and `tau = 1.0` controls pass their individual numerical
criteria, whereas `tau = 1.7` fails.  This is evidence of a relaxation-time
dependent discretization error; it does not authorize an after-the-fact change
to the frozen baseline or its acceptance thresholds.

The next G1 task is therefore evidence analysis and a protocol decision, not
an unmotivated repeat of the completed nine-case matrix.
