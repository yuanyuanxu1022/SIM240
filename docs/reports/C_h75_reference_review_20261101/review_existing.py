#!/usr/bin/env python3
"""Reconstruct a new, bounded review of existing C/h75 records. No solver imports."""
from pathlib import Path
from collections import deque
import csv
import difflib
import hashlib
import itertools
import json
import math
import re
import statistics
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
GRID=ROOT/'CASE/03_grid_convergence/G2_EX240_grid_convergence'
ARCH=GRID/'archive/g2_grid_20260917T165045+0800'
CROOT=ROOT/'CASE/03_grid_convergence/G2_EX240_fine_T_statfix_C_v1'
CRUN=CROOT/'runs/fine_t_C_20261014T151036+0800'
INPUTS={}

def sha(p):
    p=Path(p).resolve();h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    INPUTS[str(p)]=h.hexdigest();return h.hexdigest()
def text(p):sha(p);return Path(p).read_text()
def kv(p):return dict(s.split('=',1) for s in text(p).splitlines() if '=' in s and not s.startswith('#'))
def js(p):return json.loads(text(p))
def save(n,x):
    p=OUT/n
    if p.exists():raise FileExistsError(p)
    p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def resolve_old(s):
    p=Path(s)
    if p.exists():return p,'original_path'
    changes={'CASE/G2_EX240_grid_convergence/':'CASE/03_grid_convergence/G2_EX240_grid_convergence/',
             'CASE/G2_EX240_single_period_transport/':'CASE/02_geometry_transport/G2_EX240_single_period_transport/',
             'CASE/G1_Poiseuille_Bouzidi_Validation/':'CASE/00_validation/G1_Poiseuille_Bouzidi_Validation/'}
    for a,b in changes.items():
        if '/'+a in s:return Path(s.replace('/'+a,'/'+b,1)),'explicit_directory_migration'
    return p,'unresolved'

def geometry(dx,smooth=False):
    nx=round(240/dx);ny=nx;nh=round(75/dx);nd=0 if smooth else round(100/dx)
    x,z=np.meshgrid(np.arange(nx)+.5,np.arange(nh+nd)+.5,indexing='ij')
    left=60/dx;right=180/dx
    def fluid(xx,zz):
        xx=np.remainder(xx,nx)
        return (zz>=0)&(zz<nh+nd*((xx>=left)&(xx<right)))
    f=fluid(x,z);nodes=int(f.sum())*ny;links=0;qmin=1.;qmax=0.
    for cx,cy,cz in itertools.product([-1,0,1],repeat=3):
        if cx*cx+cy*cy+cz*cz not in [1,2]:continue
        hits=f&~fluid(x+cx,z+cz);links+=int(hits.sum())*ny
        if not hits.any():continue
        xx=x[hits];zz=z[hits];q=np.full(xx.shape,np.inf)
        if cz:
            for height,mode in [(0,'bottom'),(nh,'mesa'),(nh+nd,'groove')]:
                t=(height-zz)/cz;hitx=np.remainder(xx+t*cx,nx)
                inside=(hitx>=left)&(hitx<right)
                valid=(t>=0)&(t<=1)
                if mode=='mesa':valid &= (~inside) if nd else True
                if mode=='groove':valid &= inside if nd else True
                q=np.minimum(q,np.where(valid,t,np.inf))
        if cx and nd:
            for edge in [left,right]:
                t=(edge-xx)/cx;hitz=zz+t*cz
                valid=(t>=0)&(t<=1)&(hitz>=nh)&(hitz<=nh+nd)
                q=np.minimum(q,np.where(valid,t,np.inf))
        assert np.isfinite(q).all() and np.max(np.abs(q-.5))<=1e-10
        qmin=min(qmin,float(q.min()));qmax=max(qmax,float(q.max()))
    return dict(dx_nm=dx,smooth=smooth,nx=nx,ny=ny,fluid_nodes=nodes,candidate_links=links,
                q_min=qmin,q_max=qmax,method='independent XZ wall-ray intersection and periodic Y extrusion')

def scalar(path,smooth=False,corrected=False):
    r=kv(path/'result.txt');sha(path/'diagnostics.csv')
    tail=deque(maxlen=1000);ext={'mass_error':0.,'corrected_mass_error':0.,'mass_ledger_agreement':0.,'Mach':0.,'max_density_deviation':0.}
    n=0;finite=True;firstmass=None;mass_recomputed=0.
    with (path/'diagnostics.csv').open() as f:
        for row in csv.DictReader(f):
            v={k:float(x) for k,x in row.items()};assert v['step']==n;n+=1
            finite &= all(math.isfinite(x) for x in v.values()) and bool(v['finite'])
            if firstmass is None:firstmass=v['mass']
            mass_recomputed=max(mass_recomputed,abs((v['mass']-firstmass)/firstmass))
            for k in ext:ext[k]=max(ext[k],abs(v.get(k,0)))
            tail.append(v)
    values=[v['J'] for v in tail];mean=math.fsum(values)/len(values)
    std=statistics.stdev(values)/abs(mean);span=(max(values)-min(values))/abs(mean)
    ck='Jx' if smooth or r.get('direction')=='parallel' else 'Jy'
    cross=max(abs(v[ck]) for v in tail)
    mass=ext['corrected_mass_error'] if corrected else ext['mass_error']
    code=int(text(path/'exit_code.txt').strip())
    gate=dict(finite=finite,window_complete=len(tail)==1000,converged=r.get('converged')=='true',
              mass=mass<1e-10 if corrected else mass<=1e-10,Mach=ext['Mach']<.05,
              density=ext['max_density_deviation']<=1e-6,std=std<=1e-6,span=span<=5e-6,
              cross=cross<=1e-12,positive_flux=tail[-1]['J']>0,exit=code==0,
              section=tail[-1].get('section_relative_difference',0)<=1e-5,material=r.get('material_unchanged')=='true')
    if corrected:gate['ledger_agreement']=ext['mass_ledger_agreement']<=1e-13
    K=float(r['K_LBM_m3'] if smooth else r['Keff_m3'])
    assert abs(1e-6*tail[-1]['J']/1e5/K-1)<1e-12
    return dict(path=str(path.relative_to(ROOT)),K_m3=K,rows=n,extrema=ext,mass_from_legacy_mass_column=mass_recomputed,
                window_std=std,window_span=span,window_cross=cross,checks=gate,
                scalar_PASS=all(gate.values()),source_PASS=r['PASS'],exit_code=code,
                raw_result=r)

def main():
    cm=js(CRUN/'manifest.json');completion=js(CRUN/'completion.json');checks=[]
    def binding(path,h,label,mandatory=True):
        p=Path(path);actual=sha(p) if p.is_file() else None
        checks.append(dict(path=str(p),expected=h,actual=actual,matches=h==actual,label=label,mandatory_for_data_review=mandatory))
        if mandatory:assert actual==h,(label,p)
    for filename,h in completion['output_sha256'].items():binding(CRUN/filename,h,'C_saved_output')
    for path,h in cm['source_files'].items():binding(Path(path),h,'C_source')
    binding(cm['binary']['path'],cm['binary']['sha256'],'C_executable')
    for path,h in cm['current_library_files'].items():binding(Path(path),h,'C_saved_OpenLB_source_library')
    for path,h in cm['dynamic_libraries'].items():binding(Path(path),h,'C_current_dynamic_library',False)

    base=GRID/'build/generated/g2_ex240_dx1p25.cpp';new=CROOT/'src/fine_T_statfix_C.cpp'
    assert sha(base)=='898cbe394a4528ae3ef925002ccb16eb33da433651276457e5913b128174281e'
    diff=''.join(difflib.unified_diff(text(base).splitlines(True),text(new).splitlines(True),fromfile=str(base),tofile=str(new)))
    (OUT/'C_statistics_only.diff').write_text(diff)
    changed=[s[1:] for s in diff.splitlines() if s.startswith(('+','-')) and not s.startswith(('+++','---'))]
    physical_tokens=['collideAndStream','setBouzidiBoundary','ForcedBGK','defineRho','defineU','defineField','materialAt(','const T dx =','const T dt =']
    assert not any(token in s for s in changed for token in physical_tokens)
    oldpath=ARCH/'runs/dx1p25/EX240_perpendicular/steady/diagnostics.csv'
    sha(oldpath);sha(CRUN/'diagnostics.csv');mismatch=0;common=None;count=0
    with oldpath.open() as a,(CRUN/'diagnostics.csv').open() as b:
        aa=csv.DictReader(a);bb=csv.DictReader(b);common=set(aa.fieldnames)&set(bb.fieldnames)
        for x,y in itertools.zip_longest(aa,bb):
            assert x is not None and y is not None
            mismatch+=sum(x[k]!=y[k] for k in common);count+=1
    assert mismatch==0 and count==29549 and len(common)==20
    save('C_physics_compatibility.json',dict(statistics_only_diff_lines=len(diff.splitlines()),physical_operations_changed=False,
         source_hashes_bound=True,common_diagnostic_columns=sorted(common),identical_rows=count,mismatched_values=mismatch,
         interpretation='All saved legacy diagnostics match; approved changes measure mass and acceptance only. Not a proof of every unsaved lattice population.'))

    records=[];geometries={};manifest_hashes=[];readers=[]
    for tag,dx in [('5',5.),('2p5',2.5),('1p25',1.25)]:
        for case in ['Smooth75','EX240_parallel','EX240_perpendicular']:
            smooth=case=='Smooth75';original=ARCH/'runs'/('dx'+tag)/case/'steady'
            selected=CRUN if tag=='1p25' and case=='EX240_perpendicular' else original
            rec=scalar(selected,smooth,selected==CRUN);assert rec['scalar_PASS']
            rec.update(grid_tag=tag,dx_nm=dx,case=case,used_scheme_C=selected==CRUN)
            geometry_key=(dx,smooth)
            if geometry_key not in geometries:geometries[geometry_key]=geometry(dx,smooth)
            expected=geometries[geometry_key];r=rec['raw_result'];ba=kv(selected/'boundary_audit.txt')
            assert expected['fluid_nodes']==int(r['fluid_nodes'])
            assert expected['candidate_links']==int(r['candidate_links'])==int(r['installed_links'])
            assert all(abs(float(r[k])-.5)<=1e-10 for k in ['q_min','q_max'])
            assert int(r['fallback_count'])==int(r['unresolved_links'])==0
            assert ba.get('geometry_PASS')=='true' and ba.get('q_audit_PASS')=='true'
            rec['independent_geometry_PASS']=True
            if selected!=CRUN:
                mt=text(original/'run_manifest.txt')
                for line in mt.splitlines():
                    match=re.fullmatch(r'([0-9a-f]{64})\s+(.+)',line)
                    if match:
                        pp,mapping=resolve_old(match[2]);binding(pp,match[1],'G2_source_binary_protocol')
                        manifest_hashes.append(dict(old_path=match[2],current_path=str(pp),mapping=mapping,sha256=match[1]))
                pre=kv(original.parent/'precheck/result.txt');assert pre['geometry_PASS']=='true' and pre['q_audit_PASS']=='true'
                assert int(text(original.parent/'precheck/exit_code.txt'))==0
            if smooth:
                sha(selected/'velocity_profile.csv')
                with (selected/'velocity_profile.csv').open() as f:profile=list(csv.DictReader(f))
                err=[];truth=[]
                for rr in profile:
                    z=float(rr['z']);analytic=1e5*z*(75e-9-z)/(2e-6)
                    truth.append(analytic);err.append(float(rr['u_LBM'])-analytic)
                rec['profile_L2_relative']=math.sqrt(math.fsum(x*x for x in err)/math.fsum(x*x for x in truth))
                rec['smooth_K_relative']=abs(rec['K_m3']/(75e-9)**3*12-1)
                # Original Step3 deliberately does not reject an otherwise valid coarse sample for analytic error.
                assert rec['profile_L2_relative']<.02 and rec['smooth_K_relative']<.02
            else:
                pvd=next((selected/'vtkData').glob('*.pvd'))
                readers.append(dict(case=case,dx_nm=dx,result_directory=str(selected),reader=str(pvd),final_step=int(r['steps_completed']),fluid_nodes=expected['fluid_nodes']))
            records.append(rec)
    oldfail=scalar(ARCH/'runs/dx1p25/EX240_perpendicular/steady')
    assert not oldfail['scalar_PASS'] and not oldfail['checks']['mass'] and oldfail['exit_code']==3
    save('historical_failed_record_preserved.json',oldfail)
    gs={}
    by={(r['dx_nm'],r['case']):r['K_m3'] for r in records}
    for dx in [5.,2.5,1.25]:
        ks=by[dx,'Smooth75'];kp=by[dx,'EX240_parallel'];kt=by[dx,'EX240_perpendicular']
        gs[dx]=dict(K_smooth=ks,K_parallel=kp,K_perpendicular=kt,eta_parallel=kp/ks,eta_perpendicular=kt/ks,anisotropy=kp/kt)
    gci=[]
    for name in gs[1.25]:
        f,m,c=[gs[dx][name] for dx in [1.25,2.5,5.]];d21=m-f;d32=c-m
        assert d21*d32>0 and abs(d21)>1e-14*max(abs(f),abs(m),abs(c))
        order=math.log(abs(d32/d21),2);assert order>0
        den=2**order-1;g21=1.25*abs((m-f)/f)/den;g32=1.25*abs((c-m)/m)/den
        ratio=g32/(2**order*g21);ext=f+(f-m)/den
        gci.append(dict(metric=name,fine=f,medium=m,coarse=c,observed_order=order,extrapolated=ext,
                        GCI_fine_percent=g21*100,ea_percent=abs((m-f)/f)*100,e_ext_percent=abs((ext-f)/ext)*100,
                        legacy_ratio=ratio,legacy_ratio_is_independent_asymptotic_evidence=False,
                        ratio_identity_residual=ratio-abs(f/m),legacy_ratio_threshold_satisfied=.95<=ratio<=1.05,
                        medium_to_fine_relative=abs(m/f-1)))
    assert all(r['GCI_fine_percent']<=2 for r in gci if r['metric'] in ['K_parallel','K_perpendicular'])
    assert all(r['medium_to_fine_relative']<=.01 for r in gci if r['metric'].startswith('eta') or r['metric']=='anisotropy')
    save('nine_record_review.json',records);save('independent_geometry.json',list(geometries.values()))
    save('conditional_grid_estimates.json',gci);save('original_manifest_aliases.json',manifest_hashes)
    save('field_readers.json',readers);save('binding_review.json',checks)
    save('review_read_inputs_sha256.json',INPUTS)
    save('scalar_geometry_verdict.json',dict(review_id='C_H75_REVIEW_20261101_v1',new_solver_run_id=None,
        scheme_C_scalar_gate='PASS',scheme_C_geometry_PASS=True,scheme_C_full_legacy_trajectory_compatible=True,
        selected_nine_record_scalar_gate='PASS',selected_nine_record_geometry_PASS=True,
        historical_legacy_size_and_GCI_arithmetic_criteria_satisfied=True,
        qualified_scope='existing_h75_d100_w120_periodic_discrete_benchmark_with_conditional_spatial_estimates',
        exact_environment_reproduction=False,current_dynamic_library_mismatches=[r for r in checks if r['label']=='C_current_dynamic_library' and not r['matches']],
        independent_asymptotic_confirmation=False,strict_error_bound_established=False,
        historical_failed_record_unchanged=True,historical_release_recovered=False,
        saved_field_readback_pending=True,new_simulation_started=False,new_reference_for_unseen_geometry=False))
    print('Scalar, geometry, source and compatibility review complete; field readback remains.')

if __name__=='__main__':main()
