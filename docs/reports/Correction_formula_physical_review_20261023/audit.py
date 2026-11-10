"""Read-only C4/raw-data audit. No fitting, solver, or protocol changes."""
import csv
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / 'docs/reports/Correction_formula_derivation_20261023'
CASE = ROOT / 'CASE/D_series/D4_variable_groove_transport_20261023'
inputs = json.loads((OLD/'input_hashes.json').read_text())
for path in [OLD/'coefficients_and_domain.json', OLD/'recomputed36.csv',
             OLD/'DERIVATION.md', OLD/'dimensionless_correlation.py',
             CASE/'protocol/candidate_cases.csv', CASE/'development_stage_20261023/stage_cases.csv',
             CASE/'development_stage_20261023/PROTOCOL.md', CASE/'development_stage_20261023/release.json']:
    inputs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
assert all(Path(p).is_file() and hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in inputs.items())
params = json.loads((OLD/'coefficients_and_domain.json').read_text())

def model(alpha, beta, direction):
    a,b,c,q = params['coefficients'][direction]
    delta = math.exp(a+b*math.log(beta)+c*math.log(alpha)+q*math.log(alpha)**2)
    H=alpha+beta
    lc=(alpha**3+H**3)/24 if direction=='P' else alpha**3*H**3/(6*(alpha**3+H**3))
    slope_lc=(3*beta*H**2/(alpha**3+H**3) if direction=='P'
              else 3*beta*alpha**3/(H*(alpha**3+H**3)))
    return dict(K_over_w3=lc/(1+delta), K_over_flat=12*lc/(1+delta)/alpha**3,
                F=1/(1+delta), depth_log_slope=slope_lc-b*delta/(1+delta))

def inside(alpha,beta):
    return all(a*math.log(alpha)+b*math.log(beta)+c<=1e-12 for a,b,c in params['log_domain_halfspaces'])

def writecsv(name,rows):
    with (HERE/name).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

rows=list(csv.DictReader((OLD/'recomputed36.csv').open(encoding='utf-8-sig')))
points=[];pairs=[]
for r in rows:
    h,d,w=(float(r[k]) for k in ('h_nm','d_nm','w_nm'))
    # Direct original result, not the generated review's reported K.
    candidates=[Path(p) for p in inputs if p.endswith('/steady/result.txt')
                and Path(p).parent.parent.name in (f'h{h:g}_d{d:g}_dx5_{r["direction"]}', f'd{d:g}_h{h:g}_dx5_{r["direction"]}')]
    assert len(candidates)==1, (r['key'],candidates)
    raw=dict(line.split('=',1) for line in candidates[0].read_text().splitlines() if '=' in line)
    kval=float(raw['Keff_m3'])
    assert math.isclose(float(raw['mesa_gap_m'])*1e9,h,rel_tol=1e-14)
    assert math.isclose(float(raw['groove_depth_m'])*1e9,d,rel_tol=1e-14)
    assert math.isclose(float(raw['groove_width_m'])*1e9,w,rel_tol=1e-14)
    assert math.isclose(kval,float(r['K_raw_m3']),rel_tol=1e-14)
    m=model(h/w,d/w,r['direction'])
    points.append(dict(key=r['key'],direction=r['direction'],h_nm=h,d_nm=d,w_nm=w,
                       K_raw_m3=kval,K_C4_m3=m['K_over_w3']*(w*1e-9)**3,
                       depth_log_slope=m['depth_log_slope'],inside_old_hull=inside(h/w,d/w),source=str(candidates[0])))
for direction in ('P','T'):
    for h in sorted({p['h_nm'] for p in points}):
        group=sorted([p for p in points if p['direction']==direction and p['h_nm']==h],key=lambda p:p['d_nm'])
        for x,y in zip(group,group[1:]):
            pairs.append(dict(direction=direction,h_nm=h,d1_nm=x['d_nm'],d2_nm=y['d_nm'],
                              raw_change_percent=100*(y['K_raw_m3']/x['K_raw_m3']-1),
                              C4_change_percent=100*(y['K_C4_m3']/x['K_C4_m3']-1)))
writecsv('point_checks.csv',points);writecsv('depth_pairs.csv',pairs)

scan={};fd_error=0.0
for label in ('old_log_hull','proposed_core_rectangle'):
    data=[]
    for j in range(241):
        for k in range(241):
            if label=='old_log_hull':
                al=math.exp(math.log(5/24)+j/240*math.log(5));be=math.exp(math.log(5/24)+k/240*math.log(24/5))
                if not inside(al,be):continue
            else:
                s=.8*4**(j/240);t=(1/3)*4.8**(k/240);al=1/s;be=t/s
            pp=model(al,be,'P');tt=model(al,be,'T')
            data.append((al,be,pp,tt))
    result={'geometry_points':len(data),'direction_evaluations':2*len(data),
            'P_less_than_T_count':sum(p['K_over_w3']<t['K_over_w3']-1e-12 for a,b,p,t in data)}
    for direction,index in [('P',2),('T',3)]:
        bad=[x for x in data if x[index]['depth_log_slope'] < -1e-10]
        worst=min(data,key=lambda x:x[index]['depth_log_slope'])
        result[direction]={'negative_depth_slope_count':len(bad),
                           'lower_bound_violation_count':sum(x[index]['K_over_flat']<1-1e-12 for x in data),
                           'worst_depth_log_slope':worst[index]['depth_log_slope'],
                           'worst_alpha_beta':list(worst[:2])}
        # Finite-difference cross-check on a sparse subset; this tests differentiation, not physical accuracy.
        for al,be,*_ in data[::251]:
            eps=1e-5
            numerical=(math.log(model(al,be*math.exp(eps),direction)['K_over_w3'])-
                       math.log(model(al,be*math.exp(-eps),direction)['K_over_w3']))/(2*eps)
            fd_error=max(fd_error,abs(numerical-model(al,be,direction)['depth_log_slope']))
    scan[label]=result

plans=list(csv.DictReader((CASE/'protocol/candidate_cases.csv').open(encoding='utf-8-sig')))
target=[];seen=set()
for row in plans:
    if row['role'] not in ('new_dev','prediction_test'):continue
    w,h,d=(float(row[k]) for k in ('w_nm','h_nm','d_nm'))
    key=(row['role'],w,h,d)
    if key in seen:continue
    seen.add(key);s=w/h;t=d/h
    target.append(dict(role=row['role'],w_nm=w,h_nm=h,d_nm=d,P_nm=2*w,s_w_over_h=s,t_d_over_h=t,
                       beta_d_over_w=d/w,inside_old_hull=inside(h/w,d/w),
                       inside_proposed_core=(.8-1e-12<=s<=3.2+1e-12 and 1/3-1e-12<=t<=1.6+1e-12),
                       directions='P;T',status='planned geometry only; not a run or authorization',
                       C4_T_depth_log_slope=model(h/w,d/w,'T')['depth_log_slope']))
writecsv('validation_ratio_matrix.csv',target)

summary={'scope':'physical-domain algebra and existing raw-data audit; no solver or refit',
         'protected_input_count':len(inputs),'input_mismatches':[],
         'raw_points':len(points),'analytic_derivative_finite_difference_max_abs_error':fd_error,
         'negative_depth_slope_threshold':-1e-10,
         'negative_slope_sample_points':{i:sum(p['direction']==i and p['depth_log_slope'] < -1e-10 for p in points) for i in ('P','T')},
         'depth_pairs':{i:{'total':sum(p['direction']==i for p in pairs),
                           'raw_decreasing':sum(p['direction']==i and p['raw_change_percent'] < -1e-8 for p in pairs),
                           'C4_decreasing':sum(p['direction']==i and p['C4_change_percent'] < -1e-8 for p in pairs)} for i in ('P','T')},
         'scans':scan,'target_domain':{'s_w_over_h':[.8,3.2],'t_d_over_h':[1/3,1.6],'phi':.5,'P_rule':'2w','status':'proposed validation domain, not validated applicability'},
         'new_dev_geometries':sum(r['role']=='new_dev' for r in target),
         'prediction_geometries':sum(r['role']=='prediction_test' for r in target),
         'all_planned_geometries_inside_target':all(r['inside_proposed_core'] for r in target),
         'core_conclusion':'C4_T violates depth monotonicity inside old hull; do not lock as a physical prediction model',
         'asymptotic_exponents':{'C4_P_deep_d':3-params['coefficients']['P'][1],'expected_P_deep_d':1,
                                 'C4_T_deep_d':-params['coefficients']['T'][1]},
         'new_run_id':None,'model_lock_created':False}
assert fd_error<1e-8
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in inputs.items())
(HERE/'input_hashes.json').write_text(json.dumps(inputs,indent=2,ensure_ascii=False)+'\n')
(HERE/'checks.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(summary,indent=2,ensure_ascii=False))
