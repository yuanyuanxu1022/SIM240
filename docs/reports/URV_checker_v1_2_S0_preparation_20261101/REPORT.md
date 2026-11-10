# URV v1.2：R1/R2 修订及 S0 两条回归执行准备

2026-11-01。用户授权：在隔离新版本中最小修订R1/R2并验证，通过后准备S0两条h75回归的正式执行绑定，保持不自动启动。

**R1/R2已修订并通过本轮软件验证，S0具体输入、可推进程序与外层运行器已准备并封存。S0正式计算未启动，启动许可保持关闭。** 这是AI参与的本地软件/协议自审，使用peer-review的范围、证据和复现核对方法；不是独立人工验收、正式期刊同行评审或新的物理验证。

## 交付入口与隔离

- [v1.2检查器](../../../CASE/unseen_v2_reference_checker_v1_2/README.md)：仅修路径声明解析和编译宏识别，保留v1.1。
- [S0专用准备包](../../../CASE/unseen_v2_reference_S0_v1_2/README.md)：另目录构建，未触动原准备程序。
- [S0固定绑定](../../../CASE/unseen_v2_reference_S0_v1_2/evidence/S0_prepared_binding.json)及同目录SHA：1568项输入。
- [逐项验证记录](verification.json)、[只读及未授权执行拦截检查](binding_guard_verification.json)。

新物理源码urv_reference.cpp、mass_stats.h均与原准备版逐字节相同。唯一native构建配方变化为-DURV_PREPARATION_ONLY=1改为0，见[native_Makefile.diff](native_Makefile.diff)。这个新二进制具备时间推进能力；外层正式启动授权与实际求解另行控制。原准备版仍为1，原封存保持。

## R1：完整解析后才允许写分析目录

原release_inputs中任一声明缺字段会返回空列表，丢掉其他已知保护路径。v1.2要求JSON为对象、输入清单/运行列表/回归映射类型正确、每条必要路径完整且为非空合法字符串。任一解析或结构错误立即抛出拒绝，单条和批次在mkdir/save之前停止，不再回退为空保护集合。

新增测试保留有效P基准，同时让另一运行缺output_directory；单条和24条人工批次均退出2，基准子目录未创建，原标记字节保持。也核缺回归路径、错误容器、空路径和不存在合同。完整路径集合原样保留。反例均为人工材料，未写真实结果。

## R2：合并与分离的宏选项统一识别

v1.2将-DURV_PREPARATION_ONLY=0与-D URV_PREPARATION_ONLY=0归一处理，要求目标宏恰好一次、明确为0。合并/分离的冲突值、重复0、取消定义、无值、缺参数以及同名函数式宏均拒绝；其他前缀名称不能冒充目标宏。捕获的原命令文本仍完整保留。

人工完整合同的正反例调用实际binding函数，未编译人工占位文件。另有本轮真实S0构建及4次零步运行的execution_audit，确认实际程序preparation_only_build=0且collide_and_stream_calls=0；没有把旧文本探针误称为实际编译。

## 测试和首次失败

[checker_tests_final.log](checker_tests_final.log)：77项测试通过，原70项与新增7项测试方法（包含多个子用例）。首次[checker_tests_initial.log](checker_tests_initial.log)保留3项失败：旧测试故意使用不存在的合同，R1新规则使它们在目标内部失败条件之前退出。仅把4个相关测试用的“缺失合同”改为明确人工路径声明，继续测试原失败条件；没有放松数值断言。首轮F02包装测试同时已作该适配，另3项在日志失败后适配。

[runner_tests.log](runner_tests.log)：6项人工流程测试通过，覆盖native失败、超时、来源变化、独立检查失败、两条成功后不进入S1，以及缺独立启动授权时不创建启动标记。人工进程回执/授权布尔只在临时测试目录，未调用真实native或场求解器，不是用户授权或流场结果。

check_results.py、evidence.py、read_fields.py与common/全部保留v1.1原字节，见[unchanged_numerics_and_syntax.json](unchanged_numerics_and_syntax.json)。F02先保存全部差异再停止、全部物理门槛、方向/平均/质量/GCI/V2规则不变。F04多合同汇总仍未修，留在后续阶段汇总前单独处理。

## 真实编译和零步边界核对

实际make单路编译退出0；[构建记录](../../../CASE/unseen_v2_reference_S0_v1_2/evidence/build_environment.json)捕获真实编译/链接命令、g++/MPI wrapper、OpenLB HEAD、1390项编译器报告依赖、3项实际链接静态库和15项解析运行库。依赖.d是编译器-MMD输出的项目依赖，不声称捕获了全部系统头或提供可移植构建镜像。

OpenLB HEAD为882924a9cfc8dcdf82909e39530789cb6f5ebcc4；二进制SHA：`a9fe019114558653d3eb95eda7350786766ea41c50485f69cfa0a822cdc8b6a1`。这属于本轮真实构建，不能补证历史缺失环境。

[零步审计](../../../CASE/unseen_v2_reference_S0_v1_2/audits/URV_S0_ZERO_20261101_01/verification.json)：P/T各describe与precheck，共4次native调用；所有独立退出0，实际推进0步。几何独立复核为57600流体核心节点、32448条壁面连接、q=.5、无fallback/unresolved；窗1013，上限58800，dt=4.166666666666667e-12s。本轮没有initialize或实际场读取；原24项初始化审计保留在旧包，仅作为既有准备证据。四次零步不能代替正式收敛、质量或稳态场验收。

## S0输入与停止规则

| 项目 | 沿槽P | 横槽T |
|---|---|---|
| 固定后续run_id | URV_S0_P_v1_2_20261101_01 | URV_S0_T_v1_2_20261101_01 |
| 矩阵case_id | URV1_H75_P_dx5_a100000 | URV1_H75_T_dx5_a100000 |
| 主驱动轴 | +y | +x |
| 旧基准K（m³） | 9.834076003216204e-23 | 4.449022023188299e-23 |
| 旧完整诊断行 | 4343 | 2954 |

共同h75/d100/w120/P=Ly240nm、dx5nm、H125nm；a1e5m/s²、nu1e-6m²/s、rho1000kg/m³、tau1。J是流体速度体积分/平面面积（m²/s），K=nu J/a（m³），U=J/H。S0是已知h75的统计移植回归，不是新条件泛化测试。

每条K对旧同方向变化≤1e-4，保存全部20共同诊断列和全轨迹差值；未解释变化即HOLD，不另加容差。旧raw RESULT_PASS=false与旧独立foundation接受分别保留。数值/几何/出口/来源/全场证据仍须按原协议独立验收。

外层run_S0.py默认只读；未来生效合同允许执行时，逐条保存外层真实进程退出、完整日志、前后输入清单、全部原始文件/VTK引用哈希；每条完成后独立检查。第一条失败、超时、来源变化或检查失败就停止，不自动启动第二条、不重试、不进入S1。单进程/线程/cuboid、overlap3，8GiB地址空间、每条求解3600s，启动前RAM≥12GiB/首批磁盘≥100GiB，每条前磁盘≥8GiB；本轮资源快照不是未来运行时保证。

## 绑定、授权与当前停点

绑定SHA：`a836c5f4368ed5d80d1a585abde3a353848d4555094ba2556b14fd3d883cb846`。两份run_config.txt与run_manifest.txt已写到固定目录；目录仅有这两个输入，没有run.log、result、completion或正式时间推进。

本次已交付具体、完整的**执行输入绑定**，其kind为PREPARED_EXECUTION_BINDING_NOT_LAUNCH_RELEASE。prepared_run_ids固定后续身份；approved_run_ids=[]、approved_runs=[]、simulation_authorized=false、S0_started=false。真实程序/配置/资源已绑定，启动许可仍关闭。身份完整性用不落盘的结构投影检查，不把投影冒充生效合同或真实授权。

当前绑定在只读入口退出0；给同一绑定加--execute作拒绝验证时退出2，在native调用和启动标记创建之前拒绝，新包73文件前后保持。检查日志中沿用的“zero-step preparation only”是旧统一拒绝文案，表示授权关闭；不是在声称新二进制仍为准备宏1。

获得真实启动许可后，另存launch合同：基于该准备绑定SHA，逐条核配置/输入/资源，明确实际用户指令，将获准列表与prepared记录精确对应，单独封存合同SHA并交付一条tmux命令。不得改写当前准备封存来伪造批准；本轮不交付会被当前合同拒绝的启动命令，也不调用tmux。

作者未使用确认已真实收到并绑定：两候选结果未用于选V2系数或检验条件；核查位置未提供、未独立审计，不扩大为从未见过数据/外部数据不存在。原PENDING快照保留。

[保护核查](verification.json)确认本轮2410项保护文件不变；另重新核对旧2606项审查保护清单与1686项历史清单全部匹配，集合有交集不相加。原准备seal及1432绑定、v1.1 seal及21绑定保持。

新正式NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、reference_qualified=false、physical_validation=NOT_EVALUATED、submission_ready=false。本轮零步几何通过不替代正式run的geometry_PASS。原细T FAIL、旧D4预测HOLD、C/h75限定资格、V2冻结及其他旧科学状态保持。新URV完整稳态端到端验收仍待真实结果。未提交推送或对外发送项目材料。
