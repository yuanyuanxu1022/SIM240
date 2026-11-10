"""Build the "formula applicability domain" supplement page for the 2026-11-05 afternoon briefing.

Reads only saved records. No solver, no refit, no new Gate, no threshold change.
Outputs: point-level CSV, statistics JSON, one-page PDF, and a 22-page merged PDF.
"""
from pathlib import Path
import os, tempfile, csv, json, html

# The sandbox /tmp is a 10 MB tmpfs; WeasyPrint needs ~20 MB for the CJK font.
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
W_NM = 120.0

BLUE, NAVY = '#1E4FA8', '#12294D'
LIGHT, PANEL = '#E8EFF8', '#F7F9FC'
TEXT, SUB, MUT, LINE = '#1A2230', '#4A5568', '#8B97A8', '#D6DCE5'
RED, RED_BG, GRN_BG = '#D9534F', '#FBECEC', '#EAF3EC'


def stats(sel):
    E = [float(r['E_percent']) for r in sel]
    V = [abs(float(r['V2_residual_percent'])) for r in sel]
    T = [abs(float(r['V2_residual_percent'])) for r in sel if r['direction'] == 'perpendicular']
    return dict(n=len(sel), E_min=min(E), E_max=max(E),
                V2_max=max(V), V2_mean=sum(V) / len(V), V2_T_max=max(T) if T else None)


def fmt(x, d=2):
    return f'{x:.{d}f}'


rows = list(csv.DictReader(SRC_CSV.open()))
domain = json.loads(DOMAIN_JSON.read_text())
all_s = stats(rows)
ge50 = stats([r for r in rows if float(r['h_nm']) >= 50])
h25 = stats([r for r in rows if float(r['h_nm']) == 25])

# ---- point-level evidence table ----
csv_out = B / '公式适用范围_逐点数据.csv'
with csv_out.open('w', newline='') as f:
    wtr = csv.writer(f)
    wtr.writerow(['run_id', 'h_nm', 'd_nm', 'alpha_h_over_w', 'beta_d_over_w',
                  'direction', 'E_original_percent', 'V2_residual_percent',
                  'abs_V2_residual_percent', 'subdomain'])
    for r in rows:
        h, d = float(r['h_nm']), float(r['d_nm'])
        wtr.writerow([r['run_id'], h, d, f'{h / W_NM:.6f}', f'{d / W_NM:.6f}',
                      r['direction'], r['E_percent'], r['V2_residual_percent'],
                      f'{abs(float(r["V2_residual_percent"])):.6f}',
                      'h>=50' if h >= 50 else 'h=25'])

stat_out = dict(
    title='公式适用范围：分域统计（仅回顾性，非预测精度）',
    source=str(SRC_CSV.relative_to(ROOT)),
    reference='5 nm 离散 DNS 结果，非连续真解/实验',
    w_nm=W_NM, phi=domain['phi'],
    domain_note=domain['domain_note'],
    convex_hull_vertices_alpha_beta=domain['sample_ratio_vertices'],
    alpha_range=[min(v[0] for v in domain['sample_ratio_vertices']),
                 max(v[0] for v in domain['sample_ratio_vertices'])],
    beta_range=[min(v[1] for v in domain['sample_ratio_vertices']),
                max(v[1] for v in domain['sample_ratio_vertices'])],
    subdomains=dict(all=all_s, h_ge_50=ge50, h_eq_25=h25),
    limitations=[
        'V2 是对已有 18 组数据的回顾性修正，不是独立新条件预测验证',
        '落在凸包内不保证预测精度（原始 domain_note 明示）',
        '偏差参照是 5 nm 离散结果，不是连续真解或实验误差',
        'h=25 nm 的 3 组几何与另一二进制分组交织，偏差不能单独归因于几何',
        '域外属外推；改变 w 或槽宽占比 phi 需重新验证',
    ])
(B / '公式适用范围_统计.json').write_text(json.dumps(stat_out, indent=2, ensure_ascii=False) + '\n')

# ---- one-page HTML (1280x720 px, same visual language as the afternoon deck) ----
def box(left, top, width, height, inner, bg='white', border=None, radius=0):
    bd = f'border:1px solid {border};' if border else ''
    return (f'<div class="box" style="left:{left}px;top:{top}px;width:{width}px;'
            f'height:{height}px;background:{bg};{bd}border-radius:{radius}px;'
            f'padding:10px 14px;">{inner}</div>')


def table(headers, body_rows, widths=None):
    cols = ''.join(f'<col style="width:{w}%">' for w in widths) if widths else ''
    th = ''.join(f'<th>{html.escape(h)}</th>' for h in headers)
    tr = ''.join('<tr>' + ''.join(f'<td>{html.escape(str(c))}</td>' for c in row) + '</tr>'
                 for row in body_rows)
    return f'<table>{cols}<thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'


t1 = table(['项目', '取值 / 定义'], [
    ['自变量', 'α = h/w，β = d/w（w = 120 nm，槽宽占比 φ = 0.5 固定）'],
    ['数据覆盖域', 'α ∈ [0.208, 1.042]，β ∈ [0.208, 1.000]'],
    ['实际形状', '凸包，不是矩形：α = 0.208 时只到 β ≤ 0.833（缺 2 格）'],
    ['采样', '18 组几何 / 36 方向点；h = 25 nm 只有 3 个槽深'],
], [22, 78])

t2 = table(['子域', '点数', '原公式偏差', 'V2 最大|残差|', '横槽最大|残差|'], [
    ['全部 36 点', '36', f'{fmt(all_s["E_min"])}–{fmt(all_s["E_max"])}%',
     f'{fmt(all_s["V2_max"])}%', f'{fmt(all_s["V2_T_max"])}%'],
    ['h ≥ 50 nm（α ≥ 0.417）', '30', f'{fmt(ge50["E_min"])}–{fmt(ge50["E_max"])}%',
     f'{fmt(ge50["V2_max"])}%', f'{fmt(ge50["V2_T_max"])}%'],
    ['h = 25 nm（α = 0.208）', '6', f'{fmt(h25["E_min"])}–{fmt(h25["E_max"])}%',
     f'{fmt(h25["V2_max"])}%', f'{fmt(h25["V2_T_max"])}%'],
], [30, 9, 22, 19, 20])

green = (f'<div style="font-size:15px;font-weight:700;color:{NAVY};margin-bottom:5px">'
         '建议的主张范围</div>'
         f'<div style="font-size:13.5px;color:{TEXT};line-height:1.5">'
         f'把公式适用域写成 <b>α、β 的比例凸包</b>；在此域内、且 <b>h ≥ 50 nm</b> 时，'
         f'V2 双向最大 |残差| ≤ <b>{fmt(ge50["V2_max"])}%</b>，横槽 ≤ <b>{fmt(ge50["V2_T_max"])}%</b>。'
         '最薄间隙 h = 25 nm 是最坏点与唯一反例所在，不宜纳入精度承诺。</div>')

red = ('<div style="font-size:15px;font-weight:700;color:#B33A36;margin-bottom:7px">'
       '四条不能说的话</div>'
       f'<div style="font-size:13px;color:{TEXT};line-height:1.62">'
       '① 这不是独立预测验证：V2 由这 18 组数据回顾性修正而来。<br>'
       '② 落在域内 ≠ 保证精度（原始 domain_note 已明示）。<br>'
       '③ 偏差参照是 5 nm 离散结果，不是连续真解或实验误差。<br>'
       '④ h = 25 nm 三点与另一程序分组交织，偏差不能单归因于几何。</div>')

blue = ('<div style="font-size:14px;font-weight:700;color:' + BLUE + ';margin-bottom:6px">'
        '域外怎么办</div>'
        f'<div style="font-size:13px;color:{TEXT};line-height:1.55">'
        '超出凸包即外推，无精度证据。改变槽宽 w 或占比 φ，可用相似映射定位到比例域，'
        '但那只是「位置换算」，不等于已有 DNS 记录，仍需重新验证。</div>')

bottom = ('<div style="font-size:13px;font-weight:700;color:' + BLUE + ';margin-bottom:4px">'
          '可直接念的一句话</div>'
          f'<div style="font-size:13.5px;color:{TEXT};line-height:1.5">'
          '「我们把公式适用范围写成 h/w 与 d/w 的比例凸包；在数据覆盖域内、间隙不小于 50 nm 时，'
          f'V2 的回顾性残差控制在约 {fmt(ge50["V2_max"], 1)}% 以内；域外只作外推，不承诺精度。」</div>')

evidence = (f'<div style="font-size:11.5px;color:{SUB};line-height:1.6">'
            '<b>证据入口</b>（相对 docs/reports）<br>'
            '· PAPER1_claim_evidence_review_20261105/recomputed_36_points.csv（36 点）<br>'
            '· Correction_formula_derivation_20261023/coefficients_and_domain.json（凸包）<br>'
            '· 逐点复算与统计：本目录 公式适用范围_逐点数据.csv / _统计.json<br>'
            '<span style="color:' + MUT + '">本页只整理既有记录，未启动求解、未重拟合、未改门槛。</span></div>')

parts = [
    f'<div class="topbar"></div>',
    f'<div class="tag">补充 · 公式适用范围</div>',
    f'<div class="title">公式适用范围：写比例域，不写绝对尺寸</div>',
    f'<div class="hr1"></div>',
    # left column
    '<div class="sec" style="left:45px;top:138px;width:760px">① 适用域：长度三次齐次，真正自变量是 α = h/w、β = d/w</div>',
    box(45, 164, 760, 158, t1, bg='white'),
    '<div class="sec" style="left:45px;top:330px;width:760px">② 精度边界：把最薄间隙单独分出来看</div>',
    box(45, 356, 760, 124, t2, bg='white'),
    box(45, 488, 760, 76, green, bg=GRN_BG, border='#BFD9C6', radius=3),
    box(45, 572, 760, 90, bottom, bg=PANEL, border=LINE, radius=3),
    # right column
    '<div class="sec" style="left:825px;top:138px;width:410px">③ 边界条件</div>',
    box(825, 164, 410, 210, red, bg=RED_BG, border='#E7B9B7', radius=3),
    box(825, 384, 410, 112, blue, bg=LIGHT, border='#C9D9F0', radius=3),
    box(825, 506, 410, 154, evidence, bg=PANEL, border=LINE, radius=3),
    '<div class="hr2"></div>',
    '<div class="foot">公式适用范围 · 补充页｜仅既有记录整理，无新增计算、无新 Gate</div>',
    '<div class="pageno">22 / 22</div>',
]

css = f'''
@font-face{{font-family:NotoCJK;src:url(file:///usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc)}}
@font-face{{font-family:NotoCJK;src:url(file:///usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc);font-weight:700}}
@page{{size:{W}px {H}px;margin:0}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;background:white;font-family:NotoCJK,sans-serif}}
.slide{{width:{W}px;height:{H}px;position:relative;background:white;overflow:hidden}}
.topbar{{position:absolute;left:0;top:0;width:{W}px;height:13px;background:{BLUE}}}
.tag{{position:absolute;left:45px;top:23px;font-size:12px;color:{MUT};letter-spacing:.5px}}
.title{{position:absolute;left:45px;top:50px;width:1190px;font-size:30px;font-weight:700;color:{NAVY};line-height:1.2}}
.hr1{{position:absolute;left:45px;top:115px;width:1190px;height:1px;background:{LINE}}}
.hr2{{position:absolute;left:45px;top:666px;width:1190px;height:1px;background:{LINE}}}
.sec{{position:absolute;font-size:15.5px;font-weight:700;color:{NAVY};line-height:1.3}}
.box{{position:absolute;overflow:hidden}}
.foot{{position:absolute;left:45px;top:676px;font-size:11px;color:{MUT}}}
.pageno{{position:absolute;left:1105px;top:676px;width:130px;text-align:right;font-size:12px;color:{BLUE}}}
table{{table-layout:fixed;border-collapse:collapse;width:100%}}
th{{background:{BLUE};color:white;font-size:13.5px;font-weight:700;padding:6px 9px;text-align:left;
    border:.5px solid {LINE}}}
td{{font-size:13px;color:{TEXT};padding:5.5px 9px;border:.5px solid {LINE};line-height:1.35}}
tbody tr:nth-child(even) td{{background:#FAFCFF}}
'''
htmlstr = f'<html><head><meta charset="utf-8"><style>{css}</style></head><body><div class="slide">' + ''.join(parts) + '</div></body></html>'

page_pdf = B / '公式适用范围_补充页.pdf'
HTML(string=htmlstr, base_url=str(B)).write_pdf(str(page_pdf))

# ---- merged 22-page PDF (original 21 pages untouched + this supplement as p.22) ----
merged_pdf = AFTERNOON / 'PAPER1_导师汇报_20261105_下午修订版_含适用范围.pdf'
writer = PdfWriter()
for p in PdfReader(str(ORIGINAL_PDF)).pages:
    writer.add_page(p)
writer.add_page(PdfReader(str(page_pdf)).pages[0])
with merged_pdf.open('wb') as f:
    writer.write(f)

print(json.dumps(dict(
    point_csv=str(csv_out.name), stats_json='公式适用范围_统计.json',
    supplement_pdf=str(page_pdf.name), merged_pdf=str(merged_pdf.name),
    merged_pages=len(PdfReader(str(merged_pdf)).pages),
    all=all_s, h_ge_50=ge50, h_eq_25=h25), indent=2, ensure_ascii=False))
