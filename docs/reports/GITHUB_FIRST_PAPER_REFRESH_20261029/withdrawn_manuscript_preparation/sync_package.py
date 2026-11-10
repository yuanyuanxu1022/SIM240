"""Synchronize approved first-paper sharing scope; no scientific code execution."""
from pathlib import Path
import csv,hashlib,json,os,re,shutil,subprocess
ROOT=Path('/home/dell/yuanyuanxu/SIM240')
REPO=ROOT.parent/'SIM240_code_figures_data_review_20261026'
OUT=ROOT/'docs/reports/GITHUB_FIRST_PAPER_REFRESH_20261029'
OLD=ROOT/'docs/reports/GITHUB_FIRST_PAPER_COMPLETE_20261028'
PREFIX=Path('05_第一篇文章'); MIRROR=PREFIX/'项目文件'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert subprocess.check_output(['git','-C',str(REPO),'status','--porcelain'])==b''
assert subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD']).decode().strip()=='025eac0c7f752c4a023ebc64db0950fa6b7c98b5'
old=json.loads((OLD/'source_files.json').read_text());reused=json.loads((OLD/'reused_sources.json').read_text())
selected={r['source']:r for r in old}
extras=['docs/reports/SIM240_First_Paper_English_20261028.md','docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md']
extras += ['output/pdf/'+n for n in ['SIM240_First_Paper_ZH_20261028.pdf','SIM240_First_Paper_EN_20261028.pdf','SIM240_Supplement_ZH_20261028.pdf','SIM240_Supplement_EN_20261028.pdf']]
for folder,names in {
 'Paper_bilingual_layout_20261028':['README.md','CHINESE_READING.md','author_scope.json','translation_map.json','supplement_translation_map.json','verification.json','visual_review.json','pdf_text_checks.json','local_link_checks.json','paper_template.typ','layout.lua','build_documents.py','verify_documents.py'],
 'Appendix_E_final_review_20261028':['REPORT.md','ASTRA_REVIEW.md','review_scope.json','review_receipt.json','record_binding_checks.json','verification.json']
}.items(): extras += ['docs/reports/'+folder+'/'+n for n in names]
for name in extras:
 p=ROOT/name
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<25*1024*1024
 assert p.read_bytes()[:4]!=b'\x7fELF'
 selected[str(p)]={'source':str(p),'source_relative':name,'target':str(MIRROR/name),'kind':'current_bilingual_pdf_or_review_evidence'}
changed=[]
for r in selected.values():
 p=Path(r['source']);r.update(bytes=p.stat().st_size,sha256=sha(p));q=REPO/r['target']
 if not q.exists() or sha(q)!=r['sha256']:
  changed.append(r);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 assert sha(q)==r['sha256']
# Verify all reused sources against both live source and indexed Git blob identity.
tree=subprocess.check_output(['git','-C',str(REPO),'ls-tree','-r','-z','HEAD'])
blobs={}
for item in tree.rstrip(b'\0').split(b'\0'):
 meta,path=item.split(b'\t',1);blobs[path.decode()]=meta.split()[2].decode()
for r in reused:
 p=Path(r['source']);b=p.read_bytes();assert sha(p)==r['sha256']
 assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==blobs[r['target']]
lookup={r['source']:r['target'] for r in reused};lookup.update({s:r['target'] for s,r in selected.items()})
# Read-only mapping from pre-existing index covers external OpenLB excerpts.
with (REPO/'文件清单.csv').open(encoding='utf-8-sig') as f: index=list(csv.DictReader(f))
for r in index:
 p=Path(r['原项目路径']);p=p if p.is_absolute() else ROOT/p
 if str(p) not in lookup and r['本文件夹路径'] in blobs and p.is_file() and sha(p)==r['SHA256']:lookup[str(p)]=r['本文件夹路径']
unresolved=[];views=[]
for src,target in [
 ('docs/reports/SIM240_中文稿_导师审阅版_20261022.md','当前正文_阅读版.md'),
 ('docs/reports/SIM240_First_Paper_English_20261028.md','Current_Manuscript_EN.md'),
 ('docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md','方法补充_阅读版.md'),
 ('docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md','Supplement_EN.md')]:
 source=ROOT/src;dest=REPO/PREFIX/target
 def replace(m):
  ref=m.group(2)
  if ref.startswith(('http:','https:','mailto:','#')):return m.group(0)
  name,sep,anchor=ref.partition('#');name=re.sub(r':\d+$','',name)
  p=Path(name);p=p if p.is_absolute() else (source.parent/p).resolve()
  mapped=lookup.get(str(p))
  if not mapped:
   unresolved.append({'source':src,'link':ref});mapped=str(PREFIX/'材料覆盖与缺口.md');sep=''
  return '['+m.group(1)+']('+os.path.relpath(REPO/mapped,dest.parent)+('#'+anchor if sep else '')+')'
 original=source.read_text();view=re.sub(r'\[([^\]]*)\]\(([^)]+)\)',replace,original)
 # A link-only transformation must preserve all mathematical text.
 math=lambda s:re.findall(r'\$\$[\s\S]*?\$\$|(?<!\$)\$(?!\$)[^\n$]*?\$',s)
 assert math(original)==math(view)
 dest.write_text(view);views.append({'source':src,'target':str(dest.relative_to(REPO)),'sha256':sha(dest)})
# Refresh exact per-target entries; older dated snapshots remain historical.
for r in selected.values():
 row={'原项目路径':r['source_relative'],'本文件夹路径':r['target'],'字节数':str(r['bytes']),'SHA256':r['sha256']}
 index=[x for x in index if x['本文件夹路径']!=r['target']];index.append(row)
with (REPO/'文件清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['原项目路径','本文件夹路径','字节数','SHA256']);w.writeheader();w.writerows(index)
with (REPO/PREFIX/'文件映射.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['来源路径','仓库路径','字节数','SHA256','本轮方式']);w.writeheader()
 for r in list(selected.values())+reused:w.writerow({'来源路径':r['source'],'仓库路径':r['target'],'字节数':r['bytes'],'SHA256':r['sha256'],'本轮方式':'当前原字节副本' if r['source'] in selected else '复用既有来源'})
write(OUT/'source_files.json',list(selected.values()));write(OUT/'changed_source_copies.json',changed);write(OUT/'reading_copies.json',views);write(OUT/'unresolved_links.json',unresolved)
print(json.dumps({'source_copies_verified':len(selected),'reused_sources_verified':len(reused),'changed_source_copies':len(changed),'reading_copies':len(views),'unresolved_links':unresolved},ensure_ascii=False))
