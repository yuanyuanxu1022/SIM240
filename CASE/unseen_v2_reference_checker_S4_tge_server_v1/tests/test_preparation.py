"""Authority, identity and isolation checks only; never call native/VTK programs.

This is the server-lineage counterpart of the local 15-check suite.  The
concerns are the same, but the plan differs: two formal runs (the 1.25 nm
same-build baseline rerun and the 0.625 nm supplement) instead of one.
"""
from pathlib import Path
import copy, importlib.util, json, os, sys, unittest
from unittest.mock import patch

CHECKER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHECKER / 'analysis'))
import server_stage as s


class PreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bound = json.loads(Path(os.environ['TGE_TEST_DOCUMENT']).read_text())

    def test_valid_two_formal_and_three_zero_plan(self):
        self.assertEqual(len(s.validate_plan(self.bound)), 3)

    def test_wrong_candidate_physics_refused(self):
        cfg = s.kv(self.bound['prepared_runs'][1]['run_config_path'])
        for key, value in [('direction', 'P'), ('dx_nm', '0.3125'), ('h_nm', '60.0'),
                           ('acceleration_m_s2', '200000'), ('window_tstar', '0.5'),
                           ('max_time_H_diffusion', '4'), ('frame_tstar', '0,1')]:
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    s.physics(dict(cfg, **{key: value}))

    def test_aliased_extra_physics_key_refused(self):
        cfg = s.kv(self.bound['prepared_runs'][0]['run_config_path'])
        cfg['restart'] = 'old'
        with self.assertRaises(ValueError):
            s.physics(cfg)

    def test_extra_formal_identity_refused(self):
        bad = copy.deepcopy(self.bound)
        bad['prepared_runs'] += [copy.deepcopy(bad['prepared_runs'][0])]
        with self.assertRaises(ValueError):
            s.validate_plan(bad)
        bad = copy.deepcopy(self.bound)
        bad['prepared_runs'].pop()
        with self.assertRaises(ValueError):
            s.validate_plan(bad)

    def test_missing_or_reordered_zero_calls_refused(self):
        for key in ('missing', 'reordered'):
            bad = copy.deepcopy(self.bound)
            if key == 'missing':
                bad['zero_prepared_runs'].pop()
            else:
                bad['zero_prepared_runs'].reverse()
            with self.subTest(key=key), self.assertRaises(ValueError):
                s.validate_plan(bad)

    def test_wrong_zero_identity_or_output_refused(self):
        for key, value in [('run_id', 'OLD_S4_ID'),
                           ('output_directory', str(s.CASE / 'runs')),
                           ('mode', 'steady'),
                           ('planned_case_id', 'URV1_U_THIN_T_dx1p25_a100000')]:
            bad = copy.deepcopy(self.bound)
            bad['zero_prepared_runs'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                s.validate_plan(bad)

    def test_time_stepping_and_next_stage_flags_refused(self):
        for flag in [f for f in s.FLAGS
                     if f not in ('native_zero_step_authorized', 'initial_field_readback_authorized')]:
            bad = copy.deepcopy(self.bound)
            bad[flag] = True
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                s.validate_plan(bad)

    def test_prospective_budgets_not_silently_adopted(self):
        for key in ('formal_solver_wall_cap_seconds', 'formal_checker_cap_seconds'):
            bad = copy.deepcopy(self.bound)
            bad[key] = 172800
            with self.subTest(key=key), self.assertRaises(ValueError):
                s.validate_plan(bad)

    def test_original_grid_and_failure_preserved(self):
        for key, value in [('original_grid_nm', [2.5, 1.25, .625]),
                           ('original_S4_stage_accepted', True),
                           ('reference_qualified', True),
                           ('MODEL_COMPARISON', 'IMPROVED')]:
            bad = copy.deepcopy(self.bound)
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                s.validate_plan(bad)

    def test_resource_change_refused_in_preparation(self):
        for key, value in [('per_process_address_space_GiB', 128),
                           ('required_available_RAM_GiB', 40),
                           ('native_call_cap_seconds', 3600)]:
            bad = copy.deepcopy(self.bound)
            bad['zero_resource_proposal'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                s.validate_plan(bad)

    def test_reader_substitution_refused(self):
        bad = copy.deepcopy(self.bound)
        bad['reader_path'] = bad['provenance']['native_binary']
        with self.assertRaises(ValueError):
            s.validate_plan(bad)

    def test_unexecuted_status_and_manual_boundary_refused(self):
        for key, value in [('NUMERICAL_GATE', 'PASS'), ('RESULT_PASS', True),
                           ('geometry_PASS', True), ('AI_may_start_solver', True),
                           ('user_manually_starts', False)]:
            bad = copy.deepcopy(self.bound)
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                s.validate_plan(bad)

    def test_preparation_cannot_execute_and_writes_nothing(self):
        spec = importlib.util.spec_from_file_location(
            'audit_zero_server', s.CASE / 'scripts/audit_zero_server.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        before = {str(p) for p in s.CASE.rglob('*')}
        with patch.object(module.subprocess, 'Popen',
                          side_effect=AssertionError('child process forbidden')) as child:
            with self.assertRaises(ValueError):
                module.execute(s.CASE / 'evidence/preparation_S.json', '0' * 64, self.bound)
            self.assertFalse(child.called)
        self.assertEqual(before, {str(p) for p in s.CASE.rglob('*')})

    def test_hash_mismatch_refused_before_load(self):
        with self.assertRaises(ValueError):
            s.verify_seal(Path(os.environ['TGE_TEST_DOCUMENT']), '0' * 64)

    def test_full_existing_lineage_and_pristine_plan(self):
        s.verify_lineage(self.bound)
        s.require_pristine(self.bound)

    def test_formal_authority_rejects_preparation_seal(self):
        spec = importlib.util.spec_from_file_location(
            'run_formal_server', s.CASE / 'scripts/run_formal_server.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.assertRaises(ValueError):
            module.validate_formal_authority(self.bound)

    def test_formal_authority_requires_zero_authority_off(self):
        spec = importlib.util.spec_from_file_location(
            'run_formal_server', s.CASE / 'scripts/run_formal_server.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for key, value in [('native_zero_step_authorized', True),
                           ('initial_field_readback_authorized', True),
                           ('S5_authorized', True),
                           ('automatic_retry_authorized', True),
                           ('automatic_extension_authorized', True),
                           ('AI_may_start_solver', True),
                           ('original_S4_stage_accepted', True)]:
            fake = copy.deepcopy(self.bound)
            fake.update(kind='AUTHORIZED_S4_TGE_SERVER_FORMAL_RELEASE',
                        simulation_authorized=True, formal_simulation_authorized=True,
                        approved_run_ids=[self.bound['prepared_runs'][0]['run_id']],
                        approved_runs=[self.bound['prepared_runs'][0]],
                        actual_run_ids=[], formal_resources=dict(solver_wall_cap_seconds=21600),
                        NUMERICAL_GATE='NOT_EVALUATED', RESULT_PASS=False, geometry_PASS=None,
                        reference_qualified=False)
            fake[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                module.validate_formal_authority(fake)

    def test_build_equivalence_criterion_is_immutable(self):
        for mutate in [
                lambda b: b['lineage']['build_equivalence_criterion'].update(relative_tolerance=1e-2),
                lambda b: b['lineage']['build_equivalence_criterion'].update(reference_K_m3=1.0),
                lambda b: b['lineage']['build_equivalence_criterion'].update(
                    applies_to_run_id=s.RUN_0P625),
                lambda b: b['lineage']['build_equivalence_criterion'].update(
                    declared_before_measurement=False)]:
            bad = copy.deepcopy(self.bound)
            mutate(bad)
            with self.assertRaises(ValueError):
                s.verify_lineage(bad)

    def _formal_module(self):
        spec = importlib.util.spec_from_file_location(
            'run_formal_server', s.CASE / 'scripts/run_formal_server.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_subset_approval_is_accepted(self):
        """Approving one of the two prepared runs is legitimate and must pass."""
        module = self._formal_module()
        one = self.bound['prepared_runs'][0]
        fake = copy.deepcopy(self.bound)
        fake.update(approved_runs=[one], approved_run_ids=[one['run_id']])
        self.assertEqual([r['run_id'] for r in module.validate_approved_identities(fake)],
                         [one['run_id']])

    def test_approval_must_match_plan_exactly(self):
        module = self._formal_module()
        one, two = self.bound['prepared_runs'][0], self.bound['prepared_runs'][1]
        cases = {
            'empty': ([], []),
            'id_not_in_plan': ([dict(one, run_id='OTHER')], ['OTHER']),
            'ids_do_not_match_records': ([one], [two['run_id']]),
            'duplicate_record': ([one, dict(one)], [one['run_id'], one['run_id']]),
            'all_but_ids_empty': ([one], []),
        }
        for name, (runs, ids) in cases.items():
            fake = copy.deepcopy(self.bound)
            fake.update(approved_runs=runs, approved_run_ids=ids)
            with self.subTest(name=name), self.assertRaises(ValueError):
                module.validate_approved_identities(fake)

    def test_equivalence_needs_both_builds_in_plan(self):
        bad = copy.deepcopy(self.bound)
        bad['prepared_runs'] = [bad['prepared_runs'][1]]
        with self.assertRaises(ValueError):
            s.validate_plan(bad)


if __name__ == '__main__':
    unittest.main(verbosity=2)
