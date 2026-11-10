#!/usr/bin/env python3
"""Bounded arithmetic review of saved D2/D3 text records. No solver or N8 field reads."""
import csv
import hashlib
import io
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
seen = {}

def read(path):
    path = Path(path)
    path = path if path.is_absolute() else ROOT / path
    data = path.read_bytes()
    seen[str(path.relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
    return data.decode()

def kv(path):
    return dict(line.split('=', 1) for line in read(path).splitlines() if '=' in line)

def rows(path):
    return list(csv.DictReader(io.StringIO(read(path))))

def write(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n')

inventory = rows('docs/reports/SIM240_Supplementary_Methods_20261024/Table_S1_run_inventory.csv')
points = []
record_checks = []
manifest_missing = {}
windows = []
for row in inventory:
    raw = kv(row['result_path'])
    manifest = kv(row['manifest_path'])
    exit_code = int(read(Path(row['result_path']).with_name('exit_code.txt')).strip())
    read(row['log_path'])
    missing = [k for k in ['source_sha256', 'generated_source_sha256', 'openlb_commit', 'compiler', 'compile_flags'] if k not in manifest]
    manifest_missing[row['run_id']] = missing
    record_checks.append({'run_id': row['run_id'], 'recorded_PASS': raw['PASS'], 'independent_exit': exit_code,
                          'binary_sha_matches_inventory': manifest['binary_sha256'] == row['binary_sha256']})
    if row['group'] not in ('main', 'refinement'):
        continue
    h, d, dx = (float(raw[k])*1e9 for k in ['mesa_gap_m', 'groove_depth_m', 'dx_m'])
    direction = raw['direction']
    h, d = round(h), round(d)
    K = float(raw['Keff_m3'])
    J = float(raw['J_main_m2_s'])
    nu = (float(raw['tau']) - .5)*float(raw['dx_m'])**2/(3*float(raw['dt_s']))
    K_recomputed = nu*J/float(raw['acceleration_m_s2'])
    shallow, deep = (h*1e-9)**3/12, ((h+d)*1e-9)**3/12
    model = (shallow+deep)/2 if direction == 'parallel' else 2/(1/shallow+1/deep)
    c, p = (1.7685, 1.6331) if direction == 'parallel' else (.4900, .6990)
    F = 1/(1+c*(d/120)**p)
    points.append({'id': row['run_id'], 'h_nm': h, 'd_nm': d, 'dx_nm': dx, 'direction': direction,
                   'group': row['group'], 'K': K, 'K_chain_relative_difference': K_recomputed/K-1,
                   'K_model': model, 'E_percent': 100*(model/K-1), 'F_V2': F,
                   'r_percent': 100*(F*model/K-1), 'result_path': row['result_path']})
    if row['group'] == 'main':
        diag = rows(Path(row['result_path']).with_name('diagnostics.csv'))
        last = [float(r['J']) for r in diag[-1000:]]
        mean = statistics.mean(last)
        sd = statistics.stdev(last)/abs(mean)
        span = (max(last)-min(last))/abs(mean)
        windows.append({'id': row['run_id'], 'rows_read': len(diag), 'rel_std': sd, 'rel_span': span,
                        'margin': 1-sd/1e-6, 'record_std_abs_difference': abs(sd-float(raw['window_main_rel_std']))})

main = [p for p in points if p['group'] == 'main']
def point(h, d, direction, group='main'):
    return next(p for p in points if (p['h_nm'],p['d_nm'],p['direction'],p['group']) == (h,d,direction,group))

ratios = []
for h in [50,75,125]:
    for direction in ['parallel','perpendicular']:
        q = point(h,120,direction)['K']/point(h,25,direction)['K']
        entry = {'h_nm':h,'direction':direction,'ratio_5nm':q,'gain_5nm_percent':100*(q-1),
                 'hypothetical_equal_endpoint_error_limit_for_positive_gain_percent':100*(q-1)/(q+1)}
        if h == 125:
            qfine = point(h,120,direction,'refinement')['K']/point(h,25,direction,'refinement')['K']
            entry['ratio_2p5nm'] = qfine
            entry['gain_2p5nm_percent'] = 100*(qfine-1)
        ratios.append(entry)

refinement = []
for fine in [p for p in points if p['group'] == 'refinement']:
    coarse = point(fine['h_nm'],fine['d_nm'],fine['direction'])
    refinement.append({'h_nm':fine['h_nm'],'d_nm':fine['d_nm'],'direction':fine['direction'],
                       'K_change_percent':100*(fine['K']/coarse['K']-1),
                       'E5_percent':coarse['E_percent'],'E2p5_percent':fine['E_percent'],
                       'r5_percent':coarse['r_percent'],'r2p5_percent':fine['r_percent']})
baseP, baseT = point(75,100,'parallel'), point(75,100,'perpendicular')
A = baseP['K']/baseT['K']
Am = baseP['K_model']/baseT['K_model']
angles = {'A_5nm':A,'A_model':Am,'A_error_percent':100*(Am/A-1),
          'beta_ref_deg':math.degrees(math.atan(1/A)), 'beta_model_deg':math.degrees(math.atan(1/Am))}
angles['beta_difference_deg'] = angles['beta_model_deg']-angles['beta_ref_deg']
archives = []
for row in rows('docs/reports/SIM240_Supplementary_Methods_20261024/Table_S4_grid_archive.csv'):
    raw = kv(row['result_path'])
    K = float(raw['K_LBM_m3'] if 'K_LBM_m3' in raw else raw['Keff_m3'])
    ex = int(read(Path(row['result_path']).with_name('exit_code.txt')).strip())
    archives.append({'grid':row['grid'],'case':row['case'],'K':K,'recorded_PASS':raw['PASS'],
                     'independent_exit':ex,'table_relative_difference':K/float(row['K_m3'])-1,
                     'result_path':row['result_path']})

protected = json.loads(read('docs/reports/Paper_text_figure_corrections_20261027/input_hashes.json'))['protected_sha256']
protection_mismatches = []
for path, expected in protected.items():
    p = ROOT/path
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    seen[path] = digest
    if digest != expected:
        protection_mismatches.append(path)
for path in [
 'docs/reports/SIM240_中文稿_导师审阅版_20261022.md',
 'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md',
 'docs/reports/G4_derivation_source_audit_20261025/REPORT.md',
 'docs/reports/Correction_formula_derivation_20261023/DERIVATION.md',
 'docs/reports/G4_reference_criteria_review_20261026/decisions.json',
 'docs/reports/D4_N8_acceptance_20261026/verdict.json',
 'CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp',
 'CASE/D_series/D2_groove_error_map/scripts/run_matrix.sh',
 'CASE/D_series/D2_groove_error_map/scripts/run_dx25_refinement_20261018.sh',
]:
    read(path)

summary = {
 'scope':'saved text records and arithmetic; no new flow computation, fit or N8 field extraction',
 'run_inventory_count':len(inventory),'main_count':len(main),'refinement_count':len(refinement),
 'direction_summary':{direction:{'n':len(sub), 'positive_n':sum(p['E_percent']>0 for p in sub),
     'E_min_percent':min(p['E_percent'] for p in sub),'E_max_percent':max(p['E_percent'] for p in sub),
     'V2_max_abs_percent':max(abs(p['r_percent']) for p in sub)}
     for direction in ['parallel','perpendicular'] for sub in [[p for p in main if p['direction']==direction]]},
 'V2_T_h_ge_50_max_abs_percent':max(abs(p['r_percent']) for p in main if p['direction']=='perpendicular' and p['h_nm']>=50),
 'V2_worsened_main_ids':[p['id'] for p in main if abs(p['r_percent'])>abs(p['E_percent'])],
 'K_chain_max_relative_difference':max(abs(p['K_chain_relative_difference']) for p in points),
 'final_window_rows_read':sum(w['rows_read'] for w in windows),
 'final_window_margin_below_1percent':sum(w['margin']<.01 for w in windows),
 'final_window_margin_below_point1percent':sum(w['margin']<.001 for w in windows),
 'ratios':ratios,'anisotropy_and_angles':angles,'refinements':refinement,
 'historical_failed_records':[p for p in archives if p['recorded_PASS']!='true' or p['independent_exit']!=0],
 'manifest_missing_fields_count':{key:sum(key in v for v in manifest_missing.values()) for key in ['source_sha256','generated_source_sha256','openlb_commit','compiler','compile_flags']},
 'protected_prior_selection_count':len(protected),'prior_selection_mismatches':protection_mismatches,
 'formal_gate_reassessed':False,'reference_qualified':False,'strict_error_bound_established':False,
 'new_solver_run_id':None,'submission_ready':False
}
checks = {
 '52_saved_records_PASS_exit_and_binary_identity':len(record_checks)==52 and all(r['recorded_PASS']=='true' and r['independent_exit']==0 and r['binary_sha_matches_inventory'] for r in record_checks),
 '36_main_18_unique_geometries':len(main)==36 and len({(p['h_nm'],p['d_nm']) for p in main})==18,
 '8_refinement_records':len(refinement)==8,
 'all_36_discrete_biases_positive':all(p['E_percent']>0 for p in main),
 'units_K_chain_matches_saved_values':summary['K_chain_max_relative_difference']<1e-12,
 '36_saved_last_windows_meet_std_span':len(windows)==36 and all(w['rel_std']<=1e-6 and w['rel_span']<=5e-6 and w['record_std_abs_difference']<1e-12 for w in windows),
 'all_8_refined_biases_positive':all(p['E2p5_percent']>0 for p in refinement),
 'unique_V2_worsened_point_preserved':summary['V2_worsened_main_ids']==['h25_d100_dx5_T'],
 'historical_finest_T_failure_preserved':len(summary['historical_failed_records'])==1 and summary['historical_failed_records'][0]['independent_exit']==3,
 'historical_table_matches_raw':all(abs(p['table_relative_difference'])<1e-12 for p in archives),
 '436_selected_prior_inputs_unchanged':len(protected)==436 and not protection_mismatches,
 'all_read_inputs_unchanged_after_arithmetic':all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in seen.items()),
}
write('recomputed.json',summary)
write('pointwise.json',points)
write('record_checks.json',{'runs':record_checks,'missing_manifest_fields':manifest_missing,'last_windows':windows,'historical':archives})
write('source_manifest.json',{'sha256':seen,'scope':'selected actually read files; no universal project-integrity claim'})
write('verification.json',{'checks':checks,'all_checks_pass':all(checks.values()),'scientific_accuracy_pass':False})
print(json.dumps({'all_checks_pass':all(checks.values()),'check_count':len(checks),'read_file_count':len(seen),'ratios':ratios,'anisotropy':angles},ensure_ascii=False,indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
