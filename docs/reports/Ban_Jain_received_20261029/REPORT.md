# 微信目录两份原文接收与闭环线索核对（2026-10-29）

## 范围与文件身份

用户提供目录 `/home/dell/文档/xwechat_files/wxid_w4wzxvlq903i22_5b59/msg/file/2026-10` 及两个文件名。本轮核实际PDF，不根据“TAN木”发音强行匹配。原件和工作副本逐项SHA256/字节数见 intake.json。

| 文件 | 已核身份 | 页数与证据 |
|---|---|---|
| BAN-DISSERTATION-2021.pdf | Yang Hun Ban, *Fluid Dynamics of Thin Films in Semiconductor Manufacturing Processes*, University of Texas at Austin, PhD, August 2021; supervisor Roger T. Bonnecaze | 154页；PDF第2—3页、摘要与目录。与下载目录既有Ban博士论文逐字节相同 |
| 011602_1_online.pdf | Akhilesh Jain, Andrew Spann, Roger T. Bonnecaze, *Effect of droplet size, droplet placement, and gas dissolution on throughput and defect rate in UV nanoimprint lithography*, JVST B **35**, 011602 (2017), DOI 10.1116/1.4971771 | 13页含AIP封面；PDF第1—2页。在线2016-12-15；下载水印2025不作发表年份 |

两份署名单位均为UT Austin，不能称为佳能公司署名论文；也没有Tan或Taylor署名。老师“TAN木”的原意仍未被文件本身唯一确定。

## 针对闭环的阅读记录

1. Ban目录：第2章“Optimal placement of droplets for UV nanoimprint lithography”（正文p.26起），模拟方法§2.2 p.29起；第3章“Minimizing Filling Time ... Templates with Multiple Structures”（p.60起），§3.2方法p.63起，§3.3.3方向p.78、§3.3.4尺寸p.80。适合后续精读局部结构如何接入整体流动/填充模型。本轮没有对154页逐页科学终审，目录中的毛细各向异性不能当成本项目水力迁移率各向异性的验证。
2. Jain正文011602-3（PDF4）式(1)(2)给出润滑压力方程及高度平均速度，输运系数含H³/(12μ)；式(3)(4)处理毛细边界。正文011602-4（PDF5）方法段明确：猜模板速度→求压力→积分压力得到力→调速度满足力平衡→重求压力/通量→VOF推进界面并降低模板→重构界面，直到达到目标间隙且全域填充。该流程解释“公式—过程计算—填充指标”的连接。
3. 同一方法页写与Reddy与Bonnecaze文献[22]的结果对比。引言011602-2将[22]描述为基于润滑理论的动态多滴模拟；参考文献表[22]为MEE82,60(2005)。因此这里只确认“与既有模拟结果比较”的文献陈述，不把它说成该文完成新实验闭环、独立显式沟槽检验或本项目公式已验证。64×64典型单滴网格和小于1%体积变化是作者报告的数值设置/守恒控制，不能替代压力/填充时间的全范围误差界。
4. Jain正文011602-12参考文献[39]包含X.G.Liang、H.Tan、Z.L.Fu、S.Y.Chou，Nanotechnology18,025303（列2006）。与此前候选DOI 10.1088/0957-4484/18/2/025303的在线2006/卷期2007线索相符；只能作为Tan名字线索，不能据此确认老师指该文。
5. 重要区分：本次JVST Jain2017不是现正文参考文献[1]的 *Fluid flow in UV nanoimprint lithography with patterned templates*, MEE173,62–70 (2017), DOI 10.1016/j.mee.2017.04.001。两篇作者名单、题目与DOI不同；不能用同一个“Jain2017”混称或互换公式出处。

视觉核对：已渲染并查看Ban PDF3标题页、Jain PDF2标题/摘要页及PDF5方法页；页图在 tmp/pdfs/ban_jain_received_20261029/。文本阅读限身份/目录、Jain引言相关段、方法011602-3—4、结尾/参考文献，不声明整篇结果图或全博士论文验收。

## 对第一篇目标的影响

这些原文提供实现路线，不能直接证明本项目V2修正有效。建议保持既有目标：先在全充液、给定瞬时间隙与闭合速度的长方形区域预测压力与挤压阻力R_sq=F_net/V，再与不使用V2的、同条件且合格的独立显式沟槽参照比较。局部K到宏观方程的平均定义、单位、边界、力定义和尺度分离需先审；不能只替换一个系数便宣称动态填充时间已验证。完整多滴填充还需要界面、毛细边界、压头运动和可能的气体模型，属于另行定义的范围。

本轮仅原文身份/方法证据核对及资料维护；无新增计算或数值/物理验证，无编译/求解/拟合/新run_id/下一Gate/提交推送。旧D4_N8_diag_v3_1_20261026_v1及NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD和历史FAIL保持。

下一具体资料动作：对Ban§3.2与现有第一篇K接口逐式建立来源/单位/平均定义对应表，再完善瞬时挤压问题的边界、力定义、独立参照与资源清单；不自动实现或启动长计算。
