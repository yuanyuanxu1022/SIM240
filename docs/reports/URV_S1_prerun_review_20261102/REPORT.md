# S1 光滑基准运行前材料与合同兼容性审查

日期2026-11-02。结论：**原URV-v1已明确S1两条物理问题，输入和解析基准静态核对通过；当前S0/A1宿主、来源分支、捕获器及控制器不能直接作为S1执行包。S1_RUN_READINESS=NOT_READY，需要在新隔离候选中按阶段接入。** 这不是S1数值失败；S1没有运行、没有实际run_id或正式启动合同。本轮只读审核并新增报告/草案，未修改CASE源码、合同或规则，未编译、调用原生程序、运行求解器或签发许可。

## 1. 本轮范围与证据

用户原话：“另定范围后，审核 S1 光滑基准的运行前材料与合同兼容性。”当前仅据原矩阵审核两条 S1_SMOOTH_THIN，不扩到S2/S3或完整24条实现。scope_review.json记录实际范围。S0原始数据、封存、修复验收保持；S0已接受是接续前提，但不能代替新版本S1接入、零步或解析验收。

本轮读取原URV协议/矩阵/describe-only模板，现A1宿主/观察量/捕获/启动代码和独立检查器，核对原科学门槛。使用精确有理数及已有独立Python/NumPy几何枚举器做纯算术，不加载OpenLB或推进流场。2399项受保护文件前后不变，包含S0完整复核及当前源/规则。没有把旧G1平板结果、h75零步或软件夹具标成此次S1已完成。

## 2. 审核的最小S1输入与物理意义

| 输入/预期 | 原S1规定 |
|---|---|
| planned_case_id | URV1_SMOOTH_H30_P_dx1p25_a100000；URV1_SMOOTH_H30_T_dx1p25_a100000 |
| 几何 | h30nm，d0，Lx=Ly240nm；原w120nm占位保留，d0时无真实沟槽 |
| 方向 | P沿+y；T沿+x。平板物理上无槽向，各自独立对解析解验收 |
| 网格 | dx1.25nm；192×192×24=884736个核心流体节点 |
| 流体与驱动 | rho1000kg/m³，nu1e-6m²/s，mu0.001Pa·s，tau1；a1e5m/s²，G1e8Pa/m |
| 边界 | x/y周期，静止无滑移Bouzidi上下壁，D3Q19_FORCE/ForcedBGK |
| 时间步 | dt=2.6041666666666667e-13s，按原转换式 |
| 统计与上限 | 原2592步窗口，27648步上限；窗口物理时长6.75e-10s，上限7.2e-9s |
| 壁面预期 | candidate=valid=installed368640、q0.5，无fallback/unresolved；仅静态几何预期 |
| 资源 | 1 MPI/线程/cuboid、overlap3、每方向原生墙钟14400s，地址空间8GiB |

J=流体核心速度体积分/平面面积（m²/s），K=nu J/a（m³），U=J/H（m/s），本S1的H=h=30nm。这是固定间隙、全充液平板输运控制；不涉及压头运动或填充。

解析速度 u(z)=a z(h-z)/(2nu)，K=h³/12=2.25e-24m³，J=2.25e-13m²/s，截面平均速度U=7.5e-6m/s，最大速度1.125e-5m/s。由该连续解析解估计Re_H=3.375e-7、Mach约4.0595e-9；这些是理论值，不是求解器测量。连续体积1.728e-21m³、质量1.728e-18kg。

保存的目标步号用有理数独立复算为0,35,70,173,346,692,1728,3456,6912,13824,27648；保留原到达时刻与收敛末态保存规则，提前停止不为未来帧延算。新原生配置必须以后由describe核实其实际double运算与该表一致。

独立重算A1体积项的S1标量累加，得到1.727999999993599e-21m³，相对其native-style名义体积差3.7047663623415744e-12，在原1e-10容限内；该算术支持没有必要预先放宽体积门槛，仍不等于原生几何PASS。详见static_volume_observer_arithmetic.json。

## 3. 可以复用与不能直接复用的部分

可以复用：原S1矩阵和describe-only模板、原物理/平均/时间/保存规则，原2%解析验收条件；已接受A1的质量helper、体积项舍入及原mass_stats.h；原检查器已有d0解析K/速度剖面分支、几何枚举、实际场读取和完整质量/统计窗/来源保护。原check_results.py按family决定仅H75做旧回归，因此S1不应伪造h75同几何历史轨迹。

但当前执行包直接复用不兼容，源码定位与SHA见compatibility_findings.json：

1. **C01：原生捕获器固定57600节点。** 原生steady在初态测量前就构建DensityCapture，measure逐格append；S1要求884736节点。按当前源码，其上界保护会拒绝多出的节点。这是源逻辑推断，本轮没有制造一次失败运行。
2. **C02：来源修订明确仅S0。** revision.py要求stage==S0_REGRESSION；新合同只改为S1无法通过。该限制是正确的已有阶段边界，不能删除它或给S0许可改名。
3. **C03：启动控制器只接受S0两条身份及3600s。** S1原墙钟是14400s，另有两条planned_case_id；现控制器的阶段/身份/资源等固定核对不兼容。
4. **C04：h75专项检查不适用于S1。** 捕获映射、5nm常量、190差异点、11/201份采样与旧D4/v1.2轨迹均专用于h75。S1原合同没有要求复现h75历史，也不能把这些专项缺失写成S1的物理FAIL或虚填专项PASS。
5. **C05：S1准备证据尚未形成。** 当前URV准备链只有规划矩阵与非执行describe模板；没有已审核的S1候选/来源绑定、实际构建、两方向原生安装/初始化与独立场读回、正式身份和执行合同。旧h75零步审计也固定57600节点。

这些是预期阶段接入缺口，未出现新的指令或原始证据矛盾，不触发新的Astra裁定。F04跨阶段汇总仍为独立开放事项：未来必须逐条保留S0/S1各自合同与SHA，不回写旧completion；它不阻止未来单一S1合同的两条验收。

## 4. 最小接入建议与原门槛

建议见MINIMUM_ADAPTATION_DRAFT.md，状态DRAFT_NOT_ADOPTED_NOT_IMPLEMENTED：在新隔离副本中保留A1观察量算术，S1不实例化/调用h75专用捕获器，使用已有capture=nullptr测量路径；保留完整旧统计与补偿列。原URV-v1并未规定S1保存h75的190点密度，S1的h75重放字段应标NOT_APPLICABLE_S0_ONLY，不伪报通过。若另需通用全密度捕获，应另定范围。

同时需精确S1源码修订/构建anchor与S1控制器；只能接受本阶段两条原矩阵身份，原R1/R2及来源/非法输出保护保留，不能加通配白名单。原check_results.py/evidence.py/read_fields.py和科学规则保持字节。原S0源/捕获/合同/接受记录不改；本轮不默认要求重跑已接受S0。未来新构建若出现非预期运算变化，应先停下审查。

每方向必须满足：K解析相对误差严格<2%，速度剖面相对L2严格<2%；补偿质量严格<1e-10、账本差≤1e-13、密度偏离≤1e-6、Mach<.05、Re_H≤.01；末窗std≤1e-6、span≤5e-6、横向通量≤1e-12m²/s、截面相对差≤1e-5；q=.5±1e-10、体积相对差≤1e-10、candidate=installed、fallback/unresolved0、有限/正通量/材料保持、原生/独立退出0。P/T各自验收，另报告方向一致性，不新增P/T差异门槛。

1份D3Q19核心分布为134479872bytes=128.25MiB，是单份核心数组大小，不是总内存或峰值测量；原8GiB地址空间、≥12GiB可用RAM、首批≥100GiB/每条≥8GiB空闲盘、每条4GiB输出预算仍需后续构建/零步和实际启动核查。两条14400s墙钟上限合计8小时只是预算，不是预计完成时间。

## 5. 明确停点

本轮材料审查完成；原S1输入/时间/解析与静态几何一致性通过，S1执行链尚未准备合格。没有新CASE、真实S1run_id、启动合同、编译、原生describe/precheck/initialize/steady、软件测试或求解。S1 NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false（尚未接受，不是已运行失败）。S0_ACCEPTED_NEW_A1_PAIR保持。

下一范围可采用草案：新隔离S1候选的最小接入、构建/软件与限定指令审计，再做两方向明确授权的原生零步和实际场读回，准备封存；正式计算仍单独授权。不能把本审查或S0旧许可当成这些后续动作已获准。

reference_qualified=false、strict_error_bound_established=false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED、submission_ready=false保持。光滑控制即使将来通过，也不直接证明V2对两个未见沟槽条件更准确或挤压应用闭环。旧FAIL、历史唯一归因NOT_ESTABLISHED、F04及外部数据声明范围保持。

本报告采用scientific-writing组织证据，非独立人工科学终审。技能来源沿用本会话已核当前v2：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026), Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents, https://doi.org/10.48550/arXiv.2609.00065；仅为工作辅助出处，不是项目数值证据。本轮未外发项目内容、提交或推送。
