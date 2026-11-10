# S2 有限性能任务单次启动核查

快照时间：2026-11-02 20:55:58 +0800。范围仅单次只读启动状态，不作完整性能/数值/几何验收，不重跑或持续轮询。

已确认用户启动：目标tmux会话存在，控制器PID716959，沿槽P原生求解器PID717003；两进程的参数与绑定release及P配置相符。release SHA b675010adcc9e57627d3ff39c93d72394e16489e3713abe09851d5de31c5c7e1 已核对；本轮没有重做完整2058输入接受。

启动尝试记录时间20:55:01.490726，P进程意向记录20:55:01.584289。该意向文件的process_started_not_yet_confirmed=true是启动前静态字段，不能单独证明运行；本轮以真实进程和新增完整诊断行确认。attempt中的actual列表亦是原静态字段，不把空列表解释为原生未启动。

P（URV_S2_PERF_P_dx1p25_v1_20261102_01，沿槽+y）正在运行，diagnostics最后已见完整行为step91；观测记录sample56也已见step91。这里只报告落盘进度，不把它当实际调用次数的精确上限，也不由短段推吞吐量/收敛时间。

T（URV_S2_PERF_T_dx1p25_v1_20261102_01，横槽+x）尚未启动，目录仅run_config.txt/run_manifest.txt，符合P证据充足才进入T的控制顺序。P尚无performance_receipt/acceptance，批次结果不存在；当前没有完成或性能充足结论。控制器日志为空，仅据此不能判断异常；实际进程和数据证明正在工作。

performance_attempt.json、持久lock均存在，不能重复执行原启动命令。每条1800秒或观察完整step≥2048先到停止、TERM10秒后必要时KILL；原协议的证据不足/异常即停、不重试、不进正式S2继续有效。

本轮新增snapshot.json、日志尾部/已有JSON快照及此状态记录，原始运行文件只读；没有调用求解器/VTK读取器、构建、发送信号、启动/重启任务或进入正式计算。没有再次读取正在变化的日志；报告只对应上述时刻，不保证稍后状态。

NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、REFERENCE_QUALIFIED_FOR_CASE=false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED；reference_qualified/strict_error_bound_established/submission_ready=false及旧历史FAIL/S0/S1接受不变。下一步等性能批次结束后另行分析已有结果，不自动进入正式S2/S3。
