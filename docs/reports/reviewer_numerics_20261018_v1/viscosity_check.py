#!/usr/bin/env python3
"""Directly infer viscosity from raw result triples and check current text.

No dependency on existing audit reports or numerical-result summaries.
"""
from pathlib import Path
import csv
import hashlib
import json
import math

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
HASHES={}


def read(path):
    HASHES[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
    return path.read_text()


def parse(path):
    return dict(line.split('=',1) for line in read(path).splitlines() if '=' in line)


def single(path):
    r=parse(path)
    tau=float(r['tau']);dx=float(r['dx_m']);dt=float(r['dt_s'])
    nu=(tau-.5)*dx*dx/(3*dt)
    rho=float(r.get('rho_phys_kg_m3',1000.0))
    # Missing rho is declared, not silently treated as a recorded input.
    density_basis='explicit_result' if 'rho_phys_kg_m3' in r else 'manuscript_rho1000_and_source_constant'
    diag_path=path.parent/'diagnostics.csv'
    HASHES[str(diag_path)]=hashlib.sha256(diag_path.read_bytes()).hexdigest()
    with diag_path.open() as stream:
        initial=next(csv.DictReader(stream))
    rho_from_initial_mass=float(initial['mass'])/(float(initial['rho'])*float(r['fluid_volume_m3']))
    mu=rho*nu
    j=float(r['J_main_m2_s']);k=float(r['Keff_m3']);a=float(r['acceleration_m_s2'])
    return {'result_path':str(path.relative_to(ROOT)),'case':r['case'],'h_nm':float(r['mesa_gap_m'])*1e9,'d_nm':float(r['groove_depth_m'])*1e9,'direction':r['direction'],'tau':tau,'dx_m':dx,'dt_s':dt,'nu_inferred_m2_s':nu,'rho_used_kg_m3':rho,'rho_basis':density_basis,'rho_indirect_from_initial_mass_kg_m3':rho_from_initial_mass,'mu_inferred_Pa_s':mu,'mu_inferred_mPa_s':1000*mu,'rho_recorded':r.get('rho_phys_kg_m3'),'mu_recorded':r.get('mu_phys_Pa_s'),'K_stored_m3':k,'K_recomputed_m3':nu*j/a,'J_stored_m2_s':j,'mu_from_stored_K_and_J_Pa_s':k*rho*a/j,'dt_required_for_mu15_s':rho*(tau-.5)*dx*dx/(3*.015)}


result_root=ROOT/'CASE/D_series/D2_groove_error_map/results'
maprows=[]
for path in sorted(result_root.glob('*/steady/result.txt')):
    if path.parent.parent.name.startswith(('_','mu15')):continue
    r=parse(path)
    if abs(float(r['dx_m'])-5e-9)>1e-18:continue
    maprows.append(single(path))
assert len(maprows)==36,len(maprows)
checks=[single(result_root/('mu15_h75_d100_dx5_'+d)/'steady/result.txt') for d in ('P','T')]
with (OUT/'viscosity36.csv').open('w',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(maprows[0]));writer.writeheader();writer.writerows(maprows)

groups={}
for r in maprows:
    groups.setdefault((round(r['h_nm']),round(r['d_nm'])),{})[r['direction']]=r
text_geometry=[]
for (h,d),items in sorted(groups.items()):
    kp=items['parallel']['K_stored_m3'];kt=items['perpendicular']['K_stored_m3']
    href=(h+.5*d)*1e-9
    text_geometry.append({'h_nm':h,'d_nm':d,'K_parallel':kp,'K_perpendicular':kt,'anisotropy':kp/kt,'Href_m':href,'eta_parallel':kp/(href**3/12),'eta_perpendicular':kt/(href**3/12),'k_parallel_correct_m2':kp/href,'k_parallel_if_divide_period_m2':kp/240e-9})
viscosity_pairs=[]
for high in checks:
    low=next(r for r in maprows if abs(r['h_nm']-75)<1e-6 and abs(r['d_nm']-100)<1e-6 and r['direction']==high['direction'])
    viscosity_pairs.append({'direction':high['direction'],'J_mu1':low['J_stored_m2_s'],'J_mu15':high['J_stored_m2_s'],'J_mu1_over_J_mu15':low['J_stored_m2_s']/high['J_stored_m2_s'],'K_change_percent':100*(high['K_stored_m3']/low['K_stored_m3']-1)})
texts={}
for name in ('第一篇论文_第1章引言草稿_20261017.md','第一篇论文_第2章方法草稿_20261017.md','第一篇论文_第3章验证草稿_20261017.md','第一篇论文_第4章结果I草稿_20261018.md','第一篇论文_第5章_对比对象选择草稿_20261018.md'):
    path=ROOT/'docs/reports'/name
    lines=read(path).splitlines()
    texts[str(path.relative_to(ROOT))]=[{'line':i,'text':line} for i,line in enumerate(lines,1) if any(k in line for k in ('15 mPa','15 mPa·s','0.015','10^{-6}','viscosity','黏度','沿 $x$ 驱动','thirty-six geometries','K^{[\\mathrm{m^2}]}','唯一有效'))]
for source in ('CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp','CASE/D_series/D2_groove_error_map/scripts/run_mu_check.sh'):
    read(ROOT/source)
read(Path('/home/dell/openlb/src/core/unitConverter.h'))
payload={'map_count':len(maprows),'map_missing_rho':sum(r['rho_recorded'] is None for r in maprows),'map_missing_mu':sum(r['mu_recorded'] is None for r in maprows),'nu_range':[min(r['nu_inferred_m2_s'] for r in maprows),max(r['nu_inferred_m2_s'] for r in maprows)],'mu_range_at_rho1000_mPa_s':[min(r['mu_inferred_mPa_s'] for r in maprows),max(r['mu_inferred_mPa_s'] for r in maprows)],'rho_indirect_range':[min(r['rho_indirect_from_initial_mass_kg_m3'] for r in maprows),max(r['rho_indirect_from_initial_mass_kg_m3'] for r in maprows)],'mu15_checks':checks,'paired_scaling':viscosity_pairs,'geometry_count':len(text_geometry),'geometry_values':text_geometry,'text_matches':texts,'inputs':HASHES}
changed=[path for path,expected in HASHES.items() if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected]
payload['inputs_changed_during_check']=changed
assert not changed,changed
assert all(abs(r['nu_inferred_m2_s']/1e-6-1)<1e-14 for r in maprows)
assert all(abs(r['K_recomputed_m3']/r['K_stored_m3']-1)<1e-14 for r in maprows+checks)
(OUT/'viscosity_text_check.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:v for k,v in payload.items() if k not in ('geometry_values','text_matches','inputs','mu15_checks')},indent=2))
