#!/usr/bin/env python3
"""Document-only consistency and provenance checks; no solver or fit imports."""
from pathlib import Path
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
TARGET = ROOT/'docs/reports/SIM240_中文稿_限定措辞与理论附录候选_20261027.md'
original, candidate = BASE.read_text(), TARGET.read_text()
changes = json.loads((HERE/'changes.json').read_text())
review = ROOT/'docs/reports/Paper_core_reference_final_review_20261027'
protected = json.loads((HERE/'protected_inputs.json').read_text())['sha256']
changed = [p for p,h in protected.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
checks = {}
checks['base_matches_preparation_sha'] = hashlib.sha256(BASE.read_bytes()).hexdigest() == (HERE/'source_base_sha256.txt').read_text().split()[0]
checks['base_matches_final_review_binding'] = hashlib.sha256(BASE.read_bytes()).hexdigest() == json.loads((review/'source_manifest.json').read_text())['sha256'][str(BASE.relative_to(ROOT))]
checks['exactly_24_named_replacements_pending_author_adoption'] = len(changes)==24 and len({x['id'] for x in changes})==24 and all(x['author_approval']=='PENDING' for x in changes)
expected = original
for item in changes:
    assert expected.count(item['old'])==1,item['id']
    expected=expected.replace(item['old'],item['new'],1)
checks['candidate_prefix_exactly_matches_declared_replacements'] = candidate.startswith(expected)
suffix = candidate[len(expected):]
checks['only_declared_new_sections_appended'] = suffix.startswith('\n\n### D.7 ') and suffix.count('## 附录 E')==1
checks['standalone_appendix_equals_integrated_appendix'] = candidate[candidate.index('## 附录 E'):]==(HERE/'THEORY_APPENDIX_CANDIDATE.md').read_text()

def equations(text):
    return re.findall(r'\$\$(.*?)\$\$',text,re.S)
checks['all_original_displayed_math_unchanged'] = equations(original)==equations(expected)
checks['main_equation_tags_1_to_7_unchanged'] = re.findall(r'\\tag\{([^}]+)\}',expected)==re.findall(r'\\tag\{([^}]+)\}',original)==list('1234567')
checks['appendix_tags_E1_to_E6_only'] = re.findall(r'\\tag\{([^}]+)\}',suffix)==['E1','E2','E3','E4','E5','E6']
intrusion=next(x for x in changes if x['id']=='R23')
availability=next(x for x in changes if x['id']=='R24')
clean_base=original.replace(intrusion['old'],'',1).replace(availability['old'],availability['new'],1)
table_lines=lambda s:[line for line in s.splitlines() if line.startswith('|')]
checks['table_rows_unchanged_except_declared_C_availability_and_nonresearch_prefix'] = table_lines(clean_base)==table_lines(expected)
bibliography=lambda s:s.split('## 参考文献',1)[1].split('## 附录 A',1)[0]
checks['bibliography_verbatim_unchanged'] = bibliography(original)==bibliography(candidate)
checks['nonresearch_intrusion_removed_only_from_candidate'] = intrusion['old'] in original and intrusion['old'] not in candidate
checks['title_abstract_and_each_conclusion_explicit_5nm_scope'] = '5 nm' in candidate.splitlines()[0] and all('5 nm' in candidate.split('**'+n+'、**',1)[1].split('\n\n',1)[0] for n in ['一','二','三','四'])
checks['V2_and_reference_qualifiers_present'] = all(x in candidate for x in ['回顾性评价','作者采用待确认','不能作为连续解误差界','四个已检查几何','过压 $p-p_b$','上界不构成','本轮未重新求解或拟合'])
checks['no_G4_formula_substitution'] = 'F_{yy}^{\\rm V2}' in candidate and 'F_{xx}^{\\rm V2}' in candidate and '1.7685' in candidate and '0.4900' in candidate

summary=json.loads((review/'recomputed.json').read_text())
pair=[x for x in summary['ratios'] if x['h_nm']==125]
rounded=[format(x[k],'.4f')+'%' for x in pair for k in ['gain_5nm_percent','gain_2p5nm_percent']]
checks['four_added_paired_gains_match_existing_review_at_4_decimals'] = all(x in candidate for x in rounded)
broken=[]
for p in [TARGET,HERE/'REVISION_NOTE.md']:
    for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if link.startswith(('http:','https:','#')):continue
        if not (p.parent/link.split('#')[0]).exists():broken.append({'file':str(p),'target':link})
checks['markdown_local_links_resolve'] = not broken
checks['selected_prior_inputs_and_final_review_artifacts_unchanged'] = not changed
checks['readable_equation_delimiters_balanced'] = candidate.count('$$')%2==0
note=(HERE/'REVISION_NOTE.md').read_text()
checks['scientific_holds_and_unresolved_availability_recorded'] = all(x in note for x in ['reference_qualified=false','strict_error_bound_established=false','submission_ready=false','数据可用性','预测HOLD'])
out={'status':'CANDIDATE_DOCUMENT_CHECKS_ONLY','checks':checks,'all_checks_pass':all(checks.values()),
     'check_count':len(checks),'protected_selected_file_count':len(protected),'changed_protected_files':changed,
     'broken_local_links':broken,'added_gain_strings':rounded,'base_sha256':hashlib.sha256(BASE.read_bytes()).hexdigest(),
     'candidate_sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest(),
     'mathematical_proof_revalidated':False,'numerical_gate_reassessed':False,'author_approval':'PENDING',
     'solver_started':False,'real_N8_extraction':False,'submission_ready':False}
(HERE/'verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out,ensure_ascii=False,indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
