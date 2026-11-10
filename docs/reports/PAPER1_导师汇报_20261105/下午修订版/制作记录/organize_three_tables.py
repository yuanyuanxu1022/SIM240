from pathlib import Path
import xml.etree.ElementTree as E,zipfile,re,copy,shutil,json,posixpath
B=Path(__file__).resolve().parent.parent;bk=B/'制作记录/三类明细表整理前_20页备份';bk.mkdir(exist_ok=True)
files=['PAPER1_导师汇报_20261105_下午修订版.pptx','PAPER1_导师汇报_20261105_下午修订版.pdf','下午汇报逐页讲稿.md','先读这里_下午汇报.md']
for f in files:
 if not (bk/f).exists():shutil.copy2(B/f,bk/f)
g={'__file__':str(B/'制作记录/revise_ooxml.py')};exec(compile((B/'制作记录/revise_ooxml.py').read_text().split('# Native edits preserve')[0],'native_helpers','exec'),g)
N=g['NS'];q=g['q'];text=g['text'];blank=g['blank_body'];box=g['box'];table=g['table'];runpara=g['runpara'];xml=lambda r:E.tostring(r,encoding='utf-8',xml_declaration=True)
with zipfile.ZipFile(bk/files[0]) as z:D={n:z.read(n) for n in z.namelist()}
slides={int(re.search(r'slide(\d+)\.xml$',n).group(1)):E.fromstring(v) for n,v in D.items() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)};g['slides']=slides
# Reuse the two existing evidence tables, then add only the missing OpenFOAM detail table.
blank(5);text(5,3,'1 计数明细 · 研究样本');text(5,4,'18 种几何：四档间隙下的槽深组合，共 36 个方向点',25)
text(5,7,'证据：中文稿表1；PAPER1_claim_evidence_review_20261105/REPORT.md。',9)
box(5,.65,1.43,12,.55,'槽宽 w=120 nm、周期 P=240 nm 固定；每种几何分别沿槽、横槽计算。',16,True,color='0E3F8C',fill='E8EFF8')
table(5,.65,2.12,[2.10,5.1,2.4,2.4],[['最小间隙 h','已计算的槽深 d','几何数量','方向点数量'],['25 nm','25 / 50 / 100 nm','3','6'],['50 nm','25 / 50 / 75 / 100 / 120 nm','5','10'],['75 nm','25 / 50 / 75 / 100 / 120 nm','5','10'],['125 nm','25 / 50 / 75 / 100 / 120 nm','5','10'],['合计','18 种不同的 h–d 组合','18','36']],rowh=.59,fs=14)
box(5,.65,5.92,12,.81,'用于分析导度随几何和方向的变化，以及原公式与 V2 相对数值结果的偏差。\n当前为 5 nm 离散样本的回顾性比较；h25/d75、h25/d120 未采样，不填补。',14,color='0E3F8C',fill='E8EFF8')
blank(10);text(10,3,'1 计数明细 · 可信度检查');text(10,4,'5 项验证任务：检查计算可信度，包含多次运行或结果复用',24)
text(10,7,'证据：S0—S4 原验收报告；S4 原横槽网格 FAIL 保留。',9)
rows=[['验证任务','几何与计算设置','检查内容','当前结论'],['S0 修复回归','h75 / d100；两方向','质量诊断修正后，关键流动输出是否一致','通过'],['S1 平板解析','h30；无沟槽','与平板解析解比较导度和速度剖面','通过'],['S2 常规网格','h60 / d80；两方向\n5 / 2.5 / 1.25 nm','换网格后结果是否足够稳定','通过'],['S3 驱动力','h60 / d80；2.5 nm\n三档驱动力，两方向','驱动力变化时，导度是否基本不变','通过'],['S4 薄间隙网格','h30 / d80；两方向\n5 / 2.5 / 1.25 nm','沿槽网格通过；横槽变化 1.328%\n超过事先规定的 1%','未通过']]
t=table(10,.65,1.55,[2.2,3.25,4.65,1.9],rows,rowh=.70,fs=13)
for tc in t.findall('.//a:tr',N)[-1].findall('a:tc',N):
 for c in tc.findall('.//a:rPr/a:solidFill/a:srgbClr',N):c.set('val','D9534F')
box(10,.65,5.98,12,.75,'五项是检查任务数，不能当作新增五种几何，也不能当作总共只运行了五次。\nS3 的中档结果复用 S2；单条运行合格与整个阶段通过分别判断。',14,color='0E3F8C',fill='E8EFF8')
slides[23]=copy.deepcopy(slides[21]);blank(23)
text(23,3,'1 计数明细 · OpenFOAM 静态接入');text(23,4,'5 个 OpenFOAM 算例：四个系数 / 方向组合，加一次子类接入',24)
text(23,7,'证据：OpenFOAM_comparison_clarification_20261104/REPORT.md；C01—C04 / GDI01 原验收。',9)
box(23,.65,1.42,12,.59,'共同输入：h=75、d=100、w=120、P=240 nm，平均液层厚度 H=125 nm。\n合成平均域 24×48 µm，512 单元；静态压差 24 Pa，无闭合运动。',13,color='0E3F8C',fill='E8EFF8')
table(23,.65,2.12,[1.35,2.15,1.6,6.9],[['算例','使用的模型','方向','具体检查什么'],['C01','V2','横槽','V2 横槽导度输入下，二维与 OpenFOAM 平均模型是否一致'],['C02','V2','沿槽','V2 沿槽导度输入下，二维与 OpenFOAM 平均模型是否一致'],['C03','原公式','横槽','原公式横槽导度输入下，两端实现是否一致'],['C04','原公式','沿槽','原公式沿槽导度输入下，两端实现是否一致'],['GDI01','V2 + 子类','横槽','grooveDarcy 按几何直接算 K/D，经实际阻力源接入并复现结果']],rowh=.62,fs=13)
box(23,.65,6.02,12,.73,'五例均已有受限静态接入验收，共用同一平均几何，不逐槽解析，不能据此证明 V2 精度。\n12 类新宿主审计、A/B/C 三例待运行方案另外计数。',14,color='0E3F8C',fill='E8EFF8')
# Clone notes/layout links for the new editable slide.
R='http://schemas.openxmlformats.org/package/2006/relationships';CT='http://schemas.openxmlformats.org/package/2006/content-types'
r=E.fromstring(D['ppt/slides/_rels/slide21.xml.rels'])
for n in r:
 if n.get('Type','').endswith('/notesSlide'):n.set('Target','../notesSlides/notesSlide23.xml')
D['ppt/slides/_rels/slide23.xml.rels']=xml(r)
r=E.fromstring(D['ppt/notesSlides/_rels/notesSlide21.xml.rels'])
for n in r:
 if n.get('Type','').endswith('/slide'):n.set('Target','../slides/slide23.xml')
D['ppt/notesSlides/_rels/notesSlide23.xml.rels']=xml(r);D['ppt/notesSlides/notesSlide23.xml']=D['ppt/notesSlides/notesSlide21.xml']
newnotes={5:'这里的18是不同间隙和槽深的组合数。h25只有三种槽深，h50、75、125各五种，合计18。每种分别沿槽、横槽驱动，所以是36个方向点。未采样的两格不填补。这批数据用于回顾性比较，不代表18种全部取得严格参考资格。',10:'这里的5是五项检查任务。S0看诊断修复后关键输出是否保持一致，S1对平板解析解，S2看常规间隙网格敏感性，S3看驱动力线性，S4看薄间隙网格敏感性。每项可能包含多次运行，S3还复用了S2中档结果。前四项通过，S4横槽中细变化1.328%超过1%，所以S4仍未通过，不能把单条检查通过说成整个阶段通过。',23:'OpenFOAM五例共用h75/d100平均几何。C01和C02分别输入V2横槽、沿槽导度，C03和C04分别输入原公式横槽、沿槽导度，核对二维与OpenFOAM平均模型的一致性。GDI01进一步通过grooveDarcy子类，按几何直接计算K和阻力，经实际动量源接入，复现已有平均模型结果。四个C例各有二维和OpenFOAM两端，GDI01有一个OpenFOAM端，因此五例不是总共五次程序执行，也不是另外五种独立几何。它们核对接入，不提供V2对真实沟槽的独立精度证据。新宿主12类不求解审计和A/B/C三例待运行方案另计。'}
sources={5:'中文稿表1；PAPER1_claim_evidence_review_20261105/REPORT.md',10:'URV_S1_results_review_20261102/REPORT.md；URV_S2_completed_review_20261103_095422/REPORT.md；URV_S3_completed_review_20261103_172033/REPORT.md；URV_S4_completed_review_20261104_143205/REPORT.md；URV_S0_results_review_20261101/REPORT.md。',23:'OpenFOAM_comparison_clarification_20261104/REPORT.md；SDI_C01_results_20261030/REPORT.md；SDI_C02_results_20261030/REPORT.md；SDI_C03_results_20261030/REPORT.md；SDI_C04_results_20261030/REPORT.md；GDI01_results_20261030/REPORT.md。'}
for i,content in newnotes.items():
 nr=E.fromstring(D[f'ppt/notesSlides/notesSlide{i}.xml'])
 for sp in nr.findall('.//p:sp',N):
  ph=sp.find('p:nvSpPr/p:nvPr/p:ph',N)
  if ph is not None and ph.get('type')=='body':
   tx=sp.find('p:txBody',N)
   for p in tx.findall('a:p',N):tx.remove(p)
   for line in [content,'证据入口（相对docs/reports）：'+sources[i]]:tx.append(runpara(line,12))
 D[f'ppt/notesSlides/notesSlide{i}.xml']=xml(nr)
ct=E.fromstring(D['[Content_Types].xml'])
for part,typ in [('slides/slide23.xml','slide'),('notesSlides/notesSlide23.xml','notesSlide')]:E.SubElement(ct,'{'+CT+'}Override',{'PartName':'/ppt/'+part,'ContentType':'application/vnd.openxmlformats-officedocument.presentationml.'+typ+'+xml'})
E.register_namespace('',CT);D['[Content_Types].xml']=xml(ct)
rels=E.fromstring(D['ppt/_rels/presentation.xml.rels']);rid='rId'+str(max(int(n.get('Id')[3:]) for n in rels)+1);E.SubElement(rels,'{'+R+'}Relationship',{'Id':rid,'Type':N['r']+'/slide','Target':'slides/slide23.xml'});D['ppt/_rels/presentation.xml.rels']=xml(rels)
pr=E.fromstring(D['ppt/presentation.xml']);lst=pr.find('p:sldIdLst',N);lookup={n.get('Id'):n.get('Target') for n in rels};oldorder=[int(re.search(r'slide(\d+)\.xml',lookup[n.get(q('r:id'))]).group(1)) for n in lst];sids={i:n for i,n in zip(oldorder,list(lst))};sids[23]=E.Element(q('p:sldId'),{'id':str(max(int(n.get('id')) for n in lst)+1),q('r:id'):rid})
order=[3,22,5,10,23]+[i for i in oldorder if i not in [3,22,5,10]]
for n in list(lst):lst.remove(n)
for pos,i in enumerate(order,1):
 lst.append(sids[i])
 for t in slides[i].findall('.//a:t',N):
  if re.fullmatch(r'\d+ / 20',t.text or ''):t.text=f'{pos} / 21'
 D[f'ppt/slides/slide{i}.xml']=xml(slides[i])
D['ppt/presentation.xml']=xml(pr)
ep='http://schemas.openxmlformats.org/officeDocument/2006/extended-properties';vt='http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes';app=E.fromstring(D['docProps/app.xml']);app.find('{'+ep+'}Slides').text='21';hp=app.find('{'+ep+'}HeadingPairs/{'+vt+'}vector')
if hp is not None:
 for j,v in enumerate(list(hp)[:-1]):
  if any(n.text=='Slides' for n in v.iter()):
   for n in list(hp)[j+1].iter():
    if n.tag=='{'+vt+'}i4':n.text='21'
top=app.find('{'+ep+'}TitlesOfParts/{'+vt+'}vector')
if top is not None:
 for n in list(top):top.remove(n)
 top.set('size','21')
 for i in order:E.SubElement(top,'{'+vt+'}lpstr').text=''.join(t.text or '' for t in g['shape'](i,4).findall('.//a:t',N))
D['docProps/app.xml']=xml(app)
with zipfile.ZipFile(B/files[0],'w',zipfile.ZIP_DEFLATED) as z:
 for n,v in D.items():z.writestr(n,v)
# Reorder the existing speaking script by slide identity and replace the three table explanations.
s=(bk/files[2]).read_text();chunks=re.split(r'(?=^## 第 \d+ 页｜)',s,flags=re.M);oldnotes={i:ch for i,ch in zip(oldorder,chunks[1:])}
header=chunks[0].replace('正文 17 页','正文 18 页').replace('第 1—4、6—7、12—17 页','第 1—6、8—9、13—18 页')
result=[header]
for pos,i in enumerate(order,1):
 title=''.join(t.text or '' for t in g['shape'](i,4).findall('.//a:t',N))
 if i in newnotes:part=f'## 第 {pos} 页｜{title}\n\n{newnotes[i]}\n\n证据：{sources[i]}\n\n'
 else:part=re.sub(r'^## 第 \d+ 页｜',f'## 第 {pos} 页｜',oldnotes[i],count=1)
 result.append(part)
(B/files[2]).write_text(''.join(result))
u=(bk/files[3]).read_text().replace('正文第 1—17 页','正文第 1—18 页').replace('第 18—20 页','第 19—21 页').replace('第 1—4、6—7、12—17 页','第 1—6、8—9、13—18 页').replace('第 5、8 页','第 7、10 页').replace('共 20 页','共 21 页').replace('20 页均','21 页均').replace('20 页尺寸','21 页尺寸').replace('PDF 为 20 页','PDF 为 21 页')
u=u.replace('第2页新增三类计数对照：18种参数几何、S0—S4五项验证任务、C01—C04及GDI01五个已完成OpenFOAM接入算例。','第2页是三类计数总对照；第3、4、5页连续放置18种参数几何表、S0—S4五项验证任务表、C01—C04及GDI01五个OpenFOAM算例表。已有两张表复用调整，只新增一张OpenFOAM明细表。')
(B/files[3]).write_text(u);(B/'制作记录/slide_order.json').write_text(json.dumps(order));print('Reused 2 tables, added OpenFOAM detail table; pages:',len(order),'table pages:3,4,5')
