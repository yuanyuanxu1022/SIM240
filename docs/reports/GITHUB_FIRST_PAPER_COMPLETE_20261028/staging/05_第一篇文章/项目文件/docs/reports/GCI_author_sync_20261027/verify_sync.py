"""Verify only the adopted document delta and preserved files."""
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SUP = ROOT/'docs/reports/SIM240_Supplementary_Methods_20261024'
REVIEW = ROOT/'docs/reports/GCI_decision_review_20261027'
main = ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
checks = {}
def check(name, value):
    checks[name] = bool(value)

protected = json.loads((OUT/'protected_inputs.json').read_text())
check('protected_inputs_byte_unchanged',all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items()))
check('table_S5_exact_candidate_copy',(SUP/'Table_S5_conditional_gci.csv').read_bytes()==(REVIEW/'candidate_gci_table.csv').read_bytes())
rows = list(csv.DictReader((SUP/'Table_S5_conditional_gci.csv').open()))
check('table_has_six_metrics', len(rows)==6)
check('three_dependent_failure_flags',{r['metric'] for r in rows if r['includes_failed_fine_T']=='True'}=={'K_perpendicular','eta_perpendicular','anisotropy'})
mt = main.read_text(); st = (SUP/'SUPPLEMENTARY_METHODS.md').read_text()
candidate = (REVIEW/'CANDIDATE_TEXT.md').read_text()
table = candidate[candidate.index('| 指标 |'):candidate.index('\n\n定义：')]
check('six_display_rows_exact_candidate', table in st)
paras = [line[2:] for line in candidate.splitlines() if line.startswith('> ')]
check('reviewed_asymptotic_and_smooth_text_exact',all(p in st for p in paras[1:]))
expected = paras[0].replace('补充表[待编定表号]', '[补充材料 S9、表 S5](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#table-s5)').replace('方法参照[10]', '方法参照 [10]')
check('main_adopted_paragraph_exact',expected in mt)
reversed_main=mt.replace(expected,'两级网格不能确定观测阶，也不能给出整个参数范围的误差上界。基准几何另有一套归档的三网格 GCI 分析 [10]，但**不将其细网格估计套用于全部生产网格样点**。',1)
reversed_main=reversed_main.replace('五张补充数据表分别为表 S1—S5；表 S5 补列历史基准的条件性 Richardson/GCI 估计。','四张补充数据表分别为表 S1—S4。',1)
reversed_main=reversed_main.replace('| §3.2—3.4 | 表S4、S5 |','| §3.2—3.4 | 表S4 |',1)
check('main_only_three_selected_replacements', reversed_main==(OUT/'before'/main.name).read_text())
oldst=(OUT/'before/SUPPLEMENTARY_METHODS.md').read_text()
check('supplement_S1_through_S8_preserved',st[st.index('<a id="sm-s1">'):st.index('<a id="sm-s9">')]==oldst[oldst.index('<a id="sm-s1">'):oldst.index('<a id="sm-s9">')])
check('supplement_S10_S11_preserved',st[st.index('<a id="sm-s10">'):]==oldst[oldst.index('<a id="sm-s10">'):])
check('S9_old_records_preserved',st[st.index('<a id="sm-s9">'):st.index('<a id="table-s5">')]==oldst[oldst.index('<a id="sm-s9">'):oldst.index('<a id="sm-s10">')])
check('failure_threshold_exit_and_scope_present',all(s in st for s in ['1.1967043900362632','10^{-10}','独立退出码3','FAIL/INCONCLUSIVE','不构成全参数域严格误差界']))
check('method_version_limitation_preserved','完整版本对应尚未闭合' in st)
check('no_placeholder_from_candidate', '[待编定表号]' not in mt+st)
mapping=list(csv.DictReader((SUP/'SUPPLEMENT_NUMBER_MAP.csv').open()))
check('index_eleven_rows_S9_points_to_S4_S5',len(mapping)==11 and next(r for r in mapping if r['previous_index']=='S9')['supplementary_table']=='表S4、S5')
links=[]
for path in [main,SUP/'SUPPLEMENTARY_METHODS.md',SUP/'README.md',OUT/'REPORT.md']:
    for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
        if target.startswith(('http:','https:')):
            continue
        raw,_,anchor=target.partition('#')
        raw=re.sub(r':\d+$','',raw)  # Local file links may carry editor line numbers.
        dest=(path.parent/raw).resolve() if raw else path
        if raw.startswith('/'):
            dest=Path(raw)
        exists=dest.exists()
        if anchor and exists:
            exists = f'id="{anchor}"' in dest.read_text()
        links.append(dict(source=str(path.relative_to(ROOT)),target=target,exists=exists))
check('all_selected_document_local_links_resolve',all(r['exists'] for r in links))
check('state_handoff_current_sync_both_present',all('GCI_author_sync_20261027/REPORT.md' in (ROOT/'docs/reports'/n).read_text().split('\n## ',2)[1] for n in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']))
result=dict(checks=checks,all_pass=all(checks.values()),protected_file_count=len(protected),local_links_checked=len(links),broken_links=[r for r in links if not r['exists']],new_solver_run=False)
(OUT/'verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(result,indent=2,ensure_ascii=False))
raise SystemExit(0 if result['all_pass'] else 1)
