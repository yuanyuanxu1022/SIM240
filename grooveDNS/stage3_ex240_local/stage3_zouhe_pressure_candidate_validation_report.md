# SIM240 阶段三步骤4：Zou/He压力边界第三候选验证报告

## 结论

第三候选的**650步短程门禁PASS**。将整个开放压力面从本机OpenLB的
`LocalPressure`改为`ZouHePressure`后，Z0、Z1、移动壁—压力面分离对照和原始开放
C几何均通过冻结阈值。原始C在step 209越过Mach门槛并随后产生巨大有限值；
Zou/He-C650的全过程最大Mach仅`6.1829116816418037e-05`，rho范围为
`[0.99987883917914711, 1.0002955951371546]`，无NaN/Inf、非法link或材料转换。

这证明第三候选机制获得了当前短程证据支持：问题来自LocalPressure的全population
regularized重建与移动Bouzidi带来的斜向非平衡信息不兼容，而不是LocalPressure一般的
弱非零流能力、直接交线、x周期seam或材料转换。

该结论**不等于步骤4正式验收**，也不是10 nm移动成功。下一步可以进入约2000步的
转换前观察；本轮没有执行该观察。延长观察通过以前，仍**不允许进入步骤5单次材料转换
账本**。

## 实际源码、API与调用路径

本机OpenLB为`5953d8a-dirty`，提交
`882924a9cfc8dcdf82909e39530789cb6f5ebcc4`。本轮没有修改OpenLB。工作树的dirty状态
来自已有未跟踪文件，不是本轮库级改动。

- `src/boundary/localPressure3D.h:38-63`：实际类型为
  `boundary::LocalPressure<T,DESCRIPTOR,MixinDynamics>`；仅接受`Flat`法向，邻域半径0，
  使用`CombinedRLBdynamics`与`momenta::RegularizedPressureBoundaryTuple`，无
  postprocessor。
- `src/dynamics/momenta/aliases.h:152-158`：LocalPressure tuple为
  `FixedDensity + FixedPressureMomentum + RegularizedBoundaryStress`。
- `src/dynamics/dynamics.h:475-517`：`CombinedRLBdynamics::collide`先求rho/u/pi，随后
  对`f0...f18`全部执行`fEq+fromPiToFneq(pi)`重建，再调用嵌套BGK collision。
- `src/boundary/zouHePressure3D.h:35-63`：本版本实际API为
  `boundary::ZouHePressure<T,DESCRIPTOR,MixinDynamics>`；支持D3Q19平面，邻域半径1，
  使用`ZouHeDynamics`和`BasicDirichletPressureBoundaryTuple`，无独立postprocessor。
- `src/dynamics/momenta/aliases.h:190-197`：Zou/He pressure也使用`FixedDensity`和
  `FixedPressureMomentum`，但stress使用`BulkStress`。目标rho由
  `SuperLattice::defineRho(...)`写入外部`RHO`字段；本轮两个压力面均为rho=1。
- `src/boundary/zouHeDynamics.h:87-139`：实际实现用`subIndexOutgoing`得到5个缺失项，
  只对这5项做opposite非平衡反弹重建，再修正4个斜向项的切向动量，随后执行BGK
  collision。这里“只闭合未知项”指**边界重建阶段**；正常BGK collision当然仍更新
  全部19项。
- `src/boundary/setBoundary.h:79-117`：`boundary::set`按实际outside/fluid indicator求
  离散法向、安装dynamics，并按邻域半径把节点加入boundary communicator。

本版本Zou/He setter同样只返回`Flat`处理，不提供通用edge/corner dynamics。当前应用
没有跳过交线节点：沿用已经验证的`PeriodicXOutside`，使x周期padding不被认作外部，
压力面的离散外法向始终由真实y端决定；固体身份仍由材料图和Bouzidi链接保留。原几何
每个y压力面为1200个节点，共2400个，全部交给Zou/He；与固壁链接共存的节点仍有唯一
压力dynamics，固壁链接则由PostStream Bouzidi处理。Zou/He的radius=1通信也由
`boundary::set`注册。

## D3Q19闭合集合

完整19方向、`c_i`、opposite、低/高y面的已知/未知状态、LocalPressure读取以及与
Bouzidi 12/15/17的关系见
[`zouhe_pressure_d3q19_closure_table.md`](zouhe_pressure_d3q19_closure_table.md)。本机编号为：

`0↔0, 1↔10, 2↔11, 3↔12, 4↔13, 5↔14, 6↔15, 7↔16, 8↔17, 9↔18`。

- 低y面，离散法向`(direction=1, orientation=-1)`，Zou/He未知入射集合为
  `{5,11,13,17,18}`，即`c_y=+1`。
- 高y面，离散法向`(direction=1, orientation=+1)`，未知入射集合为
  `{2,4,8,9,14}`，即`c_y=-1`。

在已定位的低y反馈链上，`f8`是streaming得到的已知出射项，Zou/He不会在边界重建
阶段覆盖它；`f17`是唯一由Zou/He闭合的未知入射项。方向17 Bouzidi仍在PostStream
读取链接侧`f17`并写opposite `f8`，但它不再与LocalPressure“由应力重建全部19项”
组成原来的全population反馈。

## 独立候选程序与冻结设置

新增[`explicit_piston_zouhe_pressure_candidate.cpp`](explicit_piston_zouhe_pressure_candidate.cpp)，
并只在本目录Makefile增加`openlb-zouhe-pressure-candidate`目标。它复用既有真实
`SuperGeometry`、`SuperLattice`、D3Q19、BGK、moving Bouzidi、周期感知outside、统计
及192条跨x周期固壁link修复。没有覆盖历史LocalPressure程序或历史输出。

主要冻结量保持为：`dx=5 nm`、`dt=1e-11 s`、`nu=1e-6 m²/s`、`rho=1000 kg/m³`、
轨迹总步数10000（`T=1e-7 s`）、五次平滑75→65 nm轨迹、相同壁速和rho=1压力值。
650步时仅移动到`h=74.975145476312491 nm`，壁速
`-0.01106494436577752 m/s`，材料转换数保持0。

冻结验收：移动案例无非有限值、Mach不超过0.05、rho位于[0.8,1.2]、相对质量收支
残差不超过`1e-3`、非法/遗漏周期固壁link为0、材料不变且发生正的累计净外排；Z0采用
`1e-12`零场/质量残差门槛，Z1采用Mach<0.01、rho位于[0.99,1.01]、质量残差
`≤1e-5`且通量非零。没有事后放宽阈值。

当前归档源码SHA-256为
`3a6f4511ac99c0d60e003d5c4ff16be11fc75cb55c4bac6b7dbec7928cd80763`；完整命令、
退出码、结果哈希及源码沿革见
[`zouhe_pressure_candidate_run_manifest.txt`](zouhe_pressure_candidate_run_manifest.txt)。

## Z0：固定壁、Zou/He、零驱动

run-id：`zouhe_pressure_Z0_zero_fixed_650_20260908`，650/650步，退出码0，PASS。

|量|结果|
|---|---:|
|max Mach / max speed|0 / 0 m/s|
|rho范围|[1,1]|
|初/末质量|均为`7.1999999999946862e-18 kg`|
|两端通量、累计外排、质量收支残差|均为0|
|非法link / 错误周期固壁link / 转换|0 / 0 / 0|
|材料场|不变|

因此新压力边界没有破坏原B类固定零场回归水平；既有LocalPressure B650结果也保持原样。

## Z1：固定壁、弱非零压力流

Z1使用与先前已通过的LocalPressure基准相同的16³域、x/z周期、y压力开放、相同单位
映射与`Δrho=2e-6`。为直接比较最终剖面，另以同一候选程序的`Z1LP`模式复现一次原
LocalPressure闭合；这不是调参。

|量|Zou/He Z1|LocalPressure Z1LP|
|---|---:|---:|
|run-id|`zouhe_pressure_Z1_nonzero_fixed_650_20260908`|`localpressure_fixed_nonzero_profile_650_20260908`|
|650步/退出码/PASS|650 / 0 / 是|650 / 0 / 是|
|max Mach|`5.0152543531662641e-05`|`5.0152542982464496e-05`|
|rho范围|`[0.999999,1.000001]`|`[0.999999,1.000001]`|
|低y向外通量 (kg/s)|`-9.2231111101611328e-14`|`-9.2231110084467759e-14`|
|高y向外通量 (kg/s)|`9.2657777769488787e-14`|`9.2657776754834838e-14`|
|净向外通量 (kg/s)|`4.2666666787745939e-16`|`4.2666667036707916e-16`|
|最大相对质量收支残差|`2.9251079072461844e-14`|`2.9134732880742518e-14`|

两者都是从高rho端向低rho端的弱、有限、低Mach流。逐y平面平均速度剖面的最大绝对差
仅`1.5986269079337756e-10 m/s`；rho剖面均保持预设线性梯度量级。故Zou/He在固定
几何的非零流条件下可以正确承担本基准的压力开放边界，而非仅在零场下“看似稳定”。

## moving separated control

几何保持先前分离对照：压力面与最近moving Bouzidi链接的格点索引距离为3，中间至少
两层普通fluid，无pressure-moving双重cell。唯一改变是LocalPressure→Zou/He。

|量|LocalPressure separated|Zou/He separated|
|---|---:|---:|
|650步判定|FAIL|PASS|
|首次Mach>0.05|step 247|无|
|首次rho越界|step 278|无|
|max Mach|`1.5101809520653931e11`|`3.8045551481117472e-05`|
|rho范围|`[-6.7559e10,8.2862e10]`|`[0.99997891346426493,1.0003640958250091]`|
|NaN/Inf|650步内无，但已巨大有限爆发|无|
|最大速度|`4.3595e13 m/s`|`0.01098280469454547 m/s`|

Zou/He separated的初/末质量为`8.4000000000005038e-18`与
`8.4011798283535184e-18 kg`；两端瞬时向外通量分别为
`5.6257970073665678e-14`和`5.6257970073660131e-14 kg/s`，累计净外排
`2.520546882146971e-22 kg`，最大相对质量收支残差`1.7046226681300072e-4`，低于
冻结的`1e-3`。非法link、双重边界cell和材料转换均为0，材料不变。

这一对照表明，Direct intersection并非必要条件；更换仅未知population闭合后，在
同样移动壁诱导非零排液时失稳消失，支持“LocalPressure全population regularization
与moving-wall非平衡信息不兼容”的机制。

## 原始开放C650与局部补丁消融

|量|原LocalPressure C|Zou/He C（无旧补丁）|
|---|---:|---:|
|650步判定|FAIL|PASS|
|首次Mach>0.05|step 209|无|
|首次rho越过[0.8,1.2]|step 236|无|
|首次NaN/Inf|650步内无，已有巨大有限值|无|
|max Mach|`9.4035306800538525e11`|`6.1829116816418037e-05`|
|rho范围|`[-5.3827623199670685e11,4.3688164980672888e11]`|`[0.99987883917914711,1.0002955951371546]`|
|最大速度及位置|`2.7145654847309981e14 m/s @ (0,0,13)`|`0.017848528618857887 m/s @ (9,0,14)`|
|非法/错误周期link|0 / 0|0 / 0|
|材料转换 / 材料变化|0 / 无|0 / 无|

Zou/He-C的初/末域内质量为`7.1999999999946862e-18`与
`7.2004430578547148e-18 kg`。650步时低/高y向外质量通量分别为
`2.1014344248249934e-13`和`2.1014344248251878e-13 kg/s`，符号和大小体现两端对称
排液；梯形积分累计净外排为`9.5656885850207806e-22 kg`。最大相对质量收支残差
`1.9439259979607998e-4`，满足预定`1e-3`，但不应被描述为高精度守恒证明；这仍是
短时、无材料转换的亚格点移动壁测试。

旧第一处补丁的A/B消融结果：`Cpatch`和`Cnopatch`的diagnostics除有意改变的材料标签
外，所有数值字段最大绝对差为0；四个跟踪cell的rho/u/Mach及`f0...f18`最大绝对差也为
0。因此在整个压力面都使用Zou/He以后，旧的交线材料6/7特殊闭合已无数值作用，当前
生产候选应采用更简单的`Cnopatch`；**192条跨周期固壁link修复仍须保留**，因为那是
独立确认的真实几何/link完整性修复。

## f3/f8/f17历史

原LocalPressure链在step 52以后发生持续反馈放大；Zou/He中相同cell的population随
逐渐增加的壁速平滑变化，但没有原来的指数式反向放大。代表值如下（旧值来自逐算子
因果trace；新值为该步完成后的cell状态，阶段不同，故只用于量级和趋势比较）：

|step|旧LP `(0,0,14)` collision后f3|旧LP source Bouzidi后f8|新ZH `(0,0,14)` f3|新ZH `(0,0,14)` f8|新ZH `(0,0,14)` f17|新ZH局部Mach|
|---:|---:|---:|---:|---:|---:|---:|
|52|`-1.2708e-9`|`-2.6271e-7`|`5.8862e-8`|`7.3090e-8`|`-1.2234e-8`|`4.4646e-7`|
|100|`-1.6070e-6`|`-9.6745e-6`|`3.1366e-7`|`3.8684e-7`|`-1.9554e-7`|`1.6259e-6`|
|160|`-8.9808e-5`|`-5.4140e-4`|`1.1221e-6`|`1.4292e-6`|`-9.7851e-7`|`4.1352e-6`|
|209|`-2.5282e-3`|`-1.5610e-2`|`2.3567e-6`|`3.0644e-6`|`-2.3286e-6`|`6.9922e-6`|
|650|旧解已巨大有限爆发|旧解已巨大有限爆发|`5.8604e-5`|`8.1599e-5`|`-7.5962e-5`|`6.1826e-5`|

历史异常位置`(0,0,13)`、`(0,0,14)`、`(0,0,15)`及邻居`(0,1,15)`均被逐步记录。
在新C中它们没有从step几十开始的持续反向反馈，也没有重新触发全局Mach/rho门槛。
完整可复现对比为
[`zouhe_f3_f8_f17_history_comparison.csv`](zouhe_f3_f8_f17_history_comparison.csv)，补丁消融
为[`zouhe_patch_ablation_diff.txt`](zouhe_patch_ablation_diff.txt)。

## 判定与下一步权限

1. Z0：PASS。
2. Z1：PASS，且与LocalPressure弱非零流基准的全局量及速度剖面一致。
3. separated moving：PASS；原LocalPressure separated为FAIL。
4. 原始Zou/He-C650：PASS；无旧局部补丁版本同样PASS。
5. 第三候选650步短程门禁：**PASS**。
6. 约2000步转换前观察：**允许作为下一步执行，但本轮未执行**。
7. 步骤4正式验收：尚未完成，仍需上述延长观察。
8. 步骤5单次材料转换账本：**仍不允许进入**。

没有运行完整10 nm、材料转换、FreeSurface、液滴、润湿、空气、网格扫描或扩域。

## 文件索引

- 代码：`explicit_piston_zouhe_pressure_candidate.cpp`
- 构建目标：`make openlb-zouhe-pressure-candidate`
- 后处理：`analyze_zouhe_pressure_candidate.py`
- 汇总：`zouhe_pressure_candidate_summary.csv`
- D3Q19闭合：`zouhe_pressure_d3q19_closure_table.md`
- 运行清单：`zouhe_pressure_candidate_run_manifest.txt`
- 原始结果：`output/zouhe_pressure_*_20260908/`及
  `output/localpressure_fixed_nonzero_profile_650_20260908/`

