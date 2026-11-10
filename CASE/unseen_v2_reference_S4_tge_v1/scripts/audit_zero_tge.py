"""One candidate, zero steps: 3 native modes + one read, only after new authority."""
from pathlib import Path
import argparse,json,os,resource,signal,subprocess,sys,time
CASE=Path(__file__).resolve().parents[1]
CHECKER=CASE.parent/'unseen_v2_reference_checker_S4_tge_v1'
sys.path.insert(0,str(CHECKER/'analysis'))
from tge_stage import (AUDIT_ID,CASE_ID,ELF_SHA,MODES,ZERO_RESOURCES,need,sha,kv,load,
    verify_seal,require_pristine,validate_zero_authority,unchanged,static_summary)
from check_zero_tge import validate_completed_zero
from zero_evidence_s4 import validate_zero_outputs,validate_initial_readback

def save(path,value):
    need(not path.exists(),'refusing receipt overwrite');path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')

def resources(initial):
    mem=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
    import shutil
    free=shutil.disk_usage(CASE).free
    need(mem>=12*1024**3,'available memory below adopted 12GiB zero limit')
    need(free>=(100 if initial else 8)*1024**3,'disk below adopted zero limit')
    return dict(MemAvailable_bytes=mem,disk_free_bytes=free)

def limits():
    resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0))

def stop(child):
    if child.poll() is None:
        os.killpg(child.pid,signal.SIGTERM)
        try:child.wait(timeout=10)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()

def bounded_process(command,log,env,output):
    started=time.monotonic();reason=None
    with log.open('x') as stream:
        child=subprocess.Popen(command,cwd=CASE,stdout=stream,stderr=subprocess.STDOUT,
            env=env,start_new_session=True,preexec_fn=limits)
        try:
            while child.poll() is None:
                remaining=300-(time.monotonic()-started)
                if remaining<=0:reason='wall_timeout';break
                try:child.wait(timeout=min(5.,remaining))
                except subprocess.TimeoutExpired:pass
                size=sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
                if size>4*1024**3:reason='output_budget_exceeded';break
                import shutil
                if shutil.disk_usage(CASE).free<8*1024**3:reason='free_disk_below_limit';break
        finally:stop(child)
        code=child.wait()
    return dict(independent_process_exit_code=code,timed_out=reason=='wall_timeout',
        resource_stop_reason=reason,elapsed_seconds=time.monotonic()-started,solver_wall_cap_seconds=300)

def execute(path,digest,bound):
    validate_zero_authority(bound,path)
    current=verify_seal(path,digest);need(current==bound,'inspection/release mismatch')
    require_pristine(bound);resources(True)
    attempt=CASE/'audit_attempts'/digest;attempt.mkdir(parents=True,exist_ok=False)
    folder=CASE/'audits'/AUDIT_ID
    need(not (folder/'verification.json').exists(),'zero receipt exists; no retry')
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
        QT_QPA_PLATFORM='offscreen',PYTHONDONTWRITEBYTECODE='1')
    env.pop('LD_LIBRARY_PATH',None);env.pop('LD_PRELOAD',None)
    records=[]
    for rec in bound['zero_prepared_runs']:
        need(sha(path)==digest,'release changed');validate_zero_authority(bound,path);unchanged(bound);available=resources(False)
        need(rec['mode'] in MODES and kv(rec['run_config_path'])['mode']==rec['mode'],'zero forbids steady')
        binary=bound['provenance']['native_binary'];need(sha(binary)==ELF_SHA,'native binary changed')
        run=Path(rec['output_directory'])
        result=bounded_process([binary,rec['run_config_path']],run/'run.log',env,run)
        (run/'exit_code.txt').write_text(str(result['independent_process_exit_code'])+'\n')
        save(run/'process_receipt.json',result)
        need(result['independent_process_exit_code']==0 and not result['timed_out'] and result['resource_stop_reason'] is None,
             'zero failed; no retry/next call')
        geo=validate_zero_outputs(rec)
        receipt=dict(run_id=rec['run_id'],planned_case_id=CASE_ID,mode=rec['mode'],output=str(run),
            native_exit_code=0,collide_and_stream_calls=0,geometry=geo,resources_before=available,
            elapsed_seconds=result['elapsed_seconds'])
        if rec['mode']=='initialize':
            report=folder/('field_readback_'+CASE_ID+'.json');log=folder/('field_reader_'+CASE_ID+'.log')
            reader=Path(bound['reader_path'])
            need(bound['inputs_sha256'].get(str(reader))==sha(reader),'reader unbound')
            cmd=['/usr/bin/pvpython','--force-offscreen-rendering','-B',str(reader),'--run',str(run),'--out',str(report)]
            proc=bounded_process(cmd,log,env,folder)
            save(report.with_suffix('.process.json'),dict(independent_exit_code=proc['independent_process_exit_code'],
                timed_out=proc['timed_out'],resource_stop_reason=proc['resource_stop_reason'],elapsed_seconds=proc['elapsed_seconds']))
            need(proc['independent_process_exit_code']==0 and not proc['timed_out'] and proc['resource_stop_reason'] is None,
                 'field reader failed; stop')
            validate_initial_readback(rec,report,folder)
            receipt.update(field_readback=str(report),field_readback_sha256=sha(report))
        need(sha(path)==digest,'release changed');unchanged(bound);records.append(receipt);save(folder/'progress'/f'{len(records):02d}.json',receipt)
        print(json.dumps(dict(mode=rec['mode'],native_exit=0,actual_time_steps=0)),flush=True)
    raw={str(p):sha(p) for p in folder.rglob('*') if p.is_file()}
    manifest=folder/'audit_files_sha256.json';save(manifest,raw)
    save(folder/'verification.json',dict(audit_id=AUDIT_ID,ZERO_STEP_AUDIT_PASS=True,binary_sha256=ELF_SHA,
        native_describe=1,native_precheck=1,native_initialize=1,initialized_frames_read=1,
        actual_time_steps=0,steady_mode_invocations=0,records=records,
        raw_manifest_path=str(manifest),raw_manifest_sha256=sha(manifest),preparation_A_sha256=bound['preparation_A_sha256'],
        audit_release_path=str(path),audit_release_sha256=digest,density_capture='NOT_APPLICABLE_S0_ONLY',
        formal_simulation_started=False,NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,
        reference_qualified=False,next_stage_started=False))
    validate_completed_zero(bound,path)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--release',type=Path,required=True);ap.add_argument('--release-sha256',required=True)
    ap.add_argument('--execute',action='store_true');args=ap.parse_args()
    try:
        path=args.release.resolve();bound=verify_seal(path,args.release_sha256);require_pristine(bound)
        if args.execute:execute(path,args.release_sha256,bound)
        else:print(json.dumps(static_summary(bound),indent=2))
        code=0
    except Exception as e:print(type(e).__name__+': '+str(e),file=sys.stderr);code=2
    raise SystemExit(code)
