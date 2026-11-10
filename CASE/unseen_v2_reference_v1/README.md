# URV-v1 隔离参考程序：已编译、零步审计完成

这是两个候选条件的**显式沟槽参考程序准备包**。本版只允许描述配置、实际安装边界和初始化；`steady` 在原生程序中被拒绝。正式计算未启动，当前没有新参考 K，没有 V2 新预测成绩，也没有正式启动命令。

用户已采用 URV-v1 用于本轮实现、编译与零步审计。采用记录见 [common/adoption.json](common/adoption.json)。`common/` 中旧协议材料为逐字节副本，其“候选/尚未实现”等字段保留原日期语义；本版当前状态见本 README、准备封存和本轮报告。外部未归档数据使用历史仍为 PENDING。后续正式执行须另行核对历史、授权范围、逐条编号与输入绑定；不能把本轮准备封存作为正式执行许可。

- 主程序：[src/urv_reference.cpp](src/urv_reference.cpp)，从绑定的 D4 源码隔离移植；[mass_stats.h](src/mass_stats.h) 为 C 补偿求和头文件的原字节副本。
- 独立检查器：[analysis/check_results.py](analysis/check_results.py)，不导入求解器、拟合器或运行器。它检查来源、完成记录、双质量账本、全部统计窗及首次停止、几何、单位、平板剖面、h75 回归、三驱动力控制、网格资格和 V2 敏感性比较。调用前须另有正式执行合同及其独立保存的 SHA。
- 真实场读取：[analysis/read_fields.py](analysis/read_fields.py)，使用 VTK reader 读取完整引用链，排除周期重叠点，核流体坐标、数组、单位和体积分通量。周期压力为扰动，耗散数组单位 m²/s³；二维 CSV 的 Phi 为 rho×运动学耗散，单位 W/m³，两者分开。
- 零步审计：[scripts/audit_zero.py](scripts/audit_zero.py)，本轮编号 `URV_ZERO_20261101_01`。24 次 describe、24 次实际 precheck、24 次 initialize、24 个初始化场读取；总时间推进调用 0。
- 准备封存：[evidence/preparation_seal.json](evidence/preparation_seal.json) 与 SHA；本版编译依赖和动态库见 [evidence/build_environment.json](evidence/build_environment.json)。这是当前构建记录，不替代历史环境证据。
- 本轮证据入口：[准备报告](../../docs/reports/URV_v1_preparation_20261101/REPORT.md)。源码、检查器、编译与零步审计分别报告，正式数值/结果/物理验收仍未评估。

固定定义：P 沿槽 +y；T 横槽 +x。J 为流体速度体积分除以平面面积（m²/s）；K=nu×J/a（m³）；平均速度 U=J/(h+d/2)。参考程序不输入原公式或 V2 的 K。旧顺序 mass/mass_error 仍完整输出；正式质量门采用补偿物理质量相对自身初态的变化，严格 <1e-10；另要求密度差账本与其全程差 ≤1e-13。

原生零步初始化并非严格零速度场：与体力方案一致的物理速度包含 a×dt/2。初始化速度通过 reader 与这一值及双精度诊断对照。它不代表已计算出稳态流量。

## 后续完成结果的输入合同

下面是检查器所需格式，**不是已存在或已获准的执行包**。本轮 `preparation_seal.json` 的 simulation_authorized=false、preparation_only_build=true，检查器会直接拒绝它。

正式执行合同至少包含 protocol_id、simulation_authorized、preparation_only_build、author_external_data_history_confirmation、approved_run_ids、inputs_sha256；后者须覆盖检查器/协议全文件、主程序、编译依赖与运行库。另含 h75_regression_references 的 P/T 原结果目录、result_sha256、diagnostics_sha256。后续执行准备须绑定具体配置、输出目录、资源上限、每阶段授权与 run_id，并在移除编译保护后重新编译、检查、封存；本轮没有移除保护。

每条完成记录 completion.json 至少包含 release_sha256、planned_case_id、run_id、independent_process_exit_code、inputs_unchanged、完整 inputs_after_sha256、output_sha256。output_sha256 使用相对于该条结果目录的路径，须覆盖全部日志、配置、原生结果、诊断、帧表，以及完整 VTK master/引用 payload。独立退出必须来自外层进程捕获，不能从原生 PASS 字段抄写。缺失、改字节、来源变化、未完成、零步输出均不得通过。

检查器命令接口为 `--run` 或 `--batch-index`，另须提供 `--release`、`--release-sha256`、`--out`；检查器仅分析，不运行求解器。逐条结果可先独立验收，当前汇总入口保守要求全部 24 条合格记录齐全再给两个条件的汇总比较。每阶段仍须用户分别启动、完成后审查，不自动串批。

h75 回归比较全部共同旧诊断字段。本版采用保守停止：若不逐项相同，保存差值并暂停；即使 K 差 <1e-4，也不能自动解释为无影响。后续若出现可解释的浮点差，须保留原始差值、独立说明及裁定，不能静默加宽阈值。

## 本轮验证边界

Python 35 组测试、原 C 算术测试和长双精度独立质量参考测试通过。Python 测试包含明确标记的人工数组和两条旧 h75 完整轨迹；人工 K/轨迹不是流场求解。首轮测试中 q 精确相等断言不适合浮点坐标；第二轮人工汇总断言误把薄间隙恶化视为主要条件必须失败，两次日志均保留，最终按 URV-v1 分条件判定。物理门槛没有改变。

本版检查器尚未经新 URV 稳态完整输出作端到端验证，这是正式结果尚未产生的直接限制。编译成功、72 次零步调用和 24 个初始化场读取不能授予新参考资格。NUMERICAL_GATE=NOT_EVALUATED，RESULT_PASS=false，REFERENCE_QUALIFIED_FOR_CASE=false，physical_validation=NOT_EVALUATED，submission_ready=false。
