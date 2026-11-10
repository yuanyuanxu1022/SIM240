"""v3 rejection/archival tests. Manual arrays and fixed short processes only."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock
import uuid
import numpy as np
import test_legacy_no_solve as legacy
from common import HERE,ROOT,SETTINGS,sha,digest,read_json,write_json
from synthetic_child import fixture
from readback import check,check_capture,check_required_records
from runner import synthetic,capture_succeeded
from archive import archive_stopped_work


def alter_array(root,name,change):
    p=root/'solution'/(name+'.npy');a=np.load(p,allow_pickle=False);change(a)
    with p.open('wb') as f:np.save(f,a,allow_pickle=False)
    m=read_json(p.parent/'manifest.json');m['files'][p.name]['sha256']=sha(p)
    (p.parent/'manifest.json').write_text(json.dumps(m)+'\n')


def saved_schema_fixture(owner,root):
    """Synthetic RECORD SCHEMA fixture only: no approved packet or PDE output."""
    c=owner.packet('synthetic_record_schema',root)
    record,work=Path(c['record_dir']),Path(c['work_dir']);record.mkdir();work.mkdir();fixture(work)
    for name in ('stdout.log','stderr.log'):(work/name).write_text('SYNTHETIC_SCHEMA_NOT_PDE\n')
    lock=read_json(HERE/'source_lock.json');write_json(record/'source_lock.json',lock)
    source=ROOT/'solve_entry_review_20261025/evidence/preflight_all9.json'
    shutil.copyfile(source,record/'assembly_preflight.json')
    pre=next(r['preflight'] for r in read_json(source)['records'] if r['planned_id']==c['planned_id'])
    write_json(work/'solver_diagnostics.json',dict(ksp_type='gmres',pc_type='none',ksp_reason=2,
        ksp_iterations=1,ksp_reported_residual_history=[1.,0.],true_unpreconditioned_relative_residual=0.,**SETTINGS))
    write_json(work/'runtime_environment.json',dict(python='SYNTHETIC_SCHEMA_NOT_PDE',executable=c['argv'][0],
        executable_sha256=lock['files'][str(Path(c['argv'][0]).resolve())],environment=c['environment'],
        versions={'fenics-dolfinx':'0.11.0','fenics-basix':'0.11.0','fenics-ffcx':'0.11.0',
                  'petsc4py':'3.25.6','dolfinx_mpc':'0.11.0','numpy':'2.5.4','mpi4py':'4.1.2'}))
    write_json(work/'worker_completion.json',dict(status='SOLVER_EXITED_UNVERIFIED',run_id=c['run_id'],
        contract_sha256=digest(c),NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None))
    (work/'stages.jsonl').write_text(''.join(json.dumps({'stage':name})+'\n' for name in ('ASSEMBLY','SOLVER','RESULT_RECORD')))
    f=work/'system/manifest.json';m=read_json(f)
    m['metadata'].update(physical_plan=c['physical_plan'],mesh_stats={'periodic_link_audit':{'pairs':[{'slave_dof':2,'master_dof':3,'coefficient':1.}]}},
        matrix_csr_sha256=pre['matrix_csr_sha256'],rhs_sha256_before_projection=pre['rhs_sha256_before_projection'])
    f.write_text(json.dumps(m)+'\n')
    started=dict(inputs_sha256_before=lock['files'],resource_before=dict(MemAvailable_bytes=8*1024**3,
        work_volume=dict(mechanism='preexisting_dedicated_tmpfs',capacity_bytes=512*1024**2),
        record_volume=dict(identity={'filesystem':'ext4'},available_bytes=3*1024**3)))
    capture=dict(work_files={str(p.relative_to(work)):{} for p in work.rglob('*') if p.is_file()},
        memory_enforcement='cgroup_v2_memory.max',wall_seconds=.1,sampled_output_peak_bytes=1000,
        cgroup_stats={'memory.max':str(4*1024**3),'memory.events':'oom_kill 0\n','cgroup.events':'populated 0\n'})
    return c,record,work,started,capture


class Tests(legacy.Tests):
    def test_17_original_counterexample_now_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root)
            alter_array(root,'reconstructed_solution',lambda a:a.__setitem__(0,7.))
            alter_array(root,'velocity_reconstructed_values',lambda a:a.__setitem__(0,7.))
            r=check(root);self.assertEqual(r['status'],'DIAGNOSTIC_READBACK_FAIL')
            self.assertAlmostEqual(r['metrics']['reconstruction_relative'],6.)

    def test_18_periodic_reconstruction_not_equal_raw_slave(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root)
            alter_array(root,'algebraic_solution_before_backsub',lambda a:a.__setitem__(2,0.))
            self.assertEqual(check(root)['status'],'DIAGNOSTIC_READBACK_PASS')
            alter_array(root,'reconstructed_solution',lambda a:a.__setitem__(2,4.))
            alter_array(root,'pressure_raw_P1',lambda a:a.__setitem__(0,4.))
            self.assertEqual(check(root)['status'],'DIAGNOSTIC_READBACK_FAIL')

    def test_19_pressure_shift_and_coefficient_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root)
            alter_array(root,'pressure_zero_mean_P1',lambda a:a.__iadd__(.1))
            self.assertEqual(check(root)['status'],'DIAGNOSTIC_READBACK_FAIL')
            alter_array(root,'periodic_coefficients',lambda a:a.__setitem__(0,.5))
            with self.assertRaisesRegex(ValueError,'UNIT_PERIODIC'):check(root)

    def test_20_offline_archive_after_source_removed(self):
        root=HERE/'evidence'/('offline_'+uuid.uuid4().hex[:10]);root.mkdir()
        c=self.packet('success',root);m=synthetic(c,'success')
        self.assertTrue(capture_succeeded(m));work=Path(c['work_dir']);record=Path(c['record_dir'])
        shutil.rmtree(work)  # Synthetic source only; production never deletes source.
        self.assertEqual(check(record/'archive')['status'],'DIAGNOSTIC_READBACK_PASS')
        self.assertEqual(check_capture(record,record/'archive')['status'],'CAPTURE_BINDING_PASS')
        write_json(root/'offline_check.json',{'kind':'SYNTHETIC_ONLY','status':'PASS_ARCHIVE_WITHOUT_SOURCE','record_dir':str(record)})

    def test_21_archive_copy_failure_preserves_source_exit_and_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c=self.packet('failure',root)
            with mock.patch('archive.shutil.copyfileobj',side_effect=OSError(28,'SYNTHETIC_ARCHIVE_FULL')):
                m=synthetic(c,'failure')
            record,work=Path(c['record_dir']),Path(c['work_dir'])
            self.assertEqual(m['independent_exit_code'],7);self.assertFalse(capture_succeeded(m))
            self.assertEqual(m['archive_status'],'ARCHIVE_INCOMPLETE')
            self.assertTrue((work/'partial.bin').exists());self.assertTrue((record/'archive.incomplete').exists())
            self.assertFalse((record/'archive_manifest.json').exists())
            self.assertIn('ARCHIVE_FULL',read_json(record/'archive_failure.json')['original_archive_exception'])

    def test_22_archive_fsync_failure_not_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c=self.packet('fsync',root);work,record=Path(c['work_dir']),Path(c['record_dir'])
            work.mkdir();record.mkdir();(work/'partial').write_bytes(b'preserve')
            with mock.patch('archive.os.fsync',side_effect=OSError(5,'SYNTHETIC_FSYNC_FAILED')):
                with self.assertRaises(Exception):archive_stopped_work(work,record,c,children_stopped=True,independent_exit_code=-9)
            self.assertTrue((work/'partial').exists());self.assertFalse((record/'archive_manifest.json').exists())

    def test_23_archive_checks_stopped_writers_and_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c=self.packet('links',root);work,record=Path(c['work_dir']),Path(c['record_dir'])
            work.mkdir();record.mkdir();(work/'bad').symlink_to('/etc/hosts')
            with self.assertRaisesRegex(ValueError,'STOPPED'):archive_stopped_work(work,record,c,children_stopped=False,independent_exit_code=0)
            with self.assertRaisesRegex(ValueError,'SYMLINK'):archive_stopped_work(work,record,c,children_stopped=True,independent_exit_code=0)
            self.assertFalse((record/'archive_manifest.json').exists())

    def test_24_required_record_schema_success_and_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            c,record,work,s,m=saved_schema_fixture(self,Path(tmp));r=check(work)
            self.assertEqual(check_required_records(record,work,c,s,m,r)['status'],'REQUIRED_RECORD_SCHEMA_PASS')
            for name in ('solver_diagnostics.json','runtime_environment.json','stages.jsonl','worker_completion.json'):
                with self.subTest(missing=name):
                    saved=(work/name).read_bytes();(work/name).unlink()
                    with self.assertRaisesRegex(ValueError,'REQUIRED_RECORD'):check_required_records(record,work,c,s,m,r)
                    (work/name).write_bytes(saved)

    def test_25_contradictory_solver_records_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            c,record,work,s,m=saved_schema_fixture(self,Path(tmp));r=check(work)
            path=work/'solver_diagnostics.json';original=read_json(path)
            for key,value in [('ksp_reason',-3),('ksp_iterations',2001),('restart',25),
                              ('ksp_rtol',1e-8),('true_unpreconditioned_relative_residual',1e-5)]:
                bad=copy.deepcopy(original);bad[key]=value;path.write_text(json.dumps(bad))
                with self.subTest(key=key),self.assertRaises(ValueError):check_required_records(record,work,c,s,m,r)

    def test_26_environment_stage_resource_map_contradictions(self):
        with tempfile.TemporaryDirectory() as tmp:
            c,record,work,s,m=saved_schema_fixture(self,Path(tmp));r=check(work)
            for name,change in [('runtime_environment.json',lambda d:d['environment'].update(OMP_NUM_THREADS='2')),
                                 ('runtime_environment.json',lambda d:d['versions'].update(numpy='0'))]:
                path=work/name;original=path.read_bytes();d=read_json(path);change(d);path.write_text(json.dumps(d))
                with self.assertRaisesRegex(ValueError,'ENVIRONMENT|VERSIONS'):check_required_records(record,work,c,s,m,r)
                path.write_bytes(original)
            path=work/'stages.jsonl';original=path.read_bytes();path.write_text('{"stage":"SOLVER"}\n')
            with self.assertRaisesRegex(ValueError,'STAGE'):check_required_records(record,work,c,s,m,r)
            path.write_bytes(original)
            bad=copy.deepcopy(m);bad['cgroup_stats']['memory.events']='oom_kill 1\n'
            with self.assertRaisesRegex(ValueError,'CGROUP'):check_required_records(record,work,c,s,bad,r)
            bad=copy.deepcopy(s);bad['resource_before']['record_volume']['identity']['filesystem']='tmpfs'
            with self.assertRaisesRegex(ValueError,'RESOURCE'):check_required_records(record,work,c,bad,m,r)
            path=work/'system/manifest.json';d=read_json(path);d['metadata']['mesh_stats']['periodic_link_audit']['pairs'][0]['master_dof']=4;path.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,'PERIODIC_MAP'):check_required_records(record,work,c,s,m,r)

    def test_27_record_failure_cannot_return_success(self):
        good=dict(independent_exit_code=0,children_stopped=True,inputs_unchanged=True,archive_status='ARCHIVE_COMPLETE')
        self.assertTrue(capture_succeeded(good))
        for key in ('inventory_error','supervisor_error','archive_error','stop_cleanup_error','stop_reason'):
            self.assertFalse(capture_succeeded({**good,key:'SYNTHETIC_FAILURE'}))

    def test_28_archive_hash_tamper_and_path_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=self.packet('tamper',Path(tmp));synthetic(c,'success');record=Path(c['record_dir']);archive=record/'archive'
            self.assertEqual(check_capture(record,archive)['status'],'CAPTURE_BINDING_PASS')
            (archive/'stdout.log').write_text('tampered')
            with self.assertRaisesRegex(ValueError,'INVENTORY'):check_capture(record,archive)

    def test_29_durable_volume_requires_separate_filesystem(self):
        from resources import durable_record_volume
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'SEPARATE_PERSISTENT'):durable_record_volume(tmp,tmp,1)

    def test_30_zero_child_exit_archive_failure_is_not_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=self.packet('success_archive_fail',Path(tmp))
            with mock.patch('archive.shutil.copyfileobj',side_effect=OSError(28,'SYNTHETIC_ARCHIVE_FULL')):
                m=synthetic(c,'success')
            self.assertEqual(m['independent_exit_code'],0);self.assertFalse(capture_succeeded(m))
            self.assertEqual((Path(c['record_dir'])/'independent_exit_code.txt').read_text(),'0\n')
            self.assertEqual(m['archive_status'],'ARCHIVE_INCOMPLETE')

    def test_31_all_saved_process_archives_independent_integrity(self):
        from readback import check_archive
        records=list((HERE/'evidence').glob('process_*/records/*/capture_manifest.json'))
        records+=list((HERE/'evidence').glob('memory_*/records/*/capture_manifest.json'))
        self.assertGreaterEqual(len(records),5)
        reasons=[]
        for path in records:
            r=check_archive(path.parent);self.assertEqual(r['status'],'ARCHIVE_INTEGRITY_PASS')
            self.assertFalse(r['RESULT_PASS']);reasons.append(r['stopped_reason'])
        self.assertIn('CGROUP_MEMORY_OOM',reasons);self.assertIn('WALL_TIMEOUT',reasons)

    def test_32_failure_publishing_complete_marker_is_rejected(self):
        import archive
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c=self.packet('publish_failure',root);work,record=Path(c['work_dir']),Path(c['record_dir'])
            work.mkdir();record.mkdir();(work/'raw').write_bytes(b'keep')
            original=archive.sync_dir
            def faulty(path):
                if (record/'archive_manifest.json').exists():raise OSError(5,'SYNTHETIC_PUBLISH_SYNC_FAILURE')
                return original(path)
            with mock.patch('archive.sync_dir',side_effect=faulty):
                with self.assertRaisesRegex(OSError,'PUBLISH_SYNC'):archive_stopped_work(work,record,c,children_stopped=True,independent_exit_code=0)
            self.assertFalse((record/'archive_manifest.json').exists());self.assertTrue((work/'raw').exists())
            self.assertIn('PUBLISH_SYNC',read_json(record/'archive_failure.json')['original_archive_exception'])


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    forbidden=[k for k in sys.modules if k.split('.')[0] in {'petsc4py','dolfinx','dolfinx_mpc','ufl'}]
    out=dict(status='PASS_NO_PDE_TESTS' if result.wasSuccessful() and not forbidden else 'FAIL',
        tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=[str(x[1]) for x in result.skipped],
        forbidden_backend_modules_loaded=forbidden,real_KSP_created=False,real_PDE_solved=False,
        NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None)
    write_json(HERE/'evidence/test_summary.json',out)
    raise SystemExit(0 if out['status']=='PASS_NO_PDE_TESTS' else 1)
