# OpenFOAM 子类及间隙依赖接续核实

日期：2026-11-05。用户要求将本项目K模型放入porosityModel子类，以实际间隙直接计算多孔阻力。

**结论：当前项目已经有完成该职责的 `grooveDarcy : public porosityModel`，本轮核对并隔离重编译、运行时加载和代数装配复核通过。沿用既有子类，不重复造类、不改原/V2公式或模型系数。补齐了实际间隙场配置与宿主字段接入说明。没有启动新流场计算或将它安装到未指定的实际宿主。**

## 物理量与调用关系

本项目K是深度积分导度，单位m³；OpenFOAM线性Darcy系数D单位m⁻²，源项为−μDU，除密度后为−νDU。本机及在线Foundation13原生[DarcyForchheimer说明](https://cpp.openfoam.org/v13/DarcyForchheimer_8H_source.html)已核。在线[porosityModel接口](https://cpp.openfoam.org/v13/classFoam_1_1porosityModel.html)与本机实际编译接口分别核对。

用户所写 `d_i=h/K_i` 的分子需与速度归一化一致。当前实现采用液体体积平均速度U，J=HU，因此：

```text
h = mesaGap                         最小间隙
H = h + (grooveWidth/period)*depth  液体体积/平面面积
K_i = K_i(h, depth, width)          深度积分导度
D_i = H/K_i                        多孔阻力系数
```

若用户式中的h指这个平均厚度H，表达一致；若h指最小间隙，不能直接代入分子。基准h75nm、槽深100nm、等宽槽对应H125nm。H不是仅因使用OpenFOAM就自动等于网格厚度，实际宿主仍须采用同一平均与守恒定义。

实际路径为：宿主注册/更新mesaGap长度场 → 标准porosityForce → grooveDarcy每次装配读取各单元当前h → 原公式或已公布舍入系数V2 → K、H、D → 坐标旋转 → 阻力矩阵。原/V2的总K都包含h，不能把“V2修正因子仅含d/w”误说成“V2总K与h无关”。

核心位置：

- [grooveTransport.H](../../../CASE/groove_porosity_model_v1/src/grooveTransport.H)：原/V2、H、D的直接计算。
- [grooveDarcy.C](../../../CASE/groove_porosity_model_v1/src/grooveDarcy.C)：已注册间隙场查询、逐单元刷新、方向旋转、μ/ν装配。
- [grooveDarcy.H](../../../CASE/groove_porosity_model_v1/src/grooveDarcy.H)：直接继承porosityModel并注册选择类型。

## 本轮最小改动

1. 新增[间隙场配置](../../../CASE/groove_porosity_model_v1/examples/fvModels.gapField)：gapMode=field、gapField=mesaGap，示例槽向为全局y；没有手工d/f/H。
2. 新增[宿主间隙字段说明](../../../CASE/groove_porosity_model_v1/examples/HOST_GAP_FIELD.md)：给出创建volScalarField的代码位置、更新顺序、J/H/U含义及动态连续性缺口。
3. README增加上述入口和本轮记录。
4. `scripts/check_assembly.py`补一行创建build/logs目录。新隔离目录中首次检查已执行正常代数程序，但在写日志时因目录不存在退出1；原失败见[checks.log](checks.log)，不当作物理或仿真失败，不删日志。修正后10类检查全部通过，见[checks_attempt2.log](checks_attempt2.log)。

没有改子类或系数计算C++源码；没有重编覆盖原build/lib或build/bin。隔离工作目录为 `tmp/groove_porosity_refresh_20261105/CASE/groove_porosity_model_v1`；现有网格和冻结系数只复制到该目录作测试夹具，不修改原网格、不新建正式run_id。

## 实际验证与范围

- 本轮实际重新编译共享库、原生OpenFOAM装配检查程序和纯系数检查程序：[compile.log](compile.log)。源码与隔离复制件逐份一致。
- 原公式/V2、0°/90°/45°、固定间隙与间隙场、同一时间步内更新间隙、区域外无阻力、标量/张量装配、正积分阻力与包装器负源项、mu/nu替代读取路径均由既有原生代数检查运行覆盖。检查程序没有PDE solve或时间推进。
- 正常、缺mu、缺nu三组及七种非法输入，共10类均得到预期结果。非法输入保留各自非零退出与具体拒绝原因；不把任意崩溃当通过。
- 41项纯系数检查通过，包含光滑极限K=h³/12、D=12/h²。四项原/V2与两槽向对照匹配冻结系数，最大相对差2.220446049250313e-16。
- 新配置通过本机foamDictionary实际语法读取：[field_dictionary_parse.log](field_dictionary_parse.log)。它仍是配置片段，不是完整可启动算例。
- 新检查摘要：[verification.json](verification.json)、[logs/assembly_checks.json](logs/assembly_checks.json)。本轮没有重做既有GDI01流场验收；已有C01—C04/GDI01历史证据仍按各自原范围解释。

这些结果说明本机Foundation13下代码/单位/方向/间隙刷新/装配接口可用，不是原/V2精度、连续参考或真实压印过程验证。旧源码、原库和已冻结案例保护核对见preservation_verification.json；历史FAIL与reference_qualified=false等状态不变。

## 实际使用仍需对应的宿主

当前支持全充液、单相、xy二维empty、流体体积平均和总未解析壁面阻力。把K中的总壁阻再叠加到已解析同一套无滑移厚度剪切上，会重复计阻；三维、液气相权重、运动网格和实际nanrPrint求解器需要另按宿主方程核对，不能由本轮编译自动放行。

对固定h，现有uniform模式即可；对变化h，宿主必须先创建并更新字段再装配阻力。变化h若用于挤压，还必须处理∂tH+div(HU)=0、储液体积和边界通量。子类刷新D没有自动实现这些方程。本轮未提供新的运动规律或仿真启动命令。

本次要求在“porosityModel内部直接根据几何/间隙计算K和阻力”这一范围已由既有实现加本轮复核满足。后续接入特定应用时，先确认实际宿主路径/版本/速度与厚度定义，再做其最小字段接入及方程审查；本轮不自行扩大到两相/动态过程，不启动下一Gate或正式流场。
