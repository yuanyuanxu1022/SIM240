"""S2 source/authority/fail-stop software checks. All native paths are mocked."""
from pathlib import Path
from contextlib import ExitStack
import copy
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

CHECKER = Path(__file__).resolve().parents[1]
CASE = CHECKER.parent / 'unseen_v2_reference_S2_reuse_v1'
sys.path.insert(0, str(CHECKER/'analysis'))
sys.path.insert(0, str(CASE/'scripts'))
from evidence import EvidenceError, sha, kv, exact_parameters
from contracts import verify_provenance
from stage_s2 import (validate_records, validate_zero_plan, validate_zero_authority,
                      validate_formal_authority, require_pristine, verify_seal, CASES, MODES)
import prepare_S2 as prep
import run_S2 as runner
import audit_S2_zero as auditor


class S2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = prep.view()

    def mutation_rejected(self, change):
        d = copy.deepcopy(self.data); change(d)
        with self.assertRaises(EvidenceError):
            verify_provenance(d)

    def test_genuine_reused_provenance_with_closed_authority(self):
        verify_provenance(self.data)
        self.assertFalse(self.data['simulation_authorized'])
        self.assertFalse(self.data['native_zero_step_authorized'])
        self.assertFalse(self.data['performance_time_stepping_authorized'])

    def test_six_exact_records(self):
        self.assertEqual(len(validate_records(self.data, CHECKER)), 6)

    def test_eighteen_zero_records(self):
        records = validate_zero_plan(self.data)
        self.assertEqual([(r['planned_case_id'], r['mode']) for r in records], [(c, m) for c in CASES for m in MODES])

    def test_exact_grid_time_arithmetic(self):
        expected = {5.: (46080, 648, 37632), 2.5: (368640, 2592, 150528), 1.25: (2949120, 10368, 602112)}
        for r in self.data['prepared_runs']:
            cfg = kv(r['run_config_path']); p = exact_parameters(cfg)
            self.assertEqual((p['nodes'], p['window'], p['cap']), expected[float(cfg['dx_nm'])])

    def test_original_scientific_reader_bytes(self):
        original = CASE.parent/'unseen_v2_reference_checker_S1_a1_v1'
        for name in ['check_results.py', 'evidence.py', 'read_fields.py']:
            self.assertEqual((CHECKER/'analysis'/name).read_bytes(), (original/'analysis'/name).read_bytes())
        for p in (CHECKER/'common').iterdir():
            if p.is_file(): self.assertEqual(p.read_bytes(), (original/'common'/p.name).read_bytes())

    def test_wrong_stage_rejected(self):
        self.mutation_rejected(lambda d: d.update(stage='S1_SMOOTH_THIN'))

    def test_partial_case_list_rejected(self):
        self.mutation_rejected(lambda d: d['prepared_runs'].pop())

    def test_extra_case_rejected(self):
        self.mutation_rejected(lambda d: d['prepared_runs'].append(copy.deepcopy(d['prepared_runs'][0])))

    def test_wrong_geometry_case_rejected(self):
        self.mutation_rejected(lambda d: d['prepared_runs'][0].update(planned_case_id='URV1_U_THIN_P_dx5_a100000'))

    def test_reordered_cases_rejected(self):
        self.mutation_rejected(lambda d: d['prepared_runs'].reverse())

    def test_performance_identity_rejected(self):
        self.mutation_rejected(lambda d: d['prepared_runs'][0].update(run_id='PERF_SOFTWARE_ONLY'))

    def test_all_grids_four_hours_rejected(self):
        self.mutation_rejected(lambda d: d['resources'].update(solver_wall_cap_seconds_per_case=14400))

    def test_wrong_fine_wall_cap_rejected(self):
        self.mutation_rejected(lambda d: d['resources']['solver_wall_cap_seconds_by_dx_nm'].update({'1.25': 86400}))

    def test_wrong_binary_binding_rejected(self):
        self.mutation_rejected(lambda d: d['inputs_sha256'].update({d['provenance']['native_binary']: '0'*64}))

    def test_missing_native_source_rejected(self):
        self.mutation_rejected(lambda d: d['inputs_sha256'].pop(d['provenance']['native_sources'][0]))

    def test_missing_runtime_library_rejected(self):
        env = json.loads(Path(self.data['provenance']['build_environment']).read_text())
        library = next(iter(env['dynamic_library_sha256']))
        self.mutation_rejected(lambda d: d['inputs_sha256'].pop(library))

    def test_old_S1_guard_still_rejects_S2(self):
        from revision_s1 import verify_s1_revision
        with self.assertRaises(EvidenceError):
            verify_s1_revision(self.data, {}, CHECKER)

    def test_zero_plan_missing_call_rejected(self):
        d = copy.deepcopy(self.data); d['zero_prepared_runs'].pop()
        with self.assertRaises(EvidenceError): validate_zero_plan(d)

    def test_zero_plan_steady_rejected(self):
        d = copy.deepcopy(self.data); d['zero_prepared_runs'][0]['mode'] = 'steady'
        with self.assertRaises(EvidenceError): validate_zero_plan(d)

    def test_zero_plan_output_escape_rejected(self):
        d = copy.deepcopy(self.data); d['zero_prepared_runs'][0]['output_directory'] = str(CASE.parent)
        with self.assertRaises(EvidenceError): validate_zero_plan(d)

    def test_zero_native_wrapper_refuses_steady_before_process(self):
        record = copy.deepcopy(self.data['prepared_runs'][0])
        with patch.object(auditor, 'native_process') as native:
            with self.assertRaises(EvidenceError): auditor.call_native('SOFTWARE_ONLY_NOT_EXECUTABLE', record, {})
            native.assert_not_called()

    def test_preparation_not_zero_authority(self):
        with self.assertRaises(EvidenceError): validate_zero_authority(self.data)

    def test_preparation_not_formal_authority(self):
        with self.assertRaises(EvidenceError): validate_formal_authority(self.data)

    def test_performance_release_not_formal_authority(self):
        d = copy.deepcopy(self.data); d.update(kind='AUTHORIZED_PERFORMANCE_RELEASE', simulation_authorized=True)
        with self.assertRaises(EvidenceError): validate_formal_authority(d)

    def test_authority_flag_alone_cannot_launch(self):
        d = copy.deepcopy(self.data); d.update(kind='AUTHORIZED_EXECUTION_LAUNCH_RELEASE', simulation_authorized=True,
            approved_runs=d['prepared_runs'], approved_run_ids=d['prepared_run_ids'])
        with self.assertRaises(EvidenceError): validate_formal_authority(d)

    def test_formal_authority_cannot_skip_B_seal(self):
        d = copy.deepcopy(self.data); d.update(kind='AUTHORIZED_EXECUTION_LAUNCH_RELEASE', simulation_authorized=True,
            approved_runs=d['prepared_runs'], approved_run_ids=d['prepared_run_ids'])
        # Hypothetical authorization is mocked, never written as a genuine record.
        recorded = dict(stage='S2_REG_GRID', formal_simulation_authorized=True,
                        approved_run_ids=d['prepared_run_ids'])
        with patch('stage_s2.explicit_authority', return_value=recorded), \
             patch('stage_s2.verify_zero_receipt') as zero:
            with self.assertRaises(EvidenceError): validate_formal_authority(d)
            zero.assert_not_called()

    def test_closed_preparation_execute_refused_without_any_output(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S2_') as temp:
            path = Path(temp)/'CLOSED_SOFTWARE_FIXTURE.json'; path.write_text(json.dumps(self.data))
            with patch.object(runner, 'native_process') as native:
                with self.assertRaises(EvidenceError): runner.execute(path, sha(path), self.data)
                native.assert_not_called()
            with patch.object(auditor, 'call_native') as native:
                with self.assertRaises(EvidenceError): auditor.execute(path, sha(path), self.data)
                native.assert_not_called()
            self.assertFalse((CASE/'launch_attempts').exists())
            self.assertFalse((CASE/'audit_attempts').exists())

    def test_wrong_external_preparation_SHA_rejected(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S2_') as temp:
            path = Path(temp)/'CLOSED.json'; path.write_text(json.dumps(self.data))
            with self.assertRaises(EvidenceError): verify_seal(path, '0'*64)

    def test_used_output_refused(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S2_') as temp:
            folder = Path(temp); (folder/'run_config.txt').write_text('')
            (folder/'run_manifest.txt').write_text(''); (folder/'run.log').write_text('synthetic')
            with self.assertRaises(EvidenceError): require_pristine([dict(output_directory=str(folder))])

    def test_formal_caps_by_grid(self):
        self.assertEqual([runner.wall_cap(r['run_config_path']) for r in self.data['prepared_runs']],
                         [3600, 3600, 14400, 14400, 43200, 43200])

    def test_no_B_seal_without_real_audit(self):
        # Exercise absence prerequisite without creating A or attempting a solver.
        with patch.object(prep, 'verify_zero_receipt') as verify, \
             patch('stage_s2.verify_seal', return_value=copy.deepcopy(self.data)):
            # finalize_zero requires A; currently absent or later real A, but zero is always absent.
            with self.assertRaises((EvidenceError, FileNotFoundError)): prep.finalize_zero()
            verify.assert_not_called()
        self.assertFalse((CASE/'evidence/preparation_B.json').exists())

    def pipeline(self, native_code=0, checker_code=0, accepted=True, drift=False):
        """Pure mocked controller exercise; no genuine authorization/zero evidence."""
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S2_PIPELINE_') as temp:
            folder = Path(temp); records = []
            for i in range(6):
                rid = 'SYNTHETIC_S2_'+str(i); run = folder/'runs'/rid/'steady'; run.mkdir(parents=True)
                (run/'run_config.txt').write_text(f'mode=steady\nrun_id={rid}\noutput_directory={run}\ndx_nm=5\n')
                (run/'run_manifest.txt').write_text(f'run_id={rid}\nmode=steady\n')
                records.append(dict(run_id=rid, planned_case_id='SYNTHETIC_CASE_'+str(i),
                    output_directory=str(run), run_config_path=str(run/'run_config.txt')))
            sentinel = folder/'SYNTHETIC_INPUT'; sentinel.write_text('unchanged')
            doc = dict(prepared_runs=records, inputs_sha256={str(sentinel): sha(sentinel)},
                       provenance=dict(native_binary='SOFTWARE_MOCK_ONLY_NOT_EXECUTABLE'))
            def native(*args):
                if drift: sentinel.write_text('changed')
                return dict(independent_process_exit_code=native_code, timed_out=False,
                            resource_stop_reason=None, elapsed_seconds=0.)
            def checked(argv, **kwargs):
                output = Path(argv[argv.index('--out')+1]); output.mkdir(parents=True)
                (output/'acceptance.json').write_text(json.dumps(dict(RESULT_PASS=accepted,
                    NUMERICAL_GATE='PASS', geometry_PASS=True, smooth=None,
                    fixture_label='SOFTWARE_MOCK_ONLY_NOT_SCIENTIFIC_EVIDENCE')))
                return types.SimpleNamespace(returncode=checker_code)
            with patch.object(runner, 'CASE', folder), patch.object(runner, 'binding', return_value=doc), \
                 patch.object(runner, 'validate_formal_authority'), patch.object(runner, 'resources', return_value={}), \
                 patch.object(runner, 'native_process', side_effect=native) as process, \
                 patch.object(runner.subprocess, 'run', side_effect=checked):
                failed = native_code != 0 or checker_code != 0 or not accepted or drift
                if failed:
                    with self.assertRaises(EvidenceError): runner.execute(Path('SYNTHETIC'), 'synthetic', doc)
                    self.assertEqual(process.call_count, 1)
                else:
                    runner.execute(Path('SYNTHETIC'), 'synthetic', doc)
                    self.assertEqual(process.call_count, 6)
                completed = folder/'launch_attempts/synthetic/S2_completed.json'
                self.assertEqual(completed.exists(), not failed)
                if completed.exists(): self.assertFalse(json.loads(completed.read_text())['next_stage_started'])

    def test_native_failure_prevents_next_case(self): self.pipeline(native_code=3)
    def test_checker_failure_prevents_next_case(self): self.pipeline(checker_code=2)
    def test_false_acceptance_prevents_next_case(self): self.pipeline(accepted=False)
    def test_input_drift_prevents_next_case(self): self.pipeline(drift=True)
    def test_mocked_six_success_accepts_groove_smooth_null_no_next_stage(self): self.pipeline()


if __name__ == '__main__':
    unittest.main(verbosity=2)
