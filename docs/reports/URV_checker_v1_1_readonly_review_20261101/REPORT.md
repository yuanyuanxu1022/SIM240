# URV v1.1 只读复核与合同要求对应检查

2026-11-01。用户范围：只读复核v1.1与合同要求，继续核实外部数据历史；获得真实确认后再准备S0正式执行绑定，保持不自动启动。

**本轮复核完成，但v1.1尚不能作为S0正式执行绑定的已放行检查器。** 已封存内容保持，70组现有软件测试本轮再次全部通过；额外两组隔离人工检查确认F01和F03各有一项残留边界。F02差异先保存的修订在本轮检查范围内成立。原70通过记录不撤销、不覆写，也不能推成所有输入边界均已覆盖。

采用peer-review证据对应流程，属作者请求的AI自审，不是独立人工或期刊审稿。授权和处理边界由[review_intake.json](review_intake.json)、[过程声明检查](intake_validation.json)记录；自有项目/非期刊、AI处理与保留规则沿用[前轮范围说明](../URV_v1_readonly_review_S0_20261101/INTAKE_NOTES.md)。声明检查通过不代表科学或执行放行。

## 仍成立的部分

两份封存及其输入当前匹配：原准备seal SHA=e0eb9a54c1c1168d25483a085e70462d04cfa76aeb4922dddbea17b07b1811cb，1432输入；检查器revision seal SHA=df3003c57560576548e9b0988507bc2f7a63982522988d5a284cc75fdd0f35ce，21输入。原830文件准备包、v1.1包、前轮报告、历史源/结果均按本轮前后清单核对，不改动。

本轮[70组现有测试复跑](existing_70_tests.log)全部通过，没有改测试以取得此结果。原diagnostics/check_slice/compare_legacy/aggregate及reader的payloads/leaves/audit与原实现逐字节一致。没有更改平均、方向、单位、质量门槛、回归K差1e-4或敏感性/GCI规则。

F01对正常合同下的raw自身、子目录、父目录、符号链接、既有输出和批次目录保护有效；新增反例是“合同声明不完整”与“另一处有效基准目录”同时存在的组合，原70未覆盖。

F02的源码顺序、通过/失败单元测试和已保存的完整20列样例一致。旧P4343行、旧T2954行自对照，以及人工修改一项J后失败的报告，完整20列对象均在，人工修改例legacy_gate_PASS=false。它们证明比较/保存行为，不是新S0结果；没有在本轮运行实际新流场作端到端验证。

F03的来源角色、依赖闭包、运行编号—配置—目录对应、单阶段约束等主要检查已实际实施；旧缺项人工合同被拒绝的事实仍成立。本轮复现的是捕获编译命令解析中的另一种表示方式，不把它说成全部来源校验无效。

## R1：声明解析失败后，已知保护路径被清空

**位置：** [contracts.py:16](../../../CASE/unseen_v2_reference_checker_v1_1/analysis/contracts.py#L16)的release_inputs，尤其第24—26行。

**观察与依据：** 函数先收集输入、其他运行目录和基准目录；任一声明缺字段时，它在except中返回空列表。该列表用于公开check_run的输出保护；输出目录是在binding拒绝之前创建的。

**实际反例：** 在本报告的新人工目录内建立当前raw与另一个baseline raw；合同始终保留有效的P基准声明。对照组运行声明含output_directory，基准内分析输出被拒绝且无写入。只删该运行声明的output_directory，release_inputs返回[]，随后在同一个人工baseline下创建analysis_malformed/failure.json。两次CLI均退出2，只有后者发生禁止的目录内写入。见[对照证据](synthetic_probes/R1_malformed_metadata/verification.json)及其两份CLI日志。

**影响：** 退出2不等于只读边界保持；在正常文件系统和普通缺字段错误下仍可发生。所有反例只在新人工目录，没有碰实际历史结果。

**最小行动：** 声明解析遇错应在任何mkdir/save前失败；不能清空保护集合后继续创建分析目录。下一修订至少覆盖“有效基准+另一条不完整声明”的组合，并同时核无新增目录/文件。本轮按只读授权不修源码，R1保留为S0绑定前缺口。

## R2：分离式宏声明未进入唯一性检查

**位置：** [contracts.py:79](../../../CASE/unseen_v2_reference_checker_v1_1/analysis/contracts.py#L79)到第81行。

**观察与依据：** shlex拆分后，只选取以-DURV_PREPARATION_ONLY或-UURV_PREPARATION_ONLY开头的token。合同要求的“唯一明确为0”没有覆盖-D与宏名分成两个token的捕获记录。

**实际反例：** 先用原完整人工合同作成功对照，再把捕获命令增加`-D URV_PREPARATION_ONLY=1`，保留原`-DURV_PREPARATION_ONLY=0`，同步人工构建记录及合同哈希。binding仍返回成功。见[捕获文本检查证据](synthetic_probes/R2_split_macro_capture/verification.json)。

**限制：** 本轮没有调用编译器，不测定该文本对应的真实最终宏值，不声称编译出过错误二进制。测试里的编译器/库/程序为原测试提供的惰性占位字节；CONFIRMED和授权标记是人工数据，不是作者确认或执行许可。结论仅为合同承诺的宏唯一性检查存在解析遗漏。

**最小行动：** 统一识别-D/-U合并及分离形式，保留原始命令，再按原政策要求恰好一次明确0；重复、冲突、undef拒绝。不改变物理门槛，也不通过删掉命令中的不利部分使其“看起来唯一”。本轮不修源码，R2保留为S0绑定前缺口。

两项定位、严重度、复现范围和行动见[findings.json](findings.json)。R1为HIGH、R2为MEDIUM。F04多合同汇总仍是既有后续事项，没有本轮新增修改或授权。

## 外部历史与S0状态

本轮在原v1.1 common、原审查的历史记录及最新项目状态中没有找到新的真实作者确认；最后明确答复仍是“尚不能确认，需要核查”。已单独向用户询问是否有新结论，并要求如有结论提供已核查的位置或来源。最终状态以本报告目录的history_status.json记录为准；未答复或仍未查清，均不能转为CONFIRMED。只查本地状态不能证明其他电脑、未归档材料或他人数据不存在。

S0 h75是已知回归控制，不是两个新候选的预测成绩。原两条草案保持，不重建编号/目录、不填正式程序或最终配置SHA。即使以后外部历史获确认，仍须解决R1/R2并通过相应核对，再准备真实正式构建、逐条绑定和独立退出/资源/产物捕获，不能自动放行。

本轮native编译0、求解0、实际VTK数据读取0；现有测试中独立reader仅导入并拒绝非法输出，不读取场。没有修改v1.1、原准备包、原协议、测试、旧结果或冻结门槛，没有提交推送或对外发送项目材料。所有新增产物限本报告、人工反例与共享状态/交接维护。

当前新正式NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null；reference_qualified=false、strict_error_bound_established=false、submission_ready=false；实际正式run_id为空，S0保持未启动。软件复核有新增证据，不将其称为新增流场/物理验证。旧FAIL、C/h75限定资格、V2/G4锁和D4预测HOLD保持。

## 接续范围

只读复核任务已完成。后续可另行授权隔离小版本仅收口R1/R2，新增对应反例，保留v1.1封存；作者继续核实外部历史。两项均满足后才进入S0正式执行绑定准备，继续不自动启动。F04后续汇总前单独处理。

技能方法归属沿用同日已核条目：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://arxiv.org/abs/2609.00065)，DOI [10.48550/arXiv.2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。仅说明AI流程来源，不作本项目数值/物理证据；本轮没有新增文献检索。
