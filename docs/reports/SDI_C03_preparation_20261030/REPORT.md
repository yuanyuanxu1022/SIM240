# SDI-v1 C03原公式横槽对照：材料已备，保持未启动

核对日期2026-10-30。用户范围为“准备C03原公式横槽对照材料，保持相同边界、平均定义和验收门槛，暂不启动计算”。本次交付在独立目录，不启动压力求解，不授权下一例。

首先阅读[准备包入口](../../../CASE/interface_static_darcy_v1_2/README.md)和[具体规格及共同输入表](../../../CASE/interface_static_darcy_v1_2/common/C03_SPEC.md)。两个最小程序沿用已核对的C01版本；C03换回原局部立方律系数，沟槽沿y、驱动沿x，直接对照V2横槽C01。C02是V2沿槽例，本次只用于检查器旧例回归。

## 已验证的准备内容

|事项|本轮实际证据与范围|
|---|---|
|原公式系数选取|按原SDI-v1的C03条目及方向选择绑定系数表；audit_c03.py另按h75/d100nm的表达式重算K_parallel/K_perpendicular|
|物理输入不变|H=125nm，L=24×48μm，μ=0.001Pa·s、ρ=1000kg/m³，512单元，G=10⁶Pa/m；C01/C03 JSON共同字段逐项一致|
|边界和离散|0/p、blockMeshDict、controlDict、fvSchemes、fvSolution及5份网格文件与C01逐字节一致；二维除Kxx/Kyy以外的输入一致|
|平均及阻力口径|U为液体体积平均，J=HU，D=H K⁻¹，采用总阻力平均压力模型；不重复计算上下壁剪切|
|程序/编译来源|两份C++源码、两份Make配置和两个二进制与C01 SHA256一致；继承原真实编译证据，本次未新编译|
|网格与矩阵|实际checkMesh通过；二维audit-only与OF auditOnly均退出0、flow_solved=false；OF矩阵对称、最小对角3.712485923423402e-19，初始压力仍为0|
|检查器1.2.0|仅扩展C03支持及版本标记；全部函数AST与1.1.0相同，保留1.1既有几何识别修正和原阈值|
|功能测试|15项人造数据测试通过；不求解CFD，包括平均厚度、守恒、符号、几何舍入/倾斜和身份拒绝|
|C01/C02旧例回归|只读已有数据，各50项数值检查和全部指标/Gate/原始文件哈希与旧分析一致，仅忽略版本元数据；无重跑|
|准备封装|release_manifest绑定44文件、21运行库；默认只读preflight通过；技术launch_ready不授予启动权限|
|旧材料保持|准备前快照223份旧文件，结束时逐项验证文件集和SHA256，见preservation_verification.json|

完整静态输出在[preparation.json](../../../CASE/interface_static_darcy_v1_2/reports/preparation.json)及同目录三个日志；复用来源见solver_reuse.json和inherited_C01_preparation.json。新材料的本机库路径和上游绝对路径已绑定，这不是任意机器可直接运行的可移植性验收。

## 解析预期与后续比较

C03输入Kxx=6.518158783783783e-23m³、Kyy=2.4088541666666665e-22m³；Dxx=1.917719468739877e15m⁻²、Dyy=5.1891891891891894e14m⁻²。解析Ux约5.214527027027026e-7m/s，Jx约6.518158783783784e-14m²/s，出口Q约3.1287162162162162e-18m³/s。以上均来自输入公式，**没有C03计算结果**。

C03和C01应有相同线性压力场，流量比的解析预期为1.4313684610462438；此比值只用于描述性核对，不另设看结果后的倍率门槛。未来用户明确授权启动并完成后，先核全部原始证据和两端独立退出码，再用新检查器按同一SDI-v1判断C03自身，最后与C01比较压力、流量和恢复K。若有失败，保留原数据并停，不重试或调门槛。

本次没有改变原协议的任何thresholds或linear_solver字段，未重新拟合。所有数值门槛及符号/几何守卫见C03_SPEC.md及protocol.json；单例自检仍为每端23项、跨端4项共50项。C03/C01系数差导致的流量差只能说明公式对平均预测的影响，不构成“原公式/V2哪个准确”的独立证据。真实沟槽参考、未拟合条件、网格独立及物理准确性依然未完成。

## 当前状态与接续

```text
protocol_id: SDI-v1
package/checker_version: 1.2.0
case_id: C03
planned_run_id: SDI_C03_v1_2_20261030_01
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
geometry_PASS: true (synthetic average domain only)
physical_validation: NOT_EVALUATED
independent_human_acceptance: false
flow_run_authorized_by_preparation: false
```

未创建runs、SDI_output或时间1输出；本轮不交付启动命令，不建立tmux会话，不启动C03/C04或其他例。无下一增长算授权。接续动作是保持未启动；只有收到用户后续明确启动指令时才进入单例执行阶段，完成后另做结果分析。C01和C02原接口通过状态保留，原C01严格零几何识别的未评价记录保留。

旧D4_N8_diag_v3_1_20261026_v1的NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null不变；reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD及历史FAIL保持。无新拟合、真实N8提取、稿件修改、Git提交推送或对外发送。

## 可复核文件

- [C01_C03_input_comparison.json](C01_C03_input_comparison.json)：共同输入、唯一物理变化及预期。
- [checker_1_1_to_1_2.diff](checker_1_1_to_1_2.diff)、[regression_comparison.json](regression_comparison.json)：版本差异及旧例逐项比较。
- [C01_checker_1_2_regression.json](C01_checker_1_2_regression.json)、[C02_checker_1_2_regression.json](C02_checker_1_2_regression.json)：已有结果的只读复核。
- [preservation_before.json](preservation_before.json)、[preservation_verification.json](preservation_verification.json)：旧C01/C02封装、原结果和既有报告的保护核验。
- [source_manifest.json](source_manifest.json)、[verification.json](verification.json)：准备材料哈希及最终检查。
- [state_sync.json](state_sync.json)：状态/交接仅替换当前段落的更新回执。

新增路径为CASE/interface_static_darcy_v1_2/和本报告目录；常规状态维护为[SIM240_AI_CONTEXT.md](../SIM240_AI_CONTEXT.md)、[AI_HANDOFF_20261015.md](../AI_HANDOFF_20261015.md)。科学证据组织沿用scientific-writing，技能出处保留在原协议入口。实际审查者为AI，没有独立人工科学签字。
