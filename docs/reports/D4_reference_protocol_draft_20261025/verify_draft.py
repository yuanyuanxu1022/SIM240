#!/usr/bin/env python3
"""Static review of draft tables, immutable evidence and status synchronization."""
import csv
import difflib
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
D4 = ROOT / 'CASE/D_series/D4_variable_groove_transport_20261023'


def load(p):
    return json.loads(Path(p).read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def rows(p):
    with Path(p).open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def kv(p):
    return dict(s.split('=', 1) for s in Path(p).read_text().splitlines() if '=' in s)


def main():
    protected = load(OUT / 'protected_inputs.json')
    changed = [p for p, digest in protected.items() if not Path(p).is_file() or sha(p) != digest]
    assert not changed, changed
    p = load(OUT / 'proposal.json')
    assert p['status'] == 'REVIEW_DRAFT_NOT_FROZEN_NOT_APPROVED_NOT_EXECUTABLE'
    for flag in ['execution_authorized', 'proposed_reference_contract_v2_activated', 'proposed_grid_v3_activated',
                 'model_v2_created', 'reserved_flow_results_opened', 'new_reference_adopted',
                 'new_solver_implemented', 'new_compilation_or_initialization_or_solve',
                 'launch_command_or_runtime_manifest_created', 'teacher_approval_claimed']:
        assert p[flag] is False, flag
    assert p['combined_reference_error_budget_finalized'] is False and p['total_error_bound_claimed'] is False
    assert p['wide_finest_permission'] == p['prediction_permission'] == 'HOLD'
    design = load(D4 / 'protocol/design.json')
    held = {(h, d, w) for h in design['new_prediction_test']['h_nm'] for d in design['new_prediction_test']['d_nm'] for w in design['new_prediction_test']['w_nm']}
    geometry = rows(OUT / 'geometry_coverage10.csv')
    assert len(geometry) == 10
    g = {r['geometry_id']: r for r in geometry}
    assert len(g) == 10
    known = 0
    ratios = set()
    for r in geometry:
        h, d, w = [int(r[k]) for k in ['h_nm', 'd_nm', 'w_nm']]
        assert 50 <= h <= 125 and 25 <= d <= 120 and 60 <= w <= 240
        assert (h, d, w) not in held
        assert int(r['P_nm']) == int(r['Ly_nm']) == 2*w
        assert Fraction(4, 5) <= Fraction(w, h) <= Fraction(16, 5)
        assert Fraction(1, 3) <= Fraction(d, h) <= Fraction(8, 5)
        ratios.add((Fraction(w, h), Fraction(d, h)))
        assert r['reserved_prediction_geometry'] == 'False'
        known += r['role'].startswith('existing')
    assert known == 7
    assert all((s, t) in ratios for s in [Fraction(4, 5), Fraction(16, 5)] for t in [Fraction(1, 3), Fraction(8, 5)])
    meshes = rows(OUT / 'reference_mesh_budget30.csv')
    assert len(meshes) == 30
    for r in meshes:
        x = g[r['geometry_id']]
        delta = Fraction(r['mesh_size_nm'])
        nx, nh, nd, nw = [int(Fraction(x[k])/delta) for k in ['P_nm', 'h_nm', 'd_nm', 'w_nm']]
        c = nx*nh + nw*nd
        # A polygon's boundary segments give an independent Euler count for V.
        boundary = 2*nx + 2*nh + 2*nd
        t = 2*c
        v = (t+boundary)//2 + 1
        assert v == int(r['vertices_before_constraints'])
        assert t == int(r['triangles'])
        edges = (3*t+boundary)//2
        assert edges+v == int(r['scalar_P2_dofs_before_constraints'])
        assert 2*(edges+v)+v == int(r['stokes_P2P1_dofs_before_constraints'])
    scale = rows(OUT / 'scale_audit_meshes2.csv')
    assert len(scale) == 2
    for r in scale:
        large, small = g[r['large_geometry']], g[r['small_geometry']]
        for key in ['h_nm', 'd_nm', 'w_nm', 'P_nm', 'Ly_nm']:
            assert Fraction(small[key])/Fraction(large[key]) == Fraction(2, 3)
        assert Fraction(r['small_mesh_nm_exact'])/Fraction(r['large_mesh_nm_exact']) == Fraction(2, 3)
        assert Fraction(r['expected_K_scale_fraction']) == Fraction(2, 3)**3
    stops = rows(OUT / 'stop_comparison6.csv')
    assert len(stops) == 6
    scenario = 0
    for r in stops:
        raw = kv(Path(r['original_output']) / 'result.txt')
        assert raw['run_id'] == r['original_run_id'] and int(raw['steps_completed']) == int(r['old_stop_step'])
        assert int(raw['window_steps']) == int(r['window_samples'])
        late, n, base = [int(r[k]) for k in ['common_planned_final_step', 'window_samples', 'pair_baseline_max_step']]
        assert late == base+2*n < int(r['original_maximum_step_cap'])
        assert late == p['strong_stop_common_steps'][r['geometry_id']]
        assert not r['actual_new_run_id'] and r['execution_authorized'] == 'False'
        assert math.isclose(float(r['extra_pair_tstar']), 1.5, abs_tol=1e-12)
        assert r['is_runtime_prediction_or_guaranteed_bound'] == 'False'
        scenario += float(r['constant_cost_per_step_scenario_hours'])
    for gid in ['G01', 'G02', 'G04']:
        pair = [r for r in stops if r['geometry_id'] == gid]
        assert len(pair) == 2 and {r['direction'] for r in pair} == {'P', 'T'}
        assert len({r['common_planned_final_step'] for r in pair}) == 1
        assert int(pair[0]['pair_baseline_max_step']) == max(int(r['old_stop_step']) for r in pair)
    resource = load(OUT / 'resource_comparison.json')
    assert math.isclose(scenario, resource['stop_constant_cost_per_step_scenario_total_hours'], abs_tol=1e-12)
    assert resource['linear_reference_solve_counts']['total_before_audit_repeats'] == 84
    assert resource['core_plus_matched_scale_linear_solves'] == 88
    assert resource['reference_mesh_largest_stokes_dofs_before_constraints'] == max(int(r['stokes_P2P1_dofs_before_constraints']) for r in meshes)
    assert resource['reference_FE_time_measured'] is False
    assert resource['automatic_batch_progression'] is False
    states, sections = {}, []
    for name in ['SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md']:
        target = ROOT / 'docs/reports' / name
        before, after = (OUT / (name + '.before')).read_text(), target.read_text()
        def partition(t):
            start = t.index('\n## ')
            end = t.index('\n## ', start+1)
            return t[:start], t[start:end], t[end:]
        bh, _, bt = partition(before)
        ah, section, at = partition(after)
        assert bh == ah and bt == at
        assert 'D4_reference_protocol_draft_20261025' in section and 'HOLD' in section and '未启动' in section
        sections.append(section)
        states[name] = {'before_sha256': sha(OUT / (name + '.before')), 'after_sha256': sha(target), 'other_sections_unchanged': True}
        (OUT / (name + '.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=name+'.before', tofile=name)))
    assert sections[0] == sections[1]
    dump('state_sync.json', states)
    links = []
    for name in ['README.md', 'REFERENCE_METHOD_DRAFT.md', 'STOP_COMPARISON_DRAFT.md', 'COVERAGE_AND_RESOURCES.md']:
        text = (OUT / name).read_text()
        for target in re.findall(r'\]\(([^)]+)\)', text):
            if target.startswith(('https://', 'http://', '#')):
                continue
            # verification.json is the current output, populated after these checks.
            if target != 'verification.json':
                assert (OUT / target.split('#')[0]).resolve().exists(), (name, target)
            links.append({'document': name, 'target': target})
    lock = ROOT / 'docs/reports/Correlation_selection_freeze_20261024/candidate_lock.json'
    assert sha(lock) == '08ae91994910e98afd701143928a5186a9b22d003c96f73d9643c2eb11d810dc'
    result = {'ok': True, 'checked_at_utc': datetime.now(timezone.utc).isoformat(),
              'protected_paths': len(protected), 'changed_protected_paths': changed,
              'geometries': len(geometry), 'known_geometry_count': known, 'new_development_geometry_count': 10-known,
              'reserved_geometry_overlap_count': 0, 'base_mesh_budgets': len(meshes), 'matched_scale_meshes': len(scale),
              'stop_rows': len(stops), 'common_step_arithmetic_and_old_binding_checked': True,
              'linear_problem_core_count': 84, 'linear_core_plus_scale_count': 88,
              'additional_audit_repeats_and_3_nonlinear_problems_separate': True,
              'mesh_counts_checked_with_independent_boundary_Euler_identity': True,
              'no_implementation_or_compilation_or_physical_solve': True,
              'no_reference_model_or_threshold_adopted': True,
              'no_execution_manifest_or_launch_command': True,
              'FE_backend_ready': False, 'combined_reference_error_budget_finalized': False,
              'old_narrow_grid_FAIL_and_G4_preserved': True, 'future_execution': 'HOLD',
              'other_state_sections_unchanged': True, 'local_links': links,
              'human_approval_or_method_validation': 'NOT_CLAIMED'}
    dump('verification.json', result)
    dump('artifact_hashes.json', {str(f.relative_to(OUT)): sha(f) for f in OUT.rglob('*') if f.is_file() and f.name != 'artifact_hashes.json'})
    print(json.dumps({k: v for k, v in result.items() if k != 'local_links'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
