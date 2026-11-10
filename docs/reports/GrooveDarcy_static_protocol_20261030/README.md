# grooveDarcy 定间隙接入协议与后续挤压接口

**已准备GDI-v1：首例对应已有C01，用实际porosityForce动量源求压力与平均速度，再对照旧二维/OF静态结果。新流场未启动，宿主求解器和正式单例包尚未实现。** 本轮用户仅授权协议、对照材料与接口明确，不包含编译新宿主或启动仿真。

阅读顺序：

1. [PROTOCOL.md](PROTOCOL.md)：方程、全512单元阻力区、初值/边界、耦合算法、原门槛与新增动量守卫。
2. [EXPECTED_VALUES.md](EXPECTED_VALUES.md)：四个旧例实际CSV与新接入解析预期，明确没有新结果。
3. [SQUEEZE_INTERFACE.md](SQUEEZE_INTERFACE.md)：间隙字段、储液体积、连续性、通量、正闭合符号和力定义。
4. [protocol.json](protocol.json)、[reference_values.json](reference_values.json)、[input_bindings.json](input_bindings.json)：机器可读输入和已有证据哈希。
5. [offline_audit.json](offline_audit.json)、[verification.json](verification.json)：纯读取/算术与文件保护核对。

首例GDI01保持h=75nm、H=125nm、24/0Pa、24×48µm、16×32×1；预期平均Ux≈3.64303614e-7m/s、Q≈2.18582168e-18m³/s。新链的区别是通过grooveDarcy从几何现场生成阻力，并进入动量—压力迭代；不绕过子类直接重用旧D压力求解器。

关键准备发现：旧装配测试只覆盖半区，正式对照需全域512单元；迹分裂各向异性需要外迭代与未分裂动量残差，单次压力收敛不够；更新间隙阻力仍须独立实现∂tH+div(HU)=0及H/b0面通量转换。

本轮仅新建本目录和维护项目状态/交接；旧子类、库、原SDI协议、C01–C04输出不修改。本目录prepare_offline.py只读取已有文件并生成协议/参考表，不调用OpenFOAM、编译器、求解器或旧检查器；没有新的run_id、流场结果、物理验证或启动命令。当前subclass已有编译/装配证据不等于host已实现；各阶段见protocol.json。

下一具体动作是按GDI-v1实现最小宿主、外部验收适配器及全域GDI01包，然后编译与不求解审计；后续正式运行另行授权。其他映射、SDI控制项、挤压实现和独立参考范围均不自动启动。reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD与历史FAIL保持。

本报告由AI按scientific-writing技能辅助组织，未作独立人工科学签字。流程来源已核为v2（2026-10-30访问），引为：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。仅为证据组织流程来源，不作流动物理依据。

技术依据：本机Foundation13 [porosityForce源项符号](https://cpp.openfoam.org/v13/porosityForce_8C_source.html)、[fvMatrix](https://cpp.openfoam.org/v13/fvMatrix_8C_source.html)及incompressibleFluid/correctPressure.C；宿主采用这里审核的受限方程，不声称通用incompressibleFluid模块本身已经用于本例。旧物理定义见[导度—阻力说明](../Shared_transport_interface_20261030/CONDUCTANCE_RESISTANCE_INTERFACE.md)，子类完成状态见[实现报告](../Groove_porosity_model_20261030/REPORT.md)。
