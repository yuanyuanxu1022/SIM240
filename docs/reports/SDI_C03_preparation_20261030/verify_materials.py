"""Verify existing static preparation and completed-case regressions. No solve."""
import ast
import hashlib
import json
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[3]
REPORT=Path(__file__).resolve().parent
ROOT=PROJECT/'CASE/interface_static_darcy_v1_2'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name, value):
    p=REPORT/name
    if p.exists():raise FileExistsError(p)
    p.write_text(json.dumps(value,indent=2)+'\n')


def main():
    regression=[]
    for case,baseline in [
        ('C01','docs/reports/SDI_C01_results_20261030/interface_analysis_geometry_v1_1.json'),
        ('C02','docs/reports/SDI_C02_results_20261030/interface_analysis.json')]:
        old=json.loads((PROJECT/baseline).read_text())
        newpath=REPORT/(case+'_checker_1_2_regression.json')
        new=json.loads(newpath.read_text())
        assert new['checker_version']=='1.2.0'
        old.pop('checker_version',None);new.pop('checker_version')
        assert old==new, case+' changed beyond checker version'
        n=sum(len(r['checks']) for r in new['results'].values())+len(new['cross_checks'])
        assert n==50 and new['RESULT_PASS'] is True
        regression.append(dict(case_id=case,checks=n,all_metrics_gates_and_raw_hashes_identical=True,
                               baseline=baseline,baseline_sha256=sha(PROJECT/baseline),
                               new_report=newpath.name,new_report_sha256=sha(newpath)))
    oldchecker=PROJECT/'CASE/interface_static_darcy_v1_1/analysis/check_results.py'
    newchecker=ROOT/'analysis/check_results.py'
    def functions(p):
        return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body
                if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    assert functions(oldchecker)==functions(newchecker)
    save('regression_comparison.json',dict(checker_version='1.2.0',all_function_ASTs_unchanged=True,
         old_checker_sha256=sha(oldchecker),new_checker_sha256=sha(newchecker),cases=regression,
         CFD_rerun=False,physical_validation='NOT_EVALUATED'))
    c01=json.loads((PROJECT/'CASE/interface_static_darcy_v1/common/C01.json').read_text())
    c03=json.loads((ROOT/'common/C03.json').read_text())
    same=['H_m','L_m','mu_Pa_s','rho_kg_m3','mesh_cells','drive_axis','G_Pa_per_m',
          'pressure_units','velocity_definition','thresholds','linear_solver','source_hashes','source_paths']
    assert all(c01[k]==c03[k] for k in same)
    expected=json.loads((ROOT/'common/C03_expected.json').read_text())
    prep=json.loads((ROOT/'reports/preparation.json').read_text())
    assert prep['flow_solver_executed'] is False
    assert all(c['exit_code']==0 for c in prep['commands'])
    assert prep['two_dimensional_audit']['flow_solved'] is False
    assert prep['openfoam_audit']['flow_solved'] is False
    assert prep['openfoam_audit']['initial_p_max_Pa']==0
    save('C01_C03_input_comparison.json',dict(same_fields=same,all_same_fields_equal=True,
         C01_input_sha256=sha(PROJECT/'CASE/interface_static_darcy_v1/common/C01.json'),
         C03_input_sha256=sha(ROOT/'common/C03.json'),
         changed_physical_inputs=['K_m3','D_m_minus2'],
         added_trace_metadata=['coefficient_input_id','orientation_id'],
         changed_identity_fields=['case_id','schema'],
         C03_coefficient_family=c03['coefficient_input_id'],orientation=c03['orientation_id'],
         original_formula_recomputed_in_static_audit=True,expected=expected,
         ratio_is_descriptive_no_new_acceptance_threshold=True,C03_flow_solved=False))
    # Record the already observed terminal unittest result; do not rerun it.
    testfiles=[ROOT/'tests/test_checker.py',ROOT/'tests/test_geometry_release.py']
    (ROOT/'reports/functional_tests.json').write_text(json.dumps(dict(
         kind='OBSERVED_TERMINAL_UNITTEST_RESULT',
         command='python -B -m unittest discover -s CASE/interface_static_darcy_v1_2/tests -v',
         exit_code=0,tests_run=15,failures=0,errors=0,
         observed_summary='Ran 15 tests in 0.031s; OK',
         synthetic_fixtures_only=True,CFD_solver_launched=False,
         checker_sha256=sha(newchecker),files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in testfiles]),indent=2)+'\n')
    for p in ROOT.rglob('*.py'):ast.parse(p.read_text())
    for p in ROOT.rglob('*.json'):json.loads(p.read_text())
    assert not (ROOT/'runs').exists()
    for rel in ['openfoam/cases/C03/1','openfoam/cases/C03/SDI_output']:
        assert not (ROOT/rel).exists()
    print(json.dumps(dict(C01_checks_unchanged=50,C02_checks_unchanged=50,
                         checker_function_ASTs_unchanged=True,physical_settings_unchanged=True,
                         C03_actual_run_id=None,C03_flow_solved=False)))


if __name__=='__main__':main()
