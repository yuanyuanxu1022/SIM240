#!/usr/bin/env python3
"""Read-only artifact/old-input verification, no solver calls."""
from pathlib import Path
import ast
import csv
import hashlib
import json
import math

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CASE=HERE.parent


def check_hashes(hashes):
    return [p for p,v in hashes.items() if not Path(p).is_file()
            or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=v]


def main():
    s=json.loads((HERE/'static_results.json').read_text())
    c=json.loads((HERE/'c_parameters.json').read_text())
    d=json.loads((CASE/'mechanism_study_20261021/design.json').read_text())
    assert not c['solver_started'] and c['run_id'] is None
    assert d['material']['liquid_dynamic_viscosity_Pa_s']['value']==.010
    assert c['material_model']['mu_liquid_Pa_s']==.010
    assert math.isclose(c['mapping']['M_SI'],s['physical_M_main'],rel_tol=1e-14)
    assert c['N']==[64]*3 and c['steps']==64 and len(c['cases'])==4
    assert math.isclose(c['duration_s'],6.666666666666667e-12,rel_tol=1e-14)
    assert s['script_sha256']==hashlib.sha256((HERE/'static_review.py').read_bytes()).hexdigest()
    rows=list(csv.DictReader((HERE/'spectral_rates.csv').open()))
    assert len(rows)==495
    def row(route,dx,mode):
        return next(r for r in rows if r['route']==route and float(r['dx_nm'])==dx
                    and float(r['phi0'])==0 and r['mode']==str(mode))
    for mode in ((1,0,0),(4,0,0),(8,0,0)):
        for route,grows in (('tau_growth',True),('alpha_growth',False)):
            errors=[abs(float(row(route,dx,mode)['signed_rate_bias_percent'])) for dx in (2.5,1.25,.625)]
            assert (errors[0]<errors[1]<errors[2]) if grows else (errors[0]>errors[1]>errors[2])
    for route in ('tau_growth','alpha_growth'):
        for dx in (2.5,1.25,.625):
            axis=[float(row(route,dx,mode)['signed_rate_bias_percent']) for mode in ((1,0,0),(0,1,0),(0,0,1))]
            assert max(axis)-min(axis)<1e-4  # eigensolver cancellation at tiny 1-lambda
            a=float(row(route,dx,(3,0,0))['continuum_rate_lu'])
            b=float(row(route,dx,(2,2,1))['continuum_rate_lu'])
            assert math.isclose(a,b,rel_tol=1e-14)
    for init in s['initial_arrays']:
        assert init['rho_min_kg_m3']>0 and abs(init['phi_mean']-.5)<1e-14
    assert s['initial_arrays'][1]['gas_core_density_offset_relative_to_1p2']<1e-4
    assert s['tau1_scalar_crosscheck_max_abs']<1e-13
    assert max(r['double_difference_percentage_points'] for r in s['independent_axial_decimal_checks'])<2e-5
    inputs=json.loads((CASE/'ab_diffusion_validation_20261022/analysis_20261022/input_hashes.json').read_text())
    binding=json.loads((CASE/'ab_diffusion_validation_20261022/evidence/build_binding.json').read_text())['sha256']
    bad_inputs=check_hashes(inputs);bad_binding=check_hashes(binding)
    assert not bad_inputs and not bad_binding
    for name in ('SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md'):
        old=(HERE/'before'/name).read_text()
        new=(ROOT/'docs/reports'/name).read_text()
        assert old.split('## 第二篇论文：')[0]==new.split('## 第二篇论文：')[0]
    for py in HERE.glob('*.py'): ast.parse(py.read_text())
    result=dict(status='STATIC_REVIEW_CHECKS_PASS_NOT_PHYSICAL_GATE',
                old_analysis_inputs=len(inputs),old_analysis_input_mismatches=bad_inputs,
                old_run_binding_files=len(binding),old_run_binding_mismatches=bad_binding,
                first_paper_shared_opening_unchanged=True,
                static_review_exit_code=0,verification_exit_code=0,
                no_OpenLB_execution=True,no_compilation=True,
                formal_gates={k:'NOT_EVALUATED' for k in ('NUMERICAL_GATE','RESULT_PASS','geometry_PASS')})
    (HERE/'evidence/verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
