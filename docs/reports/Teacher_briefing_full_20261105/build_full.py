"""Local OOXML fallback: editable PPTX plus a static PDF from the same layout.

No solver, fitting, dependency installation, or source-result mutation.
The skill's Artifact Tool runtime is unavailable on this host.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import csv, hashlib, json, math, re, zipfile
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

ROOT=Path('/home/dell/yuanyuanxu/SIM240')
WORK=ROOT/'docs/reports/Teacher_briefing_full_20261105'
QA=WORK/'qa'
PPT=ROOT/'output/pptx/SIM240_Paper1_Full_Briefing_20261105.pptx'
PDF=ROOT/'output/pdf/SIM240_Paper1_Full_Briefing_20261105.pdf'
FONT='Noto Sans CJK SC'
FONTFILE='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
BOLD='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
INK='172B3A'; BLUE='155B83'; GRAY='526471'; RED='A43F29'; WHITE='FFFFFF'
W,H=1280,720
EMU=9525
for p in [QA,PPT.parent,PDF.parent]:p.mkdir(parents=True,exist_ok=True)

slides=[]
def slide(title,note,source='',takeaway=None):
    s={'title':title,'elements':[],'note':note,'source':source}
    slides.append(s)
    if takeaway:text(s,takeaway,64,578,1152,64,25,BLUE,True)
    return s
def text(s,value,x,y,w,h,size=27,color=INK,bold=False):
    s['elements'].append(dict(kind='text',text=value,x=x,y=y,w=w,h=h,size=size,color=color,bold=bold))
def table(s,headers,data,x=64,y=160,widths=None,row_h=64,size=25):
    widths=widths or [1152/len(headers)]*len(headers)
    s['elements'].append(dict(kind='table',rows=[headers]+data,x=x,y=y,w=sum(widths),h=row_h*(len(data)+1),widths=widths,row_h=row_h,size=size))
def picture(s,path,x,y,w,h,crop=None):
    s['elements'].append(dict(kind='image',path=str(ROOT/path),x=x,y=y,w=w,h=h,crop=crop))
def lines(s,items,y=160,gap=105,size=28):
    for i,(heading,body) in enumerate(items):
        text(s,heading,64,y+i*gap,1152,38,size,BLUE,True)
        text(s,body,64,y+i*gap+43,1152,gap-45,size-2)

# Existing verified content provides historical evidence, not new simulations.
old=json.loads((ROOT/'docs/reports/Teacher_briefing_20261029/slide_content.json').read_text())
MAN='docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
def reuse(i):
    s=json.loads(json.dumps(old[i]));slides.append(s)
    s['note']=s['note'].replace('本轮','前期整理时').replace('这两个参考值均已与原始result.txt逐项核对','前期报告已核对这两个参考值与原始result.txt')
    return s
s=reuse(0)
s['elements'][0]['text']='前期成果与本周验证进展'
s['elements'][1]['text']='固定间隙、全充液单相沟槽的阶段研究'
s['elements'][2]['text']='2026年11月5日  导师讨论稿  科学终审待完成'
s['note']='老师好，今天汇报单相沟槽研究的完整进展。先介绍研究对象、前期18组几何和主要发现，再讲本周补充的数值验证、薄间隙未通过项和下一步。前期成果与本周新增验证会分别说明。代码、分析与稿件整理有较多AI辅助，尚待作者理解核对和人工科学终审。'
reuse(1)
s=reuse(2);s['title']='沟槽几何与流动方向'
s['elements']=[e for e in s['elements'] if e['kind']!='table' and not (e['kind']=='text' and e['x']==610)]
text(s,'h：凸台顶面至上壁面的间隙\nd：槽深，槽内流体高度为 h+d\nw：槽宽，固定120 nm\nP：周期，固定240 nm',610,175,605,205,29)
text(s,'槽沿 y 延伸，沿槽对应 Kyy\n横槽为 x 方向，对应 Kxx',610,435,605,105,29,BLUE,True)
text(s,'固定间隙、全充液、无滑移',610,594,605,50,26,GRAY)
s['note']='h是凸台顶面到上壁面的间隙，d是槽深，所以槽内流体高度是h+d。槽宽120纳米，周期240纳米。沿槽为y，横槽为x。左图只截取已有原图的单胞剖面，不表示本研究已经模拟完整压印过程。'
s=slide('前期18组几何具体由哪些组合构成',
 '这里的组指间隙h和槽深d的一种组合。25纳米间隙只有三档槽深，其余三档间隙各五档槽深，合计18种。每种几何计算沿槽和横槽，共36个方向点。它不是完整的20种组合，未计算的两格不能补填。',MAN+' §2.1 表1')
table(s,['间隙 h / nm','已计算槽深 d / nm','几何数','方向点'],[
 ['25','25、50、100','3','6'],['50','25、50、75、100、120','5','10'],['75','25、50、75、100、120','5','10'],['125','25、50、75、100、120','5','10'],['合计','槽宽120 nm，周期240 nm','18','36']],y=160,widths=[210,542,190,210],row_h=65,size=25)
text(s,'h=25 nm时未计算 d=75、120 nm。几何数、方向点数和运行数分别计数。',64,588,1152,75,25,RED)
reuse(3);reuse(4);reuse(5);reuse(6);reuse(7);reuse(8);reuse(9);reuse(10)
s=slide('理论与机理解释的边界',
 '已有附录E在理想Stokes、固定全充液无滑移周期直槽等假设下，论证局部立方律对两个主导度给出非严格上界。这里沿用既有审查，不在汇报制作中重新终审。这个上界只限定大小关系，不能给出误差百分比，也不能推出各向异性偏差符号。侧壁和台阶流动是待检验的解释，尚未用耗散分解确定各自贡献。',MAN+' 附录E、§5.1；docs/reports/Appendix_E_final_review_20261028/REPORT.md')
lines(s,[('已有理论结论','在附录E的理想Stokes假设下，局部立方律给出两个主导度的上界。'),('成立前提','固定几何、全充液、无滑移、周期直槽；d=0时可以取等号。'),('不能直接推出','误差幅度、各向异性偏差的符号、数值离散误差界。'),('机制仍待验证','侧壁黏性作用及台阶流动重分布尚无定量耗散份额。')],gap=108,size=28)
s=reuse(11);s['title']='前期数值检查及其适用边界'
s['note']='这一页概括本周之前的证据，不把旧失败改判。历史平板检查、四组沟槽加密、基准周期复制及多力控制分别有适用范围。周期复制只检查周期构造一致性，不能证明改变实际结构周期后的物理尺度收敛。历史细横槽质量失败及来源限制保留。本周的新证据从后面单独介绍。'
s=slide('OpenFOAM已有静态接入与验证边界',
 '这部分计算在10月30日已有，本周核对其原始文件、接受记录和接口分工。C01到C04是原公式与V2乘两个方向，GDI01是实际grooveDarcy阻力源接入的一个V2横槽工况。它们将沟槽等效成阻力，没有逐条解析槽，也没有闭合运动。因此支持静态接入一致性，不能作为V2准确或挤压载荷精度的独立验证。', 'docs/reports/OpenFOAM_comparison_clarification_20261104/REPORT.md')
text(s,'既有计算：10月30日完成。本周：核对实际算例与证据。',64,148,1152,58,28,BLUE,True)
table(s,['工况','输入及方向','出口 Q / m³·s⁻¹'],[
 ['C01 / C02','V2：横槽 / 沿槽','2.18582e-18 / 4.99873e-18'],['C03 / C04','原公式：横槽 / 沿槽','3.12872e-18 / 1.15625e-17'],['GDI01','V2横槽，实际阻力源','2.18582e-18']],y=230,widths=[210,422,520],row_h=74,size=24)
text(s,'共同几何 h75/d100/w120/P240 nm。平均域24×48 μm，固定压差24 Pa。\n支持静态接入一致性，未逐槽解析，未验证动态挤压压力与载荷。',64,560,1152,100,25,RED)
s=slide('本周工作总览：11月2日至11月4日',
 '本周重点是补强数值参考证据，不是重新生成前期18组主地图。11月2日完成S0修复回归与S1平板。11月3日完成S2网格和S3驱动力。11月4日完成S4薄间隙结果复核，发现横槽网格未过，并准备补证材料。同时整理结论证据、OpenFOAM澄清和汇报稿。', 'docs/reports/PAPER1_本周进展_20261102_20261104.md；各阶段既有REPORT.md')
table(s,['日期','已完成的工作','结果'],[
 ['11月2日','S0修复回归、S1平板基准','通过相应验收'],['11月3日','S2三网格、S3三档驱动力','常规间隙检查通过'],['11月4日','S4薄间隙六条结果复核','横槽网格FAIL'],['11月4日','0.625 nm补证隔离准备','软件通过，未原生执行'],['本周整理','结论证据表、OpenFOAM澄清、讲稿','不等于新增流场结果']],y=160,widths=[190,607,355],row_h=76,size=25)
s=slide('S0与S1：修复回归及光滑平板基准',
 'S0检查质量观察量修复版本是否保留原有流动结果，两条新结果通过回归和专项验收，旧失败保留。S1去掉沟槽，用30纳米光滑平板与解析解比较。两方向导度相对误差约0.173%，速度剖面相对L2约0.079%，均小于原2%要求。它支持该平板基准，不能推断所有沟槽条件都达到同样精度。','docs/reports/URV_A1_S0_results_review_20261102/REPORT.md；docs/reports/URV_S1_results_review_20261102/REPORT.md')
lines(s,[('S0：修复版本的回归验收','h75/d100 nm，两方向。原流动轨迹保持，专项质量检查通过。'),('S1：光滑平板解析校准','h30/d0 nm，两方向，dx=1.25 nm。'),('S1结果','K相对误差约0.173%，速度剖面相对L2约0.079%，均通过原2%要求。'),('结论范围','支持该基准的数值实现；历史FAIL保留，复杂沟槽精度另查。')],gap=108,size=28)
s=slide('S2：常规间隙两方向三网格检查',
 '在间隙60纳米、槽深80纳米条件下，两方向各做5、2.5、1.25纳米三档网格，共六条。六条结果逐项接受，两方向网格门通过。细格沿槽和横槽导度如表，对应横槽阻力约为沿槽2.515倍。这里说的是本组条件；网格估计不等于严格误差界，也没有在本阶段评价V2。','docs/reports/URV_S2_completed_review_20261103_095422/REPORT.md')
text(s,'h60 / d80 / w120 / P240 nm，dx=5、2.5、1.25 nm，共六条',64,150,1152,60,28)
table(s,['方向','细网格 K / m³','中细变化','网格检查'],[
 ['沿槽 y','5.907331e-23','0.203234%','PASS'],['横槽 x','2.348907e-23','0.744252%','PASS']],y=260,widths=[210,432,260,250],row_h=85,size=27)
text(s,'该条件下：横槽阻力 / 沿槽阻力 ≈ 2.515',64,566,1152,55,32,BLUE,True)
text(s,'六条数值、几何、结果检查通过。未进行V2正式模型比较。',64,627,1152,40,23,GRAY)
s=slide('S3：常规间隙三档驱动力控制',
 '同一几何和2.5纳米网格，比较三档加速度。中档沿用S2原合同的两条结果，新增的是两方向各两个驱动力，共四条。检验的是提取导度是否随驱动力基本不变，两方向均通过原0.001门槛。常规间隙的网格和驱动力证据已齐，跨阶段参考资格和模型评分仍未做。','docs/reports/URV_S3_completed_review_20261103_172033/REPORT.md')
text(s,'h60/d80 nm，固定dx=2.5 nm，保持几何、物性和边界一致',64,150,1152,60,28)
table(s,['加速度 a / m·s⁻²','方向','证据来源'],[
 ['50000','沿槽、横槽','S3新增两条'],['100000','沿槽、横槽','复用S2中档两条'],['200000','沿槽、横槽','S3新增两条']],y=245,widths=[390,310,452],row_h=77,size=27)
text(s,'两方向导度相对极差均通过原0.001门槛。\nS2网格 + S3驱动力控制通过，参考资格与模型比较仍待做。',64,586,1152,82,26,BLUE,True)
s=slide('S4：薄间隙横槽网格未通过',
 '薄间隙h30/d80纳米的六条计算已完成，逐条数值、几何和结果检查通过。沿槽中细变化0.165%，通过。横槽中细变化1.328%，超过原1%上限，虽然GCI估计0.912%通过另一项，但原协议要求两项同时通过，所以S4阶段未通过。不能以单条稳态通过代替网格检查，也不能看到结果后改门槛。S5没有启动。','docs/reports/URV_S4_completed_review_20261104_143205/REPORT.md')
text(s,'h30/d80 nm，dx=5、2.5、1.25 nm，两方向共六条已完成',64,150,1152,60,28)
table(s,['方向','中细变化 ≤1%','细格GCI ≤1%','方向判定'],[
 ['沿槽','0.165169%','0.094321%','PASS'],['横槽','1.328387%','0.912233%','FAIL']],y=255,widths=[210,340,340,262],row_h=85,size=27)
text(s,'六条单条验收通过，但S4阶段未通过。S5未启动。',64,558,1152,60,30,RED,True)
text(s,'原两项网格门槛须同时满足。尚未唯一确定超差原因。',64,627,1152,40,25,GRAY)
s=slide('横槽补证：已准备，尚无新流场结果',
 '针对横槽未过，已准备只新增0.625纳米横槽点，与旧2.5和1.25纳米结果构成追加分支。原失败永久保留。输入、旧基准引用、来源和零步接口已隔离准备，15项软件测试通过。但实际初始化审计、性能标定和正式流场计算都没有执行。最新采用前审查要求修订资格衔接和资源规则，因此不能说补证协议已经最终冻结，也不能承诺运行时间。','docs/reports/URV_S4_TGE_preparation_20261104_152009/REPORT.md；docs/reports/URV_S4T_supplement_final_review_20261104/REPORT.md')
lines(s,[('最小补证方向','仅新增横槽dx=0.625 nm，引用旧2.5 / 1.25 nm证据，保留原FAIL。'),('已完成的准备','隔离输入、来源绑定、检查入口及资源材料，15项软件测试通过。'),('尚未执行','实际初始化审计、初态读回、性能标定、正式流场计算。'),('最新审查停点','资格衔接和资源规则需修订，尚未最终采用冻结，执行关闭。')],gap=108,size=28)
s=slide('当前证据能够支持哪些结论',
 '需要把四层证据分开。前期地图支持相对5纳米离散参考的偏差和回顾性修正评价。新常规条件已有网格和驱动力证据。OpenFOAM已有静态接入一致性。新条件V2准确性以及真实挤压压力载荷精度仍未评价。论文已有材料，不等于所有主张都已闭环。','docs/reports/PAPER1_claim_evidence_matrix_20261104/REPORT.md；当前共享状态与所引阶段报告')
table(s,['结论层次','当前状态'],[
 ['已有样本的偏差与方向性','可按5 nm离散参考和采样范围报告'],['V2对已有样本的修正','回顾性整体改善，局部存在恶化'],['常规间隙数值控制','S2网格、S3驱动力通过'],['V2新条件预测精度','参考资格和正式比较尚未完成'],['挤压压力 / 载荷 / 动态填充','无相应独立精度验证']],y=160,widths=[470,682],row_h=76,size=25)
s=slide('后续路线与请导师裁定的问题',
 '首先请老师确定论文主张范围。若以已有样本偏差和回顾性修正为主，仍需保留来源和离散参考限制，并由作者审查贡献是否充分。若要主张新条件预测，继续修订补证资格和资源规则，按授权完成所需证据，再固定V2比较。不能看完新结果重新调参数后称独立预测。若进一步主张挤压应用，则另外建立运动与守恒一致的压力载荷验证，不在这次汇报中默认启动。','docs/reports/PAPER1_claim_evidence_matrix_20261104/REPORT.md；docs/reports/URV_S4T_supplement_final_review_20261104/REPORT.md')
lines(s,[('请导师确定论文主张','已有样本的偏差与修正，还是进一步主张新条件独立预测？'),('若继续新条件预测','先修订补证与资源规则，补齐所需检查和参考资格，再固定模型比较。'),('薄间隙补证投入','是否继续追加资源？原FAIL保留，不承诺未经实测的完成时间。'),('应用扩展另立范围','若保留工艺预测主张，补瞬时挤压压力、载荷及独立参照。')],gap=108,size=28)
s=reuse(13);s['title']='AI参与、本人掌握与当前材料'
s['note']='代码、数据整理、分析和稿件起草有较多AI辅助，需要本人如实说明参与和理解程度。人工未核实的内容不能因多轮AI检查就说成人工验证。已有中英文审阅稿、主图、补充记录和本周证据，但没有达到投稿就绪。希望老师判断研究贡献与最优先补证，同时指导本人先掌握几何、公式和哪些结果。'
# Backup slides retain concrete group definitions and worked formula details.
s=slide('备查：验证组的参数与数量',
 'S编号表示验证任务，不表示18组几何。S0回归、S1平板、S2常规网格、S3常规驱动力、S4薄间隙网格；S5尚未启动。S3复用S2两条不能重复计为新增，网格和驱动力变化也不是新独立几何。','各S0—S4完成报告；原URV-v1阶段矩阵')
table(s,['组别','h / d，nm','变化条件','实际新增条数'],[
 ['S0回归','75 / 100','沿槽、横槽回归','2'],['S1平板','30 / 0','沿槽、横槽解析校准','2'],['S2网格','60 / 80','两方向 × 三网格','6'],['S3驱动力','60 / 80','两方向各增低、高档','4'],['S4网格','30 / 80','两方向 × 三网格','6']],y=160,widths=[215,210,497,230],row_h=73,size=25)
text(s,'0.625 nm补证仅准备，不计已完成运行。S5未启动。',64,628,1152,40,25,RED)
s=reuse(14);s['title']='备查：V2系数与具体代入'
s['note']=s['note'].replace('本轮arithmetic.json','前期arithmetic.json')
s=slide('备查：老师可能追问的问题',
 '如果被问现在能否投稿，回答还需确定主张和完成作者科学审查；新条件预测路线的参考资格和正式比较未完成。如果被问1.328%为何不能放过，回答1%是预定门槛，不能事后修改。OpenFOAM使用输入等效阻力，不能独立证明该阻力准确。若被问创新，不能只说各向异性，要说明指定范围的方向性偏差、后果和修正局限，并请老师结合文献评估。','docs/reports/PAPER1_PPT逐页讲稿_20261105.md；结论证据对照表')
lines(s,[('为什么不能把1.328%算通过？','1%是预定标准。后续可另立补证，但保留原失败。'),('OpenFOAM算过，为何还要验证？','静态接入一致性与等效阻力本身的准确性需要不同证据。'),('现在能否宣布论文完成？','新条件模型比较、人工科学审查与投稿准备尚未完成。'),('可能的研究贡献是什么？','指定样点的方向性偏差及其后果、经验修正的改善与局限。')],gap=108,size=28)
s=slide('备查：证据入口与工具说明',
 '科学结果以所列稿件和阶段原始证据索引为准，研究技能仅辅助组织和表述，不支持任何CFD结论。本次制作没有运行求解器、重新拟合或更改任何历史失败。所有页面有来源备注。','本次source_manifest.json；既有项目报告与前期arithmetic.json')
text(s,'前期科学内容：中文导师审阅稿 §2—6、附录E，补充表S1—S11\n本周验证：S0 / S1 / S2 / S3 / S4 各阶段完成复核报告\n补证停点：TGE准备A、S4T采用前终审报告\nOpenFOAM：20261104实际算例澄清报告',64,155,1152,210,27)
text(s,'本PPT制作仅整理既有证据，未新增仿真、拟合或科学验收。\nAI内部审查不等于人工科学终审。',64,405,1152,100,27,BLUE,True)
text(s,'研究工具：Kassis T. 等（2026），Scientific Agent Skills: A Library of\nProcedural Knowledge for Research Agents，arXiv:2609.00065。\n工具文献仅说明辅助流程，不作为本研究科学证据。',64,545,1152,110,23,GRAY)
assert len(slides)==28,len(slides)
# Record the exact source snapshots actually used; never bind future logs.
sources={}
for path in [MAN,'docs/reports/Teacher_briefing_20261029/slide_content.json','docs/reports/Teacher_briefing_20261029/arithmetic.json','docs/reports/PAPER1_claim_evidence_matrix_20261104/REPORT.md','docs/reports/URV_A1_S0_results_review_20261102/REPORT.md','docs/reports/URV_S1_results_review_20261102/REPORT.md','docs/reports/URV_S2_completed_review_20261103_095422/REPORT.md','docs/reports/URV_S3_completed_review_20261103_172033/REPORT.md','docs/reports/URV_S4_completed_review_20261104_143205/REPORT.md','docs/reports/URV_S4_TGE_preparation_20261104_152009/REPORT.md','docs/reports/URV_S4T_supplement_final_review_20261104/REPORT.md','docs/reports/OpenFOAM_comparison_clarification_20261104/REPORT.md']:
    sources[path]=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
for s in slides:
    for e in s['elements']:
        if e['kind']=='image':
            path=Path(e['path']);sources[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Use explicit exponent notation: the local CJK font lacks superscript-minus glyphs.
def safe_notation(value):
    for a,b in [('s⁻¹','s^(-1)'),('s⁻²','s^(-2)'),('10⁻²³','10^(-23)'),('10⁻²²','10^(-22)'),('10⁻²⁷','10^(-27)'),('K₀','K0')]:
        value=value.replace(a,b)
    return value
for s in slides:
    for e in s['elements']:
        if e['kind']=='text':e['text']=safe_notation(e['text'])
        elif e['kind']=='table':e['rows']=[[safe_notation(c) for c in row] for row in e['rows']]

# OOXML writer: all prose and tables are editable native PowerPoint objects.
NS='http://schemas.openxmlformats.org'
A=NS+'/drawingml/2006/main'; PN=NS+'/presentationml/2006/main'; RN=NS+'/officeDocument/2006/relationships'
REL=NS+'/package/2006/relationships'
def xml(s):return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+s).encode()
def rels(items):return xml('<Relationships xmlns="'+REL+'">'+''.join(f'<Relationship Id="{i}" Type="{RN}/{typ}" Target="{escape(target)}"/>' for i,typ,target in items)+'</Relationships>')
def xfrm(x,y,w,h):return f'<a:xfrm><a:off x="{round(x*EMU)}" y="{round(y*EMU)}"/><a:ext cx="{round(w*EMU)}" cy="{round(h*EMU)}"/></a:xfrm>'
def fill(c):return f'<a:solidFill><a:srgbClr val="{c}"/></a:solidFill>'
def paras(value,size,color,bold=False):
    result=[]
    for line in value.split('\n'):
        sz=round(size*75)
        result.append(f'<a:p><a:pPr algn="l"><a:lnSpc><a:spcPct val="110000"/></a:lnSpc><a:spcAft><a:spcPts val="300"/></a:spcAft></a:pPr><a:r><a:rPr lang="zh-CN" sz="{sz}" b="{int(bold)}">{fill(color)}<a:latin typeface="{FONT}"/><a:ea typeface="{FONT}"/><a:cs typeface="{FONT}"/></a:rPr><a:t xml:space="preserve">{escape(line)}</a:t></a:r><a:endParaRPr lang="zh-CN" sz="{sz}"/></a:p>')
    return ''.join(result)
def shape(e,idx):
    return f'<p:sp><p:nvSpPr><p:cNvPr id="{idx}" name="Text {idx}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr>{xfrm(e["x"],e["y"],e["w"],e["h"])}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t"/><a:lstStyle/>{paras(e["text"],e["size"],e["color"],e["bold"])}</p:txBody></p:sp>'
def tablexml(e,idx):
    grid=''.join(f'<a:gridCol w="{round(w*EMU)}"/>' for w in e['widths'])
    trs=[]
    for ri,row in enumerate(e['rows']):
        cells=[]
        for cell in row:
            bg=BLUE if ri==0 else ('EEF3F6' if ri%2 else WHITE)
            color=WHITE if ri==0 else INK
            cells.append(f'<a:tc><a:txBody><a:bodyPr wrap="square"/><a:lstStyle/>{paras(cell,e["size"],color,ri==0)}</a:txBody><a:tcPr marL="152400" marR="95250" marT="114300" marB="57150" anchor="ctr">{fill(bg)}<a:lnL w="6350">{fill(WHITE)}</a:lnL><a:lnR w="6350">{fill(WHITE)}</a:lnR><a:lnT w="6350">{fill(WHITE)}</a:lnT><a:lnB w="6350">{fill(WHITE)}</a:lnB></a:tcPr></a:tc>')
        trs.append(f'<a:tr h="{round(e["row_h"]*EMU)}">'+''.join(cells)+'</a:tr>')
    return f'<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="{idx}" name="Table {idx}"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="{round(e["x"]*EMU)}" y="{round(e["y"]*EMU)}"/><a:ext cx="{round(e["w"]*EMU)}" cy="{round(e["h"]*EMU)}"/></p:xfrm><a:graphic><a:graphicData uri="{A}/table"><a:tbl><a:tblPr firstRow="1" bandRow="1"/><a:tblGrid>{grid}</a:tblGrid>{"".join(trs)}</a:tbl></a:graphicData></a:graphic></p:graphicFrame>'
def imagebox(e):
    with Image.open(e['path']) as im:iw,ih=im.size
    if e.get('crop'):
        l,t,r,b=e['crop'];iw*=r-l;ih*=b-t
    scale=min(e['w']/iw,e['h']/ih);nw,nh=iw*scale,ih*scale
    return e['x']+(e['w']-nw)/2,e['y']+(e['h']-nh)/2,nw,nh
def picxml(e,idx,rid):
    x,y,w,h=imagebox(e)
    crop=''
    if e.get('crop'):
        l,t,r,b=e['crop'];crop=f'<a:srcRect l="{round(l*100000)}" t="{round(t*100000)}" r="{round((1-r)*100000)}" b="{round((1-b)*100000)}"/>'
    return f'<p:pic><p:nvPicPr><p:cNvPr id="{idx}" name="Source figure {idx}" descr="{escape(Path(e["path"]).name)}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="{rid}"/>{crop}<a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr>{xfrm(x,y,w,h)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>'
group='<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
media={}
def full_elements(s,i):
    title=dict(kind='text',text=s['title'],x=64,y=65 if i else 122,w=1152,h=64 if i else 180,size=42 if i else 55,color=INK,bold=True)
    foot=dict(kind='text',text=f'SIM240 单相研究阶段汇报   2026年11月5日                                             {i+1} / {len(slides)}',x=64,y=685,w=1152,h=24,size=15,color=GRAY,bold=False)
    return [title]+s['elements']+[foot]
with zipfile.ZipFile(PPT,'w',zipfile.ZIP_DEFLATED) as z:
    def put(path,content):z.writestr(path,content)
    overrides=[]
    def part(path,kind,data):
        put(path,data);overrides.append((path,kind))
    mainct='application/vnd.openxmlformats-officedocument.presentationml.'
    for i,s in enumerate(slides,1):
        sr=[('rId1','slideLayout','../slideLayouts/slideLayout1.xml'),('rId2','notesSlide',f'../notesSlides/notesSlide{i}.xml')]
        objects=[]
        for idx,e in enumerate(full_elements(s,i-1),2):
            if e['kind']=='text':objects.append(shape(e,idx))
            elif e['kind']=='table':objects.append(tablexml(e,idx))
            else:
                pth=e['path']
                if pth not in media:media[pth]='image'+str(len(media)+1)+'.png'
                rid='rId'+str(len(sr)+1);sr.append((rid,'image','../media/'+media[pth]));objects.append(picxml(e,idx,rid))
        doc=f'<p:sld xmlns:p="{PN}" xmlns:a="{A}" xmlns:r="{RN}"><p:cSld><p:bg><p:bgPr>{fill(WHITE)}<a:effectLst/></p:bgPr></p:bg><p:spTree>{group}{"".join(objects)}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'
        part(f'ppt/slides/slide{i}.xml',mainct+'slide+xml',xml(doc));put(f'ppt/slides/_rels/slide{i}.xml.rels',rels(sr))
        n={'text':s['note']+'\n\n来源：'+s['source']+'\n\n范围：原始记录算术核对或现行稿件说明；未新增求解、拟合或科学Gate验收。','x':64,'y':80,'w':1100,'h':580,'size':22,'color':INK,'bold':False}
        note_shape=shape(n,2).replace('<p:nvPr/>','<p:nvPr><p:ph type="body" idx="1"/></p:nvPr>',1)
        notes=f'<p:notes xmlns:p="{PN}" xmlns:a="{A}" xmlns:r="{RN}"><p:cSld><p:spTree>{group}{note_shape}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>'
        part(f'ppt/notesSlides/notesSlide{i}.xml',mainct+'notesSlide+xml',xml(notes));put(f'ppt/notesSlides/_rels/notesSlide{i}.xml.rels',rels([('rId1','slide',f'../slides/slide{i}.xml'),('rId2','notesMaster','../notesMasters/notesMaster1.xml')]))
    for path,name in media.items():put('ppt/media/'+name,Path(path).read_bytes())
    prs=f'<p:presentation xmlns:p="{PN}" xmlns:a="{A}" xmlns:r="{RN}"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:notesMasterIdLst><p:notesMasterId r:id="rId2"/></p:notesMasterIdLst><p:sldIdLst>'+''.join(f'<p:sldId id="{255+i}" r:id="rId{i+2}"/>' for i in range(1,len(slides)+1))+f'</p:sldIdLst><p:sldSz cx="{W*EMU}" cy="{H*EMU}" type="screen16x9"/><p:notesSz cx="6858000" cy="9144000"/><p:defaultTextStyle><a:defPPr><a:defRPr lang="zh-CN"><a:latin typeface="{FONT}"/><a:ea typeface="{FONT}"/></a:defRPr></a:defPPr></p:defaultTextStyle></p:presentation>'
    part('ppt/presentation.xml',mainct+'presentation.main+xml',xml(prs));put('ppt/_rels/presentation.xml.rels',rels([('rId1','slideMaster','slideMasters/slideMaster1.xml'),('rId2','notesMaster','notesMasters/notesMaster1.xml')]+[(f'rId{i+2}','slide',f'slides/slide{i}.xml') for i in range(1,len(slides)+1)]))
    cmap='<p:clrMap accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" bg1="lt1" bg2="lt2" folHlink="folHlink" hlink="hlink" tx1="dk1" tx2="dk2"/>'
    part('ppt/slideMasters/slideMaster1.xml',mainct+'slideMaster+xml',xml(f'<p:sldMaster xmlns:p="{PN}" xmlns:a="{A}" xmlns:r="{RN}"><p:cSld><p:spTree>{group}</p:spTree></p:cSld>{cmap}<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>'))
    put('ppt/slideMasters/_rels/slideMaster1.xml.rels',rels([('rId1','slideLayout','../slideLayouts/slideLayout1.xml'),('rId2','theme','../theme/theme1.xml')]))
    part('ppt/slideLayouts/slideLayout1.xml',mainct+'slideLayout+xml',xml(f'<p:sldLayout xmlns:p="{PN}" xmlns:a="{A}" xmlns:r="{RN}" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree>{group}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>'))
    put('ppt/slideLayouts/_rels/slideLayout1.xml.rels',rels([('rId1','slideMaster','../slideMasters/slideMaster1.xml')]))
    part('ppt/notesMasters/notesMaster1.xml',mainct+'notesMaster+xml',xml(f'<p:notesMaster xmlns:p="{PN}" xmlns:a="{A}" xmlns:r="{RN}"><p:cSld><p:spTree>{group}</p:spTree></p:cSld>{cmap}<p:notesStyle/></p:notesMaster>'))
    put('ppt/notesMasters/_rels/notesMaster1.xml.rels',rels([('rId1','theme','../theme/theme1.xml')]))
    colors={'dk1':INK,'lt1':WHITE,'dk2':GRAY,'lt2':'EEF3F6','accent1':BLUE,'accent2':'A96A13','accent3':'2C785C','accent4':'775B91','accent5':'557E90','accent6':RED,'hlink':'0563C1','folHlink':'954F72'}
    clr=''.join(f'<a:{k}><a:srgbClr val="{v}"/></a:{k}>' for k,v in colors.items())
    fnt=''.join(f'<a:{kind}Font><a:latin typeface="{FONT}"/><a:ea typeface="{FONT}"/><a:cs typeface="{FONT}"/></a:{kind}Font>' for kind in ['major','minor'])
    solid='<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    fmt=f'<a:fmtScheme name="Simple"><a:fillStyleLst>{solid*3}</a:fillStyleLst><a:lnStyleLst>'+''.join(f'<a:ln w="{v}">{solid}<a:prstDash val="solid"/></a:ln>' for v in [6350,12700,19050])+f'</a:lnStyleLst><a:effectStyleLst>{"<a:effectStyle><a:effectLst/></a:effectStyle>"*3}</a:effectStyleLst><a:bgFillStyleLst>{solid*3}</a:bgFillStyleLst></a:fmtScheme>'
    part('ppt/theme/theme1.xml','application/vnd.openxmlformats-officedocument.theme+xml',xml(f'<a:theme xmlns:a="{A}" name="SIM240"><a:themeElements><a:clrScheme name="Research">{clr}</a:clrScheme><a:fontScheme name="Noto CJK">{fnt}</a:fontScheme>{fmt}</a:themeElements></a:theme>'))
    put('_rels/.rels',rels([('rId1','officeDocument','ppt/presentation.xml'),('rId2','metadata/core-properties','docProps/core.xml')]).replace((RN+'/metadata/core-properties').encode(),(NS+'/package/2006/metadata/core-properties').encode()))
    part('docProps/core.xml','application/vnd.openxmlformats-package.core-properties+xml',xml('<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>SIM240 第一篇导师阶段汇报</dc:title><dc:description>AI辅助整理；以5nm离散参考为基准；尚未投稿就绪</dc:description></cp:coreProperties>'))
    ctypes='<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>'+''.join(f'<Override PartName="/{path}" ContentType="{kind}"/>' for path,kind in overrides)+'</Types>'
    put('[Content_Types].xml',xml(ctypes))

# Same layout, local preview/PDF; no generated scientific illustrations.
SCALE=1.5
fontcache={}
def font(size,bold=False):
    k=(size,bold)
    if k not in fontcache:fontcache[k]=ImageFont.truetype(BOLD if bold else FONTFILE,round(size*SCALE),index=2)
    return fontcache[k]
def wrap(value,ft,max_width):
    out=[]
    for para in value.split('\n'):
        cur=''
        for c in para:
            if cur and ft.getlength(cur+c)>max_width:out.append(cur);cur=c
            else:cur+=c
        out.append(cur)
    return out
fit=[]
def drawtext(draw,value,box,size,color,bold=False,center=False):
    x,y,w,h=box;ft=font(size,bold);ls=wrap(value,ft,w*SCALE)
    lineh=math.ceil(size*1.10+4)*SCALE
    required=(len(ls)-1)*lineh+size*SCALE*1.3
    if required>h*SCALE+2:fit.append({'text':value,'height':h,'required':required/SCALE})
    if center:y+=(h-required/SCALE)/2
    for i,line in enumerate(ls):draw.text((x*SCALE,(y+i*lineh/SCALE)*SCALE),line,font=ft,fill='#'+color,anchor='lt')
images=[]
for i,s in enumerate(slides):
    im=Image.new('RGB',(round(W*SCALE),round(H*SCALE)),'#'+WHITE);dr=ImageDraw.Draw(im)
    for e in full_elements(s,i):
        if e['kind']=='text':drawtext(dr,e['text'],(e['x'],e['y'],e['w'],e['h']),e['size'],e['color'],e['bold'])
        elif e['kind']=='image':
            pic=Image.open(e['path']).convert('RGB')
            if e.get('crop'):
                l,t,r,b=e['crop'];pic=pic.crop((int(pic.width*l),int(pic.height*t),int(pic.width*r),int(pic.height*b)))
            x,y,w,h=imagebox(e);pic=pic.resize((round(w*SCALE),round(h*SCALE)),Image.Resampling.LANCZOS);im.paste(pic,(round(x*SCALE),round(y*SCALE)))
        else:
            for ri,row in enumerate(e['rows']):
                x=e['x'];y=e['y']+ri*e['row_h']
                for ci,cell in enumerate(row):
                    width=e['widths'][ci];bg=BLUE if ri==0 else ('EEF3F6' if ri%2 else WHITE)
                    dr.rectangle((x*SCALE,y*SCALE,(x+width)*SCALE,(y+e['row_h'])*SCALE),fill='#'+bg,outline='white',width=2)
                    drawtext(dr,cell,(x+16,y+12,width-26,e['row_h']-18),e['size'],WHITE if ri==0 else INK,ri==0,center=True);x+=width
    im.save(QA/f'slide-{i+1:02}.png');images.append(im)
images[0].save(PDF,'PDF',save_all=True,append_images=images[1:],resolution=144.0,title='SIM240 第一篇导师阶段汇报',author='AI-assisted research briefing')
mont=Image.new('RGB',(4*480,math.ceil(len(images)/4)*270),'#D9E1E6')
for i,im in enumerate(images):mont.paste(im.resize((480,270)),((i%4)*480,(i//4)*270))
mont.save(QA/'contact_sheet.png')
if fit:(QA/'text_fit_findings.json').write_text(json.dumps(fit,ensure_ascii=False,indent=2))
notes=['# 第一篇导师汇报逐页讲稿','', '第1—24页为完整汇报，约18—22分钟；第25—28页备查。前期主地图采用5nm离散参考，本周各阶段按各自网格与协议说明。' ,'']
for i,s in enumerate(slides,1):
    notes += [f'## 第{i}页：'+s['title'].replace('\n',''),' ',s['note'],'', '证据入口：'+s['source'],'']
(WORK/'完整汇报逐页讲稿.md').write_text('\n'.join(notes))
(WORK/'slide_content.json').write_text(json.dumps(slides,ensure_ascii=False,indent=2))
(WORK/'source_manifest.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2))
checked={}
with zipfile.ZipFile(PPT) as z:
    for n in z.namelist():
        if n.endswith('.xml') or n.endswith('.rels'):ET.fromstring(z.read(n))
    checked['slide_count']=len([n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+.xml',n)])
    checked['native_table_count']=sum(z.read(n).count(b'<a:tbl>') for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+.xml',n))
    checked['notes_count']=len([n for n in z.namelist() if re.fullmatch(r'ppt/notesSlides/notesSlide\d+.xml',n)])
checked.update({'source_hashes_unchanged':all(hashfile(ROOT/k)==v for k,v in sources.items()),'local_text_fit_findings':fit,'runtime':'stdlib OOXML fallback; artifact-tool unavailable','pdf':'raster companion from same layout, not a PowerPoint-rendered PDF','pptx_sha256':hashfile(PPT),'pdf_sha256':hashfile(PDF),'no_solver_or_fit_run':True,'scientific_gates_unchanged':True})
(WORK/'verification.json').write_text(json.dumps(checked,ensure_ascii=False,indent=2))
print(json.dumps({'pptx':str(PPT),'pdf':str(PDF),'slides':len(slides),'fit_findings':fit},ensure_ascii=False,indent=2))
