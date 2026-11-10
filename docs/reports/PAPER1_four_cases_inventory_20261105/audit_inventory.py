"""Read-only inventory of four named historical runs and two existing refinements.

No solver imports, subprocess calls, field-array decoding, fitting, or gate changes.
Only writes this new report directory. Never opens reserved prediction results.
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import re
import statistics
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CASE = ROOT / 'CASE/D_series/D2_groove_error_map'
RUNS = [f'h50_d{d}_dx5_{dr}' for d in (25, 100) for dr in ('P', 'T')]
RUNS += [f'h50_d100_dx2.5_{dr}' for dr in ('P', 'T')]
fingerprints = {}


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def track(p):
    fingerprints[str(p.relative_to(ROOT))] = sha(p)


def kv(p):
    track(p)
    return dict(line.split('=', 1) for line in p.read_text().splitlines() if '=' in line)


def close(a, b, rel=1e-10, absolute=1e-28):
    return abs(a-b) <= max(absolute, rel * max(abs(a), abs(b)))


records = []
for name in RUNS:
    base = CASE / 'results' / name
    all_files = sorted(p for p in base.rglob('*') if p.is_file())
    for p in all_files:
        track(p)
    result = kv(base/'steady/result.txt')
    manifest = kv(base/'steady/run_manifest.txt')
    premanifest = kv(base/'precheck/run_manifest.txt')
    audits = {mode: kv(base/mode/'boundary_audit.txt') for mode in ('precheck', 'steady')}
    exits = {mode: int((base/mode/'exit_code.txt').read_text()) for mode in ('precheck', 'steady')}
    p = base/'steady/diagnostics.csv'
    with p.open() as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        data = [{k: float(v) for k, v in row.items()} for row in reader]
    tail = data[-1000:]
    vals = [r['J'] for r in tail]
    mean = statistics.mean(vals)
    std = statistics.stdev(vals)/abs(mean)
    span = (max(vals)-min(vals))/abs(mean)
    crosscol = 'Jx' if result['direction']=='parallel' else 'Jy'
    cross = max(abs(r[crosscol]) for r in tail)
    maxima = {k: max(abs(r[k]) for r in data) for k in
              ('Mach','mass_error','max_density_deviation','section_relative_difference')}
    nominal = float(result['nominal_volume_m3'])
    volume = float(result['fluid_volume_m3'])
    nu = (float(result['tau'])-.5)*float(result['dx_m'])**2/(3*float(result['dt_s']))
    k_from_j = nu*float(result['J_main_m2_s'])/float(result['acceleration_m_s2'])
    name_match = re.fullmatch(r'h50_d(25|100)_dx(5|2\.5)_([PT])', name)
    depth_nm, grid_nm, letter = name_match.groups()
    dx_nm = float(grid_nm)
    expected_nodes = round(240/dx_nm)*round(240/dx_nm)*round(50/dx_nm) + \
        round(120/dx_nm)*round(240/dx_nm)*round(float(depth_nm)/dx_nm)
    checks = {
        'recorded_inputs_match_named_geometry_direction':
            close(float(result['mesa_gap_m']),50e-9) and
            close(float(result['groove_depth_m']),float(depth_nm)*1e-9) and
            close(float(result['dx_m']),dx_nm*1e-9) and
            result['direction']==('parallel' if letter=='P' else 'perpendicular') and
            manifest['direction']==letter and
            float(manifest['mesa_gap_nm'])==50 and
            float(manifest['groove_depth_nm'])==float(depth_nm) and
            float(manifest['dx_nm'])==dx_nm,
        'recorded_shared_physical_settings':
            close(float(result['Lx_m']),240e-9) and close(float(result['Ly_m']),240e-9) and
            close(float(result['groove_width_m']),120e-9) and
            float(result['acceleration_m_s2'])==1e5 and float(result['tau'])==1 and
            result['periodicity']=='x_y' and result['descriptor']=='D3Q19_FORCE' and
            result['collision']=='ForcedBGK' and close(nu,1e-6),
        'recorded_fluid_nodes_match_geometry_arithmetic':
            int(result['fluid_nodes'])==expected_nodes and
            all(int(a['material_1'])==expected_nodes for a in audits.values()),
        'independent_exits_zero': all(x==0 for x in exits.values()),
        'saved_pass_converged': result['PASS']=='true' and result['converged']=='true',
        'diagnostic_rows_match_step_0_to_final': len(data)==int(result['steps_completed'])+1 and
            all(r['step']==i for i,r in enumerate(data)),
        'diagnostic_all_values_finite': all(math.isfinite(x) for r in data for x in r.values()),
        'diagnostic_finite_flags': all(r['finite']==1 for r in data),
        'last_j_matches_result': close(data[-1]['J'],float(result['J_main_m2_s'])),
        'K_reconstructed_from_recorded_units': close(k_from_j,float(result['Keff_m3'])),
        'final_1000_std_matches_result': close(std,float(result['window_main_rel_std']),rel=1e-8),
        'final_1000_span_matches_result': close(span,float(result['window_main_rel_span']),rel=1e-8),
        'final_1000_cross_matches_result': close(cross,float(result['window_cross_abs_max'])),
        'recorded_window_thresholds': std<=1e-6 and span<=5e-6 and cross<=1e-12,
        'recorded_diagnostic_thresholds': maxima['Mach']<.05 and maxima['mass_error']<1e-10
            and maxima['max_density_deviation']<=1e-6
            and data[-1]['section_relative_difference']<=1e-5,
        'nominal_volume_vs_saved_counted_volume': abs(volume/nominal-1)<=1e-10,
        'precheck_steady_manifests_equal': manifest==premanifest,
        'geometry_q_recorded_true': all(a.get('geometry_PASS')=='true' and
            a.get('q_audit_PASS')=='true' for a in audits.values()),
        'boundary_no_recorded_fallback_unresolved': all(all(int(a[k])==0 for k in
            ('geometric_fallback_count','missing_fluid_neighbour_fallback_count','unresolved_link_count'))
            for a in audits.values()),
        'links_installed_match_candidates': all(a['candidate_links']==a['installed_links'] for a in audits.values()),
        'time_column_matches_dt': all(close(r['time_s'],r['step']*float(result['dt_s']),absolute=1e-25)
            for r in data),
    }
    for col,key in [('Mach','max_Mach'),('mass_error','max_mass_abs_relative'),
                    ('max_density_deviation','max_density_deviation')]:
        checks['diagnostic_max_matches_'+key]=close(maxima[col],float(result[key]))
    xmls = []
    for p in all_files:
        if p.suffix not in ('.pvd','.vtm','.vti'):
            continue
        tree = ET.parse(p)
        root = tree.getroot()
        refs=[]
        for element in root.iter():
            for attribute in ('file','File'):
                if attribute in element.attrib:
                    q=p.parent/element.attrib[attribute]
                    refs.append({'reference':element.attrib[attribute], 'exists':q.is_file(),
                                 'inside_named_run':q.resolve().is_relative_to(base.resolve())})
        xmls.append({'path':str(p.relative_to(ROOT)), 'type':root.attrib.get('type'),
                     'references':refs,
                     'image_geometry':[x.attrib for x in root.iter('ImageData')],
                     'array_metadata':[x.attrib for x in root.iter('DataArray')],
                     'datasets':[x.attrib for x in root.iter('DataSet')]})
    checks['vtk_reference_targets_present']=all(r['exists'] and r['inside_named_run']
        for x in xmls for r in x['references'])
    checks['vtk_contains_initial_and_result_step']=set([0,int(result['steps_completed'])]).issubset(
        {int(m.group(1)) for p in all_files if p.suffix=='.vti'
         for m in [re.search(r'_iT(\d+)iC',p.name)] if m})
    headers = {}
    for filename in ('field_slice.csv','energy_dissipation.csv','velocity_profile.csv','pressure_profile.csv'):
        p=base/'steady'/filename
        with p.open() as f:
            headers[filename]={'header':f.readline().strip(),
                               'data_row_count':sum(1 for line in f if line.strip())}
    log=(base/'steady/run.log').read_text(errors='replace')
    records.append({'run_id':name,'role':'main' if '_dx5_' in name else 'existing_refinement',
                    'result':result,'manifest':manifest,'exit_codes':exits,'boundary_audits':audits,
                    'diagnostic_rows':len(data),'diagnostic_columns':columns,
                    'recomputed_last_window':{'std':std,'span':span,'cross_max':cross,
                       'physical_duration_first_to_last_s':tail[-1]['time_s']-tail[0]['time_s']},
                    'recomputed_diagnostic_maxima':maxima,'nu_from_dx_dt_tau':nu,
                    'csv_structural_inventory':headers,'vtk_structural_inventory':xmls,
                    'file_count':len(all_files),'total_bytes':sum(p.stat().st_size for p in all_files),
                    'saved_log_tail':log.splitlines()[-4:],
                    'checks':checks, 'check_failures':[k for k,v in checks.items() if not v]})

extra = [CASE/'src/d2_groove_error_map.cpp',CASE/'src/Makefile',CASE/'build/d2_groove_error_map',
         CASE/'scripts/run_matrix.sh',
         ROOT/'docs/reports/SIM240_Supplementary_Methods_20261024/Table_S1_run_inventory.csv',
         ROOT/'docs/reports/SIM240_Supplementary_Methods_20261024/Table_S2_refinement.csv',
         ROOT/'docs/reports/Historical_build_adjudication_20261028/REPORT.md',
         ROOT/'docs/reports/Chapter5_mechanism_audit_20261018/REPORT.md']
for p in extra:
    track(p)
lookup = {r['run_id']:r for r in records}
ratios={}
for dr in ('P','T'):
    shallow=float(lookup[f'h50_d25_dx5_{dr}']['result']['Keff_m3'])
    deep5=float(lookup[f'h50_d100_dx5_{dr}']['result']['Keff_m3'])
    deep25=float(lookup[f'h50_d100_dx2.5_{dr}']['result']['Keff_m3'])
    ratios[dr]={'same_dx5_depth_gain':deep5/shallow,
                'deep_5_to_2p5_change_percent':100*(deep25/deep5-1),
                'mixed_grid_diagnostic_ratio_not_depth_gain_evidence':deep25/shallow}
summary={'date':'2026-11-05','runs':records,'ratios':ratios,
         'current_binary_sha256':sha(CASE/'build/d2_groove_error_map'),
         'named_run_recorded_binary_hashes':sorted({r['manifest']['binary_sha256'] for r in records}),
         'found_named_h50_directories':sorted(p.name for p in (CASE/'results').iterdir()
             if p.is_dir() and re.match(r'^h50_d(?:25|100)_',p.name)),
         'scope':{'solver_executed':False,'original_checker_replayed':False,
                  'field_arrays_decoded':False,'flow_mechanism_extracted':False,
                  'reserved_prediction_opened':False,'formal_gate_reaccepted':False,
                  'new_simulation_run_id':None}}
(OUT/'inventory.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(OUT/'read_inputs_sha256.json').write_text(json.dumps(fingerprints,indent=2)+'\n')
changed=[p for p,h in fingerprints.items() if sha(ROOT/p)!=h]
verification={'protected_input_count':len(fingerprints),'protected_input_changed':changed,
              'run_count':len(records),'diagnostic_rows':sum(r['diagnostic_rows'] for r in records),
              'numeric_structure_check_failures':{r['run_id']:r['check_failures'] for r in records
                                                   if r['check_failures']},
              'input_unchanged':not changed,'field_processing_performed':False}
(OUT/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
for r in records:
    print(r['run_id'],'K=',r['result']['Keff_m3'],'rows=',r['diagnostic_rows'],
          'files=',r['file_count'],'failures=',r['check_failures'])
print(json.dumps({'ratios':ratios,'verification':verification},ensure_ascii=False))
