# G2 paper database

This directory is a derived, paper-oriented archive of completed OpenLB G2 EX240 grid-convergence results. The source data remain under `CASE/03_grid_convergence/G2_EX240_grid_convergence/results/`.

- `G2_transport_summary.csv`: run-level transport and gate fields.
- `G2_grid_convergence.csv`: Smooth75, parallel and perpendicular coefficients by grid.
- `G2_resistance.csv`: reciprocal resistance, `R=1/K`, and resistance ratio.
- `G2_validation_status.md`: preserved gate and exit status.
- `G2_paper_summary.md`: manuscript-style interpretation.
- `figures/`: 600-dpi PNG and PDF figures generated from the two source CSV files.

No LBM calculation, OpenLB source, raw result, or PASS/FAIL threshold is changed by this archive.
