# -*- coding: utf-8 -*-
"""Build a concise (5-page) advisor deck: 1.25 nm server rerun + build equivalence.

All numbers come from docs/reports/URV_S4_TGE_1p25_结果复核_20261104/REPORT.md
and URV_S4_TGE_1p25_结果汇报_20261104.md. No new simulation, no new validation.
"""
import math, os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ---------------- palette (reuse academic blue/white) ----------------
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
GREEN = "2E9E5B"
LIKE_RED_BG = "FBECEC"
LIKE_GRN_BG = "EAF3EC"

FONT = "Microsoft YaHei"
W, H = 13.333, 7.5
TOTAL = 5
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "PAPER1_1p25结果_20261105.pptx")

prs = Presentation()
prs.slide_width  = Inches(W)
prs.slide_height = Inches(H)
BLANK = prs.slide_layouts[6]

_checks = []

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

def base(slide, tag, title, page, footer, title_size=25, title_y=0.50, title_h=0.66):
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

def chip(slide, x, y, w, h, text, fill=LIGHT, color=BLUE, size=10.5, bold=True, radius=0.28):
    rect(slide, x, y, w, h, fill, None, rounded=radius)
    tb(slide, x, y + (h - 0.26) / 2, w, 0.26,
       [{"text": text, "size": size, "bold": bold, "color": color, "line": 1.0}],
       align=PP_ALIGN.CENTER)

FOOT = "SIM240 第一篇 · 1.25 nm 服务器重跑 · 2026-11-05"

# =====================================================================
# 01 封面
# =====================================================================
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, W, 0.14, NAVY)
rect(s, 0, 0.14, 0.30, H - 0.14, LIGHT2)
rect(s, 0.62, 1.28, 0.055, 3.10, NAVY)
chip(s, 0.88, 1.22, 2.72, 0.34, "第一篇单相研究 · 本周进展", LIGHT, BLUE, 10.5)
tb(s, 0.88, 1.72, 11.4, 0.80,
   [{"text": "薄间隙 1.25 nm 服务器重跑", "size": 40, "bold": True, "color": NAVY, "line": 1.15}],
   page=1, label="cover title")
tb(s, 0.88, 2.62, 11.4, 0.52,
   [{"text": "结果与本机逐位一致，构建等价成立", "size": 21, "color": MID, "line": 1.2}],
   page=1, label="cover sub")

# 三个结论卡
concl = [
    ("构建等价", "相对差 = 0", GREEN, LIKE_GRN_BG),
    ("数值质量", "18 项核对全过", BLUE, LIGHT),
    ("实测开销", "2h6m · 1.6 GB", NAVY, PANEL),
]
cx = 0.88
for title, val, col, bg in concl:
    rect(s, cx, 3.55, 3.80, 1.10, bg, None, rounded=0.06)
    tb(s, cx + 0.25, 3.72, 3.30, 0.36,
       [{"text": title, "size": 13, "bold": True, "color": SUB, "line": 1.0}])
    tb(s, cx + 0.25, 4.10, 3.30, 0.42,
       [{"text": val, "size": 20, "bold": True, "color": col, "line": 1.0}])
    cx += 4.00

tb(s, 0.88, 5.10, 11.4, 1.05,
   [{"text": "薄间隙横槽最细那档网格，放到实验室服务器重算，答案和本机一模一样——", "size": 15, "color": TEXT, "line": 1.5},
    {"text": "换机器、换编译，结果不变", "size": 15, "bold": True, "color": NAVY, "line": 1.5},
    {"text": "。这为「服务器结果可配对本机原始点」扫清了前提。", "size": 15, "color": TEXT, "line": 1.5}],
   page=1, label="cover body")
tb(s, 0.88, 6.30, 11.4, 0.4,
   [{"text": "（不是 S4 通过——横槽 1.328% > 1% 的结论原样保留）", "size": 11.5, "color": MUT, "line": 1.2}],
   page=1, label="cover caveat")
notes(s, "封面：一句话——1.25nm 服务器重跑完成，答案与本机逐位一致，构建等价成立。\n"
         "但明确强调：这只是「换机器算得一样」，不等于 S4 薄间隙这个点通过，1.328% 的 FAIL 没变。")

# =====================================================================
# 02 这件事是什么
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "背景 · 为什么重跑", "这件事是什么：S4 卡点 + 重跑的两个目的", 2, FOOT)

tb(s, 0.60, 1.50, 12.1, 0.50,
   [{"text": "卡点回顾", "size": 17, "bold": True, "color": NAVY, "line": 1.1}], page=2, label="h1")
rect(s, 0.60, 2.05, 12.1, 1.55, PANEL, LINE, lw=0.75, rounded=0.04)
tb(s, 0.90, 2.22, 11.5, 1.25,
   [{"text": "薄间隙（间隙 30 nm、槽深 80 nm）横槽方向，三档网格（5 / 2.5 / 1.25 nm）算出的", "size": 14, "line": 1.4},
    {"text": "中细差 = 1.328%，超过 1% 门槛", "size": 14, "bold": True, "color": RED, "line": 1.4},
    {"text": "，这个点暂未通过。", "size": 14, "line": 1.4}],
   page=2, label="背景")

tb(s, 0.60, 3.90, 12.1, 0.50,
   [{"text": "这周做了什么：把最细的 1.25 nm 拿到服务器（内存大得多）重跑，两个目的", "size": 17, "bold": True, "color": NAVY, "line": 1.1}], page=2, label="h2")

# 两个目的卡
purposes = [
    ("目的 ① · 验证「构建等价」", "换一台机器、重新编译程序，算出的数字是不是还一样。\n这是后面能不能放心用服务器结果的前提。", BLUE, LIGHT),
    ("目的 ② · 实测真实开销", "这一档到底吃多少内存、跑多快，给「要不要再加密到 0.625 nm」一个准数。", NAVY, PANEL),
]
px = 0.60
for title, body, col, bg in purposes:
    rect(s, px, 4.50, 5.95, 1.80, bg, None, rounded=0.05)
    tb(s, px + 0.30, 4.68, 5.35, 0.40,
       [{"text": title, "size": 14.5, "bold": True, "color": col, "line": 1.1}])
    tb(s, px + 0.30, 5.12, 5.35, 1.10,
       [{"text": body, "size": 12.5, "color": SUB, "line": 1.4}])
    px += 6.20
notes(s, "讲清楚背景：S4 薄间隙横槽 1.328% 超 1% 门槛，卡点。这周重跑 1.25 有两个目的：验证构建等价、实测开销。")

# =====================================================================
# 03 核心结果①
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "核心结果①", "构建等价成立，且是「完美」级", 3, FOOT)

tb(s, 0.60, 1.42, 12.1, 0.46,
   [{"text": "两台机器、两个编译版本，答案逐位相同", "size": 16, "bold": True, "color": SUB, "line": 1.1}], page=3, label="lead")

data = [
    ["项目", "数值"],
    ["服务器算出的 K 值", "3.471791836744987 × 10⁻²⁴ m³"],
    ["本机参照 K 值（测量前冻结）", "3.471791836744987 × 10⁻²⁴ m³"],
    ["相对差", "0（逐位相同）"],
    ["判定门槛", "≤ 1 × 10⁻⁶"],
]
table(s, 0.60, 2.00, 6.20, data, [3.10, 3.10], fs=13, header_fs=13, row_h=0.62,
      aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER],
      cell_styles={(3, 1): {"bold": True, "color": GREEN}, (4, 1): {"color": SUB}})

# 右边：绿色大结论
rect(s, 7.05, 2.00, 5.65, 1.55, LIKE_GRN_BG, None, rounded=0.05)
tb(s, 7.35, 2.20, 5.05, 0.42,
   [{"text": "构建等价", "size": 15, "bold": True, "color": GREEN, "line": 1.0}])
tb(s, 7.35, 2.62, 5.05, 0.80,
   [{"text": "相对差 = 0", "size": 26, "bold": True, "color": GREEN, "line": 1.1}])
tb(s, 7.35, 3.30, 5.05, 0.30,
   [{"text": "判据只要求 ≤ 百万分之一，实测为零", "size": 10.5, "color": SUB, "line": 1.1}])

tb(s, 0.60, 4.05, 12.1, 0.46,
   [{"text": "数值质量：全部干净", "size": 16, "bold": True, "color": NAVY, "line": 1.1}], page=3, label="h2")

data2 = [
    ["检查项", "结果", "检查项", "结果"],
    ["数值门槛", "通过", "质量守恒", "4.4×10⁻¹⁵"],
    ["几何正确", "通过", "Mach 数", "6.3×10⁻⁹"],
    ["非法边界 / 回退", "0 / 0", "是否收敛", "是（满额 12537 步）"],
]
table(s, 0.60, 4.62, 12.1, data2, [2.40, 2.60, 2.40, 2.60], fs=12.5, header_fs=12.5, row_h=0.56,
      aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.CENTER],
      cell_styles={(1, 1): {"color": GREEN, "bold": True}, (2, 1): {"color": GREEN, "bold": True},
                   (3, 1): {"color": GREEN, "bold": True}})
notes(s, "核心结果①：服务器 K 和本机 K 逐位相同，相对差=0，构建等价成立。数值质量全部干净。\n"
         "强调「逐位相同」是比特级一致，比判据严格得多。")

# =====================================================================
# 04 核心结果② + 边界
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "核心结果② + 边界", "实测开销，以及「能说 / 不能说」", 4, FOOT)

tb(s, 0.60, 1.42, 12.1, 0.46,
   [{"text": "实测开销（给「要不要跑 0.625」的准数）", "size": 16, "bold": True, "color": NAVY, "line": 1.1}], page=4, label="h1")
data = [
    ["总耗时", "峰值内存", "速度"],
    ["2 小时 6 分", "约 1.6 GB", "1.65 步/秒"],
]
table(s, 0.60, 1.98, 8.20, data, [2.73, 2.73, 2.74], fs=14, header_fs=13, row_h=0.66)

tb(s, 0.60, 3.15, 12.1, 0.46,
   [{"text": "能说什么 / 不能说什么（重要）", "size": 16, "bold": True, "color": NAVY, "line": 1.1}], page=4, label="h2")

# 左：能说
rect(s, 0.60, 3.70, 5.95, 2.55, LIKE_GRN_BG, None, rounded=0.05)
tb(s, 0.90, 3.86, 5.35, 0.40,
   [{"text": "能说（有证据）", "size": 14, "bold": True, "color": GREEN, "line": 1.0}])
tb(s, 0.90, 4.30, 5.35, 1.80,
   [{"text": "• 1.25 nm 服务器成功跑完，结果与本机一致，构建等价成立。", "size": 12.5, "color": TEXT, "line": 1.45},
    {"text": "• 为「服务器结果可配对本机原始点」扫清了前提。", "size": 12.5, "color": TEXT, "line": 1.45, "space": 6}],
   page=4, label="能说")

# 右：不能说
rect(s, 6.75, 3.70, 5.95, 2.55, LIKE_RED_BG, None, rounded=0.05)
tb(s, 7.05, 3.86, 5.35, 0.40,
   [{"text": "不能说（避免过度声称）", "size": 14, "bold": True, "color": RED, "line": 1.0}])
tb(s, 7.05, 4.30, 5.35, 1.80,
   [{"text": "• 这还不足以让「S4 薄间隙」通过：横槽 1.328% > 1% 没变。", "size": 12.5, "color": TEXT, "line": 1.45},
    {"text": "• 这不是「验证成功」，是「换机器得到一致结果」——回答的是「构建可不可信」，不是「横槽收敛没收敛」。", "size": 12.5, "color": TEXT, "line": 1.45, "space": 6}],
   page=4, label="不能说")
notes(s, "核心结果②：实测开销 2h6m、1.6GB、1.65 步/秒。\n"
         "重点讲「能说/不能说」：能说构建等价成立；不能说 S4 通过，1.328% 的 FAIL 没变。")

# =====================================================================
# 05 留给导师的决策
# =====================================================================
s = prs.slides.add_slide(BLANK)
base(s, "待导师拍板", "薄间隙这个点，论文打算怎么处理？", 5, FOOT)

tb(s, 0.60, 1.50, 12.1, 0.50,
   [{"text": "两条路（需导师定，不是我们能定的）", "size": 17, "bold": True, "color": NAVY, "line": 1.1}], page=5, label="lead")

# 路 A
rect(s, 0.60, 2.15, 12.1, 1.75, PANEL, LINE, lw=0.75, rounded=0.05)
chip(s, 0.85, 2.35, 1.55, 0.34, "路 A · 收窄", LIGHT, BLUE, 11)
tb(s, 2.65, 2.35, 9.8, 1.45,
   [{"text": "薄间隙如实写成「现有网格下未收敛到 1%，作为已知边界报告」，不作为主要结论。", "size": 14, "color": TEXT, "line": 1.4},
    {"text": "→ 不需要再跑 0.625，明天即可收尾。", "size": 14, "bold": True, "color": GREEN, "line": 1.4, "space": 4}],
   page=5, label="路A")

# 路 B
rect(s, 0.60, 4.15, 12.1, 1.75, PANEL, LINE, lw=0.75, rounded=0.05)
chip(s, 0.85, 4.35, 1.55, 0.34, "路 B · 补证", LIGHT, BLUE, 11)
tb(s, 2.65, 4.35, 9.8, 1.45,
   [{"text": "坚持「薄间隙也要收敛到 1% 以内」→ 需再加密一层 0.625 nm。", "size": 14, "color": TEXT, "line": 1.4},
    {"text": "内存已实测约 10.7 GB（服务器 126 GB 够），约 63 小时；能否压到 1% 是估算，非保证。", "size": 13, "color": SUB, "line": 1.4, "space": 4}],
   page=5, label="路B")

tb(s, 0.60, 6.20, 12.1, 0.50,
   [{"text": "本轮为结果整理，无新增计算；原始横槽 1.328% FAIL 与冻结门槛不变。", "size": 11.5, "color": MUT, "line": 1.2}],
   page=5, label="footnote")
notes(s, "最后一个待导师拍板的问题：薄间隙这个点，路 A 收窄（如实报告未收敛，不用跑 0.625），\n"
         "还是路 B 补证（跑 0.625 再加密一层）。关键数字：0.625 内存约 10.7GB、约 63 小时。")

# =====================================================================
# 版面自检
# =====================================================================
issues = []
for page, label, need, have in _checks:
    if need > have + 0.02:
        issues.append((page, label, need, have))

prs.save(OUT)
print("saved:", OUT)
print("checks:", len(_checks), "issues:", len(issues))
for p, l, n, h in issues:
    print("  OVERFLOW p%d %s need=%.2f have=%.2f" % (p, l, n, h))
