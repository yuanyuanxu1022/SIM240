# SIM-EC1XT240 STEP 5 单次材料转换账本验证报告

> Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is `SIM-EC1XT240`.

## 判定

**STEP 5 FAIL。** 第一次真实`fluid -> solid`事件按几何预测发生，程序也完成了转换后500步，
但转换瞬间出现非物理的Mach和密度跃升，且移动控制体积质量残差超过冻结的`1e-3`门槛。
退出码3是验收失败，不是PASS。

没有修改OpenLB库、STEP 4基线、物性、tau、dt、壁速、轨迹、Zou/He压力、moving Bouzidi、
192条周期固壁link修复或验收门槛。没有进入第二次材料转换或完整10 nm运动。

## 程序与运行

- 独立程序：`explicit_piston_single_conversion_ledger.cpp`；
- STEP 4冻结基线SHA-256：`9444c61aab6cc67499211f2724d109923d91d9bc0fe66747446acf2da5e399e2`；
- STEP 5程序SHA-256：`24f31902eb2e8d7b566354424551a56d9918f01308368755641811c6ee5aa5eb`；
- 正式诊断run-id：`single_conversion_ledger_v2_20260908`；
- 命令：`mpirun -np 1 ./explicit_piston_single_conversion_ledger`；
- OpenLB运行版本：`5953d8a-dirty`；
- 完成step 4095，即转换后500步；退出码3。

`single_conversion_ledger_v1_20260908`完整保留。v1暴露了两个诊断实现问题：刚体平移使
凸台底面和槽顶同时跨过节点中心，故预测数不是1152而是2304；压力边界的转移核对应读取
population直接矩，不能只用其固定rho momenta返回值。v2只修正这两项诊断并增加受影响
receiver逐population记录，没有改变物性或运动。

## 首次转换事件

转换发生于：

- step：`3595`；
- 物理时间：`3.595e-8 s`；
- `h=72.4989847248 nm`；前一步`h=72.5005751172 nm`；
- 当前切割层`alpha=0.499796944965`；
- 转换节点：`2304`，与刚体几何预测一致。

事件不是单个孤立cell。凸台底面的`iz=15, z=72.5 nm`有1152个节点，槽顶的
`iz=35, z=172.5 nm`也有1152个节点同时转换。材料来源为：material 1共2208个，
低端material 4共48个，高端material 5共48个，全部转为material 3。按字典序首个事件
cell为lattice `(0,0,15)`，物理坐标`(2.5,2.5,72.5) nm`。

转换前后共11708条局部Bouzidi固壁link完成所有权平移，单个转换cell对应3、4、5、7或9条
link；旧/新总数均为11708。新q约为`0.999796944965`，均在合法范围，`max_illegal_links=0`。

## 转换状态处置与账本

新程序没有删除质量或全域归一化。对每个转换cell，按当前连续几何的`alpha`取得其
geometry-aware质量和动量，将19个完整population按守恒权重分给下一层持久流体邻居，随后：

1. 将源cell材料由1/4/5改为3；
2. 将源cell dynamics改为`NoDynamics`；
3. 同步SuperGeometry和lattice overlap；
4. 重建周期感知Bouzidi距离及壁速字段；
5. 执行collision、streaming和PostStream。

转移的geometry-aware质量为`1.47606903859e-19 kg`。v2的population直接矩账本相对差为
`1.58419e-4`（相对于本次转移质量），没有达到程序冻结的`1e-12`逐转换账本要求。这一差异
集中来自Zou/He压力cell的“指定rho momenta”与其shifted populations直接和并不完全相同；
因此该状态映射不能判为守恒转换实现。

## 首个异常cell、population与link

首个明确异常在转换重分配后、collision之前已经存在：

- receiver lattice：`(13,47,34)`；
- 物理坐标：`(67.5,237.5,167.5) nm`；
- material 5，高y端Zou/He压力边界；
- 它位于新转换槽顶cell的下一层，同时获得新的moving Bouzidi固壁link；
- q约`0.999796944965`，link本身合法。

该cell的OpenLB shifted `f0`由`0`跃迁到`0.172152281043`，是绝对变化最大的population；
19个population总增量约`0.52509`。由于Zou/He仍指定`rho=1`，其boundary momenta把这批
新增population解释为强法向速度，collision前已得到`u_y=0.5241847381`、
`Mach=0.907914599`。这不是单个q非法，而是**转换重分配首先制造了与固定rho压力闭合不相容
的population状态**。

首次collide/stream/PostStream后，同一cell仍有`u_y=0.3460053510`、
`Mach=0.599298848`。此时关键值包括`f0=0.1721522810`、`f3=0.0323807106`、
`f8=0.0011898019`和`f17=-0.0024068287`。因此首个制造异常的操作是转换population重分配；
Zou/He momenta/collision把不相容状态转化为强法向速度，后续streaming/Bouzidi传播异常。

完整before、after-transfer及首个collide/stream后的19分量均保存在
`conversion_population_before_after.csv`，没有裁剪异常值。

## 转换后500步

|量|结果|判定|
|---|---:|---|
|完成步数|转换后500步|完成|
|非有限值|0|通过|
|非法link|0|通过|
|材料转换计数|2304/预测2304|通过|
|最大Mach|`1.085249925`（step 3641）|失败|
|rho范围|`[0.837008053,1.561065783]`|失败|
|最终`R_geom_macro`|`7.633616e-3`|失败|
|最终`R_geom_population`|`8.331094e-3`|失败|
|最大绝对`R_geom_macro`|`7.633616e-3`|失败|
|累计macro流入/流出|`1.279765e-18 / 1.463536e-18 kg`|已记录|
|累计population流入/流出|`1.993230e-16 / 1.995118e-16 kg`|已记录|

最大Mach发生在step 3641；最大rho发生在step 3682，最小rho发生在step 3741。虽然全过程
保持有限并完成500步，但Mach、rho、转换账本和质量残差均未达到冻结要求，不能因程序完成
或退出过程正常而判PASS。

## 结论与下一步边界

本轮已验证：首次刚体材料转换事件能够在正确step修改真实SuperGeometry材料、dynamics和
Bouzidi链接，且转换数量和几何预测一致。然而当前“将cut-cell剩余population直接分配给
持久邻居”的应用层状态映射与Zou/He固定rho压力cell不兼容，是转换瞬间异常的确定来源。

下一步仍应停留在STEP 5，只设计压力cell专用、矩一致的保守转换闭合，并分别验证质量、
动量及未知incoming populations的唯一来源。不得把本结果用于完整10 nm，也不得进入液滴、
润湿、空气或下一次材料转换。

**STEP 5 SINGLE MATERIAL CONVERSION FAIL**
