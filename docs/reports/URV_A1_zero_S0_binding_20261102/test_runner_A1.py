"""A1 controller policy tests. All hypothetical execution uses mocks only."""
from pathlib import Path
import copy,importlib.util,json,sys,tempfile,unittest
from unittest.mock import patch
# This file lives in docs/reports/<report>/; explicit source path, no shell.
PROJECT=Path(__file__).resolve().parents[3]
SCRIPT=PROJECT/'CASE/unseen_v2_reference_S0_mrp_v1_a1/scripts/run_S0_A1.py'
spec=importlib.util.spec_from_file_location('runner_A1_policy_test',SCRIPT)
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
PREP=SCRIPT.parents[1]/'evidence/S0_prepared_binding_A1_20261102_01.json'
DATA=json.loads(PREP.read_text());DIGEST=runner.sha(PREP)

class RunnerPolicy(unittest.TestCase):
    def test_actual_prepared_binding_readonly(self):
        with patch.object(runner,'native_process') as native:
            data,_=runner.inspect(PREP,DIGEST)
        self.assertFalse(data['simulation_authorized']);self.assertEqual(data['approved_run_ids'],[])
        native.assert_not_called()

    def test_prepared_binding_cannot_execute_or_create_attempt(self):
        marker=runner.CASE/'launch_attempts';before=marker.exists()
        with patch.object(runner,'native_process') as native:
            with self.assertRaisesRegex(ValueError,'preparation only'):
                runner.execute(PREP,DIGEST,DATA)
        self.assertEqual(marker.exists(),before);native.assert_not_called()

    def test_release_sha_mismatch_rejected(self):
        with self.assertRaises(ValueError):runner.inspect(PREP,'0'*64)

    def test_resource_failure_stops_inspection(self):
        with patch.object(runner,'resources',side_effect=ValueError('SYNTHETIC resource shortage')):
            with self.assertRaisesRegex(ValueError,'resource shortage'):runner.inspect(PREP,DIGEST)

    def test_bound_input_drift_stops_inspection(self):
        with patch.object(runner,'unchanged',side_effect=ValueError('SYNTHETIC input drift')):
            with self.assertRaisesRegex(ValueError,'input drift'):runner.inspect(PREP,DIGEST)

    def synthetic(self,root):
        # No authorization contract is written. This in-memory fixture bypasses
        # binding solely to exercise downstream stopping, with all native calls mocked.
        records=[]
        for d in ('P','T'):
            run=root/'runs'/('SYNTHETIC_'+d)/'steady';run.mkdir(parents=True)
            config=run/'run_config.txt';config.write_text('SYNTHETIC NOT A RUN CONFIG\n')
            records.append(dict(run_id='SYNTHETIC_'+d,planned_case_id='SYNTHETIC_CASE_'+d,
                                output_directory=str(run),run_config_path=str(config)))
        return dict(fixture_label='SYNTHETIC_POLICY_ONLY_NO_USER_AUTHORIZATION',
            prepared_run_ids=['SYNTHETIC_P','SYNTHETIC_T'],approved_run_ids=['SYNTHETIC_P','SYNTHETIC_T'],
            prepared_runs=records,approved_runs=records,inputs_sha256={},
            launch_authorization=dict(user_explicitly_authorized=True,user_instruction_verbatim='SYNTHETIC MOCK ONLY'),
            provenance=dict(native_binary='SYNTHETIC_NEVER_EXECUTED'))

    def stop_case(self,reason):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=self.synthetic(root)
            native_result=dict(independent_process_exit_code=7 if reason=='native' else 0,timed_out=False,elapsed_seconds=0)
            finalize_error=ValueError('SYNTHETIC corrupt capture') if reason=='capture' else None
            def checker_call(command,**kwargs):
                if reason=='checker':return type('Exit',(),{'returncode':2})()
                out=Path(command[command.index('--out')+1]);out.mkdir(parents=True)
                receipt={k:True for k in ['RESULT_PASS','URV_RESULT_PASS','MASS_CAPTURE_INTEGRITY',
                                          'SAME_INPUT_REPLAY','CORRECTED_LEDGER_UNCHANGED','PHYSICAL_OUTPUT_GUARD']}
                receipt['fixture_label']='SYNTHETIC_NOT_SCIENTIFIC_ACCEPTANCE'
                if reason=='replay_flag':receipt['SAME_INPUT_REPLAY']=False
                (out/'mass_repair_review.json').write_text(json.dumps(receipt))
                return type('Exit',(),{'returncode':0})()
            with patch.object(runner,'CASE',root),patch.object(runner,'binding',return_value=data),\
                 patch.object(runner,'resources',return_value={'fixture':'no real resource probe'}),\
                 patch.object(runner,'unchanged',return_value={}),\
                 patch.object(runner,'native_process',return_value=native_result) as native,\
                 patch.object(runner,'finalize_capture',side_effect=finalize_error) as finalize,\
                 patch.object(runner.subprocess,'run',side_effect=checker_call) as check:
                if reason=='success':runner.execute(Path('SYNTHETIC'), 'SYNTHETIC_SHA',data)
                else:
                    with self.assertRaises(ValueError):runner.execute(Path('SYNTHETIC'),'SYNTHETIC_SHA',data)
                self.assertEqual(native.call_count,2 if reason=='success' else 1)
                if reason in ('native','capture'):check.assert_not_called()
                if reason=='native':finalize.assert_not_called()
                else:self.assertEqual(finalize.call_count,2 if reason=='success' else 1)
            self.assertEqual((root/'launch_attempts/SYNTHETIC_SHA/S0_completed.json').exists(),reason=='success')

    def test_native_failure_no_T(self):self.stop_case('native')
    def test_capture_failure_no_checker_or_T(self):self.stop_case('capture')
    def test_original_or_supplementary_checker_failure_no_T(self):self.stop_case('checker')
    def test_inconsistent_replay_flag_no_T_even_exit_zero(self):self.stop_case('replay_flag')
    def test_synthetic_two_case_sequence_only_after_full_flags(self):self.stop_case('success')

if __name__=='__main__':unittest.main()
