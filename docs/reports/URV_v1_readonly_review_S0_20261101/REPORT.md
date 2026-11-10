# URV-v1 准备包只读复核与 S0 未生效材料

日期：2026-11-01。状态：**只读复核已完成，执行准备保持 HOLD；S0 两条 h75 回归仅有未生效草案，正式计算未启动。**

用户要求按顺序复核准备包、确认外部数据历史、随后另行准备 S0 执行绑定，并保持不启动。本轮收到用户对外部历史的明确答复：**“尚不能确认，需要核查”**。这项事实不能替作者填成 CONFIRMED。因此没有形成生效执行合同、没有开放推进保护、没有编译或运行原生程序。独立于该确认，已完成源与证据复核，并整理可复用的 S0 配置与基准材料。

本报告为作者请求的 AI 自审工作稿；AI 正在检查前轮由 AI 生成的代码，不是独立人工审查。采用 peer-review 的证据对应和问题定位流程；本项目是确定性 CFD，数值判断沿用 URV-v1，没有套用临床试验或 p 值要求。[审查范围](INTAKE_NOTES.md)、[过程声明](review_intake.json)及[声明检查](intake_validation.json)只记录此次处理边界，不构成人工科学放行。

## 复核仍成立的准备证据

- 已封存 CASE 的 **830 个文件**前后 SHA 一致；准备封存的 **1,432 项输入**当前均匹配。原准备报告及其冻结材料保持。没有改主程序、检查器、Makefile 或旧输出。
- 旧 C/h75 与 h75 回归控制合计 **1,686 项历史绑定**仍匹配。旧细横槽 FAIL、C/h75 的限定离散资格、V2/G4 锁和旧 D4 预测 HOLD 均保留。
- 既有零步审计的 **796 个文件**哈希匹配；重新从配置计算并核对 24 项边界/材料/体积，结果符合已安装数量。19 处源码替换逆向恢复原 D4 全文。
- 既有编译、72 次原生零步调用、24 个初始化 VTK reader 记录仍有证据。**本轮没有重复编译、调用求解器、做原生预检或重读 VTK。** 旧 35 测试通过日志按历史软件证据读取，没有冒充本轮重新通过。
- 当前 Makefile 的 `URV_PREPARATION_ONLY=1` 和解析阶段的 steady 拒绝逻辑保持。没有 `CASE/unseen_v2_reference_v1/results/`，没有实际新正式 run_id。

证据：[review_verification.json](review_verification.json)、[case_hashes_before.json](case_hashes_before.json)、[geometry_recalculation.json](geometry_recalculation.json)。这些事实支持准备证据未漂移，不等于正式执行链没有缺口。

## 四项需要记录的缺口

机器条目和原始定位见 [findings.json](findings.json)。本轮没有修复源码，所有人工反例只使用本新报告目录，未对实际原始结果做破坏性测试。

### F01：非法输出位置被拒绝后，失败处理仍写入该位置

**定位：** 原 [check_results.py 第136行](../../../CASE/unseen_v2_reference_v1/analysis/check_results.py#L136)及第272—276行。

**观察：** check_run 拒绝 `out` 位于 `run` 内部，但外层异常分支继续向 `args.out/failure.json` 保存失败记录。即使输入目录被判为禁止写入，仍会被写入新文件。

**证据：** [人工 CLI 反例](synthetic_probes/output_inside_raw/probe.json)实际返回 2，同时在新建人工 raw 目录生成 failure.json。只有人工标记文件，未使用任何真实流场。不是仅凭源码推测。

**影响与行动：** 这违反检查器对原结果只读的约定；进入真实验收前应统一核验输出位置，非法目标只报 stderr/非零退出，不写该路径，并覆盖符号链接和批次目录。前轮测试没有覆盖这条失败分支；原“准备测试通过”不应解释为该路径已验证。

### F02：h75 回归失败时，逐列差异没有先保存

**定位：** 原 check_results.py 第108—122、201—204、216行。

**观察：** compare_legacy 能算出共同列的差值；当 all_exact=false 时，程序在创建分析目录和保存比较对象之前抛错，最终只有通用失败提示。原 README 所说“保存差值并暂停”在这个失败分支尚未实现。

**证据：** [人工共同字段比较与控制流记录](synthetic_probes/legacy_difference/probe.json)。这里验证了 helper 算术和源码先后顺序，**没有声称复现过新 URV 完整流场失败**。

**影响与行动：** S0 的任务就是检验统计移植是否改变旧轨迹；应在经安全核验的新分析目录保存全部共同字段差异及 K 相对差，再作停止判断。保持原严格停止方式，不因为补齐诊断而放宽物理门槛。

### F03：执行合同没有强制最小来源覆盖及逐条身份对应

**定位：** 原 check_results.py 第124—134、153—161行。

**观察：** binding 核对清单中声明的哈希，并要求 analysis/common 文件被列入，但不强制 native 源码、二进制、编译依赖与运行库全部出现。approved_run_ids 只是名单，未强制绑定每条 planned_case_id、配置 SHA 与唯一输出目录。

**证据：** [人工缺项合同](synthetic_probes/incomplete_release/probe.json)仅列 Python/common 文件，省略 native 源/程序/依赖/库，实际调用 binding 仍返回成功。人工合同中的 CONFIRMED/授权字段仅用于该函数反例，明确标人工，**不是作者历史确认，也不是实际执行合同**。逐条对应缺口是静态检查结果。

**影响与行动：** 单纯“给定哈希都相符”不能证明关键来源没有漏列。真实执行前，应通过新版本或等效的外层校验，强制来源角色/完整覆盖与 run_id→case→配置 SHA→输出目录对应，再保留前后核对。当前准备封存确实包含 1,432 项；问题是未来执行合同的校验器没有强制维持这种覆盖，不能据此说已有 1,432 项封存无效。

### F04：单一合同的24条汇总入口不兼容分阶段封存

**定位：** 原 check_results.py 第140—141、259—271行。

**观察：** 汇总 CLI 把同一个 release/SHA 传给全部 24 条，且要求各条 completion 中的 SHA 都等于它。按协议 S0—S5 分别冻结、分别启动的正常记录会有不同合同 SHA，当前入口不能直接合并。

**证据：** [不同阶段 SHA 的人工分支核对](synthetic_probes/separate_stage_anchors/probe.json)与 CLI 静态结构；人工分支明确 mock 来源层，仅核对合同 SHA 一致性分支，没有运行真实阶段。

**影响与行动：** 后续汇总索引应逐条携带各自受信合同/SHA，分别重验再汇总；不能回写旧 completion，也不能为适配入口提前授权全部 24 条。这项不阻塞 S0 单条分析，可在进入后续汇总前单独修订；不把它混成当前必须重构全部程序的理由。

## 外部数据历史的当前事实

[external_data_history.json](external_data_history.json)保存问题范围与用户原话，状态为 `PENDING_AUTHOR_CHECK`。尚不能确认不等于曾使用过，也不等于从未使用过。

既有本地检索只支持“已检查范围内无匹配候选记录”；它不能回答其他电脑、未归档文件或他人数据的使用情况。本轮没有扩大到全电脑扫描，也没有读取旧 D4 保留预测组流场。

后续由作者按两个候选分别检查：

1. 是否存在其他机器、个人目录、移动盘或未归档结果/配置；哪些位置已查、哪些未查。
2. 是否收到过他人的同几何结果；若有，记录来源、日期及可定位材料，不要求提供密码或无权共享的第三方材料。
3. 分开记录“曾见过结果”和“曾用于选 V2 系数/公式/检验条件”。见过结果不自动等于已用于拟合，但不能省略披露。

若发现已有使用历史，应保留原预测封存和历史事实，重新限定“未见预测”的主张或另行预先选条件；不能悄悄将旧结果重新标成未见。**S0 h75 本来就是已知回归控制，与两个新条件的未见检验分开。** 仅因 h75 是已知控制，不代表可以越过用户指定“先确认历史、再正式绑定”的顺序。

## 已准备的 S0 两条未生效材料

入口为 [S0_binding_DRAFT.json](S0_DRAFT_NOT_EXECUTABLE/S0_binding_DRAFT.json)。这不是 execution release；simulation_authorized=false、approved_run_ids=[]、实际 run_id=[]。模板仅 `mode=describe`，输出目录为 `DRAFT_NOT_AN_EXECUTION_DIRECTORY`；没有创建未来正式输出目录或提供启动命令。

| 条件 | 沿槽 P | 横槽 T |
|---|---|---|
| 方向 | +y | +x |
| h/d/w/period（nm） | 75/100/120/240 | 相同 |
| dx；平均 H（nm） | 5；125 | 相同 |
| a（m/s²）；压强梯度（Pa/m） | 1e5；1e8 | 相同 |
| 旧 D4 基准 K（m³） | 9.834076003216204e-23 | 4.449022023188299e-23 |
| 旧轨迹停止步 | 4,342 | 2,953 |
| 新计算结果 | 无 | 无 |

共同固定项：rho=1000kg/m³、nu=1e-6m²/s、mu=.001Pa·s、tau=1；Lx=Ly=240nm、x/y 周期、静止无滑移 Bouzidi。J 仍为体积分速度/平面面积（m²/s）；K=nu×J/a（m³），U=J/H。dt=4.166666666666667e-12s，统计窗1013步，上限58800步，流体57600点，壁面32448连接，q=.5。以上用有理数重算，与原矩阵及旧配置一致。

两条旧基准的源结果、完整诊断、所有原始输出哈希及独立 foundation 接受证书已列入 [baseline_inputs_sha256.json](S0_DRAFT_NOT_EXECUTABLE/baseline_inputs_sha256.json)。旧 raw RESULT_PASS=false 保留，独立接受证书另列，不回写旧原生字段。

模板候选编号以 `PROPOSED_` 开头，只供审阅，没有当作已批准或已执行编号。当前准备程序 SHA 已记录为“准备版”，未来正式程序 SHA、最终配置 SHA 与最终执行清单 SHA 均留空。**不把当前禁止 steady 的二进制填成未来正式二进制。**

验收沿用 URV-v1：每条原数值/几何门槛、K 与旧基准相对差≤1e-4、全部20共同诊断列的完整轨迹比较；差异先保存，不能解释则停止。每条墙钟上限3600s、地址空间8GiB，单进程/线程/cuboid、overlap3；运行时重新核 RAM/磁盘。失败不自动重试、不自动进入 S1。通过 S0 只能支持新统计副本回归，不授予两个新几何参考资格。

[draft_verification.json](S0_DRAFT_NOT_EXECUTABLE/draft_verification.json)记录静态草案核对。原 frozen matrix、时间、平均定义、物理门槛和模型系数均未更改。

## 停点与接续动作

**本轮已完成：** 只读来源/几何复核、四项缺口定位、四组隔离人工核查、记录用户历史答复、S0 不生效材料及项目交接。**本轮未完成：** 外部历史事实确认、F01—F03 的修订与验证、正式构建/外层运行器和生效执行绑定；未做编译、求解或新物理验收。

下一任务范围可以明确为：在另行授权的新版本中最小修订 F01—F03，保留当前封存并用反例验证；作者并行核对外部历史。两项完成后，再准备 S0 两条正式绑定、正式构建及独立退出/资源/原始产物捕获，仍不自动启动。F04 在后续汇总前单独处理。

新正式 NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null；reference_qualified=false、strict_error_bound_established=false、submission_ready=false。旧 Gate、FAIL 与限定资格不变。项目当前状态和最新 AI_HANDOFF 已同步，以新停点覆盖前轮“只待常规复核即可接续”的不完整认识。

科研技能流程来源沿用同日已核书目信息：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://arxiv.org/abs/2609.00065), DOI [10.48550/arXiv.2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。仅作 AI 工具流程归属说明，不作本项目数值/物理结果证据；本轮没有新增文献验证或向第三方发送项目材料。
