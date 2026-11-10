#!/usr/bin/env python3
"""Fail-closed URV-v1 acceptance of completed results; never executes the solver.

Native zero-step outputs cannot pass. CLI requires a separately approved execution
release and its independently supplied SHA. The current preparation seal is rejected.
"""
from pathlib import Path
import argparse
import json
import math
import os
import subprocess
import sys
import numpy as np
from evidence import (need,sha,kv,rows,save,close,exact_parameters,check_boundary,
                      window_metrics,grid_estimate,sensitivity)

CASE=Path(__file__).resolve().parents[1]
LIMITS=json.loads((CASE/'common/acceptance_spec.json').read_text())

def diagnostics(config, result, data):
    """Pure arithmetic acceptance. Callable only on explicit supplied arrays."""
    p=exact_parameters(config);L=LIMITS['per_run'];n=p['window']
    required=['step','J','rho','Mach','mass','time_s','mass_error','max_density_deviation',
        'Jx','Jy','Jz','Q_section1','Q_section2','section_relative_difference',
        'pressure_min','pressure_max','window_rel_std','window_rel_span','window_cross_abs_max',
        'finite','corrected_mass','corrected_mass_error','delta_mass_error','mass_ledger_agreement','density_delta']
    need(set(required)==set(data), 'diagnostic schema mismatch')
    N=len(data['J']);steps=int(result['steps_completed'])
    need(N==steps+1 and n<=N and steps<=p['cap'], 'incomplete or excessive trajectory')
    need(all(len(v)==N and np.isfinite(v).all() for v in data.values()), 'nonfinite/misaligned trajectory')
    need(np.array_equal(data['step'],np.arange(N)), 'missing or reordered steps')
    need(np.all(data['finite']==1), 'nonfinite measurement flag')
    need(close(data['time_s'],np.arange(N)*p['dt'],rtol=1e-13,atol=1e-24), 'time units')
    for key in ['Mach','max_density_deviation','mass_ledger_agreement']:
        need(np.all(data[key]>=0), 'negative magnitude '+key)
    need(np.all(data['mass']>0) and np.all(data['corrected_mass']>0), 'nonpositive physical mass')
    need(close(data['corrected_mass'][0],1000*p['nodes']*p['dx']**3), 'initial mass/units')
    legacy=(data['mass']-data['mass'][0])/data['mass'][0]
    corrected=(data['corrected_mass']-data['corrected_mass'][0])/data['corrected_mass'][0]
    delta=(data['density_delta']-data['density_delta'][0])/(p['nodes']+data['density_delta'][0])
    ledger=np.abs(corrected-delta)
    for actual,key in [(legacy,'mass_error'),(corrected,'corrected_mass_error'),
                       (delta,'delta_mass_error'),(ledger,'mass_ledger_agreement')]:
        need(close(actual,data[key],rtol=1e-10,atol=1e-16), 'independent mass recomputation '+key)
    main=data['Jy'] if config['direction']=='P' else data['Jx']
    cross=-data['Jx'] if config['direction']=='P' else data['Jy']
    need(close(main,data['J'],rtol=1e-13,atol=1e-30), 'directional main flux')
    std,span,crossmax=window_metrics(main,cross,n)
    need(all(np.all(data[k][:n-1]==-1) for k in ['window_rel_std','window_rel_span','window_cross_abs_max']), 'premature window metrics')
    for actual,key,tol in [(std,'window_rel_std',1e-12),(span,'window_rel_span',1e-12),
                           (crossmax,'window_cross_abs_max',1e-28)]:
        need(close(actual,data[key][n-1:],rtol=1e-5,atol=tol), 'window recomputation '+key)
    accepted=(std<=L['window_relative_sample_std_max'])&(span<=L['window_relative_span_max'])&(crossmax<=L['cross_flux_abs_m2_s_max'])
    need(bool(accepted[-1]) and not np.any(accepted[:-1]), 'final step is not first acceptable statistical window')
    q1,q2=data['Q_section1'],data['Q_section2'];den=np.maximum(np.abs(q1),np.abs(q2))
    section=np.divide(np.abs(q1-q2),den,out=np.zeros_like(den),where=den>0)
    need(close(section,data['section_relative_difference'],rtol=1e-6,atol=1e-15), 'section recomputation')
    worst_mass=float(np.abs(corrected).max());worst_ledger=float(ledger.max())
    worst_rho=float(data['max_density_deviation'].max());worst_mach=float(data['Mach'].max())
    Re=worst_mach/math.sqrt(3)*p['dx']/p['dt']*(p['h']+p['d'])/p['nu']
    need(worst_mass<L['compensated_mass_relative_strict'], 'corrected mass gate')
    need(worst_ledger<=L['ledger_agreement_max'], 'mass ledger agreement gate')
    need(worst_rho<=L['density_deviation_max'] and worst_mach<L['Mach_strict'], 'density or Mach gate')
    need(section[-1]<=L['section_relative_max'], 'final section mismatch')
    need(Re<=LIMITS['new_physics_guards']['Re_H_max'], 'Reynolds guard')
    need(main[-1]>0, 'nonpositive final flux')
    K=p['nu']*main[-1]/p['a'];resistance=1000*p['a']/main[-1]
    for value,key,tol in [(K,'Keff_m3',0),(main[-1],'J_main_m2_s',0),
        (resistance,'R_eff_Pa_s_per_m3',0),(worst_mass,'max_mass_abs_relative',1e-16),
        (float(np.abs(legacy).max()),'legacy_max_mass_abs_relative',1e-16),
        (float(np.abs(delta).max()),'max_delta_mass_abs_relative',1e-16),
        (worst_ledger,'max_mass_ledger_agreement',1e-16),(worst_rho,'max_density_deviation',1e-16),
        (worst_mach,'max_Mach',1e-16),(std[-1],'window_main_rel_std',1e-12),
        (span[-1],'window_main_rel_span',1e-12),(crossmax[-1],'window_cross_abs_max',1e-28),
        (section[-1],'section_relative_difference',1e-15)]:
        need(close(value,float(result[key]),rtol=1e-6,atol=tol), 'summary disagreement '+key)
    need(result['legacy_mass_gate_PASS']==str(float(np.abs(legacy).max())<1e-10).lower(), 'legacy mass flag erased')
    need(close([float(v) for v in result['J_vector_m2_s'].split(',')],
               [data['J'+k][-1] for k in 'xyz'],rtol=1e-12,atol=1e-30), 'final vector flux')
    return dict(K_m3=float(K),J_main_m2_s=float(main[-1]),diagnostic_rows=N,
        all_full_windows_recomputed=len(std),first_accepted_window_is_final=True,
        corrected_mass_max=worst_mass,legacy_mass_max=float(np.abs(legacy).max()),
        ledger_agreement_max=worst_ledger,final_span=float(span[-1]),Re_H=Re)

def check_slice(run, config, K):
    p=exact_parameters(config);rec=rows(run/'field_slice.csv')
    need(rec, 'missing double precision field slice')
    data={k:np.array([float(r[k]) for r in rec]) for k in rec[0]}
    need(all(np.isfinite(v).all() for v in data.values()), 'nonfinite slice')
    need(len(rec)*p['ny']==p['nodes'], 'slice fluid count')
    x,z=data['x'],data['z']
    ix=np.rint(x/p['dx']-.5).astype(int);iz=np.rint(z/p['dx']-.5).astype(int)
    need(close(x,(ix+.5)*p['dx']) and close(z,(iz+.5)*p['dx']), 'slice lattice coordinates')
    need(len(set(zip(ix,iz)))==len(rec), 'duplicated slice nodes')
    groove=(x>=(p['P']-p['w'])/2)&(x<(p['P']+p['w'])/2)
    need(np.all((ix>=0)&(ix<p['nx'])&(z>=0)&(z<p['h']+p['d']*groove)) and np.all(data['material']==1), 'slice solid or overlap')
    velocity=data['uy'] if config['direction']=='P' else data['ux']
    Ks=p['nu']*float(velocity.sum())*p['dx']**2/(p['P']*p['a'])
    need(close(Ks,K,rtol=2e-8), 'slice and volume-integral flux disagreement')
    smooth=None
    if p['d']==0:
        exact=p['a']*z*(p['h']-z)/(2*p['nu'])
        L2=float(np.linalg.norm(velocity-exact)/np.linalg.norm(exact))
        err=abs(K/(p['h']**3/12)-1)
        need(err<LIMITS['smooth']['K_relative_strict'] and L2<LIMITS['smooth']['profile_L2_relative_strict'], 'smooth analytic validation')
        smooth=dict(K_relative_error=err,profile_L2_relative=L2)
    return smooth

def compare_legacy(run,baseline):
    old=rows(baseline/'diagnostics.csv');new=rows(run/'diagnostics.csv')
    common=sorted(set(old[0])&set(new[0]));report={}
    aligned=min(len(old),len(new))
    for key in common:
        a=np.array([float(r[key]) for r in old[:aligned]])
        b=np.array([float(r[key]) for r in new[:aligned]])
        report[key]=dict(exact=bool(np.array_equal(a,b)),max_absolute_difference=float(np.max(np.abs(a-b))))
    # No post hoc difference tolerance. Any difference is HOLD pending explicit review.
    exact=len(old)==len(new) and all(r['exact'] for r in report.values())
    return dict(all_common_columns=report,old_rows=len(old),new_rows=len(new),
                common_rows_compared=aligned,all_exact=exact,
                unexplained_differences_stop=not exact)

def binding(release, expected_sha):
    need(sha(release)==expected_sha, 'execution release trust anchor mismatch')
    bound=json.loads(Path(release).read_text())
    need(bound['protocol_id']=='URV-v1', 'wrong protocol')
    need(bound['simulation_authorized'] is True and bound['preparation_only_build'] is False,
         'current package authorizes zero-step preparation only')
    need(bound['author_external_data_history_confirmation']=='CONFIRMED', 'external data history pending')
    for path,digest in bound['inputs_sha256'].items(): need(sha(path)==digest, 'execution source/input changed: '+path)
    for path in [*CASE.joinpath('analysis').glob('*.py'),*CASE.joinpath('common').glob('*')]:
        if path.is_file(): need(str(path) in bound['inputs_sha256'], 'unbound checker/protocol '+str(path))
    return bound

def check_run(run, release, expected_sha, output):
    run=Path(run).resolve();output=Path(output).resolve()
    need(not output.is_relative_to(run), 'analysis must be outside original run')
    bound=binding(release,expected_sha)
    completion=json.loads((run/'completion.json').read_text())
    need(completion['release_sha256']==expected_sha and completion['independent_process_exit_code']==0, 'missing/mismatched independent exit')
    need(completion['inputs_unchanged'] is True, 'run input drift')
    need(completion['inputs_after_sha256']==bound['inputs_sha256'], 'post-run input binding incomplete')
    required={'run_config.txt','run_manifest.txt','run.log','exit_code.txt','result.txt','result_summary.csv',
        'effective_config.txt','boundary_audit.txt','diagnostics.csv','field_slice.csv',
        'frame_index.csv','frame_schedule.csv','execution_audit.txt'}
    hashes=completion['output_sha256']
    need(required<=set(hashes), 'incomplete output manifest')
    need(all((run/f).resolve().is_relative_to(run) for f in hashes), 'output path escape')
    for file,digest in hashes.items(): need(sha(run/file)==digest,'raw output hash mismatch '+file)
    need((run/'exit_code.txt').read_text().strip()=='0' and (run/'run.log').stat().st_size>0, 'process did not complete normally')
    cfg=kv(run/'run_config.txt');r=kv(run/'result.txt');effective=kv(run/'effective_config.txt');manifest=kv(run/'run_manifest.txt')
    ident=completion['planned_case_id'];matrix=rows(CASE/'common/case_matrix.csv')
    matches=[row for row in matrix if row['planned_case_id']==ident]
    need(len(matches)==1, 'case not in adopted matrix');row=matches[0]
    need(cfg['mode']==manifest['mode']=='steady' and r['formal_simulation']=='true', 'zero-step cannot pass completed-result acceptance')
    need(cfg['run_id']==r['run_id']==effective['run_id']==manifest['run_id']==completion['run_id'], 'run identity mismatch')
    need(completion['run_id'] in bound['approved_run_ids'], 'run not individually approved')
    need(cfg['direction']==row['direction'], 'direction not approved')
    for key,mkey in [('h_nm','h_nm'),('d_nm','d_nm'),('w_nm','w_nm'),('period_nm','P_nm'),('Ly_nm','Ly_nm'),('dx_nm','dx_nm'),('nu_m2_s','nu_m2_s'),('acceleration_m_s2','acceleration_m_s2')]:
        need(float(cfg[key])==float(row[mkey]), 'config not approved: '+key)
    protocol=json.loads((CASE/'common/protocol.json').read_text())
    need(float(cfg['window_tstar'])==.75 and float(cfg['max_time_H_diffusion'])==8, 'observation time changed')
    need([float(v) for v in cfg['frame_tstar'].split(',')]==protocol['time']['frame_tstar'], 'frame plan changed')
    for key in ['converged','material_unchanged','finite','all_measurements_finite','geometry_PASS','PASS']:
        need(r[key]=='true','native flag failed '+key)
    need(r['NUMERICAL_GATE']=='PASS' and r['RESULT_PASS']=='false', 'native/independent status confusion')
    need(r['exit_code']=='0', 'native nonzero exit')
    need(r['direction']==('parallel' if cfg['direction']=='P' else 'perpendicular'), 'native direction mapping')
    need(r['mass_gate_statistic']=='Neumaier_physical_mass', 'wrong mass statistic')
    need(r['descriptor']=='D3Q19_FORCE' and r['collision']=='ForcedBGK' and r['periodicity']=='x_y', 'physical kernel changed')
    need(r['wall_boundary']=='Bouzidi_zero_velocity_exact_EX240', 'wall model changed')
    p=exact_parameters(cfg)
    force=[0.,0.,0.];force[1 if cfg['direction']=='P' else 0]=p['a']*p['dt']**2/p['dx']
    need(close([float(v) for v in r['force_lattice'].split(',')],force,rtol=1e-12), 'force conversion/direction')
    for key,value in [('rho_phys_kg_m3',1000),('nu_phys_m2_s',p['nu']),('mu_phys_Pa_s',.001),
        ('tau',1),('Lx_m',p['P']),('Ly_m',p['Ly']),('mesa_gap_m',p['h']),
        ('groove_depth_m',p['d']),('groove_width_m',p['w']),('H_ref_m',p['H']),
        ('dt_s',p['dt']),('dx_m',p['dx']),('acceleration_m_s2',p['a'])]:
        need(close(float(r[key]),value), 'result units or parameters '+key)
    for key,value in [('window_steps',p['window']),('maximum_steps',p['cap'])]:
        need(int(r[key])==int(effective[key])==value, 'native exact-step arithmetic '+key)
    actual=kv(run/'execution_audit.txt')
    need(actual['preparation_only_build']=='0' and int(actual['collide_and_stream_calls'])==int(r['steps_completed']), 'time-stepping provenance')
    geo=check_boundary(cfg,kv(run/'boundary_audit.txt'))
    need(int(r['candidate_links'])==int(r['installed_links'])==geo['candidate_links'], 'result link count')
    need(int(r['fallback_count'])==int(r['unresolved_links'])==0, 'result fallback')
    need(abs(float(r['q_min'])-.5)<=1e-10 and abs(float(r['q_max'])-.5)<=1e-10, 'result wall distance')
    need(int(r['fluid_nodes'])==p['nodes'], 'result fluid count')
    need(close(float(r['fluid_volume_m3']),p['P']*p['Ly']*p['H'],rtol=1e-10), 'result volume')
    raw=rows(run/'diagnostics.csv');data={key:np.array([float(row[key]) for row in raw]) for key in raw[0]}
    scalar=diagnostics(cfg,r,data);smooth=check_slice(run,cfg,scalar['K_m3'])
    summary=rows(run/'result_summary.csv');need(len(summary)==1,'summary row count')
    need(close(float(summary[0]['Keff']),scalar['K_m3']), 'CSV summary K')
    regression=None
    if row['family']=='H75':
        reference=bound['h75_regression_references'][cfg['direction']]
        baseline=Path(reference['directory']);need(sha(baseline/'result.txt')==reference['result_sha256'], 'regression reference binding')
        need(sha(baseline/'diagnostics.csv')==reference['diagnostics_sha256'], 'regression diagnostics binding')
        err=abs(scalar['K_m3']/float(kv(baseline/'result.txt')['Keff_m3'])-1)
        legacy=compare_legacy(run,baseline)
        need(err<=LIMITS['statistics_port_regression']['K_relative_max'], 'h75 K port regression')
        need(legacy['all_exact'], 'legacy trajectory difference needs separate explanation; fail-stop')
        regression=dict(relative_K_change=err,legacy=legacy)
    frames=rows(run/'frame_index.csv');schedule=rows(run/'frame_schedule.csv')
    steps=int(r['steps_completed']);expected={0,steps};frame_steps=[int(f['step']) for f in frames]
    need(len(schedule)==len(protocol['time']['frame_tstar']), 'incomplete frame schedule')
    for request,item in zip(protocol['time']['frame_tstar'],schedule):
        from fractions import Fraction
        target=math.ceil(Fraction(str(request))*6*(Fraction(cfg['h_nm'])/Fraction(cfg['dx_nm']))**2)
        need(float(item['requested_tstar'])==request and int(item['target_step'])==target and int(item['reached'])==int(target<=steps), 'requested/saved frame schedule')
        if target<=steps: expected.add(target)
    need(frame_steps==sorted(expected) and len(frames)==int(r['frames_written']), 'missing, future, or duplicate frame')
    for f in frames:
        need(close(float(f['time_s']),int(f['step'])*p['dt'],atol=1e-24) and close(float(f['tstar']),p['nu']*int(f['step'])*p['dt']/p['h']**2,atol=1e-14), 'frame time units')
    output.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ,QT_QPA_PLATFORM='offscreen',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    with (output/'field_reader.log').open('w') as log:
        proc=subprocess.run(['/usr/bin/pvpython','--force-offscreen-rendering','-B',str(CASE/'analysis/read_fields.py'),
            '--run',str(run),'--out',str(output/'fields.json')],stdout=log,stderr=subprocess.STDOUT,env=env,timeout=3600)
    need(proc.returncode==0,'independent full-field reader failed')
    fields=json.loads((output/'fields.json').read_text());need(fields['PASS'],'field evidence failed')
    for path,digest in fields['payload_sha256'].items():
        need(hashes.get(str(Path(path).relative_to(run)))==digest,'VTK payload absent from completion binding')
    need(all(sha(run/f)==s for f,s in hashes.items()), 'output changed during analysis')
    binding(release,expected_sha)
    accepted=dict(protocol_id='URV-v1',planned_case_id=ident,run_id=cfg['run_id'],family=row['family'],stage=row['stage'],
        direction=cfg['direction'],dx_nm=float(cfg['dx_nm']),acceleration_m_s2=p['a'],
        NUMERICAL_GATE='PASS',geometry_PASS=True,RESULT_PASS=True,
        REFERENCE_QUALIFIED_FOR_CASE=False,MODEL_COMPARISON='NOT_EVALUATED',physical_validation='NOT_EVALUATED',
        scalar=scalar,smooth=smooth,regression=regression,geometry=geo,release_sha256=expected_sha,
        completion_sha256=sha(run/'completion.json'),independent_exit_code=0)
    save(output/'acceptance.json',accepted)
    return accepted

def aggregate(accepted):
    """Only called by CLI on fresh check_run returns, never trusted input receipts."""
    need(len(accepted)==24 and len({r['planned_case_id'] for r in accepted})==24,'all 24 cases required')
    need(all(r['RESULT_PASS'] is True for r in accepted),'per-run acceptance incomplete')
    predictions=rows(CASE/'common/model_predictions_before_reference.csv');out=[]
    for family in ['U_REG','U_THIN']:
        for direction in ['P','T']:
            select=[r for r in accepted if r['family']==family and r['direction']==direction]
            grid=sorted([r for r in select if r['stage'].endswith('_GRID')],key=lambda r:-r['dx_nm'])
            need([r['dx_nm'] for r in grid]==[5,2.5,1.25], 'reference grid completeness')
            forces=sorted([r for r in select if r['dx_nm']==2.5],key=lambda r:r['acceleration_m_s2'])
            need([r['acceleration_m_s2'] for r in forces]==[5e4,1e5,2e5], 'linearity controls incomplete')
            forceK=np.array([r['scalar']['K_m3'] for r in forces]);linearity=float(np.ptp(forceK)/forceK.mean())
            estimate=grid_estimate(*[r['scalar']['K_m3'] for r in grid],grid[-1]['scalar']['final_span'])
            qualified=estimate['REFERENCE_QUALIFIED_FOR_CASE'] and linearity<=.001
            pred=next(r for r in predictions if r['family']==family and r['direction']==direction)
            comparison=sensitivity(float(pred['K_original_m3']),float(pred['K_V2_m3']),grid[-1]['scalar']['K_m3'],estimate['u']) if qualified else dict(MODEL_COMPARISON='NOT_EVALUATED')
            out.append(dict(family=family,direction=direction,REFERENCE_QUALIFIED_FOR_CASE=qualified,
                grid=estimate,linearity_K_span_over_mean=linearity,comparison=comparison))
    return dict(protocol_id='URV-v1',conditions=out,
        primary_practical_support=all(r['REFERENCE_QUALIFIED_FOR_CASE'] and r['comparison'].get('practical_improvement',False) for r in out if r['family']=='U_REG'),
        strict_error_bound_established=False,physical_validation='NOT_EVALUATED',submission_ready=False)

def main():
    ap=argparse.ArgumentParser();group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--run',type=Path);group.add_argument('--batch-index',type=Path)
    ap.add_argument('--release',type=Path,required=True);ap.add_argument('--release-sha256',required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    try:
        if args.run:
            check_run(args.run,args.release,args.release_sha256,args.out)
        else:
            index=json.loads(args.batch_index.read_text());need(len(index)==24, '24 raw run paths required')
            need(len(set(index))==24, 'duplicate raw run path')
            records=[check_run(Path(p),args.release,args.release_sha256,args.out/f'case_{i:02d}') for i,p in enumerate(index)]
            save(args.out/'comparison.json',aggregate(records))
    except Exception as error:
        # Keep failure evidence outside all raw results. Never write success on failure.
        failure=args.out/'failure.json'
        if not failure.exists(): save(failure,dict(RESULT_PASS=False,NUMERICAL_GATE='NOT_EVALUATED',
            error=type(error).__name__+': '+str(error),independent_exit_code=2,solver_executed=False))
        print(type(error).__name__+': '+str(error),file=sys.stderr);return 2
    return 0

if __name__=='__main__': raise SystemExit(main())
