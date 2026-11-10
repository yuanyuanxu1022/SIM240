"""Read saved evidence only; never import a solver or launch a subprocess."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


specs = [
    ('C01', 'interface_static_darcy_v1', 'SDI_C01_v1_20261030_01', 'V2', 'transverse'),
    ('C02', 'interface_static_darcy_v1_1', 'SDI_C02_v1_1_20261030_01', 'V2', 'parallel'),
    ('C03', 'interface_static_darcy_v1_2', 'SDI_C03_v1_2_20261030_01', 'original', 'transverse'),
    ('C04', 'interface_static_darcy_v1_3', 'SDI_C04_v1_3_20261030_01', 'original', 'parallel'),
    ('GDI01', 'groove_darcy_static_v1', 'GDI01_v1_20261030_01', 'V2', 'transverse'),
]
records = []
for case, package, run_id, model, direction in specs:
    run = ROOT / 'CASE' / package / 'runs' / run_id
    report_id = case if case == 'GDI01' else 'SDI_' + case
    report = ROOT / 'docs/reports' / (report_id + '_results_20261030')
    accepted = report / ('interface_analysis_geometry_v1_1.json' if case == 'C01' else 'interface_analysis.json')
    analysis = json.loads(accepted.read_text())
    execution = json.loads((run / 'execution.json').read_text())
    assert analysis['run_id'] == execution['run_id'] == run_id
    assert execution['status'] == 'completed'
    assert all(s['exit_code'] == 0 and not s['timed_out'] for s in execution['steps'])
    checked = []
    for entry in analysis['raw_files']:
        path = run / entry['path']
        actual = sha(path)
        assert actual == entry['sha256'], str(path)
        checked.append({'path': str(path.relative_to(ROOT)), 'sha256': actual})
    assert sha(run / 'run_manifest.json') == analysis['run_manifest_sha256']
    metrics = []
    for endpoint in (['openfoam'] if case == 'GDI01' else ['two_dimensional', 'openfoam']):
        sub = 'openfoam/GDI_output' if case == 'GDI01' else ('openfoam/SDI_output' if endpoint == 'openfoam' else 'two_dimensional')
        with (run / sub / 'faces.csv').open() as f:
            faces = list(csv.DictReader(f))
        with (run / sub / 'cells.csv').open() as f:
            cells = list(csv.DictReader(f))
        q = math.fsum(float(r['phi_m3_s']) for r in faces if r['patch'] == 'xHigh')
        volume = math.fsum(float(r['volume_m3']) for r in cells)
        u = math.fsum(float(r['volume_m3']) * float(r['Ux_m_s']) for r in cells) / volume
        assert len(cells) == 512 and q > 0
        metrics.append({'endpoint': endpoint, 'cell_count': len(cells), 'Q_m3_s': q, 'U_m_s': u})
    records.append({
        'case_id': case, 'run_id': run_id, 'model': model, 'direction': direction,
        'package': str(run.parent.parent.relative_to(ROOT)),
        'accepted_analysis': str(accepted.relative_to(ROOT)), 'accepted_analysis_sha256': sha(accepted),
        'saved_status': {k: analysis[k] for k in ['NUMERICAL_GATE', 'RESULT_PASS', 'geometry_PASS', 'geometry_scope', 'physical_validation']},
        'raw_files_hash_verified': checked, 'run_manifest_hash_verified': True,
        'exits': [{'label': s['label'], 'exit_code': s['exit_code'], 'timed_out': s['timed_out']} for s in execution['steps']],
        'recomputed_metrics': metrics,
    })
result = {
    'date': '2026-11-04', 'kind': 'READ_ONLY_SAVED_CASE_IDENTITY_HASH_AND_Q_RECOMPUTATION',
    'scope': 'Saved acceptance read; raw-file and run-manifest hashes checked; Q and mean U recomputed. Not a full rerun of acceptance.',
    'solver_calls': 0, 'builds': 0, 'new_run_ids': [], 'cases': records,
    'raw_file_entries_verified': sum(len(r['raw_files_hash_verified']) for r in records),
}
(OUT / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
stream = io.StringIO()
writer = csv.DictWriter(stream, fieldnames=['case_id', 'run_id', 'model', 'direction', 'endpoint', 'cell_count', 'Q_m3_s', 'U_m_s'])
writer.writeheader()
for r in records:
    for m in r['recomputed_metrics']:
        writer.writerow({**{k: r[k] for k in ['case_id', 'run_id', 'model', 'direction']}, **m})
(OUT / 'case_results.csv').write_text(stream.getvalue())
print(json.dumps({'cases': len(records), 'raw_file_entries_verified': result['raw_file_entries_verified'], 'solver_calls': 0}))
