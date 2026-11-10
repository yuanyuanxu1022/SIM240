#!/usr/bin/env python3
"""Static 12-case review and synthetic arithmetic probes. Never launches OpenLB."""
from pathlib import Path
from decimal import Decimal,ROUND_CEILING
import ast,csv,datetime,hashlib,importlib.util,json,math,shutil,sys
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
CASE=ROOT/'CASE/D_series/D4_variable_groove_transport_20261023';PLAN=CASE/'development_completion_plan_20261024';GIB=1024**3

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))
def kv(p):return dict(s.split('=',1) for s in Path(p).read_text().splitlines() if '=' in s)
def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csvout(n,rs):
 with (OUT/n).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def ceil(x):return int(x.to_integral_value(rounding=ROUND_CEILING))

def main():
 planrows=rows(PLAN/'development_grid12.csv');canonical={r['planned_case_id']:r for r in rows(CASE/'protocol/candidate_cases.csv')};assert len(planrows)==12
 before={str(p.resolve()):sha(p) for p in PLAN.rglob('*') if p.is_file()}
 old=load(ROOT/'docs/reports/D4_remaining14_acceptance_20261024/protection_before.json');protected_changes=[]
 for p,h in old.items():
  actual=sha(p)
  if actual!=h:protected_changes.append(p)
  before[p]=actual
 assert not protected_changes,protected_changes
 acceptance_paths=[ROOT/'docs/reports/D4_remaining14_acceptance_20261024/verdict.json',ROOT/'docs/reports/D4_prediction_readiness_20261024/readiness.json']
 for p in acceptance_paths:before[str(p)]=sha(p)
 write('protected_inputs_before.json',before)
 coarse_s=load(ROOT/'docs/reports/D4_prediction_readiness_20261024/screen_acceptance/scalar_results.json')+load(ROOT/'docs/reports/D4_remaining14_acceptance_20261024/scalar_acceptance/scalar_results.json')
 accepted={}
 for s in coarse_s:
  if float(s['acceleration_m_s2'])!=1e5:continue
  batch='development_screen_20261023_v1' if 'development_screen_20261023' in s['run_id'] else 'development_remaining14_20261024_v1'
  out=CASE/'results'/batch/s['run_id']/'steady';cfg=kv(out/'run_config.txt')
  k=tuple(Decimal(cfg[n]) for n in ['h_nm','d_nm','w_nm'])+(cfg['direction'],)
  assert k not in accepted
  assert s['independent_numerical_gate'] and s['geometry_PASS'] and (out/'exit_code.txt').read_text().strip()=='0'
  accepted[k]=(s,out,cfg)
 batches={b['group']:b for b in load(PLAN/'batches.json') if b['group']!='DEV14'}
 mem={s.split(':')[0]:int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith(('MemTotal:','MemAvailable:','SwapTotal:','SwapFree:'))}
 disk=shutil.disk_usage(CASE).free
 resource={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'memory_bytes':mem,'free_disk_bytes':disk,'memory_available_GiB':mem['MemAvailable']/GIB,'disk_free_GiB':disk/GIB,'cgroup_memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip() if Path('/sys/fs/cgroup/memory.max').exists() else None,'cgroup_memory_current':Path('/sys/fs/cgroup/memory.current').read_text().strip() if Path('/sys/fs/cgroup/memory.current').exists() else None,'swap_not_counted_as_available_RAM':True}
 write('resource_snapshot.json',resource)
 mid14=load(ROOT/'docs/reports/D4_remaining14_acceptance_20261024/verdict.json');assert mid14['independent_remaining14_acceptance']=='PASS'
 grouped=[];pairs=[];matrix=[];coarse_records=[];seen_coarse=set();input_fields=['role','h_nm','d_nm','w_nm','P_nm','Ly_nm','phi','direction','dx_nm','acceleration_m_s2','nu_m2_s','rho_kg_m3','tau','blind_geometry']
 for r in planrows:
  source=canonical[r['planned_case_id']];assert all(r[k]==source[k] for k in input_fields)
  assert source['role']=='grid_reference' and source['blind_geometry']=='False'
  h,d,w,P,Ly,dx=[Decimal(r[k]) for k in ['h_nm','d_nm','w_nm','P_nm','Ly_nm','dx_nm']]
  assert h==75 and P==Ly==2*w and dx in [Decimal('2.5'),Decimal('1.25')]
  assert (h,d,w) in [(Decimal(75),Decimal(25),Decimal(60)),(Decimal(75),Decimal(120),Decimal(60)),(Decimal(75),Decimal(120),Decimal(240))]
  assert all(x/dx==(x/dx).to_integral_value() for x in [h,d,w,P,Ly,(P-w)/2])
  n=int((P*Ly*h+w*Ly*d)/dx**3);win=ceil(Decimal('4.5')*(h/dx)**2);cap=ceil(Decimal(48)*((h+d)/dx)**2);dt=dx**2*Decimal('1e-18')/(Decimal(6)*Decimal('1e-6'))
  assert n==int(r['computed_fluid_nodes']) and win==int(r['window_steps']) and cap==int(r['maximum_steps'])
  spec=load(PLAN/'planned_configs'/(r['planned_case_id']+'.json'));assert not spec['execution_released'] and 'run_id' not in spec['solver_parameters'] and 'output_directory' not in spec['solver_parameters']
  a,out,cfg=accepted[(h,d,w,r['direction'])];assert Decimal(cfg['period_nm'])==P and Decimal(cfg['Ly_nm'])==Ly and cfg['dx_nm']=='5'
  if (h,d,w,r['direction']) not in seen_coarse:
   seen_coarse.add((h,d,w,r['direction']));coarse_records.append({'h_nm':str(h),'d_nm':str(d),'w_nm':str(w),'P_nm':str(P),'Ly_nm':str(Ly),'direction':r['direction'],'dx_nm':5,'run_id':a['run_id'],'K_m3':a['K_m3'],'source_result':str(out/'result.txt'),'source_result_sha256':sha(out/'result.txt'),'acceptance_evidence':str(ROOT/'docs/reports'/('D4_prediction_readiness_20261024/REPORT.md' if 'development_screen' in a['run_id'] else 'D4_remaining14_acceptance_20261024/REPORT.md'))})
  geom=CASE/r['existing_geometry_precheck_evidence'];b=kv(geom/'boundary_audit.txt');e=kv(geom/'result.txt')
  assert (geom/'exit_code.txt').read_text().strip()=='0' and b['geometry_PASS']=='true' and b['q_audit_PASS']=='true'
  assert e['collide_and_stream_calls']=='0' and int(e['fluid_nodes'])==n
  assert b['q_min']==b['q_max']=='0.5' and int(b['unresolved_link_count'])==0
  oldconfig=kv(geom/'run_config.txt');actualdir=CASE/'results'/r['planned_batch_id']/(r['planned_case_id'].replace('CAND_','D4_',1)+'_'+r['planned_batch_id'])/'steady'
  formal_dirs=list((CASE/'results').glob('*/'+r['planned_case_id'].replace('CAND_','D4_',1)+'_*/steady/result.txt'));assert not formal_dirs
  factor=(Decimal(5)/dx)**2;scenario_steps=ceil(Decimal(a['steps'])*factor)
  # NumPy std on a strided window creates a dense deviation temporary. Do not allocate it.
  temp_scenario=max(0,scenario_steps+1-win+1)*win*8;temp_cap=(cap+1-win+1)*win*8
  rec={'planned_case_id':r['planned_case_id'],'batch':r['plan_batch'],'direction':r['direction'],'h_nm':str(h),'d_nm':str(d),'w_nm':str(w),'P_nm':str(P),'dx_nm':str(dx),'dt_s':str(dt),'fluid_nodes':n,'window_steps':win,'maximum_steps':cap,'coarse_run_id':a['run_id'],'coarse_steps_observed':a['steps'],'coarse_solver_seconds_observed':a['elapsed_seconds'],'same_geometry_same_physical_stopping_scenario_seconds':float(Decimal(str(a['elapsed_seconds']))*(Decimal(5)/dx)**5),'existing_geometry_precheck_direction':oldconfig['direction'],'existing_geometry_precheck_peak_RSS_KiB':int(r['existing_geometry_precheck_peak_RSS_KiB']),'existing_precheck_path':str(geom),'formal_result_exists':False,'actual_run_config_exists':(actualdir/'run_config.txt').exists(),'planned_template_is_direct_solver_input':False,'scenario_sliding_std_dense_temporary_GiB':temp_scenario/GIB,'step_cap_sliding_std_dense_temporary_GiB':temp_cap/GIB,'historical_cap_solver_work_hours':float(r['step_cap_work_extrapolated_hours']),'old_screen_scenario_hours':float(r['screen_scaled_stopping_scenario_hours'])}
  matrix.append(rec)
 assert len(seen_coarse)==6
 csvout('case_review12.csv',matrix);csvout('accepted_coarse6.csv',coarse_records)
 for label,b in batches.items():
  rs=[r for r in matrix if r['batch']==label];assert len(rs)==b['cases']
  grouped.append({'group':label,'cases':len(rs),'minimum_available_RAM_GiB':b['minimum_available_RAM_GiB'],'minimum_free_disk_GiB':b['minimum_free_disk_GiB'],'snapshot_RAM_sufficient':mem['MemAvailable']>=b['minimum_available_RAM_GiB']*GIB,'snapshot_disk_sufficient':disk>=b['minimum_free_disk_GiB']*GIB,'existing_precheck_peak_RSS_GiB':max(r['existing_geometry_precheck_peak_RSS_KiB'] for r in rs)/1024**2,'historical_screen_scenario_hours':b['screen_scaled_stopping_scenario_hours'],'coarse_same_geometry_scenario_hours':sum(r['same_geometry_same_physical_stopping_scenario_seconds'] for r in rs)/3600,'historical_step_cap_work_extrapolated_hours':b['step_cap_work_extrapolated_hours'],'largest_naive_std_temp_scenario_GiB':max(r['scenario_sliding_std_dense_temporary_GiB'] for r in rs),'largest_naive_std_temp_step_cap_GiB':max(r['step_cap_sliding_std_dense_temporary_GiB'] for r in rs),'execution_released':False,'automatic_next_batch':False})
 write('batch_resource_review.json',grouped)
 spec=importlib.util.spec_from_file_location('reviewed_grid_comparator',PLAN/'compare_grid.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);policy=load(PLAN/'grid_policy.json')
 tests=mod.selfcheck(policy);write('existing_comparator_selfcheck.json',tests)
 synthetic=[]
 for h,d,w in policy['geometries_h_d_w_nm']:
  for dx in policy['dx_nm_coarse_to_fine']:
   for dr in ('P','T'):synthetic.append(dict(h_nm=h,d_nm=d,w_nm=w,dx_nm=dx,direction=dr,K_m3=(2 if dr=='P' else 1)*(1+.0005*(dx/1.25)**2)*1e-23,numerical_gate_pass='true',geometry_pass='true',independent_reference_accepted='true',run_id='synthetic_'+str(len(synthetic)),acceptance_evidence='synthetic_not_real'))
 full=mod.evaluate(synthetic,policy);assert full['GRID_SENSITIVITY_TARGET']=='PASS'
 narrow=mod.evaluate([r for r in synthetic if r['w_nm']==60],policy);assert narrow['GRID_SENSITIVITY_TARGET']=='INCOMPLETE_OR_REFERENCE_INVALID' and len(narrow['missing'])==6
 after_first10=mod.evaluate([r for r in synthetic if not(r['w_nm']==240 and r['dx_nm']==1.25)],policy);assert after_first10['GRID_SENSITIVITY_TARGET']=='INCOMPLETE_OR_REFERENCE_INVALID' and len(after_first10['missing'])==2
 forged=[dict(r,run_id='same_id',acceptance_evidence='/does/not/exist',P_nm=999,Ly_nm=999,nu_m2_s=999) for r in synthetic];identity=mod.evaluate(forged,policy);assert identity['GRID_SENSITIVITY_TARGET']=='PASS'
 boundary=mod.quantity([1.01,1.002,1.0],policy)
 empty=mod.evaluate([],policy);assert len(empty['missing'])==18
 probes={'all_data_synthetic':True,'existing_14_checks':tests,'physical_magnitude_K_full_table_status':full['GRID_SENSITIVITY_TARGET'],'narrow_only_12_rows_status':narrow['GRID_SENSITIVITY_TARGET'],'narrow_only_missing_wide_rows':narrow['missing'],'coarse6_mid6_narrowfine4_status':after_first10['GRID_SENSITIVITY_TARGET'],'coarse6_mid6_narrowfine4_missing':after_first10['missing'],'declared_acceptance_with_nonexistent_evidence_wrong_P_and_duplicate_runid_status':identity['GRID_SENSITIVITY_TARGET'],'explanation':'existing comparator is arithmetic only; missing exporter must prove identity and bindings before use','exact_decimal_one_percent_boundary_float_probe':boundary,'no_real_grid_results_read':True}
 write('comparator_probes.json',probes);csvout('synthetic_full18.csv',synthetic)
 # Observe existing runtime allowlists without importing executable stage modules.
 stage_inventory=[]
 for release in [CASE/'evidence/formal_run_release.json',CASE/'development_stage_20261023/release.json',CASE/'development_remaining14_20261024/release.json']:
  obj=load(release);allowed=set(obj['allowed_case_ids']);overlap=allowed & {r['planned_case_id'] for r in planrows}
  assert not overlap;stage_inventory.append({'release':str(release),'grid12_allowed':len(overlap),'allowed_count':len(allowed)})
 for file in [PLAN/'compare_grid.py',PLAN/'verify_plan.py',CASE/'tools/run_case.py',CASE/'development_remaining14_20261024/run_remaining.py']:ast.parse(file.read_text())
 write('entry_review.json',{'dedicated_grid_runtime_stage_directory_found':False,'searched_case_directories':[p.name for p in CASE.iterdir() if p.is_dir()],'existing_runtime_releases':stage_inventory,'actual_grid12_configs_found':sum(r['actual_run_config_exists'] for r in matrix),'direct_solver_templates':0,'existing_zero_step_unique_meshes_verified':6,'zero_step_evidence_is_formal_run':False,'all_12_formal_case_results_absent':True,'existing_plan_verifier_stale_after_DEV14':'verify_plan.py asserts every planned result batch absent, now false for completed DEV14; do not execute it to rewrite frozen verification','default_launch_command_delivered':False})
 changed=[p for p,h in before.items() if sha(p)!=h];assert not changed
 write('static_verification.json',{'ok':True,'scope':'static review, coarse-source pairing, existing zero-step evidence and synthetic arithmetic only','grid_cases_checked':12,'accepted_coarse_references':6,'zero_step_unique_geometries':6,'frozen_protected_paths_checked':len(before),'protected_changed':changed,'synthetic_comparator_selfchecks':tests['synthetic_checks'],'readiness_not_inferred_from_test_pass':True,'solver_launched':False,'compile_run':False,'new_steady_results':0,'prediction_stage_released':False})
 print(json.dumps({'static_review_completed':True,'grid_runtime_ready':False,'resources':resource,'batches':grouped,'comparison_gaps_reproduced':True},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
