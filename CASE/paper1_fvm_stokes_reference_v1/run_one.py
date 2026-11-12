#!/usr/bin/env python3
"""Prepared single-case runner. Execute ONLY after the user launches it explicitly.

Never advances to another mesh, direction, Gate, retry or acceptance assessment.
Requires an unchanged release manifest and sourced OpenFOAM Foundation 13.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time
import uuid

ROOT=Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_release():
    release=ROOT/'release_manifest.json'
    data=json.loads(release.read_text())
    if data.get('status')!='PREPARED_NOT_RUN':
        raise RuntimeError('unexpected release status')
    for rel,expected in data['sha256'].items():
        path=ROOT/rel
        if not path.is_file() or digest(path)!=expected:
            raise RuntimeError('release drift: '+rel)
    for absolute,expected in data.get('external_sha256',{}).items():
        path=Path(absolute)
        if not path.is_file() or digest(path)!=expected:
            raise RuntimeError('OpenFOAM library drift: '+absolute)
    return release


def limits():
    resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE,(256*1024**2,256*1024**2))
    os.nice(5)


def command(args,log,seconds,env):
    started=time.monotonic()
    with log.open('xb') as stream:
        proc=subprocess.Popen(args,stdout=stream,stderr=subprocess.STDOUT,env=env,
                              start_new_session=True,preexec_fn=limits)
        try:
            code=proc.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL)
            proc.wait()
            code=124
    return dict(argv=args,independent_exit_code=code,elapsed_seconds=time.monotonic()-started)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',required=True)
    parser.add_argument('--execute',action='store_true',help='explicit operator launch, no implied authorization')
    args=parser.parse_args()
    if not args.execute:
        parser.error('preparation only; --execute is required for an explicitly authorized launch')
    if os.environ.get('WM_PROJECT_VERSION')!='13' or os.environ.get('WM_PROJECT_DIR')!='/opt/openfoam13':
        raise RuntimeError('source /opt/openfoam13/etc/bashrc first; other OpenFOAM versions are not validated')
    release=verify_release()
    if json.loads(release.read_text()).get('formal_review_status')!='ASTRA_FINAL_STATIC_RECHECK_COMPLETE':
        raise RuntimeError('Specified Astra final static recheck is pending; this prepared release cannot launch')
    plan=json.loads((ROOT/'prepared_manifest.json').read_text())
    ids={c['case_id'] for c in plan['cases']}
    if args.case not in ids:
        raise RuntimeError('case is outside the frozen 26 input records')
    case=ROOT/'prepared'/args.case
    evidence=case/'referenceEvidence'
    if evidence.exists() or (case/'runtime').exists():
        raise RuntimeError('previous evidence exists; no overwrite, resume or retry is authorized')
    runtime=case/'runtime';runtime.mkdir()
    run_id=args.case+'_'+time.strftime('%Y%m%dT%H%M%S')+'_'+uuid.uuid4().hex[:8]
    exe=ROOT/'bin/paper1StokesReference'
    source_hash=digest(release)
    env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    receipt=dict(run_id=run_id,case_id=args.case,source_manifest_sha256=source_hash,
                 executable_sha256=digest(exe),openfoam_version=env['WM_PROJECT_VERSION'],
                 execution_scope='this case only',solver_converged=False,commands=[])
    (runtime/'started.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (runtime/'release_snapshot.json').write_bytes(release.read_bytes())
    for tool in ('blockMesh','checkMesh'):
        info=command(['/opt/openfoam13/platforms/linux64GccDPInt32Opt/bin/'+tool,'-case',str(case)],
                     runtime/('log.'+tool),120,env)
        receipt['commands'].append(info)
        if info['independent_exit_code']!=0:
            receipt['independent_exit_code']=info['independent_exit_code']
            (runtime/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
            raise RuntimeError(tool+' failed; stop, no solver launched')
    if 'Mesh OK.' not in (runtime/'log.checkMesh').read_text():
        raise RuntimeError('checkMesh has no Mesh OK; stop')
    info=command(['/usr/bin/time','-v','-o',str(runtime/'resource.txt'),str(exe),'-case',str(case)],
                 runtime/'log.solver',1800,env)
    receipt['commands'].append(info)
    receipt['independent_exit_code']=info['independent_exit_code']
    (runtime/'exit_code.txt').write_text(str(info['independent_exit_code'])+'\n')
    receipt['solver_converged']='solution converged' in (runtime/'log.solver').read_text().lower()
    try:
        verify_release()
        receipt['release_unchanged']=digest(release)==source_hash
    except RuntimeError:
        receipt['release_unchanged']=False
    receipt['evidence_sha256']={p.name:digest(p) for p in evidence.glob('*.csv')} if evidence.exists() else {}
    meta=json.loads((case/'case.json').read_text())
    times=sorted((float(p.name),p) for p in case.iterdir()
                 if p.is_dir() and p.name.replace('.','',1).isdigit() and float(p.name)>0)
    native_names=('v',) if meta['direction']=='P' else ('U','p','phi')
    receipt['native_field_sha256']={}
    if times:
        final=times[-1][1]
        for name in native_names:
            path=final/name
            if path.is_file():receipt['native_field_sha256'][str(path.relative_to(case))]=digest(path)
    receipt['mesh_sha256']={}
    for name in ('points','faces','owner','neighbour','boundary'):
        path=case/'constant/polyMesh'/name
        if path.is_file():receipt['mesh_sha256'][name]=digest(path)
    receipt['runtime_logs_sha256']={p.name:digest(p) for p in runtime.iterdir() if p.is_file() and p.name not in ('started.json','receipt.json')}
    receipt['case_disk_bytes']=sum(p.stat().st_size for p in case.rglob('*') if p.is_file())
    receipt['disk_budget_met']=receipt['case_disk_bytes']<=1024**3
    if not receipt['release_unchanged'] or not receipt['disk_budget_met']:
        receipt['solver_converged']=False
    (runtime/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if evidence.exists():
        (evidence/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(run_id=run_id,exit_code=info['independent_exit_code'],
                         solver_converged=receipt['solver_converged'],
                         numerical_reference_accepted=False)))
    return 0 if info['independent_exit_code']==0 else 1


if __name__=='__main__':
    raise SystemExit(main())
