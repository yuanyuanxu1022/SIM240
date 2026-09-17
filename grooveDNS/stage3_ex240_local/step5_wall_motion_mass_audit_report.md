# SIM-EC1XT240 STEP 5-C 移动固壁质量交换项审计

## 判定

**FAIL：加入移动固壁扫掠质量项后仍不闭合。** 本轮仅离线读取已完成的 v3/mass-audit 数据，未重新运行或修改仿真。

- 原 `max |R_pop| = 1.20808380745e-3`；
- 加入本次唯一 topology event 的物理扫掠项后，
  `max |R_corrected| = 1.19503461408e-3`；
- 冻结门槛为 `1e-3`，因此仍为 FAIL；
- 不允许进入最终 0→10 nm 验证。

结果说明，第一次转换时间步确实遗漏了一个可计算的移动壁面扫掠项，但其大小只能解释该步
population-consistent 残差增量的约 `7.08%`。其余缺口仍来自动态 topology 后的 population/边界离散交换，不能通过本墙项审计消除。

## 数据与计算口径

输入均为冻结结果：

- population-consistent 时序：
  `step5_5_dynamic_material/output/mass_audit_consistency_0to3nm_v1_20260909/first_conversion_history.csv`；
- 2304 个事件节点及转换前 stored `f0...f18`：
  `step5_5_dynamic_material/output/first_material_conversion_0to3nm_v3_20260909/topology_events.csv`。

使用本机 OpenLB `5953d8a-dirty` 已核实的 shifted-population 定义：

```text
rho_pop = 1 + sum(q=0..18) f_q
deltaV_i = [alpha_i(h_after)-alpha_i(h_before)] dx^3
deltaM_wall,i = rho_pop,i rho_phys deltaV_i
```

`deltaM_wall` 采用有符号流体控制体积变化：压头占据体积时为负，释放体积时为正。现有时序中的
`cumulative_outward_mass` 以向外为正，故保持 STEP 4/STEP 5 的实际符号后：

```text
R_pop = [M_pop(t)-M_pop(0)+M_out(t)] / M_pop(0)
R_corrected = [M_pop(t)-M_pop(0)+M_out(t)-M_wall_motion(t)] / M_pop(0)
```

等价地，可将 `-deltaM_wall` 记为正的“壁面占据质量”。报告没有把符号相反的两个定义混用。

这里的 `alpha_before/after` 均来自同一个连续几何 cut-cell 定义，只相差 step 3594→3595 的真实壁面位移；
没有把 material 改为 solid 后机械地令整个格点 `alpha=0`。后者会把约半个格点体积错误当成本时间步的壁面扫掠，并重复计算此前已经位于压头内的部分。

## A. 第一次 2304 节点转换的墙面账本

- conversion step：3595；
- `h_before = 72.50057511725 nm`；
- `h_after = 72.49898472482 nm`；
- 本步压头位移：`0.001590392427 nm`；
- 转换节点：2304，其中 `z=72.5 nm` 与 `z=172.5 nm` 各 1152 个；
- 每个节点 `alpha_before = 0.50011502345`；
- 每个节点 `alpha_after = 0.499796944965`；
- `rho_pop` 范围：`[0.9944058144, 1.1096799051]`。

汇总结果：

|量|有符号结果|占据量（正值）|
|---|---:|---:|
|`deltaV_wall`|`-9.16066037937e-26 m³`|`9.16066037937e-26 m³`|
|`deltaM_wall`|`-9.39541922710e-23 kg`|`9.39541922710e-23 kg`|
|相对初始质量|`-1.30491933710e-5`|`1.30491933710e-5`|

几何交叉核对：

```text
Lx Ly [h_after-h_before]
= 240 nm × 240 nm × (-0.001590392427 nm)
= -9.16066037937e-26 m³
```

与2304节点的 `sum(delta alpha dx^3)` 一致。虽然节点分布在凸台底面和槽顶两个 z 层，但二者在 x 方向各自覆盖互补区域，合计只形成一个完整 `240×240 nm²` 计划面积，没有重复计算两个完整平面。

## B. step 3594→3595

|step|`R_pop`|累计 `M_wall_motion/M0`|`R_corrected`|
|---:|---:|---:|---:|
|3594|`-8.41169493221e-4`|0|`-8.41169493221e-4`|
|3595|`-1.02558045109e-3`|`-1.30491933710e-5`|`-1.01253125772e-3`|
|3596|`-1.02671379191e-3`|`-1.30491933710e-5`|`-1.01366459854e-3`|

原事件步残差增量为：

```text
delta R_pop = -1.84410957873e-4
```

扣除墙面扫掠项后仍为：

```text
delta R_corrected = -1.71361764502e-4
未闭合质量 = -1.23380470441e-21 kg
```

因此墙项只解释了该事件步缺口的 `7.076%`。`R_corrected` 在 step 3595 已为
`-1.01253125772e-3`，仍略超冻结门槛。

## C. 0→3 nm 全过程

本区间只有 step 3595 一次 topology event，所以此后累计离散事件墙项保持
`-9.39541922710e-23 kg`。末态为：

|量|step 3898|
|---|---:|
|位移|`2.9996885378 nm`|
|`R_pop`|`-1.20808380745e-3`|
|`R_corrected`|`-1.19503461408e-3`|
|corrected 未闭合质量|`-8.60424922135e-21 kg`|

全过程最大绝对修正残差出现在 step 3898：

```text
max |R_corrected| = 1.19503461408e-3 > 1e-3
```

墙面扫掠项仅将末态绝对残差降低约 `1.080%`。它不能解释转换后持续累积的全部缺口。

## 物理解释与范围

`M_pop` 本身已经使用随 `h` 连续变化的 `alpha` 对移动流体域积分。因此单独加入墙项时必须避免把同一连续体积变化重复记账。
本报告严格按任务指定，仅在 topology event 上计算该步的物理扫掠薄层，并公开符号。审计证明：

1. material/dynamics 提交瞬间没有删除 stored populations；
2. 连续壁面在转换步占据的薄层质量是一个真实但很小的账本项；
3. 加入该项后仍有 `1.23380e-21 kg` 的事件步缺口，并在末态达到 `8.60425e-21 kg`；
4. 因而剩余问题仍属于转换后 population、moving Bouzidi、NoDynamics/cut-cell 与开放边界之间的离散交换闭合，不能判定为单纯审计漏掉墙面扫掠量。

本轮未实现任何质量补偿、population 重构、归一化或参数调整。

## 输出与停止点

- 可复现离线脚本：`step5_5_dynamic_material/postprocess_wall_motion_mass_audit.py`；
- 2304节点逐项账本：同一 mass-audit run 目录中的
  `wall_motion_conversion_event_cells.csv`；
- 全时序修正残差：`wall_motion_corrected_history.csv`；
- 数值摘要：`wall_motion_mass_audit_summary.txt`。

**STEP 5-C FAIL。停止在移动固壁/动态拓扑质量闭合审计，不进入 0→10 nm。**

Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is **SIM-EC1XT240**.
