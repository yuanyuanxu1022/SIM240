#!/usr/bin/env python3
"""Check immutable inputs, audit arithmetic, source pointers and state boundaries."""
import csv
import difflib
import hashlib
import json
import math
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
OLD = ROOT / 'docs/reports/D4_grid_narrow_fine4_acceptance_20261025'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(p):
    return json.loads(Path(p).read_text())


def rows(p):
    with Path(p).open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    protected = load(OUT / 'protected_inputs.json')
    changed = [p for p, h in protected.items() if not Path(p).is_file() or sha(p) != h]
    assert not changed, changed
    lock = ROOT / 'docs/reports/Correlation_selection_freeze_20261024/candidate_lock.json'
    assert sha(lock) == '08ae91994910e98afd701143928a5186a9b22d003c96f73d9643c2eb11d810dc'
    geom = rows(OUT / 'geometry_corner_summary8.csv')
    assert len(geom) == 8
    for r in geom:
        expected = 4 * round(float(r['Ly_nm']) / float(r['dx_nm']))
        assert int(r['setter_missing_neighbour_branch_links_static']) == expected
        assert int(r['corner_intersection_links']) == expected
        assert int(r['fluid_to_fluid_corner_touch_links_static']) == expected
        assert r['setter_branch_changes_analytical_q_links'] == r['audit_q_gt_half_missing_neighbour_links'] == '0'
        assert float(r['actual_installed_q_min']) == float(r['actual_installed_q_max']) == .5
    for loc in load(OUT / 'source_locators.json'):
        assert sha(loc['path']) == loc['sha256']
        assert 1 <= loc['first_line'] <= loc['last_line'] <= len(Path(loc['path']).read_text().splitlines())
    raw = {r['run_id']: r for r in load(OLD / 'grid_review/accepted_references16.json')['rows']}
    count = 0
    terminal_window_samples = 0
    for r in rows(OUT / 'stopping_evidence16.csv'):
        series = rows(Path(raw[r['run_id']]['raw_output']) / 'diagnostics.csv')
        n = int(r['window_samples'])
        j = [float(z['J']) for z in series[-n:]]
        relative_std = statistics.stdev(j) / abs(statistics.fmean(j))
        assert math.isclose(relative_std, float(r['final_std_relative']), rel_tol=1e-8, abs_tol=1e-14)
        assert r['post_stop_samples_available'] == '0'
        assert r['verified_stricter_stop_resolve'] == r['terminal_error_bound_established'] == 'False'
        assert int(series[-1]['step']) == int(r['steps'])
        count += len(series)
        terminal_window_samples += n
    transport = rows(OUT / 'transport_checks16.csv')
    assert len(transport) == 16
    for r in transport:
        assert abs(float(r['J_to_K_relative_difference'])) < 1e-13
        assert abs(float(r['slice_relative_difference'])) < 2e-8
        assert abs(float(r['R_to_K_identity_relative_difference'])) < 1e-13
        assert r['half_step_is_error_correction_to_remove'] == 'False'
        # Independently check actual saved slice locations on half-cell centres.
        info = raw[r['run_id']]
        p = Path(info['raw_output'])
        profile = rows(p / 'field_slice.csv')
        dx = float(info['dx_nm']) * 1e-9
        nx = round(float(info['P_nm']) / float(info['dx_nm']))
        nh = round(float(info['h_nm']) / float(info['dx_nm']))
        nd = round(float(info['d_nm']) / float(info['dx_nm']))
        nw = round(float(info['w_nm']) / float(info['dx_nm']))
        edge = (nx - nw) // 2
        expected = {(ix, iz) for ix in range(nx) for iz in range(nh + nd) if iz < nh or edge <= ix < edge + nw}
        actual = set()
        for z in profile:
            xscaled, zscaled = float(z['x']) / dx - .5, float(z['z']) / dx - .5
            ix, iz = round(xscaled), round(zscaled)
            assert abs(xscaled - ix) < 1e-9 and abs(zscaled - iz) < 1e-9
            actual.add((ix, iz))
        assert len(profile) == len(actual) and actual == expected
    smooth = rows(OUT / 'smooth_quadrature_decomposition6.csv')
    assert len(smooth) == 6
    for r in smooth:
        h = float(r['h_nm'])
        assert math.isclose(float(r['analytic_midpoint_quadrature_percent']), 50 * (5 / h)**2, abs_tol=1e-10)
        assert math.isclose(float(r['observed_K_error_percent']), float(r['analytic_midpoint_quadrature_percent']) + float(r['LBM_vs_sampled_analytic_contribution_percentage_points']), abs_tol=1e-8)
    checklist = [
        {'id': 'R01', 'revision': 'audit branch semantics and unchanged half-link q', 'existing_evidence': 'COMPLETE_STATIC_CLARIFICATION', 'implementation_or_new_solver': 'NOT_DONE_NOT_AUTHORIZED'},
        {'id': 'R02', 'revision': 'preserve transport definition; separate quadrature diagnostics', 'existing_evidence': '16_TRANSPORT_AND_6_SMOOTH_CHECKED', 'implementation_or_new_solver': 'NO_NEW_EXTRACTOR_ADOPTED'},
        {'id': 'R03', 'revision': 'prospective same-discretization stronger-stop comparison', 'existing_evidence': 'POST_STOP_DATA_ABSENT', 'implementation_or_new_solver': 'DRAFT_REQUIRED_NO_RUN'},
        {'id': 'R04', 'revision': 'independent cross-section reference and domain coverage design', 'existing_evidence': 'REFERENCE_ACCURACY_NOT_QUALIFIED', 'implementation_or_new_solver': 'DRAFT_REQUIRED_NO_RUN'},
        {'id': 'R05', 'revision': 'version references evaluation and any future model separately', 'existing_evidence': 'G4_V1_AND_OLD_FAIL_PRESERVED', 'implementation_or_new_solver': 'NO_NEW_MODEL_OR_RELEASE'}]
    with (OUT / 'minimum_revision_items.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(checklist[0]))
        w.writeheader()
        w.writerows(checklist)
    state, sections = {}, []
    for name in ['SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md']:
        p = ROOT / 'docs/reports' / name
        before, after = (OUT / (name + '.before')).read_text(), p.read_text()
        def split(t):
            start = t.index('\n## ')
            end = t.index('\n## ', start + 1)
            return t[:start], t[start:end], t[end:]
        bh, _, bt = split(before)
        ah, current, at = split(after)
        assert bh == ah and bt == at
        assert 'D4_reference_static_audit_20261025' in current
        assert '不启动计算' in current and '未改求解器' in current and 'FAIL' in current and 'HOLD' in current
        sections.append(current)
        state[name] = {'before_sha256': sha(OUT / (name + '.before')), 'after_sha256': sha(p), 'other_sections_identical': True}
        (OUT / (name + '.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=name + '.before', tofile=name)))
    assert sections[0] == sections[1]
    dump('state_sync.json', state)
    links = []
    for name in ['REPORT.md', 'MINIMUM_REVISION_LIST.md']:
        for target in re.findall(r'\]\(([^)]+)\)', (OUT / name).read_text()):
            if target.startswith(('http://', 'https://', '#')):
                continue
            assert (OUT / target.split('#')[0]).resolve().exists(), target
            links.append({'file': name, 'target': target})
    result = {'ok': True, 'checked_at_utc': datetime.now(timezone.utc).isoformat(),
              'protected_paths': len(protected), 'changed_protected_paths': changed,
              'unique_meshes': 8, 'raw_development_direction_records': 16,
              'diagnostic_rows_read': count, 'terminal_window_samples_independently_checked': terminal_window_samples,
              'actual_saved_slice_node_sets_checked': 16, 'smooth_direction_records': 6,
              'minimum_revision_items': len(checklist),
              'static_corner_branch_counts_are_not_runtime_instrumentation': True,
              'changed_installed_analytical_q_by_static_missing_neighbour_branch': 0,
              'new_time_integration_or_initialization': False,
              'new_reference_or_model_or_threshold_adopted': False,
              'prior_gate_and_G4_lock_preserved': True,
              'stricter_stop_evidence_still_absent': True,
              'future_execution': 'HOLD', 'state_other_sections_preserved': True,
              'local_links': links, 'human_scientific_approval': 'NOT_CLAIMED'}
    dump('verification.json', result)
    dump('artifact_hashes.json', {str(p.relative_to(OUT)): sha(p) for p in OUT.rglob('*') if p.is_file() and p.name != 'artifact_hashes.json'})
    print(json.dumps({k: v for k, v in result.items() if k not in ['local_links']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
