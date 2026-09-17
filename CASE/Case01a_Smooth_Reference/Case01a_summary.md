# Case01a Smooth Reference H75 Summary

## 1. 科学问题

在无沟槽、无纹理的$240\times240\,\mathrm{nm^2}$周期区域和$75\,\mathrm{nm}$平板间隙中，OpenLB-LBM能否给出可靠的光滑表面流阻基准，供后续EX240结构阻力归一化？

## 2. 计算参数

| 参数 | 设置 |
|---|---:|
| OpenLB | 1.8r1 local revision 5953d8a-dirty |
| lattice/collision | D3Q19 / ForcedBGK |
| boundary | exact planar Bouzidi, q=0.5 halfway |
| periodicity | x/y periodic |
| geometry | 240 nm × 240 nm × 75 nm |
| dx/dt | 5 nm / 1e-11 s |
| tau | 1.7 |
| ay | 1e5 m/s2 |

预运行geometry、material、wall-link、q和fallback门禁全部通过。

## 3. 流阻结果

| 指标 | 数值 |
|---|---:|
| $J_y$ | 3.679999984e-12 m2/s |
| $R_J=\rho a/J_y$ | 2.717391316e19 Pa·s/m3 |
| maximum mass drift | 0 |
| maximum Mach | 2.508010e-7 |
| velocity L2 | 4.065283% |

## 4. 与理论Poiseuille比较

理论$J_y=3.515625000\times10^{-12}\,\mathrm{m^2/s}$，理论$R_J=2.844444444\times10^{19}\,\mathrm{Pa\,s/m^3}$。LBM通量高估`4.675555%`，流阻低估`4.466712%`，未达到2%精度门槛。

该结果与Case01及Case01c同参数结果一致，再次确认这是当前$dx$和$\tau$组合的系统离散偏移，而不是沟槽或边界漏link造成的差异。

## 5. 后续用于EX240阻力归一化

该数值可作为“同网格、同$\tau$、同驱动”的诊断性Smooth分母候选，因为系统离散误差可能在阻力比中部分抵消。但在没有同网格收敛和误差抵消验证前，不能把它当作已验证的正式归一化基准，也不能据此启动Case02。

此外，Frozen Protocol v2.1将正式Case01a定义为$H=175\,\mathrm{nm}$。本$H=75\,\mathrm{nm}$算例必须标记为`Case01a_Smooth_Reference_H75`；若论文需要$R^*_{175}$，仍必须另行执行协议中的H175参考。

最终判定：**FAIL（解析精度）**；EX240和Case02均未运行。
