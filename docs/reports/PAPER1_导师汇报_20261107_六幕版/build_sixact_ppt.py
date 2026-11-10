#!/usr/bin/env python3
# 生成六幕故事版导师汇报 PPT（2026-11-07）
# 内容全部来自已核实材料：论文稿（四批修订后）、闭环报告、验收记录、文献调研
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

W, H = Inches(13.333), Inches(7.5)
INK   = RGBColor(0x21, 0x21, 0x21)
GRAY  = RGBColor(0x5F, 0x5E, 0x5A)
TEAL  = RGBColor(0x0F, 0x6E, 0x56)
RED   = RGBColor(0x99, 0x3C, 0x1D)
LIGHT = RGBColor(0xF1, 0xEF, 0xE8)
FIG   = "/home/dell/yuanyuanxu/SIM240/figures/paper"

prs = Presentation()
prs.slide_width, prs.slide_height = W, H
BLANK = prs.slide_layouts[6]

def slide():
    return prs.slides.add_slide(BLANK)

def box(s, x, y, w, h):
    tb = s.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    return tf

def para(tf, text, size=17, color=INK, bold=False, first=False, space=8, align=PP_ALIGN.LEFT):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(space)
    for seg, c, b in text:
        r = p.add_run(); r.text = seg
        r.font.size = Pt(size); r.font.color.rgb = c; r.font.bold = b
    return p

def T(s):  # plain title
    return s

def title(s, text, tag=None, tagcolor=TEAL):
    tf = box(s, Inches(0.55), Inches(0.32), Inches(12.2), Inches(0.95))
    p = para(tf, [(text, INK, True)], size=27, first=True, space=2)
    if tag:
        p2 = para(tf, [(tag, tagcolor, False)], size=14, space=0)
    # left accent bar
    bar = s.shapes.add_shape(1, Inches(0.30), Inches(0.38), Inches(0.075), Inches(0.78))
    bar.fill.solid(); bar.fill.fore_color.rgb = TEAL; bar.line.fill.background()

def pageno(s, i, n=13):
    tf = box(s, Inches(12.35), Inches(7.05), Inches(0.85), Inches(0.35))
    para(tf, [(f"{i}/{n}", GRAY, False)], size=12, first=True, space=0, align=PP_ALIGN.RIGHT)

def bullets(s, items, x=Inches(0.62), y=Inches(1.45), w=Inches(12.1), size=17, gap=10):
    tf = box(s, x, y, w, Inches(5.6))
    first = True
    for it in items:
        para(tf, it, size=size, first=first, space=gap)
        first = False

# ---------- 页1 封面 ----------
s = slide()
tf = box(s, Inches(0.8), Inches(1.7), Inches(11.7), Inches(2.6))
para(tf, [("有限间隙矩形沟槽中局部立方律的", INK, True)], size=34, first=True, space=4, align=PP_ALIGN.CENTER)
para(tf, [("方向性输运偏差", INK, True)], size=34, space=18, align=PP_ALIGN.CENTER)
para(tf, [("——量出它的错、解释它的方向、给出它的使用边界", GRAY, False)], size=20, align=PP_ALIGN.CENTER)
tf2 = box(s, Inches(1.6), Inches(4.7), Inches(10.1), Inches(1.6))
para(tf2, [("36 个条件无一例外高估；沿槽最多三倍；理论上只能高估", TEAL, True)], size=19, first=True, space=6, align=PP_ALIGN.CENTER)
para(tf2, [("六幕故事版 · 2026-11-07", GRAY, False)], size=14, align=PP_ALIGN.CENTER)

# ---------- 页2 研究问题（幕①②） ----------
s = slide(); title(s, "研究问题：一个没人量过的速算", "第一幕·世界 → 第二幕·疑点")
bullets(s, [
    [("为什么必须有它：", INK, True), ("纳米压印要铺满整块模板，算不起逐条解析每个 240 nm 沟槽 → 工程上普遍折算为等效输运系数", INK, False)],
    [("这个速算＝局部立方律：", INK, True), (("沿槽把深槽与浅台当并联通道，跨槽当两段串联阻力；简洁、无需拟合、只依赖几何", INK, False))],
    [("疑点：", RED, True), (("它假设侧壁不存在；而本文几何槽深 100 ≈ 槽宽 120 nm——侧壁贴在流动的脸上", INK, False))],
    [("没有人量过：它在纳米沟槽的双向误差，方向多大、传到哪里", INK, False)],
    [("本文问题句（§1.3）：", TEAL, True), ("考察两主方向有效导度 → 分析偏差 → 评价修正 → 识别局限", INK, False)],
], size=18, gap=14)

# ---------- 页3 几何与尺子（幕③） ----------
s = slide(); title(s, "对象与尺子：显式分辨每一个沟槽", "第三幕·造尺子")
bullets(s, [
    [("直的矩形沟槽单胞：", INK, True), (("周期 P=240、槽宽 w=120 nm；间隙 h=25–125、槽深 d=25–120；18 种几何 × 2 方向 = 36 个主条件", INK, False))],
    [("尺子＝OpenLB 直接数值模拟", INK, True), (("：显式分辨沟槽（非折算），全充液、无滑移、稳态", INK, False))],
    [("主网格 5 nm，4 种几何另做 2.5 nm 加密；Bouzidi 插值边界（q=0.5）", INK, False)],
    [("本文检验对象：", TEAL, True), ("式(3) 局部立方律的 Kxx、Kyy vs 显式真值——同一几何、同一通量定义、同一物性", INK, False)],
], w=Inches(6.6), size=16.5, gap=12)
pic = s.shapes.add_picture(f"{FIG}/Fig1_device_and_unitcell.png", Inches(7.45), Inches(1.55), width=Inches(5.4))

# ---------- 页4 尺子的可信度 ----------
s = slide(); title(s, "尺子可信吗：四道关卡", "第三幕·造尺子（与 OpenLB 官方基准同构）")
bullets(s, [
    [("关卡① 平板解析基准：", INK, True), (("0.444% → 0.111% → 0.0272%，每加密一倍误差约降四分之一——与 OpenLB 官方 Poiseuille 基准同构", INK, False))],
    [("关卡② 沟槽加密（4 几何）：", INK, True), (("沿槽变化 <0.6%，跨槽最大 −4.43%（最薄间隙），比较方向不变", INK, False))],
    [("关卡③ 过程干净：", INK, True), (("单胞复制 2→4 周期阻力逐位相同；驱动力加大 4 倍系数不变（差 ~10⁻⁸）", INK, False))],
    [("关卡④ 36 点全部按预设判据收敛（声明：停止条件≠独立验收指标）", INK, False)],
    [("另：同系数双实现互核（OpenFOAM，见第 10 页）；两版程序输出逐位一致（h75/d100）", INK, False)],
    [("诚实边界：全图连续误差界未建立；薄隙跨槽网格敏感度 −4.43% 已如实标注", GRAY, False)],
], size=16.5, gap=11)

# ---------- 页5 真相（幕④） ----------
s = slide(); title(s, "真相：36/36 全部高估", "第四幕·真相", tagcolor=RED)
bullets(s, [
    [("沿槽 Kyy：", RED, True), ("+10.30% ～ +204.85%（最高处公式值≈真值的三倍）", INK, False)],
    [("跨槽 Kxx：", RED, True), ("+8.11% ～ +54.19%", INK, False)],
    [("另 8 条 2.5 nm 加密记录 + 2 条新增（h=100）同向", INK, False)],
    [("合计：", TEAL, True), ("19 种几何、46 条离散记录，全部低于公式值", INK, False)],
    [("高估不是个别点的偏差，是系统行为；偏差幅度随几何有规律变化", INK, False)],
], w=Inches(6.3), size=17, gap=13)
pic = s.shapes.add_picture(f"{FIG}/Fig8_error_map.png", Inches(7.15), Inches(1.5), width=Inches(5.7))

# ---------- 页6 理论根源 ----------
s = slide(); title(s, "为什么只能高估：理论上界", "第四幕·真相·理论根源（附录 E）")
bullets(s, [
    [("附录 E（连续 Stokes 模型，变分论证）证明：", INK, True), (("局部立方律给出的两个主导度均为上界——只能高估，不可能低估", INK, False))],
    [("Kyy ≤ ⟨H³⟩/12，Kxx ≤ 1/(12⟨H⁻³⟩)；一般形式适用于任意周期直槽截面", INK, False)],
    [("无槽极限取等号：平板基准 0.444% 已验证等号端", INK, False)],
    [("数值与理论方向一致（46 条无一越界）——", INK, True), (("但上界只给方向，不给幅度", RED, False))],
    [("口径纪律：称“与理论方向一致的数值对照”，不称“定理被数值证明”", GRAY, False)],
], size=17, gap=13)

# ---------- 页7 代价（幕⑤） ----------
s = slide(); title(s, "代价：误差传到工程决策", "第五幕·代价", tagcolor=RED)
bullets(s, [
    [("两方向偏差不相等 → 各向异性被系统性夸大：", INK, True), (("数值 2.21 vs 公式 3.70（高估约 67%）", INK, False))],
    [("45° 驱动下重建流向相差 ", INK, False), ("9.20°", RED, True), ("（24.34° vs 15.14°）——布滴方向就错 9 度", INK, False)],
    [("这些系数正是降阶挤压模型压力方程的直接输入（式 7）", INK, False)],
    [("→ 误差进入填充压力、荷载与闭合时间的预测；两方向倍率不同还会改变压力分布形态", INK, False)],
    [("因此：只核对总输运能力不足以评判此类模型，必须同时检验两个主值及其比值", TEAL, True)],
], w=Inches(6.6), size=16.5, gap=12)
pic = s.shapes.add_picture(f"{FIG}/Fig4_K_and_anisotropy.png", Inches(7.35), Inches(1.55), width=Inches(5.5))

# ---------- 页8 修正（幕⑥上） ----------
s = slide(); title(s, "修正 V2：能与不能", "第六幕·说明书（1/3）")
bullets(s, [
    [("能：", TEAL, True), (("最大绝对残差 沿槽 205% → 10.5%、跨槽 54% → 18.7%；36 点中 35 点改善", INK, False))],
    [("不能①：", RED, True), (("薄隙反例——(h,d)=(25,100) 跨槽 +16.36% → −18.71%，绝对偏差反而增大", INK, False))],
    [("不能②：", RED, True), (("残差随间隙漂移——同一 d/w 下沿槽残差 h75→h100 相差 7.93 个百分点", INK, False))],
    [("诊断：乘性修正因子只依赖 d/w（完整公式仍含 h）——间隙依赖未抓全，改进方向明确", INK, False)],
    [("口径：V2 为回顾性评价（数据在形式选择时已可见），不称独立预测验证", GRAY, False)],
], size=17, gap=13)

# ---------- 页9 新增对照 ----------
s = slide(); title(s, "新增间隙对照与构建复现", "第六幕·说明书（2/3）· 2026-11-06/07 新增")
bullets(s, [
    [("h=100 nm（未参与 V2 标定的新间隙，固定系数对照）：", INK, True)],
    [("　原公式偏差 +49.4% / +126.6% → V2 +4.4% / −2.0%；方向比 A 偏差 −6.15%", INK, False)],
    [("　沿槽残差漂移 7.93 个百分点（未过 5pp 结构筛查）→ 确认修正因子缺间隙依赖", INK, False)],
    [("口径：按“新增间隙的固定公式对照”入稿（§4.4），不认证盲测身份、不称预测能力", GRAY, False)],
    [("构建复现（h75/d100）：", INK, True), (("两版程序输出逐位一致（K 值与停止步数），诊断末位差 3.7×10⁻³³——单几何复现，不外推", INK, False))],
    [("上界计数更新：36 主 + 8 加密 + 2 新增 = 19 种几何 46 条，全部低于公式值", TEAL, True)],
], size=16.5, gap=11)

# ---------- 页10 接入核验 ----------
s = slide(); title(s, "接入核验：系数能否真正驱动求解器", "第六幕·说明书（3/3）· §5.3（I1）")
bullets(s, [
    [("C01–C04：", INK, True), (("同一套系数（原公式 / V2）分别进入二维实现与 OpenFOAM 平均压力求解器，出口通量一致", INK, False))],
    [("GDI01：", INK, True), (("V2 跨槽系数经实际动量阻力源接入，与 C01 基线一致", INK, False))],
    [("设置：平均厚度 125 nm、24×48 μm 域、0.001 Pa·s、两端 24/0 Pa", INK, False)],
    [("换 V2 后出口流量：跨槽降 30.14%、沿槽降 56.77% —— 输入变化的输出响应", INK, False)],
    [("界限：", RED, True), (("证明接入一致性（单位/方向/通量），不证明公式准确性；静态压差驱动，不涉及动态填充", INK, False))],
], size=17, gap=13)

# ---------- 页11 文献定位 ----------
s = slide(); title(s, "我们在文献里的位置", "定位：占了图上一个空位")
bullets(s, [
    [("系数级研究都在推导新公式：", INK, True), (("Patir–Cheng 1978、Lauga–Stone 2003、Sbragaglia 2007、Dewangan 2020（独立 FEM 对照）", INK, False))],
    [("过程级研究都在使用系数：", INK, True), (("Jain 2017（用 K 做压印模拟但未验 K）、Cochrane 2018、Ryu 2017（实验 10%）、Taylor–Boning 2009", INK, False))],
    [("空位：", TEAL, True), ("“被普遍使用的折算到底错多少”——本文占了它（对 Jain 的关系：他造车，我们测他用的发动机）", INK, False)],
    [("验证栈最厚：四道关卡 + 理论上界 + 双实现互核；文献无一用 ≤1% 网格硬门槛，本文正文亦从未用作验收", INK, False)],
    [("唯一短板：无实验对照（Ryu/Taylor–Boning/Cochrane 有）——已在 §5.4 如实声明", RED, False)],
], size=16.5, gap=12)

# ---------- 页12 结论 ----------
s = slide(); title(s, "结论：这个公式的使用说明书", "第六幕·收束")
bullets(s, [
    [("何时可用：", TEAL, True), (("作保守上界（只高不低）；V2 修正后常规间隙残差 10–19%", INK, False))],
    [("何时不可信：", RED, True), (("薄隙跨槽（反例）；精确流向预测（偏差 9.2°）；外推到其他版型/新几何", INK, False))],
    [("怎么核查：", INK, True), (("必须同时报告两个主值及其比值，不能只看总输运能力", INK, False))],
    [("边界：单图案族（w=120、φ=0.5、矩形直槽）；5 nm 离散参考；静态全充液；非动态压印", GRAY, False)],
    [("对应论文结论四条（§6），每条可追溯到原始运行", GRAY, False)],
], size=17, gap=13)

# ---------- 页13 待决 ----------
s = slide(); title(s, "待导师决定的三件事", "下一步")
bullets(s, [
    [("① 投哪家？", INK, True), (("PoF（二区，流体力学开场）vs ME（三区，压印开场，Jain 同刊）——决定摘要口径，两版素材已备", INK, False))],
    [("② §5.1 机制要不要补？", INK, True), (("现只有候选因素；补分区通量分解可从“量出现象”升到“解释机理”——决定论文天花板（方案已备未执行）", INK, False))],
    [("③ 实验对照要不要补？", INK, True), (("文献闭环唯一缺环；趋势级即可（Ryu 先例 10%）", INK, False))],
], size=18, gap=16)
tf = box(s, Inches(0.62), Inches(4.6), Inches(12.1), Inches(1.8))
para(tf, [("底注：", GRAY, True), (("S4 薄隙横槽 1.328% 原样 FAIL、如实披露，该点不作定量评分；其余证据链不依赖它。中文稿已完成四批修订（附录 D.10–D.13 留痕），待英文同步。", GRAY, False))], size=14.5, first=True, space=6)

for i in range(1, 14):
    pageno(prs.slides[i-1], i)

import os
out_dir = "/home/dell/yuanyuanxu/SIM240/docs/reports/PAPER1_导师汇报_20261107_六幕版"
os.makedirs(out_dir, exist_ok=True)
out = os.path.join(out_dir, "PAPER1_导师汇报_20261107_六幕故事版.pptx")
prs.save(out)
print("saved:", out, "slides:", len(prs.slides.__iter__.__self__._sldIdLst))
