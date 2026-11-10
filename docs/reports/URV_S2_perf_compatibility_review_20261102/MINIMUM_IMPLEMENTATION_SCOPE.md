# S2 性能标定最小实现范围（待采用；本轮未实施）

本范围具体落实已采用 S2-MIP-v1-PERF，不更改它的候选、预算、物理或科学门槛。此文是实施边界，不是新的执行许可。

## 1. 目录和文件

建议未来新建 `CASE/unseen_v2_reference_S2_perf_v1/`，所有新输出位于其 `performance_runs/<包含PERF的新编号>/steady/`。这是协议所说“隔离S2树”的具体路径；当前不创建该 CASE。旧 S2/检查器、S1、S0 和其他 CASE 全部只读。不得添加文件到冻结检查器 analysis/common，不复制并放松正式阶段白名单。

| 建议新增文件 | 单一职责 | 明确边界 |
|---|---|---|
| scripts/prepare_perf.py | 从 B 两条细网格配置派生新身份，收集新代码/配置/依赖与 B，生成性能准备封存 | 无子进程调用；默认所有执行许可 false，approved/actual 空；不生成正式授权 |
| analysis/perf_contract.py | 验证原 B 和独立零步接受；验证性能准备/将来授权 release、固定候选/来源/资源/输出隔离 | 对原 B 调原 verify_seal/verify_zero_receipt；新性能 release 不传原 verify_provenance 的正式阶段分派 |
| scripts/run_perf.py | 默认只读预检；未来在真实性能授权下，顺序 P→T，自动观察、停止、记录收据 | 仅两个原 steady 调用；无重试/延长/续跑/正式入口；P 证据不足或异常即 HOLD，不运行 T |
| analysis/check_perf.py | 不导入运行控制器；从绑定、原始轨迹、观察记录和真实进程收据独立复算性能判定 | 不启动原生程序/VTK读取器，不调用正式稳态验收，不判模型精度 |

另加必要 `tests/test_perf.py`、README、配置/绑定证据；监测循环留在 run_perf 内，不为本任务抽象通用框架。文件名在实施封存时固定，职责/权限不可变。测试为软件模拟，不是原生零步或性能运行；不生成 C++ 源码、Makefile 或新二进制。

## 2. 配置与绑定

1. 原 B 固定绝对路径、SHA `2e55f3369f9445e7763ee1f9a87c57f79348d1b332c959bc038c1bcc4739081f`；原 ELF 固定 SHA `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`。检查 B 的1816项输入、原零步收据以及 B 中独立接受文件的路径/SHA、18条/6帧计数和两项true。仅原 verify_zero_receipt 不足以代替独立接受引用检查。
2. 两候选限定为 `URV1_U_REG_P_dx1p25_a100000` 和 `URV1_U_REG_T_dx1p25_a100000`，顺序 P→T。与 [fine_config_review.json](fine_config_review.json) 中各自原 run_config 逐键比较，**只允许 run_id 和 output_directory 改变**；mode仍steady，所有物理、窗、最大时间与帧字符串保持。新 PERF 编号不得占用正式 approved_run_ids 或原矩阵验收映射；可只读记录 source_planned_case_id 作为来源。
3. 新准备封存建议 kind=`S2_PERF_PREPARATION_NOT_AUTHORIZATION`，stage=`S2_PERFORMANCE_ONLY`，protocol=`S2-MIP-v1-PERF`；列两条 prepared_benchmark 记录，approved_benchmark/actual 空，native_zero_step/performance_time_stepping/formal_simulation_authorized 均 false。stage 是独立工程用途，不添加到 URV-v1 的六阶段科学矩阵。
4. 绑定输入取 B.inputs 的完整超集，加 B 本身及其固定 SHA、新性能代码/软件检查/文档/两配置/manifest、选定解释器/环境来源。将来执行 release 再加准备封存及真实授权证据。闭包不反向加入 B，B 不回写；避免准备、授权、收据相互引用成哈希循环。审核文档与随后采用记录应纳入新准备闭包。
5. 将来有明确性能推进授权时另存 kind=`AUTHORIZED_PERFORMANCE_RELEASE`、purpose=`S2_PERFORMANCE_NOT_REFERENCE`；只在此 release 中置 performance_time_stepping_authorized=true、列两条批准性能编号；formal_simulation_authorized=false、approved_formal_run_ids=[]，AI_may_start_native=false，用户手动启动。真实原话/交互问答来源如实保存；旧零步授权和本轮“审核”都不能作为替代。
6. 默认只读入口不能创建启动尝试/输出运行痕迹，拒绝无 --execute、无外部固定 SHA 或许可不足的调用。执行前同时检查路径祖先/符号链接/同编号占用/已有输出/并发锁，拒绝续跑和覆盖；有效合同也不能自动开启下一阶段。当前不准备执行合同或命令。

## 3. 监测、停止和证据

固定1进程、1线程、1 cuboid、overlap3，原 RLIMIT_AS=8 GiB；MemAvailable≥12 GiB、批次初始磁盘≥100 GiB/每条前≥8 GiB、每条输出≤4 GiB。未来自动观察记录 RSS、MemAvailable、输出/空闲磁盘，并按原资源边界停止；RSS观察峰值不能称操作系统全程精确峰值。不得在测得不足后降低门槛、删历史结果或自动换机器。

起止以 monotonic 为准，同时记录可读实际时间；每秒最多一次样本。用增量读取诊断文件，不重扫整份CSV，不改变C++缓冲。样本保存序号/实际时间、进程存活、最新完整step、文件字节偏移、RSS/可用内存/输出字节/空闲磁盘；完整文件的尾部残行原样保留并记录长度/位置/哈希，不删除或猜补。

壁钟截止独立于新增诊断行，不能等下一行或重哈希结束后才执行停止。单条启动起1800秒或已见完整step≥2048先到停止；来源/资源/非有限/原安全守卫异常优先停止。SIGTERM→最多10秒→必要时SIGKILL覆盖进程组，保留实际信号/退出码/超时标志/停止决定及退出时刻。所有重输入哈希放在启动前与子进程退出后；采样中保持轻量，记录实际采样间隔，不能声称严格均匀时间或掩盖监测开销。

原生 effective_config 的 formal_simulation=true 保持；父收据记录性能用途及正式授权false。原生 result、execution_audit、最终帧缺失就列缺失，不人工补齐原生文件。停止时观察到的末步与退出后文件末个完整步分别保存；后者不能倒填进先前采样时刻。无原生精确计数时 actual_collide_and_stream_calls=null，仅报 last_complete_step 下界。

保存主机/CPU、操作系统、解释器绝对路径/版本、环境与线程设置、运行前后来源/动态库哈希及已有构建环境。当前已核对可用的解释器为 `/home/dell/miniconda3/bin/python3`；未来实施需固定实际使用版本和依赖，而不能只写泛指 python3。不得为测速自动安装依赖、切换编译选项或修改机器配置。

P 的子进程退出后先封存原始输出、前后来源哈希及父收据，再运行独立 check_perf；只有 PERF_EVIDENCE_SUFFICIENT、停止可解释且无异常，才允许在同一已授权批次执行 T。所有异常/证据不足/用户停止都保持 HOLD，无自动补测；若 T 未执行明确写 NOT_EXECUTED。原生意外 exit0/完整末态必须 HOLD 解释，不能作为正常短测放行；原窗首个完整窗口至少step10367，目标2048前不应正常收敛。

## 4. 独立检查与判读

独立检查应从真实观察样本重新选择区间：首次观测step≥256/1024分别为起点，此后首次step≥起点+512为终点。真实 Δstep/Δmonotonic 必须正有限；允许重叠并标明。记录每个区间步/秒、秒/步及精度限制。突发落盘导致窗口缺失就判不足；不以退出后刷出的行制造带时间戳的区间。≥2048是观察目标，不承诺实际步数硬上限。

对所有已保存完整诊断行核25列、从step0起连续顺序、原 time_s=step·dt、finite=1、正质量/有限值/方向投影。依原 acceptance_spec 和 check_results 的运算重新计算 legacy/corrected/delta_mass_error 及账本一致性，容差和界限原样复用：corrected质量相对误差<1e-10、账本差≤1e-13、密度偏离≤1e-6、Mach<0.05，Re_H≤0.01；保留旧质量误差，不拿它替换修正质量门。复算 Re_H 仍按原检查器用 h+d（此几何为140 nm）计算，不能和通量平均中的H=h+d/2混用。以现有 exact_parameters 和原初始节点数2949120作单位依据；复算原函数无副作用时可只读引用，避免模块名覆盖。

原稳态std/span/cross列在前10367行的-1是未就绪占位，可合法出现；短测不要求完整窗口、最终截面一致/收敛或K准确度，也不伪造它们通过。所有保存行中安全异常均阻止 T；最后一行良好不能掩盖之前异常。几何证据只引用已有零步接受，正式 geometry_PASS 不升级。

判定限定 PERF_EVIDENCE_SUFFICIENT / PERF_EVIDENCE_INSUFFICIENT / PERF_ABORTED_UNEXPECTED；两方向分别出结论。计划SIGTERM/超时但证据充足可属第一种，仍保留真实超时/非零退出；非计划exit0、来源变化、资源或安全失败不得用“测速完成”掩盖。科学字段固定 NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、REFERENCE_QUALIFIED_FOR_CASE=false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED、submission_ready=false。

仅能按慢区间给“若走满602112步”的有条件成本，另列初始化/输出及完整10368步统计窗成本未覆盖；不能据此保证12小时内收敛。性能目录无 checkpoint/resume，数据不续跑、拼接、进入GCI/参考或模型误差比较；正式计算另起初态/编号/目录及授权。

## 5. 实施阶段的软件检查与停点

实施可用合成轨迹、假时钟及模拟子进程检查以下真实风险；不调用原生程序或VTK读取器，不用真实时间推进验证控制器：

- 真实 B 和同一 ELF 路径合法；错 B SHA、来源漂移、漏独立接受、错阶段/额外case/错方向/非1.25网格/非允许配置变化均拒绝。
- 零步/正式/准备合同不可当性能许可；默认只读无 Popen/启动标记；二次执行/并发/符号链接/正式输出目录均拒绝。
- 原100/8/4/12/8 GiB边界和1800/2048/10秒边界不串到正式43200秒；输入哈希不进入计时内循环。
- 模拟无行/逐行/成批落盘、合法-1、半行、无step0/缺行/非有限值/账本错误、时间不增；真实端点≥起点+512和重叠区间正确；不以末次好行覆盖早期坏行。
- 模拟目标步/墙钟/资源/用户停止/意外退出/TERM无响应→KILL，记录真实原因与退出；P不足/异常严格不进入T，不重试/加时/转正式。
- checker从原始样本独立复算，篡改区间/父结论/哈希被拒绝；尾行保留；退出后刷行不倒填样本；精确次数缺失保持null，RSS只称观察峰值。

通过后只交付关闭授权的性能准备封存和软件检查报告，旧3072项保护范围逐项复核。**本范围不包含编译、重复原生零步、真实性能推进、正式流场计算、命令交付或研究Gate升级。** 若后续授权已明确覆盖某步骤，沿用其覆盖范围，不重复索取；无覆盖步骤保持未执行。
