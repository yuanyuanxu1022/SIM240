#!/usr/bin/env python3
"""Audit existing supporting artifacts and selected reported method numbers.

No solver, compiler, optimizer, or old audit is executed or modified. Recorded
PASS/exit are inventoried separately from independent numerical recomputation.
"""
import collections
import csv
import hashlib
import json
import math
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
hashes={}


def read(path):
    path=Path(path)
    if not path.is_absolute():path=ROOT/path
    data=path.read_bytes()
    try:key=str(path.relative_to(ROOT))
    except ValueError:key=str(path)
    hashes[key]=hashlib.sha256(data).hexdigest()
    return data.decode(errors='replace')


def kv(path):
    return dict(s.split('=',1) for s in read(path).splitlines() if '=' in s)


index=ROOT/'docs/reports/第一篇_run_id索引_20261022.csv'
rows=list(csv.DictReader(read(index).splitlines()))
assert len(rows)==52
inventory=[]
binary_groups=collections.Counter()
metadata_counts=collections.Counter()
main={};fine={};q=[];mach=[]
for row in rows:
    base=ROOT/row['rel_path'];steady=base/'steady'
    r=kv(steady/'result.txt');m=kv(steady/'run_manifest.txt')
    shell_exit=read(steady/'exit_code.txt').strip()
    dr=row['direction'];h=round(float(r['mesa_gap_m'])*1e9);d=round(float(r['groove_depth_m'])*1e9)
    dx=round(float(r['dx_m'])*1e9,8)
    group=('oblique' if dr.startswith('oblique') else 'viscosity' if row['run_id'].startswith('mu15') else 'main' if dx==5 else 'refinement')
    rec=dict(run_id=row['run_id'],group=group,h=h,d=d,dx_nm=dx,direction=dr,
             result=str((steady/'result.txt').relative_to(ROOT)),
             manifest=str((steady/'run_manifest.txt').relative_to(ROOT)),
             recorded_PASS=r.get('PASS'),shell_exit=shell_exit,
             binary_sha256=m.get('binary_sha256'),manifest_keys=sorted(m),
             K=float(r['Keff_m3']),q_min=float(r['q_min']),q_max=float(r['q_max']),Mach=float(r['max_Mach']))
    for key in ('binary_sha256','source_sha256','generated_source_sha256','openlb_commit','compiler','compile_flags'):
        if m.get(key):metadata_counts[key]+=1
    binary_groups[m.get('binary_sha256','MISSING')]+=1
    if (steady/'run.log').exists():
        text=read(steady/'run.log');v=re.findall(r'Version\s*:\s*(\S+)',text)
        rec.update(log=str((steady/'run.log').relative_to(ROOT)),log_version_string=v[0] if v else None,log_style='individual')
    else:
        shared=ROOT/'CASE/D_series/D2_groove_error_map/results/dx25_refine4_run_20261018.log'
        text=read(shared)
        case=m['case_id']
        marker=f'--- {case} steady exit={shell_exit}'
        assert marker in text,(case,'no shared log binding marker')
        rec.update(log=str(shared.relative_to(ROOT)),log_version_string='5953d8a-dirty',log_style='shared_batch',shared_log_marker=marker,
                   result_case_label=r['case'],manifest_case_label=case)
    rec['artifacts']={}
    for filename in ('diagnostics.csv','boundary_audit.txt','velocity_profile.csv','pressure_profile.csv','field_slice.csv'):
        p=steady/filename
        rec['artifacts'][filename]=p.is_file()
        if p.is_file() and filename=='boundary_audit.txt':read(p)
    for filename in ('result.txt','exit_code.txt','boundary_audit.txt'):
        p=base/'precheck'/filename
        rec['artifacts']['precheck/'+filename]=p.is_file()
        if p.is_file():read(p)
    q.append((rec['q_min'],rec['q_max']));mach.append(rec['Mach'])
    if group=='main':main[h,d,dr]=rec
    if group=='refinement':fine[h,d,dr]=rec
    inventory.append(rec)

refinements=[]
for key,f in sorted(fine.items()):
    c=main[key];h,d,dr=key;a,b=h**3,(h+d)**3
    model=((a+b)/24 if dr=='parallel' else a*b/(6*(a+b)))*1e-27
    ec=100*(model/c['K']-1);ef=100*(model/f['K']-1)
    refinements.append(dict(h=h,d=d,direction=dr,K5=c['K'],K2_5=f['K'],
                            K_change_percent=100*(f['K']/c['K']-1),E5_percent=ec,E2_5_percent=ef,
                            E_change_percentage_points=ef-ec))

g4root=ROOT/'CASE/03_grid_convergence/G4_EX240_period_convergence'
for f in ('README.md','PERIOD_CONVERGENCE_PROTOCOL.md','REUSE_AUDIT.md','period_matrix.csv'):read(g4root/f)
g4batches={2:'g4_period_nx2_fields_v1_20261012T001316+0800',4:'g4_period_nx4_fields_v1_20261012T105719+0800',8:'g4_period_nx8_fields_v1_20261012T163341+0800'}
g4=[];g4lookup={}
for nx,batch in g4batches.items():
    batchdir=g4root/'results'/batch
    read(batchdir/'G4_LEVEL_REPORT.md')
    for dr in ('P','T'):
        for label,a in (('5e4',5e4),('1e5',1e5),('2e5',2e5)):
            steady=batchdir/'runs'/f'nx{nx}_{dr}_a{label}'/'steady'
            r=kv(steady/'result.txt');m=kv(steady/'run_manifest.txt')
            assert math.isclose(float(r['acceleration_m_s2']),a)
            assert math.isclose(float(r['dx_m']),2.5e-9,rel_tol=1e-12)
            assert math.isclose(float(r['mesa_gap_m']),75e-9,rel_tol=1e-12)
            assert math.isclose(float(r['groove_depth_m']),100e-9,rel_tol=1e-12)
            item=dict(nx=nx,direction=dr,acceleration=a,run_id=m.get('run_id'),
                      path=str(steady.relative_to(ROOT)),K=float(r['Keff_m3']),R=float(r['R_eff_Pa_s_per_m3']),
                      recorded_PASS=r.get('PASS'),shell_exit=read(steady/'exit_code.txt').strip())
            g4.append(item);g4lookup[nx,dr,a]=item
linear=[];period=[]
for nx in g4batches:
    for dr in ('P','T'):
        vals=[g4lookup[nx,dr,a]['K'] for a in (5e4,1e5,2e5)]
        linear.append(dict(nx=nx,direction=dr,K_span_over_mean=(max(vals)-min(vals))/(sum(vals)/3)))
for dr in ('P','T'):
    for n0,n1 in ((2,4),(4,8)):
        r0=g4lookup[n0,dr,1e5]['R'];r1=g4lookup[n1,dr,1e5]['R']
        period.append(dict(direction=dr,nx0=n0,nx1=n1,relative_R_difference=abs(r1-r0)/r0))

gridroot=ROOT/'CASE/03_grid_convergence/G2_EX240_grid_convergence/archive/g2_grid_20260917T165045+0800'
for f in ('G2_GRID_CONVERGENCE_REPORT.md','SOURCE_MANIFEST.md','g2_richardson_gci.csv'):read(gridroot/f)
grids=[]
for dx in ('dx5','dx2p5','dx1p25'):
    for case in ('Smooth75','EX240_parallel','EX240_perpendicular'):
        steady=gridroot/'runs'/dx/case/'steady';r=kv(steady/'result.txt')
        read(steady/'run_manifest.txt')
        j=float(r['J_m2_s'] if case=='Smooth75' else r['J_main_m2_s'])
        k=j*1e-11
        item=dict(dx=dx,case=case,path=str(steady.relative_to(ROOT)),K=k,
                  recorded_PASS=r.get('PASS'),shell_exit=read(steady/'exit_code.txt').strip())
        if case=='Smooth75':item['analytic_error_percent']=100*(k/(75e-9)**3*12-1)
        grids.append(item)
gridp=next(x['K'] for x in grids if x['case']=='EX240_parallel' and x['dx']=='dx2p5')
baseline_relative_difference=abs(g4lookup[2,'P',1e5]['K']/gridp-1)

cdir=ROOT/'CASE/03_grid_convergence/G2_EX240_fine_T_statfix_C_v1/runs/fine_t_C_20261014T151036+0800'
cmanifest=json.loads(read(cdir/'manifest.json'));cres=kv(cdir/'result.txt')
c_state=dict(run_id=cmanifest['run_id'],formal_reference_accepted=cmanifest['formal_reference_accepted'],
             recorded_PASS=cres.get('PASS'),shell_exit=read(cdir/'exit_code.txt').strip())

for f in ('docs/ex240/ex240_layout_report.md','CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp',
          'CASE/D_series/D2_groove_error_map/src/Makefile',
          'docs/reports/reviewer_numerics_20261018_v1/REPORT.md',
          'docs/reports/Methods_and_Section4_review_20261022/recomputed_section4.json'):
    read(f)
oas=ROOT/'docs/ex240/SIM-EC1XT240.OAS';read(oas)
oas_hash=hashes[str(oas.relative_to(ROOT))]
assert oas_hash=='209fbd4b907dc591c8786035face94de7df05fd10debf7e73dfc51a186ac0bfc'
for path in ('/home/dell/openlb/src/dynamics/dynamics.h','/home/dell/openlb/src/dynamics/momenta/elements.h',
             '/home/dell/openlb/src/dynamics/forcing.h','/home/dell/openlb/CITATION.cff'):
    read(path)
pdf=ROOT/'docs/reports/Jain_citation_audit_20261017/raw/patir1978_JLubrTech_100_12-17.pdf'
read(pdf)

result=dict(scope='supporting-artifact inventory and selected method-number recomputation; no full gate or build-provenance approval',
            run_counts=dict(collections.Counter(x['group'] for x in inventory)),
            manifests_with_fields={k:metadata_counts[k] for k in ('binary_sha256','source_sha256','generated_source_sha256','openlb_commit','compiler','compile_flags')},
            binary_hash_groups=dict(binary_groups),logs_by_style=dict(collections.Counter(x['log_style'] for x in inventory)),
            q_all_52_halfway=all(a==b==.5 for a,b in q),Mach_range=[min(mach),max(mach)],
            runs=inventory,refinements=refinements,G4_runs=g4,G4_linearity=linear,G4_period=period,
            G4_grid_baseline_relative_difference=baseline_relative_difference,archived_grid=grids,
            scheme_C=c_state,OAS_hash_matches_layout_report=True)
(HERE/'support_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(HERE/'input_hashes.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2)+'\n')
with (HERE/'run_inventory.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=['run_id','group','result','manifest','recorded_PASS','shell_exit','binary_sha256','log_style','log'])
    writer.writeheader();writer.writerows({k:x.get(k) for k in writer.fieldnames} for x in inventory)
assert all(hashlib.sha256((ROOT/p if not Path(p).is_absolute() else Path(p)).read_bytes()).hexdigest()==h for p,h in hashes.items())
print(json.dumps({k:v for k,v in result.items() if k not in ('runs','G4_runs','archived_grid','refinements')},ensure_ascii=False,indent=2))
