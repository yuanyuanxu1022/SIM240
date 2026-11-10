"""Read-only by default. Native execution needs a separate performance release."""
from pathlib import Path
import argparse
import csv
import json
import os
import resource
import shutil
import signal
import subprocess
import sys
import time

CASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(CASE/'analysis'))
from perf_contract import (need,sha,kv,load,save,now,verify,authorize,pristine,unchanged,
                           no_symlinks,PURPOSE)
from check_perf import Diagnostics,SAMPLE_HEADER,raw_hashes,check,SUFFICIENT


def resources(run,pid=None,initial=False):
    available=next(int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()
                   if line.startswith('MemAvailable:'))
    rss=0
    if pid is not None:
        try:
            rss=next(int(line.split()[1])*1024 for line in Path(f'/proc/{pid}/status').read_text().splitlines()
                     if line.startswith('VmRSS:'))
        except (FileNotFoundError,StopIteration):
            rss=0  # Exit race is also recorded by child.poll(); never a peak claim.
    size=0
    for path in Path(run).rglob('*'):
        need(not path.is_symlink(),'output symlink during run')
        if path.is_file():size+=path.stat().st_size
    return dict(RSS_bytes=rss,MemAvailable_bytes=available,output_bytes=size,
                disk_free_bytes=shutil.disk_usage(run).free)


def resource_guard(sample,initial=False):
    need(sample['RSS_bytes']<=8*1024**3,'RSS exceeds process envelope')
    need(sample['MemAvailable_bytes']>=12*1024**3,'available RAM below 12 GiB')
    need(sample['output_bytes']<=4*1024**3,'output above 4 GiB')
    need(sample['disk_free_bytes']>=(100 if initial else 8)*1024**3,'free disk below requirement')


def child_limits():
    resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))


def environment():
    need(not os.environ.get('LD_PRELOAD') and not os.environ.get('LD_LIBRARY_PATH'),
         'unbound loader override forbidden')
    env=dict(os.environ)
    env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
               NUMEXPR_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen')
    return env


def monitor(child,run,diagnostic,writer,cancelled,clock=time.monotonic,sleep=time.sleep,
            read_resources=resources,send_signal=os.killpg,start=None):
    """Injectable observer for software tests; fixed production budgets, no retry."""
    start=clock() if start is None else start
    deadline=start+1800.;next_sample=start
    samples=[];signals=[];reason=None;error=None
    try:
        while True:
            t=clock()
            if cancelled():reason='user_stop';break
            if child.poll() is not None:reason='unexpected_exit';break
            if t>=deadline:reason='wall_timeout';break
            if t<next_sample:
                sleep(min(next_sample-t,deadline-t));continue
            try:
                diagnostic.read_new(run/'diagnostics.csv')
                metrics=read_resources(run,child.pid)
                t=clock()
                if t>=deadline:reason='wall_timeout';break
                if child.poll() is not None:reason='unexpected_exit';break
                sample=dict(sample=len(samples),monotonic=t,alive=1,
                    last_complete_step=diagnostic.last,complete_bytes=diagnostic.complete_bytes,
                    complete_prefix_sha256=diagnostic.digest.hexdigest(),**metrics)
                writer.writerow(sample);samples.append(sample)
                resource_guard(metrics)
            except (ValueError,OSError,UnicodeError,OverflowError) as exc:
                reason='safety_or_resource_error';error=str(exc);break
            next_sample=t+1.
            if diagnostic.last>=2048:reason='target_observed';break
    finally:
        decision=clock()
        if child.poll() is None:
            signals.append(dict(signal='SIGTERM',monotonic=clock()))
            try:send_signal(child.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                signals.append(dict(signal='SIGKILL',monotonic=clock()))
                try:send_signal(child.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                child.wait()
        code=child.wait()
    return dict(process_start_monotonic=start,stop_decision_monotonic=decision,
        process_exit_monotonic=clock(),stop_reason=reason or 'controller_error',
        stop_error=error,signals_sent=signals,independent_process_exit_code=code,
        timed_out=reason=='wall_timeout',solver_wall_cap_seconds=1800,
        observed_target_step=2048,SIGTERM_grace_seconds=10),samples


def inspect(path,digest):
    data=verify(path,digest)
    pristine(data['prepared_benchmark_runs'])
    return data


def execute(path,digest,inspection):
    data=verify(path,digest);authorize(data)
    need(inspection==data,'inspection/release changed')
    pristine(data['prepared_benchmark_runs'])
    need(not (CASE/'performance_attempt.json').exists(),'attempt exists; no retry')
    env=environment()
    first=resources(Path(data['prepared_benchmark_runs'][0]['output_directory']))
    resource_guard(first,True)
    lock=CASE/'performance_execution.lock';no_symlinks(lock)
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    os.close(fd)  # Persistent consumed lock: never auto-unlink or resume after interruption.
    save(CASE/'performance_attempt.json',dict(release_path=str(Path(path).resolve()),
        release_sha256=digest,started_at=now(),purpose=PURPOSE,actual_benchmark_run_ids=[]))
    cancelled=[False]
    old_handlers={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
    def request_stop(signum,frame):cancelled[0]=True
    for s in old_handlers:signal.signal(s,request_stop)
    statuses=[]
    try:
        for record in data['prepared_benchmark_runs']:
            if cancelled[0]:break
            pristine([record]);run=Path(record['output_directory'])
            before=unchanged(data['inputs_sha256']);available=resources(run);resource_guard(available)
            # Re-check cancellation after potentially expensive provenance reads.
            if cancelled[0]:break
            diagnostic=Diagnostics(kv(record['run_config_path']))
            start_wall=now();start=time.monotonic()
            save(run/'performance_process_intent.json',dict(run_id=record['run_id'],
                release_sha256=digest,argv=[data['native_binary'],record['run_config_path']],
                recorded_at=start_wall,process_started_not_yet_confirmed=True))
            with (run/'run.log').open('x') as log,(run/'performance_observations.csv').open('x',buffering=1) as stream:
                writer=csv.DictWriter(stream,fieldnames=SAMPLE_HEADER);writer.writeheader()
                child=subprocess.Popen([data['native_binary'],record['run_config_path']],cwd=CASE,
                    stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True,preexec_fn=child_limits)
                process,samples=monitor(child,run,diagnostic,writer,lambda:cancelled[0],start=start)
            process['native_pid']=child.pid
            # Fresh parser verifies every complete final row, including termination flush.
            final=Diagnostics(kv(record['run_config_path']));final_error=None
            try:final.read_new(run/'diagnostics.csv')
            except (ValueError,OSError,UnicodeError,OverflowError) as exc:final_error=str(exc)
            after={p:sha(p) if Path(p).is_file() else None for p in data['inputs_sha256']}
            raw=raw_hashes(run)
            missing=[name for name in ['result.txt','execution_audit.txt','frame_index.csv'] if not (run/name).exists()]
            count=None
            if (run/'execution_audit.txt').exists():
                try:count=int(kv(run/'execution_audit.txt')['collide_and_stream_calls'])
                except (ValueError,KeyError):pass  # Checker will reject malformed raw evidence.
            receipt=dict(run_id=record['run_id'],release_sha256=digest,purpose=PURPOSE,
                formal_simulation_authorized=False,native_formal_simulation_flag_expected=True,
                started_at=start_wall,ended_at=now(),**process,inputs_before_sha256=before,
                inputs_after_sha256=after,raw_output_sha256=raw,resources_before=available,
                host=dict(hostname=os.uname().nodename,platform=list(os.uname()),python=sys.version,
                          executable=str(Path(sys.executable).resolve())),
                thread_environment={k:env[k] for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS',
                     'MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']},
                diagnostics_after_exit=final.summary(),diagnostic_error_after_exit=final_error,
                last_live_observed_step=int(samples[-1]['last_complete_step']) if samples else None,
                last_complete_step_lower_bound=final.last,exact_collide_and_stream_calls=count,
                missing_native_outputs=missing,unexpected_native_final_output=(run/'result.txt').exists(),
                cannot_resume=True,performance_data_cannot_be_reference=True)
            save(run/'performance_receipt.json',receipt)
            result=check(data,record,digest)
            save(run/'performance_acceptance.json',result)
            statuses.append(dict(run_id=record['run_id'],PERF_OUTCOME=result['PERF_OUTCOME']))
            if cancelled[0] or result['PERF_OUTCOME']!=SUFFICIENT:break
    finally:
        for s,handler in old_handlers.items():signal.signal(s,handler)
        actual={r['run_id'] for r in data['prepared_benchmark_runs']
                if (Path(r['output_directory'])/'performance_process_intent.json').exists()}
        save(CASE/'performance_batch_result.json',dict(purpose=PURPOSE,
            evaluated_runs=statuses,execution_intent_run_ids=sorted(actual),
            not_started_run_ids=[r['run_id'] for r in data['prepared_benchmark_runs'] if r['run_id'] not in actual],
            started_without_acceptance_run_ids=sorted(actual-{r['run_id'] for r in statuses}),
            formal_simulation_authorized=False,
            no_automatic_retry=True,no_next_stage=True))
    return statuses


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--release',required=True);parser.add_argument('--expected-sha256',required=True)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    data=inspect(args.release,args.expected_sha256)
    if args.execute:
        results=execute(args.release,args.expected_sha256,data)
        return 0 if len(results)==2 and all(r['PERF_OUTCOME']==SUFFICIENT for r in results) else 2
    print(json.dumps(dict(PREPARATION_BINDING_CHECK=True,solver_executed=False,
        kind=data['kind'],performance_time_stepping_authorized=data['performance_time_stepping_authorized'],
        formal_simulation_authorized=False,prepared_benchmark_run_ids=data['prepared_benchmark_run_ids'])))
    return 0


if __name__=='__main__':
    sys.exit(main())
