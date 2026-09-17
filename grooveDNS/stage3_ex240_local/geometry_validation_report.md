# EX240 局部静态几何验证报告

## 1. 执行结果

独立程序 `geometry_generator.cpp` 已编译并以

```text
./geometry_generator --run-id static_h65_dx5 --h-nm 65 --dx-nm 5 --overlap 3
```

运行，退出码为0，所有离散检查通过。随后只读取VTI生成截面和平面图。程序源码中不存在 lattice、`collideAndStream`、液滴初始化或移动压头逻辑。

## 2. 参数分级

### 用户已确认

- x周期240 nm；左半凸台 `[0,60) nm`，中央凹槽 `[60,180) nm`，右半凸台 `[180,240) nm`；
- 凹槽宽120 nm、深100 nm；上方为带槽压头，下方固定平板；
- 坐标为基底 `z=0`、凸台底面 `z=h`、槽顶 `z=h+100 nm`。

### 本轮几何检查参数

- `h=65 nm`，仅为静态材料样本；
- `dx=5 nm`、y周期长度240 nm；
- z向基底支撑厚20 nm、压头背衬厚20 nm、上下外部padding各15 nm；
- overlap=3 cells作为未来OpenLB接入元数据。overlap/周期ghost没有写入物理VTI，也不计入材料体积。

### 正式压印仍待确认

初始1000 nm、最终65 nm、位移−935 nm及运动时间均未确认为局部显式工况；供液体积/形状、接触角、气体模型和实际材料物性也未确定。本轮没有把52 µm宏观液滴缩放或初始化。

## 3. 坐标与离散定义

VTI使用CellData。节点面坐标为 `x=i·dx`、`y=j·dx`、`z=−35 nm+k·dx`；材料单元中心为 `(i+1/2)dx`、`(j+1/2)dx`、`−35 nm+(k+1/2)dx`。网格为48×48×47个物理单元。

因为所有名义边界都是5 nm的整数倍，有效体素面与名义壁面完全重合：`x=60,180 nm`，`z=0,65,165 nm`。本结果没有声称更一般分辨率也会精确重合；程序会拒绝不能整除边界的输入，而不是悄悄移动壁面。

| 尺寸 | 名义值 | 离散值 |
|---|---:|---:|
| 左半凸台 | 60 nm | 12 cells |
| 中央凹槽宽 | 120 nm | 24 cells |
| 右半凸台 | 60 nm | 12 cells |
| 凹槽深度 | 100 nm | 20 cells |
| 测试间隙 h | 65 nm | 13 cells |

## 4. 材料和拓扑检查

材料计数为：外部padding 13,824；内部可用空间52,992；固定基底9,216；压头32,256个单元。实体和外部区域分别编码，没有把padding误标为流体空间。

- 周期缝左60 nm与右60 nm拼接为120 nm完整凸台：通过；
- 中央凹槽24 cells=120 nm：通过；
- 凹槽深度20 cells=100 nm：通过；
- 在 `z=h/2` 上，材料1贯通全部x单元，证明 `h>0` 时凸台下间隙与槽内空间横向连通：通过；
- x/y为周期、z非周期；完整x边界没有被标成实体墙：通过。

这也说明阶段二连续实体墙模型的 `Bxx≈0` 不能转移到本几何。

## 5. OpenLB接口边界

实现前核对了本机 `/home/dell/openlb` 的实际接口：现有阶段三使用 `CuboidDecomposition::setPeriodicity({true,true,false})`、`Mesh::setOverlap(3)`、`SuperGeometry`和`SuperVTMwriter3D/SuperGeometryF3D`。本轮为了保证这是纯几何、无lattice状态的可审计导出，生成器直接写标准VTI材料CellData，并在参数中显式记录未来OpenLB周期性和overlap；没有虚构动态材料API。

现有M3只保留为字段级转换/回滚参考。真实动态材料重分类、边界动力学、分布函数重建和overlap同步仍属于S3-B，不因本次静态VTI通过而视为完成。

## 6. 输出与限制

- `output/static_h65_dx5/ex240_material.vti`：材料场；
- `output/static_h65_dx5/geometry_parameters.csv`：确认/测试/待确认参数及离散尺寸；
- `output/static_h65_dx5/validation.txt`：机器可读检查证据；
- `xz_section.png/.pdf`、`xy_plan.png/.pdf`：带单位和尺寸标注的图。

本报告只验证一个规则周期单胞的静态材料定义。没有证明动态转换守恒、润湿、困气、真实供液或最终压印状态，也没有运行任何流体仿真。
