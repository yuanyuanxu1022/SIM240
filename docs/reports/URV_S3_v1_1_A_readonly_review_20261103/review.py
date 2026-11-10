"""Read-only frozen A review and bounded synthetic content probes. No native runs."""
from pathlib import Path
import json,hashlib,sys,contextlib,io,tempfile,datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_S3_reuse_v1_1';CHECK=ROOT/'CASE/unseen_v2_reference_checker_S3_reuse_v1_1';IMPL=ROOT/'docs/reports/URV_S3_R1_R2_revision_20261103'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())

def main():
 for n in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:(OUT/('before_'+n)).write_bytes((ROOT/'docs/reports'/n).read_bytes())
 A=CASE/'evidence/preparation_A.json';expected='7f6ca19de96949a537802f92804c787cf092e8de0eb10c681ed279736a2d3695';assert sha(A)==expected and A.with_suffix('.sha256').read_text().strip()==expected
 d=load(A);assert len(d['inputs_sha256'])==2437 and all(sha(p)==h for p,h in d['inputs_sha256'].items())
 parent=CASE.parent/'unseen_v2_reference_S3_reuse_v1/evidence/preparation_A.json';assert sha(parent)=='5d4e70d85d586b3cdf1ebca09f82f1f4abf90166642c34f1a5f4663cdeb4f02d'
 old=load(parent);assert len(old['inputs_sha256'])==2339 and all(d['inputs_sha256'].get(p)==h for p,h in old['inputs_sha256'].items())
 protected=dict(d['inputs_sha256'])
 for tree in [CASE,CHECK,IMPL]:
  for p in tree.rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts:protected[str(p)]=sha(p)
 (OUT/'protected_files_before.json').write_text(json.dumps(protected,indent=2)+'\n')
 for p,h in load(IMPL/'report_manifest.json').items():assert sha(IMPL/p)==h,('prior report manifest drift',p)
 testlog=(IMPL/'sealed_candidate_all_tests.log').read_text();assert 'Ran 130 tests' in testlog and testlog.rstrip().endswith('OK')
 post=load(IMPL/'postseal_verification.json');assert post['seal_sha256']==expected and post['full_suite_exit_code']==0 and post['full_suite_after_seal_tests']==130
 sys.path.insert(0,str(CHECK/'analysis'));sys.path.insert(0,str(CASE/'scripts'));sys.path.insert(0,str(CHECK/'tests'))
 import stage_s3 as stage,run_S3,audit_S3_zero
 from s3_baselines import verify_baselines
 from evidence import EvidenceError
 from fixtures_zero_v1_1 import ZeroFixture,LABEL
 stage.verify_seal(A,expected);stage.validate_records(d,CHECK);stage.require_pristine(d['prepared_runs']);stage.require_pristine(stage.validate_zero_plan(d));baseline=verify_baselines(d)
 flags=['simulation_authorized','formal_simulation_authorized','native_zero_step_authorized','performance_time_stepping_authorized']
 assert all(d[k] is False for k in flags)
 assert all(d[k]==[] for k in ['approved_runs','approved_run_ids','approved_audit_run_ids','actual_formal_run_ids','actual_audit_run_ids'])
 assert not any((CASE/p).exists() for p in ['launch_attempts','audit_attempts','analysis_results','evidence/preparation_B.json'])
 source=CASE.parent/'unseen_v2_reference_checker_S3_reuse_v1';scientific=[]
 for p in [source/'analysis/check_results.py',source/'analysis/evidence.py',source/'analysis/read_fields.py',*(source/'common').glob('*')]:
  if p.is_file():q=CHECK/p.relative_to(source);assert q.read_bytes()==p.read_bytes();scientific.append(str(q))
 entries={}
 with patch('subprocess.Popen',side_effect=AssertionError('NO CHILD PROCESS IN READONLY REVIEW')) as proc:
  for name,module in [('formal_default',run_S3),('zero_default',audit_S3_zero)]:
   stdout=io.StringIO();stderr=io.StringIO()
   with patch.object(sys,'argv',['entry','--release',str(A),'--release-sha256',expected]),contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):code=module.main()
   assert code==0;entries[name]=dict(exit_code=code,stdout=stdout.getvalue(),stderr=stderr.getvalue())
  rejects=[]
  for name,validator in [('zero_authority',stage.validate_zero_authority),('formal_authority',stage.validate_formal_authority)]:
   try:validator(d)
   except EvidenceError as e:rejects.append(dict(name=name,rejected=True,error=str(e)))
   else:raise AssertionError('closed A authority accepted')
  assert not proc.called
 mutations=[('positive_complete_synthetic',None)]
 for key,v in [('acceleration_m_s2','200000'),('direction','perpendicular'),('dx_m','5e-9'),('nu_m2_s','2e-6'),('formal_simulation','true')]:mutations.append(('R1_wrong_'+key,(key,v)))
 mutations.extend((n,None) for n in ['R2_duplicate_report','R2_wrong_initial_J','R2_cross_case_payload','R2_reader_nonzero_exit','R2_native_advancement'])
 probes=[]
 for name,change in mutations:
  with tempfile.TemporaryDirectory(prefix='SYNTHETIC_REVIEW_S3_V1_1_') as temp:
   f=ZeroFixture(temp)
   if name.startswith('R1_'):f.change_kv(Path(f.plan[0]['output_directory'])/'effective_config.txt',change[0],change[1])
   elif name=='R2_duplicate_report':
    for r in f.records:
     if r['mode']=='initialize':r['field_readback']=str(f.fields[0])
   elif name=='R2_wrong_initial_J':f.change_json(f.fields[0],lambda x:x['frames'][0].update(J_m2_s=[0,0,0],roundoff_bound_m2_s=[1,1,1]))
   elif name=='R2_cross_case_payload':f.change_json(f.fields[0],lambda x:x.update(payload_sha256=load(f.fields[1])['payload_sha256']))
   elif name=='R2_reader_nonzero_exit':f.change_json(f.fields[0].with_suffix('.process.json'),lambda x:x.update(independent_exit_code=2))
   elif name=='R2_native_advancement':f.change_kv(Path(f.plan[0]['output_directory'])/'execution_audit.txt','collide_and_stream_calls',1)
   f.refresh()
   with patch.object(stage,'CASE',f.root),patch.object(stage,'verify_seal',return_value=f.released),patch.object(stage,'validate_zero_authority'),patch('subprocess.Popen',side_effect=AssertionError('NO PROCESS IN SYNTHETIC PROBE')):
    try:stage.verify_zero_receipt(f.bound);accepted=True;error=None
    except EvidenceError as e:accepted=False;error=str(e)
   assert accepted==(name=='positive_complete_synthetic'),(name,accepted,error)
   probes.append(dict(name=name,accepted=accepted,error=error,fixture=LABEL,authority_checks_mocked=True,file_and_hash_checks_real=True))
 (OUT/'targeted_probe_results.json').write_text(json.dumps(probes,ensure_ascii=False,indent=2)+'\n')
 assert all(sha(p)==h for p,h in protected.items())
 result=dict(reviewed_at=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),preparation_A_path=str(A),preparation_A_sha256=expected,inputs_verified=2437,original_A_and_2339_inputs_preserved=True,scientific_files_byte_identical=len(scientific),prior_report_manifest_verified=True,prior_postseal_tests_verified=130,full_suite_rerun_this_review=False,protected_files_unchanged=len(protected),baseline_K=baseline,read_only_entries=entries,closed_A_authority_rejections=rejects,targeted_software_probes=len(probes),positive_probe_passed=True,ten_negative_probes_rejected=True,R1_R2_SCOPE_REVIEW_PASS=True,BINDING_INTEGRITY_PASS=True,preparation_review='PASS_WITH_NATIVE_AUDIT_PENDING',new_native_authorization_received=False,all_execution_permissions_closed=True,new_execution_release_created=False,start_command_delivered=False,native_calls=0,VTK_reader_invocations=0,time_steps=0,builds=0,CASE_writes=0,NUMERICAL_GATE='NOT_EVALUATED',geometry_PASS=None,RESULT_PASS=False,REFERENCE_QUALIFIED_FOR_CASE=False,MODEL_COMPARISON='NOT_EVALUATED',physical_validation='NOT_EVALUATED',submission_ready=False)
 (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
