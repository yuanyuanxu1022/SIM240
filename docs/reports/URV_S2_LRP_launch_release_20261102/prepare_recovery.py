"""S2-LRP-v1 preparation only. Never call an execution entry or launch tmux."""
from pathlib import Path
import contextlib,copy,datetime,hashlib,importlib.util,io,json,os,re,shlex,subprocess,sys
from unittest.mock import patch
from zoneinfo import ZoneInfo
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_S2_reuse_v1';PERF=ROOT/'CASE/unseen_v2_reference_S2_perf_v1'
LRP=ROOT/'docs/reports/URV_S2_log_recovery_protocol_20261102'
OLD=CASE/'evidence/S2_formal_launch_release_reuse_v1_20261102_01.json'
NEW=CASE/'evidence/S2_formal_launch_release_LRP_v1_20261102_02.json'
SESSION='urv_s2_formal_lrp_v1_20261102_02'
LOG=CASE/'evidence/S2_formal_controller_LRP_v1_20261102_02.log'
CHANGED=PERF/'evidence/S2_perf_controller_v1_20261102_01.log'
OLD_SHA='2c0ed4c3c9d05178da160c2c2772ea8cee4ea03808ce7d765a19e3e3a86d1ad0'
CURRENT_LOG_SHA='ca3607bfc8f2c7aaeb99997253e85485f1633f74983f85aa087c96da70d8799c'
load=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(ok,msg):
 if not ok:raise ValueError(msg)
def save(p,d):
 with Path(p).open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def now():return datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
def diff(entries):return [dict(path=p,expected=h,current=sha(p) if Path(p).is_file() else None) for p,h in entries.items() if not Path(p).is_file() or sha(p)!=h]

def main():
 need(not os.environ.get('LD_LIBRARY_PATH') and not os.environ.get('LD_PRELOAD'),'clean loader environment required')
 need(sha(OLD)==OLD_SHA,'old formal release changed')
 old=load(OLD); original_inputs=old['inputs_sha256']
 changes=diff(original_inputs)
 need(len(changes)==1 and changes[0]['path']==str(CHANGED) and changes[0]['current']==CURRENT_LOG_SHA,'unexpected formal drift')
 need(not NEW.exists() and not NEW.with_suffix('.json.sha256').exists() and not LOG.exists(),'new execution identity occupied')
 for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:(OUT/('before_'+name)).write_bytes((ROOT/'docs/reports'/name).read_bytes())
 # Preserve all old inputs at their current bytes, including the documented changed log.
 protected={p:sha(p) for p in original_inputs}
 for tree in [LRP,ROOT/'docs/reports/URV_S2_formal_launch_release_20261102',ROOT/'docs/reports/URV_S2_perf_results_review_20261102']:
  for p in tree.rglob('*'):
   if p.is_file():protected[str(p)]=sha(p)
 for p in [OLD,OLD.with_suffix('.json.sha256'),CASE/'evidence/S2_formal_controller_reuse_v1_20261102_01.log']:
  protected[str(p)]=sha(p)
 save(OUT/'protected_inputs_before.json',protected)
 for name,h in load(LRP/'report_manifest.json').items():need(sha(LRP/name)==h,'LRP report manifest drift')
 sys.path.insert(0,str(CASE/'scripts'));import run_S2 as runner
 from stage_s2 import verify_zero_receipt,validate_formal_authority,require_pristine
 from check_results import binding
 B=CASE/'evidence/preparation_B.json';B_SHA='2e55f3369f9445e7763ee1f9a87c57f79348d1b332c959bc038c1bcc4739081f'
 base,resources=runner.inspect(B,B_SHA);verify_zero_receipt(base)
 need(not (CASE/'launch_attempts').exists(),'formal attempt exists; do not retry')
 active=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:args=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x]
  except OSError:continue
  if args and (Path(args[0]).name=='urv_reference' or any(Path(a).name in ('run_S2.py','run_perf.py','audit_S2_zero.py') for a in args)):
   active.append(dict(pid=int(p.name),args=args))
 need(not active,'related task active')
 sessions=subprocess.run(['tmux','list-sessions','-F','#{session_name}'],capture_output=True,text=True)
 need(sessions.returncode in (0,1),'tmux query error')
 need(not any(s.startswith('urv_s2') for s in sessions.stdout.splitlines()),'S2 session active')
 ldd=subprocess.run(['/usr/bin/ldd',base['provenance']['native_binary']],capture_output=True,text=True,check=True)
 (OUT/'ldd_clean.txt').write_text(ldd.stdout)
 libs=load(base['provenance']['build_environment'])['dynamic_library_sha256']
 paths={str(Path(m.group(1)).resolve()) for line in ldd.stdout.splitlines() if (m:=re.search(r'(/[^\s]+)',line))}
 need('not found' not in ldd.stdout and paths==set(libs) and not diff(libs),'runtime library closure drift')
 perf_release=PERF/'evidence/S2_perf_launch_release_v1_20261102_01.json';perf_bound=load(perf_release)
 need(not diff(perf_bound['inputs_sha256']),'PERF input drift')
 raw=load(ROOT/'docs/reports/URV_S2_perf_results_review_20261102/raw_evidence_sha256.json')
 need(diff(raw)==changes,'PERF difference set differs from known log')
 # Replay already completed evidence only, redirecting report writes to this new directory.
 spec=importlib.util.spec_from_file_location('recovery_perf_review',ROOT/'docs/reports/URV_S2_perf_results_review_20261102/review_existing.py')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=OUT
 checked=m.c.verify(perf_release,m.EXPECTED);m.c.authorize(checked)
 reviews=[m.independent(r,checked) for r in checked['prepared_benchmark_runs']]
 need(reviews==load(ROOT/'docs/reports/URV_S2_perf_results_review_20261102/independent_review.json')['direction_reviews'],'PERF replay differs')
 first,second=[load(Path(r['output_directory'])/'performance_receipt.json') for r in checked['prepared_benchmark_runs']]
 need(second['process_start_monotonic']>first['process_exit_monotonic'],'P/T sequence invalid')
 snapshot=OUT/'PERF_controller_changed_snapshot.log.txt';snapshot.write_bytes(CHANGED.read_bytes())
 rejected=OUT/'old_formal_rejection_snapshot.log.txt';rejected.write_bytes((CASE/'evidence/S2_formal_controller_reuse_v1_20261102_01.log').read_bytes())
 adoption=OUT/'adoption.json'
 save(adoption,dict(recorded_at=now(),source='current_user_message',verbatim='采用 S2-LRP-v1 后，准备独立恢复清单与新正式执行绑定，完成只读核对，再交付用户手动启动命令；不自动启动。',preparation_and_command_delivery_authorized=True,AI_may_start_solver=False,new_solver_authorization_granted_by_this_record=False,formal_authority_source=old['launch_authorization_evidence']))
 precheck=OUT/'precheck.json'
 save(precheck,dict(checked_at=now(),resources=resources,runtime_libraries_sha256=libs,active_processes=active,tmux_stdout=sessions.stdout,tmux_stderr=sessions.stderr,formal_directories_pristine=True,no_formal_attempts=True,B_inputs_verified=len(base['inputs_sha256']),PERF_inputs_verified=len(perf_bound['inputs_sha256']),PERF_raw_count=len(raw),PERF_raw_unchanged=len(raw)-1,PERF_replays_exact=True,P_then_T_verified=True))
 recovery=OUT/'recovery_manifest.json'
 save(recovery,dict(protocol='S2-LRP-v1',recorded_at=now(),old_release=dict(path=str(OLD),sha256=OLD_SHA,status='SUPERSEDED_FOR_FUTURE_LAUNCH_NOT_MODIFIED',original_failure='EvidenceError: bound input drift'),exception=dict(original_path=str(CHANGED),expected_original_sha256=original_inputs[str(CHANGED)],current_sha256=CURRENT_LOG_SHA,current_size_bytes=CHANGED.stat().st_size,snapshot_path=str(snapshot),snapshot_sha256=sha(snapshot),current_log_meaning='Old PERF inspect/pristine rejected already used output before execute',unknowns=['caller','complete command','whether execute flag present','complete invocation history']),old_formal_rejection_snapshot=dict(path=str(rejected),sha256=sha(rejected)),PERF_resource_prerequisite='RETAINED_WITH_DOCUMENTED_LOG_EXCEPTION',old_raw_closure_intact=False,retained_old_inputs=len(original_inputs)-1,required_B_inputs=len(base['inputs_sha256']),native_run_ids_unchanged=True,no_scientific_threshold_change=True,no_solver_retry_or_launch=True))
 data=copy.deepcopy(old);inputs=dict(original_inputs);del inputs[str(CHANGED)]
 added=[]
 def include(p):
  p=str(Path(p).resolve());h=sha(p);need(p not in inputs or inputs[p]==h,'closure conflict '+p)
  if p not in inputs:added.append(p)
  inputs[p]=h
 for p in [snapshot,rejected,OLD,OLD.with_suffix('.json.sha256'),adoption,precheck,recovery,OUT/'ldd_clean.txt',OUT/'prepare_recovery.py'] :include(p)
 for p in LRP.iterdir():
  if p.is_file():include(p)
 for r in checked['prepared_benchmark_runs']:include(OUT/(r['run_id']+'_checker_replay.json'))
 retained={p:h for p,h in original_inputs.items() if p!=str(CHANGED)}
 need(all(inputs.get(p)==h for p,h in retained.items()),'inherited inputs dropped or changed')
 need(all(inputs.get(p)==h for p,h in base['inputs_sha256'].items()),'B not fully retained')
 need(set(original_inputs)-set(inputs)=={str(CHANGED)},'unexpected removed input')
 delta=OUT/'input_set_delta.json';save(delta,dict(removed_paths=[str(CHANGED)],retained_exactly=len(retained),added_paths_before_delta_file=sorted(added),replacement_snapshot=str(snapshot),B_retained_exactly=len(base['inputs_sha256'])))
 include(delta)
 data.update(inputs_sha256=inputs,released_at=now(),supersedes_release=dict(path=str(OLD),sha256=OLD_SHA,reason='S2-LRP-v1 documented controller log exception'),recovery_protocol='S2-LRP-v1',recovery_manifest=dict(path=str(recovery),sha256=sha(recovery)),recovery_scope_adoption=dict(path=str(adoption),sha256=sha(adoption)),PERF_RESOURCE_PREREQUISITE='RETAINED_WITH_DOCUMENTED_LOG_EXCEPTION',ORIGINAL_PERF_RAW_CLOSURE_INTACT=False)
 need(data['launch_authorization']==old['launch_authorization'] and data['launch_authorization_evidence']==old['launch_authorization_evidence'],'authority changed')
 need(data['prepared_runs']==old['prepared_runs'] and data['resources']==old['resources'],'scope changed')
 need(not diff(inputs),'new input drift');save(NEW,data);digest=sha(NEW)
 with NEW.with_suffix('.json.sha256').open('x') as f:f.write(digest+'\n')
 bound,available=runner.inspect(NEW,digest);binding(NEW,digest);validate_formal_authority(bound)
 wrong=False
 try:runner.inspect(NEW,'0'*64)
 except ValueError:wrong=True
 need(wrong,'wrong external SHA not rejected')
 stdout=io.StringIO()
 with patch('subprocess.Popen',side_effect=AssertionError('NO CHILD PROCESS ALLOWED IN READONLY ENTRY')),patch.object(sys,'argv',['run_S2.py','--release',str(NEW),'--release-sha256',digest]),contextlib.redirect_stdout(stdout):
  need(runner.main()==0,'readonly entry failed')
 (OUT/'release_readonly.stdout.txt').write_text(stdout.getvalue())
 require_pristine(data['prepared_runs']);need(not (CASE/'launch_attempts').exists(),'readonly created attempts')
 need(not diff(protected) and not diff(inputs),'postcheck protected/input drift')
 save(OUT/'verification.json',dict(checked_at=now(),NEW_FORMAL_BINDING_PASS=True,release_path=str(NEW),release_sha256=digest,new_inputs=len(inputs),old_exactly_retained=len(retained),B_exactly_retained=len(base['inputs_sha256']),excluded_live_log=str(CHANGED),runtime_libraries=len(libs),protected_files_unchanged=len(protected),resources=available,default_readonly_exit=0,wrong_external_SHA_rejected=True,no_launch_attempts=True,solver_calls=0,VTK_calls=0,builds=0,old_binding_modified=False,actual_formal_run_ids=[],formal_simulation_authorized=True,AI_may_start_solver=False,user_manually_starts=True))
 program=shlex.join(['env','-u','LD_LIBRARY_PATH','-u','LD_PRELOAD','/home/dell/miniconda3/bin/python3','-B','scripts/run_S2.py','--release',str(NEW),'--release-sha256',digest,'--execute'])
 inner='cd '+shlex.quote(str(CASE))+' && exec '+program+' > '+shlex.quote(str(LOG))+' 2>&1'
 command='tmux new-session -d -s '+SESSION+' '+shlex.quote(inner)
 (OUT/'START_COMMAND.txt').write_text(command+'\n')
 save(OUT/'command_binding.json',dict(command=command,session=SESSION,controller_log_path=str(LOG),release_path=str(NEW),release_sha256=digest,command_generated=True,command_executed=False,tmux_started_by_AI=False))
 print(json.dumps(dict(release_sha256=digest,inputs=len(inputs),MemAvailable_GiB=available['MemAvailable_bytes']/1024**3,disk_free_GiB=available['disk_free_bytes']/1024**3,solver_calls=0),indent=2))
if __name__=='__main__':main()
