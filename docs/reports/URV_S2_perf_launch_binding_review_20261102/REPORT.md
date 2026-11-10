# S2 两条有限性能推进：启动绑定前只读核查

日期：2026-11-02。用户本轮要求“获得明确覆盖两条有限性能推进的授权后，复核封存与届时资源，生成独立执行绑定并交付一条命令，由用户手动启动；正式计算仍另行授权。”这是条件表述；目前没有把它记作已获得性能推进许可。

本轮已完成可独立进行的来源、配置、资源、启动痕迹及环境核查，并形成非执行绑定方案。使用scientific-writing组织证据。当前等待明确授权；未签发真实性能执行release、未生成启动命令、未调用求解器或推进时间。

## 1. 具体待授权对象

只限既有两条预留身份：`URV_S2_PERF_P_dx1p25_v1_20261102_01`（沿槽+y），随后 `URV_S2_PERF_T_dx1p25_v1_20261102_01`（横槽+x）。h/d/w/period/Ly=60/80/120/240/240 nm，dx1.25 nm，2949120核心节点；原mode=steady、窗10368步、最大602112步和帧计划保持。

每方向启动起1800秒或首次观察完整诊断step≥2048，先到停止；SIGTERM后最多10秒再必要时SIGKILL。2048为落盘观察目标，非实际调用硬上限。P证据不足/异常即HOLD不进入T，不自动重试/延长/续跑。性能数据不进入正式参考/GCI/V2误差表。正式S2和S3均不包含在拟授权中，正式43200秒上限不改。

## 2. 17:40 +0800 只读核查结果

- 准备封存 `CASE/unseen_v2_reference_S2_perf_v1/evidence/preparation_perf.json`，SHA `806c40a62620396faf6795008a81b25f7f9bf4182869b6df4422b575b2b08030`，2055项输入重核对一致；原B及同一ELF绑定通过。
- 两输出目录均仅config/manifest；未有performance_attempt.json、performance_execution.lock或performance_batch_result.json；未发现相关原生/性能进程或相应tmux会话。
- 可用内存22033121280 bytes（20.51994 GiB）≥12 GiB，磁盘341449019392 bytes（317.99918 GiB）≥整批初始100 GiB。是当前快照，不保证未来资源；签发真实release及实际启动时仍须复核。
- tmux可用。完整机器记录见 precheck.json；本轮没有重跑49项既有软件检查，也没有重做原生零步或场读取。

## 3. 启动环境问题及范围内处理

首次只读核查调用原控制器environment()时被既有守卫拒绝：当前终端有非空LD_LIBRARY_PATH，内容是OpenFOAM相关搜索路径，LD_PRELOAD未设置。未深入审核这些变量来自哪份shell初始化文件，不把路径内容当成来源文件证明。

随后只在本次只读命令进程使用 `env -u LD_LIBRARY_PATH -u LD_PRELOAD`，没有修改全局变量、shell文件、代码或封存。干净环境下inspect、environment和资源守卫均通过。用ldd只读解析原二进制得到15个动态库，其实际路径集合和逐项SHA与原build_environment完全一致；没有执行求解器main。见 ldd_clean.txt、loader_environment_review.json。

未来命令应明确携带同样的单进程环境前缀，并在真实绑定时重新检查。该处理遵守既有“拒绝未绑定loader覆盖”的守卫，没有放宽门槛或出现新的来源矛盾；本轮未重编译或改任何检查器。

## 4. 非执行方案与真实授权缺口

release_plan.json 为 `NON_EXECUTABLE_PERFORMANCE_RELEASE_PLAN_NOT_AUTHORIZATION`，所有许可false，approved/actual空。它只列出未来release/授权证据的候选路径和两条prepared配置，不是可执行合同。

未来真实release的基础闭包计划为2058项：原2055项+准备文件本身+准备SHA旁文件+真实授权证据；如果另绑定届时前置证据，实际项数按新合同如实记。kind应为AUTHORIZED_PERFORMANCE_RELEASE、purpose=S2_PERFORMANCE_NOT_REFERENCE；只有performance_time_stepping_authorized=true，formal_simulation_authorized=false、AI_may_start_native=false，用户手动启动。原准备封存不回写。

根据原PERFORMANCE_PROTOCOL.md第1节“实际执行必须另有明确覆盖‘两条有限性能时间推进’的授权”，已单独询问是否现在授权这两条、仅生成合同和命令由用户手动启动，并明确不含正式S2。**当前未收到答案，不能生成真实授权记录或开启执行许可。** 若收到交互回答，须同存完整问题和实际选项答复，标明reply_to_async_question，不伪称手写整句。

## 5. 停点

仅新增本核查目录并维护共享状态/交接；原封存/源码/检查器/结果不改。NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、REFERENCE_QUALIFIED_FOR_CASE=false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED；reference_qualified/strict_error_bound_established/submission_ready=false，原历史FAIL、S0/S1接受和F04 OPEN等保持。

下一步为收到明确授权后重新核对资源/封存、另存真实授权与独立release、只读验证后交付一条绑定命令，由用户手动启动。当前无构建、求解器/VTK读取器调用、时间推进、自动重跑、下一阶段、Git提交推送或项目资料外发。
