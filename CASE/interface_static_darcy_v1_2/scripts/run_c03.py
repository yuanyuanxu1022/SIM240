#!/usr/bin/env python3
"""Default: read-only preflight. --execute launches only the bound C03 pair."""
import argparse
import hashlib
import json
import os
import re
import resource
import shutil
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def preflight():
    manifest=json.loads((ROOT/'common/release_manifest.json').read_text())
    if manifest['case_id']!='C03' or manifest['protocol_id']!='SDI-v1':raise ValueError('Wrong release')
    for rec in manifest['files']:
        p=Path(rec['path'])
        if p.is_absolute() or '..' in p.parts:raise ValueError('Invalid release path')
        if sha(ROOT/p)!=rec['sha256']:raise ValueError('Release changed: '+str(p))
    for rec in manifest['libraries']:
        if sha(Path(rec['path']))!=rec['sha256']:raise ValueError('Runtime library changed: '+rec['path'])
    prep=json.loads((ROOT/'reports/preparation.json').read_text())
    if any(c['exit_code']!=0 for c in prep['commands']) or prep['flow_solver_executed'] is not False:raise ValueError('Missing clean preparation')
    for rec in prep['binary_source_binding']:
        if sha(ROOT/rec['path'])!=rec['sha256']:raise ValueError('Compile source/binary binding changed')
    cfg=json.loads((ROOT/'common/C03.json').read_text())
    if sha(ROOT/'common/protocol.json')!=cfg['source_hashes']['design_protocol']:raise ValueError('Protocol copy changed')
    for key,path in cfg['source_paths'].items():
        if sha(Path(path))!=cfg['source_hashes'][key]:raise ValueError('Upstream source changed: '+key)
    case=ROOT/'openfoam/cases/C03'
    if (case/'SDI_output').exists() or (case/'1').exists():raise ValueError('Template contains solver output')
    return manifest


def environment(manifest):
    env=dict(os.environ)
    env.update(manifest['openfoam_environment'])
    paths=sorted({str(Path(r['path']).parent) for r in manifest['libraries'] if '/OpenFOAM/' in r['path']})
    env['LD_LIBRARY_PATH']=':'.join(paths+([env['LD_LIBRARY_PATH']] if env.get('LD_LIBRARY_PATH') else []))
    env['OMP_NUM_THREADS']='1';env['OPENBLAS_NUM_THREADS']='1'
    return env


def cap_memory():
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--run-id',default='SDI_C03_v1_2_20261030_01')
    args=parser.parse_args()
    if not re.fullmatch(r'SDI_C03_v1_2_[A-Za-z0-9_]+',args.run_id):raise ValueError('Invalid C03 run id')
    release=preflight()
    if not args.execute:
        print(json.dumps(dict(preflight_satisfied=True,case_id='C03',flow_solver_executed=False,planned_run_id=args.run_id)))
        return 0
    run=ROOT/'runs'/args.run_id
    run.parent.mkdir(exist_ok=True);run.mkdir(exist_ok=False)
    for folder in ['common','bin','provenance','logs']: (run/folder).mkdir()
    for name in ['C03.json','C03_2d.txt','protocol.json','PROTOCOL.md']:
        shutil.copy2(ROOT/'common'/name,run/'common'/name)
    for name in ['darcy2d','depthAveragedDarcyFoam']:shutil.copy2(ROOT/'build/bin'/name,run/'bin'/name)
    shutil.copytree(ROOT/'openfoam/cases/C03',run/'openfoam')
    for rel in ['two_dimensional/darcy2d.cpp','openfoam/application/depthAveragedDarcyFoam.C','openfoam/application/Make/files','openfoam/application/Make/options','analysis/check_results.py','scripts/run_c03.py','reports/preparation.json','common/release_manifest.json']:
        target=run/'provenance'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,target)
    bound=[dict(path=str(p.relative_to(run)),sha256=sha(p)) for p in sorted(run.rglob('*')) if p.is_file()]
    record=dict(protocol_id='SDI-v1',case_id='C03',run_id=args.run_id,files=bound,
                release_manifest_sha256=sha(ROOT/'common/release_manifest.json'),libraries=release['libraries'],
                environment=release['openfoam_environment'],prepared_launch_only=False)
    (run/'run_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    state=dict(case_id='C03',run_id=args.run_id,status='started',start_time_unix=time.time(),steps=[],result_acceptance='NOT_EVALUATED')
    def save(): (run/'execution.json').write_text(json.dumps(state,indent=2)+'\n')
    save()
    steps=[('two_dimensional',[str(run/'bin/darcy2d'),'--input',str(run/'common/C03_2d.txt'),'--output',str(run/'two_dimensional')]),
           ('openfoam',[str(run/'bin/depthAveragedDarcyFoam'),'-case',str(run/'openfoam')])]
    try:
        for label,cmd in steps:
            start=time.time();timed_out=False
            with (run/'logs'/(label+'.log')).open('w') as log:
                try:
                    result=subprocess.run(cmd,cwd=run,env=environment(release),stdout=log,stderr=subprocess.STDOUT,
                                          timeout=300,preexec_fn=cap_memory)
                    code=result.returncode
                except subprocess.TimeoutExpired:code=124;timed_out=True
            state['steps'].append(dict(label=label,argv=cmd,exit_code=code,seconds=time.time()-start,timed_out=timed_out));save()
            if code:
                state.update(status='failed',end_time_unix=time.time());save()
                print('C03 stopped after '+label+'; outputs and exit code retained. No retry.')
                return code if code>0 else 1
    except BaseException as exc:
        state.update(status='interrupted_or_error',error=str(exc),end_time_unix=time.time());save();raise
    state.update(status='completed',end_time_unix=time.time());save()
    print('C03 pair completed. Result analysis has not been run. Evidence: '+str(run))
    return 0


if __name__=='__main__':raise SystemExit(main())
