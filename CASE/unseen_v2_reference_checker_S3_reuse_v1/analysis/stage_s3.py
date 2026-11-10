"""S3 identity/authority checks only. Scientific acceptance remains unchanged."""
from pathlib import Path
import json
from evidence import need, sha, kv

CASE = Path(__file__).resolve().parents[2] / 'unseen_v2_reference_S3_reuse_v1'
STAGE = 'S3_REG_LINEARITY'
REVISION = 'URV-S3-S1-ELF-REUSE-v1'
ELF_SHA = '5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b'
AUDIT_ID = 'URV_S3_ZERO_20261103_01'
MODES = ('describe', 'precheck', 'initialize')
CASES = tuple(f'URV1_U_REG_{d}_dx2p5_a{a}' for a in (50000, 200000) for d in ('P', 'T'))
RUN_IDS = tuple(f'URV_S3_{d}_a{a}_reuse_v1_20261103_01' for a in (50000, 200000) for d in ('P', 'T'))
RESOURCES = dict(processes=1, threads=1, cuboids=1, overlap=3,
    per_process_address_space_GiB=8, required_available_RAM_GiB=12,
    required_initial_free_disk_GiB=100, required_before_each_run_free_disk_GiB=8,
    output_budget_GiB_per_case=4,
    solver_wall_cap_seconds_by_dx_nm={'2.5': 14400})


def unchanged(inputs):
    need(isinstance(inputs, dict) and inputs, 'empty input closure')
    current = {p: sha(p) for p in inputs}
    need(current == inputs, 'bound input drift')
    return current


def validate_records(bound, checker_case):
    from contracts import approved_records
    need(bound.get('stage') == STAGE, 'S3 stage only')
    need(bound.get('performance_time_stepping_authorized') is False and
         bound.get('automatic_retry_authorized') is False and bound.get('automatic_extension_authorized') is False and
         bound.get('S4_authorized') is False and bound.get('S5_authorized') is False, 'S3 disallows performance/retry/extension/next stage')
    records = bound.get('approved_runs') or bound.get('prepared_runs')
    need(isinstance(records, list) and len(records) == 4, 'exact four S3 identities required')
    need([r.get('planned_case_id') for r in records] == list(CASES), 'S3 exact case order required')
    need([r.get('run_id') for r in records] == list(RUN_IDS), 'S3 prepared identity changed')
    need(bound.get('resources') == RESOURCES, 'S3 per-grid resource contract changed')
    projection = dict(bound, approved_runs=records, approved_run_ids=[r['run_id'] for r in records])
    approved_records(projection, checker_case)
    for r in records:
        need(Path(r['output_directory']) == CASE / 'runs' / r['run_id'] / 'steady', 'S3 output isolation violation')
        need(not Path(r['output_directory']).is_symlink(), 'S3 run symlink refused')
    return records


def bound_file(bound, path, digest):
    from contracts import covered
    path = covered(str(path), bound['inputs_sha256'])
    need(sha(path) == digest, 'required evidence SHA mismatch')
    return path


def explicit_authority(bound, key, evidence_key):
    auth = bound.get(key, {})
    need(auth.get('user_explicitly_authorized') is True and
         isinstance(auth.get('user_instruction_verbatim'), str) and auth['user_instruction_verbatim'].strip(),
         'explicit scoped user authorization missing')
    evidence = bound.get(evidence_key, {})
    path = bound_file(bound, evidence.get('path', ''), evidence.get('sha256'))
    recorded = json.loads(path.read_text())
    need(recorded.get('user_instruction_verbatim') == auth['user_instruction_verbatim'] and
         recorded.get('user_explicitly_authorized') is True, 'authorization evidence mismatch')
    return recorded


def verify_zero_receipt(bound):
    receipt = bound_file(bound, bound.get('zero_audit_path', ''), bound.get('zero_audit_sha256'))
    need(receipt == CASE / 'audits' / AUDIT_ID / 'verification.json', 'wrong S3 zero receipt path')
    audit = json.loads(receipt.read_text())
    need(audit.get('audit_id') == AUDIT_ID and audit.get('ZERO_STEP_AUDIT_PASS') is True and
         audit.get('binary_sha256') == ELF_SHA and audit.get('actual_time_steps') == 0 and
         audit.get('steady_mode_invocations') == 0, 'S3 four-configuration zero audit incomplete')
    need(audit.get('native_describe') == audit.get('native_precheck') == audit.get('native_initialize') == 4 and
         audit.get('initialized_frames_read') == 4, 'S3 zero audit counts incomplete')
    release = bound_file(bound, audit['audit_release_path'], audit['audit_release_sha256'])
    released = verify_seal(release, audit['audit_release_sha256'])
    validate_zero_authority(released)
    records = audit.get('records', [])
    need([(r.get('planned_case_id'), r.get('mode')) for r in records] ==
         [(c, m) for c in CASES for m in MODES], 'S3 zero audit coverage changed')
    need(all(r.get('native_exit_code') == 0 and r.get('collide_and_stream_calls') == 0 for r in records),
         'S3 zero call failed or advanced')
    for r in records:
        if r['mode'] == 'initialize':
            field = bound_file(bound, r['field_readback'], r['field_readback_sha256'])
            value = json.loads(field.read_text())
            need(value.get('PASS') is True and value.get('actual_reader') is True and len(value['frames']) == 1,
                 'S3 initial field not independently read')
    manifest = bound_file(bound, audit['raw_manifest_path'], audit['raw_manifest_sha256'])
    for path, digest in json.loads(manifest.read_text()).items():
        need(Path(path).resolve().is_relative_to(CASE / 'audits' / AUDIT_ID), 'zero output escape')
        bound_file(bound, path, digest)
    expected_files = json.loads(manifest.read_text())
    folder = CASE / 'audits' / AUDIT_ID
    actual_files = {str(p): sha(p) for p in folder.rglob('*') if p.is_file() and p not in (manifest, receipt)}
    need(actual_files == expected_files, 'zero raw manifest file set/content mismatch')
    return audit


def validate_zero_plan(bound):
    need(bound.get('prepared_run_ids') == list(RUN_IDS), 'zero requires exact formal identity plan')
    records = bound.get('zero_prepared_runs', [])
    need([(r.get('planned_case_id'), r.get('mode')) for r in records] ==
         [(c, m) for c in CASES for m in MODES], 'exact twelve zero identities required')
    formal = {r['planned_case_id']: kv(r['run_config_path']) for r in bound['prepared_runs']}
    for r in records:
        expected_id = f'ZERO_{AUDIT_ID}_{r["planned_case_id"]}_{r["mode"]}'
        expected_run = CASE / 'audits' / AUDIT_ID / r['planned_case_id'] / r['mode']
        need(r['run_id'] == expected_id and Path(r['output_directory']) == expected_run,
             'zero output or identity escape')
        path = bound_file(bound, r['run_config_path'], r['run_config_sha256'])
        need(path == expected_run / 'run_config.txt', 'zero config location mismatch')
        expected = dict(formal[r['planned_case_id']], mode=r['mode'], run_id=expected_id,
                        output_directory=str(expected_run))
        need(kv(path) == expected, 'zero audit physics or mode differs from formal input')
        manifest = bound_file(bound, expected_run / 'run_manifest.txt',
                              bound['inputs_sha256'].get(str(expected_run / 'run_manifest.txt')))
        need(kv(manifest) == dict(run_id=expected_id, mode=r['mode']), 'zero manifest mismatch')
    return records


def validate_zero_authority(bound):
    need(bound.get('kind') == 'AUTHORIZED_ZERO_STEP_AUDIT_RELEASE' and
         bound.get('native_zero_step_authorized') is True and
         bound.get('simulation_authorized') is False and bound.get('formal_simulation_authorized') is False and
         bound.get('performance_time_stepping_authorized') is False and
         bound.get('approved_runs') == bound.get('approved_run_ids') == [], 'separate zero-only release required')
    need(bound.get('stage') == STAGE and bound.get('resources') == RESOURCES, 'zero stage/resources changed')
    original = bound_file(bound, bound.get('preparation_A_path', ''), bound.get('preparation_A_sha256'))
    need(original == CASE / 'evidence/preparation_A.json', 'zero must bind original S3 preparation A')
    prepared = json.loads(original.read_text())
    need(prepared.get('kind') == 'S3_PREPARATION_A_NOT_AUTHORIZATION' and
         prepared.get('simulation_authorized') is False and prepared.get('native_zero_step_authorized') is False,
         'A seal contains execution authority')
    need(all(bound['inputs_sha256'].get(p) == h for p, h in prepared['inputs_sha256'].items()),
         'zero release drops or changes A inputs')
    need(bound.get('prepared_runs') == prepared['prepared_runs'] and
         bound.get('zero_prepared_runs') == prepared['zero_prepared_runs'], 'zero release changes identities')
    records = validate_zero_plan(bound)
    ids = [r['run_id'] for r in records]
    need(bound.get('approved_audit_run_ids') == ids, 'all twelve exact audit IDs must be covered')
    recorded = explicit_authority(bound, 'audit_authorization', 'audit_authorization_evidence')
    need(recorded.get('stage') == STAGE and recorded.get('native_zero_step_authorized') is True and
         recorded.get('formal_simulation_authorized') is False and
         recorded.get('performance_time_stepping_authorized') is False and
         recorded.get('approved_audit_run_ids') == ids, 'authorization does not cover exactly S3 zero audit')


def validate_formal_authority(bound):
    need(bound.get('kind') == 'AUTHORIZED_EXECUTION_LAUNCH_RELEASE' and
         bound.get('simulation_authorized') is True and
         bound.get('formal_simulation_authorized') is True and bound.get('native_zero_step_authorized') is False, 'formal S3 release required')
    need(bound.get('approved_runs') == bound.get('prepared_runs') and
         bound.get('approved_run_ids') == bound.get('prepared_run_ids') == list(RUN_IDS),
         'formal S3 identities differ from preparation')
    recorded = explicit_authority(bound, 'launch_authorization', 'launch_authorization_evidence')
    need(recorded.get('stage') == STAGE and recorded.get('formal_simulation_authorized') is True and
         recorded.get('approved_run_ids') == list(RUN_IDS), 'authorization does not cover formal four-case S3')
    prepared_path = bound_file(bound, bound.get('preparation_B_path', ''), bound.get('preparation_B_sha256'))
    need(prepared_path == CASE / 'evidence/preparation_B.json', 'formal S3 must bind the real B seal')
    prepared = json.loads(prepared_path.read_text())
    need(prepared.get('kind') == 'S3_PREPARATION_B_NOT_AUTHORIZATION' and
         prepared.get('simulation_authorized') is False and prepared.get('zero_audit_status') == 'PASSED',
         'B seal is not completed zero-audit preparation')
    need(all(bound['inputs_sha256'].get(p) == h for p, h in prepared['inputs_sha256'].items()),
         'formal release drops or changes B inputs')
    need(bound.get('prepared_runs') == prepared.get('prepared_runs') and
         bound.get('zero_audit_path') == prepared.get('zero_audit_path') and
         bound.get('zero_audit_sha256') == prepared.get('zero_audit_sha256'),
         'formal release differs from B identities or zero receipt')
    verify_zero_receipt(bound)


def verify_seal(path, expected_sha):
    path = Path(path).resolve()
    need(sha(path) == expected_sha, 'external preparation SHA mismatch')
    data = json.loads(path.read_text())
    need(data.get('protocol_id') == 'URV-v1' and data.get('stage') == STAGE and
         data.get('addendum_id') == REVISION, 'S3 preparation identity mismatch')
    unchanged(data['inputs_sha256'])
    need(data.get('author_external_data_history_confirmation') == 'CONFIRMED', 'author history declaration missing')
    author = bound_file(data, data['author_reply_file'], data['author_reply_sha256'])
    need(json.loads(author.read_text())['status'] == 'AUTHOR_DECLARED_NONUSE_CONFIRMED', 'history declaration scope')
    from contracts import verify_provenance
    verify_provenance(data)
    if data.get('kind') in ('S3_PREPARATION_A_NOT_AUTHORIZATION', 'S3_PREPARATION_B_NOT_AUTHORIZATION'):
        need(all(data.get(k) is False for k in ('simulation_authorized','formal_simulation_authorized','native_zero_step_authorized','performance_time_stepping_authorized')), 'preparation contains execution authority')
        need(data.get('approved_run_ids') == data.get('approved_runs') == data.get('approved_audit_run_ids') == [], 'preparation contains approved identities')
    need(data.get('prepared_run_ids') == list(RUN_IDS), 'S3 prepared IDs mismatch')
    validate_records(data, Path(__file__).resolve().parents[1])
    return data


def require_pristine(records):
    for r in records:
        run = Path(r['output_directory'])
        need(not run.is_symlink() and {p.name for p in run.iterdir()} == {'run_config.txt', 'run_manifest.txt'},
             'output already used; no restart or overwrite')
        manifest = kv(run / 'run_manifest.txt')
        cfg = kv(r['run_config_path'])
        need(cfg['run_id'] == manifest['run_id'] == r['run_id'] and cfg['mode'] == manifest['mode'],
             'native config/manifest mismatch')
