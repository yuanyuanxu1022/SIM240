"""Artificial process receipts test fail-stop; no native/field solver executes."""
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
path = ROOT / 'CASE/unseen_v2_reference_S0_v1_2/scripts/run_S0.py'
spec = importlib.util.spec_from_file_location('s0_runner_under_test', path)
runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)


class RunnerTests(unittest.TestCase):
    def fixture(self, root):
        source = root / 'SYNTHETIC_INPUT'; source.write_text('frozen')
        records = []
        for direction in ['P', 'T']:
            run = root / 'runs' / direction; run.mkdir(parents=True)
            config = run / 'run_config.txt'; config.write_text('SYNTHETIC NOT A SOLVER CONFIG')
            records.append(dict(run_id='SYNTHETIC_' + direction, planned_case_id='SYNTHETIC_' + direction,
                                run_config_path=str(config), output_directory=str(run)))
        data = dict(prepared_runs=records, approved_runs=records,
            prepared_run_ids=['SYNTHETIC_P', 'SYNTHETIC_T'], approved_run_ids=['SYNTHETIC_P', 'SYNTHETIC_T'],
            inputs_sha256={str(source): runner.sha(source)},
            provenance={'native_binary': 'SYNTHETIC_NEVER_EXECUTED'},
            launch_authorization=dict(user_explicitly_authorized=True,
                user_instruction_verbatim='ARTIFICIAL TEST FLAGS ONLY; NOT USER AUTHORITY'))
        return data, source

    def scenario(self, code=0, timeout=False, checker_code=0, drift=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); data, source = self.fixture(root)
            calls = []
            def artificial_process(command, run, env):
                calls.append(run.name)
                (run / 'run.log').write_text('SYNTHETIC output; no native program ran\n')
                (run / 'vtkData').mkdir(); (run / 'vtkData/payload.vti').write_text('SYNTHETIC bytes')
                if drift:
                    source.write_text('changed synthetic input')
                return dict(independent_process_exit_code=code, timed_out=timeout, elapsed_seconds=0.0)
            with patch.object(runner, 'CASE', root), \
                 patch.object(runner, 'binding', return_value=data), \
                 patch.object(runner, 'resources', return_value={'fixture': True}), \
                 patch.object(runner, 'native_process', side_effect=artificial_process), \
                 patch.object(runner.subprocess, 'run', return_value=SimpleNamespace(returncode=checker_code)):
                error = None
                try:
                    runner.execute(root / 'SYNTHETIC_RELEASE', 'SYNTHETIC_ANCHOR', data)
                except runner.need.__globals__['EvidenceError'] as e:
                    error = str(e)
            completed = json.loads((root / 'runs/P/completion.json').read_text())
            self.assertIn('vtkData/payload.vti', completed['output_sha256'])
            if code != 0 or timeout or checker_code != 0 or drift:
                self.assertIsNotNone(error)
                self.assertEqual(calls, ['P'])
                self.assertFalse((root / 'runs/T/run.log').exists())
                self.assertFalse((root / 'launch_attempts/SYNTHETIC_ANCHOR/S0_completed.json').exists())
            else:
                self.assertIsNone(error)
                self.assertEqual(calls, ['P', 'T'])
                done = json.loads((root / 'launch_attempts/SYNTHETIC_ANCHOR/S0_completed.json').read_text())
                self.assertFalse(done['next_stage_started'])
                self.assertFalse(done['reference_qualified'])
            return completed

    def test_native_failure_stops_before_T_and_preserves_completion(self):
        self.assertEqual(self.scenario(code=3)['independent_process_exit_code'], 3)

    def test_timeout_stops_before_T_and_preserves_completion(self):
        self.assertTrue(self.scenario(code=-15, timeout=True)['timed_out'])

    def test_independent_check_failure_stops_before_T(self):
        self.scenario(checker_code=2)

    def test_input_drift_stops_before_T(self):
        self.assertFalse(self.scenario(drift=True)['inputs_unchanged'])

    def test_two_artificial_successes_never_enter_S1(self):
        self.scenario()

    def test_missing_separate_authorization_prevents_process_or_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); data, _ = self.fixture(root)
            data['launch_authorization']['user_explicitly_authorized'] = False
            with patch.object(runner, 'CASE', root), patch.object(runner, 'binding', return_value=data), \
                 patch.object(runner, 'native_process') as process:
                with self.assertRaisesRegex(ValueError, 'separate user launch authorization missing'):
                    runner.execute(root / 'SYNTHETIC_RELEASE', 'SYNTHETIC', data)
                process.assert_not_called()
            self.assertFalse((root / 'launch_attempts').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
