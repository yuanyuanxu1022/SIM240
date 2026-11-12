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


# ==================== P2 证据强度五级 ====================
def p2():
    s = prs.slides.add_slide(BLANK)
    header(s, "关于「沟槽 K 准不准」，能拿出的证据只有这五类",
           "它们查的不是同一件事：第 1–2 类查数值解，第 3 类查接口，第 4–5 类才查独立解与物理——不能互相顶替")

    rows = [
        ("1", "自洽 + 平板基准", "有", "平板通道解析解（S1）；周期 ×2/4/8 逐位相同；驱动力 ×4 偏差 3.7e−8；质量、密度、Mach",
         "程序实现没崩；平板极限下解是对的——而且解析基准不是我们自己算的", "平板解不是沟槽几何；自洽只说明程序稳，不说明沟槽 K 对", GREEN),
        ("2", "网格加密", "有", "5 → 2.5 nm，四个几何；偏差只动 0.37–5.39 个百分点",
         "这批几何在两档网格下的离散敏感性（0.37–5.39 个百分点）", "两档算不出收敛阶，不能说已渐近收敛或给出误差界；收敛到错值也会很稳", GREEN),
        ("3", "接口换算互核", "半个", "输入的是「公式的 K」（原式或 V2），不是 OpenLB 的 K；两端按式(8) 各算出口流量（C01–C04）",
         "单位、方向、张量约定对不对，K 换算成流量这条管道通不通", "OpenLB 的 K 压根没进这个检查——所以它连「OpenLB 准不准」都查不了", AMBER),
        ("4", "显式沟槽独立求解", "缺", "换一套完全不同的算法直接解沟槽几何，不走 LBM",
         "才能查 LBM 实现与 Bouzidi 边界有没有引入系统偏差", "——这一级整级没有，稿里明写「尚未完成」", DRED),
        ("5", "实验", "缺", "真实压印或微观流动测量",
         "才能查模型假设本身（单相、全充液、稳态）对不对", "——整级没有，故稿里明写「本文不涉及物理验证」", DRED),
    ]
    text(s, Inches(0.72), Inches(1.40), Inches(0.5), Inches(0.22), "级", size=9, color=GRAY, bold=True)
    text(s, Inches(1.18), Inches(1.40), Inches(1.85), Inches(0.22), "手段", size=9, color=GRAY, bold=True)
    text(s, Inches(3.10), Inches(1.40), Inches(0.55), Inches(0.22), "有吗", size=9, color=GRAY, bold=True)
    text(s, Inches(3.75), Inches(1.40), Inches(2.90), Inches(0.22), "做了什么", size=9, color=TXT, bold=True)
    text(s, Inches(6.80), Inches(1.40), Inches(2.85), Inches(0.22), "能证明", size=9, color=GREEN, bold=True)
    text(s, Inches(9.80), Inches(1.40), Inches(2.95), Inches(0.22), "不能证明", size=9, color=RED, bold=True)

    y = Inches(1.66); rh = Inches(0.92)
    for i, (lv, name, have, did, can, cannot, col) in enumerate(rows):
        fill = WHITE if i % 2 == 0 else LBLUE2
        if have == "缺":
            fill = LAMBER
        box(s, Inches(0.55), y, Inches(12.23), rh, fill=fill, line=LINE, radius=True)
        box(s, Inches(0.55), y, Inches(0.05), rh, fill=col)
        text(s, Inches(0.72), y + Inches(0.30), Inches(0.4), Inches(0.28),
             lv, size=13, color=col, bold=True)
        text(s, Inches(1.18), y + Inches(0.30), Inches(1.80), Inches(0.28),
             name, size=10, color=NAVY, bold=True, spacing=1.2)
        text(s, Inches(3.10), y + Inches(0.30), Inches(0.60), Inches(0.28),
             have, size=10, color=col, bold=True)
        text(s, Inches(3.75), y + Inches(0.09), Inches(2.92), Inches(0.76),
             did, size=8.2, color=TXT, spacing=1.3)
        text(s, Inches(6.80), y + Inches(0.09), Inches(2.85), Inches(0.76),
             can, size=8.2, color=SUB, spacing=1.3)
        text(s, Inches(9.80), y + Inches(0.09), Inches(2.92), Inches(0.76),
             cannot, size=8.2, color=DRED, spacing=1.3)
        y = y + rh + Inches(0.04)

    box(s, Inches(0.55), Inches(6.48), Inches(12.23), Inches(0.44), fill=LBLUE, radius=True)
    box(s, Inches(0.55), Inches(6.48), Inches(0.075), Inches(0.44), fill=BLUE)
    text(s, Inches(0.92), Inches(6.52), Inches(11.55), Inches(0.38),
         [("能站住的只有第 1、2 级，第 3 级只迈了半步。", {'size': 10, 'bold': True, 'color': NAVY}),
          ("第 1 级只到实现与平板极限，第 2 级只到网格敏感性，第 3 级只到接口换算；真正咬住沟槽 K 的第 4、5 级，两级皆空。", {'size': 9.0, 'color': SUB})],
         spacing=1.3)
    footer(s, 2)


# ==================== P3 因此哪句话不能说 + 换条件的真相 ====================
def p3():
    s = prs.slides.add_slide(BLANK)
    header(s, "所以：哪些话能说、哪些不能说，以及「换条件」的实情",
           "这一页是自我审查，不是表功——审稿人一定会问到这些")

    # 左：能说 / 不能说
    L = Inches(0.55); LW = Inches(6.02)
    text(s, L, Inches(1.38), LW, Inches(0.24), "按现有证据，话只能这么说", size=10.5, color=NAVY, bold=True)
    says = [
        ("能说", "「相对 5 nm 离散参考，原公式在 36 条主结果上全部高估，最大 +204.85%。」",
         "这是数值比较，参考值本身经过第 1–2 级检查。", GREEN, LGREEN),
        ("能说", "「V2 把这 36 条的平均绝对偏差从 88.85% 降到 6.40%（沿槽）、30.63% 降到 4.42%（横槽）。」",
         "但必须紧跟两句：这是回顾性评价（标定集含于主比较集）；最大绝对相对偏差仍有 10.50% / 18.71%。", GREEN, LGREEN),
        ("不能说", "「原公式在真实压印过程中高估了 204.85%。」",
         "没有第 5 级。真实过程还涉及两相、非稳态、图案边缘，本文都没碰。", RED, LAMBER),
        ("不能说", "「我们的 K 是准确的。」",
         "没有第 4 级。LBM 实现与边界格式若有系统偏差，第 1–3 级都查不出来。", RED, LAMBER),
    ]
    y = Inches(1.66)
    for tag, main, note, col, bg in says:
        h = Inches(1.02)
        box(s, L, y, LW, h, fill=bg, radius=True)
        box(s, L, y, Inches(0.05), h, fill=col)
        text(s, L + Inches(0.16), y + Inches(0.10), Inches(0.75), Inches(0.24),
             tag, size=9.2, color=col, bold=True)
        text(s, L + Inches(0.95), y + Inches(0.09), LW - Inches(1.12), Inches(0.44),
             main, size=9.2, color=TXT, spacing=1.3)
        text(s, L + Inches(0.95), y + Inches(0.60), LW - Inches(1.12), Inches(0.36),
             note, size=8.2, color=SUB, spacing=1.24)
        y = y + h + Inches(0.06)

    # 右：换条件的真相（认错）
    R = Inches(6.78); RW = Inches(6.00)
    box(s, R, Inches(1.38), RW, Inches(4.78), fill=WHITE, line=AMBER, radius=True)
    box(s, R, Inches(1.38), RW, Inches(0.05), fill=AMBER)
    text(s, R + Inches(0.22), Inches(1.50), RW - Inches(0.44), Inches(0.26),
         "「换条件」这条，我上一版写错了", size=11, color=AMBER, bold=True)
    text(s, R + Inches(0.22), Inches(1.80), RW - Inches(0.44), Inches(0.42),
         "我原先把 18 个几何当成「换条件验证」，这不成立——18 个是研究对象本身，其中 9 个还参与了 V2 标定。用开发集证明开发集，逻辑上是空的。",
         size=8.6, color=DRED, spacing=1.34)

    facts = [
        ("18 几何（d/h 0.2–4.0）", "9 个直接进 V2 系数拟合，其余 9 个在选函数形式时也已可见 ⇒ 整体是开发集，不算验证"),
        ("斜向 30/45/60°", "稿里原话：「内部自洽性，不构成对主值准确性的验证」"),
        ("槽宽 60 / 240", "稿里原话：「来自已知开发结果的回顾性诊断」"),
        ("h=100 新增间隙", "唯一接近（不在标定集、系数冻结），但稿里主动降级为「固定公式补充比较」，不认证盲测"),
        ("三档驱动力 / 三档周期", "前提检验（线性、单胞），不是验证公式"),
    ]
    yy = Inches(2.32)
    for k, v in facts:
        text(s, R + Inches(0.22), yy, Inches(1.95), Inches(0.30),
             k, size=8.2, color=NAVY, bold=True, spacing=1.2)
        text(s, R + Inches(2.22), yy, Inches(3.56), Inches(0.44),
             v, size=8.0, color=SUB, spacing=1.24)
        yy = yy + Inches(0.46)

    box(s, R + Inches(0.22), Inches(4.86), RW - Inches(0.44), Inches(1.16), fill=LAMBER, radius=True)
    text(s, R + Inches(0.36), Inches(4.92), RW - Inches(0.72), Inches(1.06),
         [("准确定位：", {'size': 8.8, 'bold': True, 'color': AMBER}),
          ("环 B 只有半个——h=100 是唯一一次系数冻结下的新条件对照，换了 h、没换 d/w。有价值，但不认证盲测，也不证明全域。", {'size': 8.2, 'color': SUB}),
          ("\n要补：在等宽矩形槽族内、看结果前冻结系数，选未开发的 h/d 做事前预测。换占空比或槽形会动到原式的等宽假设，属模型外，得先扩公式。", {'size': 8.2, 'color': SUB})],
         spacing=1.28)
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
