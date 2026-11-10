# 二维模型与 OpenFOAM 共用输入及导度—阻力接口

日期：2026-10-30。**准备完成；尚未冻结、未接入求解器、未运行。**

本轮按用户要求交付输入表和接口说明。研究问题保持全充液、单相、刚性图案区的瞬时压力与挤压阻力；已有固定壁面局部导度只是候选输入，不自动证明挤压应用有效。

阅读顺序：

1. [共用输入表](COMMON_INPUTS.md)：先看哪些已有依据，哪些只是候选，哪些尚未定。
2. [导度—阻力接口说明](CONDUCTANCE_RESISTANCE_INTERFACE.md)：看单位、平均厚度、方向、驱动和壁面阻力怎样保持一致。
3. [基准系数换算示例](COEFFICIENT_EXAMPLES.md)：已复算原公式、公布 V2 及两条既有 OpenLB 输入的条件性数值。

供后续程序读取的材料：`common_inputs.json`、`coefficient_examples.json`。其中 `launch_ready=false`，待定量用 `null`，没有用零值替代未知物性、尺寸或驱动。它们不是可直接运行的 OpenFOAM 字典。输出指标中的主量最终须统一压力载荷与总应力口径。

复算与来源：`prepare_inputs.py` 仅使用 Python 标准库，读取原始文件，复算系数并写入本目录；不导入旧 D3 脚本，不编译或启动任何流动程序。`source_manifest.json` 记录来源哈希，`verification.json` 记录输入/算术检查。检查满足只说明这份准备材料内部一致，不能用于宣布任何流动 Gate 通过。

已完成：现行 K/J 定义与公布 V2 核对、两个既有 5 nm result.txt 的数值读取、候选几何三种高度、两槽向矩阵映射、K→κ→D 的有条件换算、符号/力/守恒输出口径及后续检查清单。

尚缺：绝对区域长宽与周期数、驱动大小、物性采用、OpenFOAM 总阻力或解析壁面路线、运动/体积源实现、边界/载荷对应、网格/资源、冻结门槛、同条件合格显式参考与新条件设计。**这份输入表不是正式放行协议。**

此次只有输入与算术复核，没有新流动结果、编译、网格生成、短测、仿真、拟合、Gate 推进或新仿真 run_id。原 D4 诊断、历史 FAIL、第一篇参考未合格和投稿未就绪状态保持。没有新增长算启动授权或提交推送。

下一具体动作：对“125 nm 平均厚度对应的速度定义”和“总阻力/解析壁面二选一路线”做科学审核，再形成静态压力驱动接口算例的实施协议；正式公式与结论冻结建议 GPT-6 Astra｜High。准备材料本身可由 GPT-6.1 Sol｜High 完成，不声称切换实际模型。

流程来源：本材料使用 scientific-writing Skill 的证据定位与状态分离流程，并已注明来源：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。2026-10-30 核摘要页显示当前 v2；该流程文献不是 CFD 验证依据，也未加入正式论文参考文献。
