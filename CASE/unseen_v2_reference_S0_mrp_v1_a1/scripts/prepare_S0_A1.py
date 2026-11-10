#!/usr/bin/env python3
"""Seal new S0 identities after real zero-step audit; never authorizes/runs them."""
from pathlib import Path
import json,sys

CASE=Path(__file__).resolve().parents[1]
PROJECT=CASE.parents[1]
CHECKER=CASE.parent/'unseen_v2_reference_checker_mrp_v1_a1'
sys.path.insert(0,str(CHECKER/'analysis'))
from evidence import sha,kv,save,need,exact_parameters

def main():
    output=CASE/'evidence/S0_prepared_binding_A1_20261102_01.json'
    need(not output.exists(),'refusing preparation binding overwrite')
    original=json.loads((CASE/'evidence/preparation_manifest.json').read_text())
    need(all(sha(p)==h for p,h in original['inputs_sha256'].items()),'sealed A1 source drift')
    zero=CASE/'audits/URV_A1_ZERO_20261102_01/verification.json'
    z=json.loads(zero.read_text())
    need(z['ZERO_STEP_AUDIT_PASS'] is True and z['actual_time_steps']==0,'real zero audit required')
    binary=CASE/'build/urv_reference'
    need(z['binary_sha256']==sha(binary)==original['candidate_binary_sha256'],'zero/binary binding mismatch')
    oldcase=CASE.parent/'unseen_v2_reference_S0_v1_2'
    base=json.loads((oldcase/'evidence/S0_prepared_binding.json').read_text())
    envpath=CASE/'evidence/build_environment.json';env=json.loads(envpath.read_text())
    document={k:v for k,v in base.items() if k not in ['inputs_sha256','prepared_runs','prepared_run_ids']}
    document.update(binding_id='URV-S0-A1-PREPARED-20261102-01',addendum_id='URV-MRP-v1-A1',
        kind='PREPARED_EXECUTION_BINDING_NOT_LAUNCH_RELEASE',
        status='ZERO_AUDIT_PASSED_AWAITING_SEPARATE_FORMAL_LAUNCH_AUTHORIZATION',
        simulation_authorized=False,approved_run_ids=[],approved_runs=[],actual_formal_run_ids=[],S0_started=False,
        launch_authorization=dict(user_explicitly_authorized=False,user_instruction_verbatim=None),
        zero_audit_path=str(zero),zero_audit_sha256=sha(zero),
        checker_revision_seal=str(CASE/'evidence/preparation_manifest.json'),
        checker_revision_sha256=sha(CASE/'evidence/preparation_manifest.json'))
    document['provenance']=dict(native_binary=str(binary),native_sources=list(env['native_sources_sha256']),
        build_recipe=env['build_recipe_path'],build_environment=str(envpath),
        dependency_file=env['dependency_file_path'],ldd_record=str(CASE/'evidence/ldd.txt'))
    anchor=CHECKER/'revision/revision_anchor.json'
    document['source_revision']=dict(id='URV-MRP-v1',anchor=str(anchor),sha256=sha(anchor))
    records=[];baselines={};initial_comparison={};inputs={}
    for direction in ('P','T'):
        ident=f'URV_S0_{direction}_A1_20261102_01';run=CASE/'runs'/ident/'steady'
        run.mkdir(parents=True,exist_ok=False)
        oldrun=oldcase/'runs'/f'URV_S0_{direction}_v1_2_20261101_01'/'steady'
        cfg=kv(oldrun/'run_config.txt');cfg.update(run_id=ident,output_directory=str(run))
        path=run/'run_config.txt';path.write_text(''.join(k+'='+v+'\n' for k,v in cfg.items()))
        manifest=run/'run_manifest.txt';manifest.write_text('run_id='+ident+'\nmode=steady\n')
        records.append(dict(run_id=ident,planned_case_id=f'URV1_H75_{direction}_dx5_a100000',
            run_config_path=str(path),run_config_sha256=sha(path),output_directory=str(run)))
        for p in [path,manifest]:inputs[str(p)]=sha(p)
        completion=oldrun/'completion.json';oldoutputs=json.loads(completion.read_text())['output_sha256']
        names={'field_slice.csv','velocity_profile.csv','pressure_profile.csv','energy_dissipation.csv',
               'frame_index.csv','frame_schedule.csv'}
        physical={name:digest for name,digest in oldoutputs.items()
                  if name in names or Path(name).suffix in ('.pvd','.vtm','.vti')}
        need(names<=set(physical) and len(physical)==27,'expected complete physical baseline closure')
        need(all(sha(oldrun/name)==h for name,h in physical.items()),'old raw physical baseline changed')
        physical_path=CASE/'evidence'/f'v12_physical_output_baseline_{direction}.json'
        save(physical_path,physical)
        baselines[direction]=dict(v12_diagnostics=str(oldrun/'diagnostics.csv'),
            v12_output_manifest=str(physical_path),v12_completion=str(completion),
            baseline_role='existing failed-or-passed v1.2 immutable raw statistics/fields; not an accuracy reference')
        for p in [physical_path,completion,oldrun/'diagnostics.csv']:
            inputs[str(p)]=sha(p)
        initial=kv(CASE/'audits/URV_A1_ZERO_20261102_01'/direction/'initialize/result.txt')
        import csv
        with (oldrun/'diagnostics.csv').open() as f:old0=next(csv.DictReader(f))
        oldref=Path(document['h75_regression_references'][direction]['directory'])
        with (oldref/'diagnostics.csv').open() as f:foundation0=next(csv.DictReader(f))
        need(float(initial['mass'])==float(old0['mass'])==float(foundation0['mass']),'zero legacy mass mismatch')
        need(float(initial['corrected_mass'])==float(old0['corrected_mass']),'zero compensated mass mismatch')
        initial_comparison[direction]=dict(legacy_mass_exact_old_and_v12=True,corrected_mass_exact_v12=True,
                                          qualification='initial scalar comparison only, not steady/capture equivalence')
        for name in ['result.txt','diagnostics.csv']:inputs[str(oldref/name)]=sha(oldref/name)
        certificate=Path(document['h75_regression_references'][direction]['independent_certificate'])
        inputs[str(certificate)]=sha(certificate)
    document['prepared_run_ids']=[r['run_id'] for r in records];document['prepared_runs']=records
    document['mass_repair_baselines']=baselines;document['initial_scalar_comparison']=initial_comparison
    document['exact_parameters']={d:exact_parameters(kv(Path(records[i]['run_config_path']))) for i,d in enumerate(('P','T'))}
    document['capture_acceptance']=dict(schedule=str(CHECKER/'revision/density_capture_schedule.json'),
        planned_capture_counts=dict(P=11,T=201),raw_binary64_snapshot_bytes=460800,
        supplementary_checker=str(CHECKER/'analysis/check_mass_repair.py'),
        original_checker=str(CHECKER/'analysis/check_results.py'),
        finalizer_before_completion=True,original_and_supplementary_required_before_next_case=True,
        initial_mode_exercises_capture=False,steady_capture_end_to_end_verified=False)
    # Current actual closure, exact revision baselines/adoption, zero raw files,
    # runtime wrapper, original rules, and author-history declaration are all bound.
    for key in ['native_sources_sha256','dependency_sha256','link_library_sha256','dynamic_library_sha256']:
        inputs.update(env[key])
    inputs[env['compiler_executable']]=env['compiler_sha256']
    for folder in [CASE/'src',CASE/'scripts',CHECKER/'analysis',CHECKER/'common',CHECKER/'revision',CASE/'audits/URV_A1_ZERO_20261102_01']:
        for p in folder.rglob('*'):
            if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts:inputs[str(p)]=sha(p)
    frozen=json.loads(anchor.read_text())
    for rec in frozen['frozen_inputs']:inputs[rec['path']]=rec['sha256']
    for rec in frozen['diffs'].values():
        if rec['baseline_path']:inputs[rec['baseline_path']]=rec['baseline_sha256']
    for p in [binary,envpath,CASE/'build/urv_reference.d',CASE/'evidence/ldd.txt',
              CASE/'evidence/preparation_manifest.json',CASE/'evidence/preparation_manifest.sha256',
              CASE/'evidence/adoption.json',Path(document['author_reply_file'])]:inputs[str(p)]=sha(p)
    original_anchor=json.loads((CHECKER/'common/source_preparation_anchor.json').read_text())
    inputs[original_anchor['preparation_seal']]=sha(original_anchor['preparation_seal'])
    need(all(sha(p)==h for p,h in inputs.items()),'prepared input closure drift')
    document['inputs_sha256']=dict(sorted(inputs.items()))
    save(output,document)
    (CASE/'evidence/S0_prepared_binding_A1_20261102_01.sha256').write_text(sha(output)+'  '+output.name+'\n')
    print(json.dumps(dict(binding_sha256=sha(output),prepared_run_ids=document['prepared_run_ids'],
                         inputs=len(inputs),simulation_authorized=False)))
    return 0

if __name__=='__main__':sys.exit(main())
