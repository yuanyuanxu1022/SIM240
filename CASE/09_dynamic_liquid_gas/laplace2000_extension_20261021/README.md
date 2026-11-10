# LP2000 独立诊断扩展

状态（2026-10-21）：2000步诊断已完整结束并分析，独立exit0、2001条记录与全部预定截面齐备。最新结论见`analysis_2000_20261021/REPORT.md`：压力振荡衰减、尾窗均值接近，但仍有8–14%峰峰波动及残余运动，正式Gate未评估。`analysis_pending_20261021/`为旧运行中快照。

用户已授权准备2000步扩展并交付运行命令。运行参数与分析窗口冻结于PROTOCOL.md和protocol.json；从step0重新计算总2000步，非checkpoint续算。默认入口run_diagnostic.py只运行新run_id `target_lp_diagnostic2000_20261021_v1`，没有自动后续算例。

与原200步保持相同物性、网格、初态和碰撞耦合。原200步目录完全保留；本目录C++仅限制laplace、将准许长度设为0或2000、添加每250步中截面保存。差异见evidence/source_changes.diff。

已验证：

- evidence/build.log、build_exit_code.txt：真实编译与独立退出码0。
- evidence/build_binding.json：当前源码、参数、协议、后处理、后端源树、库和二进制SHA256；启动前后核对。
- evidence/preparation_checks.json：零步读数与原200步step0逐字段相同，初始截面逐字节相同；262144流体点，LP无壁且无非法/回退link条件。仅0步，无时间推进。
- evidence/entry_guard_checks.json：拒绝2001步、200步、contact；2000步解析被接受后由已有目录防覆盖检查拦住，未创建网格/推进。
- test_analysis.py：3个解析定义测试，分别核固定窗口与趋势、常数/零均值、不受早期窗选择影响的已知衰减测试信号。测试数据不是物理结果。

默认运行命令保存于NEXT_COMMAND.txt；由用户在SIM240 Linux机器终端启动。预计约4–5分钟是按旧200步摊销外推，新增输出有开销。

完成后证据位于evidence/target_lp_diagnostic2000_20261021_v1/（独立退出码、完整日志、manifest）与output/同run_id/（逐步history、初末/每250步中截面、几何审计）。不以tmux消失或exit0代替验收。若非零退出/数据不完整，先分析失败，不自动重跑或修改参数。

analyze_completed.py仅离线读取已完成的2001条数据，按冻结的末500/250步及相邻半窗输出统计、全程最大守恒漂移、半径与化学势截面描述。它不会启动求解器，也不会给出正式PASS。后续由新结果分析任务执行并复核。

本轮三类正式Gate均NOT_EVALUATED；真实GHY资料与第一篇证据不升级。完整准备校验见verification.json。
