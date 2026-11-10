#!/usr/bin/env python3
"""Read-only first-paper file/scalar/diagnostic recheck. Python standard library.

Never launches a solver, shell, optimizer, compilation, network, or file writer.
Legacy result PASS and current file checks are distinct from reference accuracy.
"""
from pathlib import Path
import csv,hashlib,json,math,statistics,sys

BASE=Path(__file__).resolve().parent
PROJECT=BASE/'project'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def kv(p):return dict(line.split('=',1) for line in p.read_text().splitlines() if '=' in line)
def bias(pred,ref):return 100*(pred/ref-1)
def close(a,b):return math.isclose(a,b,rel_tol=2e-12,abs_tol=1e-30)

def main():
    package=json.loads((BASE/'package_manifest.json').read_text());bad=[]
    for rel,expected in package.items():
        p=BASE/rel
        if not p.resolve().is_relative_to(BASE):raise ValueError('Invalid manifest path')
        if not p.is_file() or sha(p)!=expected:bad.append(rel)
    if bad:raise ValueError('File integrity failed: '+json.dumps(bad,ensure_ascii=False))
    old=rows(PROJECT/'docs/reports/PAPER1_claim_final_review_20261105/recomputed_44_records.csv')
    locations=[Path(x['source']).parent for x in old]
    locations += [Path('CASE/D_series/D2_groove_error_map/results')/n/'steady' for n in ['h100_d100_dx5_P','h100_d100_dx5_T','h75_d100_dx5_buildB_P','h75_d100_dx5_buildB_T']]
    computed=[]
    for rel in locations:
        p=PROJECT/rel;r=kv(p/'result.txt');m=kv(p/'run_manifest.txt')
        if (p/'exit_code.txt').read_text().strip()!='0':raise ValueError('Nonzero saved D2 exit '+str(rel))
        tau,dx,dt,a,h,d,w=(float(r[x]) for x in ['tau','dx_m','dt_s','acceleration_m_s2','mesa_gap_m','groove_depth_m','groove_width_m'])
        nu=(tau-.5)*dx**2/(3*dt);k=nu*float(r['J_main_m2_s'])/a
        if not close(k,float(r['Keff_m3'])):raise ValueError('K/J mismatch '+str(rel))
        yy=((h+d)**3+h**3)/24;xx=h**3*(h+d)**3/(6*(h**3+(h+d)**3))
        parallel=r['direction']=='parallel';lc=yy if parallel else xx
        f=1/(1+(1.7685*(d/w)**1.6331 if parallel else .4900*(d/w)**.6990))
        computed.append({'run':rel.parent.name,'component':'Kyy' if parallel else 'Kxx','K_LB_m3':k,'K_LC_m3':lc,'K_V2_m3':f*lc,'original_bias_percent':bias(lc,k),'V2_bias_percent':bias(f*lc,k),'binary_sha256':m['binary_sha256'],'LB_below_LC':k<lc})
    primary=computed[:36]  # Old table is geometry-paired, main 36 followed by 8 fine.
    # Select by saved dx rather than depending on row ordering.
    primary=[x for x in computed[:44] if '_dx5_' in x['run']]
    if len(primary)!=36:raise ValueError('Old main cohort is not 36')
    new={x['component']:x for x in computed if x['run'].startswith('h100_')}
    a_lb=new['Kyy']['K_LB_m3']/new['Kxx']['K_LB_m3'];a_v2=new['Kyy']['K_V2_m3']/new['Kxx']['K_V2_m3']
    a_bias=bias(a_v2,a_lb)
    if not close(a_bias,-6.151885459383766):raise ValueError('A convention mismatch')
    diagnostics=[]
    for name in ['h100_d100_dx5_P','h100_d100_dx5_T','h75_d100_dx5_buildB_P','h75_d100_dx5_buildB_T','h75_d100_dx5_P','h75_d100_dx5_T']:
        p=PROJECT/'CASE/D_series/D2_groove_error_map/results'/name/'steady';r=kv(p/'result.txt')
        rr=[{k:float(v) for k,v in x.items()} for x in rows(p/'diagnostics.csv')]
        if not all(math.isfinite(v) for x in rr for v in x.values()):raise ValueError('Nonfinite diagnostics '+name)
        if any(x['step']!=i for i,x in enumerate(rr)) or len(rr)!=int(r['steps_completed'])+1:raise ValueError('Step mismatch '+name)
        j=[x['J'] for x in rr[-1000:]];mean=statistics.mean(j);std=statistics.stdev(j)/abs(mean);span=(max(j)-min(j))/abs(mean)
        mass=max(abs((x['mass']-rr[0]['mass'])/rr[0]['mass']) for x in rr)
        density=max(x['max_density_deviation'] for x in rr);mach=max(x['Mach'] for x in rr)
        cross='Jx' if name.endswith('_P') else 'Jy';crossmax=max(abs(x[cross]) for x in rr[-1000:])
        last=rr[-1];qd=abs(last['Q_section1']-last['Q_section2'])/max(abs(last['Q_section1']),abs(last['Q_section2']))
        if not (std<=1e-6 and span<=5e-6 and mass<1e-10 and density<=1e-6 and mach<.05 and crossmax<=1e-12 and qd<=1e-5):raise ValueError('Saved diagnostic condition failed '+name)
        if not close(last['J'],float(r['J_main_m2_s'])):raise ValueError('Final J mismatch '+name)
        diagnostics.append({'run':name,'steps':len(rr)-1,'saved_diagnostic_conditions_satisfied':True})
    builds=[]
    for comp,dr in [('Kxx','T'),('Kyy','P')]:
        oldx=next(x for x in computed if x['run']=='h75_d100_dx5_'+dr)
        newx=next(x for x in computed if x['run']=='h75_d100_dx5_buildB_'+dr)
        builds.append({'component':comp,'difference_percent':bias(newx['K_LB_m3'],oldx['K_LB_m3'])})
    outlets=[];expected=rows(PROJECT/'docs/reports/PAPER1_formula_comparison_20261105/OpenFOAM_outlet_Q.csv')
    for rec in expected:
        cid=rec['case_id'];idx=int(cid[-1])-1 if cid.startswith('C') else None
        base='interface_static_darcy_v1'+('' if idx==0 else '_'+str(idx)) if idx is not None else 'groove_darcy_static_v1'
        endpoint=Path('two_dimensional') if rec['endpoint']=='two_dimensional' else Path('openfoam')/('GDI_output' if cid=='GDI01' else 'SDI_output')
        ff=rows(PROJECT/'CASE'/base/'runs'/rec['run_id']/endpoint/'faces.csv')
        q=math.fsum(float(x['phi_m3_s']) for x in ff if x['patch']=='xHigh')
        if not close(q,float(rec['Q_m3_s'])):raise ValueError('Outlet mismatch '+cid+' '+rec['endpoint'])
        outlets.append({'case_id':cid,'endpoint':rec['endpoint'],'Q_m3_s':q})
    data46=computed[:46]
    summary={'package_files_verified':len(package),'source_files':len(json.loads((BASE/'source_manifest.json').read_text())),
      'file_integrity_ok':True,'D2_scalar_records_recomputed':len(computed),
      'old_main_records':len(primary),'old_refined_records':8,'new_gap_records':2,'build_repeat_records':2,
      'comparison46_below_LC':all(x['LB_below_LC'] for x in data46),
      'h100':{'directions':new,'A_LB':a_lb,'A_V2':a_v2,'A_bias_percent':a_bias},
      'old_main_V2_MAE_percent':{comp:statistics.mean(abs(x['V2_bias_percent']) for x in primary if x['component']==comp) for comp in ['Kxx','Kyy']},
      'saved_diagnostic_rechecks':diagnostics,'h75_build_comparisons':builds,'outlet_faces_recomputed':outlets,
      'new_simulations':0,'new_fits':0,'scientific_gate_advanced':False,'reference_qualified':False,'strict_blind_test_certified':False}
    print(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False))

if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError,StopIteration) as e:
        print('CHECK_FAILED: '+str(e),file=sys.stderr);raise SystemExit(1)
