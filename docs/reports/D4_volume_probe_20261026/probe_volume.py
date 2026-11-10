"""Bounded filesystem/cache probes only. No mount or PDE execution capability."""
import argparse
import ctypes
from datetime import datetime
from zoneinfo import ZoneInfo
import errno
import hashlib
import json
import os
from pathlib import Path
import subprocess
import signal
import sys
import time
import uuid

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
PACKAGE=REPO/'CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/pilot_record_v3_1_20261026'
WORK=Path('/run/user/1000/sim240_pilot_n8_work_20261026')
RECORD=Path('/home/dell/yuanyuanxu/SIM240_runtime_records/reference_pilot_n8_20261026')

def bounded_command(argv,*,timeout=10,**kwargs):
    """Kill the complete compiler/loader process group on timeout."""
    proc=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
        start_new_session=True,**kwargs)
    try:out,err=proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        out,err=proc.communicate(timeout=5)
        err+='\nBOUNDED_COMMAND_TIMEOUT_PROCESS_GROUP_KILLED\n'
    return subprocess.CompletedProcess(argv,proc.returncode,out,err)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def sync_dir(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)

def save(path,obj):
    with path.open('x') as f:
        json.dump(obj,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    sync_dir(path.parent)

def packet():
    sys.path.insert(0,str(PACKAGE))
    from common import read_json,validate
    c=read_json(PACKAGE/'path_contract_draft.json');validate(c)
    assert Path(c['work_dir']).parent==WORK and Path(c['record_dir']).parent==RECORD
    assert c['authorized_to_execute'] is False and c['approval'] is None
    return c

def layout_check():
    # Exactly the reviewed read-only checker; no --execute and no backend.
    p=subprocess.run([sys.executable,'-B',str(PACKAGE/'precheck_layout.py')],
        capture_output=True,text=True,timeout=10)
    return {'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}

def persistent_probe():
    from resources import mount_identity
    identity=mount_identity(RECORD)
    if identity['filesystem'] not in {'ext4','xfs','btrfs','zfs'}:raise ValueError('PERSISTENT_FILESYSTEM_REQUIRED')
    st=RECORD.stat();fs=os.statvfs(RECORD)
    if RECORD.resolve()!=RECORD or st.st_uid!=1000 or (st.st_mode&0o777)!=0o700 or fs.f_bavail*fs.f_frsize<2*1024**3:
        raise ValueError('RECORD_PATH_NOT_READY')
    directory=RECORD/('volume_probe_persistent_'+uuid.uuid4().hex[:12]);directory.mkdir(mode=0o700)
    value=(b'SIM240_PERSISTENT_PROBE_NOT_PDE\n'*40000)[:1024**2]
    path=directory/'known_bytes.bin'
    with path.open('xb') as f:f.write(value);f.flush();os.fsync(f.fileno())
    sync_dir(directory)
    expected=hashlib.sha256(value).hexdigest();assert sha(path)==expected and path.stat().st_size==len(value)
    result={'status':'PERSISTENT_SMALL_FILE_PASS','kind':'FILESYSTEM_PROBE_NOT_PDE',
        'directory':str(directory),'file':str(path),'bytes':len(value),'sha256':expected,
        'identity':identity,'available_bytes_before':fs.f_bavail*fs.f_frsize}
    save(directory/'probe_result.json',result)
    return result

def checked_remove_probe(root,expected_files):
    """Only explicit files created by this invocation, never general cleanup."""
    if root.parent!=WORK or not root.name.startswith('volume_probe_') or root.is_symlink():
        raise ValueError('PROBE_CLEANUP_PATH_REJECTED')
    actual=[p for p in root.rglob('*') if p.is_file() or p.is_symlink()]
    if {str(p.relative_to(root)) for p in actual}!=set(expected_files) or any(p.is_symlink() for p in actual):
        raise ValueError('PROBE_CLEANUP_INVENTORY_CHANGED')
    for p in actual:p.unlink()
    for p in sorted((p for p in root.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):p.rmdir()
    root.rmdir();sync_dir(WORK)

def compiler_probe(record):
    root=WORK/('volume_probe_cache_'+uuid.uuid4().hex[:12]);root.mkdir(mode=0o700)
    (root/'tmp').mkdir();(root/'cache').mkdir()
    source=root/'constant.c';library=root/'cache/constant.so'
    source.write_text('int sim240_probe_constant(void) { return 240; }\n')
    env=os.environ.copy();env.update(TMPDIR=str(root/'tmp'),XDG_CACHE_HOME=str(root/'cache'),
        OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    command=['/usr/bin/cc','-shared','-fPIC','-O0',str(source),'-o',str(library)]
    p=bounded_command(command,cwd=root,env=env,timeout=10)
    (record/'compiler.stdout.log').write_text(p.stdout);(record/'compiler.stderr.log').write_text(p.stderr)
    (record/'compiler.exit_code').write_text(str(p.returncode)+'\n')
    if p.returncode:raise RuntimeError('CACHE_LIBRARY_COMPILATION_FAILED')
    # Separate short Python loader; no scientific backend or mesh.
    code='import ctypes,sys; lib=ctypes.CDLL(sys.argv[1]); assert lib.sim240_probe_constant()==240; print("CACHE_LOAD_PASS")'
    q=bounded_command(['/usr/bin/python3','-B','-c',code,str(library)],cwd=root,env=env,timeout=10)
    (record/'loader.stdout.log').write_text(q.stdout);(record/'loader.stderr.log').write_text(q.stderr)
    (record/'loader.exit_code').write_text(str(q.returncode)+'\n')
    if q.returncode:raise RuntimeError('CACHE_LIBRARY_LOAD_FAILED')
    result={'status':'CACHE_LOAD_PASS','compiler_argv':command,'compiler_exit':p.returncode,
        'loader_exit':q.returncode,'source_sha256':sha(source),'library_sha256':sha(library)}
    checked_remove_probe(root,['constant.c','cache/constant.so'])
    return result

def capacity_probe(record):
    root=WORK/('volume_probe_capacity_'+uuid.uuid4().hex[:12]);root.mkdir(mode=0o700)
    fill=root/'fill.bin';total=0;error=None;deadline=time.monotonic()+60
    with fill.open('xb',buffering=0) as f:
        while total<513*1024**2:
            if time.monotonic()>deadline:raise TimeoutError('CAPACITY_PROBE_60_SECONDS_EXCEEDED')
            try:
                n=f.write(b'V'*min(1024**2,513*1024**2-total))
                if not n:raise RuntimeError('ZERO_PROGRESS_WRITE')
                total+=n
            except OSError as exc:error=exc.errno;break
    if error!=errno.ENOSPC or total>512*1024**2:raise RuntimeError('EXPECTED_CAPPED_VOLUME_ENOSPC_NOT_OBSERVED')
    # Keep the volume full while the separate persistent record captures exit.
    code=('import errno,json,sys\ntry:\n f=open(sys.argv[1],"xb",buffering=0); f.write(b"X"); f.close()\n'
          'except OSError as e:\n print(json.dumps({"errno":e.errno,"kind":"FILESYSTEM_PROBE_NOT_PDE"})); sys.exit(28 if e.errno==errno.ENOSPC else 9)\n'
          'sys.exit(8)\n')
    child=subprocess.run(['/usr/bin/python3','-B','-c',code,str(root/'expected_failed_write.bin')],
        capture_output=True,text=True,timeout=10)
    (record/'full_volume_child.stdout.log').write_text(child.stdout)
    (record/'full_volume_child.stderr.log').write_text(child.stderr)
    with (record/'full_volume_child.independent_exit_code').open('x') as f:
        f.write(str(child.returncode)+'\n');f.flush();os.fsync(f.fileno())
    if child.returncode!=28:raise RuntimeError('FULL_VOLUME_FAILURE_EXIT_NOT_CAPTURED')
    free=os.statvfs(WORK)
    result={'status':'CAPACITY_ENOSPC_PASS','successful_write_bytes':total,'errno':error,
        'fill_sha256':sha(fill),'available_bytes_when_full':free.f_bavail*free.f_frsize,
        'free_inodes_when_full':free.f_favail,'full_volume_child_exit':child.returncode,
        'record_disk_exit_written_while_full':True}
    save(record/'capacity_probe.json',result)
    files=['fill.bin']
    if (root/'expected_failed_write.bin').exists():files.append('expected_failed_write.bin')
    checked_remove_probe(root,files)
    return result

def archive_probes(base_contract):
    from common import expected_argv,expected_environment,validate
    from runner import synthetic
    from readback import check,check_archive
    results=[]
    for mode in ('success','failure'):
        c=json.loads(json.dumps(base_contract));c['run_id']='VOLUME_PROBE_'+mode+'_'+uuid.uuid4().hex[:12]
        c['work_dir']=str(WORK/c['run_id']);c['record_dir']=str(RECORD/c['run_id'])
        c['argv']=expected_argv(c);c['environment']=expected_environment(c);validate(c)
        m=synthetic(c,mode,limits=dict(wall_seconds=5,grace_seconds=.1,memory_bytes=512*1024**2,output_bytes=8*1024**2))
        r=Path(c['record_dir']);w=Path(c['work_dir'])
        assert m['kind']=='SYNTHETIC_PROCESS_NOT_PDE' and m['archive_status']=='ARCHIVE_COMPLETE'
        integrity=check_archive(r)
        if mode=='success':assert check(r/'archive',record=r)['status']=='DIAGNOSTIC_READBACK_PASS'
        else:assert m['independent_exit_code']==7 and (r/'archive/partial.bin').read_bytes()==b'partial-raw-fixture'
        # All these paths are newly created SYNTHETIC probe runs; delete only
        # hash-bound source files, preserving the persistent archive.
        from archive import strict_inventory
        assert strict_inventory(w)==m['work_files']
        if w.parent!=WORK or not w.name.startswith('VOLUME_PROBE_'):raise ValueError('SYNTHETIC_CLEANUP_PATH_REJECTED')
        for name in m['work_files']:(w/name).unlink()
        for d in sorted((d for d in w.rglob('*') if d.is_dir()),key=lambda d:len(d.parts),reverse=True):d.rmdir()
        w.rmdir()
        if mode=='success':assert check(r/'archive',record=r)['status']=='DIAGNOSTIC_READBACK_PASS'
        results.append({'mode':mode,'record_dir':str(r),'independent_exit_code':m['independent_exit_code'],
            'archive_integrity':integrity,'synthetic_source_removed_after_hash_verification':True})
    return results

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=['persistent','mounted'],required=True)
    args=parser.parse_args();c=packet()
    result={'phase':args.phase,'started_at_Asia_Shanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'kind':'FILESYSTEM_PROBE_NOT_PDE','probe_source_sha256':sha(Path(__file__)),
        'authorized_to_solve':False,'real_solver_called':False,'actual_run_id':None}
    if args.phase=='persistent':
        result['persistent']=persistent_probe();result['status']='PERSISTENT_PROBE_PASS'
    else:
        result['layout_before']=layout_check()
        if result['layout_before']['exit_code']!=0:
            result['status']='REFUSED_LAYOUT_NOT_READY';print(json.dumps(result,indent=2));return 2
        record=RECORD/('volume_probe_mounted_'+uuid.uuid4().hex[:12]);record.mkdir(mode=0o700)
        try:
            result['persistent']=persistent_probe()
            result['cache']=compiler_probe(record)
            result['capacity']=capacity_probe(record)
            result['archives']=archive_probes(c)
            result['layout_after']=layout_check()
            if result['layout_after']['exit_code']!=0:raise RuntimeError('FINAL_EMPTY_LAYOUT_CHECK_FAILED')
            result['status']='BOUNDED_VOLUME_PROBES_PASS_ONLY'
        except Exception as exc:
            result['status']='PROBE_FAILED';result['exception']=repr(exc)
            save(record/'probe_result.json',result);raise
        save(record/'probe_result.json',result)
    result['forbidden_backend_modules_loaded']=[k for k in sys.modules if k.split('.')[0] in {'petsc4py','dolfinx','dolfinx_mpc','ufl'}]
    assert not result['forbidden_backend_modules_loaded']
    print(json.dumps(result,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
