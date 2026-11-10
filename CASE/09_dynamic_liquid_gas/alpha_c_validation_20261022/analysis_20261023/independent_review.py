"""Offline second implementation. Does not import frozen numerical helpers or run OpenLB."""
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
BATCH = 'alpha_c_20261022_v1_alpha'
C = np.array([[0,0,0],[-1,0,0],[0,-1,0],[0,0,-1],[-1,-1,0],[-1,1,0],[-1,0,-1],[-1,0,1],[0,-1,-1],[0,-1,1],[1,0,0],[0,1,0],[0,0,1],[1,1,0],[1,-1,0],[1,0,1],[1,0,-1],[0,1,1],[0,1,-1]])
W = np.array([1/3]+[1/18]*3+[1/36]*6+[1/18]*3+[1/36]*6)
coverage = {'field_files': 0, 'field_rows': 0, 'history_rows': 0}

def require(ok, message):
    if not ok:
        raise AssertionError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def readj(path):
    return json.loads(Path(path).read_text())

def csvdata(path):
    with Path(path).open() as f:
        names = f.readline().strip().split(',')
    a = np.loadtxt(path, delimiter=',', skiprows=1, ndmin=2)
    require(a.shape[1] == len(names) and np.isfinite(a).all(), 'CSV finite/column '+str(path))
    return {k: a[:,j] for j,k in enumerate(names)}

def field(path, n):
    d = csvdata(path)
    xyz = np.column_stack([d[k] for k in ('x','y','z')])
    require(xyz.shape == (n**3,3), 'field length '+str(path))
    require(np.all(xyz == xyz.astype(int)) and np.all((xyz>=0)&(xyz<n)), 'coordinates '+str(path))
    ix = xyz.astype(int)
    flat = (ix[:,0]*n+ix[:,1])*n+ix[:,2]
    require(np.array_equal(np.sort(flat),np.arange(n**3)), 'duplicate/missing coordinates '+str(path))
    order = np.argsort(flat)
    coverage['field_files'] += 1
    coverage['field_rows'] += n**3
    return {k:v[order].reshape((n,)*3) for k,v in d.items() if k not in ('x','y','z')}

def lap(a):
    out = np.zeros_like(a)
    for j in range(1,19):
        out += (6*W[j])*(np.roll(a,tuple(-C[j]),axis=(0,1,2))-a)
    return out

def gradient(a):
    g = np.zeros((3,)+a.shape)
    for j in range(1,19):
        g += (3*W[j])*C[j,:,None,None,None]*np.roll(a,tuple(-C[j]),axis=(0,1,2))
    return g

def fftmode(a, mode, center):
    return np.fft.fftn(a-center)[tuple(mode)]/a.size

def fitrate(z):
    t = np.arange(len(z),dtype=float)
    start = int(np.ceil((len(z)-1)/4))
    t = t[start:]; y = np.log(np.abs(z[start:]))
    x = t-t.mean()
    return float(-np.dot(x,y-y.mean())/np.dot(x,x))

def maximum(a):
    return float(np.max(np.abs(a)))

def physicalmu(p,c):
    return 4*c['beta']*p*(p-1)*(p-.5)-c['kappa']*lap(p)

def main():
    protocol = readj(BASE/'protocol.json')
    limits = protocol['thresholds']
    cases = protocol['stages']['alpha']
    manifest = readj(BASE/'evidence'/BATCH/'manifest.json')
    frozen = readj(HERE/'frozen_export_adapted/verdict.json')
    binding = readj(BASE/'evidence/build_binding.json')
    require(manifest['protocol_id']==protocol['protocol_id'] and manifest['batch_id']==BATCH and manifest['stage']=='alpha','batch identity')
    require(manifest['source_binding']==binding and manifest['source_hashes_unchanged'] and not manifest['source_mismatches'],'binding provenance')
    require(manifest['independent_exit_code']==0 and int((BASE/'evidence'/BATCH/'exit_code.txt').read_text())==0,'batch independent exit')
    require([m['case_id'] for m in manifest['cases']]==[c['id'] for c in cases] and len(cases)==16,'ordered complete matrix')
    mismatches = [p for p,h in binding['sha256'].items() if not Path(p).is_file() or sha(p)!=h]
    rawhash = readj(HERE/'raw_input_hashes.json')
    rawmismatch = [p for p,h in rawhash.items() if not Path(p).is_file() or sha(p)!=h]
    require(not mismatches and not rawmismatch,'bound/raw input hashes')
    require(all(sha(p)==h for p,h in frozen['input_sha256'].items()),'frozen analysis input hashes')
    result = []
    for c,entry in zip(cases,manifest['cases']):
        rid = BATCH+'_'+c['id']; n=c['N']; steps=c['steps']
        ev = BASE/'evidence'/BATCH/rid
        out = BASE/'output'/BATCH/rid
        require(entry==readj(ev/'manifest.json') and entry['run_id']==rid and entry['parameters']==c,'child manifest '+rid)
        require(entry['independent_exit_code']==0 and int((ev/'exit_code.txt').read_text())==0,'child independent exit '+rid)
        require(datetime.fromisoformat(entry['finished_utc'])>=datetime.fromisoformat(entry['started_utc']),'child timestamps')
        require((ev/'console.log').stat().st_size>0 and '--initialize-only' not in entry['command'],'formal log/command')
        require(entry['command']==[str(BASE/'build/alpha_diffusion'),c['id'],str(out)],'exact command')
        cfg=readj(out/'config.json'); res=readj(out/'result.json')
        require(cfg['case_id']==c['id'] and cfg['N']==n and cfg['steps']==steps and cfg['nominal_steps']==steps,'config completion')
        require(cfg['MPI_ranks']==1 and cfg['mode']==c['mode'] and cfg['nonlinear']==(c['kind']!='linear'),'config model')
        require(cfg['fixture']==('compressible' if c['kind']=='source' else ''),'fixture')
        for k in ('alpha','tau','sigma','width','center','amplitude','a','kappa'):
            require(np.isclose(cfg[k],c[k],rtol=1e-14,atol=1e-30),'parameter '+k)
        require(res['requested_steps']==steps and res['completed_steps']==steps,'completed steps')
        ini=field(out/'initial.csv',n)
        r={'id':c['id'],'N':n,'kind':c['kind'],'alpha':c['alpha'],'steps':steps}
        checks={}
        if c['kind']=='source':
            post=field(out/'post_collision.csv',n); stream=field(out/'post_stream.csv',n); refresh=field(out/'post_refresh.csv',n)
            p=ini['phi']; mu=ini['mu']; S=ini['source']; b=W*(-2.5+1.5*np.sum(C*C,axis=1))
            errors={'velocity':maximum(np.array([ini[k] for k in ('ux','uy','uz')])-.01*gradient(p)),
                    'source':maximum(S-np.sum(.01*gradient(p)*gradient(p),axis=0)),
                    'old_source':maximum(ini['source_old']-S), 'initial_mu':maximum(mu-physicalmu(p,c)),
                    'refreshed_mu':maximum(refresh['mu']-physicalmu(refresh['phi'],c))}
            collision=0.; migration=0.; transported=np.zeros_like(p)
            for j in range(19):
                eq=W[j]*c['alpha']*mu-W[j]
                if j==0: eq += p-c['alpha']*mu
                collision=max(collision,maximum(post['f'+str(j)]-eq-b[j]*S))
                migration=max(migration,maximum(stream['f'+str(j)]-np.roll(post['f'+str(j)],tuple(C[j]),axis=(0,1,2))))
                transported += b[j]*np.roll(S,tuple(C[j]),axis=(0,1,2))
            errors.update(collision=collision,migration=migration,
                          point=maximum(stream['phi']-p-c['alpha']/6*lap(mu)-transported),
                          budget_per_node=float(abs(np.sum(stream['phi']-p,dtype=np.longdouble)+np.sum(S,dtype=np.longdouble))/n**3),
                          refresh_phi=maximum(refresh['phi']-stream['phi']))
            errors['population_phi']=max(maximum(f['phi']-1-sum(f['f'+str(j)] for j in range(19))) for f in (ini,post,stream,refresh))
            require(res['acceptance_evaluated'],'source evaluation flag')
            checks={k:v<=limits['local_absolute'] for k,v in errors.items()}
            r.update(errors=errors,source_sum=float(np.sum(S,dtype=np.longdouble)),phase_change=float(np.sum(stream['phi']-p,dtype=np.longdouble)))
        else:
            require(res['safe'],'safe output')
            hist=csvdata(out/'history.csv'); coverage['history_rows']+=len(hist['step'])
            require(np.array_equal(hist['step'],np.arange(steps+1)) and np.all(hist['nodes']==n**3) and np.all(hist['finite']==1),'history coverage')
            # Preserve decimal phase sums in long double rather than round through binary64.
            with (out/'history.csv').open() as f: text=list(csv.DictReader(f))
            q=np.array([x['phase_sum'] for x in text],dtype=np.longdouble); drift=(q-q[0])/q[0]; peak=int(np.argmax(abs(drift)))
            require(maximum(drift-hist['relative_drift'])<1e-14,'reported drift')
            r.update(phase_drift_max=float(abs(drift[peak])),phase_drift_step=peak,phase_drift_final=float(drift[-1]))
            checks['phase_amount']=r['phase_drift_max']<=limits['phase_relative_drift']
            end=field(out/'final.csv',n)
            for f,t in ((ini,0),(end,steps)):
                require(max(maximum(f[k]) for k in ('source','source_old','ux','uy','uz'))==0,'unforced fixture')
                require(abs(np.sum(f['phi'],dtype=np.longdouble)-q[t])/n**3<1e-13,'field/history phase')
                require(abs(fftmode(f['phi'],c['mode'],c['center'])-complex(hist['mode_re'][t],hist['mode_im'][t]))<1e-13,'field/history Fourier')
            checks['observer_point']=maximum(hist['one_step_max_error'])<=limits['local_absolute']
            if c['kind']=='linear':
                # Full population matrix, implemented directly here without frozen imports.
                k=2*np.pi*np.array(c['mode'])/n
                symbol=np.dot(6*W,1-np.cos(C@k))
                eq=W*c['alpha']*(c['a']+c['kappa']*symbol); eq[0]+=1-eq.sum()
                T=np.diag(np.exp(-1j*(C@k)))@((1-1/c['tau'])*np.eye(19)+(1/c['tau'])*eq[:,None]*np.ones((1,19)))
                modes=csvdata(out/'initial_population_modes.csv')
                require(np.array_equal(modes['population'],np.arange(19)),'19 modal populations')
                z=modes['re']+1j*modes['im']; ideal=c['amplitude']/2*eq.astype(complex)
                require(abs(sum(z)-fftmode(ini['phi'],c['mode'],c['center']))<1e-13,'population Fourier')
                ref=[]; ideal_seq=[]
                for t in range(steps+1):
                    ref.append(sum(z)); ideal_seq.append(sum(ideal));z=T@z;ideal=T@ideal
                ref=np.array(ref);measured=hist['mode_re']+1j*hist['mode_im']
                scalar=(1-c['alpha']*symbol*(c['a']+c['kappa']*symbol)/6)**np.arange(steps+1)*ref[0]
                require(maximum(ref-scalar)/c['amplitude']<1e-8,'tau1 scalar/matrix cross-check')
                fr=fitrate(measured); rr=fitrate(ref)
                continuum=c['alpha']*(c['tau']-.5)/3*np.dot(k,k)*(c['a']+c['kappa']*np.dot(k,k))
                xyz=np.indices((n,)*3);theta=sum(k[j]*xyz[j] for j in range(3))
                endpoint=[]
                for f,t in ((ini,0),(end,steps)):
                    expected=c['center']+2*np.real(ideal_seq[t]*np.exp(1j*theta))
                    endpoint.append(float(np.sqrt(np.mean((f['phi']-expected)**2))/(c['amplitude']/np.sqrt(2))))
                r.update(rate=fr,reference_rate=rr,rate_ratio=fr/rr,continuum_relative_error=abs(fr/continuum-1),
                         mode_error_over_A=maximum(measured-ref)/c['amplitude'],endpoint_3D_L2=endpoint,
                         all_step_observed_L2=maximum(hist['reference_L2_over_initial_RMS']),fit_window=[int(np.ceil(steps/4)),steps])
                checks.update(discrete_fit=abs(fr/rr-1)<=limits['rate_relative_to_discrete'],
                              continuum=r['continuum_relative_error']<=limits['continuous_rate_error_coarse' if n==16 else 'continuous_rate_error_fine'],
                              mode=r['mode_error_over_A']<=limits['mode_over_initial_amplitude'],
                              endpoint_L2=max(endpoint)<=limits['field_L2_over_initial_RMS'],
                              observer_L2=r['all_step_observed_L2']<=limits['field_L2_over_initial_RMS'])
            else:
                muerr=step_error=identity=energy_history=diss_history=0.; old=None
                for t in range(steps+1):
                    f=field(out/f'field_step_{t}.csv',n);p=f['phi'];mu=f['mu']
                    require(abs(np.sum(p,dtype=np.longdouble)-q[t])/n**3<1e-13,'nonlinear phase history')
                    require(max(maximum(f[k]) for k in ('source','source_old','ux','uy','uz'))==0,'nonlinear unforced')
                    muerr=max(muerr,maximum(mu-physicalmu(p,c)))
                    energy=np.sum(c['beta']*p*p*(p-1)**2-c['kappa']/2*p*lap(p),dtype=np.longdouble)
                    diss=-c['alpha']/6*np.sum(mu*lap(mu),dtype=np.longdouble)
                    energy_history=max(energy_history,float(abs(energy-np.longdouble(text[t]['free_energy']))/n**3))
                    diss_history=max(diss_history,float(abs(diss-np.longdouble(text[t]['link_dissipation']))/n**3))
                    if old is not None:
                        dp=p-old['phi'];step_error=max(step_error,maximum(dp-c['alpha']/6*lap(old['mu'])))
                        remainder=energy-oldenergy-np.sum(old['mu']*dp,dtype=np.longdouble)
                        residual=energy-oldenergy+olddiss-remainder
                        identity=max(identity,float(abs(residual)/n**3))
                        require(abs(remainder-np.longdouble(text[t]['energy_time_remainder']))/n**3<1e-12,'time remainder history')
                        require(abs(residual-np.longdouble(text[t]['energy_balance_residual']))/n**3<1e-12,'energy residual history')
                    old=f;oldenergy=energy;olddiss=diss
                require(maximum(ini['phi']-field_no_count(out/'field_step_0.csv',n)['phi'])==0,'initial endpoint duplicate')
                require(maximum(end['phi']-old['phi'])==0,'final endpoint duplicate')
                r.update(mu_error=muerr,step_error=step_error,energy_residual_per_node=identity,energy_history_error=energy_history,dissipation_history_error=diss_history)
                checks.update(actual_mu=muerr<=1e-12,full_field_step=step_error<=1e-12,energy_identity=identity<=1e-12,energy_observers=max(energy_history,diss_history)<=1e-12)
        r['checks']={k:bool(v) for k,v in checks.items()};r['operator_contract_pass']=all(checks.values())
        frozen_case=next(x for x in frozen['all_cases'] if x['id']==c['id'])
        require(r['operator_contract_pass']==frozen_case['operator_contract_pass'],'frozen/independent verdict disagreement')
        if c['kind']=='linear':
            require(abs(r['rate_ratio']-frozen_case['rate_ratio'])<1e-7,'independent rate agreement')
            require(abs(r['continuum_relative_error']-frozen_case['continuum_relative_error'])<1e-7,'independent continuum agreement')
        result.append(r)
        print(c['id'],r['operator_contract_pass'],flush=True)
    matrix=[]
    for n,alpha in ((16,1),(32,4)):
        ratios=[next(r['rate_ratio'] for r in result if r['id']==f'linear_n{n}_{d}_a{alpha}') for d in ('x','y','z')]
        spread=max(ratios)-min(ratios);matrix.append(dict(name=f'axes_n{n}',spread=spread,passed=bool(spread<=limits['axis_normalized_rate_spread'])))
    for d in ('x','y','z','xy','xyz'):
        errors=[next(r['continuum_relative_error'] for r in result if r['id']==f'linear_n{n}_{d}_a{a}') for n,a in ((16,1),(32,4))]
        matrix.append(dict(name='refinement_'+d,errors=errors,reduction_factor=errors[0]/errors[1],passed=bool(errors[1]<errors[0])))
    totals=dict(checked_utc=datetime.now(timezone.utc).isoformat(),batch_id=BATCH,protocol_id=protocol['protocol_id'],
                independent_exit_codes=[0]*17,bound_files=len(binding['sha256']),bound_mismatches=mismatches,
                raw_files=len(rawhash),raw_mismatches=rawmismatch,coverage=coverage,all_cases=result,matrix_checks=matrix,
                elapsed_seconds=(datetime.fromisoformat(manifest['finished_utc'])-datetime.fromisoformat(manifest['started_utc'])).total_seconds(),
                operator_contract_pass=bool(all(r['operator_contract_pass'] for r in result) and all(r['passed'] for r in matrix)),
                NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS='NOT_EVALUATED',geometry_PASS='NOT_EVALUATED',
                limitations=['linear intermediate 3D fields unavailable; all-time L2 is solver observer','two grids are not GCI','pure CH phase amount is not coupled NS mass'])
    totals['frozen_comparison_max_continuum_error_difference']=max(abs(r['continuum_relative_error']-next(f['continuum_relative_error'] for f in frozen['all_cases'] if f['id']==r['id'])) for r in result if r['kind']=='linear')
    (HERE/'independent_review.json').write_text(json.dumps(totals,indent=2)+'\n')
    with (HERE/'case_summary.csv').open('w') as f:
        names=['id','N','alpha','steps','operator_contract_pass','phase_drift_max','phase_drift_step','phase_drift_final','continuum_relative_error','rate_ratio','step_error','energy_residual_per_node']
        w=csv.DictWriter(f,fieldnames=names,extrasaction='ignore');w.writeheader();w.writerows(result)
    print(json.dumps({k:v for k,v in totals.items() if k not in ('all_cases','limitations')},indent=2))

def field_no_count(path,n):
    # Reuse structural validation without double-counting an already-audited file.
    before=coverage.copy();out=field(path,n);coverage.update(before);return out

if __name__=='__main__':
    main()
