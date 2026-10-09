# F2_dynamic_v3 动态压缩模型设计方案

## 设计边界

本报告只审计并设计，不修改 `F2_dynamic_v2_motion` 的 C++、不编译、不运行计算。目标是建立单相液膜压缩模型，用于在动态高度下提取局部或准稳态水力阻力

```text
R(h) = Delta p(h) / Q(h)
```

这里的目标不是两相界面、VOF 或润湿填充，而是固定 EX240 真实几何拓扑下液膜高度改变所对应的单相动态水力响应。

## 1. 当前 v2 架构

### Geometry 生成

v2 在 `main()` 中根据运行参数 `p.mesaGap` 建立固定计算域。对每个 lattice cell 调用：

```text
materialAt(block.getPhysR(latticeR), p.mesaGap)
```

`materialAt()` 根据 `upperWall(x, mesaGap)` 将单元分为 fluid material-1、底部 material-2 和上部/沟槽壁 material-3。`ExactEX240FluidIndicator(p.mesaGap)` 用于解析 EX240 壁面距离和 Bouzidi link。

### Material 定义

当前 material field 只在时间循环之前写入一次，随后执行 `geometry.rename()`、`geometry.communicate()` 和初始 material 计数。初始 fluid volume 由 `nominalVolume(p.mesaGap)` 与 material-1 体积比较。

### Bouzidi boundary

v2 在初始 geometry 上执行 `auditGeometryLinks()`，然后对 material 2 和 3 调用 `setBouzidiBoundary()`，再用 `auditInstalledDistances()` 检查 q 和 link 数量。该安装路径只执行一次。

### LBM 流程

初始化后设置 Forced BGK、体力、rho/U 和 equilibrium。时间循环的核心只有：

```text
if step > 0:
    lattice.collideAndStream()
state = measure(...)
```

### timestep 与 diagnostics

v2 已定义：

```text
currentGap = max(0, p.mesaGap - compressionVelocity * step * dt)
```

并把 `currentGap` 写入 `diagnostics.csv` 的 `height_nm` 列。但是该变量没有反馈给 material field、geometry indicator 或 Bouzidi boundary，因此当前只改变诊断记录，不改变物理边界。

现有 diagnostics 记录了 J、rho、Mach、mass、mass_error、density deviation、截面 Q、pressure range、fill ratio 和收敛窗口指标。审计时还应修正一个设计问题：当前源码中的 diagnostics 表头顺序与数据写入顺序不完全一致，v3 必须采用显式字段映射并用 CSV 读回测试验证列对齐。

## 2. v2 缺少的动态模块

v2 尚缺少以下闭合链：

```text
h(t)
  ↓
wall position
  ↓
material field update
  ↓
geometry communication / validation
  ↓
Bouzidi q and link update
  ↓
LBM collision and streaming
```

具体缺口为：

1. `currentGap` 没有驱动 material 更新；
2. geometry 只创建一次，没有动态几何状态；
3. Bouzidi link 和 q 只审计/安装一次；
4. 没有对 newly-fluid、newly-solid 单元的分布函数处理；
5. 没有压头位移、壁面速度和流体边界通量的离散一致性；
6. 没有 `dV/dt` 与排出流量 Q 的质量闭合残差；
7. 没有把动态过程划分为可提取 `R(h)` 的准稳态窗口。

## 3. Geometry update 方案

### 推荐方案：离散高度状态的安全重建

v3 建议先采用清晰、可审计的离散高度序列，而不是一开始做连续 sub-grid 移动：

```text
h_0 -> h_1 -> h_2 -> ... -> h_n
```

每个高度状态使用同一固定 lattice domain，重新计算：

```text
upperWall(x, h_k)
materialAt(position, h_k)
ExactEX240FluidIndicator(h_k)
```

domain 顶部必须按最大初始高度预留；不能随着 h 缩小而改变 lattice domain 尺寸，否则会把几何变化与网格变化混在一起。

### 两种实现路径

**路径 A：每个高度状态重建 SuperGeometry/SuperLattice 边界对象。** 这是首版 v3 的推荐路径，代价是计算和初始化成本较高，但可以避免旧边界 postprocessor 残留。

**路径 B：在同一对象上增量更新 material。** 只有在确认 OpenLB 对动态 material、边界 postprocessor 移除/重装和分布函数迁移的 API 后才采用。该路径效率更高，但更容易留下旧 link、旧 q 或旧 cell state。

## 4. Material update 方案

每个更新时刻应执行：

1. 计算目标 `h(t)`；
2. 对全部 core cell 重新调用 `materialAt(position,h(t))`；
3. `geometry.rename()` 与 `geometry.communicate()`；
4. 重新计算 material-0/1/2/3 计数；
5. 计算解析目标体积 `V_target(h)` 与实际 `V_fluid`；
6. 分类 newly-fluid 和 newly-solid 单元；
7. 对 newly-fluid 单元初始化 rho/U 或从邻域重构分布函数；
8. 对 newly-solid 单元处理残余 population 和壁面反作用力；
9. 在进入下一次 `collideAndStream()` 前完成几何一致性检查。

不允许仅修改一个 `height_nm` 输出列而保留旧 material field。

## 5. Bouzidi link update 方案

每个高度状态必须重新执行：

```text
ExactEX240FluidIndicator(h(t))
auditGeometryLinks()
setBouzidiBoundary(...)
auditInstalledDistances()
```

必须保存每一状态的：

- candidate link 数；
- installed link 数；
- q_min、q_max；
- fallback 数；
- unresolved link 数；
- geometry_PASS 和 q_audit_PASS。

重新安装前必须确认旧 Bouzidi postprocessor 不会继续作用于已失效的 link。若 OpenLB API 无法安全移除旧 postprocessor，首版 v3 应采用路径 A：为每个高度状态创建新的 lattice/boundary 对象，或将高度状态作为独立短 run，以避免边界对象累积。

## 6. 质量守恒检查方案

### 体积闭合

每个时刻记录：

```text
V_fluid(t)
V_target(h(t))
delta_V(t) = V_fluid(t) - V_target(h(t))
dVdt_target
```

### 质量闭合

记录 material-1 质量、密度积分和相对质量误差：

```text
mass_error(t) = [M(t)-M(0)] / M(0)
```

### 排出流量与压头运动

对于不可压单相液体，压头体积变化必须由边界通量承担。应同时记录：

- 压头位移速度及 `dVdt_target`；
- P/T 方向的截面 Q；
- 周期方向净通量；
- 密度变化贡献；
- 质量闭合残差 `residual = dVdt_target - Q_out`。

当前 v2 使用 x/y 周期边界。纯周期闭合域没有物理入口/出口，因此压头压缩后的体积去向必须被明确建模：要么增加与压头运动相容的开放排出边界，要么把模型定义为周期 RVE 中的局部准稳态响应，并明确不解释为全局压头排液。不能在没有排出边界或体积约束的情况下宣称不可压缩质量守恒。

### R(h) 提取

只有在某个高度窗口内满足：

- geometry 和 Bouzidi audit 通过；
- `V_fluid` 与 `V_target` 一致；
- mass error、Mach、rho deviation 通过；
- Q、Delta p 和窗口统计达到稳态；
- 质量闭合残差通过；

才计算

```text
R(h) = Delta p(h) / Q(h)
```

并记录该值对应的 `h_window`、时间范围和门禁状态。

## 7. 需要修改的文件列表

本次不修改任何文件。未来实现 v3 时建议新建独立目录，不覆盖 v2：

```text
CASE/07_filling_dynamics/F2_dynamic_v3/
├── README.md
├── PROTOCOL.md
├── src/
│   ├── f2_dynamic_v3.cpp
│   └── Makefile
├── scripts/
│   ├── preflight_dynamic.py
│   ├── run_precheck_dynamic.sh
│   └── run_dynamic.sh
├── results/
└── reports/
```

源码职责建议拆分为：

- `DynamicHeightLaw`：定义 h(t)、速度和时间范围；
- `DynamicGeometryState`：material、体积和 cell transition；
- `DynamicBouzidiState`：解析 wall、q 和 link 审计；
- `MassClosureDiagnostics`：质量、体积、Q 和闭合残差；
- `RWindowAnalyzer`：准稳态窗口和 `R(h)` 提取。

不应修改：

- `CASE/07_filling_dynamics/F2_dynamic_v2_motion` 当前源码；
- F1/G2/G3 原 Case；
- 既有 results、PASS/FAIL 阈值和验证协议。

## 8. 风险分析

### 高风险

1. **周期边界与压缩排液不相容**：x/y 周期边界不能自动提供全局排液出口，可能把压缩体积错误地转化为密度变化。
2. **旧 Bouzidi link 残留**：仅改 material 而不重装 postprocessor 会产生错误壁面位置和 q。
3. **新增/移除流体单元的 population 处理**：直接切换 material 可能造成非物理质量或动量跳变。
4. **几何阶梯化**：h(t) 连续变化但 lattice material 只能按 cell 状态变化，会产生离散壁面跳跃和瞬态压力脉冲。

### 中风险

1. 动态压缩速度相对于 LBM 松弛时间过大，导致 Mach、rho deviation 或边界稳定性恶化；
2. `Delta p` 在周期体力驱动和动态壁面条件下的定义不清；
3. 稳态窗口尚未建立，瞬态 Q 直接用于 `R(h)` 会把惯性效应误判为水力阻力；
4. diagnostics 表头和写入顺序不一致，可能导致后处理把 fillRatio 或窗口指标读错。

### 低风险但必须审计

1. 结果目录、manifest、source hash 和独立 exit code 的对应关系；
2. newly-fluid 初始化时的 rho/U 连续性；
3. P/T 方向、压力定义和 Q 截面位置的一致性。

## 结论

v2 已提供固定几何单相输运和 `currentGap` 记录基础，但尚未实现真正的动态几何—material—Bouzidi 联动。v3 应作为独立 Case，从几何状态重建、边界链接更新和质量闭合三条证据链开始；在这些证据通过前，不应把 `R(h)` 动态曲线解释为已验证的压头压缩阻力模型。
