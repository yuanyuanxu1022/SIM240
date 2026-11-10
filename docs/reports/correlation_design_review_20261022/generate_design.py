#!/usr/bin/env python3
"""Generate candidate rows and static geometry checks. Never invoke a solver."""
from pathlib import Path
from fractions import Fraction
from itertools import product
import csv
import argparse
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
INPUT = HERE
OUTPUT = HERE


def save_csv(name, rows):
    with (OUTPUT/name).open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def cross(o, a, b):
    return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])


def hull(points):
    points = sorted(set(points))
    lo, hi = [], []
    for point in points:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], point) <= 0:
            lo.pop()
        lo.append(point)
    for point in reversed(points):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], point) <= 0:
            hi.pop()
        hi.append(point)
    return lo[:-1]+hi[:-1]


def ratio_key(h, d, w):
    return Fraction(w, h), Fraction(d, h)


def geometry_grid(family):
    return [(h, d, w) for h, d, w in product(
        family['h_nm'], family['d_nm'], family['w_nm'])]


def build():
    config = json.loads((INPUT/'design.json').read_text())
    old = config['historical_development']
    old_geometries = [(h, d, old['w_nm']) for h, d in product(old['h_nm'], old['d_nm'])]
    development = geometry_grid(config['new_development'])
    prediction = geometry_grid(config['new_prediction_test'])
    rows = []

    def add(kind, geometries, dxs=(5,), accelerations=(100000,), existing=False, fixed_P=None):
        for (h, d, w), dx, acceleration, direction in product(
                geometries, dxs, accelerations, config['directions']):
            period = fixed_P or 2*w
            ly = period
            phi = w/period
            edge = (period-w)/2
            dx_tag = str(dx).replace('.', 'p')
            ident = f'CAND_{kind}_h{h}_d{d}_w{w}_P{period}_Ly{ly}_dx{dx_tag}_{direction}_a{acceleration}'
            nx, ny = round(period/dx), round(ly/dx)
            nf = nx*ny*round(h/dx)+round(w/dx)*ny*round(d/dx)
            for length in [period, ly, h, d, w, period-w, edge]:
                assert abs(length/dx-round(length/dx)) < 1e-9, (ident, length)
            assert 0 < w < period and h > 0 and d >= 0
            rows.append({
                'planned_case_id': ident, 'actual_run_id': '', 'role': kind,
                'h_nm': h, 'd_nm': d, 'w_nm': w, 'P_nm': period, 'Ly_nm': ly,
                'phi': phi, 'direction': direction, 'dx_nm': dx,
                'acceleration_m_s2': acceleration, 'nu_m2_s': config['nu_m2_s'],
                'rho_kg_m3': config['rho_kg_m3'], 'tau': config['tau'],
                'dt_s': (config['tau']-.5)*(dx*1e-9)**2/(3*config['nu_m2_s']),
                'w_over_h': w/h, 'd_over_h': d/h,
                'nx_core': nx, 'ny_core': ny, 'fluid_nodes_expected': nf,
                'fluid_volume_nm3': period*ly*h+w*ly*d,
                'min_positive_feature_cells': min(v/dx for v in [h,w,period-w,d] if v>0),
                'single_D3Q19_distribution_bytes': nf*19*8,
                'existing_D2_result': existing,
                'new_steady_solve_proposed': not existing,
                'allowed_for_model_development': kind in ['legacy_dev', 'new_dev'],
                'blind_geometry': (h,d,w) in prediction and fixed_P is None,
                'status': 'candidate_not_run' if not existing else 'conditional_legacy_reuse',
                'teacher_approved': False,
            })

    add('legacy_dev', old_geometries, existing=True)
    add('new_dev', development)
    add('prediction_test', prediction)
    add('regression', [tuple(config['new_regression_geometry_h_d_w_nm'])])
    add('smooth', [(h,0,120) for h in config['smooth_h_nm']])
    add('grid_reference', [tuple(g) for g in config['grid_geometries_h_d_w_nm']],
        dxs=config['grid_extra_dx_nm'])
    add('linearity', [tuple(config['linearity_geometry_h_d_w_nm'])],
        accelerations=config['linearity_extra_acceleration_m_s2'])
    main = list(rows)
    rows = []
    add('optional_fixedP', geometry_grid(config['optional_fixed_period']), fixed_P=240)
    add('optional_deep', geometry_grid(config['optional_deep_groove_stress']))
    optional = list(rows)
    save_csv('candidate_cases.csv', main)
    save_csv('optional_cases.csv', optional)

    devkeys = {ratio_key(*g) for g in old_geometries+development}
    polygon = hull([(math.log(float(x)),math.log(float(y))) for x,y in devkeys])
    coverage = []
    for h,d,w in prediction:
        point = math.log(w/h), math.log(d/h)
        inside = all(cross(polygon[i],polygon[(i+1)%len(polygon)],point) >= -1e-12
                     for i in range(len(polygon)))
        duplicate = ratio_key(h,d,w) in devkeys
        assert inside and not duplicate
        coverage.append({'h_nm':h, 'd_nm':d, 'w_nm':w, 'inside_log_ratio_hull':inside,
                         'same_dimensionless_geometry_as_development':duplicate})
    save_csv('prediction_geometry_checks.csv', coverage)
    count = {role:sum(r['role']==role for r in main) for role in sorted({r['role'] for r in main})}
    assert count == {'grid_reference':16, 'legacy_dev':30, 'linearity':4,
                     'new_dev':16, 'prediction_test':16, 'regression':2, 'smooth':6}
    assert len({r['planned_case_id'] for r in main+optional}) == len(main+optional)
    assert sum(r['new_steady_solve_proposed'] for r in main) == 60
    assert len({(r['h_nm'],r['d_nm'],r['w_nm']) for r in main
                if r['role'] in ['legacy_dev','new_dev']}) == 23
    # Match every legacy row to an actual original result using an adjacent local index.
    index_path = INPUT/'legacy_evidence.csv'
    assert index_path.is_file(), 'archive the legacy result locator table before generating'
    with index_path.open(encoding='utf-8-sig') as stream:
        evidence = list(csv.DictReader(stream))
    assert len(evidence)==30
    for row in main:
        if row['role']!='legacy_dev':continue
        matches=[q for q in evidence if float(q['h_nm'])==row['h_nm']
                 and float(q['d_nm'])==row['d_nm'] and q['direction']==row['direction']]
        assert len(matches)==1
    audit = {
        'design_id':config['design_id'], 'status':'static_design_checks_only',
        'main_rows':len(main), 'by_role_direction_rows':count,
        'existing_direction_rows':30, 'new_steady_direction_rows_proposed':60,
        'new_primary_direction_rows':32, 'new_reference_and_control_direction_rows':28,
        'development_geometries':23, 'prediction_geometries':8,
        'optional_direction_rows':len(optional), 'all_grid_edges_integer':True,
        'candidate_ids_unique':True, 'all_8_prediction_points_in_log_ratio_hull':True,
        'prediction_ratio_duplicates':0, 'legacy_rows_bound_to_source_index':True,
        'largest_planned_fluid_nodes':max(r['fluid_nodes_expected'] for r in main),
        'largest_single_distribution_array_bytes':max(r['single_D3Q19_distribution_bytes'] for r in main),
        'ram_estimate_is_total':False, 'flow_fields_inspected':False,
        'OpenLB_geometry_precheck_executed':False, 'solver_modified':False,
        'solver_run':False, 'teacher_approved':False,
        'source_code_hash':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'configuration_hash':hashlib.sha256((INPUT/'design.json').read_bytes()).hexdigest(),
    }
    (OUTPUT/'design_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
    print(json.dumps(audit,ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input-dir',type=Path,default=HERE)
    parser.add_argument('--out',type=Path,default=HERE)
    args=parser.parse_args()
    INPUT=args.input_dir.resolve()
    OUTPUT=args.out.resolve()
    OUTPUT.mkdir(parents=True,exist_ok=True)
    build()
