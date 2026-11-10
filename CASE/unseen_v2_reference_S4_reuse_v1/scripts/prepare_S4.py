"""Materialize closed S4 identities and seals. No native/build/VTK calls."""
from pathlib import Path
import argparse,json,sys
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1]
CHECKER=CASE.parent/'unseen_v2_reference_checker_S4_reuse_v1'
PARENT=CASE.parent/'unseen_v2_reference_S3_reuse_v1_1'
PRIOR=ROOT/'docs/reports/URV_S4_prerun_scope_review_20261103_200311'
sys.path.insert(0,str(CHECKER/'analysis'))
from evidence import need,sha,kv,save,exact_parameters
from stage_s4 import CASES,RUN_IDS,MODES,AUDIT_ID,REVISION,RESOURCES,verify_seal,verify_zero_receipt
from revision_s4_reuse import PARENT_SHA

def write_identity(run,rid,ident,mode,original):
    run.mkdir(parents=True,exist_ok=False);cfg=dict(original,mode=mode,run_id=rid,output_directory=str(run))
    path=run/'run_config.txt';path.write_text(''.join(k+'='+v+'\n' for k,v in cfg.items()))
    (run/'run_manifest.txt').write_text(f'run_id={rid}\nmode={mode}\n')
    return dict(run_id=rid,planned_case_id=ident,mode=mode,run_config_path=str(path),run_config_sha256=sha(path),output_directory=str(run))

def materialize():
    need(not (CASE/'evidence/identity_plan.json').exists(),'identity plan exists; no overwrite')
    formal=[];zero=[]
    for rid,ident in zip(RUN_IDS,CASES):
        original=kv(ROOT/'docs/reports/Unseen_V2_reference_protocol_20261101/describe_only_templates'/(ident+'.txt'))
        formal.append(write_identity(CASE/'runs'/rid/'steady',rid,ident,'steady',original))
        for mode in MODES:
            aid=f'ZERO_{AUDIT_ID}_{ident}_{mode}'
            zero.append(write_identity(CASE/'audits'/AUDIT_ID/ident/mode,aid,ident,mode,original))
    save(CASE/'evidence/identity_plan.json',dict(prepared_runs=formal,zero_prepared_runs=zero))

def view():
    parent=PARENT/'evidence/S3_formal_launch_release_v1_1_20261103_01.json'
    need(sha(parent)==PARENT_SHA,'S3 release changed');old=json.loads(parent.read_text())
    planpath=CASE/'evidence/identity_plan.json';plan=json.loads(planpath.read_text());inputs=dict(old['inputs_sha256'])
    anchor=CHECKER/'s4_revision/anchor.json'
    # New software copied in isolation; genuine predecessor build files stay at original paths.
    for tree in [CASE/'scripts',CHECKER,PRIOR,ROOT/'docs/reports/URV_S3_completed_review_20261103_172033']:
        for p in tree.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:inputs[str(p)]=sha(p)
    for rec in old['approved_runs']:
        for tree in [Path(rec['output_directory']),PARENT/'analysis_results'/rec['run_id']]:
            for p in tree.rglob('*'):
                if p.is_file():inputs[str(p)]=sha(p)
    for p in (PARENT/'launch_attempts'/PARENT_SHA).iterdir():
        if p.is_file():inputs[str(p)]=sha(p)
    for p in [parent,parent.with_suffix('.sha256'),planpath,CASE/'README.md',CASE/'evidence/adoption.json']:
        inputs[str(p)]=sha(p)
    for rec in plan['prepared_runs']+plan['zero_prepared_runs']:
        for p in [Path(rec['run_config_path']),Path(rec['output_directory'])/'run_manifest.txt']:inputs[str(p)]=sha(p)
    return dict(protocol_id='URV-v1',schema_version='URV-EXEC-1.1',stage='S4_THIN_GRID',addendum_id=REVISION,
        kind='S4_PREPARATION_A_NOT_AUTHORIZATION',simulation_authorized=False,formal_simulation_authorized=False,
        native_zero_step_authorized=False,initial_field_readback_authorized=False,performance_time_stepping_authorized=False,
        preparation_only_build=False,approved_run_ids=[],approved_runs=[],approved_audit_run_ids=[],actual_formal_run_ids=[],actual_audit_run_ids=[],
        prepared_runs=plan['prepared_runs'],prepared_run_ids=list(RUN_IDS),zero_prepared_runs=plan['zero_prepared_runs'],resources=RESOURCES,
        launch_authorization=dict(user_explicitly_authorized=False,user_instruction_verbatim=None),AI_may_start_solver=False,user_manually_starts=True,
        automatic_retry_authorized=False,automatic_extension_authorized=False,S5_authorized=False,
        author_external_data_history_confirmation=old['author_external_data_history_confirmation'],author_reply_file=old['author_reply_file'],author_reply_sha256=old['author_reply_sha256'],
        external_history_independently_verified=False,author_confirmation_scope=old['author_confirmation_scope'],
        provenance=old['provenance'],source_revision=dict(id=REVISION,anchor=str(anchor),sha256=sha(anchor)),inputs_sha256=inputs,
        h75_regression_references={},density_capture='NOT_APPLICABLE_S0_ONLY',
        exact_parameters={rec['planned_case_id']:exact_parameters(kv(rec['run_config_path'])) for rec in plan['prepared_runs']},
        NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None,REFERENCE_QUALIFIED_FOR_CASE=False,reference_qualified=False,
        strict_error_bound_established=False,MODEL_COMPARISON='NOT_EVALUATED',physical_validation='NOT_EVALUATED',submission_ready=False,
        zero_audit_status='NOT_EXECUTED',performance_status='SEPARATE_RESOURCE_DECISION_PENDING',next_stage_started=False,F04='OPEN_OUT_OF_SCOPE')

def seal():
    data=view();need(all(sha(p)==h for p,h in data['inputs_sha256'].items()),'cannot seal drifted inputs')
    from contracts import verify_provenance
    verify_provenance(data)
    path=CASE/'evidence/preparation_A.json';save(path,data);verify_seal(path,sha(path))
    with path.with_suffix('.sha256').open('x') as f:f.write(sha(path)+'\n')

def finalize_zero():
    original=CASE/'evidence/preparation_A.json';data=verify_seal(original,sha(original))
    zero=CASE/'audits'/AUDIT_ID/'verification.json';need(zero.is_file(),'real S4 zero audit missing; no B')
    evidence=json.loads(zero.read_text());audit_release=Path(evidence['audit_release_path'])
    need(sha(audit_release)==evidence['audit_release_sha256'],'zero release drift')
    released=json.loads(audit_release.read_text())
    for p,h in released['inputs_sha256'].items():
        need(sha(p)==h and (p not in data['inputs_sha256'] or data['inputs_sha256'][p]==h),'conflicting zero inputs')
        data['inputs_sha256'][p]=h
    for p in [original,original.with_suffix('.sha256'),audit_release,*(CASE/'audits'/AUDIT_ID).rglob('*')]:
        if p.is_file():need(not p.is_symlink(),'audit symlink');data['inputs_sha256'][str(p)]=sha(p)
    data.update(kind='S4_PREPARATION_B_NOT_AUTHORIZATION',zero_audit_status='PASSED',
        zero_audit_path=str(zero),zero_audit_sha256=sha(zero),preparation_A_path=str(original),preparation_A_sha256=sha(original),
        actual_audit_run_ids=[r['run_id'] for r in released['zero_prepared_runs']])
    verify_zero_receipt(data);path=CASE/'evidence/preparation_B.json';save(path,data)
    with path.with_suffix('.sha256').open('x') as f:f.write(sha(path)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['identities','seal','finalize-zero']);args=parser.parse_args()
    {'identities':materialize,'seal':seal,'finalize-zero':finalize_zero}[args.action]()
