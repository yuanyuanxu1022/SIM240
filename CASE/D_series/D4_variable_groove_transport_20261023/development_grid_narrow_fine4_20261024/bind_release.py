#!/usr/bin/env python3
"""Freeze local NARROW_FINE4 readiness; never start or rebind an existing release."""
from pathlib import Path
import csv,datetime,json,subprocess
from export_references import sha,load,verify_bundle
HERE=Path(__file__).resolve().parent;CASE=HERE.parent;PROJECT=CASE.parents[2]
def main():
    if (HERE/'release.json').exists():raise SystemExit('release already exists; no in-place rebinding')
    prep=load(HERE/'evidence/preparation.json');tests=load(HERE/'evidence/prebinding_review.json')
    assert prep['ok'] and tests['ok'] and prep['stage_cases']==4 and tests['other_canonical_rows_rejected']==86
    assert prep['formal_steady_runs']==prep['collide_and_stream_calls']==0
    assert load(HERE/'evidence/cli_prebinding.json')['ok']
    assert load(HERE/'evidence/scalar_adapter_regression/scalar_summary.json')['all_scalar_and_geometry_checks_passed']
    assert (HERE/'evidence/scalar_adapter_exit_code.txt').read_text().strip()=='0'
    assert (HERE/'evidence/flow_reader_exit_code.txt').read_text().strip()=='0' and load(HERE/'evidence/flow_reader_regression/flow_frames.json')['ok']
    parent=PROJECT/'docs/reports/D4_grid_mid6_acceptance_20261024'
    assert load(parent/'verdict.json')['independent_MID6_acceptance']=='PASS'
    assert load(parent/'independent/certificate.json')['independent_acceptance']=='PASS'
    assert len(verify_bundle(HERE/'evidence/upstream12_bundle.json'))==12
    assert not (CASE/'results/development_grid_narrow_fine4_20261024_v1').exists()
    report=PROJECT/'docs/reports/D4_grid_narrow_fine4_preparation_20261024'
    bind=load(report/'protected_inputs_before.json')
    for p,h in load(HERE/'evidence/upstream12_bundle.json')['bound_inputs_sha256'].items():
        if p in bind:assert bind[p]==h
        bind[p]=h
    for file in ['resource_budget.json','case_budget4.csv','implementation_provenance.json']:
        p=report/file;bind[str(p)]=sha(p)
    for p in HERE.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.name not in ('release.json','execution.lock','startup_check.log','startup_console.log'):bind[str(p)]=sha(p)
    for k,h in bind.items():assert sha(k)==h,k
    commit=subprocess.check_output(['git','-C','/home/dell/openlb','rev-parse','HEAD'],text=True).strip();assert commit=='882924a9cfc8dcdf82909e39530789cb6f5ebcc4'
    rows=list(csv.DictReader((HERE/'stage_cases.csv').open()));assert len(rows)==4
    obj={'release_id':'D4_grid_narrow_fine4_local_release_20261024_v1','batch_id':'development_grid_narrow_fine4_20261024_v1','created_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'released':True,'meaning':'local technical readiness for user-started four narrow 1.25nm cases only; not scientific acceptance','user_authorized_preparation':True,'AI_started_formal_run':False,'teacher_approval_independently_verified':False,'allowed_case_ids':[r['planned_case_id'] for r in rows],'allowed_role':'grid_reference','OpenLB_commit':commit,'bound_inputs_sha256':bind,'numerical_protocol':'original unchanged protocol/execution.json','comparison_protocol':'byte-identical frozen executable v2 from MID6','analysis_automatically_run':False,'next_stage_automatically_run':False,'wide_fine_grid_released':False,'prediction_released':False}
    with (HERE/'release.json').open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'ready_for_user_start':True,'allowed_cases':4,'bound_paths':len(bind),'release_sha256':sha(HERE/'release.json'),'steady_started':False}))
if __name__=='__main__':main()
