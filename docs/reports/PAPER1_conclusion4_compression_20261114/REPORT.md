# 结论第四条压缩候选（2026-11-14）

> 本包只出候选，不改任何母本。采纳与否、采纳哪一个，由用户决定。
> 三个被引用文件的当前指纹（改前）：
> 中文稿 `7f85e77c7155c143`／96904 B；英文稿 `4badbe87609fa3cb`／109026 B；结论文件 `98080077d3ea3a47`／21474 B。

## 0 一句话结论

两个候选都通过"数字一个不丢"的机器核对（0 孤儿）。**推荐候选 A**：数字全保、只重排结构，中文 644→608 字（−5.6%），英文 2226→2029 字符（−8.8%）。候选 B 更短（中文 644→513，−20.3%），代价是把方向比与重建角的四个汇总数字退回 §4.5，结论层不再给出这两个指标的改善幅度。

## 1 为什么要改这一条

中文稿六条结论里，第四条 644 字，其余五条在 110—260 字之间。它同时装了六件事：主集统计、薄隙单点、子集上限、间隙漂移、有限元对照、等权矩阵。后果是"35/36 总体改善"这个主句被夹在中间，读者刚读到主句就撞上两段限定和一段 DOE，容易读成"结论其实不成立"。用户 2026-11-14 定的口径是：**主句突出"总体改善，但不保证逐点或方向比改善"；DOE、漂移和各项数字继续留在对应表格中。**

## 2 结构裁决：结论文件与母本 §6 可以不一样

这一点必须先说清，否则下次又会被当成"两份文件不一致"的 bug。

| 文件 | 职能 | 第四条当前形态 |
|---|---|---|
| `PAPER1_conclusions_current_20261109.md` | 六条口径的唯一仲裁件，必须留全量数字 | 本来就是三段：主集 L58、有限元独立对照 L60、DOE 说明 L107（标题已写明"不属于六条结论正文"） |
| 中文稿 / 英文稿 §6 | 给读者看的摘要 | 把上述三段并成一段 |

所以"不对称"不是错误，是职能不同。**本包不动结论文件**（`98080077…` 保持），只把母本 §6 压成"主句 + 交叉法一段 + 指针"，细节留在 §4.4／§4.5／§4.6 与结论文件。

交接时必须一起写的一句话：**§6 第四条不再出现 7.93、42.72、5.02、7.63、1.51，不等于这些数字被撤回**——它们分别在 §4.4 L434、§4.5 L456 与结论文件 L58／L60 原位。

## 3 候选 A（推荐）

### 3.1 中文稿 §6 第四条

**改前（L594，644 字）**

**四、** 使用固定V2系数回顾性比较同一主集合，沿槽平均绝对偏差由88.85%降至6.40%，横槽由30.63%降至4.42%，合计35/36条绝对偏差减小；该 $d/w$ 单变量经验修正的残余最大绝对值分别为10.50%与18.71%。h=25 nm、d=100 nm横槽条件的改善判断随5/2.5 nm参考改变，h≥50 nm子集的6.92%不是连续适用范围承诺。V2残差的间隙依赖仍需与模型选择、参数估计和参考误差分别评价。 固定d100的沿槽残余在h75与h100间变号，漂移7.93个百分点>5个百分点；缺少h/w的因子表达能力有限，离散参考贡献仍待排除。在与本文主集合并列的有限元独立离散对照中（§4.5，17个横槽成对几何），固定V2的横槽平均绝对偏差为4.21%、有符号均值+1.83%，方向比与45°重建角的平均绝对偏差亦由42.72%与5.02°降至7.63%与1.51°；但3个几何的这两项指标同时恶化，局部立方律的方向比在2个几何上本就低估，故改善是总体性的而非逐点的。该集合与本文36条5 nm主统计分属不同参考与不同几何集合，不作合并；其中新增有限元计算待正式采用，既有有限元结果保留有限采用建议及溯源限制，既有合格有限体积法记录保留资格；本比较不构成物理验证。 在所列等权采样矩阵中，固定 V2 的沿槽有符号残余仍呈间隙相关差异；所列参数趋势在更换数值对照后保留。这支持按采样条件评价单变量因子的局限，不单独确定唯一的缺失变量、物理原因或连续参数域精度。

**候选 A（608 字，−5.6%）**

**四、** 使用固定V2系数回顾性比较同一主集合，沿槽平均绝对偏差由88.85%降至6.40%，横槽由30.63%降至4.42%，合计35/36条绝对偏差减小，残余最大绝对值分别为10.50%与18.71%（表8）。改善是总体性的，但不保证逐点改善，也不保证方向比改善：h=25 nm、d=100 nm横槽点的改善判断随5/2.5 nm参考改变，h≥50 nm子集的6.92%只对该子集成立（§4.4）。在与主集合并列的有限元独立对照中（§4.5，表9、表10，17个横槽成对几何），固定V2的横槽平均绝对偏差为4.21%、有符号均值+1.83%，方向比与45°重建角的平均绝对偏差由42.72%与5.02°降至7.63%与1.51%，但3个几何的这两项指标同时增大，局部立方律的方向比在2个几何上本就低估，故改善同样是总体而非逐点的。该集合与36条5 nm主统计分属不同参考与不同几何集合，不作合并；新增有限元计算待正式采用，既有有限元结果保留有限采用建议及溯源限制，既有合格有限体积法记录保留资格；本比较既非物理验证，也不构成连续参数域的精度保证。V2残差的间隙依赖、固定d100沿槽残余在h75与h100间的变号与漂移幅度，以及残余须与模型选择、参数估计和参考误差分别评价，见§4.4；等权矩阵下的间隙相关差异见§4.6。这些均指向仅以$d/w$为自变量的因子表达有限，但不单独确定唯一的缺失变量或物理原因。

### 3.2 英文稿 §6 第四条

**改前（L586，2226 字符）**

**4.** Retrospective comparison using the fixed V2 coefficients reduces the along-groove mean absolute discrepancy from 88.85% to 6.40% and the transverse value from 30.63% to 4.42%, improving 35/36 main records. Maximum absolute residuals of this $d/w$-only empirical correction are 10.50% and 18.71%, respectively. At h=25 nm, d=100 nm, the local transverse improvement assessment changes between 5 and 2.5 nm references. The 6.92% maximum in the h≥50 nm subset is not a continuous applicability guarantee. Residual gap dependence must be assessed separately from model selection, parameter estimation and reference error. At fixed d100, the along-groove residual changes sign between h75 and h100 and drifts by 7.93 percentage points > 5 percentage points; the factor omits h/w, while the discrete-reference contribution remains unresolved. In the independent finite-element discretization comparison listed alongside the present main set (§4.5, 17 paired transverse geometries), fixed V2 gives a transverse mean absolute discrepancy of 4.21% with a signed mean of +1.83%, while the mean absolute deviations of the direction ratio and the 45° reconstructed angle fall from 42.72% and 5.02° to 7.63% and 1.51°; at three geometries both metrics worsen, and the local-law direction ratio is already underestimated at two geometries, so the improvement is overall rather than pointwise. That set and the present 36-result 5 nm main statistics use different references and different geometry sets and are not merged; the new finite-element runs await formal adoption, legacy finite-element results retain their limited-use recommendation and provenance limitations, and qualified finite-volume records retain their qualification. The comparison constitutes neither physical validation nor a continuous-domain guarantee. Within the specified equally weighted matrix, the fixed-V2 along-groove signed residual retains gap-related variation, and the listed parameter trends persist after changing the numerical comparison. This supports evaluating the limitations of the single-variable factor under the sampled conditions, but does not identify a unique missing variable or physical cause, or establish continuous-domain accuracy.

**候选 A（2029 字符，−8.8%）**

**4.** Using the fixed V2 coefficients, a retrospective comparison on the same main set reduces the along-groove mean absolute discrepancy from 88.85% to 6.40% and the transverse value from 30.63% to 4.42%, improving 35/36 records, with maximum absolute residuals of 10.50% and 18.71% (Table 8). The improvement is overall rather than pointwise or uniform in the direction ratio: the transverse record at h=25 nm, d=100 nm changes its improvement assessment between the 5 and 2.5 nm references, and the 6.92% for the h≥50 nm subset holds only within that subset (§4.4). In the independent finite-element comparison listed alongside the main set (§4.5, Tables 9 and 10, 17 paired transverse geometries), fixed V2 gives a transverse mean absolute discrepancy of 4.21% with a signed mean of +1.83%, and reduces the mean absolute deviations of the direction ratio and the 45° reconstructed angle from 42.72% and 5.02° to 7.63% and 1.51%; yet both metrics increase at three geometries and the local-law direction ratio is already underestimated at two, so this improvement is likewise overall rather than pointwise. That set and the 36-record 5 nm main statistics use different references and different geometry sets and are not merged; the new finite-element runs await formal adoption, legacy finite-element results retain their limited-use recommendation and provenance limitations, and qualified finite-volume records retain their qualification; the comparison is neither a physical validation nor a guarantee of continuous-domain accuracy. Gap dependence of the V2 residual, the sign change and drift magnitude of the fixed-d100 along-groove residual between h=75 and h=100 nm, and the need to assess the residual separately from model selection, parameter estimation and reference error are reported in §4.4, while the gap-related variation on the equally weighted matrix is reported in §4.6; all indicate a limited expressive capacity of a factor in $d/w$ alone, but do not identify a unique missing variable or physical cause.

### 3.3 A 逐条改了什么

1. **主句前置。** 第一句直接给"沿槽 88.85→6.40、横槽 30.63→4.42、合计 35/36、残余最大值 10.50／18.71（表8）"，主句与量化在同一句结束。
2. **新增定性判断提前。** "改善是总体性的，但不保证逐点改善，也不保证方向比改善"放在第二句句首；原文这句在段末（"故改善是总体性的而非逐点的"），读者要读到 400 字后才看到。
3. **薄隙两句并一句。** h25／d100 随参考改变 + 6.92% 只对该子集成立，合成一句并加 `（§4.4）`。删去原文独立的"V2 残差的间隙依赖仍需与模型选择、参数估计和参考误差分别评价"，该要求并入末句保留。
4. **漂移退出结论层。** "漂移 7.93 个百分点 > 5 个百分点"改为"变号与漂移幅度，见 §4.4"。原位 §4.4 L434 完整保留 7.93、5 个百分点门槛和"结构筛查 FAIL 保留"。
5. **DOE 三句压成一句指针。** "等权矩阵下的间隙相关差异见 §4.6"。§4.6 与结论文件 L107 保留全部分额。
6. **交叉法一段数字全保。** 4.21／+1.83／42.72／5.02／7.63／1.51、3 个几何、2 个几何、四类资格句（不作合并／待正式采用／有限采用建议及溯源限制／保留资格）逐项保留，只删"亦""该 $d/w$ 单变量"等冗余。
7. **一处措辞对齐。** "本比较不构成物理验证"→"既非物理验证，也不构成连续参数域的精度保证"。原因是英文原句本来就有后半句，中文缺一半；补的是限制，不是主张。

## 4 候选 B（更短，代价明确）

### 4.1 与 A 的唯一实质差别

删掉"方向比与 45° 重建角的平均绝对偏差由 42.72% 与 5.02° 降至 7.63% 与 1.51%"，改为"方向比与 45° 重建角总体改善"。四个数字退回 §4.5 L456。

代价要说清：表 10 只列 3 个恶化几何各自的 $A$ 与 $\beta$ 值，**不含 17 对的汇总**。所以 B 一旦采纳，**结论层就没有方向比改善的量化支撑**，读者必须翻到 §4.5 才知道幅度。这正是审稿人会问"只用一个求解器"的地方，删掉风险不小。

**候选 B 中文（513 字，−20.3%）**

**四、** 使用固定V2系数回顾性比较同一主集合，沿槽平均绝对偏差由88.85%降至6.40%，横槽由30.63%降至4.42%，合计35/36条绝对偏差减小，残余最大绝对值为10.50%与18.71%（表8）。改善是总体性的，但不保证逐点改善，也不保证方向比改善：个别点的判断随参考网格改变，h≥50 nm子集的6.92%只对该子集成立（§4.4）。在与主集合并列的有限元独立对照中（§4.5，表9、表10，17个横槽成对几何），固定V2把横槽平均绝对偏差降至4.21%、有符号均值+1.83%，方向比与45°重建角总体改善，但有3个几何的这两项指标同时增大，故该组改善同样是总体而非逐点的。该集合与36条5 nm主统计分属不同参考与不同几何集合，不作合并；新增有限元计算待正式采用，既有有限元结果保留有限采用建议及溯源限制，既有合格有限体积法记录保留资格；本比较既非物理验证，也不构成连续参数域的精度保证。V2残差的间隙依赖与漂移变号，以及残余须与模型选择、参数估计和参考误差分别评价，见§4.4；等权矩阵下的间隙相关差异见§4.6。这些均指向仅以$d/w$为自变量的因子表达有限，但不单独确定唯一的缺失变量或物理原因。

**候选 B 英文（1782 字符，−19.9%）**

**4.** Using the fixed V2 coefficients, a retrospective comparison on the same main set reduces the along-groove mean absolute discrepancy from 88.85% to 6.40% and the transverse value from 30.63% to 4.42%, improving 35/36 records, with maximum absolute residuals of 10.50% and 18.71% (Table 8). The improvement is overall rather than pointwise or uniform in the direction ratio: individual records change their assessment with the reference grid, and the 6.92% for the h≥50 nm subset holds only within that subset (§4.4). In the independent finite-element comparison listed alongside the main set (§4.5, Tables 9 and 10, 17 paired transverse geometries), fixed V2 reduces the transverse mean absolute discrepancy to 4.21% with a signed mean of +1.83%, and improves the direction ratio and the 45° reconstructed angle overall, yet both metrics increase at three geometries, so this improvement is likewise overall rather than pointwise. That set and the 36-record 5 nm main statistics use different references and different geometry sets and are not merged; the new finite-element runs await formal adoption, legacy finite-element results retain their limited-use recommendation and provenance limitations, and qualified finite-volume records retain their qualification; the comparison is neither a physical validation nor a guarantee of continuous-domain accuracy. Gap dependence of the V2 residual and its drift and sign change, and the need to assess the residual separately from model selection, parameter estimation and reference error are reported in §4.4, while the gap-related variation on the equally weighted matrix is reported in §4.6; all indicate a limited expressive capacity of a factor in $d/w$ alone, but do not identify a unique missing variable or physical cause.

## 5 数字去向的机器核对

**方法。** 先剔除章节号（§4.4）、表号（表8／Table 9）、补充材料号（S7）、几何标签（h75／d100／(50,25)）与长度单位（nm），再比较原第四条与候选的数字集合。对被删的每个数字，在全篇搜索其它出现位置并记录所属章节；搜不到即判"孤儿"，核对直接失败。

**结果。**

| 候选 | 语言 | 字数变化 | 删除的数字 | 其它出处 | 孤儿 |
|---|---|---|---|---|---|
| A | 中 | 644→608（−5.6%） | 7.93 | §4.4（1 处） | 0 |
| A | 英 | 2226→2029（−8.8%） | 7.93 | §4.4（1 处） | 0 |
| B | 中 | 644→513（−20.3%） | 7.93；42.72／5.02／7.63／1.51 | §4.4（1 处）；§4.5（各 1 处） | 0 |
| B | 英 | 2226→1782（−19.9%） | 同 B 中 | §4.4；§4.5 | 0 |

逐数字明细见 `NUMBER_MAP.csv`（42 行：语言、数字、A 是否保留、B 是否保留、外部出处数、出处列表）。

**两条限制，如实记录：**

- 7.93、42.72、5.02、7.63、1.51 的其它出处各只有 **1 处**，且都在**正文段落**里，不是表内数字。严格按"留在对应表格中"读，A 与 B 都只满足"留在对应章节"，B 更进一步把四个数留在了表 10 旁边的正文。若要求必须落在表内，只能选 A 并接受这一点，或另做加行（本包不做）。
- 核对脚本 `tmp/audit_item4_ab.py`、`tmp/emit_number_map.py` 属本轮临时工具，未提交；方法已写在上文，可按同样规则复现。

## 6 建议

**选 A。** 三条理由：

1. 用户要求的"总体改善，但不保证逐点或方向比改善"已经落在第二句句首，读者不必读到段末。
2. A 不牺牲任何量化支撑；结论第四条本来就承担"两个集合"的说明义务，比其余五条长是它的职能，不是缺陷。
3. 跨方法对照是回应"单一求解器"质疑的唯一材料，结论层只剩 4.21% 一个数会明显削弱它。

若更看重六条篇幅整齐，选 B；但要接受"结论层不再给方向比幅度"这一后果，并在 §4.5 开头确保读者能看到 42.72→7.63／5.02→1.51（现已满足，L456）。

## 7 未做 / 采纳后的连锁

- 本轮**未改任何母本**，本包只是候选。
- 采纳时的连锁（按固定顺序）：改中英母本 → `build_submission.py` 重跑派生投稿件（两份哈希会变）→ 更新 authority 表两行与 `MANIFEST.md` → 同步 `SIM240_AI_CONTEXT.md` 与最新 `AI_HANDOFF`。结论文件不动，`98080077…` 不变。
- 未改 §4.4／§4.5／§4.6 任何文字，未改表 8／9／10。
- 仍未处理、属 C7 范围：旧采用报告 §3.2"17 个横槽点没有任何解析解或严格界"与附录 E 冲突，正确收窄应为"未建立逐点连续解数值误差的严格界"。
- 仍未处理、属另一 AI 包内问题：`PAPER1_reference_closeout_review_20261114/REPORT.md` 引用的 `CONTRIBUTION_AND_PROVENANCE.md` 全库不存在。
