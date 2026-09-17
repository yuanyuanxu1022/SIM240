# SIM-EC1XT240 STEP 5.4 Moving Piston Geometry Redesign

## 判定

**STEP 5.4 虚拟链接候选：FAIL。** 新表示在不改变 material 编号的情况下越过了第一次 2304 节点拓扑阈值，且 moving Bouzidi 链接始终合法、Mach 保持低值；但移动控制体积残差在第一次阈值 step 3595 即达到 `-1.11587e-3`，随后继续增长。计算在 step 5570、位移 `6.05953 nm` 时因 `rho_max=1.2000344` 超过冻结上限而停止，未完成 10 nm。

因此目前不能进入完整单周期压印。没有继续 fluid→solid conversion、STEP 6、两相、润湿或扩域。

## 几何更新方法

独立程序 `explicit_piston_virtual_link_moving_geometry.cpp` 从 STEP 4 PASS 源码复制，保留原显式几何、D3Q19、Zou/He、单位映射、物性、tau、dt、壁速和五次平滑 10 nm 轨迹。

候选采用“静态 material + 动态解析壁链接”方法：

1. material 1/4/5/2/3 编号始终保持初始 `h=75 nm` 的值；
2. 每步用当前 `h(t)` 和真实 60/120/60 nm、100 nm 槽深解析 indicator 判断物理流体中心和压头内部节点；
3. 只对物理流体 owner 遍历 D3Q19 链接；若邻居在当前解析压头或基底内部，通过二分求实际交点 q；
4. 在 owner 的 `BOUZIDI_DISTANCE/VELOCITY` 字段中更新链接，由现有 moving Bouzidi PostStream 闭合；
5. 被压头扫过但仍保存为 material 1/4/5 的节点称为 ghost-fluid storage。它们保留 lattice populations 供 Bouzidi 插值读取，但不计入物理 Mach、rho、压力边界通量或 active-cell 数；
6. moving-control-volume 质量继续按连续几何 `alpha*rho` 积分。

本机 OpenLB 的 `BouzidiVelocityPostProcessor` 确实只依据 owner 的 q 字段激活，并读取壁后邻居 population；它不检查壁后邻居 material。因此该方案在 API 层面可执行，但 ghost population 如何演化并不是一个已验证的守恒移动边界模型。这正是本轮测试内容。

## 程序与运行

- 程序：`explicit_piston_virtual_link_moving_geometry.cpp`
- run-id：`step5_4_virtual_link_full10nm_v1_20260908`
- 命令：`mpirun -np 1 ./explicit_piston_virtual_link_moving_geometry C`
- STEP 4 源 SHA-256：`9444c61aab6cc67499211f2724d109923d91d9bc0fe66747446acf2da5e399e2`
- 候选源 SHA-256：`47cc3defac6437c353eb17b17dbdb0a185eef5e7af27d569d9e9b7f97d6104cb`
- 请求：10000 步、10 nm
- 实际：5570 步、`6.05952645 nm`
- 最终 `h=68.94047355 nm`
- 退出码：3，原因 `rho > 1.2`

## Material 变化

- material conversion：0；
- material change：0；
- material field：逐步及最终保持不变；
- 初始物理 active fluid：57600 节点；
- step 3595 后物理 active fluid：55296 节点；
- ghost-fluid storage：0 -> 2304 节点。

这里“material 不变”不等于离散物理域不变。解析压头越过节点中心后，2304 个原 material-fluid 节点被重新分类为 ghost storage，而不是物理流体；这种分类只存在于应用层 indicator 和统计中，没有改变 OpenLB dynamics/material。

## Link 变化

| step | h (nm) | active Bouzidi links | virtual fluid-storage links | active cells | ghost cells | 非法 link |
|---:|---:|---:|---:|---:|---:|---:|
|1|75.000000|32448|272|57600|0|0|
|3594|72.500575|32448|272|57600|0|0|
|3595|72.498985|32448|11980|55296|2304|0|
|5000|70.000000|32448|11980|55296|2304|0|
|5570|68.940474|32448|11980|55296|2304|0|

active link 总数保持 32448，但 step 3595 时 owner 层发生整体切换：11708 条压头相关链接从传统 material-solid 邻居转为跨向仍有 fluid material 编号的 ghost storage；加上原有 272 条解析/离散边界差异链接，virtual link 总数成为 11980。q 均在合法范围，跨周期 false-solid link 为0。

因此几何链接在计数上连续、没有漏链，但链接背后的 population 来源从 NoDynamics 实体存储变成仍具有流体 dynamics/压力处理的 ghost 节点。这一变化与质量残差首次超限同步。

## Mach、速度与 rho

| 指标 | 结果 | 门槛 | 判定 |
|---|---:|---:|---|
|最大 Mach|`0.0178759125`|`<=0.05`|PASS|
|最大速度|`5.16033144 m/s`|由 Mach 门槛控制|PASS|
|最大速度 step|5086|—|—|
|最大速度 cell|`(33,0,34)`，material 4|—|低 y 压力面|
|rho 全过程范围|`[0.976957048,1.200034402]`|`[0.8,1.2]`|FAIL|
|首次 rho 超限|step 5570，`rho_max=1.200034402`|—|停止原因|
|NaN/Inf|0|0|PASS|

首次超限的 rho 最大 cell 位于 lattice `(35,1,34)`，物理坐标 `(177.5,7.5,167.5) nm`，material 1；对应压力约 `1.66695e7 Pa`。同一步最低 rho 为 `0.9769920`。

Mach 没有爆炸，说明动态链接切换避免了 STEP 5 直接 population 重分配造成的瞬时高速冲击。但 rho 在持续压缩过程中积累并最终越界，不能据此宣称 ghost 模型稳定。

## Moving control volume 质量

| 指标 | 结果 | 门槛 | 判定 |
|---|---:|---:|---|
|首次 `|R_geom,macro| >= 1e-3`|step 3595|`<1e-3`|FAIL|
|step 3594 `R_geom,macro`|`-9.28533e-4`|`<1e-3`|PASS|
|step 3595 `R_geom,macro`|`-1.11587e-3`|`<1e-3`|FAIL|
|最终 `R_geom,macro`|`-3.38438e-3`|`<1e-3`|FAIL|
|最终 `R_geom,population`|`-3.38872e-3`|辅助核对|同量级 FAIL|

最终 `M_geom=6.97666326e-18 kg`；累计 macro 流入/流出为 `1.86121e-20 / 2.17581e-19 kg`。macro 与 population 残差非常接近，说明失败不是单纯由出口通量求积口径造成。

残差第一次超限恰好发生在 ghost layer 建立和 11708 条链接切换的 step 3595。当前最可能的问题是：ghost 节点继续执行原流体/Zou-He dynamics，其 populations 被 Bouzidi 当作壁后插值数据读取，但 ghost 区没有与 moving control volume 一致的状态更新和质量交换定义。静态 material 虽避免了显式 mass redistribution，却没有消除拓扑变化需要的守恒闭合。

## 压力状态

停止时物理 active fluid 压力范围为 `[-1.91733e6,1.66695e7] Pa`。两个压力面仍使用原等参考压力 Zou/He；保存的 `pressure_initial.csv` 和 `pressure_final.csv` 只统计解析物理流体中心，不包含 ghost storage。该压力是 converter 定义下的数值压力，不应直接解释为实验压印载荷。

## 是否可以进入单周期压印

**不可以。** 本候选只完成 `6.06 nm`，rho 和 `R_geom` 均失败。虽然 material 编号不变、链接合法且 Mach 较低，但 ghost population 与移动控制体积之间缺少守恒、一致的演化规则。

若未来继续这一路线，所需的不只是再次调整 q：必须给 ghost/active 状态切换定义明确的 dynamics、population 时间层及质量交换闭合。这实质上仍是动态计算域拓扑问题，只是从 material 编号转换改成 active-mask/dynamics 转换；在完成独立验证前不能视为已绕过 STEP 5。

## 输出文件

- `output/step5_4_virtual_link_full10nm_v1_20260908/moving_control_volume_longrun_history.csv`
- `output/step5_4_virtual_link_full10nm_v1_20260908/dynamic_link_history.csv`
- `output/step5_4_virtual_link_full10nm_v1_20260908/pressure_initial.csv`
- `output/step5_4_virtual_link_full10nm_v1_20260908/pressure_final.csv`
- `output/step5_4_virtual_link_full10nm_v1_20260908/result.txt`
- `output/step5_4_virtual_link_full10nm_v1_20260908/run_manifest.txt`
- `step5_4_virtual_link_console.log`
- `step5_4_virtual_link_exit_code.txt`

## 最终结论

虚拟动态链接设计在不改变 material 编号时能越过第一次几何阈值，并保持合法链接和低 Mach；但它未能在 10 nm 全程维持 rho 和 moving-control-volume 质量守恒。STEP 5.4 判定 **FAIL**，不能进入单周期压印。

Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is **SIM-EC1XT240**.
