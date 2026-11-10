# D4首批中网格6项执行与独立验收协议 v1

2026-10-24，用户已明确授权实现入口、来源绑定、分块验收、逐几何比较和运行前核查；不授权AI自动启动正式计算，不声称老师外部批准。只允许stage_cases.csv所列三几何(h,d,w)=(75,25,60)/(75,120,60)/(75,120,240)nm、dx2.5nm、P/T共6项，P=Ly=2w、φ=.5、a1e5、ρ1000、ν1e−6、μ.001、τ1。其余84条canonical行均拒绝，包括已完成粗格、窄/宽1.25nm、预测及参考。最大2.5nm流体节点1990656。

原C++、binary、库和protocol/execution.json保持；make --question核现有构建有效，source/binary必须与旧已验收绑定一致。只有describe/precheck可在本轮自动执行，两者collideAndStream=0，不当物理验收。新批次id固定development_grid_mid6_20261024_v1，任何已存在正式批次拒绝覆盖/续跑；同case已有正式result拒绝重跑。

入口run_mid6.py默认只检查，明确--execute才创建正式results。start_from_project.sh自动定位项目根目录；绑定相对路径也按该根解析，不依赖调用目录。单进程单MPI rank、启动前和逐项前MemAvailable≥6GiB且磁盘≥10GiB，swap不计作可用RAM。release绑定本机源码/binary/库/头文件/构建版本、上游已验收记录、比较协议和程序、6份正式配置、零步与拒绝测试。另一机器必须重建绑定。

原数值门槛不改：全程质量漂移<1e−10、密度≤1e−6、Mach<.05；末完整窗口样本std≤1e−6/span≤5e−6/cross≤1e−12m²/s；末双截面差≤1e−5；正主通量、有限值、材料不变、完整几何/q=.5、无fallback/unresolved。dt=dx²/(6ν)=1.041666666666667e−12s，统计窗Δt*=.75=4050步；最长时间8(h+d)²/ν，d25上限76800步、d120上限292032步。停止于原首个合格窗，不为补未来帧延算。帧计划t*=0/.01/.02/.05/.1/.2/.5/1/2/4/8及收敛末态，未达到的未来点如实标记。

逐项保留完整配置、run_id/manifest、source/binary/OpenLB/依赖、日志、/usr/bin/time资源、独立exit、原始CSV与VTK引用及输入前后哈希。非零exit、绑定变化、资源不足或不合预期标志立即停；不自动重试/分析/拟合或下一批。原RESULT_PASS=false保留，独立阶段结论另存。完成时independent_acceptance=pending。

独立验收由用户在批次完成后另发任务。accept_batch.py只读完整已结束中6，调用analyze_results.py与check_flow_frames.py，分别保存分析退出码/日志/资源，后生成绑定raw+analysis+源码协议的certificate。analyze_results用数值矩阵读取diagnostics，window_metrics.py按16MiB工作预算分块重算所有完整窗，ddof1、全部门槛和首个停止点不变，不用E[J²]−E[J]²近似。输出数组随诊断行数线性增长，上限由本批固定maximum_steps限制。流场reader逐帧处理，仅缓存规定帧对应诊断行；保留坐标基准，不累计三维场。最大中格按保守每核心节点2KiB加1GiB估计约4.80GiB后处理空间，需独立空闲RAM≥6GiB；这是预算，非实测细格峰值保证。

export_references.py核既有粗6的真实独立验收产物/原始哈希；未来中格须先产生certificate再导出。完整canonical配置、物性/方法、独立exit、K/run_id、源码/库绑定均核。比较CLI只接带哈希绑定的bundle，普通手填true CSV不构成验收证据。容器哈希用于完整性，非对抗篡改的数字签名。verify_bundle会重核真实源及接受证据，不仅重算容器哈希。

grid_policy.json为新的可执行v2：保留旧草案全部研究容差1%/0.5%与η=.0001、趋势顺序/条件GCI；以输入十进制字符串、Decimal精度60判定阈值，K用差值≤limit×参考比较，A在同一Decimal上下文计算，浮点仅用于条件性p/GCI展示。并非新增物理容差或老师批准。每几何KP/KT/A独立判断；两个窄槽六量仅形成narrow_two_geometry_gate，最终仍三几何九量全部PASS才能记GRID_SENSITIVITY_TARGET=PASS。部分缺项全局不能PASS。中6只有两格数据，不能完成三格网格判定。

原草案和release保留。本v2及逐点来源在新细格结果出现前绑定；任何变化另立版本。数字边界与趋势测试覆盖等号及两侧、差值抵消、缺项、重复/伪造来源和局部/全局范围。仅三几何规定扩散缩放路径的联合离散敏感性，不宣称全域网格独立、零误差或误差上界。

后续窄细4项与宽细P/T仍关闭；次序6→4→1→1。宽细RAM22GiB及多日预算问题未由本批许可解决。预测16+4继续关闭，G4 v1候选锁不改；用新增开发数据重拟合另立v2模型，并在取得保留结果前重新冻结。比较v2和模型v2是不同对象，不混淆。
