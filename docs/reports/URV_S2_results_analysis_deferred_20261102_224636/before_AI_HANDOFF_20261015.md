# SIM240 项目 — AI 交接摘要（任何 AI 工具进入项目先读）

## 新绑定正式 S2 已启动；快照时完成前两条、正在第三条（2026-11-02 22:44:50 +08:00）

用户本轮授权仅单次启动状态核查，不重跑、不持续轮询。证据入口 `docs/reports/URV_S2_LRP_startup_check_20261102_224450/snapshot.json`、REPORT.md。

已确认新会话 urv_s2_formal_lrp_v1_20261102_02 存在；控制器PID780296绑定新release SHA d08297ebda69d9698d40762f778eb43299fa3c01c35e5591b6d31b4e06ef26cd，原生PID781184正在URV_S2_P_dx2p5_reuse_v1_20261102_01（2.5nm沿槽P）。该次快照最后已落盘完整诊断step460，不等同精确当前调用数或完成进度百分比。

5nm沿槽P与横槽T均已有completion和独立acceptance：原生独立退出0，无超时/资源停止，inputs_unchanged=true；自动独立检查器NUMERICAL_GATE=PASS、geometry_PASS=true、RESULT_PASS=true，检查器退出0。P3328步/约27.27s，T1940步/约16.47s。这里只记录已有接受文件，不替代本轮之后对整批的独立完整分析；原生result中RESULT_PASS=false是原设计待独立接受字段，不是新矛盾。

2.5nm横槽与1.25nm两方向仍只有配置/manifest，未启动。六条总体为已完成并获自动接受2、运行中1、尚未启动3。新控制日志存在且快照时为空；实际会话/原生进程/诊断和前两条接受证明已进入正式计算，不能按日志为空判未启动。正式launch_attempts新SHA目录已有两条检查器日志。

本轮不重新哈希2160项输入、不做全轨迹科学验收、不新增计算/重跑、不修改CASE/绑定/门槛、不控制或终止任务。仅新增本快照报告并更新共享状态。原PERF日志例外及旧正式拒绝均保留。

下一步：保持本批按既有六条授权和失败即停控制器运行；结束后由用户另发完整分析请求，按URV-v1/MRP/A1/S2-MIP-v1/S2-LRP-v1核对所有已有结果。不得自动重跑、加时或进入S3。参考资格false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED、历史FAIL及F04 OPEN不因本次启动核查升级。当前快照不预测结束时间。

## S1 合同已签、命令已交付、等待用户手动启动（2026-11-02 11:30，已被上节完成）

- **接手先读本节**。用户已授权两条 S1 身份；启动合同已签、默认只读核对退出 0，但**求解器未执行**、`actual_formal_run_ids=[]`。入口 `docs/reports/URV_S1_launch_release_20261102/REPORT.md`、`START_COMMAND.txt`。
- 合同 `CASE/unseen_v2_reference_S1_a1_v1/evidence/S1_launch_release_A1_v1_20261102_01.json`，SHA `d15d044729fe398afcd6996346d7b260dd22a0930037da653d98e76ed5966d68`，kind=AUTHORIZED_EXECUTION_LAUNCH_RELEASE、stage=S1_SMOOTH_THIN、inputs **1477 项**（准备 1473＋零步审计＋准备合同＋旁文件＋授权证据）。授权证据 `evidence/S1_launch_authorization_A1_v1_20261102_01.json`，`AI_may_start_solver=false`、`user_manually_starts=true`、`automatic_retry_authorized=false`。
- 授权来自交互选项（`verbatim_recorded_from_typed_sentence=false`），非手写整句；证据同存选项全文、提问原文与先前指令。需严格手写原话时可另写替换并重签。
- 只读核对实测：`PREPARATION_BINDING_CHECK=true`、`solver_executed=false`、两条身份正确、RAM 22144049152 bytes、disk 341548318720 bytes、退出 0；1477 项逐项重哈希一致；两 run 目录净；`launch_attempts` 不存在。
- **环境坑**：默认 `python3`（3.13）无 numpy，会 `ModuleNotFoundError`；必须 `/home/dell/miniconda3/bin/python3`（3.14.7／numpy 2.5.3）。命令已固定该路径。
- 启动命令在 `START_COMMAND.txt`（会话 `urv_s1_a1_v1_20261102_01`）；控制器强制 P→原 URV 验收全过→才 T，失败即停、无重试、不进 S2。每方向 14400 s，两条上限约 8 h（上限非预计）。
- 状态：S1 NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false（未运行）；S2–S5 未启动；reference_qualified=false、strict_error_bound_established=false、submission_ready=false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED、HISTORICAL_EXCLUSIVE_ATTRIBUTION=NOT_ESTABLISHED、旧 v1.2 横槽 FAIL／380 差异、前 MRP 静态 FAIL 均保持；F04 OPEN。
- 下一动作：用户手动执行那条命令；跑完后另启任务做验收。助手不代执行、不轮询。常规 GPT-6.1 Sol｜High；新指令或证据矛盾按用户指定 GPT-6 Astra｜High 裁定。

## S0 已通过、S1 建成待授权（2026-11-02 11:13 状态补齐，已被上节推进）

- **接手先读本节**。本节据 10:01—10:35 实际产物补齐；其下“S1运行前材料审查…不能直接接入／未构建”与更早“A1启动绑定…待明确正式授权”两节为历史快照，已被本节覆盖，证据与限制未删改。
- **S0 已验收通过**：`URV_S0_P_A1_20261102_01`（沿槽+y）4342 步／4343 行、`URV_S0_T_A1_20261102_01`（横槽+x）2953 步／2954 行；原 20 列与旧 D4 精确相同（145940 值）、5 个修正账本列与 v1.2 相同（36485 值）；NUMERICAL_GATE=PASS、geometry_PASS=true、原 URV_RESULT_PASS=true、专项 RESULT_PASS=true；K 独立复算 P 9.834076003216203e-23 m³／T 4.449022023188299e-23 m³；212 份密度重放重现 T 190 点 380 项差异（首差 step11、最大差 step1141 有符号 −7.395570986446986e-32 kg）；S0_REVISION_DISPOSITION=ACCEPTED_NEW_A1_PAIR。入口 `docs/reports/URV_A1_S0_results_review_20261102/REPORT.md`、disposition.json、numerical_gates.csv、T_same_density_replay_190.csv、T_380_entry_reconstruction.csv。S0 合同 SHA `cf7f1aaccf22b8d47b0c81147b9f9dcb22d07615f45664b09c9f7d1347826148`，A1 ELF `c1fc2a1eeacced8f11a9bb045c25d70936b7be03fe5495a0b8f51789bd8fe8af`。
- **S1 已建成、零步通过、正式未跑**：`CASE/unseen_v2_reference_S1_a1_v1/`（src/build/runs/scripts/evidence/audits）＋`CASE/unseen_v2_reference_checker_S1_a1_v1/`（revision、s1_revision、tests）。相对 A1 仅删 S0 密度捕获 6 行使能、2 处 measure 参数置空（`adopted_source_delta.patch`），其余源／header／Makefile 字节保持。新 ELF `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`，`compile_exit_code=0`。
- 验证范围：检查器既有 **42 项**＋S1 新增 **20 项**软件测试分开通过；884736 空间前缀体积差异 0（软件算术）；限定 `SOURCE_REVISION_AUDIT=PASS`（三次舍入乘 0x2edc4/0x2edd4/0x2ede4、最终显式 FMA 0x2edf4、体积独立加 0x3ff71、26 内核序列同 A1），不主张完整传递机器等价。两方向零步 `URV_S1_ZERO_20261102_01`：6 次调用全退出 0、推进 0 步、steady 0；884736 节点、368640 壁面链、q=0.5、material 0/884736/36864/147456、fallback=unresolved=0；legacy 初态质量 1.7280000000210298e-18 kg、补偿 1.7280000000000002e-18 kg、体积 1.7279999999935988e-21 m³、初始 J 3.906249999932872e-16 m²/s（半步力修正）、Mach 4.6984885187957832e-12；两帧初始化场独立读回通过。
- 已准备身份 `URV_S1_P_A1_v1_20261102_01`／`URV_S1_T_A1_v1_20261102_01`，`preparation_manifest.json` kind=S1_PREPARATION_NOT_AUTHORIZATION、simulation_authorized=false、1473 项输入；两 run 目录仅 run_config.txt／run_manifest.txt。`scripts/run_S1.py` 默认只读，准备合同在 binding 处拒绝执行；旧 S0 许可不可挪用；S1 每方向 14400 s、地址空间 8 GiB、RAM≥12 GiB、盘≥100/8 GiB、输出预算 4 GiB。
- 状态边界：S1 NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false（未运行非失败）；`density_capture=NOT_APPLICABLE_S0_ONLY`；S2–S5（20 项）与模型比较未启动。旧 v1.2 T RESULT_PASS=false／exit2／380 项差异、前 MRP 静态 FAIL、HISTORICAL_EXCLUSIVE_ATTRIBUTION=NOT_ESTABLISHED 全部保留；reference_qualified=false、strict_error_bound_established=false、submission_ready=false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED。F04 跨阶段汇总仍 OPEN。
- 下一具体动作：用户明确授权两条 S1 身份后，复核 1473 项封存与当时资源→另存带授权原话的启动合同并验独立 SHA→交付一条 SHA 绑定 tmux 命令由用户手动启动→P 跑完后原 URV 解析/数值/几何验收全过才 T，失败即停、不重试、不进 S2。当前无启动命令，不自动启动。常规 GPT-6.1 Sol｜High；新指令或证据矛盾按用户指定 GPT-6 Astra｜High 裁定。本轮为状态补齐：未编译、未调用原生、未求解、未提交推送、未外发资料。
- **11:24 启动前只读复核与方案准备已完成**：`docs/reports/URV_S1_launch_plan_20261102/`（REPORT.md、launch_release_plan.json、verification.json）。1473 项输入缺失 0／变化 0；ELF 与零步审计同源；两 run 目录净；`launch_attempts` 不存在；RAM 20.67 GiB、盘 318.10 GiB 过门槛；tmux／进程均 0。**关键坑**：准备合同不含零步审计与准备合同自身，而 `run_S1.py` 第 58–63 行要求启动合同 `inputs_sha256` 收进零步审计，否则 `zero audit not bound`；S1 启动合同应为 **1475 项**。方案仍 `authorized=false`、未签发合同、未生成命令。

## S1运行前材料审查完成：原输入静态一致，现A1执行包不能直接接入；未构建／未启动（2026-11-02，历史快照，已被上节覆盖）

- 用户本轮仅要求“另定范围后，审核 S1 光滑基准的运行前材料与合同兼容性”，据原URV-v1审查S1两条，不含新实现／编译／原生零步或正式计算。入口docs/reports/URV_S1_prerun_review_20261102/REPORT.md、scope_review.json、reviewed_inputs.csv、static_geometry_and_analytics.json、compatibility_findings.json、MINIMUM_ADAPTATION_DRAFT.md与verification.json。草案未采用／实现，不是启动许可。
- 两条planned_case_id仍URV1_SMOOTH_H30_P_dx1p25_a100000／URV1_SMOOTH_H30_T_dx1p25_a100000，实际run_id空；h30/d0、Lx=Ly240、dx1.25nm、rho1000、nu1e-6、a1e5、tau1，P+y／T+x。纯有理数／NumPy静态枚举核对884736核心节点、368640壁面链、q.5、dt2.604166666666667e-13s、2592窗口／27648cap；解析K2.25e-24m³、J2.25e-13m²/s、U7.5e-6m/s。原K/剖面相对L2各严格<2%及全数值／几何门槛保持。以上是运行前预期，不是S1几何／流场PASS。
- 当前S0/A1直接启动不兼容：C01原生steady无条件构建57600节点h75捕获器，与S1884736冲突；C02来源修订仅S0；C03控制器固定S0身份/3600s，原S1每方向14400s；C04映射/5nm/190点历史和11/201份捕获专用h75；C05当前URV准备链尚无S1候选／构建／原生安装和初始化／执行绑定。源码定位和SHA已保存；这些是预期阶段边界，未发生新证据矛盾，无新Astra调用。
- 草案建议新隔离S1候选保留A1旧质量helper、补偿列与体积舍入；S1不调用h75捕获器，使用既有null捕获测量路径，原S1按原URV解析/数值规则验收。h75历史重放不适用S1，不虚填PASS或放宽原数值门。需新精确来源anchor与仅两条S1的控制器，旧S0源码／许可／捕获／回执不改；原check_results/evidence/read_fields/科学规则保持。未来构建／限定指令审计／软件及两方向原生零步须另明确准备范围，正式许可最后单独办理。
- 原资源保持：1进程/线程/cuboid、overlap3、地址空间8GiB、可用RAM≥12GiB、首批盘≥100GiB/每条≥8GiB、每条输出4GiB预算；S1每方向14400s。单份核心D3Q19数组128.25MiB不是峰值内存；实际资源与原生S1仍待。A1体积表达式在S1尺寸下纯算术相对差3.7047663623415744e-12，原1e-10内；不能代替原生几何审计。
- S0_ACCEPTED_NEW_A1_PAIR保持：URV_S0_P/T_A1_20261102_01分别4342/2953步、4343/2954行，原20列精确回归、补偿守卫、212份密度重放、190点/380项再现、20实际场读回和物理输出均通过；详见URV_A1_S0_results_review_20261102/REPORT.md、disposition.json。正式S0合同SHA cf7f1aaccf22b8d47b0c81147b9f9dcb22d07615f45664b09c9f7d1347826148、A1 ELF c1fc2a1eeacced8f11a9bb045c25d70936b7be03fe5495a0b8f51789bd8fe8af均保持。2399项保护文件前后不变，无CASE／源码／合同／规则修改，无构建或原生调用。
- S1_RUN_READINESS=NOT_READY_STAGE_ADAPTATION_REQUIRED，simulation_authorized=false、S1未启动；NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false（未接受而非已运行失败）、geometry_PASS=null。旧v1.2 T拒绝/380差异/exit2和前MRP静态FAIL不改；HISTORICAL_EXCLUSIVE_ATTRIBUTION=NOT_ESTABLISHED，reference_qualified=false、strict_error_bound_established=false、submission_ready=false，MODEL_COMPARISON/physical_validation=NOT_EVALUATED。旧细T、C/h75、V2/G4、D4预测HOLD、旧N8 D4_N8_diag_v3_1_20261026_v1、GDI01和外部声明范围不变。F04跨阶段汇总仍OPEN，后续需按各条独立合同SHA，不阻单批S1验收。
- 当前审查任务完成。下一具体动作：采用MINIMUM_ADAPTATION_DRAFT后，在新隔离副本实现S1接入及来源／运行层，完成构建／软件／限定指令审计和明确包含的双向原生零步；保持正式计算另授权、不默认重跑S0或进入S2。建议GPT-6.1 Sol｜High；新指令或证据矛盾按用户指定GPT-6 Astra｜High裁定。没有启动命令、提交推送或项目资料外发。

## 微信目录Ban博士论文与Jain JVST2017接收停点（2026-10-29）

- 用户补充两精确文件名，已核实际PDF并存`docs/reports/Ban_Jain_received_20261029/REPORT.md`、intake.json、sources/及提取文本。Ban=Yang Hun Ban2021、UT Austin博士论文154页；011602=Jain/Spann/Bonnecaze，JVST B35,011602(2017)，DOI10.1116/1.4971771，13页含封面。均非佳能公司署名论文，也未据此确认老师“TAN木”。Ban与下载版同字节；原件不改。
- 已读身份/目录、Jain相关引言、011602-3—4方法与文末参考文献，目视Ban标题及Jain标题/方法页；未全审154页或全部结果图。方法给出压力—力平衡调模板速度—界面推进的过程连接；验证陈述对照Reddy/Bonnecaze[22]既有模拟，不升级为实验或本项目修正验证。Jain[39]确含H.Tan，仅名称线索。本次JVST文与正式稿[1]Jain MEE2017、DOI10.1016/j.mee.2017.04.001明确不同。
- 既有推荐主目标R_sq=F_net/V保持，未冻结/实现；下一具体动作核Ban§3.2与本项目K的单位/平均定义接口，补瞬时挤压边界、净力口径、合格独立参照/资源清单。不能直接称动态填充性能闭环；完整界面/气体/运动范围另定。
- 本轮只资料接收/方法核对与状态维护；无新增计算或数值/物理验证，无编译/求解/拟合/真实N8提取/新run_id/下一Gate/提交推送/长算授权。旧D4_N8_diag_v3_1_20261026_v1，NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD及历史FAIL保持。常规核对GPT-6.1 Sol｜High，理论最终冻结另按Astra建议。

## “TAN木”另篇文献消歧：已有候选，尚未确认（2026-10-29）

- 用户明确“还有一篇TAN木的文献”并要求查找，不能继续把它视作Ban。已查下载文件名/相关本地记录、Seki参考文献并做Tan/Tanaka/Tam/TAMU/Taylor/Lam定向检索；已询问名字是作者还是机构、以及年份/主题线索，尚未收到确认。
- 主要两候选：Liang、Hua Tan、Fu、Chou，Nanotechnology18,025303(2007)，DOI10.1088/0957-4484/18/2/025303（在线2006，摘要为气泡实验/模型比较）；Hayden K.Taylor，Proc.SPIE9777,97770E(2016)，DOI10.1117/12.2218757（Seki2022引文[13]，多尺度液滴/缺陷方向）。两位作者不同，分别是字面名字线索和主题上下文线索，不给出确定身份或伪造匹配概率。
- 辅助Taylor/Lam/Boning2009，DOI10.1088/0960-1317/19/7/075007（Seki引文[11]）。`These_HT_compil.pdf`首页已核为Teyssèdre2013，不能把HT误当Taylor。出处/检索范围/版本差异见`docs/reports/TAN_name_disambiguation_20261029/RESULTS.md`及三份Crossref原回执；作者公开网页HTML已留存，Taylor旧网页2015年份与DOI2016差异保留。未取得并全文验收这三篇候选，不声明找到老师指定文献。
- 本轮仅候选查找与资料/状态维护，无新增计算或验证，无编译/求解/拟合/真实N8提取/新run_id/下一Gate/提交推送/长算授权。旧Gate/PASS/FAIL、独立参考/严格界/投稿状态保持；既有挤压阻力目标仍是推荐，不因候选改变。
- 下一动作：根据用户补充线索确认候选身份；若明确Tan或多尺度Taylor，再针对该篇取得原文并核验证路径。文献查找GPT-6.1 Sol｜High，无需切换。

## 佳能三篇原文已接收，Seki验证/反馈证据已核，最小闭环草案已准备（2026-10-29）

- 按用户“根据第一篇要保留的结论确定目标”完成进一步选择：主目标为全充液长方形图案区给定瞬时间隙/闭合速度的挤压阻力R_sq=F_net/V（N·s/m）；次目标为同区域槽沿短边/长边的阻力比，压力分布为诊断。逐条映射现有§6四结论，见`docs/reports/Canon_received_review_20261029/PAPER1_PREDICTION_TARGET.md`及target_selection_record.json。指出恒速刚性不可压缩全充液下净排液总量受守恒约束，不宜单独作为修正精度目标；载荷与方向性分别评价。仅目标推荐，未冻结具体几何/边界/力定义/网格/资源/门槛，未执行或修改正式稿；无新增计算或验证/新run_id/长算授权，旧Gate与科学状态保持。下一动作明确为R_sq算例输入/边界/净力口径/独立参照/资源/验收字段清单及理论审核。
- 用户最新澄清“现在已经实现公式，但是用什么实现闭环比较好”。本轮明确推荐候选：Python二维各向异性Reynolds模型的瞬时挤压压力/载荷，与经验证的独立显式沟槽Stokes有限元参照比较；FEniCSx仅为实现选项，未宣称现有参考合格。建议先用已有(75,100)nm基准核接口，长方形两槽向可作候选以避免对称载荷掩盖方向性；边界、尺度分离、总法向力口径与资源须预审。详见`docs/reports/Canon_received_review_20261029/RECOMMENDED_CLOSURE.md`；这是推荐，未由用户采用/冻结，未实现或运行，不把同模型三组输入当独立验证，不推完整填充时间。当前不再追问“缺什么”作为澄清前提；下一动作是具体问题清单与协议审核。无新增计算或验证/新run_id/长算授权，旧科学状态保持。
- 导师反馈补充：用户强调“缺少实现闭环的东西”。前轮交付只是文献/方案，不能视为实现；新增`docs/reports/Canon_received_review_20261029/MISSING_DELIVERABLES.md`，把缺口落实为可核查接口与应用算例、同条件独立参照、新条件检验，并按局部系数/工艺预测/机制/实际反馈主张区分终点。此前曾询问老师具体侧重，现用户已明确要求选择闭环方法，见本节最新推荐；不声称所有历史宏观模块不存在。本轮无新增计算或验证，无新run_id/源码改动/启动或Gate变化。
- 用户上传下载目录并要求继续。收到3篇独立PDF：Seki2022 `011005_1.pdf`（13页，SHA3afac08d…），Sreenivasan2017 `micronano201775.pdf`（19页），Choi/Resnick2019 `32_753.pdf`（5页）；无扩展名的Enabling文件与Seki逐字节相同，不算2020会议版。原下载字节与sources/副本核对保持，入口`docs/reports/Canon_received_review_20261029/intake.json`。
- 已完成Seki正文/参考文献文本阅读，重点式(1)(2)及图4/6/9、§3.3.1原页核对；Choi相关文本与pp.755—756图6—8核对；Sreenivasan仅身份/相关工艺背景段，未做全篇终审。Seki图4/6含缺陷实测—模拟趋势比较；图9膜面平坦度改善是模拟示例；§3.3.1明示测量套刻→调整配方→再测量迭代。Choi图8的HODC+DPC同时施加，不能拆出DPC或流阻单独贡献。
- 报告`docs/reports/Canon_received_review_20261029/REPORT.md`按页码/证据ID区分模型连接、数值/物理对照、工艺反馈；含Ban2021接点、K(m³)/κ(m²)/无量纲k及平均定义风险。原文Ban无量纲hf=0.01与H0=1μm时最终100nm的叙述不一致，仅记录疑点，不代作者订正或据此换算本项目时间。
- 已准备`MINIMUM_CLOSURE_DRAFT.md`，状态PROPOSAL_ONLY_NOT_FROZEN_NOT_RUN：先核参考与已有基准的接口，再固定V2与新条件独立检验；可选同模型三组K应用影响示例须标敏感性，独立应用精度仍需外部同条件对照。没有新参数/门槛冻结，没有新求解。Seki2020会议版及老师“TAN木”名称对应仍未确认。
- 本轮仅新增文献副本/提取/接收与阅读记录、报告/草案并维护资料入口/本状态/交接；未改稿件科学正文、源码、CSV、原结果与冻结协议，无新增计算或数值/物理验证，无编译/求解/拟合/真实N8提取/新run_id/下一项/提交推送/对外发送/长算授权。旧D4_N8_diag_v3_1_20261026_v1；NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null；reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD与历史FAIL保持。
- 当前卡点是第一篇所需独立参考/留出证据未齐，推荐应用问题尚未完成具体边界、尺度与资源预审。下一具体动作：按RECOMMENDED_CLOSURE形成瞬时压力/载荷问题清单并核参考条件/来源与单位映射；仅资料/协议准备，不自动启动计算。文献与常规接口核对GPT-6.1 Sol｜High；疑难理论/矛盾裁决或最终冻结按协议建议Astra｜High。

## 第一篇：导师汇报PPT及真实公式示例已准备（2026-10-29）

- 用户范围：用具体几何串起原模型—数值参考—V2修正—偏差，生成第一篇研究思路与成果PPT。已生成16页汇报，1—14页主讲、15—16页备查，逐页备注及独立讲稿齐备；入口`docs/reports/Teacher_briefing_20261029/README.md`。交付`output/pptx/SIM240_Paper1_Teacher_Briefing_20261029.pptx`、`output/pdf/SIM240_Paper1_Teacher_Briefing_20261029.pdf`及该报告目录`讲稿与公式示例.md`。
- 已验证范围：从36个主方向原始result.txt读取K并逐项核表S1，按既有公式/公布V2系数复算偏差、残差、倍率、基准各向异性与主值重建流向；无重新拟合。示例run_id为h75_d100_dx5_P/T，h75/d100/w120/dx5 nm：沿槽偏差+144.95%→+5.90%，跨槽+46.51%→+2.35%。原始输入哈希、逐项数字与文件检查分别见source_manifest.json、arithmetic.json、verification.json。
- 制作限制：指定Artifact Tool运行时不可用，采用本地标准库OOXML生成可编辑文字/表格及嵌图；16页本地布局预览已逐页检查，结构/关系/几何检查无发现。PDF为同布局生成的图片型静态副本，已抽页经Poppler核对；未用PowerPoint/LibreOffice实际打开，跨机字体和换行仍需注意。未安装依赖或修改环境配置。
- 科学边界：新增的是既有数据算术复核与汇报材料，不是新仿真、独立人工科学验收或Gate放行。保留5nm离散参考限定、V2回顾性/局部失效、历史细横槽FAIL、完整历史构建缺口；reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD均保持。旧D4 run_id=D4_N8_diag_v3_1_20261026_v1及NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null未变。
- 修改范围：新增上述汇报目录、PPT/PDF及维护本状态/最新交接；未改原稿、源码、图件、原始结果或冻结协议，无新求解run_id/编译/求解/重跑/真实N8提取/提交推送/对外发送/长算启动或新授权。
- 下一动作：用户按讲稿向导师汇报，如实说明AI参与及本人掌握/亲自复核范围；请导师判断保留主张和优先补证。收到反馈后另定范围，不自动进入下一项计算。普通汇报整理GPT-6.1 Sol｜High，无需切换。

## 公式与结论说明PDF已完成（2026-10-29）

- 用户要求将前轮公式/结论解释转PDF，并明确删除末尾“如果向老师汇报”引用示例、补强建议与本轮状态段、模型建议；PDF未收入这些段落。交付 `output/pdf/SIM240_公式与结论说明_20261029.pdf`，A4共4页；源稿/排版/生成脚本/文字核对记录在 `docs/reports/Formula_conclusions_summary_20261029/`。
- 保留K/J定义与单位、局部立方律、理想Stokes上界及假设、V2经验关系、四条结论/数据表、局部失效与回顾性评价限制；本轮只排版现有解释，没有科学推导或数值复算。关键数字及指定删段已检查，4页渲染目视无明显乱码、重叠或截断，见verification.json。
- 本轮无新增计算或数值/物理验证，无源码修改/编译/求解/拟合/新run_id/真实N8提取/Git提交推送；旧run_id、历史FAIL、各Gate及reference_qualified=false、strict_error_bound_established=false、submission_ready=false保持。此PDF不是投稿版或科学放行记录。
- 下一具体动作：用户阅读交付PDF。任务完成，无需用户启动长计算，无新增长算授权；稿件上传继续暂停，科学验证缺口仍按既有停点处理。

## 文献[6]：新提供PDF为接收稿重复副本，发表版对应仍待（2026-10-29）

- 用户提供`/home/dell/下载/dewangan2018(1).pdf`；与既有dewangan2018.pdf逐字节相同，658320字节、35页，SHA f02b194d45669ba336d3e57e7f6ca7099dbd11e3dcb352cd42333baf53d916cb。元数据及目视首页均为Accepted Manuscript。入口`docs/reports/Dewangan2018_duplicate_receipt_20261029/REPORT.md`、receipt.json及verification.json。
- 接收稿六项指定条件已核的状态保持；本次没有新增最终发表版，不执行或伪报两版本对应完成，不再列“缺原文”。原接收合同、两PDF、中英文稿/补充保持。下一动作：取得期刊最终发表版后按既有六项对应核查；普通资料任务Sol｜High，理论实质矛盾或严格数值界另用Astra｜High。
- 本轮仅文件版本核对并维护本状态/交接，无新增计算或数值/物理验证，无求解器编译/求解/拟合/真实N8提取/第二项/新run_id/Git提交推送。旧N8、历史FAIL、Gate、reference_qualified=false、strict_error_bound_established=false、submission_ready=false及预测HOLD保持。稿件补传继续按下方最新共享范围暂停。

## 第一篇：代码、图片、数据已核对，稿件补传撤回（2026-10-29，当前共享停点）

- 用户最新裁定“稿子不用上传，先上传代码什么的”。本轮只处理代码/图/数据入口；此前远端旧稿保留。裁定前的本地稿件/PDF/补充/审查记录及相关清单更新已全部撤回，未进入提交/推送。最新双语稿和四份嵌图PDF仍未上传，不得据撤回快照声称已补齐。
- 私有仓库yuanyuanxu1022/SIM240_code_figures_data仍private=true；独立共享副本提交`a8d68cdcdd152f57d7f77de8c5079fe4c48ad0ff`已推送，远端main及3个变更blob核对一致、工作区干净。本次只新增`06_代码图片数据查看/README.md`、`核对记录_20261029.json`及根README入口，科学代码/数据无新增变更。
- 01—04已索引8608条的远端路径/Git对象全核；8602条与当前来源SHA256及Git对象身份一致；6张历史配图原路径失效，但已实际下载远端字节并核历史SHA一致。D2/D3主代码/分析及当前图件另查38份均已有覆盖。范围为既定共享清单，不是全电脑/全历史/全部大场完整备份。证据`docs/reports/GITHUB_FIRST_PAPER_REFRESH_20261029/REPORT.md`、`publish.json`、`code_only_verification.json`、`code_figures_data_audit.json`；withdrawn_manuscript_preparation/仅为撤回快照。
- 本轮无新增计算或数值/物理验证，无编译/求解/重算/真实N8提取/新run_id或长算授权。旧run_id与历史FAIL、Gate、reference_qualified=false、strict_error_bound_established=false、submission_ready=false保持，不因文件核对改变。
- 下一具体动作：用户/老师从仓库`06_代码图片数据查看/README.md`访问代码/图/数据。稿件补传暂不执行；若需全部大场或可迁移运行包另定范围，不自动启动。常规资料管理GPT-6.1 Sol｜Low，无需切换。

## 导师口头汇报准备（2026-10-29）

- 后续公式解释：按现行正文§2.2—2.3、§3.2、§4.4区分指标定义、平板解析基准、局部立方律模型、OpenLB离散参考、V2经验修正与偏差评价；沿槽yy/跨槽xx、K单位m³保持。V2是回顾性经验修正，数值参考不是真值；本轮仅解释，未复算、推导新公式或改变科学采用状态。
- 本轮范围：用户询问如何向老师汇报当前成果，并明确担心“都是AI做的”；仅核对当前状态、路线/历史入口与现行中文稿，组织口头说明，不进行科学终审。汇报以第一篇固定几何、全充液、单相方向性输运比较为主。
- 口径：已有中英文审阅稿、四张主图与配套记录；18种几何/36个主方向样点及定量偏差为现行稿件记载，本轮未从原始CSV重新验算。AI参与代码、分析和文字的实际范围应如实说明；不替用户虚构独立设计、编程、复核或理解程度，不将AI多轮审查称为独立人工验证。
- 本轮无新增计算或验证；仅修改本状态和最新交接。历史FAIL、参考可信范围、构建来源缺口及submission_ready=false均保持。无新run_id，无编译/求解/重跑/提交推送/对外发送或长算授权；旧N8记录及Gate不变。
- 下一具体动作：向导师展示当前中文审阅PDF，围绕科学问题、现有发现、验证限制及需导师裁定的重点汇报；由本人说明已理解与尚不能独立解释的部分。是否补算及补算范围另行确定，不自动开始。

## 资料副本：英文目录命名已落实（2026-10-28）

- 用户要求把上一轮分类副本改用英文名称。新根目录`/home/dell/yuanyuanxu/SIM240_Paper_Archives_20261028`；两篇为`Paper_1_Single_Phase_Groove_Transport`和`Paper_2_Liquid_Gas_Flow_Resistance`，内部为`Research_Materials/SIM240`和`Shared_Foundations_and_Historical_Archive/SIM240`；阅读入口`READ_ME_FIRST.md`，总入口`README.md`。旧中文目录已重命名，不另留一套重复副本。
- 仅改整理副本的外层目录、入口和管理文件名称，更新当前清单中的副本路径及入口链接；内部原始科研文件、PDF、源码、数据、冻结合同名称与内容保持。原复制日志/脚本/初次回执保留历史路径，以新`rename_mapping.json`和`file_manifest_sha256.csv`为当前索引。
- 本状态/最新交接同步至两边共用副本，更新对应SHA和大小；全量副本内容核对及入口链接检查见新根`rename_verification.json`。这不是数值或物理验证；无编译/求解/拟合/新run_id/真实N8提取/Git提交推送或新长算授权，历史Gate/PASS/FAIL保持。
- 下一动作：用户从新英文目录的READ_ME_FIRST.md查看。此次命名任务完成，常规资料管理GPT-6.1 Sol｜Low。下方中文目录路径为重命名前的历史记录。

## 资料整理：SIM240完整分类副本已核验（2026-10-28，文件整理完成）

- 用户裁定：复制到SIM240同级新文件夹；完整保留原始数据、日志、已有程序和隐藏内容；共用资料两篇各留一份；归属不明的早期填充/液滴、grooveDNS、CASE/H/archive/plans、工具配置、临时文件、回收站与Git历史，经用户确认作为“共用与历史资料”两边保留，不认定为本篇正式结果。
- 副本根目录：`/home/dell/yuanyuanxu/SIM240_两篇文章整理_20261028/`。仅两个顶层资料文件夹“第一篇文章”“第二篇文章”；每篇含`01_本篇资料/SIM240`与`02_共用与历史资料/SIM240`及`阅读入口.md`。总入口`使用说明.md`，逐项原路径/去向/SHA在`逐项复制与SHA256清单.csv`；规则及核验见`分类规则.json`、`复制核验报告.json`、`阅读入口核验.json`、`链接依赖清单.csv`。
- 初次全量核验：原目录122744项=99858普通文件+3715符号链接+19171目录；本篇第一82242文件、第二2902文件，共用14714文件各复制一份，总114572普通文件；全部复制内容/权限/链接核对无差异，原来源前后无变化。34条新阅读入口链接均存在。40条副本链接记录原本即不可解析，原链接文字保持；外部依赖未自动收入，不能称任意机器可运行/可独立复现。
- 本轮原项目仅维护本状态和最新交接；源码、稿件、数据、原结果及冻结协议未改。两份状态文件随后同步到两边共用副本，附逐项更新哈希回执，清单与最终报告同步修正。本次仅复制资料，没有编译/求解/拟合/真实N8提取/新run_id/Git提交推送或新长算授权；旧PASS/FAIL与Gate保持。
- 同步更正前次总结快照：`Paper_bilingual_layout_20261028/README.md`及verification已存在并核到，中文/英文正文与S1—S11同步、四份嵌图审阅PDF的文档核验已完成；不再列为未生成报告。作者最终科学采用、真实声明、最终访问版本与期刊格式继续待办；submission_ready=false。其余科研停点以下方当前科研记录为准。
- 下一具体动作：用户从两个阅读入口查看；若另做可迁移运行包，须独立审查依赖及路径，不从本次文件校验推定数值验证。本复制任务完成，无需用户启动计算。常规资料管理GPT-6.1 Sol｜Low；数值/物理审查另按范围。

## 第一篇：附录解释、中英文正文及S1—S11已同步，四份嵌图审阅PDF完成（2026-10-28，当前科研停点）

- 用户授权按上一轮采用范围整理解释、同步英文并嵌图；C-E1—C-E4已合入正式中文附录E。沿用指定Astra书面终审“可限定冻结”的假设与结论，没有理论推广或严格数值误差界审定，未新增Astra调用；作者整篇最终科学签字仍独立待办。原书面意见及其额度中断/缺失JSON回执边界见`docs/reports/Appendix_E_final_review_20261028/REPORT.md`。
- 当前中文为`docs/reports/SIM240_中文稿_导师审阅版_20261022.md`；当前英文新入口`docs/reports/SIM240_First_Paper_English_20261028.md`，旧20261019英文整合稿原字节保留为历史稿。补充中文原入口保持，英文为`docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md`。正文202块、补充73块逐段同步，四张既有主图统一当前图号1—4，未复活旧图9/10或动态行程主张。
- 直接阅读`output/pdf/SIM240_First_Paper_ZH_20261028.pdf`（12页）、`SIM240_First_Paper_EN_20261028.pdf`（14页）、`SIM240_Supplement_ZH_20261028.pdf`（4页）、`SIM240_Supplement_EN_20261028.pdf`（5页）。四PDF为A4单栏作者审阅版，不是期刊最终模板；PDF收正文/E/参考文献，A—D管理历史仍在正式中文源。表S1—S5完整CSV沿原目录，PDF不含全部原始场。
- 工作/核验入口`docs/reports/Paper_bilingual_layout_20261028/README.md`、author_scope.json、translation_map.json、supplement_translation_map.json、verification.json及qa/。原16个展示公式、11条书目保持，275块数学/数字对应通过；54本地链接及35页排版检查通过。625份选定来源仅两份授权中文文稿改变，其余623份（图件/CSV/原结果/源码/协议/旧英文等）保持。这是文档核对，不是数值精度或物理验收。
- 下一具体动作：作者/导师核对两种语言及真实作者/单位/基金/贡献/冲突/AI资料；按最终固定版本完善数据声明并核目标期刊格式。英文同步和嵌图已完成，不重复列作未开始。[6]接收稿适用条件已核，发表版对应及四组完整历史构建仍OPEN。改变假设、理论实质推广或严格数值界才再用Astra｜High；普通收尾GPT-6.1 Sol｜High。
- 本轮四PDF和新英文/修订尚未上传GitHub，最后共享仍025eac0c7f752c4a023ebc64db0950fa6b7c98b5；源附录C的f11c0f2是更早日期记录，不代表本轮覆盖。无求解器编译/仿真/拟合/科研派生量重算/夹具/真实N8提取/第二项/新run_id，无提交推送或启动命令。旧N8 D4_N8_diag_v3_1_20261026_v1，NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD；历史细横槽FAIL/exit3保持。

## GitHub：第一篇当前全文与配套材料已上传，剩余事项已更新（2026-10-28，当前共享/资料入口）

- 用户明确要求上传第一篇文章全部现有内容并盘点下一步；目标沿用原私有`yuanyuanxu1022/SIM240_code_figures_data`，API重核private=true及push权限。仅在独立共享副本提交推送main，提交`025eac0c7f752c4a023ebc64db0950fa6b7c98b5`、父提交`dccaca7af38a35c37cbddb74109621e1d2255abd`；远端HEAD、父提交及241个变更路径/逐项blob SHA已核，工作区干净。未从主项目或参考仓库push、未改账号/remote/权限或邀请老师。
- 新入口`05_第一篇文章/README.md`：当前中文全文、方法S1—S11/表S1—S5、四主图三格式和代码、选择的证据记录及79条表内运行入口；现存英文稿明确标2026-10-19历史未同步版。228份原字节副本+2份仅适配链接的阅读版及入口/清单/检查，共241路径；复用397份既存来源（约228MB），总来源清单8608→8836行。228份副本/397份源字节与Git身份、543条阅读入口链接、296公式片段/附录E保持及远端blob核对见`docs/reports/GITHUB_FIRST_PAPER_COMPLETE_20261028/REPORT.md`、source_files.json、publish.json、verification.json。
- 本次明确包括正文，取代前次“未上传正文”的范围；第三方论文原件/全文/页图、账号资料、编译产物、第二篇和真实N8原始场不收入本轮。原件局部本机路径保留出处，阅读版映射共享文件；不是所有历史档案/全文和全部大场的完整可移植复现证明。旧恢复性报告的强断言由历史构建裁决覆盖，旧盘点M1缺原文由当前接收记录覆盖，不按旧快照重复列缺。
- 最新剩余清单`docs/reports/GITHUB_FIRST_PAPER_COMPLETE_20261028/NEXT_STEPS.md`及仓库`05_第一篇文章/材料覆盖与缺口.md`：作者/导师最终采用（附录E限定书面意见已取得，见顶部）；作者单位/基金/冲突/CRediT/AI声明；英文同步与最终嵌图版式；实际固定版本/访问方式的数据声明；[6]最终发表版对应；四组历史来源若能补档继续按合同核。正文附录C仍记录f11c0f2旧日期快照，本轮未改其历史说明，最终声明需采用本次实际覆盖版本。当前私有分享不等于公开数据/DOI或投稿就绪。
- 连续定量精度、全图统一误差、独立预测或机制份额仅在确需升级主张时另立参考合同；不自动重算或做N8。原文稿/公式本轮未改，无编译/求解/拟合/重画/夹具/真实N8提取/第二项/新run_id；旧N8仍D4_N8_diag_v3_1_20261026_v1，NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null，reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD；细横槽FAIL/exit3保持，未重新验收。普通资料收尾GPT-6.1 Sol｜High；本轮附录E限定书面审查见顶部，后续实质理论改变/严格数值界另用Astra｜High。

## 第一篇：三段历史构建限定文字已按作者范围同步，最终理论冻结仍未执行（2026-10-28，当前停点）

- 用户本轮明确采用C1/C2/C3：C1合并补充S10末段，C2合并正文§4.4回顾性段，C3插入§5.3范围/局限段；未收到排除条目。正式稿2处、补充材料1处，三段核心文字均已落位；整篇稿件最终科学签字不由本次写入代替。入口`docs/reports/Historical_build_text_sync_20261028/REVISION_NOTE.md`、`author_scope.json`、`document_changes.json/.diff`、`verification.json`，前稿在before/。
- 本轮仅落实前轮GPT-6 Astra｜High历史构建裁决，未新增模型裁决或理论推导。公式/系数/结果数字/正文表行、摘要/结论/参考文献和附录E保持；补充仅S10末段改变，S11与表S1—S5不改。候选与旧裁决报告保留历史字节，当前采用状态由本同步记录补充。
- 四组SHA仍22/22/6/2：285f…为标定主图18+加密4，5761…为扩展主图18+加密4，85cc…为独立D3六项，efd2…为黏度两项。现存匹配28=22+6只确认二进制身份，mtime/今日HEAD/.d/config.mk不补完整历史构建关联，四组仍OPEN，不回填manifest。原裁决入口`docs/reports/Historical_build_adjudication_20261028/REPORT.md`、`ASTRA_REVIEW.md`与verdict.json。
- 正式稿现已说明主图9标定/9扩展几何的程序身份完全分区、d75范围内留出而d120/h25范围外扩展、潜在构建效应不能由现有记录单独识别。同几何P/T同SHA不保证误差抵消，单点对照也不证明全图等价；不能据此判定已知物理偏差或自动决定重算。5nm保存记录比较及V2回顾性评价保留，未升级连续精度或独立预测主张。
- 本轮只改上述两份文稿、更新本状态/最新交接并新增同步记录；选定来源哈希及公式/附录E等保护见verification.json。无编译/求解/真实N8提取/数值夹具/拟合/重画/第二项/Git提交推送/新run_id，无启动命令或长算授权。旧N8仍D4_N8_diag_v3_1_20261026_v1，NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null，reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD；细横槽历史FAIL/exit3保持，未重新验收。
- 三段同步任务完成。附录E及公式/结论最终理论冻结仍须另按GPT-6 Astra｜High审查范围处理，不自动开始；普通核稿GPT-6.1 Sol｜High无需切换。后续作者声明、最终数据覆盖/排版及整篇科学采用保持各自待办，不因文字同步关闭。

## 第一篇：[6]2018接收稿已取得，M1指定适用条件已核（2026-10-28，当前资料接续入口）

- 用户提供`/home/dell/下载/dewangan2018.pdf`，确为正文[6]，DOI10.1016/j.euromechflu.2018.02.004；658320字节，SHA `f02b194d45669ba336d3e57e7f6ca7099dbd11e3dcb352cd42333baf53d916cb`。版本为Elsevier接收稿，35个PDF页=1页封面+34页稿件；不是最终排版版。入口`docs/reports/Dewangan2018_received_20261028/REPORT.md`、`intake.json`、`contract_receipt.json`。
- 按M1核身份、正弦/平壁几何与沿槽方向、主问题无滑移及另行滑移扩展、完整谱方法与小振幅/厚薄通道近似的区别、h/a及Q/Q0定义、矩形槽与本文引用关系。指定条件在接收稿层面已核；最终排版版逐页对应未核，不称全文全部推导或全部参考文献终校通过。完整谱方法不能概括为仅小振幅，也不能直接给本文矩形槽P/T精度背书。
- 仅同步正式稿引言[6]一句/书目注/附录C引文清单3处，补充S11日期/[6]条目2处；差异`document_changes.json/.diff`，前稿`before/`。公式、结果、图表及历史FAIL保持，作者最终科学采用未记录。更新本状态及最新交接；旧缺口报告保留历史快照，由新receipt补充M1当前状态。校验范围见本目录`verification.json`。
- 历史构建专项仍是独立事项，本轮未裁决其源码/版本绑定与标定—留出分组推断，不因本次[6]核对关闭来源缺口或认可其中“完整绑定”等强断言。下方该专项段落保留其原范围，不作为本轮独立验收。需要裁决实质理论/多证据矛盾或严格界时才按规则用GPT-6 Astra｜High，本次未触发。
- 无编译、求解、真实N8提取、数值夹具、拟合、重画、第二项、Git提交推送或新run_id。旧N8仍`D4_N8_diag_v3_1_20261026_v1`，`NUMERICAL_GATE=NOT_EVALUATED`、`RESULT_PASS=false`、`geometry_PASS=null`，`reference_qualified=false`、`strict_error_bound_established=false`、`submission_ready=false`、预测HOLD沿用；无新运行命令/授权。第三方PDF/全文/页图只留本地，前轮GitHub提交`dccaca7`不因本次本地修订自动刷新。
- 本次接收核对完成；下一资料动作可由作者核对版本说明，另行取得最终排版版后对照指定段。历史构建、作者声明、最终共享覆盖/版式及作者最终采用分别继续处理；不自动重跑任何算例。常规资料核对建议GPT-6.1 Sol｜High，无需切换。

- 补充下载资料核对（本次用户确认仅核新资料）：`MS_SPECTRAL_2_RG.pdf`为30页作者格式稿，SHA `a025ee8b4b7bc7877930ed8c6884bb7ad8b8d9b48a39b041613594c674a56161`，首页Preprint日期2019-03-23；不能据日期认定为更晚科学修订或最终发表版。与35页接收稿的主问题/完整谱方法范围相合，但缺少后者2.1.3滑移扩展，附录/公式号及尺度符号有差异，不能混用。正式稿/S11继续以已核接收稿为据，最终发表版对应仍未核；本轮不改稿件或公式，无需Astra裁决现有限定引文，不声称两稿全部公式等价。新增入口`docs/reports/Download_new_sources_20261028/REPORT.md`、`intake.json`、`verification.json`。
- 本次新增资料未提供历史构建证据；旧专项矛盾未裁决，不重跑建议算例。仅新增上述资料记录并维护本状态/交接，7份选定来源哈希保护；无编译/求解/真实N8提取/数值夹具/拟合/第二项/Git提交推送/新run_id，既有Gate、FAIL、reference_qualified=false及严格界/投稿未就绪状态保持。此资料核对完成，常规核对GPT-6.1 Sol｜High无需切换；实质理论矛盾裁决或最终理论冻结再用GPT-6 Astra｜High。


## 第一篇：当前缺口已盘点，先完成资料/投稿收尾，强精度补证另立范围（2026-10-28，当前科研接续入口）

- 用户请求核对现在缺什么、还需补什么；本轮只读盘点，不作理论最终冻结。入口`docs/reports/Current_gap_inventory_20261028/REPORT.md`、`remaining_items.json`、`current_evidence_checks.json`。当前正文为V2回顾性比较稿，后续G4预测合同不自动作为本稿前置；P8/P9/P10指定方法原文对应及GCI表S5已补齐，不重复列缺。
- 仍需处理：正文[6]2018原文具体适用条件、四组完整历史构建来源（恢复不了则保留限制）、作者/单位/基金/冲突/CRediT/AI等声明、最终数据代码访问及版本覆盖、四图嵌入后的版式/目标要求、作者导师最终科学采用。四张图文件本轮确认已有，不要求重画全套；本轮未刷新远端或核期刊现行政策。
- 本轮逐份读52份原manifest，二进制SHA均与表S1相符，仍为22/22/6/2组；source_sha256/generated_source_sha256/openlb_commit/compiler/compile_flags五字段各52份缺失，不据此断言全机不存在档案。历史细T仍PASS=false/exit3/质量1.1967043900362632e−10；全图连续精度、稳态误差及严格误差界未闭合。限定5nm比较可沿用现有数据；若要升级连续定量/预测主张，另立参考合同，不自动补跑36点或18项。
- 真实N8绑定仍DRAFT_NOT_APPROVED_NOT_EXECUTABLE、approval=null、real_extraction_authorized=false/solver_authorized=false，计划实际分析目录本轮不存在；人工夹具不等于真实场精度。旧run_id=D4_N8_diag_v3_1_20261026_v1，NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null；reference_qualified=false、strict_error_bound_established=false、submission_ready=false，预测HOLD。77份选定读取来源本轮前后保护；未读实际N8数组、编译/求解/夹具/拟合/保留评分/第二项/Git提交推送；正文/补充/图件/源码/协议/历史FAIL不改。
- 下一具体动作：先取得[6]原文及接收既有构建档案，核缺失能否恢复；并由作者完善声明和最终共享/排版材料。强精度验证仅在明确保留主张与新合同/授权后准备。常规核对GPT-6.1 Sol｜High；最终理论冻结、实质矛盾或严格误差界审定用GPT-6 Astra｜High，本轮未触发。下方P8接收与GitHub协作问题保留各自范围。

## 第一篇：Bouzidi原文已收到，P8六项指定对应已核（2026-10-27，当前科研接续入口）

- 用户指定下载目录最新PDF，已接收真正Bouzidi发表版：DOI10.1063/1.1399290，PDF9页=1页AIP封面+3452—3459连续八页正文，413724字节，SHA751511dd8df61e373a0f94c86da350642ab38fe5c3602ac20bcff979ba4d10d7。入口`docs/reports/Bouzidi_P8_received_20261027/REPORT.md`、`intake.json`、`contract_receipt.json`、`current_implementation.json`。旧未取得报告保留历史快照，当前由本接收入口取代。
- 六项已核：3453页III.A的q与II节碰撞/传播定义；3454页图1、固定壁线性式5a/5b、静止壁适用说明、q=.5/式7。13份当前D2/OpenLB源码配置按原行号/SHA核；PostStream读取经正常CPU SISD传播映射至原文碰撞后值，存储常数偏移因相反方向等权及系数和1抵消。原文q=.5归后一分支、代码归前一分支，端点代数相同；没有实质理论矛盾，未触发Astra。P8只关闭有效链/有限输入/所查当前源码六项对应，不作运行、历史构建或精度证明。
- 仅同步补充S11的[8]原文状态/[5]副本不能替代其他原文的表述、正文附录C的参考文献终校清单；源码、理论假设/公式/结论、全部数据表、冻结合同及历史FAIL保持。前稿/精确差异见本目录before及document_changes.diff；80份选定保护输入与修改范围检查见verification.json。九页均渲染目视核身份/连续性，方法详读3453—3454；其他算例未重新验证。
- 本轮无编译、OpenLB预检运行、数值夹具、求解、真实N8提取、拟合、第二项、Git提交推送或新run_id；原件未远端发布。旧N8仍D4_N8_diag_v3_1_20261026_v1，NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null；reference_qualified=false、strict_error_bound_established=false、submission_ready=false，预测HOLD。P9/P10指定对应沿用原接收记录，正文[6]2018年全文适用条件和四组完整历史构建仍OPEN。
- 当前P8接收任务完成，无新增计算许可/启动命令。下一具体资料动作仍是取得[6]原文或四组对应历史构建档案后按既有合同核对；不得由P8关闭提前放行数值参考/预测。常规对应核查GPT-6.1 Sol｜High；理论实质矛盾/假设改变/严格界裁定再用GPT-6 Astra｜High。GitHub协作问题保持下方记录，本轮未复核平台状态。

## 共享协作：完整截图已补齐，需GitHub核账号身份/邀请异常（2026-10-27，当前共享入口）

- 用户目标仍为邀请老师bokong537协作；已确认能检索/选中，但发送时报错。最新完整截图显示github.com/settings/emails、账号25yuanyuanxu-source、Primary/Verified和隐私邮箱编号34883237。邮箱验证与页面截图前置已完成，不再要求重复同页截图、验证邮箱或反复邀请。入口`docs/reports/Teacher_collaboration_access_20261027/FULL_SCREENSHOT_FOLLOWUP.md`及`case.json`。
- 本轮API复核仍为编号34883237→dengzhang（200），新账号按名404，老师bokong537公开200/ID34483962；上一轮Astra独立API复核结果保持。截图所示与公开记录存在未解释差异，不据此确认封禁、盗号、伪造或缓存/改名根因；平台内部状态仍待核。
- 下一具体动作：用户用受影响账号登录GitHub Support并提交已准备的`SUPPORT_REQUEST_READY.md`，请求核账号身份/公开可见性及邀请失败；可附现有错误截图，精确报错尚未取得但不再要求机械重试。代理没有提交工单或发送消息。免费账号可报账号问题，不要求购买套餐或承诺处理时限。
- 原上传授权与8,637项清单保留，直接登录脚本未由代理运行，不能代替修复邀请老师功能。本轮未改账号配置/token scope/邮箱/密码/remote、未发送邀请、未提交/推送/编译/求解/真实N8提取/第二项，无新run_id。
- 科研最新状态见顶部Bouzidi原文接收入口；旧N8 run_id=D4_N8_diag_v3_1_20261026_v1，NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD，旧FAIL保持。

## 第一篇：上一轮原文接收，P9/P10指定核对闭合，P8仍缺（2026-10-27）

- 用户范围：`/home/dell/下载`刚下载的三篇，沿用最小资料合同，只读核方法原件/当前实现，保持新增计算关闭。入口`docs/reports/Primary_text_received_20261027/REPORT.md`、`intake.json`、`contract_receipt.json`、`current_implementation.json`；原件路径/大小/SHA、Crossref响应、页预览与核对结果均在该目录。
- 实际收到：P9 Guo六页发表版（10.1103/PhysRevE.65.046308），P10 Celik四页发表版（10.1115/1.2960953）；指定页/公式与当前源码或旧作者稿的对应已核。P10六作者位于末页；式4上标21/式6内部12的符号不一致也保留在发表版。P9力密度F与FORCE加速度字段、ρ_lat系数、omega=1/tau及半步速度转换对应，只关所查当前实现关系，不绑定历史程序。
- 第三份为正文[5]Dewangan–Datta2020，DOI10.1017/jfm.2020.134，35页，与目录既有无(1)副本SHA相同。只核首页/身份，不计新增独立理论证据；不是P8 Bouzidi，也不是正文[6]2018年文章。P8仍缺10.1063/1.1399290的完整8页；[6]2018年全文条件与四组完整历史构建绑定继续OPEN，未重新全机搜档。
- 文件维护：正文附录C仅更新参考文献终校剩余清单；补充S11只更新P9/P10已核状态及[5]副本身份。此前作者采用的GCI表/限定文字已同步，见`GCI_author_sync_20261027/REPORT.md`；表S1—S5、正文科学段落/结果/理论附录、模型、源码、冻结协议、旧报告与历史FAIL保持。来源核实不等于数值参考合格或全图误差界。当前正式稿仍待作者终审。
- 核对范围/权限：三份PDF提取exit0，9页新原件+1页旧文稿附录已渲染目视；原件、所查源码及选定旧证据字节保护见verification.json，不是全部源码/历史运行重验。无编译、求解、真实N8提取、拟合、第二项或Git提交推送，无新run_id；本轮无理论实质变更/严格界裁定，未触发新的Astra复核。
- 状态：旧N8仍D4_N8_diag_v3_1_20261026_v1；NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、reference_qualified=false、strict_error_bound_established=false、submission_ready=false，预测HOLD。历史G2 Step3 FAIL/INCONCLUSIVE及5nm离散参考口径保持。
- 下一具体动作：取得真正P8及其q/两分支/时间层原文证据，取得[6]2018年原文及历史构建档案后按合同只读核对；本次补齐P9/P10不授权新计算。常规资料核对GPT-6.1 Sol｜High；假设改变、理论实质推广或严格误差界再用GPT-6 Astra｜High。

## 第一篇：提取器v2四项修订及人工验证完成，实际N8仍关闭（2026-10-26，当前入口/停点）

- 用户授权完成B01/B02/C01/C02小版本修订及人工验证，保持实际N8提取/求解关闭。新入口 `docs/reports/G4_offline_extractor_revision_v2_20261026/REPORT.md`、`resolution.json`、`fixture_results.json`、`verification.json`；状态 FOUR_PREPARATION_FINDINGS_ADDRESSED_SYNTHETIC_VALIDATION_PASS_REAL_CLOSED。原准备/只读审查目录及证据原字节保留，没有修改理论判据、物理门槛或裁定严格误差界。
- 代码仅新增 `CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/offline_extractor_revision_v2_20261026/`，8份Python源码与规范/README。numerics.py及原17组test_fixtures.py为未改字节副本；新绑定读取、完整分析记录、新人工夹具及synthetic_cli；公开extract_real_record无条件在访问路径前拒绝。可测试读取器只接受人工标记且先拒绝真实N8目录及上下级路径，无真实分析/求解入口。
- B01已准备固定原验收证书SHA、原accepted-input清单SHA、48文件摘要、代码/规范、唯一分析标识及输出位置的真实绑定/信任锚草案；原150项验收输入覆盖全部48记录，逐项SHA一致。real_N8_binding_DRAFT.json批准null、状态DRAFT_NOT_APPROVED_NOT_EXECUTABLE、实际提取/求解false，拟议实际分析目录未创建。源run_id仍D4_N8_diag_v3_1_20261026_v1，不新增求解run_id。
- B02共用必需record schema的人工成功/拒绝链已核：48文件、8+17数组、N8尺寸153顶点/256三角形/1275混合自由度/39周期对；固定字节快照读数组并读后/分析后复核。C01已核非零速度/压力L2的闭式分子分母/比值、压力平移及重排。C02固定软件一致性2e−11、后处理变化1e−8、64eps软件邻域（不是误差界）、完整有限JSON/唯一产物/日志/失败/退出状态，不激活物理Gate。
- 30组测试（17回归+13新增）0失败0错误0跳过，进程exit0，完整日志fixtures_run1.log；另2个独立人工进程，成功外层/记录exit均0，改字节失败例两处均2且保留failure/traceback/事件、不写成功指标。人工矩阵/节点场不是PDE解，成功不代表物理准确。人工包与过程证据保留在报告子目录、全部标人工；旧17组历史记录不覆盖。
- 四问题在准备范围内实现并经人工验证，实际数据运行及独立验收未做。静态核96审查来源、48实际N8记录、358生产来源锁、4233历史保护路径和G4的14绑定保持；实际.npy仅字节SHA核验、未np.load或积分，无PDE后端/后端建网/组装/求解/OpenLB编译/拟合/Git提交推送。
- 原N8仍仅ONE_N8_DIAGNOSTIC_ACCEPTED；NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD；旧网格FAIL/G4锁/旧3%与5%评分均不变。
- 本轮仅新增v2代码/报告与更新本状态/最新交接。下一具体动作：只读复核v2代码、绑定草案和人工证据；之后若另进已有N8分析，须限定已有记录及唯一新分析产物，保持不重跑、不进入第二项。本版无真实执行路由，当前无启动命令。下一步建议GPT-6.1 Sol｜High；改变理论判据/审定严格界才建议GPT-6 Astra｜High，未声称模型切换。
- GitHub共享包已发布（2026-10-26）：用户先指定`yuanyuanxu1022/SIM240_code_figures_data`并审查206路径草案，随后明确要求上传。只在独立副本`/home/dell/yuanyuanxu/SIM240_code_figures_data_review_20261026`创建提交`f11c0f20f6aaadf6920b95390855ec418cf8ae42`并推送该私有仓库`main`；GitHub API确认父提交、206变更文件、远端HEAD及6个关键blob SHA，副本工作树干净。200份新增主项目来源逐字节/大小/SHA一致，清单8391→8591；旧8391份保持原提交并沿用其完整验证记录，未本轮重新全量读取。发布详情见`docs/reports/GITHUB_SHARE_N8_PACKAGE_PREP_20261026/PUBLISH.md`、`publish.json`；上传前草案报告仍保留为历史准备记录。共享包不含真实N8原始场/完整运行记录、第二篇快照或论文正文。无新求解、真实N8提取、第二项、科学Gate或投稿放行；源run_id仍`D4_N8_diag_v3_1_20261026_v1`，NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、reference_qualified=false、submission_ready=false、预测HOLD。下一具体研究动作仍为只读复核v2代码/绑定/人工证据；实际N8分析或新增求解须另行界定范围。

## 第一篇：G4论文主张与最少验证清单已形成，不启动计算（2026-10-26，当前入口/停点）

- 用户授权明确G4精度/适用范围主张及最少验证，明确不启动计算。新入口`docs/reports/G4_paper_claims_minimum_validation_20261026/REPORT.md`，六类主张`claims.json`，来源绑定`source_manifest.json`，静态检查`verification.json`。这是作者工作稿/主张规划，不是公式最终理论冻结或运行许可；submission_ready=false。
- 当前论文可保留G4“有物理约束的四参数经验关系式”及相对于旧5nm参考的留组表现；不承诺全域/连续物理3%/5%、任意占比或真实工艺准确性。旧数据15几何/30方向；拟议域s[.8,3.2]/t[1/3,1.6]与实际冻结8测试几何集合分开，即使测试全通过也不称全域统一保证。阻力误差按倒数换算，A单列。
- 最少验证按V0已有证据只读收口→V1版本化合格参考/误差证据→V2原冻结16主方向+4细格、8个A独立评分→V3按结果限定论文措辞。16+4不是当前运行授权；主参考变化/重拟合另立版本，不能替换v1原5nm主分数。完整18矩形项不作为所有论文表述的机械前置；若用新有限元参考，删减/替代需事前逐项写明等价方法证据，N8不替代沟槽精度。
- 本轮静态核对25份去重来源、14锁绑定、6条G4旧CV统计行、训练角色/测试几何和报告本地链接，未运行拟合/预测评分/流场验收。旧CV各向异性最大6.357866%/5.931917%继续披露；未来六条件3%/5%目标不改、测试未评估。两个窄槽旧三格FAIL、10/12开发加密证据和宽细/预测HOLD不变。
- 本轮只新增上述目录及维护两份状态/交接，未改正文/模型/系数/协议/门槛/源结果，无编译/新run_id/求解/Git提交推送。N8已有诊断验收见下一节；NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null，预测HOLD。
- 下一具体动作：先只读完成V0的主张—已有证据一致性核对，并审V1参考合同/提取方法缺口；不得自动运行剩余17项或第二项，任何新求解须另审授权。当前无需用户终端操作。公式/理论最终冻结前终审按AGENTS建议GPT-6 Astra｜High，当前工作稿不声称已完成该终审。

## 第一篇：首项N8只读独立验收通过，仅限代数求解/记录诊断（2026-10-26，当前入口/停点）

- 用户授权只读验收、不重跑/不进入第二项。实际run_id=D4_N8_diag_v3_1_20261026_v1；报告`docs/reports/D4_N8_acceptance_20261026/REPORT.md`，机器判定`verdict.json`，冻结读回`frozen_readback.json`、另一算术路径`independent_arithmetic.json`、完整输入SHA与audit.py/log。结论ONE_N8_DIAGNOSTIC_ACCEPTED；审查exit0，无PDE后端导入/求解/重跑。
- 已独立核实：批准合同/358来源与开始结束锁相同；launcher与worker exit0；41份work及持久archive逐份大小/SHA完整，原目录/副本读回相同；4233历史保护路径、150本轮读取输入前后SHA保持。原A/b与锁定预检字节SHA一致，未重新组装。
- GMRES/无预条件器、restart50/max2000/rtol1e−10等固定设置一致；正原因2、680次、681条历史。CSR真实残差9.986628529227613e−11≤1e−10；独立稠密乘法9.986616675720506e−11，均与记录差≤1e−12。仅低门槛约0.134%，不放宽、不冒称精度裕量充分。r=Tx/周期/壁面误差0，39周期对/132壁面自由度，零空间≤1.97e−19、相容/投影变化0；压力去均值误差3.253e−19、平移误差0；独立面积权重差8.674e−18；矩形153顶点/256三角形/面积2及P2/P1映射通过。
- 运行北京时间17:41:34→17:41:35，监督耗时1.245秒；cgroup记账峰值82628608字节/无OOM或max事件，直接子RSS141008KiB、树RSS抽样202473472字节（统计口径不同，不相加），完整work802193字节≤512MiB。运行子组已清理；预算可行性结论仅此N8，不外推更细格/整批。原记录仍CHILD_EXITED_UNVERIFIED，独立结论在新报告，不覆盖原始结果。
- 批准仍只限该已完成首项；原physical_plan/18项执行位false、原候选、来源锁、科学协议/阈值/G4锁/旧FAIL保持。NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、预测HOLD。解析场L2、通量能量、网格收敛、余17项/沟槽/公式验证未评估。
- 当前任务完成，已同步状态/交接；无编译/拟合/Git提交推送，不给重跑命令。下一具体动作如继续，先按用户新范围审查后续精度或另一单项及预算；本轮不启动第二项，也不复用N8许可扩大计算。现阶段无需终端操作。


## 第一篇：真实网格到原始记录适配已静态核查，求解仍关闭（2026-10-26，历史准备入口；最新结论见上方）

- 范围/路径：用户要求审真实结果适配、收敛与资源，明确协议和运行授权前不计算。新入口 `CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/result_adapter_review_20261026/REVIEW.md`、`bridge.py`、`evidence/bridge_audit.json`和`independent_review.json`；修正前一`raw_capture_review_20261025/raw_writer.py`二维速度自由度映射，原始数组增至16组。前一求解候选、DRAFT_v2、18项拒绝白名单、G4 v1及旧网格FAIL不变。
- 已验证：9/9真实矩形网格/MPC/DOF上人工数值的16份原始数组逐值和哈希读回；最细104943混合自由度，速度93170/节点46585、压力11773、周期对299。独立复核PASS_REVIEW_ONLY，4233保护路径不变；合成进程stdout/stderr及独立exit7测试保持。无KSP、无PDE求解、无正式run_id或真实结果。本轮没有OpenLB编译、Git提交/推送。
- 未验证/失败保留：GMRES+PC NONE未迭代，4GiB RAM/4GiB盘/2小时未验证；候选未收敛时只抛诊断，不保留已有代数向量原始文件；逐项峰值RSS、通量/能量/周期迹、真实进程记录及独立科学验收尚缺。当前主机可用RAM约16.64GiB、盘约337.03GiB只是2026-10-26快照；上轮299272KiB/1.14秒只测组装。NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、预测HOLD。
- 下一动作/权限：仅审并准备失败向量保留、真实进程接线、逐项资源记录和预条件/诊断顺序；参考协议须另审冻结并取得用户运行授权后才能计算。当前无需用户在终端执行命令。

## 第一篇：待审可调用求解候选与结果记录合同完成静态审查，仍未求解（2026-10-25，历史准备入口；最新结论见上方）

- 用户授权继续审查“可调用的求解代码和结果记录方案”，同时确认既有预检、仍不求解。新入口 `CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/solver_result_review_20261025/README.md`、`candidate_solver.py`、`record_contract.json`、`evidence/static_review.json`和`independent_review.json`。前一9项真实组装/压力预检独立结论保持PASS，本轮读取确认而未重复组装矩阵或进行PDE求解。
- 原`solve_entry_review_20261025/entry.py`只到组装/零空间登记，无KSP/solve与结果写出。新独立候选函数显式列GMRES+无预条件器的诊断路径、KSP报告与真实`‖b−Ax‖/‖b‖`分离、收敛失败拒绝、周期回填后P1面积去均值；唯一solve调用位于`check_release`后。当前18项冻结白名单`execution_authorized=false`，9个混合问题静态调用门禁均在创建KSP前拒绝；新/旧候选源码均未执行求解，无KSP实例、正式run_id、场、通量或求解退出码。无预条件器方案未证明最细104943矩阵的时间/内存可行，不是生产解法冻结。
- 本轮静态建网/空间9项核原P1压力与MPC重建空间自由度顺序逐点相同，最大坐标差0；本机PETSc相关API存在但未构造KSP。新审查脚本避免上轮接口目录`inspect.py`潜在遮蔽标准库。独立无后端复核9项静态映射/9项冻结拒绝/一处受门禁solve调用、旧4233路径及上轮接口包19文件哈希均通过；这不是求解分支的运行测试。
- 新`record_contract.json`为`DRAFT_NOT_APPROVED_NOT_A_RESULT`，列求解前10组、求解后16组和失败时6组必备证据：输入/版本/网格/周期/参数绑定，独立退出码和完整日志，原始双精度网格与场、真实残差、压力原值与面积去均值、周期迹、通量、能量、资源/哈希及独立验收。实际run_id、exit、原始结果与真实残差仍全为空。独立运行器、写出器、泛函提取/验收及9项标量求解路径未实现；原DRAFT_v2与候选阈值未启用，运行预算未验。NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、预测HOLD，G4 v1和旧网格FAIL保持。
- 下一具体动作：若继续准备，先审可行的预条件/资源与独立进程日志/原始结果写出，再形成可复核的运行版本和独立验收器；仍需新协议/运行授权才可启动矩形求解。此轮无OpenLB编译/推进、PDE求解、重拟合、Git提交或推送。


## 第一篇：首批中网格6项独立验收PASS的历史证据（2026-10-24；最新网格结论见顶部）

- 用户授权整批结束后独立验收。本批development_grid_mid6_20261024_v1北京时间12:35:37→16:30:44完成，14107.606463秒；批次与6项独立exit均0。当前入口docs/reports/D4_grid_mid6_acceptance_20261024/REPORT.md、verdict.json和independent/certificate.json。旧运行中/4项快照保留，现以本段为准。
- 冻结验收程序scalar/flow/总分析exit均0：重算91200行诊断与66906个4050步完整窗，核首个停止点、J/K/R/切片/守恒；6项数值/几何/来源/输出阶段PASS。最坏质量1.36360595e−11<1e−10、密度8.75048167e−9≤1e−6、Mach2.49781115e−7<.05、std9.99843736e−7≤1e−6/span4.97540473e−6≤5e−6、末截面1.61014454e−7≤1e−5、cross1.39589343e−20≤1e−12。原RESULT_PASS=false和原manifest/completion中pending快照不改，独立结论另存。
- 独立三网格六方向累计4391424节点/1067136壁面连接、q=.5、无fallback/unresolved；61完整帧/128引用文件实际读取通过，节点集合不变、字段有限、通量匹配在Float32界内，最大主相对差3.26135295e−9，末态与CSV舍入后逐值一致。标量分析峰值79096KiB/2.00s、流场1037968KiB/49.09s；分块std工作区8359200字节≤16MiB预算。
- 240本批原始文件、3397 release绑定、3404去重manifest/库绑定保持；统一保护3638路径前后哈希相同（集合重叠不相加），OpenLB HEAD与G4锁/14绑定保持。本轮未编译、启动或重跑求解器，未改协议/门槛/旧FAIL、未拟合或推送GitHub。
- 粗6+中6已来源绑定导出，三格比较因缺1.25nm六项返回INCOMPLETE_OR_REFERENCE_INVALID。描述性5对2.5nm差：h75/d25/w60的KP/KT/A=0.919906%/1.606273%/0.675517%；d120/w60=0.954085%/1.587959%/0.623966%；d120/w240=0.228374%/1.085936%/0.848350%。横槽1.09–1.61%差异是5nm参考敏感性风险，不能称网格独立，亦不提前当5对1.25的最终目标FAIL/PASS。
- 本节历史验收覆盖中格6项；当前开发网格10/12已数值/场验收，两窄槽三格FAIL，尚缺宽槽最细两项，详顶部；原基础8/主开发16/额外线性4验收保持。中6通过满足下一批的上游条件，窄槽4项已完成并数值/场独立PASS，但两窄槽三格目标FAIL，以上方入口为准；后续宽细/预测停止。宽细22GiB/多日预算未解决，预测16+4仍关闭；G4 v1锁保留，重拟合另立模型v2并在保留结果前冻结。

## 第一篇：D4余14项已完成并独立验收PASS，开发细格与预测仍未进入（2026-10-24，当前入口）

- 2026-10-24北京时间12:11:55再次复核：批次/14项退出码仍0，3155个保护路径与36份验收产物哈希全部一致，原独立PASS保持。证据docs/reports/D4_remaining14_reconfirmation_20261024/verification.json；本轮无新增计算或数值分析，不重复验收、不推进细格/预测。
- 用户授权独立验收14项原始结果及流场。批次development_remaining14_20261024_v1北京时间11:39:59→11:55:52结束，953.632694秒；批次及14项独立exit均0。独立报告docs/reports/D4_remaining14_acceptance_20261024/REPORT.md与verdict.json。旧“运行中/9项”是历史接收快照，当前以本段为准。
- 独立重算48,849行诊断与34,681完整1013步滑窗，14项数值/几何门槛通过；原RESULT_PASS=false完整保留，本目录另记阶段独立PASS。最坏质量2.8563681e−12<1e−10、密度3.0756491e−8≤1e−6、Mach4.3561726e−7<.05、末窗std9.99970999e−7≤1e−6/span4.97528672e−6≤5e−6、末截面2.57115771e−7≤1e−5、末窗cross3.19670987e−21≤1e−12。
- 7几何14方向独立核累计1,255,104节点/691,488边界连接，q=.5且无fallback/unresolved。读取全部141帧及296引用文件，节点集合不变、字段有限、通量积分均在Float32舍入/求和界内（最大主相对差8.55705776e−9），末态与CSV舍入后逐值一致。未到达未来计划帧明确未达到，不补造；不声称全时刻完整场或能量/机制验收。
- 552本批原始文件、2611条release键记录、2617份去重manifest/库绑定保持，统一保护集合3155路径哈希前后相符（集合重叠不相加）。OpenLB HEAD882924a9cfc8dcdf82909e39530789cb6f5ebcc4；G4候选锁及14绑定文件保持。分析中断后仅重做只读VTK分析；额外审查器命令格式假设订正已保留失败日志，不是原仿真FAIL。本轮无求解器启动/重跑/编译、门槛修改、拟合或GitHub推送。
- 结合原已验收筛选6项，主开发16/16、额外驱动力4/4齐全；基础8项验收保持，本轮对既有证据仅核哈希。开发细格当前6/12（中格本轮验收见上方），三格空间精度尚未验收；预测16+4仍未进入。当前阶段通过不等于完整D4、最终公式或预测运行放行。
- 中格6项已完成并独立验收PASS，以上方本轮入口为准；当前开发网格10/12已数值/场验收，两窄槽三格FAIL，尚缺宽细2项，停止后续阶段。G4 v1锁保留；若新开发数据重拟合须另立v2并在取得保留预测结果前重新冻结。原启动缺陷与历史快照保留，其他第一篇/第二篇内容不改。

## 第一篇：G4主候选v1已冻结，双向权衡与参数稳定性审查完成（2026-10-24，当前入口）

- 用户授权“审查两方向精度权衡与参数稳定性，确定最终候选及预测冻结规则”。入口 `docs/reports/Correlation_selection_freeze_20261024/REPORT.md`，具体合同 `FREEZE_RULES.md`。本轮确定G4为下一轮主候选；G6比较、MIX7探索对照。候选冻结不等于科学有效性通过、老师已批准或D4运行放行。
- 独立重算120条G4/G6留组预测并回查旧原始K，最大相对差4.44e−16；110个去重输入哈希保持。训练仍w120、h50/75/125、d25/50/75/100/120nm的15几何30方向、dx5；未新拟合、未加入未验收新开发数据，h25仍为已知补充。开发s范围应为0.96–2.4，草案1.6–2.4不准确。
- 两方向/两检验等重MAE G4/G6=1.378484%/1.482027%；最差单方向MAE=1.997849%/3.562852%。G4沿槽更准，G6横槽更准；P权重分界0.445896，不能说唯一最优。G4各向异性A的留h/留d最坏6.35787%/5.93192%，弱项保留；G6分别4.12145%/3.48102%，但留h的A平均误差更大。
- 8个删层模型的pP范围：G4 0.05–0.729325，G6 0.05–1.171023；留h触下界2/3与3/3，触界按距边界<1e−5重核。计划保留几何的沿槽最大预测偏移G4/G6=2.67729%/5.04361%，横槽=.50894%/1.02562%；不是精度界或置信区间。优化起点一致不能替代参数约束充分；沿槽Jacobian条件数以T固定，不能当完整联合辨识结论。
- MIX7沿槽完整G4+横槽G6，实际需7参数；其A旧留组MAE最低，但没有跨式KT≤KP解析保证。原草案有限扫描不能称风险已排除，直接更换G4内部T又是未经拟合的新式。本轮保留草案原样、报告指出纠正，不把事后挑方向当独立验证。
- 锁 `candidate_lock.json`，ID `G4_candidate_prediction_v1_20261024`，SHA256 `08ae91994910e98afd701143928a5186a9b22d003c96f73d9643c2eb11d810dc`。绑定模型/系数/规则/预测等14文件；16主方向+4细格参考×3方案=60预测行，8主几何×3方案=24个A。`verify_lock.py`退出0，独立标量重算最大相对差4.44e−16，内存缺失/篡改两测试拒绝。模型锁只在本目录，不是旧D4 runner的release。
- 前瞻新目标采用草案3%/5%建议：P、T、A各自MAE≤3%、max≤5%，六条件全满足；不是老师原话或既有数值阈值，G4现有CV的A已超过5%，不掩盖失败风险。先核验完整来源/独立exit/原数值与几何协议，缺失或无效参考不判完整预测PASS；细格证据另列，不以细格替换粗格主分数，不把5nm一致性升级为全域物理正确。
- 正确时序为先锁候选/系数/逐点预测，再审前置条件和运行许可，由用户计算后独立验收；原草案“盲测PASS后锁”被纠正。本轮未读保留结果，不声称外部人员从未看过，运行前还须核验生成时间与接触记录。任何重拟合或规则变化另立v2，已见数据不得再次称盲测。
- D4余14主开发启动目录缺陷已修正，当前以顶部D4独立验收为准：筛选6项PASS，余14已独立验收PASS；主开发16/16和额外线性4/4齐全，开发细格尚缺12项；网格比较草案保留，网格/预测执行未放行；不自动启动或跨阶段。无新OpenLB run_id、求解器修改/编译、原协议/运行许可改动、Gate升级或GitHub推送；旧FAIL、其他第一篇与第二篇内容保持。拟议目标域仍φ=.5、P=2w、s[.8,3.2]、t[1/3,1.6]，未获全域精度保证。

## 第一篇既有稿：方法承诺收紧与补充材料编号完成（2026-10-24）

- 用户授权“按报告中的三处候选句收紧方法承诺，并将支持资料索引对应到正式补充材料编号”，已完成。正文 `docs/reports/SIM240_中文稿_导师审阅版_20261022.md` 的§2.1收紧历史构建复现承诺和52项统计范围，§2.4将线性检查限定于h75/d100、dx2.5nm及被检力范围；同步前指和附录相关句。§2.3已修正的机制解释保留，摘要、§4—6、公式和原表数值未改。
- 补充材料入口 `docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md`；原支持索引S1—S11与补充材料S1—S11一一对应。`SUPPLEMENT_NUMBER_MAP.csv`给出锚点和正文位置；表S1—S4分别为52项D2/D3清单、8行双网格、18行指定基准周期/多力和9行历史三网格。正文已引用具体编号，原 `Methods_support_audit_20261022/SUPPORTING_MATERIALS_INDEX.md`增加同一对应表。
- 本轮证据/核对入口 `SIM240_Supplementary_Methods_20261024/REVISION_NOTE.md`、`verification.json`；`verify_revision.py`退出0，28项检查通过、79个本地链接无断链、213项选定读取输入哈希保持。表S2变化、表S3线性/复制聚合及表S4平板误差独立复算与所列值一致。前稿、原索引、差异和首次脚本检查记录保留；原审计20项/519输入为上一轮记录，没有将其冒充本轮全量重验。
- 限制保留：52份manifest有二进制哈希，不等于历史源码、编译配置和OpenLB依赖绑定完整；48独立日志+4加密共享批次日志。h25仅5格，双网格差值不是误差界；历史1.25nm横槽FAIL/exit3和方案C初始formal_reference_accepted=false均保留。P/w有设计版图入口，非加工后实测；5nm历史成本依据、未闭合文献与图件检查不因编号完成而闭合。
- 本次授权任务已完成，无新OpenLB run_id、编译、仿真、拟合、源码/原始结果/冻结协议/阈值修改、Gate升级、远端同步、发布或投稿；submission_ready=false。并行D4、候选G4/G6与第二篇状态保持，未读取或轮询新运行。本稿补充材料仍是本地作者审阅版本，不能据此声称公开包已覆盖。
- 当前卡点是历史来源/文献/图文等既有证据限制，不妨碍本次文字与编号交付；后续若开展全稿终审，先从本轮REVISION_NOTE核剩余项，具体范围按用户授权。没有新增长计算授权，不自动进入D4后续阶段或预测计算。

## 第一篇§4及摘要、讨论、结论已同步（2026-10-22）

- 用户授权“按候选稿订正§4，并同步摘要、讨论中相同的趋势与机制表述”，本轮已完成。当前导师审阅入口 `docs/reports/SIM240_中文稿_导师审阅版_20261022.md`；变更/接续 `docs/reports/Section4_sync_20261022/REVISION_NOTE.md`，前稿快照/差异/编辑记录齐备。
- §4已原样采用上一轮候选稿；摘要、§5.1/§5.3、结论和引言直接对应语句统一限定：沿槽偏差并非随h全程单调下降；d100/h25→50有139.14%→154.24%反例；h125增深收益仍39.2%；3.05倍为模型值/参考值而非相对误差三倍。串并联、剪切、台阶重分布及h缺项均不被认定为唯一已证机制。
- 全18点与子集口径已同步：沿槽最大绝对残差10.5%；跨槽18点18.7%，h≥50的15点6.9%；(25,100)跨槽5nm参考下+16.36%→−18.71%为局部变差，2.5nm参考下+21.76%→−14.94%作对照。45°的9.20°差明确来自两组主值重建，回顾性评价限定保留。
- `verify_sync.py`退出0、24项检查通过；方法/§3、§5.2、书目保持，7编号公式数学内容一致，1—7式/1—8表/1—11书目编号连续，§4与候选一致；66项输入（含52原始结果及前轮审查产物）SHA256全匹配。沿用前轮已核数字，不重复仿真或优化器。
- 本轮无新OpenLB run_id、编译、仿真、原始数据/源码/协议/阈值修改、Gate升级、英文同步或投稿。submission_ready=false，历史FAIL与第二篇状态保持。5nm历史成本/参数来源、历史构建与文献/成品图等缺口未因此闭合。
- 本次授权任务完成；接手以当前稿与本轮REVISION_NOTE为准，前轮§4未改/候选待写入为历史停点。后续全稿或图文终审另按实际任务进行，无新增长算授权。
- 方法章复读评估（2026-10-22）为历史停点：§2.3速度解释已于2026-10-23订正，方法三处承诺与补充材料编号已按上方2026-10-24入口落实；剩余证据限制以该入口为准。

## 第二篇论文：C v2运行入口已复查并准备交付，尚未启动（2026-10-27，当前入口）

- **本轮授权与停点**：用户要求按新版本复查输入与资源、准备C独立运行入口，不自动启动。已完成只读检查、命令语法核对和交接；没有求解器调用（含零步）、编译、tmux新会话创建或正式C run_id。当前COMMAND_READY_NOT_STARTED，不把命令交付写成已启动。入口`CASE/09_dynamic_liquid_gas/alpha_c_validation_20261022/c_execution_binding_v2_20261024/CURRENT_STARTUP_20261027.md`，明细`launch_preparation_20261027/STATUS.md`、precheck_resources.json、NEXT_COMMAND.txt。
- **当前证据**：北京时间2026-10-27 17:59:31，新runner默认只读预查exit0、验收--check-inputs exit0，3808项绑定一致；新旧C预定output/evidence批次目录均不存在，单次ps无coupled_check，计划tmux会话`sim240-c-v2-20261027`未占用。动态库无缺失，二进制可执行；未重复23项旧测试或重编未改物理程序。可用磁盘336.52GiB（需12GiB）、MemAvailable13.05GiB，为快照非预留；正式耗时/峰值RSS仍未知。
- **独立运行命令**：已在NEXT_COMMAND.txt保存唯一tmux后台命令，指定当前本机C v2绝对工作目录、`/home/dell/miniconda3/bin/python -u run_c.py --run`。bash -n与分词核查exit0，未执行；stdout/stderr追加到launch_preparation_20261027/runner.log，逐项独立日志/exit仍由runner记录。下一动作由用户在这台Ubuntu电脑的普通终端手动执行一次；AI交付后停止，不自动启动、轮询、重跑或分析。
- **绑定/物理边界保持**：执行ID C_BINDING_COMPAT_20261024_v2，固定batch_id alpha_c_20261024_binding_v2_c仍只是预留。新binding SHA61b1bd4f…，原binding/alpha验收不改，精确接受已审查AGENTS变化；旧runner拒绝不被覆盖。四组64³/64步、原物性/源项初始化/输出/判据保持，Q/质量1e-9不豁免。已有本构相量/目标质量首步超限预测仍为预测，非实测FAIL；三类正式Gate均NOT_EVALUATED。
- **完成后的接续**：用户反馈计算结束后另开验收，核总/四项独立退出、完整manifest、输入哈希、每组65帧及首步三阶段分布，再按本v2验收入口和旧数值函数分列实现、物理漂移、安全性；不把exit0/目录/会话消失当PASS。不重复alpha，不用旧NEXT_COMMAND；不自动进入细格C/alpha16/D/静滴/润湿/K。准备/测试历史见下方2026-10-24入口，原冻结文档为当时快照。第一篇并行内容保留，状态同步/保护见本次launch目录state_sync.json和final_integrity.json。

## 第二篇论文：C独立执行/验收绑定v2已实现并预查通过，未启动（2026-10-24，准备依据）

- **本轮授权与停点**：用户授权“按独立设计处理C执行与验收绑定，保持物理输入和判据不变，不启动计算”。已在`CASE/09_dynamic_liquid_gas/alpha_c_validation_20261022/c_execution_binding_v2_20261024/`完成；入口`PREPARATION_REPORT.md`、`PROTOCOL_ADDENDUM.md`、`README.md`。未调用求解器（含零步）、未编译、未启动C、无正式C run_id，无启动命令交付、Git提交/推送或Gate升级。
- **实现与冻结**：新增binding.py/run_c.py/analyze_completed_c.py以及精确兼容声明、物理合同副本和一次性freeze_execution。执行ID`C_BINDING_COMPAT_20261024_v2`，固定新batch_id`alpha_c_20261024_binding_v2_c`只是预留，正式output/evidence均不存在。新`execution_binding.json`合并去重3808项，SHA`61b1bd4fff26a0fcd0e6e0c4601d3182b15148ea8955b69d1ceb3874f50fb4ae`；运行和完成验收共用同一verify_binding。原程序和analyze_c.py原字节复用，物理未改，无需重编，不冒称新编译。
- **唯一管理兼容**：父binding SHA a3409a57…、原alpha canonical verdict SHA018467d3…与EXPORT_PROVENANCE均未改；只接受已审查AGENTS旧5700b378…→当前59d1cc51…，重建旧文本/精确diff/current三者互核，未来其他变化仍拒绝。其余3400项旧绑定匹配，alpha391验收输入和392原始文件核对保持。原run_suite C默认预查仍按旧绑定exit2，保留其拒绝，不将旧3401写成当前全部匹配。
- **物理合同保持**：新physical_contract逐字段等于父protocol中的4组C、backend/material/完整thresholds/c_output。仍64³/64步、dx2.5nm/160nm、alpha1/tau_CH1、NS tau[1,1.25]，初态/源项启动/每步16字段及首步三阶段分布保持。Q/质量1e-9、实现1e-12、安全条件全部继承；没有解释后豁免。旧预测本构equal/target的DeltaQ/Q约−2.36935e-9/+8.29233e-9、target质量−8.27245e-9仍预计超限，非实测C FAIL。
- **已验证的准备证据**：freeze exit0；新运行默认只读预查exit0、新验收--check-inputs exit0。test_binding.py 23项/0失败/exit0，覆盖内存输入篡改拒绝、alpha依赖/绑定项完整、默认不执行不创建、完整来源fixture及缺帧/退出码/零步/错误batch拒绝、原数值加载器拒绝假数据、预算失败不豁免、假进程非零停止。另一个隔离元数据端到端测试exit0，明确替换数值回调，不做物理计算，验证预算失败使验收返回1且Gate不提升。见preparation_evidence/日志/独立exit及preparation_verification.json。
- **尚未验证**：实际C完成数据不存在；完成分析入口按预期exit2并未创建verdict，不能把预查或fixture称C验收通过。未来真实数值仍由原analyze_c.py核全程原始数据；无完整耦合、平衡、K、Laplace/润湿新证据。三类正式Gate均NOT_EVALUATED；alpha历史纯CH算子合同保持有限范围。跨机器运行未验证，正式耗时/峰值RSS未知，当前预查不预留资源。
- **运行/验收接续**：新runner默认只预查；将来明确--run才可能调用原程序，锁后复查，逐项独立日志/exit，非零停止，前后哈希，无覆盖/恢复/重跑/自动后处理。新验收核匹配manifest/新binding/父协议/alpha依赖、完整4项/独立exit0/65帧/首步三阶段分布，再原数值分析；实现、物理预算、安全性分列，原始输入读取前后核SHA。新路径不写旧alpha或C目录。
- **接续更新**：该实施准备任务完成。用户已于2026-10-27要求运行准备，新的输入/资源核查与命令交付入口见上方；命令准备不等于启动。旧物理/协议/门槛/alpha证据未改，C没有自动开始，后续仍由用户独立运行后另行验收。

## 第二篇论文：alpha空间批次完成并通过冻结算子合同（2026-10-23，已验收依据）

- 同日追加复核：`CASE/09_dynamic_liquid_gas/alpha_c_validation_20261022/reconfirmation_20261023/verification.json` 记录再次实核总/16项独立exit0、规定步序、3401冻结输入/392原始文件/33分析产物/391规范判定输入SHA全部相符（集合重叠不相加）；既有alpha合同PASS保持，无新计算或重新数值分析。该任务在回贴后由用户转入第一篇公式审查，此处补齐交接。

- **本轮范围与停点**：用户要求对独立运行后的alpha核对退出码、完整数据及输入哈希并验收；本轮仅读取和处理已完成结果，没有启动/重跑、编译任何求解器，没有启动C。正式批次`alpha_c_20261022_v1_alpha`已完成，原17:12 intake“未找到”及用户“尚未启动”均为运行前历史快照，不再是当前状态；原始记录保留。
- **完成证据**：北京时间2026-10-23 17:29:46.378488→17:31:27.376847，实测100.998359秒；总批次及16项独立exit均0，完成步数/配置/子与总manifest一致。10线性粗128/细512步、4本构粗16/细64步、2源项单步齐备。根目录`CASE/09_dynamic_liquid_gas/alpha_c_validation_20261022/`，总manifest位于`evidence/alpha_c_20261022_v1_alpha/manifest.json`，全部run_id及原始文件见`analysis_20261023/raw_input_hashes.json`。
- **当前验收入口**：`analysis_20261023/REPORT.md`、`independent_review.json`、`case_summary.csv`、`alpha_diagnostics.png/pdf`；规范落盘为`analysis_alpha/verdict.json`，附`EXPORT_PROVENANCE.json`。`operator_contract_pass=true`，16/16算例、7/7矩阵检查通过；NUMERICAL_GATE、RESULT_PASS、geometry_PASS均保持NOT_EVALUATED，不是完整两相物理Gate通过。
- **导出缺陷保留**：原冻结分析器数据检查后JSON输出遇numpy.bool，exit2，日志保存在`analysis_20261023/frozen_analysis.log`；未改冻结源码。独立进程适配仅将10个numpy.bool转Python bool，原公式/阈值保持，适配分析exit0；另写不导入冻结数值helpers的独立复核exit0。两套结论一致，连续率误差最大绝对差3.71e-11。重核输入后才逐字节复制适配verdict至此前缺失的规范路径，不删除原失败，不冒称原分析器exit0。
- **输入与数据**：3401项冻结绑定SHA256全匹配，392份原始运行文件另存读取前后哈希。独立核200份三维CSV/4,919,296行场数据/3,374逐步记录，有限值、坐标唯一完整、行数步序配置均通过。OpenLB1.9.0，绑定HEAD882924a9cfc8dcdf82909e39530789cb6f5ebcc4。保护/最终核查见`analysis_20261023/protection_before.json`与`final_integrity.json`。
- **衰减/方向/细化**：同40nm物理盒，dx2.5/1.25nm、alpha1/4、tau_CH1，M_SI1.7361111111e-17、W10nm及sigma.03保持。固定窗粗32..128、细128..512。连续率误差轴向1.785058%→.449222%，xy3.943929%→1.004349%，xyz6.214608%→1.593822%，满足预定7%/2%，五方向均下降约3.90～3.97倍；不改旧B1的5%/2%。实测率/离散率最大相对差1.40841e-8，轴向归一化spread粗2.88499e-9/细1.22877e-8，均通过。两格不是GCI，波矢模长不同不直接解释为物理各向异性。
- **全程漂移/本构**：14无源组全程最大abs(DeltaQ/Q0)=2.1163192726e-13，`linear_n32_y_a4`第511步，末步2.1084262808e-13，低于1e-9；这是纯CH相量而非完整NS物理质量。4非线性每步全场mu残差0，最大更新5.91112e-16，独立能量余额/节点最大1.62370e-21，均低于1e-12。源项两组DeltaQ约−.01107381215，符合−sumS，最大全局余额/节点5.51732e-17；不计为无源漂移。线性全程L2仍是程序内观测，仅初末完整场可离线独立复核。
- **实现/准备背景**：CH_ALPHA只进入CH平衡分布，不全局缩放原CHEM_POTENTIAL；源项修正及共享库哈希保持。此前4个binary编译、CH59184/NS3240局部检查与20项零步初始化证据仍有效；旧A/B/实际谱3045项保护和历史FAIL保持。原PREPARATION_STATUS/README为绑定准备时快照，未改字节，以本段和验收报告更新当前状态。第一篇并行入口前缀在本轮同步时原样保留，见`analysis_20261023/state_sync.json`。
- **C当前状态**：预定正式C批次manifest不存在，本轮未调用C runner或交付C启动命令。已有4项64³/64步、dx2.5nm/160nm、alpha1/tau1，等密度/目标密度×mu0/真实本构，NS tau[1,1.25]；预留12GiB、约9.68GB原始输出为准备估计，正式耗时未知。alpha依赖现已通过，但不等于用户已授权启动C。
- **C问题与接续**：原初场预测和运行前条件审查现已于2026-10-24完成，最新结论见上方C审查入口；新增目标组质量预测−8.27245e-9，实际C预查因AGENTS管理规则变化exit2，原绑定未改。alpha历史合同保持，C尚未运行；后续需独立执行/验收版本承接，不自动进入任何新计算。

## 第二篇论文：实际CH离散精度与C参数选择完成（2026-10-22，接续依据）

- 最新入口 `CASE/09_dynamic_liquid_gas/actual_mobility_review_20261022/REVIEW.md`；参数方案 `C_PARAMETER_PLAN.md` / `c_parameters.json`，独立静态脚本 `static_review.py` / `spectral_rates.csv` / `static_results.json`。本轮仅静态谱与初始数组计算，没有OpenLB run_id、时间积分、代码编译、C运行或新长算命令。旧A2+B冻结合同PASS及全部历史FAIL不改，三类正式Gate仍NOT_EVALUATED。
- 主模型mu_l=.010Pa·s已同步未冻结机理方案/design/模型证据表；rho_l1000、rho_g1.2、mu_g1.8e-5、sigma.03、W物理10nm。dx2.5nm时dt1.04166667e-13s、tau_NS气1.25、sigma*2.08333333e-5、beta*6.25e-5、kappa*1.25e-4；tau_CH1/alpha1对应新M_SI1.73611111e-17m²/(Pa·s)，较历史12mPa·s映射大20%，是明示模型选择，非GHY或实测迁移率。
- 关键实际谱：同L160nm、同M/W/sigma，dx2.5→1.25→.625nm且alpha1/tau_CH1→2.5→8.5时，40nm波长连续衰减率偏差−1.447%→−12.913%→−38.096%，不能当精度细化已通过。495项19×19谱与tau1精确式、轴向弱A式/60位独立方程交叉核对。保持tau1而alpha1→4→16的候选偏差改善，但本机新alpha类型未实现/编译/验证，不能直接运行细格C；不得全局缩放CHEM_POTENTIAL而改变NS毛细力。
- C首批参数已选择：64³/160nm/dx2.5nm，每项64步(6.667ps)，RHOS等密度[1,1]或目标[1,.0012]，各做人工mu0与实际本构，共4项；TAUS均[1,1.25]。等密度对照保持运动黏度、并非保持动力黏度。初场mean(phi)=.5，目标气核rho_min1.20006868kg/m³、半步力Mach约7.987e-6，仅静态检查非启动验收。候选判据和账本已写，实际实现/输出核对后须新冻结执行协议；旧NS A1未覆盖tau1.25，需扩展新局部检查。128³/alpha4细格等待新alpha合同，C不测K、不验平衡。
- Cochrane2018本地11页期刊正式版核查：kr还关联相间作用、临界饱和度和可调系数，不可宣称普遍唯一kr(S)；10mPa·s来自其表1，气黏度18.6e-6与本模型1.8e-5分开。论文定位可为特定沟槽下饱和度表征的充分性检验；未分辨差异不证明S足够。K液相通量配合±差分仍是候选提取组合，观察窗/状态一致性未正式冻结，不等同标准独立相压差kr。
- 参数卡/材料策略已订正旧“12为唯一/完全一致GHY实测”“定性方向相同即量值不敏感”及“SI换算证明底噪、粗化必提高信噪比”；GHY原五点/null物性与旧12mPa·s算例、历史design_audit.json保留。保护与前稿见本目录evidence/verification.json及before/，旧3019分析输入和2636运行绑定保持。
- 该后续实现/编译/冻结准备现已按用户授权完成，见上方alpha_c_validation最新入口；本段保留先前静态选择依据。长算仍由用户启动，不自动进入C细格、D平衡、静滴/润湿/沟槽K；没有新长算授权。第一篇并行写作内容保持。

## 第二篇论文：A2＋B完整批次冻结验收完成（2026-10-22，已完成证据）

- 用户要求计算完成后核对完整证据并验收，本轮已完成。最新入口 `CASE/09_dynamic_liquid_gas/ab_diffusion_validation_20261022/analysis_20261022/REPORT.md`。batch_id ab_diffusion_20261022_v1，北京时间14:06:57.323至14:15:06.943，489.620173s；批次及22项独立exit0、完整manifest/配置/日志/规定步数齐备。
- 4A2单步＋14B1模态扩散＋4B2真实化学势短测均满足冻结合同；冻结analyze_completed.py原样exit0/operator_contract_pass=true，7项矩阵比较全部通过。18002条B逐步记录、120份规定三维场共1925120行有限且坐标完整。2636项绑定与运行前后/当前一致；3019份去重分析输入保存哈希，旧2274项保护保持。
- 独立independent_review.py不导入冻结分析/参考/求解器，以描述子、矩阵幂、3D FFT与全场重算，exit0；拟合率与冻结最大绝对差1.08420e−17，最大漂移一致。supplemental_statistics.py补核所有B端点能量/耗散定义，exit0；PNG/PDF诊断图导出并渲染目视检查。原始数据、源码、协议、参考、二进制和运行前绑定文档均不改。
- A2逐点最大更新误差独立约4.9960e−16、总账余额/节点最大9.3354e−17（限均1e−12），逐分布迁移差0。有散场sum(S)=+.01107381215286002、DeltaQ=−.011073812152812224，−DeltaQ/sum(S)=.999999999995684；此为预期源项变化，不能混进B无源守恒漂移或当漏量。单步采用S_old=S_initial，不替代多步AB/完整耦合验证。
- B1全程复模态误差/初始A最大约1.20e−12、全程观测L2/初始RMS最大2.09019e−10（限1e−8）；初末L2独立3D复核，全程场未逐步保存，不能冒称全程3D重建复核。tau1连续率误差轴向1.18705%→.297518%、xy2.41491%→.609674%、xyz3.70219%→.936498%，低于5%/2%，细化缩小3.95..3.99倍，非GCI。轴置换一致；斜波矢长度不同，不当任意方向各向同性证明。
- B2每步本构mu一致、局部更新最大5.33108e−16；每步全场独立能量收支通过。全部tau1观测能量余额/节点最大5.50360e−21；B1独立能量重建限初末，B2每步均独立。全18B相量最大相对漂移2.9553443e−13（N32/x/tau.75，step2048，末态同）；N32/x/tau2.5峰6.7092165e−14在2046步，末6.7085226e−14。只证明sum(phi)有限合同，无NS总质量验证。
- 精度限制保留：tau_CH=2.5与完整离散参考一致，但人造自由能下连续扩散率仍低估N16=36.1406%、N32=12.1976%。冻结协议对此点连续差仅描述，故合同PASS成立；不能称已验证高精度物理细化，也不能把该百分比套到真实目标beta/kappa。后续实际参数谱审查/C参数选择现已完成，见上方最新入口；本段保留A/B验收边界，不再作为待审停点。
- 已完成批次禁止重复启动。NEXT_COMMAND/README/PREPARATION_STATUS/准备verification是绑定历史快照，保留原样，当前以本入口/分析REPORT为准。本轮无新OpenLB运行、重编译或门槛修改，不自动进入C/D、静滴/润湿/K；三类正式Gate仍NOT_EVALUATED，第一篇并行写作/旧FAIL/真实GHY证据保持原状态。

## 第二篇论文：NS/CH离散收支与平衡参考审查完成（2026-10-22，接续背景）

- 用户授权本轮审查化学势扩散/完整NS-CH离散收支与平衡参考、确定下一组验证。入口 `CASE/09_dynamic_liquid_gas/coupled_balance_review_20261022/REVIEW.md`；具体设计 `NEXT_VALIDATION_DESIGN.md`。新增静态代数脚本/结果与输入保护证据；没有新OpenLB run_id、求解器修改、编译、时间推进、参考平衡求解或长算命令。
- 已核实源码并推导：周期修正CH总账 ΔΣphi=−ΣSOURCE_AB；Σ(u·Gphi)=−Σphi·div_h(u)。实现残差与物理相量漂移须分列，低Mach不能代替无散/守恒。目标tau_CH=1有精确逐节点一步式，可直接验证扩散与源项迁移；旧2000步仍是旧源项，不能当修正后结果。
- 自由能须与实际链接拉普拉斯一致。有限数组代数检查exit0，源项矩/梯度积分分部/相量总账/能量变分符合推导；人造场展示L不等于div-grad、净毛细力和能量交换不必精确相消，不能将这些反例数值当目标静滴的实测误差。NS raw动量与带半步力动量的收支不同，实际CellD/CSE证据仍待做。
- 不等密度CH扩散携带质量；所读NS路径未见显式匹配的扩散质量动量通量，完整渐近等效项与误差量级未核实，不能宣称热力学一致或据此宣布既有全部结果错误。平衡参考拟解固定总相量下mu_h=常数，再检查稳定性/保持、体相密度及机械压力；尚未求得参考场。
- 物理网格细化新增约束：M_SI=M_lu*dt/rho_ref。dx减半且dt/4时，保持物理迁移率需M_lu乘4；alpha固定1时tau_CH由1变2.5，但最新实际谱发现此路精度变差，替代alpha细化待新实现验收；不能把两格tau_CH1/alpha1当同一物理模型。W/R、有限盒、网格和迁移率变化分开。
- A＋B独立实现、编译和执行协议冻结已完成，当前运行边界/下一动作见上方最新准备入口。C完整耦合短测、D约束平衡参考/保持仍在后续分别验收，不自动串联；三类正式Gate仍NOT_EVALUATED。
- 当前保护核对：1502项source3d绑定、1772项旧算例/后端保护、1972项平移原始输入均匹配（集合有重叠，不相加）。已完成批次source3d_translation_20261022_v1保持有限算子PASS，不重跑；第一篇与真实GHY证据不升级。共享入口与本报告同步。

## 第二篇论文：三维源项平移矩阵验收完成（2026-10-22，接续背景）

- 用户要求按冻结协议分析完整矩阵，本轮已完成，最新入口 `CASE/09_dynamic_liquid_gas/source3d_validation_20261022/analysis_20261022/REPORT.md`。batch_id `source3d_translation_20261022_v1`，北京时间08:18:16至08:22:34，总耗时257.967681s；批次及36子运行独立exit0，27,036条完整逐步记录与72份三维初末场（1,327,104点）齐备有限。输入1502份绑定哈希重新核对且与运行前后记录一致；原始输入保护/独立证据见分析目录verification.json。
- 冻结 `analyze_translation.py` 原样执行exit0、operator_contract_pass=true，修正实现18条（16移动+2零速度）满足全部预定判据，16项矩阵比较全通过。旧实现18条是缺陷对照；其移动速度比N16约0.499611、N32约0.499975，复现半速不等于物理输运PASS。三类正式Gate仍NOT_EVALUATED。
- 修正速度比N16约0.974499、N32约0.993588；最坏速度误差2.5500836%→0.6412140%，低于5%/2%限，细化约减小3.97696倍。最坏末态去背景波形L2=4.0054050%/1.0072132%，低于10%/4%；振幅误差0.000469731%/0.000121941%，低于2%/1%。两级log2误差比约1.99167，不能称GCI或已验证渐近阶。
- 方向一致性：轴间速度比差约1e-14至3e-14，正反/对角与轴向差至约4e-14，低于冻结0.002限；零速度全程最大L2=9.4471e-12、静止分量相位变化约1e-15rad。对角速度仍使用轴向可分离余弦波，不能据此证明斜向波矢、曲面界面或任意界面方向各向同性。
- 全程最大相量漂移：全矩阵5.7498450e-13（old/N32/xyz-，step987），修正最大1.3489210e-13（new/N32/xyz+，step974）；均小于1e-9，末态分别-4.9305005e-13/+1.2778667e-13，未用末态替代全程峰值。此处是sum(phi)守恒，没有NS/rho，不能当真实总质量验证。
- 独立 `recompute_and_plot.py` exit0，不导入冻结分析/求解器，重算全部配置/记录、相位回归、三维FFT及解析场/L2；速度比与冻结最大差6.9944e-15，端点FFT差1.9776e-16。PNG/PDF诊断图导出并检查，数据表/figure_provenance与input_hashes保存。初版独立漂移用比值再减1造成约1e-16相消差，已改先作差再除，初版JSON/log保留，不改冻结口径或原始数据。
- 先前analysis_pending两次快照保留为历史，用户已启动且本批次已结束，禁止重复启动/重跑。本轮无新仿真、重编译、绑定源码/协议/门槛修改或自动下一阶段；第一篇与真实GHY证据不升级。
- 后续离散收支/平衡参考审查已完成，当前动作见顶部2026-10-22审查入口；仍无新耦合/静滴/润湿/沟槽K长算授权或运行，不能将本轮算子PASS作为完整两相物理PASS。

## 第二篇论文：目标物性与LP2000证据（2026-10-21，接续背景）

- 用户授权核查模型物性的OpenLB映射/两相实现并准备静滴和平壁验证，强调以第一篇为基础；当前仅理想模型支线。第一篇几何、深度积分K(m³)、x跨槽/y沿槽定义、ν—τ—Δt关系、解析q=1/2壁面与全液Poiseuille验证方法沿用；第一篇稿件/源码/数据/旧冻结协议与历史PASS/FAIL未改，不能继承两相物理PASS。
- 最新入口`CASE/09_dynamic_liquid_gas/target_prevalidation_20261021/PREPARATION_STATUS.md`；单位与实现核查`UNIT_AND_BACKEND_AUDIT.md`；诊断协议`PROTOCOL.md`/`protocol.json`；源`src/target_prevalidation.cpp`及`target_parameters.h`；`audit_mapping.py`、`mapping.json`。模型ρl1000、ρg1.2kg/m³、μl0.012、μg1.8e-5Pa·s、σ0.03N/m、两表面90°保持，均非GHY测量。
- 本机OpenLB实际HEAD882924a9…、CITATION自标1.9.0；编译OLB_VERSION=9bad48a-dirty不作为库版本。每次诊断manifest记录全后端src树、库、配置、源码与二进制哈希、完整命令/日志和独立exit_code。共享OpenLB库未改。
- 映射核算Δx2.5nm、Δt8.68055556e-14s、ρ*=[1,0.0012]、τ液1/气1.125、σ*=1.44675926e-5；M*=1/6对应M_SI=1.44675926e-17m²/(Pa·s)，仅代码/连续模型推导，非实测迁移率。旧静滴φ=0液/1气与RHOS/TAUS端点顺序不一致；在新副本修正，旧源码SHA256仍26331757…不变。
- 实装修正：先赋ρ等字段再建平衡分布；化学势/耦合前从实际分布刷新STATISTIC/PHIWETTING；解析平壁求交；周期轴N节点使用0..N−1；均匀体积力BODY_FORCE与加速度EXTERNAL_FORCE分清；耦合除ρ前拦截非正密度（ρ*=1−0.9988φ），无φ截断/质量归一化。压力输出p_h和体相机械压力候选p_h+φμc−f0，正式Laplace需再核压力张量/核心取样与末态半径。
- 已验证有限范围：`evidence/build_v4_exit_code.txt=0`；四项零步run_id `target_{lp,ca,fl,fg}_init_20261021_v4`独立exit0，无collideAndStream。LP262144流体点；CA159744点/40960壁links；FL/FG各7680点/2560links，安装与解析q=1/2一致、fallback条件0；ρ/τ映射误差0。初始CA拟合89.9952°仅初态检查，非润湿验证。独立复读`evidence/preparation_checks.json`通过。
- 开发失败保留：v1 CA/FL/FG通用求交q偏差1.2207e-4，link审计exit4；v3 CA/FL/FG相场缓存差1/6导致ρ映射错误、CA/FG负密度，exit3。对应源码快照/日志/raw均保留；v2只编译。旧STEP6G/R2/移动壁历史FAIL与旧R1记录不变，不用新准备抹除。
- 200步结果已独立复核（2026-10-21）：run_id `target_lp_pilot200_20261021_v4`，独立exit0、201条step0..200、25.174891s，1494个绑定文件中1485个为后端src。启动阶段正密度/有限性成立；完整压力p_h压差−0.413349至3.420247MPa，未稳态，Laplace仍NOT_EVALUATED。审查入口`target_prevalidation_20261021/pilot200_independent_review/REVIEW.md`、`recompute.py`、`recomputed.json`；原PILOT200_ANALYSIS.md保留，错误读数不继续当证据。
- 订正关键数：液体量最大绝对漂移3.8026695e−6（step110）、末态−3.6459651e−6；总质量最大3.7366240e−6、末态−3.5826412e−6，均不是1e−10；Mach峰3.4733464e−5（step3）、末1.8466605e−6。末50条峰峰/均值184.659%；末40条213.093%，106.547%是半幅/均值。微小漂移不能直接称浮点舍入，0壁links只核LP无壁设定。中截面初末形态接近，不证明全程3D不变形。
- 压力解释订正：SI换算同时放大信号与扰动，不改变两者比值，当前只证实确定性启动振荡，未测得数值底噪；0.510上升比例不能单独识别振荡，峰谷周期45–49步才是直接证据。包络拟合用4峰/去早期峰分别τ约619/424步，408不是唯一已识别时标；声学机制仅候选，不能承诺相关瞬态样本按1/√N降误差。体积等效R16.203→参考1.481MPa，φ=0.5轮廓R15.9969→1.5003MPa，半径/机械压力口径仍待定。
- 用户已明确授权并完成**独立2000步诊断扩展准备**（2026-10-21）：新入口`CASE/09_dynamic_liquid_gas/laplace2000_extension_20261021/README.md`、`PROTOCOL.md`/`protocol.json`、`run_diagnostic.py`、`analyze_completed.py`。旧200步完整目录211份文件SHA256本轮保护不变。新run_id `target_lp_diagnostic2000_20261021_v1`，仅laplace、从0到2000，无checkpoint；物性/网格/初始化/几何/碰撞耦合保持，源码差异仅入口限制、长度和每250步截面输出。输入及判读口径已冻结，正式Laplace未放行。
- 扩展编译`evidence/build_exit_code.txt=0`；新零步`target_lp2000_initialization_20261021_v1`独立exit0，初始截面与旧200步初态逐字节相同、step0所有CSV读数相同，262144流体点、LP无壁links且审计无异常。三个后处理定义测试exit0；4项入口防错检查通过（含拒绝非LP/非0或2000步、既有目录）；`evidence/build_binding.json`/`final_preflight.json`确认启动前绑定。零步检查没有collideAndStream，不是新2000步运行或物理Gate通过。
- 扩展判读固定step1501..2000（500条）、1751..2000（250条）及相邻250条半窗：两压力定义分别统计均值/峰峰/归一化/线性趋势；全程守恒最大漂移与末态分列、密度/Mach/φ/映射/有限性；每250步轮廓/化学势截面，轮廓和体积半径分报、包络区间敏感性。后处理不自动判压力收敛或正式PASS、不预设1.481/1.500MPa目标。
- **2000步结果分析已完成（2026-10-21）**：run_id `target_lp_diagnostic2000_20261021_v1`，独立exit0/manifest完成记录/result2000/2000一致，完整2001条step0..2000及9个预定4096点中截面齐备有限；实际耗时254.665109s（4分14.7秒）；1497个绑定文件当前全部匹配、运行前后记录未变，前201条CSV与旧200步逐字段相同。最新入口`laplace2000_extension_20261021/analysis_2000_20261021/REPORT.md`；冻结后处理`frozen_analysis.json`和独立`review_and_plot.py`/`independent_checks.json`均exit0，PNG/PDF诊断图已导出并检查。旧analysis_pending保留为运行中历史快照，不再是当前停点。
- **诊断结论**：全程液体量最大绝对漂移3.8026695e−6、总质量3.7366240e−6（均step110），末态−2.8079206e−6/−2.7591519e−6；最小ρ*=.0012、无适用列非有限、最大Mach3.47335e−5、映射误差0。压力Δp_h末500/250步均值1.4214698/1.4181095MPa，均值差−0.2364%；相邻250半窗均值差−0.4728%；峰峰占比13.6425%/8.3563%，回归窗变化−0.7514%/+0.3749%。机械压力候选判断相同。早/晚各250条峰峰降32.35倍，固定包络拟合完整/后半τ约504.25/503.88步，中位周期45步：确认启动振荡衰减，尾窗均值较一致，但仍不能判静滴平衡。
- **未闭合问题**：末态最大速度0.0169524m/s（尾500最大.0171358），体相化学势均值液核约−49633Pa/气核−489Pa且截面非均匀；残余运动与热力学弛豫仍在。轮廓R15.99597格参考1.50038MPa、体积R16.20301参考1.48121MPa，尾均值偏差约−4%至−5.5%不等于已校准压力或唯一曲率误差。诊断安全成立，正式NUMERICAL_GATE/RESULT_PASS/geometry_PASS均NOT_EVALUATED。
- **接续状态（2026-10-22修订）**：压力/化学势只读审查发现三维源项矩缺陷，当前具体动作以顶部独立修正准备为准；不自动盲延长18万步、调σ追目标、进入CA/FL/FG或沟槽K。用户已有本次结果分析授权已完成，本轮无新求解器运行、重编译、物性/源码/协议/阈值修改；第一篇及GHY证据不升级。报告/脚本/原始输入哈希与`verification.json`提供接续证据。
- 最小机理设计仍见`mechanism_study_20261021/`：固定P240/w120/d100/h75nm、2×2周期、F全液与同Sl0.8的G_roof/G_band，成对±G与零驱动测Kxx/Kyy/A。完整沟槽机理求解器未实现，正式协议未冻结；新前置仅提供接续基础。
- 真实GHY无新增实验反馈；身份/批次、ρ/σ/两表面θ、水参与时点仍未知。原GHY转录/材料表、paired_transport配置及freeze_decision哈希与上一轮验证一致，仍未放行真实GHY预测。第一篇与真实GHY记录不被理想模型参数覆盖。

## 中文重写稿v2停点（2026-10-19，用户认为旧稿写得不好）

- **当前阅读入口**：`SIM240_EJMB_中文重写稿_v2_20261019.md`。按用户反馈实质重组为“槽深/间隙的方向响应→局部立方律偏差→经验修正范围”，汉字约4074（旧12158，均不含数字/公式/英文）。EJMB定位不变，不覆盖其他工作流的选刊/图件/声明产物。
- **来源与修改边界**：旧中文整合稿、英文稿和源五章不改；完整原稿快照 `Chinese_rewrite_20261019/原中文稿完整快照.md`，诊断与变更 `AUDIT_AND_PLAN.md`/`REVISION_NOTE.md`，输入与核对 `input_hashes.json`/`verification.json`。V2与原闭合数学内容一致、式号仅重排；新主稿实际引用9个原编号，22书目仍在支持快照。结构迁移与过程压缩不等于删除数据/失败记录。
- **有限核对**：14项通过，检查命令独立exit0；7份输入哈希不变、快照一致、公式/引用/6个几何倍率舍入核对及关键限定保留。不是原始诊断/退出码重验，不升级NUMERICAL_GATE/RESULT_PASS/geometry_PASS，submission_ready=false。
- **限制/下一动作**：保留最薄间隙双网格、回顾性模型选择、旧T FAIL/方案C与构建来源缺口；图9/10定量传播保留支持资料，正文承诺待其链条核准后决定。下方图4/7/8最新验收不被倒退。以新中文稿核图9/10和图号，再同步英文（英文尚未同步）、补真实作者声明及科学终审；不能靠改写升级创新或预测验证。
- **执行范围**：无新run_id、源代码/图/原始数据/协议修改、编译、仿真、优化器、Gate、机制积分、两相、长算命令、投稿或对外通信，无新增长算授权。

## EJMB五项材料停点（2026-10-19，本轮核查）

- 完整附件接续：见`EJMB_submission_preparation_20261019/PASTED_GUIDANCE_REVIEW.md`及`check_citation_usage.py`/`citation_usage.json`。本机已有scientific-writing2.3、peer-review2.4、citation-management2.3、academic-humanizer0.3.3，不将商城同名v1.1.0当作本机技能，不需新装或先转bib才能查编号。英文未引用19/20/22；中文未编号引用1/3/6/7/9/10/11/13/14/16/19/20/22；22条书目均无悬空/重复编号。该离线检查exit0且原稿哈希不变，未核元数据或引用支持。CTAN核实CAS类为cas-sc/cas-dc，与elsarticle不同；figures/paper已有5组PDF/PNG/SVG，仅存在性核查。下一动作还包括按实际方法与段落核查这些未引用条目，不能为销项机械补引；未安装或改正文，无新计算/验证。
- 范围：回应五项投稿缺口；新建`EJMB_submission_preparation_20261019/READINESS_NOTE.md`、`highlights_draft.txt`、`keywords_draft.txt`、`verification.json`。4条Highlights字符数80/73/76/78，6个关键词；只是候选，未完成正式投稿件，未改中英文原稿，3输入哈希保护。
- 本轮核得Elsevier Option C确有无法共享时说明原因的例外；Zenodo可预留DOI但不等于发布。无证据支持“缺Highlights必然学术拒稿”。本轮EJMB原文403，专属初投/Word/位置等沿用已有报告待原文再核，通用Highlights时点与本刊摘录不同须说明；不覆盖前轮成功取到的历史。
- 卡点：图9/10链待核；未建立并验收数据公开包、未取得DOI；AI真实工具/用途及人工审查、研究过程用途Methods说明、全体作者利益冲突、权利和元数据均待核。不得代写无冲突或声称数据已公开。
- 下一动作：按最终图表建立公开候选清单，厘清图9/10后冻结包，作者核准具体包与元数据再发布。submission_ready=false；无新增计算或数值验证，无新OpenLB run_id、源码/协议/原始结果变动、编译、仿真、Gate升级、长算命令、仓库上传、对外通信或投稿授权。

## 中文稿停点（2026-10-19，本聊天新增交付）

- **范围**：用户要中文稿，沿本聊天已采纳EJMB推荐整理，未重启选刊或修改其他工作流候选池。新入口 `SIM240_EJMB_中文整合工作稿_20261019.md`，约1.2万汉字，摘要/引言/方法/核查/结果/讨论/结论齐备，非英文逐句对译或投稿终稿。
- **产物与验证**：`EJMB_chinese_20261019/build_chinese.py`、`新增中文段落.md`、`integration_record.json`；构建独立exit0，7输入哈希不变，公式标签唯一、22书目无被引缺项，主要误差/残差口径有限核对。未重审全部科学主张/原文或数值诊断，不升级NUMERICAL_GATE/RESULT_PASS/geometry_PASS。
- **边界**：源五章与英文稿、V2、主张台账、原始数据不改；派生中文稿同步固定单胞LBM/宏观Reynolds与体相/边界误差归因两处限定。图未嵌入、图9/10链待核，署名/真实声明待补，submission_ready=false。无新run_id、编译、仿真、优化器、长算命令或投稿/对外通信；不恢复机制收支或两相。
- **下一动作**：作者/导师先看中文摘要/第6章结论，再看第4—5章；核图9/10实际链，压缩重复并同步中英文。保留其他工作流下方选刊报告，若源稿变化须按哈希记录合并，不能覆盖。

## 选刊细筛停点（2026-10-19，本轮扩展候选）

- **用户范围**：按当前稿件筛选中科院大类二区/三区；截图明确二区P3/三区P4、发表当年目录分区、Article或Review；费用“暂不限制，先看适合程度”。项目既有稳妥与2027年3—4月录用目标沿用作规划前提，录用认定完整条文及学院2027分区版本仍待确认。
- **本轮成果**：`SIM240_journal_screening_20261019_v2/REPORT.md`，同目录`evidence/`保存检索响应/官网入口/6 DOI请求记录，`input_hashes.json`保存9份现有输入快照。按现有引言、结果、讨论、CORE_CLAIMS和候选摘要进行适配筛选，不重新数值验收。旧PoF/MEE方案保留，本报告扩展原先两刊池，不覆盖其他工作流稿件。
- **当前候选**：PoF（2025公开大类2区）为二区优先候选；新增重点三区C&F与EJM B，分别偏计算评估链和流动物理；TL/MEE为有条件应用备选；TCFD当前不优先。分区均属公开转载初筛，尚非学校认可归档。CAS2026起停发表已核，不以新锐/JCR代替中科院口径。无录用率排序或保证。
- **证据与缺口**：官网范围及代表论文核对；Crossref6个明确DOI中5成功、EJM2018首请求curl35，原失败保留，以出版社检索与高校作者表补证。不是6篇全文审读，近期全目录筛选/WoS/Scopus未做。PoF官网2025平均首决定20天/录用54天，不保证本稿；C&F/EJM/MEE普通稿官方速度未核得，具体APC未逐项核价。纠正旧方案的“经验修正非PoF类型”“PoF必须唯一补证路径”“MEE最稳”“格式保证不秒拒”等过强判断。
- **未改变状态**：submission_ready=false；V2仍数据知情事后评价，机制候选、最薄间隙双网格/全图不确定度不足及图9/10链待核。NUMERICAL_GATE/RESULT_PASS/geometry_PASS均不升级；本轮无新增计算或数值验证，无新OpenLB run_id、编译、仿真、优化器、长算命令、投稿或对外联系；不改正文/图件/源码/协议/原始结果/历史FAIL，不自动下一Gate/两相，无新增长算授权。
- **下一具体动作**：作者/导师从PoF、C&F、EJM B确定偏好的贡献叙事；整稿就绪前核关键图链、历史来源和主张限制，学院确认分区版次和录用认定。旧`SIM240_PoF定向写作工作稿_20261019.md`可作候选摘要/结论底稿，不表示作者已批准最终刊或投稿。

## 六轮文字与台账一致性审查已闭合（2026-10-19，当前稿内一致性接续入口）

- **状态**：Codex 第六轮只读验收通过，三项定点订正销项。24 主张文本哈希 24/24 一致、正文—台账证据关联 24/24 一致、表格编号 I–VIII 唯一（第4章 TABLE I 为跨章引用）、36/36 主地图原始结果哈希一致、E_pct 复算最大差 0。
- **架构**：Codex（VS Code 插件，只读挑刺、不得改文件/编译/跑仿真）→ 结论回贴 → WorkBuddy（唯一执行方 + 证据闸门，逐条回原始文件复算）→ Codex 复核。**Codex 每轮均有实质发现；我方每轮均有失误**，详见下条。
- **本轮已修正的实质问题**（均有原始数据或源码行号支撑）：
  - **TABLE III 漏 h=25 整行（6/18 几何，占 1/3）**；全 18 几何 η∥ = 0.531–1.147（h25/d25、d50 两点 >1，d100 回落 0.976）、η⊥ = 0.063–0.852。
  - 「87% 容积死空间」**张冠李戴**（0.132 实为 h50/d120，非"最薄间隙最深槽"）+ 1−η 不能当容积占比 → 撤回。
  - 「唯一杠杆是 h」被数据反驳（固定 h25 时 A 增 6.771 倍）→ 改为「首选 h、槽深二级、随间隙变薄增强」。
  - 第4章轴向写反（P 沿 y、T 沿 x）、渗透率 K/P → **K/H_ref**（差 −47.9%）、「36 种几何」→ 18 几何×2 方向。
  - −18.705% 改为**双网格并列**：5nm −18.705%、2.5nm −14.936%；条件外推须附公式与假设阶数（p=1.00/1.26/1.51/2.00 → −10.80/−12.01/−12.75/−13.60%），任一个都不是真值或不确定度界。
  - 方法章：主地图 μ=1 mPa·s（36 工况）/μ=15 仅 2 对照；时间步分列；稳态判据 P/T 与 D3 分写（含 1e-12 绝对值门槛与 D3 相对 std 1e-6）；48→52 次（**第3章 TABLE VI 保留历史 48 及日期，不得改成 52**）。
  - 平板误差：总 0.4444% 中约 0.2222%（=1/(2×15²)）来自中点法求积 → 撤「误差完全由内点格式控制」，改为「未分解体相/边界，仅确立总积分误差的观测阶」。
  - 机制归因全部降级为候选解释（撤「隶属槽口不属容积」「全部来自角部失效」）；四条件从「恒等成立条件」改为「共同建模前提 + 代数恒等」。
  - 文献编号统一：**[1]–[16] 引言 / [17] OpenLB / [18] Bouzidi / [19] Guo / [20] Roache / [21] Celik / [22] Ladd**；Patir–Cheng 全文统一 [12]。
  - claims 台账按 `check_revision.py:164` 口径（**先删 [claim:]/[evidence:]/[@E] 标签再合并空白**）全量重算 24 条；E008 绑定 C005/C009/C017 且同步写入 CSV。
  - OpenLB 版本：HEAD=882924a9 与协议一致，但树内 CITATION.cff 自标 1.9.0、无标签，「1.8r1」无法证实 → 正文改引提交哈希 + 保留历史构建绑定限制。
- **本方四类失误（接手 AI 务必避免）**：①表格审计只查相邻两章（漏第2章 TABLE II 重号）；②哈希算法自创（未先读既有校验脚本）；③绑定顺序颠倒（先写 CSV 后改正文，致 E008 未同步）；④用精确字符串搜索验证语义修改（漏 "the"）。共同点：**"以为做对了"而非"验证过做对了"**。
- **交付物**：`正文修改清单_第4章与方法章_20261018.md`（v3）、`正文修订执行报告_v3_20261019.md`、`定点订正执行报告_第二轮_20261019.md`、`第四轮执行报告_B1编号统一与A类订正_20261019.md`、`第五轮执行报告_编号哈希与E008_20261019.md`、`第六轮执行报告_E008台账与引言口径_20261019.md`；闸门核验 `SIM240_independent_audit_20261018/CODEX_ROUND1_VERDICT.md`、`Codex第三轮核验_20261019.md`；备份 `before_v3_backup/`、`before_round4_backup/`、`before_round5_backup/`、`before_round6_backup/`。
- **边界与未做**：六轮全为文字/编号/台账一致性，**未新增数值验收**；NUMERICAL_GATE / RESULT_PASS / geometry_PASS 均未升级；**图件数据链、完整方法证据、历史构建来源绑定仍未审查**，需另立范围；submission_ready 未成立（人工作者确认待做）。无新 OpenLB run_id、无编译、无新长算授权。

## 原始数值证据独立审查（2026-10-18，当前数值接续入口）

- 范围：用户要求从result/CSV/源码独立审查K提取、收敛、质量/Mach/密度、网格；旧CORE_CLAIMS/audit/release作为被审对象，不能作证明。报告`docs/reports/reviewer_numerics_20261018_v1/REPORT.md`；复算、逐运行数值、36误差、历史网格/C、来源哈希与终检均在同目录。没有改正文、冻结卡、求解器、原始输出或旧审查报告；并行第5章写作状态保留。
- 已验证（已有输出复算）：48正式运行/228211诊断行的数值门槛与独立exit0吻合；K差≤3.79e-16，CSV/3D VTI通量差≤1.25e-13/2.41e-9；48材料几何逐点吻合，18个D3Q19方向候选links独立计数正确。36离散样点闭合误差和公布V2残差可复现。475原始输入哈希终检不变；无新数值Gate。
- 网格限制：4加密仅两几何/两方向，两级最大差2.1584%，不作全地图界；h25仅5层无加密。历史h75/d100原始三网格p=P1.513/T1.256，细GCI0.125%/0.551%、5nm条件1.011%/3.080%，不能外推其他几何。渐近比在本实现恒等于Kfine/Kmedium，不能独立证明渐近区。旧细T质量1.1967e-10/exit3仍FAIL；方案C补偿2.2041e-14/exit0，共有20列29549行与旧数据一致，9源码哈希正确，完整来源放行仍另核。
- 必改文字：第2章156/164停止判据错写；旧验收截面差上界应1.2661e-6，非2.7e-10；旧CODE_REVIEW的J/K倒数关系写反；第3章67/81“误差完全来自内点”被原始剖面积分分解反驳（5nm约一半来自中点积分）。本轮只提出问题未代修正文。
- 构建卡点：OLB_ROOT当前CITATION为1.9.0/HEAD882924a…，C原manifest也记该HEAD；D2日志版本由Makefile硬编码5953d8a-dirty，不能据此确认历史1.8r1。48清单无source哈希；4组binary中的24次引用路径已与当前程序不同。只报告来源缺口，不推断全部历史版本或数值已错。
- 黏度重审补充：`VISCOSITY_AND_TEXT_ADDENDUM.md`及`viscosity_check.py`/`viscosity36.csv`/`viscosity_text_check.json`直接从36原始result反推nu=1e-6、rho1000下mu=1mPa·s，18旧result缺rho/mu字段如实标注；原始初态mass/(rho_lat V)支持rho≈1000。两个mu15有dt=2.77778e-13，K与原mu1仅差−0.0006444%/−0.0002832%，不能把mu1原始J直接贴mu15标签，也不能据此认定K错15倍。当前正文批次表和第3章已区分两组，方法通用dt/nu需加例外。
- 当前第4章仍有直接错误，不能因其他章节修订就视为销项：14/82驱动轴互换、k=K/P而非本文定义K/Href；36几何应18几何/36方向；49/117的全图eta范围漏h25（etaP最大1.146793，etaT最小0.063153），1−eta不是死体积；37/105排除d影响被同h样点A增6.771/3.434倍反驳。下一步优先作者核对这些段落并另行授权最小正文修订；此轮只审不改，无新OpenLB运行/编译/长算权限。
- 下一具体动作：审读报告、最小改文字、从既有归档补版本/构建绑定；若保留h25定量结论再另拟网格补证。无新OpenLB run_id（沿用原目录）、无编译/新仿真/优化器/长算命令，无新增长计算授权。不得为了补交接启动或轮询计算；不自动转入下一Gate/两相/机制收支。

## 第5章按审查清单局部修订（2026-10-18，写作接续入口）

- 用户明确授权修订第5章。已写回`docs/reports/第一篇论文_第5章_对比对象选择草稿_20261018.md`，中英文与写作说明同步；说明`docs/reports/Chapter5_revision_20261018/REVISION_NOTE.md`，源记录/备份/验证见同目录。前轮20项审查仍在`Chapter5_mechanism_audit_20261018/REPORT.md`，不改历史审查或原结果。
- 机制与比较：保留条件Reynolds平均关系，撤“唯一尖角归因”“同号必可修/单调”“四壁矩形管”等论断；V2仍为已采纳的数据知情经验修订，限样点、非独立最终测试。开放槽原定义与截面未对齐，撤正式误差标定与猜测摩擦因子，现fRe图不作定量验证证据。12.3仍暂缓。
- 数字与方法：保留未修正模型B荷载比0.371464–0.901197、修正0.937291–1.050836，修正有符号中位残差−2.12%。修正时间主链0.960996–1.004658，先插K再求S；保留并行新增先插S的0.962185–1.005938作敏感性，两者最大逐深度差约0.162个百分点，不冒充严格不确定度界。d120正确Sm/Sref为0.371464–0.477857、冻结B/积分B差约17.99%；不再混用A字段。
- 符号与方向：明确项目K∥=Kyy/K⊥=Kxx；传播脚本x沿槽是局部轴名，正文映射为沿槽/跨槽。V=−dh/dt>0时正压方程右端为−μV，归档正右端/绝对荷载实现只影响符号不影响幅值比。方形场A=4时0.78为沿槽权重；不同主值改动一般会改变压力形状。
- 并行边界：编辑准备期间同章被另一工作流改写，并新增make_table2b_common_stroke.py/表、修改make_fig9.py。已留多次快照，在稳定最新底稿上用哈希保护合并，未覆盖并行生成器/表。当前图9/10尚未由本轮验收，不能据修改脚本推断标签与主链已同步。清理仍待逐批确认，本轮不删除/移动任何文件。
- 验证：check_revision.py独立exit0，47项文字/数值/输入哈希检查通过，58个正文段落映射已记账；人工作者确认待做，submission_ready=false。只沿用既有审查数值和局部代数核对，无新OpenLB计算、编译、优化器运行、原始数值Gate或run_id；冻结门槛与PASS/FAIL不变，无新增长计算授权。
- 下一动作：作者审阅当前第5章；继续整稿时核图9/10实际数据链、图注与分量标签，再检查其他章节是否仍复述已撤机制。热管原始定义、全域不确定度、机制定量分离与独立预测测试仍未完成，不因文字处置标为销项。

## 清理任务停点：2026-10-18，仍等待逐批确认

- 用户要求清理重复内容，保留最终结果与过程；每一批均须先明确列单并获得确认。当前未删除、移动或重命名任何候选文件，只维护清单与交接，未新增计算/验证，run_id不适用。
- 入口：`docs/reports/SIM240_cleanup_20261018.md`。第一批CLEAN-01为统一四图目录内5个Python缓存，共71430字节；保留全部源码、图像和证据。拟在确认后复核哈希、可恢复移至项目同级回收目录；永久清空另确认。当前等待本批批准，不执行下一批。
- 限定扫描发现13组内容完全相同文件；旧图和备份存在路径引用或过程价值，暂留。原始数据、协议、日志/退出码、历史FAIL及.Trash-0保留；Git既有删除项与本轮无关。

## 前一停点：2026-10-18 论文修订与V2口径统一

- 用户最终裁定：沿用V2，只统一验证口径。V2为当前论文经验关系；数据知情的探索性修订、样点残差、非独立最终测试三项限制必须保留。V1只作历史对照，不再承诺连续域±20%。
- 完成路径：第1/2/3章草稿、PoF前置材料摘要、首篇范围v2.1；核心入口 docs/reports/SIM240_manuscript_revision_20261018/CORE_CLAIMS.md，交付说明 REVISION_NOTE.md。并行工作流新增V2实现与文献段保留，备份见before/及concurrent_before_reconciliation/；没有覆盖其拟合程序、PPT或原始输出。
- 本轮检查：check_revision.py独立exit0；36地图方向工况重新从result核算，原审计绑定的288份steady/precheck原始文件哈希不变；V2导出六位小数参数与残差表相符。map36_evidence.csv、correction_groups.csv、validation.json保存结果。不是完整历史来源验收，不是新Gate。
- 当前数字口径：18几何/36地图方向工况；48正式运行含4加密+2黏度+6斜向驱动。V2舍入式在18沿槽样点最大绝对残差10.505%；15个h≥50 nm跨槽样点6.921%，h25/d100跨槽−18.705%。d75未参与系数估计，但模型选择时已可见，不能叫V2的独立最终测试。
- 实现状态：另一工作流已新增CASE/D_series/D2_groove_error_map/analysis_fit_v2.py及V2_FIT_REPORT.md等。本轮仅静态与系数评价检查，未运行优化器；当前输出缺完整优化success/终止记录、全精度解与环境记录，不能由文件存在声称独立优化复现通过。24条核心主张哈希/映射无误；严格Skill审核因未获人工作者确认仍非零，submission_ready=false。
- 已纠正：全地图2.2%上界、把细GCI套给5 nm、D3旋转槽壁及Jain流向不偏、η当死空间、正间隙弹性却说减h提高流量。机制仍为候选解释，12.3继续暂缓；μ1→15对照已有，原μ1图片不冒充μ15。
- 仍未解决：方案C原始run fine_t_C_20261014T151036+0800有PASS/独立exit0，但历史独立放行报告CASE/reports/fine_T_C_release_20261014_v1/RELEASE.md当前缺失；旧FAIL、新C输出、历史放行记载及后来环境问题分别保留。几何分组内部交叉验证、冻结后的未见条件测试、全域不确定度与机制收支未完成。并行新增引文编号与方法章有冲突，整稿合并需统一，本轮未重审新文献段。
- 下一具体动作：作者审阅CORE_CLAIMS及残差表；若继续验证，先补V2优化运行的收敛/精度/环境记录，再设计完整几何分组内部检查。需要新算例另行授权，由用户启动。无新OpenLB run_id、编译、求解器运行或Gate放行；不启动长算、不恢复12.3、不扩展两相。

> 最近交接维护日期：2026-10-18（最新单相论文审查见文件顶部；此前查新、出图及Skill任务保留其证据日期，均不构成新仿真授权；文件名沿用原交接日期）。本文件为跨工具（Claude Code / CodeBuddy / 其他 agent）交接用。工作协议以 `AGENTS.md` 为准（必读），本文件只讲"当前到哪了、下一步干什么"。

## 1 已锁定的路线（按用户2026-10-16本轮指令）

- 求解器仍为OpenLB；首篇真单相、显式沟槽，压力/体力驱动，无气液界面、表面张力及接触角。两相润湿/困气后置第二篇，覆盖此前首篇Q1+Q2表述。
- 几何P=240 nm、槽宽120 nm、槽深100 nm、凸台间隙h=75 nm；槽区总高175 nm、平均125 nm；mu=15 mPa·s，rho约1000 kg/m³。这是本轮用户输入，未修改旧run参数。
- 核心产出K_parallel/K_perp及等效模型误差；用户最新明确首篇全充液，alpha、Z压速与两相后置。
- 已找到NIL直接先例Jain2017（10.1016/j.mee.2017.04.001）及FEM比较Dewangan2020（10.1017/jfm.2020.134），不能声称首次。Jain公式全文现已取得并复核（见D2最新核对）；独立Asta交叉和数据库人工查新仍待补。补查取得同团队2018公开会议稿并核对第3页式(2)，只作模型口径与毛细边界争议线索，不替代期刊全文。

方向判断（2026-10-16追问）：已有工作覆盖NIL各向异性渗透率及单相受限沟槽的显式数值校核；具体EX240问题是否重复仍未定。仅换OpenLB或纳米尺寸不自动构成创新。有限间隙矩形槽的误差边界、耗散机制及可验证修正是候选贡献，尚不能称为文献空白。本轮无新增计算或数值验证。
- 本轮产物：`docs/reports/SIM240_LITERATURE_REVIEW_20261016.md`与`docs/reports/SIM240_LITERATURE_EVIDENCE_20261016.json`。全文/摘要证据、推导和缺口分别标注；2个DOI入口抽检HTTP200，5个PDF公式页目视核对。run_id不适用，无新增OpenLB运行或数值Gate放行。
- 以下R0/R1/R2等保留历史证据，不作为首篇当前执行路线；本轮未刷新运行状态、未改变任何PASS/FAIL，也不启动或停止用户计算。

## 文献检索Skills安装（2026-10-16）

- 用户要求“装一点找文献的SKILL”；沿用双平台偏好，为Codex与Claude Code各安装paper-lookup、literature-review、citation-management、scientific-critical-thinking，来源K-Dense固定提交`a1043ef544e3a100c28e70a736b6cf32554d0677`。每平台67文件，格式/语法及双端SHA256检查通过；仅适配不支持的compatibility头字段，正文/脚本未改，原版已保存。
- 指南`docs/reports/SIM240_literature_skills_20261016.md`；完整记录`/home/dell/.codex/skill-install-records/20261016-literature-skills/installation.json`。2条DOI元数据成功提取并核对标题，一次3条公开检索成功且标不完整；DOI注册2条均核实，另一次Jain元数据SSL失败如实记录，不能把接口连通性当全文或查新完成。
- 基础脚本依赖已可用，未新增账号/密钥/付费调用；Scholar专用依赖、可选PDF/AI示意图与Claude运行时发现未验证。下一轮/刷新会话后可调用；不自动触发新查新或仿真。本轮无新增OpenLB计算/数值验收/Gate放行，不刷新D2状态。

## 科研Skill筛选、双平台安装与自动选用（2026-10-17）

- 完整15项截图已收到，各仓库主页/说明及候选关键规则已核；微信原文仍受验证拦截。报告`docs/reports/SIM240_writing_skills_screen_20261017.md`扩充：最小新增建议=第2项K-Dense的scientific-writing、peer-review＋第14项academic-humanizer；第7项handbook可读，3精读及10/12写作按需备选，不全部叠装。1/6与9是完整工作流备选；4/5/8偏ML、11社科/15医学低优先级；13不建议原样安装。不是全仓库安全或写作质量实测、未核星标，不新增CFD验收或创新结论。上游规则未应用到项目。
- 用户随后明确要求补充并以后自动使用；两平台均已安装scientific-writing/peer-review/academic-humanizer，各70文件，固定K-Dense@a1043ef5…和AIScientists-Dev@94b88b23…，版本2.3/2.4/0.3.3。保留既有Skill及新技能上游正文/资源，适配元数据并增加implicit=true。49项文件/格式/资源/CLI/合成行为检查通过，脚本独立exit0；Codex只读运行时发现3项enabled=true。Claude当前PATH无程序，运行时识别未实测；真实稿件与实际隐式路由效果未测，不能把配置完成当写作效果验证。
- 路由已写入个人`/home/dell/.codex/AGENTS.md`、新建`/home/dell/.claude/CLAUDE.md`及本项目AGENTS §0.2；另存用户长期偏好便条。报告`docs/reports/SIM240_writing_skills_install_20261017.md`，原版/指令备份/逐文件哈希/命令退出及Codex发现记录见`/home/dell/.codex/skill-install-records/20261017-writing-auto/installation.json`。后续具体任务按需读取Skill，不再让用户反复点名；Claude会话发现另核，不自动启动仿真。
- 当前Codex会话已覆盖文献检索/综述/引文核验/科学批判、Matplotlib/科学作图、ParaView论文图、Zotero、Word/PDF/PPT/表格。官方可安装清单中`jupyter-notebook`是较相关的新增候选；GitHub PR/CI、部署、Figma和语音类目前优先级低。官方清单脚本只按个人Skill目录标注，不得据其`installed=false`否认系统或插件已提供的同类能力。
- 前轮Jupyter/Scite是额外候选；Scite尚未确认安装或连接。最新任务仅安装上述3技能并设置路由，未新增账号、密钥或付费调用；未运行OpenLB、未改源码/原始结果/冻结协议，未新增数值验收或Gate放行，run_id不适用，无新增长计算授权。

## Ban 文献进入稿件（2026-10-18，本轮局部写作停点）

- 用户沿用Ban学位论文借鉴任务要求继续。本轮使用scientific-writing/scientific-critical-thinking/PDF，读取最新范围与现有稿件；补核归档Ban2020/2021期刊原页。2020 p.022601-3–4式(8)–(10)与p.022601-6 Fig.7、2021 p.012601-3式(1)–(10)为具体来源。2021期刊平板分量写“相同”，不与学位论文“为1”混同；未声称整篇逐字相同或新查新完成。
- 已局部修订`docs/reports/第一篇论文_第1章引言草稿_20261017.md`：¶2补w/P=1/2条件；¶3前两段收紧Ban模型沿用、毛细压力验证与方向K校核的区别，移除过宽的“always”及对张量操作的创新暗示。全文其他文献论证、数值/公式/引用编号未改，不代表全稿审查通过。
- 产物`docs/reports/Ban_manuscript_integration_20261018/INTEGRATION.md`含方法/讨论/局限英文候选段与中文解释，尚未插入其他章；`Introduction_before.md`为修改前备份，`source_record.json`/`claims.csv`记录源哈希、原页、7条候选主张。AI检查与人工作者复核区分，作者复核待做；源文件及主张哈希检查通过不代表投稿放行。
- 已提示第5章“唯一归因尖角”等强机制结论不由Ban文献支持，本轮未修改第5章、不恢复12.3。首篇α=1固定间隙单相范围不变。无新仿真、编译、输出复核或Gate放行，run_id不适用，无新增长计算授权；48次输出状态仅沿用已有审查、不重验收。下一动作由作者审阅本次局部文字并决定候选段落位置，继续全稿证据一致性处理时须另按实际来源核查，不能用本轮替代。

## Ban 2021 学位论文的作用核查（2026-10-17，原页复核）

- 用户提供`/home/dell/下载/BAN-DISSERTATION-2021.pdf`（154页）；已审读相关第2、3章及附录/总结，关键公式和验证图目视核查。报告`docs/reports/Ban_dissertation_relevance_20261017.md`及同名JSON记录页码、源哈希、单位推导与误读纠正；后续Ban2020/2021期刊PDF已在Jain查新目录归档，并有独立吸收报告；本轮核其文件存在/签名，未重新独立核对逐式一致性。原“出版PDF仍未取得”的获取状态已过时，论文与期刊的版本关系仍以逐项核对证据为准。
- p.33式(2.9)(2.10)与p.67式(3.9)(3.10)继续使用等效方向K；p.66明确K_c=H0²/12。Ban沿y，与本项目一致；其有量纲K为m²，本项目深度积分系数为m³，须乘H_ref=h+d/2。换算后与现有Jain/局部立方律基线相同，不另算独立模型。相关章节未见目标的显式矩形槽单相K误差标定；p.42–43/Fig.2.7是毛细压力校核，不是K校核。不授权首次或保证二区。
- 借鉴：区分宏观薄膜近似与槽尺度闭合精度、隔离毛细驱动与水力阻力、用固定梯度下K误差解释流量误差；不把铺展长度比当K比。α/润湿/移动边界继续后置；机制收支仍暂缓。已有`BAN2021_DISSERTATION_ABSORPTION.md`部分版本/归一化/接触角/创新表述过强，使用时以本报告§6纠正，不覆盖其他工作流文件。
- 本轮更新上述报告、Jain引文报告/证据及本状态/交接；无新增仿真、编译、日志轮询、独立数值验收或Gate放行，run_id不适用，未改源码/原始结果/冻结协议，无新增长计算授权。下一动作按原范围验收现有矩阵后统一口径比较；查新按下节最新四任务状态补Scholar清单、C/D与剩余证据，不再要求重下已归档的Cochrane/Ban全文。

## Jain2017后续引文与四项查新（2026-10-17，本轮复核）

- 当前查新入口：`docs/reports/Jain_citation_audit_20261017/STATUS_20261017.md`；补核来源、修改前哈希及边界见同目录`STATUS_RECONCILIATION_20261017.json`。本轮使用literature-review/scientific-critical-thinking，纠正状态冲突和证据外推，不重新执行整套检索。
- **A：公开索引层已有筛查，覆盖未闭合。** 既有归档记载Semantic Scholar 9条、OpenCitations 11条，去重解析12篇有DOI期刊＋1篇会议，另1条仅题名线索；12个DOI引文关系已有核对。Scholar Cited by列表仍未取得，部分候选仍仅摘要/预览；本轮未重试，不将旧返回数当作当前总数。
- **B：18组据执行报告已运行，归档不完整。** 本轮核到`raw/taskB_openalex_batch1.json`只有前5组规范化结果摘要，余13组仅有报告记载。此前“B未做”已过时，“95%/无具体待办/全部原始结果归档”也不成立。本轮实际打开出版社Dewangan 2024图1，所示为连续光滑波纹，图1槽形待核项关闭；原图为`raw/dewangan2024_fig1_verified_20261017.png`。正文和全部算例仍未取得，继续保留近邻。
- **全文获取状态已更新。** Ban2020、Ban2021、Cochrane2018、Dewangan2020的PDF及对应吸收报告已在该目录；此前要求重下这些全文的待办已失效。本轮核文件签名和报告状态，未独立重做逐式审读；不据文件存在声称全部候选均已全文排除。
- **C传统数据库人工核查、D Asta均未执行。** C须包含Jain被引检索与独立主题检索，记录导出/筛选数量、截断与全文可得性；D先用既有独立问题检索，再逐条核实候选。需有适当访问权限者取得材料，后续AI可辅助分析；不笼统写成只能由用户本人或只能在校园网完成。
- **结论边界：** 仅限现有证据“未确认目标闭合误差标定的直接先例”；不启用“首次”。单个近似的失效不证明所有解析方法不可行；C/D完成也不构成唯一的新颖性放行开关。不再给未经校准的完成/把握度百分比或期刊录用保证。
- 本轮改动：上述STATUS/TASK_B报告、查新续查清单、本状态与交接，新增状态记账JSON及公开图1；原始JSON/PDF及数值结果未改。run_id不适用；本轮无新增OpenLB计算、编译、数值验证或Gate放行，无新增长计算授权。下一动作：按续查清单取得C的被引＋主题检索导出及Scholar清单，另取得D报告后对照；保留13组归档、中文/早期文献和候选全文缺口。

## 查新、D4与α核对（2026-10-16，本轮）

- 用户转贴三项待确认建议，要求查项目文档。核对报告`docs/reports/SIM240_three_questions_check_20261016.md`：查新清单已存在于`CASE/plans/SIM240_查新续查指令_20261016.md`，文档仍标待执行；本轮未执行传统库/Asta检索。已纠正“查新只影响措辞”“Jain与DNS逐位吻合”“仅平滑波形”等错误，早期完整检索指令加范围提示。
- “对比口径”中的D4为文献滑移条纹模型编号，不是已找到的D系列对齐CASE；当前只发现D1/D2/D3目录，未找到独立D4规约。h75/d100是旧新复现/基准采样点，不自动构成非零沟槽理论精度对齐；Jain与局部立方律的方向/单位/H_ref换算已在D2审查§3核对，不因旧待办而重新说成未解决。D4是否需计算及补点数未定，不取消补证需求、不自动建新矩阵。
- α已定义为槽内体积分数，首篇明确α=1；α<1后置，不需用户重拍面积/体积或启动死区扫描。固体掩膜改变流道，不自动等效真实气体或停滞液体；自由面/接触线也非互斥选项。冻结卡历史段仍有旧扫描与α=0表述，本轮不修改版本化协议，以当前范围为准。
- 已更新上述两个检索文档、“对比数据与换算口径”、报告及本状态/交接；未改范围/冻结卡/源码/运行脚本/原始结果。run_id不适用，无新增计算/编译/数值验收、无Gate放行，历史PASS/FAIL不变，不刷新运行快照。
- 下一动作：使用已修订清单实际推进查新；另据现有独立验收证据决定非零沟槽适用性/独立参考的最少补证，α仍后置。无新增长计算授权，不自动运行D3/D4。

## 投稿层级初评（2026-10-16，用户明确中科院分区）

- 已在线核对期刊范围与分区口径；中科院文献情报中心2026-03-27官方声明2026起停发，本轮统一用2025年3月升级版工程技术大类。逐刊分区来自公开转载，未登录本校官方归档，最终考核仍须按本校政策核实；不混入2026新锐/JCR/SJR。
- 用户最新目标：“想二区尽量二区，三区也接受”。投稿策略改为二区优先准备与选刊（PoF候选），三区可接受备选（MEE）；此前“三区为主目标”的偏好由本条覆盖，但不提升现有证据等级、不保证录用。若仅九点K/误差表，仍有创新不足风险；四区不是本轮明确接受的投稿层级，不自动列入投稿顺序。Engineering with Computers暂不优先。
- 报告`docs/reports/SIM240_journal_target_assessment_20261016.md`保存来源、缺口与分层判断。本轮无新增计算或数值验证，不更新D2运行快照、不改任何PASS/FAIL；run_id不适用。未改范围/协议/源码/输出，未联系期刊或投稿；无新增长计算授权。
- 下一动作：现有矩阵独立验收后先做12.1/12.2后处理，判断是否存在有推广价值的新增结论；保留最新范围中12.3机制收支暂缓、12.4仅补充的裁定。若二区证据不足，提出最少补证方案或按用户偏好转投三区，不自动恢复暂缓项或启动D3/新几何。范围§13与选刊报告已同步；本轮仅文档更新，无新增计算/验证，run_id不适用，历史PASS/FAIL不变。

## 六篇新文献的内容借鉴（2026-10-16，本轮最新）

- 已审读下载目录六篇论文及OpenLB 1.5手册，核对六篇DOI元数据、13个原文页面；四篇明确使用/介绍OpenLB，两篇是一般LBM纳米水流研究。报告与溯源：`docs/reports/SIM240_OpenLB_six_papers_content_20261016.md`及同名JSON。
- 当前范围文件已为v2.0，旧153行审查是修订前快照，不能继续当作未改现状。本轮在`CASE/plans/SIM240_第一篇范围重定位_纯液体单相_20261016.md`增补§12，并将斜槽条目改为闭合误差对流量/流向的影响：张量旋转本身不是新物理或Jain独有假设。数值范围、现有矩阵和运行参数未变。
- 待检验内容按优先级：h/d区间敏感性、等体积平板输运效率、压力/黏性牵引与空间耗散、误差对流向预测的影响。前两项可先基于验收数据后处理；机制项仍须后处理设计与精度依据。水的近壁经验律不移植UV胶。
- 报告内等体积效率和45°流向角是既有dx=2.5 nm、h75/d100系数的代数演示，不是新增或已验证的斜向算例。原PDF哈希未改；run_id不适用。未编译、未启动/轮询/停止仿真、未新增数值验收或Gate放行，保留历史FAIL及方案C独立放行边界。
- 下一动作：等现有矩阵完成并独立验收后，先提取区间弹性与等体积效率，按误差和不确定度决定机制补证；本轮不交付或授权新增长计算。其他工作流文件与结果不覆盖。

## 第一篇范围文件集中审查（2026-10-16）

- 用户指定的`CASE/plans/40_第一篇范围重定位_纯液体单相_20261016.md`不存在；实际审查`CASE/plans/SIM240_第一篇范围重定位_纯液体单相_20261016.md`（修订前153行快照；已由当前v2.0与§12补充覆盖）。该审查任务当时未改原文/冻结卡/源码/脚本/原始结果；报告`docs/reports/SIM240_first_paper_scope_review_20261016.md`及同名JSON记录26正文问题＋6组配套问题、行号/原文/SHA256和建议替换定位。该历史审查本身不等于数值问题销项；当前文字以已修订v2.0及§12为准。
- 关键必须修正：首篇alpha后置与旧扫描路线冲突；DNS参考解不等于实验真值；J/Q/K量纲、逐几何H_ref=h+(w/P)d、Jain无量纲k及方向/宽度比；方案C已独立放行不得与旧细T FAIL混同；中间间隙新颖性论据错误；固定h不等于Z挤压已验证；Ma不替代Re；牛顿胶适用性须有边界。模型适用、数值不确定度、固定G/固定Q耗散比较、能量积分及独立修正验证仍需证据。
- 范围文字已修订到v2.0并有本轮§12内容建议；其余配套条目是否全部销项未在本轮复核。数值验收另等现有批次结束，不由审查自动补算。现有运行只沿用21:57快照，本轮不刷新、不轮询；无新OpenLB计算/编译/独立数值验收或Gate放行。历史FAIL、方案C历史放行与后来环境哈希失败分别保留。

## D2矩阵与Jain全文的最新核对（2026-10-16 21:57快照）

## D2代表场ParaView打开入口（2026-10-17）

- 本轮只读定位 h=75 nm、d=100 nm、dx=5 nm 的最终稳态 VTM：P=`CASE/D_series/D2_groove_error_map/results/h75_d100_dx5_P/steady/vtkData/data/g2_ex240_parallel_iT0004329.vtm`，T=`CASE/D_series/D2_groove_error_map/results/h75_d100_dx5_T/steady/vtkData/data/g2_ex240_perpendicular_iT0002940.vtm`；不要把 `iT0000000.vtm` 当稳态图。
- 本机 `paraview`/`pvpython` 可用，版本 5.11.2。两 VTM 均已用 `pvpython` 成功读取为多块数据；实际点场名为 `material`、`velocity_m_s`、`pressure_Pa`、`dissipation_m2_s3`。坐标为米，150 nm=`1.5e-7` m、120 nm=`1.2e-7` m。
- 两代表点已有 `result.txt: PASS=true, converged=true, finite=true` 与独立 `exit_code.txt=0`；仅支持这两个代表点，不代表整个 D2 矩阵放行。未启动/重跑仿真，未改源码或原始结果，未生成图，未新增数值 Gate。无独立 run_id，沿用 case 标识 `D2-P-h75-d100-dx5`、`D2-T-h75-d100-dx5`。
- 用户截图已确认 P 最终 VTM 打开并建立 `Slice1`，z=`1.5e-7` m、Normal=(0,0,1)、`velocity_m_s/Magnitude`。**本轮修正此前150 nm出图建议**：只读探针在y=120 nm、x=30/210 nm测得material=3和速度0，在x=120 nm测得material=1、主速度8.49056e-5 m/s；两侧蓝区是固体，不能称为慢液体。改在共同液层中部z=`3.75e-8` m（37.5 nm），三处均material=1，中心/两侧主速度约1.33679e-4/7.98165e-5 m/s，可用于同高度液体速度对照。未新增仿真或数值Gate放行。
- **最新四图统一排版交付（2026-10-17）**：当前交付只用`figures/paraview/D2_publication_layout_20261017_v1/figures_v2/`，含Fig1 XY速度P/T、Fig2 XZ速度P/T、Fig3采样位置+u_y高度曲线、Fig4跨槽耗散的PNG/PDF/SVG；PREVIEW.png总览、CAPTIONS.md中英文图注、README及QA_RECORD/MANUAL_REVIEW同目录上级。速度复用旧`D2_h75_d100_dx5_PT_publication_20261017_v1/rendered_v4`，耗散由同原T场重绘为一致5 nm样本足迹并明确披露相对GUI POINTS+Threshold的方法改变；不平滑/外推墙面值或增加网格分辨率。统一nm轴/驱动/灰固体/字号及(a)(b)，速度共享0..1.8e-4 m/s，耗散独立0..32 m²/s³，不逐图归一化。5个场面板逐格RGB差0；CSV有效971/933点回原P场差0，混合边界保留NaN不补零，1001插值点不作独立网格。渲染、CSV核对、最终排版、像素/元数据/PDF字体检查、新耗散pvsm重开独立exit0，PNG/PDF/灰度已目视，原输入/既有证据/用户文件哈希未变。初轮figures/图3图例近曲线，保留但不交付；最终figures_v2图例已移出数据区。工作尺寸/像素见README，不称期刊合规；8-bit Viridis两处极小亮度反向、两曲线灰度相近的限制如实记录并用实虚线+标签冗余编码。图注14段有句子哈希/E-ID映射，受控schema修正后检查exit0但5个本地来源无公共标识警告保留；作者human verification仍unverified/submission_ready=false，不伪造审批。基准nu=1e-6 m²/s、按rho1000对应mu1 mPa·s，非mu15档；不据图认定Jain误差/角点网格无关或能量机制验证。下一步用户看图、人工作者核图注，期刊明确后适配版宽；无新OpenLB仿真/编译/数值Gate，run_id不适用，无新增长计算授权。
- **用户GUI样张与当前停点（2026-10-17）**：P的`CASE/D_series/D1_nanoimprint_droplet_filling/h75_d100_dx5_P_XY_z37p5nm.png`及同名`.pvsm`均已收到，PNG为2400×1335、RGB、白底、图例完整。状态XML及pvpython离屏LoadState独立exit0确认实际引用D2最终P场`g2_ex240_parallel_iT0004329.vtm`、z=3.75e-8 m、Normal=(0,0,1)、velocity_m_s/Magnitude；不能因保存在D1目录而称其D1结果。状态仍为蓝—白—红、0至1.6571265587117523e-4 m/s、Grow and update on Apply自动范围及略倾斜透视，论文样式尚待统一，两个原文件均未改或移动，SHA256见当前状态。最新用户截图已打开最终T场`g2_ex240_perpendicular_iT0002940.vtm`并建立Slice2，y=1.2e-7 m、Normal=(0,1,0)正确；x竖直/z水平、固体尚未分离。下一动作只给少量GUI指导：先点-Y使x水平、z竖直，待新截图后再做材料区分及流线，不预设小涡。统一规范成图仍以上条独立目录为准；本次无新仿真/数值验收，run_id不适用，无新增长计算授权。
- **图3已完成统一排版（2026-10-17）**：两用户CSV原件不变，直接回原P场核对差0，保留971/933个有效液体插值点，排除边界混合点且不补零/平滑。当前Fig3在上述四图包，含位置示意、u_y(z)、nm轴、单位、实虚线及不遮数据的图例；不作滑移或模型失效断言。原GUI profiles状态未完整重开验收，绘图依据已直接绑定原场的CSV；无需重复导出。
- **图4已完成统一排版（2026-10-17）**：用户draft_v1原PNG/pvsm及旧错误状态均保留，检查证据仍见`docs/reports/paraview_dissipation_state_audit_20261017/`。当前Fig4同原T场/y120/0..32，改用与速度一致的5 nm样本足迹并披露边界显示方法，补全nm轴/驱动/灰色Solid；不把侵蚀采样边缘当真实墙面，不求解墙面值。新`rendered/dissipation_footprints.pvsm`重开exit0，坐标/图例由assemble.py复现；上限覆盖30.8325843811。排版完成不等于机制/能量收支验收。
- **专用Skill交付（2026-10-17）**：双平台技能各5文件的安装/结构/脚本测试详见`docs/reports/paraview_publication_skill_20261017.json`。本轮Codex当前技能目录已列出`paraview-publication`，用户显式调用后实际执行完成图组；Claude Code运行时与隐式路由仍待核实。原技能保留，root-only检查脚本的溯源局限仍有效；本图组另外保存完整reader/payload哈希。后续直接从该技能和上述交付目录继续，不依赖旧GUI或聊天。

- 用户本轮明确首篇只做真单相Kxx/Kyy、误差地图；alpha、Z压速、两相后置。更新此前“alpha处理待决”的状态，不自动扩大矩阵。
- Jain2017本地全文已取得，本轮目视核对期刊p.64式(11)(12)(13)，其与局部立方律经代数和数值双路换算一致。原文小写k无量纲，大写K[m²]；维度κ=H0² k/12、SIM240 M[m³]=κ H_ref，原文沿x而本项目沿y。此前“全文仍缺”的说法由本条覆盖。
- 纠正CASE计划中的新颖性论据：Jain §3.1从H=1000 nm算到10 nm，涵盖中间间隙；不能以“他只研究最终薄隙、我们研究中间间隙”定创新。局部显式误差地图与机制/修正是候选贡献，仍待后续文献及独立验证，查新不只影响措辞。
- 21:57:44一次快照：其他工作流的d2matrix已运行--with-recheck；14/18主方向工况已写最终PASS=true及独立shell exit0，precheck几何/q=true；当时h125_d50_dx5_P在算。仅记录快照，不轮询、不判整批通过。实际计划=18主方向+4细网格复核方向，不是总共18次。
- 已核实旧Smooth75误差0.44444%/0.11104%/0.02716%；D2 h75/d100/dx5的P/T通量、K、停止步数复现旧档，P诊断20列全一致，T质量两列不完全相同，故不称全部逐位复现。单点复现/旧平板验证不替代全矩阵网格独立。
- 报告及哈希：`docs/reports/D2_readiness_audit_20261016.md`和同名JSON。本轮未编译/新启动/停止仿真，不修改正运行的源码、脚本或原始输出，不新增Gate放行。待用户确认批次结束后统一验收；脚本汇总步数字段错配及最终done不反映整批成功已记录，不能靠DONE验收。

## D1用户提交命令的已有结果核对（2026-10-16）

- 本轮仅读取已有D1输出；无新编译/仿真/停止操作或Gate放行。首篇单相范围不变，本项为用户主动提交的两相校准检查。
- 一次快照未见默认tmux服务或D1进程。`CASE/D_series/D1_nanoimprint_droplet_filling/output/run80/run104/run120/run15`分别指四个独立目录（不是嵌套路径）；各history有301行、末步6000，重算样本指标与result一致。80°/104°样本指标通过；120°/15°漂移及角误差失败。旧`output/`100°结果与v1b.log吻合、样本指标通过，但早于当前构建；不完整粘贴命令与该结果绑定未证实。
- 证据：`docs/reports/D1_existing_run_check_20261016.md`及同名JSON。run_id仅有可覆盖的run80/run104/run120/run15标签，旧100°无唯一run_id。未找到本CASE逐run独立shell退出/manifest；源码构建绑定、geometry/q及完整验收未证实，不据此称CASE全部通过。`CALIBDONE`和当前main的return0都不代表指标通过。
- 规约V1b=Laplace，而CASE初值报告V1b=6000步接触角，命名冲突待澄清。若继续两相，下一步先只读诊断120°/15°，保留FAIL、不自动加沟槽、不改阈值、不启动长算。此前phasefield目录校准是否运行未在本轮刷新，不能把D1结果当成另一程序结果。

## 2 当前进度（R1记录截至13:30；R2文件核对截至16:13 +0800）

- **R0 完成**：相场 CH 守恒 FAIL 根因 = 非自洽初值（erf 剖面≠tanh 离散平衡 + 压力无 Laplace 跳变）激发启动寄生流，× well-balanced CH 对流源项非零零阶矩记账；稳态守恒（~1e-8/步）；润湿边界排除。报告：`grooveDNS/stage3_ex240_local/phasefield_minimal_validation/R0_phasefield_conservation_root_cause_20261015.md`。
- **E0 完成**：`--init-phi tanh --init-pressure laplace` 修复验证通过（全程漂移 3.5–3.8e-4 < 1e-3，启动 Mach 降 10×）。E0-a 证明 φ 剖面是主因。报告：同目录 `E0_self_consistent_init_experiment_20261015.md`。
- **R1 正式 run**（run-id `phasefield_contact_theta100_R18_formal_tanh_20261015`、`phasefield_laplace_R16_sigma001_formal_tanh_20261015`，tanh+Laplace 初值）：2026-10-15 13:20 启动，contact 6000 步 + laplace 4000 步，**已全部完成并判读为 PASS**（contact：角误差 2.92°、漂移 7.30e-4、末五次角范围 1.62°；laplace：Laplace 误差 11.75%、Δp 稳定性 2.94%、漂移 3.82e-4；两 run exit_code=0，manifest 与参数齐）。报告：`grooveDNS/stage3_ex240_local/phasefield_minimal_validation/R1_wetting_benchmark_validation_20261015.md`（含 WorkBuddy 独立复核段）。**R0+R1 前置已打通，R2-XY / R2-Z 可开工。**
- **R1退出证据补注**：本轮见result与manifest记录exit0，未找到两正式run的独立shell `exit_code.txt`；保留既有验收记录，不新增声称shell退出已独立证明。基准仅覆盖等密度、平壁100°/周期球滴与既定参数，不能自动外推到60°带槽和更长时程。
- **R2-XY当前快照（16:13）**：源码、Makefile和程序已存在。4-rank几何审计字段geometry/q=true，candidate=valid=installed=4819154，fallback/unresolved=0。其他工作流新增`output/R2XY_short200_4r_20261015/`：计划200步、完成3步，NUMERICAL_GATE=false、RESULT_PASS=false、geometry_PASS=true，较早漂移0.0017909594、Mach约0.02467；随后同目录改为完成2步、漂移0.0010882027>1e-3、Mach约0.05100>0.05、finite=true，result/manifest记exit3；另有`R2XY_initdiag_20261015`零步诊断finite=false、Mach=inf、exit3。没有独立shell退出文件；当前源码与构建绑定待查；同run目录结果被并发改写，两次观察已入快照，不能称两个独立批次，后续须唯一run ID归档。**停点=短测守恒FAIL，不是200步预检完成。**本轮仅读取这些已有输出，未启动或重新编译；保留所有失败目录。
- **h75旧放行与当前环境分开**：历史细T方案C及新九点链放行保留。最新完整`verify_release.py`为exit1，`libudev.so.1`哈希不符；9项源码/1541项OpenLB文件/19项输出均匹配，15动态库仅1项不同。另行冻结函数检查归档数值/几何/GCI通过，不替代完整环境失败，不改旧manifest或系统库。
- **已有阶段汇报**：`CASE/reports/stage_report_20261015_v1/阶段工作汇报.md`和`evidence_snapshot.json`，按其快照时间使用，不覆盖后续研究定位修正。
- **Agent交付（2026-10-15 22:59）**：个人级Claude Code子Agent `/home/dell/.claude/agents/plain-language-skill-helper.md`；角色是面向非技术背景人员的Skill维护助手，不是SIM240科研子Agent。支持通俗解释、定位Skill、保留原版、最小修改、适度验证和交接。必要字段/正文/空白已检查，Python无YAML解析器，尚未在Claude Code中调用。目录为此次新建，若主对话不能发现，重启Claude Code后指定该Agent。模型继承主对话、权限为default，未改账号设置。
- **最近交付（2026-10-16，技能安装）**：`/home/dell/.claude/skills/`新增官方`skill-creator`、`docx`、`pdf`、`pptx`，固定来源`anthropics/skills@dbd4588f9e1033efb41dad4bef2f7947c8993d44`。用户随后已明确选择两个平台。Codex实际入口与当前会话技能目录核对后，已有系统skill-creator和Word/PDF/PPT插件技能全部覆盖，保留原版本，不重复安装同类副本。四份SKILL入口及147个文件复制SHA256检查通过；清单`/home/dell/.claude/skill-install-records/20261016-anthropics-four-skills.json`。当前PATH无claude/pandoc/LibreOffice，系统Python缺若干文档库；仅完成技能文件安装，未安装依赖或验证Claude调用。双平台来源/入口哈希清单：`/home/dell/.codex/skill-install-records/20261016-dual-platform-inventory.json`；Claude147个文件再次匹配。Codex能力确认仅限当前会话，未验证另一CLI环境或文档生成。下一步按具体任务检查合适环境和实际发现情况，不为验证安装而改论文/跑仿真。本轮无新增计算、数值复核或Gate放行，不刷新前述数值快照。

## 3 R1 判读门槛（冻结协议，已判读通过，不得看结果后调整）

contact：接触角误差 ≤5°（输入 100°）、全程漂移 ≤1e-3、末五次接触角波动 ≤2°、φ∈[−0.05,1.05]、Mach≤0.05。
laplace：Laplace 误差 ≤15%、Δp 末五次稳定性 ≤5%、全程漂移 ≤1e-3、同上数值门槛。
两类证据分开报：数值门槛 / 物理验证各自 PASS/FAIL，不得合并声称。历史 FAIL（20260910 两 run）原样保留，不得改写。

## 4 关键约定（AGENTS.md 之外，用户明确要求）

- 长仿真（>几分钟）一律 tmux 后台跑：AI 只负责改代码/编译/给命令/算完查结果，**不轮询**。
- 涉及本项目的改动先读 `SIM240_AI_CONTEXT.md`（当前状态）再动手。
- **用户2026-10-15固定要求：每次做完及时更新进度，供额度耗尽或切换其他AI后接续。** 结束/停点前按AGENTS.md §12.1同步当前状态与本交接，写明改动、证据、未完成、下一动作和长计算授权边界；无新增计算时直说，不把复述当进展。

## 5 下一步（范围集中审查后的停点）

1. 按范围集中审查报告修订范围及配套定义；Jain全文已核，继续引文追踪。现有D2批次结束后另行验收，不重复启动。
2. 用户最新明确alpha/压速/两相后置；D2矩阵已在其他工作流启动（见21:57快照），本轮不重复启动或改运行配置。
3. 厂家>100 mbar不能单独反推出theta_m<104°或全部J-FIL无需外压，旧讨论中的该推断本轮不采用。文献报告A组给出不同几何判据和来源。
4. 本轮仅文献、公式/单位核查和文档维护，无新增编译、数值验证或Gate放行；旧失败和冻结门槛全部保留。

### 此前两相准备交付（历史记录，不自动继续）

0. **此前接触角校准命令交付；是否启动及完成本轮未核实。**用户贴的命令含`.../`路径和粘贴错乱；本轮一次快照仅见tmux `d1v1b`，无`pfcalib`/phasefield进程、四个原校准输出目录不存在，未轮询、未启动仿真。已按`CASE/plans/SIM240_润湿校准代码改动方案_20261016.md`准备`grooveDNS/stage3_ex240_local/phasefield_minimal_validation/run_wetting_calibration_20261016.sh`；四角80/104/120/15度，15度extent100、其余64，6000步、VTK500、tanh+Laplace，四个独立单rank进程。唯一批次/run_id、不覆盖旧结果，记录实际命令和独立shell退出，任一非零整批非零；程序原manifest漏theta/extent由外部命令记录补充，不改原输出。bash语法及隔离替代程序记账检查通过（未执行真实OpenLB），证据`docs/reports/pfcalib_launch_check_20261016.json`。交付命令为`tmux new-session -d -s pfcalib 'cd /home/dell/yuanyuanxu/SIM240/grooveDNS/stage3_ex240_local/phasefield_minimal_validation && exec bash ./run_wetting_calibration_20261016.sh'`；**命令已准备/交付不等于用户已启动或校准通过**。完成后新任务读取各run诊断/result/独立exit，按原门槛验收；不自动进入R2，不持续查运行日志。
1. 判读 R1：**已完成，两 run 全 PASS**（见第 2 节）。
2. **R2-XY 协议文件为v1.0，正式物理映射仍未放行**（`CASE/plans/SIM240_液滴R2-XY最小验证协议_20261015.md`）：保留用户已定的OpenLB、h75、显式顶面沟槽、60°与y周期边界。§2.8原给dt≈2.04e-10 s，但按其所列公式与dx=5nm、rho=1000、sigma_phys=0.03、sigma_lat=0.01，重算为约6.45e-12 s；mu=0.01时nu=1e-5而非1e-6。源码的输出字符串仍引用旧dt；**不得据旧字符串解释物理时间或流量**。仅记录问题，未改冻结协议或求解源码。
3. **待办顺序**：单位算术审计已完成（`CASE/plans/R2XY_S2.8_单位口径审计_20261015.md`），先订正并选定物理映射、足迹/液量（960nm较944.2nm体积约+3.4%）与域内/域外观测定义 → 核对源码/构建来源，诊断R2短测守恒/Mach FAIL及零步非有限输出，不能直接认定与R1同根因 → 修复和必要参数基准明确后完成200步预检预算 → 正式参数冻结且用户授权后交付tmux命令。调整τ或σ_lat需要独立验证，不能保证只做R1两项即全部放行；不重做已有R1来充当带槽验证。
4. 任一门槛 FAIL → 按 result.txt 具体项诊断，不自动改门槛、不自动进入下一步。
