"""Create a separately authorized S0 launch release; never execute the solver."""
from pathlib import Path
from datetime import datetime
import copy
import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
REPORT = Path(__file__).resolve().parent
CASE = ROOT / 'CASE/unseen_v2_reference_S0_v1_2'
CHECKER = ROOT / 'CASE/unseen_v2_reference_checker_v1_2'
sys.path.insert(0, str(CHECKER / 'analysis'))
from evidence import need, sha, save
from check_results import binding


def main():
    prepared = CASE / 'evidence/S0_prepared_binding.json'
    expected = 'a836c5f4368ed5d80d1a585abde3a353848d4555094ba2556b14fd3d883cb846'
    need(sha(prepared) == expected, 'prepared trust anchor changed')
    source = json.loads(prepared.read_text())
    need(source['simulation_authorized'] is False and source['approved_run_ids'] == [],
         'preserve the inactive preparation snapshot')
    need(not (CASE / 'launch_attempts').exists(), 'launch marker already present')
    for record in source['prepared_runs']:
        need({p.name for p in Path(record['output_directory']).iterdir()} ==
             {'run_config.txt', 'run_manifest.txt'}, 'run directory no longer pristine')
    need(all(sha(p) == digest for p, digest in source['inputs_sha256'].items()), 'input drift')
    session = 'urv_s0_v1_2_20261101_01'
    need(shutil.which('tmux'), 'tmux unavailable')
    tmux_version = subprocess.check_output(['tmux', '-V'], text=True).strip()
    check_session = subprocess.run(['tmux', 'has-session', '-t', '=' + session],
                                  capture_output=True, text=True)
    need(check_session.returncode == 1, 'session exists or tmux session check failed')
    authorization = REPORT / 'user_launch_authorization.json'
    reply = '现在授权两条 S0；生成合同和命令，由我手动启动'
    save(authorization, dict(recorded_at_local=datetime.now().astimezone().isoformat(),
        source='actual_user_async_reply',
        question_item_id='["request_user_input_async","call_0f657e98d39e487c8f8c708d58361009",0]',
        question_verbatim='请明确这条消息是否表示：现在授权 S0 两条 h75 回归，只让我生成启动合同和一条命令，由你手动执行？现有封存中的启动授权仍为关闭；“获准启动后”是条件表述，需要有明确原话才能写入真实授权合同。',
        answer_verbatim=reply, approved_run_ids=source['prepared_run_ids'],
        stage='S0_REGRESSION', user_starts_manually=True,
        agent_solver_execution_authorized=False, future_stages_authorized=False,
        automatic_retry_authorized=False))
    release = copy.deepcopy(source)
    release.update(binding_id='URV-S0-LAUNCH-v1.2-20261101-01',
        kind='AUTHORIZED_S0_LAUNCH_RELEASE_USER_START_ONLY',
        status='AUTHORIZED_COMMAND_PREPARED_NOT_STARTED', simulation_authorized=True,
        approved_run_ids=copy.deepcopy(source['prepared_run_ids']),
        approved_runs=copy.deepcopy(source['prepared_runs']),
        source_prepared_binding=str(prepared), source_prepared_binding_sha256=expected,
        launch_authorization=dict(user_explicitly_authorized=True,
            user_instruction_verbatim=reply, authorization_record_path=str(authorization),
            authorization_record_sha256=sha(authorization), user_starts_manually=True,
            agent_solver_execution_authorized=False, next_stage_authorized=False))
    for p in [prepared, prepared.with_suffix('.sha256'), authorization, Path(__file__).resolve()]:
        release['inputs_sha256'][str(p.resolve())] = sha(p)
    releasepath = CASE / 'evidence/S0_launch_release_20261101_01.json'
    save(releasepath, release)
    digest = sha(releasepath)
    releasepath.with_suffix('.sha256').write_text(digest + '  ' + releasepath.name + '\n')
    # Validate the real authorization/provenance/identity release layer only.
    # Neither check_run nor execute is called; there are no completed results.
    bound = binding(releasepath, digest)
    need(bound['approved_runs'] == source['prepared_runs'], 'identity map differs')
    runner = CASE / 'scripts/run_S0.py'
    python = '/home/dell/miniconda3/bin/python3'
    environment = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
    check = subprocess.run([python, '-B', str(runner), '--release', str(releasepath),
        '--release-sha256', digest], capture_output=True, text=True, timeout=60, env=environment)
    (REPORT / 'launch_readonly_check.log').write_text(check.stdout + check.stderr)
    need(check.returncode == 0, 'launch read-only validation failed')
    resource_snapshot = json.loads(check.stdout)['resources_snapshot']
    process_command = [python, '-B', 'scripts/run_S0.py', '--release',
                       'evidence/' + releasepath.name, '--release-sha256', digest, '--execute']
    inner = ('cd ' + shlex.quote(str(CASE)) + ' && exec ' + shlex.join(process_command)
             + ' >> evidence/S0_launch_console_20261101_01.log 2>&1')
    command = shlex.join(['tmux', 'new-session', '-d', '-s', session, inner])
    (REPORT / 'launch_command.txt').write_text(command + '\n')
    need(shlex.split(command)[:5] == ['tmux', 'new-session', '-d', '-s', session], 'tmux argv')
    # Parse syntax only. This does not create a tmux session or run the command.
    syntax = subprocess.run(['/bin/bash', '-n', '-c', command], capture_output=True, text=True)
    need(syntax.returncode == 0, 'command shell syntax invalid')
    need(sha(prepared) == expected, 'original prepared binding was changed')
    need(not (CASE / 'launch_attempts').exists(), 'unexpected launch marker')
    for record in source['prepared_runs']:
        need({p.name for p in Path(record['output_directory']).iterdir()} ==
             {'run_config.txt', 'run_manifest.txt'}, 'unexpected solver output')
    save(REPORT / 'verification.json', dict(
        checked_at_local=datetime.now().astimezone().isoformat(),
        prepared_binding_sha256=expected, prepared_inputs_match=len(source['inputs_sha256']),
        launch_release_path=str(releasepath), launch_release_sha256=digest,
        launch_inputs_match=len(release['inputs_sha256']),
        real_user_authorization_record=str(authorization), user_reply_preserved_verbatim=True,
        approved_records_identical_to_prepared=True, approved_run_ids=bound['approved_run_ids'],
        public_binding_validation_passed=True, readonly_runner_exit=check.returncode,
        resources_snapshot=resource_snapshot, resource_thresholds_met_at_check=True,
        tmux_version=tmux_version, target_session_exists=False,
        command_bash_syntax_exit=syntax.returncode,
        command_saved=str(REPORT / 'launch_command.txt'), command_executed_by_agent=False,
        tmux_session_created_by_agent=False, native_solver_called=False,
        S0_started=False, actual_formal_run_ids=[],
        next_stage_authorized=False, native_recompile_this_turn=False,
        new_numerical_or_physical_validation=False))
    print(json.dumps(dict(launch_release_sha256=digest,
        prepared_inputs_match=len(source['inputs_sha256']),
        launch_inputs_match=len(release['inputs_sha256']), readonly_exit=check.returncode,
        resources_snapshot=resource_snapshot, S0_started=False)))


if __name__ == '__main__':
    main()
