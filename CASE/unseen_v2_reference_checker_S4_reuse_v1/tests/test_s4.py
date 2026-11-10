"""S4 authority, failure-stop, and packet tests. All process interfaces simulated."""
from pathlib import Path
import contextlib,copy,io,json,sys,tempfile,types,unittest
from unittest.mock import patch
CHECK=Path(__file__).resolve().parents[1];CASE=CHECK.parent/'unseen_v2_reference_S4_reuse_v1'
sys.path.insert(0,str(CHECK/'analysis'));sys.path.insert(0,str(CASE/'scripts'))
from evidence import EvidenceError,sha,kv,exact_parameters
from contracts import verify_provenance
import stage_s4 as stage
import prepare_S4 as prep
import run_S4 as runner
import audit_S4_zero as auditor
import check_s4_grid
from s4_grid import grid_for_direction

class S4Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=prep.view()
 def mutated(self,change):
  d=copy.deepcopy(self.data);change(d)
  with self.assertRaises((EvidenceError,KeyError)):verify_provenance(d)
 def test_real_closed_provenance(self):verify_provenance(self.data)
 def test_six_and_eighteen_exact(self):
  self.assertEqual(len(stage.validate_records(self.data,CHECK)),6);self.assertEqual(len(stage.validate_zero_plan(self.data)),18)
 def test_wrong_stage(self):self.mutated(lambda d:d.update(stage='S2_REG_GRID'))
 def test_wrong_family(self):self.mutated(lambda d:d['prepared_runs'][0].update(planned_case_id='URV1_U_REG_P_dx5_a100000'))
 def test_missing_case(self):self.mutated(lambda d:d['prepared_runs'].pop())
 def test_extra_case(self):self.mutated(lambda d:d['prepared_runs'].append(copy.deepcopy(d['prepared_runs'][0])))
 def test_wrong_order(self):self.mutated(lambda d:d['prepared_runs'].reverse())
 def test_wrong_run_id(self):self.mutated(lambda d:d['prepared_runs'][0].update(run_id='SYNTHETIC_WRONG'))
 def test_wrong_direction(self):self.mutated(lambda d:d['prepared_runs'][0].update(planned_case_id=stage.CASES[1]))
 def test_wrong_binary_hash(self):self.mutated(lambda d:d['inputs_sha256'].update({d['provenance']['native_binary']:'0'*64}))
 def test_missing_source(self):self.mutated(lambda d:d['inputs_sha256'].pop(d['provenance']['native_sources'][0]))
 def test_missing_library(self):
  env=json.loads(Path(self.data['provenance']['build_environment']).read_text());self.mutated(lambda d:d['inputs_sha256'].pop(next(iter(env['dynamic_library_sha256']))))
 def test_missing_predecessor_raw(self):
  anchor=json.loads((CHECK/'s4_revision/anchor.json').read_text());prior=json.loads(Path(anchor['predecessor_release_path']).read_text())
  self.mutated(lambda d:d['inputs_sha256'].pop(str(Path(prior['approved_runs'][0]['output_directory'])/'diagnostics.csv')))
 def test_wrong_budget(self):self.mutated(lambda d:d['resources']['solver_wall_cap_seconds_by_dx_nm'].update({'1.25':86400}))
 def test_retry_permission(self):self.mutated(lambda d:d.update(automatic_retry_authorized=True))
 def test_extension_permission(self):self.mutated(lambda d:d.update(automatic_extension_authorized=True))
 def test_next_stage_permission(self):self.mutated(lambda d:d.update(S5_authorized=True))
 def test_performance_permission(self):self.mutated(lambda d:d.update(performance_time_stepping_authorized=True))
 def test_scientific_files_exact(self):
  old=CHECK.parent/'unseen_v2_reference_checker_S3_reuse_v1_1'
  for p in (old/'common').iterdir():self.assertEqual(p.read_bytes(),(CHECK/'common'/p.name).read_bytes())
  for n in ['check_results.py','evidence.py','read_fields.py','zero_evidence.py']:self.assertEqual((old/'analysis'/n).read_bytes(),(CHECK/'analysis'/n).read_bytes())
 def test_old_stage_guards_reject_S4(self):
  from stage_s2 import validate_records as s2
  from stage_s3 import validate_records as s3
  for f in [s2,s3]:
   with self.assertRaises(EvidenceError):f(self.data,CHECK)
 def test_exact_time_and_geometry(self):
  self.assertEqual([runner.wall_cap(r['run_config_path']) for r in self.data['prepared_runs']],[3600,3600,14400,14400,43200,43200])
  for i,r in enumerate(self.data['prepared_runs']):
   p=exact_parameters(kv(r['run_config_path']));self.assertEqual((p['nodes'],p['window'],p['cap']),[(32256,162,23232),(258048,648,92928),(2064384,2592,371712)][i//2])
 def test_zero_steady_rejected(self):
  d=copy.deepcopy(self.data);d['zero_prepared_runs'][0]['mode']='steady'
  with self.assertRaises(EvidenceError):stage.validate_zero_plan(d)
 def test_zero_missing_or_duplicate(self):
  for missing in [True,False]:
   d=copy.deepcopy(self.data)
   if missing:d['zero_prepared_runs'].pop()
   else:d['zero_prepared_runs'][1]=copy.deepcopy(d['zero_prepared_runs'][0])
   with self.assertRaises(EvidenceError):stage.validate_zero_plan(d)
 def test_native_wrapper_refuses_formal(self):
  with patch.object(auditor,'native_process') as native:
   with self.assertRaises(EvidenceError):auditor.call_native('INERT_NOT_EXECUTABLE',self.data['prepared_runs'][0],{})
   native.assert_not_called()
 def test_closed_authority_refused(self):
  for f in [stage.validate_zero_authority,stage.validate_formal_authority]:
   with self.assertRaises(EvidenceError):f(self.data)
 def test_flags_alone_not_authorization(self):
  d=copy.deepcopy(self.data);d.update(kind='AUTHORIZED_EXECUTION_LAUNCH_RELEASE',simulation_authorized=True,formal_simulation_authorized=True,approved_run_ids=list(stage.RUN_IDS),approved_runs=d['prepared_runs'])
  with self.assertRaises(EvidenceError):stage.validate_formal_authority(d)
 def test_formal_requires_actual_B(self):
  d=copy.deepcopy(self.data);d.update(kind='AUTHORIZED_EXECUTION_LAUNCH_RELEASE',simulation_authorized=True,formal_simulation_authorized=True,approved_run_ids=list(stage.RUN_IDS),approved_runs=d['prepared_runs'])
  with patch.object(stage,'explicit_authority',return_value=dict(stage=stage.STAGE,formal_simulation_authorized=True,approved_run_ids=list(stage.RUN_IDS))),patch.object(stage,'verify_zero_receipt') as zero:
   with self.assertRaises(EvidenceError):stage.validate_formal_authority(d)
   zero.assert_not_called()
 def test_real_closed_exec_no_output_or_process(self):
  with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S4_CLOSED_') as t:
   p=Path(t)/'CLOSED.json';p.write_text(json.dumps(self.data))
   with patch.object(runner,'native_process') as native,patch.object(auditor,'call_native') as audit,patch('subprocess.Popen',side_effect=AssertionError('NO PROCESS')):
    for f in [runner.execute,auditor.execute]:
     with self.assertRaises(EvidenceError):f(p,sha(p),self.data)
    native.assert_not_called();audit.assert_not_called()
   self.assertFalse((CASE/'launch_attempts').exists());self.assertFalse((CASE/'audit_attempts').exists())
 def test_both_default_entries_readonly(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'CLOSED.json';p.write_text(json.dumps(self.data))
   for module in [runner,auditor]:
    with patch('subprocess.Popen',side_effect=AssertionError('NO PROCESS')),patch.object(sys,'argv',['entry','--release',str(p),'--release-sha256',sha(p)]),contextlib.redirect_stdout(io.StringIO()):self.assertEqual(module.main(),0)
 def test_aggregate_entry_refuses_preparation(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'CLOSED.json';p.write_text(json.dumps(self.data));out=Path(t)/'out'
   with self.assertRaises(EvidenceError):check_s4_grid.analyze(p,sha(p),out)
   self.assertFalse(out.exists())
 def test_external_SHA_and_false_progress(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'CLOSED.json';p.write_text(json.dumps(self.data))
   with self.assertRaises(EvidenceError):stage.verify_seal(p,'0'*64)
   for key,val in [('RESULT_PASS',True),('geometry_PASS',True),('actual_audit_run_ids',['FAKE']),('approved_audit_run_ids',['FAKE']),('initial_field_readback_authorized',True)]:
    d=copy.deepcopy(self.data);d[key]=val;p.write_text(json.dumps(d))
    with self.subTest(key=key),self.assertRaises(EvidenceError):stage.verify_seal(p,sha(p))
 def test_used_directory(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'run.log').write_text('SYNTHETIC')
   with self.assertRaises(EvidenceError):stage.require_pristine([dict(output_directory=str(p))])
 def pipeline(self,native_code=0,checker_code=0,accepted=True,drift=False,timeout=False,checker_timeout=False,grid_pass=True):
  with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S4_PIPELINE_') as t:
   folder=Path(t);records=[]
   for i,(dx,d) in enumerate([(dx,d) for dx in [5,2.5,1.25] for d in ['P','T']]):
    rid=f'SYNTHETIC_S4_{i}';run=folder/'runs'/rid/'steady';run.mkdir(parents=True)
    (run/'run_config.txt').write_text(f'mode=steady\nrun_id={rid}\noutput_directory={run}\ndx_nm={dx}\ndirection={d}\n')
    (run/'run_manifest.txt').write_text(f'run_id={rid}\nmode=steady\n');records.append(dict(run_id=rid,planned_case_id=f'SYNTHETIC_{i}',output_directory=str(run),run_config_path=str(run/'run_config.txt')))
   sentinel=folder/'INPUT';sentinel.write_text('fixed');doc=dict(prepared_runs=records,inputs_sha256={str(sentinel):sha(sentinel)},provenance=dict(native_binary='INERT_NEVER_EXECUTED'))
   def native(*args):
    if drift:sentinel.write_text('changed')
    return dict(independent_process_exit_code=native_code,timed_out=timeout,resource_stop_reason='wall_timeout' if timeout else None,elapsed_seconds=0.)
   def checked(argv,**kwargs):
    if checker_timeout:raise runner.subprocess.TimeoutExpired(argv,3600)
    p=Path(argv[argv.index('--out')+1]);p.mkdir(parents=True);(p/'acceptance.json').write_text(json.dumps(dict(RESULT_PASS=accepted,NUMERICAL_GATE='PASS',geometry_PASS=True,fixture='SYNTHETIC')))
    return types.SimpleNamespace(returncode=checker_code)
   failure=native_code or checker_code or not accepted or drift or timeout or checker_timeout or not grid_pass
   with patch.object(runner,'CASE',folder),patch.object(runner,'binding',return_value=doc),patch.object(runner,'validate_formal_authority'),patch.object(runner,'resources',return_value={}),patch.object(runner,'native_process',side_effect=native) as process,patch.object(runner.subprocess,'run',side_effect=checked),patch('s4_grid.grid_for_direction',return_value=dict(GRID_CHECKS_PASS=grid_pass)):
    if failure:
     with self.assertRaises((EvidenceError,runner.subprocess.TimeoutExpired)):runner.execute(Path('INERT'),'synthetic',doc)
     self.assertEqual(process.call_count,6 if not grid_pass and not(native_code or checker_code or not accepted or drift or timeout or checker_timeout) else 1)
    else:runner.execute(Path('INERT'),'synthetic',doc);self.assertEqual(process.call_count,6)
    self.assertEqual((folder/'launch_attempts/synthetic/S4_completed.json').exists(),not bool(failure))
    if not grid_pass:self.assertTrue((folder/'launch_attempts/synthetic/S4_grid_report.json').exists())
 def test_native_failure_stops(self):self.pipeline(native_code=3)
 def test_native_timeout_stops(self):self.pipeline(timeout=True)
 def test_checker_failure_stops(self):self.pipeline(checker_code=2)
 def test_checker_timeout_stops(self):self.pipeline(checker_timeout=True)
 def test_false_acceptance_stops(self):self.pipeline(accepted=False)
 def test_input_drift_stops(self):self.pipeline(drift=True)
 def test_grid_failure_preserved_without_completed(self):self.pipeline(grid_pass=False)
 def test_six_success_no_next_stage(self):self.pipeline()
 def grid_fixture(self,root):
  doc=copy.deepcopy(self.data);accepted={};h='a'*64
  for i,rec in enumerate(doc['prepared_runs']):
   run=Path(root)/rec['run_id'];run.mkdir();cfg=kv(rec['run_config_path']);cfg['output_directory']=str(run)
   path=run/'run_config.txt';path.write_text(''.join(k+'='+v+'\n' for k,v in cfg.items()));rec.update(output_directory=str(run),run_config_path=str(path),run_config_sha256=sha(path))
   K=[1.008,1.002,1.0005][i//2]*1e-23
   (run/'result.txt').write_text(f'J_main_m2_s={K*100000/1e-6}\nwindow_main_rel_span=1e-6\n')
   c=dict(run_id=rec['run_id'],planned_case_id=rec['planned_case_id'],release_sha256=h,independent_process_exit_code=0,timed_out=False,resource_stop_reason=None,inputs_before_sha256=doc['inputs_sha256'],inputs_after_sha256=doc['inputs_sha256'],inputs_unchanged=True,output_sha256={p.name:sha(p) for p in run.iterdir()})
   cp=run/'completion.json';cp.write_text(json.dumps(c))
   accepted[rec['run_id']]=dict(run_id=rec['run_id'],planned_case_id=rec['planned_case_id'],stage=stage.STAGE,direction=cfg['direction'],dx_nm=float(cfg['dx_nm']),acceleration_m_s2=100000,RESULT_PASS=True,NUMERICAL_GATE='PASS',geometry_PASS=True,independent_exit_code=0,release_sha256=h,completion_sha256=sha(cp),scalar=dict(K_m3=K,final_span=1e-6))
  return doc,accepted,h
 def test_local_grid_keeps_reference_closed(self):
  with tempfile.TemporaryDirectory() as t:
   d,a,h=self.grid_fixture(t);v=grid_for_direction(d,'P',a,h);self.assertTrue(v['GRID_CHECKS_PASS']);self.assertFalse(v['REFERENCE_QUALIFIED_FOR_CASE']);self.assertEqual(v['MODEL_COMPARISON'],'NOT_EVALUATED')
 def test_grid_wrong_release_or_K_or_extra_raw(self):
  for mutation in ['release','K','extra','missing','acceptance','span']:
   with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as t:
    d,a,h=self.grid_fixture(t);rid=d['prepared_runs'][0]['run_id']
    if mutation=='release':h='b'*64
    elif mutation=='K':a[rid]['scalar']['K_m3']*=2
    elif mutation=='extra':(Path(d['prepared_runs'][0]['output_directory'])/'EXTRA').write_text('SYNTHETIC')
    elif mutation=='missing':a.pop(rid)
    elif mutation=='span':a[rid]['scalar']['final_span']=2e-6
    else:a[rid]['RESULT_PASS']=False
    with self.assertRaises(EvidenceError):grid_for_direction(d,'P',a,h)
 def test_zero_pipeline_18_plus_6_no_next_stage(self):self.zero_pipeline()
 def test_zero_pipeline_native_failure_stops(self):self.zero_pipeline(native_failure=True)
 def test_zero_pipeline_reader_failure_stops(self):self.zero_pipeline(reader_failure=True)
 def zero_pipeline(self,native_failure=False,reader_failure=False):
  from fixtures_zero_s4 import ZeroFixture
  with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S4_ZERO_PIPELINE_') as t:
   fixture=ZeroFixture(t);fixture.receipt.unlink();fixture.manifest.unlink()
   doc=dict(zero_prepared_runs=fixture.plan,inputs_sha256={},provenance=dict(native_binary='INERT_SOFTWARE_ONLY'),preparation_A_sha256='a'*64)
   def native(binary,record,env):
    if native_failure:raise EvidenceError('SYNTHETIC native failure')
    return dict(native_exit_code=0,collide_and_stream_calls=0,elapsed_seconds=0.,output=record['output_directory'])
   def reader(*args):
    if reader_failure:raise EvidenceError('SYNTHETIC reader failure')
   with patch.object(auditor,'CASE',fixture.root),patch.object(auditor,'AUDIT_ID',stage.AUDIT_ID),patch.object(auditor,'verify_seal',return_value=doc),patch.object(auditor,'validate_zero_authority'),patch.object(auditor,'validate_zero_plan',return_value=fixture.plan),patch.object(auditor,'require_pristine'),patch.object(auditor,'resources',return_value={}),patch.object(auditor,'unchanged',return_value={}),patch.object(auditor,'call_native',side_effect=native) as calls,patch.object(auditor,'field_readback',side_effect=reader) as readers,patch('subprocess.Popen',side_effect=AssertionError('NO PROCESS')),contextlib.redirect_stdout(io.StringIO()):
    if native_failure or reader_failure:
     with self.assertRaises(EvidenceError):auditor.execute(Path('INERT'),'synthetic',doc)
     self.assertEqual(calls.call_count,1 if native_failure else 3);self.assertEqual(readers.call_count,0 if native_failure else 1)
     self.assertFalse(fixture.receipt.exists())
    else:
     auditor.execute(Path('INERT'),'synthetic',doc);self.assertEqual(calls.call_count,18);self.assertEqual(readers.call_count,6)
     result=json.loads(fixture.receipt.read_text());self.assertEqual(result['actual_time_steps'],0);self.assertFalse(result['next_stage_started'])
 def test_formal_resource_decision_missing_after_B_rejected(self):self.formal_resource_fixture(False)
 def test_formal_resource_scope_synthetic_structure(self):self.formal_resource_fixture(True)
 def formal_resource_fixture(self,present):
  with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S4_RESOURCE_AUTH_') as t:
   root=Path(t);(root/'evidence').mkdir();d=copy.deepcopy(self.data)
   d.update(kind='AUTHORIZED_EXECUTION_LAUNCH_RELEASE',simulation_authorized=True,formal_simulation_authorized=True,approved_runs=d['prepared_runs'],approved_run_ids=list(stage.RUN_IDS))
   b=root/'evidence/preparation_B.json';b.write_text(json.dumps(dict(kind='S4_PREPARATION_B_NOT_AUTHORIZATION',simulation_authorized=False,zero_audit_status='PASSED',inputs_sha256={},prepared_runs=d['prepared_runs'])))
   d.update(preparation_B_path=str(b),preparation_B_sha256=sha(b));d['inputs_sha256'][str(b)]=sha(b)
   if present:
    p=root/'SYNTHETIC_RESOURCE_NOT_REAL_AUTHORIZATION.json';p.write_text(json.dumps(dict(stage=stage.STAGE,resource_decision_accepted=True,ordered_run_ids=list(stage.RUN_IDS),solver_wall_cap_seconds_by_dx_nm=stage.RESOURCES['solver_wall_cap_seconds_by_dx_nm'],per_checker_wait_cap_seconds=3600,automatic_retry=False,automatic_extension=False,user_instruction_verbatim='SYNTHETIC_SCHEMA_ONLY_NOT_REAL_AUTHORIZATION')))
    d['inputs_sha256'][str(p)]=sha(p);d['formal_resource_decision']=dict(path=str(p),sha256=sha(p))
   with patch.object(stage,'CASE',root),patch.object(stage,'explicit_authority',return_value=dict(stage=stage.STAGE,formal_simulation_authorized=True,approved_run_ids=list(stage.RUN_IDS))),patch.object(stage,'verify_zero_receipt') as zero:
    if present:stage.validate_formal_authority(d)
    else:
     with self.assertRaises(EvidenceError):stage.validate_formal_authority(d)
    zero.assert_called_once()

if __name__=='__main__':unittest.main(verbosity=2)
