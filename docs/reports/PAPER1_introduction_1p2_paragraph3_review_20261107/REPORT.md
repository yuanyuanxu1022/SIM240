# §1.2第三段审读：比较条件、量纲换算、方波限制与贡献句

日期：2026-11-07。用户授权逐段审读并压缩重复；本轮输出双语候选，不合入正式引言。本轮无新增数值计算或验证。

## 原段

> 已有工作在所解问题和系数定义上与本文各有区别。Jain等[1]以图案化模板下的各向异性输运组织压印流动模型；本文将问题收窄为固定、全充液单胞中的系数比较，不借用过程模型结果认证这些系数。Patir–Cheng[4]印刷第15页式（23）、（24）在局部Reynolds模型中给出横向调和与纵向算术平均；乘回其归一化高度的三次方后才可与本文深度积分导度比较，不能直接混用流量因子与单位为m³的K。Dewangan–Datta[5]的§4.1—4.2选择平滑形貌与三角形沟槽作理论—有限元对照，§4对方波形貌指出特定谱级数发散及相应表达式不适用，不能直接作为本文矩形台阶的同条件解。本文增加的是这一固定矩形槽族中原公式双向偏差、各向异性后果及既定经验修正表现的配套评价，不据上述区别宣称首创。文献核对范围见补充材料S11。

## 四项裁定

1. **同条件差异。** 本文与Jain的过程模型研究问题不同，可说明过程尺度与局部系数评价的侧重点；不能由此断言Jain从未作系数验证，也不把过程模拟结果或平均模型双实现当作本文显式导度的独立参考。“匹配条件”指本文公式—显式离散结果的成对比较，涵盖几何、物性、边界/驱动及通量归一化；不声称已与这些文献建立同几何参数的逐点对照。对应K定义及均匀体力与压力梯度的线性响应解释沿用正文方法，本轮不新建比较或重审参考资格。

2. **系数换算。** 原段“乘回其归一化高度的三次方”表述不完整且容易混淆有量纲参考间隙与无量纲高度。对这里引用的Patir–Cheng压力流因子φ_i，记有量纲参考间隙为h0，可写K_i=(h0³/12)φ_i；K为m³，φ无量纲。h0不是本稿的最小残隙h，不能把同名符号直接代入。所引一维关系给出K_parallel=〈H³〉/12、K_perp=1/(12〈H⁻³〉)，属于局部Reynolds模型；不是所有流量因子的一般换算，也不认证矩形台阶全场解。若用m²的平均速度渗透率，须在相同平均/驱动定义下再通过参考高度转换，不能仅改单位标签。引言留简要说明，具体式子与原文印刷15页式23/24定位留§2.3和补充S6。

3. **方波限制。** 本轮定向重读[5]§4开头：方波高度跳变导致S1发散，影响其式3.11、3.21渗透率表达式及3.25有效滑移表达式。本段只保留这一特定限制，删去上一段已介绍的平滑/三角形有限元对照。它不能推出所有非光滑形貌、谱方法或连续Stokes解失效，不能据此声称CFD是唯一途径。其未能直接给出本几何参考，不等于本研究首创。

4. **贡献句。** 保留固定矩形槽族的双向偏差、各向异性后果、既定经验修正评价。补“离散结果”和“回顾性”，避免把量化偏差写成相对连续真值的已知误差、把既定V2写成已独立验证的新预测公式。删除正文“本文增加的是……配套评价”的笼统措辞，不以排他性或首次口吻陈述。全面新颖性、普适精度或投稿就绪不由本轮裁定。

## 压缩安排

| 原段内容 | 本段处理 | 详细内容所在 |
|---|---|---|
| Jain的过程应用 | 缩为与本文局部评价的对象区别，保留[1] | 前段已审引用分工 |
| Patir–Cheng算术/调和及原文式号 | 不重复平均介绍，保留[4]及恢复量纲要求 | §2.3/补充S6及既有原文页图 |
| Dewangan的平滑与三角形有限元对照 | 本段删去重复 | §1.2第二段候选 |
| 特定方波表达式限制 | 一句保留，限定到相关摄动表达式，保留[5] | 原文§4及补充S11 |
| 贡献与“非首创”句 | 用工作内容和评价身份表达 | 下一段继续审上界与参考边界，不叠加空泛免责声明 |
| 文献核对范围见S11 | 不再单独占正文一句 | 补充S11及本审读报告仍保留来源边界，不删除证据 |

## 中文候选

> 与压印过程模拟[1]相比，本文聚焦固定间隙、全充液、无滑移周期矩形沟槽中的导度，将局部立方律与显式计算的离散结果比较。Patir–Cheng平均关系[4]按参考间隙恢复量纲后，统一为深度积分导度K（m³；见§2.3及补充S6）。Dewangan–Datta[5]在方波形貌下的特定谱级数发散限制了其相关摄动表达式，故这些表达式不能直接作为本文矩形台阶的同条件参考。本文在匹配几何、物性和边界条件下，量化双向公式偏差及其各向异性后果，并回顾性评价既定经验修正。

## 英文对应候选

> Compared with process-scale imprint simulations [1], the present study focuses on conductance in fixed-gap, fully filled, no-slip periodic rectangular grooves, comparing the local cubic law with discrete groove-resolved results. The Patir–Cheng averaging relations [4] are dimensionalized using the reference gap and expressed as depth-integrated conductance K in m³ (§2.3 and Supplementary S6). For square-wave topographies, divergence of a specific spectral sum limits the associated perturbation expressions of Dewangan and Datta [5], preventing their direct use as matched reference solutions for the rectangular steps studied here. At matched geometry, fluid properties and boundary conditions, we quantify directional formula discrepancies and their consequences for anisotropy, and retrospectively evaluate a fixed empirical correction.

## 实际核对范围

本轮读取当前中英文§1.2、补充S5/S6以及前两段审读报告；重新目视本地Patir印刷第15页式23/24页图，并定向重读本地[5]发表版提取文本的方波限制。不是全文逐式复证，未新增网页检索、文献身份或新颖性检索。Jain应用范围沿用前段已核出版社可见材料，本轮未重读其全文；相关限制如实继承。

输入哈希见source_manifest.json，本轮保护正式中英文稿、补充及原文/前轮报告；验证见verification.json。只作文字与关系核查，不将输入保持计为科学验证。使用已读scientific-writing与academic-humanizer；程序性来源沿用§1.2第一段报告所列Kassis等Scientific Agent Skills（2026，arXiv:2609.00065），不另加正文科学引文。

## 停点

正式中英文引言均未改，前两段候选仍未合入；已合入摘要保持。无编译/求解/拟合/流场处理/新run_id/新验收/Gate或上传，S4原FAIL、reference_qualified=false、strict_error_bound_established=false、submission_ready=false不变。无新计算命令或长算授权。

下一具体动作：继续审§1.2末段的理论上界、5nm离散参考及工艺精度边界，统一本节收束；若用户明确要求采用候选，再同步中英文并检查整节重复。
