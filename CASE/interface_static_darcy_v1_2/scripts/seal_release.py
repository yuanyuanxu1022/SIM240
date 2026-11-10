#!/usr/bin/env python3
"""Seal existing compilation/static evidence. Never build or launch a flow solver."""
import ast
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    target=ROOT/'common/release_manifest.json'
    if target.exists():raise FileExistsError('Release already sealed; no silent reseal')
    preparation=json.loads((ROOT/'reports/preparation.json').read_text())
    for r in preparation['binary_source_binding']:
        if sha(ROOT/r['path'])!=r['sha256']:raise ValueError('Compile binding changed')
    for p in ROOT.rglob('*.py'):
        if 'build' not in p.parts:ast.parse(p.read_text())
    libraries={}
    for name in ['darcy2d','depthAveragedDarcyFoam']:
        result=subprocess.run(['ldd',str(ROOT/'build/bin'/name)],text=True,capture_output=True,check=True)
        if 'not found' in result.stdout:raise ValueError('Missing runtime library')
        (ROOT/'reports'/('ldd_'+name+'.log')).write_text(result.stdout)
        for line in result.stdout.splitlines():
            for token in line.split():
                if token.startswith('/'):
                    p=Path(token)
                    if p.is_file():libraries[str(p)]=sha(p)
    paths=set()
    for folder in ['common','two_dimensional','openfoam/cases/C03','analysis','scripts','tests','reports']:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':paths.add(p)
    for rel in ['README.md','.gitignore','openfoam/application/depthAveragedDarcyFoam.C','openfoam/application/Make/files','openfoam/application/Make/options','build/bin/darcy2d','build/bin/depthAveragedDarcyFoam']:paths.add(ROOT/rel)
    env={k:os.environ[k] for k in ['WM_PROJECT_DIR','WM_PROJECT_VERSION','WM_OPTIONS','FOAM_LIBBIN']}
    env['FOAM_INST_DIR']=str(Path(env['WM_PROJECT_DIR']).parent)
    report=dict(release_version='1.2.0',checker_version='1.2.0',protocol_id='SDI-v1',case_id='C03',date='2026-10-30',status='PREPARED_NOT_RUN',
                launch_ready=True,flow_run_authorized_by_preparation=False,actual_run_id=None,
                planned_run_id='SDI_C03_v1_2_20261030_01',files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in sorted(paths)],
                libraries=[dict(path=p,sha256=s) for p,s in sorted(libraries.items())],openfoam_environment=env,
                NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=None,geometry_PASS=True,geometry_scope='synthetic_average_domain_only')
    target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(files_bound=len(paths),libraries_bound=len(libraries),flow_solved=False,launch_ready=True)))


if __name__=='__main__':main()
