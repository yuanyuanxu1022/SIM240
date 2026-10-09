# G5A：垂向加载下的方向性挤压阻抗结果

> 运行日期：2026-09-21
>
> run ID：`run_20260921_190046`
> 原始结果：`CASE/05_mesoscale/G5A_squeeze_resistance/results/run_20260921_190046/`

## 1. 计算定义与证据状态

本节将已有 EX240 微尺度输运闭合用于单相、全充液、一维准静态 squeeze-flow 模型。压头以恒定速度

$$
V_p=75\ \mathrm{nm/s}
$$

沿壁法向 $z$ 方向下压；液体沿条带坐标 $s$ 的面内方向排出。`parallel` 对应沟槽延伸方向 $+y$，`perpendicular` 对应横跨沟槽方向 $+x$。因此，本节比较的是相同下压速度下所需的压力和垂向载荷，并不是独立的 $z$ 向贯穿流动。

采用：

- 宏观条带尺寸：$L=W=1.0\ \mathrm{mm}$；
- 动力黏度：$\mu=1.0\times10^{-3}\ \mathrm{Pa\,s}$；
- 两端定压出口：$p_{\mathrm{out}}=0\ \mathrm{Pa}$；
- 介尺度离散：$N=401$ 个控制体；
- 微尺度输入：`transport_database/G3_height_resistance.csv`，其源网格为 $\Delta x=2.5\ \mathrm{nm}$；
- 高度：$h=50,75,125\ \mathrm{nm}$。

主比较量定义为

$$
C_F=\frac{F_z}{V_p},
$$

其中 $F_z$ 为压头受到的表压积分载荷。

本次运行的 `INPUT_GATE`、`NUMERICAL_GATE`、`ANALYTIC_GATE`、`MASS_GATE`、`LINEARITY_GATE` 和 `RESULT_PASS` 均为 `true`，且应用退出码为 0。所有工况的质量相对误差均约为 $10^{-13}$；压力峰值解析误差约为 $10^{-13}$；载荷解析误差为 $3.11\times10^{-6}$，低于冻结门槛 $10^{-4}$。

## 2. 垂向载荷与挤压阻抗

| $h$ | 模型/排液方向 | $p_{\max}$ (Pa) | $F_z$ (N) | $C_F$ (N s/m) |
|---:|---|---:|---:|---:|
| 50 nm | Smooth | $9.000\times10^5$ | $6.000\times10^{-1}$ | $8.000\times10^6$ |
| 50 nm | EX240 parallel | $1.643\times10^5$ | $1.095\times10^{-1}$ | $1.460\times10^6$ |
| 50 nm | EX240 perpendicular | $6.538\times10^5$ | $4.359\times10^{-1}$ | $5.812\times10^6$ |
| 75 nm | Smooth | $2.667\times10^5$ | $1.778\times10^{-1}$ | $2.370\times10^6$ |
| 75 nm | EX240 parallel | $9.584\times10^4$ | $6.389\times10^{-2}$ | $8.519\times10^5$ |
| 75 nm | EX240 perpendicular | $2.138\times10^5$ | $1.425\times10^{-1}$ | $1.900\times10^6$ |
| 125 nm | Smooth | $5.760\times10^4$ | $3.840\times10^{-2}$ | $5.120\times10^5$ |
| 125 nm | EX240 parallel | $3.528\times10^4$ | $2.352\times10^{-2}$ | $3.136\times10^5$ |
| 125 nm | EX240 perpendicular | $5.073\times10^4$ | $3.382\times10^{-2}$ | $4.509\times10^5$ |

![不同高度下的挤压阻抗](../05_mesoscale/G5A_squeeze_resistance/results/run_20260921_190046/Figure_G5_squeeze_impedance_vs_h.png)

**Figure G5-1.** 不同液膜高度下 Smooth、EX240 parallel 和 EX240 perpendicular 的归一化挤压阻抗 $C_F$。在相同下压速度下，较低的 $K$ 对应较高的压力和垂向载荷。

## 3. 方向性响应

| $h$ | $C_{F,\parallel}$ (N s/m) | $C_{F,\perp}$ (N s/m) | $C_{F,\perp}/C_{F,\parallel}$ |
|---:|---:|---:|---:|
| 50 nm | $1.460\times10^6$ | $5.812\times10^6$ | 3.980 |
| 75 nm | $8.519\times10^5$ | $1.900\times10^6$ | 2.231 |
| 125 nm | $3.136\times10^5$ | $4.509\times10^5$ | 1.438 |

![方向挤压阻抗比](../05_mesoscale/G5A_squeeze_resistance/results/run_20260921_190046/Figure_G5_directional_ratio_vs_h.png)

**Figure G5-2.** EX240 横槽/沿槽挤压阻抗比随液膜高度的变化。

对于相同宏观几何和出口边界，G5A 结果满足

$$
\frac{C_{F,\perp}}{C_{F,\parallel}}
=\frac{K_{\parallel}}{K_{\perp}}
=\frac{R_{\perp}}{R_{\parallel}}.
$$

数值阻抗比与输入迁移率比的相对偏差均约为 $10^{-13}$。因此，G5A 保持了微尺度 G3 数据所给出的方向性闭合：横槽方向因面内排液能力较低，在相同 $V_p$ 下需要更大的压力和 $F_z$。

从 50 nm 增加到 125 nm：

- $C_{F,\parallel}$ 下降约 78.5%；
- $C_{F,\perp}$ 下降约 92.2%；
- 方向阻抗比由 3.980 降至 1.438，下降约 63.9%。

这表明，在当前固定网格输入和条带边界条件下，较大液膜间隙降低了整体挤压阻抗，并减弱了沟槽诱导的方向性载荷差异。

## 4. 结果解释与表述边界

恒速下压时，总排液体积流量由压头排开体积决定：

$$
Q_{\mathrm{out,total}}=WLV_p=7.5\times10^{-14}\ \mathrm{m^3/s}.
$$

因此，不应将本节结果表述为“parallel 的总排液量高于 perpendicular”。本节的物理含义是：为了维持相同下压速度，perpendicular 排液需要更高的压力和垂向载荷。

同一名义 mesa 间隙下，两个 EX240 方向的 $C_F$ 均低于 Smooth 对照。这与沟槽提供额外局部流动空间相一致；但该对照不是等液体体积对照，不能据此声称沟槽在所有几何或体积约束下都必然降低挤压阻力。

可用于论文的表述为：

> 在固定 $\Delta x=2.5\ \mathrm{nm}$ 微尺度输入、单相全充液和准静态双侧排液条带条件下，EX240 的横槽排液在全部考察高度下均需要高于沿槽排液的压力与垂向载荷。随着液膜高度由 50 nm 增至 125 nm，沿槽和横槽挤压阻抗均降低，且方向阻抗比由 3.98 减弱至 1.44。

必须同时保留以下限制：

```text
INPUT_CLOSURE_STATUS: CANDIDATE_FIXED_GRID
FINAL_GRID_INDEPENDENT_CLOSURE: false
```

因此，本节是微尺度方向性输运闭合在准静态挤压模型中的验证应用；它不等同于真实移动边界 LBM、两相填充预测或微尺度网格无关的最终结论。
