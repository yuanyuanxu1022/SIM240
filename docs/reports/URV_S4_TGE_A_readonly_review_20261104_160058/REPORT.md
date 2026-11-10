# S4 TGE 准备 A、采用范围与3＋1资源提案只读复核

日期：2026-11-04T16:31:14.036298+08:00。用户要求仅只读复核，明确零步授权之后才核届时资源并生成独立执行绑定；性能/正式继续分别授权。此报告为AI辅助内部工作复核，不是原生审计、实际资源可行性证明或人工科学终审。

**结论：当前准备A的封存完整、单配置采用范围与实现一致，3＋1资源提案与现有零步入口相容，未发现需要改动准备包的阻断项。可以在用户明确授权该3＋1及采用资源方案后，进入届时封存/资源复核和独立绑定准备；当前尚未获得该授权，不签发执行release或启动命令。**

## 1. 封存、来源与原失败保留

A：`CASE/unseen_v2_reference_S4_tge_v1/evidence/preparation_A.json`，SHA `53e544543ae26402a0d0fac7a7b3294e0a2286e7a7d4c336ce08e91abf53bfb9`；独立sidecar一致。3695项输入逐项一致，本轮保护A/sidecar与全部先前准备报告后共3718文件内容前后不变；先前准备报告document_manifest全部核对。直接调用只读verify_seal/require_pristine，未执行控制器、未重跑15项软件测试、未调用原生或pvpython。

真实来源角色、构建捕获与同一S1 ELF SHA `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`一致；OpenLB `882924a9cfc8dcdf82909e39530789cb6f5ebcc4`及依赖/链接/动态库文件闭包通过。未重新编译、未运行原生加载审计，不将旧构建证据当新网格接入证据。

准备采用记录保留真实原话，仅授权隔离准备及必要软件检查。3＋1提案resource_decision_accepted=false/user_explicitly_authorized=false；A的全部执行flag=false，approved与actual列表空。原S4六条独立接受、P网格PASS、T中细1.328387035%>1% FAIL与S4_STAGE_ACCEPTED=false依旧原样绑定。原24点矩阵/资格/门槛未改。

## 2. 采用范围与目录

仅T/+x、dx0.625nm，h30/d80/w120/P=Ly240nm、平均H70nm、a100000m/s²、nu1e-6m²/s、tau1，静止无滑移、x/y周期、固定全充液；J按平面面积归一，K=nuJ/a（m³）、U=J/H。三零步模式仅改变mode/身份/输出目录，候选物理和观测参数相同。配置和基准引用已核对；没有混用沿槽/横槽或h/H。

|预留模式|run_id|本轮观察|
|---|---|---|
|steady|`URV_S4_T_dx0p625_TGE_v1_20261104_01`|仅配置与身份文件|
|describe|`ZERO_URV_S4_TGE_ZERO_v1_20261104_01_describe`|仅配置与身份文件|
|precheck|`ZERO_URV_S4_TGE_ZERO_v1_20261104_01_precheck`|仅配置与身份文件|
|initialize|`ZERO_URV_S4_TGE_ZERO_v1_20261104_01_initialize`|仅配置与身份文件|

4个目录均仅config/manifest；audit_attempts/launch_attempts不存在。没有新网格原生、初态、性能、正式或独立流场接受证据。这里只陈述包内文件状态，本轮未查实时进程。

旧T2.5/1.25nm仍由原S4正式release SHAe5f7de1e584b776f8cc9bf1dbb31f198422ce10984ba8ad7d729220afdcdd19b、各原completion/acceptance及raw闭包引用，新身份带SUPPLEMENT；未来新2.5/1.25/0.625nm不能覆盖原5/2.5/1.25nm失败。正式结果/资格/聚合控制器未实施，属于已限定的后续范围，不是本次3＋1前置缺失。

## 3. 3＋1资源方案与实际实现边界

|提案项目|值|本轮只读核对|
|---|---|---|
|原生模式与推进|describe→precheck→initialize各1次，推进0步|精确3身份及非steady模式校验，执行后原R1/R2核步数0|
|初态读取|initialize后读1场|固定原read_fields.py；按原始身份/初态/VTK闭包核对|
|时间|每次原生/读取各300s|控制器共用300s受限进程函数；失败即停|
|内存|每个受限进程地址空间8GiB|RLIMIT_AS，不是RSS或全部进程树总内存限制|
|可用内存前置|12GiB|批次和每次原生调用前检查；不能承诺全程空闲内存固定|
|空闲磁盘|批次100GiB、之后8GiB|调用前/运行间隔观察；不是磁盘预留|
|输出|4GiB|原生按各模式目录监控；读取器按整个audit目录监控，更保守|
|并发|1进程/1线程/1cuboid，overlap3|同ELF、配置和环境约束保持|
|失败后行为|立即停止、不重试、不转PERF/正式/S5|权限/净目录/单次attempt与控制路径相符|

300s是单次进程等待预算，终止/清理、哈希、文件核对另计；4×300s不是全批恰好20分钟的保证。8GiB地址空间不等于实测峰值、也不证明16515072节点及初态场读取一定装得下。若限时/内存/输出/磁盘失败，保留失败并停，不自动加时/加内存/重试。

候选自己的峰值RSS、持续速率仍未测；旧条件38.4537h仅成本缩放算术，不能挪为正式预算。这里只确认资源方案适合作为失败即停的受限零步尝试提案，不声称该尝试必定成功。原300s/8GiB资源提案尚未由用户采用，当前无资源执行权限。

按本轮要求，**没有重新检查当前RAM/磁盘或运行冲突**。先前资源快照时间2026-11-04T15:43:53.168249+08:00只作历史材料，不能充当授权后的启动前资源检查。

## 4. 权限与未来执行绑定条件

静态核对零步执行分支：任何输出或子进程前必须验证新zero-only授权、A继承/外部SHA、精确3身份、资源方案采用与净目录。准备A、旧S4六条授权不能启动该分支。固定读取器/原生身份与每次输入指纹核对保持，原始R1/R2及新3记录关联/清单复核存在。本轮未以execute参数做连通测试，也未伪造授权/资源采用文件。

已另存binding_plan.json，kind=NON_EXECUTABLE_ZERO_BINDING_PLAN_NOT_AUTHORIZATION；它不是release、不是命令，全部执行flag=false。未来真实授权至少须覆盖：新T0.625单配置3次原生零步＋1次真实初态读取、0步推进、上述300s/8GiB等限制、失败即停不重试、仅让AI生成合同/命令由用户本人手动启动、不含PERF/正式/S5。

授权到达后才做：重核A/3695项及source、届时RAM/磁盘和冲突、4净目录、新路径未用；另存实际用户授权与已采用资源决策，新zero release继承A全部输入并绑定A/sidecar/不可变审查证据。只记录实际回答，不把条件指令扩写成当前许可。实际新增输入数量待签发计算，不预填虚构值；未来活动控制日志不能纳入输入清单。新release只读/权限校验通过后先写交接，再交一条用户手动命令，AI不代启动。

## 5. 本轮停点

PREPARATION_A_READONLY_REVIEW_PASS=true；RESOURCE_PROPOSAL_STATIC_COMPATIBLE=true；ZERO_EXECUTION_AUTHORIZATION_RECEIVED=false；EXECUTION_RELEASE_CREATED=false；START_COMMAND_CREATED=false。CASE源码/配置/合同/结果修改0、构建0、软件测试重跑0、原生0、VTK0、PERF0、正式0；未自动升级B或进入S5。

reference_qualified=false、MODEL_COMPARISON/physical_validation未评价、strict_error_bound/submission_ready=false、F04 OPEN和全部历史FAIL保持。下一步为等待明确3＋1授权及资源采用；之后才复核届时状态、签发独立绑定和手动命令。已有准备授权无需再确认。

证据入口verification.json、protected_before.json、binding_plan.json；原A/提案/实现均未改。使用[peer-review](/home/dell/.codex/skills/peer-review/SKILL.md)，工具出处Kassis等(2026)，[Scientific Agent Skills](https://arxiv.org/abs/2609.00065)，同日先前公开元数据核对v2；仅工作流出处，无项目数据用于公开查询。内部AI复核不替代作者人工科学终审。
