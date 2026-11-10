# 3＋1授权续接核对：既有合同已运行并失败停止，不交付重复启动命令

核对时间：2026-11-04T20:53:45.461714+08:00。本轮收到授权问答答复“现在授权3＋1并采用上述限制；生成合同和命令，由我手动启动”，随后用户要求继续。按项目当前证据查验时发现，工作区已经存在相同准备身份的独立绑定，且已有实际调用及失败记录；因此本轮转为核对已有授权/合同/原始记录，未覆盖旧绑定、未创建新尝试、未重发旧命令。

**结论：已有3＋1尝试在第2个原生调用precheck失败后停止。第1次describe完成；第3次initialize和初态场读取未执行。该审计未通过，不能形成准备B或开启PERF/正式/S5。现有路径不再满足净目录前置，原授权明确失败即停、不重试，不能把这次续接当成重试许可。**

## 1. 已有绑定与真实授权

合同 `CASE/unseen_v2_reference_S4_tge_v1/evidence/S4_TGE_zero_launch_release_v1_20261104_01.json`，SHA `d654196816e36fe97638c079c26a498e6203db8a01bd492042ecb1320c314949`，3710项输入本轮重核一致；A仍为53e544543ae26402a0d0fac7a7b3294e0a2286e7a7d4c336ce08e91abf53bfb9。原绑定记录见 `docs/reports/URV_S4_TGE_zero_binding_20261104_165506/REPORT.md`，原结果整理见 `docs/reports/URV_S4_TGE_zero_results_20261104_1719/REPORT.md`。

本轮用户原始问答封装另外保存为user_reply_evidence.json，含questionItemId `["request_user_input_async","call_9c20a0a182d04ff892e71a96a6616210",0]`；答案与已有授权记录完全相同，没有扩写成手写长句。已有授权文件中问题原文在“上限 8 GiB”处多一个空格，因此逐字问题匹配为false、去除空白后匹配为true；范围、数值、答复一致。这里只保存这一来源细节，不改旧授权，也不把本轮答复伪造成早前运行的独立时间戳证据。

当前许可是8GiB/300s/3＋1、失败即停、不重试、仅用户手动启动；并存S4T v0.2终审是针对未采用的后续资格/更大资源草案，不能用它静默提高本次内存或时限。新资格、整任务组内存方案和正式控制器仍待另定范围；本轮不做最终冻结或独立Astra签署声明。

## 2. 原始执行事实

|步骤|原始证据|判定|
|---|---|---|
|describe|独立退出0，耗时0.367478s，execution_audit记录collide_and_stream_calls=0|配置描述完成；不是几何/流场接受|
|precheck|独立退出−6，耗时10.417795s，timed_out=false、resource_stop_reason=null，日志std::bad_alloc/SIGABRT|调用失败，审计停止|
|initialize|目录仍只有run_config.txt和run_manifest.txt|未执行|
|初态场读取|无field_readback回执、无初始化场|未执行|
|正式steady|目录仍只有config/manifest|未执行|

已有结果报告的precheck日志、进程回执、控制日志副本与原始文件完全一致。原控制日志仅describe完成消息，随后 `EvidenceError: zero failed; no retry/next call`。audit_attempts中的该SHA标记目录已存在；仅progress/01.json，无整份verification.json。原生/控制器/相关读场进程本轮单次快照均无，原tmux会话不存在；之后不持续轮询。

值得精确记录：失败的precheck没有留下execution_audit.txt、result.txt或boundary_audit.txt。已核对源码的precheck分支在推进循环之前返回，支持“该模式不进入时间推进”的静态判断；但不能把缺失的实际执行计数文件写成已经读到一个0计数。该条实际几何/q接受仍未评价，geometry_PASS=null，不因静态预测或describe通过而改成true。

## 3. 内存失败能说明什么

直接观察到的是：同一封存二进制在采用的8GiB单进程RLIMIT_AS约束下，precheck出现std::bad_alloc并SIGABRT退出。未触发300s超时，回执没有控制器资源停止原因。这支持记录为受限接入中的内存申请失败，不能判为流场/公式物理失效。

仍未建立：实际峰值RSS、具体失败申请/缓冲区位置、最小所需地址空间、是否还存在其他宿主资源约束、整台机器在另一份已验证方案下是否可运行。故不把旧结果报告“8GiB不够”扩大成“已测需要十几到二十几GiB”或“本机一定不能跑”。地址空间上限和可用RAM属于不同指标，也不能简单相加推导硬件容量不足。新16/18/22GiB或48h数字都仍不是当前执行许可。

原结果报告提到0.9375nm作为中间候选也不能直接采用：80nm/0.9375nm=256/3，不满足当前解析器长度/网格比为整数的约束。若以后研究不同网格族，需要先审精确几何对齐及非原r=2规则；本轮没有选择或创建新网格。

## 4. 已知输出范围缺口与后续最小审查

运行日志证实OpenLB曾在进程cwd（CASE根）创建./tmp目录；当前零步控制器只观察模式输出目录，读取器观察audit目录，CASE根tmp未纳入4GiB观察范围。此次旧报告记录为空目录，不据此认定实际超出4GiB，但该监控范围缺口须在未来新准备中处理。旧现场与源文件全部保留，没有为恢复净目录而删除输出或attempt标记。

若用户另定失败后处置范围，最小后续是只读资源/输出审查：定位主要分配与进程树生命周期、列出地址空间/实际内存证据缺口、明确所有输出与临时目录计费、再提出隔离修订及候选资源规则。不能直接重跑旧3＋1、自动改8GiB为16GiB、清目录绕过一次性标记、修改网格/几何或进入PERF/正式/S5。需要新准备/新身份/新预算和新的重试执行许可时，分别明确后才能实施；已有授权无需重复询问，但它未覆盖失败后重试。

## 5. 本轮保护与交接

本轮3710项合同输入及共3739份受保护已有文件核对前后一致。没有CASE改动、编译、原生/VTK调用、软件测试重跑、性能推进、正式计算、新合同或启动命令。本轮只新增此报告目录、原始授权回执副本与只读核对记录，并同步共享状态。

原S4六条per-run接受/P网格PASS/T1.328387035%>1%网格FAIL/S4_STAGE_ACCEPTED=false保持；本次3＋1 ZERO_STEP_AUDIT_PASS=false，NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null。reference_qualified=false、MODEL_COMPARISON/physical_validation未评价、strict_error_bound/submission_ready=false、F04 OPEN及历史FAIL/声明范围均不变。

下一具体动作：另定“失败后资源与输出范围的只读补证/最小修订协议”范围；当前不签发重复命令、不改原包、不重试、不自动进入下一阶段。若进一步要求多线索根因裁决或最终资源规则终审，按项目偏好建议GPT-6 Astra｜High；本轮只是原始事实与范围续接核对，不声称该终审已完成。
