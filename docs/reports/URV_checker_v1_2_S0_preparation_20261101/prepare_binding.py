"""Seal concrete S0 preparation, without approving or starting execution."""
from pathlib import Path
import ast
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
REPORT = Path(__file__).resolve().parent
OLD = ROOT / 'CASE/unseen_v2_reference_checker_v1_1'
CHECKER = ROOT / 'CASE/unseen_v2_reference_checker_v1_2'
CASE = ROOT / 'CASE/unseen_v2_reference_S0_v1_2'
sys.path.insert(0, str(CHECKER / 'analysis'))
from evidence import sha, save, kv, exact_parameters, need
from contracts import verify_provenance, approved_records


def main():
    envpath = CASE / 'evidence/build_environment.json'
    env = json.loads(envpath.read_text())
    unchanged = {}
    for folder in ['analysis', 'common']:
        for p in (OLD / folder).glob('*'):
            if p.is_file() and p.name != 'contracts.py':
                q = CHECKER / folder / p.name
                need(p.read_bytes() == q.read_bytes(), 'unexpected numerical/rule edit: ' + str(q))
                unchanged[str(q)] = sha(q)
    need('Ran 77 tests' in (REPORT / 'checker_tests_final.log').read_text()
         and (REPORT / 'checker_tests_final.log').read_text().rstrip().endswith('OK'), 'checker tests incomplete')
    need('Ran 6 tests' in (REPORT / 'runner_tests.log').read_text()
         and (REPORT / 'runner_tests.log').read_text().rstrip().endswith('OK'), 'runner tests incomplete')
    syntax = []
    for p in [*CHECKER.rglob('*.py'), *CASE.glob('scripts/*.py'), *REPORT.glob('*.py')]:
        compile(p.read_text(), str(p), 'exec'); syntax.append(str(p))
    save(REPORT / 'unchanged_numerics_and_syntax.json', dict(
        byte_identical_files=unchanged, in_memory_syntax_checked=syntax,
        no_native_physics_source_changes=True, no_acceptance_threshold_changes=True))
    sealpath = CHECKER / 'evidence/revision_seal.json'
    seal = dict(revision_id='URV-CHECKER-v1.2-20261101', kind='CHECKER_REVISION_PREPARATION_ONLY',
        simulation_authorized=False, approved_run_ids=[], actual_formal_run_ids=[], S0_started=False,
        R1='ADDRESSED_AND_TESTED', R2='ADDRESSED_AND_TESTED', F04='OPEN_OUT_OF_SCOPE',
        checker_tests=77, runner_artificial_tests_separate=6,
        external_data_history='AUTHOR_DECLARED_NONUSE_CONFIRMED',
        source_revision_seal=str(OLD / 'evidence/revision_seal.json'),
        source_revision_sha256=sha(OLD / 'evidence/revision_seal.json'),
        inputs_sha256={str(p): sha(p) for p in CHECKER.rglob('*') if p.is_file()},
        checker_tests_log=str(REPORT / 'checker_tests_final.log'),
        checker_tests_log_sha256=sha(REPORT / 'checker_tests_final.log'))
    save(sealpath, seal)
    (sealpath.with_suffix('.sha256')).write_text(sha(sealpath) + '  revision_seal.json\n')
    draftpath = ROOT / 'docs/reports/URV_v1_readonly_review_S0_20261101/S0_DRAFT_NOT_EXECUTABLE/S0_binding_DRAFT.json'
    draft = json.loads(draftpath.read_text())
    declaration = ROOT / 'docs/reports/URV_external_history_confirmation_20261101/author_declaration.json'
    need(json.loads(declaration.read_text())['status'] == 'AUTHOR_DECLARED_NONUSE_CONFIRMED', 'real author declaration missing')
    auditpath = CASE / 'audits/URV_S0_ZERO_20261101_01/verification.json'
    audit = json.loads(auditpath.read_text())
    need(audit['actual_time_steps'] == 0 and audit['native_describe'] == audit['native_precheck'] == 2, 'zero audit incomplete')
    records = []; parameters = {}
    for direction in ['P', 'T']:
        run_id = f'URV_S0_{direction}_v1_2_20261101_01'
        run = CASE / 'runs' / run_id / 'steady'; cfg = run / 'run_config.txt'
        p = exact_parameters(kv(cfg))
        need(p['nodes'] == 57600 and p['window'] == 1013 and p['cap'] == 58800, 'S0 exact arithmetic')
        parameters[direction] = p
        records.append(dict(run_id=run_id, planned_case_id=f'URV1_H75_{direction}_dx5_a100000',
            run_config_path=str(cfg), run_config_sha256=sha(cfg), output_directory=str(run)))
    files = {p for base in [CHECKER, CASE / 'src', CASE / 'scripts', CASE / 'evidence', CASE / 'audits', CASE / 'runs']
             for p in base.rglob('*') if p.is_file()}
    files.update([CASE / 'README.md', CASE / 'PROTOCOL.md', CASE / 'run_config.md', CASE / '.gitignore',
                  CASE / 'build/urv_reference', CASE / 'build/urv_reference.d',
                  declaration, draftpath, ROOT / 'CASE/unseen_v2_reference_v1/evidence/preparation_seal.json',
                  OLD / 'evidence/revision_seal.json', REPORT / 'checker_tests_final.log', REPORT / 'runner_tests.log',
                  REPORT / 'unchanged_numerics_and_syntax.json', Path(__file__).resolve(), REPORT / 'build_s0.py',
                  REPORT / 'audit_S0_zero.py', REPORT / 'test_runner.py'])
    for mapping in [env['dependency_sha256'], env['link_library_sha256'], env['dynamic_library_sha256'],
                    draft['reference_inputs_sha256']]:
        for path, digest in mapping.items():
            need(sha(path) == digest, 'captured input changed: ' + path); files.add(Path(path))
    files.update([Path(env['compiler_executable']), Path(env['mpi_wrapper_executable'])])
    data = dict(protocol_id='URV-v1', schema_version='URV-EXEC-1.1',
        binding_id='URV-S0-PREPARED-v1.2-20261101-01',
        kind='PREPARED_EXECUTION_BINDING_NOT_LAUNCH_RELEASE',
        status='PREPARATION_COMPLETE_AWAITING_SEPARATE_USER_LAUNCH_AUTHORIZATION',
        stage='S0_REGRESSION', simulation_authorized=False, preparation_only_build=False,
        author_external_data_history_confirmation='CONFIRMED',
        author_confirmation_scope='results not used to select V2 coefficients or these two conditions; author declaration only',
        author_reply_file=str(declaration), author_reply_sha256=sha(declaration),
        checked_external_locations_or_sources=None, external_history_independently_verified=False,
        approved_run_ids=[], approved_runs=[], actual_formal_run_ids=[], S0_started=False,
        prepared_run_ids=[r['run_id'] for r in records], prepared_runs=records,
        launch_authorization=dict(user_explicitly_authorized=False, user_instruction_verbatim=None),
        provenance=dict(native_binary=env['binary_path'], native_sources=list(env['native_sources_sha256']),
            build_recipe=env['build_recipe_path'], build_environment=str(envpath),
            dependency_file=env['dependency_file_path'], ldd_record=str(CASE / 'evidence/ldd.txt')),
        inputs_sha256={str(p.resolve()): sha(p) for p in sorted(files)},
        h75_regression_references={r['direction']: r['baseline'] for r in draft['cases']},
        exact_parameters=parameters, acceptance=draft['acceptance'],
        resources=dict(processes=1, threads=1, cuboids=1, overlap=3,
            per_process_address_space_GiB=8, required_available_RAM_GiB=12,
            required_initial_free_disk_GiB=100, required_before_each_run_free_disk_GiB=8,
            solver_wall_cap_seconds_per_case=3600),
        zero_audit_path=str(auditpath), zero_audit_sha256=sha(auditpath),
        checker_revision_seal=str(sealpath), checker_revision_sha256=sha(sealpath),
        formal_NUMERICAL_GATE='NOT_EVALUATED', RESULT_PASS=False, geometry_PASS=None,
        reference_qualified=False, physical_validation='NOT_EVALUATED', submission_ready=False,
        F04='OPEN_OUT_OF_SCOPE', old_h75_raw_RESULT_PASS_false_preserved=True)
    verify_provenance(data)
    projection = dict(data, approved_run_ids=data['prepared_run_ids'], approved_runs=records)
    approved_records(projection)  # identity audit only; no authorization projection is saved
    finalpath = CASE / 'evidence/S0_prepared_binding.json'
    save(finalpath, data)
    finalpath.with_suffix('.sha256').write_text(sha(finalpath) + '  S0_prepared_binding.json\n')
    print(json.dumps(dict(prepared_binding=str(finalpath), binding_sha256=sha(finalpath),
        bound_inputs=len(data['inputs_sha256']), simulation_authorized=False,
        reserved_run_ids=data['prepared_run_ids'], approved_run_ids=[])))


if __name__ == '__main__':
    main()
