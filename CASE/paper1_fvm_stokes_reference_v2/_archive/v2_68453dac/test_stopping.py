"""Numeric steady criterion v2, exercised on the residuals actually observed."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('postprocess', ROOT/'postprocess.py')
pp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pp)


def log(ux=None, uz=None, p=None, v=None, string=False):
    rows = []
    if ux is not None:
        rows.append(f'smoothSolver:  Solving for Ux, Initial residual = {ux}, '
                    f'Final residual = 7.7e-13, No Iterations 15')
    if uz is not None:
        rows.append(f'smoothSolver:  Solving for Uz, Initial residual = {uz}, '
                    f'Final residual = 5.0e-13, No Iterations 6')
    if p is not None:
        rows.append(f'GAMG:  Solving for p, Initial residual = {p}, '
                    f'Final residual = {p}, No Iterations 0')
    if v is not None:
        rows.append(f'PCG:  Solving for v, Initial residual = {v}, '
                    f'Final residual = 1e-17, No Iterations 3')
    if string:
        rows.append('SIMPLE solution converged in 40000 iterations')
    return '\n'.join(rows)+'\nEnd\n'


class TestStopping(unittest.TestCase):
    def test_forty_thousand_steps_is_accepted_numerically(self):
        # h75_d0_T_flat at 40000 steps: Ux 5.5e-11 but Uz stuck at 4.0e-10.
        stop = pp.steady_stop(log(ux='5.5484435647187403e-11', uz='4.1285861653565263e-10',
                                  p='5.2534994642251872e-13'), 'T')
        self.assertFalse(stop['log_reports_converged'])
        self.assertTrue(stop['numeric_ok'])
        self.assertAlmostEqual(stop['residual']/5.5484435647187403e-11, 1, places=12)

    def test_six_thousand_steps_is_rejected(self):
        # The recorded REFERENCE_CHECK_FAIL: Ux 4.86e-05 is four decades short.
        stop = pp.steady_stop(log(ux='4.8589982251424422e-05', uz='8.9490155991215683e-10',
                                  p='6.5723823965380204e-13'), 'T')
        self.assertFalse(stop['numeric_ok'])
        self.assertFalse(stop['log_reports_converged'])

    def test_uz_floor_never_decides(self):
        # A converged Ux with a Uz so large it would fail 1e-10 still passes:
        # Uz is deliberately excluded from the criterion.
        stop = pp.steady_stop(log(ux='1e-10', uz='9.9e-09'), 'T')
        self.assertTrue(stop['numeric_ok'])

    def test_scalar_direction_uses_v(self):
        stop = pp.steady_stop(log(v='1e-12', p='1e-3'), 'P')
        self.assertEqual(stop['dominant'], 'v')
        self.assertTrue(stop['numeric_ok'])

    def test_last_occurrence_wins(self):
        text = log(ux='1e-3')+log(ux='1e-11')
        self.assertAlmostEqual(pp.steady_stop(text, 'T')['residual']/1e-11, 1, places=12)

    def test_log_string_is_sufficient(self):
        stop = pp.steady_stop(log(ux='1e-11', string=True), 'T')
        self.assertTrue(stop['log_reports_converged'])

    def test_missing_component_is_not_convergence(self):
        stop = pp.steady_stop(log(uz='1e-12', p='1e-13'), 'T')
        self.assertIsNone(stop['residual'])
        self.assertFalse(stop['numeric_ok'])


class TestThresholdsUnchanged(unittest.TestCase):
    def test_scheme_a_targets_are_not_relaxed(self):
        # Guard against a v2 edit that quietly loosens the published targets.
        import json
        manifest = json.loads((ROOT/'prepared_manifest.json').read_text())
        t = manifest['thresholds']
        self.assertEqual(t['K_difference_percent'], 2.0)
        self.assertEqual(t['A_difference_percent'], 2.0)
        self.assertEqual(t['beta_difference_deg'], 0.40)
        self.assertEqual(t['flat_K_percent'], 0.1)
        self.assertEqual(t['grid_mid_coarse_percent'], 1.0)
        self.assertEqual(t['grid_fine_mid_percent'], 0.5)
        self.assertEqual(t['algebraic_change_percent'], 0.05)
        self.assertEqual(t['power_balance_percent'], 0.1)


if __name__ == '__main__':
    unittest.main()
