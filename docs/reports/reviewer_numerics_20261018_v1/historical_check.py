#!/usr/bin/env python3
"""Recompute archived three-grid chain and later compensated-mass reference."""
import csv
import json
import math
import statistics
from recompute import ROOT, OUT, SOURCES, kv, rows, track, relative

base=ROOT/'CASE/03_grid_convergence/G2_EX240_grid_convergence/archive/g2_grid_20260917T165045+0800/runs'
items=[]
for dxlabel in ('dx5','dx2p5','dx1p25'):
    for case in ('Smooth75','EX240_parallel','EX240_perpendicular'):
        steady=base/dxlabel/case/'steady'
        r=kv(steady/'result.txt'); diag=rows(steady/'diagnostics.csv')
        vals=[float(x['J']) for x in diag[-1000:]]
        mass=[float(x['mass']) for x in diag]
        k=float(diag[-1]['J'])*.001/1e8
        item={'grid':dxlabel,'case':case,'path':str(steady.relative_to(ROOT)),'K':k,'original_PASS':r['PASS'],'exit':track(steady/'exit_code.txt').read_text().strip(),'mass_max':max(abs((x-mass[0])/mass[0]) for x in mass),'std':statistics.stdev(vals)/abs(statistics.fmean(vals)),'span':(max(vals)-min(vals))/abs(statistics.fmean(vals)),'steps':len(diag)-1,'dx_m':float(r['dx_m']),'dt_s':float(r['dt_s']),'h_m':float(r.get('mesa_gap_m',r.get('H_m'))),'d_m':float(r.get('groove_depth_m',0)),'q':[float(r['q_min']),float(r['q_max'])],'fluid_nodes':int(r['fluid_nodes'])}
        if case=='Smooth75':
            profile=rows(steady/'velocity_profile.csv')
            height=float(r['H_m']); mu=.001; gradient=1e8
            theory=height**3/12
            analytic=[gradient/(2*mu)*float(x['z'])*(height-float(x['z'])) for x in profile]
            lbm=[float(x['u_LBM']) for x in profile]
            j_profile=math.fsum(lbm)*float(r['dx_m'])
            item.update({'analytic_K':theory,'analytic_K_error_percent':100*(k/theory-1),'profile_L2_percent':100*math.sqrt(math.fsum((a-b)**2 for a,b in zip(lbm,analytic))/math.fsum(a*a for a in analytic)),'J_profile_relative_difference':relative(j_profile,float(diag[-1]['J'])),'profile_analytic_column_max_difference':max(abs(float(x['u_analytic'])-a) for x,a in zip(profile,analytic))})
            exact_j=gradient*theory/mu
            analytic_midpoint_j=math.fsum(analytic)*float(r['dx_m'])
            item['midpoint_quadrature_error_percent']=100*(analytic_midpoint_j/exact_j-1)
            item['integrated_velocity_profile_error_percent']=100*(j_profile-analytic_midpoint_j)/exact_j
        items.append(item)

gcis=[]
for case in ('Smooth75','EX240_parallel','EX240_perpendicular'):
    kf,km,kc=[next(x['K'] for x in items if x['grid']==g and x['case']==case) for g in ('dx1p25','dx2p5','dx5')]
    p=math.log((kc-km)/(km-kf),2)
    ext=kf+(kf-km)/(2**p-1)
    fine=1.25*abs(km-kf)/kf/(2**p-1)
    medium=1.25*abs(kc-km)/km/(2**p-1)
    coarse=1.25*2**p*abs(kc-km)/kc/(2**p-1)
    gcis.append({'case':case,'fine_K':kf,'medium_K':km,'coarse_K':kc,'order':p,'extrapolated_K':ext,'GCI_fine_percent':100*fine,'GCI_medium_percent':100*medium,'GCI_coarse_percent':100*coarse,'asymptotic_ratio':medium/(2**p*fine),'ratio_equals_fine_over_medium':kf/km,'coarse_K_over_extrapolated_percent':100*(kc/ext-1)})

cpath=ROOT/'CASE/03_grid_convergence/G2_EX240_fine_T_statfix_C_v1/runs/fine_t_C_20261014T151036+0800'
cr=kv(cpath/'result.txt'); cd=rows(cpath/'diagnostics.csv'); manifest=json.loads(track(cpath/'manifest.json').read_text())
corrected=[float(x['corrected_mass']) for x in cd]; legacy=[float(x['mass']) for x in cd]
cv=[float(x['J']) for x in cd[-1000:]]
old=rows(base/'dx1p25'/'EX240_perpendicular'/'steady'/'diagnostics.csv')
common=list(old[0])
different=sum(any(x[k]!=y[k] for k in common) for x,y in zip(old,cd))
c={'path':str(cpath.relative_to(ROOT)),'PASS':cr['PASS'],'shell_exit':track(cpath/'exit_code.txt').read_text().strip(),'steps':len(cd)-1,'corrected_mass_max':max(abs((x-corrected[0])/corrected[0]) for x in corrected),'legacy_mass_max':max(abs((x-legacy[0])/legacy[0]) for x in legacy),'delta_mass_error_max':max(abs(float(x['delta_mass_error'])) for x in cd),'mass_ledger_agreement_max':max(abs(float(x['corrected_mass_error'])-float(x['delta_mass_error'])) for x in cd),'std':statistics.stdev(cv)/statistics.fmean(cv),'span':(max(cv)-min(cv))/statistics.fmean(cv),'K':float(cd[-1]['J'])*.001/1e8,'common_original_columns':common,'common_rows_compared':min(len(old),len(cd)),'different_common_rows':different,'manifest_formal_reference_accepted':manifest['formal_reference_accepted'],'source_hash_check':{}}
for path,expected in manifest['source_files'].items():
    p=ROOT/str(path).split('/SIM240/',1)[-1]
    c['source_hash_check'][str(p.relative_to(ROOT))]=track(p).is_file() and SOURCES[str(p.relative_to(ROOT))]==expected

current=json.loads((OUT/'runs.json').read_text())
viscosity=[]
for x in current:
    if x['group']!='viscosity':continue
    orig=next(y for y in current if y['group']=='map' and abs(y['h_nm']-75)<1e-6 and abs(y['d_nm']-100)<1e-6 and y['direction']==x['direction'])
    viscosity.append({'direction':x['direction'],'K_mu1':orig['K_recomputed_m3'],'K_mu15':x['K_recomputed_m3'],'K_change_percent':100*(x['K_recomputed_m3']/orig['K_recomputed_m3']-1)})
payload={'archived_runs':items,'recomputed_GCI':gcis,'scheme_C':c,'mu_comparison':viscosity,'D2_D3_manifest_source_hash_missing':sum(x['source_sha256_manifest'] is None for x in current),'D2_D3_binary_hash_groups':{h:sum(x['binary_sha256_manifest']==h for x in current) for h in sorted(set(x['binary_sha256_manifest'] for x in current))}}
(OUT/'historical.json').write_text(json.dumps(payload,indent=2)+'\n')
(OUT/'historical_source_hashes.json').write_text(json.dumps(SOURCES,indent=2)+'\n')
print(json.dumps({k:v for k,v in payload.items() if k!='archived_runs'},indent=2))
