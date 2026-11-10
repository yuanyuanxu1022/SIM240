#!/usr/bin/env python3
"""Read saved six runs only. No imports of solver/checker/fit; write here only."""
from pathlib import Path
import csv, json, hashlib, math, statistics, datetime

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
D2 = ROOT / 'CASE/D_series/D2_groove_error_map'
RES = D2 / 'results'
NAMES = ['h100_d100_dx5_P', 'h100_d100_dx5_T',
         'h75_d100_dx5_buildB_P', 'h75_d100_dx5_buildB_T',
         'h75_d100_dx5_P', 'h75_d100_dx5_T']

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()

def kv(p):
    return dict(line.split('=',1) for line in p.read_text().splitlines() if '=' in line)

def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def table(name,rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def close(a,b):
    return math.isclose(a,b,rel_tol=2e-12,abs_tol=1e-30)

def bias(pred,ref): return 100*(pred/ref-1)

# Protect ALL files in these six run directories, including fields (hash only).
paths=[p for n in NAMES for p in (RES/n).rglob('*') if p.is_file()]
paths += [D2/'src/d2_groove_error_map.cpp',D2/'build/d2_groove_error_map',D2/'build/d2_groove_error_map.d',
          D2/'scripts/run_closure_blindtest_20261106.sh',D2/'scripts/check_closure_blindtest_20261106.py',
          D2/'analysis_fit_v2.py',RES/'closure_blindtest_verdict.json',RES/'closure_blindtest_20261106.csv']
for folder,names in {
 'PAPER1_bound_closure_review_20261105':['REPORT.md','source_manifest.json','final_verification.json','proposed_geometry_scalar_checks.csv'],
 'PAPER1_闭环方案_20261105':['REPORT.md','bound_check_44_points.csv'],
 'Historical_build_adjudication_20261028':['REPORT.md'],
 'PAPER1_claim_final_review_20261105':['REPORT.md','bound_records44_recomputed.csv'],
}.items():
    paths += [ROOT/'docs/reports'/folder/name for name in names if (ROOT/'docs/reports'/folder/name).exists()]
paths += [ROOT/'docs/reports'/n for n in ['SIM240_中文稿_导师审阅版_20261022.md','SIM240_First_Paper_English_20261028.md']]
manifest={str(p.relative_to(ROOT)):digest(p) for p in sorted(set(paths))}
mf=OUT/'source_manifest.json'
if mf.exists():
    assert json.loads(mf.read_text())==manifest, 'protected inputs drifted since first audit'
else: dump('source_manifest.json',manifest)

binary=digest(D2/'build/d2_groove_error_map')
audits=[]; comparisons=[]; chronology=[]
for name in NAMES:
    p=RES/name; r=kv(p/'steady/result.txt'); m=kv(p/'steady/run_manifest.txt')
    pre=kv(p/'precheck/result.txt'); b=kv(p/'steady/boundary_audit.txt'); bp=kv(p/'precheck/boundary_audit.txt')
    with (p/'steady/diagnostics.csv').open() as f:
        rows=[{k:float(v) for k,v in x.items()} for x in csv.DictReader(f)]
    first,last=rows[0],rows[-1]; win=rows[-1000:]; j=[x['J'] for x in win]
    dr='Jy' if name.endswith('_P') else 'Jx'; cross='Jx' if dr=='Jy' else 'Jy'
    mean=statistics.mean(j); std=statistics.stdev(j)/abs(mean); span=(max(j)-min(j))/abs(mean)
    cr=max(abs(x[cross]) for x in win)
    mass=max(abs((x['mass']-first['mass'])/first['mass']) for x in rows)
    den=max(x['max_density_deviation'] for x in rows); mach=max(x['Mach'] for x in rows)
    q=lambda x: abs(x['Q_section1']-x['Q_section2'])/max(abs(x['Q_section1']),abs(x['Q_section2'])) if max(abs(x['Q_section1']),abs(x['Q_section2'])) else 0.
    section=q(last)
    h,d,w,dx=(float(r[k]) for k in ['mesa_gap_m','groove_depth_m','groove_width_m','dx_m'])
    lx,ly,dt,tau,a=(float(r[k]) for k in ['Lx_m','Ly_m','dt_s','tau','acceleration_m_s2'])
    nu=(tau-.5)*dx*dx/(3*dt); k=nu*last[dr]/a
    vol=lx*ly*h+w*ly*d; nodes=round(lx/dx)*round(ly/dx)*round(h/dx)+round(w/dx)*round(ly/dx)*round(d/dx)
    expected_h=100. if name.startswith('h100') else 75.
    checks={
      'precheck_exit_zero':(p/'precheck/exit_code.txt').read_text().strip()=='0',
      'steady_exit_zero':(p/'steady/exit_code.txt').read_text().strip()=='0',
      'native_precheck_flags':all(pre[x]=='true' for x in ['geometry_PASS','converter_PASS','q_audit_PASS']),
      'native_result_flags':all(r[x]=='true' for x in ['PASS','converged','finite','material_unchanged']),
      'row_count_and_steps':len(rows)==int(r['steps_completed'])+1 and all(x['step']==i for i,x in enumerate(rows)),
      'all_finite':all(math.isfinite(v) for x in rows for v in x.values()) and all(x['finite']==1 for x in rows),
      'time_step':all(close(x['time_s'],i*dt) for i,x in enumerate(rows)),
      'main_component':all(x['J']==x[dr] for x in rows),
      'K_from_converter_and_final_J':close(k,float(r['Keff_m3'])),
      'expected_geometry_and_parameters': all(close(v,t) for v,t in [(h,expected_h*1e-9),(d,100e-9),(w,120e-9),(dx,5e-9),(lx,240e-9),(ly,240e-9),(tau,1),(a,1e5),(nu,1e-6)]),
      'direction_and_model':r['direction']==('parallel' if dr=='Jy' else 'perpendicular') and r['descriptor']=='D3Q19_FORCE' and r['collision']=='ForcedBGK' and r['periodicity']=='x_y',
      'manifest_parameters':all(close(float(m[key]),val) for key,val in [('dx_nm',5),('tau',1),('acceleration_m_s2',1e5),('mesa_gap_nm',expected_h),('groove_depth_nm',100)]),
      'pre_and_steady_same_binary':kv(p/'precheck/run_manifest.txt')['binary_sha256']==m['binary_sha256'],
      'fluid_node_count':all(int(x)==nodes for x in [r['fluid_nodes'],b['material_1'],bp['material_1'],pre['fluid_nodes']]),
      'volume_roundoff_gate':abs(float(r['fluid_volume_m3'])/vol-1)<=1e-10,
      'q_and_boundary_counts':all(int(b[x])==int(b['candidate_links']) for x in ['valid_distance_links','installed_links']) and all(float(b[x])==.5 for x in ['q_min','q_max','installed_q_min','installed_q_max']) and all(int(b[x])==0 for x in ['geometric_fallback_count','missing_fluid_neighbour_fallback_count','unresolved_link_count']) and bp==b,
      'mass_gate':mass<1e-10, 'density_gate':den<=1e-6,'Mach_gate':mach<.05,
      'window_std_gate':std<=1e-6,'window_span_gate':span<=5e-6,'cross_flux_gate':cr<=1e-12,
      'final_section_gate':section<=1e-5, 'positive_J':last['J']>0,
      'reported_maxima_match':all(close(v,float(r[key])) for v,key in [(mass,'max_mass_abs_relative'),(den,'max_density_deviation'),(mach,'max_Mach'),(std,'window_main_rel_std'),(span,'window_main_rel_span'),(cr,'window_cross_abs_max'),(section,'section_relative_difference')]),
      'raw_mass_error_column':all(close((x['mass']-first['mass'])/first['mass'],x['mass_error']) for x in rows),
      'raw_section_difference_column':all(close(q(x),x['section_relative_difference']) for x in rows),
      'log_has_final_record':f"step={r['steps_completed']}" in (p/'steady/run.log').read_text() and f"Keff={r['Keff_m3']}" in (p/'steady/run.log').read_text(),
    }
    if 'nu_phys_m2_s' in r:
        checks['reported_nu_from_converter']=close(nu,float(r['nu_phys_m2_s']))
    # Recompute stopping window before final step; don't rely on saved window statistics.
    prev=rows[-1001:-1]; pj=[x['J'] for x in prev]; pm=statistics.mean(pj)
    prev_pass=statistics.stdev(pj)/abs(pm)<=1e-6 and (max(pj)-min(pj))/abs(pm)<=5e-6 and max(abs(x[cross]) for x in prev)<=1e-12
    checks['penultimate_window_not_converged']=not prev_pass
    # All full windows' stopping conditions from raw J; stable two-pass centered sums.
    earliest=None
    for end in range(1000,len(rows)+1):
        vals=[x['J'] for x in rows[end-1000:end]]; mn=sum(vals)/1000
        s=math.sqrt(sum((v-mn)**2 for v in vals)/999)/abs(mn)
        sp=(max(vals)-min(vals))/abs(mn)
        if s<=1e-6 and sp<=5e-6 and max(abs(x[cross]) for x in rows[end-1000:end])<=1e-12:
            earliest=end-1;break
    checks['first_converged_step_matches']=earliest==int(r['steps_completed'])
    aud={'case':name,'recorded_run_id':m['case_id'],'scope':'four_new' if name in NAMES[:4] else 'historical_control',
         'steps':int(r['steps_completed']),'rows':len(rows),'K_recomputed_m3':k,'binary_sha256':m['binary_sha256'],
         'matches_current_binary':m['binary_sha256']==binary,'current_source_bound_to_executable':False,
         'physical_nu_reported_in_result':'nu_phys_m2_s' in r,
         'saved_geometry_PASS':b['geometry_PASS'],'geometry_count_and_boundary_record_checks':checks['fluid_node_count'] and checks['q_and_boundary_counts'],
         'max_mass_relative':mass,'max_density_deviation':den,'max_Mach':mach,'window_std':std,'window_span':span,'window_cross_abs':cr,
         'section_rel_final':section,'section_rel_max_transient':max(q(x) for x in rows),
         'Q1_final_m3_s':last['Q_section1'],'Q2_final_m3_s':last['Q_section2'],
         'J_times_transverse_period_m3_s':last['J']*(lx if dr=='Jy' else ly),
         'fluid_nodes':nodes,'checks':checks,'all_scoped_checks_pass':all(checks.values()),
         'formal_NUMERICAL_GATE':'NOT_EVALUATED_BY_THIS_AUDIT','reference_qualified':False,
         'field_arrays_decoded':False,'OpenLB_version_log':[line for line in (p/'steady/run.log').read_text().splitlines() if 'Version  :' in line]}
    audits.append(aud)
    lc_y=((h+d)**3+h**3)/24;lc_x=h**3*(h+d)**3/(6*(h**3+(h+d)**3))
    lc=lc_y if dr=='Jy' else lc_x;fac=1/(1+(1.7685*(d/w)**1.6331 if dr=='Jy' else .4900*(d/w)**.6990));v2=lc*fac
    comparisons.append({'case':name,'role':aud['scope'],'h_nm':expected_h,'d_nm':100,'w_nm':120,'P_nm':240,'dx_nm':5,'component':'Kyy' if dr=='Jy' else 'Kxx','K_LB_m3':k,'K_LC_m3':lc,'K_V2_m3':v2,'LC_bias_percent':bias(lc,k),'V2_bias_percent':bias(v2,k),'LB_below_LC':k<lc})
    for part in ['precheck/run_manifest.txt','precheck/result.txt','steady/result.txt']:
        f=p/part;chronology.append({'path':str(f.relative_to(ROOT)),'mtime_local':datetime.datetime.fromtimestamp(f.stat().st_mtime).astimezone().isoformat(),'sha256':digest(f),'evidence_kind':'mutable_filesystem_metadata_not_trusted_timestamp'})

build=[]; builddiag=[]
for direction in ['P','T']:
    old=RES/f'h75_d100_dx5_{direction}';new=RES/f'h75_d100_dx5_buildB_{direction}'
    for f in sorted(x for x in old.rglob('*') if x.is_file()):
        rel=f.relative_to(old); nf=new/rel
        build.append({'direction':direction,'relative_file':str(rel),'new_file_exists':nf.exists(),'byte_identical':nf.exists() and digest(f)==digest(nf)})
    with (old/'steady/diagnostics.csv').open() as f: oldrows=list(csv.DictReader(f))
    with (new/'steady/diagnostics.csv').open() as f: newrows=list(csv.DictReader(f))
    assert len(oldrows)==len(newrows) and oldrows[0].keys()==newrows[0].keys()
    for col in oldrows[0]:
        av=[float(x[col]) for x in oldrows];bv=[float(x[col]) for x in newrows]
        diff=[abs(x-y) for x,y in zip(av,bv)];den=max(map(abs,av))
        builddiag.append(dict(direction=direction,column=col,rows=len(av),different_values=sum(x!=y for x,y in zip(av,bv)),max_abs_difference=max(diff),max_abs_difference_over_column_max=max(diff)/den if den else 0))
ratios=[]
for h,prefix in [(100,'h100_d100_dx5_'),(75,'h75_d100_dx5_buildB_')]:
    p=next(x for x in comparisons if x['case']==prefix+'P');t=next(x for x in comparisons if x['case']==prefix+'T')
    ref=p['K_LB_m3']/t['K_LB_m3'];v=p['K_V2_m3']/t['K_V2_m3'];lc=p['K_LC_m3']/t['K_LC_m3']
    ratios.append({'h_nm':h,'A_LB':ref,'A_V2':v,'A_LC':lc,'V2_bias_percent':bias(v,ref),'LC_bias_percent':bias(lc,ref),'legacy_reversed_V2_bias_percent':bias(ref,v)})
residual_change={comp:abs(next(x for x in comparisons if x['h_nm']==100 and x['component']==comp)['V2_bias_percent']-next(x for x in comparisons if x['h_nm']==75 and x['component']==comp)['V2_bias_percent']) for comp in ['Kxx','Kyy']}
for f in [ROOT/'docs/reports/PAPER1_bound_closure_review_20261105/proposed_geometry_scalar_checks.csv',D2/'scripts/run_closure_blindtest_20261106.sh',D2/'scripts/check_closure_blindtest_20261106.py',D2/'src/d2_groove_error_map.cpp']:
    chronology.append({'path':str(f.relative_to(ROOT)),'mtime_local':datetime.datetime.fromtimestamp(f.stat().st_mtime).astimezone().isoformat(),'sha256':digest(f),'evidence_kind':'mutable_filesystem_metadata_not_trusted_timestamp'})
dump('case_audits.json',audits);table('comparison.csv',comparisons);table('ratios.csv',ratios);table('build_file_comparison.csv',build);table('chronology.csv',chronology)
table('build_diagnostic_differences.csv',builddiag)
with (ROOT/'docs/reports/PAPER1_bound_closure_review_20261105/proposed_geometry_scalar_checks.csv').open() as f:
    prediction=next(x for x in csv.DictReader(f) if x['label']=='A')
dump('prediction_identity.json',{
    'previous_prediction_source':'docs/reports/PAPER1_bound_closure_review_20261105/proposed_geometry_scalar_checks.csv',
    'previous_prediction':prediction,
    'matches_rounded_fixed_formula':all(close(float(prediction[x['component']+'_V2_m3']),x['K_V2_m3']) for x in comparisons[:2]),
    'coefficient_refit_in_this_audit':False,
    'new_h_not_in_old_D2_calibration_grid':True,
    'complete_team_nonexposure_verified':False,
    'immutable_prerun_contract_recovered':False,
    'strict_blind_test_certified':False,
    'recommended_description':'fixed-model comparison at an additional gap, outside the nine-geometry coefficient calibration set; no claim of certified blindness'})
dump('summary.json',{'new_cases':4,'historical_controls':2,'all_scoped_checks_pass':all(x['all_scoped_checks_pass'] for x in audits),'failed_checks':{x['case']:[k for k,v in x['checks'].items() if not v] for x in audits},'primary_K_abs_le_10_percent':all(abs(x['V2_bias_percent'])<=10 for x in comparisons[:2]),'residual_change_percentage_points':residual_change,'structural_le_5pp':max(residual_change.values())<=5,'formal_reference_qualified':False,'new_simulations':0,'new_fits':0,'current_binary_sha256':binary,'build_file_differences':[x for x in build if not x['byte_identical']]})
changed=[name for name,sha in manifest.items() if digest(ROOT/name)!=sha]
dump('verification.json',{'protected_files':len(manifest),'changed_inputs':changed,'all_scoped_checks_pass':all(x['all_scoped_checks_pass'] for x in audits),'audit_output_only':True,'field_files_hashed_not_decoded':True,'simulation_or_fit_run':False,'formal_gate_advanced':False})
print(json.dumps(json.loads((OUT/'summary.json').read_text()),ensure_ascii=False,indent=2))
