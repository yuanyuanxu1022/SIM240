#!/usr/bin/env python3
"""Offline, fixed-window descriptive analysis. Never starts a solver or awards a gate."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
PRESSURES=['p_h_inside_minus_outside_Pa','p_bulk_candidate_inside_minus_outside_Pa']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def window_metrics(steps,values):
    mean=float(np.mean(values));span=float(np.ptp(values))
    slope=float(np.polyfit(steps-steps[0],values,1)[0])
    change=slope*float(steps[-1]-steps[0])
    return dict(first_step=int(steps[0]),last_step=int(steps[-1]),count=len(steps),
                mean_Pa=mean,peak_to_peak_Pa=span,standard_deviation_Pa=float(np.std(values)),
                peak_to_peak_over_abs_mean=span/abs(mean) if abs(mean)>1e-12 else None,
                slope_Pa_per_step=slope,fitted_window_change_Pa=change,
                fitted_change_over_abs_mean=change/abs(mean) if abs(mean)>1e-12 else None)

def describe_pressure(steps,values):
    report={'windows':{}}
    for lo,hi in [(1501,2000),(1751,2000),(1501,1750)]:
        use=(steps>=lo)&(steps<=hi)
        report['windows'][f'{lo}_{hi}']=window_metrics(steps[use],values[use])
    report['mean_difference_last250_vs_last500_Pa']=(
        report['windows']['1751_2000']['mean_Pa']-report['windows']['1501_2000']['mean_Pa'])
    report['adjacent_half_mean_difference_Pa']=(
        report['windows']['1751_2000']['mean_Pa']-report['windows']['1501_1750']['mean_Pa'])
    peaks=np.array([i for i in range(1,len(values)-1) if values[i]>values[i-1] and values[i]>values[i+1]],dtype=int)
    troughs=np.array([i for i in range(1,len(values)-1) if values[i]<values[i-1] and values[i]<values[i+1]],dtype=int)
    report['envelope_diagnostics']=[]
    for lo in [1,1001]:
        pt=[i for i in peaks if steps[i]>=lo]
        ts=[];amp=[]
        for i in pt:
            left=troughs[(troughs<i)&(steps[troughs]>=lo)];right=troughs[troughs>i]
            if len(left) and len(right):
                j,k=left[-1],right[0]
                baseline=values[j]+(values[k]-values[j])*(steps[i]-steps[j])/(steps[k]-steps[j])
                a=(values[i]-baseline)/2
                if a>0:ts.append(float(steps[i]));amp.append(float(a))
        fit=dict(start_step=lo,peak_count=len(pt),envelope_points=len(ts),
                 median_peak_interval_steps=float(np.median(np.diff(steps[pt]))) if len(pt)>1 else None,
                 positive_decay_tau_steps=None,log_envelope_slope=None,
                 status='descriptive_only_not_mode_identification_or_confidence_interval')
        if len(ts)>=3:
            slope=float(np.polyfit(ts,np.log(amp),1)[0]);fit['log_envelope_slope']=slope
            if slope<0:fit['positive_decay_tau_steps']=-1/slope
        report['envelope_diagnostics'].append(fit)
    return report

def read_slice(path):
    a=np.genfromtxt(path,delimiter=',',names=True)
    lines={}
    for row in a:lines.setdefault(float(row['y_lu']),[]).append((float(row['x_lu']),float(row['phi'])-.5))
    points=[]
    for y,line in lines.items():
        line.sort()
        for (x,v),(xx,vv) in zip(line,line[1:]):
            if v*vv<0:points.append((x+(xx-x)*(-v)/(vv-v),y))
            elif v==0:points.append((x,y))
    w=1-a['phi'];area=float(w.sum())
    result=dict(weighted_area_lu2=area,weighted_area_radius_lu=math.sqrt(area/math.pi) if area>0 else None,
                contour_fit=None,chemical_potential_slice={},bulk_mask_counts={})
    if len(points)>=6:
        xy=np.array(points);matrix=np.column_stack([2*xy[:,0],2*xy[:,1],np.ones(len(xy))])
        xc,yc,c=np.linalg.lstsq(matrix,(xy**2).sum(axis=1),rcond=None)[0]
        rsq=c+xc**2+yc**2
        if rsq>0:
            radius=math.sqrt(rsq)
            result['contour_fit']=dict(center_lu=[float(xc),float(yc)],radius_lu=radius,
                radial_rms_lu=float(np.sqrt(np.mean((np.linalg.norm(xy-[xc,yc],axis=1)-radius)**2))),points=len(points))
    for label,use in [('liquid',a['phi']<.01),('gas',a['phi']>.99)]:
        result['bulk_mask_counts'][label]=int(use.sum())
        v=a['chemical_potential_lu'][use]
        result['chemical_potential_slice'][label]=dict(mean_lu=float(v.mean()),range_lu=float(np.ptp(v)),std_lu=float(v.std())) if len(v) else None
    return result

def analyze(run,record):
    protocol=json.loads((HERE/'protocol.json').read_text())
    a=np.genfromtxt(run/'history.csv',delimiter=',',names=True)
    if len(a)!=2001 or not np.array_equal(a['step'],np.arange(2001)):
        raise ValueError('fixed tail analysis requires complete steps 0..2000; preserve partial run for failure review')
    manifest=json.loads((record/'manifest.json').read_text());ec=int((record/'exit_code.txt').read_text())
    if manifest['run_id']!=protocol['run_id'] or manifest['protocol_id']!=protocol['protocol_id']:
        raise ValueError('wrong run/protocol identity')
    if ec!=0 or manifest.get('independent_exit_code')!=0 or not manifest.get('source_hashes_unchanged'):
        raise ValueError('nonzero exit or failed recorded provenance; independent failure review required')
    files=[run/'history.csv',record/'manifest.json',record/'exit_code.txt',HERE/'protocol.json']+sorted(run.glob('slice_*.csv'))
    before={str(p):sha(p) for p in files}
    out=dict(run_id=protocol['run_id'],protocol_id=protocol['protocol_id'],independent_exit_code=ec,
             records=len(a),whole_run={},pressure={},shape_snapshots={},pressure_convergence='REQUIRES_REVIEW',
             NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS='NOT_EVALUATED',geometry_PASS='NOT_EVALUATED')
    for raw,col in [('liquid_amount_lu3','liquid_drift'),('total_mass_lu','total_mass_drift')]:
        values=(a[raw]-a[raw][0])/a[raw][0]
        if not np.allclose(values,a[col],rtol=1e-10,atol=1e-14):raise ValueError('drift ledger mismatch: '+col)
        i=int(np.argmax(abs(values)))
        out['whole_run'][col]=dict(max_absolute=float(abs(values[i])),at_step=i,final=float(values[-1]),
                                  below_inherited_candidate_1e_minus3=bool(np.max(abs(values))<=.001))
    out['whole_run'].update(all_finite=bool(np.all(a['finite']==1)),rho_min=float(np.min(a['rho_min'])),
                           phi_min=float(np.min(a['phi_min'])),phi_max=float(np.max(a['phi_max'])),
                           max_Mach=float(np.max(a['max_Mach'])),max_u_m_s=float(np.max(a['max_u_m_s'])),
                           rho_mapping_error_max=float(np.max(a['rho_mapping_error'])),tau_mapping_error_max=float(np.max(a['tau_mapping_error'])))
    for col in PRESSURES:out['pressure'][col]=describe_pressure(a['step'],a[col])
    for step in protocol['midplane_snapshot_steps']:
        file=run/('slice_initial.csv' if step==0 else f'slice_step_{step}.csv')
        out['shape_snapshots'][str(step)]=read_slice(file)
    rv=float((3*a['liquid_amount_lu3'][-1]/(4*np.pi))**(1/3))
    rc=out['shape_snapshots']['2000']['contour_fit']
    out['reference_only']=dict(volume_equivalent_radius_lu=rv,volume_based_pressure_Pa=.06/(rv*2.5e-9),
                                contour_based_pressure_Pa=.06/(rc['radius_lu']*2.5e-9) if rc else None,
                                note='not an acceptance target; curvature and mechanical-pressure conventions require review')
    if not all(sha(Path(p))==h for p,h in before.items()):raise ValueError('input changed during analysis')
    out['input_sha256']=before
    return out

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    rid=json.loads((HERE/'protocol.json').read_text())['run_id']
    if args.output.exists():raise ValueError('refusing to overwrite analysis output')
    result=analyze(HERE/'output'/rid,HERE/'evidence'/rid)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ['run_id','records','pressure_convergence','NUMERICAL_GATE','RESULT_PASS','geometry_PASS']}))

if __name__=='__main__':main()
