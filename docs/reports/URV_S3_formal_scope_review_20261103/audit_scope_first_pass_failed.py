"""Read-only formal S3 scope/resource review. No solver, reader, build or release grant."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
import ast
import contextlib
import io
import json
import os
import subprocess
import sys

ROOT = Path('/home/dell/yuanyuanxu/SIM240')
OUT = Path(__file__).resolve().parent
CASE = ROOT / 'CASE/unseen_v2_reference_S3_reuse_v1_1'
CHECK = ROOT / 'CASE/unseen_v2_reference_checker_S3_reuse_v1_1'
B = CASE / 'evidence/preparation_B.json'
B_SHA = 'a5b69ec95180bf92327a3bba1311639dd2a5fb1bec412cd80c3869dda2a47f92'
sys.path[:0] = [str(CHECK / 'analysis'), str(CASE / 'scripts')]
from evidence import need, sha, kv, exact_parameters, EvidenceError
import stage_s3 as stage
import run_S3 as runner
from s3_baselines import verify_baselines


def load(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def subprocess_timeouts(path):
    tree = ast.parse(Path(path).read_text())
    return [dict(line=node.lineno, timeout=kw.value.value)
            for node in ast.walk(tree) if isinstance(node, ast.Call) and
            isinstance(node.func, ast.Attribute) and node.func.attr == 'run' and
            isinstance(node.func.value, ast.Name) and node.func.value.id == 'subprocess'
            for kw in node.keywords if kw.arg == 'timeout' and isinstance(kw.value, ast.Constant)]


def main():
    for name in ['SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md']:
        with (OUT / ('before_' + name)).open('xb') as stream:
            stream.write((ROOT / 'docs/reports' / name).read_bytes())
    data = stage.verify_seal(B, B_SHA)
    need(B.with_suffix('.sha256').read_text().strip() == B_SHA, 'B sidecar drift')
    need(len(data['inputs_sha256']) == 2609, 'B input count changed')
    stage.require_pristine(data['prepared_runs'])
    need(not (CASE / 'launch_attempts').exists() and not (CASE / 'analysis_results').exists(), 'formal already attempted')
    need(not any(CASE.joinpath('evidence').glob('S3_formal_launch*')), 'formal binding already exists; review scope differs')
    previous = ROOT / 'docs/reports/URV_S3_zero_results_review_v1_1_20261103'
    protected = dict(data['inputs_sha256'])
    for directory in (CASE, CHECK, previous):
        for p in directory.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                protected[str(p)] = sha(p)
    save(OUT / 'protected_inputs_before.json', protected)
    for relative, digest in load(previous / 'report_manifest.json').items():
        need(sha(previous / relative) == digest, 'independent review report drift')
    acceptance = load(data['independent_zero_review_path'])
    need(sha(data['independent_zero_review_path']) == data['independent_zero_review_sha256'] and
         acceptance['ZERO_STEP_INDEPENDENT_REVIEW_PASS'] and acceptance['ZERO_STEP_GEOMETRY_PASS'], 'independent zero review not bound/passed')
    with patch('subprocess.Popen', side_effect=AssertionError('no process in binding review')) as process:
        stage.verify_zero_receipt(data)
        baselines = verify_baselines(data)
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, 'argv', ['run_S3.py', '--release', str(B), '--release-sha256', B_SHA]), \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = runner.main()
        need(code == 0 and not process.called, 'readonly B controller failed or invoked process')
        refusals = {}
        for name, validator in [('formal', stage.validate_formal_authority), ('zero', stage.validate_zero_authority)]:
            try:
                validator(data)
            except EvidenceError as error:
                refusals[name] = str(error)
            else:
                raise AssertionError('B grants execution permission')

    configurations = []
    for index, record in enumerate(data['prepared_runs'], 1):
        cfg = kv(record['run_config_path'])
        p = exact_parameters(cfg)
        baseline = next(r for r in data['baseline_references'] if r['direction'] == cfg['direction'])
        middle = kv(baseline['config_path'])
        keys = set(cfg) - {'run_id', 'output_directory', 'acceleration_m_s2'}
        need({k: cfg[k] for k in keys} == {k: middle[k] for k in keys}, 'S3 differs from S2 beyond permitted force/identity')
        cap = runner.wall_cap(record['run_config_path'])
        need(cap == 14400 and p['window'] == 2592 and p['cap'] == 150528 and p['nodes'] == 368640, 'frozen grid/time/budget changed')
        configurations.append(dict(order=index, **record, direction=cfg['direction'],
            acceleration_m_s2=p['a'], dx_nm=float(cfg['dx_nm']), exact_parameters=p,
            mode=cfg['mode'], solver_wall_cap_seconds=cap, checker_outer_cap_seconds=3600,
            run_directory_pristine=True, baseline_run_id=baseline['run_id'],
            control_after_acceptance=cfg['direction'] if index in (3, 4) else None))
    baseline_data = []
    for ref in data['baseline_references']:
        completion = load(ref['completion_path'])
        accepted = load(ref['acceptance_path'])
        run = Path(ref['completion_path']).parent
        baseline_data.append(dict(direction=ref['direction'], run_id=ref['run_id'], K_m3=baselines[ref['direction']],
            original_release_sha256=ref['release_sha256'], completion_path=ref['completion_path'],
            original_solver_elapsed_seconds=completion['elapsed_seconds'],
            original_diagnostic_rows=accepted['scalar']['diagnostic_rows'],
            original_output_bytes=sum((run / p).stat().st_size for p in completion['output_sha256']),
            original_output_files=len(completion['output_sha256']), rerun_required=False,
            authority_transferred_to_S3=False))
    clean = dict(os.environ)
    clean.pop('LD_LIBRARY_PATH', None)
    clean.pop('LD_PRELOAD', None)
    link = subprocess.run(['/usr/bin/ldd', data['provenance']['native_binary']], env=clean,
                          capture_output=True, text=True, timeout=30, check=True)
    (OUT / 'clean_environment_ldd.txt').write_text(link.stdout)
    paths = {str(Path(word).resolve()) for line in link.stdout.splitlines() for word in line.split() if word.startswith('/')}
    build = load(data['provenance']['build_environment'])
    need(paths == set(build['dynamic_library_sha256']) and
         all(sha(p) == h for p, h in build['dynamic_library_sha256'].items()), 'loader/library drift')
    processes = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            argv = (proc / 'cmdline').read_bytes().decode(errors='replace').strip('\0').split('\0')
            if argv and (Path(argv[0]).name == 'urv_reference' or
                any(Path(arg).name in ('run_S3.py', 'audit_S3_zero.py') for arg in argv[1:])):
                processes.append(dict(pid=int(proc.name), argv=argv))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            pass
    panes = subprocess.run(['/usr/bin/tmux', 'list-panes', '-a', '-F', '#{session_name}|#{pane_pid}|#{pane_current_command}'],
                           env=clean, capture_output=True, text=True, timeout=10)
    need(panes.returncode in (0, 1), 'tmux snapshot failed')
    resource_snapshot = dict(checked_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        **runner.resources(True), dynamic_libraries_verified=len(paths),
        relevant_processes=processes, tmux_panes=panes.stdout.splitlines(),
        tmux_query_exit_code=panes.returncode, tmux_query_stderr=panes.stderr,
        interpretation='Current snapshot only; repeat prebinding and at actual launch. No resource reservation.')
    need(not processes, 'existing native or S3 process requires review before any future binding')
    checker_caps = subprocess_timeouts(CHECK / 'analysis/check_results.py')
    controller_caps = subprocess_timeouts(CASE / 'scripts/run_S3.py')
    need([r['timeout'] for r in checker_caps] == [3600] and
         [r['timeout'] for r in controller_caps] == [3600], 'checker timeout implementation changed')
    save(OUT / 'configurations.json', configurations)
    save(OUT / 'S2_baseline_references.json', baseline_data)
    save(OUT / 'resources.json', dict(frozen_resources=data['resources'], current_snapshot=resource_snapshot,
        total_solver_cap_seconds=57600, total_checker_wait_cap_seconds=14400,
        total_is_not_batch_hard_wall_limit=True, new_performance_advance_required=False,
        performance_decision_basis='Same mid-grid/geometry/ELF has completed S2 evidence; S3 four configurations passed zero audit.',
        inherited_outer_checker_timeout=controller_caps, inherited_reader_timeout=checker_caps,
        timeout_scope='Outer check process wait is bounded; no claim of whole process-tree cleanup or strict 20 h batch cap.'))
    save(OUT / 'formal_binding_plan.json', dict(
        kind='NON_EXECUTABLE_RELEASE_PLAN_NOT_AUTHORIZATION', protocol_id='S3-FRD-v1',
        stage=stage.STAGE, addendum_id=stage.REVISION, preparation_B_path=str(B), preparation_B_sha256=B_SHA,
        planned_run_ids=[r['run_id'] for r in configurations], planned_runs=configurations,
        simulation_authorized=False, formal_simulation_authorized=False, native_zero_step_authorized=False,
        performance_time_stepping_authorized=False, approved_runs=[], approved_run_ids=[], approved_audit_run_ids=[],
        AI_may_start_solver=False, user_manually_starts=True,
        expected_future_release_kind='AUTHORIZED_EXECUTION_LAUNCH_RELEASE',
        minimum_future_added_immutable_inputs=[str(B), str(B.with_suffix('.sha256')), 'actual scoped formal authorization evidence'],
        future_release_must_retain_all_B_inputs=True, completed_zero_authority_not_transferred=True,
        new_formal_authorization_required=True, authorization_must_cover_automatic_sequential_progress=True,
        checker_including_saved_field_readback_in_scope=True,
        raw_log_must_be_new_and_not_bound_input=True, automatic_retry_authorized=False,
        automatic_extension_authorized=False, S4_authorized=False, S5_authorized=False,
        future_binding_verifications=['B SHA/input closure, raw zero receipt and independent review',
            'same four identities/configuration paths and pristine output directories',
            'source/binary/build/library provenance and S2 baseline own-release evidence',
            'real scoped user answer retained with complete question',
            'resources, process/session absence and unused release/log/attempt paths',
            'actual formal authority validator, fixed external SHA and readonly controller inspection'],
        future_verification_must_not_execute_solver=True, execution_command_generated=False))
    need(all(sha(p) == h for p, h in protected.items()), 'protected data changed during review')
    save(OUT / 'verification.json', dict(reviewed_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        scope_protocol='S3-FRD-v1', scope_review='COMPATIBLE_PENDING_EXPLICIT_FORMAL_AUTHORIZATION_AND_FRESH_BINDING_CHECKS',
        preparation_B_sha256=B_SHA, B_inputs_verified=2609, protected_files_unchanged=len(protected),
        predecessor_report_manifest_verified=True, frozen_zero_receipt_rechecked=True,
        independent_zero_review_bound=True, S2_baselines_verified=True, formal_configurations_verified=4,
        all_formal_directories_pristine=True, readonly_controller_exit_code=code,
        readonly_controller_output=json.loads(stdout.getvalue()), closed_B_authority_refusals=refusals,
        loader_libraries_verified=15, current_resources=resource_snapshot,
        formal_authorization_received=False, formal_release_created=False, execution_command_created=False,
        CASE_writes=0, source_or_config_changes=0, builds=0, native_solver_calls=0,
        VTK_reader_invocations=0, time_steps=0, software_tests_rerun=False,
        S3_CONTROL_PASS='NOT_EVALUATED', NUMERICAL_GATE='NOT_EVALUATED', geometry_PASS=None, RESULT_PASS=False,
        reference_qualified=False, MODEL_COMPARISON='NOT_EVALUATED', physical_validation='NOT_EVALUATED',
        submission_ready=False, next_stage_started=False))
    print(json.dumps(dict(B_inputs_verified=2609, protected_files=len(protected), formal_configs=4,
        snapshot=resource_snapshot, formal_authorization=False, no_execution=True), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
