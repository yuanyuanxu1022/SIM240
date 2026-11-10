#!/usr/bin/env python3
"""Manufactured in-memory checker tests and existing-data regression; no PDE solves."""
import copy
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
PKG=Path(__file__).resolve().parents[1];ROOT=PKG.parents[1]
sys.path.insert(0,str(PKG/'analysis'))
from check_results import expected_configuration,integration_checks,native_check,check_run,numbers
from sdi_metrics import evaluate

def fixture():
    cfg=json.loads((PKG/'common/GDI01.json').read_text());protocol=json.loads((PKG/'common/protocol.json').read_text())
    cells=numbers(PKG/'references/C01/openfoam/SDI_output/cells.csv');faces=numbers(PKG/'references/C01/openfoam/SDI_output/faces.csv')
    mu=cfg['mu_Pa_s'];H=cfg['H_m'];G=cfg['G_Pa_per_m'];lx,ly,_=cfg['L_m'];D=cfg['D_m_minus2'];u=cfg['K_m3'][0][0]*G/mu/H;Qs=u*H*ly
    coeff=[];evidence=[];balance={int(c['cell_id']):[] for c in cells}
    for c in cells:
        c.update(p_Pa=G*(lx-c['x_m']),Ux_m_s=u,Uy_m_s=0,Uz_m_s=0,Jx_m2_s=H*u,Jy_m2_s=0,Jz_m2_s=0)
        r=dict(cell_id=c['cell_id'],H_m=H,zone_member=1)
        for a in 'xyz':
            for b in 'xyz':r['D'+a+b+'_m_minus2']=D['xy'.index(a)]['xy'.index(b)] if a in 'xy' and b in 'xy' else 0
        coeff.append(r)
        v=c['volume_m3'];diag=mu*(D[0][0]+D[1][1])*v;Fx=mu*D[0][0]*u*v
        evidence.append(dict(cell_id=c['cell_id'],old_Ux_m_s=u,old_Uy_m_s=0,old_Uz_m_s=0,old_p_Pa=c['p_Pa'],
            diag_kg_s=diag,source_x_N=diag*u-Fx,source_y_N=0,source_z_N=0,
            grad_px_Pa_m=-G,grad_py_Pa_m=0,grad_pz_Pa_m=0,force_x_N=Fx,force_y_N=0,force_z_N=0,
            pressure_matrix_raw_residual_m3_s=0))
    for f in faces:
        q=u*f['Sx_m2'] if abs(f['Sx_m2'])>abs(f['Sy_m2']) else 0
        f.update(phi_m3_s=q,phi_U_m3_s=q);balance[int(f['owner'])].append(q)
        if f['neighbour']>=0:balance[int(f['neighbour'])].append(-q)
    for r in evidence:r['pressure_matrix_raw_residual_m3_s']=-math.fsum(balance[int(r['cell_id'])])
    raw=math.fsum(abs(r['pressure_matrix_raw_residual_m3_s']) for r in evidence)
    solver=dict(flow_solved=True,converged=True,iterations=1,outer_iterations=1,normalized_residual=raw/Qs,
        true_normalized_residual=raw/Qs,raw_residual_L1_m3_s=raw)
    history=[dict(outer=1,linear_iterations=1,normalized_residual=raw/Qs,initial_raw_L1_m3_s=Qs,
        final_raw_L1_m3_s=raw,true_normalized_residual=raw/Qs,momentum_L2_relative=0,momentum_max_relative=0,
        delta_U_L2_relative=0,delta_U_max_relative=0,delta_p_max_relative=0,global_mass_relative=0,
        local_mass_relative=0,side_leakage_relative=0,face_flux_consistency_relative=0,energy_relative=0)]
    return cfg,protocol,cells,faces,coeff,evidence,history,solver

class CheckerTests(unittest.TestCase):
    def test_manufactured_exact_solution(self):
        args=fixture();expected_configuration(args[0],args[1]);base,_=evaluate(args[0],args[2],args[3],args[-1])
        self.assertTrue(base['interface_checks_satisfied'])
        result=integration_checks(*args)
        self.assertTrue(all(c['satisfied'] for c in result['checks']),result['checks'])
    def rejects_metric(self,alter,name):
        a=fixture();alter(a);r=integration_checks(*a)
        self.assertTrue(any(not c['satisfied'] and name in c['name'] for c in r['checks']))
    def test_wrong_force_rejected(self):
        self.rejects_metric(lambda a:a[5][0].update(force_x_N=a[5][0]['force_x_N']*2),'force')
    def test_wrong_diagonal_rejected(self):
        self.rejects_metric(lambda a:a[5][0].update(diag_kg_s=a[5][0]['diag_kg_s']*2),'diag')
    def test_wrong_deferred_source_rejected(self):
        self.rejects_metric(lambda a:a[5][0].update(source_x_N=0),'source')
    def test_spoofed_gradient_rejected(self):
        self.rejects_metric(lambda a:a[5][0].update(grad_px_Pa_m=0),'gradient')
    def test_incomplete_outer_convergence_rejected(self):
        self.rejects_metric(lambda a:a[5][0].update(old_Ux_m_s=0),'delta_U')
    def test_wrong_tensor_rejected(self):
        self.rejects_metric(lambda a:a[4][0].update(Dxx_m_minus2=a[4][0]['Dxx_m_minus2']*1.1),'coefficient')
    def test_half_zone_rejected(self):
        a=fixture();a[4][0]['zone_member']=0
        with self.assertRaises(ValueError):integration_checks(*a)
    def test_missing_history_rejected(self):
        a=fixture();a[6].clear()
        with self.assertRaises(ValueError):integration_checks(*a)
    def test_nan_raw_csv_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'nan.csv';p.write_text('cell_id,Ux_m_s\n0,nan\n')
            with self.assertRaises(ValueError):numbers(p)
    def test_audit_is_not_completed_run(self):
        with self.assertRaises((ValueError,OSError)):check_run(PKG/'build/audit_case')
    def test_wrong_case_identity_rejected(self):
        a=fixture();a[0]['case_id']='C01'
        with self.assertRaises(ValueError):expected_configuration(a[0],a[1])
    def test_all_existing_SDI_metrics_unchanged(self):
        paths=[('interface_static_darcy_v1','SDI_C01_v1_20261030_01','C01','interface_analysis_geometry_v1_1.json'),
            ('interface_static_darcy_v1_1','SDI_C02_v1_1_20261030_01','C02','interface_analysis.json'),
            ('interface_static_darcy_v1_2','SDI_C03_v1_2_20261030_01','C03','interface_analysis.json'),
            ('interface_static_darcy_v1_3','SDI_C04_v1_3_20261030_01','C04','interface_analysis.json')]
        for pkg,runid,case,report in paths:
            run=ROOT/'CASE'/pkg/'runs'/runid;cfg=json.loads((run/f'common/{case}.json').read_text())
            old=json.loads((ROOT/f'docs/reports/SDI_{case}_results_20261030/{report}').read_text())
            for label,folder in [('two_dimensional','two_dimensional'),('openfoam','openfoam/SDI_output')]:
                actual,_=evaluate(cfg,numbers(run/folder/'cells.csv'),numbers(run/folder/'faces.csv'),json.loads((run/folder/'solver.json').read_text()))
                self.assertEqual(actual,old['results'][label])
    def test_native_parser_existing_fields(self):
        run=ROOT/'CASE/interface_static_darcy_v1/runs/SDI_C01_v1_20261030_01/openfoam'
        r=native_check(run,numbers(run/'SDI_output/cells.csv'),numbers(run/'SDI_output/faces.csv'))
        self.assertEqual(set(r),{'p','U','J','phi','phi_U'})

if __name__=='__main__':unittest.main(verbosity=2)
