# S4 已结束结果的完整独立复核（AI 辅助内部工作报告）

**结论：六条原生计算及逐条独立验收通过；S4 在横槽网格门停止，整个阶段未通过。** 沿槽三网格通过；横槽中—细变化1.328387035%超过原1%上限，虽细网格GCI估计0.912232592%通过另一项，仍不能补偿前项失败。不改门槛、不重跑、不加时、不进入S5。

## 1. 范围、结束证据与来源

用户此前已要求“批次实际结束后，按原URV-v1／MRP／A1／S4-MIP-v1／S4-FRD-v1完整独立分析已有结果”。本轮询问是否结束，14:29:14北京时间只做一次进程/完成记录快照，确认无目标控制器或原生进程，原会话已消失；六份completion和自动acceptance齐全。最后网格报告文件修改时间为2026-11-04T14:14:04.884067+08:00（文件系统辅助时间，不伪称独立退出时刻）。控制日志保存原文 `EvidenceError: S4 grid evidence failed; no retry/extension/next stage`。S4_grid_report.json存在且总GRID_CHECKS_PASS=false，S4_completed.json不存在，符合冻结控制器先写网格报告、失败即停的代码路径。父控制器独立退出码未记录，不能从报错自行补造为2；六条原生独立退出码和本轮六条检查器退出码均确证为0，无原生超时/资源停止。

正式release：`CASE/unseen_v2_reference_S4_reuse_v1/evidence/S4_formal_launch_release_v1_20261104_01.json`；SHA `e5f7de1e584b776f8cc9bf1dbb31f198422ce10984ba8ad7d729220afdcdd19b`。全部3284项输入重哈希一致；核对准备B、原18＋6零步及来源/前序S3控制、真实正式授权和资源决策。精确复用S1 ELF `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`，OpenLB `882924a9cfc8dcdf82909e39530789cb6f5ebcc4`；本轮未构建或重新执行限定指令审计，依靠封存来源与同一ELF身份核对。

六个run_id按原序保留：

- `URV_S4_P_dx5_reuse_v1_20261103_01`
- `URV_S4_T_dx5_reuse_v1_20261103_01`
- `URV_S4_P_dx2p5_reuse_v1_20261103_01`
- `URV_S4_T_dx2p5_reuse_v1_20261103_01`
- `URV_S4_P_dx1p25_reuse_v1_20261103_01`
- `URV_S4_T_dx1p25_reuse_v1_20261103_01`

原协议入口 `docs/reports/URV_S4_formal_scope_resource_review_20261104_090724/PROTOCOL.md`；原科学门槛 `CASE/unseen_v2_reference_checker_S4_reuse_v1/common/acceptance_spec.json`；执行源 `CASE/unseen_v2_reference_S4_reuse_v1/scripts/run_S4.py`。源码、配置、合同、旧原始结果与自动接受记录未修改。

## 2. 实际完成的复核

在本报告新目录执行六次冻结check_results.py，每次仅读取已有结果并将新记录写到replay_<run_id>；六次保存场读取共读回68帧。每份新acceptance.json与fields.json分别与原自动文件完全一致。逐个核对completion绑定、计算前后输入映射、原始输出集合及内容；合计238个原始输出、69368558bytes（completion另计）。3563份受保护文件前后内容不变。

重新计算61650行诊断、54852个完整统计窗；各条最后一窗均为首次全部满足稳态条件，前一窗至少一项不满足。除冻结检查器复算外，报告脚本另外直接复算末窗样本标准差/跨度、质量账本、密度/Mach/Re、截面流量差、K与三网格算术。复核边界与实际场的单位、方向、材料/节点/链数、q、保存时间和场积分闭合。这个独立性指从原始证据重做验收，并不新增另一种物理解法或实验验证。

## 3. 参数与六条结果

固定间隙全充液单相、无滑移矩形沟槽：h=30nm，d=80nm，w=120nm，周期及Ly=240nm，平均厚度H=h+d/2=70nm；rho=1000kg/m³，nu=1e-6m²/s，mu=0.001Pa·s，a=100000m/s²，tau=1。沿槽P为+y，横槽T为+x；x/y周期，Bouzidi静止壁，D3Q19_FORCE/ForcedBGK。不是移动挤压/两相流计算，不输入V2系数。

J为单位平面面积的体积流量（m²/s）；K=nu·J/a，单位m³；平均速度U=J/H；阻力系数R=mu/K。单条求解墙钟包含该原生进程初始化和输出，不是纯步进时间。

|方向|dx (nm)|实际步数|原生求解秒|K (m³)|NUMERICAL_GATE／RESULT_PASS／geometry_PASS|
|---|---:|---:|---:|---:|---|
|P|5|2096|14.776|2.769129925729e-23|PASS／true／true|
|T|5|1209|9.025|3.647976923758e-24|PASS／true／true|
|P|2.5|8387|430.614|2.754644779507e-23|PASS／true／true|
|T|2.5|3935|196.586|3.517910669378e-24|PASS／true／true|
|P|1.25|33480|11635.868|2.750102454185e-23|PASS／true／true|
|T|1.25|12537|4326.036|3.471791836745e-24|PASS／true／true|

六条原生耗时合计16612.905s（4.614696h），不含检查/哈希等其他耗时；细格P/T分别3.232185/1.201677h，均在12h原上限内。各条前可用内存≥12GiB、盘≥8GiB，首条记录盘≥100GiB，输出均≤4GiB；不把这些快照当成全程RSS峰值或资源硬界。

## 4. 数值与几何门槛

|方向／dx nm|末窗相对std|末窗相对span|补偿质量最大相对变化|旧质量最大相对变化|最大密度偏差|最大Mach|末态截面相对差|
|---|---:|---:|---:|---:|---:|---:|---:|
|P／5|9.96966938e-07|3.44845884e-06|7.6426e-16|0.0000e+00|8.8818e-16|1.4108e-07|0.0000e+00|
|T／5|9.84635345e-07|4.39606261e-06|2.4838e-15|7.7438e-13|1.8196e-08|2.7298e-08|1.4402e-06|
|P／2.5|9.99887289e-07|3.48400114e-06|3.8213e-16|0.0000e+00|8.8818e-16|7.0647e-08|0.0000e+00|
|T／2.5|9.63279630e-07|4.95867849e-06|4.3945e-15|1.4918e-12|4.8940e-09|1.2789e-08|2.2240e-07|
|P／1.25|9.99776410e-07|3.49127785e-06|3.8213e-16|0.0000e+00|3.3307e-16|3.5330e-08|0.0000e+00|
|T／1.25|8.27721573e-07|4.98765217e-06|4.3945e-15|2.5541e-11|1.2731e-09|6.2652e-09|9.4018e-07|

六条均满足原规则：补偿质量严格<1e-10（本次最大4.39448301e-15），质量双账本差≤1e-13（最大2.60527259e-16），密度偏差≤1e-6，Mach严格<0.05，Re_H≤0.01（最大1.07700353e-05），完整末窗样本std≤1e-6/span≤5e-6，横向通量≤1e-12m²/s（最大1.70590779e-20），末态截面差≤1e-5。

三网格流体节点32256/258048/2064384，壁面链30528/122496/490752；材料计数/几何掩膜通过；q_min=q_max=0.5，候选链与安装链相等，fallback/unresolved均0。体积相对误差最大1.88511429e-11<1e-10；各条全序列有限，保存场与双精度切片/全域积分闭合通过。原生RESULT_PASS=false表示留给外部独立检查；外部RESULT_PASS=true，两者不混淆。

末窗靠近门槛符合首次达标即停的控制规则；它只说明时间稳态合格，不能替代空间网格检查。旧质量列原样保留并复算，无历史差异删除。h75精确回归和密度捕获重放仅适用S0，本次标记NOT_APPLICABLE_S0_ONLY，不虚填S4密度重放PASS。已有MRP/A1指令审核的范围限制及历史唯一归因NOT_ESTABLISHED保持。

## 5. 三网格：明确保留横槽失败

原规则r=2、Fs=1.25；K随加密同向变化、差分不近零且观测阶p正且有限。中细差 `abs(K_medium/K_fine-1)` 与细网格GCI估计均须≤1%。从新验收记录重做s4_grid，再独立直接计算阶数/两门，与原控制器网格报告完全一致。

|方向|观测阶p|中—细变化（上限1%）|细网格GCI估计（上限1%）|方向网格判定|
|---|---:|---:|---:|---|
|P|1.673071307|0.165169313%|0.094320912%|PASS|
|T|1.495818803|1.328387035%|0.912232592%|FAIL|

沿槽通过。横槽中—细变化超出门槛0.328387035个百分点，故横槽及S4整体GRID_CHECKS_PASS=false。不能只挑GCI通过项、把1%改成2%、把单条稳态通过当网格通过，或因六条已算完补写成功S4_completed.json。GCI与u仍为数值敏感性估计，不是严格误差界/置信区间。本轮未证明超差的具体物理或离散误差机制，也不由此认定V2失败或成功。

## 6. 科学结论与下一停点

已验证：六条固定离散网格结果各自通过原数值/几何/流场核对；沿槽三网格符合原阶段门。未通过：横槽三网格中—细变化门，S4阶段接受=false。未评价：S5三驱动力控制、跨阶段参考资格/F04、原公式/V2正式比较、物理验证和投稿资格。

`REFERENCE_QUALIFIED_FOR_CASE=false`，`reference_qualified=false`，`MODEL_COMPARISON=NOT_EVALUATED`，`physical_validation=NOT_EVALUATED`，`strict_error_bound_established=false`，`submission_ready=false`，F04 OPEN。S0–S3已接受证据不因本次失败自动撤销；旧FAIL、380项旧差异、MRP静态FAIL、旧v1 HOLD、S2-LRP、第一候选B拒绝记录与作者外部非使用声明范围继续保留。作者声明不等于外部历史独立取证。

下一具体动作只可另定横槽网格未过的处置审查范围，先核证据是否足以判断空间离散问题及需要何种最小补证；不在本报告自动设计/实施第四网格、续算、改公式或门槛，也不进入S5。长计算若以后需要仍另行授权；此次分析无需再索同范围结果分析授权。

## 7. 审核限度与文件

本报告为AI辅助的内部计算验收工作报告，非人工科学终审或期刊审稿决定。作者仍需亲自理解/复核并负责。未宣称实验或完全独立软件参考实现，不把同一检查器的重复执行误写为独立物理验证。

证据入口：status_snapshot.json、controller_log_tail.txt、protected_inputs_and_outputs.json、independent_review.json、independent_grid_report.json、run_summary.csv、supplementary_verification.json以及六个replay目录。review_completed.py可读但单次输出拒绝覆盖，不应为查看报告再次运行。此前intake多余policy_context字段被验证器拒绝，初稿保留；移到单独context说明后声明验证通过。这只是报告工具接口修正，无科学门槛/结果改动，也未引起CFD检查重跑。

使用[peer-review](/home/dell/.codex/skills/peer-review/SKILL.md)与[scientific-writing](/home/dell/.codex/skills/scientific-writing/SKILL.md)。技能工具出处：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026), *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*, [arXiv:2609.00065](https://arxiv.org/abs/2609.00065)。2026-11-04公开元数据核对为v2，无期刊版本记录；该来源仅解释工作流程，不支持本项目CFD数值结论。公开查询未包含项目内容。
