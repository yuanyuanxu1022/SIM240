#!/usr/bin/env python3
"""Analyze only existing completed A2+B data using frozen independent references."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from reference import C,W,load_field,lap,grad,amplitude,sequence,rate,matrix
from run_suite import BASE,PROTOCOL,BATCH,entries
TH=PROTOCOL['thresholds']
def require(ok,message):
    if not ok:raise ValueError(message)
def records(path):
    with Path(path).open() as f:rows=list(csv.DictReader(f))
    require(bool(rows),'empty CSV')
    for r in rows:
        require(all(np.isfinite(float(v)) for v in r.values()),'nonfinite or missing CSV value')
    return rows
def check_history(rows,steps,n):
    require(len(rows)==steps+1,'history row count mismatch')
    require([int(r['step']) for r in rows]==list(range(steps+1)),'missing/reordered/duplicate step')
    require(all(int(r['nodes'])==n**3 and int(r['finite'])==1 for r in rows),'node count or finite flag mismatch')
def drift_summary(values):
    v=np.asarray(values,dtype=np.longdouble);d=(v-v[0])/v[0];idx=int(np.argmax(abs(d)))
    return dict(max_abs=float(abs(d[idx])),step=idx,signed_at_max=float(d[idx]),final=float(d[-1]))
def configuration(case,path,steps):
    cfg=json.loads((path/'config.json').read_text());result=json.loads((path/'result.json').read_text())
    require(cfg['case_id']==case['id'] and cfg['N']==case['N'] and cfg['steps']==steps and cfg['nominal_steps']==case['steps'],'config ID/grid/steps mismatch')
    require(cfg['mode']==case['mode'] and cfg['MPI_ranks']==1,'mode/rank mismatch')
    require(cfg['nonlinear']==(case['kind']=='nonlinear') and cfg['fixture']=='','model mismatch')
    for key in ['tau','center','amplitude','kappa']:require(abs(cfg[key]-case[key])<1e-15,f'{key} mismatch')
    require(abs(cfg['a']-case.get('a',0))<1e-15,'a mismatch')
    require(result['requested_steps']==steps and result['completed_steps']==steps and result['safe'],'incomplete/unsafe result')
    return cfg,result
def analyze_b(case,path,initialization=False):
    steps=0 if initialization else case['steps'];n=case['N'];configuration(case,path,steps)
    rows=records(path/'history.csv');check_history(rows,steps,n)
    d=drift_summary([r['phase_sum'] for r in rows]);checks={'phase_amount':d['max_abs']<=TH['max_abs_relative_phase_drift']}
    for i,r in enumerate(rows):require(abs(float(r['relative_drift'])-float((np.longdouble(r['phase_sum'])-np.longdouble(rows[0]['phase_sum']))/np.longdouble(rows[0]['phase_sum'])))<1e-14,'reported drift mismatch')
    fields=[load_field(path/name,n) for name in ['initial.csv','final.csv']]
    initial,final=fields
    for f,idx in [(initial,0),(final,steps)]:
        require(np.max(abs(f['source']))==0 and np.max(abs(f['source_old']))==0,'B has a nonzero source')
        require(all(np.max(abs(f[a]))==0 for a in ['ux','uy','uz']),'B has nonzero velocity')
        require(abs(float(np.sum(f['phi'],dtype=np.longdouble))-float(rows[idx]['phase_sum']))/n**3<1e-13,'field sum/history mismatch')
        require(abs(amplitude(f['phi'],case)-complex(float(rows[idx]['mode_re']),float(rows[idx]['mode_im'])))<1e-13,'field FFT/history mismatch')
    metrics=dict(id=case['id'],steps=steps,drift=d)
    if case['kind']=='linear':
        mode_rows=records(path/'initial_population_modes.csv');require([int(r['population']) for r in mode_rows]==list(range(19)),'initial population modes incomplete')
        pop=np.array([complex(float(r['re']),float(r['im'])) for r in mode_rows])
        require(abs(pop.sum()-amplitude(initial['phi'],case))<1e-13,'initial populations do not recover phase Fourier mode')
        seq=sequence(case,pop)[:steps+1];ideal=sequence(case)[:steps+1]
        actual=np.array([complex(float(r['mode_re']),float(r['mode_im'])) for r in rows]);err=float(max(abs(seq-actual))/case['amplitude'])
        require(np.max(abs(ideal-seq))/case['amplitude']<TH['linear_complex_coefficient_over_initial_amplitude'],'ideal and actual initialization references disagree')
        l2max=max(float(r['reference_L2_over_initial_RMS']) for r in rows)
        checks.update(complex_mode=err<=TH['linear_complex_coefficient_over_initial_amplitude'],all_step_field_L2=l2max<=TH['linear_fluctuation_L2_over_initial_RMS'])
        # Full 3D endpoint checks avoid subtracting nearly equal Parseval scalars.
        indices=np.indices((n,)*3);theta=2*np.pi*sum(a*m for a,m in zip(indices,case['mode']))/n
        endpoint_errors=[]
        for field,t in [(initial,0),(final,steps)]:
            ref=case['center']+2*np.real(ideal[t]*np.exp(1j*theta))
            error=float(np.sqrt(np.mean((field['phi']-ref)**2))/(case['amplitude']/np.sqrt(2)));endpoint_errors.append(error)
            require(abs(error-float(rows[t]['reference_L2_over_initial_RMS']))<1e-9,'endpoint field L2/history mismatch')
            checks[f'field_L2_step{t}']=error<=TH['linear_fluctuation_L2_over_initial_RMS']
        metrics.update(max_mode_error_over_A=err,max_reported_field_L2=l2max,endpoint_field_L2=endpoint_errors)
        if steps:
            actual_rate=rate(actual);ref_rate=rate(seq);rate_error=abs(actual_rate/ref_rate-1)
            checks['rate_reference']=rate_error<=TH['measured_fitted_rate_over_discrete_reference']
            mat,e,k,lam=matrix(case);continuum=(case['tau']-.5)/3*float(k@k)*(case['a']+case['kappa']*float(k@k))
            continuum_error=abs(actual_rate/continuum-1)
            if case['tau']==1:checks['continuum_rate']=continuum_error<=TH[f'linear_tau1_continuum_rate_N{n}']
            metrics.update(measured_rate=actual_rate,reference_rate=ref_rate,rate_ratio=actual_rate/ref_rate,continuum_rate=continuum,continuum_relative_error=continuum_error)
    else:
        old=None;muerr=0.;steperr=0.;energyerr=0.
        beta=case['beta'];kap=case['kappa']
        for step,row in enumerate(rows):
            f=load_field(path/f'field_step_{step}.csv',n);p=f['phi'];mu=f['mu'];expected=4*beta*p*(p-1)*(p-.5)-kap*lap(p)
            muerr=max(muerr,float(np.max(abs(mu-expected))))
            require(abs(amplitude(p,case)-complex(float(row['mode_re']),float(row['mode_im'])))<1e-13,'nonlinear full field FFT mismatch')
            for harmonic in [2,3]:require(abs(amplitude(p,case,harmonic).real-float(row[f'harmonic{harmonic}_re']))<1e-13,'nonlinear harmonic mismatch')
            energy=float(np.sum(beta*p*p*(p-1)**2-kap/2*p*lap(p),dtype=np.longdouble))
            diss=float(-np.sum(mu*lap(mu),dtype=np.longdouble)/6)
            require(abs(energy-float(row['free_energy']))/n**3<1e-12,'energy definition mismatch')
            require(abs(diss-float(row['link_dissipation']))/n**3<1e-12,'link dissipation mismatch')
            require(abs(float(np.sum(p,dtype=np.longdouble))-float(row['phase_sum']))/n**3<1e-13,'nonlinear intermediate sum mismatch')
            if old is not None:steperr=max(steperr,float(np.max(abs(p-old['phi']-lap(old['mu'])/6))))
            energyerr=max(energyerr,abs(float(row['energy_balance_residual']))/n**3)
            old=f
        checks.update(actual_mu=muerr<=TH['mu_absolute'],local_update=steperr<=TH['nonlinear_step_absolute'],energy_identity=energyerr<=1e-12)
        metrics.update(max_mu_error=muerr,max_local_update_error=steperr,max_energy_identity_per_node=energyerr)
    if case['tau']==1:
        checks['solver_local_update']=max(float(r['one_step_max_error']) for r in rows)<=TH['nonlinear_step_absolute']
    metrics.update(checks=checks,contract_pass=all(checks.values()),initialization_only=initialization)
    return metrics
def analyze_a2(name,path,initialization=False):
    n=PROTOCOL['A2_N'];cfg=json.loads((path/'config.json').read_text());res=json.loads((path/'result.json').read_text())
    require(cfg['fixture']==name and cfg['N']==n and cfg['tau']==1 and cfg['MPI_ranks']==1,'A2 config mismatch')
    require(cfg['steps']==(0 if initialization else 1) and res['completed_steps']==cfg['steps'],'A2 step mismatch')
    before=load_field(path/'initial.csv',n,True)
    xyz=np.indices((n,)*3)*2*np.pi/n;x,y,z=xyz
    phi_expected=.35+.08*np.cos(x+.31)+.04*np.sin(y+.2)+.02*np.cos(x+y+.7)
    require(np.max(abs(before['phi']-phi_expected))<=1e-12,'A2 initial phase mismatch')
    psi=.01*(np.sin(x+.2)*np.sin(y+.6)+.17*np.cos(y+z+.5))
    gp=grad(psi);u_expected=np.zeros((3,n,n,n))
    if name=='solenoidal':u_expected=np.array([gp[1],-gp[0],np.zeros_like(x)])
    if name=='compressible':u_expected=.01*grad(before['phi'])
    require(np.max(abs(u_expected-np.array([before[a] for a in ['ux','uy','uz']])))<=1e-12,'A2 prescribed velocity mismatch')
    source_expected=np.sum(u_expected*grad(before['phi']),axis=0)
    require(np.max(abs(source_expected-before['source']))<=1e-12 and np.max(abs(before['source_old']-before['source']))<=1e-12,'A2 source/bootstrap mismatch')
    if name=='constant_mu':require(np.max(abs(before['mu']-.003))<=1e-12,'constant mu mismatch')
    if name=='specified_mu':require(np.max(abs(before['mu']-(.002*np.sin(x+.3)+.001*np.cos(y+z))))<=1e-12,'specified mu mismatch')
    for f in [before]:require(np.max(abs(1+sum(f['f'+str(i)] for i in range(19))-f['phi']))<=1e-12,'A2 populations/phase mismatch')
    if initialization:return dict(id=name,initialization_only=True,nodes=n**3,contract_pass=None)
    collided=load_field(path/'post_collision.csv',n,True);streamed=load_field(path/'post_stream.csv',n,True);after=load_field(path/'post_refresh.csv',n,True)
    for f in [collided,streamed,after]:require(np.max(abs(1+sum(f['f'+str(i)] for i in range(19))-f['phi']))<=1e-12,'A2 populations/phase mismatch')
    point=0.;collerr=0.;streamerr=0.;prediction=np.zeros((n,)*3)
    cc=np.sum(C*C,axis=1);bs=W*(-2.5+1.5*cc)
    for i,(c,w) in enumerate(zip(C,W)):
        expect=(before['phi']-(1-w)*before['mu'] if i==0 else w*before['mu'])-w+bs[i]*before['source']
        collerr=max(collerr,float(np.max(abs(expect-collided['f'+str(i)]))))
        source=np.roll(collided['f'+str(i)],tuple(c),axis=(0,1,2))
        streamerr=max(streamerr,float(np.max(abs(source-streamed['f'+str(i)]))))
        prediction+=bs[i]*np.roll(before['source'],tuple(c),axis=(0,1,2))
    prediction+=before['phi']+lap(before['mu'])/6
    point=float(np.max(abs(streamed['phi']-prediction)))
    change=np.sum(streamed['phi']-before['phi'],dtype=np.longdouble);ss=np.sum(before['source'],dtype=np.longdouble)
    budget=float(abs(change+ss)/n**3)
    u=np.array([before[a] for a in ['ux','uy','uz']]);div=sum(grad(u[a])[a] for a in range(3))
    adjoint=float(abs(ss+np.sum(before['phi']*div,dtype=np.longdouble))/n**3)
    checks=dict(population_collision=collerr<=1e-12,population_streaming=streamerr<=1e-12,point_update=point<=TH['A2_point_update_absolute'],global_budget=budget<=TH['A2_global_budget_per_node'],adjoint=adjoint<=1e-12,refresh_preserves_phi=float(np.max(abs(after['phi']-streamed['phi'])))<=1e-12)
    if name=='constant_mu':checks['stationary']=float(np.max(abs(streamed['phi']-before['phi'])))<=1e-12
    if name in ['solenoidal','compressible']:
        for f in [before,after]:require(np.max(abs(f['mu']-(12*1.4467592592592595e-5*f['phi']*(f['phi']-1)*(f['phi']-.5)-6*1.4467592592592595e-5*lap(f['phi']))))<=1e-12,'A2 actual constitutive mu mismatch')
    require(abs(res['point_update_max_error']-point)<=1e-12,'A2 solver point summary mismatch')
    return dict(id=name,contract_pass=all(checks.values()),checks=checks,point_error=point,collision_error=collerr,stream_error=streamerr,source_sum=float(ss),phase_change=float(change),budget_per_node=budget,divergence_max=float(np.max(abs(div))))
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    require(not args.output.exists(),'analysis output exists; no overwrite')
    evidence=BASE/'evidence'/BATCH;output=BASE/'output'/BATCH;manifest=json.loads((evidence/'manifest.json').read_text())
    require(int((evidence/'exit_code.txt').read_text())==0 and manifest['independent_exit_code']==0 and manifest.get('finished_utc') and manifest['source_hashes_unchanged'],'batch incomplete/failed')
    expected=[(stage,name) for stage,name in entries()]
    require([(e['stage'],e['case_id']) for e in manifest['cases']]==expected,'batch missing/duplicate/reordered cases')
    for p,h in manifest['source_binding']['sha256'].items():require(Path(p).is_file() and hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,'bound input changed: '+p)
    results=[]
    for entry in manifest['cases']:
        run_id=entry['run_id'];sub=evidence/run_id
        require(int((sub/'exit_code.txt').read_text())==0 and entry['independent_exit_code']==0 and entry.get('finished_utc'),'child incomplete/failed')
        if entry['stage']=='a2':r=analyze_a2(entry['case_id'],output/run_id)
        else:r=analyze_b(next(c for c in PROTOCOL['B_cases'] if c['id']==entry['case_id']),output/run_id)
        results.append(r)
    comparisons=[]
    for n in [16,32]:
        axis=[next(r for r in results if r['id']==f'lin_n{n}_{d}_t100')['rate_ratio'] for d in ['x','y','z']]
        comparisons.append(dict(name=f'axis_N{n}',pass_=max(axis)-min(axis)<=TH['axis_symmetry_rate_spread'],spread=max(axis)-min(axis)))
    for d in ['x','y','z','xy','xyz']:
        errors=[next(r for r in results if r['id']==f'lin_n{n}_{d}_t100')['continuum_relative_error'] for n in [16,32]]
        comparisons.append(dict(name='refinement_'+d,pass_=errors[1]<errors[0],errors=errors))
    payload=dict(batch_id=BATCH,all_cases=results,matrix_checks=comparisons,operator_contract_pass=all(r['contract_pass'] for r in results) and all(r['pass_'] for r in comparisons),NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS='NOT_EVALUATED',geometry_PASS='NOT_EVALUATED')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(payload,indent=2)+'\n')
    print('operator_contract_pass=',payload['operator_contract_pass']);return 0 if payload['operator_contract_pass'] else 1
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print('ANALYSIS_FAILED:',repr(exc),file=sys.stderr);sys.exit(2)
