#!/usr/bin/env python3
"""Bind existing verified prerequisites and describe configs only; never advances flow."""
from pathlib import Path
import ast,csv,datetime,hashlib,importlib.util,json,shlex,subprocess,sys
ROOT=Path(__file__).resolve().parent;CASE=ROOT.parent;PROJECT=CASE.parents[2]
spec=importlib.util.spec_from_file_location('stage',ROOT/'run_development.py');stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)
sha=stage.sha

def main():
    if (ROOT/'release.json').exists():raise SystemExit('release exists; preserve frozen preparation')
    foundation=PROJECT/'docs/reports/D4_foundation_acceptance_20261023'
    accepted=json.loads((foundation/'complete/acceptance.json').read_text())
    assert accepted['foundation_acceptance']=='PASS' and accepted['completed_cases']==8 and accepted['frames_read']==74
    prior=json.loads((CASE/'evidence/formal_run_release.json').read_text())
    binding=dict(prior['bound_inputs_sha256'])
    for p,h in binding.items():assert sha(p)==h,p
    for p,h in json.loads((foundation/'complete/all_raw_files_sha256.json').read_text()).items():assert sha(p)==h,p
    for p,h in json.loads((foundation/'complete/analysis_scripts_sha256.json').read_text()).items():assert sha(foundation/p)==h,p
    for p,h in json.loads((CASE/'evidence/protected_inputs.json').read_text()).items():assert sha(PROJECT/p)==h,p
    for f in foundation.glob('complete/*'):
        if f.is_file():binding[str(f.resolve())]=sha(f)
    # Pin all original run evidence (CSV, VTM and referenced payloads) as prerequisites.
    binding.update(json.loads((foundation/'complete/all_raw_files_sha256.json').read_text()))
    for p in ROOT.glob('*.py'):ast.parse(p.read_text())
    source_rows={r['planned_case_id']:r for r in stage.base.candidates()}
    rows=stage.rows();assert len(rows)==20
    selected=[r for r in rows if r['substage']=='screen'];assert len(selected)==6
    assert {r['acceleration_m_s2'] for r in selected}=={'50000','100000','200000'}
    pre=json.loads((CASE/'evidence/preflight.json').read_text());checks=[]
    for i,r in enumerate(rows):
        original={k:v for k,v in r.items() if k!='substage'};assert original==source_rows[r['planned_case_id']]
        assert r['blind_geometry']=='False' and r['role'] in ['new_dev','linearity']
        match=next(g for g in pre['geometry_records'] if all(stage.base.kv(CASE/g['output']/'run_config.txt')[k]==r[v]
            for k,v in [('h_nm','h_nm'),('d_nm','d_nm'),('w_nm','w_nm'),('period_nm','P_nm'),('dx_nm','dx_nm'),('Ly_nm','Ly_nm')]))
        boundary=stage.base.kv(CASE/match['output']/'boundary_audit.txt')
        assert boundary['geometry_PASS']=='true' and boundary['q_audit_PASS']=='true'
        out,code=stage.base.launch(r,'describe',ROOT/'evidence/configuration',f'devprep_{i:02}')
        assert code==0
        eff=stage.base.kv(out/'effective_config.txt')
        for k,col in [('h_m','h_nm'),('d_m','d_nm'),('w_m','w_nm'),('Lx_m','P_nm'),('Ly_m','Ly_nm'),('dx_m','dx_nm')]:
            assert abs(float(eff[k])-float(r[col])*1e-9)<1e-20
        checks.append({'planned_case_id':r['planned_case_id'],'substage':r['substage'],'description_output':str(out.relative_to(ROOT)),
            'geometry_evidence':match['output'],'geometry_nodes':match['nodes'],'collide_and_stream_calls':0})
    report={'ok':True,'described_rows':20,'screen_cases':6,'held_remaining_cases':14,
        'existing_unique_actual_meshes_reused':8,'checks':checks,'solver_time_advancement_calls':0,
        'foundation_cases':8,'foundation_frames':74,'teacher_approval_independently_verified':False}
    (ROOT/'evidence/preparation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    policy=json.loads((ROOT/'policy.json').read_text())
    inner=f'cd {shlex.quote(str(CASE))} && exec python3 development_stage_20261023/run_development.py --batch-id {policy["batch_id"]} --execute'
    command='tmux new-session -d -s d4-dev-screen-20261023 '+shlex.quote(inner)
    subprocess.run(['bash','-n'],input=command,text=True,check=True)
    (ROOT/'NEXT_COMMAND.txt').write_text(command+'\n')
    for p in ROOT.rglob('*'):
        if p.is_file() and p.suffix not in ['.pyc'] and '__pycache__' not in p.parts and p.name!='release.json':binding[str(p.resolve())]=sha(p)
    release={'released':True,'release_kind':'technical_launch_preconditions_for_user_started_development_screen_only',
        'allowed_case_ids':[r['planned_case_id'] for r in selected],'bound_inputs_sha256':binding,
        'user_start_required':True,'teacher_approval_independently_verified':False,'next_stage_released':False,
        'steady_runs_started_by_preparation':0,'NUMERICAL_GATE':'NOT_EVALUATED','RESULT_PASS':False}
    # Every other row is rejected by the same stage validation used at runtime.
    rejected=0
    for r in rows:
        if r['substage']=='screen':stage.validate_row(r,release)
        else:
            try:stage.validate_row(r,release)
            except RuntimeError:rejected+=1
            else:raise AssertionError('held row accepted')
    assert rejected==14
    (ROOT/'release.json').write_text(json.dumps(release,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False))
if __name__=='__main__':main()
