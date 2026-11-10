"""Read-only provenance and analytic-series arithmetic; no solver or optimizer.

Writes only this audit's algebra_checks.json. This is not CFD acceptance.
"""
from pathlib import Path
import csv
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def readj(path):
    return json.loads(path.read_text())

lock_path = ROOT / 'docs/reports/Correlation_selection_freeze_20261024/candidate_lock.json'
lock = readj(lock_path)
fit = readj(ROOT / 'docs/reports/Constrained_correlation_20261023/fits.json')['G4']
assert fit == lock['coefficients']['G4']
with (ROOT / 'docs/reports/Constrained_correlation_20261023/data_roles.csv').open() as stream:
    rows = list(csv.DictReader(stream))
dev = [r for r in rows if r['role'] == 'development']
geometry = {(float(r['h']), float(r['d']), float(r['w'])) for r in dev}
assert len(dev) == 30 and len(geometry) == 15
assert all(abs(float(r['w']) - 120) < 1e-10 for r in dev)
assert {r['direction'] for r in dev} == {'P', 'T'}

# Exact rectangular-duct series at d=w; K normalized by w^3 and P=2w.
# N counts odd terms. Tail bound is analytic truncation only, not floating error.
N = 1000
last_odd = 2*N-1
series = math.fsum(math.tanh(n*math.pi/2)/n**5 for n in range(1, 2*N, 2))
rect = (1 - 192*series/math.pi**5)/24
tail_bound = (192/(24*math.pi**5))/(4*last_odd**4)
g4_contact = 1/48
error_percent = 100*(g4_contact/rect - 1)
assert rect < g4_contact
# The first positive term alone already proves the two limits differ.
assert (1-192*math.tanh(math.pi/2)/math.pi**5)/24 < g4_contact
assert fit['P'][1] < 3 and fit['P'][1] > 0 and fit['T'][1] > 0

bound_errors = []
for rel, expected in lock['bound_files'].items():
    p = lock_path.parent / rel
    if hashlib.sha256(p.read_bytes()).hexdigest() != expected:
        bound_errors.append(rel)
assert not bound_errors
out = {
    'scope': 'analytic_series_arithmetic_and_existing_parameter_provenance_only',
    'solver_called': False, 'optimizer_called': False, 'new_flow_results': 0,
    'formal_run_id': None, 'prediction_results_read': False,
    'locked_coefficients_equal_original_fit': True,
    'candidate_lock_sha256': hashlib.sha256(lock_path.read_bytes()).hexdigest(),
    'candidate_bound_files_checked': len(lock['bound_files']),
    'candidate_bound_mismatches': bound_errors,
    'development_direction_rows': len(dev), 'development_geometries': len(geometry),
    'development_s_levels': sorted({float(r['s']) for r in dev}),
    'development_h_nm': sorted({float(r['h']) for r in dev}),
    'development_d_nm': sorted({float(r['d']) for r in dev}),
    'parameters': {d: {'ln_a': fit[d][0], 'a': math.exp(fit[d][0]), 'p': fit[d][1], 'm_fixed': 1}
                   for d in ('T', 'P')},
    'contact_square_limit': {
        'beta': 1, 'phi': .5, 'outside_finite_target_domain': True,
        'series_odd_terms': N, 'last_odd': last_odd,
        'rectangle_K_over_w3': rect,
        'series_truncation_bound_excluding_floating_roundoff': tail_bound,
        'G4_K_over_w3': g4_contact,
        'G4_relative_difference_percent': error_percent,
        'not_a_new_CFD_benchmark': True,
    },
    'numeric_prediction_acceptance': 'NOT_EVALUATED_THIS_AUDIT',
    'human_theory_review': 'PENDING',
}
(HERE/'algebra_checks.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(out, ensure_ascii=False, indent=2))
