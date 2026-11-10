# 核心结论与修正公式验证口径（作者审阅稿）

本文件是本轮核心结论的可审计版本。正文三章、摘要与范围文件已同步修订；标记供内部追溯，不用于期刊排版。机器检查不能替代人工作者确认，当前不具备投稿放行状态。

## 一、建议采用的论文核心结论

在固定间隙、全充液、连续介质、牛顿无滑移的理想周期矩形沟槽中，Jain等价局部立方律在已采样的18种几何、36个主方向工况上均高估输运系数；沿槽偏差为+10.30%～+204.85%，跨槽为+8.11%～+54.19%。这些是相对于离散数值参考解的样点偏差，不是任意几何的普适误差界。[claim:C001] [evidence:E001,E002]

两方向偏差不同，因而既影响通量也影响各向异性及斜向流向。在h=75 nm、d=100 nm、驱动相对槽轴45°时，DNS主值给出通量角24.3424°，原闭合给出15.1412°，相差−9.2012°。D3用DNS主值检验张量关系，不证明原闭合的流向正确，也未验证液滴前沿。[claim:C002] [evidence:E001,E002]

经验修正能改善部分样点，但当前证据只支持“限定数据组、限定版本”的残差报告；不支持连续参数域的统一精度保证。侧壁剪切与台阶附近流动重分布是候选解释，尚未完成独立的机制定量分离。[claim:C003] [evidence:E002]

### 可直接用于结论章的英文

For the 18 sampled ideal rectangular-groove geometries, the arithmetic–harmonic local-cubic-law closure overestimates both depth-integrated transport coefficients. The observed discrepancies are +10.30–+204.85% parallel to the grooves and +8.11–+54.19% perpendicular to them. Unequal principal-value errors also bias the anisotropy and the predicted direction of oblique flow. These findings characterize sampled closure discrepancies relative to discrete numerical references, whose uncertainty has not been bounded over the full parameter domain.[claim:C004] [evidence:E001,E002]

The original empirical correction improves predictions at three withheld-depth geometries, with maximum absolute residuals approximately within 17% and 4% in the parallel and perpendicular directions. However, its parallel calibration residual reaches 28.09%, and no continuous-domain 20% accuracy guarantee is justified. A subsequent correction proposal improves retrospective residuals but remains exploratory because its model selection followed access to extension results. Quantitative separation of side-wall and step-region contributions, genuinely unseen-condition prediction tests for the revised model, and validation of dynamic filling are not established.[claim:C005] [evidence:E001,E002]

## 二、固定误差定义，不用改分母掩盖残差

原闭合误差为 E_i=(K_model,i/K_DNS,i−1)；修正残差为 r_i=(F_i K_model,i/K_DNS,i−1)=F_i(1+E_i)−1。正文百分数为上述无量纲量乘100。正号表示高估，负号表示低估；分母始终为对应几何、方向、网格的DNS参考值。[claim:C006] [evidence:E001,E002]

## 三、公式版本分开，不静默替换

V1为原拟合的舍入表达：F_parallel=1/[1+1.7207(d/H_ref)^1.8046]，F_perp=1/[1+0.5276(d/w)^0.8259]，H_ref=h+d/2。保留原脚本及原留出检验；本轮没有重新拟合。[claim:C007] [evidence:E002,E003]

V2为后续提案的舍入表达：F_parallel=1/[1+1.7685(d/w)^1.6331]，F_perp=1/[1+0.4900(d/w)^0.6990]。本轮只评价已给公式，没有复现其minimax优化；不把系数、变量和适用域的事后选择称为预先固定，也未批准替换V1。[claim:C008] [evidence:E002,E004]

**【2026-10-18 11:55 修订，作者已批准采用 V2】** C008 中「没有复现其minimax优化」这一条已不成立，补记为 [claim:C008a]：

- **复现已补齐**：`CASE/D_series/D2_groove_error_map/analysis_fit_v2.py` 从结果 CSV 重算两组建模的全部系数与残差，输出 `results/analysis/v2_fit_params.csv`、`v2_residuals.csv`、`V2_FIT_REPORT.md`。脚本固定了校准集（d∈{25,50,100}×h∈{50,75,125}，9 几何 18 残差）、目标函数（minimax，与所报「最大绝对残差」口径一致；另报 RMS 作敏感性对照）与多起点搜索，**无手填数字**，任何人可重跑。
- **全精度系数**：a∥=1.768488、b∥=1.633079；a⊥=0.489952、b⊥=0.699049。正文与图采用舍入值 1.7685/1.6331、0.4900/0.6990；两者残差差异在小数第三位（如校准集跨槽 4.1855% 对 4.189%），引用时须注明用的是哪一组。
- **RMS 对照**（回应「改善是否来自拟合准则」）：同形式改用最小二乘得 a∥=1.8515/b∥=1.6260、a⊥=0.5264/b⊥=0.8119，域内最大残差仅由 10.5% 升至 13.1%（沿槽）、6.9% 升至 9.1%（跨槽）⇒ 改善主体来自**变量由 d/H_ref 换成 d/w**，非拟合准则。
- **作者决定**：采用 V2 作为论文正式关系（Eq. 3），V1 降为文档化对照（Eq. 2）。**C008 中「未批准替换V1」一条据此撤销。**
- **C014 的约束仍全部有效并被遵守**：正文只写「所报为采样域上界、非连续域保证」，未写预先规定判据；V2 被明写为**数据知情的模型修订**（变量选择发生在扩展批次算完之后），d=75 仅作留出复核而非「完全独立最终测试」。
- **C016 的约束被遵守**：跨槽因子主动排除 h=25 并明确不声明该处精度（实测 −18.7%），未以最优常数掩盖。

**【一处必须知会的自我更正，[claim:C008b]】** 先前给作者的口头表述「改用 d/w 后残差随间隙的系统性消失」**不成立**：实测残余 h 依赖仅由 14–37 个百分点降至 6–21，**且符号翻转**（h=50 偏正、h=125 偏负），并未消除。该更正已写入第 1 章 ¶5、PPT 与 A1 决策备忘；文稿据此把 V2 的适用范围写成「采样域上界」，并明确不外推至 h>125 nm。

**同步改动位置（2026-10-18）**：第 1 章 ¶5(iii) 与 ¶6、摘要（10.5%/6.9%，删去 exploratory 定性）、PPT P8 与 P2 及 `correction_validation.png`（按 V2 重绘，左留出右全 18 档）、`CORRECTION_MODEL_FIT_20261017.md`（加 V1 历史标注）、`SIM240_第一篇范围重定位` §1、`SIM240_论文骨架` 待办第 8 项、`AI_HANDOFF_20261015.md` 与 `SIM240_AI_CONTEXT.md`（加处置注）、`交付物缺陷审计_20261017.md` A1。


### 现有样点最大绝对残差（%）

以下数值按上述公布的舍入系数重新求值；不等于用全精度系数复现拟合，亦不包含DNS参考不确定度。每组“几何数”按单方向计，同几何P/T不算独立几何。[claim:C009] [evidence:E001,E002]

| 数据组 | 几何数 | V1沿槽 | V1跨槽 | V2沿槽 | V2跨槽 | 证据 |
|---|---:|---:|---:|---:|---:|---|
| 原标定集 | 9 | 28.091 | 5.670 | 9.914 | 4.189 | [claim:C010] [evidence:E001] |
| 原留出深度d75 | 3 | 16.873 | 3.470 | 9.334 | 3.858 | [claim:C011] [evidence:E001] |
| 深度扩展d120 | 3 | 38.582 | 9.212 | 10.505 | 6.921 | [claim:C012] [evidence:E001] |
| 间隙扩展h25 | 3 | 43.912 | 19.962 | 7.213 | 18.705 | [claim:C013] [evidence:E001] |

原d75组支持原先固定V1的有限留出深度检验。对后来V2，它与其他扩展数据已在模型选择时可见，即使未进入系数优化器，也不能重新叫作完全独立最终测试。V2的“±12%/±8%”只能说明事后样本残差的概括，不是预先规定判据或连续域保证。[claim:C014] [evidence:E002,E004]

不能把d/w≤0.83作为经验证的±20%边界：100/120=0.833333虽在严格十进制边界之外，但0.625至0.83之间没有相应样点证明整段满足。改写边界或取整不能增加证据。[claim:C015] [evidence:E001,E002]

只依赖d/w的跨槽乘法因子不能同时任意精确覆盖所有h：在d=100 nm、h=25/50/75/125 nm四点上，即使自由选最优单一F，最小可达的最大相对残差仍约12.3397%。这是该四点集的限制，不反驳主动排除h25的候选适用范围。[claim:C016] [evidence:E001,E002]

## 四、数值证据与公式证据分开验收

48次正式运行=36地图方向工况+4加密+2黏度+6斜向驱动。既有审计扫描228211行诊断，所查运行指标未见超限；不等于完整源码/构建/环境验收，更不是48种独立几何。[claim:C017] [evidence:E001,E002]

5→2.5 nm的0.33%～0.52%沿槽变化及0.72%～2.16%跨槽变化仅来自h50/d100和h125/d25。1.25 nm的0.125%/0.551%是归档细网格GCI；沿用该拟合所得5 nm条件估计约1.01%/3.08%，不能变成全域误差条。细T来源限制须随表说明。[claim:C018] [evidence:E001,E002]

旧细T的历史FAIL保留；方案C有原始PASS与独立exit0，但所引用的独立放行报告当前路径缺失。原审查前completion、历史独立放行记载、后续环境哈希问题与本轮输出复核是不同证据状态，不互相覆盖。[claim:C019] [evidence:E001,E002]

## 五、下一步验证口径（计划，尚未执行）

如继续开发修正公式，先保存完整实现、参数精度、优化目标、约束、起点/种子、优化器版本和收敛记录；清楚记录数据何时进入系数拟合、变量选择和范围选择。不得用重算残差冒充复现优化。

内部交叉验证按完整几何分组，同一几何的两方向及不同网格必须同组。变量/模型/超参数选择应在训练折内部重复；不能先用全部数据选型、再只对已选系数交叉验证并称完全无泄漏。可考虑留一深度/留一间隙评估，但它们仍是内部稳健性检查，不抹去已发生的数据接触。

若要报告冻结后预测精度，应先锁定公式版本、使用条件、允许误差和参考解不确定度要求，再使用未参与此前模型选择的条件检验。新仿真需另行授权；本轮不启动、不准备下一Gate、不恢复机制积分。

## 六、解释纪律

固定G和μ时，J=KG/μ；正的间隙弹性意味着增大h提高通量。η_i=K_i/(H_ref³/12)是等体积参照的通流能力比，不是静止体积分数。“η=0.18即82%死空间”与“减小间隙提高跨槽通量”均撤回；本文现有范围不包含移动压头导致G随时间变化的推断。[claim:C020] [evidence:E002]

高耗散颜色不能单独证明高阻力；固定驱动下通量增加也会增大总功率。现有耗散图只能提供空间线索，不能代替物理域上的能量闭合、牵引分解和局部收敛。机制收支继续暂缓。[claim:C021] [evidence:E002]

## 七、文件与责任

本轮修改：引言、方法、验证三章，投稿包摘要/候选标题/验证建议，首篇范围v2.1及共享状态。旧稿副本位于before/。冻结卡、原始输出、求解器未改。**（2026-10-18 11:55 补）** 拟合实现现已补齐为 `analysis_fit_v2.py`，此前「拟合实现未改」是因为当时尚未建立该脚本，现状见 C008a。

证据索引见source_manifest.json，逐主张哈希见claims.csv，文字/数值与输入稳定性检查见validation.json。人工作者尚未确认，submission_ready=false。该台账覆盖本文件核心主张，不冒充对全稿每条文献、全部方法或期刊政策的完整核验。

使用scientific-writing的证据绑定和探索性/验证性分层规则；由AI辅助修改，作者责任、最终科学判断及投稿披露仍待确认。未向外部检索服务发送未发表稿件；联网仅核对公开工具论文元数据。

流程引用：Kassis, T.; Agarwal, V.; He, Y.; Patel, D.; Brueckner, A. M. *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. arXiv:2609.00065v2，DOI:10.48550/arXiv.2609.00065；本轮核对公开记录。此引用仅说明写作流程，不作流动物理证据。 [claim:C022] [evidence:E005]
