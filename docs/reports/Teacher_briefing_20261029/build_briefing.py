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
WORK=ROOT/'docs/reports/Teacher_briefing_20261029'
QA=WORK/'qa'
PPT=ROOT/'output/pptx/SIM240_Paper1_Teacher_Briefing_20261029.pptx'
PDF=ROOT/'output/pdf/SIM240_Paper1_Teacher_Briefing_20261029.pdf'
FONT='Noto Sans CJK SC'
FONTFILE='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
BOLD='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
INK='172B3A'; BLUE='155B83'; GRAY='526471'; RED='A43F29'; WHITE='FFFFFF'
W,H=1280,720
EMU=9525
for p in [QA,PPT.parent,PDF.parent]:p.mkdir(parents=True,exist_ok=True)

inventory=ROOT/'docs/reports/SIM240_Supplementary_Methods_20261024/Table_S1_run_inventory.csv'
rows=list(csv.DictReader(inventory.open()))
main=[r for r in rows if r['group']=='main']
assert len(main)==36
evidence=[]
sources={}
def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_result(path):
    p=ROOT/path
    sources[str(p.relative_to(ROOT))]=hashfile(p)
    return dict(line.strip().split('=',1) for line in p.read_text().splitlines() if '=' in line)
def calc(r):
    raw=read_result(r['result_path'])
    ref=float(raw['Keff_m3'])
    assert math.isclose(ref,float(r['K_m3']),rel_tol=1e-13)
    h,d,w=float(r['h_nm'])*1e-9,float(r['d_nm'])*1e-9,120e-9
    para=r['direction']=='parallel'
    mod=(h**3+(h+d)**3)/24 if para else h**3*(h+d)**3/(6*(h**3+(h+d)**3))
    f=1/(1+1.7685*(d/w)**1.6331) if para else 1/(1+.4900*(d/w)**.6990)
    return dict(run_id=r['run_id'],h_nm=int(r['h_nm']),d_nm=int(r['d_nm']),direction=r['direction'],
                ref=ref,model=mod,F=f,corrected=f*mod,E_pct=100*(mod/ref-1),r_pct=100*(f*mod/ref-1),
                recorded_PASS=raw.get('PASS'),result_path=r['result_path'])
for r in main:evidence.append(calc(r))
ex={r['direction']:r for r in evidence if r['h_nm']==75 and r['d_nm']==100}
p,t=ex['parallel'],ex['perpendicular']
P=[r for r in evidence if r['direction']=='parallel'];T=[r for r in evidence if r['direction']=='perpendicular']
assert all(r['E_pct']>0 for r in evidence)
assert sum(abs(r['r_pct'])>abs(r['E_pct']) for r in evidence)==1
stats={
 'main_points':len(evidence),'geometries':len({(r['h_nm'],r['d_nm']) for r in evidence}),
 'parallel_error_range':[min(r['E_pct'] for r in P),max(r['E_pct'] for r in P)],
 'perpendicular_error_range':[min(r['E_pct'] for r in T),max(r['E_pct'] for r in T)],
 'max_abs_residual_parallel':max(abs(r['r_pct']) for r in P),
 'max_abs_residual_perpendicular':max(abs(r['r_pct']) for r in T),
 'max_abs_residual_perpendicular_hge50':max(abs(r['r_pct']) for r in T if r['h_nm']>=50),
 'anisotropy_reference':p['ref']/t['ref'],'anisotropy_model':p['model']/t['model'],
 'flow_angle_reference_deg':math.degrees(math.atan(t['ref']/p['ref'])),
 'flow_angle_model_deg':math.degrees(math.atan(t['model']/p['model'])),
}
for direction in ['parallel','perpendicular']:
    a=next(r for r in evidence if r['h_nm']==50 and r['d_nm']==25 and r['direction']==direction)
    b=next(r for r in evidence if r['h_nm']==50 and r['d_nm']==120 and r['direction']==direction)
    stats['h50_depth_gain_'+direction]=b['ref']/a['ref']
sources[str(inventory.relative_to(ROOT))]=hashfile(inventory)
MAN='docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
sources[MAN]=hashfile(ROOT/MAN)
for f in ['Fig1_device_and_unitcell.png','Fig4_K_and_anisotropy.png','Fig8_error_map.png']:
    q=ROOT/'figures/paper'/f;sources[str(q.relative_to(ROOT))]=hashfile(q)
(WORK/'arithmetic.json').write_text(json.dumps({'example':ex,'stats':stats,'all_main_points':evidence},ensure_ascii=False,indent=2))

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

s=slide('矩形沟槽中的方向性输运\n与局部立方律偏差',
 '老师，我汇报第一篇的阶段性材料。重点是固定几何、全充液条件下，简化模型与显式数值结果的比较。大量技术工作使用AI辅助，今天请您判断研究贡献与下一步补证重点。',MAN)
text(s,'第一篇文章阶段汇报',64,348,1100,52,34,BLUE,True)
text(s,'以5 nm离散数值结果为参考的模型比较',64,424,1120,56,31)
text(s,'2026年10月29日｜导师讨论稿｜作者最终科学审定待完成',64,550,1152,55,23,GRAY)

s=slide('研究问题与第一篇的范围',
 '大尺度压印模型通常需要简化沟槽输运。本文检查局部平板组合给出的系数，与显式解析沟槽的数值结果相差多少。固定、全充液是研究前提；动态下压和液气填充不在本篇范围。',MAN+' §1.1—1.3')
lines(s,[('工程背景','大尺度模型需要用等效通流系数代替逐条纳米沟槽。'),('本文问题','常用简化公式对沿槽、跨槽两个方向分别偏多少？'),('研究条件','固定间隙、全充液、牛顿液体、无滑移、周期直槽。'),('范围边界','尚未验证动态下压、自由表面、润湿、困气与真实树脂流变。')],gap=108)

s=slide('计算几何与参数范围',
 '左侧只展示原图1(b)的截面，完整原图保持不变。h是凸台下最薄间隙，d是槽深，深区总高度是h+d。槽沿y延伸；沿槽为yy，跨槽为xx。右表是18种几何，分别算两个方向，共36个主方向样点；不是36种几何。',MAN+' §2.1、表1；原图1(b)截面选区')
picture(s,'figures/paper/Fig1_device_and_unitcell.png',64,145,500,435,crop=(.025,.405,.47,.98))
text(s,'原图1(b)截面；仅展示计算单胞',64,590,500,40,20,GRAY)
table(s,['间隙 h / nm','槽深 d / nm'],[['25','25、50、100'],['50 / 75 / 125','25、50、75、100、120']],x=610,y=175,widths=[210,390],row_h=75,size=23)
text(s,'周期240 nm；槽宽120 nm\n沿槽 y → Kyy；跨槽 x → Kxx\n18种几何 × 2方向 = 36个样点',610,435,605,145,27)
text(s,'OpenLB单相稳态求解；x/y周期边界',610,604,605,48,24,GRAY)
s['note']+=' 求解采用OpenLB D3Q19、带Guo体力的BGK模型，固壁使用Bouzidi边界；τ=1。细节按现行方法章节核对，不把方法名称当作精度保证。'

s=slide('公式按用途区分',
 '不要把所有公式都叫成我们提出的公式。平板解析式来自已有理论；局部立方律是被检验的已有模型；OpenLB先求流场，再提取数值参考；V2是数据标定的经验修正；偏差公式只是比较指标。',MAN+' §2.2—2.3、§3.2、§4.4')
table(s,['类别','表达或来源','用途'],[
 ['平板解析基准','K₀ = h³ / 12','检查简单几何的数值实现'],
 ['局部立方律','Kmod：由 h、d 直接计算','被检验的简化模型'],
 ['数值参考','Kref = μJ / G；J来自流场','指定网格下的比较基准'],
 ['V2经验修正','Kcorr = F × Kmod','评价已有样点的改善'],
 ['偏差指标','E = Kmod / Kref − 1','判断高估、低估及幅度']
],widths=[240,455,457],row_h=73,size=24)

s=slide('局部立方律：沿槽与跨槽',
 '浅区按h立方除以12，深区按h加d的立方除以12。等宽条件下，沿槽取算术平均，跨槽取调和平均。它没有显式解析侧壁和台阶附近的完整流动；仅凭这一点不能断言哪个机制贡献最大。',MAN+' §2.3、式(3)')
text(s,'浅区：h³ / 12     深区：(h+d)³ / 12',64,150,1152,56,33)
text(s,'沿槽 yy：深区、浅区并行输送',64,250,1152,45,28,BLUE,True)
text(s,'Kyy mod = [ h³ + (h+d)³ ] / 24',64,307,1152,60,36)
text(s,'跨槽 xx：液体依次通过深浅区',64,410,1152,45,28,BLUE,True)
text(s,'Kxx mod = h³(h+d)³ / { 6[ h³+(h+d)³ ] }',64,467,1152,65,34)
text(s,'适用于当前等宽条纹；K单位为m³，尺寸代入前需换为米。',64,590,1152,48,23,GRAY)

s=slide('真实示例：原模型与数值参考',
 f'选用h75、d100的基准几何。浅区75纳米，深区175纳米。沿槽原模型算出24.08854，原始结果给9.83408，单位均为10的负23次方立方米；比值减1得到高估144.95%。跨槽同样计算得到高估46.51%。这两个参考值均已与原始result.txt逐项核对。',
 'h75_d100_dx5_P/T/steady/result.txt；'+MAN+' 式(3)—(4)',
 '同一几何中，沿槽与跨槽的模型偏差幅度不同。')
text(s,'h = 75 nm；d = 100 nm；w = 120 nm；网格 = 5 nm',64,142,1152,55,29)
table(s,['方向','原模型 Kmod','数值参考 Kref','相对偏差 E'],[
 ['沿槽 yy',f'{p["model"]/1e-23:.5f}',f'{p["ref"]/1e-23:.5f}',f'+{p["E_pct"]:.2f}%'],
 ['跨槽 xx',f'{t["model"]/1e-23:.5f}',f'{t["ref"]/1e-23:.5f}',f'+{t["E_pct"]:.2f}%']
],y=245,widths=[235,300,310,307],row_h=82,size=28)
text(s,'K统一以10⁻²³ m³表示；E = (Kmod / Kref − 1) × 100%',64,515,1152,52,25,GRAY)

s=slide('同一示例：经验修正与剩余偏差',
 '在同一个例子中，d除以w为0.83333。把它代入V2经验关系，得到沿槽修正因子0.43232、跨槽0.69863。用原模型乘修正因子，再与同一个参考比较，残差分别为正5.90%和正2.35%。这说明本例改善，不代表任意几何都改善，更不是实验精度。',
 '原始h75_d100_dx5_P/T结果；'+MAN+' 式(4)、式(6)',
 '本例改善明显；结论限定于该几何与5 nm数值参考。')
text(s,'d/w = 100/120 = 0.83333；Kcorr = F × Kmod',64,145,1152,55,30)
table(s,['方向','因子 F','修正值 Kcorr','修正后残差'],[
 ['沿槽 yy',f'{p["F"]:.5f}',f'{p["corrected"]/1e-23:.5f}',f'+{p["r_pct"]:.2f}%'],
 ['跨槽 xx',f'{t["F"]:.5f}',f'{t["corrected"]/1e-23:.5f}',f'+{t["r_pct"]:.2f}%']
],y=245,widths=[235,250,350,317],row_h=82,size=28)
text(s,'K单位：10⁻²³ m³；残差 = (Kcorr / Kref − 1) × 100%',64,515,1152,50,25,GRAY)

s=slide('成果一：增加槽深的收益具有方向差异',
 '原图左侧为两个方向的通流系数，右侧为各向异性，右图纵轴是对数。以h50为例，槽深从25增加到120，沿槽系数变成3.55倍，跨槽仅1.034倍。结论限定于已采样条件，不把趋势直接当作某个耗散机制的定量证明。',
 '36个主方向原始result.txt；现行正文图2、表5')
picture(s,'figures/paper/Fig4_K_and_anisotropy.png',64,150,1152,395)
text(s,'h = 50 nm，d：25 → 120 nm',64,569,600,42,27,BLUE,True)
text(s,f'沿槽：{stats["h50_depth_gain_parallel"]:.2f}倍     跨槽：{stats["h50_depth_gain_perpendicular"]:.3f}倍',64,619,1152,42,30)

s=slide('成果二：36个样点相对数值参考均高估',
 '热图中的斜线格是没有计算的几何，不填补或插值。沿槽偏差10.30%至204.85%，跨槽8.11%至54.19%。两幅图色标不同，不能跨图只比颜色深浅；这里高估是相对于5纳米离散参考。',
 '36个主方向原始result.txt；现行正文图4、表6')
picture(s,'figures/paper/Fig8_error_map.png',64,145,1152,410)
text(s,'沿槽：+10.30% ～ +204.85%   ｜   跨槽：+8.11% ～ +54.19%',64,572,1152,54,29,BLUE,True)
text(s,'斜线格：未计算；两个面板采用不同色标；参考网格均为5 nm。',64,632,1152,35,22,GRAY)

s=slide('成果三：主值偏差影响各向异性与流向',
 '各向异性是沿槽系数除以跨槽系数。基准几何下，数值结果为2.21，原模型为3.70。45度驱动时，由两组主值在同一线性张量关系下重建的流向分别24.34度和15.14度，相差9.20度。这不是实验测得的流向偏差，也不是新做的45度仿真。',
 'h75_d100_dx5_P/T/steady/result.txt；'+MAN+' §4.3、式(5)',
 '模型评价需要同时检查两个主值、比值与流向。')
text(s,'基准几何：h = 75 nm，d = 100 nm',64,145,1152,48,29)
table(s,['比较量','数值主值重建','局部立方律'],[
 ['各向异性 Kyy / Kxx',f'{stats["anisotropy_reference"]:.2f}',f'{stats["anisotropy_model"]:.2f}'],
 ['45°驱动下的通量角',f'{stats["flow_angle_reference_deg"]:.2f}°',f'{stats["flow_angle_model_deg"]:.2f}°']
],y=240,widths=[492,330,330],row_h=82,size=27)
text(s,'角度均从槽轴量起；tan β = (Kxx / Kyy) tan θ',64,515,1152,50,25,GRAY)

s=slide('成果四：V2降低整体最坏偏差，也有局部失效',
 '按现行稿件公布的舍入系数，重新计算36点残差。沿槽最坏绝对残差10.5%，跨槽全18点18.7%，只有h大于等于50的15个跨槽点才是6.9%。h25、d100的跨槽点从正16.36%变为负18.71%，绝对偏差变大。这是回顾性评价，扩展数据在选择模型时已经可见，不能叫独立预测精度。',
 '36个主方向原始result.txt；'+MAN+' §4.4、表8')
table(s,['样点范围','原始最大绝对偏差','V2最大绝对残差'],[
 ['沿槽：18点','204.85%','10.5%'],['跨槽：18点','54.19%','18.7%'],['跨槽：h≥50 nm，15点','54.19%','6.9%']
],y=155,widths=[480,350,322],row_h=75,size=26)
text(s,'局部失效：h = 25 nm，d = 100 nm，跨槽',64,503,1152,45,27,RED,True)
text(s,'偏差由 +16.36% 变为 −18.71%；绝对偏差反而增大。',64,557,1152,52,27)
text(s,'V2属于已有数据的回顾性经验修正；新几何预测能力尚未建立。',64,622,1152,40,23,GRAY)

s=slide('数值证据与尚未闭合的限制',
 '平板三网格基准与复杂沟槽精度要分开。四个沟槽几何做双网格比较，最薄间隙跨槽变化约负4.43%，不是所有点统一误差上界。周期复制检查的是实现一致性，不是物理代表性尺度。历史细横槽质量FAIL仍保留。完整历史构建绑定与实验验证未完成。',
 MAN+' §2.4、§3；补充S7—S10')
table(s,['证据项目','现有记录','适用边界'],[
 ['平板解析基准','三网格偏差：0.444%→0.0272%','仅平直壁配置'],
 ['沟槽网格加密','4个几何；最薄跨槽变化−4.43%','不是全图误差界'],
 ['周期复制、多力检查','基准几何的一致性检查','不是RVE或逐点线性证明'],
 ['历史细横槽','质量审计FAIL记录保留','不能按正常退出改判'],
 ['来源与物理验证','部分历史构建绑定待补；无实验对照','不宣称真实工艺预测精度']
],widths=[265,485,402],row_h=76,size=23)

s=slide('论文贡献与结论边界',
 '沟槽有各向异性本身不是创新。当前可讨论的贡献是，给出指定几何和分辨率下，常用近似的方向性偏差、各向异性后果和经验修正的局限。附录E在理想Stokes模型下论证主导度上界，但不提供偏差幅度、机制份额或真实工艺精度。论文的新颖性和是否足够发表，需要老师结合已有文献判断。',
 MAN+' §1.2、§5—6、附录E')
lines(s,[('可讨论的贡献','指定样点下的方向性偏差地图，以及对各向异性与流向的影响。'),('经验关系的价值','展示修正的整体改善、局部失效及适用范围。'),('理论解释的范围','理想Stokes假设下的主导度上界；不提供偏差幅度和机制份额。'),('仍需导师判断','科学新意是否充分；哪些结论保留；哪些验证必须补充。')],gap=108)

s=slide('AI参与、当前材料与导师讨论重点',
 '我需要如实说明代码、数据整理、分析和稿件起草大量使用AI。本人理解程度和人工复核范围由本人说明，不把多轮AI检查称作独立人工验证。已有中英文审阅稿和四图，但尚未投稿就绪。希望老师判断问题价值、应保留的结论和最优先的一项验证；后续计算范围另定。',
 'docs/reports/SIM240_AI_CONTEXT.md；当前稿件与用户本轮说明')
lines(s,[('AI使用情况','代码、数据整理、分析和稿件起草大量使用AI辅助。'),('本人需要如实说明','哪些原理已掌握、哪些结果亲自复核、哪些仍不能独立解释。'),('当前材料状态','中英文审阅稿、四张主图、补充表与记录已整理；尚未投稿就绪。'),('请导师裁定','研究价值与保留主张；最优先补的验证；本人先掌握哪部分。')],gap=108)

s=slide('备查：V2系数与具体代入过程',
 '这一页用于老师追问，不必在主讲中逐字念。V2系数来自现有拟合，未做本轮重新拟合。尺寸之比d/w无量纲。沿槽原模型的纳米立方结果为240885.4167，再乘10的负27次方换为立方米。先算F，再乘原模型，再除同一个数值参考减1。',
 MAN+' §2.3、§4.4；本轮arithmetic.json')
text(s,'Fyy = 1 / [ 1 + 1.7685 (d/w)^1.6331 ]',64,150,1152,65,33)
text(s,'Fxx = 1 / [ 1 + 0.4900 (d/w)^0.6990 ]',64,230,1152,65,33)
text(s,'本例沿槽：[(75)³ + (175)³] / 24 × 10⁻²⁷',64,335,1152,55,30)
text(s,'= 2.408854 × 10⁻²² m³',64,400,1152,55,32,BLUE,True)
text(s,'修正：0.432322 × 2.408854 × 10⁻²² = 1.041401 × 10⁻²² m³',64,485,1152,60,27)
text(s,'残差：(10.41401 / 9.83408 − 1) ×100% = +5.90%\n（两个K均以10⁻²³ m³表示）',64,560,1152,100,25)

s=slide('备查：证据入口与研究工具说明',
 '所有主方向数值已由本轮脚本读取原始result.txt并与表S1核对。其余验证覆盖和限制沿用现行稿件，本轮没有新增仿真或人工科学验收。AI及技能只辅助组织与算术核对，不作为科学有效性的证据。',
 '本轮source_manifest.json、arithmetic.json；Kassis等工具文献已核arXiv页面')
text(s,'科学内容与原始数据',64,145,1152,42,29,BLUE,True)
text(s,'现行中文导师审阅稿：§2—6、附录E\n补充材料：表S1运行索引、S2加密、S4—S5归档网格证据\n示例：h75_d100_dx5_P/T → steady/result.txt',64,203,1152,175,26)
text(s,'工具辅助说明',64,405,1152,42,29,BLUE,True)
text(s,'AI辅助整理与表达；本轮从原始记录复算模型值、偏差和V2残差。\n未运行求解器、重新拟合或改变历史PASS/FAIL。',64,461,1152,105,25)
text(s,'Kassis T. 等（2026）Scientific Agent Skills: A Library of Procedural Knowledge\nfor Research Agents. arXiv:2609.00065. doi:10.48550/arXiv.2609.00065',64,597,1152,65,19,GRAY)

# Use explicit exponent notation: the local CJK font lacks superscript-minus glyphs.
def safe_notation(value):
    for a,b in [('10⁻²³','10^(-23)'),('10⁻²²','10^(-22)'),('10⁻²⁷','10^(-27)'),('K₀','K0')]:
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
    foot=dict(kind='text',text=f'SIM240 第一篇｜5 nm离散参考下的阶段性比较                                      {i+1} / {len(slides)}',x=64,y=685,w=1152,h=24,size=15,color=GRAY,bold=False)
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
notes=['# 第一篇导师汇报逐页讲稿','', '建议主讲第1—14页，约10分钟；第15—16页备查。数字均以5 nm离散参考为比较口径。','']
for i,s in enumerate(slides,1):
    notes += [f'## 第{i}页：'+s['title'].replace('\n',''),' ',s['note'],'', '证据入口：'+s['source'],'']
(WORK/'讲稿与公式示例.md').write_text('\n'.join(notes))
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
print(json.dumps({'pptx':str(PPT),'pdf':str(PDF),'slides':len(slides),'fit_findings':fit,'example':ex,'stats':stats},ensure_ascii=False,indent=2))
