# dx=1.25 nm EX240 Perpendicular 运行时质量三账本复核

## 1. 范围与证据边界

目标运行目录：
`CASE/03_grid_convergence/G2_EX240_grid_convergence/results/g2_grid_20260917T165045+0800/runs/dx1p25/EX240_perpendicular/steady/`

本次仅审计已有 `diagnostics.csv`、`result.txt`、`run.log` 与生成源代码；不修改 LBM 参数、几何、门限或 PASS 逻辑，不重跑 G2 矩阵。

关键原始结果：`max_mass_abs_relative=1.1967043900362632e-10`，最大值在 step 625，`exit_code=3`。

需要明确：归档没有保存每步完整三维 material map、rho 场或 collideAndStream 前后的双时刻质量。因此，以下对 material 账本和 population 前后差分的结论分为“已证实”和“无法由现有输出判定”。

## 2. A：material 账本

源码 `build/generated/g2_ex240_dx1p25.cpp` 的 `measure()` 遍历固定 `block.forCoreSpatialLocations`，仅筛选 `material==1`；几何未使用动态更新或移动边界。`result.txt` 给出：

- `fluid_nodes=3,686,400`；
- `fluid_volume_m3=7.1999999999129086e-21`；
- `material_unchanged=true`；
- Bouzidi candidate/installed links 均为 521,472，fallback/unresolved 均为 0。

因此，在现有静态几何实现中，step=0 到 step=625 的 material-1 数量和流体体积理论上保持不变；但 `diagnostics.csv` 没有逐步输出 `fluidNodes` 或 `volume`，无法对每个 step 做独立数值核对。现有证据支持“没有几何变化”，不等于已经保存了逐步 material 账本。

## 3. B：density 账本

`diagnostics.csv` 在 step 625 附近给出：

| step | `rho`（全流体平均） | `max_density_deviation` | mass error |
|---:|---:|---:|---:|
| 624 | 0.99999999999575695 | 6.4746119577e-10 | 1.1958912196e-10 |
| 625 | 0.99999999999330569 | 6.4508687281e-10 | 1.1967043900e-10 |
| 626 | 0.99999999999168143 | 6.4274630063e-10 | 1.1882324382e-10 |
| 627 | 0.99999999999116740 | 6.4044103354e-10 | 1.1779479723e-10 |

step 624→625 的总质量仅增加约 `5.85e-31 kg`，随后立即下降；step 625→626 又下降约 `6.10e-30 kg`。平均 rho 在该区间没有持续上升，反而略低于 1。由此可排除“持续的整体密度增长”作为超限主因。step 0 的初始质量为 `7.1999999993792838e-18 kg`，目标理论质量为约 `7.2e-18 kg`，初始偏差本身已处于 `10^-10` 相对量级，需要与运行时波动分开解释。

## 4. C：population/streaming 账本

源码主循环为：

```text
if (step > 0) lattice.collideAndStream();
state = measure(...);
massError = (state.mass - initial.mass) / initial.mass;
```

因此 step 625 的记录是一次 `collideAndStream()` 完成后、`measure()` 读取到的质量；现有 CSV 没有保存同一步 collide 前质量，不能直接计算 collideAndStream 前后质量差，也不能给出 boundary link 的净质量交换量。

可确认的时间行为是：质量误差在 step 120 首次超过 `1.0e-10`，step 625 达到峰值，随后回落；这表现为短时质量跳变/波动，而非单调发散。boundary audit 显示 Bouzidi link 完整且无 fallback/unresolved，但该静态审计不能证明每个时间步的 streaming 质量通量严格闭合。

## 5. 分类判断

| 候选来源 | 判断 | 依据 |
|---|---|---|
| 1. 纯统计舍入误差 | **不支持为主因** | 已有 double/Kahan/long double 对比仅为 `10^-14` 相对差异，远小于峰值量级 |
| 2. 瞬态物理变化 | **不支持“整体密度物理增长”** | step 625 后质量回落，平均 rho 未持续升高；但局部瞬态仍无法由平均量完全排除 |
| 3. streaming/boundary 质量交换 | **最可疑但尚未证实** | 超限为短时峰值，发生在 collideAndStream 后；缺少前后双账本和净 link 通量 |
| 4. 其他实现路径 | **仍未排除** | 初始 M0 与运行时 M 使用同一 `measure()` 但无逐步 material/volume 输出；块归约顺序、测量时序等需运行时证据 |

严格结论：现有归档不能把超限归因于单纯浮点统计；也没有证据表明几何 material 数量变化。最合理的工作假设是“短时 streaming/boundary 或测量路径引起的质量账本波动”，但要形成闭环仍需运行时双时刻质量与 material 账本。

## 6. 下一步建议

在不改变任何冻结规范的前提下，仅对该目标点增加诊断字段：

1. `collideAndStream()` 前后各测一次 material-1 数量、volume、mass、densityIntegral；
2. 记录 step 620–630 的逐块/逐 link 质量差分，特别是 Bouzidi 边界 link 净交换；
3. 保留当前 double 账本，同时旁路记录 Kahan/long double 账本；
4. 重新判断 step 625 峰值属于统计误差、streaming/boundary 交换还是其他实现路径；不改变原门限和 PASS 逻辑。

在上述运行时证据获得前，该点仍应保持 `FAIL`，不得通过放宽阈值或改写 PASS 逻辑处理。
