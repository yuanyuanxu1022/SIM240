#!/usr/bin/env python3
"""Generate review-only geometry, work-size and stopping tables. No PDE solve."""
import csv
import hashlib
import importlib.util
import json
import shutil
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
AUDIT = ROOT / 'docs/reports/D4_reference_static_audit_20261025'
ACCEPT = ROOT / 'docs/reports/D4_grid_narrow_fine4_acceptance_20261025'
D4 = ROOT / 'CASE/D_series/D4_variable_groove_transport_20261023'


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def load(p):
    return json.loads(Path(p).read_text())


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def table(name, records):
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)


def kv(p):
    return dict(s.split('=', 1) for s in Path(p).read_text().splitlines() if '=' in s)


def main():
    if (OUT / 'proposal.json').exists():
        raise SystemExit('Refuse overwrite of draft generation; use another directory.')
    protected = dict(load(AUDIT / 'protected_inputs.json'))
    for p in AUDIT.rglob('*'):
        if p.is_file():
            protected[str(p)] = sha(p)
    design = load(D4 / 'protocol/design.json')
    for p in [D4 / 'protocol/design.json', D4 / 'protocol/execution.json',
              ROOT / 'docs/reports/Correlation_selection_freeze_20261024/FREEZE_RULES.md']:
        protected.setdefault(str(p), sha(p))
    changed = [p for p, digest in protected.items() if not Path(p).is_file() or sha(p) != digest]
    assert not changed, changed
    dump('protected_inputs.json', protected)
    for name in ['SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md']:
        (OUT / (name + '.before')).write_bytes((ROOT / 'docs/reports' / name).read_bytes())
    selected = [
        ('G01', 75, 25, 60, 'B1', 'narrow_shallow_lower_ratio_corner', 'existing_development'),
        ('G02', 75, 120, 60, 'B1', 'narrow_deep_upper_depth_ratio_corner', 'existing_development'),
        ('G03', 75, 25, 240, 'B2', 'wide_shallow_upper_width_ratio_corner', 'existing_development'),
        ('G04', 75, 120, 240, 'B2', 'wide_deep_upper_ratio_corner', 'existing_development'),
        ('G05', 75, 75, 120, 'B2', 'interior_old_training_geometry', 'existing_training'),
        ('G06', 50, 25, 120, 'B2', 'minimum_gap_old_training_geometry', 'existing_training'),
        ('G07', 125, 120, 240, 'B2', 'maximum_total_height_and_inertia_screen', 'new_development_only'),
        ('G08', 125, 100, 120, 'B2', 'large_gap_old_training_geometry', 'existing_training'),
        ('G09', 50, 50, 80, 'B2', 'two_thirds_scale_of_G05', 'new_development_only'),
        ('G10', 50, 80, 160, 'B2', 'two_thirds_scale_of_G04', 'new_development_only')]
    held = {(h, d, w) for h in design['new_prediction_test']['h_nm']
            for d in design['new_prediction_test']['d_nm'] for w in design['new_prediction_test']['w_nm']}
    geometries, meshes = [], []
    for ident, h, d, w, batch, role, evidence in selected:
        assert (h, d, w) not in held
        assert 50 <= h <= 125 and 25 <= d <= 120 and 60 <= w <= 240
        assert Fraction(4, 5) <= Fraction(w, h) <= Fraction(16, 5)
        assert Fraction(1, 3) <= Fraction(d, h) <= Fraction(8, 5)
        geometries.append({'geometry_id': ident, 'h_nm': h, 'd_nm': d, 'w_nm': w,
                           'P_nm': 2*w, 'Ly_nm': 2*w, 'phi': .5,
                           'w_over_h': float(Fraction(w, h)), 'd_over_h': float(Fraction(d, h)),
                           'batch_proposal': batch, 'purpose': role, 'role': evidence,
                           'reserved_prediction_geometry': False,
                           'status': 'DRAFT_NOT_A_RUN_NOT_AUTHORIZED'})
        for delta in [Fraction(5), Fraction(5, 2), Fraction(5, 4)]:
            nx, nh, nd, nw = [Fraction(v) / delta for v in [2*w, h, d, w]]
            assert all(v.denominator == 1 for v in [nx, nh, nd, nw])
            nx, nh, nd, nw = map(int, [nx, nh, nd, nw])
            squares = nx*nh + nw*nd
            vertices = (nx+1)*(nh+1) + (nw+1)*nd
            triangles = 2*squares
            edges = vertices + triangles - 1
            scalar_p2 = vertices + edges
            stokes = 2*scalar_p2 + vertices
            # Sparse storage scenario, not a measured allocation or guaranteed bound.
            scenario = 4*100*16*stokes + 1024**3
            meshes.append({'geometry_id': ident, 'mesh_size_nm': float(delta),
                           'rectangular_subcells': squares, 'triangles': triangles,
                           'vertices_before_constraints': vertices,
                           'scalar_P2_dofs_before_constraints': scalar_p2,
                           'stokes_P2P1_dofs_before_constraints': stokes,
                           'storage_scenario_bytes_100nnz_4copies_plus1GiB': scenario,
                           'is_measured_memory_or_bound': False})
    table('geometry_coverage10.csv', geometries)
    table('reference_mesh_budget30.csv', meshes)
    refs = load(ACCEPT / 'grid_review/accepted_references16.json')['rows']
    stop = []
    for gid, depth, width, dx in [('G01', 25, 60, '1.25'), ('G02', 120, 60, '1.25'), ('G04', 120, 240, '2.5')]:
        pair = [r for r in refs if int(r['h_nm']) == 75 and int(r['d_nm']) == depth
                and int(r['w_nm']) == width and Fraction(r['dx_nm']) == Fraction(dx)]
        assert len(pair) == 2 and {r['direction'] for r in pair} == {'P', 'T'}
        old = {r['direction']: kv(Path(r['raw_output']) / 'result.txt') for r in pair}
        base = max(int(v['steps_completed']) for v in old.values())
        n = int(old['P']['window_steps'])
        assert n == int(old['T']['window_steps'])
        common = base + 2*n
        cap = min(int(v['maximum_steps']) for v in old.values())
        assert common < cap
        for r in pair:
            raw = old[r['direction']]
            resource = load(Path(r['raw_output']) / 'resource_usage.json')
            seconds = resource['elapsed_seconds']*common/int(raw['steps_completed'])
            stop.append({'planned_test_id': 'STOP_DRAFT_' + gid + '_' + r['direction'],
                         'geometry_id': gid, 'h_nm': 75, 'd_nm': depth, 'w_nm': width,
                         'dx_nm': dx, 'direction': r['direction'], 'original_run_id': r['run_id'],
                         'original_output': r['raw_output'],
                         'old_stop_step': int(raw['steps_completed']), 'window_samples': n,
                         'pair_baseline_max_step': base, 'common_planned_final_step': common,
                         'original_maximum_step_cap': cap, 'dt_s': float(raw['dt_s']),
                         'extra_pair_tstar': 2*n*float(raw['dt_s'])*1e-6/(75e-9)**2,
                         'old_elapsed_seconds': resource['elapsed_seconds'],
                         'measured_old_peak_RSS_KiB': resource['max_rss_kb'],
                         'constant_cost_per_step_scenario_hours': seconds/3600,
                         'is_runtime_prediction_or_guaranteed_bound': False,
                         'actual_new_run_id': '', 'execution_authorized': False})
    table('stop_comparison6.csv', stop)
    deps = {x: importlib.util.find_spec(x) is not None for x in ['dolfinx', 'petsc4py', 'basix', 'ufl', 'gmsh', 'scipy', 'numpy']}
    dump('environment_readonly_snapshot.json', {
        'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.executable,
        'modules_visible_to_this_python': deps,
        'executables': {x: shutil.which(x) for x in ['gmsh', 'mpiexec', 'pvpython']},
        'scope': 'this interpreter only; no imports of solvers, installation or all-environment audit',
        'reference_backend_ready': False})
    resources = {
        'reference_mesh_largest_stokes_dofs_before_constraints': max(r['stokes_P2P1_dofs_before_constraints'] for r in meshes),
        'largest_sparse_storage_scenario_GiB': max(r['storage_scenario_bytes_100nnz_4copies_plus1GiB'] for r in meshes)/1024**3,
        'reference_FE_time_measured': False,
        'reference_FE_candidate_RAM_budget_GiB_per_process': 8,
        'reference_FE_candidate_disk_budget_GiB_total': 20,
        'FE_trial_time_caps_hours': {'B0_benchmarks': 2, 'B1_two_narrow_anchors': 4, 'B2_remaining_coverage': 12},
        'FE_trial_time_caps_are_allocations_not_predictions': True,
        'linear_reference_solve_counts': {'flat3x2x3': 18, 'MMS2x3': 6, 'geometry10x2x3': 60, 'total_before_audit_repeats': 84},
        'conditional_inertia_nonlinear_problem_count': 3,
        'algebraic_and_quadrature_and_alternate_mesh_audits_excluded_from_84': True,
        'stop_comparison_proposed_new_runs': 6,
        'stop_constant_cost_per_step_scenario_total_hours': sum(r['constant_cost_per_step_scenario_hours'] for r in stop),
        'stop_candidate_available_RAM_GiB': {'G01_G02_dx1p25': 4, 'G04_dx2p5': 6},
        'stop_candidate_disk_GiB_total': 25,
        'lbm_dx0p625_option': {'proposed_direction_runs': 4,
                              'same_physical_time_node_step_work_factor': 32,
                              'old_four_elapsed_seconds': 21133.26,
                              'constant_work_cost_scenario_hours': 21133.26*32/3600,
                              'would_preserve_old_dx5_FAIL': True,
                              'selected_or_released': False},
        'wide_dx1p25_option': {'old_available_RAM_requirement_GiB': 22,
                             'old_multiday_scenario_only': True, 'released': False},
        'automatic_batch_progression': False,
        'resource_caps_require_explicit_review_before_use': True}
    # Derive alternative from raw measured records, never silently copy an estimate.
    fine_records = [r for r in refs if Fraction(r['dx_nm']) == Fraction('1.25')]
    measured_seconds = sum(load(Path(r['raw_output']) / 'resource_usage.json')['elapsed_seconds'] for r in fine_records)
    resources['lbm_dx0p625_option']['old_four_elapsed_seconds'] = measured_seconds
    resources['lbm_dx0p625_option']['constant_work_cost_scenario_hours'] = measured_seconds*32/3600
    dump('resource_comparison.json', resources)
    proposal = {
        'draft_id': 'D4_CROSS_SECTION_REFERENCE_STOP_COVERAGE_20261025_DRAFT_v1',
        'status': 'REVIEW_DRAFT_NOT_FROZEN_NOT_APPROVED_NOT_EXECUTABLE',
        'old_grid_protocol_executable_v2_unchanged': True,
        'proposed_reference_contract_v2_activated': False,
        'proposed_grid_v3_activated': False,
        'model_G4_v1_unchanged': True, 'model_v2_created': False,
        'physical_family': {'phi': .5, 'P_equals': '2w', 'Ly_equals': 'P',
                            'h_nm': [50, 125], 'd_nm': [25, 120], 'w_nm': [60, 240],
                            's': [.8, 3.2], 't': ['1/3', '8/5']},
        'geometry_count': 10, 'reserved_geometry_overlap_count': 0,
        'reserved_flow_results_opened': False, 'external_exposure_verified': False,
        'recommended_method': 'independent conforming cross-section P2 Poisson and P2-P1 Stokes; inertia qualification separate',
        'backend_candidate': 'FEniCSx/PETSc or reviewed independent FE assembly; backend/version not selected or installed',
        'reference_mesh_sizes_nm': [5, 2.5, 1.25],
        'all_new_tolerances_are_proposals_not_old_gate_amendments': True,
        'proposed_limits': {
            'flat_K_relative': .0005, 'flat_velocity_L2_relative': .001,
            'MMS_finest_velocity_L2_relative': .001, 'MMS_J_absolute': .0001,
            'algebraic_true_relative_residual': 1e-10,
            'tightened_algebraic_Q_change_relative': .0001,
            'quadrature_Q_change_relative': .0001,
            'middle_to_fine_Q_difference_relative': .0025,
            'conditional_reference_estimator_relative': .005,
            'alternate_mesh_Q_difference_relative': .0025,
            'reference_mass_section_relative': 1e-6,
            'nondimensional_divergence_L2_relative': 1e-6,
            'energy_relative_balance': 1e-6,
            'stokes_to_NS_modeling_Q_difference_relative': .0005,
            'scaled_geometry_normalized_K_difference_relative': .001,
            'LBM_baseline_reproduction_K_relative': 1e-6,
            'strong_stop_std_relative': 1e-7, 'strong_stop_span_relative': 5e-7,
            'strong_stop_last_two_block_mean_difference_relative': 1e-6,
            'old_to_common_late_Q_difference_relative': .0005},
        'strong_stop_common_steps': {'G01': 79349, 'G02': 80113, 'G04': 39967},
        'new_reference_adopted': False, 'new_solver_implemented': False,
        'new_compilation_or_initialization_or_solve': False,
        'launch_command_or_runtime_manifest_created': False,
        'execution_authorized': False, 'teacher_approval_claimed': False,
        'prediction_permission': 'HOLD', 'wide_finest_permission': 'HOLD',
        'old_narrow_grid_verdict': 'TWO_GEOMETRIES_FAIL_5_QUANTITIES_FAIL_1_PASS'}
    dump('proposal.json', proposal)
    dump('generation_summary.json', {'generated_at_utc': datetime.now(timezone.utc).isoformat(),
                                     'protected_paths': len(protected), 'geometry_rows': len(geometries),
                                     'mesh_budget_rows': len(meshes), 'stop_plan_rows': len(stop),
                                     'old_inputs_changed': [], 'no_physical_computation': True})
    print(json.dumps({'geometry_rows': len(geometries), 'mesh_rows': len(meshes), 'stop_rows': len(stop),
                      'protected_paths': len(protected),
                      'stop_cost_scenario_hours': resources['stop_constant_cost_per_step_scenario_total_hours'],
                      'largest_FE_dofs_before_constraints': resources['reference_mesh_largest_stokes_dofs_before_constraints'],
                      'FE_backend_ready': False, 'execution_authorized': False}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
