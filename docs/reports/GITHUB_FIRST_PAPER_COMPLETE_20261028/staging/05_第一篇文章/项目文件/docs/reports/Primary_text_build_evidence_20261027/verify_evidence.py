"""Verify read-only evidence bookkeeping and protected bytes, not CFD accuracy."""
from pathlib import Path
import hashlib
import json
import re

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
protected = json.loads((OUT/'protected_inputs.json').read_text())
bad = [p for p,h in protected.items() if not Path(p).is_file() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
build = json.loads((OUT/'build_evidence.json').read_text())
ledger = json.loads((OUT/'retrieval_ledger.json').read_text())
version = json.loads((OUT/'ref10_version_identity.json').read_text())
close = json.loads((OUT/'closeout.json').read_text())
checks = []
def check(name, ok, detail=None):
    checks.append({'name':name,'pass':bool(ok),'detail':detail})
check('selected_existing_files_unchanged',not bad,{'count':len(protected),'changed_or_missing':bad})
check('specified_runs_and_four_groups',build['run_count']==52 and sorted(g['count'] for g in build['hash_groups'])==[2,6,22,22])
check('retained_binary_identity_only_28_runs',build['linked_runs_with_retained_elf']==28)
check('24_runs_still_without_matched_elf',sum(g['count'] for g in build['hash_groups'] if not g['matching_elf_paths'])==24)
check('four_source_makefile_snapshots_match',len(build['source_comparisons'])==4 and all(x['matches_package_and_fixed_git'] for x in build['source_comparisons']))
check('extra_archive_binary_not_substituted',any(a['elf'] and a['sha256'].startswith('037a7220') and not a['matching_run_ids'] for a in build['artifacts']))
check('full_build_gap_preserved',build['historical_source_build_binding_complete'] is False and close['historical_build_binding_complete'] is False)
check('six_doi_records_parsed',len(ledger['papers'])==3 and all(x['new_full_text_saved_and_visually_verified'] is False for x in ledger['papers']))
check('published_version_identity_without_false_fulltext_closure',len(version['published_authors'])==6 and version['publication_date']=='2008/07' and not version['published_pdf_downloaded'] and not version['full_version_equivalence_verified'])
payload_bad=[]
for x in ledger['requests']:
    if x.get('file'):
        p=OUT/x['file']
        if hashlib.sha256(p.read_bytes()).hexdigest()!=x['sha256'] or p.stat().st_size!=x['bytes']:
            payload_bad.append(x['file'])
check('saved_response_bytes_match_ledger',not payload_bad,payload_bad)
check('failed_pdf_not_delivered_as_pdf',not list((OUT/'evidence').glob('*.pdf')))
broken=[]
for p in [OUT/'REPORT.md',OUT/'MINIMUM_EVIDENCE_CONTRACT.md']:
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        resolved = (p.parent/target.split('#')[0]).resolve()
        # This certificate is written below; it need not preexist its own first check.
        if resolved == (OUT/'verification.json').resolve():
            continue
        if not target.startswith(('https://','http://','#')) and not resolved.exists():
            broken.append([p.name,target])
check('report_local_links_resolve',not broken,broken)
for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
    current=(ROOT/'docs/reports'/name).read_text()
    old=(OUT/'before'/name).read_text()
    current_tail=current[current.index('\n## ',current.index('## ')+3)+1:]
    old_tail=old[old.index('\n## ',old.index('## ')+3)+1:]
    check(name+'_old_body_preserved',current_tail==old_tail)
check('scientific_status_and_execution_boundary_preserved',close['NUMERICAL_GATE']=='NOT_EVALUATED' and not close['RESULT_PASS'] and close['geometry_PASS'] is None and not close['reference_qualified'] and not close['solver_or_compiler_executed'] and not close['theory_changed'] and not close['real_n8_extraction'])
result={'scope':'Evidence bookkeeping and selected bytes; no numerical/physics acceptance','all_checks_pass':all(x['pass'] for x in checks),'check_count':len(checks),'checks':checks}
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'all_checks_pass':result['all_checks_pass'],'check_count':len(checks),'protected_files':len(protected),'failed':[x['name'] for x in checks if not x['pass']]},ensure_ascii=False))
raise SystemExit(0 if result['all_checks_pass'] else 1)
