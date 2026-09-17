# 阶段三移动 Bouzidi—LocalPressure 交线诊断报告

## 结论

首次数值失稳已定位到低 y 开放压力面与移动压头 Bouzidi 边界交线及其直接邻近格点，而不是材料转换：

- A（移动Bouzidi＋封闭侧边界）在650步内稳定；
- B（固定Bouzidi＋LocalPressure）在650步内严格保持零场；
- C（移动Bouzidi＋LocalPressure）在step 157首次超过Mach=0.05，step 182首次越过ρ范围，step 583首次出现NaN/Inf；
- 所有工况均禁止材料转换，C失稳时h仍为74.98 nm，远未到首次格点转换。

因此可明确排除“移动Bouzidi本身必然失稳”和“静态LocalPressure本身失稳”。在本机当前处理器组合及几何下，失稳需要**移动Bouzidi与LocalPressure同时存在**，源区是两者的交线节点。

这不是10 nm移动成功报告。本轮只完成边界组合故障定位。

## 独立诊断程序与共同设置

新增 `explicit_piston_boundary_intersection_diag.cpp`，没有覆盖 `explicit_piston_10nm.cpp`。程序使用真实OpenLB `SuperGeometry`、`SuperLattice`、`LocalPressure3D`和`BouzidiVelocityPostProcessor`，复用已验证的 `PeriodicXOutside`。

三个工况共同使用：`dx=5 nm`、`dt=1e-11 s`、`tau=1.7`；x周期、基底固定、初始ρ=1、u=0、零体力；v2五次轨迹的名义总运动时间仍为`1e-7 s`。诊断只运行到step 650，此时`h=74.9751455 nm`，位移仅0.0248545 nm，远小于到首个材料转换所需约2.5 nm。程序不存在材料转换调用，三个结果均记录`conversion_nodes=0`。

OpenLB版本宏为`5953d8a-dirty`，Git commit为`882924a9cfc8dcdf82909e39530789cb6f5ebcc4`。最终诊断源码SHA-256为`ad87bea0cfcc45b8561e60e5d8fc1a95efd47b707538c22410d519a501766505`。

## A/B/C消融结果

| 工况 | y侧边界 | Bouzidi壁 | 首次Mach超限 | 首次ρ超限 | 首次NaN/Inf | 650步结论 |
|---|---|---|---:|---:|---:|---|
| A | 材料4/5改为BounceBack，非LocalPressure | 按五次轨迹移动 | 无 | 无 | 无 | 稳定 |
| B | 原等参考压力LocalPressure | 固定h=75 nm、壁速0 | 无 | 无 | 无 | 稳定、零场 |
| C | 原等参考压力LocalPressure | 按五次轨迹移动 | 157 | 182 | 583 | 失稳 |

A的最大Mach为`5.32772e-4`、最大物理速度`0.153798 m/s`，ρ总范围约`[1,1.001958]`；B的速度为0、ρ为1。C最终发散至非有限值。A、B与C除被消融的边界条件/壁运动外，几何、converter、时间范围、q更新和异常门槛一致。

第一批诊断曾把A中的材料4/5仅按材料号误标为LocalPressure；该批文件已重命名为`*_label_bug_preserved_*`保留。最终程序改用实际dynamics RTTI判断LocalPressure并重新运行。`dual_boundary_history.csv`中A只有表头、B/C各有真实双重作用节点。`global_extrema.csv`中的`dual_cells`列实际是“材料4/5上有Bouzidi链接的候选数”，A中不应解释成LocalPressure双重节点；双重作用的权威字段是逐cell文件中的`is_LocalPressure/is_Bouzidi/is_dual`。

## 第一个异常cell与相邻链接

C在step 157的第一个门槛异常为：

- lattice坐标 `(ix,iy,iz)=(0,0,14)`；物理坐标`(2.5,2.5,67.5) nm`；
- material 4，实际dynamics RTTI包含`FixedPressureMomentum<1,-1>`，即低y端LocalPressure；
- ρ=1，格子速度`(0,0.0290853,0)`，Mach=`0.0503772`；
- 该cell自身没有有效q，所以不是Bouzidi处理cell。

它正上方一格 `(0,0,15)`、物理坐标`(2.5,2.5,72.5) nm`才是交线源cell：

- material 4，同时`is_LocalPressure=1`、`is_Bouzidi=1`、`is_dual=1`；
- 有效链接为D3Q19的12、15、17，即`(0,0,+1)`、`(+1,0,+1)`、`(0,+1,+1)`；
- step 157的三个q均约`0.499924`，对应壁速系数均约`-1.42390e-6`；q合法且接近0.5，不是越界q；
- 该交线cell的LocalPressure约束使ρ保持1，但其y速度反向增长，step 162自身Mach达到`0.0533255`。

这说明第一个超限格点位于交线cell直接下方，而污染源可进一步定位到交线cell的移动Bouzidi链接与LocalPressure碰撞/正则化组合。不能简单表述为“同一离散链接同时是压力链接和固壁链接”：压力条件是节点dynamics，Bouzidi是该节点上的特定固壁方向PostStream链接；二者在同一交线cell、同一时间步中先后作用。

## 异常前20步局部历史

下面摘录首次异常cell `(0,0,14)` 的完整21步记录；完整19个stored populations、19个q和19个壁速系数见CSV。OpenLB的`cell[i]`是其内部shifted population存储值，本报告不把它误称为未移位的物理占据量。

| step | rho | uy(lattice) | Mach | f5 | f6 | f11 | f12 |
|---:|---:|---:|---:|---:|---:|---:|---:|
|137|1|0.00418570|0.00724984|2.25832e-5|-1.00611e-4|1.41427e-4|1.11774e-5|
|142|1|0.00680376|0.0117845|3.64765e-5|-1.61833e-4|2.30908e-4|1.73786e-5|
|147|1|0.0110500|0.0191391|5.88326e-5|-2.60502e-4|3.76405e-4|2.70516e-5|
|152|1|0.0179331|0.0310610|9.47839e-5|-4.19586e-4|6.12777e-4|4.21827e-5|
|156|1|0.0264052|0.0457352|1.38723e-4|-6.14589e-4|9.04214e-4|6.02786e-5|
|157|1|0.0290853|0.0503772|1.52571e-4|-6.76151e-4|9.96483e-4|6.59210e-5|

对应交线cell `(0,0,15)` 的uy从step 137的`-0.00278973`增长至step 157的`-0.0190460`，Mach从`0.00483195`增至`0.0329887`；step 162达到`0.0533255`。两个相邻压力cell呈相反y速度并指数式放大，而q只从约0.499950平滑变至0.499917、壁速系数数量级仅`1e-6`。这正是边界组合产生非物理反馈的局部证据。

首次ρ异常发生于step 182的内部邻近cell `(0,1,14)`，物理坐标`(2.5,7.5,67.5) nm`，ρ=`1.20232`、Mach=`0.292613`。首次NaN/Inf发生于step 583的低y LocalPressure cell `(0,0,9)`，物理坐标`(2.5,2.5,42.5) nm`，uy与Mach为NaN。三类门槛事件的完整f/q/边界标志保存在`threshold_event_cells.csv`。

## 当前最可能根因

最可能根因是：低y交线cell同时使用`LocalPressure`的固定密度/正则化压力dynamics和移动`BouzidiVelocityPostProcessor`，PostStream壁面修正产生的切向/法向非平衡分布在下一步被压力dynamics重构，形成一对相邻压力cell之间的非物理正反馈。依据为：

1. A证明相同移动q和壁速在非LocalPressure侧壁下稳定；
2. B证明相同LocalPressure及静态q交线严格稳定；
3. C的首个异常紧邻真实dual cell，dual cell随后5步越过同一Mach阈值；
4. q合法、连续，且没有材料转换、无非法链接。

该结果定位了组合故障，但还没有证明是LocalPressure碰撞公式、PostStream调度次序或角点缺少专用闭合中的哪一行公式；不能据此宣称OpenLB绝对无法实现。

## 下一步最小修复候选（不超过3项）

1. **交线专用节点/链接划分**：仅在独立程序中把压力面内部保持LocalPressure，将固壁交线节点改为本机明确支持的边/角闭合，并逐链接保证压力与Bouzidi唯一归属；先运行同一650步A0诊断。
2. **将压力截面与移动压头交线空间分离**：增加局部静态储液缓冲结构，使压力平面边缘接固定壁而非移动壁；必须明确新增区域和质量积分范围，不能仅延长y而保留同一交线。
3. **若公开API不能表达上述划分**：申请最小库级能力，在`setBouzidiBoundary.h`及BlockLattice PostProcessor容器中按节点/链接标签启停处理器，以构造可审计的交线专用调度；修改前另行审批。

本轮没有直接实施这些修复，也没有继续完整10 nm移动。

## 文件

- 程序：`explicit_piston_boundary_intersection_diag.cpp`
- A：`output/boundary_intersection_diag_A_20260907/`
- B：`output/boundary_intersection_diag_B_20260907/`
- C：`output/boundary_intersection_diag_C_20260907/`
- 全局时序：各目录`global_extrema.csv`
- 交线逐cell时序：`dual_boundary_history.csv`
- 异常前历史：C目录`first_anomaly_cell_history.csv`
- 三类首次事件：C目录`threshold_event_cells.csv`

所有旧静态、固定压力基线、10 nm失败记录和原程序均保留；未修改OpenLB库或其他阶段目录。诊断进程均已正常结束。
