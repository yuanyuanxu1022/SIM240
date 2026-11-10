"""Prepare the genuinely authorized formal release; never executes run_S3 --execute."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
import contextlib
import copy
import io
import json
import os
import shlex
import subprocess
import sys

ROOT = Path('/home/dell/yuanyuanxu/SIM240')
OUT = Path(__file__).resolve().parent
CASE = ROOT / 'CASE/unseen_v2_reference_S3_reuse_v1_1'
CHECK = ROOT / 'CASE/unseen_v2_reference_checker_S3_reuse_v1_1'
FRD = ROOT / 'docs/reports/URV_S3_formal_scope_review_20261103'
B = CASE / 'evidence/preparation_B.json'
B_SHA = 'a5b69ec95180bf92327a3bba1311639dd2a5fb1bec412cd80c3869dda2a47f92'
RELEASE = CASE / 'evidence/S3_formal_launch_release_v1_1_20261103_01.json'
AUTH = CASE / 'evidence/S3_formal_launch_authorization_v1_1_20261103_01.json'
LOG = CASE / 'S3_formal_controller_v1_1_20261103_01.log'
SESSION = 'urv_s3_formal_v1_1_20261103_01'
PYTHON = '/home/dell/miniconda3/bin/python3'
QUESTION = '是否现在采用 S3-FRD-v1，并授权 S3 v1.1 完整四条正式计算：低力沿槽P→低力横槽T→高力沿槽P→高力横槽T，每条求解上限4小时、标准独立检查上限1小时；前一条完整验收通过才自动继续，第三条还须沿槽0.1%线性门通过才进入第四条，最后检查横槽线性门？四条求解预算合计16小时、检查另最多4小时，文件核对等另计，不保证20小时内结束；任何失败即停，不自动重试、加时、性能推进或进入S4/S5。本次只让我复核后生成正式合同和一条命令，由你本人手动启动。'
ANSWER = '现在采用并授权完整四条；生成合同和命令，由我手动启动'
sys.path[:0] = [str(CHECK / 'analysis'), str(CASE / 'scripts')]
from evidence import sha, need, EvidenceError, kv
import stage_s3 as stage
import run_S3 as runner
from s3_baselines import verify_baselines
from check_results import binding


def load(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def no_formal_attempt():
    need(not (CASE / 'launch_attempts').exists() and not (CASE / 'analysis_results').exists(),
         'formal attempt/output already exists; do not retry/rebind')
    need(not LOG.exists(), 'formal controller log exists; do not overwrite')


def main():
    need(not any(p.exists() for p in (RELEASE, RELEASE.with_suffix('.sha256'), AUTH)),
         'formal binding path already used; do not overwrite')
    no_formal_attempt()
    data = stage.verify_seal(B, B_SHA)
    need(len(data['inputs_sha256']) == 2609, 'B input count drift')
    need(B.with_suffix('.sha256').read_text().strip() == B_SHA, 'B sidecar drift')
    stage.require_pristine(data['prepared_runs'])
    stage.validate_zero_plan(data)
    with patch('subprocess.Popen', side_effect=AssertionError('no process in original evidence check')):
        stage.verify_zero_receipt(data)
        baselines = verify_baselines(data)
    protected = dict(data['inputs_sha256'])
    for directory in (CASE, CHECK, FRD, ROOT / 'docs/reports/URV_S3_zero_results_review_v1_1_20261103'):
        for p in directory.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                need(not p.is_symlink(), 'protected source symlink')
                protected[str(p)] = sha(p)
    save(OUT / 'protected_files_before.json', protected)
    for name in ['SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md']:
        with (OUT / ('before_' + name)).open('xb') as stream:
            stream.write((ROOT / 'docs/reports' / name).read_bytes())
    for name, digest in load(FRD / 'report_manifest.json').items():
        need(sha(FRD / name) == digest, 'S3-FRD scope report drift')
    scope_review = load(FRD / 'verification.json')
    need(scope_review['scope_protocol'] == 'S3-FRD-v1' and
         scope_review['scope_review'] == 'COMPATIBLE_PENDING_EXPLICIT_FORMAL_AUTHORIZATION_AND_FRESH_BINDING_CHECKS',
         'adopted scope review differs')
    plan = load(FRD / 'formal_binding_plan.json')
    need(plan['kind'] == 'NON_EXECUTABLE_RELEASE_PLAN_NOT_AUTHORIZATION' and
         plan['planned_run_ids'] == data['prepared_run_ids'] and plan['preparation_B_sha256'] == B_SHA,
         'scope identity plan differs from B')
    need(all(runner.wall_cap(r['run_config_path']) == 14400 for r in data['prepared_runs']),
         'formal wall caps changed')
    clean = dict(os.environ)
    clean.pop('LD_LIBRARY_PATH', None)
    clean.pop('LD_PRELOAD', None)
    elf = Path(data['provenance']['native_binary'])
    build = load(data['provenance']['build_environment'])
    need(sha(elf) == build['binary_sha256'] == stage.ELF_SHA, 'reused ELF drift')
    linked = subprocess.run(['/usr/bin/ldd', str(elf)], env=clean, capture_output=True,
                            text=True, timeout=30, check=True)
    (OUT / 'clean_environment_ldd.txt').write_text(linked.stdout)
    resolved = {str(Path(word).resolve()) for line in linked.stdout.splitlines()
                for word in line.split() if word.startswith('/')}
    need(resolved == set(build['dynamic_library_sha256']) and
         all(sha(p) == h for p, h in build['dynamic_library_sha256'].items()), 'loader resolution/library drift')
    active = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            argv = (proc / 'cmdline').read_bytes().decode(errors='replace').strip('\0').split('\0')
            if argv and (Path(argv[0]).name == 'urv_reference' or any(
                Path(arg).name in ('run_S3.py', 'audit_S3_zero.py', 'read_fields.py') for arg in argv[1:])):
                active.append(dict(pid=int(proc.name), argv=argv))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            pass
    need(not active, 'active native/S3/field-reader task; stop before binding')
    sessions = subprocess.run(['/usr/bin/tmux', 'list-panes', '-a', '-F', '#{session_name}|#{pane_pid}|#{pane_current_command}'],
                              env=clean, capture_output=True, text=True, timeout=10)
    need(sessions.returncode in (0, 1), 'cannot inspect tmux sessions')
    need(not any(line.split('|')[0] == SESSION for line in sessions.stdout.splitlines()), 'target session exists')
    need(Path(PYTHON).is_file() and os.access(PYTHON, os.X_OK) and
         Path('/usr/bin/pvpython').is_file() and os.access('/usr/bin/pvpython', os.X_OK), 'required interpreter/reader missing')
    available = runner.resources(True)
    prebinding = dict(checked_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        preparation_B_path=str(B), preparation_B_sha256=B_SHA, B_inputs_verified=2609,
        B_and_all_execution_flags_unchanged=True, zero_receipt_and_independent_review_verified=True,
        S3_FRD_manifest_verified=True, S2_baseline_K=baselines, resources=available,
        relevant_processes=active, tmux_panes=sessions.stdout.splitlines(),
        tmux_query_exit_code=sessions.returncode, tmux_query_stderr=sessions.stderr,
        formal_directories_pristine=4, launch_attempts_absent=True, new_controller_log_absent=True,
        binary_sha256=sha(elf), dynamic_libraries_verified=len(resolved),
        openlb_version=build['openlb_version'], native_solver_calls=0,
        VTK_reader_invocations=0, time_steps=0, builds=0)
    save(OUT / 'prebinding_verification.json', prebinding)
    adopted = dict(protocol_id='S3-FRD-v1', path=str(FRD / 'PROTOCOL.md'), sha256=sha(FRD / 'PROTOCOL.md'))
    authorization = dict(kind='USER_AUTHORIZATION_EVIDENCE',
        recorded_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        authorization_source='user_reply_to_request_user_input_async',
        question_item_id='["request_user_input_async","call_359ddf48ffb44e17958a24f0b2d3b9cd",0]',
        user_explicitly_authorized=True, user_instruction_verbatim=ANSWER,
        authorization_question_verbatim=QUESTION, selected_answer_verbatim=ANSWER,
        verbatim_recorded_from_typed_sentence=False,
        authorization_recording_note='The actual selected answer is recorded verbatim together with the complete scope question.',
        stage=stage.STAGE, addendum_id=stage.REVISION, adopted_scope_protocol=adopted,
        preparation_B_path=str(B), preparation_B_sha256=B_SHA,
        simulation_authorized=True, formal_simulation_authorized=True,
        native_zero_step_authorized=False, initial_field_readback_authorized=False,
        performance_time_stepping_authorized=False, approved_run_ids=data['prepared_run_ids'],
        approved_runs=data['prepared_runs'], approved_audit_run_ids=[],
        standard_independent_check_including_saved_field_reads_authorized=True,
        sequential_advance_only_after_acceptance=True,
        P_linearity_required_before_fourth_run=True, T_linearity_required_after_fourth_run=True,
        linearity_K_span_over_mean_max=.001, per_solver_wall_cap_seconds=14400,
        per_checker_wait_cap_seconds=3600, solver_total_budget_seconds=57600,
        checker_total_wait_budget_seconds=14400, strict_20_hour_batch_completion_guaranteed=False,
        failure_policy='STOP_WITHOUT_RETRY_EXTENSION_OR_NEXT_STAGE', automatic_retry_authorized=False,
        automatic_extension_authorized=False, S4_authorized=False, S5_authorized=False,
        AI_may_start_solver=False, user_manually_starts=True)
    save(AUTH, authorization)
    bound = copy.deepcopy(data)
    bound.update(kind='AUTHORIZED_EXECUTION_LAUNCH_RELEASE',
        release_id='URV_S3_FORMAL_LAUNCH_v1_1_20261103_01',
        released_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        preparation_B_path=str(B), preparation_B_sha256=B_SHA,
        simulation_authorized=True, formal_simulation_authorized=True,
        native_zero_step_authorized=False, performance_time_stepping_authorized=False,
        approved_runs=copy.deepcopy(data['prepared_runs']), approved_run_ids=list(data['prepared_run_ids']),
        approved_audit_run_ids=[], actual_formal_run_ids=[],
        launch_authorization=dict(user_explicitly_authorized=True, user_instruction_verbatim=ANSWER),
        launch_authorization_evidence=dict(path=str(AUTH), sha256=sha(AUTH)),
        adopted_scope_protocol=adopted,
        formal_execution_scope=dict(ordered_run_ids=data['prepared_run_ids'],
            standard_checker_including_saved_field_readback=True,
            per_solver_wall_cap_seconds=14400, per_checker_wait_cap_seconds=3600,
            total_solver_budget_seconds=57600, total_checker_wait_budget_seconds=14400,
            strict_20_hour_batch_wall_limit=False, P_control_required_before_run_4=True,
            T_control_required_after_run_4=True, K_span_over_mean_limit=.001,
            automatic_retry=False, automatic_extension=False, automatic_next_stage=False),
        process_environment_requirements=dict(unset=['LD_LIBRARY_PATH', 'LD_PRELOAD']),
        user_manual_execution_only=True)
    additions = [B, B.with_suffix('.sha256'), AUTH, FRD / 'report_manifest.json',
                 *(FRD / name for name in load(FRD / 'report_manifest.json')),
                 OUT / 'prebinding_verification.json', OUT / 'clean_environment_ldd.txt', Path(__file__).resolve()]
    for p in additions:
        if str(p) in bound['inputs_sha256']:
            need(bound['inputs_sha256'][str(p)] == sha(p), 'inherited input changed while adding evidence')
        bound['inputs_sha256'][str(p)] = sha(p)
    need(str(LOG) not in bound['inputs_sha256'], 'writable controller log must not be immutable input')
    save(RELEASE, bound)
    digest = sha(RELEASE)
    with RELEASE.with_suffix('.sha256').open('x') as stream:
        stream.write(digest + '\n')
    # Validate the actual release with actual authority; all subprocesses blocked.
    with patch('subprocess.Popen', side_effect=AssertionError('no subprocess while checking formal release')) as process:
        observed = stage.verify_seal(RELEASE, digest)
        stage.validate_formal_authority(observed)
        need(binding(RELEASE, digest) == observed, 'scientific checker binding differs')
        stage.require_pristine(observed['prepared_runs'])
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, 'argv', ['run_S3.py', '--release', str(RELEASE), '--release-sha256', digest]), \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = runner.main()
        need(code == 0 and not process.called, 'formal readonly CLI failed or started a process')
        refused = {}
        for name, check in [('formal_release_as_zero', lambda: stage.validate_zero_authority(observed)),
                            ('B_as_formal', lambda: stage.validate_formal_authority(data)),
                            ('wrong_expected_sha', lambda: stage.verify_seal(RELEASE, '0' * 64))]:
            try:
                check()
            except EvidenceError as error:
                refused[name] = str(error)
            else:
                raise AssertionError('unsafe authority accepted: ' + name)
    inspected = json.loads(stdout.getvalue())
    need(inspected['simulation_authorized'] is True and inspected['solver_executed'] is False and
         inspected['prepared_run_ids'] == data['prepared_run_ids'] and inspected['zero_audit_status'] == 'PASSED',
         'readonly formal binding output mismatch')
    no_formal_attempt()
    need(all(sha(p) == h for p, h in protected.items()), 'protected file changed')
    stage.unchanged(bound['inputs_sha256'])
    argv = ['env', '-u', 'LD_LIBRARY_PATH', '-u', 'LD_PRELOAD', PYTHON, '-B', 'scripts/run_S3.py',
            '--release', str(RELEASE), '--release-sha256', digest, '--execute']
    inner = 'cd ' + shlex.quote(str(CASE)) + ' && exec ' + shlex.join(argv)
    inner += ' > ' + shlex.quote(str(LOG)) + ' 2>&1'
    command = 'tmux new-session -d -s ' + shlex.quote(SESSION) + ' ' + shlex.quote(inner)
    with (OUT / 'START_COMMAND.txt').open('x') as stream:
        stream.write(command + '\n')
    syntax = subprocess.run(['/bin/bash', '-n'], input=command + '\n', capture_output=True, text=True, timeout=10)
    need(syntax.returncode == 0 and len(shlex.split(command)) == 6 and shlex.split(command)[-1] == inner,
         'command syntax/argument roundtrip failed')
    need(all(sha(p) == h for p, h in bound['inputs_sha256'].items()), 'release input drift after command check')
    need(all(sha(p) == h for p, h in protected.items()), 'old inputs/outputs changed')
    no_formal_attempt()
    save(OUT / 'verification.json', dict(
        verified_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        release_path=str(RELEASE), release_sha256=digest, release_inputs_verified=len(bound['inputs_sha256']),
        actual_user_authorization_received=True, selected_answer_and_complete_question_recorded=True,
        authorization_path=str(AUTH), authorization_sha256=sha(AUTH), adopted_scope_protocol=adopted,
        original_B_sha256=B_SHA, original_B_inputs_preserved=2609,
        protected_existing_files_unchanged=len(protected), formal_authority_check_pass=True,
        scientific_checker_binding_check_pass=True, readonly_controller_exit_code=code,
        readonly_controller_output=inspected, readonly_controller_stderr=stderr.getvalue(),
        readonly_controller_subprocess_calls=0, authority_and_hash_rejections=refused,
        bash_syntax_exit_code=syntax.returncode, command_argv_roundtrip_pass=True,
        controller_log_path=str(LOG), controller_log_is_bound_input=False, tmux_session=SESSION,
        simulation_authorized=True, formal_simulation_authorized=True,
        native_zero_step_authorized=False, performance_time_stepping_authorized=False,
        approved_run_ids=bound['approved_run_ids'], actual_formal_run_ids=[],
        actual_audit_run_ids=bound['actual_audit_run_ids'], formal_output_directories_pristine=4,
        launch_attempt_created=False, analysis_results_created=False,
        native_solver_calls=0, VTK_reader_invocations=0, builds=0, time_steps=0,
        source_or_config_changes=0, resources_snapshot=available,
        AI_may_start_solver=False, user_manually_starts=True,
        NUMERICAL_GATE='NOT_EVALUATED', geometry_PASS=None, RESULT_PASS=False,
        S3_CONTROL_PASS='NOT_EVALUATED', reference_qualified=False,
        MODEL_COMPARISON='NOT_EVALUATED', physical_validation='NOT_EVALUATED', submission_ready=False))
    print(json.dumps(dict(release_path=str(RELEASE), release_sha256=digest,
        bound_inputs=len(bound['inputs_sha256']), protected_files=len(protected),
        resources_snapshot=available, readonly_controller=inspected, formal_started=False),
        ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
