"""Targeted type-dispatch rejection tests; no PDE or process fixtures."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import common
from common import HERE,ROOT,read_json,sha,write_json
import readback
from synthetic_child import fixture

OLD=ROOT/'pilot_record_v3_20261026'
OFFLINE=max((OLD/'evidence').glob('offline_*/offline_check.json'),key=lambda p:p.stat().st_mtime_ns)
RECORD=Path(read_json(OFFLINE)['record_dir']);ARCHIVE=RECORD/'archive'
OBSERVED=[]


def override_json(changes):
    original=readback.load_json
    def read(path):
        value=original(path)
        for target,change in changes:
            if Path(path)==Path(target):value=copy.deepcopy(value);change(value)
        return value
    return patch.object(readback,'load_json',side_effect=read)


def set_kind(path,kind):
    value=read_json(path);value['metadata']['record_kind']=kind
    path.write_text(json.dumps(value)+'\n')


class Tests(unittest.TestCase):
    def test_01_two_allowed_mappings(self):
        for parent,array in readback.ARRAY_KIND_BY_PARENT.items():
            self.assertEqual(readback.validate_record_kinds({'kind':parent},{'kind':parent},
                {'record_kind':array},{'record_kind':array}),parent)
        self.assertFalse(read_json(HERE/'contract_template.json')['authorized_to_execute'])

    def test_02_unknown_missing_parent_kinds_before_dispatch(self):
        for name in ('STARTED.json','capture_manifest.json'):
            for mode in ('unknown','missing'):
                def change(d):
                    if mode=='unknown':d['kind']='UNKNOWN_REVIEW_INJECTION'
                    else:d.pop('kind')
                with self.subTest(name=name,mode=mode),override_json([(RECORD/name,change)]):
                    with self.assertRaisesRegex(ValueError,'PARENT_RECORD_KIND'):
                        readback.check_capture(RECORD,ARCHIVE)

    def test_03_parent_labels_must_match(self):
        with override_json([(RECORD/'capture_manifest.json',lambda d:d.update(kind='REAL_DIAGNOSTIC_UNVERIFIED'))]):
            with self.assertRaisesRegex(ValueError,'PARENT_RECORD_KIND'):readback.check_capture(RECORD,ARCHIVE)

    def test_04_unknown_missing_array_kinds(self):
        for name in ('system','solution'):
            for mode in ('unknown','missing'):
                with tempfile.TemporaryDirectory() as temp:
                    work=Path(temp);fixture(work);path=work/name/'manifest.json';m=read_json(path)
                    if mode=='unknown':m['metadata']['record_kind']='UNKNOWN_ARRAY'
                    else:m['metadata'].pop('record_kind')
                    path.write_text(json.dumps(m))
                    with self.subTest(name=name,mode=mode),self.assertRaisesRegex(ValueError,'ARRAY_RECORD_KIND'):
                        readback.check(work)

    def test_05_system_solution_labels_must_match(self):
        with tempfile.TemporaryDirectory() as temp:
            work=Path(temp);fixture(work);set_kind(work/'system/manifest.json','REAL_DIAGNOSTIC_UNVERIFIED')
            with self.assertRaisesRegex(ValueError,'ARRAY_RECORD_KIND'):readback.check(work)

    def test_06_parent_array_cross_labels_rejected(self):
        changes=[(ARCHIVE/name/'manifest.json',lambda d:d['metadata'].update(record_kind='REAL_DIAGNOSTIC_UNVERIFIED'))
                 for name in ('system','solution')]
        with override_json(changes):
            with self.assertRaisesRegex(ValueError,'PARENT_ARRAY_RECORD_KIND'):readback.check_capture(RECORD,ARCHIVE)
        # Also exercise the reverse correspondence without fabricating a run or approval.
        with self.assertRaisesRegex(ValueError,'PARENT_ARRAY_RECORD_KIND'):
            readback.validate_record_kinds({'kind':'REAL_DIAGNOSTIC_UNVERIFIED'},
                {'kind':'REAL_DIAGNOSTIC_UNVERIFIED'},
                {'record_kind':'SYNTHETIC_MANUAL_ARRAYS_NOT_PDE'},
                {'record_kind':'SYNTHETIC_MANUAL_ARRAYS_NOT_PDE'})

    def test_07_archive_only_checks_known_matching_parent_type(self):
        for both in (False,True):
            changes=[(RECORD/'capture_manifest.json',lambda d:d.update(kind='UNKNOWN_REVIEW_INJECTION'))]
            if both:changes.append((RECORD/'STARTED.json',lambda d:d.update(kind='UNKNOWN_REVIEW_INJECTION')))
            with self.subTest(both=both),override_json(changes):
                with self.assertRaisesRegex(ValueError,'PARENT_RECORD_KIND'):readback.check_archive(RECORD)

    def test_08_real_arrays_without_parent_rejected_by_cli(self):
        with tempfile.TemporaryDirectory() as temp:
            work=Path(temp);fixture(work)
            for name in ('system','solution'):set_kind(work/name/'manifest.json','REAL_DIAGNOSTIC_UNVERIFIED')
            # Real labels on manual arrays are rejection input, not a real result.
            with self.assertRaisesRegex(ValueError,'REAL_RECORD_REQUIRES_INDEPENDENT_PARENT_CAPTURE'):
                readback.check(work)
            p=subprocess.run([sys.executable,'-B',str(HERE/'readback.py'),str(work)],capture_output=True,text=True,timeout=10)
            self.assertNotEqual(p.returncode,0)
            self.assertIn('REAL_RECORD_REQUIRES_INDEPENDENT_PARENT_CAPTURE',p.stderr)
            self.assertNotIn('DIAGNOSTIC_READBACK_PASS',p.stdout)

    def test_09_legal_synthetic_saved_capture_and_partial_archives(self):
        self.assertEqual(readback.check(ARCHIVE)['status'],'DIAGNOSTIC_READBACK_PASS')
        self.assertEqual(readback.check_capture(RECORD,ARCHIVE)['status'],'CAPTURE_BINDING_PASS')
        saved=[]
        for path in (OLD/'evidence').rglob('capture_manifest.json'):
            if read_json(path).get('archive_status')=='ARCHIVE_COMPLETE':
                result=readback.check_archive(path.parent)
                self.assertFalse(result['RESULT_PASS']);saved.append(result)
        self.assertGreaterEqual(len(saved),6)
        self.assertTrue(any(x['independent_exit_code']==7 for x in saved))
        self.assertTrue(any(x['stopped_reason']=='CGROUP_MEMORY_OOM' for x in saved))
        OBSERVED.append({'case':'saved_synthetic_archives','count':len(saved),'new_processes_started':False})

    def test_10_default_and_public_real_gate_still_denied(self):
        from runner import run
        from solver import solve_prepared_mixed_system,DiagnosticGMRES
        c=read_json(HERE/'contract_template.json');common.validate(c)
        self.assertFalse(c['physical_plan']['execution_authorized'])
        for call in (lambda:run(c),lambda:solve_prepared_mixed_system({},DiagnosticGMRES(**common.SETTINGS),c,lambda *a:None)):
            with self.assertRaisesRegex(common.Rejected,'NOT_AUTHORIZED'):call()
        self.assertFalse(Path(c['work_dir']).exists());self.assertFalse(Path(c['record_dir']).exists())

    def test_11_original_review_counterexample_now_rejected(self):
        spec=importlib.util.spec_from_file_location('unchanged_v3_readback',OLD/'readback.py')
        old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        prior=old.load_json
        def inject(path):
            obj=prior(path)
            if Path(path)==RECORD/'capture_manifest.json':obj['kind']='UNKNOWN_REVIEW_INJECTION'
            return obj
        with patch.object(old,'load_json',side_effect=inject):
            before=old.check_capture(RECORD,ARCHIVE)
        with override_json([(RECORD/'capture_manifest.json',lambda d:d.update(kind='UNKNOWN_REVIEW_INJECTION'))]):
            with self.assertRaisesRegex(ValueError,'PARENT_RECORD_KIND') as caught:
                readback.check_capture(RECORD,ARCHIVE)
        self.assertEqual(before['status'],'CAPTURE_BINDING_PASS')
        OBSERVED.append({'case':'same_review_counterexample','v3':before,'v3_1':'REJECTED:'+str(caught.exception),
                         'original_files_changed':False,'real_run_or_approval_created':False})

    def test_12_numerical_reconstruction_check_still_active(self):
        with tempfile.TemporaryDirectory() as temp:
            work=Path(temp);fixture(work)
            for name in ('reconstructed_solution','velocity_reconstructed_values'):
                path=work/'solution'/(name+'.npy');a=np.load(path);a[0]=7.
                with path.open('wb') as f:np.save(f,a,allow_pickle=False)
                m=read_json(path.parent/'manifest.json');m['files'][path.name]['sha256']=sha(path)
                (path.parent/'manifest.json').write_text(json.dumps(m))
            r=readback.check(work);self.assertEqual(r['status'],'DIAGNOSTIC_READBACK_FAIL')
            self.assertAlmostEqual(r['metrics']['reconstruction_relative'],6.)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    forbidden=[k for k in sys.modules if k.split('.')[0] in {'petsc4py','dolfinx','dolfinx_mpc','ufl'}]
    report=dict(status='PASS_TARGETED_NO_SOLVE_TESTS' if result.wasSuccessful() and not forbidden else 'FAIL',
        tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),
        forbidden_backend_modules_loaded=forbidden,real_solver_called=False,real_KSP_created=False,
        new_process_fixtures_started=False,approved_packet_created=False,observed=OBSERVED,
        NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None)
    write_json(HERE/'evidence/test_summary.json',report)
    raise SystemExit(0 if report['status']=='PASS_TARGETED_NO_SOLVE_TESTS' else 1)
