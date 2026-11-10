#!/usr/bin/env python3
"""Record the user's authorization and prepare/validate a release; never solve."""
from pathlib import Path
import copy
import datetime
import hashlib
import importlib.util
import json
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CASE = ROOT / 'CASE/unseen_v2_reference_S0_mrp_v1_a1'
PREPARED = CASE / 'evidence/S0_prepared_binding_A1_20261102_01.json'
PREPARED_SHA = 'd58019c2843454ce0ec1b2548e83fb6af66f4081d20acd54b695d665c916766c'
RELEASE = CASE / 'evidence/S0_launch_release_A1_20261102_01.json'
AUTH = CASE / 'evidence/S0_launch_authorization_A1_20261102_01.json'
USER_WORDING = '在授权 A1 的沿槽、横槽两条 S0，只让我生成正式合同和启动命令，由我手动运行'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    assert not RELEASE.exists() and not AUTH.exists(), 'Never overwrite a release/authorization'
    assert sha(PREPARED) == PREPARED_SHA
    original = json.loads(PREPARED.read_text())
    protected = json.loads((ROOT / 'docs/reports/URV_A1_launch_binding_review_20261102/protected_inputs_before.json').read_text())
    protected.update(original['inputs_sha256'])
    for path in (ROOT / 'docs/reports/URV_A1_launch_binding_review_20261102').rglob('*'):
        if path.is_file():
            protected[str(path)] = sha(path)
    for path in (PREPARED, PREPARED.with_suffix('.sha256'), CASE / 'S0_A1_PREPARATION_20261102.md'):
        protected[str(path)] = sha(path)
    assert all(sha(path) == digest for path, digest in protected.items())
    save(OUT / 'protected_inputs_before.json', protected)
    for name in ('SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md'):
        with (OUT / ('before_' + name)).open('xb') as stream:
            stream.write((ROOT / 'docs/reports' / name).read_bytes())
    assert not (CASE / 'launch_attempts').exists()
    assert all({path.name for path in Path(record['output_directory']).iterdir()} ==
               {'run_config.txt', 'run_manifest.txt'} for record in original['prepared_runs'])
    tmux = subprocess.run(['tmux', 'list-sessions', '-F', '#{session_name}'], capture_output=True, text=True)
    assert 'urv_s0_a1_20261102_01' not in tmux.stdout.splitlines(), 'Session already exists'
    save(OUT / 'tmux_prelaunch_snapshot.json', dict(exit_code=tmux.returncode, stdout=tmux.stdout, stderr=tmux.stderr))
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    authorization = dict(
        recorded_at_utc=now, user_instruction_verbatim=USER_WORDING,
        interpretation='Present affirmative authorization for the exact A1 P/T S0 pair; AI generates release and command only; user manually starts.',
        simulation_authorized=True, approved_run_ids=original['prepared_run_ids'],
        authorized_AI_actions=['read-only checks', 'create separate execution binding', 'deliver one startup command'],
        AI_may_start_solver=False, user_manually_starts=True, automatic_retry_authorized=False,
        S1_or_other_runs_authorized=False, historical_v12_authorization_reused=False,
        conditional_contradiction_ruling='GPT-6 Astra | High if a new instruction or evidence contradiction appears',
        prepared_binding_file=str(PREPARED), prepared_binding_sha256=PREPARED_SHA)
    save(AUTH, authorization)
    bound = copy.deepcopy(original)
    bound.update(binding_id='URV-S0-A1-LAUNCH-20261102-01', kind='AUTHORIZED_EXECUTION_LAUNCH_RELEASE',
                 status='AUTHORIZED_FOR_USER_MANUAL_START_NOT_STARTED', simulation_authorized=True,
                 approved_run_ids=copy.deepcopy(original['prepared_run_ids']),
                 approved_runs=copy.deepcopy(original['prepared_runs']),
                 prepared_binding_file=str(PREPARED), prepared_binding_sha256=PREPARED_SHA,
                 release_created_at_utc=now)
    bound['launch_authorization'] = dict(user_explicitly_authorized=True,
        user_instruction_verbatim=USER_WORDING, authorization_evidence_file=str(AUTH),
        authorization_evidence_sha256=sha(AUTH), AI_may_start_solver=False,
        user_manually_starts=True, automatic_retry_authorized=False,
        S1_or_other_runs_authorized=False)
    for path in (AUTH, PREPARED, PREPARED.with_suffix('.sha256')):
        bound['inputs_sha256'][str(path)] = sha(path)
    save(RELEASE, bound)
    digest = sha(RELEASE)
    with RELEASE.with_suffix('.sha256').open('x') as stream:
        stream.write(digest + '  ' + RELEASE.name + '\n')
    # Import only Python validation. Never call the controller's execute/main.
    spec = importlib.util.spec_from_file_location('A1_launch_readonly', CASE / 'scripts/run_S0_A1.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    checked, resources = module.inspect(RELEASE, digest)
    validated = module.binding(RELEASE, digest)
    assert checked == validated == bound
    assert bound['approved_runs'] == bound['prepared_runs']
    assert bound['launch_authorization']['user_instruction_verbatim'] == USER_WORDING
    differences = [key for key in sorted(original.keys() | bound.keys()) if original.get(key) != bound.get(key)]
    expected_changes = {'binding_id', 'kind', 'status', 'simulation_authorized', 'approved_run_ids',
        'approved_runs', 'prepared_binding_file', 'prepared_binding_sha256', 'release_created_at_utc',
        'launch_authorization', 'inputs_sha256'}
    assert set(differences) == expected_changes
    assert all(bound['inputs_sha256'][path] == value for path, value in original['inputs_sha256'].items())
    save(OUT / 'release_field_changes.json', dict(changed_top_level_fields=differences,
        original_input_count=len(original['inputs_sha256']), launch_input_count=len(bound['inputs_sha256']),
        original_input_hashes_preserved=True, approved_records_equal_prepared=True))
    argv = ['/home/dell/miniconda3/bin/python3', '-B', 'scripts/run_S0_A1.py',
            '--release', str(RELEASE.relative_to(CASE)), '--release-sha256', digest, '--execute']
    inner = 'cd ' + shlex.quote(str(CASE)) + ' && exec ' + shlex.join(argv)
    command = shlex.join(['tmux', 'new-session', '-d', '-s', 'urv_s0_a1_20261102_01', inner])
    syntax = subprocess.run(['/bin/bash', '-n'], input=command + '\n', text=True, capture_output=True)
    assert syntax.returncode == 0
    assert shlex.split(command)[-1] == inner
    with (OUT / 'START_COMMAND.txt').open('x') as stream:
        stream.write(command + '\n')
    assert all(sha(path) == value for path, value in protected.items())
    assert not (CASE / 'launch_attempts').exists()
    assert all({path.name for path in Path(record['output_directory']).iterdir()} ==
               {'run_config.txt', 'run_manifest.txt'} for record in bound['approved_runs'])
    save(OUT / 'verification.json', dict(status='AUTHORIZED_RELEASE_VALIDATED_USER_START_PENDING',
        created_at_utc=now, release_file=str(RELEASE), release_sha256=digest,
        launch_input_count=len(bound['inputs_sha256']), all_input_hashes_match=True,
        prepared_binding_unchanged=True, protected_existing_files_unchanged=len(protected),
        read_only_inspect_pass=True, immutable_binding_validator_pass=True,
        resources_snapshot=resources, command_syntax_check_exit=syntax.returncode,
        command_executed=False, native_calls_this_task=0, native_rebuilds=0,
        source_checker_threshold_changes=False, prior_software_tests_rerun=False,
        simulation_authorized=True, approved_run_ids=bound['approved_run_ids'],
        launch_attempts_exists=False, S0_started=False, run_directories_pristine=True,
        S0='HOLD_PENDING_FORMAL_REGRESSION_AND_REPLAY', NUMERICAL_GATE='NOT_EVALUATED',
        RESULT_PASS=False, geometry_PASS=None, S1_started=False,
        reference_qualified=False, strict_error_bound_established=False, submission_ready=False,
        historical_exclusive_attribution='NOT_ESTABLISHED', new_contradiction_detected=False,
        new_Astra_ruling_invoked=False))
    print(json.dumps(dict(release_sha256=digest, input_count=len(bound['inputs_sha256']),
        protected_files=len(protected), resources=resources, native_calls=0)))


if __name__ == '__main__':
    main()
