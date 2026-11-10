#!/usr/bin/env python3
"""Default is read-only preflight. --execute requires an explicit new run ID."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import time
PKG=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def preflight(root=PKG):
    release=json.loads((root/'common/release_manifest.json').read_text())
    if release['case_id']!='GDI01' or release['protocol_id']!='GDI-v1':raise ValueError('Wrong release identity')
    seen=set()
    for rec in release['files']:
        p=Path(rec['path'])
        if p.is_absolute() or '..' in p.parts or str(p) in seen:raise ValueError('Unsafe release path')
        seen.add(str(p))
        if sha(root/p)!=rec['sha256']:raise ValueError('Release input/source/binary changed: '+str(p))
    for rec in release['libraries']:
        if sha(Path(rec['path']))!=rec['sha256']:raise ValueError('Runtime library changed: '+rec['path'])
    for path,digest in json.loads((root/'common/input_bindings.json').read_text()).items():
        if sha(Path(path) if path.startswith('/') else root.parents[1]/path)!=digest:raise ValueError('Upstream binding changed: '+path)
    prep=json.loads((root/'reports/preparation.json').read_text())
    if not prep['compile_pass'] or not prep['no_solve_audit_pass'] or prep['flow_solved'] or not prep['checker_tests_pass']:raise ValueError('Preparation evidence incomplete')
    cfg=json.loads((root/'common/GDI01.json').read_text())
    if sha(root/'common/protocol.json')!=cfg['GDI_protocol_sha256']:raise ValueError('Frozen protocol changed')
    for output in ['GDI_output','GDI_audit','1']:
        if (root/'cases/GDI01'/output).exists():raise ValueError('Template contains output: '+output)
    return release
def environment(release,library_dir):
    env=dict(os.environ);env.update(release['openfoam_environment'])
    paths=sorted({str(Path(r['path']).parent) for r in release['libraries']})
    env['LD_LIBRARY_PATH']=':'.join([str(library_dir)]+paths)
    env['OMP_NUM_THREADS']='1';env['OPENBLAS_NUM_THREADS']='1'
    return env
def cap_memory():
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--run-id');a=p.parse_args()
    release=preflight()
    if not a.execute:
        print(json.dumps(dict(preflight_satisfied=True,case_id='GDI01',protocol_id='GDI-v1',flow_solver_executed=False,run_id=None)));return 0
    if not a.run_id or not re.fullmatch(r'GDI01_v1_[A-Za-z0-9_]+',a.run_id):raise ValueError('Supply an explicit GDI01_v1_ prefixed run ID')
    run=PKG/'runs'/a.run_id;run.parent.mkdir(exist_ok=True);run.mkdir(exist_ok=False)
    for folder in ['bin','lib','logs','provenance']:(run/folder).mkdir()
    for folder in ['common','references']:shutil.copytree(PKG/folder,run/folder)
    shutil.copytree(PKG/'cases/GDI01',run/'openfoam')
    shutil.copy2(PKG/'build/bin/grooveDarcyStaticFoam',run/'bin/grooveDarcyStaticFoam')
    shutil.copy2(PKG/'build/lib/libgroovePorosity.so',run/'lib/libgroovePorosity.so')
    for folder in ['application','analysis','scripts','provenance/subclass']:
        for source in (PKG/folder).rglob('*'):
            if not source.is_file() or source.is_symlink() or 'linux64GccDPInt32Opt' in source.parts or '__pycache__' in source.parts:continue
            dest=(run if folder.startswith('provenance/') else run/'provenance')/source.relative_to(PKG)
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
    for rel in ['common/release_manifest.json','reports/preparation.json']:
        dest=run/'provenance'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(PKG/rel,dest)
    files=[dict(path=str(f.relative_to(run)),sha256=sha(f)) for f in sorted(run.rglob('*')) if f.is_file()]
    manifest=dict(protocol_id='GDI-v1',case_id='GDI01',run_id=a.run_id,files=files,
        release_manifest_sha256=sha(PKG/'common/release_manifest.json'),libraries=release['libraries'],
        environment=release['openfoam_environment'],simulation_authorization_acknowledged_by_execute_flag=True)
    (run/'run_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    state=dict(protocol_id='GDI-v1',case_id='GDI01',run_id=a.run_id,status='started',start_time_unix=time.time(),steps=[],result_acceptance='NOT_EVALUATED')
    def save():(run/'execution.json').write_text(json.dumps(state,indent=2)+'\n')
    save();cmd=[str(run/'bin/grooveDarcyStaticFoam'),'-case',str(run/'openfoam'),'-solve','-runId',a.run_id]
    start=time.monotonic();timeout=False
    try:
        with (run/'logs/openfoam.log').open('w') as log:
            try:r=subprocess.run(cmd,cwd=run,env=environment(release,run/'lib'),stdout=log,stderr=subprocess.STDOUT,timeout=300,preexec_fn=cap_memory);code=r.returncode
            except subprocess.TimeoutExpired:code=124;timeout=True
        state['steps'].append(dict(label='openfoam',argv=cmd,exit_code=code,seconds=time.monotonic()-start,timed_out=timeout))
        state.update(status='completed' if code==0 else 'failed',end_time_unix=time.time());save()
        print(json.dumps(dict(status=state['status'],run_dir=str(run),result_acceptance='NOT_EVALUATED',retry=False)))
        return code if code>=0 else 1
    except BaseException as exc:
        state.update(status='interrupted_or_error',error=str(exc),end_time_unix=time.time());save();raise
if __name__=='__main__':raise SystemExit(main())
