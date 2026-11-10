from pathlib import Path
import csv,json,hashlib,math,re,collections,xml.etree.ElementTree as ET
P=Path('/home/dell/yuanyuanxu/SIM240'); W=P.parent/'SIM240_代码图片数据_20261022'; O=P/'docs/reports/shared_workspace_check_20261022'
rows=list(csv.DictReader((W/'文件清单.csv').open(encoding='utf-8-sig')))
M={r['原项目路径']:r['本文件夹路径'] for r in rows}
REV={str((W/r['本文件夹路径']).resolve()):r['原项目路径'] for r in rows}
def hashfile(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def kv(p):
 d={}
 if p.is_file():
  for line in p.read_text(errors='replace').splitlines():
   if '=' in line:
    k,v=line.split('=',1);d[k.strip()]=v.strip()
 return d
def wp(rel):return W/M[rel] if rel in M else None
hash_bad=[];source_drift=[];missing=[]
for r in rows:
 f=W/r['本文件夹路径']
 if not f.is_file():missing.append(r);continue
 if hashfile(f)!=r['SHA256']:hash_bad.append(r['本文件夹路径'])
 sf=P/r['原项目路径']
 if not sf.is_file() or hashfile(sf)!=r['SHA256']:source_drift.append(r['原项目路径'])
R={'workspace':str(W),'manifest_files':len(rows),'manifest_bytes':sum(int(r['字节数']) for r in rows),'missing_manifest_files':missing,'hash_mismatch':hash_bad,'source_snapshot_drift':source_drift,'git_folder_present':(W/'.git').exists(),'root_files':[p.name for p in W.iterdir() if p.is_file()]}
index=list(csv.DictReader((W/'03_数据/00_数据索引/52项运行_当前位置.csv').open(encoding='utf-8-sig')))
runrows=[];groups=collections.Counter();meta=collections.Counter();diag_bad=[]
shared=wp('CASE/D_series/D2_groove_error_map/results/dx25_refine4_run_20261018.log')
sharedtext=shared.read_text() if shared else ''
for r in index:
 rel=r['rel_path'];res=wp(rel+'/steady/result.txt');d=kv(res);mf=kv(wp(rel+'/steady/run_manifest.txt'))
 artifact={n:bool(wp(rel+'/steady/'+n) and wp(rel+'/steady/'+n).is_file()) for n in ['result.txt','diagnostics.csv','run_manifest.txt','exit_code.txt','boundary_audit.txt','run.log']}
 prereq={n:bool(wp(rel+'/precheck/'+n) and wp(rel+'/precheck/'+n).is_file()) for n in ['result.txt','boundary_audit.txt','run_manifest.txt','exit_code.txt','run.log']}
 dc=wp(rel+'/steady/diagnostics.csv');count=0;last=None;nonfinite=0;sequence=True
 with dc.open() as f:
  for rr in csv.DictReader(f):
   step=int(rr['step'])
   if last is not None and step!=last+1:sequence=False
   last=step;count+=1
   for value in rr.values():
    try:
     if not math.isfinite(float(value)):nonfinite+=1
    except (ValueError,TypeError):pass
 diag={'rows':count,'last_step':last,'result_steps':int(d['steps_completed']),'continuous':sequence,'nonfinite_numeric_cells':nonfinite,'end_matches_result':last==int(d['steps_completed'])}
 if not sequence or nonfinite or not diag['end_matches_result']:diag_bad.append(r['run_id'])
 case=mf.get('case_id','')
 shared_matches=(f'--- {case} precheck exit=0' in sharedtext and f'--- {case} steady exit=0' in sharedtext)
 if 'oblique' in rel:group='斜向6项'
 elif float(r['dx_nm'])==2.5:group='加密8项'
 elif r['run_id'].startswith('mu15'):group='黏度2项'
 else:group='主地图36项'
 groups[group]+=1
 for key in ['binary_sha256','source_sha256','generated_source_sha256','openlb_commit','compiler','compile_flags']:meta[key]+=int(key in mf)
 exittext=wp(rel+'/steady/exit_code.txt').read_text().strip()
 runrows.append({'run_id':r['run_id'],'group':group,'result_path':str(res.relative_to(W)),'artifacts':artifact,'precheck':prereq,'diagnostics':diag,'independent_exit':exittext,'result_self_PASS':d.get('PASS'),'shared_log_covers_missing_individual':not artifact['run.log'] and shared_matches,'manifest_case_id':case})
R['runs52']={'groups':dict(groups),'artifact_counts':{k:sum(r['artifacts'][k] for r in runrows) for k in runrows[0]['artifacts']},'precheck_counts':{k:sum(r['precheck'][k] for r in runrows) for k in runrows[0]['precheck']},'diagnostic_rows':sum(r['diagnostics']['rows'] for r in runrows),'diagnostics_issues':diag_bad,'shared_log_missing_run_covers':sum(r['shared_log_covers_missing_individual'] for r in runrows),'manifest_field_counts':dict(meta),'exit_counts':dict(collections.Counter(r['independent_exit'] for r in runrows))}
(O/'52项文件核对.json').write_text(json.dumps(runrows,ensure_ascii=False,indent=2))
# Four summary tables against original per-run results; normalized data are derived, originals untouched.
points=[]
for name in ['summary.csv','d75_summary.csv','h25_summary.csv','d120_summary.csv']:
 f=wp('CASE/D_series/D2_groove_error_map/results/'+name)
 for rr in csv.DictReader(f.open()):
  if float(rr['dx_nm'])!=5:continue
  direction=rr.get('direction') or rr['case_id'].split('-')[1]
  points.append({'h_nm':int(rr['h_nm']),'d_nm':int(rr['d_nm']),'direction':direction,'K_m3':float(rr['Keff_m3']),'summary_file':str(f.relative_to(W))})
bykey={}
for r in runrows:
 if r['group']=='主地图36项':
  d=kv(W/r['result_path']);bykey[(round(float(d['mesa_gap_m'])*1e9),round(float(d['groove_depth_m'])*1e9),'P' if d['direction']=='parallel' else 'T')]=r
for pt in points:
 h,d,dr=pt['h_nm'],pt['d_nm'],pt['direction'];raw=bykey[(h,d,dr)];val=float(kv(W/raw['result_path'])['Keff_m3']);pt['result_path']=raw['result_path'];pt['relative_summary_difference']=abs(pt['K_m3']/val-1)
 model=((h**3+(h+d)**3)/24 if dr=='P' else 1/(6*(h**-3+(h+d)**-3)))*1e-27
 pt['local_model_K_m3']=model;pt['model_error_percent']=(model/val-1)*100
R['summary36']={'rows':len(points),'unique_keys':len({(x['h_nm'],x['d_nm'],x['direction']) for x in points}),'max_summary_relative_difference':max(x['relative_summary_difference'] for x in points)}
R['transverse_depth_variation_by_h']={str(h):{'depths':[x['d_nm'] for x in points if x['h_nm']==h and x['direction']=='T'],'max_over_min_minus_one_percent':100*(max(x['K_m3'] for x in points if x['h_nm']==h and x['direction']=='T')/min(x['K_m3'] for x in points if x['h_nm']==h and x['direction']=='T')-1)} for h in [25,50,75,125]}
with (O/'36项汇总与原始值对应.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(points[0]));w.writeheader();w.writerows(points)
# Dependencies referenced by VTK index files.
links=[];xmlfail=[]
for r in rows:
 f=W/r['本文件夹路径']
 if f.suffix.lower() not in {'.pvd','.vtm','.pvtu','.pvti'}:continue
 try:tree=ET.parse(f)
 except ET.ParseError:xmlfail.append(str(f.relative_to(W)));continue
 for el in tree.iter():
  for key in ['file','File','Source']:
   if key not in el.attrib:continue
   target=(f.parent/el.attrib[key]).resolve()
   if not target.is_file():
    source=(P/r['原项目路径']).parent/el.attrib[key]
    links.append({'index':str(f.relative_to(W)),'reference':el.attrib[key],'source_target_exists':source.is_file()})
R['vtk_dependencies']={'unresolved':len(links),'xml_parse_failures':xmlfail,'examples':links[:12]}
(O/'VTK引用缺口.json').write_text(json.dumps(links,ensure_ascii=False,indent=2))
# Count portability blockers without executing code.
absfiles=[]
for f in (W/'01_代码').rglob('*'):
 if not f.is_file():continue
 t=f.read_text(errors='replace')
 if '/home/dell/' in t:absfiles.append(str(f.relative_to(W)))
R['code']={'files':sum(p.is_file() for p in (W/'01_代码').rglob('*')),'files_with_home_dell_paths':len(absfiles),'absolute_path_files':absfiles,'full_openlb_dependency_included':False,'build_or_execution_performed':False}
# Frozen instructions excluded by the previous category filter.
prev=list(csv.DictReader((P.parent/'第一篇论文_整理版_20261022/99_文件索引/全部文件对应表.csv').open(encoding='utf-8-sig')))
protocols=[r['原项目路径'] for r in prev if r['原项目路径'].startswith('CASE/') and re.search('protocol|run_config|readme',Path(r['原项目路径']).name,re.I) and r['原项目路径'] not in M]
R['excluded_case_instructions']=protocols
# Required grid and periodic reference cases: count actual raw records, not duplicated archives.
gridprefix='CASE/03_grid_convergence/G2_EX240_grid_convergence/archive/g2_grid_20260917T165045+0800/runs/'
grids=[r for r in rows if r['原项目路径'].startswith(gridprefix) and r['原项目路径'].endswith('/steady/result.txt')]
R['historical_grid']=[{'path':r['本文件夹路径'],'PASS':kv(W/r['本文件夹路径']).get('PASS'),'exit_code':kv(W/r['本文件夹路径']).get('exit_code')} for r in grids]
batches=['g4_period_nx2_fields_v1_20261012T001316+0800','g4_period_nx4_fields_v1_20261012T105719+0800','g4_period_nx8_fields_v1_20261012T163341+0800']
R['periodic_reference']={batch:sum(batch in r['原项目路径'] and r['原项目路径'].endswith('/steady/result.txt') for r in rows) for batch in batches}
R['limitations']=['文件核对不等于物理验收','未重新运行求解器或优化器','未确认老师已收到或具有共享访问权限','代码与数据分类分离，未适配执行路径','历史源码与构建绑定尚未闭合']
(O/'check_results.json').write_text(json.dumps(R,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in R.items() if k not in ['code','historical_grid','excluded_case_instructions']},ensure_ascii=False,indent=2))
print('CODE_PATH_BLOCKERS',len(absfiles));print('EXCLUDED_INSTRUCTION_COUNT',len(protocols));print('EXCLUDED_INSTRUCTION_EXAMPLES',protocols[:8]);print('GRID_COUNT',len(grids))
