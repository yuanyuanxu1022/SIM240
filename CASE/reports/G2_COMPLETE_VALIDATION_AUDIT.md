# G2 验证完整性审计报告

**审计范围**：`CASE/05_mechanism_analysis/G2_EX240_force_linearity` 与 `CASE/03_grid_convergence/G2_EX240_grid_convergence` 的现有结果。仅审计，不修改物理参数、网格、阈值或 PASS 逻辑，不启动计算。

## 1. 结论

G2 的两类证据状态不同：

1. **三驱动力线性验证：已完成并通过**。Parallel 与 Perpendicular 均覆盖 `a=5e4/1e5/2e5 m/s²`，共 6 个稳态点；所有点 `R²=0.9999999999999998`，K 的相对跨度远低于 1%，运行门禁均为 PASS。
2. **三网格收敛验证：数值收敛证据通过，但正式 Step3 门禁未完成**。`dx=5.0/2.5/1.25 nm` 均有 Parallel/Perpendicular 结果，K 序列单调，Richardson 阶数、渐近比和细网格 GCI 均通过；但 `dx=1.25 nm / EX240_perpendicular / steady` 的质量误差为 `1.1967043900362632e-10`，超过冻结门限 `1.0e-10`，`exit_code=3`。

因此当前应报告为：

```text
三驱动力线性验证：PASS（6/6）
三网格 Richardson/GCI 数学验证：PASS
Step3 数值门禁：FAIL（8/9 steady 点通过）
G2 完整验证：未完成，不能宣称正式 G2 全部通过
```

## 2. 三驱动力线性验证审计

数据源：
`CASE/05_mechanism_analysis/G2_EX240_force_linearity/results/g2_force_linearity_20260917T120627+0800/g2_force_linearity.csv`

Case 目录审计显示，独立驱动力目录为 `runs/G2-P-a5e4`、`runs/G2-P-a2e5`、`runs/G2-T-a5e4`、`runs/G2-T-a2e5`；`1e5 m/s²` 两个正式点在 CSV 中标记为 `formal_G2-P`/`formal_G2-T` 且 `reused=true`，对应已完成的 G2 正式基准结果，而非缺失驱动力点。

协议门槛：`R² >= 0.9999`、三驱动力 K 最大相对跨度 `<=1%`，并满足质量、Mach、收敛、有限值、正常退出及既有几何门禁。

| 方向 | 驱动力 (m/s²) | K (m²/(Pa·s)) | R² | K 最大相对跨度 | 运行门禁 |
|---|---:|---:|---:|---:|---|
| Parallel | 5e4, 1e5, 2e5 | `9.7824237955e-23`, `9.7824236970e-23`, `9.7824239395e-23` | 0.9999999999999998 | `2.4784979e-08` | 3/3 PASS |
| Perpendicular | 5e4, 1e5, 2e5 | `4.3852936726e-23`, `4.3852935121e-23`, `4.3852935529e-23` | 0.9999999999999998 | `3.6600327e-08` | 3/3 PASS |

Parallel 和 Perpendicular 均完整覆盖三种驱动力；质量误差、Mach、收敛、有限值和正常退出字段在 6 个结果中均满足协议。该部分可以作为 G2 的独立 PASS 证据。

## 3. 三网格结果与方向覆盖

数据源：
`CASE/03_grid_convergence/G2_EX240_grid_convergence/results/g2_grid_20260917T165045+0800/g2_grid_summary.csv`

| dx (nm) | K_parallel | K_perpendicular | 方向比 `K∥/K⊥` | Parallel 门禁 | Perpendicular 门禁 |
|---:|---:|---:|---:|---|---|
| 5.00 | `9.8340759586e-23` | `4.4490220210e-23` | 2.21039049 | PASS | PASS |
| 2.50 | `9.7824236970e-23` | `4.3852935121e-23` | 2.23073408 | PASS | PASS |
| 1.25 | `9.7643255262e-23` | `4.3586133688e-23` | 2.24023668 | PASS | **FAIL** |

覆盖情况为 3 个 dx × 2 个方向，共 6 个 EX240 网格点；另有 3 个 Smooth75 参考点。随网格加密，Parallel、Perpendicular 的 K 均单调变化，方向比也单调变化。EX240 方向比从粗到细的跨度为约 `1.3401%`；Parallel K 跨度约 `0.711%`，Perpendicular K 跨度约 `2.027%`。这些跨度描述离散趋势，不替代正式门禁。

## 4. Richardson 与 GCI 审计

数据源：
`CASE/03_grid_convergence/G2_EX240_grid_convergence/results/g2_grid_20260917T165045+0800/g2_richardson_gci.csv`

| 指标 | Richardson p | 细网格 GCI | 渐近比 | 数学状态 |
|---|---:|---:|---:|---|
| K_smooth | 1.9909 | 0.0352% | 0.99916 | PASS |
| K_parallel | 1.5130 | 0.1250% | 0.99815 | PASS |
| K_perpendicular | 1.2562 | 0.5510% | 0.99392 | PASS |
| eta_parallel | 0.9398 | 0.1381% | 0.99899 | PASS |
| eta_perpendicular | 1.0884 | 0.5857% | 0.99475 | PASS |
| anisotropy | 1.0982 | 0.4648% | 1.00426 | PASS |

所有 Richardson 计算均为有限、正阶数且满足协议渐近比区间；Parallel/Perpendicular 的细网格 GCI 均小于 2%。这证明三网格离散收敛性证据完整，但不能覆盖细网格横槽点的质量门禁失败。

## 5. 独立保留的质量误差诊断

目标点：`dx=1.25 nm / EX240_perpendicular / steady`。

该点 `converged=true`、Mach 和 Bouzidi link 审计正常，但 `max_mass_abs_relative=1.1967043900362632e-10`，因此 `PASS=false`、`exit_code=3`。最大值出现在 step 625；末 1000 步约为 `9.4e-11`，未见持续增长。

详细质量账本实现审计已单独保留：

- [G2 Step3 mass accumulation audit](G2_STEP3_mass_accumulation_audit.md)
- [dx=1.25 nm EX240 perpendicular mass ledger](G2_STEP3_dx1p25_EX240_perpendicular_mass_ledger.md)

本总报告不将该诊断折叠为“收敛通过”，也不以数学 GCI 结果替代质量门禁。当前 Step3 批次状态仍为 `STEADY_MATRIX=FAIL`、`POSTPROCESS_EXIT=3`。

## 6. 下一步建议（不改变冻结规范）

1. 继续对上述目标点做**只读实现/账本复核**，区分初始质量离散偏差、普通 double 累加误差及 step 625 的瞬态触发路径；保持当前物理参数、门限和 PASS 逻辑不变。
2. 在冻结源码与协议下，使该细网格横槽点重新获得质量门禁和正常退出证据后，再重跑 Step3 后处理矩阵。
3. 只有在 9 个 steady 点全部通过后，才决定生产网格。当前不应宣布生产网格或 G2 正式闭合；`dx=2.5 nm` 只能作为基于 GCI 的候选，不能作为已批准选择。

## 7. 证据边界

本审计基于现有 CSV、`result.txt`、退出码和冻结协议文件；未运行新模拟，未修改任何 Case 文件。G2 的线性与离散收敛证据已具备论文级可复核数据，但由于一个质量门禁失败，正式 G2 完整验证结论仍为 **FAIL/未完成**。
