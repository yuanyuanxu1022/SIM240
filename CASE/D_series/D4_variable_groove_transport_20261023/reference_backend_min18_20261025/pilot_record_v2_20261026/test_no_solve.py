"""Meaningful control-flow/record tests using manual arrays and fake PETSc only."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
import uuid
import numpy as np
from common import HERE,ROOT,Rejected,SETTINGS,template,validate,read_json,verify_lock,write_json
from records import arrays
from readback import check,check_capture
from resources import MemoryGroup,hard_output_volume
from runner import run,synthetic
from solver import DiagnosticGMRES,_solve_core
from synthetic_child import fixture

EVIDENCE=HERE/'evidence'


class Vec:
    def __init__(self,a):self.data=np.asarray(a,dtype=float).copy()
    @property
    def array(self):return self.data
    def set(self,x):self.data[:]=x
    def copy(self):return Vec(self.data)
    def axpy(self,a,b):self.data+=a*b.data
    def norm(self):return np.linalg.norm(self.data)


def fake_system(mode):
    class Matrix:
        def createVecRight(self):return Vec(np.zeros(5))
        createVecLeft=createVecRight
        def mult(self,x,y):y.data[:]=x.data*np.array([1,1,0,0,0])
    class KSP:
        def create(self,**kw):
            if mode=='create_fail':raise RuntimeError('FAKE_KSP_CREATE_FAILED')
            return self
        def getPC(self):return self
        def __getattr__(self,k):
            if k.startswith('set'):return lambda *a,**kw:None
            raise AttributeError(k)
        def solve(self,b,x):
            if mode=='solve_fail':raise RuntimeError('FAKE_KSP_SOLVE_FAILED')
            x.data[:]=[1,0,2,2,2]
            if mode=='bad_residual':x.data[0]=2
        def getConvergedReason(self):return 2
        def getIterationNumber(self):return 1
        def getConvergenceHistory(self):return [1.,0.]
        def destroy(self):pass
    KSP.Type=types.SimpleNamespace(GMRES='gmres');KSP.NormType=None
    class Space:
        def sub(self,i):return self
        def collapse(self):return self,[np.array([2,3,4])]
        def tabulate_dof_coordinates(self):return np.array([[0,0,0],[1,0,0],[0,1,0]])
    class MPC:
        function_space=Space()
        def backsubstitution(self,x):
            if mode=='backsub_fail':raise RuntimeError('FAKE_BACKSUB_FAILED')
    pet=types.SimpleNamespace(KSP=KSP,PC=types.SimpleNamespace(Type=types.SimpleNamespace(NONE='none')),COMM_SELF=None)
    pet.KSP.NormType=types.SimpleNamespace(UNPRECONDITIONED='unpreconditioned')
    system=dict(matrix=Matrix(),rhs=Vec([1,0,0,0,0]),
        item=dict(plan={'planned_id':'SYNTHETIC_FAKE_KSP_NOT_PDE'},mpc=MPC(),space=Space(),
                  pressure={'nodal_area_weights':np.ones(3)}),matrix_csr_sha256='fixture',rhs_sha256_before_projection='fixture')
    return system,pet


class Tests(unittest.TestCase):
    def packet(self,name,root):
        w=root/'work';r=root/'records';w.mkdir(exist_ok=True);r.mkdir(exist_ok=True)
        c=template(w,r,'/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice')
        c['run_id']=name;c['work_dir']=str(w/name);c['record_dir']=str(r/name)
        from common import expected_argv,expected_environment
        c['argv']=expected_argv(c);c['environment']=expected_environment(c)
        return c

    def test_01_immutable_plan_and_default_denial(self):
        with tempfile.TemporaryDirectory() as temp:
            c=self.packet('denied',Path(temp));validate(c)
            self.assertFalse(c['physical_plan']['execution_authorized'])
            self.assertEqual(c['environment']['XDG_CONFIG_HOME'],str(Path(c['work_dir'])/'config'))
            with self.assertRaisesRegex(Rejected,'NOT_AUTHORIZED'):run(c)
            self.assertFalse(Path(c['work_dir']).exists());self.assertFalse(Path(c['record_dir']).exists())

    def test_02_binding_mutations(self):
        with tempfile.TemporaryDirectory() as temp:
            c=self.packet('binding',Path(temp))
            changes=[('work_dir',str(Path(temp)/'wrong')),('argv',['wrong']),('planned_id','B0MIN_FLAT_T_d5'),
                     ('source_lock_sha256','0'*64),('environment',{}),('solver_settings',{})]
            for key,value in changes:
                bad=copy.deepcopy(c);bad[key]=value
                with self.subTest(key=key),self.assertRaises((Rejected,KeyError)):validate(bad)
            bad=copy.deepcopy(c);bad['physical_plan']['mesh']['nx']=99
            with self.assertRaisesRegex(Rejected,'PHYSICAL_PLAN'):validate(bad)

    def test_03_missing_dependency_rejected(self):
        lock=read_json(HERE/'source_lock.json');lock['files'].pop(str(HERE/'worker.py'))
        with self.assertRaisesRegex(Rejected,'MANDATORY_DEPENDENCY'):verify_lock(lock)

    def test_04_duplicate_json_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'bad.json';p.write_text('{"x":1,"x":2}')
            with self.assertRaisesRegex(Rejected,'DUPLICATE'):read_json(p)

    def test_05_manual_array_independent_recomputation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);fixture(root)
            result=check(root);self.assertEqual(result['status'],'DIAGNOSTIC_READBACK_PASS')
            self.assertEqual(result['record_kind'],'SYNTHETIC_MANUAL_ARRAYS_NOT_PDE')
            # Re-hash an intentionally wrong x, so detection is numerical, not just SHA.
            p=root/'solution/algebraic_solution_before_backsub.npy';x=np.load(p);x[0]=1.5
            with p.open('wb') as out:np.save(out,x,allow_pickle=False)
            from common import sha
            m=read_json(root/'solution/manifest.json');m['files'][p.name]['sha256']=sha(p)
            (root/'solution/manifest.json').write_text(json.dumps(m))
            result=check(root);self.assertEqual(result['status'],'DIAGNOSTIC_READBACK_FAIL')
            self.assertAlmostEqual(result['metrics']['true_residual_after_projection'],.5)

    def test_06_file_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);fixture(root);(root/'system/csr_values.npy').write_bytes(b'broken')
            with self.assertRaisesRegex(ValueError,'HASH'):check(root)

    def test_07_fake_ksp_success_and_failure_stages(self):
        for mode,stage in [('success',None),('create_fail','KSP_CREATION'),('solve_fail','KSP_SOLVE'),
                           ('bad_residual','RESIDUAL_CHECK'),('backsub_fail','MPC_AND_PRESSURE_POSTPROCESS')]:
            system,pet=fake_system(mode);captured=[]
            sink=lambda *args:captured.append(args)
            if stage:
                with self.assertRaises(Exception):_solve_core(system,DiagnosticGMRES(**SETTINGS),sink,pet)
                self.assertEqual(captured[0][0],stage)
                if mode=='create_fail':self.assertIsNone(captured[0][2])
                if mode=='backsub_fail':np.testing.assert_array_equal(captured[0][2],[1,0,2,2,2])
            else:
                result=_solve_core(system,DiagnosticGMRES(**SETTINGS),sink,pet)
                self.assertFalse(captured);np.testing.assert_array_equal(result['pressure_zero_area_mean_P1'],np.zeros(3))

    def test_08_ordinary_disk_cannot_replace_hard_output_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,'CAPPED_TMPFS'):hard_output_volume(Path(temp),512*1024**2)

    def test_09_direct_worker_denies_before_backend(self):
        from worker import handshake
        with tempfile.TemporaryDirectory() as temp:
            c=self.packet('direct',Path(temp));record=Path(c['record_dir']);record.mkdir()
            write_json(record/'contract.json',c)
            with self.assertRaisesRegex(Rejected,'NOT_AUTHORIZED'):handshake(record)

    def test_10_real_public_solver_gate_denied(self):
        from solver import solve_prepared_mixed_system
        with tempfile.TemporaryDirectory() as temp:
            c=self.packet('solvergate',Path(temp))
            with self.assertRaisesRegex(Rejected,'NOT_AUTHORIZED'):
                solve_prepared_mixed_system({},DiagnosticGMRES(**SETTINGS),c,lambda *a:None)

    def test_11_process_success_failure_timeout_output(self):
        root=EVIDENCE/('process_'+uuid.uuid4().hex[:10]);root.mkdir()
        limits=dict(wall_seconds=5,grace_seconds=.1,memory_bytes=512*1024**2,output_bytes=8*1024**2)
        saved=[]
        for mode in ('success','failure','sleep','output'):
            c=self.packet(mode,root);current=limits.copy()
            if mode=='sleep':current['wall_seconds']=.4
            if mode=='output':current['output_bytes']=100*1024
            m=synthetic(c,mode,limits=current);saved.append(c['record_dir'])
            self.assertTrue(m['inputs_unchanged'])
            if mode=='success':
                self.assertEqual(m['independent_exit_code'],0)
                self.assertEqual(check(Path(c['work_dir']))['status'],'DIAGNOSTIC_READBACK_PASS')
                self.assertEqual(check_capture(Path(c['record_dir']),Path(c['work_dir']))['status'],'CAPTURE_BINDING_PASS')
                # Parent and worker output bindings are checked independently.
                (Path(c['work_dir'])/'unlisted.txt').write_text('tamper')
                with self.assertRaisesRegex(ValueError,'INVENTORY'):check_capture(Path(c['record_dir']),Path(c['work_dir']))
                (Path(c['work_dir'])/'unlisted.txt').unlink()
            elif mode=='failure':
                self.assertEqual(m['independent_exit_code'],7);self.assertIn('partial.bin',m['work_files'])
            else:self.assertIn(m['stop_reason'],{'WALL_TIMEOUT','SAMPLED_OUTPUT_EXCEEDED'})
            if mode=='sleep':
                child=int((Path(c['work_dir'])/'descendant_pid.txt').read_text())
                status=Path(f'/proc/{child}/status')
                if status.exists():self.assertIn('State:\tZ',status.read_text())
            with self.assertRaises(FileExistsError):synthetic(c,mode,limits=current)
        write_json(root/'fixture_index.json',dict(record_dirs=saved,kind='SYNTHETIC_ONLY'))

    def test_12_cgroup_memory_oom_short_fixture(self):
        parent=Path('/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice')
        root=EVIDENCE/('memory_'+uuid.uuid4().hex[:10]);root.mkdir()
        try:group=MemoryGroup(parent,'sim240-test-'+uuid.uuid4().hex[:10],64*1024**2)
        except (OSError,ValueError) as e:
            write_json(root/'unavailable.json',{'reason':repr(e)});self.skipTest('delegated memory unavailable: '+str(e))
        try:
            c=self.packet('oom',root)
            result=synthetic(c,'memory',limits=dict(wall_seconds=5,grace_seconds=.1,memory_bytes=512*1024**2,output_bytes=8*1024**2),group=group)
            self.assertNotEqual(result['independent_exit_code'],0)
            events=dict(line.split() for line in result['cgroup_stats']['memory.events'].splitlines())
            self.assertGreater(int(events['oom_kill']),0)
            self.assertEqual(result['stop_reason'],'CGROUP_MEMORY_OOM')
            write_json(root/'memory_test.json',dict(status='KERNEL_OOM_RECORDED',result=result))
        finally:group.close()

    def test_13_fake_ksp_failure_vector_archived_on_disk(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('fixture_failure_archive',ROOT/'execution_record_review_20261026/failure_archive.py')
        archive=importlib.util.module_from_spec(spec);spec.loader.exec_module(archive)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);system,pet=fake_system('backsub_fail')
            def sink(stage,error,vector,diagnostics,binding):
                archive.save_failure(root,'fake_ksp_not_pde',stage,error,vector,diagnostics,binding)
            with self.assertRaisesRegex(RuntimeError,'FAKE_BACKSUB_FAILED'):
                _solve_core(system,DiagnosticGMRES(**SETTINGS),sink,pet)
            saved=np.load(root/'fake_ksp_not_pde/partial_algebraic_solution_before_backsub.npy')
            np.testing.assert_array_equal(saved,[1,0,2,2,2])
            m=read_json(root/'fake_ksp_not_pde/failure_manifest.json')
            self.assertEqual(m['failure_stage'],'MPC_AND_PRESSURE_POSTPROCESS')
            self.assertFalse(m['RESULT_PASS'])

    def test_14_snapshot_error_preserves_original_exception(self):
        system,pet=fake_system('solve_fail');old_matrix=system['matrix']
        class BrokenVector(Vec):
            @property
            def array(self):raise RuntimeError('FAKE_VECTOR_READ_FAILURE')
        old_matrix.createVecRight=lambda:BrokenVector(np.zeros(5))
        captured=[]
        with self.assertRaisesRegex(RuntimeError,'FAKE_KSP_SOLVE_FAILED'):
            _solve_core(system,DiagnosticGMRES(**SETTINGS),lambda *a:captured.append(a),pet)
        self.assertIsNone(captured[0][2]);self.assertIn('FAKE_VECTOR_READ_FAILURE',captured[0][3]['snapshot_error'])

    def test_15_p2_midpoints_and_p1_cell_mapping(self):
        from readback import check_cell_maps
        vertices=np.array([[0.,0.],[1.,0.],[0.,1.]])
        nodes=np.vstack([vertices,[.5,0],[0,.5],[.5,.5]])
        raw=dict(mesh_coordinates_hat=vertices,mesh_triangles=np.array([[0,1,2]],dtype=np.int64),
                 velocity_dof_coordinates_hat=np.repeat(nodes,2,axis=0),
                 velocity_dof_components=np.tile([0,1],6),velocity_reconstructed_dof_indices=np.arange(12),
                 pressure_coordinates_hat=vertices,pressure_reconstructed_dof_indices=np.arange(12,15))
        system=dict(cell_velocity_mixed_dofs=np.arange(12).reshape(1,12),cell_pressure_mixed_dofs=np.arange(12,15).reshape(1,3))
        check_cell_maps(system,raw)
        raw['velocity_dof_coordinates_hat'][6]=[.4,0]
        with self.assertRaisesRegex(ValueError,'CELL_ELEMENT'):check_cell_maps(system,raw)

    def test_16_full_work_volume_preserves_original_failure(self):
        from worker import archive_failure
        class FullArchive:
            def save_failure(self,*a,**k):raise OSError(28,'SYNTHETIC_NO_SPACE_LEFT')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);record=root/'record';record.mkdir();work=root/'work';work.mkdir()
            c=self.packet('archivefull',root)
            with self.assertRaisesRegex(RuntimeError,'ORIGINAL_FAKE_SOLVER_FAILURE'):
                archive_failure(FullArchive(),record,work,c,'KSP_SOLVE',
                    RuntimeError('ORIGINAL_FAKE_SOLVER_FAILURE'),None,{}, {})
            saved=read_json(record/'failure_archive_error.json')
            self.assertIn('ORIGINAL_FAKE_SOLVER_FAILURE',saved['original_exception'])
            self.assertIn('NO_SPACE_LEFT',saved['archive_exception'])
            self.assertFalse(saved['RESULT_PASS'])


if __name__=='__main__':
    EVIDENCE.mkdir(exist_ok=True)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    forbidden=[name for name in sys.modules if name=='petsc4py' or name.startswith(('petsc4py.','dolfinx.','dolfinx_mpc.'))]
    summary=dict(status='PASS_NO_PDE_TESTS' if result.wasSuccessful() and not forbidden else 'FAIL',
        tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=[str(x[1]) for x in result.skipped],
        forbidden_backend_modules_loaded=forbidden,real_KSP_created=False,real_PDE_solved=False,
        NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None)
    write_json(EVIDENCE/'test_summary.json',summary)
    raise SystemExit(0 if summary['status']=='PASS_NO_PDE_TESTS' else 1)
