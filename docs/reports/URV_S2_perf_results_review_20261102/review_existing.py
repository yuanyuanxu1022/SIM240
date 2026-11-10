"""Offline review of completed PERF outputs. Writes only this report directory."""
from pathlib import Path
import csv
import hashlib
import io
import json
import math
import sys
import numpy as np

ROOT=Path('/home/dell/yuanyuanxu/SIM240')
CASE=ROOT/'CASE/unseen_v2_reference_S2_perf_v1'
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(CASE/'analysis'))
import perf_contract as c
import check_perf as frozen
EXPECTED='b675010adcc9e57627d3ff39c93d72394e16489e3713abe09851d5de31c5c7e1'


def save(name,value):c.save(OUT/name,value)


def independent(record,bound):
    run=Path(record['output_directory'])
    receipt=c.load(run/'performance_receipt.json')
    automatic=c.load(run/'performance_acceptance.json')
    assert receipt['inputs_before_sha256']==receipt['inputs_after_sha256']==bound['inputs_sha256']
    assert receipt['run_id']==record['run_id'] and receipt['release_sha256']==EXPECTED
    assert receipt['stop_reason']=='target_observed' and receipt['independent_process_exit_code']==-15
    assert receipt['timed_out'] is False and receipt['stop_error'] is None
    assert receipt['signals_sent'][0]['signal']=='SIGTERM' and len(receipt['signals_sent'])==1
    cfg=c.kv(run/'run_config.txt');eff=c.kv(run/'effective_config.txt')
    assert eff['run_id']==record['run_id'] and eff['mode']=='steady' and eff['formal_simulation']=='true'
    assert eff['direction']==('parallel' if cfg['direction']=='P' else 'perpendicular')
    assert int(eff['window_steps'])==10368 and int(eff['maximum_steps'])==602112
    pars=c.frozen_helpers()[1].exact_parameters(cfg)
    boundary=c.kv(run/'boundary_audit.txt')
    assert all(int(boundary[k])==490752 for k in ['candidate_links','valid_distance_links','installed_links'])
    assert int(boundary['material_1'])==2949120
    assert all(int(boundary[k])==0 for k in ['geometric_fallback_count','missing_fluid_neighbour_fallback_count','unresolved_link_count'])
    assert all(abs(float(boundary[k])-.5)<=1e-10 for k in ['q_min','q_max','installed_q_min','installed_q_max'])
    raw=(run/'diagnostics.csv').read_bytes();complete_end=raw.rfind(b'\n')+1
    complete=raw[:complete_end];tail=raw[complete_end:]
    reader=csv.DictReader(io.StringIO(complete.decode('ascii')))
    assert reader.fieldnames==frozen.HEADER
    rows=list(reader);arrays={k:np.array([float(row[k]) for row in rows]) for k in reader.fieldnames}
    count=len(rows);steps=arrays['step']
    assert np.array_equal(steps,np.arange(count)) and count==2066
    assert all(np.isfinite(a).all() for a in arrays.values()) and np.all(arrays['finite']==1)
    assert np.allclose(arrays['time_s'],steps*pars['dt'],rtol=1e-13,atol=1e-24)
    assert np.all(arrays['mass']>0) and np.all(arrays['corrected_mass']>0)
    assert math.isclose(arrays['corrected_mass'][0],1000*pars['nodes']*pars['dx']**3,rel_tol=1e-12)
    legacy=(arrays['mass']-arrays['mass'][0])/arrays['mass'][0]
    corrected=(arrays['corrected_mass']-arrays['corrected_mass'][0])/arrays['corrected_mass'][0]
    delta=(arrays['density_delta']-arrays['density_delta'][0])/(pars['nodes']+arrays['density_delta'][0])
    ledger=np.abs(corrected-delta)
    for expected,key in [(legacy,'mass_error'),(corrected,'corrected_mass_error'),
                         (delta,'delta_mass_error'),(ledger,'mass_ledger_agreement')]:
        assert np.allclose(expected,arrays[key],rtol=1e-10,atol=1e-16),key
    main=arrays['Jy' if cfg['direction']=='P' else 'Jx']
    assert np.allclose(main,arrays['J'],rtol=1e-13,atol=1e-30)
    assert all(np.all(arrays[k]==-1) for k in ['window_rel_std','window_rel_span','window_cross_abs_max'])
    limits=c.load(c.CHECKER/'common/acceptance_spec.json');L=limits['per_run']
    maxima=dict(corrected_mass=float(np.abs(corrected).max()),legacy_mass=float(np.abs(legacy).max()),
        ledger=float(ledger.max()),density=float(arrays['max_density_deviation'].max()),
        Mach=float(arrays['Mach'].max()))
    maxima['Re_H']=maxima['Mach']/math.sqrt(3)*pars['dx']/pars['dt']*(pars['h']+pars['d'])/pars['nu']
    assert maxima['corrected_mass']<L['compensated_mass_relative_strict']
    assert maxima['ledger']<=L['ledger_agreement_max']
    assert maxima['density']<=L['density_deviation_max'] and maxima['Mach']<L['Mach_strict']
    assert maxima['Re_H']<=limits['new_physics_guards']['Re_H_max']
    for k in ['Mach','max_density_deviation','mass_ledger_agreement']:assert np.all(arrays[k]>=0)
    with (run/'performance_observations.csv').open() as stream:
        observer=csv.DictReader(stream);assert observer.fieldnames==frozen.SAMPLE_HEADER;samples=list(observer)
    t=np.array([float(s['monotonic']) for s in samples]);seen=np.array([int(s['last_complete_step']) for s in samples])
    assert np.array_equal([int(s['sample']) for s in samples],np.arange(len(samples)))
    assert np.isfinite(t).all() and np.all(np.diff(t)>=1-1e-9) and np.all(np.diff(seen)>=0)
    assert t[0]>=receipt['process_start_monotonic'] and t[-1]<=receipt['stop_decision_monotonic']
    assert np.all([int(s['alive'])==1 for s in samples])
    assert seen[-1]>=2048 and np.all(seen[:-1]<2048)
    # Rebuild every observed byte-prefix fingerprint directly from raw complete lines.
    endpoints={0:(-1,hashlib.sha256(b'').hexdigest())};offset=0;digest=hashlib.sha256()
    for i,line in enumerate(complete.splitlines(keepends=True)):
        offset+=len(line);digest.update(line);endpoints[offset]=(i-1,digest.hexdigest())
    offsets=np.array([int(s['complete_bytes']) for s in samples]);assert np.all(np.diff(offsets)>=0)
    for s in samples:
        assert endpoints[int(s['complete_bytes'])]==(int(s['last_complete_step']),s['complete_prefix_sha256'])
    windows=[]
    for threshold in [256,1024]:
        i=int(np.flatnonzero(seen>=threshold)[0])
        j=int(np.flatnonzero((np.arange(len(seen))>i)&(seen>=seen[i]+512))[0])
        ds=int(seen[j]-seen[i]);dt=float(t[j]-t[i]);assert ds>=512 and dt>0
        windows.append(dict(threshold=threshold,start_sample=i,end_sample=j,start_step=int(seen[i]),
            end_step=int(seen[j]),start_monotonic=float(t[i]),end_monotonic=float(t[j]),
            delta_steps=ds,delta_seconds=dt,seconds_per_step=dt/ds,steps_per_second=ds/dt))
    assert windows==automatic['throughput_intervals']
    rss=np.array([int(s['RSS_bytes']) for s in samples]);mem=np.array([int(s['MemAvailable_bytes']) for s in samples])
    output=np.array([int(s['output_bytes']) for s in samples]);disk=np.array([int(s['disk_free_bytes']) for s in samples])
    assert np.all(rss>=0) and rss.max()<=8*1024**3 and mem.min()>=12*1024**3
    assert output.max()<=4*1024**3 and disk.min()>=8*1024**3
    assert receipt['resources_before']['MemAvailable_bytes']>=12*1024**3
    assert receipt['resources_before']['disk_free_bytes']>=8*1024**3
    stop_seconds=receipt['stop_decision_monotonic']-receipt['process_start_monotonic'];assert 0<stop_seconds<1800
    assert receipt['signals_sent'][0]['monotonic']>=receipt['stop_decision_monotonic']
    assert receipt['process_exit_monotonic']>=receipt['signals_sent'][0]['monotonic']
    assert not (run/'result.txt').exists() and not (run/'execution_audit.txt').exists()
    assert receipt['exact_collide_and_stream_calls'] is None
    frame_rows=list(csv.DictReader((run/'frame_index.csv').open()))
    assert [int(v['step']) for v in frame_rows]==[0,139,277,692,1383]
    assert not any('final' in v['reason'] for v in frame_rows)
    for expected,key in [(len(tail),'incomplete_tail_bytes'),(complete_end,'complete_bytes')]:
        assert receipt['diagnostics_after_exit'][key]==expected
    assert receipt['diagnostics_after_exit']['incomplete_tail_sha256']==hashlib.sha256(tail).hexdigest()
    slow=max(w['seconds_per_step'] for w in windows)
    replay=frozen.check(bound,record,EXPECTED)
    assert replay==automatic and replay['PERF_OUTCOME']==frozen.SUFFICIENT
    save(record['run_id']+'_checker_replay.json',replay)
    return dict(run_id=record['run_id'],direction=cfg['direction'],PERF_OUTCOME='PERF_EVIDENCE_SUFFICIENT',
        independent_raw_review_pass=True,automatic_checker_reproduced_exactly=True,
        started_at=receipt['started_at'],ended_at=receipt['ended_at'],stop_decision_seconds=stop_seconds,
        native_process_elapsed_seconds=receipt['process_exit_monotonic']-receipt['process_start_monotonic'],
        stop_reason=receipt['stop_reason'],native_exit_code=receipt['independent_process_exit_code'],
        timed_out=receipt['timed_out'],last_complete_step=count-1,complete_rows=count,
        exact_collide_and_stream_calls=None,incomplete_tail_bytes=len(tail),
        throughput_intervals=windows,safety_maxima=maxima,observed_RSS_peak_bytes=int(rss.max()),
        observed_RSS_peak_GiB=float(rss.max()/1024**3),minimum_available_RAM_GiB=float(mem.min()/1024**3),
        minimum_free_disk_GiB=float(disk.min()/1024**3),maximum_observed_output_bytes=int(output.max()),
        total_run_directory_files_bytes=sum(p.stat().st_size for p in run.rglob('*') if p.is_file()),
        observation_samples=len(samples),sample_interval_min_seconds=float(np.diff(t).min()),
        sample_interval_max_seconds=float(np.diff(t).max()),max_positive_observed_step_jump=int(np.diff(seen).max()),
        conditional_full_cap_hours=slow*602112/3600,conditional_12h_steps=43200/slow,
        full_window_cost_observed=False,full_window_steps=10368,frames_saved=len(frame_rows),
        formal_geometry_not_upgraded=True,**c.SCIENCE)


def main():
    for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        p=OUT/('before_'+name);assert not p.exists();p.write_bytes((ROOT/'docs/reports'/name).read_bytes())
    old=ROOT/'docs/reports/URV_S2_perf_launch_release_20261102'
    protected=c.load(old/'protected_inputs_before.json')
    for tree in [CASE,old,ROOT/'docs/reports/URV_S2_perf_startup_check_20261102_205558']:
        for p in tree.rglob('*'):
            if p.is_file():protected[str(p.resolve())]=c.sha(p)
    c.unchanged(protected);save('protected_inputs_before.json',protected)
    release=CASE/'evidence/S2_perf_launch_release_v1_20261102_01.json'
    bound=c.verify(release,EXPECTED);c.authorize(bound)
    batch=c.load(CASE/'performance_batch_result.json');assert batch['not_started_run_ids']==[]
    assert batch['started_without_acceptance_run_ids']==[]
    save('raw_evidence_sha256.json',{str(p.resolve()):c.sha(p) for p in CASE.rglob('*') if p.is_file()})
    reviews=[independent(r,bound) for r in bound['prepared_benchmark_runs']]
    assert [r['run_id'] for r in reviews]==[r['run_id'] for r in batch['evaluated_runs']]
    assert [r['PERF_OUTCOME'] for r in reviews]==[r['PERF_OUTCOME'] for r in batch['evaluated_runs']]
    first=c.load(Path(bound['prepared_benchmark_runs'][0]['output_directory'])/'performance_receipt.json')
    second=c.load(Path(bound['prepared_benchmark_runs'][1]['output_directory'])/'performance_receipt.json')
    assert second['process_start_monotonic']>first['process_exit_monotonic']
    result=dict(reviewed_at=c.now(),protocol_id='S2-MIP-v1-PERF',release_sha256=EXPECTED,
        inputs_verified=len(bound['inputs_sha256']),both_directions_independently_sufficient=True,
        sequence_P_then_T_verified=True,performance_batch_complete=True,actual_solver_calls_this_review=0,
        actual_VTK_reads_this_review=0,builds_this_review=0,retries=0,formal_started=False,
        direction_reviews=reviews,protected_files=len(protected),**c.SCIENCE)
    save('independent_review.json',result)
    with (OUT/'performance_summary.csv').open('x') as f:
        fields=['direction','stop_decision_seconds','native_exit_code','last_complete_step','incomplete_tail_bytes',
            'observed_RSS_peak_GiB','conditional_full_cap_hours','conditional_12h_steps']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        writer.writerows({k:r[k] for k in fields} for r in reviews)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
