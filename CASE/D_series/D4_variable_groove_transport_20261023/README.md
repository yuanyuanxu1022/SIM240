# 可变槽宽/周期单相输运工作区

2026-10-23。用户授权实现与运行前检查；本目录独立于旧D2，物理范围仍是固定间隙、充分充液、牛顿单相周期直槽。

**当前：源码已编译，90行配置解释、42种实际网格几何/q检查、6组初态三维场读取均通过；所有检查为零时间步。正式稳态、流动收敛、平板/回归精度以及真实中间帧尚未验收。**

先读PREPARATION_STATUS.md，再读PROTOCOL.md与protocol/execution.json。源码src/variable_groove_transport.cpp；历史D2副本及差异位于evidence。完整旧输入保护59项，旧源码、数据、FAIL和冻结门槛未改。

实现了w/P/Ly/a等参数、居中槽几何、动态面积/体积/归一化、完整小数网格与run_id、输入合法性/禁止覆盖/分阶段保护。单MPI rank；不能直接mpirun多进程使用。物理碰撞、力和通量定义沿用D2；d=0单独退化为完整平板顶壁。

新观察窗Δt*=νΔt/h²=.75，最长时间8(h+d)²/ν，详见新协议；不改旧1000步窗/60000上限。帧计划t*=0,.01,.02,.05,.1,.2,.5,1,2,4,8，实际step/time/tstar及到达情况写入frame_index/frame_schedule；收敛末态必保存。pressure_Pa为周期压力扰动，dissipation_m2_s3保留原单位。

tools/build.py仅编译并记录本机环境。tools/preflight.py解释所有参数、运行42种零步几何检查及6组初态输出；tools/verify_geometry_independently.py独立核节点和18方向边界连接；tools/check_initial_fields.py需要pvpython，实际读取VTK。tools/check_rejections.py检查非法输入/覆盖与阶段拦截。其他机器须重新编译、预查和绑定，不能复用本机绝对路径的release或宣称本机验证已覆盖老师机器。

编译默认OpenLB为/home/dell/openlb，可用SIM240_OLB_ROOT环境变量指定本机依赖；需先有对应库。共享包先恢复隔离_workspace，新增D4必须在恢复后的CASE/D_series目录使用，不直接在分类数据目录写入新结果。旧工作区不覆盖；本轮没有重做新增D4的全新Git克隆验证。

**给用户的唯一首批命令在NEXT_COMMAND.txt，目前没有执行。** 它只启动2项旧几何回归和6项平板，共8项；不是新增60项全批。run_stage不自动分析、不自动进入开发/预测/网格阶段，程序失败即停止；完成后需独立分析输出。另82条主表行被当前阶段许可拦截，预测组还需预先冻结模型/预测。

evidence/formal_run_release.json的released仅指本机首批启动前提已准备，不是NUMERICAL_GATE或RESULT_PASS。当前NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false。源码/配置/依赖哈希变化后命令会拒绝继续，需要重新核查和绑定。
