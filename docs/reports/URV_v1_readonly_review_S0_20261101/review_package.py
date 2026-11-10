#!/usr/bin/env python3
"""Read sealed inputs; write only new review artifacts and isolated synthetic probes.

No solver, native precheck, compiler, fitting routine, or VTK reader is executed.
The reviewed CASE and all historical evidence must retain their initial hashes.
"""
from pathlib import Path
import ast
import csv
import difflib
import hashlib
import importlib
import json
import os
import subprocess
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_v1'
PREVIOUS=ROOT/'docs/reports/URV_v1_preparation_20261101'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for data in iter(lambda:f.read(1<<20),b''):h.update(data)
    return h.hexdigest()

def save(p,data):
    p=Path(p)
    if p.exists():raise FileExistsError(p)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def snapshot(folder):
    return {str(p):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}

def main():
    intake=json.loads((OUT/'intake_validation.json').read_text())
    assert intake['status']=='READY_FOR_LOCAL_REVIEW'
    start=snapshot(CASE);save(OUT/'case_hashes_before.json',start)
    for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        dest=OUT/'before'/name;dest.parent.mkdir(exist_ok=True)
        dest.write_bytes((ROOT/'docs/reports'/name).read_bytes())
    seal=CASE/'evidence/preparation_seal.json';bound=json.loads(seal.read_text())
    assert sha(seal)==(CASE/'evidence/preparation_seal.sha256').read_text().strip()
    assert not bound['simulation_authorized'] and bound['preparation_only_build']
    assert bound['approved_run_ids']==bound['actual_formal_run_ids']==[]
    assert all(sha(p)==s for p,s in bound['inputs_sha256'].items())
    previous_manifest=json.loads((PREVIOUS/'source_manifest.json').read_text())['files']
    shared={'docs/reports/SIM240_AI_CONTEXT.md','docs/reports/AI_HANDOFF_20261015.md'}
    assert all(sha(ROOT/p)==s for p,s in previous_manifest.items() if p not in shared)
    assert all(sha(ROOT/p)==previous_manifest[p] for p in shared)
    historical=json.loads((ROOT/'docs/reports/C_h75_reference_review_20261101/protected_inputs_verified.json').read_text())['files']
    historical=dict(historical)
    foundation=ROOT/'docs/reports/D4_foundation_acceptance_20261023/complete'
    input_hashes=json.loads((foundation/'input_hashes.json').read_text())
    historical.update({str(ROOT/p):s for p,s in input_hashes.items() if 'regression_' in p and p.endswith(('/diagnostics.csv','/result.txt'))})
    assert all(sha(p)==s for p,s in historical.items())
    save(OUT/'historical_inputs_before.json',historical)
    zero=CASE/'audits/URV_ZERO_20261101_01'
    zeroindex=json.loads((zero/'audit_files_sha256.json').read_text())
    assert all(sha(p)==s for p,s in zeroindex.items())
    audit=json.loads((zero/'verification.json').read_text())
    assert audit['actual_time_steps']==0 and audit['native_initialize']==24
    assert audit['native_describe']==24 and audit['native_precheck']==24
    edit=json.loads((PREVIOUS/'source_port_edits.json').read_text())
    restored=(CASE/'src/urv_reference.cpp').read_text()
    for e in reversed(edit['edits']):
        assert restored.count(e['new'])==1
        restored=restored.replace(e['new'],e['old'])
    base=ROOT/'CASE/D_series/D4_variable_groove_transport_20261023/src/variable_groove_transport.cpp'
    assert restored==base.read_text()
    sys.path.insert(0,str(CASE/'analysis'))
    checker=importlib.import_module('check_results')
    evidence=importlib.import_module('evidence')
    geometry_records=[]
    for entry in audit['records']:
        folder=Path(entry['modes']['precheck']['output'])
        cfg=evidence.kv(folder/'run_config.txt')
        geo=evidence.check_boundary(cfg,evidence.kv(folder/'boundary_audit.txt'))
        geometry_records.append(dict(planned_case_id=entry['planned_case_id'],independent_geometry=geo))
    save(OUT/'geometry_recalculation.json',dict(records=geometry_records,native_calls_this_review=0))
    # F01: exercise only a new artificial raw directory, never an existing run.
    artificial=OUT/'synthetic_probes/output_inside_raw/RAW_SYNTHETIC_NOT_SOLVER_OUTPUT'
    artificial.mkdir(parents=True)
    (artificial/'SYNTHETIC_MARKER.txt').write_text('Artificial error-path probe, no simulated data.\n')
    before=snapshot(artificial)
    proc=subprocess.run([sys.executable,'-B',str(CASE/'analysis/check_results.py'),
        '--run',str(artificial),'--release',str(seal),'--release-sha256',sha(seal),
        '--out',str(artificial)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,
        env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'),timeout=30)
    after=snapshot(artificial)
    (artificial.parent/'cli.log').write_text(proc.stdout)
    created=sorted(set(after)-set(before))
    assert proc.returncode==2 and str(artificial/'failure.json') in created
    save(artificial.parent/'probe.json',dict(synthetic_only=True,independent_exit_code=proc.returncode,
        created_inside_artificial_raw=created,observed_raw_write_after_rejection=True,
        actual_CASE_or_results_touched=False))
    # F02: the helper computes differences, but check_run raises before saving it.
    legacy=OUT/'synthetic_probes/legacy_difference'
    for label,tail in [('old','1.0'),('new','1.1')]:
        folder=legacy/label;folder.mkdir(parents=True)
        (folder/'diagnostics.csv').write_text('step,J,mass_error\n0,0.5,0\n1,'+tail+',0\n')
    comparison=checker.compare_legacy(legacy/'new',legacy/'old')
    assert not comparison['all_exact']
    source=(CASE/'analysis/check_results.py').read_text()
    branch=source.index("need(legacy['all_exact']")
    directory=source.index('output.mkdir(parents=True,exist_ok=False)')
    assert branch<directory
    save(legacy/'probe.json',dict(synthetic_only=True,helper_comparison=comparison,
        evidence_kind='helper computation plus static control-flow inspection; not full-run reproduction',
        raises_before_analysis_directory_creation=True,
        difference_report_saved_by_this_review_not_by_original_failure_path=True))
    # F03: an artificial release missing native source/binary/libs is accepted by
    # binding(). No solver/runner reads this fixture; it is not author approval.
    coverage=OUT/'synthetic_probes/incomplete_release'
    coverage.mkdir(parents=True)
    minimum={str(p):sha(p) for folder in ['analysis','common'] for p in (CASE/folder).glob('*') if p.is_file()}
    release=coverage/'SYNTHETIC_NOT_AN_EXECUTION_CONTRACT.json'
    payload=dict(protocol_id='URV-v1',simulation_authorized=True,preparation_only_build=False,
        author_external_data_history_confirmation='CONFIRMED',inputs_sha256=minimum,
        fixture_label='SYNTHETIC_CALL_TO_BINDING_ONLY_NOT_USER_AUTHORIZATION')
    save(release,payload)
    accepted=checker.binding(release,sha(release))
    assert accepted==payload and str(CASE/'build/urv_reference') not in minimum
    save(coverage/'probe.json',dict(synthetic_only=True,binding_function_returned_success=True,
        covered_python_and_common=len(minimum),native_binary_bound=False,native_source_bound=False,
        build_dependencies_bound=False,actual_user_authorization=False,native_calls=0))
    # F04: future batches with distinct seals cannot share the current CLI anchor.
    stages=OUT/'synthetic_probes/separate_stage_anchors';stages.mkdir(parents=True)
    later=stages/'SYNTHETIC_S1';later.mkdir()
    save(later/'completion.json',dict(release_sha256='B'*64,independent_process_exit_code=0))
    with patch.object(checker,'binding',return_value={'inputs_sha256':{}}):
        try:checker.check_run(later,Path('unused'),'A'*64,stages/'analysis')
        except evidence.EvidenceError as error:message=str(error)
        else:raise AssertionError('mixed stage anchors unexpectedly accepted')
    assert 'independent exit' in message
    save(stages/'probe.json',dict(synthetic_only=True,release_layer_mocked=True,
        stage_A_anchor='A'*64,stage_B_completion_anchor='B'*64,observed_rejection=message,
        cli_static_fact='one --release and one --release-sha256 supplied to all 24 check_run calls',
        no_real_stages_run=True))
    assert snapshot(CASE)==start
    assert all(sha(p)==s for p,s in historical.items())
    assert not (CASE/'results').exists()
    save(OUT/'review_verification.json',dict(readonly_review_completed=True,
        package_tree_files_unchanged=len(start),preparation_bindings_unchanged=len(bound['inputs_sha256']),
        previous_report_manifest_checked=True,historical_bindings_unchanged=len(historical),
        existing_zero_audit_output_files_verified=len(zeroindex),
        independently_recomputed_geometry_configurations=24,
        reversible_source_edits_checked=len(edit['edits']),synthetic_review_probes=4,
        old_35_tests_read_as_prior_evidence_not_rerun=True,solver_calls=0,compiler_calls=0,
        new_VTK_reader_calls=0,formal_runs_started=0,
        external_history_answer='尚不能确认，需要核查',external_history_status='PENDING_AUTHOR_CHECK',
        execution_readiness='HOLD',S0_execution_binding_status='DRAFT_ONLY_NOT_EFFECTIVE',
        physical_validation='NOT_EVALUATED',new_reference_qualified=False))
    print(json.dumps(dict(readonly_review_completed=True,findings=4,source_unchanged=True,
        compiler_calls=0,solver_calls=0,execution_readiness='HOLD')))

if __name__=='__main__':main()
