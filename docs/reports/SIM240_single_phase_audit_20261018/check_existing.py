"""Read-only checks of existing outputs; writes only this audit's evidence JSON.

Not a solver run, full provenance release, or substitute for frozen Gate review.
"""
from pathlib import Path
import csv
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
D2 = ROOT / 'CASE/D_series/D2_groove_error_map/results'
D3 = ROOT / 'CASE/D_series/D3_oblique_groove_tensor_check/results'
inputs = {}

def bind(path):
    inputs[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()

def kv(path):
    bind(path)
    return dict(line.split('=', 1) for line in path.read_text().splitlines() if '=' in line)

def model(h, d, direction):
    return ((h**3 + (h+d)**3)/24 if direction == 'P'
            else 1/(6*(h**-3+(h+d)**-3))) * 1e-27

specs = []
for h in (50, 75, 125):
    for d in (25, 50, 100):
        for direction in ('P', 'T'):
            specs.append((D2/f'h{h}_d{d}_dx5_{direction}', 'map', h, d, direction))
for prefix, hs, ds in [('d75', (50,75,125), (75,)),
                       ('h25', (25,), (25,50,100)),
                       ('d120', (50,75,125), (120,))]:
    for h in hs:
        for d in ds:
            for direction in ('P','T'):
                name = f'h25_d{d}_dx5_{direction}' if prefix == 'h25' else f'{prefix}_h{h}_dx5_{direction}'
                specs.append((D2/name, 'map', h, d, direction))
for h,d in [(50,100),(125,25)]:
    for direction in ('P','T'):
        specs.append((D2/f'h{h}_d{d}_dx2.5_{direction}', 'refinement', h,d,direction))
for direction in ('P','T'):
    specs.append((D2/f'mu15_h75_d100_dx5_{direction}', 'viscosity',75,100,direction))
for path in sorted(D3.glob('*/steady/result.txt')):
    if path.parent.parent.name.startswith('_'):
        continue
    specs.append((path.parent.parent, 'oblique',None,None,None))

records=[]
for path,group,h,d,direction in specs:
    result = kv(path/'steady/result.txt')
    manifest = kv(path/'steady/run_manifest.txt')
    pre = kv(path/'precheck/result.txt')
    codes=[]
    for mode in ('precheck','steady'):
        ep=path/mode/'exit_code.txt'; bind(ep); codes.append(ep.read_text().strip())
    diag = path/'steady/diagnostics.csv'; bind(diag)
    count=0; bad_finite=0; max_mass=max_rho=max_ma=0.; last=None
    with diag.open() as f:
        for row in csv.DictReader(f):
            count+=1; last=row
            bad_finite += row['finite'] not in ('1','true')
            max_mass=max(max_mass,abs(float(row['mass_error'])))
            max_rho=max(max_rho,abs(float(row['max_density_deviation'])))
            max_ma=max(max_ma,abs(float(row['Mach'])))
    checks={
        'shell_exit_zero':codes==['0','0'],
        'reported_pass':result.get('PASS')=='true',
        'converged':result.get('converged')=='true',
        'geometry':pre.get('geometry_PASS')=='true',
        'q_audit':pre.get('q_audit_PASS')=='true',
        'converter':pre.get('converter_PASS')=='true',
        'finite_all_diagnostic_rows':bad_finite==0,
        'mass_all_rows':max_mass<1e-10,
        'density_all_rows':max_rho<=1e-6,
        'mach_all_rows':max_ma<.05,
        'final_section':float(result['section_relative_difference'])<=1e-5,
        'final_std':float(result['window_main_rel_std'])<=1e-6,
        'final_span':float(result['window_main_rel_span'])<=5e-6,
        'materials':result.get('material_unchanged')=='true',
        'no_fallback':int(result['fallback_count'])==0,
        'no_unresolved':int(result['unresolved_links'])==0,
        'complete_diag_steps':count==int(result['steps_completed'])+1 and int(last['step'])==int(result['steps_completed']),
    }
    record=dict(path=str(path.relative_to(ROOT)),group=group,h=h,d=d,direction=direction,
                checks=checks,diag_rows=count,max_mass=max_mass,max_rho=max_rho,max_ma=max_ma,
                K=float(result['Keff_m3']),J=float(result['J_main_m2_s']),
                result=result,manifest_keys=sorted(manifest),binary_sha256=manifest.get('binary_sha256'))
    if group=='map':
        km=model(h,d,direction); ratio=km/record['K']
        f_old=1/(1+(1.7207*(d/(h+d/2))**1.8046 if direction=='P' else .5276*(d/120)**.8259))
        f_new=1/(1+(1.7685*(d/120)**1.6331 if direction=='P' else .4900*(d/120)**.6990))
        record.update(K_model=km,E_pct=(ratio-1)*100,old_residual_pct=(ratio*f_old-1)*100,
                      proposed_residual_pct=(ratio*f_new-1)*100)
    records.append(record)

maps={(r['h'],r['d'],r['direction']):r for r in records if r['group']=='map'}
angle=[]
for h in (50,75):
    ap=maps[h,100,'P']['K']/maps[h,100,'T']['K']
    am=model(h,100,'P')/model(h,100,'T')
    angle.append(dict(h=h,theta_deg=45,A_DNS=ap,A_model=am,
                      beta_DNS_deg=math.degrees(math.atan(1/ap)),
                      beta_model_deg=math.degrees(math.atan(1/am))))
mu=[]
for r in records:
    if r['group']=='viscosity':
        base=maps[75,100,r['direction']]
        mu.append(dict(direction=r['direction'],K_change_pct=(r['K']/base['K']-1)*100,J_ratio=base['J']/r['J']))
grid=[]
for r in records:
    if r['group']=='refinement':
        base=maps[r['h'],r['d'],r['direction']]
        grid.append(dict(h=r['h'],d=r['d'],direction=r['direction'],coarse_vs_fine_pct=(base['K']/r['K']-1)*100))
ratios=[maps[h,100,'T']['K_model']/maps[h,100,'T']['K'] for h in (25,50,75,125)]
gci_path=ROOT/'CASE/03_grid_convergence/G2_EX240_grid_convergence/archive/g2_grid_20260917T165045+0800/g2_richardson_gci.csv'
bind(gci_path)
coarse=[]
with gci_path.open() as f:
    for row in csv.DictReader(f):
        if row['metric'] in ('K_parallel','K_perpendicular'):
            val=float(row['coarse_value']); ext=float(row['richardson_extrapolated'])
            coarse.append(dict(metric=row['metric'],dx_nm=5,
                               extrapolation_difference_pct=100*abs(val-ext)/abs(val),
                               conditional_coarse_GCI_pct=125*abs(val-ext)/abs(val)))
documents=[
    'CASE/plans/SIM240_第一篇范围重定位_纯液体单相_20261016.md',
    'CASE/plans/SIM240_几何与单位口径冻结_20261016.md',
    'docs/reports/第一篇论文_第1章引言草稿_20261017.md',
    'docs/reports/第一篇论文_第2章方法草稿_20261017.md',
    'docs/reports/第一篇论文_第3章验证草稿_20261017.md',
    'docs/reports/交付物缺陷审计_20261017.md',
    'docs/reports/修正公式重拟合_又稳又好听_20261017.md',
    'docs/reports/Jain_citation_audit_20261017/STATUS_20261017.md',
    'CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp',
    'CASE/D_series/D3_oblique_groove_tensor_check/src/d3_oblique_groove_tensor_check.cpp',
    'CASE/D_series/D2_groove_error_map/scripts/fit_correction.py',
    'CASE/D_series/D2_groove_error_map/results/analysis/ACCEPTANCE_AND_ANALYSIS_20261016.md',
    'CASE/D_series/D2_groove_error_map/results/analysis/EXTENDED_ANALYSIS_20261017.md',
    'CASE/D_series/D3_oblique_groove_tensor_check/results/D3_OBLIQUE_ACCEPTANCE_20261016.md',
    'CASE/03_grid_convergence/G2_EX240_fine_T_statfix_C_v1/runs/fine_t_C_20261014T151036+0800/result.txt',
    'CASE/03_grid_convergence/G2_EX240_fine_T_statfix_C_v1/runs/fine_t_C_20261014T151036+0800/exit_code.txt',
    'CASE/03_grid_convergence/G2_EX240_fine_T_statfix_C_v1/runs/fine_t_C_20261014T151036+0800/completion.json',
]
for name in documents:
    bind(ROOT/name)
evidence=dict(date='2026-10-18',scope='existing output arithmetic/selected gate checks only; no new simulation or full release',
              counts={g:sum(r['group']==g for r in records) for g in ('map','refinement','viscosity','oblique')},
              geometry_count=len({(r['h'],r['d']) for r in records if r['group']=='map'}),
              failed_checks=[dict(path=r['path'],failed=[k for k,v in r['checks'].items() if not v]) for r in records if not all(r['checks'].values())],
              records=records,grid=grid,viscosity=mu,angles=angle,conditional_coarse_GCI=coarse,
              diagnostic_rows_total=sum(r['diag_rows'] for r in records),
              referenced_release_path_exists=(ROOT/'CASE/reports/fine_T_C_release_20261014_v1/RELEASE.md').exists(),
              h_independent_T_d100_best_possible_max_residual_pct=100*(max(ratios)-min(ratios))/(max(ratios)+min(ratios)),
              input_sha256=inputs)
(OUT/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in evidence.items() if k not in ('records','input_sha256')},ensure_ascii=False,indent=2))
for key in [(125,100,'P'),(125,120,'P'),(25,100,'T')]:
    r=maps[key]; print(key,{k:r[k] for k in ['E_pct','old_residual_pct','proposed_residual_pct']})
for direction in ('P','T'):
    rs=[r for r in records if r['group']=='map' and r['direction']==direction]
    print(direction,'E range',min(r['E_pct'] for r in rs),max(r['E_pct'] for r in rs))
