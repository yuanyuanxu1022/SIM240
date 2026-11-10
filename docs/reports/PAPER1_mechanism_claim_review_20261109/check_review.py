"""Audit saved diagnostic products and candidate numeric parity; no raw fields/solver."""
from pathlib import Path
import csv, hashlib, json, re, math
from collections import defaultdict

OUT=Path(__file__).resolve().parent
OLD=OUT.parent/'PAPER1_mechanism_offline_20261109'
def read(n):
    with (OLD/n).open() as f:return list(csv.DictReader(f))
def write(n,x):
    (OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

p=read('positive_excess_diagnostic.csv')
targets=[r for r in p if math.isclose(float(r['d_nm']),120,rel_tol=1e-12)]
groups=defaultdict(list)
for r in targets:groups[(r['run_id'],r['scheme'])].append(r)
checks=[]
def check(name,condition):
    checks.append({'check':name,'passed':bool(condition)})
    assert condition,name
check('target_group_count',len(groups)==20)
residual=[];shares={};key=[]
for (run,scheme),rr in groups.items():
    S=sum(float(r['R_excess_term_over_R_LC']) for r in rr)
    E=float(rr[0]['drive_excess_over_R_LC'])
    check(run+scheme+'_nonnegative',all(float(r['R_excess_term_over_R_LC'])>=0 for r in rr))
    check(run+scheme+'_sum',abs(S-float(rr[0]['sum_terms_over_R_LC']))<1e-13)
    frac={r['term']:float(r['R_excess_term_over_R_LC'])/S for r in rr}
    check(run+scheme+'_fraction',all(abs(frac[r['term']]-float(r['term_fraction_of_positive_sum']))<1e-13 for r in rr))
    shares[(run,scheme)]=frac
    if scheme=='wall_quadratic':
        row={'run_id':run,'direction':rr[0]['direction'],'w_nm':float(rr[0]['w_nm']),
             'dx_nm':float(rr[0]['dx_nm']),'E':E,'S':S,'residual_percent':100*(S-E)/E,
             'term_over_R_LC':{r['term']:float(r['R_excess_term_over_R_LC']) for r in rr},
             'share_percent':{k:100*v for k,v in frac.items()}}
        residual.append(row)
        if row['dx_nm']==2.5:key.append(row)
max_scheme=max(100*abs(f-shares[(run,'odd_extension')][term])
               for (run,scheme),ss in shares.items() if scheme=='wall_quadratic' for term,f in ss.items())
max_res={str(dx):max(abs(r['residual_percent']) for r in residual if r['dx_nm']==dx) for dx in [5,2.5,1.25]}
power=read('power_checks.csv')
main=[r for r in power if math.isclose(float(r['d_nm']),120,rel_tol=1e-12) and r['scheme']=='wall_quadratic']
range_power=[min(float(r['strain_input_residual_percent']) for r in main),max(float(r['strain_input_residual_percent']) for r in main)]
summary=json.loads((OLD/'summary.json').read_text())
check('scheme_difference_matches_saved_summary',abs(max_scheme-summary['positive_term_fraction_max_scheme_difference_pp'])<1e-10)
for got,want in zip(range_power,summary['power_main_target_residual_range_percent']):check('power_range_matches',abs(got-want)<1e-12)
cn=(OUT/'CANDIDATE_CN.md').read_text();en=(OUT/'CANDIDATE_EN.md').read_text()
for r in key:
    for value in r['share_percent'].values():
        number=f'{value:.1f}'
        check('bilingual_share_'+r['direction']+str(r['w_nm'])+number,number+'%' in cn and number+'%' in en)
for number in [f'{max_res["5"]:.2f}',f'{max_res["2.5"]:.2f}',f'{max_scheme:.2f}','1.775','0.532']:
    check('bilingual_key_number_'+number,number in cn and number in en)
for r in key:
    if r['direction']=='P':
        check('along_absolute_component_'+str(r['w_nm']),f'{r["term_over_R_LC"]["transverse_gradient"]:.3f}' in cn)
write('review_numbers.json',{'source':'saved CSV only','common_grid_rows':key,
      'positive_sum_max_abs_residual_percent_by_dx_nm':max_res,
      'max_scheme_share_difference_pp':max_scheme,'strain_power_residual_percent_range':range_power})
for file in OUT.glob('*.md'):
    for target in re.findall(r'\]\(([^)]+)\)',file.read_text()):
        if target == 'verification.json':
            continue  # This script writes the receipt below; checked after writing.
        if not target.startswith(('http:','https:')):check('local_link_'+file.name+target,(file.parent/target).resolve().exists())
protected=json.loads((OUT/'protected_inputs.json').read_text())
drift=[p for p,h in protected.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
check('protected_inputs_unchanged',not drift)
write('verification.json',{'checks':checks,'check_count':len(checks),'all_passed':all(c['passed'] for c in checks),
      'protected_file_count':len(protected),'changed_inputs':drift,'raw_fields_read':False,'solver_calls':0,
      'new_run_id':None,'formal_manuscripts_modified':False,'reference_qualified':False,
      'strict_error_bound_established':False,'submission_ready':False,
      'scope':'saved arithmetic and textual consistency, not independent physical validation or author approval'})
assert (OUT/'verification.json').is_file()
print(json.dumps({'checks':len(checks),'all_passed':True,'protected_files':len(protected),'max_residuals':max_res,'max_scheme_pp':max_scheme}))
