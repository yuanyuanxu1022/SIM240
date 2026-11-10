# S3 准备 A 与采用范围的只读复核

日期：2026-11-03；完整性复核时间10:42:04 +08:00。用户范围：只读复核A与范围；12次原生零步及4次初态场读取获得明确授权后才准备执行绑定；当前不启动。本轮无新的执行授权，不生成合同/命令，不修改原源码/封存。

## 1. 裁定

**完整性通过，运行前内容审查不通过；HOLD，暂不为原A生成原生执行绑定。** 准备A仍为有效保存的历史准备包，2339项输入一致，SHA256 5d4e70d85d586b3cdf1ebca09f82f1f4abf90166642c34f1a5f4663cdeb4f02d未变；不是文件漂移、编译失败或已发生的数值错误。

实际代码中有两处尚未被此前57+42项测试覆盖的零步内容核对缺口，需在新隔离版本最小修订并验证。现有软件测试通过的事实保留，但不能由此推导零步检查完整。结论不要求改变物理内核、原生二进制或科学阈值。

状态：BINDING_INTEGRITY_PASS=true；SCOPE_REVIEW_PASS=false；EXECUTION_BINDING_READY=false；disposition=HOLD_FOR_R1_R2_MINIMAL_ISOLATED_REVISION。原NUMERICAL_GATE仍NOT_EVALUATED，geometry_PASS=null，RESULT_PASS=false（尚未计算），不能写成物理FAIL。

## 2. 已确认的相符项

- 四条新正式配置为dx2.5nm低/高力a50000/200000的P/T；十二零步配置及预留顺序与原S3-PR-v1一致。四正式和十二零步目录均仅run_config/run_manifest。
- A全部四项执行许可false，approved及actual列表空；无audit_attempts、launch_attempts、analysis_results、准备B；默认两入口只读退出0。本轮拦截任何子进程创建，未发生原生/VTK调用。
- 原S1 ELF 5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b和真实来源链通过；13份科学公共/检查器文件字节同S2。既有实施报告清单全部一致。
- 两条中力S2基准保留原合同d08297ebda69d9698d40762f778eb43299fa3c01c35e5591b6d31b4e06ef26cd及身份/输出；K沿槽5.919337058277595e-23、横槽2.3663885892433063e-23m³。未把中档列入S3新授权。
- 本轮2362项覆盖准备、代码、基准来源与实施报告的保护文件前后一致。未重跑原99项套件或重复读取真实场；只新增有明确标签的合成诊断探针。

## 3. R1：实际输出参数未充分与配置交叉核对

位置：CASE/unseen_v2_reference_S3_reuse_v1/scripts/audit_S3_zero.py，audit_outputs第55–76行。当前effective_config只核对run_id、mode、window_steps、maximum_steps、dt_s，未逐项核对已输出的方向、acceleration_m_s2、dx_m、nu_m2_s、几何长度及formal_simulation。

合成只读探针给initialize分支提供正确配置/几何及半步J，单独将effective中的a改为200000、方向改为perpendicular、dx改为5nm、nu改为2e-6、formal_simulation改true，函数均接受。它证明代码不能拒绝这类互相矛盾的输出；不证明原生程序实际上产生过这些值。本轮没有执行原生审计。

采用范围要求核对方向、力转换与单位，故这是运行前必须补齐的检查缺口，不能仅以封存配置或固定ELF正确替代输出证据核对。initialize已有半步J检查继续保留，不能删除。

最小修订：在新隔离候选中，按当前配置和exact_parameters核对effective已提供的所有相关物理字段、方向、零步formal_simulation=false及网格/时间/体积/窗口转换；计算并核对力转换的一致性，保留既有半步J判断。不要求为新增格子力输出而改C++。各模式应覆盖实际提供的字段；对应单字段矛盾均应拒绝。阈值保持原值。

## 4. R2：零步总收据未充分关联到逐配置原始读回

位置：CASE/unseen_v2_reference_checker_S3_reuse_v1/analysis/stage_s3.py，verify_zero_receipt第79–97行。当前检查case/mode顺序、摘要退出/步数、各读回PASS/actual_reader/单帧，以及文件指纹；但没有充分核对records的run_id/output与各自零步计划，也未要求四个初始化读回唯一且落在各自配置对应的报告/载荷位置，未在此处复核读回的该配置初态通量。

合成探针在临时目录隔离此内容检查，模拟授权解析返回（不声称构造了真实授权或完整原生证据），保持真实文件/哈希检查，产生两个反例：①四份PASS读回但J均为0；②四个initialize记录重复引用第一份读回。该内容检查均接受。源码也直接显示只查PASS/actual_reader/len(frames)==1，未核对实际case关联和通量。authority_checks_mocked=true明确保存在synthetic_gap_probes.json；不能把这个探针解读为突破真实授权。

原逐次执行器正常路径会生成不同文件，但执行器的生成约定不能代替B资格检查器的逐点验证。若后续总收据本身被错配，当前函数未充分拒绝；原始文件哈希只能证明内容未变，不能证明引用关系正确。

最小修订：以已授权零步计划逐条核对run_id/output/mode，读取各自process_receipt与execution_audit确认真实独立退出/无超时/零步，重新核对该次原始输出参数及初始化状态；四份读回必须唯一并匹配各自expected路径，frame.step=0、核心节点及半步通量与该配置/原result一致，payload_sha256仅引用该initialize的真实VTK闭包并与原始清单一致。读取器process回执须退出0且未超时；不拿另一配置读回或摘要PASS替代。不运行新求解器，不凭修订直接宣告原生审计通过。

## 5. 证据与覆盖范围

check_integrity.py / verification.json：真实封存、侧文件、2339项输入、原报告清单、科学字节、基准及默认入口的只读复核。

reproduce_zero_gaps.py / synthetic_gap_probes.json：仅软件合成反例，临时目录使用SYNTHETIC_SOFTWARE_PROBE_NOT_NATIVE_OR_FIELD_EVIDENCE标签。R1通过给函数供应合成元数据复现；R2只隔离内容检查并模拟授权解析，真实文件与哈希检查保持。没有真实VTK读回、原生执行或CASE写入。此前57+42套件未直接覆盖audit_outputs/verify_zero_receipt的这类正向内容/错配路径，故现有通过记录与本次发现不矛盾，不需要据此裁定历史原生结果失败。

本轮没有遇到不能由原始代码和有界合成探针独立核验的复杂证据矛盾；未调用其他模型或子代理，也不声称模型切换。

## 6. 后续最小范围及权限

建议下一步仅在新隔离候选修订R1/R2及补充正向/负向软件检查，保留现A、旧源码和原报告；同一ELF、四正式/十二零步计划、科学common、0.1%线性门、资源上限和旧S2基准保持。需核对新来源/路径、重新封存新A，不覆盖本A或借用旧A哈希。

这只是最小修订提案，本轮没有实施。修订/复核通过且真正获得12次零步+4次场读取授权后，再审资源并另存零步执行绑定、交付用户手动命令。当前不询问或伪造执行许可；不生成原生或正式命令。正式四条还须后续独立授权，不自动性能推进/重跑/扩时/进入S4或S5。

S2六条及网格结论不变。旧PERF日志例外、历史FAIL、F04 OPEN、作者声明范围及reference_qualified/physical_validation/MODEL_COMPARISON/submission_ready边界保持。共享状态按本轮HOLD结论更新，不回写旧A内的科学状态或原实施报告。
