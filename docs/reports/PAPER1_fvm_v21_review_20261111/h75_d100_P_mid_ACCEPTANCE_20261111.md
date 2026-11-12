# h75_d100_P_mid 独立验收（2026-11-11 23:48 结束）

只读验收。未重跑、未改参数、未改门槛、未启动新算例。

## 1. 运行身份

| 项 | 值 |
|---|---|
| case | `h75_d100_P_mid` |
| run_id | `h75_d100_P_mid_20261111T234826_ef3cf27b` |
| 启动 | 23:48:26 |
| 结束 | 23:48:30 |
| 外迭代 | **2**（`final_time = 2.5`） |
| 停止原因 | `native_convergence` |
| `post_hoc_acceptance` | `accepted` |
| `ends_with_End` | true |
| 独立退出码 | 0 |
| 平板例外 | 未使用（`flat_zero_component_exception=false`） |
| 求解墙钟 | **0.62 s**（上限 14400 s，用掉 0.004%） |
| 网格 | 76800 单元（`dx = 0.625 nm`） |
| 种子 | `h75_d100_P_coarse` 末时刻 `2` → `0.5`，`map_exit_code=0` |

末残差：`v = 1.587030e-12 < 1e-10`。日志 `SIMPLE solution converged` / `End`。

## 2. 判定

`read_case()` → **`LOCAL_CHECKS_PASS`**，`issues = []`。

| 检查 | 值 | 门槛 | 结论 |
|---|---:|---:|---|
| 功率收支 | **0.035477%** | ≤ 0.1%（fine/tight/flat 硬闸；mid 为诊断） | PASS |
| 截面通量极差 | 0.0% | ≤ 0.1% | 不适用 |
| `ΣV` vs 冻结几何体积 | 一致 | 硬闸 | PASS |
| `checkMesh` | `Mesh OK.` | 硬闸 | PASS |
| 种子链（P coarse 2 → 0.5） | 完整 | 逐项绑定 | PASS |

**口径提醒**：P 是**标量 Poisson 单分量模型**（`equation="scalar_Poisson"`），`section_evidence = "exact y invariance of scalar model; not an independent mass test"`。⇒ **P 方向的"截面通量极差 0"不是独立质量守恒检验**，不能当作证据强度使用。P 的守恒证据只有功率收支与几何体积两项。

## 3. P 两档 K

| 层 | dx (nm) | 单元 | K (m³) | 外迭代 | 墙钟 | 功率收支 |
|---|---:|---:|---:|---:|---:|---:|
| coarse | 1.25 | 19200 | `9.766083321436146e-23` | 2 | 0.168 s | 0.105666% |
| mid | 0.625 | 76800 | **`9.758353097414943e-23`** | 2 | 0.62 s | 0.035477% |

- `d21 = |K_mid/K_coarse − 1| = 0.079154%` ≤ 1% ✓
- 对比 T 方向的 `d21 = 0.194279%`：P 在本层比 T 平滑，**但这是同一几何、同一有限体积框架下两个方向的结果，不是同一算法的两次运行**（P 为标量 Poisson 单分量 `v`，T 为速度/压力耦合 Stokes）。两者只能作"同框架不同方向"的对照，**不得**据此推断某一方向更好或更坏。
- 两档都是 **2 外迭代**即触发 `native_convergence`。**步数少不构成正确性的证据，也不能由此判断"没有漏算"**——可信度来自完整验收项（功率收支、几何体积、种子绑定、`checkMesh`、退出码、`End`），不是迭代次数。

## 4. delta 诊断（未进协议）

`K5_P = 9.834076e-23`（`comparison_inputs.json`）。

| Kref 取法 | `delta = (K5_P/Kref−1)×100` | 是否 <2% |
|---|---:|---|
| coarse | **+0.696212%** | ✓ |
| mid | **+0.775980%** | ✓ |

**距 2% 门槛余量 2.6~2.9 倍。**

**口径限制（必须遵守）**：`+0.6962%` 只是 **coarse 诊断**，不是正式判定；`+0.7760%` 同理。**不得用 T 方向的加密变化替 P 赋予"翻盘可能性小"之类的概率判断。** P 的正式结论必须由 P 自己的 fine 与 tight 给出。

## 5. 正式状态

`assess()` 对 `h75_d100_P` 为 **`NOT_ASSESSABLE`**，原因：`d32`（fine）与 `alg`（tight）均无法计算。

**P 必须完成自己的 fine 与 tight，不得用外推替代。** 下面这张表只是**算术校验**（"若 delta 破 2%，K_fine 须低到什么程度"），**不是对 P 结果的预测，不作概率陈述**：

| 项 | 值 |
|---|---:|
| 使 `delta = 2%` 所需的 `K_fine` | `9.641251e-23` |
| 相对 mid 需变化 | **−1.200%** |
| coarse→mid 实测变化 | −0.079% |

两者相差约 15 倍。**这只是说明"要翻线需要一次量级不同的下跌"，不说明它不会发生**。真实 `K_fine` 由 fine 算例给出，本报告不作预期。

## 6. 工期纠正（重要）

此前把 T 的墙钟（fine 12,764 s / tight 4,053 s）套到 P 上是错的。**P 是单分量标量方程，不是压速耦合 Stokes**：实测 coarse 0.168 s、mid 0.62 s。⇒ **P 的 fine/tight 预计各几秒到几十秒**，不是几小时。13,792 倍的算力差距来自方程类型，不是网格。

**注意**：这个工期差异同时说明 P 与 T 的"网格加密行为"不可互相外推——算法路径不同，加密后的表现没有先验理由相同。这也是 P 必须自己跑完 fine/tight 的技术原因。

## 7. 边界

- 本轮只读，未启动/重跑/停止/改代码/改门槛/改稿件。
- `assess()` 顶层仍 `status=INCOMPLETE`、`execution_status=PARTIAL`、`selected_six_all_pass=false`、`scientific_gate=NOT_A_GLOBAL_REFERENCE_QUALIFICATION`。
- 三项目级资格（`reference_qualified` / `strict_error_bound_established` / `submission_ready`）**仍为 false**。
- T 方向的 `FAIL`（`delta=+2.5110%`）不变；历史 FAIL 不变；36 条主统计与论文数字不变。
- P 方向的 `delta` 目前只是诊断，**不得**写入任何协议结论或用于改稿。
