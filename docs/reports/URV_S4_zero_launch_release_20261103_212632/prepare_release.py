"""Single-use S4 zero-only binding generator. Never starts native or VTK work."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import contextlib,copy,hashlib,io,json,os,re,shlex,subprocess,sys
from unittest.mock import patch
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_S4_reuse_v1';CHECK=ROOT/'CASE/unseen_v2_reference_checker_S4_reuse_v1'
REVIEW=ROOT/'docs/reports/URV_S4_A_readonly_review_20261103_205756'
IMPL=ROOT/'docs/reports/URV_S4_implementation_20261103_203002'
A=CASE/'evidence/preparation_A.json';A_SHA='e9d12e68eaa324bd8e78ad57825710936f9e00518faf39337923b930ad82a165'
RELEASE=CASE/'evidence/S4_zero_launch_release_v1_20261103_01.json'
AUTH=CASE/'evidence/S4_zero_launch_authorization_v1_20261103_01.json'
SESSION='urv_s4_zero_v1_20261103_01';LOG=CASE/'S4_zero_controller_v1_20261103_01.log'
PYTHON='/home/dell/miniconda3/bin/python3'
QUESTION='S4 准备 A 的只读复核已通过。是否现在授权18次原生零步调用（六配置各 describe／precheck／initialize，推进0步）及6次初态场读取：每次原生调用、每次读取各最多300秒，失败即停、不重试？本次仅让我在复核封存和届时资源后生成独立执行合同和一条命令，由你本人手动启动；不包含性能推进或正式计算。'
ANSWER='现在授权18＋6；生成合同和命令，由我手动启动'
QID='["request_user_input_async","call_00fda303fc644ba0899a14837bda04fd",0]'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
def save(path,value):
    with Path(path).open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def now():return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
def no_execution_artifacts(data):
    for name in ('audit_attempts','launch_attempts','analysis_results','evidence/preparation_B.json'):
        assert not (CASE/name).exists(),'S4 execution artifact already exists; no duplicate binding'
    folder=CASE/'audits/URV_S4_ZERO_v1_20261103_01'
    expected={str(Path(r['planned_case_id'])/r['mode']/name) for r in data['zero_prepared_runs'] for name in ('run_config.txt','run_manifest.txt')}
    assert {str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file()}==expected,'audit output already used'

def main():
    sys.path[:0]=[str(CHECK/'analysis'),str(CASE/'scripts')]
    import stage_s4 as stage
    import run_S4,audit_S4_zero
    from evidence import EvidenceError
    assert not any(p.exists() for p in (RELEASE,RELEASE.with_suffix('.sha256'),AUTH,LOG)),'binding/session/log path already used'
    data=stage.verify_seal(A,A_SHA);assert A.with_suffix('.sha256').read_text().strip()==A_SHA
    assert len(data['inputs_sha256'])==2976
    stage.require_pristine(data['prepared_runs']);zeros=stage.validate_zero_plan(data);stage.require_pristine(zeros);no_execution_artifacts(data)
    protected=load(OUT/'protected_files_before.json');assert all(sha(p)==h for p,h in protected.items())
    for folder in (REVIEW,IMPL):
        manifest=load(folder/'document_manifest.json');assert all(sha(folder/p)==h for p,h in manifest.items())
    review=load(REVIEW/'review_verification.json');assert review['PREPARATION_A_READONLY_REVIEW_PASS'] and review['preparation_A_sha256']==A_SHA
    assert review['historical_tests_verified']==120 and load(IMPL/'software_verification.json')['successful']
    clean=dict(os.environ);clean.pop('LD_LIBRARY_PATH',None);clean.pop('LD_PRELOAD',None)
    build=load(data['provenance']['build_environment']);binary=Path(data['provenance']['native_binary'])
    assert sha(binary)==stage.ELF_SHA==build['binary_sha256']
    linked=subprocess.run(['/usr/bin/ldd',str(binary)],env=clean,capture_output=True,text=True,timeout=30,check=True)
    assert 'not found' not in linked.stdout
    with (OUT/'clean_environment_ldd.txt').open('x') as f:f.write(linked.stdout)
    libraries={str(Path(word).resolve()) for line in linked.stdout.splitlines() for word in line.split() if word.startswith('/')}
    assert libraries==set(build['dynamic_library_sha256']),'resolved dynamic dependencies changed'
    assert all(sha(p)==h for p,h in build['dynamic_library_sha256'].items())
    active=[]
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():continue
        try:args=(proc/'cmdline').read_bytes().decode(errors='replace').strip('\0').split('\0')
        except (PermissionError,FileNotFoundError,ProcessLookupError):continue
        if args and (Path(args[0]).name=='urv_reference' or any(re.fullmatch(r'(?:run|audit)_S[0-5](?:_[A-Za-z0-9]+)*\.py',Path(arg).name) for arg in args[1:])):
            active.append(dict(pid=int(proc.name),args=args))
    assert not active,'conflicting URV solver/controller process found'
    sessions=subprocess.run(['/usr/bin/tmux','list-sessions','-F','#{session_name}'],env=clean,capture_output=True,text=True,timeout=10)
    assert sessions.returncode in (0,1)
    assert SESSION not in sessions.stdout.splitlines(),'tmux session already exists'
    if sessions.returncode==1:assert 'no server running' in sessions.stderr or 'No such file or directory' in sessions.stderr,'tmux query failure must not be mistaken for no sessions'
    for executable in (PYTHON,'/usr/bin/pvpython','/usr/bin/tmux','/usr/bin/env'):
        assert Path(executable).is_file() and os.access(executable,os.X_OK)
    available=run_S4.resources(True)
    snapshot=dict(at=now(),host=os.uname().nodename,resources=available,resources_pass=True,
        relevant_conflict_processes=active,existing_tmux_sessions=sessions.stdout.splitlines(),tmux_query_exit=sessions.returncode,tmux_query_stderr=sessions.stderr,
        binary_sha256=sha(binary),dynamic_libraries_currently_resolved_and_verified=len(libraries),ldd_exit=linked.returncode,
        original_A_inputs_verified=2976,pristine_formal_directories=6,pristine_zero_directories=18,
        historical_tests_evidence_verified=120,tests_rerun=False,resource_reserved=False,
        Python_executable=PYTHON,Python_version=sys.version,pvpython_path='/usr/bin/pvpython',pvpython_executed=False,
        native_calls=0,VTK_reader_calls=0,builds=0,actual_time_steps=0)
    save(OUT/'prebinding_verification.json',snapshot)
    ids=[r['run_id'] for r in zeros]
    fields=[dict(planned_case_id=r['planned_case_id'],initialization_run_id=r['run_id'],initialization_directory=r['output_directory'],
        field_readback_path=str(CASE/'audits'/stage.AUDIT_ID/('field_readback_'+r['planned_case_id']+'.json'))) for r in zeros if r['mode']=='initialize']
    authorization=dict(kind='USER_AUTHORIZATION_EVIDENCE',recorded_at=now(),authorization_source='user_reply_to_request_user_input_async',
        question_item_id=QID,user_explicitly_authorized=True,user_instruction_verbatim=ANSWER,
        authorization_question_verbatim=QUESTION,selected_answer_verbatim=ANSWER,verbatim_recorded_from_typed_sentence=False,
        authorization_recording_note='Actual selected answer preserved; complete question plus answer defines scope; no fabricated typed expanded sentence.',
        stage=stage.STAGE,addendum_id=stage.REVISION,audit_id=stage.AUDIT_ID,preparation_A_path=str(A),preparation_A_sha256=A_SHA,
        native_zero_step_authorized=True,initial_field_readback_authorized=True,native_call_count=18,initial_field_read_count=6,
        allowed_native_modes=list(stage.MODES),actual_time_steps_authorized=0,native_call_wall_cap_seconds=300,field_read_wall_cap_seconds=300,
        approved_audit_run_ids=ids,approved_initial_field_reads=fields,approved_run_ids=[],simulation_authorized=False,formal_simulation_authorized=False,
        performance_time_stepping_authorized=False,AI_may_start_solver=False,user_manually_starts=True,automatic_retry_authorized=False,
        automatic_extension_authorized=False,S5_authorized=False,failure_policy='STOP_WITHOUT_RETRY')
    save(AUTH,authorization)
    bound=copy.deepcopy(data)
    bound.update(kind='AUTHORIZED_ZERO_STEP_AUDIT_RELEASE',release_id='URV_S4_ZERO_LAUNCH_v1_20261103_01',released_at=now(),
        preparation_A_path=str(A),preparation_A_sha256=A_SHA,native_zero_step_authorized=True,initial_field_readback_authorized=True,
        approved_audit_run_ids=ids,approved_initial_field_reads=fields,
        audit_authorization=dict(user_explicitly_authorized=True,user_instruction_verbatim=ANSWER),
        audit_authorization_evidence=dict(path=str(AUTH),sha256=sha(AUTH)),
        zero_execution_scope=dict(native_call_count=18,initial_field_read_count=6,allowed_modes=list(stage.MODES),maximum_time_steps=0,
            native_call_wall_cap_seconds=300,field_read_wall_cap_seconds=300,failure_policy='STOP_WITHOUT_RETRY'),
        process_environment_requirements=dict(unset=['LD_LIBRARY_PATH','LD_PRELOAD']),user_manual_execution_only=True)
    additions=[A,A.with_suffix('.sha256'),AUTH,REVIEW/'document_manifest.json',*(REVIEW/p for p in load(REVIEW/'document_manifest.json')),
        OUT/'prebinding_verification.json',OUT/'clean_environment_ldd.txt',Path(__file__).resolve(),Path(PYTHON).resolve(),Path('/usr/bin/pvpython').resolve()]
    for p in additions:
        if str(p) in bound['inputs_sha256']:assert bound['inputs_sha256'][str(p)]==sha(p)
        else:bound['inputs_sha256'][str(p)]=sha(p)
    assert str(LOG) not in bound['inputs_sha256'] and not LOG.exists()
    # Validate permissions and full file closure before writing the new contract.
    stage.unchanged(bound['inputs_sha256']);stage.validate_zero_authority(bound)
    save(RELEASE,bound);digest=sha(RELEASE)
    with RELEASE.with_suffix('.sha256').open('x') as f:f.write(digest+'\n')
    assert stage.verify_seal(RELEASE,digest)==bound
    try:stage.validate_formal_authority(bound)
    except EvidenceError as error:formal_refusal=str(error)
    else:raise AssertionError('zero contract accepted as formal authority')
    try:stage.verify_seal(RELEASE,'0'*64)
    except EvidenceError as error:wrong_sha_refusal=str(error)
    else:raise AssertionError('wrong external SHA accepted')
    stdout,stderr=io.StringIO(),io.StringIO()
    with patch('subprocess.Popen',side_effect=AssertionError('No subprocess in default binding check')) as process:
        with patch.object(sys,'argv',['audit_S4_zero.py','--release',str(RELEASE),'--release-sha256',digest]),contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):code=audit_S4_zero.main()
        assert code==0 and not process.called
    response=json.loads(stdout.getvalue());assert response['solver_executed'] is False and response['planned_native_calls']==18 and response['planned_initial_field_reads']==6 and response['native_zero_step_authorized'] is True
    inner='cd '+shlex.quote(str(CASE))+' && exec '+shlex.join(['/usr/bin/env','-u','LD_LIBRARY_PATH','-u','LD_PRELOAD',PYTHON,'-B','scripts/audit_S4_zero.py','--release',str(RELEASE),'--release-sha256',digest,'--execute'])
    inner+=' > '+shlex.quote(str(LOG))+' 2>&1'
    command='tmux new-session -d -s '+shlex.quote(SESSION)+' '+shlex.quote(inner)
    syntax=subprocess.run(['/bin/bash','-n'],input=command+'\n',capture_output=True,text=True,timeout=10)
    assert syntax.returncode==0 and len(shlex.split(command))==6 and shlex.split(command)[-1]==inner
    assert '--execute' not in ['audit_S4_zero.py','--release',str(RELEASE),'--release-sha256',digest]
    stage.unchanged(bound['inputs_sha256']);stage.require_pristine(bound['prepared_runs']);stage.require_pristine(zeros);no_execution_artifacts(data)
    assert all(sha(p)==h for p,h in protected.items()) and sha(A)==A_SHA
    with (OUT/'START_COMMAND.txt').open('x') as f:f.write(command+'\n')
    save(OUT/'verification.json',dict(at=now(),release_path=str(RELEASE),release_sha256=digest,release_inputs_verified=len(bound['inputs_sha256']),
        original_A_sha256=A_SHA,original_A_inputs_verified=2976,original_A_and_inputs_unchanged=True,protected_files_unchanged=len(protected),
        authorization_path=str(AUTH),authorization_sha256=sha(AUTH),real_user_authorization_received=True,
        authorization_source='Actual selected answer plus complete question',zero_authority_valid=True,formal_authority_rejected=formal_refusal,
        wrong_external_SHA_rejected=wrong_sha_refusal,readonly_CLI_exit=code,readonly_CLI_response=response,readonly_CLI_stderr=stderr.getvalue(),readonly_CLI_subprocess_calls=0,
        bash_syntax_exit=syntax.returncode,command_argv_roundtrip=True,controller_log_path=str(LOG),controller_log_is_bound_input=False,
        session_name=SESSION,approved_audit_run_count=18,approved_initial_field_read_count=6,actual_audit_run_ids=[],actual_formal_run_ids=[],
        simulation_authorized=False,formal_simulation_authorized=False,performance_time_stepping_authorized=False,S5_authorized=False,
        native_calls=0,VTK_reader_calls=0,builds=0,actual_time_steps=0,tmux_session_started=False))
    print(json.dumps(dict(release_sha256=digest,inputs=len(bound['inputs_sha256']),resources=available,protected=len(protected),native_calls=0,VTK_calls=0,tmux_started=False),indent=2))
if __name__=='__main__':main()
