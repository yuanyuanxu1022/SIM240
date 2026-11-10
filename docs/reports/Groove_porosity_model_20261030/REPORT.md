# grooveDarcy 子类已实现并通过编译、运行时加载与阻力装配检查

2026-10-30；本轮用户要求把 K 模型放入 OpenFOAM porosityModel 子类直接计算阻力。交付位于 [CASE/groove_porosity_model_v1](../../../CASE/groove_porosity_model_v1/README.md)。范围为本机 Foundation 13 的独立子类、配置片段和短时代数检查；没有启动流场仿真或接入 nanrPrint 两相案例。

## 物理意义与架构

用户给出的 d_i=h/K_i 在 h 代表与速度定义对应的平均厚度时成立。现有 SDI 定义 U 为液体体积平均，J=HU，故 H=h_mesa+(w/P)*d_g；75nm槽顶间隙、100nm槽深、等宽槽的 H=125nm。代码明确区分 mesaGap 与 H，自动算 K、H、D，禁止手填 d/f/H。K单位m³，D单位m⁻²，每体积源为−μDU，每质量源为−νDU。

类 grooveDarcy 直接派生 porosityModel，按运行时选择表注册。标准 porosityForce 包装器可加载它。系数计算与源项装配分为两个小文件，未改动 OpenFOAM 安装源码。原公式/V2公式与公布舍入常数来自已有 [接口说明](../Shared_transport_interface_20261030/CONDUCTANCE_RESISTANCE_INTERFACE.md)。只支持等宽槽，V2进一步限于120/240nm固定槽宽/周期；输入数学有效不等于落入经验验证域。

gapMode=uniform读取固定槽顶间隙；gapMode=field在每次装配读取已注册的长度字段，支持逐单元差异和同时间步更新。宿主必须创建/更新该字段。局部x为沿槽，局部y为横槽；支持均匀平面内旋转。第一版要求xy二维empty网格，Dzz=0仅为受约束算子的嵌入，不建立竖向模型。壁面总阻力不能与已解析同一套无滑移厚度剪切或另一份总Darcy源叠加。

这一子类不提供∂tH+div(HU)=0、运动边界、液气相处理或载荷积分。间隙变化会改变阻力，但不会自动产生对应的排液；固定网格的phi也不会自动完成变H通量换算。空间变化/动态耦合与宿主平均定义必须作为后续单独问题检查。

## 实际执行证据

- 共享库 libgroovePorosity.so、检查程序 auditPorosity 和纯系数程序 testTransport 均实际编译，产物位于新包 build/。
- 动态加载共享库，经 porosityModel::New 和 fvModel::New 的标准 porosityForce 路径装配。检查程序没有solve调用或时间推进。
- 2种公式×3个角度(0/90/45°)×2种间隙输入；场模式在同一时间步由75nm更新为交替50/100nm。检查标量矩阵、张量矩阵、积分力、包装器右端负源项和区域外无源项。物理/除密度动量以及mu/nu缺失的替代路径分别检查。
- 正常、缺mu、缺nu三组各202752个标量断言通过。这是批量装配断言数量，不是独立物理验证数量。7类非法输入得到预期错误：零/负/NaN间隙、错误间隙单位、非等宽槽、手填d、错误矩阵单位。
- 纯系数41项检查包括平板极限K=h³/12与D=12/h²、基准V2值及非法几何。
- 四个SDI主对照系数与冻结表逐项对照，最大相对差2.220446049250313e-16。装配测试允许相对2e-11，系数检查1e-12；这是新代码单元检查容差，不修改原SDI-v1或任何科学Gate门槛。

具体命令、退出码、耗时、源码哈希与系数源哈希见 [assembly_checks.json](logs/assembly_checks.json)，编译及每次检查日志同目录。正常检查程序全部返回0；预期非法输入返回非零并匹配具体错误原因，未把任意崩溃当作拒绝通过。

开发期间首次编译发现Foundation13没有dimViscosity符号，改为显式长度平方/时间维度；测试程序首次包含已不提供的fvCFD.H，改用所需头文件；首次标准包装器测试缺少libfvModels.so的加载，测试夹具补齐。日志全部保留；cellZones头部类别也改为cellZoneList，最终正常日志无上述警告/错误。没有掩盖初次失败或改验收阈值。

## 状态与边界

```text
source_implemented: true
compiled: true
runtime_selection_tested: true
standard_porosityForce_assembly_tested: true
gap_field_refresh_tested: true
new_flow_run_id: null
flow_solved: false
NUMERICAL_GATE: NOT_EVALUATED
RESULT_PASS: false
geometry_PASS: null
physical_validation: NOT_EVALUATED
independent_human_acceptance: false
```

这些Gate值仅针对新子类尚未开展的流场验收，不能覆盖C01–C04已有的局部接口PASS。C04报告及四例原记录保持；本轮保护368份原包/协议文件，内容哈希全部不变，见 [preservation_verification.json](preservation_verification.json)。C01历史几何识别记录、其他历史FAIL不变。reference_qualified=false、strict_error_bound_established=false、submission_ready=false和预测HOLD保持。

未验证：该子类求出的压力/流量、一般网格精度、45°压力边界、空间变H的连续性、挤压体积变化、MPI、运动/拓扑变化、真实沟槽独立参考、V2新条件预测和物理准确性。虽保留基类网格回调接口，不能据源码存在声称运动网格已通过。

下一具体动作是为该子类另准备标准动量方程下的最小定间隙接入协议，并与已验收静态结果对照；应用方向若改成挤压，先审核间隙更新、连续性和力定义。没有本轮之外的长算授权，未准备或启动C05、其他正式流场或下一Gate，也未提交推送。

进度与交接已同步至 [SIM240_AI_CONTEXT.md](../SIM240_AI_CONTEXT.md) 和 [AI_HANDOFF_20261015.md](../AI_HANDOFF_20261015.md)。更新前副本及差异在本目录，后续历史节保持。完整文件清单见 source_manifest.json。

## 接口来源

依据本机 OpenFOAM Foundation 13 的 porosityModel、DarcyForchheimer 和 porosityForce；本轮在线核对 [DarcyForchheimer 源项与单位](https://cpp.openfoam.org/v13/DarcyForchheimer_8H_source.html)、[porosityModel接口](https://cpp.openfoam.org/v13/porosityModel_8H_source.html)，实际编译以本机头文件为准。新实现声明GPL-3.0-or-later，矩阵分裂保留上游来源说明；未修改系统库。
