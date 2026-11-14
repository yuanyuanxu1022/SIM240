#!/usr/bin/env python3
"""Read saved evidence only. Never imports a solver or changes a CASE package."""
import csv
import hashlib
import json
import math
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.dont_write_bytecode = True
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
INPUTS = {}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def bind(path):
    path = path.resolve()
    value = digest(path)
    key = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    if key in INPUTS:
        assert INPUTS[key] == value, f'input changed during audit: {key}'
    INPUTS[key] = value
    return value


def read(path):
    bind(path)
    return json.loads(path.read_text())


def rows(path):
    bind(path)
    with path.open() as stream:
        return list(csv.DictReader(stream))


def field_integral(path, period_nm):
    bind(path)
    with np.load(path, allow_pickle=False) as z:
        for key in ('p', 'ux', 'uz', 'pressure'):
            assert np.isfinite(z[key]).all(), (str(path), key)
        p, t, ux = z['p'], z['t'], z['ux']
        assert t.min() >= 0 and t.max() < p.shape[1]
        edges = np.sort(np.concatenate([t[[0, 1]].T, t[[1, 2]].T,
                                        t[[0, 2]].T]), axis=1)
        unique, inv = np.unique(edges, axis=0, return_inverse=True)
        edge_dofs = inv.reshape(3, t.shape[1]).T + p.shape[1]
        assert len(ux) == p.shape[1] + len(unique)
        a, b = p[:, t[1]] - p[:, t[0]], p[:, t[2]] - p[:, t[0]]
        areas = np.abs(a[0] * b[1] - a[1] * b[0]) / 2
        assert (areas > 0).all()
        k = math.fsum(areas * np.sum(ux[edge_dofs], axis=1) / 3) / period_nm * 1e-27
        mesh = hashlib.sha256(np.ascontiguousarray(p, dtype=np.float64).tobytes()
                              + np.ascontiguousarray(t, dtype=np.int64).tobytes()).hexdigest()
    return k, mesh


def main():
    pkg = ROOT / 'CASE/paper1_fem_stokes_reference_v2'
    manifest = read(pkg / 'release_manifest.json')
    body = {k: v for k, v in manifest.items() if k != 'release_sha256'}
    calculated = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':'),
                                         ensure_ascii=False).encode()).hexdigest()
    assert calculated == manifest['release_sha256']
    for entry in manifest['files']:
        path = pkg / entry['path']
        assert bind(path) == entry['sha256'] and path.stat().st_size == entry['bytes']
    points = read(pkg / 'points.json')
    auth = read(pkg / 'authorization.json')
    assert auth['release_sha256'] == manifest['release_sha256']
    assert bind(pkg / 'points.json') == manifest['point_set_sha256']
    assert bind(pkg / 'acceptance_rule.json') == manifest['acceptance_rule_sha256']
    eligible = {x['case'] for x in points['points'] if x['status'] == 'ELIGIBLE'}
    excluded = [x['case'] for x in points['points'] if x['status'] == 'EXCLUDED_BY_AUTHOR_DECISION']
    assert set(auth['granted_cases']) == eligible
    queue = rows(pkg / 'QUEUE_STATUS.csv')
    assert {x['case'] for x in queue} == eligible and len(queue) == len(eligible)
    completed, field_checks = [], []
    for receipt_path in sorted(pkg.glob('runs/*/SOLVE_RECEIPT.json')):
        solve = read(receipt_path)
        verify = read(receipt_path.with_name('VERIFY_RECEIPT.json'))
        case = solve['case']
        assert case in eligible and solve['run_id'] == receipt_path.parent.name
        assert solve['state'] == 'SOLVED' and solve['exit_code'] == 0
        assert solve['release_sha256'] == verify['release_sha256'] == manifest['release_sha256']
        assert verify['solve_receipt_sha256'] == bind(receipt_path)
        assert verify['solve_receipt_unchanged']
        assert verify['reference_status'] == 'REFERENCE_CANDIDATE'
        assert not any(verify[k] for k in ('gate_problems', 'additive_gate_problems', 'provenance_problems'))
        for key in ('python', 'numpy', 'scipy', 'scikit_fem'):
            assert solve['environment'][key] == manifest['environment'][key]
        assert [x['dx_nm'] for x in solve['levels']] == [5.0, 2.5, 1.25]
        for level in solve['levels']:
            folder = pkg / 'results' / case
            meta_path, field = folder / level['json_file'], folder / level['field_file']
            meta = read(meta_path)
            assert bind(meta_path) == level['json_sha256']
            assert bind(field) == level['field_sha256_solver'] == level['field_sha256_rehashed']
            assert meta['field_sha256'] == bind(field)
            kval, mesh = field_integral(field, meta['P_nm'])
            assert mesh == level['mesh_sha256']
            saved = next(x for x in verify['levels'] if x['dx_nm'] == level['dx_nm'])
            assert abs(kval / saved['K_recomputed_m3'] - 1) < 1e-11
            field_checks.append({'package': 'FEM_v2', 'case': case, 'dx_nm': level['dx_nm'],
                                 'K_integrated_m3': kval, 'field_sha256': bind(field), 'mesh_sha256': mesh})
        completed.append({'case': case, 'run_id': solve['run_id'], 'exit_code': solve['exit_code'],
                          'state': 'COMPLETED', 'reference_status': verify['reference_status'],
                          'started_at': solve['started_at'], 'finished_at': solve['finished_at'],
                          'wall_seconds': solve['wall_seconds'], 'receipt': str(receipt_path.relative_to(ROOT))})
    assert len(completed) == len({x['case'] for x in completed}) == len(eligible) == 12
    assert len({x['run_id'] for x in completed}) == 12
    assert len(field_checks) == 36
    assert not any((pkg / 'results' / name).exists() for name in excluded)

    pilot = ROOT / 'CASE/paper1_fem_stokes_pilot_v1/results'
    legacy = []
    for folder in sorted(pilot.iterdir()):
        if not folder.is_dir():
            continue
        verify = read(folder / 'VERIFICATION.json')
        assert verify['status'] == 'PILOT_NUMERICAL_CHECKS_PASS' and not verify['problems']
        metas = [read(path) for path in sorted(folder.glob('dx_*.json'))]
        assert sorted(x['dx_nm'] for x in metas) == [1.25, 2.5, 5.0]
        for meta in metas:
            field = folder / meta['field_file']
            assert bind(field) == meta['field_sha256']
            kval, mesh = field_integral(field, meta['P_nm'])
            saved = next(x for x in verify['levels'] if x['dx_nm'] == meta['dx_nm'])
            assert abs(kval / saved['K_recomputed_m3'] - 1) < 1e-11
            assert abs(kval / meta['K_m3'] - 1) < 1e-11
            field_checks.append({'package': 'FEM_pilot_v1', 'case': folder.name,
                                 'dx_nm': meta['dx_nm'], 'K_integrated_m3': kval,
                                 'field_sha256': bind(field), 'mesh_sha256': mesh})
        legacy.append({'case': folder.name, 'state': 'COMPLETED_SAVED_FIELDS',
                       'numeric_label_recorded': verify['status'],
                       'run_time_provenance': 'LEGACY_LIMITATION_NOT_RETROACTIVELY_REPAIRED',
                       'K_fine_m3': next(x['K_m3'] for x in metas if x['dx_nm'] == 1.25)})
    assert len(legacy) == 24 and len(field_checks) == 108

    fvm = ROOT / 'CASE/paper1_fvm_stokes_reference_v2'
    release = read(fvm / 'release_manifest.json')
    internal_drift, external_drift = [], []
    for path_str, expected in release['sha256'].items():
        path = Path(path_str)
        if not path.is_absolute():
            path = fvm / path
        if not path.exists() or bind(path) != expected:
            internal_drift.append(str(path))
    for path_str, expected in release['external_sha256'].items():
        path = Path(path_str)
        actual = bind(path) if path.exists() else None
        if actual != expected:
            external_drift.append({'path': str(path), 'expected': expected, 'actual': actual})
    prepared = read(fvm / 'prepared_manifest.json')
    fvm_rows, binding_issues, receipt_count, recorded_checks = [], [], 0, 0
    for case in prepared['cases']:
        name = case['case_id']
        folder = fvm / 'prepared' / name
        receipt_path = folder / 'runtime/receipt.json'
        row = {'case': name, 'formal_receipt_present': receipt_path.exists()}
        if receipt_path.exists():
            receipt_count += 1
            receipt = read(receipt_path)
            row.update(run_id=receipt['run_id'], exit_code=receipt['independent_exit_code'],
                       stopping=receipt.get('stopping'), solver_converged=receipt.get('solver_converged'))
            for key, base in [('evidence_sha256', folder / 'referenceEvidence'),
                              ('native_field_sha256', folder),
                              ('mesh_sha256', folder / 'constant/polyMesh'),
                              ('runtime_logs_sha256', folder / 'runtime')]:
                for rel, expected in receipt.get(key, {}).items():
                    path = base / rel
                    actual = bind(path) if path.exists() else None
                    recorded_checks += 1
                    if actual != expected:
                        binding_issues.append({'case': name, 'group': key, 'path': str(path.relative_to(ROOT)),
                                               'expected': expected, 'actual': actual})
            row['bound_file_issues'] = sum(x['case'] == name for x in binding_issues)
        fvm_rows.append(row)

    historical = read(ROOT / 'docs/reports/PAPER1_fvm_v21_batch_20261112/execution/h25_d100_T_fine.assessment.json')
    qualified = [x for x in historical['comparisons'] if x.get('reference_accepted')]
    fvm_integrals = {}
    for comparison in qualified:
        folder = fvm / 'prepared' / (comparison['point'] + '_fine')
        case = read(folder / 'case.json')
        path = folder / 'referenceEvidence/cells.csv'
        bind(path)
        component = 'Uy_m_s' if case['direction'] == 'P' else 'Ux_m_s'
        with path.open() as stream:
            integral = math.fsum(float(x[component]) * float(x['V_m3'])
                                 for x in csv.DictReader(stream))
        kval = case['nu_m2_s'] / case['acceleration_m_s2'] * integral / case['Aplan_m2']
        assert abs(kval / comparison['Kref_m3'] - 1) < 1e-11
        fvm_integrals[comparison['point']] = kval
    server_history = read(ROOT / 'docs/reports/PAPER1_h125T_server_recheck_20261113/RECALC.json')
    bind(ROOT / 'docs/reports/PAPER1_h125T_server_recheck_20261113/REPORT.md')

    pair_table = rows(ROOT / 'docs/reports/PAPER1_fem_v2_results_20261114/PAIR_TABLE_v2.csv')
    counts = {'geometry_rows': len(pair_table),
              'P': sum(bool(x['K_P_m3']) for x in pair_table),
              'T': sum(bool(x['K_T_m3']) for x in pair_table),
              'pairs': sum(bool(x['K_P_m3']) and bool(x['K_T_m3']) for x in pair_table),
              'P_sources': dict(Counter(x['K_P_source'] for x in pair_table))}
    assert (counts['geometry_rows'], counts['P'], counts['T'], counts['pairs']) == (19, 19, 17, 17)
    source_lookup = {(x['case'], x['dx_nm']): x['K_integrated_m3'] for x in field_checks}
    comparison_bindings = []
    for row in pair_table:
        geom = row['geometry'].replace('/', '_')
        for direction in ('P', 'T'):
            if not row[f'K_{direction}_m3']:
                continue
            case_id = geom + '_' + direction
            source_k = (fvm_integrals[case_id] if row[f'K_{direction}_source'] == 'qualified_FVM'
                        else source_lookup[case_id, 1.25])
            relative_difference = float(row[f'K_{direction}_m3']) / source_k - 1
            assert abs(relative_difference) < 1e-11
            comparison_bindings.append({'case': case_id, 'source': row[f'K_{direction}_source'],
                                        'K_relative_difference': relative_difference})
    primary = rows(ROOT / 'docs/reports/PAPER1_V2_coefficient_choice_audit_20261110/fixed_V2_primary36_checked.csv')
    assert len(primary) == 36 and len({(x['h_nm'], x['d_nm']) for x in primary}) == 18
    protected_docs = [ROOT / x for x in [
        'docs/reports/SIM240_中文稿_导师审阅版_20261022.md',
        'docs/reports/SIM240_First_Paper_English_20261028.md',
        'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md',
        'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md',
        'docs/reports/PAPER1_conclusions_current_20261109.md']]
    for path in protected_docs:
        bind(path)
    changes = [key for key, expected in INPUTS.items()
               if not (ROOT / key).exists() or digest(ROOT / key) != expected]
    assert not changes, changes
    result = {'checked_at': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
              'scope': 'SAVED_EVIDENCE_INVENTORY_NOT_NEW_QUALIFICATION',
              'new_solves': 0, 'new_reference_grants': 0, 'full_PDE_reassembly_this_audit': False,
              'fem_v2': {'release': manifest['release_sha256'], 'files_checked': len(manifest['files']),
                         'completed': completed, 'excluded': excluded, 'pending_eligible': [],
                         'additional_geometries_out_of_scope': points['excluded_from_this_package'],
                         'queue_timing_column_empty': all(not x['wall_seconds'] for x in queue)},
              'fem_pilot_v1': {'completed': legacy, 'groove_direction_records': 22,
                               'flat_checks': 2, 'run_time_receipts_reconstructed': False},
              'fvm': {'internal_files_checked': len(release['sha256']), 'internal_drift': internal_drift,
                      'external_files_checked': len(release['external_sha256']), 'external_drift': external_drift,
                      'formal_receipts_present': receipt_count, 'recorded_file_hashes_checked': recorded_checks,
                      'recorded_file_binding_issues': binding_issues, 'cases': fvm_rows,
                      'historical_qualified_references': qualified,
                      'historical_qualified_fine_K_reintegrated': fvm_integrals,
                      'server_diagnostics_from_saved_report_only': server_history,
                      'automatic_retries_authorized': False},
              'comparison_counts': counts, 'comparison_source_bindings': comparison_bindings,
              'field_integral_checks': len(field_checks),
              'protected_input_count': len(INPUTS), 'changed_inputs': changes,
              'server_live_processes_checked': False}
    for name, obj in [('INVENTORY.json', result), ('FIELD_CHECKS.json', field_checks),
                      ('INPUT_SNAPSHOT.json', INPUTS)]:
        (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    status_rows = []
    for item in legacy:
        status_rows.append({'group': '已完成', 'package': 'FEM_pilot_v1', 'case': item['case'],
                            'unit': '三档网格算例', 'detail': '保存场齐全、K重算一致；历史运行绑定限制仍保留'})
    for item in completed:
        status_rows.append({'group': '已完成', 'package': 'FEM_v2', 'case': item['case'],
                            'unit': '三档网格算例', 'detail': '求解和复核回执齐全；REFERENCE_CANDIDATE；run_id=' + item['run_id']})
    for name in excluded:
        status_rows.append({'group': '已排除', 'package': 'FEM_v2', 'case': name,
                            'unit': '方向点', 'detail': '作者已排除整个h25档；不是排队等待运行'})
    for item in points['excluded_from_this_package']:
        status_rows.append({'group': '已排除', 'package': 'FEM_v2', 'case': item['case'],
                            'unit': '新增几何方向点', 'detail': '不在本包及本轮范围；未新增算例'})
    for item in historical['comparisons']:
        accepted = bool(item.get('reference_accepted'))
        if accepted:
            detail = '历史合格参考保留；一致性=' + item['status'] + '；本轮重新积分fine K一致，不重新授资格'
        elif item['point'] == 'h25_d100_T':
            detail = 'tight服务器诊断已完成但功率超门槛、正式回执缺失；按已定范围不追加'
        else:
            detail = '本地fine超时记录保留；服务器fine续跑已完成但未走完整接收链；tight未完成'
        status_rows.append({'group': '已完成' if accepted else '旧任务未解决', 'package': 'FVM_v2.1',
                            'case': item['point'], 'unit': '方向参考链', 'detail': detail})
    with (OUT / 'CASE_STATUS.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['group', 'package', 'case', 'unit', 'detail'], lineterminator='\n')
        writer.writeheader()
        writer.writerows(status_rows)
    print(json.dumps({'FEM_new_completed': len(completed), 'FEM_old_completed': len(legacy),
                      'FEM_field_checks': len(field_checks), 'FVM_receipts': receipt_count,
                      'FVM_recorded_file_binding_issues': len(binding_issues),
                      'FVM_internal_drift': len(internal_drift), 'FVM_external_drift': len(external_drift),
                      'protected_inputs': len(INPUTS), 'changed_inputs': changes}, ensure_ascii=False))


if __name__ == '__main__':
    main()
