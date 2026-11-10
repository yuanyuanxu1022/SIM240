"""Build the S4-TGE 3+1 zero-step execution binding. Never runs the solver."""
import json, os, shutil, subprocess, sys, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path('/home/dell/yuanyuanxu/SIM240')
CASE = ROOT / 'CASE/unseen_v2_reference_S4_tge_v1'
CHECKER = ROOT / 'CASE/unseen_v2_reference_checker_S4_tge_v1'
PARENT_CHECKER = ROOT / 'CASE/unseen_v2_reference_checker_S4_reuse_v1'
REPORT = ROOT / 'docs/reports/URV_S4_TGE_zero_binding_20261104_165506'
REVIEW = ROOT / 'docs/reports/URV_S4_TGE_A_readonly_review_20261104_160058'
A = CASE / 'evidence/preparation_A.json'
A_SHA = '53e544543ae26402a0d0fac7a7b3294e0a2286e7a7d4c336ce08e91abf53bfb9'
AUDIT_ID = 'URV_S4_TGE_ZERO_v1_20261104_01'
CASE_ID = 'URV1_U_THIN_T_dx0p625_a100000_SUPPLEMENT'
STAGE = 'S4_T_TRANSVERSE_GRID_SUPPLEMENT'
REVISION = 'S4-TGE-PREP-v1'
RELEASE_NAME = 'S4_TGE_zero_launch_release_v1_20261104_01.json'
AUTH_NAME = 'S4_TGE_zero_authorization_v1_20261104_01.json'
DECISION_NAME = 'S4_TGE_zero_resource_decision_v1_20261104_01.json'
ZERO_RESOURCES = dict(processes=1, threads=1, cuboids=1, overlap=3,
    per_process_address_space_GiB=8, required_available_RAM_GiB=12,
    required_initial_free_disk_GiB=100, required_before_each_call_free_disk_GiB=8,
    output_budget_GiB_per_call=4, native_call_cap_seconds=300, field_reader_cap_seconds=300)
QUESTION = ('准备 A 的只读复核已通过。是否现在授权 T／0.625 nm 的3次原生零步调用（describe、precheck、initialize，推进0步）'
            '及1次初态场读取，并采用以下限制：每次原生或读取最多300秒，每个受限进程地址空间上限 8 GiB，可用内存前置12 GiB，'
            '首批空闲磁盘100 GiB、之后8 GiB，单次输出上限4 GiB；失败即停、不重试？本次仅让我在重核封存和届时资源后生成独立合同与一条命令，'
            '由你本人手动启动；不包含性能推进、正式计算或S5。终止清理和文件核对另计。')
ANSWER = '现在授权3＋1并采用上述限制；生成合同和命令，由我手动启动'
TZ = timezone(timedelta(hours=8))

sys.path.insert(0, str(CHECKER / 'analysis'))
from tge_stage import sha, load, verify_seal, require_pristine  # noqa: E402


def write_new(path, value):
    path = Path(path)
    assert not path.exists(), 'refusing overwrite: %s' % path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    return path


def now():
    return datetime.now(TZ).isoformat()


def meminfo():
    out = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.split(':')[0] in ('MemTotal', 'MemAvailable', 'SwapTotal', 'SwapFree'):
            out[line.split(':')[0]] = int(line.split()[1]) * 1024
    return out


def main():
    stamp = now()
    prepared = load(A)
    assert sha(A) == A_SHA, 'preparation A changed'
    verify_seal(A, A_SHA)
    require_pristine(prepared)

    # ---- 1. resource snapshot at issuance (read only) ----
    mem = meminfo()
    disk = shutil.disk_usage(CASE).free
    load_avg = Path('/proc/loadavg').read_text().split()[:3]
    ps = subprocess.run(['bash', '-c', "ps -eo pid,rss,etime,comm,args | grep -iE 'urv|pvpython|paraview' | grep -v grep || true"],
                        capture_output=True, text=True)
    tmux = subprocess.run(['bash', '-c', 'tmux ls 2>&1; echo "rc=$?"'], capture_output=True, text=True)
    snapshot = dict(kind='RESOURCE_SNAPSHOT_AT_ZERO_ISSUANCE_NOT_RESERVATION', stage=STAGE, sampled_at=stamp,
        host='dell-OptiPlex-Tower-Plus-7010', meminfo_bytes=mem, disk_free_bytes=disk,
        disk_free_GiB=round(disk / 1024**3, 3), available_RAM_GiB=round(mem['MemAvailable'] / 1024**3, 4),
        load_average_1_5_15=[float(x) for x in load_avg],
        conflicting_solver_processes=ps.stdout.strip() or 'NONE',
        tmux_query=tmux.stdout.strip(),
        memory_floor_met_now=mem['MemAvailable'] >= 12 * 1024**3,
        disk_floor_met_now=disk >= 100 * 1024**3,
        note='Point-in-time reading, not a reservation; the zero entry re-checks before every call and stops without retry.')
    snap_path = write_new(REPORT / 'resource_snapshot.json', snapshot)

    env_check = subprocess.run(['bash', '-c', 'ldd /home/dell/yuanyuanxu/SIM240/CASE/unseen_v2_reference_S1_a1_v1/build/urv_reference; echo "rc=$?"'],
                               capture_output=True, text=True)
    write_new(REPORT / 'native_ldd_at_issuance.txt', env_check.stdout + env_check.stderr)
    env_path = REPORT / 'native_ldd_at_issuance.txt'

    # ---- 2. actual user authorization (verbatim) ----
    zero_ids = [r['run_id'] for r in prepared['zero_prepared_runs']]
    folder = CASE / 'audits' / AUDIT_ID
    reads = [dict(planned_case_id=CASE_ID,
                  initialization_run_id=zero_ids[2],
                  initialization_directory=str(CASE / 'audits' / AUDIT_ID / CASE_ID / 'initialize'),
                  field_readback_path=str(folder / ('field_readback_' + CASE_ID + '.json')))]
    auth = dict(kind='USER_AUTHORIZATION_EVIDENCE', recorded_at=stamp,
        authorization_source='user_reply_to_request_user_input_async',
        user_explicitly_authorized=True,
        user_instruction_verbatim=ANSWER, authorization_question_verbatim=QUESTION,
        selected_answer_verbatim=ANSWER, verbatim_recorded_from_typed_sentence=False,
        authorization_recording_note='Actual selected answer preserved verbatim; the complete question plus that answer define the scope. No fabricated expanded sentence.',
        stage=STAGE, revision=REVISION, audit_id=AUDIT_ID,
        preparation_A_path=str(A), preparation_A_sha256=A_SHA,
        native_zero_step_authorized=True, initial_field_readback_authorized=True,
        native_call_count=3, initial_field_read_count=1, actual_time_steps=0,
        allowed_native_modes=['describe', 'precheck', 'initialize'],
        native_call_wall_cap_seconds=300, field_read_wall_cap_seconds=300,
        failure_policy='STOP_WITHOUT_RETRY', fail_stop_no_retry=True, approved_audit_run_ids=zero_ids,
        approved_initial_field_reads=reads, approved_run_ids=[], approved_runs=[],
        simulation_authorized=False, formal_simulation_authorized=False,
        performance_time_stepping_authorized=False, S5_authorized=False,
        automatic_retry_authorized=False, automatic_extension_authorized=False,
        AI_may_start_solver=False, user_manually_starts=True,
        explicitly_excluded=['performance_time_stepping', 'formal_simulation', 'S5'],
        note='Termination cleanup and file verification are accounted separately; no whole-batch 20-minute guarantee.')
    auth_path = write_new(CASE / 'evidence' / AUTH_NAME, auth)

    # ---- 3. adopted resource decision ----
    decision = dict(kind='USER_RESOURCE_DECISION_EVIDENCE', recorded_at=stamp, stage=STAGE, revision=REVISION,
        audit_id=AUDIT_ID, user_explicitly_authorized=True, user_instruction_verbatim=ANSWER,
        resource_decision_accepted=True, resources=ZERO_RESOURCES,
        resource_scope='ONE_LIMITED_FAIL_STOP_ZERO_AUDIT_ATTEMPT_ONLY',
        limits_are_not_results=['per_process_address_space_8GiB is RLIMIT_AS, not measured RSS or whole-tree total',
                                '300s are per-call wait budgets; termination/cleanup/hash/file checks excluded',
                                '4x300s is not a whole-batch completion promise',
                                'no claim that 16515072 nodes plus the initial field read fit inside 8GiB'],
        automatic_adaptation_authorized=False,
        note='Adopted verbatim from the user answer; any change of limit requires a new explicit user decision.')
    decision_path = write_new(CASE / 'evidence' / DECISION_NAME, decision)

    # ---- 4. release = A inputs + new immutable inputs ----
    extra = [A, A.with_suffix('.sha256'), auth_path, decision_path, snap_path, env_path,
             REPORT / 'prepare_zero_release_tge.py',
             REVIEW / 'REPORT.md', REVIEW / 'verification.json', REVIEW / 'binding_plan.json',
             REVIEW / 'disposition.json', REVIEW / 'final_integrity.json', REVIEW / 'document_manifest.json',
             REVIEW / 'review_intake.json', REVIEW / 'review_intake_validation.json']
    inputs = dict(prepared['inputs_sha256'])
    added = {}
    for p in extra:
        assert p.is_file() and not p.is_symlink(), 'bad extra input %s' % p
        h = sha(p)
        assert inputs.get(str(p)) in (None, h), 'extra input conflicts with A closure: %s' % p
        if str(p) not in inputs:
            inputs[str(p)] = h
            added[str(p)] = h

    review_evidence = {str(p): sha(p) for p in extra if str(p).startswith(str(REVIEW))}
    release = dict(prepared)
    release.update(dict(
        kind='AUTHORIZED_S4_TGE_ZERO_RELEASE',
        release_id='URV_S4_TGE_ZERO_LAUNCH_v1_20261104_01',
        released_at=stamp,
        native_zero_step_authorized=True,
        initial_field_readback_authorized=True,
        zero_audit_status='AUTHORIZED_NOT_EXECUTED',
        approved_audit_run_ids=zero_ids,
        approved_initial_field_reads=reads,
        approved_run_ids=[], approved_runs=[],
        actual_audit_run_ids=[], actual_formal_run_ids=[],
        preparation_A_path=str(A), preparation_A_sha256=A_SHA,
        zero_authorization=dict(path=str(auth_path), sha256=sha(auth_path)),
        zero_resource_decision=dict(path=str(decision_path), sha256=sha(decision_path)),
        audit_authorization=dict(user_explicitly_authorized=True, user_instruction_verbatim=ANSWER),
        audit_authorization_evidence=dict(path=str(auth_path), sha256=sha(auth_path)),
        zero_execution_scope=dict(native_call_count=3, initial_field_read_count=1,
            allowed_modes=['describe', 'precheck', 'initialize'], maximum_time_steps=0,
            native_call_wall_cap_seconds=300, field_read_wall_cap_seconds=300,
            fail_stop_no_retry=True, failure_policy='STOP_WITHOUT_RETRY', whole_batch_duration_guaranteed=False),
        resource_snapshot=dict(path=str(snap_path), sha256=sha(snap_path)),
        resource_precondition_at_issuance=('MET' if snapshot['memory_floor_met_now'] and snapshot['disk_floor_met_now'] else 'NOT_MET'),
        resource_precondition_note=('At issuance the 12GiB available-memory floor was not satisfied, so this command must only be run after the pre-check passes; '
                                    'the zero entry itself re-checks and stops before any write if the floor is unmet.'),
        review_evidence=review_evidence,
        review_report=str(REVIEW / 'REPORT.md'),
        process_environment_requirements=dict(unset=['LD_LIBRARY_PATH', 'LD_PRELOAD'],
            OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
            QT_QPA_PLATFORM='offscreen', PYTHONDONTWRITEBYTECODE='1'),
        controller_interpreter=dict(path='/home/dell/miniconda3/bin/python3',
            symlink_target='/home/dell/miniconda3/bin/python3.14', sha256=sha(Path('/home/dell/miniconda3/bin/python3')),
            note='recorded for provenance only; symlink path is not part of the immutable closure'),
        reader_interpreter=dict(path='/usr/bin/pvpython', symlink_target='/usr/bin/pvpython3.12',
            sha256=sha(Path('/usr/bin/pvpython3.12')),
            note='recorded for provenance only; symlink path is not part of the immutable closure'),
        inputs_sha256=inputs,
    ))
    rel_path = write_new(CASE / 'evidence' / RELEASE_NAME, release)
    digest = sha(rel_path)
    (CASE / 'evidence' / (RELEASE_NAME + '.sha256')).write_text(digest + '\n')

    summary = dict(kind='ZERO_RELEASE_BUILD_SUMMARY', built_at=stamp,
        release_path=str(rel_path), release_sha256=digest,
        inherited_A_inputs=len(prepared['inputs_sha256']), added_inputs=len(added),
        total_inputs=len(inputs), added_input_paths=sorted(added),
        authorization=dict(path=str(auth_path), sha256=sha(auth_path)),
        resource_decision=dict(path=str(decision_path), sha256=sha(decision_path)),
        resource_precondition_at_issuance=release['resource_precondition_at_issuance'],
        available_RAM_GiB=snapshot['available_RAM_GiB'], disk_free_GiB=snapshot['disk_free_GiB'],
        solver_executed=False, native_calls=0, VTK_calls=0)
    write_new(REPORT / 'build_summary.json', summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
