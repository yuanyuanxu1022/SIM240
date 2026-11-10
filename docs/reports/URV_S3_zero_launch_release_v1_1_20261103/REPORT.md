# S3 v1.1 十二次零步及四次初态读取：独立执行绑定交付

核对时间：2026-11-03 13:26:47 +08:00。本轮仅根据真实授权生成合同、进行只读核对并交付用户手动命令。使用 scientific-writing 技能整理本地证据记录；不是人工科学终审。

用户实际选择“现在授权上述12＋4；生成合同和命令，由我手动启动”。授权证据完整保留原问题、选项原文及 questionItemId，明确这是交互选项答复，不冒充用户手写的展开长句。原问题明确 S3 v1.1、四配置各 describe/precheck/initialize 共12次、4次真实初态场读取、推进0步、失败即停不重试，只生成合同及一条用户手动命令，不含性能推进或正式计算。

## 绑定结论

独立合同：`/home/dell/yuanyuanxu/SIM240/CASE/unseen_v2_reference_S3_reuse_v1_1/evidence/S3_zero_launch_release_v1_1_20261103_01.json`

SHA256：`dbe8b8a4ee33806e7d7ceeeaea0ec76ad68985fbb51851bcb0d3cae7dbd28f42`。侧文件为同名 `.sha256`（替换 `.json` 后缀）。

审计身份：`URV_S3_ZERO_v1_1_20261103_01`；新增执行合同ID：`URV_S3_ZERO_LAUNCH_v1_1_20261103_01`。完整12个批准的零步run_id与4份读取计划见合同及真实授权文件；四条正式身份只是预留，approved_runs/approved_run_ids仍为空，不纳入本轮授权。

准备 A SHA `7f6ca19de96949a537802f92804c787cf092e8de0eb10c681ed279736a2d3695`及原2437项输入全部保留且未变化；新合同2451项输入逐项重哈希一致。新增14项只含原A/侧文件、真实授权、此前v1.1只读复核报告清单及其7个文件、本轮资源/依赖快照及生成脚本。旧A、旧v1的HOLD、原S2合同及原始结果不覆盖。2472份受保护文件前后指纹一致。

授权文件：`/home/dell/yuanyuanxu/SIM240/CASE/unseen_v2_reference_S3_reuse_v1_1/evidence/S3_zero_launch_authorization_v1_1_20261103_01.json`，SHA `001169bef5d3c7f71a2f5bc1d709fc2713fc2d0a5208f60b6098a0dec4925715`。

## 权限和调用范围

仅 native_zero_step_authorized=true；simulation_authorized、formal_simulation_authorized、performance_time_stepping_authorized=false。AI_may_start_solver=false、user_manually_starts=true；automatic_retry/extension与S4/S5权限均false。实际审计和正式run列表仍为空。

顺序为a50000/P、a50000/T、a200000/P、a200000/T；每配置依次describe→precheck→initialize，并读回各自初始化场。12次原生调用及4次读取每次上限均300秒；最大子进程超时预算合计80分钟，文件处理及核对另计，此数不是预计耗时，也不是批次硬总时限。每步失败即停，不重试，不进入steady、性能或后续阶段。初始化需要真实构造几何和导出初态，但collide_and_stream_calls必须0。

沿用原URV-v1/MRP/A1/S3物理、边界、平均定义、科学阈值及资源要求，不改变C++或限定指令结论。本轮没有构建或重做反汇编。原S1 ELF SHA `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`，OpenLB版本 `882924a9cfc8dcdf82909e39530789cb6f5ebcc4` 保持；净环境ldd解析15个动态库，路径和内容同原构建记录。

## 本轮只读核对证据

- verify_seal、来源链、S2两中档基准核对通过；新合同真实零步授权验证通过；正式授权验证明确拒绝该零步合同，错误外部SHA也被拒绝。
- 原准备A仍四权限全关闭。12零步目录及4正式目录只有配置与manifest；无audit_attempts/launch_attempts/analysis_results、零步verification或准备B。
- 实际默认零步入口不带execute，退出0；运行时拦截所有Popen，实际子进程创建0。输出ZERO_PLAN_BINDING_CHECK=true、solver_executed=false、planned_native_calls=12、planned_initial_field_reads=4、native_zero_step_authorized=true。
- 命令通过bash -n语法核对及shell参数往返检查；没有执行tmux命令。已有130项封存后测试及此前11探针的报告清单通过指纹核对，本轮不重跑测试。
- 资源检查于2026-11-03T13:24:36.393326+08:00：MemAvailable=19307630592字节（17.98GiB），可用盘=341194334208字节（317.76GiB），高于12/100GiB启动门槛。1进程/1线程/1cuboid/overlap3，8GiB单进程地址空间、逐条8GiB盘及4GiB输出预算保持。执行入口届时重新检查资源，快照不保证未来资源。
- 单次进程/会话快照未发现原生求解器或S3控制器，也无tmux会话；这不是用户启动后的核查。

本轮只新增3个CASE evidence文件（授权、独立执行合同、其SHA侧文件），本报告目录及共享状态维护；原源码、配置、原始结果和原准备A未改。原生求解器调用0、VTK读取器调用0、时间推进0、构建0；本轮ldd/tmux查询/bash语法进程为检查工具，不算作求解或场读取。

## 手动命令与停点

完整可复制命令在 `START_COMMAND.txt`，仅由用户在dell机器终端执行。会话 `urv_s3_zero_v1_1_20261103_01`；命令按固定SHA核对合同及输入，使用原miniconda解释器，并仅对子进程移除LD_LIBRARY_PATH/LD_PRELOAD，规避OpenFOAM库干扰，不修改全局环境。

控制日志：`/home/dell/yuanyuanxu/SIM240/CASE/unseen_v2_reference_S3_reuse_v1_1/S3_zero_controller_v1_1_20261103_01.log`。该日志当前不存在，不是绑定输入，不复用旧日志；原始每次退出/执行计数/配置/几何/帧读取保存在固定audit目录。执行时首次创建audit_attempts/<release SHA>，已用目录禁止重试。

命令已准备/交付不代表用户已启动。当前zero_audit_status=NOT_EXECUTED；准备B未创建；S3 NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false（尚未运行）；reference_qualified=false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED、submission_ready=false。原S2已验收结论、历史FAIL、作者声明范围、旧PERF日志例外及F04 OPEN均保持。

下一动作：用户手动执行这一条命令；若请求，可只做一次启动快照，不重跑或持续轮询。审计结束后另行独立复核真实12+4已有结果，合格才另存关闭权限的B；正式四条仍另行授权。

证据：verification.json、prebinding_verification.json、clean_environment_ldd.txt、protected_files_before.json、prepare_release.py、START_COMMAND.txt、final_integrity.json、report_manifest.json。同步入口为docs/reports/SIM240_AI_CONTEXT.md及AI_HANDOFF_20261015.md。
