"""Numerical definitions with analytic expectations, no solver execution."""
import unittest
import numpy as np
from analyze_completed import describe_pressure, window_metrics

class AnalysisDefinitions(unittest.TestCase):
    def test_fixed_inclusive_window_and_linear_trend(self):
        t=np.arange(2001);v=2e6+500*t
        result=describe_pressure(t,v)
        w=result['windows']['1501_2000']
        self.assertEqual(w['count'],500)
        self.assertEqual(w['first_step'],1501)
        self.assertEqual(w['last_step'],2000)
        self.assertAlmostEqual(w['mean_Pa'],2e6+500*(1501+2000)/2)
        self.assertAlmostEqual(w['slope_Pa_per_step'],500)
        self.assertAlmostEqual(w['fitted_window_change_Pa'],500*499)
        self.assertAlmostEqual(result['adjacent_half_mean_difference_Pa'],500*250)

    def test_constant_and_zero_mean_do_not_invent_decay(self):
        t=np.arange(2001)
        for v in [np.zeros(len(t)),np.full(len(t),1.5e6)]:
            result=describe_pressure(t,v)
            self.assertTrue(all(x['positive_decay_tau_steps'] is None for x in result['envelope_diagnostics']))
        w=window_metrics(np.arange(4),np.array([-3.,-1.,1.,3.]))
        self.assertIsNone(w['peak_to_peak_over_abs_mean'])
        self.assertEqual(w['peak_to_peak_Pa'],6.)

    def test_known_damped_oscillation_envelope(self):
        t=np.arange(2001);v=1.5e6+1e6*np.exp(-t/600)*np.cos(2*np.pi*t/50)
        result=describe_pressure(t,v)
        for fit in result['envelope_diagnostics']:
            self.assertGreater(fit['envelope_points'],3)
            self.assertAlmostEqual(fit['median_peak_interval_steps'],50,delta=1)
            self.assertAlmostEqual(fit['positive_decay_tau_steps'],600,delta=20)

if __name__=='__main__':unittest.main()
