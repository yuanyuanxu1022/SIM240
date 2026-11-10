#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SIM240 本周工作汇报 PPT — 2026-11-06 → 11-10（六页，无封面）

叙事：这一周把第一篇论文从「数据齐了」推到「稿件能投」。
结构（6 页）：五件事 → 别人怎么闭环 → 我怎么用 → 拿到什么 → 全文闭环 → 待拍板/下周。

所有数字的出处见同目录 DATA_SOURCES.md；绘图不允许出现无出处的数字。
十七页详版脚本存于 _archive_gen_week_17p.py，仅供回退参考，不再维护。
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR

BLUE   = RGBColor(0x1E, 0x4F, 0xA8)
NAVY   = RGBColor(0x0E, 0x3F, 0x8C)
MBLUE  = RGBColor(0x3D, 0x7B, 0xD9)
PALE   = RGBColor(0xC5, 0xDD, 0xF7)
LBLUE  = RGBColor(0xE8, 0xEF, 0xF8)
LBLUE2 = RGBColor(0xF0, 0xF5, 0xFC)
TXT    = RGBColor(0x1A, 0x22, 0x30)
SUB    = RGBColor(0x4A, 0x55, 0x68)
GRAY   = RGBColor(0x8B, 0x97, 0xA8)
RED    = RGBColor(0xD9, 0x53, 0x4F)
DRED   = RGBColor(0xA3, 0x2D, 0x2D)
GREEN  = RGBColor(0x0F, 0x6E, 0x56)
LGREEN = RGBColor(0xE1, 0xF5, 0xEE)
AMBER  = RGBColor(0x99, 0x3C, 0x1D)
LAMBER = RGBColor(0xFA, 0xEC, 0xE7)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
LINE   = RGBColor(0xD6, 0xDC, 0xE5)
FONT = "微软雅黑"
HERE = os.path.dirname(os.path.abspath(__file__))

TOTAL = 6
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def box(s, l, t, w, h, fill=None, line=None, radius=False):
    st = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shp = s.shapes.add_shape(st, l, t, w, h)
    shp.shadow.inherit = False
    if radius:
        try:
            shp.adjustments[0] = 0.06
        except Exception:
            pass
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line; shp.line.width = Pt(1.1)
    shp.text_frame.word_wrap = True
    return shp


def text(s, l, t, w, h, runs, size=20, color=TXT, bold=False,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.25):
    tb = s.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0; tf.margin_right = 0
    tf.margin_top = 0; tf.margin_bottom = 0
    if isinstance(runs, str):
        runs = [(runs, {})]
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = spacing
    for txt, ov in runs:
        if ov.get('new_para') and p.runs:
            p = tf.add_paragraph()
            p.alignment = ov.get('align', align)
            p.line_spacing = ov.get('spacing', spacing)
        for j, piece in enumerate(str(txt).split("\n")):
            if j > 0:
                p.add_line_break()
            if not piece:
                continue
            r = p.add_run(); r.text = piece
            r.font.name = ov.get('font', FONT)
            r.font.size = Pt(ov.get('size', size))
            r.font.bold = ov.get('bold', bold)
            r.font.color.rgb = ov.get('color', color)
    return tb


def header(s, title, sub=None):
    box(s, 0, 0, prs.slide_width, Inches(0.12), fill=BLUE)
    text(s, Inches(0.55), Inches(0.28), Inches(11.9), Inches(0.55),
         title, size=26, color=NAVY, bold=True)
    if sub:
        text(s, Inches(0.55), Inches(0.84), Inches(12.3), Inches(0.36),
             sub, size=13.5, color=GRAY)
    box(s, 0, Inches(1.28), prs.slide_width, Inches(0.015), fill=LINE)


def footer(s, page_no):
    text(s, Inches(0.55), Inches(7.06), Inches(8), Inches(0.28),
         "SIM240 ｜ 本周工作汇报 ｜ 2026-11-06 → 11-10", size=10.5, color=GRAY)
    text(s, Inches(11.4), Inches(7.04), Inches(1.4), Inches(0.3),
         f"{page_no} / {TOTAL}", size=11.5, color=BLUE, bold=True, align=PP_ALIGN.RIGHT)


def conn(s, x1, y1, x2, y2, color, width=1.8, dash=False):
    from pptx.oxml.ns import qn
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    c.line.color.rgb = color
    c.line.width = Pt(width)
    if dash:
        ln = c.line._get_or_add_ln()
        ln.append(ln.makeelement(qn('a:prstDash'), {'val': 'dash'}))
    return c


# ==================== P1 这一周做了五件事（无封面，直接从正文起） ====================
def p1():
    s = prs.slides.add_slide(BLANK)
    header(s, "这一周做了五件事", "2026-11-06 → 11-10 ｜ 一句话：从「数据齐了」到「稿件能投」")

    items = [
        ("11-06", "补闭环", "h=100 新增间隙对照\n两构建输出逐位一致",
         "关掉挂了近三周的\n「混合构建不可分离」", BLUE),
        ("11-08", "定口径", "六条结论定稿\n逐条绑证据位置",
         "从「三份文件三种说法」\n变成唯一事实来源", MBLUE),
        ("11-09", "补理论", "附录 E 增 E.1 下界\n上界 → 上下界",
         "顺带算出区间宽度\n与两个反向结论", BLUE),
        ("11-10", "加证据", "成对宽度组合入\n§4.3 / §5.1 / S14",
         "第一次能回答\n「宽度变了会怎样」", MBLUE),
        ("11-10", "出投稿件", "派生脚本 + 版本裁决\n+ 全库哈希重绑",
         "把「改哪份稿」\n从记忆变成查表", GREEN),
    ]
    y = Inches(1.62); h = Inches(4.40); w = Inches(2.24)
    gap = (Inches(12.23) - 5 * w) / 4
    conn(s, Inches(1.67), Inches(1.50), Inches(11.66), Inches(1.50), PALE, 2.2)
    for i, (date, title, what, why, col) in enumerate(items):
        l = Inches(0.55) + i * (w + gap)
        cx = l + w / 2
        dot = s.shapes.add_shape(MSO_SHAPE.OVAL, cx - Inches(0.075), Inches(1.425),
                                 Inches(0.15), Inches(0.15))
        dot.fill.solid(); dot.fill.fore_color.rgb = col
        dot.line.color.rgb = WHITE; dot.line.width = Pt(2)
        dot.shadow.inherit = False

        box(s, l, y, w, h, fill=WHITE, line=LINE, radius=True)
        box(s, l, y, w, Inches(0.05), fill=col)
        text(s, l + Inches(0.18), y + Inches(0.17), w - Inches(0.36), Inches(0.24),
             date, size=10.5, color=GRAY, bold=True)
        text(s, l + Inches(0.18), y + Inches(0.44), w - Inches(0.36), Inches(0.42),
             title, size=16, color=NAVY, bold=True)
        text(s, l + Inches(0.18), y + Inches(0.98), w - Inches(0.36), Inches(0.9),
             what, size=11, color=TXT, spacing=1.5)
        box(s, l + Inches(0.18), y + Inches(1.98), w - Inches(0.36), Inches(0.012), fill=LINE)
        text(s, l + Inches(0.18), y + Inches(2.12), w - Inches(0.36), Inches(0.24),
             "为什么值得做", size=9.5, color=col, bold=True)
        text(s, l + Inches(0.18), y + Inches(2.40), w - Inches(0.36), Inches(1.03),
             why, size=10, color=SUB, spacing=1.45)

    text(s, Inches(0.55), Inches(6.24), Inches(12.23), Inches(0.68),
         [("五件事共用一条标准：", {'size': 11.5, 'bold': True, 'color': NAVY}),
          ("每一个新说法都必须能指到「稿件哪一节 + 哪张表 + 哪份原始数据」，指不到的就不写进稿。", {'size': 11.5, 'color': SUB}),
          ("\n贯穿全周的方法线：11-05 查文献 → 11-06 核对 OpenLB 源码 → 本周逐条落进稿子（下面两页）。", {'size': 10.5, 'color': BLUE})])
    footer(s, 1)


# ==================== P2 别人怎么闭环 ====================
def p2():
    s = prs.slides.add_slide(BLANK)
    header(s, "别人是怎么闭环的：四份材料，一套骨架",
           "11-05 查文献（徐新鹏 + OpenLB）→ 11-06 核对官方源码 → 本周逐条落进稿子")

    cards = [
        ("徐新鹏 2012 → 2013 ｜ PRE / JPCM", "换一个建模尺度去验",
         "连续模型说「接触线附近蒸发/凝结改接触角 → 液滴迁移」；随即用分子动力学当数值实验，验「朝低温、速度正比于温度梯度」，再查尺寸与共存温度的影响。",
         "只说「约 10 nm 半定量一致」，不说普遍适用。", BLUE),
        ("徐新鹏 2014（共同作者）｜ Nature Physics", "改变条件，看边界在哪",
         "饼状弹跳：液滴不回缩就能以扁平形态离开 → 提出「压入柱间的毛细能转为向上动能」，要求两个时间尺度匹配 → 再改柱形、柱距、撞击条件，看何时出现、何时不出现。",
         "结论落在「出现/不出现的范围」，不在单点精度。", MBLUE),
        ("用 OpenLB 发文 ｜ Bukreev 2025 / Czelusniak 2025", "先分块自证，再核接口",
         "Bukreev：子模块先各自对解析解，耦合再验一次，最后用自动微分灵敏度与有限差分做独立算法交叉。Czelusniak：先导出方法逼近哪个方程，再建基准族，最后报收敛阶。",
         "每个部分先证明自己，再核接口。", GREEN),
        ("OpenLB 官方源码 ｜ tests/benchmarks（1.9.0）", "看收敛阶，不设绝对门槛",
         "官方 Poiseuille 误差 0.0250 → 0.00673 → 0.00176（网格 11/21/41），相邻比 3.48–3.83，接近二阶的 4 倍律；回归容差是 errorFactor 1–2，不是 ≤1%。",
         "同份数据：bounceBack 12.8–23.2%，插值类 1.1–5.7%。", AMBER),
    ]
    w = Inches(6.0); h = Inches(1.72)
    for i, (src, head, body, note, col) in enumerate(cards):
        r, c = i // 2, i % 2
        l = Inches(0.55) + c * Inches(6.24)
        t = Inches(1.44) + r * (h + Inches(0.12))
        box(s, l, t, w, h, fill=WHITE, line=LINE, radius=True)
        box(s, l, t, Inches(0.055), h, fill=col)
        text(s, l + Inches(0.24), t + Inches(0.085), w - Inches(0.45), Inches(0.22),
             src, size=8.5, color=GRAY, bold=True)
        text(s, l + Inches(0.24), t + Inches(0.31), w - Inches(0.45), Inches(0.26),
             head, size=12.5, color=NAVY, bold=True)
        text(s, l + Inches(0.24), t + Inches(0.63), w - Inches(0.46), Inches(0.70),
             body, size=8.8, color=SUB, spacing=1.30)
        text(s, l + Inches(0.24), t + Inches(1.36), w - Inches(0.46), Inches(0.28),
             note, size=8.5, color=col, spacing=1.26)

    box(s, Inches(0.55), Inches(5.16), Inches(12.23), Inches(1.42), fill=LBLUE, radius=True)
    box(s, Inches(0.55), Inches(5.16), Inches(0.075), Inches(1.42), fill=BLUE)
    text(s, Inches(0.92), Inches(5.28), Inches(11.4), Inches(0.26),
         "四份看下来，闭环其实是同一套骨架——这一篇就照这个顺序写", size=11.5, color=BLUE, bold=True)
    steps = ["① 每一部分先单独证明自己", "② 再核接口",
             "③ 用另一种独立手段交叉", "④ 最后才说能回答什么，\n并明说不能回答什么"]
    for i, st in enumerate(steps):
        x = Inches(0.92) + i * Inches(2.82)
        text(s, x, Inches(5.62), Inches(2.70), Inches(0.80), st,
             size=9.8, color=NAVY, bold=True, spacing=1.34)
    footer(s, 2)


# ==================== P3 我怎么用 ====================
def p3():
    s = prs.slides.add_slide(BLANK)
    header(s, "这周怎么用：每一条惯例都对到稿子的某一节",
           "不是「读了文献」，是「能指到哪一节改了、改成什么」")

    rows = [
        ("解析解基准 + 看收敛阶", "平板 h=75 对 h³/12：0.444%→0.111%→0.0272%，每加密一倍约降 1/4（官方相邻比 3.48–3.83）", "同构句已入稿，引 [7]", "§3.2 表 3", BLUE),
        ("边界格式选择有据", "官方对比四种格式、插值类优于 bounceBack ⇒ 选 Bouzidi + q=0.5", "补半句", "§2.1", MBLUE),
        ("独立算法交叉", "同一套系数进 OpenFOAM 独立实现（C01–C04 / GDI01）", "新增 §5.3 式(8)", "§5.3", GREEN),
        ("预测性检验", "h=100 新增间隙：预测先冻结、事后再比", "已入稿，不称盲测", "§4.4", GREEN),
        ("平台可信靠引用", "引 Krause 2021 [7]，自己只验特定几何", "已做", "§2.1", MBLUE),
        ("官方没有 ≤1% 硬门槛", "1% 只是内部停止条件，正文从未当验收指标", "口径写进稿", "§3.1", AMBER),
    ]
    y = Inches(1.44)
    text(s, Inches(0.72), y, Inches(2.9), Inches(0.24), "文献里的惯例", size=9.5, color=GRAY, bold=True)
    text(s, Inches(3.75), y, Inches(4.9), Inches(0.24), "本文的对应物", size=9.5, color=GRAY, bold=True)
    text(s, Inches(8.85), y, Inches(2.0), Inches(0.24), "本周落稿", size=9.5, color=GRAY, bold=True)
    text(s, Inches(11.20), y, Inches(1.5), Inches(0.24), "位置", size=9.5, color=GRAY, bold=True)
    y = Inches(1.72); rh = Inches(0.66)
    for i, (k, v, st, loc, col) in enumerate(rows):
        fill = WHITE if i % 2 == 0 else LBLUE2
        box(s, Inches(0.55), y, Inches(12.23), rh, fill=fill, line=LINE)
        box(s, Inches(0.55), y, Inches(0.045), rh, fill=col)
        text(s, Inches(0.74), y + Inches(0.19), Inches(2.95), Inches(0.32),
             k, size=10, color=NAVY, bold=True, spacing=1.26)
        text(s, Inches(3.75), y + Inches(0.16), Inches(4.95), Inches(0.38),
             v, size=9.2, color=TXT, spacing=1.26)
        text(s, Inches(8.85), y + Inches(0.19), Inches(2.3), Inches(0.32),
             st, size=9, color=col, bold=True, spacing=1.26)
        text(s, Inches(11.20), y + Inches(0.19), Inches(1.4), Inches(0.32),
             loc, size=9, color=GRAY)
        y = y + rh

    box(s, Inches(0.55), Inches(5.90), Inches(6.0), Inches(0.86), fill=LGREEN, radius=True)
    text(s, Inches(0.78), Inches(6.00), Inches(5.6), Inches(0.70),
         [("落稿的三处零计算改动：", {'size': 9.5, 'bold': True, 'color': GREEN}),
          ("\n① §3.2 同构句（引[7]）　② §2.1 Bouzidi 依据　③ 新增 §5.3 静态接入", {'size': 9.2, 'color': SUB})],
         spacing=1.32)
    box(s, Inches(6.79), Inches(5.90), Inches(6.0), Inches(0.86), fill=LAMBER, radius=True)
    text(s, Inches(7.02), Inches(6.00), Inches(5.6), Inches(0.70),
         [("有一条没照搬：", {'size': 9.5, 'bold': True, 'color': AMBER}),
          ("\n官方看速度场 L2 误差，我们看总积分导度 K ⇒ 只说「结构同构」，不说「误差可比」。", {'size': 9.2, 'color': SUB})],
         spacing=1.32)
    footer(s, 3)


# ==================== P4 这一周拿到什么 ====================
def p4():
    s = prs.slides.add_slide(BLANK)
    header(s, "这一周拿到什么：六个数 + 六条结论",
           "数字都指得到原始记录；六条是唯一口径（结论文件 / 稿件 §6 / 汇报 PPT 三处一致）")

    cells = [
        ("46", "条比较记录", "36 主 + 8 加密 + 2 新增；分母仍 36", NAVY),
        ("36 / 36", "全部高估，无一例外", "沿槽 +10.30~+204.85%　横槽 +8.11~+54.19%", RED),
        ("2.21 → 3.70", "各向异性比（h=75/d=100）", "相对高估约 67%；45° 流向差 9.20°", MBLUE),
        ("35 / 36", "V2 回顾性改善", "MAE 沿槽 88.85→6.40 / 横槽 30.63→4.42", GREEN),
        ("63.00× / 1.984×", "上下界区间最宽处", "均 h=25/d=100；46 条 0 违反", AMBER),
        ("10.50% / 18.71%", "V2 最大绝对相对偏差", "沿槽 / 横槽；唯一恶化点在薄隙横槽", DRED),
    ]
    w = (Inches(12.23) - Inches(0.24)) / 3
    h = Inches(1.30)
    for i, (num, label, note, col) in enumerate(cells):
        r, c = i // 3, i % 3
        l = Inches(0.55) + c * (w + Inches(0.12))
        t = Inches(1.42) + r * (h + Inches(0.10))
        box(s, l, t, w, h, fill=WHITE, line=LINE, radius=True)
        box(s, l, t, w, Inches(0.045), fill=col)
        text(s, l + Inches(0.16), t + Inches(0.14), w - Inches(0.32), Inches(0.40),
             num, size=20, color=col, bold=True)
        text(s, l + Inches(0.16), t + Inches(0.58), w - Inches(0.32), Inches(0.24),
             label, size=9.5, color=NAVY, bold=True)
        text(s, l + Inches(0.16), t + Inches(0.84), w - Inches(0.32), Inches(0.40),
             note, size=8.6, color=SUB, spacing=1.24)

    text(s, Inches(0.55), Inches(4.44), Inches(12.23), Inches(0.26),
         "六条结论（一行一条，详细证据在结论文件）", size=10.5, color=GRAY, bold=True)
    concl = [
        ("一", "定位与数据规模", "18 几何 36 条（5 nm），＋8 加密＋2 新增＝46；统计分母恒 36"),
        ("二", "原式两个方向全部高估", "沿槽 +10.30~+204.85%、横槽 +8.11~+54.19%，36/36 无一例外"),
        ("三", "两方向不等幅及后果", "A 2.21→3.70（约 +67%）；45° 重建流向差 9.20°"),
        ("四", "V2 回顾性改善", "35/36 改善；不构成独立预测精度证明（标定集含于主比较集）"),
        ("五", "新增间隙与静态接入", "h=100：+4.39/−2.03（横/沿），A 相对偏差 −6.15%"),
        ("六", "上下界与机制诊断", "h³/12 ≤ K ≤ 原式，46 条均落在界内；区间宽度给「松多少」"),
    ]
    cw = (Inches(12.23) - Inches(0.20)) / 2
    ch = Inches(0.60)
    for i, (no, name, body) in enumerate(concl):
        r, c = i % 3, i // 3
        l = Inches(0.55) + c * (cw + Inches(0.20))
        t = Inches(4.72) + r * (ch + Inches(0.06))
        box(s, l, t, cw, ch, fill=LBLUE2, radius=True)
        text(s, l + Inches(0.14), t + Inches(0.16), Inches(0.3), Inches(0.28),
             no, size=11, color=BLUE, bold=True)
        text(s, l + Inches(0.50), t + Inches(0.07), cw - Inches(0.64), Inches(0.22),
             name, size=9.8, color=NAVY, bold=True)
        text(s, l + Inches(0.50), t + Inches(0.30), cw - Inches(0.62), Inches(0.26),
             body, size=8.6, color=SUB, spacing=1.2)

    text(s, Inches(0.55), Inches(6.72), Inches(12.23), Inches(0.30),
         "口径红线：46 条 ≠ 46 次验证　｜　V2 是回顾性评价　｜　上界只给方向不给幅度　｜　FAIL 不改写为 PASS",
         size=9.6, color=AMBER, bold=True)
    footer(s, 4)


# ==================== P5 全文自己怎么闭环 ====================
def p5():
    s = prs.slides.add_slide(BLANK)
    header(s, "这一篇自己怎么闭环：八节按「上一节留下的问题」串起来",
           "把这条链讲顺，方法就能独立讲出来，不必依赖任何内部文件")

    box(s, Inches(0.55), Inches(1.42), Inches(12.23), Inches(0.62), fill=LBLUE, radius=True)
    text(s, Inches(0.85), Inches(1.51), Inches(11.7), Inches(0.46),
         [("一句话方法链：", {'size': 10, 'bold': True, 'color': BLUE}),
          ("几何 → K 与偏差 ε → 参照本身可不可信 → 双向偏差 → 有限修正 → 上下界", {'size': 12.5, 'bold': True, 'color': NAVY})])

    chain = [
        ("§1.1 → §1.2", "问题从哪来 / 边界在哪",
         "大面积压印不能逐槽解析 ⇒ 必须折算等效系数 ⇒ 这折算准吗；有人在推系数、有人在用，但没人量化「用错了多少」", BLUE),
        ("§2", "方法",
         "同一几何、同一驱动：显式沟槽算 K，与式(3) 比，偏差定义 ε = K式/K参考 − 1", MBLUE),
        ("§3", "先自证那把尺子",
         "排在 §4 之前：解析基准 → 网格序列 → 四几何加密 → 已知限制；尺子不可信，就不拿它判别人对错", GREEN),
        ("§4", "结果",
         "36/36 高估 → 两方向不等幅 → 后果（A、9.20°）→ V2 改善 35/36，并保留两处修不动", GREEN),
        ("附录 E / §5 / §6", "解释与收束",
         "上下界给方向、梯度诊断给结构、六条结论各自标明能说到哪一步", AMBER),
    ]
    y = Inches(2.24)
    for sec, name, body, col in chain:
        box(s, Inches(0.55), y, Inches(12.23), Inches(0.72), fill=WHITE, line=LINE, radius=True)
        box(s, Inches(0.55), y, Inches(0.05), Inches(0.72), fill=col)
        text(s, Inches(0.76), y + Inches(0.10), Inches(1.6), Inches(0.26),
             sec, size=10, color=col, bold=True)
        text(s, Inches(0.76), y + Inches(0.38), Inches(1.6), Inches(0.26),
             name, size=8.8, color=NAVY, bold=True, spacing=1.18)
        text(s, Inches(2.48), y + Inches(0.16), Inches(10.1), Inches(0.46),
             body, size=10, color=SUB, spacing=1.3)
        y = y + Inches(0.80)

    tips = [
        ("自证尺子", "§3 排在 §4 之前，顺序本身就是态度", GREEN),
        ("独立交叉", "同系数进第二个实现，只支持「接口对」，不冒充「K 准」", MBLUE),
        ("保留失败", "1/36 未改善、S4 仍 FAIL、h=100 不称盲测，三条都留在稿里", AMBER),
    ]
    tw = (Inches(12.23) - Inches(0.24)) / 3
    for i, (name, body, col) in enumerate(tips):
        l = Inches(0.55) + i * (tw + Inches(0.12))
        box(s, l, Inches(6.26), tw, Inches(0.62), fill=WHITE, line=LINE, radius=True)
        text(s, l + Inches(0.14), Inches(6.33), tw - Inches(0.28), Inches(0.22),
             name, size=9.5, color=col, bold=True)
        text(s, l + Inches(0.14), Inches(6.55), tw - Inches(0.28), Inches(0.28),
             body, size=8.4, color=SUB, spacing=1.18)
    footer(s, 5)


# ==================== P6 待拍板 + 下周 ====================
def p6():
    s = prs.slides.add_slide(BLANK)
    header(s, "还差什么：三件等您定，然后投出去",
           "科学内容这周已封口，剩下的是格式与声明，不需要新计算")

    L = Inches(0.55); LW = Inches(6.02)
    text(s, L, Inches(1.44), LW, Inches(0.26), "要您拍板的三件（我不能代填）", size=11, color=AMBER, bold=True)
    asks = [
        ("A", "期刊定型", "先定投哪里，格式、字数、图件规格才定得下来。候选：MEE（周期短）／EJMB（流体，周期长）。"),
        ("B", "作者侧信息", "作者与单位、基金、利益冲突、CRediT 贡献、AI 使用声明——需您提供口径，我落位。"),
        ("C", "补充材料打包", "25 处指向本地审计目录的相对链接必须改；附录字母 E→A 要四份文件同改。"),
    ]
    y = Inches(1.74)
    for no, name, body in asks:
        box(s, L, y, LW, Inches(1.28), fill=LAMBER, radius=True)
        text(s, L + Inches(0.20), y + Inches(0.14), Inches(0.3), Inches(0.28),
             no, size=13, color=AMBER, bold=True)
        text(s, L + Inches(0.52), y + Inches(0.14), LW - Inches(0.75), Inches(0.26),
             name, size=12, color=NAVY, bold=True)
        text(s, L + Inches(0.52), y + Inches(0.46), LW - Inches(0.78), Inches(0.72),
             body, size=9.6, color=SUB, spacing=1.32)
        y = y + Inches(1.40)

    R = Inches(6.78); RW = Inches(6.00)
    text(s, R, Inches(1.44), RW, Inches(0.26), "下周按依赖顺序走三步", size=11, color=GREEN, bold=True)
    steps = [
        ("1", "按刊格式化", "图件分辨率与格式、参考文献风格、字数压缩（摘要按刊限）"),
        ("2", "补齐声明项", "作者/基金/COI/CRediT/AI 使用；数据可用性最终措辞"),
        ("3", "两处加固 + 终校", "§4.2 标 5 nm、§3.1 补「不构成误差界」；三方一致性再核"),
    ]
    y = Inches(1.74)
    for no, name, body in steps:
        box(s, R, y, RW, Inches(1.28), fill=LGREEN, radius=True)
        text(s, R + Inches(0.20), y + Inches(0.14), Inches(0.3), Inches(0.28),
             no, size=13, color=GREEN, bold=True)
        text(s, R + Inches(0.52), y + Inches(0.14), RW - Inches(0.75), Inches(0.26),
             name, size=12, color=NAVY, bold=True)
        text(s, R + Inches(0.52), y + Inches(0.46), RW - Inches(0.78), Inches(0.72),
             body, size=9.6, color=SUB, spacing=1.32)
        y = y + Inches(1.40)

    box(s, Inches(0.55), Inches(6.06), Inches(12.23), Inches(0.86), fill=LBLUE, radius=True)
    box(s, Inches(0.55), Inches(6.06), Inches(0.075), Inches(0.86), fill=BLUE)
    text(s, Inches(0.92), Inches(6.16), Inches(11.5), Inches(0.70),
         [("唯一没推进的一格：投稿就绪状态仍是 false，卡点在作者信息与期刊格式，不在科学内容。", {'size': 10.5, 'bold': True, 'color': NAVY}),
          ("\n另有一条悬案：V2 函数形式的直接前身仍未确认——30 份下载文献已查完，四系数确由本研究标定，但是否沿用他人函数形式，需您指认具体篇名段落。", {'size': 9.6, 'color': SUB})],
         spacing=1.34)
    footer(s, 6)


for fn in (p1, p2, p3, p4, p5, p6):
    fn()

assert len(prs.slides) == TOTAL, len(prs.slides)

# 页脚页码按实际幻灯片顺序统一重排：各页函数里的编号只作占位，
# 避免插页后硬编码编号与真实顺序错位。
# 只认「右下角页脚位置」的那个文本框（上沿 ≥7.0in、左沿 ≥11.0in），
# 不能按文本形状全盘匹配——那会误伤正文里的「36 / 36」这类数字。
for i, s_ in enumerate(prs.slides, 1):
    for sh in s_.shapes:
        if not sh.has_text_frame or sh.top is None or sh.left is None:
            continue
        if sh.top >= Inches(7.0) and sh.left >= Inches(11.0):
            p0 = sh.text_frame.paragraphs[0]
            if p0.runs:
                p0.runs[0].text = f"{i} / {TOTAL}"

out = os.path.join(HERE, "本周工作汇报.pptx")
prs.save(out)
print(f"已生成 {len(prs.slides)} 页 → {out}")
