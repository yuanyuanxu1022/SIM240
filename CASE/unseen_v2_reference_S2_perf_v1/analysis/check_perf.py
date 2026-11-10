"""Independent partial-trajectory/resource checker. Never imports a controller."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import sys
from perf_contract import (CASE, CHECKER, SCIENCE, need, sha, kv, load, save,
                           verify, authorize, frozen_helpers)

HEADER = ('step,J,rho,Mach,mass,time_s,mass_error,max_density_deviation,Jx,Jy,Jz,'
          'Q_section1,Q_section2,section_relative_difference,pressure_min,pressure_max,'
          'window_rel_std,window_rel_span,window_cross_abs_max,finite,corrected_mass,'
          'corrected_mass_error,delta_mass_error,mass_ledger_agreement,density_delta').split(',')
SAMPLE_HEADER = ['sample','monotonic','alive','last_complete_step','complete_bytes',
                 'complete_prefix_sha256','RSS_bytes','MemAvailable_bytes',
                 'output_bytes','disk_free_bytes']
LIMITS = load(CHECKER/'common/acceptance_spec.json')
SUFFICIENT = 'PERF_EVIDENCE_SUFFICIENT'
INSUFFICIENT = 'PERF_EVIDENCE_INSUFFICIENT'
ABORTED = 'PERF_ABORTED_UNEXPECTED'
EXCLUDED = {'performance_receipt.json','performance_acceptance.json'}


def close(a,b,rtol=1e-10,atol=1e-16):
    return abs(a-b)<=atol+rtol*abs(b)


class Diagnostics:
    """Incremental complete-line parsing, all-row guards, no stream modification."""
    def __init__(self,config):
        self.config=config
        self.p=frozen_helpers()[1].exact_parameters(config)
        self.offset=0; self.complete_bytes=0; self.tail=b''; self.header=False
        self.last=-1; self.first=None; self.digest=hashlib.sha256(); self.endpoints={}
        self.maxima=dict(corrected_mass=0.,legacy_mass=0.,ledger=0.,density=0.,Mach=0.,Re_H=0.)

    def row(self,line):
        fields=next(csv.reader([line.decode('ascii')]))
        need(len(fields)==len(HEADER),'diagnostic schema width')
        a=dict(zip(HEADER,map(float,fields)))
        need(all(math.isfinite(v) for v in a.values()),'nonfinite diagnostics')
        need(a['step']==self.last+1,'missing/reordered/noninteger diagnostic step')
        need(a['finite']==1,'nonfinite native measurement flag')
        need(a['step']<=self.p['cap'],'native maximum step exceeded')
        need(close(a['time_s'],a['step']*self.p['dt'],1e-13,1e-24),'time units mismatch')
        for k in ['Mach','max_density_deviation','mass_ledger_agreement']:
            need(a[k]>=0,'negative magnitude '+k)
        need(a['mass']>0 and a['corrected_mass']>0,'nonpositive mass')
        if self.first is None:
            need(close(a['corrected_mass'],1000*self.p['nodes']*self.p['dx']**3,1e-12,0),
                 'initial mass units')
            self.first=a
        b=self.first
        legacy=(a['mass']-b['mass'])/b['mass']
        corrected=(a['corrected_mass']-b['corrected_mass'])/b['corrected_mass']
        delta=(a['density_delta']-b['density_delta'])/(self.p['nodes']+b['density_delta'])
        ledger=abs(corrected-delta)
        for value,key in [(legacy,'mass_error'),(corrected,'corrected_mass_error'),
                          (delta,'delta_mass_error'),(ledger,'mass_ledger_agreement')]:
            need(close(value,a[key]),'independent mass recomputation '+key)
        main=a['Jy'] if self.config['direction']=='P' else a['Jx']
        need(close(main,a['J'],1e-13,1e-30),'directional flux mismatch')
        if a['step']<self.p['window']-1:
            need(all(a[k]==-1 for k in ['window_rel_std','window_rel_span','window_cross_abs_max']),
                 'premature window metrics')
        L=LIMITS['per_run']
        Re=a['Mach']/math.sqrt(3)*self.p['dx']/self.p['dt']*(self.p['h']+self.p['d'])/self.p['nu']
        need(abs(corrected)<L['compensated_mass_relative_strict'],'corrected mass safety guard')
        need(ledger<=L['ledger_agreement_max'],'mass ledger safety guard')
        need(a['max_density_deviation']<=L['density_deviation_max'],'density safety guard')
        need(a['Mach']<L['Mach_strict'],'Mach safety guard')
        need(Re<=LIMITS['new_physics_guards']['Re_H_max'],'Reynolds safety guard')
        for key,value in [('corrected_mass',abs(corrected)),('legacy_mass',abs(legacy)),
                          ('ledger',ledger),('density',a['max_density_deviation']),('Mach',a['Mach']),('Re_H',Re)]:
            self.maxima[key]=max(self.maxima[key],value)
        self.last=int(a['step'])

    def feed(self,data):
        self.offset+=len(data)
        data=self.tail+data
        chunks=data.split(b'\n'); self.tail=chunks.pop()
        for line in chunks:
            if not self.header:
                need(line.decode('ascii').split(',')==HEADER,'diagnostic header mismatch')
                self.header=True
            else:
                self.row(line)
            self.digest.update(line+b'\n')
            self.complete_bytes+=len(line)+1
            self.endpoints[self.complete_bytes]=(self.last,self.digest.hexdigest())

    def read_new(self,path):
        path=Path(path)
        if not path.exists():
            need(self.offset==0,'diagnostic file disappeared')
            return
        need(path.stat().st_size>=self.offset,'diagnostic file truncated')
        with path.open('rb') as stream:
            stream.seek(self.offset)
            self.feed(stream.read())

    def summary(self):
        return dict(last_complete_step=self.last,complete_rows=self.last+1,
            complete_bytes=self.complete_bytes,total_bytes_read=self.offset,
            incomplete_tail_bytes=len(self.tail),incomplete_tail_sha256=hashlib.sha256(self.tail).hexdigest(),
            incomplete_tail_start_offset=self.complete_bytes,complete_prefix_sha256=self.digest.hexdigest(),
            safety_maxima=self.maxima,exact_collide_and_stream_calls=None,
            step_is_only_lower_bound=True)


def intervals(samples):
    windows=[]
    for threshold in (256,1024):
        start=next((s for s in samples if int(s['last_complete_step'])>=threshold),None)
        end=next((s for s in samples if start and float(s['monotonic'])>float(start['monotonic']) and
                  int(s['last_complete_step'])>=int(start['last_complete_step'])+512),None)
        if start is None or end is None:
            return None
        dt=float(end['monotonic'])-float(start['monotonic'])
        ds=int(end['last_complete_step'])-int(start['last_complete_step'])
        need(math.isfinite(dt) and dt>0 and ds>=512,'invalid throughput endpoints')
        windows.append(dict(threshold=threshold,start_sample=int(start['sample']),end_sample=int(end['sample']),
            start_step=int(start['last_complete_step']),end_step=int(end['last_complete_step']),
            start_monotonic=float(start['monotonic']),end_monotonic=float(end['monotonic']),
            delta_steps=ds,delta_seconds=dt,seconds_per_step=dt/ds,steps_per_second=ds/dt))
    return windows


def validate_samples(samples,diag,receipt):
    prior=None
    for i,s in enumerate(samples):
        need(list(s)==SAMPLE_HEADER,'observation schema mismatch')
        need(int(s['sample'])==i,'observation ordering')
        t=float(s['monotonic'])
        need(math.isfinite(t) and receipt['process_start_monotonic']<=t<=receipt['stop_decision_monotonic'],
             'observation time outside live interval')
        need(prior is None or t-prior>=1-1e-9,'observation faster than 1 Hz or time reversed')
        prior=t
        step=int(s['last_complete_step']); offset=int(s['complete_bytes'])
        expected=diag.endpoints.get(offset,(-1,hashlib.sha256(b'').hexdigest()) if offset==0 else None)
        need(expected==(step,s['complete_prefix_sha256']),'observation not supported by raw complete prefix')
        need(int(s['alive'])==1,'post-exit samples cannot supply live throughput')
        for key in ['RSS_bytes','MemAvailable_bytes','output_bytes','disk_free_bytes']:
            need(int(s[key])>=0,'invalid resource observation')
        need(int(s['RSS_bytes'])<=8*1024**3 and int(s['MemAvailable_bytes'])>=12*1024**3 and
             int(s['output_bytes'])<=4*1024**3 and int(s['disk_free_bytes'])>=8*1024**3,
             'resource bound violated')
    # Last samples cannot reverse progress; prefix digest checks alone would permit it.
    need(all(int(a['complete_bytes'])<=int(b['complete_bytes']) and
             int(a['last_complete_step'])<=int(b['last_complete_step']) for a,b in zip(samples,samples[1:])),
         'observed progress reversed')


def outcome(receipt,samples,diag):
    reasons=[]; win=None
    try:
        need(receipt['inputs_before_sha256']==receipt['inputs_after_sha256'],'source drift')
        need(receipt['stop_reason'] in ('target_observed','wall_timeout'),'unexpected stop reason')
        need(receipt['independent_process_exit_code'] in (-15,-9),'unexpected native exit; explicit review required')
        need(not receipt['unexpected_native_final_output'],'unexpected complete native output')
        need(receipt['signals_sent'] and receipt['signals_sent'][0]['signal']=='SIGTERM','missing planned SIGTERM')
        need(receipt['solver_wall_cap_seconds']==1800 and receipt['observed_target_step']==2048 and
             receipt['SIGTERM_grace_seconds']==10,'stop budget mismatch')
        signals=receipt['signals_sent'];decision=receipt['stop_decision_monotonic']
        need(signals[0]['monotonic']>=decision,'signal before stop decision')
        need(len(signals) in (1,2),'unexpected signal sequence')
        if len(signals)==2:
            need(signals[1]['signal']=='SIGKILL' and
                 signals[1]['monotonic']-signals[0]['monotonic']>=10 and
                 receipt['independent_process_exit_code']==-9,'invalid TERM/KILL grace evidence')
        else:
            need(receipt['independent_process_exit_code']==-15,'SIGKILL exit without recorded SIGKILL')
        need(receipt['process_exit_monotonic']>=signals[-1]['monotonic'],'exit before last signal')
        need(receipt['timed_out']==(receipt['stop_reason']=='wall_timeout'),'timeout flag erased')
        duration=receipt['stop_decision_monotonic']-receipt['process_start_monotonic']
        need(math.isfinite(duration) and duration>=0,'invalid process timing')
        if receipt['stop_reason']=='target_observed':
            need(samples and int(samples[-1]['last_complete_step'])>=2048,'target stop unsupported')
            need(not any(int(s['last_complete_step'])>=2048 for s in samples[:-1]),'target stop was delayed')
            need(duration<1800,'wall deadline preceded target')
        else:
            need(duration>=1800,'wall stop before deadline')
            need(not any(int(s['last_complete_step'])>=2048 for s in samples),'target preceded wall stop')
        validate_samples(samples,diag,receipt)
        win=intervals(samples)
    except (ValueError,KeyError,TypeError) as exc:
        reasons.append(str(exc))
    if reasons:
        result=ABORTED
    elif win is None:
        result=INSUFFICIENT;reasons=['required two observed throughput intervals unavailable']
    else:
        result=SUFFICIENT
    return dict(PERF_OUTCOME=result,reasons=reasons,throughput_intervals=win,
        intervals_overlap=bool(win and max(win[0]['start_monotonic'],win[1]['start_monotonic'])<
                               min(win[0]['end_monotonic'],win[1]['end_monotonic'])),
        slow_interval_full_602112_steps_seconds=(max(w['seconds_per_step'] for w in win)*602112 if win else None),
        observed_RSS_peak_bytes=max((int(s['RSS_bytes']) for s in samples),default=None),
        exact_peak_RSS_known=False,full_window_cost_observed=False,completion_within_12h_guaranteed=False,
        timestamp_basis='external complete-record observation; buffering and sampling uncertainty',
        next_direction_allowed=result==SUFFICIENT,**SCIENCE)


def raw_hashes(run):
    hashes={}
    for p in sorted(Path(run).rglob('*')):
        need(not p.is_symlink(),'output symlink refused')
        if p.is_file() and p.relative_to(run).as_posix() not in EXCLUDED:
            hashes[p.relative_to(run).as_posix()]=sha(p)
    return hashes


def check(data,record,release_sha):
    run=Path(record['output_directory']);receipt=load(run/'performance_receipt.json')
    need(receipt['release_sha256']==release_sha and receipt['run_id']==record['run_id'],'receipt identity')
    need(receipt['purpose']=='S2_PERFORMANCE_NOT_REFERENCE','performance receipt purpose')
    need(receipt['inputs_before_sha256']==data['inputs_sha256'],'input snapshot not release closure')
    need(receipt.get('formal_simulation_authorized') is False,'parent scientific authority must stay closed')
    need(raw_hashes(run)==receipt['raw_output_sha256'],'raw output drift/unbound output')
    diagnostic=Diagnostics(kv(record['run_config_path']));error=None
    try:
        diagnostic.read_new(run/'diagnostics.csv')
    except (ValueError,UnicodeError,OverflowError) as exc:
        error=str(exc)
    with (run/'performance_observations.csv').open() as stream:
        samples=list(csv.DictReader(stream))
    result=outcome(receipt,samples,diagnostic)
    if error:
        result.update(PERF_OUTCOME=ABORTED,reasons=[error,*result['reasons']],next_direction_allowed=False)
    result.update(run_id=record['run_id'],release_sha256=release_sha,
                  receipt_sha256=sha(run/'performance_receipt.json'),diagnostics=diagnostic.summary())
    # A precheck/native flag, when present, must be the original steady-mode flag.
    if (run/'effective_config.txt').exists():
        native=kv(run/'effective_config.txt')
        need(native.get('formal_simulation')=='true','native steady flag changed')
    required=['result.txt','execution_audit.txt','frame_index.csv']
    need(receipt['missing_native_outputs']==[n for n in required if not (run/n).exists()],
         'missing native outputs misreported')
    need(receipt['unexpected_native_final_output']==(run/'result.txt').exists(),'native final output erased')
    count=None
    if (run/'execution_audit.txt').exists():
        count=int(kv(run/'execution_audit.txt')['collide_and_stream_calls'])
        need(count>=diagnostic.last,'native call count below saved complete step')
    need(receipt['exact_collide_and_stream_calls']==count,'native call count fabricated or erased')
    result['exact_collide_and_stream_calls']=count
    # Parent summaries are evidence to verify, not results to trust.
    need(receipt['diagnostics_after_exit']==diagnostic.summary() or error is not None,
         'parent diagnostic summary differs from raw replay')
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--release',required=True);parser.add_argument('--expected-sha256',required=True)
    parser.add_argument('--run-id',required=True)
    args=parser.parse_args()
    data=verify(args.release,args.expected_sha256);authorize(data)
    record=next((r for r in data['prepared_benchmark_runs'] if r['run_id']==args.run_id),None)
    need(record is not None,'unapproved performance run')
    result=check(data,record,args.expected_sha256)
    save(Path(record['output_directory'])/'performance_acceptance.json',result)
    print(json.dumps(result,allow_nan=False))
    return 0 if result['PERF_OUTCOME']==SUFFICIENT else 2


if __name__=='__main__':
    sys.exit(main())
