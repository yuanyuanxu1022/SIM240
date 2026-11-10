from pathlib import Path
import zipfile,xml.etree.ElementTree as E,copy,re,json,shutil,posixpath
B=Path(__file__).resolve().parent.parent
bk=B/'制作记录/加入计数说明前_19页备份';bk.mkdir(exist_ok=True)
files=['PAPER1_导师汇报_20261105_下午修订版.pptx','PAPER1_导师汇报_20261105_下午修订版.pdf','下午汇报逐页讲稿.md','先读这里_下午汇报.md']
for f in files:
 if not (bk/f).exists():shutil.copy2(B/f,bk/f)
# Reuse native-object helpers, stopping before any old deck authoring statements.
src=(B/'制作记录/revise_ooxml.py').read_text().split('# Native edits preserve')[0]
g={'__file__':str(B/'制作记录/revise_ooxml.py')};exec(compile(src,'native_helpers','exec'),g)
N=g['NS'];q=g['q'];text=g['text'];table=g['table'];box=g['box'];blank=g['blank_body'];runpara=g['runpara']
with zipfile.ZipFile(bk/files[0]) as z:D={n:z.read(n) for n in z.namelist()}
slides={int(re.search(r'slide(\d+)\.xml$',n).group(1)):E.fromstring(v) for n,v in D.items() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)}
g['slides']=slides
slides[22]=copy.deepcopy(slides[21]);blank(22)
text(22,3,'1 计数口径 · 三类工作分别计数')
text(22,4,'18 种几何、5 项验证任务、5 个 OpenFOAM 算例有何区别？',24)
text(22,7,'依据：论文参数表；S0—S4 验收报告；OpenFOAM_comparison_clarification_20261104/REPORT.md。',8.5)
rows=[
 ['比较项目','18 种几何（36 个方向点）','5 项验证任务（S0—S4）','5 个已完成 OpenFOAM 算例'],
 ['在数什么','不同的间隙 h 与槽深 d 组合\n每种几何分别沿槽、横槽驱动','检查计算可信度的五项任务\n每项可含多档网格或驱动力','平均模型的五个静态接入算例\n共用 h75/d100 几何输入'],
 ['具体包含','h25：d25 / 50 / 100\nh50 / 75 / 125：各五档槽深\n槽宽120、周期240 nm固定','S0 修复回归，S1 平板解析\nS2 常规网格，S3 驱动力\nS4 薄间隙网格','C01 / C02：V2 横槽 / 沿槽\nC03 / C04：原公式 横槽 / 沿槽\nGDI01：porosity 子类实际接入'],
 ['回答什么','导度如何随几何和方向变化？\n原公式和 V2 相对离散结果\n各有多大偏差？','平板是否算准、驱动力是否线性？\n换网格后结果是否足够稳定？\n用于检查参考的可信度','同一 K / 阻力定义能否正确接入？\n子类直接算系数后能否复现\n已有平均模型结果？'],
 ['当前证据边界','5 nm 历史样本与回顾性评价\n不是 18 种已获严格资格的参考','S0—S3 通过\nS4 横槽 1.328% > 1%，未通过\n不计为新增 5 种样本几何','五例已有静态接入验收\n不逐槽解析，不验证 V2 精度\n不是另外 5 种独立沟槽几何']
]
table(22,.65,1.43,[1.30,3.40,3.50,3.80],rows,rowh=.92,fs=12)
box(22,.65,6.17,12.0,.59,'另行计数：12 类是新宿主代码审计；A/B/C 是 3 例待运行方案，均不计入已完成的 5 例。',13,True,color='0E3F8C',fill='E8EFF8')
# Use "task" consistently where the weekly validation count appears.
text(10,4,'11 月 2—4 日：五项验证任务，四项通过，一项停在横槽网格',25)
tbl=g['shape'](10,9).find('.//a:tbl',N);tx=tbl.find('a:tr/a:tc/a:txBody',N)
for p in tx.findall('a:p',N):tx.remove(p)
tx.append(runpara('验证任务',11,True,'FFFFFF'))
# Attach layout and notes without inheriting another case identity.
R='http://schemas.openxmlformats.org/package/2006/relationships';CT='http://schemas.openxmlformats.org/package/2006/content-types';xml=lambda x:E.tostring(x,encoding='utf-8',xml_declaration=True)
r=E.fromstring(D['ppt/slides/_rels/slide21.xml.rels'])
for n in r:
 if n.get('Type','').endswith('/notesSlide'):n.set('Target','../notesSlides/notesSlide22.xml')
D['ppt/slides/_rels/slide22.xml.rels']=xml(r)
r=E.fromstring(D['ppt/notesSlides/_rels/notesSlide21.xml.rels'])
for n in r:
 if n.get('Type','').endswith('/slide'):n.set('Target','../slides/slide22.xml')
D['ppt/notesSlides/_rels/notesSlide22.xml.rels']=xml(r)
nr=E.fromstring(D['ppt/notesSlides/notesSlide21.xml'])
notes='这三种计数回答不同问题。18种几何是论文的参数样本，每种两个方向，共36个方向点。5项是S0到S4五类验证任务，其中包含多次计算和既有结果复用，不能当作另外五种几何。OpenFOAM有五个已完成静态算例：C01、C02使用V2分别算横槽和沿槽，C03、C04使用原公式分别算横槽和沿槽；GDI01把同一模型通过porosity子类实际接入。四个C例各有二维和OpenFOAM两端，GDI01有一个OpenFOAM端，所以五例不能简单解释成总共只有五次程序执行。五例共用h75/d100的平均几何，目的是核对接入一致性，不能证明V2精度。今天新宿主的12类审计是软件检查，A/B/C三例是待运行方案，都另外记录。三类工作不能相加成独立物理样本数。'
for sp in nr.findall('.//p:sp',N):
 ph=sp.find('p:nvSpPr/p:nvPr/p:ph',N)
 if ph is not None and ph.get('type')=='body':
  tx=sp.find('p:txBody',N)
  for p in tx.findall('a:p',N):tx.remove(p)
  for line in [notes,'证据：OpenFOAM_comparison_clarification_20261104/REPORT.md；Groove_gap_host_integration_20261105/REPORT.md；Groove_gap_flow_acceptance_plan_20261105/PLAN.md；中文稿表1与S0—S4报告。']:tx.append(runpara(line,12))
D['ppt/notesSlides/notesSlide22.xml']=xml(nr)
ct=E.fromstring(D['[Content_Types].xml'])
for part,typ in [('slides/slide22.xml','slide'),('notesSlides/notesSlide22.xml','notesSlide')]:E.SubElement(ct,'{'+CT+'}Override',{'PartName':'/ppt/'+part,'ContentType':'application/vnd.openxmlformats-officedocument.presentationml.'+typ+'+xml'})
E.register_namespace('',CT);D['[Content_Types].xml']=xml(ct)
pr=E.fromstring(D['ppt/presentation.xml']);rels=E.fromstring(D['ppt/_rels/presentation.xml.rels']);rid='rId'+str(max(int(n.get('Id')[3:]) for n in rels)+1)
E.SubElement(rels,'{'+R+'}Relationship',{'Id':rid,'Type':N['r']+'/slide','Target':'slides/slide22.xml'});D['ppt/_rels/presentation.xml.rels']=xml(rels)
lst=pr.find('p:sldIdLst',N);ne=E.Element(q('p:sldId'),{'id':str(max(int(n.get('id')) for n in lst)+1),q('r:id'):rid});lst.insert(1,ne);D['ppt/presentation.xml']=xml(pr)
lookup={n.get('Id'):n.get('Target') for n in rels};order=[]
for pos,sid in enumerate(lst,1):
 i=int(re.search(r'slide(\d+)\.xml',lookup[sid.get(q('r:id'))]).group(1));order.append(i)
 for t in slides[i].findall('.//a:t',N):
  if re.fullmatch(r'\d+ / 19',t.text or ''):t.text=f'{pos} / 20'
 D[f'ppt/slides/slide{i}.xml']=xml(slides[i])
app=E.fromstring(D['docProps/app.xml']);ep='http://schemas.openxmlformats.org/officeDocument/2006/extended-properties';vt='http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes'
app.find('{'+ep+'}Slides').text='20'
hp=app.find('{'+ep+'}HeadingPairs/{'+vt+'}vector')
if hp is not None:
 for i,v in enumerate(list(hp)[:-1]):
  if any(n.text=='Slides' for n in v.iter()):
   for n in list(hp)[i+1].iter():
    if n.tag=='{'+vt+'}i4':n.text='20'
top=app.find('{'+ep+'}TitlesOfParts/{'+vt+'}vector')
if top is not None:
 for n in list(top):top.remove(n)
 top.set('size','20')
 for i in order:E.SubElement(top,'{'+vt+'}lpstr').text=''.join(t.text or '' for t in g['shape'](i,4).findall('.//a:t',N))
D['docProps/app.xml']=xml(app)
with zipfile.ZipFile(B/files[0],'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in D.items():z.writestr(n,b)
# Update the external script and all navigational references.
s=(bk/files[2]).read_text();s=s.replace('正文 16 页','正文 17 页').replace('第 1—3、5—6、11—16 页','第 1—4、6—7、12—17 页')
s=re.sub(r'^## 第 (\d+) 页｜',lambda m:f'## 第 {int(m.group(1))+(int(m.group(1))>=2)} 页｜',s,flags=re.M)
pos=s.index('## 第 3 页｜');s=s[:pos]+'## 第 2 页｜18 种几何、5 项验证任务、5 个 OpenFOAM 算例有何区别？\n\n'+notes+'\n\n证据：OpenFOAM_comparison_clarification_20261104/REPORT.md；S0—S4验收报告；论文参数表。\n\n'+s[pos:]
s=s.replace('五组验证任务','五项验证任务');(B/files[2]).write_text(s)
u=(bk/files[3]).read_text().replace('正文第 1—16 页','正文第 1—17 页').replace('第 17—19 页','第 18—20 页').replace('第 1—3、5—6、11—16 页','第 1—4、6—7、12—17 页').replace('第 4、7 页','第 5、8 页').replace('共 19 页','共 20 页').replace('19 页均','20 页均').replace('19 页尺寸','20 页尺寸').replace('PDF 为 19 页','PDF 为 20 页')
u=u.replace('现从几何与方向开始。','现从几何与方向开始。第2页新增三类计数对照：18种参数几何、S0—S4五项验证任务、C01—C04及GDI01五个已完成OpenFOAM接入算例。')
(B/files[3]).write_text(u)
(B/'制作记录/slide_order.json').write_text(json.dumps(order))
print('Added editable comparison slide at page 2; total:',len(order))
