#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SIM240 论文汇报 PPT — 十四页结构（提问 / 立论 / 结果 / 收束 / 开放问题）"""
import math
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
GOLD   = RGBColor(0xFF, 0xD5, 0x6B)
SOLID  = RGBColor(0x5F, 0x5E, 0x5A)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
LINE   = RGBColor(0xD6, 0xDC, 0xE5)
FONT = "微软雅黑"
HERE = os.path.dirname(os.path.abspath(__file__))

TOTAL = 14
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
        shp.line.color.rgb = line; shp.line.width = Pt(1.2)
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


def text_paras(s, l, t, w, h, paras, size=14, color=TXT,
               anchor=MSO_ANCHOR.TOP, spacing=1.5, gap=7):
    tb = s.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0; tf.margin_right = 0
    tf.margin_top = 0; tf.margin_bottom = 0
    for i, runs in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = spacing
        if i > 0:
            p.space_before = Pt(gap)
        for txt, ov in runs:
            r = p.add_run(); r.text = txt
            r.font.name = ov.get('font', FONT)
            r.font.size = Pt(ov.get('size', size))
            r.font.bold = ov.get('bold', False)
            r.font.color.rgb = ov.get('color', color)
    return tb


def header(s, title, sub=None):
    box(s, 0, 0, prs.slide_width, Inches(0.12), fill=BLUE)
    text(s, Inches(0.55), Inches(0.30), Inches(11.9), Inches(0.55),
         title, size=28, color=NAVY, bold=True)
    if sub:
        text(s, Inches(0.55), Inches(0.88), Inches(12.2), Inches(0.36),
             sub, size=14, color=GRAY)
    box(s, 0, Inches(1.30), prs.slide_width, Inches(0.015), fill=LINE)


def footer(s, page_no):
    text(s, Inches(0.55), Inches(7.04), Inches(7), Inches(0.28),
         "SIM240 ｜ 第一篇论文汇报", size=11, color=GRAY)
    text(s, Inches(11.4), Inches(7.02), Inches(1.4), Inches(0.3),
         f"{page_no} / {TOTAL}", size=12, color=BLUE, bold=True, align=PP_ALIGN.RIGHT)


def arrow_line(s, x1, y1, x2, y2, color, width=2.0, dash=False):
    from pptx.oxml.ns import qn
    import copy
    conn = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    conn.line.color.rgb = color
    conn.line.width = Pt(width)
    ln = conn.line._get_or_add_ln()
    tail = ln.makeelement(qn('a:tailEnd'), {'type': 'triangle', 'w': 'med', 'len': 'med'})
    ln.append(tail)
    return conn


# ==================== P1 封面 ====================
def page1():
    s = prs.slides.add_slide(BLANK)
    box(s, 0, 0, prs.slide_width, Inches(0.18), fill=BLUE)
    box(s, 0, Inches(7.32), prs.slide_width, Inches(0.18), fill=LBLUE)
    text(s, Inches(0.6), Inches(0.55), Inches(6), Inches(0.4),
         "研究汇报 ｜ 论文内容与结论", size=15, color=GRAY)
    text(s, Inches(1.0), Inches(2.05), Inches(11.33), Inches(1.7),
         "有限间隙矩形沟槽中局部立方律的\n双向导度偏差及经验修正",
         size=34, color=NAVY, bold=True, align=PP_ALIGN.CENTER, spacing=1.3)
    box(s, Inches(5.67), Inches(3.9), Inches(2.0), Inches(0.04), fill=BLUE)
    text(s, Inches(1.5), Inches(4.2), Inches(10.33), Inches(1.3),
         "一个可以证明的必然性：\n局部立方律为什么一定高估，以及它到底松了多少",
         size=20, color=SUB, align=PP_ALIGN.CENTER, spacing=1.4)
    text(s, Inches(0.6), Inches(6.35), Inches(12.13), Inches(0.4),
         "汇报人：＿＿＿＿　　日期：2026 年 11 月",
         size=15, color=GRAY, align=PP_ALIGN.CENTER)


# ==================== P2 问题与对象 ====================
def page2():
    s = prs.slides.add_slide(BLANK)
    header(s, "研究问题与对象", "固定、全充液矩形沟槽中，局部立方律对两个方向导度的描述准不准")

    box(s, Inches(0.55), Inches(1.46), Inches(12.23), Inches(1.14), fill=LBLUE, radius=True)
    box(s, Inches(0.55), Inches(1.46), Inches(0.075), Inches(1.14), fill=BLUE)
    text(s, Inches(0.88), Inches(1.57), Inches(2.2), Inches(0.26),
         "核心研究问题", size=13, color=BLUE, bold=True)
    text(s, Inches(0.88), Inches(1.86), Inches(11.72), Inches(0.66),
         [("固定、全充液矩形沟槽中，局部立方律对", {}),
          ("沿槽与横槽", {'color': NAVY, 'bold': True}),
          ("导度的描述与显式 OpenLB 计算相差多少；本研究标定的经验修正 ", {}),
          ("V2", {'color': NAVY, 'bold': True}),
          (" 能改善多少？", {})],
         size=17, color=TXT, spacing=1.35)

    top = Inches(2.76); h = Inches(2.86)
    gap = Inches(0.26); w = Inches(3.90)
    xs = [Inches(0.55), Inches(0.55) + w + gap, Inches(0.55) + 2 * (w + gap)]

    cards = [
        ("研究对象", "几何与主方向",
         [[("矩形沟槽阵列，周期 ", {}), ("P = 240 nm", {'bold': True, 'color': NAVY}),
           ("，槽与凸台等宽（槽宽 ", {}), ("w = 120 nm", {'bold': True, 'color': NAVY}), ("）。", {})],
          [("间隙 ", {}), ("h", {'bold': True}), (" 与槽深 ", {}), ("d", {'bold': True}),
           (" 为变化量。", {})],
          [("比较两个主方向：", {}),
           ("沿槽 Kyy", {'color': BLUE, 'bold': True}), (" 与 ", {}),
           ("横槽 Kxx", {'color': BLUE, 'bold': True}), ("。", {})]]),
        ("物理条件", "算的是哪一种流动",
         [[("固定间隙、全充液、单相牛顿液体、壁面无滑移、稳态。", {})],
          [("即液体已充满沟槽之后的稳态输运，不涉及填充过程、自由表面或接触角。", {})]]),
        ("被评价公式", "局部立方律",
         [[("把图案化表面当作局部平板组合、用间隙 ", {}),
           ("h", {'bold': True}),
           (" 的立方关系估算通流能力的简化式。", {})],
          [("它未显式解析侧壁与台阶处流动，", {}),
           ("故两个方向须分别检验。", {'color': RED, 'bold': True})]]),
    ]

    for i, (title, sub, paras) in enumerate(cards):
        x = xs[i]
        box(s, x, top, w, h, fill=WHITE, line=LINE, radius=True)
        box(s, x + Inches(0.24), top + Inches(0.22), Inches(0.36), Inches(0.36), fill=BLUE, radius=True)
        text(s, x + Inches(0.24), top + Inches(0.26), Inches(0.36), Inches(0.28),
             str(i + 1), size=14, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
        text(s, x + Inches(0.72), top + Inches(0.22), Inches(2.95), Inches(0.34),
             title, size=18, color=NAVY, bold=True)
        text(s, x + Inches(0.72), top + Inches(0.58), Inches(2.95), Inches(0.26),
             sub, size=11, color=GRAY)
        box(s, x + Inches(0.24), top + Inches(0.96), w - Inches(0.48), Inches(0.014), fill=LINE)
        text_paras(s, x + Inches(0.26), top + Inches(1.12), w - Inches(0.54), h - Inches(1.28),
                   paras, size=13, color=TXT, spacing=1.55)

    box(s, Inches(0.55), Inches(5.74), Inches(12.23), Inches(1.02), fill=NAVY, radius=True)
    text(s, Inches(0.9), Inches(5.84), Inches(3.4), Inches(0.26),
         "这一页留下三个问题，后面逐一回答", size=12, color=RGBColor(0x9C, 0xC0, 0xF0), bold=True)
    qs = [("① 为什么它必然高估？", "→ 第 4 页", Inches(0.9)),
          ("② 到底高估多少？", "→ 第 6 页", Inches(4.55)),
          ("③ 两个方向是否等幅？", "→ 第 9 页", Inches(8.20))]
    for q, tag, qx in qs:
        text(s, qx, Inches(6.14), Inches(3.45), Inches(0.30),
             [(q, {'color': WHITE, 'size': 14, 'bold': True})], size=14)
        text(s, qx, Inches(6.44), Inches(3.45), Inches(0.24),
             [(tag, {'color': GOLD, 'size': 10.5})], size=10.5)

    footer(s, 2)


# ==================== P3 局部立方律公式怎么来的 ====================
def page_formula():
    s = prs.slides.add_slide(BLANK)
    header(s, "这个公式是怎么来的",
           "只有两步：先从两块平行平板算出 h³/12，再把深浅两区按两种方式拼起来")

    # ---------- 上半：平板 ----------
    L = Inches(0.55)
    text(s, L, Inches(1.38), Inches(4.4), Inches(0.24),
         "第一步　最简单的通道：两块平行平板", size=11, color=GRAY, bold=True)

    # 通道：上壁 / 液体 / 下壁
    cx0, cy0 = Inches(0.85), Inches(2.02)
    cw_, chh = Inches(3.20), Inches(1.06)
    box(s, cx0, cy0 - Inches(0.06), cw_, Inches(0.06), fill=SOLID)
    box(s, cx0, cy0, cw_, chh, fill=PALE)
    box(s, cx0, cy0 + chh, cw_, Inches(0.06), fill=SOLID)

    # 速度剖面：中间快、贴壁为零
    for i in range(1, 10):
        z = i / 10.0
        u = 4.0 * z * (1.0 - z)
        seg = 0.82 * u
        if seg < 0.03:
            continue
        box(s, cx0 + Inches(0.10), cy0 + Inches(z * 1.06) - Inches(0.022),
            Inches(seg), Inches(0.044), fill=BLUE)

    # h 标注
    text(s, cx0 + cw_ + Inches(0.10), cy0 + Inches(0.40), Inches(0.40), Inches(0.24),
         "h", size=13, color=NAVY, bold=True)
    box(s, cx0 + cw_ + Inches(0.06), cy0, Inches(0.012), chh, fill=GRAY)

    text(s, L, Inches(3.24), Inches(4.5), Inches(0.28),
         [("液体被压着向左流，速度呈抛物线：", {'size': 10.5}),
          ("中间快，贴壁为零", {'size': 10.5, 'color': DRED, 'bold': True})],
         size=10.5, color=SUB)

    # ---------- 右上：三步 ----------
    R = Inches(5.10); RW = Inches(7.68)
    steps = [
        ("算流量", "把这条抛物线沿高度积分，得到单位宽度的流量",
         "q = (h³ / 12μ) · (Δp / L)"),
        ("取名导度", "把驱动项除掉，剩下的就是几何决定的通流能力",
         "K = h³ / 12　（单位 m³）"),
        ("看那个三次方", "这就是“立方律”三个字的来历",
         "h 翻一倍 → 流量涨 8 倍"),
    ]
    for i, (head, desc, formula) in enumerate(steps):
        yy = Inches(1.38) + i * Inches(0.655)
        box(s, R, yy, RW, Inches(0.58), fill=LBLUE2, line=LINE, radius=True)
        box(s, R, yy, Inches(0.055), Inches(0.58), fill=BLUE)
        text(s, R + Inches(0.18), yy + Inches(0.16), Inches(0.30), Inches(0.26),
             str(i + 1), size=12, color=BLUE, bold=True)
        text(s, R + Inches(0.52), yy + Inches(0.05), Inches(3.05), Inches(0.22),
             head, size=11.5, color=NAVY, bold=True)
        text(s, R + Inches(0.52), yy + Inches(0.28), Inches(3.05), Inches(0.24),
             desc, size=9.5, color=SUB)
        text(s, R + Inches(3.72), yy + Inches(0.14), Inches(3.78), Inches(0.32),
             formula, size=12.5, color=BLUE, bold=True)

    # ---------- 下半：两种拼法 ----------
    text(s, L, Inches(3.66), Inches(11.0), Inches(0.24),
         "第二步　沟槽是深浅交替的，把两段拼起来——两个方向拼法不同", size=11, color=GRAY, bold=True)

    cw2 = Inches(5.985); top2 = Inches(3.96); ch2 = Inches(2.06)
    cards = [
        ("沿槽方向：并排走，各走各的", "两条车道同时通车",
         "深区和浅区互不干扰、各自承担流量，所以把两者的导度加起来再平均。",
         "算术平均", "Kyy = [ (h+d)³ + h³ ] / 24"),
        ("横槽方向：接力走，一个接一个", "必须先跨深区、再跨浅区",
         "深区和浅区串联在同一条路上，慢的那段拖住整体，所以把阻力相加。",
         "调和平均", "Kxx = (h+d)³·h³ / { 6[(h+d)³ + h³] }"),
    ]
    for i, (title, sub, plain, method, formula) in enumerate(cards):
        x = Inches(0.55) + i * (cw2 + Inches(0.26))
        box(s, x, top2, cw2, ch2, fill=WHITE, line=LINE, radius=True)
        box(s, x, top2, cw2, Inches(0.52), fill=NAVY, radius=True)
        box(s, x, top2 + Inches(0.40), cw2, Inches(0.12), fill=NAVY)
        text(s, x + Inches(0.24), top2 + Inches(0.10), cw2 - Inches(2.0), Inches(0.28),
             title, size=13, color=WHITE, bold=True)
        text(s, x + Inches(0.24), top2 + Inches(0.72), cw2 - Inches(0.48), Inches(0.24),
             sub, size=10.5, color=RED, bold=True)
        text(s, x + Inches(0.24), top2 + Inches(0.96), cw2 - Inches(0.48), Inches(0.46),
             plain, size=10.5, color=SUB, spacing=1.35)
        text(s, x + Inches(0.24), top2 + Inches(1.52), Inches(1.05), Inches(0.22),
             method, size=9.5, color=GRAY)
        text(s, x + Inches(1.32), top2 + Inches(1.50), cw2 - Inches(1.56), Inches(0.30),
             formula, size=12, color=BLUE, bold=True)

    # ---------- 底部：一句话 ----------
    box(s, Inches(0.55), Inches(6.12), Inches(12.23), Inches(0.74), fill=NAVY, radius=True)
    text(s, Inches(0.88), Inches(6.22), Inches(11.6), Inches(0.54),
         [("“局部”两个字的含义：", {'color': RGBColor(0x9C, 0xC0, 0xF0), 'bold': True}),
          ("每一处高度都当成一块独立平板，再按并联或串联拼起来。拼法本身没错——"
           "错在拼的时候，", {'color': WHITE}),
          ("台阶和竖墙这些界面被抹掉了", {'color': GOLD, 'bold': True}),
          ("。", {'color': WHITE})],
         size=12, color=WHITE, spacing=1.3)

    footer(s, 3)


# ==================== P3 定理 ====================
def page3():
    s = prs.slides.add_slide(BLANK)
    header(s, "先证明一件事：高估不是偶然",
           "理想连续 Stokes 模型里，局部立方律给出上界、h³/12 给出下界；只有无槽平板（d = 0）时三者合一")

    L = Inches(0.55); LW = Inches(5.60)
    text(s, L, Inches(1.42), LW, Inches(0.24),
         "两张图的差别，就是误差的来源", size=11, color=GRAY, bold=True)

    # 图 A：等效平行平板
    text(s, L, Inches(1.70), LW, Inches(0.26),
         [("局部模型的假设：", {'color': NAVY, 'bold': True}),
          ("每一处高度都是一对独立平行平板", {})], size=11.5, color=SUB)
    ay = Inches(2.02)
    box(s, L + Inches(0.30), ay, Inches(4.10), Inches(0.20), fill=SOLID)
    box(s, L + Inches(0.30), ay + Inches(0.20), Inches(4.10), Inches(0.52), fill=PALE)
    box(s, L + Inches(0.30), ay + Inches(0.72), Inches(4.10), Inches(0.20), fill=SOLID)
    text(s, L + Inches(4.55), ay + Inches(0.30), Inches(0.50), Inches(0.26),
         "h", size=13, color=NAVY, bold=True)
    text(s, L + Inches(0.46), ay + Inches(0.30), Inches(1.2), Inches(0.24),
         "自由流动，无侧壁", size=10, color=RGBColor(0x18, 0x5F, 0xA5))

    # 图 B：真实沟槽
    text(s, L, Inches(3.22), LW, Inches(0.26),
         [("真实几何：", {'color': DRED, 'bold': True}),
          ("液体还要绕过台阶、贴着竖壁走", {})], size=11.5, color=SUB)
    by = Inches(3.54)
    box(s, L + Inches(0.30), by, Inches(4.10), Inches(0.18), fill=SOLID)
    box(s, L + Inches(0.30), by + Inches(0.18), Inches(4.10), Inches(0.26), fill=PALE)
    box(s, L + Inches(0.30), by + Inches(0.44), Inches(1.38), Inches(0.54), fill=SOLID)
    box(s, L + Inches(1.68), by + Inches(0.44), Inches(1.34), Inches(0.54), fill=PALE)
    box(s, L + Inches(3.02), by + Inches(0.44), Inches(1.38), Inches(0.54), fill=SOLID)
    box(s, L + Inches(0.30), by + Inches(0.98), Inches(4.10), Inches(0.18), fill=SOLID)
    text(s, L + Inches(4.55), by + Inches(0.18), Inches(0.50), Inches(0.24),
         "h", size=13, color=NAVY, bold=True)
    text(s, L + Inches(3.52), by + Inches(0.58), Inches(0.55), Inches(0.24),
         "d", size=12, color=WHITE, bold=True)
    # 侧壁红色标记
    box(s, L + Inches(1.665), by + Inches(0.46), Inches(0.03), Inches(0.50), fill=RED)
    box(s, L + Inches(3.005), by + Inches(0.46), Inches(0.03), Inches(0.50), fill=RED)

    text(s, L, Inches(4.82), LW, Inches(0.26),
         [("红标处 = 竖壁与台阶：平行平板模型里不存在这些界面", {'color': DRED})],
         size=10, color=DRED)

    text(s, L, Inches(5.16), LW, Inches(0.72),
         [("多出来的界面带来额外黏性剪切与台阶处的速度重分布，两种模型都当成不存在；"
           "真实流动因此多耗散一部分能量，同样压差只能给出更小的通量。", {})],
         size=11.5, color=SUB, spacing=1.4)

    # 右侧：定理
    R = Inches(6.50); RW = Inches(6.28)
    box(s, R, Inches(1.42), RW, Inches(1.06), fill=NAVY, radius=True)
    text(s, R + Inches(0.26), Inches(1.50), RW - Inches(0.5), Inches(0.22),
         "定理（附录 E）：上界与下界", size=10.5, color=RGBColor(0x9C, 0xC0, 0xF0), bold=True)
    for k, sub_ in enumerate(("yy", "xx")):
        text(s, R + Inches(0.26), Inches(1.72) + k * Inches(0.28), RW - Inches(0.5), Inches(0.26),
             [("h³/12  ≤  K", {'size': 13.5, 'bold': True}), (sub_, {'size': 9, 'bold': True}),
              ("  ≤  K", {'size': 13.5, 'bold': True}), (sub_, {'size': 9, 'bold': True}),
              ("LCL", {'size': 9, 'bold': True}),
              ("　　" if k == 0 else "　　d = 0 时三者合一", {'size': 9.5})],
             size=13.5, color=GOLD, spacing=1.1)

    text(s, R, Inches(2.54), RW, Inches(0.22), "怎么证（三步）", size=10.5, color=GRAY, bold=True)
    steps = [
        ("截面不等式", "对任意高度 H(x)，Cauchy–Schwarz 给出 ∫|∂zU|²dz ≥ 12q²/H³"),
        ("能量恒等式", "耗散 D = P·K——通量与耗散是同一个量"),
        ("加权平均", "合并两步得 K ≤ ⟨H³⟩/12 与 K ≤ 1/(12⟨H⁻³⟩)，右端正是式（3）"),
    ]
    for i, (head, body) in enumerate(steps):
        yy = Inches(2.76) + i * Inches(0.62)
        box(s, R, yy, RW, Inches(0.56), fill=LBLUE2, line=LINE, radius=True)
        text(s, R + Inches(0.16), yy + Inches(0.14), Inches(0.32), Inches(0.28),
             str(i + 1), size=12, color=BLUE, bold=True)
        text(s, R + Inches(0.56), yy + Inches(0.07), Inches(1.45), Inches(0.22),
             head, size=11, color=NAVY, bold=True)
        text(s, R + Inches(2.05), yy + Inches(0.07), RW - Inches(2.22), Inches(0.44),
             body, size=10, color=SUB, spacing=1.2, anchor=MSO_ANCHOR.MIDDLE)

    text(s, R, Inches(4.64), RW, Inches(0.22), "这个定理买到了什么", size=10.5, color=GRAY, bold=True)
    gains = [
        ("方向不必再测", "——只要 d > 0，高估是必然的"),
        ("要测的只剩幅度", "——定理不给数字"),
        ("修正结构自洽", "——V2 因子恒小于 1，不破坏上界"),
    ]
    for i, (head, body) in enumerate(gains):
        yy = Inches(4.90) + i * Inches(0.36)
        text(s, R, yy, Inches(0.18), Inches(0.24), "·", size=14, color=BLUE, bold=True)
        text(s, R + Inches(0.18), yy, Inches(6.0), Inches(0.30),
             [(head, {'color': NAVY, 'bold': True}), (body, {})],
             size=11, color=SUB, spacing=1.2)

    text(s, Inches(0.55), Inches(6.22), Inches(12.23), Inches(0.58),
         [("边界：", {'color': DRED, 'bold': True}),
          ("定理针对理想连续 Stokes 问题，不保证 5 nm 离散解的误差，也不给出偏差幅度、方向比偏差的符号或 V2 的准确度。"
           "它解释“为什么偏”，不解释“偏多少”。", {})],
         size=11, color=SUB, spacing=1.3)

    footer(s, 4)


# ==================== P4 怎么量 ====================
def page4():
    s = prs.slides.add_slide(BLANK)
    header(s, "怎么把这个必然性量出来",
           "定理说方向、不给幅度——所以必须把同一几何的真实流动算出来，再逐点对比")

    top = Inches(1.44); ch = Inches(1.46)
    cw = Inches(2.8775); gap = Inches(0.24)
    items = [
        ("求解器", "OpenLB 格子玻尔兹曼", "D3Q19 速度集，单松弛 BGK，τ = 1"),
        ("驱动方式", "Guo 体力项", "等效压差驱动，读稳态通量"),
        ("壁面处理", "Bouzidi 插值反弹", "主、加密、黏度对照 q = 0.5，无一例外"),
        ("离散参考", "5 nm 网格为主", "4 种几何另加密到 2.5 nm"),
    ]
    for i, (tag, main, sub) in enumerate(items):
        x = Inches(0.55) + i * (cw + gap)
        box(s, x, top, cw, ch, fill=LBLUE2, line=LINE, radius=True)
        box(s, x, top, Inches(0.06), ch, fill=BLUE)
        text(s, x + Inches(0.22), top + Inches(0.14), cw - Inches(0.36), Inches(0.24),
             tag, size=11.5, color=BLUE, bold=True)
        text(s, x + Inches(0.22), top + Inches(0.40), cw - Inches(0.36), Inches(0.34),
             main, size=15, color=NAVY, bold=True)
        text(s, x + Inches(0.22), top + Inches(0.80), cw - Inches(0.36), Inches(0.50),
             sub, size=11, color=SUB, spacing=1.35)

    text(s, Inches(0.55), Inches(3.08), Inches(6.0), Inches(0.26),
         "数据规模：主集合 + 加密 + 新增", size=11, color=GRAY, bold=True)

    cy = Inches(3.40); bh = Inches(1.04)
    bw = Inches(2.66); step = Inches(3.19)
    chain = [
        ("18 种几何", "36 条主方向结果（5 nm）", False),
        ("+ 8 条", "2.5 nm 加密，4 种几何", False),
        ("+ 2 条", "新增间隙 h = 100 nm", False),
        ("19 种几何", "46 条比较记录", True),
    ]
    for i, (main, sub, hi) in enumerate(chain):
        x = Inches(0.55) + i * step
        if hi:
            box(s, x, cy, bw, bh, fill=BLUE, radius=True)
            text(s, x, cy + Inches(0.19), bw, Inches(0.40),
                 main, size=21, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
            text(s, x, cy + Inches(0.65), bw, Inches(0.30),
                 sub, size=11.5, color=RGBColor(0xC9, 0xDA, 0xF2), align=PP_ALIGN.CENTER)
        else:
            box(s, x, cy, bw, bh, fill=WHITE, line=LINE, radius=True)
            text(s, x, cy + Inches(0.19), bw, Inches(0.40),
                 main, size=20, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
            text(s, x, cy + Inches(0.65), bw, Inches(0.30),
                 sub, size=11.5, color=SUB, align=PP_ALIGN.CENTER)
        if i < 3:
            ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x + bw + Inches(0.11),
                                    cy + Inches(0.41), Inches(0.30), Inches(0.22))
            ar.shadow.inherit = False
            ar.fill.solid(); ar.fill.fore_color.rgb = MBLUE
            ar.line.fill.background()

    ny = Inches(4.68); nh = Inches(0.96)
    nw = Inches(5.985)
    notes = [
        ("5 nm 不是真值", "它是同一离散分辨率下的参考；连续解精度由解析基准、收敛与加密对照另行支撑。", RED),
        ("加密只覆盖 4 种几何", "沿槽变化 ≤ 1.33 个百分点；横槽最坏 (h,d)=(25,100) 由 16.36% 变 21.76%。", BLUE),
    ]
    for i, (head, body, col) in enumerate(notes):
        x = Inches(0.55) + i * (nw + Inches(0.26))
        box(s, x, ny, nw, nh, fill=WHITE, line=LINE, radius=True)
        box(s, x, ny, Inches(0.06), nh, fill=col)
        text(s, x + Inches(0.22), ny + Inches(0.13), nw - Inches(0.40), Inches(0.26),
             head, size=12.5, color=col, bold=True)
        text(s, x + Inches(0.22), ny + Inches(0.43), nw - Inches(0.40), Inches(0.46),
             body, size=11, color=SUB, spacing=1.35)

    box(s, Inches(0.55), Inches(5.80), Inches(12.23), Inches(0.80), fill=NAVY, radius=True)
    text(s, Inches(0.88), Inches(5.92), Inches(11.6), Inches(0.28),
         [("46 条比较记录 ≠ 46 种几何 ≠ 46 次独立验证", {'color': GOLD, 'bold': True}),
          ("　　主比较统计的分母仍是 36 条；8 条加密与 2 条新增单独报告。", {'color': WHITE})],
         size=13.5, spacing=1.2)

    text(s, Inches(0.55), Inches(6.68), Inches(12.23), Inches(0.30),
         [("下一页：", {'color': GRAY}), ("方向由定理保证，那就只剩一个问题——到底松了多少。", {})],
         size=11, color=SUB)

    footer(s, 5)


# ==================== P5 偏差幅度 ====================
def page5():
    s = prs.slides.add_slide(BLANK)
    header(s, "问题②　到底高估多少",
           "18 种几何、36 条主方向结果全部为正——这不是新发现，是定理该有的样子")

    ty = Inches(1.44); th = Inches(2.98)
    cw = Inches(5.985)
    dirs = [
        ("沿槽方向  Kyy", "18 / 18 高估", "+10.30%", "+204.85%",
         "h = 50 nm，d = 120 nm", "模型值约为参考的 3.05 倍", "h = 125 nm，d = 25 nm"),
        ("横槽方向  Kxx", "18 / 18 高估", "+8.11%", "+54.19%",
         "h = 125 nm，d = 120 nm", "模型值约为参考的 1.54 倍", "h = 25 nm，d = 25 nm"),
    ]
    for i, (name, badge, lo, hi, maxpos, maxratio, minpos) in enumerate(dirs):
        x = Inches(0.55) + i * (cw + Inches(0.26))
        box(s, x, ty, cw, th, fill=WHITE, line=LINE, radius=True)
        box(s, x, ty, cw, Inches(0.50), fill=NAVY, radius=True)
        box(s, x, ty + Inches(0.38), cw, Inches(0.12), fill=NAVY)
        text(s, x + Inches(0.24), ty + Inches(0.12), cw - Inches(1.6), Inches(0.28),
             name, size=15, color=WHITE, bold=True)
        text(s, x + cw - Inches(1.30), ty + Inches(0.14), Inches(1.06), Inches(0.24),
             badge, size=10.5, color=RGBColor(0xC9, 0xDA, 0xF2), align=PP_ALIGN.RIGHT)

        text(s, x + Inches(0.24), ty + Inches(0.64), cw - Inches(0.48), Inches(0.22),
             "相对 5 nm 离散参考的偏差范围", size=10.5, color=GRAY)
        text(s, x + Inches(0.24), ty + Inches(0.86), cw - Inches(0.48), Inches(0.48),
             [(lo, {'color': MBLUE, 'bold': True, 'size': 30}),
              ("　→　", {'color': GRAY, 'size': 16}),
              (hi, {'color': BLUE, 'bold': True, 'size': 30})],
             size=30, spacing=1.0)

        box(s, x + Inches(0.24), ty + Inches(1.52), cw - Inches(0.48), Inches(0.014), fill=LINE)

        rows = [
            ("最大偏差处", maxpos, maxratio),
            ("最小偏差处", minpos, "高估幅度最温和的点"),
        ]
        ry = ty + Inches(1.64)
        for k, (lab, val, note) in enumerate(rows):
            yy = ry + k * Inches(0.62)
            text(s, x + Inches(0.24), yy, Inches(1.05), Inches(0.22),
                 lab, size=10.5, color=GRAY)
            text(s, x + Inches(1.34), yy - Inches(0.02), cw - Inches(1.60), Inches(0.24),
                 val, size=13, color=NAVY, bold=True)
            text(s, x + Inches(1.34), yy + Inches(0.24), cw - Inches(1.60), Inches(0.22),
                 note, size=10.5, color=SUB)

    box(s, Inches(0.55), Inches(4.60), Inches(12.23), Inches(0.92), fill=LBLUE, radius=True)
    box(s, Inches(0.55), Inches(4.60), Inches(0.07), Inches(0.92), fill=BLUE)
    text(s, Inches(0.86), Inches(4.70), Inches(11.7), Inches(0.24),
         [("两个方向松得不一样：沿槽最多 3.05 倍、横槽最多 1.54 倍——为什么？", {'color': NAVY, 'bold': True, 'size': 13})], size=13)
    text(s, Inches(0.86), Inches(4.96), Inches(11.7), Inches(0.50),
         [("这不是凑巧。下一页把“地板”补上：真实值夹在下界与这个上界之间，两堵墙的距离有闭式，"
           "松紧差别正是从这个式子里读出来的。再往后（第 8 页）把偏差换成能感知的数，第 9 页看修正、第 10 页看后果。", {})],
         size=12, color=SUB, spacing=1.3)

    # 趋势说明
    ty2 = Inches(5.66)
    text(s, Inches(0.55), ty2, Inches(12.23), Inches(0.24),
         "参数趋势（稿内 §4.2）", size=11, color=GRAY, bold=True)
    text(s, Inches(0.55), ty2 + Inches(0.26), Inches(12.23), Inches(0.66),
         [("固定间隙时，沿槽偏差随 d/w 增大而增大；但加入 h = 25 nm 后不再单调——d = 100 nm 时沿槽偏差由 "
           "h = 25 的 139.14% 升到 h = 50 的 154.24%，再降到 144.95% 与 108.38%。", {})],
         size=11.5, color=SUB, spacing=1.4)

    text(s, Inches(0.55), Inches(6.62), Inches(12.23), Inches(0.40),
         [("口径：", {'color': DRED, 'bold': True}),
          ("偏差 =（局部立方律导度 / OpenLB 离散导度 − 1）× 100%，正值表示公式偏高；每方向 18 条、合计 36 条。"
           "本页范围只属于这 18 种几何与 5 nm 参考，不代表连续参数域；8 条加密与 2 条新增单列，不并入统计。", {})],
         size=10, color=SUB, spacing=1.25)

    footer(s, 6)


# ==================== P7 可行区间（下界） ====================
def page_interval():
    s = prs.slides.add_slide(BLANK)
    header(s, "地板在哪里：真实值夹在两堵墙之间",
           "上界是天花板（原公式）；把槽腔封死、只留 h 厚贯通层，就得到地板 h³/12。两堵墙之间才是真实值")

    # 左：区间图
    pic = os.path.join(HERE, "interval_cn.png")
    s.shapes.add_picture(pic, Inches(0.55), Inches(1.40), width=Inches(7.30))

    # 右：四张卡
    RX = Inches(8.05); RW = Inches(4.73)

    def card(y, h, head, runs, head_col=BLUE, fill=LBLUE2):
        box(s, RX, y, RW, h, fill=fill, line=LINE, radius=True)
        box(s, RX, y, Inches(0.055), h, fill=head_col)
        text(s, RX + Inches(0.20), y + Inches(0.11), RW - Inches(0.36), Inches(0.22),
             head, size=11, color=head_col, bold=True)
        text(s, RX + Inches(0.20), y + Inches(0.36), RW - Inches(0.36), h - Inches(0.44),
             runs, size=9.5, color=SUB, spacing=1.36)

    card(Inches(1.40), Inches(0.94), "地板　槽腔封死后剩下的那层",
         [("K ≥ ", {}), ("h³/12", {'bold': True, 'color': NAVY, 'size': 11}),
          ("　只保留贯通 h 层的平行平板通流，是最保守的可容许状态。", {})])

    card(Inches(2.42), Inches(0.94), "天花板　原公式（附录 E 上界）",
         [("K ≤ ", {}), ("K", {'bold': True, 'color': NAVY, 'size': 11}),
          ("LCL", {'bold': True, 'color': NAVY, 'size': 7.5}),
          ("　把槽深整个当成完全贯通的平板层，所以只会偏高。", {})])

    card(Inches(3.44), Inches(1.42), "两堵墙差多远　r = (h + d)/h",
         [("沿槽　", {}), ("(1 + r³)/2", {'bold': True, 'color': NAVY, 'size': 10.5}),
          ("　横槽　", {}), ("2r³/(1 + r³) < 2", {'bold': True, 'color': NAVY, 'size': 10.5}),
          ("\nr = 5 时得 63.00 与 1.984。横槽无论槽多深，上界最多是地板的 ", {}),
          ("2 倍", {'bold': True, 'color': DRED}),
          ("；沿槽没有这个上限——所以沿槽才松到 63 倍。", {})])

    card(Inches(4.90), Inches(1.04), "实测站在哪　不是中点",
         [("46 条记录全在区间内；两方向各 ", {}),
          ("11/18", {'bold': True, 'color': NAVY}),
          (" 个几何更靠地板。平均：地板低估 58.17/23.84%、原公式高估 88.85/30.63%（沿槽/横槽）。", {})])

    # 底部红线
    box(s, Inches(0.55), Inches(6.06), Inches(12.23), Inches(0.82), fill=NAVY, radius=True)
    text(s, Inches(0.86), Inches(6.16), Inches(11.7), Inches(0.62),
         [("区间能说什么：", {'color': GOLD, 'bold': True}),
          ("它不含槽宽 w，所以解释不了宽度依赖；横槽区间窄（≤2 倍）也不等于预测准——横槽实测仍有 +54.19% 的高估。"
           "区间是理论约束与比较基线，不是点预测。本页由式（3）与 h³/12 直接化简，未新增计算。", {'color': WHITE})],
         size=11, spacing=1.3)

    footer(s, 7)


# ==================== P8 高估意味着什么（等效缝高） ====================
def page_heff():
    s = prs.slides.add_slide(BLANK)
    header(s, "高估这么多，实际意味着什么",
           "把 m³ 换成人能感知的数：这块沟槽相当于多高的缝、同样压差下流量偏大几倍")

    lx = 0.55; lw = 6.06; ly = 1.44; lh = 4.55
    box(s, Inches(lx), Inches(ly), Inches(lw), Inches(lh), fill=WHITE, line=LINE, radius=True)
    text(s, Inches(lx + 0.26), Inches(ly + 0.15), Inches(lw - 0.52), Inches(0.28),
         "导度换算成「相当于多高的光滑缝」", size=14, color=NAVY, bold=True)
    text(s, Inches(lx + 0.26), Inches(ly + 0.44), Inches(lw - 0.52), Inches(0.24),
         "平板关系 K = h³/12，反过来 H =(12K)^⅓；75 nm 平板算回去正好 75.0 nm，可当校验",
         size=9.5, color=GRAY)

    bars = [
        ("平板 75 nm", 75.0, "75.0 nm", SOLID, WHITE),
        ("沿槽 实际", 105.7, "105.7 nm", MBLUE, WHITE),
        ("沿槽 公式", 142.5, "142.5 nm", RED, WHITE),
        ("横槽 实际", 81.1, "81.1 nm", MBLUE, WHITE),
        ("横槽 公式", 92.1, "92.1 nm", RED, WHITE),
    ]
    for i, (lab, val, txtlab, cbar, ctxt) in enumerate(bars):
        yy = 2.26 + i * 0.46
        text(s, Inches(lx + 0.26), Inches(yy), Inches(1.30), Inches(0.30),
             lab, size=10.5, color=SUB, anchor=MSO_ANCHOR.MIDDLE)
        bw = val * 0.02912
        box(s, Inches(2.15), Inches(yy), Inches(bw), Inches(0.30), fill=cbar)
        text(s, Inches(2.27), Inches(yy), Inches(bw - 0.20), Inches(0.30),
             txtlab, size=11, color=ctxt, bold=True, anchor=MSO_ANCHOR.MIDDLE)

    text(s, Inches(lx + 0.26), Inches(4.62), Inches(lw - 0.52), Inches(0.50),
         [("真实几何最高处 h+d = 175 nm、最低处 75 nm。沿槽实际只兑现到 106 nm，"
           "公式以为兑现到 142 nm。", {})], size=10.5, color=SUB, spacing=1.3)
    text(s, Inches(lx + 0.26), Inches(5.12), Inches(lw - 0.52), Inches(0.44),
         "差的 36 nm 就是台阶竖墙的代价：公式几乎全额兑现了深槽，实际没有。",
         size=10.5, color=DRED, spacing=1.3)
    text(s, Inches(lx + 0.26), Inches(5.62), Inches(lw - 0.52), Inches(0.26),
         "横槽只差 11 nm（81 对 92），串联机制下最薄那段本来就在卡着。",
         size=10.5, color=SUB, spacing=1.3)

    rx = 6.85; rw = 5.93
    box(s, Inches(rx), Inches(1.44), Inches(rw), Inches(2.16), fill=WHITE, line=LINE, radius=True)
    text(s, Inches(rx + 0.28), Inches(1.58), Inches(rw - 0.56), Inches(0.26),
         "同样压差下　公式算出的流量偏大", size=13.5, color=NAVY, bold=True)
    text(s, Inches(rx + 0.28), Inches(1.84), Inches(rw - 0.56), Inches(0.22),
         "基准几何 h = 75、d = 100 nm；倍数 = 1 + 偏差", size=9.5, color=GRAY)
    text(s, Inches(rx + 0.28), Inches(2.12), Inches(2.50), Inches(0.52),
         "× 2.45", size=27, color=BLUE, bold=True)
    text(s, Inches(rx + 0.28), Inches(2.66), Inches(2.50), Inches(0.22),
         "沿槽　偏差 +144.95%", size=10, color=SUB)
    text(s, Inches(rx + 3.02), Inches(2.12), Inches(2.50), Inches(0.52),
         "× 1.47", size=27, color=MBLUE, bold=True)
    text(s, Inches(rx + 3.02), Inches(2.66), Inches(2.50), Inches(0.22),
         "横槽　偏差 +46.51%", size=10, color=SUB)
    box(s, Inches(rx + 0.28), Inches(3.02), Inches(rw - 0.56), Inches(0.012), fill=LINE)
    text(s, Inches(rx + 0.28), Inches(3.12), Inches(rw - 0.56), Inches(0.36),
         [("全 18 个几何的平均：沿槽 ×1.89、横槽 ×1.31。", {})], size=10, color=SUB, spacing=1.2)

    box(s, Inches(rx), Inches(3.83), Inches(rw), Inches(2.16), fill=WHITE, line=LINE, radius=True)
    text(s, Inches(rx + 0.28), Inches(3.97), Inches(rw - 0.56), Inches(0.26),
         "同样流量下　公式以为的压力只要这么多", size=13.5, color=NAVY, bold=True)
    text(s, Inches(rx + 0.28), Inches(4.23), Inches(rw - 0.56), Inches(0.22),
         "把偏差翻过来：1 ÷（1 + 偏差）", size=9.5, color=GRAY)
    text(s, Inches(rx + 0.28), Inches(4.50), Inches(2.50), Inches(0.52),
         "41%", size=27, color=GOLD, bold=True)
    text(s, Inches(rx + 0.28), Inches(5.04), Inches(2.50), Inches(0.22),
         "沿槽　少估 59%", size=10, color=SUB)
    text(s, Inches(rx + 3.02), Inches(4.50), Inches(2.50), Inches(0.52),
         "68%", size=27, color=GOLD, bold=True)
    text(s, Inches(rx + 3.02), Inches(5.04), Inches(2.50), Inches(0.22),
         "横槽　少估 32%", size=10, color=SUB)
    box(s, Inches(rx + 0.28), Inches(5.40), Inches(rw - 0.56), Inches(0.012), fill=LINE)
    text(s, Inches(rx + 0.28), Inches(5.50), Inches(rw - 0.56), Inches(0.36),
         [("含义：公式偏乐观，照它估的推动条件会偏松。", {})], size=10, color=SUB, spacing=1.2)

    box(s, Inches(0.55), Inches(6.12), Inches(12.23), Inches(0.52), fill=LBLUE, radius=True)
    box(s, Inches(0.55), Inches(6.12), Inches(0.07), Inches(0.52), fill=BLUE)
    text(s, Inches(0.86), Inches(6.22), Inches(11.7), Inches(0.30),
         [("一句话：高估的是「过流能力」，所以流量跟着一起高估——公式让这块图案看起来比实际好流。",
           {'color': NAVY, 'bold': True, 'size': 12.5})], size=12.5)

    text(s, Inches(0.55), Inches(6.74), Inches(12.23), Inches(0.24),
         [("口径：", {'color': DRED, 'bold': True}),
          ("基准几何 h=75/d=100 nm、Δx=5 nm；流量倍数 = 1+ε、压力比 = 1/(1+ε)，是同一组数的两种读法，"
           "不是实测流量差。单相全充液稳态，不涉及填充快慢。", {})],
         size=9.5, color=SUB, spacing=1.2)

    footer(s, 8)


# ==================== P8 V2 修正 ====================
def page6():
    s = prs.slides.add_slide(BLANK)
    header(s, "修正：能压到多少，哪里压不动",
           "答案是能压下来——沿槽均值从 88.85% 降到 6.40%，但最坏点仍在 10.50% / 18.71%")

    # 左：改善
    L = Inches(0.55); LW = Inches(6.50)
    box(s, L, Inches(1.42), LW, Inches(3.62), fill=WHITE, line=LINE, radius=True)
    text(s, L + Inches(0.26), Inches(1.54), LW - Inches(0.5), Inches(0.28),
         "修得动的地方", size=13, color=BLUE, bold=True)
    text(s, L + Inches(0.26), Inches(1.84), LW - Inches(0.5), Inches(0.26),
         "沿用本研究标定的 V2 系数，不重新拟合", size=10.5, color=GRAY)

    nums = [
        ("35 / 36", "条绝对偏差减小", BLUE),
        ("88.85% → 6.40%", "沿槽平均绝对偏差", MBLUE),
        ("30.63% → 4.42%", "横槽平均绝对偏差", MBLUE),
    ]
    for i, (val, lab, col) in enumerate(nums):
        yy = Inches(2.20) + i * Inches(0.62)
        text(s, L + Inches(0.26), yy, Inches(2.55), Inches(0.36),
             val, size=17, color=col, bold=True)
        text(s, L + Inches(2.95), yy + Inches(0.06), LW - Inches(3.2), Inches(0.28),
             lab, size=11.5, color=SUB)

    box(s, L + Inches(0.26), Inches(4.10), LW - Inches(0.52), Inches(0.014), fill=LINE)
    text(s, L + Inches(0.26), Inches(4.22), LW - Inches(0.5), Inches(0.62),
         [("但注意选点：", {'color': NAVY, 'bold': True}),
          ("h ≥ 50 nm 子集的横槽最大偏差只有 6.92%（15 点），全 18 点是 18.71%。"
           "6.92% 不能当成适用范围承诺。", {})],
         size=11, color=SUB, spacing=1.35)

    # 右：两处修不动
    R = Inches(7.29); RW = Inches(5.49)
    box(s, R, Inches(1.42), RW, Inches(3.62), fill=WHITE, line=LINE, radius=True)
    box(s, R, Inches(1.42), Inches(0.06), Inches(3.62), fill=DRED)
    text(s, R + Inches(0.26), Inches(1.54), RW - Inches(0.5), Inches(0.28),
         "修不动的地方", size=13, color=DRED, bold=True)
    text(s, R + Inches(0.26), Inches(1.84), RW - Inches(0.5), Inches(0.26),
         "两处例外，都不是小数点级别的差别", size=10.5, color=GRAY)

    fails = [
        ("① 最坏点仍在", "残差最大 10.50%（沿槽）/ 18.71%（横槽），"
         "改善只是把最坏从 204.85% 压到 18.71%，不是压进噪声。"),
        ("② 换参考就翻案", "(h,d)=(25,100) 横槽：5 nm 参考下 16.36%→18.71%（变差），"
         "2.5 nm 参考下 21.76%→14.94%（变好）。结论跟着参考网格走。"),
    ]
    for i, (head, body) in enumerate(fails):
        yy = Inches(2.18) + i * Inches(1.28)
        text(s, R + Inches(0.26), yy, RW - Inches(0.5), Inches(0.26),
             head, size=12, color=DRED, bold=True)
        text(s, R + Inches(0.26), yy + Inches(0.28), RW - Inches(0.52), Inches(0.84),
             body, size=11, color=SUB, spacing=1.4)

    # 底部：为何修不满
    box(s, Inches(0.55), Inches(5.20), Inches(12.23), Inches(1.30), fill=NAVY, radius=True)
    text(s, Inches(0.88), Inches(5.28), Inches(3.6), Inches(0.24),
         "为什么修不满：三重原因分不开", size=11, color=RGBColor(0x9C, 0xC0, 0xF0), bold=True)
    text(s, Inches(0.88), Inches(5.54), Inches(11.6), Inches(0.24),
         [("F 只含 ", {}), ("d/w", {'color': GOLD, 'bold': True}),
          ("、不含 ", {}), ("h", {'color': GOLD, 'bold': True}),
          ("，而残差随 h 变化。是模型缺项、参数估计，还是参考误差？现有记录分不开其中任何一项。", {})],
         size=12, color=WHITE)
    text(s, Inches(0.88), Inches(5.86), Inches(11.6), Inches(0.56),
         [("另有硬约束：", {'color': RGBColor(0xC9, 0xDA, 0xF2)}),
          ("9 个标定几何与 9 个扩展几何恰好对应两组不同构建程序，构建差异与几何效应完全重合，无法分离。"
           "扩展数据在选型时已可见，残差只能作回顾性描述，不构成独立预测精度。",
           {'color': RGBColor(0xC9, 0xDA, 0xF2)})],
         size=10.5, spacing=1.25)

    text(s, Inches(0.55), Inches(6.58), Inches(12.23), Inches(0.32),
         [("下一页：", {'color': GRAY}),
          ("修正只能压低“多少”，压不回“朝哪”——两方向不等幅的后果，才是更难修的。", {})],
         size=11, color=SUB)

    footer(s, 9)


# ==================== P9 流向后果 ====================
def page7():
    s = prs.slides.add_slide(BLANK)
    header(s, "问题③　两个方向是否等幅",
           "答案是不等。基准几何 h = 75 nm、d = 100 nm：错的不只是“多少”，还有“朝哪”")

    # 左：方向比柱状
    L = Inches(0.55); LW = Inches(5.55)
    box(s, L, Inches(1.42), LW, Inches(3.90), fill=WHITE, line=LINE, radius=True)
    text(s, L + Inches(0.26), Inches(1.54), LW - Inches(0.5), Inches(0.26),
         "方向比 A = Kyy / Kxx", size=12, color=NAVY, bold=True)
    text(s, L + Inches(0.26), Inches(1.82), LW - Inches(0.5), Inches(0.24),
         "同一几何、同一参考下两个比值", size=10.5, color=GRAY)

    base_y = Inches(4.80)
    bx1 = L + Inches(1.00); bx2 = L + Inches(3.20)
    bwd = Inches(1.30)
    box(s, L + Inches(0.55), base_y, LW - Inches(0.85), Inches(0.015), fill=LINE)
    h1 = Inches(1.135); h2 = Inches(1.90)
    box(s, bx1, base_y - h1, bwd, h1, fill=MBLUE, radius=True)
    text(s, bx1, base_y - h1 + Inches(0.14), bwd, Inches(0.38),
         "2.21", size=22, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    text(s, bx1 - Inches(0.15), base_y + Inches(0.10), bwd + Inches(0.30), Inches(0.46),
         "OpenLB\n离散参考", size=10.5, color=SUB, align=PP_ALIGN.CENTER, spacing=1.2)
    box(s, bx2, base_y - h2, bwd, h2, fill=BLUE, radius=True)
    text(s, bx2, base_y - h2 + Inches(0.14), bwd, Inches(0.38),
         "3.70", size=22, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    text(s, bx2 - Inches(0.15), base_y + Inches(0.10), bwd + Inches(0.30), Inches(0.46),
         "局部立方律\n原公式", size=10.5, color=SUB, align=PP_ALIGN.CENTER, spacing=1.2)

    box(s, L + Inches(0.55), Inches(2.08), LW - Inches(1.1), Inches(0.76), fill=LBLUE, radius=True)
    text(s, L + Inches(0.72), Inches(2.16), LW - Inches(1.4), Inches(0.60),
         [("模型高估 ", {}), ("约 67%", {'color': DRED, 'bold': True, 'size': 15}),
          ("　—— 相对增幅，不是百分点。", {'size': 10.5}),
          ("\n仅此基准几何，不推广到其他几何。", {'size': 10})],
         size=11, color=SUB, spacing=1.3)

    # 右：角差图
    R = Inches(6.36); RW = Inches(6.42)
    box(s, R, Inches(1.42), RW, Inches(3.90), fill=WHITE, line=LINE, radius=True)
    text(s, R + Inches(0.26), Inches(1.54), RW - Inches(0.5), Inches(0.26),
         "45° 驱动下重建的平均流向", size=12, color=NAVY, bold=True)
    text(s, R + Inches(0.26), Inches(1.82), RW - Inches(0.5), Inches(0.24),
         "同一线性张量关系，两组主导度各自重建", size=10.5, color=GRAY)

    ox, oy = R + Inches(0.85), Inches(4.74)
    ln = 2.15
    for deg, col in [(45.0, MBLUE), (54.2, BLUE)]:
        ex = ox + Inches(ln * math.cos(math.radians(deg)))
        ey = oy - Inches(ln * math.sin(math.radians(deg)))
        arrow_line(s, ox, oy, ex, ey, col, width=2.0)
    box(s, ox, oy, Inches(2.45), Inches(0.012), fill=LINE)
    box(s, ox, oy - Inches(2.20), Inches(0.012), Inches(2.20), fill=LINE)
    text(s, ox + Inches(0.05), oy + Inches(0.10), Inches(2.3), Inches(0.24),
         "沿槽方向 →", size=10, color=GRAY)

    text(s, R + Inches(2.34), Inches(2.72), Inches(1.72), Inches(0.24),
         "原公式重建", size=10.5, color=BLUE, bold=True)
    text(s, R + Inches(2.48), Inches(3.16), Inches(1.72), Inches(0.24),
         "OpenLB 重建", size=10.5, color=MBLUE, bold=True)

    # 角差数字块
    box(s, R + Inches(4.18), Inches(2.24), Inches(1.96), Inches(1.34), fill=LBLUE, radius=True)
    text(s, R + Inches(4.18), Inches(2.40), Inches(1.96), Inches(0.50),
         "9.20°", size=28, color=RED, bold=True, align=PP_ALIGN.CENTER)
    text(s, R + Inches(4.18), Inches(2.96), Inches(1.96), Inches(0.24),
         "两线夹角", size=10.5, color=SUB, align=PP_ALIGN.CENTER)
    text(s, R + Inches(4.18), Inches(3.20), Inches(1.96), Inches(0.22),
         "（示意，非按比例）", size=9.5, color=GRAY, align=PP_ALIGN.CENTER)

    # 底部：后果
    box(s, Inches(0.55), Inches(5.46), Inches(12.23), Inches(1.02), fill=NAVY, radius=True)
    text(s, Inches(0.88), Inches(5.56), Inches(4.0), Inches(0.24),
         "这意味着什么", size=11, color=RGBColor(0x9C, 0xC0, 0xF0), bold=True)
    text(s, Inches(0.88), Inches(5.86), Inches(11.6), Inches(0.50),
         [("降阶模型若只用单一系数、或沿用局部立方律给出的各向异性，", {}),
          ("45° 方向上的通量会被指到差 9.2° 的方向", {'color': GOLD, 'bold': True}),
          ("。填充前沿位置与困气位置都依此确定——这是本文最可操作的一条后果。", {})],
         size=13, color=WHITE, spacing=1.3)

    text(s, Inches(0.55), Inches(6.58), Inches(12.23), Inches(0.40),
         [("边界：", {'color': DRED, 'bold': True}),
          ("方向由同一线性张量关系重建，不是实验测得的流向误差；9.20° 是角差，不是填充预测；"
           "动态挤压与填充过程本文未验证，不对其作断言。", {})],
         size=10.5, color=SUB, spacing=1.25)

    footer(s, 10)


# ==================== P11 六条结论 ====================
def page8():
    s = prs.slides.add_slide(BLANK)
    header(s, "六条结论", "三个问题答完，连同立论与两条补充对照，收成六条")

    items = [
        ("一", "定位",
         "固定周期与槽宽的全充液矩形沟槽中，评价局部立方律的双向偏差、各向异性后果与本研究标定的 V2 修正的表现。",
         "不是首创，是这一族几何上的配套定量评价。"),
        ("二", "原公式偏差",
         "36 条 5 nm 主方向结果全部高估：沿槽 +10.30% 至 +204.85%，横槽 +8.11% 至 +54.19%（Δx = 5 nm）。",
         "方向由附录 E 定理保证；幅度是这 18 种几何的实测范围。"),
        ("三", "基准各向异性",
         "h=75、d=100 时，OpenLB 比 2.21、原公式 3.70，相对高估约 67%；45° 驱动流向差 9.20°。",
         "67% 是相对增幅、仅此基准几何；两个主值与比值都须检查。"),
        ("四", "V2 回顾性改善",
         "35/36 条改善；沿槽平均绝对偏差 88.85%→6.40%，横槽 30.63%→4.42%；最坏 10.50% / 18.71%。",
         "回顾性比较，非独立预测；h=25、d=100 横槽的改善判断随参考网格改变。"),
        ("五", "新增间隙与静态接入",
         "补算 h=100 nm（不在原标定集，沿用本研究标定的 V2 系数、未重拟合），数值按沿槽/横槽排："
         "原公式 +126.62%/+49.43%，V2 −2.03%/+4.39%；方向比 A 偏差 −6.15%；"
         "静态接入后出口流量降 56.77%/30.14%。",
         "称“新增间隙固定公式对照”、不称盲测；程序间一致 ≠ 导度准确；不是动态挤压、载荷或填充时间的证据。"),
        ("六", "理论上界与机制诊断",
         "理想连续模型中 h³/12 ≤ K ≤ 原公式，仅 d=0 三者合一；46 条记录（36＋8＋2）均落在界内。"
         "两宽度组的梯度诊断给出方向性结构。",
         "上界只对连续模型；机制诊断限于指定基线、分解与几何；46 条不是 46 次独立验证。"),
    ]
    y = Inches(1.42)
    for i, (num, head, body, caveat) in enumerate(items):
        h = Inches(0.855)
        box(s, Inches(0.55), y, Inches(12.23), h, fill=LBLUE2, line=LINE, radius=True)
        box(s, Inches(0.55), y, Inches(0.06), h, fill=BLUE if i % 2 == 0 else NAVY)
        text(s, Inches(0.78), y + Inches(0.095), Inches(0.42), Inches(0.30),
             num, size=14, color=BLUE, bold=True)
        text(s, Inches(1.28), y + Inches(0.065), Inches(2.35), Inches(0.26),
             head, size=13, color=NAVY, bold=True)
        text(s, Inches(1.28), y + Inches(0.315), Inches(7.05), Inches(0.48),
             body, size=10.5, color=TXT, spacing=1.32)
        text(s, Inches(8.62), y + Inches(0.075), Inches(4.02), Inches(0.70),
             caveat, size=9.5, color=SUB, spacing=1.35)
        y = y + h + Inches(0.062)

    footer(s, 11)


# ==================== P11 四条边界 ====================
def page9():
    s = prs.slides.add_slide(BLANK)
    header(s, "四条边界：六条结论各自能说到哪一步",
           "不是结果不可信，而是把可说的范围划清楚")

    cw = Inches(5.985); ch = Inches(2.24)
    xs = [Inches(0.55), Inches(0.55) + cw + Inches(0.26)]
    ys = [Inches(1.44), Inches(1.44) + ch + Inches(0.26)]

    cards = [
        ("① 5 nm 是离散参考，不是真值",
         "最薄间隙 h=25 nm 在该网格下 h/Δx = 5（壁面半格插值）。加密到 2.5 nm 后，沿槽变 −0.386%、横槽变 −4.431%；"
         "0.625 nm 的核查因内存限制未完成。连续解误差至今未定。",
         "所以说的是“相对 5 nm 参考的偏差”，不是“真实误差”。"),
        ("② V2 是回顾性比较，不是独立预测",
         "9 个标定几何与 9 个扩展几何恰好对应两组不同构建程序；扩展数据在选型时已可见。",
         "V2 的精度主张只到“在标定几何族内回顾性残差”，不构成盲测。"),
        ("③ S4 薄隙网格控制未通过",
         "h=30 nm、d=80 nm 的薄隙网格加密控制残差 1.328%，超过 1% 门槛。",
         "历史 FAIL 原样保留，不改写为 PASS；它与主地图的 h=25、d=100 是两个几何。"),
        ("④ w 恒定，d/w 与 d 完全共线",
         "w 恒为 120 nm，d/w 只能取 0.208 / 0.417 / 0.625 / 0.833 / 1.000，与 d 严格同步。",
         "V2 的 F(d/w) 在本文数据里与“任何只含 d 的函数”不可区分；w 的作用从未被检验。"),
    ]
    for i, (head, body, tail) in enumerate(cards):
        x = xs[i % 2]; y = ys[i // 2]
        box(s, x, y, cw, ch, fill=WHITE, line=LINE, radius=True)
        box(s, x, y, Inches(0.06), ch, fill=DRED)
        text(s, x + Inches(0.24), y + Inches(0.18), cw - Inches(0.48), Inches(0.30),
             head, size=13, color=DRED, bold=True)
        text(s, x + Inches(0.24), y + Inches(0.58), cw - Inches(0.50), Inches(0.88),
             body, size=10.5, color=SUB, spacing=1.4)
        box(s, x + Inches(0.24), y + Inches(1.52), cw - Inches(0.48), Inches(0.012), fill=LINE)
        text(s, x + Inches(0.24), y + Inches(1.64), cw - Inches(0.50), Inches(0.50),
             tail, size=10.5, color=NAVY, spacing=1.35)

    text(s, Inches(0.55), Inches(6.50), Inches(12.23), Inches(0.32),
         [("下一页：", {'color': GRAY}),
          ("边界说的是“不能说”，还有一类是“还不知道”——三类分开列，才知道下一步往哪走。", {})],
         size=11, color=SUB)

    footer(s, 12)


# ==================== P12 还需回答的问题 ====================
def page10():
    s = prs.slides.add_slide(BLANK)
    header(s, "还需回答的问题",
           "三类分法：能答但受噪声限 / 设计上分不开 / 必须新算")

    cw = Inches(3.98); gap = Inches(0.145)
    xs = [Inches(0.55) + i * (cw + gap) for i in range(3)]
    top = Inches(1.42); ch = Inches(4.72)

    cols = [
        ("甲　受分辨率所限", "能答，但答案本身带噪声", MBLUE, LBLUE2, BLUE,
         [("h = 25 为什么反常",
           "d=100 时沿槽偏差 139%→154%→145%→108%，非单调。h=25 仅 h/Δx=5，疑为网格偏置，未证实。"),
          ("真实误差到底多大",
           "2.5 nm 显示横槽 −4.43%；0.625 nm 因内存未完成。连续解误差始终未定。"),
          ("V2 残差为何随 h 变",
           "因子缺 h、参数估计、参考误差三者混在一起，现有记录分不开。")]),
        ("乙　设计上分不开", "补算也救不回，只能声明", RGBColor(0x85, 0x4F, 0x0B),
         RGBColor(0xFA, 0xEE, 0xDA), RGBColor(0x85, 0x4F, 0x0B),
         [("构建与几何完全重合",
           "9 标定全属旧构建、9 扩展全属新构建。分离二者需交叉设计，现有数据不可能。"),
          ("w 的作用从未检验",
           "w 恒 120 nm，d/w 与 d 共线——F(d/w) 在本数据里不可辨识。"),
          ("其他图案未覆盖",
           "其他占空比、其他槽宽、图案交界均无数据。")]),
        ("丙　必须新算", "这是下一步的入口", DRED,
         RGBColor(0xFC, 0xEB, 0xEB), DRED,
         [("上界为何松紧悬殊",
           "沿槽松到 3.05 倍、横槽只松 1.54 倍。定理只给方向不给幅度——这是最值得追的一条。"),
          ("耗散究竟在哪产生",
           "侧壁剪切？台阶再分布？需局部耗散分解，现有结果不能判定。"),
          ("9.2° 真的影响工艺吗",
           "需要动态挤压或填充模型验证，本文范围外。")]),
    ]

    for i, (title, sub, head_col, fill_col, line_col, qs) in enumerate(cols):
        x = xs[i]
        box(s, x, top, cw, ch, fill=WHITE, line=LINE, radius=True)
        box(s, x, top, cw, Inches(0.68), fill=fill_col if i > 0 else LBLUE)
        text(s, x + Inches(0.22), top + Inches(0.12), cw - Inches(0.44), Inches(0.28),
             title, size=12.5, color=head_col, bold=True)
        text(s, x + Inches(0.22), top + Inches(0.40), cw - Inches(0.44), Inches(0.24),
             sub, size=10, color=SUB)
        box(s, x, top + Inches(0.67), cw, Inches(0.012), fill=line_col)

        yq = top + Inches(0.82)
        for j, (head, body) in enumerate(qs):
            text(s, x + Inches(0.22), yq, cw - Inches(0.44), Inches(0.26),
                 head, size=11.5, color=NAVY, bold=True)
            text(s, x + Inches(0.22), yq + Inches(0.26), cw - Inches(0.44), Inches(0.62),
                 body, size=10, color=SUB, spacing=1.4)
            yq = yq + Inches(1.24)

    box(s, Inches(0.55), Inches(6.26), Inches(12.23), Inches(0.72), fill=NAVY, radius=True)
    text(s, Inches(0.88), Inches(6.36), Inches(11.6), Inches(0.52),
         [("汇报口径：", {'color': RGBColor(0x9C, 0xC0, 0xF0), 'bold': True, 'size': 10.5}),
          ("甲类说“知道，但受噪声限”；乙类说“设计上分不开，已如实声明”；丙类说“这就是下一步”。"
           "三类都不辩解，只陈述事实。", {'color': WHITE, 'size': 12.5})],
         size=12.5, spacing=1.3)

    footer(s, 13)


# ==================== P13 使用条件卡片（可单独拆出） ====================
def page_card():
    s = prs.slides.add_slide(BLANK)
    header(s, "这张数表怎么用：三个能、四个前提、五条红线",
           "等效缝高把导度翻译成厚度——但它只能翻译已有结果，不能新增结果")

    GREEN = RGBColor(0x2E, 0x7D, 0x32)
    AMBER = RGBColor(0x9A, 0x63, 0x00)

    # ---------- 左上：能用 ----------
    L = Inches(0.55); LW = Inches(6.00)
    box(s, L, Inches(1.44), LW, Inches(2.00), fill=WHITE, line=LINE, radius=True)
    box(s, L, Inches(1.44), Inches(0.06), Inches(2.00), fill=GREEN)
    text(s, L + Inches(0.24), Inches(1.56), LW - Inches(0.46), Inches(0.28),
         "能用来做这三件事", size=13.5, color=GREEN, bold=True)
    can = [("① 估流量", "同压差下  Q = Q平板 × (H/h)³"),
           ("② 估压差", "同流量下  Δp = Δp平板 × (h/H)³"),
           ("③ 看方向差", "两个 H 相除，三次方就是各向异性比")]
    for i, (h1, h2) in enumerate(can):
        yy = Inches(1.90) + i * Inches(0.50)
        text(s, L + Inches(0.24), yy, Inches(1.34), Inches(0.26),
             h1, size=11.5, color=NAVY, bold=True)
        text(s, L + Inches(1.64), yy - Inches(0.01), LW - Inches(1.88), Inches(0.26),
             h2, size=11, color=SUB)

    # ---------- 左下：前提 ----------
    box(s, L, Inches(3.58), LW, Inches(2.16), fill=WHITE, line=LINE, radius=True)
    box(s, L, Inches(3.58), Inches(0.06), Inches(2.16), fill=AMBER)
    text(s, L + Inches(0.24), Inches(3.70), LW - Inches(0.46), Inches(0.28),
         "用之前必须成立的四个前提", size=13.5, color=AMBER, bold=True)
    need = [("物理", "单相／全充液／稳态／无自由面"),
            ("流体", "牛顿、恒黏度（黏度只作比例因子）"),
            ("图案", "w=120 nm、P=240 nm、占空比 0.5 固定"),
            ("格点", "(h,d) 落在已算格点上；插值＝猜测")]
    for i, (tag, body) in enumerate(need):
        yy = Inches(4.04) + i * Inches(0.42)
        text(s, L + Inches(0.24), yy, Inches(0.62), Inches(0.24),
             tag, size=10, color=GRAY, bold=True)
        text(s, L + Inches(0.90), yy - Inches(0.01), LW - Inches(1.14), Inches(0.24),
             body, size=11, color=SUB)

    # ---------- 右：红线 ----------
    R = Inches(6.80); RW = Inches(5.98)
    box(s, R, Inches(1.44), RW, Inches(4.30), fill=WHITE, line=RGBColor(0xE8, 0xC5, 0xC3), radius=True)
    box(s, R, Inches(1.44), Inches(0.06), Inches(4.30), fill=DRED)
    text(s, R + Inches(0.26), Inches(1.56), RW - Inches(0.50), Inches(0.28),
         "明确不能用的五条红线", size=13.5, color=DRED, bold=True)
    bans = [
        ("① 不能说“更准”", "H 与 K 一一对应、信息量完全相同。让数好懂，不让数变准。"),
        ("② 不能算填充", "填充速度、前沿、困气属瞬态两相，本表是定常单相。"),
        ("③ 不能换图案", "w 全程固定 120 nm，d/w 与 d 共线，“w 的影响”从未检验。"),
        ("④ 不能当真实误差", "5 nm 是离散参考、不是连续解真值；h=25 仅 h/Δx=5。"),
        ("⑤ 不能两方向平均", "平均值不对应任何物理流道。分开报，或按流向投影。"),
    ]
    for i, (h1, h2) in enumerate(bans):
        yy = Inches(1.94) + i * Inches(0.74)
        text(s, R + Inches(0.26), yy, RW - Inches(0.52), Inches(0.26),
             h1, size=11.5, color=DRED, bold=True)
        text(s, R + Inches(0.26), yy + Inches(0.26), RW - Inches(0.54), Inches(0.42),
             h2, size=10.5, color=SUB, spacing=1.35)

    # ---------- 底部 ----------
    box(s, Inches(0.55), Inches(5.92), Inches(12.23), Inches(0.96), fill=NAVY, radius=True)
    text(s, Inches(0.88), Inches(6.02), Inches(7.4), Inches(0.34),
         [("一句话红线：", {'color': GOLD, 'bold': True}),
          ("H 只能“翻译”已有结果，不能“新增”结果。", {'color': WHITE})],
         size=13.5, spacing=1.2)
    text(s, Inches(8.42), Inches(6.04), Inches(4.2), Inches(0.72),
         [("基准几何 h=75 / d=100：", {'color': RGBColor(0x9C, 0xC0, 0xF0), 'size': 10}),
          ("\n沿槽 105.67 nm（2.80×）　横槽 81.12 nm（1.27×）", {'color': WHITE, 'size': 11})],
         size=11, spacing=1.3)

    footer(s, 14)


page1(); page2(); page_formula(); page3(); page4(); page5()
page_interval(); page_heff(); page6(); page7(); page8(); page9(); page10(); page_card()
prs.save("/home/dell/yuanyuanxu/SIM240/docs/reports/PPT_论文汇报_20261109/论文汇报.pptx")
print(f"已生成 {TOTAL} 页")
