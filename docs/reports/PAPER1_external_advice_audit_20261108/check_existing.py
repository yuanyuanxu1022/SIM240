"""Read saved scalars only; no solver, gate checker, fitting, or field decoding."""
from pathlib import Path
import csv
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REPORTS = ROOT / 'docs/reports'
paths = [
    REPORTS / 'SIM240_中文稿_导师审阅版_20261022.md',
    REPORTS / 'SIM240_First_Paper_English_20261028.md',
    REPORTS / 'SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md',
    REPORTS / 'SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md',
    REPORTS / 'SIM240_Supplementary_Methods_20261024/Table_S2_refinement.csv',
    REPORTS / 'SIM240_Supplementary_Methods_20261024/Table_S8_control_evidence.csv',
    REPORTS / 'PAPER1_claim_final_review_20261105/recomputed_44_records.csv',
    REPORTS / 'PAPER1_new_four_cases_acceptance_20261107/comparison.csv',
    REPORTS / 'PAPER1_new_four_cases_acceptance_20261107/REPORT.md',
    REPORTS / 'URV_S4_completed_review_20261104_143205/REPORT.md',
    REPORTS / 'URV_S4_TGE_zero_results_20261104_1719/REPORT.md',
    REPORTS / 'URV_S4_TGE_1p25_data_audit_20261105_100521/REPORT.md',
]
records = list(csv.DictReader(paths[6].open()))
paths += [ROOT / r['source'] for r in records]
baseline = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
(OUT / 'protected_inputs.json').write_text(json.dumps(baseline, indent=2, ensure_ascii=False) + '\n')
checked = []
for r in records:
    data = dict(line.split('=', 1) for line in (ROOT / r['source']).read_text().splitlines() if '=' in line)
    nu = (float(data['tau']) - .5) / 3 * float(data['dx_m']) ** 2 / float(data['dt_s'])
    k = nu * float(data['J_main_m2_s']) / float(data['acceleration_m_s2'])
    assert math.isclose(k, float(r['K_m3']), rel_tol=2e-14)
    assert math.isclose(k, float(data['Keff_m3']), rel_tol=2e-14)
    checked.append({'run_id': r['run_id'], 'K_recomputed_m3': k})
refinements = []
for r in csv.DictReader(paths[4].open()):
    component = 'Kyy' if r['direction'] == 'parallel' else 'Kxx'
    pair = [next(v for v in records if float(v['h_nm']) == float(r['h']) and float(v['d_nm']) == float(r['d']) and v['component'] == component and float(v['dx_nm']) == dx) for dx in (5, 2.5)]
    change = 100 * (float(pair[1]['K_m3']) / float(pair[0]['K_m3']) - 1)
    assert math.isclose(change, float(r['K_change_percent']), abs_tol=1e-11)
    refinements.append({'h_nm': float(r['h']), 'd_nm': float(r['d']), 'component': component, 'change_percent': change})
main = [r for r in records if float(r['dx_nm']) == 5]
peaks = {}
for component in ('Kxx', 'Kyy'):
    rows = [r for r in main if r['component'] == component]
    peaks[component] = {field: max(rows, key=lambda r: abs(float(r[field]))) for field in ('E_LC_percent', 'E_V2_percent')}
result = {'scope': 'saved scalar arithmetic only; not a new numerical acceptance or error bound', 'records_recomputed': len(checked), 'main_records': len(main), 'refinement_records': len(refinements), 'refinements': refinements, 'main_peaks': peaks, 'all_inputs_unchanged': all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha for name, sha in baseline.items()), 'protected_input_count': len(baseline)}
assert result['all_inputs_unchanged']
(OUT / 'scalar_checks.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('main_peaks', 'refinements')}, ensure_ascii=False))
for component, fields in peaks.items():
    print(component, {field: (r['run_id'], r[field]) for field, r in fields.items()})
