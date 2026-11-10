#!/usr/bin/env python3
"""Independent readback of zero-step diagnostics. Never awards a physical gate."""
import csv
import json
import math
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent

def kv(p):
    return dict(line.split('=',1) for line in p.read_text().splitlines() if '=' in line)

def fit_circle(path, wall=None):
    rows=list(csv.DictReader(path.open()))
    rings={}
    for r in rows:
        y=float(r['y_lu'])
        if wall is not None and y < wall+8:
            continue  # exclude 2 interface widths next to the wall
        rings.setdefault(y,[]).append((float(r['x_lu']),float(r['phi'])-.5))
    pts=[]
    for y, line in rings.items():
        line.sort()
        for (x,a),(xx,b) in zip(line,line[1:]):
            if a*b<0:
                pts.append((x+(xx-x)*(-a)/(b-a),y))
            elif a==0:
                pts.append((x,y))
    xy=np.array(pts)
    a=np.column_stack((2*xy[:,0],2*xy[:,1],np.ones(len(xy))))
    xc,yc,c=np.linalg.lstsq(a,(xy**2).sum(axis=1),rcond=None)[0]
    radius=math.sqrt(c+xc*xc+yc*yc)
    err=float(np.sqrt(np.mean((np.sqrt(((xy-[xc,yc])**2).sum(axis=1))-radius)**2)))
    out=dict(center=[float(xc),float(yc)],radius_lattice=radius,
             radial_rms_lattice=err,contour_points=len(pts))
    if wall is not None:
        out['angle_degrees_liquid_side']=math.degrees(math.acos((wall-yc)/radius))
    return out

def main():
    out={'scope':'zero-step initialization only; no collideAndStream', 'runs':{}}
    for code,mode in [('lp','laplace'),('ca','contact'),('fl','flat_liquid'),('fg','flat_gas')]:
        rid=f'target_{code}_init_20261021_v4'
        run=HERE/'output'/rid
        record=HERE/'evidence'/rid
        ec=int((record/'exit_code.txt').read_text())
        assert ec==0, (mode,ec)
        result=kv(run/'result.txt'); geo=kv(run/'geometry_audit.txt')
        rows=list(csv.DictReader((run/'history.csv').open()))
        assert len(rows)==1 and int(rows[0]['step'])==0
        assert result['RESULT_PASS']=='NOT_EVALUATED'
        assert geo['bad_ns_or_ch_links']=='0' and geo['fallback_predicate_count']=='0'
        row={k:float(v) for k,v in rows[0].items()}
        assert row['rho_min']>0 and row['rho_mapping_error']<1e-10 and row['tau_mapping_error']<1e-10
        summary=dict(run_id=rid,independent_exit_code=ec,geometry=geo,
                     min_rho=row['rho_min'],max_rho=row['rho_max'],
                     rho_mapping_error=row['rho_mapping_error'],tau_mapping_error=row['tau_mapping_error'],
                     max_Mach=row['max_Mach'],initial_max_u_m_s=row['max_u_m_s'])
        if code in ['lp','ca']:
            summary['initial_contour_fit']=fit_circle(run/'slice_initial.csv',float(geo['wall_lower_lattice']) if code=='ca' else None)
            assert abs(summary['initial_contour_fit']['radius_lattice']-(18 if code=='ca' else 16))<.1
        else:
            target=1. if code=='fl' else .0012
            assert abs(row['rho_min']-target)<1e-12 and abs(row['rho_max']-target)<1e-12
        out['runs'][mode]=summary
    out.update(initialization_checks_pass=True, NUMERICAL_GATE='NOT_EVALUATED',
               RESULT_PASS='NOT_EVALUATED',geometry_PASS='NOT_EVALUATED',
               dynamic_stability='NOT_TESTED',formal_validation_released=False)
    (HERE/'evidence/preparation_checks.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':
    main()
