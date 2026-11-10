# S2 有限性能标定接入

采用 S2-MIP-v1-PERF 及 docs/reports/URV_S2_perf_compatibility_review_20261102/MINIMUM_IMPLEMENTATION_SCOPE.md。
本 CASE 仅复用原 S1 二进制，不包含 C++ 源码或构建步骤。B/原检查器和其他 CASE 只读。

四项职责：scripts/prepare_perf.py、analysis/perf_contract.py、scripts/run_perf.py、analysis/check_perf.py。
tests/test_perf.py 仅做软件模拟，不调用原生程序或场读取器。

准备仅预留两条含 PERF 的身份，P 沿槽+y → T 横槽+x，dx1.25 nm、h60/d80 nm；输出仅 performance_runs 下。
原配置仅 run_id/output_directory 改变；原10368步窗、602112最大步及帧计划保持。
独立准备封存 evidence/preparation_perf.json 的所有执行权限关闭，approved/actual为空。
run_perf 默认只读核对；准备封存即使附 --execute 也拒绝，且不创建启动标记。

未来真实推进须有两条有限性能推进的明确授权、单独 AUTHORIZED_PERFORMANCE_RELEASE 及外部SHA，由用户手动启动。
本轮不生成该合同或启动命令；正式计算始终另行授权。
未来每条预算1800秒或首次观察完整step≥2048先到停止，SIGTERM后最多10秒再必要时SIGKILL。
每秒最多一次观察；保留缓冲超调、非零退出、缺少末态/原生计数和未换行尾部的真实证据。
P异常或两个测速区间不足即停，不自动进入T，不重试/延长/续跑/转正式。

科学字段保持未评价/false。性能证据不进入正式参考、GCI、V2误差表；不能保证12小时内收敛。
报告入口 docs/reports/URV_S2_perf_implementation_20261102/REPORT.md；共享交接见 docs/reports/SIM240_AI_CONTEXT.md。
