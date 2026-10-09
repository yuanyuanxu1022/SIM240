# G2 Step3 质量累加实现审计

**目标运行**：`dx=1.25 nm / EX240_perpendicular / steady`  
**结果目录**：`CASE/03_grid_convergence/G2_EX240_grid_convergence/results/g2_grid_20260917T165045+0800/runs/dx1p25/EX240_perpendicular/steady/`  
**源码**：`CASE/03_grid_convergence/G2_EX240_grid_convergence/build/generated/g2_ex240_dx1p25.cpp`  
**审计日期**：2026-09-18  
**范围**：只审计质量账本实现和现有时间序列，不修改 Case、物理参数、阈值或 PASS 逻辑。

## 1. 审计结论

当前 `mass_error` 来自一个以初始测量质量为基准、逐步重新遍历
material-1 core cells 的普通双精度累加账本。`step=0` 的初始化账本已经相对
理论质量偏低 `8.6210583e-11`，因此该偏差在后续差分中被隐藏在 M0 基准内；
运行中的累加舍入和瞬态密度分布随后形成 step=625 的最大值
`1.1967043900e-10`。

这确认了一个重要的实现事实：当前失败值是“测量质量相对 M0 的全程最大值”，
不是直接相对解析名义质量的守恒误差。现有数据支持普通求和舍入是主要贡献
来源之一，但没有 step=625 的完整三维逐点 population，不能把剩余部分全部
严格证明为浮点误差。

## 2. 质量代码路径

### 2.1 M0 初始化

源码位置：`Measurement measure(...)` 约第 407–465 行；调用位置约第 681 行。

初始化完成后执行：

```cpp
const Measurement initial = measure(lattice, geometry, converter, p.drive);
```

此时 lattice 已由 `defineRhoU`/`iniEquilibrium` 初始化，随后才进入时间循环。
`initial.mass` 就是 M0，没有使用理论质量或 `rhoPhys*N*dx^3` 替代它。

### 2.2 当前质量累加

在 `measure()` 的 material-1 分支中，约第 420–435 行：

```cpp
if (blockGeometry.getMaterial(latticeR) != 1) {
  return;
}
const T rho = cell.computeRho();
++value.fluidNodes;
value.volume += dx * dx * dx;
value.mass += rho * rhoPhys * dx * dx * dx;
value.densityIntegral += rho * dx * dx * dx;
```

因此当前质量公式为

$$
M(t)=\sum_{c\in\mathrm{material\ 1\ core}}
\rho_c(t)\,\rho_{phys}\,\Delta x^3,
$$

并且门禁误差在约第 707 行计算为

$$
e_M(t)=\frac{M(t)-M_0}{M_0}.
$$

### 2.3 普通 double 求和

`Measurement::mass` 类型为 `T`，而本源文件定义 `using T = double`。代码使用
逐 cell 的 `operator+=`，没有 Kahan/Neumaier 补偿、`long double`、精确整数
体积账本或 pairwise reduction。`volume` 和 `densityIntegral` 也是各自独立
的普通 double 累加。

## 3. material 与周期边界语义

### 3.1 material 筛选

质量、体积、密度积分和速度积分均只统计：

```cpp
block.forCoreSpatialLocations(...)
if (blockGeometry.getMaterial(latticeR) != 1) return;
```

因此：

- material 0、2、3 不计入质量；
- overlap/padding 不计入质量；
- 统计节点数为 material-1 core cells 的 `3,686,400`；
- 结果中 `material_unchanged=true`，没有证据表明统计集合随时间改变。

### 3.2 周期边界

`wrapPeriodicXY()` 只出现在 Bouzidi 几何邻居审计和安装距离检查中，用于把
边界邻居索引映射回 x/y 周期范围。`measure()` 的质量循环不调用该函数，也
不额外复制或折算周期端点。

该运行是单 MPI rank，源码没有对质量执行跨 rank reduction；因此本点不存在
“周期端点重复计数”或“MPI 分块质量未合并”的直接证据。质量账本的核心风险
是单 rank 上对 3,686,400 项的累加顺序与浮点舍入。

## 4. 初始质量偏差

从目标 `diagnostics.csv` 的 step=0 记录：

```text
fluid_nodes = 3686400
rho = 1
mass_error = 0
mass = 7.1999999993792838e-18 kg
```

由固定节点数和 `dx=1.25e-9 m` 得到理论值：

$$
V_{exact}=3{,}686{,}400(1.25\times10^{-9})^3
       =7.2\times10^{-21}\ \mathrm{m^3},
$$

$$
M_{exact}=1000V_{exact}=7.2\times10^{-18}\ \mathrm{kg}.
$$

所以：

$$
\frac{M_0-M_{exact}}{M_{exact}}
=-8.6210583\times10^{-11}.
$$

这一步的 `rho` 已为 1，故该偏差不能解释为初始化密度偏离；它来自
`rho * rhoPhys * dx^3` 项运算及 3,686,400 次普通 double 加法的舍入。它还
说明当前 `mass_error=0` 只表示“相对自身 M0 为零”，不表示“相对理论质量
为零”。

## 5. step=625 最大误差触发路径

时间循环约第 702–724 行的顺序为：

```cpp
for (int step = 0; step <= maximumSteps; ++step) {
  if (step > 0) lattice.collideAndStream();
  const Measurement state = measure(...);
  const T massError = (state.mass - initial.mass) / initial.mass;
  maxMassError = std::max(maxMassError, std::abs(massError));
  diagnostics << ... << massError << ...;
}
```

目标序列给出的关键记录为：

| step | M(t) (kg) | 相对 M0 的 `mass_error` | 相对理论质量偏差 |
|---:|---:|---:|---:|
| 0 | 7.1999999993792838e-18 | 0 | -8.6210583e-11 |
| 120 | 7.2000000001016616e-18 | 1.0033025050e-10 | +1.4120e-11 |
| 625 | 7.2000000002409109e-18 | **1.1967043900e-10** | +3.3459847e-11 |
| 999 | 7.1999999997870540e-18 | 5.6634751918e-11 | -2.9575833e-11 |
| 29548 | 7.2000000000559801e-18 | 9.3985595286e-11 | +7.7750139e-12 |

因此 step=625 的数值关系是：

$$
e_M(625)=
\frac{7.2000000002409109\times10^{-18}
-7.1999999993792838\times10^{-18}}
{7.1999999993792838\times10^{-18}}
=1.1967043900\times10^{-10}.
$$

其中约 `8.62e-11` 的量级已经存在于 M0 相对理论值的负偏差中；step=625
的当前累加值相对理论质量仅为 `+3.35e-11`。这说明最大值由“有偏 M0 基准
+运行态普通求和/密度场变化”共同触发，而不是一个可从结果直接读出的
`1.1967e-10` 物理质量增量。

门禁在约第 718 行不断更新 `maxMassError`，因此 step=625 的瞬态峰值会保留
到最终结果，即使最后 1000 步的误差约为 `9.39856e-11` 且不再增长。

## 6. 证据边界

**已确认**

1. M0 由第一次 `measure()` 的 material-1 core-cell 普通 double 求和得到。
2. 当前 M(t) 使用完全相同的筛选和累加表达式。
3. 周期 wrap 不参与质量统计；overlap/padding 不计入。
4. step=625 是全程最大值触发点；最终窗口不是峰值来源。
5. 初始 rho=1 时已经存在 `-8.6210583e-11` 的相对理论质量偏差。

**高可信推断**

3.6864M 项普通 double 累加及其运算顺序是主要误差贡献之一；瞬态密度场
变化改变各项舍入表现，使 step=625 出现峰值。

**尚未证实**

没有保存 step=625 的完整三维逐点 rho/population，因此不能仅凭现有 CSV 将
该步剩余误差严格分成“LBM 总质量变化”和“运行态累加舍入”。

## 7. 下一步建议

下一步应保持当前物理参数、几何、阈值和 PASS 逻辑不变，只增加诊断证据：

1. 在同一统计循环记录 `M_nominal`、`M0`、`M(t)`、`M(t)-M_nominal` 和
   `densityIntegral/volume`；
2. 对 step=0、625 和最终步的完整 material-1 rho 做 Kahan/Neumaier 或
   `long double` 独立求和；
3. 对比普通求和与补偿求和，但不以补偿值替换现有门禁值；
4. 若补偿求和仍超过 `1e-10`，再检查 population 守恒和碰撞/力项；若补偿
   求和回到阈值内，则可把当前失败明确归档为质量测量累加误差。

在完成上述独立证据前，当前点必须继续报告 `RESULT_PASS=false`、
`exit_code=3`；不得将其改写为通过。
