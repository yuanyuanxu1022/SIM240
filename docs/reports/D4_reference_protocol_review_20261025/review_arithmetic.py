#!/usr/bin/env python3
"""Static pressure/periodic contract and conditional budget arithmetic; no PDE solve."""
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
PARENT = ROOT / 'docs/reports/D4_reference_protocol_draft_20261025'
D = Decimal


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


def table(name, rows):
    with (OUT / name).open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    if (OUT / 'review_decision.json').exists():
        raise SystemExit('Refuse overwrite of completed arithmetic review.')
    protected = dict(load(PARENT / 'protected_inputs.json'))
    for p in PARENT.rglob('*'):
        if p.is_file():
            protected[str(p)] = sha(p)
    assert not [p for p, h in protected.items() if not Path(p).is_file() or sha(p) != h]
    dump('protected_inputs.json', protected)
    for name in ['SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md']:
        (OUT / (name + '.before')).write_bytes((ROOT / 'docs/reports' / name).read_bytes())

    # Deliberately elementary static analytic identities, no mesh or linear solve.
    eps, pi = .1, math.pi
    max_div = max_wall = max_periodic = 0.0
    for z in [0, .125, .25, .5, .75, .875, 1]:
        g = z*z*(1-z)**2
        gp = 2*z - 6*z*z + 4*z*z*z
        def field(x):
            return (z-z*z+eps*math.sin(pi*x)*gp,
                    -eps*pi*math.cos(pi*x)*g,
                    eps*math.cos(pi*x)*math.cos(pi*z))
        for x in [0, .125, .5, 1, 1.875, 2]:
            div = eps*pi*math.cos(pi*x)*gp - eps*pi*math.cos(pi*x)*gp
            max_div = max(max_div, abs(div))
            if z in [0, 1]:
                max_wall = max(max_wall, *(abs(v) for v in field(x)[:2]))
        max_periodic = max(max_periodic, *(abs(a-b) for a, b in zip(field(0), field(2))))
    assert max_div == max_wall == 0 and max_periodic < 1e-14
    dump('pressure_periodic_static_checks.json', {
        'scope': 'analytic identities only, not a solver or implemented constraint validation',
        'physical_weak_blocks': '[[nu*K,-B^T],[-B,0]]; B(q,u)=integral(q div u)',
        'body_force_form': '-nu*Delta(u)+grad(pi)=a*ex, pi periodic',
        'equivalent_no_body_force_pressure': 'p_eq=rho*pi-rho*a*x; remove explicit a*ex',
        'flat_dimensionless_body_form_residual': 0,
        'flat_dimensionless_equivalent_no_body_form_residual': 0,
        'flat_dimensionless_double_drive_form_residual': -1,
        'double_drive_would_change_flat_K_factor': 2,
        'constant_pressure_contributes_integral_div_test': 'zero by solid no-slip and paired periodic traces',
        'periodic_faces': 'x=0 and x=P, 0<z<h; no fluid face above h',
        'pressure_gauge': 'one constant nullspace then volume-weighted zero mean',
        'MMS_sample_max_divergence': max_div,
        'MMS_sample_max_wall_speed': max_wall,
        'MMS_sample_max_periodic_trace_difference': max_periodic,
        'MMS_exact_flux_functional_fraction': '1/6',
        'PDE_solved': False})

    budgets = [
        {'component': 'spatial', 'limit_relative': '0.0012', 'limit_percent': '0.12',
         'ratio_definition': 'Q_space/Q_Stokes_exact - 1', 'evidence_type': 'conditional estimator, not established bound'},
        {'component': 'algebraic', 'limit_relative': '0.0001', 'limit_percent': '0.01',
         'ratio_definition': 'successive numerical reference ratio minus one', 'evidence_type': 'tightened solve comparison, not yet run'},
        {'component': 'quadrature', 'limit_relative': '0.0001', 'limit_percent': '0.01',
         'ratio_definition': 'successive numerical reference ratio minus one', 'evidence_type': 'increased quadrature comparison, not yet run'},
        {'component': 'Stokes_to_NS', 'limit_relative': '0.0005', 'limit_percent': '0.05',
         'ratio_definition': 'Q_NS/Q_Stokes - 1', 'evidence_type': 'model-gap comparison, unavailable in minimal scope'},
        {'component': 'LBM_stop', 'limit_relative': '0.0005', 'limit_percent': '0.05',
         'ratio_definition': 'Q_late/Q_old - 1', 'evidence_type': 'same-grid time comparison, deferred'}]
    table('conditional_budget5.csv', budgets)
    with localcontext() as ctx:
        ctx.prec = 60
        bs, ba, bq, bm, bt = [D(r['limit_relative']) for r in budgets]
        r_plus = (1+bs)*(1+ba)*(1+bq)/(1-bm)-1
        r_minus = 1-(1-bs)*(1-ba)*(1-bq)/(1+bm)
        r = max(r_plus, r_minus)
        c_plus = 1/((1-bt)*(1-r))-1
        c_minus = 1-1/((1+bt)*(1+r))
        c = max(c_plus, c_minus)
        a_bound = 2*c/(1-c)
        assert a_bound < D('.005')
        budget_result = {
            'precision': 60, 'component_sum_percent': str(sum([bs, ba, bq, bm, bt])*100),
            'reference_direction_positive_envelope_percent': str(r_plus*100),
            'reference_direction_negative_envelope_percent': str(r_minus*100),
            'reference_A_conservative_envelope_percent': str(2*r/(1-r)*100),
            'comparison_direction_envelope_percent': str(c*100),
            'comparison_A_conservative_envelope_percent': str(a_bound*100),
            'margin_to_half_percent_in_percentage_points': str(D('.5')-100*a_bound),
            'maximum_direction_envelope_for_A_half_percent': str(D('.005')/(2+D('.005'))*100),
            'orientation': 'R=Q_ref/Q_NS; S=Q_late/Q_old; C=1/(S*R)',
            'reference_R_plus_envelope': '(1+b_space)(1+b_alg)(1+b_quad)/(1-b_model)-1',
            'comparison_C_plus_envelope': '1/[(1-b_stop)(1-r)]-1',
            'A_propagation': '2*c/(1-c)',
            'all_component_bounds_established': False,
            'this_is_a_physical_accuracy_certificate': False,
            'old_LBM_spatial_bias_included_in_budget': False,
            'old_LBM_spatial_bias_is_retained_signal_not_removed': True,
            'model_G4_prediction_error_included': False,
            'new_budget_active': False}
    dump('budget_arithmetic.json', budget_result)

    cases = []
    for delta, nx, nz in [(5, 48, 15), (2.5, 96, 30), (1.25, 192, 60)]:
        for dr in ['P', 'T']:
            cases.append({'planned_id': f'B0MIN_FLAT_{dr}_d{str(delta).replace(".","p")}',
                          'problem': 'flat75', 'direction_or_field': dr, 'mesh_label': str(delta)+'nm',
                          'nx': nx, 'nz': nz, 'quadrature_degree': 8, 'true_relative_residual_target': 1e-10,
                          'role': 'base', 'actual_run_id': '', 'authorized_to_execute': False})
    for field in ['scalar', 'mixed']:
        for n in [8, 16, 32]:
            cases.append({'planned_id': f'B0MIN_MMS_{field}_N{n}', 'problem': 'MMS',
                          'direction_or_field': field, 'mesh_label': f'N{n}', 'nx': 2*n, 'nz': n,
                          'quadrature_degree': 8, 'true_relative_residual_target': 1e-10,
                          'role': 'base', 'actual_run_id': '', 'authorized_to_execute': False})
    assert len(cases) == 12
    bases = [r.copy() for r in cases if r['mesh_label'] in ['1.25nm', 'N32']]
    for base in bases:
        strict = dict(base, planned_id=base['planned_id']+'_ALG', role='algebraic_repeat', true_relative_residual_target=1e-12)
        cases.append(strict)
    for base in [r for r in bases if r['problem'] == 'MMS']:
        cases.append(dict(base, planned_id=base['planned_id']+'_QUAD', role='quadrature_repeat', quadrature_degree=12))
    assert len(cases) == 18
    table('minimal_benchmark18.csv', cases)
    topology = []
    for nx, nz in sorted({(r['nx'], r['nz']) for r in cases}):
        vertices = (nx+1)*(nz+1)
        triangles = 2*nx*nz
        p2 = 2*vertices+triangles-1
        topology.append({'nx': nx, 'nz': nz,
                         'P2_trace_nodes_each_periodic_face': 2*nz+1,
                         'free_P2_trace_pairs_after_wall_values': 2*nz-1,
                         'P1_pressure_trace_pairs': nz+1,
                         'scalar_P2_dofs_before_constraints': p2,
                         'Stokes_P2P1_dofs_before_constraints': 2*p2+vertices,
                         'scalar_free_dofs': p2-(4*nx+2)-(2*nz-1),
                         'pressure_free_dofs_after_periodic_and_one_gauge': vertices-(nz+1)-1})
    table('periodic_topology6.csv', topology)
    max_dof = max(r['Stokes_P2P1_dofs_before_constraints'] for r in topology)
    sparse = (4*100*16*max_dof+1024**3)/1024**3
    stop = list(csv.DictReader((PARENT/'stop_comparison6.csv').open(encoding='utf-8-sig')))
    future_pair_hours = sum(float(r['constant_cost_per_step_scenario_hours']) for r in stop if r['geometry_id'] == 'G02')
    decision = {
        'review_id': 'D4_REFERENCE_PROTOCOL_REVIEW_20261025_v1',
        'revised_draft_id': 'D4_REFERENCE_CONSTRAINT_BUDGET_MINIMUM_20261025_DRAFT_v2',
        'status': 'REVIEW_COMPLETE_MINIMUM_SCOPE_SELECTED_NOT_FROZEN_NOT_AUTHORIZED',
        'old_draft_preserved': True,
        'pressure_body_force_equivalence_needs_wording_correction': True,
        'pressure_weak_form_signs_consistent': True,
        'periodic_boundary_extent_and_gauge_need_explicit_contract': True,
        'budget_proposal_defined': True, 'budget_validated': False, 'budget_activated': False,
        'spatial_estimator_proposal_per_direction_relative': .0012,
        'primary_FEM_backend_for_preparation': 'FEniCSx/PETSc candidate; exact isolated versions still to select',
        'minimum_implementation_scope': 'rectangle P2 Poisson and periodic P2/P1 Stokes; flat75 and two MMS only',
        'minimal_problem_count': 18, 'base_problem_count': 12,
        'algebraic_repeat_count': 4, 'quadrature_repeat_count': 2,
        'largest_raw_Stokes_dof_count': max_dof,
        'sparse_memory_scenario_GiB': sparse,
        'candidate_available_RAM_GiB': 4, 'candidate_total_disk_GiB': 4,
        'candidate_trial_time_allocation_hours': 2,
        'resource_numbers_are_allocations_and_scenarios_not_measurements': True,
        'later_stopping_pair_priority': 'G02 P/T only, after separate review; source changes not in minimum implementation',
        'later_G02_pair_work_scenario_hours': future_pair_hours,
        'deferred': ['other flat heights', 'all groove meshes and reference solves', '10 geometry coverage and scale audits',
                     '3 nonlinear NS problems', 'OpenLB stopping-control modification and all 6 stop runs',
                     '0.625nm and wide finest', 'new fit and prediction stage'],
        'new_solver_or_backend_implemented': False,
        'dependency_installation': False,
        'new_compilation_initialization_or_solve': False,
        'execution_authorized': False, 'teacher_approval_claimed': False,
        'reference_contract_frozen': False, 'new_reference_adopted': False,
        'old_narrow_grid_gate': 'FAIL', 'G4_lock_changed': False,
        'reserved_flow_results_read': False,
        'next_action': 'prepare isolated backend/version and static interface package for 18 benchmarks only when implementation is requested',
        'verified_at_utc': datetime.now(timezone.utc).isoformat()}
    dump('review_decision.json', decision)
    print(json.dumps({'protected_inputs': len(protected), 'minimal_benchmarks': 18, 'max_raw_dofs': max_dof,
                      'conditional_A_comparison_envelope_percent': budget_result['comparison_A_conservative_envelope_percent'],
                      'execution_authorized': False}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
