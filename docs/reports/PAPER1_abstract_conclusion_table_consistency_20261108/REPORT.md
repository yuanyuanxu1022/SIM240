# 当前稿摘要、结论与表注一致性检查（2026-11-08）

结论：当前中英文摘要、结论及关键表格与用户刚确认的结论总体一致。本轮未发现方向颠倒、主统计分母混用或把理论上界当作V2精度证明的冲突。需要统一两处措辞；表1、6、8宜补足单独阅读所需的范围说明。其余补注属可选清晰化，不是数字错误。正式稿与全部数字均未修改。

## 范围与依据

本轮唯一科学判断基准是用户上一条确认的最新结论及限定，记录于review_basis.json。当前四份工作稿为检查对象：

- 中文正文：SIM240_中文稿_导师审阅版_20261022.md；
- 英文正文：SIM240_First_Paper_English_20261028.md；
- 当前中文补充：SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md；
- 当前英文补充：同目录SUPPLEMENTARY_METHODS_EN_20261028.md。

项目状态入口仅用于遵守进入项目的导航要求，不用作数字或结论依据；没有打开旧审查报告、旧候选稿、历史聊天存档或原始运行结果来重新裁定数字。当前补充文稿里的历史基准表只检查其已写出的身份、参考与限制，不据此重作物理结论或扩大适用范围。无仿真、标量重算、拟合、理论重证或数值资格验收。

使用scientific-writing技能约束样本集合、分母、术语和结论范围。该技能不是科学证据来源。本报告为作者内部文字检查，非投稿放行。

## 已一致的主张

| 项目 | 当前中文位置 | 当前英文位置 | 文字检查结果 |
|---|---|---|---|
| 18种主几何、36条5 nm方向结果 | 摘要第1段；表1及§2.1集合说明；结论一 | Abstract第1段；Table 1及§2.1；Conclusion 1 | 一致。每种几何两个方向，未称36种几何。 |
| 原式偏差范围与最大位置 | 表6；结论一；摘要列两方向最大值 | Table 6；Conclusion 1；Abstract | 沿槽+10.30%～+204.85%，最大h50/d120；横槽+8.11%～+54.19%，最大h125/d120，与用户口径一致。摘要/结论不重复最大位置不构成冲突。 |
| 基准各向异性 | 摘要第2段、表7、结论二 | Abstract第2段、Table 7、Conclusion 2 | 3.70/2.21及约67%均限定在基准比较，未推广为全部几何。表7措辞改进见下。 |
| V2均值与35/36 | 表8及其后说明、结论三 | Table 8及其后说明、Conclusion 3 | 沿槽88.85%→6.40%，横槽30.63%→4.42%；18/18及17/18合计35/36，含义为绝对偏差减小。未把新增/加密纳入旧分母。 |
| V2最大绝对残差 | 摘要第2段、表8、结论三 | 对应三处 | 表8和摘要均显式写绝对值。10.5%/10.50%、18.7%/18.71%属显示精度差异，本轮不改变任一数字。 |
| 薄隙网格依赖 | 摘要、§2.1、表4、表S7、结论三 | 对应位置 | h25仅5格及横槽−4.43%已在正文说明；两网格对应偏差分别列示，不当连续解误差界。 |
| 连续模型上界 | 摘要末段、结论一 | Abstract末段、Conclusion 1 | 明确限定理想Stokes模型，独立于离散百分比；摘要明确不确定V2准确度。结论并未把回顾性改善写成由定理保证。 |
| h100固定公式对照 | 摘要第2段、结论四、表S6 | 对应位置 | 系数固定、一个新增间隙、非普遍预测精度；表S6明确不认证严格盲测。摘要未写h100具体尺寸不构成矛盾。 |
| S4仍FAIL及几何区分 | §3.3末、表S8及其后说明 | 对应位置 | h30/d80，1.328387035%>1%；区别于h25主几何及h75历史质量失败。未以GCI通过抵消原FAIL。 |
| 19几何46条比较记录 | §2.1集合说明、结论一、表S6与S8 | 对应位置 | 36主＋8加密＋2新增；构建复现不增加比较几何。旧52项运行清单和含黏度检查的另一46集合明确分开。 |

摘要只列最大偏差，结论另列平均值与35/36，是信息分工，不是统计口径不一致。不要求摘要、结论与每张表逐一重复全部数字或失败细节；必须确保适当位置披露，并避免其他位置出现相反或扩大性主张。

## 两处需统一的措辞

### W1 主比较的5 nm参考，不宜写成涵盖全文所有误差区间

中文§2.3第211行：“因此全文报告的误差区间应理解为……以5 nm生产网格为参考……”；英文对应第205行“The reported discrepancy intervals therefore use the 5 nm production grid as reference.”

上下文可理解为主比较，但按字面范围过宽：表2和表S7还使用2.5 nm参考，表3则相对于解析平板值计算误差。不能将这些不同定义机械统一成5 nm。

建议中文替换为：“主比较中18种几何、36条主方向结果的公式偏差区间，均以5 nm生产网格的OpenLB结果为离散参考。加密对照按各自标明的参考网格报告；平板解析基准的误差以解析值为参考。”保留原段后续敏感性范围与限制，不改数字。

建议英文替换为：“The model-discrepancy ranges for the 36 main principal-direction records at 18 geometries use the 5 nm OpenLB results as discrete references. Refinement comparisons use the reference grid specified for each comparison; flat-wall benchmark errors use the analytical values as references.”

### W2 中文表7“预测流向”与摘要、结论及英文的“重建”未完全统一

中文§4.3标题第337行、表7标题第341行用“预测流向”；本段、摘要与结论则说明是在同一线性张量关系下由主导度重建。英文Table 7第333行已经使用“reconstructed flow direction”。现有中文上下文提供限定，不构成已证实的物理夸大，但表单独引用时容易弱化该限定。

建议§4.3标题改为“两方向的偏差改变各向异性与重建通量方向”。表7标题改为“基准几何（h=75 nm，d=100 nm）的各向异性与重建通量方向”。表头“由显式数值主值计算”可改为“由5 nm OpenLB主导度计算”。保留全部原数值及角度符号。

建议附中文表注：“通量方向由两组主导度按同一线性张量关系重建；不表示实验测得的流向误差。各向异性相对偏差以OpenLB方向比为分母，角差为公式重建角减去OpenLB主值重建角。”英文对应注释可用：“Flux directions are reconstructed from the two sets of principal conductances using the same linear tensor relation; the angle difference is not an experimentally measured error. The relative anisotropy discrepancy uses the OpenLB ratio as denominator, and the angle difference is model reconstruction minus reconstruction from the OpenLB principal values.”

## 三张关键表宜补充的独立表注

### T1 表1：明确主采样矩阵身份

中文第67行、英文第63行。现有标题“采样几何与样点数”及“Sampled geometries and principal-direction samples”未直接写主比较/5 nm，但紧邻正文明确，数字没有冲突。

建议表注：“本表仅列18种主比较几何及其36条5 nm主方向结果，每种几何沿槽、横槽各一条；不包括2.5 nm加密、新增h=100 nm几何及其他控制检查。未采样组合不属于本表覆盖范围。”

英文：“This table lists only the 18 main comparison geometries and their 36 principal-direction results on the 5 nm grid, one per direction at each geometry. Refinements, the added h=100 nm geometry and other controls are excluded. Unsampled combinations are outside this table's coverage.”

### T6 表6：把离散分母和36条集合带进表注

中文第312行、英文第306行。前导句已交代5 nm和18×2，表单独阅读时欠明确。

建议表注：“相对偏差按（局部立方律导度/OpenLB离散导度−1）×100%计算，参考为同几何、同方向的5 nm结果；正值表示公式值较高。每方向18条，合计36条；8条加密与2条新增间隙结果不并入本表。所列范围不代表连续参数域或真实物理误差范围。”

英文：“Relative discrepancy is (local-cubic-law conductance/OpenLB discrete conductance−1)×100%, using matched 5 nm references; positive values indicate larger model values. The table contains 18 records per direction, 36 in total, excluding the eight refinement and two added-gap records. The ranges do not characterize a continuous parameter domain or errors relative to physical reality.”

### T8 表8：将已有段落说明整理为明确表注

中文第374行、英文第366行。现有列头已写最大/平均绝对偏差，紧邻后文已定义算术平均、35/36及15点子集限制，实质一致；建议把这些内容标记为表注并补集合排除项，避免读者误用46作分母。

建议表注：“除单列的15点子集外，每方向统计同一组18条5 nm主结果。最大与平均值均针对相对偏差的绝对值，平均值为算术平均；‘绝对偏差减小’表示固定V2相对于原公式更接近同一离散参考，两方向合计35/36。8条加密和h=100 nm新增2条不纳入本表；h≥50 nm的15点子集不构成连续适用范围或精度保证。”

英文：“Except for the separately listed 15-sample subset, each direction uses the same 18 main records on the 5 nm grid. Maxima and means concern absolute relative discrepancies, with arithmetic means. ‘Absolute discrepancy reduced’ means that fixed V2 is closer than the original law to the same discrete reference, giving 35/36 across both directions. The eight refinement and two added-gap records are excluded. The 15-sample h≥50 nm subset does not establish a continuous applicability range or accuracy guarantee.”

## 其他表注检查

- 表2：已区分5/2.5 nm参考，补充S7已定义差值。可选补注“差值为2.5 nm参考下的百分比偏差减去5 nm参考下的百分比偏差，单位为百分点”，不把+5.39个百分点误写成+5.39%。
- 表3：相对于平板解析值的误差定义合理；不应改成以5 nm离散值为参考，也不能把这张表推广为沟槽全图精度。
- 表4：标题已说明5 nm作分母。可选补完整变化定义100(K2.5/K5−1)%及“不是连续解误差界”；当前后文已有限定。
- 表5：当前标题及前导句说明槽深25→120 nm。可选补“倍率为同间隙下K(d=120)/K(d=25)，使用5 nm结果，仅列三档已采样间隙；不包含h=25 nm未采样的d=120 nm组合”。
- 表S1：52项运行清单身份与19几何46条比较记录不同，当前已分开，勿为统一口径强行改成46。
- 表S2：8行对应四旧几何的两方向，变化归一、百分点差及非误差界限制清楚。
- 表S3：18行周期/多力检查不代表18个新比较几何，当前限定清楚。
- 表S4、S5：当前文稿已将原失败状态及条件性估计随表披露；仅检查这一表述，不重新采用历史数字裁定当前主结论。
- 表S6：6条包括h100两方向、h75构建B两方向及h75历史两方向对照，只有h100增加比较几何；不与46再相加。原A_blind标签不是盲测认证，当前已说明。
- 表S7：每档以本档K为分母，V2有符号偏差与绝对偏差变化判断分开，符合口径。
- 表S8：S4 h30/d80 FAIL、归一方式不同、不并入主统计及不提供误差界均明确；摘要/结论未重复全部控制细节本身不构成冲突。如结论需要自成完整限定，可另加一句指出S4阶段仍FAIL，但不是本轮必须新增的数字内容。

## 可采用的最小修改清单

1. 双语§2.3将5 nm参考的范围限定为36条主比较，并保留加密和解析基准各自定义。
2. 中文§4.3/表7统一“重建通量方向”，补表7参考与差异定义；英文补对应表注。
3. 双语表1、6、8补上上述集合与分母说明；可先只做这三张关键表，不必重写全部表格。

摘要和结论目前没有需要改变的数字，也不需要为了字面一致把所有统计重复一遍。理论/V2、回顾性/独立预测、主比较/补充结果的科学边界保留。以上均为建议文本，未合入正式稿。

本轮仅新增本目录与同步共享状态；四稿SHA保护及结束核对见protected_manuscripts.json、verification.json。无新run_id、求解/编译/拟合、Gate放行、上传或投稿。当前任务完成；若接续采用，执行最小清单后再核双语一致，不新增算例。
