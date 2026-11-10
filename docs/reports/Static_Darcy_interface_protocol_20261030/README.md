# 静态导度—阻力接口：审核与实施协议

日期：2026-10-30。版本：SDI-v1。状态：**设计已明确，尚未实现、编译或运行**。

用户授权范围：审核平均速度与壁面阻力，确定接口方式，制定最小静态压力驱动算例协议。本目录是 AI 辅助的方法审核与实现规格，不是独立人工验收或科学 Gate 放行。

按以下顺序读：

1. [审核结论与推导](INTERFACE_REVIEW.md)：为什么采用平均速度、为什么不能再叠加完整壁面阻力。
2. [最小算例实施协议](PROTOCOL.md)：方程、边界、具体尺寸、检查指标、停止条件和实施步骤。
3. [解析预期值](EXPECTED_VALUES.md)：未来计算应对照的数值；这些不是求解器结果。
4. `protocol.json`：机器可读设计；`analytic_checks.py` / `analytic_checks.json`：纯代数与解析积分复核。

**采用方式：恒定储液厚度下的总 Darcy 阻力平均模型。** 二维端读取 K；OpenFOAM 端读取 D=H K⁻¹，求解压力方程并重建平均速度。OpenFOAM 首阶段拟新建一个独立的小型有限体积应用，不直接使用 nanrPrint 的两相求解入口，也不宣称本轮验证了内置 DarcyForchheimer 的接入。

此前材料见 [共用输入表](../Shared_transport_interface_20261030/COMMON_INPUTS.md)。旧包作为准备快照保留；本协议只具体化静态接口检查，不填定未来挤压算例的尺寸、速度或体积变化方式。旧包中 Dzz 未定的问题在本协议内通过二维约束解决，不据此定义三维竖向阻力。

本轮已完成源码定义检查、接口推导、解析反例与输入算术检查。未新增流动计算、网格、短测、拟合、新仿真 run_id 或长算授权。`NUMERICAL_GATE=NOT_EVALUATED`，`RESULT_PASS=null`，`geometry_PASS=null`；原项目历史 FAIL、参考资格、严格误差界与投稿状态保持。

下一动作：按照本协议实现独立的二维压力程序、OpenFOAM 平均 Darcy 应用及结果读取器，进行源码/字典/编译检查；在完成实现与运行前检查后再准备单例启动材料。本轮不提供运行命令。

流程说明：使用 scientific-writing 的证据组织和 peer-review 的方法审查结构。本任务是用户授权的自有研究协议审核，无期刊委托或编辑通道；范围、授权、局限见 `review_scope.json`，没有虚构期刊许可或人工签字。Skill 的期刊审稿 intake CLI 不适用于本次自有协议的托管 AI 审核，未宣称其通过。未把项目内容提交给搜索或其他第三方服务；网页查询仅为公开官方文档。

流程文献已核：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。2026-10-30 查阅为 v2；仅作流程来源，不作流动物理依据。
