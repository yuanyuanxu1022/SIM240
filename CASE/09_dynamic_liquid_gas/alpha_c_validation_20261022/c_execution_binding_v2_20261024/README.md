# C 执行与验收绑定 v2

这是独立的执行/来源核对层，物理程序继续使用父目录已编译的 coupled_check，数值分析继续调用父目录原封不动的 analyze_c.py。未改方程、物性、4组算例、64³/64步、源项初始化、输出字段或冻结判据。运行前附录见 PROTOCOL_ADDENDUM.md。

父 binding、alpha manifest/verdict/EXPORT_PROVENANCE、旧错误日志及全部原始证据保留。本层仅接受已审查的AGENTS管理规则两条变更：旧5700b378…→新59d1cc51…，未来任何其他变更仍拒绝。不能用本层声称旧3401项在当前全部匹配。

运行入口 run_c.py 默认只预查，只有显式--run才可能调用求解器；无覆盖/恢复/重试/自动后处理，单批次锁，失败停止。此次实施任务明确不启动计算，也不交付启动命令。准备检查在 preparation_evidence/，最新完成状态见 PREPARATION_REPORT.md（不是物理Gate）。

分析入口 analyze_completed_c.py 的--check-inputs仅核同一新增绑定，不判断C完成。完成分析另需--output指定本目录内新的分析文件夹，要求完整4项/独立exit0/每组65帧/首步三阶段分布，再交给冻结数值分析器。新批次固定alpha_c_20261024_binding_v2_c，数据只写本目录output和evidence；旧alpha和原C路径不写。没有正式批次时，完成分析必须拒绝，不能用初始化或合成测试数据替代。

未来C的实现合同、物理预算、安全性分列。物理预算保持Q/质量1e-9，已预测两组本构相量及目标组质量可能超限；余额可解释不豁免预算。所有正式Gate仍NOT_EVALUATED。

本目录仅按本机原绝对路径核查；没有验证跨机器搬迁。Python封装不改变C++程序，未重编不声称新编译。版本冻结：execution_binding.json；一次性准备封装freeze_execution.py；来源和控制流隔离测试test_binding.py不运行求解器。
