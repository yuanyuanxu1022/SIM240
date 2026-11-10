#!/usr/bin/env python3
"""Independent rational budget enclosure and static scope/state verification."""
import csv
import difflib
import hashlib
import itertools
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction as F
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(p):
    return json.loads(Path(p).read_text())


def rows(p):
    with Path(p).open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def dec(f):
    with localcontext() as ctx:
        ctx.prec = 65
        return Decimal(f.numerator)/Decimal(f.denominator)


def main():
    protected = load(OUT / 'protected_inputs.json')
    changed = [p for p, h in protected.items() if not Path(p).is_file() or sha(p) != h]
    assert not changed, changed
    decision = load(OUT / 'review_decision.json')
    for flag in ['budget_validated', 'budget_activated', 'new_solver_or_backend_implemented', 'dependency_installation',
                 'new_compilation_initialization_or_solve', 'execution_authorized', 'teacher_approval_claimed',
                 'reference_contract_frozen', 'new_reference_adopted', 'G4_lock_changed', 'reserved_flow_results_read']:
        assert decision[flag] is False, flag
    lock = ROOT / 'docs/reports/Correlation_selection_freeze_20261024/candidate_lock.json'
    assert sha(lock) == '08ae91994910e98afd701143928a5186a9b22d003c96f73d9643c2eb11d810dc'
    bs, ba, bq, bm, bt = map(F, ['.0012', '.0001', '.0001', '.0005', '.0005'])
    Rs, Cs = [], []
    for signs in itertools.product([-1, 1], repeat=5):
        es, ea, eq, em, et = [b*s for b, s in zip([bs, ba, bq, bm, bt], signs)]
        R = (1+es)*(1+ea)*(1+eq)/(1+em)
        S = 1+et
        C = 1/(S*R)
        Rs.append(R)
        Cs.append(C)
    r = (1+bs)*(1+ba)*(1+bq)/(1-bm)-1
    c = 1/((1-bt)*(1-r))-1
    ab = 2*c/(1-c)
    assert max(abs(x-1) for x in Rs) <= r
    assert max(abs(x-1) for x in Cs) <= c
    exact_ratio_extreme = max(Cs)/min(Cs)-1
    assert exact_ratio_extreme <= ab < F('.005')
    existing = load(OUT / 'budget_arithmetic.json')
    for key, value in [('reference_direction_positive_envelope_percent', r),
                       ('comparison_direction_envelope_percent', c),
                       ('comparison_A_conservative_envelope_percent', ab)]:
        assert abs(dec(100*value)-Decimal(existing[key])) < Decimal('1e-54'), key
    dump('budget_interval_verification.json', {
        'ok': True, 'method': 'exact rational extrema over 32 signed component corners',
        'component_corners': 32,
        'all_reference_factors_within_uniform_r': True,
        'all_comparison_factors_within_uniform_c': True,
        'reference_positive_envelope_percent': str(dec(100*r)),
        'comparison_direction_envelope_percent': str(dec(100*c)),
        'comparison_A_conservative_envelope_percent': str(dec(100*ab)),
        'actual_extreme_A_factor_percent_over_conditional_boxes': str(dec(100*exact_ratio_extreme)),
        'assumptions_proven_in_real_fluid_data': False,
        'old_LBM_space_error_or_infinite_time_tail_bounded': False,
        'new_solver_called': False})
    cases = rows(OUT / 'minimal_benchmark18.csv')
    assert len(cases) == len({r['planned_id'] for r in cases}) == 18
    assert sum(r['role'] == 'base' for r in cases) == 12
    assert sum(r['role'] == 'algebraic_repeat' for r in cases) == 4
    assert sum(r['role'] == 'quadrature_repeat' for r in cases) == 2
    assert sum(r['problem'] == 'flat75' and r['role'] == 'base' for r in cases) == 6
    for r in cases:
        assert r['problem'] in ['flat75', 'MMS']
        assert not r['actual_run_id'] and r['authorized_to_execute'] == 'False'
        assert r['direction_or_field'] in ['P', 'T', 'scalar', 'mixed']
        if r['role'] == 'algebraic_repeat':
            assert float(r['true_relative_residual_target']) == 1e-12
        if r['role'] == 'quadrature_repeat':
            assert r['problem'] == 'MMS' and r['quadrature_degree'] == '12'
    topology = rows(OUT / 'periodic_topology6.csv')
    assert len(topology) == 6
    for r in topology:
        nx, nz = int(r['nx']), int(r['nz'])
        # Count trace points independently of the generation formula.
        p2trace = list(range(2*nz+1))
        assert len(p2trace) == int(r['P2_trace_nodes_each_periodic_face'])
        assert len([z for z in p2trace if z not in [0, 2*nz]]) == int(r['free_P2_trace_pairs_after_wall_values'])
        assert len(range(nz+1)) == int(r['P1_pressure_trace_pairs'])
        v = (nx+1)*(nz+1)
        t = 2*nx*nz
        e = (3*t+2*nx+2*nz)//2
        assert e+v == int(r['scalar_P2_dofs_before_constraints'])
        assert 2*(e+v)+v == int(r['Stokes_P2P1_dofs_before_constraints'])
    assert max(int(r['Stokes_P2P1_dofs_before_constraints']) for r in topology) == decision['largest_raw_Stokes_dof_count'] == 104943
    pc = load(OUT / 'pressure_periodic_static_checks.json')
    assert pc['PDE_solved'] is False
    assert pc['MMS_sample_max_periodic_trace_difference'] < 1e-14
    assert pc['MMS_sample_max_divergence'] == pc['MMS_sample_max_wall_speed'] == 0
    state, sections = {}, []
    for name in ['SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md']:
        target = ROOT / 'docs/reports' / name
        before, after = (OUT / (name+'.before')).read_text(), target.read_text()
        def parts(t):
            first = t.index('\n## ')
            second = t.index('\n## ', first+1)
            return t[:first], t[first:second], t[second:]
        bh, _, bt0 = parts(before)
        ah, section, at = parts(after)
        assert bh == ah and bt0 == at
        assert 'D4_reference_protocol_review_20261025' in section and '未启动' in section and 'HOLD' in section
        sections.append(section)
        state[name] = {'before_sha256': sha(OUT/(name+'.before')), 'after_sha256': sha(target), 'other_sections_unchanged': True}
        (OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=name+'.before', tofile=name)))
    assert sections[0] == sections[1]
    dump('state_sync.json', state)
    links = []
    for name in ['REPORT.md', 'MINIMUM_SCOPE.md']:
        text = (OUT/name).read_text()
        for ref in re.findall(r'\]\(([^)]+)\)', text):
            if ref.startswith(('https://', 'http://', '#')):
                continue
            assert (OUT/ref.split('#')[0]).resolve().exists(), (name, ref)
            links.append({'file': name, 'target': ref})
    verification = {
        'ok': True, 'verified_at_utc': datetime.now(timezone.utc).isoformat(),
        'protected_paths': len(protected), 'changed_protected_paths': changed,
        'minimum_benchmarks': 18, 'base_problems': 12, 'audit_repeats': 6,
        'rational_budget_corners_checked': 32,
        'pressure_periodic_checks_are_analytic_not_backend_validation': True,
        'budget_proposal_arithmetically_consistent': True,
        'physical_budget_validated_or_reference_certified': False,
        'old_LBM_grid_error_or_late_time_tail_not_absorbed': True,
        'no_dependency_install_or_solver_implementation': True,
        'no_compilation_initialization_or_physical_solve': True,
        'no_reference_model_or_protocol_frozen': True,
        'old_G4_and_narrow_grid_FAIL_preserved': True,
        'wide_finest_and_prediction': 'HOLD',
        'other_state_sections_preserved': True, 'local_links': links,
        'teacher_approval': 'NOT_CLAIMED'}
    dump('verification.json', verification)
    dump('artifact_hashes.json', {str(f.relative_to(OUT)): sha(f) for f in OUT.rglob('*') if f.is_file() and f.name != 'artifact_hashes.json'})
    print(json.dumps({k: v for k, v in verification.items() if k != 'local_links'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
