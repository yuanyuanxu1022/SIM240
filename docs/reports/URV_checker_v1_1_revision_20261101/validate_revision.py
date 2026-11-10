#!/usr/bin/env python3
"""Persist software validation artifacts and verify all frozen original inputs.

No compiler/native solver/VTK data reader is called. Python sources are compiled
in memory for syntax checking, with no cache written into either CASE.
"""
from pathlib import Path
import ast
import csv
import difflib
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
OLD=ROOT/'CASE/unseen_v2_reference_v1'
NEW=ROOT/'CASE/unseen_v2_reference_checker_v1_1'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for data in iter(lambda:f.read(1<<20),b''):h.update(data)
    return h.hexdigest()

def save(p,data):
    if p.exists():raise FileExistsError(p)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def main():
    initial=json.loads((OUT/'original_case_before.json').read_text())
    assert initial=={str(p):sha(p) for p in OLD.rglob('*') if p.is_file()}
    protected=json.loads((OUT/'protected_inputs_before.json').read_text())
    assert all(sha(p)==s for p,s in protected.items())
    seal=OLD/'evidence/preparation_seal.json';bound=json.loads(seal.read_text())
    assert all(sha(p)==s for p,s in bound['inputs_sha256'].items())
    assert 'Ran 70 tests' in (OUT/'tests_final.log').read_text() and '\nOK\n' in (OUT/'tests_final.log').read_text()
    sources=0
    for p in NEW.rglob('*.py'):
        compile(p.read_text(),str(p),'exec');sources+=1
    unchanged={}
    for file,names in [('check_results.py',['diagnostics','check_slice','compare_legacy','aggregate']),
                       ('read_fields.py',['payloads','leaves','audit'])]:
        a=(OLD/'analysis'/file).read_text();b=(NEW/'analysis'/file).read_text()
        aa={n.name:ast.get_source_segment(a,n) for n in ast.parse(a).body if isinstance(n,ast.FunctionDef)}
        bb={n.name:ast.get_source_segment(b,n) for n in ast.parse(b).body if isinstance(n,ast.FunctionDef)}
        for name in names:
            assert aa[name]==bb[name]
            unchanged[file+':'+name]=dict(byte_identical=True,characters=len(aa[name]))
    assert (OLD/'analysis/evidence.py').read_bytes()==(NEW/'analysis/evidence.py').read_bytes()
    common={}
    for p in (OLD/'common').iterdir():
        if p.is_file():assert sha(p)==sha(NEW/'common'/p.name);common[p.name]=sha(p)
    save(OUT/'unchanged_numerics.json',dict(functions=unchanged,evidence_module_unchanged=True,
        original_common_files_identical=common,physical_thresholds_changed=False))
    for name in ['check_results.py','read_fields.py']:
        a=(OLD/'analysis'/name).read_text();b=(NEW/'analysis'/name).read_text()
        (OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='v1/'+name,tofile='v1.1/'+name)))
    sys.path.insert(0,str(NEW/'analysis'))
    import check_results as checker
    from evidence import kv
    foundation=ROOT/'CASE/D_series/D4_variable_groove_transport_20261023/results/foundation_20261023_v1'
    reports=[]
    for direction in ['P','T']:
        run=next(foundation.glob('*regression*_'+direction+'_*'))/'steady'
        reference=dict(directory=str(run),result_sha256=sha(run/'result.txt'),diagnostics_sha256=sha(run/'diagnostics.csv'))
        target=OUT/'validation_examples'/('existing_h75_'+direction+'_self_comparison');target.mkdir(parents=True)
        K=float(kv(run/'result.txt')['Keff_m3'])
        result=checker.regression_check(run,reference,K,target)
        assert result['legacy']['all_exact'] and len(result['legacy']['all_common_columns'])==20
        reports.append(dict(example='existing_control_self_comparison_not_new_run',direction=direction,
            common_columns=20,diagnostic_rows=result['legacy']['old_rows'],difference=0,output=str(target)))
    # Full 20-column saved failure: only an explicitly artificial copy is edited.
    baseline=next(foundation.glob('*regression*_P_*'))/'steady'
    raw=OUT/'validation_examples/SYNTHETIC_h75_changed_trajectory/raw';raw.mkdir(parents=True)
    with (baseline/'diagnostics.csv').open() as f:reader=csv.DictReader(f);data=list(reader);keys=reader.fieldnames
    data[1]['J']=str(float(data[1]['J'])*1.001)
    with (raw/'diagnostics.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(data)
    (raw/'SYNTHETIC_MARKER.txt').write_text('Copied old control with one artificial diagnostic change; not a flow solution.\n')
    target=raw.parent/'analysis';target.mkdir()
    reference=dict(directory=str(baseline),result_sha256=sha(baseline/'result.txt'),diagnostics_sha256=sha(baseline/'diagnostics.csv'))
    try:checker.regression_check(raw,reference,float(kv(baseline/'result.txt')['Keff_m3']),target)
    except Exception as error:assert 'legacy trajectory difference' in str(error)
    else:raise AssertionError('artificial trajectory change accepted')
    compared=json.loads((target/'regression_comparison.json').read_text())
    assert len(compared['legacy']['all_common_columns'])==20 and not compared['legacy_gate_PASS']
    save(raw.parent/'verification.json',dict(synthetic=True,all_20_columns_saved=True,accepted=False,solver_calls=0))
    # Re-run exactly the previously accepted deficient contract through the new CLI.
    old_fixture=ROOT/'docs/reports/URV_v1_readonly_review_S0_20261101/synthetic_probes/incomplete_release/SYNTHETIC_NOT_AN_EXECUTION_CONTRACT.json'
    probe=OUT/'validation_examples/F03_old_deficient_contract_rejected'
    fake_raw=OUT/'validation_examples/SYNTHETIC_EMPTY_RAW';fake_raw.mkdir()
    command=[sys.executable,'-B',str(NEW/'analysis/check_results.py'),'--run',str(fake_raw),
        '--release',str(old_fixture),'--release-sha256',sha(old_fixture),'--out',str(probe)]
    proc=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,
        env=dict(os.environ,OPENBLAS_NUM_THREADS='1'),timeout=30)
    assert proc.returncode==2 and not (probe/'acceptance.json').exists()
    (probe/'cli.log').write_text(proc.stdout)
    assert 'schema URV-EXEC-1.1 required' in proc.stdout
    assert list(fake_raw.iterdir())==[]
    assert initial=={str(p):sha(p) for p in OLD.rglob('*') if p.is_file()}
    assert all(sha(p)==s for p,s in protected.items())
    assert not (OLD/'results').exists()
    status=dict(revision_id='URV-CHECKER-v1.1-20261101',software_preparation_PASS=True,
        F01='ADDRESSED_AND_TESTED',F02='ADDRESSED_AND_TESTED',F03='ADDRESSED_AND_TESTED',
        F04='OPEN_OUT_OF_SCOPE',unit_tests=70,original_tests=35,revision_tests=35,
        Python_sources_compiled_in_memory=sources,original_CASE_files_unchanged=len(initial),
        original_preparation_inputs_unchanged=len(bound['inputs_sha256']),protected_old_bindings_unchanged=len(protected),
        full_20_column_examples=reports,synthetic_full_20_column_failure_saved=True,
        old_deficient_contract_cli_exit=2,native_compiler_calls=0,solver_calls=0,new_VTK_data_reader_calls=0,
        source_physics_or_threshold_changes=False,S0_started=False,actual_formal_run_ids=[],
        external_data_history='PENDING_AUTHOR_CHECK',effective_execution_binding=False,
        formal_NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None,
        reference_qualified=False,strict_error_bound_established=False,submission_ready=False,
        new_URV_completed_result_end_to_end_validation='NOT_EVALUATED')
    save(OUT/'verification.json',status)
    print(json.dumps(status,ensure_ascii=False))

if __name__=='__main__':main()
