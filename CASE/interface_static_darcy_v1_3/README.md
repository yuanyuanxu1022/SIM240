# SDI-v1 C04：原公式沿槽对照包

日期2026-10-30。**输入、程序来源和静态核对已完成，C04流动计算尚未启动。** 该独立目录为interface_static_darcy_v1_3，启动脚本为scripts/run_c04.py；不使用C03的目录、脚本或运行编号。

阅读：[共同输入与C04规格](common/C04_SPEC.md)、[C04输入](common/C04.json)、[解析预期](common/C04_expected.json)、[静态核对证据](reports/preparation.json)、[检查器版本说明](common/CHECKER_CHANGELOG.md)、[完整准备报告](../../docs/reports/SDI_C04_preparation_20261030/REPORT.md)。

C04是SDI-v1中的“原局部立方律、沟槽沿x、驱动沿x”，检验沿槽系数。C02是V2沿槽，作为同方向公式对照；C03是原公式横槽，作为原公式槽向交换对照。编号不等于旧路线表的Case04结构参数扫描。

保持24/0Pa边界、24×48μm区域、H=125nm、μ=0.001Pa·s、16×32×1网格；U为液体体积平均速度，J=HU，D=H K⁻¹。K/D已包含总壁面阻力，不再解析厚度剪切，不加载另一份Darcy源。原SDI-v1全部thresholds及linear_solver保持不变。

两份C++、Make配置和二进制与C01逐文件SHA256相同，复用真实编译证据，本轮没有重新编译。网格复制后在C04路径实际checkMesh；二维audit-only、OF auditOnly实际执行，后者仅装配矩阵后退出，初始压力仍为0，无压力迭代。

检查器1.3.0支持已完成C01—C04的既定非零x主轴驱动问题，只修改版本/说明和支持列表，所有函数AST与1.2.0相同。15项人造数据测试通过；只读C01/C02/C03已有结果，各50项数值检查、指标、Gate和原始文件哈希均与旧分析一致。它们不代表C04计算通过。

当前source_prepared=true、compile_identity_verified=true（复用编译）、mesh_checked=true、matrix_assembly_audit=true；run_completed=false、NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=null、geometry_PASS=true（仅准备阶段合成平均域），physical_validation=NOT_EVALUATED。没有C04独立人工科学验收。

planned_run_id=SDI_C04_v1_3_20261030_01，actual_run_id=null。scripts/run_c04.py默认只读核查封装；只有显式执行参数才启动该例两端。run_id必须属于C04/v1_3且不能覆盖已存在目录，失败/超时停止，无重试、无下一例、无自动验收。每端串行、300秒/2GiB预算和2000次迭代上限不变。

用户本轮授权准备完成后交付单条tmux命令，实际启动由用户执行。命令及状态核对回执在准备报告目录launch_command.json。技术launch_ready不代表已经运行，封装本身不授予AI启动权限。C04完成后另读原始结果按SDI-v1评价，先对照C02，再作与C03的方向对照；比值仅描述，不新增Gate。共享闭合的一致性仍不证明真实流动准确性。

原[协议副本](common/PROTOCOL.md)保留制定时的状态文字；本入口和preparation.json反映当前准备范围。报告证据组织沿用scientific-writing，出处及既有引用见[原协议入口](../../docs/reports/Static_Darcy_interface_protocol_20261030/README.md)。
