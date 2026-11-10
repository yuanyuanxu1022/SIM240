"""Read-only six-result review. Only saved-result checkers may be executed."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import csv, hashlib, json, math, os, resource, subprocess, sys
import numpy as np

ROOT=Path('/home/dell/yuanyuanxu/SIM240')
OUT=Path(__file__).resolve().parent
S3=ROOT/'CASE/unseen_v2_reference_S3_reuse_v1_1'
C3=ROOT/'CASE/unseen_v2_reference_checker_S3_reuse_v1_1'
S2=ROOT/'CASE/unseen_v2_reference_S2_reuse_v1'
C2=ROOT/'CASE/unseen_v2_reference_checker_S2_reuse_v1'
R3=S3/'evidence/S3_formal_launch_release_v1_1_20261103_01.json'
H3='04836ee00515ac961f80022153eb398ea1692f03b943ca713e7414ce9716b574'
R2=S2/'evidence/S2_formal_launch_release_LRP_v1_20261102_02.json'
H2='d08297ebda69d9698d40762f778eb43299fa3c01c35e5591b6d31b4e06ef26cd'
sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p: json.loads(Path(p).read_text())
def save(name,value):
    with (OUT/name).open('x') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def limits():
    resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))

def main():
    assert sha(R3)==H3 and sha(R2)==H2
    b3,b2=load(R3),load(R2)
    protected=dict(b3['inputs_sha256'])
    assert all(sha(p)==h for p,h in protected.items())
    for tree in [S3/'runs',S3/'analysis_results',S3/'evidence',S3/'launch_attempts',
                 S2/'runs',S2/'analysis_results',S2/'evidence',S2/'launch_attempts',
                 ROOT/'docs/reports/URV_S3_formal_launch_release_v1_1_20261103',
                 ROOT/'docs/reports/URV_S3_formal_scope_review_20261103',
                 ROOT/'docs/reports/URV_S3_zero_results_review_v1_1_20261103',
                 ROOT/'docs/reports/URV_S2_completed_review_20261103_095422']:
        for p in tree.rglob('*'):
            if p.is_file():
                h=sha(p)
                assert str(p) not in protected or protected[str(p)]==h
                protected[str(p)]=h
    for p in [R3.with_suffix('.sha256'),Path(str(R2)+'.sha256'),S3/'S3_formal_controller_v1_1_20261103_01.log']:
        protected[str(p)]=sha(p)
    save('protected_inputs_and_outputs.json',protected)
    sys.path.insert(0,str(C3/'analysis'))
    import stage_s3,s3_baselines,evidence
    stage_s3.verify_seal(R3,H3);stage_s3.validate_formal_authority(b3)
    baseline_values=s3_baselines.verify_baselines(b3)
    batch=load(S3/'launch_attempts'/H3/'S3_completed.json')
    assert batch==dict(stage='S3_REG_LINEARITY',solver_runs=4,S3_CONTROL_PASS=True,
                      next_stage_started=False,reference_qualified=False,MODEL_COMPARISON='NOT_EVALUATED')
    records=[(S3,C3,R3,H3,b3,r,'S3_new') for r in b3['approved_runs']]
    records += [(S2,C2,R2,H2,b2,next(r for r in b2['approved_runs'] if r['run_id']==ref['run_id']),'S2_midpoint')
                for ref in b3['baseline_references']]
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
             QT_QPA_PLATFORM='offscreen',PYTHONDONTWRITEBYTECODE='1')
    env.pop('LD_LIBRARY_PATH',None);env.pop('LD_PRELOAD',None)
    reviews=[];accepted={};field_count=0
    for case,checker,release,digest,bound,rec,role in records:
        rid=rec['run_id'];run=Path(rec['output_directory']);target=OUT/('replay_'+rid)
        command=['/home/dell/miniconda3/bin/python3','-B',str(checker/'analysis/check_results.py'),
                 '--run',str(run),'--release',str(release),'--release-sha256',digest,'--out',str(target)]
        assert Path(command[2]).name=='check_results.py' and '--execute' not in command
        with (OUT/(rid+'_checker.log')).open('x') as log:
            proc=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,env=env,timeout=3600,preexec_fn=limits)
        save('checker_exit_'+rid+'.json',dict(command=command,exit_code=proc.returncode,solver_executed=False))
        assert proc.returncode==0,(rid,proc.returncode)
        a=load(target/'acceptance.json');fields=load(target/'fields.json')
        assert a==load(case/'analysis_results'/rid/'acceptance.json')
        assert fields==load(case/'analysis_results'/rid/'fields.json')
        assert fields['PASS'] and fields['actual_reader']
        accepted[rid]=a;field_count+=len(fields['frames'])
        comp=load(run/'completion.json')
        assert comp['inputs_before_sha256']==comp['inputs_after_sha256']==bound['inputs_sha256']
        assert comp['inputs_unchanged'] and comp['release_sha256']==digest
        assert comp['independent_process_exit_code']==0 and not comp['timed_out'] and comp['resource_stop_reason'] is None
        assert comp['elapsed_seconds']<=comp['solver_wall_cap_seconds']
        raw={str(p.relative_to(run)):sha(p) for p in run.rglob('*') if p.is_file() and p.name!='completion.json'}
        assert raw==comp['output_sha256']
        cfg=evidence.kv(run/'run_config.txt');r=evidence.kv(run/'result.txt');p=evidence.exact_parameters(cfg)
        with (run/'diagnostics.csv').open() as f: rows=list(csv.DictReader(f))
        x={k:np.array([float(z[k]) for z in rows]) for k in rows[0]}
        assert np.array_equal(x['step'],np.arange(len(rows))) and all(np.isfinite(z).all() for z in x.values())
        assert len(rows)==int(r['steps_completed'])+1
        J=float(x['J'][-1]);K=p['nu']*J/p['a'];assert K==a['scalar']['K_m3']
        mass=(x['corrected_mass']-x['corrected_mass'][0])/x['corrected_mass'][0]
        delta=(x['density_delta']-x['density_delta'][0])/(p['nodes']+x['density_delta'][0])
        legacy=(x['mass']-x['mass'][0])/x['mass'][0]
        n=p['window'];last=x['J'][-n:];prev=x['J'][-n-1:-1]
        std=float(np.std(last,ddof=1)/abs(np.mean(last)));span=float(np.ptp(last)/abs(np.mean(last)))
        prevstd=float(np.std(prev,ddof=1)/abs(np.mean(prev)));prevspan=float(np.ptp(prev)/abs(np.mean(prev)))
        cross=-x['Jx'] if cfg['direction']=='P' else x['Jy']
        allstd,allspan,allcross=evidence.window_metrics(x['J'],cross,n)
        passes=(allstd<=1e-6)&(allspan<=5e-6)&(allcross<=1e-12)
        assert passes[-1] and not passes[:-1].any()
        assert prevstd>1e-6 or prevspan>5e-6 or max(abs(cross[-n-1:-1]))>1e-12
        rho=float(x['max_density_deviation'].max());mach=float(x['Mach'].max())
        Re=mach/math.sqrt(3)*p['dx']/p['dt']*(p['h']+p['d'])/p['nu']
        den=np.maximum(abs(x['Q_section1']),abs(x['Q_section2']))
        sec=np.divide(abs(x['Q_section1']-x['Q_section2']),den,out=np.zeros_like(den),where=den>0)
        volume=float(r['fluid_volume_m3'])/(p['P']*p['Ly']*p['H'])-1
        v=dict(run_id=rid,role=role,direction=cfg['direction'],acceleration_m_s2=p['a'],dx_nm=float(cfg['dx_nm']),
            release_sha256=digest,completion_sha256=sha(run/'completion.json'),steps=len(rows)-1,diagnostic_rows=len(rows),
            full_windows=len(allstd),first_accepted_window_is_final=True,solver_seconds=comp['elapsed_seconds'],
            solver_cap_seconds=comp['solver_wall_cap_seconds'],J_m2_s=J,K_m3=K,U_mean_m_s=J/p['H'],R_Pa_s_per_m3=.001/K,
            window_steps=n,window_std=std,window_span=span,previous_window_std=prevstd,previous_window_span=prevspan,
            cross_flux_window_max=float(allcross[-1]),corrected_mass_max=float(abs(mass).max()),
            legacy_mass_max=float(abs(legacy).max()),ledger_max=float(abs(mass-delta).max()),
            density_deviation_max=rho,Mach_max=mach,Re_H_max=Re,section_final=float(sec[-1]),
            volume_relative_error=volume,core_fluid_nodes=p['nodes'],installed_links=int(r['installed_links']),
            fallback=int(r['fallback_count']),unresolved=int(r['unresolved_links']),q_min=float(r['q_min']),q_max=float(r['q_max']),
            field_frames=len(fields['frames']),raw_files=len(raw),raw_bytes=sum((run/f).stat().st_size for f in raw),
            original_and_replay_acceptance_equal=True,original_and_replay_fields_equal=True,checker_exit=0,
            NUMERICAL_GATE=a['NUMERICAL_GATE'],geometry_PASS=a['geometry_PASS'],RESULT_PASS=a['RESULT_PASS'],
            REFERENCE_QUALIFIED_FOR_CASE=False)
        assert abs(mass).max()<1e-10 and abs(mass-delta).max()<=1e-13 and rho<=1e-6 and mach<.05 and Re<=.01
        assert std<=1e-6 and span<=5e-6 and sec[-1]<=1e-5 and abs(volume)<=1e-10
        reviews.append(v);save('progress_'+str(len(reviews))+'.json',v)
        print(json.dumps(dict(done=rid,K=K,steps=v['steps'],frames=v['field_frames'])),flush=True)
    controls=[]
    for d in ['P','T']:
        report=s3_baselines.control_for_direction(b3,d,accepted,H3)
        assert report==load(S3/'launch_attempts'/H3/f'linearity_{d}.json')
        points=sorted([v for v in reviews if v['direction']==d],key=lambda v:v['acceleration_m_s2'])
        assert [v['acceleration_m_s2'] for v in points]==[50000,100000,200000]
        ks=[v['K_m3'] for v in points];L=(max(ks)-min(ks))/(sum(ks)/3)
        assert math.isclose(L,report['K_span_over_mean'],rel_tol=2e-15) and L<=.001
        assert points[1]['K_m3']==baseline_values[d]
        cfgs=[evidence.kv(Path(next(r['output_directory'] for r in (b3['approved_runs']+b2['approved_runs']) if r['run_id']==v['run_id']))/'run_config.txt') for v in points]
        stripped=[{k:val for k,val in c.items() if k not in ['run_id','output_directory','acceleration_m_s2']} for c in cfgs]
        assert stripped[0]==stripped[1]==stripped[2]
        controls.append(dict(**report,L_percent=100*L,L_ppm=1e6*L,
            independently_recomputed=True,controller_receipt_exact=True,
            endpoint_J_ratio=points[-1]['J_m2_s']/points[0]['J_m2_s'],
            K_low_over_mid_minus_one=ks[0]/ks[1]-1,K_high_over_mid_minus_one=ks[2]/ks[1]-1,
            same_configuration_except_identity_output_force=True))
    assert all(sha(p)==h for p,h in protected.items()),'protected evidence drift'
    result=dict(reviewed_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        protocols=['URV-v1','MRP','A1','S3 v1.1','S3-FRD-v1'],S3_release_sha256=H3,S2_release_sha256=H2,
        S3_inputs_verified=len(b3['inputs_sha256']),S2_inputs_verified=len(b2['inputs_sha256']),
        protected_files_unchanged=len(protected),full_checker_replays=6,all_receipts_and_fields_exact=True,
        actual_VTK_reader_invocations=6,total_field_frames_read=field_count,runs=reviews,controls=controls,
        diagnostic_rows=sum(v['diagnostic_rows'] for v in reviews),full_windows=sum(v['full_windows'] for v in reviews),
        formal_S3_solver_seconds=sum(v['solver_seconds'] for v in reviews if v['role']=='S3_new'),
        S3_FOUR_RUN_ACCEPTANCE=True,S2_TWO_MIDPOINT_REUSE_ACCEPTANCE=True,S3_CONTROL_PASS=True,
        solver_calls=0,builds=0,retries=0,extensions=0,S4_started=False,S5_started=False,
        REFERENCE_QUALIFIED_FOR_CASE=False,reference_qualified=False,MODEL_COMPARISON='NOT_EVALUATED',
        physical_validation='NOT_EVALUATED',strict_error_bound_established=False,submission_ready=False,
        F04='OPEN_OUT_OF_SCOPE',human_scientific_final_review=False)
    save('independent_review.json',result)
    with (OUT/'run_summary.csv').open('x') as f:
        writer=csv.DictWriter(f,fieldnames=list(reviews[0]));writer.writeheader();writer.writerows(reviews)
    print('REVIEW_COMPLETE '+str(OUT),flush=True)

if __name__=='__main__': main()
