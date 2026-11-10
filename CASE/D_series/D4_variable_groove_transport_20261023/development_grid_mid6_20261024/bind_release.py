#!/usr/bin/env python3
"""Bind the completed local readiness package; refuse any existing release."""
from pathlib import Path
import csv,datetime,json,subprocess
from export_references import sha,load
HERE=Path(__file__).resolve().parent;CASE=HERE.parent;PROJECT=CASE.parents[2]
def main():
    if (HERE/'release.json').exists():raise SystemExit('existing release; never rebind in place')
    prep=load(HERE/'evidence/preparation.json');tests=load(HERE/'evidence/prebinding_review.json')
    assert prep['ok'] and tests['ok'] and tests['other_canonical_rows_rejected']==84
    assert prep['formal_steady_runs']==prep['collide_and_stream_calls']==0
    assert load(HERE/'evidence/scalar_adapter_regression/scalar_summary.json')['all_scalar_and_geometry_checks_passed']
    assert (HERE/'evidence/scalar_adapter_exit_code.txt').read_text().strip()=='0'
    assert (HERE/'evidence/flow_reader_regression_exit_code.txt').read_text().strip()=='0'
    assert load(HERE/'evidence/flow_reader_regression/flow_frames.json')['ok']
    assert load(HERE/'evidence/cli_prebinding.json')['ok']
    assert load(HERE/'evidence/system_python_tests.json')['ok']
    assert (HERE/'evidence/system_scalar_exit_code.txt').read_text().strip()=='0'
    assert (HERE/'evidence/final_flow_reader_exit_code.txt').read_text().strip()=='0'
    assert load(HERE/'evidence/final_flow_reader_regression/flow_frames.json')['ok']
    assert not (CASE/'results/development_grid_mid6_20261024_v1').exists()
    protected=load(PROJECT/'docs/reports/D4_grid_execution_review_20261024/protected_inputs_before.json')
    bind={str((Path(k) if Path(k).is_absolute() else PROJECT/k).resolve()):h for k,h in protected.items()}
    coarse=load(HERE/'evidence/coarse6_bundle.json');bind.update(coarse['bound_inputs_sha256'])
    for p in HERE.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.name not in ('release.json','execution.lock','startup_check.log','startup_console.log'):
            bind[str(p)]=sha(p)
    for k,h in bind.items():assert sha(k)==h,k
    commit=subprocess.check_output(['git','-C','/home/dell/openlb','rev-parse','HEAD'],text=True).strip();assert commit=='882924a9cfc8dcdf82909e39530789cb6f5ebcc4'
    rows=list(csv.DictReader((HERE/'stage_cases.csv').open()));assert len(rows)==6
    obj={'release_id':'D4_grid_mid6_local_release_20261024_v1','batch_id':'development_grid_mid6_20261024_v1','created_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'released':True,'meaning':'local technical readiness for explicit user start of MID6 only; not scientific acceptance','user_authorized_preparation':True,'AI_started_formal_run':False,'teacher_approval_independently_verified':False,'allowed_case_ids':[r['planned_case_id'] for r in rows],'allowed_role':'grid_reference','OpenLB_commit':commit,'bound_inputs_sha256':bind,'numerical_protocol':'original unchanged protocol/execution.json','grid_comparison_protocol':'new executable v2 retaining original research tolerances','analysis_automatically_run':False,'next_stage_automatically_run':False,'remaining_grid_released':False,'prediction_released':False}
    with (HERE/'release.json').open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'released_for_explicit_user_start':True,'cases':6,'bound_inputs':len(bind),'release_sha256':sha(HERE/'release.json'),'steady_started':False}))
if __name__=='__main__':main()
