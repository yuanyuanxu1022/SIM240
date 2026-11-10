#!/usr/bin/env python3
"""Verify document synchronization and preservation of selected existing evidence."""
from pathlib import Path
import csv
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE=ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
PACKAGE=ROOT/'docs/reports/Paper_bounded_candidate_20261027'
CANDIDATE=ROOT/'docs/reports/SIM240_中文稿_限定措辞与理论附录候选_20261027.md'
before=(HERE/'before'/BASE.name).read_text()
formal=BASE.read_text()
candidate=CANDIDATE.read_text()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
status=json.loads((HERE/'sync_status.json').read_text())
ops=json.loads((HERE/'status_adaptations.json').read_text())
expected=candidate
for op in ops:
    assert expected.count(op['old'])==1,op['id']
    expected=expected.replace(op['old'],op['new'],1)
changes=json.loads((PACKAGE/'changes.json').read_text())
applied=list(csv.DictReader((HERE/'applied_items.csv').open()))
protected=json.loads((HERE/'protected_inputs.json').read_text())['sha256']
mismatches=[p for p,h in protected.items() if sha(ROOT/p)!=h]
displayed=lambda s:re.findall(r'\$\$(.*?)\$\$',s,re.S)
main=lambda s:s.split('## 参考文献',1)[0]
tables=lambda s:[line for line in s.splitlines() if line.startswith('|')]
bibliography=lambda s:s.split('## 参考文献',1)[1].split('## 附录 A',1)[0]
proof=lambda s:s[s.index('设一个周期的截面为'):]
adapted_ids={'R02','R03'}
missing=[r['id'] for r in changes if r['id'] not in adapted_ids and r['new'] and r['new'] not in formal]
checks={
 'formal_exactly_candidate_plus_7_declared_status_adaptations':formal==expected and len(ops)==7,
 'pre_sync_snapshot_matches_candidate_base':sha(HERE/'before'/BASE.name)==status['before_sha256'],
 'candidate_unchanged_since_review':sha(CANDIDATE)==status['candidate_sha256'],
 'current_formal_matches_sync_binding':sha(BASE)==status['after_sha256'],
 'all_24_revisions_recorded_and_present':len(changes)==24 and len(applied)==25 and not missing,
 'selection_interpretation_and_human_review_limits_explicit':all(r['selection_basis']=='ALL_DELIVERED_ITEMS_NO_EXCLUSIONS_SPECIFIED' and r['separate_itemwise_human_scientific_verification']=='NOT_RECORDED' for r in applied),
 'main_displayed_formulas_unchanged':displayed(main(before))==displayed(main(formal)),
 'main_equation_tags_1_to_7_preserved':re.findall(r'\\tag\{([^}]+)\}',main(formal))==list('1234567'),
 'all_8_main_numeric_tables_unchanged':tables(main(before))==tables(main(formal)),
 'bibliography_unchanged':bibliography(before)==bibliography(formal),
 'appendix_E_proof_body_verbatim_candidate':proof(formal)==proof(candidate),
 'appendix_E_tags_preserved':re.findall(r'\\tag\{([^}]+)\}',proof(formal))==['E1','E2','E3','E4','E5','E6'],
 'title_and_four_conclusions_explicit_5nm': '5 nm' in formal.splitlines()[0] and all('5 nm' in formal.split('**'+n+'、**',1)[1].split('\n\n',1)[0] for n in ['一','二','三','四']),
 'V2_coefficients_preserved':all(s in formal for s in ['1.7685','1.6331','0.4900','0.6990','F_{yy}^{\\rm V2}','F_{xx}^{\\rm V2}']),
 'nonresearch_intrusion_removed': '六级听力邪修版' not in formal,
 'all_476_selected_existing_inputs_unchanged':len(protected)==476 and not mismatches,
 'author_final_review_and_scientific_holds_preserved':status['final_author_scientific_approval']=='PENDING' and not status['submission_ready'] and not status['reference_qualified'] and not status['strict_error_bound_established'] and status['prediction_permission']=='HOLD' and '作者终审待完成' in formal,
}
broken=[]
for path in [BASE,HERE/'REVISION_NOTE.md']:
    for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
        if target.startswith(('http:','https:','#')):continue
        # This report is emitted below; validate its readability after writing.
        if (path.parent/target.split('#')[0]).resolve()==(HERE/'verification.json').resolve():continue
        if not (path.parent/target.split('#')[0]).exists():broken.append({'file':str(path.relative_to(ROOT)),'target':target})
checks['local_markdown_links_resolve']=not broken
result={'checks':checks,'all_checks_pass':all(checks.values()),'check_count':len(checks),
 'missing_revision_ids':missing,'protected_selected_file_count':len(protected),'changed_protected_files':mismatches,
 'broken_links':broken,'before_sha256':status['before_sha256'],'candidate_sha256':sha(CANDIDATE),
 'formal_sha256':sha(BASE),'scope':'document synchronization only; no new theory certification or numerical Gate',
 'new_solver_run_id':None,'scientific_accuracy_pass':False,'submission_ready':False}
(HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
assert json.loads((HERE/'verification.json').read_text())==result
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
