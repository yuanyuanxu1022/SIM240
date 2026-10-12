# SIM240 AI CONTEXT

> 用途：供后续 AI/Codex 快速恢复 SIM240 当前状态。
> 本文件只描述“项目现在是什么状态”，不是历史日志，也不是论文正文。
> 状态基准：原主线条目为 2026-09-21；G4 周期复制执行状态于 2026-10-12 针对性更新。
> 决策优先级：以最新研究方案 `CASE/SIM240研究方案 Draft v2.0.md` 和当前 Gate 证据为准。
> 历史 `SIM_EC1XT240_CURRENT_STATE.md` 中的 moving-boundary STEP 5 已降为可选 G6，不再阻塞当前主线。

## 1. 当前研究定位

当前论文主线已经从“单纯比较周期结构流阻”提升为：

**微观 DNS 参数化 → 有效迁移率张量 $\mathbf K_{\mathrm{eff}}$ → 介尺度闭合 → 宏观纳米压印挤压排液预测。**

纳米压印宏观过程是：

**$z$ 方向压头加载 → 产生内部压力场 $p(x,y,t)$ → $x$-$y$ 平面横向排液。**

周期体力驱动只是在固定间隙 RVE 中提取局部线性输运闭合参数的数值方法。

它不代表真实压印的外部驱动，也不等于把完整压印过程替换成压力驱动通道流。

第一阶段物理范围：连续介质、牛顿、单相、等温、全充液、无滑移、低 Reynolds 数。

两相、润湿、困气、非牛顿、固化和封闭结构属于后续扩展。

直接移动边界 LBM 仅作为后期高保真交叉验证，不是当前论文主线的前置条件。

## 2. 核心闭合关系

固定间隙、线性响应下：

$$
\boldsymbol q=-\frac{\mathbf K_{\mathrm{eff}}}{\mu}\nabla_{\parallel}p.
$$

介尺度质量守恒：

$$
\frac{\partial H_{\mathrm{eff}}}{\partial t}
+\nabla_{\parallel}\cdot\boldsymbol q=0.
$$

因此：

$$
\nabla_{\parallel}\cdot
\left(\frac{\mathbf K_{\mathrm{eff}}}{\mu}\nabla_{\parallel}p\right)
=\frac{\partial H_{\mathrm{eff}}}{\partial t}.
$$

$\mathbf K_{\mathrm{eff}}$ 是微尺度 OpenLB DNS 向介尺度模型传递的核心参数。

当前主输出优先使用深度积分通量 $\boldsymbol q$（或 $J_i$）和 $K_{ij}$；若报告 $B_{ij}=K_{ij}/H_{\mathrm{ref}}$，必须明确 $H_{\mathrm{ref}}$。

## 3. 当前科学问题

1. 如何在驱动力线性、网格收敛和周期边界一致的条件下可靠提取 $\mathbf K_{\mathrm{eff}}$？
2. $h$、$D/P$、$W_g/P$ 和方向 $\theta$ 如何影响 $\mathbf K_{\mathrm{eff}}$？
3. 如何建立 $K_{\parallel}$、$K_{\perp}$ 和完整迁移率张量，并验证张量旋转关系？
4. 如何把 $\mathbf K_{\mathrm{eff}}$ 接入介尺度 squeeze-flow 模型，预测 $p$、$\boldsymbol q$ 和 $F_z$？
5. RVE、准静态闭合和连续介质模型的适用范围是什么？

## 4. 当前 OpenLB 数值协议

| 项目 | 当前值 |
|---|---|
| OpenLB | 1.8r1 |
| OpenLB commit | `882924a9cfc8dcdf82909e39530789cb6f5ebcc4` |
| lattice | D3Q19 |
| collision | ForcedBGK |
| 精度 | `double` |
| G1 已验证生产网格 $\Delta x$ | 2.5 nm |
| G1 已验证生产时间步 $\Delta t$ | $2.5\times10^{-12}$ s |
| $\tau$ | 1.7 |
| G1 网格序列 | $\Delta x=10.0,\ 5.0,\ 2.5$ nm；扩散标度保持 $\tau=1.7$ |
| 面内边界 | $x/y$ 双周期 |
| 固壁 | $z$ 向 link-wise Bouzidi；当前平板所有 $q\approx0.5$，退化为 halfway link bounce-back |
| 驱动 | 周期体力；基准 $a=10^5\ \mathrm{m/s^2}$，$G=\rho a$ |
| 线性检查 | $a=5\times10^4,\ 10^5,\ 2\times10^5\ \mathrm{m/s^2}$ |
| 物性 | $\rho=1000\ \mathrm{kg/m^3}$，$\nu=10^{-6}\ \mathrm{m^2/s}$，$\mu=10^{-3}\ \mathrm{Pa\,s}$ |
| 统计域 | 仅 material 1 物理流体；overlap/padding 不计入积分 |

当前 G1 平板：$L_x=L_y=240$ nm，$H=75$ nm，单 MPI rank。

解析迁移率：

$$
K_{\mathrm{smooth}}=\frac{h^3}{12}.
$$

## 5. 当前 Case 路线

| Gate | 任务 | 核心产出/判据 |
|---|---|---|
| G0 | 数值实现与边界审计 | 几何、material、周期映射、links、$q$、fallback、单位和证据链正确 |
| G1 | Smooth 平板迁移率验证 | 验证 $K=h^3/12$；驱动力线性；三网格收敛/GCI |
| G2 | EX240 直沟槽 RVE | 提取 $K_{\parallel}(h)$、$K_{\perp}(h)$ 及不确定度 |
| G3 | 0°/45°/90°方向验证 | 验证 $\mathbf K(\theta)=\mathbf R\mathbf K_0\mathbf R^T$ |
| G4 | 结构/间隙参数化 | 建立 $\mathbf K_{\mathrm{eff}}=f(h/P,D/P,W_g/P,\theta)$ |
| G5 | 介尺度挤压模型 | 输出宏观 $p$、$\boldsymbol q$、$F_z$ 和质量闭合 |
| G6 | 直接移动边界 LBM 交叉验证 | 可选；只在质量与载荷门禁通过后用于验证准静态模型 |
| G7 | 复杂物理扩展 | 两相、润湿、非牛顿、封闭结构、困气等后续研究 |

## 6. 当前真实进度

### 已完成

- OpenLB 环境、编译和运行链路已建立。
- G0 几何、material、周期边界和实现检查已完成。
- 周期 material overlap 通信根因已定位并修复。
- Bouzidi link 安装审计已完成。
- theoretical/candidate/valid/installed links = `23040/23040/23040/23040`。
- $q_{\min}=0.49999999999999784$，$q_{\max}=0.5$。
- geometric fallback = 0；missing-neighbour fallback = 0。
- unresolved anomaly/links = 0。
- 当前功能网格已达到稳态，并通过质量、密度、Mach、截面一致性和有限性检查。

**判定：G0 实现与边界安装审计完成。**

### 已完成（G1）

- **G1 Smooth Poiseuille / mobility validation：PASS（G1-v3 冻结协议）。**
- 固定物理定义：$H=75$ nm，$\Delta x=2.5$ nm，$\Delta t=2.5\times10^{-12}$ s，$\tau=1.7$；三驱动力为 $a_y=5\times10^4,10^5,2\times10^5\ \mathrm{m/s^2}$。
- 三个稳态算例均有独立退出码 `0`，收敛、质量守恒、密度、Mach、截面通量、有限性、几何与 $q$ 审计均通过；$q\approx0.5$、fallback/unresolved links 均为 0。
- 三个迁移率误差均为 `+1.168883%`，速度剖面 $L_2$ 误差均为 `1.016323%`，满足 2% 门槛。
- 力—通量拟合：$R^2=1.0$；截距占最大 $J$ 的 $6.04\times10^{-9}$，满足独立线性门槛。
- 三网格误差单调降低；观察阶 `2.095847`，Richardson 外推相对理论误差 `+0.098068%`，细网格 GCI `1.323053%`。

保留历史事实：原冻结的 5 nm、$\tau=1.7$ 基线仍为 FAIL（通量 `+4.675555%`、剖面 $L_2$ `4.065283%`）；它是离散误差诊断记录，不得改写成 PASS。

**判定：G1 在 G1-v3 细网格冻结协议下正式 PASS；原 5 nm 基线仍独立保留为 FAIL。**

### 当前 G4 周期复制审计（2026-10-12）

- 修复版完整 MPI scaling `g4_scaling_nx2_fields_v1_20261011T221741+0800` 数值与场输出检查通过。
- 修复版 Nx=2 `g4_period_nx2_fields_v1_20261012T001316+0800` 六点独立 exit=0、收敛、几何/q、质量、密度、Mach、线性和 E(1→2) 审查通过；每点切片 9600 数据行，完整覆盖。
- 放行证据另存 `CASE/03_grid_convergence/G4_EX240_period_convergence/reports/NX2_FIELDS_RELEASE_20261012.json`，原批次不改写。
- 旧 Nx=4 `g4_period_nx4_20261011T201010+0800` 因用户关机/重启而运行中断；不是数值算法 FAIL；全部原始证据保留。
- 修复版 Nx=4 编译与初始化输出短检查通过；独立入口 `scripts/run_fields_nx4.py`，每例 16 ranks、并发 1。用户已于 2026-10-12 启动批次 `g4_period_nx4_fields_v1_20261012T105719+0800`；当前只有进程存在证据，未审查结果，不作 PASS/FAIL 判定。
- 本 G4 执行目录验证周期复制数值不变性/接缝完整性，不等同于下表 G4 参数化闭合完成，也不构成物理 RVE 收敛证据。

### 原路线条目（历史状态，不能替代具体批次证据）

- G2 正式 EX240 $\mathbf K_{\mathrm{eff}}$ 数据库。
- G3 张量方向验证。
- G4 参数化闭合模型。
- G5 介尺度 squeeze-flow 模型。
- G6/G7 不属于当前启动范围。

已有固定间隙或动态边界结果只作为候选数据/方法经验，不自动追认为新版 Gate 结果。

## 7. 当前边界问题结论

旧问题不是几何高度、体力换算或采样位置错误。

旧审计发现：直接修改 `BlockGeometry` 后，周期 material overlap 未正确同步，导致周期接缝部分 Bouzidi link 异常。

修复后：

- theoretical links = 23040；
- candidate links = 23040；
- valid-distance links = 23040；
- installed links = 23040；
- $q\approx0.5$；
- fallback = 0；
- unresolved anomaly = 0。

5 nm 基线的约 4.68% 通量偏差与 $\tau$/网格相关；网格误差按约二阶下降，且 2.5 nm 的独立三驱动力矩阵通过。现有证据支持将其定性为离散偏移，但并未给出 ForcedBGK、离散体力与 halfway 边界各自贡献的严格分解。

**边界安装审计通过，不等于 Poiseuille 解析精度通过。**

## 8. 每个 Case 强制输出规范

任何 Case 开始前必须明确：

1. 该 Case 回答什么科学问题；
2. 需要输出哪些数据；
3. 需要生成哪些论文图；
4. 需要保存哪些 CSV 和原始场；
5. 对应论文哪一章节；
6. PASS/FAIL 标准是什么。

每个正式 run 至少保存：唯一 run ID、源码哈希、OpenLB 版本/commit、完整参数与单位转换、质量/通量/密度/Mach 时序、收敛证据、独立退出码、完整日志和原始场。

图表必须从原始 CSV 自动重算，不得硬编码汇总值。

收敛、结果文件写出和程序正常退出是三类独立证据，不得互相替代。

## 9. 当前禁止事项

- 不直接跳到完整动态纳米压印。
- 不把 moving-boundary 未通过结果写成成功。
- 不把周期 body-force 说成真实压印外部驱动。
- 不把单网格 $\mathbf K_{\mathrm{eff}}$ 称为最终闭合参数。
- 不修改解析高度来人为降低误差。
- 不通过减去速度常数偏移制造 PASS。
- G1 未通过前，不把 EX240 结果作为最终定量论文结论。
- 不用 $p_{\max}-p_{\min}$ 代替周期体力驱动的宏观压降。
- 不把边界安装 PASS、稳态 PASS 或退出文件存在误写为 Gate1 PASS。
- 不在当前阶段加入两相、润湿、困气、非牛顿或固化。

## 10. 下一任务

当前执行任务：等待用户启动的修复版 Nx=4 独立批次自行结束；本阶段不持续轮询。结束后另行审查所有门槛、输出、E(2→4) 与横槽质量轨迹。未放行前不自动启动 Nx=8。
以下为较早的总体路线事项，不作为本次计算启动依据。

1. 正式冻结 EX240 $\mathbf K_{\mathrm{eff}}$ 提取协议，包括 $J_i$、$K_{ij}$、参考高度、方向、间隙、网格、驱动力和近零交叉项定义。
2. 在已冻结 EX240 协议下，开展固定间隙的 $K_\parallel$、$K_\perp$ 正式计算与不确定度评估。
3. 若需发表机理解释，再独立分解常量速度偏移的离散来源；该工作不阻塞已通过的 G1 验证门。

## 更新规则

每完成一个 Gate 或研究路线发生变化时：

1. 更新“当前真实进度”；
2. 更新“当前已知问题”；
3. 更新“下一任务”；
4. 删除已经失效的临时信息；
5. 不无限追加历史日志。

该文件始终描述“SIM240 现在是什么状态”，而不是“SIM240 过去发生过什么”。
