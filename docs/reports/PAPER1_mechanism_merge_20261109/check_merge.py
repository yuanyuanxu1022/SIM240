"""Check actual manuscript integration, numbering, links and saved evidence bindings."""
from pathlib import Path
import csv, hashlib, json, math, re
from collections import Counter
from urllib.parse import unquote

OUT=Path(__file__).resolve().parent
REP=OUT.parent;SUP=REP/'SIM240_Supplementary_Methods_20261024';OLD=REP/'PAPER1_mechanism_offline_20261109'
names=['SIM240_中文稿_导师审阅版_20261022.md','SIM240_First_Paper_English_20261028.md',
       'SUPPLEMENTARY_METHODS.md','SUPPLEMENTARY_METHODS_EN_20261028.md']
paths=[REP/names[0],REP/names[1],SUP/names[2],SUP/names[3]]
before=[(OUT/(n+'.before')).read_text() for n in names]
after=[p.read_text() for p in paths];checks=[]
def check(label,ok,detail=None):
    c={'check':label,'passed':bool(ok)}
    if detail is not None:c['detail']=detail
    checks.append(c)
def section(t,start,end=None):
    a=t.index(start);b=t.index(end,a) if end else len(t);return t[a:b]
def read(path):
    with path.open() as f:return list(csv.DictReader(f))
def dump(n,x):(OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

# Check the changed prose by reversing logged substitutions against actual
# pre-merge snapshots. This protects unrelated concurrent/prior manuscript edits.
edits=json.loads((OUT/'edits.json').read_text())
for i,(a,b) in enumerate(zip(after[:2],before[:2])):
    prefix='CN' if i==0 else 'EN';t=a
    own=[e for e in edits if e['label'].startswith(prefix+' ') and ' supplement ' not in e['label']]
    for e in reversed(own):
        check(prefix+' reverse edit unique: '+e['label'],t.count(e['new'])==1)
        t=t.replace(e['new'],e['old'],1)
    check(prefix+' all other manuscript text preserved',t==b)
    check(prefix+' chapter 3 unchanged',section(a,'## 3 ','## 4 ')==section(b,'## 3 ','## 4 '))
    check(prefix+' chapter 4 unchanged',section(a,'## 4 ','## 5 ')==section(b,'## 4 ','## 5 '))
    check(prefix+' Appendix E unchanged',section(a,'## 附录 E' if i==0 else '## Appendix E')==section(b,'## 附录 E' if i==0 else '## Appendix E')) if i==0 else check(prefix+' Appendix E unchanged',section(a,'## Appendix E','## References')==section(b,'## Appendix E','## References'))
    tags_before=re.findall(r'\\tag\{([^}]+)\}',b);tags_after=re.findall(r'\\tag\{([^}]+)\}',a)
    check(prefix+' existing equation tags retained',tags_after==tags_before)
    numbered=lambda text:[v for v in re.findall(r'\$\$(.*?)\$\$',text,re.S) if r'\tag{' in v]
    check(prefix+' existing numbered formula content retained',numbered(a)==numbered(b))
    refs_before=re.findall(r'^\[\d+\].*$',b,re.M);refs_after=re.findall(r'^\[\d+\].*$',a,re.M)
    check(prefix+' reference entries unchanged',refs_after==refs_before)
    check(prefix+' bibliography 1 to 11',list(map(int,re.findall(r'^\[(\d+)\]',a,re.M)))==list(range(1,12)))
    check(prefix+' main chapter numbering retained',re.findall(r'^## ([1-6]) ',a,re.M)==list('123456'))
    check(prefix+' five conclusion items',len(re.findall(r'^\*\*(?:[一二三四五]、|[1-5]\.)\*\*',section(a,'## 6 '),re.M))==5)
    check(prefix+' false blanket absence removed',all(s not in a for s in ['本文未作该分解','本文未分解这些因素对整体输运的贡献','which has not been performed','Their respective contributions to overall transport have not been separated.']))
    check(prefix+' local causal limit retained',('未独立分解侧壁剪切与台阶附近流动重分布' in a) if i==0 else ('Sidewall-shear and step-redistribution contributions have not been separated' in a))
    check(prefix+' original S4 FAIL retained','1.328387035%' in a and 'FAIL' in a)
    check(prefix+' fixed coefficients preserved','1.7685' in a and '1.6331' in a and '0.4900' in a and '0.6990' in a)
    check(prefix+' no provisional mechanism labels',all(s not in a for s in ['机制补充候选','mechanism supplement candidate','(M1)','(M2)']))
    check(prefix+' primary-only geometry qualifier',('主参数图的周期' in a) if i==0 else ('The main parameter map uses period' in a))
    check(prefix+' restricted geometry diagnostic',all(s in a for s in ['$h=75$ nm','$d=120$ nm','$w=60$']))

for i in [2,3]:
    a,b=after[i],before[i];prefix='CN' if i==2 else 'EN'
    check(prefix+' S1 to S13 sections unchanged',section(a,'<a id="sm-s1"></a>','<a id="sm-s14"></a>').rstrip()==section(b,'<a id="sm-s1"></a>').rstrip())
    check(prefix+' supplement section numbering',list(map(int,re.findall(r'^## S(\d+) ',a,re.M)))==list(range(1,15)))
    check(prefix+' S14 equations unique',re.findall(r'\\tag\{([^}]+)\}',a)==['S14.1','S14.2'])
    check(prefix+' derivative-square notation',r'\partial_z b^2' not in a and r'\partial_z c^2' not in a and r'(\partial_z b)^2' in a and r'(\partial_z c)^2' in a)
    check(prefix+' new definitions avoid V and U collision',r'\boldsymbol v=\boldsymbol u/J' in a and r'v=u_y/J' in a and r's=u_z/J' in a)
    check(prefix+' incompressibility group constraint',r'\partial_xv=-\partial_zs' in a)
    check(prefix+' share and residual denominators retained','100s_j/S%' in a and '100(S−E)/E%' in a)
    check(prefix+' residual figures retained',all(s in a for s in ['−0.5803%','+0.00259%','1.5555%','0.5336%','0.4252']))
    check(prefix+' full spatial radii retained','1/8' in a and '1/4' in a and '1/2' in a)
    check(prefix+' S14 and S9 anchors unique',a.count('id="sm-s14"')==1 and a.count('id="table-s9"')==1)
    check(prefix+' delimiters balanced',a.count(r'\[')==a.count(r'\]') and a.count('$$')%2==0)

eq=lambda t:[re.sub(r'\s+','',v) for v in re.findall(r'\\\[\n(.*?)\\\]',section(t,'## S14 '),re.S)]
check('S14 CN/EN mathematical displays identical',eq(after[2])==eq(after[3]) and len(eq(after[2]))==3)
mapping=read(SUP/'SUPPLEMENT_NUMBER_MAP.csv')
check('number map now S1 to S14',[r['supplement_section'] for r in mapping]==['S'+str(i) for i in range(1,15)])

# Reconcile the new Table S9 with the original saved diagnostic records.
table=read(SUP/'Table_S9_mechanism_diagnostic.csv');key=read(OLD/'key_results.csv');positive=read(OLD/'positive_excess_diagnostic.csv')
check('Table S9 ten targets',len(table)==10 and {r['run_id'] for r in table}=={r['run_id'] for r in key})
check('Table S9 excludes smooth controls',all(math.isclose(float(r['d_nm']),120,rel_tol=1e-12) for r in table))
for r in table:
    k=next(s for s in key if s['run_id']==r['run_id']);rid=r['run_id']
    check(rid+' geometry and grid',r['direction']==k['direction'] and math.isclose(float(r['w_nm']),float(k['w_nm'])) and float(r['dx_nm'])==float(k['dx_nm']))
    check(rid+' physical period',math.isclose(float(r['P_nm']),2*float(r['w_nm'])))
    for field in ['R_drive_over_R_LC','R_strain_over_R_LC','strain_input_residual_percent','positive_sum_vs_drive_excess_relative_percent']:
        check(rid+' '+field,float(r[field])==float(k[field]))
    pp=[s for s in positive if s['run_id']==rid and s['scheme']=='wall_quadratic']
    S=sum(float(v['R_excess_term_over_R_LC']) for v in pp);E=float(pp[0]['drive_excess_over_R_LC'])
    check(rid+' excess sums',abs(float(r['sum_terms_over_R_LC'])-S)<1e-13 and float(r['drive_excess_over_R_LC'])==E)
    check(rid+' signed excess residual',abs(float(r['positive_sum_vs_drive_excess_relative_percent'])-100*(S-E)/E)<1e-10)
    for term in ['profile_departure','transverse_gradient','axial_gradient','vertical_velocity_gradient']:
        src=[v for v in pp if v['term']==term]
        if src:
            val=float(src[0]['R_excess_term_over_R_LC']);share=100*float(src[0]['term_fraction_of_positive_sum'])
            check(rid+' '+term,float(r[term+'_over_R_LC'])==val and float(r[term+'_share_percent'])==share)
            if float(r['dx_nm'])==2.5:
                num=f'{share:.1f}'+'%';check('CN/EN main share '+rid+term,num in after[0] and num in after[1])
        else:check(rid+' '+term+' is blank',r[term+'_over_R_LC']==r[term+'_share_percent']=='')

for x in ['1.775','0.532','1.56%','0.53%','0.43','139.14%','154.24%']:
    check('CN/EN key number '+x,all(x in a for a in after[:2]))

# Resolve every Markdown file/image link and explicit HTML anchor in all four
# documents. Compare inherited failures separately rather than inventing fixes.
def link_errors(p,t):
    errors=[]
    for dest in re.findall(r'!?\[[^\]\n]*\]\(([^\n)]+)\)',t):
        dest=unquote(dest.strip().strip('<>'))
        if re.match(r'^[a-z]+://',dest):continue
        target,_,anchor=dest.partition('#');target=re.sub(r':\d+$','',target)
        q=(p.parent/target).resolve() if target else p.resolve()
        if not q.exists():errors.append({'link':dest,'reason':'missing path'})
        elif anchor:
            qt=t if q==p.resolve() else q.read_text()
            if ('id="'+anchor+'"') not in qt:errors.append({'link':dest,'reason':'missing explicit anchor'})
    return errors
links=[]
for p,a,b in zip(paths,after,before):
    old=link_errors(p,b);new=link_errors(p,a);links.append({'path':str(p),'before_errors':old,'after_errors':new})
    check(p.name+' all file links and anchors resolve',not new,new)
dump('link_checks.json',links)

protected=json.loads((OUT/'protected_inputs.json').read_text())
drift=[p for p,h in protected.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
check('all bound source products unchanged',not drift,drift)
dump('verification.json',{'all_passed':all(x['passed'] for x in checks),'check_count':len(checks),
     'failed':[x for x in checks if not x['passed']],'checks':checks,'protected_input_count':len(protected),
     'changed_inputs':drift,'new_table_rows':len(table),'manuscripts_modified':4,
     'new_run_id':None,'solver_calls':0,'raw_fields_read':False,'fit_calls':0,'reference_qualified':False,
     'strict_error_bound_established':False,'submission_ready':False,
     'scope':'document, numbering, link and saved-number consistency; no new scientific reference acceptance'})
print(json.dumps({'checks':len(checks),'all_passed':all(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']]},ensure_ascii=False))
raise SystemExit(0 if all(x['passed'] for x in checks) else 1)
