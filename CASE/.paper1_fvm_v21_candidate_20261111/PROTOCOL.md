# 固定六方向显式沟槽独立参考：v2.1_stopping_fix

2026-11-11。PREPARED_NOT_RUN，PENDING_ASTRA_V21_RECHECK。作者授权定点修复、边界测试和指定模型静态审查；没有求解启动授权。v1不变，旧v2完整清单/输入/源码/二进制已归档到docs/reports/PAPER1_fvm_v21_review_20261111/v2_unreleased_snapshot.tar.gz；旧哈希仍标识未放行历史快照，不能冒充新审查。

C++源码与二进制沿用v1且逐字节核验，不编译。几何、物性、网格、离散格式、线性容差与比较门槛不改。修订的是运行接收/来源实现，不能称所有条件均未改变。原生残差普通p/U/v恢复1e-10，tight恢复1e-11；比较使用严格小于，与本机原生代码一致。T平板新增明确限定的零分量例外。

## 1. 比较对象和三个实现决定

本协议对应理想、稳态、全充液、不可压、恒黏度、无滑移的周期直矩形槽 Stokes 问题。x 横槽、y 沿槽、z 高度；槽宽 120 nm，周期 240 nm，槽/凸台各半。mu=1e-3 Pa·s，rho=1000 kg/m³，nu=1e-6 m²/s，加速度 1e5 m/s²。只施加一次体力；压力扰动周期，不再同时施加压降。

1. **K 归一化**：J_i=sum(u_i V)/Aplan，K_i=nu*J_i/a，单位 m³。另输出 ubar=sum(u_i V)/Vfluid、kappa=nu*ubar/a（m²）、Href=Vfluid/Aplan（m），并核 K=Href*kappa。禁止把体积平均速度算出的 kappa 直接拿来与论文 K 比较。
2. **沿槽 P**：求解标量 v(x,z)，-nu*Laplacian(v)=a；物理速度 (Ux,Uy,Uz)=(0,v,0)。y 方向 empty 只用于标量的平移不变性，不删除物理 Uy。v 在固壁为 0、x 周期。没有压力求解或跨槽流动。独立导出物理 Uy，不能把 v 当 Ux。
3. **横槽 T**：独立源码求解 -nu*Laplacian(U)+grad(p)=a*ex、div(U)=0。源码没有 `fvm::ddt` 或 `fvm::div(phi,U)` 项（逐行核过），也不依赖日志中的应力模型名称推断 Stokes。压力为运动学压力 p'/rho，固定一个参考单元消除常数零空间；x 周期，固壁 noSlip 和 fixedFluxPressure，配合 constrainPressure；y empty，Uy=0。

这里是有限体积第二实现，不输入局部立方律或 V2 的 K。不声称不存在共同几何/边界/归一化错误，不称第二方实验或物理验证。

## 2. 真实边界和挤出厚度

沟槽在 0<x<120 nm、0<z<d；贯通间隙在 0<x<240 nm、d<z<d+h；120<x<240 nm、z<d 为固体。周期端只连接 z>d 的流体；x=0、z<d 是上一周期凸台的侧壁，必须设 wall，不能误接周期。x=120、z<d 也是 wall。三块网格共形，没有内部人造壁或挡板。平板 d=0 另用完整单块。

数值挤出厚度 Ly=1 nm、单层 empty；几何和解严格沿 y 不变。其体积 V=P*Ly*(h+d/2)，Aplan=P*Ly；积分除以 Aplan 后 Ly 消去，等价于原 Ly=240 nm 的连续平移不变模型。P 的通量为沿 y 完整截面流量、由不变性精确满足；不把这一恒等关系计为额外质量验证。T 在每个 x 位置积分完整流体截面，侧壁零通量，保存校正后面通量并与体积积分主通量交叉检查。

## 3. 固定范围与具体输入数

| h/d nm | 方向 | 针对声明 |
|---|---|---|
|75/100|P、T|基准 A 与 45 度重建角差|
|25/100|T|V2 横槽旧最坏、薄隙分辨率|
|50/120|P|原公式沿槽旧最大偏差|
|125/120|P、T|V2 沿槽旧最坏、原公式横槽旧最大偏差|

每方向三档均匀贴体网格 dx=1.25、0.625、0.3125 nm，保持物理壁位置不变，分别命名 coarse/mid/fine。单例最大 454656 流体单元（h125_d120_T_fine），全部 26 例的单元数在生成时逐例写入 `case.json` 的 `expected_cells`。总 18 个主网格输入。每方向另有一个相同 fine 网格的 tight 输入，将线性容差和稳态残差控制收紧 10 倍，用于原判据已要求的代数误差检查：共 6 个，不是新几何/新网格/独立重复样本。

另有 h75/d0 平板 P、T 各一份 dx=0.625 nm，检验这份新源码的解析基准。因此准备目录总 26 份：18 主网格+6 同网格 tight+2 平板。不把"6 方向"说成"只有 6 次运行"，也不把 26 次潜在运行说成 26 条公式验证。

### 3.1 资源预算（与prepared_manifest.resource_caps同源核对）

|层|endTime上限|墙钟上限|初场|
|---|---:|---:|---|
|coarse|60000|1800 s|零|
|mid|120000|14400 s|coarse绑定末态|
|fine|200000|43200 s|mid绑定末态|
|tight|250000|43200 s|fine绑定末态|
|flat|60000|3600 s|零|

迭代Time不是物理时间。不同几何/网格的耗时不能用单个平板保证；tight有先触墙钟的风险。墙钟或异常退出拒收，不自动增配。正常到迭代上限可经完整判据接收，并显式记录iteration_cap，不伪称主动收敛。

### 3.2 完整字段与平板例外

机器规则唯一来源prepared_manifest.acceptance_rule；控制器与读回器调用同一acceptance.py，独立解析原日志/CSV后对照回执；case.json必须等于清单中的对应记录。

沟槽P仅查v；沟槽T查Ux、Uz、p，以及实际打印的Uy。普通全部<1e-10，tight全部<1e-11；tight线性容差1e-13、其他层1e-12、relTol=0。Ktight与Kfine差≤0.05%不代替tight自己达标。

平板P仍查v，不要求不存在的p/Ux字段。仅d=0、direction=T、level=flat且元数据flat_zero_component_exception=true允许不要求Uz归一化残差低于阈值，但Uz日志仍须完整有限非负。此例外同时要求p/Ux<1e-10、导出场max|Ux|有限且>0、max|Uz|/max|Ux|≤1e-9，以及K和剖面解析误差均≤0.1%。这是可忽略幅值的操作性条件，不称浮点机器零。既有最细收支检查仍全部适用。

### 3.3 日志轮次、结束与停止原因

本机Foundation13 singleRegionConvergenceControl::criteriaSatisfied使用solvei=0，向量取cmptMax(initialResidual)，原生比较为严格<。固定C++无Time逐轮打印；nNonOrthogonalCorrectors=0下，每轮只有v，或Ux/(可选Uy)/Uz/p各一次。解析器验证完整顺序，禁止重复p/缺字段/负数/非有限残差；取最后完整轮对应的首次求解，不任意抓全文最后一行。原生收敛报告须在最后求解之后，其时间值须等于startTime+完整轮数，不能绕过任何字段条件。

独立退出码须0且日志最后非空行严格为End。实际停止原因与事后接收分开：native_convergence优先（同轮达上限仍记原生）；否则按本机Time::running的time<endTime-0.5*deltaT判断iteration_cap，deltaT固定1，轮数为ceil(endTime-startTime-0.5)。其他正常提前退出记unclassified_normal_exit并拒收；124记wall_clock，其他非零记abnormal_exit并拒收。上限正常结束且完整标准达标允许post_hoc_acceptance=accepted。最终原生场时间须与startTime+轮数一致。

零残差是合法值；回执stopping字典须与同日志/原CSV独立重算结果逐项严格相等，零/零一致，一零一非零不一致。same_residual另作有限非负数相对差≤1e-9的边界辅助测试，正式接收不通过它放宽字典一致性。不存在主导分量OR分支。

### 3.4 延拓来源

源先通过同一release的完整独立读回，不仅看solver_converged布尔。从receipt绑定的最终原生场时间取源，不选任意最新目录。校验源case/run/release、退出/日志/收敛、原场、五份mesh及同几何/方向和前一层身份。目标0.5保持冻结0目录不变；因purgeWrite可能清除0.5，映射后输入另存runtime/seed_inputs，逐字节核身份。

回执绑定source_run_id、source_receipt_sha256、source_release_sha256、source_time、source_field_sha256、source_mesh_sha256、target_time与mapped field hash、mapFields工具hash/argv/log/exit、seeded checkMesh日志和退出码。mapFields加入external_sha256；后处理递归核整条固定层链，缺环/漂移拒收。充分收敛时初场只改变路径，不能预先假设有限迭代已充分求解。

## 4. 既有参考与比较门槛

- 平板两方向 K 相对解析 h³/12 差 ≤0.1%，单元中心体积加权速度剖面 L2 差 ≤0.1%。数值积分定义明确，不冒称连续 L2 误差界。
- 每方向 d21=abs(Kmid/Kcoarse−1)≤1%，d32=abs(Kfine/Kmid−1)≤0.5%，且 d32≤d21；两者均 ≤0.05% 时免除递减关系。
- abs(Ktight/Kfine−1)≤0.05%。tight 不当第四档网格。
- 各层均须正体积/有限值/几何与来源无误。最细 fine 及同网格 tight、平板 flat 要求：T 完整截面面通量最大极差/平均值 ≤0.1%，校正面通量与体积主通量差 ≤0.1%；驱动功与黏性耗散相对差 ≤0.1%。coarse/mid 保存这些诊断，不额外施加最细层 0.1% 门槛。P 的 y 不变通量关系不计作独立测试。
- 原始场+日志、独立退出码、run_id、源码/字典/二进制/库身份、证据 hash 均绑定；只看程序 End 或 CSV 不接收。
- 满足上述参考条件才计算 delta=(K5/Kref−1)*100%；abs(delta)≤2% 为该方向交叉一致性 PASS，>2% 为 FAIL。参考未取得是 NOT_ASSESSABLE，不是 LB 被判错。
- 基准 A 差 abs(A5/Aref−1)*100%≤2%，beta 差 abs(beta5−betaref)≤0.40 度；均由同一 P/T 参考导出，不计成额外独立样本。正确 A5/Aref=(1+delta_y)/(1+delta_x)，delta 在该式以小数代入。角度始终从槽轴量起，beta=atan(Kxx/Kyy)，原公式角差=betaLC−betaref。

## 5. 后处理及结果修改

`referenceEvidence/cells.csv` 记录每个流体单元坐标、V、三物理速度分量、梯度平方、黏性耗散和运动学压力；T 另导出 `x_faces.csv`，面通量统一朝 +x。`postprocess.py` 独立按体积加权重算 K，逐位置核域、体积和截面完整性；不读取保留预测结果，不更改 V2。`comparison_inputs.json` 从 v1 逐字节继承（六方向 K5 及已存来源哈希），v2 生成时校验其与 `map36_evidence.csv` 一致，不一致即拒绝生成。LC 与 V2 只在参考接收后评价，固定已发表在当前稿的四个舍入系数。

原 36 条 5 nm 表 6/8 不混入新参考。新表只报六方向及其子集计数；新最大值只限实际子集。若 8% 等超 2% 结果出现，按 DECISION_RULES_V1 的传播 epsilon_R=(1+delta)(1+epsilon5)−1 和失败改稿规则处理；不放宽阈值、重拟合、删点、自动加网格或试其他几何。

## 6. 资源与执行边界

`run_one.py` 只允许操作员明确指定一份已发布输入；默认不执行，`--execute` 表示显式启动，不能从准备完成推断授权。要求已加载 `/opt/openfoam13`，拒其他版本和 MPI。每次运行预先检查 `release_manifest.json`、源码/输入/可执行文件/外部库指纹；拒覆盖、续跑与自动重试。单进程，线程 1，地址空间硬上限 4 GiB，单文件硬上限 256 MiB；blockMesh/checkMesh 各 120 秒，mapFields 900 秒；求解墙钟上限按 §3.1 分层取用，超时杀整个子进程组并记录失败；总目录 1 GiB 是结束后的接收检查而非实时磁盘配额。无法保证所有实例在预算内通过，不自动增配。

每次只运行一份输入，完成后不自动进入下一层/方向或接收，原始失败保留。日志/退出码/source hash/资源记录写 receipt，`postprocess.py` 单独分析。层间依赖由 `seed_from` 表达：源算例未通过绑定完整的独立读回时，下一层拒绝启动——这是**依赖**，不是自动续跑。

执行是否结束与参考是否合格分开：全部固定运行记录结束但参考失败时，标记 COMPLETE_WITH_REFERENCE_FAILURE；提前出现失败则 STOPPED_ON_FAILURE，后续未运行项仍原样列出。它们均不授权继续加算。原生最终 v 或 U/p/phi、五份 mesh、独立退出码、日志和运行时 release 快照均必须留存且哈希一致；删除原场不能用 CSV 补足接收资格。


## 7. 准备/运行/审查边界

仅合成测试和静态审查不是数值基准。旧v1 T平板FAIL、带外40000步诊断、S4/D4及reference_qualified=false/strict_error_bound_established=false/submission_ready=false不变。平板长跑仅说明该平板求解不足可明显改善；不保证沟槽精度，不把未收敛偏差称假误差，不推断LBM高估K。

本release两方向平板必须按新规则各自LOCAL_CHECKS_PASS，控制器才允许任何沟槽启动。不能复用v1或带外诊断冒充当前基准。指定Astra审查新快照后仍须作者另行授权启动；不自动执行、重试、批跑或换点。当前26输入全部未执行。
