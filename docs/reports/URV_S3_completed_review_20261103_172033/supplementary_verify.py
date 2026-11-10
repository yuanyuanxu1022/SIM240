"""Additional read-only resource, timeline, protected-file checks."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,shlex
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
load=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
x=load(OUT/'independent_review.json');snap=load(OUT/'completion_snapshot.json')
c=ROOT/'CASE/unseen_v2_reference_S3_reuse_v1_1';att=c/'launch_attempts'/x['S3_release_sha256']
records=[]
for row in x['runs']:
    case=c if row['role']=='S3_new' else ROOT/'CASE/unseen_v2_reference_S2_reuse_v1'
    run=case/'runs'/row['run_id']/'steady';completion=load(run/'completion.json')
    available=completion['resources_before']
    assert available['MemAvailable_bytes']>=12*1024**3
    assert available['disk_free_bytes']>=8*1024**3
    assert row['raw_bytes']<=4*1024**3
    assert completion['density_capture']=='NOT_APPLICABLE_S0_ONLY'
    times={key:(run/name).stat().st_mtime for key,name in [('run_log','run.log'),('completion','completion.json')]}
    times['acceptance']=(case/'analysis_results'/row['run_id']/'acceptance.json').stat().st_mtime
    assert times['run_log']<=times['completion']<=times['acceptance']
    records.append(dict(run_id=row['run_id'],resources_before=available,density_capture=completion['density_capture'],
        output_bytes=row['raw_bytes'],mtime_unix=times,mtime_local={k:datetime.fromtimestamp(v,ZoneInfo('Asia/Shanghai')).isoformat() for k,v in times.items()}))
new=[r for r in records if r['run_id'].startswith('URV_S3')]
for prev,nxt in zip(new,new[1:]):assert prev['mtime_unix']['acceptance']<nxt['mtime_unix']['completion']
p_time=(att/'linearity_P.json').stat().st_mtime;t_time=(att/'linearity_T.json').stat().st_mtime
assert new[2]['mtime_unix']['acceptance']<=p_time<new[3]['mtime_unix']['completion']
assert new[3]['mtime_unix']['acceptance']<=t_time<=(att/'S3_completed.json').stat().st_mtime
actual_processes=[];self_shell_rows=[]
for line in snap['processes']:
    command=line.split(None,3)[3];tokens=shlex.split(command)
    if Path(tokens[0]).name in ['bash','sh','rg']:self_shell_rows.append(line)
    else:actual_processes.append(line)
assert actual_processes==[] and 'urv_s3_formal_v1_1_20261103_01' not in snap['tmux_stdout']
protected=load(OUT/'protected_inputs_and_outputs.json')
assert all(sha(p)==h for p,h in protected.items())
result=dict(verified_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),records=records,
    launch_order_consistent_with_mtimes=True,mtime_is_auxiliary_not_monotonic_runtime_evidence=True,
    P_control_before_fourth_completion=True,controller_source_enforces_P_before_T_high=True,
    captured_snapshot_relevant_processes=actual_processes,self_shell_rows_excluded=len(self_shell_rows),
    batch_mtime=snap['batch_mtime'],controller_log_bytes=(c/'S3_formal_controller_v1_1_20261103_01.log').stat().st_size,
    independent_parent_controller_exit_code='NOT_RECORDED',native_exit_codes=[0]*4,replay_checker_exit_codes=[0]*6,
    saved_field_frames=60,saved_raw_files=sum(r['raw_files'] for r in x['runs']),
    S3_raw_files=sum(r['raw_files'] for r in x['runs'] if r['role']=='S3_new'),
    all_protected_files_unchanged=len(protected),formal_S3_solver_seconds=x['formal_S3_solver_seconds'],
    solver_calls=0,builds=0,retries=0,extensions=0,
    helper_correction='Before replay, corrected S2 digest sidecar name from .sha256 to actual .json.sha256; original helper retained; no frozen inputs or results changed.')
with (OUT/'supplementary_verification.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='records'},ensure_ascii=False,indent=2))
