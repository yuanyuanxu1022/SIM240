# A1 两条 S0 正式启动绑定已交付准备，等待用户手动启动

本轮授权原话：“在授权 A1 的沿槽、横槽两条 S0，只让我生成正式合同和启动命令，由我手动运行”。根据前后对话，明确指A1沿槽P、横槽T两条S0，现在允许生成正式合同和一条命令，由用户手动运行。原话原字节保存，不把“在授权”擅自改写为用户另一句话；解释记录于独立authorization。AI没有启动权限，不自动重试或进入S1。

正式合同：`CASE/unseen_v2_reference_S0_mrp_v1_a1/evidence/S0_launch_release_A1_20261102_01.json`。
SHA256：`cf7f1aaccf22b8d47b0c81147b9f9dcb22d07615f45664b09c9f7d1347826148`。
授权证据：`CASE/unseen_v2_reference_S0_mrp_v1_a1/evidence/S0_launch_authorization_A1_20261102_01.json`。准备合同仍为d58019c2843454ce0ec1b2548e83fb6af66f4081d20acd54b695d665c916766c，原文件及关闭授权快照保持，未回写。

两条正式身份和配置保持：URV_S0_P_A1_20261102_01（P沿槽+y）、URV_S0_T_A1_20261102_01（T横槽+x）。h75/d100/w120/P=Ly240/dx5nm，rho1000kg/m³、nu1e-6m²/s、tau1、a1e5m/s²、H125nm；原J/K/U定义、边界、1013窗口／58800cap、保存计划和验收门槛保持。单进程／线程，每方向原生墙钟3600s、地址空间8GiB；P全部验收后才T。未启动、未取得新结果。

已完成的本轮检查：原1545项输入逐项相符；正式合同共1548项，新增本次授权和原准备合同／旁SHA绑定。完整来源、A1静态修订、6次原生零步和2初始化场读回、旧D4／v1.2基准、密度捕获规则不变。A1 ELF仍为c1fc2a1eeacced8f11a9bb045c25d70936b7be03fe5495a0b8f51789bd8fe8af。2033项既有保护文件不变。当前原检查器binding及控制器inspect均通过；实际默认CLI退出0，simulation_authorized=true、solver_executed=false。命令仅经bash -n及shell拆分核验，绝未执行。

本轮资源最新CLI快照：可用内存21.31GiB、磁盘318.26GiB，满足12／100GiB原门槛；控制器真实启动仍会自动重查。两steady目录均只有run_config.txt、run_manifest.txt，无launch_attempts或计算日志。命令保存在START_COMMAND.txt，固定session名urv_s0_a1_20261102_01、固定case目录、当前Python／控制器及上述合同SHA，交付后等待用户启动，不再次轮询。

执行链不变：P原生→捕获索引最终化→独立退出码与所有原始输出completion绑定→原URV验收＋独立密度重放／补偿账本／27项物理输出守卫→全部通过才T。任意失败、超时、来源漂移或资源不足立即停，不能重复执行同一命令来重跑；不自动进入S1。真实steady捕获／重放端到端尚未执行，原107项软件和10项控制器测试本轮未重跑；没有编译或源码修改。

当前S0仍HOLD_PENDING_FORMAL_REGRESSION_AND_REPLAY；NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null。授权和命令交付不是运行成功。旧v1.2 T拒绝／380差异／exit2和历史唯一归因NOT_ESTABLISHED保持；reference_qualified=false、strict_error_bound_established=false、submission_ready=false，物理验证／模型比较NOT_EVALUATED。S1未授权／未启动，F04范围外。没有新指令或证据矛盾，未新调用Astra；若出现沿用GPT-6 Astra｜High。没有提交推送。

科学写作技能用于证据组织；本记录是AI辅助核查，非独立人工科学签字。来源按本会话已核公开记录：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026), Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents, https://doi.org/10.48550/arXiv.2609.00065；只说明技能来源，不作为项目数值证据。没有外发项目资料。

后续：用户在本机终端执行唯一绑定命令。实际启动后另开任务单次检查状态；完成后按原URV-v1／MRP／A1分析现有结果，不重跑或自动进入S1。共享状态与最新交接已同步，原阶段准备快照不改。
