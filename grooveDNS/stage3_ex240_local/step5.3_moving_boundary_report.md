# SIM-EC1XT240 STEP 5.3 Moving Boundary Compression Validation

## 判定

本轮得到两个必须分开的结论：

1. **转换前移动边界压缩：PASS。** 在固定 fluid material 拓扑仍与连续压头一致的全部 3594 步内，无 NaN/Inf、无非法 link、rho 和 Mach 合格，`max |R_geom|=9.28533e-4 < 1e-3`。
2. **无 material conversion 的完整 10 nm 移动：FAIL / 不可表示。** 原 D3Q19+Bouzidi 实现以 fluid owner—solid neighbor 链接表示壁面。step 3595 起有 2304 个仍标为 fluid 的节点中心进入连续压头实体；若继续碰撞，它们会成为“实体内部流体”，链接所有权也不再代表真实壁面。为避免伪造 10 nm 成功，程序在最后合法的 step 3594 停止。

因此 STEP 5.3 没有授权进入所谓“完整单周期压印过程”。本轮没有发生 fluid→solid 转换，也没有修改 OpenLB、tau、dt、壁速、几何尺寸、压力边界或 STEP 4 冻结文件。

## 实现依据与范围

独立程序 `explicit_piston_moving_boundary_compression.cpp` 从通过的 `explicit_piston_zouhe_moving_control_volume_longrun.cpp` 机械复制，并保留：

- 显式 60/120/60 nm 压头及 100 nm 槽深；
- `dx=5 nm`、`dt=1e-11 s`；
- 原 10000 步五次平滑 10 nm 轨迹及原壁速；
- x 周期、y 两端等参考压力 Zou/He；
- moving Bouzidi 和 192 条跨周期固壁 link 修复；
- moving-control-volume `alpha*rho` 质量定义；
- Mach `<=0.05`、rho `[0.8,1.2]`、`|R_geom|<1e-3` 门槛。

新增内容仅为逐步拓扑预检和初末压力分布输出。程序每步计算“固定 fluid material 中已有多少节点中心进入当前连续压头”。step 0–3594 均为 0；预测 step 3595 为 2304，与 STEP 5 已验证的第一次转换数量一致。

## 运行信息

- run-id：`step5_3_no_conversion_prethreshold_3594_v1_20260908`
- 命令：`mpirun -np 1 ./explicit_piston_moving_boundary_compression C`
- OpenLB：`5953d8a-dirty`
- STEP 4 冻结源 SHA-256：`9444c61aab6cc67499211f2724d109923d91d9bc0fe66747446acf2da5e399e2`
- 新程序 SHA-256：`224c33cc13052dfe22c164fe62954bf4b4adec0082d431ff43645e530adb2e0f`
- 完成步数：3594
- 物理时间：`3.594e-8 s`
- 退出码：3；含义是完整 10 nm 条件未达到，不是数值崩溃

## 压头位移历史

压头沿原五次平滑轨迹连续移动，没有改变加载速度：

| 项目 | 结果 |
|---|---:|
|初始 h|`75 nm`|
|最终合法 h|`72.5005751173 nm`|
|实际位移|`2.4994248828 nm`|
|请求位移|`10 nm`|
|最终壁速|`-0.159000399 m/s`|
|格子壁速|`-3.18000798e-4`|
|下一步 h|`72.4989847248 nm`|
|下一步进入实体的 fluid 节点|2304|

完整逐步位移、壁速和物理时间见 `moving_control_volume_longrun_history.csv`。

## 稳定性和质量收支

| 指标 | 结果 | 门槛 | 转换前判定 |
|---|---:|---:|---|
|最大 Mach|`9.4638870e-4`|`<=0.05`|PASS|
|最大速度|`0.273198886 m/s`|由 Mach 门槛控制|PASS|
|rho 全过程范围|`[0.989110468,1.109679905]`|`[0.8,1.2]`|PASS|
|最大 `|R_geom,macro|`|`9.2853266e-4`|`<1e-3`|PASS|
|最终 `R_geom,population`|`-9.3254916e-4`|辅助一致性|PASS 量级|
|NaN/Inf|0|0|PASS|
|非法 link|0|0|PASS|
|material conversion/change|0/0|0/0|PASS|

最大 Mach、最大速度、rho 极值和最大质量残差均发生在最后合法 step 3594。累计 macro 流入/流出分别为 `2.58368e-22 / 8.94015e-20 kg`；最终几何质量为 `7.10417147e-18 kg`。full-cell 质量残差为 `1.9576e-2`，仍不适用于移动控制体积，正式判据继续使用 STEP 4 已验证的 `R_geom`。

## 压力分布

压力按本机 OpenLB 实现计算：

`p_lattice = c_s^2 (rho-1)`，再由当前 UnitConverter 转成 Pa。这里是相对于 converter 参考压力的数值压力响应，不等同于实验压印压力标定。

最终 step 3594：

- 全部流体节点压力范围：`[-9.07461e5, 9.13999e6] Pa`；
- 平均值：`5.99588e5 Pa`；
- 最小值位置：lattice `(24,23,10)`，物理坐标 `(122.5,117.5,47.5) nm`，material 1；
- 最大值位置：lattice `(35,1,35)`，物理坐标 `(177.5,7.5,172.5) nm`，material 1；
- 两个 Zou/He 压力面 material 4/5 均保持参考压力 `0 Pa`；
- material 1 平均压力：`6.25657e5 Pa`。

初始和最终 57600 个流体节点的坐标、material、rho、格子压力和物理压力分别保存在 `pressure_distribution_initial.csv` 与 `pressure_distribution_final.csv`。

## 为什么不能继续到 10 nm

固定 material 图由初始 `h=75 nm` 生成。当前 Bouzidi 更新函数只在固定 fluid owner 上寻找相邻 material 2/3，并更新这些链接的 q 和壁速。当压头面越过流体节点中心后，正确离散域需要改变 owner、dynamics 和边界链接。只移动连续 indicator/q 而让该节点继续作为 BGK fluid，会同时产生：

- 压头实体内部仍执行 collision/streaming 的流体节点；
- 错误的流体占据体积；
- 不再对应真实界面的 Bouzidi owner/link；
- 没有物理意义的 `R_geom` 与压力场。

所以这不是当前 3594 步中的数值不稳定，而是“二值 lattice 材料拓扑冻结”对可表示位移的确定限制。完整 10 nm 必须采用经过验证的拓扑/状态转换方法，或另一种能跨 cell 更新真实计算域的边界方案；不能把冻结材料运行强行延长到 10000 步。

## 输出文件

- `output/step5_3_no_conversion_prethreshold_3594_v1_20260908/moving_control_volume_longrun_history.csv`
- `output/step5_3_no_conversion_prethreshold_3594_v1_20260908/topology_audit.csv`
- `output/step5_3_no_conversion_prethreshold_3594_v1_20260908/pressure_distribution_initial.csv`
- `output/step5_3_no_conversion_prethreshold_3594_v1_20260908/pressure_distribution_final.csv`
- `output/step5_3_no_conversion_prethreshold_3594_v1_20260908/result.txt`
- `output/step5_3_no_conversion_prethreshold_3594_v1_20260908/run_manifest.txt`
- `step5_3_moving_boundary_console.log`
- `step5_3_moving_boundary_exit_code.txt`

## 最终结论

无转换移动边界在第一次 lattice 拓扑变化前满足全部数值门槛，实际验证位移为 `2.499425 nm`；完整 10 nm 无转换目标未完成且按当前真实 Bouzidi/material 实现不可成立。停止在 STEP 5.3，不进入 STEP 6、两相、润湿或扩域。

Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is **SIM-EC1XT240**.
