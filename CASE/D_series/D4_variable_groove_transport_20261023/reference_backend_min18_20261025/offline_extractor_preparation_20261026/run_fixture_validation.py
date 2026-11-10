"""Execute only the synthetic unittest suite; persist a bounded review record."""
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
import numpy as np
import test_fixtures


def main():
    source=Path(__file__).resolve().parent
    repo=source.parents[4]
    out=repo/'docs/reports/G4_offline_extractor_preparation_20261026'
    require_target=out/'fixture_results.json'
    if require_target.exists():
        raise SystemExit('Refuse to overwrite final fixture validation record')
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(test_fixtures.Fixtures)
    ids=[t.id() for t in suite]
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (out/'fixtures_final.log').write_text(stream.getvalue())
    paths=sorted(source.glob('*.py'))
    record=dict(status='SYNTHETIC_FIXTURES_PASS' if result.wasSuccessful() else 'SYNTHETIC_FIXTURES_FAIL',
                tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
                test_ids=ids,python=sys.version,numpy=np.__version__,
                code_sha256={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                actual_N8_arrays_loaded=False,actual_field_metrics_computed=False,
                PDE_backend_imported=False,PDE_assembled_or_solved=False,
                synthetic_fields_are_nodal_samples_not_PDE_solutions=True,
                physical_thresholds_activated=False,reference_qualified=False,
                strict_error_bound_established=False,
                real_archive_adapter_tested='Guard tested; dormant read branch static review only')
    require_target.write_text(json.dumps(record,indent=2)+'\n')
    print(record['status'], 'tests=',record['tests_run'],'failures=',record['failures'],'errors=',record['errors'])
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
