# S2 六配置原生零步：真实授权绑定与命令交付

日期：2026-11-02。结论：**A封存与资源只读核查通过，已取得明确授权，另存只允许18次原生零步及6次初态场实读的执行合同，命令已准备；没有启动。** 性能推进和正式计算继续关闭。

## 1. 真实授权及范围

用户最初消息为“取得六配置原生零步的明确授权后，核对 A 封存与资源，生成零步执行绑定并交付一条命令，由你手动启动；性能推进和正式计算保持未启动。”其中“取得授权后”与启动主体需要确认，未被写成已有授权。

随后向用户明确询问：“是否现在授权 S2 六配置的18次原生零步调用及6次初态场读取，只让我生成绑定合同和一条命令，由你本人在终端手动启动？这不包含性能推进或正式计算。”用户实际答复：**“现在授权；生成合同和命令，我本人手动启动”**。

授权证据保存上述完整问题和实际答复，注明来自对明确范围问题的真实用户回复，不伪造一段用户手写的独立完整授权句。user_manually_starts=true、AI_may_start_native=false。本轮仅签发绑定与交付命令，助手没有执行。

## 2. 封存与资源核对

- 原A封存：`CASE/unseen_v2_reference_S2_reuse_v1/evidence/preparation_A.json`，SHA256 `320d1d8469e2db50db161f91bca20339e60cb9054875722e9cbb50d9ab236e62`。1584项输入逐项核对，来源/真实构建闭包及原S0/S1前置证据通过；原A字节、许可关闭状态保持。
- 同一S1 ELF：`5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`，未构建或修改程序。
- 授权后检查可用内存21930479616 bytes（约20.42 GiB）、空闲磁盘341488254976 bytes（约318.04 GiB）；以 `authorized_release_check.json` 内的实际记录为准。原要求可用内存至少12 GiB、初始磁盘至少100 GiB；每条前至少8 GiB，进程地址空间8 GiB。实际启动前程序会重新核查，本次快照不保证未来资源不变。
- 六个正式准备目录和18个零步准备目录均仍只有配置/manifest；没有audit_attempts、launch_attempts、analysis_results或B封存。
- `/usr/bin/tmux` 与 `/usr/bin/pvpython` 文件存在；本轮没有执行字段读取器。目标tmux会话 `urv_s2_zero_20261102_01` 检查时不存在。

授权前只读快照在 `precheck.json`，`launch_plan.json` 是授权前关闭许可的历史方案，不是当前执行合同；授权后状态以真实合同和 `authorized_release_check.json` 为准。

## 3. 独立零步执行合同

授权证据：`CASE/unseen_v2_reference_S2_reuse_v1/evidence/S2_zero_authorization_reuse_v1_20261102_01.json`。

执行合同：`CASE/unseen_v2_reference_S2_reuse_v1/evidence/S2_zero_launch_release_reuse_v1_20261102_01.json`。

合同SHA256：`4b6759d061bc59079556c3a3b4bb34a7a8970b2f6529d4fa0cebeb1bdc1925c0`。

kind=AUTHORIZED_ZERO_STEP_AUDIT_RELEASE、stage=S2_REG_GRID、1586项输入（原A的1584项加A本身及真实授权文件）。native_zero_step_authorized=true；simulation_authorized=false、performance_time_stepping_authorized=false；正式approved_runs/approved_run_ids仍空。仅approved_audit_run_ids覆盖18条精确准备身份，实际audit/formal编号仍空。

范围是h60/d80/w120/P240/Ly240 nm，dx5/2.5/1.25 nm、P/T六配置各describe/precheck/initialize一次，另六个初态场实际读取。steady不在零步白名单，物理时间推进必须为0；每调用原生上限300s、每场实读上限300s，失败即停，不重试、不改门槛、不自动性能推进或正式求解。

## 4. 命令与实际只读验证

`START_COMMAND.txt` 保存唯一交付命令，绑定上述真实合同路径和完整外部SHA。命令由用户在本机Linux终端手动执行；助手未执行。它只启动audit_S2_zero.py，不自动封B、重跑或进入其他阶段。

外层shell启用noclobber，控制台日志写入 `CASE/unseen_v2_reference_S2_reuse_v1/evidence/S2_zero_console_reuse_v1_20261102_01.log`，避免重复命令覆盖同名日志。该日志尚不存在。每个原生子进程的run.log/独立exit和字段读取器记录由既有控制器保存。

实际只读验证已调用verify_seal、validate_zero_plan、validate_zero_authority及目录/资源守卫；Python入口不带execute，退出0，报告ZERO_PLAN_BINDING_CHECK=true、solver_executed=false、planned_native_calls=18、planned_initial_field_reads=6。shell只做 `bash -n` 语法核对，未执行tmux启动命令。完整记录在 `authorized_release_check.json`、release_readonly.stdout/stderr。

## 5. 当前科学状态与后续

原生调用0、字段读取调用0、时间推进0；S2 NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false、REFERENCE_QUALIFIED_FOR_CASE=false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED。B封存不存在。合同已签发/命令已交付不等于用户已启动或审计已通过。

用户执行后，按另起任务做单次启动状态核查；审计完成后再独立复核18次原生0步、六帧实读、哈希及退出证据，合格后才另存B。当前不等待、不轮询、不自动重跑、不启动性能或正式S2。原S0/S1接受事实、历史FAIL、F04 OPEN、作者外部声明范围及submission_ready=false保持。

本记录沿用scientific-writing的证据组织方式，技能方法引用见采用的S2-MIP-v1主协议末尾；AI核查不替代原生接入、数值验收或人工科学终审。当前状态和交接已同步，原状态副本保留本目录。
