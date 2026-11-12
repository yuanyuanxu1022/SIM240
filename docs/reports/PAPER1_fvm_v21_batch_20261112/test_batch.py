"""Synthetic fail-stop tests. No mesh tool, mapping or solver is invoked."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('batch',HERE/'run_remaining.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)


def config(points=None,known=None):
    pts=points or ['p']
    return dict(points=pts,remaining=[x+'_'+lev for x in pts for lev in ('coarse','mid','fine','tight')],
                known_consistency_failures=known or [],thresholds=dict(grid_mid_coarse_percent=1,
                grid_fine_mid_percent=.5,algebraic_change_percent=.05))


def assessment(cfg):
    return dict(cases={p+'_'+lev:dict(status='NOT_EXECUTED') for p in cfg['points']
                      for lev in ('coarse','mid','fine','tight')},
                comparisons=[dict(point=p,status='NOT_ASSESSABLE') for p in cfg['points']])


class BatchTests(unittest.TestCase):
    def exercise(self,cfg,values=None,local_bad=None,runner_bad=None,new_fail=None,baseline_bad=False):
        called=[];current=assessment(cfg)
        def invoke(cid):
            called.append(cid)
            return 7 if cid==runner_bad else 0
        def evaluate(cid):
            current['cases'][cid]=dict(status='REFERENCE_CHECK_FAIL' if cid==local_bad else 'LOCAL_CHECKS_PASS',
                                      metrics=dict(K_m3=(values or {}).get(cid,1.0)))
            if cid==new_fail:
                stem=cid.rsplit('_',1)[0]
                next(c for c in current['comparisons'] if c['point']==stem).update(status='FAIL',reference_accepted=True)
            if baseline_bad:current['baseline']=dict(A_pass=False,beta_pass=True)
            return copy.deepcopy(current)
        with tempfile.TemporaryDirectory() as d:
            work=Path(d);code=b.run_sequence(cfg,current,None,work,invoke,evaluate)
            state=json.loads((work/'status.json').read_text())
        return code,called,state
    def test_serial_success(self):
        c=config();code,called,state=self.exercise(c)
        self.assertEqual(code,0);self.assertEqual(called,c['remaining']);self.assertEqual(state['completed'],c['remaining'])
    def test_local_failure_stops_without_next_case(self):
        code,called,state=self.exercise(config(),local_bad='p_mid')
        self.assertEqual(code,1);self.assertEqual(called,['p_coarse','p_mid']);self.assertEqual(state['status'],'STOPPED_ON_FAILURE')
    def test_runner_failure_no_retry(self):
        code,called,_=self.exercise(config(),runner_bad='p_coarse')
        self.assertEqual(code,1);self.assertEqual(called,['p_coarse'])
    def test_mid_grid_failure_stops(self):
        code,called,_=self.exercise(config(),values={'p_mid':.98})
        self.assertEqual(code,1);self.assertEqual(called,['p_coarse','p_mid'])
    def test_fine_non_decreasing_change_stops(self):
        code,called,_=self.exercise(config(),values={'p_mid':.999,'p_fine':.9962})
        self.assertEqual(code,1);self.assertEqual(called[-1],'p_fine')
    def test_fine_mid_half_percent_failure(self):
        code,called,_=self.exercise(config(),values={'p_mid':.992,'p_fine':.986})
        self.assertEqual(code,1);self.assertEqual(called[-1],'p_fine')
    def test_small_change_exception_is_preserved(self):
        code,_,_=self.exercise(config(),values={'p_mid':.9999,'p_fine':.9997,'p_tight':.9997})
        self.assertEqual(code,0)
    def test_tight_algebra_failure(self):
        code,called,_=self.exercise(config(),values={'p_tight':1.001})
        self.assertEqual(code,1);self.assertEqual(called[-1],'p_tight')
    def test_new_consistency_failure_stops_before_other_point(self):
        code,called,_=self.exercise(config(['p','q']),new_fail='p_tight')
        self.assertEqual(code,1);self.assertNotIn('q_coarse',called)
    def test_known_consistency_failure_retained_not_hidden(self):
        cfg=config(known=['p']);code,_,state=self.exercise(cfg,new_fail='p_tight')
        self.assertEqual(code,0);self.assertEqual(state['known_consistency_failures'],['p'])
    def test_baseline_output_failure_stops(self):
        code,called,_=self.exercise(config(),baseline_bad=True)
        self.assertEqual(code,1);self.assertEqual(len(called),1)
    def test_exception_stops_without_retry(self):
        cfg=config();called=[]
        def fail(cid):called.append(cid);raise OSError('synthetic mapping failure')
        with tempfile.TemporaryDirectory() as d:
            code=b.run_sequence(cfg,assessment(cfg),None,Path(d),invoke=fail)
        self.assertEqual(code,1);self.assertEqual(len(called),1)
    def test_execution_directory_refuses_resume(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'execution').mkdir()
            with patch.object(b,'HERE',Path(d)),patch.dict(b.os.environ,{'WM_PROJECT_VERSION':'13','WM_PROJECT_DIR':'/opt/openfoam13'}):
                with self.assertRaisesRegex(b.Halt,'no overwrite/resume/retry'):b.preflight({},None)
    def test_reference_failure_not_mistaken_for_LB_failure(self):
        cfg=config();a=assessment(cfg);a['comparisons'][0]['reference_accepted']=False
        self.assertTrue(any('reference qualification failed' in x for x in b.science_issues(a,cfg)))

if __name__=='__main__':unittest.main()
