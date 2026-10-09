# EX240 周期纳米沟槽方向性液压阻力机制

## 1. 数值结果与证据状态

本报告分析已有 OpenLB 单相、固定几何、周期体力驱动结果，不运行新算例。
坐标统一为 parallel=`+y`、perpendicular=`+x`、`z`=壁法向。

| Direction | Keff (m3) | R_eff (Pa s m-3) | run evidence |
|---|---:|---:|---|
| parallel (+y) | 9.7643255262e-23 | 1.0241362778e19 | converged, PASS=true, exit 0 |
| perpendicular (+x) | 4.3586133688e-23 | 2.2943076510e19 | converged, mass gate slightly exceeded, PASS=false, exit 3 |

方向比为

\[
\frac{R_{\perp}}{R_{\parallel}}
=\frac{K_{\parallel}}{K_{\perp}}
=2.2402367.
\]

该数值来自 `dx=1.25 nm`。其中 perpendicular 的
`mass_error=1.196704e-10`，略高于冻结门槛 `1e-10`。因此细网格数值和
场可用于受限的机制分析，但不能写成两个方向均完整 `RESULT_PASS`。
dx=2.5 nm 已通过运行给出相同机制趋势及方向比 2.230734，作为辅助检查。

## 2. 几何起点

EX240 单胞在 `x` 方向为 60/120/60 nm 的 mesa/groove/mesa 排列，沟槽
沿 `y` 连续。mesa 下液膜高度为 75 nm，沟槽深度为 100 nm。因此：

- 沿 `y` 流动时，几何在主流方向上平移不变，175 nm 高的沟槽区域形成
  连续输运路径；
- 沿 `x` 流动时，流体周期跨越 75 nm 薄膜区和 175 nm 沟槽区，必须在
  `x-z` 截面内调整速度和压力。

方向差异不是外部驱动力差异：两方向均有 `rho*a=1e8 Pa/m`，对应一个
周期 24 Pa 的相同等效驱动。

## 3. Geometry -> velocity reconstruction

Parallel 场几乎为纯 `u_y`：非主方向速度均值与主速度均值之比仅
`6.4e-8`，沟槽附加体积贡献 40.89% 净通量。流动能够直接利用沿槽连续的
额外高度，主速度在中央沟槽附近达到最大。

Perpendicular 场则发生显著 `x-z` 重构：平均 `|u_z|` 约为平均主速度的
12%，而沟槽附加体积仅贡献 5.87% 净通量。94.13% 净通量仍由
`z<75 nm` 的连续薄膜承担。沟槽附加体积内约 42.6% 节点出现幅值很小的
负 `u_x`，说明存在局部反向速度分量；由于未积分流线，本文不把它夸大为
已确认的闭合涡或惯性分离。

由最终 VTI 重算得到

\[
J_{\parallel}=9.764328\times10^{-12},\qquad
J_{\perp}=4.358610\times10^{-12}\ \mathrm{m^2/s},
\]

其比值 2.240239 与汇总 `Keff` 比一致。相同体力下横槽方向的速度重构没有
转化为同等有效净通量，这是 `R_perpendicular>R_parallel` 的直接运动学
表现。

## 4. Velocity reconstruction -> pressure redistribution

Parallel 方向沿程相位平均压力近似常数，局部变化仅为微帕量级。
Perpendicular 方向出现与两侧沟槽边缘锁定的周期压力重分布：细网格相位
平均压力在 `x=60.625 nm` 为 `-4.8309 Pa`，在 `x=179.375 nm` 为
`+4.8310 Pa`；dx=2.5 nm 得到近似相同的位置和幅值。

这些压力变化用于满足截面改变下的局部动量与连续性约束。它们不是独立于
体力驱动的第二个压降，也不能用 `p_max-p_min` 代替 24 Pa 等效宏观驱动。
沟槽边缘的点值梯度随网格加密明显增大，因此只作为强梯度位置证据，不作为
已收敛的局部损失系数。

## 5. Pressure redistribution -> viscous dissipation

OpenLB `dissipation_m2_s3` 表明：在相同体力下，parallel 因流量更大而有
更大的原始总耗散；这不能反向解释为其阻力更大。在线性 Stokes 响应下，
把 perpendicular 场缩放到与 parallel 相同的流量后，其耗散积分是
parallel 的 2.236 倍，与阻力比 2.240 相符。

空间上，parallel 的薄膜区和沟槽附加体积分别贡献约 55.7% 和 44.3%
耗散；perpendicular 的薄膜区贡献约 91.2%，沟槽口上下 5 nm 区域的平均
比耗散约为全域平均的 3.1 倍。两个方向的局部最大耗散均位于沟槽口/角点
附近，但局部峰值随网格变化，不作为收敛量。

这说明横槽方向的黏性代价集中在受限薄膜和几何重构区域，而深沟槽体积对
净横向输运贡献很小。对给定流量而言，横槽方向需要更大的驱动力和耗散，
最终表现为更高的有效阻力。

## 6. 机制链

```text
EX240 条纹几何
  -> parallel 沿几何不变方向连续输运；perpendicular 周期跨越台阶
  -> perpendicular 出现 x-z 速度重构，深沟槽净通量利用率低
  -> 沟槽边缘形成周期压力重分布
  -> 等流量下薄膜/沟槽口区域承担更高黏性耗散
  -> K_perpendicular < K_parallel，R_perpendicular > R_parallel
```

核心机制不是高 Re 的惯性扩张损失，而是低 Mach、低 Re 条件下，几何取向
改变了可利用的连续流动截面、局部速度梯度及 Stokes 黏性耗散泛函。

## 7. Results + Discussion 建议表述

> Under the same periodic body force, transport parallel to the EX240 grooves
> remains nearly unidirectional and utilizes the additional groove volume as a
> continuous conducting pathway. In contrast, perpendicular transport requires
> substantial velocity reconstruction in the x-z plane, while most of the net
> flux remains confined to the 75 nm basal film. The associated periodic
> pressure redistribution and localized viscous dissipation near the groove
> mouths increase the dissipation required at equal flow rate. Consequently,
> the effective perpendicular resistance is approximately 2.24 times the
> parallel resistance for the present geometry and numerical protocol.

论文中必须紧接限定：该 2.24 比值对应当前 EX240 几何和数值协议；细网格
perpendicular 的质量门禁略超阈值，局部压力梯度与耗散峰值也未证明点值
网格收敛。因此本结果支持方向性阻力的机制解释，但不证明任意纳米沟槽的
普适各向异性规律。

## 8. 关联报告

- `velocity_mechanism.md`：速度分量、通量分区及位置统计；
- `pressure_loss_analysis.md`：周期压力重分布及宏观压降边界；
- `dissipation_analysis.md`：OpenLB 耗散字段、等流量归一化及空间分区。
