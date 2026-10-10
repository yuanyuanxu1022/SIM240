# G4 EX240 多周期阻力收敛协议（冻结版）

冻结日期：2026-10-10。本协议在看结果前冻结；任何门禁、定义、阈值、公式在批次启动后不得修改（继承 AGENTS.md §13 与 SIM240_AI_CONTEXT.md §9）。

## 1. 范围与科学问题

回答：EX240 周期沟槽在横向复制 Nx=1,2,4,8（Ny=1）时，沿槽/横槽水力阻力 R 的数值行为如何，周期接缝与多周期几何实现是否保持数值完整性。

**解释边界（报告必须逐字保留）**：在 x/y 双周期边界与周期体力驱动下，Nx 个严格周期的解是单周期解的直接复制，R 按构造与 Nx 无关。本算例验证的是**数值不变性、周期接缝完整性与大域质量审计**；**不构成物理代表性尺度收敛或 RVE 收敛证据**（roadmap Case03 风险条目与本协议一致）。周期体力结果不得与入口/出口模型结果混用。

## 2. 冻结物理与数值参数（继承 G2 冻结表，不得改动）

| 参数 | 冻结值 |
|---|---|
| 周期/沟槽几何 | 周期 240 nm；台阶 60+60 nm；沟槽宽 120 nm；沟槽深 100 nm |
| 液膜高度 | h = 75 nm |
| 网格 | dx = 2.5 nm；dt = (tau−0.5)dx²/(3ν) = 1.0416666666666667e-12 s |
| LBM | D3Q19 FORCE；ForcedBGK；tau = 1.0；双精度；MPI 模式编译 |
| 壁面 | Bouzidi 零速；解析 q=0.5（容差 1e-10）；零 fallback、零 unresolved |
| 边界 | x/y 双周期；z 固壁 |
| 物性 | ρ = 1000 kg/m³；ν = 1.0e-6 m²/s（μ = 1e-3 Pa·s） |
| 驱动力 | a ∈ {5e4, 1e5, 2e5} m/s²（基准 1e5）；方向 P（沿槽 +y）/ T（横槽 +x） |
| 收敛窗 | 最近 1000 步 |

冻结母版源码：`CASE/02_geometry_transport/G2_EX240_single_period_transport/src/g2_ex240_single_period_transport.cpp`，SHA-256 `4acd63db67e273f87fed487fa7d1866f18dc82c018aaba1151f44882bd021002`。

## 3. Nx 矩阵与最大步数

- Nx = 1, 2, 4, 8；Ny = 1。Nx=1 的 6 个稳态点为复用基线（见 REUSE_AUDIT.md），不重跑。
- 每 Nx 期望值：fluid_nodes = 460800·Nx；candidate_links = 130176·Nx；q_min = q_max = 0.5。
- `maximumSteps = 60000·Nx²`（Nx=2: 240000；Nx=4: 960000；Nx=8: 3840000）。步数按 Lx²/ν 物理时间缩放冻结；未在步数上限内收敛 → 如实 FAIL（exit 3），不得事后延长。

## 4. 归一化与阻力定义

- A_plan(Nx) = Nx·240 nm·240 nm（代码经 `areaPlan = lx·ly` 自动成立）
- J_i = (1/A_plan)∫_{V_f} u_i dV；K_i = μJ_i/(ρa)；R_i = ρa/J
- nominalVolume = A_plan·h + Nx·(120nm·240nm·100nm)；referenceHeight 恒为 125 nm（自检锚）

## 5. 收敛判据（冻结阈值）

E(2Nx, Nx) = |R(2Nx) − R(Nx)| / R(Nx) ≤ **1%**（对齐力线性 K 跨度 ≤1% 门禁惯例）。

- 两方向各自判定；每个方向以三驱动力中基准 a=1e5 的 R 为准（另两驱动力作为级内线性自检）
- **连续两个扩展达标**：E(2→4) 与 E(4→8) 均 ≤1% 才报告多周期收敛；E(1→2) 仅报告（Nx=1 为复用基线）
- 任一扩展未达标 → 如实报告并做机制排查（接缝/Bouzidi/体力），不调整阈值

## 6. 每点验收门禁（10 项，继承 G2 冻结值）

1. geometry_PASS：fluid_nodes == 460800·Nx 且体积相对差 ≤1e-10
2. Bouzidi 审计：candidate == valid == installed；q=0.5±1e-10；fallback=0；unresolved=0
3. 质量：全程最大 max_mass_abs_relative ≤ 1e-10（相对 M0）
4. 密度：最大偏差 ≤ 1e-6
5. Mach < 0.05
6. 截面通量差 ≤ 1e-5
7. 横向通量 ≤ 1e-12 m²/s
8. 收敛窗：std/mean ≤ 1e-6 且 span/mean ≤ 5e-6
9. 有限值 + 材料场不变
10. 独立 exit_code.txt = 0（shell 与程序内一致）

级内追加：每 Nx 三驱动力线性拟合 R² ≥ 0.9999 且 K 最大相对跨度 ≤ 1%。

## 7. 计算模式与 MPI 仪器化层

**生产模式：MPI 多 rank**。生成源含 MPI 仪器化层（白名单块 M1–M10，见 scripts/generate_period_source.py 与 verify_deltas.py），逐条声明：

- M1 秩检查：`G4_EXPECTED_RANKS` 环境变量校验（未设置时接受任意 rank 数）
- M2 分解：`CuboidDecomposition(domain, dx, 1)` 后 `splitRegular(0, 48)`（每块约 48×48×50）
- M3 测量归约：measure() 全字段 MPI 归约（SUM/MAX/MIN/LAND），归约后计算派生量
- M4 材料计数归约；M5 边界审计归约（含 installed 字段，归约后再判 pass）
- M6 邻居物性：audit 改用块局部扩展读取 `block.get(solidR...)`（halo 材料由 geometry.communicate() 提供）
- M7 截面/剖面坐标：measure 与 writeFinalProfiles 改用全局格坐标 `getIcGlob`
- M8 剖面数组跨 rank 归约
- M9 文件写出：writePath 助手（非主 rank 写 /dev/null），覆盖 boundary_audit/result/result_summary/diagnostics/field_slice/profiles
- M10 其余 OpenLB 原生 MPI 组件（collideAndStream、SuperVTMwriter 等）不改

**生产 rank 分配（冻结）**：Nx=2 → 8 rank；Nx=4 → 16 rank；Nx=8 → 16 rank（每 rank ≥ 23 万格；cuboid 数 4Nx，均匀分配）。run_manifest 记录 rank 数与 G4_EXPECTED_RANKS。

**Scaling 验证（批次启动前必须通过，判据预先冻结）**：
- 对象：Nx=2、a=1e5；serial 模式二进制（1 rank）与 MPI 模式二进制（1/4/8/16 rank）各跑完整 precheck + 稳态
- 判据：各配置 10 项门禁全过；candidate_links == 260352；|J(MPI,nrank) − J(serial,1)|/J(serial,1) ≤ 1e-10；mass_error 轨迹逐点差 ≤ 1e-12
- 通过后才允许任何生产批次；失败 → 触发下述回退预案

**回退预案（预冻结）**：并发串行——serial 模式二进制、每点 1 rank、每级 6 点并发钉 P 核 0–5（taskset），总墙钟约 5 天。回退触发 = scaling 验证失败；切换需人工评审并记录。

**质量账本**：门禁施加于归约后的普通 double 求和（与 G2 口径一致）。历史证据边界：G2 审计表明 double/Kahan/long double 离线差异仅 ~1e-14 量级（G2_FINAL_STATUS §5），MPI 树形归约进一步降低漂移。预冻结增强预案：若 Nx=4 T 点 mass 轨迹峰值 > 5e-11，人工评审后可启用生成器 Kahan 开关（仅作用于后续批次，已跑批次不重判、门禁不变）。

## 8. 逐级门控与执行纪律

- 放行链：Nx=1 基线冻结（复用引用）→ Nx=2 级全过 → 人工审查放行 Nx=4 → 全过 → 人工审查放行 Nx=8
- 每级放行审查清单：10 门禁全过、级内线性自检、T 方向质量轨迹趋势审计（峰值/末段/漂移趋势）、E 比值、日志与磁盘检查
- 脚本（run_period_matrix.sh --level）只执行单级，**绝不自动跨级**
- 长算例必须 tmux 手动启动；每点独立 run 目录（时间戳 batch_id）；拒绝覆盖已存在目录；每点 run_manifest.txt + run.log + 独立 exit_code.txt
- 不得看结果后修改任何门禁/定义/阈值/公式；失败点如实报告（exit 3），不重写为 PASS

## 9. 归档与证据链

- 每批次：SOURCE_MANIFEST.md（协议 SHA、生成器 SHA、生成源 SHA、二进制 SHA、git commit、git status、ranks/钉核表）、batch_status.txt、latest_batch.txt
- 每 run：run_manifest.txt、run.log、exit_code.txt、boundary_audit.txt、diagnostics.csv、result.txt、result_summary.csv、field_slice.csv、pressure/velocity/energy_dissipation_profile.csv、vtkData
- 汇总报告：reports/G4_PERIOD_CONVERGENCE_SUMMARY.md（含 §1 解释边界原文、E 比值表、门禁汇总、证据边界）

## 10. 结论措辞边界

可断言：多周期几何实现下 R 的数值不变性程度、周期接缝与 Bouzidi 审计完整性、大域质量审计行为、线性响应保持。
不可断言：物理代表性尺度收敛、RVE 有效性证明、网格误差消除、真实压印外驱动行为。
