# 阶段三移动 Bouzidi—LocalPressure 交线兼容性修复报告

## 判定

本轮达到停止条件 **B**：已证明交线 population 读写反馈，并测试了一个不改
OpenLB 库、保留压力开放边界与全部移动 Bouzidi 链接的最小应用层闭合候选；
该候选削弱原交线源但暴露出压力面—x周期拼接线的第二个失稳源，修复 C 未
通过 650 步。因此没有进行约 2000 步
延长观察，也**不能进入单次材料转换账本**。

这不是 10 nm 移动成功报告。所有运行都位于首次 material conversion 之前，
转换数为 0。

## 实际读取、冻结和修改的文件

冻结读取：

- `stage3_boundary_intersection_diagnosis_report.md`，SHA-256
  `58c6882ef49d5298865bae118615eac19843368debde70964b163254a076d6d0`；
- `explicit_piston_boundary_intersection_diag.cpp`，SHA-256
  `ad87bea0cfcc45b8561e60e5d8fc1a95efd47b707538c22410d519a501766505`；
- 原 C 的 `first_anomaly_cell_history.csv`、`threshold_event_cells.csv`、
  `dual_boundary_history.csv`，SHA-256 分别为
  `c9592b...1ba3`、`ff0ca0...8427`、`bc5dc7...5442`；
- 两份 frozen protocol、原 A/B/C 输出；
- 本机 OpenLB 的 descriptor、LocalPressure、momenta、CombinedRLB、streaming、
  Bouzidi PostStream 和 SuperLattice 调度源码。

本轮新增 `explicit_piston_operator_population_trace.cpp`、
`explicit_piston_boundary_intersection_fix.cpp`、本报告及
`boundary_intersection_d3q19_access_table.md`；只在本目录的 `Makefile` 新增两个
独立构建目标。没有修改原诊断程序、原 A/B/C、OpenLB 库或其他阶段目录。

最终诊断源码 SHA-256 为
`81b7880b69461c9918628ad15fea1f4d8bc2c88a638785def98976038b4ce4ed`；
B（首轮）与 v2 运行所用修复源码 SHA-256 为
`b352ea2631fd7f3b7069d0c38940f8e0e2bf052c8a4cbc1c8c029371ffc6c97a`；
v3 C 运行源码 SHA-256 为
`948c1992f1bfe9364cc3332cbcd3d82ff8d5b8a806faac875df77a7feea5fb19`；
最终 v3 B 回归及当前源码 SHA-256 为
`28fe9b9588b9001c38e66328862bbd5705755e272c6569a5980547a30301f69d`
（与 v3 C 仅 run-id 字符串不同）。

## D3Q19、边界访问和实际算子顺序

完整 19 方向、opposite、两个 cell 的邻居材料及算子读写见
`boundary_intersection_d3q19_access_table.md`。本版本 opposite 对为：

`0↔0, 1↔10, 2↔11, 3↔12, 4↔13, 5↔14, 6↔15, 7↔16, 8↔17, 9↔18`。

`SuperLattice::collideAndStream()` 的实际顺序为：

|阶段|本项目实际动作|时间层/邻居依赖|写入及覆盖关系|
|---|---|---|---|
|PreCollide|communicator、已注册 processor/custom task|读当前 t|本例无额外物理处理|
|collision 内 momenta|LocalPressure 用固定 rho=1；从当前 cell 的 `cy=0,-1` populations 计算法向 u 和应力|读 t；不读邻居|只计算矩|
|reconstruction + collision|`CombinedRLBdynamics` 先重构全部 f0..f18，再调用修正后的 BGK collision|读上一步矩；同 cell|写全部 19；OpenLB API 将重构与 collision 融合，应用层不能在两者中间插桩|
|PostCollide|传播 overlap communication 与 processor|读碰撞后 t*|更新传播所需 overlap|
|stream|每个 propagatable population 按 `c_i` rotate|目标 f_i 依赖 `p-c_i`|写 stream 后状态|
|PostStream communication|先同步 processor 邻域|读 stream 后状态|提供 Bouzidi 邻居数据|
|moving Bouzidi PostStream|有效 q 读取边界、solid-side、fluid-side population|读 stream 后本 cell 与邻居|方向12/15/17分别覆盖 f3/f6/f8|
|PostPostProcess|最终 coupling communicator|读 PostStream 后状态|本单 rank 观测 cell 未再变化|
|statistics/output|读取边界 momenta、direct shifted moments、质量和通量|读完成步 n+1|不修改流场|

逐阶段记录通过公开 API 将 `collide()` 与 block `stream()` 分开；没有改库。
OpenLB 融合在同一 collision 调用里的 LocalPressure reconstruction 与 BGK 无法再
细分实测，但其源码内顺序已经核对。

源码依据位置：D3Q19 为 `src/descriptor/definition/common.h`；shifted rho/j 为
`src/dynamics/lbm.h`；LocalPressure flat setter 为
`src/boundary/localPressure3D.h`；压力 momenta 与 regularized stress 为
`src/dynamics/momenta/elements.h` 和 `src/boundary/helper.h`；全19分量重构为
`src/dynamics/dynamics.h` 的 `CombinedRLBdynamics::collide`；Bouzidi 链接回写为
`src/boundary/setBouzidiBoundary.h`；总调度为 `src/core/superLattice.hh`。

## 第一个异常 population 与制造异常的算子

交线 cell `(0,0,15)` 的活动链接是 12、15、17。方向17的闭环为：

1. LocalPressure reconstruction 写 `f17`；
2. stream 将该 `f17` 带入方向17的 solid-side cell；
3. moving Bouzidi PostStream 从 solid-side 读回并覆盖压力 cell 的 opposite
   population `f8`；
4. 下一步 LocalPressure 把 `f8` 作为 `cy=-1` 的已知法向 population 读取，
   再重构包括 `f17` 在内的全部分量。

因此第一个进入未经协调反馈的 population 是 **f8**，首次直接制造该不兼容
覆盖的算子是 **moving Bouzidi PostStream 的 i=17 链接**；LocalPressure 的
all-population reconstruction 是闭环的另一半，二者单独运行均稳定。

逐算子 C 数据的代表值如下。所有 f 都是 shifted population：

|step|阶段|LP uy at `(0,0,15)`|f17|f8|
|---:|---|---:|---:|---:|
|145|collision 后|-5.4638e-3|-5.28373e-3|-4.37309e-3|
|145|stream 后、Bouzidi 前|-1.79190e-2|-1.59090e-7|-7.12908e-6|
|145|Bouzidi 后|-6.01462e-3|-1.59090e-7|**-5.28289e-3**|
|157|collision 后|-1.73017e-2|-1.67055e-2|-1.38219e-2|
|157|stream 后、Bouzidi 前|-5.66758e-2|-2.66433e-7|-2.20695e-5|
|157|Bouzidi 后|-1.90460e-2|-2.66433e-7|**-1.67027e-2**|
|162|collision 后|-2.79680e-2|-2.69914e-2|-2.23300e-2|
|162|stream 后、Bouzidi 前|-9.15817e-2|-3.42722e-7|-3.54773e-5|
|162|Bouzidi 后|-3.07875e-2|-3.42722e-7|**-2.69866e-2**|

step 157 的 `f8` PostStream 单步改变量为 `-1.66806e-2`，是同阶段
`f3 (-3.41070e-3)` 和 `f6 (-8.57761e-4)` 的数倍。无 q 的首报警 cell
`(0,0,14)` 在 step 157 经过 stream 后达到 Mach `0.0503772`，其 PostStream
状态不再被 Bouzidi 改写，说明它是从交线源向下传播后的首个全局门槛事件。

边界 momenta 与直接矩并不相同。例如交线 cell step 157 Bouzidi 后：
LocalPressure 接口给 `rho=1, uy=-0.0190460`，而按 shifted populations 恢复为
`rho=1.0344161, Mach=0.0434406`。这正是节点压力矩与链接回写状态不一致的
量化证据；不能用 `rho=sum(f_i)`，本版本必须加 1。

完整 step 145–170、六个局部 cell、每阶段 f0..f18、两种 rho/u/Mach 均在：

- `output/operator_population_trace_C_20260907/per_operator_population_trace.csv`；
- 固定对照在 `output/operator_population_trace_B_20260907/`，严格零场；
- 实际邻域和 q 在 `d3q19_topology_step157.csv`。

## 根因判断

根因已从“边界组合相关”细化为：平面 LocalPressure 是节点级 collision closure，
moving Bouzidi 是链接级 PostStream closure；OpenLB 当前公开 boundary setter 只把
两者独立注册，没有适用于“压力面与移动插值壁相交”的共同 corner/intersection
closure。LocalPressure 写全部 19 个 populations，而 Bouzidi 后写其中 f3/f6/f8；
f8 又参与下一步 LocalPressure 法向矩，形成时间层反馈。

本机 `LocalPressure3D`、`ZouHePressure3D` 和 `InterpolatedPressure3D` 的 setter
都只接受 `DiscreteNormalType::Flat`，未找到可直接选用的 pressure-edge/corner/
moving-wall-intersection API。这里的结论是“当前应用层公开组合缺少共同闭合”，
不是“OpenLB 绝对无法实现”。

## 最小修复候选与代码差异

唯一实施候选：保持压力面、参考压力、全部 q 和全部 moving Bouzidi 链接不变；
把拥有固壁链接的低/高 y 压力交线 cell 从 LocalPressure
材料4/5分到材料6/7，并用本版本 `ZouHePressure` 的 missing-population
reconstruction。其余压力面仍为 LocalPressure。没有裁剪 q/rho/u、没有质量
归一化、没有改粘度/时间尺度、没有封闭出口或改实体材料。

代码差异摘要：

- 新增交线材料6/7及唯一边界归属；
- 新增固定阈值、原始质量、两端有符号通量和梯形积分质量收支；
- 新增 `(0,0,14)`、`(0,0,15)` 全 population 历史；
- 新增非法 q、交线归属和材料变化审计；
- 没有节点材料转换调用。

首版候选把所有邻接压头的压力交线都归入6/7，失败记录保存在
`output/boundary_intersection_fix_C650_20260907/`。v2 将判定严格限制为
`c_z>0` 的已定位移动水平壁链接，并修正“基底 Bouzidi 也被计为移动交线”的
审计口径；物理结果未改善，失败记录在
`output/boundary_intersection_fix_C650_v2_20260907/`。v2 的首超限点转移到
压力面—固定基底交线，说明非零流动下固定 Bouzidi 交线也需要共同闭合。
因此 v3 仍沿用同一候选，只把材料6/7扩展到所有压力—固壁交线（含基底）；
失败记录在 `output/boundary_intersection_fix_C650_v3_20260907/`。

## B-650 回归

最终回归 run-id `boundary_intersection_fix_B650_v3_20260907`，原 LocalPressure + 固定
Bouzidi，不启用候选：

- 650/650 步，退出码0，PASS；
- max Mach=0，rho=[1,1]，max speed=0；
- 初末原始流体质量均 `7.1999999999946862e-18 kg`；
- 两端累计外流=0，最大及最终相对质量收支残差=0；
- 非有限值、非法 q/link、材料转换均为0，材料场不变。

故原 B 基线没有退化。

## 修复 C-650

权威结果采用覆盖全部压力—固壁交线的最终 run-id
`boundary_intersection_fix_C650_v3_20260907`：

- 完成650步，退出码3，**FAIL**；没有 NaN/Inf，但发生巨大有限值爆发；
- step 209 首次 Mach>0.05，位置 `(0,0,13)`、material 4、
  `h=74.9991154 nm`、Mach=`0.0505617`；step 236 首次 rho 越过[0.8,1.2]；
- 650步 max Mach=`9.43345e11`，rho范围已扩展到
  `[-5.48391e11,4.35299e11]`，max speed位置为 `(47,47,13)`、material 5；
- 非法 q/link=0，交线归属错误=0，材料转换=0，材料场不变；
- 初始原始流体质量 `7.1999999999946862e-18 kg`；650步质量、出口积分及
  相对质量残差已发散到非物理量级，不能判守恒通过；
- `(0,0,14)`、`(0,0,15)` 仍出现反向速度增长，见两个 cell history CSV。

与原 C（Mach step157、rho step182、NaN step583）相比，v3 把首 Mach/rho
事件分别延迟52/54步，并在650步内避免NaN，但仍远不满足冻结阈值，不能据此
判兼容性修复成功。更关键的是，v3 首报警 `(0,0,13)` 没有 Bouzidi q，位于
LocalPressure 压力面与 x 周期拼接线；原 top 交线 `(0,0,15)` 在 step209 的
Mach 仅 `8.54e-4`。所以原 `f17→f8` 双边界环已被明显削弱，剩余爆发不能再
全部归咎于该环，而需单独审查非零流动下的 pressure–periodic seam 闭合。
程序退出码明确为3，没有把“跑满650步”写成物理通过。

## 延长观察、步骤4与下一步

修复 C 未通过650步，因此按冻结顺序没有运行约2000步延长观察。用户所称
步骤4通过条件（650步无非有限、Ma<=0.05、rho合格、无非法/遗漏链接、无转换、
B不退化且局部不再放大）**未达到**。

下一步**不可以**进入“单次材料转换账本”。若继续，只建议一个具体小诊断：
对 v3 首报警 `(0,0,13)`、其 x 周期对端 `(47,0,13)` 及高 y 对应 cell 做与本轮
相同的逐算子 trace，同时在 PostCollide/PostStream communicator 前后分别取样，
确认 LocalPressure reconstruction 的哪一个 population 在跨 x 周期后首先不一致。
在该 seam 问题排除前，不应继续设计压力—固壁8未知联合闭合，更不应进入材料转换。
