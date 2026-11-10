#!/usr/bin/env python3
"""Read-only final evidence and inactive-draft audit, writing only this review."""
from pathlib import Path
import ast
import hashlib
import json
import re

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
CASE=ROOT/'CASE/unseen_v2_reference_v1'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for data in iter(lambda:f.read(1<<20),b''):h.update(data)
    return h.hexdigest()

def main():
    before=json.loads((OUT/'case_hashes_before.json').read_text())
    after={str(p):sha(p) for p in CASE.rglob('*') if p.is_file()}
    assert before==after
    old=json.loads((OUT/'historical_inputs_before.json').read_text())
    assert all(sha(p)==s for p,s in old.items())
    historical_report=ROOT/'docs/reports/URV_v1_preparation_20261101'
    manifest=json.loads((historical_report/'source_manifest.json').read_text())['files']
    shared={'docs/reports/SIM240_AI_CONTEXT.md','docs/reports/AI_HANDOFF_20261015.md'}
    assert all(sha(ROOT/p)==s for p,s in manifest.items() if p not in shared)
    draft=OUT/'S0_DRAFT_NOT_EXECUTABLE'
    contract=json.loads((draft/'S0_binding_DRAFT.json').read_text())
    assert not contract['simulation_authorized'] and contract['approved_run_ids']==contract['actual_formal_run_ids']==[]
    assert contract['author_external_data_history_confirmation']=='PENDING'
    assert contract['future_formal_binary_sha256'] is None and contract['effective_execution_inputs_sha256'] is None
    assert len(contract['cases'])==2
    for case in contract['cases']:
        assert case['actual_run_id'] is None and case['approved_run_id'] is None
        assert case['final_steady_config_sha256'] is None and case['current_new_result'] is None
        assert not Path(case['provisional_target_directory']).exists()
        cfg=dict(line.split('=',1) for line in Path(case['inactive_template']).read_text().splitlines())
        assert cfg['mode']=='describe' and cfg['output_directory']=='DRAFT_NOT_AN_EXECUTION_DIRECTORY'
        assert sha(case['inactive_template'])==case['inactive_template_sha256']
    assert not (CASE/'results').exists()
    assert json.loads((OUT/'external_data_history.json').read_text())['literal_answer']=='尚不能确认，需要核查'
    for p in OUT.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    links=0
    for p in [OUT/'REPORT.md',OUT/'INTAKE_NOTES.md']:
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if '://' in target:continue
            assert (p.parent/target.split('#')[0]).exists(),target
            links+=1
    for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        text=(ROOT/'docs/reports'/name).read_text()
        assert text.splitlines()[2].startswith('## URV-v1只读复核完成')
        assert 'PENDING_AUTHOR_CHECK' in text[:7000]
        previous=(OUT/'before'/name).read_text()
        end=previous.index('\n## ',previous.index('\n## ')+2)+1
        new_end=text.index('\n## ',text.index('\n## ')+2)+1
        assert previous[end:]==text[new_end:]
    result=dict(readonly_review_DELIVERY_PASS=True,execution_readiness='HOLD',
        package_files_unchanged=len(before),historical_bindings_unchanged=len(old),
        preparation_report_preserved=True,shared_context_and_handoff_updated=True,
        source_fixes_performed=False,compiler_calls=0,solver_calls=0,formal_runs_started=0,
        author_history='PENDING_AUTHOR_CHECK',S0_draft_cases=2,S0_effective_binding=False,
        proposed_directories_not_created=True,local_links_checked=links,
        formal_NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None,
        reference_qualified=False,strict_error_bound_established=False,submission_ready=False)
    (OUT/'final_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    files={str(p.relative_to(ROOT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='source_manifest.json'}
    files.update({str(p.relative_to(ROOT)):sha(p) for p in [ROOT/n for n in shared]})
    (OUT/'source_manifest.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
