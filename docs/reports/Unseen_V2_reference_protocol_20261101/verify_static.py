#!/usr/bin/env python3
"""Offline independent arithmetic/schema checks. Never calls a solver/compiler."""
from pathlib import Path
from decimal import Decimal, localcontext, ROUND_CEILING
from collections import Counter
import ast
import csv
import hashlib
import json
import math

OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    protocol=json.loads((OUT/'protocol.json').read_text());spec=json.loads((OUT/'acceptance_spec.json').read_text())
    rows=list(csv.DictReader((OUT/'case_matrix.csv').open()));assert len(rows)==24
    assert len(set(r['planned_case_id'] for r in rows))==24
    expected={'S0_REGRESSION':2,'S1_SMOOTH_THIN':2,'S2_REG_GRID':6,'S3_REG_LINEARITY':4,'S4_THIN_GRID':6,'S5_THIN_LINEARITY':4}
    assert dict(Counter(r['stage'] for r in rows))==expected
    with localcontext() as ctx:
        ctx.prec=60
        for r in rows:
            h,d,dx=[Decimal(r[k]) for k in ['h_nm','d_nm','dx_nm']]
            dt=Decimal('.5')*(dx*Decimal('1e-9'))**2/(3*Decimal('1e-6'))
            win=(Decimal('.75')*(h*Decimal('1e-9'))**2/(Decimal('1e-6')*dt)).to_integral_value(rounding=ROUND_CEILING)
            cap=(8*((h+d)*Decimal('1e-9'))**2/(Decimal('1e-6')*dt)).to_integral_value(rounding=ROUND_CEILING)
            nodes=240*240*(h+d/2)/dx**3
            assert int(r['window_steps'])==win and int(r['maximum_steps'])==cap
            assert int(r['expected_fluid_nodes'])==nodes
            assert abs(Decimal(r['dt_s'])/dt-1)<Decimal('1e-15')
            assert Decimal(r['G_Pa_per_m'])==1000*Decimal(r['acceleration_m_s2'])
            assert r['execution_authorized']=='False' and r['actual_run_id']==''
            tpl=OUT/'describe_only_templates'/(r['planned_case_id']+'.txt')
            cfg=dict(s.split('=',1) for s in tpl.read_text().splitlines())
            assert cfg['mode']=='describe' and cfg['run_id']=='PLAN_'+r['planned_case_id']
            assert cfg['output_directory']=='NOT_AN_EXECUTION_DIRECTORY'
            assert cfg['direction']==r['direction']
            assert float(cfg['dx_nm'])==float(dx) and float(cfg['h_nm'])==float(h) and float(cfg['d_nm'])==float(d)
    assert not protocol['authorization']['simulation_authorized'] and protocol['authorization']['approved_run_id'] is None
    assert not protocol['preparation']['backend_source_port_implemented']
    assert not protocol['preparation']['backend_compiled_this_round'] and not protocol['preparation']['native_zero_step_prechecks_run']
    assert protocol['reference_qualified_global'] is False
    assert spec['comparison']['minimum_practical_improvement_absolute_error']==.02
    preds=list(csv.DictReader((OUT/'model_predictions_before_reference.csv').open()))
    assert len(preds)==4
    for r in preds:
        h=float(r['h_nm'])*1e-9;d=float(r['d_nm'])*1e-9
        if r['direction']=='P':original=(h**3+(h+d)**3)/24;aa,bb=1.7685,1.6331
        else:original=1/(6*(h**-3+(h+d)**-3));aa,bb=.4900,.6990
        corr=original/(1+aa*(d/120e-9)**bb)
        assert math.isclose(float(r['K_original_m3']),original,rel_tol=1e-14)
        assert math.isclose(float(r['K_V2_m3']),corr,rel_tol=1e-14)
        assert r['reference_K_m3']=='' and r['reference_result_available']=='False'
    assert sha(OUT/'model_predictions_before_reference.csv')==json.loads((OUT/'prediction_seal.json').read_text())['model_predictions_sha256']
    bindings=json.loads((OUT/'preparation_bindings.json').read_text())
    assert all(sha(p)==h for p,h in bindings['files'].items())
    assert protocol['resources']['aggregate_wall_caps_hours']==sum(int(r['wall_cap_seconds']) for r in rows)/3600==110
    for name in ['prepare_protocol.py','verify_static.py']:ast.parse((OUT/name).read_text())
    report=dict(protocol_id='URV-v1',rows=24,reference_rows=12,control_rows=12,
        stage_counts=expected,decimal60_independent_arithmetic_PASS=True,describe_templates_only=True,
        existing_source_bindings_match=True,predictions_only_no_reference_results=True,
        wall_cap_sum_hours=110,compiled_this_round=False,native_program_called=False,
        simulations_started=0,execution_frozen=False,external_data_history_confirmation='PENDING',
        static_check_PASS=True)
    (OUT/'static_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
if __name__=='__main__':main()
