# 首批6项2.5nm中网格准备入口

先读PROTOCOL.md、policy.json及项目docs/reports/SIM240_AI_CONTEXT.md。此目录为新阶段，不修改旧源/结果/协议或G4锁。只允许stage_cases.csv中6项中格，其他细格与预测关闭。

start_from_project.sh默认--check，不创建正式结果；只有用户明确--execute才运行。运行前预存6份launch_configs、核来源及资源、拒绝已有batch/case。NEXT_COMMAND.txt只在preparation、review、release和实际启动目录检查通过后交付。准备/发命令≠用户已启动或计算完成；结果需独立验收。

prepare_stage.py只做describe/precheck零步；test_preparation.py用旧已验收数据/人造数据检查，不运行steady。bind_release.py冻结本机输入，已存在release绝不覆盖。

analyze_results.py及window_metrics.py提供分块独立数值核验；check_flow_frames.py逐帧核字段及通量；accept_batch.py是完成后显式验收入口，不自动调用。export_references.py只输出核过来源的bundle；compare_grid.py只接受bundle，分别给每几何、窄槽局部和全局三格状态，CLI退出0不是网格PASS。

完整状态及准备验证在项目根docs/reports/D4_grid_mid6_preparation_20261024/REPORT.md。此README与evidence/preparation为准备快照，后续运行状态以项目当前状态及新独立验收报告为准，不能改绑定文件来追记进度。
