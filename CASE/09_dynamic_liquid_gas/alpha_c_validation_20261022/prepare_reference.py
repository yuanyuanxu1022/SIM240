#!/usr/bin/env python3
"""Generate pre-run parameters and independent alpha-only discrete references.

This performs finite matrix algebra, not OpenLB or spatial time evolution.
Do not run again after freeze or change an existing protocol.
"""
from pathlib import Path
import csv
import itertools
import json
import numpy as np

BASE=Path(__file__).resolve().parent

def build():
    cases=[]
    modes={'x':(1,0,0),'y':(0,1,0),'z':(0,0,1),'xy':(1,1,0),'xyz':(1,1,1)}
    for n,alpha in ((16,1.),(32,4.)):
        dx=40/n;dt=(dx*1e-9)**2/(6e-5);sigma=.03*dt**2/(1000*(dx*1e-9)**3)
        width=10/dx;beta=12*sigma/width;kappa=1.5*sigma*width
        for label,mode in modes.items():
            cases.append(dict(id=f'linear_n{n}_{label}_a{int(alpha)}',kind='linear',N=n,
                alpha=alpha,tau=1.,dx_nm=dx,dt_s=dt,sigma=sigma,width=width,
                beta=beta,kappa=kappa,center=.1,amplitude=.001,a=.46*beta,
                mode=mode,steps=128 if n==16 else 512))
        for center in (.1,.9):
            cases.append(dict(id=f'nonlinear_n{n}_c{int(center*100):03d}_a{int(alpha)}',kind='nonlinear',N=n,
                alpha=alpha,tau=1.,dx_nm=dx,dt_s=dt,sigma=sigma,width=width,
                beta=beta,kappa=kappa,center=center,amplitude=.0001,a=0.,mode=(1,0,0),steps=16 if n==16 else 64))
    for alpha in (1.,4.):
        cases.append(dict(id=f'source_n8_a{int(alpha)}',kind='source',N=8,alpha=alpha,tau=1.,
            dx_nm=2.5,dt_s=1.0416666666666667e-13,sigma=2.0833333333333333e-5,
            width=4.,beta=6.25e-5,kappa=1.25e-4,center=.35,amplitude=.08,a=0.,mode=(1,0,0),steps=1))
    c_cases=[dict(id=f'C_{r}_{mu}',density=r,chemical=mu,N=64,steps=64,alpha=1.,tau=1.,
                 rhos=[1.,1.] if r=='equal' else [1.,.0012],taus=[1.,1.25])
             for r in ('equal','target') for mu in ('mu0','constitutive')]
    protocol=dict(protocol_id='ALPHA_C_DIAGNOSTICS_20261022_v1',status='FROZEN_BEFORE_FORMAL_SPATIAL_RUNS',
        stages={'alpha':cases,'c':c_cases},batch_prefix='alpha_c_20261022_v1',
        backend=dict(root='/home/dell/openlb',MPI_ranks=1,platform='CPU_SISD',descriptor='D3Q19',overlap=3),
        material=dict(rho_reference_kg_m3=1000.,mu_liquid_Pa_s=.010,rho_gas_kg_m3=1.2,
                      mu_gas_Pa_s=1.8e-5,sigma_SI=.03,interface_width_m=1e-8,
                      M_SI=1.736111111111111e-17,GHY_measurements=False),
        thresholds=dict(local_absolute=1e-12,phase_relative_drift=1e-9,mass_relative_drift=1e-9,
            Mach=.05,mode_over_initial_amplitude=1e-8,field_L2_over_initial_RMS=1e-8,
            rate_relative_to_discrete=1e-4,continuous_rate_error_coarse=.07,
            continuous_rate_error_fine=.02,axis_normalized_rate_spread=.002),
        alpha_fit_window='ceil(.25*steps)..steps inclusive; no tail-window selection',
        c_output=dict(frame_fields=['phi','mu','source','source_old','ux','uy','uz','jx','jy','jz','Fx','Fy','Fz','p_h','rho','tau'],
                      every_step=True,format='gzip level1, little-endian float64 C-order (x,y,z,field)',
                      named_snapshot_steps=[0,1,16,32,64],
                      step1_population_stages=['pre','post_collision','post_stream'],
                      population_columns='ns_f0..18,ch_f0..18; same gzip layout, last axis 38'),
        gates={k:'NOT_EVALUATED' for k in ('NUMERICAL_GATE','RESULT_PASS','geometry_PASS')})
    (BASE/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    header=['// Generated before execution from protocol.json.\n#pragma once\n',
            'struct AlphaConfig {const char* id;const char* kind;int n,steps,mx,my,mz;double alpha,tau,sigma,width,beta,kappa,center,amplitude,a,dx_nm,dt_s;};\n',
            'inline const AlphaConfig alphaConfigs[]={\n']
    cvel=np.array([(0,0,0)]+[v for v in itertools.product((-1,0,1),repeat=3) if sum(x*x for x in v) in (1,2)])
    weights=np.array([1/3 if sum(v*v)==0 else 1/18 if sum(v*v)==1 else 1/36 for v in cvel])
    checks=[]
    for c in cases:
        vals=[c[k] for k in ('N','steps')]+list(c['mode'])+[c[k] for k in ('alpha','tau','sigma','width','beta','kappa','center','amplitude','a','dx_nm','dt_s')]
        header.append('{"'+c['id']+'","'+c['kind']+'",'+','.join(format(v,'.17g') for v in vals)+'},\n')
        if c['kind']!='linear':continue
        k=2*np.pi*np.array(c['mode'])/c['N'];lh=float(np.sum(6*weights*(1-np.cos(cvel@k))))
        ak=c['alpha']*(c['a']+c['kappa']*lh);e=weights*ak;e[0]+=1-ak
        matrix=np.exp(-1j*(cvel@k))[:,None]*(e[:,None]*np.ones((1,19)))
        eigen=np.linalg.eigvals(matrix);v=eigen[np.argmin(abs(eigen-1))]
        scalar=1-c['alpha']/6*lh*(c['a']+c['kappa']*lh)
        assert abs(v-scalar)<1e-13
        ce=c['alpha']/6*(k@k)*(c['a']+c['kappa']*(k@k));rate=-np.log(scalar)
        limit=.07 if c['N']==16 else .02
        assert abs(rate/ce-1)<limit
        with (BASE/'reference'/f'{c["id"]}.csv').open('w') as f:
            w=csv.writer(f);w.writerow(['step','mode_re','mode_im'])
            for step in range(c['steps']+1):w.writerow([step,c['amplitude']/2*scalar**step,0.])
        checks.append(dict(id=c['id'],g=scalar,rate=rate,continuum_rate=float(ce),
                           continuous_relative_error=float(rate/ce-1),preset_limit=limit))
    header.append('};\n');(BASE/'src/alpha_configs.h').write_text(''.join(header))
    (BASE/'evidence/reference_static_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    return protocol

if __name__=='__main__':
    if (BASE/'evidence/build_binding.json').exists():raise SystemExit('Refusing generation after frozen binding')
    p=build();print('Prepared',len(p['stages']['alpha']),'alpha spatial cases and',len(p['stages']['c']),'C cases; no solver started')
