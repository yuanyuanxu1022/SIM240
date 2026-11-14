"""Bounded claim audit: existing tables only; no solver imports or qualification writes."""
import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
R = ROOT / 'docs/reports'
FILES = [
    'SIM240_中文稿_导师审阅版_20261022.md',
    'SIM240_First_Paper_English_20261028.md',
    'SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md',
    'SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md',
    'PAPER1_conclusions_current_20261109.md',
    'PAPER1_submission_manuscript_20261110/SIM240_submission_CN.md',
    'PAPER1_submission_manuscript_20261110/SIM240_submission_EN.md',
    'PAPER1_CURRENT_FILES_AUTHORITY_20261110.md',
    'PAPER1_submission_package_20261109/MANIFEST.md',
    'SIM240_manuscript_revision_20261018/map36_evidence.csv',
    'PAPER1_fem_v2_results_20261114/PAIR_TABLE_v2.csv',
    'PAPER1_fem_v2_results_review_20261114/STATISTICS.json',
    'PAPER1_fem_v2_doe_20261114/DOE_V2_NEW_REFERENCE.json',
    'PAPER1_fem_v2_doe_20261114/DOE_V2_NEW_REFERENCE_15.csv',
    'PAPER1_fem_v2_adoption_review_20261114/ADOPTION_REVIEW.md',
    'Appendix_E_final_review_20261028/ASTRA_REVIEW.md',
    'PAPER1_doe_wording_fix_20261114/verification.json',
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def table(name):
    with (R / name).open(newline='') as f:
        return list(csv.DictReader(f))


def summary(v):
    return dict(n=len(v), signed_mean=statistics.mean(v),
                mean_absolute=statistics.mean(abs(x) for x in v),
                minimum=min(v), maximum=max(v),
                positive=sum(x > 0 for x in v), negative=sum(x < 0 for x in v))


def lc(h, d, direction):
    return ((h**3 + (h+d)**3)/24 if direction == 'P'
            else 1/(6*(h**-3+(h+d)**-3))) * 1e-27


def factor(d, direction):
    a, b = (1.7685, 1.6331) if direction == 'P' else (0.4900, 0.6990)
    return 1/(1+a*(d/120)**b)


paths = [R / p for p in FILES]
pkg = ROOT / 'CASE/paper1_fem_stokes_reference_v2'
receipts = sorted(pkg.glob('runs/*/VERIFY_RECEIPT.json'))
assert len(receipts) == 12
paths += receipts + [pkg/'verify_results.py', pkg/'PROTOCOL.md', pkg/'acceptance_rule.json']
main = table('SIM240_manuscript_revision_20261018/map36_evidence.csv')
assert len(main) == 36
paths += [ROOT / x['result_path'] for x in main]
before = {str(p.relative_to(ROOT)): dict(sha256=sha(p), bytes=p.stat().st_size)
          for p in paths}
for x in main:
    assert sha(ROOT / x['result_path']) == x['result_sha256']
    h, d = float(x['h_nm']), float(x['d_nm'])
    model, ref = lc(h, d, x['direction']), float(x['K_DNS_m3'])
    assert abs(model/float(x['K_model_m3'])-1) < 1e-12
    assert abs((model/ref-1)*100-float(x['E_pct'])) < 1e-9
    v2 = (model*factor(d, x['direction'])/ref-1)*100
    assert abs(v2-float(x['V2_rounded_residual_pct'])) < 1e-9
    x['checked_v2'] = v2

main_stats = {}
for direction in ['P', 'T']:
    rows = [x for x in main if x['direction'] == direction]
    old = [float(x['E_pct']) for x in rows]
    new = [x['checked_v2'] for x in rows]
    main_stats[direction] = dict(LC=summary(old), V2=summary(new),
        improved=sum(abs(b) < abs(a) for a, b in zip(old, new)))

pairs = table('PAPER1_fem_v2_results_20261114/PAIR_TABLE_v2.csv')
complete = [p for p in pairs if p['K_P_m3'] and p['K_T_m3']]
assert len(pairs) == 19 and len(complete) == 17
counts = Counter()
for p in pairs:
    for direction in ['P', 'T']:
        if p[f'K_{direction}_m3']:
            counts[direction] += 1
            counts['FVM' if p[f'K_{direction}_source'] == 'qualified_FVM' else 'FEM'] += 1
    if not p['K_T_m3']:
        continue
    h, d = [float(s[1:]) for s in p['geometry'].split('/')]
    kp, kt = float(p['K_P_m3']), float(p['K_T_m3'])
    lp, lt = lc(h,d,'P'), lc(h,d,'T')
    a = kp/kt
    al, av = lp/lt, lp*factor(d,'P')/(lt*factor(d,'T'))
    beta = lambda x: math.degrees(math.atan(1/x))
    checks = {
        'A_ref': a, 'beta_ref_deg': beta(a), 'A_LC': al, 'A_V2': av,
        'T_LC_vs_ref_percent': (lt/kt-1)*100,
        'T_V2_vs_ref_percent': (lt*factor(d,'T')/kt-1)*100,
        'LC_A_vs_ref_percent': (al/a-1)*100,
        'V2_A_vs_ref_percent': (av/a-1)*100,
        'LC_beta_vs_ref_deg': beta(al)-beta(a),
        'V2_beta_vs_ref_deg': beta(av)-beta(a),
    }
    for key, val in checks.items():
        assert abs(float(p[key])-val) < 1e-8, (p['geometry'],key,val,p[key])
assert dict(counts) == {'P':19,'FEM':34,'T':17,'FVM':2}, counts
oldstats = json.loads((R/FILES[11]).read_text())
new_stats = {}
for col in oldstats['summary']:
    v = [float(p[col]) for p in complete]
    new_stats[col] = summary(v)
    for field in ['n','signed_mean','mean_absolute','positive','negative']:
        assert abs(new_stats[col][field]-oldstats['summary'][col][field]) < 1e-10
bad_a = [p['geometry'] for p in complete if abs(float(p['V2_A_vs_ref_percent'])) > abs(float(p['LC_A_vs_ref_percent']))]
bad_b = [p['geometry'] for p in complete if abs(float(p['V2_beta_vs_ref_deg'])) > abs(float(p['LC_beta_vs_ref_deg']))]
negative_a = [p['geometry'] for p in complete if float(p['LC_A_vs_ref_percent']) < 0]
assert bad_a == bad_b == ['h50/d25','h75/d25','h125/d50']
assert negative_a == ['h75/d25','h125/d25']

grid = table('PAPER1_fem_v2_doe_20261114/DOE_V2_NEW_REFERENCE_15.csv')
doe = json.loads((R/FILES[12]).read_text())
assert len(grid) == 15
hs, ds = [50,75,125], [25,50,75,100,120]
shares = {}
for name in ['LC_P','V2_P','LC_T','V2_T']:
    vals = {(int(r['h_nm']),int(r['d_nm'])):float(r[name+'_percent']) for r in grid}
    mean = statistics.mean(vals.values())
    mh = {h:statistics.mean(vals[h,d] for d in ds) for h in hs}
    md = {d:statistics.mean(vals[h,d] for h in hs) for d in ds}
    total = sum((v-mean)**2 for v in vals.values())
    sh = 5*sum((v-mean)**2 for v in mh.values())
    sd = 3*sum((v-mean)**2 for v in md.values())
    ans = dict(grand_mean=mean, share_h_percent=100*sh/total,
               share_d_percent=100*sd/total,
               share_interaction_percent=100*(total-sh-sd)/total)
    target=doe['new_set_decomposition'][name]
    assert all(abs(v-target[k]) < 2e-5 for k,v in ans.items())
    shares[name]=ans
assert all(float(r['V2_P_percent']) > 0 for r in grid if r['h_nm']=='75')
assert all(float(r['V2_P_percent']) < 0 for r in grid if r['h_nm']=='125')
grid_rows = []
for path in receipts:
    receipt = json.loads(path.read_text())
    for coarse, fine in zip(receipt['levels'], receipt['levels'][1:]):
        kc, kf = coarse['K_recomputed_m3'], fine['K_recomputed_m3']
        coarse_denominator = 100*abs(kf/kc-1)
        fine_denominator = 100*abs(kc/kf-1)
        assert abs(coarse_denominator-fine['K_change_from_coarser_recomputed_percent']) < 1e-12
        grid_rows.append(dict(run_id=path.parent.name, dx_nm=fine['dx_nm'],
            coarse_denominator_percent=coarse_denominator,
            fine_denominator_percent=fine_denominator))
grid_maxima = [max((x for x in grid_rows if x['dx_nm']==level),
                  key=lambda x:x['coarse_denominator_percent']) for level in [2.5,1.25]]
assert [f"{x['fine_denominator_percent']:.4f}" for x in grid_maxima] == ['0.1925','0.0910']
assert [f"{x['coarse_denominator_percent']:.4f}" for x in grid_maxima] == ['0.1921','0.0909']
after = {str(p.relative_to(ROOT)): dict(sha256=sha(p),bytes=p.stat().st_size) for p in paths}
assert before == after
result = dict(status='PASS_BOUNDED_TABLE_ARITHMETIC', source_files_checked=len(before),
    original_result_file_hashes_checked=36, main_statistics=main_stats,
    comparison_counts=dict(counts), paired_geometries=17,
    alternative_statistics=new_stats, V2_A_and_angle_worse=bad_a,
    LC_A_negative=negative_a, descriptive_shares_from_6dp_csv=shares,
    grid_change_denominator_audit=dict(receipts_read=12, adjacent_pairs=24,
        maxima=grid_maxima,
        finding='Published 0.1925/0.0910 values match finer-denominator rounding; frozen verifier and receipts use coarser denominator. No change to thresholds or historical verdicts.'),
    changed_inputs=[], new_simulations=0, full_PDE_reassembly=False,
    full_field_reintegration=False, reference_status_changed=False,
    limitation='Table arithmetic and stored original-result hashes; not a fresh numerical acceptance or physical validation.')
(OUT/'INPUT_SNAPSHOT.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n')
(OUT/'CHECKS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','source_files_checked','comparison_counts','paired_geometries','changed_inputs']},ensure_ascii=False))
