# SIM240 输运参数与介尺度填充模型接口审计

## 1. 审计范围与结论

审计对象为当前 EX240 G2 单周期 OpenLB 实现及已完成的 G2 Step3 输出，重点代码：

`CASE/02_geometry_transport/G2_EX240_single_period_transport/src/g2_ex240_single_period_transport.cpp`

结论：当前代码已经能够提取**固定几何、周期体力驱动下的局部水力输运参数**，足以支持

```text
geometry → J/K_eff → 介尺度输运闭合的第一版参数接口
```

但尚不能直接完成真实瞬态“填充预测”。目前缺少压力边界/压力降的独立定义、随时间变化的有效高度与局部储液量、二维/三维介尺度场接口，以及经过能量收支验证的全域耗散积分。

## 2. 当前已经输出的量

### 2.1 速度

- VTK：`velocity_m_s` 三维速度场；
- `field_slice.csv`：`ux,uy,uz,speed`，在固定切片输出；
- `velocity_profile.csv`：按主驱动方向位置平均的速度剖面；
- `diagnostics.csv`：每步主方向通量 `J` 和三分量 `Jx,Jy,Jz`。

速度输出足以复核局部流场、主方向通量和横向交叉流门禁。

### 2.2 压力

- VTK：`pressure_Pa`；
- `field_slice.csv`：rho 与 pressure；
- `pressure_profile.csv`：按驱动坐标切片平均的压力剖面；
- `result.txt`：`pressure_range_Pa=p_min,p_max`。

但当前驱动为 x/y 周期体力，不存在入口/出口压力边界。`pressure_range_Pa` 是流体节点上的局部压力范围，不应直接称为周期单元压力降；宏观驱动力应使用已记录的 `rho*a` 并明确符号和方向。

### 2.3 流量/通量

源码 `measure()` 中：

```text
integratedVelocity[i] += u_i * dx^3
J_i = integratedVelocity[i] / areaPlan
```

因此 `J_i` 的单位为 `m²/s`，是深度积分通量/单位平面面积通量。对主方向，`result.txt` 写出 `J_main_m2_s`，`result_summary.csv` 写出 `J`。

同时代码在两个截面累计：

```text
Q_section = Σ u_main * dx²
```

并写出 `Q_sections_m3_s` 及截面相对差异。该量可作为周期质量闭合检查；对于本 RVE，主参数仍应使用 `J`，不能把两个截面 Q 当成独立入口/出口流量。

### 2.4 质量

- `diagnostics.csv`：逐步 `mass`、`mass_error`、平均 rho、最大密度偏差；
- `result.txt`：最大相对质量误差、fluid volume、material unchanged；
- 质量定义为 material-1 节点上 `rho * rhoPhys * dx³` 的顺序累加。

质量输出可以作为数值守恒门禁，但不是填充模型所需的液体体积随时间/位置变化量。当前几何固定，不能从该质量序列直接得到压印填充前沿。

### 2.5 能量耗散

OpenLB 输出：

- VTK：`dissipation_m2_s3` functor；
- `field_slice.csv`：`Phi`；
- `energy_dissipation.csv`：沿驱动坐标的切片平均 `Phi`。

代码先调用 `BlockLatticePhysDissipation3D` 得到基于非平衡应力的物理耗散量，再执行：

```text
phi = rhoPhys * epsilon
```

因此 `Phi` 实际上更接近体积耗散率（应以 `W/m³` 解释），而 writer 名称 `dissipation_m2_s3` 对乘以 `rhoPhys` 后的字段并不完全准确。当前输出是切片/位置平均，不是整个 fluid domain 的积分功率，也没有与 `G·Q` 或 `∫2μE:E dV` 做独立能量收支核对。

## 3. 当前 K_eff 的计算

源码最终使用：

```text
K_eff = muPhys * J_main / (rhoPhys * acceleration)
```

其中：

- `J_main = ∫_fluid u_main dV / A_plan`；
- `rhoPhys * acceleration` 是周期体力对应的体积力强度；
- `muPhys=rhoPhys*nuPhys`。

因此当前 `K_eff` 是固定几何 RVE 在线性体力驱动下的主方向有效迁移率，适合写入：

```text
q = -K_eff/mu * grad(p)
```

其中 `grad(p)` 必须明确等效为 `-rho*a`，不能使用 `p_max-p_min` 替代。

## 4. geometry → hydraulic transport → filling model 映射

### 4.1 已有 geometry 参数

`result.txt` 和 precheck/boundary audit 已有：

- `Lx,Ly` 周期尺寸；
- `mesa_gap`、`groove_depth`、`groove_width`、`H_ref`；
- `dx,dt,tau` 及流体节点数/体积；
- material-0/1/2/3 计数；
- candidate/installed link 数、q 范围、fallback、unresolved link；
- VTK material 场和速度/压力/耗散场。

这足以重建 G2 固定 RVE 的拓扑和数值几何审计链。

### 4.2 已有 hydraulic transport 参数

- `K_parallel`、`K_perpendicular`；
- `J` 与三分量 `J_vector`；
- `Q_sections` 与截面差异；
- 质量误差、Mach、收敛窗口和有限值；
- 粗/中/细网格 Richardson/GCI；
- 三驱动力线性验证；
- 局部压力/速度/耗散剖面。

这些量足以建立基准高度下的主方向对角输运闭合和各向异性比。

### 4.3 填充模型仍缺少的参数

要进入介尺度填充/挤压预测，还需要：

1. **明确压力驱动接口**：二维/三维场中的 `∇p`、符号约定、单位胞平均压力梯度与 `J` 的映射；
2. **完整迁移率张量**：至少 `K_parallel,K_perpendicular`，并定义旋转方向和非对角项；
3. **有效储液高度/体积**：`H_eff(h)`、单位面积液体体积及其随 h 或时间的变化；
4. **局部几何闭合**：从结构高度场/solid mask 计算 `H_eff(x,y,t)`，而不是只保存单个 `H_ref`；
5. **瞬态质量闭合**：填充方程所需的 `∂H_eff/∂t + ∇·q=0` 验证数据；
6. **边界/初始条件**：压头加载、压力边界、液体初始分布和填充前沿定义；
7. **能量/阻力交叉验证**：全域耗散积分、体力功率和压力功率之间的独立收支。

## 5. 当前能否支持介尺度填充预测

### 可以支持

- 固定 h、固定 EX240 RVE 的局部 Darcy/润滑型输运闭合；
- `K_parallel(h)`、`K_perpendicular(h)` 的参数化数据库框架；
- 各向异性主方向输运比较；
- 在外部介尺度模型已给定 `∇p` 和 `H_eff` 时计算局部 `q`。

### 尚不能直接支持

- 直接由当前周期体力稳态结果预测压印填充时间或填充前沿；
- 直接输出宏观压力场、液体占据率、填充体积分数或压头载荷；
- 以当前 `pressure_range_Pa` 作为入口—出口压力降；
- 以当前切片 `Phi` 作为已验证的全域耗散功率；
- 在 h、几何或边界随时间变化时自动更新 `K_eff` 和质量守恒。

## 6. 后续需要增加的输出（建议，不在本次修改）

建议后续新增独立后处理/输出字段，而不是改变现有 G2 定义：

| 类别 | 建议输出 |
|---|---|
| 压力接口 | `grad_p_effective_Pa_m`、方向、符号和 `rho*a` 对照 |
| 输运 | `K_tensor`、主/交叉通量、单位面积 `q`、截面/体积分一致性 |
| geometry | full material mask、局部 `H_eff(x,y)`、fluid volume fraction、solid/groove fractions |
| filling | `H_eff` 时序、`dH_eff/dt`、`div(q)`、质量闭合残差、填充前沿 |
| 能量 | 全域 `∫Phi dV`、`G·Q`、压力功率、相对能量残差 |
| 可追溯性 | run_id、源码 hash、OpenLB commit、完整参数和独立退出码 |

## 7. 最终判断

当前 SIM240 OpenLB 输出已足以提取经过 G2 线性与网格证据支持的固定几何 `K_parallel/K_perpendicular`，可作为介尺度输运闭合的输入。它还不是完整的介尺度填充预测接口；在进入论文级填充预测前，必须补齐压力梯度接口、局部有效高度/体积、瞬态质量闭合和全域能量收支验证。
