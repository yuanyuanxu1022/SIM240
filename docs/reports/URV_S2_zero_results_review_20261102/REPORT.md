# S2 六配置零步审计：独立结果复核与 B 封存

日期：2026-11-02，时间均为北京时间。结论：**18次已有原生零步记录、六配置几何及初态统计、六个实际保存场的独立复核全部通过；已另存关闭执行许可的B封存。没有重新求解、性能推进或正式计算。**

## 1. 范围与证据链

用户授权“按原 URV-v1／MRP／A1／S2-MIP-v1 独立复核已有零步审计结果，合格后另存 B 封存；不重跑、不进入性能推进或正式计算。”本次没有执行原生describe/precheck/initialize/steady，只调用既有独立字段读取器六次，读取已保存VTK。分析脚本review_zero.py与所有新结果保存在本报告目录，原源码、旧输出及原门槛未改。

- 审计号URV_S2_ZERO_20261102_01。真实零步release SHA `4b6759d061bc59079556c3a3b4bb34a7a8970b2f6529d4fa0cebeb1bdc1925c0`；1586项绑定输入、真实授权、S0/S1前置、真实构建/依赖及同一S1 ELF均核对通过。
- 原A SHA `320d1d8469e2db50db161f91bca20339e60cb9054875722e9cbb50d9ab236e62`保持，未覆写。原ELF SHA `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`保持。
- 原始审计清单234项哈希逐一相符；加清单自身和工作程序verification，共236个文件，库存无缺项或额外文件。18条progress逐条与工作程序records相同，原始退出与实际模式独立核查，未仅采用PASS标记。
- 六次新字段读取均实际使用/usr/bin/pvpython及冻结的独立read_fields.py，输出放本目录；退出均0，单帧step/time=0，原始payload闭包及字段积分与原读取收据完全一致。使用同一冻结独立读取方法，不声称新增另一种物理算法。

## 2. 原生调用、资源与几何

18份独立退出码均0，process_receipt均无超时/资源停止、原时限300s内完成；execution_audit均preparation_only_build=0、collide_and_stream_calls=0。describe/precheck/initialize各6次，身份、方向、配置/manifest与原矩阵完全对应；没有diagnostics或S0专用mass_capture。首次及逐条资源记录满足原12GiB可用内存、初始100GiB/逐条8GiB磁盘要求。8GiB地址上限由已绑定控制器实施，本轮未测量进程RSS峰值。

几何为h60/d80/w120/P240/Ly240 nm。槽顶/槽底液层厚度60/140nm，平均液体厚度H=100nm；名义液体体积5.76e-21 m³。x/y周期与固定壁面下，独立枚举核心材料、解析壁面交点、原生壁面链及真实字段中的核心格点一致。所有candidate=valid=installed，fallback/unresolved=0，原生与独立q均满足0.5±1e-10。

下表每格的P/T初态统计相同，分别独立核对。J单位m²/s，是初态主轴通量，不是稳态导度：

| dx / nm | 每方向核心节点 | 每方向壁面链 | 核心体积相对误差 | 初态J / m²/s | 初态Mach |
|---|---:|---:|---:|---:|---:|
| 5 | 46,080 | 30,528 | 5.794e-13 | 2.0833333333e-14 | 3.007e-10 |
| 2.5 | 368,640 | 122,496 | 4.038e-12 | 5.2083333333e-15 | 3.759e-11 |
| 1.25 | 2,949,120 | 490,752 | 1.771e-11 | 1.3020833334e-15 | 4.698e-12 |

最大体积相对误差1.771e-11，小于原1e-10门槛。三个网格的窗/最大步数仍为648/37632、2592/150528、10368/602112，dt转换按原有理数定义复算通过；这些是待正式运行的参数，不是实际推进步数。

## 3. MRP/A1初态统计核查

依据绑定的observer运算路径，在rho=1初态下用binary64显式FMA复算旧质量顺序累加，用独立math.fsum核对均匀项的补偿质量，并按A1规定的已舍入单元体积逐项累加。六配置旧质量、补偿质量及体积均与原生记录精确相同。结果和逐步运算路径可由review_zero.py及initial_statistics.csv复核。

六配置补偿质量均5.7600000000000002e-18 kg，density_delta=0、最大密度偏离0。旧顺序质量随网格的末位差异被保留，没有回填理论值；它是这里的初态累加差异，不能称作随时间流失的质量。本次0步没有质量守恒时间轨迹，也没有重新证明动态MRP回归。S0专用密度捕获/重放记NOT_APPLICABLE_S0_ONLY，原S0/A1已接受证据仅作前置来源，不虚填S2新密度重放PASS。

初态物理速度含半步体力修正U=a·dt/2，J=H·U；因此初态J不为0且随dt/网格变化，不能把这六个初态通量用于稳态K、方向性输运或网格收敛判断。Mach与该半步修正一致，最大3.007e-10，满足原<0.05守卫。

## 4. 独立六帧读取与双精度切片

六帧的核心材料分类、三维唯一节点覆盖、长度/速度/压力/运动学耗散单位、初态主轴流量和浮点导出误差界全部通过；重复周期层和固体均被排除。各帧核心节点分别对应表中数量。pressure_Pa为周期扰动，初态范围[0,0]；速度/压力/耗散字段有限，耗散非负。没有把非零的初态耗散诊断改写成严格为0。

双精度field_slice每方向行数为960/3840/15360，覆盖所有核心XZ格点，材料1、rho1、pressure0、主轴半步力速度与三个方向的分量均核对；velocity_profile、pressure_profile、energy_dissipation的坐标/覆盖/有限性亦符合初态。

证据：native_review.json、native_calls.csv、initial_statistics.csv；六个field_reread_*.json/log及reader_progress；independent_review_acceptance.json。新旧读取收据的帧数据与payload哈希一致。六次新调用仅为文件读取，不运行LBM碰撞或推进。

## 5. B封存与接口核对

B：`CASE/unseen_v2_reference_S2_reuse_v1/evidence/preparation_B.json`。

SHA256：`2e55f3369f9445e7763ee1f9a87c57f79348d1b332c959bc038c1bcc4739081f`；绑定输入1816项。B包含未改的A、真实零步授权/release、原审计闭包及本轮独立检查文件；另存，不修改A或历史封存。记录18个已完成actual_audit_run_ids，actual_formal_run_ids仍空。元数据依实际证据填写，没有把A中原先空的实际审计身份沿用为已完成状态。

B与原接口的verify_seal/verify_zero_receipt均通过。正式控制器使用B进行默认只读核对退出0、solver_executed=false、simulation_authorized=false、zero_audit_status=PASSED；闭合权限检查分别拒绝把B用作零步或正式执行release。B的native_zero_step_authorized、performance_time_stepping_authorized、simulation_authorized均false，approved_audit_run_ids及正式approved均空。B不是新的启动许可。

B直接绑定本轮机器可读独立复核证据；包含B自身SHA的报告及封存后验证不加入B输入，以避免自引用哈希循环。B_seal_verification.json及最终verification.json单独记录封存核对。

## 6. 独立状态与科学结论边界

| 层次 | 本轮结论 |
|---|---|
| ZERO_STEP_INDEPENDENT_REVIEW_PASS | true |
| ZERO_STEP_GEOMETRY_PASS | true，仅零步接入 |
| 正式NUMERICAL_GATE | NOT_EVALUATED |
| 正式RESULT_PASS | false，未运行/未验收 |
| 正式geometry_PASS | null，未推进正式流场 |
| REFERENCE_QUALIFIED_FOR_CASE | false |
| MODEL_COMPARISON / physical_validation | NOT_EVALUATED |

**本轮通过意味着同一程序在六个几何/方向配置下能正确建立初态、安装壁面并输出可独立读取的数据。** 它不证明稳态收敛、质量时间守恒、导度精度、三网格资格、V2预测改善或12小时可行性。初始化/字段读取耗时不是稳态推进速度证据；性能协议仍需另定实际实施/推进范围。

S0/S1已接受事实、旧v1.2横槽FAIL/380差异、前MRP静态FAIL、HISTORICAL_EXCLUSIVE_ATTRIBUTION=NOT_ESTABLISHED、D4预测HOLD、GDI01及外部历史声明原范围、F04 OPEN保持。原24项正式矩阵仍完成4、剩20，零步不计正式完成项；项目reference_qualified、strict_error_bound_established、submission_ready均false。没有启动性能或正式计算，不自动重跑或进入下一阶段。

下一步可另行审核已采用性能协议与B的兼容性，限定性能标定的最小实现及真实推进授权；本轮只到B封存。科学写作与证据组织使用scientific-writing技能，方法引用沿用S2-MIP-v1主协议末尾；AI独立文件核查不替代人工科学终审或实验验证。
