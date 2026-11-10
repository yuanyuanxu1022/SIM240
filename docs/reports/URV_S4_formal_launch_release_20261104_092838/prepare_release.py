"""Single-use authorized S4 document binding. Never starts any solver or reader."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
import contextlib
import copy
import io
import json
import os
import re
import shlex
import subprocess
import sys

ROOT = Path('/home/dell/yuanyuanxu/SIM240')
OUT = Path(__file__).resolve().parent
CASE = ROOT/'CASE/unseen_v2_reference_S4_reuse_v1'
CHECK = ROOT/'CASE/unseen_v2_reference_checker_S4_reuse_v1'
FRD = ROOT/'docs/reports/URV_S4_formal_scope_resource_review_20261104_090724'
REVIEW = ROOT/'docs/reports/URV_S4_zero_results_review_20261103_220122'
B = CASE/'evidence/preparation_B.json'
B_SHA = '7ca2ce3c27076a80d7d692bb13f3030854cf44b683dfe6bcec54ed15c288b06c'
RELEASE = CASE/'evidence/S4_formal_launch_release_v1_20261104_01.json'
AUTH = CASE/'evidence/S4_formal_launch_authorization_v1_20261104_01.json'
DECISION = CASE/'evidence/S4_formal_resource_decision_v1_20261104_01.json'
LOG = CASE/'S4_formal_controller_v1_20261104_01.log'
SESSION = 'urv_s4_formal_v1_20261104_01'
PYTHON = '/home/dell/miniconda3/bin/python3'
QUESTION = '是否现在采用 S4-FRD-v1，并授权完整六条正式 S4：按5／2.5／1.25 nm、每档沿槽P→横槽T；单条求解上限分别为1／4／12小时，每条标准独立检查外层等待最多1小时，前条完整验收通过才继续（包括第四条后自动进入细网格）？暂不另做PERF，接受细网格可能12小时未完成、批次随即停止的风险；求解预算合计34小时、检查另最多6小时，文件处理及清理另计，40小时不是总时限保证。失败即停，不自动重试、加时或进入S5。本次仅让我复核后生成正式合同和一条命令，由你本人手动启动。'
ANSWER = '现在采用并授权完整六条；生成合同和命令，由我手动启动'
QID = '["request_user_input_async","call_a2f8d135b2a942e78a70d8438206254e",0]'
sys.path[:0] = [str(CHECK/'analysis'), str(CASE/'scripts')]
from evidence import need, sha, EvidenceError
import stage_s4 as stage
import run_S4 as runner
from check_results import binding


def now():
    return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()


def load(p):
    return json.loads(Path(p).read_text())


def save(p, value):
    with Path(p).open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def no_attempt():
    need(not (CASE/'launch_attempts').exists() and not (CASE/'analysis_results').exists(), 'S4 formal path used')
    need(not LOG.exists(), 'new control log already exists')
    need(not list(CASE.rglob('completion.json')) and not list(CASE.rglob('diagnostics.csv')), 'formal output exists')


def main():
    need(not any(p.exists() for p in (RELEASE, RELEASE.with_suffix('.sha256'), AUTH, DECISION)), 'binding paths used; no overwrite')
    no_attempt()
    with patch('subprocess.Popen', side_effect=AssertionError('file-only prerequisite check')):
        data = stage.verify_seal(B, B_SHA)
        stage.verify_zero_receipt(data)
        stage.validate_zero_plan(data)
        stage.require_pristine(data['prepared_runs'])
    need(len(data['inputs_sha256']) == 3248 and B.with_suffix('.sha256').read_text().strip() == B_SHA, 'B changed')
    acceptance = load(data['independent_zero_review_path'])
    need(sha(data['independent_zero_review_path']) == data['independent_zero_review_sha256'] and
         acceptance['ZERO_STEP_INDEPENDENT_REVIEW_PASS'] is True and
         acceptance['eighteen_records_reviewed'] == 18 and acceptance['actual_VTK_field_rereads'] == 6,
         'independent zero acceptance missing')
    protected = dict(data['inputs_sha256'])
    for folder in (CASE, CHECK, FRD, REVIEW):
        for p in folder.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                need(not p.is_symlink(), 'symlink input')
                protected[str(p)] = sha(p)
    save(OUT/'protected_files_before.json', protected)
    for folder in (FRD, REVIEW):
        for name, digest in load(folder/'document_manifest.json').items():
            need(sha(ROOT/name) == digest, 'prior review report changed: '+name)
    scope = load(FRD/'scope_audit.json')
    candidate = load(FRD/'resource_decision_candidate.json')
    plan = load(FRD/'formal_binding_plan.json')
    need(scope['PASS'] is True and scope['B_sha256'] == B_SHA and scope['frozen_runner_static_compatible'] is True, 'scope review mismatch')
    need(candidate['protocol_id'] == 'S4-FRD-v1' and candidate['resource_decision_accepted'] is False and
         candidate['ordered_run_ids'] == data['prepared_run_ids'] and
         plan['kind'] == 'NON_EXECUTABLE_FORMAL_BINDING_PLAN_NOT_AUTHORIZATION', 'scope candidate changed')
    caps = [runner.wall_cap(r['run_config_path']) for r in data['prepared_runs']]
    need(caps == [3600,3600,14400,14400,43200,43200], 'solver caps changed')
    clean = dict(os.environ)
    clean.pop('LD_LIBRARY_PATH', None); clean.pop('LD_PRELOAD', None)
    elf = Path(data['provenance']['native_binary'])
    build = load(data['provenance']['build_environment'])
    need(sha(elf) == build['binary_sha256'] == stage.ELF_SHA, 'ELF changed')
    linked = subprocess.run(['/usr/bin/ldd',str(elf)], env=clean, capture_output=True, text=True, timeout=30, check=True)
    need('not found' not in linked.stdout, 'unresolved library')
    with (OUT/'clean_environment_ldd.txt').open('x') as f: f.write(linked.stdout)
    resolved = {str(Path(w).resolve()) for line in linked.stdout.splitlines() for w in line.split() if w.startswith('/')}
    need(resolved == set(build['dynamic_library_sha256']) and
         all(sha(p) == h for p,h in build['dynamic_library_sha256'].items()), 'clean loader drift')
    active = []
    for p in Path('/proc').iterdir():
        if not p.name.isdigit(): continue
        try: args = (p/'cmdline').read_bytes().decode(errors='replace').strip('\0').split('\0')
        except (FileNotFoundError,PermissionError,ProcessLookupError): continue
        if args and (Path(args[0]).name == 'urv_reference' or any(
            re.fullmatch(r'(?:run|audit)_S[0-5](?:_[A-Za-z0-9]+)*\.py', Path(a).name) or
            Path(a).name in ('read_fields.py','run_perf.py') for a in args[1:])):
            active.append(dict(pid=int(p.name),argv=args))
    need(not active, 'conflicting native/controller/reader task')
    sessions = subprocess.run(['/usr/bin/tmux','list-panes','-a','-F','#{session_name}|#{pane_pid}|#{pane_current_command}'],
                              env=clean,capture_output=True,text=True,timeout=10)
    need(sessions.returncode in (0,1), 'tmux query failed')
    if sessions.returncode == 1:
        need('no server running' in sessions.stderr or 'No such file or directory' in sessions.stderr, 'unexplained tmux error')
    need(not any(s.split('|')[0] == SESSION for s in sessions.stdout.splitlines()), 'target session used')
    for executable in (PYTHON,'/usr/bin/pvpython','/usr/bin/env','/usr/bin/tmux'):
        need(Path(executable).is_file() and os.access(executable,os.X_OK), 'executable unavailable')
    available = runner.resources(True)
    preflight = dict(checked_at=now(),host=os.uname().nodename,preparation_B_path=str(B),preparation_B_sha256=B_SHA,
        B_inputs_verified=3248,zero_audit_and_independent_review_verified=True,S4_FRD_manifest_verified=True,
        relevant_processes=active,tmux_panes=sessions.stdout.splitlines(),tmux_query_exit=sessions.returncode,
        tmux_query_stderr=sessions.stderr,resources=available,resources_reserved=False,
        pristine_formal_directories=6,launch_attempts_absent=True,new_log_absent=True,
        binary_sha256=sha(elf),dynamic_libraries_resolved_and_verified=len(resolved),
        openlb_version=build['openlb_version'],Python_executable=PYTHON,Python_version=sys.version,
        numpy_version=__import__('numpy').__version__,pvpython_invoked=False,native_calls=0,VTK_calls=0,builds=0)
    save(OUT/'prebinding_verification.json',preflight)
    adopted = dict(protocol_id='S4-FRD-v1',path=str(FRD/'PROTOCOL.md'),sha256=sha(FRD/'PROTOCOL.md'))
    auth = dict(kind='USER_AUTHORIZATION_EVIDENCE',recorded_at=now(),stage=stage.STAGE,addendum_id=stage.REVISION,
        authorization_source='user_reply_to_request_user_input_async',question_item_id=QID,
        user_explicitly_authorized=True,user_instruction_verbatim=ANSWER,selected_answer_verbatim=ANSWER,
        authorization_question_verbatim=QUESTION,verbatim_recorded_from_typed_sentence=False,
        authorization_recording_note='Actual selected answer and complete question preserved; no fabricated expanded typed sentence.',
        adopted_scope_protocol=adopted,preparation_B_path=str(B),preparation_B_sha256=B_SHA,
        simulation_authorized=True,formal_simulation_authorized=True,
        approved_runs=data['prepared_runs'],approved_run_ids=data['prepared_run_ids'],approved_audit_run_ids=[],
        standard_independent_check_including_saved_field_reads_authorized=True,
        sequential_advance_only_after_acceptance=True,fourth_to_fifth_fine_grid_advance_authorized=True,
        fine_grid_12h_timeout_and_incomplete_batch_risk_accepted=True,skip_additional_PERF_as_precondition=True,
        solver_wall_cap_seconds_by_dx_nm=stage.RESOURCES['solver_wall_cap_seconds_by_dx_nm'],
        per_checker_wait_cap_seconds=3600,solver_total_budget_seconds=122400,checker_total_wait_budget_seconds=21600,
        strict_40_hour_batch_completion_guaranteed=False,grid_checks_after_six_accepted_runs=True,
        native_zero_step_authorized=False,initial_field_readback_authorized=False,performance_time_stepping_authorized=False,
        automatic_retry_authorized=False,automatic_extension_authorized=False,S5_authorized=False,
        AI_may_start_solver=False,user_manually_starts=True,failure_policy='STOP_WITHOUT_RETRY_EXTENSION_OR_NEXT_STAGE')
    save(AUTH,auth)
    decision = copy.deepcopy(candidate)
    decision.update(kind='ADOPTED_FORMAL_RESOURCE_DECISION_NOT_EXECUTION_RELEASE',status='ADOPTED_BY_ACTUAL_USER_REPLY',
        adopted_at=now(),resource_decision_accepted=True,user_explicitly_authorized=True,user_instruction_verbatim=ANSWER,
        authorization_question_verbatim=QUESTION,authorization_question_item_id=QID,
        authorization_evidence=dict(path=str(AUTH),sha256=sha(AUTH)),adopted_scope_protocol=adopted,
        fourth_to_fifth_fine_grid_advance_accepted=True,fine_grid_12h_timeout_risk_accepted=True)
    save(DECISION,decision)
    bound = copy.deepcopy(data)
    bound.update(kind='AUTHORIZED_EXECUTION_LAUNCH_RELEASE',release_id='URV_S4_FORMAL_LAUNCH_v1_20261104_01',released_at=now(),
        preparation_B_path=str(B),preparation_B_sha256=B_SHA,simulation_authorized=True,formal_simulation_authorized=True,
        native_zero_step_authorized=False,initial_field_readback_authorized=False,performance_time_stepping_authorized=False,
        approved_runs=copy.deepcopy(data['prepared_runs']),approved_run_ids=list(data['prepared_run_ids']),
        approved_audit_run_ids=[],actual_formal_run_ids=[],
        launch_authorization=dict(user_explicitly_authorized=True,user_instruction_verbatim=ANSWER),
        launch_authorization_evidence=dict(path=str(AUTH),sha256=sha(AUTH)),adopted_scope_protocol=adopted,
        formal_resource_decision=dict(path=str(DECISION),sha256=sha(DECISION)),
        formal_execution_scope=dict(ordered_run_ids=data['prepared_run_ids'],
            standard_checker_including_saved_field_readback=True,solver_wall_cap_seconds_by_dx_nm=stage.RESOURCES['solver_wall_cap_seconds_by_dx_nm'],
            per_checker_wait_cap_seconds=3600,total_solver_budget_seconds=122400,total_checker_wait_budget_seconds=21600,
            strict_40_hour_batch_wall_limit=False,fourth_to_fifth_advance=True,fine_grid_12h_timeout_risk_accepted=True,
            grid_checks_after_six_accepted_runs=True,automatic_retry=False,automatic_extension=False,automatic_next_stage=False),
        process_environment_requirements=dict(unset=['LD_LIBRARY_PATH','LD_PRELOAD']),user_manual_execution_only=True)
    additions = [B,B.with_suffix('.sha256'),AUTH,DECISION,FRD/'document_manifest.json',
        *(ROOT/name for name in load(FRD/'document_manifest.json')),OUT/'prebinding_verification.json',
        OUT/'clean_environment_ldd.txt',Path(__file__).resolve(),Path(PYTHON).resolve(),Path('/usr/bin/pvpython').resolve()]
    for p in additions:
        if str(p) in bound['inputs_sha256']: need(bound['inputs_sha256'][str(p)] == sha(p), 'inherited input changed')
        bound['inputs_sha256'][str(p)] = sha(p)
    need(str(LOG) not in bound['inputs_sha256'] and not LOG.exists(), 'active log cannot be immutable input')
    with patch('subprocess.Popen',side_effect=AssertionError('no process during in-memory release validation')):
        stage.unchanged(bound['inputs_sha256']);stage.validate_formal_authority(bound)
    save(RELEASE,bound);digest=sha(RELEASE)
    with RELEASE.with_suffix('.sha256').open('x') as f: f.write(digest+'\n')
    with patch('subprocess.Popen',side_effect=AssertionError('no process in formal release check')) as process:
        observed=stage.verify_seal(RELEASE,digest);stage.validate_formal_authority(observed)
        need(binding(RELEASE,digest) == observed,'checker binding mismatch')
        stage.require_pristine(observed['prepared_runs'])
        stdout,stderr=io.StringIO(),io.StringIO()
        with patch.object(sys,'argv',['run_S4.py','--release',str(RELEASE),'--release-sha256',digest]),contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            code=runner.main()
        need(code==0 and not process.called,'default readonly check failed/started child')
        refused={}
        for name,check in [('formal_as_zero',lambda:stage.validate_zero_authority(observed)),
                           ('B_as_formal',lambda:stage.validate_formal_authority(data)),
                           ('wrong_external_SHA',lambda:stage.verify_seal(RELEASE,'0'*64))]:
            try:check()
            except EvidenceError as e:refused[name]=str(e)
            else:raise AssertionError('unsafe authority accepted: '+name)
    inspection=json.loads(stdout.getvalue())
    need(inspection['simulation_authorized'] is True and inspection['solver_executed'] is False and
         inspection['prepared_run_ids']==data['prepared_run_ids'] and inspection['zero_audit_status']=='PASSED','readonly output mismatch')
    inner='cd '+shlex.quote(str(CASE))+' && exec '+shlex.join(['/usr/bin/env','-u','LD_LIBRARY_PATH','-u','LD_PRELOAD',PYTHON,'-B','scripts/run_S4.py','--release',str(RELEASE),'--release-sha256',digest,'--execute'])
    inner+=' > '+shlex.quote(str(LOG))+' 2>&1'
    command='tmux new-session -d -s '+shlex.quote(SESSION)+' '+shlex.quote(inner)
    syntax=subprocess.run(['/bin/bash','-n'],input=command+'\n',capture_output=True,text=True,timeout=10)
    need(syntax.returncode==0 and len(shlex.split(command))==6 and shlex.split(command)[-1]==inner,'command syntax/roundtrip')
    no_attempt();stage.require_pristine(bound['prepared_runs']);stage.unchanged(bound['inputs_sha256'])
    need(all(sha(p)==h for p,h in protected.items()),'old evidence changed')
    with (OUT/'START_COMMAND.txt').open('x') as f:f.write(command+'\n')
    save(OUT/'verification.json',dict(verified_at=now(),release_path=str(RELEASE),release_sha256=digest,
        release_inputs_verified=len(bound['inputs_sha256']),original_B_sha256=B_SHA,original_B_inputs_preserved=3248,
        protected_existing_files_unchanged=len(protected),actual_authorization_received=True,
        authorization_path=str(AUTH),authorization_sha256=sha(AUTH),actual_selected_answer_and_complete_question_recorded=True,
        adopted_resource_decision_path=str(DECISION),adopted_resource_decision_sha256=sha(DECISION),
        formal_authority_pass=True,scientific_checker_binding_pass=True,readonly_controller_exit=code,
        readonly_controller_output=inspection,readonly_controller_stderr=stderr.getvalue(),readonly_subprocess_calls=0,
        authority_and_hash_rejections=refused,bash_syntax_exit=syntax.returncode,command_argv_roundtrip=True,
        controller_log_path=str(LOG),controller_log_is_bound_input=False,session_name=SESSION,
        approved_run_ids=bound['approved_run_ids'],actual_formal_run_ids=[],actual_audit_run_ids=bound['actual_audit_run_ids'],
        pristine_formal_directories=6,formal_attempt_created=False,formal_analysis_created=False,
        resources_snapshot=available,simulation_authorized=True,formal_simulation_authorized=True,
        native_zero_step_authorized=False,performance_time_stepping_authorized=False,S5_authorized=False,
        AI_may_start_solver=False,user_manually_starts=True,tmux_session_started=False,
        native_calls=0,VTK_calls=0,builds=0,time_steps=0,source_or_config_changes=0,
        NUMERICAL_GATE='NOT_EVALUATED',geometry_PASS=None,RESULT_PASS=False,reference_qualified=False,
        MODEL_COMPARISON='NOT_EVALUATED',physical_validation='NOT_EVALUATED',submission_ready=False))
    print(json.dumps(dict(release_sha256=digest,release_inputs=len(bound['inputs_sha256']),
        protected_files=len(protected),resources=available,solver_executed=False,formal_started=False),ensure_ascii=False))


if __name__=='__main__': main()
