#!/usr/bin/env python3
"""Existing C4 correlation, explicit in w/h/d. No fit, solver, or final model lock."""
from pathlib import Path
import json,math
PARAMS=json.loads(Path(__file__).with_name('coefficients_and_domain.json').read_text())
def inside_sample_envelope(w,h,d,tolerance=1e-12):
    if min(w,h,d)<=0:return False
    x,z=math.log(h/w),math.log(d/w)
    return all(a*x+b*z+c<=tolerance for a,b,c in PARAMS['log_domain_halfspaces'])
def predict(w,h,d,direction='P',unit='nm',allow_extrapolation=False):
    """Positive lengths in same unit. Returns K [m^3] and dimensionless corrections.

    Domain membership is an interpolation-screen, not an accuracy certificate.
    The phi=0.5, P=2w family is fixed; changing phi needs a new model.
    """
    if not all(math.isfinite(v) for v in [w,h,d]) or w<=0 or h<=0 or d<0:raise ValueError('finite w,h>0 and d>=0 required')
    if direction not in ['P','T']:raise ValueError('P=along grooves, T=across grooves')
    if unit not in ['m','nm']:raise ValueError('unit must be m or nm')
    factor=1. if unit=='m' else 1e-9
    if d==0:
        K=(h*factor)**3/12
        return {'K_m3':K,'K_LC_m3':K,'F_mobility':1.,'C_resistance':1.,'Delta_excess':0.,'inside_sample_envelope':False,'status':'exact flat-gap limit of continuum model'}
    inside=inside_sample_envelope(w,h,d)
    if not inside and not allow_extrapolation:raise ValueError('outside sampled log-ratio envelope; no validated extrapolation')
    a,b,c,q=PARAMS['coefficients'][direction]
    s,t=w/h,d/h
    g=a+b*math.log(t)-(b+c)*math.log(s)+q*math.log(s)**2
    Delta=math.exp(g);F=1/(1+Delta)
    K0=(((h*factor)**3+((h+d)*factor)**3)/24 if direction=='P'
         else 1/(6*((h*factor)**-3+((h+d)*factor)**-3)))
    return {'K_m3':K0*F,'K_LC_m3':K0,'F_mobility':F,'C_resistance':1+Delta,'Delta_excess':Delta,
        'inside_sample_envelope':inside,'status':'existing retrospective C4 candidate; new-width transfer not independently validated'}
if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--w',type=float,required=True);ap.add_argument('--h',type=float,required=True);ap.add_argument('--d',type=float,required=True)
    ap.add_argument('--direction',choices=['P','T'],required=True);ap.add_argument('--unit',choices=['nm','m'],default='nm');a=ap.parse_args()
    print(json.dumps(predict(a.w,a.h,a.d,a.direction,a.unit),ensure_ascii=False,indent=2))
