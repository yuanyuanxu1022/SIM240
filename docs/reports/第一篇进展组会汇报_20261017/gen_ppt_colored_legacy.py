#!/usr/bin/env python3
"""生成第一篇进展组会汇报 PPT（10 页，学术蓝白风，简洁·有图·有结论）"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
import copy

# ---------- 配色 ----------
BLUE    = RGBColor(0x1E, 0x4F, 0xA8)   # 主蓝
NAVY    = RGBColor(0x0E, 0x3F, 0x8C)   # 藏蓝
LBLUE   = RGBColor(0xF0, 0xF5, 0xFC)   # 浅蓝底
LBLUE2  = RGBColor(0xE8, 0xEF, 0xF8)
MBLUE   = RGBColor(0x3D, 0x7B, 0xD9)   # 中蓝
RED     = RGBColor(0xD9, 0x53, 0x4F)   # 警示红
TEXT    = RGBColor(0x1A, 0x22, 0x30)
SUB     = RGBColor(0x4A, 0x55, 0x68)
FAINT   = RGBColor(0x8B, 0x97, 0xA8)
LINE    = RGBColor(0xD6, 0xDC, 0xE5)
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
PALEB   = RGBColor(0xBF, 0xD0, 0xEA)

FONT = "微软雅黑"

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
TOTAL = 10

def set_ea(run, name=FONT):
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {})
        rPr.append(ea)
    ea.set('typeface', name)

def add_text(slide, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
             space_after=0, line_spacing=1.15, wrap=True):
    """runs: str 或 [(text, size, color, bold), ...]（可含多段列表）"""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = 0; tf.margin_right = 0; tf.margin_top = 0; tf.margin_bottom = 0
    if isinstance(runs, str):
        runs = [(runs, 16, TEXT, False)]
    first = True
    for item in runs:
        text, size, color, bold = item
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.space_after = Pt(space_after)
        if line_spacing: p.line_spacing = line_spacing
        r = p.add_run(); r.text = text
        r.font.size = Pt(size); r.font.color.rgb = color; r.font.bold = bold
        r.font.name = FONT; set_ea(r)
    return tb

def add_rect(slide, x, y, w, h, fill, line_color=None, radius=None):
    shp_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shp = slide.shapes.add_shape(shp_type, Inches(x), Inches(y), Inches(w), Inches(h))
    if radius:
        try: shp.adjustments[0] = radius
        except Exception: pass
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line_color is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line_color; shp.line.width = Pt(1)
    shp.shadow.inherit = False
    return shp

def add_pic(slide, path, x, y, w=None, h=None):
    return slide.shapes.add_picture(path, Inches(x), Inches(y),
                                    Inches(w) if w else None, Inches(h) if h else None)

def header(slide, title, num):
    """内容页统一头部：竖条 + 标题 + 页脚"""
    add_rect(slide, 0.55, 0.42, 0.09, 0.52, BLUE)
    add_text(slide, 0.78, 0.40, 10.5, 0.6, [(title, 26, NAVY, True)])
    add_rect(slide, 0.55, 1.06, 12.23, 0.016, LINE)
    # 页脚
    add_text(slide, 0.55, 7.12, 6, 0.3, [("SIM240 · 纳米压印沟槽 DNS 输运标定", 10, FAINT, False)])
    add_text(slide, 11.9, 7.12, 0.9, 0.3, [(f"{num:02d} / {TOTAL}", 11, NAVY, True)], align=PP_ALIGN.RIGHT)

ASSETS = "/home/dell/yuanyuanxu/SIM240/docs/reports/第一篇进展组会汇报_20261017/assets"

# ================= P1 封面 =================
s = prs.slides.add_slide(BLANK)
add_rect(s, 0, 0, 13.333, 0.95, NAVY)
add_text(s, 0.6, 0.30, 8, 0.4, [("SIM240 · 纳米压印方向性输运 · 第一篇进展汇报", 15, PALEB, True)])
add_text(s, 10.2, 0.32, 2.6, 0.4, [("2026-10-17 组会", 12, PALEB, False)], align=PP_ALIGN.RIGHT)
add_text(s, 0.9, 2.05, 11.53, 1.9, [
    ("纳米压印沟槽输运的 DNS 定量标定：", 33, NAVY, True),
    ("Jain 型闭合的误差与修正", 33, NAVY, True),
], align=PP_ALIGN.CENTER, line_spacing=1.3)
add_rect(s, 6.42, 4.28, 0.5, 0.045, BLUE)
add_text(s, 2.0, 4.55, 9.33, 0.85, [
    ("Directional transport in nanoimprint grooves: error quantification and correction of the Jain-type closure", 13.5, FAINT, False),
], align=PP_ALIGN.CENTER, line_spacing=1.4)
add_text(s, 2.0, 5.45, 9.33, 0.45, [
    ("数据工作已全部完成 —— 误差表 · 设计结论 · 修正公式齐备", 17, SUB, False),
], align=PP_ALIGN.CENTER)
add_rect(s, 0, 6.42, 13.333, 0.62, BLUE)
add_text(s, 0.6, 6.55, 12.1, 0.4, [
    ("48 档 DNS 全部通过验证 ｜ 公式误差 +12%~+205% ｜ 修正公式留出考场 6/6", 15.5, WHITE, True),
], align=PP_ALIGN.CENTER)
add_rect(s, 0, 7.04, 13.333, 0.46, LBLUE)
add_text(s, 0.6, 7.12, 6, 0.3, [("SIM240 课题组 · 组会汇报", 11, SUB, False)])
add_text(s, 10.2, 7.12, 2.5, 0.3, [("2026 年 10 月 17 日", 11, SUB, False)], align=PP_ALIGN.RIGHT)

# ================= P2 一页结论 =================
s = prs.slides.add_slide(BLANK)
header(s, "今天只说四个答案", 2)
add_rect(s, 0.55, 1.32, 2.9, 5.62, NAVY)
add_text(s, 0.85, 1.75, 2.35, 1.6, [
    ("一页结论", 27, WHITE, True),
    ("先给答案，", 15, PALEB, False),
    ("再给证据", 15, PALEB, False),
], line_spacing=1.35)
add_text(s, 0.85, 5.6, 2.35, 1.2, [
    ("证据页：", 13, PALEB, True),
    ("P5 误差表 · P6 设计结论", 12, PALEB, False),
    ("P7 修正 · P8 张量性", 12, PALEB, False),
], line_spacing=1.5)
concl = [
    ("01", "公式错多少", "Jain 型闭合（行业在用）全面高估通流能力，沿槽最多 +154%、跨槽最多 +49%，槽越深错越多 → 公式必须标定后才能用于设计", "+154%", RED),
    ("02", "该控制什么", "想让液体横跨沟槽流得更快，唯一有效旋钮是减小间隙 h；加深沟槽几乎无效，深槽容积 82% 是死空间 → 工艺上优先保证间隙均匀", "η=0.18", RED),
    ("03", "怎么修", "两个无量纲修正因子，在从未见过的槽深 d=75 nm 上 6/6 通过留出验证：沿槽误差 +66~99%→±17%，跨槽 +34~41%→±4% → 交付可用的改进公式", "6/6", NAVY),
    ("04", "顺带两证", "K 是合格张量（斜槽旋转律 6/6 命中，流向预测不偏）；K 与胶黏度无关（换 15 倍稠的胶差 0.0006%）→ 结论对所有牛顿胶通用", "0.0006%", NAVY),
]
y = 1.32
for num, t, d, big, bcol in concl:
    add_rect(s, 3.72, y, 9.06, 1.30, LBLUE2, LINE)
    add_rect(s, 3.95, y+0.24, 0.62, 0.62, BLUE)
    add_text(s, 3.95, y+0.335, 0.62, 0.45, [(num, 17, WHITE, True)], align=PP_ALIGN.CENTER)
    add_text(s, 4.78, y+0.13, 6.35, 1.06, [
        (t, 17.5, NAVY, True),
        (d, 12.5, SUB, False),
    ], line_spacing=1.18)
    add_text(s, 11.25, y+0.30, 1.35, 0.8, [(big, 17, bcol, True)], align=PP_ALIGN.RIGHT)
    y += 1.44

# ================= P3 背景问题 =================
s = prs.slides.add_slide(BLANK)
header(s, "问题：行业正在用的公式，从未被定量验证过", 3)
# 左侧示意图（矩形拼装）
add_rect(s, 0.55, 1.35, 6.3, 5.5, LBLUE, LINE)
# 模具（顶）
add_rect(s, 1.0, 1.75, 2.2, 1.05, MBLUE)          # 凸台左
add_rect(s, 3.2, 1.35, 2.4, 1.45, MBLUE)          # 凸台中（槽顶）
add_rect(s, 5.6, 1.75, 0.8, 1.05, MBLUE)          # 凸台右
add_rect(s, 1.0, 2.80, 5.4, 0.30, NAVY)           # 模具主体
# 沟槽内的液
add_rect(s, 3.2, 2.80, 2.4, 0.75, LBLUE2, None)
# 液膜
add_rect(s, 1.0, 3.55, 5.4, 0.55, RGBColor(0xBF,0xD7,0xF0), None)
# 基板
add_rect(s, 0.85, 4.10, 5.7, 0.42, NAVY)
add_rect(s, 0.85, 5.30, 5.7, 0.28, TEXT)
# 标注
add_text(s, 1.0, 4.55, 5.5, 1.9, [
    ("h = 75 nm  残余间隙（压印中间阶段）", 12.5, TEXT, False),
    ("d = 100 nm  沟槽深度", 12.5, TEXT, False),
    ("w = 120 nm  槽宽（P = 240 nm 周期）", 12.5, TEXT, False),
    ("沿槽流 ↔ 顺，跨槽流 ↕ 难 —— 方向性阻力决定填充与缺陷", 12.5, NAVY, True),
], line_spacing=1.5)
# 右侧文字
add_text(s, 7.15, 1.5, 5.6, 3.1, [
    ("纳米压印（J-FIL）", 16, NAVY, True),
    ("滴胶 → 模具下压 → 液体填槽；沿槽快、跨槽慢的方向性决定填充时间与缺陷。", 13.5, SUB, False),
    ("行业做法", 16, NAVY, True),
    ("Jain et al. 2017（Microelectron. Eng. 173）用各向异性渗透率算压印流动，数学上就是局部立方律（条纹平均）。", 13.5, SUB, False),
    ("问题", 16, NAVY, True),
    ("该公式从未在“矩形直角槽 + 有限间隙”上被定量验证——原论文只与实验定性比较。", 13.5, SUB, False),
], line_spacing=1.35, space_after=6)
add_rect(s, 7.15, 4.85, 5.6, 1.15, RGBColor(0xFB,0xEC,0xEA), None)
add_text(s, 7.4, 5.0, 5.15, 0.9, [
    ("我们做什么", 14.5, RED, True),
    ("OpenLB 显式沟槽 DNS，定量标定其误差并给出修正。基准几何 h=75/d=100 沿槽方向公式高估 +146% —— 正在用的公式可能把填充速度算错 2.5 倍。", 12.5, TEXT, False),
], line_spacing=1.25)

# ================= P4 方法验证 =================
s = prs.slides.add_slide(BLANK)
header(s, "方法：36 档 DNS 与五重验证链", 4)
steps = [
    ("1", "几何显式建模", "真实沟槽（凸台/槽/台阶）直接画进网格，不做任何等效化"),
    ("2", "六项门禁", "质量漂移 <1e-10 · 密度偏差 ≤1e-6 · 马赫数 <0.05 · 收敛窗口 · 截面一致性 · 体积守恒"),
    ("3", "窗口收敛", "1000 步窗口 std≤1e-6、span≤5e-6，全部档位自动收敛"),
    ("4", "网格复核", "dx 5→2.5 nm 复算，K 变化 0.3–2.2%，量级符合预期"),
    ("5", "新旧对账", "重叠档与历史 PASS 数据逐位一致（同一把尺子）"),
]
y = 1.35
for num, t, d in steps:
    add_rect(s, 0.55, y, 7.6, 0.94, WHITE, LINE)
    add_rect(s, 0.78, y+0.21, 0.52, 0.52, BLUE)
    add_text(s, 0.78, y+0.30, 0.52, 0.35, [(num, 16, WHITE, True)], align=PP_ALIGN.CENTER)
    add_text(s, 1.52, y+0.10, 6.5, 0.78, [
        (t, 15, NAVY, True),
        (d, 11.5, SUB, False),
    ], line_spacing=1.15)
    y += 1.07
# 右侧大数字
add_rect(s, 8.45, 1.35, 4.33, 3.2, NAVY)
add_text(s, 8.45, 1.75, 4.33, 1.1, [("48", 54, WHITE, True)], align=PP_ALIGN.CENTER)
add_text(s, 8.45, 2.95, 4.33, 0.5, [("档 DNS 全部 PASS", 17, WHITE, True)], align=PP_ALIGN.CENTER)
add_text(s, 8.7, 3.5, 3.85, 1.0, [
    ("平板极限误差 0.03%", 13, PALEB, False),
    ("Ma < 4e-7 · 质量漂移 ≤1e-11", 13, PALEB, False),
], align=PP_ALIGN.CENTER, line_spacing=1.5)
add_rect(s, 8.45, 4.75, 4.33, 2.0, LBLUE2, LINE)
add_text(s, 8.7, 4.95, 3.85, 1.7, [
    ("判断", 14.5, NAVY, True),
    ("数据可信度由五重验证保证，全部数字经独立交叉复核（0 处不一致），可直接写进论文方法节。", 12.5, SUB, False),
], line_spacing=1.3)

# ================= P5 误差地图 =================
s = prs.slides.add_slide(BLANK)
header(s, "主结果一：公式全面高估，槽越深错越多", 5)
add_rect(s, 0.55, 1.32, 12.23, 0.52, LBLUE, None)
add_text(s, 0.8, 1.42, 11.7, 0.35, [("模型到底错多少？—— 9 种几何 × 2 方向，误差全部为正（= 模型全部高估）", 14.5, NAVY, True)])
add_pic(s, f"{ASSETS}/error_map.png", 0.55, 2.0, 7.9)
add_rect(s, 8.75, 2.0, 4.03, 4.75, WHITE, LINE)
add_text(s, 9.0, 2.2, 3.55, 4.4, [
    ("误差表（E = (模型−DNS)/DNS）", 15, NAVY, True),
    ("沿槽：+10.3% ~ +154.2%", 13.5, TEXT, False),
    ("跨槽：+11.7% ~ +49.1%", 13.5, TEXT, False),
    ("最狠一格：h=50/d=100 沿槽", 12.5, SUB, False),
    ("+154%", 30, RED, True),
    ("各向异性比也被高估：模型 7.26 vs DNS 3.92（+85%）", 12.5, SUB, False),
    ("判断", 14, NAVY, True),
    ("误差随槽深单调放大、随间隙减小而增大——系统性的、有明确规律的，修正有清晰靶子。", 12.5, SUB, False),
], line_spacing=1.3, space_after=7)

# ================= P6 设计结论 =================
s = prs.slides.add_slide(BLANK)
header(s, "主结果二：想让液体横着流快，只有减 h 一条路", 6)
add_pic(s, f"{ASSETS}/efficiency_map.png", 0.55, 1.32, 7.9)
add_rect(s, 8.75, 1.32, 4.03, 3.32, WHITE, LINE)
add_text(s, 9.0, 1.5, 3.55, 3.0, [
    ("等体积效率（右图）", 14.5, NAVY, True),
    ("η⟂ = 0.18（h50/d100）：深槽容积 82% 对跨槽是死空间", 12.5, SUB, False),
    ("弹性系数（左下图数据）", 14.5, NAVY, True),
    ("Ŝ_d^T ≈ 0.001–0.05：槽深翻倍，跨槽通流几乎不动", 12.5, SUB, False),
    ("Ŝ_h^T ≈ 2.7–2.8：间隙是跨槽的绝对主导", 12.5, SUB, False),
    ("→ 加深槽“白挖”，减 h 才是唯一有效旋钮。", 12.5, NAVY, True),
], line_spacing=1.35, space_after=8)
add_rect(s, 0.55, 4.85, 5.95, 1.85, WHITE, LINE)
add_text(s, 0.85, 5.0, 5.4, 1.55, [
    ("加深沟槽对跨槽几乎无用", 15, NAVY, True),
    ("d 的弹性系数 ≈0：槽深翻倍、跨槽通流几乎不动；h 的弹性系数 ≈2.7–2.8、稳定主导。", 12, SUB, False),
], line_spacing=1.3)
add_rect(s, 6.85, 4.85, 5.93, 1.85, WHITE, LINE)
add_text(s, 7.15, 5.0, 5.35, 1.55, [
    ("深槽容积大量是死空间", 15, NAVY, True),
    ("等体积效率 η⟂=0.18：槽内 82% 容积对跨槽无贡献；η∥=0.60–0.95，沿槽好一些。", 12, SUB, False),
], line_spacing=1.3)
add_text(s, 0.55, 6.72, 12.2, 0.35, [
    ("给工艺的直接建议：优先控制间隙均匀性，而不是改槽深设计。", 13.5, BLUE, True),
])

# ================= P7 修正公式（高潮） =================
s = prs.slides.add_slide(BLANK)
header(s, "主结果三：修正公式通过留出考场 —— 6/6", 7)
add_rect(s, 0.55, 1.32, 7.6, 0.5, NAVY)
add_text(s, 0.8, 1.42, 7.2, 0.35, [("留出考场：d=75 nm（从未参与拟合）× 3 间隙 × 2 方向", 14, WHITE, True)])
add_pic(s, f"{ASSETS}/correction_validation.png", 0.55, 1.95, 7.6)
add_rect(s, 8.45, 1.32, 4.33, 5.42, LBLUE2, LINE)
add_text(s, 8.72, 1.52, 3.8, 5.1, [
    ("6 / 6 全部通过", 30, NAVY, True),
    ("判据提前定死：沿槽 ≤±20%、跨槽 ≤±10%", 12, SUB, False),
    ("两个修正因子", 15.5, NAVY, True),
    ("沿槽：F∥ = 1/(1+1.72(d/H_ref)^1.80)", 12.5, TEXT, False),
    ("跨槽：F⟂ = 1/(1+0.53(d/w)^0.83)", 12.5, TEXT, False),
    ("误差压降", 15.5, NAVY, True),
    ("沿槽 +66~99% → ±17%", 13, TEXT, False),
    ("跨槽 +34~41% → ±4%", 13, TEXT, False),
    ("适用范围（18 档外推验证）", 14, NAVY, True),
    ("跨槽：h∈[50,125]、d/w≤1 内 ±10%；沿槽：d/w≤0.83 内 ±20%；下界 h=50 nm", 11.5, SUB, False),
    ("判断：论文第三层贡献闭环——给行业公式补上“经验证的修正”与失效边界。", 12.5, NAVY, True),
], line_spacing=1.28, space_after=6)

# ================= P8 张量性 + 黏度 =================
s = prs.slides.add_slide(BLANK)
header(s, "顺带两个证明：K 是张量、且与胶水无关", 8)
add_pic(s, f"{ASSETS}/tensor_validation.png", 0.7, 1.45, 4.7)
add_rect(s, 5.75, 1.45, 7.03, 2.4, WHITE, LINE)
add_text(s, 6.05, 1.62, 6.45, 2.1, [
    ("K 是合格的二阶张量", 16, NAVY, True),
    ("斜槽 30°/45°/60° × 2 几何：旋转律 K(θ)=K∥cos²θ+K⟂sin²θ 与流向偏转角 tanφ=(K⟂/K∥)tanθ 全部 6/6 命中（<1e-4%）。", 12.5, SUB, False),
    ("→ Jain 把 kxx/kyy 当张量用是对的：流向预测不偏，偏的只是幅值。", 12.5, TEXT, False),
], line_spacing=1.3)
add_rect(s, 5.75, 4.05, 7.03, 2.72, WHITE, LINE)
add_text(s, 6.05, 4.22, 6.45, 2.4, [
    ("K 与胶水黏度无关（实测）", 16, NAVY, True),
    ("换 15 倍稠的胶（μ=15 mPa·s，mr-NIL210 量级）：K 变化 0.0006%，流量恰好慢 15 倍。", 12.5, SUB, False),
    ("→ 误差表与修正公式对所有牛顿胶通用，不需要重跑。", 12.5, TEXT, False),
    ("锚点：45° 档偏转角 DNS 24.34° = 理论 24.34°（四位有效数字）", 12, FAINT, False),
], line_spacing=1.3)

# ================= P9 下一步 =================
s = prs.slides.add_slide(BLANK)
header(s, "下一步：从“算”转向“写”", 9)
tasks = [
    ("查新（进行中）", "四项指令已打包：Jain 引文追踪 / 专项检索 / WoS 人工核查 / 独立交叉。结论只决定“首次”措辞，不影响工作本身。", "本周"),
    ("论文初稿", "骨架与素材库已就绪，36 档数据 + 验收报告 + 代码审查报告全部归档，随时开工。", "1–2 周"),
    ("投稿", "体量匹配的期刊档：3 区稳、2 区冲（数据+分析+修正三层贡献支撑）。", "2–3 周"),
]
y = 1.45
for t, d, w in tasks:
    add_rect(s, 0.55, y, 7.0, 1.62, WHITE, LINE)
    add_rect(s, 0.80, y+0.18, 0.52, 0.52, BLUE)
    add_text(s, 0.80, y+0.27, 0.52, 0.35, [("✓", 15, WHITE, True)], align=PP_ALIGN.CENTER)
    add_text(s, 1.52, y+0.14, 4.70, 1.36, [
        (t, 15.5, NAVY, True),
        (d, 12, SUB, False),
    ], line_spacing=1.25)
    add_text(s, 6.35, y+0.14, 1.1, 0.4, [(w, 12.5, BLUE, True)], align=PP_ALIGN.RIGHT)
    y += 1.78
add_rect(s, 8.0, 1.45, 4.78, 5.3, NAVY)
add_text(s, 8.3, 1.7, 4.2, 4.8, [
    ("时间线", 16, WHITE, True),
    ("今天", 15, WHITE, True),
    ("数据工作 100% 收官（36 档）", 12.5, PALEB, False),
    ("本周", 15, WHITE, True),
    ("查新结论 + 初稿第一节", 12.5, PALEB, False),
    ("1–2 周", 15, WHITE, True),
    ("全文初稿，组会再汇报", 12.5, PALEB, False),
    ("2–3 周", 15, WHITE, True),
    ("老师修改意见 + 投稿", 12.5, PALEB, False),
    ("判断：瓶颈已从“能不能算”变成“怎么写好”。", 13, RGBColor(0xFF,0xE0,0x8A), True),
], line_spacing=1.4, space_after=7)

# ================= P10 结束 =================
s = prs.slides.add_slide(BLANK)
add_rect(s, 0, 0, 13.333, 7.5, WHITE)
add_rect(s, 0, 0, 13.333, 0.18, NAVY)
add_text(s, 1.0, 1.6, 11.33, 1.6, [
    ("48", 72, NAVY, True),
], align=PP_ALIGN.CENTER)
add_text(s, 1.0, 3.25, 11.33, 0.6, [
    ("48 档 DNS ｜ 修正考场 6/6 ｜ 张量验证 6/6", 20, SUB, False),
], align=PP_ALIGN.CENTER)
add_rect(s, 6.42, 4.25, 0.5, 0.045, BLUE)
add_text(s, 1.0, 4.6, 11.33, 0.8, [
    ("误差 +154% → 修正 ±17%：第一篇的答案都在这里", 24, NAVY, True),
], align=PP_ALIGN.CENTER)
add_text(s, 1.0, 5.55, 11.33, 0.5, [
    ("谢谢！期待老师的意见——下一步：查新结论 + 论文初稿", 15, SUB, False),
], align=PP_ALIGN.CENTER)
add_rect(s, 0, 7.04, 13.333, 0.46, LBLUE)
add_text(s, 0.6, 7.12, 6, 0.3, [("SIM240 课题组 · 组会汇报", 11, SUB, False)])
add_text(s, 10.2, 7.12, 2.5, 0.3, [("2026 年 10 月 17 日", 11, SUB, False)], align=PP_ALIGN.RIGHT)

OUT = "/home/dell/yuanyuanxu/SIM240/docs/reports/第一篇进展组会汇报_20261017/第一篇进展组会汇报_20261017.pptx"
prs.save(OUT)
print("saved:", OUT, "slides:", len(prs.slides.__iter__.__self__._sldIdLst))
