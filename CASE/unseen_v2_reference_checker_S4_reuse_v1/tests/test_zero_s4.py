"""R1/R2 regression tests. Synthetic file fixtures; no process or real VTK calls."""
from pathlib import Path
import json,sys,tempfile,unittest
from unittest.mock import patch
from fixtures_zero_s4 import ZeroFixture
from evidence import EvidenceError,kv
from zero_evidence_s4 import validate_zero_outputs,validate_initial_readback
import stage_s4 as stage

class ZeroRevisionTests(unittest.TestCase):
 def check(self,f):
  f.refresh()
  # Isolate raw-content verification from real authority. No real author/run record is made.
  with patch.object(stage,'CASE',f.root),patch.object(stage,'verify_seal',return_value=f.released),patch.object(stage,'validate_zero_authority'):
   return stage.verify_zero_receipt(f.bound)
 def fixture(self):
  t=tempfile.TemporaryDirectory(prefix='SYNTHETIC_S4_R1_R2_');self.addCleanup(t.cleanup);return ZeroFixture(t.name)
 def reject(self,f):
  with self.assertRaises((EvidenceError,KeyError,ValueError)):self.check(f)
 def test_complete_eighteen_records_and_six_readbacks(self):
  f=self.fixture();self.check(f)
  for r in f.plan:validate_zero_outputs(r)
  self.assertEqual(len(f.fields),6)
 def test_R1_all_effective_fields_across_three_modes(self):
  mutations=dict(acceleration_m_s2='200000',direction='perpendicular',dx_m='9e-9',nu_m2_s='2e-6',formal_simulation='true',h_m='7e-8',d_m='9e-8',w_m='1e-7',Lx_m='3e-7',Ly_m='3e-7',phi='.4',dt_s='2e-12',nominal_volume_m3='1e-21',plan_area_m2='1e-14',nx=95,ny=95,window_steps=2591,maximum_steps=150527)
  for mode in stage.MODES:
   for key,value in mutations.items():
    with self.subTest(mode=mode,key=key):
     f=self.fixture();r=next(r for r in f.plan if r['mode']==mode);f.change_kv(Path(r['output_directory'])/'effective_config.txt',key,value)
     with self.assertRaises((EvidenceError,ValueError)):validate_zero_outputs(r)
 def test_R1_zero_effective_unknown_direction(self):
  f=self.fixture();r=f.plan[0];f.change_kv(Path(r['output_directory'])/'effective_config.txt','direction','P');self.reject(f)
 def test_R2_duplicate_readback_original_counterexample(self):
  f=self.fixture()
  for r in f.records:
   if r['mode']=='initialize':r['field_readback']=str(f.fields[0])
  self.reject(f)
 def test_R2_zero_flux_original_counterexample(self):
  f=self.fixture();f.change_json(f.fields[0],lambda d:d['frames'][0].update(J_m2_s=[0,0,0],roundoff_bound_m2_s=[1,1,1]));self.reject(f)
 def test_R2_swapped_P_T_readbacks(self):
  f=self.fixture();a=[r for r in f.records if r['mode']=='initialize'];a[0]['field_readback'],a[1]['field_readback']=a[1]['field_readback'],a[0]['field_readback'];self.reject(f)
 def test_R2_wrong_record_run_id(self):
  f=self.fixture();f.records[0]['run_id']='WRONG';self.reject(f)
 def test_R2_wrong_record_output(self):
  f=self.fixture();f.records[0]['output']=str(f.root);self.reject(f)
 def test_R2_wrong_original_A(self):
  f=self.fixture();f.audit['preparation_A_sha256']='b'*64;self.reject(f)
 def test_R2_native_nonzero_exit(self):
  f=self.fixture();p=Path(f.plan[0]['output_directory'])/'process_receipt.json';f.change_json(p,lambda d:d.update(independent_process_exit_code=3));self.reject(f)
 def test_R2_native_timeout(self):
  f=self.fixture();p=Path(f.plan[0]['output_directory'])/'process_receipt.json';f.change_json(p,lambda d:d.update(timed_out=True));self.reject(f)
 def test_R2_native_resource_stop(self):
  f=self.fixture();p=Path(f.plan[0]['output_directory'])/'process_receipt.json';f.change_json(p,lambda d:d.update(resource_stop_reason='synthetic'));self.reject(f)
 def test_R2_nonzero_advancement(self):
  f=self.fixture();p=Path(f.plan[0]['output_directory'])/'execution_audit.txt';f.change_kv(p,'collide_and_stream_calls',1);self.reject(f)
 def test_R2_reader_nonzero_exit(self):
  f=self.fixture();f.change_json(f.fields[0].with_suffix('.process.json'),lambda d:d.update(independent_exit_code=2));self.reject(f)
 def test_R2_reader_timeout(self):
  f=self.fixture();f.change_json(f.fields[0].with_suffix('.process.json'),lambda d:d.update(timed_out=True));self.reject(f)
 def test_R2_missing_reader_process(self):
  f=self.fixture();f.fields[0].with_suffix('.process.json').unlink();self.reject(f)
 def test_R2_wrong_frame_step(self):
  f=self.fixture();f.change_json(f.fields[0],lambda d:d['frames'][0].update(step=1));self.reject(f)
 def test_R2_wrong_nodes(self):
  f=self.fixture();f.change_json(f.fields[0],lambda d:d['frames'][0].update(unique_fluid_nodes=1));self.reject(f)
 def test_R2_wrong_units(self):
  f=self.fixture();f.change_json(f.fields[0],lambda d:d.update(velocity_units='lattice'));self.reject(f)
 def test_R2_wrong_diagnostic_J(self):
  f=self.fixture();f.change_json(f.fields[0],lambda d:d['frames'][0].update(diagnostic_J_m2_s=[0,0,0]));self.reject(f)
 def test_R2_negative_roundoff(self):
  f=self.fixture();f.change_json(f.fields[0],lambda d:d['frames'][0].update(roundoff_bound_m2_s=[-1,0,0]));self.reject(f)
 def test_R2_nonfinite_flux(self):
  f=self.fixture();f.change_json(f.fields[0],lambda d:d['frames'][0].update(J_m2_s=[float('nan'),0,0]));self.reject(f)
 def test_R2_payload_cross_configuration(self):
  f=self.fixture();other=json.loads(f.fields[1].read_text())['payload_sha256'];f.change_json(f.fields[0],lambda d:d.update(payload_sha256=other));self.reject(f)
 def test_R2_unbound_payload(self):
  f=self.fixture();f.change_json(f.fields[0],lambda d:d.update(payload_sha256={}));self.reject(f)
 def test_R2_payload_tampered(self):
  f=self.fixture();r=next(r for r in f.plan if r['mode']=='initialize');(Path(r['output_directory'])/'vtkData/data/test.vti').write_text('changed synthetic payload');self.reject(f)
 def test_R2_VTK_future_frame(self):
  f=self.fixture();r=next(r for r in f.plan if r['mode']=='initialize');p=Path(r['output_directory'])/'vtkData/test.pvd';p.write_text(p.read_text().replace('timestep="0"','timestep="1"'));self.reject(f)
 def test_R2_initial_result_wrong_identity(self):
  f=self.fixture();r=next(r for r in f.plan if r['mode']=='initialize');f.change_kv(Path(r['output_directory'])/'result.txt','run_id','WRONG');self.reject(f)
 def test_R2_initial_result_wrong_half_force(self):
  f=self.fixture();r=next(r for r in f.plan if r['mode']=='initialize');f.change_kv(Path(r['output_directory'])/'result.txt','J_vector_m2_s','0,0,0');self.reject(f)
 def test_R2_native_frame_table_wrong_step(self):
  f=self.fixture();r=next(r for r in f.plan if r['mode']=='initialize');(Path(r['output_directory'])/'frame_index.csv').write_text('step,time_s,tstar,reason\n1,0,0,initial\n');self.reject(f)
 def test_R2_missing_native_record(self):
  f=self.fixture();f.records.pop();self.reject(f)
 def test_R2_extra_raw_file_stale_manifest(self):
  f=self.fixture();self.check(f);(f.folder/'EXTRA').write_text('SYNTHETIC')
  with patch.object(stage,'CASE',f.root),patch.object(stage,'verify_seal',return_value=f.released),patch.object(stage,'validate_zero_authority'),self.assertRaises(EvidenceError):stage.verify_zero_receipt(f.bound)
if __name__=='__main__':unittest.main(verbosity=2)
