"""Single-use preparation of an authorized zero-only release. Never starts native work."""
from pathlib import Path
import copy
import datetime
import hashlib
import json
import os
import shlex
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = Path('/home/dell/yuanyuanxu/SIM240')
OUT = Path(__file__).resolve().parent
CASE = ROOT / 'CASE/unseen_v2_reference_S3_reuse_v1_1'
CHECK = ROOT / 'CASE/unseen_v2_reference_checker_S3_reuse_v1_1'
A = CASE / 'evidence/preparation_A.json'
A_SHA = '7f6ca19de96949a537802f92804c787cf092e8de0eb10c681ed279736a2d3695'
REVIEW = ROOT / 'docs/reports/URV_S3_v1_1_A_readonly_review_20261103'
IMPL = ROOT / 'docs/reports/URV_S3_R1_R2_revision_20261103'
RELEASE = CASE / 'evidence/S3_zero_launch_release_v1_1_20261103_01.json'
AUTH = CASE / 'evidence/S3_zero_launch_authorization_v1_1_20261103_01.json'
PYTHON = '/home/dell/miniconda3/bin/python3'
SESSION = 'urv_s3_zero_v1_1_20261103_01'
QUESTION = '是否现在授权 S3 v1.1 的12次原生零步调用（四配置各 describe/precheck/initialize，推进0步）及4次初态场读取，失败即停、不重试？本次仅让我在复核封存与资源后生成独立执行合同和一条命令，由你本人手动启动；不包含性能推进或正式计算。'
ANSWER = '现在授权上述12＋4；生成合同和命令，由我手动启动'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
load = lambda p: json.loads(Path(p).read_text())


def save_new(path, value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def no_execution_artifacts():
    forbidden = [CASE / x for x in ('audit_attempts', 'launch_attempts', 'analysis_results',
                                    'evidence/preparation_B.json')]
    forbidden.append(CASE / 'audits/URV_S3_ZERO_v1_1_20261103_01/verification.json')
    assert not any(p.exists() for p in forbidden), 'S3 already attempted/completed; do not rebind'
    folder = CASE / 'audits/URV_S3_ZERO_v1_1_20261103_01'
    assert {str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file()} == {
        str(Path(r['planned_case_id']) / r['mode'] / n)
        for r in load(A)['zero_prepared_runs'] for n in ('run_config.txt', 'run_manifest.txt')
    }, 'unexpected existing audit files'


def main():
    sys.path[:0] = [str(CHECK / 'analysis'), str(CASE / 'scripts')]
    import stage_s3 as stage
    import run_S3
    from s3_baselines import verify_baselines

    assert not any(p.exists() for p in (RELEASE, RELEASE.with_suffix('.sha256'), AUTH))
    data = stage.verify_seal(A, A_SHA)
    assert A.with_suffix('.sha256').read_text().strip() == A_SHA
    assert len(data['inputs_sha256']) == 2437
    assert all(data[k] is False for k in ('simulation_authorized', 'formal_simulation_authorized',
                                         'native_zero_step_authorized', 'performance_time_stepping_authorized'))
    stage.require_pristine(data['prepared_runs'])
    zeros = stage.validate_zero_plan(data)
    stage.require_pristine(zeros)
    no_execution_artifacts()
    baseline = verify_baselines(data)

    protected = dict(data['inputs_sha256'])
    for tree in (CASE, CHECK, REVIEW, IMPL):
        for p in tree.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                protected[str(p)] = sha(p)
    save_new(OUT / 'protected_files_before.json', protected)
    for name in ('SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md'):
        with (OUT / ('before_' + name)).open('xb') as stream:
            stream.write((ROOT / 'docs/reports' / name).read_bytes())
    for directory in (REVIEW, IMPL):
        for relative, digest in load(directory / 'report_manifest.json').items():
            assert sha(directory / relative) == digest, ('prior report drift', directory, relative)
    review = load(REVIEW / 'verification.json')
    assert review['BINDING_INTEGRITY_PASS'] and review['R1_R2_SCOPE_REVIEW_PASS']
    assert review['prior_postseal_tests_verified'] == 130

    clean = dict(os.environ)
    clean.pop('LD_LIBRARY_PATH', None)
    clean.pop('LD_PRELOAD', None)
    elf = Path(data['provenance']['native_binary'])
    build = load(data['provenance']['build_environment'])
    assert sha(elf) == stage.ELF_SHA == build['binary_sha256']
    linked = subprocess.run(['/usr/bin/ldd', str(elf)], env=clean, text=True,
                            capture_output=True, timeout=30, check=True)
    (OUT / 'clean_environment_ldd.txt').write_text(linked.stdout)
    libraries = set()
    for line in linked.stdout.splitlines():
        for word in line.split():
            if word.startswith('/'):
                libraries.add(str(Path(word).resolve()))
    assert libraries == set(build['dynamic_library_sha256']), 'dynamic library resolution changed'
    assert all(sha(p) == h for p, h in build['dynamic_library_sha256'].items())
    active = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            args = (proc / 'cmdline').read_bytes().decode(errors='replace').strip('\0').split('\0')
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if args and (Path(args[0]).name == 'urv_reference' or any(
            Path(arg).name in ('audit_S3_zero.py', 'run_S3.py') for arg in args[1:]
        )):
            active.append(dict(pid=int(proc.name), args=args))
    assert not active, 'native/S3 task already running'
    sessions = subprocess.run(['/usr/bin/tmux', 'list-sessions', '-F', '#S'], env=clean,
                              capture_output=True, text=True, timeout=10)
    assert sessions.returncode in (0, 1)
    assert SESSION not in sessions.stdout.splitlines(), 'session name already used'
    assert Path('/usr/bin/pvpython').is_file() and os.access('/usr/bin/pvpython', os.X_OK)
    assert Path(PYTHON).is_file() and os.access(PYTHON, os.X_OK)
    resources = run_S3.resources(True)
    snapshot = dict(checked_at=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
                    resources=resources, resources_pass=True, active_native_or_S3_processes=active,
                    existing_tmux_sessions=sessions.stdout.splitlines(),
                    tmux_query_exit_code=sessions.returncode, tmux_query_stderr=sessions.stderr,
                    dynamic_libraries_verified=len(libraries), clean_ldd_exit_code=linked.returncode,
                    binary_sha256=sha(elf), openlb_version=build['openlb_version'],
                    original_A_inputs_verified=len(data['inputs_sha256']),
                    prior_review_manifest_verified=True, prior_postseal_130_test_evidence_verified=True,
                    software_tests_rerun=False, prior_review_rerun=False,
                    baseline_K=baseline, pristine_formal_directories=4, pristine_zero_directories=12,
                    no_execution_artifacts=True, native_calls=0, VTK_reader_invocations=0,
                    time_steps=0, builds=0)
    save_new(OUT / 'prebinding_verification.json', snapshot)

    audit_ids = [r['run_id'] for r in zeros]
    field_plan = [dict(planned_case_id=r['planned_case_id'],
                       initialization_run_id=r['run_id'],
                       initialization_directory=r['output_directory'],
                       field_readback_path=str(CASE / 'audits' / stage.AUDIT_ID /
                           ('field_readback_' + r['planned_case_id'] + '.json')))
                  for r in zeros if r['mode'] == 'initialize']
    authorization = dict(kind='USER_AUTHORIZATION_EVIDENCE',
        recorded_at=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        authorization_source='user_reply_to_request_user_input_async',
        question_item_id='["request_user_input_async","call_35f755d5d0174f219e23b0e27d7a515f",0]',
        user_explicitly_authorized=True, user_instruction_verbatim=ANSWER,
        authorization_question_verbatim=QUESTION, selected_answer_verbatim=ANSWER,
        verbatim_recorded_from_typed_sentence=False,
        authorization_recording_note='Actual selected answer recorded verbatim; scope is supplied by the complete question and answer together.',
        stage=stage.STAGE, addendum_id=stage.REVISION, audit_id=stage.AUDIT_ID,
        preparation_A_path=str(A), preparation_A_sha256=A_SHA,
        native_zero_step_authorized=True, initial_field_readback_authorized=True,
        native_calls_authorized=12, initial_field_reads_authorized=4,
        allowed_native_modes=list(stage.MODES), actual_time_steps_authorized=0,
        native_call_wall_cap_seconds=300, field_read_wall_cap_seconds=300,
        approved_audit_run_ids=audit_ids, approved_initial_field_reads=field_plan,
        approved_run_ids=[], simulation_authorized=False, formal_simulation_authorized=False,
        performance_time_stepping_authorized=False, AI_may_start_solver=False,
        user_manually_starts=True, automatic_retry_authorized=False,
        automatic_extension_authorized=False, failure_policy='STOP_WITHOUT_RETRY',
        S4_authorized=False, S5_authorized=False)
    save_new(AUTH, authorization)
    bound = copy.deepcopy(data)
    bound.update(kind='AUTHORIZED_ZERO_STEP_AUDIT_RELEASE',
        release_id='URV_S3_ZERO_LAUNCH_v1_1_20261103_01',
        released_at=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        preparation_A_path=str(A), preparation_A_sha256=A_SHA,
        native_zero_step_authorized=True, approved_audit_run_ids=audit_ids,
        audit_authorization=dict(user_explicitly_authorized=True,
                                 user_instruction_verbatim=ANSWER),
        audit_authorization_evidence=dict(path=str(AUTH), sha256=sha(AUTH)),
        approved_initial_field_reads=field_plan,
        zero_execution_scope=dict(native_calls=12, initial_field_reads=4,
            allowed_modes=list(stage.MODES), maximum_time_steps=0,
            native_call_wall_cap_seconds=300, field_read_wall_cap_seconds=300,
            failure_policy='STOP_WITHOUT_RETRY'),
        process_environment_requirements=dict(unset=['LD_LIBRARY_PATH', 'LD_PRELOAD']),
        user_manual_execution_only=True)
    additions = [A, A.with_suffix('.sha256'), AUTH, REVIEW / 'report_manifest.json',
                 *(REVIEW / x for x in load(REVIEW / 'report_manifest.json')),
                 OUT / 'prebinding_verification.json', OUT / 'clean_environment_ldd.txt',
                 Path(__file__).resolve()]
    for p in additions:
        if str(p) in bound['inputs_sha256']:
            assert bound['inputs_sha256'][str(p)] == sha(p)
        else:
            bound['inputs_sha256'][str(p)] = sha(p)
    save_new(RELEASE, bound)
    digest = sha(RELEASE)
    with RELEASE.with_suffix('.sha256').open('x') as stream:
        stream.write(digest + '\n')
    stage.verify_seal(RELEASE, digest)
    stage.validate_zero_authority(bound)
    stage.require_pristine(stage.validate_zero_plan(bound))
    stage.require_pristine(bound['prepared_runs'])
    no_execution_artifacts()
    assert all(sha(p) == h for p, h in protected.items()), 'protected file changed'
    stage.unchanged(bound['inputs_sha256'])
    # Authority validators are file-only. Positive zero authority and negative formal
    # authority are checked without calling an execute entry point or any subprocess.
    from evidence import EvidenceError
    try:
        stage.validate_formal_authority(bound)
    except EvidenceError as error:
        formal_refusal = str(error)
    else:
        raise AssertionError('zero-only release accepted as formal authority')
    try:
        stage.verify_seal(RELEASE, '0' * 64)
    except EvidenceError as error:
        wrong_sha_refusal = str(error)
    else:
        raise AssertionError('wrong expected SHA accepted')
    # The ordinary CLI is inspected with all subprocess creation blocked.
    import contextlib
    import io
    from unittest.mock import patch
    import audit_S3_zero
    stdout, stderr = io.StringIO(), io.StringIO()
    with patch('subprocess.Popen', side_effect=AssertionError('NO PROCESS DURING BINDING CHECK')) as proc:
        with patch.object(sys, 'argv', ['audit_S3_zero.py', '--release', str(RELEASE),
                                      '--release-sha256', digest]), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = audit_S3_zero.main()
        assert code == 0 and not proc.called
    inspected = json.loads(stdout.getvalue())
    assert inspected['solver_executed'] is False and inspected['planned_native_calls'] == 12
    assert inspected['planned_initial_field_reads'] == 4 and inspected['native_zero_step_authorized'] is True
    controller_log = CASE / 'S3_zero_controller_v1_1_20261103_01.log'
    assert not controller_log.exists() and str(controller_log) not in bound['inputs_sha256']
    command_args = ['env', '-u', 'LD_LIBRARY_PATH', '-u', 'LD_PRELOAD', PYTHON, '-B',
                    'scripts/audit_S3_zero.py', '--release', str(RELEASE),
                    '--release-sha256', digest, '--execute']
    inner = 'cd ' + shlex.quote(str(CASE)) + ' && exec ' + shlex.join(command_args)
    inner += ' > ' + shlex.quote(str(controller_log)) + ' 2>&1'
    command = 'tmux new-session -d -s ' + shlex.quote(SESSION) + ' ' + shlex.quote(inner)
    with (OUT / 'START_COMMAND.txt').open('x') as stream:
        stream.write(command + '\n')
    syntax = subprocess.run(['/bin/bash', '-n'], input=command + '\n', text=True,
                             capture_output=True, timeout=10)
    assert syntax.returncode == 0
    assert len(shlex.split(command)) == 6 and shlex.split(command)[-1] == inner
    stage.unchanged(bound['inputs_sha256'])
    assert all(sha(p) == h for p, h in protected.items())
    no_execution_artifacts()
    save_new(OUT / 'verification.json', dict(
        verified_at=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        release_path=str(RELEASE), release_sha256=digest,
        release_inputs_verified=len(bound['inputs_sha256']),
        original_A_sha256=A_SHA, original_A_inputs_verified=2437,
        original_A_and_inputs_unchanged=True, protected_files_unchanged=len(protected),
        authorization_evidence_path=str(AUTH), authorization_evidence_sha256=sha(AUTH),
        real_user_authorization_received=True, authorization_source='selected answer plus complete question',
        zero_authority_validation_pass=True, formal_authority_rejected=formal_refusal,
        wrong_expected_sha_rejected=wrong_sha_refusal,
        readonly_CLI_exit_code=code, readonly_CLI_output=inspected,
        readonly_CLI_stderr=stderr.getvalue(), readonly_CLI_subprocess_calls=0,
        bash_syntax_exit_code=syntax.returncode, command_argv_roundtrip_pass=True,
        controller_log_path=str(controller_log), controller_log_is_bound_input=False,
        native_zero_step_authorized=True, initial_field_reads_authorized=4,
        simulation_authorized=False, formal_simulation_authorized=False,
        performance_time_stepping_authorized=False, actual_audit_run_ids=[], actual_formal_run_ids=[],
        native_calls=0, VTK_reader_invocations=0, time_steps=0, builds=0,
        actual_zero_audit_status='NOT_EXECUTED', preparation_B_created=False,
        execution_attempt_created=False, NUMERICAL_GATE='NOT_EVALUATED', geometry_PASS=None,
        RESULT_PASS=False, reference_qualified=False, MODEL_COMPARISON='NOT_EVALUATED',
        physical_validation='NOT_EVALUATED', submission_ready=False,
        resources_snapshot=resources, session=SESSION, user_manually_starts=True,
        AI_may_start_solver=False, no_automatic_retry_extension_or_next_stage=True))
    print(json.dumps(dict(release=str(RELEASE), sha256=digest,
                         bound_inputs=len(bound['inputs_sha256']), resources=resources,
                         protected_files=len(protected), readonly_CLI=inspected), ensure_ascii=False))


if __name__ == '__main__':
    main()
