# OpenLB EX240 项目阶段性成果总结报告

## 一、项目目标

项目目标是使用 OpenLB 建立 EX240 的多尺度数值路线：以纳米周期单元获得输运参数，以静态 FreeSurface 验证液滴/界面数值能力，最终再开发宏观压印模型。当前尚未形成完整 EX240 版图压印模型，三类模型必须明确区分。

## 二、阶段一：B_yy 纵向输运

源码 `case.h`/`grooveDns.cpp` 建立 D3Q19、Forced-BGK 单相直沟槽模型。沟槽沿 y，x 方向为实体墙，z 上下为无滑移墙，y−/y+ 周期。体力仅沿 +y，输运系数按 `B_yy=−μ q_y/(dp/dy)=μq_y/(ρa_y)` 计算。

网格结果（`tmp/grid_convergence_exact65.csv`）：

|dx|B_yy|
|---:|---:|
|5 nm|112.4366 nm²|
|2.5 nm|102.3725 nm²|
|1.25 nm|97.6164 nm²|

97.6164 nm²是当前最细网格的离散计算值，不应称为严格网格无关真值。当前缺少正式 Richardson 外推/GCI 或独立解析基准。阶段一还缺少真正的总质量漂移和周期截面通量平衡指标。

## 三、阶段二：B_xx 横向阻断

`CHECK_BXX` 分支施加 +x 体力并将 y 体力置零，固定运行 20000 步。已有结果为：

```text
Qx = 2.375010871854205e-28 m³/s
qx = 6.089771466292833e-15 m/s
max_abs_ux = 1.088960398264679e-13 m/s
Bxx = 6.089771466292834e-27 m²
```

Bxx 在当前数值容差内可视为 0，但该结果验证的是连续实体墙的横向阻断，不是非零横向渗透率标定。

## 四、边界条件与空气

阶段一、二只有 y 周期；x/z 为实体墙 BounceBack，模型是单相直沟槽输运。没有空气相、VOF、自由表面或 trapped-air。周期边界不等于空气出口；当前没有 open/pressure 边界用于局部周期单元，也不存在“版图外部”排气路径。

## 五、阶段三静态 FreeSurface

初始半球/自由球测试显示：原始 1dx 初始化在非零表面张力下早期 EPSILON 越界；官方风格 Indicator/Functor 邻域壳层会造成约 22.55% 体积偏差。随后采用 `8×8×8` 子单元采样估计球-网格体积分数，并改用完整球解析体积 `V=(4/3)πR³=9.047786842338600e-22 m³`。

修复后 Gate A（sigma=0）完成 100 步，初始离散体积误差约 0.00503%，无体积/MASS漂移。Gate B（sigma=0.0309 N/m）完成 100 步和 1200 步；1200 步 `max|u|≈0.00271 m/s`，体积漂移约 −0.238%，MASS 漂移约 −0.204%，Interface 保持单一连通分量，无 EPSILON 越界或 NaN/Inf。该稳定性仍需更长时间、网格和 Laplace 压差验证，不能等同真实空气或压印验证。

## 六、移动压头前置测试

- **M1：已完成。** `movingPistonIndicator` 通过，验证五次平滑轨迹、0→−10 nm 位移、单调下降和固定网格覆盖集合。
- **M2：初步完成。** 能识别 Fluid/Interface→Solid 候选，容量不足时拒绝转换。
- **M3 字段级原型：初步完成。** 独立预设字段测试验证 MASS/EPSILON 守恒、EPSILON 范围和原子性回滚。
- **M3 字段级 FreeSurface 集成：初步完成。** 验证字段同步逻辑，但不是实际 OpenLB 动态 lattice。
- **真实 lattice 动态转换：未完成。** 因缺少安全 API 未进入 T1/T2/T3。

## 七、当前最大技术阻塞

OpenLB 1.8r1 没有公开、安全的动态材料重分类接口，也没有自动重建固流边界链接、overlap/MPI 状态和 FreeSurface 邻域状态的接口。仅写 lattice 字段不能构成真实几何更新；固定壁加速度不能称为移动压头；字段级数组原型不能称为真实 lattice 动态转换。因此当前不能安全实现真实移动压头。

## 八、已完成与未完成清单

|内容|状态|
|---|---|
|阶段一 B_yy 实现及网格序列|已完成|
|阶段二 B_xx 阻断回归|已完成|
|周期/单相边界审计|已完成|
|静态 FreeSurface Gate A|已完成|
|静态 FreeSurface Gate B 1200 步|初步完成|
|精确体积分数初始化|已完成（8×8×8近似）|
|M1 轨迹单元测试|已完成|
|M2 转换识别/拒绝|初步完成|
|M3 质量重分配原型|初步完成|
|真实 lattice 动态节点转换|未完成|
|T1/T2/T3 移动压头|未完成|
|trapped-air、9 滴、1 mm EX240 压印|不适用/未开始|

## 九、论文可用结论

**可以直接写入：** 单相 D3Q19 理想直沟槽的周期输运实现；B_yy 网格序列及当前最细离散值；连续实体墙导致 Bxx 在数值容差内为零；精确体积分数静态自由球在 1200 步内无 EPSILON 越界且速度衰减。

**需加限定：** 97.6164 nm²仅为最细网格计算值；静态 FreeSurface 结果为无 trapped-air 的数值验证；8×8×8 体积分数是高阶采样近似。

**当前不能写：** 已验证完整 EX240 版图、真实纳米沟槽压印、液滴融合/排气、移动压头质量守恒或 trapped-air 压力。

## 十、下一步决策

**A：继续开发。** 新增 `DynamicMaterialMap`、`ConversionTransaction`、`NeighborhoodUpdater`、`MovingBoundary`，完成真实 lattice 单步、平板活塞和 −10 nm T1 验证；开发量大、风险高。

**B：暂停阶段三。** 整理阶段一、二和静态 FreeSurface 成果，补充 GCI/总质量守恒/Laplace 验证后向老师汇报。若论文周期有限，B 更稳妥。

## 十一、给老师的简短汇报摘要

目前已完成 OpenLB 理想直沟槽的 B_yy/B_xx 周期输运验证，并完成静态 FreeSurface 自由球的精确体积分数初始化；在真实表面张力下 1200 步测试稳定。移动压头的轨迹和字段级质量守恒原型已完成，但 OpenLB 1.8r1 缺少安全的动态材料/边界重构接口，真实 lattice 节点转换尚未实现，因此不能声称已完成压印模拟。继续开发需要自定义几何、边界、邻域同步和质量账本模块，工作量和风险较高，请决定是否继续。

## 当前项目状态与证据路径

主要源码/结果：`README.md`、`case.h`、`grooveDns.cpp`、`tmp/`、`stage3_minimal_test/`、`stage3_free_sphere_test/`、`stage3_moving_piston_test/`。关键报告包括：`/tmp/grooveDNS_stage12_audit.md`、`/tmp/stage3_exact_volume_gateB_1200_report.md`、`/tmp/stage3_real_lattice_integration_report.md`、`/tmp/stage3_pretests_autonomous_final_report.md`、`/tmp/stage3_custom_dynamic_freesurface_feasibility.md`、`/tmp/moving_piston_indicator_unit_test_report.md`、`/tmp/moving_piston_conversion_unit_test_report.md`、`/tmp/stage3_M3_freesurface_integration_report.md`。

本报告仅基于现有文件和已有结果整理；生成过程中未运行仿真、未修改源代码、README、阶段一/二结果或 `../tmp/`，未删除任何文件。
