# 正式S4六条：真实授权、资源采用与独立执行绑定

签发后核对时间：2026-11-04T09:32:56.698455+08:00。结论：用户已明确采用S4-FRD-v1并授权完整六条，独立正式执行release已准备并通过只读验收，唯一命令见START_COMMAND.txt；**AI未执行该命令，正式计算未启动**。

## 1. 真实授权及采用来源

question_item_id：`["request_user_input_async","call_a2f8d135b2a942e78a70d8438206254e",0]`。用户实际选择：“现在采用并授权完整六条；生成合同和命令，由我手动启动”。完整问题与实际答复原样记录在/home/dell/yuanyuanxu/SIM240/CASE/unseen_v2_reference_S4_reuse_v1/evidence/S4_formal_launch_authorization_v1_20261104_01.json，SHA `172917cc1cfa97a8dc0b639d0f09320841ac0e22047e20650d342822903f4b3a`。

授权明确覆盖：采用S4-FRD-v1；5/2.5/1.25nm每档P→T六条；原1/4/12h逐条求解上限；每条外层标准独立检查（含保存场读回）1h；前条完整接受才继续，第四条后自动进细格；暂不另做PERF，接受细格12h可能超时而批次不完整；失败停、不重试/加时/进S5；AI只准备合同和命令、用户手动启动。求解34h、检查另最多6h，文件/清理另计，不保证40h完成。

授权来自实际选项答复，verbatim_recorded_from_typed_sentence=false；不伪造一段用户手写的扩展原话。此前“获得授权后”的条件指令与本次实际授权分别保留。原资源候选文件仍accepted=false不修改；本次另存真实采用记录/home/dell/yuanyuanxu/SIM240/CASE/unseen_v2_reference_S4_reuse_v1/evidence/S4_formal_resource_decision_v1_20261104_01.json，SHA `8be519f62fd48e48d59439a424353ecfd72d860d24ceae11336088ba031e05d1`。采用记录本身不是可执行release，正式权限由下述独立release承载。

## 2. 正式release及身份

路径：`/home/dell/yuanyuanxu/SIM240/CASE/unseen_v2_reference_S4_reuse_v1/evidence/S4_formal_launch_release_v1_20261104_01.json`；SHA256 `e5f7de1e584b776f8cc9bf1dbb31f198422ce10984ba8ad7d729220afdcdd19b`，输入3284项；kind=AUTHORIZED_EXECUTION_LAUNCH_RELEASE，stage=S4_THIN_GRID。release有独立.sha256侧文件，完整继承原B3248输入，并绑定B/侧文件、真实授权/采用、S4-FRD审查与新运行前核对等不可变证据。

|顺序|精确正式run_id|求解上限|独立检查外层等待|
|---:|---|---|---|
|1|`URV_S4_P_dx5_reuse_v1_20261103_01`|1h|1h|
|2|`URV_S4_T_dx5_reuse_v1_20261103_01`|1h|1h|
|3|`URV_S4_P_dx2p5_reuse_v1_20261103_01`|4h|1h|
|4|`URV_S4_T_dx2p5_reuse_v1_20261103_01`|4h|1h|
|5|`URV_S4_P_dx1p25_reuse_v1_20261103_01`|12h|1h|
|6|`URV_S4_T_dx1p25_reuse_v1_20261103_01`|12h|1h|

上述身份沿用原B，日期20261103不改，实际正式身份仍空。approved_runs/approved_run_ids精确同序六条；approved_audit_run_ids为空。原18个actual_audit及6初态读取是既有完成证据，不授权重做。

simulation_authorized/formal_simulation_authorized=true；native_zero/initial_field_readback/PERF/retry/extension/S5均false、AI_may_start_solver=false、user_manually_starts=true。零步专用initial_field_readback=false不排除本次真实正式授权内的标准检查器保存场读取。

## 3. 已完成运行前核对

- 原B SHA `7ca2ce3c27076a80d7d692bb13f3030854cf44b683dfe6bcec54ed15c288b06c`及3248输入不变，原18＋6收据、逐条原始文件/R1R2及完整独立接受文件核对通过。
- 真实B/来源/当前3284输入、formal_resource_decision门、formal授权、原科学checker binding均通过。默认run_S4只读CLI退出0、solver_executed=false、zero_audit_status=PASSED、精确六ID；受控检查子进程调用0。没有用已授权release的--execute做验证。
- formal release当zero、关闭B当formal、错误外部SHA均被拒绝；原3288项保护文件不变。包内只新增授权、资源采用、正式release及其侧文件4项，无源码、配置、门槛、旧合同改动。
- 同S1 ELF SHA `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`；OpenLB版本 `882924a9cfc8dcdf82909e39530789cb6f5ebcc4`。历史构建/1392依赖/3链接及15动态库来源保持，清除LD_LIBRARY_PATH/LD_PRELOAD后实际ldd解析15库路径/指纹与构建一致；未重新编译或调用原生程序。
- 最新签发前快照2026-11-04T09:30:26.915086+08:00：主机dell-OptiPlex-Tower-Plus-7010，可用RAM19.380GiB、盘317.527GiB，满足12/100GiB。无相关原生、URV控制器或场读取器进程，tmux无会话/目标会话；解释器、numpy及pvpython文件可用，未执行pvpython。此快照非资源预留，用户实际启动时控制器仍重查。
- 六正式目录均只含config/manifest；launch_attempts/analysis_results/新控制日志均不存在，无诊断/正式completion。不是“已启动”证据。
- 命令bash -n退出0，tmux参数和内层命令往返核对一致；活动控制日志未纳入不可变输入。START_COMMAND.txt是静态交付，没有运行tmux new-session。

## 4. 运行语义和限制

用户手动启动后：每条求解→completion/全过程原始证据→标准独立接受；任一门失败停，无自动重试/延时/续算。全部六条接受后才按原三网格规则评价P/T并写阶段汇总，网格不通过仍HOLD，不进入S5或V2比较。

1/4/12h为原生进程上限，初始化及输出在该进程内。独立检查外层1h，内部读取器1h含在其中；文件/指纹/网格汇总/清理另计，40h不是硬批次总时限。外层检查超时没有整棵读取器后代树统一清理保证；超时后保持HOLD，后续另做单次残留核查，不自动再起批次。S4持续性能/峰值RSS/收敛步数未知，S2条件估算不是完成保证，已在真实采用问题中明确接受细格超时风险。

控制日志`/home/dell/yuanyuanxu/SIM240/CASE/unseen_v2_reference_S4_reuse_v1/S4_formal_controller_v1_20261104_01.log`，会话`urv_s4_formal_v1_20261104_01`。唯一命令固定miniconda Python -B，子进程清除LD_LIBRARY_PATH/LD_PRELOAD，不改变全局环境。用户无输出返回提示符也不等同启动成功，不重复执行；下一任务按请求单次查会话、attempt、日志/已有回执，不持续轮询。

## 5. 当前科学状态与交接

正式NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false（尚未计算），reference_qualified=false，MODEL_COMPARISON/physical_validation=NOT_EVALUATED，strict_error_bound_established/submission_ready=false，F04 OPEN。S0–S3已接受、S4零步独立接受、旧FAIL/380项差异、MRP静态FAIL、旧v1 HOLD与历史唯一归因限制保持。原S2-LRP日志例外及上轮首份B错误候选原样保留，不重判或覆盖。

本轮实际新增原生调用0、VTK0、编译0、时间推进0，未启动性能或正式计算，没有源码/配置/门槛变更。新正式授权和合同不等于已执行；actual_formal_run_ids在签发时为空，不事后覆写签发合同。

证据：prebinding_verification.json、verification.json、clean_environment_ldd.txt、START_COMMAND.txt、protected_files_before.json、final_integrity.json和document_manifest.json。此前授权待确认的只读快照在docs/reports/URV_S4_formal_authorization_pending_20261104_092559，仅是确认前历史，不替代本次真实答复。

下一动作：用户在dell本地Linux终端手动执行START_COMMAND.txt唯一命令一次，贴回输出或报错；没有输出也说明。用户实际执行后，单次核查正式S4启动状态，不重跑、不持续轮询。命令交付后本任务停止。
