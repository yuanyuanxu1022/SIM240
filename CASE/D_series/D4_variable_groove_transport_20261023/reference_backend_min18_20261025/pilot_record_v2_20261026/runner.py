"""Default precheck only. No valid approved packet is distributed with this package."""
import argparse
from datetime import datetime,timezone
import os
from pathlib import Path
import signal
import subprocess
import sys
from common import HERE,ROOT,Rejected,digest,read_json,sha,validate,verify_lock,write_json
from records import inventory
from resources import MemoryGroup,cgroup_parent_check,hard_output_volume,supervise


def prerequisites(c):
    validate(c,execution=True)
    work,record=Path(c['work_dir']),Path(c['record_dir'])
    if work.exists() or record.exists(): raise Rejected('NO_OVERWRITE')
    volume=hard_output_volume(work.parent,c['resource_limits']['output_bytes'])
    cgroup_parent_check(c['cgroup_parent'])
    stat=os.statvfs(record.parent)
    mem=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
    if mem<c['resource_limits']['minimum_available_memory_bytes'] or stat.f_bavail*stat.f_frsize<c['resource_limits']['minimum_record_disk_bytes']:
        raise Rejected('INSUFFICIENT_AVAILABLE_RESOURCES')
    return dict(work_volume=volume,MemAvailable_bytes=mem,record_disk_available_bytes=stat.f_bavail*stat.f_frsize)


def _capture(c,argv,env,*,kind,group=None,limits=None,resource_before=None):
    work,record=Path(c['work_dir']),Path(c['record_dir'])
    record.mkdir(exist_ok=False); work.mkdir(exist_ok=False)
    for name in ('cache','tmp','config'): (work/name).mkdir()
    lock=read_json(HERE/'source_lock.json')
    before={p:sha(p) for p in lock['files']}
    write_json(record/'contract.json',c)
    write_json(record/'source_lock.json',lock)
    write_json(record/'STARTED.json',dict(kind=kind,contract_sha256=digest(c),argv=c['argv'],
        effective_argv=argv,work_dir=str(work),record_dir=str(record),run_id=c['run_id'],parent_pid=os.getpid(),
        started_utc=datetime.now(timezone.utc).isoformat(),inputs_sha256_before=before,
        environment=env,resource_before=resource_before,worker_nonce=os.urandom(24).hex()))
    result={}; proc=None
    try:
        with (work/'stdout.log').open('xb') as out,(work/'stderr.log').open('xb') as err:
            proc=subprocess.Popen(argv,cwd=work,env=env,stdout=out,stderr=err,
                                  close_fds=True,start_new_session=True)
            result=supervise(proc,work,limits or c['resource_limits'],group)
    except BaseException as exc:
        result['supervisor_error']=type(exc).__name__+':'+str(exc)
        if group: group.kill()
        if proc and proc.returncode is None:
            try: os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            result['independent_exit_code']=proc.wait()
    finally:
        # The record volume is separate, so tmpfs exhaustion cannot prevent exit recording.
        code=result.get('independent_exit_code')
        (record/'independent_exit_code.txt').write_text('START_FAILED\n' if code is None else str(code)+'\n')
        result.update(kind=kind,contract_sha256=digest(c),run_id=c['run_id'],
                      ended_utc=datetime.now(timezone.utc).isoformat(),
                      inputs_sha256_after={p:sha(p) if Path(p).is_file() else None for p in before})
        result['inputs_unchanged']=before==result['inputs_sha256_after']
        try: result['work_files']=inventory(work)
        except OSError as exc: result['inventory_error']=repr(exc)
        result.update(status='CHILD_EXITED_UNVERIFIED',NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None)
        write_json(record/'capture_manifest.json',result)
    return result


def run(c):
    before=prerequisites(c)  # Every gate precedes cgroup, files, subprocess and backend.
    group=MemoryGroup(c['cgroup_parent'],'sim240-'+c['run_id'],c['resource_limits']['memory_bytes'])
    try:
        argv=[str(ROOT/'.backend/bin/python'),'-B',str(HERE/'bootstrap.py'),str(group.path),*c['argv']]
        return _capture(c,argv,c['environment'],kind='REAL_DIAGNOSTIC_UNVERIFIED',group=group,resource_before=before)
    finally: group.close()


def synthetic(c,mode,*,limits=None,group=None):
    # Fixed fixture only; no arbitrary command / PDE module can be supplied.
    if mode not in {'success','failure','sleep','output','memory'}: raise Rejected('FIXED_FIXTURE_ONLY')
    argv=[sys.executable,'-B',str(HERE/'synthetic_child.py'),mode]
    if group: argv=[sys.executable,'-B',str(HERE/'bootstrap.py'),str(group.path),*argv]
    env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    return _capture(c,argv,env,kind='SYNTHETIC_PROCESS_NOT_PDE',limits=limits,group=group)


def main():
    p=argparse.ArgumentParser(description='Default static precheck; never implicitly executes')
    p.add_argument('--contract',type=Path,required=True);p.add_argument('--execute',action='store_true')
    a=p.parse_args();c=read_json(a.contract)
    if not a.execute:
        validate(c,execution=False);print('PREPARATION_ONLY; EXECUTION_NOT_AUTHORIZED');return 0
    result=run(c)
    return 0 if result.get('independent_exit_code')==0 and not result.get('stop_reason') and result['inputs_unchanged'] else 2


if __name__=='__main__':raise SystemExit(main())
