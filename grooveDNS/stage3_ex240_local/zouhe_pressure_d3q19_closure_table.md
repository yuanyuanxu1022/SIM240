# 本机 OpenLB D3Q19 Zou/He pressure closure 表

本表对应本项目实际 OpenLB `5953d8a-dirty`、提交
`882924a9cfc8dcdf82909e39530789cb6f5ebcc4`，不是外部版本推断。

## 实际实现路径

- API类型：`src/boundary/zouHePressure3D.h` 中
  `boundary::ZouHePressure<T,DESCRIPTOR,MixinDynamics>`。
- 注册：`boundary::set(...)`，见 `src/boundary/setBoundary.h`。本项目使用显式
  `boundaryI`、fluid material indicator和周期感知outside indicator。
- 仅支持 `DiscreteNormalType::Flat`；其他类型返回空，邻域半径为1。
- dynamics：`ZouHeDynamics` + `BasicDirichletPressureBoundaryTuple`。
- 密度：`BasicDirichletPressureBoundaryTuple` 使用 `FixedDensity`，通过
  `SuperLattice::defineRho(...)`写入其外部 `RHO` 字段。本轮等参考压力取rho=1。
- collision：`src/boundary/zouHeDynamics.h` 的 `ZouHeDynamics::collide` 调用
  `util::subIndexOutgoing`得到5个未知population，仅对这5项进行非平衡反弹重建；随后只对
  其中4个斜向项作切向动量修正，最后调用原BGK collision operator。
- postprocessor：`ZouHePressure::getPostProcessor`返回空；注册时只因邻域半径1把相关点加入
  boundary communicator。moving Bouzidi仍是独立的PostStream processor。

`util::subIndexOutgoing<direction,orientation>`先选取
`c_direction=orientation`的出射项，再返回它们的opposite。因此：

- 低y面法向 `(direction=1, orientation=-1)`：未知入射项满足 `c_y=+1`；
- 高y面法向 `(direction=1, orientation=+1)`：未知入射项满足 `c_y=-1`。

## 19方向闭合表

“LP读取”指 `FixedPressureMomentum` 和 `RegularizedBoundaryStress` 用于法向矩/应力的
已知集合；LocalPressure随后由 `CombinedRLBdynamics`重建全部19项。Zou/He“重建”仅指
进入BGK前的未知项重建；普通BGK collision随后仍会更新所有populations。

| i | c_i | opp | 低y：streaming状态 | 低y Zou/He重建 | 低y LP读取 | 高y：streaming状态 | 高y Zou/He重建 | 高y LP读取 | 与方向12/15/17 Bouzidi关系 |
|---:|---|---:|---|---|---|---|---|---|---|
| 0 | (0,0,0) | 0 | 已知/本地 | 否 | 是 | 已知/本地 | 否 | 是 | 无 |
| 1 | (-1,0,0) | 10 | 已知 | 否 | 是 | 已知 | 否 | 是 | 无 |
| 2 | (0,-1,0) | 11 | 已知出射 | 否 | 是 | 未知入射 | **是，法向项** | 否 | 无 |
| 3 | (0,0,-1) | 12 | 已知 | 否 | 是 | 已知 | 否 | 是 | 方向12 Bouzidi写f3 |
| 4 | (-1,-1,0) | 13 | 已知出射 | 否 | 是 | 未知入射 | **是，斜向项** | 否 | 无 |
| 5 | (-1,1,0) | 14 | 未知入射 | **是，斜向项** | 否 | 已知出射 | 否 | 是 | 无 |
| 6 | (-1,0,-1) | 15 | 已知 | 否 | 是 | 已知 | 否 | 是 | 方向15 Bouzidi写f6 |
| 7 | (-1,0,1) | 16 | 已知 | 否 | 是 | 已知 | 否 | 是 | 无 |
| 8 | (0,-1,-1) | 17 | 已知出射 | 否；保留streaming非平衡信息 | 是 | 未知入射 | **是，斜向项** | 否 | 方向17 Bouzidi写f8；低y侧为反馈载体 |
| 9 | (0,-1,1) | 18 | 已知出射 | 否；保留streaming非平衡信息 | 是 | 未知入射 | **是，斜向项** | 否 | 无 |
| 10 | (1,0,0) | 1 | 已知 | 否 | 是 | 已知 | 否 | 是 | 无 |
| 11 | (0,1,0) | 2 | 未知入射 | **是，法向项** | 否 | 已知出射 | 否 | 是 | 无 |
| 12 | (0,0,1) | 3 | 已知 | 否 | 是 | 已知 | 否 | 是 | Bouzidi方向12读侧/链接方向，opp=f3 |
| 13 | (1,1,0) | 4 | 未知入射 | **是，斜向项** | 否 | 已知出射 | 否 | 是 | 无 |
| 14 | (1,-1,0) | 5 | 已知出射 | 否 | 是 | 未知入射 | **是，斜向项** | 否 | 无 |
| 15 | (1,0,1) | 6 | 已知 | 否 | 是 | 已知 | 否 | 是 | Bouzidi方向15读侧/链接方向，opp=f6 |
| 16 | (1,0,-1) | 7 | 已知 | 否 | 是 | 已知 | 否 | 是 | 无 |
| 17 | (0,1,1) | 8 | 未知入射 | **是，斜向项** | 否 | 已知出射 | 否 | 是 | Bouzidi方向17读取f17并写opp=f8 |
| 18 | (0,1,-1) | 9 | 未知入射 | **是，斜向项** | 否 | 已知出射 | 否 | 是 | 无 |

低y面未知集合为 `{5,11,13,17,18}`；高y面未知集合为
`{2,4,8,9,14}`。这来自本机 `subIndexOutgoing` 和实际D3Q19编号。

## 与已发现反馈链的关系

在低y面，`f8`是streaming得到的已知出射population，Zou/He不会在边界重建阶段覆盖它；
`f17`是未知入射population，只由Zou/He闭合。对于方向17的moving Bouzidi link，
PostStream读取该方向侧的 `f17`并写opposite `f8`。所以该population对仍共享物理链接，
但不再发生LocalPressure那种“先用全部已知项构造应力，再重建全部19项”的处理。

第一处局部修复使用的方向12/15/17分别写 `f3/f6/f8`。低y Zou/He重建集合与这些写目标
没有交集；其重建集合包含方向17本身。算子阶段仍必须唯一：collision阶段Zou/He闭合
`f17`，streaming后Bouzidi按固壁链接写 `f8`。是否稳定必须由Z0、Z1、separated和C650
实测判断，不能仅由集合不重叠推断PASS。
