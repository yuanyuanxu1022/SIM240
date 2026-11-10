#!/usr/bin/env python3
"""Read-only v1.1 review; persist audit/probes only in this new report directory.

Compiler/solver/VTK-data execution is forbidden. All writable raw directories and
build captures below are explicitly synthetic; original packages are hashed.
"""
from pathlib import Path
import ast
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
OLD=ROOT/'CASE/unseen_v2_reference_v1'
NEW=ROOT/'CASE/unseen_v2_reference_checker_v1_1'
PREV=ROOT/'docs/reports/URV_checker_v1_1_revision_20261101'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()

def snapshot(folder):return {str(p):sha(p) for p in folder.rglob('*') if p.is_file()}

def save(p,data):
    if p.exists():raise FileExistsError(p)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def main():
    assert json.loads((OUT/'intake_validation.json').read_text())['status']=='READY_FOR_LOCAL_REVIEW'
    before={**snapshot(OLD),**snapshot(NEW),**snapshot(PREV)}
    prior_review=ROOT/'docs/reports/URV_v1_readonly_review_S0_20261101'
    before.update(snapshot(prior_review))
    historical=json.loads((prior_review/'historical_inputs_before.json').read_text())
    assert all(sha(p)==s for p,s in historical.items())
    before.update(historical)
    save(OUT/'protected_inputs_before.json',before)
    for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        p=OUT/'before'/name;p.parent.mkdir(exist_ok=True)
        p.write_bytes((ROOT/'docs/reports'/name).read_bytes())
    seals={}
    for path in [OLD/'evidence/preparation_seal.json',NEW/'evidence/revision_seal.json']:
        rec=json.loads(path.read_text())
        assert not rec['simulation_authorized'] and rec['approved_run_ids']==rec['actual_formal_run_ids']==[]
        assert all(sha(p)==s for p,s in rec['inputs_sha256'].items())
        seals[str(path)]=dict(sha256=sha(path),input_count=len(rec['inputs_sha256']))
    manifest=json.loads((PREV/'source_manifest.json').read_text())['files']
    assert all(sha(ROOT/p)==s for p,s in manifest.items())
    # Re-run existing deterministic tests; no production code or threshold edits.
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    with (OUT/'existing_70_tests.log').open('w') as log:
        proc=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(NEW/'tests'),'-p','test_*.py','-v'],
            stdout=log,stderr=subprocess.STDOUT,env=env,timeout=120)
    assert proc.returncode==0 and 'Ran 70 tests' in (OUT/'existing_70_tests.log').read_text()
    sys.path.insert(0,str(NEW/'analysis'));sys.path.insert(0,str(NEW/'tests'))
    import check_results as checker
    import contracts
    from fixtures_contract import ContractFixture
    # R1: valid declared baseline must remain protected when another declaration
    # is malformed. Never probe this against actual historical raw results.
    probe=OUT/'synthetic_probes/R1_malformed_metadata'
    raw=probe/'SYNTHETIC_CURRENT_RAW';raw.mkdir(parents=True)
    baseline=probe/'SYNTHETIC_BASELINE_RAW';baseline.mkdir()
    marker=baseline/'MARKER_NOT_REAL_RESULTS.txt';marker.write_text('Synthetic-only input directory.\n')
    common=dict(protocol_id='URV-v1',simulation_authorized=False,preparation_only_build=True,
        author_external_data_history_confirmation='PENDING',inputs_sha256={str(marker):sha(marker)},
        h75_regression_references={'P':{'directory':str(baseline)}},
        fixture_label='SYNTHETIC_OUTPUT_GUARD_PROBE_NOT_AUTHORIZATION')
    observed=[]
    for label,record in [('well_formed',{'run_id':'SYNTHETIC','output_directory':str(raw)}),
                         ('malformed',{'run_id':'SYNTHETIC'})]:
        document=dict(common,approved_runs=[record]);release=probe/(label+'_NOT_EXECUTION.json')
        save(release,document)
        output=baseline/('analysis_'+label)
        initial=snapshot(baseline)
        call=[sys.executable,'-B',str(NEW/'analysis/check_results.py'),'--run',str(raw),
            '--release',str(release),'--release-sha256',sha(release),'--out',str(output)]
        proc=subprocess.run(call,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=env,timeout=30)
        (probe/(label+'_cli.log')).write_text(proc.stdout)
        new_files=sorted(set(snapshot(baseline))-set(initial))
        observed.append(dict(metadata=label,exit=proc.returncode,collected_protected_paths=contracts.release_inputs(release),
            created_inside_synthetic_baseline=new_files,analysis_directory_created=output.exists()))
        assert proc.returncode==2
    assert not observed[0]['created_inside_synthetic_baseline']
    assert str(baseline/'analysis_malformed/failure.json') in observed[1]['created_inside_synthetic_baseline']
    save(probe/'verification.json',dict(synthetic_only=True,observations=observed,
        residual_reproduced=True,actual_raw_results_touched=False,compiler_calls=0,solver_calls=0))
    # R2: a split-form second macro declaration is not inspected by the v1.1
    # joined-prefix filter. This tests captured text, not an actual compiler.
    macro=OUT/'synthetic_probes/R2_split_macro_capture';macro.mkdir(parents=True)
    fixture=ContractFixture(macro)
    baseline_digest=sha(fixture.path);checker.binding(fixture.path,baseline_digest)
    fixture.env['compile_command']+=' -D URV_PREPARATION_ONLY=1'
    changed_digest=fixture.refresh()
    accepted=checker.binding(fixture.path,changed_digest)
    assert accepted['provenance']==fixture.document['provenance']
    save(macro/'verification.json',dict(synthetic_only=True,
        captured_command=fixture.env['compile_command'],binding_function_returned_success=True,
        joined_and_split_macro_declarations_both_present=True,
        actual_compiler_invoked=False,actual_native_binary_compiled=False,
        actual_effective_macro_value='NOT_MEASURED_NO_COMPILER_RUN',
        actual_author_confirmation=False,actual_execution_authorization=False))
    # Confirm the frozen numerical methods and the documented F02 samples.
    numerical={}
    for file,names in [('check_results.py',['diagnostics','check_slice','compare_legacy','aggregate']),
                       ('read_fields.py',['payloads','leaves','audit'])]:
        a=(OLD/'analysis'/file).read_text();b=(NEW/'analysis'/file).read_text()
        aa={n.name:ast.get_source_segment(a,n) for n in ast.parse(a).body if isinstance(n,ast.FunctionDef)}
        bb={n.name:ast.get_source_segment(b,n) for n in ast.parse(b).body if isinstance(n,ast.FunctionDef)}
        for name in names:assert aa[name]==bb[name];numerical[file+':'+name]=True
    examples=[]
    for directory in ['existing_h75_P_self_comparison','existing_h75_T_self_comparison',
                      'SYNTHETIC_h75_changed_trajectory/analysis']:
        p=PREV/'validation_examples'/directory/'regression_comparison.json'
        result=json.loads(p.read_text());assert len(result['legacy']['all_common_columns'])==20
        examples.append(dict(path=str(p),sha256=sha(p),columns=20,legacy_gate_PASS=result['legacy_gate_PASS']))
    assert examples[0]['legacy_gate_PASS'] and examples[1]['legacy_gate_PASS'] and not examples[2]['legacy_gate_PASS']
    assert before=={p:sha(p) for p in before}
    assert not (OLD/'results').exists() and not (NEW/'results').exists()
    save(OUT/'verification.json',dict(readonly_review_completed=True,review_id='URV-v1.1-READONLY-20261101',
        protected_existing_files_unchanged=len(before),seals=seals,existing_tests_rerun=70,
        existing_tests_passed=True,new_synthetic_probes=2,
        F01='RESIDUAL_R1_MALFORMED_METADATA',F02='CONFIRMED_WITHIN_REVIEW_SCOPE',
        F03='RESIDUAL_R2_SPLIT_MACRO_CAPTURE',F04='OPEN_PREVIOUSLY_KNOWN',
        unchanged_numerical_functions=numerical,F02_saved_examples=examples,
        source_or_threshold_edits=False,native_compiler_calls=0,solver_calls=0,actual_VTK_data_reader_calls=0,
        formal_execution_ready=False,effective_S0_binding=False,S0_started=False,
        formal_NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None,
        reference_qualified=False,strict_error_bound_established=False,submission_ready=False))
    print(json.dumps(dict(readonly_review_completed=True,existing_tests=70,residuals_reproduced=2,
        source_edits=False,solver_calls=0,S0_started=False)))

if __name__=='__main__':main()
