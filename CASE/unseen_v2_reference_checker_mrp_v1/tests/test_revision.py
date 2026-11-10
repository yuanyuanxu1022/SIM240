from pathlib import Path
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
from evidence import EvidenceError,sha
from contracts import approved_records,check_run_identity,output_location
import check_results as checker
from fixtures_contract import ContractFixture,CASE

class RevisionTests(unittest.TestCase):
    def cli(self,raw,out,root,batch=None):
        seal=CASE.parent/'unseen_v2_reference_v1/evidence/preparation_seal.json'
        command=[sys.executable,'-B',str(CASE/'analysis/check_results.py')]
        command+=['--batch-index',str(batch)] if batch else ['--run',str(raw)]
        command+=['--release',str(seal),'--release-sha256',sha(seal),'--out',str(out)]
        return subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
            env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'),timeout=30)

    def test_F01_raw_itself_has_no_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'raw';raw.mkdir();(raw/'marker').write_text('SYNTHETIC')
            before=list(raw.iterdir());proc=self.cli(raw,raw,root)
            self.assertEqual(proc.returncode,2);self.assertEqual(before,list(raw.iterdir()))

    def test_F01_child_directory_not_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'raw';raw.mkdir();target=raw/'new_analysis'
            self.assertEqual(self.cli(raw,target,root).returncode,2)
            self.assertFalse(target.exists());self.assertEqual(list(raw.iterdir()),[])

    def test_F01_symlink_output_cannot_enter_raw(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'raw';raw.mkdir();alias=root/'alias';alias.symlink_to(raw,target_is_directory=True)
            self.assertEqual(self.cli(raw,alias/'child',root).returncode,2)
            self.assertEqual(list(raw.iterdir()),[])

    def test_F01_input_symlink_is_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'raw';raw.mkdir();alias=root/'alias';alias.symlink_to(raw,target_is_directory=True)
            self.assertEqual(self.cli(alias,raw/'child',root).returncode,2)
            self.assertEqual(list(raw.iterdir()),[])

    def test_F01_existing_output_not_modified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'raw';raw.mkdir();out=root/'out';out.mkdir()
            (out/'marker').write_text('existing analysis')
            self.assertEqual(self.cli(raw,out,root).returncode,2)
            self.assertEqual([p.name for p in out.iterdir()],['marker'])

    def test_F01_raw_ancestor_not_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'raw';raw.mkdir()
            self.assertEqual(self.cli(raw,root,root).returncode,2)
            self.assertFalse((root/'failure.json').exists())

    def test_F01_batch_checks_every_raw_before_first_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);runs=[]
            for n in range(24):
                p=root/f'raw{n}';p.mkdir();runs.append(str(p))
            index=root/'index.json';index.write_text(json.dumps(runs))
            target=Path(runs[-1])/'out'
            self.assertEqual(self.cli(None,target,root,index).returncode,2)
            self.assertFalse(target.exists())
            self.assertTrue(all(list(Path(p).iterdir())==[] for p in runs))

    def test_F01_valid_new_output_retains_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'raw';raw.mkdir();out=root/'out'
            self.assertEqual(self.cli(raw,out,root).returncode,2)
            self.assertTrue((out/'failure.json').is_file())
            self.assertFalse((out/'acceptance.json').exists());self.assertEqual(list(raw.iterdir()),[])

    def test_F01_release_baseline_is_protected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);f=ContractFixture(root);baseline=root/'baseline';baseline.mkdir()
            f.document['h75_regression_references']={'P':{'directory':str(baseline)}}
            digest=f.rewrite()
            with self.assertRaises(EvidenceError):checker.check_run(f.run,f.path,digest,baseline/'analysis')
            self.assertEqual(list(baseline.iterdir()),[])

    def test_F01_protected_package_target_refused(self):
        with self.assertRaises(EvidenceError):output_location(CASE/'new_analysis',[Path('/tmp/SYNTHETIC_RAW')])

    def test_F01_standalone_reader_rejects_raw_output_without_reading_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw=Path(tmp)/'raw';raw.mkdir();target=raw/'forbidden.json'
            proc=subprocess.run(['/usr/bin/pvpython','--force-offscreen-rendering','-B',str(CASE/'analysis/read_fields.py'),
                '--run',str(raw),'--out',str(target)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                env=dict(os.environ,QT_QPA_PLATFORM='offscreen',OPENBLAS_NUM_THREADS='1'),timeout=30)
            self.assertEqual(proc.returncode,2);self.assertFalse(target.exists())
            self.assertEqual(list(raw.iterdir()),[])

    def regression(self,root,changed=False,K=1e-23):
        baseline=root/'old';raw=root/'new';out=root/'analysis'
        for p in [baseline,raw,out]:p.mkdir()
        old='step,J,mass_error\n0,0.5,0\n1,1,0\n'
        (baseline/'diagnostics.csv').write_text(old)
        (raw/'diagnostics.csv').write_text(old.replace('1,1,0','1,1.001,0') if changed else old)
        (baseline/'result.txt').write_text('Keff_m3=1e-23\n')
        reference=dict(directory=str(baseline),result_sha256=sha(baseline/'result.txt'),diagnostics_sha256=sha(baseline/'diagnostics.csv'))
        return raw,out,reference,K

    def test_F02_exact_regression_report_saved(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw,out,ref,K=self.regression(Path(tmp));result=checker.regression_check(raw,ref,K,out)
            report=json.loads((out/'regression_comparison.json').read_text())
            self.assertTrue(result['legacy']['all_exact']);self.assertTrue(report['K_gate_PASS'])

    def test_F02_changed_column_saved_before_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw,out,ref,K=self.regression(Path(tmp),changed=True)
            with self.assertRaisesRegex(EvidenceError,'legacy trajectory difference'):checker.regression_check(raw,ref,K,out)
            report=json.loads((out/'regression_comparison.json').read_text())
            self.assertFalse(report['legacy_gate_PASS']);self.assertGreater(report['legacy']['all_common_columns']['J']['max_absolute_difference'],0)
            self.assertEqual(set(report['legacy']['all_common_columns']),{'J','mass_error','step'})

    def test_F02_large_K_change_report_saved_before_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw,out,ref,K=self.regression(Path(tmp),K=1.01e-23)
            with self.assertRaisesRegex(EvidenceError,'K port regression'):checker.regression_check(raw,ref,K,out)
            report=json.loads((out/'regression_comparison.json').read_text())
            self.assertGreater(report['relative_K_change'],1e-4);self.assertFalse(report['K_gate_PASS'])

    def test_F02_wrapper_keeps_difference_and_failure_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw,out,ref,K=self.regression(root,changed=True);out.rmdir()
            def fail_with_real_comparison(run,release,anchor,owned):
                return checker.regression_check(run,ref,K,owned)
            release=root/'SYNTHETIC_PATH_DECLARATIONS_ONLY.json';release.write_text('{}')
            with patch.object(checker,'_check_run',side_effect=fail_with_real_comparison):
                with self.assertRaises(EvidenceError):checker.check_run(raw,release,'synthetic',out)
            self.assertTrue((out/'failure.json').exists());self.assertTrue((out/'regression_comparison.json').exists())
            self.assertFalse((out/'acceptance.json').exists())

    def fixture_test(self,mutate,regex=None):
        with tempfile.TemporaryDirectory() as tmp:
            fixture=ContractFixture(tmp);mutate(fixture);digest=fixture.rewrite()
            if regex:
                with self.assertRaisesRegex((EvidenceError,KeyError),regex):checker.binding(fixture.path,digest)
            else:
                with self.assertRaises((EvidenceError,KeyError)):checker.binding(fixture.path,digest)

    def test_F03_complete_synthetic_closure_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=ContractFixture(tmp);bound=checker.binding(f.path,sha(f.path))
            self.assertEqual(bound['approved_runs'][0]['run_id'],'SYNTHETIC_S0_P')
            check_run_identity(bound,f.run,f.cfg,'SYNTHETIC_S0_P','URV1_H75_P_dx5_a100000')

    def test_F03_old_minimal_release_no_longer_accepted(self):
        def mutate(f):f.document.pop('provenance')
        self.fixture_test(mutate,'roles missing')

    def test_F03_omitted_native_binary_rejected(self):
        self.fixture_test(lambda f:f.document['inputs_sha256'].pop(str(f.binary)),'required provenance not bound')

    def test_F03_omitted_native_source_rejected(self):
        self.fixture_test(lambda f:f.document['inputs_sha256'].pop(str(f.sources[0])),'required provenance not bound')

    def test_F03_missing_compiler_dependency_rejected(self):
        def mutate(f):f.env['dependency_sha256'].pop(str(f.header));f.refresh()
        self.fixture_test(mutate,'dependency closure incomplete')

    def test_F03_missing_runtime_library_rejected(self):
        def mutate(f):f.env['dynamic_library_sha256']={};f.refresh()
        self.fixture_test(mutate,'runtime library closure incomplete')

    def test_F03_missing_linked_library_rejected(self):
        def mutate(f):f.env['link_library_sha256'].pop(str(f.static[-1]));f.refresh()
        self.fixture_test(mutate,'required linked library not captured')

    def test_F03_missing_dependency_input_hash_rejected(self):
        self.fixture_test(lambda f:f.document['inputs_sha256'].pop(str(f.header)),'required provenance not bound')

    def test_F03_current_preparation_build_rejected(self):
        def mutate(f):f.env['preparation_only_build']=True;f.refresh()
        self.fixture_test(mutate,'preparation build cannot pass')

    def test_F03_ambiguous_preparation_flag_rejected(self):
        def mutate(f):f.env['compile_command']+=' -DURV_PREPARATION_ONLY=1';f.refresh()
        self.fixture_test(mutate,'flag missing or ambiguous')

    def test_F03_physical_source_edit_rejected(self):
        def mutate(f):
            f.sources[0].write_text(f.sources[0].read_text()+'\n// SYNTHETIC mutation\n')
            f.env['native_sources_sha256'][str(f.sources[0])]=sha(f.sources[0]);f.refresh()
        self.fixture_test(mutate,'physical source differs')

    def test_F03_missing_run_map_rejected(self):
        self.fixture_test(lambda f:f.document.pop('approved_runs'),'per-run identity bindings required')

    def test_F03_duplicate_approved_ID_rejected(self):
        self.fixture_test(lambda f:f.document['approved_run_ids'].append('SYNTHETIC_S0_P'),'duplicate approved run')

    def test_F03_config_changed_after_binding_rejected(self):
        self.fixture_test(lambda f:f.cfg.write_text(f.cfg.read_text().replace('dx_nm=5','dx_nm=2.5')),'source/input changed')

    def test_F03_swapped_case_rejected(self):
        self.fixture_test(lambda f:f.document['approved_runs'][0].update(planned_case_id='URV1_H75_T_dx5_a100000'),'direction mismatch')

    def test_F03_output_directory_swap_rejected(self):
        self.fixture_test(lambda f:f.document['approved_runs'][0].update(output_directory=str(f.root/'elsewhere')),'identity/directory mismatch')

    def test_F03_config_SHA_swap_rejected(self):
        self.fixture_test(lambda f:f.document['approved_runs'][0].update(run_config_sha256='0'*64),'config SHA mismatch')

    def test_F03_stage_swap_rejected(self):
        self.fixture_test(lambda f:f.document.update(stage='S1_SMOOTH_THIN'),'cross-stage')

    def test_F03_completed_run_identity_swap_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=ContractFixture(tmp);bound=checker.binding(f.path,sha(f.path))
            with self.assertRaisesRegex(EvidenceError,'run-to-case'):check_run_identity(bound,f.run,f.cfg,'SYNTHETIC_S0_P','URV1_H75_T_dx5_a100000')

    def test_F03_pending_history_stays_blocked(self):
        self.fixture_test(lambda f:f.document.update(author_external_data_history_confirmation='PENDING'),'history pending')

if __name__=='__main__':unittest.main(verbosity=2)
