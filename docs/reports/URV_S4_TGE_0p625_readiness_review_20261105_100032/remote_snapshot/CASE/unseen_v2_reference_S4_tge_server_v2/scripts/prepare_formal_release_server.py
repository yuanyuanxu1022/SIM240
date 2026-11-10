"""Issue the formal 0.625 nm supplement release. Records the user answer verbatim. Never runs.

Run this on the server, after preparation_S exists.
"""
from pathlib import Path
import json, os, shutil, subprocess, sys

CASE = Path(__file__).resolve().parents[1]
CHECKER = CASE.parent / 'unseen_v2_reference_checker_S4_tge_server_v2'
sys.path.insert(0, str(CHECKER / 'analysis'))

import server_stage as s  # noqa: E402
from evidence import need, sha  # noqa: E402

EV = CASE / 'evidence'
PREP = EV / 'preparation_S.json'
RELEASE = EV / 'S4_TGE_SERVER_formal_launch_release_v2_20261104_01.json'
AUTH = EV / 'S4_TGE_SERVER_formal_authorization_v2_20261104_01.json'
DECISION = EV / 'S4_TGE_SERVER_formal_resource_decision_v2_20261104_01.json'

QUESTION = ('是否授权在服务器 10.103.102.55 的 yuanyuan 账户内，用已封存的服务器版准备 S 与同一构建，'
            '运行 0.625 nm 横槽补充算例（单个稳态算例，run_id URV_S4_T_dx0p625_TGESRV_v2_20261104_01），'
            '作为薄间隙横槽网格加密的最后一档，并以其结果与原始 5/2.5 nm 点及 1.25 nm 基准配对？'
            '同时采用以下资源：单进程地址空间 64 GiB、可用内存前置 80 GiB、'
            '首批空闲磁盘 200 GiB（之后每次 20 GiB）、单次输出上限 16 GiB、'
            '求解墙钟上限 96 小时、独立检查上限 1 小时；失败即停、不重试、不加时；'
            '不包含性能标定独立报告或 S5。')
ANSWER = ('授权在服务器 55 的 yuanyuan 账户跑 0.625 nm 横槽补证算例（长算，需 tmux 后台），'
          '墙钟止损 96 小时')

RESOURCES = dict(processes=1, threads=1, cuboids=1, overlap=3,
                 per_process_address_space_GiB=64,
                 required_available_RAM_GiB=80,
                 required_initial_free_disk_GiB=200,
                 required_before_each_run_free_disk_GiB=20,
                 output_budget_GiB_per_run=16,
                 solver_wall_cap_seconds=96 * 3600,
                 checker_wall_cap_seconds=3600,
                 automatic_retry=False, automatic_extension=False)

RUN_ID = s.RUN_0P625


def write_new(path, value):
    path = Path(path)
    need(not path.exists(), 'refusing overwrite: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    return path


def main():
    need(PREP.is_file(), 'preparation_S.json missing; prepare first')
    need(not RELEASE.exists(), 'formal release already exists')
    prep = s.verify_seal(PREP, (EV / 'preparation_S.json.sha256').read_text().strip())
    s.require_pristine(prep)

    stamp = s.now()
    mem = int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines()
                   if l.startswith('MemAvailable:'))) * 1024
    disk = shutil.disk_usage(CASE).free
    host = subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip()
    snapshot_value = dict(
        kind='RESOURCE_SNAPSHOT_AT_FORMAL_ISSUANCE_NOT_RESERVATION', sampled_at=stamp,
        host=host, available_RAM_GiB=round(mem / 1024**3, 4), disk_free_GiB=round(disk / 1024**3, 3),
        load_average=Path('/proc/loadavg').read_text().split()[:3],
        note='The formal entry re-checks memory and disk before the run and stops without retry.')
    snapshot = write_new(CASE / 'launch_attempts_precheck/resource_snapshot.json', snapshot_value)

    auth = write_new(AUTH, dict(
        kind='USER_AUTHORIZATION_EVIDENCE', recorded_at=stamp,
        authorization_source='user_message_in_session',
        user_explicitly_authorized=True,
        authorization_question_verbatim=QUESTION, user_instruction_verbatim=ANSWER,
        selected_answer_verbatim=ANSWER,
        authorization_recording_note='The user message is preserved verbatim. The question text above was '
                                     'composed by the assistant and was not sent as a separate prompt; scope is '
                                     'defined by the user message read against the sealed plan, not by an '
                                     'unanswered option list.',
        stage=s.STAGE, revision=s.REVISION,
        preparation_S_path=str(PREP), preparation_S_sha256=sha(PREP),
        formal_simulation_authorized=True, simulation_authorized=True,
        native_zero_step_authorized=False, initial_field_readback_authorized=False,
        performance_time_stepping_authorized=False, S5_authorized=False,
        automatic_retry_authorized=False, automatic_extension_authorized=False,
        approved_run_ids=[RUN_ID], approved_runs_scope='exactly one steady run, 0.625 nm transverse',
        explicitly_excluded=['separate performance-calibration report', 'S5',
                             'automatic retry', 'automatic time extension'],
        failure_policy='STOP_WITHOUT_RETRY',
        execution_account='yuanyuan on 10.103.102.55',
        AI_may_start_solver=False, user_manually_starts=True))

    decision = write_new(DECISION, dict(
        kind='USER_RESOURCE_DECISION_EVIDENCE', recorded_at=stamp, stage=s.STAGE, revision=s.REVISION,
        user_explicitly_authorized=True, user_instruction_verbatim=ANSWER,
        resource_decision_accepted=True, resources=RESOURCES,
        scope='ONE 0.625 nm TRANSVERSE SUPPLEMENT RUN ON THE LAB SERVER',
        rationale=['measured 0.625 nm peak RSS is 10.69 GiB locally; 64 GiB leaves ample room',
                   'the 0.625 nm grid has 16,515,072 fluid nodes, 8x the 1.25 nm baseline',
                   'the 96 hour wall cap is a stop-loss, not a prediction'],
        limits_are_not_results=['64 GiB is RLIMIT_AS, not measured RSS',
                                'the wall cap is a stop-loss, not an expected duration',
                                'the local 10.69 GiB peak was measured at precheck, not at steady run'],
        automatic_adaptation_authorized=False))

    inputs = dict(prep['inputs_sha256'])
    extra = [auth, decision, snapshot, PREP, EV / 'preparation_S.json.sha256',
             CHECKER / 'analysis/check_formal_server.py',
             CASE / 'scripts/run_formal_server.py',
             CASE / 'scripts/prepare_formal_release_server.py']
    added = {}
    for p in extra:
        p = Path(p)
        if p.is_file():
            key = s.key_for(p.resolve())
            if key not in inputs:
                inputs[key] = sha(p)
                added[key] = sha(p)

    one = next(r for r in prep['prepared_runs'] if r['run_id'] == RUN_ID)
    release = dict(prep)
    release.update(dict(
        kind='AUTHORIZED_S4_TGE_SERVER_FORMAL_RELEASE',
        release_id='URV_S4_TGE_SERVER_FORMAL_LAUNCH_v2_20261104_01',
        released_at=stamp,
        simulation_authorized=True, formal_simulation_authorized=True,
        native_zero_step_authorized=False, initial_field_readback_authorized=False,
        performance_time_stepping_authorized=False,
        automatic_retry_authorized=False, automatic_extension_authorized=False, S5_authorized=False,
        approved_runs=[one], approved_run_ids=[RUN_ID],
        actual_run_ids=[], actual_audit_run_ids=[], actual_formal_run_ids=[],
        preparation_S_path=str(PREP), preparation_S_sha256=sha(PREP),
        formal_authorization=dict(path=str(auth), sha256=sha(auth)),
        formal_resource_decision=dict(path=str(decision), sha256=sha(decision)),
        launch_authorization=dict(user_explicitly_authorized=True, user_instruction_verbatim=ANSWER),
        launch_authorization_evidence=dict(path=str(auth), sha256=sha(auth)),
        formal_resources=RESOURCES,
        formal_solver_wall_cap_seconds=RESOURCES['solver_wall_cap_seconds'],
        formal_checker_cap_seconds=RESOURCES['checker_wall_cap_seconds'],
        source_binary_sha256=s.load(EV / 'build_environment.json')['binary_sha256'],
        resource_snapshot=dict(path=str(snapshot), sha256=sha(snapshot)),
        resource_precondition_at_issuance=('MET' if mem >= 80 * 1024**3 and disk >= 200 * 1024**3
                                           else 'NOT_MET'),
        inputs_sha256=inputs))

    write_new(RELEASE, release)
    digest = sha(RELEASE)
    (EV / (RELEASE.name + '.sha256')).write_text(digest + '\n')
    print(json.dumps(dict(release=str(RELEASE), sha256=digest, inputs=len(inputs),
                          added=len(added), approved_run_ids=release['approved_run_ids'],
                          resources=RESOURCES,
                          available_RAM_GiB=snapshot_value['available_RAM_GiB'],
                          disk_free_GiB=snapshot_value['disk_free_GiB'],
                          precondition=release['resource_precondition_at_issuance']), indent=2))


if __name__ == '__main__':
    main()
