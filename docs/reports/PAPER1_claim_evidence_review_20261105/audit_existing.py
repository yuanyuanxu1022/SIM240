#!/usr/bin/env python3
"""Read existing result records; recompute published comparisons, never solve or fit."""
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SUP = ROOT / 'docs/reports/SIM240_Supplementary_Methods_20261024'
used = {}


def read(path):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    b = p.read_bytes()
    key = str(p.relative_to(ROOT))
    sha = hashlib.sha256(b).hexdigest()
    if key in used:
        assert used[key]['sha256'] == sha, key
    used[key] = {'sha256': sha, 'bytes': len(b)}
    return b.decode('utf-8-sig')


def kv(path):
    return dict(line.split('=', 1) for line in read(path).splitlines() if '=' in line)


def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def close(a, b, tol=2e-13):
    return math.isclose(a, b, rel_tol=tol, abs_tol=0)


def model(h, d, direction):
    u, v = (h+d)**3, h**3
    return ((u+v)/24 if direction == 'parallel' else u*v/(6*(u+v))) * 1e-27


def factor(d, direction):
    a, p = (1.7685, 1.6331) if direction == 'parallel' else (0.4900, 0.6990)
    return 1/(1+a*(d/120)**p)


def main():
    # The fixed protected set is explicit; this is not a whole-repository audit.
    docs = [
        'docs/reports/SIM240_中文稿_导师审阅版_20261022.md',
        'docs/reports/SIM240_First_Paper_English_20261028.md',
        'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md',
        'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md',
        'docs/reports/Historical_build_text_sync_20261028/REVISION_NOTE.md',
        'docs/reports/Appendix_E_final_review_20261028/REPORT.md',
        'docs/reports/Appendix_E_final_review_20261028/ASTRA_REVIEW.md',
        'docs/reports/PAPER1_h25_reference_candidate_audit_20261104_225645/REPORT.md',
        'docs/reports/PAPER1_h25_d100_T_counterexample_20261104/REPORT.md',
        'docs/reports/URV_S4_TGE_1p25_data_audit_20261105_100521/REPORT.md',
        'CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp',
        'CASE/D_series/D2_groove_error_map/analysis_fit_v2.py',
    ]
    for p in docs:
        read(p)
    for p in SUP.glob('Table_S*.csv'):
        read(p)
    rows = list(csv.DictReader(read(SUP / 'Table_S1_run_inventory.csv').splitlines()))
    records, numeric, checks = {}, [], []
    for row in rows:
        result = kv(row['result_path'])
        manifest = kv(row['manifest_path'])
        exit_path = str(Path(row['result_path']).with_name('exit_code.txt'))
        exit_code = int(read(exit_path).strip())
        # Viscosity is explicitly saved for the two viscosity controls; otherwise
        # infer nu from the saved BGK converter, not from the table's K value.
        dx, dt, tau = (float(result[k]) for k in ('dx_m', 'dt_s', 'tau'))
        nu_converter = dx*dx*(tau-.5)/(3*dt)
        nu = float(result.get('nu_phys_m2_s', nu_converter))
        k_flux = nu*float(result['J_main_m2_s'])/float(result['acceleration_m_s2'])
        k = float(result['Keff_m3'])
        raw = {
            'run_id': row['run_id'], 'group': row['group'],
            'h_nm': int(row['h_nm']), 'd_nm': int(row['d_nm']),
            'dx_nm': float(row['dx_nm']), 'direction': row['direction'],
            'K_result_m3': k, 'K_flux_recomputed_m3': k_flux,
            'binary_sha256': manifest['binary_sha256'],
            'checks': {
                'K_matches_table': close(k, float(row['K_m3'])),
                'K_matches_flux_converter': close(k, k_flux),
                'converter_matches_explicit_nu': close(nu, nu_converter),
                'dx_matches_table': close(dx*1e9, float(row['dx_nm'])),
                'h_matches_table': close(float(result['mesa_gap_m'])*1e9, int(row['h_nm'])),
                'd_matches_table': close(float(result['groove_depth_m'])*1e9, int(row['d_nm'])),
                'recorded_PASS': result['PASS'] == row['recorded_PASS'] == 'true',
                'recorded_converged': result['converged'] == 'true',
                'independent_exit_zero': exit_code == int(row['independent_exit_code']) == 0,
                'binary_sha_matches_table': manifest['binary_sha256'] == row['binary_sha256'],
                'recorded_finite': result['finite'] == 'true' and math.isfinite(k),
            },
            'missing_historical_manifest_fields': [key for key in
                ('source_sha256', 'generated_source_sha256', 'openlb_commit', 'compiler', 'compile_flags')
                if key not in manifest],
        }
        checks.append(raw)
        records[row['run_id']] = (row, result, manifest)
        if row['group'] != 'main':
            continue
        h, d, direction = raw['h_nm'], raw['d_nm'], row['direction']
        km = model(h, d, direction)
        f = factor(d, direction)
        numeric.append({**{key:raw[key] for key in ('run_id','h_nm','d_nm','direction','binary_sha256')},
                        'K_ref_m3': k, 'K_model_m3': km, 'F_V2_published': f,
                        'E_percent': 100*(km/k-1), 'V2_residual_percent': 100*(f*km/k-1)})
    assert len(rows) == 52 and len(numeric) == 36
    failed = [(r['run_id'], k) for r in checks for k,v in r['checks'].items() if not v]
    assert not failed, failed
    by = {(r['h_nm'], r['d_nm'], r['direction']):r for r in numeric}
    extrema = {}
    for direction in ('parallel','perpendicular'):
        subset = [r for r in numeric if r['direction'] == direction]
        extrema[direction] = {
            'minimum_E_percent': min(r['E_percent'] for r in subset),
            'maximum_E_percent': max(r['E_percent'] for r in subset),
            'maximum_abs_V2_residual_percent': max(abs(r['V2_residual_percent']) for r in subset),
            'h_ge_50_count': sum(r['h_nm'] >= 50 for r in subset),
            'h_ge_50_max_abs_V2_residual_percent': max(abs(r['V2_residual_percent']) for r in subset if r['h_nm'] >= 50),
        }
    growth = []
    for h in (50,75,125):
        for direction in ('parallel','perpendicular'):
            a, b = by[h,25,direction], by[h,120,direction]
            growth.append({'h_nm':h,'direction':direction,'ratio_d120_over_d25':b['K_ref_m3']/a['K_ref_m3'],
                           'same_recorded_binary':a['binary_sha256']==b['binary_sha256']})
    refinements=[]
    for row in csv.DictReader(read(SUP / 'Table_S2_refinement.csv').splitlines()):
        h,d,direction=int(row['h']),int(row['d']),row['direction']
        p='P' if direction=='parallel' else 'T'
        coarse=by[h,d,direction]
        rr, r, m=records[f'h{h}_d{d}_dx2.5_{p}']
        k=float(r['Keff_m3']); km=model(h,d,direction)
        expected={'K5':coarse['K_ref_m3'],'K2_5':k,'K_change_percent':100*(k/coarse['K_ref_m3']-1),
                  'E5_percent':coarse['E_percent'],'E2_5_percent':100*(km/k-1)}
        expected['E_change_percentage_points']=expected['E2_5_percent']-expected['E5_percent']
        # Small near-zero percentage differences are checked at numerical rounding scale.
        assert all(math.isclose(float(row[key]),v,rel_tol=1e-10,abs_tol=1e-11) for key,v in expected.items())
        refinements.append({'h_nm':h,'d_nm':d,'direction':direction,**expected,
                            'V2_residual_fine_percent':100*(factor(d,direction)*km/k-1),
                            'same_coarse_fine_binary':coarse['binary_sha256']==m['binary_sha256']})
    p,t=by[75,100,'parallel'],by[75,100,'perpendicular']
    ratio_ref=p['K_ref_m3']/t['K_ref_m3']; ratio_mod=p['K_model_m3']/t['K_model_m3']
    groups=defaultdict(list)
    for r in numeric:
        calibration=r['h_nm'] in (50,75,125) and r['d_nm'] in (25,50,100)
        groups['calibration' if calibration else 'extension'].append(r)
    summary={
        'review_time':datetime.now().astimezone().isoformat(),
        'scope':'postprocessing_saved_records_only_no_fit_no_solver_no_gate_reacceptance',
        'inventory_count':len(rows),'geometry_count':len(by)//2,'main_direction_count':len(numeric),
        'groups':dict(Counter(r['group'] for r in rows)),
        'checks_count':sum(len(r['checks']) for r in checks),'failed_checks':failed,
        'binary_groups':dict(Counter(r['binary_sha256'] for r in checks)),
        'main_all_E_positive':all(r['E_percent']>0 for r in numeric),
        'extrema':extrema,'depth_growth':growth,
        'anisotropy':{'reference':ratio_ref,'model':ratio_mod,'relative_discrepancy_percent':100*(ratio_mod/ratio_ref-1),
                      'beta_ref_degrees':math.degrees(math.atan(1/ratio_ref)),
                      'beta_model_degrees':math.degrees(math.atan(1/ratio_mod)),
                      'beta_difference_degrees':math.degrees(math.atan(1/ratio_mod)-math.atan(1/ratio_ref))},
        'V2_absolute_discrepancy_worsened_ids':[r['run_id'] for r in numeric if abs(r['V2_residual_percent'])>abs(r['E_percent'])],
        'refinements':refinements,
        'main_calibration_extension_binary_partition':{name:{'direction_count':len(grp),'geometry_count':len(grp)//2,
            'binary_groups':dict(Counter(r['binary_sha256'] for r in grp))} for name,grp in groups.items()},
        'all_52_manifests_lack_five_historical_build_fields':all(len(r['missing_historical_manifest_fields'])==5 for r in checks),
        'limitations':['not full raw trajectory or field reacceptance','not historical source recovery',
                      'not continuum reference qualification','not independent validation of V2',
                      'no new novelty or full literature audit','no new theory freeze'],
    }
    dump('record_checks.json',checks); dump('recomputed_summary.json',summary)
    with (OUT/'recomputed_36_points.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(numeric[0]));writer.writeheader();writer.writerows(numeric)
    dump('reviewed_input_manifest.json',used)
    changed=[p for p,v in used.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=v['sha256']]
    assert not changed,changed
    dump('input_integrity.json',{'protected_file_count':len(used),'all_unchanged':not changed,'changed':changed})
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
