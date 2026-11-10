"""Verify source preservation, exact scalar checks, locators and document integrity.

These checks do not prove H1 admissibility or novelty; those arguments are written
in LOWER_BOUND_REVIEW and the first-hand literature matrix.
"""
from pathlib import Path
from fractions import Fraction as F
import csv, hashlib, json, math, re

OUT=Path(__file__).resolve().parent
checks=[]
def check(name,ok):checks.append({'check':name,'passed':bool(ok)})
g=F(1,4)-F(1,6);gp=F(1,4)-F(1,2)+F(1,3)
check('exact trial work integral',g==F(1,12))
check('exact trial gradient integral',gp==F(1,12))
check('fixed-drive positive difference coefficient',2*g-gp==F(1,12))
check('fixed-flux profile integral',12*g==1)
check('fixed-flux profile energy',144*gp==12)
for h in [F(1,2),F(1),F(3)]:
    lower=h**3/12;up=(h**3+h**3)/24;ut=h**6/(6*(h**3+h**3))
    check('flat limits '+str(h),lower==up==ut)
d=F(2)
check('closed-gap along upper bound is positive',d**3/24>0)
L,K,U=F(1),F(4),F(9)
check('log midpoint counterexample',K*K>L*U and abs(L/K-1)<abs(U/K-1))
records=json.loads((OUT/'crossref_records.json').read_text())
check('ten DOI identities',len(records)==10 and all(r.get('returned_doi','').lower()==r['requested_doi'].lower() for r in records))
q=(OUT/'SEARCH_LOG.md').read_text();check('22 recorded queries',len(re.findall(r'^\d+\. `',q,re.M))==22)
protected=json.loads((OUT/'protected_inputs.json').read_text())
drift=[p for p,h in protected.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
check('all bound scientific inputs unchanged',not drift)
for p in OUT.glob('*.md'):
    t=p.read_text();check(p.name+' whitespace',all(l.rstrip()==l for l in t.splitlines()))
    for link in re.findall(r'\]\(([^)]+)\)',t):
        if not link.startswith('http'):
            check(p.name+' link '+link,(p.parent/link.split('#')[0]).resolve().exists())
check('publisher Tran PDF identity',hashlib.sha256((OUT/'Tran2021_publisher.pdf').read_bytes()).hexdigest()=='a6270962c6bbd9f35609fb0d9bbfa58614a3ca00182d74646efc921332b982e0')
result={'all_passed':all(r['passed'] for r in checks),'check_count':len(checks),'checks':checks,
    'protected_input_count':len(protected),'changed_inputs':drift,'new_solver_calls':0,'raw_fields_read':False,
    'fit_calls':0,'reserved_prediction_results_read':False,'new_run_id':None,'formal_manuscripts_changed':False,
    'independent_external_reviewer_certified':False,'model_switch_verified':False,
    'scope':'source, exact arithmetic and report consistency; theory and literature verdicts require reading the written arguments',
    'reference_qualified':False,'submission_ready':False}
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'all_passed':result['all_passed'],'failed':[r for r in checks if not r['passed']]}))
raise SystemExit(0 if result['all_passed'] else 1)
