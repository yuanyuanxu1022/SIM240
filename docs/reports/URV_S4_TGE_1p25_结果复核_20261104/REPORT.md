# S4 薄间隙 1.25 nm 服务器重跑：结果整理与独立复核

时间：2026-11-04 23:58（北京时间）
run_id：`URV_S4_T_dx1p25_TGESRV_v1_20261104_01`
服务器：`10.103.102.55`（jj-Rack-Server），账户 `yuanyuan`
合同 SHA：`758f13deecec0a26ae309e982cbcadfb1aa9bf198e58513292bd2114df49631d`

> 本文是**技术复核/归档版**（取回服务器证据 + 独立重算）。
>
> 同日还有另外两份 1.25 产出，**角度不同、互补不重复**：
> - 给导师口头汇报的通俗版：`docs/reports/URV_S4_TGE_1p25_结果汇报_20261104.md`
> - 并行会话做的**数据收集/表格/Excel 版**（70 份取回文件、10 个 VTI 帧、
>   12538×25 原始诊断 Excel、完整性核对）：`outputs/URV_S4_1p25_data_20261104_234955/`
> - 并行会话的科学收尾证据：`docs/reports/URV_S4_TGE_completion_check_20261104_234545/`
>
> 本文的**独有贡献**是：不采信结果文件、从原始通量独立重算 K，并逐项复核 18 个检查点，
> 另澄清了统计窗的样本标准差异径（见 §2）。

---

## 0. 结论（一句话）

**1.25 nm 在服务器上跑完，我们从原始诊断数据独立重算的 K 值，与服务器报告值、本机参照值三者逐位相同（相对差 = 0）；构建等价判据成立。数值门槛、几何、质量守恒、边界审计全部干净。**

**但：这只是"构建等价 + 实测性能"的接受，不等于 S4 阶段通过。** 原始横槽中细差 1.328% > 1% 的 FAIL 没有被触碰。

---

## 1. 本轮做了什么

1. 从服务器取回 13 份原始证据，归档到 `server_evidence/`。
2. 写 `independent_recheck.py`，**不采信 result.txt 的 K**，改用 `diagnostics.csv` 的原始通量 J 自己重算。
3. 逐项核对 18 个检查点（全部 PASS），结果存 `independent_recalculation.json`。

**没有任何新增计算、没有重跑、没有改服务器文件、没有启动新算例。**

---

## 2. 独立复算（本轮新增的核心证据）

复算公式（输入全部来自冻结的 run_config，不是拟合）：

```
K = J · μ / (ρ · a)
μ = 0.001 Pa·s   ρ = 1000 kg/m³   a = 100000 m/s²
```

| 量 | 数值 |
|---|---|
| 原始诊断末步 J | 3.47179183674498660e-13 m²/s |
| **独立复算 K（末步）** | **3.47179183674498684e-24 m³** |
| 独立复算 K（末 2592 步窗均值） | 3.47179256440171055e-24 m³ |
| 服务器 result.txt 的 K | 3.47179183674498684e-24 m³ |
| 本机参照 K（测量前冻结） | 3.47179183674498684e-24 m³ |
| **与本机参照相对差** | **0.000000e+00**（门槛 ≤ 1e-6） |

统计窗（末 2592 步）：`rel_std = 8.2772157262e-07`、`rel_span = 4.9876521654e-06`，与 acceptance.json 及原始诊断末行一致。

> ★口径说明（值得记住）：检查器 `evidence.py:125` 用的是**样本标准差 ddof=1**
> （`w.std(axis=1, ddof=1)/|mean|`），不是总体标准差。第一版复算用了 n，
> 得出 8.2756e-7 与 8.2772e-7 的"不一致"是**口径差异造成的假警报**，不是数据问题。
> 检查器自身核对原始诊断的容差是 `rtol=1e-5`，本复算与之对齐。

---

## 3. 18 项核对结果：全部 PASS

| 类别 | 检查项 | 结果 |
|---|---|---|
| 复算 | 独立 K 与 result.txt 一致（<1e-12） | PASS，相对差 0 |
| 复算 | 独立 J 与 result.txt 一致 | PASS |
| 复算 | 统计窗 = 2592 步；诊断行数 = 步数+1 | PASS（12538 / 12537） |
| 复算 | 窗口 rel_std 与 acceptance 及原始诊断一致 | PASS |
| 复算 | 窗口 rel_span 与 acceptance 一致 | PASS |
| 几何 | fluid_nodes = 2064384 | PASS |
| 几何 | 边界 q 全 = 0.5 | PASS |
| 几何 | 无回退 / 无未解析链接 | PASS（0 / 0） |
| 数值 | 质量守恒 max < 1e-12 | PASS（4.39e-15） |
| 数值 | Mach < 0.05 | PASS（6.27e-9） |
| 执行 | exit_code=0 / 收敛 / 非超时 / 非资源停止 | PASS |
| 执行 | 输入闭包运行前后未变 | PASS |
| 验收 | BUILD_EQUIVALENCE_PASS（acceptance） | PASS |
| 验收 | 独立复算 K 与本机参照 ≤1e-6 | PASS（0） |
| 验收 | 正式回执 BUILD_EQUIVALENCE_PASS | PASS |
| 边界 | 未把构建等价误写为 S4 阶段接受 | PASS |

完整机器可读结果：`independent_recalculation.json`。

---

## 4. 实测开销（给 0.625 决策用的准数）

| 项目 | 数值 |
|---|---|
| 墙钟耗时 | 2:06:15（7575.4 s） |
| 峰值 RSS | 1,599,728 KiB ≈ **1.526 GiB** |
| 吞吐 | 1.655 步/秒（0.604 s/步） |
| 墙钟上限 | 21600 s（6 h），实际用了 35% |
| 交换分区 | 0 次 swap |

对比：0.625 nm 流体节点是 1.25 nm 的 **8 倍**（16,515,072 vs 2,064,384）；本机实测 0.625 **precheck 峰值 10.69 GiB**，服务器 126 GiB 可用内存无压力。

---

## 5. 能说什么 / 不能说什么

**能说（有本轮证据支撑）**

- 服务器 1.25 nm 结果与本机参照**逐位一致**，构建等价成立（判据在测量前冻结为 ≤1e-6）。
- 数值门槛、几何、质量守恒、边界审计独立复核全部通过。
- 这一档的真实开销（1.53 GiB / 2h06m / 1.655 步·s⁻¹）已实测，不是估算。
- 现在服务器构建的结果**有资格**与本机原始 5 / 2.5 nm 点配对。

**不能说**

- **不能说 S4 阶段通过**：`S4_stage_accepted=false`、`RESULT_PASS=false`、
  `reference_qualified=false`、`MODEL_COMPARISON / physical_validation = NOT_EVALUATED`。
- **不能说横槽网格已收敛**：中细差 1.328387% > 1% 的 FAIL 原样保留。
- **不能把"窗均值 K"当正式 K**：正式 K 取末步值；窗均值 3.47179256e-24 与末步差约
  2.1e-7 相对，仅作稳定性参考。

---

## 6. 证据清单（本目录）

| 文件 | 说明 |
|---|---|
| `independent_recheck.py` | 独立复算脚本（只读，可重跑） |
| `independent_recalculation.json` | 18 项核对的机器可读结果 |
| `server_evidence/result.txt` | 服务器原始结果 |
| `server_evidence/diagnostics.csv` | 完整诊断 12538 行（6.4 MB） |
| `server_evidence/acceptance.json` | 独立检查器验收回执 |
| `server_evidence/completion.json` | 完成回执（含输入/输出哈希） |
| `server_evidence/boundary_audit.txt` | 几何与边界审计 |
| `server_evidence/run.log` | 含 `/usr/bin/time -v` 峰值 RSS |
| `server_evidence/result_summary.csv` | 结果汇总 |
| `server_evidence/formal_run_record.json` | 正式运行回执 |
| `server_evidence/*_checker.log` | 独立检查器日志 |
| `server_evidence/frame_index.csv` / `frame_schedule.csv` | 场输出索引 |
| `server_evidence/execution_audit.txt` / `exit_code.txt` | 执行审计 |

---

## 7. 状态与下一步

- **状态**：1.25 nm 结果已整理、已独立复核、已归档。**本轮无新增计算或科学验收**。
- **0.625 nm**：用户已要求"在 55 上跑、结果暂不整理"。它仍需先完成 v2 合同手续
  （见 `docs/reports/URV_S4_TGE_server_closeout_pending_20261104_225446/` 与
  23:35 的 v2 结构说明），且 `check_formal_server.py` 的构建等价判据目前硬绑 1.25 run_id，
  需先理顺再启动。**尚未启动**。
- **S4 口径（路 A 收窄 / 路 B 补 0.625）**：留待导师拍板，冻结门槛与历史 FAIL 不变。

---

*本文为 AI 辅助的结果整理与独立复核，不替代人工科学终审。*
