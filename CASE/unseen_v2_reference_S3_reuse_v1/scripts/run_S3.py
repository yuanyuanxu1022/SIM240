"""Read-only by default. Four formal S3 runs require their own launch release."""
from pathlib import Path
import argparse
import json
import os
import resource
import shutil
import signal
import subprocess
import sys
import time

CASE = Path(__file__).resolve().parents[1]
CHECKER = CASE.parent / 'unseen_v2_reference_checker_S3_reuse_v1'
sys.path.insert(0, str(CHECKER / 'analysis'))
from evidence import need, sha, save, kv
from stage_s3 import (verify_seal, require_pristine, validate_formal_authority,
                      unchanged, RESOURCES, validate_zero_plan)
from check_results import binding


def resources(initial):
    mem = next(int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()
               if line.startswith('MemAvailable:'))
    disk = shutil.disk_usage(CASE).free
    need(mem >= 12*1024**3, 'available RAM below frozen 12 GiB')
    need(disk >= (100 if initial else 8)*1024**3, 'free disk below frozen requirement')
    return dict(MemAvailable_bytes=mem, disk_free_bytes=disk)


def child_limits():
    resource.setrlimit(resource.RLIMIT_AS, (8*1024**3, 8*1024**3))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def process_environment():
    return dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
                NUMEXPR_NUM_THREADS='1', QT_QPA_PLATFORM='offscreen', PYTHONDONTWRITEBYTECODE='1')


def inspect(release, expected_sha):
    data = verify_seal(release, expected_sha)
    require_pristine(data['prepared_runs'])
    validate_zero_plan(data)
    return data, resources(True)


def wall_cap(config):
    dx = float(kv(config)['dx_nm'])
    need(dx == 2.5, 'S3 requires original 2.5 nm grid')
    return RESOURCES['solver_wall_cap_seconds_by_dx_nm'][str(int(dx)) if dx == 5 else str(dx)]


def stop(child):
    if child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()


def native_process(command, run, env, cap):
    """Enforce the frozen per-grid wall cap and observe aggregate output budget."""
    started = time.monotonic(); reason = None
    with (run / 'run.log').open('x') as log:
        child = subprocess.Popen(command, cwd=CASE, stdout=log, stderr=subprocess.STDOUT,
            env=env, start_new_session=True, preexec_fn=child_limits)
        try:
            while child.poll() is None:
                remaining = cap - (time.monotonic() - started)
                if remaining <= 0:
                    reason = 'wall_timeout'; break
                try:
                    child.wait(timeout=min(5., remaining))
                except subprocess.TimeoutExpired:
                    pass
                size = sum(p.stat().st_size for p in run.rglob('*') if p.is_file())
                if size > 4*1024**3:
                    reason = 'output_budget_exceeded'; break
                if shutil.disk_usage(CASE).free < 8*1024**3:
                    reason = 'free_disk_below_limit'; break
        finally:
            stop(child)
        code = child.wait()
    return dict(independent_process_exit_code=code, timed_out=reason == 'wall_timeout',
                resource_stop_reason=reason, elapsed_seconds=time.monotonic()-started,
                solver_wall_cap_seconds=cap)


def output_hashes(run):
    output = {}
    for p in run.rglob('*'):
        need(not p.is_symlink(), 'raw output symlink refused')
        if p.is_file():
            need(p.resolve().is_relative_to(run), 'raw output escape')
            output[str(p.relative_to(run))] = sha(p)
    return output


def execute(release, expected_sha, data):
    bound = binding(release, expected_sha)
    validate_formal_authority(bound)
    # Never trust a caller-supplied inspection object after validating the release.
    need(data == bound, 'inspection/release mismatch')
    require_pristine(bound['prepared_runs'])
    attempt = CASE / 'launch_attempts' / expected_sha
    attempt.mkdir(parents=True, exist_ok=False)
    env = process_environment()
    accepted_points = {}
    for record in bound['prepared_runs']:
        run = Path(record['output_directory'])
        require_pristine([record])
        available = resources(False); before = unchanged(bound['inputs_sha256'])
        process = native_process([bound['provenance']['native_binary'], record['run_config_path']],
                                 run, env, wall_cap(record['run_config_path']))
        (run / 'exit_code.txt').write_text(str(process['independent_process_exit_code'])+'\n')
        after = {p: sha(p) for p in bound['inputs_sha256']}
        output = output_hashes(run)
        completion = dict(protocol_id='URV-v1', release_sha256=expected_sha,
            run_id=record['run_id'], planned_case_id=record['planned_case_id'],
            inputs_before_sha256=before, inputs_after_sha256=after, inputs_unchanged=before == after,
            output_sha256=output, resources_before=available, density_capture='NOT_APPLICABLE_S0_ONLY', **process)
        save(run / 'completion.json', completion)
        need(not process['timed_out'] and process['independent_process_exit_code'] == 0 and
             not process.get('resource_stop_reason'), 'native failure/resource stop; no retry or next case')
        need(after == before, 'input drift; stage stopped')
        need(sum((run/p).stat().st_size for p in output) <= 4*1024**3, 'output budget exceeded')
        analysis = CASE / 'analysis_results' / record['run_id']
        with (attempt / (record['run_id']+'_checker.log')).open('x') as log:
            checked = subprocess.run([sys.executable, '-B', str(CHECKER/'analysis/check_results.py'),
                '--run', str(run), '--release', str(release), '--release-sha256', expected_sha,
                '--out', str(analysis)], stdout=log, stderr=subprocess.STDOUT,
                env=env, timeout=3600, preexec_fn=child_limits)
        need(checked.returncode == 0, 'independent checker failed; no next case')
        accepted = json.loads((analysis / 'acceptance.json').read_text())
        need(accepted.get('RESULT_PASS') is True and accepted.get('NUMERICAL_GATE') == 'PASS' and
             accepted.get('geometry_PASS') is True, 'S3 numerical/geometry acceptance failed')
        accepted_points[record['run_id']] = accepted
        from s3_baselines import control_for_direction
        direction = accepted['direction']
        same_direction = [r for r in bound['prepared_runs'] if kv(r['run_config_path'])['direction'] == direction]
        if all(r['run_id'] in accepted_points for r in same_direction):
            report = control_for_direction(bound, direction, accepted_points, expected_sha)
            save(attempt / ('linearity_'+direction+'.json'), report)
            need(report['CONTROL_PASS'] is True, 'S3 linearity failed; no retry or next case')
    save(attempt / 'S3_completed.json', dict(stage='S3_REG_LINEARITY', solver_runs=4, S3_CONTROL_PASS=True,
        next_stage_started=False, reference_qualified=False, MODEL_COMPARISON='NOT_EVALUATED'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', type=Path, required=True)
    ap.add_argument('--release-sha256', required=True)
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args()
    try:
        path = args.release.resolve()
        data, available = inspect(path, args.release_sha256)
        if args.execute:
            execute(path, args.release_sha256, data)
        else:
            print(json.dumps(dict(PREPARATION_BINDING_CHECK=True, solver_executed=False,
                simulation_authorized=data['simulation_authorized'], prepared_run_ids=data['prepared_run_ids'],
                zero_audit_status=data.get('zero_audit_status'), resources_snapshot=available)))
        return 0
    except Exception as error:
        print(type(error).__name__+': '+str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
