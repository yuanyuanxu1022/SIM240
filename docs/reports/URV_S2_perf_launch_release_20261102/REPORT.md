# S2 两条有限性能推进：真实授权执行绑定与命令交付

日期：2026-11-02。本轮已收到明确交互答复：“现在授权两条有限性能推进；生成合同和命令，由我手动启动”。已按S2-MIP-v1-PERF生成独立性能release、完成来源/资源/环境及权限核对，并准备一条SHA绑定命令随本轮回复交付。**未执行命令，未启动求解器或tmux任务。**

## 1. 真实授权与身份

真实证据为 `CASE/unseen_v2_reference_S2_perf_v1/evidence/S2_perf_authorization_v1_20261102_01.json`，SHA `c2bd8766f0c98e2195031009186dba3fbb7d483cda95af0f843a1e692ae96efc`。如实记录 reply_to_async_question、完整提问和答复、原questionItemId，verbatim_recorded_from_typed_sentence=false；没有把条件句或选项答复改写成用户手写整句。

授权仅覆盖：

1. `URV_S2_PERF_P_dx1p25_v1_20261102_01`，沿槽+y。
2. `URV_S2_PERF_T_dx1p25_v1_20261102_01`，横槽+x；只有P独立性能检查证据充足且无异常才执行。

U_REG h60/d80/w120/period240/Ly240nm，dx1.25nm，2949120核心节点，原加速度/流体/平均/帧/10368步窗/602112最大步不改。每条启动起1800秒或首次观察完整diagnostics step≥2048，先到停止；SIGTERM后最多10秒，必要时SIGKILL。2048不是实际推进次数硬上限，缺失精确计数填null。无自动重试、延长、续跑或转正式。AI_may_start_native=false，用户手动启动；正式S2仍另行授权。

## 2. 合同与只读验证

执行合同 `CASE/unseen_v2_reference_S2_perf_v1/evidence/S2_perf_launch_release_v1_20261102_01.json`：

- kind=`AUTHORIZED_PERFORMANCE_RELEASE`，stage=`S2_PERFORMANCE_ONLY`，purpose=`S2_PERFORMANCE_NOT_REFERENCE`。
- SHA `b675010adcc9e57627d3ff39c93d72394e16489e3713abe09851d5de31c5c7e1`，2058项输入：原2055项+原准备文件+准备SHA旁文件+真实授权文件。
- performance_time_stepping_authorized=true；formal_simulation_authorized/simulation_authorized/native_zero_step_authorized=false；approved_benchmark仅上述两条，所有正式approved和actual列表空。
- 原准备封存SHA `806c40a62620396faf6795008a81b25f7f9bf4182869b6df4422b575b2b08030`、B SHA `2e55f3369f9445e7763ee1f9a87c57f79348d1b332c959bc038c1bcc4739081f` 和原ELF SHA `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`不改。

原封存检查器及新增authorize验证全部通过；默认只读控制器实际返回0、PREPARATION_BINDING_CHECK=true、solver_executed=false、性能许可true/正式许可false。错误外部SHA被拒绝。只读核对期间真实Popen禁止，没有进入执行分支。证据 release_readonly.stdout.txt、release_verification.json；本轮不重跑49项软件检查或原生零步。

## 3. 当前资源与环境

20:23 +0800快照：MemAvailable21431119872 bytes=19.95929GiB≥12GiB，磁盘341435523072 bytes=317.98661GiB≥100GiB；两条性能目录仍仅config/manifest，无performance_attempt/lock/batch结果、无相关原生或性能进程，目标tmux会话可用。执行时控制器会再次检查资源。

命令在启动Python前用 `env -u LD_LIBRARY_PATH -u LD_PRELOAD` 清除单进程loader覆盖，不更改用户shell配置。干净环境下ldd只读解析的15个动态库路径/逐项SHA与原构建记录一致，未运行求解器main。原资源1进程/1线程/1cuboid、overlap3、8GiB地址空间、12GiB可用内存、100/8GiB磁盘、4GiB输出不变。记录见 precheck.json、ldd_clean.txt。

## 4. 命令与输出入口

唯一启动命令见 START_COMMAND.txt；会话名 `urv_s2_perf_v1_20261102_01`。命令携带真实release绝对路径与固定SHA，代码没有读取旁文件临时替换SHA。整个命令只作文本生成/解析，没有交给shell或tmux执行。

父控制器日志将写 `CASE/unseen_v2_reference_S2_perf_v1/evidence/S2_perf_controller_v1_20261102_01.log`，本轮该文件尚不存在。每条原生run.log、diagnostics、原样保存场、performance_observations.csv、performance_receipt.json及独立performance_acceptance.json写入各自performance_runs/<ID>/steady。若用户启动后失败，保留现场，不重跑或挪用编号。

软件实现及假进程检查不等于真实原生性能验证。短段没有覆盖完整10368步统计窗成本，不能保证正式12小时内收敛；性能数据不进入参考资格、GCI或V2误差表。原生formal_simulation=true如出现仍原样保留，父合同正式许可false。

## 5. 停点与交接

本轮只新增授权/独立release/旁SHA、核查报告和命令文本，维护共享状态及最新交接；3126项受保护旧文件复核无漂移。没有改代码、构建、求解器/VTK读取器调用、时间推进、持续轮询、重跑、正式S2/S3、Git提交推送或对外发送项目材料。实际性能run_id列表为空；命令交付不证明用户已启动。

科学字段仍NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、REFERENCE_QUALIFIED_FOR_CASE=false，MODEL_COMPARISON/physical_validation=NOT_EVALUATED；reference_qualified/strict_error_bound_established/submission_ready=false。S0/S1接受、原横槽FAIL/380差异、早期MRP静态FAIL、HISTORICAL_EXCLUSIVE_ATTRIBUTION=NOT_ESTABLISHED、D4预测HOLD、F04 OPEN/外部声明范围等不变。

下一动作：用户手动执行START_COMMAND.txt中的一条命令；实际执行后另启任务单次核查启动状态，完成后另做已有性能结果分析，不自动进入正式计算。本报告按scientific-writing组织证据，属于AI辅助绑定记录，不是独立人工科学接受。
