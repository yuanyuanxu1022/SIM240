"""Synthetic software tests only. No solver or native zero-step execution."""
from pathlib import Path
import copy,ctypes,json,math,shutil,struct,sys,tempfile,unittest
from fractions import Fraction
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
from evidence import EvidenceError,sha
from mass_capture import (arithmetic_self_check,bits,replay_values,validate_index,finalize_capture,check_map)
from contracts import verify_provenance
from revision import verify_revision
from fixtures_contract import ContractFixture,CASE

NATIVE=CASE.parent/'unseen_v2_reference_S0_mrp_v1_a1'
LIB=ctypes.CDLL(str(NATIVE/'build/mrp_software_fixture.so'))
LIB.mrp_legacy_step.argtypes=[ctypes.c_double]*4;LIB.mrp_legacy_step.restype=ctypes.c_double
LIB.mrp_capture_fixture.argtypes=[ctypes.c_char_p,ctypes.c_int];LIB.mrp_capture_fixture.restype=ctypes.c_int

class MRPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.fixture_run=Path(cls.temp.name)/'SYNTHETIC_NO_FLOW';cls.fixture_run.mkdir()
        (cls.fixture_run/'run_config.txt').write_text('run_id=SYNTHETIC_MRP_NO_FLOW\ndirection=P\n')
        assert LIB.mrp_capture_fixture(str(cls.fixture_run).encode(),0)==0
        cls.index=finalize_capture(cls.fixture_run,Path(sys.executable).resolve())
        cls.root=cls.fixture_run/'mass_capture';cls.binary=sha(Path(sys.executable).resolve())
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def assert_bad(self,index,pattern=''):
        with self.assertRaises(EvidenceError):
            validate_index(index,self.root,'SYNTHETIC_MRP_NO_FLOW','P',self.binary)

    def test_constructed_exact_rational_oracle(self):
        self.assertTrue(arithmetic_self_check()['constructed_not_historical'])
        p=((1.*1000.)*5e-9)*5e-9;m=3.5e-21
        self.assertEqual(bits(LIB.mrp_legacy_step(1.,1000.,5e-9,m)),bits(float(Fraction(p)*Fraction(5e-9)+Fraction(m))))

    def test_native_helper_matches_independent_loop(self):
        values=[1.,math.nextafter(1.,math.inf),1.-2e-9]*73
        total=0.
        for rho in values:total=LIB.mrp_legacy_step(rho,1000.,5e-9,total)
        self.assertEqual(bits(total),bits(replay_values(values,1000.,5e-9)['fused_mass']))

    def test_captured_initial_and_step0_separate_files(self):
        keys={(r['phase'],r['step']) for r in self.index['records']}
        self.assertEqual(len(keys),11);self.assertIn(('initial_reference',0),keys);self.assertIn(('diagnostic',0),keys)

    def test_capture_has_all_core_coordinates(self):check_map(self.root/'core_index_map.csv')

    def test_raw_record_actual_native_arithmetic(self):
        r=self.index['records'][0]
        actual=replay_values([1.]*57600,1000.,5e-9)
        self.assertEqual(bits(actual['fused_mass']),r['native_mass_hex64'])
        self.assertEqual(bits(actual['corrected_mass']),r['native_corrected_mass_hex64'])
        self.assertEqual(bits(actual['density_delta']),r['native_density_delta_hex64'])

    def test_finalizer_refuses_overwrite(self):
        with self.assertRaises(EvidenceError):finalize_capture(self.fixture_run,Path(sys.executable).resolve())

    def test_missing_initial_rejected(self):
        x=copy.deepcopy(self.index);x['records']=[r for r in x['records'] if r['phase']!='initial_reference'];self.assert_bad(x)

    def test_missing_planned_step_rejected(self):
        x=copy.deepcopy(self.index);x['records'].pop();self.assert_bad(x)

    def test_duplicate_phase_rejected(self):
        x=copy.deepcopy(self.index);x['records'].append(x['records'][0]);self.assert_bad(x)

    def test_wrong_phase_rejected(self):
        x=copy.deepcopy(self.index);x['records'][0]['phase']='diagnostic';self.assert_bad(x)

    def test_wrong_payload_hash_rejected(self):
        x=copy.deepcopy(self.index);x['records'][0]['sha256']='0'*64;self.assert_bad(x)

    def test_wrong_map_hash_rejected(self):
        x=copy.deepcopy(self.index);x['map_sha256']='0'*64;self.assert_bad(x)

    def test_wrong_binary_hash_rejected(self):
        x=copy.deepcopy(self.index);x['native_binary_sha256']='0'*64;self.assert_bad(x)

    def test_wrong_dtype_rejected(self):
        x=copy.deepcopy(self.index);x['records'][0]['dtype']='>f8';self.assert_bad(x)

    def test_wrong_time_rejected(self):
        x=copy.deepcopy(self.index);x['records'][0]['time_s']=1.;self.assert_bad(x)

    def test_wrong_fp_environment_rejected(self):
        x=copy.deepcopy(self.index);x['records'][0]['fe_round']=1024;self.assert_bad(x)

    def test_wrong_order_native_capture_rejected(self):
        with tempfile.TemporaryDirectory() as d:self.assertEqual(LIB.mrp_capture_fixture(d.encode(),1),2)

    def test_wrong_map_order_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'map.csv';lines=(self.root/'core_index_map.csv').read_text().splitlines(True)
            lines[1],lines[2]=lines[2],lines[1];p.write_text(''.join(lines))
            with self.assertRaises(EvidenceError):check_map(p)

    def test_truncated_capture_rejected(self):
        x=copy.deepcopy(self.index)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);shutil.copyfile(self.root/'core_index_map.csv',root/'core_index_map.csv')
            first=x['records'][0]['file'];(root/first).write_bytes(b'bad')
            with self.assertRaises(EvidenceError):validate_index(x,root,'SYNTHETIC_MRP_NO_FLOW','P',self.binary)

    def test_nonfinite_density_rejected(self):
        for rho in [math.nan,math.inf,-1.,0.]:
            with self.subTest(rho=rho),self.assertRaises(EvidenceError):replay_values([rho],1000.,5e-9)

    def test_legacy_anchor_still_accepted(self):
        with tempfile.TemporaryDirectory() as d:verify_provenance(ContractFixture(d).document)

    def revision_bound(self):
        path=CASE/'revision/revision_anchor.json';a=json.loads(path.read_text());native={str(p):sha(p) for p in (NATIVE/'src').glob('*') if p.suffix in ('.cpp','.h')}
        inputs={str(path):sha(path),**native}
        for r in a['frozen_inputs']:inputs[r['path']]=r['sha256']
        for r in a['diffs'].values():
            inputs[r['path']]=r['sha256']
            if r['baseline_path']:inputs[r['baseline_path']]=r['baseline_sha256']
        return {'stage':'S0_REGRESSION','inputs_sha256':inputs,'provenance':{'native_sources':list(native)},
                'source_revision':{'id':'URV-MRP-v1','anchor':str(path),'sha256':sha(path)}},a['native_source_sha256']

    def test_exact_revision_source_binding(self):
        b,o=self.revision_bound();verify_revision(b,o,CASE)

    def test_unreviewed_source_rejected(self):
        b,o=self.revision_bound();o=dict(o,**{'urv_reference.cpp':'0'*64})
        with self.assertRaises(EvidenceError):verify_revision(b,o,CASE)

    def test_unbound_revision_rejected(self):
        b,o=self.revision_bound();b.pop('source_revision')
        with self.assertRaises(EvidenceError):verify_revision(b,o,CASE)

    def test_instruction_audit_failure_blocks_real_revision_provenance(self):
        b,o=self.revision_bound()
        environment=json.loads((NATIVE/'evidence/build_environment.json').read_text())
        build=[NATIVE/'src/Makefile',NATIVE/'build/urv_reference',NATIVE/'build/urv_reference.d',
               NATIVE/'evidence/build_environment.json',NATIVE/'evidence/ldd.txt']
        for p in build:b['inputs_sha256'][str(p)]=sha(p)
        for key in ['dependency_sha256','link_library_sha256','dynamic_library_sha256']:
            b['inputs_sha256'].update(environment[key])
        b['inputs_sha256'][environment['compiler_executable']]=environment['compiler_sha256']
        b['schema_version']='URV-EXEC-1.1'
        b['provenance'].update(native_binary=str(NATIVE/'build/urv_reference'),
            build_recipe=str(NATIVE/'src/Makefile'),build_environment=str(NATIVE/'evidence/build_environment.json'),
            dependency_file=str(NATIVE/'build/urv_reference.d'),ldd_record=str(NATIVE/'evidence/ldd.txt'))
        original_read=Path.read_text
        anchor_path=CASE/'revision/revision_anchor.json'
        def force_failed_anchor(path,*args,**kwargs):
            text=original_read(path,*args,**kwargs)
            if path==anchor_path:
                document=json.loads(text);document['instruction_audit_status']='FAIL'
                return json.dumps(document)
            return text
        # Synthetic tamper simulation; the actual accepted anchor is never edited.
        with patch.object(Path,'read_text',force_failed_anchor):
            with self.assertRaisesRegex(EvidenceError,'instruction audit not passed'):
                verify_provenance(b)

    def test_source_diff_tamper_rejected(self):
        b,o=self.revision_bound();p=next(iter(json.loads((CASE/'revision/revision_anchor.json').read_text())['diffs'].values()))['path']
        original=Path.read_text
        def altered(path,*args,**kwargs):
            return original(path,*args,**kwargs)+('tamper\n' if str(path)==p else '')
        with patch.object(Path,'read_text',altered),self.assertRaises(EvidenceError):verify_revision(b,o,CASE)

if __name__=='__main__':unittest.main()
