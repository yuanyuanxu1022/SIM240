"""Authority, identity and isolation checks only; never call native/VTK programs."""
from pathlib import Path
import copy, importlib.util, json, os, sys, unittest
from unittest.mock import patch
CHECKER=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(CHECKER/'analysis'))
import tge_stage as s

class PreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bound=json.loads(Path(os.environ['TGE_TEST_DOCUMENT']).read_text())

    def test_valid_single_candidate_plan(self):
        self.assertEqual(len(s.validate_plan(self.bound)),3)

    def test_wrong_candidate_physics_refused(self):
        cfg=s.kv(self.bound['prepared_runs'][0]['run_config_path'])
        for key,value in [('direction','P'),('dx_nm','1.25'),('h_nm','60.0'),('acceleration_m_s2','200000'),
                          ('window_tstar','0.5'),('max_time_H_diffusion','4'),('frame_tstar','0,1')]:
            with self.subTest(key=key):
                bad=dict(cfg,**{key:value})
                with self.assertRaises(ValueError):s.physics(bad)

    def test_aliased_extra_physics_key_refused(self):
        cfg=s.kv(self.bound['prepared_runs'][0]['run_config_path']);cfg['restart']='old'
        with self.assertRaises(ValueError):s.physics(cfg)

    def test_extra_formal_identity_refused(self):
        b=copy.deepcopy(self.bound);b['prepared_runs']*=2
        with self.assertRaises(ValueError):s.validate_plan(b)

    def test_missing_or_reordered_zero_calls_refused(self):
        for key in ['missing','reordered']:
            b=copy.deepcopy(self.bound)
            if key=='missing':b['zero_prepared_runs'].pop()
            else:b['zero_prepared_runs'].reverse()
            with self.subTest(key=key),self.assertRaises(ValueError):s.validate_plan(b)

    def test_wrong_zero_identity_or_output_refused(self):
        for key,value in [('run_id','OLD_S4_ID'),('output_directory',str(s.PARENT)),('mode','steady'),
                          ('planned_case_id','URV1_U_THIN_T_dx1p25_a100000')]:
            b=copy.deepcopy(self.bound);b['zero_prepared_runs'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):s.validate_plan(b)

    def test_time_stepping_and_next_stage_flags_refused(self):
        for flag in [f for f in s.FLAGS if f not in ('native_zero_step_authorized','initial_field_readback_authorized')]:
            b=copy.deepcopy(self.bound);b[flag]=True
            with self.subTest(flag=flag),self.assertRaises(ValueError):s.validate_plan(b)

    def test_prospective_budgets_not_silently_adopted(self):
        for key in ['formal_solver_wall_cap_seconds','formal_checker_cap_seconds']:
            b=copy.deepcopy(self.bound);b[key]=43200
            with self.subTest(key=key),self.assertRaises(ValueError):s.validate_plan(b)

    def test_original_grid_and_failure_preserved(self):
        for key,value in [('original_grid_nm',[2.5,1.25,.625]),('original_S4_stage_accepted',True),
                          ('reference_qualified',True),('MODEL_COMPARISON','IMPROVED')]:
            b=copy.deepcopy(self.bound);b[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):s.validate_plan(b)

    def test_resource_increase_refused(self):
        b=copy.deepcopy(self.bound);b['zero_resource_proposal']['per_process_address_space_GiB']=16
        with self.assertRaises(ValueError):s.validate_plan(b)

    def test_reader_substitution_refused(self):
        b=copy.deepcopy(self.bound);b['reader_path']=b['provenance']['native_binary']
        with self.assertRaises(ValueError):s.validate_plan(b)

    def test_unexecuted_status_and_manual_boundary_refused(self):
        for key,value in [('NUMERICAL_GATE','PASS'),('RESULT_PASS',True),('geometry_PASS',True),
                          ('AI_may_start_solver',True),('user_manually_starts',False)]:
            b=copy.deepcopy(self.bound);b[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):s.validate_plan(b)

    def test_preparation_cannot_execute_and_writes_nothing(self):
        spec=importlib.util.spec_from_file_location('audit_zero_tge',s.CASE/'scripts/audit_zero_tge.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        before={str(p) for p in s.CASE.rglob('*')}
        with patch.object(module.subprocess,'Popen',side_effect=AssertionError('child process forbidden')) as child:
            with self.assertRaises(ValueError):module.execute(s.CASE/'evidence/preparation_A.json','0'*64,self.bound)
            self.assertFalse(child.called)
        self.assertEqual(before,{str(p) for p in s.CASE.rglob('*')})

    def test_hash_mismatch_refused_before_load(self):
        with self.assertRaises(ValueError):s.verify_seal(Path(os.environ['TGE_TEST_DOCUMENT']),'0'*64)

    def test_full_existing_history_and_pristine_plan(self):
        s.verify_history(self.bound);s.require_pristine(self.bound)

if __name__=='__main__':unittest.main(verbosity=2)
