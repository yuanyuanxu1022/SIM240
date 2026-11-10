# C04原公式沿槽对照包：静态准备完成，启动命令已核对

日期2026-10-30（Asia/Shanghai）。用户授权准备C04、沿用原SDI-v1定义和门槛，完成静态核对后交付命令。**C04输入与封装已备，静态核对通过；本轮没有启动流动求解。** 命令供用户在本机终端执行，实际run_id仍为空。

阅读：[准备包入口](../../../CASE/interface_static_darcy_v1_3/README.md) → [共同输入和C04规格](../../../CASE/interface_static_darcy_v1_3/common/C04_SPEC.md) → [静态审计证据](../../../CASE/interface_static_darcy_v1_3/reports/preparation.json) → [命令与身份核对](launch_command.json)。本C04是SDI-v1内部的原公式沿槽例，不是旧路线表Case04参数扫描。

## 1. 对照关系与不变的输入

C04直接与C02比较同方向下的原公式/V2输入；与C03比较同一原公式的沿槽/横槽变化。不能只改tmux会话名或运行编号代替相应输入。

|项目|C04设置|
|---|---|
|系数与方向|original_local_cubic，槽沿x、压力沿x，即沿槽|
|平均域与网格|24×48μm，平均厚度及计算层厚度125nm，16×32×1共512单元|
|边界|xLow/xHigh物理过压24/0Pa，y侧无通量，z为empty|
|物性和驱动|μ=0.001Pa·s、ρ=1000kg/m³、G=10⁶Pa/m|
|平均定义及阻力接口|U为液体体积平均，J=HU，D=H K⁻¹；总阻力不重复叠加厚度剪切|
|Kxx/Kyy（m³）|2.4088541666666665e-22 / 6.518158783783783e-23|
|Dxx/Dyy（m⁻²）|5.1891891891891894e14 / 1.917719468739877e15|
|线性和资源限制|归一化残差≤1e-12、relTol=0、最多2000次；每端串行300秒/2GiB预算|

K/D非对角项均为0；相对C03，两者主值同时交换。源系数按原协议C04条目与冻结哈希查找，并另按h75/d100nm的原局部立方律复算。C02同方向共同输入、thresholds及linear_solver均逐项相同；10份边界/网格/离散字典与C02逐字节相同，二维输入除Kxx/Kyy外相同。

不解惯性、厚度壁面剪切、Brinkman扩散、运动边界或两相，不加载porosityForce/另一份Darcy源；H恒定才能将div J与div U对应。V=0，F/V不适用。这里没有真实沟槽网格、局部应力、一般斜向边界或填充时间验证。

## 2. 本轮实际完成的核对

|核对|证据与结果|
|---|---|
|编译来源|两份C++、两份Make及两个二进制与原C01哈希相同；继承真实编译记录，没有新编译|
|网格|同一网格逐文件复制，在C04路径实际checkMesh，全几何/拓扑检查通过|
|输入/矩阵|二维audit-only、OF auditOnly均实际执行、退出0；OF仅装配对称正对角矩阵后退出，初始p=0，flow_solved=false|
|冻结定义|源系数/协议哈希、平均定义、thresholds和linear_solver核对，均保持原SDI-v1|
|检查器1.3.0|只改说明、版本及C04支持列表，全部函数AST与1.2.0相同|
|功能测试|15项人造数据测试通过，日志完整；包括错误身份、未支持C05、几何舍入/倾斜、平均厚度、守恒和符号异常|
|旧例回归|只读C01/C02/C03原始结果，各50项数值检查、指标、Gate和原始文件哈希与旧分析一致，仅忽略版本元数据|
|封装与只读预检|46份文件和21个运行库绑定，默认run_c04.py预检通过；未调用执行模式|
|命令核对|bash语法、目录/runner/编号核对通过；预留运行目录不存在、sdi_c04会话未占用；没有建立tmux会话|

本轮未修改求解器源码或原检查器/原包。15项功能测试与旧例3×50项回归不是C04流动结果。阶段证据分别见包内preparation.json、functional_tests.log/json、regression_summary.json，以及本目录[检查器diff](checker_1_2_to_1_3.diff)、[回归比较](regression_comparison.json)和三个回归JSON。

所有文件和库按本机路径绑定，不声称在任意其他机器上可直接运行。技术launch_ready=true只表示材料齐备，不能推断已经启动或科学验收通过。

## 3. 解析预期，仅供未来结果核对

原公式给出Kxx=K_parallel；同一24Pa压差下，C04解析Ux约1.927083333333333e-6m/s、Jx约2.4088541666666664e-13m²/s、Q约1.15625e-17m³/s。精确浮点值见[C04_expected.json](../../../CASE/interface_static_darcy_v1_3/common/C04_expected.json)，明确标记为非求解输出。

C04/C02解析Q比2.3130890243424327，C04/C03解析Q比3.6956052262174715。它们是原先设计的描述性预期，不新增倍率Gate，不以输入系数在两套平均程序中重现来证明原/V2物理准确性。固定系数、固定压差问题预期压力线性曲线相同，而流量随Kxx改变。

## 4. 当前状态、单例执行边界及后续验收

```text
protocol_id: SDI-v1
package/checker_version: 1.3.0
case_id: C04
planned_run_id: SDI_C04_v1_3_20261030_01
actual_run_id: null
source_prepared: true
compile_identity_verified: true (unchanged compiled programs reused)
new_compilation_performed: false
mesh_checked: true
matrix_assembly_audit: true
flow_solver_executed: false
run_completed: false
NUMERICAL_GATE: NOT_EVALUATED
RESULT_PASS: null
geometry_PASS: true (preparation static synthetic domain only)
physical_validation: NOT_EVALUATED
independent_human_acceptance: false
```

用户在本机终端执行本轮交付的单条tmux命令后，只运行C04二维与OF两个程序，保存参数/源码/二进制/协议绑定、完整日志、独立退出码及原始p/U/J/phi/phi_U。不复用C03编号或目录，不覆盖既有运行，失败/超时停、不重试、不进入C05。原始完成记录与外部验收分开。

完成后另按原SDI-v1检查C04自身的50项数值检查及几何/身份守卫，再与C02作同方向公式对照、与C03作同公式方向对照。压力、U/J、Q、恢复K、守恒、泄漏、面通量和耗散门槛均保留，完整列表见C04_SPEC及原protocol.json。无原始结果不填PASS，不调门槛。静态平均接口一致不构成真实沟槽独立物理验证、一般网格独立或挤压/填充准确性证据。

## 5. 保护、状态同步和停点

本轮变更限新目录CASE/interface_static_darcy_v1_3、新报告目录及项目状态/交接。准备前快照346份C01—C03旧包/运行及相关报告，前后文件集与SHA256保持，详见preservation_before.json、[verification.json](verification.json)。本轮无压力求解、重跑、拟合、真实N8提取、Git提交推送或对外发送。

C01/C02/C03既有SDI局部接口通过及C01严格零几何识别的原未评价记录保留。旧D4_N8_diag_v3_1_20261026_v1仍NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null；reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD与历史FAIL不变。

当前停点为“材料及启动命令已备，实际执行待用户”。下一具体动作是用户执行命令并返回终端输出（无输出也说明），再单次核查启动/完成状态。Codex不等待或持续轮询，不自行启动下一例。命令已准备/交付不等于用户已执行，actual_run_id需后续证据确认。

本报告沿用scientific-writing组织证据和限制，技能出处及既有引用见[原协议入口](../Static_Darcy_interface_protocol_20261030/README.md)。[项目当前状态](../SIM240_AI_CONTEXT.md)、[最新交接](../AI_HANDOFF_20261015.md)已同步，回执state_sync.json。来源及最终核对见[source_manifest.json](source_manifest.json)和verification.json。
