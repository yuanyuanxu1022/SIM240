# S1 启动合同已签发：授权已记录，命令已交付，等待用户手动启动

日期：2026-11-02 11:30。**合同已签发并通过默认只读核对，但未执行、未启动任何计算。启动权在用户手上。**

## 1. 授权来源

用户在本轮交互中选择：“授权，两条都跑”，授权范围仅 `URV_S1_P_A1_v1_20261102_01` 与 `URV_S1_T_A1_v1_20261102_01`。

授权证据 `CASE/unseen_v2_reference_S1_a1_v1/evidence/S1_launch_authorization_A1_v1_20261102_01.json` 记录：用户原话、提问原文、先前指令原文、范围、以及 `AI_may_start_solver=false`、`user_manually_starts=true`、`automatic_retry_authorized=false`。

**必须如实保留的限制**：本次授权来自交互选项（`verbatim_recorded_from_typed_sentence=false`），不是用户手写整句。记录里同时保存了选项全文、提问原文与用户先前指令“取得 S1 授权后另存启动合同并交付单条 tmux 命令”，以便日后核对。若日后需要严格手写原话，可由用户另写一句替换该证据文件并重签合同。

## 2. 启动合同

`CASE/unseen_v2_reference_S1_a1_v1/evidence/S1_launch_release_A1_v1_20261102_01.json`

```text
SHA256 d15d044729fe398afcd6996346d7b260dd22a0930037da653d98e76ed5966d68
kind   AUTHORIZED_EXECUTION_LAUNCH_RELEASE
stage  S1_SMOOTH_THIN
simulation_authorized  true
inputs 1477 项
```

1477 = 准备合同 1473 + 零步审计 verification.json + 准备合同本身 + 其 .sha256 旁文件 + 授权证据。比上一轮预估的 1475 多 2 项，原因是同时收进了授权证据与其旁文件——与 S0 先例（1545→1548）的做法一致。

合同内含：provenance 六角色、资源合同（1 进程／1 线程／1 cuboid／overlap 3／8 GiB 地址空间／RAM≥12 GiB／首批盘≥100 GiB／每条≥8 GiB／每方向 14400 s）、零步审计绑定、`addendum_id=URV-S1-A1-v1`、两条精确身份、原 S1 验收门槛（K 与剖面相对 L2 各 <2%）、`next_stage_automatic=false`、`failed_case_automatic_retry=false`。

## 3. 只读核对（已实际执行）

```text
{"PREPARATION_BINDING_CHECK": true, "solver_executed": false,
 "simulation_authorized": true,
 "prepared_run_ids": ["URV_S1_P_A1_v1_20261102_01","URV_S1_T_A1_v1_20261102_01"],
 "resources_snapshot": {"MemAvailable_bytes": 22144049152, "disk_free_bytes": 341548318720}}
退出码 0
```

1477 项输入在执行前被逐项重新哈希，全部一致；两个 run 目录仍为净态；`launch_attempts` 目录不存在。合同 SHA 与旁文件一致。

**过程中遇到并解决的一个问题**：系统默认 `python3` 是 3.13 且无 numpy，直接跑会 `ModuleNotFoundError`。改用 S0 当轮实际使用的 `/home/dell/miniconda3/bin/python3`（3.14.7，numpy 2.5.3）后通过。启动命令已固定该解释器路径，避免用户执行时踩同一个坑。

## 4. 交付的启动命令

见 `START_COMMAND.txt`，一字不改地复制执行。会话名 `urv_s1_a1_v1_20261102_01`。

执行顺序由控制器强制：先 P（沿槽），原生退出 0 且原 URV 解析／数值／几何验收全部通过，才进入 T（横槽）；任一失败即停，无重试，不进入 S2。

## 5. 预期的资源与时间

每方向墙钟上限 14400 s（4 小时），两条合计上限约 8 小时——这是上限，不是预计耗时。S0 的 h75 两条实际分别为 43.1 s 与 30.9 s；S1 网格大得多（884736 节点 vs 57600，约 15 倍），但收敛窗更短（2592 步 vs 1013 步的统计窗，上限 27648 步 vs 58800 步）。实际耗时需跑起来才知道。

## 6. 状态

| 项 | 状态 |
|---|---|
| 启动合同 | 已签发，SHA `d15d0447…` |
| 默认只读核对 | 退出 0，未执行求解器 |
| 正式计算 | **未启动**，等待用户手动执行命令 |
| S1 NUMERICAL_GATE | NOT_EVALUATED |
| S1 geometry_PASS | null |
| S1 RESULT_PASS | false（未运行） |
| actual_formal_run_ids | [] |

`reference_qualified=false`、`strict_error_bound_established=false`、`submission_ready=false`、`MODEL_COMPARISON/physical_validation=NOT_EVALUATED`、`HISTORICAL_EXCLUSIVE_ATTRIBUTION=NOT_ESTABLISHED`、旧 v1.2 横槽 FAIL 与 380 项差异均保持。

本轮未编译、未调用求解器、未修改源码或规则、未改门槛、未提交推送、未外发资料。本记录为 AI 辅助证据，不是独立人工科学终审。
