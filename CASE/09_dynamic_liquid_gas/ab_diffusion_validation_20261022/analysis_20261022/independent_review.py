#!/usr/bin/env python3
"""Independent completed-data audit. No imports from frozen solver/reference/analyzer.

Uses actual descriptor, NumPy matrix powers, FFT, full fields and fixed protocol.
Writes only this new analysis directory; never executes/rebuilds OpenLB.
"""
from pathlib import Path
import csv
import datetime as dt
import hashlib
import json
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent;BASE=HERE.parent
P=json.loads((BASE/'protocol.json').read_text());BATCH=P['batch_id'];TH=P['thresholds']
E=BASE/'evidence'/BATCH;O=BASE/'output'/BATCH
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest=json.loads((E/'manifest.json').read_text())
assert int((E/'exit_code.txt').read_text())==0 and manifest['independent_exit_code']==0
assert manifest['finished_utc'] and manifest['source_hashes_unchanged'] and not manifest['source_mismatches']
expected=[('a2',n) for n in P['A2_cases']]+[('b',c['id']) for c in P['B_cases']]
assert [(e['stage'],e['case_id']) for e in manifest['cases']]==expected
assert len(set(e['run_id'] for e in manifest['cases']))==22
protected=dict(manifest['source_binding']['sha256'])
for folder in [E,O]:
    for f in folder.rglob('*'):
        if f.is_file():protected[str(f)]=sha(f)
protected[str(HERE/'frozen_analysis.json')]=sha(HERE/'frozen_analysis.json')
for name,hsh in protected.items():assert Path(name).is_file() and sha(name)==hsh,name
(HERE/'input_hashes.json').write_text(json.dumps(protected,indent=2)+'\n')
src=Path('/home/dell/openlb/src/descriptor/definition/common.h').read_text()
def table(name):
    body=re.search(r'\b'+name+r'<3,19>\[[^;]+?=\s*\{(.*?)\n\};',src,re.S).group(1)
    return np.array([[int(x) for x in row.split(',')] for row in re.findall(r'\{([^{}]+)\}',body)])
C=table('c');tw=table('t');W=tw[:,0]/tw[:,1]
assert C.shape==(19,3) and len(W)==19
def shift(f,c,sign=1):return np.roll(f,tuple(sign*np.array(c)),axis=(0,1,2))
def L(f):return sum(6*w*(shift(f,c,-1)-f) for c,w in zip(C,W))
def G(f):return np.array([sum(3*w*c[a]*shift(f,c,-1) for c,w in zip(C,W)) for a in range(3)])
def sumld(f):return np.sum(f,dtype=np.longdouble)
def rawcsv(path,dtype=np.float64):
    with Path(path).open() as f:header=f.readline().strip().split(',')
    data=np.loadtxt(path,delimiter=',',skiprows=1,dtype=dtype,ndmin=2)
    assert data.shape[1]==len(header) and np.isfinite(data).all(),path
    return {h:data[:,i] for i,h in enumerate(header)}
field_files=0;field_points=0
def field(path,n):
    global field_files,field_points
    f=rawcsv(path);assert len(f['phi'])==n**3,path
    pos=np.stack([f[a] for a in ['x','y','z']],axis=1);assert np.all(pos==np.rint(pos)) and np.all((pos>=0)&(pos<n))
    ind=((pos[:,0].astype(int)*n+pos[:,1].astype(int))*n+pos[:,2].astype(int));order=np.argsort(ind)
    assert np.array_equal(ind[order],np.arange(n**3)),path
    field_files+=1;field_points+=n**3
    return {h:a[order].reshape((n,)*3) for h,a in f.items() if h not in ['x','y','z']}
def coeff(phi,case,multiple=1):
    n=case['N'];index=tuple((multiple*np.array(case['mode']))%n)
    return (np.fft.fftn(phi-case['center'])/n**3)[index]
def fitted_rate(y):
    t=np.arange(len(y));start=int(np.ceil(.25*(len(y)-1)));t=t[start:];z=np.log(abs(y[start:]))
    tc=t-t.mean();return float(-np.dot(tc,z-z.mean())/np.dot(tc,tc))
def kinetic_reference(case,initial):
    k=2*np.pi*np.array(case['mode'])/case['N'];lam=np.sum(6*W*(1-np.cos(C@k)))
    ak=case['a']+case['kappa']*lam;e=W*ak;e[0]+=1-ak
    omega=1/case['tau'];T=np.diag(np.exp(-1j*C@k))@((1-omega)*np.eye(19)+omega*np.outer(e,np.ones(19)))
    times=np.arange(case['steps']+1)
    if case['tau']==1:curve=initial.sum()*(1-lam*ak/6)**times
    else:curve=np.array([np.sum(np.linalg.matrix_power(T,int(t))@initial) for t in times])
    ev=np.linalg.eigvals(T);hydro=ev[np.argmin(abs(ev-1))]
    return curve,-float(np.log(abs(hydro))),float((case['tau']-.5)/3*(k@k)*(case['a']+case['kappa']*(k@k)))
result=[];histories={};refcurves={};total_rows=0
for entry in manifest['cases']:
    rid=entry['run_id'];path=O/rid;sub=E/rid
    child=json.loads((sub/'manifest.json').read_text());assert child==entry
    assert int((sub/'exit_code.txt').read_text())==entry['independent_exit_code']==0
    assert entry['finished_utc'] and entry['cwd']==str(BASE)
    assert entry['command']==[str(BASE/'build/ab_check'),entry['stage'],entry['case_id'],str(path)]
    assert (sub/'console.log').is_file()
    cfg=json.loads((path/'config.json').read_text());done=json.loads((path/'result.json').read_text())
    name=entry['case_id']
    if entry['stage']=='a2':
        n=8;assert cfg['fixture']==name and cfg['N']==8 and cfg['tau']==1 and cfg['steps']==1 and cfg['MPI_ranks']==1
        assert done['completed_steps']==done['requested_steps']==1 and done['acceptance_evaluated']
        f=[field(path/(s+'.csv'),n) for s in ['initial','post_collision','post_stream','post_refresh']]
        before,post,streamed,after=f;bs=W*(-2.5+1.5*np.sum(C*C,axis=1))
        collision=0.;stream=0.;prediction=before['phi']+L(before['mu'])/6
        for i,(c,w,b) in enumerate(zip(C,W,bs)):
            eq=(before['phi']-(1-w)*before['mu'] if i==0 else w*before['mu'])-w
            collision=max(collision,float(np.max(abs(post['f'+str(i)]-eq-b*before['source']))))
            stream=max(stream,float(np.max(abs(streamed['f'+str(i)]-shift(post['f'+str(i)],c)))))
            prediction+=b*shift(before['source'],c)
        for v in f:assert np.max(abs(sum(v['f'+str(i)] for i in range(19))+1-v['phi']))<=1e-12
        diff=streamed['phi']-before['phi'];change=sumld(diff);source=sumld(before['source']);q=sumld(before['phi'])
        u=np.array([before[s] for s in ['ux','uy','uz']]);div=sum(G(u[a])[a] for a in range(3))
        adj=abs(source+sumld(before['phi']*div))/n**3
        point=float(np.max(abs(streamed['phi']-prediction)));budget=float(abs(change+source)/n**3)
        checks=[collision<=1e-12,stream<=1e-12,point<=TH['A2_point_update_absolute'],budget<=TH['A2_global_budget_per_node'],adj<=1e-12,np.max(abs(after['phi']-streamed['phi']))<=1e-12]
        if name=='constant_mu':checks.append(np.max(abs(diff))<=1e-12)
        result.append(dict(id=name,run_id=rid,kind='A2',N=n,checks_pass=bool(all(checks)),point_error=point,collision_error=collision,stream_error=stream,source_sum=float(source),phase_change=float(change),relative_phase_change=float(change/q),budget_per_node=budget,adjoint_per_node=float(adj),source_change_ratio=float(-change/source) if abs(source)>1e-15 else None))
        continue
    case=next(c for c in P['B_cases'] if c['id']==name);n=case['N'];steps=case['steps'];size=n**3
    for key in ['N','tau','center','amplitude','kappa','mode','steps']:assert cfg[key]==case[key],(name,key)
    assert cfg['nonlinear']==(case['kind']=='nonlinear') and cfg['fixture']=='' and cfg['MPI_ranks']==1
    assert done['completed_steps']==done['requested_steps']==steps and done['safe']
    h=rawcsv(path/'history.csv',np.longdouble);total_rows+=len(h['step']);histories[name]=h
    assert np.array_equal(h['step'],np.arange(steps+1)) and np.all(h['nodes']==size) and np.all(h['finite']==1)
    drift=(h['phase_sum']-h['phase_sum'][0])/h['phase_sum'][0];peak=int(np.argmax(abs(drift)))
    assert np.max(abs(drift-h['relative_drift']))<1e-14
    a=field(path/'initial.csv',n);b=field(path/'final.csv',n)
    fftdiff=0.;sumdiff=0.
    for f,t in [(a,0),(b,steps)]:
        assert all(np.max(abs(f[key]))==0 for key in ['source','source_old','ux','uy','uz'])
        fftdiff=max(fftdiff,float(abs(coeff(f['phi'],case)-complex(h['mode_re'][t],h['mode_im'][t]))))
        sumdiff=max(sumdiff,float(abs(sumld(f['phi'])-h['phase_sum'][t])/size))
    r=dict(id=name,run_id=rid,kind=case['kind'],N=n,tau=case['tau'],steps=steps,max_abs_drift=float(abs(drift[peak])),drift_peak_step=peak,signed_drift_at_peak=float(drift[peak]),final_drift=float(drift[-1]),FFT_vs_history_max_difference=fftdiff,field_sum_per_node_max_difference=sumdiff)
    checks=[r['max_abs_drift']<=TH['max_abs_relative_phase_drift'],fftdiff<1e-13,sumdiff<1e-13]
    if case['kind']=='linear':
        ini=rawcsv(path/'initial_population_modes.csv');assert np.array_equal(ini['population'],np.arange(19))
        initial=ini['re']+1j*ini['im'];assert abs(initial.sum()-coeff(a['phi'],case))<1e-13
        ref,discrete_rate,cont=kinetic_reference(case,initial);refcurves[name]=ref
        actual=np.asarray(h['mode_re'],float)+1j*np.asarray(h['mode_im'],float)
        err=float(max(abs(ref-actual))/case['amplitude']);obs_l2=float(max(h['reference_L2_over_initial_RMS']))
        endpoint=[];xyz=np.indices((n,)*3);theta=2*np.pi*sum(v*m for v,m in zip(xyz,case['mode']))/n
        # Compare to bound ideal-start curve for the exact solver-observer definition.
        bound=rawcsv(BASE/'reference'/(name+'.csv'));ideal=bound['re']+1j*bound['im']
        assert len(ideal)==steps+1 and max(abs(ideal-ref))/case['amplitude']<1e-8
        for f,t in [(a,0),(b,steps)]:
            exact=case['center']+2*(ideal[t].real*np.cos(theta)-ideal[t].imag*np.sin(theta))
            l2=float(np.sqrt(np.mean((f['phi']-exact)**2))/(case['amplitude']/np.sqrt(2)));endpoint.append(l2)
            assert abs(l2-h['reference_L2_over_initial_RMS'][t])<1e-9
        measured=fitted_rate(actual);reference_rate=fitted_rate(ref);ratio=measured/reference_rate
        continuum_error=abs(measured/cont-1)
        checks.extend([err<=TH['linear_complex_coefficient_over_initial_amplitude'],obs_l2<=TH['linear_fluctuation_L2_over_initial_RMS'],max(endpoint)<=TH['linear_fluctuation_L2_over_initial_RMS'],abs(ratio-1)<=TH['measured_fitted_rate_over_discrete_reference']])
        if case['tau']==1:checks.extend([continuum_error<=TH[f'linear_tau1_continuum_rate_N{n}'],max(h['one_step_max_error'])<=1e-12,max(abs(h['energy_balance_residual']))/size<=1e-12])
        r.update(max_mode_error_over_A=err,max_reported_L2_over_initial_RMS=obs_l2,independent_endpoint_L2=endpoint,measured_rate=measured,reference_rate=reference_rate,rate_ratio=ratio,hydrodynamic_eigenmode_rate=discrete_rate,continuum_rate=cont,continuum_relative_error=float(continuum_error),signed_continuum_rate_bias=float(measured/cont-1))
    else:
        old=None;max_mu=0.;max_update=0.;max_energy=0.;max_diss=0.;max_time=0.;max_balance=0.
        for t in range(steps+1):
            f=field(path/f'field_step_{t}.csv',n);phi=f['phi'];mu=f['mu'];beta=case['beta'];kap=case['kappa']
            expect=4*beta*phi*(phi-1)*(phi-.5)-kap*L(phi);max_mu=max(max_mu,float(max(abs(expect-mu).flat)))
            energy=sumld(beta*phi**2*(phi-1)**2-kap/2*phi*L(phi));diss=-sumld(mu*L(mu))/6
            max_energy=max(max_energy,float(abs(energy-h['free_energy'][t])/size));max_diss=max(max_diss,float(abs(diss-h['link_dissipation'][t])/size))
            assert abs(sumld(phi)-h['phase_sum'][t])/size<1e-13
            for multiple in [1,2,3]:
                value=coeff(phi,case,multiple)
                if multiple==1:assert abs(value-complex(h['mode_re'][t],h['mode_im'][t]))<1e-13
                else:assert abs(value.real-h[f'harmonic{multiple}_re'][t])<1e-13
            if old is not None:
                delta=phi-old['phi'];update=float(np.max(abs(delta-L(old['mu'])/6)));max_update=max(max_update,update)
                work=sumld(old['mu']*delta);time=energy-old_energy-work;balance=energy-old_energy+old_diss-time
                max_time=max(max_time,float(abs(time-h['energy_time_remainder'][t])/size));max_balance=max(max_balance,float(abs(balance)/size))
                assert abs(balance-h['energy_balance_residual'][t])/size<1e-12
            old=f;old_energy=energy;old_diss=diss
        r.update(max_constitutive_mu_error=max_mu,max_local_update_error=max_update,max_energy_definition_per_node=max_energy,max_link_dissipation_definition_per_node=max_diss,max_time_remainder_definition_per_node=max_time,max_energy_balance_per_node=max_balance)
        checks.extend([max_mu<=TH['mu_absolute'],max_update<=TH['nonlinear_step_absolute'],max_energy<=1e-12,max_diss<=1e-12,max_time<=1e-12,max_balance<=1e-12])
    r['checks_pass']=bool(all(checks));result.append(r)

linear=[r for r in result if r['kind']=='linear'];nonlinear=[r for r in result if r['kind']=='nonlinear'];allb=linear+nonlinear
comparison=[]
for n in [16,32]:
    axis=[next(r for r in linear if r['id']==f'lin_n{n}_{a}_t100')['rate_ratio'] for a in ['x','y','z']]
    comparison.append(dict(check='axis_spread_N'+str(n),value=max(axis)-min(axis),pass_=max(axis)-min(axis)<=TH['axis_symmetry_rate_spread']))
refinement=[]
for name in ['x','y','z','xy','xyz']:
    errors=[next(r for r in linear if r['id']==f'lin_n{n}_{name}_t100')['continuum_relative_error'] for n in [16,32]]
    comparison.append(dict(check='error_reduction_'+name,pass_=errors[1]<errors[0]))
    refinement.append(dict(mode=name,coarse_error=errors[0],fine_error=errors[1],reduction_factor=errors[0]/errors[1],two_level_log2_ratio=float(np.log2(errors[0]/errors[1]))))
frozen=json.loads((HERE/'frozen_analysis.json').read_text());frozen_by={r['id']:r for r in frozen['all_cases']}
max_rate_difference=max(abs(r['measured_rate']-frozen_by[r['id']]['measured_rate']) for r in linear)
max_drift_difference=max(abs(r['max_abs_drift']-frozen_by[r['id']]['drift']['max_abs']) for r in allb)
peak=max(allb,key=lambda r:r['max_abs_drift'])
summary=dict(batch_id=BATCH,started_UTC=manifest['started_utc'],finished_UTC=manifest['finished_utc'],wall_seconds=(dt.datetime.fromisoformat(manifest['finished_utc'])-dt.datetime.fromisoformat(manifest['started_utc'])).total_seconds(),complete_cases=22,independent_child_exit_zero=22,history_rows=total_rows,field_files_read=field_files,field_points_read=field_points,bound_hashes_rechecked=len(manifest['source_binding']['sha256']),all_input_hashes_saved=len(protected),old_protected_hashes=2274,all_checks_pass=all(r['checks_pass'] for r in result) and all(r['pass_'] for r in comparison),max_B_drift=peak,max_linear_mode_error_over_A=max(r['max_mode_error_over_A'] for r in linear),max_linear_reported_L2=max(r['max_reported_L2_over_initial_RMS'] for r in linear),max_rate_relative_error_to_discrete=max(abs(r['rate_ratio']-1) for r in linear),frozen_vs_independent_rate_max_absolute=max_rate_difference,frozen_vs_independent_drift_max_absolute=max_drift_difference,all_cases=result,matrix_checks=comparison,refinement=refinement,new_OpenLB_run=False,solver_recompiled=False,NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS='NOT_EVALUATED',geometry_PASS='NOT_EVALUATED')
assert summary['all_checks_pass'] and total_rows==18002 and field_files==120 and field_points==1925120
assert max_rate_difference<1e-14 and max_drift_difference<1e-18
for name,hsh in protected.items():assert sha(name)==hsh,name
(HERE/'independent_checks.json').write_text(json.dumps(summary,indent=2)+'\n')
def savecsv(name,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with (HERE/name).open('w') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)
savecsv('case_metrics.csv',result);savecsv('refinement.csv',refinement)

plt.rcParams.update({'font.size':10,'pdf.fonttype':42,'savefig.facecolor':'white'})
colors=['#0072B2','#D55E00','#009E73']
fig,axes=plt.subplots(2,2,figsize=(11,8.2),layout='constrained')
ax=axes[0,0]
for tag,tau,col in [('075',.75,colors[0]),('100',1.,colors[1]),('250',2.5,colors[2])]:
    key=f'lin_n32_x_t{tag}';h=histories[key];a=np.asarray(h['mode_re'],float)+1j*np.asarray(h['mode_im'],float);ref=refcurves[key];t=np.asarray(h['step'],float)/2048
    ax.semilogy(t,abs(a)/abs(a[0]),color=col,lw=1.5,label=f'tau={tau:g}: measured')
    ax.semilogy(t[::64],abs(ref[::64])/abs(ref[0]),ls='none',marker='o',ms=3,mfc='none',color=col)
ax.set(xlabel='Step / final step',ylabel='Fourier amplitude / initial amplitude',title='(a) Full kinetic reference (open circles)');ax.legend(fontsize=8);ax.grid(alpha=.2)
ax=axes[0,1];names=['x','y','z','xy','xyz'];x=np.arange(5)
for n,col,marker in [(16,colors[0],'o'),(32,colors[1],'s')]:
    errors=[100*next(r for r in linear if r['id']==f'lin_n{n}_{d}_t100')['continuum_relative_error'] for d in names]
    ax.plot(x,errors,marker=marker,color=col,label=f'N={n}')
ax.axhline(5,color=colors[0],ls=':',label='N16 limit 5%');ax.axhline(2,color=colors[1],ls='--',label='N32 limit 2%');ax.set_xticks(x,names)
ax.set(ylim=(0,5.5),ylabel='Absolute decay-rate error (%)',xlabel='Wavevector direction',title='(b) tau=1, continuum comparison');ax.legend(fontsize=8,ncol=2);ax.grid(alpha=.2)
ax=axes[1,0]
for tag,tau,col,marker in [('075',.75,colors[0],'o'),('100',1.,colors[1],'s'),('250',2.5,colors[2],'^')]:
    ratios=[next(r for r in linear if r['id']==f'lin_n{n}_x_t{tag}') for n in [16,32]]
    ax.plot([16,32],[r['measured_rate']/r['continuum_rate'] for r in ratios],marker=marker,color=col,label=f'tau={tau:g}')
ax.axhline(1,color='0.3',ls='--',lw=1);ax.set(xticks=[16,32],ylim=(0,1.1),xlabel='N',ylabel='Measured / continuum decay rate',title='(c) Discrete agreement is distinct from accuracy');ax.legend(fontsize=8);ax.grid(alpha=.2)
ax=axes[1,1]
for key,col,ls in [('lin_n32_x_t075',colors[0],'-'),('lin_n32_xyz_t100',colors[1],'--'),('lin_n32_x_t250',colors[2],':')]:
    h=histories[key];d=(h['phase_sum']-h['phase_sum'][0])/h['phase_sum'][0]
    ax.plot(np.asarray(h['step'],float)/float(h['step'][-1]),np.asarray(d,float)/1e-13,color=col,ls=ls,label=key.replace('lin_n32_',''))
ax.set(xlabel='Step / final step',ylabel='Signed phase-amount drift (x 1e-13)',title='(d) Full-history conservation, B cases');ax.legend(fontsize=8)
ax.text(.03,.96,'All B max = 2.9553e-13; limit = 1e-9',transform=ax.transAxes,va='top',fontsize=8);ax.grid(alpha=.2)
fig.savefig(HERE/'AB_diagnostics.png',dpi=200,facecolor='white');fig.savefig(HERE/'AB_diagnostics.pdf',facecolor='white');plt.close(fig)
provenance=dict(purpose='Internal verification diagnostic; no journal compliance claim',raw_batch_id=BATCH,sources='input_hashes.json, case_metrics.csv, independent_checks.json',transformations=['FFT normalization by N^3','fixed last 75 percent rate fit','amplitude normalized by initial amplitude','signed long-double phase drift','continuum-relative rate errors'],smoothing='none',uncertainty='deterministic trajectories; no statistical error bars',missing_data='none in required records',reference='independent matrix powers or tau1 scalar powers; no OpenLB rerun',matplotlib_version=matplotlib.__version__,size_inches=[11,8.2],PNG_dpi=200,alt_text='Four panels show kinetic-reference agreement, decreasing tau1 grid errors, the large tau2.5 continuum-rate bias, and very small full-history conserved-phase drift.')
(HERE/'figure_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['all_cases','matrix_checks','refinement','max_B_drift']},indent=2))
