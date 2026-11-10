#!/usr/bin/env python3
"""Join independent scalar and VTK evidence, bind raw data, preserve frozen inputs."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]
CASE=PROJECT/'CASE/D_series/D4_variable_groove_transport_20261023'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out=ROOT/'complete';scalar=json.loads((out/'scalar_summary.json').read_text());fields=json.loads((out/'flow_frames.json').read_text())
    assert scalar['whole_batch_complete'] and scalar['all_scalar_and_geometry_checks_passed'] and fields['ok'] and fields['cases']==8
    protected=json.loads((CASE/'evidence/protected_inputs.json').read_text())
    assert all(sha(PROJECT/p)==h for p,h in protected.items())
    hashes={}
    for name in ['input_hashes.json','flow_files_sha256.json']:
        for p,h in json.loads((out/name).read_text()).items():
            actual=Path(p) if Path(p).is_absolute() else PROJECT/p
            assert sha(actual)==h,p
            hashes[str(actual)]=h
    # Record all batch payloads, even auxiliary output not used as acceptance input.
    batch=CASE/'results/foundation_20261023_v1'
    for p in batch.rglob('*'):
        if p.is_file():hashes[str(p)]=sha(p)
    release=json.loads((CASE/'evidence/formal_run_release.json').read_text())
    for p,h in release['bound_inputs_sha256'].items():assert sha(Path(p))==h
    result={'foundation_acceptance':'PASS','independent_NUMERICAL_GATE':'PASS','geometry_PASS':True,
            'FOUNDATION_RESULT_PASS':True,'solver_raw_RESULT_PASS':'false (preserved)',
            'scope':'8 foundation cases only: smooth baseline, legacy regression, time-series output',
            'batch_id':'foundation_20261023_v1','completed_cases':8,'diagnostic_rows':scalar['diagnostic_rows'],
            'frames_read':fields['frames_read'],'original_protected_files_unchanged':len(protected),
            'release_bound_inputs_unchanged':len(release['bound_inputs_sha256']),
            'raw_and_scalar_hash_files':len(hashes),'analysis_started_solver':False,
            'frozen_protocol_changed':False,'historical_results_changed':False,
            'next_stage_preparation_eligible':True,'next_stage_execution_released':False,
            'current_release_allowed_case_count':len(release['allowed_case_ids']),
            'next_action':'Prepare and review development-stage cases and numerical references; preserve prediction lock before test data.',
            'not_established':['new-width accuracy','grid independence over candidate range','final correlation prediction validation']}
    scripts={p.name:sha(p) for p in ROOT.glob('*.py')}
    (out/'all_raw_files_sha256.json').write_text(json.dumps(hashes,indent=2,ensure_ascii=False))
    (out/'acceptance.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    (out/'analysis_scripts_sha256.json').write_text(json.dumps(scripts,indent=2))
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
