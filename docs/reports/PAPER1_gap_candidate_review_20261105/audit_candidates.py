"""Read-only candidate audit: saved fits, known data and design metadata only.

No solver/fitter/import of project analysis modules; reserved prediction CSVs are
hashed as opaque bytes and never parsed. No reserved flow-result paths are opened.
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import statistics

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CG = ROOT / 'docs/reports/Constrained_correlation_20261023'
CH = ROOT / 'docs/reports/bivariate_piecewise_comparison_20261022'
LOCK = ROOT / 'docs/reports/Correlation_selection_freeze_20261024'
protected = {}
access = {}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(path, mode='content'):
    path = path.resolve()
    key = str(path.relative_to(ROOT))
    h = digest(path)
    if key in protected:
        assert protected[key] == h
    protected[key] = h
    if access.get(key) != 'content':
        access[key] = mode
    return path


def read_json(path):
    return json.loads(bind(path).read_text())


def read_csv(path):
    with bind(path).open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def write_csv(name, rows):
    with (OUT / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def close(x, y, rtol=2e-12):
    return abs(x-y) <= rtol * max(abs(x), abs(y), 1e-100)


def blend(x, y, m):
    assert x >= 0 and y > 0 and m > 0
    if x == 0:
        return 0.
    low, high = min(x, y), max(x, y)
    return low / (1+(low/high)**m)**(1/m)


def g_value(fit, h, d, w, direction):
    s, t = w/h, d/h
    r = t*(3+t*(3+t))
    lp, lt = r/2, r/(r+2)
    at, pt, *mt = fit['T']; ap, pp, *mp = fit['P']
    et = blend(lt, math.exp(at)*s**pt, mt[0] if mt else 1)
    ep = et + blend(lp-et, math.exp(ap)*s**pp+s*s*t/2, mp[0] if mp else 1)
    return (h*1e-9)**3/12 * (1+(ep if direction == 'P' else et))


def ch_value(fit, h, d, w, direction):
    flat = (h*1e-9)**3/12
    t = d/h
    r = t*(3+t*(3+t))
    old = flat*(1+(r/2 if direction == 'P' else r/(r+2)))
    if d == 0:
        return flat
    a, b, c, q = fit['coefficients']
    x, z = math.log(h/w), math.log(d/w)
    g = a+b*z+c*x
    g += q*(x*x if fit['model'] == 'C4' else max(x-fit['tau'], 0.))
    return old/(1+math.exp(g))


lock = read_json(LOCK / 'candidate_lock.json')
lock_hash = digest(LOCK / 'candidate_lock.json')
assert lock_hash == bind(LOCK / 'candidate_lock.sha256').read_text().split()[0]
for name, h in lock['bound_files'].items():
    p = bind(LOCK / name, 'hash_only')
    assert digest(p) == h
assert lock['status'] == 'CANDIDATE_FROZEN_NOT_VALIDATED'
assert not lock['target_domain']['accuracy_validated']

fits = read_json(CG / 'fits.json')
old_fits = read_json(CH / 'fits.json')
for model in ['G4', 'G6']:
    assert fits[model] == lock['coefficients'][model]
    for direction in ['P', 'T']:
        loga, p, *m = fits[model][direction]
        assert math.exp(loga) > 0 and p > 0 and (not m or m[0] > 0)
    assert fits[model]['P'][1] < 3
full = {(r['model'], r['direction']): r for r in old_fits
        if r['scheme'] == 'full' and r['model'] in ['C4', 'H4']}
assert len(full) == 4

# Verify known old 36 raw results, explicitly obtained through the old data-role file.
known = read_csv(CG / 'data_roles.csv')
by_key = {r['key']: r for r in known}
raw_count = 0
for r in known:
    raw = dict(line.split('=', 1) for line in bind(Path(r['source'])).read_text().splitlines() if '=' in line)
    assert close(float(raw['Keff_m3']), float(r['K']))
    assert close(float(raw['mesa_gap_m'])*1e9, float(r['h']))
    assert close(float(raw['groove_depth_m'])*1e9, float(r['d']))
    assert close(float(raw['groove_width_m'])*1e9, float(r['w']))
    assert close(float(raw['dx_m']), 5e-9)
    raw_count += 1

# Evaluate stored C4/H4 full and outer-fold formulas, without any parameter fitting.
old_prediction_checks = []
for filename in ['full_fit_predictions.csv', 'outer_predictions.csv']:
    for r in read_csv(CH / filename):
        if r['model'] not in ['C4', 'H4']:
            continue
        if filename.startswith('full'):
            fit = full[(r['model'], r['direction'])]
        else:
            fit = next(f for f in old_fits if f['scheme'] == r['scheme']
                       and f['model'] == r['model'] and f['direction'] == r['direction']
                       and float(f['held_level']) == float(r['held_level']))
        k = ch_value(fit, float(r['h']), float(r['d']), 120., r['direction'])
        assert close(k, float(r['K_pred']))
        assert close(float(r['K_ref']), float(by_key[r['key']]['K']))
        old_prediction_checks.append({'model': r['model'], 'key': r['key'],
            'scheme': r.get('scheme', 'full'), 'relative_difference': k/float(r['K_pred'])-1})

# Recompute all stored known G4/G6 rows, including outer folds and known h25.
predictions = read_csv(CG / 'predictions.csv')
cv = {}
g_checks = []
for r in predictions:
    if r['model'] not in ['G4', 'G6']:
        continue
    tag = r['model'] + ('__'+r['scheme']+'_'+str(int(float(r['group'])))
                       if r['scheme'] in ['leave_h', 'leave_d'] else '')
    fit = fits[tag]
    h, d, w = (float(r[x]) for x in ['h_nm', 'd_nm', 'w_nm'])
    k = g_value(fit, h, d, w, r['direction'])
    ref = float(r['K_raw_m3'])
    assert close(k, float(r['K_pred_m3'])) and close(ref, float(by_key[r['key']]['K']))
    err = 100*(k/ref-1)
    assert abs(err-float(r['error_percent'])) < 1e-10
    g_checks.append(k/float(r['K_pred_m3'])-1)
    if r['scheme'] in ['leave_h', 'leave_d']:
        key = (r['scheme'], r['group'], h, d, w)
        cv.setdefault((r['model'], key), {})[r['direction']] = (k, ref)


def stats(errors):
    return {'n': len(errors), 'MAE_percent': statistics.mean(map(abs, errors)),
            'RMSE_percent': math.sqrt(statistics.mean(e*e for e in errors)),
            'max_abs_percent': max(map(abs, errors)), 'bias_percent': statistics.mean(errors)}


tradeoffs = []
for scheme in ['leave_h', 'leave_d']:
    keys = sorted(k for m, k in cv if m == 'G4' and k[0] == scheme)
    assert len(keys) == 15
    for model in ['G4', 'G6', 'MIX7']:
        errs = {q: [] for q in ['P', 'T', 'A']}
        for key in keys:
            pair = cv[(model, key)] if model != 'MIX7' else {
                'P': cv[('G4', key)]['P'], 'T': cv[('G6', key)]['T']}
            for direction in ['P', 'T']:
                k, ref = pair[direction]
                errs[direction].append(100*(k/ref-1))
            errs['A'].append(100*((pair['P'][0]/pair['T'][0])/(pair['P'][1]/pair['T'][1])-1))
        for quantity in ['P', 'T', 'A']:
            tradeoffs.append({'scheme': scheme, 'model': model, 'quantity': quantity, **stats(errs[quantity])})
saved = read_csv(LOCK / 'tradeoffs.csv')
for row in tradeoffs:
    original = next(r for r in saved if all(r[k] == row[k] for k in ['scheme', 'model', 'quantity']))
    for k in ['MAE_percent', 'RMSE_percent', 'max_abs_percent', 'bias_percent']:
        assert abs(row[k]-float(original[k])) < 1e-10
write_csv('known_CV_recomputed.csv', tradeoffs)

# Record sample-domain membership separately from theoretical construction domain.
domains = []
for h, d, w in sorted({(float(r['h']), float(r['d']), float(r['w'])) for r in known}):
    s, t = w/h, d/h
    inside = .8-1e-12 <= s <= 3.2+1e-12 and 1/3-1e-12 <= t <= 1.6+1e-12
    domains.append({'h_nm': h, 'd_nm': d, 'w_nm': w, 's_w_over_h': s, 't_d_over_h': t,
        'C4_H4_training_geometry': True, 'G4_G6_training_geometry': h >= 50,
        'inside_G_v1_target': inside, 'independent_test': False,
        'role': 'known_development' if h >= 50 else 'known_thin_gap_supplement'})
write_csv('known_domain_membership.csv', domains)

# Concrete counterexamples of C/H structural extrapolation, not numerical flow results.
witnesses = []
for model in ['C4', 'H4']:
    for d in [.01, 100., 120., 1e8]:
        h, w = 75., 120.
        flat = (h*1e-9)**3/12
        fit = full[(model, 'T')]
        k = ch_value(fit, h, d, w, 'T')
        witnesses.append({'model': model, 'direction': 'T', 'h_nm': h, 'd_nm': d, 'w_nm': w,
                          'K_over_flat': k/flat, 'scope': 'formula_only_diagnostic_not_accuracy_test'})
write_csv('C4_H4_structural_witnesses.csv', witnesses)
assert all(r['K_over_flat'] < 1 for r in witnesses if r['d_nm'] in [.01, 1e8])

# Existing reserved design metadata only: never read reserved predictions/flow results.
design = read_csv(ROOT / 'docs/reports/correlation_design_review_20261022/candidate_cases.csv')
groups = {}
for r in design:
    if r['role'] != 'prediction_test':
        continue
    geometry = tuple(float(r[k]) for k in ['h_nm', 'd_nm', 'w_nm'])
    groups.setdefault(geometry, []).append(r)
matrix = []
for number, ((h, d, w), group) in enumerate(sorted(groups.items()), 1):
    assert {r['direction'] for r in group} == {'P', 'T'}
    assert (h, d, w) not in {(r['h_nm'], r['d_nm'], r['w_nm']) for r in domains}
    s, t = w/h, d/h
    assert .8 <= s <= 3.2 and 1/3 <= t <= 1.6
    matrix.append({'test_id': f'V1-{number:02d}', 'h_nm': h, 'd_nm': d, 'w_nm': w,
        'period_nm': 2*w, 's_w_over_h': s, 't_d_over_h': t,
        'directions': 'P_and_T', 'primary_dx_nm_from_old_lock': 5,
        'extra_grid_dx_nm_from_old_lock': '2.5;1.25' if (h,d,w) == (60,80,180) else '',
        'observed_flow_result_read_this_audit': False, 'external_non_exposure': 'UNVERIFIED',
        'reference_qualified_this_audit': False, 'execution_authorized_this_audit': False,
        'planned_P_id': next(r['planned_case_id'] for r in group if r['direction'] == 'P'),
        'planned_T_id': next(r['planned_case_id'] for r in group if r['direction'] == 'T')})
assert len(matrix) == 8
write_csv('independent_test_design_metadata.csv', matrix)

for folder, names in [(CG, ['PROTOCOL.md','REPORT.md','models.py','predict.py','summary.csv']),
                      (CH, ['PROTOCOL.md','REPORT.md','FORMULAS.md','cv_summary.csv','formula_checks.json']),
                      (LOCK, ['FREEZE_RULES.md','REPORT.md','parameter_stability.csv','audit_summary.json'])]:
    for name in names:
        bind(folder/name)
for name in ['G4_derivation_source_audit_20261025/REPORT.md',
             'G4_derivation_source_audit_20261025/review_decision.json',
             'PAPER1_h25_reference_candidate_audit_20261104_225645/REPORT.md',
             'D4_reference_revision_review_20261025/REPORT.md',
             'URV_S2_completed_review_20261103_095422/REPORT.md',
             'URV_S4_completed_review_20261104_143205/REPORT.md',
             'PAPER1_formula_comparison_20261105/REPORT.md']:
    bind(ROOT/'docs/reports'/name)
for name in ['README.md','PROTOCOL.md']:
    bind(ROOT/'CASE/D_series/D4_variable_groove_transport_20261023'/name)

coefficients = {'C4_H4_full18': list(full.values()), 'G4_G6_frozen': lock['coefficients']}
(OUT/'reviewed_coefficients.json').write_text(json.dumps(coefficients, ensure_ascii=False, indent=2)+'\n')
summary = {'audit_id': 'PAPER1_gap_candidate_review_20261105', 'solver_runs': 0, 'fit_calls': 0,
    'reserved_flow_results_read': False, 'reserved_prediction_csv_parsed': False,
    'candidate_lock_sha256': lock_hash, 'candidate_lock_status': lock['status'],
    'lock_bound_file_hashes_verified': len(lock['bound_files']), 'known_raw_results_checked': raw_count,
    'C4_H4_saved_prediction_rows_recomputed': len(old_prediction_checks),
    'C4_H4_max_relative_recompute_difference': max(abs(r['relative_difference']) for r in old_prediction_checks),
    'G4_G6_saved_prediction_rows_recomputed': len(g_checks),
    'G4_G6_max_relative_recompute_difference': max(map(abs, g_checks)),
    'G4_G6_CV_direction_rows_recomputed': len(cv)*2,
    'tradeoff_summary_rows_recomputed': len(tradeoffs),
    'known_geometries': len(domains),
    'G_training_geometries_inside_target': sum(r['inside_G_v1_target'] and r['G4_G6_training_geometry'] for r in domains),
    'G_training_geometries_outside_target': sum(not r['inside_G_v1_target'] and r['G4_G6_training_geometry'] for r in domains),
    'old_reserved_design_geometries': len(matrix), 'old_reserved_primary_direction_points': len(matrix)*2,
    'external_non_exposure_verified': False, 'new_scientific_acceptance': False,
    'formal_MODEL_COMPARISON_changed': False, 'new_simulation_run_id': None}
(OUT/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
(OUT/'source_manifest.json').write_text(json.dumps({p:{'sha256':h,'access':access[p]} for p,h in protected.items()},ensure_ascii=False,indent=2)+'\n')
changed = [p for p,h in protected.items() if digest(ROOT/p) != h]
assert not changed
(OUT/'verification.json').write_text(json.dumps({'protected_inputs':len(protected),'changed_inputs':changed,
    'reserved_prediction_files_hash_only':[p for p,m in access.items() if m=='hash_only' and 'reserved_' in p],
    'solver_calls':0,'optimizer_calls':0,'new_formal_acceptance':False},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary, ensure_ascii=False))
