"""Prepare/inspect eighteen zero calls; --execute requires a zero-only release."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import time

CASE = Path(__file__).resolve().parents[1]
CHECKER = CASE.parent / 'unseen_v2_reference_checker_S4_reuse_v1'
sys.path.insert(0, str(CHECKER / 'analysis'))
from evidence import need, sha, kv, save, exact_parameters, check_boundary, close
from stage_s4 import (AUDIT_ID, ELF_SHA, MODES, verify_seal, validate_zero_plan,
                      validate_zero_authority, unchanged, require_pristine)
from run_S4 import resources, process_environment, child_limits, native_process, output_hashes


def call_native(binary, record, env):
    config = kv(record['run_config_path'])
    need(record['mode'] in MODES and config['mode'] == record['mode'], 'zero audit forbids steady')
    need(sha(binary) == ELF_SHA, 'zero audit binary drift')
    run = Path(record['output_directory'])
    process = native_process([binary, record['run_config_path']], run, env, 300)
    (run / 'exit_code.txt').write_text(str(process['independent_process_exit_code'])+'\n')
    save(run / 'process_receipt.json', process)
    need(process['independent_process_exit_code'] == 0 and not process['timed_out'] and
         not process.get('resource_stop_reason'), 'zero call failed; stop without retry')
    execution = kv(run / 'execution_audit.txt')
    need(execution['preparation_only_build'] == '0' and execution['collide_and_stream_calls'] == '0',
         'wrong binary or nonzero time advancement')
    return dict(native_exit_code=0, collide_and_stream_calls=0,
                elapsed_seconds=process['elapsed_seconds'], output=str(run))


def field_readback(run, out, log, env):
    command = ['/usr/bin/pvpython', '--force-offscreen-rendering', '-B',
               str(CHECKER/'analysis/read_fields.py'), '--run', str(run), '--out', str(out)]
    started = time.monotonic()
    try:
        with log.open('x') as stream:
            checked = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT,
                                     env=env, timeout=300, preexec_fn=child_limits)
    except subprocess.TimeoutExpired:
        save(out.with_suffix('.process.json'), dict(independent_exit_code=None, timed_out=True,
             elapsed_seconds=time.monotonic()-started, exit_code_status='not returned by subprocess.run'))
        raise
    save(out.with_suffix('.process.json'), dict(independent_exit_code=checked.returncode, timed_out=False,
         elapsed_seconds=time.monotonic()-started))
    need(checked.returncode == 0, 'actual field reader failed')
    result = json.loads(out.read_text())
    need(result.get('PASS') is True and result.get('actual_reader') is True and len(result['frames']) == 1,
         'independent initial field readback incomplete')


def audit_outputs(record):
    from zero_evidence_s4 import validate_zero_outputs
    return validate_zero_outputs(record)


def execute(release, expected_sha, data):
    # Full authority and pristine-path checks precede every new output or process.
    bound = verify_seal(release, expected_sha)
    need(data == bound, 'inspection/release mismatch')
    validate_zero_authority(bound)
    records = validate_zero_plan(bound)
    require_pristine(records)
    resources(True)
    folder = CASE/'audits'/AUDIT_ID
    attempt = CASE/'audit_attempts'/expected_sha
    attempt.mkdir(parents=True, exist_ok=False)
    need(not (folder/'verification.json').exists(), 'audit receipt exists; no retry')
    env = process_environment(); completed = []
    for record in records:
        available = resources(False); before = unchanged(bound['inputs_sha256'])
        result = call_native(bound['provenance']['native_binary'], record, env)
        result.update(planned_case_id=record['planned_case_id'], run_id=record['run_id'],
                      mode=record['mode'], resources_before=available)
        result['geometry'] = audit_outputs(record)
        if record['mode'] == 'initialize':
            out = folder / ('field_readback_'+record['planned_case_id']+'.json')
            log = folder / ('field_reader_'+record['planned_case_id']+'.log')
            field_readback(Path(record['output_directory']), out, log, env)
            from zero_evidence_s4 import validate_initial_readback
            validate_initial_readback(record, out, folder)
            result.update(field_readback=str(out), field_readback_sha256=sha(out))
        need(unchanged(bound['inputs_sha256']) == before, 'zero audit changed bound inputs')
        completed.append(result)
        save(folder/'progress'/f'{len(completed):02d}.json', result)
        print(json.dumps(dict(planned_case_id=record['planned_case_id'], mode=record['mode'],
                              native_exit=0, actual_time_steps=0)), flush=True)
    files = {str(folder/relative): digest for relative, digest in output_hashes(folder).items()}
    manifest = folder/'audit_files_sha256.json'; save(manifest, files)
    save(folder/'verification.json', dict(audit_id=AUDIT_ID, ZERO_STEP_AUDIT_PASS=True,
        binary_sha256=ELF_SHA, native_describe=6, native_precheck=6, native_initialize=6,
        initialized_frames_read=6, actual_time_steps=0, steady_mode_invocations=0, records=completed,
        raw_manifest_path=str(manifest), raw_manifest_sha256=sha(manifest),
        preparation_A_sha256=bound['preparation_A_sha256'], audit_release_path=str(release),
        audit_release_sha256=expected_sha, density_capture='NOT_APPLICABLE_S0_ONLY',
        formal_simulation_started=False, NUMERICAL_GATE='NOT_EVALUATED', RESULT_PASS=False,
        reference_qualified=False, next_stage_started=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', type=Path, required=True)
    ap.add_argument('--release-sha256', required=True)
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args()
    try:
        path = args.release.resolve(); data = verify_seal(path, args.release_sha256)
        records = validate_zero_plan(data); require_pristine(records)
        if args.execute:
            execute(path, args.release_sha256, data)
        else:
            print(json.dumps(dict(ZERO_PLAN_BINDING_CHECK=True, solver_executed=False,
                planned_native_calls=len(records), planned_initial_field_reads=6,
                native_zero_step_authorized=data.get('native_zero_step_authorized', False))))
        return 0
    except Exception as error:
        print(type(error).__name__+': '+str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
