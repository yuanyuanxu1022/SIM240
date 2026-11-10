#!/usr/bin/env python3
"""Read-only evidence audit; writes only beside this script. Never solves or fits."""
from pathlib import Path
from collections import Counter, deque
import csv
import hashlib
import json
import math
import re
import statistics

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
READ = {}
HASH = {}
BIND = []

def sha(p):
    p = Path(p).resolve()
    if p not in HASH:
        h = hashlib.sha256()
        with p.open('rb') as f:
            for block in iter(lambda: f.read(1 << 20), b''):
                h.update(block)
        HASH[p] = h.hexdigest()
    READ[str(p)] = HASH[p]
    return HASH[p]

def text(p):
    sha(p)
    return Path(p).read_text(errors='replace')

def js(p):
    return json.loads(text(p))

def kv(p):
    return dict(line.split('=', 1) for line in text(p).splitlines()
                if '=' in line and not line.startswith('#'))

def table(p):
    sha(p)
    with Path(p).open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def save(name, value):
    p = OUT/name
    if p.exists():
        raise FileExistsError(p)
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')

def bind(p, expected, label):
    p = Path(p)
    actual = sha(p) if p.is_file() else None
    rec = dict(path=str(p), expected_sha256=expected, actual_sha256=actual,
               matches=actual==expected, label=label)
    BIND.append(rec)
    return rec['matches']

def numbers(r, key, default=None):
    v = r.get(key)
    return float(v) if v is not None else default

def audit_run(result, family, identity=None, group=None):
    result=Path(result); folder=result.parent; r=kv(result)
    # These identities describe artifact records, not distinct independent experiments.
    rec=dict(family=family, group=group, run_id=identity or r.get('run_id',folder.parent.name),
             result_path=str(result.relative_to(ROOT)), result_sha256=sha(result),
             direction=r.get('direction'), recorded_PASS=r.get('PASS'),
             recorded_NUMERICAL_GATE=r.get('NUMERICAL_GATE','NOT_RECORDED'),
             recorded_RESULT_PASS=r.get('RESULT_PASS','NOT_RECORDED'),
             recorded_geometry_PASS=r.get('geometry_PASS','NOT_RECORDED'))
    for col,key,scale in [('h_nm','mesa_gap_m',1e9),('d_nm','groove_depth_m',1e9),
                         ('w_nm','groove_width_m',1e9),('P_nm','Lx_m',1e9),
                         ('Ly_nm','Ly_m',1e9),('dx_nm','dx_m',1e9),('K_m3','Keff_m3',1)]:
        val=numbers(r,key)
        rec[col]=None if val is None else val*scale
    a=numbers(r,'acceleration_m_s2',1e5); nu=numbers(r,'nu_phys_m2_s',1e-6)
    Jkey='J_main_m2_s' if 'J_main_m2_s' in r else 'J_m2_s'
    J=numbers(r,Jkey); K=numbers(r,'Keff_m3',nu*J/a if J is not None else None)
    rec.update(K_m3=K,acceleration_m_s2=a,nu_m2_s=nu,
               K_from_J_m3=None if J is None else nu*J/a,
               K_identity_relative=None if J is None or K is None else abs(nu*J/a/K-1))
    exitfile=folder/'exit_code.txt'
    rec['independent_exit']=int(text(exitfile).strip()) if exitfile.exists() else None
    pre=folder.parent/'precheck/result.txt'
    if pre.exists():
        pp=kv(pre);rec['precheck']={k:pp.get(k) for k in ['geometry_PASS','converter_PASS','q_audit_PASS']}
    manifest=folder/'run_manifest.txt'
    if manifest.exists():
        m=kv(manifest)
        rec['manifest_fields_present']={k:k in m for k in ['binary_sha256','source_sha256','generated_source_sha256','openlb_commit','compiler','compile_flags']}
        rec['manifest_case_id']=m.get('case_id')
        rec['binary_sha256']=m.get('binary_sha256')
        if m.get('binary') and m.get('binary_sha256'):
            rec['current_binary_matches_recorded']=bind(Path(m['binary']),m['binary_sha256'],'recorded_binary_'+family)
    boundary=folder/'boundary_audit.txt'
    if boundary.exists():
        bb=kv(boundary)
        rec['boundary_audit_record']={k:v for k,v in bb.items() if 'PASS' in k or 'fallback' in k or 'unresolved' in k or k in ['candidate_links','installed_links']}
    geometric_keys=['candidate_links','installed_links','fallback_count','unresolved_links','q_min','q_max','fluid_nodes','nominal_volume_m3','fluid_volume_m3']
    rec['geometry_record']={k:r.get(k) for k in geometric_keys}
    gp=[]
    if all(k in r for k in ['candidate_links','installed_links']):gp.append(r['candidate_links']==r['installed_links'])
    for k in ['fallback_count','unresolved_links']:
        if k in r:gp.append(float(r[k])==0)
    if all(k in r for k in ['q_min','q_max']):gp.extend(abs(float(r[k])-.5)<=1e-10 for k in ['q_min','q_max'])
    if all(k in r for k in ['fluid_nodes','dx_m','nominal_volume_m3']):
        rec['node_volume_relative']=abs(float(r['fluid_nodes'])*float(r['dx_m'])**3/float(r['nominal_volume_m3'])-1)
        gp.append(rec['node_volume_relative']<=1e-10)
    rec['saved_geometry_evidence_consistent']=all(gp) if gp else None

    diag=folder/'diagnostics.csv'
    if diag.exists():
        sha(diag)
        win=int(r.get('window_steps',1000)); window=deque(maxlen=win)
        maxima={k:0.0 for k in ['mass_error','Mach','max_density_deviation','corrected_mass_error','delta_mass_error','mass_ledger_agreement']}
        all_finite=True;continuous=True;n=0;first_mass=None;mass_recomputed=0.;last=None
        with diag.open() as f:
            for row in csv.DictReader(f):
                numeric={k:float(v) for k,v in row.items() if v not in ['true','false']}
                all_finite &= all(math.isfinite(v) for v in numeric.values()) and row.get('finite','1') not in ['0','false']
                if 'step' in numeric:continuous &= numeric['step']==n
                if first_mass is None:first_mass=numeric['mass']
                mass_recomputed=max(mass_recomputed,abs((numeric['mass']-first_mass)/first_mass))
                for k in maxima:
                    if k in numeric:maxima[k]=max(maxima[k],abs(numeric[k]))
                window.append(numeric);n+=1;last=numeric
        vals=[v['J'] for v in window];mean=math.fsum(vals)/len(vals)
        relstd=statistics.stdev(vals)/abs(mean) if len(vals)>1 and mean else None
        relspan=(max(vals)-min(vals))/abs(mean) if mean else None
        cross_col='Jx' if r.get('direction')=='parallel' else 'Jy'
        cross=max(abs(v[cross_col]) for v in window) if cross_col in last and not str(r.get('direction','')).startswith('angle') else None
        masskey='corrected_mass_error' if r.get('mass_gate_statistic')=='Neumaier_physical_mass' else 'mass_error'
        # Recompute only recorded scalar gates; do not pretend to re-enumerate full geometry/VTK.
        checks=dict(finite=all_finite,step_sequence=continuous,window_complete=len(window)==win,
            converged_record=r.get('converged')=='true',window_std=relstd is not None and relstd<=1e-6,
            window_span=relspan is not None and relspan<=5e-6,
            mass=maxima[masskey]<1e-10,density=maxima['max_density_deviation']<=1e-6,
            Mach=maxima['Mach']<.05,main_flux=last['J']>0,
            section=last.get('section_relative_difference',0)<=1e-5,
            independent_exit=rec['independent_exit']==0)
        if cross is not None:checks['cross_flux']=cross<=1e-12
        if masskey=='corrected_mass_error':checks['ledger_agreement']=maxima['mass_ledger_agreement']<=1e-13
        rec['scalar_recheck']=dict(diagnostic_rows=n,window_steps=win,all_saved_finite=all_finite,
            maxima=maxima,legacy_mass_from_mass_column=mass_recomputed,last_J=last['J'],
            final_window_rel_std=relstd,final_window_rel_span=relspan,final_window_cross_abs_max=cross,
            final_section_relative_difference=last.get('section_relative_difference'),
            std_difference_from_saved=abs(relstd-float(r.get('window_main_rel_std',relstd))),
            last_J_difference_relative=None if J is None else abs(last['J']/J-1),
            checks=checks,all_checked_scalar_gates_satisfied=all(checks.values()))
    return rec

def main():
    s=ROOT/'docs/reports/SIM240_Supplementary_Methods_20261024'
    inventory=table(s/'Table_S1_run_inventory.csv')
    records=[]
    for rr in inventory:
        rec=audit_run(ROOT/rr['result_path'],'D2_D3_S1',rr['run_id'],rr['group'])
        rec['S1_K_matches_raw']=math.isclose(rec['K_m3'],float(rr['K_m3']),rel_tol=1e-13)
        rec['log_path']=rr['log_path'];rec['log_style']=rr['log_style']
        log=text(ROOT/rr['log_path'])
        rec['log_nonempty']=bool(log.strip())
        if rr['log_style']=='shared_batch':rec['shared_log_contains_full_manifest_id']=rec['manifest_case_id'] in log
        if rr['group']=='main':
            rec['model_data_role']='calibration' if round(rec['h_nm']) in [50,75,125] and round(rec['d_nm']) in [25,50,100] else 'seen_during_model_selection'
        else:rec['model_data_role']='seen_supporting_control_or_refinement'
        records.append(rec)
    for rr in table(s/'Table_S4_grid_archive.csv'):
        rec=audit_run(ROOT/rr['result_path'],'G2_historical_grid',rr['grid']+'_'+rr['case'],'historical_grid')
        # Smooth archive does not explicitly record a groove height; use its declared case identity only.
        rec['table_case']=rr['case'];rec['table_grid']=rr['grid'];records.append(rec)
    croot=ROOT/'CASE/03_grid_convergence/G2_EX240_fine_T_statfix_C_v1/runs/fine_t_C_20261014T151036+0800'
    rec=audit_run(croot/'result.txt','G2_scheme_C','fine_t_C_20261014T151036+0800','corrected_mass_ledger')
    cm=js(croot/'manifest.json');completion=js(croot/'completion.json')
    rec['manifest_formal_reference_accepted']=cm['formal_reference_accepted']
    rec['completion_formal_reference_accepted']=completion['formal_reference_accepted']
    rec['historical_release_path_exists']=(ROOT/'CASE/reports/fine_T_C_release_20261014_v1/RELEASE.md').exists()
    for name,h in completion['output_sha256'].items():bind(croot/name,h,'scheme_C_output')
    for section in ['source_files','historical_inputs','current_library_files','dynamic_libraries']:
        x=cm.get(section,{})
        if isinstance(x,dict):
            for p,h in x.items():
                if isinstance(h,str) and re.fullmatch('[0-9a-f]{64}',h):bind(Path(p),h,'scheme_C_'+section)
    records.append(rec)
    for rr in table(s/'Table_S3_periodic_checks.csv'):
        rec=audit_run(ROOT/rr['result_path'],'G4_period_linearity',rr['run_id'],'period_or_force_control')
        rec['nx_periods']=int(rr['nx']);records.append(rec)
    g3=ROOT/'CASE/04_parameter_study/G3_EX240_height_sweep/results'
    for p in sorted(g3.glob('g3h_*/result.txt')):
        if 'formal' in p.parent.name or 'baseline' in p.parent.name:
            records.append(audit_run(p,'G3_height',p.parent.name,'fixed_grid_height'))

    d4=ROOT/'CASE/D_series/D4_variable_groove_transport_20261023'
    plans=table(d4/'protocol/candidate_cases.csv')
    byid={r['planned_case_id']:r for r in plans}
    old_acceptance={
      'foundation_20261023_v1':'docs/reports/D4_foundation_acceptance_20261023/complete',
      'development_screen_20261023_v1':'docs/reports/D4_prediction_readiness_20261024/screen_acceptance',
      'development_remaining14_20261024_v1':'docs/reports/D4_remaining14_acceptance_20261024/scalar_acceptance',
      'development_grid_mid6_20261024_v1':'docs/reports/D4_grid_mid6_acceptance_20261024/independent/analysis',
      'development_grid_narrow_fine4_20261024_v1':'docs/reports/D4_grid_narrow_fine4_acceptance_20261025/independent/analysis'}
    selected_bindings={};cert_hashes={}
    allowed_raw={'result.txt','diagnostics.csv','run_manifest.json','run_manifest.txt','exit_code.txt','boundary_audit.txt','effective_config.txt','run_config.txt','stage_manifest.json'}
    for batch,accept in old_acceptance.items():
        acc=ROOT/accept
        ars=js(acc/'scalar_results.json'); prior={x['run_id']:x for x in ars}
        cert_hashes[batch]=sha(acc/'scalar_results.json')
        priorhash=js(acc/'input_hashes.json')
        for p,h in priorhash.items():
            if Path(p).name in allowed_raw and isinstance(h,str):selected_bindings[(p,h)]='previous_acceptance_raw'
        for result in sorted((d4/'results'/batch).glob('*/steady/result.txt')):
            m=js(result.parent/'run_manifest.json');pl=byid[m['planned_case_id']]
            assert pl['role']!='prediction_test' and pl['blind_geometry']!='True', 'Do not read reserved prediction flow'
            rr=audit_run(result,'D4_bound_explicit',m['run_id'],pl['role'])
            rr['batch_id']=batch;rr['planned_case_id']=m['planned_case_id'];rr['model_data_role']='seen_development_or_control'
            rr['existing_acceptance_path']=str(acc.relative_to(ROOT));rr['prior_scalar_record']=prior[m['run_id']]
            rr['prior_scalar_K_matches']=math.isclose(rr['K_m3'],prior[m['run_id']]['K_m3'],rel_tol=1e-13)
            rr['build_environment_recorded']=bool(m.get('OpenLB_build_environment',{}).get('commands'))
            # Select direct source/build/physics and current-run bindings, not every chained old release or VTK.
            sel={}
            for p,h in m['inputs_sha256'].items():
                pp=Path(p)
                if str(pp).startswith(str(d4/'src')) or str(pp).startswith(str(d4/'build')) or str(pp).startswith('/home/dell/openlb/') or str(pp).startswith(str(d4/'protocol')) or pp==result.parent/'run_config.txt':sel[p]=h
            sel.update(m.get('OpenLB_build_environment',{}).get('library_hashes',{}))
            rr['selected_input_bindings']=len(sel)
            for p,h in sel.items():selected_bindings[(p,h)]='D4_direct_source_build_input'
            records.append(rr)
    for (p,h),label in selected_bindings.items():bind(Path(p),h,label)

    mainrows=[r for r in records if r['family']=='D2_D3_S1' and r['group']=='main']
    grids=[]
    for item in table(s/'Table_S2_refinement.csv'):
        h=int(item['h']);d=int(item['d']);direction=item['direction']
        coarse=next(r for r in records if r['family']=='D2_D3_S1' and r['group']=='main' and round(r['h_nm'])==h and round(r['d_nm'])==d and r['direction']==direction)
        fine=next(r for r in records if r['family']=='D2_D3_S1' and r['group']=='refinement' and round(r['h_nm'])==h and round(r['d_nm'])==d and r['direction']==direction)
        change=100*(fine['K_m3']/coarse['K_m3']-1)
        grids.append(dict(h_nm=h,d_nm=d,direction=direction,coarse_K=coarse['K_m3'],fine_K=fine['K_m3'],K_change_percent=change,table_matches=abs(change-float(item['K_change_percent']))<1e-10))
    d4grid=[]
    for d in [25,120]:
        pair={}
        for direction in ['parallel','perpendicular']:
            rr=[r for r in records if r['family']=='D4_bound_explicit' and round(r['h_nm'])==75 and round(r['w_nm'])==60 and round(r['d_nm'])==d and r['direction']==direction and r['acceleration_m_s2']==1e5]
            vals={round(r['dx_nm'],2):r['K_m3'] for r in rr}
            pair[direction]=vals
        pair['anisotropy']={dx:pair['parallel'][dx]/pair['perpendicular'][dx] for dx in [5,2.5,1.25]}
        for direction,vals in pair.items():
            e02=abs(vals[5]/vals[1.25]-1)*100;e12=abs(vals[2.5]/vals[1.25]-1)*100
            d4grid.append(dict(h_nm=75,d_nm=d,w_nm=60,quantity=direction,values=vals,E02_percent=e02,E12_percent=e12,original_size_criteria_satisfied=e02<=1 and e12<=.5))
    # Proposed new conditions, with historical search reported separately; do not calculate DNS or fit.
    seen=sorted({(round(r['h_nm'],7),round(r['d_nm'],7),round(r['w_nm'],7),round(r['P_nm'],7)) for r in records if all(r.get(k) is not None for k in ['h_nm','d_nm','w_nm','P_nm'])})
    candidates=[dict(id='U_REG',h_nm=60,d_nm=80,w_nm=120,P_nm=240,H_nm=100,role='within_sampled_h_range_prediction'),
                dict(id='U_THIN',h_nm=30,d_nm=80,w_nm=120,P_nm=240,H_nm=70,role='thin_gap_stress_test_outside_claimed_transverse_h_ge_50')]
    for r in candidates:
        key=tuple(r[k] for k in ['h_nm','d_nm','w_nm','P_nm'])
        r['matches_audited_existing_geometry']=key in seen
        r['matches_D4_reserved_geometry']=any(tuple(float(v[k]) for k in ['h_nm','d_nm','w_nm','P_nm'])==key for v in plans if v['blind_geometry']=='True')
        r['status']='PROPOSED_NOT_FROZEN_NOT_RUN'
    save('run_audit.json',records)
    save('binding_audit.json',dict(checks=BIND,selected_scope='D2 current binaries; scheme C saved outputs and source/libraries; D4 accepted scalar raw files and direct source/build/physics inputs. No full VTK reacceptance.',counts=dict(Counter(r['label'] for r in BIND)),mismatches=[r for r in BIND if not r['matches']]))
    save('grid_audit.json',dict(D2_two_grid=grids,D4_original_grid_size_criteria=d4grid,warning='Grid changes are not rigorous errors; D4 original FAILs are preserved.'))
    save('candidate_conditions.json',dict(candidates=candidates,seen_geometry_tuples=seen,reserved_D4_geometry_tuples=sorted({tuple(float(r[k]) for k in ['h_nm','d_nm','w_nm','P_nm']) for r in plans if r['blind_geometry']=='True'}),global_unseen_claim=False))
    counts=Counter(r['family'] for r in records)
    summary=dict(record_count=len(records),family_counts=dict(counts),note='Artifact records include historical duplicates, controls, smooth baselines and copied geometry; not unique new independent reference runs.',scalar_rechecked=sum('scalar_recheck' in r for r in records),scalar_gates_not_all_satisfied=[dict(run_id=r['run_id'],family=r['family'],checks=r['scalar_recheck']['checks']) for r in records if 'scalar_recheck' in r and not r['scalar_recheck']['all_checked_scalar_gates_satisfied']],D2_manifest_missing={k:sum(not r.get('manifest_fields_present',{}).get(k,False) for r in records if r['family']=='D2_D3_S1') for k in ['source_sha256','generated_source_sha256','openlb_commit','compiler','compile_flags']},D2_binary_groups=dict(Counter(r.get('binary_sha256') for r in records if r['family']=='D2_D3_S1')),D2_main_role_binary_counts={role:dict(Counter(r.get('binary_sha256') for r in mainrows if r['model_data_role']==role)) for role in ['calibration','seen_during_model_selection']},binding_mismatches=len([r for r in BIND if not r['matches']]),read_file_count=len(READ),reference_qualified=False,new_solver_runs=0,new_fits=0,formal_gates_changed=False)
    save('summary.json',summary)
    fields=['family','group','run_id','h_nm','d_nm','w_nm','P_nm','dx_nm','direction','K_m3','independent_exit','recorded_PASS','recorded_NUMERICAL_GATE','recorded_RESULT_PASS','recorded_geometry_PASS','saved_geometry_evidence_consistent','model_data_role','result_path']
    with (OUT/'run_inventory.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(records)
    save('read_inputs_sha256.json',READ)
    print(json.dumps(summary,indent=2,ensure_ascii=False))

if __name__=='__main__':
    main()
