# SIM-EC1XT240 STEP 5.2 Candidate B 局部 rho/u 重构报告

## 判定

**Candidate B：FAIL。** 第一次 2304 节点 `fluid -> solid` 转换和后续 500 步均已完成；无 NaN/Inf、无非法 link，rho 保持在冻结范围内，转换质量账本达到机器精度。但是最大 Mach 为 `0.188021 > 0.05`，最大 `|R_geom|=5.57187e-3 > 1e-3`。本轮在失败后停止，未进入 STEP 6。

没有修改 OpenLB、STEP 4/STEP 5 冻结程序、Candidate A、几何、tau、dt、壁速、物性或 Zou/He 边界。

## 方法

Candidate B 保持 Candidate A 已冻结的局部受影响区：每个转换源对应压头法向下方 8 层持久 material-1 节点，且 pressure material 4/5 不作为接收节点。区别是：

1. 不把源节点的 19 个 populations 直接逐项加到接收节点；
2. 先由源状态计算应转移的宏观质量和三分量动量；
3. 对每个接收节点汇总所有源的增量；
4. 令目标矩为接收节点原有 `rho/j` 加分配的 `delta rho/delta j`；
5. 用本机 OpenLB `Cell::iniEquilibrium(rho,u)` 一次性重构该节点的 19 个 populations，其中 `u=j/rho`。

该方法保留局部目标质量和动量，但主动丢弃受影响区域原有及源 populations 携带的非平衡应力。没有把 rho/u 重置为 1/0，也没有裁剪、全域归一化或调整参数。

## 运行信息

- 程序：`explicit_piston_conversion_repair_candidate_b.cpp`
- run-id：`conversion_repair_B_equilibrium_column8_v1_20260908`
- 命令：`mpirun -np 1 ./explicit_piston_conversion_repair_candidate_b`
- OpenLB：`5953d8a-dirty`
- Candidate B SHA-256：`614e3cb36269fb69e71e2a71d7613892746d00cd3468dea85a50c71aef593fac`
- 冻结 STEP 5 SHA-256：`24f31902eb2e8d7b566354424551a56d9918f01308368755641811c6ee5aa5eb`
- 转换 step：3595，`h=72.4989847248 nm`
- 完成 step：4095，即转换后 500 步
- 退出码：3，表示验收失败

## 转换质量与动量账本

- 转换节点：2304，与几何预测一致；
- material 1/4/5 来源：2208/48/48；
- 转移质量：`1.47606903859e-19 kg`；
- 转移相对误差：`-1.60772e-17`；
- 转移格子动量：`(0.00531234318, 3.28807139e-5, -0.561880894)`；
- 非法 link：0。

局部平衡重构没有破坏转换瞬间的代数质量账本。受影响节点重构前 rho 范围为 `[0.993964,1.024667]`，重构后为 `[1.058217,1.136766]`；局部状态仍在冻结 rho 区间内。

开放域 500 步质量收支为：

| 量 | 结果 |
|---|---:|
|初始 `M_geom`|`7.2000000000e-18 kg`|
|最终 `M_geom`|`7.0956045842e-18 kg`|
|域内质量变化|`-1.0439541579e-19 kg`|
|累计 macro 流入|`3.4661851674e-19 kg`|
|累计 macro 流出|`4.9113139684e-19 kg`|
|累计向外净质量|`1.4451288010e-19 kg`|
|最终 `R_geom,macro`|`5.5718700e-3`|
|最终 `R_geom,population`|`5.5421596e-3`|
|最大 `|R_geom,macro|`|`5.5718700e-3`|

虽然转换瞬间账本闭合，但域内质量减少量与累计向外净质量之差仍为 `4.01175e-20 kg`，即初始质量的 `5.57e-3`，未满足 `1e-3`。

## 首异常 cell

第一次 Mach 超限即为全过程最大值，发生在转换 step 3595 的首次推进后：

- lattice：`(13,47,34)`；
- 物理坐标：`(67.5,237.5,167.5) nm`；
- material：5，高 y Zou/He 压力边界；
- 最大速度：`54.2770743 m/s`；
- Mach：`0.188021301`；
- 同步 rho 范围：`[0.989103226,1.113319172]`；
- 非法 link：0。

受影响 material-1 节点在重构完成、推进前的最大 Mach 仅 `0.0014671`；第一次推进后，受影响节点自身最大 Mach 增至 `0.0665473`，全局压力面 cell 达到 `0.1880213`。因此异常不是重构前目标 rho/u 已超阈，而是大范围局部平衡重构形成的离散状态界面经过首次 collision/streaming 后，在邻近 Zou/He 压力面产生更强速度脉冲。

Mach 随后为：step 3596 `0.134287`、step 3597 `0.116304`、step 3600 `0.102299`、step 3610 `0.075781`。到 step 4095 仍为 `0.068921`，没有在 500 步内持续回到门槛下。

rho 全过程为 `[0.958019127,1.113983664]`，没有违反 `[0.8,1.2]`：最大值在 step 3597，最小值在 step 3691。

## 与原 FAIL 和 Candidate A 对比

| 指标 | 原 STEP 5 | Candidate A | Candidate B | 标准 |
|---|---:|---:|---:|---:|
|最大 Mach|`1.085250`|`0.0788251`|`0.188021`|`<=0.05`|
|rho 范围|`[0.837008,1.561066]`|`[0.970753,1.113655]`|`[0.958019,1.113984]`|`[0.8,1.2]`|
|最大 `|R_geom|`|`7.63362e-3`|`5.78999e-3`|`5.57187e-3`|`<1e-3`|
|转换相对账本误差|`1.58419e-4`|`-4.04e-15`|`-1.61e-17`|`<=1e-12`|
|NaN/Inf / 非法 link|0 / 0|0 / 0|0 / 0|0 / 0|

Candidate B 继续控制了 rho，并使转换账本闭合，但最大 Mach 比 Candidate A 更高；质量残差只从 Candidate A 的 `5.78999e-3` 小幅降至 `5.57187e-3`，仍显著不合格。由此可知，简单把整个局部受影响区重构为平衡态不是充分修复，并且丢弃其非平衡应力会加剧第一次推进时的速度不连续。

## 输出文件

- `output/conversion_repair_B_equilibrium_column8_v1_20260908/post_conversion_history.csv`
- `output/conversion_repair_B_equilibrium_column8_v1_20260908/conversion_event.csv`
- `output/conversion_repair_B_equilibrium_column8_v1_20260908/conversion_population_before_after.csv`
- `output/conversion_repair_B_equilibrium_column8_v1_20260908/result.txt`
- `output/conversion_repair_B_equilibrium_column8_v1_20260908/run_manifest.txt`
- `output/conversion_repair_B_equilibrium_column8_v1_20260908/run.log`
- `step5_conversion_repair_candidate_b_console.log`
- `step5_conversion_repair_candidate_b_exit_code.txt`

## 最终结论

Candidate B 未满足 Mach 和 `R_geom` 门槛，判定 **FAIL**。失败后没有改参数或继续其他修复；STEP 6 未启动。

Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is **SIM-EC1XT240**.
