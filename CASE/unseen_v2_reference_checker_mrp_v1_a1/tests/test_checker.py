"""Synthetic arithmetic/mutation tests plus two read-only historical trajectory tests."""
from pathlib import Path
import copy
import json
import math
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
from evidence import (EvidenceError,kv,rows,exact_parameters,geometry,check_boundary,
                      window_metrics,grid_estimate,sensitivity)
from check_results import diagnostics,compare_legacy,aggregate,binding

CASE=Path(__file__).resolve().parents[1]
PROJECT=CASE.parents[1]

def fixture():
    cfg=dict(mode='steady',run_id='SYNTHETIC_NOT_A_FLOW_SOLUTION',direction='T',h_nm='30',d_nm='80',
        w_nm='120',period_nm='240',Ly_nm='240',dx_nm='5',nu_m2_s='1e-6',
        acceleration_m_s2='100000',window_tstar='.75',max_time_H_diffusion='8')
    p=exact_parameters(cfg);N=p['window'];J=1e-12;mass=1000*p['nodes']*p['dx']**3
    d={k:np.zeros(N) for k in ['step','J','rho','Mach','mass','time_s','mass_error',
        'max_density_deviation','Jx','Jy','Jz','Q_section1','Q_section2','section_relative_difference',
        'pressure_min','pressure_max','window_rel_std','window_rel_span','window_cross_abs_max',
        'finite','corrected_mass','corrected_mass_error','delta_mass_error','mass_ledger_agreement','density_delta']}
    d['step']=np.arange(N,dtype=float);d['time_s']=d['step']*p['dt']
    for key in ['J','Jx']:d[key][:]=J
    for key in ['mass','corrected_mass']:d[key][:]=mass
    for key in ['rho','finite']:d[key][:]=1
    for key in ['Q_section1','Q_section2']:d[key][:]=J*p['Ly']
    for key in ['window_rel_std','window_rel_span','window_cross_abs_max']:d[key][:-1]=-1
    r={k:'0' for k in ['max_mass_abs_relative','legacy_max_mass_abs_relative','max_delta_mass_abs_relative',
        'max_mass_ledger_agreement','max_density_deviation','max_Mach','window_main_rel_std',
        'window_main_rel_span','window_cross_abs_max','section_relative_difference']}
    r.update(steps_completed=str(N-1),Keff_m3=str(p['nu']*J/p['a']),J_main_m2_s=str(J),
        R_eff_Pa_s_per_m3=str(1000*p['a']/J),J_vector_m2_s=f'{J},0,0',legacy_mass_gate_PASS='true')
    return cfg,r,d

class CheckerTests(unittest.TestCase):
    def test_synthetic_positive_trajectory(self):
        c,r,d=fixture();got=diagnostics(c,r,d)
        self.assertEqual(got['all_full_windows_recomputed'],1)
        self.assertAlmostEqual(got['K_m3']/1e-23,1)

    def test_physical_mass_and_delta_independently_recomputed(self):
        c,r,d=fixture();p=exact_parameters(c)
        d['corrected_mass'][-1]*=(1+1e-11)
        measured=(d['corrected_mass'][-1]-d['corrected_mass'][0])/d['corrected_mass'][0]
        d['density_delta'][-1]=p['nodes']*measured
        d['corrected_mass_error'][-1]=d['delta_mass_error'][-1]=measured
        r['max_mass_abs_relative']=r['max_delta_mass_abs_relative']=str(measured)
        diagnostics(c,r,d)

    def test_missing_new_mass_column(self):
        c,r,d=fixture();del d['density_delta']
        with self.assertRaises(EvidenceError): diagnostics(c,r,d)

    def test_nonfinite_hidden_earlier(self):
        c,r,d=fixture();d['Jz'][2]=np.nan
        with self.assertRaises(EvidenceError): diagnostics(c,r,d)

    def test_missing_step(self):
        c,r,d=fixture();d['step'][4]=5
        with self.assertRaises(EvidenceError): diagnostics(c,r,d)

    def test_mass_violation_even_when_summary_claims_pass(self):
        c,r,d=fixture();d['corrected_mass'][-1]*=(1+2e-10)
        with self.assertRaises(EvidenceError): diagnostics(c,r,d)

    def test_mass_ledgers_disagree(self):
        c,r,d=fixture();d['density_delta'][-1]=1e-6
        with self.assertRaises(EvidenceError): diagnostics(c,r,d)

    def test_late_stop_rejected(self):
        c,r,d=fixture()
        for k in d:d[k]=np.r_[d[k],d[k][-1]]
        d['step'][-1]+=1;d['time_s'][-1]+=exact_parameters(c)['dt'];r['steps_completed']=str(len(d['J'])-1)
        with self.assertRaises(EvidenceError): diagnostics(c,r,d)

    def test_incomplete_window_rejected(self):
        c,r,d=fixture()
        for k in d:d[k]=d[k][:-1]
        r['steps_completed']=str(len(d['J'])-1)
        with self.assertRaises(EvidenceError): diagnostics(c,r,d)

    def test_direction_swap_rejected(self):
        c,r,d=fixture();c['direction']='P'
        with self.assertRaises(EvidenceError): diagnostics(c,r,d)

    def test_K_wrong_dimensions(self):
        c,r,d=fixture();r['Keff_m3']=str(float(r['Keff_m3'])*1e9)
        with self.assertRaises(EvidenceError): diagnostics(c,r,d)

    def test_Mach_strict_boundary(self):
        c,r,d=fixture();d['Mach'][1]=.05
        with self.assertRaises(EvidenceError): diagnostics(c,r,d)

    def test_Re_guard(self):
        c,r,d=fixture();d['Mach'][1]=.001
        with self.assertRaises(EvidenceError): diagnostics(c,r,d)

    def test_statistical_summary_does_not_override_trajectory(self):
        c,r,d=fixture();d['J'][2]*=1.01;d['Jx'][2]*=1.01
        with self.assertRaises(EvidenceError): diagnostics(c,r,d)

    def test_geometry_from_known_exact_groove(self):
        c,_,_=fixture();c.update(h_nm='75',d_nm='100')
        g=geometry(c);self.assertEqual(g['fluid_nodes'],57600)
        self.assertEqual(g['candidate_links'],32448)
        for q in [g['q_min'],g['q_max']]:
            self.assertLessEqual(abs(q-.5),1e-10)

    def test_smooth_analytic_link_count(self):
        c,_,_=fixture();c.update(d_nm='0',dx_nm='1.25')
        g=geometry(c);self.assertEqual(g['fluid_nodes'],192*192*24)
        self.assertEqual(g['candidate_links'],10*192*192)

    def test_q_and_geometry_corruption(self):
        run=next((CASE.parent/'unseen_v2_reference_v1/audits/URV_ZERO_20261101_01').glob('URV1_H75_P*/precheck'))
        c=kv(run/'run_config.txt');b=kv(run/'boundary_audit.txt')
        check_boundary(c,b)
        for key,value in [('q_min','.49'),('installed_links','1'),('material_1','1'),('unresolved_link_count','1')]:
            bad=dict(b);bad[key]=value
            with self.assertRaises(EvidenceError): check_boundary(c,bad)

    def test_grid_second_order_known_sequence(self):
        g=grid_estimate(1.04,1.01,1.0025,1e-6)
        self.assertAlmostEqual(g['p'],2)
        self.assertAlmostEqual(g['extrapolated_K_m3'],1)
        self.assertTrue(g['REFERENCE_QUALIFIED_FOR_CASE'])

    def test_bad_grid_does_not_score(self):
        for K in [(1,1,1),(1,1.1,1.05),(1.02,1.01,.99),(2,1.5,1.25)]:
            self.assertFalse(grid_estimate(*K,1e-6)['REFERENCE_QUALIFIED_FOR_CASE'])

    def test_grid_uncertainty_is_not_rigorous_bound(self):
        g=grid_estimate(1.04,1.01,1.0025,.009)
        self.assertEqual(g['u'],.009)
        self.assertFalse(g['strict_error_bound_established'])

    def test_sensitivity_improve_degrade_inconclusive(self):
        self.assertEqual(sensitivity(1.4,1.01,1,.005)['MODEL_COMPARISON'],'IMPROVED')
        self.assertEqual(sensitivity(1.01,1.4,1,.005)['MODEL_COMPARISON'],'DEGRADED')
        self.assertEqual(sensitivity(.99,1.01,1,.02)['MODEL_COMPARISON'],'INCONCLUSIVE')

    def test_breakpoints_and_percentage_points(self):
        s=sensitivity(.99,1.01,1,.02)
        self.assertIn(.99,s['evaluation_points_m3']);self.assertIn(1.01,s['evaluation_points_m3'])
        s=sensitivity(1.04,1.01,1,0);self.assertAlmostEqual(s['delta_max'],-.03)
        self.assertTrue(s['practical_improvement'])
        self.assertFalse(sensitivity(1.02,1.01,1,0)['practical_improvement'])

    def test_sensitivity_exhaustive_oracle(self):
        for K0,Kv,K,u in [(2,.9,1,.2),(.99,1.01,1,.03),(.5,.6,1,.2)]:
            s=sensitivity(K0,Kv,K,u);x=np.linspace(K*(1-u),K*(1+u),100001)
            delta=np.abs(Kv/x-1)-np.abs(K0/x-1)
            self.assertLessEqual(s['delta_min'],float(delta.min())+1e-14)
            self.assertGreaterEqual(s['delta_max'],float(delta.max())-1e-14)

    def test_aggregate_missing_data(self):
        with self.assertRaises(EvidenceError): aggregate([])

    def synthetic_accepted(self):
        accepted=[]
        for row in rows(CASE/'common/case_matrix.csv'):
            dx=float(row['dx_nm']);K=1e-23*(1+.04*(dx/5)**2)
            accepted.append(dict(planned_case_id=row['planned_case_id'],family=row['family'],stage=row['stage'],
                direction=row['direction'],dx_nm=dx,acceleration_m_s2=float(row['acceleration_m_s2']),
                RESULT_PASS=True,scalar=dict(K_m3=K,final_span=1e-6)))
        return accepted

    def test_aggregate_separates_valid_reference_and_model_degradation(self):
        # Artificial numbers exercise the decision chain; these are not simulated K.
        summary=aggregate(self.synthetic_accepted())
        self.assertEqual(len(summary['conditions']),4)
        self.assertTrue(all(r['REFERENCE_QUALIFIED_FOR_CASE'] for r in summary['conditions']))
        self.assertEqual(summary['conditions'][-1]['comparison']['MODEL_COMPARISON'],'DEGRADED')
        self.assertTrue(summary['primary_practical_support'])

    def test_failed_linearity_suppresses_scoring(self):
        accepted=self.synthetic_accepted()
        for r in accepted:
            if r['family']=='U_REG' and r['direction']=='P' and r['acceleration_m_s2']==2e5:
                r['scalar']['K_m3']*=1.1
        condition=aggregate(accepted)['conditions'][0]
        self.assertFalse(condition['REFERENCE_QUALIFIED_FOR_CASE'])
        self.assertEqual(condition['comparison']['MODEL_COMPARISON'],'NOT_EVALUATED')

    def test_duplicate_case_rejected(self):
        accepted=self.synthetic_accepted();accepted[-1]=accepted[0]
        with self.assertRaises(EvidenceError): aggregate(accepted)

    def test_untrusted_release(self):
        with self.assertRaises(EvidenceError): binding(CASE/'common/adoption.json','0'*64)

    def test_historical_P_and_T_windows_readonly(self):
        foundation=PROJECT/'CASE/D_series/D4_variable_groove_transport_20261023/results/foundation_20261023_v1'
        for direction in ['P','T']:
            run=next(foundation.glob('*regression*_'+direction+'_*'))/'steady'
            c=kv(run/'run_config.txt');r=kv(run/'result.txt');raw=rows(run/'diagnostics.csv')
            J=np.array([float(a['J']) for a in raw]);cross=np.array([float(a['Jx' if direction=='P' else 'Jy']) for a in raw])
            std,span,_=window_metrics(J,cross,exact_parameters(c)['window'],work_elements=65536)
            self.assertAlmostEqual(std[-1],float(r['window_main_rel_std']),delta=1e-12)
            self.assertAlmostEqual(span[-1],float(r['window_main_rel_span']),delta=1e-12)
            self.assertTrue(compare_legacy(run,run)['all_exact'])

if __name__=='__main__': unittest.main(verbosity=2)
