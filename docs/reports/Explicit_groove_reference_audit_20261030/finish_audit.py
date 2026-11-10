#!/usr/bin/env python3
"""Supplement initial audit with bounded unseen-condition search and reuse labels."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import re
import subprocess

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
READ={}

def sha(p):
    p=Path(p).resolve(); h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    READ[str(p)]=h.hexdigest();return h.hexdigest()

def text(p):
    sha(p);return Path(p).read_text(errors='replace')

def js(p):return json.loads(text(p))

def save(name,x):
    p=OUT/name
    if p.exists():raise FileExistsError(p)
    p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def kv(p):return dict(x.split('=',1) for x in text(p).splitlines() if '=' in x and not x.startswith('#'))

def main():
    records=js(OUT/'run_audit.json');summary=js(OUT/'summary.json');bindings=js(OUT/'binding_audit.json')
    # Audit original fit history as evidence; never import/run these scripts.
    fit=ROOT/'CASE/D_series/D2_groove_error_map/analysis_fit_v2.py'
    ft=text(fit)
    manuscript=ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md';mt=text(manuscript)
    fit_evidence=dict(fit_script=str(fit.relative_to(ROOT)),fit_script_sha256=sha(fit),
        calibration_declared='CALIB_D = (25.0, 50.0, 100.0)' in ft and 'CALIB_H = (50.0, 75.0, 125.0)' in ft,
        extension_loaded_in_script=all(x in ft for x in ['d75_summary.csv','h25_summary.csv','d120_summary.csv']),
        manuscript_declares_extension_seen='扩展数据在模型形式选择时已经可见' in mt,
        binary_separation=summary['D2_main_role_binary_counts'],
        independent_final_test_geometry_count_in_36=0,
        interpretation='Exclusion from the coefficient objective is not exclusion from model selection. No old extension geometry is rebranded as unseen.')
    assert fit_evidence['calibration_declared'] and fit_evidence['manuscript_declares_extension_seen']
    save('data_use_history.json',fit_evidence)

    # A bounded CASE/docs metadata search. Never read reserved D4 prediction field arrays or solve results.
    cmd=['rg','--files','--hidden','--no-ignore','CASE','docs','-g','result.txt','-g','run_config.txt','-g','effective_config.txt']
    result=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,check=True)
    paths=sorted(result.stdout.splitlines());(OUT/'metadata_search_paths.txt').write_text('\n'.join(paths)+'\n')
    candidates=js(OUT/'candidate_conditions.json')['candidates']
    parsed=[];unparsed=[];skipped=[]
    def length(data,aliases):
        for key,scale in aliases:
            if key in data:
                try:return float(data[key])*scale
                except ValueError:pass
        return None
    for s in paths:
        if '/reference_backend_min18_' in s or 'prediction_test' in s:
            skipped.append(s);continue
        p=ROOT/s
        try:d=kv(p)
        except (OSError,UnicodeError):unparsed.append(s);continue
        h=length(d,[('mesa_gap_m',1e9),('mesa_gap_nm',1),('h_m',1e9),('h_nm',1)])
        depth=length(d,[('groove_depth_m',1e9),('groove_depth_nm',1),('d_m',1e9),('d_nm',1)])
        w=length(d,[('groove_width_m',1e9),('groove_width_nm',1),('w_m',1e9),('w_nm',1)])
        period=length(d,[('period_m',1e9),('period_nm',1),('Lx_m',1e9),('P_nm',1),('Lx_nm',1)])
        if None in [h,depth,w,period]:unparsed.append(s);continue
        parsed.append(dict(path=s,h_nm=h,d_nm=depth,w_nm=w,P_nm=period,
                           kind=p.name,formal_simulation=d.get('formal_simulation'),steps=d.get('steps_completed')))
    for c in candidates:
        matches=[r for r in parsed if all(abs(r[k]-c[k])<1e-6 for k in ['h_nm','d_nm','w_nm','P_nm'])]
        c['parsed_metadata_matches']=matches
        assert not matches and not c['matches_audited_existing_geometry'] and not c['matches_D4_reserved_geometry']
        c['novelty_status']='NO_MATCH_IN_BOUNDED_LOCAL_RECORD_SEARCH; not global proof of blindness'
    save('unseen_condition_search.json',dict(search_command=cmd,searched_paths=len(paths),
        fully_parsed_geometry_records=len(parsed),unparsed_paths=unparsed,
        skipped_reserved_or_algebraic_backend_paths=skipped,candidates=candidates,
        reserved_prediction_flows_read=False,
        remaining_requirement='Before preregistration, author confirms external/private data-use history; do not evaluate or redesign V2 on these future DNS outcomes.'))

    qualifications=[]
    for r in records:
        family=r['family'];h=round(r['h_nm'] or 0);d=round(r['d_nm'] or 0);w=round(r['w_nm'] or 0)
        scope='fixed_gap_single_phase_periodic_transport_only'
        if family=='D4_bound_explicit':
            label='REUSABLE_BOUND_FIXED_GRID'
            allowed='fixed-resolution explicit numerical record and corresponding accepted control/development scope'
            source='selected direct source/build/input and prior scalar evidence match'
            if w==60 and d in [25,120]:grid='3 levels available; original grid sensitivity target FAIL at geometry level'
            elif w==240 and d==120:grid='5/2.5nm available; 1.25nm directions missing; original workflow held'
            elif r['group']=='smooth':grid='analytic K/profile baseline accepted; no universal patterned-grid guarantee'
            else:grid='single bound 5nm record; additional spatial qualification needed'
        elif family=='G2_scheme_C':
            label='CONDITIONAL_HISTORICALLY_RELEASED_RECORD'
            allowed='corrected-ledger 1.25nm transverse numerical record; historical release claim retained, current complete receipt/environment not reproduced'
            source='19 saved outputs and 9 source entries match; historical receipts missing and dynamic environment drift'
            grid='historical 3-level chain; restoration or explicit versioned requalification required for current release'
        elif family=='G2_historical_grid' and r['recorded_PASS']=='false':
            label='FAILED_DIAGNOSTIC_ONLY';allowed='historical failure/diagnostic, excluded as accepted fine reference'
            source='raw and independent exit3 preserved';grid='mass-gate FAIL; cannot use this point to claim accepted 3-grid convergence'
        else:
            label='REUSABLE_DISCRETE_RECORD_WITH_LIMITS'
            allowed='retrospective comparison or saved-resolution support; not independent final test'
            source='old numerical/log evidence; incomplete historical source/build binding'
            if family=='D2_D3_S1' and (h,d) in [(25,100),(50,100),(125,25),(125,120)]:grid='matched 5/2.5nm sensitivity; not a continuum error bound'
            elif family=='G2_historical_grid':grid='part of historical grid chain; chain qualification checked separately'
            elif family=='G4_period_linearity':grid='periodic copy and drive checks at h75/d100/dx2.5 only; no all-geometry spatial guarantee'
            elif family=='G3_height':grid='fixed dx2.5nm height samples; endpoint uncertainty/linearity not closed'
            elif family=='D2_D3_S1' and (h,d)==(75,100):grid='old baseline; historical grid and corrected-C qualifications separate'
            else:grid='no matched multilevel evidence in the audited primary set'
        qualifications.append(dict(run_id=r['run_id'],family=family,reuse_class=label,allowed_use=allowed,
            source_status=source,spatial_status=grid,independent_unseen_test=False,
            squeeze_reference_qualified=False,scope=scope,result_path=r['result_path']))
    with (OUT/'qualification.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(qualifications[0]));writer.writeheader();writer.writerows(qualifications)
    save('qualification.json',dict(scope='Evidence reuse labels only; original numerical and scientific Gates not rewritten',
                                  classes=dict(Counter(r['reuse_class'] for r in qualifications)),records=qualifications))

    # Check the scheme C executable separately, and classify the original 52 mismatch records honestly.
    croot=ROOT/'CASE/03_grid_convergence/G2_EX240_fine_T_statfix_C_v1/runs/fine_t_C_20261014T151036+0800'
    cm=js(croot/'manifest.json');bp=Path(cm['binary']['path'])
    cbin=dict(path=str(bp),exists=bp.is_file(),expected_sha256=cm['binary']['sha256'],actual_sha256=sha(bp) if bp.is_file() else None)
    cbin['matches']=cbin['actual_sha256']==cbin['expected_sha256']
    mismatch=bindings['mismatches']
    save('binding_interpretation.json',dict(initial_binding_records=len(bindings['checks']),
        initial_mismatch_records=len(mismatch),unique_mismatch_paths=len({r['path'] for r in mismatch}),
        mismatch_by_label=dict(Counter(r['label'] for r in mismatch)),
        scheme_C_binary=cbin,
        D4_selected_bindings_all_match=all(r['matches'] for r in bindings['checks'] if r['label'].startswith('D4_') or r['label']=='previous_acceptance_raw'),
        C_original_outputs_all_match=all(r['matches'] for r in bindings['checks'] if r['label']=='scheme_C_output'),
        C_source_entries_all_match=all(r['matches'] for r in bindings['checks'] if r['label']=='scheme_C_source_files'),
        no_raw_data_corruption_inferred=True,
        interpretation='The 24 D2 binary mismatch records repeat a replaced executable path; 26 C historical-input issues concern changed rules/missing reports; two C runtime libraries changed. These do not mean 52 damaged simulation outputs. mtime or current Makefile alone cannot reconstruct missing historical source-to-binary binding.'))

    # Direct numerical comparisons that are useful without any new PDE solves or fitting.
    base=[r for r in records if r['family']=='D2_D3_S1' and r['group']=='main']
    comparisons=[]
    for r in records:
        if r['family']=='D4_bound_explicit' and r['group']=='regression':
            old=next(x for x in base if round(x['h_nm'])==75 and round(x['d_nm'])==100 and x['direction']==r['direction'])
            comparisons.append(dict(kind='bound_new_implementation_vs_old_baseline',direction=r['direction'],old_K=old['K_m3'],new_K=r['K_m3'],relative_difference=abs(r['K_m3']/old['K_m3']-1)))
    save('reuse_comparisons.json',dict(comparisons=comparisons,
        note='Local regression agreement does not prove all historical builds/geometry groups equivalent.'))
    save('supplement_read_inputs_sha256.json',READ)
    print(json.dumps(dict(records=len(records),classes=dict(Counter(r['reuse_class'] for r in qualifications)),
        total_diagnostic_rows=sum(r['scalar_recheck']['diagnostic_rows'] for r in records),
        metadata_paths=len(paths),parsed_geometry_records=len(parsed),unparsed=len(unparsed),
        candidates=[{k:v for k,v in c.items() if k!='parsed_metadata_matches'} for c in candidates],
        C_binary_matches=cbin['matches']),indent=2,ensure_ascii=False))

if __name__=='__main__':main()
