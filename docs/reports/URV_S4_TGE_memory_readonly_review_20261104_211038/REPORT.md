# TGE 内存需求与资源修订范围只读审查（AI 辅助工作稿）

用户指令：读核查内存需求与资源修订范围。范围仅为已有日志、同一封存 ELF/源码、旧结果与当前资源接口的只读核查；本轮只写此报告与共享交接，不修改 CASE、旧合同、参数或内存限制，不构建、不启动任何原生/读场/PERF/正式计算，不重试，不进入 S5。作者负责人工审定；不是独立人工终审，也未声称模型切换或 Astra 已裁定。

**结论：原 8 GiB 单进程地址空间上限与不改动的 T/0.625 nm 稠密存储实现不相容。现在不再只依赖“节点变成8倍”的经验判断：旧栈回溯定位到 Bouzidi 距离场的 Column<double> 分配路径，源码推导的三组同时存在的 double 场载荷小计约8.68850 GiB，加上三组逐格点指针后约9.32424 GiB，尚未含全部辅助内存。8 GiB 不应再次作为同配置成功接入的资源方案；但实际峰值、最小可用上限、16 GiB 是否足够以及整台电脑能否运行，仍未建立。**

本报告形成后续资源修订的最小范围建议，尚未采用或最终冻结资源新值，没有失败后重试许可。

## 1. 原始失败与身份

- 既有零步 audit_id：`URV_S4_TGE_ZERO_v1_20261104_01`；失败身份 `ZERO_URV_S4_TGE_ZERO_v1_20261104_01_precheck`。
- 原 release：`CASE/unseen_v2_reference_S4_tge_v1/evidence/S4_TGE_zero_launch_release_v1_20261104_01.json`，SHA `d654196816e36fe97638c079c26a498e6203db8a01bd492042ecb1320c314949`，3710项封存输入本轮逐项一致。
- 原准备A SHA `53e544543ae26402a0d0fac7a7b3294e0a2286e7a7d4c336ce08e91abf53bfb9`；同S1 ELF SHA `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`；OpenLB提交 `882924a9cfc8dcdf82909e39530789cb6f5ebcc4`。
- describe退出0/0.367478s且已有执行计数0；precheck退出−6/10.417795s、`std::bad_alloc`、`timed_out=false`、`resource_stop_reason=null`。初始化/初态读回未执行。没有precheck的execution_audit、boundary_audit或result，不声称已读到其步数计数或几何通过。
- precheck静态分支在时间推进前返回。新定位是壁面接入中的内存分配失败；未产生流场结果，不是V2/物理结论反证。

## 2. 旧栈回溯能定位到什么

本轮只用 `addr2line -C -f -e <既有ELF> <日志中的相对偏移>` 读取二进制符号，没有执行ELF。相对偏移已由日志提供，避免把ASLR后的绝对地址误当ELF偏移；ELF为x86-64 PIE。原偏移与返回地址减1两种读法一致：

|日志偏移|符号含义|
|---|---|
|0x7da35|`cpu::sisd::Column<double>::Column(size_t)`|
|0x80223|`ConcreteData::allocate<Array<BOUZIDI_DISTANCE>>`|
|0x80780|`ConcreteBlockLattice::getData<Array<BOUZIDI_DISTANCE>>`|
|0x80e91|`Cell::setFieldComponent<BOUZIDI_DISTANCE>`|
|0x8173a及后续|`setBouzidiBoundary<...,BouzidiPostProcessor>`，再回到main|

符号输出见existing_stack_symbols.txt与existing_stack_symbols_return_minus_one.txt。ELF没有可用行号调试信息（显示??:?），故定位层级是函数/字段，不能声称得到精确C++抛出行、失败的是第几列或当时申请/驻留字节。先前“具体缓冲区未定位”现可更新为“已定位BOUZIDI_DISTANCE列分配路径，列序号和实际峰值未知”。这来自新增只读证据，不回写旧报告。

## 3. 为什么不是只算1652万流体节点

物理几何保持h30/d80/w120/周期与Ly240nm，T方向+x，dx0.625nm。当前程序在矩形包络的全部格点分配场数组，包括实体、壁面和重叠层，并非稀疏地只给流体或壁面链分配：

1. `urv_reference.cpp`构造domainTop=h+d+4dx的矩形IndicatorCuboid，再创建单cuboid。
2. CuboidDecomposition按端点计数构造与shrink；此固定几何的核心z层数由源码得到(h+d)/dx+5。旧5/2.5/1.25nm三个算例的全部材料数之和分别为62208、451584、3428352，与此公式逐项一致（old_geometry_crosscheck.json）。这些是旧结果交叉核对，不是新网格原生审计。
3. 候选静态核心为384×384×181=26,689,536；SuperLattice默认overlap3，BlockStructure每轴两侧各加3，数组格点数为390×390×187=28,442,700。候选数是源码推导，未伪装成实际precheck输出。
4. CPU_SISD的POPULATION使用单份CyclicColumn数组，不臆加第二份分布量缓冲；FORCE三列。BOUZIDI_DISTANCE为FIELD_BASE<0,0,1>，即Q=19列double，首次访问时getData按全部getNcells()分配。它不是“196万条壁面链各存一个数”。

|同时存在的主要载荷|0.625nm静态载荷GiB|
|---|---:|
|19列分布量double|4.026377946|
|3列体力double|0.635743886|
|19列Bouzidi距离double|4.026377946|
|上述三场小计|**8.688499779**|
|BlockDynamicsMap两组逐格点指针|0.423829257|
|CPU动态分派字段一组逐格点指针|0.211914629|
|上述五项小计|**9.324243665**|

GiB=2^30字节。每组分配生命周期与源码位置见source_locations.json，算术见static_memory_accounting.json。指针按当前x86-64 ELF的8字节计。这是同时存续的指定数组有效载荷小计，不是完整进程地址空间、峰值RSS或建议预算。未计材料数组、mask、通信索引/缓冲、后处理器、分配器/页对齐、共享库/栈映射、VTK写出和读场临时数组。不能把9.32向上取整成“10 GiB肯定足够”。

旧结果报告中的“384×384×180=26542080全域”少计一个端点z层，也未含重叠层；旧1.25nm“192×192×90”与实际旧材料总数不符。这里单独更正内存估算口径，不修改旧结果、几何或协议。流体节点2,064,384→16,515,072仍精确8倍；完整数组格点由于固定辅助层数，增幅不是精确8倍。

因此，未改实现的成功precheck必须容纳超过8 GiB的同时载荷，原上限结构性不足；其他宿主约束是否同时存在仍无法排除。原崩溃没有保留RSS/VSZ峰值、失败请求序号或内核分配原因，不能唯一量化所有因果贡献。

## 4. 当前机器与资源机制快照

2026-11-04T21:15:35+08:00单次只读快照（非失败当时、非启动准入）：MemTotal=33320763392bytes≈31.03GiB，MemAvailable=16220262400bytes≈15.11GiB，磁盘空闲339213897728bytes≈315.92GiB；swap约8GiB。没有关闭其他任务、改swap或改系统限制。

当前检查进程的cgroup路径及可见祖先均已只读记录，memory.max/high为max，memory控制器存在；这不能证明旧失败子进程的整个资源环境，也不能证明有权创建并配置新的独立资源组。该共享组的memory.peak/events不能归因给过去求解器。根cgroup没有memory.*文件并不等于系统不支持：已进一步读到实际所在组文件。未创建资源组/写入限额/做探针。不能把“当前检查进程无AS限制”当成旧子进程没有8GiB限制。

旧控制器只在创建子进程前setrlimit(RLIMIT_AS,8GiB)，没有采集VmPeak/VmHWM、wait4峰值或独立组内存；RSS与虚拟地址空间是不同指标，不能将8GiB与12GiB可用RAM门槛相加推导机器需要20GiB。RLIMIT_AS的含义由Linux man-pages核对；整组内存与后代归属由内核cgroup-v2文档核对，参见文末来源。

## 5. 需要修订的最小接口范围

详细待采用文本见RESOURCE_REVISION_SCOPE_DRAFT.md。建议仅动新隔离候选的控制器/资源记录/封存接入，保留同ELF、几何、方向、物性、边界、平均定义、MRP/A1路径与原科学门槛。

- **分开三项**：单个大进程地址空间、整任务组实际内存/后代、启动及运行的宿主余量；不能只把8换成16。
- **补充可归因峰值记录**：每个调用独立记录生效限制、独立退出、wall/资源原因、wait4或等价原生峰值RSS、/proc采样的VmSize/VmPeak/VmRSS/VmHWM及其采样局限；如采用专属cgroup，保存memory.peak/events并由组外监督收尾。不得拿共享桌面组历史峰值充数。
- **完整进程生命周期**：零步原生退出并回收后才读场；整组包含控制器及全部后代。未来正式检查器raw/data与pvpython会同时占内存，必须另预算，不能以“求解器1进程”当整活动只有1进程。
- **完整输出范围**：旧cwd=CASE会先建根tmp，旧监视只覆盖run或audit目录，未覆盖根tmp。新候选须把临时cwd隔离到本身份或将其纳入计费，覆盖日志/回执/失败残留/分析/VTK/临时文件；定期观测不是硬磁盘配额，必须准确表述并给守卫机制。此次没有证据表明旧输出实际超过4GiB。
- **资源候选而非采用**：先前16GiB单进程AS、18GiB任务组、22GiB启动可用RAM、4GiB宿主余量可以进入核查清单，仍未证明足够/可执行/已授权。21:15快照15.11GiB低于22GiB候选门，不能据此签发该方案“资源通过”，也不能据此判本机永远不可行。300秒只用了10.42秒，没有从本次失败推出必须加时的依据；新时限须按新范围另审。旧1800/3600秒、48h正式、4h检查均未被本轮采用。
- **失败后身份与权限**：旧attempt和输出保留；新准备/新资源采用/新审计身份及输出/新封存/真实失败后重试授权分别建立。不得清目录、复用旧SHA、另发编号规避不重试。新3＋1只0推进，之后仍不自动PERF/正式/S5。

## 6. 后续读场与正式分析的额外风险

已核冻结read_fields.py：material视图外还同时生成mask、非零索引、物理坐标、整数坐标、ids、选出的速度/压力/耗散以及float64临时数组、unique副本，不能用原始VTK文件大小当读场峰值。初始化模式不读diagnostics，但正式模式创建全轨迹字典。冻结check_results.py保留raw CSV字符串字典和数值数组后启动pvpython，父子同时驻留。window_metrics使用约2000000个元素分块，并非把所有完整窗口复制成二维大数组，不能按窗口数×窗长虚构峰值。满cap约1486849行的父/子字符串对象开销尚无测量；本轮不重放科学检查器或读取新VTK，也不重构科学累加路径。

若后续要削减内存，优先另审控制层生命周期、重复对象释放或有界读取；改动累加顺序须独立检查数值口径。稀疏化BOUZIDI_DISTANCE、缩小overlap、改二维/MPI/碰撞/浮点类型属于更大实现变化，排除在本次最小资源修订范围之外。

## 7. 保护、停点与下一步

本轮初始3710项绑定输入和3739项旧保护文件全部与前轮相同。最终完整性另见final_integrity.json；27份本轮直接读取的源/原始记录指纹见reviewed_sources_sha256.json。无CASE改动、构建、原生调用、读场、重放科学检查、PERF、正式、重试、加时或新执行合同。唯一新增是本审查目录、共享状态/交接的当前说明，没有新run_id。

原S4六条per-run接受、P网格PASS、T中细1.328387035%>1% FAIL、S4_STAGE_ACCEPTED=false保持。失败零步未过、geometry_PASS=null、NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false；reference_qualified=false、MODEL_COMPARISON/physical_validation未评价、strict_error_bound/submission_ready=false、F04 OPEN及全部历史FAIL不变。

下一步建议：采用“只改隔离资源包装与证据记录”的最小准备范围后，再实现/软件验证并封存执行关闭的候选。先复核整组机制与具体预算，再单独批准新的3＋1；不直接交启动命令。本轮不是最终资源规则终审。遇到新的矛盾/复杂归因或资源规则最终冻结，按用户偏好建议GPT-6 Astra｜High；没有调用/冒充其独立裁定。

## 方法与来源

本报告为AI辅助内部审查工作稿，使用peer-review技能做声明与证据边界整理；intake验证READY_FOR_LOCAL_REVIEW只验证声明，不代表科学或资源可行性通过。未发送项目材料到搜索服务；仅查询以下公开规范/技能出处。

- Linux man-pages, getrlimit(2)：RLIMIT_AS是虚拟地址空间上限，超限分配可返回ENOMEM。[原文](https://man7.org/linux/man-pages/man2/getrlimit.2.html)，2026-11-04核对。
- Linux kernel, Control Group v2：整组/后代内存计费、memory.max/peak/events机制。[原文](https://docs.kernel.org/admin-guide/cgroup-v2.html)，2026-11-04核对；引用机制不代表本项目已实施。
- Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents. [arXiv:2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。2026-11-04公开记录为v2。仅用于技能流程归属，不作CFD/内存容量证据。
