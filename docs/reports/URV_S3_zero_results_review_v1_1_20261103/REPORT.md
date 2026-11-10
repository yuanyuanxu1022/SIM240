# S3 v1.1 零步12＋4完整独立复核与关闭权限的B封存

日期：2026-11-03 15:23:52 +08:00。结论：**十二次原生零步、四配置几何及初态统计、四份保存场重读全部通过；已另存执行权限关闭的准备B。没有重跑求解器，也没有启动正式计算。**

用户范围：“按原 URV-v1／MRP／A1／S3 v1.1 完整独立复核已有12＋4结果，合格后另存执行权限关闭的准备 B；不重跑、不启动正式计算”。本轮使用peer-review技能组织项目内部证据审查；属于AI辅助技术复核，不是人工科学终审。本轮最初进度说明“不重新读取场文件”过窄，已在实际分析前说明改为四次只读保存场重放；它们属于独立结果分析，不是再次执行十二次原生审计，不推进LBM。所有新读回与分析输出均保存在本报告目录。

## 1. 协议与来源完整性

审计身份URV_S3_ZERO_v1_1_20261103_01，四配置为U_REG、h60/d80/w120/周期240/Ly240nm、平均H100nm、dx2.5nm；rho1000kg/m³、nu1e-6m²/s、tau1，P沿槽+y、T横槽+x，a50000/200000m/s²。J=核心速度体积分/平面面积，单位m²/s；K=nu J/a，单位m³。本轮没有从初态J评价稳态K或模型。

零步执行合同SHA dbe8b8a4ee33806e7d7ceeeaea0ec76ad68985fbb51851bcb0d3cae7dbd28f42及2451项输入逐项一致；原准备A SHA7f6ca19de96949a537802f92804c787cf092e8de0eb10c681ed279736a2d3695及2437项输入保留；原v1 A/HOLD与2339项旧输入保留。原S1 ELF SHA5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b及真实构建/依赖/限定指令链通过原来源验证，没有重编译或新增反汇编结论。

原S2合同及两个中档基准仍按自身来源核验，P K=5.919337058277595e-23、T K=2.3663885892433063e-23m³，未改写为S3下的新结果。外部数据历史仍限定为作者声明未用h60/d80、h30/d80结果选系数或条件，不升级为外部独立审计。

原始审计清单156项全部一致；含清单自身及总收据共158文件，实际文件集合无新增/漏失/替代。2602项既有输入、源码、旧报告与原始输出前后指纹一致。

## 2. 十二次调用与R1/R2内容重验

十二条均为真实既有describe/precheck/initialize，各四条；run_id、planned_case_id、mode、输出目录、manifest、原A指纹及授权逐项关联。原生独立process_receipt、exit_code.txt与execution_audit交叉一致：退出0、无超时/资源停止、原时限300s内完成、collide_and_stream_calls=0、preparation_only_build=0。十二份progress与总收据records逐项一致。无steady diagnostics或S0 mass_capture。未补写不存在的控制器父进程独立退出码。

R1逐实际effective参数核对方向、a、dx、nu、h/d/w/周期、dt、面积/体积、网格与窗/上限及formal=false；a_lat换算与初态半步响应对应，原始物理、平均口径及科学门槛未改。

R2逐记录重读全部零步原始文本与读取器证据，四份读回路径/身份唯一，均属于自身初始化目录；重建各自PVD→VTM→VTI闭包并核对payload指纹、帧0、节点、单位、数组、通量及导出舍入界。实际调用原冻结检查器的完整verify_zero_receipt与共享zero_evidence，且额外独立核对precheck result、时间资源、初态算术和双精度切片，没有用摘要PASS代替内容核对。

原资源记录满足MemAvailable≥12GiB、首条磁盘≥100GiB/后续≥8GiB，每次输出≤4GiB。1进程/1线程/1cuboid、overlap3、8GiB地址上限由已绑定控制器实现；本轮没有实测历史进程峰值RSS。两个读取阶段的300s预算分别记录，不把初始化后检查开销当作原生求解时长。

## 3. 几何、质量、体积与初态响应

八份precheck/initialize几何均从解析矩形槽独立枚举重算：368640核心流体节点、122496条候选/有效/安装壁面链；material0/1/2/3为0/368640/9216/184320。原生q_min/q_max均0.5；独立交点枚举最大0.5000000000000036，与0.5差约3.55e-15，满足原±1e-10。所有fallback/unresolved为0。

四初始化体积均5.7599999999767373e-21m³，相对解析体积的偏差约4.04e-12，小于原1e-10。独立逐节点重放A1的dx³舍入及顺序相加得到完全相同结果，没有以解析体积回填。

初始旧质量均5.7600000000297481e-18kg。独立按MRP规范，以rho=1、实际double dx、三个先行舍入乘法及最终math.fma逐节点累加，结果精确相同；补偿初始质量均5.7600000000000002e-18kg，亦与独立稳定求和精确一致。density_delta及max_density_deviation均0。旧质量末位偏差是初始空间累计的舍入差，不是时间流失；零步没有动态质量轨迹，不宣称重新证明动态MRP回归。

每份双精度XZ切片3840行、乘ny96覆盖368640节点，坐标/材料/密度/零压力、各速度分量和三类剖面通过。初态运动只含半步体力响应U=a dt/2，dt=1.0416666666666667e-12s，因此J=H a dt/2。

|方向|a/(m/s²)|原生初态J/(m²/s)|保存场重读J/(m²/s)|初态Mach|
|---|---:|---:|---:|---:|
|P|50000|2.6041666666496735e-15|2.6041666600917789e-15|1.879395408e-11|
|T|50000|2.6041666666496735e-15|2.6041666600917789e-15|1.879395408e-11|
|P|200000|1.0416666666598694e-14|1.0416666640367116e-14|7.517581630e-11|
|T|200000|1.0416666666598694e-14|1.0416666640367116e-14|7.517581630e-11|

低/高力解析初态J分别2.604166666666667e-15、1.041666666666667e-14m²/s；原生相对差约6.53e-12，保存场差异满足原float32导出舍入界与半步响应容差。高力是低力4倍，两方向初态相同是初始化响应的预期，不能据此判定稳态各向同性或S3线性控制通过。初态Mach均远低于0.05；该事实不替代正式过程中全程Mach/Re、收敛和质量验收。

双精度初态Phi为微小非负数，原值及范围留在initial_statistics.csv；未将初始化舍入量解释为真实稳态壁面耗散机制。S0专用密度捕获/重放记NOT_APPLICABLE_S0_ONLY，本轮没有新增h75密度重放。历史唯一归因NOT_ESTABLISHED及旧FAIL不改。

## 4. 四份保存场的实际独立重读

四次pvpython独立退出0、无超时，各读1个step0帧；各帧唯一核心节点368640、数组material/velocity_m_s/pressure_Pa/dissipation_m2_s3齐全，物理单位、固液位置、核心去重、压力零、有限与非负耗散均通过。每份PVD/VTM/VTI三个载荷文件，完整引用指纹与原报告一致。

每份新报告与对应原报告整个JSON内容精确相同，包括帧统计、通量、导出舍入界、版本、单位及payload指纹。原字段无run_id/units通用键并非漏证：检查使用冻结格式中的velocity_units等专门字段、固定路径与payload闭包，不要求凭空增加字段。

四次新调用只读原始文件，所有输出另存；脚本对允许创建的子进程作白名单限制，只允许当条pvpython/read_fields命令，任何原生求解器/其他命令均拒绝。没有重跑原生describe/precheck/initialize或steady。

## 5. B封存与权限检查

准备B：`/home/dell/yuanyuanxu/SIM240/CASE/unseen_v2_reference_S3_reuse_v1_1/evidence/preparation_B.json`

SHA256：`a5b69ec95180bf92327a3bba1311639dd2a5fb1bec412cd80c3869dda2a47f92`，侧文件为preparation_B.sha256；绑定2609项输入。

B包含原A、零步真实授权/执行合同、原始审计全部证据及本轮独立复核脚本、验收、切片/统计摘要、新读回与进程记录。原A和原执行合同保持；B另存，未修改被冻结脚本。12个actual_audit_run_ids按真实已完成证据填写，actual_formal_run_ids为空；批准列表全部清空。B包含自身SHA的本报告/封存后验证不加入B输入，避免自引用。

B kind=S3_PREPARATION_B_NOT_AUTHORIZATION，zero_audit_status=PASSED；ZERO_STEP_INDEPENDENT_REVIEW_PASS=true、ZERO_STEP_GEOMETRY_PASS=true。simulation/formal/native_zero/performance与initial_field_readback权限均false。AI不启动、用户手动及不重试/加时/下一阶段边界保持。

B通过verify_seal、来源、原始零步总收据与实际记录/载荷核对；正式控制器默认只读退出0、solver_executed=false、simulation_authorized=false、zero_audit_status=PASSED。明确权限拒绝：formal S3 release required；separate zero-only release required。故B不是再次执行零步或正式计算的许可。

## 6. 科学边界与停点

本轮接受的是四配置的真实零步接入、几何与初态证据；不是正式稳态单条验收。正式NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false（未运行而非计算失败），S3_CONTROL_PASS=NOT_EVALUATED。新的ZERO_STEP_GEOMETRY_PASS与以上正式字段分别记录。

REFERENCE_QUALIFIED_FOR_CASE/reference_qualified=false，MODEL_COMPARISON/physical_validation=NOT_EVALUATED，strict_error_bound_established/submission_ready=false。S0/S1/S2已接受证据、旧v1 HOLD、旧横槽FAIL/380项差异、前MRP静态FAIL、历史唯一归因未建立、F04 OPEN和旧PERF日志例外全部保留。未放宽0.1%线性门，也未重拟合V2或使用新点挑条件。

本轮原生求解器调用0、时间推进0、构建0；独立保存场读取4次。CASE只新增B和SHA侧文件，源码/配置/旧输入/原始输出未改；其余新文件在本报告目录，共享状态/交接已维护。没有交付正式启动命令、没有启动正式四条、性能或S4/S5。

下一具体动作：另行审定正式S3四条执行范围、资源和授权绑定前条件；原顺序低P→低T→高P→高T、每条14400s及原独立检查/线性门保持。四条求解预算16小时、检查及文件处理另计，是上限预算而非预计耗时。本轮不生成正式执行合同或启动命令。

证据入口：review_existing.py、native_review.json、native_calls.csv、initial_statistics.csv、四份field_reread_*.json/log、reader_*_process.json、independent_review_acceptance.json、seal_B.py、B_seal_verification.json、final_integrity.json、report_manifest.json。共享入口docs/reports/SIM240_AI_CONTEXT.md及AI_HANDOFF_20261015.md。
