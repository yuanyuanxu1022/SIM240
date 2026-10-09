# EX240 黏性耗散机制分析

## 1. 字段定义与单位

OpenLB VTI 直接输出 `dissipation_m2_s3`，即物理比耗散率
`epsilon`，单位为 `m2/s3`。生成源码在写出 `field_slice.csv` 和
`energy_dissipation.csv` 时又计算

\[
\Phi=\rho_{phys}\,\epsilon,
\]

因此 CSV 中的 `Phi` 是体积耗散功率密度，单位为 `W/m3`。本文同时报告：

\[
\bar\epsilon,\qquad \int_V\epsilon\,dV,
\qquad \bar\Phi=\rho\bar\epsilon,
\qquad P_\mu=\rho\int_V\epsilon\,dV.
\]

统计只积分物理域内 material-1 流体节点，不包含 overlap 或固体。

## 2. 原始同体力结果

| dx=1.25 nm | parallel | perpendicular |
|---|---:|---:|
| mean epsilon (m2/s3) | 7.80440 | 3.47733 |
| integral epsilon dV (m5/s3) | 5.61917e-20 | 2.50368e-20 |
| mean Phi (W/m3) | 7.80440e3 | 3.47733e3 |
| viscous power P_mu (W) | 5.61917e-17 | 2.50368e-17 |

Perpendicular 的原始总耗散更小，不能据此判断其阻力更小。原因是两方向
采用相同体力而不是相同流量；parallel 的流量约为 perpendicular 的
2.24 倍，外力输入功率和稳态耗散也相应更大。这与稳态能量平衡一致。

## 3. 等流量比较

低 Mach、线性响应下，速度随驱动力成正比，而黏性耗散随速度梯度平方
变化。把 perpendicular 场缩放到与 parallel 相同的流量，需要速度乘以

\[
A=Q_{\parallel}/Q_{\perp}=2.240239.
\]

对应耗散乘以 `A^2`。于是：

\[
\left(\int\epsilon dV\right)_{\perp,Q=Q_{\parallel}}
=1.25651\times10^{-19}\ \mathrm{m^5/s^3},
\]

是原 parallel 耗散积分的 2.236 倍。该比值与
`R_perpendicular/R_parallel=2.240` 相差约 0.18%，支持方向阻力差异是
黏性耗散算子在两种几何取向下不同的结果，而不是惯性压降机制。

## 4. 空间分布

### Parallel

- 60% 的流体体积位于 `z<75 nm` 薄膜区，贡献 55.74% 耗散；
- 40% 的沟槽附加体积贡献 44.26% 耗散；
- 距沟槽竖直边缘 5 nm 内的附加沟槽区域只占 3.33% 总流体节点，贡献
  9.24% 总耗散，其 mean epsilon=21.62 m2/s3；
- 最大 epsilon=173.89 m2/s3，位置约为
  `(x,z)=(60.625,75.625) nm`，即沟槽下角附近。

这表明 parallel 的体积耗散分布总体随有效流动体积展开，但几何角点仍
形成局部耗散增强。

### Perpendicular

- `z<75 nm` 薄膜区贡献 91.17% 总耗散；
- 沟槽附加体积只贡献 8.83%；
- 沟槽口上下 5 nm 区域贡献 18.64% 总耗散，其 mean epsilon 为
  10.80 m2/s3，约为全域平均值的 3.11 倍；
- 最大 epsilon=76.78 m2/s3，位置约为
  `(x,z)=(181.875,74.375) nm`，即另一侧沟槽口附近。

因此，perpendicular 的耗散主要由连续薄膜和沟槽口速度重构区承担，
深沟槽内部并不是主要净输运或耗散通道。已有 VTI 支持“沟槽口/局部几何
变化区域出现耗散增强”；但壁面剪切应力没有被直接输出，本文不把该结果
改写成定量 `tau_w` 分布。

## 5. 网格敏感性

dx=2.5 nm 的体积平均 epsilon 分别为 parallel 7.80523、
perpendicular 3.48445 m2/s3，与细网格接近；等流量耗散比为 2.221，
与细网格 2.236 的机制一致。

局部最大 epsilon 则随加密上升：parallel 从 111.29 增至 173.89，
perpendicular 从 47.75 增至 76.78 m2/s3。这反映台阶角点的局部梯度
对分辨率敏感。因此论文机制应优先使用体积积分、分区占比和高耗散区位置，
不能把局部最大值当作已网格收敛的材料量。

## 6. 证据边界

细网格 perpendicular 的 `mass_error=1.196704e-10` 略高于 `1e-10`，
其 `PASS=false`、应用退出码为 3。耗散场有限且与 dx=2.5 nm 的空间模式
一致，可用于候选机制解释，但不构成完整门禁通过或普适耗散定律。
