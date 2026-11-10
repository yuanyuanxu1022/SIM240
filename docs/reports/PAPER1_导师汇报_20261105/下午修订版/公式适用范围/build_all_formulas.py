"""List every formula in the first-paper briefing/manuscript, then explain them in separate tables.

Only existing formulas are transcribed from:
  - PPT page 6/21 (the screenshot the user supplied)
  - SIM240_中文稿_导师审阅版_20261022.md  eq.(1)-(7), appendix E (E1)-(E6)
  - Correction_formula_derivation_20261023/DERIVATION.md  eq.(4)-(17)
No new derivation result, no refit, no solver, no threshold change.
Outputs an editable Markdown and a 4-page projection PDF.
"""
from pathlib import Path
import os, tempfile, csv, json, html, re

B = Path(__file__).resolve().parent
_TMP = B / '_tmp'
_TMP.mkdir(exist_ok=True)
os.environ.setdefault('TMPDIR', str(_TMP))
tempfile.tempdir = str(_TMP)

from weasyprint import HTML

ROOT = B.parents[4]
CN = ROOT / 'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
DER = ROOT / 'docs/reports/Correction_formula_derivation_20261023/DERIVATION.md'
SRC_CSV = ROOT / 'docs/reports/PAPER1_claim_evidence_review_20261105/recomputed_36_points.csv'

# ---------------------------------------------------------------- hard checks
cn = CN.read_text()
der = DER.read_text()
rows = list(csv.DictReader(SRC_CSV.open()))

def kmod(h, d, direc):
    H = h + d
    return (H**3 + h**3) / 24 if direc == 'parallel' else (H**3 * h**3) / (6 * (H**3 + h**3))

e_kmod = e_E = e_r = e_F = 0.0
for r in rows:
    h, d = float(r['h_nm']) * 1e-9, float(r['d_nm']) * 1e-9
    km, kr = float(r['K_model_m3']), float(r['K_ref_m3'])
    F, E, rr = float(r['F_V2_published']), float(r['E_percent']) / 100, float(r['V2_residual_percent']) / 100
    e_kmod = max(e_kmod, abs(kmod(h, d, r['direction']) / km - 1))
    e_E = max(e_E, abs(km / kr - 1 - E))
    e_r = max(e_r, abs((F * (1 + E) - 1) - rr))
    beta = float(r['d_nm']) / 120.0
    pred = 1 / (1 + 1.7685 * beta**1.6331) if r['direction'] == 'parallel' else 1 / (1 + 0.4900 * beta**0.6990)
    e_F = max(e_F, abs(F / pred - 1))

checks = {
    'source_has_eq3': '\\frac{1}{24}' in cn and '\\frac{1}{6}' in cn,
    'source_has_V2_coeffs': all(s in cn for s in ('1.7685', '1.6331', '0.4900', '0.6990')),
    'source_has_dt': '4.1667' in cn,
    'derivation_has_homogeneity': '\\lambda^3K_i' in der,
    'derivation_has_bounds': '\\frac{h^3}{12}\\le K_i\\le K_i^{LC}' in der,
    'eq3_numeric_36pts': e_kmod < 1e-12,
    'E_definition_36pts': e_E < 1e-12,
    'r_equals_F_times_1plusE_36pts': e_r < 1e-12,
    'eq6_F_36pts': e_F < 1e-12,
}
assert all(checks.values()), checks

# ---------------------------------------------------------------- formula master list
# (编号, 公式(纯文本), 公式(HTML), 名称, 回答什么问题, 出处)
F = [
 ('正文式(1)', 'Δt = (τ − 1/2)·Δx² / (3ν) = 4.1667×10⁻¹² s；ν* = c_s²(τ − 1/2) = 1/6',
  'Δt = (τ − 1/2)·Δx<sup>2</sup> / (3ν) = 4.1667×10<sup>−12</sup> s<br>ν* = c<sub>s</sub><sup>2</sup>(τ − 1/2) = 1/6',
  '格子时间步', '给定网格与黏度后，一步算多长', '正文 §2.1；汇报第 6 页'),
 ('正文式(2)', 'J_i = (1/A_plan)∫_Ω u_i dV；K_i = μJ_i/G_i；G_i = ρa_i',
  'J<sub>i</sub> = (1/A<sub>plan</sub>)∫<sub>Ω</sub> u<sub>i</sub> dV<br>K<sub>i</sub> = μJ<sub>i</sub>/G<sub>i</sub>；G<sub>i</sub> = ρa<sub>i</sub>',
  '通量与导度定义', '模拟算出的速度怎么变成一个可比的数字', '正文 §2.2'),
 ('换算式', 'J_i = H_ref⟨u_i⟩；K_i = H_ref κ_i；H_ref = h + d/2',
  'J<sub>i</sub> = H<sub>ref</sub>⟨u<sub>i</sub>⟩；K<sub>i</sub> = H<sub>ref</sub> κ<sub>i</sub>；H<sub>ref</sub> = h + d/2',
  '导度 ↔ 渗透率', '和文献的 m² 渗透率怎么换算（必须统一参考高度）', '正文 §2.2'),
 ('局部平板', 'k_shallow = h³/12；k_deep = (h+d)³/12',
  'k<sub>shallow</sub> = h<sup>3</sup>/12；k<sub>deep</sub> = (h+d)<sup>3</sup>/12',
  '两块平板的立方律', '最基础的积木：平板流量随间隙三次方变', '正文 §2.3'),
 ('正文式(3) / 汇报①', 'K_yy^mod = [(h+d)³ + h³]/24；K_xx^mod = (h+d)³h³ / {6[(h+d)³+h³]}',
  'K<sub>yy</sub><sup>mod</sup> = [(h+d)<sup>3</sup> + h<sup>3</sup>]/24<br>K<sub>xx</sub><sup>mod</sup> = (h+d)<sup>3</sup>h<sup>3</sup> / {6[(h+d)<sup>3</sup>+h<sup>3</sup>]}',
  '原局部立方律（待检验）', '不用模拟、手算就能估两个方向导度', '正文 §2.3 / 式(3)；汇报第 6 页①'),
 ('汇报②', 'K = νJ/a', 'K = νJ/a',
  'OpenLB 显式沟槽基准 (5 nm)', '不输入任何公式，直接按真实沟槽几何求通量', '汇报第 6 页②；与式(2)代数等价'),
 ('正文式(4) / 汇报误差定义', 'E_i = K^mod/K^ref − 1；r_i = F·K^mod/K^ref − 1；E = (K模型/K参考 − 1)×100%',
  'E<sub>i</sub> = K<sup>mod</sup>/K<sup>ref</sup> − 1<br>r<sub>i</sub> = F·K<sup>mod</sup>/K<sup>ref</sup> − 1',
  '偏差与残差', '原公式差多少、修正后还剩多少', '正文 §2.3 / 式(4)；汇报第 6 页'),
 ('正文式(5)', 'tanβ = (K_xx/K_yy)·tanθ；A = K_yy/K_xx',
  'tanβ = (K<sub>xx</sub>/K<sub>yy</sub>)·tanθ；A = K<sub>yy</sub>/K<sub>xx</sub>',
  '线性张量重建流向', '导度之比错了，预测的流动方向会偏多少', '正文 §4.3 / 式(5)'),
 ('正文式(6) / 汇报③', 'F_yy^V2 = 1/[1 + 1.7685(d/w)^1.6331]；F_xx^V2 = 1/[1 + 0.4900(d/w)^0.6990]',
  'F<sub>yy</sub><sup>V2</sup> = 1/[1 + 1.7685(d/w)<sup>1.6331</sup>]<br>F<sub>xx</sub><sup>V2</sup> = 1/[1 + 0.4900(d/w)<sup>0.6990</sup>]',
  'V2 乘性修正因子', '把原公式乘一个小于 1 的数，压掉高估', '正文 §4.4 / 式(6)；汇报第 6 页③'),
 ('正文式(7)', 'K_yy·p_ξξ + K_xx·p_ηη = −μV',
  'K<sub>yy</sub>·p<sub>ξξ</sub> + K<sub>xx</sub>·p<sub>ηη</sub> = −μV',
  '降阶挤压模型方程', '导度误差会怎么传进压印压力/荷载预测（仅讨论，未验证）', '正文 §5.2 / 式(7)'),
 ('推导式 D1', 'K_i = h³κ_i(s,t;φ)，s=w/h、t=d/h；K_i(λw,λh,λd) = λ³K_i(w,h,d)',
  'K<sub>i</sub> = h<sup>3</sup>κ<sub>i</sub>(s,t;φ)，s=w/h、t=d/h<br>K<sub>i</sub>(λw,λh,λd) = λ<sup>3</sup>K<sub>i</sub>(w,h,d)',
  '长度三次齐次性', '为什么适用范围要写比例 h/w、d/w 而不是纳米数', 'DERIVATION.md 式(4)(5)'),
 ('推导式 D2', 'K_∥^LC = [(1−φ)h³ + φ(h+d)³]/12；K_⊥^LC = 1/{12[(1−φ)h⁻³ + φ(h+d)⁻³]}',
  'K<sub>∥</sub><sup>LC</sup> = [(1−φ)h<sup>3</sup> + φ(h+d)<sup>3</sup>]/12<br>K<sub>⊥</sub><sup>LC</sup> = 1/{12[(1−φ)h<sup>−3</sup> + φ(h+d)<sup>−3</sup>]}',
  '一般槽宽占比的立方律', 'φ=0.5 时即退化为正文式(3)', 'DERIVATION.md 式(6)(7)'),
 ('推导式 D3', 'F_i = K_i/K_i^LC；C_i = 1/F_i；Δ_i = C_i − 1 = K_i^LC/K_i − 1',
  'F<sub>i</sub> = K<sub>i</sub>/K<sub>i</sub><sup>LC</sup>；C<sub>i</sub> = 1/F<sub>i</sub>；Δ<sub>i</sub> = K<sub>i</sub><sup>LC</sup>/K<sub>i</sub> − 1',
  '导度修正 / 阻力修正 / 超额阻力', '三个说法是同一个量的不同写法，别混用', 'DERIVATION.md 式(8)(9)'),
 ('推导式 D4', 'K_i = K_i^LC/(1+Δ_i)；R_i = (μ/K_i^LC)(1+Δ_i)',
  'K<sub>i</sub> = K<sub>i</sub><sup>LC</sup>/(1+Δ<sub>i</sub>)；R<sub>i</sub> = (μ/K<sub>i</sub><sup>LC</sup>)(1+Δ<sub>i</sub>)',
  '修正的代入形式', '阻力乘 (1+Δ)，导度除 (1+Δ)', 'DERIVATION.md 式(9)'),
 ('推导式 D5', 'lnΔ_i = a + b·lnβ + c·lnα + q(lnα)²，α=h/w、β=d/w',
  'lnΔ<sub>i</sub> = a + b·lnβ + c·lnα + q(lnα)<sup>2</sup>，α=h/w、β=d/w',
  'C4 经验闭合（既有拟合）', '四项形式是经验近似，不是 Stokes 方程唯一强制', 'DERIVATION.md 式(10)'),
 ('推导式 D6', 'F_i(w,h,d) = [1 + A(d/h)^b (h/w)^p exp{−r[ln(w/h)]²}]⁻¹',
  'F<sub>i</sub>(w,h,d) = [1 + A(d/h)<sup>b</sup> (h/w)<sup>p</sup> exp{−r[ln(w/h)]<sup>2</sup>}]<sup>−1</sup>',
  '同时输入 w,h,d 的显式式', '与式(10)严格代数等价（相对差 ≤1.11×10⁻¹⁵）', 'DERIVATION.md 式(11)(12)'),
 ('推导式 D7', 'h³/12 ≤ K_i ≤ K_i^LC；[h³/12]/K_i^LC ≤ F_i ≤ 1；K_⊥ ≤ K_∥',
  'h<sup>3</sup>/12 ≤ K<sub>i</sub> ≤ K<sub>i</sub><sup>LC</sup><br>[h<sup>3</sup>/12]/K<sub>i</sub><sup>LC</sup> ≤ F<sub>i</sub> ≤ 1；K<sub>⊥</sub> ≤ K<sub>∥</sub>',
  '理想 Stokes 物理上下界', '为什么原式必然高估；只定方向，不定偏差幅度', 'DERIVATION.md 式(15)；附录 E 式(E6)'),
 ('推导式 D8', '5/24 ≤ α = h/w ≤ 25/24；5/24 ≤ β = d/w ≤ 1（外包矩形，非已验证矩形）',
  '5/24 ≤ α = h/w ≤ 25/24；5/24 ≤ β = d/w ≤ 1',
  '比例域（适用范围）', '公式在哪片几何内插值有效；域内仍不保证精度', 'DERIVATION.md 式(17)；§6'),
 ('附录E 式(E1)', '−ΔU + ∇Π = e_i；∇·U = 0；K_i = (1/P)∫_Ω U_i dA',
  '−ΔU + ∇Π = e<sub>i</sub>；∇·U = 0；K<sub>i</sub> = (1/P)∫<sub>Ω</sub> U<sub>i</sub> dA',
  '无量纲 Stokes 弱解', '把流动写成能量极小问题', '附录 E'),
 ('附录E 式(E2)', 'D = ∫_Ω|∇U|² dA = ∫_Ω U_i dA = P·K_i',
  'D = ∫<sub>Ω</sub>|∇U|<sup>2</sup> dA = ∫<sub>Ω</sub> U<sub>i</sub> dA = P·K<sub>i</sub>',
  '能量恒等式', '耗散 = 通量 = 导度', '附录 E'),
 ('附录E 式(E3)', '∫₀^H |∂_z U_i|² dz ≥ 12q_i²/H³',
  '∫<sub>0</sub><sup>H</sup>|∂<sub>z</sub>U<sub>i</sub>|<sup>2</sup> dz ≥ 12q<sub>i</sub><sup>2</sup>/H<sup>3</sup>',
  '截面耗散下界', '平板是"最省力"的速度剖面', '附录 E'),
 ('附录E 式(E4)(E5)', 'K_∥ ≤ ⟨H³⟩/12；K_⊥ ≤ 1/(12⟨H⁻³⟩)',
  'K<sub>∥</sub> ≤ ⟨H<sup>3</sup⟩/12；K<sub>⊥</sub> ≤ 1/(12⟨H<sup>−3</sup>⟩)',
  '两方向导度上界', '等号右边正是式(3)的两个值', '附录 E'),
 ('附录E 式(E6)', 'K_yy ≤ K_yy^mod；K_xx ≤ K_xx^mod',
  'K<sub>yy</sub> ≤ K<sub>yy</sub><sup>mod</sup>；K<sub>xx</sub> ≤ K<sub>xx</sub><sup>mod</sup>',
  '最终结论：原式是上界', '解释了 36/36 全高估的方向，但不给幅度', '附录 E / 式(E6)'),
]

# ---------------------------------------------------------------- Markdown
md = [
 '# 全部公式清单与逐条解释（下午汇报备查）',
 '',
 '> 只转录既有公式，未新增推导结论、未重拟合、未启动求解、未改门槛。',
 '> 出处：汇报第 6 页（三个对象、一个误差定义）；中文稿式(1)–(7)、附录 E 式(E1)–(E6)；',
 '> `Correction_formula_derivation_20261023/DERIVATION.md` 式(4)–(17)。',
 '',
 '**先说一句口径**：本文所有偏差/残差都是「相对于 5 nm 离散数值参考」的回顾性比较，',
 '不是实验误差，也不是连续真解误差。换参考网格，数值本身会变。',
 '',
 '## 表 0　全部公式一览（先列全，后面再分开解释）',
 '',
 '| 编号 | 公式 | 名称 | 它回答什么问题 | 出处 |',
 '|---|---|---|---|---|',
]
for no, m, _h, name, q, src in F:
    md.append(f'| **{no}** | `{m}` | {name} | {q} | {src} |')

md += [
 '',
 '## 表 1　符号与单位（先把字母认全）',
 '',
 '| 符号 | 大白话 | 单位 / 本项目取值 |',
 '|---|---|---|',
 '| h | 凸台与平壁之间最薄的液层间隙 | nm；25 / 50 / 75 / 125 |',
 '| d | 槽深 | nm；25 / 50 / 75 / 100 / 120 |',
 '| w | 槽宽 | nm；固定 120 |',
 '| P | 一个沟槽的周期 | nm；240（P = 2w） |',
 '| φ | 槽宽占周期的比例 | 0.5（固定） |',
 '| α / β | 无量纲比例 h/w、d/w | 真正决定公式准不准的自变量 |',
 '| K | 深度积分导度，越大越容易流 | **m³**（不是 m² 渗透率） |',
 '| κ | 通常意义的渗透率 | m²；K = H_ref·κ |',
 '| H_ref | 平均液层厚度 | h + d/2 |',
 '| J | 单位平面面积的体积通量 | m²/s |',
 '| G | 等效驱动强度 | Pa/m；G = ρa |',
 '| μ / ν / ρ | 动力黏度 / 运动黏度 / 密度 | 1 mPa·s / 1×10⁻⁶ m²/s / 1000 kg/m³ |',
 '| a | 施加的体积加速度 | 1×10⁵ m/s² |',
 '| τ / Δx / Δt | 松弛时间 / 网格 / 时间步 | 1 / 5 nm / 4.1667×10⁻¹² s |',
 '| F | V2 乘性修正因子 | 无量纲，恒 < 1 |',
 '| E / r | 原公式偏差 / 修正后残差 | 正=高估导度（=低估阻力） |',
 '| A / θ / β_dir | 各向异性比 / 驱动角 / 通量角 | A = K_yy/K_xx |',
 '| V | 模具闭合速度 | m/s；V = −ḣ > 0（仅 §5.2 讨论） |',
 '',
 '## 表 2　① 原局部立方律：怎么来的（分开解释）',
 '',
 '| 步骤 | 式子 | 为什么这么做 | 局限 |',
 '|---|---|---|---|',
 '| 1 | k_shallow = h³/12、k_deep = (h+d)³/12 | 把浅区、深区各当成一块无限宽平板；平板导度是间隙的三次方 | 忽略侧壁 |',
 '| 2 | 沿槽取**算术**平均 → [(h+d)³+h³]/24 | 两区并排同时过流，相当于并联 | 忽略深浅交界处的重分布 |',
 '| 3 | 横槽取**调和**平均 → (h+d)³h³/{6[(h+d)³+h³]} | 液体要依次穿过两区，相当于串联 | 同上 |',
 '| 4 | 令 d = 0，两式都退回 h³/12 | 与平板解析解自洽，是基本一致性检查 | 只验证了这个退化情形 |',
 '| 结论 | 式(3) 是**待检验的近似**，不是精确解 | 附录 E 证明它在理想 Stokes 下是导度**上界** | 只定"必然高估"的方向，不给偏差幅度 |',
 '',
 '## 表 3　② 数值基准 K：怎么算（分开解释）',
 '',
 '| 步骤 | 式子 | 说明 |',
 '|---|---|---|',
 '| 1 | J_i = (1/A_plan)∫_Ω u_i dV | 把速度场沿驱动方向做体积分，再除以单胞平面面积 → m²/s |',
 '| 2 | K_i = μJ_i/G_i，G_i = ρa_i | 乘黏度、除驱动 → m³ |',
 '| 3 | **K = νJ/a**（汇报第 6 页写法） | 与上式**代数等价**：μ/G = ρν/(ρa) = ν/a |',
 '| 4 | K_i = H_ref κ_i | 与文献 m² 渗透率换算；必须统一 H_ref = h+d/2 |',
 '| 5 | 对照 | K^ref 是 5 nm 网格的**离散结果**；不输入式(3) 或 V2 的任何系数 |',
 '',
 '**关键点**：截图上「不输入原公式或 V2 的系数」这句话的分量就在这里——',
 'K^ref 独立算出来，才能当尺子去量原公式。但尺子本身还要过网格与来源检查（第 3 章、S4）。',
 '',
 '## 表 4　③ V2 修正因子（分开解释）',
 '',
 '| 项 | 内容 |',
 '|---|---|',
 '| 公式 | F_yy = 1/[1+1.7685(d/w)^1.6331]；F_xx = 1/[1+0.4900(d/w)^0.6990] |',
 '| 怎么用 | K^V2 = F · K^mod（在原公式上乘一个恒小于 1 的数） |',
 '| 变量 | **只有 d/w**，没有显式 h；但总导度 K^mod 本身含 h，所以"总公式仍含 h" |',
 '| 系数来源 | 既有 18 组几何的回顾性拟合（2026-10-22），18 个 P 点、18 个 T 点分别拟合；本轮未重估 |',
 '| 性质 | 四项对数形式是**经验近似**：不是完整二阶 Taylor（缺交叉项、ln²β），也不是 Stokes 唯一强制 |',
 '| 效果 | 原公式偏差 +8.11%~+204.85% → 残差沿槽最大 10.5%、横槽 18.7%；h≥50 的 15 个横槽点 6.9% |',
 '| 反例 | h25/d100 横槽：5 nm 参考下 16.36% → −18.71%（反而变差）；换 2.5 nm 参考又变好 |',
 '| 不能说 | "全部点改善""V2 精度 ≤6.9%""新几何预测已验证"；残差来源（模型形式/拟合/参考网格）尚未分离 |',
 '',
 '## 表 5　误差 E 与残差 r（分开解释）',
 '',
 '| 项 | 内容 |',
 '|---|---|',
 '| 定义 | E = K^mod/K^ref − 1（×100% 即百分数）；r = F·K^mod/K^ref − 1 |',
 '| 符号 | **正 = 高估导度 = 低估阻力**；负 = 低估导度 |',
 '| 参照 | K^ref 是同几何、同方向、**同网格**的 5 nm 离散值 |',
 '| 两者关系 | **r = F(1+E) − 1**（由定义直接代数得到，36 点数值核对一致，最大差 2.2×10⁻¹⁶） |',
 '| 为什么重要 | 这一个式子解释了"修正后为什么有的点变好、有的点变差、甚至变号" |',
 '| 换参考会变 | 四个双网格几何中，换 2.5 nm 参考使 E 变化 0.37–5.39 个百分点；最坏 h25/d100 横槽 16.36%→21.76% |',
 '| 不能说 | 这些百分比不是相对真实连续流动的误差，不是全域精度界，也不是实验误差 |',
 '',
 '## 表 6　公式之间的换算关系（把三块拼成一条线）',
 '',
 '| 从 | 到 | 关系 | 核对 |',
 '|---|---|---|---|',
 '| 式(2) K=μJ/G | 汇报② K=νJ/a | 因 μ=ρν、G=ρa ⇒ μ/G = ν/a，**同一个式子** | 代数恒等 |',
 '| 平板立方律 | 式(3) | 算术/调和平均 | d=0 退回 h³/12 |',
 '| 式(3) | 式(4) 的 E | E = K^mod/K^ref − 1 | 36 点最大差 5.6×10⁻¹⁷ |',
 '| 式(3) | 式(2) 的 K_model | K_model 就是式(3) 的值 | 36 点最大相对差 6.7×10⁻¹⁶ |',
 '| 式(6) F | 式(4) 的 r | r = F(1+E) − 1 | 36 点最大差 2.2×10⁻¹⁶ |',
 '| 式(3)(6) | V2 预测 | K^V2 = F·K^mod | 36 点 F 与式(6) 相对差 0 |',
 '| F / C / Δ | 三种叫法 | C = 1/F；Δ = 1/F − 1 = K^LC/K − 1 | 阻力乘 (1+Δ)，导度除 (1+Δ) |',
 '| K / κ | 单位换算 | K = H_ref·κ；R = μ/K | 与 OpenFOAM 的 d_i = H/K_i 同源 |',
 '',
 '## 表 7　适用范围（分开解释）',
 '',
 '| 层面 | 内容 |',
 '|---|---|',
 '| 物理前提 | 单相牛顿液体、完全充液、固定间隙、无滑移、周期矩形直槽、低 Re 的 Stokes 模型；φ = w/P = 0.5、P = 2w |',
 '| 为什么写比例 | 式 D1：K = w³·κ(h/w, d/w)，整体放大 λ 倍则 K 放大 λ³ 倍 ⇒ 真正自变量是 α=h/w、β=d/w |',
 '| 几何域 | 5/24 ≤ α ≤ 25/24、5/24 ≤ β ≤ 1 是**外包矩形**；实际采用 18 点在 lnα–lnβ 平面的**凸包**做保守内插筛选 |',
 '| 缺格 | h=25 nm 只算 3 个槽深（缺 d=75、120），凸包不是完整矩形 |',
 '| 精度 | 仅回顾性：V2 最大|残差| 沿槽 18 点 10.5%、横槽 18 点 18.7%；h≥50 nm 的 15 个横槽点 6.9% |',
 '| 域内 ≠ 保证 | 原始 domain_note 明写 "membership does not guarantee prediction accuracy" |',
 '| 域外 | 超出凸包即外推；改 w 或 φ 只能用相似映射 h₀=120h/w、d₀=120d/w 定位比例位置，**不等于已有 DNS 记录**，仍需重新验证 |',
 '| 已知越界反例 | h75/w120/d10000 nm 时，C4 给横槽 K 约为平板值的 0.114，违反下界 ⇒ 不能当任意槽深的全域公式 |',
 '',
 '## 表 8　S4 判断（公式精度能不能往下走）',
 '',
 '| 项 | 沿槽 P | 横槽 T |',
 '|---|---|---|',
 '| 事先门槛 | 中—细变化 ≤1% **且** 细网格 GCI ≤1%（r=2, Fs=1.25） | 同左 |',
 '| 观测阶 p | 1.673 | 1.496 |',
 '| 中—细变化 | 0.165%　PASS | **1.328%　FAIL** |',
 '| 细网格 GCI | 0.094%　PASS | 0.912%　通过，但不抵补前一项 |',
 '| 方向判定 | PASS | **FAIL** |',
 '',
 '阶段判定：GRID_CHECKS_PASS=false、S4_STAGE_ACCEPTED=false、reference_qualified=false；',
 'S5 未启动，MODEL_COMPARISON / physical_validation 未评价。',
 '三条不能做：把 1% 改成 2%；只挑 GCI 通过项；因六条已算完补写 S4_completed.json。',
 '',
 '**与公式适用范围的关系**：0.625 nm 补的是「薄间隙严格参考」这条线，',
 '不改变 18 组数据的覆盖形状，也不扩大公式适用域；两条线不能互相替代。',
 '',
 '## 表 9　公式 → 结论对应（接证据链总表）',
 '',
 '| 公式 | 支撑哪条结论 | 边界 |',
 '|---|---|---|',
 '| 式(3) + 式(4) | 36/36 全部高估，沿槽 +10.30~+204.85%、横槽 +8.11~+54.19% | 相对 5 nm 离散参考 |',
 '| 式(6) + 式(4) | V2 把最坏偏差降到 10.5% / 18.7% | 回顾性，非独立预测 |',
 '| 式(5) | 各向异性 2.21→3.70（高估 67%）、45° 流向差 −9.20° | 线性张量重建，非实验流向 |',
 '| 式(E4)(E5)(E6) | 理想 Stokes 下原式是上界，解释高估方向 | 不给幅度、不给比值符号 |',
 '| 式 D1 / 式(17) | 适用范围写成比例域而非绝对尺寸 | 域内不保证精度 |',
 '| 式(7) | 主值误差会传进降阶挤压模型的压力/荷载 | 仅模型含义讨论，未验证动态过程 |',
 '',
 '## 证据入口（相对 docs/reports）',
 '',
 '- `SIM240_中文稿_导师审阅版_20261022.md` 式(1)–(7)、附录 E',
 '- `Correction_formula_derivation_20261023/DERIVATION.md`、`coefficients_and_domain.json`',
 '- `PAPER1_claim_evidence_review_20261105/recomputed_36_points.csv`（36 点复算）',
 '- `URV_S4_completed_review_20261104_143205/REPORT.md` §5',
 '- 同目录 `证据链总表_下午汇报.md`、`全部公式_数值核对.json`',
 '',
]
(B / '全部公式清单与逐条解释_下午汇报.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

(B / '全部公式_数值核对.json').write_text(json.dumps(dict(
    note='Transcription/consistency checks only; no new derivation result',
    n_points=len(rows), checks=checks,
    max_rel_diff_K_model_vs_eq3=e_kmod,
    max_abs_diff_E_definition=e_E,
    max_abs_diff_r_vs_F_times_1plusE=e_r,
    max_rel_diff_F_vs_eq6=e_F), indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

# ---------------------------------------------------------------- PDF
W, H = 1280, 720
BLUE, NAVY = '#1E4FA8', '#12294D'
PANEL, LIGHT = '#F7F9FC', '#E8EFF8'
TEXT, SUB, MUT, LINE = '#1A2230', '#4A5568', '#8B97A8', '#D6DCE5'
RED_BG, GRN_BG = '#FBECEC', '#EAF3EC'


def table(headers, body, widths, cls=''):
    cols = ''.join(f'<col style="width:{w}%">' for w in widths)
    th = ''.join(f'<th>{h}</th>' for h in headers)
    tr = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in body)
    return f'<table class="{cls}">{cols}<thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'


def box(left, top, width, height, inner, bg='white', border=None, radius=0):
    bd = f'border:1px solid {border};' if border else ''
    return (f'<div class="box" style="left:{left}px;top:{top}px;width:{width}px;'
            f'height:{height}px;background:{bg};{bd}border-radius:{radius}px;'
            f'padding:9px 12px;">{inner}</div>')


def page(title, num, parts, note, total=6):
    return ('<div class="slide"><div class="topbar"></div>'
            f'<div class="tag">补充 · 全部公式清单与解释 {num} / {total}</div>'
            f'<div class="title">{title}</div><div class="hr1"></div>'
            + ''.join(parts)
            + '<div class="hr2"></div>'
            f'<div class="foot">{note}</div><div class="pageno">公式页 {num} / {total}</div></div>')


def master_table(items):
    body = [[f'<b>{html.escape(no)}</b>', h,
             f'<b>{html.escape(name)}</b><br><span class="sm">{html.escape(q)}　｜　{html.escape(src)}</span>']
            for no, _m, h, name, q, src in items]
    return table(['编号', '公式', '名称 / 回答什么 / 出处'], body, [12, 58, 30], cls='fm2')


# ---- pages 1-3: all 23 formulas, split three ways so nothing is clipped
p1 = page('表 0（1/3）　全部公式一览：定义与三个对象', 1, [
    '<div class="sec" style="left:45px;top:130px;width:1190px">'
    '汇报第 6 页的「三个对象＋一个误差定义」＋ 中文稿 §2 的定义式（共 8 条）</div>',
    box(45, 156, 1190, 480, master_table(F[:8]), bg='white'),
], '出处：汇报第 6/21 页；中文稿 §2.1–2.3、式(1)–(4)。本页只转录，不新增推导结论。')

p1b = page('表 0（2/3）　全部公式一览：结果式与相似性', 2, [
    '<div class="sec" style="left:45px;top:130px;width:1190px">'
    '中文稿 §4–§5 的结果式、挤压模型式，以及推导文档的相似性与一般 φ 立方律（共 8 条）</div>',
    box(45, 156, 1190, 480, master_table(F[8:16]), bg='white'),
], '出处：中文稿式(5)–(7)；DERIVATION.md 式(4)–(9)。')

p1c = page('表 0（3/3）　全部公式一览：经验闭合、上下界与附录 E', 3, [
    '<div class="sec" style="left:45px;top:130px;width:1190px">'
    'C4 经验闭合与显式 F(w,h,d)、物理上下界、比例域，以及附录 E 的上界证明（共 7 条）</div>',
    box(45, 156, 1190, 480, master_table(F[16:]), bg='white'),
], '出处：DERIVATION.md 式(10)–(17)；中文稿附录 E 式(E1)–(E6)。')

# ---- page 2: symbols + object 1 and 2
sym = [
 ['h / d', '最薄间隙 / 槽深', 'nm；h=25/50/75/125，d=25~120'],
 ['w / P / φ', '槽宽 / 周期 / 槽宽占比', 'w=120 nm、P=240 nm、φ=0.5 固定'],
 ['α / β', '比例 h/w、d/w', '真正决定公式准不准的自变量'],
 ['K / κ', '深度积分导度 / 渗透率', 'K 单位 m³，κ 单位 m²；K=H_ref·κ'],
 ['H_ref', '平均液层厚度', 'h + d/2'],
 ['J / G / a', '通量 / 驱动强度 / 加速度', 'm²/s、Pa/m、1×10⁵ m/s²'],
 ['μ / ν / ρ', '动力黏度 / 运动黏度 / 密度', '1 mPa·s / 1×10⁻⁶ m²/s / 1000 kg/m³'],
 ['τ / Δx / Δt', '松弛时间 / 网格 / 时间步', '1 / 5 nm / 4.1667×10⁻¹² s'],
 ['F / E / r', 'V2 因子 / 偏差 / 残差', '正 E = 高估导度 = 低估阻力'],
 ['A / θ / β_dir', '各向异性 / 驱动角 / 通量角', 'A = K_yy/K_xx'],
]
t_sym = table(['符号', '大白话', '单位 / 取值'], [[html.escape(a), html.escape(b), html.escape(c)] for a, b, c in sym],
              [17, 38, 45], cls='sm2')

t_obj1 = table(['步骤', '式子', '为什么 / 局限'], [
 ['1', 'k_shallow = h³/12；k_deep = (h+d)³/12', '把浅区、深区各当无限宽平板；忽略侧壁'],
 ['2', '沿槽 K_yy = [(h+d)³+h³]/24', '两区并排同时过流 → 算术平均（并联）'],
 ['3', '横槽 K_xx = (h+d)³h³/{6[(h+d)³+h³]}', '液体依次穿过两区 → 调和平均（串联）'],
 ['4', 'd = 0 时两式都退回 h³/12', '与平板解析解自洽；只验证这一退化情形'],
 ['结论', '式(3) 是待检验近似，不是精确解', '附录 E 证明它在理想 Stokes 下是导度上界；只定方向，不给幅度'],
], [9, 42, 49], cls='sm2')

t_obj2 = table(['步骤', '式子', '说明'], [
 ['1', 'J_i = (1/A_plan)∫_Ω u_i dV', '速度场做体积分、除单胞面积 → m²/s'],
 ['2', 'K_i = μJ_i/G_i，G_i = ρa_i', '乘黏度、除驱动 → m³'],
 ['3', '<b>K = νJ/a</b>（汇报第 6 页）', '<b>与上式代数等价</b>：μ/G = ρν/(ρa) = ν/a'],
 ['4', 'K_i = H_ref κ_i', '与文献 m² 渗透率换算，须统一 H_ref = h+d/2'],
 ['5', 'K^ref 不输入式(3) 或 V2 系数', '独立算出来才能当尺子；尺子本身仍需网格与来源检查'],
], [9, 40, 51], cls='sm2')

sym_extra = ('<div class="ct" style="margin-top:9px;color:' + BLUE + '">先把三个对象分清</div>'
             '<div class="txt2" style="font-size:10.2px;line-height:1.42">'
             '<b>① 原公式</b>手算、待检验；<b>② OpenLB</b>独立算、当尺子 K<sup>ref</sup>；'
             '<b>③ V2</b>在①上乘 F、属回顾性修正。<br>'
             '<b>E</b>＝①比②；<b>r</b>＝③比②。三者不是三种算法，也不是三批独立数据。<br>'
             '<b>单位</b>：K 是 m³（深度积分导度），κ 是 m²，两者差一个 H<sub>ref</sub>；'
             '引用文献前须核对对方用哪个参考高度。</div>')
p2 = page('表 1–3　符号先认全；① 原公式与 ② 数值基准分开解释', 4, [
    box(45, 132, 400, 355, '<div class="ct">表 1　符号与单位</div>' + t_sym,
        bg=PANEL, border=LINE, radius=3),
    box(45, 497, 400, 137, sym_extra, bg=LIGHT, border='#C9D9F0', radius=3),
    box(455, 132, 780, 226, '<div class="ct">表 2　① 原局部立方律：怎么来的</div>' + t_obj1, bg='white', border=LINE, radius=3),
    box(455, 368, 780, 266, '<div class="ct">表 3　② OpenLB 显式沟槽基准：怎么算</div>' + t_obj2, bg='white', border=LINE, radius=3),
], '关键点：截图「不输入原公式或 V2 系数」的分量在于 K^ref 独立算出；但 K=νJ/a 与正文 K=μJ/G 是同一个式子。')

# ---- page 3: object 3 + error definition + conversion
t_obj3 = table(['项', '内容'], [
 ['公式', 'F_yy = 1/[1+1.7685(d/w)<sup>1.6331</sup>]；F_xx = 1/[1+0.4900(d/w)<sup>0.6990</sup>]'],
 ['怎么用', 'K<sup>V2</sup> = F · K<sup>mod</sup>；F 恒 &lt; 1，把原公式的高估压下来'],
 ['变量', '<b>只有 d/w</b>，未显式含 h；但 K<sup>mod</sup> 本身含 h ⇒「总导度仍含 h」'],
 ['系数来源', '既有 18 组几何回顾性拟合（2026-10-22），P/T 各 18 点分别拟合；本轮未重估'],
 ['性质', '四项对数形式是<b>经验近似</b>：不是完整二阶 Taylor，也不是 Stokes 唯一强制'],
 ['效果', '偏差 +8.11%~+204.85% → 残差沿槽 10.5% / 横槽 18.7%；h≥50 的 15 个横槽点 6.9%'],
 ['反例', 'h25/d100 横槽：5 nm 参考 16.36% → −18.71%（变差）；换 2.5 nm 参考又变好'],
 ['不能说', '「全部点改善」「V2 精度 ≤6.9%」「新几何预测已验证」；残差来源尚未分离'],
], [15, 85], cls='sm2')

t_err = table(['项', '内容'], [
 ['定义', 'E = K<sup>mod</sup>/K<sup>ref</sup> − 1（×100%）；r = F·K<sup>mod</sup>/K<sup>ref</sup> − 1'],
 ['符号', '<b>正 = 高估导度 = 低估阻力</b>；负 = 低估导度'],
 ['参照', 'K<sup>ref</sup> 是同几何、同方向、<b>同网格</b>的 5 nm 离散值'],
 ['两者关系', '<b>r = F(1+E) − 1</b>；36 点核对一致（最大差 2.2×10⁻¹⁶）'],
 ['为什么重要', '这一式解释了修正后「有的变好、有的变差、甚至变号」'],
 ['换参考会变', '4 个双网格几何换 2.5 nm 参考，E 变 0.37–5.39 个百分点'],
 ['不能说', '不是相对连续真解的误差、不是全域精度界、不是实验误差'],
], [17, 83], cls='sm2')

t_conv = table(['从 → 到', '关系', '核对'], [
 ['式(2) K=μJ/G → 汇报② K=νJ/a', 'μ=ρν、G=ρa ⇒ μ/G=ν/a，<b>同一个式子</b>', '代数恒等'],
 ['平板立方律 → 式(3)', '算术 / 调和平均', 'd=0 退回 h³/12'],
 ['式(3) → K_model', 'K_model 就是式(3) 的值', '36 点最大相对差 6.7×10⁻¹⁶'],
 ['式(3)(4) → E', 'E = K<sup>mod</sup>/K<sup>ref</sup> − 1', '36 点最大差 5.6×10⁻¹⁷'],
 ['式(6) → r', 'r = F(1+E) − 1', '36 点最大差 2.2×10⁻¹⁶'],
 ['F / C / Δ', 'C = 1/F；Δ = 1/F − 1 = K<sup>LC</sup>/K − 1', '导度除 (1+Δ)，阻力乘 (1+Δ)'],
], [34, 46, 20], cls='sm2')

p3 = page('表 4–6　③ V2 因子、误差定义、公式之间怎么拼', 5, [
    box(45, 132, 590, 272, '<div class="ct">表 4　③ V2 乘性修正因子</div>' + t_obj3, bg=PANEL, border=LINE, radius=3),
    box(645, 132, 590, 272, '<div class="ct">表 5　误差 E 与残差 r</div>' + t_err, bg=GRN_BG, border='#BFD9C6', radius=3),
    box(45, 412, 1190, 222, '<div class="ct">表 6　公式之间的换算关系（把三块拼成一条线；数值均已核对）</div>' + t_conv,
        bg='white', border=LINE, radius=3),
], '所有核对只复算既有 36 点保存记录，未启动求解、未重拟合、未改门槛。')

# ---- page 4: applicability + S4 + formula->conclusion
t_dom = table(['层面', '内容'], [
 ['物理前提', '单相牛顿、完全充液、固定间隙、无滑移、周期矩形直槽、低 Re Stokes；φ=0.5、P=2w'],
 ['为什么写比例', 'K = w³·κ(h/w,d/w)；整体放大 λ 倍则 K 放大 λ³ 倍 ⇒ 自变量是 α=h/w、β=d/w'],
 ['几何域', '5/24 ≤ α ≤ 25/24、5/24 ≤ β ≤ 1 只是<b>外包矩形</b>；实际用 18 点在 lnα–lnβ 平面的<b>凸包</b>筛选'],
 ['缺格', 'h=25 只算 3 个槽深（缺 d=75、120），凸包不是完整矩形'],
 ['精度', '仅回顾性：V2 最大|残差| 沿槽 10.5%、横槽 18.7%；h≥50 的 15 个横槽点 6.9%'],
 ['域内 ≠ 保证', '原始 domain_note 明写 "membership does not guarantee prediction accuracy"'],
 ['域外', '改 w 或 φ 只能相似映射定位比例位置，<b>不等于已有 DNS 记录</b>，仍需重新验证'],
], [16, 84], cls='sm2')

t_s4 = table(['事先门槛：中—细 ≤1% 且 GCI ≤1%', '沿槽 P', '横槽 T'], [
 ['观测阶 p', '1.673', '1.496'],
 ['中—细变化', '0.165%　PASS', '<b>1.328%　FAIL</b>'],
 ['细网格 GCI', '0.094%　PASS', '0.912%　通过，不抵补前一项'],
 ['<b>方向判定</b>', '<b>PASS</b>', '<b>FAIL</b>'],
], [46, 22, 32], cls='sm2')

t_map = table(['公式', '支撑哪条结论', '边界'], [
 ['式(3)＋式(4)', '36/36 全高估；沿槽 +10.30~+204.85%、横槽 +8.11~+54.19%', '相对 5 nm 离散参考'],
 ['式(6)＋式(4)', 'V2 把最坏偏差降到 10.5% / 18.7%', '回顾性，非独立预测'],
 ['式(5)', '各向异性 2.21→3.70（高估 67%）、45° 流向差 −9.20°', '张量重建，非实验流向'],
 ['式(E4)(E5)(E6)', '理想 Stokes 下原式是上界，解释高估方向', '不给幅度、不给比值符号'],
 ['式 D1 / 式(17)', '适用范围写成比例域而非绝对尺寸', '域内不保证精度'],
 ['式(7)', '主值误差会传进降阶挤压模型的压力 / 荷载', '仅模型含义讨论，未验证'],
], [19, 50, 31], cls='sm2')

p4 = page('表 7–9　适用范围、S4 判断、公式→结论对应', 6, [
    box(45, 132, 590, 268, '<div class="ct">表 7　适用范围</div>' + t_dom, bg=PANEL, border=LINE, radius=3),
    box(645, 132, 590, 268, '<div class="ct" style="color:#B33A36">表 8　S4 判断</div>' + t_s4
        + '<div class="txt2" style="margin-top:8px">阶段判定：GRID_CHECKS_PASS=false、'
          'S4_STAGE_ACCEPTED=false、reference_qualified=false；S5 未启动。<br>'
          '<b>三条不能做</b>：把 1% 改成 2%；只挑 GCI 通过项；补写 S4_completed.json。<br>'
          '0.625 nm 补的是薄间隙严格参考，<b>不扩大公式适用域</b>。</div>',
        bg=RED_BG, border='#E7B9B7', radius=3),
    box(45, 410, 1190, 224, '<div class="ct">表 9　公式 → 结论对应（接证据链总表）</div>' + t_map,
        bg='white', border=LINE, radius=3),
], '被问到时可报 10.5% / 18.7% / 6.9% / 1.328%，但每次补一句：这是同一批 18 组数据回头修正的回顾性残差，不是独立预测精度。')

css = f'''
@font-face{{font-family:NotoCJK;src:url(file:///usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc)}}
@font-face{{font-family:NotoCJK;src:url(file:///usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc);font-weight:700}}
@page{{size:{W}px {H}px;margin:0}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;background:white;font-family:NotoCJK,sans-serif}}
.slide{{width:{W}px;height:{H}px;position:relative;background:white;overflow:hidden;page-break-after:always}}
.slide:last-child{{page-break-after:auto}}
.topbar{{position:absolute;left:0;top:0;width:{W}px;height:13px;background:{BLUE}}}
.tag{{position:absolute;left:45px;top:23px;font-size:12px;color:{MUT}}}
.title{{position:absolute;left:45px;top:50px;width:1190px;font-size:28px;font-weight:700;color:{NAVY};line-height:1.2}}
.hr1{{position:absolute;left:45px;top:115px;width:1190px;height:1px;background:{LINE}}}
.hr2{{position:absolute;left:45px;top:666px;width:1190px;height:1px;background:{LINE}}}
.sec{{position:absolute;font-size:14px;font-weight:700;color:{NAVY};line-height:1.3}}
.box{{position:absolute;overflow:hidden}}
.foot{{position:absolute;left:45px;top:676px;width:1000px;font-size:10.5px;color:{MUT}}}
.pageno{{position:absolute;left:1085px;top:676px;width:150px;text-align:right;font-size:11.5px;color:{BLUE}}}
table{{table-layout:fixed;border-collapse:collapse;width:100%}}
th{{background:{BLUE};color:white;font-size:12px;font-weight:700;padding:5px 7px;text-align:left;border:.5px solid {LINE}}}
td{{font-size:11.2px;color:{TEXT};padding:4px 7px;border:.5px solid {LINE};line-height:1.4;vertical-align:top}}
tbody tr:nth-child(even) td{{background:#FAFCFF}}
table.fm th{{font-size:12.5px;padding:5px 8px}}
table.fm td{{font-size:10.7px;padding:3.5px 8px;line-height:1.35}}
table.fm2 th{{font-size:12.5px;padding:5px 9px}}
table.fm2 td{{font-size:11.5px;padding:5px 9px;line-height:1.35}}
table.sm2 th{{font-size:12px;padding:5px 7px}}
table.sm2 td{{font-size:11px;padding:4.5px 7px;line-height:1.42}}
.sm{{font-size:10px;color:{SUB}}}
.ct{{font-size:13.5px;font-weight:700;color:{NAVY};margin-bottom:6px}}
.txt2{{font-size:10.8px;color:{TEXT};line-height:1.55}}
'''

htmlstr = ('<html><head><meta charset="utf-8"><style>' + css + '</style></head><body>'
           + p1 + p1b + p1c + p2 + p3 + p4 + '</body></html>')
out = B / '全部公式清单与解释.pdf'
HTML(string=htmlstr, base_url=str(B)).write_pdf(str(out))

print(json.dumps(dict(checks=checks, n_formulas=len(F),
                      markdown='全部公式清单与逐条解释_下午汇报.md',
                      pdf=str(out.name), checks_json='全部公式_数值核对.json'),
                 indent=2, ensure_ascii=False))
