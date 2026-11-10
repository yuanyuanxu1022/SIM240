# D4余14项主开发执行协议 v1

2026-10-24。用户明确授权准备首批14项执行入口与运行前核查，尚未启动计算。本阶段许可仅表示通过本机技术准备后可以交付用户手动启动，不声称老师外部批准或科学结果通过。旧阶段、模型锁、网格草案和原始FAIL不改。

stage_cases.csv只列原主表中尚未完成的14项new_dev：h75nm、w60/d25/50/100/120各P/T，以及w240/d25/50/100各P/T，dx5nm、P=Ly=2w、φ=.5、a1e5、ρ1000、ν1e−6、μ.001、τ1。排除已完成h75/d120/w240及所有linearity、smooth、regression、legacy、grid_reference、prediction。顺序沿用既有DEV14方案。

复用原C++源码和已编译binary，SHA256需与历史已验收批次一致；make --question只检查构建状态，没有重新编译。新增Python入口复用原run_case.prepare生成实际运行目录/manifest，事先保存14份完整key=value正式配置，其内容须在未来运行生成后逐字节一致。预先保存配置不表示正式运行目录存在。

原protocol/execution.json及开发筛选PROTOCOL数值门槛原样继承：质量漂移<1e−10、密度≤1e−6、Mach<.05、窗口样本std≤1e−6/span≤5e−6/cross≤1e−12、末截面差≤1e−5、有限值、正主通量、几何/q=.5、无fallback/unresolved。统计窗Δt*=.75（1013步）、最大物理时间8(h+d)²/ν、帧计划0/.01/.02/.05/.1/.2/.5/1/2/4/8与收敛末态保持。不新增/放宽结果阈值。

准备限参数核对、describe/precheck零步运行、独立节点/18方向几何与q核查、来源保护和调度拦截测试；禁止准备程序执行steady。14个方向分别precheck，只有7种不同几何；零步结果不作为流动物理验收。

release绑定源/binary/库/头文件等原证据、首6筛选独立验收、本方案、阶段源码/协议/白名单、14份配置及本轮零步与审查证据。启动前及每项前后验证哈希；核当前OpenLB提交，不把旧构建环境当当前环境。其他机器必须重新编译/核查/绑定，不能照抄本机release。

默认运行入口只检查。仅明确--execute且固定batch_id被接受时创建正式结果目录。已存在批次禁止覆盖/续跑；发现相同case在规范results下已有正式result也拒绝。单进程单MPI rank，启动前及每项前MemAvailable≥2GiB、磁盘≥7GiB，取自DEV14方案；检查资源是当时快照，不是运行峰值保证。

逐项保存run_id、完整配置、run manifest、源码/二进制/依赖/协议/构建哈希、库版本、完整日志、/usr/bin/time资源、独立进程exit、原始CSV/场、输入后核对。非零退出、绑定变化、执行输出不完整或资源不足则停；不重试、不自动续跑。每项独立exit0仍需完成后的独立验收；原RESULT_PASS=false不修改。

批次运行锁只防本入口重入，不声称能防所有人为手工启动。批次完成停在independent_acceptance=pending，不自动分析、拟合、运行网格或预测。原12开发细格、20预测/预测细格继续关闭；G4 v1系数与逐点预测不变。

固定batch_id=development_remaining14_20261024_v1，输出根为D4/results/<batch_id>，本机命令见NEXT_COMMAND.txt。准备完成、交付命令、用户启动、运行完成和独立验收是不同状态，分别记录。
