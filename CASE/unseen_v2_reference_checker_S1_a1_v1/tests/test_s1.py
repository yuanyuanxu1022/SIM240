"""S1 arithmetic/source/stage/runner tests. Hypothetical execution is mocked."""
from pathlib import Path
import copy
import csv
import ctypes
from fractions import Fraction
import importlib.util
import json
import math
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import numpy as np

CHECKER=Path(__file__).resolve().parents[1]
CASE=CHECKER.parent/'unseen_v2_reference_S1_a1_v1'
ROOT=CASE.parents[1]
REPORT=ROOT/'docs/reports/URV_S1_implementation_20261102'
sys.path.insert(0,str(CHECKER/'analysis'))
sys.path.insert(0,str(CASE/'scripts'))
from evidence import EvidenceError,sha,kv,exact_parameters
from contracts import verify_provenance,approved_records
from revision_s1 import verify_s1_revision
from check_results import check_slice
import prepare_packet
import run_S1 as runner


class S1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document=prepare_packet.view()
        cls.observed=json.loads((CHECKER/'s1_revision/anchor.json').read_text())['native_source_sha256']
        cls.library=REPORT/'s1_software_fixture.so'
        command=['g++','-O3','-march=native','-std=c++20','-fPIC','-shared',
                 '-I'+str(CASE/'src'),str(CHECKER/'tests/s1_arithmetic_fixture.cpp'),'-o',str(cls.library)]
        process=subprocess.run(command,capture_output=True,text=True,timeout=60)
        (REPORT/'software_fixture_build.json').write_text(json.dumps(dict(argv=command,exit=process.returncode,
            stdout=process.stdout,stderr=process.stderr,software_only_no_OpenLB=True),indent=2)+'\n')
        assert process.returncode==0,process.stderr
        cls.lib=ctypes.CDLL(str(cls.library));cls.lib.s1_mass_step.argtypes=[ctypes.c_double]*4
        cls.lib.s1_mass_step.restype=ctypes.c_double
        cls.lib.s1_volume_prefixes.argtypes=[ctypes.c_double,ctypes.POINTER(ctypes.c_double),ctypes.c_int]

    def test_actual_build_provenance_closed_authority(self):
        self.assertFalse(self.document['simulation_authorized'])
        verify_provenance(self.document)

    def test_exact_two_S1_identities(self):
        d=dict(self.document,approved_runs=self.document['prepared_runs'],approved_run_ids=self.document['prepared_run_ids'])
        self.assertEqual(len(approved_records(d)),2)

    def test_wrong_stage_rejected(self):
        for stage in ('S0_REGRESSION','S2_REG_GRID'):
            d=dict(self.document,stage=stage)
            with self.assertRaises(EvidenceError):verify_provenance(d)

    def test_wrong_case_pair_rejected(self):
        d=copy.deepcopy(self.document);d['prepared_runs'][0]['planned_case_id']='URV1_H75_P_dx5_a100000'
        with self.assertRaises(EvidenceError):verify_provenance(d)

    def test_nonwhitelisted_source_rejected(self):
        observed=dict(self.observed,**{'urv_reference.cpp':'0'*64})
        with self.assertRaises(EvidenceError):verify_s1_revision(self.document,observed,CHECKER)

    def mutated_anchor(self, change):
        with tempfile.TemporaryDirectory() as tmp:
            checker=Path(tmp);(checker/'s1_revision').mkdir()
            anchor=json.loads((CHECKER/'s1_revision/anchor.json').read_text());change(anchor)
            path=checker/'s1_revision/anchor.json';path.write_text(json.dumps(anchor))
            d=copy.deepcopy(self.document);d['inputs_sha256'][str(path)]=sha(path)
            d['source_revision']=dict(id='URV-S1-A1-v1',anchor=str(path),sha256=sha(path))
            with self.assertRaises(EvidenceError):verify_s1_revision(d,self.observed,checker)

    def test_failed_machine_audit_rejected(self):
        self.mutated_anchor(lambda a:a.update(instruction_audit_status='FAIL'))

    def test_false_anchor_authority_rejected(self):
        self.mutated_anchor(lambda a:a.update(simulation_authorized=True))

    def test_diff_binding_rejected(self):
        self.mutated_anchor(lambda a:a['diffs']['urv_reference.cpp'].update(sha256='0'*64))

    def test_missing_source_binding_rejected(self):
        d=copy.deepcopy(self.document);del d['inputs_sha256'][d['provenance']['native_sources'][0]]
        with self.assertRaises(EvidenceError):verify_provenance(d)

    def test_prepared_execution_rejected_before_native_or_marker(self):
        with patch.object(runner,'native_process') as native:
            with self.assertRaises(EvidenceError):
                # binding checks real preparation=false before using any process.
                path=REPORT/'SYNTHETIC_CLOSED_PREPARATION.json';path.write_text(json.dumps(self.document))
                runner.execute(path,sha(path),self.document)
            native.assert_not_called()
        self.assertFalse((CASE/'launch_attempts').exists())

    def test_S1_exact_time_and_size(self):
        for record in self.document['prepared_runs']:
            p=exact_parameters(kv(record['run_config_path']))
            self.assertEqual((p['window'],p['cap'],p['nodes']),(2592,27648,884736))

    def test_actual_C_helper_fma_oracle(self):
        dx=5e-9;rho=1.;m=3.5e-21;partial=((rho*1000.)*dx)*dx
        actual=self.lib.s1_mass_step(rho,1000.,dx,m)
        self.assertEqual(actual,float(Fraction(partial)*Fraction(dx)+Fraction(m)))
        self.assertNotEqual(actual,partial*dx+m)

    def test_S1_volume_all_884736_prefixes(self):
        count=884736;dx=1.25*1e-9;values=(ctypes.c_double*count)()
        self.lib.s1_volume_prefixes(dx,values,count);reference=0.;term=(dx*dx)*dx
        for value in values:
            reference+=term;self.assertEqual(value,reference)
        (REPORT/'volume_prefix_software.json').write_text(json.dumps(dict(prefixes=count,differences=0,
            volume_m3=reference,software_only=True,native_geometry_evidence=False),indent=2)+'\n')

    def smooth_fixture(self, folder, scale=1., distortion=0.):
        cfg=kv(self.document['prepared_runs'][0]['run_config_path']);p=exact_parameters(cfg)
        z=(np.arange(24)+.5)*p['dx'];u=p['a']*z*(p['h']-z)/(2*p['nu'])
        u=scale*u+distortion*u.max()*np.sin(2*np.pi*z/p['h'])
        rows=[dict(x=(x+.5)*p['dx'],z=float(zv),ux=0,uy=float(v),material=1)
              for x in range(192) for zv,v in zip(z,u)]
        with (folder/'field_slice.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        K=p['nu']*sum(row['uy'] for row in rows)*p['dx']**2/(p['P']*p['a'])
        return cfg,K

    def test_original_smooth_analytic_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg,K=self.smooth_fixture(Path(tmp));result=check_slice(Path(tmp),cfg,K)
            self.assertLess(result['K_relative_error'],.02);self.assertLess(result['profile_L2_relative'],.02)

    def test_original_smooth_K_failure_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg,K=self.smooth_fixture(Path(tmp),scale=1.021)
            with self.assertRaises(EvidenceError):check_slice(Path(tmp),cfg,K)

    def test_original_smooth_profile_failure_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg,K=self.smooth_fixture(Path(tmp),distortion=.04)
            with self.assertRaises(EvidenceError):check_slice(Path(tmp),cfg,K)

    def pipeline(self, native_code=0, checker_code=0, accepted=True):
        with tempfile.TemporaryDirectory() as tmp:
            case=Path(tmp);records=[]
            for d in ('P','T'):
                rid='SYNTHETIC_S1_'+d;run=case/'runs'/rid/'steady';run.mkdir(parents=True)
                (run/'run_config.txt').write_text('SOFTWARE_MOCK_ONLY\n')
                records.append(dict(run_id=rid,planned_case_id='SYNTHETIC_'+d,output_directory=str(run),run_config_path=str(run/'run_config.txt')))
            doc=dict(protocol_id='URV-v1',prepared_runs=records,approved_runs=records,
                prepared_run_ids=[r['run_id'] for r in records],approved_run_ids=[r['run_id'] for r in records],
                inputs_sha256={},provenance=dict(native_binary='SOFTWARE_MOCK_ONLY_NOT_EXECUTABLE'),
                launch_authorization=dict(user_explicitly_authorized=True,user_instruction_verbatim='SYNTHETIC FLAGS ONLY; NO REAL AUTHORIZATION'))
            def checked(argv,**kwargs):
                target=Path(argv[argv.index('--out')+1]);target.mkdir(parents=True)
                (target/'acceptance.json').write_text(json.dumps(dict(RESULT_PASS=accepted,NUMERICAL_GATE='PASS',geometry_PASS=True,smooth={})))
                return types.SimpleNamespace(returncode=checker_code)
            with patch.object(runner,'CASE',case),patch.object(runner,'binding',return_value=doc),\
                 patch.object(runner,'resources',return_value={}),\
                 patch.object(runner,'native_process',return_value=dict(independent_process_exit_code=native_code,timed_out=False,elapsed_seconds=0.)) as native,\
                 patch.object(runner.subprocess,'run',side_effect=checked):
                failed=native_code!=0 or checker_code!=0 or not accepted
                if failed:
                    with self.assertRaises(EvidenceError):runner.execute(Path('SYNTHETIC'), 'synthetic', doc)
                    self.assertEqual(native.call_count,1)
                else:
                    runner.execute(Path('SYNTHETIC'),'synthetic',doc);self.assertEqual(native.call_count,2)
                self.assertEqual((case/'launch_attempts/synthetic/S1_completed.json').exists(),not failed)

    def test_native_failure_prevents_T(self):self.pipeline(native_code=3)
    def test_checker_failure_prevents_T(self):self.pipeline(checker_code=2)
    def test_false_acceptance_prevents_T(self):self.pipeline(accepted=False)
    def test_mock_pair_success_no_next_stage(self):self.pipeline()


if __name__=='__main__':unittest.main()
