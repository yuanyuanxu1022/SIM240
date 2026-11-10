"""Read-only integrity/scope review; no native calls, no CASE writes."""
from pathlib import Path
import json,sys,hashlib,contextlib,io,datetime,ast
from unittest.mock import patch
from zoneinfo import ZoneInfo
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_S3_reuse_v1';CHECK=ROOT/'CASE/unseen_v2_reference_checker_S3_reuse_v1';IMPL=ROOT/'docs/reports/URV_S3_implementation_20261103'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())

def main():
 for n in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:(OUT/('before_'+n)).write_bytes((ROOT/'docs/reports'/n).read_bytes())
 A=CASE/'evidence/preparation_A.json';expected='5d4e70d85d586b3cdf1ebca09f82f1f4abf90166642c34f1a5f4663cdeb4f02d';need=sha(A)==expected;assert need and A.with_suffix('.sha256').read_text().strip()==expected
 d=load(A);dif=[p for p,h in d['inputs_sha256'].items() if not Path(p).is_file() or sha(p)!=h];assert not dif
 protected=dict(d['inputs_sha256'])
 for tree in [CASE,CHECK,IMPL]:
  for p in tree.rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts:protected[str(p)]=sha(p)
 (OUT/'protected_files_before.json').write_text(json.dumps(protected,indent=2)+'\n')
 for p,h in load(IMPL/'report_manifest.json').items():assert sha(IMPL/p)==h,('prior report manifest drift',p)
 sys.path.insert(0,str(CHECK/'analysis'));sys.path.insert(0,str(CASE/'scripts'))
 import stage_s3,run_S3,audit_S3_zero
 from s3_baselines import verify_baselines
 stage_s3.verify_seal(A,expected);stage_s3.validate_records(d,CHECK);records=stage_s3.validate_zero_plan(d)
 stage_s3.require_pristine(d['prepared_runs']);stage_s3.require_pristine(records)
 source=CASE.parent/'unseen_v2_reference_checker_S2_reuse_v1';science=[]
 for p in [source/'analysis/check_results.py',source/'analysis/evidence.py',source/'analysis/read_fields.py',*(source/'common').glob('*')]:
  if p.is_file():q=CHECK/p.relative_to(source);assert p.read_bytes()==q.read_bytes();science.append(str(q))
 baselines=verify_baselines(d);entries={}
 with patch('subprocess.Popen',side_effect=AssertionError('NO PROCESS IN READONLY REVIEW')) as creation:
  for name,module in [('formal_default',run_S3),('zero_default',audit_S3_zero)]:
   stdout=io.StringIO();stderr=io.StringIO()
   with patch.object(sys,'argv',['entry','--release',str(A),'--release-sha256',expected]),contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):code=module.main()
   entries[name]=dict(exit_code=code,stdout=stdout.getvalue(),stderr=stderr.getvalue());assert code==0
  assert not creation.called
 assert all(d[k] is False for k in ['simulation_authorized','formal_simulation_authorized','native_zero_step_authorized','performance_time_stepping_authorized'])
 assert d['approved_runs']==d['approved_run_ids']==d['approved_audit_run_ids']==d['actual_formal_run_ids']==d['actual_audit_run_ids']==[]
 assert not any((CASE/n).exists() for n in ['audit_attempts','launch_attempts','analysis_results','evidence/preparation_B.json'])
 assert all(sha(p)==h for p,h in protected.items())
 result=dict(reviewed_at=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),preparation_A_sha256=expected,inputs_verified=len(d['inputs_sha256']),protected_files_unchanged=len(protected),prior_report_manifest_verified=True,scientific_files_byte_identical=len(science),baseline_K=baselines,formal_records=4,zero_records=12,closed_permissions=True,entry_readonly_checks=entries,BINDING_INTEGRITY_PASS=True,SCOPE_REVIEW_PASS=False,EXECUTION_BINDING_READY=False,disposition='HOLD_FOR_R1_R2_MINIMAL_ISOLATED_REVISION',unresolved=['R1 effective output physics/zero-mode cross-check','R2 per-configuration zero readback and raw record association'],native_calls=0,VTK_reads=0,builds=0,CASE_writes=0,new_authorization_received=False,new_execution_release_created=False,NUMERICAL_GATE='NOT_EVALUATED',geometry_PASS=None,RESULT_PASS=False,REFERENCE_QUALIFIED_FOR_CASE=False,MODEL_COMPARISON='NOT_EVALUATED',physical_validation='NOT_EVALUATED',submission_ready=False)
 (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
