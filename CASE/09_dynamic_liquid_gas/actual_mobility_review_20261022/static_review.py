#!/usr/bin/env python3
"""Static D3Q19 spectral/initial-array audit. No time integration or OpenLB call.

The eigenproblem linearizes f0=beta*phi**2*(1-phi)**2 in a uniform
bulk. It is not a curved-interface, nonlinear or full NS/CH validation.
"""
from pathlib import Path
import csv
import hashlib
import itertools
import json
import math
from decimal import Decimal, localcontext
import numpy as np

HERE = Path(__file__).resolve().parent
C = np.array([(0, 0, 0)] + [v for v in itertools.product((-1, 0, 1), repeat=3)
                          if sum(x*x for x in v) in (1, 2)], dtype=int)
W = np.array([1/3 if np.dot(v,v)==0 else 1/18 if np.dot(v,v)==1 else 1/36 for v in C])
assert len(C)==19 and np.isclose(W.sum(), 1)
assert np.allclose(np.einsum('i,ij,ik->jk', W, C, C), np.eye(3)/3)
RHO, NU, SIGMA, WIDTH, LENGTH = 1000., 1e-5, .03, 10e-9, 160e-9
M_SI = (1/6)*(2.5e-9)**2/(6*NU)/RHO


def mapping(dx_nm, route):
    dx = dx_nm*1e-9
    dt = dx*dx/(6*NU)
    factor = (2.5/dx_nm)**2
    tau, alpha = {'tau_growth': (.5+.5*factor, 1.),
                  'alpha_growth': (1., factor),
                  'unchanged_CH_changes_M': (1., 1.)}[route]
    sigma = SIGMA*dt*dt/(RHO*dx**3)
    width = WIDTH/dx
    return dict(dx_nm=dx_nm, dt_s=dt, tau_CH=tau, alpha=alpha,
                sigma_lu=sigma, W_nodes=width, beta_lu=12*sigma/width,
                kappa_lu=1.5*sigma*width,
                M_SI=(tau-.5)*alpha/3*dt/RHO,
                tau_NS_liquid=1., tau_NS_gas=1.25)


def eigen_rate(k, tau, alpha, a, kappa):
    lam_h = float(np.sum(6*W*(1-np.cos(C@k))))
    ak = alpha*(a+kappa*lam_h)
    e = W*ak
    e[0] += 1-ak
    omega = 1/tau
    matrix = np.exp(-1j*(C@k))[:,None]*((1-omega)*np.eye(19)+omega*e[:,None])
    eig = np.linalg.eigvals(matrix)
    value = eig[np.argmin(abs(eig-1))]
    return -np.log(abs(value)), value, lam_h, float(np.max(abs(eig)))


def spatial_operators(phi):
    lap = np.zeros_like(phi)
    grad = np.zeros(phi.shape+(3,))
    for ci, wi in zip(C, W):
        neighbor = np.roll(phi, tuple(-ci), axis=(0,1,2))
        lap += 6*wi*(neighbor-phi)
        grad += neighbor[...,None]*(3*wi*ci)
    return lap, grad


def axial_decimal_check(p, mode):
    """Independent three-velocity-group secular equation, 60-digit root.

    Transverse velocities aggregate to x velocities 0,+1,-1; the equilibrium
    coefficients are 1-A/3,A/6,A/6. Decimal protects 1-lambda cancellation.
    Trigonometric inputs originate in double precision, not arbitrary-precision cos.
    """
    with localcontext() as ctx:
        ctx.prec=60
        D=lambda v: Decimal(str(v))
        q=2*np.pi*mode*(p['dx_nm']*1e-9)/LENGTH
        cq=D(math.cos(q));lh=2*(1-cq)
        tau=D(p['tau_CH']);omega=1/tau;r=1-omega
        a=2*D(p['beta_lu']);kap=D(p['kappa_lu']);alpha=D(p['alpha'])
        ak=alpha*(a+kap*lh);e0=1-ak/3;b=ak/3
        v=Decimal(1)
        for _ in range(25):
            den=v*v-2*v*r*cq+r*r
            f=omega*(e0/(v-r)+b*(v*cq-r)/den)-1
            fp=omega*(-e0/(v-r)**2+b*(cq*den-(v*cq-r)*(2*v-2*r*cq))/den**2)
            v-=f/fp
        ce=(tau-D('.5'))*alpha/3*D(q)**2*(a+kap*D(q)**2)
        return float(100*(-v.ln()/ce-1))


def initial_arrays(n, length_nm=160.):
    p = mapping(length_nm/n, 'alpha_growth')
    dx_nm = length_nm/n
    x,y,z = np.meshgrid(*[np.arange(n)*dx_nm]*3, indexing='ij')
    corr = np.sin(2*np.pi*y/length_nm+.37)*np.cos(2*np.pi*z/length_nm+.19)+.25*np.cos(4*np.pi*y/length_nm+.23)
    # Offset fixes discrete initial amount, never a runtime normalization.
    lo, hi = length_nm/4-5,length_nm/4+5
    for _ in range(60):
        a0=(lo+hi)/2
        phi=.5*(1+np.tanh(2*(abs(x-length_nm/2)-(a0+corr))/10))
        if phi.mean()>.5: lo=a0
        else: hi=a0
    lap, _ = spatial_operators(phi)
    mu=4*p['beta_lu']*phi*(phi-1)*(phi-.5)-p['kappa_lu']*lap
    _, gm=spatial_operators(mu)
    force=-phi[...,None]*gm
    rho=1-.9988*phi
    u=force/(2*rho[...,None])
    return dict(N=n, length_nm=length_nm, dx_nm=dx_nm, a0_nm=a0, corrugation_primary_amplitude_nm=1.,
                phi_mean=float(phi.mean()), phi_min=float(phi.min()), phi_max=float(phi.max()),
                rho_min_kg_m3=float(rho.min()*RHO), rho_max_kg_m3=float(rho.max()*RHO),
                gas_core_density_offset_relative_to_1p2=float(rho.min()*RHO/1.2-1),
                mu_max_abs_lu=float(abs(mu).max()),
                capillary_force_max_norm_lu=float(np.linalg.norm(force,axis=-1).max()),
                initial_half_force_Mach_max=float(np.linalg.norm(u,axis=-1).max()*np.sqrt(3)),
                capillary_force_sum_lu=force.sum(axis=(0,1,2)).tolist(),
                static_only=True)


def main():
    rows=[]; scalar_errors=[]; weak_errors=[]; decimal_checks=[]
    modes=[(1,0,0),(0,1,0),(0,0,1),(2,0,0),(3,0,0),(4,0,0),
           (8,0,0),(16,0,0),(1,1,0),(1,1,1),(2,2,1)]
    maps=[]
    for route in ('tau_growth','alpha_growth','unchanged_CH_changes_M'):
      for dx_nm in (2.5,1.25,.625):
        p=mapping(dx_nm,route)
        for phi0 in (0.,.1,.5,.9,1.):
          a=p['beta_lu']*(12*phi0*phi0-12*phi0+2)
          for mode in modes:
            k=2*np.pi*np.array(mode)*(dx_nm*1e-9)/LENGTH
            rate,eig,lh,spectral_radius=eigen_rate(k,p['tau_CH'],p['alpha'],a,p['kappa_lu'])
            k2=float(k@k)
            ce=(p['tau_CH']-.5)*p['alpha']/3*k2*(a+p['kappa_lu']*k2)
            rows.append(dict(route=route,dx_nm=dx_nm,phi0=phi0,mode=str(mode),
                             tau_CH=p['tau_CH'],alpha=p['alpha'],
                             lambda_real=float(eig.real),lambda_imag=float(eig.imag),
                             Lambda=lh,rate_lu=float(rate),rate_SI_s_inv=float(rate/p['dt_s']),
                             continuum_rate_lu=ce,signed_rate_bias_percent=float(100*(rate/ce-1)),
                             spectrum_max_abs=spectral_radius,
                             continuum_growth_expected=bool(ce<0)))
            if p['tau_CH']==1:
                exact=1-p['alpha']/6*lh*(a+p['kappa_lu']*lh)
                scalar_errors.append(abs(eig-exact))
        # Stable endpoints: Lambda <=16/3, positive free-energy curvature.
        lhmax=16/3
        p['bulk_tau1_g_min_if_applicable']=1-p['alpha']/6*lhmax*(2*p['beta_lu']+p['kappa_lu']*lhmax) if p['tau_CH']==1 else None
        maps.append(dict(route=route,**p))
        if route!='unchanged_CH_changes_M':
            for mode in (1,4,8):
                bias=axial_decimal_check(p,mode)
                row=next(v for v in rows if v['route']==route and v['dx_nm']==dx_nm and v['phi0']==0 and v['mode']==str((mode,0,0)))
                decimal_checks.append(dict(route=route,dx_nm=dx_nm,mode=mode,
                    high_precision_bias_percent=bias,
                    double_difference_percentage_points=abs(bias-row['signed_rate_bias_percent'])))
    # Independent weak-chemical-potential axial asymptotic check at tau=2.5.
    for q in (.1,.3,.7):
        tau=2.5; omega=1/tau;r=1-omega
        factor=omega**2/(omega**2+2*r*(1-np.cos(q)))
        ak=1e-6
        rate,_,lh,_=eigen_rate(np.array([q,0.,0.]),tau,1.,ak,0.)
        observed=rate/((tau-.5)/3*ak*lh)
        weak_errors.append(abs(observed/factor-1))
    assert max(scalar_errors)<1e-13
    assert max(weak_errors)<2e-5
    assert max(v['double_difference_percentage_points'] for v in decimal_checks)<2e-5
    for p in maps:
        if p['route']!='unchanged_CH_changes_M': assert math.isclose(p['M_SI'],M_SI,rel_tol=1e-14)
    with (HERE/'spectral_rates.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    report=dict(status='STATIC_ANALYSIS_ONLY_NOT_SOLVER_VALIDATION',solver_started=False,
                physical_M_main=M_SI, mappings=maps,
                tau1_scalar_crosscheck_max_abs=float(max(scalar_errors)),
                weak_A_axial_factor_crosscheck_max_relative=float(max(weak_errors)),
                independent_axial_decimal_checks=decimal_checks,
                initial_arrays=[initial_arrays(32,80.),initial_arrays(64)],
                beta_SI_Pa=12*SIGMA/WIDTH,kappa_SI_Pa_m2=1.5*SIGMA*WIDTH,
                rows=len(rows), script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (HERE/'static_results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='mappings'},indent=2))


if __name__=='__main__': main()
