# SIM-EC1XT240 STEP 5.1 单次材料转换根因诊断报告

## 结论

STEP 5.1 已完成，诊断结果为 **ROOT CAUSE LOCATED**，但 STEP 5 数值验收仍为 **FAIL**。第一次 `fluid -> solid` 转换在 step 3595 发生，共转换 2304 个节点。数值异常在转换后的首次 collision 之前已经存在，因此首要制造异常的操作不是 collision、streaming 或 Bouzidi，而是冻结 STEP 5 算法中的局部 population 质量/动量转移。

该算法把每个被转换节点的 `alpha * F_i` 分摊到其下方平面最多五个持久 fluid 邻居。多个源节点的接收集合重叠，使单个接收节点在一个事件中接收约半个格点质量；接收源数最高为 5。最大接收节点的直接密度由 1.00105 瞬时升至 1.58381。压力材料节点上还出现“Zou/He momenta 给出的规定密度为 1、population 直接恢复密度为 1.51974”的不一致，超额 populations 被解释为很大的法向速度，产生 Mach 0.907915。第一步推进只传播并部分改变了这个冲击，并非异常起点。

本轮未修改 STEP 5 算法、OpenLB、物性、时间步、壁速、几何或边界条件，也未运行 STEP 6。

## 运行与数据来源

- 独立程序：`explicit_piston_conversion_root_cause_diag.cpp`
- 冻结基线：`explicit_piston_single_conversion_ledger.cpp`
- run-id：`conversion_root_cause_diag_v1_20260908`
- 命令：`mpirun -np 1 ./explicit_piston_conversion_root_cause_diag`
- OpenLB 版本：`5953d8a-dirty`
- 程序退出码：0；含义仅为诊断完整执行，不代表 STEP 5 通过
- 转换步：3595
- 转换前后流体材料节点数：57600 -> 55296
- 输出目录：`output/conversion_root_cause_diag_v1_20260908/`

程序复现冻结 STEP 5 的转换和接收规则，只运行至第一次转换及其后的一个 `collideAndStream`，没有继续进行完整位移。

## 1. 首异常定位

冻结阈值为 `Mach <= 0.05`、`0.8 <= rho <= 1.2`。两个阈值均在 step 3595、转换完成但尚未 collision 时首次违反。

| 事件阶段 | 指标 | lattice 坐标 | 物理坐标 (nm) | material | rho（边界接口） | rho（population 直接恢复） | 速度 | Mach |
|---|---:|---|---|---:|---:|---:|---|---:|
| 转换后、collision 前 | 最大 Mach | (13,47,34) | (67.5,237.5,167.5) | 5 / 高 y 压力面 | 1 | 1.519740841 | (0,0.524184738,0) | 0.907914599 |
| 转换后、collision 前 | 最大 rho | (34,1,34) | (172.5,7.5,167.5) | 1 / fluid | 1.583809779 | 1.583809779 | (4.51e-5,7.09e-5,-4.06e-4) | 7.18e-4 |
| 首次 collide/stream 后 | 最大 Mach | (13,47,34) | (67.5,237.5,167.5) | 5 / 高 y 压力面 | 1 | 1.307926903 | (0,0.346005351,0) | 0.599298848 |
| 首次 collide/stream 后 | 最大 rho | (34,2,34) | (172.5,12.5,167.5) | 1 / fluid | 1.454026978 | 1.454026978 | (0.00141,-0.00629,-0.07122) | 0.1239 |

转换前后的完整异常 cell populations 见 `first_anomaly_cells.csv`。在压力节点 `(13,47,34)`，异常速度是 Zou/He 规定的 `rho=1` 与突然增大的 population 总和共同恢复出的法向速度；这不是“密度仍为 1 所以状态正常”。

## 2. 转换事件质量与动量账本

OpenLB 当前 descriptor 存储 shifted populations，直接物理 population 为 `F_i = f_i + w_i`。报告同时保存边界 momenta 接口和直接 population 恢复两种口径。

| 阶段 | 几何加权质量：边界接口 (kg) | 几何加权质量：直接恢复 (kg) | 相对转换前变化：边界接口 (kg) | 相对转换前变化：直接恢复 (kg) |
|---|---:|---:|---:|---:|
| 转换前（当前 h） | 7.1040775306e-18 | 7.1047065305e-18 | 0 | 0 |
| 转换后、collision 前 | 7.0983347993e-18 | 7.1047065305e-18 | -5.7427313305e-21 | -1.1823431123e-32 |
| 首次 collide/stream 后 | 7.0934692138e-18 | 7.0985306495e-18 | -1.0608316765e-20 | -6.1758810318e-21 |

直接 population 口径显示，转移操作在全局几何加权质量上做到约 `1.2e-32 kg` 的代数守恒；但它没有保证局部状态平滑或与压力边界 moments 一致。边界接口口径在 collision 前已少 `5.74e-21 kg`，主要来自压力节点 prescribed-rho 与直接 population 状态的分离。全部三分量动量与 19 个 population 总和见 `conversion_mass_momentum_budget.csv`。

## 3. Population 逐方向变化

19 个方向都发生了接收和活跃域变化。最大单 cell shifted-population 突变是 `f0`：

- `max |delta f0| = 0.18325887982032446`
- cell `(13,1,34)`，material 1，物理坐标 `(67.5,7.5,167.5) nm`

较大的斜向单 cell 变化包括 `f8/f18` 约 0.047895，以及 `f9/f17` 约 0.047842。它们是整套 `alpha * F_i` 转移的组成部分，而不是某一个独立 boundary-link 的无源生成。逐方向总和、最大变化幅度和位置见 `conversion_population_trace.csv`。

压力异常 cell `(13,47,34)` 从 4 个转换源接收：

- 接收格子质量：0.5250901896
- 直接 rho：0.9946506516 -> 1.5197408412
- 边界 rho：1 -> 1
- 转移后 Mach：0.907914599

这证明首个 Mach 爆发在 redistribution 完成后已经形成。

## 4. Receiver 分布

共有 2400 个唯一接收 cell，源节点重叠统计为：

| 每个 receiver 的源数 | receiver 数 |
|---:|---:|
| 1 | 96 |
| 3 | 8 |
| 4 | 272 |
| 5 | 2024 |

最大接收量位于 `(34,1,34)`，物理坐标 `(172.5,7.5,167.5) nm`：

- source count：5
- 接收格子质量：0.5827578515
- 接收物理质量：7.2844731443e-23 kg
- 直接 rho：1.0010519273 -> 1.5838097789
- 首次推进后 rho：1.1333522557

因此异常不是总质量凭空增加，而是一次转换中把转换层的质量高度集中到单层、且接收模板重叠的持久 fluid 节点。完整 receiver 坐标、来源数、接收质量/动量、前后 rho/Mach 和各方向接收量见 `receiver_mass_distribution.csv`。

## 5. Bouzidi link 检查

| 指标 | 转换前 | 转换后 |
|---|---:|---:|
| 被转换层相关 Bouzidi link | 11708 | 11708 |
| 全部活跃 link | — | 32176 |
| 非法 link | — | 0 |
| 跨周期恢复 link | — | 192 |
| 错误 solid link | — | 0 |

转换前 q 范围为 `[0.00011502345, 0.5]`；转换后新一层链接的 q 为约 `0.999796945`，仍在合法范围。壁速系数由约 `±3.18000798e-4` 连续变为 `±3.18078487e-4`。材料转换确实按几何改变了 link 所有者和交点，但没有生成非法 q、遗漏链接或错误周期 solid link。逐 link 记录见 `conversion_link_change.csv`。

因此 Bouzidi 更新不是首次异常制造者：异常在 Bouzidi/碰撞/流送之前的接收 population 中已经可见。

## 根因判定

根因链为：

`2304 个 fluid 节点同时转 solid`
-> `冻结算法把 alpha * F_i 分摊到下方五点 receiver 模板`
-> `模板重叠，2024 个 receiver 各接收 5 个源`
-> `局部直接 rho 瞬时最高达到 1.58381`
-> `压力节点 prescribed rho=1 与 direct populations 不相容`
-> `Zou/He moments 恢复出强法向速度，Mach 最高 0.907915`
-> `随后 collision/streaming 将局部冲击传播到邻域`。

所以，STEP 5 FAIL 的首因是转换 redistribution 的局部闭合/接收策略产生过度集中的非平衡 population 状态；压力边界处的 moments 约束进一步把该不一致转换为大速度。全局直接质量近乎守恒不能替代局部稳定性和边界兼容性验收。

本报告只定位问题，没有实施修复或调参。STEP 5 仍为 FAIL，STEP 6 未执行。

## 输出文件

- `output/conversion_root_cause_diag_v1_20260908/conversion_population_trace.csv`
- `output/conversion_root_cause_diag_v1_20260908/receiver_mass_distribution.csv`
- `output/conversion_root_cause_diag_v1_20260908/conversion_mass_momentum_budget.csv`
- `output/conversion_root_cause_diag_v1_20260908/conversion_link_change.csv`
- `output/conversion_root_cause_diag_v1_20260908/first_anomaly_cells.csv`
- `output/conversion_root_cause_diag_v1_20260908/run_manifest.txt`

历史内部路径中的 `ex240` 名称为保持可复现性而保留；正确模型名称为 **SIM-EC1XT240**。
