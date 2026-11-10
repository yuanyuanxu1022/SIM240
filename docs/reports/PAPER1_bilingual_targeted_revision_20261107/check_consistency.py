"""Read-only checks of revised manuscripts against bound, previously audited evidence."""
from pathlib import Path
import csv
import difflib
import hashlib
import json
import math
import re

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
SUP=ROOT/'SIM240_Supplementary_Methods_20261024'
paths=[ROOT/'SIM240_中文稿_导师审阅版_20261022.md', ROOT/'SIM240_First_Paper_English_20261028.md', SUP/'SUPPLEMENTARY_METHODS.md', SUP/'SUPPLEMENTARY_METHODS_EN_20261028.md']
texts=[p.read_text() for p in paths]
old=[(OUT/('before_'+p.name)).read_text() for p in paths]
checks=[]
def check(name,value,detail=None):
    checks.append({'check':name,'pass':bool(value),'detail':detail})

bound=json.loads((OUT/'protected_inputs.json').read_text())
changed=[x['path'] for x in bound if hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()!=x['sha256']]
check('bound_evidence_and_legacy_CSV_unchanged',not changed,changed)

def equations(text):
    ans={}
    for block in re.findall(r'\$\$(.*?)\$\$',text,re.S):
        tag=re.search(r'\\tag\{([^}]+)\}',block)
        if tag:
            assert tag[1] not in ans,tag[1]
            ans[tag[1]]=re.sub(r'\s+','',block)
    return ans
eq=[equations(s) for s in texts[:2]]
for i in range(2):
    check(f'main_{i}_equation_labels',set(eq[i])=={str(x) for x in range(1,9)}|{'E'+str(x) for x in range(1,7)})
    baseline=equations(old[i])
    check(f'main_{i}_existing_numbered_equations_preserved',all(eq[i][k]==v for k,v in baseline.items()))
check('new_English_interface_equation_matches_Chinese',eq[0]['8']==eq[1]['8'])
for i in range(2):
    key='## 附录 E' if i==0 else '## Appendix E.'
    def proof(s):
        part=s[s.index(key):]
        return part.split('## References')[0] if i else part
    check(f'main_{i}_theoretical_appendix_verbatim',proof(texts[i])==proof(old[i]))

stats=list(csv.DictReader((ROOT/'PAPER1_claim_final_review_20261105/recomputed_direction_stats.csv').open()))
check('main_record_count',sum(int(x['n']) for x in stats)==36)
check('improvement_count',sum(int(x['improved']) for x in stats)==35)
expected={'Kxx':('30.63','4.42','54.19','18.71'),'Kyy':('88.85','6.40','204.85','10.50')}
for row in stats:
    vals=tuple(f"{float(row[k]):.2f}" for k in ['LC_MAE','V2_MAE','LC_max','V2_max_abs'])
    check('audited_stats_'+row['component'],vals==expected[row['component']],vals)
    for i,t in enumerate(texts[:2]):check(f'stats_present_main_{i}_'+row['component'],all(v+'%' in t for v in vals))

new=list(csv.DictReader((SUP/'Table_S6_added_gap_build_comparison.csv').open()))
check('S6_exact_audited_copy',(SUP/'Table_S6_added_gap_build_comparison.csv').read_bytes()==(ROOT/'PAPER1_new_four_cases_acceptance_20261107/comparison.csv').read_bytes())
check('S6_roles_and_counts',len(new)==6 and sum(x['role']=='four_new' for x in new)==4)
h100={x['component']:x for x in new if float(x['h_nm'])==100}
for comp,row in h100.items():
    h,d,w=(float(row[x])*1e-9 for x in ['h_nm','d_nm','w_nm'])
    lc=((h+d)**3+h**3)/24 if comp=='Kyy' else h**3*(h+d)**3/(6*(h**3+(h+d)**3))
    c,b=(1.7685,1.6331) if comp=='Kyy' else (0.4900,0.6990)
    v2=lc/(1+c*(d/w)**b)
    kval=float(row['K_LB_m3'])
    check('h100_formula_recompute_'+comp,math.isclose(lc,float(row['K_LC_m3']),rel_tol=2e-14) and math.isclose(v2,float(row['K_V2_m3']),rel_tol=2e-14))
    check('h100_bias_recompute_'+comp,math.isclose(100*(v2/kval-1),float(row['V2_bias_percent']),abs_tol=1e-11))
a_lb=float(h100['Kyy']['K_LB_m3'])/float(h100['Kxx']['K_LB_m3'])
a_v2=float(h100['Kyy']['K_V2_m3'])/float(h100['Kxx']['K_V2_m3'])
check('h100_A_negative_6p15',f'{100*(a_v2/a_lb-1):.2f}'=='-6.15')
thin=list(csv.DictReader((SUP/'Table_S7_thin_gap_correction.csv').open()))
check('thin_grid_improvement_reversal',len(thin)==2 and abs(float(thin[0]['V2_bias_percent']))>abs(float(thin[0]['LC_bias_percent'])) and abs(float(thin[1]['V2_bias_percent']))<abs(float(thin[1]['LC_bias_percent'])))

for i,t in enumerate(texts):
    check(f'S4_disclosure_{i}','1.328387035%' in t and 'FAIL' in t)
    check(f'h100_ratio_disclosure_{i}','−6.15%' in t)
    check(f'private_snapshot_{i}','e05b3f21171ce52a66af41dfe172e79c0a099c20' in t)
    check(f'math_fences_{i}',t.count('$$')%2==0)
    check(f'code_fences_{i}',t.count('```')%2==0)
    check(f'no_stale_absolute_V2_gap_claim_{i}',not any(x in t for x in ['V2 depends only on','V2 does not explicitly include gap','最高约三倍的误差','薄隙跨槽不可靠','此前缺乏双向']))
for i,t in enumerate(texts[:2]):
    sections=re.findall(r'^### (\d+\.\d+)\s',t,re.M)
    check(f'unique_subsections_{i}',len(sections)==len(set(sections)),sections)
    check(f'static_and_applicability_sections_{i}','5.3' in sections and '5.4' in sections)
    refs=re.findall(r'^\[(\d+)\] ',t,re.M)
    check(f'reference_inventory_{i}',refs==[str(x) for x in range(1,12)],refs)
    key='## 参考文献' if i==0 else '## References'
    def bibliography(s):
        part=s[s.index(key):]
        return part.split('## 附录 A')[0].strip() if i==0 else part.strip()
    check(f'bibliography_preserved_{i}',bibliography(t)==bibliography(old[i]))

def table_rows(text,n,english):
    pattern=(r'\*\*Table '+str(n)+r'\.' if english else r'\*\*表\s*'+str(n)+r'\s')
    m=re.search(pattern,text)
    assert m,(n,english)
    tail=text[m.end():]
    block=re.search(r'(?m)^\|.*(?:\n\|.*)*',tail)[0]
    return block.splitlines()[2:]
for n in range(1,9):
    def numeric_rows(rows):
        return [re.findall(r'[+−-]?\d+(?:\.\d+)?',row) for row in rows]
    # Table 3 uses equivalent typesetting of scientific notation; compare the full token list.
    rows_c=numeric_rows(table_rows(texts[0],n,False))
    rows_e=numeric_rows(table_rows(texts[1],n,True))
    check(f'matched_numeric_table_{n}',rows_c==rows_e,{'Chinese':rows_c,'English':rows_e} if rows_c!=rows_e else None)
for i,t in enumerate(texts[2:]):
    check(f'supplement_anchors_{i}',all(f'id="sm-s{x}"' in t for x in range(1,14)))
    check(f'supplement_table_anchors_{i}',all(f'id="table-s{x}"' in t for x in range(1,9)))

def links(text):
    return set(re.findall(r'!?\[[^\]]*\]\(([^\s)]+)\)',text))
def valid_local(path,target):
    if target.startswith(('https://','http://','mailto:')):return True
    target,_,fragment=target.partition('#')
    target=re.sub(r':\d+$','',target)
    dest=path if not target else ((path.parent/target).resolve() if not target.startswith('/') else Path(target))
    if not dest.exists():return False
    if fragment and dest.suffix=='.md':
        s=dest.read_text()
        if 'id="'+fragment+'"' not in s:
            # New manuscript links use explicit anchors; existing heading links are recorded separately.
            return False
    return True
legacy_missing=[]
for p,t,b in zip(paths,texts,old):
    bad_new=[x for x in links(t)-links(b) if not valid_local(p,x)]
    check('new_local_links_'+p.name,not bad_new,bad_new)
    legacy_missing += [{'file':p.name,'target':x} for x in links(t)&links(b) if not valid_local(p,x)]
check('history_preserved_exactly',(OUT/'INTERNAL_REVISION_HISTORY_THROUGH_20261107.md').read_text()==old[0][old[0].index('## 附录 D　'):old[0].index('## 附录 E')])
for p,b,t in zip(paths,old,texts):
    (OUT/(p.name+'.diff')).write_text(''.join(difflib.unified_diff(b.splitlines(True),t.splitlines(True),fromfile='before/'+p.name,tofile='after/'+p.name)))
result={'checks':checks,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'legacy_link_issues':legacy_missing,'scope':'document consistency and selected arithmetic against previously audited sources; not solver/reference requalification','new_solver_runs':0,'new_fits':0,'submission_ready':False}
(OUT/'consistency_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['passed','failed','legacy_link_issues']},ensure_ascii=False))
if result['failed']:raise SystemExit(1)
