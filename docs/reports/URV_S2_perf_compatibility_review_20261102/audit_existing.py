#!/usr/bin/env python3
"""Read-only B/PERF compatibility evidence; writes only this report directory.

Does not compile, execute native programs, read VTK with a reader, or create a
performance case/release/run. This is a documentary audit, not a PERF controller.
"""
from pathlib import Path
import datetime
import hashlib
import json
import sys

ROOT = Path('/home/dell/yuanyuanxu/SIM240')
OUT = ROOT / 'docs/reports/URV_S2_perf_compatibility_review_20261102'
CASE = ROOT / 'CASE/unseen_v2_reference_S2_reuse_v1'
CHECKER = ROOT / 'CASE/unseen_v2_reference_checker_S2_reuse_v1'
B_PATH = CASE / 'evidence/preparation_B.json'
B_SHA = '2e55f3369f9445e7763ee1f9a87c57f79348d1b332c959bc038c1bcc4739081f'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save(name, value):
    target = OUT / name
    assert not target.exists(), f'report already exists: {target}'
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def main():
    for name in ['SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md']:
        source = ROOT / 'docs/reports' / name
        target = OUT / ('before_'+name)
        assert not target.exists()
        target.write_bytes(source.read_bytes())
    previous = ROOT / 'docs/reports/URV_S2_zero_results_review_20261102'
    protected = json.loads((previous / 'protected_inputs_before.json').read_text())
    assert isinstance(protected, dict) and len(protected) == 3036
    drift = [p for p, digest in protected.items() if not Path(p).is_file() or sha(p) != digest]
    assert not drift, drift
    for tree in [CASE, CHECKER, previous]:
        for path in tree.rglob('*'):
            if path.is_file():
                protected[str(path.resolve())] = sha(path)
    save('protected_inputs_before.json', protected)
    sys.path.insert(0, str(CHECKER / 'analysis'))
    from stage_s2 import verify_seal, verify_zero_receipt
    from evidence import kv, exact_parameters
    bound = verify_seal(B_PATH, B_SHA)
    receipt = verify_zero_receipt(bound)
    independent = bound['independent_zero_review']
    assert sha(independent['path']) == independent['sha256']
    assert bound['inputs_sha256'][independent['path']] == independent['sha256']
    accepted = json.loads(Path(independent['path']).read_text())
    assert accepted['ZERO_STEP_INDEPENDENT_REVIEW_PASS'] is True
    assert accepted['ZERO_STEP_GEOMETRY_PASS'] is True
    assert accepted['native_records_reviewed'] == 18
    assert accepted['actual_VTK_field_rereads'] == 6
    assert all(bound[key] is False for key in [
        'simulation_authorized', 'native_zero_step_authorized',
        'performance_time_stepping_authorized'])
    assert bound['approved_runs'] == bound['approved_run_ids'] == []
    protocol_path = ROOT / 'docs/reports/URV_S2_minimum_preparation_protocol_20261102/performance_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['protocol_id'] == 'S2-MIP-v1-PERF'
    assert protocol['same_native_binary_sha256'] == sha(bound['provenance']['native_binary'])
    fine = [r for r in bound['prepared_runs'] if 'dx1p25_' in r['planned_case_id']]
    assert [r['planned_case_id'] for r in fine] == protocol['candidate_cases']
    configs = []
    for record in fine:
        config = kv(record['run_config_path'])
        parameters = exact_parameters(config)
        assert parameters['window'] == protocol['native_window_steps'] == 10368
        assert parameters['cap'] == protocol['native_maximum_steps'] == 602112
        assert parameters['nodes'] == 2949120
        configs.append(dict(source_record=record, source_config=config,
            exact_parameters=parameters, allowed_future_native_config_changes=['run_id','output_directory'],
            candidate_perf_run_id=None, actual_performance_run_id=None))
    save('fine_config_review.json', configs)
    pristine = {r['run_id']: sorted(p.name for p in Path(r['output_directory']).iterdir())
                for r in bound['prepared_runs']}
    assert all(names == ['run_config.txt', 'run_manifest.txt'] for names in pristine.values())
    candidate = ROOT / 'CASE/unseen_v2_reference_S2_perf_v1'
    assert not candidate.exists(), 'proposed performance case already exists; inspect before proceeding'
    no_run_artifacts = {name: not (CASE/name).exists() for name in ['launch_attempts','performance_runs']}
    assert all(no_run_artifacts.values())
    review_paths = [B_PATH, CASE/'evidence/preparation_A.json', protocol_path,
        protocol_path.with_name('PERFORMANCE_PROTOCOL.md'),
        CASE/'scripts/run_S2.py', CASE/'scripts/audit_S2_zero.py',
        CHECKER/'analysis/stage_s2.py', CHECKER/'analysis/contracts.py',
        CHECKER/'analysis/revision_s2_reuse.py', CHECKER/'analysis/check_results.py',
        CHECKER/'analysis/evidence.py', CHECKER/'common/acceptance_spec.json',
        Path(bound['provenance']['native_binary']), *map(Path,bound['provenance']['native_sources']),
        Path(independent['path'])]
    save('reviewed_inputs_sha256.json', {str(p): sha(p) for p in review_paths})
    save('B_compatibility_audit.json', dict(
        reviewed_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
        review_kind='READ_ONLY_B_PERF_COMPATIBILITY_NOT_EXECUTION_ACCEPTANCE',
        B_path=str(B_PATH), B_sha256=sha(B_PATH), expected_B_sha256=B_SHA,
        B_bound_inputs=len(bound['inputs_sha256']), verify_seal_pass=True,
        verify_zero_receipt_pass=True, independent_zero_acceptance_hash_verified=True,
        zero_native_records=accepted['native_records_reviewed'], zero_field_rereads=accepted['actual_VTK_field_rereads'],
        zero_steps=receipt['actual_time_steps'], binary_sha256=sha(bound['provenance']['native_binary']),
        B_authority_unchanged_and_closed=True, performance_protocol_bound_in_B=(
            bound['inputs_sha256'].get(str(protocol_path)) == sha(protocol_path)),
        selected_cases=[r['planned_case_id'] for r in fine],
        formal_run_directories=pristine, no_run_artifacts=no_run_artifacts,
        proposed_perf_case_not_created=True, native_calls_this_review=0,
        VTK_reader_calls_this_review=0, builds_this_review=0, performance_time_steps_this_review=0,
        new_approved_performance_run_ids=[], new_actual_performance_run_ids=[],
        performance_time_stepping_authorized=False, formal_simulation_authorized=False,
        COMPATIBILITY='COMPATIBLE_AS_READ_ONLY_PREDECESSOR_REQUIRES_SEPARATE_PERF_LAYER',
        PERF_IMPLEMENTATION_STATUS='NOT_IMPLEMENTED',
        NUMERICAL_GATE='NOT_EVALUATED', RESULT_PASS=False,
        REFERENCE_QUALIFIED_FOR_CASE=False, MODEL_COMPARISON='NOT_EVALUATED',
        physical_validation='NOT_EVALUATED', submission_ready=False))
    print(json.dumps(dict(B_inputs=len(bound['inputs_sha256']), protected_inputs=len(protected),
        fine_cases=len(fine), B_compatible_as_predecessor=True, native_calls=0, builds=0)))


if __name__ == '__main__':
    main()
