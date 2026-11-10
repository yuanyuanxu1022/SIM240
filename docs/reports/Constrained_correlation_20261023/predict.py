"""Evaluate a candidate closure; accuracy at new widths is not independently validated."""
from pathlib import Path
import argparse,json,math
from models import normalized,gains

def predict(w,h,d,model='G4',unit='nm',allow_extrapolation=False):
    if not all(math.isfinite(x) for x in (w,h,d)) or min(w,h)<=0 or d<0:
        raise ValueError('finite w,h>0 and d>=0 required')
    if model not in ('G4','G6') or unit not in ('nm','m'):raise ValueError('G4/G6 and nm/m only')
    s,t=w/h,d/h
    inside=.8-1e-12<=s<=3.2+1e-12 and 1/3-1e-12<=t<=1.6+1e-12
    if d and not inside and not allow_extrapolation:
        raise ValueError('outside proposed target rectangle; use explicit diagnostic extrapolation only')
    fit=json.loads(Path(__file__).with_name('fits.json').read_text())[model]
    flat=(h*(1e-9 if unit=='nm' else 1))**3/12;cp,ct=gains(s,t)
    result={'model':model,'phi':.5,'period_in_input_unit':2*w,'input_unit':unit,'s_w_over_h':s,'t_d_over_h':t,
            'inside_proposed_target':inside,'status':'retrospective candidate, not independently validated accuracy; not final model lock'}
    for dr,c in [('P',cp),('T',ct)]:
        kn=float(normalized(s,t,fit,dr));f=kn/(1+float(c))
        result[dr]={'K_m3':flat*kn,'K_over_flat':kn,'F_mobility':f,'C_resistance':1/f}
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--w',type=float,required=True);ap.add_argument('--h',type=float,required=True);ap.add_argument('--d',type=float,required=True)
    ap.add_argument('--model',choices=['G4','G6'],default='G4');ap.add_argument('--unit',choices=['nm','m'],default='nm');ap.add_argument('--allow-extrapolation',action='store_true')
    args=ap.parse_args();print(json.dumps(predict(args.w,args.h,args.d,args.model,args.unit,args.allow_extrapolation),indent=2))
