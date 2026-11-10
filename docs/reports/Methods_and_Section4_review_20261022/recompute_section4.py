#!/usr/bin/env python3
"""Read existing raw results; recompute Section 4 without fitting or simulation.

The run index supplies paths only. Geometry, physics, J and K come from each
raw result.txt. Saved K is checked against nu*J/a; missing nu is reconstructed
from the recorded tau, dx and dt. This checks conversion consistency only.
This is a manuscript-number audit, not independent solver validation.
"""
import csv
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INDEX = ROOT / 'docs/reports/第一篇_run_id索引_20261022.csv'
inputs = {}


def bind(path):
    data = path.read_bytes()
    inputs[str(path.relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
    return data.decode('utf-8')


def closure(h, d, direction):
    a, b = h**3, (h+d)**3
    return ((a+b)/24 if direction == 'parallel' else a*b/(6*(a+b)))*1e-27


def factor(d, direction):
    a, b = (1.7685, 1.6331) if direction == 'parallel' else (.4900, .6990)
    return 1/(1+a*(d/120)**b)


rows = list(csv.DictReader(bind(INDEX).splitlines()))
assert len(rows) == 52
main, fine, controls, oblique = {}, {}, [], []
for row in rows:
    path = ROOT / row['rel_path'] / 'steady/result.txt'
    data = dict(line.split('=', 1) for line in bind(path).splitlines() if '=' in line)
    h = round(float(data['mesa_gap_m'])*1e9)
    d = round(float(data['groove_depth_m'])*1e9)
    dx = round(float(data['dx_m'])*1e9, 8)
    assert math.isclose(dx, float(row['dx_nm']), abs_tol=1e-7)
    assert row['geometry'] == f'h={h},d={d}'
    if row['direction'].startswith('oblique'):
        theta = float(row['direction'].split('-')[1].replace('deg', ''))
        nu = ((float(data['tau'])-.5)*float(data['dx_m'])**2 /
              (3*float(data['dt_s'])))
        assert math.isclose(float(data['direction'].replace('angle','')), theta)
        oblique.append(dict(run_id=row['run_id'], h=h, d=d, theta_deg=theta,
                            G_over_mu=float(data['acceleration_m_s2'])/nu,
                            J=list(map(float, data['J_vector_m2_s'].split(',')))))
        continue
    direction = row['direction']
    assert direction == data['direction']
    K = float(data['Keff_m3'])
    nu = ((float(data['tau'])-.5)*float(data['dx_m'])**2 /
          (3*float(data['dt_s'])))
    if 'nu_phys_m2_s' in data:
        assert math.isclose(nu, float(data['nu_phys_m2_s']), rel_tol=2e-15)
    K_recomputed = nu*float(data['J_main_m2_s'])/float(data['acceleration_m_s2'])
    assert math.isclose(K, K_recomputed, rel_tol=2e-15)
    Km = closure(h, d, direction)
    rec = dict(run_id=row['run_id'], path=str(path.relative_to(ROOT)), h=h, d=d,
               dx=dx, direction=direction, K=K, K_from_J=K_recomputed,
               Kmod=Km, E_percent=100*(Km/K-1),
               F=factor(d, direction), residual_percent=100*(factor(d, direction)*Km/K-1),
               q_min=float(data['q_min']), q_max=float(data['q_max']),
               Mach=float(data['max_Mach']),
               mu=float(data['mu_phys_Pa_s']) if 'mu_phys_Pa_s' in data else None,
               nu_from_recorded_conversion=nu)
    if row['run_id'].startswith('mu15'):
        controls.append(rec)
    elif dx == 5:
        assert math.isclose(nu, 1e-6)
        assert (h, d, direction) not in main
        main[h, d, direction] = rec
    else:
        assert dx == 2.5
        fine[h, d, direction] = rec

expected = {(h, d, direction) for h in (25, 50, 75, 125)
            for d in ((25, 50, 100) if h == 25 else (25, 50, 75, 100, 120))
            for direction in ('parallel', 'perpendicular')}
assert set(main) == expected
assert len(fine) == 8 and len(controls) == 2 and len(oblique) == 6
assert all(r['q_min'] == r['q_max'] == .5 for r in [*main.values(), *fine.values(), *controls])

table5 = []
for h in (50, 75, 125):
    p = main[h, 120, 'parallel']['K']/main[h, 25, 'parallel']['K']
    t = main[h, 120, 'perpendicular']['K']/main[h, 25, 'perpendicular']['K']
    table5.append(dict(h=h, parallel_ratio=p, perpendicular_ratio=t,
                       parallel_increase_percent=100*(p-1), perpendicular_increase_percent=100*(t-1)))
thin = [r for r in main.values() if r['h'] == 25 and r['direction'] == 'perpendicular']
thin_ratio = max(r['K'] for r in thin)/min(r['K'] for r in thin)

table6, correction = {}, {}
for direction in ('parallel', 'perpendicular'):
    group = [r for r in main.values() if r['direction'] == direction]
    lo, hi = min(group, key=lambda r:r['E_percent']), max(group, key=lambda r:r['E_percent'])
    table6[direction] = dict(min=lo, max=hi, positive_count=sum(r['E_percent']>0 for r in group), count=len(group),
                             max_to_min_error_ratio=hi['E_percent']/lo['E_percent'])
    correction[direction] = dict(
        full_count=len(group), full_max_abs_residual=max(group,key=lambda r:abs(r['residual_percent'])),
        h_ge50_count=sum(r['h']>=50 for r in group),
        h_ge50_max_abs_residual=max((r for r in group if r['h']>=50),key=lambda r:abs(r['residual_percent'])),
        worsened_points=[r for r in group if abs(r['residual_percent'])>abs(r['E_percent'])])

monotonic = {}
for direction in ('parallel', 'perpendicular'):
    depth_checks, gap_checks = [], []
    for h in (25, 50, 75, 125):
        group = sorted((r for r in main.values() if r['direction']==direction and r['h']==h),key=lambda r:r['d'])
        depth_checks.append(dict(h=h, sequence=[dict(d=r['d'], E_percent=r['E_percent'], run_id=r['run_id']) for r in group],
                                 increasing=all(b['E_percent']>=a['E_percent'] for a,b in zip(group,group[1:]))))
    for d in (25, 50, 75, 100, 120):
        group = sorted((r for r in main.values() if r['direction']==direction and r['d']==d),key=lambda r:r['h'])
        gap_checks.append(dict(d=d, sequence=[dict(h=r['h'], E_percent=r['E_percent'], run_id=r['run_id']) for r in group],
                               decreasing=all(b['E_percent']<=a['E_percent'] for a,b in zip(group,group[1:]))))
    monotonic[direction] = dict(error_vs_depth=depth_checks,error_vs_gap=gap_checks)

p, t = main[75,100,'parallel'], main[75,100,'perpendicular']
Aref, Amod = p['K']/t['K'], p['Kmod']/t['Kmod']
br, bm = math.degrees(math.atan(1/Aref)), math.degrees(math.atan(1/Amod))
table7 = dict(Aref=Aref,Amod=Amod,relative_overestimate_percent=100*(Amod/Aref-1),
              beta_ref_deg=br,beta_model_deg=bm,delta_beta_deg=bm-br)
for item in oblique:
    h,d = item['h'],item['d']
    theta = math.radians(item['theta_deg'])
    G_over_mu = item['G_over_mu']
    Jpred = [main[h,d,'perpendicular']['K']*math.sin(theta)*G_over_mu,
             main[h,d,'parallel']['K']*math.cos(theta)*G_over_mu]
    item['Jpred_xy'] = Jpred
    item['relative_vector_difference'] = math.hypot(*(a-b for a,b in zip(item['J'][:2],Jpred)))/math.hypot(*Jpred)
    item['beta_measured_deg'] = math.degrees(math.atan2(item['J'][0],item['J'][1]))

refinements = []
for key, f in sorted(fine.items()):
    c = main[key]
    refinements.append(dict(h=f['h'],d=f['d'],direction=f['direction'],
                            fine_over_coarse_change_percent=100*(f['K']/c['K']-1),
                            E_coarse_percent=c['E_percent'],E_fine_percent=f['E_percent'],
                            E_change_percentage_points=f['E_percent']-c['E_percent'],
                            residual_coarse_percent=c['residual_percent'], residual_fine_percent=f['residual_percent']))

result = dict(scope='existing-result number audit; no optimizer, simulation, or full gate audit',
              main_count=len(main),fine_count=len(fine),control_count=len(controls),
              table5=table5,thin_gap_cross_ratio=thin_ratio,table6=table6,
              table7=table7,correction=correction,monotonic=monotonic,
              refinements=refinements,oblique_internal_consistency=oblique)
checks = {
    'table5_six_ratios_match_printed_rounding':
        [(f"{r['parallel_ratio']:.2f}", f"{r['perpendicular_ratio']:.3f}") for r in table5]
        == [('3.55','1.034'),('2.13','1.021'),('1.39','1.009')],
    'thin_gap_ratio_matches_1_037': f'{thin_ratio:.3f}' == '1.037',
    'table6_four_endpoints_match_printed_rounding':
        [(f"{table6[k]['min']['E_percent']:.2f}", f"{table6[k]['max']['E_percent']:.2f}")
         for k in ('parallel','perpendicular')] == [('10.30','204.85'),('8.11','54.19')],
    'table6_four_locations_match':
        [(table6[k]['min']['h'],table6[k]['min']['d'],table6[k]['max']['h'],table6[k]['max']['d'])
         for k in ('parallel','perpendicular')] == [(125,25,50,120),(25,25,125,120)],
    'all_36_errors_positive': all(r['E_percent'] > 0 for r in main.values()),
    'table7_values_match_printed_rounding':
        [f'{x:.2f}' for x in (Aref,Amod,br,bm,bm-br)] == ['2.21','3.70','24.34','15.14','-9.20'],
    'published_V2_maxima_match_named_subsets':
        f"{abs(correction['parallel']['full_max_abs_residual']['residual_percent']):.1f}" == '10.5'
        and f"{abs(correction['perpendicular']['h_ge50_max_abs_residual']['residual_percent']):.1f}" == '6.9',
    'thin_cross_residuals_match_printed_rounding':
        [(f"{r['residual_coarse_percent']:.1f}",f"{r['residual_fine_percent']:.1f}")
         for r in refinements if r['h']==25 and r['direction']=='perpendicular'] == [('-18.7','-14.9')],
    '46_reported_wall_intersections_are_halfway':
        all(r['q_min'] == r['q_max'] == .5 for r in [*main.values(),*fine.values(),*controls]),
}
assert all(checks.values()), checks
result['numeric_claim_checks'] = checks
(HERE/'recomputed_section4.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
with (HERE/'per_point.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(next(iter(main.values())).keys()))
    writer.writeheader();writer.writerows(main.values())
(HERE/'input_hashes.json').write_text(json.dumps(inputs,ensure_ascii=False,indent=2)+'\n')
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in inputs.items())
print(json.dumps(dict(table5=table5,thin_gap_cross_ratio=thin_ratio,table7=table7,
                      parallel_gap_decrease_failures=[x for x in monotonic['parallel']['error_vs_gap'] if not x['decreasing']],
                      max_residual_full={k:v['full_max_abs_residual']['residual_percent'] for k,v in correction.items()},
                      worsened={k:[dict(h=r['h'],d=r['d'],E=r['E_percent'],residual=r['residual_percent']) for r in v['worsened_points']] for k,v in correction.items()},
                      oblique_max_relative_difference=max(x['relative_vector_difference'] for x in oblique)),ensure_ascii=False,indent=2))
