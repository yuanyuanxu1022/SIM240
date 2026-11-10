# Independent saved-field extractor — preparation only

Scope: dimensionless 2×1 mixed P2/P1 rectangular records, with the first existing N8 as the future target. NumPy and the Python standard library only. No PDE backend, assembly, solve, fitting, or launcher dependency.

- `numerics.py`: in-memory reconstruction, analytic MMS, volume/section/control-volume integration, CSR multiplication and pressure-row diagnostics.
- `extractor.py`: metrics API, synthetic-file reader, dormant existing-N8 adapter. `REAL_RECORD_EXTRACTION_ENABLED=False`; real entry rejects before accessing a path. No executable real-record CLI.
- `test_fixtures.py`: synthetic fields, independent polynomial/analytic answers and negative controls.
- `run_fixture_validation.py`: persist synthetic validation only; refuses to overwrite the final result.

The actual N8 arrays have not been loaded during preparation. Synthetic nodal interpolation is not a PDE solution. The full archived input inventory, parent exit/provenance and independent prior acceptance remain necessary for any later real analysis. Do not change the closed real-entry switch under the old solver approval.

Report: `docs/reports/G4_offline_extractor_preparation_20261026/REPORT.md`.
Criteria: `docs/reports/G4_reference_criteria_review_20261026/CRITERIA_REVISION.md`.

No scalar-case, groove-domain, generalized MPC, formal reference qualification or strict error certificate is supplied by this package.
