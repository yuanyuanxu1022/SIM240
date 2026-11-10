# SDI-v1 C03：原公式横槽对照准备包

日期：2026-10-30。**输入、程序来源绑定和静态核对已完成；按用户要求保持未启动。** 没有 C03 流动计算结果，actual_run_id=null。

阅读入口：[C03规格与共同输入表](common/C03_SPEC.md)、[输入JSON](common/C03.json)、[解析预期](common/C03_expected.json)、[静态核对证据](reports/preparation.json)、[检查器版本说明](common/CHECKER_CHANGELOG.md)。完整准备报告见[REPORT.md](../../docs/reports/SDI_C03_preparation_20261030/REPORT.md)。

C03与已完成的C01都是沿x驱动、沟槽沿y的横槽平均问题。唯一物理输入变化是将V2的K/D替换为原局部立方律的K/D；C02是V2沿槽方向，作为已有检查器回归数据使用，不作为C03同方向公式对照。这里的C03是SDI-v1内部编号，与旧路线表的Case03不是同一个任务。

两个求解程序、Make配置和二进制均与原C01逐文件SHA256一致，复用其真实编译证据，本轮未重新编译。网格逐文件复用，并在C03路径实际运行checkMesh；二维audit-only和OpenFOAM auditOnly均实际执行，后者仅装配矩阵后退出，未求解压力。平均层厚度仍为125nm，U=J/H，D=H K⁻¹，阻力已包含壁面作用。

检查器1.2.0只增加C03输入身份支持及版本标记，所有指标计算与1.1.0一致，保留已有几何识别修正。15项人造数据测试通过；读取C01和C02已有结果，各50项数值检查与旧判定逐项一致。它们不构成C03运行证据。

当前状态：source_prepared=true、compile_identity_verified=true（复用编译）、mesh_checked=true、matrix_assembly_audit=true；run_completed=false、NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=null、geometry_PASS=true（仅合成平均域），physical_validation=NOT_EVALUATED、independent_human_acceptance=false。

`scripts/run_c03.py`默认只读核查封装，准备过程只调用默认模式。发布清单中的launch_ready=true只表示技术材料齐备；flow_run_authorized_by_preparation=false。预留编号SDI_C03_v1_2_20261030_01，实际编号为空，未创建runs目录、时间1流场或SDI_output。没有启动C03或下一例的授权，也不在此交付启动命令。

原[SDI-v1协议](common/PROTOCOL.md)保留制定时的状态文字及原始门槛；本README与准备报告描述当前状态。流程沿用scientific-writing的证据组织，技能出处见[原协议入口](../../docs/reports/Static_Darcy_interface_protocol_20261030/README.md)。后续仅在用户明确授权启动C03并完成后，读取原始输出按相同门槛分析，不自动重跑或推进下一项。
