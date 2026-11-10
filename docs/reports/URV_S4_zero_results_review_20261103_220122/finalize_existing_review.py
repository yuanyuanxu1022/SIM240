"""Continue from six successful saved reader receipts; all subprocesses forbidden."""
from pathlib import Path
from unittest.mock import patch
import json,copy
import review_existing as r
from review_existing import *

def main():
    bound = stage.verify_seal(RELEASE, RELEASE_SHA)
    stage.validate_zero_authority(bound)
    prepared = stage.verify_seal(A, A_SHA)
    plan = stage.validate_zero_plan(bound)
    protected = load(OUT / 'protected_inputs_and_outputs_before.json')
    receipt = load(AUDIT / 'verification.json')
    raw = load(receipt['raw_manifest_path'])
    files = {str(p):sha(p) for p in AUDIT.rglob('*') if p.is_file()}
    need(sha(receipt['raw_manifest_path']) == receipt['raw_manifest_sha256'], 'raw manifest drift')
    need({p:h for p,h in files.items() if p not in (str(AUDIT/'verification.json'),str(AUDIT/'audit_files_sha256.json'))} == raw, 'raw file drift')
    view = copy.deepcopy(prepared)
    view.update(preparation_A_path=str(A), preparation_A_sha256=A_SHA,
                zero_audit_path=str(AUDIT/'verification.json'), zero_audit_sha256=sha(AUDIT/'verification.json'))
    view['inputs_sha256'].update(bound['inputs_sha256']);view['inputs_sha256'].update(files)
    for p in (A,A.with_suffix('.sha256'),RELEASE,RELEASE.with_suffix('.sha256')):
        view['inputs_sha256'][str(p)] = sha(p)
    stage.verify_zero_receipt(view)
    native = load(OUT/'native_review.json')
    need(native['PASS'] is True and len(native['native_records'])==18 and len(native['initial_statistics'])==6, 'incomplete prior raw review')
    calls = native['native_records']; summaries = native['initial_statistics']; readers=[]
    for i,record in enumerate([p for p in plan if p['mode']=='initialize'],1):
        process = load(OUT/f'reader_{i}_process.json')
        need(process['planned_case_id']==record['planned_case_id'] and process['independent_exit_code']==0 and process['timed_out'] is False, 'saved independent reader process mismatch')
        need(0 <= process['elapsed_seconds'] <= 300, 'independent reader cap')
        expected = OUT/('field_reread_'+record['planned_case_id']+'.json')
        need(process['report_path']==str(expected) and process['report_sha256']==sha(expected), 'fresh report drift')
        argv=['/usr/bin/pvpython','--force-offscreen-rendering','-B',str(CHECK/'analysis/read_fields.py'),'--run',record['output_directory'],'--out',str(expected)]
        need(process['argv']==argv, 'saved reader command mismatch')
        original = AUDIT/('field_readback_'+record['planned_case_id']+'.json')
        fresh = load(expected)
        need(fresh==load(original) and fresh['PASS'] is True and fresh['actual_reader'] is True and fresh['solver_executed'] is False, 'fresh and original readback mismatch')
        need(len(fresh['frames'])==1 and fresh['frames'][0]['step']==0, 'fresh frame mismatch')
        validate_initial_readback(record,original,AUDIT)
        readers.append(process)
    need(len(readers) == 6, 'exact six saved-field rereads required')
    need(all(sha(p) == h for p, h in protected.items()), 'protected input/output changed during review')
    stage.unchanged(bound['inputs_sha256'])
    stage.require_pristine(bound['prepared_runs'])
    save(OUT / 'independent_review_acceptance.json', dict(
        reviewed_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(), audit_id=stage.AUDIT_ID,
        release_path=str(RELEASE), release_sha256=RELEASE_SHA, preparation_A_sha256=A_SHA,
        ZERO_STEP_INDEPENDENT_REVIEW_PASS=True, ZERO_STEP_GEOMETRY_PASS=True,
        R1_actual_parameters_rechecked=True, R2_record_field_payload_chain_rechecked=True,
        eighteen_records_reviewed=len(calls), initial_field_reports_reviewed=6,
        actual_VTK_field_rereads=len(readers), initialized_frames_reread=6,
        raw_manifest_files_verified=len(raw), audit_files_verified=len(files),
        release_inputs_verified=len(bound['inputs_sha256']), protected_files_verified=len(protected),
        MRP_initial_arithmetic_exact=True, A1_initial_volume_path_exact=True,
        density_capture='NOT_APPLICABLE_S0_ONLY', new_h75_density_replay=False,
        reader_records=readers, B_sealing_condition_satisfied=True,
        native_solver_calls_this_review=0, time_steps_this_review=0, builds_this_review=0,
        original_files_changed=False, solver_executed=False,
        NUMERICAL_GATE='NOT_EVALUATED', geometry_PASS=None, RESULT_PASS=False,
        GRID_CHECKS_PASS='NOT_EVALUATED', REFERENCE_QUALIFIED_FOR_CASE=False,
        reference_qualified=False, MODEL_COMPARISON='NOT_EVALUATED', physical_validation='NOT_EVALUATED',
        submission_ready=False, formal_started=False, performance_started=False, next_stage_started=False))
    print(json.dumps(dict(ZERO_STEP_INDEPENDENT_REVIEW_PASS=True, native_records=18,
                         saved_field_rereads=6, raw_files=len(raw), audit_files=len(files),
                         protected_files=len(protected), B_sealing_condition_satisfied=True)))

if __name__=='__main__':
    with patch('subprocess.Popen', side_effect=AssertionError('No subprocess during saved-evidence finalization')):
        main()
