# S4-MIP-v1：隔离接入、软件检查与准备A封存

完成时间：2026-11-03T20:46:06.396246+08:00。用户授权原话：“采用 S4-MIP-v1 最小范围后，隔离实现 S4 接入与软件检查，交付执行权限关闭的准备 A；原生审计、性能推进及正式计算仍另行授权。”本轮按已采用最小范围实施；原运行前范围PROTOCOL.md仍保留其原历史状态，不回写。新adoption.json记录本次真实采用及准备授权，不赋予执行许可。

## 1. 交付裁定

隔离S4接入已实现、120项软件检查全部通过，准备A已封存，两个真实默认只读入口均退出0。执行权限全部false，approved和actual列表均空。24个准备目录仅含run_config.txt及run_manifest.txt；无原生记录、初态场、正式结果、审计/启动尝试或准备B。

准备A：`CASE/unseen_v2_reference_S4_reuse_v1/evidence/preparation_A.json`，SHA256 `e9d12e68eaa324bd8e78ad57825710936f9e00518faf39337923b930ad82a165`，kind=S4_PREPARATION_A_NOT_AUTHORIZATION，2976项输入逐项一致，配套preparation_A.sha256一致。这是准备封存，不能用于执行；没有启动release或tmux命令。

本轮实现和软件检查不建立NUMERICAL_GATE/geometry_PASS/RESULT_PASS。S4仍NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false（未运行）；REFERENCE_QUALIFIED_FOR_CASE/reference_qualified=false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED、strict_error_bound_established/submission_ready=false，F04 OPEN_OUT_OF_SCOPE。

## 2. 架构、物理及最小改动

新增`CASE/unseen_v2_reference_S4_reuse_v1/`与`CASE/unseen_v2_reference_checker_S4_reuse_v1/`。物理内核仍在原S1绝对路径，二进制SHA `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`；没有复制源码为新内核，没有复制/重建ELF或捏造新构建记录。历史真实构建、1392依赖、3链接库、15动态库、编译器与S1限定指令审计被原样绑定和复核；本轮C++构建0、机器指令审计0，30份Python文件只做内存语法编译检查，不产生本地构建产物。

薄间隙U_THIN h30/d80/w120/P240/Ly240nm，H70nm、a1e5m/s²；P沿槽+y、T横槽+x，rho1000kg/m³、nu1e-6m²/s、mu.001Pa·s。J为核心速度体积分/平面面积，K=nu·J/a（m³），U=J/H。固定单相全充液、静止Bouzidi壁面、x/y周期、D3Q19_FORCE/ForcedBGK、tau1及半步力修正保持。原A1体积和MRP/旧质量观察量运算路径均未动。

10个common和check_results.py/evidence.py/read_fields.py共13科学文件逐字节不变；旧zero_evidence.py亦保持。新增zero_evidence_s4.py仅将精确原生记录数12改18、唯一读回数4改6及对应消息，不改R1/R2计算和核对。contracts.py仅新增精确S4来源分派，不改旧分支。source_and_scope_audit.json及差异patch可直接审查。

## 3. 实现入口与权限

|新增部分|作用与限制|
|---|---|
|stage_s4.py / revision_s4_reuse.py / s4_revision/anchor.json|精确阶段、六配置、顺序、目录、同一ELF和真实来源闭包；直接核对原S3合同、完成记录、接受/原始输出及控制，不把S4伪装成旧阶段|
|prepare_S4.py|材料化六正式/18零步身份、封存A，以及未来真实零步证据合格后才允许封存B；不调用进程|
|run_S4.py|默认只读，正式执行需独立真实授权、B及另行接受的资源范围；逐条完整检查后续行，失败即停；全六条后保存分方向网格报告，网格失败保留报告但不写S4完成标志|
|audit_S4_zero.py / zero_evidence_s4.py|默认只读；独立18+6授权后才允许describe/precheck/initialize，原生及初态读回各等待300s；保留R1实际参数、R2各自场路径/载荷/单位/通量关联与过程收据|
|s4_grid.py / check_s4_grid.py|从已接受六条的原始包、completion和接受记录按方向计算原网格指标；核对独立退出/输入/载荷/K/窗跨度；局部GRID_CHECKS_PASS与完整参考资格分开，不调用24项聚合或评分V2|

原S3来源/结果保留在原合同下，只读作为前置证据；旧授权明确没有S4权限。新适配核对原S3 2632输入、实际四条原始输出及完成接受、两方向控制与已有完整独立复核，不通过复制旧运行器或改旧stage获得许可。原S2/S3模板和结果未修改。

当前正式准备身份如下，均未批准或执行；零步18身份见identity_plan.json，六配置各describe/precheck/initialize。readback计划为6，实际0。

|预留正式run_id|方向|dx/nm|核心节点预期|窗 / 最大步|
|---|---|---:|---:|---:|
|`URV_S4_P_dx5_reuse_v1_20261103_01`|P|5|32,256|162 / 23232|
|`URV_S4_T_dx5_reuse_v1_20261103_01`|T|5|32,256|162 / 23232|
|`URV_S4_P_dx2p5_reuse_v1_20261103_01`|P|2.5|258,048|648 / 92928|
|`URV_S4_T_dx2p5_reuse_v1_20261103_01`|T|2.5|258,048|648 / 92928|
|`URV_S4_P_dx1p25_reuse_v1_20261103_01`|P|1.25|2,064,384|2592 / 371712|
|`URV_S4_T_dx1p25_reuse_v1_20261103_01`|T|1.25|2,064,384|2592 / 371712|

上述几何/时间是原输入静态预期，不是原生安装PASS。不得把prepared_run_ids当actual_formal_run_ids。

## 4. 软件检查、语法和真实只读验证

首次115项软件检查通过；补齐模拟零步18+6流程和资源前置检查后，最终120项全部通过，0失败/0错误。guarded_software_tests.log及software_verification.json记录最终结果。测试包含原科学算术/结果包拒绝、S4来源身份/权限/资源/目录拒绝、R1/R2逐记录参数和初态载荷关联、模拟求解及检查失败/超时/漂移即停、网格失败保留证据，以及模拟18原生+6读取的顺序和失败即停。合成材料只在明确标记的临时目录中，不作为真实审计/数值结果。

测试进程审计仅允许Python独立检查器CLI处理合成错误包；实际原生/VTK/编译进程0。模拟接口次数是软件行为证据，不能填入A的actual列表。未执行原生describe、precheck、initialize或steady，也未实际运行pvpython。

封存后分别真实运行run_S4.py和audit_S4_zero.py的默认只读入口（没有--execute），均退出0，分别确认PREPARATION_BINDING_CHECK及ZERO_PLAN_BINDING_CHECK、solver_executed=false。2976项输入、110份候选文件前后不变。两条进程命令和输出见sealed_A_verification.json与*.readonly.stdout/stderr；它们是读取软件元数据的Python调用，不是原生审计。

原始3106份受保护文件本轮未变；本轮新包110份与封存输入一致。源码/二进制存在、历史构建成功、当前软件检查、原生几何审计、正式计算与独立验收分别记录，不互相替代。

## 5. 准备A的当前关闭状态

simulation_authorized、formal_simulation_authorized、native_zero_step_authorized、initial_field_readback_authorized、performance_time_stepping_authorized、S5_authorized、automatic_retry_authorized和automatic_extension_authorized均false。approved_runs/approved_run_ids/approved_audit_run_ids/actual_formal_run_ids/actual_audit_run_ids均空。zero_audit_status=NOT_EXECUTED，performance_status=SEPARATE_RESOURCE_DECISION_PENDING。无launch_attempts、audit_attempts、analysis_results、preparation_B或正式结果。

未来仅把标志置true不能运行：零步必须有独立授权文件、原始A和精确18身份且授权记录覆盖18调用+6读回；正式须原B、真实六条授权及另行接受的六条资源决策文档。资源决策是单独前置，本轮没有采用或签发。原边界/统计/收敛/质量门不改。

## 6. 仍未验证与接续

本轮无新流场或物理结果，无法裁定S4几何安装、实际流速、守恒、收敛、网格指标或模型误差。原单条1/4/12h上限及细格若跑满最大步粗估约32h的预算风险保留；S4真实速度/峰值内存/收敛步数均未测。准备B后、正式绑定前另作资源决策，若需有限PERF另定范围和授权，不把本次软件模拟当性能实测。

S0/S1/S2/S3既有接受、旧v1 HOLD、旧横槽FAIL/380项差异、MRP静态FAIL、历史唯一归因未建立、作者非使用声明有限范围均保持；F04未实现或放行。S4网格指标将来也不能替代S5薄间隙驱动力检查或完整参考资格/模型评价。AI辅助实施和证据报告不代表人工科学终审。

下一具体动作：只读复核本准备A与已采用范围；获得明确覆盖18次原生零步+6次初态场读取的授权后，复核封存与届时资源，另存零步执行绑定并交付用户手动命令。当前不生成执行合同/命令，不自动启动。PERF及正式计算继续分别另行授权。

证据入口：sealed_A_verification.json、software_verification.json、guarded_software_tests.log、software_coverage.json、source_and_scope_audit.json、engineering_changes.json及patch、six_prepared_identities.json、protected_files_before.json、package_files_sha256.json和document_manifest.json。共享状态/最新交接已同步；无Git提交/推送。
