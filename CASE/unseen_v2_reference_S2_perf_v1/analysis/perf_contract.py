"""Separate performance authority; frozen B and its validators remain read-only."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import sys

CASE = Path(__file__).resolve().parents[1]
ROOT = CASE.parents[1]
OLD = CASE.parent / 'unseen_v2_reference_S2_reuse_v1'
CHECKER = CASE.parent / 'unseen_v2_reference_checker_S2_reuse_v1'
B_PATH = OLD / 'evidence/preparation_B.json'
B_SHA = '2e55f3369f9445e7763ee1f9a87c57f79348d1b332c959bc038c1bcc4739081f'
ELF_SHA = '5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b'
PROTOCOL_DIR = ROOT / 'docs/reports/URV_S2_minimum_preparation_protocol_20261102'
REVIEW = ROOT / 'docs/reports/URV_S2_perf_compatibility_review_20261102'
IMPLEMENTATION = ROOT / 'docs/reports/URV_S2_perf_implementation_20261102'
STAGE = 'S2_PERFORMANCE_ONLY'
PURPOSE = 'S2_PERFORMANCE_NOT_REFERENCE'
PREP = 'S2_PERF_PREPARATION_NOT_AUTHORIZATION'
RELEASE = 'AUTHORIZED_PERFORMANCE_RELEASE'
IDS = [f'URV_S2_PERF_{d}_dx1p25_v1_20261102_01' for d in ('P','T')]
CASES = [f'URV1_U_REG_{d}_dx1p25_a100000' for d in ('P','T')]
MODULES = ['scripts/prepare_perf.py', 'scripts/run_perf.py',
           'analysis/perf_contract.py', 'analysis/check_perf.py', 'tests/test_perf.py']
SCIENCE = dict(NUMERICAL_GATE='NOT_EVALUATED', RESULT_PASS=False, geometry_PASS=None,
    REFERENCE_QUALIFIED_FOR_CASE=False, MODEL_COMPARISON='NOT_EVALUATED',
    physical_validation='NOT_EVALUATED', reference_qualified=False,
    strict_error_bound_established=False, submission_ready=False)


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1<<20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def kv(path):
    data = {}
    for line in Path(path).read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        k,v = line.split('=',1)
        need(k not in data, 'duplicate config key')
        data[k] = v
    return data


def no_symlinks(path):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts, 'noncanonical path')
    for item in [path,*path.parents]:
        need(not item.is_symlink(), 'symlink path refused: '+str(item))
    need(path.resolve() == path, 'path alias refused')
    return path


def unchanged(inputs):
    need(isinstance(inputs,dict) and bool(inputs), 'empty source closure')
    actual = {p:sha(p) for p in inputs}
    need(actual == inputs, 'bound input drift')
    return actual


def frozen_helpers():
    # The original checker receives ORIGINAL B only, never a performance release.
    directory = str(CHECKER/'analysis')
    if directory not in sys.path:
        sys.path.insert(0,directory)
    import stage_s2
    import evidence
    need(Path(stage_s2.__file__).resolve()==CHECKER/'analysis/stage_s2.py', 'checker module shadowed')
    need(Path(evidence.__file__).resolve()==CHECKER/'analysis/evidence.py', 'evidence module shadowed')
    return stage_s2,evidence


def verify_B():
    need(sha(B_PATH)==B_SHA, 'B external hash mismatch')
    stage,_ = frozen_helpers()
    bound = stage.verify_seal(B_PATH,B_SHA)
    stage.verify_zero_receipt(bound)
    need(bound['kind']=='S2_PREPARATION_B_NOT_AUTHORIZATION', 'wrong predecessor kind')
    need(len(bound['inputs_sha256'])==1816, 'B closure changed')
    record = bound['independent_zero_review']
    need(bound['inputs_sha256'].get(record['path'])==record['sha256']==sha(record['path']),
         'independent zero acceptance not bound')
    accepted = load(record['path'])
    need(accepted['ZERO_STEP_INDEPENDENT_REVIEW_PASS'] is True and
         accepted['ZERO_STEP_GEOMETRY_PASS'] is True and accepted['native_records_reviewed']==18 and
         accepted['actual_VTK_field_rereads']==6, 'independent zero prerequisite incomplete')
    need(all(bound[k] is False for k in ['simulation_authorized','native_zero_step_authorized',
         'performance_time_stepping_authorized']), 'B must remain closed')
    need(sha(bound['provenance']['native_binary'])==ELF_SHA, 'same ELF required')
    return bound


def protocol():
    return load(PROTOCOL_DIR/'performance_protocol.json')


def records_check(data, b):
    records = data.get('prepared_benchmark_runs')
    need(isinstance(records,list) and len(records)==2, 'exact two performance records required')
    need([r['run_id'] for r in records]==IDS, 'performance IDs/order changed')
    need([r['source_planned_case_id'] for r in records]==CASES, 'performance candidates/order changed')
    original = {r['planned_case_id']:r for r in b['prepared_runs']}
    for r in records:
        need('planned_case_id' not in r, 'performance must not enter formal acceptance mapping')
        rid = r['run_id']
        need(bool(re.fullmatch(r'[A-Za-z0-9_]+',rid)) and 'PERF' in rid, 'invalid PERF ID')
        run = CASE/'performance_runs'/rid/'steady'
        need(r['output_directory']==str(run), 'performance output isolation')
        no_symlinks(run)
        path = run/'run_config.txt'
        need(r['run_config_path']==str(path), 'config location')
        need(data['inputs_sha256'].get(str(path))==r['run_config_sha256']==sha(path), 'config not bound')
        need(data['inputs_sha256'].get(str(run/'run_manifest.txt'))==sha(run/'run_manifest.txt'),
             'manifest not bound')
        expected = dict(kv(original[r['source_planned_case_id']]['run_config_path']),
                        run_id=rid,output_directory=str(run))
        need(kv(path)==expected and expected['mode']=='steady', 'native config changed beyond identity/output')
        need(kv(run/'run_manifest.txt')==dict(run_id=rid,mode='steady'), 'manifest identity')
    return records


def validate_document(data, b):
    p = protocol()
    need(data.get('protocol_id')=='S2-MIP-v1-PERF' and data.get('stage')==STAGE and
         data.get('purpose')==PURPOSE, 'performance-only identity required')
    need(data.get('schema_version')=='S2-PERF-BINDING-1','unknown performance binding schema')
    need(data.get('kind') in (PREP,RELEASE), 'performance seal/release only')
    need(data.get('B_path')==str(B_PATH) and data.get('B_sha256')==B_SHA, 'pinned B required')
    need(data.get('native_binary')==b['provenance']['native_binary'] and
         data.get('native_binary_sha256')==ELF_SHA, 'native provenance mismatch')
    need(data.get('resources')==p['resources'] and data.get('budget')==p['budget'] and
         data.get('performance_windows')==p['performance_windows'], 'PERF budgets/resources/windows changed')
    need(data.get('native_window_steps')==10368 and data.get('native_maximum_steps')==602112,
         'original native window/cap required')
    need(data.get('prepared_benchmark_run_ids')==IDS, 'prepared IDs incomplete')
    need(data.get('formal_simulation_authorized') is False and data.get('simulation_authorized') is False and
         data.get('native_zero_step_authorized') is False, 'non-performance permission enabled')
    need(data.get('approved_formal_run_ids')==[] and data.get('approved_run_ids')==[] and
         data.get('approved_runs')==[], 'formal approved scope forbidden')
    need(data.get('actual_benchmark_run_ids')==[] and data.get('actual_formal_run_ids')==[],
         'input binding cannot claim future completed runs')
    need(data.get('AI_may_start_native') is False and data.get('user_manually_starts') is True,
         'user-manual execution boundary required')
    need(data.get('automatic_retry_authorized') is False,'automatic retry forbidden')
    need(all(data.get(k)==v for k,v in SCIENCE.items()), 'scientific states must stay closed')
    inputs = data['inputs_sha256']
    need(all(inputs.get(k)==v for k,v in b['inputs_sha256'].items()), 'B inputs dropped or changed')
    need(inputs.get(str(B_PATH))==B_SHA, 'B file itself missing from closure')
    for rel in [*MODULES,'README.md','evidence/adoption.json','evidence/runtime_environment.json']:
        need(inputs.get(str(CASE/rel))==sha(CASE/rel), 'new implementation file not bound: '+rel)
    for directory in [CASE/'analysis',CASE/'scripts',CASE/'tests']:
        for path in directory.rglob('*'):
            if path.is_file():
                need('__pycache__' not in path.parts and inputs.get(str(path))==sha(path), 'unbound new code')
    for path in [REVIEW/'MINIMUM_IMPLEMENTATION_SCOPE.md',REVIEW/'minimum_scope.json',
                 IMPLEMENTATION/'adoption.json',IMPLEMENTATION/'software_checks.json',
                 PROTOCOL_DIR/'PERFORMANCE_PROTOCOL.md',PROTOCOL_DIR/'performance_protocol.json']:
        need(inputs.get(str(path))==sha(path), 'scope/protocol/software evidence missing')
    env = load(CASE/'evidence/runtime_environment.json')
    need(str(Path(sys.executable).resolve())==env['python_executable'] and
         sys.version==env['python_version'], 'wrong Python interpreter/version')
    need(inputs.get(env['python_executable'])==env['python_sha256'], 'interpreter not bound')
    for path,digest in env['runtime_files_sha256'].items():
        need(inputs.get(path)==digest, 'runtime dependency missing')
    records_check(data,b)
    if data['kind']==PREP:
        need(data.get('performance_time_stepping_authorized') is False and
             data.get('approved_benchmark_run_ids')==[] and data.get('approved_benchmark_runs')==[],
             'preparation cannot authorize execution')
    return data


def verify(path, expected_sha):
    need(isinstance(expected_sha,str) and len(expected_sha)==64 and sha(path)==expected_sha,
         'external SHA mismatch')
    data = load(path)
    unchanged(data['inputs_sha256'])
    return validate_document(data,verify_B())


def authorize(data):
    need(data['kind']==RELEASE and data.get('performance_time_stepping_authorized') is True,
         'preparation/zero/formal authority cannot launch performance')
    need(data.get('approved_benchmark_run_ids')==IDS and
         data.get('approved_benchmark_runs')==data['prepared_benchmark_runs'], 'approved benchmark pair mismatch')
    prep = Path(data['preparation_path'])
    need(data['inputs_sha256'].get(str(prep))==data['preparation_sha256']==sha(prep), 'preparation not bound')
    prior = verify(prep,data['preparation_sha256'])
    need(prior['kind']==PREP and prior['prepared_benchmark_runs']==data['prepared_benchmark_runs'],
         'release/preparation mismatch')
    need(all(data['inputs_sha256'].get(k)==v for k,v in prior['inputs_sha256'].items()), 'release drops preparation')
    auth = data.get('performance_authorization',{})
    path = auth.get('path','')
    need(data['inputs_sha256'].get(path)==auth.get('sha256')==sha(path), 'real performance authorization not bound')
    recorded = load(path)
    need(recorded.get('user_explicitly_authorized') is True and
         recorded.get('performance_time_stepping_authorized') is True and
         recorded.get('formal_simulation_authorized') is False and
         recorded.get('approved_benchmark_run_ids')==IDS and
         recorded.get('user_manually_starts') is True and recorded.get('AI_may_start_native') is False and
         isinstance(recorded.get('user_instruction_verbatim'),str) and
         bool(recorded['user_instruction_verbatim'].strip()), 'explicit scoped performance authority missing')
    need(recorded.get('authorization_source') in ('typed_user_message','reply_to_async_question'),
         'authorization source must be truthfully recorded')
    if recorded['authorization_source']=='reply_to_async_question':
        need(isinstance(recorded.get('question_verbatim'),str) and bool(recorded['question_verbatim'].strip()) and
             recorded.get('verbatim_recorded_from_typed_sentence') is False,
             'async authorization needs full question and accurate attribution')
    need(recorded.get('automatic_retry_authorized') is False, 'no retry authority')
    return data


def pristine(records):
    for r in records:
        run = no_symlinks(Path(r['output_directory']))
        need(sorted(p.name for p in run.iterdir())==['run_config.txt','run_manifest.txt'],
             'output already used; no restart/overwrite')


def now():
    return datetime.datetime.now().astimezone().isoformat()
