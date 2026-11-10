"""Stage-local original three-grid arithmetic from already accepted raw packets."""
from pathlib import Path
import json,math
from evidence import need,sha,kv,grid_estimate

def grid_for_direction(bound,direction,accepted,release_sha):
    need(direction in ('P','T'),'unknown grid direction')
    records=[r for r in bound['prepared_runs'] if kv(r['run_config_path'])['direction']==direction]
    need(len(records)==3,'exact three-grid direction required');ks=[];spans=[];points=[]
    for rec,dx in zip(records,[5.,2.5,1.25]):
        rid=rec['run_id'];need(rid in accepted,'missing grid acceptance');a=accepted[rid]
        cfg=kv(rec['run_config_path']);need(sha(rec['run_config_path'])==rec['run_config_sha256'],'grid config changed')
        need(float(cfg['dx_nm'])==dx and float(cfg['h_nm'])==30 and float(cfg['d_nm'])==80 and float(cfg['acceleration_m_s2'])==100000,'wrong thin-grid physical role')
        need(a['run_id']==rid and a['planned_case_id']==rec['planned_case_id'] and a['stage']=='S4_THIN_GRID' and
             a['direction']==direction and a['dx_nm']==dx and a['acceleration_m_s2']==100000,'grid acceptance identity mismatch')
        need(a['RESULT_PASS'] is True and a['NUMERICAL_GATE']=='PASS' and a['geometry_PASS'] is True and a['independent_exit_code']==0,'grid point not accepted')
        run=Path(rec['output_directory']);cp=run/'completion.json';c=json.loads(cp.read_text())
        need(a['completion_sha256']==sha(cp) and a['release_sha256']==c['release_sha256']==release_sha,'grid completion binding mismatch')
        need(c['run_id']==rid and c['planned_case_id']==rec['planned_case_id'] and c['independent_process_exit_code']==0 and c['timed_out'] is False and c['resource_stop_reason'] is None,'grid process failure')
        need(c['inputs_before_sha256']==c['inputs_after_sha256']==bound['inputs_sha256'] and c['inputs_unchanged'] is True,'grid source drift')
        actual={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name!='completion.json'}
        need(actual==set(c['output_sha256']),'grid raw file set changed')
        for name,h in c['output_sha256'].items():
            p=(run/name).resolve();need(p.is_relative_to(run) and sha(p)==h,'grid raw drift')
        raw=kv(run/'result.txt');K=float(cfg['nu_m2_s'])*float(raw['J_main_m2_s'])/100000
        need(math.isfinite(K) and K>0 and math.isclose(K,a['scalar']['K_m3'],rel_tol=1e-13),'grid K disagrees with raw result')
        span=float(a['scalar']['final_span']);need(math.isfinite(span) and 0<=span<=5e-6,'invalid accepted span')
        need(math.isclose(span,float(raw['window_main_rel_span']),rel_tol=1e-6,abs_tol=1e-12),'grid span disagrees with raw result')
        ks.append(K);spans.append(span);points.append(dict(run_id=rid,completion_sha256=sha(cp)))
    estimate=grid_estimate(*ks,spans[-1]);ok=bool(estimate.pop('REFERENCE_QUALIFIED_FOR_CASE'))
    return dict(direction=direction,dx_nm=[5,2.5,1.25],K_m3=ks,points=points,grid_estimate=estimate,
        GRID_CHECKS_PASS=ok,REFERENCE_QUALIFIED_FOR_CASE=False,reference_qualified=False,
        MODEL_COMPARISON='NOT_EVALUATED',physical_validation='NOT_EVALUATED',submission_ready=False,
        strict_error_bound_established=False,S5_control='NOT_EVALUATED')
