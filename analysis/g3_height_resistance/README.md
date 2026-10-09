# G3 height-resistance extraction

This independent post-processing module scans completed G3-h steady results
under `CASE/04_parameter_study/G3_EX240_height_sweep/results/` and generates:

- `transport_database/G3_height_resistance.csv`
- `transport_database/Figure_R_vs_h.png`
- `transport_database/Figure_anisotropy_vs_h.png`

The database contains one paired row per liquid-film height with
`R_parallel`, `R_perp`, `K_parallel`, `K_perp`, and
`anisotropy = K_parallel / K_perp = R_perp / R_parallel`.

The pressure drop is the periodic-body-force equivalent
`Delta-p = rho * acceleration * drive_length`. Flow rate is the mean of the
two recorded section flows in `result.txt`; if those are unavailable, it is
derived from `Delta-p/R_eff`. `energy_dissipation` is the arithmetic mean of
the existing `energy_dissipation.csv` profile (`Phi`), not a volume-integrated
dissipation power.

Only directories containing both `result_summary.csv` and `result.txt` are
included. Precheck-only heights are excluded from the formal table.

Run with:

```bash
conda run --no-capture-output -n sim240-analysis \
  python analysis/g3_height_resistance/extract_g3_height_resistance.py
```

The module does not modify OpenLB, simulation code, or raw results.
