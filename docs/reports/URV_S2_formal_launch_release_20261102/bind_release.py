"""Bind received formal six-case authority. Never execute solver or tmux launch."""
from pathlib import Path
import contextlib
import copy
import io
import json
import os
import re
import shlex
import subprocess
import sys
from unittest.mock import patch

ROOT=Path('/home/dell/yuanyuanxu/SIM240')
CASE=ROOT/'CASE/unseen_v2_reference_S2_reuse_v1'
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(CASE/'scripts'))
import run_S2 as runner
from evidence import need,sha,save
from stage_s2 import unchanged,validate_formal_authority,require_pristine,verify_zero_receipt
from check_results import binding


def main():
    completing = sys.argv[1:]==['--complete-existing-records']
    need(not os.environ.get('LD_LIBRARY_PATH') and not os.environ.get('LD_PRELOAD'),'clean loader environment required')
    for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        target=OUT/('before_'+name)
        if target.exists():
            need(completing and target.read_bytes()==(ROOT/'docs/reports'/name).read_bytes(),
                 'existing snapshot differs or explicit completion not selected')
        else:target.write_bytes((ROOT/'docs/reports'/name).read_bytes())
    old=ROOT/'docs/reports/URV_S2_formal_binding_precheck_20261102'
    protected=json.loads((old/'protected_inputs_before.json').read_text())
    for f in old.rglob('*'):
        if f.is_file():protected[str(f.resolve())]=sha(f)
    unchanged(protected)
    if (OUT/'protected_inputs_before.json').exists():
        need(completing and json.loads((OUT/'protected_inputs_before.json').read_text())==protected,
             'protection snapshot changed')
    else:save(OUT/'protected_inputs_before.json',protected)
    B=CASE/'evidence/preparation_B.json'
    B_SHA='2e55f3369f9445e7763ee1f9a87c57f79348d1b332c959bc038c1bcc4739081f'
    original,resources=runner.inspect(B,B_SHA);verify_zero_receipt(original)
    need(not (CASE/'launch_attempts').exists(),'existing formal attempt; no retry')
    active=[]
    for f in Path('/proc').iterdir():
        if not f.name.isdigit():continue
        try:args=(f/'cmdline').read_bytes().decode(errors='replace').strip('\0').split('\0')
        except OSError:continue
        if args and (Path(args[0]).name=='urv_reference' or 'scripts/run_S2.py' in args):
            active.append(dict(pid=int(f.name),argv=args))
    need(not active,'related process already running')
    session='urv_s2_formal_reuse_v1_20261102_01'
    sessions=subprocess.run(['tmux','list-sessions','-F','#{session_name}'],capture_output=True,text=True)
    need(sessions.returncode in (0,1) and session not in sessions.stdout.splitlines(),'session occupied')
    ldd=subprocess.run(['/usr/bin/ldd',original['provenance']['native_binary']],capture_output=True,text=True,check=True)
    ldd_name='ldd_clean_after_correction.txt' if completing else 'ldd_clean.txt'
    with (OUT/ldd_name).open('x') as stream:stream.write(ldd.stdout)
    libs=json.loads(Path(original['provenance']['build_environment']).read_text())['dynamic_library_sha256']
    paths={str(Path(m.group(1)).resolve()) for line in ldd.stdout.splitlines() if (m:=re.search(r'(/[^\s]+)',line))}
    need('not found' not in ldd.stdout and paths==set(libs),'runtime library closure mismatch');unchanged(libs)
    perf=ROOT/'docs/reports/URV_S2_perf_results_review_20261102'
    perf_review=json.loads((perf/'independent_review.json').read_text())
    need(perf_review['both_directions_independently_sufficient'] is True,'PERF prerequisite absent')
    perf_raw=json.loads((perf/'raw_evidence_sha256.json').read_text());unchanged(perf_raw)
    scope=ROOT/'docs/reports/URV_S2_formal_scope_resource_protocol_20261102'
    scope_data=json.loads((scope/'decision.json').read_text())
    need(scope_data['candidate_prepared_run_ids']==original['prepared_run_ids'],'FRD scope mismatch')
    precheck_name='precheck_after_correction.json' if completing else 'precheck.json'
    save(OUT/precheck_name,dict(checked_at=__import__('datetime').datetime.now().astimezone().isoformat(),
        B_sha256=B_SHA,B_inputs=len(original['inputs_sha256']),resources=resources,
        MemAvailable_GiB=resources['MemAvailable_bytes']/1024**3,disk_free_GiB=resources['disk_free_bytes']/1024**3,
        runtime_libraries_sha256=libs,formal_directories_pristine=True,active_processes=active,
        target_session_available=True,formal_launch_attempt_exists=False,solver_executed=False))
    question='是否现在采用 S2-FRD-v1 并授权完整六条正式 S2：按 5/2.5/1.25 nm、每档 P→T 顺序，单条时限各为 1/4/12 小时，验收通过才继续，失败即停？这表示第四条通过后会自动进入细网格，接受细网格可能在 12 小时内未完成的风险；求解预算合计 34 小时，检查和文件处理另计。本次只让我生成合同和一条命令，由你手动启动，不授权自动重跑或 S3。'
    answer='现在采用并授权正式六条；生成合同和命令，由我手动启动'
    auth=CASE/'evidence/S2_formal_authorization_reuse_v1_20261102_01.json'
    now=__import__('datetime').datetime.now().astimezone().isoformat()
    authorization=dict(recorded_at=now,authorization_source='reply_to_async_question',
        question_item_id='["request_user_input_async","call_20478990c1e340edac12dd55467c2e24",0]',
        question_verbatim=question,answer_verbatim=answer,user_instruction_verbatim=answer,
        verbatim_recorded_from_typed_sentence=False,user_explicitly_authorized=True,
        stage='S2_REG_GRID',adopted_resource_protocol='S2-FRD-v1',formal_simulation_authorized=True,
        approved_run_ids=original['prepared_run_ids'],AI_may_start_solver=False,user_manually_starts=True,
        automatic_retry_authorized=False,automatic_extension_authorized=False,S3_authorized=False,
        fourth_to_fifth_automatic_on_acceptance_understood=True,fine_12h_completion_not_guaranteed_understood=True,
        solver_budget_hours=34,checker_and_IO_additional=True)
    if auth.exists():
        prior_auth=json.loads(auth.read_text())
        need(completing and all(prior_auth.get(k)==v for k,v in authorization.items() if k!='recorded_at'),
             'existing authorization differs; refusing overwrite')
    else:save(auth,authorization)
    data=copy.deepcopy(original);inputs=data['inputs_sha256']
    def include(path,digest=None):
        path=str(Path(path).resolve());observed=sha(path)
        need(digest is None or observed==digest,'referenced evidence drift')
        need(path not in inputs or inputs[path]==observed,'conflicting evidence closure')
        inputs[path]=observed
    include(B,B_SHA);include(B.with_suffix('.sha256'));include(auth)
    perf_release=ROOT/'CASE/unseen_v2_reference_S2_perf_v1/evidence/S2_perf_launch_release_v1_20261102_01.json'
    include(perf_release,'b675010adcc9e57627d3ff39c93d72394e16489e3713abe09851d5de31c5c7e1')
    for path,digest in json.loads(perf_release.read_text())['inputs_sha256'].items():include(path,digest)
    for path,digest in perf_raw.items():include(path,digest)
    for folder in [perf,scope,old]:
        for path in folder.rglob('*'):
            if path.is_file():include(path)
    include(OUT/'precheck.json');include(OUT/'ldd_clean.txt')
    if completing:
        include(OUT/precheck_name);include(OUT/ldd_name)
    data.update(kind='AUTHORIZED_EXECUTION_LAUNCH_RELEASE',released_at=now,
        simulation_authorized=True,formal_simulation_authorized=True,
        native_zero_step_authorized=False,performance_time_stepping_authorized=False,
        approved_runs=data['prepared_runs'],approved_run_ids=data['prepared_run_ids'],actual_formal_run_ids=[],
        preparation_B_path=str(B),preparation_B_sha256=B_SHA,
        launch_authorization=dict(user_explicitly_authorized=True,user_instruction_verbatim=answer),
        launch_authorization_evidence=dict(path=str(auth),sha256=sha(auth)),
        adopted_resource_protocol=dict(id='S2-FRD-v1',path=str(scope/'PROTOCOL.md'),sha256=sha(scope/'PROTOCOL.md')),
        performance_prerequisite=dict(path=str(perf/'independent_review.json'),sha256=sha(perf/'independent_review.json'),
            outcome='BOTH_DIRECTIONS_PERF_EVIDENCE_SUFFICIENT'),performance_status='COMPLETED_INDEPENDENTLY_SUFFICIENT',
        AI_may_start_solver=False,user_manually_starts=True,automatic_retry_authorized=False,
        automatic_extension_authorized=False,S3_authorized=False,
        execution_environment_prefix=['env','-u','LD_LIBRARY_PATH','-u','LD_PRELOAD'])
    release=CASE/'evidence/S2_formal_launch_release_reuse_v1_20261102_01.json'
    unchanged(inputs);save(release,data);digest=sha(release)
    checked,available=runner.inspect(release,digest);binding(release,digest);validate_formal_authority(checked)
    with release.with_suffix('.json.sha256').open('x') as stream:stream.write(digest+'\n')
    output=io.StringIO()
    with patch('subprocess.Popen',side_effect=AssertionError('NO REAL PROCESS ALLOWED')),\
         patch.object(sys,'argv',['run_S2.py','--release',str(release),'--release-sha256',digest]),contextlib.redirect_stdout(output):
        need(runner.main()==0,'default readonly entry failed')
    (OUT/'release_readonly.stdout.txt').write_text(output.getvalue())
    bad=False
    try:binding(release,'0'*64)
    except ValueError:bad=True
    need(bad,'wrong external SHA accepted')
    require_pristine(checked['prepared_runs']);unchanged(protected)
    need(not (CASE/'launch_attempts').exists(),'readonly inspection created launch artifacts')
    save(OUT/'release_verification.json',dict(checked_at=now,FORMAL_BINDING_CHECK_PASS=True,
        release_path=str(release),release_sha256=digest,inputs=len(inputs),source_files_unchanged=len(protected),
        formal_authorization_evidence_path=str(auth),formal_authorization_evidence_sha256=sha(auth),
        approved_run_ids=data['approved_run_ids'],actual_formal_run_ids=[],default_readonly_exit_code=0,
        wrong_external_SHA_rejected=True,formal_simulation_authorized=True,AI_may_start_solver=False,
        solver_calls=0,VTK_reader_calls=0,builds=0,no_launch_attempts=True,reference_qualified=False))
    logfile=CASE/'evidence/S2_formal_controller_reuse_v1_20261102_01.log';need(not logfile.exists(),'log exists')
    program=shlex.join(['env','-u','LD_LIBRARY_PATH','-u','LD_PRELOAD','/home/dell/miniconda3/bin/python3',
        '-B','scripts/run_S2.py','--release',str(release),'--release-sha256',digest,'--execute'])
    inner='cd '+shlex.quote(str(CASE))+' && exec '+program+' > '+shlex.quote(str(logfile))+' 2>&1'
    command='tmux new-session -d -s '+session+' '+shlex.quote(inner)
    (OUT/'START_COMMAND.txt').write_text(command+'\n')
    save(OUT/'command_binding.json',dict(command=command,session=session,controller_log_path=str(logfile),
        release_path=str(release),release_sha256=digest,command_generated=True,command_executed=False,
        actual_formal_run_ids=[],tmux_started_by_AI=False))
    print(json.dumps(dict(release_sha256=digest,inputs=len(inputs),protected_files=len(protected),
        resources=resources,solver_executed=False,command_generated_not_executed=True)))


if __name__=='__main__':main()
