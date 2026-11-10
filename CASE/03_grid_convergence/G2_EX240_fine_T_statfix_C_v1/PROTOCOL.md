# 细 T 方案 C：仅统计修复的独立正式参考 v1（冻结）

冻结日期：2026-10-14。目标仅为 h=75 nm、dx=1.25 nm、T/+x 的一个新正式参考；不覆盖旧 FAIL、不扩展 P、端点高度、45° 或 Z 挤压。依据为 4000 步诊断的 `STATISTICAL_BRANCH_SUPPORTED`，但该诊断不是正式 K 放行。

## 物理与算法不变项

源自 `G2_EX240_grid_convergence/build/generated/g2_ex240_dx1p25.cpp`（SHA256 `898cbe394a4528ae3ef925002ccb16eb33da433651276457e5913b128174281e`）。仅允许在独立副本中增加质量统计，不改原 `value.mass += rho * rhoPhys * dx * dx * dx`、D3Q19_FORCE/ForcedBGK、Bouzidi、周期边界、材料、初始化、体力、时间推进、通量或收敛计算。

- 单周期 240×240 nm；槽宽 120 nm、槽深 100 nm、mesa 间隙 75 nm；dx=1.25 nm、dt=2.604166666666667e-13 s、tau=1。
- rho=1000 kg/m³、nu=1e-6 m²/s、mu=1e-3 Pa·s、a_x=1e5 m/s²；1 rank、1 cuboid、1 计算线程、overlap=3。
- 最大 60000 步；原 1000 样本 J 收敛窗：相对样本 std≤1e-6、span≤5e-6、交叉 J≤1e-12。不人为延长、不提前截断为 4000 步。

## 双账本及门槛

- `diagnostics.csv` 的旧 `mass`、`mass_error` 保持原顺序 double 求和和旧初态分母，逐步另列 `corrected_mass`、`corrected_mass_error`、`delta_mass_error`、`mass_ledger_agreement`。
- 修复量是同一批 `computeRho()`、同一流体掩模、同一物理质量项的 Neumaier 求和。新质量门禁使用该账本相对其自身初态的全程最大绝对相对变化，**严格 `<1e-10`**；旧值同时输出且按原严格门槛单独标记，不能回写历史 PASS。
- 独立交叉量为补偿求和的 Σ(rho−1)，以 `[Σdelta(t)−Σdelta(0)]/[N+Σdelta(0)]` 计算；两条相对质量轨迹全程最大绝对差≤1e-13 是测量一致性目标，不替代物理质量门槛。全程非有限值拒绝。
- 其他原门槛不改：几何/材料和体积、candidate=installed、q=0.5±1e-10、fallback/unresolved=0、Mach<0.05、density≤1e-6、末态截面差≤1e-5、主 J>0、收敛、独立退出码0。`result_summary.csv` 的 `mass_error` 和 `result.txt` 的 `max_mass_abs_relative` 指**新批准统计**，新增 `legacy_*` 字段报告旧账本。

## 执行与验收边界

先审查最小源码 diff、算术测试、OpenLB 版本/库与构建证据、资源预算，再编译并做 `precheck T` 零推进：独立 exit0、geometry/converter/q PASS、3,686,400 流体节点、521,472 安装 links、无 fallback/unresolved、collideAndStream 0 次。预检通过只说明**可由用户启动正式计算**。

正式运行必须用新 run_id，保存源/库/程序哈希、完整参数、run.log、原始 CSV/场、独立 shell exit、全程质量/密度/Mach/J、最终 result。运行结束后另行审查旧轨迹与诊断前 4000 步 J/legacy mass 的兼容性（预期逐位，但若不同须解释）、新旧门禁、末窗、几何与 q。若库或动力学变化，不拼接旧网格链；即使单点 PASS，还需审查 Smooth/P/T 九点链的来源和 STEP3 GCI/相对指标，才能声明 h75 网格结论。端点高度的网格和线性证据仍另行补齐。

历史 dx1.25/T `PASS=false` 与 exit3 永久保留；本独立新版本不得称旧运行已被“修正为 PASS”。本协议不授权自动启动正式 60000 步计算。
