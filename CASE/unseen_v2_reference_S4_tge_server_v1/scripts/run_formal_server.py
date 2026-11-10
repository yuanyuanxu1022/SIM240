"""Server formal runner. Read-only by default; one authorized run per release.

Purpose of the 1.25 nm rerun is BUILD EQUIVALENCE plus throughput/RSS measurement,
not a new stage acceptance.  Nothing here promotes scientific status.
"""
from pathlib import Path
import argparse, json, os, resource, shutil, signal, subprocess, sys, time

CASE = Path(__file__).resolve().parents[1]
CHECKER = CASE.parent / 'unseen_v2_reference_checker_S4_tge_server_v1'
sys.path.insert(0, str(CHECKER / 'analysis'))

import server_stage as s  # noqa: E402
from evidence import need, sha, kv  # noqa: E402

TIME_BIN = Path('/usr/bin/time')


def save(path, value):
    path = Path(path)
    need(not path.exists(), 'refusing receipt overwrite: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write('\n')


def resources(initial, bound):
    res = bound['formal_resources']
    mem = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                   if line.startswith('MemAvailable:'))) * 1024
    disk = shutil.disk_usage(CASE).free
    need(mem >= res['required_available_RAM_GiB'] * 1024**3,
         'available memory below adopted %d GiB formal limit' % res['required_available_RAM_GiB'])
    need(disk >= (res['required_initial_free_disk_GiB'] if initial
                  else res['required_before_each_run_free_disk_GiB']) * 1024**3,
         'free disk below adopted formal limit')
    return dict(MemAvailable_bytes=mem, disk_free_bytes=disk)


def limits(bound):
    cap = bound['formal_resources']['per_process_address_space_GiB'] * 1024**3
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def stop(child):
    if child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()


def peak_rss(log):
    try:
        for line in reversed(Path(log).read_text(errors='replace').splitlines()):
            if 'Maximum resident set size' in line:
                return int(line.rsplit(':', 1)[1].strip()) * 1024
    except OSError:
        pass
    return None


def bounded(command, log, env, output, bound):
    res = bound['formal_resources']
    cap = res['solver_wall_cap_seconds']
    budget = res['output_budget_GiB_per_run'] * 1024**3
    floor = res['required_before_each_run_free_disk_GiB'] * 1024**3
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
                solver_wall_cap_seconds=cap,
                peak_rss_bytes=peak_rss(log))


def output_hashes(run):
    out = {}
    for p in run.rglob('*'):
        need(not p.is_symlink(), 'raw output symlink refused')
        if p.is_file():
            need(p.resolve().is_relative_to(run), 'raw output escape')
            out[str(p.relative_to(run))] = sha(p)
    return out


def validate_approved_identities(bound):
    """The approved set must be a non-empty, duplicate-free subset of the sealed plan."""
    approved = bound.get('approved_runs')
    need(isinstance(approved, list) and approved, 'explicit approved formal runs required')
    need(all(r in bound['prepared_runs'] for r in approved),
         'approved formal runs must be part of the sealed plan')
    need(len({r['run_id'] for r in approved}) == len(approved), 'duplicate approved run identity')
    need(bound.get('approved_run_ids') == [r['run_id'] for r in approved],
         'approved_run_ids must match the approved runs exactly')
    return approved


def validate_formal_authority(bound):
    need(bound.get('kind') == 'AUTHORIZED_S4_TGE_SERVER_FORMAL_RELEASE',
         'separate formal release required')
    need(bound.get('formal_simulation_authorized') is True
         and bound.get('simulation_authorized') is True, 'formal run not authorized')
    need(bound.get('native_zero_step_authorized') is False
         and bound.get('initial_field_readback_authorized') is False,
         'zero-step authority must be off in a formal release')
    need(bound.get('S5_authorized') is False and bound.get('automatic_retry_authorized') is False
         and bound.get('automatic_extension_authorized') is False, 'retry/extension/S5 must stay off')
    validate_approved_identities(bound)
    need(bound.get('actual_run_ids') == [], 'release must not pre-claim execution')
    need(bound.get('AI_may_start_solver') is False and bound.get('user_manually_starts') is True,
         'manual execution boundary changed')
    need(bound.get('original_S4_stage_accepted') is False and bound.get('reference_qualified') is False
         and bound.get('NUMERICAL_GATE') == 'NOT_EVALUATED' and bound.get('RESULT_PASS') is False
         and bound.get('geometry_PASS') is None, 'release promotes unexecuted status')

    auth = bound.get('formal_authorization') or {}
    path = s.covered(bound, auth.get('path', ''))
    need(path == CASE / 'evidence/S4_TGE_SERVER_formal_authorization_v1_20261104_01.json'
         and sha(path) == auth.get('sha256'), 'wrong authorization evidence')
    value = s.load(path)
    need(value.get('user_explicitly_authorized') is True
         and value.get('formal_simulation_authorized') is True
         and isinstance(value.get('user_instruction_verbatim'), str)
         and value['user_instruction_verbatim'].strip(), 'actual formal authorization missing')
    need(value.get('approved_run_ids') == bound['approved_run_ids'],
         'authorization does not cover exactly these run ids')

    decision = bound.get('formal_resource_decision') or {}
    dpath = s.covered(bound, decision.get('path', ''))
    need(dpath == CASE / 'evidence/S4_TGE_SERVER_formal_resource_decision_v1_20261104_01.json'
         and sha(dpath) == decision.get('sha256'), 'wrong formal resource evidence')
    dvalue = s.load(dpath)
    need(dvalue.get('resource_decision_accepted') is True
         and dvalue.get('resources') == bound['formal_resources'],
         'formal resource decision not adopted or mismatched')


def verify_release(path, digest):
    path = s.canonical(path)
    need(path.parent == CASE / 'evidence' and sha(path) == digest,
         'external seal trust anchor/path mismatch')
    bound = s.load(path)
    need(bound.get('protocol_id') == 'URV-v1'
         and bound.get('schema_version') == 'S4-TGE-SERVER-1', 'wrong release schema')
    s.unchanged(bound)
    need(all(bound['inputs_sha256'].get(k) == v
             for k, v in s.load(CASE / 'evidence/preparation_S.json')['inputs_sha256'].items()),
         'formal release drops preparation inputs')
    prep = s.load(s.covered(bound, CASE / 'evidence/preparation_S.json'))
    need(bound.get('preparation_S_sha256') == sha(CASE / 'evidence/preparation_S.json'),
         'preparation seal not bound')
    need(bound['prepared_runs'] == prep['prepared_runs'], 'release changes prepared identities')
    need(bound.get('source_binary_sha256') == s.load(
        CASE / 'evidence/build_environment.json')['binary_sha256'], 'wrong source binary')
    need(bound.get('lineage') == prep['lineage'], 'release changes the lineage criterion')
    return bound


def execute(path, digest, bound):
    validate_formal_authority(bound)
    need(verify_release(path, digest) == bound, 'inspection/release mismatch')
    s.require_pristine(bound)
    resources(True, bound)
    attempt = CASE / 'launch_attempts' / digest
    attempt.mkdir(parents=True, exist_ok=False)

    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               NUMEXPR_NUM_THREADS='1', QT_QPA_PLATFORM='offscreen', PYTHONDONTWRITEBYTECODE='1')
    env.pop('LD_LIBRARY_PATH', None)
    env.pop('LD_PRELOAD', None)

    for rec in bound['approved_runs']:
        run = Path(rec['output_directory'])
        s.require_pristine(dict(prepared_runs=[rec], zero_prepared_runs=[]))
        available = resources(False, bound)
        before = dict(bound['inputs_sha256'])
        binary = bound['provenance']['native_binary']
        need(sha(binary) == bound['source_binary_sha256'], 'native binary changed')
        command = [binary, rec['run_config_path']]
        if TIME_BIN.is_file():
            command = [str(TIME_BIN), '-v', '--'] + command
        process = bounded(command, run / 'run.log', env, run, bound)
        (run / 'exit_code.txt').write_text(str(process['independent_process_exit_code']) + '\n')
        after = {k: sha(s.resolve_key(bound, k)) for k in bound['inputs_sha256']}
        output = output_hashes(run)
        save(run / 'completion.json', dict(
            protocol_id='URV-v1', release_sha256=digest, run_id=rec['run_id'],
            planned_case_id=rec['planned_case_id'],
            inputs_before_sha256=before, inputs_after_sha256=after,
            inputs_unchanged=before == after, output_sha256=output,
            resources_before=available, density_capture='NOT_APPLICABLE_S0_ONLY', **process))
        need(process['independent_process_exit_code'] == 0 and not process['timed_out']
             and process['resource_stop_reason'] is None, 'native failure/resource stop; no retry')
        need(after == before, 'input drift; stopped')
        need(sum((run / p).stat().st_size for p in output)
             <= bound['formal_resources']['output_budget_GiB_per_run'] * 1024**3,
             'output budget exceeded')

        analysis = CASE / 'analysis_results' / rec['run_id']
        with (attempt / (rec['run_id'] + '_checker.log')).open('x') as log:
            checked = subprocess.run(
                [sys.executable, '-B', str(CHECKER / 'analysis/check_formal_server.py'),
                 '--release', str(path), '--release-sha256', digest, '--run', str(run),
                 '--out', str(analysis)],
                stdout=log, stderr=subprocess.STDOUT, env=env,
                timeout=bound['formal_resources']['checker_wall_cap_seconds'],
                preexec_fn=lambda: limits(bound))
        need(checked.returncode == 0, 'independent checker failed; no next run')
        accepted = s.load(analysis / 'acceptance.json')
        need(accepted.get('BUILD_EQUIVALENCE_PASS') is True,
             'build equivalence failed; the two builds are not interchangeable')

    need(sha(path) == digest, 'release changed during the run')
    s.unchanged(bound)
    save(attempt / 'formal_run_record.json', dict(
        release_sha256=digest, runs=bound['approved_run_ids'],
        BUILD_EQUIVALENCE_PASS=True, S5_started=False, next_stage_started=False,
        original_S4_stage_accepted=False, reference_qualified=False,
        NUMERICAL_GATE='NOT_EVALUATED', RESULT_PASS=False, geometry_PASS=None))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', type=Path, required=True)
    ap.add_argument('--release-sha256', required=True)
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args()
    try:
        path = args.release.resolve()
        bound = verify_release(path, args.release_sha256)
        # Check the whole formal authority up front, so a defective release is
        # rejected before the user starts anything, not only at --execute time.
        validate_formal_authority(bound)
        s.require_pristine(bound)
        if args.execute:
            execute(path, args.release_sha256, bound)
        else:
            print(json.dumps(dict(binding_check=True, solver_executed=False,
                                  formal_simulation_authorized=bound['formal_simulation_authorized'],
                                  approved_run_ids=bound['approved_run_ids'],
                                  resources=bound['formal_resources']), indent=2))
        code = 0
    except Exception as error:
        print(type(error).__name__ + ': ' + str(error), file=sys.stderr)
        code = 2
    raise SystemExit(code)
