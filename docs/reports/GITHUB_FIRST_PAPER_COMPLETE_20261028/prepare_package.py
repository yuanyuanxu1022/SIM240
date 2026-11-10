"""Prepare current first-paper sharing files; does not execute scientific code."""
from pathlib import Path
from collections import defaultdict,Counter
import csv,json,hashlib,shutil,re,os,subprocess
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
REPO=ROOT.parent/'SIM240_code_figures_data_review_20261026'
PREFIX=Path('05_第一篇文章')
STAGE=OUT/'staging'
MIRROR=PREFIX/'项目文件'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
tracked=set(subprocess.run(['git','-C',str(REPO),'ls-files','-z'],capture_output=True,check=True).stdout.decode().rstrip('\0').split('\0'))
with (REPO/'文件清单.csv').open(encoding='utf-8-sig') as f:oldrows=list(csv.DictReader(f))
oldmap=defaultdict(list)
for r in oldrows:
 p=Path(r['原项目路径']);p=p if p.is_absolute() else ROOT/p
 oldmap[str(p)].append(r)
selected={};excluded=[];reused={};digest_cache={}
def digest(p):
 s=str(p)
 if s not in digest_cache:digest_cache[s]=sha(p)
 return digest_cache[s]
def add(p,kind):
 p=Path(p);p=p if p.is_absolute() else ROOT/p
 assert p.is_relative_to(ROOT),p
 assert p.is_file() and not p.is_symlink(),p
 if any(x in p.parts for x in ['__pycache__','build','pages','before']) or p.suffix.lower() in ['.o','.d','.pyc','.deb']:
  raise ValueError(p)
 if p.read_bytes()[:4]==b'\x7fELF':raise ValueError('ELF rejected')
 assert p.stat().st_size<25*1024*1024,p
 target=MIRROR/p.relative_to(ROOT)
 selected[str(p)]={'source':str(p),'source_relative':str(p.relative_to(ROOT)),'target':str(target),'bytes':p.stat().st_size,'sha256':digest(p),'kind':kind}
def reuse_or_add(p,kind):
 p=Path(p);p=p if p.is_absolute() else ROOT/p
 if str(p) in selected:return selected[str(p)]['target']
 for r in oldmap.get(str(p),[]):
  if r['本文件夹路径'] in tracked and r['SHA256']==digest(p):
   reused[str(p)]={'source':str(p),'target':r['本文件夹路径'],'bytes':p.stat().st_size,'sha256':digest(p),'kind':kind}
   return r['本文件夹路径']
 add(p,kind);return selected[str(p)]['target']
main=ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
supp=ROOT/'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md'
add(main,'current_manuscript');add(ROOT/'docs/reports/SIM240_EJMB_英文整合工作稿_20261019.md','historical_english_not_synchronized')
for p in (ROOT/'docs/reports/SIM240_Supplementary_Methods_20261024').iterdir():
 if p.name in ['SUPPLEMENTARY_METHODS.md','README.md','SUPPLEMENT_NUMBER_MAP.csv','REVISION_NOTE.md','verification.json'] or p.name.startswith('Table_S') and p.suffix=='.csv':add(p,'supplement')
for p in (ROOT/'figures/paper').iterdir():
 if p.is_file() and p.suffix.lower() in ['.py','.md','.pdf','.png','.svg']:add(p,'paper_figures_and_scripts')
for case in ['D2_groove_error_map','D3_oblique_groove_tensor_check']:
 folder=ROOT/'CASE/D_series'/case
 for p in folder.glob('*.py'):add(p,'first_paper_analysis_code')
 for sub in ['src','scripts']:
  if (folder/sub).exists():
   for p in (folder/sub).rglob('*'):
    if p.is_file() and p.suffix.lower() in ['.cpp','.h','.py','.sh','.md']:add(p,'first_paper_source_or_script')
 for p in (folder/'results').glob('*.csv'):add(p,'first_paper_summary_data')
 if (folder/'results/analysis').exists():
  for p in (folder/'results/analysis').iterdir():
   if p.is_file() and p.suffix.lower() in ['.csv','.md','.json','.png','.txt']:add(p,'stored_analysis_output')
report_dirs=['Methods_support_audit_20261022','Methods_sources_data_audit_20261027','Primary_text_received_20261027','Bouzidi_P8_received_20261027','Dewangan2018_received_20261028','Download_new_sources_20261028','Primary_text_build_evidence_20261027','Historical_build_binding_recovery_20261028','Historical_build_adjudication_20261028','Historical_build_text_sync_20261028','GCI_author_sync_20261027','Paper_core_reference_final_review_20261027','Paper_text_figure_corrections_20261027','Paper_formal_sync_20261027','Current_gap_inventory_20261028']
for name in report_dirs:
 d=ROOT/'docs/reports'/name
 if not d.exists():continue
 for p in d.iterdir():
  if not p.is_file():continue
  bad=any(x in p.name.lower() for x in ['before','initial','git_status','state_changes','state_sync','state_verification','package_file_checks','output_manifest'])
  if p.suffix.lower() in ['.md','.json','.csv','.py','.diff'] and not bad and p.stat().st_size<600000:add(p,'selected_evidence_report')
 # Include the substantive machine-readable ledger, never PDF fulltexts/page images.
 if name=='Historical_build_adjudication_20261028':
  for p in (d/'evidence').iterdir():
   if p.suffix in ['.json','.csv']:add(p,'adjudication_evidence')
for name in ['Methods_followup_relstd_20261022.json','第一篇论文_方法与结果证据表_20261022.md','第一篇_run_id索引_20261022.csv']:
 p=ROOT/'docs/reports'/name
 if p.exists():add(p,'supporting_index')
for name in ['CASE/03_grid_convergence/G2_EX240_grid_convergence/STEP3_PROTOCOL.md','CASE/03_grid_convergence/G4_EX240_period_convergence/PERIOD_CONVERGENCE_PROTOCOL.md','docs/ex240/ex240_layout_report.md']:
 if (ROOT/name).exists():reuse_or_add(ROOT/name,'existing_protocol_or_geometry')
coverage=[]
for table in ['Table_S1_run_inventory.csv','Table_S3_periodic_checks.csv','Table_S4_grid_archive.csv']:
 with (ROOT/'docs/reports/SIM240_Supplementary_Methods_20261024'/table).open() as f:rows=list(csv.DictReader(f))
 for i,row in enumerate(rows,2):
  result=ROOT/row['result_path'];assert result.is_file()
  rec={'table':table,'table_line':i,'run_id':row.get('run_id') or row.get('case'),'recorded_PASS':row.get('recorded_PASS'),'independent_exit_code':row.get('independent_exit_code'),'artifacts':[]}
  runfiles=[result]
  for name in ['run_manifest.txt','exit_code.txt','run.log','diagnostics.csv']:
   p=result.parent/name
   if p.exists():runfiles.append(p)
  if row.get('log_path'):
   p=ROOT/row['log_path']
   if p.exists() and p not in runfiles:runfiles.append(p)
  for p in runfiles:
   if p.stat().st_size>2*1024*1024 and not oldmap.get(str(p)):
    excluded.append({'source':str(p),'reason':'Large diagnostic not already indexed in shared repository; kept local'});continue
   target=reuse_or_add(p,'run_artifact_'+table[:8]);rec['artifacts'].append({'source':str(p),'target':target,'sha256':digest(p),'bytes':p.stat().st_size})
  coverage.append(rec)
assert len(coverage)==79
# Source paths in links are resolved to exact new copies or verified prior source mappings.
def resolve_source(p):
 p=Path(p)
 if str(p) in selected:return selected[str(p)]['target']
 if str(p) in reused:return reused[str(p)]['target']
 for r in oldmap.get(str(p),[]):
  if r['本文件夹路径'] in tracked:
   # Do not silently use a stale copy for a live linked local source.
   if p.is_file() and r['SHA256']!=digest(p):continue
   reused[str(p)]={'source':str(p),'target':r['本文件夹路径'],'bytes':int(r['字节数']),'sha256':r['SHA256'],'kind':'linked_existing_source'}
   return r['本文件夹路径']
 return None
unresolved=[]
def portable_view(source,target):
 text=source.read_text()
 def replace(m):
  label,ref=m.group(1),m.group(2)
  if ref.startswith(('https://','http://','#','mailto:')):return m.group(0)
  name,sep,anchor=ref.partition('#');name=re.sub(r':\d+$','',name)
  src=Path(name) if Path(name).is_absolute() else (source.parent/name).resolve()
  dest=resolve_source(src)
  if not dest:
   unresolved.append({'document':str(source),'target':ref,'reason':'Local-only folder/artifact or excluded evidence; see coverage note'})
   dest=str(PREFIX/'材料覆盖与缺口.md');sep='';anchor=''
  rel=os.path.relpath(REPO/dest,REPO/target.parent)
  return '['+label+']('+rel+('#'+anchor if sep else '')+')'
 view=re.sub(r'\[([^\]]*)\]\(([^)]+)\)',replace,text)
 # Turn figure filenames in the reading copy into working links; scientific prose stays unchanged.
 for name in ['Fig1_device_and_unitcell.pdf','Fig4_K_and_anisotropy.pdf','Fig7_error_vs_gap.pdf','Fig8_error_map.pdf']:
  src=ROOT/'figures/paper'/name;dest=selected[str(src)]['target']
  view=view.replace('`figures/paper/'+name+'`','['+name+']('+os.path.relpath(REPO/dest,REPO/target.parent)+')')
 path=STAGE/target;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(view)
 return {'source':str(source),'target':str(target),'kind':'reading_copy_links_only','source_sha256':digest(source),'sha256':sha(path)}
views=[portable_view(main,PREFIX/'当前正文_阅读版.md'),portable_view(supp,PREFIX/'方法补充_阅读版.md')]
for rec in selected.values():
 p=STAGE/rec['target'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(rec['source'],p);assert sha(p)==rec['sha256']
(OUT/'source_files.json').write_text(json.dumps(list(selected.values()),ensure_ascii=False,indent=2)+'\n')
(OUT/'reused_sources.json').write_text(json.dumps(list(reused.values()),ensure_ascii=False,indent=2)+'\n')
(OUT/'run_coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
(OUT/'reading_copies.json').write_text(json.dumps(views,ensure_ascii=False,indent=2)+'\n')
(OUT/'unresolved_source_links.json').write_text(json.dumps(unresolved,ensure_ascii=False,indent=2)+'\n')
(OUT/'excluded.json').write_text(json.dumps(excluded,ensure_ascii=False,indent=2)+'\n')
summary={'new_source_copies':len(selected),'new_source_bytes':sum(r['bytes'] for r in selected.values()),'reused_indexed_sources':len(reused),'referenced_run_records':len(coverage),'unresolved_source_links':len(unresolved),'excluded_large_diagnostics':len(excluded),'source_kinds':dict(Counter(r['kind'] for r in selected.values()))}
(OUT/'package_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
