# Independent extractor v2 — synthetic validation, real extraction closed

This isolated revision addresses B01/B02/C01/C02 from the read-only review. Original code, 17-test record and all actual N8 records remain unchanged.

- numerics.py and test_fixtures.py are unchanged copies of v1; extractor.py retains the numerical API but the real entry now unconditionally rejects.
- binding.py anchors record inventory to an acceptance certificate, its accepted-input list, code/spec and a binding digest. The testable record reader accepts explicitly synthetic records only and rejects the actual N8 root before reading payloads.
- analysis_record.py provides unique output directories, complete artifacts, finite-value checks, predeclared software comparison states and failure logs. This is not a physical Gate.
- synthetic_fixture.py and test_revision.py construct marked artificial records and exact nonzero L2 oracle fixtures. No PDE is solved.
- synthetic_cli.py is a synthetic-only child process entry; it checks the supplied trust-anchor digest and returns the recorded exit code.
- ANALYSIS_SPEC.md is the predeclared numerical and recording specification.

The actual N8 binding and trust anchor are drafts under docs/reports/G4_offline_extractor_revision_v2_20261026. They are not an execution approval. There is no real-record analysis CLI or solver command in this package.

Read docs/reports/G4_offline_extractor_revision_v2_20261026/REPORT.md and verification.json for scope and results. No scalar-case, groove-domain or strict error-bound qualification is claimed.
