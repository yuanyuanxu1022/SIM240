from pathlib import Path
import zipfile,xml.etree.ElementTree as E,copy,re,json,hashlib
B=Path(__file__).resolve().parent.parent
SRC=B.parent/'PAPER1_导师汇报_20261105.pptx'
OUT=B/'PAPER1_导师汇报_20261105_下午修订版.pptx'
NS={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
for k,v in NS.items():E.register_namespace(k,v)
q=lambda t:'{'+NS[t.split(':')[0]]+'}'+t.split(':')[1]
def el(t,attrs=None):return E.Element(q(t),attrs or {})
def sub(p,t,attrs=None):return E.SubElement(p,q(t),attrs or {})
with zipfile.ZipFile(SRC) as z: data={n:z.read(n) for n in z.namelist()}
slides={i:E.fromstring(data[f'ppt/slides/slide{i}.xml']) for i in range(1,21)}
def tree(i):return slides[i].find('p:cSld/p:spTree',NS)
def shape(i,sid):
 for s in tree(i):
  c=s.find('.//p:cNvPr',NS)
  if c is not None and c.get('id')==str(sid):return s
 raise KeyError((i,sid))
def runpara(txt,size=14,bold=False,color='1A2230',align='l'):
 p=el('a:p'); pp=sub(p,'a:pPr',{'algn':align});ln=sub(pp,'a:lnSpc');sub(ln,'a:spcPct',{'val':'120000'})
 for chunk in re.split(r'(\^\{[^}]+\}|_\{[^}]+\})',txt):
  if not chunk:continue
  marked=chunk.startswith('^{') or chunk.startswith('_{')
  value=chunk[2:-1] if marked else chunk
  attrs={'lang':'zh-CN','sz':str(round(size*(.72 if marked else 1)*100)),'b':str(int(bold))}
  if marked:attrs['baseline']='30000' if chunk[0]=='^' else '-25000'
  r=sub(p,'a:r');rp=sub(r,'a:rPr',attrs);c=sub(rp,'a:solidFill');sub(c,'a:srgbClr',{'val':color})
  for typ in ['latin','ea','cs']:sub(rp,'a:'+typ,{'typeface':'Microsoft YaHei'})
  sub(r,'a:t').text=value
 sub(p,'a:endParaRPr',{'lang':'zh-CN','sz':str(round(size*100))})
 return p
def text(i,sid,txt,size=None,color=None):
 s=shape(i,sid);tx=s.find('p:txBody',NS)
 if tx is None:raise ValueError((i,sid))
 ps=tx.findall('a:p',NS)
 tmpl=ps[0].find('a:r/a:rPr',NS) if ps else None
 fs=size or (float(tmpl.get('sz','1400'))/100 if tmpl is not None else 14)
 co=color or ('1A2230' if tmpl is None or tmpl.find('a:solidFill/a:srgbClr',NS) is None else tmpl.find('a:solidFill/a:srgbClr',NS).get('val'))
 bold=tmpl is not None and tmpl.get('b')=='1'
 for p in ps:tx.remove(p)
 for j,line in enumerate(txt.split('\n')):tx.append(runpara(line,fs,bold if j==0 else False,co))
 return s

def blank_body(i):
 tr=tree(i)
 for s in list(tr):
  c=s.find('.//p:cNvPr',NS)
  if c is not None and int(c.get('id')) not in [1,2,3,4,5,6,7,8]:tr.remove(s)

def box(i,x,y,w,h,content='',fs=15,bold=False,color='1A2230',fill=None,border=None,align='l'):
 tr=tree(i);sid=max([int(c.get('id')) for c in tr.findall('.//p:cNvPr',NS)]+[1])+1
 s=sub(tr,'p:sp');nv=sub(s,'p:nvSpPr');sub(nv,'p:cNvPr',{'id':str(sid),'name':f'Afternoon text {sid}'});sub(nv,'p:cNvSpPr',{'txBox':'1'});sub(nv,'p:nvPr')
 sp=sub(s,'p:spPr');xf=sub(sp,'a:xfrm');sub(xf,'a:off',{'x':str(round(x*914400)),'y':str(round(y*914400))});sub(xf,'a:ext',{'cx':str(round(w*914400)),'cy':str(round(h*914400))});g=sub(sp,'a:prstGeom',{'prst':'rect'});sub(g,'a:avLst')
 if fill:sub(sub(sp,'a:solidFill'),'a:srgbClr',{'val':fill})
 else:sub(sp,'a:noFill')
 ln=sub(sp,'a:ln',{'w':'8000'})
 if border:sub(sub(ln,'a:solidFill'),'a:srgbClr',{'val':border})
 else:sub(ln,'a:noFill')
 tx=sub(s,'p:txBody');sub(tx,'a:bodyPr',{'wrap':'square','lIns':'91440','rIns':'91440','tIns':'45720','bIns':'45720','anchor':'t'});sub(tx,'a:lstStyle')
 for line in content.split('\n'):tx.append(runpara(line,fs,bold,color,align))
 return s

def table(i,x,y,widths,rows,rowh=.56,fs=13):
 tr=tree(i);sid=max([int(c.get('id')) for c in tr.findall('.//p:cNvPr',NS)]+[1])+1
 g=sub(tr,'p:graphicFrame');nv=sub(g,'p:nvGraphicFramePr');sub(nv,'p:cNvPr',{'id':str(sid),'name':f'Editable table {sid}'});sub(nv,'p:cNvGraphicFramePr');sub(nv,'p:nvPr')
 xf=sub(g,'p:xfrm');sub(xf,'a:off',{'x':str(round(x*914400)),'y':str(round(y*914400))});sub(xf,'a:ext',{'cx':str(round(sum(widths)*914400)),'cy':str(round(rowh*len(rows)*914400))})
 gd=sub(sub(g,'a:graphic'),'a:graphicData',{'uri':'http://schemas.openxmlformats.org/drawingml/2006/table'});tbl=sub(gd,'a:tbl');sub(tbl,'a:tblPr',{'firstRow':'0','bandRow':'0'});grid=sub(tbl,'a:tblGrid')
 for w in widths:sub(grid,'a:gridCol',{'w':str(round(w*914400))})
 for ri,row in enumerate(rows):
  rr=sub(tbl,'a:tr',{'h':str(round(rowh*914400))})
  for val in row:
   tc=sub(rr,'a:tc');tx=sub(tc,'a:txBody');sub(tx,'a:bodyPr');sub(tx,'a:lstStyle')
   for line in val.split('\n'):tx.append(runpara(line,fs,ri==0,'FFFFFF' if ri==0 else '1A2230'))
   pr=sub(tc,'a:tcPr',{'marL':'91440','marR':'91440','marT':'45720','marB':'45720','anchor':'ctr'});sub(sub(pr,'a:solidFill'),'a:srgbClr',{'val':'0E3F8C' if ri==0 else ('F0F5FC' if ri%2 else 'FFFFFF')})
   for edge in ['lnL','lnR','lnT','lnB']:
    ln=sub(pr,'a:'+edge,{'w':'5000'});sub(sub(ln,'a:solidFill'),'a:srgbClr',{'val':'D6DCE5'})
 return g
# Native edits preserve all source figures and the reference theme.
text(1,8,'局部立方律偏差、经验修正与最新证据边界',23)
text(1,10,'研究范围：固定间隙、完全充液、单相矩形沟槽\n汇报日期：2026 年 11 月 5 日下午',14)
text(2,4,'已有数值发现可以汇报，严格参考与独立预测尚未闭环',25)
text(2,7,'正文约 12—15 分钟；附录 3 页按需查阅。',10)
for sid,txt in {12:'研究对象',13:'固定间隙、全充液矩形沟槽，比较沿槽与横槽的流动阻力',15:'1 分钟',19:'核心发现',20:'18 组几何、36 个方向点：原公式高估，V2 回顾性改善且有反例',22:'4 分钟',26:'证据与卡点',27:'S1—S3 支持局部数值可信度；S4 横槽网格仍未通过',29:'4 分钟',33:'今天新增',34:'1.25 nm 数据复核；OpenFOAM 间隙接入与流量收支方案',36:'3 分钟',40:'请导师裁定',41:'论文保持何种主张；是否继续薄间隙补证与受控接入验收',43:'1 分钟'}.items():text(2,sid,txt)
text(3,12,'几何尺寸（示例 h=60、d=80、w=120、P=240 nm）\nh：凸台与平壁之间的最小间隙；槽内液层高 h+d\nd：槽深　w：槽宽　P：周期',14)
text(4,12,'② 离散比较基准：OpenLB 显式沟槽（5 nm）\n按沟槽几何直接求通量，取 K = νJ/a。\n不输入原公式或 V2 的系数。\n目前得到相对该离散结果的偏差；参考自身仍需网格与来源检查。',13.5)
text(4,14,'③ V2：在原公式上乘经验因子\nF∥ = 1 / [1 + 1.7685(d/w)^{1.6331}]\nF⊥ = 1 / [1 + 0.4900(d/w)^{0.6990}]\n仅修正因子未显式含 h，总导度仍含 h。\n残差来源尚未分离，不能只归因于缺少 h。',13)
text(6,14,'限定：5 nm 历史样本中的描述性关系。部分槽深端点跨不同程序组，构建差异与几何作用尚未完全分离。',12)
text(8,13,'V2 的定位：固定已公布系数的回顾性经验修正，尚无独立新条件预测验证。',12)
text(8,15,'回顾性评价的三个限制\n扩展数据在模型选择时已经可见。\n修正因子仅含 d/w，总 K 仍含 h。\n9 个标定几何与 9 个扩展几何分属不同程序组，构建差异尚未分离。\n\n若要证明预测精度\n需固定 V2 系数，使用未参与模型选择、且已独立验收的新条件参考。',13)
text(9,11,'为什么还要检查方向\n同一驱动方向下，两套主值重建的流向相差 9.20°。\n这提示降阶模型的流量分配可能受影响；真实填充顺序仍未验证。',14)
text(10,11,'11 月 5 日新增进展\n① 1.25 nm 数据收尾\n完成场数据复核，K 复现一致；S4 原 FAIL 保留。\n② 稿件主张逐项复核\n区分离散偏差、参考资格与预测验证。\n③ OpenFOAM 新宿主\n已编译并完成 12 类不求解审计；受控流场方案待落实。\n0.625 nm 方案审查中断，尚未运行。',12)
text(10,7,'S0—S4 为既有阶段结果；11 月 5 日新增审查、接入实现与方案，分别报告。',9)
text(11,10,'S1 光滑平板（h=30 nm，无槽）\nK 相对解析误差：0.173%\n速度剖面 L2 误差：0.079%\n两方向通过原定标准，支持该配置的平板实现。\n仍须单独核查沟槽几何、网格与来源。',14)
text(12,10,'驱动力跨度 4 倍，通量近似同比增长，K 几乎不变，支持所测范围内的线性响应。',11)
text(12,20,'这组检查支持什么\n在 h60/d80、2.5 nm 网格与三档驱动力内，未检出超过 0.1% 的驱动力依赖。\n中—细网格差 0.203% / 0.744% 明显大于驱动力跨度，仍需重视网格敏感性。\n这两类变化都不是连续真解误差的严格上界。',13)
text(13,12,'单条合格与网格独立是两项检查\n单条检查约束数值、几何与稳态；跨网格检查约束结果对分辨率的敏感性。\n构建复现不改写原 FAIL；后续补证须另定方案。',12)
# Replace stale server slide entirely.
blank_body(14);text(14,3,'4 最新进展 · 11 月 5 日数据复核');text(14,4,'1.25 nm 已完成：K 复现一致，S4 横槽网格仍未通过',25)
text(14,7,'证据：URV_S4_TGE_1p25_data_audit_20261105_100521/REPORT.md；原 S4 报告。',9)
box(14,.65,1.40,12.0,.56,'本条：h=30 nm，d=80 nm，横槽；完成数据审查与预定构建等价检查。',15,True,color='0E3F8C',fill='E8EFF8')
table(14,.65,2.12,[2.3,4.3,5.4],[['核对项目','实测或复算','能说明什么'],['末态 K','3.471791836744987×10⁻²⁴ m³','服务器 / 本机 K 相对差为 0'],['实际停止','第 12537 步首次满足收敛窗','最大步数为 371712，并非跑满'],['求解资源','2 h 6 min 15 s；峰值 1.526 GiB','实测 1.655 步/s，仅属于本条'],['数据与流场','10 帧三维场、切片和通量复核通过','25 列中 22 列相同，3 列有微小差异']],rowh=.60,fs=13)
box(14,.65,5.34,5.85,1.13,'已得到：本条 K 构建复现成立\n尚未取得严格参考资格。',16,True,color='0E3F8C',fill='E8EFF8')
box(14,6.65,5.34,6.0,1.13,'仍保留：1.328% > 1%\n0.625 nm 尚未运行，资源准备未闭合。',16,True,color='D9534F',fill='FBECEC')
# Replace outdated OpenFOAM slide.
blank_body(15);text(15,3,'5 OpenFOAM · 把 K 接入平均模型');text(15,4,'阻力系数必须用与速度、通量一致的平均液层厚度',25)
text(15,7,'证据：Groove_porosity_refresh_20261105；Groove_gap_host_integration_20261105。',9)
box(15,.65,1.45,6.05,1.00,'dᵢ = H / Kᵢ　（本项目为总 Darcy 阻力）\nH = h + (w/P)d　　J = H U',21,True,color='0E3F8C',fill='E8EFF8')
box(15,.65,2.65,6.05,1.38,'h：凸台与平壁的最小间隙\nH：面积平均液层厚度，不能混用\nh=75、d=100、w/P=1/2 时，H=125 nm。',16)
box(15,.65,4.18,6.05,2.12,'几何改变时同时更新 K、H 和储量变化率。\n若公式中的 h 原本表示平均厚度，可写 h/Kᵢ；使用前必须先统一定义。\nK 单位 m³，dᵢ 单位 m⁻²。',15,fill='F7F9FC',border='D6DCE5')
box(15,6.9,1.45,5.75,1.00,'新宿主的连续性方程\n∂H/∂t + ∇xy·(H U) = 0',21,True,color='0E3F8C',fill='E8EFF8')
box(15,6.9,2.65,5.75,2.18,'已经落实\ngrooveDarcy 子类直接计算 K 和 dᵢ。\n间隙、Hdot、阻力和面通量同步更新。\nFoundation 13 编译、12 类不求解审计通过。',15)
box(15,6.9,5.05,5.75,1.25,'尚未得到新压力或流场结果\n旧静态 C01—C04 / GDI01 只支持接入一致性，不能验证 V2 精度。',14,True,color='D9534F',fill='FBECEC')
# Add one slide by copying the source chrome and relationships.
slides[21]=copy.deepcopy(slides[15]);blank_body(21)
text(21,3,'5 OpenFOAM · 下一步受控流场方案');text(21,4,'验收要同时核对压力、实际排液和储液体积变化',25)
text(21,7,'方案：Groove_gap_flow_acceptance_plan_20261105/PLAN.md；以下均为拟议工况，尚未运行。',9)
table(21,.65,1.48,[1.15,2.85,3.0,5.0],[['拟议工况','当前 / 前一最小间隙','主要检查','解析预期与证据边界'],['A 固定回归','75 / 75 nm','退回旧 GDI01；512 单元','压力线性，净排液为 0'],['B 静态改隙','50 / 50 nm','H 与网格厚度不同；512 单元','H=100 nm，检查实际通量换算'],['C 闭合快照','75 / 77 nm；间隔 0.25 s','储量源与两端排液；拟 2048 单元','Hdot=−8 nm/s；压力含二次项']],rowh=.68,fs=13)
box(21,.65,4.38,12.0,.68,'收支目标：V新 − V旧 + Δt × ΣQ向外 = 0',22,True,color='0E3F8C',fill='E8EFF8')
box(21,.65,5.22,7.5,1.22,'Q 从求解器实际边界面通量带符号积分。\n再用边界速度与 H 独立重建；储量从前后间隙和单元面积重算。',14,fill='F7F9FC',border='D6DCE5')
box(21,8.35,5.22,4.3,1.22,'运行前仍缺 4 项准备\n边界处理、网格参数化、独立检查器、封存执行包。',14,True,color='D9534F',fill='FBECEC')
# Update evidence scope and advisor decisions.
text(16,3,'6 当前结论与限制')
text(16,4,'现有证据支持离散结果分析，尚不足以宣布全面验证',25)
text(16,7,'最新对照：PAPER1_claim_evidence_review_20261105/REPORT.md；保留历史失败与来源缺口。',9)
text(16,10,'可保留的主张\n18 组几何、36 个方向点的离散导度与方向差异。\n原公式相对 5 nm 参考全部高估导度。\nV2 降低整体最坏偏差，存在局部恶化反例。\n主值重建显示各向异性与流向角差异。\n理想 Stokes 条件下，理论给出非严格上界。\n\n共同限定：已采样范围、离散参考、回顾性评价。',13.5)
text(16,12,'必须补证或限定的主张\n新条件下固定 V2 的独立预测精度。\n薄间隙严格参考与严格误差界。\n真实压印压力、载荷、填充时间与实验吻合。\n把全部偏差归因于某一耗散机制。\n\n来源问题：不同历史程序组与参数分组交织，构建影响尚未完全分离。',13.5)
text(16,14,'1.25 nm 复现关闭了本条构建一致性问题；参考资格、模型精度与投稿准备仍分别待审。\n新 OpenFOAM 分支目前完成接入与不求解审计，流场验收方案尚待落实。',13)
text(16,16,'严格参考：未取得　　正式模型精度比较：未评价　　物理验证：未评价　　投稿准备：未完成',12)
text(17,3,'6 请导师裁定')
text(17,4,'建议先明确论文主张，再确定两条补证路线的投入',25)
text(17,10,'现有材料可用于讨论论文组织和后续方案，最终投稿判断仍需作者与导师审阅。',15)
text(17,12,'问题 1：论文是否保持当前证据范围？\n建议围绕已采样条件下的原公式偏差、方向性后果和 V2 回顾性修正展开。\n保留薄间隙反例、历史 FAIL 和程序来源限制。\n若把新条件预测作为核心贡献，须补独立合格参考和冻结系数比较。',15)
text(17,14,'问题 2：下一步优先补哪条证据？\n路线 A：继续严格参考路线，恢复 0.625 nm 准备审查，先核几何、初态和资源。\n路线 B：落实 OpenFOAM 四项运行前缺口，再按 A/B/C 逐项验收。\n两条路线回答不同问题，均不能自动扩大论文主张。',15)
text(17,17,'我的建议：先完成有边界的论文论证，再按导师选择补证。\nAI 协助代码、检查和材料整理；作者仍须逐项学习、核对并承担科学结论责任。',14)
text(18,17,'机制解释仍需补证\n侧壁和台阶附近的速度重分布是候选解释。\n现有数据尚未分离其贡献，不能作唯一归因。',13)
# Q&A native table cells, preserve its existing row geometry.
qa=shape(19,9).find('.//a:tbl',NS)
rows=qa.findall('a:tr',NS)
def celltxt(tc,value,size=12):
 tx=tc.find('a:txBody',NS)
 for p in tx.findall('a:p',NS):tx.remove(p)
 for line in value.split('\n'):tx.append(runpara(line,size))
celltxt(rows[4].findall('a:tc',NS)[1],'旧算例核接口；新宿主完成间隙接入和不求解检查。实际压力、边界排液与储量收支仍待受控流场验收，均不赋予 V2 精度。',12)
celltxt(rows[5].findall('a:tc',NS)[1],'门槛事先冻结，原 FAIL 保留。1.25 nm K 已复现，仍未取得严格参考；0.625 nm 尚未运行，是否继续取决于论文主张和资源。',12)
for rr in rows:rr.set('h',str(round(.745*914400)))
shape(19,9).find('p:xfrm/a:ext',NS).set('cy',str(round(.745*7*914400)))
# Source appendix updates, full evidence in speaker notes.
text(20,10,'18 几何 / 36 点、V2 与主张范围');text(20,11,'PAPER1_claim_evidence_review_20261105/REPORT.md',10)
text(20,25,'1.25 nm 数据、构建等价与实测资源');text(20,26,'URV_S4_TGE_1p25_data_audit_20261105_100521/REPORT.md',9)
text(20,28,'新 OpenFOAM 宿主实现 / 受控流场方案');text(20,29,'Groove_gap_host_integration_20261105；Groove_gap_flow_acceptance_plan_20261105',9)
text(20,31,'0.625 nm 当前准备停点');text(20,32,'URV_S4_TGE_0p625_readiness_review_20261105_100032/INTERRUPTED_HANDOFF.md',8.5)
text(20,7,'入口相对 docs/reports/；修订版未新增求解、阶段验收或物理验证。',9)
# Add slide/notes relationships and content type entries.
relsns='http://schemas.openxmlformats.org/package/2006/relationships';ctns='http://schemas.openxmlformats.org/package/2006/content-types'
def xmlbytes(r):return E.tostring(r,encoding='utf-8',xml_declaration=True)
r=E.fromstring(data['ppt/slides/_rels/slide15.xml.rels'])
for n in r:
 if n.get('Type','').endswith('/notesSlide'):n.set('Target','../notesSlides/notesSlide21.xml')
data['ppt/slides/_rels/slide21.xml.rels']=xmlbytes(r)
data['ppt/notesSlides/notesSlide21.xml']=data['ppt/notesSlides/notesSlide15.xml']
r=E.fromstring(data['ppt/notesSlides/_rels/notesSlide15.xml.rels'])
for n in r:
 if n.get('Type','').endswith('/slide'):n.set('Target','../slides/slide21.xml')
data['ppt/notesSlides/_rels/notesSlide21.xml.rels']=xmlbytes(r)
r=E.fromstring(data['[Content_Types].xml'])
for part,typ in [('slides/slide21.xml','slide'),('notesSlides/notesSlide21.xml','notesSlide')]:E.SubElement(r,'{'+ctns+'}Override',{'PartName':'/ppt/'+part,'ContentType':'application/vnd.openxmlformats-officedocument.presentationml.'+typ+'+xml'})
E.register_namespace('',ctns)
data['[Content_Types].xml']=xmlbytes(r)
r=E.fromstring(data['ppt/_rels/presentation.xml.rels']);rid='rId'+str(max(int(c.get('Id')[3:]) for c in r)+1)
E.SubElement(r,'{'+relsns+'}Relationship',{'Id':rid,'Type':NS['r']+'/slide','Target':'slides/slide21.xml'});data['ppt/_rels/presentation.xml.rels']=xmlbytes(r)
r=E.fromstring(data['ppt/presentation.xml']);lst=r.find('p:sldIdLst',NS);E.SubElement(lst,q('p:sldId'),{'id':str(max(int(c.get('id')) for c in lst)+1),q('r:id'):rid});new=lst[-1];lst.remove(new);lst.insert(15,new);data['ppt/presentation.xml']=xmlbytes(r)
ORDER=list(range(1,16))+[21]+list(range(16,21))
# Main speaker script, synchronized with native notes.
NOTES={
1:'老师好。今天汇报第一篇固定间隙、全充液单相矩形沟槽研究。重点说明已有发现、最近补证和仍未闭合的部分。论文的数值观察可以汇报，但目前还不能据此宣布原公式或 V2 已获正式精度验证。',
2:'先给结论：18 组几何的 36 个方向点上，原公式相对 5 nm 数值结果均高估导度。V2 降低整体最坏偏差，但有局部反例。平板、常规间隙网格和驱动力检查已通过；薄间隙横槽仍卡在网格门槛。今天新增的是 1.25 nm 数据收尾和 OpenFOAM 接入实现，没有新增动态流场。',
3:'h 是凸台与平壁之间最薄液层，d 是槽深。沿槽和横槽是两个不同驱动方向。K 表示薄膜导度，单位是立方米。同样驱动和黏度下，K 越大，流动阻力越小。研究对象是已经完全充液的固定结构，图中的工艺示意不代表本次模拟了完整压印。',
4:'先分清三个对象。原公式把深浅区按局部平板计算；OpenLB 按显式沟槽求通量；V2 在原公式上乘经验因子。修正因子没有显式 h，但总公式仍含 h。这里的误差是相对离散数值参考的偏差，不是实验误差或连续真解误差。两条原公式适用于本项目槽宽占周期一半的几何。',
5:'18 组是 18 种 h 与 d 的组合。h 等于 25 nm 时只有三种槽深，其他三档间隙各五种槽深，合计 18。每组沿槽、横槽各算一次，共 36 个方向点。未采样的两个几何不插值，也不当作已有结果。',
6:'历史 5 nm 数据显示，加深沟槽时沿槽导度变化更明显，横槽变化较小，因而各向异性增大。但某些端点来自不同历史程序组，几何作用与构建差异尚未完全分离，所以本页按描述性关系汇报，不作为严格的单因素因果结论。',
7:'36 个方向点上原公式都高估导度。沿槽最大偏差为 204.85%，横槽为 54.19%。这些数字的共同参照是 5 nm 离散结果。四个双网格几何显示，换参考网格会改变误差，但不能把这几个变化当作全部样本的误差上界。',
8:'V2 将沿槽最大绝对偏差降到 10.5%，横槽降到 18.7%。但 h25、d100 的横槽点在 5 nm 参考下反而变差，换成 2.5 nm 参考又变好。这说明局部判定依赖参考质量。扩展数据在模型选择时已可见，而且与程序分组交织，所以当前只称回顾性修正。',
9:'以 h75、d100 为例，原公式把各向异性从数值结果的 2.21 估成约 3.70。45 度驱动下，由两套主值重建的流向相差 9.20 度。这个角差是张量重建结果，还不是实际器件或实验流向误差。',
10:'S0 到 S4 是五组验证任务，不是又增加了五种样本几何。S0 是修复后的回归检查，S1 是平板，S2 是常规间隙三网格，S3 是驱动力控制，S4 是薄间隙三网格。前四组通过，S4 六条各自检查通过但横槽跨网格未通过。11 月 5 日新增的数据审查与 OpenFOAM 实现单独列出。',
11:'S1 用平板解析解检查所用配置，K 和速度剖面误差分别约 0.173% 与 0.079%。S2 在 h60、d80 的三网格检查中，两方向都满足该阶段要求。细网格下横槽阻力约为沿槽的 2.515 倍。但阶段检查通过与跨阶段正式参考资格是两回事。',
12:'在同一几何、同一网格下把驱动力跨度放到四倍，K 几乎不变，支持所测范围内的线性响应。右侧很小的跨度只说明驱动力敏感性小，不能解释成 K 精确到七八位。网格敏感性仍明显更大，也不是严格的真解误差界。',
13:'这是当前主要卡点。薄间隙 h30、d80 的六条运行都有结果，单条检查通过。但横槽从 2.5 nm 到 1.25 nm 的 K 仍变化 1.328%，超过事先规定的 1%。GCI 估计小于 1% 不能抵补另一项未通过。原 S4 失败保留，不能据此直接给 V2 判精度。',
14:'服务器上的 1.25 nm 已经完成，三维场和原始诊断也复核了。K 与本机在已保存精度下相同，满足预定构建等价判据。实际在第 12537 步首次满足收敛窗后停止，并非跑满最大步数。求解实测约两小时六分，峰值 1.526 GiB。三列诊断有极小差异，所以不能称全部数据逐位一致。它关闭本条构建复现问题，未关闭 S4 网格问题。',
15:'OpenFOAM 中本项目采用总 Darcy 阻力。因为 K 对应单位宽度薄膜通量，而求解器 U 是液体平均速度，二者通过平均液层厚度 H 联系，所以阻力系数是 H 除以 K。最小间隙 h 与平均厚度 H 要分清。本项目 H 等于 h 加槽宽占比乘槽深。新宿主同时接入间隙、储量变化和加权面通量，已编译并完成不求解审计，尚无新压力流场结果。',
21:'下一步拟用三个有解析答案的工况验收。A 退回旧固定间隙，B 检查改变间隙后的通量换算，C 用一个均匀闭合快照检查排液与储量。核心是从实际面通量积分 Q，从前后间隙重算储量，再核收支。0.25 秒只是拟议快照间隔，不是已运行时间，也不是实际工艺参数。边界处理、网格适配、独立检查器和执行包四项仍待完成。',
16:'当前能保留的是带条件的离散发现和回顾性评价。需要补证的是固定 V2 的新条件预测、薄间隙严格参考，以及真实压印压力和实验吻合。理论上界要保留理想 Stokes 假设，非严格上界不保证偏差大小或各向异性。不同程序分组与几何条件交织，也需要作为方法限制写清。',
17:'建议先把论文贡献保持在现有证据范围，保留反例和失败。请老师裁定后续投入：如果要走严格参考和独立预测路线，恢复 0.625 nm 准备审查；如果先完成平均模型使用链，就落实新宿主的受控流场验收。两条路线解决不同问题，不能互相替代。代码、检查和材料整理有 AI 辅助，我需要继续逐项理解和核对，由作者承担结论责任。',
18:'本页只在追问时打开。固定槽深后，误差随间隙的变化并非所有点都单调。以 d100 沿槽为例，四档间隙约为 139.14%、154.24%、144.95%、108.38%。因此不能把现象概括成越薄误差一定越大，也不能唯一归因于侧壁。',
19:'备查答案以证据范围为限。被问到是否必须继续 0.625 nm，要先说明论文主张：追求薄间隙严格参考需要继续补证；保持现有离散与回顾性主张时，不能把这项计算说成所有论文工作的唯一前提。现有材料也不等于可以直接投稿。',
20:'所有入口相对 docs/reports。详细 run_id、哈希、阈值和原始文件在相应报告中。下午修订版只整理和校正证据表述，没有启动求解、改变门槛或签发新的阶段验收。'
}
SOURCES={14:'URV_S4_TGE_1p25_data_audit_20261105_100521/REPORT.md\nrun_id=URV_S4_T_dx1p25_TGESRV_v1_20261104_01',15:'Groove_porosity_refresh_20261105/REPORT.md\nGroove_gap_host_integration_20261105/REPORT.md\nOpenFOAM_comparison_clarification_20261104/REPORT.md',21:'Groove_gap_flow_acceptance_plan_20261105/PLAN.md\nCHECKER_SPEC.md; PREREQUISITES.csv; analytic_expected.json\nformal_protocol_adopted=false; launch_ready=false; checker_implemented=false; run_id=null',16:'PAPER1_claim_evidence_review_20261105/REPORT.md',17:'URV_S4_TGE_0p625_readiness_review_20261105_100032/INTERRUPTED_HANDOFF.md'}
SOURCES.update({
1:'PAPER1_claim_evidence_review_20261105/REPORT.md',
2:'PAPER1_claim_evidence_review_20261105/REPORT.md; URV_S4_completed_review_20261104_143205/REPORT.md',
3:'SIM240_中文稿_导师审阅版_20261022.md，图1、§2.1',
4:'SIM240_中文稿_导师审阅版_20261022.md，§2.3、§4.4',
5:'SIM240_中文稿_导师审阅版_20261022.md，表1；PAPER1_claim_evidence_review_20261105/REPORT.md',
6:'PAPER1_claim_evidence_review_20261105/REPORT.md；中文稿图2',
7:'PAPER1_claim_evidence_review_20261105/REPORT.md；中文稿图4',
8:'PAPER1_claim_evidence_review_20261105/REPORT.md；recomputed_36_points.csv',
9:'PAPER1_claim_evidence_review_20261105/REPORT.md；中文稿表7与式5',
10:'URV_S1_results_review_20261102/REPORT.md；URV_S2_completed_review_20261103_095422/REPORT.md；URV_S3_completed_review_20261103_172033/REPORT.md；URV_S4_completed_review_20261104_143205/REPORT.md',
11:'URV_S1_results_review_20261102/REPORT.md；URV_S2_completed_review_20261103_095422/REPORT.md',
12:'URV_S3_completed_review_20261103_172033/REPORT.md',
13:'URV_S4_completed_review_20261104_143205/REPORT.md',
18:'PAPER1_claim_evidence_review_20261105/REPORT.md；中文稿图3',
19:'PAPER1_claim_evidence_review_20261105/REPORT.md；URV_S4_TGE_1p25_data_audit_20261105_100521/REPORT.md',
20:'本页列出的报告入口。'
})
script=['# 第一篇导师汇报：下午修订版逐页讲稿','', '正文 18 页，约 12—15 分钟；附录 3 页按需打开。若只讲 8 分钟：第 1—5、7—8、13—18 页，其余作备查。','', '开场 30 秒：原公式相对已有离散结果存在明显方向相关偏差，V2 总体改善但有反例；1.25 nm 已完成并复现 K，但薄间隙网格检查仍未通过。OpenFOAM 新宿主已实现间隙接入，实际压力—排液—储量验收还没有运行。','']
for pos,i in enumerate(ORDER,1):
 if i!=1:text(i,8,f'{pos} / 21',9)
 title=''.join(shape(i,4).findall('.//a:t',NS)[0].itertext()) if i!=1 else '纳米矩形沟槽的方向性输运'
 notes=NOTES[i]
 path=f'ppt/notesSlides/notesSlide{i}.xml';nr=E.fromstring(data[path]);body=None
 for sp in nr.findall('.//p:sp',NS):
  ph=sp.find('p:nvSpPr/p:nvPr/p:ph',NS)
  if ph is not None and ph.get('type')=='body':body=sp.find('p:txBody',NS);break
 if body is None:raise ValueError(('notes body missing',i))
 old='\n'.join(t.text or '' for t in body.findall('.//a:t',NS))
 for p in body.findall('a:p',NS):body.remove(p)
 for line in (notes+'\n\n证据入口（相对 docs/reports）：\n'+SOURCES[i]).split('\n'):body.append(runpara(line,12))
 data[path]=xmlbytes(nr)
 data[f'ppt/slides/slide{i}.xml']=xmlbytes(slides[i])
 script += [f'## 第 {pos} 页｜{title}','',notes,'']
 if i in SOURCES:script += ['证据：'+SOURCES[i].replace('\n','；'),'']
app=E.fromstring(data['docProps/app.xml']);apns='http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'
for n in app:
 if n.tag=='{'+apns+'}Slides':n.text='21'
data['docProps/app.xml']=xmlbytes(app)
with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in data.items():z.writestr(n,b)
(B/'下午汇报逐页讲稿.md').write_text('\n'.join(script),encoding='utf8')
(B/'制作记录/slide_order.json').write_text(json.dumps(ORDER))
print(OUT)
print('slides:',len(ORDER),'bytes:',OUT.stat().st_size)
