"""Bounded arithmetic on eight already-known D4 results; no solver or field reader."""
from pathlib import Path
import csv
import hashlib
import json
import math

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
SCALE = ROOT / 'docs/reports/PAPER1_scale_failure_audit_20261108'
MECH = ROOT / 'docs/reports/PAPER1_mechanism_offline_20261109'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def kv(path):
    return dict(line.split('=', 1) for line in path.read_text().splitlines() if '=' in line)

def near(a, b):
    assert math.isclose(a, b, rel_tol=2e-12, abs_tol=1e-35), (a, b)

def dump_csv(name, rows):
    with (OUT / name).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

protected = [
    ROOT / 'docs/reports/SIM240_中文稿_导师审阅版_20261022.md',
    ROOT / 'docs/reports/SIM240_First_Paper_English_20261028.md',
    ROOT / 'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md',
    ROOT / 'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md',
    ROOT / 'docs/reports/PAPER1_submission_package_20261109/MANIFEST.md',
    ROOT / 'docs/reports/PAPER1_conclusions_current_20261109.md',
    SCALE / 'scalar_records.csv', SCALE / 'source_manifest.json',
    MECH / 'positive_excess_diagnostic.csv', MECH / 'source_manifest.json',
]
before = {str(p.relative_to(ROOT)): sha(p) for p in protected}
old_sha = json.loads((SCALE / 'source_manifest.json').read_text())
all_rows = list(csv.DictReader((SCALE / 'scalar_records.csv').open()))
rows = [r for r in all_rows if r['role'].startswith('D4')
        and float(r['h_nm']) == 75 and float(r['d_nm']) == 120
        and float(r['w_nm']) in (60, 240) and float(r['dx_nm']) in (5, 2.5)]
assert len(rows) == 8
assert len({(r['w_nm'], r['dx_nm'], r['direction']) for r in rows}) == 8
diag_rows = list(csv.DictReader((MECH / 'positive_excess_diagnostic.csv').open()))
bound_inputs = {}
records = []
configs = []
for r in rows:
    path = ROOT / r['source']
    assert 'prediction' not in r['source']
    for name in ('result.txt', 'run_manifest.txt', 'exit_code.txt'):
        p = path.parent / name
        assert sha(p) == old_sha[str(p)], str(p)
        bound_inputs[str(p.relative_to(ROOT))] = sha(p)
    raw = kv(path)
    manifest = kv(path.parent / 'run_manifest.txt')
    assert (path.parent / 'exit_code.txt').read_text().strip() == '0'
    assert manifest['binary_sha256'] == r['binary_sha256']
    assert manifest['run_id'] == raw['run_id'] == r['run_id']
    assert raw['direction'] == {'P': 'parallel', 'T': 'perpendicular'}[r['direction']]
    assert raw['geometry_PASS'] == 'true' and raw['NUMERICAL_GATE'] == 'PASS'
    cfg = path.parent / 'run_config.txt'
    assert sha(cfg) == manifest['config_sha256']
    bound_inputs[str(cfg.relative_to(ROOT))] = sha(cfg)
    configs.append(kv(cfg))
    for field, nm in [('mesa_gap_m', 75), ('groove_depth_m', 120),
                      ('groove_width_m', float(r['w_nm'])),
                      ('Lx_m', 2*float(r['w_nm'])), ('Ly_m', 2*float(r['w_nm'])),
                      ('dx_m', float(r['dx_nm']))]:
        near(float(raw[field]), nm * 1e-9)
    K = float(raw['nu_phys_m2_s']) * float(raw['J_main_m2_s']) / float(raw['acceleration_m_s2'])
    near(K, float(raw['Keff_m3']))
    near(K, float(r['K_m3']))
    h, d = 75e-9, 120e-9
    LC = ((h**3 + (h+d)**3)/24 if r['direction'] == 'P'
          else h**3*(h+d)**3/(6*(h**3+(h+d)**3)))
    near(LC, float(r['K_LC_m3']))
    a = LC/K
    records.append(dict(run_id=r['run_id'], source=r['source'], w_nm=float(r['w_nm']),
                        P_nm=2*float(r['w_nm']), dx_nm=float(r['dx_nm']), direction=r['direction'],
                        K_m3=K, K_LC_m3=LC, F=1/a, r=a-1,
                        binary_sha256=r['binary_sha256'], stored_RESULT_PASS=raw['RESULT_PASS']))

assert len({r['binary_sha256'] for r in records}) == 1
# Save differing configuration keys for inspection, not a blanket equivalence claim.
config_differences = {k: sorted({c.get(k, '<missing>') for c in configs})
                      for k in set().union(*(set(c) for c in configs))
                      if len({c.get(k, '<missing>') for c in configs}) > 1}

pairs, mechanism = [], []
for dx in (5.0, 2.5):
    for w in (60.0, 240.0):
        pair = {r['direction']: r for r in records if r['dx_nm'] == dx and r['w_nm'] == w}
        p, t = pair['P'], pair['T']
        ap, at = 1+p['r'], 1+t['r']
        A = p['K_m3']/t['K_m3']
        ALC = p['K_LC_m3']/t['K_LC_m3']
        B = ALC/A
        near(B, ap/at)
        c = 2/(ap+at)
        floor = abs(ap-at)/(ap+at)
        near(c*ap-1, -(c*at-1))
        near(max(abs(c*ap-1), abs(c*at-1)), floor)
        for trial in (1/ap, 1/at, c/2, 2*c):
            assert max(abs(trial*ap-1), abs(trial*at-1)) >= floor-1e-12
        pairs.append(dict(w_nm=w, P_nm=2*w, dx_nm=dx, F_P=p['F'], F_T=t['F'],
                          A_reference=A, A_LC=ALC, B=B, A_bias_percent=100*(B-1),
                          scalar_c_opt=c, scalar_floor_percent=100*floor))
        for scheme in ('wall_quadratic', 'odd_extension'):
            sums, residuals = {}, {}
            for direction in ('P', 'T'):
                rec = pair[direction]
                terms = [x for x in diag_rows if x['run_id'] == rec['run_id'] and x['scheme'] == scheme]
                assert len(terms) == (2 if direction == 'P' else 3)
                S = sum(float(x['R_excess_term_over_R_LC']) for x in terms)
                near(S, float(terms[0]['sum_terms_over_R_LC']))
                near(rec['r'], float(terms[0]['drive_excess_over_R_LC']))
                sums[direction] = S
                residuals[direction] = rec['r']-S
                for term in terms:
                    mechanism.append(dict(w_nm=w, dx_nm=dx, scheme=scheme, direction=direction,
                        run_id=rec['run_id'], term=term['term'],
                        term_over_directional_R_LC=float(term['R_excess_term_over_R_LC']),
                        fraction_positive_sum=float(term['term_fraction_of_positive_sum']),
                        sum_positive=S, drive_excess=rec['r'], signed_residual=rec['r']-S))
            Bdiag = (1+sums['P'])/(1+sums['T'])
            near((1+sums['P']+residuals['P'])/(1+sums['T']+residuals['T']), B)
            pairs[-1][scheme+'_B_from_positive_terms'] = Bdiag
            pairs[-1][scheme+'_B_relative_difference_percent'] = 100*(Bdiag/B-1)

dump_csv('selected_records.csv', records)
dump_csv('paired_evidence.csv', pairs)
dump_csv('mechanism_link.csv', mechanism)
after = {str(p.relative_to(ROOT)): sha(p) for p in protected}
assert before == after
assert all(sha(ROOT/p) == value for p, value in bound_inputs.items())
verification = dict(scope='existing scalar arithmetic and already-computed gradient diagnostics only',
    records=8, physical_geometries=2, grid_pairs=4, common_binary=records[0]['binary_sha256'],
    original_small_files_match_prior_binding=True, config_differences=config_differences,
    protected_before=before, protected_after=after, bound_raw_inputs=bound_inputs,
    script_sha256=sha(Path(__file__)), original_fields_reprocessed=False,
    new_solver_runs=0, new_fits=0, independent_numerical_acceptance=False,
    reference_qualified=False, strict_error_bound_established=False, submission_ready=False)
(OUT/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(pairs=pairs, config_differences=config_differences,
                     protected_inputs_unchanged=True, source_binding_matched=True),ensure_ascii=False,indent=2))
