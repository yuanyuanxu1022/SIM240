# S2-MIP-v1 隔离实现与软件检查报告

日期：2026-11-02。结论：**S2 阶段绑定、默认只读的正式控制器和六配置零步审计入口已经隔离实现，78项软件检查通过；仍使用同一 S1 求解二进制。** 没有构建、OpenLB调用、原生零步、VTK实读、性能推进或正式计算。原生审计和正式流场的科学门均未验收。

## 1. 授权范围与改动路径

用户采用 S2-MIP-v1，授权隔离实现阶段绑定、控制器与软件检查，准备六配置零步审计入口；原生审计/性能推进按明确覆盖的授权执行，正式计算另行授权。本轮原生执行授权保持关闭，没有据此启动审计。逐字记录在 `adoption.json` 与新 CASE 的 `evidence/adoption.json`。

新增工程目录：

- `CASE/unseen_v2_reference_S2_reuse_v1/`：README、三条Python入口、六条正式准备身份、18条零步准备身份与A封存；没有新 native src/build，也没有性能执行脚本。
- `CASE/unseen_v2_reference_checker_S2_reuse_v1/`：复制的原科学检查/门槛、S2精确来源分支与阶段守卫、保留的42项软件检查和新增36项检查。

核心新增文件：`analysis/revision_s2_reuse.py`、`analysis/stage_s2.py`、`s2_revision/anchor.json`；`scripts/prepare_S2.py`、`scripts/run_S2.py`、`scripts/audit_S2_zero.py`；`tests/test_s2.py`。隔离 `contracts.py` 只新增S2精确分派，差异见 `contracts_delta.patch`。原S1/S0源码、合同、输出、检查器及门槛均未修改。

## 2. 同一二进制复用与科学计算保持

固定引用 `CASE/unseen_v2_reference_S1_a1_v1/build/urv_reference`，SHA256：

`5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`

来源角色直接指向真实的既有构建记录、4项源文件、依赖、编译器、静态/动态库及ldd记录，没有复制ELF或虚构新构建。新阶段的真实provenance核对通过，仍检查1392项依赖、3项静态库、15项动态库。OpenLB提交仍为 `882924a9cfc8dcdf82909e39530789cb6f5ebcc4`。

原 `check_results.py`、`evidence.py`、`read_fields.py` 与 common 全部文件按字节保持S1版本。A1/S1的测量舍入与限定指令审计只作为精确ELF的历史限定证据复用；本轮不重做机器审计，不主张全路径机器等价。新分支重构同一基线/diff并核对原审计的二进制身份，绑定已接受S0、两条S1 acceptance/completion与原输出哈希。它不重新计算S0/S1或扩大其科学结论。

## 3. 当前封存与身份

A封存：`CASE/unseen_v2_reference_S2_reuse_v1/evidence/preparation_A.json`。

- kind=`S2_PREPARATION_A_NOT_AUTHORIZATION`；1584项绑定输入。
- SHA256=`320d1d8469e2db50db161f91bca20339e60cb9054875722e9cbb50d9ab236e62`。
- simulation_authorized=false、native_zero_step_authorized=false、performance_time_stepping_authorized=false。
- approved_run_ids=[]、approved_runs=[]、actual_formal_run_ids=[]、actual_audit_run_ids=[]。
- 六条正式准备身份和18条零步身份仅保留配置/manifest；24个输出目录都只有这两个文件，没有运行日志或结果。

六个正式准备run_id按顺序为 `URV_S2_P_dx5_reuse_v1_20261102_01`、`URV_S2_T_dx5_reuse_v1_20261102_01`、`URV_S2_P_dx2p5_reuse_v1_20261102_01`、`URV_S2_T_dx2p5_reuse_v1_20261102_01`、`URV_S2_P_dx1p25_reuse_v1_20261102_01`、`URV_S2_T_dx1p25_reuse_v1_20261102_01`。这些是准备身份，不能写成实际运行。完整映射在 `evidence/identity_plan.json`。

初始软件候选封存及77项初检记录已保存为 `preparation_A_initial_software_candidate.json`、`entry_audit_initial_candidate.json`、`software_tests_initial_candidate.log`。封存前复核补齐了“正式release必须绑定真实B封存”的守卫及其检查，最终78项通过后重新生成当前A；旧候选仅是软件准备历史，不得拿其SHA运行。本轮没有原生执行或科学失败被回写。

## 4. 控制器与审计入口的行为

正式入口默认只读。执行需新的真实授权、精确六条S2身份/配置、每网格1/4/12小时时限及真实B封存；B必须包含完整18次零步审计、六个实际初态字段读取及原始输出闭包。性能release、S1许可、单独授权布尔值或只有零步摘要都不能替代。逐条原生正常完成→原独立数值/几何/来源检查通过→下一条；沟槽smooth=null不误作FAIL；资源停止、超时、来源变化或独立失败即停，不重试、不延时、不进S3。

零步入口默认只读。执行只接受独立 `AUTHORIZED_ZERO_STEP_AUDIT_RELEASE`，覆盖所有18个精确审计身份、A封存及真实授权证据。模式白名单只有describe/precheck/initialize；每条300s、初态实读300s，资源保持原8GiB地址/12GiB可用内存/100GiB初始及8GiB逐条磁盘。审计分别核对参数、独立几何/壁面、初态质量/半步力流量及真实VTK；时间推进必须为0。任何失败保留证据停止。

`prepare_S2.py finalize-zero` 只能消费真实已完成的审计记录封存B，不调用求解器、不授权计算。目前B不存在。六配置原生和性能授权均未获得；后续长批仍由用户手动后台启动，AI不持续等待或轮询。

## 5. 实际执行的软件验证

完整Python软件检查：**78项通过=原42项＋S2新增36项**，日志 `software_tests.log`。覆盖真实复用来源正例、原科学文件逐字节保持、六配置/18模式与精确时间算术、阶段/身份/几何/库/资源/目录/授权拒绝、B封存缺失拒绝、正式流程各类失败不进下一条，以及模拟六条成功后不进S3。假设的求解/验收流程使用显式标记的软件模拟；没有编译C++或实际运行OpenLB/VTK。

18个Python文件AST解析通过，见 `syntax_audit.json`。最终A封存后实际调用四个Python命令行入口检查，见 `entry_audit.json`：

| 入口检查 | 实际退出 | 求解器/字段读取器 |
|---|---:|---|
| 正式入口默认只读 | 0 | 未调用 |
| 零步入口默认只读 | 0 | 未调用 |
| 用关闭许可A请求正式execute | 2，正确拒绝 | 未调用 |
| 用关闭许可A请求零步execute | 2，正确拒绝 | 未调用 |

没有生成launch_attempts、audit_attempts或analysis_results。源/库/二进制哈希、24个原生目录只含配置及原保护文件的最终核查见 `verification.json`。CLI退出2是本轮预期的授权拒绝证据，不是原生计算FAIL；也不能把软件退出0称数值PASS。

## 6. 科学状态、限制与下一动作

S2 NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false、REFERENCE_QUALIFIED_FOR_CASE=false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED。项目reference_qualified/strict_error_bound_established/submission_ready=false；原24项仍只完成S0/S1共4项，剩20。

保留历史v1.2横槽FAIL/380差异、前MRP静态FAIL、HISTORICAL_EXCLUSIVE_ATTRIBUTION=NOT_ESTABLISHED、D4预测HOLD、GDI01及作者外部数据声明的原范围。F04聚合OPEN。S1正偏来源仍未分解，S2网格不替代平板收敛；性能协议仍需实际证据，软件通过不能证明12小时可行。

下一动作：取得明确覆盖六配置原生零步的授权后，核对当前A和资源、另存真实零步授权release并交付一条绑定命令，由用户手动启动；实际完成后再独立核对并封存B。性能推进和正式S2计算各按其明确授权与协议执行，当前不启动。绑定字段说明见 `BINDING_INTERFACE.md`。

本报告使用scientific-writing整理证据，方法引用沿用已采用 `URV_S2_minimum_preparation_protocol_20261102/PROTOCOL.md` 末尾的Scientific Agent Skills引用；AI检查不等于人工科学终审或实验验证。项目当前状态与日期最新交接已同步。
