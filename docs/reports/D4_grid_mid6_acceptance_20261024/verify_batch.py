#!/usr/bin/env python3
"""Read-only batch/config/provenance/completeness review, separate from numerical reader."""
from pathlib import Path
import csv,datetime,hashlib,json,math,subprocess
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/D_series/D4_variable_groove_transport_20261023'
STAGE=CASE/'development_grid_mid6_20261024'
BATCH=CASE/'results/development_grid_mid6_20261024_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))
def kv(p):return dict(s.split('=',1) for s in Path(p).read_text().splitlines() if '=' in s)
def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
 manifest=load(BATCH/'stage_manifest.json');completion=load(BATCH/'stage_completion.json');progress=load(BATCH/'stage_progress.json');table=rows(STAGE/'stage_cases.csv')
 ids=[r['planned_case_id'] for r in table]
 assert len(ids)==len(set(ids))==6 and manifest['case_ids']==ids
 assert [r['case_id'] for r in progress]==ids
 assert completion['attempted_cases']==6 and completion['exit_code']==0 and completion['next_stage_started'] is False
 assert (BATCH/'exit_code.txt').read_text().strip()=='0' and not (BATCH/'stage_error.txt').exists()
 assert all(r['exit_code']==0 for r in progress)
 assert manifest['analysis_automatically_run'] is False and manifest['next_stage_automatically_run'] is False
 release=load(STAGE/'release.json');assert sha(STAGE/'release.json')==manifest['release_sha256']
 bindings={};counts=[];config_checks=[];aux_rows=0;resources=[]
 for row,pr in zip(table,progress):
  out=BATCH/pr['output'];runid=row['planned_case_id'].replace('CAND_','D4_',1)+'_'+manifest['batch_id']
  assert out==BATCH/runid/'steady'
  m=load(out/'run_manifest.json');cfg=kv(out/'run_config.txt');effective=kv(out/'effective_config.txt');r=kv(out/'result.txt');txt=kv(out/'run_manifest.txt')
  assert cfg['run_id']==m['run_id']==r['run_id']==txt['run_id']==runid
  assert m['planned_case_id']==row['planned_case_id'] and m['stage']=='grid_mid6_development'
  assert m['model_prediction_data'] is False and m['stage_release_sha256']==manifest['release_sha256']
  assert cfg['output_directory']==str(out) and cfg['mode']==m['mode']=='steady'
  assert (out/'run_config.txt').read_bytes()==(STAGE/'launch_configs'/(row['planned_case_id']+'.txt')).read_bytes()
  assert txt['config_sha256']==sha(out/'run_config.txt')
  assert txt['binary_sha256']==sha(CASE/'build/variable_groove_transport')
  assert m['command']==[str(CASE/'build/variable_groove_transport'),str(out/'run_config.txt')]
  assert cfg['direction']==row['direction']
  for ck,rk in [('h_nm','h_nm'),('d_nm','d_nm'),('w_nm','w_nm'),('period_nm','P_nm'),('Ly_nm','Ly_nm'),('dx_nm','dx_nm'),('nu_m2_s','nu_m2_s'),('acceleration_m_s2','acceleration_m_s2')]:assert float(cfg[ck])==float(row[rk])
  for key in ['rho_phys_kg_m3','nu_phys_m2_s','mu_phys_Pa_s','tau']:
   expected={'rho_phys_kg_m3':1000,'nu_phys_m2_s':1e-6,'mu_phys_Pa_s':.001,'tau':1}[key]
   assert math.isclose(float(r[key]),expected,rel_tol=1e-14)
  for fkey,expected in [('descriptor','D3Q19_FORCE'),('collision','ForcedBGK'),('periodicity','x_y')]:assert r[fkey]==expected
  assert r['RESULT_PASS']=='false' and r['exit_code']=='0'
  assert load(out/'inputs_after.json')['unchanged'] is True
  assert (out/'exit_code.txt').read_text().strip()=='0' and (out/'run.log').stat().st_size>0
  b=kv(out/'boundary_audit.txt');assert b['geometry_PASS']==b['q_audit_PASS']=='true'
  for k,h in m['inputs_sha256'].items():
   p=str((ROOT/Path(k)).resolve())
   assert p not in bindings or bindings[p]==h
   bindings[p]=h
  for k,h in m['OpenLB_build_environment']['library_hashes'].items():bindings[str(Path(k).resolve())]=h
  head=[v for v in m['OpenLB_build_environment']['commands'] if v['command']==['git','-C','/home/dell/openlb','rev-parse','HEAD']]
  assert len(head)==1 and head[0]['exit_code']==0 and head[0]['stdout'].strip()==release['OpenLB_commit']
  rr=load(out/'resource_usage.json');assert rr['elapsed_seconds']>0 and rr['max_rss_kb']>0;resources.append(rr)
  for n in ['velocity_profile.csv','pressure_profile.csv','energy_dissipation.csv','field_slice.csv','result_summary.csv']:
   data=rows(out/n);assert data
   for item in data:
    for key,value in item.items():
     if key not in ('Case','direction'):assert math.isfinite(float(value)),(n,key)
   aux_rows+=len(data)
  summary=rows(out/'result_summary.csv');assert len(summary)==1 and summary[0]['Case']==runid
  assert float(summary[0]['Keff'])==float(r['Keff_m3']) and float(summary[0]['J'])==float(r['J_main_m2_s'])
  counts.append({'run_id':runid,'boundary_links':int(b['candidate_links']),'fluid_nodes':int(b['material_1'])})
  config_checks.append({'run_id':runid,'exact_prepared_config_match':True,'manifest_command_and_identity_match':True,'own_exit_zero':True})
 for k,h in bindings.items():assert sha(k)==h,k
 current_head=subprocess.check_output(['git','-C','/home/dell/openlb','rev-parse','HEAD'],text=True).strip();assert current_head==release['OpenLB_commit']
 lockpath=ROOT/'docs/reports/Correlation_selection_freeze_20261024/candidate_lock.json';lock=load(lockpath)
 assert sha(lockpath)=='08ae91994910e98afd701143928a5186a9b22d003c96f73d9643c2eb11d810dc'
 for k,h in lock['bound_files'].items():assert sha(lockpath.parent/k)==h,k
 old=load(OUT/'protection_before.json');assert all(sha(k)==h for k,h in old.items())
 start=datetime.datetime.fromisoformat(manifest['started_UTC']);end=datetime.datetime.fromisoformat(completion['finished_UTC'])
 write('batch_review.json',{'ok':True,'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'batch_id':manifest['batch_id'],'start_utc':start.isoformat(),'end_utc':end.isoformat(),'wall_seconds':(end-start).total_seconds(),'cases':6,'batch_and_case_exit_codes_zero':True,'unique_manifest_bound_paths_verified':len(bindings),'stage_release_entries':len(release['bound_inputs_sha256']),'protected_paths_unchanged':len(old),'auxiliary_csv_rows_checked_finite':aux_rows,'sum_fluid_nodes_over_6_directions':sum(v['fluid_nodes'] for v in counts),'sum_boundary_links_over_6_directions':sum(v['boundary_links'] for v in counts),'distinct_geometries':3,'resource_peak_RSS_kib':max(r['max_rss_kb'] for r in resources),'sum_solver_elapsed_seconds':sum(r['elapsed_seconds'] for r in resources),'OpenLB_commit':current_head,'G4_lock_sha256':sha(lockpath),'G4_bound_files_verified':len(lock['bound_files']),'source_RESULT_PASS_preserved_false':True,'grid_accuracy_evaluated':False,'prediction_stage_released':False,'config_checks':config_checks,'geometry_counts':counts})
 write('manifest_bindings_verified.json',bindings)
 print('Batch identity, exact configs, exits, source/build bindings, CSV and protected hashes: PASS')
if __name__=='__main__':main()
