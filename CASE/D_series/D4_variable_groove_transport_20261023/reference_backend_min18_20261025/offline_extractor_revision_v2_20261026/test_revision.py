"""v2 regression tests: marked records only, no PDE solve or real field reads."""
from copy import deepcopy
import json
from math import pi,sqrt
from pathlib import Path
import tempfile
import unittest
import numpy as np
from binding import read_synthetic_record,canonical,digest,REAL_ROOT,SYNTHETIC
from analysis_record import run_synthetic_analysis,checks,compare,SOFTWARE_LIMIT,DECISION_BAND
from numerics import Field,Rejected
from extractor import extract_arrays,extract_real_record
from test_fixtures import make_fixture
from synthetic_fixture import make_case,seal,write_json


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='sim240_v2_synthetic_');self.base=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def case(self):return make_case(self.base)

    def test_nonzero_L2_closed_form_with_pressure_offset_and_permutation(self):
        B=.01*(2/105+pi*pi/630)
        for offset,shuffle in [(0,False),(17,True)]:
            s,a=make_fixture(lambda x,z:(z*(1-z),0.),lambda x,z:x-1,shuffle=shuffle,offset=offset)
            m=Field(s,a).integrate('mms_mixed',12)
            expected=dict(u_error2=B,u_exact2=1/15+B,p_error2=2/3+.005,p_exact2=.005,
                          u_L2_relative=sqrt(B/(1/15+B)),p_L2_relative=sqrt((2/3+.005)/.005))
            for k,v in expected.items():np.testing.assert_allclose(m[k],v,atol=2e-11,rtol=2e-11)

    def test_real_schema_reader_success_and_N8_dimensions(self):
        c=self.case();s,a=read_synthetic_record(c['binding'],c['trust'])
        self.assertEqual(s['mesh_coordinates_hat'].shape,(153,2))
        self.assertEqual(a['cell_velocity_mixed_dofs'].shape,(256,12))
        self.assertEqual(len(s['reconstructed_solution']),1275)
        self.assertEqual(len(s['periodic_slave_dofs']),39)
        self.assertEqual(len(c['binding']['inventory']),48)
        self.assertEqual(len(s),17);self.assertEqual(len(a),8)

    def test_replacement_inventory_cannot_replace_pinned_binding(self):
        c=self.case();b=deepcopy(c['binding']);b['inventory']['contract.json']='0'*64
        b['inventory_sha256']=digest(b['inventory'])
        with self.assertRaisesRegex(Rejected,'BINDING_ANCHOR'):read_synthetic_record(b,c['trust'])

    def test_certificate_and_accepted_input_index_tamper(self):
        c=self.case();cert=Path(c['binding']['acceptance_path']);old=cert.read_bytes();cert.write_bytes(old+b' ')
        with self.assertRaisesRegex(Rejected,'CERTIFICATE_CHANGED'):read_synthetic_record(c['binding'],c['trust'])
        cert.write_bytes(old);idx=Path(c['binding']['acceptance_inputs_path']);idx.write_bytes(idx.read_bytes()+b' ')
        with self.assertRaisesRegex(Rejected,'INPUT_LIST_CHANGED'):read_synthetic_record(c['binding'],c['trust'])

    def test_inventory_must_already_be_in_accepted_input_list(self):
        c=self.case();b=c['binding'];index=Path(b['acceptance_inputs_path']);d=json.loads(index.read_text());d.pop(next(iter(d)));write_json(index,d)
        b['acceptance_inputs_sha256']=__import__('hashlib').sha256(index.read_bytes()).hexdigest()
        c['trust']['acceptance_inputs_sha256']=b['acceptance_inputs_sha256'];c['trust']['binding_sha256']=digest(b)
        with self.assertRaisesRegex(Rejected,'NOT_IN_ACCEPTED'):read_synthetic_record(b,c['trust'])

    def test_wrong_run_case_parent_and_completion_rejected(self):
        c=self.case()
        for filename,key,value,reason in [
          ('capture_manifest.json','run_id','OTHER','RUN_BINDING'),
          ('contract.json','planned_id','B0MIN_MMS_mixed_N16','CASE_BINDING'),
          ('capture_manifest.json','independent_exit_code',7,'INCOMPLETE_PARENT'),
          ('capture_manifest.json','archive_status','INCOMPLETE','INCOMPLETE_PARENT'),
          ('archive/worker_completion.json','status','FAILED','COMPLETION_STATUS'),
          ('archive/worker_completion.json','contract_sha256','0'*64,'CONTRACT_BINDING')]:
            with self.subTest(key=key):
                p=c['root']/filename;old=p.read_bytes();d=json.loads(old);d[key]=value;write_json(p,d);seal(c)
                with self.assertRaisesRegex(Rejected,reason):read_synthetic_record(c['binding'],c['trust'])
                p.write_bytes(old);seal(c)

    def test_manifest_shape_and_dtype_rejected_after_trusted_transport(self):
        c=self.case();p=c['root']/'archive/solution/manifest.json';old=p.read_bytes()
        for key,value in [('shape',[999,2]),('dtype','<f4')]:
            with self.subTest(key=key):
                d=json.loads(old);d['files']['mesh_coordinates_hat.npy'][key]=value;write_json(p,d);seal(c)
                with self.assertRaisesRegex(Rejected,'ARRAY_SCHEMA'):read_synthetic_record(c['binding'],c['trust'])
                p.write_bytes(old);seal(c)

    def test_missing_or_modified_record_bytes_rejected(self):
        c=self.case();p=c['root']/'synthetic_aux_00.json';old=p.read_bytes();p.unlink()
        with self.assertRaisesRegex(Rejected,'INVENTORY_CHANGED'):read_synthetic_record(c['binding'],c['trust'])
        p.write_bytes(old+b' ')
        with self.assertRaisesRegex(Rejected,'BYTES_CHANGED'):read_synthetic_record(c['binding'],c['trust'])

    def test_change_during_read_rejected(self):
        c=self.case()
        def hook(root):
            p=root/'synthetic_aux_00.json';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(Rejected,'BYTES_CHANGED'):read_synthetic_record(c['binding'],c['trust'],after_load_test_hook=hook)

    def test_wrong_synthetic_kind_and_real_root_rejected_before_arrays(self):
        c=self.case();b=deepcopy(c['binding']);b['kind']='REAL_N8_ANALYSIS_DRAFT'
        with self.assertRaisesRegex(Rejected,'SYNTHETIC_BINDING'):read_synthetic_record(b,c['trust'])
        b=deepcopy(c['binding']);b['record_root']=str(REAL_ROOT)
        with self.assertRaisesRegex(Rejected,'REAL_ROOT_FORBIDDEN'):read_synthetic_record(b,c['trust'])
        with self.assertRaisesRegex(Rejected,'CLOSED'):extract_real_record(REAL_ROOT)

    def test_complete_synthetic_analysis_artifacts_and_no_overwrite(self):
        c=self.case();code,out=run_synthetic_analysis(c['binding'],c['trust'])
        self.assertEqual(code,0)
        required={'input_binding.json','events.jsonl','metrics.json','checks.json','status.json','analysis.exit_code','output_manifest.json'}
        self.assertEqual({p.name for p in out.iterdir()},required)
        self.assertEqual((out/'analysis.exit_code').read_text(),'0\n')
        status=json.loads((out/'status.json').read_text());self.assertEqual(status['status'],'SYNTHETIC_METRICS_RECORDED')
        self.assertFalse(status['RESULT_PASS']);self.assertFalse(status['actual_N8_processed'])
        with self.assertRaisesRegex(Rejected,'UNIQUE_EXISTING_PARENT'):run_synthetic_analysis(c['binding'],c['trust'])

    def test_failed_analysis_retains_error_log_and_nonzero_exit(self):
        c=self.case();p=c['root']/'synthetic_aux_00.json';p.write_bytes(p.read_bytes()+b' ')
        code,out=run_synthetic_analysis(c['binding'],c['trust'])
        self.assertEqual(code,2);self.assertTrue((out/'failure.json').is_file())
        self.assertFalse((out/'metrics.json').exists())
        self.assertIn('FAILED',(out/'events.jsonl').read_text())
        status=json.loads((out/'status.json').read_text());self.assertEqual(status['status'],'SYNTHETIC_ANALYSIS_FAILED')

    def test_nonfinite_missing_and_near_threshold_statuses(self):
        self.assertEqual(compare(SOFTWARE_LIMIT,SOFTWARE_LIMIT),'NEAR_THRESHOLD')
        self.assertEqual(compare(SOFTWARE_LIMIT-2*DECISION_BAND,SOFTWARE_LIMIT),'PASS')
        self.assertEqual(compare(SOFTWARE_LIMIT+2*DECISION_BAND,SOFTWARE_LIMIT),'FAIL')
        self.assertEqual(compare(None,SOFTWARE_LIMIT),'MISSING')
        self.assertEqual(compare(float('nan'),SOFTWARE_LIMIT),'INVALID')
        c=self.case();s,a=read_synthetic_record(c['binding'],c['trust']);m=extract_arrays(s,a)
        m['high_rule']['D']=float('nan')
        with self.assertRaises(ValueError):checks(m)


if __name__=='__main__':unittest.main(verbosity=2)
