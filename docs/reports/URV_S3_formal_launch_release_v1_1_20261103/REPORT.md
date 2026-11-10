# S3 v1.1 正式四条：真实授权绑定与用户手动命令交付

时间：2026-11-03 15:56:32 +08:00。结论：**已根据真实授权另存正式执行合同，封存/权限/资源和默认只读入口核对通过，交付一条用户手动启动命令；AI未执行启动，正式四条尚未运行。** 使用scientific-writing技能整理内部授权/证据记录，不代替人工科学终审。

## 1. 真实授权与采用范围

用户先给“获得明确授权后……”的条件指令，本轮随后对实际完整提问选择“现在采用并授权完整四条；生成合同和命令，由我手动启动”。授权证据完整保留提问和选择原文、questionItemId，verbatim_recorded_from_typed_sentence=false，明确来自交互选择，不冒充手写展开句。

提问明确采用S3-FRD-v1、低P→低T→高P→高T、每条4h求解/1h标准检查、前条完整验收通过才续行、第三条P线性门后才第四条、最后判T、16h+4h文件核对等另计非20h保证、任何失败即停、不重试/加时/性能或S4/S5，以及只生成合同命令由用户本人启动。标准独立检查含原保存场读取，不产生新零步权限。

授权文件：`/home/dell/yuanyuanxu/SIM240/CASE/unseen_v2_reference_S3_reuse_v1_1/evidence/S3_formal_launch_authorization_v1_1_20261103_01.json`，SHA `67ac9e56104f5ed02531b5d023a697642be0cfd32610a5d975d4b538f20d3017`。

采用的S3-FRD-v1协议：`/home/dell/yuanyuanxu/SIM240/docs/reports/URV_S3_formal_scope_review_20261103/PROTOCOL.md`，SHA `e2ddde0b4a1c5cf42447e8be80f6b8e9d78b952d890902bb41b1ea0ebecc9c8f`。原范围报告是授权前历史快照，保持原样，由本轮真实授权决定当前权限。

## 2. 新正式合同与原证据保留

合同：`/home/dell/yuanyuanxu/SIM240/CASE/unseen_v2_reference_S3_reuse_v1_1/evidence/S3_formal_launch_release_v1_1_20261103_01.json`

SHA256：`04836ee00515ac961f80022153eb398ea1692f03b943ca713e7414ce9716b574`，独立侧文件为同名`.sha256`（替换.json后缀）。release_id=URV_S3_FORMAL_LAUNCH_v1_1_20261103_01；kind=AUTHORIZED_EXECUTION_LAUNCH_RELEASE，stage=S3_REG_LINEARITY，addendum保持URV-S3-S1-ELF-REUSE-v1.1。

新合同2632项输入全部重哈希一致；继承B全部2609项，新增23项为B文件/侧文件、真实授权、S3-FRD-v1报告清单及其16份文件、本轮净环境依赖/资源前置记录与生成脚本。B SHA a5b69ec95180bf92327a3bba1311639dd2a5fb1bec412cd80c3869dda2a47f92不变，原A、零步release、真实12+4结果、完整独立复核及旧v1 HOLD均保留。2633份既有受保护文件前后不变。

simulation_authorized/formal_simulation_authorized=true仅适用于新正式release；native_zero_step_authorized/performance_time_stepping_authorized=false，approved_audit_run_ids空。原B及其所有执行权限仍false；不转移或覆盖原授权。12个actual_audit_run_ids保留，actual_formal_run_ids仍空，授权不等于运行完成。

## 3. 四身份、控制顺序与原门槛

|顺序|批准run_id|方向|a/(m/s²)|求解上限|
|---|---|---|---:|---|
|1|URV_S3_P_a50000_reuse_v1_1_20261103_01|P沿槽+y|50000|14400s|
|2|URV_S3_T_a50000_reuse_v1_1_20261103_01|T横槽+x|50000|14400s|
|3|URV_S3_P_a200000_reuse_v1_1_20261103_01|P沿槽+y|200000|14400s|
|4|URV_S3_T_a200000_reuse_v1_1_20261103_01|T横槽+x|200000|14400s|

原h60/d80/w120/周期Ly240nm、H100nm、dx2.5nm、rho1000/nu1e-6/tau1、368640节点、dt1.0416666666666667e-12s、2592窗/150528最大步、保存计划、边界/半步体力、J/K平均与原验收门不变。同一原S1 ELF SHA5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b和构建来源/OpenLB版本882924a9cfc8dcdf82909e39530789cb6f5ebcc4通过验证，没有修改C++、构建或扩大限定机器审计。

两个a100000中档依各自原S2合同只读引用，P K=5.919337058277595e-23、T K=2.3663885892433063e-23m³。它们未列入S3 approved，不重算/重绑。

标准流程为每条求解→原独立数值/几何/完整场验收全过→才下一条；第三条之后分别引用低/中/高沿槽K判跨度/均值≤0.001，失败不启动T高；第四条后同门判T。退出0或求解器自报PASS不能替代独立验收。任何失败、输入漂移、超时或资源停止即终止，不自动重试/加时/恢复/下一阶段。未放宽质量、Mach、密度、Re、收敛、几何/原始场或0.1%控制门。

## 4. 本轮实际核对

- 原B2609项闭包、原始零步总收据/R1/R2关联链和绑定独立验收通过；四正式目录保持只有配置/manifest。
- S3-FRD-v1完整报告清单和四身份一致；原S2双向中档原合同/配置/completion/接受/原始输出来源核对通过。
- 实际新release的verify_seal、validate_formal_authority、check_results.binding均通过；使用真实授权证据，没有模拟权限。各校验没有创建求解器或场读取进程。
- 默认正式入口不带execute，退出0：PREPARATION_BINDING_CHECK=true、simulation_authorized=true、zero_audit_status=PASSED、solver_executed=false，四身份正确。调用时拦截所有Popen，实际子进程创建0。
- 新正式release不能用作零步release、原关闭B不能用作正式release、错误外部SHA均被明确拒绝。
- 命令仅进行bash -n语法和shell参数往返核对，未执行tmux命令；无launch_attempts/analysis_results或正式控制日志。

资源前置快照2026-11-03T15:53:29.439605+08:00：可用内存20.09GiB、磁盘317.65GiB，达到12/100GiB门槛；默认入口稍后读取内存19.91GiB亦通过。未发现原生/S3/场读取进程或tmux会话。净环境ldd解析15项动态库，路径和内容与原构建记录一致。资源快照不保证未来资源，入口启动时重核。

预算沿用单条求解4h、标准检查外层1h；四条16h求解+另最多4h检查，文件/来源核对、停止清理另计。字段读取器内部1h在外层检查内，不再叠加。单进程线程、8GiB每受限进程地址空间、逐条盘8GiB/输出4GiB不变；既有超时进程树清理边界按S3-FRD-v1如实保留，超时HOLD后另查，不宣称严格20h总时限。无需新增PERF推进。

## 5. 手动命令和活动日志

命令在START_COMMAND.txt；用户在dell机器终端完整执行一次。会话`urv_s3_formal_v1_1_20261103_01`，固定新正式release SHA。使用原miniconda解释器及-B，仅对子进程移除LD_LIBRARY_PATH/LD_PRELOAD，避免OpenFOAM库路径干扰，不修改全局环境。

新控制日志：`/home/dell/yuanyuanxu/SIM240/CASE/unseen_v2_reference_S3_reuse_v1_1/S3_formal_controller_v1_1_20261103_01.log`。它目前不存在，也未列为不可变输入；不复用旧控制日志，不制造bound input drift。正式原始结果将在四个已冻结steady目录，逐条检查输出在analysis_results/<run_id>，进度/线性/完成记录在launch_attempts/<release SHA>。

命令已交付不等于用户已启动。正常后台启动可能无屏幕输出并立即返回提示符；只能在用户执行后另做一次状态核查，不能据提示符或tmux退出直接判完成。不持续轮询、不自动补跑。

## 6. 停点与接续

本轮只新增CASE evidence三份（真实授权、新正式合同、SHA侧文件）、本报告目录及共享进度/交接；原源码/配置/A/B/旧合同和原始结果未改。构建0、原生求解器0、VTK读取器0、时间推进0。四正式目录净，actual_formal_run_ids空；S3 NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false（未运行），S3_CONTROL_PASS=NOT_EVALUATED。

reference_qualified=false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED、strict_error_bound_established/submission_ready=false；旧v1 HOLD、历史横槽FAIL/380差异、MRP静态FAIL/历史唯一归因未建立、S0/S1/S2接受、F04 OPEN、PERF例外及作者声明范围均保持。正式授权不提升任何科学结果。

下一动作：用户手动执行唯一命令；实际执行后按请求单次核查启动状态。批次结束后另按原URV-v1/MRP/A1/S3 v1.1/S3-FRD-v1独立分析已有四条及两方向三档控制，不重跑、加时或进入S4/S5。启动状态建议GPT-6.1 Sol｜Low，完整结果验收High。

证据：prepare_release.py、prebinding_verification.json、clean_environment_ldd.txt、protected_files_before.json、verification.json、START_COMMAND.txt、final_integrity.json、report_manifest.json；共享入口docs/reports/SIM240_AI_CONTEXT.md和AI_HANDOFF_20261015.md。
