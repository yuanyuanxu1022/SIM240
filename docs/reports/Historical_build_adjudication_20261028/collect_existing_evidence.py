"""Read stored artifacts only; no solver, compilation, model import or fitting."""
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
import csv,json,hashlib,re
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
TABLE=ROOT/'docs/reports/SIM240_Supplementary_Methods_20261024/Table_S1_run_inventory.csv'
RESID=ROOT/'CASE/D_series/D2_groove_error_map/results/analysis/v2_residuals.csv'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=list(csv.DictReader(TABLE.open()))
oldjson=ROOT/'docs/reports/Historical_build_binding_recovery_20261028/binding_recovery.json'
old=json.loads(oldjson.read_text())
protected={TABLE,RESID,oldjson,ROOT/'docs/reports/Historical_build_binding_recovery_20261028/REPORT.md',ROOT/'docs/reports/Primary_text_build_evidence_20261027/MINIMUM_EVIDENCE_CONTRACT.md',ROOT/'docs/reports/Primary_text_build_evidence_20261027/binary_group_contract.csv',ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md',ROOT/'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md',ROOT/'tools/audit_historical_build_binding.py',ROOT/'CASE/D_series/D2_groove_error_map/analysis_fit_v2.py',ROOT/'CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp'}
for r in rows:
 protected.update([ROOT/r['manifest_path'],ROOT/r['result_path']])
 ex=(ROOT/r['result_path']).parent/'exit_code.txt'
 if ex.exists():protected.add(ex)
for r in old['runs']:
 for key in ['binary_resolved','dep_file']:
  if r.get(key):
   p=Path(r[key]);p=p if p.is_absolute() else ROOT/p
   if p.is_file():protected.add(p)
for p in [Path('/home/dell/openlb/config.mk'),Path('/home/dell/openlb/CITATION.cff')]:
 if p.is_file():protected.add(p)
manifest={str(p):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(protected)}
(OUT/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
def parse(p):
 kv={};he=[]
 for n,line in enumerate(p.read_text().splitlines(),1):
  if '=' in line:
   k,_,v=line.partition('=');kv[k.strip()]=v.strip()
  m=re.match(r'^([a-f0-9]{64})\s+(\S+)$',line.strip())
  if m:he.append({'sha256':m[1],'path':m[2],'line':n})
 return kv,he
records=[];cache={}
oldby={r['run_id']:r for r in old['runs']}
for r in rows:
 mp=ROOT/r['manifest_path'];rp=ROOT/r['result_path'];kv,hs=parse(mp);rv,_=parse(rp)
 binsha=kv.get('binary_sha256')
 if not binsha:
  matches=[x['sha256'] for x in hs if x['sha256']==r['binary_sha256']]
  binsha=matches[0] if matches else None
 b=oldby[r['run_id']].get('binary_resolved');actual=None
 if b and Path(b).is_file():
  if b not in cache:cache[b]=sha(Path(b))
  actual=cache[b]
 ex=rp.parent/'exit_code.txt';exit_value=ex.read_text().strip() if ex.exists() else None
 rk=rv.get('Keff_m3')
 rec={'run_id':r['run_id'],'group':r['group'],'h_nm':float(r['h_nm']),'d_nm':float(r['d_nm']),'dx_nm':float(r['dx_nm']),'direction':r['direction'],'manifest_path':r['manifest_path'],'result_path':r['result_path'],'binary_sha256_S1':r['binary_sha256'],'binary_sha256_manifest':binsha,'manifest_matches_S1':binsha==r['binary_sha256'],'retained_candidate_binary':b,'candidate_sha256':actual,'candidate_matches_record':actual==r['binary_sha256'],'K_m3_S1':r['K_m3'],'K_m3_result':rk,'K_matches_S1':float(rk)==float(r['K_m3']) if rk else False,'recorded_PASS':rv.get('PASS'),'stored_exit_code':exit_value,'source_build_fields_present':{k:k in kv for k in ['source_sha256','generated_source_sha256','openlb_commit','compiler','compile_flags']}}
 if r['group']=='main':rec['data_role_current_script']='calibration' if float(r['d_nm']) in {25,50,100} and float(r['h_nm']) in {50,75,125} else 'extension'
 records.append(rec)
assert len(records)==52 and all(r['manifest_matches_S1'] and r['K_matches_S1'] for r in records)
group_counts=Counter(r['binary_sha256_S1'] for r in records)
cross=Counter((r.get('data_role_current_script','not_main'),r['binary_sha256_S1']) for r in records)
main=[r for r in records if r['group']=='main'];assert len(main)==36
pairs=defaultdict(list)
for r in main:pairs[(r['h_nm'],r['d_nm'])].append(r)
pair_rows=[{'h_nm':h,'d_nm':d,'directions':sorted(x['direction'] for x in rs),'same_recorded_binary_hash':len({x['binary_sha256_S1'] for x in rs})==1,'binary_hashes':sorted({x['binary_sha256_S1'] for x in rs}),'data_role':rs[0]['data_role_current_script']} for (h,d),rs in sorted(pairs.items())]
assert len(pair_rows)==18 and all(r['same_recorded_binary_hash'] for r in pair_rows)
residuals=list(csv.DictReader(RESID.open()));assert len(residuals)==18
summary=[]
for role in ['calibration','extension']:
 chosen=[r for r in residuals if ('calibration' if float(r['d_nm']) in {25,50,100} and float(r['h_nm']) in {50,75,125} else 'extension')==role]
 for dr in ['P','T']:
  vals=[float(r[f'E1_{dr}_pct']) for r in chosen]
  summary.append({'role':role,'direction':dr,'geometries':len(chosen),'mean_pct_from_stored_rounded_CSV':sum(vals)/len(vals),'max_abs_pct_from_stored_rounded_CSV':max(abs(v) for v in vals),'source':str(RESID.relative_to(ROOT))})
summary_data={'total_runs':52,'manifest_and_result_identity_matches':True,'binary_groups':[{'sha256':s,'runs':n,'groups':dict(Counter(r['group'] for r in records if r['binary_sha256_S1']==s))} for s,n in group_counts.items()],'current_candidate_matching_runs':sum(r['candidate_matches_record'] for r in records),'missing_fields_by_name':{k:sum(not r['source_build_fields_present'][k] for r in records) for k in ['source_sha256','generated_source_sha256','openlb_commit','compiler','compile_flags']},'main_role_by_hash':[{'role':role,'sha256':s,'direction_runs':n} for (role,s),n in cross.items() if role!='not_main'],'main_geometry_pairs':pair_rows,'stored_residual_summary':summary,'interpretation':'Hash identity and existing-data aggregation only. No source-binding proof, model refit or numerical acceptance.'}
(OUT/'evidence/existing_run_ledger.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
(OUT/'evidence/existing_data_summary.json').write_text(json.dumps(summary_data,ensure_ascii=False,indent=2)+'\n')
with (OUT/'evidence/main_role_binary_matrix.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['role','h_nm','d_nm','direction','binary_sha256','run_id','manifest_path'])
 for r in main:w.writerow([r['data_role_current_script'],r['h_nm'],r['d_nm'],r['direction'],r['binary_sha256_S1'],r['run_id'],r['manifest_path']])
print(json.dumps({k:summary_data[k] for k in ['total_runs','binary_groups','current_candidate_matching_runs','missing_fields_by_name','main_role_by_hash','stored_residual_summary']},ensure_ascii=False,indent=2))
