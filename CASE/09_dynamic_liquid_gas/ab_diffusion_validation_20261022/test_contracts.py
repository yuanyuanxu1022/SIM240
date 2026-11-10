"""Synthetic corruption/reference tests, no OpenLB solver execution."""
import csv
import tempfile
import unittest
from pathlib import Path
import numpy as np
from analyze_completed import check_history,drift_summary,records
from reference import lap,grad,matrix,sequence,load_field
from run_suite import PROTOCOL

class Contracts(unittest.TestCase):
    def test_history_requires_all_steps(self):
        rows=[dict(step=str(t),nodes='4096',finite='1') for t in [0,1,3]]
        with self.assertRaises(ValueError):check_history(rows,3,16)
        rows=[dict(step=str(t),nodes='4096',finite='1') for t in [0,1,1]]
        with self.assertRaises(ValueError):check_history(rows,2,16)
    def test_max_drift_keeps_interior_peak(self):
        d=drift_summary(['1000','1000.00001','1000'])
        self.assertEqual(d['step'],1);self.assertGreater(d['max_abs'],1e-9);self.assertEqual(d['final'],0)
    def test_nonfinite_rejected(self):
        with tempfile.TemporaryDirectory() as p:
            f=Path(p)/'data.csv';f.write_text('step,value\n0,nan\n')
            with self.assertRaises(ValueError):records(f)
    def test_tau1_scalar_and_matrix_references(self):
        c=next(c for c in PROTOCOL['B_cases'] if c['id']=='lin_n16_xyz_t100')
        _,_,_,lam=matrix(c);g=1-lam*(c['a']+c['kappa']*lam)/6
        self.assertLess(np.max(abs(sequence(c)-c['amplitude']/2*g**np.arange(c['steps']+1))),1e-14)
    def test_tau250_kinetic_startup_detectable(self):
        c=next(c for c in PROTOCOL['B_cases'] if c['id']=='lin_n16_x_t250')
        seq=sequence(c);mat,_,_,_=matrix(c);ev=np.linalg.eigvals(mat);h=ev[np.argmin(abs(ev-1))]
        # Replacing a kinetic start by a single exponent must be distinguishable.
        naive=seq[0]*h**np.arange(len(seq))
        self.assertGreater(np.max(abs(seq-naive))/c['amplitude'],1e-5)
    def test_periodic_energy_and_adjoint(self):
        xyz=np.indices((8,)*3)*2*np.pi/8;x,y,z=xyz
        p=.4+.1*np.cos(x+.3)+.07*np.sin(x+y+.2);q=np.sin(y+z+.7)
        for a in range(3):self.assertLess(abs(np.sum(p*grad(q)[a]+q*grad(p)[a])),1e-12)
        self.assertLessEqual(float(np.sum(q*lap(q))),1e-12)
    def test_coordinate_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as p:
            f=Path(p)/'field.csv';f.write_text('x,y,z,phi\n'+'0,0,0,0.5\n'*8)
            with self.assertRaises(AssertionError):load_field(f,2)

if __name__=='__main__':unittest.main()
