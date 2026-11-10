# 矩形参考求解：资源与原始记录准备（不求解）

2026-10-25。本目录承接 `solver_result_review_20261025` 的未执行候选，完成**资源复核和两项记录基础部件**。使用 scientific-critical-thinking 技能区分组装实测、存储情景和求解预算。原 18 项白名单 `execution_authorized=false`、参考协议 `DRAFT_v2`、旧网格 FAIL、G4 v1 锁及预测 HOLD 均未改变。

## 资源判断

[`resource_review.json`](evidence/resource_review.json) 复测最大混合平板 `B0MIN_FLAT_T_d1p25` 的**组装/压力预检**：矩阵 104943×104943、3,103,649 非零元；子进程独立退出 0、峰值 RSS 299272 KiB（约 292.3 MiB）、1.14 秒。矩阵/RHS SHA 与先前 9 项审计相同，输入前后 SHA 一致，`solver_called=false`。测量命令的完整标准输出和标准错误分别在 [`assembly_only_stdout.json`](evidence/assembly_only_stdout.json)、[`assembly_only_stderr.log`](evidence/assembly_only_stderr.log)。该次只测组装，不测 GMRES 迭代。

测量时 `MemAvailable=17954631680` B（约 16.72 GiB）、本卷可用 `361916616704` B（约 337.06 GiB）；这是瞬时机器快照，不是未来可用承诺。按 32 位列号的 CSR 三数组约 35.9 MiB，104943 未知量、GMRES 重启长度 50 时 51 个双精度向量约 40.8 MiB；均只是**一小部分**存储，未包括 PETSc 装配、临时副本、因子或环境。先前“可用 RAM 4 GiB、结果盘 4 GiB、总 2 小时”仍是**待审预算**；无预条件器 GMRES 的收敛、实际峰值内存、耗时和输出盘量均未测，不能放行 18 项。资源安排继续建议单进程、逐项串行，每项运行前重新量测并在超预算时停止，不能降低精度门槛凑结果；该安排不是许可或运行命令。

## 新增的记录部件

- [`raw_writer.py`](raw_writer.py) 只接受显式标识来源的内存数组，在新目录用 `.npy` 保存 16 组原始数据：三角网格及坐标、原代数向量、周期回填后向量、速度/压力自由度坐标与索引、速度分量与原值、壁面索引、P1 压力原值/面积权重/去均值、周期从属/主索引。核形状、float64/int64、有限值、索引范围、压力/速度回填及压力去均值；记录文件 SHA、形状和精度，禁止覆盖及链接输出目录。未来真实来源还必须带 planned ID、源码/网格/矩阵哈希。`.npy` 数据是原值，不截断为图或四舍五入 CSV。二维速度展开的修正和真实网格人工场核查见[后续适配审查](../result_adapter_review_20261026/REVIEW.md)。
- [`process_capture.py`](process_capture.py) 为独立子进程捕获基础部件，用非 shell 参数数组启动，分别保存完整 `stdout.log`、`stderr.log`、`independent_exit_code.txt`，记录命令、开始/结束时间、输入前后 SHA、日志 SHA 和耗时；子进程失败时保留文件，不自动重试。**真实求解适配入口明确拒绝**，当前仅可用于合成测试。其 RSS 字段是操作系统对本 Python 进程所启动子进程的累积高水位，不能当单项峰值；正式资源记录须单独实现逐项峰值。

[`test_preparation.py`](test_preparation.py) 使用明确标记 `SYNTHETIC_*_NOT_RESULT` 的小数组和退出码 7 的短子进程，通过 16 组数据逐值读回/哈希、完整双日志、独立退出码、输入改动和覆盖/链接拒绝。临时合成文件在测试后删除，只有 [`synthetic_checks.json`](evidence/synthetic_checks.json) 保存判定；没有把它们放进正式结果目录。[独立静态复核](evidence/independent_preparation_review.json) 为 `PASS_PREPARATION_ONLY`，4233 个受保护路径均一致。

## 尚缺的正式运行链

1. 为真实有限元对象写**受审适配层**，把 mixed DOF、周期映射和网格逐项传入写出器；当前候选 `candidate_solver.py` 只返回内存结果，尚未调用本目录代码。
2. 补充求解历史/真实残差、周期迹、通量/散度、能量和平板物理单位的原始诊断与独立复算；本目录的 14 组数组不足以通过 `record_contract.json`。
3. 审查实际预条件器、逐项峰值 RSS/时长/盘量，形成可审的参数与预算；当前 PC NONE 只是代数候选，不是生产方案。
4. 参考协议和门槛先经审查冻结，再另行取得矩形求解授权；运行器须绑定新的 release、唯一 run_id、日志/退出码/输入 SHA 和失败保留。此目录不提供真实启动命令。

因此没有正式 run_id、真实原始场、求解独立退出码或数值验收。`NUMERICAL_GATE=NOT_EVALUATED`、`RESULT_PASS=false`、`geometry_PASS=null`；不影响旧开发结果及预测禁令。
