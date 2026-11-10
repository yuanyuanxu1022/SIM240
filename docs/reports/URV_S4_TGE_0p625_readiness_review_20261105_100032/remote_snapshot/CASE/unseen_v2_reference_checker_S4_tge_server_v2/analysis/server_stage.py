"""Server-lineage TGE preparation and zero-only authority.

All paths are derived from this file's location and bound inputs are stored as
paths RELATIVE to the project root, so the same seal is portable across hosts
that share the same relative layout.  This module never executes a program.
"""
from pathlib import Path
import datetime, json, re, sys

CHECKER = Path(__file__).resolve().parents[1]
CASE = CHECKER.parent / 'unseen_v2_reference_S4_tge_server_v2'
ROOT = CASE.parents[1]
REF = CASE / 'reference'
sys.path.insert(0, str(CHECKER / 'analysis'))
from evidence import need, sha, kv, exact_parameters, geometry  # noqa: E402

STAGE = 'S4_T_TRANSVERSE_GRID_SUPPLEMENT_SERVER'
REVISION = 'S4-TGE-SERVER-v2'

RUN_1P25 = 'URV_S4_T_dx1p25_TGESRV_v2_20261104_01'
RUN_0P625 = 'URV_S4_T_dx0p625_TGESRV_v2_20261104_01'
CASE_1P25 = 'URV1_U_THIN_T_dx1p25_a100000_TGESRV'
CASE_0P625 = 'URV1_U_THIN_T_dx0p625_a100000_TGESRV'
AUDIT_ID = 'URV_S4_TGE_SRV_ZERO_v2_20261104_01'
MODES = ('describe', 'precheck', 'initialize')

# Cross-build lineage: what the LOCAL build already established.
LOCAL_A_SHA = '53e544543ae26402a0d0fac7a7b3294e0a2286e7a7d4c336ce08e91abf53bfb9'
LOCAL_1P25_COMPLETION = '2599a496cefb3a1836313a52c201fdbd6ba954adc6143dcb1a11a17ad1de069a'
LOCAL_1P25_K = 3.471791836744987e-24
LOCAL_T_MEDIUM_FINE = 0.013283870347425175      # 1.3283870347 percent, the standing FAIL
BUILD_EQUIVALENCE_RTOL = 1e-6                    # declared before any server measurement

# PROPOSED zero-audit resources for THIS host.  Not adopted by the user and not
# authorized.  The local 8 GiB cap is known to be too small (bad_alloc at
# 16,515,072 fluid nodes), so this proposal is deliberately generous: the audit
# should MEASURE real usage instead of failing on the cap.
SERVER_RESOURCES = dict(
    processes=1, threads=1, cuboids=1, overlap=3,
    per_process_address_space_GiB=64,
    required_available_RAM_GiB=80,
    required_initial_free_disk_GiB=200,
    required_before_each_call_free_disk_GiB=20,
    output_budget_GiB_per_call=16,
    native_call_cap_seconds=900,
    field_reader_cap_seconds=900)

FLAGS = ('simulation_authorized', 'formal_simulation_authorized', 'native_zero_step_authorized',
         'initial_field_readback_authorized', 'performance_time_stepping_authorized',
         'automatic_retry_authorized', 'automatic_extension_authorized', 'S5_authorized')

_FRAME = '0,0.01,0.02,0.05,0.1,0.2,0.5,1,2,4,8'
_CONFIG_KEYS = {'mode', 'run_id', 'output_directory', 'direction', 'dx_nm', 'h_nm', 'd_nm',
                'w_nm', 'period_nm', 'Ly_nm', 'nu_m2_s', 'acceleration_m_s2',
                'window_tstar', 'max_time_H_diffusion', 'frame_tstar'}


def _physics(dx_nm):
    return dict(direction='T', dx_nm=dx_nm, h_nm='30.0', d_nm='80.0', w_nm='120',
                period_nm='240', Ly_nm='240', nu_m2_s='1e-06', acceleration_m_s2='100000',
                window_tstar='0.75', max_time_H_diffusion='8', frame_tstar=_FRAME)


PHYSICS = {'0.625': _physics('0.625'), '1.25': _physics('1.25')}


def load(path):
    return json.loads(Path(path).read_text())


def now():
    return datetime.datetime.now().astimezone().isoformat()


def canonical(path):
    path = Path(path)
    need(path.is_absolute() and path.is_file() and str(path) == str(path.resolve()),
         'missing/noncanonical input: ' + str(path))
    need(not any(q.is_symlink() for q in (path, *path.parents)), 'input symlink refused')
    return path


def rel_key(path):
    path = canonical(path)
    need(path.is_relative_to(ROOT), 'input outside project root: ' + str(path))
    return str(path.relative_to(ROOT))


def key_for(path):
    """Project files are keyed relatively; the OpenLB tree is keyed absolutely.

    The OpenLB checkout lives outside the project (usually ~/openlb), so it
    cannot be addressed relative to ROOT.  The seal records it under its
    absolute path and lists it in `external_roots`; that makes the seal
    host-bound, which `unchanged` asserts explicitly.
    """
    path = canonical(path)
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def resolve_key(bound, key):
    return canonical(ROOT / key) if not key.startswith('/') else canonical(Path(key))


def covered(bound, path):
    path = canonical(path)
    key = key_for(path)
    need(bound['inputs_sha256'].get(key) == sha(path), 'unbound/changed input: ' + str(path))
    return path


def unchanged(bound):
    inputs = bound.get('inputs_sha256')
    need(isinstance(inputs, dict) and inputs, 'empty input closure')
    need(bound.get('root') == str(ROOT), 'project root moved; seal is host-bound')
    roots = bound.get('external_roots') or []
    need(all(Path(r).is_dir() for r in roots), 'recorded external root missing')
    for key, digest in inputs.items():
        need(re.fullmatch('[0-9a-f]{64}', digest) is not None, 'invalid input digest')
        need(not key.startswith('/') or any(key.startswith(r + '/') for r in roots),
             'absolute input outside the declared external roots: ' + key)
        need('..' not in Path(key).parts, 'input key escapes its root')
        need(sha(resolve_key(bound, key)) == digest, 'bound input drift: ' + key)


def physics(cfg):
    need(set(cfg) == _CONFIG_KEYS, 'candidate schema changed')
    need(cfg['dx_nm'] in PHYSICS, 'unknown grid spacing')
    need(all(cfg[k] == v for k, v in PHYSICS[cfg['dx_nm']].items()),
         'candidate physics/observation changed')
    return exact_parameters(cfg)


def validate_plan(bound):
    need(bound.get('stage') == STAGE and bound.get('revision') == REVISION, 'wrong server stage')
    formal = bound.get('prepared_runs', [])
    zeros = bound.get('zero_prepared_runs', [])
    need(len(formal) == 2 and len(zeros) == 3,
         'exactly two formal plans (1.25 baseline rerun, 0.625 supplement) and three zero plans required')

    expected = [
        (formal[0], RUN_1P25, CASE_1P25, 'steady', CASE / 'runs' / RUN_1P25 / 'steady'),
        (formal[1], RUN_0P625, CASE_0P625, 'steady', CASE / 'runs' / RUN_0P625 / 'steady'),
    ]
    expected += [(rec, 'ZERO_' + AUDIT_ID + '_' + mode, CASE_0P625, mode,
                  CASE / 'audits' / AUDIT_ID / CASE_0P625 / mode)
                 for rec, mode in zip(zeros, MODES)]

    for rec, run_id, case_id, mode, out in expected:
        need(rec == dict(run_id=run_id, planned_case_id=case_id, mode=mode,
                         output_directory=str(out),
                         run_config_path=str(out / 'run_config.txt'),
                         run_config_sha256=bound['inputs_sha256'].get(key_for(out / 'run_config.txt'))),
             'identity/order/output isolation changed')
        cfg = kv(covered(bound, rec['run_config_path']))
        physics(cfg)
        need(cfg['run_id'] == run_id and cfg['mode'] == mode
             and cfg['output_directory'] == str(out), 'config identity changed')
        need(kv(covered(bound, out / 'run_manifest.txt')) == dict(run_id=run_id, mode=mode),
             'manifest changed')

    need(bound.get('zero_resource_proposal') == SERVER_RESOURCES, 'server resource proposal changed')
    need(bound.get('reader_path') == str(CHECKER / 'analysis/read_fields.py'),
         'exact frozen field reader required')
    need(bound.get('original_S4_stage_accepted') is False and bound.get('reference_qualified') is False
         and bound.get('MODEL_COMPARISON') == 'NOT_EVALUATED'
         and bound.get('physical_validation') == 'NOT_EVALUATED'
         and bound.get('submission_ready') is False
         and bound.get('next_stage_started') is False, 'scientific status promoted')
    need(bound.get('NUMERICAL_GATE') == 'NOT_EVALUATED' and bound.get('RESULT_PASS') is False
         and bound.get('geometry_PASS') is None, 'unexecuted preparation promoted acceptance')
    need(bound.get('AI_may_start_solver') is False and bound.get('user_manually_starts') is True,
         'manual execution boundary changed')
    need(bound.get('proposed_grid_nm') == [2.5, 1.25, 0.625]
         and bound.get('original_grid_nm') == [5, 2.5, 1.25],
         'supplement overwrote the original grid family')
    if bound.get('kind') == 'S4_TGE_SERVER_PREPARATION_NOT_AUTHORIZATION':
        need(all(bound.get(k) is False for k in FLAGS),
             'this preparation interface forbids every execution flag')
        need(bound.get('formal_solver_wall_cap_seconds') is None
             and bound.get('formal_checker_cap_seconds') is None,
             'preparation must leave formal budgets undecided')
        need('formal_resources' not in bound, 'preparation must not carry formal resources')
    return zeros


def verify_lineage(bound):
    """The server build must be tied to what the local build already established."""
    lin = bound.get('lineage') or {}
    need(lin.get('kind') == 'CROSS_BUILD_LINEAGE_REFERENCE', 'lineage block missing')

    need(lin.get('local_preparation_A_sha256') == LOCAL_A_SHA
         and sha(covered(bound, REF / 'local_preparation_A.json')) == LOCAL_A_SHA,
         'local preparation A reference changed')
    covered(bound, REF / 'local_preparation_A.sha256')

    acc = load(covered(bound, REF / 'local_1p25_acceptance.json'))
    need(acc.get('run_id') == 'URV_S4_T_dx1p25_reuse_v1_20261103_01'
         and acc.get('direction') == 'T' and acc.get('dx_nm') == 1.25
         and acc.get('RESULT_PASS') is True and acc.get('NUMERICAL_GATE') == 'PASS'
         and acc.get('geometry_PASS') is True and acc.get('independent_exit_code') == 0,
         'local 1.25 nm baseline was not independently accepted')
    need(acc.get('completion_sha256') == LOCAL_1P25_COMPLETION,
         'local 1.25 nm completion fingerprint changed')
    need(abs(acc['scalar']['K_m3'] / LOCAL_1P25_K - 1) < 1e-12,
         'local 1.25 nm K value changed')

    grid = load(covered(bound, REF / 'local_S4_grid_report.json'))
    transverse = [d for d in grid['directions'] if d['direction'] == 'T'][0]
    need(grid.get('GRID_CHECKS_PASS') is False and transverse.get('GRID_CHECKS_PASS') is False,
         'original transverse grid FAIL erased')
    change = transverse['grid_estimate']['medium_fine_change']
    need(abs(change - LOCAL_T_MEDIUM_FINE) < 1e-15 and change > 0.01,
         'standing medium-fine FAIL value changed')

    review = load(covered(bound, REF / 'local_independent_review.json'))
    need(review.get('S4_STAGE_ACCEPTED') is False and review.get('S4_GRID_CHECKS_PASS') is False,
         'original stage-acceptance record changed')

    need(lin.get('build_equivalence_criterion') == dict(
        source_run_id='URV_S4_T_dx1p25_reuse_v1_20261103_01',
        reference_K_m3=LOCAL_1P25_K,
        relative_tolerance=BUILD_EQUIVALENCE_RTOL,
        applies_to_run_id=RUN_1P25,
        declared_before_measurement=True,
        on_failure='STOP; the two builds are not interchangeable and the 0.625 supplement '
                   'cannot be paired with the original 5/2.5 nm points'),
        'build equivalence criterion changed')


def verify_seal(path, digest):
    path = canonical(path)
    need(path.parent == CASE / 'evidence'
         and re.fullmatch('[0-9a-f]{64}', digest) is not None and sha(path) == digest,
         'external seal trust anchor/path mismatch')
    bound = load(path)
    need(bound.get('protocol_id') == 'URV-v1'
         and bound.get('schema_version') == 'S4-TGE-SERVER-1', 'wrong server preparation schema')
    unchanged(bound)
    validate_plan(bound)
    verify_lineage(bound)
    for tree in (CASE / 'scripts', CASE / 'common', CHECKER / 'analysis', CHECKER / 'tests'):
        for p in sorted(tree.rglob('*')):
            if p.is_file():
                covered(bound, p.resolve())
    if bound.get('kind') == 'S4_TGE_SERVER_PREPARATION_NOT_AUTHORIZATION':
        need(path == CASE / 'evidence/preparation_S.json', 'wrong preparation location')
        need(all(bound.get(k) is False for k in FLAGS), 'preparation contains execution authority')
        need(bound.get('approved_run_ids') == bound.get('approved_runs') == []
             and bound.get('approved_audit_run_ids') == []
             and bound.get('actual_audit_run_ids') == bound.get('actual_formal_run_ids') == [],
             'preparation contains fictitious approved/executed identities')
        need(bound.get('formal_solver_wall_cap_seconds') is None
             and bound.get('formal_checker_cap_seconds') is None,
             'preparation must leave formal budgets undecided')
        need('formal_resources' not in bound, 'preparation must not carry formal resources')
    elif bound.get('kind') == 'AUTHORIZED_S4_TGE_SERVER_ZERO_RELEASE':
        need(path == CASE / 'evidence/S4_TGE_SERVER_zero_launch_release_v2_20261104_01.json',
             'wrong zero release location')
        need(bound.get('formal_simulation_authorized') is False
             and bound.get('simulation_authorized') is False,
             'zero release must not carry formal authority')
        need(bound.get('approved_run_ids') == [] and bound.get('approved_runs') == [],
             'zero release must not approve formal runs')
    elif bound.get('kind') == 'AUTHORIZED_S4_TGE_SERVER_FORMAL_RELEASE':
        need(path == CASE / 'evidence/S4_TGE_SERVER_formal_launch_release_v2_20261104_01.json',
             'wrong formal release location')
        need(bound.get('native_zero_step_authorized') is False
             and bound.get('initial_field_readback_authorized') is False,
             'formal release must not carry zero-step authority')
        need(bound.get('automatic_retry_authorized') is False
             and bound.get('automatic_extension_authorized') is False
             and bound.get('S5_authorized') is False, 'formal release enables retry/extension/S5')
        need(isinstance(bound.get('approved_run_ids'), list) and bound['approved_run_ids'],
             'formal release must name the approved run ids')
        need([r['run_id'] for r in bound.get('approved_runs', [])] == bound['approved_run_ids'],
             'approved run ids and records disagree')
        need(all(r in bound['prepared_runs'] for r in bound['approved_runs']),
             'approved run is not part of the sealed plan')
        need(isinstance(bound.get('formal_resources'), dict)
             and bound['formal_resources'].get('solver_wall_cap_seconds'), 'formal budget undecided')
    else:
        need(False, 'unsupported release kind')
    return bound


def require_pristine(bound):
    for rec in bound['prepared_runs'] + bound['zero_prepared_runs']:
        out = Path(rec['output_directory'])
        need(not out.is_symlink()
             and {p.name for p in out.iterdir()} == {'run_config.txt', 'run_manifest.txt'},
             'output used; no retry/overwrite: ' + str(out))


def validate_zero_authority(bound, path):
    """Runs before every write/process in the zero entry."""
    need(bound.get('kind') == 'AUTHORIZED_S4_TGE_SERVER_ZERO_RELEASE'
         and bound.get('native_zero_step_authorized') is True
         and bound.get('initial_field_readback_authorized') is True,
         'separate explicit 3+1 authorization required')
    need(Path(path) == CASE / 'evidence/S4_TGE_SERVER_zero_launch_release_v2_20261104_01.json',
         'wrong zero release identity')
    original = covered(bound, CASE / 'evidence/preparation_S.json')
    prepared = load(original)
    need(bound.get('preparation_S_sha256') == sha(original), 'original preparation not bound')
    covered(bound, original.with_suffix('.sha256'))
    need(all(bound['inputs_sha256'].get(k) == v for k, v in prepared['inputs_sha256'].items()),
         'zero release drops preparation inputs')
    need(bound['prepared_runs'] == prepared['prepared_runs']
         and bound['zero_prepared_runs'] == prepared['zero_prepared_runs'],
         'zero release changes prepared identities')
    need(bound.get('zero_resource_proposal') == prepared['zero_resource_proposal']
         and bound.get('reader_path') == prepared['reader_path'],
         'zero release changes resources or reader')
    need(bound.get('approved_runs') == bound.get('approved_run_ids') == []
         and bound.get('actual_audit_run_ids') == bound.get('actual_formal_run_ids') == [],
         'zero release must not grant/claim formal work')
    need(bound.get('approved_audit_run_ids') == [r['run_id'] for r in prepared['zero_prepared_runs']],
         'exact 3-call authorization required')
    for role, filename in (('zero_authorization', 'S4_TGE_SERVER_zero_authorization_v2_20261104_01.json'),
                           ('zero_resource_decision',
                            'S4_TGE_SERVER_zero_resource_decision_v2_20261104_01.json')):
        ref = bound.get(role, {})
        p = covered(bound, ref.get('path', ''))
        need(p == CASE / 'evidence' / filename and sha(p) == ref.get('sha256'),
             'wrong authorization/resource evidence')
        value = load(p)
        need(value.get('stage') == STAGE and value.get('user_explicitly_authorized') is True
             and isinstance(value.get('user_instruction_verbatim'), str)
             and value['user_instruction_verbatim'].strip(),
             'actual scoped user declaration missing')
        if role == 'zero_authorization':
            need(value.get('native_call_count') == 3 and value.get('initial_field_read_count') == 1
                 and value.get('actual_time_steps') == 0
                 and value.get('fail_stop_no_retry') is True
                 and value.get('approved_audit_run_ids') == bound['approved_audit_run_ids'],
                 'authorization does not cover exact 3+1')
            need(value.get('formal_simulation_authorized') is False
                 and value.get('performance_time_stepping_authorized') is False,
                 'zero authorization includes time stepping')
        else:
            need(value.get('resource_decision_accepted') is True
                 and value.get('resources') == SERVER_RESOURCES,
                 'server resource decision not adopted')


def static_summary(bound):
    one = kv(bound['prepared_runs'][0]['run_config_path'])
    two = kv(bound['prepared_runs'][1]['run_config_path'])
    return dict(stage=STAGE, binding_check=True, solver_executed=False,
                prepared_formal_runs=2,
                planned_native_zero_calls=3, planned_initial_field_reads=1,
                parameters_1p25=physics(one), parameters_0p625=physics(two),
                original_S4_stage_accepted=False, reference_qualified=False,
                native_zero_step_authorized=bound['native_zero_step_authorized'],
                formal_simulation_authorized=False,
                performance_time_stepping_authorized=False,
                build_equivalence_rtol=BUILD_EQUIVALENCE_RTOL)
