# SDI-v1双程序实现与C01运行包

日期：2026-10-30。当前状态：**源码与编译完成，平均域网格及静态审计完成，C01尚未求解。** 用户授权本轮实现、编译、静态核对和准备首例运行包，没有要求本轮启动流动计算。

## 阅读入口与具体改动

运行包入口：[CASE/interface_static_darcy_v1/README.md](../../../CASE/interface_static_darcy_v1/README.md)。本轮只新增该独立CASE目录和本报告目录，并同步项目状态/交接。既有D2/D3、nanrPrint、原始结果、SDI-v1协议和此前输入包均未修改。

|材料|作用|实际完成范围|
|---|---|---|
|two_dimensional/darcy2d.cpp|独立二维有限体积程序，读取K|C++17编译通过；零初值，CG/对角预条件，不调用解析答案|
|openfoam/application/depthAveragedDarcyFoam.C|平均Darcy压力程序，读取D|Foundation13编译通过；PCG/DIC，物理压力Pa，面内逆矩阵，z为空方向|
|analysis/check_results.py|读取已完成原始结果并评价|语法及11项人造数据功能测试通过；尚无真实求解结果可验收|
|common及openfoam/cases/C01|C01输入、边界、网格、协议副本|绑定原/V2输入来源，仅生成C01；没有批量运行入口|
|scripts/run_c01.py|默认只预检查，显式执行才运行两端|只读预检查通过；执行路径未启动；任一失败停止，不重跑|
|common/release_manifest.json|源码、二进制、输入、静态证据与运行库绑定|50个文件、21个运行库；临时副本改输入被成功拒绝|

二维使用C++而非Python科学计算包，无需安装SciPy。两端只共享输入/输出约定，分别装配和求解压力系统。二维的输出是体积流量形式的J通量；OpenFOAM先由总D计算U再以H U还原J，H=125nm。两端均不从解析压力初始化。

原协议副本保留制定时“尚未实现”等状态文字以维持哈希；那是协议制定时的快照，当前实现状态以本报告、运行包README和preparation.json为准。协议阈值未作改动，也未因编译或网格检查把未来结果填为通过。

## 验证证据与明确限制

实际命令与退出码见CASE内reports/preparation.json，包含两个编译、checkMesh和两端audit-only入口。本轮另生成一次blockMesh网格。网格为512单元、2个求解方向，体积约1.44×10⁻¹⁶m³，最大非正交角0，checkMesh显示Mesh OK。OpenFOAM静态入口装配了压力矩阵，确认对称、对角项为正、矩阵维度为体积流量，并在调用solve之前返回；未执行压力迭代。

矩阵最小对角项约1.95216044×10⁻¹⁹（对应集成通量/压力系数）；这是装配检查值，不是物理验证结果。二维审计只读输入与计数/体积，不执行CG。两端可执行文件和源码哈希已与实际编译记录绑定。

编译过程保留了一次新增审计输出的API错误：`Info.precision`不是Foundation13的messageStream成员；已改用标准输出打印审计JSON后重新编译通过。失败日志位于CASE内reports/preparation_attempts/001_initial_failure。初始一次未封装的编译和后续完成静态审计的记录，与最终编译绑定分别说明，不把旧二进制存在当最终编译证据。

检查器11项测试使用内存中的合成数据，覆盖理想数据接受、压力反号、局部/全域不守恒、125/175nm比例误用、丢面、交换导度、未收敛、法向错误、非有限CSV、缺完成证据和零驱动绝对门槛。测试日志和清单见CASE内reports/checker_synthetic_tests.*。没有因此声称C01流动通过。

运行包的实际动态库加载另在精简环境、2GiB地址空间上限下审计，见本目录runtime_environment_audit.json/log。没有依赖用户终端已加载完整OpenFOAM配置才能找到库的未核假设；但本包仍绑定当前机器，换机/升级需重建。

预检查完整性反例见preflight_negative_control.json：复制已封装文件到临时目录，在副本输入中增加换行后被哈希检查拒绝；原包未改，无流动求解。C01启动脚本默认模式的预检查已通过，且runs目录、SDI_output和时间1场均未创建。

尚未核实：实际PCG/CG迭代收敛、运行后的压力/速度/流量、原生场写出、质量/能量门槛和两端一致性。编译和矩阵装配不能代替这些证据。此最小恒系数算例也不验证复杂压力、网格独立性、真实沟槽、三维局部应力、挤压、两相或内置DarcyForchheimer加载。

## 首例交付与停点

首例C01：V2、槽沿y、x驱动；24×48μm、125nm平均厚度，x两端过压24Pa/0Pa，另外两边不穿流。预期值保持原协议，未来分别对解析答案和两端差异验收。其他8项预定诊断未生成运行包或启动。

预留名称 `SDI_C01_v1_20261030_01` 仅是planned_run_id；actual_run_id=null。启动方式见运行包README：同一台Linux机器普通终端执行一条tmux命令，由用户启动两端C01；每端300s/2GiB/单进程上限，失败即停，不自动分析、重试或推进下一例。输入、程序、源码副本、原始CSV和原生OpenFOAM场、日志、两个独立退出码将在该次运行目录保留。

当前C01：source_prepared=true、compile_checked=true、mesh_checked=true、matrix_assembly_audit=true、run_completed=false、NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=null、geometry_PASS=true（仅合成平均域）。独立人工验收尚无。历史D4_N8_diag_v3_1_20261026_v1保持NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null；reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD与历史FAIL保持。

下一具体动作：用户启动C01；结束后发起结果分析，只读已有目录并运行检查器。尚未交付或授权任何下一例、拟合、显式沟槽参考、挤压运行、提交推送或对外发送。下一步建议GPT-6.1 Sol｜High；理论矛盾或最终物理裁决按项目协议建议GPT-6 Astra｜High。

流程采用已读scientific-writing技能的来源绑定和状态分离；流程文献已列于[协议入口](../Static_Darcy_interface_protocol_20261030/README.md)，不作为本程序的物理验证依据。该报告由AI辅助生成，未声称独立人工审核通过。
