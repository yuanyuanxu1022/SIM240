"""Provenance and control-flow tests only. Never runs OpenLB; temp data are synthetic."""
import copy
import importlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import binding as b
import run_c
import analyze_completed_c as analyzer

class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bound,cls.protocol=b.verify_binding()

    def mutated(self,target):
        target=Path(target)
        def read(path):
            data=b.read_bytes(path)
            return data+b'\n' if Path(path)==target else data
        with self.assertRaises((RuntimeError,ValueError)):b.verify_binding(read=read)

    def test_01_real_binding_and_physics_equal(self):
        bound,protocol=b.verify_binding()
        self.assertEqual(b.read_json(b.ROOT/'physical_contract.json'),b.source_contract(protocol))
        self.assertEqual(bound['alpha_dependency']['original_input_count'],391)

    def test_02_source_tamper_rejected(self):self.mutated(b.PARENT/'src/coupled_check.cpp')
    def test_03_binary_tamper_rejected(self):self.mutated(b.PARENT/'build/coupled_check')
    def test_04_parameter_tamper_rejected(self):self.mutated(b.PARENT/'protocol.json')
    def test_05_alpha_raw_tamper_rejected(self):
        verdict=b.read_json(b.PARENT/'analysis_alpha/verdict.json')
        self.mutated(next(p for p in verdict['input_sha256'] if p.endswith('history.csv')))
    def test_06_alpha_verdict_tamper_rejected(self):self.mutated(b.PARENT/'analysis_alpha/verdict.json')
    def test_07_parent_binding_tamper_rejected(self):self.mutated(b.PARENT/'evidence/build_binding.json')
    def test_08_new_AGENTS_tamper_rejected(self):self.mutated(b.PARENT.parents[2]/'AGENTS.md')
    def test_09_new_script_tamper_rejected(self):self.mutated(b.ROOT/'analyze_completed_c.py')
    def test_10_physics_declaration_tamper_rejected(self):self.mutated(b.ROOT/'physical_contract.json')
    def test_11_export_provenance_tamper_rejected(self):self.mutated(b.PARENT/'analysis_alpha/EXPORT_PROVENANCE.json')

    def test_12_missing_bound_entry_rejected(self):
        payload=copy.deepcopy(self.bound);payload['sha256'].pop(str(b.PARENT/'src/coupled_check.cpp'))
        def read(path):return json.dumps(payload).encode() if Path(path)==b.binding_path() else b.read_bytes(path)
        with self.assertRaises(RuntimeError):b.verify_binding(read=read)

    def test_13_default_cli_never_executes_or_creates_formal_dirs(self):
        before=[p.exists() for p in b.paths()]
        with patch.object(sys,'argv',['run_c.py']),patch.object(run_c.subprocess,'run',side_effect=AssertionError('forbidden solver invocation')),redirect_stdout(io.StringIO()):
            self.assertEqual(run_c.main(),0)
        self.assertEqual(before,[p.exists() for p in b.paths()]);self.assertEqual(before,[False,False])

    def test_14_analyzer_input_check_never_executes_or_writes(self):
        before=[p.exists() for p in b.paths()]
        with patch.object(sys,'argv',['analyze_completed_c.py','--check-inputs']),patch.object(run_c.subprocess,'run',side_effect=AssertionError('forbidden solver invocation')),redirect_stdout(io.StringIO()):
            self.assertEqual(analyzer.main(),0)
        self.assertEqual(before,[p.exists() for p in b.paths()])

    def test_15_analyzer_refuses_absent_completion_no_output(self):
        target=b.ROOT/'analysis_test_missing_completion'
        with patch.object(sys,'argv',['analyze_completed_c.py','--output',str(target)]):
            with self.assertRaises(FileNotFoundError):analyzer.main()
        self.assertFalse(target.exists())

    def fixture(self,root):
        (root/'execution_binding.json').write_text(json.dumps(self.bound))
        ev,out=b.paths(root);ev.mkdir(parents=True);out.mkdir(parents=True)
        manifest=dict(schema_version=2,execution_id=b.EXECUTION_ID,protocol_id=b.EXECUTION_ID,
            physics_protocol_id=b.PARENT_ID,batch_id=b.BATCH,stage='c',execution_binding_sha256=b.sha(root/'execution_binding.json'),
            source_binding=self.bound,alpha_dependency=self.bound['alpha_dependency'],started_utc=b.now(),finished_utc=b.now(),
            independent_exit_code=0,source_hashes_unchanged=True,source_mismatches=[],cases=[],synthetic_provenance_fixture=True)
        for case in self.protocol['stages']['c']:
            rid=b.BATCH+'_'+case['id'];sub=ev/rid;data=out/rid;sub.mkdir();data.mkdir();(data/'frames').mkdir()
            entry=dict(run_id=rid,case_id=case['id'],stage='c',parameters=case,command=b.command(case,data),cwd=str(b.PARENT),
                       started_utc=b.now(),finished_utc=b.now(),independent_exit_code=0)
            manifest['cases'].append(entry);(sub/'manifest.json').write_text(json.dumps(entry));(sub/'exit_code.txt').write_text('0\n');(sub/'console.log').write_text('SYNTHETIC fixture, no solver\n')
            for name in ['config.json','history.csv','frame_schema.json','step1_pre.bin.gz','step1_post_collision.bin.gz','step1_post_stream.bin.gz']:(data/name).write_text('SYNTHETIC: not numerical data')
            (data/'result.json').write_text(json.dumps(dict(requested_steps=64,completed_steps=64,NS_collide_calls=64,CH_collide_calls=64,safe=True)))
            for t in range(65):(data/'frames'/f'step_{t}.bin.gz').write_text('SYNTHETIC: not numerical data')
        (ev/'manifest.json').write_text(json.dumps(manifest));(ev/'exit_code.txt').write_text('0\n')
        return manifest

    def test_16_complete_provenance_fixture_and_wrong_batch_rejection(self):
        with tempfile.TemporaryDirectory(prefix='sim240_c_provenance_') as temp:
            root=Path(temp);m=self.fixture(root)
            # Positive provenance only: never assert numerical acceptance on these files.
            self.assertEqual(len(b.validate_completed(root,self.bound)[1]),4)
            m['batch_id']='wrong';(b.paths(root)[0]/'manifest.json').write_text(json.dumps(m))
            with self.assertRaises(RuntimeError):b.validate_completed(root,self.bound)

    def test_17_child_independent_exit_mismatch_rejected(self):
        with tempfile.TemporaryDirectory(prefix='sim240_c_exit_') as temp:
            root=Path(temp);m=self.fixture(root);ev,_=b.paths(root)
            (ev/m['cases'][0]['run_id']/'exit_code.txt').write_text('7\n')
            with self.assertRaises(RuntimeError):b.validate_completed(root,self.bound)

    def test_18_missing_frame_rejected(self):
        with tempfile.TemporaryDirectory(prefix='sim240_c_missing_') as temp:
            root=Path(temp);m=self.fixture(root);_,out=b.paths(root)
            (out/m['cases'][0]['run_id']/'frames/step_31.bin.gz').unlink()
            with self.assertRaises(RuntimeError):b.validate_completed(root,self.bound)

    def test_19_zero_step_result_rejected(self):
        with tempfile.TemporaryDirectory(prefix='sim240_c_zero_') as temp:
            root=Path(temp);m=self.fixture(root);_,out=b.paths(root);p=out/m['cases'][0]['run_id']/'result.json'
            v=b.read_json(p);v['completed_steps']=0;p.write_text(json.dumps(v))
            with self.assertRaises(RuntimeError):b.validate_completed(root,self.bound)

    def test_20_binding_manifest_disagreement_rejected(self):
        with tempfile.TemporaryDirectory(prefix='sim240_c_manifest_') as temp:
            root=Path(temp);m=self.fixture(root);m['execution_binding_sha256']='0'*64
            (b.paths(root)[0]/'manifest.json').write_text(json.dumps(m))
            with self.assertRaises(RuntimeError):b.validate_completed(root,self.bound)

    def test_21_frozen_numerical_loader_rejects_synthetic_fixture(self):
        with tempfile.TemporaryDirectory(prefix='sim240_c_numeric_reject_') as temp:
            root=Path(temp);self.fixture(root);case=self.protocol['stages']['c'][0]
            sys.path.insert(0,str(b.PARENT))
            from analyze_c import analyze_case
            with self.assertRaises((ValueError,RuntimeError)):
                analyze_case(case,b.paths(root)[1]/(b.BATCH+'_'+case['id']),self.protocol['thresholds'])

    def test_22_budget_failure_not_waived_and_Gates_never_promoted(self):
        rows=[dict(initialization_only=False,implementation_contract_pass=True,physical_amount_drift_within_budget=True,safety_pass=True) for _ in range(4)]
        self.assertTrue(b.summarize(rows)['complete_C_contract_pass'])
        rows[1]['physical_amount_drift_within_budget']=False;summary=b.summarize(rows)
        self.assertTrue(summary['implementation_contract_pass']);self.assertFalse(summary['complete_C_contract_pass'])
        for k,v in b.GATES.items():self.assertEqual(summary[k],v)

    def test_23_stub_execution_stops_at_nonzero_without_solver(self):
        with tempfile.TemporaryDirectory(prefix='sim240_c_stub_exec_') as temp:
            root=Path(temp);(root/'execution_binding.json').write_text(json.dumps(self.bound));calls=[]
            def fake(command,**kwargs):
                calls.append(command);kwargs['stdout'].write('SYNTHETIC process stub; no OpenLB\n')
                return SimpleNamespace(returncode=9 if len(calls)==2 else 0)
            with patch.object(run_c,'ROOT',root),patch.object(run_c,'paths',lambda:b.paths(root)),patch.object(run_c,'binding_path',lambda:root/'execution_binding.json'),\
                 patch.object(run_c,'precheck',return_value=(self.bound,self.protocol)),patch.object(run_c,'verify_binding',return_value=(self.bound,self.protocol)),\
                 patch.object(run_c,'post_mismatches',return_value=[]),patch.object(run_c.subprocess,'run',side_effect=fake),redirect_stdout(io.StringIO()):
                self.assertEqual(run_c.execute(),9)
            self.assertEqual(len(calls),2);m=b.read_json(b.paths(root)[0]/'manifest.json')
            self.assertEqual(m['independent_exit_code'],9);self.assertEqual(len(m['cases']),2)

if __name__=='__main__':unittest.main(verbosity=2)
