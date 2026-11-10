#!/usr/bin/env python3
"""Check this documentary scope and old-file preservation; no native execution."""
from pathlib import Path
import ast
import hashlib
import json
import datetime

ROOT=Path('/home/dell/yuanyuanxu/SIM240')
OUT=Path(__file__).resolve().parent


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    scope=json.loads((OUT/'minimum_scope.json').read_text())
    protocol=json.loads((ROOT/'docs/reports/URV_S2_minimum_preparation_protocol_20261102/performance_protocol.json').read_text())
    review=json.loads((OUT/'B_compatibility_audit.json').read_text())
    B_path=Path(scope['B_path']);B=json.loads(B_path.read_text())
    assert sha(B_path)==scope['B_sha256']==review['expected_B_sha256']
    assert len(B['inputs_sha256'])==1816
    for key in ['resources','budget','performance_windows','native_window_steps','native_maximum_steps']:
        assert scope[key]==protocol[key],key
    assert scope['candidate_cases']==protocol['candidate_cases']
    assert scope['formal_wall_cap_seconds_fine']==43200
    assert scope['native_config_allowed_changes']==['run_id','output_directory']
    assert len(scope['proposed_modules'])==4
    for key in ['implementation_completed','build_authorized','native_zero_step_authorized',
                'performance_time_stepping_authorized','formal_simulation_authorized',
                'launch_contract_generated','start_command_delivered','case_directory_created']:
        assert scope[key] is False,key
    for key in ['approved_benchmark_run_ids','approved_formal_run_ids','actual_benchmark_run_ids','new_actual_run_ids']:
        assert scope[key]==[],key
    assert not Path(scope['proposed_case_directory']).exists()
    assert all(scope[k]==protocol['scientific_outputs'][k] for k in protocol['scientific_outputs'])
    assert scope['geometry_PASS'] is None
    records=json.loads((OUT/'fine_config_review.json').read_text())
    assert [r['source_record']['planned_case_id'] for r in records]==scope['candidate_cases']
    assert all(r['candidate_perf_run_id'] is None and r['actual_performance_run_id'] is None for r in records)
    for name in ['audit_existing.py','verify_review.py']:
        tree=ast.parse((OUT/name).read_text())
        assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in
                       ('Popen','run','system','execv','execve') for n in ast.walk(tree))
    protected=json.loads((OUT/'protected_inputs_before.json').read_text())
    drift=[p for p,h in protected.items() if not Path(p).is_file() or sha(p)!=h]
    assert not drift,drift
    reviewed=json.loads((OUT/'reviewed_inputs_sha256.json').read_text())
    assert all(sha(p)==h for p,h in reviewed.items())
    for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        old=(OUT/('before_'+name)).read_text()
        now=(ROOT/'docs/reports'/name).read_text()
        assert old.split('\n## ',2)[2]==now.split('\n## ',2)[2],name+' historical tail changed'
        assert 'S2性能兼容性审核完成' in now.split('\n## ',2)[1]
    result=dict(checked_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
        DOCUMENTARY_REVIEW_CHECK_PASS=True,scientific_or_performance_acceptance=False,
        protocol_budget_resources_windows_preserved=True,permissions_closed=True,
        B_inputs_unchanged=1816,protected_old_files=len(protected),old_file_drift=[],
        reviewed_input_files=len(reviewed),state_handoff_historical_tails_unchanged=True,
        performance_CASE_not_created=True,performance_implementation_not_created=True,
        native_calls=0,VTK_reader_calls=0,builds=0,time_steps=0,
        new_run_ids=[],performance_release_generated=False,start_command_delivered=False)
    (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    manifest={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*')
              if p.is_file() and p.name!='report_manifest.json'}
    (OUT/'report_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
