#!/usr/bin/env python3
"""Build protocol/reference tables from existing files; never execute a solver."""
import csv
import hashlib
import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
def read(path):
    return json.loads((ROOT/path).read_text())
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name, value):
    (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')

def main():
    original_path='docs/reports/Static_Darcy_interface_protocol_20261030/protocol.json'
    original=read(original_path)
    coeff_path=original['coefficient_source']
    coeff=read(coeff_path)
    assert sha(ROOT/coeff_path)==original['coefficient_source_sha256']
    definitions=[
        ('GDI01','C01','interface_static_darcy_v1','SDI_C01_v1_20261030_01','interface_analysis_geometry_v1_1.json'),
        ('GDI02','C02','interface_static_darcy_v1_1','SDI_C02_v1_1_20261030_01','interface_analysis.json'),
        ('GDI03','C03','interface_static_darcy_v1_2','SDI_C03_v1_2_20261030_01','interface_analysis.json'),
        ('GDI04','C04','interface_static_darcy_v1_3','SDI_C04_v1_3_20261030_01','interface_analysis.json'),
    ]
    refs=[]
    common=None
    bindings={original_path:sha(ROOT/original_path),coeff_path:sha(ROOT/coeff_path)}
    for new_id,old_id,pkg,run_id,analysis_file in definitions:
        run=ROOT/f'CASE/{pkg}/runs/{run_id}'
        cfg=json.loads((run/f'common/{old_id}.json').read_text())
        analysis_path=f'docs/reports/SDI_{old_id}_results_20261030/{analysis_file}'
        analysis=read(analysis_path)
        execution=json.loads((run/'execution.json').read_text())
        assert execution['status']=='completed' and execution['run_id']==run_id
        assert all(s['exit_code']==0 and not s['timed_out'] for s in execution['steps'])
        assert analysis['NUMERICAL_GATE']=='PASS' and analysis['RESULT_PASS'] and analysis['geometry_PASS']
        assert analysis['run_id']==run_id
        assert sha(run/'run_manifest.json')==analysis['run_manifest_sha256']
        assert cfg['thresholds']==original['thresholds'] and cfg['linear_solver']==original['linear_solver']
        shared={k:cfg[k] for k in ['H_m','L_m','mu_Pa_s','rho_kg_m3','mesh_cells','drive_axis','G_Pa_per_m','pressure_units','velocity_definition']}
        if common is None: common=shared
        assert shared==common
        assert cfg['source_hashes']['design_protocol']==sha(ROOT/original_path)
        assert cfg['source_hashes']['coefficient_source']==sha(ROOT/coeff_path)
        for item in analysis['raw_files']:
            p=run/item['path']; assert sha(p)==item['sha256'],p
            bindings[str(p.relative_to(ROOT))]=item['sha256']
        for p in [run/'execution.json',run/'run_manifest.json',run/f'common/{old_id}.json',ROOT/analysis_path]:
            bindings[str(p.relative_to(ROOT))]=sha(p)
        plan=next(c for c in original['planned_cases'] if c['case_id']==old_id)
        family=cfg.get('coefficient_input_id',plan['input_id'])
        orientation=cfg.get('orientation_id',plan['orientation_id'])
        assert family==plan['input_id'] and orientation==plan['orientation_id']
        row=next(r for r in coeff['rows'] if r['input_id']==family and r['orientation_id']==orientation)
        assert row['K_global_m3']==cfg['K_m3'] and row['D_global_m_minus2_conditional_total_drag']==cfg['D_m_minus2']
        K=cfg['K_m3'][0][0]; H=cfg['H_m']; mu=cfg['mu_Pa_s']; G=cfg['G_Pa_per_m']; Lx,Ly,b=cfg['L_m']
        expected=dict(Kxx_m3=K,Kyy_m3=cfg['K_m3'][1][1],Dxx_m_minus2=H/K,Dyy_m_minus2=cfg['D_m_minus2'][1][1],
            Ux_m_s=K*G/mu/H,Jx_m2_s=K*G/mu,Q_m3_s=K*G/mu*Ly,
            R_Q_Pa_s_m_minus3=G*Lx/(K*G/mu*Ly),power_W=G*Lx*K*G/mu*Ly)
        observed={}
        for program,folder in [('two_dimensional','two_dimensional'),('openfoam','openfoam/SDI_output')]:
            cells=list(csv.DictReader((run/f'{folder}/cells.csv').open()))
            faces=list(csv.DictReader((run/f'{folder}/faces.csv').open()))
            assert len(cells)==512
            vol=math.fsum(float(c['volume_m3']) for c in cells)
            U=math.fsum(float(c['Ux_m_s'])*float(c['volume_m3']) for c in cells)/vol
            J=math.fsum(float(c['Jx_m2_s'])*float(c['volume_m3']) for c in cells)/vol
            Q=math.fsum(float(f['phi_m3_s']) for f in faces if f['patch']=='xHigh')
            for a,bv in [(U,expected['Ux_m_s']),(J,expected['Jx_m2_s']),(Q,expected['Q_m3_s'])]:
                assert abs(a/bv-1)<=original['thresholds']['Q_relative']
            previous=analysis['results'][program]
            for a,bv in [(U,previous['mean_U_main_m_s']),(J,previous['mean_J_main_m2_s']),
                (Q,previous['boundary_Q_m3_s']['xHigh'])]: assert abs(a/bv-1)<1e-12
            observed[program]=dict(mean_Ux_m_s=U,mean_Jx_m2_s=J,Q_m3_s=Q,R_Q_Pa_s_m_minus3=G*Lx/Q,
                provenance='recomputed_from_existing_CSV_not_new_flow_result')
        refs.append(dict(planned_case=new_id,baseline_case=old_id,baseline_run_id=run_id,
            baseline_run_dir=str(run.relative_to(ROOT)),analysis_path=analysis_path,
            family=family,orientation=orientation,
            coefficient_source_row=row,analytic_expectation=expected,existing_observed=observed,
            planned_new_run_id=None,new_result=None))
    source_root=ROOT/'CASE/groove_porosity_model_v1'
    old_manifest=read('docs/reports/Groove_porosity_model_20261030/source_manifest.json')
    for rel in ['src/grooveDarcy.C','src/grooveDarcy.H','src/grooveTransport.H','build/lib/libgroovePorosity.so']:
        p=source_root/rel; key=str(p.relative_to(ROOT)); assert sha(p)==old_manifest[key],key
        bindings[key]=sha(p)
    upstream=Path('/home/dell/OpenFOAM/OpenFOAM-13')
    for rel in ['src/fvModels/general/porosityForce/porosityForce.C',
        'src/finiteVolume/cfdTools/general/fvModels/fvModelTemplates.C',
        'applications/modules/incompressibleFluid/correctPressure.C',
        'applications/modules/incompressibleFluid/momentumPredictor.C']:
        p=upstream/rel; bindings[str(p)]=sha(p)
    protocol=dict(protocol_id='GDI-v1',date='2026-10-30',status='PROTOCOL_PREPARED_HOST_NOT_IMPLEMENTED_NOT_RUN',
        scope='steady_fixed_gap_native_porosityForce_momentum_pressure_integration',
        first_case_only='GDI01',first_case_baseline='C01',run_id=None,launch_ready=False,simulation_authorized=False,
        solver_design_name='grooveDarcyStaticFoam',solver_exists=False,
        OpenFOAM='Foundation 13',pressure_definition='physical_gauge_Pa',
        velocity_definition='fluid_volume_mean_U=J/H',
        inputs=dict(mesaGap_m=75e-9,grooveDepth_m=100e-9,grooveWidth_m=120e-9,period_m=240e-9,
            H_m=125e-9,L_m=[24e-6,48e-6,125e-9],mu_Pa_s=1e-3,rho_kg_m3=1000,nu_m2_s=1e-6,
            mesh_cells=[16,32,1],porous_zone_cells=512,gapMode='uniform',
            xLow_p_Pa=24,xHigh_p_Pa=0,side_flux=0,G_Pa_m=1e6,V_m_s=0,
            family='V2_published_rounded',groove_axis='y',drive_axis='x'),
        momentum_terms=dict(total_Darcy=True,pressure=True,ddt=False,convection=False,viscous_laplacian=False,
            gravity=False,Forchheimer=False,extra_porosity_source=False,thickness_resolved_shear=False),
        boundary=dict(p=dict(xLow='fixedValue 24 Pa',xHigh='fixedValue 0 Pa',yLow='zeroGradient',yHigh='zeroGradient',frontAndBack='empty'),
            U=dict(xLow='zeroGradient',xHigh='zeroGradient',yLow='slip',yHigh='slip',frontAndBack='empty')),
        initial_internal_fields=dict(p_Pa=0,U_m_s=[0,0,0]),
        algorithm=dict(source_route='negative of standard porosityForce physical-momentum source on LHS',
            splitting='scalar_trace_implicit_plus_deferred_anisotropic_term',
            pressure='laplacian(rAU,p)=div(phiHbyA)',phi='phiHbyA-pEqn.flux()',
            velocity='HbyA-rAU*grad(p)',max_outer_iterations=2000,relaxation=1,
            zero_pressure_initial_guess_each_outer=True,pressure_relTol=0,
            no_pseudo_time_term=True,normalization='raw final L1 / raw initial L1 with zero internal pressure per assembled equation'),
        inherited_SDI_thresholds=original['thresholds'],inherited_linear_solver=original['linear_solver'],
        additional_pre_run_fixed_checks=dict(geometry_relative_tolerance=1e-10,
            coefficient_relative_tolerance=1e-12,unsplit_momentum_relative_L2_and_max=1e-10,
            outer_velocity_change_relative_L2_and_max=1e-10,outer_pressure_change_relative_max=1e-10),
        extra_checks_are_new_integration_guards_not_changes_to_SDI=True,
        resources=dict(processes=1,wall_seconds=300,memory_GiB=2,max_pressure_iterations_per_outer=2000),
        baselines=[dict(case=r['planned_case'],baseline=r['baseline_case'],new_run_id=None,authorized=False) for r in refs],
        stages=dict(protocol_prepared=True,subclass_previously_compiled=True,subclass_current_binding_verified=True,
            host_source_prepared=False,host_compiled=False,full_zone_run_package_prepared=False,
            pre_run_audit_pass=False,new_flow_run_started=False,new_flow_run_completed=False,result_checker_implemented=False),
        NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=None,geometry_PASS=None,physical_validation='NOT_EVALUATED',
        independent_human_acceptance=False,squeeze_interface_status='DEFINED_NOT_IMPLEMENTED_NOT_RUN',
        squeeze_parameters_frozen=False,submission_ready=False)
    save('protocol.json',protocol)
    save('squeeze_interface.json',dict(status='INTERFACE_DEFINED_NOT_IMPLEMENTED_NOT_RUN',
        candidate_model='fixed_planform_reference_mesh_fully_filled_rigid_uniform_closure',
        host_fields=dict(mesaGap=dict(type='registered volScalarField',units='m',producer='host',consumer='grooveDarcy',finite_positive_required=True),
            H=dict(units='m',definition='mesaGap+(grooveWidth/period)*grooveDepth'),
            gap_epoch=dict(definition='same gap snapshot ID and hash used in drag, continuity, flux, force')),
        update_order=['save_old_gap','update_new_gap_once','register_or_update_mesaGap','compute_same_epoch_H_and_dHdt',
            'freeze_gap_during_outer_iterations','assemble_porosity_force','solve_weighted_pressure_continuity',
            'audit_volume_flux_and_force','write_gap_epoch_and_diagnostics'],
        sign_convention='V_close>0 means dHdt=-V_close',
        continuity='dHdt+div_xy(H*U)=0',cell_balance='sum_outward_Q=-A_plan_cell*(H_new-H_old)/dt',
        instantaneous_Darcy_pressure='-div_xy(K*grad(p))=mu*V_close',
        native_velocity_flux='phi_U=U_f dot Sf; reference face area=b0*edge_length',
        conserved_depth_flux='Q_J=(H_face/b0)*phi_U with consistent pressure correction and face reconstruction',
        split_pressure_2d='div_xy(H*rAU*grad(p))=div_xy(H*HbyA)+dHdt',
        static_recovery='dHdt=0 and H=b0 reduce to GDI-v1',
        squeezing_velocity_m_s=None,time_step_s=None,duration_s=None,dynamic_thresholds=None,
        future_boundary='to be frozen; four zero-overpressure edges are a distinct candidate from static inlet/outlet',
        force='pressure integral and complete normal stress must be distinguished before reference comparison',
        motion_implemented=False,continuity_implemented=False,new_run_id=None,simulation_authorized=False))
    save('reference_values.json',dict(kind='EXISTING_BASELINES_AND_ANALYTIC_EXPECTATIONS_NOT_NEW_GDI_RESULTS',cases=refs))
    save('input_bindings.json',bindings)
    lines=['# 已有静态基线与新接入的解析预期','','所有 GDI 新结果均不存在；下表 Q 为已有 CSV 复算值。压力解析式为 p=10⁶(24×10⁻⁶−x) Pa。','',
        '|计划编号|对应旧例|公式/槽向|解析 Ux (m/s)|解析 Q (m³/s)|已有二维 Q (m³/s)|已有OF Q (m³/s)|',
        '|---|---|---|---:|---:|---:|---:|']
    for r in refs:
        a=r['analytic_expectation'];obs=r['existing_observed']
        lines.append(f"|{r['planned_case']}|{r['baseline_case']}|{r['family']} / {r['orientation']}|{a['Ux_m_s']:.12e}|{a['Q_m3_s']:.12e}|{obs['two_dimensional']['Q_m3_s']:.12e}|{obs['openfoam']['Q_m3_s']:.12e}|")
    lines+=['','首个实施单元仅GDI01；其余编号只作已有结果映射，不表示已准备或获准运行。',
        'GDI01解析Jx=4.5537951695675916e-14 m²/s；Dxx≈2.7449631646886185e15 m⁻²、Dyy≈1.2003056558749922e15 m⁻²。',
        'R_Q=Δp/Q是静态水力阻力，单位Pa·s/m³；V=0时不定义F/V。',
        '旧例内部PASS仅为SDI静态平均接口证据；表中解析数值和旧结果不建立V2独立预测或真实沟槽参考资格。','']
    (OUT/'EXPECTED_VALUES.md').write_text('\n'.join(lines))
    save('offline_audit.json',dict(status='OFFLINE_BINDING_AND_ARITHMETIC_PASS_NO_FLOW_RUN',
        bound_files=len(bindings),baseline_cases_checked=4,baseline_program_CSVs_checked=8,
        inherited_thresholds_exact=True,inherited_linear_solver_exact=True,shared_baseline_inputs_equal=True,
        subclass_source_and_library_current_hash_match=True,all_baseline_raw_hashes_match=True,
        new_solver_called=False,compile_called=False,subclass_tests_rerun=False,
        host_implemented=False,new_flow_run_id=None,new_results=None,human_verified=False))
    print(json.dumps(dict(protocol=protocol['protocol_id'],status=protocol['status'],bound_files=len(bindings),new_flow_run_id=None),indent=2))

if __name__=='__main__': main()
