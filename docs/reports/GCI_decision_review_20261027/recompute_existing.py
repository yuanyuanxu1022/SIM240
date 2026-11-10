"""Read existing scalar records only; never import or launch project solvers."""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARCHIVE = ROOT / 'CASE/03_grid_convergence/G2_EX240_grid_convergence/archive/g2_grid_20260917T165045+0800'
G1 = ROOT / 'CASE/00_validation/G1_Poiseuille_Bouzidi_Validation/results/g1_v2_20260916T202853+0800'
protected = {}

def read(path):
    data = path.read_bytes()
    protected[str(path.relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
    return data.decode()

def kv(path):
    return dict(line.split('=', 1) for line in read(path).splitlines() if '=' in line)

fixed = [
    'docs/reports/Celik_GCI_verification_20261027/REPORT.md',
    'docs/reports/SIM240_中文稿_导师审阅版_20261022.md',
    'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md',
    'CASE/03_grid_convergence/G2_EX240_grid_convergence/STEP3_PROTOCOL.md',
    'CASE/03_grid_convergence/G2_EX240_grid_convergence/scripts/postprocess_grid.py',
    'docs/reports/Methods_sources_data_audit_20261027/evidence/asme_gci_official_manuscript.txt',
]
for item in fixed:
    read(ROOT / item)
old = {r['metric']: r for r in csv.DictReader(read(ARCHIVE / 'g2_richardson_gci.csv').splitlines())}
values = {}
records = []
for tag in ['1p25', '2p5', '5']:
    vals = {}
    for case, metric, key in [('Smooth75', 'K_smooth', 'K_LBM_m3'), ('EX240_parallel', 'K_parallel', 'Keff_m3'), ('EX240_perpendicular', 'K_perpendicular', 'Keff_m3')]:
        folder = ARCHIVE / 'runs' / ('dx' + tag) / case / 'steady'
        data = kv(folder / 'result.txt')
        exit_code = int(read(folder / 'exit_code.txt').strip())
        vals[metric] = float(data[key])
        records.append(dict(grid=tag, case=case, value=vals[metric], original_PASS=data['PASS'], exit_code=exit_code, mass_max=float(data['max_mass_abs_relative']), source=str((folder / 'result.txt').relative_to(ROOT))))
    vals['eta_parallel'] = vals['K_parallel'] / vals['K_smooth']
    vals['eta_perpendicular'] = vals['K_perpendicular'] / vals['K_smooth']
    vals['anisotropy'] = vals['K_parallel'] / vals['K_perpendicular']
    for metric, value in vals.items():
        values.setdefault(metric, []).append(value)

rows = []
for metric, (f, m, c) in values.items():
    p = math.log(abs((c-m)/(m-f))) / math.log(2)
    ext = f + (f-m)/(2**p-1)
    ea = abs((f-m)/f)
    eext = abs((ext-f)/ext)
    gci = 1.25 * ea/(2**p-1)
    gm = 1.25*abs((m-c)/m)/(2**p-1)
    ratio = gm/(2**p*gci)
    assert math.isclose(p, float(old[metric]['apparent_order_p']), rel_tol=1e-12)
    assert math.isclose(gci*100, float(old[metric]['GCI_fine_percent']), rel_tol=1e-12)
    assert abs(ratio-abs(f/m)) < 1e-14
    dependent_fail = metric in ['K_perpendicular', 'eta_perpendicular', 'anisotropy']
    rows.append(dict(metric=metric, fine_dx_nm=1.25, medium_dx_nm=2.5, coarse_dx_nm=5, r21=2, r32=2, Fs=1.25, fine_value=f, medium_value=m, coarse_value=c, p=p, extrapolated=ext, ea_percent=100*ea, eext_percent=100*eext, GCI_fine_percent=100*gci, legacy_ratio=ratio, ratio_identity_residual=ratio-abs(f/m), includes_failed_fine_T=dependent_fail, interpretation='historical_conditional_estimate_not_accuracy_certificate'))
smooth = rows[0]
analytic = (75e-9)**3/12
error_exact = abs(smooth['fine_value']-analytic)/abs(analytic)
error_fine = abs(smooth['fine_value']-analytic)/abs(smooth['fine_value'])
g1r = list(csv.DictReader(read(G1 / 'richardson_summary.csv').splitlines()))
g1m = list(csv.DictReader(read(G1 / 'matrix_summary.csv').splitlines()))
result = dict(raw_records=records, rows=rows, smooth=dict(analytic=analytic, error_exact_denominator_percent=100*error_exact, error_fine_denominator_percent=100*error_fine, same_denominator_coverage=smooth['GCI_fine_percent']/(100*error_fine)), g1_saved_richardson=g1r, g1_saved_matrix=g1m)
(OUT / 'recomputed.json').write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
with (OUT / 'candidate_gci_table.csv').open('w') as file:
    writer = csv.DictWriter(file, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
(OUT / 'protected_inputs.json').write_text(json.dumps(protected, indent=2, ensure_ascii=False)+'\n')
assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest()==h for p,h in protected.items())
(OUT / 'verification.json').write_text(json.dumps(dict(six_rows_match_archive=True, six_ratio_identities_within_1e_14=True, raw_records_read=len(records), protected_inputs_unchanged=len(protected), solver_started=False, gate_reclassified=False), indent=2)+'\n')
print(json.dumps(dict(rows=rows, smooth=result['smooth'], protected_count=len(protected)), ensure_ascii=False, indent=2))
