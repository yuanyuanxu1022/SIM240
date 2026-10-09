# G2 最终状态报告

## 1. 状态结论

G2 验证阶段的分析与归档已完成，结果可作为后续 G3-h 高度扫描的输入基线。需要保留严格证据边界：

```text
三驱动力线性验证：PASS（Parallel/Perpendicular，3 个驱动力）
三网格 Richardson/GCI：数学验证 PASS
Step3 steady 数值矩阵：8/9 PASS
dx=1.25 nm EX240_perpendicular：质量门禁 FAIL
G2：具备参数研究输入资格，但不能表述为 9/9 门禁全部通过
```

## 2. 驱动力线性验证

数据源：
`CASE/05_mechanism_analysis/G2_EX240_force_linearity/results/g2_force_linearity_20260917T120627+0800/g2_force_linearity.csv`

- 方向：Parallel、Perpendicular；
- 驱动力：`5e4、1e5、2e5 m/s²`；
- 共 6 个稳态点，全部收敛、有限值、正常退出并通过运行门禁；
- 两个方向的 `R²=0.9999999999999998`；
- K 最大相对跨度：Parallel `2.48e-08`，Perpendicular `3.66e-08`，远低于 1% 协议门槛。

因此 G2 的线性响应和 Parallel/Perpendicular 覆盖完整。

## 3. 三网格 Richardson/GCI

三网格为 `dx=5.0、2.5、1.25 nm`，方向覆盖 Parallel 与 Perpendicular。K 序列及方向比均随网格加密单调变化。

| 指标 | apparent order p | 细网格 GCI |
|---|---:|---:|
| K_parallel | 1.5130 | 0.1250% |
| K_perpendicular | 1.2562 | 0.5510% |
| anisotropy | 1.0982 | 0.4648% |

Richardson 阶数为有限正值，渐近比满足协议，主要输运量细网格 GCI 均小于 2%。因此离散收敛证据完整；但 GCI 不替代质量、边界和正常退出门禁。

## 4. 生产网格选择

后续 SIM240 参数研究采用 **`dx=2.5 nm`**：

- 相对 `dx=1.25 nm`，K_parallel 变化约 `0.185%`；
- K_perpendicular 变化约 `0.609%`；
- anisotropy 变化约 `0.426%`；
- 细网格 GCI 分别为 `0.125%`、`0.551%` 和 `0.465%`；
- 目标网格的节点数为 `460,800`，而 1.25 nm 为 `3,686,400`，并且更细网格需要更小时间步和更多稳态步数，节点-步成本约高一个数量级以上。

因此 2.5 nm 在精度、方向性保持、参数扫描成本和可重复性之间更平衡。`dx=1.25 nm` 仅保留为参考细网格，不作为生产网格。

## 5. 1.25 nm 横槽质量门禁异常

目标点：`dx=1.25 nm / EX240_perpendicular / steady`。

- `max_mass_abs_relative=1.1967043900362632e-10`，超过冻结门限 `1.0e-10`；
- 最大值出现在 step 625，`exit_code=3`；
- 质量误差随后回落，末 1000 步约 `9.4e-11`，未见持续增长；
- Mach、material/geometry、Bouzidi link、收敛和有限值检查正常；
- double/Kahan/long double 离线累加差异仅 `10^-14` 相对量级，不能解释该峰值。

现有证据不支持将异常归因于纯统计舍入或整体密度持续增长；最可疑的是短时 streaming/boundary 质量交换或其他运行时测量路径，但缺少 collideAndStream 前后双账本，尚未最终定性。该异常单独保留为参考细网格诊断，不改变 G2 其他结果，也不放宽门禁。

详细记录：

- [G2 完整验证审计](G2_COMPLETE_VALIDATION_AUDIT.md)
- [质量精度验证](G2_mass_precision_validation.md)
- [运行时质量三账本复核](G2_dx1p25_perpendicular_runtime_mass_ledger.md)

## 6. G2 输入参数冻结状态

以下参数冻结为后续 G3-h 的基线输入，除非另有经过审计的参数化要求：

| 项目 | 冻结值 |
|---|---|
| 结构 | EX240 单周期直沟槽 RVE |
| 周期/台阶/沟槽 | `240/60/120 nm` |
| 沟槽深度 | `100 nm` |
| 基线液膜高度 | `h=75 nm` |
| 生产网格 | `dx=2.5 nm` |
| LBM | D3Q19 FORCE，ForcedBGK，`tau=1.0` |
| 壁面边界 | Bouzidi，`q=0.5`，无 fallback/unresolved link |
| 周期边界 | x/y periodic |
| 流体参数 | `rho=1000 kg/m³`，`nu=1.0e-6 m²/s` |
| 正式基准驱动力 | `1.0e5 m/s²` |
| 方向 | Parallel 与 Perpendicular |
| 质量门限 | `max_mass_abs_relative < 1.0e-10`（保持不变） |

几何、物理参数和门禁均未因 1.25 nm 异常而修改。

## 7. 进入 G3-h 的前置条件

G3-h 可在上述冻结基线下进入代码框架/小测试和高度参数化审计阶段。正式高度扫描必须继续继承 G2 的 LBM、边界、质量、Mach、收敛、有限值和正常退出规范；本报告不启动任何 G3 计算。
