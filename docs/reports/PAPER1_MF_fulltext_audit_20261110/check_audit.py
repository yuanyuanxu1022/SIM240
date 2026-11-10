"""Verify source counterexample, saved arithmetic, and protected file identities."""
from pathlib import Path
import csv
import hashlib
import json
import math
import re
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
REP = ROOT / 'docs/reports'
OLD = REP / 'PAPER1_nearest_work_comparison_20261109'
checks = []


def check(name, ok, detail=None):
    c = dict(check=name, passed=bool(ok))
    if detail is not None:
        c['detail'] = detail
    checks.append(c)


protected = json.loads((OUT / 'protected_inputs.json').read_text())
for name, digest in protected.items():
    check('protected input ' + name, hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest)

pdf = OLD / 'sources/round2/Mohammadi2013_jfm.pdf'
page34 = subprocess.run(['pdftotext', '-f', '12', '-l', '12', '-layout', str(pdf), '-'],
    check=True, capture_output=True, text=True).stdout
page41 = subprocess.run(['pdftotext', '-f', '19', '-l', '19', '-layout', str(pdf), '-'],
    check=True, capture_output=True, text=True).stdout
check('printed page 34 is PDF page 12', page34.lstrip().startswith('34'))
check('Figure 6 identified on page 34', 'F IGURE 6.' in page34)
check('source counterexample S=0.08 visible in extracted Figure 6 labels', '0.08' in page34)
check('Figure 6 has S=0.06 cases too; presence is not maximum', 'S = 0.06' in page34)
check('source within-50-percent wording', 'still within 50 %' in page34)
check('printed page 41 contains hydraulic-aperture subsection', '4.4.2.' in page41 and 'hydraulically equivalent channel opening' in page41)
norm = lambda t: re.sub(r'\s+', ' ', t)
check('source explicitly could not confirm actual high-wavenumber limit',
      'confirm if this is the actual limit' in norm(page41))
check('source suggests actual limit differs', 'this limit will be different' in norm(page41))

script = (OLD / 'check_round2.py').read_text()
check('old test used presence of S=0.06 as purported maximum', '("振幅上限 0.06", "S = 0.06")' in script)
check('old ratio test hard-coded S_CAP', 'S_CAP = 0.06' in script)

with (REP / 'SIM240_manuscript_revision_20261018/map36_evidence.csv').open() as handle:
    records = list(csv.DictReader(handle))
geometries = sorted({(float(r['h_nm']), float(r['d_nm'])) for r in records})
check('primary source 36 records and 18 geometries', len(records) == 36 and len(geometries) == 18)
S_A = [2*d/h for h,d in geometries]
S_B = [2*d/(h+d/2) for h,d in geometries]
S_C = [2*d/(h+d) for h,d in geometries]
check('A range arithmetic', math.isclose(min(S_A), .4) and math.isclose(max(S_A), 8))
check('B range arithmetic', math.isclose(min(S_B), 4/11) and math.isclose(max(S_B), 8/3))
check('C is a counterexample to B being smallest possible convention',
      all(c < b for c,b in zip(S_C, S_B)) and math.isclose(min(S_C), 1/3) and math.isclose(max(S_C), 1.6))
for h,d in geometries:
    Hmean = h+d/2
    for label,H0,expected_mean in [('A',h,-d/h),('B',Hmean,0),('C',h+d,d/(h+d))]:
        calculated = 2-2*Hmean/H0
        check(f'h{h:g}d{d:g} convention {label} Save', math.isclose(calculated, expected_mean, abs_tol=1e-12))
check('saved LC overestimates conductance throughout primary36',
      all(float(r['K_model_m3']) > float(r['K_DNS_m3']) for r in records))
check('corresponding resistance ratios are below one',
      all(0 < float(r['K_DNS_m3'])/float(r['K_model_m3']) < 1 for r in records))

arithmetic = json.loads((OUT / 'arithmetic.json').read_text())
for example in arithmetic['reference_geometry_examples']:
    check(example['direction'] + ' Href geometric mean 125nm', example['H_ref_nm'] == 125)
    H = (12*example['K_LB_m3'])**(1/3)*1e9
    check(example['direction'] + ' hydraulic aperture derived from existing K',
          math.isclose(H,example['H_hyd_from_K_LB_nm']) and not math.isclose(H,125))
check('two principal hydraulic apertures differ at one geometry',
      len(arithmetic['reference_geometry_examples']) == 2 and
      not math.isclose(*[r['H_hyd_from_K_LB_nm'] for r in arithmetic['reference_geometry_examples']]))

cn = (OUT / 'CANDIDATE_CN_v3.md').read_text()
en = (OUT / 'CANDIDATE_EN_v3.md').read_text()
for name,t in [('CN',cn),('EN',en)]:
    body = t.split('## §1.2' if name=='CN' else '## Section 1.2',1)[1].split('\n## ',1)[0]
    refs = re.findall(r'\[(Ng|MF|St)\]',body)
    check(name + ' related-work citation keys in intended first-use order', refs == ['Ng','MF','St'])
    check(name + ' no hard S=0.06 exclusion in candidate body', '0.06' not in body)
    check(name + ' geometry volume identity stated', r'H_{\rm ref}=V_f/A_{\rm plan}=h+d/2' in t)
    check(name + ' MF opening reference included', r'EC_h' in t and '4.4.2' in t)

for name in ['REPORT.md','CANDIDATE_CN_v3.md','CANDIDATE_EN_v3.md','SOURCE_NOTES.md']:
    t=(OUT/name).read_text()
    check(name + ' no vertical-tab formula corruption','\x0b' not in t)
    for dest in re.findall(r'\]\(([^)]+)\)',t):
        if '://' not in dest:
            check(name + ' local link '+dest,(OUT/dest.partition('#')[0]).exists())

result = dict(checks_passed=sum(c['passed'] for c in checks), checks_failed=sum(not c['passed'] for c in checks),
    checks=checks, scope='Source locating, scalar arithmetic, candidate consistency and hashes; not theory certification or a numerical gate',
    formal_manuscripts_modified=False, original_round2_artifacts_modified=False,
    independent_human_signoff='not asserted', new_run_id=None, submission_ready=False)
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(passed=result['checks_passed'],failed=[c for c in checks if not c['passed']]),ensure_ascii=False))
assert result['checks_failed']==0
