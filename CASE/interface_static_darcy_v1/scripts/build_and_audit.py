#!/usr/bin/env python3
"""Compile, mesh, and audit only. This file has no flow-solve mode."""
import ast
import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-mesh',action='store_true',help='Explicitly re-audit the existing mesh, without regenerating it')
    args=parser.parse_args()
    if os.environ.get('WM_PROJECT_VERSION')!='13':
        raise RuntimeError('Requires the existing Foundation 13 environment')
    reports=ROOT/'reports'; reports.mkdir(exist_ok=True)
    attempts=reports/'preparation_attempts';attempts.mkdir(exist_ok=True)
    number=1
    while (attempts/f'{number:03}').exists():number+=1
    logs=attempts/f'{number:03}';logs.mkdir()
    commands=[]
    def call(label,argv,cwd=ROOT,env=None):
        start=time.time()
        with (logs/(label+'.log')).open('w') as log:
            result=subprocess.run(argv,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300)
        commands.append(dict(label=label,argv=[str(x) for x in argv],cwd=str(cwd),exit_code=result.returncode,seconds=time.time()-start,log=str((logs/(label+'.log')).relative_to(ROOT))))
        (logs/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        if result.returncode:raise RuntimeError(label+' failed; inspect its log. No retry performed.')
        return (logs/(label+'.log')).read_text()
    call('compile_2d',['g++','-std=c++17','-O2','-Wall','-Wextra','-Wpedantic','-Werror','two_dimensional/darcy2d.cpp','-o','build/bin/darcy2d'])
    env=dict(os.environ,SDI_BUILD_BIN=str(ROOT/'build/bin'))
    call('compile_openfoam',['wmake'],ROOT/'openfoam/application',env)
    case=ROOT/'openfoam/cases/C01'
    if (case/'constant/polyMesh').exists():
        if not args.reuse_mesh:raise FileExistsError('Mesh already exists; no automatic regeneration')
    else:
        if args.reuse_mesh:raise FileNotFoundError('No mesh to reuse')
        call('blockMesh',['blockMesh','-case',str(case)])
    log=call('checkMesh',['checkMesh','-case',str(case),'-allGeometry','-allTopology'])
    if 'Mesh OK.' not in log:raise RuntimeError('checkMesh did not report Mesh OK')
    two=json.loads(call('audit_2d',[str(ROOT/'build/bin/darcy2d'),'--input',str(ROOT/'common/C01_2d.txt'),'--audit-only']).strip())
    text=call('audit_openfoam',[str(ROOT/'build/bin/depthAveragedDarcyFoam'),'-case',str(case),'-auditOnly'])
    foam=json.loads(next(line.split('SDI_AUDIT ',1)[1] for line in text.splitlines() if line.startswith('SDI_AUDIT ')))
    cfg=json.loads((ROOT/'common/C01.json').read_text())
    volume=cfg['L_m'][0]*cfg['L_m'][1]*cfg['H_m']
    for record in [two,foam]:
        assert record['audit_only'] and record['flow_solved'] is False and record['cells']==512
        assert abs(record['volume_m3']/volume-1)<1e-12
    assert foam['Dxx_m_minus2']==cfg['D_m_minus2'][0][0] and foam['Dyy_m_minus2']==cfg['D_m_minus2'][1][1]
    syntax=[]
    for p in ROOT.rglob('*.py'):
        if 'build' not in p.parts:
            ast.parse(p.read_text());syntax.append(str(p.relative_to(ROOT)))
    binding=[]
    for p in [ROOT/'two_dimensional/darcy2d.cpp',ROOT/'openfoam/application/depthAveragedDarcyFoam.C',ROOT/'openfoam/application/Make/files',ROOT/'openfoam/application/Make/options',ROOT/'build/bin/darcy2d',ROOT/'build/bin/depthAveragedDarcyFoam']:
        binding.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p)))
    report=dict(date='2026-10-30',protocol_id='SDI-v1',kind='COMPILE_MESH_AND_AUDIT_ONLY',
                commands=commands,environment={k:os.environ.get(k) for k in ['WM_PROJECT_DIR','WM_PROJECT_VERSION','WM_OPTIONS']},
                binary_source_binding=binding,two_dimensional_audit=two,openfoam_audit=foam,
                python_syntax_files=syntax,flow_solver_executed=False,geometry_scope='synthetic_average_domain_only',
                NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=None,geometry_PASS=True)
    (reports/'preparation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Both compiles, blockMesh/checkMesh, and audit-only input loading completed; no pressure solve.')


if __name__=='__main__':main()
