"""Read-only static audit of existing code, logs, manifests and provenance."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
CODE=ROOT/'CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/offline_extractor_preparation_20261026'
PREP=ROOT/'docs/reports/G4_offline_extractor_preparation_20261026'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()

def read(p):return json.loads(p.read_text())

def main():
    m=read(OUT/'source_manifest.json')
    for group,files in m.items():
        for name,h in files.items():assert sha(ROOT/name)==h,name
    fixture=read(PREP/'fixture_results.json')
    assert fixture['tests_run']==17 and fixture['failures']==fixture['errors']==fixture['skipped']==0
    assert len(fixture['code_sha256'])==4
    for name,h in fixture['code_sha256'].items():assert sha(ROOT/name)==h,name
    log=(PREP/'fixtures_final.log').read_text()
    assert sum(s.endswith(' ... ok') for s in log.splitlines())==17
    assert 'Ran 17 tests' in log and log.strip().endswith('OK')
    for p in CODE.glob('*.py'):ast.parse(p.read_text())
    tree=ast.parse((CODE/'extractor.py').read_text())
    flag=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REAL_RECORD_EXTRACTION_ENABLED' for t in n.targets))
    assert ast.literal_eval(flag.value) is False
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='extract_real_record')
    assert isinstance(fn.body[0],ast.If) and isinstance(fn.body[0].body[0],ast.Raise)
    record=Path('/home/dell/yuanyuanxu/SIM240_runtime_records/reference_pilot_n8_20261026/D4_N8_diag_v3_1_20261026_v1')
    c=read(record/'contract.json');capture=read(record/'capture_manifest.json');completed=read(record/'archive/worker_completion.json')
    digest=hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    assert capture['contract_sha256']==completed['contract_sha256']==digest
    assert c['run_id']==capture['run_id']==completed['run_id']=='D4_N8_diag_v3_1_20261026_v1'
    assert c['planned_id']=='B0MIN_MMS_mixed_N8'
    assert capture['archive_status']=='ARCHIVE_COMPLETE' and capture['independent_exit_code']==0
    assert capture['children_stopped'] is True and capture['inputs_unchanged'] is True
    metadata=read(record/'archive/system/manifest.json')['metadata']
    assert metadata['pressure_support']['physical_pressure_dofs']==153
    assert metadata['pressure_support']['pressure_slave_dofs_removed']==9
    assert metadata['pressure_support']['algebraic_nonzero_dofs']==144
    assert metadata['matrix_shape']==[1275,1275]
    freeze=ROOT/'docs/reports/Correlation_selection_freeze_20261024'
    g4=read(freeze/'candidate_lock.json')
    for p,h in g4['bound_files'].items():assert sha(freeze/p)==h,p
    findings=read(OUT/'findings.json')
    assert len(findings['items'])==5
    text=(OUT/'REVIEW.md').read_text()
    for link in re.findall(r'\]\(([^)]+)\)',text):
        if not link.startswith('http') and link!='verification.json':assert (OUT/link).is_file(),link
    assert not any(n.split('.')[0] in {'numpy','scipy','ufl','petsc4py','dolfinx','extractor','numerics','test_fixtures','worker','solver','assembly'} for n in sys.modules)
    out=dict(status='STATIC_REVIEW_EVIDENCE_CHECK_PASS',review_conclusion='STATIC_REVIEW_COMPLETE_REAL_EXTRACTION_HOLD',
             source_counts={k:len(v) for k,v in m.items()},G4_bound_files_unchanged=len(g4['bound_files']),
             all_reviewed_files_and_raw_records_unchanged=True,recorded_fixture_tests=17,
             recorded_fixture_python_files=4,fixture_tests_rerun_this_task=0,
             new_synthetic_tests_executed=0,real_N8_arrays_loaded=False,real_field_metrics_computed=False,
             actual_read_branch_executed=False,backend_imported=False,solver_started=False,
             theory_criteria_changed=False,strict_error_bound_established=False,
             code_or_fixture_changed=False,real_entry_remains_closed=True,
             actual_N8_contract_sha256=digest,actual_pressure_metadata=dict(physical_dofs=153,slaves=9,independent_support=144),
             findings=5,release_blockers=2,validation_and_record_gaps=2,documentation_correction=1,
             reference_qualified=False,NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None,
             prediction_permission='HOLD',submission_ready=False)
    (OUT/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
    print(out['status'],'; original 17-test record preserved, zero tests rerun; real entry HOLD.')

if __name__=='__main__':main()
