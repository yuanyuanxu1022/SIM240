# G2 Step3 质量账本分解报告

**目标运行**：`dx=1.25 nm / EX240_perpendicular / steady`  
**批次**：`g2_grid_20260917T165045+0800`  
**审计日期**：2026-09-18  
**范围**：只分析该运行的质量误差来源，不修改物理参数、门禁阈值或 Case 结构。

## 1. 结论

该点的 `mass_error=1.1967043900362632e-10` 主要由质量测量账本的浮点
累加基线和“全时间序列最大值”判定共同放大；现有证据不支持把它解释为
LBM 已发生同量级的真实质量生成。

最关键的直接证据是：在 `step=0`，所有初始化流体节点的平均密度为
`rho=1`，但源码逐节点累加得到的初始质量已经比理论质量低
`8.6210583e-11`（相对理论值）。因此后续 `mass_error` 使用该有偏的初始
质量作分母和基准时，剩余可用误差余量已被消耗大部分。

这不是对失败门禁的否定。按冻结协议，该点仍然是：

```text
RESULT_PASS=false
NUMERICAL_GATE contribution=FAIL
geometry_PASS=true
in-program exit_code=3
```

## 2. 冻结定义与原始证据

源码 `build/generated/g2_ex240_dx1p25.cpp` 在 material-1 core cells 上执行：

```cpp
value.volume += dx * dx * dx;
value.mass += rho * rhoPhys * dx * dx * dx;
value.densityIntegral += rho * dx * dx * dx;
```

每一步的门禁质量误差为：

```cpp
mass_error = (state.mass - initial.mass) / initial.mass;
```

并且：

```cpp
maxMassError = max(maxMassError, abs(mass_error));
```

因此门禁使用的是全程最大误差，而不是最终一步或收敛窗口内误差。

原始结果给出：

| 量 | 值 |
|---|---:|
| fluid nodes | 3,686,400 |
| `dx` | 1.25e-9 m |
| `rhoPhys` | 1000 kg/m3 |
| 理论体积 `N*dx^3` | 7.200000000000000e-21 m3 |
| 理论质量 `rhoPhys*N*dx^3` | 7.200000000000000e-18 kg |
| `step=0` 累加质量 `M0` | 7.1999999993792838e-18 kg |
| `M0` 相对理论质量偏差 | -8.6210583e-11 |
| 报告最大 `mass_error` | 1.1967043900362632e-10 |
| 最大误差所在步 | 625 |
| 独立退出码 | 3 |

## 3. 误差分解

### 3.1 初始账本基线误差

在 `step=0`：

- `rho=1`；
- `mass_error=0`，因为它被定义为相对于自身 `initial.mass`；
- 但 `M0` 相对理论质量已经是 `-8.6210583e-11`。

这与物理初始化质量不足不同：初始化场的密度是 1，偏差来自对 3,686,400
个很小浮点项进行普通串行累加，以及 `rho*rhoPhys*dx^3` 的乘法/加法舍入。
源码同时对 `volume`、`mass` 和 `densityIntegral` 使用不同的累加表达式，
不能假定它们的舍入误差完全相同。

### 3.2 瞬态峰值

从 `diagnostics.csv` 重算得到：

| 区间 | 最大 `abs(mass_error)` | 所在步 | 该步相对理论质量偏差 |
|---|---:|---:|---:|
| 1–999 | 1.1967043900e-10 | 625 | +3.3459847e-11 |
| 1000–2999 | 1.1448519362e-10 | 1414 | +2.8274611e-11 |
| 3000–9999 | 1.0545515008e-10 | 3064 | +1.9244569e-11 |
| 10000–19999 | 9.4221414709e-11 | 11634 | +8.0108333e-12 |
| 20000–29548 | 9.4020690010e-11 | 20000 | +7.8100972e-12 |

门禁首次超过 `1.0e-10` 的步数为 120；最大值发生在步 625。此时质量相对
理论值实际上只有 `+3.3459847e-11`，其余约 `8.62e-11` 的量级来自初始
累加基线与运行中累加舍入的组合。该分解不能把剩余项全部严格归为舍入，
因为 step=625 的完整三维逐点 population 未被保存，无法离线做补偿求和。

### 3.3 稳态尾部

最后 1000 个样本（`step=28549–29548`）中：

- `mass_error=9.3985595286e-11`（基本恒定）；
- `window_rel_std=9.9995236e-7`；
- `window_rel_span=3.4611809e-6`；
- `section_relative_difference=5.0407192e-9`。

所以质量误差的门禁失败由全程峰值触发，而不是最终通量统计窗口出现新的
质量发散。按照冻结协议仍必须保留该 FAIL，不能改用稳态尾部值替换
`maxMassError`。

## 4. 交叉账本证据

### 4.1 体积

结果文件的最终 `fluid_volume_m3=7.1999999999129086e-21`，相对理论体积
约为 `-1.21e-11`。这与同一普通累加模式产生的量级相符，说明几何节点数
本身没有发生变化；`fluid_nodes=3686400` 且 `material_unchanged=true`。

### 4.2 平均密度与点值密度

- 最终平均密度列：`rho=1.0000000000344249`，相对 1 的偏差约
  `3.44e-11`；
- 最大点值密度偏差：`1.6636287902827007e-9`；
- `rho_min=0.99999999833638997`、`rho_max=1.0000000016636288`。

点值密度偏差不是总质量误差，不能直接相加作为质量预算。平均密度和
`mass` 由不同浮点累加路径得到，二者存在约 `1e-11–1e-10` 的舍入差，
进一步说明当前账本对求和顺序敏感。

### 4.3 其他门禁

本点同时满足：

- geometry/Bouzidi audit：candidate=installed=`521472`，q=0.5，fallback=0；
- `max_Mach=3.1455271e-8`；
- `max_density_deviation=1.6636288e-9`；
- `section_relative_difference=5.0407192e-9`；
- `window_rel_std=9.9995236e-7`、`window_rel_span=3.4611809e-6`；
- finite=true，material_unchanged=true，converged=true。

因此当前证据指向质量账本/门禁统计边界，而不是几何 link、Mach、稳态窗口
或明显的密度爆炸。

## 5. 根因判断的证据等级

**已确认**

1. `mass_error` 的初始参考 `M0` 本身相对理论质量有 `-8.6210583e-11`
   的累加偏差。
2. 最大误差发生在瞬态 step 625；最终 1000 样本没有继续增长。
3. 固定节点数、几何体积和 material field 没有发生变化。
4. 门禁使用全程 `max(abs(mass_error))`，不是最终状态值。

**高可信推断**

普通双精度逐节点累加是该误差的主导来源之一；3.6864M 节点使求和舍入
达到 `1e-10` 量级是数值上合理的。瞬态密度场变化会改变求和顺序下的舍入
表现，并形成 step 625 峰值。

**尚未证实**

仅凭现有 CSV 不能把 step 625 的剩余 `3.3459847e-11` 相对理论偏差完全
拆成“真实 LBM 总质量变化”与“运行态累加舍入误差”。因为没有保存该步的
完整三维逐点 rho/population，无法进行独立 Kahan/long-double 重算。

## 6. 不允许采取的处理

- 不修改 `rho`、`nu`、`mu`、`a`、`tau`、dx 或网格尺寸来压低误差；
- 不把 `1.196704e-10` 四舍五入成 `1e-10`；
- 不放宽 `massTolerance=1e-10`；
- 不用最终稳态 `9.39856e-11` 替代全程最大值；
- 不把程序内 `PASS=false` 和退出码 3 改写成 PASS；
- 不将该点的 `Keff` 作为已通过 Gate 的最终闭合值。

## 7. 建议的最小后续诊断

在不改变物理参数和门禁的前提下，下一次诊断应只增加账本证据：

1. 同一运行路径同时记录 `M_nominal=rhoPhys*N*dx^3`、`M0`、`M(t)`、
   `M(t)-M_nominal` 和 `densityIntegral/volume`；
2. 对同一时刻的三维 material-1 rho 做 Kahan 或 long-double 独立求和，
   至少覆盖 step 0、step 625 和最终步；
3. 保持现有 `maxMassError` 门禁原样，诊断值只用于解释，不用于替代门禁；
4. 若补偿求和显示真实总质量仍超过 `1e-10`，再沿 population/碰撞守恒
   路径定位；若补偿求和回到门限内，则可将当前失败明确归档为测量累加误差。

在完成该独立证据前，最严谨的结论是：

> 该点的质量门禁确实 FAIL，但失败主要表现为接近双精度累加分辨率的
> 质量账本偏差，现有结果不足以证明存在同量级的物理质量不守恒。

## 8. 数据来源

- 原始结果：
  `CASE/03_grid_convergence/G2_EX240_grid_convergence/results/g2_grid_20260917T165045+0800/runs/dx1p25/EX240_perpendicular/steady/result.txt`
- 质量时间序列：同目录 `diagnostics.csv`
- 独立退出码：同目录 `exit_code.txt`
- 边界审计：同目录 `boundary_audit.txt`
- 计算源码：
  `CASE/03_grid_convergence/G2_EX240_grid_convergence/build/generated/g2_ex240_dx1p25.cpp`
