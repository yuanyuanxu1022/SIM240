from pathlib import Path
import os,csv,hashlib,json,shutil,subprocess
P=Path('/home/dell/yuanyuanxu/SIM240');W=P.parent/'SIM240_代码图片数据_20261022';O=P/'docs/reports/shared_workspace_check_20261022'
rows=list(csv.DictReader((W/'文件清单.csv').open(encoding='utf-8-sig')));M={r['原项目路径']:r['本文件夹路径'] for r in rows};added=[];excluded=[];coverage=[]
roots=['figures/paper','figures/paraview/D2_h75_d100_dx5_PT_publication_20261017_v1','figures/paraview/D2_publication_layout_20261017_v1','CASE/D_series/D2_groove_error_map','CASE/D_series/D3_oblique_groove_tensor_check','CASE/D_series/D3_squeeze_error_propagation','CASE/00_validation/G1_Poiseuille_Bouzidi_Validation','CASE/03_grid_convergence/G2_EX240_grid_convergence','CASE/03_grid_convergence/G4_EX240_period_convergence','CASE/03_grid_convergence/G2_EX240_fine_T_statfix_C_v1','CASE/03_grid_convergence/G2_EX240_fine_T_mass_diagnostic_v1','CASE/03_grid_convergence/G2_EX240_fine_T_mass_diagnostic_v2','CASE/04_parameter_study/G3_EX240_height_sweep','analysis','transport_database','docs/ex240']
auditroots=['Methods_support_audit_20261022','Methods_and_Section4_review_20261022','SIM240_independent_audit_20261018','SIM240_single_phase_audit_20261018','reviewer_numerics_20261018_v1','Chapter5_mechanism_audit_20261018','paraview_dissipation_state_audit_20261017']
roots += ['docs/reports/'+x for x in auditroots]
codeext={'.py','.sh','.cpp','.cc','.cxx','.c','.h','.hh','.hpp','.hxx','.ipynb','.pvsm','.mk'}
imageext={'.png','.pdf','.svg','.jpg','.jpeg','.tiff','.tif','.eps'}
skipdirs={'.git','__pycache__','.venv','venv','tmp','build','.cache'}
skipsuffix={'.o','.d','.pyc','.a','.so','.bak'}
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def add(p,key,target):
 if key in M:return
 q=W/target
 if q.exists():raise RuntimeError('位置冲突 '+str(target))
 q.parent.mkdir(parents=True,exist_ok=True);h=digest(p);shutil.copy2(p,q)
 assert digest(q)==h and digest(p)==h
 r={'原项目路径':key,'本文件夹路径':str(target),'字节数':str(q.stat().st_size),'SHA256':h};rows.append(r);M[key]=str(target);added.append(r)
def classification(rel):
 p=Path(rel);parts=p.parts
 if rel.startswith('CASE/'):
  tail=Path(*parts[2:])
  if p.suffix in codeext or p.name.startswith('Makefile'):return Path('01_代码/计算与分析')/tail
  if p.suffix in imageext:return Path('02_图片/03_附加结果与历史验证')/tail
  if p.suffix=='.md':return Path('01_代码/00_技术说明')/p
  return Path('03_数据/计算结果')/tail
 if rel.startswith('figures/paper/'):
  if p.suffix in codeext:return Path('01_代码/图片生成')/p.name
  return Path('02_图片/04_历史图与说明')/p.name
 if rel.startswith('figures/paraview/'):
  tail=Path(*parts[2:])
  if p.suffix in codeext:return Path('01_代码/流场出图')/tail
  if p.suffix in imageext:return Path('02_图片/02_可选流场图')/tail
  return Path('03_数据/流场绘图数据')/tail
 if rel.startswith('analysis/'):
  tail=Path(*parts[1:])
  if p.suffix in codeext:return Path('01_代码/其他后处理')/tail
  if p.suffix in imageext:return Path('02_图片/05_辅助分析图片')/tail
  if p.suffix=='.md':return Path('01_代码/00_技术说明')/p
  return Path('03_数据/其他后处理')/tail
 if rel.startswith('docs/ex240/'):return Path('04_几何')/p.name
 if rel.startswith('transport_database/'):return Path('03_数据/输运汇总')/p.name
 if rel.startswith('docs/reports/'):
  tail=Path(*parts[2:])
  if p.suffix in codeext:return Path('01_代码/科学核对')/tail
  if p.suffix in imageext:return Path('02_图片/06_技术检查图片')/tail
  return Path('03_数据/科学核对记录')/tail
 raise ValueError(rel)
for root in roots:
 assert (P/root).exists(),root
 num=0
 for here,dirs,files in os.walk(P/root,followlinks=False):
  dirs[:]=[d for d in dirs if d not in skipdirs and not (Path(here)/d).is_symlink()]
  for name in files:
   p=Path(here)/name;rel=str(p.relative_to(P));why=None
   if p.is_symlink():why='外部/符号链接不直接复制'
   elif p.suffix in skipsuffix or '.bak_' in name:why='编译产物或临时备份'
   elif root.startswith('docs/reports/') and p.suffix not in codeext|imageext|{'.csv','.json','.txt'}:why='非代码/数据/图片，不纳入本次材料'
   elif root.startswith('docs/reports/') and p.name.startswith(('patir','manuscript')):why='外部文献页面或文字快照，不作为计算材料'
   if why:excluded.append({'path':rel,'reason':why});continue
   with p.open('rb') as f:magic=f.read(4)
   if magic==b'\x7fELF':excluded.append({'path':rel,'reason':'本机二进制程序'});continue
   add(p,rel,classification(rel));num+=1
 coverage.append({'root':root,'eligible_files':num,'included_files':sum(k.startswith(root+'/') for k in M)})
# Additional visualization sources and artifacts directly related to this project stage, no presentation documents.
for root in ['docs/reports/第一篇进展组会汇报_20261017','docs/reports/方法与流场确认_导师版_20261022/assets']:
 for p in (P/root).rglob('*'):
  if not p.is_file() or p.is_symlink():continue
  if any(d in skipdirs for d in p.relative_to(P/root).parts):continue
  if p.suffix in imageext or p.suffix in {'.csv','.json'} or (p.suffix=='.py' and p.name.startswith('make_')):
   rel=str(p.relative_to(P));tail=Path(*p.relative_to(P).parts[2:])
   target=(Path('01_代码/补充图片生成') if p.suffix=='.py' else Path('02_图片/07_补充图片') if p.suffix in imageext else Path('03_数据/补充图数据'))/tail
   add(p,rel,target)
for name in ['Methods_followup_relstd_20261022.json','D2_readiness_audit_20261016.json']:
 p=P/'docs/reports'/name
 if p.is_file():add(p,str(p.relative_to(P)),Path('03_数据/科学核对记录')/name)
# Current dependency snapshot, kept distinct from historical case provenance.
lib=Path('/home/dell/openlb');libdest=Path('01_代码/依赖/openlb')
libroots=['src','external','config','LICENSE','AUTHORS.txt','CITATION.cff','CONTRIBUTORS.txt','Makefile','README.md','config.mk','config.git.mk','default.mk','default.single.mk','default.mixed.mk','rules.mk']
for rel in libroots:
 start=lib/rel
 if not start.exists():continue
 candidates=[start] if start.is_file() else start.rglob('*')
 for p in candidates:
  if not p.is_file() or p.is_symlink():continue
  if any(d in skipdirs|{'lib'} for d in p.relative_to(lib).parts[:-1]) or p.suffix in skipsuffix:continue
  with p.open('rb') as f:magic=f.read(4)
  if magic==b'\x7fELF':continue
  add(p,str(p),libdest/p.relative_to(lib))
with (W/'文件清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
meta={'snapshot':'current_dependency_only','openlb_head':subprocess.check_output(['git','-C',str(lib),'rev-parse','HEAD'],text=True).strip(),'tracked_dirty':subprocess.check_output(['git','-C',str(lib),'status','--porcelain','--untracked-files=no'],text=True).splitlines(),'historical_run_version_proven':False,'dependency_license':'01_代码/依赖/openlb/LICENSE'}
(W/'01_代码/依赖/依赖来源.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
(O/'完整范围补齐记录.json').write_text(json.dumps({'roots':coverage,'new_files':added,'excluded_files':excluded,'total_source_files':len(rows),'total_source_bytes':sum(int(r['字节数']) for r in rows)},ensure_ascii=False,indent=2))
print(json.dumps({'新增来源文件':len(added),'总来源文件':len(rows),'总字节数':sum(int(r['字节数']) for r in rows),'依赖提交':meta['openlb_head']},ensure_ascii=False))
