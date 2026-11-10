"""Read-only S2 baseline references; never rebind an old result to S3."""
from pathlib import Path
import json
import numpy as np
from evidence import need,sha,kv,close

S2=Path('/home/dell/yuanyuanxu/SIM240/CASE/unseen_v2_reference_S2_reuse_v1')
S2_RELEASE=S2/'evidence/S2_formal_launch_release_LRP_v1_20261102_02.json'
S2_SHA='d08297ebda69d9698d40762f778eb43299fa3c01c35e5591b6d31b4e06ef26cd'
BASE_IDS={d:f'URV_S2_{d}_dx2p5_reuse_v1_20261102_01' for d in ('P','T')}

def verify_baselines(bound):
    from contracts import covered
    refs=bound.get('baseline_references')
    need(isinstance(refs,list) and [r.get('direction') for r in refs]==['P','T'], 'exact ordered S2 baseline pair required')
    inputs=bound['inputs_sha256'];covered(str(S2_RELEASE),inputs)
    need(sha(S2_RELEASE)==S2_SHA,'original S2 release changed')
    prior=json.loads(S2_RELEASE.read_text())
    need(all(inputs.get(p)==h for p,h in prior['inputs_sha256'].items()),'S3 drops or changes historical S2 input')
    values={}
    for ref in refs:
        d=ref['direction'];rid=BASE_IDS[d];ident=f'URV1_U_REG_{d}_dx2p5_a100000'
        record=next(r for r in prior['approved_runs'] if r['run_id']==rid)
        need(ref.get('run_id')==rid and ref.get('planned_case_id')==ident and
             ref.get('release_path')==str(S2_RELEASE) and ref.get('release_sha256')==S2_SHA,'wrong baseline identity/release')
        run=Path(record['output_directory']);cp=run/'completion.json';ap=S2/'analysis_results'/rid/'acceptance.json'
        for key,path in [('config',Path(record['run_config_path'])),('completion',cp),('acceptance',ap)]:
            need(ref.get(key+'_path')==str(path) and ref.get(key+'_sha256')==sha(covered(str(path),inputs)), 'baseline file binding mismatch: '+key)
        comp=json.loads(cp.read_text());accepted=json.loads(ap.read_text());cfg=kv(record['run_config_path'])
        need(comp['run_id']==accepted['run_id']==rid and comp['planned_case_id']==accepted['planned_case_id']==ident,'baseline actual identity')
        need(comp['release_sha256']==accepted['release_sha256']==S2_SHA and accepted['completion_sha256']==sha(cp),'baseline completion/release substitution')
        need(comp['inputs_before_sha256']==comp['inputs_after_sha256']==prior['inputs_sha256'] and comp['inputs_unchanged'] is True,'baseline historical input drift')
        need(comp['independent_process_exit_code']==accepted['independent_exit_code']==0 and
             comp['timed_out'] is False and comp.get('resource_stop_reason') is None,'baseline exit/resource failure')
        need(accepted['RESULT_PASS'] is True and accepted['NUMERICAL_GATE']=='PASS' and accepted['geometry_PASS'] is True,'baseline not accepted')
        need(accepted['stage']=='S2_REG_GRID' and cfg['direction']==accepted['direction']==d and
             float(cfg['acceleration_m_s2'])==100000 and float(cfg['dx_nm'])==2.5,'wrong baseline physical role')
        actual={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name!='completion.json'}
        need(actual==set(comp['output_sha256']),'baseline raw file set changed')
        for relative,h in comp['output_sha256'].items():
            p=(run/relative).resolve();need(p.is_relative_to(run),'baseline output escape')
            need(sha(covered(str(p),inputs))==h,'baseline raw content drift')
        result=kv(run/'result.txt');K=float(accepted['scalar']['K_m3'])
        need(K>0 and np.isfinite(K) and close(K,float(result['Keff_m3']),rtol=1e-13),'baseline K differs from raw result')
        need(ref.get('K_m3')==K,'baseline declared K differs from accepted result')
        values[d]=K
    return values

def linear_metric(values):
    a=np.asarray(values,dtype=float)
    need(a.shape==(3,) and np.isfinite(a).all() and np.all(a>0),'three positive finite conductances required')
    metric=float(np.ptp(a)/a.mean())
    return dict(K_span_over_mean=metric,limit=.001,CONTROL_PASS=metric<=.001)

def control_for_direction(bound,direction,accepted,release_sha):
    """Verify each S3 point under its own completion, S2 midpoint under S2."""
    from contracts import covered
    need(direction in ('P','T'),'unknown direction')
    base=verify_baselines(bound);needed=[r for r in bound['prepared_runs'] if kv(r['run_config_path'])['direction']==direction]
    need(len(needed)==2,'exact low/high new points required')
    result={100000.:base[direction]};evidence=[]
    for record in needed:
        rid=record['run_id'];need(rid in accepted,'missing new linearity point')
        a=accepted[rid];cfg=kv(record['run_config_path']);force=float(cfg['acceleration_m_s2'])
        need(a['run_id']==rid and a['planned_case_id']==record['planned_case_id'] and
             a['direction']==direction and a['stage']=='S3_REG_LINEARITY' and a['dx_nm']==2.5 and
             a['acceleration_m_s2']==force,'new point identity/force/stage mismatch')
        need(a['RESULT_PASS'] is True and a['NUMERICAL_GATE']=='PASS' and a['geometry_PASS'] is True and
             a['independent_exit_code']==0,'new point not accepted')
        need(force in (50000.,200000.) and force not in result,'duplicate or wrong new force')
        run=Path(record['output_directory']);completion=run/'completion.json';c=json.loads(completion.read_text())
        need(a['completion_sha256']==sha(completion) and a['release_sha256']==c['release_sha256']==release_sha,'new point completion substitution')
        need(c['inputs_before_sha256']==c['inputs_after_sha256']==bound['inputs_sha256'] and c['inputs_unchanged'] is True,'new point input closure mismatch')
        need(c['run_id']==rid and c['planned_case_id']==record['planned_case_id'] and c['independent_process_exit_code']==0 and
             c['timed_out'] is False and c.get('resource_stop_reason') is None,'new point completion identity/exit')
        actual={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name!='completion.json'}
        need(actual==set(c['output_sha256']), 'new point raw file set changed')
        for relative,h in c['output_sha256'].items():
            p=(run/relative).resolve();need(p.is_relative_to(run) and sha(p)==h,'new point raw output changed')
        raw=kv(run/'result.txt');Kraw=float(cfg['nu_m2_s'])*float(raw['J_main_m2_s'])/force
        need(close(float(a['scalar']['K_m3']),Kraw,rtol=1e-13),'new point K differs from raw result')
        result[force]=float(a['scalar']['K_m3']);evidence.append(dict(run_id=rid,release_sha256=a['release_sha256'],completion_sha256=a['completion_sha256']))
    report=linear_metric([result[a] for a in (50000.,100000.,200000.)])
    return dict(direction=direction,accelerations_m_s2=[50000,100000,200000],K_m3=[result[a] for a in (50000.,100000.,200000.)],
        S2_midpoint_run_id=BASE_IDS[direction],S2_release_sha256=S2_SHA,S3_points=evidence,
        REFERENCE_QUALIFIED_FOR_CASE=False,MODEL_COMPARISON='NOT_EVALUATED',physical_validation='NOT_EVALUATED',**report)
