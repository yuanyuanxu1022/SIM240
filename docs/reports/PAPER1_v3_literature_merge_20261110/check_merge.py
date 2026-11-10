"""Check adopted text, reference identity, numbering, links and file bindings."""
from pathlib import Path
from urllib.parse import unquote
import hashlib
import json
import re
import subprocess
import zipfile

OUT = Path(__file__).resolve().parent
REP = OUT.parent
ROOT = REP.parents[1]
SUP = REP / 'SIM240_Supplementary_Methods_20261024'
V3 = REP / 'PAPER1_MF_fulltext_audit_20261110'
CN = REP / 'SIM240_中文稿_导师审阅版_20261022.md'
EN = REP / 'SIM240_First_Paper_English_20261028.md'
SC = SUP / 'SUPPLEMENTARY_METHODS.md'
SE = SUP / 'SUPPLEMENTARY_METHODS_EN_20261028.md'
MAN = REP / 'PAPER1_submission_package_20261109/MANIFEST.md'
DOCS = [CN,EN,SC,SE]
PURE = re.compile(r'\[(\d+(?:\s*[,;–—-]\s*\d+)*)\]')
checks = []


def check(name, ok, detail=None):
    c = dict(check=name,passed=bool(ok))
    if detail is not None:c['detail']=detail
    checks.append(c)


def dump(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def remap(text,mapping):
    return PURE.sub(lambda m:'['+re.sub(r'\d+',lambda n:str(mapping[int(n[0])]),m[1])+']',text)
def bibliography(text):
    return {int(m[1]):m[2].rstrip('.') for m in re.finditer(r'^\[(\d+)\] .+?DOI:\s*(\S+)',text,re.M)}
def expand(cite):
    result=[]
    for part in re.split(r'[,;]',cite):
        numbers=list(map(int,re.findall(r'\d+',part)))
        result.extend(range(numbers[0],numbers[-1]+1) if re.search(r'[–—-]',part) else numbers)
    return result
def identities(text,lookup):
    return PURE.sub(lambda m:'['+','.join(lookup[n] for n in expand(m[1]))+']',text)
def section(text,start,end=None):
    return text.split(start,1)[1].split(end,1)[0] if end else text.split(start,1)[1]


before={p:(OUT/(p.name+'.before')).read_text() for p in DOCS+[MAN]}
after={p:p.read_text() for p in DOCS+[MAN]}
edits=json.loads((OUT/'edits.json').read_text())
concurrent=json.loads((OUT/'concurrent_changes.json').read_text()) if (OUT/'concurrent_changes.json').exists() else None
mapping={int(k):v for k,v in json.loads((OUT/'citation_map.json').read_text())['old_to_new'].items()}
inverse={v:k for k,v in mapping.items()}
old_lookup=bibliography(before[CN]);new_lookup=bibliography(after[CN])
check('original bibliography identities 1-11',list(old_lookup)==list(range(1,12)))
check('current CN bibliography identities 1-14',list(new_lookup)==list(range(1,15)))
check('CN EN bibliographic identity and order match',bibliography(after[EN])==new_lookup)
for old,new in mapping.items():
    check(f'old reference {old} now {new} same DOI',old_lookup[old]==new_lookup[new])
expected={7:'10.1088/1873-7005/aa5b58',8:'10.1017/jfm.2013.184',9:'10.1021/ac0257389'}
metadata_names={7:'Ng2017_crossref.json',8:'Mohammadi2013_crossref.json',9:'Stroock2002_crossref.json'}
for n,doi in expected.items():
    check('new reference '+str(n)+' DOI identity',new_lookup[n]==doi)
    data=json.loads((REP/'PAPER1_nearest_work_comparison_20261109/sources'/metadata_names[n]).read_text())['message']
    for p in [CN,EN]:
        line=next(s for s in after[p].splitlines() if s.startswith('['+str(n)+'] '))
        check(p.name+f' new reference {n} verified title/year/page',data['title'][0].lower() in line.lower() and
              str(data['published']['date-parts'][0][0]) in line and data['page'].replace('-','–') in line)

# Remove only logged literal insertions/edits; the remaining citation-only text
# must retain the exact old DOI sequence and wording, independently of its number.
for p in DOCS+[MAN]:
    restored=after[p]
    if p==MAN and concurrent:
        own=(OUT/concurrent['manifest']['own_completed_snapshot']).read_text()
        observed=(OUT/concurrent['manifest']['observed_snapshot']).read_text()
        check('concurrent MANIFEST update preserved exactly',after[p]==observed)
        check('own MANIFEST completion snapshot bound',sha(OUT/concurrent['manifest']['own_completed_snapshot'])==concurrent['manifest']['own_completed_sha256'])
        own_row=next(s for s in own.splitlines() if s.startswith('| 5 |'))
        current_row=next(s for s in observed.splitlines() if s.startswith('| 5 |'))
        addition=next(s for s in observed.splitlines() if s.startswith('**1.1.3 结论定稿文件'))
        stripped=observed.replace(current_row,own_row,1).replace('\n\n'+addition,'',1)
        check('concurrent MANIFEST scope is row5 plus mapping note only',stripped==own)
        restored=own
    own=[e for e in edits if e['path']==str(p.relative_to(ROOT))]
    for e in reversed(own):
        if e['kind']=='literal':
            check(p.name+' uniquely reversible '+e['label'],restored.count(e['new'])==1)
            restored=restored.replace(e['new'],e['old'],1)
    if p in DOCS:
        check(p.name+' every retained citation preserves DOI and surrounding text',
              identities(restored,new_lookup)==identities(before[p],old_lookup))
        restored=remap(restored,inverse)
    check(p.name+' reverses exactly to actual baseline',restored==before[p])

blocks=json.loads((OUT/'adopted_blocks.json').read_text())
for label,p in [('CN',CN),('EN',EN)]:
    t=after[p];old=before[p]
    for part in ['intro','height']:
        check(label+' adopted '+part+' present once',t.count(blocks[label+'_'+part])==1)
    original_candidate=(V3/('CANDIDATE_'+label+'_v3.md')).read_text()
    intro_head='## §1.2候选：现有第二段后插入' if label=='CN' else '## Section 1.2: insert after the existing second paragraph'
    height_head='## §2.2候选：现有H_ref与κ关系后的定义澄清' if label=='CN' else '## Section 2.2: clarify the existing H_ref and κ relation'
    for part,heading in [('intro',intro_head),('height',height_head)]:
        adopted=original_candidate.split(heading,1)[1].split('\n## ',1)[0].strip()
        for key,n in [('Ng',7),('MF',8),('St',9)]:adopted=adopted.replace('['+key+']','['+str(n)+']')
        check(label+' '+part+' equals reviewed v3 except citation keys',adopted==blocks[label+'_'+part])
    check(label+' no unresolved citation keys',not re.search(r'\[(Ng|MF|St)\]',t))
    check(label+' original equation tags unchanged',re.findall(r'\\tag\{([^}]+)\}',t)==re.findall(r'\\tag\{([^}]+)\}',old))
    check(label+' all displayed equations unchanged',re.findall(r'\$\$\n(.*?)\n\$\$',t,re.S)==re.findall(r'\$\$\n(.*?)\n\$\$',old,re.S))
    check(label+' abstract unchanged',section(t,'## 摘要' if label=='CN' else '## Abstract','## 1 ')==section(old,'## 摘要' if label=='CN' else '## Abstract','## 1 '))
    for chapter in [3,4,5]:
        check(label+f' chapter {chapter} unchanged except reference numbers',
              identities(section(t,f'## {chapter} ',f'## {chapter+1} '),new_lookup)==identities(section(old,f'## {chapter} ',f'## {chapter+1} '),old_lookup))
    end='## 参考文献' if label=='CN' else '## Data,'
    check(label+' five conclusions unchanged except any citation numbers',identities(section(t,'## 6 ',end),new_lookup)==identities(section(old,'## 6 ',end),old_lookup))
    appendix='## 附录 E' if label=='CN' else '## Appendix E'
    check(label+' full Appendix E unchanged',section(t,appendix,'\n## References' if label=='EN' else None)==section(old,appendix,'\n## References' if label=='EN' else None))
    body=t.split('## 参考文献' if label=='CN' else '## References',1)[0]
    first=[]
    for match in PURE.finditer(body):
        for n in expand(match[1]):
            if n not in first:first.append(n)
    check(label+' bibliography follows actual first appearance 1-14',first==list(range(1,15)),first)
    check(label+' no unsupported amplitude exclusion in adopted intro','0.06' not in blocks[label+'_intro'] and '6—44' not in blocks[label+'_intro'])
    check(label+' Href volume normalization adopted',r'H_{\rm ref}=V_f/A_{\rm plan}=h+d/2' in t)

for label,p in [('CN',SC),('EN',SE)]:
    t=after[p];s11=section(t,'## S11 ','<a id="sm-s12">')
    check(label+' supplementary sections remain S1-S14',list(map(int,re.findall(r'^## S(\d+) ',t,re.M)))==list(range(1,15)))
    check(label+' supplementary equation tags unchanged',re.findall(r'\\tag\{([^}]+)\}',t)==re.findall(r'\\tag\{([^}]+)\}',before[p]))
    check(label+' MF full-text scope and counterexample recorded',all(x in s11 for x in ['10.1017/jfm.2013.184','0.08','0.06','4.4.2']))
    check(label+' source-version and Stroock access scope recorded',all(x in s11 for x in ['10.1088/1873-7005/aa5b58','10.1021/ac0257389','5307']))
    check(label+' S11 references ordered 4-13',list(map(int,re.findall(r'^- \*\*\[(\d+)\]',s11,re.M)))==list(range(4,14)))
    for other in ['S10','S12','S13','S14']:
        if other=='S14': old_section=section(before[p],'## '+other+' ');new_section=section(t,'## '+other+' ')
        else:
            following='## S'+str(int(other[1:])+1)+' '
            old_section=section(before[p],'## '+other+' ',following);new_section=section(t,'## '+other+' ',following)
        check(label+' '+other+' unchanged except citation numbers',identities(old_section,old_lookup)==identities(new_section,new_lookup))

protected=json.loads((OUT/'protected_inputs.json').read_text())
for name,digest in protected.items():
    if concurrent and name==concurrent['independent_conclusions']['path']:
        c=concurrent['independent_conclusions']
        check('concurrent conclusion baseline binding retained',digest==c['baseline_sha256'])
        check('concurrent conclusion update preserved without overwrite',sha(ROOT/name)==c['observed_sha256'])
        prior=(OUT/'conclusions.concurrent_before.md').read_text()
        now=(ROOT/name).read_text()
        check('concurrent conclusion content outside mapping 3.1 unchanged',
              prior.split('### 3.1 ',1)[0]==now.split('### 3.1 ',1)[0] and
              prior.split('### 3.1 ',1)[1].split('\n## 4 ',1)[1]==now.split('### 3.1 ',1)[1].split('\n## 4 ',1)[1])
    else:check('protected '+name,sha(ROOT/name)==digest)

# All numerical bracket references in the four current documents resolve;
# bracketed algebra is deliberately outside the citation grammar.
for p in DOCS:
    referenced=[n for m in PURE.finditer(after[p]) for n in expand(m[1])]
    check(p.name+' every numerical citation resolves',set(referenced)<=set(new_lookup))
    check(p.name+' math delimiters balanced',after[p].count('$$')%2==0 and after[p].count(r'\[')==after[p].count(r'\]'))

link_receipt=[]
for p in DOCS:
    issues=[];count=0
    for dest in re.findall(r'!?\[[^\]\n]*\]\(([^\n)]+)\)',after[p]):
        dest=unquote(dest.strip().strip('<>'))
        if re.match(r'^[a-z]+://',dest):continue
        count+=1
        target,_,anchor=dest.partition('#');target=re.sub(r':\d+$','',target)
        q=(p.parent/target).resolve() if target else p.resolve()
        if not q.exists():issues.append(dict(link=dest,reason='missing file'))
        elif anchor and not re.search(r'id=[\"\x27]'+re.escape(anchor)+r'[\"\x27]',q.read_text()):issues.append(dict(link=dest,reason='missing explicit anchor'))
    check(p.name+' all local file and explicit-anchor links resolve',not issues,issues)
    link_receipt.append(dict(path=str(p.relative_to(ROOT)),local_links=count,issues=issues))
dump('link_checks.json',link_receipt)

manifest_rows=[]
for line in after[MAN].splitlines():
    cells=[c.strip() for c in line.split('|')]
    if len(cells)>4 and cells[1].isdigit():
        path=ROOT/cells[2].strip('`');row=int(cells[1]);hi,si=(5,6) if row<=5 else (3,4)
        check('MANIFEST hash row '+str(row),sha(path)[:16]==cells[hi].strip('`'))
        check('MANIFEST bytes row '+str(row),path.stat().st_size==int(cells[si]))
        if row<=4:check('MANIFEST current content date row '+str(row),'2026-11-10' in cells[4])
        manifest_rows.append(dict(row=row,path=str(path.relative_to(ROOT)),sha256=sha(path),bytes=path.stat().st_size))
check('eight numbered MANIFEST rows checked',len(manifest_rows)==8)
dump('manifest_rows_verified.json',manifest_rows)
for name,digest in json.loads((OUT/'output_hashes.json').read_text()).items():check('output SHA '+name,sha(ROOT/name)==digest)

# Active companion deliverables have no numerical citation references to remap.
conclusion=(REP/'PAPER1_conclusions_current_20261109.md').read_text()
check('independent conclusions contain no numerical citations',PURE.search(conclusion) is None)
with zipfile.ZipFile(REP/'PPT_论文汇报_20261109/论文汇报.pptx') as z:
    texts=' '.join(z.read(n).decode() for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n))
check('PPT contains no numerical bracket citations',PURE.search(texts) is None)

for p in DOCS+[MAN]:
    result=subprocess.run(['git','diff','--no-index','--check',str(OUT/(p.name+'.before')),str(p)],capture_output=True,text=True)
    check(p.name+' diff has no whitespace errors',result.returncode in (0,1) and not result.stdout and not result.stderr)

result=dict(checks_passed=sum(c['passed'] for c in checks),checks_failed=sum(not c['passed'] for c in checks),checks=checks,
    scope='Text adoption, bibliography identity, numbering, links and hashes; not theoretical or numerical revalidation',
    historical_records_renumbered=False,new_run_id=None,submission_ready=False,human_final_scientific_signoff='not asserted')
dump('verification.json',result)
print(json.dumps(dict(passed=result['checks_passed'],failed=[c for c in checks if not c['passed']]),ensure_ascii=False))
assert result['checks_failed']==0
