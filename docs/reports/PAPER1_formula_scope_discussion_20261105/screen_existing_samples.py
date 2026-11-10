from pathlib import Path
import csv,json,math,hashlib
B=Path(__file__).resolve().parent
source=B.parent/'PAPER1_claim_evidence_review_20261105/recomputed_36_points.csv'
before=hashlib.sha256(source.read_bytes()).hexdigest()
rows=list(csv.DictReader(source.open(newline='')))
assert len(rows)==36
seen=set();pairs={}
for r in rows:
 r['h_nm']=int(r['h_nm']);r['d_nm']=int(r['d_nm'])
 for k in ['K_ref_m3','K_model_m3','F_V2_published','E_percent','V2_residual_percent']:r[k]=float(r[k]);assert math.isfinite(r[k])
 key=(r['h_nm'],r['d_nm'],r['direction']);assert key not in seen;seen.add(key)
 assert '_dx5_' in r['run_id']
 assert abs(100*(r['K_model_m3']/r['K_ref_m3']-1)-r['E_percent'])<1e-10
 assert abs(100*(r['F_V2_published']*r['K_model_m3']/r['K_ref_m3']-1)-r['V2_residual_percent'])<1e-10
 pairs.setdefault(key[:2],[]).append(r)
assert len(pairs)==18 and all({r['direction'] for r in p}=={'parallel','perpendicular'} for p in pairs.values())
thresholds=[5,10,20];summary={'scope':'retrospective screening of saved dx5 samples; no prediction, continuous-domain guarantee, gate acceptance or solver run','thresholds_percent':thresholds,'threshold_status':'illustrative discussion levels, not adopted acceptance criteria','geometry_count':18,'direction_count':36,'source_sha256':before,'models':{}}
for name,col in [('original','E_percent'),('V2','V2_residual_percent')]:
 m={'screening':[],'maximum_abs_discrepancy_percent':{}}
 for d in ['parallel','perpendicular']:m['maximum_abs_discrepancy_percent'][d]=max(abs(r[col]) for r in rows if r['direction']==d)
 for eps in thresholds:
  joint=[{'h_nm':h,'d_nm':d} for (h,d),rs in sorted(pairs.items()) if all(abs(r[col])<=eps for r in rs)]
  m['screening'].append({'illustrative_tolerance_percent':eps,'parallel_pass_count':sum(abs(r[col])<=eps for r in rows if r['direction']=='parallel'),'perpendicular_pass_count':sum(abs(r[col])<=eps for r in rows if r['direction']=='perpendicular'),'both_direction_geometry_count':len(joint),'both_direction_geometries':joint})
 summary['models'][name]=m
summary['V2_perpendicular_h50_75_125']={'sample_count':15,'max_abs_percent':max(abs(r['V2_residual_percent']) for r in rows if r['direction']=='perpendicular' and r['h_nm'] in [50,75,125]),'depths_nm':[25,50,75,100,120],'continuous_domain_validated':False}
(B/'screening_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
with (B/'screened_36_points.csv').open('w',newline='') as f:
 names=list(rows[0])+[f'{model}_within_{eps}pct' for model in ['original','V2'] for eps in thresholds];w=csv.DictWriter(f,fieldnames=names);w.writeheader()
 for r in rows:
  out=dict(r)
  for model,col in [('original','E_percent'),('V2','V2_residual_percent')]:
   for eps in thresholds:out[f'{model}_within_{eps}pct']=abs(r[col])<=eps
  w.writerow(out)
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
print(json.dumps({name:[(x['illustrative_tolerance_percent'],x['parallel_pass_count'],x['perpendicular_pass_count'],x['both_direction_geometry_count']) for x in m['screening']] for name,m in summary['models'].items()},ensure_ascii=False))
