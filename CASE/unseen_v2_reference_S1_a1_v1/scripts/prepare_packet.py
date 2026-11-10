"""Create closed-authority S1 preparation; never runs or authorizes a solver."""
from pathlib import Path
import json
import sys

CASE = Path(__file__).resolve().parents[1]
ROOT = CASE.parents[1]
CHECKER = CASE.parent / 'unseen_v2_reference_checker_S1_a1_v1'
sys.path.insert(0, str(CHECKER / 'analysis'))
from evidence import sha, kv, save, need, exact_parameters


def materialize():
    plan = CASE / 'evidence/identity_plan.json'
    need(not plan.exists(), 'S1 identity plan already exists')
    records = []
    for direction in ('P', 'T'):
        rid = f'URV_S1_{direction}_A1_v1_20261102_01'
        ident = f'URV1_SMOOTH_H30_{direction}_dx1p25_a100000'
        run = CASE / 'runs' / rid / 'steady'
        run.mkdir(parents=True, exist_ok=False)
        template = ROOT / 'docs/reports/Unseen_V2_reference_protocol_20261101/describe_only_templates' / (ident + '.txt')
        cfg = kv(template); cfg.update(mode='steady', run_id=rid, output_directory=str(run))
        path = run / 'run_config.txt'
        path.write_text(''.join(k + '=' + v + '\n' for k,v in cfg.items()))
        (run / 'run_manifest.txt').write_text(f'run_id={rid}\nmode=steady\n')
        records.append(dict(run_id=rid, planned_case_id=ident, run_config_path=str(path),
                            run_config_sha256=sha(path), output_directory=str(run)))
    save(plan, dict(simulation_authorized=False, prepared_runs=records))


def view():
    envpath = CASE / 'evidence/build_environment.json'
    env = json.loads(envpath.read_text())
    plan = json.loads((CASE / 'evidence/identity_plan.json').read_text())
    records = plan['prepared_runs']
    inputs = {}
    for key in ('native_sources_sha256','dependency_sha256','link_library_sha256','dynamic_library_sha256'):
        inputs.update(env[key])
    inputs[env['compiler_executable']] = env['compiler_sha256']
    for folder in (CASE/'src',CASE/'scripts',CHECKER/'analysis',CHECKER/'common',CHECKER/'revision',CHECKER/'s1_revision',CHECKER/'tests'):
        for path in folder.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                inputs[str(path)] = sha(path)
    anchor = CHECKER / 's1_revision/anchor.json'
    revision = json.loads(anchor.read_text())
    for record in revision['frozen_inputs']:
        inputs[record['path']] = record['sha256']
    for record in revision['diffs'].values():
        inputs[record['baseline_path']] = record['baseline_sha256']
    original = json.loads((CHECKER/'common/source_preparation_anchor.json').read_text())
    inputs[original['preparation_seal']] = original['preparation_seal_sha256']
    author = ROOT / 'docs/reports/URV_external_history_confirmation_20261101/author_declaration.json'
    for path in (CASE/'build/urv_reference', CASE/'build/urv_reference.d',envpath,CASE/'evidence/ldd.txt',
                 CASE/'evidence/adoption.json',CASE/'evidence/identity_plan.json',author):
        inputs[str(path)] = sha(path)
    for record in records:
        for path in (Path(record['run_config_path']),Path(record['output_directory'])/'run_manifest.txt'):
            inputs[str(path)] = sha(path)
    return dict(protocol_id='URV-v1', schema_version='URV-EXEC-1.1', stage='S1_SMOOTH_THIN',
        addendum_id='URV-S1-A1-v1', kind='PREPARED_EXECUTION_BINDING_NOT_LAUNCH_RELEASE',
        simulation_authorized=False, preparation_only_build=False, approved_run_ids=[],approved_runs=[],
        prepared_run_ids=[r['run_id'] for r in records], prepared_runs=records,
        actual_formal_run_ids=[],S1_started=False,
        launch_authorization=dict(user_explicitly_authorized=False,user_instruction_verbatim=None),
        author_external_data_history_confirmation='CONFIRMED',author_reply_file=str(author),
        author_reply_sha256=sha(author),external_history_independently_verified=False,
        author_confirmation_scope='author nonuse declaration for the two groove candidates; S1 is a known analytic control',
        provenance=dict(native_binary=env['binary_path'],native_sources=list(env['native_sources_sha256']),
            build_recipe=env['build_recipe_path'],build_environment=str(envpath),
            dependency_file=env['dependency_file_path'],ldd_record=str(CASE/'evidence/ldd.txt')),
        source_revision=dict(id='URV-S1-A1-v1',anchor=str(anchor),sha256=sha(anchor)),
        inputs_sha256=inputs,h75_regression_references={},
        resources=dict(processes=1,threads=1,cuboids=1,overlap=3,per_process_address_space_GiB=8,
            required_available_RAM_GiB=12,required_initial_free_disk_GiB=100,required_before_each_run_free_disk_GiB=8,
            solver_wall_cap_seconds_per_case=14400),
        exact_parameters={d:exact_parameters(kv(records[i]['run_config_path'])) for i,d in enumerate(('P','T'))},
        density_capture='NOT_APPLICABLE_S0_ONLY',S0_predecessor=revision['S0_acceptance_file'],
        NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None,
        reference_qualified=False,strict_error_bound_established=False,submission_ready=False,
        MODEL_COMPARISON='NOT_EVALUATED',physical_validation='NOT_EVALUATED',F04='OPEN_OUT_OF_SCOPE')


def seal():
    data = view()
    save(CASE/'evidence/preparation_manifest.json',dict(kind='S1_PREPARATION_NOT_AUTHORIZATION',
        candidate_binary_sha256=sha(CASE/'build/urv_reference'),simulation_authorized=False,
        inputs_sha256=data['inputs_sha256']))


def finalize():
    original_path = CASE/'evidence/preparation_manifest.json'
    original = json.loads(original_path.read_text())
    need(all(sha(p)==h for p,h in original['inputs_sha256'].items()),'S1 preparation source drift')
    zero = CASE/'audits/URV_S1_ZERO_20261102_01/verification.json'
    evidence = json.loads(zero.read_text())
    need(evidence['ZERO_STEP_AUDIT_PASS'] is True and evidence['actual_time_steps']==0,'S1 real zero audit required')
    data = view()
    need(evidence['binary_sha256']==original['candidate_binary_sha256'],'zero/binary identity')
    data.update(zero_audit_path=str(zero),zero_audit_sha256=sha(zero),
        status='S1_ZERO_AUDIT_PASSED_AWAITING_FORMAL_LAUNCH_AUTHORIZATION',
        binding_id='URV-S1-A1-v1-PREPARED-20261102-01')
    for path in [original_path,*zero.parent.rglob('*')]:
        if path.is_file():data['inputs_sha256'][str(path)]=sha(path)
    output=CASE/'evidence/S1_prepared_binding_20261102_01.json';save(output,data)
    output.with_suffix('.sha256').write_text(sha(output)+'  '+output.name+'\n')
    print(json.dumps(dict(prepared_binding_sha256=sha(output),input_count=len(data['inputs_sha256']),simulation_authorized=False)))


if __name__ == '__main__':
    action=sys.argv[1]
    need(action in ('identities','seal','finalize'),'unknown preparation action')
    {'identities':materialize,'seal':seal,'finalize':finalize}[action]()
