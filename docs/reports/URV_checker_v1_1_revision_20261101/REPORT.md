# URV 检查器 v1.1：F01—F03 最小修订与验证

2026-11-01。本轮授权：在新版本中修订前三项检查器缺口并验证，保留原准备封存；外部历史继续核查，S0保持未启动。

**F01、F02、F03 已在隔离检查器 v1.1 中修订并通过软件验证。** 新入口 [CASE/unseen_v2_reference_checker_v1_1](../../../CASE/unseen_v2_reference_checker_v1_1/README.md)。70组测试通过，其中35组为原回归、35组为新增修订验证。原准备CASE的830文件、1432项准备绑定及另选1725项旧证据/审查文件保持。本轮没有编译或运行OpenLB；S0没有启动，正式执行合同没有生效。

本报告沿用 scientific-writing 的证据组织规则，为AI参与的软件准备记录，不是独立人工科学验收。原问题和反例保留在 [只读复核报告](../URV_v1_readonly_review_S0_20261101/REPORT.md)，没有覆盖历史发现或历史FAIL。

## 实现范围

新版本仅复制必要的analysis/common及Python回归测试；不复制或修改求解程序，不移除原URV_PREPARATION_ONLY=1保护，不改变任何物理参数或数值门槛。原CASE路径继续是历史准备入口，新检查器是独立同级目录，避免在原830文件中新增或替换文件。

[check_results.py.diff](check_results.py.diff)与[read_fields.py.diff](read_fields.py.diff)给出相对原版的准确差异。[unchanged_numerics.json](unchanged_numerics.json)核对以下函数源码逐字节一致：diagnostics、check_slice、compare_legacy、aggregate，以及reader的payloads/leaves/audit；evidence.py整个模块、原common文件也逐字节一致。质量统计、通量单位、P/T方向、样本窗口、原K差1e-4、GCI与模型比较规则均未修改。

## F01：输出位置先检查，非法路径不写文件

原缺口为check_run先拒绝out位于run内，但main异常分支又向原args.out写failure.json。

修订后，公开check_run先规范化并核验目标，再独占创建新分析目录。原结果、其他批次结果、合同声明的输入/回归基准、原准备包及新检查器包均为保护对象；同目录、父子重叠、符号链接重叠及既有输出目录拒绝复用。失败记录只能写入本次合法创建的分析目录。批次先核对全部原结果，不能分析到后面才发现输出位置冲突。原生reader的独立CLI入口也在读取场之前做同样检查。

验证包括：out=raw、raw子目录、输入/输出符号链接、raw父目录、既有输出目录、批次第24条目录、合同中的回归基准、保护CASE目录。非法目标退出2，原目录无新增文件；合法全新目标在合同拒绝时保存失败记录，没有成功acceptance。独立reader非法路径测试只导入模块并执行保护，不读取任何VTK场数据。

## F02：回归差异先保存，再按原门槛停止

新增小函数regression_check，不改原compare_legacy算术。旧基准哈希核对后计算K新/旧值、相对差、全部共同列差异及轨迹长度，先保存regression_comparison.json，再分别判断K差≤1e-4和旧轨迹逐项相同。超限或差异仍失败，不降低门槛。

软件验证覆盖完全相同、共同列被改动、K差超限，以及外层失败回执与完整差异同时保留。另保存可复查例子：

- [旧h75 P完整20列自对照](validation_examples/existing_h75_P_self_comparison/regression_comparison.json)，4343行；
- [旧h75 T完整20列自对照](validation_examples/existing_h75_T_self_comparison/regression_comparison.json)，2954行；
- [人工改动一项J后的20列失败对照](validation_examples/SYNTHETIC_h75_changed_trajectory/analysis/regression_comparison.json)，差值已保存，legacy_gate_PASS=false。

前两项只验证已有控制轨迹的比较与保存，不是新S0结果；第三项为明确标记的人工副本，不是流场解。外层失败路径单元测试只替换内部调度，实际差异函数没有mock；没有将这种测试称为新URV完整结果端到端验收。若输入来源已不符或文件本身非法，仍先拒绝，不生成无法计算的假差值。

## F03：强制完整来源角色和逐条运行身份

新增contracts.py，要求未来执行合同schema_version=URV-EXEC-1.1，保留protocol_id=URV-v1。未来真实执行前必须绑定native二进制、cpp/h源、构建配方、本次构建记录、编译器、.d依赖、链接库与捕获的动态库，以及新检查器/协议全文件。构建记录的路径和哈希要与总清单一致；.d首个规则和ldd捕获文件被独立解析，不能只靠手填短清单。要求原物理内核源码哈希与原准备锚点一致，准备构建及模糊的宏定义被拒绝。

每条approved_runs将run_id、planned_case_id、run_config_path/config SHA及唯一output_directory对应；批准名单必须完全一致且不重复。配置须属于单一冻结阶段的矩阵，方向、物理输入、时间与帧计划一致；实际完成记录再核case/配置字节/目录，防止只有编号在白名单却对应了另一条配置。运行目录不可复用或嵌套。

验证覆盖：完整人工清单可通过一致性检查；漏程序、源、依赖、动态库、链接库、配置SHA或运行对应时拒绝；变更物理源、混入准备宏、互换case/阶段/目录、重复编号时拒绝；历史PENDING仍拒绝。人工构建的程序/编译器/库只是惰性占位字节，不会执行，测试中的CONFIRMED和授权标记不是作者确认或实际许可。

前轮曾被原binding接受的缺项人工合同，已通过新版真实CLI再次检查，退出2并保留[拒绝回执](validation_examples/F03_old_deficient_contract_rejected/failure.json)，无成功acceptance。

未来合同的具体字段见[合同要求](../../../CASE/unseen_v2_reference_checker_v1_1/EXECUTION_CONTRACT_REQUIREMENTS.md)。校验器保证声明的覆盖和一致性；不冒充验证作者事实或密码学证明编译记录真实。外部合同SHA、实际构建日志和独立退出仍须有真实证据。本轮没有生成此类生效合同。

## 验证与保护

[tests_final.log](tests_final.log)：**70测试、0失败、0错误**，35原回归+35新增。首轮原回归35通过、随后69通过，补独立reader非法目标覆盖后最终70通过；没有隐藏失败或放宽门槛。8个Python源在内存中完成语法/字节码编译，不写CASE缓存，也不是native编译。

[verification.json](verification.json)记录原830文件、1432项准备绑定和1725项额外保护文件均匹配；其中额外保护包含前轮审查材料及既有历史源/结果。原准备seal SHA仍为e0eb9a54c1c1168d25483a085e70462d04cfa76aeb4922dddbea17b07b1811cb。此前失败反例、原细T FAIL、C/h75限定资格、V2/G4锁和旧D4预测HOLD保持。没有Git提交推送或对外发送项目材料。

本版软件准备结论为F01/F02/F03=ADDRESSED_AND_TESTED，**不等于S0已通过或正式执行就绪**。尚无新URV完整稳态输出，因此完整新记录端到端验收仍NOT_EVALUATED。

## 停点

外部历史继续沿用用户原话“尚不能确认，需要核查”，记录仍为PENDING_AUTHOR_CHECK；本轮没有收到新事实确认，没有用测试中的CONFIRMED覆盖它。原S0草案保持未生效，actual_formal_run_ids=[]，S0_started=false。

F04分阶段多合同汇总入口在本轮范围外，仍OPEN。原aggregate函数保持，不因为修复前三项提前合并授权全部24条。它不阻止未来单条S0验收，但后续汇总前需独立修订。

下一具体动作：只读复核v1.1修订、合同要求与证据；作者继续核查外部数据历史。获得真实确认后，再另行准备S0正式构建、逐条配置/编号/目录、独立退出与资源捕获及生效合同；继续不自动启动。本轮新正式NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、reference_qualified=false、strict_error_bound_established=false、submission_ready=false。

科研技能方法归属沿用同日已核条目：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://arxiv.org/abs/2609.00065)，DOI [10.48550/arXiv.2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。仅作AI流程归属，不作本项目数值/物理证据；本轮未新增文献检索。
