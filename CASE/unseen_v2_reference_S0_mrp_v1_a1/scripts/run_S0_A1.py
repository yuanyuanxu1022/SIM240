#!/usr/bin/env python3
"""A1 S0 only. Read-only default; --execute requires separately authorized release.

Original URV acceptance and independent density replay must both pass before T.
The capture index is finalized and completion-bound before independent acceptance.

The prepared binding intentionally has no approved executions. A separately
authorized, externally pinned launch release is required before any process
can enter steady mode. No retries, next-stage chaining, or threshold changes.
"""
from pathlib import Path
import argparse
import json
import os
import resource
import signal
import shutil
import subprocess
import sys
import time

CASE = Path(__file__).resolve().parents[1]
CHECKER = CASE.parent / 'unseen_v2_reference_checker_mrp_v1_a1'
sys.path.insert(0, str(CHECKER / 'analysis'))
from evidence import need, sha, save, kv
from contracts import verify_provenance, approved_records
from check_results import binding
from mass_capture import finalize_capture


def resources(initial):
    mem = next(int(line.split()[1]) * 1024 for line in Path('/proc/meminfo').read_text().splitlines()
               if line.startswith('MemAvailable:'))
    disk = shutil.disk_usage(CASE).free
    need(mem >= 12 * 1024**3, 'available RAM below frozen 12 GiB requirement')
    need(disk >= (100 if initial else 8) * 1024**3, 'free disk below frozen requirement')
    return dict(MemAvailable_bytes=mem, disk_free_bytes=disk)


def unchanged(inputs):
    current = {p: sha(p) for p in inputs}
    need(current == inputs, 'bound input bytes changed')
    return current


def inspect(release, expected_sha):
    need(sha(release) == expected_sha, 'release trust anchor mismatch')
    data = json.loads(release.read_text())
    need(data['protocol_id'] == 'URV-v1' and data['stage'] == 'S0_REGRESSION', 'S0 protocol/stage only')
    need(data['author_external_data_history_confirmation'] == 'CONFIRMED', 'history declaration required')
    declaration = Path(data['author_reply_file'])
    need(sha(declaration) == data['author_reply_sha256'], 'author declaration binding')
    need(json.loads(declaration.read_text())['status'] == 'AUTHOR_DECLARED_NONUSE_CONFIRMED', 'author declaration scope')
    unchanged(data['inputs_sha256'])
    verify_provenance(data)
    need(data.get('addendum_id') == 'URV-MRP-v1-A1', 'A1 addendum binding required')
    need(data['inputs_sha256'][data['provenance']['native_binary']] ==
         'c1fc2a1eeacced8f11a9bb045c25d70936b7be03fe5495a0b8f51789bd8fe8af', 'wrong A1 binary')
    zero = Path(data['zero_audit_path'])
    need(data['inputs_sha256'].get(str(zero)) == data['zero_audit_sha256'] == sha(zero), 'zero audit not bound')
    audit = json.loads(zero.read_text())
    need(audit['ZERO_STEP_AUDIT_PASS'] is True and audit['actual_time_steps'] == 0 and
         audit['native_describe'] == audit['native_precheck'] == audit['native_initialize'] == 2,
         'A1 two-direction zero audit incomplete')
    for direction in ('P','T'):
        baseline = data['mass_repair_baselines'][direction]
        for key in ('v12_diagnostics','v12_output_manifest'):
            path = Path(baseline[key])
            need(data['inputs_sha256'].get(str(path)) == sha(path), 'unbound mass repair baseline')
    # Check prepared identities without fabricating authorization or a passing
    # execution contract. This projection is never written or passed to binding.
    projection = dict(data, approved_run_ids=data['prepared_run_ids'], approved_runs=data['prepared_runs'])
    records = approved_records(projection)
    need(len(records) == 2, 'exactly two S0 identities required')
    need([r['planned_case_id'] for r in data['prepared_runs']] ==
         ['URV1_H75_P_dx5_a100000', 'URV1_H75_T_dx5_a100000'], 'S0 P then T only')
    need([r['run_id'] for r in data['prepared_runs']] ==
         ['URV_S0_P_A1_20261102_01', 'URV_S0_T_A1_20261102_01'], 'reserved identities changed')
    for r in data['prepared_runs']:
        run = Path(r['output_directory'])
        need(run == CASE / 'runs' / r['run_id'] / 'steady', 'S0 output must use isolated exact directory')
        need({p.name for p in run.iterdir()} == {'run_config.txt', 'run_manifest.txt'},
             'run directory not pristine; refusing restart/overwrite')
        manifest = kv(run / 'run_manifest.txt')
        need(manifest['run_id'] == r['run_id'] and manifest['mode'] == 'steady', 'native manifest identity')
    need(data['resources'] == dict(processes=1, threads=1, cuboids=1, overlap=3,
         per_process_address_space_GiB=8, required_available_RAM_GiB=12,
         required_initial_free_disk_GiB=100, required_before_each_run_free_disk_GiB=8,
         solver_wall_cap_seconds_per_case=3600), 'resource contract changed')
    return data, resources(True)


def child_limits():
    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def native_process(command, run, env):
    started = time.monotonic(); timed_out = False
    with (run / 'run.log').open('x') as log:
        child = subprocess.Popen(command, cwd=CASE, stdout=log, stderr=subprocess.STDOUT,
            env=env, start_new_session=True, preexec_fn=child_limits)
        try:
            code = child.wait(timeout=3600)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL); child.wait()
            code = child.returncode
    return dict(independent_process_exit_code=code, timed_out=timed_out,
                elapsed_seconds=time.monotonic() - started)


def execute(release, expected_sha, data):
    # Public completed-result contract validation must pass before creating any
    # marker/log or invoking a native process. The prepared binding fails here.
    bound = binding(release, expected_sha)
    need(bound['approved_runs'] == bound['prepared_runs'] and
         bound['approved_run_ids'] == bound['prepared_run_ids'], 'launch identities differ from prepared binding')
    need(bound.get('launch_authorization', {}).get('user_explicitly_authorized') is True,
         'separate user launch authorization missing')
    need(bound['launch_authorization'].get('user_instruction_verbatim', '').strip(), 'authorization evidence missing')
    attempt = CASE / 'launch_attempts' / expected_sha
    attempt.mkdir(parents=True, exist_ok=False)  # one attempt; no automatic retry
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
               MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1', QT_QPA_PLATFORM='offscreen')
    for record in data['prepared_runs']:
        run = Path(record['output_directory'])
        available = resources(False); before = unchanged(bound['inputs_sha256'])
        process = native_process([bound['provenance']['native_binary'], record['run_config_path']], run, env)
        (run / 'exit_code.txt').write_text(str(process['independent_process_exit_code']) + '\n')
        capture_error = None
        if not process['timed_out'] and process['independent_process_exit_code'] == 0:
            try:
                finalize_capture(run, bound['provenance']['native_binary'])
            except Exception as error:
                capture_error = type(error).__name__ + ': ' + str(error)
                save(run / 'capture_finalization_failure.json', dict(error=capture_error, S0='HOLD'))
        after = {p: sha(p) for p in bound['inputs_sha256']}
        output = {}
        for p in run.rglob('*'):
            need(not p.is_symlink(), 'unexpected raw output symlink')
            if p.is_file():
                need(p.resolve().is_relative_to(run), 'raw output path escape')
                output[str(p.relative_to(run))] = sha(p)
        completion = dict(protocol_id='URV-v1', release_sha256=expected_sha,
            run_id=record['run_id'], planned_case_id=record['planned_case_id'],
            inputs_before_sha256=before, inputs_after_sha256=after,
            inputs_unchanged=after == before, output_sha256=output,
            resources_before=available, capture_finalization_error=capture_error, **process)
        save(run / 'completion.json', completion)
        need(not process['timed_out'] and process['independent_process_exit_code'] == 0,
             'native failure/timeout: stage stopped, no retry or next case')
        need(after == before, 'input drift: stage stopped')
        need(capture_error is None, 'lossless capture finalization failed: stage stopped')
        analysis = CASE / 'analysis_results' / record['run_id']
        log_path = attempt / (record['run_id'] + '_checker.log')
        with log_path.open('x') as log:
            checked = subprocess.run([sys.executable, '-B', str(CHECKER / 'analysis/check_mass_repair.py'),
                '--run', str(run), '--release', str(release), '--release-sha256', expected_sha,
                '--out', str(analysis)], stdout=log, stderr=subprocess.STDOUT,
                env=env, timeout=3600, preexec_fn=child_limits)
        need(checked.returncode == 0, 'original URV or supplementary checker stopped stage; inspect saved evidence')
        accepted = json.loads((analysis / 'mass_repair_review.json').read_text())
        need(accepted.get('RESULT_PASS') is True and accepted.get('URV_RESULT_PASS') is True and
             accepted.get('MASS_CAPTURE_INTEGRITY') is True and accepted.get('SAME_INPUT_REPLAY') is True and
             accepted.get('CORRECTED_LEDGER_UNCHANGED') is True and accepted.get('PHYSICAL_OUTPUT_GUARD') is True,
             'supplementary acceptance incomplete; no next case')
    save(attempt / 'S0_completed.json', dict(stage='S0_REGRESSION', solver_runs=2,
        next_stage_started=False, reference_qualified=False, model_comparison='NOT_EVALUATED'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', type=Path, required=True)
    ap.add_argument('--release-sha256', required=True)
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args()
    try:
        data, available = inspect(args.release.resolve(), args.release_sha256)
        if args.execute:
            execute(args.release.resolve(), args.release_sha256, data)
        else:
            print(json.dumps(dict(PREPARATION_BINDING_CHECK=True, solver_executed=False,
                simulation_authorized=data['simulation_authorized'], prepared_run_ids=data['prepared_run_ids'],
                resources_snapshot=available)))
        return 0
    except Exception as error:
        print(type(error).__name__ + ': ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
