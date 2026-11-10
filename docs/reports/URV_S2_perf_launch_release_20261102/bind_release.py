"""Record the received user authority and bind it; never start a solver/tmux job."""
from pathlib import Path
import contextlib
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from unittest.mock import patch

ROOT=Path('/home/dell/yuanyuanxu/SIM240')
CASE=ROOT/'CASE/unseen_v2_reference_S2_perf_v1'
OUT=Path(__file__).resolve().parent
sys.path[:0]=[str(CASE/'analysis'),str(CASE/'scripts')]
import perf_contract as c
import run_perf as runner


def main():
    for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        target=OUT/('before_'+name)
        c.need(not target.exists(),'this binding report already exists')
        target.write_bytes((ROOT/'docs/reports'/name).read_bytes())
    prior=ROOT/'docs/reports/URV_S2_perf_launch_binding_review_20261102'
    protected=c.load(prior/'protected_inputs_before.json')
    for p in prior.rglob('*'):
        if p.is_file():protected[str(p.resolve())]=c.sha(p)
    c.unchanged(protected)
    c.save(OUT/'protected_inputs_before.json',protected)
    prep=CASE/'evidence/preparation_perf.json'
    prep_sha='806c40a62620396faf6795008a81b25f7f9bf4182869b6df4422b575b2b08030'
    data=runner.inspect(prep,prep_sha)
    runner.environment()
    resources=runner.resources(Path(data['prepared_benchmark_runs'][0]['output_directory']))
    runner.resource_guard(resources,True)
    markers={n:(CASE/n).exists() for n in
             ['performance_attempt.json','performance_execution.lock','performance_batch_result.json']}
    c.need(not any(markers.values()),'execution marker exists')
    active=[]
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():continue
        try:args=(path/'cmdline').read_bytes().decode(errors='replace').strip('\0').split('\0')
        except OSError:continue
        if args and (Path(args[0]).name=='urv_reference' or str(CASE/'scripts/run_perf.py') in args):
            active.append(dict(pid=int(path.name),executable=Path(args[0]).name))
    c.need(not active,'native/performance process already active')
    session='urv_s2_perf_v1_20261102_01'
    tmux=shutil.which('tmux');c.need(tmux,'tmux unavailable')
    sessions=subprocess.run([tmux,'list-sessions','-F','#{session_name}'],capture_output=True,text=True)
    c.need(sessions.returncode in (0,1) and session not in sessions.stdout.splitlines(),'session occupied')
    dynamic=subprocess.run(['/usr/bin/ldd',data['native_binary']],capture_output=True,text=True,check=True)
    (OUT/'ldd_clean.txt').write_text(dynamic.stdout)
    paths={str(Path(hit.group(1)).resolve()) for line in dynamic.stdout.splitlines()
           if (hit:=re.search(r'(/[^\s]+)',line))}
    libraries=c.load(data['native_build_environment'])['dynamic_library_sha256']
    c.need('not found' not in dynamic.stdout and paths==set(libraries),'loader dependency closure changed')
    c.unchanged(libraries)
    precheck=dict(checked_at=c.now(),preparation_sha256=prep_sha,preparation_inputs=len(data['inputs_sha256']),
        resources=resources,MemAvailable_GiB=resources['MemAvailable_bytes']/1024**3,
        disk_free_GiB=resources['disk_free_bytes']/1024**3,resources_pass=True,
        loader_overrides_unset=not os.environ.get('LD_LIBRARY_PATH') and not os.environ.get('LD_PRELOAD'),
        dynamic_library_sha256=libraries,active_processes=active,execution_markers=markers,
        target_tmux_session_available=True,solver_executed=False)
    c.save(OUT/'precheck.json',precheck)
    auth=CASE/'evidence/S2_perf_authorization_v1_20261102_01.json'
    question='是否现在授权 S2 的沿槽 P、横槽 T 两条 1.25 nm 有限性能推进：每条启动起最多 1800 秒，或首次观察到完整诊断 step≥2048 即停止，以先到者为准；P 证据不足或异常时不进入 T？本次只让我生成正式绑定合同和一条命令，由你本人手动启动，不包含正式 S2 计算。'
    answer='现在授权两条有限性能推进；生成合同和命令，由我手动启动'
    c.save(auth,dict(recorded_at=c.now(),authorization_source='reply_to_async_question',
        question_item_id='["request_user_input_async","call_f02c82b439174d8e88811c959f7b4bb8",0]',
        question_verbatim=question,answer_verbatim=answer,user_instruction_verbatim=answer,
        verbatim_recorded_from_typed_sentence=False,user_explicitly_authorized=True,
        performance_time_stepping_authorized=True,formal_simulation_authorized=False,
        approved_benchmark_run_ids=c.IDS,AI_may_start_native=False,user_manually_starts=True,
        automatic_retry_authorized=False,budget=data['budget'],purpose=c.PURPOSE))
    data['inputs_sha256'].update({str(prep):prep_sha,str(prep.with_suffix('.json.sha256')):
        c.sha(prep.with_suffix('.json.sha256')),str(auth):c.sha(auth)})
    c.need(len(data['inputs_sha256'])==2058,'unexpected release closure size')
    data.update(kind=c.RELEASE,released_at=c.now(),preparation_path=str(prep),preparation_sha256=prep_sha,
        performance_time_stepping_authorized=True,approved_benchmark_run_ids=c.IDS,
        approved_benchmark_runs=data['prepared_benchmark_runs'],
        performance_authorization=dict(path=str(auth),sha256=c.sha(auth)),
        execution_environment_prefix=['env','-u','LD_LIBRARY_PATH','-u','LD_PRELOAD'],
        launch_control='user manual only; no automatic retry, continuation or formal S2')
    release=CASE/'evidence/S2_perf_launch_release_v1_20261102_01.json'
    c.save(release,data);digest=c.sha(release)
    checked=runner.inspect(release,digest);c.authorize(checked)
    with release.with_suffix('.json.sha256').open('x') as stream:stream.write(digest+'\n')
    stdout=io.StringIO()
    argv=['run_perf.py','--release',str(release),'--expected-sha256',digest]
    with patch('subprocess.Popen',side_effect=AssertionError('NO SOLVER/EXTERNAL PROCESS PERMITTED')),\
         patch.object(sys,'argv',argv),contextlib.redirect_stdout(stdout):
        c.need(runner.main()==0,'default readonly release check failed')
    (OUT/'release_readonly.stdout.txt').write_text(stdout.getvalue())
    # Wrong external SHA is rejected before any authority/launch path.
    rejected=False
    try:runner.inspect(release,'0'*64)
    except ValueError:rejected=True
    c.need(rejected,'wrong SHA accepted')
    c.pristine(checked['prepared_benchmark_runs']);c.unchanged(protected)
    c.need(not any((CASE/name).exists() for name in markers),'readonly check created execution markers')
    c.save(OUT/'release_verification.json',dict(checked_at=c.now(),AUTHORIZED_PERFORMANCE_BINDING_PASS=True,
        release_path=str(release),release_sha256=digest,release_input_count=len(data['inputs_sha256']),
        real_authorization_evidence_sha256=c.sha(auth),authorization_source='reply_to_async_question',
        performance_time_stepping_authorized=True,formal_simulation_authorized=False,
        approved_benchmark_run_ids=c.IDS,actual_benchmark_run_ids=[],AI_may_start_native=False,
        user_manually_starts=True,wrong_external_SHA_rejected=True,default_readonly_exit_code=0,
        native_calls=0,VTK_reader_calls=0,time_steps=0,builds=0,no_execution_markers=True,
        protected_files_unchanged=len(protected),**c.SCIENCE))
    native_command=shlex.join(['env','-u','LD_LIBRARY_PATH','-u','LD_PRELOAD',
        '/home/dell/miniconda3/bin/python3','-B','scripts/run_perf.py',
        '--release',str(release),'--expected-sha256',digest,'--execute'])
    logfile=CASE/'evidence/S2_perf_controller_v1_20261102_01.log'
    c.need(not logfile.exists(),'controller logfile already exists')
    inner='cd '+shlex.quote(str(CASE))+' && exec '+native_command+' > '+shlex.quote(str(logfile))+' 2>&1'
    command='tmux new-session -d -s '+session+' '+shlex.quote(inner)
    # Parse text only. Never feed the generated command to a shell/tmux.
    tokens=shlex.split(command);c.need(tokens[:4]==['tmux','new-session','-d','-s'],'command shape')
    (OUT/'START_COMMAND.txt').write_text(command+'\n')
    c.save(OUT/'command_binding.json',dict(session=session,command=command,
        release_path=str(release),release_sha256=digest,controller_log_path=str(logfile),
        command_generated=True,command_executed=False,tmux_session_started_by_AI=False,
        authorization_kind=c.RELEASE,actual_benchmark_run_ids=[]))
    print(json.dumps(dict(release_sha256=digest,inputs=2058,resources=precheck,
                         native_calls=0,command_generated_not_executed=True),ensure_ascii=False))


if __name__=='__main__':main()
