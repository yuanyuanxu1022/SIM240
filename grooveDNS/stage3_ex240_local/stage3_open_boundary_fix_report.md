# 固定开放边界初始化修复报告

日期：2026-09-07  
结论：**失败节点已定位，但固定基线尚未通过；未运行移动测试。**

## 实际失败节点

新增诊断在调用LocalPressure前使用OpenLB自身的 `computeBoundaryTypeAndNormal` 枚举压力节点，并保存物理坐标、原材料、类型、法向和六邻域材料。

- 压力节点总数：2400；
- 合法节点：2340，低y端法向 `(0,-1,0)` 1170个，高y端 `(0,1,0)` 1170个；
- 失败节点：60，两个压力面各30个，均位于 `x=2.5 nm`（低x周期缝）或 `x=237.5 nm`（高x周期缝）的可用高度；
- 这些节点返回 `DiscreteNormalType::Flat(0)`，但法向是非法的 `(0,0,0)`；
- 其跨x邻居在BlockGeometry padding中仍显示材料0，因而被默认 `outsideI=material 0` 当作外部，而不是周期另一侧的压力节点；
- 它们不是基底/压头实体节点，不能改为固体，也不能跳过，否则x周期压力面将留下缺口。

逐节点证据见失败run目录中的 `boundary_node_diagnostic.csv`。

## 源码依据

`localPressure3D.h`只支持Flat类型；`getDynamics()`对其他类型抛异常。更直接的异常来自 `setBoundary3D.h` 的方向构造器：只接受六个单位轴法向，零法向在else分支抛出 `Could not set Boundary.`。

通用 `boundary::set` 使用传入的fluid/outside indicator调用 `computeBoundaryTypeAndNormal`。当前默认材料0 outside indicator没有表达“x padding应周期绕回”的语义，故周期缝压力节点得到零法向。OpenLB微通道/后向台阶示例都使用可识别的完整入口/出口平面；没有找到示例会在零法向节点上静默跳过压力边界。

## 已尝试修复与结果

1. 首次失败run `open_drain_fixed_h75_20260907`：便捷setter初始化异常，0步；已保留。
2. `fix1`：先按类型把非Flat节点划为明确固壁交线。诊断显示所有节点类型均为Flat，因此没有节点被重分类，仍失败。
3. `fix2`：显式调用新式LocalPressure接口并传入压力、流体、outside indicators。由此排除重载歧义，但60个零法向节点仍失败，0步。

没有执行任何 `collideAndStream`，没有移动压头。

## 正确的最小后续修复

必须在本目录实现周期感知的outside indicator：对y外侧返回outside，对x方向的周期padding不返回outside，并使x缝压力节点稳定得到±y法向；或者只对这60个节点显式安装与所在端一致的±y LocalPressure动力学。两种方案都必须验证跨x周期邻居确实同步，且同一节点只有压力动力学，不叠加固壁。

不能采用以下伪修复：把60节点改成固体、跳过节点、关闭x周期、或把零法向硬报为Flat通过。

## 基线结果

固定h=75 nm基线仍为未通过：完成0步，无可用速度、密度、通量、质量或守恒残差结果。移动测试未启动。本轮没有修改OpenLB库或其他阶段目录。
