"""Validate evidence receipt and narrow document delta; no numerical backend."""
from pathlib import Path
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
checks={}
def check(name,value): checks[name]=bool(value)
items=json.loads((OUT/'intake.json').read_text())
check('three_received_PDFs_parse',len(items)==3 and all(r['pdfinfo_exit']==0 and r['text_exit']==0 for r in items))
expected={'P9':6,'P10':4,'NEW_THIRD':35}
check('expected_page_counts',all(int(re.search(r'Pages:\s+(\d+)',r['pdfinfo']).group(1))==expected[r['id']] for r in items))
protected=json.loads((OUT/'protected_inputs.json').read_text())
check('all_selected_protected_files_unchanged',all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items()))
check('PDF_source_headers',all(Path(r['path']).read_bytes().startswith(b'%PDF-') for r in items))
check('extra_is_exact_existing_copy',next(r for r in items if r['id']=='NEW_THIRD')['sha256']==hashlib.sha256(Path('/home/dell/下载/effective-permeability-tensor-of-confined-flows-with-wall-grooves-of-arbitrary-shape.pdf').read_bytes()).hexdigest())
for key,doi,marker,n in [('P9','10.1103/PhysRevE.65.046308','046308-',6),('P10','10.1115/1.2960953','078001-',4)]:
    pages=[t for t in (OUT/'evidence'/f'{key}.txt').read_text().split('\f') if t.strip()]
    check(key+'_continuous_journal_pages',len(pages)==n and all(marker+str(i) in t for i,t in enumerate(pages,1)))
    check(key+'_DOI_present',doi in pages[0])
check('ten_reviewed_previews_exist',len(list((OUT/'evidence').glob('*page*.png')))==10)
cross=json.loads((OUT/'crossref_identity.json').read_text())
check('three_bounded_crossref_records',len(cross)==3 and all('error' not in r and r['title'] for r in cross))
receipt=json.loads((OUT/'contract_receipt.json').read_text())
check('scoped_receipt_P9_P10_checked_P8_open',receipt['P9']['specified_contents_checked'] and receipt['P10']['specified_contents_checked'] and not receipt['P8']['received'])
check('four_build_groups_still_open',len(receipt['historical_build_groups'])==4 and set(receipt['historical_build_groups'].values())=={'OPEN'})
main=ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
sup=ROOT/'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md'
mt=main.read_text();st=sup.read_text()
beforemt=(OUT/'before'/main.name).read_text();beforest=(OUT/'before'/sup.name).read_text()
old='[6]书目信息已核；[8]、[9]全文公式及[10]期刊发表版的完整核对仍有缺口，范围见补充材料S11'
new='[6]全文适用条件及[8]边界原文公式对应仍缺；[9]指定力项/速度与当前实现对应、[10]发表版指定步骤/公式及附录版本对应已核，范围与剩余限制见补充材料S11'
check('main_only_reference_checklist_changed',mt.replace(new,old,1)==beforemt)
check('supplement_before_S11_including_GCI_table_unchanged',st.split('<a id="sm-s11"></a>')[0]==beforest.split('<a id="sm-s11"></a>')[0])
def remove_status_lines(t):
    return '\n'.join(line for line in t.splitlines() if not line.startswith(('- **[5] Dewangan','- **[9] Guo','- **[10] GCI')))
check('supplement_only_three_source_status_lines_changed',remove_status_lines(st)==remove_status_lines(beforest))
check('source_version_inconsistency_disclosed',all(t in st for t in ['式（4）外推量上标为21','式（6）内部仍写12','不证明迭代误差已获充分控制']))
check('states_point_to_current_receipt',all('Primary_text_received_20261027/REPORT.md' in (ROOT/'docs/reports'/n).read_text().split('\n## ',2)[1] for n in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']))
links=[]
for path in [main,sup,OUT/'REPORT.md']:
    for link in re.findall(r'\]\(([^)]+)\)',path.read_text()):
        if link.startswith(('https:','http:')):continue
        raw,_,anchor=link.partition('#');raw=re.sub(r':\d+$','',raw)
        p=(path.parent/raw).resolve() if raw else path
        if raw.startswith('/'):p=Path(raw)
        ok=p.exists() and (not anchor or f'id="{anchor}"' in p.read_text())
        links.append(dict(source=str(path.relative_to(ROOT)),target=link,exists=ok))
check('document_local_links_resolve',all(r['exists'] for r in links))
result=dict(checks=checks,all_pass=all(checks.values()),protected_count=len(protected),local_links_checked=len(links),broken_links=[r for r in links if not r['exists']],solver_started=False,strict_bound_adjudicated=False)
(OUT/'verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(result,indent=2,ensure_ascii=False))
raise SystemExit(0 if result['all_pass'] else 1)
