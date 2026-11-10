#!/usr/bin/env python3
"""Verify adopted candidate, cross-section wording, formulas and input integrity.

Uses the previously completed raw-result audit, checks its hashes again, and
does not run a solver, optimizer, or rewrite that previous audit's artifacts.
"""
import hashlib
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PREVIOUS=ROOT/'docs/reports/Methods_and_Section4_review_20261022'
TARGET=ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
before=(HERE/'manuscript_before.md').read_text()
after=TARGET.read_text()
record=json.loads((HERE/'edit_record.json').read_text())
audit=json.loads((PREVIOUS/'recomputed_section4.json').read_text())
hashes=json.loads((HERE/'input_hashes.json').read_text())


def section(text,start,end):
    return text.split(start,1)[1].split(end,1)[0]


def formulas(text):
    result={}
    for block in re.findall(r'\$\$([\s\S]*?)\$\$',text):
        tag=re.search(r'\\tag\{(\d+)\}',block)
        if tag:
            normalized=re.sub(r'\s+','',block.replace(r'\,',''))
            result[int(tag[1])]=normalized
    return result


candidate='## 4 结果'+(PREVIOUS/'Section4_revision_candidate.md').read_text().split('## 4 结果',1)[1]
adopted='## 4 结果'+section(after,'## 4 结果','## 5 讨论')
adopted=adopted.strip().removesuffix('---').strip()
abstract=section(after,'## 摘要','## 1 引言')
results=section(after,'## 4 结果','## 5 讨论')
discussion=section(after,'## 5 讨论','## 6 结论')
conclusion=section(after,'## 6 结论','## 参考文献')
checks={
    'pre_revision_snapshot_matches_record':hashlib.sha256(before.encode()).hexdigest()==record['before_sha256'],
    'manuscript_matches_edit_record':hashlib.sha256(TARGET.read_bytes()).hexdigest()==record['after_sha256'],
    'section4_exactly_adopts_authorized_candidate':adopted==candidate.strip(),
    'methods_and_numerical_reference_chapters_unchanged':section(before,'## 2 研究对象与比较方法','## 4 结果')==section(after,'## 2 研究对象与比较方法','## 4 结果'),
    'section5_2_unchanged':section(before,'### 5.2','### 5.3')==section(after,'### 5.2','### 5.3'),
    'bibliography_unchanged':section(before,'## 参考文献','## 附录 A')==section(after,'## 参考文献','## 附录 A'),
    'all_seven_numbered_formulas_mathematically_unchanged':len(formulas(before))==7 and formulas(before)==formulas(after),
    'equation_numbers_1_through_7':re.findall(r'\\tag\{(\d+)\}',after)==list(map(str,range(1,8))),
    'table_numbers_1_through_8':re.findall(r'^\*\*表 (\d+)\s',after,re.M)==list(map(str,range(1,9))),
    'reference_definitions_1_through_11':re.findall(r'^\[(\d+)\] ',after,re.M)==list(map(str,range(1,12))),
    'raw_audit_and_prior_artifacts_protected':all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items()),
    'all_previous_numeric_claim_checks_pass':all(audit['numeric_claim_checks'].values()),
    'full_cross_and_subset_residuals_in_abstract_results_discussion_conclusion':all('18.7%' in t and '6.9%' in t for t in (abstract,results,discussion,conclusion)),
    'local_worsening_disclosed_in_all_four_sections':all('反而增大' in t or '16.36%增至18.71%' in t for t in (abstract,results,discussion,conclusion)),
    'all_along_residual_present_in_abstract_results_conclusion':all('10.5%' in t for t in (abstract,results,conclusion)),
    'reference_grid_specified_in_all_four_sections':all('5 nm' in t for t in (abstract,results,discussion,conclusion)),
    'nonmonotonic_counterexample_in_results_and_discussion':all('139.14%' in t and '154.24%' in t for t in (results,discussion)),
    'h125_relative_gain_in_abstract_results_conclusion':all('39.2%' in t for t in (abstract,results,conclusion)),
    'reconstructed_angle_identified':all('主值重建' in t for t in (abstract,results,conclusion)),
    'threefold_value_is_distinguished_from_relative_error':'3.05倍' in results and '204.85%' in results,
    'incorrect_two_orders_and_threefold_error_removed':all(w not in after for w in ('跨越两个数量级','高估超过三倍','几乎不再起作用','这正是最薄间隙残差偏大的原因')),
    'candidate_mechanisms_explicitly_limited':'候选因素' in discussion and '没有独立测量局部阻力份额' in discussion and '不能单独证明间隙缺项' in discussion,
    'retrospective_evaluation_retained':'回顾性评价' in results and '回顾性评价' in abstract and '回顾性评价' in conclusion,
    'previous_stage_record_marked_historical':'上一轮随后仅审查§4' in after and '### D.4' in after,
}
assert all(checks.values()),{k:v for k,v in checks.items() if not v}
raw={p:h for p,h in hashes.items() if p.endswith('/steady/result.txt')}
assert len(raw)==52
data=dict(checks=checks,all_checks_pass=True,check_count=len(checks),
          protected_input_count=len(hashes),raw_result_count=len(raw),
          after_sha256=hashlib.sha256(TARGET.read_bytes()).hexdigest(),
          scope='Authorized prose synchronization and integrity checks; uses prior numerical audit, no new physical validation.',
          prior_audit='docs/reports/Methods_and_Section4_review_20261022/recomputed_section4.json')
(HERE/'verification.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(data,ensure_ascii=False,indent=2))
