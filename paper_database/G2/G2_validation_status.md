# G2 validation status

Source: `g2_grid_summary.csv`; no simulation was rerun during archiving.

| dx (nm) | direction | run_gate_PASS | exit_code | mass_error | convergence_PASS | boundary_audit_PASS | normal_exit_PASS |
|---:|---|---|---:|---:|---|---|---|
| 1.25 | parallel | True | 0 | 0.0 | True | True | True |
| 1.25 | perpendicular | False | 3 | 1.1967043900362632e-10 | True | True | False |
| 2.5 | parallel | True | 0 | 0.0 | True | True | True |
| 2.5 | perpendicular | True | 0 | 8.529943723626527e-12 | True | True | True |
| 5 | parallel | True | 0 | 0.0 | True | True | True |
| 5 | perpendicular | True | 0 | 8.934175019802938e-13 | True | True | True |

The `dx=1.25 nm` EX240 perpendicular point has `run_gate_PASS=false` and `exit_code=3` because its recorded mass error is `1.1967043900362632e-10`. This status is preserved unchanged.

The Smooth75 reference rows have `run_gate_PASS=true` for all three grids.
