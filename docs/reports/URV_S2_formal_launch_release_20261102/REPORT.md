# 正式 S2 完整六条：真实授权绑定与启动命令交付

2026-11-02。用户已回答：“现在采用并授权正式六条；生成合同和命令，由我手动启动”。本轮已完成新的正式执行合同、固定SHA及唯一命令文本，原检查器和正式授权验证通过；**没有执行启动命令、启动tmux任务或调用求解器。**

## 1. 真实授权与执行范围

真实授权文件 `CASE/unseen_v2_reference_S2_reuse_v1/evidence/S2_formal_authorization_reuse_v1_20261102_01.json`，SHA `17e8a36f86351bc143e9ca1a843be7f2448b7ea3e4d7ca844d9ab83f5bf00348`。如实记录完整交互问题、实际答复及questionItemId，authorization_source=reply_to_async_question、verbatim_recorded_from_typed_sentence=false；不把先前条件句写成授权。

用户采用S2-FRD-v1完整六条主方案：

|顺序|正式run_id|单条求解预算|
|---|---|---:|
|1|URV_S2_P_dx5_reuse_v1_20261102_01|3600秒|
|2|URV_S2_T_dx5_reuse_v1_20261102_01|3600秒|
|3|URV_S2_P_dx2p5_reuse_v1_20261102_01|14400秒|
|4|URV_S2_T_dx2p5_reuse_v1_20261102_01|14400秒|
|5|URV_S2_P_dx1p25_reuse_v1_20261102_01|43200秒|
|6|URV_S2_T_dx1p25_reuse_v1_20261102_01|43200秒|

U_REG h60/d80/w120/period240/Ly240nm，P沿槽+y、T横槽+x，a1e5m/s²、原单相/固定壁/平均/窗口/最大步/帧计划和科学阈值保持。每条独立验收通过才继续，失败即停，无自动重跑、加时或S3。第四条通过会直接进入第五条；用户已明确接受细格可能在12小时内未完成的风险。

34小时为六条求解预算之和；每条独立检查最多1小时，文件/清理/哈希另计，不是完成保证或严格40小时批次硬上限。现正式控制器没有PERF式连续RSS/MemAvailable/逐行安全扫描，覆盖边界以S2-FRD-v1为准；本轮没有追加监测功能或改源码。

## 2. 合同与来源闭包

正式release：`CASE/unseen_v2_reference_S2_reuse_v1/evidence/S2_formal_launch_release_reuse_v1_20261102_01.json`。

- kind=AUTHORIZED_EXECUTION_LAUNCH_RELEASE，schema=URV-EXEC-1.1，stage=S2_REG_GRID。
- SHA `2c0ed4c3c9d05178da160c2c2772ea8cee4ea03808ce7d765a19e3e3a86d1ad0`，**2140项输入**。
- simulation_authorized/formal_simulation_authorized=true，仅精确六条approved；AI_may_start_solver=false，user_manually_starts=true；native_zero_step/performance_time_stepping/S3/自动重试/自动加时许可false，actual_formal_run_ids=[]。
- 完整保留原B的1816项输入及B本身/真实SHA旁文件；另绑定PERF执行来源、已完成原始文件和独立复核、S2-FRD-v1/静态范围检查、绑定前核查、本次真实采用/授权与资源/库核查。原B不回写。
- B SHA `2e55f3369f9445e7763ee1f9a87c57f79348d1b332c959bc038c1bcc4739081f`、原ELF SHA `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`保持；2140项来源重哈希一致。

原runner.inspect、check_results.binding、validate_formal_authority均通过。默认只读入口实际退出0、PREPARATION_BINDING_CHECK=true、solver_executed=false、simulation_authorized=true；错误外部SHA被拒绝。没有执行--execute分支或调用原生程序，也没有重复49项既有软件检查/原生零步。证据 release_readonly.stdout.txt、release_verification.json。

## 3. 当前资源、目录与环境

22:08 +0800前置快照MemAvailable20342935552 bytes=18.94584GiB、磁盘341479403520 bytes=318.02748GiB，满足12/100GiB；随后默认只读入口再次通过前置资源校验，快照见release_readonly.stdout.txt。实际执行时仍会重查，不拿当前资源快照作全程保证。

六个正式目录均只有run_config.txt/run_manifest.txt，launch_attempts不存在，没有相关原生/正式控制器进程，目标会话未占用。命令在Python前使用env -u LD_LIBRARY_PATH -u LD_PRELOAD，单进程清理loader覆盖，不修改全局shell；15个动态库路径集合及逐项SHA与原构建一致。前置证据 precheck.json / precheck_after_correction.json、ldd_clean.txt / ldd_clean_after_correction.txt。

本轮文档生成第一次遇到校验旁文件名引用错误：误查preparation_B.json.sha256，实际原文件为preparation_B.sha256。记录binding_attempt_01.json保留；只修正本轮辅助绑定脚本，保留已记录真实授权、旧快照/封存/旁文件，不重复生成或覆盖。首次尚未写正式release、无求解器调用；随后只完成文档绑定，不是仿真重跑，也不是新的科学FAIL。

## 4. 唯一命令及结果入口

START_COMMAND.txt为本轮唯一交付命令，固定会话 `urv_s2_formal_reuse_v1_20261102_01`，显式携带正式release绝对路径和上述固定SHA；不是原PERF命令。命令仅生成并作文本解析核对，未交给shell/tmux执行。

父日志将写 `CASE/unseen_v2_reference_S2_reuse_v1/evidence/S2_formal_controller_reuse_v1_20261102_01.log`，本轮不存在。每条原始结果写其原净runs/<run_id>/steady，completion/真实退出/来源闭包保留；原独立检查写analysis_results/<run_id>。launch_attempts/<releaseSHA>记录批次尝试，失败即停。若启动后失败，保留现场，不重复命令/目录或自动生成新编号重跑。

原生result.txt中的RESULT_PASS=false与独立接受分开，不能手改。即使六条逐项接受，S2_completed也不意味着参考资格或模型比较通过；原aggregate要求24条，F04仍OPEN，不自动进入S3或评分V2。

## 5. 当前停点

本轮新增正式授权、release/旁SHA、本报告及唯一命令，维护共享状态/最新交接；3229项受保护旧文件未变，原代码/结果/门槛/封存不改。未构建、调用求解器/VTK读取器、推进、发信号、重跑、提交推送或对外发送。实际六条列表仍空；命令准备/交付不证明用户启动。

NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、REFERENCE_QUALIFIED_FOR_CASE=false，MODEL_COMPARISON/physical_validation=NOT_EVALUATED，reference_qualified/strict_error_bound_established/submission_ready=false；S0/S1接受、旧FAIL/380差异、MRP静态FAIL、HISTORICAL_EXCLUSIVE_ATTRIBUTION=NOT_ESTABLISHED、D4预测HOLD、F04 OPEN/外部声明范围保持。

下一动作：用户手动执行唯一命令，随后另启任务单次核查正式S2启动状态；不在本轮等待长计算、持续轮询或启动下一阶段。记录按scientific-writing证据约束组织，是AI辅助授权绑定，不是科学接受或人工终审。
