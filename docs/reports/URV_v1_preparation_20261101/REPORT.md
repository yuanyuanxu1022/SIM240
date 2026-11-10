# URV-v1 隔离参考程序与独立检查器准备报告

2026-11-01。用户授权：按采用的 URV-v1 实现、编译并做零步审计；正式计算保持未启动。审计编号 `URV_ZERO_20261101_01`，不是正式求解 run_id。

**本轮准备任务完成。** 隔离程序已实际编译；24 组配置各完成描述、实际边界安装和初始化检查，合计 72 次原生零步调用；24 个初始化场已由真实 VTK reader 读取。实际时间推进调用总数为 **0**。独立检查器已实现并通过准备级测试。尚无两个新几何的稳态参考 K，不判定 V2 是否改善，不放行正式数值/物理验收。

## 实现与物理边界

新增 CASE 为 [CASE/unseen_v2_reference_v1](../../../CASE/unseen_v2_reference_v1/README.md)。原 D4、原 C、旧结果、历史 FAIL、V2/G4 锁和原 URV 协议材料保持。

主程序 [urv_reference.cpp](../../../CASE/unseen_v2_reference_v1/src/urv_reference.cpp) 从 D4 绑定源隔离移植，C 的 mass_stats.h 为原字节副本。19 处列明替换可逆恢复原 D4 全文；几何/壁面 7,858 字符、物理场/剖面输出 3,068 字符、初始化/体力/碰撞参数 584 字符、原收敛窗 993 字符逐字节未改。证据为 [source_port.diff](source_port.diff)、[source_port_edits.json](source_port_edits.json)、[physical_port_audit.json](physical_port_audit.json)。这些源码核对不替代之后的真实 h75 回归。

原顺序质量 mass/mass_error 及其原初态分母完整保留；新增补偿物理质量与补偿 Σ(rho−1) 双账本。质量门仍严格 <1e-10，两修正账本全程差 ≤1e-13；另存旧质量门状态。碰撞、材料、边界、体力、速度、J、时间推进及原窗口停止计算没有重新定义。新增计数器只记录实际 collideAndStream 调用。构建 `URV_PREPARATION_ONLY=1`；即使显式配置 `mode=steady`，也在创建有效配置/流场前拒绝。

研究对象保持固定间隙、单相、充满液体、解析真实矩形沟槽。P=+y 沿槽，T=+x 横槽；J=速度体积分/平面面积（m²/s），K=nu×J/a（m³），U=J/(h+d/2)。参考动力学不输入原公式或 V2 系数。模型预测表及其 SHA 保持原值、参考列仍空。共同数据为 period=Ly=240nm、w=120nm、rho=1000kg/m³、nu=1e-6m²/s、tau=1。候选仍为 U_REG h60/d80 和 U_THIN h30/d80（nm）；薄间隙横槽风险单列。

## 编译与原生零步证据

实际编译退出 0，完整日志 [compile_attempt1.log](compile_attempt1.log)。编译器 g++13.3.0，经 mpic++；OpenLB 当前 HEAD=`882924a9cfc8dcdf82909e39530789cb6f5ebcc4`。编译日志含警告，无编译错误；程序 SHA256=`9a139fc569b901b01c4709d5e5cd6c9ff89e66a9a42e67a198d3a96faadd08d3`。实际依赖清单来自此次 .d 与链接库，1,393 项；另绑定 15 项动态库。OpenLB 工作树状态按实际记录，不声称干净，也不把当前构建冒充历史环境。[build_environment.json](../../../CASE/unseen_v2_reference_v1/evidence/build_environment.json) 保存编译命令、源/库、编译器与程序哈希。

矩阵 24 项全部核窗口、最大步数与 dt，独立有理数算术与原生配置输出一致。各项还实际安装壁面、测量初态、保存场再读回。8 种不同几何/网格的结果如下；同几何的两个方向和额外驱动力也分别做了原生零步审计。

| h/d（nm） | dx（nm） | 核心流体节点 | 实际安装壁面连接 | q 范围 |
|---|---:|---:|---:|---|
| 75/100 回归 | 5 | 57,600 | 32,448 | 0.5–0.5 |
| 30/0 平板 | 1.25 | 884,736 | 368,640 | 0.5–0.5 |
| 60/80 | 5 | 46,080 | 30,528 | 0.5–0.5 |
| 60/80 | 2.5 | 368,640 | 122,496 | 0.5–0.5 |
| 60/80 | 1.25 | 2,949,120 | 490,752 | 0.5–0.5 |
| 30/80 | 5 | 32,256 | 30,528 | 0.5–0.5 |
| 30/80 | 2.5 | 258,048 | 122,496 | 0.5–0.5 |
| 30/80 | 1.25 | 2,064,384 | 490,752 | 0.5–0.5 |

上述 candidate=valid=installed，fallback/unresolved=0，材料数量与独立解析/枚举相符。独立 XZ 壁面求交、Y 周期挤出核壁面数量；初态体积与预期相符。初始修正质量对应 rho×N×dx³，密度差账本初值为 0。[zero_step_summary.json](zero_step_summary.json) 与 [zero_step_verification.json](zero_step_verification.json) 给出逐项路径；完整原始证据保存在 `CASE/unseen_v2_reference_v1/audits/URV_ZERO_20261101_01/`，没有正式 results/。

24 个初始 VTK 场均用真实 reader 核引用 payload、坐标、唯一流体点、速度/压力/耗散有限值和单位，排除周期重叠点。积分 J 与双精度测量在 Float32 导出及 Float64 求和界内一致，包含体力半步速度 a×dt/2；这不是稳态速度。周期压力为 Pa 扰动，VTK 耗散为 m²/s³；二维 CSV Phi 乘 rho，为 W/m³。没有凭初始化场声称稳态耗散或质量全过程闭合。

零步过程按单进程、单线程和地址空间 8GiB 限制执行。零步输出总占盘约 20MiB，仅代表初始化场；没有实测正式运行峰值内存、全过程输出或耗时。原 110 小时为 24 条墙钟上限之和，含义不变。正式执行仍需重新检查当时 RAM/磁盘及逐条资源限制。

## 独立检查器与测试

[check_results.py](../../../CASE/unseen_v2_reference_v1/analysis/check_results.py) 不导入求解器或拟合器，仅分析已完成数据。它要求独立提供执行合同 SHA，核输入/输出哈希、独立退出与完整轨迹；重算两质量账本、全部统计窗和首次达标停止点；核方向/单位、边界/体积/截面、Re、平板解析剖面及 h75 回归。源程序的 PASS 不替代独立检查。

汇总模块实施三驱动力控制、三格条件 GCI/中细差、估计敏感性带及原/V2 比较。参考不合格则不评分；薄间隙恶化可以与主要条件改善同时存在。u 仍是估计敏感性，不是置信区间或严格误差界；最低实用改善仍为 2 个百分点。当前汇总 CLI 保守要求 24 条已独立验收的原始记录齐备；逐条验收可先进行，不自动串批。

本轮软件验证：

- **35 组 Python 测试通过**：[checker_tests_final.log](checker_tests_final.log)。包含人工轨迹/判定算术、破坏质量/方向/单位/时间/窗口/几何的反例、参考失败不评分、薄间隙恶化不自动否决主要条件，以及来源/数据历史/缺文件/独立非零退出保护。人工值全部为测试数据，不是新 DNS。
- 两条旧 h75 P/T 完整诊断轨迹只读复算全部窗口及最终 std/span，匹配旧记录；本轮没有重新求解 h75。
- **2 个 C++ 算术测试程序通过**：原 C 测试 [mass_stats_test.log](mass_stats_test.log)；独立 long double 参考与真实顺序累加损失反例 [mass_oracle_test.log](mass_oracle_test.log)。后者用二进制可精确表示扰动，补偿和与独立参考相符；它是算术验证，不是流动验证。
- **2 个外部 CLI 拒绝测试通过**：当前准备封存与错误 SHA 均退出 2，无成功 acceptance；回执位于 [checker_cli_rejections](checker_cli_rejections)。原生 `steady` 负例也退出 2，时间步为 0。

开发过程失败保留：首轮 26 测试中，几何测试用了不适合浮点坐标的逐位相等断言（q=0.5000000000000018），后改按原 q 容差 1e-10 核；第二轮 29 测试中，一条人工汇总断言错误要求薄间隙恶化也使主要条件失败，已按协议分条件判定修正。两次日志均保留；没有改物理门槛或历史 FAIL。最终 35 测试均通过。

**检查器尚未经新 URV 完整稳态输出作端到端验证。** 因本轮明确不产生该输出，此项保持未评估。未来正式执行合同、逐条 run_id/配置/输出目录/资源绑定、正式外层运行器及开放时间推进后的新构建仍需另行准备。当前封存只允许准备；不能直接用本版主程序启动正式计算。

## 保护、封存与下一停点

[preparation_seal.json](../../../CASE/unseen_v2_reference_v1/evidence/preparation_seal.json) 为 **PREPARATION_ONLY_NOT_EXECUTION_RELEASE**，SHA256=`e0eb9a54c1c1168d25483a085e70462d04cfa76aeb4922dddbea17b07b1811cb`；1,432 项程序/检查器/协议/构建依赖绑定。simulation_authorized=false，preparation_only_build=true，approved_run_ids=[]，actual_formal_run_ids=[]。后续正式版本必须重新绑定，不覆盖本准备证据。

本轮 82 项预先选定保护来源前后哈希一致；并重新对照上一轮 C/h75 基线与 h75 回归原结果/诊断共 **1,686 项既有绑定，均无变化**，见 [old_evidence_preservation.json](old_evidence_preservation.json)。这不是整个工作区清洁声明；原有 Git 修改/删除/未跟踪项没有清理。没有 Git 提交、推送或对外发送。

当前状态分别为：

| 层级 | 当前状态 |
|---|---|
| 隔离实现、此次编译、零步几何/初始化、检查器准备测试 | PASS |
| 新正式流场计算 | 未启动 |
| 新正式 NUMERICAL_GATE | NOT_EVALUATED |
| 新正式 RESULT_PASS | false |
| 新候选稳态 geometry_PASS / 参考资格 | 未评估 / false；零步几何 PASS 单列 |
| 新 V2 模型比较、实验物理验证 | NOT_EVALUATED |
| strict_error_bound_established、submission_ready | false |

外部未归档数据历史仍 PENDING；用户对 URV-v1 的本轮实现采用不代替这项事实确认。旧 D4 预测 HOLD、旧 N8 状态、G4 冻结和 C/h75 限定资格不升级。下一具体动作是只读复核本准备包；之后确认外部数据历史并另行准备 S0 两条 h75 回归的正式执行合同。每阶段仍分别授权、用户启动、完成后独立验收。本轮不交付正式启动命令，也不自动进入 S0。

本报告由 AI 按 scientific-writing 的证据组织规则和 paraview-publication 的真实 reader 规则整理；不是独立人工科学验收或论文最终采用。当前状态与跨 AI 停点同步到 `docs/reports/SIM240_AI_CONTEXT.md` 和最新 `AI_HANDOFF_20261015.md`。

所用科研技能方法来源：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://arxiv.org/abs/2609.00065), DOI [10.48550/arXiv.2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。2026-11-01 在线核作者、题名、年份及当前修订；这是 AI 工具流程归属说明，不作为本项目流动物理或数值精度证据。
