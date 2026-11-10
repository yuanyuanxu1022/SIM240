#!/usr/bin/env python3
"""Freeze already verified preparation once; no solver execution."""
from pathlib import Path
import ast
import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
import numpy as np

BASE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def capture(command,cwd=None):
    p=subprocess.run(command,cwd=cwd,capture_output=True,text=True,timeout=30)
    if p.returncode:raise RuntimeError('metadata command failed '+repr(command))
    return p.stdout.strip()

def main():
    target=BASE/'evidence/build_binding.json'
    if target.exists():raise RuntimeError('binding exists; no overwrite')
    verification=json.loads((BASE/'evidence/preparation_verification_final.json').read_text())
    assert verification['preparation_pass'] and verification['spatial_steps_executed']==0
    assert verification['initialization_count']==20 and not verification['formal_batches_started']
    assert int((BASE/'evidence/verification_final_exit_code.txt').read_text())==0
    assert int((BASE/'evidence/test_contracts_v1_exit_code.txt').read_text())==0
    assert all(x['passed'] for x in json.loads((BASE/'evidence/CLI_guard_checks.json').read_text()))
    for p in BASE.glob('*.py'):ast.parse(p.read_text())
    assert subprocess.run(['make','-q'],cwd=BASE,capture_output=True).returncode==0
    protected=json.loads((BASE/'evidence/protected_inputs.json').read_text())
    assert all(Path(p).is_file() and sha(p)==h for p,h in protected.items())
    root=Path('/home/dell/openlb')
    env=dict(prepared_utc=dt.datetime.now(dt.timezone.utc).isoformat(),python=sys.version,
        python_executable=sys.executable,numpy=np.__version__,platform=platform.platform(),
        compiler=capture(['mpic++','--version']),mpi_compiler_command=capture(['mpic++','--showme']),
        openlb_head=capture(['git','rev-parse','HEAD'],root),
        openlb_citation=(root/'CITATION.cff').read_text(),
        custom_compile_label='882924a9-alpha-c-diagnostic; not the OpenLB library version',
        scientific_writing_skill_record=dict(arxiv='2609.00065',current_version_checked='v2',
            checked_date='2026-10-22',authors=['Timothy Kassis','Vinayak Agarwal','Yuhuan He','Darshil Patel','Aubrey M. Brueckner']))
    (BASE/'evidence/environment.json').write_text(json.dumps(env,indent=2)+'\n')
    hashes=dict(protected)
    for p in BASE.iterdir():
        if p.is_file() and p.suffix in ('.py','.md','.json','.txt') or p.name=='Makefile':hashes[str(p.resolve())]=sha(p)
    for folder in ('src','build','reference','before','evidence'):
        for p in (BASE/folder).rglob('*'):
            if not p.is_file() or '__pycache__' in p.parts or p.suffix=='.pyc':continue
            if folder=='evidence' and (p.name=='build_binding.json' or p.name.startswith('freeze_') or p.name=='final_preflight.json'):continue
            hashes[str(p.resolve())]=sha(p)
    for p in (root/'src').rglob('*'):
        if p.is_file():hashes[str(p.resolve())]=sha(p)
    for p in [root/'config.mk',root/'CITATION.cff',root/'build/lib/libolbcore.a']+list((root/'external/lib').glob('*.a')):
        hashes[str(p.resolve())]=sha(p)
    payload=dict(created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),protocol_id='ALPHA_C_DIAGNOSTICS_20261022_v1',
                 openlb_head=env['openlb_head'],old_protected_count=len(protected),
                 formal_space_runs_started=False,sha256=hashes)
    with target.open('x') as f:f.write(json.dumps(payload,indent=2)+'\n')
    # Read-only stage prechecks after the binding exists; they never pass --run.
    outcomes=[]
    for stage,wanted in (('alpha',0),('c',2)):
        p=subprocess.run([sys.executable,'run_suite.py','--stage',stage],cwd=BASE,capture_output=True,text=True,timeout=30)
        assert p.returncode==wanted,(stage,p.stdout,p.stderr)
        if stage=='c':assert 'C waits for completed alpha analysis' in p.stderr
        outcomes.append(dict(stage=stage,exit_code=p.returncode,expected_exit=wanted,stdout=p.stdout,stderr=p.stderr))
    bad=[p for p,h in hashes.items() if not Path(p).is_file() or sha(p)!=h];assert not bad
    for stage in ('alpha','c'):
        for folder in ('output','evidence'):assert not (BASE/folder/('alpha_c_20261022_v1_'+stage)).exists()
    final=dict(frozen=True,bound_file_count=len(hashes),protected_file_count=len(protected),mismatches=bad,
        prechecks=outcomes,formal_spatial_steps_executed=0,formal_batches_started=False,
        alpha_command_prepared=True,c_command_not_delivered=True,
        NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS='NOT_EVALUATED',geometry_PASS='NOT_EVALUATED')
    (BASE/'evidence/final_preflight.json').write_text(json.dumps(final,indent=2)+'\n')
    print('FROZEN_PREPARATION_OK:',len(hashes),'bound files;',len(protected),'protected old files; alpha precheck0; C dependency rejection2; no formal run')

if __name__=='__main__':main()
