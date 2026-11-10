# S3 v1.1 准备 A 与 R1/R2 范围只读复核

日期：2026-11-03，复核时间12:31:37 +08:00。用户范围：只读复核新版A与R1/R2；通过且获得明确12次原生零步+4次初态场读取授权后才另存执行绑定/手动命令，当前不启动。本消息是条件要求，本轮没有新的原生执行授权。使用peer-review技能组织项目内部证据审查，不构成人工科学终审。

## 1. 审查结论

**本轮准备包及R1/R2修订范围审查通过，真实原生审计仍待授权、绑定和用户手动执行。**

BINDING_INTEGRITY_PASS=true；R1_R2_SCOPE_REVIEW_PASS=true；preparation_review=PASS_WITH_NATIVE_AUDIT_PENDING。该结论限定于v1.1，不撤销旧v1准备A的HOLD，也不声称真实原生/几何/数值/线性控制通过。

新版A：CASE/unseen_v2_reference_S3_reuse_v1_1/evidence/preparation_A.json，SHA256 7f6ca19de96949a537802f92804c787cf092e8de0eb10c681ed279736a2d3695，2437项绑定输入当前完全一致，SHA侧文件一致。原A SHA5d4e70d85d586b3cdf1ebca09f82f1f4abf90166642c34f1a5f4663cdeb4f02d及其2339项输入均原样保留。

## 2. 范围与来源

四正式身份仍只对应2.5nm、U_REG、低/高驱动力a50000/200000的沿槽P/横槽T；中档a100000两条在S2原合同下只读引用，未列入S3新批准列表。原几何/物性、J/K平均定义、碰撞/体力/边界、质量/收敛/0.1%线性门与原资源限制未改变。预留4正式与12零步配置均仅配置/manifest，预计初态实际读取4次。

本轮重新核对同一原S1 ELF及构建/依赖/库来源链，SHA5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b保持；13份科学common/核心检查器文件字节同原包。新来源锚、父A和S2合同关系一致。没有C++修改/重编译或新反汇编，不把历史限定指令结论扩大。

S2两中格K仍P=5.919337058277595e-23、T=2.3663885892433063e-23m³；原合同d08297ebda69d9698d40762f778eb43299fa3c01c35e5591b6d31b4e06ef26cd与实际配置/完成/接受/原始输出绑定通过。没有把S2原结果改成S3合同下结果，没有评分V2。

## 3. R1/R2闭合范围的核查

R1：zero_evidence.validate_zero_outputs逐模式核对effective的方向、驱动力、几何/网格/物性/时间/面积/体积/步数及零步标志，检查原生独立进程receipt、退出文件与execution_audit。initialize保持原质量/几何/半步J检查，并关联实际result身份与初帧。原生零步入口调用该检查后才记录该条完成。

R2：stage_s3.verify_zero_receipt在核验授权与原始清单后调用validate_audit_records，从计划逐条关联case/run_id/mode/output/A指纹，重读每次原始输出；四初始化报告必须各自匹配唯一case路径与读取器正常退出，核对帧0、核心节点、单位、原result与导出通量及半步力响应。从自身初始化目录PVD/VTM/VTI重建引用闭包并核对载荷指纹及原始绑定。执行入口读回后也调用validate_initial_readback；两处没有分离成不同判据。

没有发现此次R1/R2修订遗漏原反例或扩大到物理内核/科学阈值的变更。这个结论是有范围的代码/软件证据审查，不是穷尽所有潜在软件缺陷的证明，更不是实际原生审计替代。

## 4. 本轮独立定向探针与已有软件证据

本轮不重跑整套130项。已校验既有修订报告清单、封存后130项退出0/全部通过的日志与postseal记录，并确认对应封存当前未变。

另做11个有明确SYNTHETIC标签的有界软件探针：1个完整十二记录/四读回正常合成路径接受；10个负例分别为错误effective驱动力、方向、dx、nu、零步标志，重复读回报告、错误初态J、跨配置载荷、读取器非零退出、非零原生推进。十个负例全部被拒绝，具体异常在targeted_probe_results.json。

上述内容探针沿用原复现的隔离方式：临时目录模拟授权解析以单独检验内容分支，真实文件/哈希/逐记录检查实际运行；authority_checks_mocked=true。它们不是真实授权，不表示原生调用或VTK读取发生。没有把合成actual_reader标志算作真实读取。

真实准备A的正式/零步默认入口本轮均只读退出0；在拦截全部子进程创建条件下完成，Popen调用0。直接权限检查确认同一A被零步与正式授权验证器拒绝，不能按默认检查通过推导可执行。

## 5. 权限、边界及停点

simulation_authorized/formal_simulation_authorized/native_zero_step_authorized/performance_time_stepping_authorized均false；approved与actual列表空。没有B、audit_attempts、launch_attempts或analysis_results。当前没有新的执行合同或启动命令，也没有运行器原生/VTK子进程。

本轮CASE写入0、构建0、原生0、VTK读取器0、时间推进0。2464份准备/代码/旧证据/修订报告保护文件结束时一致；原准备和历史报告未改。仅新增本报告目录和共享状态维护。

NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false（未运行）、参考资格false、MODEL_COMPARISON/physical_validation未评价、submission_ready=false。旧v1 HOLD、S2接受/网格结论、历史FAIL、旧PERF日志例外、F04 OPEN与作者外部声明范围保持。

## 6. 后续允许的范围

技术前置复核已通过。后续若获得明确覆盖v1.1的12次原生零步及4次初态实际场读取授权，只生成独立零步执行绑定和一条由用户手动运行的命令；绑定前须重核A、输入与净目录、同一ELF/环境和届时资源，不用当前资源快照作将来保证，不覆盖A或挪用S2/旧S3许可。

新零步合同应保留formal_simulation_authorized=false、performance_time_stepping_authorized=false、simulation_authorized=false，明确仅批准十二零步ID与四初始化读回；用户手动启动，AI不执行。实际完成后再按原协议独立审核，合格后才另存关闭权限的B。正式四条仍另行授权，不自动性能推进、求解、重跑、加时或进入S4/S5。

证据入口：verification.json、targeted_probe_results.json、protected_files_before.json、review.py、report_manifest.json。当前停在准备包只读复核通过，等待真实零步授权。
