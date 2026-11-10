#!/usr/bin/env python3
"""Bounded integrity/numbering checks for this authorized manuscript edit."""
import hashlib
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
manuscript=ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
before=(HERE/'manuscript_before.md').read_text()
after=manuscript.read_text()


def section(s, start, end):
    return s.split(start,1)[1].split(end,1)[0]


checks={
    'before_snapshot_hash_matches_record': hashlib.sha256(before.encode()).hexdigest()==(HERE/'manuscript_before_sha256.txt').read_text().strip(),
    'intro_and_abstract_unchanged': before.split('## 2 研究对象与比较方法',1)[0]==after.split('## 2 研究对象与比较方法',1)[0],
    'section4_unchanged': section(before,'## 4 结果','## 5 讨论')==section(after,'## 4 结果','## 5 讨论'),
    'discussion_conclusion_references_unchanged': section(before,'## 5 讨论','## 附录 A')==section(after,'## 5 讨论','## 附录 A'),
    'all_numbered_formula_blocks_unchanged':
        re.findall(r'\$\$(?:(?!\$\$)[\s\S])*?\\tag\{\d+\}(?:(?!\$\$)[\s\S])*?\$\$',before)
        ==re.findall(r'\$\$(?:(?!\$\$)[\s\S])*?\\tag\{\d+\}(?:(?!\$\$)[\s\S])*?\$\$',after),
    'equation_numbers_1_through_7': re.findall(r'\\tag\{(\d+)\}',after)==list(map(str,range(1,8))),
    'table_numbers_1_through_8': re.findall(r'^\*\*表 (\d+)\s',after,re.M)==list(map(str,range(1,9))),
    'reference_definitions_1_through_11': re.findall(r'^\[(\d+)\] ',after,re.M)==list(map(str,range(1,12))),
    'table2_and_table4_unchanged':
        section(before,'**表 2','> **注**')==section(after,'**表 2','> **注**')
        and section(before,'**表 4','规律很清楚')==section(after,'**表 4','规律很清楚'),
    'half_force_correction_reported':'半时间步力修正' in section(after,'### 2.1','### 2.2'),
    'thin_gap_ratio_reported':r'$h/\Delta x=5$' in section(after,'### 2.1','### 2.2'),
    'old_zero_boundary_error_claim_removed':'离散误差完全由内点格式控制' not in after,
    'old_two_grid_uncertainty_claim_removed':'其误差不确定度为' not in after,
    'all_section4_numeric_checks_pass': all(json.loads((HERE/'recomputed_section4.json').read_text())['numeric_claim_checks'].values()),
}
hashes=json.loads((HERE/'input_hashes.json').read_text())
checks['53_original_inputs_unchanged']=len(hashes)==53 and all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
checks['manuscript_matches_edit_record']=hashlib.sha256(manuscript.read_bytes()).hexdigest()==json.loads((HERE/'edit_record.json').read_text())['after_sha256']
assert all(checks.values()),checks
result=dict(checks=checks,all_checks_pass=True,
            limitations='Number/structure/integrity checks only; no full bibliography, rendered-figure, provenance or physical-gate approval.',
            manuscript_sha256=hashlib.sha256(manuscript.read_bytes()).hexdigest(),
            section4_before_sha256=hashlib.sha256(section(before,'## 4 结果','## 5 讨论').encode()).hexdigest(),
            section4_after_sha256=hashlib.sha256(section(after,'## 4 结果','## 5 讨论').encode()).hexdigest())
(HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
