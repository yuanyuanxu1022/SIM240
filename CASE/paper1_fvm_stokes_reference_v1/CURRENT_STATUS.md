# 当前状态（2026-11-11 更新，v1 目录已封存为记录）

配置、后处理、OpenFOAM13 编译和指定 GPT-6 Astra High 静态复核均已完成；两方向平板基准已执行，结果见 [`PAPER1_fvm_flat_benchmark_20261111/REPORT.md`](../../docs/reports/PAPER1_fvm_flat_benchmark_20261111/REPORT.md)。

- `h75_d0_P_flat`（run `h75_d0_P_flat_20261111T103656_dc029a26`）：退出码 0，2 步收敛，K 误差 **+0.013889%**，`LOCAL_CHECKS_PASS`。
- `h75_d0_T_flat`（run `h75_d0_T_flat_20261111T103754_f0282937`）：跑满 6000 步上限未收敛，K 误差 **−8.943434%**，`REFERENCE_CHECK_FAIL`。同算例跑到 40000 步为 **+0.013878%**，证明这是迭代预算不足，不是实现错误。

因此本目录的两个阻塞已经确定：6000 步上限不足以让 T 收敛；`residualControl { U 1e-10 }` 被 Uz 分量的归一化残差地板（4.1e-10，而此时 Uz 已是机器零）卡住，日志字符串结构性不可达。

**本目录已封存，不再修改、不再重跑。** 两条运行记录（含 T 的 FAIL）原样保留，是本结论的第一手实证。修复版见 [`../paper1_fvm_stokes_reference_v2/`](../paper1_fvm_stokes_reference_v2/)：分层迭代预算、层间初场延拓、数值收敛判据，几何/阈值/离散格式/源码均未改动，其复核状态为 `PENDING_ASTRA_V2_RECHECK`。

最新完整回执：[`PAPER1_fvm_preparation_review_20261110/REPORT.md`](../../docs/reports/PAPER1_fvm_preparation_review_20261110/REPORT.md)。指定模型初审与修复后复核：[`ASTRA_REVIEW.md`](../../docs/reports/PAPER1_fvm_preparation_review_20261110/ASTRA_REVIEW.md)。该报告的"平板基准待启动"表述已被本次实际执行取代，其余结论（静态检查、B1/B2 修复、26 份输入构成）仍有效。

固定 4 几何 6 方向、方案 A 目标及失败处置不变。六方向沟槽算例在 v1 与 v2 中均未求解。release 的 `numerical_execution_authorized` 仍为 false。
