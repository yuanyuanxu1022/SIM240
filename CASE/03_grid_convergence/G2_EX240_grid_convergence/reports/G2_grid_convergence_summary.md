# Objective

本报告总结 OpenLB 对显式 EX240 周期纳米沟槽真实几何的三网格验证。目标是比较 `dx=5 nm`、`2.5 nm` 和 `1.25 nm` 下的有效输运系数，检查 `K_parallel` 与 `K_perpendicular` 的网格收敛，并使用 Richardson extrapolation 与 Grid Convergence Index (GCI) 评估离散化误差，为后续 SIM240 F1/F2 计算选择计算网格。

数据来源为：

- `results/g2_grid_20260917T165045+0800/g2_grid_summary.csv`
- `results/g2_grid_20260917T165045+0800/g2_richardson_gci.csv`

# Grid configurations

| 网格 | dx (nm) | EX240 parallel / perpendicular | 说明 |
|---|---:|---|---|
| coarse | 5.0 | 有 | 粗网格 |
| medium | 2.5 | 有 | 候选生产网格 |
| fine | 1.25 | 有 | 参考细网格 |

三组结果均采用同一 EX240 几何、同一方向定义和同一有效输运量定义；本报告只比较网格分辨率，不改变物理参数或边界条件。`g2_grid_summary.csv` 中的 `dx=1.25 nm`、EX240 perpendicular 记录具有 `mass_error=1.1967043900362632e-10`、`exit_code=3` 和 `run_gate_PASS=false`，因此该单点不能作为完整数值门禁通过的结果表述。它仍被保留为已有 Richardson/GCI 序列中的细网格数值，但相关结论必须与该门禁异常一并解释。

# Hydraulic coefficient convergence

## K_parallel

| dx (nm) | K_parallel |
|---:|---:|
| 5.0 | 9.834075958643652e-23 |
| 2.5 | 9.782423697043172e-23 |
| 1.25 | 9.764325526249012e-23 |

`K_parallel` 随网格加密单调降低。由 `dx=2.5 nm` 到 `1.25 nm` 的变化约为 `0.185%`，由 `dx=5 nm` 到 `1.25 nm` 的总跨度约为 `0.714%`。因此沿槽方向的有效输运系数对网格进一步加密的敏感性较小。

## K_perpendicular

| dx (nm) | K_perpendicular |
|---:|---:|
| 5.0 | 4.4490220210459354e-23 |
| 2.5 | 4.3852935121144107e-23 |
| 1.25 | 4.358613368821741e-23 |

`K_perpendicular` 同样随网格加密单调降低，但变化幅度大于 `K_parallel`。由 `dx=2.5 nm` 到 `1.25 nm` 的变化约为 `0.612%`，三网格总跨度约为 `2.074%`。这表明横槽方向对几何边界离散和局部速度重排更敏感。

## Directional ratio

| dx (nm) | anisotropy = K_parallel/K_perpendicular |
|---:|---:|
| 5.0 | 2.210390488544205 |
| 2.5 | 2.2307340819991053 |
| 1.25 | 2.2402366762089274 |

方向比随网格加密略有增加，但三网格范围内保持同一数量级。该比值的细网格趋势应结合横槽方向单点的质量门禁异常使用，不能仅凭比值变化宣称完全网格独立。

# Richardson and GCI analysis

Richardson/GCI 汇总如下。`GCI_fine_percent` 对应细网格相对于 Richardson 外推值的指标，`GCI_medium_percent` 对应中等网格指标；数值直接来自 `g2_richardson_gci.csv`。

| metric | apparent order p | Richardson extrapolated | GCI fine (%) | GCI medium (%) | asymptotic ratio | asymptotic PASS |
|---|---:|---:|---:|---:|---:|---|
| K_parallel | 1.5129876294506368 | 9.754563861479575e-23 | 0.12496593778028703 | 0.3559935199394659 | 0.9981499297766432 | true |
| K_perpendicular | 1.2561724912115397 | 4.339399834463539e-23 | 0.5510219860185761 | 1.308170066726721 | 0.9939159959945745 | true |
| anisotropy | 1.0981812083843374 | 2.2485661018158467 | 0.4647625904539864 | 0.9992237510869528 | 1.0042598507309783 | true |

三项指标的 `mathematical_valid` 均为 `true`，`asymptotic_PASS` 均为 `true`，且诊断均为 `asymptotic range confirmed`。这说明三网格序列呈现可用于 Richardson 估计的单调渐近趋势。需要保留两个限制：

1. `K_perpendicular` 的中等网格 `GCI_medium=1.308170066726721%` 高于 1%，因此不能把 `dx=2.5 nm` 描述为对所有指标均达到 1% 严格误差门槛。
2. 细网格 EX240 perpendicular 的原始 `run_gate_PASS=false`，原因是质量误差略超既定门槛；GCI 的数学有效性不等价于该运行的完整 `RESULT_PASS`。

# Grid selection for SIM240

后续 F1/F2 采用 `dx=2.5 nm` 作为生产计算网格，理由是：

- 相对于 `dx=5 nm`，中等网格已经进入三网格 Richardson/GCI 所显示的渐近趋势；
- `K_parallel` 从中等网格到细网格的变化仅约 `0.185%`；
- `K_perpendicular` 从中等网格到细网格的变化约 `0.612%`，虽比 parallel 更敏感，但仍显著小于从粗网格到细网格的总变化；
- 各向异性比在三网格中保持稳定，`dx=2.5 nm` 与 `dx=1.25 nm` 的差异约为 `0.424%`；
- `dx=1.25 nm` 的三维流体节点数为 `3,686,400`，而 `dx=2.5 nm` 为 `460,800`，细网格在存储和计算成本上显著增加；
- 因此 `dx=2.5 nm` 是当前精度证据与计算成本之间的折中生产网格，`dx=1.25 nm` 保留为参考细网格。

该选择不是对细网格门禁异常的忽略，也不是宣称所有后续几何参数都已完成网格独立性验证。对于 F1/F2 的关键端点或最终论文定量结论，仍建议保留代表性 `dx=1.25 nm` 复核，并先解决 EX240 perpendicular 的质量门禁问题。

# Key conclusions

- 三个网格均显示 `K_parallel` 和 `K_perpendicular` 随网格加密单调收敛；横槽方向对网格分辨率更敏感。
- Richardson extrapolation 给出了有效的渐近趋势，`K_parallel`、`K_perpendicular` 和 anisotropy 的 `asymptotic_PASS` 均为 `true`。
- `K_parallel` 的细网格 GCI 为 `0.12496593778028703%`，`K_perpendicular` 的细网格 GCI 为 `0.5510219860185761%`。
- `dx=2.5 nm` 被选为后续 F1/F2 的生产网格，`dx=1.25 nm` 作为参考细网格，而不是默认生产网格。
- 该结论受 EX240 perpendicular 细网格质量门禁异常限制；GCI 通过不能替代完整运行门禁和后续代表性复核。
