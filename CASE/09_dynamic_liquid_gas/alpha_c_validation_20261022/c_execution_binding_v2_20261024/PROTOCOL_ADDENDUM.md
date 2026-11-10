# C 执行来源兼容附录 v2

2026-10-24。执行ID C_BINDING_COMPAT_20261024_v2；父物理协议 ALPHA_C_DIAGNOSTICS_20261022_v1；新批次 alpha_c_20261024_binding_v2_c。仅改变执行/验收来源绑定，科学公式和结论没有新冻结或新放行。

## 授权与不变量

用户授权“按独立设计处理C执行与验收绑定，保持物理输入和判据不变，不启动计算”。本次允许编写独立Python层、冻结其输入、静态/来源/合成fixture检查；不调用OpenLB，包括零步模式，不启动正式C。后续启动仍须用户明确指令。

物理合同从原protocol.json逐字段继承，包含四组cases及原backend/material/thresholds/c_output，副本physical_contract.json逐字段核对。C++源码、二进制、OpenLB后端、初态、tau/alpha、64³/64步及输出字节均沿用原哈希。未改C++，不重新编译。新binding.py的摘要汇总逻辑与原analyze_completed的C分支相同，不更改analyze_c.py数值公式。

Q/质量全程最大相对漂移各≤1e-9；实现局部/每节点残差≤1e-12；安全条件按原协议。人工mu0不当本构平衡；等密度保持运动黏度不保持动力黏度。旧首步预测−2.36935425e-9/+8.29233009e-9以及目标质量−8.27245235e-9保留，C用于收支诊断，不承诺物理守恒通过。NUMERICAL_GATE、RESULT_PASS、geometry_PASS保持NOT_EVALUATED。

## 精确兼容与历史依赖

旧build_binding.json SHA固定a3409a57…，不改其字节。旧AGENTS哈希5700b378…保留为历史字段；当前仅允许已审查的59d1cc51…，精确diff及旧文本重建与当前字节相互核对。其余3400项逐项原哈希，禁止忽略文档或任意新AGENTS变更。

alpha依赖保留原batch/manifest、canonical verdict SHA018467d3…、EXPORT_PROVENANCE SHAd1a07013…、全部391项原始输入及批次独立exit。原JSON输出失败exit2、仅布尔输出适配后exit0的事实不改写；独立复核JSON与其已记录SHA一致。父绑定保留当时AGENTS，不谎称其现在匹配。

execution_binding.json记录新的文件映射（只替换管理文件这一项的当前期望值、加入历史依赖及本执行层），并保存父绑定SHA、兼容声明及alpha依赖。运行端和验收端调用同一个verify_binding；完整核对所需路径集合，不能删除关键绑定项。新binding自身SHA写入运行manifest并在完成验收时核对，执行前后还核全部输入。

## 执行及完成验收

run_c.py 默认只预查，不创建正式目录、不锁定执行、不调用程序；显式--run才可能执行。执行拿单批次锁后复查，拒绝新旧C既有批次；四组顺序固定，逐项检查绑定、记录原程序绝对命令/cwd/参数/日志/独立退出，非零即停，原始失败保留。无自动重跑/恢复/后处理/下一Gate。至少预留12GiB磁盘，真实耗时/峰值RSS仍未知。

新C输出位于本目录output/<batch>/<run_id>，证据位于evidence/<batch>/<run_id>。manifest保存新增绑定全文及SHA、父物理协议及alpha历史依赖，形式Gate保持原值。

analyze_completed_c.py先核相同绑定与来源。--check-inputs只报告来源准备通过，不接受结果。完成验收必须四组独立exit0、批次/子manifest相符、固定命令/参数/步数完整、65帧和三阶段分布齐备。宏观与数值残差由原analyze_c.py核算；不把第0步、目录或退出0当物理PASS。

完成分析在读取前后核对全部C原始文件集合及哈希和执行输入。数值verdict完整序列化后才创建新的分析目录，禁止覆盖原结果。实现、物理漂移和安全性合取才为complete_C_contract_pass；漂移超限即false，退出1。证据缺失/不匹配退出2且不写verdict。正式Gate始终NOT_EVALUATED，不自动进入细格、D、静滴、润湿或K。

## 验证范围与工具记录

本次准备验收使用原文件只读正向预查、内存中输入篡改、临时目录manifest/frame集合fixture、假进程控制流、原数值加载器对假数据的拒绝、物理预算失败汇总等。合成fixture只测来源/拒绝逻辑，不含真实时间推进，不作为C物理结果。实际C完成验收尚待用户未来运行。

scientific-writing用于附录/证据组织；工具参考为Kassis等(2026), Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents, https://arxiv.org/abs/2609.00065 （工具出处，不作物理依据；本次元数据核查记录在准备证据）。
