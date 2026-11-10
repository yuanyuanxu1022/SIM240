#!/usr/bin/env python3
"""Independent static row and geometry verification; no generator import."""
from pathlib import Path
from fractions import Fraction
from itertools import combinations
import argparse
import csv
import json
import math
import hashlib

parser=argparse.ArgumentParser()
parser.add_argument('--data-dir',type=Path,default=Path(__file__).resolve().parent)
parser.add_argument('--project',type=Path)
args=parser.parse_args()
root=args.data_dir
read=lambda name:list(csv.DictReader((root/name).open(encoding='utf-8-sig')))
rows=read('candidate_cases.csv');optional=read('optional_cases.csv')
assert len(rows)==90 and len(optional)==20
assert sum(r['new_steady_solve_proposed']=='True' for r in rows)==60
ids=[r['planned_case_id'] for r in rows+optional];assert len(ids)==len(set(ids))
counts={role:sum(r['role']==role for r in rows) for role in {r['role'] for r in rows}}
assert counts=={'legacy_dev':30,'new_dev':16,'prediction_test':16,'regression':2,'smooth':6,'grid_reference':16,'linearity':4}
group=lambda r:(int(r['h_nm']),int(r['d_nm']),int(r['w_nm']))
development={group(r) for r in rows if r['role'] in ['legacy_dev','new_dev']}
tests={group(r) for r in rows if r['role']=='prediction_test'}
assert len(development)==23 and len(tests)==8 and not development&tests
key=lambda t:(Fraction(t[2],t[0]),Fraction(t[1],t[0]))
assert not {key(t) for t in development}&{key(t) for t in tests}
points=[(math.log(w/h),math.log(d/h)) for h,d,w in development]
orient=lambda a,b,c:(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
for h,d,w in tests:
    point=(math.log(w/h),math.log(d/h));inside=False
    for a,b,c in combinations(points,3):
        area=orient(a,b,c)
        if abs(area)<1e-12:continue
        weights=[orient(point,b,c)/area,orient(a,point,c)/area,orient(a,b,point)/area]
        if all(v>=-1e-10 for v in weights):inside=True;break
    assert inside,(h,d,w)
for r in rows+optional:
    h,d,w,P,ly,dx=[Fraction(r[n]) for n in ['h_nm','d_nm','w_nm','P_nm','Ly_nm','dx_nm']]
    assert P>w>0 and h>0 and d>=0
    assert all((s/dx).denominator==1 for s in [h,d,w,P,ly,(P-w)/2])
    nodes=(P*ly*h+w*ly*d)/(dx**3)
    assert nodes.denominator==1 and int(nodes)==int(r['fluid_nodes_expected'])
    assert abs(float(r['fluid_volume_nm3'])-float(nodes*dx**3))<1e-6
    dt=(float(r['tau'])-.5)*(float(dx)*1e-9)**2/(3*float(r['nu_m2_s']))
    assert abs(dt/float(r['dt_s'])-1)<1e-12
    assert r['actual_run_id']=='' and r['teacher_approved']=='False'
    if r['role'] in ['prediction_test','grid_reference','linearity','regression','smooth']:
        assert r['allowed_for_model_development']=='False'
    if r['role']!='optional_fixedP':assert P==2*w
    assert int(r['single_D3Q19_distribution_bytes'])==int(nodes)*19*8
source_checked=0
if args.project:
    for r in read('legacy_evidence.csv'):
        file=args.project/r['source_result']
        kv=dict(t.split('=',1) for t in file.read_text().splitlines() if '=' in t)
        assert hashlib.sha256(file.read_bytes()).hexdigest()==r['sha256']
        assert float(kv['Keff_m3'])==float(r['Keff_m3'])
        for f,n in [('mesa_gap_m','h_nm'),('groove_depth_m','d_nm'),('groove_width_m','w_nm')]:
            assert abs(float(kv[f])*1e9-float(r[n]))<1e-6
        source_checked+=1
result={'ok':True,'rows_checked':len(rows),'optional_rows_checked':len(optional),
        'new_steady_direction_rows':60,'legacy_raw_results_checked':source_checked,
        'prediction_geometries':8,'dimensionless_duplicates':0,
        'prediction_hull_check_method':'independent triangle barycentric enumeration',
        'all_grid_alignment_and_volume_checks_passed':True,
        'generator_imported':False,'OpenLB_precheck_executed':False,
        'simulation_run':False,'teacher_approved':False}
(root/'independent_design_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False))
