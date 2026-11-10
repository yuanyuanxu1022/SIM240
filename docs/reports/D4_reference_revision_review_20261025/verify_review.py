#!/usr/bin/env python3
"""Verify local review arithmetic, unchanged evidence and bounded state edits."""
import csv
import difflib
import hashlib
import json
import re
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
D = Decimal


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return json.loads(Path(p).read_text())


def rows(p):
    return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))


def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2,
                                      allow_nan=False) + '\n')


def main():
    protected = read(OUT / 'protected_inputs.json')
    changed = [p for p, h in protected.items() if not Path(p).is_file() or sha(p) != h]
    assert not changed, changed
    assert sha(MODEL / 'candidate_lock.json') == '08ae91994910e98afd701143928a5186a9b22d003c96f73d9643c2eb11d810dc'
    lock = read(MODEL / 'candidate_lock.json')
    for rel, h in lock['bound_files'].items():
        assert sha(MODEL / rel) == h
    frozen = runpy.run_path(str(MODEL / 'frozen_models.py'))
    raw = rows(OUT / 'raw_reference_checks16.csv')
    sensitivity = rows(OUT / 'locked_G4_reference_sensitivity24.csv')
    assert len(raw) == 16 and len(sensitivity) == 24
    byid = {r['run_id']: r for r in read(OLD / 'grid_review/accepted_references16.json')['rows']}
    for r in raw:
        assert r['raw_K_m3'] == byid[r['run_id']]['K_m3']
        assert r['raw_output'] == byid[r['run_id']]['raw_output']
    maximum = D(0)
    with localcontext() as ctx:
        ctx.prec = 80
        for r in sensitivity:
            h, d, w = (int(r[k]) for k in ['h_nm', 'd_nm', 'w_nm'])
            q = r['quantity']
            norm = {dr: float(frozen['normalized'](w / h, d / h, lock['coefficients']['G4'], dr)) for dr in ['P', 'T']}
            model = norm['P'] / norm['T'] if q == 'A' else (h * 1e-9) ** 3 / 12 * norm[q]
            assert abs(model / float(r['locked_G4_prediction']) - 1) < 1e-13
            e = D(r['signed_model_error_percent']) / 100
            ref = D(r['numerical_reference'])
            assert abs(e - (D(r['locked_G4_prediction']) / ref - 1)) < D('1e-75')
            coarse = next(z for z in sensitivity if [z[k] for k in ['h_nm', 'd_nm', 'w_nm', 'quantity']] == [r[k] for k in ['h_nm', 'd_nm', 'w_nm', 'quantity']] and z['dx_reference_nm'] == '5')
            e0 = D(coarse['signed_model_error_percent']) / 100
            delta = D(coarse['numerical_reference']) / ref - 1
            maximum = max(maximum, abs(e - ((1 + e0) * (1 + delta) - 1)))
            assert abs(e - e0 - D(r['model_error_shift_from_dx5_percentage_points']) / 100) < D('1e-75')
            if q != 'A':
                assert abs(D(r['signed_resistance_error_percent']) / 100 + e / (1 + e)) < D('1e-75')
            assert r['role'] == 'KNOWN_DEVELOPMENT_DIAGNOSTIC_NOT_RESERVED_SCORE'
        assert maximum < D('1e-75')
        u = D('.005')
        budget = {
            'assumption': 'illustration only; a rigorous uniform reference bound u is NOT established',
            'u_relative': str(u),
            '3percent_observed_conditional_total_percent': str((D('.03') + (1 + D('.03')) * u) * 100),
            '5percent_observed_conditional_total_percent': str((D('.05') + (1 + D('.05')) * u) * 100),
            'sufficient_observed_for_3percent_total_percent': str((D('.03') - u) / (1 + u) * 100),
            'sufficient_observed_for_5percent_total_percent': str((D('.05') - u) / (1 + u) * 100),
            'A_bound_from_two_direction_bounds_percent': str(2 * u / (1 - u) * 100),
            'R_bound_from_K_bound_percent': str(u / (1 - u) * 100),
            'original_thresholds_modified': False,
            'original_5nm_reference_replaced': False}
        dump('budget_identity_examples.json', budget)
    proposal = read(OUT / 'revision_proposal.json')
    assert proposal['old_grid_verdict_retained'] == {'geometry_FAIL': 2, 'quantity_FAIL': 5, 'quantity_PASS': 1}
    for flag in ['old_grid_thresholds_changed', 'model_v2_created_or_fitted',
                 'current_model_coefficients_changed', 'proposal_new_thresholds_activated',
                 'prediction_results_opened', 'solver_started', 'wide_finest_execution_released',
                 'prediction_execution_released', 'new_launch_command_delivered']:
        assert proposal[flag] is False, flag
    assert proposal['selected_new_dx_nm'] is None
    state_sync = {}
    sections = []
    for name in ['SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md']:
        p = ROOT / 'docs/reports' / name
        before = (OUT / (name + '.before')).read_text()
        after = p.read_text()
        # Only replace the first current D4 section, preserve all following sections.
        def tail(t):
            first = t.index('\n## ')
            return t[t.index('\n## ', first + 1):]
        assert tail(before) == tail(after), name
        first = after.index('\n## ')
        end = after.index('\n## ', first + 1)
        sections.append(after[first:end])
        assert 'D4_reference_revision_review_20261025' in sections[-1]
        assert '未启动' in sections[-1] and 'FAIL' in sections[-1]
        (OUT / (name + '.diff')).write_text(''.join(difflib.unified_diff(
            before.splitlines(True), after.splitlines(True), fromfile=name + '.before', tofile=name)))
        state_sync[str(p)] = {'before_sha256': sha(OUT / (name + '.before')),
                              'after_sha256': sha(p), 'remaining_sections_byte_equal': True}
    assert sections[0] == sections[1]
    dump('state_sync.json', state_sync)
    local_links = []
    for name in ['REPORT.md', 'REVISION_PLAN.md']:
        text = (OUT / name).read_text()
        for target in re.findall(r'\]\(([^)]+)\)', text):
            if target.startswith(('https://', 'http://', '#')):
                continue
            p = (OUT / target.split('#')[0]).resolve()
            assert p.exists(), (name, target)
            local_links.append({'document': name, 'target': target})
    dump('verification.json', {
        'ok': True, 'checked_at_utc': datetime.now(timezone.utc).isoformat(),
        'protected_paths': len(protected), 'changed_protected_paths': changed,
        'old_raw_and_protocol_and_model_unchanged': True,
        'raw_direction_records_checked': len(raw), 'model_reference_rows_checked': len(sensitivity),
        'reference_change_identity_maximum_absolute_residual': str(maximum),
        'resistance_identity_checked': True,
        'budget_examples_are_conditional_not_established_bounds': True,
        'future_execution_HOLD': True, 'new_solver_run': False,
        'refit_or_new_reference_adoption': False,
        'current_state_sections_match': True,
        'local_links_checked': len(local_links), 'local_links': local_links,
        'human_scientific_adoption': 'NOT_CLAIMED'})
    artifacts = {str(p.relative_to(OUT)): sha(p) for p in OUT.rglob('*')
                 if p.is_file() and p.name != 'artifact_hashes.json'}
    dump('artifact_hashes.json', artifacts)
    print(json.dumps({'ok': True, 'protected_paths_unchanged': len(protected),
                      'raw_direction_records': len(raw), 'model_reference_rows': len(sensitivity),
                      'local_links': len(local_links), 'state_other_sections_unchanged': True,
                      'future_execution': 'HOLD'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
