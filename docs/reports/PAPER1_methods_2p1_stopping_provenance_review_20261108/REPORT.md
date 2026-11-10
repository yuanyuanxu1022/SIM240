# §2.1停止条件、保存PASS与历史可追溯性审读

日期：2026-11-08，Asia/Shanghai。作者授权的逐部分审读；不合入正式稿，不重跑接受器或求解器，不改冻结阈值。

## 裁定

现稿已有“停止条件而非独立验收”的正确限定，数字也与当前D2逻辑相符，不应把现稿描述成已将两者混同。建议补明最近1000条滑动窗口、三项同时达标、面内正交通量的窗口绝对峰值，并明确程序内PASS是比停止状态更宽的一组内部检查。来源说明保留，并加入新增表S6入口，避免旧52清单被误读为已含新增四例。

## 三类状态

|层次|代表什么|边界|
|---|---|---|
|converged|最近1000条主通量窗口首次同时满足三项停止量|不是整个场的空间误差界或物理验证；到最大步数也会结束循环，不能把正常结束一律叫收敛|
|原生result中的PASS|内部检查的合取：体积/边界/材料、末态有限性、converged、全程保存的质量/密度/Mach极值、窗口正交通量、末态截面差及正主通量|不是另一个独立检查器的结论；也不是正式NUMERICAL_GATE/RESULT_PASS/geometry_PASS的统一放行|
|独立复核/验收|对已保存原始记录按明确口径重算，记录检查对象、规则、报告与结论|通过限定原始资料核对不自动得到连续参考资格、阶段接受或物理保真度；各项状态分开报告|

独立退出文件是执行状态证据，与result自写的exit_code字段分开，不是单凭退出0认定精度。原生预检查geometry_PASS、q_audit_PASS和converter_PASS亦为程序保存字段，不能不加说明地当成本轮重新完成的独立几何审查。

## 停止量精确定义

当前D2的FluxWindow保留最近1000条数据，每个步号记录一次，包括初始步。s采用样本标准差（分母N−1），相对量为s/|mean(J_main)|与(max−min)/|mean(J_main)|，阈值10⁻⁶和5×10⁻⁶。第三项为同窗口max|J_orthogonal|≤10⁻¹²m²/s。

“连续1000步”不是要求1000个相邻窗口全部合格；是一个窗口包含1000条连续样本，第一次合格便停止。J_orthogonal是对驱动正交的面内积分通量，不等于每个节点的横向速度，也不是始终指x分量；T横槽驱动时正交量对应y。D3斜向存在物理交叉通量，不把D2主轴绝对阈值套到其上。

当前maximumSteps=60000；达上限而未满足窗口条件时不会标converged=true。PASS还要求maxMassError<10⁻¹⁰、maxDensityDeviation≤10⁻⁶、maxMach<.05、末态两截面相对差≤10⁻⁵等，不改成另一套项目统一门槛。本轮核代码与保存状态，不重新重算所有诊断极值。保持阈值无量纲/有量纲的区别，不能把10⁻⁶的相对时间波动称作百万分之一导度精度。

当前§3.1已有“首次达标即停”及余量讨论，方向正确。其中“全部满足在构造上必然成立”应限定到按达标规则收敛退出的记录，不能泛指所有启动过的计算；程序有最大步数路径。候选不将余量小视为不可信，也不将其视为空间误差小。

## 保存证据的具体例子

本轮实际读取历史h75/d100、dx1.25nm横槽原result与独立exit_code.txt：converged=true，但PASS=false、退出3。保存最大质量相对变化1.1967043900362632×10⁻¹⁰超10⁻¹⁰；末窗标准差9.9995236164813166×10⁻⁷、极差3.4611808676254171×10⁻⁶。它说明时间通量停止和内部其他检查可产生不同结果。该历史质量失败不同于h30/d80的S4网格阶段失败。

S4六个单例检查通过但横槽中细变化1.328387035%>1%，阶段仍FAIL；本轮沿用已审控制报告及补充表S8，不重验这些轨迹。新增四例的既有独立核对报告明确通过的是保存资料/诊断复算范围，正式Gate与连续参考资格未重新签发，不能把其“通过限定核查”改成全图参考合格。

## 追溯性重核

本轮读取表S1全部52个manifest/result及其独立exit_code.txt：52保存PASS/converged为true、52外部退出0、52个manifest二进制SHA均与表S1相符。4组SHA条数22/22/6/2；日志索引48独立、4共用批次。只核保存记录及索引，不称本轮读取了全部日志/诊断或重新验收52算例。

52份manifest均无source_sha256、generated_source_sha256、openlb_commit、compiler、compile_flags字段。说明清单本身没有完整绑定，不等同工程别处永久没有档案。历史构建裁决与当前补充S10仍确认四组完整绑定未闭合；h75单几何复现不关闭全图来源问题。

当前D2 src/Makefile固定注入OLB_VERSION=5953d8a-dirty；因此日志同一字符串不能独立证明实际依赖commit，当前源树版本或文件时间也不能回填历史字段。原尝试case根目录Makefile不存在，实际读取src/Makefile，不把路径不同当源码缺失。

## 中文替换候选

停止条件基于最近1000条连续通量样本。主通量的样本标准差与极差分别除以窗口均值的绝对值，要求不超过10⁻⁶和5×10⁻⁶；主轴驱动工况还要求该窗口内、与驱动方向正交的面内通量绝对最大值不超过10⁻¹² m²/s。窗口首次同时满足上述条件时结束迭代并记录converged=true。程序内PASS另汇总有限性、质量、密度、Mach数、边界及截面通量等检查。停止状态、程序内PASS与独立复核结果分别报告，数值参考的可靠性及限制见第3章。

原D2/D3运行的参数、结果、日志、二进制哈希和独立退出记录按补充表S1定位，新增间隙与构建对照记录见补充表S6。已保存的二进制哈希用于区分程序身份；部分历史运行的应用源码、OpenLB依赖内容及实际编译配置仍未完整绑定，不能据现存源码或版本标签认定历史构建环境已完整复现，详见补充S10。

## 英文对应候选

Stopping is based on the latest 1000 consecutive flux samples. The sample standard deviation and range of the main flux, each normalized by the absolute window mean, must not exceed 10⁻⁶ and 5×10⁻⁶, respectively. For principal-axis forcing, the maximum absolute in-plane flux orthogonal to the driving direction within the same window must also not exceed 10⁻¹² m²/s. Iteration stops at the first window satisfying all these conditions, with converged=true recorded. The program-internal PASS flag additionally combines finiteness, mass, density, Mach-number, boundary and section-flux checks. Stopping status, program-internal PASS and independent review outcomes are reported separately; reference reliability and limitations are assessed in Section 3.

Parameters, results, logs, binary hashes and separately recorded exit codes for the original D2/D3 runs are indexed in Supplementary Table S1. Added-gap and build-comparison records are indexed in Supplementary Table S6. Saved binary hashes distinguish program identities. Binding to application source, OpenLB dependency contents and the effective compilation configuration remains incomplete for some historical runs. Existing source files or version labels therefore do not establish complete reconstruction of the historical build environment; see Supplementary S10.

只替换原长段中的停止和来源子段；前轮几何、驱动与速度提取候选独立衔接。正式采用时可分两段，使停止方法与记录来源清楚分开。符号按现稿数学排版，不新增编号式或参考文献。

## 实际范围与停点

本轮读当前中英文§2.1及中文§3.1、补充S4/S10与表S1/S4/S8、当前D2窗口/循环/PASS逻辑及Makefile、既有统计与构建裁决/新增验收。未导入求解器，不重新复算52条完整diagnostics，未读取保留流动结果。保存状态不作新增科学接受，原生与独立状态按报告对象限定。

输入身份/保持见source_manifest.json及verification.json；52条状态/来源与历史失败例见saved_provenance_and_status.json。使用已读scientific-writing及academic-humanizer，流程来源沿用§1.2第一段报告所列Kassis等Scientific Agent Skills（2026，arXiv:2609.00065），不另加科学引文，无联网检索。

正式稿/原记录/源码/系数/阈值未改，先前摘要合入保持，引言与§2.1候选未合入。本轮只本目录及共享状态更新；无编译/求解/拟合/场处理/新接受/Gate/run_id/上传，无新长算授权。S4原FAIL、reference_qualified=false、strict_error_bound_established=false、submission_ready=false保持。

下一具体动作：审§2.1单胞周期假设及其边界，随后逐段审物性、松弛参数与时间步换算；若用户要求采用，则按子段范围同步中英文，不覆盖已保留条件。
