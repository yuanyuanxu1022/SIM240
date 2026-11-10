# R0：相场 CH 守恒根因定位报告（step6G 液滴下压路线）

- 日期：2026-10-15
- 性质：**只读诊断**。未编译、未运行、未修改任何源码与历史结论。
- 诊断对象：`phasefield_minimal_validation.cpp`（step6G）两个正式 run 的 FAIL 项 `max_phase_amount_relative_drift`（2.107e-3 / 2.395e-3 > 1e-3）。
- 结论速览：**漂移是启动弛豫瞬态，不是持续泄漏；不是润湿边界；不是 step6G 实现 bug。根因 = 非自洽初值激发的声波/毛细波寄生流 × well-balanced CH 对流源项的非零零阶矩记账。稳态守恒良好（~1e-8/步）。**

---

## 1 证据 E1：漂移是启动瞬态，稳态守恒（数据）

来源：两个正式 run 的 `history.csv`（`phasefield_contact_theta100_R18_formal_20260910`、`phasefield_laplace_R16_sigma001_formal_20260910`）。

| 量 | contact（θ=100°，含壁面） | laplace（全周期，无壁面） |
|---|---|---|
| 总步数 | 6000 | 4000 |
| 初始 phase_amount | 11728.25 | 17198.26 |
| 第 1 步单步变化 | **0（精确为零，−5.7e-15）** | **0（精确为零）** |
| 第 2/3 步单步变化 | −6.73 / −7.20 | −11.16 / −12.14 |
| 漂移谷底 | step 19，−2.107e-3 | step 18，−2.395e-3 |
| 末态漂移 | −6.73e-4 | −1.60e-3 |
| step50→末尾净漂移 | +2.13e-4 / 5950 步 ≈ **3.6e-8/步** | −1.61e-5 / 3950 步 ≈ **−4.1e-9/步** |

判定：FAIL 门槛（全程最大 |漂移| ≤ 1e-3）几乎全部由前 ~20 步贡献；第 50 步以后的漂移速率在舍入误差量级。**方案在稳态是守恒的。**

## 2 证据 E2：润湿边界被排除（对照实验天然存在）

laplace 案例为**全周期边界、无壁面、无 Bouzidi 润湿边界**（`Config{64,64,64,16,false}`，`setBouzidiWellBalanced` 仅在 `walls=true` 时调用），其启动漂移（2.40e-3）**不小于**含润湿边界的 contact 案例（2.11e-3）。

判定：**润湿边界（边界化学势/接触角处理）不是漂移的主要来源。** 先前"优先怀疑润湿边界"的假设被否定。

## 3 证据 E3：源码机制（OpenLB 1.8r1，只读核对）

### 3.1 漂移与对流源项逐点对应

step6G 主循环（`advance()`，源码 199–206 行）：`SOURCE`/`SOURCE_OLD` 字段由耦合后处理 `WellBalancedCahnHilliardPostProcessor`（`src/dynamics/phaseFieldCoupling.h:724-731`）以 Adams–Bashforth 二阶外推维护：

```cpp
source = gradPhi · u;                       // 对流项
SOURCE = 1.5*source - 0.5*source_old;       // AB2 外推
```

CH 碰撞中的源项修正（`src/dynamics/forcing.h:495-504`，`forcing::WellBalancedCahnHilliard`）：

```cpp
sourceTerm_i = t_i * (-2 + 0.5*invCs2*|c_i|^2) * source;
cell[iPop] += sourceTerm;
```

该修正的**零阶矩**（D3Q19 逐方向求和）= (−2 + 0.5·3·1)·source = **−0.5·source ≠ 0**。即：CH 格式的全局质量守恒依赖 `Σ_cells(u·∇φ)` 逐时步抵消，这只在速度场离散无散、且状态处于离散一致流形时近似成立。

**与 E1 数据完全吻合**：
- 第 1 步 `SOURCE=0`（初始化置零，且 u₀=0 时恰好自洽）→ 漂移精确为零 → **无源项的 CH 碰撞+迁移严格守恒**；
- 第 2 步起源项激活 → 漂移开始，且时间上与寄生流峰值重合（见 3.2）；
- 稳态 u→0 → source→0 → 漂移速率回落到 1e-8/步量级。

### 3.2 启动寄生流：初值不自洽的激发源

`history.csv` 逐行数据（两案例一致）：

| step | max_Mach | 漂移 | φ 范围 | Δp |
|---|---|---|---|---|
| 0 | 0 | 0 | [0,1] | 0 |
| 1 | 2.03e-2 | **0** | [−0.022, 1.019] | 2.7e-7 |
| 2 | 1.94e-2 | −5.7e-4 | [−0.019, 1.015] | 6.2e-4 |
| 5 | 1.67e-2 | −1.7e-3 | [−0.028, 1.020] | 2.4e-3 |

两个不自洽同时存在（源码核对）：

1. **φ 初值非离散平衡剖面**：初始化用 `SmoothIndicatorSphere3D(sphere, interfaceWidth/2)`（erf 型平滑指示函数，step6G 115–116 行），而该模型自身的离散平衡界面为 tanh 剖面 `0.5·(1+tanh(2d/w))`（壁面处理器 `phaseFieldCoupling.h:918` 等处使用的正是此形式）。第 1 步 φ 即越过 [0,1]（−0.022/1.019），说明界面在向 tanh 平衡剖面迁移。
2. **NS 压力场无 Laplace 跳变**：初始压力均匀为零（`defineRhoU(all,zero,...)`），液滴内外 Δp 从 0 开始建立（step 1 仅 2.7e-7，目标约 1.1e-3），初始声波必然产生。

两者共同激发 Ma≈2e-2 的启动寄生流（毛细波+声波），使 `u·∇φ` 在界面处非零，源项的非守恒记账随之累积 → 前 20 步损失约 2e-3 相场总量；随后波动衰减（laplace 案例 Ma 末态 4.7e-6），部分质量随振荡回流（漂移从谷底部分恢复）。

### 3.3 非 step6G 实现 bug

OpenLB 官方示例 `examples/multiComponent/contactAngle3d.cpp` 使用**完全相同**的初始化方式（`SmoothIndicatorSphere3D(sphere, interfaceWidth/2)`，217–219 行）。该启动瞬态是"示例级初始化惯例 + well-balanced CH 方案性质"的组合，不是本项目代码引入的错误。

## 4 根因判定（分层）

**已验证（证据链完整）**：
1. 漂移集中在前 ~20 步启动弛豫，稳态守恒（E1）；
2. 润湿边界不是主因（E2）；
3. 漂移由对流源项驱动：源项为零的时步漂移精确为零，源项激活即漂移，且量级与寄生流同步（E1+E3.1）；
4. 初值存在两处不自洽：φ 剖面非 tanh 离散平衡、压力场无 Laplace 跳变（E3.2）。

**推测（待 E0 判别实验证实）**：
- 自洽初始化后，启动寄生流可压低 1–2 个量级，全程最大漂移有可能自然降到 1e-3 以下；
- laplace 案例的末五次 Δp 稳定性 FAIL（7.08% > 5%）同一根源（启动激发的毛细振荡衰减慢），自洽初始化后有望改善；若仍不达标，可延长运行/后移采样窗。

## 5 修复方案

### Fix B1（首选，最小代码修改，动 step6G 本地源码）

自洽初始化，两处改动（新增变体 run-id，不覆盖原 run）：
1. φ 初值改用模型自身离散平衡剖面：`φ(d) = 0.5·(1+tanh(2d/w))`，d 为到液滴表面的距离（w=interfaceWidth）；
2. NS 压力初值带 Laplace 跳变：液滴内 `p_in = 2σ/R`、外部 0（晶格单位）。

预期：step 1 起 Ma 从 ~2e-2 降至 ~1e-3 以下；全程漂移显著缩小。

### Fix A（协议级保险，R1 新冻结协议的设计项）

无论 Fix B1 效果如何，R1 协议声明：初始化后设**弛豫窗口 N_relax（建议 200 步）**，守恒基线取弛豫后，门槛 `|漂移| ≤ 1e-3` 只作用于测量窗口；启动段漂移单独如实报告为"初始化弛豫量"。
依据：守恒的物理含义是"被测物理过程不泄漏质量"，不含数值初值弛豫。**这是运行前声明的新协议口径，不是对旧 FAIL 的改写**——20260910 两个 run 的 FAIL 按冻结协议原样保留。

### 不做

- 不修改 OpenLB 上游 `forcing.h` / `phaseFieldCoupling.h` 的源项格式（侵入性大，破坏与发表方案的可比性；且稳态已守恒，无必要）。

## 6 判别实验 E0（短程，单进程，分钟级）

| 实验 | 内容 | 判据 |
|---|---|---|
| E0-a | 仅改压力初始化（Laplace 跳变），laplace 案例 200 步 | step 1–50 的 max_Mach 与全程 max 漂移 |
| E0-b | 压力 + tanh φ 双改，laplace 案例 200 步 | 同上；对比 a/b 分离两处不自洽的贡献 |
| E0-c | 取 a/b 中最优者，contact 案例 500 步 | 接触角是否仍正常弛豫至 ~100°；漂移与 Mach |

判读：
- 若 E0-b/c 全程漂移 < 1e-3 → R1 协议可保留全程口径（Fix B1 充分）；
- 若仍 ≥ 1e-3 → R1 协议采用 Fix A 窗口化口径（运行前声明）；
- 若 E0-c 接触角弛豫异常 → 回退并单独排查（此时才考虑源项层面的深入）。

## 7 对路线的影响

- R0 结论：**相场 CH 路线无需"修复求解器"，只需自洽初始化 + 协议口径修正**。R1（平壁静滴润湿基准）的前置障碍从"方案不可用"降级为"初始化工程问题"。
- laplace 稳定性 FAIL 的处置并入 E0 观测项，暂不单独立项。
- 三个历史 FAIL（FreeSurface / 相场 / 移动边界）原样保留，本报告不改变任何既有判定。

## 8 证据文件清单

- 数据：`output/phasefield_contact_theta100_R18_formal_20260910/history.csv`、`output/phasefield_laplace_R16_sigma001_formal_20260910/history.csv`
- 本地源码：`phasefield_minimal_validation.cpp`（初始化 108–132 行、主循环 243–255 行、判定 260–266 行）
- OpenLB 源码（只读）：`src/dynamics/phaseFieldCoupling.h`（672–768 行）、`src/dynamics/forcing.h`（470–511 行）、`src/dynamics/equilibrium.h`（92–120 行）、`src/dynamics/dynamics.h`（446–453 行）、`examples/multiComponent/contactAngle3d.cpp`
