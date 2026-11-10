"""Check published fixed V2 on saved scalars; do not fit or run CV."""
from pathlib import Path
import csv
import hashlib
import json
import math

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
REP=ROOT/'docs/reports'
checks=[]


def check(name,condition):checks.append(dict(check=name,passed=bool(condition)))
def read(path):
    with path.open() as handle:return list(csv.DictReader(handle))


for name,digest in json.loads((OUT/'protected_inputs.json').read_text()).items():
    check('input identity '+name,hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest)
source=read(REP/'SIM240_manuscript_revision_20261018/map36_evidence.csv')
saved=read(OUT/'fixed_V2_primary36_checked.csv')
summary=json.loads((OUT/'fixed_formula_check.json').read_text())
check('36 scalar source rows',len(source)==len(saved)==36)
check('18 geometry groups',len({(r['h_nm'],r['d_nm']) for r in source})==18)
coefficients={'P':(1.7685,1.6331),'T':(.4900,.6990)}
residuals=[]
for r,s in zip(source,saved):
    a,b=coefficients[r['direction']]
    factor=1/(1+a*(float(r['d_nm'])/120)**b)
    e=100*(factor*float(r['K_model_m3'])/float(r['K_DNS_m3'])-1)
    check(r['result_path']+' published residual',abs(e-float(r['V2_rounded_residual_pct']))<1e-10)
    check(r['result_path']+' audit row',s['raw_result_path']==r['result_path'] and abs(e-float(s['V2_residual_percent']))<1e-10)
    residuals.append(e)
mae=sum(abs(e) for e in residuals)/len(residuals)
check('primary MAE',math.isclose(mae,summary['primary']['MAE_percent'],abs_tol=1e-10))
check('primary maximum',math.isclose(max(map(abs,residuals)),summary['primary']['max_absolute_percent'],abs_tol=1e-10))
check('four records exceed illustrative 10% line',sum(abs(e)>10 for e in residuals)==4)
thin=[r for r in saved if float(r['h_nm'])==25]
check('three h25 geometries and six directional records',len(thin)==6 and len({r['d_nm'] for r in thin})==3)
check('h25 P signed residuals are all positive',all(float(r['V2_residual_percent'])>0 for r in thin if r['direction']=='P'))
check('h25 T signed residuals are all negative',all(float(r['V2_residual_percent'])<0 for r in thin if r['direction']=='T'))
refined=read(REP/'SIM240_Supplementary_Methods_20261024/Table_S7_thin_gap_correction.csv')
check('saved two-grid contrast is specific h25 d100 Kxx',len(refined)==2 and all(float(r['h_nm'])==25 and float(r['d_nm'])==100 and r['direction']=='Kxx' for r in refined))
check('both saved two-grid discrepancies are negative',all(float(r['V2_bias_percent'])<0 for r in refined))
for direction in ['P','T']:
    same=[r for r in saved if r['direction']==direction and math.isclose(float(r['d_over_h']),1)]
    required={round(float(r['required_F_for_exact_discrete_K']),8) for r in same}
    check(direction+' same d/h does not give exact factor collapse in discrete sample',len(same)==3 and len(required)==3)
check('new fitting results explicitly unverified',summary['new_fits_verified'] is False)
cv=summary['reported_cv_arithmetic_only']
check('19 two-direction geometry folds imply 38 records',cv['19_geometry_folds_implies_direction_records']==38)
check('reported CV mean reduction arithmetic only',math.isclose(cv['MAE_relative_reduction_percent'],23.703703703703706))
check('reported CV worst change arithmetic only',math.isclose(cv['worst_absolute_change_percentage_points'],.58,abs_tol=1e-10))
result=dict(checks_passed=sum(c['passed'] for c in checks),checks_failed=sum(not c['passed'] for c in checks),checks=checks,
    scope='Published fixed formula, saved scalar facts and file identity only; no refitting or cross-validation reproduction',
    new_refits_verified=False,CV_reproduced=False,formal_manuscripts_modified=False,new_run_id=None,submission_ready=False)
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(passed=result['checks_passed'],failed=[c for c in checks if not c['passed']]),ensure_ascii=False))
assert result['checks_failed']==0
