"""Synthetic, in-memory checker tests. No CFD program is imported or launched."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('checker',ROOT/'analysis/check_results.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)


def fixture():
    cfg=json.loads((ROOT/'common/C03.json').read_text())
    nx,ny,_=cfg['mesh_cells'];lx,ly,H=cfg['L_m'];dx,dy=lx/nx,ly/ny
    G=cfg['G_Pa_per_m'];mu=cfg['mu_Pa_s'];J=cfg['K_m3'][0][0]*G/mu;U=J/H
    cells=[]
    for j in range(ny):
        for i in range(nx):
            cells.append(dict(cell_id=j*nx+i,x_m=(i+.5)*dx,y_m=(j+.5)*dy,z_m=H/2,volume_m3=dx*dy*H,
                              p_Pa=G*(lx-(i+.5)*dx),Ux_m_s=U,Uy_m_s=0.,Uz_m_s=0.,Jx_m2_s=J,Jy_m2_s=0.,Jz_m2_s=0.))
    faces=[]
    for j in range(ny):
        for i in range(nx+1):
            low=i==0;high=i==nx;s=(-1 if low else 1)*dy*H
            faces.append(dict(face_id=len(faces),owner=j*nx+(0 if low else i-1),neighbour=-1 if low or high else j*nx+i,
                              patch='xLow' if low else ('xHigh' if high else 'internal'),x_m=i*dx,y_m=(j+.5)*dy,z_m=H/2,
                              Sx_m2=s,Sy_m2=0.,Sz_m2=0.,phi_m3_s=U*s,phi_U_m3_s=U*s))
    for j in range(ny+1):
        for i in range(nx):
            low=j==0;high=j==ny;s=(-1 if low else 1)*dx*H
            faces.append(dict(face_id=len(faces),owner=(0 if low else j-1)*nx+i,neighbour=-1 if low or high else j*nx+i,
                              patch='yLow' if low else ('yHigh' if high else 'internal'),x_m=(i+.5)*dx,y_m=j*dy,z_m=H/2,
                              Sx_m2=0.,Sy_m2=s,Sz_m2=0.,phi_m3_s=0.,phi_U_m3_s=0.))
    solver=dict(flow_solved=True,converged=True,normalized_residual=0.,true_normalized_residual=0.,iterations=1,raw_residual_L1_m3_s=0.)
    return cfg,cells,faces,solver


class CheckerTests(unittest.TestCase):
    def test_ideal_synthetic_fields_accepted(self):
        result,_=checker.evaluate(*fixture());self.assertTrue(result['interface_checks_satisfied'])

    def test_wrong_pressure_sign_rejected(self):
        data=fixture()
        for c in data[1]:c['p_Pa']=-c['p_Pa']
        result,_=checker.evaluate(*data);self.assertFalse(result['interface_checks_satisfied'])

    def test_global_and_local_mass_failures_detected(self):
        data=fixture();data[2][0]['phi_m3_s']+=1e-19
        result,_=checker.evaluate(*data)
        failed={r['name'] for r in result['checks'] if not r['satisfied']}
        self.assertIn('global_mass_relative',failed);self.assertIn('local_mass_relative',failed)

    def test_wrong_average_height_scale_detected(self):
        data=fixture()
        for c in data[1]:c['Ux_m_s']*=1.4;c['Jx_m2_s']*=1.4
        for f in data[2]:f['phi_U_m3_s']*=1.4
        result,_=checker.evaluate(*data);self.assertFalse(result['interface_checks_satisfied'])

    def test_missing_face_rejected(self):
        data=fixture();data[2].pop()
        with self.assertRaises(ValueError):checker.evaluate(*data)

    def test_swapped_tensor_detected(self):
        data=fixture();cfg=data[0];cfg['K_m3'][0][0],cfg['K_m3'][1][1]=cfg['K_m3'][1][1],cfg['K_m3'][0][0]
        result,_=checker.evaluate(*data);self.assertFalse(result['interface_checks_satisfied'])

    def test_unconverged_status_rejected(self):
        data=fixture();data[3]['converged']=False
        with self.assertRaises(ValueError):checker.evaluate(*data)

    def test_wrong_normal_rejected(self):
        data=fixture();data[2][0]['Sx_m2']*=-1
        with self.assertRaises(ValueError):checker.evaluate(*data)

    def test_nonfinite_csv_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'raw.csv';p.write_text('p_Pa\nnan\n')
            with self.assertRaises(ValueError):checker.read_csv(p)

    def test_missing_completed_run_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(OSError):checker.check_run(Path(tmp))

    def test_zero_drive_uses_absolute_checks(self):
        cfg,cells,faces,solver=fixture();cfg['G_Pa_per_m']=0
        for c in cells:
            for field in ['p_Pa','Ux_m_s','Jx_m2_s']:c[field]=0.
        for f in faces:f['phi_m3_s']=f['phi_U_m3_s']=0.
        result,_=checker.evaluate(cfg,cells,faces,solver);self.assertTrue(result['interface_checks_satisfied'])


if __name__=='__main__':unittest.main()
