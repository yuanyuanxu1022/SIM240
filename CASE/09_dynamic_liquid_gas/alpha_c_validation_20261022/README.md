# Alpha参数化与C粗网格收支独立验证

准备入口：PREPARATION_STATUS.md。物理/实现口径：CODE_REVIEW.md。执行冻结：PROTOCOL.md + protocol.json。完整绑定：evidence/build_binding.json。

本目录新增，旧A/B与共享OpenLB未改。alpha只进入CH平衡分布，NS读取原始化学势；三维修正源项沿用已验收版本。C是64步完整耦合诊断，不测K或判平衡。

## 当前执行边界

本轮已编译并检查真实CellD碰撞、静态参考、合成负对照及20项零步初始化。没有正式alpha/C空间推进。每阶段默认只预检查，显式--run才启动；不覆盖、不恢复、不重试，不自动分析或下一阶段。

用户首先独立启动alpha阶段，命令只见NEXT_COMMAND.txt。它执行16项CH空间验证；结束后另行核对证据并按冻结协议分析。C的4项程序已编译和零步检查，但须alpha验收通过后由用户另行启动，runner不会自动接续。

## 结果分析约定

分析器只读取已有完成数据，要求批次/全部子项独立退出0、完整manifest/步数/文件集合、绑定不变。alpha分析输出固定交接目录analysis_alpha/verdict.json供C预查读取；C分析另存analysis_c。输出目录若存在，分析器拒绝覆盖。

形式为 `analyze_completed.py --stage <alpha或c> --output <新的分析目录>`。这不是启动求解器的命令；计算完成前不把目录或可执行文件当作完成证据。

逐步C三维字段为gzip小端float64，形状及列见各run内frame_schema.json，可用analyze_c.py读取。第1步另有NS/CH全部38个分布的三个阶段数据；其余步的逐分布误差来自程序内阶段检查，宏观量可从全程字段独立重算。

## 依赖、储存与范围

单MPI进程、CPU_SISD；使用本机既有OpenLB库，不需重建后端。Python后处理需NumPy；版本证据在evidence/environment.json。磁盘预留alpha3GiB、C12GiB；C未压缩原始字段约9.68GB，实际gzip大小待运行后核实。正式耗时未实测。

任何失败保留原目录/日志；修复另立版本，不放宽冻结门槛、不修改历史FAIL。第一篇、GHY原始资料、C细网格/D平衡/静滴/润湿/沟槽K均不由本目录自动推进。
