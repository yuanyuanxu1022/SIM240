# 当前批次：余14项粗格主开发

本入口独立于旧6项筛选。只允许stage_cases.csv中的14项new_dev，不含已完成几何、线性、平板、回归、旧资料、网格或预测；使用原已验收筛选的源码/binary与全部原数值门槛。

先读PROTOCOL.md，再看evidence/preparation.json、evidence/prebinding_review.json、release.json和evidence/final_review.json。14份实际key=value配置位于launch_configs/，未来运行生成配置必须逐字节一致。zero_step_checks/均为describe/precheck，collideAndStream=0，不是正式流动结果。

运行入口run_remaining.py默认只检查；仅明确--execute由用户手动启动后才创建正式batch目录。源码、binary、依赖或冻结输入变化会拒绝运行；已存在批次拒绝覆盖/续跑，已存在相同case正式结果也拦截。资源要求可用RAM≥2GiB、空闲磁盘≥7GiB；本机单进程单MPI rank，每项前重新核资源。

NEXT_COMMAND.txt是本机唯一待用户启动命令。release.released仅表示14项技术启动前提已准备，不是NUMERICAL_GATE或RESULT_PASS，也不表示已运行。程序不自动分析、不续到网格/预测。非零退出、绑定变化、资源不足即停，不重复点命令重跑已有batch。

正式输出预定在父目录results/development_remaining14_20261024_v1；每项保存配置/manifest/日志/资源/独立exit/CSV/VTK及输入后核对，批次另有stage_manifest、stage_progress、exit_code和stage_completion。运行完成后独立分析原始数据、全滑窗、实际全部流场及来源，保持原RESULT_PASS=false，另记录范围受限验收结论。

当前完整状态见PREPARATION_STATUS.md；旧D4根README和旧NEXT_COMMAND是绑定历史快照，不能照它们重复启动已经完成的基础/筛选。新机器不能复用本机绝对路径release，须重新构建与核查绑定。
