#!/usr/bin/env python3
"""Read-only package verification plus rejection CLI tests; never invokes a solver."""
from pathlib import Path
import ast
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
REPORT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_v1'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()

def main():
    seal=CASE/'evidence/preparation_seal.json';digest=sha(seal)
    assert digest==(CASE/'evidence/preparation_seal.sha256').read_text().strip()
    bound=json.loads(seal.read_text())
    assert not bound['simulation_authorized'] and bound['preparation_only_build']
    assert bound['approved_run_ids']==bound['actual_formal_run_ids']==[]
    assert all(sha(p)==s for p,s in bound['inputs_sha256'].items())
    protected=json.loads((REPORT/'protected_inputs_before.json').read_text())
    assert all(sha(p)==s for p,s in protected.items())
    audit=CASE/'audits/URV_ZERO_20261101_01'
    zero=json.loads((audit/'verification.json').read_text())
    assert zero['actual_time_steps']==0 and zero['initialized_frames_read']==24
    assert all(sha(p)==s for p,s in json.loads((audit/'audit_files_sha256.json').read_text()).items())
    assert not (CASE/'results').exists()
    for p in CASE.rglob('*.py'):
        if 'audits' not in p.parts:ast.parse(p.read_text(),filename=str(p))
    # External checker calls must refuse the current release, even if given real
    # initialized outputs. Rejection receipts are analysis artifacts, not run results.
    native=next(audit.glob('URV1_H75_P*/initialize'))
    attempts=[]
    for label,anchor in [('preparation_release',digest),('wrong_release_hash','0'*64)]:
        dest=REPORT/'checker_cli_rejections'/label
        assert not dest.exists()
        proc=subprocess.run([sys.executable,'-B',str(CASE/'analysis/check_results.py'),
            '--run',str(native),'--release',str(seal),'--release-sha256',anchor,
            '--out',str(dest)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,
            env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'),timeout=30)
        (dest/'cli.log').write_text(proc.stdout)
        receipt=json.loads((dest/'failure.json').read_text())
        assert proc.returncode==2 and receipt['RESULT_PASS'] is False
        assert not (dest/'acceptance.json').exists()
        attempts.append(dict(test=label,independent_exit_code=proc.returncode,RESULT_PASS=False,
            accepted=False,error=receipt['error']))
    assert all(sha(p)==s for p,s in protected.items())
    assert all(sha(p)==s for p,s in bound['inputs_sha256'].items())
    evidence=dict(PREPARATION_PASS=True,preparation_seal_sha256=digest,
        compilation_dependencies=len(json.loads((CASE/'evidence/build_environment.json').read_text())['dependency_sha256']),
        package_input_bindings=len(bound['inputs_sha256']),protected_old_inputs=len(protected),
        original_inputs_unchanged=True,native_describe=24,native_precheck=24,native_initialize=24,
        actual_reader_frames=24,actual_time_steps=0,formal_runs_started=0,
        Python_tests=35,C_plus_plus_arithmetic_test_programs=2,
        cli_rejections=attempts,formal_NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,
        new_reference_qualified=False,strict_error_bound_established=False,submission_ready=False,
        external_data_history='PENDING',new_completed_URV_end_to_end_acceptance='NOT_EVALUATED')
    (REPORT/'verification.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(evidence,ensure_ascii=False))

if __name__=='__main__': main()
