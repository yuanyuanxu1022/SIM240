# S4 单条横槽补证：3＋1 零步独立执行绑定与手动命令

签发：2026-11-04T16:56+08:00（本机 dell-OptiPlex-Tower-Plus-7010，Linux）。本轮按用户明确答复“现在授权3＋1并采用上述限制；生成合同和命令，由我手动启动”，重核准备 A 封存与当时资源，另存真实授权与资源采用，签发独立零步合同并准备一条手动命令。**未执行原生、未读场、未构建、未性能推进、未正式计算；也未创建 tmux 会话或运行带 --execute 的入口。**

**结论：合同已签发、只读校验全通过；但签发时刻的可用内存不满足你采用的 12 GiB 门槛（20 次采样中 19 次低于 12.00 GiB，区间 11.07–12.05 GiB），因此 RESOURCE_PRECONDITION_AT_ISSUANCE=NOT_MET。现在直接启动会在写任何文件之前被控制器拒绝并退出（不产生半截尝试、不占用量），所以请先跑检查命令，确认可用内存 ≥12.00 GiB 后再执行启动命令。**

## 1. 授权证据（逐字保存，不扩写）

- 完整问题：“准备 A 的只读复核已通过。是否现在授权 T／0.625 nm 的3次原生零步调用（describe、precheck、initialize，推进0步）及1次初态场读取，并采用以下限制：每次原生或读取最多300秒，每个受限进程地址空间上限 8 GiB，可用内存前置12 GiB，首批空闲磁盘100 GiB、之后8 GiB，单次输出上限4 GiB；失败即停、不重试？本次仅让我在重核封存和届时资源后生成独立合同与一条命令，由你本人手动启动；不包含性能推进、正式计算或S5。终止清理和文件核对另计。”
- 实际答复：“现在授权3＋1并采用上述限制；生成合同和命令，由我手动启动”
- 证据：`CASE/unseen_v2_reference_S4_tge_v1/evidence/S4_TGE_zero_authorization_v1_20261104_01.json`（SHA `928fcbef5e9d8643bae90bf6eeb7f07f1420a604226bebf9c425bb3dfda9fa18`），来源记为 `user_reply_to_request_user_input_async`，`verbatim_recorded_from_typed_sentence=false`，不把选项答复写成用户手工输入的扩展长句。
- 资源采用：`CASE/unseen_v2_reference_S4_tge_v1/evidence/S4_TGE_zero_resource_decision_v1_20261104_01.json`（SHA `622410fcc491ee37be3e07d2c85a15454fbea89b67377955fc01eae7af322044`），`resource_decision_accepted=true`，`resources` 与实现中的 `ZERO_RESOURCES` 完全一致。

## 2. 封存与净目录（签发前重核）

- 准备 A：`CASE/unseen_v2_reference_S4_tge_v1/evidence/preparation_A.json`，SHA `53e544543ae26402a0d0fac7a7b3294e0a2286e7a7d4c336ce08e91abf53bfb9`，与 sidecar 一致；3695 项输入逐项指纹一致；同源校验（同一个 S1 ELF `5c3836e9…b07b`、OpenLB `882924a9…bcc4`、依赖闭包）通过。
- 四个预留目录仍只有 `run_config.txt`、`run_manifest.txt`；`audit_attempts/`、`launch_attempts/`、控制器日志、零步 `verification.json` 均不存在。
- `solver_executed=false`、原生调用 0、VTK 0、软件测试未重跑、构建 0。

## 3. 新合同

- 路径：`CASE/unseen_v2_reference_S4_tge_v1/evidence/S4_TGE_zero_launch_release_v1_20261104_01.json`
- SHA256：`d654196816e36fe97638c079c26a498e6203db8a01bd492042ecb1320c314949`（外部独立 sidecar `.sha256` 另存）
- `kind=AUTHORIZED_S4_TGE_ZERO_RELEASE`；输入闭包 **3710 项** = 继承 A 的 3695 项 + 新增 15 项（A 与 sidecar、真实授权、资源采用、资源快照、环境 ldd、绑定生成器、8 份不可变只读复核证据）。实际项数由签发时计算，不预填估计值。
- 权限：`native_zero_step_authorized=true`、`initial_field_readback_authorized=true`；`simulation_authorized / formal_simulation_authorized / performance_time_stepping_authorized / automatic_retry / automatic_extension / S5` 全部 `false`；`approved_runs`、`approved_run_ids`、`actual_audit_run_ids`、`actual_formal_run_ids` 全空；`AI_may_start_solver=false`、`user_manually_starts=true`。
- 批准身份恰为 3 个零步 run_id（`…describe` / `…precheck` / `…initialize`，audit_id `URV_S4_TGE_ZERO_v1_20261104_01`）+ 1 次初态读回（`field_readback_URV1_U_THIN_T_dx0p625_a100000_SUPPLEMENT.json`），推进 0 步。
- 科学状态未升级：`NUMERICAL_GATE=NOT_EVALUATED`、`RESULT_PASS=false`、`geometry_PASS=null`、`reference_qualified=false`、`original_S4_stage_accepted=false`、`MODEL_COMPARISON/physical_validation=NOT_EVALUATED`、`submission_ready=false`、`next_stage_started=false`。

## 4. 只读校验（全部通过，未用 --execute）

| 检查 | 结果 |
|---|---|
| 外部 SHA 校验 `verify_seal` | 通过 |
| `validate_zero_authority` 精确 3＋1 | 通过 |
| 四预留目录净度 `require_pristine` | 通过 |
| 3710 项输入逐项未变 | 通过 |
| 错误外部 SHA 被拒 | 通过（按预期拒绝） |
| 该零步合同被正式 S4 权限校验拒绝 | 通过（按预期拒绝） |
| A 仍为无执行权限的封存 | 通过（SHA 未变） |
| 无 `audit_attempts`、无零步回执、无控制器日志 | 通过 |
| 真实默认入口（无 --execute） | 退出 0，`binding_check=true`、`solver_executed=false`、计划 3 次零步 / 1 次读回、节点 16515072、dt 6.510416666666667e-14 s |

## 5. 届时资源（事实，不是预留）

- 采样时间 16:52–16:57。可用内存 **11.07–12.05 GiB**（20 次采样，19 次 <12.00 GiB）：`12.045, 11.667, 11.548, 11.461, 11.837, 11.808, 11.212, 11.202, 11.249, 11.376, 11.222, 11.229, 11.222, 11.132, 11.816, 11.646, 11.827, 11.661, 11.069, 11.180`。
- 空闲磁盘 316.17 GiB（门槛：首批 100 GiB）；load average 约 2.5（24 核）；未发现 `urv`／`pvpython`／`paraview` 求解或读场进程；tmux 无 server（无会话）。
- 因此 `memory_floor_met_now=false`、`RESOURCE_PRECONDITION_AT_ISSUANCE=NOT_MET`。这项是**签发时刻事实**，不构成预留，也不代表你启动那一刻的数值；控制器在批次开始和每次原生调用前都会重新检查，不满足即停。
- 未能核对的是候选自身的峰值 RSS 与持续速度；8 GiB 是 `RLIMIT_AS`（单进程地址空间），不等于实测峰值，也不证明 16515072 节点加初态场读取一定装得下。旧 38.4537 h 只是成本缩放算术，不作正式预算。

## 6. 交付的命令（未执行）

- 检查命令：`CHECK_BEFORE_START.txt`（只读，显示可用内存与磁盘）。
- 启动命令：`START_COMMAND.txt`，唯一一条 `tmux new-session`，参数经安全引用、`bash -n` 语法通过、参数往返一致；会话名 `urv_s4_tge_zero_v1_20261104_01`；控制器日志 `CASE/unseen_v2_reference_S4_tge_v1/S4_TGE_zero_controller_v1_20261104_01.log`（活动日志不进不可变输入，避免日志增长造成 bound input drift）。
- 本轮**没有**执行这条命令，没有创建会话、没有日志、没有尝试目录、没有原生输出与读回。命令已准备 ≠ 已启动 ≠ 已完成。

## 7. 使用与边界

1. 在 dell 这台机器本地终端先执行检查命令；只有可用内存 ≥12.00 GiB（且磁盘 ≥100 GiB）才执行启动命令。
2. 若内存不足仍执行，控制器会在写任何文件前退出 2，日志里出现 `available memory below adopted 12GiB zero limit`；此时**不要反复重跑**，先释放内存再试。
3. 启动后 tmux 在后台运行，终端回到提示符本身不是启动或完成证据；把终端完整输出贴回，由下一轮单次查状态。
4. 失败即停、不重试、不加时、不加内存、不转 PERF／正式／S5；终止清理与文件核对另计，4×300 s 不是整批完成时长保证。
5. 3＋1 结束后必须另行独立复核（`analysis/check_zero_tge.py`）后才谈准备 B；本轮不授权、不预判结果。

## 8. 未改变的状态

原 S4 六条 per-run 接受、P 网格 PASS、T 中细差 1.328387035% >1% FAIL、`S4_STAGE_ACCEPTED=false`、`reference_qualified=false`、`MODEL_COMPARISON/physical_validation` 未评价、`strict_error_bound/submission_ready=false`、F04 OPEN 及全部历史 FAIL、作者声明范围、被拒 B、旧 v1 HOLD 一律保持。CASE 源码/配置/科学阈值/结果未改；未提交、未推送。

证据入口：`build_summary.json`、`validation_readonly.json`、`resource_snapshot.json`、`memory_samples.json`、`native_ldd_at_issuance.txt`、`START_COMMAND.txt`、`CHECK_BEFORE_START.txt`、`verification.json`、`document_manifest.json`。

本报告为 AI 辅助整理，不替代作者人工科学终审；不声称模型切换或独立人工审稿。
