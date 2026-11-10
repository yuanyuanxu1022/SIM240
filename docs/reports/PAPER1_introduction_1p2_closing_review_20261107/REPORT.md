# §1.2末段审读与整节收束

日期：2026-11-07。用户要求审读理论上界、5nm离散参考与工艺精度边界并统一本节收束。本轮为明确范围文字/主张对应核对，沿用现有理论审查，不重新推导或冻结定理，不自动合入正式稿。

## 原段

> 本文比较局部立方律与显式数值主值的偏差幅度及方向差异，并检查经验修正的剩余残差。理想Stokes模型中的主导度上界另见附录E；本文不把正偏差本身作为新颖性的充分依据。当前比较以5 nm离散结果为参考，为评价降阶模型提供数值证据，尚不能据此认定其已具备工艺预测精度。

## 逐句裁定

1. 原首句重复第三段已经明确的“双向偏差、各向异性、既定修正评价”。改为“连续模型性质与数值比较分开评价”，让末段承担证据层级和结论范围的收束，不再次列工作清单。
2. 原“理想Stokes模型中的主导度上界另见附录E”方向正确，但需明确原公式、两个主方向、连续解身份与定理不提供的精度信息。按当前附录E，条件包括h>0、固定周期矩形槽、全充液、不可压缩常黏度牛顿流体、静止无滑移壁与单一均匀驱动。两主值各自满足非严格上界，平板d=0可取等号；不能自动约束离散KLB，不能推出方向比偏差符号、V2精度或具体耗散份额。完整条件留附录/方法，段中用“所述模型”回指。
3. “不把正偏差本身作为新颖性的充分依据”是合理的审查约束，但作为正文句偏重自我辩护。删去该句不会增加首次/排他性主张；前面文献关系与具体工作内容已给出定位。本轮不据此认定全面新颖性已经审定。
4. 保留“5nm离散参考”，明确是主比较而非全部记录均5nm；四种旧几何的2.5nm加密另作参考敏感性，不替换主统计，也不是全地图连续误差界。h100补充比较与构建复现继续按正文数据角色，不在这一收束段重复计数。
5. 工艺精度边界保留，但与研究用途连在一起：为降阶输运近似评价提供依据，不保证实际填充时间、动态挤压、载荷或真实胶行为。静态OpenFOAM平均模型接入只支持所测实现/单位/方向/通量一致性，不能据其补出工艺精度。无需在引言末段逐项重列这些未研究物理。
6. “采样几何与指定离散参考”的限制明确修饰定量比较；不能把理论上界错误限于18/19个已算几何或5nm网格。上界成立范围由连续模型假设决定，定量比较范围由样本与参考决定。

## 三层证据的对应

| 层次 | 对象与作用 | 不能自动支持 |
|---|---|---|
| 原公式的理论上界 | 附录E所列连续Stokes模型中两主方向K*≤K_LC | 离散网格无误差、偏差百分数、方向比误差符号或V2准确度 |
| 数值比较 | 5nm主集合评价相对离散结果的偏差，2.5nm局部加密另列敏感性 | 全地图连续参考资格、全参数域精度或独立预测认证 |
| 应用意义 | 为降阶输运近似评价与后续系数使用提供依据 | 实际动态压印、填充时间、载荷或真实胶精度 |

此表是主张对应关系，非新增数学证明、数值验收或物理验证。原S4 FAIL等记录不因收束措辞改变。

## 中文候选

> 本文将原公式的连续模型性质与数值比较分开评价。附录E表明，局部立方律给出所述周期Stokes模型中两主方向连续导度的上界，但不确定偏差幅度或V2准确度。主比较以5 nm显式计算结果为离散参考，加密结果另用于检查参考敏感性。定量比较的结论限于采样几何与指定离散参考，为评价降阶输运近似提供依据，尚未建立连续参数范围或实际压印过程的精度保证。

## 英文对应候选

> We assess the continuous-model properties of the original formula separately from its numerical comparison. Appendix E shows that the local cubic law bounds both principal continuous conductances from above in the stated periodic Stokes model, without determining discrepancy magnitudes or V2 accuracy. The main comparison uses groove-resolved results on a 5 nm grid as discrete references; refinements separately characterize reference sensitivity. The quantitative comparison is restricted to the sampled geometries and specified discrete references. It informs assessment of the reduced transport approximation without establishing accuracy guarantees over a continuous parameter domain or for the actual imprinting process.

## §1.2整节衔接

- 第一段候选：Jain/Ban的过程应用及Patir–Cheng的平均关系来源，说明为什么关注这类局部系数。
- 第二段候选：Dewangan–Datta近邻理论与数值研究，明确小参数/完整谱解等方法层次。
- 第三段候选：本文对象、系数换算、特定方波表达式的限制与实际工作内容。
- 本末段：区分连续模型上界、离散定量比较与应用精度，以范围清楚的评价意义收束。
- 后续§1.3负责具体研究设计与任务安排，不再次完整复述文献综述；该节尚未由本轮重写，合入时再核重叠。

四段可以在逻辑上接续，但“逐段已审”不等于已合入或已完成全文终审。此前候选保留原文件，本轮不回写旧报告。没有新文献身份、引文调整或外部文献检索。

## 核对与停点

本轮实际读当前中英文§1.2及§1.3、中文方法数据角色与参考限制、讨论§5.4、附录E全文，并对照已有主张终审报告及前三段审读候选。只检查现有定理的文字引用范围，不重新证明E1–E6，不将旧报告中的历史未合入任务当作当前状态。科学采用与整篇最终审定仍由作者负责。

输入哈希见source_manifest.json；主稿字节保护也覆盖其摘要、附录E、数值表与书目。verification.json记录原文保持及状态更新范围，不把哈希检查当成独立科学验证。使用已读scientific-writing和academic-humanizer；程序性来源沿用§1.2第一段审读报告所列Kassis等Scientific Agent Skills（2026，arXiv:2609.00065），不另加正文科学引文。

本轮只新增本目录及更新两共享状态；正式中英文引言尚未合入已审候选，前轮实际摘要合入保持。无新增数值计算或验证、编译/求解/拟合/场处理/run_id/Gate/上传，原数据/系数/门槛保持；S4原FAIL、reference_qualified=false、strict_error_bound_established=false、submission_ready=false不变，无新长算授权或命令。

下一具体动作：按逐部分节奏审§1.3研究问题与工作安排，检查与本节收束重复及主/加密/新增数据身份；若用户明确要求合入，再同步已审引言中英文候选并核衔接。本轮不是最终理论或投稿放行。
