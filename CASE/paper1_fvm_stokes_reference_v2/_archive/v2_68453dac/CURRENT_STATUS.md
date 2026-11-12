# 当前状态（v2，2026-11-11）

状态：`PREPARED_NOT_RUN`，`formal_review_status = PENDING_ASTRA_V2_RECHECK`，`numerical_execution_authorized = false`。26 份输入已生成并冻结，**没有任何求解结果**。

## 为什么有 v2

v1 的两方向平板基准暴露两个阻塞（证据见 [`PAPER1_fvm_flat_benchmark_20261111/REPORT.md`](../../docs/reports/PAPER1_fvm_flat_benchmark_20261111/REPORT.md)）：

1. **6000 步迭代上限不足**。`h75_d0_T_flat` 跑满 6000 步给 −8.943434%；同算例 40000 步给 +0.013878%，与 P 方向的 +0.013889% 在六位有效数字上一致。
2. **`residualControl { U 1e-10 }` 结构性不可达**。40000 步时 Ux 残差 5.5e-11、p 残差 5.3e-13 均已达标，但 Uz 残差卡在 4.13e-10；而此刻 max|Uz| = 1.45e-16，相对 max|Ux| 仅 2.06e-12，已是机器零。Uz 方程源项恒为零、归一化分母极小，残差被摁在 1e-9 量级的地板。

因此单加步数走不通，判据必须同时改。

## v2 改了什么

| 项 | v1 | v2 |
|---|---|---|
| 迭代上限 | 6000 | coarse 6e4 / mid 1.2e5 / fine 2e5 / tight 2.5e5 / flat 6e4（上限，非计划量） |
| 墙钟上限 | 1800 s | 1800 / 14400 / 43200 / 43200；flat 3600 |
| 初场 | 全零场 | mid←coarse、fine←mid、tight←fine；`mapFields` 写入 `0.5/` |
| 残差控制 | 仅作判据 | 仅作提前退出触发：p 1e-10、U 1e-9、v 1e-10；tight 各收紧 10 倍 |
| 收敛判定 | 日志字符串 | 退出码 0 + End，且（字符串 或 主导分量 ≤1e-9）；postprocess 独立重算并与 receipt 核对 |

**几何、物性、边界、离散格式、linear solver 容差、全部接收与比较阈值未改。** 源码与二进制哈希与 v1 相同，不需要重编译。

## 已验证（准备证据，不是数值基准）

- 合成测试 21/21 通过（含判据边界的 7 项、阈值未放松的 1 项守卫）。
- `mapFields` 机制：写入目标 `startTime` 目录、条目数与极值完整。
- 发布树外副本跑通 coarse→mid 全链路：种子进 `0.5/`，`release_unchanged = True`（种子不造成假漂移），后处理按新判据正确判 FAIL。副本已删除。
- 复核闸门实测有效：当前状态下 `run_one.py --case … --execute` 直接被拒。
- v1 release 未被破坏：哈希仍 `ac4ca625…5b633`，漂移 0 项。

## 停点

开跑前必须完成指定模型复核，并把 `formal_review_status` 改为 `ASTRA_FINAL_STATIC_RECHECK_COMPLETE`。主代理不自行改写该位。

开跑顺序由 `seed_from` 决定，必须先粗后细：`h75_d100_T_coarse` → `_mid` → `_fine` → `_tight`。源算例未产生 `solver_converged=true` 的 receipt 时，下一层拒绝启动。

六方向沟槽算例在 v1 与 v2 中均未求解。固定 4 几何 6 方向、方案 A 目标及失败处置不变。
