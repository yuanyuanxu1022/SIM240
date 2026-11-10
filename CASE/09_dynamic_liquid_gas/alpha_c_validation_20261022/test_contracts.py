#!/usr/bin/env python3
"""Synthetic data/negative controls for independent audits; no solver calls."""
import gzip
import json
from pathlib import Path
import tempfile
import numpy as np
from analyze_alpha import drift
from analyze_c import binary,quantities,population_step1
from numerical_reference import C,W,lap,grad,matrix,sequence
from run_suite import BASE,PROTOCOL

def main():
    checks=[]
    n=8;x,y,z=np.indices((n,)*3);phi=.35+.08*np.cos(2*np.pi*x/n+.31)+.04*np.sin(2*np.pi*y/n+.2)
    zero=np.zeros_like(phi);rho=1-.9988*phi
    f={k:zero.copy() for k in ['mu','source','source_old','ux','uy','uz','jx','jy','jz','Fx','Fy','Fz','p_h']}
    f.update(phi=phi,rho=rho,tau=1+.25*phi)
    cfg=dict(rhos=[1,.0012],constant_mu_zero=True,beta=6.25e-5,kappa=1.25e-4)
    q=quantities(f,cfg)
    assert q['Mach_max']==0 and q['half_force_velocity_error']==0 and q['mu_constitutive_max_error']==0
    checks.append('zero_mu_variable_density_static_control')
    # Deliberately create full population evidence for an exact zero-force hold.
    pops=np.zeros((n,n,n,38));pops[...,19:]=-W;pops[...,19]+=phi
    with tempfile.TemporaryDirectory(prefix='sim240_alpha_c_static_') as folder:
        out=Path(folder)
        for name in ('step1_pre.bin.gz','step1_post_collision.bin.gz','step1_post_stream.bin.gz'):
            with gzip.open(out/name,'wb') as h:h.write(pops.astype('<f8').tobytes())
        metrics=population_step1(out,n,f,f,cfg)
        assert max(metrics.values())<1e-12;checks.append('independent_full_population_control')
        bad=pops.copy();bad[0,0,0,20]+=1e-5
        with gzip.open(out/'step1_post_collision.bin.gz','wb') as h:h.write(bad.astype('<f8').tobytes())
        metrics=population_step1(out,n,f,f,cfg)
        assert metrics['CH_collision']>1e-6 and metrics['CH_stream']>1e-6
        checks.append('detects_corrupted_collision_and_streaming')
        with gzip.open(out/'truncated.bin.gz','wb') as h:h.write(b'1234')
        detected=False
        try:binary(out/'truncated.bin.gz',n,16)
        except ValueError:detected=True
        assert detected;checks.append('detects_incomplete_binary')
    # Global phase-source balance is not a phase-invariance assertion.
    velocity=.01*grad(phi);source=np.sum(velocity*grad(phi),axis=0)
    b=W*(-2.5+1.5*np.sum(C*C,axis=1))
    delta=sum(v*np.roll(source,tuple(c),axis=(0,1,2)) for v,c in zip(b,C))
    assert abs(np.sum(delta,dtype=np.longdouble)+np.sum(source,dtype=np.longdouble))<1e-12
    assert abs(np.sum(delta))>1e-5;checks.append('nonzero_expected_source_change_not_hidden_as_leak')
    d=drift(['1','1.0000000002','1.0000000001']);assert d['step']==1 and d['max_abs']>abs(d['final'])
    checks.append('max_drift_includes_interior_peak')
    for c in PROTOCOL['stages']['alpha']:
        if c['kind']!='linear':continue
        mat,e,k,lh=matrix(c);seq=sequence(c);g=1-c['alpha']/6*lh*(c['a']+c['kappa']*lh)
        assert np.max(abs(seq-c['amplitude']/2*g**np.arange(c['steps']+1)))<1e-14
    checks.append('alpha_complete_19_population_vs_scalar_reference')
    # A half-force momentum ledger includes both force endpoints and raw cuts.
    oldJ,newJ=0.,.002;oldF,newF=.002,.004;oldcut,newcut=.00001,.00002;om=1.25
    newJ+=om*oldcut;oldP=oldJ+oldcut+oldF/2;newP=newJ+newcut+newF/2
    residual=newP-oldP-(oldF+newF)/2-om*oldcut-newcut+oldcut
    assert abs(residual)<1e-15;checks.append('physical_momentum_trapezoid_and_cut_identity')
    return dict(passed=True,checks=checks,count=len(checks),OpenLB_started=False)

if __name__=='__main__':print(json.dumps(main(),indent=2))
