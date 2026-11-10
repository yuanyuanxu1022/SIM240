# -*- coding: utf-8 -*-
"""13-page 16:9 briefing PDF — table-first, no filler prose.

Design contract (differs from the earlier 28-page prose version):
  1. every page is carried by a table or a figure, not by paragraphs;
  2. at most one 20px conclusion line per page;
  3. no "how to say this", no "if the advisor asks", no meta commentary;
  4. emphasis by colour + weight on numbers, not by adjectives.

Numbers come from existing reports (indexed on the last page).
Building this document performs no simulation and no new validation.
"""
import os
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "SIM240_PAPER1_Briefing_20261105_v3.pdf")

NAVY, BLUE, MID = "#0E3F8C", "#1E4FA8", "#3D7BD9"
LIGHT, LIGHT2, PANEL = "#E8EFF8", "#F3F7FC", "#F8FAFD"
TEXT, SUB, MUT, LINE, WHITE = "#1A2230", "#4A5568", "#8B97A8", "#D3DAE4", "#FFFFFF"
RED, REDBG, GRN, GRNBG, GOLDBG = "#B7332C", "#FBECEA", "#2F6B3C", "#EAF3EC", "#FCF3DF"

P = []


def div(x, y, w, h, inner="", bg=None, border=None, r=0, extra=""):
    s = ["position:absolute", "left:%dpx" % x, "top:%dpx" % y,
         "width:%dpx" % w, "height:%dpx" % h, "box-sizing:border-box",
         "background:%s" % (bg or "transparent")]
    if border: s.append("border:" + border)
    if r: s.append("border-radius:%dpx" % r)
    if extra: s.append(extra)
    return '<div style="%s">%s</div>' % (";".join(s), inner)


def t(x, y, w, h, s, size=13, color=TEXT, bold=False, lh=1.45, align="left", extra=""):
    st = ["position:absolute", "left:%dpx" % x, "top:%dpx" % y,
          "width:%dpx" % w, "height:%dpx" % h, "font-size:%dpx" % size,
          "line-height:%.2f" % lh, "color:%s" % color,
          "text-align:%s" % align, "box-sizing:border-box"]
    if bold: st.append("font-weight:700")
    if extra: st.append(extra)
    return '<div style="%s">%s</div>' % (";".join(st), s)


def hr(x, y, w, color=LINE, h=1):
    return div(x, y, w, h, "", bg=color)


def badge(x, y, w, h, s, bg=LIGHT, color=BLUE, size=10.5):
    return div(x, y, w, h,
               t(0, (h - size * 1.3) / 2, w, size * 1.3, s, size=size,
                 color=color, bold=True, lh=1.3, align="center"),
               bg=bg, r=3)


def table(cols, rows, x, y, cw, rh=38, hh=40, fs=12.5, hfs=12,
          aligns=None, styles=None, zebra=True, head=BLUE, total=None):
    aligns = aligns or ["left"] * len(cols)
    o = ['<table style="position:absolute;left:%dpx;top:%dpx;width:%dpx;'
         'border-collapse:collapse;table-layout:fixed;font-size:%dpx;">' % (x, y, sum(cw), fs)]
    o.append("<colgroup>" + "".join('<col style="width:%dpx">' % c for c in cw) + "</colgroup><thead><tr>")
    for i, c in enumerate(cols):
        o.append('<th style="height:%dpx;background:%s;color:#fff;font-size:%dpx;'
                 'font-weight:700;text-align:%s;padding:0 10px;">%s</th>'
                 % (hh, head, hfs, aligns[i], c))
    o.append("</tr></thead><tbody>")
    for ri, row in enumerate(rows):
        istot = total is not None and ri == len(rows) - 1
        bg = LIGHT2 if istot else (PANEL if (zebra and ri % 2 == 1) else WHITE)
        o.append("<tr>")
        for ci, v in enumerate(row):
            st = (styles or {}).get((ri, ci), {})
            o.append('<td style="height:%dpx;background:%s;color:%s;text-align:%s;'
                     'padding:0 10px;border-bottom:1px solid %s;%s">%s</td>'
                     % (rh, st.get("bg", bg), st.get("color", TEXT), aligns[ci], LINE,
                        "font-weight:700;" if st.get("bold", istot or ci == 0) else "", v))
        o.append("</tr>")
    o.append("</tbody></table>")
    return "".join(o)


TOTAL = 15

def page(tag, title, body, note, n=None, total=None):
    n = len(P) + 1
    total = TOTAL
    P.append('<div class="page">%s%s%s</div>' % (
        hr(0, 0, 1280, NAVY, 7)
        + t(43, 18, 900, 16, tag, size=10, color=MID, lh=1.2)
        + t(43, 36, 1150, 40, title, size=27, color=NAVY, bold=True, lh=1.2)
        + hr(43, 88, 1194, LINE, 1)
        , body,
        hr(43, 678, 1194, LINE, 1)
        + t(43, 684, 1000, 20, note, size=9.5, color=MUT, lh=1.2)
        + t(1040, 684, 197, 20, "%02d / %d" % (n, total), size=10, color=BLUE, lh=1.2, align="right")
    ))


# ============================================================ 01 cover
P.append('<div class="page">'
 + hr(0, 0, 1280, NAVY, 9)
 + div(43, 56, 5, 214, "", bg=NAVY)
 + t(70, 56, 700, 24, "第一篇单相研究　·　导师汇报", size=12.5, color=MID, lh=1.3)
 + t(70, 90, 900, 52, "纳米矩形沟槽的方向性输运", size=42, color=NAVY, bold=True, lh=1.2)
 + t(70, 150, 900, 32, "局部立方律偏差、经验修正与验证进展", size=20, color=MID, lh=1.3)
 + hr(70, 196, 300, LINE, 1.5)
 + t(70, 210, 620, 52, "固定间隙　·　完全充液　·　单相牛顿流体　·　周期直槽<br>"
                        "2026 年 11 月 5 日　·　15 页", size=12.5, color=SUB, lh=1.95)

# contents on the right
 + t(736, 56, 500, 20, "本文件结构", size=11, color=BLUE, bold=True, lh=1.3)
 + table(["页", "内容", "页", "内容"],
         [["1", "封面", "9", "各向异性与流向"],
          ["2", "全篇结论一览", "10", "本周验证总览 S0—S4"],
          ["3", "几何与符号", "11", "基准 / 网格 / 驱动力"],
          ["4", "18 组几何采样", "12", "薄间隙网格未通过"],
          ["5", "18 组逐点结果", "13", "OpenFOAM 结论"],
          ["6", "方向性", "14", "能说 / 不能说"],
          ["7", "原公式偏差", "15", "两个请示"],
          ["8", "V2 修正", "—", "—"]],
         736, 74, [30, 186, 30, 186], rh=22, hh=24, fs=8, hfs=8,
         aligns=["center", "left", "center", "left"],
         styles={(i, 0): {"color": NAVY} for i in range(8)})

# three KPI — each 大数字 + 它是什么 + 怎么来的
 + div(70, 288, 290, 128,
       t(0, 12, 290, 30, "18 组", size=26, color=NAVY, bold=True, lh=1.1, align="center")
       + t(0, 46, 290, 20, "几何组合", size=11, color=NAVY, bold=True, lh=1.2, align="center")
       + t(12, 68, 266, 18, "间隙 h × 槽深 d 的搭配", size=9, color=TEXT, lh=1.2, align="center")
       + t(12, 88, 266, 40, "4 档间隙 × 5 档槽深，<br>实际算出 18 种（缺 2 格）", size=8.5, color=SUB, lh=1.4, align="center"),
       bg=PANEL, border="1px solid " + LINE, r=4)
 + div(374, 288, 290, 128,
       t(0, 12, 290, 30, "36 点", size=26, color=NAVY, bold=True, lh=1.1, align="center")
       + t(0, 46, 290, 20, "方向样点", size=11, color=NAVY, bold=True, lh=1.2, align="center")
       + t(12, 68, 266, 18, "18 组 × 2 个方向", size=9, color=TEXT, lh=1.2, align="center")
       + t(12, 88, 266, 40, "每组建模算两次：<br>沿槽一次、横槽一次", size=8.5, color=SUB, lh=1.4, align="center"),
       bg=PANEL, border="1px solid " + LINE, r=4)
 + div(678, 288, 290, 128,
       t(0, 12, 290, 30, "5 组", size=26, color=RED, bold=True, lh=1.1, align="center")
       + t(0, 46, 290, 20, "本周验证 S0—S4", size=11, color=RED, bold=True, lh=1.2, align="center")
       + t(12, 68, 266, 18, "平板 · 网格 · 驱动力 · 薄间隙", size=9, color=TEXT, lh=1.2, align="center")
       + t(12, 88, 266, 40, "4 组通过，<br>1 组停在横槽网格", size=8.5, color=RED, lh=1.4, align="center"),
       bg=REDBG, border="1px solid #E6C6C2", r=4)

# bottom note
 + div(70, 430, 898, 52, t(18, 11, 862, 34,
       "全部偏差 = 相对 5 nm 离散数值参考的偏差，非实验真值；V2 为回顾性修正，新条件预测未证明。",
       size=11, color=NAVY, bold=True, lh=1.3), bg=LIGHT, r=4)
 + div(70, 430, 5, 52, "", bg=NAVY)

# key numbers strip
 + t(70, 502, 900, 18, "关键数字速查（细节见第 2 页）", size=10, color=BLUE, bold=True, lh=1.2)
 + table(["量", "值", "量", "值"],
         [["K<sub>yy</sub> / K<sub>xx</sub>（h60/d80）", "5.9073 / 2.3489 e−23 m³", "原公式最大高估", "+204.85%"],
          ["横槽 / 沿槽阻力", "2.515 倍", "V2 后最大绝对偏差", "10.5% / 18.7%"],
          ["薄间隙横槽中细变化", "1.328%（门槛 1%）", "各向异性 A（h75/d100）", "2.21（模型 3.70）"]],
         70, 522, [220, 290, 220, 290], rh=26, hh=24, fs=9, hfs=9,
         aligns=["left", "center", "left", "center"],
         styles={(i, 0): {"color": NAVY} for i in range(3)} | {(i, 2): {"color": NAVY} for i in range(3)})
 + t(70, 628, 900, 18, "代码、检查、材料整理有 AI 辅助；科学结论由作者核对并负责。", size=9, color=MUT, lh=1.2)
 + '</div>')

# ============================================================ 02 summary table
rows = [
    ["槽深对两方向影响不同", "K<sub>yy</sub> 涨 3.55×（h50）；K<sub>xx</sub> 变 &lt; 4%", "已采样", "表 5"],
    ["原公式 36 点全部高估导度", "沿槽 +10.30→+204.85%；横槽 +8.11→+54.19%", "已采样", "表 6"],
    ["偏差改变各向异性与流向", "A 2.21 对 3.70（+67%）；45° 流向差 9.20°", "已采样", "表 7"],
    ["V2 压低整体最坏偏差", "204.85→10.5%；54.19→18.7%", "回顾性", "表 8"],
    ["V2 存在局部失效点", "h25/d100 横槽 16.36→18.71%（5 nm 参考）", "反例", "表 8"],
    ["平板解析基准", "K 误差 0.173%；剖面 L2 误差 0.079%", "通过", "S1"],
    ["常规间隙三网格", "中细 0.203% / 0.744%（门槛 1%）", "通过", "S2"],
    ["常规间隙三档驱动力", "L = 8.30e−8 / 3.81e−8（门槛 1e−3）", "通过", "S3"],
    ["薄间隙三网格", "横槽中细 1.328% &gt; 1% → 阶段未通过", "未通过", "S4"],
    ["V2 对新条件的预测能力", "参考资格与模型比较均未评价", "未评价", "P1/P2"],
]
st = {}
for i in range(len(rows)):
    c = rows[i][2]
    st[(i, 2)] = {"color": GRN if c == "通过" else (RED if c in ("未通过",) else NAVY)}
b = t(43, 100, 1194, 20, "十行看完全篇：每一项的数值、状态、出处", size=11.5, color=SUB, lh=1.3)
b += table(["结论", "关键数值", "状态", "出处"], rows, 43, 126, [452, 476, 116, 150],
           rh=50, hh=44, fs=12.5, aligns=["left", "left", "center", "center"], styles=st)
page("汇总", "全篇结论一览", b, "状态口径：已采样 = 5 nm 参考下的回顾性结论；未评价 = 缺合格参考。")

# ============================================================ 03 geometry
rows = [["h", "凸台顶面到上壁面的间隙", "60 nm", "槽内流体高度 = h + d"],
        ["d", "槽深", "80 nm", "决定 d/w，V2 只依赖它"],
        ["w", "槽宽", "120 nm", "与 P 共同固定采样"],
        ["P", "周期", "240 nm", "单胞宽度"],
        ["H", "平均流体厚度 h + d/2", "100 nm", "求平均速度 U = J/H 用"],
        ["K<sub>yy</sub>", "沿槽（y）薄膜导度", "5.9073e−23 m³", "基准几何 1.25 nm"],
        ["K<sub>xx</sub>", "横槽（x）薄膜导度", "2.3489e−23 m³", "同上；K<sub>xx</sub>/K<sub>yy</sub> = 2.515"]]
b = div(43, 100, 604, 470, '<img src="assets/fig1_geometry.png" style="width:604px;display:block;">',
        bg=WHITE, border="1px solid " + LINE)
b += t(43, 576, 604, 20, "图 1　(a) 流程　(b) 单胞剖面　(c) 两个主方向", size=9.5, color=MUT, lh=1.25)
b += table(["符号", "含义", "示例取值", "备注"], rows, 667, 104, [58, 190, 150, 172],
           rh=54, hh=40, fs=11.5, aligns=["center", "left", "center", "left"])
b += div(667, 522, 570, 52, t(16, 12, 538, 30,
       "h 不是槽底到上壁面的总高度 —— 这是最容易讲错的一处。", size=11.5, color=RED, bold=True, lh=1.3),
       bg=REDBG, r=3)
b += div(43, 612, 1194, 52, t(20, 14, 1154, 26,
       "只算固定间隙下的流动阻力。动态下压、槽内填充、困气、树脂流变均不作结论。",
       size=12, color=NAVY, bold=True, lh=1.3), bg=LIGHT, r=3)
page("1 研究什么 · 几何", "固定间隙、完全充液的矩形沟槽：两个方向的流动阻力", b,
     "图源：本文图 1；取值示例为 S4 之前的常规间隙条件 h60/d80。", 3)

# ============================================================ 04 sample
rows = [["薄间隙组", "25", "25 / 50 / 100", "3", "6", "缺 d = 75、120"],
        ["50 nm 组", "50", "25 / 50 / 75 / 100 / 120", "5", "10", "完整"],
        ["75 nm 组", "75", "25 / 50 / 75 / 100 / 120", "5", "10", "完整"],
        ["125 nm 组", "125", "25 / 50 / 75 / 100 / 120", "5", "10", "完整"],
        ["合计", "—", "4 档间隙 × 5 档槽深中的 18 格", "18", "36", "非完整 4×5 矩阵"]]
b = table(["分组", "间隙 h / nm", "已算槽深 d / nm", "几何", "方向点", "完整性"], rows,
          43, 106, [148, 130, 330, 90, 100, 396], rh=46, hh=44, fs=12.5,
          aligns=["left", "center", "left", "center", "center", "left"], total=True,
          styles={(4, 0): {"color": NAVY}, (4, 3): {"color": NAVY}, (4, 4): {"color": NAVY},
                  (4, 5): {"color": RED}, (0, 5): {"color": RED}})

b += div(43, 396, 176, 96, t(0, 14, 176, 34, "18", size=28, color=NAVY, bold=True, lh=1.1, align="center")
         + t(0, 52, 176, 28, "几何组合", size=11, color=TEXT, lh=1.6, align="center"),
         bg=PANEL, border="1px solid " + LINE, r=4)
b += div(230, 396, 176, 96, t(0, 14, 176, 34, "36", size=28, color=NAVY, bold=True, lh=1.1, align="center")
         + t(0, 52, 176, 28, "方向样点", size=11, color=TEXT, lh=1.6, align="center"),
         bg=PANEL, border="1px solid " + LINE, r=4)
b += div(417, 396, 176, 96, t(0, 14, 176, 34, "5 nm", size=23, color=NAVY, bold=True, lh=1.25, align="center")
         + t(0, 52, 176, 28, "生产网格", size=11, color=TEXT, lh=1.6, align="center"),
         bg=PANEL, border="1px solid " + LINE, r=4)
b += div(604, 396, 633, 96, t(18, 14, 598, 68,
       "18 = 几何数，36 = 方向点数。同一几何分两次驱动得两个 K，不构成新几何组。",
       size=11.5, color=NAVY, bold=True, lh=1.55), bg=LIGHT, r=4)
b += div(604, 396, 5, 96, "", bg=NAVY)

# right-bottom grid
b += t(43, 508, 660, 20, "为什么是 18 而不是 20", size=11, color=BLUE, bold=True, lh=1.3)
b += t(43, 532, 660, 120,
       "完整 4×5 矩阵应有 20 格；最薄间隙 h=25 nm 只算了 3 档槽深，缺 d=75 与 d=120 两格。<br>"
       "这 2 格在热图里是斜线格，全文不填补、不插值、不外推 —— 外推会在误差图上造出假点，"
       "而误差图是 C1 与 C2 的图形证据。", size=10.5, color=SUB, lh=1.65)

gw, gh, gx, gy = 66, 33, 830, 528
ds, hs = ["25", "50", "75", "100", "120"], ["125", "75", "50", "25"]
have = {(0, 0), (0, 1), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
        (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (3, 0), (3, 1), (3, 3)}
for ci, dd in enumerate(ds):
    b += t(gx + ci * gw, gy - 18, gw, 15, dd, size=9, color=SUB, lh=1.2, align="center")
for ri, hh_ in enumerate(hs):
    b += t(gx - 34, gy + ri * gh + 9, 30, 15, hh_, size=9, color=SUB, lh=1.2, align="right")
    for ci in range(5):
        f = (ri, ci) in have
        ex = ("background:%s" % ("#C9D9EE" if f else
              "repeating-linear-gradient(45deg,#EFF2F6,#EFF2F6 3px,#DCE2EA 3px,#DCE2EA 6px)"))
        b += div(gx + ci * gw + 2, gy + ri * gh + 2, gw - 4, gh - 4, "", r=2, extra=ex)
b += t(gx - 34, gy + 4 * gh + 4, 220, 14, "纵轴 间隙 h / nm", size=8.5, color=MUT, lh=1.2)
b += t(gx, gy + 4 * gh + 20, 220, 14, "横轴 槽深 d / nm →", size=8.5, color=MUT, lh=1.2)
b += t(gx + 5 * gw + 10, gy + 6, 78, 14, "深色已算", size=8.5, color=SUB, lh=1.2)
b += t(gx + 5 * gw + 10, gy + 40, 78, 14, "斜纹未算", size=8.5, color=RED, lh=1.2)

page("2 已有发现 · 采样", "18 组几何、36 个方向点（槽宽 120 nm、周期 240 nm 固定）", b,
     "参数组合见中文稿表 1（§2.1）。", 4)

# ============================================================ 05b 18-geometry full table
# 数据源：Table_S1_run_inventory.csv（group=main, dx=5 nm），K 由 m³ 换算为 1e-23 m³；
# E 与 V2 残差按式 (3)(4) 现算，结果与报告表 6 / 表 8 完全一致：
#   E_P ∈ [10.30, 204.85]%，E_T ∈ [8.11, 54.19]%，max|V2_P| = 10.50%，max|V2_T| = 18.71%
G18 = [
    (25,  25,  0.489,  0.214,  2.282,  19.93,   8.11,   5.52,  -7.10),
    (25,  50,  1.195,  0.221,  5.400,  52.60,  13.52,   7.21, -10.32),
    (25, 100,  3.430,  0.222, 15.450, 139.14,  16.36,   3.39, -18.71),
    (50,  25,  1.939,  1.417,  1.369,  17.49,  13.42,   3.38,  -2.53),
    (50,  50,  3.061,  1.462,  2.094,  53.13,  26.69,   7.59,   0.09),
    (50,  75,  4.349,  1.465,  2.969,  99.08,  33.67,   9.33,  -1.19),
    (50, 100,  5.736,  1.465,  3.916, 154.24,  37.14,   9.91,  -4.19),
    (50, 120,  6.886,  1.465,  4.701, 204.85,  38.69,  10.11,  -6.92),
    (75,  25,  5.176,  4.356,  1.188,  14.46,  13.51,   0.71,  -2.45),
    (75,  50,  6.755,  4.446,  1.520,  46.49,  30.07,   2.92,   2.76),
    (75,  75,  8.305,  4.448,  1.867,  90.50,  40.50,   4.62,   3.86),
    (75, 100,  9.834,  4.449,  2.210, 144.95,  46.51,   5.90,   2.35),
    (75, 120, 11.048,  4.449,  2.483, 195.54,  49.52,   6.75,   0.35),
    (125,  25, 20.127, 18.463,  1.090,  10.30,  11.68,  -2.94,  -4.03),
    (125,  50, 22.786, 18.621,  1.224,  33.72,  28.12,  -6.05,   1.22),
    (125,  75, 24.878, 18.626,  1.336,  66.70,  40.47,  -8.45,   3.84),
    (125, 100, 26.682, 18.634,  1.432, 108.38,  49.12,  -9.91,   4.18),
    (125, 120, 28.016, 18.637,  1.503, 147.77,  54.19, -10.50,   3.48),
]

def fnum(v, dec=3):
    return ("%." + str(dec) + "f") % v

rows18, st18 = [], {}
for i, (h, d, kyy, kxx, A, ep, et, rp, rt) in enumerate(G18):
    rows18.append([str(h), str(d), "%.2f" % (d / 120.0),
                   fnum(kyy), fnum(kxx), fnum(A),
                   "%+.2f%%" % ep, "%+.2f%%" % et,
                   "%+.2f%%" % rp, "%+.2f%%" % rt])
    if h == 25:
        for c in range(10):
            st18[(i, c)] = {"bg": "#FBF3E6"}
    # 原公式偏差着色：越大越深
    for c, v in ((6, ep), (7, et)):
        if v >= 150:
            st18[(i, c)] = {**st18.get((i, c), {}), "color": "#8E1E18", "bold": True}
        elif v >= 100:
            st18[(i, c)] = {**st18.get((i, c), {}), "color": RED, "bold": True}
        elif v >= 50:
            st18[(i, c)] = {**st18.get((i, c), {}), "color": "#9A5B12"}
    # V2 残差着色：|r| 越大越红
    for c, v in ((8, rp), (9, rt)):
        a = abs(v)
        if a >= 15:
            st18[(i, c)] = {"color": "#8E1E18", "bold": True, "bg": "#FBECEA"}
        elif a >= 10:
            st18[(i, c)] = {**st18.get((i, c), {}), "color": RED, "bold": True}
        elif a >= 6:
            st18[(i, c)] = {**st18.get((i, c), {}), "color": "#9A5B12"}

b = t(43, 98, 1194, 32,
      '槽宽 w = 120 nm、周期 P = 240 nm 固定；K 单位 10⁻²³ m³；E 与 V2 残差均为相对 5 nm 离散参考的百分比<br>'
      '<span style="color:#8B97A8">着色：原公式偏差 50—100% 橙 / 100—150% 红 / ≥150% 深红；V2 残差 |r| ≥6% 橙 / ≥10% 红 / ≥15% 深红底；'
      '米色底 = 最薄间隙 h=25 nm</span>',
      size=9.5, color=SUB, lh=1.45)
b += table(["h / nm", "d / nm", "d/w", "K<sub>yy</sub>", "K<sub>xx</sub>", "A = K<sub>yy</sub>/K<sub>xx</sub>",
            "原公式 E<sub>yy</sub>", "原公式 E<sub>xx</sub>", "V2 残差 yy", "V2 残差 xx"],
           rows18, 43, 130, [114, 70, 84, 134, 134, 86, 148, 148, 138, 138],
           rh=24, hh=32, fs=9, hfs=8.5,
           aligns=["center"] * 10, styles=st18, zebra=False)

b += t(43, 618, 1194, 40,
         '读法：E<sub>yy</sub> 列 18 个数全部为正 → 原公式在沿槽 18/18 高估；E<sub>xx</sub> 同样 18/18 为正。'
         'V2 残差出现负号 → 该点由高估转为低估，即修正在此处矫往过正。',
         size=9.5, color=NAVY, bold=True, lh=1.35)

page("2 已有发现 · 18 组全表",
     "18 组几何的具体尺寸与逐点结果（36 个方向点的全部数值）", b,
     "数据源：Table_S1_run_inventory.csv（group=main, dx=5 nm）；E 与 V2 残差按式 (3)(4) 现算，与表 6 / 表 8 一致。")

# ============================================================ 05 directionality
b = div(43, 100, 760, 344, '<img src="assets/fig4_k_aniso.png" style="width:760px;display:block;">',
        bg=WHITE, border="1px solid " + LINE)
b += t(43, 450, 760, 20, "图 2　(a) K<sub>yy</sub> 与 K<sub>xx</sub> 随槽深　(b) 各向异性 A = K<sub>yy</sub>/K<sub>xx</sub>", size=9.5, color=MUT, lh=1.25)

rows = [["50", "3.55×", "1.034×", "2.1 → 7.4"],
        ["75", "2.13×", "1.021×", "2.5 → 5.3"],
        ["125", "1.39×", "1.009×", "1.1 → 1.6"]]
b += table(["间隙 h / nm", "K<sub>yy</sub> 倍率", "K<sub>xx</sub> 倍率", "A 范围"], rows,
           823, 104, [110, 104, 104, 106], rh=44, hh=42, fs=11.5,
           aligns=["center", "center", "center", "center"],
           styles={(0, 1): {"color": NAVY}, (1, 1): {"color": NAVY}, (2, 1): {"color": NAVY},
                   (0, 2): {"color": RED}, (1, 2): {"color": RED}, (2, 2): {"color": RED}})
b += t(823, 286, 424, 20, "三行槽深均为 25 → 120 nm（4.8 倍）", size=10, color=MUT, lh=1.2)
b += div(823, 312, 424, 70, t(14, 9, 396, 52,
       "槽深涨 4.8 倍，沿槽导度涨 1.4—3.6 倍；横槽几乎不动（&lt; 4%）。",
       size=10.5, color=TEXT, lh=1.5), bg=PANEL, border="1px solid " + LINE, r=4)
b += div(823, 396, 424, 82, "", bg=LIGHT, r=4)
b += t(837, 404, 396, 66,
       "各向异性因此主要由槽深撑起来：<br>约 1.1（h125/d25）→ 15（h25/d100）。",
       size=11.5, color=NAVY, bold=True, lh=1.5)
b += div(823, 396, 5, 82, "", bg=NAVY)

b += div(43, 470, 760, 54, t(16, 10, 728, 34,
       "两个方向对同一几何变化的敏感度相差一个量级 —— 这是「方向性」的直接来源。",
       size=11.5, color=NAVY, bold=True, lh=1.4), bg=LIGHT, r=3)
b += div(43, 470, 5, 54, "", bg=NAVY)

rows2 = [["K<sub>yy</sub>（实线）", "随 d 单调上扬", "槽越深，沿槽越通畅"],
         ["K<sub>xx</sub>（虚线）", "四条几乎水平", "槽深不改善横槽通路"],
         ["A = K<sub>yy</sub>/K<sub>xx</sub>", "随 d 快速拉开", "方向性被槽深放大"]]
b += table(["看到什么", "图 2a / 2b 的趋势", "物理解读"], rows2, 43, 532,
           [176, 250, 334], rh=29, hh=28, fs=10, aligns=["left", "left", "left"])
b += t(43, 651, 760, 18,
       "限定：已采样 18 格范围内的观察，不外推到未采样几何与动态压印过程。",
       size=8.5, color=MUT, lh=1.2)
b += t(823, 494, 424, 170,
       "为什么倍率差这么多：K<sub>yy</sub> 走的是「深区 + 浅区并联」，深区一加深，通路立刻变宽；"
       "K<sub>xx</sub> 走的是「深区 + 浅区串联」，最窄的浅区卡住它，所以加深槽几乎没收益。",
       size=10.5, color=SUB, lh=1.6)
page("2 已有发现 · 方向性", "加深沟槽对沿槽输运的提升远大于横槽", b,
     "图源：本文图 2；5 nm 参考，18 几何 / 36 方向点；倍率来自表 5。", 5)

# ============================================================ 06 original law
b = div(43, 96, 726, 296, '<img src="assets/fig8_error_map.png" style="width:726px;display:block;">',
        bg=WHITE, border="1px solid " + LINE)
b += t(43, 398, 726, 20, "图 3　原公式偏差的 d–h 分布（左 沿槽 / 右 横槽）；斜线格未采样",
       size=9.5, color=MUT, lh=1.25)

rows = [["沿槽 K<sub>yy</sub>", "18", "+10.30% → +204.85%", "h50 / d120", "h125 / d25", "18 / 18"],
        ["横槽 K<sub>xx</sub>", "18", "+8.11% → +54.19%", "h125 / d120", "h25 / d25", "18 / 18"]]
b += table(["方向", "点数", "偏差范围", "最大点", "最小点", "高估点数"], rows,
           789, 100, [58, 40, 138, 74, 68, 70], rh=50, hh=52, fs=10, hfs=9.5,
           aligns=["center", "center", "center", "center", "center", "center"],
           styles={(0, 2): {"color": NAVY}, (1, 2): {"color": NAVY},
                   (0, 5): {"color": RED}, (1, 5): {"color": RED}})

b += div(789, 296, 448, 124, t(14, 10, 420, 104,
       "沿槽最大点模型值约为参考的 <b style=\"font-size:16px\">3.05 倍</b>；<br>"
       "沿槽最大偏差约为最小偏差的 <b>20 倍</b>，<br>"
       "范围明显宽于横槽。", size=11, color=TEXT, lh=1.55), bg=PANEL, border="1px solid " + LINE, r=4)

b += div(43, 424, 726, 62, t(16, 10, 694, 40,
       "36 个点无一例外全部高估导度 → 即全部低估阻力。方向一致，比幅度更重要。",
       size=12, color=NAVY, bold=True, lh=1.4), bg=LIGHT, r=3)
b += div(43, 500, 1194, 44, "", bg=REDBG, r=3)
b += t(62, 508, 1158, 28,
       "但参照是 5 nm 离散解，本身有网格误差 —— 它是「相对该参考的偏差」，不是相对实验值。",
       size=11, color=RED, bold=True, lh=1.3)

rows3 = [["沿槽", "随 d/w 增大而上升", "固定 d 时随 h 增大而下降"],
         ["横槽", "d ≥ 50 nm 后趋平", "随 h 增大而下降"],
         ["双网格 4 几何", "换 2.5 nm 参考后变化 0.37—5.39 个百分点", "横槽最敏感"]]
b += table(["观察对象", "趋势", "网格敏感性"], rows3, 43, 556,
           [174, 500, 520], rh=30, hh=30, fs=10.5, aligns=["left", "left", "left"])
page("2 已有发现 · 原公式", "原局部立方律在 36 个方向点上全部高估导度", b,
     "图源：本文图 4；误差定义式 (4)，5 nm 参考；中文稿表 6、表 2。", 6)

# ============================================================ 07 V2
rows = [["沿槽 18 点", "204.85%", "10.5%", "−194.35", "降"],
        ["横槽 18 点", "54.19%", "18.7%", "−35.49", "降"],
        ["横槽 h≥50 nm，15 点", "—", "6.9%", "—", "子集"],
        ["反例 h25/d100 横槽（5 nm 参考）", "16.36%", "18.71%", "+2.35", "升"],
        ["反例 h25/d100 横槽（2.5 nm 参考）", "21.76%", "14.94%", "−6.82", "降"]]
b = table(["范围", "原公式", "V2", "变化 / 百分点", "方向"], rows,
          43, 100, [290, 122, 120, 136, 70], rh=50, hh=44, fs=12,
          aligns=["left", "center", "center", "center", "center"],
          styles={(0, 2): {"color": NAVY}, (1, 2): {"color": NAVY}, (2, 2): {"color": NAVY},
                  (3, 2): {"color": RED}, (3, 4): {"color": RED}, (3, 0): {"color": RED}})

b += div(43, 384, 738, 196, "", bg=PANEL, border="1px solid " + LINE, r=4)
b += t(61, 392, 702, 18, "V2 的结构与局限", size=11, color=BLUE, bold=True, lh=1.2)
b += t(61, 412, 702, 30,
       "F<sub>yy</sub> = 1/[1+1.7685 (d/w)<sup>1.6331</sup>]　　F<sub>xx</sub> = 1/[1+0.4900 (d/w)<sup>0.6990</sup>]",
       size=10.5, color=TEXT, lh=1.4)
b += table(["局限", "具体表现"],
           [["只含 d/w，不含 h", "残差仍随间隙变化，结构上缺一个自变量"],
            ["非盲测", "9 个扩展几何在模型形式选择时已可见"],
            ["两组程序", "9 标定 + 9 扩展分属不同构建，不可分离"],
            ["超出标定范围", "d=120、h=25 均在标定范围之外"]],
           61, 448, [156, 500], rh=26, hh=26, fs=9, hfs=9,
           aligns=["left", "left"])
b += div(43, 600, 738, 52, t(16, 10, 706, 30,
       "结论：V2 是「对已有数据的拟合式描述」，不是预测关系。",
       size=12, color=NAVY, bold=True, lh=1.4), bg=LIGHT, r=3)
b += div(43, 600, 5, 52, "", bg=NAVY)

b += div(801, 100, 436, 262, "", bg=REDBG, border="1px solid #E6C6C2", r=4)
b += t(819, 110, 400, 20, "为什么反例必须留在正文", size=11.5, color=RED, bold=True, lh=1.3)
b += t(819, 134, 400, 218,
       "只报前两行，读者会认为 V2 单调改善。<br><br>"
       "第 4 行存在一个点变差；第 5 行说明<br>"
       "该点换个参考网格又变好 ——<br>"
       "局部结论本身依赖参考分辨率。<br><br>"
       "删掉这两行 = 夸大模型质量。", size=11, color=TEXT, lh=1.6)

b += div(801, 380, 436, 160, "", bg=PANEL, border="1px solid " + LINE, r=4)
b += t(819, 390, 400, 20, "要证明预测能力，缺什么", size=11.5, color=BLUE, bold=True, lh=1.3)
b += t(819, 414, 400, 116,
       "① 固定已公布系数不动<br>② 换未参与拟合的新几何<br>"
       "③ 该几何自身须先通过网格与驱动力检查<br>④ 再作同条件比较",
       size=11, color=TEXT, lh=1.65)

b += div(801, 558, 436, 106, "", bg=GOLDBG, border="1px solid #E3D2A8", r=4)
b += t(819, 566, 400, 20, "现行状态", size=10.5, color="#8A5E0B", bold=True, lh=1.3)
b += t(819, 588, 400, 68,
       "reference_qualified = false<br>MODEL_COMPARISON = NOT_EVALUATED",
       size=10.5, color=TEXT, lh=1.5, extra="font-family:monospace")
page("2 已有发现 · 经验修正", "V2 压低整体最坏偏差，但存在局部反向点", b,
     "同一 36 点样本、相对 5 nm 参考（末行另注 2.5 nm）；中文稿表 8，§4.4。", 7)

# ============================================================ 08 anisotropy
rows = [["各向异性 A = K<sub>yy</sub> / K<sub>xx</sub>", "2.21", "3.70", "+67%", "模型夸大方向性"],
        ["45° 驱动流向角 β", "24.34°", "15.14°", "−9.20°", "流向明显偏斜"]]
b = table(["项（基准几何 h=75 / d=100 nm）", "显式数值", "局部立方律", "差异", "含义"], rows,
          43, 100, [340, 150, 150, 150, 404], rh=56, hh=48, fs=12.5,
          aligns=["left", "center", "center", "center", "left"],
          styles={(0, 3): {"color": RED}, (1, 3): {"color": RED},
                  (0, 2): {"color": NAVY}, (1, 2): {"color": NAVY}})

b += div(43, 276, 590, 172, "", bg=PANEL, border="1px solid " + LINE, r=4)
b += t(61, 286, 554, 20, "由主值推流向（线性张量）", size=11.5, color=BLUE, bold=True, lh=1.3)
b += t(61, 310, 554, 32, "tan β = ( K<sub>xx</sub> / K<sub>yy</sub> ) · tan θ", size=18, color=TEXT, bold=True, lh=1.4)
b += t(61, 350, 554, 88,
       "θ、β 均自槽轴量起。θ = 45° 时，两组主值重建的流向相差 <b>9.20°</b>。<br>"
       "即：总量可能接近，方向已经偏。", size=11, color=TEXT, lh=1.55)

b += div(647, 276, 590, 172, "", bg=REDBG, border="1px solid #E6C6C2", r=4)
b += t(665, 286, 554, 20, "为什么只比总量会漏问题", size=11.5, color=RED, bold=True, lh=1.3)
b += t(665, 310, 554, 128,
       "压印填充关心「液体往哪流」，不只是「流了多少」。<br>"
       "总量对上、方向偏 9°，在窄槽里表现为<b>各槽进液不均</b>，"
       "进而影响残胶厚度分布。<br>"
       "<span style=\"color:#8B97A8\">（此因果链为推断，本文未验证残胶均匀性。）</span>",
       size=11, color=TEXT, lh=1.55)

rows2 = [["30° / 45° / 60° 斜向驱动", "检查同一主值的内部自洽", "不验证主值本身准确"],
         ["附录 E（T1）", "理想 Stokes 下给出非严格上界", "不给偏差幅度、不给方向比符号"]]
b += table(["已有检查 / 理论", "它能证明什么", "它不能证明什么"], rows2,
           43, 468, [330, 400, 464], rh=34, hh=34, fs=10.5,
           aligns=["left", "left", "left"])

b += div(43, 578, 1194, 44, t(20, 11, 1154, 24,
       "9.20° 来自同一张量的重建，不是实验测得的流向误差，不能推广为真实器件精度。",
       size=11.5, color=NAVY, bold=True, lh=1.3), bg=LIGHT, r=3)
b += div(43, 578, 5, 44, "", bg=NAVY)
b += t(43, 636, 1194, 36,
       "一句话：C3 的价值不在于多一个误差百分比，而在于说明「单一的导度标量不足以描述这个结构」——"
       "必须同时给两个主值。", size=11, color=SUB, lh=1.45)
page("2 已有发现 · 各向异性", "偏差改变各向异性与预测流向", b,
     "基准几何 h=75 / d=100 nm；中文稿表 7，式 (5)。", 8)

# ============================================================ 09 S0-S4
rows = [["S0", "修复回归", "h=75 / d=100", "质量观察量修复前后", "通过", "旧流动轨迹保持"],
        ["S1", "光滑平板", "h=30，无槽", "对解析解 K = h³/12", "通过", "K 0.173% / 剖面 0.079%"],
        ["S2", "常规间隙网格", "h=60 / d=80", "dx = 5 / 2.5 / 1.25 nm", "通过", "中细 0.203% / 0.744%"],
        ["S3", "常规间隙驱动力", "h=60 / d=80，dx=2.5", "a = 5e4 / 1e5 / 2e5 m·s⁻²", "通过", "L 8.30e−8 / 3.81e−8"],
        ["S4", "薄间隙网格", "h=30 / d=80，两方向", "dx = 5 / 2.5 / 1.25 nm", "未通过", "横槽中细 1.328% &gt; 1%"]]
b = table(["组", "名称", "条件 h / d，nm", "改的是什么", "结果", "关键数字"], rows,
          43, 102, [50, 152, 218, 240, 88, 446], rh=44, hh=40, fs=11,
          aligns=["center", "left", "left", "left", "center", "left"],
          styles={(0, 4): {"color": GRN}, (1, 4): {"color": GRN}, (2, 4): {"color": GRN},
                  (3, 4): {"color": GRN}, (4, 4): {"color": RED}, (4, 0): {"color": RED},
                  (4, 0): {"color": RED, "bg": "#FBECEA"},
                  (4, 1): {"color": RED, "bg": "#FBECEA"},
                  (4, 2): {"color": RED, "bg": "#FBECEA"},
                  (4, 3): {"color": RED, "bg": "#FBECEA"},
                  (4, 4): {"color": RED, "bg": "#FBECEA", "bold": True},
                  (4, 5): {"color": RED, "bg": "#FBECEA", "bold": True}})

# S4 单独展开：这一行是本页唯一未通过项，需要讲清尺寸与判据
b += div(43, 376, 760, 138, "", bg=REDBG, border="1px solid " + RED, r=4)
b += t(61, 383, 724, 18, "S4 展开：唯一未通过的一组", size=11.5, color=RED, bold=True, lh=1.3)
b += table(["h", "d", "w", "P", "H = h+d/2", "两方向", "三档网格", "判据"],
           [["30", "80", "120", "240", "70", "沿槽 / 横槽", "5 / 2.5 / 1.25", "中细 ≤ 1%"]],
           61, 404, [50, 50, 50, 50, 96, 110, 150, 112], rh=26, hh=24, fs=9, hfs=8.5,
           aligns=["center"] * 8,
           styles={(0, 0): {"color": NAVY}, (0, 1): {"color": NAVY}, (0, 4): {"color": NAVY},
                   (0, 7): {"color": RED, "bold": True}})
b += t(61, 458, 724, 46,
       '沿槽 0.165% → 通过；横槽 <b style="color:#B7332C">1.328%</b> → 超门槛 0.328 个百分点，'
       '全阶段判为未通过，S5 未启动。',
       size=10, color=TEXT, lh=1.4)

rows2 = [["S0 / S1 · 11-02", "A1 回归 + 两方向解析基准", "已有结果复核"],
         ["S2 · 11-03", "六条三网格", "已有结果复核"],
         ["S3 · 11-03", "四新条 + 两中档引用", "四新条为本周新增"],
         ["S4 · 11-04", "六条三网格", "已有结果复核"]]
b += table(["组 · 日期", "具体内容", "运行性质"], rows2, 43, 528,
           [130, 360, 220], rh=28, hh=26, fs=10,
           aligns=["left", "left", "left"])

b += div(823, 376, 414, 138, "", bg=PANEL, border="1px solid " + LINE, r=4)
b += t(841, 383, 378, 18, "这一行到底卡在哪", size=11, color=BLUE, bold=True, lh=1.3)
b += t(841, 402, 378, 106,
       "六条算例逐条都合格，<br>但两张网格之间的差超了门槛。<br>"
       "单条合格 ≠ 网格收敛，两者是独立的门。",
       size=10.5, color=TEXT, lh=1.5)

b += t(823, 528, 414, 100,
       "其余四组的条件是：S0 h75/d100、S1 h30 无槽、S2/S3 h60/d80。"
       "四组的槽宽均为 120 nm、周期 240 nm。",
       size=9.5, color=SUB, lh=1.5)


page("3 本周验证 · 总览", "五组验证：四组通过，一组停在横槽网格", b,
     "S0—S4 验收报告见各 URV_*_review 目录；本周新增长算 0 次、编译 0 次、门槛修改 0 次。")

# ============================================================ 10 S2 + S3
rows = [["5 nm", "5.9544", "2.4093", "—", "0.203%", "通过"],
        ["2.5 nm", "5.9193", "2.3664", "0.132%", "0.744%", "通过"],
        ["1.25 nm", "5.9073", "2.3489", "0.641%", "—", "—"]]
b = table(["网格 dx", "K<sub>yy</sub> / e−23 m³", "K<sub>xx</sub> / e−23 m³", "GCI 估计", "中细变化", "判定"], rows,
          43, 100, [100, 140, 140, 120, 118, 120], rh=46, hh=44, fs=11.5,
          aligns=["left", "center", "center", "center", "center", "center"],
          styles={(1, 0): {"color": NAVY}, (1, 4): {"color": BLUE}, (1, 5): {"color": GRN}})
b += t(43, 286, 738, 18, "S2　常规间隙 h60 / d80，两方向三网格", size=10, color=MUT, lh=1.2)
b += div(43, 306, 738, 42, t(16, 7, 706, 26,
       "横槽阻力 = 沿槽的 2.515 倍（1.25 nm 细网格）", size=13, color=NAVY, bold=True, lh=1.4),
       bg=LIGHT, r=3)
b += div(43, 306, 5, 42, "", bg=NAVY)

rows2 = [["5×10⁴", "5.91934", "2.36639", "4.000"],
         ["1×10⁵", "5.91934", "2.36639", "4.000"],
         ["2×10⁵", "5.91934", "2.36639", "4.000"]]
b += table(["a / m·s⁻²", "K<sub>yy</sub> / e−23 m³", "K<sub>xx</sub> / e−23 m³", "J / J₀"], rows2,
           43, 360, [180, 220, 220, 118], rh=42, hh=42, fs=11.5,
           aligns=["left", "center", "center", "center"])
b += t(43, 532, 738, 18, "S3　常规间隙 h60 / d80，固定 2.5 nm，三档驱动力", size=10, color=MUT, lh=1.2)
b += div(43, 552, 738, 44, t(15, 8, 706, 26,
       "K 三档跨度 L = 8.30e−8 / 3.81e−8，门槛 1e−3 → 线性响应成立",
       size=12, color=NAVY, bold=True, lh=1.3), bg=LIGHT, r=3)

b += div(801, 100, 436, 152, "", bg=PANEL, border="1px solid " + LINE, r=4)
b += t(819, 110, 400, 20, "S1　平板解析基准（h30，无槽）", size=11, color=BLUE, bold=True, lh=1.3)
b += t(819, 136, 400, 24, "K 误差 0.173%　剖面 0.079%", size=13, color=NAVY, bold=True, lh=1.4)
b += t(819, 164, 400, 84,
       "两方向均过原定标准。<br>作用：排除「实现写错」，"
       "否则沟槽偏差无法归因于公式。", size=10.5, color=SUB, lh=1.5)

b += div(801, 268, 436, 128, "", bg=GRNBG, border="1px solid #B6D3BE", r=4)
b += t(819, 278, 400, 20, "这组数的效力范围", size=11, color=GRN, bold=True, lh=1.3)
b += t(819, 300, 400, 92,
       "六条均 NUMERICAL_GATE / geometry / RESULT = PASS；<br>"
       "质量误差 ≤1.3e−14，Mach ≈2e−7，Re ≈1.9e−5。<br>"
       "合计 10.67 h，无超时。", size=10.5, color=TEXT, lh=1.5)

b += div(801, 416, 436, 140, "", bg=GOLDBG, border="1px solid #E3D2A8", r=4)
b += t(819, 426, 400, 20, "候选参考 ≠ 合格参考", size=11, color="#8A5E0B", bold=True, lh=1.3)
b += t(819, 450, 400, 100,
       "这组数未输入 V2 系数，可作候选参考。<br>"
       "但仍须过跨阶段参考资格审查，才可用于给 V2 打分。",
       size=10.5, color=TEXT, lh=1.5)

b += t(43, 620, 1194, 48,
       "分辨率上限由网格决定，不由驱动力控制决定：中细网格差 0.203% / 0.744%，"
       "比 S3 的 L（约 1e−7）大两个数量级 —— 因此不能说「导度准到七八位」。",
       size=10.5, color=SUB, lh=1.5)
page("3 本周验证 · 基准 / 网格 / 驱动力", "平板基准通过，常规间隙三网格与三档驱动力均通过", b,
     "S1：URV_S1_results_review_20261102；S2：URV_S2_completed_review_20261103_095422；"
     "S3：URV_S3_completed_review_20261103_172033。")

# ============================================================ 11 S4
rows = [["P", "5", "2.7691e−23", "PASS", "0.165%", "1.673", "0.094%", "通过"],
        ["P", "2.5", "2.7546e−23", "PASS", "—", "—", "—", "—"],
        ["P", "1.25", "2.7501e−23", "PASS", "—", "—", "—", "—"],
        ["T", "5", "3.6480e−24", "PASS", "1.328%", "1.496", "0.912%", "未通过"],
        ["T", "2.5", "3.5179e−24", "PASS", "—", "—", "—", "—"],
        ["T", "1.25", "3.4718e−24", "PASS", "—", "—", "—", "—"]]
b = table(["向", "dx", "K / m³", "单条", "中细变化", "阶 p", "GCI", "方向判定"], rows,
          43, 100, [44, 56, 148, 66, 106, 66, 86, 88], rh=40, hh=44, fs=10.5, hfs=10.5,
          aligns=["center", "center", "center", "center", "center", "center", "center", "center"],
          styles={(0, 4): {"color": NAVY}, (0, 7): {"color": GRN},
                  (3, 4): {"color": RED}, (3, 7): {"color": RED}, (3, 0): {"color": RED}})
b += t(43, 392, 760, 20,
       "几何 h30 / d80 / w120 / P240 nm，H = 70 nm；六条合计 4.61 h，无超时、无资源停止。",
       size=10, color=SUB, lh=1.3)

b += div(43, 424, 760, 96, "", bg=PANEL, border="1px solid " + LINE, r=4)
b += t(61, 432, 724, 20, "单条合格 ≠ 网格稳定（两张独立的门）", size=11, color=NAVY, bold=True, lh=1.3)
b += t(61, 456, 724, 56,
       "单条门：本条数值 / 几何 / 稳态。六条全过。<br>"
       "网格门：换细网格结果还变不变。横槽中细 1.328% 超 1%，<b>全阶段未过</b>。",
       size=10.5, color=TEXT, lh=1.5)

b += div(43, 540, 760, 76, "", bg=REDBG, border="1px solid " + RED, r=4)
b += t(61, 548, 724, 20, "处置", size=10.5, color=RED, bold=True, lh=1.3)
b += t(61, 570, 724, 40,
       "保留 FAIL · 不改 1% 门槛 · 不重跑 · 不补写完成文件 · 不据此判 V2 失败。",
       size=11, color=TEXT, lh=1.4)

b += div(823, 100, 414, 152, "", bg=GRNBG, border="1px solid #B6D3BE", r=4)
b += t(841, 110, 378, 20, "沿槽  通过", size=12.5, color=GRN, bold=True, lh=1.3)
b += t(841, 136, 378, 108,
       "中细 <b>0.165%</b>（门槛 1%）<br>GCI 0.094%　阶 p = 1.673<br>"
       "同一条规则下沿槽是干净的。", size=10.5, color=TEXT, lh=1.55)

b += div(823, 272, 414, 152, "", bg=REDBG, border="1px solid " + RED, r=4)
b += t(841, 282, 378, 20, "横槽  未通过", size=12.5, color=RED, bold=True, lh=1.3)
b += t(841, 308, 378, 108,
       "中细 <b style=\"font-size:15px;color:#B7332C\">1.328%</b>（门槛 1%）<br>"
       "GCI 0.912% 合格，<b>不能抵补前项</b><br>"
       "超门槛 0.328 个百分点。", size=10.5, color=TEXT, lh=1.55)

b += div(823, 444, 414, 112, "", bg=PANEL, border="1px solid " + LINE, r=4)
b += t(841, 452, 378, 20, "限制范围", size=10.5, color=BLUE, bold=True, lh=1.3)
b += t(841, 474, 378, 76,
       "受限：该薄间隙参考暂不能给 V2 作正式判定。<br>"
       "不受限：S1—S3 与历史 36 点结论仍按原范围有效。",
       size=10, color=TEXT, lh=1.5)

b += div(823, 572, 414, 44, t(16, 12, 382, 24,
       "S4_STAGE_ACCEPTED = false　·　S5 未启动", size=10, color=RED, bold=True, lh=1.3),
       bg=WHITE, border="1px solid " + LINE, r=3)
page("4 卡点", "薄间隙横槽网格未通过：1.328% 超过事先规定的 1%", b,
     "S4：URV_S4_completed_review_20261104_143205；run_id URV_S4_{P,T}_dx{5,2p5,1p25}_reuse_v1。")

# ============================================================ 12b OpenFOAM
b = t(43, 100, 1194, 18,
      "几何 h=75 / d=100 nm；24×48 μm 合成平均域、512 单元、不逐槽解析；μ=0.001 Pa·s；x 端表压 24/0 Pa；V=0（静态）",
      size=10, color=SUB, lh=1.3)

rows = [["C01", "V2", "横槽（槽沿 y，驱动 +x）", "2.18582e−18", "SDI_C01_v1_20261030_01"],
        ["C02", "V2", "沿槽（槽沿 x，驱动 +x）", "4.99873e−18", "SDI_C02_v1_1_20261030_01"],
        ["C03", "原公式", "横槽", "3.12872e−18", "SDI_C03_v1_2_20261030_01"],
        ["C04", "原公式", "沿槽", "1.15625e−17", "SDI_C04_v1_3_20261030_01"],
        ["GDI01", "V2", "横槽（经 grooveDarcy 真实动量源）", "2.18582e−18", "GDI01_v1_20261030_01"]]
b += table(["算例", "系数来源", "方向与设置", "出口流量 Q / m³·s⁻¹", "run_id"], rows,
           43, 122, [70, 96, 380, 280, 368], rh=40, hh=38, fs=10.5,
           aligns=["center", "center", "left", "center", "left"],
           styles={(4, 0): {"color": NAVY}, (0, 0): {"color": NAVY}, (1, 0): {"color": NAVY}})

b += div(43, 372, 384, 150, "", bg=PANEL, border="1px solid " + LINE, r=4)
b += t(61, 379, 348, 16, "结论 1　系数变化的影响", size=11, color=BLUE, bold=True, lh=1.3)
b += t(61, 400, 348, 26, "横槽 −30.14%", size=15, color=NAVY, bold=True, lh=1.3)
b += t(61, 428, 348, 26, "沿槽 −56.77%", size=15, color=NAVY, bold=True, lh=1.3)
b += t(61, 458, 348, 58,
       "同为 V2 替换原公式后，同压差下出口流量下降；降幅沿槽更大。",
       size=9.5, color=TEXT, lh=1.4)

b += div(448, 372, 384, 150, "", bg=PANEL, border="1px solid " + LINE, r=4)
b += t(466, 379, 348, 16, "结论 2　方向比随之改变", size=11, color=BLUE, bold=True, lh=1.3)
b += t(466, 400, 348, 26, "V2　沿/横 = 2.287", size=14, color=NAVY, bold=True, lh=1.3)
b += t(466, 428, 348, 26, "原公式　沿/横 = 3.696", size=14, color=RED, bold=True, lh=1.3)
b += t(466, 458, 348, 58,
       "原公式把方向性高估约 62%（3.696 / 2.287）；这是模型层面比值，非实测。",
       size=9.5, color=TEXT, lh=1.4)

b += div(853, 372, 384, 150, "", bg=GRNBG, border="1px solid #B6D3BE", r=4)
b += t(871, 379, 348, 16, "结论 3　真实动量源接入一致", size=11, color=GRN, bold=True, lh=1.3)
b += t(871, 400, 348, 26, "GDI01 / C01 = 1.000", size=14, color=GRN, bold=True, lh=1.3)
b += t(871, 428, 348, 88,
       "经 grooveDarcy 生成 K/D、走真实阻力源与压力—速度迭代，重现已接受结果，接入链自洽。",
       size=9.5, color=TEXT, lh=1.4)

b += div(43, 536, 1194, 64, "", bg=REDBG, border="1px solid #E6C6C2", r=4)
b += t(61, 543, 1158, 16, "这三条结论的边界（必须同时说）", size=11, color=RED, bold=True, lh=1.3)
b += t(61, 561, 1158, 34,
       '模型用<b>输入的等效阻力</b>，没有逐条解析沟槽；它是程序/接口核验，不是公式准确性证据，也不是挤压或载荷验证。'
       '固定压差下两组系数的压力线几乎重合，所以<b>不能</b>靠压力场判断哪组 K 更准。',
       size=9.3, color=TEXT, lh=1.38)

b += t(43, 608, 1194, 58,
       '与第 12 页不能混：本页方向比 2.287 来自<b>输入系数</b>（h75/d100、未解析沟槽）；'
       '第 12 页 2.515 来自<b>显式沟槽计算</b>（h60/d80、逐槽解析）。两者条件不同，相差约 10%，'
       '<b>不可</b>当作同条件误差比较。',
       size=9.3, color=NAVY, lh=1.45)

page("3 本周验证 · OpenFOAM", "OpenFOAM 等效阻力接入：三条结论与它们的边界", b,
     "C01—C04 与 GDI01 均为 2026-10-30 既有计算；本周只做身份与证据核对。")

# ============================================================ 12 boundary
can = [["C1", "已采样条件下槽深对两方向影响不同", "表 5：3.55 / 2.13 / 1.39；K<sub>xx</sub> &lt; 4%"],
       ["C2", "36 个方向点上原公式全部高估导度", "表 6：+10.30→+204.85%；+8.11→+54.19%"],
       ["C3", "偏差改变各向异性与重建流向", "表 7：A 2.21 对 3.70；流向差 9.20°"],
       ["C4", "V2 压低整体最坏偏差但局部失效", "表 8：10.5% / 18.7%；反例 +2.35"],
       ["T1", "理想 Stokes 下原公式给非严格上界", "附录 E：不给幅度、不给符号"]]
cnt = [["P1", "V2 对未参与拟合条件有预测能力", "缺合格新几何 + 正式模型比较"],
       ["P2", "V2 在薄间隙同样可靠", "缺 S4 横槽合格 + S5 驱动力控制"],
       ["A1", "提高压印压力 / 载荷 / 缩短时间", "缺独立挤压或实验参照、耗散分项"],
       ["—", "任何实验或物理验证", "全文仅数值验证"],
       ["—", "投稿就绪、严格误差界", "reference_qualified = false"]]
b = div(43, 98, 588, 26, t(0, 2, 588, 22, "可以保留（有证据、有边界）", size=12.5, color=BLUE, bold=True, lh=1.3))
b += table(["", "结论", "证据"], can, 43, 128, [40, 250, 298], rh=56, hh=32, fs=10.5, hfs=10,
           aligns=["center", "left", "left"],
           styles={(0, 0): {"color": BLUE}, (1, 0): {"color": BLUE}, (2, 0): {"color": BLUE},
                   (3, 0): {"color": BLUE}, (4, 0): {"color": BLUE}})
b += div(649, 98, 588, 26, t(0, 2, 588, 22, "不能声称（尚无合格证据）", size=12.5, color=RED, bold=True, lh=1.3))
b += table(["", "主张", "缺什么"], cnt, 649, 128, [40, 250, 298], rh=56, hh=32, fs=10.5, hfs=10,
           aligns=["center", "left", "left"], head=RED,
           styles={(0, 0): {"color": RED}, (1, 0): {"color": RED}, (2, 0): {"color": RED}})

b += div(43, 456, 1194, 60, "", bg=NAVY, r=4)
b += t(64, 466, 1152, 40,
       "reference_qualified = false　·　MODEL_COMPARISON = NOT_EVALUATED　·　"
       "physical_validation = NOT_EVALUATED　·　submission_ready = false",
       size=10.5, color=WHITE, bold=True, lh=1.4)

rows3 = [["去掉「5 nm 参考」", "偏差变成绝对误差 → 立刻越界"],
         ["去掉「已采样」", "结论变成全域规律 → 未采样 2 格无法支撑"],
         ["去掉「回顾性」", "V2 变成预测模型 → 无盲测证据"]]
b += table(["若省略哪条限定", "后果"], rows3, 43, 534, [300, 894],
           rh=32, hh=32, fs=11, aligns=["left", "left"])
page("5 证据边界", "能说什么、不能说什么", b,
     "对照表：PAPER1_claim_evidence_matrix_20261104/REPORT.md（C1—C4、T1、P1/P2、A1、I1）。")

# ============================================================ 13 questions
b = div(43, 98, 588, 292, "", bg=PANEL, border="1px solid " + LINE, r=4)
b += badge(61, 110, 68, 24, "问题 1")
b += t(61, 142, 552, 26, "论文主张放在哪里", size=16, color=NAVY, bold=True, lh=1.3)
b += table(["", "路线", "覆盖范围", "还需补什么"], 
           [["A", "已有样本中的偏差、方向性、有边界修正", "36 点 / 5 nm 参考", "无（保留全部限定即可）"],
            ["B", "把「对新条件的独立预测」作为主要贡献", "须跨出已采样范围", "薄间隙参考 + 参考资格 + 模型比较"]],
           61, 176, [26, 210, 140, 168], rh=52, hh=26, fs=9.5, hfs=9,
           aligns=["center", "left", "left", "left"],
           styles={(0, 0): {"color": GRN}, (1, 0): {"color": RED}})
b += hr(61, 314, 552, LINE, 1)
b += t(61, 322, 552, 56,
       "代价：A 可即进入写作收尾；B 至少再跨两个阶段 —— 差别不在工作量，而在论文的<b>贡献类型</b>"
       "（描述 vs 预测）。", size=10, color=SUB, lh=1.5)

b += div(649, 98, 588, 292, "", bg=PANEL, border="1px solid " + LINE, r=4)
b += badge(667, 110, 68, 24, "问题 2")
b += t(667, 142, 552, 26, "薄间隙横槽是否继续投", size=16, color=NAVY, bold=True, lh=1.3)
b += table(["", "选择", "立即动作", "论文写法"],
           [["继续", "先定补证方案与资源，再授权计算", "0.625 nm 已备；需另批机时", "可写薄间隙结论"],
            ["收窄", "论文明确不覆盖最薄间隙", "不再投入机时", "1.328% 写入限制章节"]],
           667, 176, [48, 206, 160, 130], rh=52, hh=26, fs=9.5, hfs=9,
           aligns=["center", "left", "left", "left"],
           styles={(0, 0): {"color": NAVY}, (1, 0): {"color": NAVY}})
b += hr(667, 314, 552, LINE, 1)
b += t(667, 322, 552, 56,
       "两条路都不改 1% 门槛、不删历史 FAIL；区别只在论文的<b>覆盖范围</b>与后续机时投入。",
       size=10, color=SUB, lh=1.5)

rows = [["已完成且可用", "S1 / S2 / S3", "平板 0.173%、网格 0.203/0.744%、驱动力 L 8.3e−8", "可直接写入"],
        ["已有结论", "历史 18 几何 / 36 点", "原公式全高估；V2 10.5% / 18.7%", "带限定写入"],
        ["已完成但未过", "S4 六条", "横槽中细 1.328% &gt; 1%", "只作限制条款"],
        ["只准备未计算", "0.625 nm 补证", "15 项软件测试通过，无新流场", "不可作证据"],
        ["只证明接口", "OpenFOAM C01—C04 / GDI01", "静态接入一致（2026-10-30 既有）", "不可作准确性"]]
b += table(["状态", "对应工作", "关键数字", "可否进论文"], rows, 43, 396,
           [150, 250, 500, 294], rh=30, hh=30, fs=10,
           aligns=["left", "left", "left", "left"],
           styles={(0, 3): {"color": GRN}, (1, 3): {"color": GRN},
                   (2, 3): {"color": RED}, (3, 3): {"color": RED}, (4, 3): {"color": RED}})

b += div(43, 588, 1194, 50, "", bg=LIGHT, r=4)
b += div(43, 588, 5, 50, "", bg=NAVY)
b += t(64, 595, 1152, 36,
       "建议：先按 A 把局部输运主线讲完整；挤压压力、载荷、完整压印过程作为应用方向讨论，"
       "当前无独立验证，不作为已实现成果。", size=11, color=NAVY, bold=True, lh=1.35)

b += t(43, 650, 1194, 14,
       "AI 参与：代码、检查与材料整理有 AI 辅助；本人已理解核对与仍需人工复核的部分会分开说明。",
       size=9, color=MUT, lh=1.2)
page("5 请您裁定", "两个问题", b, "两个问题均为方向性裁定，不涉及本轮新增计算。")

# ============================================================ render
CSS = """
@page { size:1280px 720px; margin:0; }
* { margin:0; padding:0; }
body { font-family:"Noto Sans CJK SC",sans-serif; color:%s; }
.page { position:relative; width:1280px; height:720px; overflow:hidden;
        background:#fff; page-break-after:always; }
table { border-spacing:0; }
td, th { vertical-align:middle; }
img { display:block; }
sup { font-size:0.66em; vertical-align:0.45em; line-height:0; }
b { font-weight:700; }
""" % TEXT

doc = ('<!DOCTYPE html><html><head><meta charset="utf-8"><style>%s</style></head>'
       '<body>%s</body></html>' % (CSS, "".join(P)))
with open(os.path.join(HERE, "briefing_v3.html"), "w", encoding="utf-8") as f:
    f.write(doc)
HTML(string=doc, base_url=HERE).write_pdf(OUT)
print("pdf:", OUT, "pages:", len(P))
