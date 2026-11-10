"""S3 software tests; synthetic processes only, never native or VTK execution."""
from pathlib import Path
import contextlib,copy,io,json,sys,tempfile,types,unittest
from unittest.mock import patch
CHECKER=Path(__file__).resolve().parents[1];CASE=CHECKER.parent/'unseen_v2_reference_S3_reuse_v1_1'
sys.path.insert(0,str(CHECKER/'analysis'));sys.path.insert(0,str(CASE/'scripts'))
from evidence import EvidenceError,sha,kv
from contracts import verify_provenance
from stage_s3 import validate_records,validate_zero_plan,validate_zero_authority,validate_formal_authority,verify_seal,require_pristine,CASES,RUN_IDS,MODES,RESOURCES
from s3_baselines import verify_baselines,linear_metric,control_for_direction
import prepare_S3 as prep
import run_S3 as runner
import audit_S3_zero as auditor
import check_linearity

class S3Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=prep.view()
 def mutated(self,change):
  d=copy.deepcopy(self.data);change(d)
  with self.assertRaises(EvidenceError):verify_provenance(d)
 def test_exact_four_and_twelve(self):
  self.assertEqual(len(validate_records(self.data,CHECKER)),4);self.assertEqual(len(validate_zero_plan(self.data)),12)
 def test_closed_real_provenance(self):
  verify_provenance(self.data)
  for k in ['simulation_authorized','native_zero_step_authorized','performance_time_stepping_authorized','formal_simulation_authorized']:self.assertIs(self.data[k],False)
 def test_scientific_bytes_preserved(self):
  old=CASE.parent/'unseen_v2_reference_checker_S2_reuse_v1'
  for n in ['evidence.py','check_results.py','read_fields.py']:self.assertEqual((CHECKER/'analysis'/n).read_bytes(),(old/'analysis'/n).read_bytes())
  for p in (CHECKER/'common').iterdir():
   if p.is_file():self.assertEqual(p.read_bytes(),(old/'common'/p.name).read_bytes())
 def test_wrong_stage(self):self.mutated(lambda d:d.update(stage='S2_REG_GRID'))
 def test_missing_case(self):self.mutated(lambda d:d['prepared_runs'].pop())
 def test_extra_case(self):self.mutated(lambda d:d['prepared_runs'].append(copy.deepcopy(d['prepared_runs'][0])))
 def test_wrong_order(self):self.mutated(lambda d:d['prepared_runs'].reverse())
 def test_middle_force_cannot_be_new_point(self):self.mutated(lambda d:d['prepared_runs'][0].update(planned_case_id='URV1_U_REG_P_dx2p5_a100000'))
 def test_wrong_direction_case(self):self.mutated(lambda d:d['prepared_runs'][0].update(planned_case_id=CASES[1]))
 def test_PERF_identity_rejected(self):self.mutated(lambda d:d['prepared_runs'][0].update(run_id='PERF_NOT_S3'))
 def test_native_binary_fingerprint(self):self.mutated(lambda d:d['inputs_sha256'].update({d['provenance']['native_binary']:'0'*64}))
 def test_native_source_coverage(self):self.mutated(lambda d:d['inputs_sha256'].pop(d['provenance']['native_sources'][0]))
 def test_original_library_coverage(self):
  e=json.loads(Path(self.data['provenance']['build_environment']).read_text());self.mutated(lambda d:d['inputs_sha256'].pop(next(iter(e['dynamic_library_sha256']))))
 def test_wrong_budget(self):self.mutated(lambda d:d['resources']['solver_wall_cap_seconds_by_dx_nm'].update({'2.5':28800}))
 def test_retry_flag(self):self.mutated(lambda d:d.update(automatic_retry_authorized=True))
 def test_next_stage_flag(self):self.mutated(lambda d:d.update(S4_authorized=True))
 def test_performance_flag(self):self.mutated(lambda d:d.update(performance_time_stepping_authorized=True))
 def test_original_S2_guards_do_not_accept_S3(self):
  from stage_s2 import validate_records as prior
  with self.assertRaises(EvidenceError):prior(self.data,CHECKER)
 def test_baseline_pair_real_hashes(self):self.assertEqual(set(verify_baselines(self.data)),{'P','T'})
 def test_baseline_wrong_release(self):self.mutated(lambda d:d['baseline_references'][0].update(release_sha256='0'*64))
 def test_baseline_wrong_run(self):self.mutated(lambda d:d['baseline_references'][0].update(run_id='FAKE'))
 def test_baseline_cross_direction(self):self.mutated(lambda d:d['baseline_references'][0].update(direction='T'))
 def test_baseline_wrong_K(self):self.mutated(lambda d:d['baseline_references'][0].update(K_m3=1.))
 def test_baseline_missing_output_binding(self):
  p=Path(self.data['baseline_references'][0]['completion_path']).parent/'diagnostics.csv';self.mutated(lambda d:d['inputs_sha256'].pop(str(p)))
 def test_zero_missing_call(self):
  d=copy.deepcopy(self.data);d['zero_prepared_runs'].pop()
  with self.assertRaises(EvidenceError):validate_zero_plan(d)
 def test_zero_steady_mode(self):
  d=copy.deepcopy(self.data);d['zero_prepared_runs'][0]['mode']='steady'
  with self.assertRaises(EvidenceError):validate_zero_plan(d)
 def test_zero_output_escape(self):
  d=copy.deepcopy(self.data);d['zero_prepared_runs'][0]['output_directory']=str(CASE.parent)
  with self.assertRaises(EvidenceError):validate_zero_plan(d)
 def test_zero_native_wrapper_refuses_steady(self):
  with patch.object(auditor,'native_process') as native:
   with self.assertRaises(EvidenceError):auditor.call_native('INERT_SOFTWARE_PLACEHOLDER',self.data['prepared_runs'][0],{})
   native.assert_not_called()
 def test_preparation_not_zero_authority(self):
  with self.assertRaises(EvidenceError):validate_zero_authority(self.data)
 def test_preparation_not_formal_authority(self):
  with self.assertRaises(EvidenceError):validate_formal_authority(self.data)
 def test_flag_alone_is_not_real_formal_authority(self):
  d=copy.deepcopy(self.data);d.update(kind='AUTHORIZED_EXECUTION_LAUNCH_RELEASE',simulation_authorized=True,formal_simulation_authorized=True,approved_runs=d['prepared_runs'],approved_run_ids=d['prepared_run_ids'])
  with self.assertRaises(EvidenceError):validate_formal_authority(d)
 def test_formal_cannot_skip_zero_and_B(self):
  d=copy.deepcopy(self.data);d.update(kind='AUTHORIZED_EXECUTION_LAUNCH_RELEASE',simulation_authorized=True,formal_simulation_authorized=True,approved_runs=d['prepared_runs'],approved_run_ids=d['prepared_run_ids'])
  with patch('stage_s3.explicit_authority',return_value=dict(stage='S3_REG_LINEARITY',formal_simulation_authorized=True,approved_run_ids=list(RUN_IDS))),patch('stage_s3.verify_zero_receipt') as zero:
   with self.assertRaises(EvidenceError):validate_formal_authority(d)
   zero.assert_not_called()
 def test_zero_release_cannot_be_formal(self):
  d=copy.deepcopy(self.data);d.update(kind='AUTHORIZED_ZERO_STEP_AUDIT_RELEASE',native_zero_step_authorized=True)
  with self.assertRaises(EvidenceError):validate_formal_authority(d)
 def test_real_closed_execution_refused_before_process_and_writes(self):
  with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S3_CLOSED_') as t:
   p=Path(t)/'INERT_CLOSED_METADATA.json';p.write_text(json.dumps(self.data))
   with patch.object(runner,'native_process') as process,patch.object(auditor,'call_native') as native:
    with self.assertRaises(EvidenceError):runner.execute(p,sha(p),self.data)
    with self.assertRaises(EvidenceError):auditor.execute(p,sha(p),self.data)
    process.assert_not_called();native.assert_not_called()
   self.assertFalse((CASE/'launch_attempts').exists());self.assertFalse((CASE/'audit_attempts').exists())
 def test_default_entry_is_readonly(self):
  with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S3_ENTRY_') as t:
   p=Path(t)/'INERT_CLOSED.json';p.write_text(json.dumps(self.data))
   with patch('subprocess.Popen',side_effect=AssertionError('NO PROCESS')),patch.object(sys,'argv',['run_S3.py','--release',str(p),'--release-sha256',sha(p)]),contextlib.redirect_stdout(io.StringIO()):self.assertEqual(runner.main(),0)
 def test_wrong_external_SHA(self):
  with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S3_SHA_') as t:
   p=Path(t)/'INERT_CLOSED.json';p.write_text(json.dumps(self.data))
   with self.assertRaises(EvidenceError):verify_seal(p,'0'*64)
 def test_used_output(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'run_config.txt').write_text('');(p/'run_manifest.txt').write_text('');(p/'run.log').write_text('SYNTHETIC')
   with self.assertRaises(EvidenceError):require_pristine([dict(output_directory=str(p))])
 def test_four_hour_caps(self):self.assertEqual([runner.wall_cap(r['run_config_path']) for r in self.data['prepared_runs']],[14400]*4)
 def test_exact_force_and_steps(self):
  from evidence import exact_parameters
  self.assertEqual([exact_parameters(kv(r['run_config_path']))['a'] for r in self.data['prepared_runs']],[50000,50000,200000,200000])
  for r in self.data['prepared_runs']:
   p=exact_parameters(kv(r['run_config_path']));self.assertEqual((p['nodes'],p['window'],p['cap']),(368640,2592,150528))
 def test_local_analysis_refuses_closed_preparation(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'SYNTHETIC_CLOSED.json';p.write_text(json.dumps(self.data));target=Path(t)/'out'
   with self.assertRaises(EvidenceError):check_linearity.analyze(p,sha(p),target)
   self.assertFalse(target.exists())
 def test_linear_metric_equal(self):self.assertTrue(linear_metric([2,2,2])['CONTROL_PASS'])
 def test_linear_metric_boundary(self):
  v=[.9995,1.,1.0005];self.assertTrue(linear_metric(v)['CONTROL_PASS']);self.assertAlmostEqual(linear_metric(v)['K_span_over_mean'],.001)
 def test_linear_metric_over_limit(self):self.assertFalse(linear_metric([.99949,1.,1.00051])['CONTROL_PASS'])
 def test_linear_metric_requires_three_finite_positive(self):
  for v in [[1,1],[0,1,1],[1,float('nan'),1],[1,1,-1]]:
   with self.subTest(v=v),self.assertRaises(EvidenceError):linear_metric(v)
 def test_missing_new_point_rejected(self):
  with patch('s3_baselines.verify_baselines',return_value={'P':1,'T':1}):
   with self.assertRaises(EvidenceError):control_for_direction(self.data,'P',{},'synthetic')
 def new_point_fixture(self,root):
  d=copy.deepcopy(self.data);accepted={};expected='a'*64
  for i,record in enumerate(d['prepared_runs']):
   run=Path(root)/record['run_id'];run.mkdir();cfg=kv(record['run_config_path']);cfg.update(output_directory=str(run))
   path=run/'run_config.txt';path.write_text(''.join(k+'='+v+'\n' for k,v in cfg.items()));record.update(output_directory=str(run),run_config_path=str(path),run_config_sha256=sha(path))
   K=1.;force=float(cfg['acceleration_m_s2']);(run/'result.txt').write_text('J_main_m2_s='+str(K*force/float(cfg['nu_m2_s']))+'\n')
   comp=dict(run_id=record['run_id'],planned_case_id=record['planned_case_id'],release_sha256=expected,inputs_before_sha256=d['inputs_sha256'],inputs_after_sha256=d['inputs_sha256'],inputs_unchanged=True,independent_process_exit_code=0,timed_out=False,resource_stop_reason=None,output_sha256={p.name:sha(p) for p in run.iterdir()})
   (run/'completion.json').write_text(json.dumps(comp))
   accepted[record['run_id']]=dict(run_id=record['run_id'],planned_case_id=record['planned_case_id'],direction=cfg['direction'],stage='S3_REG_LINEARITY',dx_nm=2.5,acceleration_m_s2=force,RESULT_PASS=True,NUMERICAL_GATE='PASS',geometry_PASS=True,independent_exit_code=0,completion_sha256=sha(run/'completion.json'),release_sha256=expected,scalar=dict(K_m3=K))
  return d,accepted,expected
 def test_cross_release_join_software_fixture(self):
  with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S3_JOIN_') as t:
   d,a,h=self.new_point_fixture(t)
   with patch('s3_baselines.verify_baselines',return_value={'P':1.,'T':1.}):
    r=control_for_direction(d,'P',a,h);self.assertTrue(r['CONTROL_PASS']);self.assertEqual(r['K_m3'],[1.,1.,1.]);self.assertFalse(r['REFERENCE_QUALIFIED_FOR_CASE'])
 def test_join_wrong_new_release_rejected(self):
  with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S3_JOIN_') as t:
   d,a,h=self.new_point_fixture(t)
   with patch('s3_baselines.verify_baselines',return_value={'P':1.,'T':1.}),self.assertRaises(EvidenceError):control_for_direction(d,'P',a,'b'*64)
 def test_join_wrong_new_force_rejected(self):
  with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S3_JOIN_') as t:
   d,a,h=self.new_point_fixture(t);a[d['prepared_runs'][0]['run_id']]['acceleration_m_s2']=100000
   with patch('s3_baselines.verify_baselines',return_value={'P':1.,'T':1.}),self.assertRaises(EvidenceError):control_for_direction(d,'P',a,h)
 def test_join_false_acceptance_rejected(self):
  with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S3_JOIN_') as t:
   d,a,h=self.new_point_fixture(t);a[d['prepared_runs'][0]['run_id']]['RESULT_PASS']=False
   with patch('s3_baselines.verify_baselines',return_value={'P':1.,'T':1.}),self.assertRaises(EvidenceError):control_for_direction(d,'P',a,h)
 def test_join_K_forgery_rejected(self):
  with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S3_JOIN_') as t:
   d,a,h=self.new_point_fixture(t);a[d['prepared_runs'][0]['run_id']]['scalar']['K_m3']=1.5
   with patch('s3_baselines.verify_baselines',return_value={'P':1.,'T':1.}),self.assertRaises(EvidenceError):control_for_direction(d,'P',a,h)
 def test_join_raw_extra_file_rejected(self):
  with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S3_JOIN_') as t:
   d,a,h=self.new_point_fixture(t);(Path(d['prepared_runs'][0]['output_directory'])/'UNBOUND').write_text('synthetic')
   with patch('s3_baselines.verify_baselines',return_value={'P':1.,'T':1.}),self.assertRaises(EvidenceError):control_for_direction(d,'P',a,h)
 def pipeline(self,native_code=0,checker_code=0,accepted=True,drift=False,control_pass=True):
  with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S3_PIPELINE_') as t:
   folder=Path(t);records=[]
   for i,(force,d) in enumerate([(50000,'P'),(50000,'T'),(200000,'P'),(200000,'T')]):
    rid=f'SYNTHETIC_S3_{i}';run=folder/'runs'/rid/'steady';run.mkdir(parents=True)
    (run/'run_config.txt').write_text(f'mode=steady\nrun_id={rid}\noutput_directory={run}\ndx_nm=2.5\ndirection={d}\nacceleration_m_s2={force}\n')
    (run/'run_manifest.txt').write_text(f'run_id={rid}\nmode=steady\n')
    records.append(dict(run_id=rid,planned_case_id='SYNTHETIC_CASE_'+str(i),output_directory=str(run),run_config_path=str(run/'run_config.txt')))
   sentinel=folder/'SYNTHETIC_INPUT';sentinel.write_text('unchanged');doc=dict(prepared_runs=records,inputs_sha256={str(sentinel):sha(sentinel)},provenance=dict(native_binary='INERT_SOFTWARE_NOT_EXECUTABLE'))
   def native(*args):
    if drift:sentinel.write_text('drift')
    return dict(independent_process_exit_code=native_code,timed_out=False,resource_stop_reason=None,elapsed_seconds=0.)
   def checked(argv,**kwargs):
    path=Path(argv[argv.index('--out')+1]);path.mkdir(parents=True);i=[r['run_id'] for r in records].index(path.name)
    (path/'acceptance.json').write_text(json.dumps(dict(run_id=path.name,direction='P' if i%2==0 else 'T',RESULT_PASS=accepted,NUMERICAL_GATE='PASS',geometry_PASS=True,fixture_label='SYNTHETIC_ONLY')))
    return types.SimpleNamespace(returncode=checker_code)
   with patch.object(runner,'CASE',folder),patch.object(runner,'binding',return_value=doc),patch.object(runner,'validate_formal_authority'),patch.object(runner,'resources',return_value={}),patch.object(runner,'native_process',side_effect=native) as process,patch.object(runner.subprocess,'run',side_effect=checked),patch('s3_baselines.control_for_direction',return_value=dict(CONTROL_PASS=control_pass)) as control:
    failure=native_code!=0 or checker_code!=0 or not accepted or drift or not control_pass
    if failure:
     with self.assertRaises(EvidenceError):runner.execute(Path('INERT'), 'synthetic', doc)
     self.assertEqual(process.call_count,3 if not control_pass and not(native_code or checker_code or not accepted or drift) else 1)
    else:
     runner.execute(Path('INERT'),'synthetic',doc);self.assertEqual(process.call_count,4);self.assertEqual(control.call_count,2)
    self.assertEqual((folder/'launch_attempts/synthetic/S3_completed.json').exists(),not failure)
 def test_native_failure_stops(self):self.pipeline(native_code=3)
 def test_checker_failure_stops(self):self.pipeline(checker_code=2)
 def test_acceptance_false_stops(self):self.pipeline(accepted=False)
 def test_input_drift_stops(self):self.pipeline(drift=True)
 def test_P_control_failure_stops_before_T_high(self):self.pipeline(control_pass=False)
 def test_four_success_no_next_stage(self):self.pipeline()

if __name__=='__main__':unittest.main(verbosity=2)
