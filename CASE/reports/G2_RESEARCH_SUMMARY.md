# G2 EX240 网格收敛研究总结

## 1. 数据范围与状态

本总结基于当前仓库中的 G2 Step3 三网格结果：

`CASE/03_grid_convergence/G2_EX240_grid_convergence/results/g2_grid_20260917T165045+0800/`

状态文件 `docs/reports/SIM240_AI_CONTEXT.md` 的基准日期早于本批次结果；本报告以最新 CSV、`result.txt`、GCI 文件和既有审计报告为准。未修改任何 Case，未启动计算。

G2 的驱动力线性证据已通过；三网格 Richardson/GCI 数学证据已通过；但 Step3 9 个 steady 点中有 1 个质量门禁失败，因此不能将 G2 描述为 9/9 数值门禁完整通过。

## 2. 驱动力线性验证

数据源：
`CASE/05_mechanism_analysis/G2_EX240_force_linearity/results/g2_force_linearity_20260917T120627+0800/g2_force_linearity.csv`

Parallel 与 Perpendicular 均测试 `a=5e4、1e5、2e5 m/s²`，共 6 个稳态点：

- 两个方向 `R²=0.9999999999999998`；
- Parallel K 最大相对跨度 `2.48e-08`；
- Perpendicular K 最大相对跨度 `3.66e-08`；
- 质量、Mach、收敛、有限值、边界和正常退出字段均通过。

因此可以确认：在 G2 基准几何与数值协议下，`J`–驱动力关系线性，且两个主方向均被覆盖。

## 3. 三网格收敛与 GCI

三网格为 `dx=5.0、2.5、1.25 nm`。EX240 主结果如下：

| dx (nm) | K_parallel | K_perpendicular | `K_parallel/K_perpendicular` |
|---:|---:|---:|---:|
| 5.00 | `9.8340759586e-23` | `4.4490220210e-23` | 2.21039049 |
| 2.50 | `9.7824236970e-23` | `4.3852935121e-23` | 2.23073408 |
| 1.25 | `9.7643255262e-23` | `4.3586133688e-23` | 2.24023668 |

K_parallel、K_perpendicular 和方向比均随网格加密呈单调趋势。Richardson/GCI 结果：

| 指标 | apparent order p | 细网格 GCI |
|---|---:|---:|
| K_parallel | 1.5130 | 0.1250% |
| K_perpendicular | 1.2562 | 0.5510% |
| anisotropy | 1.0982 | 0.4648% |

三者均为有限正阶数，渐近比满足协议，细网格 GCI 小于 2%。这构成离散收敛和不确定度的主要证据。

## 4. K 的方向性

在基准高度 `h=75 nm` 下，Parallel 迁移率约为 `9.78e-23 m²/(Pa·s)`，Perpendicular 迁移率约为 `4.39e-23 m²/(Pa·s)`；Parallel/Perpendicular 方向比约为 `2.23`（2.5 nm 网格）。

因此 EX240 结构表现出明确的方向性输运：沿槽方向迁移率约为横槽方向的两倍以上。方向比从粗网格 2.2104 增至细网格 2.2402，粗到细跨度约 1.34%；2.5 nm 到 1.25 nm 的变化约 0.43%。

## 5. 2.5 nm 生产网格选择

后续参数研究采用 `dx=2.5 nm`，理由是：

- 相对 1.25 nm，K_parallel 变化约 0.185%；
- K_perpendicular 变化约 0.609%；
- anisotropy 变化约 0.426%；
- 对应细网格 GCI 分别为 0.125%、0.551% 和 0.465%；
- EX240 fluid nodes 为 460,800，而 1.25 nm 为 3,686,400；结合更小时间步和更长稳态过程，1.25 nm 的节点-步成本约为 2.5 nm 的 27 倍。

因此 2.5 nm 在精度、方向性保持和参数扫描成本之间提供合理折中。1.25 nm 作为参考细网格保留，不作为生产网格。

## 6. 1.25 nm 横槽质量门禁异常

唯一失败点为：

`dx=1.25 nm / EX240_perpendicular / steady`

- `max_mass_abs_relative=1.1967043900362632e-10 > 1.0e-10`；
- 最大值出现在 step 625；
- `exit_code=3`，所以该点 `run_gate_PASS=false`；
- Mach、material/geometry、Bouzidi link、收敛和有限值检查正常；
- 末 1000 步质量误差约 `9.4e-11`，没有持续增长。

已完成的 double/Kahan/long double 离线比较差异仅为 `10^-14` 相对量级，不能把该峰值解释为纯统计舍入。现有归档也没有 collideAndStream 前后双账本，因此 streaming/boundary 瞬态或其他测量路径仍是未闭合的限制。

详细记录：

- [G2 完整验证审计](G2_COMPLETE_VALIDATION_AUDIT.md)
- [质量精度验证](G2_mass_precision_validation.md)
- [运行时质量三账本复核](G2_dx1p25_perpendicular_runtime_mass_ledger.md)

## 7. 可用于论文的结论

在明确“G2 数值证据为 8/9 steady 门禁通过、细网格横槽点保留异常”的前提下，以下结论可以用于论文结果/方法部分：

1. 三驱动力下两个主方向的线性响应，R² 和 K 跨度数据；
2. `dx=5.0/2.5/1.25 nm` 的单调网格趋势、Richardson 阶数和 GCI；
3. `K_parallel > K_perpendicular` 及约 2.23 的基准方向比；
4. 采用 2.5 nm 生产网格的定量误差—成本依据；
5. 1.25 nm 作为参考细网格和质量异常的透明披露。

## 8. 仍属于限制的内容

- 不能写成 G2 全部 9/9 数值门禁通过或“所有细网格结果均 PASS”；
- 不能把 1.25 nm 横槽 K 当作无条件最终定量基准；
- G2 结果不能替代 G1 对 `K=h^3/12` 的解析精度闭合；当前项目状态仍记录 G1 精度门槛未通过；
- 不能把周期体力驱动直接解释为真实压印外部驱动；
- 不能由单一 `h=75 nm` 结果推导完整 `K_eff(h,\theta,...)` 参数面；
- 在未完成运行时质量双账本前，不能对 step 625 异常给出唯一根因。

## 9. 后续使用边界

后续 G3-h/参数研究可将 `dx=2.5 nm` 作为工作网格，并继承 G2 的 LBM、边界、质量、Mach、收敛和正常退出门禁。每个新高度仍需独立验证；G2 的收敛证据不能自动替代新高度的单点门禁。
