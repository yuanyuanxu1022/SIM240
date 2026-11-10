# 独立提取器v2：四项修订与人工验证

2026-10-26。状态：**FOUR_PREPARATION_FINDINGS_ADDRESSED_SYNTHETIC_VALIDATION_PASS_REAL_CLOSED**。

用户授权完成B01/B02/C01/C02的小版本修订及人工验证，保持真实N8提取与求解关闭。本轮在新目录实施，未覆盖前一版源码、17组旧测试、只读审查或实际记录。沿用[已审理论判据](../G4_reference_criteria_review_20261026/CRITERIA_REVISION.md)，未改变物理门槛或审定严格误差界；无需在本轮作理论重推或声称模型切换。报告按scientific-writing的证据边界组织。

## 1. 交付与四项闭合范围

代码目录：`CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/offline_extractor_revision_v2_20261026/`。numerics.py与原test_fixtures.py逐字节保持；extractor.py保留数值核心和人工归档接口，将真实入口改为无条件拒绝。新增绑定读取、分析记录、合成记录生成、新夹具及合成独立进程入口；没有重构生产求解代码。

|问题|本轮具体修订|已有证据|
|---|---|---|
|B01 原验收与清单未固定连接|同时固定验收证书SHA、原accepted-input清单SHA、48文件inventory摘要、代码/规范摘要、analysis_id及输出位置；inventory每项必须已列入原验收清单|实际记录的[绑定草案](real_N8_binding_DRAFT.json)、[信任锚草案](real_N8_trust_anchor_DRAFT.json)、[静态核对](real_binding_static_check.json)；清单替换、证书与原索引篡改拒绝夹具|
|B02 真实格式读取链未测|分离记录schema校验与公开真实入口；以人工标记和人工编号测试相同必需字段结构、48文件、8+17数组；解码使用同一份已核SHA的字节快照，读取后与分析后再核输入|成功读取、错run/case、非零退出、不完整归档、错完成状态、错摘要、缺文件/改字节、错shape/dtype、读取期间变化等夹具|
|C01 非零L2解析夹具不足|加入uh=(z(1−z),0)、ph=x−1相对于既有MMS的闭式误差积分，核分子、分母和平方根；再核压力加17及编号重排|新增nonzero_L2_closed_form测试，使用原2e−11绝对/相对夹具容差|
|C02 完整分析记录与比较规则缺失|预先固定归一化软件一致性容差、阈值附近状态、完整有限JSON、唯一新输出、输入前后摘要、事件/错误日志、记录退出码、输出manifest及独立进程退出|完整人工成功/失败产物、独立进程0/2退出核对、缺项/非有限/阈值附近与不覆盖测试|

[resolution.json](resolution.json)记录四项为“准备层实现并经人工验证，真实执行关闭”。这不等于真实N8已完成指标提取或独立验收。

## 2. 实际N8绑定：固定来源但不执行

原独立验收的input_sha256.json含150项输入，其中覆盖实际N8的全部48份记录；本轮逐项核其SHA与冻结审查清单和当前文件一致。绑定的源run_id仍为`D4_N8_diag_v3_1_20261026_v1`，原证书仍为ONE_N8_DIAGNOSTIC_ACCEPTED，没有创建新求解run_id。

绑定草案只准备将来的分析标识、源路径、原合同摘要、验收证书、原验收输入清单、代码/规范及输出位置。status=DRAFT_NOT_APPROVED_NOT_EXECUTABLE、approval=null、real_extraction_authorized=false、solver_authorized=false。拟议实际分析输出目录未创建。

本版`extract_real_record`无条件在路径访问前拒绝；可测试的记录读取器只接受SYNTHETIC_EXTRACTOR_REVISION_NOT_RESULT，且在读payload前拒绝真实N8目录及其上/下级路径。没有通过改全局布尔值、猴子补丁或沿用旧运行许可加载真实N8。

人工包的证书状态、record_kind与source_run_id均明确标人工，不能冒充原独立验收。临时夹具中的“重新密封”仅用于构造特定内部格式错误，使测试到达相应校验层；针对已固定锚的篡改测试不重新密封。实际N8的原验收清单没有重写。

## 3. 验证结果

[完整单元/回归日志](fixtures_run1.log)与[机器记录](fixture_results.json)：**30组测试，0失败、0错误、0跳过，测试进程exit0**。其中17组是原有夹具在新副本上的回归，13组是本次新增修订夹具；旧17组历史记录保持原样，不把回归计作17次新物理验证。

同格式人工包采用nx16/nz8：153网格顶点、256三角形、1275混合自由度、39周期配对，8组system数组与17组solution数组。人工CSR是特意构造的简单算术对象，不是MMS离散方程矩阵；节点场不是PDE求解结果。测试成功只证明规定代码路径/夹具的一致性。

另通过两个独立Python进程核对分析退出与产物：

|人工进程|外层实际退出|分析记录退出|结果|
|---|---:|---:|---|
|independent_success|0|0|SYNTHETIC_METRICS_RECORDED，完整指标、检查、状态、事件、清单|
|independent_failure|2|2|预设输入改字节触发RECORD_BYTES_CHANGED，保留failure/traceback/事件与失败状态，没有写成功指标|

成功例指人工数据的程序运行和软件一致性记录成功，不表示该人工场满足MMS方程或物理精度门槛。失败例是预期拒绝测试，不是实际N8失败。其源包、绑定、信任锚、stdout/stderr、外层process.exit_code及输出留在本目录下同名子目录，全部标人工。

## 4. 分析记录与软件判据

代码目录ANALYSIS_SPEC.md在本轮人工测试前写入并绑定SHA。主要控制如下：

- 独立压力测试函数积分与CSR压力行残差差异，以完整非零rhs范数归一；软件一致性额度2e−11。
- 回填/周期/壁面误差按保存场幅值归一，软件额度2e−11；壁面和周期索引必须完整。后处理求积变化沿用1e−8建议。
- 64个float64机器精度的绝对邻域仅作软件NEAR_THRESHOLD区分，不称误差界或可信区间；缺项/非有限量不判通过。
- 能量、L2、代数残差等物理诊断全部保存，但不在这里激活物理Gate。NUMERICAL_GATE/RESULT_PASS/geometry_PASS不被软件一致性PASS替代。
- 必交产物为input_binding、events、metrics、checks、status、analysis.exit_code及output_manifest；失败保留failure与traceback。输入或绑定无效、尚未确定安全输出目录时，只拒绝并保留进程stderr，不向不可信位置写文件。
- 新输出目录不得与源目录重叠，已有输出拒绝覆盖；无自动重试、恢复或启动后项。独立合成CLI将分析退出码作为进程退出返回。

这些是固定的软件检查与记录规则，不改变连续性、能量或参考误差预算的理论定义。夹具通过不证明参考预算中的后处理误差额度或任何严格误差界。

## 5. 本轮边界、停点与接续

本轮未导入PDE后端、后端建网/组装求解、编译OpenLB、运行拟合或Git提交推送；实际N8.npy只参与逐文件字节SHA核验，没有用np.load加载或积分。旧源码、科学协议、G4锁、旧FAIL和实际记录均保持，证据见[verification.json](verification.json)与[source_manifest.json](source_manifest.json)。

当前reference_qualified=false、strict_error_bound_established=false、NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、submission_ready=false、预测HOLD。实际N8仍只具备原代数/记录链诊断验收，真实场指标未评估。

四项在本轮准备范围内已补齐；下一具体动作是只读复核v2代码、绑定草案和本次人工证据。若之后另获已有记录分析授权，再处理真实N8；本版没有真实分析执行入口，亦不提供求解命令。标量/沟槽、其余17项及公式保留预测不属于本次修订。

已同步SIM240_AI_CONTEXT.md及最新AI_HANDOFF_20261015.md。辅助软件方法来源沿用本会话当日已核记录：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://arxiv.org/abs/2609.00065)，当前v2；不作为CFD精度证据。作者最终科学采用及严格界审定未发生。
