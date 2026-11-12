import importlib.util
import math
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('postprocess',ROOT/'postprocess.py')
pp=importlib.util.module_from_spec(spec);spec.loader.exec_module(pp)


def fixture():
    # Unequal volumes and unequal directional velocities expose both common
    # normalization errors: arithmetic velocity averaging and axis swaps.
    meta=dict(expected_cells=2,expected_V_m3=240*75e-27,h_nm=75,d_nm=0,
              w_nm=120,P_nm=240,Ly_nm=1,dx_nm=1.25,direction='P',
              nu_m2_s=1e-6,acceleration_m_s2=1e5,Aplan_m2=240e-18,rho_kg_m3=1000)
    rows=[]
    for i,(fraction,u) in enumerate(((.25,1e-5),(.75,3e-5))):
        rows.append(dict(x_m=(i+.5)*100e-9,y_m=.5e-9,z_m=30e-9,
                         V_m3=fraction*meta['expected_V_m3'],Ux_m_s=9e-5,
                         Uy_m_s=u,Uz_m_s=0,grad_norm2_s2=1,
                         diss_per_mass_m2_s3=1e-6,p_kin_m2_s2=0))
    return meta,rows


class TestReader(unittest.TestCase):
    def test_volume_weight_and_m3_normalization(self):
        m,r=fixture();v=pp.metrics(m,r,[])
        u=.25*1e-5+.75*3e-5
        expected=m['nu_m2_s']/m['acceleration_m_s2']*u*75e-9
        self.assertAlmostEqual(v['K_m3']/expected,1,places=13)
        self.assertAlmostEqual(v['K_m3']/(v['Href_m']*v['kappa_m2']),1,places=13)
        wrong=m['nu_m2_s']/m['acceleration_m_s2']*(1e-5+3e-5)/2*75e-9
        self.assertGreater(abs(v['K_m3']/wrong-1),.2)

    def test_p_uses_y_velocity(self):
        m,r=fixture();first=pp.metrics(m,r,[])['K_m3']
        for x in r:x['Ux_m_s']=1e20
        self.assertEqual(first,pp.metrics(m,r,[])['K_m3'])

    def test_volume_drift_is_rejected(self):
        m,r=fixture();r[0]['V_m3']*=2
        with self.assertRaisesRegex(ValueError,'volume'):pp.metrics(m,r,[])

    def test_nan_is_rejected(self):
        m,r=fixture();r[0]['Uy_m_s']=math.nan
        with self.assertRaisesRegex(ValueError,'nonfinite'):pp.metrics(m,r,[])

    def test_solid_ridge_cell_is_rejected(self):
        m,r=fixture();m.update(d_nm=100,expected_V_m3=m['expected_V_m3'])
        r[1].update(x_m=180e-9,z_m=20e-9)
        with self.assertRaisesRegex(ValueError,'solid ridge'):pp.metrics(m,r,[])

    def test_missing_transverse_faces_is_rejected(self):
        m,r=fixture();m['direction']='T'
        with self.assertRaisesRegex(ValueError,'section fluxes'):pp.metrics(m,r,[])

    def test_generated_plan_has_no_execution(self):
        result=pp.assess()
        self.assertEqual(result['status'],'INCOMPLETE')
        self.assertFalse(result['selected_six_all_pass'])
        self.assertEqual(len(result['comparisons']),6)
        self.assertTrue(all(d['status']=='NOT_ASSESSABLE' for d in result['comparisons']))

    def synthetic_receipt(self, directory):
        """Synthetic parser fixture; no PDE, no claims about a physical solution."""
        case=Path(directory)/'prepared'/'synthetic_P_coarse';(case/'referenceEvidence').mkdir(parents=True);(case/'runtime').mkdir()
        (case/'1').mkdir();(case/'constant/polyMesh').mkdir(parents=True)
        m,r=fixture();m.update(d_nm=100,case_id='synthetic_P_coarse',level='coarse',start_time=0,end_time_cap=2,flat_zero_component_exception=False)
        m['expected_V_m3']=240*125e-27
        for row,f in zip(r,(.25,.75)):
            row['V_m3']=m['expected_V_m3']*f;row['z_m']=110e-9
            row['diss_per_mass_m2_s3']=1e-30  # intentionally huge imbalance
        (case/'case.json').write_text(json.dumps(m))
        (case.parent.parent/'prepared_manifest.json').write_text(json.dumps(dict(cases=[m],acceptance_rule=pp._accept.RULE)))
        cells=case/'referenceEvidence/cells.csv'
        with cells.open('w') as f:
            writer=csv.DictWriter(f,fieldnames=list(r[0]));writer.writeheader();writer.writerows(r)
        (case/'1/v').write_text('SYNTHETIC NATIVE FIELD: not a simulation\n')
        for name in ('points','faces','owner','neighbour','boundary'):
            (case/'constant/polyMesh'/name).write_text('SYNTHETIC MESH\n')
        for name,text in [('log.blockMesh','synthetic'),('log.checkMesh','Mesh OK.'),
                          ('log.solver','PCG:  Solving for v, Initial residual = 1e-12, '
                                        'Final residual = 1e-18, No Iterations 3\n'
                                        'SIMPLE solution converged in 1 iterations\nEnd\n'),
                          ('resource.txt','synthetic'),
                          ('exit_code.txt','0'),('release_snapshot.json',json.dumps({'external_sha256':{str(Path('/opt/openfoam13/platforms/linux64GccDPInt32Opt/bin/mapFields')):hashlib.sha256(Path('/opt/openfoam13/platforms/linux64GccDPInt32Opt/bin/mapFields').read_bytes()).hexdigest()}}))]:
            (case/'runtime'/name).write_text(text)
        dg=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        release=dg(case/'runtime/release_snapshot.json')
        receipt=dict(run_id='synthetic_fixture_only',case_id=m['case_id'],independent_exit_code=0,
                     solver_converged=True,release_unchanged=True,disk_budget_met=True,
                     source_manifest_sha256=release,executable_sha256='synthetic',
                     stopping=pp.steady_stop((case/'runtime/log.solver').read_text(),m,pp._accept.RULE),
                     evidence_sha256={'cells.csv':dg(cells)},
                     native_field_sha256={'1/v':dg(case/'1/v')},
                     mesh_sha256={n:dg(case/'constant/polyMesh'/n) for n in ('points','faces','owner','neighbour','boundary')},
                     runtime_logs_sha256={p.name:dg(p) for p in (case/'runtime').iterdir()})
        (case/'referenceEvidence/receipt.json').write_text(json.dumps(receipt))
        return case,release

    def test_coarse_power_diagnostic_not_extra_acceptance_gate(self):
        with tempfile.TemporaryDirectory() as d:
            case,release=self.synthetic_receipt(d)
            result=pp.read_case(case,release,'synthetic')
            self.assertGreater(result['metrics']['power_balance_percent'],99)
            self.assertEqual(result['status'],'LOCAL_CHECKS_PASS')

    def test_deleted_native_field_rejected_even_with_valid_csv(self):
        with tempfile.TemporaryDirectory() as d:
            case,release=self.synthetic_receipt(d);(case/'1/v').unlink()
            result=pp.read_case(case,release,'synthetic')
            self.assertEqual(result['status'],'REFERENCE_CHECK_FAIL')
            self.assertTrue(any('native field' in p for p in result['issues']))

    def test_missing_receipt_never_accepts_csv(self):
        with tempfile.TemporaryDirectory() as d:
            case,release=self.synthetic_receipt(d);(case/'referenceEvidence/receipt.json').unlink()
            self.assertEqual(pp.read_case(case,release,'synthetic')['status'],'REFERENCE_CHECK_FAIL')

    def test_receipt_without_numeric_stopping_record_is_rejected(self):
        # Fail-closed: the v2 criterion must be stated in the receipt, not inferred.
        with tempfile.TemporaryDirectory() as d:
            case,release=self.synthetic_receipt(d)
            path=case/'referenceEvidence/receipt.json'
            data=json.loads(path.read_text());data.pop('stopping')
            path.write_text(json.dumps(data))
            result=pp.read_case(case,release,'synthetic')
            self.assertEqual(result['status'],'REFERENCE_CHECK_FAIL')
            self.assertTrue(any('numeric stopping record' in p for p in result['issues']))

    def test_finished_fixed_set_does_not_request_more_runs_after_reference_failure(self):
        records={'a':dict(status='LOCAL_CHECKS_PASS'),'b':dict(status='LOCAL_CHECKS_PASS')}
        result=pp.completion_status(records,[dict(status='NOT_ASSESSABLE',reference_accepted=False)])
        self.assertEqual(result['status'],'COMPLETE_WITH_REFERENCE_FAILURE')
        self.assertTrue(result['execution_closed'])
        self.assertFalse(result['comparison_evaluable'])
        self.assertFalse(result['automatic_followup_authorized'])

    def test_failure_can_close_task_with_other_inputs_unexecuted(self):
        records={'a':dict(status='REFERENCE_CHECK_FAIL'),'b':dict(status='NOT_EXECUTED')}
        result=pp.completion_status(records,[dict(status='NOT_ASSESSABLE')])
        self.assertEqual(result['status'],'STOPPED_ON_FAILURE')
        self.assertTrue(result['execution_closed'])


class TestSeedChain(unittest.TestCase):
    def setup_chain(self, folder):
        source,release=TestReader().synthetic_receipt(folder)
        target=source.parent/'synthetic_P_mid'
        (target/'runtime/seed_inputs').mkdir(parents=True)
        (target/'runtime/release_snapshot.json').write_bytes((source/'runtime/release_snapshot.json').read_bytes())
        m=json.loads((source/'case.json').read_text());m.update(case_id=target.name,level='mid',seed_from=source.name,start_time=.5)
        (target/'case.json').write_text(json.dumps(m))
        (target/'runtime/seed_inputs/v').write_text('SYNTHETIC mapped input')
        (target/'runtime/log.mapFields').write_text('SYNTHETIC mapping log')
        (target/'runtime/log.checkMesh.seeded').write_text('SYNTHETIC Mesh OK.')
        src=json.loads((source/'referenceEvidence/receipt.json').read_text())
        dg=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        tool='/opt/openfoam13/platforms/linux64GccDPInt32Opt/bin/mapFields'
        seed=dict(seed_from=source.name,source_run_id=src['run_id'],source_receipt_sha256=dg(source/'referenceEvidence/receipt.json'),source_release_sha256=release,source_time='1',source_field_sha256=src['native_field_sha256'],source_mesh_sha256=src['mesh_sha256'],target_time=.5,target_field_sha256={'v':dg(target/'runtime/seed_inputs/v')},map_tool_path=tool,map_tool_sha256=dg(Path(tool)),map_exit_code=0,map_log_sha256=dg(target/'runtime/log.mapFields'),mesh_exit_code=0,mesh_log_sha256=dg(target/'runtime/log.checkMesh.seeded'))
        seed['map_argv']=[tool,str(source),'-case',str(target),'-sourceTime','1','-consistent','-mapMethod','interpolate','-noFunctionObjects']
        return source,target,m,dict(seed=seed),release
    def test_bound_seed_accepts(self):
        with tempfile.TemporaryDirectory() as d:
            _,t,m,r,h=self.setup_chain(d);pp.validate_seed(t,m,r,h,'synthetic')
    def test_unbound_later_directory_is_not_selected(self):
        with tempfile.TemporaryDirectory() as d:
            s,t,m,r,h=self.setup_chain(d);(s/'999').mkdir();(s/'999/v').write_text('unbound')
            pp.validate_seed(t,m,r,h,'synthetic');self.assertEqual(r['seed']['source_time'],'1')
    def test_source_native_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            s,t,m,r,h=self.setup_chain(d);(s/'1/v').write_text('tampered')
            with self.assertRaises(ValueError):pp.validate_seed(t,m,r,h,'synthetic')
    def test_source_receipt_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            s,t,m,r,h=self.setup_chain(d);(s/'referenceEvidence/receipt.json').write_text('{}')
            with self.assertRaises(ValueError):pp.validate_seed(t,m,r,h,'synthetic')
    def test_broken_chain_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            _,t,m,r,h=self.setup_chain(d);r['seed'].pop('source_run_id')
            with self.assertRaises(ValueError):pp.validate_seed(t,m,r,h,'synthetic')
    def test_mapped_input_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            _,t,m,r,h=self.setup_chain(d);(t/'runtime/seed_inputs/v').write_text('tampered')
            with self.assertRaises(ValueError):pp.validate_seed(t,m,r,h,'synthetic')
    def test_mapping_tool_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            _,t,m,r,h=self.setup_chain(d);r['seed']['map_tool_sha256']='wrong'
            with self.assertRaises(ValueError):pp.validate_seed(t,m,r,h,'synthetic')
    def test_source_time_must_match_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            _,t,m,r,h=self.setup_chain(d);r['seed']['source_time']='999'
            with self.assertRaises(ValueError):pp.validate_seed(t,m,r,h,'synthetic')

if __name__=='__main__':unittest.main()

