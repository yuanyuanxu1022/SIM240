#!/usr/bin/env python3
"""Write inactive S0 metadata/templates only. No compilation, native run or release."""
from pathlib import Path
from fractions import Fraction
import csv
import hashlib
import json
import math
import sys

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_v1'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()

def save(p,data):
    if p.exists():raise FileExistsError(p)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def kv(p):return dict(line.split('=',1) for line in p.read_text().splitlines() if '=' in line)

def main():
    draft=OUT/'S0_DRAFT_NOT_EXECUTABLE';draft.mkdir(exist_ok=False)
    review=json.loads((OUT/'review_verification.json').read_text())
    history=json.loads((OUT/'external_data_history.json').read_text())
    assert review['execution_readiness']=='HOLD' and history['status']=='PENDING_AUTHOR_CHECK'
    with (CASE/'common/case_matrix.csv').open() as f:
        matrix=[r for r in csv.DictReader(f) if r['stage']=='S0_REGRESSION']
    assert len(matrix)==2
    foundation=ROOT/'CASE/D_series/D4_variable_groove_transport_20261023/results/foundation_20261023_v1'
    certificate=ROOT/'docs/reports/D4_foundation_acceptance_20261023/complete/acceptance.json'
    assert json.loads(certificate.read_text())['FOUNDATION_RESULT_PASS'] is True
    baseline_hashes={str(certificate):sha(certificate)};cases=[]
    for row in matrix:
        direction=row['direction'];baseline=foundation/f'D4_regression_h75_d100_w120_P240_Ly240_dx5_{direction}_a100000_foundation_20261023_v1/steady'
        old=kv(baseline/'result.txt');cfg=kv(baseline/'run_config.txt')
        assert old['RESULT_PASS']=='false' and old['NUMERICAL_GATE']=='PASS'
        assert cfg['direction']==direction
        expected=dict(h_nm='75',d_nm='100',w_nm='120',period_nm='240',Ly_nm='240',dx_nm='5',nu_m2_s='1e-06',acceleration_m_s2='100000',window_tstar='0.75',max_time_H_diffusion='8')
        assert all(Fraction(cfg[k])==Fraction(v) for k,v in expected.items())
        for p in baseline.rglob('*'):
            if p.is_file():baseline_hashes[str(p)]=sha(p)
        with (baseline/'diagnostics.csv').open() as f:
            reader=csv.DictReader(f);legacy_columns=reader.fieldnames
        assert len(legacy_columns)==20
        proposed='PROPOSED_URV_S0_'+direction+'_v1_20261101_01'
        template=dict(cfg)
        template.update(mode='describe',run_id=proposed,output_directory='DRAFT_NOT_AN_EXECUTION_DIRECTORY')
        template_path=draft/('S0_'+direction+'_describe_ONLY_DRAFT.txt')
        template_path.write_text(''.join(k+'='+v+'\n' for k,v in template.items()))
        nodes=Fraction(240*240)*(Fraction(75)+Fraction(100,2))/Fraction(5)**3
        window=math.ceil(Fraction('0.75')*6*(Fraction(75)/5)**2)
        cap=math.ceil(8*6*(Fraction(175)/5)**2)
        assert int(nodes)==int(row['expected_fluid_nodes'])==57600
        assert window==int(row['window_steps'])==1013 and cap==int(row['maximum_steps'])==58800
        cases.append(dict(planned_case_id=row['planned_case_id'],direction=direction,
            drive_axis='+y' if direction=='P' else '+x',purpose='new_statistics_port_regression_only_not_unseen_test',
            proposed_run_id=proposed,approved_run_id=None,actual_run_id=None,
            provisional_target_directory=str(CASE/'results/S0_URV1_20261101_01'/direction/'steady'),
            target_directory_created=False,
            inactive_template=str(template_path),inactive_template_sha256=sha(template_path),
            final_steady_config_sha256=None,final_execution_manifest_sha256=None,
            physical_inputs=expected,H_nm=125,rho_kg_m3=1000,mu_Pa_s=.001,tau=1,
            dt_s=float(Fraction(5,10**9)**2/(6*Fraction('1e-6'))),
            expected_fluid_nodes=57600,expected_installed_wall_links=32448,expected_q=.5,
            window_steps=window,maximum_steps=cap,
            per_case_wall_cap_seconds=3600,address_space_limit_GiB=8,
            baseline=dict(directory=str(baseline),run_id=old['run_id'],
                K_m3=float(old['Keff_m3']),J_m2_s=float(old['J_main_m2_s']),
                result_sha256=sha(baseline/'result.txt'),diagnostics_sha256=sha(baseline/'diagnostics.csv'),
                raw_RESULT_PASS=False,independent_foundation_acceptance=True,
                independent_certificate=str(certificate),certificate_sha256=sha(certificate),
                historical_steps=int(old['steps_completed']),legacy_columns=legacy_columns),
            current_new_result=None,formal_NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,
            geometry_PASS=None,regression_accepted=False))
    preparation=CASE/'evidence/preparation_seal.json'
    candidate=dict(protocol_id='URV-v1',stage='S0_REGRESSION',
        kind='INACTIVE_BINDING_DRAFT_NOT_EXECUTION_RELEASE',
        status='HOLD_HISTORY_AND_READONLY_REVIEW_FINDINGS',
        simulation_authorized=False,preparation_only_build=True,
        author_external_data_history_confirmation='PENDING',
        author_reply_file=str(OUT/'external_data_history.json'),author_reply_sha256=sha(OUT/'external_data_history.json'),
        approved_run_ids=[],actual_formal_run_ids=[],cases=cases,
        source_preparation_seal=str(preparation),source_preparation_seal_sha256=sha(preparation),
        current_binary_role='PREPARATION_ONLY_NOT_A_FORMAL_BINARY',
        current_binary_sha256=sha(CASE/'build/urv_reference'),future_formal_binary_sha256=None,
        effective_execution_inputs_sha256=None,
        reference_inputs_sha256=baseline_hashes,
        checker_review_findings=str(OUT/'findings.json'),checker_review_findings_sha256=sha(OUT/'findings.json'),
        required_before_effective_binding=[
            'Author confirms the external-data-history facts; unknown must not be converted to confirmed.',
            'Resolve F01/F02/F03 in a separately versioned checker and validate before execution; preserve original package.',
            'Separately authorize and build a time-advancing binary, preserving this preparation build and seal.',
            'Freeze exact per-run identities, final configs, output directories, source/binary/dependencies/libraries/checker and input-before/after maps.',
            'Prepare a bounded outer runner capturing independent exit, complete raw outputs/VTK closure, resources and fail-stop; do not auto-enter S1.',
            'At launch recheck RAM>=12GiB, initial free disk>=100GiB and per-run free disk>=8GiB; single rank/thread/cuboid overlap3, AS8GiB and wall3600s.'
        ],
        acceptance=dict(K_relative_change_max=.0001,
            numerical_and_geometry_gates='unchanged common/acceptance_spec.json',
            legacy_comparison='all 20 common columns, full aligned trajectories; save differences before any stop',
            unexplained_difference='HOLD, no automatic tolerance relaxation',
            each_run_independent_process_exit=0,
            next_stage_automatic=False,failed_case_automatic_retry=False,
            S0_pass_is_not_new_geometry_reference_qualification=True))
    save(draft/'S0_binding_DRAFT.json',candidate)
    save(draft/'baseline_inputs_sha256.json',baseline_hashes)
    save(draft/'draft_verification.json',dict(draft_only=True,case_count=2,
        native_calls=0,compiler_calls=0,formal_output_directories_created=False,
        actual_run_ids=[],launch_command_delivered=False,
        inactive_templates_describe_only=True,exact_arithmetic_PASS=True,
        external_history_confirmed=False,effective_binding_ready=False,
        original_baselines_unchanged=all(sha(p)==s for p,s in baseline_hashes.items())))
    print(json.dumps(dict(S0_cases_drafted=2,effective_execution_binding=False,
        external_history_confirmed=False,solver_started=False)))

if __name__=='__main__':main()
