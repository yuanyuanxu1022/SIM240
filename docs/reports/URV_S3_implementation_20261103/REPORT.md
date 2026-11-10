# S3 隔离接入与权限关闭的准备 A

日期：2026-11-03。采用S3-PR-v1。用户原话：“采用本最小范围后，隔离实现 S3 接入与软件检查，交付执行权限关闭的准备封存；原生审计和正式计算另行授权。”本轮未获得原生零步或正式计算授权，也未执行它们。AI辅助工程/证据报告，不构成人工科学终审。

## 1. 交付结论

S3隔离接入、软件检查与准备A封存完成。2339项输入当前逐项一致；57项新增S3软件测试、42项原检查器相关软件测试全部通过，22份Python源码通过AST语法检查。原common科学文件及check_results.py/evidence.py/read_fields.py字节保持S2原值；contracts.py仅增加S3来源分支，差分见implementation_delta.patch。

准备A：`CASE/unseen_v2_reference_S3_reuse_v1/evidence/preparation_A.json`，SHA256 `5d4e70d85d586b3cdf1ebca09f82f1f4abf90166642c34f1a5f4663cdeb4f02d`，侧文件preparation_A.sha256。kind=S3_PREPARATION_A_NOT_AUTHORIZATION。simulation_authorized/formal_simulation_authorized/native_zero_step_authorized/performance_time_stepping_authorized均false；approved_runs/approved_run_ids/approved_audit_run_ids及actual列表均空。

四个正式run_id仅预留，12个零步身份仅准备；原生调用0、真实VTK读取0、时间推进0、构建0。zero_audit_status=NOT_EXECUTED、formal_status=NOT_STARTED。源码/入口存在、软件通过及封存完整性均不能表述为S3几何/数值/线性控制通过。

## 2. 新增实现与职责

新CASE为CASE/unseen_v2_reference_S3_reuse_v1，新检查器为CASE/unseen_v2_reference_checker_S3_reuse_v1。旧CASE、源码、S2结果/旧接受和旧合同未改；2468项旧保护文件前后哈希一致。

- scripts/prepare_S3.py：四正式+十二零步身份/配置、默认关闭的A封存、未来需真实零步收据才可生成B的入口。原生二进制仅引用原S1文件，无C++拷贝或重编译。
- analysis/stage_s3.py、revision_s3_reuse.py：精确四条S3阶段/参数/资源/来源及分离授权检查。沿用S2原合同的合法来源链，不将S3冒充S2。正式执行必须引用未来通过零步审计的B及真实四条授权。
- scripts/run_S3.py：默认只读；正式授权后按低P→低T→高P→高T顺序，逐条原数值/几何/来源/场接受后才继续。P三点齐时先算控制，若失败则不会启动T高；原生/检查器失败或输入变化均停。无重试、扩时、S4/S5推进。
- scripts/audit_S3_zero.py：准备12次原生零步+4次初态实际场读回入口，执行必须有独立零步合同，禁止steady。除原零步几何/单位/执行计数外，核对半步力通量及方向；本轮没有运行这些入口的原生路径。
- analysis/s3_baselines.py、check_linearity.py：在各自原合同下固定S2中力两基准，核验新S3低/高点的完成/接受/原始输出及K，计算每方向(maxK-minK)/meanK≤0.001的局部报告。拒绝缺点、错方向/驱动力、合同/完成替换及未接受点，不调用要求24条的全局aggregate，不提升参考资格或评分V2。

## 3. 身份、物理与资源

|顺序|预留run_id|原矩阵planned_case_id|
|---|---|---|
|1|URV_S3_P_a50000_reuse_v1_20261103_01|URV1_U_REG_P_dx2p5_a50000|
|2|URV_S3_T_a50000_reuse_v1_20261103_01|URV1_U_REG_T_dx2p5_a50000|
|3|URV_S3_P_a200000_reuse_v1_20261103_01|URV1_U_REG_P_dx2p5_a200000|
|4|URV_S3_T_a200000_reuse_v1_20261103_01|URV1_U_REG_T_dx2p5_a200000|

四条均为U_REG、dx2.5nm、h60/d80/w120/周期240/Ly240nm、H100nm，P+y/T+x。流体rho1000kg/m³、nu1e-6m²/s、mu0.001Pa·s、tau1，原D3Q19_FORCE/ForcedBGK及固定Bouzidi壁面。J=速度体积分/平面面积，K=nu·J/a，单位m³。没有改变原质量门、观察量舍入、几何、统计窗2592、最大步150528或帧计划。

基准仍为S2两条a100000/dx2.5，原release SHA d08297ebda69d9698d40762f778eb43299fa3c01c35e5591b6d31b4e06ef26cd；K_P=5.919337058277595e-23、K_T=2.3663885892433063e-23m³。旧基准的配置、完成、接受及原始输出都纳入新只读来源闭包，未列入S3批准运行，也不重跑或改写原合同。

原S1 ELF SHA保持5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b；原真实构建、依赖、静/动态库及编译器来源均经来源检查。本轮只复用同一ELF和历史限定指令审计，不称新编译或重新反汇编通过；instruction_reuse_audit.json说明其范围。

资源仍单进程/单线程/单cuboid、overlap3、地址空间8GiB、前置可用内存12GiB、初始磁盘100GiB/逐条8GiB、输出每条4GiB、单条14400s。四条16小时求解预算，检查器另各3600s及I/O另计，不是预计耗时或严格总墙钟；后续授权/启动仍需当时资源检查。

## 4. 软件与拒绝路径验证

S3测试57项：精确四配置/十二零步、错误阶段/顺序/力/方向/身份、来源与库覆盖、跨合同中档基准哈希与K、基准冒用、三点线性等值/边界/超限、缺失/非有限/非正点、合成跨合同关联、错误新release/驱动力/接受/K或额外原始文件拒绝、准备权限关闭、默认只读、错误外部SHA、输出复用拒绝，以及纯模拟控制器的原生失败/检查失败/接受失败/漂移/线性失败即停和成功不进下一阶段。

原测试42项：test_checker/test_packet_guards/test_residuals，覆盖原科学算术及已修补的输出隔离/来源合同等接口。它们在隔离副本运行，软件fixture均标明人工合成，进程模拟不是真实求解或VTK读回证据。

封存后额外核查：真实准备A的正式默认入口退出0、零步默认入口退出0；在拦截全部子进程创建的环境中，对同一A请求--execute时两入口均退出2并拒绝；缺少真实零步时finalize-zero拒绝且B未生成。未创建launch_attempts/audit_attempts/analysis_results；四个正式与十二个零步目录仍只有run_config.txt及run_manifest.txt。没有交付正式或原生启动命令。

## 5. 权限与科学状态

本轮许可仅为实施和软件准备。零步12次原生调用+4次实际读回的授权、绑定与执行仍待后续；正式四条又须在真实零步通过后另行授权。S2既有许可不覆盖S3，准备A不能直接用于任何求解或原生审计。

NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false（未评价，非已计算失败）；S3控制尚未评价。REFERENCE_QUALIFIED_FOR_CASE/reference_qualified=false，MODEL_COMPARISON/physical_validation=NOT_EVALUATED，strict_error_bound_established/submission_ready=false。S2网格与接受结论不变；S3是同一几何控制，不增加未见几何计数。F04跨合同全局聚合仍OPEN，旧横槽FAIL/380差异、MRP静态FAIL、历史归因未建立和作者声明范围保持。

## 6. 证据入口与下一步

verification.json、scientific_files_unchanged.json、instruction_reuse_audit.json、implementation_delta.patch、两份软件测试最终日志、封存后四入口日志及report_manifest.json。代码和封存均留本地，未提交或推送。

下一步建议先只读复核本准备A与原S3-PR-v1范围；取得明确覆盖12次原生零步及4次初态场读回的授权后，再核对A及当时资源，另存零步执行绑定并交付一条用户手动命令。当前不生成/执行此命令，不进行性能推进或正式计算。后续B只能在真实审计通过后封存，不拿本轮软件fixture充作审计回执。
