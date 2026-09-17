# SIM-EC1XT240 STEP 5.2 动态材料转换修复候选报告

## 判定

**STEP 5.2 候选 A：FAIL。** 独立候选正确完成第一次 2304 节点 `fluid -> solid` 转换和其后 500 步，且无 NaN/Inf、无非法 link，rho 全过程保持在冻结范围内，转换 population 账本也达到机器精度。但最大 Mach 为 `0.0788251 > 0.05`，最大 `|R_geom|=5.78999e-3 > 1e-3`，因此不能判为修复通过，也不允许进入 STEP 6。

本轮没有修改 OpenLB 库、冻结 STEP 4/STEP 5 程序、几何、物性、tau、dt、壁速、压力边界或验收阈值。候选失败后没有改变层数、参数或继续尝试其他方案。

## 选择的修复方法

选择方向 **A：改进转换节点质量/动量分配**，没有采用平衡态强制重置（B）或改变真实材料转换时刻的分层转换（C）。原因是 STEP 5.1 已直接证明原失败由接收模板的空间重叠产生：2024 个接收节点各接收 5 个源，最大单点格子质量增量 `0.582758`；同时向 Zou/He 节点直接注入 population，使 prescribed rho 与 direct rho 不一致并产生大法向速度。

候选只在 `explicit_piston_conversion_repair_candidate.cpp` 中作以下变化：

1. 每个转换源的 `alpha * F_i` 沿压头法向向下分配给同一局部柱的 8 层持久 material-1 流体节点；
2. material 4/5 压力节点不再作为接收存储节点，压力交线源改由最近的内侧 material-1 柱接收；
3. 对压力源，将 19 个 `F_i` 用统一系数缩放，使其总和与该 Zou/He 节点规定的 boundary rho 一致，同时保留 population 形状和归一化速度；
4. 仍逐方向守恒转移 population，不清零接收节点、不裁剪 rho/u、不做全域质量归一化。

8 层深度在运行前冻结：普通柱预计增加约 `alpha/8 ~= 0.0625`；压力相邻内侧柱最多承接两个源，预计增加约 `0.125`。该值未根据运行结果调整。

## 程序与运行

- 独立程序：`explicit_piston_conversion_repair_candidate.cpp`
- 冻结 STEP 5 SHA-256：`24f31902eb2e8d7b566354424551a56d9918f01308368755641811c6ee5aa5eb`
- 候选程序 SHA-256：`beaf2dd6e7bfe62417219f8c29ca2defa4484c074e9d01e2d77a5526aee78219`
- run-id：`conversion_repair_A_column8_v1_20260908`
- 命令：`mpirun -np 1 ./explicit_piston_conversion_repair_candidate`
- OpenLB：`5953d8a-dirty`
- 转换 step：3595，`h=72.4989847248 nm`
- 完成 step：4095，即转换后 500 步
- 退出码：3，表示冻结验收失败，不是运行异常

## 转换瞬间

| 指标 | 原 STEP 5 FAIL | 候选 A |
|---|---:|---:|
|转换节点数|2304|2304|
|material 1/4/5 转换数|2208/48/48|2208/48/48|
|转移相对账本误差|`1.58419e-4`|`-4.03585e-15`|
|receiver 转移后 rho 范围|最高 `1.58381`|`[1.05822,1.13677]`|
|首次推进后 receiver 最大 Mach|压力节点 `0.59930`|内侧流体节点 `0.03254`|
|非法 link|0|0|

候选成功消除了向压力节点直接堆积约半个格点质量的首要局部冲击，并使转换 population 账本闭合到浮点舍入量级。

## 500 步结果

| 量 | 原 STEP 5 FAIL | 候选 A | 冻结标准 | 判定 |
|---|---:|---:|---:|---|
|完成转换后步数|500|500|500|PASS|
|最大 Mach|`1.085249925`|`0.0788250751`|`<=0.05`|FAIL|
|rho 全过程范围|`[0.837008053,1.561065783]`|`[0.970753149,1.113655445]`|`[0.8,1.2]`|PASS|
|最大 `|R_geom,macro|`|`7.633616e-3`|`5.789990e-3`|`<1e-3`|FAIL|
|最终 `R_geom,population`|`8.331094e-3`|`5.749802e-3`|辅助核对|FAIL 量级|
|NaN/Inf|0|0|0|PASS|
|最大非法 link|0|0|0|PASS|
|转换计数/几何预测|2304/2304|2304/2304|一致|PASS|

相对原 FAIL，候选最大 Mach 降低约 `92.7%`，最大 rho 恢复到冻结范围；质量残差仅降低约 `24.2%`，仍明显超限。

## 新异常位置与演化

候选第一次也是全过程最大 Mach 超限发生在转换 step 3595 的首次推进后：

- lattice：`(13,47,33)`；
- 物理坐标：`(67.5,237.5,162.5) nm`；
- material：5，高 y Zou/He 压力面；
- 最大速度：`22.7548392 m/s`；
- Mach：`0.0788250751`；
- 同步 rho 范围：`[0.989103226,1.112688582]`；
- 最大绝对 shifted population：`|f18|=0.0478948740`；
- 非法 link：0。

这与 STEP 5.1 的直接接收异常不同：候选没有把质量写入 pressure cell，但内侧柱接受的扰动在首次 collision/streaming 后到达相邻压力面，仍造成短时 Mach 超限。step 3596/3597 的最大 Mach 分别为 `0.05576/0.05632`，step 3600 降至 `0.04920`；说明初始尖峰明显减弱但未达到原门槛。

rho 没有违反冻结阈值。全过程 rho 最大值 `1.113655445` 出现在 step 3804，最小值 `0.970753149` 出现在 step 3968。

`R_geom,macro` 在转换后的 step 3595 为 `-9.28975e-4`，当时尚在门槛内；随后变为持续积累的正残差，step 3700 为 `7.22355e-4`、step 3800 为 `1.73724e-3`、最终 step 4095 为 `5.78999e-3`。因此失败不只是转换瞬间的代数账本误差，而是重分配扰动之后的开放边界通量与移动控制体积质量收支没有持续闭合。

## 输出

- `output/conversion_repair_A_column8_v1_20260908/post_conversion_history.csv`
- `output/conversion_repair_A_column8_v1_20260908/conversion_event.csv`
- `output/conversion_repair_A_column8_v1_20260908/conversion_population_before_after.csv`
- `output/conversion_repair_A_column8_v1_20260908/result.txt`
- `output/conversion_repair_A_column8_v1_20260908/run_manifest.txt`
- `output/conversion_repair_A_column8_v1_20260908/run.log`
- `step5_conversion_repair_console.log`
- `step5_conversion_repair_exit_code.txt`

## 结论范围

候选 A 证明：扩大局部接收深度并隔离压力接收节点能够解决原来的 rho 爆发和 population 转移账本误差，但不足以满足 Mach 与移动控制体积质量收支门槛。程序完成 500 步不等于验证通过。

**STEP 5.2 FAIL；停止在动态材料转换修复阶段，不进入 STEP 6。**

Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is **SIM-EC1XT240**.
