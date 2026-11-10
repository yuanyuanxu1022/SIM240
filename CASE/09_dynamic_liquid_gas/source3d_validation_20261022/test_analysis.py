"""Synthetic fixtures only: no solver, no physical results."""
import math
import unittest
from analyze_translation import evaluate, slope

def series(ratio=1., n=16, direction='x+'):
    rows=[]
    for t in range(round(n/(4*.008))+1):
        row=dict(step=t,nodes=n**3,phase_sum=.5*n**3,relative_drift=0.,
                 phi_min=.45,phi_max=.55,fluctuation_L2=0.,source_sum=0.,finite=1)
        for axis in 'xyz':
            moving=direction!='zero' and axis in direction
            sign=-1 if direction.endswith('-') else 1
            theta=-2*math.pi*sign*.008*ratio*t/n if moving else 0.
            row['re_'+axis]=(.05/6)*math.cos(theta)
            row['im_'+axis]=(.05/6)*math.sin(theta)
        rows.append(row)
    return rows

class AnalysisTests(unittest.TestCase):
    def test_speed_sign_and_diagonal(self):
        for direction in ['x+','x-','y+','y-','z+','z-','xyz+','xyz-']:
            result=evaluate(series(direction=direction),16,direction,'new')
            self.assertTrue(result['contract_pass'])
    def test_half_speed_detected(self):
        rows=series(.5)
        self.assertFalse(evaluate(rows,16,'x+','new')['contract_pass'])
        self.assertTrue(evaluate(rows,16,'x+','old')['contract_pass'])
    def test_missing_and_nonfinite(self):
        with self.assertRaises(ValueError):evaluate(series()[:-1],16,'x+','new')
        rows=series();rows[-1]['re_x']=float('nan')
        with self.assertRaises(ValueError):evaluate(rows,16,'x+','new')
    def test_global_max_drift_not_final(self):
        rows=series();rows[30]['phase_sum']*=1+1e-6
        rows[30]['relative_drift']=1e-6
        self.assertFalse(evaluate(rows,16,'x+','new')['tests']['conservation'])
    def test_amplitude_loss(self):
        rows=series()
        for key in ('re_x','im_x'):rows[-1][key]*=.9
        self.assertFalse(evaluate(rows,16,'x+','new')['tests']['amplitude_x'])
    def test_zero_and_slope(self):
        self.assertTrue(evaluate(series(direction='zero'),16,'zero','new')['contract_pass'])
        self.assertAlmostEqual(slope([2+3*t for t in range(30)]),3.)

if __name__=='__main__': unittest.main()
