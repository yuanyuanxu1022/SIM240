"""Synthetic v2.1 acceptance boundaries; no solver or mapped production fields."""
import importlib.util
import json
import math
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('a',ROOT/'acceptance.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


def meta(direction='T',flat=False,tight=False):
    return dict(direction=direction,d_nm=0 if flat else 100,
                level='flat' if flat else ('tight' if tight else 'coarse'),
                start_time=0,end_time_cap=1,flat_zero_component_exception=flat and direction=='T')


def cycle(ux=1e-12,uz=1e-12,p=1e-12,v=None):
    pairs=[('v',v)] if v is not None else [('Ux',ux),('Uz',uz),('p',p)]
    return ''.join(f'solver: Solving for {n}, Initial residual = {r}, Final residual = 0, No Iterations 1\n' for n,r in pairs if r is not None)


class TestStopping(unittest.TestCase):
    def stop(self,text=None,m=None,**kwargs):
        return a.steady_stop(text if text is not None else cycle()+'End\n',m or meta(),a.RULE,**kwargs)
    def test_full_vector_accepts_cap_explicitly(self):
        s=self.stop();self.assertEqual(s['actual_stop_reason'],'iteration_cap');self.assertEqual(s['post_hoc_acceptance'],'accepted')
    def test_pressure_failure(self): self.assertEqual(self.stop(cycle(p=.1)+'End')['post_hoc_acceptance'],'rejected')
    def test_vertical_failure(self): self.assertEqual(self.stop(cycle(uz=.1)+'End')['post_hoc_acceptance'],'rejected')
    def test_missing_pressure(self): self.assertEqual(self.stop(cycle(p=None)+'End')['post_hoc_acceptance'],'rejected')
    def test_missing_vertical(self): self.assertEqual(self.stop(cycle(uz=None)+'End')['post_hoc_acceptance'],'rejected')
    def test_missing_end(self): self.assertEqual(self.stop(cycle())['post_hoc_acceptance'],'rejected')
    def test_string_cannot_bypass_bad_pressure(self):
        self.assertEqual(self.stop(cycle(p=.1)+'SIMPLE solution converged in 1 iterations\nEnd')['post_hoc_acceptance'],'rejected')
    def test_tight_not_ordinary(self):
        self.assertEqual(self.stop(cycle(ux=5e-11)+'End',meta(tight=True))['post_hoc_acceptance'],'rejected')
    def test_scalar_uses_v_only(self): self.assertEqual(self.stop(cycle(v=1e-12)+'End',meta('P'))['post_hoc_acceptance'],'accepted')
    def test_scalar_cannot_use_ux(self): self.assertEqual(self.stop(m=meta('P'))['post_hoc_acceptance'],'rejected')
    def test_flat_exception_requires_amplitude_and_analytic(self):
        m=meta(flat=True);t=cycle(uz=.1)+'End'
        self.assertEqual(self.stop(t,m)['post_hoc_acceptance'],'rejected')
        args=dict(amplitudes={'Ux':1e-4,'Uz':1e-16},analytic={'flat_K_error_percent':.01,'flat_profile_L2_percent':.01})
        self.assertEqual(self.stop(t,m,**args)['post_hoc_acceptance'],'accepted')
        args['amplitudes']['Uz']=1e-6
        self.assertEqual(self.stop(t,m,**args)['post_hoc_acceptance'],'rejected')
    def test_flat_exception_cannot_apply_to_groove(self):
        m=meta();m['flat_zero_component_exception']=True
        self.assertEqual(self.stop(m=m)['post_hoc_acceptance'],'rejected')
    def test_tight_success(self): self.assertEqual(self.stop(m=meta(tight=True))['post_hoc_acceptance'],'accepted')
    def test_zero_and_zero(self): self.assertTrue(a.same_residual(0,0))
    def test_one_zero(self): self.assertFalse(a.same_residual(0,1e-20));self.assertFalse(a.same_residual(1e-20,0))
    def test_invalid_residuals(self):
        for x in (math.nan,math.inf,-1):
            self.assertFalse(a.same_residual(x,x))
            self.assertEqual(self.stop(cycle(ux=x)+'End')['post_hoc_acceptance'],'rejected')
    def test_zero_log_accepts(self): self.assertEqual(self.stop(cycle(ux=0,uz=0,p=0)+'End')['post_hoc_acceptance'],'accepted')
    def test_timeout_never_accepts(self): self.assertEqual(self.stop(exit_code=124)['post_hoc_acceptance'],'rejected')
    def test_native_priority_at_cap(self): self.assertEqual(self.stop(cycle()+'SIMPLE solution converged in 1 iterations\nEnd')['actual_stop_reason'],'native_convergence')
    def test_unknown_early_end(self):
        m=meta();m['end_time_cap']=9
        self.assertEqual(self.stop(m=m)['post_hoc_acceptance'],'rejected')
    def test_old_string_not_tail(self):
        self.assertEqual(self.stop('SIMPLE solution converged in 1 iterations\n'+cycle()+'End')['post_hoc_acceptance'],'rejected')
    def test_last_complete_cycle_not_last_pressure(self):
        t=cycle(p=.1)+'solver: Solving for p, Initial residual = 0, Final residual = 0, No Iterations 0\nEnd'
        self.assertEqual(self.stop(t)['post_hoc_acceptance'],'rejected')
    def test_decimal_seeded_time(self):
        m=meta();m.update(start_time=.5,end_time_cap=2)
        self.assertEqual(self.stop(cycle()+'End',m)['actual_stop_reason'],'iteration_cap')
        self.assertEqual(self.stop(cycle()+'SIMPLE solution converged in 1.5 iterations\nEnd',m)['post_hoc_acceptance'],'accepted')
    def test_native_report_must_match_cycle(self):
        self.assertEqual(self.stop(cycle()+'SIMPLE solution converged in 3 iterations\nEnd')['post_hoc_acceptance'],'rejected')
    def test_limits_and_targets(self):
        plan=json.loads((ROOT/'prepared_manifest.json').read_text())
        self.assertEqual(plan['acceptance_rule'],a.RULE)
        self.assertEqual(plan['revision'],'v2.1_stopping_fix')
        self.assertEqual(plan['acceptance_rule']['version'],'v2.1_stopping_fix')
        self.assertIn('tight',plan['acceptance_rule']['declared_residuals'])
        self.assertEqual(len(plan['cases']),26)
        for c in plan['cases']:
            expected=1800 if c['level']=='coarse' else dict(mid=14400,fine=43200,tight=43200,flat=3600)[c['level']]
            self.assertEqual(c['wall_clock_seconds'],expected)
            self.assertIn(f"endTime {c['end_time_cap']};",(ROOT/'prepared'/c['case_id']/'system/controlDict').read_text())
            self.assertEqual(c['exit_trigger']['U'],'1e-11' if c['level']=='tight' else '1e-10')
        for key,val in dict(K_difference_percent=2,A_difference_percent=2,beta_difference_deg=.4,flat_K_percent=.1,flat_profile_percent=.1,grid_mid_coarse_percent=1,grid_fine_mid_percent=.5,algebraic_change_percent=.05,power_balance_percent=.1).items():
            self.assertEqual(plan['thresholds'][key],val)

if __name__=='__main__':unittest.main()
