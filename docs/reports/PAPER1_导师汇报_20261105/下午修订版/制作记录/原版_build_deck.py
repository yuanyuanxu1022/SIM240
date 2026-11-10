# -*- coding: utf-8 -*-
"""Build the advisor-report deck for PAPER1 (2026-11-05).

All numbers come from docs/reports/ evidence files:
  PAPER1_claim_evidence_matrix_20261104/REPORT.md
  URV_S1/S2/S3/S4 review reports
  OpenFOAM_comparison_clarification_20261104/REPORT.md
No new simulation, no new validation.
"""
import math, os, sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ---------------- palette (academic blue/white) ----------------
NAVY  = "0E3F8C"
BLUE  = "1E4FA8"
MID   = "3D7BD9"
LIGHT = "E8EFF8"
LIGHT2= "F0F5FC"
BG    = "FFFFFF"
PANEL = "F7F9FC"
TEXT  = "1A2230"
SUB   = "4A5568"
MUT   = "8B97A8"
LINE  = "D6DCE5"
RED   = "D9534F"
YELLOW= "FFC107"
LIKE_RED_BG = "FBECEC"
LIKE_GRN_BG = "EAF3EC"

FONT = "Microsoft YaHei"
W, H = 13.333, 7.5
TOTAL = 20
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "PAPER1_导师汇报_20261105.pptx")

prs = Presentation()
prs.slide_width  = Inches(W)
prs.slide_height = Inches(H)
BLANK = prs.slide_layouts[6]

_checks = []   # (page, label, need_h, have_h)

def c(h): return RGBColor.from_string(h)

def set_run(run, size, bold=False, color=TEXT, font=FONT, italic=False, sup=False, sub=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = c(color)
    run.font.name = font
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", font)
    if sup:
        rPr.set("baseline", "30000")
    elif sub:
        rPr.set("baseline", "-25000")

def parse_markup(text):
    """Split text into runs: {^...} -> superscript, {_...} -> subscript."""
    out, buf, i = [], "", 0
    while i < len(text):
        if text[i] == "{" and i + 2 < len(text) and text[i + 1] in "^_":
            if buf:
                out.append((buf, "n")); buf = ""
            close = text.find("}", i + 2)
            if close == -1:
                buf += text[i]; i += 1; continue
            out.append((text[i + 2:close], text[i + 1]))
            i = close + 1
        else:
            buf += text[i]; i += 1
    if buf:
        out.append((buf, "n"))
    return out


def rect(slide, x, y, w, h, fill=None, line=None, lw=0.75, rounded=0.0):
    shp = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h))
    shp.shadow.inherit = False
    if rounded:
        try: shp.adjustments[0] = rounded
        except Exception: pass
    if fill:
        shp.fill.solid(); shp.fill.fore_color.rgb = c(fill)
    else:
        shp.fill.background()
    if line:
        shp.line.color.rgb = c(line); shp.line.width = Pt(lw)
    else:
        shp.line.fill.background()
    shp.text_frame.word_wrap = True
    return shp

def hline(slide, x, y, w, color=LINE, lw=1.0):
    from pptx.enum.shapes import MSO_CONNECTOR
    ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y),
                                    Inches(x + w), Inches(y))
    ln.line.color.rgb = c(color)
    ln.line.width = Pt(lw)

def tb(slide, x, y, w, h, blocks, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
       page=None, label="", lm=0.05, rm=0.05, tm=0.02, bm=0.02):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left, tf.margin_right = Inches(lm), Inches(rm)
    tf.margin_top, tf.margin_bottom = Inches(tm), Inches(bm)
    tf.vertical_anchor = anchor
    first = True
    need = 0.0
    for b in blocks:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = b.get("align", align)
        ls = b.get("line", 1.28)
        p.line_spacing = ls
        p.space_before = Pt(b.get("space", 0))
        p.space_after = Pt(0)
        runs = b.get("runs")
        if runs is None:
            s_size = b.get("size", 14)
            s_bold = b.get("bold", False)
            s_col = b.get("color", TEXT)
            runs = [(t, s_size, s_bold, s_col, {"^": True} if k == "^" else
                     ({"_": True} if k == "_" else {}))
                    for (t, k) in parse_markup(b.get("text", ""))]
        em = 0.0
        max_size = 14
        for rr in runs:
            t, s, bold, col = rr[0], rr[1], rr[2], rr[3]
            kw = rr[4] if len(rr) > 4 else {}
            max_size = max(max_size, s)
            r = p.add_run(); r.text = t
            set_run(r, s if not (kw.get("^") or kw.get("_")) else s * 0.72,
                    bold, col, sup=kw.get("^", False), sub=kw.get("_", False))
            em += sum(1.0 if ord(ch) > 127 else 0.53 for ch in t) * (
                0.72 if (kw.get("^") or kw.get("_")) else 1.0)
        usable_pt = w * 72 - (lm + rm) * 72
        per_line = max(6.0, usable_pt / max_size)
        lines = max(1, math.ceil(em / per_line))
        need += (lines * max_size * ls + b.get("space", 0) + 1.0) / 72
    have = h - tm - bm
    if page:
        _checks.append((page, label or (blocks[0].get("text", "")[:14]), need, have))
    return box

def table(slide, x, y, w, data, col_w, fs=11, header_fs=None, row_h=0.42,
          aligns=None, header_fill=NAVY, zebra=True, first_col_bold=False,
          cell_styles=None):
    rows, cols = len(data), len(data[0])
    shp = slide.shapes.add_table(rows, cols, Inches(x), Inches(y),
                                 Inches(w), Inches(row_h * rows))
    tbl = shp.table
    # no built-in style: "No Style, No Grid"
    tblPr = tbl._tbl.tblPr
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is None:
        sid = tblPr.makeelement(qn("a:tableStyleId"), {})
        tblPr.append(sid)
    sid.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"
    tbl.first_row = False
    tbl.horz_banding = False
    tbl.vert_banding = False
    for i, cw in enumerate(col_w):
        tbl.columns[i].width = Inches(cw)
    for i in range(rows):
        tbl.rows[i].height = Inches(row_h)
    for ri, row in enumerate(data):
        for ci, val in enumerate(row):
            cell = tbl.cell(ri, ci)
            cell.margin_left = Inches(0.07); cell.margin_right = Inches(0.07)
            cell.margin_top = Inches(0.02);  cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if ri == 0:
                cell.fill.fore_color.rgb = c(header_fill)
            else:
                cell.fill.fore_color.rgb = c(PANEL if (zebra and ri % 2 == 0) else BG)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.line_spacing = 1.15
            al = PP_ALIGN.CENTER
            if aligns and ci < len(aligns):
                al = aligns[ci]
            p.alignment = al
            st = {}
            if cell_styles:
                st = cell_styles.get((ri, ci), {})
            base_size = st.get("size", header_fs if ri == 0 and header_fs else fs)
            base_bold = st.get("bold", ri == 0 or (first_col_bold and ci == 0))
            base_col = st.get("color", "FFFFFF" if ri == 0 else TEXT)
            for (t, k) in parse_markup(str(val)):
                r = p.add_run(); r.text = t
                set_run(r, base_size * (0.72 if k in "^_" else 1.0), base_bold, base_col,
                        sup=(k == "^"), sub=(k == "_"))
    return tbl

def base(slide, tag, title, page, footer, title_size=24, title_y=0.52, title_h=0.62):
    rect(slide, 0, 0, W, 0.14, NAVY)
    if tag:
        tb(slide, 0.45, 0.24, 9.5, 0.26,
           [{"text": tag, "size": 9.5, "color": MID, "line": 1.0}],
           page=page, label="tag")
    tb(slide, 0.45, title_y, 12.4, title_h,
       [{"text": title, "size": title_size, "bold": True, "color": NAVY, "line": 1.18}],
       page=page, label="title")
    hline(slide, 0.45, 1.20, 12.43, LINE, 1.0)
    hline(slide, 0.45, 6.94, 12.43, LINE, 0.75)
    tb(slide, 0.45, 7.00, 10.6, 0.28,
       [{"text": footer, "size": 8.5, "color": MUT, "line": 1.0}])
    tb(slide, 11.05, 7.00, 1.83, 0.28,
       [{"text": "%02d / %d" % (page, TOTAL), "size": 9, "color": BLUE, "line": 1.0}],
       align=PP_ALIGN.RIGHT)

def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text

def pic(slide, path, x, y, w):
    from PIL import Image
    iw, ih = Image.open(path).size
    h = w * ih / iw
    slide.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w))
    return h

def chip(slide, x, y, w, h, text, fill=LIGHT, color=BLUE, size=10.5, bold=True, radius=0.28):
    rect(slide, x, y, w, h, fill, None, rounded=radius)
    tb(slide, x, y + (h - 0.26) / 2, w, 0.26,
       [{"text": text, "size": size, "bold": bold, "color": color, "line": 1.0}],
       align=PP_ALIGN.CENTER)

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
F1 = os.path.join(A, "fig1_geometry.png")
F4 = os.path.join(A, "fig4_K_anisotropy.png")
F7 = os.path.join(A, "fig7_error_gap.png")
F8 = os.path.join(A, "fig8_error_map.png")

# =====================================================================
# 01 cover
# =====================================================================
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, W, 0.14, NAVY)
rect(s, 0, 0.14, 0.30, H - 0.14, LIGHT2)
rect(s, 0.62, 1.28, 0.055, 3.10, NAVY)
chip(s, 0.88, 1.22, 2.62, 0.34, "第一篇单相研究 · 导师汇报", LIGHT, BLUE, 10.5)
tb(s, 0.88, 1.72, 11.4, 0.80,
   [{"text": "纳米矩形沟槽的方向性输运", "size": 40, "bold": True, "color": NAVY, "line": 1.15}],
   page=1, label="cover title")
tb(s, 0.88, 2.62, 11.4, 0.52,
   [{"text": "局部立方律偏差、经验修正与验证进展", "size": 21, "color": MID, "line": 1.2}],
   page=1, label="cover sub")
hline(s, 0.88, 3.34, 3.6, LINE, 1.2)
tb(s, 0.88, 3.48, 11.4, 0.95,
   [{"text": "研究范围：固定间隙、完全充液、单相矩形沟槽", "size": 13, "color": SUB, "line": 1.5},
    {"text": "汇报日期：2026 年 11 月 5 日", "size": 13, "color": SUB, "line": 1.5}],
   page=1, label="cover info")

_data = [("18", "组几何 / 36 个方向点", "已采样、5 nm 离散参考"),
         ("5 组", "本周验证 S0—S4", "平壁·网格·驱动力·薄间隙"),
         ("1 项", "未通过的检查", "薄间隙横槽 1.328% > 1%")]
for i, (big, mid, small) in enumerate(_data):
    x = 0.88 + i * 3.95
    rect(s, x, 4.62, 3.62, 1.18, PANEL, LINE, 0.75, rounded=0.06)
    tb(s, x + 0.18, 4.74, 1.06, 0.50,
       [{"text": big, "size": 24, "bold": True, "color": NAVY, "line": 1.0}],
       page=1, label="chip big")
    tb(s, x + 1.28, 4.74, 2.24, 0.95,
       [{"text": mid, "size": 11.5, "bold": True, "color": TEXT, "line": 1.3},
        {"text": small, "size": 9.5, "color": SUB, "line": 1.3}],
       page=1, label="chip txt")
tb(s, 0.88, 6.55, 11.4, 0.30,
   [{"text": "代码、检查与材料整理有 AI 辅助；科学结论由作者核对并负责。", "size": 9.5, "color": MUT, "line": 1.0}],
   page=1, label="cover note")
notes(s, "老师好，我今天汇报第一篇单相研究的思路和阶段结果。研究对象是固定间隙、完全充液的矩形沟槽。"
         "我主要关注液体沿着沟槽流和横跨沟槽流时，阻力有什么不同，以及常用简化公式能不能准确描述这种差别。"
         "今天先讲已有发现，再讲最近补的验证和薄间隙遇到的问题，最后请您帮我定论文范围和补证重点。")

# =====================================================================
# 02 agenda
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "汇报路线", "今天讲五件事：已有什么、补了什么、卡在哪里、请您裁定", 2,
     "全篇约 9 分钟；附录 3 页供追问，不占讲述时间。")
_items = [("1", "研究什么", "固定间隙、完全充液的矩形沟槽；沿槽与横槽的流动阻力差异", "1 分钟"),
          ("2", "已有主要发现", "18 组几何 36 个方向点：方向性、原公式偏差、V2 改善与局部失效", "3 分钟"),
          ("3", "最近补的证据", "平壁解析基准、常规间隙网格与驱动力、OpenFOAM 接入核对", "2 分钟"),
          ("4", "最新卡点", "薄间隙横槽中—细网格差 1.328%，超过规定的 1%", "1 分钟"),
          ("5", "请您裁定", "论文主张范围；薄间隙补证是否继续投入", "1 分钟")]
for i, (num, t, d, tm) in enumerate(_items):
    y = 1.48 + i * 1.03
    rect(s, 0.45, y, 12.43, 0.92, PANEL if i % 2 == 0 else BG, LINE, 0.75, rounded=0.05)
    rect(s, 0.62, y + 0.19, 0.54, 0.54, NAVY, rounded=0.10)
    tb(s, 0.62, y + 0.27, 0.54, 0.40,
       [{"text": num, "size": 17, "bold": True, "color": "FFFFFF", "line": 1.0}],
       align=PP_ALIGN.CENTER, page=2, label="num")
    tb(s, 1.36, y + 0.14, 3.05, 0.66,
       [{"text": t, "size": 17, "bold": True, "color": NAVY, "line": 1.25}],
       page=2, label="agenda t")
    tb(s, 4.55, y + 0.12, 6.70, 0.70,
       [{"text": d, "size": 12.5, "color": SUB, "line": 1.35}],
       anchor=MSO_ANCHOR.MIDDLE, page=2, label="agenda d")
    chip(s, 11.42, y + 0.29, 1.10, 0.34, tm, LIGHT, BLUE, 10)
notes(s, "今天的时间安排是这样：先用一分钟交代研究对象，三分钟讲已有发现，两分钟讲最近补的验证，"
         "一分钟讲一个没有通过的检查，最后留一分钟请您定方向。后面三页是备查材料，我不主动讲。")

# =====================================================================
# 03 geometry
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "1 研究什么 · 几何与方向", "固定间隙、完全充液的矩形沟槽：比较两个方向的流动阻力", 3,
     "图源：本文图 1（器件与单胞示意、剖面与两个主方向）。")
hh = pic(s, F1, 0.45, 1.44, 6.55)
tb(s, 0.45, 1.44 + hh + 0.06, 6.55, 0.30,
   [{"text": "图 1　(a) 工艺示意　(b) 单胞剖面　(c) 沿槽 K∥ 与横槽 K⊥", "size": 9, "color": MUT, "line": 1.2}],
   page=3, label="fig1 cap")

rect(s, 7.28, 1.44, 5.60, 1.72, PANEL, LINE, 0.75, rounded=0.05)
tb(s, 7.48, 1.56, 5.20, 1.50,
   [{"text": "三个尺寸（示例 h=60、d=80、w=120、P=240 nm）", "size": 11, "bold": True, "color": BLUE, "line": 1.3},
    {"text": "h　凸台顶面到上壁面的间隙；槽内流体高度为 h+d", "size": 12, "color": TEXT, "line": 1.35, "space": 4},
    {"text": "d　槽深　　w　槽宽　　P　周期（240 nm）", "size": 12, "color": TEXT, "line": 1.35, "space": 2}],
   page=3, label="dims")

rect(s, 7.28, 3.28, 5.60, 1.28, PANEL, LINE, 0.75, rounded=0.05)
tb(s, 7.48, 3.40, 5.20, 1.06,
   [{"text": "两个方向", "size": 11, "bold": True, "color": BLUE, "line": 1.3},
    {"text": "沿槽＝y 方向（K∥）；横槽＝x 方向（K⊥）", "size": 12, "color": TEXT, "line": 1.35, "space": 4},
    {"text": "K 是薄膜导度，单位 m³：同样黏度下 K 越大，阻力越小", "size": 11.5, "color": SUB, "line": 1.35, "space": 2}],
   page=3, label="dirs")

rect(s, 7.28, 4.68, 5.60, 1.52, LIGHT, None, rounded=0.05)
tb(s, 7.48, 4.80, 5.20, 1.30,
   [{"text": "当前范围：只算固定间隙下的流动阻力", "size": 11.5, "bold": True, "color": NAVY, "line": 1.3},
    {"text": "动态下压、沟槽填充、困气属于后续扩展，本次不作结论。", "size": 11.5, "color": SUB, "line": 1.4, "space": 4}],
   page=3, label="scope")
notes(s, "h 是凸台顶面和上壁面之间的间隙，d 是槽深，所以槽里面的流体高度是 h 加 d。"
         "沟槽沿 y 方向延伸，沿槽流动是 y 方向，横槽流动是 x 方向。"
         "我用 K 表示薄膜导度，可以理解成液体有多容易流动，同样黏度下 K 越大阻力越小。"
         "今天只讲固定间隙下的流动阻力，下压、填充、困气都属于后面的事。")

# =====================================================================
# 04 comparison objects
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "1 研究什么 · 比较什么", "三个对象、一个误差定义：原公式、显式计算与经验修正", 4,
     "式 (3)(4) 见中文稿 §2.3；V2 系数为公布舍入值，见 §4.4。")

rect(s, 0.45, 1.44, 6.05, 2.05, PANEL, LINE, 0.75, rounded=0.05)
tb(s, 0.65, 1.54, 5.65, 1.85,
   [{"text": "① 待检验：原局部立方律", "size": 13, "bold": True, "color": NAVY, "line": 1.25},
    {"text": "K∥ = 1/24 · [ (h+d)³ + h³ ]", "size": 13.5, "bold": True, "color": TEXT, "line": 1.5, "space": 6},
    {"text": "K⊥ = 1/6 · (h+d)³h³ / [ (h+d)³ + h³ ]", "size": 13.5, "bold": True, "color": TEXT, "line": 1.5},
    {"text": "把深区、浅区各当作独立平行平板，再取算术/调和平均；未显式含侧壁与台阶附近的重分布。", "size": 10.5, "color": SUB, "line": 1.35, "space": 6}],
   page=4, label="obj1")

rect(s, 6.80, 1.44, 6.08, 2.05, PANEL, LINE, 0.75, rounded=0.05)
tb(s, 7.00, 1.54, 5.68, 1.85,
   [{"text": "② 比较基准：OpenLB 显式沟槽计算（5 nm 生产网格）", "size": 13, "bold": True, "color": NAVY, "line": 1.25},
    {"text": "不输入任何公式系数，直接解析沟槽几何求流量，再取 K = ν·J/a。", "size": 11, "color": TEXT, "line": 1.35, "space": 6},
    {"text": "它把侧壁与台阶一并算进去，因此可以检验简化公式差多少。", "size": 11, "color": TEXT, "line": 1.35, "space": 4},
    {"text": "代价：它自己也有离散误差，须单独做网格与驱动力检查。", "size": 10.5, "color": SUB, "line": 1.35, "space": 4}],
   page=4, label="obj2")

rect(s, 0.45, 3.64, 6.05, 2.05, BG, LINE, 0.75, rounded=0.05)
tb(s, 0.65, 3.74, 5.65, 1.85,
   [{"text": "③ 修正：V2 乘性因子（只依赖 d/w）", "size": 13, "bold": True, "color": NAVY, "line": 1.25},
    {"text": "F∥ = 1/[1+1.7685(d/w){^1.6331}]", "size": 13, "bold": True, "color": TEXT, "line": 1.5, "space": 6},
    {"text": "F⊥ = 1/[1+0.4900(d/w){^0.6990}]", "size": 13, "bold": True, "color": TEXT, "line": 1.5},
    {"text": "修正后导度 = F × 原公式导度；因子只含槽深与槽宽之比。", "size": 10.5, "color": SUB, "line": 1.35, "space": 5},
    {"text": "不含间隙 h，但残差仍随 h 变化 —— 这是它的结构局限。", "size": 10.5, "color": RED, "line": 1.35}],
   page=4, label="obj3")

rect(s, 6.80, 3.64, 6.08, 2.05, BG, LINE, 0.75, rounded=0.05)
tb(s, 7.00, 3.74, 5.68, 1.85,
   [{"text": "误差定义", "size": 13, "bold": True, "color": NAVY, "line": 1.25},
    {"text": "E = ( K模型 / K参考 − 1 ) × 100%", "size": 14, "bold": True, "color": TEXT, "line": 1.6, "space": 6},
    {"text": "正值＝高估导度，也就是低估阻力；负值反之。", "size": 11, "color": TEXT, "line": 1.4, "space": 4},
    {"text": "K参考 是同几何、同方向、同网格的离散数值解。", "size": 11, "color": TEXT, "line": 1.4},
    {"text": "换参考网格，E 本身就会变，所以每个偏差都要注明参考。", "size": 10.5, "color": SUB, "line": 1.35, "space": 4}],
   page=4, label="err")

rect(s, 0.45, 5.86, 12.43, 0.96, LIGHT, None, rounded=0.05)
rect(s, 0.45, 5.86, 0.06, 0.96, NAVY)
tb(s, 0.70, 5.94, 12.0, 0.80,
   [{"text": "全文报告的偏差都是「相对该数值参考」的偏差；这一口径决定了后面每一个数字能说到什么程度。",
     "size": 12, "bold": True, "color": NAVY, "line": 1.35}],
   anchor=MSO_ANCHOR.MIDDLE, page=4, label="key")
notes(s, "这里说明比较的三个对象。原局部立方律把深区和浅区分别当成平行平板再组合，所以它只是一个待检验的近似。"
         "数值参考是用 OpenLB 直接解析沟槽几何算出来的，不输入任何公式系数。"
         "V2 是在原公式上乘一个只依赖槽深和槽宽比值的修正因子。误差定义很简单，正值表示高估导度。")

# =====================================================================
# 05 sample map
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "2 已有发现 · 数据地图", "已有 18 组几何、36 个方向点（槽宽 120 nm、周期 240 nm 固定）", 5,
     "参数组合见中文稿表 1（§2.1）；方向点由同一几何两次驱动得到。")
table(s, 0.45, 1.48, 8.55,
      [["按间隙分组", "间隙 h", "已计算的槽深 d", "几何", "方向点"],
       ["薄间隙组", "25 nm", "25 / 50 / 100 nm", "3", "6"],
       ["50 nm 组", "50 nm", "25 / 50 / 75 / 100 / 120 nm", "5", "10"],
       ["75 nm 组", "75 nm", "25 / 50 / 75 / 100 / 120 nm", "5", "10"],
       ["125 nm 组", "125 nm", "25 / 50 / 75 / 100 / 120 nm", "5", "10"],
       ["合计", "—", "—", "18", "36"]],
      [1.55, 1.35, 3.55, 0.95, 1.15], fs=11.5, header_fs=11.5, row_h=0.50,
      aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER],
      first_col_bold=True,
      cell_styles={(5, 0): {"bold": True, "color": NAVY}, (5, 3): {"bold": True, "color": NAVY},
                   (5, 4): {"bold": True, "color": NAVY}})

tb(s, 0.45, 4.62, 8.55, 0.72,
   [{"text": "这不是完整的 4×5 矩阵：完整应为 20 种，h=25 nm 时未算 d=75、120 nm，实际 18 种；未采样格不插值、不填补。",
     "size": 10.5, "color": RED, "line": 1.4}],
   page=5, label="note1")

_stats = [("18", "几何组合", "已实际计算"), ("36", "方向样点", "沿槽 + 横槽"), ("5 nm", "生产网格", "比较的离散参考")]
for i, (big, mid, small) in enumerate(_stats):
    y = 1.48 + i * 1.24
    rect(s, 9.25, y, 3.63, 1.10, PANEL, LINE, 0.75, rounded=0.06)
    tb(s, 9.43, y + 0.16, 1.45, 0.55,
       [{"text": big, "size": 23, "bold": True, "color": NAVY, "line": 1.0}],
       page=5, label="stat big")
    tb(s, 10.80, y + 0.20, 1.95, 0.75,
       [{"text": mid, "size": 12, "bold": True, "color": TEXT, "line": 1.25},
        {"text": small, "size": 9.5, "color": SUB, "line": 1.25}],
       page=5, label="stat txt")

rect(s, 0.45, 5.52, 12.43, 1.02, LIGHT, None, rounded=0.05)
tb(s, 0.70, 5.62, 12.0, 0.82,
   [{"text": "计数的关键：18 是几何数，36 是方向点数。同一组几何分两次施加沿槽、横槽驱动，得到两个 K，不构成新的几何组。",
     "size": 12, "bold": True, "color": NAVY, "line": 1.35}],
   anchor=MSO_ANCHOR.MIDDLE, page=5, label="key5")
notes(s, "这 18 组是间隙和槽深的组合，槽宽和周期固定。每一组几何分别算沿槽和横槽两个方向，所以一共 36 个方向点。"
         "需要说明的是这不是完整的四乘五矩阵，最薄那一档没有算两个较深的槽，所以是 18 种而不是 20 种。")

# =====================================================================
# 06 directionality
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "2 已有发现 · 方向性", "加深沟槽对沿槽输运的提升，明显大于横槽", 6,
     "图源：本文图 2；5 nm 离散参考，18 组几何。")
hh = pic(s, F4, 0.45, 1.44, 8.95)
tb(s, 0.45, 1.44 + hh + 0.04, 8.95, 0.28,
   [{"text": "图 2　(a) 两个主方向的导度随槽深变化　(b) 各向异性 A = K∥/K⊥", "size": 9, "color": MUT, "line": 1.2}],
   page=6, label="fig4 cap")

rect(s, 9.65, 1.44, 3.23, 2.90, PANEL, LINE, 0.75, rounded=0.05)
tb(s, 9.82, 1.54, 2.90, 2.70,
   [{"text": "槽深 25→120 nm 的 K∥ 倍率", "size": 10.5, "bold": True, "color": BLUE, "line": 1.3},
    {"text": "h=50 nm　　3.55 倍", "size": 12, "color": TEXT, "line": 1.55, "space": 5},
    {"text": "h=75 nm　　2.13 倍", "size": 12, "color": TEXT, "line": 1.55},
    {"text": "h=125 nm　 1.39 倍", "size": 12, "color": TEXT, "line": 1.55},
    {"text": "同一范围内 K⊥ 变化 < 4%", "size": 11, "bold": True, "color": RED, "line": 1.4, "space": 8},
    {"text": "样本内 A 从约 1.1（h125/d25）到 15（h25/d100）", "size": 10.5, "color": SUB, "line": 1.4, "space": 3}],
   page=6, label="rates")

rect(s, 0.45, 5.62, 12.43, 0.92, BG, LINE, 0.75, rounded=0.05)
tb(s, 0.66, 5.70, 12.0, 0.76,
   [{"text": "限定：这是已采样条件下的观察（4 档间隙 × 5 档槽深中的 18 种），不能直接推广到所有几何或动态过程。",
     "size": 11.5, "color": SUB, "line": 1.35}],
   anchor=MSO_ANCHOR.MIDDLE, page=6, label="lim6")
notes(s, "第一项观察是，加深沟槽对两个方向的影响不同。沿着槽的方向，槽越深导度涨得越快，"
         "间隙 50 纳米这一档从 25 纳米槽深到 120 纳米涨了 3.5 倍；而横跨槽的方向几乎不变，四档间隙下变化都在 4% 以内。"
         "所以各向异性主要是槽深撑起来的。")

# =====================================================================
# 07 original law over-predicts
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "2 已有发现 · 原公式偏差", "原局部立方律在 36 个方向点上全部高估导度", 7,
     "图源：本文图 4；误差定义见式 (4)，参照为 5 nm 离散值。")
hh = pic(s, F8, 0.45, 1.40, 8.75)
tb(s, 0.45, 1.40 + hh + 0.03, 8.75, 0.28,
   [{"text": "图 3　偏差的 d–h 分布（左：沿槽；右：横槽）；斜线格为未采样几何", "size": 9, "color": MUT, "line": 1.2}],
   page=7, label="fig8 cap")

_stat7 = [("+10.30% → +204.85%", "沿槽 18 点", "最大点 h=50、d=120 nm"),
          ("+8.11% → +54.19%", "横槽 18 点", "最大点 h=125、d=120 nm"),
          ("36 / 36", "全部高估", "无一例外，即低估阻力")]
for i, (v, l, n) in enumerate(_stat7):
    y = 1.40 + i * 1.42
    rect(s, 9.42, y, 3.46, 1.28, PANEL, LINE, 0.75, rounded=0.05)
    tb(s, 9.56, y + 0.12, 3.20, 1.08,
       [{"text": v, "size": 15, "bold": True, "color": NAVY, "line": 1.15},
        {"text": l, "size": 10.5, "bold": True, "color": BLUE, "line": 1.2, "space": 3},
        {"text": n, "size": 9, "color": SUB, "line": 1.2}],
       page=7, label="stat7")

rect(s, 0.45, 5.42, 12.43, 1.04, LIGHT, None, rounded=0.05)
rect(s, 0.45, 5.42, 0.06, 1.04, NAVY)
tb(s, 0.72, 5.50, 11.95, 0.88,
   [{"text": "高估导度 = 低估阻力。沿槽最大点在 h=50、d=120 nm：模型值约为数值参考的 3.05 倍，偏差 204.85%。",
     "size": 12, "bold": True, "color": NAVY, "line": 1.35},
    {"text": "参考网格会改变偏差：4 个双网格几何换 2.5 nm 参考后变化 0.37—5.39 个百分点，横槽更敏感。",
     "size": 10, "color": SUB, "line": 1.3}],
   page=7, label="key7")
notes(s, "第二项观察更关键：36 个点上原公式全部高估导度，也就是全部低估阻力。"
         "沿槽偏差从 10% 一直到 205%，最大那一组模型值差不多是真值的三倍。"
         "这个参照是五纳米网格的计算值，本身有离散误差，所以我说的是相对这个参照的偏差，不是相对实验的精度。")

# =====================================================================
# 08 V2
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "2 已有发现 · 经验修正", "V2 把整体最坏偏差降下来，但不是每一点都改善", 8,
     "同一 36 点样本、相对 5 nm 参考的回顾性评价（中文稿表 8）。")
table(s, 0.45, 1.46, 8.30,
      [["最大绝对偏差", "原公式", "V2 修正", "变化"],
       ["沿槽 18 点", "204.85%", "10.5%", "降"],
       ["横槽 18 点", "54.19%", "18.7%", "降"],
       ["横槽 h≥50 nm，15 点", "—", "6.9%", "子集"]],
      [2.55, 2.00, 1.95, 1.80], fs=12, header_fs=11.5, row_h=0.56,
      aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER],
      first_col_bold=True,
      cell_styles={(1, 2): {"bold": True, "color": NAVY}, (2, 2): {"bold": True, "color": NAVY},
                   (3, 2): {"bold": True, "color": NAVY}})

rect(s, 0.45, 3.86, 8.30, 1.58, LIKE_RED_BG, RED, 1.0, rounded=0.05)
tb(s, 0.66, 3.96, 7.95, 1.38,
   [{"text": "反例：h=25 nm、d=100 nm 的横槽点", "size": 12, "bold": True, "color": RED, "line": 1.3},
    {"text": "5 nm 参考：绝对偏差 16.36% → 18.71%（变差）", "size": 11.5, "color": TEXT, "line": 1.4, "space": 4},
    {"text": "换 2.5 nm 参考：21.76% → 14.94%（变好）", "size": 11.5, "color": TEXT, "line": 1.4},
    {"text": "局部改善还是恶化，取决于用哪套参考网格。", "size": 10.5, "color": SUB, "line": 1.35}],
   page=8, label="counter")

rect(s, 0.45, 5.56, 8.30, 0.98, BG, LINE, 0.75, rounded=0.05)
tb(s, 0.66, 5.62, 7.95, 0.86,
   [{"text": "V2 的适用范围要写清：只覆盖 d/w 变化，不覆盖间隙的独立作用。", "size": 11, "bold": True, "color": NAVY, "line": 1.3}],
   anchor=MSO_ANCHOR.MIDDLE, page=8, label="limitv2")

rect(s, 8.95, 1.46, 3.93, 5.08, PANEL, LINE, 0.75, rounded=0.05)
tb(s, 9.12, 1.58, 3.60, 4.86,
   [{"text": "所以现在只能定位为", "size": 10.5, "bold": True, "color": BLUE, "line": 1.2},
    {"text": "回顾性经验修正", "size": 15, "bold": True, "color": NAVY, "line": 1.3, "space": 3},
    {"text": "· 扩展数据在模型选择时已可见；", "size": 10.5, "color": TEXT, "line": 1.4, "space": 8},
    {"text": "· 残差仍随间隙变化，V2 只含 d/w；", "size": 10.5, "color": TEXT, "line": 1.4, "space": 4},
    {"text": "· 9 个标定几何与 9 个扩展几何分属两组程序，无法分离构建差异；", "size": 10.5, "color": TEXT, "line": 1.4, "space": 4},
    {"text": "· 尚未证明对新条件的预测精度。", "size": 10.5, "color": TEXT, "line": 1.4, "space": 4},
    {"text": "要证明预测能力", "size": 10.5, "bold": True, "color": BLUE, "line": 1.3, "space": 10},
    {"text": "必须固定已公布系数，换一批未参与拟合、且自身检查合格的几何，再比一次。", "size": 10, "color": SUB, "line": 1.35, "space": 3}],
   page=8, label="position")
notes(s, "在原公式偏差之上，现在有 V2 修正。同一批数据，沿槽最大偏差从 205% 降到 10.5%，横槽从 54% 降到 18.7%。"
         "但并不是每一点都改善：最薄间隙那个横槽点，五纳米参考下反而从 16.36% 变成 18.71%。"
         "而且这批数据在选模型时我已经看到了，所以这是回顾性评价，不是预测精度。")

# =====================================================================
# 09 anisotropy / flow direction
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "2 已有发现 · 各向异性与流向", "偏差不只影响总量：它改变了各向异性与预测流向", 9,
     "基准几何 h=75、d=100 nm；中文稿表 7，式 (5)。")
table(s, 0.45, 1.46, 7.05,
      [["项（基准几何 h=75 / d=100 nm）", "显式数值", "局部立方律", "差异"],
       ["各向异性 A = K∥ / K⊥", "2.21", "3.70", "+67%"],
       ["45° 驱动下的流向角 β", "24.34°", "15.14°", "−9.20°"]],
      [3.45, 1.25, 1.25, 1.10], fs=12, header_fs=11, row_h=0.62,
      aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER],
      cell_styles={(1, 3): {"bold": True, "color": RED}, (2, 3): {"bold": True, "color": RED},
                   (1, 2): {"bold": True, "color": NAVY}, (2, 2): {"bold": True, "color": NAVY}})

rect(s, 0.45, 3.60, 7.05, 1.86, LIGHT, None, rounded=0.05)
tb(s, 0.65, 3.70, 6.72, 1.66,
   [{"text": "为什么只比总量会漏问题", "size": 11, "bold": True, "color": BLUE, "line": 1.25},
    {"text": "同一个驱动角下，总通量可能碰巧接近，但通量方向已经偏了 9.2°。", "size": 10.5, "color": TEXT, "line": 1.4, "space": 5},
    {"text": "对压印填充来说，方向偏意味着液体会往错的位置走 —— 分配比与填充顺序都会受影响。", "size": 10.5, "color": TEXT, "line": 1.4}],
   page=9, label="note9")

rect(s, 7.80, 1.46, 5.08, 2.66, PANEL, LINE, 0.75, rounded=0.05)
tb(s, 8.00, 1.58, 4.72, 2.44,
   [{"text": "线性张量关系", "size": 11, "bold": True, "color": BLUE, "line": 1.25},
    {"text": "tan β = ( K⊥ / K∥ ) · tan θ", "size": 15, "bold": True, "color": TEXT, "line": 1.7, "space": 6},
    {"text": "θ、β 均从槽轴量起；θ=45° 时两组主值重建的流向相差 9.20°。", "size": 10.5, "color": TEXT, "line": 1.4},
    {"text": "30°、45°、60° 斜向驱动只检查同一主值的内部自洽，不验证主值本身。", "size": 10, "color": SUB, "line": 1.35, "space": 4}],
   page=9, label="tensor")

rect(s, 7.80, 4.28, 5.08, 1.18, BG, LINE, 0.75, rounded=0.05)
tb(s, 8.00, 4.36, 4.72, 1.02,
   [{"text": "A = 2.21 对 3.70：模型把方向性夸大了约 67%", "size": 11, "bold": True, "color": NAVY, "line": 1.4}],
   anchor=MSO_ANCHOR.MIDDLE, page=9, label="key9b")

rect(s, 0.45, 5.66, 12.43, 0.88, BG, LINE, 0.75, rounded=0.05)
tb(s, 0.66, 5.74, 12.0, 0.72,
   [{"text": "限定：该角差来自同一张量的重建，不是实验测得的流向误差，不能推广为真实器件的流向精度。",
     "size": 11, "color": SUB, "line": 1.35}],
   anchor=MSO_ANCHOR.MIDDLE, page=9, label="lim9")
notes(s, "第三项观察是，偏差不只是总量上的。同一个几何，显式计算给的各向异性是 2.21，原公式给 3.70。"
         "在 45 度驱动下，按这两个比值反推流向，角度差 9 度多。也就是说即便总量碰巧接近，方向也会偏。"
         "这个角差是同一张量算出来的，不是实验值。")

# =====================================================================
# 10 weekly overview
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "3 本周补的证据 · 总览", "11 月 2—4 日：五组验证，四组通过，一组停在横槽网格", 10,
     "S0—S4 验收报告见各 URV_*_review 目录；均为已有结果复核，无新增长算。")
table(s, 0.45, 1.48, 8.72,
      [["组", "条件", "改的是什么", "结果"],
       ["S0 修复回归", "h75 / d100，两方向", "质量观察量修复前后", "通过"],
       ["S1 光滑平板", "h30，无槽", "去掉沟槽，对解析解", "通过"],
       ["S2 网格", "h60 / d80，两方向", "5 / 2.5 / 1.25 nm", "通过"],
       ["S3 驱动力", "h60 / d80，固定 2.5 nm", "5×10{^4} / 10{^5} / 2×10{^5} m/s²", "通过"],
       ["S4 薄间隙网格", "h30 / d80，两方向", "5 / 2.5 / 1.25 nm", "未通过"]],
      [1.85, 2.55, 3.10, 1.22], fs=11, header_fs=11, row_h=0.56,
      aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.CENTER],
      first_col_bold=True,
      cell_styles={(1, 3): {"bold": True, "color": BLUE}, (2, 3): {"bold": True, "color": BLUE},
                   (3, 3): {"bold": True, "color": BLUE}, (4, 3): {"bold": True, "color": BLUE},
                   (5, 3): {"bold": True, "color": RED}, (5, 0): {"bold": True, "color": RED}})

rect(s, 9.42, 1.48, 3.46, 4.10, PANEL, LINE, 0.75, rounded=0.05)
tb(s, 9.58, 1.58, 3.15, 3.92,
   [{"text": "同时完成的三件事", "size": 11, "bold": True, "color": BLUE, "line": 1.3},
    {"text": "① 0.625 nm 横槽补证的隔离准备", "size": 11, "bold": True, "color": TEXT, "line": 1.35, "space": 6},
    {"text": "15 项软件测试通过；尚无新流场结果，原 S4 失败保持。", "size": 10, "color": SUB, "line": 1.35},
    {"text": "② 结论—证据对照表", "size": 11, "bold": True, "color": TEXT, "line": 1.35, "space": 6},
    {"text": "把 C1—C4、T1、P1/P2、A1、I1 逐条绑定所需证据与缺口。", "size": 10, "color": SUB, "line": 1.35},
    {"text": "③ OpenFOAM 算例核对", "size": 11, "bold": True, "color": TEXT, "line": 1.35, "space": 6},
    {"text": "C01—C04 与 GDI01 是 10 月 30 日既有计算，本周只核对身份与证据边界。", "size": 10, "color": SUB, "line": 1.35},
    {"text": "本周有 0 次新增长算、0 次编译。", "size": 10, "bold": True, "color": RED, "line": 1.35, "space": 8}],
   page=10, label="side")

rect(s, 0.45, 4.90, 8.72, 0.98, BG, LINE, 0.75, rounded=0.05)
tb(s, 0.64, 4.97, 8.40, 0.84,
   [{"text": "这周实际改进了什么", "size": 10.5, "bold": True, "color": BLUE, "line": 1.2},
    {"text": "常规间隙 h60/d80：三套网格 + 三档驱动力都过；薄间隙 h30/d80：六条都有数，但网格门没过。", "size": 9.5, "color": TEXT, "line": 1.3, "space": 3}],
   page=10, label="gain")

rect(s, 0.45, 5.98, 12.43, 0.72, LIGHT, None, rounded=0.05)
tb(s, 0.66, 6.04, 12.0, 0.60,
   [{"text": "S3 的两条中档结果直接引用 S2 已有计算，不重复计为新增运行；S4 六条全部算完，但阶段判定仍为未通过。",
     "size": 10.5, "color": SUB, "line": 1.3}],
   anchor=MSO_ANCHOR.MIDDLE, page=10, label="note10")
notes(s, "这周主要推进的是数值验证。周一周二做完了修复版本的回归，和 30 纳米光滑平板的解析验证；"
         "周三完成常规间隙的三网格和驱动力检查，都通过了；周四薄间隙六条算完，但横槽网格没达标。"
         "另外把论文结论和证据对了一遍，也澄清了之前 OpenFOAM 那批算例能证明什么。")

# =====================================================================
# 11 S1 + S2
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "3 本周 · 基准与网格", "平板解析基准通过，常规间隙三网格也通过", 11,
     "S1：URV_S1_results_review_20261102；S2：URV_S2_completed_review_20261103_095422。")
rect(s, 0.45, 1.44, 4.55, 2.30, PANEL, LINE, 0.75, rounded=0.05)
tb(s, 0.62, 1.52, 4.22, 2.14,
   [{"text": "S1　光滑平板（h=30 nm，无槽）", "size": 11, "bold": True, "color": BLUE, "line": 1.25},
    {"text": "导度 K 相对误差　0.173%", "size": 13, "bold": True, "color": NAVY, "line": 1.5, "space": 6},
    {"text": "速度剖面 L2 误差　0.079%", "size": 13, "bold": True, "color": NAVY, "line": 1.5},
    {"text": "两方向均通过原定标准：程序在平板基准下算得准。", "size": 10, "color": SUB, "line": 1.35, "space": 5},
    {"text": "作用：排除「程序本身写错」这一层，否则后面沟槽的偏差说明不了公式问题。", "size": 10, "color": SUB, "line": 1.35}],
   page=11, label="s1")

rect(s, 0.45, 3.86, 4.55, 3.02, LIGHT, None, rounded=0.05)
tb(s, 0.62, 3.94, 4.22, 2.86,
   [{"text": "这组细网格告诉我们什么", "size": 11, "bold": True, "color": BLUE, "line": 1.25},
    {"text": "横槽阻力 ≈ 沿槽的 2.515 倍", "size": 14, "bold": True, "color": NAVY, "line": 1.4, "space": 6},
    {"text": "K∥ = 5.9073×10{^-23} m³", "size": 11.5, "color": TEXT, "line": 1.45, "space": 2},
    {"text": "K⊥ = 2.3489×10{^-23} m³", "size": 11.5, "color": TEXT, "line": 1.45},
    {"text": "求解过程不输入 V2 系数，因此它检验公式时是独立的。", "size": 10, "color": SUB, "line": 1.35, "space": 6},
    {"text": "候选参考 ≠ 合格参考", "size": 10.5, "bold": True, "color": RED, "line": 1.3, "space": 4},
    {"text": "还要过跨阶段资格审查，才能用来给 V2 打分。", "size": 10, "color": SUB, "line": 1.35}],
   page=11, label="s2key")

table(s, 5.25, 1.44, 7.63,
      [["网格 dx", "K∥ / 10{^-23} m³", "K⊥ / 10{^-23} m³"],
       ["5 nm", "5.9544", "2.4093"],
       ["2.5 nm", "5.9193", "2.3664"],
       ["1.25 nm", "5.9073", "2.3489"]],
      [2.20, 2.72, 2.71], fs=12, header_fs=11.5, row_h=0.66,
      aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER],
      cell_styles={(3, 1): {"bold": True, "color": NAVY}, (3, 2): {"bold": True, "color": NAVY}})

table(s, 5.25, 4.28, 7.63,
      [["检查项（门槛 1%）", "沿槽", "横槽"],
       ["中—细网格相对变化", "0.203%", "0.744%"],
       ["细网格 GCI 估计", "0.132%", "0.641%"],
       ["观测收敛阶 p", "1.55", "1.29"]],
      [3.23, 2.20, 2.20], fs=11.5, header_fs=11, row_h=0.56,
      aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER],
      cell_styles={(1, 1): {"bold": True, "color": BLUE}, (1, 2): {"bold": True, "color": BLUE}})
tb(s, 5.25, 6.52, 7.63, 0.34,
   [{"text": "六条合计 10.67 小时、无超时；修正质量误差 ≤1.3×10{^-14}，Mach ≈2×10{^-7}。", "size": 9, "color": MUT, "line": 1.2}],
   page=11, label="s2 foot")
notes(s, "先有一个基础校准：30 纳米光滑平板，去掉沟槽，和解析解比，导度误差 0.173%，速度剖面误差 0.079%。"
         "常规间隙这一组做了三套网格，两条方向都满足既定门槛，中细网格变化分别是 0.203% 和 0.744%。"
         "这组细网格给的比值是 2.515 倍，而且这个求解过程完全没有用 V2。")

# =====================================================================
# 12 S3
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "3 本周 · 驱动力控制", "驱动力放大 4 倍，导度几乎不变：支持线性输运", 12,
     "S3：URV_S3_completed_review_20261103_172033；两方向各三档，中档引用 S2。")
table(s, 0.45, 1.48, 7.55,
      [["加速度 a / m·s{^-2}", "K∥ / 10{^-23} m³", "K⊥ / 10{^-23} m³"],
       ["5×10{^4}", "5.91934", "2.36639"],
       ["1×10{^5}", "5.91934", "2.36639"],
       ["2×10{^5}", "5.91934", "2.36639"]],
      [2.55, 2.50, 2.50], fs=12, header_fs=11.5, row_h=0.62,
      aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER])

tb(s, 0.45, 4.06, 7.55, 0.62,
   [{"text": "通量 J 随驱动力按 4.0000003 倍增长，K 保持常数 → 该范围内是线性黏性响应。",
     "size": 11, "color": TEXT, "line": 1.35}],
   page=12, label="note12")

for i, (v, l, n) in enumerate([("8.30×10{^-8}", "沿槽 L（三档跨度）", "门槛 ≤ 1×10{^-3}，实测低约四个数量级"),
                               ("3.81×10{^-8}", "横槽 L（三档跨度）", "门槛 ≤ 1×10{^-3}，实测低约四个数量级")]):
    y = 1.48 + i * 1.54
    rect(s, 8.25, y, 4.63, 1.40, PANEL, LINE, 0.75, rounded=0.05)
    tb(s, 8.42, y + 0.16, 2.05, 0.50,
       [{"text": v, "size": 17, "bold": True, "color": NAVY, "line": 1.0}],
       page=12, label="L big")
    tb(s, 10.50, y + 0.20, 2.26, 1.00,
       [{"text": l, "size": 10.5, "bold": True, "color": BLUE, "line": 1.25},
        {"text": n, "size": 9, "color": SUB, "line": 1.25}],
       page=12, label="L txt")

rect(s, 8.25, 4.50, 4.63, 2.34, LIGHT, None, rounded=0.05)
tb(s, 8.42, 4.58, 4.30, 2.18,
   [{"text": "L 的定义", "size": 10.5, "bold": True, "color": BLUE, "line": 1.3},
    {"text": "L = ( max − min ) / mean，取三档末态 K。", "size": 10.5, "color": TEXT, "line": 1.4, "space": 5},
    {"text": "它是观测跨度，不是标准差、不是置信区间、也不是绝对准确度。", "size": 10, "color": SUB, "line": 1.35, "space": 5},
    {"text": "末窗时间稳态 std 约 1 ppm，比 L 大得多。", "size": 10, "color": SUB, "line": 1.35, "space": 5},
    {"text": "所以不能说「导度准到小数点后七八位」。", "size": 10, "bold": True, "color": RED, "line": 1.35}],
   page=12, label="Ldef")

rect(s, 0.45, 4.72, 7.55, 2.20, LIGHT, None, rounded=0.05)
tb(s, 0.65, 4.78, 7.22, 2.06,
   [{"text": "这组数字能说明什么、不能说明什么", "size": 11.5, "bold": True, "color": NAVY, "line": 1.25},
    {"text": "能：在该几何、该网格、三档驱动力范围内，未检出超过 0.1% 的驱动力依赖，J 随 a 严格按 4 倍增长。", "size": 10.5, "color": TEXT, "line": 1.38, "space": 5},
    {"text": "不能：它不证明导度本身准到多少 —— 中细网格差 0.203% / 0.744% 才是当前的分辨率上限，它比 L 大两个数量级。", "size": 10.5, "color": TEXT, "line": 1.38, "space": 5},
    {"text": "为什么还要做：若 K 随驱动力漂移，说明已有惯性或压缩性效应，线性假设不成立，后面所有比较都不成立。", "size": 10.2, "color": SUB, "line": 1.35}],
   page=12, label="interpret")
notes(s, "第二类证据是驱动力。同一个网格上把驱动力分成三档，放大四倍，导度几乎完全一样，"
         "两条方向的三档跨度都在 10 的负 7 次方量级，远小于 0.1% 的门槛。"
         "这说明这个范围内是线性黏性响应。但它只是观测跨度，不代表绝对准确度。")

# =====================================================================
# 13 S4 blocker
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "4 最新卡点", "薄间隙横槽网格未通过：1.328% 超过事先规定的 1%", 13,
     "S4：URV_S4_completed_review_20261104_143205；run_id URV_S4_{P,T}_dx{5,2p5,1p25}_reuse_v1。")
table(s, 0.45, 1.46, 7.30,
      [["方向", "dx", "K / m³", "单条检查"],
       ["沿槽", "5 nm", "2.7691×10{^-23}", "通过"],
       ["沿槽", "2.5 nm", "2.7546×10{^-23}", "通过"],
       ["沿槽", "1.25 nm", "2.7501×10{^-23}", "通过"],
       ["横槽", "5 nm", "3.6480×10{^-24}", "通过"],
       ["横槽", "2.5 nm", "3.5179×10{^-24}", "通过"],
       ["横槽", "1.25 nm", "3.4718×10{^-24}", "通过"]],
      [1.20, 1.30, 3.05, 1.75], fs=11, header_fs=11, row_h=0.47,
      aligns=[PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER],
      cell_styles={(4, 0): {"bold": True, "color": TEXT}, (5, 0): {"bold": True, "color": TEXT},
                   (6, 0): {"bold": True, "color": TEXT}})
tb(s, 0.45, 4.76, 7.30, 0.32,
   [{"text": "几何 h=30、d=80、w=120、P=240 nm；H=70 nm", "size": 9.5, "color": SUB, "line": 1.2}],
   page=13, label="s4 geo")

rect(s, 0.45, 5.10, 7.30, 1.54, PANEL, LINE, 0.75, rounded=0.05)
tb(s, 0.63, 5.18, 6.98, 1.40,
   [{"text": "六条各自的检查都合格，为什么整个阶段还不过？", "size": 10.5, "bold": True, "color": NAVY, "line": 1.25},
    {"text": "单条合格＝这条算例的数值/几何/稳态没问题；网格门＝换更细网格结果还会不会变。两者独立，前一通过推不出后一通过。",
     "size": 9.8, "color": TEXT, "line": 1.32, "space": 4},
    {"text": "处理：保留 FAIL、不改 1% 门槛、不重跑、不补写完成文件；也不能据此判 V2 失败。",
     "size": 9.8, "bold": True, "color": RED, "line": 1.32}],
   page=13, label="logic")

rect(s, 8.05, 1.46, 4.83, 1.72, LIKE_GRN_BG, "4F8A5B", 1.0, rounded=0.05)
tb(s, 8.24, 1.56, 4.48, 1.52,
   [{"text": "沿槽：通过", "size": 13, "bold": True, "color": "2F6B3C", "line": 1.25},
    {"text": "中—细变化 0.165%（门槛 1%）", "size": 11, "color": TEXT, "line": 1.4, "space": 4},
    {"text": "GCI 估计 0.094%，观测阶 1.67", "size": 11, "color": TEXT, "line": 1.4}],
   page=13, label="pass")

rect(s, 8.05, 3.26, 4.83, 3.58, LIKE_RED_BG, RED, 1.0, rounded=0.05)
tb(s, 8.24, 3.35, 4.48, 3.42,
   [{"text": "横槽：未通过", "size": 13, "bold": True, "color": RED, "line": 1.25},
    {"text": "中—细变化 1.328%（门槛 1%）", "size": 11, "bold": True, "color": RED, "line": 1.4, "space": 4},
    {"text": "GCI 估计 0.912% 合格，但不能抵补前一项", "size": 10.5, "color": TEXT, "line": 1.35},
    {"text": "超出门槛 0.328 个百分点 → S4 未通过，S5 未启动", "size": 10.5, "color": TEXT, "line": 1.35, "space": 4},
    {"text": "为什么不能算过", "size": 10.5, "bold": True, "color": RED, "line": 1.3, "space": 8},
    {"text": "1% 是事先冻结的门槛，看到结果后放宽会破坏可比性。", "size": 10, "color": TEXT, "line": 1.35},
    {"text": "原始 result.txt 的 RESULT_PASS=false 原样保留：独立接受由外部检查器写出。", "size": 9.5, "color": SUB, "line": 1.32, "space": 4},
    {"text": "六条运行合计 4.61 小时，无超时、无资源停止。", "size": 9.5, "color": SUB, "line": 1.32, "space": 3}],
   page=13, label="fail")

notes(s, "薄间隙这一组出现了一个具体卡点。间隙 30 纳米、槽深 80 纳米，六条计算全部算完，"
         "每一条单独的数值、几何、结果检查都通过，沿槽的网格检查也通过。"
         "但横槽中网格和细网格差 1.328%，超过事先规定的 1%，所以整个阶段没有通过。"
         "1% 是事先定的，不能看到结果再放宽。也不能说成只差一点可以忽略。")

# =====================================================================
# 14 1.25 nm server rerun result (NEW, 2026-11-05)
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "4 最新进展 · 11-04 深夜", "1.25 nm 服务器重跑完成：与本机逐位一致，构建等价成立", 14,
     "证据：URV_S4_TGE_1p25_结果复核_20261104/REPORT.md（独立复算 18 项全过）；服务器 10.103.102.55。")

tb(s, 0.45, 1.42, 12.4, 0.44,
   [{"text": "两台机器、两个编译版本，算出的 K 值逐位相同（相对差 = 0，判据门槛 ≤ 1×10{^-6}）",
     "size": 14.5, "bold": True, "color": SUB, "line": 1.2}], page=14, label="lead")

data = [
    ["项目", "数值", "说明"],
    ["服务器 K", "3.471791836744987×10{^-24} m³", "满额 12537 步，收敛"],
    ["本机参照 K（测量前冻结）", "3.471791836744987×10{^-24} m³", "同一物理量"],
    ["相对差", "0", "判据 ≤ 1×10{^-6}，实测为零"],
    ["质量守恒 / Mach", "4.4×10{^-15} / 6.3×10{^-9}", "极干净"],
    ["实测开销", "2 小时 6 分 · 峰值 1.6 GB · 1.65 步/秒", "给 0.625 决策的准数"],
]
table(s, 0.45, 1.96, 7.60, data, [2.90, 2.75, 1.95], fs=11, header_fs=11, row_h=0.50,
      aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER],
      cell_styles={(3, 1): {"bold": True, "color": "2F6B3C"}})

rect(s, 8.30, 1.96, 4.55, 1.50, LIKE_GRN_BG, None, rounded=0.05)
tb(s, 8.55, 2.10, 4.05, 0.36,
   [{"text": "构建等价：成立", "size": 14, "bold": True, "color": "2F6B3C", "line": 1.0}])
tb(s, 8.55, 2.50, 4.05, 0.85,
   [{"text": "换机器、换编译，答案不变", "size": 13.5, "bold": True, "color": TEXT, "line": 1.3},
    {"text": "服务器结果有资格配对本机原始点", "size": 12, "color": SUB, "line": 1.3, "space": 4}])

rect(s, 8.30, 3.66, 4.55, 1.55, LIKE_RED_BG, None, rounded=0.05)
tb(s, 8.55, 3.80, 4.05, 0.36,
   [{"text": "但不是 S4 通过", "size": 14, "bold": True, "color": RED, "line": 1.0}])
tb(s, 8.55, 4.20, 4.05, 0.95,
   [{"text": "横槽 1.328% > 1% 原样保留", "size": 13, "bold": True, "color": TEXT, "line": 1.3},
    {"text": "它回答「构建可不可信」，不回答「收敛没收敛」", "size": 11.5, "color": SUB, "line": 1.3, "space": 4}])

tb(s, 0.45, 5.50, 12.4, 1.25,
   [{"text": "这页回答了上一页留下的问题之一", "size": 12.5, "bold": True, "color": NAVY, "line": 1.3},
    {"text": "① 上一页说「1.25 nm 档是本机算的」——现在服务器独立重算，逐位复现，排除了「换机器答案就变」的疑虑。",
     "size": 11.5, "color": TEXT, "line": 1.4, "space": 5},
    {"text": "② 上一页说「0.625 只做到准备」——现在有了 1.25 的实测开销（1.6 GB / 2 小时），0.625 的内存也已实测约 10.7 GB，是否补跑只剩「导师要不要」这一个决定。",
     "size": 11.5, "color": TEXT, "line": 1.4, "space": 3}],
   page=14, label="bridge")

notes(s, "这是 11 月 4 日深夜的新进展。把最细那档 1.25 纳米放到实验室服务器上独立重算，"
         "K 值和本机逐位一致，相对差是零——判据只要求百万分之一以内。"
         "数值质量、质量守恒、几何审计全部干净，两小时六分跑完，峰值内存 1.6 GB。"
         "要说清楚：这只证明「换机器算得一样」，不等于 S4 通过，横槽 1.328% 的失败保留。"
         "它的作用是给 0.625 补证扫清了前提，开销也有了准数。")

# =====================================================================
# 15 next step boundary
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "3 / 4 边界", "补证只做到「准备」，OpenFOAM 只证明「接入」", 15,
     "URV_S4_TGE_preparation_20261104_152009；OpenFOAM_comparison_clarification_20261104。")

rect(s, 0.45, 1.44, 6.05, 2.96, PANEL, LINE, 0.75, rounded=0.05)
tb(s, 0.65, 1.52, 5.65, 2.80,
   [{"text": "0.625 nm 横槽单条补证", "size": 12.5, "bold": True, "color": NAVY, "line": 1.25},
    {"text": "已准备（不等于已计算）", "size": 10.5, "bold": True, "color": BLUE, "line": 1.3, "space": 7},
    {"text": "· 输入文件与旧基准引用　· 同一可执行文件来源核对", "size": 10.5, "color": TEXT, "line": 1.4},
    {"text": "· 零步入口与资源审查材料　· 15 项软件测试全部通过", "size": 10.5, "color": TEXT, "line": 1.4},
    {"text": "为什么先做这一步", "size": 10.5, "bold": True, "color": BLUE, "line": 1.3, "space": 8},
    {"text": "先确认程序就是当初那一支、输入没被改过，再去花机时。", "size": 10, "color": SUB, "line": 1.35},
    {"text": "尚未做", "size": 10.5, "bold": True, "color": RED, "line": 1.3, "space": 8},
    {"text": "原生初始化审计、性能标定、正式流场计算。没有任何 0.625 nm 新流场结果，原 S4 失败保持。", "size": 10, "color": TEXT, "line": 1.35}],
   anchor=MSO_ANCHOR.MIDDLE, page=14, label="prep")

rect(s, 6.80, 1.44, 6.08, 2.96, PANEL, LINE, 0.75, rounded=0.05)
tb(s, 7.00, 1.52, 5.68, 2.80,
   [{"text": "OpenFOAM 等效阻力接入", "size": 12.5, "bold": True, "color": NAVY, "line": 1.25},
    {"text": "h=75 / d=100 nm；24×48 μm 合成平均域、512 单元、不逐槽解析", "size": 9.8, "color": SUB, "line": 1.35, "space": 6},
    {"text": "V2 相对原公式的出口流量：横槽 −30.14%，沿槽 −56.77%", "size": 10.5, "bold": True, "color": TEXT, "line": 1.4, "space": 5},
    {"text": "它证明了什么", "size": 10.5, "bold": True, "color": BLUE, "line": 1.3, "space": 7},
    {"text": "方向性阻力能按既定定义接入平均模型，静态接口一致（含 GDI01）。", "size": 10, "color": TEXT, "line": 1.35},
    {"text": "它没证明什么", "size": 10.5, "bold": True, "color": RED, "line": 1.3, "space": 7},
    {"text": "V2 是否准确；挤压压力与载荷；动态填充精度。", "size": 10, "color": TEXT, "line": 1.35}],
   anchor=MSO_ANCHOR.MIDDLE, page=14, label="of")

rect(s, 0.45, 4.54, 12.43, 2.24, LIGHT, None, rounded=0.05)
rect(s, 0.45, 4.54, 0.06, 2.24, NAVY)
tb(s, 0.72, 4.63, 11.95, 2.06,
   [{"text": "本页只回答一个问题：哪些是「已经做了」，哪些还只是「准备好了」", "size": 12, "bold": True, "color": NAVY, "line": 1.3},
    {"text": "① 已做完　S0—S4 的六组结果与逐条复核（S4 结论为未通过）。", "size": 10.5, "color": TEXT, "line": 1.4, "space": 6},
    {"text": "② 只准备　0.625 nm 横槽的输入、来源与测试 —— 还没算，所以不能拿来当证据。", "size": 10.5, "color": TEXT, "line": 1.4, "space": 3},
    {"text": "③ 只能说明接口　OpenFOAM 那批算例（10 月 30 日），不是公式准确性证据。", "size": 10.5, "color": TEXT, "line": 1.4, "space": 3},
    {"text": "④ 不能互比　左边 h30/d80、右边 h75/d100，几何与平均厚度都不同，两页数值不能当同条件误差比较。", "size": 10.5, "color": TEXT, "line": 1.4, "space": 3},
    {"text": "为什么要把这条写进汇报：老师最容易把「已经算了」和「准备算了」听成同一件事。", "size": 9.8, "color": SUB, "line": 1.35, "space": 8}],
   anchor=MSO_ANCHOR.MIDDLE, page=14, label="key14")

notes(s, "下一步的补证，目前只做到准备：输入、旧基准引用、同一程序来源、零步入口和资源材料都备好了，"
         "15 项软件测试也过了，但原生审计、性能标定和正式计算都还没做，所以现在没有任何新流场结果。"
         "OpenFOAM 那部分，是把方向性阻力接进平均模型，证明的是接口一致，不是 V2 准不准。")

# =====================================================================
# 15 evidence boundary
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "5 边界", "现在能说什么、不能说什么：一句话分清", 16,
     "对照表：PAPER1_claim_evidence_matrix_20261104/REPORT.md（C1—C4、T1、P1/P2、A1、I1）。")

rect(s, 0.45, 1.44, 6.05, 2.72, PANEL, LINE, 0.75, rounded=0.05)
tb(s, 0.62, 1.53, 5.72, 2.56,
   [{"text": "可以保留（有证据、有边界）", "size": 12, "bold": True, "color": BLUE, "line": 1.25},
    {"text": "C1　已采样条件下，槽深对两个方向影响不同", "size": 10.5, "color": TEXT, "line": 1.35, "space": 7},
    {"text": "C2　36 个方向点上原公式全部高估导度", "size": 10.5, "color": TEXT, "line": 1.35, "space": 4},
    {"text": "C3　偏差改变各向异性与重建流向", "size": 10.5, "color": TEXT, "line": 1.35, "space": 4},
    {"text": "C4　V2 降低整体最坏偏差，但局部失效", "size": 10.5, "color": TEXT, "line": 1.35, "space": 4},
    {"text": "T1　理想 Stokes 假设下原公式给非严格上界", "size": 10.5, "color": TEXT, "line": 1.35, "space": 4},
    {"text": "共同前提：5 nm 离散参考、回顾性口径、已采样范围。", "size": 9.8, "color": SUB, "line": 1.35, "space": 6}],
   anchor=MSO_ANCHOR.MIDDLE, page=15, label="can")

rect(s, 6.80, 1.44, 6.08, 2.72, LIKE_RED_BG, "E6C4C2", 0.75, rounded=0.05)
tb(s, 6.97, 1.53, 5.75, 2.56,
   [{"text": "不能声称（尚无合格证据）", "size": 12, "bold": True, "color": RED, "line": 1.25},
    {"text": "P1　固定 V2 对未参与拟合条件有预测能力", "size": 10.5, "color": TEXT, "line": 1.35, "space": 7},
    {"text": "P2　V2 在薄间隙同样可靠", "size": 10.5, "color": TEXT, "line": 1.35, "space": 4},
    {"text": "A1　提高真实压印压力 / 载荷 / 时间，或单一耗散机制", "size": 10.5, "color": TEXT, "line": 1.35, "space": 4},
    {"text": "任何实验或物理验证（全文只做数值验证）", "size": 10.5, "color": TEXT, "line": 1.35, "space": 4},
    {"text": "投稿就绪、严格误差界", "size": 10.5, "color": TEXT, "line": 1.35, "space": 4},
    {"text": "共同原因：缺合格参考、缺独立条件、缺人工终审。", "size": 9.8, "color": SUB, "line": 1.35, "space": 6}],
   anchor=MSO_ANCHOR.MIDDLE, page=15, label="cannot")

rect(s, 0.45, 4.22, 12.43, 1.48, BG, LINE, 0.75, rounded=0.05)
tb(s, 0.66, 4.32, 12.0, 1.30,
   [{"text": "左右两栏的分界不是「保守 / 激进」，而是「有没有对应的合格证据」。", "size": 11.5, "bold": True, "color": NAVY, "line": 1.3},
    {"text": "左边每一条都写清了后缀：相对 5 nm 参考、已采样条件、回顾性评价。去掉后缀，它们立刻变成右边。", "size": 10.2, "color": TEXT, "line": 1.38, "space": 5},
    {"text": "右边每一条都缺一个具体东西：合格的新条件参考、独立的挤压/实验参照、或人工科学终审。", "size": 10.2, "color": TEXT, "line": 1.38, "space": 3},
    {"text": "这也是明天最需要请您把关的地方：哪一条值得先补。", "size": 10.2, "bold": True, "color": SUB, "line": 1.35, "space": 4}],
   anchor=MSO_ANCHOR.MIDDLE, page=15, label="mid15")

rect(s, 0.45, 5.84, 12.43, 0.78, NAVY, None, rounded=0.05)
tb(s, 0.68, 5.92, 12.0, 0.62,
   [{"text": "reference_qualified = false　·　MODEL_COMPARISON = NOT_EVALUATED　·　physical_validation = NOT_EVALUATED　·　submission_ready = false",
     "size": 9.8, "bold": True, "color": "FFFFFF", "line": 1.35}],
   anchor=MSO_ANCHOR.MIDDLE, page=15, label="flags")
notes(s, "这张表是我自己划的边界。左边四条结论有证据，但都带条件：已采样、五纳米参考、回顾性。"
         "右边这些现在不能说：V2 对新条件有没有预测能力、挤压压力载荷、任何实验验证。"
         "底下的状态标记是项目里冻结的，不是我今天临时定的。")

# =====================================================================
# 16 questions
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "5 请您裁定", "两个问题：论文主张放到多大，薄间隙还投多少", 17,
     "两个问题均为方向性裁定，不涉及本轮新增计算。")

rect(s, 0.45, 1.42, 12.43, 0.86, LIGHT, None, rounded=0.05)
tb(s, 0.68, 1.49, 12.0, 0.72,
   [{"text": "已有主线（无论选哪条路都成立）：已采样条件下的原公式偏差、方向性后果、V2 回顾性改善与局部失效。",
     "size": 11.5, "bold": True, "color": NAVY, "line": 1.3}],
   anchor=MSO_ANCHOR.MIDDLE, page=16, label="main")

rect(s, 0.45, 2.44, 6.05, 3.10, PANEL, LINE, 0.75, rounded=0.05)
tb(s, 0.62, 2.60, 5.72, 2.86,
   [{"text": "问题 1", "size": 10, "bold": True, "color": BLUE, "line": 1.2},
    {"text": "论文主张放在哪里？", "size": 14, "bold": True, "color": NAVY, "line": 1.25, "space": 3},
    {"text": "A　围绕「已采样样本中的偏差、方向性后果、有边界的经验修正」组织", "size": 10.5, "bold": True, "color": BLUE, "line": 1.35, "space": 7},
    {"text": "现有素材基本够，但必须保留全部限定；不能写新条件预测。", "size": 9.8, "color": SUB, "line": 1.35},
    {"text": "B　把「对新条件的独立预测」作为主要贡献", "size": 10.5, "bold": True, "color": RED, "line": 1.35, "space": 7},
    {"text": "先补齐薄间隙参考、跨阶段参考资格、固定 V2 的正式比较，才写得了。", "size": 9.8, "color": SUB, "line": 1.35},
    {"text": "两条路的补证量与投稿时间差别很大，需要您定。", "size": 9.8, "color": TEXT, "line": 1.35, "space": 5}],
   page=16, label="q1")

rect(s, 6.80, 2.44, 6.08, 3.10, PANEL, LINE, 0.75, rounded=0.05)
tb(s, 6.97, 2.60, 5.75, 2.86,
   [{"text": "问题 2", "size": 10, "bold": True, "color": BLUE, "line": 1.2},
    {"text": "薄间隙横槽还要不要继续投？", "size": 14, "bold": True, "color": NAVY, "line": 1.25, "space": 3},
    {"text": "继续　先定补证方案与资源，再授权计算", "size": 10.5, "bold": True, "color": BLUE, "line": 1.35, "space": 7},
    {"text": "0.625 nm 已在准备状态；正式算需另批机时。", "size": 9.8, "color": SUB, "line": 1.35},
    {"text": "收窄　论文明确不覆盖最薄间隙", "size": 10.5, "bold": True, "color": BLUE, "line": 1.35, "space": 7},
    {"text": "把 1.328% 与原因未定的边界写进限制章节。", "size": 9.8, "color": SUB, "line": 1.35},
    {"text": "两条路都不改已冻结门槛，也不删历史 FAIL。", "size": 9.8, "color": TEXT, "line": 1.35, "space": 5}],
   page=16, label="q2")

rect(s, 0.45, 5.68, 12.43, 1.14, BG, LINE, 0.75, rounded=0.05)
rect(s, 0.45, 5.68, 0.06, 1.14, NAVY)
tb(s, 0.72, 5.76, 11.95, 0.98,
   [{"text": "我的建议：先把「局部输运」这条主线讲完整；挤压压力、载荷与完整压印过程作为应用方向讨论，但不作为已实现成果。",
     "size": 10.8, "bold": True, "color": NAVY, "line": 1.35},
    {"text": "关于 AI 参与：代码、检查与材料整理有 AI 辅助；我会区分本人已理解核对的部分，与仍需学习、人工复核的部分。", "size": 10, "color": SUB, "line": 1.35, "space": 4}],
   anchor=MSO_ANCHOR.MIDDLE, page=16, label="advice")
notes(s, "我想请您定两件事。第一，论文是围绕已有样本里的偏差和方向性后果来组织，还是必须把对新条件的独立预测当成主要贡献？"
         "这两条路需要的补证量差很多。第二，薄间隙这个横槽网格没过，值不值得继续投入？如果继续，我先把方案和资源算清楚再申请。")

# =====================================================================
# 17 appendix: Fig7
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "附录 A", "备查：偏差随间隙的变化（按槽深分组）", 18,
     "图源：本文图 3；纵轴为对数，两面板范围不同。")
hh = pic(s, F7, 0.45, 1.40, 7.40)
tb(s, 0.45, 1.40 + hh + 0.02, 7.40, 0.32,
   [{"text": "图 A1　沿槽（a）与横槽（b）的相对偏差随间隙变化", "size": 9, "color": MUT, "line": 1.2}],
   page=17, label="fig7 cap")
rect(s, 0.45, 4.92, 7.40, 1.56, LIGHT, None, rounded=0.05)
rect(s, 0.45, 4.92, 0.06, 1.56, NAVY)
tb(s, 0.66, 4.98, 7.08, 1.44,
   [{"text": "读图三点", "size": 10.5, "bold": True, "color": NAVY, "line": 1.2},
    {"text": "① 纵轴取对数，「看着差不多高」其实是成倍差别。", "size": 9.5, "color": TEXT, "line": 1.3, "space": 4},
    {"text": "② 沿槽随槽深上升，横槽在 d≥50 nm 后趋平 —— 两方向不同。", "size": 9.5, "color": TEXT, "line": 1.3, "space": 3},
    {"text": "③ 两面板纵轴范围不同，不能横向比高度。", "size": 9.5, "color": TEXT, "line": 1.3, "space": 3}],
   page=17, label="read guide")

rect(s, 8.35, 1.40, 4.53, 2.58, PANEL, LINE, 0.75, rounded=0.05)
tb(s, 8.52, 1.50, 4.18, 2.38,
   [{"text": "这页只在被追问时用", "size": 11, "bold": True, "color": BLUE, "line": 1.25},
    {"text": "沿槽偏差随 d/w 上升；固定槽深时随间隙增大而下降，但加入 h=25 nm 后并非处处单调。", "size": 9.8, "color": TEXT, "line": 1.35, "space": 5},
    {"text": "例：d=100 nm 沿槽 139.14→154.24→144.95→108.38%（h=25/50/75/125）。", "size": 9.8, "color": TEXT, "line": 1.35, "space": 3},
    {"text": "偏差有参数依赖，但尚不能确定唯一机制。", "size": 9.8, "color": SUB, "line": 1.35, "space": 3}],
   page=17, label="apA")

rect(s, 8.35, 4.12, 4.53, 1.58, LIKE_RED_BG, "E6C4C2", 0.75, rounded=0.05)
tb(s, 8.52, 4.20, 4.18, 1.42,
   [{"text": "为什么偏差这么大（口径）", "size": 10.5, "bold": True, "color": RED, "line": 1.25},
    {"text": "原公式把侧壁和台阶当作不存在；间隙越小、槽越深，这两处占比越大，偏差越大。", "size": 9.5, "color": TEXT, "line": 1.32, "space": 4},
    {"text": "这是定性解释，不是已证实的定量归因。", "size": 9.5, "bold": True, "color": RED, "line": 1.3, "space": 3}],
   page=17, label="why")

rect(s, 8.35, 5.84, 4.53, 0.72, PANEL, LINE, 0.75, rounded=0.05)
tb(s, 8.52, 5.90, 4.18, 0.60,
   [{"text": "换网格会变吗：4 个双网格几何变化 0.37—5.39 个百分点，横槽最敏感。", "size": 9.2, "color": TEXT, "line": 1.3}],
   anchor=MSO_ANCHOR.MIDDLE, page=17, label="grid")

notes(s, "这页是备查的，讲的时候可以不翻。它说明偏差不是单调的，参数依赖存在，但不能据此认定机制。")

# =====================================================================
# 18 appendix: Q&A
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "附录 B", "备查：老师可能追问的六个问题", 19,
     "回答口径与中文稿、证据对照表一致；不含未经核实的推断。")
table(s, 0.45, 1.44, 12.43,
      [["可能的追问", "回答要点"],
       ["你现在真正得到的结论是什么？", "原公式高估两个主方向的导度，偏差有方向差异；V2 降低整体最坏偏差但局部恶化。以 5 nm 离散参考为界，新条件预测仍待评价。"],
       ["这些组到底是哪些组？", "18 种 h–d 组合（h=25 三档、50/75/125 各五档），每种两方向共 36 点；本周 S0—S4 是验证组，不是新增几何。"],
       ["为什么用 OpenLB？", "直接解析沟槽几何求流量再提取 K，才能检验简化公式；但求解器自身也要过解析基准、网格、驱动力与守恒检查。"],
       ["OpenFOAM 都对比了，为什么还要继续？", "那批算例用的是输入等效阻力，检查的是接入一致性；判断 V2 准确需要同条件、且不以 V2 为输入的合格参考。"],
       ["1.328% 离 1% 很近，为什么不算通过？", "1% 是事先冻结的门槛，看到结果不能放宽；可以讨论补证或收窄主张，但原 FAIL 必须保留。"],
       ["哪些是你做的，哪些是 AI 做的？", "代码、检查与材料整理有较多 AI 辅助；我正在逐项学习几何、公式与结果含义，尚不能独立解释的部分会明确指出。"]],
      [3.60, 8.83], fs=10.5, header_fs=11.5, row_h=0.80,
      aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT], first_col_bold=True)
notes(s, "这页也是备查。如果老师问到，我按这里的口径回答，不临场加工。")

# =====================================================================
# 19 appendix: evidence index
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "附录 C", "备查：本页每个数字的证据入口", 20,
     "路径相对 docs/reports/；本轮无新增计算或验证。")
_idx = [("历史 18 几何、36 点、原公式偏差、V2 残差", "PAPER1_claim_evidence_matrix_20261104/REPORT.md"),
        ("S1 光滑平板解析基准", "URV_S1_results_review_20261102/REPORT.md"),
        ("S2 常规间隙六条、三网格指标", "URV_S2_completed_review_20261103_095422/REPORT.md"),
        ("S3 驱动力三档控制", "URV_S3_completed_review_20261103_172033/REPORT.md"),
        ("S4 薄间隙六条与横槽 FAIL", "URV_S4_completed_review_20261104_143205/REPORT.md"),
        ("0.625 nm 补证准备状态", "URV_S4_TGE_preparation_20261104_152009/REPORT.md"),
        ("OpenFOAM C01—C04 / GDI01 核对", "OpenFOAM_comparison_clarification_20261104/REPORT.md"),
        ("逐页讲稿与本周进展摘要", "PAPER1_PPT逐页讲稿 / PAPER1_本周进展（同日报告）")]
for i, (a, b) in enumerate(_idx):
    y = 1.46 + i * 0.63
    rect(s, 0.45, y, 12.43, 0.55, PANEL if i % 2 == 0 else BG, LINE, 0.6, rounded=0.04)
    tb(s, 0.66, y + 0.05, 5.55, 0.45,
       [{"text": a, "size": 10.5, "bold": True, "color": TEXT, "line": 1.15}],
       anchor=MSO_ANCHOR.MIDDLE, page=19, label="idx a")
    tb(s, 6.30, y + 0.05, 6.55, 0.45,
       [{"text": b, "size": 8.4, "color": MID, "line": 1.1}],
       anchor=MSO_ANCHOR.MIDDLE, page=19, label="idx b")
notes(s, "最后一页是证据索引，不上台讲，留着备查。")

prs.save(OUT)
print("saved:", OUT, "slides:", len(prs.slides.__iter__.__self__._sldIdLst))

# ---------------- overflow self-check ----------------
bad = 0
for (pg, lab, need, have) in _checks:
    if need > have + 0.02:
        bad += 1
        print("OVERFLOW p%02d %-22s need=%.2f have=%.2f" % (pg, lab, need, have))
print("overflow warnings:", bad, "/", len(_checks))

# ---------------- bounds self-check (shapes must stay inside the page) ----------------
oob = 0
for i, sl in enumerate(prs.slides, start=1):
    for sh in sl.shapes:
        try:
            bottom = (sh.top + sh.height) / 914400.0
            right = (sh.left + sh.width) / 914400.0
        except TypeError:
            continue
        if bottom > 7.52 or right > 13.36 or sh.top < 0 or sh.left < 0:
            oob += 1
            print("OUT-OF-BOUNDS p%02d %-18s right=%.2f bottom=%.2f"
                  % (i, sh.shape_type, right, bottom))
print("bounds warnings:", oob)
