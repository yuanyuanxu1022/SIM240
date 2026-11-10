"""Static arithmetic and saved-evidence audit. No execution entry imports."""
from pathlib import Path
from fractions import Fraction
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import importlib.util
import json
import math
import shutil

ROOT = Path('/home/dell/yuanyuanxu/SIM240')
OUT = Path(__file__).resolve().parent
CASE = ROOT / 'CASE/unseen_v2_reference_S4_reuse_v1'
CHECKER = ROOT / 'CASE/unseen_v2_reference_checker_S4_reuse_v1'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def save(name, data):
    p = OUT / name
    assert not p.exists(), 'refuse to overwrite draft evidence: ' + name
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    assert load(OUT / 'review_intake_validation.json')['valid'] is True
    prior = ROOT / 'docs/reports/URV_S4_grid_failure_disposition_20261104'
    protected = load(prior / 'protected_evidence.json')
    assert all(sha(p) == h for p, h in protected.items())
    for folder in [prior, ROOT / 'docs/reports/URV_S4_transverse_disposition_review_20261104_145410',
                   ROOT / 'docs/reports/URV_S2_perf_results_review_20261102']:
        for p in folder.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                protected[str(p)] = sha(p)
    release = CASE / 'evidence/S4_formal_launch_release_v1_20261104_01.json'
    release_sha = 'e5f7de1e584b776f8cc9bf1dbb31f198422ce10984ba8ad7d729220afdcdd19b'
    assert sha(release) == release_sha
    bound = load(release)
    assert all(sha(p) == h for p, h in bound['inputs_sha256'].items())
    spec = load(CHECKER / 'common/acceptance_spec.json')
    assert spec['reference']['medium_fine_relative_change_max'] == .01
    assert spec['reference']['fine_GCI_estimate_max'] == .01
    # This module only supplies arithmetic/read utilities; never imports controllers.
    source = CHECKER / 'analysis/evidence.py'
    module_spec = importlib.util.spec_from_file_location('static_arithmetic_only', source)
    ev = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(ev)
    refs = []
    baseline_records = [r for r in bound['prepared_runs']
                        if '_T_' in r['run_id'] and ev.kv(r['run_config_path'])['dx_nm'] in ('2.5', '1.25')]
    assert len(baseline_records) == 2
    for role, rec in zip(['coarse', 'medium'], baseline_records):
        run = Path(rec['output_directory'])
        completion = load(run / 'completion.json')
        acceptance_path = CASE / 'analysis_results' / rec['run_id'] / 'acceptance.json'
        acceptance = load(acceptance_path)
        assert acceptance['completion_sha256'] == sha(run / 'completion.json')
        assert acceptance['RESULT_PASS'] is True and acceptance['geometry_PASS'] is True
        assert acceptance['NUMERICAL_GATE'] == 'PASS'
        assert completion['release_sha256'] == acceptance['release_sha256'] == release_sha
        assert completion['inputs_before_sha256'] == completion['inputs_after_sha256'] == bound['inputs_sha256']
        assert completion['independent_process_exit_code'] == 0 and completion['timed_out'] is False
        assert completion['resource_stop_reason'] is None
        assert {str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name != 'completion.json'} == set(completion['output_sha256'])
        assert all(sha(run / p) == h for p, h in completion['output_sha256'].items())
        refs.append(dict(supplement_grid_role=role, run_id=rec['run_id'],
            planned_case_id=rec['planned_case_id'], dx_nm=float(ev.kv(rec['run_config_path'])['dx_nm']),
            original_release_path=str(release), original_release_sha256=release_sha,
            original_stage='S4_THIN_GRID', output_directory=str(run),
            config_path=rec['run_config_path'], config_sha256=rec['run_config_sha256'],
            completion_path=str(run / 'completion.json'), completion_sha256=sha(run / 'completion.json'),
            acceptance_path=str(acceptance_path), acceptance_sha256=sha(acceptance_path),
            original_output_sha256=completion['output_sha256'], K_m3=acceptance['scalar']['K_m3'],
            rerun_required=False, approved_under_supplement=False))
    template = ev.kv(baseline_records[-1]['run_config_path'])
    cfg = dict(template, dx_nm='0.625')  # in-memory arithmetic; not an executable config
    p = ev.exact_parameters(cfg)
    g = ev.geometry(cfg)
    assert p['nodes'] == 16515072 and p['window'] == 10368 and p['cap'] == 1486848
    assert g['candidate_links'] == 1964544
    assert all(abs(g[k] - .5) <= 1e-10 for k in ['q_min', 'q_max'])
    binary = bound['provenance']['native_binary']
    assert sha(binary) == '5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b'
    f = Fraction
    h, d, w, P, Ly, dx, nu = [f(v) for v in ['30e-9','80e-9','120e-9','240e-9','240e-9','0.625e-9','1e-6']]
    dt = dx * dx / (6 * nu)
    assert dt == f(p['dt']).limit_denominator(10**30) or math.isclose(float(dt), p['dt'], rel_tol=1e-15)
    nodes = (P * Ly * h + w * Ly * d) / dx**3
    assert nodes.denominator == 1 and int(nodes) == p['nodes']
    candidate = dict(protocol_id='URV-S4T-SUP-v0.1-DRAFT', kind='DOCUMENT_ONLY_NOT_RUN_CONFIGURATION',
        stage_proposal='S4T_SPATIAL_SUPPLEMENT', geometry_family='U_THIN',
        direction='T', flow_axis='+x', h_nm=30, d_nm=80, w_nm=120, period_nm=240, Ly_nm=240,
        dx_nm=.625, nu_m2_s=1e-6, rho_kg_m3=1000, mu_Pa_s=.001, acceleration_m_s2=100000,
        tau=1, mean_H_nm=70, exact_static_parameters=p, static_geometry=g,
        lattice_acceleration=float(f(100000) * dt**2 / dx),
        initial_half_force_J_m2_s=float((h + d/2) * f(100000) * dt / 2),
        native_binary_path=binary, native_binary_sha256=sha(binary), native_reuse='STATIC_CANDIDATE_NOT_NATIVE_VERIFIED',
        old_grid_family_nm=[5,2.5,1.25], proposed_grid_family_nm=[2.5,1.25,.625],
        new_formal_points_proposed=1, actual_run_ids=[], implementation_authorized=False,
        native_calls=0, actual_geometry_PASS=None, adoption_status='DRAFT_NOT_ADOPTED',
        authority={k: False for k in ['build','native_zero','initial_field_readback','PERF','formal','retry','extension','S5']})
    save('candidate_definition.json', candidate)
    save('baseline_references.json', refs)
    gi = 1024**3
    old_run = Path(baseline_records[-1]['output_directory'])
    old_completion = load(old_run / 'completion.json')
    old_step = int(ev.kv(old_run / 'result.txt')['steps_completed'])
    assert old_step == 12537
    old_seconds = old_completion['elapsed_seconds']
    linear_s_per_step = old_seconds / old_step * 8
    mem = {line.split(':')[0]: int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()
           if line.startswith(('MemTotal:', 'MemAvailable:', 'SwapTotal:', 'SwapFree:'))}
    snapshot = dict(captured_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(), **mem,
                    disk_free_bytes=shutil.disk_usage(ROOT).free, point_in_time_only=True)
    resource = dict(candidate_fluid_nodes=p['nodes'], old_fine_fluid_nodes=2064384,
        core_single_D3Q19_population_GiB=p['nodes']*19*8/gi,
        core_D3Q19_plus_FORCE_doubles_GiB=p['nodes']*(19+3)*8/gi,
        core_envelope_nodes=sum(g['material_'+str(i)] for i in range(4)),
        envelope_single_D3Q19_population_GiB=sum(g['material_'+str(i)] for i in range(4))*19*8/gi,
        caveat='Storage arithmetic, not peak RSS or virtual-address-space bound; solid/overlap/arrays/readback/allocator costs remain.',
        historical_S2_observed_RSS_GiB=1.835052,
        S2_fluid_nodes=2949120,
        naive_S2_RSS_scaled_by_fluid_nodes_GiB=1.835052*p['nodes']/2949120,
        RSS_scaling_not_a_measurement_or_guarantee=True,
        old_T_fine_elapsed_seconds=old_seconds, old_T_fine_steps=old_step,
        conditional_seconds_per_step=linear_s_per_step,
        conditional_same_stop_physical_time_hours=old_seconds*32/3600,
        conditional_full_cap_hours=linear_s_per_step*p['cap']/3600,
        conditional_1024_steps_seconds=linear_s_per_step*1024,
        all_costs_conditional_not_observed=True,
        draft_limits=dict(processes=1,threads=1,cuboids=1,overlap=3,
            proposed_address_space_GiB=16, required_MemAvailable_GiB=20,
            required_initial_disk_GiB=100, required_before_each_child_disk_GiB=32,
            output_budget_GiB_per_identity=16,
            native_zero_caps_seconds=dict(describe=120,precheck=1800,initialize=3600),
            initial_field_readback_cap_seconds=3600,
            PERF_wall_cap_seconds=7200,PERF_first_observed_target_step=1024,
            formal_wall_cap_seconds_candidate=172800,formal_checker_cap_seconds_candidate=14400,
            caps_are_unadopted_not_authority=True),
        current_snapshot=snapshot,
        current_MemAvailable_meets_proposed_20GiB=mem['MemAvailable']>=20*gi,
        current_disk_meets_proposed_100GiB=snapshot['disk_free_bytes']>=100*gi)
    save('resource_assessment.json', resource)
    save('protected_sources.json', protected)
    assert all(sha(path)==digest for path,digest in protected.items())
    save('verification.json', dict(static_draft_complete=True,
        bound_inputs_verified=len(bound['inputs_sha256']),protected_sources_unchanged=len(protected),
        baseline_references_verified=2, candidate_geometry_is_static_only=True,
        native_calls=0,builds=0,VTK_reads=0,PERF_runs=0,formal_runs=0,CASE_writes=0,
        new_run_configs=0,new_run_ids=[],execution_authorized=False,
        old_S4_failure_preserved=True,S5_started=False))
    print(json.dumps(dict(nodes=p['nodes'],links=g['candidate_links'],window=p['window'],cap=p['cap'],
        memory_available_GiB=mem['MemAvailable']/gi,conditional_hours=old_seconds*32/3600,
        conditional_full_cap_hours=resource['conditional_full_cap_hours'],protected=len(protected)),ensure_ascii=False))


if __name__ == '__main__':
    main()
