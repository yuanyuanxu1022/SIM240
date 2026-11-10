from pathlib import Path
import xml.etree.ElementTree as E,zipfile,shutil,re,posixpath,json,hashlib
B=Path(__file__).resolve().parent.parent
backup=B/'制作记录/删前两页前_21页备份'
backup.mkdir(exist_ok=True)
files=['PAPER1_导师汇报_20261105_下午修订版.pptx','PAPER1_导师汇报_20261105_下午修订版.pdf','下午汇报逐页讲稿.md','先读这里_下午汇报.md']
for f in files:
 if not (backup/f).exists():shutil.copy2(B/f,backup/f)
N={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
for k,v in N.items():E.register_namespace(k,v)
R='http://schemas.openxmlformats.org/package/2006/relationships';CT='http://schemas.openxmlformats.org/package/2006/content-types'
xml=lambda x:E.tostring(x,encoding='utf-8',xml_declaration=True)
ppt=files[0]
with zipfile.ZipFile(backup/ppt) as z:D={n:z.read(n) for n in z.namelist()}
pr=E.fromstring(D['ppt/presentation.xml']);rels=E.fromstring(D['ppt/_rels/presentation.xml.rels']);lookup={n.get('Id'):n for n in rels};lst=pr.find('p:sldIdLst',N);deleted=[]
for sid in list(lst)[:2]:
 rid=sid.get('{'+N['r']+'}id');rel=lookup[rid];part=posixpath.normpath('ppt/'+rel.get('Target'));deleted.append(part);lst.remove(sid);rels.remove(rel)
removed=[]
for part in deleted:
 rp=posixpath.dirname(part)+'/_rels/'+posixpath.basename(part)+'.rels'
 for rr in E.fromstring(D[rp]):
  if rr.get('Type','').endswith('/notesSlide'):
   np=posixpath.normpath(posixpath.dirname(part)+'/'+rr.get('Target'));removed.extend([np,posixpath.dirname(np)+'/_rels/'+posixpath.basename(np)+'.rels'])
 removed.extend([part,rp])
for part in removed:D.pop(part,None)
D['ppt/presentation.xml']=xml(pr);D['ppt/_rels/presentation.xml.rels']=xml(rels)
ct=E.fromstring(D['[Content_Types].xml'])
for n in list(ct):
 if n.get('PartName','').lstrip('/') in removed:ct.remove(n)
E.register_namespace('',CT);D['[Content_Types].xml']=xml(ct)
remaining=[];titles=[]
for num,sid in enumerate(lst,1):
 part=posixpath.normpath('ppt/'+lookup[sid.get('{'+N['r']+'}id')].get('Target'));remaining.append(part);root=E.fromstring(D[part])
 for t in root.findall('.//a:t',N):
  if re.fullmatch(r'\d+ / 21',t.text or ''):t.text=f'{num} / 19'
 D[part]=xml(root)
 title=''
 for s in root.findall('p:cSld/p:spTree/p:sp',N):
  c=s.find('p:nvSpPr/p:cNvPr',N)
  if c is not None and c.get('id')=='4':title=''.join(t.text or '' for t in s.findall('.//a:t',N))
 titles.append(title)
app=E.fromstring(D['docProps/app.xml']);ep='http://schemas.openxmlformats.org/officeDocument/2006/extended-properties';vt='http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes'
sl=app.find('{'+ep+'}Slides')
if sl is not None:sl.text='19'
hp=app.find('{'+ep+'}HeadingPairs/{'+vt+'}vector')
if hp is not None:
 vals=list(hp)
 for i,v in enumerate(vals[:-1]):
  if any((n.text or '')=='Slides' for n in v.iter()):
   for n in vals[i+1].iter():
    if n.tag=='{'+vt+'}i4':n.text='19'
top=app.find('{'+ep+'}TitlesOfParts/{'+vt+'}vector')
if top is not None:
 for n in list(top):top.remove(n)
 top.set('size','19');top.set('baseType','lpstr')
 for title in titles:E.SubElement(top,'{'+vt+'}lpstr').text=title
D['docProps/app.xml']=xml(app)
with zipfile.ZipFile(B/ppt,'w',zipfile.ZIP_DEFLATED) as z:
 for n,v in D.items():z.writestr(n,v)
# Synchronize the external script; speaker notes remain attached to retained slides.
s=(backup/files[2]).read_text();parts=re.split(r'(?=^## 第 \d+ 页｜)',s,flags=re.M)
header=parts[0].replace('正文 18 页','正文 16 页').replace('第 1—5、7—8、13—18 页','第 1—3、5—6、11—16 页')
retained=[]
for part in parts[1:]:
 m=re.match(r'## 第 (\d+) 页｜',part);n=int(m.group(1))
 if n>2:retained.append(re.sub(r'^## 第 \d+ 页｜',f'## 第 {n-2} 页｜',part,count=1))
assert len(retained)==19
(B/files[2]).write_text(header+''.join(retained))
u=(backup/files[3]).read_text().replace('正文第 1—18 页','正文第 1—16 页').replace('第 19—21 页','第 17—19 页').replace('第 1—5、7—8、13—18 页','第 1—3、5—6、11—16 页').replace('第 6、9 页','第 4、7 页').replace('共 21 页','共 19 页').replace('21 页均','19 页均').replace('21 页，逐页','19 页，逐页')
u=u.replace('正文第 1—16 页','已按用户要求删除原封面与汇报路线两页，现从几何与方向开始。正文第 1—16 页')
(B/files[3]).write_text(u)
# The PDF exporter follows the actual slide list, so deletions need no duplicated content edits.
r=B/'制作记录/render_ooxml.py';s=r.read_text().replace("if len(doc.pages)!=21:raise ValueError(('PDF page count',len(doc.pages)))","if len(doc.pages)!=len(order):raise ValueError(('PDF page count',len(doc.pages)))");r.write_text(s)
(B/'制作记录/slide_order.json').write_text(json.dumps([int(re.search(r'slide(\d+)\.xml',p).group(1)) for p in remaining]))
print('Deleted first two slides; retained:',len(remaining),'backup:',backup)
