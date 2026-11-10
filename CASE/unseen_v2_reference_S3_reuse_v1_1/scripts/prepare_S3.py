"""Prepare closed S3 identities/seals; no native/build/VTK process calls."""
from pathlib import Path
import json,sys,argparse
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1];CHECKER=CASE.parent/'unseen_v2_reference_checker_S3_reuse_v1_1'
sys.path.insert(0,str(CHECKER/'analysis'))
from evidence import need,sha,kv,save,exact_parameters
from stage_s3 import CASES,RUN_IDS,MODES,AUDIT_ID,REVISION,RESOURCES,verify_seal,verify_zero_receipt
from s3_baselines import S2_RELEASE,S2_SHA

def write_identity(run,rid,ident,mode,original):
    run.mkdir(parents=True,exist_ok=False)
    cfg=dict(original,mode=mode,run_id=rid,output_directory=str(run));path=run/'run_config.txt'
    path.write_text(''.join(k+'='+v+'\n' for k,v in cfg.items()))
    (run/'run_manifest.txt').write_text(f'run_id={rid}\nmode={mode}\n')
    return dict(run_id=rid,planned_case_id=ident,mode=mode,run_config_path=str(path),run_config_sha256=sha(path),output_directory=str(run))

def materialize():
    need(not (CASE/'evidence/identity_plan.json').exists(),'identity plan exists; refusing overwrite')
    formal=[];zero=[]
    for rid,ident in zip(RUN_IDS,CASES):
        template=ROOT/'docs/reports/Unseen_V2_reference_protocol_20261101/describe_only_templates'/(ident+'.txt');original=kv(template)
        formal.append(write_identity(CASE/'runs'/rid/'steady',rid,ident,'steady',original))
        for mode in MODES:
            aid=f'ZERO_{AUDIT_ID}_{ident}_{mode}'
            zero.append(write_identity(CASE/'audits'/AUDIT_ID/ident/mode,aid,ident,mode,original))
    save(CASE/'evidence/identity_plan.json',dict(prepared_runs=formal,zero_prepared_runs=zero))

def view():
    need(sha(S2_RELEASE)==S2_SHA,'S2 release changed')
    parent=Path('/home/dell/yuanyuanxu/SIM240/CASE/unseen_v2_reference_S3_reuse_v1/evidence/preparation_A.json');need(sha(parent)=='5d4e70d85d586b3cdf1ebca09f82f1f4abf90166642c34f1a5f4663cdeb4f02d', 'original S3 A changed')
    old=json.loads(parent.read_text());plan=json.loads((CASE/'evidence/identity_plan.json').read_text())
    anchor=CHECKER/'s3_revision/anchor.json';inputs=dict(old['inputs_sha256'])
    for folder in [CASE/'scripts',CHECKER/'analysis',CHECKER/'common',CHECKER/'revision',CHECKER/'s1_revision',CHECKER/'s2_revision',CHECKER/'s3_revision',CHECKER/'tests']:
        for p in folder.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:inputs[str(p)]=sha(p)
    for p in [parent,parent.with_suffix('.sha256'),S2_RELEASE,CASE/'evidence/identity_plan.json',CASE/'evidence/adoption.json',CASE/'evidence/baseline_references.json',CASE/'README.md',CHECKER/'README.md']:
        inputs[str(p)]=sha(p)
    scope=ROOT/'docs/reports/URV_S3_prerun_scope_review_20261103'
    for p in scope.iterdir():
        if p.is_file():inputs[str(p)]=sha(p)
    review=ROOT/'docs/reports/URV_S3_A_readonly_review_20261103'
    for p in review.iterdir():
        if p.is_file():inputs[str(p)]=sha(p)
    refs=json.loads((CASE/'evidence/baseline_references.json').read_text())
    for ref in refs:
        for k in ['config_path','completion_path','acceptance_path']:
            p=Path(ref[k]);inputs[str(p)]=sha(p)
        comp=json.loads(Path(ref['completion_path']).read_text());run=Path(ref['completion_path']).parent
        for name,h in comp['output_sha256'].items():inputs[str(run/name)]=h
        for p in Path(ref['acceptance_path']).parent.iterdir():
            if p.is_file():inputs[str(p)]=sha(p)
    for r in plan['prepared_runs']+plan['zero_prepared_runs']:
        for p in [Path(r['run_config_path']),Path(r['output_directory'])/'run_manifest.txt']:inputs[str(p)]=sha(p)
    return dict(protocol_id='URV-v1',schema_version='URV-EXEC-1.1',stage='S3_REG_LINEARITY',addendum_id=REVISION,kind='S3_PREPARATION_A_NOT_AUTHORIZATION',
        simulation_authorized=False,formal_simulation_authorized=False,native_zero_step_authorized=False,performance_time_stepping_authorized=False,
        preparation_only_build=False,approved_run_ids=[],approved_runs=[],approved_audit_run_ids=[],actual_formal_run_ids=[],actual_audit_run_ids=[],
        prepared_runs=plan['prepared_runs'],prepared_run_ids=list(RUN_IDS),zero_prepared_runs=plan['zero_prepared_runs'],resources=RESOURCES,
        launch_authorization=dict(user_explicitly_authorized=False,user_instruction_verbatim=None),AI_may_start_solver=False,user_manually_starts=True,
        automatic_retry_authorized=False,automatic_extension_authorized=False,S4_authorized=False,S5_authorized=False,
        author_external_data_history_confirmation=old['author_external_data_history_confirmation'],author_reply_file=old['author_reply_file'],author_reply_sha256=old['author_reply_sha256'],
        external_history_independently_verified=False,author_confirmation_scope=old['author_confirmation_scope'],provenance=old['provenance'],
        source_revision=dict(id=REVISION,anchor=str(anchor),sha256=sha(anchor)),inputs_sha256=inputs,baseline_references=refs,h75_regression_references={},density_capture='NOT_APPLICABLE_S0_ONLY',
        exact_parameters={r['planned_case_id']:exact_parameters(kv(r['run_config_path'])) for r in plan['prepared_runs']},
        NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None,REFERENCE_QUALIFIED_FOR_CASE=False,reference_qualified=False,
        strict_error_bound_established=False,MODEL_COMPARISON='NOT_EVALUATED',physical_validation='NOT_EVALUATED',submission_ready=False,
        zero_audit_status='NOT_EXECUTED',performance_status='NOT_PROPOSED',next_stage_started=False,F04='OPEN_OUT_OF_SCOPE')

def seal():
    d=view();need(all(sha(p)==h for p,h in d['inputs_sha256'].items()),'cannot seal changed source')
    path=CASE/'evidence/preparation_A.json';save(path,d);verify_seal(path,sha(path))
    with path.with_suffix('.sha256').open('x') as f:f.write(sha(path)+'\n')

def finalize_zero():
    original=CASE/'evidence/preparation_A.json';data=verify_seal(original,sha(original))
    zero=CASE/'audits'/AUDIT_ID/'verification.json'
    need(zero.is_file(), 'real zero audit missing; cannot finalize B')
    evidence=json.loads(zero.read_text())
    for p in (CASE/'audits'/AUDIT_ID).rglob('*'):
        if p.is_file():need(not p.is_symlink(),'audit symlink');data['inputs_sha256'][str(p)]=sha(p)
    audit_release=Path(evidence['audit_release_path']);released=json.loads(audit_release.read_text())
    for p,h in released['inputs_sha256'].items():need(sha(p)==h,'audit input drift');data['inputs_sha256'][p]=h
    for p in [original,original.with_suffix('.sha256'),audit_release]:data['inputs_sha256'][str(p)]=sha(p)
    data.update(kind='S3_PREPARATION_B_NOT_AUTHORIZATION',zero_audit_status='PASSED',zero_audit_path=str(CASE/'audits'/AUDIT_ID/'verification.json'),zero_audit_sha256=sha(CASE/'audits'/AUDIT_ID/'verification.json'),preparation_A_path=str(original),preparation_A_sha256=sha(original))
    verify_zero_receipt(data);path=CASE/'evidence/preparation_B.json';save(path,data)
    with path.with_suffix('.sha256').open('x') as f:f.write(sha(path)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['identities','seal','finalize-zero']);a=p.parse_args()
    {'identities':materialize,'seal':seal,'finalize-zero':finalize_zero}[a.action]()
