#!/usr/bin/env python3
"""Audit existing geometry, transport extraction and stopping evidence; no solver."""
import csv
import hashlib
import itertools
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
PREVIOUS = ROOT / 'docs/reports/D4_reference_revision_review_20261025'
ACCEPT = ROOT / 'docs/reports/D4_grid_narrow_fine4_acceptance_20261025'
FOUND = ROOT / 'docs/reports/D4_foundation_acceptance_20261023'
D4 = ROOT / 'CASE/D_series/D4_variable_groove_transport_20261023'


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def load(p):
    return json.loads(Path(p).read_text())


def kv(p):
    return dict(s.split('=', 1) for s in Path(p).read_text().splitlines() if '=' in s)


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def table(name, records):
    with (OUT / name).open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)


def geometry(cfg, raw):
    h, d, w, period, ly, dx = [float(cfg[k]) for k in ['h_nm', 'd_nm', 'w_nm', 'period_nm', 'Ly_nm', 'dx_nm']]
    nx, ny, nh, nd = [round(v / dx) for v in [period, ly, h, d]]
    edge, end = (period - w) / (2 * dx), (period + w) / (2 * dx)
    xx, zz = np.meshgrid(np.arange(nx) + .5, np.arange(nh + nd) + .5, indexing='ij')

    def fluid(x, z):
        x = x % nx
        return (z >= 0) & (z < nh + nd * ((x >= edge) & (x < end)))

    mask = fluid(xx, zz)
    counts = {'candidate_links': 0, 'corner_intersection_links': 0,
              'setter_missing_neighbour_branch_links_static': 0,
              'audit_q_gt_half_missing_neighbour_links': 0,
              'setter_branch_changes_analytical_q_links': 0,
              'fluid_to_fluid_corner_touch_links_static': 0}
    examples = []
    for cx, cy, cz in itertools.product([-1, 0, 1], repeat=3):
        if cx * cx + cy * cy + cz * cz not in (1, 2):
            continue
        hit = mask & ~fluid(xx + cx, zz + cz)
        mx, mz = (xx + .5 * cx) % nx, zz + .5 * cz
        bottom = mz == 0
        if nd:
            mesa = (mz == nh) & ((mx <= edge) | (mx >= end))
            roof = (mz == nh + nd) & (mx >= edge) & (mx <= end)
            side = ((mx == edge) | (mx == end)) & (mz >= nh) & (mz <= nh + nd)
            faces = bottom.astype(int) + mesa.astype(int) + roof.astype(int) + side.astype(int)
        else:
            faces = bottom.astype(int) + (mz == nh).astype(int)
        assert np.all(faces[hit] >= 1), 'a candidate ray lacks its exact half-link intersection'
        missing = hit & ~fluid(xx - cx, zz - cz)
        touch = mask & fluid(xx + cx, zz + cz) & (faces >= 2)
        counts['candidate_links'] += int(hit.sum()) * ny
        counts['corner_intersection_links'] += int((hit & (faces >= 2)).sum()) * ny
        counts['setter_missing_neighbour_branch_links_static'] += int(missing.sum()) * ny
        counts['fluid_to_fluid_corner_touch_links_static'] += int(touch.sum()) * ny
        if missing.any() and len(examples) < 4:
            ix, iz = np.argwhere(missing)[0]
            examples.append({'x_nm': float(xx[ix, iz] * dx), 'z_nm': float(zz[ix, iz] * dx),
                             'direction': [cx, cy, cz], 'analytical_q': .5,
                             'setter_assigned_q': .5, 'is_live_runtime_trace': False})
    assert int(mask.sum()) * ny == int(raw['fluid_nodes'])
    assert counts['candidate_links'] == int(raw['candidate_links']) == int(raw['installed_links'])
    return {'h_nm': h, 'd_nm': d, 'w_nm': w, 'P_nm': period, 'Ly_nm': ly,
            'dx_nm': dx, 'fluid_nodes': int(mask.sum()) * ny, **counts,
            'all_candidate_midpoints_on_closed_wall_facets': True,
            'actual_installed_q_min': float(raw['q_min']),
            'actual_installed_q_max': float(raw['q_max']),
            'examples': examples}


def main():
    if (OUT / 'analysis.json').exists():
        raise SystemExit('Refuse overwrite; create a new audit version.')
    protected = dict(load(PREVIOUS / 'protected_inputs.json'))
    for directory in [PREVIOUS, FOUND / 'complete']:
        for p in directory.rglob('*'):
            if p.is_file():
                protected[str(p)] = sha(p)
    foundation = load(FOUND / 'complete/field_cases.json')
    # Validate the recorded foundation scalar inputs, including raw profiles/diagnostics.
    for path, digest in load(FOUND / 'complete/input_hashes.json').items():
        p = Path(path) if Path(path).is_absolute() else ROOT / path
        assert sha(p) == digest, str(p)
        protected[str(p)] = digest
    sources = [
        (D4 / 'src/variable_groove_transport.cpp', [(108, 141), (192, 222), (254, 347), (380, 468), (500, 562), (671, 707), (746, 758), (799, 898)]),
        (Path('/home/dell/openlb/src/boundary/setBouzidiBoundary.h'), [(47, 80), (241, 310)]),
        (Path('/home/dell/openlb/src/dynamics/dynamics.h'), [(223, 230)]),
        (Path('/home/dell/openlb/src/dynamics/forcing.h'), [(36, 67)]),
        (Path('/home/dell/openlb/src/dynamics/momenta/elements.h'), [(1593, 1608)]),
        (D4 / 'development_grid_narrow_fine4_20261024/analyze_results.py', [(88, 131)])]
    extracts, locators = [], []
    for p, ranges in sources:
        protected.setdefault(str(p), sha(p))
        lines = p.read_text().splitlines()
        for start, end in ranges:
            locators.append({'path': str(p), 'first_line': start, 'last_line': end, 'sha256': sha(p)})
            extracts.append(f'\nSOURCE {p}:{start}-{end}\n' + '\n'.join(f'{i}: {lines[i-1]}' for i in range(start, end + 1)))
    changed = [p for p, h in protected.items() if not Path(p).is_file() or sha(p) != h]
    assert not changed, changed
    dump('protected_inputs.json', protected)
    dump('source_locators.json', locators)
    (OUT / 'source_excerpts.txt').write_text('\n'.join(extracts) + '\n')
    for name in ['SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md']:
        (OUT / (name + '.before')).write_bytes((ROOT / 'docs/reports' / name).read_bytes())
    refs = load(ACCEPT / 'grid_review/accepted_references16.json')['rows']
    transport, stopping, geometries = [], [], {}
    for row in refs:
        p = Path(row['raw_output'])
        raw, cfg = kv(p / 'result.txt'), kv(p / 'run_config.txt')
        assert raw['run_id'] == cfg['run_id'] == row['run_id']
        key = tuple(cfg[k] for k in ['h_nm', 'd_nm', 'w_nm', 'period_nm', 'Ly_nm', 'dx_nm'])
        if key not in geometries:
            geometries[key] = geometry(cfg, raw)
        b = kv(p / 'boundary_audit.txt')
        assert float(b['installed_q_min']) == float(b['installed_q_max']) == .5
        assert b['geometric_fallback_count'] == b['missing_fluid_neighbour_fallback_count'] == b['unresolved_link_count'] == '0'
        data = np.genfromtxt(p / 'diagnostics.csv', delimiter=',', names=True)
        n = int(raw['window_steps'])
        j = data['J']
        assert len(data) == int(raw['steps_completed']) + 1 and len(j) >= 2 * n
        tail, previous = j[-n:], j[-2*n:-n]
        mean = math.fsum(tail) / n
        std = math.sqrt(math.fsum((float(z) - mean) ** 2 for z in tail) / (n - 1)) / abs(mean)
        span = float(np.ptp(tail)) / abs(mean)
        cross = data['Jx'] if cfg['direction'] == 'P' else data['Jy']
        assert std <= 1e-6 and span <= 5e-6 and np.max(np.abs(cross[-n:])) <= 1e-12
        assert math.isclose(std, float(raw['window_main_rel_std']), rel_tol=1e-6, abs_tol=1e-14)
        half = n // 2
        stop = {'run_id': raw['run_id'], 'h_nm': cfg['h_nm'], 'd_nm': cfg['d_nm'],
                'w_nm': cfg['w_nm'], 'dx_nm': cfg['dx_nm'], 'direction': cfg['direction'],
                'steps': len(j)-1, 'window_samples': n, 'dt_s': float(raw['dt_s']),
                'window_tstar_sample_span': (n - 1) * float(raw['dt_s']) * float(raw['nu_phys_m2_s']) / float(raw['mesa_gap_m'])**2,
                'final_std_relative': std, 'final_span_relative': span,
                'terminal_to_last_window_mean_percent': 100 * (float(j[-1]) / mean - 1),
                'last_window_endpoint_change_percent': 100 * (float(tail[-1]) / float(tail[0]) - 1),
                'last_half_mean_change_percent': 100 * (float(np.mean(tail[half:])) / float(np.mean(tail[:half])) - 1),
                'last_to_previous_window_mean_change_percent': 100 * (mean / (math.fsum(previous) / n) - 1),
                'post_stop_samples_available': 0, 'verified_stricter_stop_resolve': False,
                'terminal_error_bound_established': False}
        stopping.append(stop)
        nu, a = float(raw['nu_phys_m2_s']), float(raw['acceleration_m_s2'])
        rho, mu = float(raw['rho_phys_kg_m3']), float(raw['mu_phys_Pa_s'])
        dx, h, d, w = [float(raw[k]) for k in ['dx_m', 'mesa_gap_m', 'groove_depth_m', 'groove_width_m']]
        period, ly = float(raw['Lx_m']), float(raw['Ly_m'])
        k = nu * float(j[-1]) / a
        rv = rho * a / float(j[-1])
        field = np.genfromtxt(p / 'field_slice.csv', delimiter=',', names=True)
        component = 'uy' if cfg['direction'] == 'P' else 'ux'
        kslice = nu / a * math.fsum(field[component]) * dx**2 / period
        href = h + w / period * d
        kmean = nu / a * href * (float(j[-1]) / href)
        half_step_contribution = nu * float(raw['dt_s']) / 2 * href
        record = {'run_id': raw['run_id'], 'direction': cfg['direction'], 'h_nm': cfg['h_nm'],
                  'd_nm': cfg['d_nm'], 'w_nm': cfg['w_nm'], 'dx_nm': cfg['dx_nm'],
                  'K_raw_m3': float(raw['Keff_m3']), 'K_recomputed_m3': k,
                  'K_from_slice_m3': kslice,
                  'slice_relative_difference': kslice/k-1,
                  'J_to_K_relative_difference': k/float(raw['Keff_m3'])-1,
                  'R_to_K_identity_relative_difference': rv*k/mu-1,
                  'Href_m': href,
                  'Href_relative_difference': href/float(raw['H_ref_m'])-1,
                  'nominal_volume_relative_difference': period*ly*href/float(raw['nominal_volume_m3'])-1,
                  'forced_velocity_half_step_K_contribution_fraction': half_step_contribution/k,
                  'half_step_is_error_correction_to_remove': False}
        assert abs(record['slice_relative_difference']) <= 2e-8
        assert abs(record['J_to_K_relative_difference']) < 1e-13
        assert abs(record['R_to_K_identity_relative_difference']) < 1e-13
        assert abs(record['Href_relative_difference']) < 1e-13
        transport.append(record)
    flat_geometry = [{k: v for k, v in row.items() if k != 'examples'} for row in geometries.values()]
    dump('geometry_corner_details8.json', list(geometries.values()))
    table('geometry_corner_summary8.csv', flat_geometry)
    table('transport_checks16.csv', transport)
    table('stopping_evidence16.csv', stopping)

    smooth = []
    for case in foundation:
        if case['row']['role'] != 'smooth':
            continue
        p = ROOT / case['output']
        raw = kv(p / 'result.txt')
        nu, a, h, dx = [float(raw[k]) for k in ['nu_phys_m2_s', 'acceleration_m_s2', 'mesa_gap_m', 'dx_m']]
        period = float(raw['Lx_m'])
        data = np.genfromtxt(p / 'field_slice.csv', delimiter=',', names=True)
        dr = case['row']['direction']
        analytic_velocity = a * data['z'] * (h - data['z']) / (2 * nu)
        k_exact = h**3 / 12
        k_sampled_exact = nu/a * math.fsum(analytic_velocity) * dx**2 / period
        k_sampled_velocity = nu/a * math.fsum(data['uy' if dr == 'P' else 'ux']) * dx**2 / period
        quadrature = (k_sampled_exact/k_exact-1)*100
        observed = (float(raw['Keff_m3'])/k_exact-1)*100
        field_difference = (k_sampled_velocity-k_sampled_exact)/k_exact*100
        assert abs(quadrature - 50*(dx/h)**2) < 1e-10
        assert abs(observed - quadrature-field_difference) < 1e-8
        smooth.append({'run_id': raw['run_id'], 'h_nm': h*1e9, 'direction': dr,
                       'K_continuum_analytic_m3': k_exact,
                       'K_sampled_analytic_midpoints_m3': k_sampled_exact,
                       'K_sampled_LBM_velocity_m3': k_sampled_velocity,
                       'observed_K_error_percent': observed,
                       'analytic_midpoint_quadrature_percent': quadrature,
                       'LBM_vs_sampled_analytic_contribution_percentage_points': field_difference,
                       'decomposition_is_groove_error_correction': False})
    assert len(smooth) == 6
    table('smooth_quadrature_decomposition6.csv', smooth)
    summary = {
        'review_id': 'D4_REFERENCE_STATIC_AUDIT_20261025_v1',
        'checked_at_utc': datetime.now(timezone.utc).isoformat(),
        'protected_paths': len(protected),
        'development_direction_records': len(refs), 'unique_development_meshes': len(geometries),
        'smooth_direction_records': len(smooth),
        'setter_missing_neighbour_branch_links_per_unique_mesh': [r['setter_missing_neighbour_branch_links_static'] for r in flat_geometry],
        'setter_semantically_different_boundary_values': 0,
        'recorded_zero_fallback_means_no_q_gt_half_invalid_second_neighbour': True,
        'all_runtime_setter_branches_instrumented': False,
        'unqualified_no_fallback_statement_supported': False,
        'maximum_J_K_relative_discrepancy': max(abs(r['J_to_K_relative_difference']) for r in transport),
        'maximum_slice_K_relative_discrepancy': max(abs(r['slice_relative_difference']) for r in transport),
        'maximum_RK_mu_relative_discrepancy': max(abs(r['R_to_K_identity_relative_difference']) for r in transport),
        'maximum_terminal_window_mean_difference_percent': max(abs(r['terminal_to_last_window_mean_percent']) for r in stopping),
        'maximum_final_window_endpoint_change_percent': max(abs(r['last_window_endpoint_change_percent']) for r in stopping),
        'maximum_previous_window_mean_change_percent': max(abs(r['last_to_previous_window_mean_change_percent']) for r in stopping),
        'stricter_stop_resolve_evidence': 'ABSENT',
        'infinite_time_error_bound': 'NOT_ESTABLISHED',
        'corner_discretization_error_root_cause': 'NOT_IDENTIFIED',
        'source_or_old_protocol_or_raw_results_modified': False,
        'new_solver_initialization_or_execution': False,
        'new_fit_or_reference_adopted': False,
        'prior_numeric_geometry_saved_field_acceptance': 'PRESERVED_WITH_AUDIT_SEMANTICS_CLARIFIED',
        'old_narrow_grid_gate': 'FAIL_5_QUANTITIES_1_PASS_TWO_GEOMETRIES_FAIL',
        'wide_finest_and_prediction_execution': 'HOLD'}
    dump('analysis.json', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
