# G2 质量统计精度验证

## 1. 范围与冻结条件

目标点为 `dx=1.25 nm / EX240_perpendicular / steady`。本次只比较质量统计的浮点累加方式，不改变 LBM 物理参数、EX240 几何、质量门限 `1.0e-10` 或既有 PASS/FAIL 逻辑；未启动 G3，也未运行新的长时间模拟。

当前结果来自：

`CASE/03_grid_convergence/G2_EX240_grid_convergence/results/g2_grid_20260917T165045+0800/runs/dx1p25/EX240_perpendicular/steady/`

原始 steady 结果为 `max_mass_abs_relative=1.1967043900362632e-10`、最大值出现在 step 625、`exit_code=3`。

## 2. 实现基线

生成源文件：
`CASE/03_grid_convergence/G2_EX240_grid_convergence/build/generated/g2_ex240_dx1p25.cpp`

- `Measurement initial = measure(...)` 在约第 681 行初始化 `M0`；
- `measure()` 对 material=1 的 core lattice locations 累加
  `mass += rho * rhoPhys * dx^3`（约第 434 行）；
- `T` 为普通 `double`；使用顺序 `+=`，无补偿项；
- 每步质量误差为 `(M-M0)/M0`（约第 707 行），并以最大绝对值参与现有门禁。

## 3. 三种累加方式对比

由于现有输出只保存最终 `field_slice.csv`（19,200 个 rho 样本），没有 step 625 的完整三维密度场，因此只能对该可复核切片做离线精度对比，不能把切片结果等同于完整 steady 重跑。

测试输入：`field_slice.csv` 的 `rho` 列；算法保持相同遍历顺序。

| 方法 | rho 总和 | 相对平均密度偏差 |
|---|---:|---:|
| double sequential（当前算法） | 19200.0000000003274 | `1.706e-14` |
| Kahan（double 补偿求和） | 19200.0000000001783 | `9.287e-15` |
| long double sequential | 19200.0000000001799 | `9.370e-15` |

相对差异：当前顺序求和与 Kahan 的总和差 `1.49e-10`（对 19,200 个样本的相对量约 `7.8e-15`）；与 long double 的差 `1.48e-10`。换算为质量相对误差后仍为 `10^-14` 量级，远小于目标点报告的 `10^-10` 门限超差量级。

## 4. 诊断判断

1. 在现有可见切片上，Kahan 与 long double 仅消除极小的累加舍入差，未显示足以解释 step 625 的 `1.1967e-10` 峰值的证据。
2. 不能据此证明全三维场的普通 double 累加没有贡献：目标网格有 3,686,400 个 fluid nodes，而当前归档没有保存每个时间步的完整 rho 场；全场的累加顺序、MPI/块归约顺序及 material 筛选仍可能改变舍入上界。
3. 因而该测试**不能授权修改门禁或把失败点改报 PASS**。它支持的最严格结论是：在可复核数据上，统计精度差异远小于当前超差；step 625 峰值仍需完整场或运行时双账本证据定位。

## 5. 对 dx=2.5 nm production grid 的建议

当前不建议“正式冻结”为 production grid。理由是：

- `dx=2.5 nm` 的 Parallel/Perpendicular 点均通过现有质量门禁，且细网格 GCI 对 `K_parallel`、`K_perpendicular` 分别为约 `0.125%`、`0.551%`；
- 但 `dx=1.25 nm / EX240_perpendicular` 仍是 Step3 唯一 FAIL 点，尚未完成质量统计实现审计闭环；
- 在未解释该失败点之前，`dx=2.5 nm` 只能标记为**暂定候选 production grid**，不能作为已批准的 G2 生产网格。

建议下一步：在不改变冻结规范的前提下，对失败点增加运行时 sequential/Kahan/long-double 双账本（至少覆盖 step 625），重新取得可比证据；只有 9/9 steady 点满足原门禁后，再做 production grid 决策。
