from pathlib import Path
import csv
import difflib
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
SUP = ROOT / 'SIM240_Supplementary_Methods_20261024'
CN = ROOT / 'SIM240_中文稿_导师审阅版_20261022.md'
EN = ROOT / 'SIM240_First_Paper_English_20261028.md'
SC = SUP / 'SUPPLEMENTARY_METHODS.md'
SE = SUP / 'SUPPLEMENTARY_METHODS_EN_20261028.md'

def before(path):
    return (OUT / ('before_' + path.name)).read_text()

def replace(text, old, new):
    assert text.count(old) == 1, (old[:90], text.count(old))
    return text.replace(old, new, 1)

def section(text, start, end, new):
    a = text.index(start)
    b = text.index(end, a)
    return text[:a] + new.rstrip() + '\n\n' + text[b:]

cn, en, sc, se = map(before, [CN, EN, SC, SE])

# Keep the complete internal revision history outside the reader-facing manuscript.
history = cn[cn.index('## 附录 D　'):cn.index('## 附录 E')]
(OUT / 'INTERNAL_REVISION_HISTORY_THROUGH_20261107.md').write_text(history)
cn = section(cn, '## 附录 D　', '## 附录 E', '''## 附录 D　版本与修订记录

本稿于2026-11-07按已确定的贡献定位完成定点修订并同步英文。完整内部修订历史单独保存在[修订归档](PAPER1_bilingual_targeted_revision_20261107/INTERNAL_REVISION_HISTORY_THROUGH_20261107.md)，本轮修改前快照、逐项差异与核对结果见同目录。历史失败及来源限制继续保留在正文§3.4与补充材料S9、S10、S12，不以整理版本记录代替科学披露。

---''')
cn = section(cn, '同步日期：', '\n---', '''同步日期：2026-11-07。本稿按已确定的贡献定位，同步双向偏差评价、连续模型上界、既定V2经验修正及静态接入的证据边界；英文与补充材料同步更新。使用既有运行与已核派生结果，未新增求解或拟合。修改前快照及本轮差异见 `PAPER1_bilingual_targeted_revision_20261107/`。本稿为作者审阅工作稿，仍待作者最终科学审定及目标期刊格式、声明和访问条件检查。''')

abstract_cn = r'''## 摘要

纳米压印降阶模型常以局部立方律估计图案化表面的等效输运，但局部平板组合未显式解析沟槽侧壁及台阶连接处的流动。本文针对周期240 nm、槽宽120 nm的等宽矩形槽与凸台，在固定间隙、全充液、无滑移牛顿流体条件下，采用格子玻尔兹曼方法分别计算沿槽与横槽导度。主数据包含18种几何、36个主方向结果，网格间距为5 nm；其中4种几何另有2.5 nm加密结果。

相对于5 nm离散参考，局部立方律在全部36个主方向条件下高估导度，沿槽与横槽最大偏差分别为+204.85%和+54.19%；前者对应公式值约为参考值的3.05倍。基准几何的各向异性由数值参考的2.21增至公式的3.70，在同一线性张量关系下，45°驱动时两组主值重建的平均通量方向相差9.20°。既定V2经验修正在同一参考下减小了35/36条记录的绝对偏差，但最薄间隙深槽横向条件的局部改善判断随参考网格改变；一个新增间隙的固定公式比较提供了补充证据。

附录E证明，局部立方律在所列连续Stokes问题中给出两主导度的上界，该界不确定偏差幅度或V2准确度。本文的定量结论限于采样条件与指定离散参考，表明模型评价需同时考察两主值、其比值及参考敏感性；未建立连续参数范围的预测精度保证或实际压印过程的准确性。

**关键词：** 纳米压印；矩形沟槽；各向异性输运；格子玻尔兹曼方法；局部立方律；模型偏差
'''
cn = section(cn, '## 摘要', '\n---', abstract_cn)
abstract_en = r'''## Abstract

Reduced nanoimprint models commonly estimate patterned-surface transport with a local cubic law, which does not explicitly resolve groove sidewalls or step connections. We assess this construction for equal-width rectangular grooves and ribs of period 240 nm and groove width 120 nm. Lattice Boltzmann calculations give the along- and across-groove conductances for fixed, fully filled gaps with Newtonian liquid and no-slip walls. The main dataset comprises 18 geometries and 36 principal-direction results on a 5 nm grid; four geometries also have 2.5 nm refinements.

Relative to the 5 nm discrete references, the local cubic law overestimates all 36 principal-direction results. Maximum discrepancies are +204.85% along and +54.19% across the grooves; the former corresponds to a model value approximately 3.05 times the reference. At the reference geometry, anisotropy increases from the numerical value of 2.21 to the model value of 3.70. Under the same linear tensor relation, the reconstructed mean flux directions differ by 9.20° for forcing at 45°. The fixed V2 empirical correction reduces absolute discrepancy in 35 of the 36 records, although the local improvement assessment at the thinnest-gap deep-groove transverse condition changes with reference grid. A fixed-form comparison at one additional gap provides supplementary evidence.

Appendix E establishes upper bounds on both principal conductances for the stated continuous Stokes problem; these bounds determine neither discrepancy magnitudes nor V2 accuracy. Quantitative conclusions concern the sampled conditions and specified discrete references. Assessment should consider both principal values, their ratio and reference sensitivity together. Continuous-domain prediction accuracy and real-imprint fidelity have not been established.

**Keywords:** nanoimprint lithography; rectangular grooves; anisotropic transport; lattice Boltzmann method; local cubic law; model discrepancy
'''
en = section(en, '## Abstract', '\n---', abstract_en)
en = replace(en, '\n## Abstract', '\n**Author-review working manuscript; synchronized on 2026-11-07.** Existing results are used without new solver runs or fitting. Author scientific approval, venue formatting, declarations and access arrangements remain pending.\n\n## Abstract')

near_cn = '''已有工作在所解问题和系数定义上与本文各有区别。Jain等[1]以图案化模板下的各向异性输运组织压印流动模型；本文将问题收窄为固定、全充液单胞中的系数比较，不借用过程模型结果认证这些系数。Patir–Cheng[4]印刷第15页式（23）、（24）在局部Reynolds模型中给出横向调和与纵向算术平均；乘回其归一化高度的三次方后才可与本文深度积分导度比较，不能直接混用流量因子与单位为m³的K。Dewangan–Datta[5]的§4.1—4.2选择平滑形貌与三角形沟槽作理论—有限元对照，§4对方波形貌指出特定谱级数发散及相应表达式不适用，不能直接作为本文矩形台阶的同条件解。本文增加的是这一固定矩形槽族中原公式双向偏差、各向异性后果及既定经验修正表现的配套评价，不据上述区别宣称首创。文献核对范围见补充材料S11。\n\n'''
near_en = '''The compared problems and coefficient definitions differ. Jain et al. [1] use anisotropic transport in a patterned-template process model; here the comparison is restricted to fixed, fully filled cells. Patir–Cheng [4, p. 15, Eqs. (23)–(24)] gives harmonic and arithmetic flow-factor averages within a local Reynolds model; the reference-height normalization must be restored before comparison with the present conductance in m³. Dewangan–Datta [5, §§4.1–4.2] compares smooth and triangular profiles with finite-element solutions. Its §4 identifies divergent spectral sums for a square-wave profile, so the affected expressions are not a matched solution for the present rectangular steps. Our contribution is a paired assessment of directional discrepancies, anisotropy consequences and fixed-correction performance for this rectangular family, without a priority claim. Source-check scopes are given in Supplementary S11.\n\n'''
cn = replace(cn, '本文比较局部立方律与显式数值主值的偏差幅度及方向差异，并检查经验修正的剩余残差。', near_cn + '本文比较局部立方律与显式数值主值的偏差幅度及方向差异，并检查经验修正的剩余残差。')
en = replace(en, 'We compare the magnitudes and directional differences', near_en + 'We compare the magnitudes and directional differences')
cn = replace(cn, '本文考察固定、全充液矩形沟槽中两主方向的有效导度，分析局部立方律相对于显式沟槽计算的偏差，评价既定经验修正的改善程度，并识别其在所考察几何条件下的局限。', '本文针对固定周期、等宽槽与凸台的全充液矩形沟槽，比较局部立方律与显式沟槽计算得到的两主方向导度，量化其对各向异性及张量重建流向的影响，并在同一离散参考下评价既定经验修正的改善与局限。理想Stokes问题中的主导度上界为原公式提供理论解释，数值比较另行报告偏差幅度及参考网格敏感性。')
en = replace(en, 'For rectangular grooves of fixed period and width,', 'We compare both principal conductances of fully filled rectangular grooves against the local cubic law, quantify consequences for anisotropy and tensor-reconstructed flow direction, and assess the fixed empirical correction at the same discrete references. Ideal-Stokes upper bounds provide theoretical context; discrepancy magnitudes and grid sensitivity are reported separately.\n\nFor rectangular grooves of fixed period and width,')

# Explicitly name the legacy boundary-audit set, which differs from the comparison set.
cn = replace(cn, '全部 46 个已分析算例（36 个主地图 + 8 个细网格 + 2 个黏度对照）', '旧边界审计集合的46条运行记录（36个主结果＋8个加密结果＋2个黏度对照；不含新增h=100 nm）')
en = replace(en, 'All 46 analyzed cases (36 main-map, 8 refinement and 2 viscosity checks)', 'All 46 records in the legacy boundary-audit set (36 main-map, 8 refinement and 2 viscosity checks, excluding the added h=100 nm cases)')
roles_cn = '''
本文使用的数据集合分工如下；相同记录可用于不同检查，不能将各行相加称为独立几何：

| 集合 | 构成 | 用途 |
|---|---|---|
| 主比较集合 | 18种几何、36条5 nm主方向结果 | 原公式与V2的主统计 |
| 加密比较 | 上述4种几何的8条2.5 nm结果 | 参考敏感性，另列 |
| 新增间隙 | h=100 nm、d=100 nm的2条5 nm结果 | 固定公式补充比较 |
| 构建复现 | h=75 nm、d=100 nm的2条新记录与历史结果对照 | 单几何复现，不新增比较几何 |
| 旧附加检查 | 2条黏度、6条斜向结果 | 分别核物性响应与张量内部自洽 |

因此公式比较合计19种几何、46条离散记录（36＋8＋2），有别于旧边界审计的46条（36＋8＋2黏度）。原表S1的52条清单保留，新增与构建对照见补充表S6。
'''
roles_en = '''
The datasets have distinct roles; records reused across checks must not be counted as independent geometries:

| Dataset | Composition | Role |
|---|---|---|
| Main comparison | 18 geometries, 36 principal-direction results at 5 nm | Main local-law and V2 statistics |
| Refinements | 8 results at 2.5 nm for 4 of those geometries | Reference sensitivity, reported separately |
| Additional gap | 2 results at 5 nm for h=100 nm, d=100 nm | Fixed-form supplementary comparison |
| Build reproduction | 2 new records for h=75 nm, d=100 nm, paired with historical records | Single-geometry reproduction, not added comparison geometries |
| Legacy additional checks | 2 viscosity and 6 oblique results | Property response and internal tensor consistency |

The formula-comparison set therefore contains 19 geometries and 46 discrete records (36+8+2), distinct from the 46-record legacy boundary-audit set (36+8+2 viscosity checks). The original 52-row Table S1 is retained; added and build-comparison records are indexed in Supplementary Table S6.
'''
cn = replace(cn, '本章支持资料按 S1—S11 编号；', roles_cn + '\n本章支持资料按S1—S13编号；')
en = replace(en, 'Supporting methods are numbered S1–S11.', roles_en + '\nSupporting methods are numbered S1–S13.')
en = replace(en, 'Solid walls use Bouzidi–Firdaouss–Lallemand interpolated bounce-back, with wall intersections obtained from the analytical geometry [7,8].', 'Solid walls use Bouzidi–Firdaouss–Lallemand interpolated bounce-back, with intersections obtained from the analytical geometry [7,8]. The scheme was formulated for fractional wall distances [8]; OpenLB also maintains implementation checks through analytical benchmarks and automated regression tests [7].')
en = replace(en, 'An independent-solver comparison would be a numerical cross-check and would not alone establish physical validation; no such same-geometry comparison has been completed.', 'An independent-solver comparison of resolved grooves would be a numerical cross-check; no such matched comparison has been completed. Independent implementations of the same static averaged model are compared in §5.3, which tests coefficient interfacing rather than resolved-groove accuracy.')
en = replace(en, 'Halving the spacing reduces the error by approximately a factor of four.', 'Halving the spacing reduces the error by approximately a factor of four. The analytical-comparison/refinement structure is consistent with OpenLB Poiseuille benchmarks and regression tests [7], although the metric here is integrated conductance rather than a velocity-field L2 norm.')

control_cn = '\n补充材料[S12、表S8](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-s12)另列后续控制链：常规几何h=60 nm、d=80 nm的网格与驱动力检查，以及薄隙h=30 nm、d=80 nm的网格检查。薄隙横槽中细变化1.328387035%超过原1%判据，S4阶段仍为FAIL；这与上文h=75 nm、d=100 nm历史细网格的质量FAIL是不同记录。控制几何不并入主比较集合，其他几何的网格差不能作为主地图误差条。\n'
cn = replace(cn, '### 3.4 已知限制', control_cn + '\n### 3.4 已知限制')
control_en = '\nThe later control chain is indexed separately in [S12 and Table S8](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md#sm-s12): grid and forcing checks at h=60 nm, d=80 nm, and grid checks at h=30 nm, d=80 nm. The thin-gap transverse medium-to-fine change is 1.328387035%, exceeding its original 1% criterion, so stage S4 remains FAIL. This differs from the historical mass failure at h=75 nm, d=100 nm. Control geometries are excluded from the main comparison set, and their grid changes are not error bars for other geometries.\n'
en = replace(en, '### 3.4 Known limitations', control_en + '\n### 3.4 Known limitations')
en = replace(en, '**No same-geometry independent-solver or experimental reference is available here.**', '**No resolved-groove independent-solver or experimental reference is available here.** The OpenFOAM comparison in §5.3 concerns the same averaged model and supports interface consistency only.')
build_en = r'''**Single-geometry build reproduction.** At $h=75$ nm and $d=100$ nm, matched calculations with the currently identifiable executable reproduce both historical principal conductances: $K_{xx}=4.449022\times10^{-23}$ m³ and $K_{yy}=9.834076\times10^{-23}$ m³. Stopping steps and stepwise main-flux values coincide in each direction; sectional-flow diagnostics have last-digit differences, with maximum absolute difference $3.66\times10^{-33}$ m³/s. This supports reproduction of the main transport results at this geometry, rather than equivalence over all historical geometries or complete binding to historical source and dependencies.'''
en = replace(en, '\n## 4 Results', '\n' + build_en + '\n\n---\n\n## 4 Results')

# Clarify theory-versus-discrete evidence at the numerical comparison.
bound_cn = '\n附录E约束的是相同理想边值问题的连续解K*，不是离散K_LB。上述46条数值记录与上界方向相容，不是46个独立物理条件，也不建立全图连续解误差界；上界本身不确定偏差幅度、方向比偏差符号或V2准确度。\n'
cn = replace(cn, '### 4.3 ', bound_cn + '\n### 4.3 ')
add46_en = '\nIn addition to the 36 main records, four existing geometries have eight 2.5 nm records (§3.3), and §4.4 adds two principal-direction records at h=100 nm. All 46 comparison records for 19 geometries lie below the corresponding local-cubic-law values. Refinements and added-gap comparisons are reported separately and are excluded from the original 36-record statistics. Appendix E constrains the continuous solution K*, not discrete K_LB. These observations are compatible with the upper bounds; they are neither 46 independent physical conditions nor a map-wide continuous-error bound. The bounds determine neither discrepancy magnitudes, the sign of the ratio discrepancy nor V2 accuracy.\n'
en = replace(en, '### 4.3 ', add46_en + '\n### 4.3 ')

# Shared, matched statistics table with pointwise improvement counts.
old_cn = r'''| 方向及样点范围 | 原始最大绝对偏差 | V2最大绝对残差 |
|---|---:|---:|
| 沿槽，全部18点 | 204.85% | 10.5% |
| 跨槽，全部18点 | 54.19% | 18.7% |
| 跨槽，$h\ge50$ nm，15点 | 54.19% | 6.9% |'''
new_cn = r'''| 方向及样点范围 | 原始最大绝对偏差 | V2最大绝对残差 | 原始平均绝对偏差 | V2平均绝对偏差 | 绝对偏差减小 |
|---|---:|---:|---:|---:|---:|
| 沿槽，全部18点 | 204.85% | 10.50% | 88.85% | 6.40% | 18/18 |
| 跨槽，全部18点 | 54.19% | 18.71% | 30.63% | 4.42% | 17/18 |
| 跨槽，$h\ge50$ nm，15点 | 54.19% | 6.9% | — | — | — |

平均绝对偏差为该方向18个主样点绝对百分比偏差的算术平均，不是有符号偏差均值；两个方向合计35/36条改善。15点子集用于定位薄隙影响，不能据此承诺所有h≥50 nm条件满足6.9%。'''
cn = replace(cn, old_cn, new_cn)
old_en = r'''| Direction and samples | Original maximum absolute discrepancy | V2 maximum absolute residual |
|---|---:|---:|
| Along, all 18 | 204.85% | 10.5% |
| Across, all 18 | 54.19% | 18.7% |
| Across, $h\ge50$ nm，15 samples | 54.19% | 6.9% |'''
new_en = r'''| Direction and samples | Original maximum absolute discrepancy | V2 maximum absolute residual | Original mean absolute discrepancy | V2 mean absolute discrepancy | Absolute discrepancy reduced |
|---|---:|---:|---:|---:|---:|
| Along, all 18 | 204.85% | 10.50% | 88.85% | 6.40% | 18/18 |
| Across, all 18 | 54.19% | 18.71% | 30.63% | 4.42% | 17/18 |
| Across, $h\ge50$ nm, 15 samples | 54.19% | 6.9% | — | — | — |

Mean absolute discrepancy is the arithmetic mean of absolute percentage discrepancies over the 18 main samples in each direction, not a signed mean. Across both directions, 35/36 records improve. The 15-sample subset identifies the thin-gap contribution; it does not guarantee a 6.9% maximum for every condition with h≥50 nm.'''
en = replace(en, old_en, new_en)
model_cn = '\nV2在本文中作为既定经验关系接受评价。乘性结构保留了局部立方律基线，公布表达式保持正值并在d=0回到平板值；这些性质不能替代系数、指数或仅选d/w作为因子变量的精度证据。现存记录未完整保存排除其他变量和函数族的事前论证，本文不补写此类选择依据，也未据新增结果重选形式或系数。\n'
cn = replace(cn, '按公布系数直接计算，', model_cn + '\n按公布系数直接计算，')
en = replace(en, 'Evaluation using the published coefficients', '\nV2 is evaluated here as a fixed empirical relation. Its multiplicative form retains the local-law baseline, stays positive and recovers the flat-plate value at d=0. These properties do not establish accuracy of its coefficients, exponents or choice of d/w as the sole factor variable. Surviving records do not fully document an a priori exclusion of alternative variables or function families; no such rationale is reconstructed, and the added results are not used to reselect the form or coefficients.\n\nEvaluation using the published coefficients')
en = replace(en, 'V2 depends only on $d/w$, whereas residuals still vary with gap.', r'The V2 multiplicative factor depends only on $d/w$, while the complete formula $K_i^{V2}=F_i(d/w)K_i^{LC}(h,d)$ still contains gap $h$. Residuals still vary with gap.')
en = replace(en, 'Without same-condition comparisons across the two program identities, potential build effects cannot be separated from geometry, model and reference effects on residuals.', 'Apart from the matched reproduction at h=75 nm, d=100 nm (§3.4), no further same-condition comparisons across the two program identities are available. Potential build effects therefore remain incompletely separated from geometry, model and reference effects on residuals.')
h100_en = r'''**Fixed-form comparison at an additional gap ($h=100$ nm).** At fixed groove width $w=120$ nm, period $P=240$ nm and depth $d=100$ nm, two principal-direction calculations were added on the 5 nm grid. This gap was absent from the original nine-geometry coefficient-calibration set. The comparison uses the previously published V2 coefficients without refitting. Across- and along-groove OpenLB conductances are $9.914424\times10^{-23}$ m³ and $1.654764\times10^{-22}$ m³. With the matched OpenLB discrete values as denominators, local-law discrepancies are +49.43% and +126.62%, and V2 residuals are +4.39% and −2.03%. The OpenLB ratio $A=K_{yy}/K_{xx}$ is 1.6690, compared with 1.5664 from V2; its discrepancy, using the same model/reference−1 convention, is −6.15%. These results provide supplementary evidence for the fixed V2 relation at one added gap. Comparison is restricted to the 5 nm references and provides neither a continuous-domain accuracy guarantee nor certification of a strictly blinded test.

At fixed $d/w$, the along-groove V2 residual changes from +5.90% at $h=75$ nm to −2.03% at $h=100$ nm, a difference of 7.93 percentage points; the transverse difference is 2.04 percentage points. The along-groove change fails the batch's recorded five-percentage-point structural screen. This motivates examining gap dependence of the multiplicative factor, but does not uniquely identify omission of gap as the cause or determine a replacement form. Supplementary Tables S6 and S7 index the added comparisons and the thin-gap two-grid assessment.'''
en = replace(en, '\n## 5 Discussion', '\n' + h100_en + '\n\n---\n\n## 5 Discussion')
cn = replace(cn, '因此，不能把修正精度与数值参考精度混为一谈。', '因此，不能把修正精度与数值参考精度混为一谈；两档原公式/V2偏差并列见补充表S7。')

# The English version lacked the accepted static-interface section.
interface_en = r'''### 5.3 Coefficient interfacing in a static averaged model

To check coefficient interfacing, the local-law and V2 conductances at $h=75$ nm, $d=100$ nm, $w=120$ nm and $P=240$ nm are supplied to a static averaged model with mean liquid thickness $\bar H=h+d/2=125$ nm. The interface is

$$
\mathbf J=-\frac{\mathbf K}{\mu}\nabla p,\qquad
\bar{\mathbf u}=\frac{\mathbf J}{\bar H},\qquad
\mathbf D=\bar H\,\mathbf K^{-1},
\tag{8}
$$

where $\mathbf D$ has units m⁻². The synthetic averaged domain is 24×48 μm with 16×32×1 cells. Viscosity is 0.001 Pa·s; the driving edges have gauge pressures 24 and 0 Pa, the other in-plane edges have no flux, and the walls do not move.

C01–C04 apply either local-law or V2 principal conductances and compare outlet fluxes from a two-dimensional implementation and an OpenFOAM averaged-pressure solver. Along-groove forcing is represented by rotating the groove direction; $K_{yy}$ always refers to groove-attached coordinates. GDI01 additionally inserts the V2 transverse coefficient through the momentum-resistance source and compares its output with the C01 baseline. Replacing the local law with V2 reduces transverse and longitudinal outlet flow by 30.14% and 56.77%, respectively: these are output responses to changed conductance at common static boundaries.

The checks support units, directions and flux interfacing in the tested cases. The averaged domain does not resolve individual grooves, and coefficients come from the same formulas. Agreement therefore does not independently validate conductance accuracy, dynamic squeezing, load or filling time. Supplementary S13 records the implementation-check scope.

### 5.4 Applicability and unverified conditions'''
en = replace(en, '### 5.3 Applicability and unverified conditions', interface_en)
cn = replace(cn, '本文所称 $K_{yy}$ 始终按槽附着坐标定义。', '本文所称 $K_{yy}$ 始终按槽附着坐标定义；接入检查范围另见补充材料S13。')
cn = replace(cn, '等宽槽/凸台的18种几何、36个主方向样点。', '等宽槽/凸台的18种主地图几何、36个主方向结果；h=100 nm另作为一个新增几何单列，合计19种比较几何。')
en = replace(en, 'Responses and discrepancy ranges come from 18 geometries and 36 principal-direction samples at period 240 nm, width 120 nm and equal groove/rib widths.', 'Main-map responses and discrepancy ranges come from 18 geometries and 36 principal-direction results at period 240 nm, width 120 nm and equal groove/rib widths. The h=100 nm comparison adds one geometry, reported separately, giving 19 comparison geometries in total.')
en = replace(en, 'V2 does not explicitly include gap, although residuals vary with gap.', 'The V2 multiplicative factor does not explicitly include gap, although the complete formula does through the local-law baseline. Residuals vary with gap.')

# Conclusions retain geometry evidence while putting model assessment first.
conc_cn = r'''## 6 结论

**一、** 相对于18种几何的36条5 nm主方向结果，局部立方律的沿槽偏差为+10.30%至+204.85%，横槽为+8.11%至+54.19%。理想连续Stokes问题中的两主导度上界由附录E单独证明，不确定这些百分比。已有8条加密及2条新增记录同样位于公式值下方，合计19种几何、46条比较记录；这些数值相容性不构成全图连续精度认证。

**二、** 两个方向的几何响应及公式偏差不同。间隙50 nm时，槽深从25增至120 nm，5 nm结果的Kyy增至3.55倍，Kxx增至1.034倍；间隙125 nm时沿槽增幅仍约39.2%，该配对两端已有加密结果支持趋势。基准几何的公式各向异性相对5 nm参考高约67%，45°驱动时同一线性张量关系重建的平均通量方向相差9.20°。这些结果说明模型比较需要同时检查两主值及其比值，尚未确定单一耗散机制或实际布胶误差。

**三、** 使用公布V2系数回顾性比较同一主集合，沿槽平均绝对偏差由88.85%降至6.40%，横槽由30.63%降至4.42%，合计35/36条绝对偏差减小；最大绝对残差分别为10.50%与18.71%。h=25 nm、d=100 nm横槽条件的改善判断随5/2.5 nm参考改变，h≥50 nm子集的6.9%不是连续适用范围承诺。V2残差的间隙依赖仍需与模型选择、参数估计和参考误差分别评价。

**四、** 保持V2系数不变，在h=100 nm、d=100 nm新增几何的横槽、沿槽及方向比上，相对5 nm参考的偏差分别为+4.39%、−2.03%和−6.15%。这是一个新增间隙的固定公式补充比较，未建立普遍预测精度。静态平均模型中的OpenFOAM接入检查支持已测单位、方向和通量一致性，不构成显式导度或动态压印过程准确性的独立验证。

---'''
cn = section(cn, '## 6 结论', '## 参考文献', conc_cn)
conc_en = r'''## 6 Conclusions

**1.** Against the 36 main principal-direction records for 18 geometries at 5 nm, local-law discrepancies range from +10.30% to +204.85% along and from +8.11% to +54.19% across the grooves. Appendix E separately establishes upper bounds for the ideal continuous Stokes problem, without determining these percentages. Eight refinement and two additional-gap records also lie below the model values, giving 46 comparison records for 19 geometries; this compatibility does not certify map-wide continuous-solution accuracy.

**2.** Geometry responses and model discrepancies differ by direction. At a 50 nm gap, deepening from 25 to 120 nm multiplies the 5 nm Kyy by 3.55 and Kxx by 1.034. At 125 nm gap, the along-groove gain remains about 39.2%, with refinements at both endpoints supporting the paired trend. At the reference geometry, the model anisotropy is about 67% higher than the 5 nm reference, and mean flux directions reconstructed under the same linear tensor relation differ by 9.20° for 45° forcing. Both principal values and their ratio require assessment; no unique dissipation mechanism or real dispensing error has been established.

**3.** Retrospective comparison using the published V2 coefficients reduces the along-groove mean absolute discrepancy from 88.85% to 6.40% and the transverse value from 30.63% to 4.42%, improving 35/36 main records. Maximum absolute residuals are 10.50% and 18.71%, respectively. At h=25 nm, d=100 nm, the local transverse improvement assessment changes between 5 and 2.5 nm references. The 6.9% maximum in the h≥50 nm subset is not a continuous applicability guarantee. Residual gap dependence must be assessed separately from model selection, parameter estimation and reference error.

**4.** With V2 coefficients fixed, the added h=100 nm, d=100 nm geometry gives transverse, longitudinal and anisotropy discrepancies of +4.39%, −2.03% and −6.15% against the 5 nm references. This fixed-form supplementary comparison does not establish general prediction accuracy. OpenFOAM interface checks in a static averaged model support tested units, directions and flux consistency, rather than independently validating resolved conductances or dynamic imprinting accuracy.

---

## Data, code and author-review status

Selected code, figures and small data are retained in the private repository [SIM240_code_figures_data](https://github.com/yuanyuanxu1022/SIM240_code_figures_data), at the checked snapshot [e05b3f21171ce52a66af41dfe172e79c0a099c20](https://github.com/yuanyuanxu1022/SIM240_code_figures_data/commit/e05b3f21171ce52a66af41dfe172e79c0a099c20), under `07_第一篇代码数据更新_20261107/`. Access is restricted to authorized users. The snapshot includes a read-only checker for saved numbers; it is not a complete reconstruction of historical build environments. This manuscript and the present supplement revision have not been newly uploaded. Public release, reviewer access and a persistent identifier remain for the authors to determine under the selected venue's requirements. Author information, funding, conflicts, contributions and AI-use disclosures also require author confirmation. This remains an author-review manuscript, not a submission-readiness declaration.

'''
en = section(en, '## 6 Conclusions', '## Appendix E.', conc_en)
data_start = '截至2026-10-27，部分代码、图片和原始数据已保存于私有仓库'
data_end = '\n\n---'
data_cn = '''截至2026-11-07，部分代码、图片和小型原始数据已保存于私有仓库[SIM240_code_figures_data](https://github.com/yuanyuanxu1022/SIM240_code_figures_data)，已核固定快照为[e05b3f21171ce52a66af41dfe172e79c0a099c20](https://github.com/yuanyuanxu1022/SIM240_code_figures_data/commit/e05b3f21171ce52a66af41dfe172e79c0a099c20)，新增入口为 `07_第一篇代码数据更新_20261107/`。该快照仅对有权限人员开放，含保存数字的只读复核脚本；不等于历史构建环境完整复现，也不是公众可下载的数据发布。本轮正文与补充材料修订未新增上传。公开范围、审稿访问方式及持久标识仍待作者按目标期刊要求确定。上传覆盖与核验范围见[上传报告](GITHUB_PAPER1_CODE_REFRESH_20261107/REPORT.md)。'''
cn = section(cn, data_start, data_end, data_cn)
cn = replace(cn, '五张补充数据表分别为表 S1—S5；表 S5 补列历史基准的条件性 Richardson/GCI 估计。', '既有表S1—S5保留，新增表S6为新增间隙与构建对照，表S7为薄隙修正的两网格比较，表S8为控制证据索引。')
cn = replace(cn, '| [S11](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-s11) | 方法引文核实边界 | §2.1、§2.3及相关引文 | — |', '| [S11](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-s11) | 方法引文核实边界 | §2.1、§2.3及相关引文 | — |\n| [S12](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-s12) | 后续控制证据及失败记录 | §3.3—3.4 | 表S8 |\n| [S13](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-s13) | 静态平均模型接入 | §5.3 | — |')

# Supplement edits are assembled below; writing happens only after all replacements succeed.
sc = section(sc, '编号版本：', '\n\n记录的PASS', '''编号版本：2026-10-24；本轮同步日期2026-11-07。保留S1—S11及表S1—S5，新增S12控制证据、S13静态平均模型接入，以及表S6—S8。所列数据来自既有D2/D3、历史基准和已完成的后续控制检查，不纳入另行开展的D4保留结果，不替换V2。代码和小型数据的已核私有快照为e05b3f21171ce52a66af41dfe172e79c0a099c20，入口 `07_第一篇代码数据更新_20261107/`；本轮稿件和补充修订未新增上传。审稿访问与最终期刊格式仍待作者确定。''')
se = section(se, 'Numbering version:', '\n\nRecorded PASS', '''Numbering version: 2026-10-24; synchronized on 2026-11-07. S1–S11 and Tables S1–S5 are retained, with S12 for controls, S13 for static averaged-model interfacing and Tables S6–S8 added. Sources are existing D2/D3 records, historical benchmarks and completed later controls. Separate D4 reserved results are excluded, and V2 is unchanged. The checked private code/small-data snapshot is e05b3f21171ce52a66af41dfe172e79c0a099c20 under `07_第一篇代码数据更新_20261107/`; the present manuscript and supplement revision have not been newly uploaded. Reviewer access and final venue formatting remain for the authors to determine.''')
sc = replace(sc, '| S11 | 方法引文核实边界 | 方法相关引文 | — |', '| S11 | 方法引文核实边界 | 方法相关引文 | — |\n| S12 | 后续控制证据及失败记录 | §3.3—3.4 | 表S8 |\n| S13 | 静态平均模型接入 | §5.3 | — |')
se = replace(se, '| S11 | Method-citation scope | Method citations | — |', '| S11 | Method-citation scope | Method citations | — |\n| S12 | Later controls and failure records | §3.3–3.4 | Table S8 |\n| S13 | Static averaged-model interfacing | §5.3 | — |')
inventory_cn = r'''
**新增比较与数据使用角色。** 主比较36条、加密8条与h=100 nm新增2条合计19种几何的46条比较记录；与S3的36＋8＋2黏度边界审计集合不同。原52行表S1不扩写、不改历史分母。

<a id="table-s6"></a>

**表 S6　新增间隙与单几何构建对照（6条记录）**

数值表：[Table_S6_added_gap_build_comparison.csv](Table_S6_added_gap_build_comparison.csv)，采用已核比较表的原字节副本。四条新增记录为h100两方向与h75构建B两方向，另有h75两条历史对照；只有h100增加一个比较几何。原目录及manifest标签由[四例验收报告](../PAPER1_new_four_cases_acceptance_20261107/REPORT.md)定位，`A_blind`原标签不作为盲测认证。A偏差统一为100(A_model/A_LB−1)%，h100 V2为−6.15%。

| 数据组 | 几何与用途 | 数据使用与身份边界 |
|---|---|---|
| 9个系数标定几何 | h=50/75/125 nm × d=25/50/100 nm；w=120 nm | 原拟合目标函数使用；主地图二进制285f67a0… |
| 9个扩展几何 | 主地图余下几何 | 形式选择时已可见，非独立预测；主地图二进制57611b21… |
| h100新增几何 | d=100 nm，两方向，5 nm | 固定公布系数，未重新拟合；不认证严格盲测 |
| h75构建复现 | d=100 nm，两方向，5 nm | 两构建K、停止步数、逐步主通量相同；不是全图构建等价 |

完整两组二进制SHA及拟合角色来源见[主张终审报告](../PAPER1_claim_final_review_20261105/REPORT.md)与S10；表中缩写仅便于识别，不替代运行清单。
'''
inventory_en = r'''
**Added comparisons and data-use roles.** The main 36, refinement 8 and added-gap 2 records form a 46-record comparison set for 19 geometries. This differs from the 36+8+2 viscosity boundary-audit set in S3. The original 52-row Table S1 and its historical denominator are unchanged.

<a id="table-s6"></a>

**Table S6. Added-gap and single-geometry build comparisons (6 records).**

The [numerical table](Table_S6_added_gap_build_comparison.csv) is a byte-preserving copy of the audited comparison CSV. Four added records comprise two h100 directions and two h75 build-B directions; the other two are historical h75 controls. Only h100 adds a comparison geometry. Original directories and manifest labels are indexed in the [four-case audit](../PAPER1_new_four_cases_acceptance_20261107/REPORT.md); the original `A_blind` label is not blinding certification. Ratio discrepancy uses 100(A_model/A_LB−1)%, giving −6.15% for V2 at h100.

| Data group | Geometry and role | Data-use and identity limits |
|---|---|---|
| 9 coefficient-calibration geometries | h=50/75/125 nm × d=25/50/100 nm; w=120 nm | Used in the coefficient objective; main-map binary 285f67a0… |
| 9 extension geometries | Remaining main-map geometries | Visible during form selection, not independent prediction; main-map binary 57611b21… |
| Added h100 geometry | d=100 nm, two directions, 5 nm | Fixed published coefficients without refitting; not certified strictly blinded |
| h75 build reproduction | d=100 nm, two directions, 5 nm | Matching K, stopping steps and stepwise main flux; not map-wide build equivalence |

Full binary hashes and fitting-role sources are in the [claim audit](../PAPER1_claim_final_review_20261105/REPORT.md) and S10. Abbreviations identify groups but do not replace manifests.
'''
sc = replace(sc, '<a id="sm-s2"></a>', inventory_cn + '\n<a id="sm-s2"></a>')
se = replace(se, '<a id="sm-s2"></a>', inventory_en + '\n<a id="sm-s2"></a>')
sc = replace(sc, '正文特指的46项D2主地图、加密和黏度检查', '旧边界审计集合的46条D2主地图、加密和黏度检查记录（不含新增h100）')
se = replace(se, 'All 46 D2 main-map, refinement and viscosity cases identified in the manuscript', 'All 46 D2 records in the legacy main-map/refinement/viscosity boundary-audit set (excluding added h100 cases)')
thin_cn = r'''
<a id="table-s7"></a>

**表 S7　h=25 nm、d=100 nm横槽的原公式/V2两网格对照**

完整表：[Table_S7_thin_gap_correction.csv](Table_S7_thin_gap_correction.csv)。同一几何的原公式和固定V2均以相应网格K为分母。

| 参考网格 | 原公式偏差 | V2偏差 | 绝对偏差变化的判断 |
|---|---:|---:|---|
| 5 nm | +16.36% | −18.71% | 增大 |
| 2.5 nm | +21.76% | −14.94% | 减小 |

局部改善判断受参考分辨率影响，不能从5 nm反例推出连续解上同样恶化。已有h125/d25与d120两端加密对照支持所报配对趋势；该薄隙点也不否定全部参数趋势。h100尚无同几何加密参考，本轮未追加计算。
'''
thin_en = r'''
<a id="table-s7"></a>

**Table S7. Two-grid local-law/V2 comparison for transverse flow at h=25 nm, d=100 nm.**

The [complete table](Table_S7_thin_gap_correction.csv) uses the corresponding grid's K as denominator for both the local law and fixed V2.

| Reference grid | Local-law discrepancy | V2 residual | Change in absolute discrepancy |
|---|---:|---:|---|
| 5 nm | +16.36% | −18.71% | Increase |
| 2.5 nm | +21.76% | −14.94% | Decrease |

The local improvement assessment depends on reference resolution; deterioration against the 5 nm reference is not established for the continuous solution. Paired refinements at h125/d25 and d120 support the reported paired trend, so this thin-gap example does not invalidate all parameter trends. A matched refinement at h100 is unavailable; no calculation was added in this revision.
'''
sc = replace(sc, '<a id="sm-s8"></a>', thin_cn + '\n<a id="sm-s8"></a>')
se = replace(se, '<a id="sm-s8"></a>', thin_en + '\n<a id="sm-s8"></a>')
provenance_cn = '''
**2026-11-07补充范围。** 原52行清单及其四组身份保持历史范围。新增h100与h75构建B四例清单均匹配当前57611b21…二进制；h75历史285f67a0…记录的两主值、停止步数与主通量序列可复现，但42对文件中仅30对字节相同，截面流量最大末位差3.65927×10⁻³³ m³/s。该结果不填补全部历史源码、依赖与编译命令的绑定缺口。详见[新增四例验收](../PAPER1_new_four_cases_acceptance_20261107/REPORT.md)的case_audits、文件对照与清单记录。
'''
provenance_en = '''
**Added scope on 2026-11-07.** The original 52-row inventory and four identity groups retain their historical scope. Manifests for the four added h100 and h75 build-B cases match the current 57611b21… executable. Both principal conductances, stopping steps and main-flux sequences reproduce the historical h75 records from binary 285f67a0…, but only 30 of 42 paired files are byte-identical; the maximum sectional-flow difference is 3.65927×10⁻³³ m³/s. This does not restore complete historical source, dependency and compiler-command binding. Case audits, file comparisons and manifests are indexed in the [four-case audit](../PAPER1_new_four_cases_acceptance_20261107/REPORT.md).
'''
sc = replace(sc, '<a id="sm-s11"></a>', provenance_cn + '\n<a id="sm-s11"></a>')
se = replace(se, '<a id="sm-s11"></a>', provenance_en + '\n<a id="sm-s11"></a>')
# Update only the explicitly superseded citation-scope entry.
sc = section(sc, '- **[5] Dewangan–Datta 2020**', '- **[6] Dewangan–Datta 2018**', '''- **[5] Dewangan–Datta 2020**：沿用已核题名/DOI身份，2026-11-07定向阅读出版社全文§4，定位方波形貌的特定谱级数限制、测试形貌与有限元对照。正文§1.2仅据此区分其问题与本文矩形台阶比较，不声称完成全面新颖性检索、重现其数值或核定本文参考精度。公开原文为 https://doi.org/10.1017/jfm.2020.134 。''')
se = section(se, '- **[5] Dewangan–Datta 2020:**', '- **[6] Dewangan–Datta 2018:**', '''- **[5] Dewangan–Datta 2020:** title/DOI identity is retained. A targeted reading of publisher §4 on 2026-11-07 located its square-wave spectral limitation, test profiles and finite-element comparison. Section 1.2 distinguishes that problem from the present rectangular-step comparison; no exhaustive novelty search, numerical reproduction or certification of our references is implied. Publisher source: https://doi.org/10.1017/jfm.2020.134 .''')
sc += r'''

<a id="sm-s12"></a>

## S12 后续控制证据及失败记录

<a id="table-s8"></a>

**表 S8　控制证据索引（不与19几何46条比较集合相加）**

机器可读来源索引：[Table_S8_control_evidence.csv](Table_S8_control_evidence.csv)。各控制的接受、失败和范围分别记录；以下为已有验收结果的汇编，本轮没有重放轨迹或重新签发阶段接受。

| 检查 | 几何与网格 | 已有证据及状态 | 对本文的限度 |
|---|---|---|---|
| 历史平板解析核验 | h75，5/2.5/1.25 nm | K偏差0.44444079/0.11103511/0.02715688%，见S9 | 只检平壁积分量 |
| S1平板控制 | d=0 | 已有接受，K相对解析偏差约0.173% | 不替代沟槽网格精度 |
| S2常规几何网格 | h60/d80，5/2.5/1.25 nm | 沿/横槽中细变化0.203234%/0.744252%，原网格检查通过 | 特定控制几何，不是全图误差界 |
| S3驱动力控制 | h60/d80，原三档驱动力 | 已有阶段接受 | 不作为V2预测检验 |
| S4薄隙网格 | h30/d80，5/2.5/1.25 nm | 六条单例检查通过；横槽中细变化1.328387035%>1%，原S4阶段FAIL；GCI约0.912232592%不补偿前项失败 | 不并入主统计，不改变阈值或参考资格 |
| 历史细横槽质量失败 | h75/d100，1.25 nm | 质量相对指标1.1967043900362632×10⁻¹⁰>10⁻¹⁰，原FAIL/exit3，见S9 | 与h30/d80网格FAIL分开 |
| S4服务器构建复现 | h30/d80横槽，1.25 nm | 同条件K复现与保存数据核对成立 | 不使原S4网格FAIL转为PASS |

S4中细变化按100|K_medium/K_fine−1|%，与主地图双网格表按K5归一的变化定义不同。两者均不构成已知连续解误差上界，不能与其他几何的最小公式偏差相除建立“安全倍数”。S5未执行，严格参考资格、全图连续误差界和物理验证未建立。本稿对现有指定离散参考作模型比较，不将此控制链包装为全部精度通过。

<a id="sm-s13"></a>

## S13 静态平均模型接入

在h75/d100、w120、P240 nm下，以平均厚度125 nm将K（m³）转换为平均速度与动量阻力：J=−K∇p/μ、u_bar=J/H_bar、D=H_bar K⁻¹（m⁻²）。C01—C04各比较二维与OpenFOAM平均压力实现，GDI01比较V2横槽实际动量源与C01基线；共九端保存出口记录，不是五组各自都有两端。

合成平均域24×48 μm、16×32×1单元、μ=0.001 Pa·s、驱动端表压24/0 Pa、另一方向无通量，壁面静止。换原公式为V2后，横/沿槽出口流量下降30.14%/56.77%。原九端faces.csv求和、接受与执行绑定见[主张终审](../PAPER1_claim_final_review_20261105/REPORT.md)、[重算出口表](../PAPER1_claim_final_review_20261105/recomputed_outlet9.csv)；单位、槽附着方向及接口约束见正文式（8）。它只支持已测静态接入一致，不是显式沟槽导度、实验或动态压印准确性证据。
'''
se += r'''

<a id="sm-s12"></a>

## S12 Later controls and failure records

<a id="table-s8"></a>

**Table S8. Control-evidence index (not added to the 19-geometry, 46-record comparison set).**

The [machine-readable index](Table_S8_control_evidence.csv) binds sources and scopes. This compiles existing acceptance results without replaying trajectories or issuing new stage acceptance.

| Check | Geometry and grids | Existing evidence and status | Limit for this study |
|---|---|---|---|
| Historical analytical plates | h75, 5/2.5/1.25 nm | K errors 0.44444079/0.11103511/0.02715688%, S9 | Planar integrated quantity only |
| S1 plate control | d=0 | Previously accepted; K error about 0.173% | Not groove-resolution evidence |
| S2 regular-geometry grids | h60/d80, 5/2.5/1.25 nm | Along/across medium-to-fine changes 0.203234%/0.744252%; original grid checks pass | Specific control, not a map-wide error bound |
| S3 forcing control | h60/d80, three original force levels | Previously accepted stage | Not a V2 prediction test |
| S4 thin-gap grids | h30/d80, 5/2.5/1.25 nm | Six per-run checks pass; transverse change 1.328387035%>1%, so original S4 stage FAIL; GCI about 0.912232592% does not compensate | Excluded from main statistics; criteria and reference status unchanged |
| Historical fine transverse mass failure | h75/d100, 1.25 nm | Relative mass metric 1.1967043900362632×10⁻¹⁰>10⁻¹⁰, original FAIL/exit3, S9 | Distinct from h30/d80 grid FAIL |
| S4 server build reproduction | h30/d80 transverse, 1.25 nm | Matched K reproduction and saved-data checks support agreement | Does not turn the original S4 grid FAIL into PASS |

S4 medium-to-fine change uses 100|K_medium/K_fine−1|%, distinct from the K5-normalized change in the main-map two-grid table. Neither is a known continuous-solution error bound; division by another geometry's minimum model discrepancy cannot establish a safety factor. S5 has not been executed. Strict reference qualification, map-wide continuous-error bounds and physical validation have not been established. This manuscript compares models against specified discrete records without presenting the control chain as universally passing accuracy evidence.

<a id="sm-s13"></a>

## S13 Static averaged-model interfacing

At h75/d100, w120 and P240 nm, mean thickness 125 nm converts K (m³) to mean velocity and momentum resistance: J=−K∇p/μ, u_bar=J/H_bar and D=H_bar K⁻¹ (m⁻²). C01–C04 each compare a two-dimensional implementation with the OpenFOAM averaged-pressure implementation. GDI01 compares the V2 transverse momentum-source result with the C01 baseline. There are nine saved outlet endpoints, not two endpoints for each of five cases.

The synthetic static domain is 24×48 μm, with 16×32×1 cells, μ=0.001 Pa·s, driving-edge gauge pressures 24/0 Pa and no flux in the other direction. Replacing the local law with V2 reduces transverse/longitudinal outlet flow by 30.14%/56.77%. Summation of the nine original faces.csv records and acceptance/execution binding are indexed in the [claim audit](../PAPER1_claim_final_review_20261105/REPORT.md) and [recomputed outlets](../PAPER1_claim_final_review_20261105/recomputed_outlet9.csv). Equation (8) defines units and groove-attached directions. These checks support the tested static interface, not resolved-groove accuracy, experiments or dynamic-imprint fidelity.
'''

# Added tables derive from already audited numbers; legacy CSVs stay byte-for-byte intact.
shutil.copyfile(ROOT/'PAPER1_new_four_cases_acceptance_20261107/comparison.csv', SUP/'Table_S6_added_gap_build_comparison.csv')
with (SUP/'Table_S7_thin_gap_correction.csv').open('w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['h_nm','d_nm','direction','dx_nm','LC_bias_percent','V2_bias_percent','reference_source'])
    for row in csv.DictReader((SUP/'Table_S2_refinement.csv').open()):
        if row['h']=='25' and row['d']=='100' and row['direction']=='perpendicular':
            factor = 1/(1+0.4900*(100/120)**0.6990)
            for dx,col in [(5,'E5_percent'),(2.5,'E2_5_percent')]:
                bias=float(row[col]); w.writerow([25,100,'Kxx',dx,bias,100*(factor*(1+bias/100)-1),'Table_S2_refinement.csv'])
controls = [
 ('historical_plates',75,0,'S9; Table S4',str(SUP/'Table_S4_grid_archive.csv'),'analytical_comparison','flat geometry only'),
 ('S1_plates','',0,'K_error_about_0.173_percent',str(ROOT/'PAPER1_claim_final_review_20261105/REPORT.md'),'previously_accepted','not groove grid accuracy'),
 ('S2_grids',60,80,'0.203234_percent_P;0.744252_percent_T',str(ROOT/'URV_S2_completed_review_20261103_095422/REPORT.md'),'PASS_scoped','not map-wide'),
 ('S3_forcing',60,80,'three_force_levels',str(ROOT/'SIM240_AI_CONTEXT.md'),'previously_accepted','not V2 validation'),
 ('S4_grids',30,80,'1.328387035_percent_T_gt_1_percent',str(ROOT/'URV_S4_completed_review_20261104_143205/REPORT.md'),'FAIL','six per-run checks do not pass stage'),
 ('historical_mass_failure',75,100,'1.1967043900362632e-10_gt_1e-10',str(SUP/'Table_S4_grid_archive.csv'),'FAIL_exit3','distinct from S4 grid failure'),
 ('S4_server_reproduction',30,80,'K=3.471791836744987e-24_m3',str(ROOT/'URV_S4_TGE_1p25_data_audit_20261105_100521/REPORT.md'),'BUILD_REPRODUCTION_ONLY','S4 remains FAIL')]
with (SUP/'Table_S8_control_evidence.csv').open('w',newline='') as f:
    w=csv.writer(f); w.writerow(['check','h_nm','d_nm','evidence','source','status','limit']);w.writerows(controls)

for path, content in [(CN,cn),(EN,en),(SC,sc),(SE,se)]:
    assert path.read_text()==before(path), 'Concurrent edit: '+str(path)
    path.write_text(content)
    diff=''.join(difflib.unified_diff(before(path).splitlines(True),content.splitlines(True),fromfile='before/'+path.name,tofile='after/'+path.name))
    (OUT/(path.name+'.diff')).write_text(diff)
print(json.dumps({'edited':[str(x) for x in [CN,EN,SC,SE]],'new_tables':3,'history_archived':True},ensure_ascii=False))
