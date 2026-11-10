"""Build a table-driven evidence-chain supplement for the 2026-11-05 afternoon briefing.

Rows = existing data groups; columns = data / conclusion / boundary.
Page 2 = formulas, applicability domain, and the S4 judgement.

Only saved records are read. No solver, no refit, no new Gate, no threshold change.
Original 21-page PDF/PPTX and the earlier 22-page PDF are NOT modified.
"""
from pathlib import Path
import os, tempfile, csv, json, html, math

# sandbox /tmp is a 10 MB tmpfs; WeasyPrint needs ~20 MB for the CJK font
B = Path(__file__).resolve().parent
_TMP = B / '_tmp'
_TMP.mkdir(exist_ok=True)
os.environ.setdefault('TMPDIR', str(_TMP))
tempfile.tempdir = str(_TMP)

from weasyprint import HTML
from pypdf import PdfReader, PdfWriter

AFTERNOON = B.parent
ROOT = B.parents[4]
SRC_CSV = ROOT / 'docs/reports/PAPER1_claim_evidence_review_20261105/recomputed_36_points.csv'
DOMAIN_JSON = ROOT / 'docs/reports/Correction_formula_derivation_20261023/coefficients_and_domain.json'
ORIGINAL_PDF = AFTERNOON / 'PAPER1_导师汇报_20261105_下午修订版.pdf'

W, H = 1280, 720
BLUE, NAVY = '#1E4FA8', '#12294D'
LIGHT, PANEL = '#E8EFF8', '#F7F9FC'
TEXT, SUB, MUT, LINE = '#1A2230', '#4A5568', '#8B97A8', '#D6DCE5'
RED, RED_BG, GRN_BG, AMB_BG = '#D9534F', '#FBECEC', '#EAF3EC', '#FDF6E8'

# ----------------------------------------------------------------verify first
rows = list(csv.DictReader(SRC_CSV.open()))
domain = json.loads(DOMAIN_JSON.read_text())
E = [float(r['E_percent']) for r in rows]
Vp = [abs(float(r['V2_residual_percent'])) for r in rows if r['direction'] == 'parallel']
Vt = [abs(float(r['V2_residual_percent'])) for r in rows if r['direction'] == 'perpendicular']
Vt50 = [abs(float(r['V2_residual_percent'])) for r in rows
        if r['direction'] == 'perpendicular' and float(r['h_nm']) >= 50]
Ep = [float(r['E_percent']) for r in rows if r['direction'] == 'parallel']
Et = [float(r['E_percent']) for r in rows if r['direction'] == 'perpendicular']
checks = {
    'n_points': len(rows) == 36,
    'all_E_positive': all(e > 0 for e in E),
    'E_parallel_range': (round(min(Ep), 2), round(max(Ep), 2)) == (10.30, 204.85),
    'E_perp_range': (round(min(Et), 2), round(max(Et), 2)) == (8.11, 54.19),
    'V2_parallel_max': round(max(Vp), 2) == 10.50,
    'V2_perp_max': round(max(Vt), 2) == 18.71,
    'V2_perp_h50_max': round(max(Vt50), 2) == 6.92,
    'n_perp_h50': len(Vt50) == 15,
    'hull_vertices': len(domain['sample_ratio_vertices']) == 5,
    'phi': domain['phi'] == 0.5,
}
assert all(checks.values()), checks

# ----------------------------------------------------------------markdown copy
groups = [
    ('① 主地图：18 组几何 / 36 个方向点（5 nm）',
     'h = 25 / 50 / 75 / 125 nm；d = 25 / 50 / 75 / 100 / 120 nm（h=25 缺 d=75、120）。正文表 1、补充材料表 S1',
     '原局部立方律在 36 个点上全部高估导度：沿槽 +10.30% ~ +204.85%，横槽 +8.11% ~ +54.19%（表 6）。',
     '偏差是相对 5 nm 离散参考，不是连续真解误差。9 个标定几何与 9 个扩展几何分属两组不同二进制，几何分组与程序分组完全重合，不能分离几何效应与构建差异。'),
    ('② 双网格加密：4 组几何 / 8 行',
     '(25,100)、(50,100)、(125,25)、(125,120) nm；5 nm ↔ 2.5 nm。表 2、表 4、表 S2',
     '加密后 K 变化：沿槽 ≤0.52%，横槽最大 −4.43%（h25/d100）。换参考网格使偏差变动 0.37–5.39 个百分点，并翻转 V2 在该点「改善 / 变差」的判断。',
     '只有两级，不能定观测收敛阶；其余 14 组几何未加密，不能把 4.43% 当作全图误差界。'),
    ('③ 斜向 6 项 + 黏度对照 2 项',
     'D3 斜向驱动 6 项；μ = 15 mPa·s 对照 2 项。表 S1',
     '一致性与鲁棒性检查：斜向有真实横向通量，按该算例自身判据处理；黏度对照与主地图物性分列。',
     '不进 36 点主地图，不参与 V2 拟合；不能与 36 点相加成独立物理样本数。'),
    ('④ 周期复制 + 多力检查：18 行',
     '基准几何 (75,100) nm、2.5 nm 网格；周期数 Nx=2；驱动力相差 4 倍。表 S3',
     'Nx=2 与归档值相对差 6.9×10⁻¹⁴；K 最大相对偏差 3.7×10⁻⁸ → 支持被测范围内的线性响应。',
     '只此一几何、一网格；不是对 36 个主地图样点逐个验证。'),
    ('⑤ 平壁解析三网格 + 历史三网格',
     'h = 75 nm 平板，5 / 2.5 / 1.25 nm。表 3；历史 9 行见表 S4 / S5',
     '对解析 h³/12 的相对误差 0.444% → 0.111% → 0.0272%，网格每加密一倍约降到四分之一。',
     '检验的是平直壁配置下的总积分误差，不外推到沟槽，也不等于全图网格无关。历史 1.25 nm 横槽质量 FAIL 原样保留。'),
    ('⑥ S0–S4 验证任务：h30/d80，6 条运行',
     '3 档网格 × 2 方向。S0 诊断、S1 平板、S2 常规间隙、S3 驱动力、S4 薄间隙',
     'S0–S3 通过。S4 六条各自的数值 / 几何 / 流场门全 PASS；沿槽三网格 PASS；横槽中—细变化 1.328% > 1% → 阶段未通过。',
     '与 ① 的 18 组几何不是同一批算例；单条 PASS 不等于阶段 PASS。判定细节见第 2 页。'),
    ('⑦ 1.25 nm 服务器条目 + OpenFOAM 5 例',
     '服务器 h30/d80 横槽 1.25 nm；C01–C04 与 GDI01 共用 h75/d100',
     '1.25 nm 的 K 与本机同值（相对差 0），满足构建等价判据；OpenFOAM 五例核对二维与平均模型的接入一致性。',
     '都不关闭 S4 网格问题；OpenFOAM 不提供 V2 对真实沟槽的独立精度证据。0.625 nm 未运行。'),
]

md = [
    '# 证据链总表：数据大组 → 结论 → 公式与适用范围 → S4 判断',
    '',
    '> 只整理既有记录，未启动求解、未重拟合、未改门槛、未新增 Gate。',
    '> 分组依据：补充材料表 S1 的 52 项逐运行清单 + 汇报 PPT 第 2 页的三类计数；',
    '> S0–S4 属另一条验证任务线，与论文 18 组几何主地图不是同一批算例。',
    '',
    '## 一、每大组数据得出什么结论',
    '',
    '| 大组 | 数据（已保存） | 得出的结论 | 边界 / 不能说 |',
    '|---|---|---|---|',
]
for name, data, concl, limit in groups:
    md.append('| ' + ' | '.join([name, data, concl, limit]) + ' |')
md += [
    '',
    '## 二、公式（三个对象，别混）',
    '',
    '| 对象 | 表达式 | 角色 |',
    '|---|---|---|',
    '| 原局部立方律（正文式 3） | K_yy^mod = [(h+d)³ + h³]/24；K_xx^mod = (h+d)³h³ / {6[(h+d)³+h³]} | 待检验的近似（深区/浅区局部平板组合） |',
    '| V2 乘性修正（§4.4 公布舍入式） | F_yy = 1/[1+1.7685(d/w)^1.6331]；F_xx = 1/[1+0.4900(d/w)^0.6990] | 在原公式上乘经验因子 |',
    '| 比较口径（式 4） | K^V2 = F·K^mod；偏差 E = K^mod/K^ref − 1；残差 = K^V2/K^ref − 1 | K^ref 是同几何同方向的 5 nm 离散值 |',
    '',
    '## 三、适用范围',
    '',
    '- **物理前提**：单相牛顿液体、完全充液、固定间隙、无滑移、周期矩形直槽、低 Re 的 Stokes 模型；槽宽占比 φ = w/P = 0.5、P = 2w。',
    '- **几何域**：Stokes 方程给出长度三次齐次性 K = w³·κ(h/w, d/w)，真正自变量是 α = h/w、β = d/w。现有 18 组落在 α ∈ [0.208, 1.042]、β ∈ [0.208, 1.000] 的**凸包**内（在对数比例坐标中定义），h = 25 nm 只覆盖 3 个槽深，不是完整矩形。',
    '- **精度（仅回顾性，不是预测）**：V2 最大 |残差| 沿槽 18 点 10.5%、横槽 18 点 18.7%；h ≥ 50 nm 的 15 个横槽点为 6.9%。落在域内不保证精度（原始 domain_note 明示）。',
    '- **域外**：改变 w 或 φ 只能用相似映射做位置换算，不等于已有 DNS 记录，仍需重新验证。换 2.5 nm 参考，误差数值会变。',
    '',
    '## 四、S4 判断（当前唯一未通过的网格门）',
    '',
    '| 项 | 沿槽 P | 横槽 T |',
    '|---|---|---|',
    '| 事先门槛 | 中—细变化 ≤1% **且** 细网格 GCI ≤1%（r=2、Fs=1.25） | 同左 |',
    '| 观测阶 p | 1.673 | 1.496 |',
    '| 中—细变化 | 0.165% → PASS | **1.328% → FAIL**（超 0.328 个百分点） |',
    '| 细网格 GCI | 0.094% → PASS | 0.912% → 通过，但不能抵补前一项 |',
    '| 方向判定 | **PASS** | **FAIL** |',
    '',
    '**阶段判定**：GRID_CHECKS_PASS = false、S4_STAGE_ACCEPTED = false、reference_qualified = false；S5 未启动，MODEL_COMPARISON / physical_validation 未评价。',
    '',
    '**三条不能做**：把 1% 改成 2%；只挑 GCI 通过项报喜；因六条已算完就补写 S4_completed.json。',
    '',
    '**S4 与公式适用范围的关系**：0.625 nm 补的是「薄间隙严格参考」这条线，它不改变 18 组数据的覆盖形状，也不扩大公式适用域；1.25 nm 已完成只关闭构建复现问题。两条线不能互相替代。',
    '',
    '## 五、证据入口（相对 docs/reports）',
    '',
    '- `PAPER1_claim_evidence_review_20261105/REPORT.md`、`recomputed_36_points.csv`',
    '- `SIM240_中文稿_导师审阅版_20261022.md` 表 1–8、§5.3',
    '- `SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md` 表 S1–S5',
    '- `Correction_formula_derivation_20261023/DERIVATION.md` §4、§6；`coefficients_and_domain.json`',
    '- `URV_S4_completed_review_20261104_143205/REPORT.md` §5',
    '- `URV_S4_TGE_1p25_data_audit_20261105_100521/REPORT.md`',
    '',
]
(B / '证据链总表_下午汇报.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

# ----------------------------------------------------------------PDF helpers
def box(left, top, width, height, inner, bg='white', border=None, radius=0):
    bd = f'border:1px solid {border};' if border else ''
    return (f'<div class="box" style="left:{left}px;top:{top}px;width:{width}px;'
            f'height:{height}px;background:{bg};{bd}border-radius:{radius}px;'
            f'padding:9px 13px;">{inner}</div>')


def table(headers, body_rows, widths, cls=''):
    cols = ''.join(f'<col style="width:{w}%">' for w in widths)
    th = ''.join(f'<th>{html.escape(h)}</th>' for h in headers)
    tr = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>' for row in body_rows)
    return f'<table class="{cls}">{cols}<thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'


def head(title, pageno):
    return [
        '<div class="topbar"></div>',
        f'<div class="tag">补充 · 证据链总表 {pageno} / 2</div>',
        f'<div class="title">{title}</div>',
        '<div class="hr1"></div>',
    ]


def foot(note):
    return [
        '<div class="hr2"></div>',
        f'<div class="foot">{note}</div>',
        f'<div class="pageno">{note[-20:]}</div>',
    ]

# ----------------------------------------------------------------page 1
t1 = table(['大组', '数据（已保存）', '得出的结论', '边界 / 不能说'],
           [[('<b>' + html.escape(parts[0]) + '</b><br><span class="sm">'
              + html.escape(parts[1]) + '</span>') if len(parts := n.split('：', 1)) == 2
             else '<b>' + html.escape(n) + '</b>',
             html.escape(d), html.escape(c), html.escape(l)]
            for n, d, c, l in groups],
           [15, 23, 34, 28], cls='tight')

p1 = head('数据大组 → 得出什么结论', 1) + [
    '<div class="sec" style="left:45px;top:132px;width:1190px">'
    '① 七组数据各自回答一个不同问题；不能相加成独立物理样本数</div>',
    box(45, 158, 1190, 476, t1, bg='white'),
    '<div class="hr2"></div>',
    '<div class="foot">分组依据：补充材料表 S1（52 项）＋ 汇报第 2 页三类计数；S0–S4 是另一条验证任务线，与主地图 18 组几何不是同一批算例。</div>',
    '<div class="pageno">补充页 1 / 2</div>',
]

# ----------------------------------------------------------------page 2
formula = ('<div class="cardtitle">② 公式：三个对象，别混</div>'
           '<div class="mono">K<sub>yy</sub><sup>mod</sup> = [(h+d)³ + h³] / 24<br>'
           'K<sub>xx</sub><sup>mod</sup> = (h+d)³h³ / {6[(h+d)³+h³]}'
           '<div class="cap">正文式 (3)：深区 / 浅区局部平板组合，是<b>待检验</b>的近似</div></div>'
           '<div class="mono" style="margin-top:9px">'
           'F<sub>yy</sub> = 1 / [1 + 1.7685 (d/w)<sup>1.6331</sup>]<br>'
           'F<sub>xx</sub> = 1 / [1 + 0.4900 (d/w)<sup>0.6990</sup>]'
           '<div class="cap">V2（§4.4 公布舍入式）：K<sup>V2</sup> = F · K<sup>mod</sup>；'
           '偏差与残差都以同几何同方向的 <b>5 nm 离散值</b>为分母</div></div>')

appl = ('<div class="cardtitle">③ 适用范围</div>'
        '<div class="txt">'
        '<b>物理前提</b>：单相牛顿、完全充液、固定间隙、无滑移、周期矩形直槽、低 Re Stokes；'
        'φ = w/P = 0.5、P = 2w。<br>'
        '<b>几何域</b>：长度三次齐次 K = w³·κ(h/w, d/w)，自变量是 α = h/w、β = d/w。'
        '现有 18 组落在 α ∈ [0.208, 1.042]、β ∈ [0.208, 1.000] 的<b>凸包</b>内'
        '（对数比例坐标中定义）；h = 25 只覆盖 3 个槽深，不是完整矩形。<br>'
        '<b>精度（仅回顾性）</b>：V2 最大 |残差| 沿槽 18 点 <b>10.5%</b>、横槽 18 点 <b>18.7%</b>；'
        'h ≥ 50 nm 的 15 个横槽点 <b>6.9%</b>。落在域内不保证精度。<br>'
        '<b>域外</b>：改 w 或 φ 只能做相似位置换算，仍需重新验证；换 2.5 nm 参考，误差数值会变。</div>')

s4 = table(['事先门槛：中—细 ≤1% 且 GCI ≤1%（r=2, Fs=1.25）', '沿槽 P', '横槽 T'], [
    ['观测阶 p', '1.673', '1.496'],
    ['中—细变化', '0.165%　PASS', '<b>1.328%　FAIL</b>（超 0.328 个百分点）'],
    ['细网格 GCI', '0.094%　PASS', '0.912%　通过，但不能抵补前一项'],
    ['<b>方向判定</b>', '<b>PASS</b>', '<b>FAIL</b>'],
], [46, 22, 32], cls='tight')

s4box = (f'<div class="cardtitle" style="color:#B33A36">④ S4 判断：当前唯一未通过的网格门</div>'
         + s4 +
         '<div class="txt" style="margin-top:8px">'
         '<b>阶段判定</b>：GRID_CHECKS_PASS=false、S4_STAGE_ACCEPTED=false、'
         'reference_qualified=false；S5 未启动，MODEL_COMPARISON / physical_validation 未评价。<br>'
         '<b>三条不能做</b>：把 1% 改成 2%；只挑 GCI 通过项报喜；因六条已算完就补写 '
         'S4_completed.json。</div>')

linkbox = ('<div class="cardtitle" style="color:' + BLUE + '">⑤ S4 这条线与公式适用范围的关系</div>'
           '<div class="txt">0.625 nm 补的是<b>薄间隙严格参考</b>这条线，'
           '它不改变 18 组数据的覆盖形状，也<b>不扩大公式适用域</b>；'
           '1.25 nm 已完成只关闭构建复现问题。两条线不能互相替代。<br>'
           '<b>被问到时怎么答</b>：可以报 10.5% / 18.7% / 6.9% 与 1.328%，'
           '但每次都要补一句「V2 是拿同一批 18 组数据回头修正的，这些是回顾性残差，'
           '不是独立预测精度」。</div>')

p2 = head('公式、适用范围与 S4 判断', 2) + [
    box(45, 132, 580, 262, formula, bg=PANEL, border=LINE, radius=3),
    box(45, 404, 580, 230, appl, bg=PANEL, border=LINE, radius=3),
    box(645, 132, 590, 336, s4box, bg=RED_BG, border='#E7B9B7', radius=3),
    box(645, 478, 590, 156, linkbox, bg=LIGHT, border='#C9D9F0', radius=3),
    '<div class="hr2"></div>',
    '<div class="foot">本页只整理既有记录：未启动求解、未重拟合、未改门槛、未新增 Gate。证据入口见同目录 证据链总表_下午汇报.md。</div>',
    '<div class="pageno">补充页 2 / 2</div>',
]

css = f'''
@font-face{{font-family:NotoCJK;src:url(file:///usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc)}}
@font-face{{font-family:NotoCJK;src:url(file:///usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc);font-weight:700}}
@page{{size:{W}px {H}px;margin:0}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;background:white;font-family:NotoCJK,sans-serif}}
.slide{{width:{W}px;height:{H}px;position:relative;background:white;overflow:hidden;page-break-after:always}}
.slide:last-child{{page-break-after:auto}}
.topbar{{position:absolute;left:0;top:0;width:{W}px;height:13px;background:{BLUE}}}
.tag{{position:absolute;left:45px;top:23px;font-size:12px;color:{MUT};letter-spacing:.5px}}
.title{{position:absolute;left:45px;top:50px;width:1190px;font-size:29px;font-weight:700;color:{NAVY};line-height:1.2}}
.hr1{{position:absolute;left:45px;top:115px;width:1190px;height:1px;background:{LINE}}}
.hr2{{position:absolute;left:45px;top:666px;width:1190px;height:1px;background:{LINE}}}
.sec{{position:absolute;font-size:15px;font-weight:700;color:{NAVY};line-height:1.3}}
.box{{position:absolute;overflow:hidden}}
.foot{{position:absolute;left:45px;top:676px;width:1000px;font-size:10.5px;color:{MUT}}}
.pageno{{position:absolute;left:1075px;top:676px;width:160px;text-align:right;font-size:11.5px;color:{BLUE}}}
table{{table-layout:fixed;border-collapse:collapse;width:100%}}
th{{background:{BLUE};color:white;font-size:12.5px;font-weight:700;padding:6px 8px;text-align:left;border:.5px solid {LINE}}}
td{{font-size:11.8px;color:{TEXT};padding:5px 8px;border:.5px solid {LINE};line-height:1.42;vertical-align:top}}
tbody tr:nth-child(even) td{{background:#FAFCFF}}
table.tight th{{font-size:13px;padding:7px 9px}}
table.tight td{{font-size:12.4px;padding:8px 9px;line-height:1.48}}
.sm{{font-size:11.5px;color:{SUB}}}
.cardtitle{{font-size:14px;font-weight:700;color:{NAVY};margin-bottom:7px}}
.mono{{font-size:13px;color:{NAVY};line-height:1.6;background:white;border:1px solid {LINE};
       padding:6px 9px;border-radius:2px;font-family:NotoCJK,sans-serif}}
.cap{{font-size:10.8px;color:{SUB};line-height:1.4;margin-top:3px;font-weight:400}}
.txt{{font-size:12.2px;color:{TEXT};line-height:1.6}}
'''

def slide(parts):
    return '<div class="slide">' + ''.join(parts) + '</div>'

htmlstr = ('<html><head><meta charset="utf-8"><style>' + css + '</style></head><body>'
           + slide(p1) + slide(p2) + '</body></html>')

page_pdf = B / '证据链总表_补充页.pdf'
HTML(string=htmlstr, base_url=str(B)).write_pdf(str(page_pdf))

merged_pdf = AFTERNOON / 'PAPER1_导师汇报_20261105_下午修订版_含证据链总表.pdf'
writer = PdfWriter()
for p in PdfReader(str(ORIGINAL_PDF)).pages:
    writer.add_page(p)
for p in PdfReader(str(page_pdf)).pages:
    writer.add_page(p)
with merged_pdf.open('wb') as f:
    writer.write(f)

print(json.dumps(dict(
    checks=checks,
    markdown='证据链总表_下午汇报.md',
    supplement_pdf=str(page_pdf.name),
    supplement_pages=len(PdfReader(str(page_pdf)).pages),
    merged_pdf=str(merged_pdf.name),
    merged_pages=len(PdfReader(str(merged_pdf)).pages)),
    indent=2, ensure_ascii=False))
