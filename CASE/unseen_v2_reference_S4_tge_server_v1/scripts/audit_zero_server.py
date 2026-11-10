"""Server zero-step controller: 3 native modes + one field read, only after a new authority.

Default (no --execute) is read-only and prints the static binding summary.
"""
from pathlib import Path
import argparse, json, os, resource, shutil, signal, subprocess, sys, time

CASE = Path(__file__).resolve().parents[1]
CHECKER = CASE.parent / 'unseen_v2_reference_checker_S4_tge_server_v1'
sys.path.insert(0, str(CHECKER / 'analysis'))

import server_stage as s  # noqa: E402
from evidence import need, sha, kv  # noqa: E402
from check_zero_server import validate_completed_zero  # noqa: E402
from zero_evidence_server import validate_zero_outputs, validate_initial_readback  # noqa: E402

TIME_BIN = Path('/usr/bin/time')


def save(path, value):
    path = Path(path)
    need(not path.exists(), 'refusing receipt overwrite: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write('\n')


def resources(initial, bound):
    res = bound['zero_resource_proposal']
    mem = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                   if line.startswith('MemAvailable:'))) * 1024
    free = shutil.disk_usage(CASE).free
    need(mem >= res['required_available_RAM_GiB'] * 1024**3,
         'available memory below adopted %d GiB zero limit' % res['required_available_RAM_GiB'])
    need(free >= (res['required_initial_free_disk_GiB'] if initial
                  else res['required_before_each_call_free_disk_GiB']) * 1024**3,
         'free disk below adopted zero limit')
    return dict(MemAvailable_bytes=mem, disk_free_bytes=free)


def limits(bound):
    cap = bound['zero_resource_proposal']['per_process_address_space_GiB'] * 1024**3
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def stop(child):
    if child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()


def peak_rss(log):
    """GNU time writes its summary to stderr, which is part of the captured log."""
    try:
        for line in reversed(Path(log).read_text(errors='replace').splitlines()):
            if 'Maximum resident set size' in line:
                return int(line.rsplit(':', 1)[1].strip()) * 1024
    except OSError:
        pass
    return None


def bounded_process(command, log, env, output, bound, cap_key):
    cap = bound['zero_resource_proposal'][cap_key]
    budget = bound['zero_resource_proposal']['output_budget_GiB_per_call'] * 1024**3
    floor = bound['zero_resource_proposal']['required_before_each_call_free_disk_GiB'] * 1024**3
    started = time.monotonic()
    reason = None
    with log.open('x') as stream:
        child = subprocess.Popen(command, cwd=CASE, stdout=stream, stderr=subprocess.STDOUT,
                                 env=env, start_new_session=True,
                                 preexec_fn=lambda: limits(bound))
        try:
            while child.poll() is None:
                remaining = cap - (time.monotonic() - started)
                if remaining <= 0:
                    reason = 'wall_timeout'
                    break
                try:
                    child.wait(timeout=min(5.0, remaining))
                except subprocess.TimeoutExpired:
                    pass
                size = sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
                if size > budget:
                    reason = 'output_budget_exceeded'
                    break
                if shutil.disk_usage(CASE).free < floor:
                    reason = 'free_disk_below_limit'
                    break
        finally:
            stop(child)
        code = child.wait()
    return dict(independent_process_exit_code=code,
                timed_out=reason == 'wall_timeout',
                resource_stop_reason=reason,
                elapsed_seconds=time.monotonic() - started,
                wall_cap_seconds=cap,
                peak_rss_bytes=peak_rss(log))


def execute(path, digest, bound):
    s.validate_zero_authority(bound, path)
    current = s.verify_seal(path, digest)
    need(current == bound, 'inspection/release mismatch')
    s.require_pristine(bound)
    resources(True, bound)
    attempt = CASE / 'audit_attempts' / digest
    attempt.mkdir(parents=True, exist_ok=False)
    folder = CASE / 'audits' / s.AUDIT_ID
    need(not (folder / 'verification.json').exists(), 'zero receipt exists; no retry')

    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               QT_QPA_PLATFORM='offscreen', PYTHONDONTWRITEBYTECODE='1')
    env.pop('LD_LIBRARY_PATH', None)
    env.pop('LD_PRELOAD', None)

    records = []
    for rec in bound['zero_prepared_runs']:
        need(sha(path) == digest, 'release changed')
        s.validate_zero_authority(bound, path)
        s.unchanged(bound)
        available = resources(False, bound)
        need(rec['mode'] in s.MODES and kv(rec['run_config_path'])['mode'] == rec['mode'],
             'zero forbids steady mode')
        binary = bound['provenance']['native_binary']
        need(sha(binary) == s.load(CASE / 'evidence/build_environment.json')['binary_sha256'],
             'native binary changed')
        run = Path(rec['output_directory'])
        command = [binary, rec['run_config_path']]
        if TIME_BIN.is_file():
            command = [str(TIME_BIN), '-v', '--'] + command
        result = bounded_process(command, run / 'run.log', env, run, bound, 'native_call_cap_seconds')
        (run / 'exit_code.txt').write_text(str(result['independent_process_exit_code']) + '\n')
        save(run / 'process_receipt.json', result)
        need(result['independent_process_exit_code'] == 0 and not result['timed_out']
             and result['resource_stop_reason'] is None,
             'zero failed; no retry/next call')
        geo = validate_zero_outputs(rec)
        receipt = dict(run_id=rec['run_id'], planned_case_id=s.CASE_0P625, mode=rec['mode'],
                       output=str(run), native_exit_code=0, collide_and_stream_calls=0,
                       geometry=geo, resources_before=available,
                       elapsed_seconds=result['elapsed_seconds'],
                       peak_rss_bytes=result['peak_rss_bytes'])
        if rec['mode'] == 'initialize':
            report = folder / ('field_readback_' + s.CASE_0P625 + '.json')
            log = folder / ('field_reader_' + s.CASE_0P625 + '.log')
            reader = Path(bound['reader_path'])
            need(bound['inputs_sha256'].get(s.key_for(reader)) == sha(reader), 'reader unbound')
            libdir = '/usr/lib/python3/dist-packages'
            cmd = ['/usr/bin/pvpython', '--force-offscreen-rendering', '-B', str(reader),
                   '--run', str(run), '--out', str(report)]
            env_reader = dict(env, PYTHONPATH=libdir)
            proc = bounded_process(cmd, log, env_reader, folder, bound, 'field_reader_cap_seconds')
            save(report.with_suffix('.process.json'), dict(
                independent_exit_code=proc['independent_process_exit_code'],
                timed_out=proc['timed_out'], resource_stop_reason=proc['resource_stop_reason'],
                elapsed_seconds=proc['elapsed_seconds'], peak_rss_bytes=proc['peak_rss_bytes'],
                pythonpath=libdir))
            need(proc['independent_process_exit_code'] == 0 and not proc['timed_out']
                 and proc['resource_stop_reason'] is None, 'field reader failed; stop')
            validate_initial_readback(rec, report, folder)
            receipt.update(field_readback=str(report), field_readback_sha256=sha(report))
        need(sha(path) == digest, 'release changed')
        s.unchanged(bound)
        records.append(receipt)
        save(folder / 'progress' / ('%02d.json' % len(records)), receipt)
        print(json.dumps(dict(mode=rec['mode'], native_exit=0, actual_time_steps=0,
                              peak_rss_bytes=result['peak_rss_bytes'])), flush=True)

    raw = {str(p): sha(p) for p in folder.rglob('*') if p.is_file()}
    manifest = folder / 'audit_files_sha256.json'
    save(manifest, raw)
    save(folder / 'verification.json', dict(
        audit_id=s.AUDIT_ID, ZERO_STEP_AUDIT_PASS=True,
        binary_sha256=s.load(CASE / 'evidence/build_environment.json')['binary_sha256'],
        native_describe=1, native_precheck=1, native_initialize=1,
        initialized_frames_read=1, actual_time_steps=0, steady_mode_invocations=0,
        records=records, raw_manifest_path=str(manifest), raw_manifest_sha256=sha(manifest),
        preparation_S_sha256=bound['preparation_S_sha256'],
        audit_release_path=str(path), audit_release_sha256=digest,
        density_capture='NOT_APPLICABLE_S0_ONLY',
        formal_simulation_started=False, NUMERICAL_GATE='NOT_EVALUATED',
        RESULT_PASS=False, reference_qualified=False, next_stage_started=False))
    validate_completed_zero(bound, path)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', type=Path, required=True)
    ap.add_argument('--release-sha256', required=True)
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args()
    try:
        path = args.release.resolve()
        bound = s.verify_seal(path, args.release_sha256)
        s.require_pristine(bound)
        if args.execute:
            execute(path, args.release_sha256, bound)
        else:
            print(json.dumps(s.static_summary(bound), indent=2))
        code = 0
    except Exception as error:
        print(type(error).__name__ + ': ' + str(error), file=sys.stderr)
        code = 2
    raise SystemExit(code)
