"""Check the limited receipt evidence and preserved inputs; no numerical backend."""
from pathlib import Path
import hashlib
import json
import re

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
checks=[]
def check(name,passed,detail=None):
    checks.append({'name':name,'pass':bool(passed),'detail':detail})
protected=json.loads((OUT/'protected_inputs.json').read_text())
changed=[p for p,h in protected.items() if not Path(p).is_file() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
check('selected_existing_files_unchanged',not changed,{'count':len(protected),'changed':changed})
screen=json.loads((OUT/'evidence/downloads_pdf_screening.json').read_text())
full=json.loads((OUT/'evidence/downloads_fulltext_matches.json').read_text())
check('22_pdf_files_identified_and_extracted',len(screen)==len(full)==22 and all(x['pdftotext_exit']==0 for x in screen+full))
check('all_screened_paths_are_user_supplied_directory',all(Path(x['path']).is_relative_to('/home/dell/下载') for x in screen))
matches=[(x['path'],m['pdf_page'],m['target']) for x in full for m in x['matches']]
pages={(p,n) for p,n,t in matches}
check('seven_matches_on_six_pages',len(matches)==7 and len(pages)==6 and not any(t=='P10' for p,n,t in matches))
previews=['openlb_refs_p28.png','jtice_refs_p11.png','micromix_refs_p23.png','micromix_refs_p24.png','guide_refs_p174.png','guide_refs_p175.png']
check('six_reviewed_previews_present',all((OUT/'evidence'/p).is_file() for p in previews),{'visual_review':'All six tool-rendered pages inspected during this turn; bibliographic entries/continuation only.'})
history=json.loads((OUT/'evidence/historical_tool_excerpts.json').read_text())
scope=json.loads((OUT/'evidence/history_search_scope.json').read_text())
check('49_historical_calls_with_paired_outputs',len(history)==49 and len(scope['sessions_with_targeted_calls'])==4 and all(h.get('call_id') and 'recorded_tool_output' in h for h in history))
build=json.loads((OUT/'evidence/downloads_build_screening.json').read_text())
check('downloads_no_named_build_or_target_text_matches',not build['named_build_archive_candidates'] and not build['targeted_text_matches'])
receipt=json.loads((OUT/'contract_receipt.json').read_text())
check('unreceived_originals_not_falsely_closed',receipt['new_qualified_originals']==0 and all(not p['required_fulltext_received'] and not p['specified_formula_review_performed'] for p in receipt['papers']))
check('four_build_gaps_and_scientific_status_preserved',not any(receipt['build_groups_complete'].values()) and not receipt['reference_qualified'] and not receipt['strict_error_bound_established'] and receipt['NUMERICAL_GATE']=='NOT_EVALUATED' and not receipt['RESULT_PASS'] and receipt['geometry_PASS'] is None and receipt['new_run_id'] is None and not receipt['compiler_or_solver_executed'] and not receipt['real_n8_extraction'])
lookup=json.loads((OUT/'public_lookup.json').read_text())
response_bad=[]
for item in lookup['requests']:
    if item.get('file') and hashlib.sha256((OUT/item['file']).read_bytes()).hexdigest()!=item['response_sha256']:
        response_bad.append(item['file'])
check('saved_lookup_response_hashes',not response_bad,response_bad)
broken=[]
for p in [OUT/'REPORT.md',OUT/'MISSING_ITEMS.md']:
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if target.startswith(('https://','http://','#')):continue
        resolved=(p.parent/target.split('#')[0]).resolve()
        if resolved==(OUT/'verification.json').resolve():continue
        if not resolved.exists():broken.append([p.name,target])
check('report_local_links',not broken,broken)
tails=[]
for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
    current=(ROOT/'docs/reports'/name).read_text()
    old=(OUT/'before'/name).read_text()
    old_tail=old[old.index('\n## ',old.index('## ')+3)+1:]
    current_tail=current[current.index('\n## ',current.index('## ')+3)+1:]
    tails.append(old_tail==current_tail)
check('two_handoffs_historical_body_preserved',all(tails))
result={'scope':'Specified-material receipt, evidence bookkeeping and selected bytes; not physics/numerical validation',
        'all_checks_pass':all(c['pass'] for c in checks),'check_count':len(checks),'checks':checks}
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'all_checks_pass':result['all_checks_pass'],'checks':len(checks),'protected_files':len(protected),'failed':[c['name'] for c in checks if not c['pass']]},ensure_ascii=False))
raise SystemExit(0 if result['all_checks_pass'] else 1)
