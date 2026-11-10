"""Frozen alpha contracts; independent NumPy fields and full-population references."""
import json
import math
import numpy as np
from numerical_reference import C,W,load_field,lap,grad,amplitude,sequence,rate,matrix

def require(ok,message):
    if not ok:raise ValueError(message)

def rows(path):
    import csv
    with path.open() as f:out=list(csv.DictReader(f))
    require(bool(out),'empty CSV')
    require(all(np.isfinite(float(v)) for r in out for v in r.values()),'nonfinite/missing CSV')
    return out

def drift(values):
    x=np.array(values,dtype=np.longdouble);d=(x-x[0])/x[0];i=int(np.argmax(abs(d)))
    return dict(max_abs=float(abs(d[i])),step=i,final=float(d[-1]))

def analyze_case(case,path,thresholds,initialization=False):
    cfg=json.loads((path/'config.json').read_text());res=json.loads((path/'result.json').read_text())
    n=case['N'];steps=0 if initialization else case['steps'];source=case['kind']=='source'
    require(cfg['case_id']==case['id'] and cfg['N']==n and cfg['steps']==steps and cfg['nominal_steps']==case['steps'],'configuration ID/grid/length mismatch')
    require(cfg['MPI_ranks']==1 and cfg['mode']==list(case['mode']),'rank/mode mismatch')
    require(cfg['fixture']==('compressible' if source else '') and cfg['nonlinear']==(case['kind']!='linear'),'wrong model/fixture')
    for key in ('alpha','tau','sigma','width','center','amplitude','a','kappa'):
        require(math.isclose(cfg[key],case[key],rel_tol=1e-14,abs_tol=1e-30),'parameter mismatch '+key)
    require(res['requested_steps']==steps and res['completed_steps']==steps,'incomplete steps')
    initial=load_field(path/'initial.csv',n,source)
    if source:return analyze_source(case,path,initial,res,initialization)
    history=rows(path/'history.csv');require(len(history)==steps+1,'history length mismatch')
    require([int(r['step']) for r in history]==list(range(steps+1)),'missing/reordered steps')
    require(all(int(r['nodes'])==n**3 and int(r['finite'])==1 for r in history),'bad nodes/finite flag')
    require(res['safe'],'unsafe result')
    end=load_field(path/'final.csv',n)
    d=drift([r['phase_sum'] for r in history]);checks={'phase_amount':d['max_abs']<=thresholds['phase_relative_drift']}
    q0=np.longdouble(history[0]['phase_sum'])
    for r in history:
        require(abs((np.longdouble(r['phase_sum'])-q0)/q0-np.longdouble(r['relative_drift']))<1e-14,'reported all-step drift mismatch')
    for f,t in ((initial,0),(end,steps)):
        require(max(np.max(abs(f[a])) for a in ('source','source_old','ux','uy','uz'))==0,'unforced CH has source or velocity')
        require(abs(np.sum(f['phi'],dtype=np.longdouble)-np.longdouble(history[t]['phase_sum']))/n**3<1e-13,'field/history Q mismatch')
        require(abs(amplitude(f['phi'],case)-complex(float(history[t]['mode_re']),float(history[t]['mode_im'])))<1e-13,'field/history Fourier mismatch')
    metrics=dict(id=case['id'],phase_drift=d,initialization_only=initialization,steps=steps)
    if case['kind']=='linear':
        modes=rows(path/'initial_population_modes.csv');require([int(r['population']) for r in modes]==list(range(19)),'missing population modes')
        actual_modes=np.array([complex(float(r['re']),float(r['im'])) for r in modes]);ref=sequence(case,actual_modes)[:steps+1];ideal=sequence(case)[:steps+1]
        require(abs(actual_modes.sum()-amplitude(initial['phi'],case))<1e-13,'population/phase initial mode mismatch')
        measured=np.array([complex(float(r['mode_re']),float(r['mode_im'])) for r in history])
        error=float(np.max(abs(measured-ref))/case['amplitude'])
        l2max=max(float(r['reference_L2_over_initial_RMS']) for r in history)
        checks.update(complex_mode=error<=thresholds['mode_over_initial_amplitude'],all_step_observed_L2=l2max<=thresholds['field_L2_over_initial_RMS'])
        xyz=np.indices((n,)*3);theta=2*np.pi*sum(v*m for v,m in zip(xyz,case['mode']))/n
        endpoints=[]
        for field,t in ((initial,0),(end,steps)):
            exact=case['center']+2*np.real(ideal[t]*np.exp(1j*theta));l2=float(np.sqrt(np.mean((field['phi']-exact)**2))/(case['amplitude']/np.sqrt(2)))
            require(abs(l2-float(history[t]['reference_L2_over_initial_RMS']))<1e-9,'endpoint L2 mismatch')
            endpoints.append(l2)
        checks['endpoint_3D_L2']=max(endpoints)<=thresholds['field_L2_over_initial_RMS']
        metrics.update(mode_error_over_A=error,all_step_observed_L2=l2max,endpoint_3D_L2=endpoints)
        if steps:
            fit=rate(measured);fit_ref=rate(ref);_,_,k,_=matrix(case)
            ce=case['alpha']*(case['tau']-.5)/3*(k@k)*(case['a']+case['kappa']*(k@k))
            er=abs(fit/ce-1);limit=thresholds['continuous_rate_error_coarse' if n==16 else 'continuous_rate_error_fine']
            checks['discrete_fit']=abs(fit/fit_ref-1)<=thresholds['rate_relative_to_discrete']
            checks['continuous_rate']=er<=limit
            metrics.update(rate=fit,reference_rate=fit_ref,rate_ratio=fit/fit_ref,continuum_relative_error=float(er))
    else:
        old=None;muerr=0.;steperr=0.;balance=0.;M=case['alpha']/6
        for t,row in enumerate(history):
            f=load_field(path/f'field_step_{t}.csv',n);p=f['phi'];mu=f['mu']
            require(abs(np.sum(p,dtype=np.longdouble)-np.longdouble(row['phase_sum']))/n**3<1e-13,'nonlinear all-step Q/field mismatch')
            muerr=max(muerr,float(np.max(abs(mu-(4*case['beta']*p*(p-1)*(p-.5)-case['kappa']*lap(p))))))
            energy=np.sum(case['beta']*p*p*(p-1)**2-case['kappa']/2*p*lap(p),dtype=np.longdouble)
            diss=-M*np.sum(mu*lap(mu),dtype=np.longdouble)
            require(abs(energy-np.longdouble(row['free_energy']))/n**3<1e-12,'free energy mismatch')
            require(abs(diss-np.longdouble(row['link_dissipation']))/n**3<1e-12,'dissipation mismatch')
            if old is not None:steperr=max(steperr,float(np.max(abs(p-old['phi']-M*lap(old['mu'])))))
            balance=max(balance,abs(float(row['energy_balance_residual']))/n**3);old=f
        checks.update(actual_mu=muerr<=1e-12,full_field_step=steperr<=1e-12,energy_identity=balance<=1e-12)
        metrics.update(mu_error=muerr,step_error=steperr,energy_residual_per_node=balance)
    checks['reported_point_update']=max(float(r['one_step_max_error']) for r in history)<=1e-12
    metrics.update(checks=checks,operator_contract_pass=None if initialization else all(checks.values()))
    return metrics

def analyze_source(case,path,before,result,initialization):
    n=case['N'];alpha=case['alpha'];u=np.array([before[a] for a in ('ux','uy','uz')]);phi=before['phi'];mu=before['mu']
    require(np.max(abs(u-.01*grad(phi)))<1e-12,'source velocity mismatch')
    require(np.max(abs(before['source']-np.sum(u*grad(phi),axis=0)))<1e-12,'source mismatch')
    require(np.max(abs(before['source']-before['source_old']))<1e-12,'source startup mismatch')
    require(np.max(abs(mu-(4*case['beta']*phi*(phi-1)*(phi-.5)-case['kappa']*lap(phi))))<1e-12,'source constitutive mismatch')
    if initialization:return dict(id=case['id'],initialization_only=True,operator_contract_pass=None)
    post=load_field(path/'post_collision.csv',n,True);stream=load_field(path/'post_stream.csv',n,True);refresh=load_field(path/'post_refresh.csv',n,True)
    b=W*(-2.5+1.5*np.sum(C*C,axis=1));collision=0.;migration=0.;source=np.zeros_like(phi)
    for i,(c,w) in enumerate(zip(C,W)):
        expect=(phi-(1-w)*alpha*mu if i==0 else w*alpha*mu)-w+b[i]*before['source']
        collision=max(collision,float(np.max(abs(post[f'f{i}']-expect))))
        migration=max(migration,float(np.max(abs(stream[f'f{i}']-np.roll(post[f'f{i}'],tuple(c),axis=(0,1,2))))))
        source+=b[i]*np.roll(before['source'],tuple(c),axis=(0,1,2))
    point=float(np.max(abs(stream['phi']-phi-alpha/6*lap(mu)-source)))
    budget=float(abs(np.sum(stream['phi']-phi,dtype=np.longdouble)+np.sum(before['source'],dtype=np.longdouble))/n**3)
    checks=dict(collision=collision<=1e-12,migration=migration<=1e-12,point=point<=1e-12,budget=budget<=1e-12,
                refresh_preserves_phi=np.max(abs(refresh['phi']-stream['phi']))<=1e-12)
    require(result['acceptance_evaluated'],'source result did not evaluate step')
    return dict(id=case['id'],initialization_only=False,checks={k:bool(v) for k,v in checks.items()},
                operator_contract_pass=all(checks.values()),collision_error=collision,migration_error=migration,point_error=point,budget_per_node=budget)

def matrix_checks(results,thresholds):
    checks=[]
    for n,alpha in ((16,1),(32,4)):
        ratios=[next(r for r in results if r['id']==f'linear_n{n}_{a}_a{alpha}')['rate_ratio'] for a in ('x','y','z')]
        checks.append(dict(name=f'axes_n{n}',passed=max(ratios)-min(ratios)<=thresholds['axis_normalized_rate_spread'],spread=max(ratios)-min(ratios)))
    for direction in ('x','y','z','xy','xyz'):
        errors=[next(r for r in results if r['id']==f'linear_n{n}_{direction}_a{alpha}')['continuum_relative_error'] for n,alpha in ((16,1),(32,4))]
        checks.append(dict(name='refinement_'+direction,passed=errors[1]<errors[0],errors=errors))
    return checks
