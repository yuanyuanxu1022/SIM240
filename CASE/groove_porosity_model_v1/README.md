# grooveDarcy：从几何与 K 模型生成 OpenFOAM 多孔阻力

适配本机 OpenFOAM Foundation 13（13-ced05121dd03）。独立研究用实现，已编译并通过系数与阻力装配检查；**没有进行新的流场计算、挤压计算或物理验证**。不改变 C01–C04 的冻结源码、运行记录或 SDI-v1 门槛。

核心文件：[子类](src/grooveDarcy.C)、[类声明](src/grooveDarcy.H)、[系数计算](src/grooveTransport.H)、[fvModels 示例](examples/fvModels)。结果入口：[本轮报告](../../docs/reports/Groove_porosity_model_20261030/REPORT.md)。

2026-11-05接续：已有子类沿用，新增[间隙场配置片段](examples/fvModels.gapField)和[宿主创建/更新间隙场说明](examples/HOST_GAP_FIELD.md)。当前源码的隔离编译和代数复核记录见[接续报告](../../docs/reports/Groove_porosity_refresh_20261105/REPORT.md)；不覆盖原程序、原构建日志或GDI01历史结果。

## 物理接口

这里的 K 是深度积分导度（m³），不是通常以 m² 表示的渗透率。平均速度采用液体体积平均 U_f：

```
mesaGap = h                         槽顶间隙，m
H = h + (grooveWidth/period)*depth  流体体积/平面面积，m
J = H U_f                          深度积分通量，m²/s
D_i = H/K_i                        Darcy 阻力系数，m⁻²
S = -mu D U_f                      每单位体积动量源
S/rho = -nu D U_f                  每单位质量加速度源
```

基准 h=75 nm、depth=100 nm、width/period=1/2，H=125 nm。不能把 75 nm 当作换算分子的 H。若宿主的 U 是包络体积上的表观速度，这个接口不能直接使用，需要重新审核平均定义、孔隙率、压力项及守恒方程。

等宽槽模型：K_parallel=((h+depth)^3+h^3)/24；K_perpendicular=(h+depth)^3*h^3/[6*((h+depth)^3+h^3)]。V2 使用已有公布舍入系数，不重新拟合：F_parallel=1/[1+1.7685*(depth/width)^1.6331]，F_perpendicular=1/[1+0.4900*(depth/width)^0.6990]。

模型由 porosityModel 直接派生并注册为 `grooveDarcy`，通过标准 `porosityForce` 调用。每次装配重新计算所有目标单元的 K、H、D。原生标量矩阵采用与 Foundation 13 DarcyForchheimer 相同的迹分裂方式，张量矩阵直接增加 mu D 或 nu D。`force()` 返回正的积分阻力，与原生约定一致；流体右端源项为负，标准 porosityForce 负责相应符号。

## 输入与更新

- `conductanceModel`：`original_local_cubic` 或 `V2_published_rounded`。
- `gapMode uniform`：读取带长度单位的 `mesaGap`；创建对象后固定。
- `gapMode field`：读取宿主已经注册的 `volScalarField`，字段名由 `gapField` 指定；必须是长度单位，宿主负责更新。仅把同名文件放进 0/ 目录不会自动创建字段。模型不推断模具运动，也不从整个计算网格厚度猜间隙。
- `grooveDepth/grooveWidth/period`：创建对象时读取、固定。几何或公式选项修改后重建模型；直接调用此子类的 dictionary read 明确拒绝热重载，避免静默保留旧系数。原生 porosityForce 自身的重读路径可重建子对象。
- `velocityAverage fluidVolume`、`wallResistance totalUnresolved`：必须显式声明。模型不能仅靠这两个字检查宿主方程是否真实遵守，应用审查仍必须做。
- `coordinateSystem`：局部 e1 沿槽，e2 横槽；均匀平面内方向。0°/90°/45°已作代数装配检查；45°没有压力边界或流场验证。
- 不允许另填 `d/f/H`。不包含 Forchheimer 项，不用负 d 特殊倍率补偿。

## 使用限制

1. 第一版仅支持全充液、单相平均模型，xy 平面、z 为 empty 的二维网格。Dzz=0仅是该受约束二维算子的嵌入，不能解释为三维竖向无阻力；三维网格与面外旋转明确拒绝。MPI、运动网格和拓扑变化回调未经运行测试。
2. K/D 已代表总未解析壁面阻力，宿主不能再叠加同一套上下壁无滑移剪切或第二份总 Darcy 阻力。保留面内黏性扩散或惯性会改变方程，需单独审核。
3. 原公式只开放等宽槽/台；V2 进一步限制槽宽120 nm、周期240 nm。正间隙与非负深度仅是数学输入检查，不表示所有输入都属于拟合域或验证域；适用范围仍由论文证据限定。
4. 间隙场更新只更新阻力。动态应用仍须满足 ∂tH+div(HU)=0，并统一运动、储液体积、网格厚度与边界通量。固定厚度网格上的原生 phi=U·Sf 不会自动变成变 H 情况的正确 J 通量。
5. 没有实现液气相权重、润湿、接触线、挤压质量源或总力积分；未安装到 nanrPrint，也未改动系统 OpenFOAM 源码。

## 已完成的检查

- 共享库、原生 OpenFOAM 检查程序和纯系数测试均实际编译。
- 通过运行时选择表加载子类，标准 porosityForce 包装器实际调用通过；未调用 PDE solve()。
- 原/V2、0°/90°/45°、固定/逐单元间隙、同一时间步更新间隙、目标区域外不加阻力。
- 物理动量和除密度动量的标量/张量装配、力输出、包装器负源项；mu/nu缺省时的rho换算路径。
- 光滑极限 K=h³/12、D=12/h²；四个 SDI 主对照输入对应的 K/D 与冻结系数表一致至相对2.23e-16以内。
- 非正/NaN间隙、错误间隙单位、非等宽槽、手填d、错误动量矩阵单位拒绝执行。

这些是代码和装配检查，不是 SDI 流场验收、网格独立性或 V2 预测有效性证明。详细记录：`build/logs/assembly_checks.json`，报告目录有保留副本。开发期两次编译接口错误以及首次包装器缺库错误均保留日志，修正后检查通过。

## 构建与检查入口（不给出仿真启动命令）

先在 shell 加载本机 `/home/dell/OpenFOAM/OpenFOAM-13/etc/bashrc`。`bash Allwmake` 只编译，产物留在 `build/lib` 和 `build/bin`；`python3 -B scripts/check_assembly.py` 只执行短时代数检查。检查网格来自 C04 已有网格的独立副本，没有重建或修改原网格。测试夹具的一半单元为测试 cellZone，一半用于区域外无附加源的检查，不能当成正式物理算例。

应用宿主需在 controlDict 的 libs 中加载本地 `build/lib/libgroovePorosity.so` 的绝对路径，并提供标准 porosityForce 库（测试明确加载 `libfvModels.so`）。`examples/fvModels` 只是配置片段，未提供可启动流场包。标准方程/相/网格设置及缺失的间隙更新与连续性代码必须另行检查。

实现依据为本机 Foundation 13 的 porosityModel、DarcyForchheimer、porosityForce；GPL-3.0-or-later，阻力矩阵分裂依据 OpenFOAM Foundation 2012–2024 源码。在线接口参见 [DarcyForchheimer](https://cpp.openfoam.org/v13/DarcyForchheimer_8H_source.html) 和 [porosityModel](https://cpp.openfoam.org/v13/porosityModel_8H_source.html)。源码本地哈希见本轮报告清单。
