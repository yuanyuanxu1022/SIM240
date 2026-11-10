"""S4 planning arithmetic and file provenance only; no native/VTK/build calls."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from fractions import Fraction
import csv,hashlib,json,math,shutil,sys
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
C3=ROOT/'CASE/unseen_v2_reference_checker_S3_reuse_v1_1'
C2=ROOT/'CASE/unseen_v2_reference_checker_S2_reuse_v1'
S3=ROOT/'CASE/unseen_v2_reference_S3_reuse_v1_1'
S2=ROOT/'CASE/unseen_v2_reference_S2_reuse_v1'
R3=S3/'evidence/S3_formal_launch_release_v1_1_20261103_01.json'
H3='04836ee00515ac961f80022153eb398ea1692f03b943ca713e7414ce9716b574'
R2=S2/'evidence/S2_formal_launch_release_LRP_v1_20261102_02.json'
H2='d08297ebda69d9698d40762f778eb43299fa3c01c35e5591b6d31b4e06ef26cd'
P3=ROOT/'docs/reports/URV_S3_completed_review_20261103_172033'
P2=ROOT/'docs/reports/URV_S2_completed_review_20261103_095422'
load=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def main():
    assert sha(R3)==H3 and sha(R2)==H2
    b3,b2=load(R3),load(R2)
    protected=load(P3/'protected_inputs_and_outputs.json')
    assert len(protected)==3019 and all(sha(p)==h for p,h in protected.items())
    assert all(sha(p)==h for p,h in b3['inputs_sha256'].items())
    assert all(sha(p)==h for p,h in b2['inputs_sha256'].items())
    # The completed review itself is now immutable evidence, excluding shared state.
    for folder in [P3,ROOT/'docs/reports/URV_S3_prerun_scope_review_20261103',
                   ROOT/'docs/reports/URV_S2_minimum_preparation_protocol_20261102']:
        for p in folder.rglob('*'):
            if p.is_file():
                h=sha(p);assert str(p) not in protected or protected[str(p)]==h
                protected[str(p)]=h
    for p in [ROOT/'AGENTS.md',C2/'common/PROTOCOL.md',S2/'scripts/run_S2.py',S2/'scripts/prepare_S2.py',
              S3/'scripts/run_S3.py',C3/'analysis/zero_evidence.py']:
        protected[str(p)]=sha(p)
    old_review=load(P3/'independent_review.json');assert old_review['S3_CONTROL_PASS'] and old_review['S3_FOUR_RUN_ACCEPTANCE']
    assert old_review['S2_TWO_MIDPOINT_REUSE_ACCEPTANCE'] and not old_review['reference_qualified']
    review_manifest=load(P3/'report_manifest.json');assert all(sha(P3/p)==h for p,h in review_manifest.items())
    # Only pure independent geometry/arithmetic functions; no solver controllers imported.
    sys.path.insert(0,str(C3/'analysis'));import evidence
    matrix=evidence.rows(C3/'common/case_matrix.csv')
    six=[r for r in matrix if r['stage']=='S4_THIN_GRID']
    expected=[f'URV1_U_THIN_{d}_dx{dx}_a100000' for dx in ['5','2p5','1p25'] for d in ['P','T']]
    assert [r['planned_case_id'] for r in six]==expected
    native=Path(b3['provenance']['native_binary']);env=load(b3['provenance']['build_environment'])
    assert sha(native)==env['binary_sha256']=='5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b'
    assert env['compile_exit_code']==0 and not env['preparation_only_build']
    for key in ['native_sources_sha256','dependency_sha256','link_library_sha256','dynamic_library_sha256']:
        assert all(sha(p)==h for p,h in env[key].items())
    assert sha(env['compiler_executable'])==env['compiler_sha256']
    differences={}
    for p in (C3/'common').glob('*'):
        if p.is_file():differences[str(p.relative_to(C3))]=sha(p)==sha(C2/'common'/p.name)
    for name in ['check_results.py','evidence.py','read_fields.py']:
        differences['analysis/'+name]=sha(C3/'analysis'/name)==sha(C2/'analysis'/name)
    assert all(differences.values())
    configs=[];callplan=[]
    s2review=load(P2/'independent_review.json')
    source=Path(next(p for p in b3['provenance']['native_sources'] if p.endswith('/urv_reference.cpp'))).read_text()
    assert 'n>100000' in source and 'capSteps<2000000000' in source and 'p.drive=1' in source and 'p.drive=0' in source
    assert 'mrp::DensityCapture capture' not in source
    for row in six:
        ident=row['planned_case_id'];template=ROOT/'docs/reports/Unseen_V2_reference_protocol_20261101/describe_only_templates'/(ident+'.txt')
        protected[str(template)]=sha(template);cfg=evidence.kv(template);p=evidence.exact_parameters(cfg);g=evidence.geometry(cfg)
        assert cfg['mode']=='describe' and cfg['output_directory']=='NOT_AN_EXECUTION_DIRECTORY'
        assert all(float(cfg[k])==float(row[m]) for k,m in [('h_nm','h_nm'),('d_nm','d_nm'),('w_nm','w_nm'),('period_nm','P_nm'),('Ly_nm','Ly_nm'),('dx_nm','dx_nm'),('acceleration_m_s2','acceleration_m_s2')])
        assert (p['nodes'],p['window'],p['cap'])==tuple(int(row[k]) for k in ['expected_fluid_nodes','window_steps','maximum_steps'])
        dx=float(cfg['dx_nm'])*1e-9;h=float(cfg['h_nm'])*1e-9;d=float(cfg['d_nm'])*1e-9;nu=float(cfg['nu_m2_s']);dt=(1-.5)*dx*dx/(3*nu)
        assert math.ceil(.75*h*h/(nu*dt)-1e-9)==p['window'] and math.ceil(8*(h+d)**2/(nu*dt)-1e-9)==p['cap']
        assert p['H']==70e-9 and p['nodes']*19*8==int(row['single_distribution_bytes'])
        frame_targets=[math.ceil(Fraction(t)*6*(Fraction(cfg['h_nm'])/Fraction(cfg['dx_nm']))**2) for t in cfg['frame_tstar'].split(',')]
        s2=next(r for r in s2review['runs'] if r['direction']==cfg['direction'] and r['dx_nm']==float(cfg['dx_nm']))
        node_ratio=p['nodes']/s2['core_fluid_nodes'];step_cost=s2['solver_seconds']/s2['steps']
        cap_cost=step_cost*node_ratio*p['cap']
        v=dict(planned_case_id=ident,direction=cfg['direction'],dx_nm=float(cfg['dx_nm']),h_nm=30,d_nm=80,w_nm=120,period_nm=240,Ly_nm=240,H_nm=70,
            acceleration_m_s2=100000,dt_s=p['dt'],lattice_acceleration=p['a']*p['dt']**2/p['dx'],
            expected_core_nodes=p['nodes'],expected_wall_links=g['candidate_links'],q_min=g['q_min'],q_max=g['q_max'],
            material=g,window_steps=p['window'],maximum_steps=p['cap'],frame_targets=frame_targets,
            single_distribution_bytes=p['nodes']*19*8,window_physical_seconds=p['window']*p['dt'],maximum_physical_seconds=p['cap']*p['dt'],
            proposed_solver_cap_seconds=int(row['wall_cap_seconds']),S2_reference_run_id=s2['run_id'],
            S2_measured_seconds_per_step=step_cost,S4_to_S2_core_node_ratio=node_ratio,
            conditional_full_cap_cost_hours=cap_cost/3600,conditional_cost_is_unmeasured=True,
            native_audit_executed=False,geometry_PASS=None,NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,actual_run_id=None)
        configs.append(v)
        for mode in ['describe','precheck','initialize']:
            callplan.append(dict(planned_case_id=ident,mode=mode,advance_steps=0,initial_field_read=mode=='initialize',execution_authorized=False,run_id=None))
    save('six_configuration_static_review.json',configs)
    with (OUT/'six_configuration_review.csv').open('x') as f:
        keys=['planned_case_id','dx_nm','direction','h_nm','d_nm','H_nm','expected_core_nodes','expected_wall_links','window_steps','maximum_steps','dt_s','proposed_solver_cap_seconds']
        w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(configs)
    save('zero_call_plan.json',dict(kind='PLAN_NOT_AUTHORIZATION',native_calls=18,initial_field_reads=6,records=callplan))
    save('binary_reuse_review.json',dict(binary_path=str(native),binary_sha256=sha(native),historical_build_record=b3['provenance']['build_environment'],
        historical_build_sha256=sha(b3['provenance']['build_environment']),dependency_files=len(env['dependency_sha256']),static_link_files=len(env['link_library_sha256']),dynamic_files=len(env['dynamic_library_sha256']),
        byte_identical_scientific_files=differences,current_S3_inputs_verified=len(b3['inputs_sha256']),current_S2_inputs_verified=len(b2['inputs_sha256']),
        decision='PREFER_EXACT_EXISTING_ELF_NO_REBUILD_IF_CLOSURE_UNCHANGED',native_S4_parameter_acceptance='SOURCE_LEVEL_ONLY_NOT_NATIVE_AUDIT',
        instruction_audit='REUSE_HISTORICAL_SCOPED_AUDIT_IF_EXACT_ELF_UNCHANGED_NOT_NEW_AUDIT',new_builds=0,native_invocations=0))
    mem=next(int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:'))
    save('resource_review.json',dict(snapshot_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),MemAvailable_bytes=mem,disk_free_bytes=shutil.disk_usage(ROOT).free,
        future_limits=dict(processes=1,threads=1,cuboids=1,overlap=3,address_space_GiB_per_process=8,available_RAM_GiB=12,initial_disk_GiB=100,before_each_disk_GiB=8,output_GiB_per_case=4),
        total_proposed_solver_caps_hours=34,resource_reserved=False,S4_performance_measured=False,
        cost_model='S2 actual elapsed / actual steps * (S4 fluid nodes / S2 fluid nodes) * S4 maximum steps; conditional rough model only',
        important_limit='No prediction of S4 convergence steps, actual peak memory, fixed costs, or completion within wall cap',
        performance_decision='REVIEW_AFTER_ZERO_BEFORE_FORMAL; no new performance run currently required or authorized by this report'))
    proposed=[ROOT/'CASE/unseen_v2_reference_S4_reuse_v1',ROOT/'CASE/unseen_v2_reference_checker_S4_reuse_v1']
    assert not any(p.exists() for p in proposed),'proposed S4 candidate already exists; review must be revised'
    save('scope_decision.json',dict(protocol_id='S4-PR-v1',kind='READ_ONLY_SCOPE_REVIEW_NOT_IMPLEMENTATION_OR_EXECUTION_AUTHORIZATION',
        user_instruction='另定 S4 运行前材料与合同兼容性审查范围，不自动实现或启动计算。',
        future_minimum_scope_id='S4-MIP-v1_PROPOSED_NOT_ADOPTED',stage='S4_THIN_GRID',planned_case_ids=expected,
        proposed_isolated_paths=[str(p) for p in proposed],proposed_paths_created=False,actual_run_ids=[],approved_run_ids=[],
        implementation_authorized=False,build_authorized=False,native_zero_step_authorized=False,initial_field_readback_authorized=False,
        performance_authorized=False,formal_simulation_authorized=False,S5_authorized=False,
        minimum_future_changes=['S4 exact-stage source adoption and authority validation','isolated contracts dispatch without weakening prior branches',
            'S4 preparation A/B closed seals and immutable input closure','S4 formal controller and separate zero audit entry',
            'R1 effective-parameter checks and R2 six distinct initial-field/payload associations','negative-path software checks without real native/VTK calls',
            'six-point stage-local grid evidence output without model scoring or full reference qualification'],
        frozen=['native source/ELF and measurement rounding paths','physics/average/force/boundaries','all common files and predictions',
            'check_results.py/evidence.py/read_fields.py scientific routines','all historical results/releases/FAILs'],
        formal_acceptance='NOT_EVALUATED',REFERENCE_QUALIFIED_FOR_CASE=False,MODEL_COMPARISON='NOT_EVALUATED',physical_validation='NOT_EVALUATED',submission_ready=False,F04='OPEN_OUT_OF_SCOPE'))
    assert all(sha(p)==h for p,h in protected.items())
    save('protected_inputs_before.json',protected)
    save('verification.json',dict(at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),STATIC_REVIEW_PASS=True,
        protected_files_unchanged=len(protected),six_templates_match_original_matrix=True,exact_and_float_step_counts_match=True,
        independent_geometry_predictions_only=True,expected_zero_native_calls=18,expected_initial_field_reads=6,
        same_binary_and_build_closure_verified=True,scientific_files_byte_identical=True,
        new_CASE_paths_created=0,solver_calls=0,native_calls=0,VTK_reader_calls=0,builds=0,performance_advancement=0,
        executable_release_created=False,launch_command_delivered=False,model_comparison_performed=False))
    print(json.dumps(dict(out=str(OUT),protected=len(protected),configs=[{k:v[k] for k in ['dx_nm','direction','expected_core_nodes','expected_wall_links','window_steps','maximum_steps','conditional_full_cap_cost_hours']} for v in configs]),indent=2))
if __name__=='__main__':main()
