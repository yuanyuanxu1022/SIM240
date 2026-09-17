# Case01c Smooth Thin-Film Lubrication Validation Report

## 最终判定

**FAIL：未通过预先定义的2%润滑理论精度门槛。**

运行前geometry/material/link/q门禁通过，稳态、质量守恒、有限性、Mach和截面通量一致性均通过；但阻力相对误差为 `-4.4667115%`，速度剖面L2误差为 `4.0652830%`。应用程序独立退出码为 `3`，不能表述为正常通过。

## Geometry

| 项目 | 设置/结果 |
|---|---:|
| 几何 | 无沟槽平行平板薄膜 |
| $L_x\times L_y\times H$ | $240\times240\times75\,\mathrm{nm^3}$ |
| 壁面 | $z=0$ 与 $z=75\,\mathrm{nm}$ |
| fluid-cell centres | $z=2.5,7.5,\ldots,72.5\,\mathrm{nm}$ |
| 网格 | $48\times48\times15$ fluid cells |
| material 1 | 34560，等于理论值 |
| geometry gate | PASS |

材料2和3分别用于下、上壁及其非物理padding层；所有物理积分和守恒统计仅使用material 1。

## Boundary

| 指标 | 结果 |
|---|---:|
| 理论wall links | 23040 |
| candidate links | 23040 |
| valid-distance links | 23040 |
| installed links | 23040 |
| q范围 | 0.49999999999999784–0.5 |
| geometric fallback | 0 |
| missing-neighbour fallback | 0 |
| unresolved | 0 |

边界为解析平面Bouzidi；本几何所有link均处于$q=0.5$的halfway极限。边界安装门禁PASS。

## 模型与理论

- OpenLB 1.8r1 local revision `5953d8a-dirty`；
- D3Q19 + ForcedBGK；
- $\Delta x=5\,\mathrm{nm}$，$\Delta t=10^{-11}\,\mathrm{s}$，$\tau=1.7$；
- $\rho=1000\,\mathrm{kg/m^3}$，$\nu=10^{-6}\,\mathrm{m^2/s}$；
- 周期体加速度$a_y=10^5\,\mathrm{m/s^2}$。

均匀薄膜中，体力对应等效压力梯度$G=\rho a_y$。Reynolds/平板Poiseuille理论为

$$
J_{\mathrm{Re}}=\frac{a_yH^3}{12\nu},\qquad
R_{\mathrm{Re}}=\frac{\rho a_y}{J_{\mathrm{Re}}}.
$$

## Convergence

| 指标 | 结果 | 判定 |
|---|---:|---|
| completed steps | 1706 | — |
| 1000点窗口relative sample std | 8.0404842e-7 | PASS |
| 1000点窗口relative span | 4.9750110e-6 | PASS |
| stop reason | frozen_window_converged | PASS |

## Conservation and Mach

| 指标 | 结果 | 判定 |
|---|---:|---|
| diagnostics rows | 1707 | 完整 |
| non-finite rows | 0 | PASS |
| maximum material-1 mass drift | 0 | PASS |
| final mean density | 999.9999999998175 kg/m3 | PASS |
| section flux relative difference | 0 | PASS |
| maximum cross flux | 1.1582265e-22 m2/s | PASS |
| maximum Mach | 2.5080096e-7 | PASS |

## Analytical comparison

| 指标 | LBM | Reynolds theory | 相对误差 |
|---|---:|---:|---:|
| $J$ | 3.679999984e-12 m2/s | 3.515625000e-12 m2/s | +4.6755551% |
| $R$ | 2.717391316e19 Pa·s/m3 | 2.844444444e19 Pa·s/m3 | -4.4667115% |

速度剖面L2相对误差为 `4.06528299%`。数值剖面相对理论剖面呈近似均匀正偏移，平均偏移为 `2.087499788e-6 m/s`，与Case01同参数结果一致。

## 证据边界

- 编译：修正目录准备错误后成功，最终编译退出码0；首次失败没有生成可执行文件或启动仿真。
- 零时间步预检查：退出码0。
- 稳态求解达到冻结窗口：是。
- 稳态应用程序独立退出码：3，由解析精度失败触发。
- 总体验证：FAIL。
- 未运行EX240或其他Case。

## 科学解释

当前Case01c在几何、驱动和解析式上与Case01平板Poiseuille基准数学等价，因此它重复确认了同一个离散偏移，而不是提供完全独立的润滑理论证据。结果说明：在$\Delta x=5\,\mathrm{nm}$、$\tau=1.7$下，绝对阻力存在约4.47%的基准偏差。

若论文需要真正独立的Reynolds润滑验证，下一版Case01c应考虑缓变膜厚$h(x)$、给定压差/流量边界或非均匀润滑压力场，并验证Reynolds方程的空间压力—流量关系；该扩展不属于本次运行。

## 文件

- 预检查：`results/precheck_20260916T094600p0800/`
- 稳态结果：`results/steady_20260916T094627p0800/`
- 主要数值：`results/steady_20260916T094627p0800/result.txt`
- 完整历史：`results/steady_20260916T094627p0800/diagnostics.csv`
- 速度剖面：`results/steady_20260916T094627p0800/velocity_profile.csv`
