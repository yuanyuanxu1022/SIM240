#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SIM240 本周工作汇报 PPT — 2026-11-06 → 11-10（十四页）

叙事：这一周把第一篇论文从「数据齐了」推到「稿件能投」。
结构：一句话 → 起点/现在 → 五条主线 → 五页详述 → 数字一页 → 问题与返工 → 红线 → 开放项 → 下周。

所有数字的出处见同目录 DATA_SOURCES.md；绘图不允许出现无出处的数字。
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

TOTAL = 17
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


def tag(s, l, t, label, fill=LBLUE, color=BLUE, w=Inches(1.02)):
    """小标签：日期 / 编号"""
    box(s, l, t, w, Inches(0.26), fill=fill, radius=True)
    text(s, l, t + Inches(0.033), w, Inches(0.22), label,
         size=9.5, color=color, bold=True, align=PP_ALIGN.CENTER)


# ==================== P1 封面 ====================
def p1():
    s = prs.slides.add_slide(BLANK)
    box(s, 0, 0, prs.slide_width, Inches(0.18), fill=BLUE)
    box(s, 0, Inches(7.32), prs.slide_width, Inches(0.18), fill=PALE)
    text(s, Inches(0.9), Inches(0.72), Inches(8), Inches(0.4),
         "本周工作汇报 ｜ 2026-11-06 → 2026-11-10", size=15, color=GRAY)

    text(s, Inches(1.0), Inches(2.10), Inches(11.33), Inches(1.9),
         "从「数据齐了」\n到「稿件能投」",
         size=44, color=NAVY, bold=True, align=PP_ALIGN.CENTER, spacing=1.22)
    box(s, Inches(5.67), Inches(4.02), Inches(2.0), Inches(0.04), fill=BLUE)
    text(s, Inches(1.4), Inches(4.30), Inches(10.5), Inches(1.4),
         "这一周补了四个洞：闭环、口径、上下界、宽度证据\n外加一件以前没做过的事——把内部工作稿变成投稿稿",
         size=19, color=SUB, align=PP_ALIGN.CENTER, spacing=1.45)
    text(s, Inches(0.9), Inches(6.42), Inches(11.5), Inches(0.4),
         "汇报人：＿＿＿＿　　2026 年 11 月", size=14, color=GRAY, align=PP_ALIGN.CENTER)


# ==================== P2 一句话 + 三个变化 ====================
def p2():
    s = prs.slides.add_slide(BLANK)
    header(s, "一句话说这一周", "如果只能说一句")

    box(s, Inches(0.55), Inches(1.50), Inches(12.23), Inches(1.42), fill=LBLUE, radius=True)
    box(s, Inches(0.55), Inches(1.50), Inches(0.08), Inches(1.42), fill=BLUE)
    text(s, Inches(0.95), Inches(1.66), Inches(11.6), Inches(1.12),
         [("第一篇论文从「数据齐了、但说不清能投什么」，推到「六条结论定稿、理论补上上下界、投稿稿已生成」。", {'size': 19, 'bold': True, 'color': NAVY}),
          ("\n剩下的不是科学问题，是作者信息和期刊格式。", {'size': 15, 'color': SUB})],
         spacing=1.42)

    cards = [
        ("结论", "从三份文件三种说法", "六条定稿，三方逐条对齐",
         "结论文件 / 稿件 §6 / 汇报 PPT 第 11 页\n现在「现有不一致：无」", BLUE),
        ("理论", "原来只有上界", "补上下界 + 区间宽度",
         "46 条记录 0 违反；还发现两个\n「越知道越没用」的反向结论", MBLUE),
        ("交付", "母稿带 4 个内部附录", "投稿派生件已生成",
         "CN 725→653 行、EN 645→643 行\n零数字改动，--check 一致", GREEN),
    ]
    y = Inches(3.22); h = Inches(3.30); w = Inches(3.90); gap = Inches(0.265)
    for i, (label, before, after, detail, col) in enumerate(cards):
        l = Inches(0.55) + i * (w + gap)
        box(s, l, y, w, h, fill=WHITE, line=LINE, radius=True)
        box(s, l, y, w, Inches(0.055), fill=col)
        text(s, l + Inches(0.26), y + Inches(0.20), w - Inches(0.5), Inches(0.3),
             label, size=13, color=col, bold=True)
        text(s, l + Inches(0.26), y + Inches(0.58), w - Inches(0.5), Inches(0.3),
             before, size=12, color=GRAY)
        text(s, l + Inches(0.26), y + Inches(0.90), w - Inches(0.5), Inches(0.26),
             "↓", size=14, color=PALE, bold=True)
        text(s, l + Inches(0.26), y + Inches(1.22), w - Inches(0.5), Inches(0.5),
             after, size=15.5, color=NAVY, bold=True, spacing=1.3)
        box(s, l + Inches(0.26), y + Inches(1.82), w - Inches(0.52), Inches(0.012), fill=LINE)
        text(s, l + Inches(0.26), y + Inches(1.98), w - Inches(0.5), Inches(1.1),
             detail, size=10.5, color=SUB, spacing=1.42)
    footer(s, 2)


# ==================== P3 起点 vs 现在 ====================
def p3():
    s = prs.slides.add_slide(BLANK)
    header(s, "起点在哪：上周五 vs 今天", "同一件事，两个时点的样子")

    rows = [
        ("结论口径", "五条，与稿件 §6 结构不对应，PPT 缺两项", "六条定稿，文件/稿件/PPT 三方逐条对齐"),
        ("理论约束", "只有上界：只说「一定高估」，不说「松多少」", "上下界（附录 E.1）+ 区间宽度闭式，46 条 0 违反"),
        ("比较记录", "36 主 + 8 加密 = 44 点边界清单", "46 条（+h=100 新增 2 条），零反例"),
        ("机制证据", "单宽度组，宽度依赖无对照", "成对宽度组 w=60/240，独立小节 S14"),
        ("稿件形态", "母稿带附录 A—D，整份转 PDF 会出双份图注", "投稿派生件，附录 A—D 已摘除"),
        ("版本管理", "文件名日期 ≠ 内容版本，曾多次改错稿", "单一裁决文件 + MANIFEST + 18 条哈希"),
        ("方法论证", "有数据有结论，但「为什么这样验」只能口头讲", "三条文献惯例逐条对上，全文八节自成闭环"),
    ]
    y0 = Inches(1.50); rh = Inches(0.665)
    # 表头
    text(s, Inches(0.72), y0 - Inches(0.06), Inches(2.3), Inches(0.3),
         "维度", size=11.5, color=GRAY, bold=True)
    text(s, Inches(3.05), y0 - Inches(0.06), Inches(4.6), Inches(0.3),
         "11-05 收工时", size=11.5, color=GRAY, bold=True)
    text(s, Inches(7.85), y0 - Inches(0.06), Inches(4.9), Inches(0.3),
         "11-10 收工时", size=11.5, color=GREEN, bold=True)
    y = y0 + Inches(0.24)
    for i, (dim, before, after) in enumerate(rows):
        fill = WHITE if i % 2 == 0 else LBLUE2
        box(s, Inches(0.55), y, Inches(12.23), rh, fill=fill, line=LINE)
        text(s, Inches(0.75), y + Inches(0.19), Inches(2.15), Inches(0.4),
             dim, size=12.5, color=NAVY, bold=True)
        text(s, Inches(3.05), y + Inches(0.14), Inches(4.55), Inches(0.5),
             before, size=11, color=GRAY, spacing=1.32)
        text(s, Inches(7.85), y + Inches(0.14), Inches(4.75), Inches(0.5),
             after, size=11, color=TXT, spacing=1.32)
        y = y + rh
    text(s, Inches(0.55), Inches(6.42), Inches(12.23), Inches(0.5),
         [("唯一没有推进的一格：", {'size': 11.5, 'color': AMBER, 'bold': True}),
          ("投稿就绪状态仍是 false。卡点不在科学内容，在作者信息（作者/基金/COI/CRediT/AI 声明）与期刊定型。", {'size': 11.5, 'color': SUB})])
    footer(s, 3)


# ==================== P4 五条主线 ====================
def p4():
    s = prs.slides.add_slide(BLANK)
    header(s, "这一周做了五件事", "按时间排，不是按重要性排")

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
    y = Inches(1.72); h = Inches(4.42); w = Inches(2.24)
    gap = (Inches(12.23) - 5 * w) / 4
    # 时间轴
    conn(s, Inches(1.67), Inches(1.60), Inches(11.66), Inches(1.60), PALE, 2.2)
    for i, (date, title, what, why, col) in enumerate(items):
        l = Inches(0.55) + i * (w + gap)
        cx = l + w / 2
        # 节点
        dot = s.shapes.add_shape(MSO_SHAPE.OVAL, cx - Inches(0.075), Inches(1.525),
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

    text(s, Inches(0.55), Inches(6.40), Inches(12.23), Inches(0.5),
         [("五件事共用一条标准：", {'size': 11.5, 'bold': True, 'color': NAVY}),
          ("每一个新说法都必须能指到「稿件哪一节 + 哪张表 + 哪份原始数据」，指不到的就不写进稿。", {'size': 11.5, 'color': SUB}),
          ("\n另有一条贯穿全周的方法线：11-05 查文献 → 11-06 核对 OpenLB 源码 → 本周逐条落进稿子。下面两页专门讲这条。", {'size': 10.5, 'color': BLUE})])
    footer(s, 4)


# ==================== P5 主线① 闭环 ====================
def p5():
    s = prs.slides.add_slide(BLANK)
    header(s, "① 补闭环：一个「没参与训练」的间隙",
           "11-06 ｜ h=100 nm 不在 V2 的 9 个标定几何里，正好当对照")

    # 左：做法
    L = Inches(0.55); LW = Inches(5.55)
    box(s, L, Inches(1.48), LW, Inches(2.28), fill=WHITE, line=LINE, radius=True)
    text(s, L + Inches(0.24), Inches(1.62), LW - Inches(0.48), Inches(0.28),
         "做了什么", size=13, color=BLUE, bold=True)
    text(s, L + Inches(0.24), Inches(1.94), LW - Inches(0.48), Inches(0.58),
         [("4 个新算例，各约 50 秒，合计 3 分 25 秒。", {}),
          ("预测值在开跑前就写进方案，事后未改。", {})],
         size=11.5, color=TXT, spacing=1.5)
    # 用两行 bullet 更清楚
    text(s, L + Inches(0.24), Inches(2.60), LW - Inches(0.48), Inches(1.1),
         [("· h=100/d=100 两方向（新间隙）", {}),
          ("\n· h=75/d=100 换构建复跑（查旧账）", {})],
         size=11, color=SUB, spacing=1.65)

    # 左下：结果
    box(s, L, Inches(3.92), LW, Inches(2.52), fill=LBLUE, radius=True)
    box(s, L, Inches(3.92), Inches(0.075), Inches(2.52), fill=BLUE)
    text(s, L + Inches(0.26), Inches(4.06), LW - Inches(0.5), Inches(0.28),
         "结果：同一点上，原公式错得多、V2 基本对上", size=12, color=BLUE, bold=True)
    res = [("原公式", "+49.43%", "+126.62%", RED),
           ("V2", "+4.39%", "−2.03%", GREEN)]
    text(s, L + Inches(1.28), Inches(4.40), Inches(1.5), Inches(0.24),
         "横槽", size=9.5, color=GRAY)
    text(s, L + Inches(2.78), Inches(4.40), Inches(1.5), Inches(0.24),
         "沿槽", size=9.5, color=GRAY)
    for i, (nm, a, b, col) in enumerate(res):
        yy = Inches(4.68) + i * Inches(0.52)
        text(s, L + Inches(0.26), yy, Inches(1.0), Inches(0.3),
             nm, size=12, color=SUB, bold=True)
        text(s, L + Inches(1.28), yy, Inches(1.45), Inches(0.3),
             a, size=14, color=col, bold=True)
        text(s, L + Inches(2.78), yy, Inches(1.45), Inches(0.3),
             b, size=14, color=col, bold=True)
    text(s, L + Inches(0.26), Inches(5.78), LW - Inches(0.5), Inches(0.5),
         "方向比 A：OpenLB 1.6690、V2 1.5664，相对偏差 −6.15%", size=10, color=SUB)

    # 右：关旧账
    R = Inches(6.40); RW = Inches(6.38)
    box(s, R, Inches(1.48), RW, Inches(2.28), fill=LGREEN, radius=True)
    box(s, R, Inches(1.48), Inches(0.075), Inches(2.28), fill=GREEN)
    text(s, R + Inches(0.26), Inches(1.62), RW - Inches(0.5), Inches(0.28),
         "顺手关掉一个挂了近三周的问题", size=12, color=GREEN, bold=True)
    text(s, R + Inches(0.26), Inches(1.96), RW - Inches(0.5), Inches(1.7),
         [("两版二进制（285f67a0 / 57611b21）在 h=75/d=100 上输出", {'size': 11.5, 'color': TXT}),
          ("逐位相同", {'size': 11.5, 'color': GREEN, 'bold': True}),
          ("：Kyy 9.8340759586436518e−23、步数 4329。", {'size': 11.5, 'color': TXT}),
          ("\n以前无法排除「两个构建混用导致差异」，现在有了实测反证。", {'size': 11, 'color': SUB})],
         spacing=1.5)

    # 右下：边界
    box(s, R, Inches(3.92), RW, Inches(2.52), fill=LAMBER, radius=True)
    box(s, R, Inches(3.92), Inches(0.075), Inches(2.52), fill=AMBER)
    text(s, R + Inches(0.26), Inches(4.06), RW - Inches(0.5), Inches(0.28),
         "这一页不能说的话（很重要）", size=12, color=AMBER, bold=True)
    text(s, R + Inches(0.26), Inches(4.38), RW - Inches(0.5), Inches(1.95),
         [("· 不称「盲测」。稿里的名字是「新增间隙固定公式对照」。", {}),
          ("· 只复跑了一个几何，不能外推 18 个几何都等价。", {}),
          ("· 沿槽残差 7.93 个百分点，超过预设 5 个点筛查 → 反而坐实「F 只依赖 d/w」不成立，这条要写进论文，不因对照通过而撤回。", {})],
         size=10.5, color=SUB, spacing=1.5)
    footer(s, 17)


# ==================== P6 主线② 结论定口径 ====================
def p6():
    s = prs.slides.add_slide(BLANK)
    header(s, "② 定口径：从「三种说法」到「一份清单」",
           "11-08 定稿 → 11-09 绑定证据 → 11-10 稿件同步重排")

    # 上：问题
    box(s, Inches(0.55), Inches(1.46), Inches(12.23), Inches(1.02), fill=LAMBER, radius=True)
    box(s, Inches(0.55), Inches(1.46), Inches(0.075), Inches(1.02), fill=AMBER)
    text(s, Inches(0.90), Inches(1.58), Inches(11.6), Inches(0.8),
         [("问题：同一批结果，三份文件三种说法——", {'size': 12, 'color': AMBER, 'bold': True}),
          ("结论文件写五条、稿件 §6 也是五条但划分不同、汇报 PPT 第 10 页只有四条（缺新增间隙与机制诊断）。", {'size': 12, 'color': SUB}),
          ("\n导师问「到底有几条」时，当时答不出唯一答案。", {'size': 11.5, 'color': AMBER})],
         spacing=1.45)

    # 六条
    items = [
        ("一", "定位与数据规模", "18 几何 36 条，＋8＋2＝46 条；分母仍 36"),
        ("二", "原式全部高估", "沿槽 +10.30~+204.85%、横槽 +8.11~+54.19%"),
        ("三", "两方向不等幅及后果", "A 2.21→3.70 约 +67%；45° 流向差 9.20°"),
        ("四", "V2 回顾性改善", "35/36；MAE 88.85→6.40 / 30.63→4.42"),
        ("五", "新增间隙与静态接入", "+4.39/−2.03（横/沿）；A −6.15%"),
        ("六", "理论上界与机制诊断", "h³/12 ≤ K ≤ 原式；46 条均落在界内"),
    ]
    y = Inches(2.72)
    for i, (num, head, body) in enumerate(items):
        col = i % 2
        row = i // 2
        l = Inches(0.55) + col * Inches(6.24)
        t = y + row * Inches(0.92)
        box(s, l, t, Inches(6.0), Inches(0.82), fill=WHITE, line=LINE, radius=True)
        box(s, l, t, Inches(0.05), Inches(0.82), fill=BLUE if i % 2 == 0 else MBLUE)
        text(s, l + Inches(0.16), t + Inches(0.16), Inches(0.35), Inches(0.3),
             num, size=13, color=BLUE, bold=True)
        text(s, l + Inches(0.56), t + Inches(0.11), Inches(2.3), Inches(0.3),
             head, size=11.5, color=NAVY, bold=True)
        text(s, l + Inches(0.56), t + Inches(0.42), Inches(5.3), Inches(0.32),
             body, size=10, color=SUB)

    # 底部：现在的状态
    box(s, Inches(0.55), Inches(5.66), Inches(12.23), Inches(0.82), fill=LGREEN, radius=True)
    text(s, Inches(0.90), Inches(5.78), Inches(11.7), Inches(0.62),
         [("现在：", {'size': 11.5, 'color': GREEN, 'bold': True}),
          ("结论文件 / 稿件 §6 / 汇报 PPT 第 11 页，三方六条逐条一一对应，文件里原话写「现有不一致：无」。", {'size': 11.5, 'color': TXT}),
          ("\n11-10 顺带补了式 (2)(5)(6)(8) 的正文回引——此前这四个式子只在文中定义过，从没被引用。", {'size': 10.5, 'color': SUB})],
         spacing=1.45)
    footer(s, 16)


# ==================== P7 主线③ 理论下界 ====================
def p7():
    s = prs.slides.add_slide(BLANK)
    header(s, "③ 补理论：从「只说会高估」到「说出松多少」",
           "11-09 ｜ 附录 E 新增 E.1 基础下界，单边变双边")

    # 上：区间图（简易绘制）
    box(s, Inches(0.55), Inches(1.46), Inches(12.23), Inches(2.05), fill=WHITE, line=LINE, radius=True)
    text(s, Inches(0.80), Inches(1.58), Inches(3.0), Inches(0.28),
         "现在能画出的区间（对数刻度示意）", size=11.5, color=BLUE, bold=True)

    bars = [("沿槽", 1.364, 63.000, "1.364× ~ 63.00×", "可宽到 63 倍"),
            ("横槽", 1.267, 1.984, "1.267× ~ 1.984×", "最宽不到 2 倍")]
    import math
    x0 = Inches(2.05); wmax = Inches(6.6)
    ratios = [math.log10(63.0), math.log10(1.984)]
    for i, (lab, lo, hi, txt, note) in enumerate(bars):
        yy = Inches(1.98) + i * Inches(0.62)
        text(s, Inches(0.80), yy + Inches(0.02), Inches(1.1), Inches(0.3),
             lab, size=12, color=NAVY, bold=True)
        wlen = wmax * (math.log10(hi) / ratios[0])
        box(s, x0, yy, wlen, Inches(0.34), fill=PALE, radius=True)
        box(s, x0, yy, wmax * (math.log10(lo) / ratios[0]), Inches(0.34), fill=RED, radius=True)
        text(s, x0 + wmax + Inches(0.14), yy + Inches(0.03), Inches(3.1), Inches(0.3),
             [("{}".format(txt), {'size': 10.5, 'color': TXT, 'bold': True}),
              ("　" + note, {'size': 10, 'color': GRAY})])
    text(s, Inches(0.80), Inches(3.20), Inches(8.0), Inches(0.26),
         "红＝下界 h³/12 到实测值；浅蓝＝实测值到上界（原公式）。区间越宽＝这个界越不管用。",
         size=9.5, color=GRAY)

    # 左下：两个反向结论
    box(s, Inches(0.55), Inches(3.68), Inches(6.0), Inches(2.76), fill=LBLUE, radius=True)
    box(s, Inches(0.55), Inches(3.68), Inches(0.075), Inches(2.76), fill=BLUE)
    text(s, Inches(0.88), Inches(3.82), Inches(5.4), Inches(0.28),
         "两个「反而更清醒」的结论", size=12, color=BLUE, bold=True)
    text(s, Inches(0.88), Inches(4.18), Inches(5.45), Inches(2.14),
         [("① 横槽的界天生没用。", {'size': 11, 'bold': True, 'color': NAVY}),
          ("横槽区间最宽不到 2 倍（理论极限），沿槽能宽到 63 倍。", {'size': 10.5, 'color': SUB}),
          ("\n② 只写上界等于只报松的一端。", {'size': 11, 'bold': True, 'color': NAVY}),
          ("按相对偏差比，沿槽与横槽各有 11/18 个几何是下界更近。", {'size': 10.5, 'color': SUB})],
         spacing=1.55)

    # 右下：红线
    box(s, Inches(6.79), Inches(3.68), Inches(6.0), Inches(2.76), fill=LAMBER, radius=True)
    box(s, Inches(6.79), Inches(3.68), Inches(0.075), Inches(2.76), fill=AMBER)
    text(s, Inches(7.12), Inches(3.82), Inches(5.4), Inches(0.28),
         "写进稿里必须守住的四句", size=12, color=AMBER, bold=True)
    text(s, Inches(7.12), Inches(4.18), Inches(5.45), Inches(2.14),
         [("· 46 条记录在界内是「相容」，不是精度验收。", {}),
          ("· 下界不能当预测式，也不能当离散误差界。", {}),
          ("· 上界只对连续模型，不保证离散参考本身的误差。", {}),
          ("· d=0 退化为平板精确解，写「可退化」不写「只有 d=0 取等」。", {})],
         size=10.5, color=SUB, spacing=1.62)
    footer(s, 7)


# ==================== P8 主线④ 成对宽度 ====================
def p8():
    s = prs.slides.add_slide(BLANK)
    header(s, "④ 加硬证据：宽度变了会怎样",
           "11-10 ｜ 原来只有一组宽度，宽度依赖只能靠嘴说；现在有对照")

    # 上：核心数
    box(s, Inches(0.55), Inches(1.46), Inches(12.23), Inches(1.10), fill=LBLUE, radius=True)
    box(s, Inches(0.55), Inches(1.46), Inches(0.075), Inches(1.10), fill=BLUE)
    text(s, Inches(0.92), Inches(1.58), Inches(11.5), Inches(0.9),
         [("同一 h=75/d=120，把槽宽从 60 nm 换到 240 nm（周期 120 / 480 nm）：", {'size': 11.5, 'color': SUB}),
          ("\n原公式给出的各向异性比一模一样，A_LC = 4.90822，两个宽度完全相同到 16 位。", {'size': 14, 'color': NAVY, 'bold': True}),
          ("　原因很简单——式(3) 里根本没有 w。", {'size': 11, 'color': SUB})],
         spacing=1.42)

    # 左下：实测
    box(s, Inches(0.55), Inches(2.76), Inches(6.0), Inches(2.05), fill=WHITE, line=LINE, radius=True)
    text(s, Inches(0.85), Inches(2.90), Inches(5.4), Inches(0.28),
         "实测（2.5 nm 参考）：方向比被高估多少", size=11.5, color=BLUE, bold=True)
    for i, (lab, val, col) in enumerate([("窄槽 w=60", "208.85%", RED), ("宽槽 w=240", "33.58%", MBLUE)]):
        yy = Inches(3.24) + i * Inches(0.68)
        text(s, Inches(0.85), yy + Inches(0.04), Inches(1.6), Inches(0.3),
             lab, size=11.5, color=SUB, bold=True)
        text(s, Inches(2.55), yy - Inches(0.02), Inches(2.0), Inches(0.32),
             val, size=18, color=col, bold=True)
        text(s, Inches(2.55), yy + Inches(0.36), Inches(3.6), Inches(0.22),
             "（A_LC 相对实测 A 高估）", size=9.5, color=GRAY)

    # 右下：最硬的一条
    box(s, Inches(6.79), Inches(2.76), Inches(6.0), Inches(2.05), fill=LGREEN, radius=True)
    box(s, Inches(6.79), Inches(2.76), Inches(0.075), Inches(2.05), fill=GREEN)
    text(s, Inches(7.12), Inches(2.90), Inches(5.4), Inches(0.28),
         "补充材料里最硬的一条（51%）", size=11.5, color=GREEN, bold=True)
    text(s, Inches(7.12), Inches(3.22), Inches(5.45), Inches(1.5),
         [("就算允许每个几何自选最有利的共同倍率，", {'size': 10.5, 'color': SUB}),
          ("\n窄槽两方向的最大残差仍有 51.08%", {'size': 15, 'color': GREEN, 'bold': True}),
          ("（5 nm 下 51.31%）。", {'size': 10.5, 'color': SUB}),
          ("\n⇒ 整体幅值校准救不了方向比。这是「必须分方向」的直接证据。", {'size': 10.5, 'color': TXT})],
         spacing=1.42)

    # 底：梯度诊断 + 限定
    box(s, Inches(0.55), Inches(4.96), Inches(6.0), Inches(1.48), fill=WHITE, line=LINE, radius=True)
    text(s, Inches(0.85), Inches(5.08), Inches(5.4), Inches(0.26),
         "机制诊断（沿槽，2.5 nm）", size=11, color=BLUE, bold=True)
    text(s, Inches(0.85), Inches(5.40), Inches(5.45), Inches(0.92),
         [("跨槽梯度项 / 剖面偏离项占比：", {'size': 10.5, 'color': SUB}),
          ("\n窄槽 41.9% / 58.1%　→　宽槽 73.2% / 26.8%", {'size': 11, 'color': NAVY, 'bold': True})],
         spacing=1.4)

    box(s, Inches(6.79), Inches(4.96), Inches(6.0), Inches(1.48), fill=LAMBER, radius=True)
    text(s, Inches(7.12), Inches(5.08), Inches(5.4), Inches(0.26),
         "这组证据的边界", size=11, color=AMBER, bold=True)
    text(s, Inches(7.12), Inches(5.38), Inches(5.45), Inches(0.98),
         [("· 宽槽只有两档网格、窄槽有历史 FAIL ⇒ 不称网格独立。", {}),
          ("· 角点占比随半径变 ⇒ 不是尖角的独立贡献率。", {})],
         size=10, color=SUB, spacing=1.5)
    footer(s, 8)


# ==================== P9 主线⑤ 投稿件 ====================
def p9():
    s = prs.slides.add_slide(BLANK)
    header(s, "⑤ 出投稿件：把内部工作稿变成能投的稿",
           "11-10 ｜ 全文终审发现一个打包级风险，不是文字错误")

    # 左：发现的坑
    box(s, Inches(0.55), Inches(1.46), Inches(6.0), Inches(2.10), fill=LAMBER, radius=True)
    box(s, Inches(0.55), Inches(1.46), Inches(0.075), Inches(2.10), fill=AMBER)
    text(s, Inches(0.88), Inches(1.58), Inches(5.4), Inches(0.28),
         "审出来的坑：稿子后面还挂着 4 个内部附录", size=11.5, color=AMBER, bold=True)
    text(s, Inches(0.88), Inches(1.92), Inches(5.45), Inches(1.5),
         [("A 图件来源映射　B 数字可追溯性", {'size': 10.5, 'color': TXT}),
          ("\nC 投稿前待办清单　D 版本修订记录", {'size': 10.5, 'color': TXT}),
          ("\n最要命的是附录 A 把图 1—4 的图注整段重抄了一遍：", {'size': 10, 'color': SUB}),
          ("\n整份转 PDF 会出双份图注，还带本地路径和待办事项。", {'size': 10, 'color': SUB})],
         spacing=1.45)

    # 右：做法
    box(s, Inches(6.79), Inches(1.46), Inches(6.0), Inches(2.10), fill=WHITE, line=LINE, radius=True)
    text(s, Inches(7.12), Inches(1.58), Inches(5.4), Inches(0.28),
         "做法：加一层派生，母本仍是唯一入口", size=11.5, color=BLUE, bold=True)
    text(s, Inches(7.12), Inches(1.92), Inches(5.45), Inches(1.5),
         [("写 build_submission.py 做机械变换，只摘附录与内部注，不碰内容。", {'size': 10.5, 'color': TXT}),
          ("\n中文 725 → 653 行、英文 645 → 643 行，", {'size': 10.5, 'color': TXT}),
          ("零数字改动。", {'size': 10.5, 'color': GREEN, 'bold': True}),
          ("\n生成的稿子自动扫禁词与断链：0 命中、0 断链。", {'size': 10, 'color': SUB})],
         spacing=1.45)

    # 下：版本裁决 + 指纹
    box(s, Inches(0.55), Inches(3.76), Inches(6.0), Inches(2.62), fill=LBLUE, radius=True)
    box(s, Inches(0.55), Inches(3.76), Inches(0.075), Inches(2.62), fill=BLUE)
    text(s, Inches(0.88), Inches(3.90), Inches(5.4), Inches(0.28),
         "同时解决了「老是改错稿」", size=11.5, color=BLUE, bold=True)
    text(s, Inches(0.88), Inches(4.24), Inches(5.45), Inches(2.0),
         [("根因终于写清了：", {'size': 10.5, 'bold': True, 'color': NAVY}),
          ("\n文件名日期 ≠ 内容版本。中文稿名叫 20261022、英文叫 20261028，内容其实都是 11-10 的。", {'size': 10.5, 'color': SUB}),
          ("\n所以按「找带今天日期的文件名」永远找不到正文。", {'size': 10.5, 'color': SUB}),
          ("\n新建一份裁决文件：五件有效文件 + 三种最易改错的方式 + 作废清单 + 改稿固定顺序。", {'size': 10.5, 'color': TXT})],
         spacing=1.42)

    box(s, Inches(6.79), Inches(3.76), Inches(6.0), Inches(2.62), fill=WHITE, line=LINE, radius=True)
    text(s, Inches(7.12), Inches(3.90), Inches(5.4), Inches(0.28),
         "现在的指纹（现场核对）", size=11.5, color=BLUE, bold=True)
    rows = [("中文母稿", "5c35a498", "76099 B"),
            ("→ 中文投稿稿", "ef66ce61", "68172 B"),
            ("英文母稿", "fff9aff2", "83079 B"),
            ("→ 英文投稿稿", "7aecf220", "81866 B"),
            ("哈希清单", "18 条", "0 不一致")]
    for i, (nm, sha, byt) in enumerate(rows):
        yy = Inches(4.26) + i * Inches(0.34)
        text(s, Inches(7.12), yy, Inches(2.0), Inches(0.3), nm,
             size=10, color=SUB if i not in (1, 3) else NAVY,
             bold=(i in (1, 3)))
        text(s, Inches(9.20), yy, Inches(1.55), Inches(0.3), sha,
             size=9.5, color=TXT if i < 4 else GREEN, bold=True)
        text(s, Inches(10.85), yy, Inches(1.6), Inches(0.3), byt,
             size=9.5, color=GRAY)
    text(s, Inches(7.12), Inches(6.02), Inches(5.45), Inches(0.3),
         "python build_submission.py --check → 两行「一致」", size=9.5, color=GREEN)
    footer(s, 9)


# ==================== P10 数字一页 ====================
def p10():
    s = prs.slides.add_slide(BLANK)
    header(s, "这一周定下来的数字", "要背的话背这一页；每个数都能指到原始数据")

    cells = [
        ("46", "条比较记录", "36 主 + 8 加密 + 2 新增；分母仍 36", NAVY),
        ("36 / 36", "全部高估，无一例外", "沿槽 +10.30~+204.85%　横槽 +8.11~+54.19%", RED),
        ("2.21 → 3.70", "各向异性比", "基准 h=75/d=100；相对高估约 67%", MBLUE),
        ("9.20°", "45° 重建流向差", "只限该基准几何，非实测流向误差", MBLUE),
        ("35 / 36", "V2 改善条数", "MAE 88.85→6.40 / 30.63→4.42", GREEN),
        ("10.50% / 18.71%", "V2 最大绝对相对偏差", "沿槽 / 横槽；唯一恶化点在薄隙横槽", GREEN),
        ("63.00× / 1.984×", "上下界区间最宽处", "均出现在 h=25/d=100；0 条违反", AMBER),
        ("11 / 18", "下界比上界更近", "两方向各自独立都是 11/18", AMBER),
    ]
    w = Inches(2.88); gap = Inches(0.235); h = Inches(1.86)
    for i, (val, lab, note, col) in enumerate(cells):
        r, c = i // 4, i % 4
        l = Inches(0.55) + c * (w + gap)
        t = Inches(1.50) + r * (h + Inches(0.20))
        box(s, l, t, w, h, fill=WHITE, line=LINE, radius=True)
        box(s, l, t, w, Inches(0.045), fill=col)
        text(s, l + Inches(0.20), t + Inches(0.20), w - Inches(0.4), Inches(0.5),
             val, size=22 if len(val) < 9 else 18, color=col, bold=True)
        text(s, l + Inches(0.20), t + Inches(0.72), w - Inches(0.4), Inches(0.3),
             lab, size=10.5, color=NAVY, bold=True)
        text(s, l + Inches(0.20), t + Inches(1.06), w - Inches(0.4), Inches(0.66),
             note, size=9, color=GRAY, spacing=1.4)

    text(s, Inches(0.55), Inches(5.90), Inches(12.23), Inches(0.7),
         [("口径提醒：", {'size': 11, 'bold': True, 'color': AMBER}),
          ("偏差一律是「公式/参考−1」，参考是 5 nm 网格的 OpenLB 结果，不是真值；46 条是记录数，不是 46 次独立验证。", {'size': 11, 'color': SUB})])
    footer(s, 10)


# ==================== P11 问题与返工 ====================
def p11():
    s = prs.slides.add_slide(BLANK)
    header(s, "本周自身查出来并修掉的五类问题",
           "这一节讲返工，不讲成绩——返工才是这周真正花时间的地方")

    rows = [
        ("1", "改错稿版本（反复发生）",
         "文件名日期 ≠ 内容版本，按名字找永远找错",
         "建裁决文件，把「改哪份」从记忆变成查表", BLUE),
        ("2", "引用了不存在的文件",
         "MANIFEST 指向一个从未生成的 REPORT.md / verification.json",
         "改指向真实存在的四个文件，删掉对不存在的「检查」的指称", MBLUE),
        ("3", "同一数字三种精度",
         "18.7 / 18.7051 / 18.71 三种精度并存，88.8 与 88.85 也一样",
         "全稿统一两位小数，10.50 / 18.71 / 6.92 / 58.17 / 23.84", MBLUE),
        ("4", "说明文字里写会变的数字",
         "归档横幅写死「当前 18820 字节」，改完措辞立刻变 19004",
         "改为只写按构造不变的量：行数、哈希、比例", AMBER),
        ("5", "归属措辞说过头",
         "V2 原写「本研究建立」，但函数形式的直接前身一直没确认",
         "全稿收窄为「本研究标定」，零数字改动；补引 [1]", AMBER),
    ]
    y = Inches(1.50); rh = Inches(0.97)
    for i, (num, title, what, fix, col) in enumerate(rows):
        box(s, Inches(0.55), y, Inches(12.23), rh - Inches(0.09), fill=WHITE, line=LINE, radius=True)
        box(s, Inches(0.55), y, Inches(0.055), rh - Inches(0.09), fill=col)
        text(s, Inches(0.74), y + Inches(0.30), Inches(0.4), Inches(0.3),
             num, size=13, color=col, bold=True)
        text(s, Inches(1.18), y + Inches(0.11), Inches(3.4), Inches(0.3),
             title, size=11.5, color=NAVY, bold=True)
        text(s, Inches(1.18), y + Inches(0.42), Inches(4.9), Inches(0.3),
             what, size=9.5, color=SUB)
        text(s, Inches(6.30), y + Inches(0.11), Inches(0.42), Inches(0.3),
             "→", size=12, color=PALE, bold=True)
        text(s, Inches(6.78), y + Inches(0.30), Inches(5.85), Inches(0.4),
             fix, size=10, color=GREEN, spacing=1.35)
        y = y + rh

    text(s, Inches(0.55), Inches(6.35), Inches(12.23), Inches(0.55),
         [("共同点：", {'size': 11, 'bold': True, 'color': NAVY}),
          ("五次里有四次是「给了可验证的断言，但没先算」。所以这周起加了一条纪律——写进文件之前，先把要写进去的那个数算一遍。", {'size': 11, 'color': SUB})])
    footer(s, 11)


# ==================== P12 红线 ====================
def p12():
    s = prs.slides.add_slide(BLANK)
    header(s, "这周守住的六条口径红线",
           "每一条都对应一个曾经差点写错的坑")

    items = [
        ("46 条 ≠ 46 次验证", "统计分母永远是 36 条 5 nm 主结果。说「46 条」必须带组成（36＋8＋2）。"),
        ("V2 是回顾性评价", "标定集含于主比较集，扩展数据在选型时已可见 ⇒ 不构成独立预测精度证明。"),
        ("上界不给幅度", "附录 E 只给方向（必高估），不给出错多少，也不证明 V2 准。"),
        ("FAIL 不改写为 PASS", "S4（h=30/d=80）横槽加密差 1.328% > 1%，阶段仍是 FAIL。"),
        ("h=25 的网格口径", "是 h/Δx=5、壁面半格插值、完整节点 4 个；不得由此外推「误差约 42%」。"),
        ("h=100 不叫盲测", "稿里叫「新增间隙固定公式对照」，精度只限所用 5 nm 网格。"),
    ]
    w = Inches(6.0); h = Inches(1.58)
    for i, (head, body) in enumerate(items):
        r, c = i // 2, i % 2
        l = Inches(0.55) + c * Inches(6.24)
        t = Inches(1.50) + r * (h + Inches(0.16))
        box(s, l, t, w, h, fill=WHITE, line=LINE, radius=True)
        box(s, l, t, Inches(0.055), h, fill=RED if i in (0, 2, 3) else AMBER)
        text(s, l + Inches(0.26), t + Inches(0.18), w - Inches(0.5), Inches(0.32),
             head, size=13, color=NAVY, bold=True)
        text(s, l + Inches(0.26), t + Inches(0.62), w - Inches(0.52), Inches(0.86),
             body, size=10.5, color=SUB, spacing=1.42)
    footer(s, 15)


# ==================== P13 开放项 ====================
def p13():
    s = prs.slides.add_slide(BLANK)
    header(s, "还开着的口子：需要您拍板的四件事",
           "前三件只能由作者做；第四件是一句话的加固，等您点头")

    items = [
        ("A", "期刊定型", "要先定投哪里，后面的格式、字数、图件规格才定得下来。\n两个候选：MEE（微电子工程，周期短）／EJMB（流体，周期长）。",
         "决定后我做格式与压缩", RED),
        ("B", "作者侧信息", "作者与单位、基金、利益冲突、CRediT 贡献声明、AI 使用声明。\n这些内容我不能代填，也需要您确认口径。",
         "您提供，我落位", AMBER),
        ("C", "补充材料打包", "补充材料里有 25 处指向本地审计目录的相对链接，投稿前必须改掉；\n附录字母 E→A 也要四份文件同时改。",
         "打包时一并处理", AMBER),
        ("D", "两处一句话加固", "① §4.2 标题「全部 36 个样点」未点明是 5 nm；\n② §3.1 守恒/密度/Mach/边界诊断，缺一句「其通过不构成导度误差界」。",
         "改则需重跑派生件", BLUE),
    ]
    y = Inches(1.50)
    for i, (tagc, head, body, note, col) in enumerate(items):
        t = y + i * Inches(1.28)
        box(s, Inches(0.55), t, Inches(12.23), Inches(1.16), fill=WHITE, line=LINE, radius=True)
        box(s, Inches(0.55), t, Inches(0.055), Inches(1.16), fill=col)
        text(s, Inches(0.78), t + Inches(0.36), Inches(0.5), Inches(0.4),
             tagc, size=17, color=col, bold=True)
        text(s, Inches(1.36), t + Inches(0.13), Inches(2.4), Inches(0.3),
             head, size=12, color=NAVY, bold=True)
        text(s, Inches(1.36), t + Inches(0.44), Inches(8.3), Inches(0.68),
             body, size=9.5, color=SUB, spacing=1.4)
        text(s, Inches(9.95), t + Inches(0.42), Inches(2.6), Inches(0.4),
             note, size=9, color=col, bold=True, spacing=1.3)

    text(s, Inches(0.55), Inches(6.52), Inches(12.23), Inches(0.45),
         [("另有一条不是待办、是悬案：", {'size': 10.5, 'bold': True, 'color': AMBER}),
          ("V2 函数形式的直接前身仍未确认。30 份下载文献已查完，四系数确实由本研究标定，但「有没有沿用别人的函数形式」只能由您指认具体篇名段落。", {'size': 10.5, 'color': SUB})])
    footer(s, 13)


# ==================== P14 下周计划 + 交付物 ====================
def p14():
    s = prs.slides.add_slide(BLANK)
    header(s, "下周：把「能投」变成「投出去」", "按依赖顺序排，前两件卡在您这边")

    box(s, Inches(0.55), Inches(1.46), Inches(6.0), Inches(4.00), fill=LBLUE, radius=True)
    box(s, Inches(0.55), Inches(1.46), Inches(0.075), Inches(4.00), fill=BLUE)
    text(s, Inches(0.88), Inches(1.60), Inches(5.4), Inches(0.28),
         "四步", size=12, color=BLUE, bold=True)
    steps = [
        ("1", "按刊格式化", "图件分辨率与格式、参考文献风格、字数压缩（摘要按刊限）"),
        ("2", "补充材料打包", "25 处内部链接改写；附录 E→A 四份同改；图注去重"),
        ("3", "补齐声明项", "作者/基金/COI/CRediT/AI 使用；数据可用性最终措辞"),
        ("4", "两处加固 + 终校", "§4.2 标 5 nm、§3.1 补「不构成误差界」；三方一致性再核一遍"),
    ]
    for i, (n, head, body) in enumerate(steps):
        t = Inches(1.98) + i * Inches(0.86)
        text(s, Inches(0.90), t, Inches(0.35), Inches(0.3), n, size=13, color=BLUE, bold=True)
        text(s, Inches(1.28), t - Inches(0.02), Inches(2.0), Inches(0.3), head,
             size=11.5, color=NAVY, bold=True)
        text(s, Inches(3.30), t, Inches(3.05), Inches(0.6), body, size=9.5, color=SUB, spacing=1.38)

    box(s, Inches(6.79), Inches(1.46), Inches(6.0), Inches(4.00), fill=WHITE, line=LINE, radius=True)
    text(s, Inches(7.12), Inches(1.60), Inches(5.4), Inches(0.28),
         "本周新增或更新的交付物", size=12, color=BLUE, bold=True)
    files = [
        ("投稿派生件", "PAPER1_submission_manuscript_20261110/"),
        ("版本裁决文件", "PAPER1_CURRENT_FILES_AUTHORITY_20261110.md"),
        ("打包清单 MANIFEST", "PAPER1_submission_package_20261109/"),
        ("结论定稿（六条）", "PAPER1_conclusions_current_20261109.md"),
        ("成对宽度合稿", "PAPER1_width_evidence_merge_20261110/"),
        ("全文终审报告", "PAPER1_final_review_20261110/REVIEW.md"),
        ("来源核查报告", "PAPER1_V2_downloads_source_audit_20261110/"),
        ("归属措辞记录", "PAPER1_V2_attribution_wording_20261110/"),
        ("汇报 PPT（14 页）", "PPT_论文汇报_20261109/"),
    ]
    for i, (nm, path) in enumerate(files):
        t = Inches(1.96) + i * Inches(0.375)
        text(s, Inches(7.12), t, Inches(2.15), Inches(0.3), nm, size=9.5, color=NAVY, bold=True)
        text(s, Inches(9.35), t, Inches(3.3), Inches(0.3), path, size=8.5, color=GRAY)

    box(s, Inches(0.55), Inches(5.62), Inches(12.23), Inches(0.86), fill=LGREEN, radius=True)
    text(s, Inches(0.90), Inches(5.74), Inches(11.7), Inches(0.66),
         [("下一周的一句话目标：", {'size': 11.5, 'bold': True, 'color': GREEN}),
          ("投出去。科学内容这周已经封口——六条结论、上下界、成对宽度证据都已定稿并被哈希绑定；", {'size': 11.5, 'color': TXT}),
          ("\n剩下的是格式与声明，不需要新计算。", {'size': 11.5, 'color': TXT})],
         spacing=1.45)
    footer(s, 14)



# ==================== P5 别人怎么闭环 ====================
def p_lit1():
    s = prs.slides.add_slide(BLANK)
    header(s, "先讲一条贯穿全周的方法线：别人怎么闭环",
           "11-05 查文献（徐新鹏 + OpenLB）→ 11-06 核对 OpenLB 官方源码 → 本周逐条落进稿子")

    cards = [
        ("徐新鹏 2012 → 2013 ｜ PRE / JPCM", "换一个建模尺度去验",
         "连续模型提出「接触线附近蒸发/凝结改变接触角 → 液滴迁移」；同作者随后把分子动力学当作数值实验，检验「迁移朝低温方向、速度正比于温度梯度」，并检查尺寸与共存温度的影响。",
         "只说到「约 10 nm 液滴半定量一致」——不说完全一致，也不说连续模型普遍适用于纳米。", BLUE),
        ("徐新鹏 2014（共同作者）｜ Nature Physics", "改变条件，看边界在哪",
         "饼状弹跳：液滴不必回缩就以扁平形态离开表面 → 提出「压入柱间的毛细能转为向上动能」，并要求竖直回弹与横向铺展的时间尺度匹配 → 再改柱形、柱距与撞击条件，看何时出现、何时不出现。",
         "结论落在「出现 / 不出现的范围」和设计含义，不落在单点精度。", MBLUE),
        ("用 OpenLB 发论文的人 ｜ Bukreev 2025 / Czelusniak 2025", "先分块自证，再核接口",
         "Bukreev：子模块先分别对解析解，耦合再验一次，最后用自动微分灵敏度与有限差分做独立算法交叉。Czelusniak：先导出方法逼近的是哪个方程，再建基准族，最后报告收敛阶。",
         "共同结构：让每个部分先证明自己，再核接口，最后才展示能回答什么问题。", GREEN),
        ("OpenLB 官方源码 ｜ tests/benchmarks（1.9.0）", "看收敛阶，不设绝对门槛",
         "官方 Poiseuille 基准误差 0.0250 → 0.00673 → 0.00176（网格 11/21/41），相邻比 3.48–3.83，接近二阶的 4 倍律；回归容差是 errorFactor 1–2，不是 ≤1%。",
         "同一份官方数据还显示：bounceBack 粗网格误差 12.8–23.2%，插值类 1.1–5.7%。", AMBER),
    ]
    w = Inches(6.0); h = Inches(1.76)
    for i, (src, head, body, note, col) in enumerate(cards):
        r, c = i // 2, i % 2
        l = Inches(0.55) + c * Inches(6.24)
        t = Inches(1.44) + r * (h + Inches(0.14))
        box(s, l, t, w, h, fill=WHITE, line=LINE, radius=True)
        box(s, l, t, Inches(0.055), h, fill=col)
        text(s, l + Inches(0.24), t + Inches(0.09), w - Inches(0.45), Inches(0.22),
             src, size=8.5, color=GRAY, bold=True)
        text(s, l + Inches(0.24), t + Inches(0.33), w - Inches(0.45), Inches(0.26),
             head, size=12.5, color=NAVY, bold=True)
        text(s, l + Inches(0.24), t + Inches(0.66), w - Inches(0.46), Inches(0.72),
             body, size=8.8, color=SUB, spacing=1.32)
        text(s, l + Inches(0.24), t + Inches(1.40), w - Inches(0.46), Inches(0.30),
             note, size=8.5, color=col, spacing=1.28)

    box(s, Inches(0.55), Inches(5.26), Inches(12.23), Inches(1.40), fill=LBLUE, radius=True)
    box(s, Inches(0.55), Inches(5.26), Inches(0.075), Inches(1.40), fill=BLUE)
    text(s, Inches(0.92), Inches(5.38), Inches(11.4), Inches(0.26),
         "四篇看下来，闭环的做法其实是同一套骨架", size=11.5, color=BLUE, bold=True)
    steps = ["① 每一部分先单独证明自己", "② 再核接口",
             "③ 用另一种独立手段交叉", "④ 最后才说能回答什么，\n并明说不能回答什么"]
    for i, st in enumerate(steps):
        x = Inches(0.92) + i * Inches(2.82)
        text(s, x, Inches(5.72), Inches(2.70), Inches(0.78), st,
             size=9.5, color=NAVY, bold=True, spacing=1.34)
    footer(s, 5)


# ==================== P6 我怎么用 ====================
def p_lit2():
    s = prs.slides.add_slide(BLANK)
    header(s, "这周怎么用：把惯例逐条对到自己的稿子上",
           "不是「读了文献」，是「每一条都能指到稿里哪一节改了、改成什么」")

    rows = [
        ("解析解基准", "平板 h=75 nm 对 h³/12：0.444% → 0.111% → 0.0272%", "同构", "§3.2 表 3", BLUE),
        ("看收敛阶，不看绝对误差", "每加密一倍误差降约 1/4（官方相邻比 3.48–3.83）", "同构句已入稿，引 [7]", "§3.2", BLUE),
        ("边界格式选择有据", "官方对比四种格式、插值类优于 bounceBack ⇒ 选 Bouzidi + q=0.5", "补半句", "§2.1", MBLUE),
        ("独立算法交叉", "同一套系数进 OpenFOAM 独立实现（C01–C04 / GDI01）", "新增 §5.3 式(8)", "§5.3", GREEN),
        ("预测性检验", "h=100 新增间隙：预测先冻结、事后再比", "已入稿，不称盲测", "§4.4", GREEN),
        ("平台可信靠引用", "引 Krause 2021 [7]，自己只验特定几何", "已做", "§2.1", MBLUE),
        ("官方没有 ≤1% 硬门槛", "1% 只是内部停止条件，正文从未当验收指标", "口径写进稿", "§3.1", AMBER),
    ]
    y = Inches(1.44)
    text(s, Inches(0.72), y, Inches(2.6), Inches(0.24), "文献里的惯例", size=9.5, color=GRAY, bold=True)
    text(s, Inches(3.55), y, Inches(4.8), Inches(0.24), "本文的对应物", size=9.5, color=GRAY, bold=True)
    text(s, Inches(8.62), y, Inches(1.9), Inches(0.24), "本周落稿", size=9.5, color=GRAY, bold=True)
    text(s, Inches(11.10), y, Inches(1.6), Inches(0.24), "位置", size=9.5, color=GRAY, bold=True)
    y = Inches(1.72); rh = Inches(0.62)
    for i, (k, v, st, loc, col) in enumerate(rows):
        fill = WHITE if i % 2 == 0 else LBLUE2
        box(s, Inches(0.55), y, Inches(12.23), rh, fill=fill, line=LINE)
        box(s, Inches(0.55), y, Inches(0.045), rh, fill=col)
        text(s, Inches(0.74), y + Inches(0.17), Inches(2.55), Inches(0.32),
             k, size=10, color=NAVY, bold=True, spacing=1.28)
        text(s, Inches(3.55), y + Inches(0.17), Inches(4.85), Inches(0.32),
             v, size=9.2, color=TXT, spacing=1.28)
        text(s, Inches(8.62), y + Inches(0.17), Inches(2.3), Inches(0.32),
             st, size=9, color=col, bold=True, spacing=1.28)
        text(s, Inches(11.10), y + Inches(0.17), Inches(1.5), Inches(0.32),
             loc, size=9, color=GRAY)
        y = y + rh

    box(s, Inches(0.55), Inches(6.10), Inches(6.0), Inches(0.80), fill=LGREEN, radius=True)
    text(s, Inches(0.78), Inches(6.18), Inches(5.6), Inches(0.66),
         [("落稿的三处零计算改动：", {'size': 9.5, 'bold': True, 'color': GREEN}),
          ("\n① §3.2 同构句（引[7]）② §2.1 Bouzidi 依据 ③ 新增 §5.3 静态接入", {'size': 9.5, 'color': SUB})],
         spacing=1.3)
    box(s, Inches(6.79), Inches(6.10), Inches(6.0), Inches(0.80), fill=LAMBER, radius=True)
    text(s, Inches(7.02), Inches(6.18), Inches(5.6), Inches(0.66),
         [("有一条没照搬：", {'size': 9.5, 'bold': True, 'color': AMBER}),
          ("\n官方看速度场 L2 误差，我们看总积分导度 K ⇒ 只说「结构同构」，不说「误差可比」。", {'size': 9.5, 'color': SUB})],
         spacing=1.3)
    footer(s, 6)


# ==================== P12 全文闭环 ====================
def p_loop():
    s = prs.slides.add_slide(BLANK)
    header(s, "这一篇自己怎么闭环：八节按「上一节留下的问题」串起来",
           "把这条链讲顺，方法就能独立讲出来，不必依赖任何内部文件")

    box(s, Inches(0.55), Inches(1.42), Inches(12.23), Inches(0.66), fill=LBLUE, radius=True)
    text(s, Inches(0.85), Inches(1.52), Inches(11.7), Inches(0.5),
         [("一句话方法链：", {'size': 10, 'bold': True, 'color': BLUE}),
          ("几何 → K 与偏差 ε → 参照本身可不可信 → 双向偏差 → 有限修正 → 上下界", {'size': 12.5, 'bold': True, 'color': NAVY})])

    chain = [
        ("§1.1", "问题从哪来", "大面积压印无法逐槽解析 ⇒ 必须折算成等效系数 ⇒ 这个折算准吗", BLUE),
        ("§1.2", "与已有工作的边界", "有人在推系数、有人在用系数，但没人量化「用错了多少」⇒ 问题成立", BLUE),
        ("§2", "方法", "同一几何、同一驱动：显式沟槽算 K，与式(3) 比，偏差定义 ε=(K式/K参考−1)", MBLUE),
        ("§3", "先自证那把尺子", "解析基准 → 网格序列 → 四几何加密 → 已知限制；尺子不可信就不量", GREEN),
        ("§4", "结果", "36/36 高估 → 两方向不等幅 → 后果（A、9.20°）→ V2 改善 35/36 并保留两处修不动", GREEN),
        ("E / §5 / §6", "解释与收束", "上下界给方向、梯度诊断给结构、六条结论各自标明能说到哪一步", AMBER),
    ]
    y = Inches(2.20)
    for i, (sec, name, body, col) in enumerate(chain):
        box(s, Inches(0.55), y, Inches(7.50), Inches(0.68), fill=WHITE, line=LINE, radius=True)
        box(s, Inches(0.55), y, Inches(0.045), Inches(0.68), fill=col)
        text(s, Inches(0.72), y + Inches(0.20), Inches(0.95), Inches(0.28),
             sec, size=9.5, color=col, bold=True)
        text(s, Inches(1.66), y + Inches(0.07), Inches(1.85), Inches(0.26),
             name, size=9.5, color=NAVY, bold=True)
        text(s, Inches(1.66), y + Inches(0.33), Inches(6.2), Inches(0.3),
             body, size=8.5, color=SUB, spacing=1.2)
        y = y + Inches(0.72)

    right = [
        ("自证尺子", "§3 排在 §4 之前，顺序本身就是态度：先证明参考值可信，再用它判别人对错。", GREEN),
        ("独立交叉", "同一套系数进第二个实现，只支持「接口对」，不冒充「K 准」——这条界线稿里写死了。", MBLUE),
        ("保留失败", "1/36 未改善、S4 仍 FAIL、h=100 不称盲测——三条都留在稿里，不修饰。", AMBER),
    ]
    yy = Inches(2.20)
    for name, body, col in right:
        box(s, Inches(8.30), yy, Inches(4.48), Inches(1.32), fill=WHITE, line=LINE, radius=True)
        box(s, Inches(8.30), yy, Inches(4.48), Inches(0.045), fill=col)
        text(s, Inches(8.52), yy + Inches(0.14), Inches(4.05), Inches(0.26),
             name, size=11, color=col, bold=True)
        text(s, Inches(8.52), yy + Inches(0.44), Inches(4.06), Inches(0.82),
             body, size=8.8, color=SUB, spacing=1.32)
        yy = yy + Inches(1.44)

    text(s, Inches(0.55), Inches(6.58), Inches(12.23), Inches(0.26),
         "被问到「你怎么知道你的数是对的」→ 答 §3；「凭什么说公式错」→ 答 §4 与附录 E；「修正能用吗」→ 答 §4.4 与 §5.4。",
         size=9.5, color=GRAY)
    footer(s, 12)


for fn in (p1, p2, p3, p4, p_lit1, p_lit2, p5, p6, p7, p8, p9, p_loop,
           p10, p11, p12, p13, p14):
    fn()

assert len(prs.slides) == TOTAL, len(prs.slides)

# 页脚页码按实际幻灯片顺序统一重排：各页函数里的编号只作占位，
# 避免插页后硬编码编号与真实顺序错位。
# 只认「右下角页脚位置」的那个文本框（上沿 ≥7.0in、左沿 ≥11.0in），
# 不能按文本形状全盘匹配——那会误伤正文里的「36 / 36」这类数字。
for _i, _s in enumerate(prs.slides, 1):
    for _sh in _s.shapes:
        if not _sh.has_text_frame:
            continue
        if _sh.top is None or _sh.left is None:
            continue
        if _sh.top >= Inches(7.0) and _sh.left >= Inches(11.0):
            _p0 = _sh.text_frame.paragraphs[0]
            if _p0.runs:
                _p0.runs[0].text = f"{_i} / {TOTAL}"

out = os.path.join(HERE, "本周工作汇报.pptx")
prs.save(out)
print(f"已生成 {len(prs.slides)} 页 → {out}")
