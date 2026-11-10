# S2-MIP-v1-PERF 与 B 封存的独立兼容性审核

日期：2026-11-02。范围：用户要求单独审核兼容性并明确性能标定的最小实现范围；本轮只读复核和形成文档，不实现性能程序，不构建、不调用原生程序、不读取新流场、不启动性能推进或正式计算。使用 scientific-writing 的证据约束报告方法；此记录是 AI 辅助工程审核，不是独立人工物理验证。

## 1. 结论

**B 可原样作为 S2-MIP-v1-PERF 的只读前置证据；现有正式/零步执行入口不能直接充当性能入口。最小实施应新增独立的性能绑定、控制器和结果检查层，复用原 S1 二进制，不修改 B、原生源码或冻结科学检查器。**

这不是性能运行放行。B 自身的所有执行许可继续关闭；性能推进必须另有明确覆盖两条有限时间推进的真实授权。当前没有性能执行合同、批准或实际性能编号，也没有启动命令。最小实现范围见 [MINIMUM_IMPLEMENTATION_SCOPE.md](MINIMUM_IMPLEMENTATION_SCOPE.md)，机器可读设计见 [minimum_scope.json](minimum_scope.json)。

## 2. 本轮实际证据

复核入口为 [audit_existing.py](audit_existing.py)，输出 [B_compatibility_audit.json](B_compatibility_audit.json)、[fine_config_review.json](fine_config_review.json)、[reviewed_inputs_sha256.json](reviewed_inputs_sha256.json)。脚本只写本报告目录；没有子进程启动或求解器调用。

| 核对项 | 实际结果 | 可以得出的结论 |
|---|---|---|
| B 外部固定 SHA | `2e55f3369f9445e7763ee1f9a87c57f79348d1b332c959bc038c1bcc4739081f`，1816 项输入重哈希一致 | B 未漂移 |
| 原 `verify_seal(B)` / `verify_zero_receipt(B)` | 均通过；独立验收文件的 SHA 和 B 内覆盖一致 | 原来源闭包及六配置零步前置证据可引用 |
| 原零步独立复核记录 | 18 条原生零步、6 帧独立重读、0 推进；接受标志均 true | 已有零步接受事实保持；本轮没有重跑这18条或重读这6帧 |
| ELF | `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b` | 与原 S1 / S2 零步为同一文件，可按现范围复用 |
| 性能协议 | Markdown/JSON 已在 B 绑定；JSON 的两条候选与 B 的细网格配置相同 | 物理与配置定义兼容 |
| 正式目录 | 六条均仅有 run_config.txt / run_manifest.txt | 这些正式输出目录尚未用于计算 |
| 新执行痕迹 | 原 S2 无 launch_attempts / performance_runs；建议的独立性能 CASE 不存在 | 此次未建立或启动性能/正式任务 |
| 保护范围 | 原保护3036项先复核一致，再扩展为3072项本轮前快照；结束逐项复核见 verification.json | 不回写旧准备、二进制、检查器、审计结果或 B |

B 的路径：`CASE/unseen_v2_reference_S2_reuse_v1/evidence/preparation_B.json`，kind=`S2_PREPARATION_B_NOT_AUTHORIZATION`；simulation_authorized、native_zero_step_authorized、performance_time_stepping_authorized 均 false，approved 列表空。其 actual_audit_run_ids 是18条历史零步调用，不能变成性能许可。

两条候选固定 h/d/w/period/Ly=60/80/120/240/240 nm，P=沿槽+y、T=横槽+x；dx=1.25 nm，2949120 个核心流体节点、490752 条壁面链。rho=1000 kg/m³、nu=1e-6 m²/s、mu=0.001 Pa·s、a=1e5 m/s²、tau=1；H=h+d/2=100 nm，局部间隙为60/140 nm。平均定义仍为 J=Σ(u_phys dx³)/平面面积，K=nu·J/a，K 单位 m³。性能标定不据瞬态 J 评价稳态 K。

## 3. 必须单独接入的具体原因

| 接口 | 现有实现证据 | 最小处理 |
|---|---|---|
| 阶段与身份 | `analysis/stage_s2.py:validate_records` 精确要求 S2_REG_GRID、六条原编号、原目录和1/4/12小时预算；`revision_s2_reuse.py` 也调用它 | 用原函数验证原 B；新性能 release 由独立验证器验证，不送入原正式阶段分派 |
| 检查器输入闭包 | `analysis/contracts.py:165` 起枚举冻结 analysis/common 的直接文件，要求均在绑定中 | 在这些目录新增 PERF 文件也会使 B 覆盖不全；新层放在另一个隔离 CASE，不扩展原输入集合或改 B |
| 运行与退出 | `scripts/run_S2.py:native_process` 最多5秒等待，无逐次进度/RSS观测；execute 要求 exit0、正式末态及原 RESULT_PASS 才继续 | 独立约1秒观测和主动停止路径；保留真实信号/非零退出，通过独立性能检查后才考虑 T |
| 零步入口 | `audit_S2_zero.py` 只接受 describe/precheck/initialize | 不借用零步授权，也不增加新的零步调用来伪装性能推进 |
| 原生模式 | `urv_reference.cpp` 只接收四种模式；steady 的 effective_config 会写 formal_simulation=true | 原字节保留；父合同把用途限定为性能诊断，不更改原生标志或源码 |
| CSV 时序 | diagnostics 每行写换行，但没有逐行 flush；统计窗满前以 -1 表示三列窗指标未就绪 | 使用实际完整行的观测时刻；接受合法 -1 占位，不把未收敛短段当成数值失败或成功 |

上述是已采用协议预见的接入差别；没有发现需要改变物理/门槛、重编译或推翻 B 的新证据矛盾。历史限定指令审计只沿用到这份完全相同的 ELF，不声称新做完整机器指令审计。若后续发现源码/库/ELF变化或协议矛盾，应停止并按用户既定规则交 GPT-6 Astra｜High 裁定，不能以本报告覆盖。

## 4. 性能证据的适用边界

单方向沿用原窗10368步、最大602112步、完整帧计划；父控制器预算是启动起1800秒或首次观察到完整诊断 step≥2048，先到即 SIGTERM，最多10秒清理后必要时 SIGKILL。1800秒是发起停止的预算；信号清理和收据整理另记，不能声称进程严格在1800.000秒前消失。正式细网格43200秒上限保持。

两个吞吐量区间分别以首次观察到 step≥256 / step≥1024 的真实样本为起点，终点是其后首次比该起点至少多512步的样本。允许区间重叠，要求正有限时间差。目标2048是落盘观测步数；因缓冲、采样和信号处理，真实推进可能更多。末个完整 step 只能提供下界；原生审计缺失时精确调用数必须为 null。

短段不能覆盖10368步完整统计窗，无法测全后续窗口统计、长时间内存与输出成本，也不能证明最终收敛时间或12小时一定够用。初始化/字段读回耗时不是逐步吞吐量证据。两个区间缺失时记录证据不足，不能扩预算、重试、拼接或进入 T；性能数据不进入正式参考、GCI、V2误差表。

## 5. 停点与后续

本轮已完成兼容性核对及可供采用的具体最小范围；性能实现尚未开始。建议后续范围仅为：在新隔离目录实现四个职责文件及必要软件检查、生成关闭执行权限的性能准备封存；测试用模拟进程/轨迹，不调用原生程序。保持同一 ELF，因此没有编译步骤；性能推进及正式计算各按覆盖其范围的真实授权执行。

科学状态保持 NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、正式 geometry_PASS=null、REFERENCE_QUALIFIED_FOR_CASE=false，MODEL_COMPARISON/physical_validation=NOT_EVALUATED；reference_qualified/strict_error_bound_established/submission_ready=false。零步几何接受独立记录，不升级正式几何。S0/S1已接受事实、旧横槽FAIL/380差异、早期MRP静态FAIL、HISTORICAL_EXCLUSIVE_ATTRIBUTION=NOT_ESTABLISHED、D4预测HOLD、F04 OPEN及外部历史声明范围均保持。正式24项矩阵仍完成4项、剩20项，测速两条不计入其中。

本轮没有构建、原生调用、VTK读取器调用、时间推进、真实新 run_id、启动命令、提交推送或对外发送项目材料。共享当前状态及最新交接已同步；复核清单见 verification.json 与 report_manifest.json。
