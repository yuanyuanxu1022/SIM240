# S2 性能接入实现与关闭权限准备封存

日期：2026-11-02。用户采用原最小范围并授权隔离实现与软件检查，明确性能推进及正式计算仍另行授权。采用记录见 adoption.json；原范围为 `docs/reports/URV_S2_perf_compatibility_review_20261102/MINIMUM_IMPLEMENTATION_SCOPE.md`，协议仍为 S2-MIP-v1-PERF / URV-v1 / MRP / A1。

**本轮已实现四项性能接入职责，49项软件检查通过，并生成执行权限关闭的准备封存。没有构建、原生调用、原生零步重跑、场读取器调用或时间推进。** 该封存不能启动性能计算，也不授权正式 S2。

## 1. 实现与物理边界

新增 CASE：`CASE/unseen_v2_reference_S2_perf_v1/`。旧 S2、冻结检查器及其他 CASE 未修改。复用同一 S1 二进制 SHA `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`，没有新 C++ / Makefile / build。

| 文件 | 实现职责 |
|---|---|
| scripts/prepare_perf.py | 只读核对 B、派生两条配置、捕获解释器/已加载模块及映射库，生成关闭权限准备封存；无子进程调用 |
| analysis/perf_contract.py | 原 B 调原验证函数；性能封存/未来release另行验证，不扩原科学矩阵、不回写 B；限制两候选、预算、配置差异及授权 |
| scripts/run_perf.py | 默认只读；执行分支必须真实性能release。自动观测、停止、保留真实退出/残行/缺失计数；P独立检查不足/异常即停，不继续T |
| analysis/check_perf.py | 不导入控制器；从原始CSV、真实观察样本及进程收据重新检查安全指标/区间/信号/来源，输出性能状态，不计算模型精度 |
| tests/test_perf.py | 假时钟、假进程及合成诊断的软件检查；测试期间所有真实 subprocess.Popen 均禁止 |

两条已准备身份为 `URV_S2_PERF_P_dx1p25_v1_20261102_01`、`URV_S2_PERF_T_dx1p25_v1_20261102_01`，对应沿槽+y、横槽+x，顺序 P→T。它们是预留身份，actual_benchmark_run_ids 为空。各目录目前仅有 run_config.txt / run_manifest.txt。

两配置从 B 的相应1.25 nm正式配置复制，逐键只改 run_id/output_directory。h/d/w/period/Ly=60/80/120/240/240 nm，rho1000 kg/m³、nu1e-6 m²/s、a1e5 m/s²、tau1，2949120核心节点。mode仍steady；10368步统计窗、602112最大步、原帧计划均保持。J=Σ(u_phys dx³)/平面面积，K=nu·J/a、单位m³；短段不据瞬态J评稳态K。

未来原生 formal_simulation=true 原字节保留；父合同的正式许可始终false。单条性能预算仍为启动起1800秒或首次观察完整诊断step≥2048先到停止，SIGTERM后最多10秒再必要时SIGKILL；正式细网格43200秒不改。每秒最多一次记录真实monotonic时间、完整字节前缀SHA/步数、RSS/可用内存/磁盘/输出。原资源1进程/1线程/1cuboid、overlap3、8 GiB地址空间、MemAvailable≥12 GiB、初始磁盘100 GiB/每条8 GiB、输出4 GiB不变。

## 2. 已完成的软件检查

软件结果 `software_checks.json`、`software_tests.log`：**49项通过，退出0**。另有5个Python文件AST语法核对；只有控制器的显式执行分支有一个Popen位置。没有生成Python缓存或新原生构建文件。

检查覆盖：准备/零步/正式许可不能作为性能许可；错阶段/候选/身份/额外case/原配置变化/输出重用/符号链接拒绝；假时钟下2048观察目标和1800秒独立截止、10秒TERM/KILL、用户停止、资源异常及P不足后不进入T；模拟同批次再次执行被拒绝。诊断检查覆盖25列/step0/连续性/单位、方向投影、所有完整行的质量重算和密度/Mach/Re守卫、合法-1占位、未换行尾部、成批落盘、真实起点后至少512步、两区间重叠、退出后行不倒填时间、原始前缀/文件篡改拒绝。

完整合成文件→父收据→独立检查器的软件路径通过，保留残行并把缺失精确计数保持null；它不是原生性能证据。另用真实B只读核对其1816项来源和独立接受文件；没有重做历史18次原生零步/6次场读取。

开发期失败保留在 software_tests_attempt_02.log / software_tests_attempt_03.log：前者1错误/1失败，后者1错误。分别为平台信息函数可能调用uname外部命令、模拟墙钟停止收据时刻不一致、模拟环境未提供线程键。已改为os.uname直接读取，并修正软件夹具；最终49项全过。这些是本轮软件检查记录，原横槽历史FAIL和原科学门槛没有被替换或抹除。

## 3. 准备封存与实际入口核对

准备文件 `CASE/unseen_v2_reference_S2_perf_v1/evidence/preparation_perf.json`：

- SHA256：`806c40a62620396faf6795008a81b25f7f9bf4182869b6df4422b575b2b08030`；2055项绑定输入。
- kind=`S2_PERF_PREPARATION_NOT_AUTHORIZATION`、stage=`S2_PERFORMANCE_ONLY`、purpose=`S2_PERFORMANCE_NOT_REFERENCE`；不加入URV的24项正式矩阵。
- B的1816项为完整子集，另绑定B文件本身、采用/审核材料、新代码/测试、两配置/清单、软件检查结果和解释器/运行依赖。B SHA仍 `2e55f3369f9445e7763ee1f9a87c57f79348d1b332c959bc038c1bcc4739081f`。
- performance_time_stepping_authorized/formal_simulation_authorized/simulation_authorized/native_zero_step_authorized均false，所有approved和actual列表空；AI_may_start_native=false，user_manually_starts=true。
- 默认入口实际只读核对退出0，输出PREPARATION_BINDING_CHECK=true、solver_executed=false。用同一真实准备封存请求执行时被明确拒绝：`preparation/zero/formal authority cannot launch performance`；真实Popen被测试保护，调用数0；未创建启动/锁/批次记录。证据 preparation_readonly.stdout.txt、closed_seal_checks.json。

解释器为 `/home/dell/miniconda3/bin/python3` 的实际可执行文件及版本，详见 evidence/runtime_environment.json；没有安装依赖或更改编译/机器配置。来源与动态库在未来实际子进程前后重核对；不在一秒观测循环内重哈希整个闭包。

## 4. 保留的限制

控制器的实际原生推进、真实进程信号清理、原生缓冲/IO表现及实际资源峰值尚未实测；软件假进程检查不能代替这些证据。未来没有两个完整测速区间就判不足，不自动重试/加时或继续T。原生意外正常退出/完整末态、来源/资源/安全异常均HOLD。

2048是已落盘观测目标，不是实际推进硬上限。观察端点是读到完整记录的时间，不能当成逐步精确时间戳。信号终止可能没有原生execution_audit/末态；精确调用数缺失时填null，完整step仅为下界。RSS只称观察峰值；短段尚未覆盖10368步完整窗成本，不保证12小时内完成或收敛。数据不得续跑、拼接、进入正式参考/GCI/V2误差表。

## 5. 科学状态、保护与停点

NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、正式geometry_PASS=null、REFERENCE_QUALIFIED_FOR_CASE=false；MODEL_COMPARISON/physical_validation=NOT_EVALUATED；reference_qualified/strict_error_bound_established/submission_ready=false。S0/S1接受事实、原横槽FAIL/380差异、早期MRP静态FAIL、HISTORICAL_EXCLUSIVE_ATTRIBUTION=NOT_ESTABLISHED、D4预测HOLD、F04 OPEN及外部声明原范围均保持。正式24项仍完成4/剩20。

3086项受保护旧文件结束逐项复核无漂移；准备的2055项闭包重核对一致。共享当前状态和最新交接只更新当前首节、历史尾部字节保留。结束证据见 verification.json、report_manifest.json。此报告/结束核对不反向加入已封存输入，以免哈希循环。

**当前没有真实性能授权、性能执行release或启动命令；没有启动性能或正式计算。** 下一动作是在明确授权覆盖两条有限性能推进后，另做封存与届时资源复核，生成带真实授权的独立release和外部SHA，再交付单条命令由用户手动启动；授权与命令交付是后续任务，本轮不自动执行。

本报告按scientific-writing组织可复核证据，为AI辅助软件准备记录，不是独立人工数值/物理接受；无项目材料外发，无Git提交推送，无记忆文件写入。
