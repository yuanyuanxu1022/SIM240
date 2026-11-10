# 准备完成证据与当前停点

日期2026-10-23；case=D4_variable_groove_transport_20261023。采用上一轮φ=.5、P=2w与60项新增方向计算的设计基线，仅完成本轮授权的实现、编译、运行前核查。未独立核实导师口头意见，不以新程序覆盖旧设计快照或历史结果。

| 步骤 | 当前证据 | 判定边界 |
|---|---|---|
| 新目录与源码 | src/variable_groove_transport.cpp，evidence/source_changes.diff | 旧D2保持；不是大规模物理模型重构 |
| 参数、体积与时间 | 90行describe通过，effective_config与独立尺寸/体积/dt/窗/上限计算一致 | 未取得新K |
| 编译 | build_exit_code=0；build.log、build_environment.json，1398份实际编译依赖及3链接库哈希 | 未重编译OpenLB库；当前库提交882924a9…，有已记录的未跟踪文件；不能充当历史运行版本证明 |
| 真实几何/q安装 | 42种唯一(h,d,w,P,Ly,dx)全部precheck exit0，节点数、安装/候选连接数一致，q=.5、fallback/unresolved=0 | 单MPI rank；每项collideAndStream=0；不当流动PASS |
| 独立几何复核 | independent_geometry.json，独立二维材料/18方向射线再乘周期长度，42项与实际安装结果相同 | 不是网格误差估计 |
| 初态完整输出 | 6组P/T：窄浅、宽深、平板；pvpython VTK reader读取四数组、流体点数/有限值/半步力初始速度匹配 | 初态frame0通过；真实启动过程和最终收敛场未运行 |
| 非法输入和保护 | 18项配置/覆盖拒绝、3项非法阶段许可拒绝、1项正对照；只有8条基础行允许启动 | 不自动运行任何阶段 |
| 旧内核与阈值 | 测量/剖面/边界审计函数逐字节相同，9项限值保持；d0顶壁退化分支在新副本修复 | 新物理时间窗为单独协议选择，与旧步窗不冒称相同 |
| 来源与输入保护 | protected_inputs.json中59项保持；138项零步动作的manifest/日志/exit/输入后哈希核对 | 零步期间的旧wrapper快照已保留；之后仅收紧steady阶段白名单，数值内核未变 |

资源实测：最大15925248流体节点的1.25nm零步几何检查峰值10124772KiB（约9.66GiB），耗时18.29s。该数值仅为本机零步检查，不是正式稳态RAM/耗时保证。6组初态VTK引用文件分别约3.3KB至56.8KB，初态高度可压缩，不能按该体积推断有非零结构的后续所有帧大小。

完整记录evidence/preflight.json、initial_fields.json、independent_geometry.json、rejection_checks.json、static_code_review.json、preparation_binding.json。NUMERICAL_GATE=NOT_EVALUATED；RESULT_PASS=false。geometry/q仅对上述实际安装的42种网格成立，不推广到任意槽宽/占比或连续范围。

下一步已准备但未执行：用户在本机Linux终端运行NEXT_COMMAND.txt的唯一tmux命令，batch_id预留foundation_20261023_v1。只计算regression两项与smooth六项；完成后先独立核收敛、质量/密度/Mach/截面、K、平板剖面、帧时间/末态及来源绑定，再决定是否放行开发组。平板K与剖面L2<2%、旧几何K相对差≤1e−4是首批新协议检查，不是当前已通过结果。

本轮无正式稳态计算、无新模型拟合或预测结果、无Gate升级/投稿/对外通信。开发/预测/大网格正式计算均未启动；历史FAIL、旧来源缺口和submission_ready=false保持。
