"""Read archived h25/T evidence; write only this new review directory.

No solver, build, fitter, old checker, or field-reader execution/import.
"""
from pathlib import Path
import csv
import hashlib
import itertools
import json
import math
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
BASE = ROOT / 'CASE/D_series/D2_groove_error_map'


def kv(path):
    return dict(line.split('=', 1) for line in path.read_text().splitlines() if '=' in line)


def read_csv(path):
    with path.open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(name, value):
    p = OUT / name
    assert not p.exists(), 'This report script does not overwrite evidence'
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def near(x, y, rtol=1e-10, atol=0.):
    return bool(np.allclose(x, y, rtol=rtol, atol=atol))


reviews = []
for tag, dxnm in [('h25_d100_dx5_T', 5.), ('h25_d100_dx2.5_T', 2.5)]:
    top = BASE / 'results' / tag
    run = top / 'steady'
    result = kv(run / 'result.txt')
    manifest = kv(run / 'run_manifest.txt')
    pre = kv(top / 'precheck/result.txt')
    boundary = kv(run / 'boundary_audit.txt')
    raw = read_csv(run / 'diagnostics.csv')
    data = {k: np.array([float(row[k]) for row in raw]) for k in raw[0]}
    n = len(raw)
    dx = float(result['dx_m'])
    dt = float(result['dt_s'])
    h, d, w = [float(result[k]) for k in ['mesa_gap_m', 'groove_depth_m', 'groove_width_m']]
    lx, ly = float(result['Lx_m']), float(result['Ly_m'])
    nx, ny = round(lx / dx), round(ly / dx)
    nh, nd, nw = round(h / dx), round(d / dx), round(w / dx)
    nz = nh + nd + 5

    # Independent analytic material layout and D3Q19 link count in x/z,
    # extended by exact y translational symmetry. This is not VTK readback.
    xs = (np.arange(nx) + .5) * dx
    zs = (np.arange(nz) - .5) * dx
    groove = (xs >= (lx-w)/2 - 1e-20) & (xs < (lx+w)/2 - 1e-20)
    fluid = (zs[:, None] >= 0) & (zs[:, None] < h + d*groove[None, :] - 1e-20)
    counts = [0, int(fluid.sum())*ny, nx*ny, nx*ny*nz-int(fluid.sum())*ny-nx*ny]
    links = 0
    for cx, cy, cz in itertools.product([-1, 0, 1], repeat=3):
        if not (0 < abs(cx)+abs(cy)+abs(cz) <= 2):
            continue
        neighbor = np.roll(fluid, shift=(-cz, -cx), axis=(0, 1))
        links += int((fluid & ~neighbor).sum()) * ny

    main = data['Jx']
    cross = data['Jy']
    mass_error = (data['mass'] - data['mass'][0]) / data['mass'][0]
    denominator = np.maximum(np.abs(data['Q_section1']), np.abs(data['Q_section2']))
    sections = np.divide(np.abs(data['Q_section1']-data['Q_section2']), denominator,
                         out=np.zeros(n), where=denominator>0)
    windows = np.lib.stride_tricks.sliding_window_view(main, 1000)
    cw = np.lib.stride_tricks.sliding_window_view(cross, 1000)
    std = windows.std(axis=1, ddof=1) / np.abs(windows.mean(axis=1))
    span = np.ptp(windows, axis=1) / np.abs(windows.mean(axis=1))
    crossmax = np.abs(cw).max(axis=1)
    accepted = (std <= 1e-6) & (span <= 5e-6) & (crossmax <= 1e-12)
    hits = (np.flatnonzero(accepted) + 999).tolist()
    K = float(result['nu_phys_m2_s']) * main[-1] / float(result['acceleration_m_s2'])

    field = read_csv(run / 'field_slice.csv')
    sf = {k: np.array([float(row[k]) for row in field]) for k in field[0]}
    ix = np.rint(sf['x']/dx-.5).astype(int)
    iz = np.rint(sf['z']/dx-.5).astype(int)
    gg = (sf['x'] >= (lx-w)/2 - 1e-20) & (sf['x'] < (lx+w)/2 - 1e-20)
    Ks = float(result['nu_phys_m2_s'])/float(result['acceleration_m_s2']) * sf['ux'].sum()*dx**2/lx
    checks = {
        'independent_shell_exit_zero': int((run/'exit_code.txt').read_text()) == 0,
        'independent_precheck_shell_exit_zero': int((top/'precheck/exit_code.txt').read_text()) == 0,
        'same_binary_between_precheck_and_steady': kv(top/'precheck/run_manifest.txt')['binary_sha256'] == manifest['binary_sha256'],
        'manifest_and_result_actual_dx_match': near(float(manifest['dx_nm']), dxnm) and near(dx, dxnm*1e-9),
        'actual_steps_complete': n == int(result['steps_completed'])+1 and np.array_equal(data['step'], np.arange(n)),
        'all_diagnostic_values_finite': all(bool(np.isfinite(a).all()) for a in data.values()),
        'finite_flags_all_one': bool(np.all(data['finite'] == 1)),
        'time_axis_consistent': near(data['time_s'], data['step']*dt, atol=1e-24),
        'dt_diffusive_scaling': near(dt, (.5)*dx**2/(3*float(result['nu_phys_m2_s']))),
        'direction_main_J_consistent': near(main, data['J'], atol=1e-30),
        'mass_trajectory_recomputed': near(mass_error, data['mass_error'], atol=1e-16),
        'full_history_mass_below_original_1e_10': float(np.abs(mass_error).max()) < 1e-10,
        'full_history_density_below_original_1e_6': float(data['max_density_deviation'].max()) <= 1e-6,
        'full_history_Mach_below_original_0p05': float(data['Mach'].max()) < .05,
        'final_section_below_original_1e_5': float(sections[-1]) <= 1e-5,
        'section_trajectory_recomputed': near(sections, data['section_relative_difference'], atol=1e-15),
        'all_windows_std_recomputed': near(std, data['window_rel_std'][999:], rtol=1e-5, atol=1e-12),
        'all_windows_span_recomputed': near(span, data['window_rel_span'][999:], rtol=1e-10, atol=1e-12),
        'all_windows_cross_recomputed': near(crossmax, data['window_cross_abs_max'][999:], atol=1e-30),
        'no_early_window_values': all(bool(np.all(data[k][:999] == -1)) for k in ['window_rel_std','window_rel_span','window_cross_abs_max']),
        'first_accepted_window_is_final': hits == [n-1],
        'K_from_final_flux_matches_result': near(K, float(result['Keff_m3'])),
        'H_ref_is_volume_over_plan': near(float(result['H_ref_m']), h+w/lx*d),
        'raw_material_counts_match_analytic_layout': all(int(boundary['material_'+str(i)]) == counts[i] for i in range(4)),
        'raw_links_match_independent_D3Q19_layout': all(int(boundary[k]) == links for k in ['candidate_links','valid_distance_links','installed_links']),
        'q_summary_halfway': all(near(float(boundary[k]), .5, atol=1e-10) for k in ['q_min','q_max','installed_q_min','installed_q_max']),
        'no_fallback_or_unresolved_summary': all(int(boundary[k]) == 0 for k in ['geometric_fallback_count','missing_fluid_neighbour_fallback_count','unresolved_link_count']),
        'slice_all_finite_and_fluid': all(bool(np.isfinite(a).all()) for a in sf.values()) and bool(np.all(sf['material'] == 1)),
        'slice_count_and_unique_sites': len(field)*ny == counts[1] and len(set(zip(ix.tolist(), iz.tolist()))) == len(field),
        'slice_coordinates_match_cell_centres': near(sf['x'], (ix+.5)*dx, atol=1e-20) and near(sf['z'], (iz+.5)*dx, atol=1e-20),
        'slice_in_exact_fluid': bool(np.all((ix >= 0)&(ix < nx)&(sf['z'] >= 0)&(sf['z'] < h+d*gg))),
        'slice_flux_integral_matches_K': near(Ks, K, rtol=1e-8),
        'reported_geometry_precheck_true': all(pre[k] == 'true' for k in ['geometry_PASS','converter_PASS','q_audit_PASS']),
    }
    reviews.append({
        'tag': tag, 'case_label': result['case'], 'manifest_case_id': manifest['case_id'],
        'recorded_PASS': result['PASS'], 'original_reported_geometry_PASS': pre['geometry_PASS'],
        'manifest': manifest, 'result': result, 'checks': checks,
        'bounded_raw_consistency_checks_pass': all(checks.values()),
        'diagnostic_rows': n, 'full_windows_recomputed': len(windows), 'first_accepted_step': hits,
        'max_mass_abs_relative_recomputed': float(np.abs(mass_error).max()),
        'max_density_deviation_recomputed': float(data['max_density_deviation'].max()),
        'max_Mach_recomputed': float(data['Mach'].max()),
        'final_std_recomputed': float(std[-1]), 'final_span_recomputed': float(span[-1]),
        'final_section_relative_recomputed': float(sections[-1]),
        'K_recomputed_m3': float(K), 'K_from_y_mid_slice_m3': float(Ks),
        'slice_relative_disagreement': float(Ks/K-1),
        'material_counts_analytic': counts, 'candidate_links_analytic': links,
        'window_sample_count': 1000, 'window_endpoint_time_span_s': 999*dt,
        'final_time_s': float(data['time_s'][-1]),
        'final_tstar_based_on_h': float(data['time_s'][-1])*float(result['nu_phys_m2_s'])/h**2,
        'legacy_source_build_fields_missing_in_manifest': [k for k in ['source_sha256','generated_source_sha256','openlb_commit','compiler','compile_flags'] if k not in manifest],
        'vtk_payload_file_count': sum(1 for p in run.rglob('*') if p.is_file() and p.suffix in ['.vti','.vtu','.vtm','.pvd']),
        'qualified_reference': False,
        'scope_limit': 'archived scalar/trajectory/analytic geometry/single y-slice consistency; not historical build reconstruction, full 3D readback, formal reference or URV gate acceptance'
    })

save('two_grid_raw_review.json', reviews)
save('comparability.json', {
    'same_recorded_binary_sha256': len({r['manifest']['binary_sha256'] for r in reviews}) == 1,
    'present_ELF_matches_both_manifests': all(digest(BASE/'build/d2_groove_error_map') == r['manifest']['binary_sha256'] for r in reviews),
    'binary_sha256': digest(BASE/'build/d2_groove_error_map'),
    'same_physics_fields': {k: reviews[0]['result'][k] == reviews[1]['result'][k] for k in ['direction','Lx_m','Ly_m','mesa_gap_m','groove_depth_m','groove_width_m','H_ref_m','tau','descriptor','collision','wall_boundary','periodicity','acceleration_m_s2','rho_phys_kg_m3','nu_phys_m2_s','mu_phys_Pa_s']},
    'K_2p5_vs_5_relative_percent': 100*(reviews[1]['K_recomputed_m3']/reviews[0]['K_recomputed_m3']-1),
    'fixed_1000_samples_with_quarter_dt': True,
    'grid_evidence': 'TWO_LEVEL_JOINT_DX_DT_SENSITIVITY_NOT_ORDER_GCI_OR_ERROR_BOUND',
    'full_reference_qualified': False,
})

lockdir = ROOT/'docs/reports/Correlation_selection_freeze_20261024'
lock = json.loads((lockdir/'candidate_lock.json').read_text())
expected_lock_hash = (lockdir/'candidate_lock.sha256').read_text().split()[0]
lock_check = {
    'lock_id': lock['lock_id'], 'status': lock['status'],
    'external_hash_matches': digest(lockdir/'candidate_lock.json') == expected_lock_hash,
    'bound_files_count': len(lock['bound_files']),
    'bound_file_drifts': [p for p, h in lock['bound_files'].items() if digest(lockdir/p) != h],
    'target_domain': lock['target_domain'], 'primary': lock['primary'], 'comparators': lock['comparators'],
    'h25_d100_s_w_over_h': 120/25, 'h25_d100_t_d_over_h': 100/25,
    'h25_d100_inside_locked_target': False,
    'h25_d100_role': 'KNOWN_OLD_SUPPLEMENT_OUTSIDE_CANDIDATE_TARGET_DOMAIN_NOT_NEW_TEST',
    'reserved_prediction_results_read_this_audit': False,
    'note': 'Bound prediction files were hashed, not used with reference outcomes; this does not establish global external non-exposure or prediction acceptance.'
}
save('candidate_lock_readonly.json', lock_check)

candidates = []
old_pred_files = [ROOT/'docs/reports/bivariate_piecewise_comparison_20261022/full_fit_predictions.csv',
                  ROOT/'docs/reports/Constrained_correlation_20261023/predictions.csv']
for path in old_pred_files:
    for row in read_csv(path):
        if row.get('key') != 'h25_d100_T' or row.get('model') not in ['C4','H4','G4','G6']:
            continue
        model = row['model']
        pred = float(row.get('K_pred_m3', row.get('K_pred')))
        record = {'model': model, 'source_csv': str(path), 'saved_K_pred_m3': pred,
                  'role': 'TRAINING_INCLUDED_h25' if model in ['C4','H4'] else 'KNOWN_h25_SUPPLEMENT_NOT_IN_FIT_NOT_BLIND',
                  'errors_by_reference_percent': {str(r['result']['dx_m']): 100*(pred/r['K_recomputed_m3']-1) for r in reviews}}
        if model in ['G4','G6']:
            params = lock['coefficients'][model]['T']
            a, p = math.exp(params[0]), params[1]
            m = params[2] if len(params) == 3 else 1.
            s, t = 120/25, 100/25
            L = ((1+t)**3-1)/((1+t)**3+1)
            B = a*s**p
            E = (L**(-m)+B**(-m))**(-1/m)
            direct = (25e-9)**3/12*(1+E)
            record['independent_T_scalar_formula_m3'] = direct
            record['scalar_formula_matches_saved_prediction'] = near(direct, pred)
            record['inside_locked_target_domain'] = False
        candidates.append(record)
save('known_candidate_point_review.json', candidates)

assert all(r['bounded_raw_consistency_checks_pass'] for r in reviews), 'Check the report: do not repair old evidence'
assert lock_check['external_hash_matches'] and not lock_check['bound_file_drifts']
print(json.dumps({'cases': [{'tag': r['tag'], 'raw_checks': r['bounded_raw_consistency_checks_pass'],
                           'rows': r['diagnostic_rows'], 'windows': r['full_windows_recomputed'],
                           'slice_K_relative_difference': r['slice_relative_disagreement']} for r in reviews],
                  'candidate_lock_integrity': True, 'all_references_qualified': False}, indent=2))
