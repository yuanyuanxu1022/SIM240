# 阶段三静态几何真实 OpenLB 接入报告

日期：2026-09-06  
正式 run-id：`openlb_static_h65_dx5_10step_final`

## 1. 结论

已把确认后的 EX240 单胞几何接入本机真实 OpenLB `SuperGeometry` 和 `SuperLattice`，使用D3Q19、x/y周期、z向固定半程反弹固壁。单相全充液以格子密度1、零速度、零体力初始化，并完成恰好10步真实 `collideAndStream`。所有流体节点的密度和速度均为有限数；质量相对漂移为0，最大物理速度为0，材料计数逐步不变。

这是固定几何初始化与基本推进检查。零速度平衡态保持不变不能单独证明移动边界、材料转换、受驱动流动或FreeSurface准确性。

## 2. 体素几何检查与性质说明

此前的 `geometry_generator.cpp` **没有使用 OpenLB**：它只构造一个C++体素数组，并直接写出标准VTI CellData。它没有 `SuperGeometry`、`SuperLattice` 或 `collideAndStream`。其用途是独立验证名义材料布局，不得称为真实lattice接入。

原体素样本采用48×48×47 cells，z向包括15 nm外部padding、20 nm基底厚度和20 nm压头背衬；材料计数为：外部13,824、内部可用空间52,992、基底9,216、压头32,256。所有体素均采用单元中心定义，`x=60/180 nm`、`z=0/65/165 nm`落在体素面上。

## 3. 真实 OpenLB 材料和边界接入

新增的 `static_lattice_integration.cpp` 使用本机 `/home/dell/openlb` 的实际API：

- `CuboidDecomposition<T,3>`，并实际调用 `setPeriodicity({true,true,false})`；
- `SuperGeometry<T,3>`，overlap=3；
- `SuperLattice<T,D3Q19<>>`；
- 流体材料1使用 `BGKdynamics`；固定基底材料2和压头材料3使用 `boundary::BounceBack`；
- `SuperGeometryF3D`/`SuperVTMwriter3D`输出真实OpenLB材料场。

OpenLB core网格为48×48×38个节点。物理节点中心为：

- x、y：2.5–237.5 nm，步长5 nm；周期长度240 nm；
- z：−2.5–182.5 nm，步长5 nm；
- 流体中心范围：x/y 2.5–237.5 nm，z 2.5–162.5 nm。

材料计数：流体52,992；固定基底2,304；压头32,256；core内没有材料0。固体合计34,560。overlap的三层块padding由OpenLB管理，统计统一使用 `forCoreSpatialLocations`，没有将ghost/overlap重复计入材料数量。

### 与独立体素结果的差异

| 项目 | 独立体素VTI | 真实OpenLB core | 解释 |
|---|---:|---:|---|
| x×y | 48×48 | 48×48 | 一致 |
| 流体节点 | 52,992 | 52,992 | 一致 |
| 压头节点 | 32,256 | 32,256 | 一致 |
| 基底节点 | 9,216 | 2,304 | 体素图为绘图保留4层、20 nm基底；OpenLB只需一层z=−2.5 nm反弹节点 |
| 外部/padding | 13,824个显式材料0 | core内0；overlap=3由框架管理 | 两种padding语义不同，不能强求总节点数相同 |

因此材料总数不同不是几何失败；用于流动的可用空间和压头离散完全一致，而OpenLB固壁采用最小一层实体节点及框架overlap。

### 周期与拓扑

在 `z=102.5 nm` 的一条实际OpenLB格点线上，节点计数为左固体12、中央流体24、右固体12。x周期连接使右端60 nm半凸台与相邻单胞左端60 nm半凸台组成120 nm完整凸台。x/y边界没有改为实体材料。

在 `z=32.5 nm=h/2`，全部48个x节点均为流体，确认凸台下间隙将中央槽内空间沿x连通。因此不能直接套用阶段二连续墙模型的 `Bxx=0`。

### 有效壁面位置

使用半程BounceBack，壁面位于相邻流体与固体节点中心的中面：

- 基底：固体中心−2.5 nm、流体中心2.5 nm，实际壁面 `z=0`；
- 凸台底面：流体中心62.5 nm、固体中心67.5 nm，实际壁面 `z=65 nm`；
- 槽顶：流体中心162.5 nm、固体中心167.5 nm，实际壁面 `z=165 nm`；
- 侧壁：节点中心分别位于边界两侧±2.5 nm，实际壁面 `x=60,180 nm`。

本测试参数下名义壁面和有效壁面完全重合；这依赖 `h`、深度和宽度均能被5 nm网格对齐。

## 4. 10步时间推进结果

构建命令：

```text
make openlb-static
```

运行命令：

```text
./static_lattice_integration
```

OpenLB版本宏为 `5953d8a-dirty`，单MPI rank；`dx=5 nm`，`dt=1×10⁻¹² s`，运动黏度基线为 `1×10⁻⁶ m²/s`。这里的物性只为数值推进配置，不是正式EX240树脂工况。

| 指标 | step 0 | step 10 | 全程判断 |
|---|---:|---:|---|
| 流体节点 | 52,992 | 52,992 | 不变 |
| 固体节点 | 34,560 | 34,560 | 不变 |
| 格子质量Σρ | 52,992 | 52,992 | 相对漂移0 |
| 物理质量（ρ=1000 kg/m³） | 6.624×10⁻¹⁸ kg | 6.624×10⁻¹⁸ kg | 不变 |
| ρ范围（格子单位） | [1,1] | [1,1] | 有限 |
| 最大物理速度 | 0 m/s | 0 m/s | 有限 |
| 材料场 | 初始计数 | 相同 | 每步检查均不变 |

时间序列覆盖step 0–10，最终物理时间 `1×10⁻¹¹ s`。x/y周期性已设置在实际 `CuboidDecomposition`，z固壁已作为材料2/3的BounceBack动力学接入。均匀零速度平衡态没有产生伪流或密度扰动。

两次早期构建失败均发生在执行前：第一次因手写C++17/头文件参数不符合本机OpenLB，第二次因OpenLB默认构建会链接目录内两个独立`main()`。最终Makefile增加了只选择本测试翻译单元的 `openlb-static` 目标；详情保存在 `build_record.txt`，没有删除既有体素程序或结果。

## 5. 输出证据

- 源码：`static_lattice_integration.cpp`；构建：`Makefile`；
- 构建记录：`build_record.txt`；
- 参数、命令、退出码：`output/openlb_static_h65_dx5_10step_final/run_record.txt`；
- 运行日志：同目录 `integration.log`；
- 逐步统计：`lattice_statistics.csv`；
- 坐标和拓扑检查：`openlb_geometry_validation.txt`；
- 真实OpenLB VTK：`vtkData/data/openlb_static_geometry_iT0000000.vtm`及其VTI块文件。

## 6. 尚未验证

本轮没有加入FreeSurface、自由界面、液滴、接触角、重力/体力、移动压头或质量重分配，也没有长时间运行。尚未验证：

- S3-B动态材料转换、边界动力学切换、分布函数初始化、周期overlap同步和转换守恒；
- S3-C真实供液体积/形状、润湿、槽填充、受压横向流动及气体处理；
- 非零驱动下的速度/压力精度、网格收敛和多MPI rank一致性；
- 宏观1000 nm、65 nm、−935 nm到局部显式工况的正式映射。

因此结论只限于：确认几何已在真实OpenLB固定材料场中正确接入，并通过10步零场基本推进检查。
