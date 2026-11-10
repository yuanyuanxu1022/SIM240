"""Document, provenance and conditional budget arithmetic only; no field loading."""
from decimal import Decimal, getcontext
from pathlib import Path
import hashlib
import json
import re
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]

def read(p):
    return json.loads(p.read_text())

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

def write(name, data):
    (OUT/name).write_text(json.dumps(data, ensure_ascii=False, indent=2,
                                   allow_nan=False) + '\n')

def main():
    m = read(OUT/'source_manifest.json')
    for group in ('files', 'N8_record_files', 'production_lock_files', 'historical_protected_files'):
        for name, expected in m[group].items():
            assert sha(ROOT/name) == expected, name
    freeze = ROOT/'docs/reports/Correlation_selection_freeze_20261024'
    g4 = read(freeze/'candidate_lock.json')
    for name, expected in g4['bound_files'].items():
        assert sha(freeze/name) == expected, name
    assert read(ROOT/'docs/reports/D4_N8_acceptance_20261026/verdict.json')['status'] == 'ONE_N8_DIAGNOSTIC_ACCEPTED'

    getcontext().prec = 60
    one = Decimal(1)
    b = dict(space=Decimal('.0012'), assembly=Decimal('.0001'),
             algebra=Decimal('.0001'), extraction=Decimal('.000001'))
    lo = hi = one
    for v in b.values():
        lo *= one-v
        hi *= one+v
    bk = max(hi-one, one-lo)
    ba_sym = 2*bk/(one-bk)
    ba_exact = max(hi/lo-one, one-lo/hi)
    br = max(one/lo-one, one-one/hi)
    assert bk < Decimal('.0015')
    assert ba_exact <= ba_sym < Decimal('.0031')
    assert 2*Decimal('.0015')/(one-Decimal('.0015')) < Decimal('.0031')
    assert (Decimal('.001')**2) == Decimal('.000001')
    assert 2*Decimal('.005')/(one-Decimal('.005')) > Decimal('.01')
    # Algebraic endpoint and reciprocal checks; no PDE quantities are evaluated.
    for ep in (lo-one, hi-one):
        for et in (lo-one, hi-one):
            ratio = (one+ep)/(one+et)
            assert lo/hi <= ratio <= hi/lo
    write('budget_arithmetic.json', {
        'status': 'CONDITIONAL_DESIGN_ARITHMETIC_ONLY_NOT_MEASURED_ERROR',
        'precision_decimal_digits': 60,
        'fractional_components': {k: str(v) for k,v in b.items()},
        'ratio_lower': str(lo), 'ratio_upper': str(hi),
        'direction_symmetric_envelope_percent': str(100*bk),
        'anisotropy_interval_envelope_percent': str(100*ba_exact),
        'anisotropy_symmetric_conservative_envelope_percent': str(100*ba_sym),
        'resistance_interval_envelope_percent': str(100*br),
        'direction_target_percent': '0.15', 'anisotropy_target_percent': '0.31',
        'raw_GCI_screen_for_target_normalized_space_budget_fraction': str(b['space']/(one+b['space'])),
        'raw_ALG_QUAD_change_if_control_were_exact_fraction': str(b['algebra']/(one+b['algebra'])),
        'all_components_must_be_valid_ratio_bounds_for_strict_interpretation': True,
        'actual_component_bounds_established': False,
        'old_comparison_envelope_reused_as_new_reference_budget': False
    })
    decisions = {
        'id': 'G4_REFERENCE_CRITERIA_REVIEW_20261026_v2',
        'status': 'REVIEWED_RECOMMENDATION_NOT_ACTIVATED_NOT_EXECUTABLE',
        'approval': None, 'candidate_thresholds_activated': False,
        'solver_execution_authorized': False, 'offline_extraction_execution_authorized': False,
        'reference_qualified': False, 'strict_error_bound_established': False,
        'new_actual_run_id': None, 'prediction_permission': 'HOLD',
        'NUMERICAL_GATE': 'NOT_EVALUATED', 'RESULT_PASS': False, 'geometry_PASS': None,
        'F01': 'DEFINITION_AND_APPLICABILITY_RESOLVED_AS_RECOMMENDATION_EVIDENCE_PENDING',
        'F03': 'BUDGET_OBJECT_AND_PROPAGATION_RESOLVED_AS_RECOMMENDATION_EVIDENCE_PENDING',
        'remaining': ['F02_EXTRACTOR_IMPLEMENTATION_AND_TOLERANCE_QUALIFICATION',
                      'F04_OTHER_CASE_EXECUTION_SUPPORT', 'F05_RESOURCES_AND_PERMISSION',
                      'F06_MODEL_STOP_AND_DOMAIN_EVIDENCE'],
        'weak_continuity': {'denominator': 'nonzero full unscaled dimensionless rhs L2 norm',
                            'numerator': 'independent physical pressure rows of b-Ax',
                            'candidate_max': 1e-10,
                            'MPC_basis_and_row_scaling_must_match': True},
        'strong_divergence': {'metric': 'L2(div u)/L2(grad u)',
                              'uniform_hard_threshold': None, 'mandatory_diagnostic': True},
        'section_flux': {'candidate_max': 1e-6,
                         'scope': 'mixed N32, all flat T, delivered finest groove T and finest controls',
                         'scalar_transverse_slices': 'NOT_APPLICABLE',
                         'all_sections_guaranteed': False},
        'energy': {'normalization': 'max(D,abs(W)); D>0,W>0',
                   'independent_residuals': ['abs(D-Pdiv-W)/S', 'abs(Pdiv)/S', 'abs(D-W)/S'],
                   'candidate_max_each': 1e-6,
                   'scalar_pressure_term': 'NOT_APPLICABLE',
                   'scope': 'all future method and groove records; old N8 analysis only',
                   'symmetric_gradient_identity': 'Dsym-D=integral(div(u)^2)',
                   'identity_boundary_scope': 'stationary no-slip walls and paired periodic faces, H1 conforming'},
        'reference_budget': {'target': 'case-specific continuous Stokes K',
                             'fractional_components': {k: float(v) for k,v in b.items()},
                             'direction_target': .0015, 'anisotropy_target': .0031,
                             'space_GCI_target_normalized_proxy_max': .0012,
                             'space_raw_GCI_max': float(b['space']/(one+b['space'])),
                             'topology_sensitivity_screen': .0012,
                             'medium_fine_screen': .0025,
                             'A_direct_screen_each': .0025,
                             'NS_model_and_LBM_stopping_included': False,
                             'conditional_estimate_is_strict_bound': False},
        'postprocess_quadrature_candidate_normalized_change': 1e-8,
        'old_N8_acceptance_changed': False, 'old_LBM_thresholds_changed': False,
        'G4_model_lock_changed': False, 'old_FAIL_preserved': True,
        'next_action': 'Prepare independent extractor and fixtures only; no new solves needed for preparation'
    }
    write('decisions.json', decisions)
    for p in (OUT/'REVIEW.md', OUT/'CRITERIA_REVISION.md'):
        txt = p.read_text()
        for link in re.findall(r'\]\(([^)]+)\)', txt):
            if not link.startswith('http'):
                assert (p.parent/link).is_file(), (p.name,link)
        width = None
        for line in txt.splitlines():
            if line.startswith('|'):
                n = len(re.findall(r'(?<!\\)\|',line))
                if width is None:
                    width = n
                assert n == width, (p.name,line)
            else:
                width = None
    for flag in ('solver_execution_authorized','offline_extraction_execution_authorized',
                 'reference_qualified','strict_error_bound_established','candidate_thresholds_activated'):
        assert decisions[flag] is False
    assert not any(x.split('.')[0] in {'numpy','scipy','dolfinx','ufl','petsc4py','worker','solver','assembly'} for x in sys.modules)
    write('verification.json', {
        'status': 'STATIC_REVIEW_AND_CONDITIONAL_BUDGET_CHECK_PASS',
        'source_counts': {k:len(v) for k,v in m.items()},
        'G4_bound_files_unchanged': len(g4['bound_files']),
        'all_bound_sources_and_raw_records_unchanged': True,
        'numerical_field_arrays_loaded': False, 'new_field_metrics_computed': False,
        'solver_or_backend_called': False, 'new_run': False,
        'conditional_design_arithmetic_checked': True,
        'field_accuracy_or_reference_qualification_tested': False,
        'human_scientific_adoption': 'NOT_RECORDED', 'submission_ready': False,
        'checks': ['source hashes', 'old N8 status', 'G4 lock', 'budget endpoint identities',
                   'table widths', 'local links', 'inactive permissions']
    })
    print('STATIC_REVIEW_AND_CONDITIONAL_BUDGET_CHECK_PASS')
    print('Conditional percent envelopes: K=',100*bk, ' A=',100*ba_sym)

if __name__ == '__main__':
    main()
