# -*- coding: utf-8 -*-
"""
生成《第一篇进展组会汇报》简洁同款版（复刻《纳米管道初步结果.pptx》版式类型）

版式规则（与参考 PPT 同源）：
  - 母版/主题直接取自参考 PPT（白底、Calibri、标题 44pt 左对齐、正文圆点列表）
  - 标题一律名词式（难点 / 计算方法 / 初步结果 / 下一步），不用口号式
  - 不用色条、卡片、大数字等装饰；结果页 = 标题 + 大图 + 图旁短要点
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = "/home/dell/yuanyuanxu/SIM240/.workbuddy/tmp/SIM240_template.pptx"
ASSETS = os.path.join(HERE, "assets")
OUT = os.path.join(HERE, "第一篇进展组会汇报_20261017.pptx")

GRAY_FILL = RGBColor(0xD9, 0xD9, 0xD9)
GRAY_LINE = RGBColor(0x7F, 0x7F, 0x7F)
DARK = RGBColor(0x40, 0x40, 0x40)


# ---------------------------------------------------------------- 基础工具
def title_slide(prs, title, subtitle_lines):
    s = prs.slides.add_slide(prs.slide_layouts[0])
    s.shapes.title.text = title
    sub = s.placeholders[1]
    tf = sub.text_frame
    tf.clear()
    for i, line in enumerate(subtitle_lines):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.add_run().text = line
    return s


def content_slide(prs, title, bullets, size=20):
    """bullets: [(lead, rest)]，lead 加粗；lead 为空则整行普通"""
    s = prs.slides.add_slide(prs.slide_layouts[1])
    s.shapes.title.text = title
    body = s.placeholders[1]
    tf = body.text_frame
    tf.clear()
    for i, (lead, rest) in enumerate(bullets):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if lead:
            r1 = para.add_run()
            r1.text = lead
            r1.font.bold = True
            r1.font.size = Pt(size)
        r2 = para.add_run()
        r2.text = rest
        r2.font.size = Pt(size)
    return s


def textbox(slide, x, y, w, h, blocks, size=17, bold_first=False, line_spacing=1.15):
    """blocks: [str 或 (lead, rest)]"""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    for i, b in enumerate(blocks):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.line_spacing = line_spacing
        para.space_after = Pt(6)
        lead, rest = (b, "") if isinstance(b, str) else b
        if lead:
            r = para.add_run()
            r.text = lead
            r.font.size = Pt(size)
            r.font.bold = bold_first or (rest != "")
            r.font.color.rgb = DARK
        if rest:
            r2 = para.add_run()
            r2.text = rest
            r2.font.size = Pt(size)
            r2.font.color.rgb = DARK
    return tb


def picture_fit(slide, filename, x, y, max_w, max_h):
    """按比例缩放塞进给定框，返回实际尺寸"""
    from PIL import Image
    path = os.path.join(ASSETS, filename)
    iw, ih = Image.open(path).size
    ar = iw / ih
    w, h = max_w, max_w / ar
    if h > max_h:
        h, w = max_h, max_h * ar
    slide.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))
    return w, h


def fig_caption(slide, x, y, w, text, size=13):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(0.56))
    p = tb.text_frame.paragraphs[0]
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
    return tb


def gray_rect(slide, x, y, w, h):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = GRAY_FILL
    sh.line.color.rgb = GRAY_LINE
    sh.line.width = Pt(1)
    sh.shadow.inherit = False
    return sh


def thin_line(slide, x1, y1, x2, y2, color=None):
    from pptx.enum.shapes import MSO_CONNECTOR
    ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                                    Inches(x2), Inches(y2))
    ln.line.color.rgb = color or GRAY_LINE
    ln.line.width = Pt(1.25)
    return ln


# ---------------------------------------------------------------- 各页内容
def build():
    prs = Presentation(TEMPLATE)
    assert len(prs.slides) == 0

    # ---------- P1 封面 ----------
    title_slide(prs, "纳米压印沟槽输运的初步结果", [
        "DNS 定量标定 Jain 型闭合的误差与修正",
        "SIM240 课题组 ｜ 2026 年 10 月 17 日组会",
    ])

    # ---------- P2 主要结论 ----------
    content_slide(prs, "主要结论", [
        ("公式错多少：", "Jain 型闭合（行业在用）全面高估——沿槽最多 +154%、跨槽最多 +49%，槽越深错越多"),
        ("错在什么工况：", "该组 2020 年多滴模拟的间隙从 1 μm 关到 10 nm，后半程正落在偏差 85%~106% 的区间，而这段从未被检验"),
        ("该控制什么：", "想让液体跨槽流快，唯一有效旋钮是减小间隙 h；加深沟槽几乎无效（深槽 82% 容积是死空间）"),
        ("怎么修：", "修正因子只用深宽比 d/w：沿槽 +10~205% → 10.5%，跨槽 +8~54% → 6.9%；未参与拟合的 d=75 nm 上 6/6 通过"),
        ("顺带两证：", "K 是合格张量（斜槽旋转律 6/6 命中，补上多图案交换分量所缺的前提）；K 与胶黏度无关（15 倍稠胶仅差 0.0006%）"),
    ], size=21)

    # ---------- P3 难点 ----------
    s = prs.slides.add_slide(prs.slide_layouts[1])
    s.shapes.title.text = "难点"
    # 删除未使用的正文占位符（避免编辑视图出现“单击此处添加文本”）
    empty = s.placeholders[1]._element
    empty.getparent().remove(empty)
    # 几何示意（纵向放大）：周期 P=240；凸台 w=120 压到间隙 h=75；槽宽 120、槽深 d=100
    base_x, period = 0.92, 1.35
    boss = period / 2
    y_mold, y_boss_b, y_sub_top, y_groove_b, y_sub_b = 3.60, 4.25, 4.70, 5.17, 5.42
    n_boss = 4
    fig_w = period * n_boss
    gray_rect(s, base_x, y_sub_top, fig_w, y_sub_b - y_sub_top)          # 基板
    for k in range(n_boss - 1):                                          # 槽（挖空）
        gr = gray_rect(s, base_x + boss + k * period, y_sub_top, boss, y_groove_b - y_sub_top)
        gr.fill.background()
    for k in range(n_boss):                                              # 模具凸台
        gray_rect(s, base_x + k * period, y_mold, boss, y_boss_b - y_mold)
    gray_rect(s, base_x, y_mold - 0.22, fig_w + boss, 0.22)               # 模具本体
    # h 标注（右侧空白区正是间隙）
    xa = base_x + fig_w + 0.10
    thin_line(s, xa, y_boss_b, xa, y_sub_top)
    fig_caption(s, xa + 0.08, (y_boss_b + y_sub_top) / 2 - 0.14, 1.3, "h = 75 nm", 12)
    fig_caption(s, base_x, y_sub_b + 0.10, fig_w + 1.5,
                "P = 240 nm／周期　w = 120 nm 槽宽　d = 100 nm 槽深（纵向放大示意）", 12)
    textbox(s, base_x, 1.95, 6.0, 1.32, [
        ("沿槽（∥）流得快，跨槽（⊥）流得慢——", "方向性阻力决定填充时间与缺陷。"),
    ], size=16)

    textbox(s, 7.35, 1.95, 5.15, 4.9, [
        ("纳米压印（J-FIL）　", "滴胶 → 模具下压 → 液体填槽。沿槽快、跨槽慢的方向性决定填充时间与缺陷。"),
        ("行业做法　", "Jain et al. 2017（Microelectron. Eng. 173）用各向异性渗透率算压印流动，数学上就是局部立方律（条纹平均）。"),
        ("问题　", "该公式从未在“矩形直角槽 + 有限间隙”上被定量验证——原论文只与实验定性比较。"),
        ("本文做什么　", "OpenLB 显式沟槽 DNS，定量标定其误差并给出修正。基准几何 h=75/d=100 沿槽方向公式高估 +146%——正在用的公式可能把填充速度算错 2.5 倍。"),
    ], size=15)

    # ---------- P4 计算方法与验证 ----------
    content_slide(prs, "计算方法与验证", [
        ("几何显式建模：", "真实沟槽（凸台／槽／台阶）直接画进网格，不做任何等效化"),
        ("六项门禁：", "质量漂移 <1e-10 · 密度偏差 ≤1e-6 · 马赫数 <0.05 · 收敛窗口 · 截面一致性 · 体积守恒"),
        ("窗口收敛：", "1000 步窗口 std≤1e-6、span≤5e-6，全部档位自动收敛"),
        ("网格复核：", "dx 5→2.5 nm 复算，K 变化 0.3–2.2%，量级符合预期"),
        ("新旧对账：", "重叠档与历史 PASS 数据逐位一致（同一把尺子）"),
        ("独立交叉复核：", "全部数字经独立脚本重算，0 处不一致（存储 6 位舍入除外）"),
        ("结果：", "48 档 DNS 全部 PASS；平板极限误差 0.03%，Ma < 4e-7，质量漂移 ≤1e-11"),
    ], size=20)

    # ---------- P5 初步结果：公式误差地图 ----------
    s = prs.slides.add_slide(prs.slide_layouts[5])
    s.shapes.title.text = "初步结果：公式误差地图"
    picture_fit(s, "error_map.png", 0.92, 1.95, 7.75, 3.6)
    fig_caption(s, 0.92, 5.65, 7.75, "E =（模型 K − DNS K）/ DNS K；左：沿槽，右：跨槽。9 种几何 × 2 方向，误差全部为正。")
    textbox(s, 8.95, 1.95, 3.55, 4.9, [
        ("误差范围　", "沿槽 +10.3% ~ +154.2%；跨槽 +11.7% ~ +49.1%"),
        ("最狠一格　", "h=50 / d=100 沿槽 +154%"),
        ("各向异性比　", "模型 7.26 vs DNS 3.92（+85%）"),
        ("判断　", "误差随槽深单调放大、随间隙减小而增大——系统性、有明确规律，修正有清晰靶子。"),
    ], size=15)

    # ---------- P6 初步结果：等体积效率 ----------
    s = prs.slides.add_slide(prs.slide_layouts[5])
    s.shapes.title.text = "初步结果：等体积效率与弹性系数"
    picture_fit(s, "efficiency_map.png", 0.92, 1.95, 7.75, 3.4)
    fig_caption(s, 0.92, 5.45, 7.75, "等体积效率 η：槽内单位容积对通流的贡献（η⟂ = 0.18 表示深槽 82% 容积对跨槽是死空间）。")
    textbox(s, 8.95, 1.95, 3.55, 4.9, [
        ("等体积效率　", "η⟂ = 0.18（h50/d100）；η∥ = 0.60–0.95，沿槽好一些。"),
        ("弹性系数　", "Ŝ_d^T ≈ 0.001–0.05：槽深翻倍，跨槽通流几乎不动；Ŝ_h^T ≈ 2.7–2.8：间隙是绝对主导。"),
        ("判断　", "加深槽“白挖”，减 h 才是唯一有效旋钮。"),
        ("给工艺的建议　", "优先控制间隙均匀性，而不是改槽深设计。"),
    ], size=15)

    # ---------- P7 初步结果：深间隙段的模型失效（新增） ----------
    s = prs.slides.add_slide(prs.slide_layouts[5])
    s.shapes.title.text = "初步结果：深间隙段模型失效"
    picture_fit(s, "dh_scaling.png", 0.92, 1.95, 7.15, 3.55)
    fig_caption(s, 0.92, 5.60, 7.15, "横轴为槽深与间隙之比 d/h，纵轴为各向异性比 K∥/K⟂（对数）。"
                                     "红线为 Jain/Ban 模型，圆点为本项目 DNS。")
    textbox(s, 8.30, 1.88, 4.20, 5.0, [
        ("背景　", "多滴铺展模拟中，间隙从 1 μm 关到 10 nm（Ban & Bonnecaze 2020），d/h 从 0.1 走到 10。"),
        ("模型行为　", "d/h=4 时模型给出 K∥/K⟂=31.8，DNS 只有 15.5，高估 106%；d/h=10 时模型给出 333。"),
        ("含义　", "该文献模拟的后半程（间隙<50 nm）正落在偏差 85%~106% 区间，而这一段从未被数值检验。"),
        ("分寸　", "其定性结论（推迟合并）由合并动力学主导，未必受影响；受影响的是填充时间、最优间距比等定量预测。"),
    ], size=13)

    # ---------- P8 初步结果：修正公式与留出验证 ----------
    s = prs.slides.add_slide(prs.slide_layouts[5])
    s.shapes.title.text = "初步结果：修正公式与留出验证"
    picture_fit(s, "correction_validation.png", 0.92, 1.95, 7.6, 4.25)
    fig_caption(s, 0.92, 6.30, 7.6, "左：留出槽深 d = 75 nm（两次拟合都未用）× 3 间隙 × 2 方向，6/6 落入判据。"
                                     "右：全部 18 档修正后残差对 d/w。")
    textbox(s, 8.75, 1.95, 3.75, 4.95, [
        ("两个修正因子　", "F∥ = 1/(1+1.7685(d/w)^1.6331)；F⟂ = 1/(1+0.4900(d/w)^0.6990)——同一变量，只差系数"),
        ("误差压降　", "沿槽 +10~205% → 10.5%；跨槽 +8~54% → 6.9%"),
        ("为什么改用 d/w　", "原式变量 d/H_ref 随 h 降得太快：所需修正只变 1.07~1.23 倍，拟合却变 1.23~1.69 倍，放大 h 依赖 → 小间隙过修、大间隙欠修（+38.6% 在 h=125）"),
        ("判据与范围　", "d/w≤1；沿槽 h≥25 内 10.5%，跨槽 h≥50 内 6.9%。h=25 跨槽 18.7%，故不声明。"),
        ("分区适用　", "同一模板上 d=50 与 d=100 两块，F∥ 相差 62%（0.703 vs 0.432）——多区域模板必须分区各算。"),
        ("坦白　", "残余 h 依赖只减半（6~21 点）、符号还翻转；所报是采样域上界，非连续域保证。"),
        ("物性前提　", "全充液单相牛顿胶。有气液界面时不适用——双相引入饱和度，K 退化为 k_r(S)。"),
    ], size=11.0)

    # ---------- P8 初步结果：斜槽旋转角验证 ----------
    s = prs.slides.add_slide(prs.slide_layouts[5])
    s.shapes.title.text = "初步结果：斜槽旋转角验证"
    picture_fit(s, "tensor_validation.png", 0.92, 1.88, 4.35, 3.55)
    fig_caption(s, 0.92, 5.50, 4.35, "横轴：驱动角 θ；纵轴：液流实际偏转角 φ。"
                                     "虚线为张量旋转律预测，点为 DNS。")
    picture_fit(s, "oblique_geometry.png", 5.42, 1.88, 3.55, 2.40)
    fig_caption(s, 5.42, 4.36, 3.55, "斜槽几何：槽轴与驱动方向夹 θ，"
                                     "液流被槽“拉回”槽方向，只偏转 φ。")
    textbox(s, 9.05, 1.88, 3.45, 5.0, [
        ("做法　", "把沟槽整体转 30°/45°/60°，沿驱动方向加同一压差，量液流的实际流向。"),
        ("结果　", "θ=45° 时驱动朝 45°，液流只走 24.3°——被槽拉回 20.7°，与理论 24.34° 四位有效数字一致。"),
        ("6/6 命中　", "两组几何 × 三个角度，K(θ) 与 φ 全部复现，误差 <1e-4%。"),
        ("补上行业缺的前提　", "现有多图案做法只处理 0°/90°：取向变了就把 kxx 与 kyy 对调（Ban & Bonnecaze 2021），等于默认旋转律成立却从未检验。本文验证了任意角下该操作成立。"),
    ], size=12.5)

    # ---------- P9 初步结果：黏度无关性 ----------
    s = prs.slides.add_slide(prs.slide_layouts[5])
    s.shapes.title.text = "初步结果：黏度无关性"
    picture_fit(s, "viscosity_check.png", 0.92, 2.05, 7.05, 3.20)
    fig_caption(s, 0.92, 5.42, 7.05, "同一几何，只把胶的黏度提高 15 倍（μ=15 mPa·s，"
                                     "mr-NIL210 量级）：K 不动，流量正好慢 15 倍。")
    textbox(s, 8.35, 1.88, 4.15, 5.0, [
        ("做法　", "同一档几何（h75/d100），把 μ 提高 15 倍重算。"),
        ("结果　", "K 变化 0.0006%，J 恰好降到 1/15——黏度只是整体快慢的缩放。"),
        ("为什么　", "K 是纯几何量，定义时已把 μ 除掉。μ 在分子分母同时出现，数学上可约。"),
        ("推论　", "全充液单相下，误差表与修正公式对所有牛顿胶通用，换胶不需重跑。"),
        ("边界　", "双相不行：一旦有气相，空隙被部分占据，渗透率变成随饱和度变化的相对渗透率 k_r(S)，其转变参数需另行标定——不再是纯几何量。"),
    ], size=12.5)

    # ---------- P10 结尾（按用户要求删除） ----------

    prs.save(OUT)
    print("saved:", OUT, "| slides:", len(prs.slides))


if __name__ == "__main__":
    build()
