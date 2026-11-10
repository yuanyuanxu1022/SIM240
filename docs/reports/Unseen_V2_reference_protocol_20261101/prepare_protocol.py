#!/usr/bin/env python3
"""Prepare concrete protocol, arithmetic, predictions and describe-only templates."""
from pathlib import Path
from fractions import Fraction
import csv
import hashlib
import json
import math

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
D4=ROOT/'CASE/D_series/D4_variable_groove_transport_20261023'
C=ROOT/'CASE/03_grid_convergence/G2_EX240_fine_T_statfix_C_v1'
REVIEW=ROOT/'docs/reports/C_h75_reference_review_20261101/verdict.json'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,obj):
    p=OUT/name
    if p.exists():raise FileExistsError(p)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csvwrite(name,rows):
    p=OUT/name
    if p.exists():raise FileExistsError(p)
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    verdict=json.loads(REVIEW.read_text());assert verdict['h75_discrete_benchmark_reuse'] and verdict['saved_field_readback_PASS']
    matrix=[]
    def add(stage,family,h,d,dx,direction,a,role):
        h=Fraction(str(h));d=Fraction(str(d));dx=Fraction(str(dx));H=h+d/2
        dt=(Fraction(1,2)*(dx*Fraction(1,10**9))**2)/(3*Fraction(1,10**6))
        window=Fraction(3,4)*(h*Fraction(1,10**9))**2/(Fraction(1,10**6)*dt)
        maximum=8*((h+d)*Fraction(1,10**9))**2/(Fraction(1,10**6)*dt)
        n=Fraction(240)**2*H/dx**3;assert n.denominator==1
        dxname=str(float(dx)).replace('.','p').replace('p0','')
        ident=f'URV1_{family}_{direction}_dx{dxname}_a{a}'
        cap=14400 if role=='smooth_control' else {5.:3600,2.5:14400,1.25:43200}[float(dx)]
        row=dict(planned_case_id=ident,stage=stage,family=family,role=role,h_nm=float(h),d_nm=float(d),
            w_nm=120.,P_nm=240.,Ly_nm=240.,H_nm=float(H),dx_nm=float(dx),direction=direction,
            drive_axis='y' if direction=='P' else 'x',rho_kg_m3=1000,nu_m2_s=1e-6,mu_Pa_s=.001,
            acceleration_m_s2=a,G_Pa_per_m=1000*a,tau=1,dt_s=float(dt),
            lattice_acceleration=float(a*dt*dt/(dx*Fraction(1,10**9))),
            nx_core=int(Fraction(240)/dx),ny_core=int(Fraction(240)/dx),
            expected_fluid_nodes=int(n),single_distribution_bytes=int(n)*19*8,
            window_steps=math.ceil(window),maximum_steps=math.ceil(maximum),
            wall_cap_seconds=cap,memory_limit_GiB=8,actual_run_id='',
            status='PROTOCOL_DRAFT_NOT_RUN',execution_authorized=False)
        matrix.append(row)
    for dr in ['P','T']:add('S0_REGRESSION','H75',75,100,5,dr,100000,'new_statistics_port_regression')
    for dr in ['P','T']:add('S1_SMOOTH_THIN','SMOOTH_H30',30,0,1.25,dr,100000,'smooth_control')
    for family,h,stage0,stage1 in [('U_REG',60,'S2_REG_GRID','S3_REG_LINEARITY'),('U_THIN',30,'S4_THIN_GRID','S5_THIN_LINEARITY')]:
        for dx in [5,2.5,1.25]:
            for dr in ['P','T']:add(stage0,family,h,80,dx,dr,100000,'reference_grid')
        for a in [50000,200000]:
            for dr in ['P','T']:add(stage1,family,h,80,2.5,dr,a,'linearity_control')
    assert len(matrix)==24
    csvwrite('case_matrix.csv',matrix)
    predictions=[]
    for family,h in [('U_REG',60),('U_THIN',30)]:
        depth=80.;a=h**3;b=(h+depth)**3
        for dr,orig,alpha,beta in [('P',(a+b)/24,1.7685,1.6331),('T',a*b/(6*(a+b)),.4900,.6990)]:
            factor=1/(1+alpha*(depth/120)**beta)
            predictions.append(dict(family=family,h_nm=h,d_nm=80,w_nm=120,P_nm=240,direction=dr,
                                    K_original_m3=orig*1e-27,V2_factor=factor,K_V2_m3=orig*factor*1e-27,
                                    reference_K_m3='',reference_result_available=False))
    csvwrite('model_predictions_before_reference.csv',predictions)
    source_paths=[D4/'src/variable_groove_transport.cpp',D4/'src/Makefile',D4/'build/variable_groove_transport',
                  D4/'protocol/execution.json',C/'src/mass_stats.h',C/'src/fine_T_statfix_C.cpp',C/'PROTOCOL.md',REVIEW,
                  ROOT/'CASE/D_series/D2_groove_error_map/analysis_fit_v2.py',
                  ROOT/'CASE/groove_darcy_static_v1/common/GDI01.json']
    bindings={str(p):sha(p) for p in source_paths}
    save('preparation_bindings.json',dict(files=bindings,
        intended_backend='isolated D4 physical kernel with C-style compensated mass statistics, not yet implemented',
        old_case_modified=False,backend_currently_execution_ready=False))
    candidates=json.loads((ROOT/'docs/reports/Explicit_groove_reference_audit_20261030/unseen_condition_search.json').read_text())
    save('data_history_status.json',dict(local_prior_audit='docs/reports/Explicit_groove_reference_audit_20261030/unseen_condition_search.json',
        local_prior_audit_sha256=sha(ROOT/'docs/reports/Explicit_groove_reference_audit_20261030/unseen_condition_search.json'),
        candidate_geometries=[{k:r[k] for k in ['id','h_nm','d_nm','w_nm','P_nm','novelty_status']} for r in candidates['candidates']],
        author_external_data_history_confirmation='PENDING',
        execution_blocked_until_history_and_protocol_are_accepted=True,
        reserved_D4_prediction_group_reassigned=False))
    save('acceptance_spec.json',dict(
        per_run=dict(compensated_mass_relative_strict=1e-10,ledger_agreement_max=1e-13,
            density_deviation_max=1e-6,Mach_strict=.05,section_relative_max=1e-5,
            window_relative_sample_std_max=1e-6,window_relative_span_max=5e-6,cross_flux_abs_m2_s_max=1e-12,
            q_absolute_tolerance=1e-10,volume_relative_tolerance=1e-10,
            fallback=0,unresolved=0,positive_main_flux=True,finite_all=True,independent_exit=0),
        smooth=dict(K_relative_strict=.02,profile_L2_relative_strict=.02),
        statistics_port_regression=dict(K_relative_max=1e-4,all_common_legacy_diagnostics_compare_and_report=True),
        new_physics_guards=dict(Re_H_max=.01,three_force_K_span_over_mean_max=.001,
            linearity_grid_nm=2.5,linearity_accelerations_m_s2=[50000,100000,200000]),
        reference=dict(grid_nm=[5,2.5,1.25],r=2,Fs=1.25,
            eligible_requires_monotonic_positive_finite_p=True,relative_difference_floor=1e-14,
            fine_GCI_estimate_max=.01,medium_fine_relative_change_max=.01,
            estimate_u='max(GCI_fine,abs(K_medium/K_fine-1),final_window_relative_span)',
            strict_error_bound=False,independent_asymptotic_evidence=False,
            legacy_GCI_ratio_not_used_as_qualification_evidence=True),
        comparison=dict(primary_family='U_REG',thin_family_role='predeclared risk check; transverse h<50 outside narrower recommended domain',
            signed_error='K_model/K_reference-1',absolute_error='abs(K_model/K_reference-1)',
            improvement_delta='abs(E_V2)-abs(E_original)',
            sensitivity_band='K_fine*(1+-u); numerical sensitivity only, not confidence interval or rigorous bound',
            classify_by_delta_range=dict(IMPROVED='max(delta)<-1e-12',DEGRADED='min(delta)>1e-12',INCONCLUSIVE='otherwise'),
            evaluate_band_at='both endpoints plus K_original/K_V2 breakpoints inside the band',
            reference_invalid='NOT_EVALUATED; do not score formula accuracy',
            minimum_practical_improvement_absolute_error=.02,
            practical_primary_support='both U_REG directions have max(delta)<=-0.02 over the estimated sensitivity band',
            requires_all_conditions_to_improve=False,do_not_refit_on_test=True),
        status_fields_separate=['NUMERICAL_GATE','RESULT_PASS','geometry_PASS','REFERENCE_QUALIFIED_FOR_CASE','MODEL_COMPARISON','physical_validation']))
    save('protocol.json',dict(protocol_id='URV-v1',date='2026-11-01',
        status='CONCRETE_DRAFT_STATICALLY_CHECKED_NOT_EXECUTION_FROZEN',
        scope='fixed_gap_fully_filled_single_phase_periodic_explicit_groove_reference_for_frozen_V2',
        physical=dict(period_nm=240,width_nm=120,duty_fraction=.5,rho_kg_m3=1000,nu_m2_s=1e-6,
                      mu_Pa_s=.001,tau=1,drive_P='+y',drive_T='+x',periodicity='x_y',walls='stationary_no_slip_Bouzidi',
                      collision='D3Q19_FORCE_ForcedBGK',average='J=sum(u_phys*dx^3)/plan_area; K=mu*J/(rho*a); H=h+d/2'),
        coefficient_model=dict(name='V2_published_rounded',parallel=[1.7685,1.6331],perpendicular=[.4900,.6990],
                      original='local cubic arithmetic/harmonic equal-duty law',refit_allowed=False),
        stages=['S0_REGRESSION','S1_SMOOTH_THIN','S2_REG_GRID','S3_REG_LINEARITY','S4_THIN_GRID','S5_THIN_LINEARITY'],
        directional_calculations=24,reference_grid_calculations=12,statistics_port_regressions=2,
        thin_smooth_controls=2,linearity_additional_calculations=8,
        h75_new_fine_grid_calculations_required=0,
        time=dict(window_tstar=.75,max_time_H_diffusion=8,steps='ceil(exact_value); native roundoff subtraction 1e-9 must match',
                  frame_tstar=[0,.01,.02,.05,.1,.2,.5,1,2,4,8],no_extra_time_to_fill_frames=True),
        resources=dict(processes=1,threads=1,overlap=3,per_process_address_space_GiB=8,
            required_available_RAM_GiB=12,required_initial_free_disk_GiB=100,
            required_before_each_run_free_disk_GiB=8,planned_output_budget_GiB_per_case=4,
            aggregate_wall_caps_hours=sum(r['wall_cap_seconds'] for r in matrix)/3600,
            resource_caps_are_not_measured_runtime_or_peak_memory=True),
        preparation=dict(protocol_materials_prepared=True,backend_source_port_implemented=False,
            backend_compiled_this_round=False,native_zero_step_prechecks_run=False,
            independent_acceptance_checker_implemented=False,new_solver_run_started=False),
        authorization=dict(simulation_authorized=False,approved_run_id=None,launch_command_delivered=False,
            new_stage_requires_separate_user_launch_and_completed_result_review=True),
        old_D4_prediction_gate_unchanged='HOLD',reference_qualified_global=False,
        physical_validation='NOT_EVALUATED',independent_human_acceptance=False))
    templates=OUT/'describe_only_templates';templates.mkdir(exist_ok=False)
    for row in matrix:
        cfg=dict(mode='describe',run_id='PLAN_'+row['planned_case_id'],
            output_directory='NOT_AN_EXECUTION_DIRECTORY',direction=row['direction'],dx_nm=row['dx_nm'],
            h_nm=row['h_nm'],d_nm=row['d_nm'],w_nm=120,period_nm=240,Ly_nm=240,nu_m2_s=1e-6,
            acceleration_m_s2=row['acceleration_m_s2'],window_tstar=.75,max_time_H_diffusion=8,
            frame_tstar='0,0.01,0.02,0.05,0.1,0.2,0.5,1,2,4,8')
        (templates/(row['planned_case_id']+'.txt')).write_text(''.join(f'{k}={v}\n' for k,v in cfg.items()))
    save('prediction_seal.json',dict(date='2026-11-01',
        model_predictions_sha256=sha(OUT/'model_predictions_before_reference.csv'),
        coefficient_source_hashes={str(p):sha(p) for p in source_paths[-2:]},
        has_new_reference_results=False,reviewed_existing_h75_does_not_make_it_unseen=True,
        final_execution_seal_still_required=True))
    print(json.dumps(dict(protocol='URV-v1',rows=len(matrix),new_reference_rows=12,
        control_rows=12,total_wall_cap_hours=sum(r['wall_cap_seconds'] for r in matrix)/3600,
        compile_or_solver_called=False),indent=2))

if __name__=='__main__':main()
