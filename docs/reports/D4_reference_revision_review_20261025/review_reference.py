#!/usr/bin/env python3
"""Read-only arithmetic review of accepted development references; never runs CFD."""
import csv
import hashlib
import json
import math
import runpy
import sys
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
OLD = ROOT / 'docs/reports/D4_grid_narrow_fine4_acceptance_20261025'
MODEL = ROOT / 'docs/reports/Correlation_selection_freeze_20261024'
D4 = ROOT / 'CASE/D_series/D4_variable_groove_transport_20261023'
D = Decimal


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def read(p):
    return json.loads(Path(p).read_text())


def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2,
                                      allow_nan=False) + '\n')


def kv(p):
    return dict(s.split('=', 1) for s in Path(p).read_text().splitlines() if '=' in s)


def table(name, rows):
    with (OUT / name).open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def scalar_model(h, d, w, fit):
    s, t = w / h, d / h
    r = t * (3 + t * (3 + t))
    lp, lt = r / 2, r / (r + 2)
    harmonic = lambda x, y: x * y / (x + y)
    et = harmonic(lt, math.exp(fit['T'][0]) * s ** fit['T'][1])
    dp = math.exp(fit['P'][0]) * s ** fit['P'][1] + s * s * t / 2
    ep = et + harmonic(lp - et, dp)
    kf = (h * 1e-9) ** 3 / 12
    return {'P': kf * (1 + ep), 'T': kf * (1 + et)}


def main():
    if (OUT / 'analysis.json').exists():
        raise SystemExit('Refuse to overwrite a completed review; use a new directory.')
    bundle = read(OLD / 'grid_review/accepted_references16.json')
    protected = dict(read(OLD / 'protection_before.json'))
    protected.update(bundle['bound_inputs_sha256'])
    for p in OLD.rglob('*'):
        if p.is_file():
            protected[str(p)] = sha(p)
    lock = read(MODEL / 'candidate_lock.json')
    assert sha(MODEL / 'candidate_lock.json') == '08ae91994910e98afd701143928a5186a9b22d003c96f73d9643c2eb11d810dc'
    for rel, digest in lock['bound_files'].items():
        p = MODEL / rel
        assert sha(p) == digest, str(p)
        protected[str(p)] = digest
    for p in [MODEL / 'candidate_lock.json', MODEL / 'candidate_lock.sha256',
              ROOT / 'AGENTS.md', D4 / 'PROTOCOL.md', D4 / 'README.md',
              D4 / 'src/variable_groove_transport.cpp']:
        protected[str(p)] = sha(p)
    changed = [p for p, digest in protected.items() if not Path(p).is_file() or sha(p) != digest]
    assert not changed, changed
    dump('protected_inputs.json', protected)
    snapshots = {}
    for name in ['SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md']:
        p = ROOT / 'docs/reports' / name
        b = p.read_bytes()
        (OUT / (name + '.before')).write_bytes(b)
        snapshots[str(p)] = hashlib.sha256(b).hexdigest()
    dump('state_before.json', snapshots)

    frozen = runpy.run_path(str(MODEL / 'frozen_models.py'))
    references = {}
    raw_audit = []
    with localcontext() as ctx:
        ctx.prec = 80
        for row in bundle['rows']:
            p = Path(row['raw_output'])
            result, cfg = kv(p / 'result.txt'), kv(p / 'run_config.txt')
            assert result['run_id'] == cfg['run_id'] == row['run_id']
            assert result['Keff_m3'] == row['K_m3']
            h, d, w = (int(row[x]) for x in ['h_nm', 'd_nm', 'w_nm'])
            dx, dr = D(row['dx_nm']), row['direction']
            key = (h, d, w, dx, dr)
            assert key not in references
            references[key] = D(result['Keff_m3'])
            volume = D(result['fluid_volume_m3']) / D(result['nominal_volume_m3']) - 1
            raw_audit.append({**{k: row[k] for k in ['planned_case_id', 'run_id', 'raw_output', 'dx_nm', 'direction']},
                              'raw_K_m3': result['Keff_m3'],
                              'fluid_to_nominal_volume_relative_difference': str(volume)})
        by_geometry = sorted(set(k[:3] for k in references))
        sensitivity = []
        maximum_scalar_rel = 0.0
        for h, d, w in by_geometry:
            values = scalar_model(h, d, w, lock['coefficients']['G4'])
            for dr in ['P', 'T']:
                expected = ((h * 1e-9) ** 3 / 12 * float(frozen['normalized'](
                    w / h, d / h, lock['coefficients']['G4'], dr)))
                maximum_scalar_rel = max(maximum_scalar_rel, abs(values[dr] / expected - 1))
            values['A'] = values['P'] / values['T']
            for q in ['P', 'T', 'A']:
                model_value = D(str(values[q]))
                qref = {}
                for dx in [D(5), D('2.5'), D('1.25')]:
                    if (h, d, w, dx, 'P') not in references or (h, d, w, dx, 'T') not in references:
                        continue
                    qref[dx] = (references[(h, d, w, dx, 'P')] / references[(h, d, w, dx, 'T')]
                                if q == 'A' else references[(h, d, w, dx, q)])
                q0 = qref[D(5)]
                e0 = model_value / q0 - 1
                for dx, ref in qref.items():
                    e = model_value / ref - 1
                    delta = q0 / ref - 1
                    reconstruction = (1 + e0) * (1 + delta) - 1
                    assert abs(e - reconstruction) < D('1e-75')
                    resistance_error = None if q == 'A' else (ref / model_value - 1) * 100
                    sensitivity.append({
                        'h_nm': h, 'd_nm': d, 'w_nm': w, 'quantity': q,
                        'dx_reference_nm': str(dx), 'locked_G4_prediction': str(model_value),
                        'numerical_reference': str(ref),
                        'signed_model_error_percent': str(e * 100),
                        'signed_coarse_reference_shift_percent': str(delta * 100),
                        'model_error_shift_from_dx5_percentage_points': str((e - e0) * 100),
                        'signed_resistance_error_percent': None if resistance_error is None else str(resistance_error),
                        'role': 'KNOWN_DEVELOPMENT_DIAGNOSTIC_NOT_RESERVED_SCORE',
                        'raw_reference_gate_reassigned': False})
        assert maximum_scalar_rel < 1e-13

        # Conditional extension of the existing three-point power law; NOT new results.
        conditional = []
        for row in read(OLD / 'independent_grid_verification.json')['records']:
            a, b, c = (D(row[k]) for k in ['Q_dx5', 'Q_dx2p5', 'Q_dx1p25'])
            ratio = abs((a - b) / (b - c))
            p = ratio.ln() / D(2).ln()
            extrapolated = c + (c - b) / (ratio - 1)
            hypothetical = c + (c - b) / ratio
            conditional.append({
                'h_nm': row['h_nm'], 'd_nm': row['d_nm'], 'w_nm': row['w_nm'],
                'quantity': row['quantity'], 'conditional_p': str(p),
                'conditional_asymptotic_Q': str(extrapolated),
                'conditional_fine_to_asymptotic_difference_percent': str(abs(c / extrapolated - 1) * 100),
                'hypothetical_Q_dx0p625_not_a_result': str(hypothetical),
                'conditional_E_1p25_to_0p625_percent': str(abs(c / hypothetical - 1) * 100),
                'conditional_E_5_to_0p625_percent': str(abs(a / hypothetical - 1) * 100),
                'conditional_E_2p5_to_0p625_percent': str(abs(b / hypothetical - 1) * 100),
                'is_error_bound': False, 'new_reference_adopted': False})

    table('locked_G4_reference_sensitivity24.csv', sensitivity)
    table('raw_reference_checks16.csv', raw_audit)
    table('conditional_refinement_diagnostics6.csv', conditional)
    draft = {
        'review_id': 'D4_REFERENCE_REVISION_REVIEW_20261025_v1',
        'status': 'REVIEW_COMPLETE_PROPOSAL_ONLY_NOT_APPROVED_OR_FROZEN',
        'old_grid_protocol': 'D4_development_grid_sensitivity_executable_20261024_v2',
        'proposed_grid_protocol': 'D4_development_grid_sensitivity_v3_DRAFT_NOT_CREATED',
        'proposed_reference_contract': 'D4_reference_contract_v2_DRAFT_NOT_ADOPTED',
        'proposed_evaluation_contract': 'D4_prediction_evaluation_v2_DRAFT_NOT_ADOPTED',
        'current_model_lock': lock['lock_id'],
        'current_model_coefficients_changed': False,
        'model_v2_created_or_fitted': False,
        'reference_strategy_recommended': 'QUALIFY_NUMERICAL_REFERENCE_BEFORE_CONTINUUM_CORRELATION_CLAIMS',
        'selected_new_dx_nm': None,
        'old_grid_thresholds_changed': False,
        'old_grid_verdict_retained': {'geometry_FAIL': 2, 'quantity_FAIL': 5, 'quantity_PASS': 1},
        'proposal_new_thresholds_activated': False,
        'preserved_v1_primary_score_reference_dx_nm': 5,
        'prospective_model_targets_percent_unchanged': {'MAE': 3, 'max_abs': 5},
        'future_numerical_budget_proposal_not_bound': {
            'P': {'maximum_reference_estimator_percent': 0.5},
            'T': {'maximum_reference_estimator_percent': 0.5},
            'A': {'maximum_reference_estimator_percent': 0.5},
            'iterative_refinement_change_percent': 0.05,
            'interpretation': 'PROPOSED_ESTIMATOR_AND_STABILITY_BUDGET_NOT_RIGOROUS_BOUND',
            'old_adjacent_mesh_targets_are_not_relabelled_uncertainty': True},
        'prediction_results_opened': False,
        'exposure_record': '16 already accepted development direction references read; no reserved flow results read; external exposure not verified',
        'wide_finest_execution_released': False,
        'prediction_execution_released': False,
        'solver_started': False,
        'teacher_approval_claimed': False,
        'new_launch_command_delivered': False,
        'required_before_future_execution': [
            'choose physical continuum correlation or fixed-resolution emulator objective',
            'static audit of reference extraction, corner/wall representation, mesh geometry and stopping error',
            'choose and approve method for qualifying reference estimators with extra independent evidence',
            'approve reference mesh strategy, domain coverage, budgets and resource ceiling',
            'freeze new grid/reference/evaluation versions before new results; preserve old FAIL',
            'separate user authorization and execution review; no automatic next-stage permission']}
    dump('revision_proposal.json', draft)
    summary = {
        'review_id': draft['review_id'], 'checked_at_utc': datetime.now(timezone.utc).isoformat(),
        'protected_input_paths': len(protected), 'raw_direction_records': len(raw_audit),
        'geometries': len(by_geometry), 'locked_model_comparison_rows': len(sensitivity),
        'narrow_comparison_rows': sum(r['w_nm'] == 60 for r in sensitivity),
        'wide_two_grid_comparison_rows': sum(r['w_nm'] == 240 for r in sensitivity),
        'conditional_diagnostic_rows': len(conditional),
        'maximum_scalar_frozen_model_relative_difference': maximum_scalar_rel,
        'maximum_fluid_nominal_volume_relative_difference': max(abs(float(r['fluid_to_nominal_volume_relative_difference'])) for r in raw_audit),
        'reference_change_identity_verified': True,
        'no_new_fit': True, 'no_new_reference_adopted': True, 'no_solver_started': True,
        'old_narrow_grid_target': 'FAIL', 'future_execution': 'HOLD',
        'physical_formula_validated': False,
        'formula_error_vs_continuum_identified': False}
    dump('analysis.json', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
