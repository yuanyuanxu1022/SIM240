from pathlib import Path
from collections import Counter
import json,hashlib,csv,re,subprocess
ROOT=Path(__file__).resolve().parents[3];B=Path(__file__).resolve().parent;R=ROOT.parent/'SIM240_code_figures_data_review_20261026';S=B/'staging'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources=json.loads((B/'source_files.json').read_text());reuse=json.loads((B/'reused_sources.json').read_text());views=json.loads((B/'reading_copies.json').read_text())
for x in sources:assert sha(x['source'])==x['sha256']==sha(S/x['target']),x['source']
# Verify each source against the blob ID recorded in the committed Git tree.
# Git blob IDs hash the object type, byte length and complete source bytes; this
# avoids downloading already committed large data through a partial clone.
entries=subprocess.run(['git','-C',str(R),'ls-tree','-r','-z','HEAD'],capture_output=True,check=True).stdout.split(b'\0')
tree={}
for entry in entries:
 if not entry:continue
 meta,name=entry.split(b'\t',1);mode,typ,oid=meta.decode().split();tree[name.decode()]={'type':typ,'oid':oid}
checks=[]
for x in reuse:
 entry=tree[x['target']];assert entry['type']=='blob'
 source=Path(x['source']);size=source.stat().st_size;git_hash=hashlib.sha1();git_hash.update(('blob '+str(size)+'\0').encode());raw_hash=hashlib.sha256()
 with source.open('rb') as f:
  while True:
   buf=f.read(1024*1024)
   if not buf:break
   git_hash.update(buf);raw_hash.update(buf)
 assert git_hash.hexdigest()==entry['oid'],(x['source'],'source vs recorded Git blob mismatch')
 assert raw_hash.hexdigest()==x['sha256']
 checks.append({'target':x['target'],'git_blob':entry['oid'],'sha256':raw_hash.hexdigest(),'bytes':size,'method':'Source bytes match committed Git blob ID and source SHA256'})
(B/'reused_blob_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
maths=lambda t:re.findall(r'\$\$[\s\S]*?\$\$|(?<!\$)\$[^$\n]*\$(?!\$)',t)
view_checks=[]
for x in views:
 a=Path(x['source']).read_text();b=(S/x['target']).read_text();assert maths(a)==maths(b)
 if '当前正文' in x['target']:assert a.split('## 附录 E',1)[1]==b.split('## 附录 E',1)[1]
 view_checks.append({'target':x['target'],'math_fragments':len(maths(a)),'math_unchanged':True})
tracked=set(subprocess.run(['git','-C',str(R),'ls-files','-z'],capture_output=True,check=True).stdout.decode().rstrip('\0').split('\0'))
newpaths={str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()};available=tracked|newpaths
links=[]
# The exact archived source documents retain their local links; check the user-facing entry documents.
front=[p for p in S.glob('*.md')]+[p for p in (S/'05_第一篇文章').glob('*.md')]
for p in front:
 for ref in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if ref.startswith(('http://','https://','#','mailto:')):continue
  base,_,anchor=ref.partition('#');target=(R/p.relative_to(S).parent/base).resolve()
  assert target.is_relative_to(R),ref
  rel=str(target.relative_to(R));exists=rel in available or any(t.startswith(rel+'/') for t in available);assert exists,(p,ref)
  links.append({'from':str(p.relative_to(S)),'ref':ref,'resolved':rel})
patterns=[r'-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----',r'gh[pousr]_[A-Za-z0-9]{30,}',r'github_pat_[A-Za-z0-9_]{30,}',r'AKIA[0-9A-Z]{16}',r'sk-(?:proj-)?[A-Za-z0-9_-]{30,}']
sensitive=[];json_count=0
for rel in sorted(newpaths):
 p=S/rel;assert not p.is_symlink();assert p.stat().st_size<25*1024*1024
 assert p.read_bytes()[:4]!=b'\x7fELF'
 if p.suffix.lower()=='.json':json.loads(p.read_text());json_count+=1
 if p.suffix.lower() in ['.md','.txt','.json','.csv','.py','.sh','.cpp','.h','.diff']:
  text=p.read_text(encoding='utf-8',errors='replace')
  for pat in patterns:
   if re.search(pat,text):sensitive.append({'path':rel,'pattern':pat})
assert not sensitive,sensitive
with (S/'文件清单.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
assert len(rows)==8836
assert len({r['本文件夹路径'] for r in rows})==len(rows)
# Validate project-owned figures only; third-party page renders/fulltexts never entered the selected paths.
for x in sources:
 if Path(x['source']).suffix.lower() in ['.pdf','.png','.svg']:
  assert x['source_relative'].startswith(('figures/paper/','CASE/D_series/D2_groove_error_map/results/analysis/'))
manifest={rel:{'bytes':(S/rel).stat().st_size,'sha256':sha(S/rel)} for rel in sorted(newpaths)}
(B/'staged_files.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
report={'all_checks_passed':True,'source_copies_checked':len(sources),'reused_committed_blobs_checked':len(checks),'reused_bytes_checked':sum(x['bytes'] for x in checks),'reading_copy_checks':view_checks,'front_document_links_checked':len(links),'front_links':links,'parseable_json_files':json_count,'credential_pattern_hits':sensitive,'new_paths':len(newpaths),'source_inventory_rows':len(rows),'source_files_unchanged':True,'source_document_science_unchanged':True,'scientific_runs_executed':False,'scope':'Selected source bytes, reused Git objects and front links only; no all-history, numerical or journal acceptance'}
(B/'precommit_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['all_checks_passed','source_copies_checked','reused_committed_blobs_checked','reused_bytes_checked','front_document_links_checked','parseable_json_files','new_paths','source_inventory_rows']},ensure_ascii=False))
