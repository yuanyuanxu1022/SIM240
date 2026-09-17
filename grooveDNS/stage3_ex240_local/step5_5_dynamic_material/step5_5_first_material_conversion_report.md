# SIM-EC1XT240 STEP 5.5 第二阶段：首次真实 material 转换验证

## 判定

**拓扑事务执行：PASS；首次转换综合验收：FAIL。**

正式v3测试完成3898步，停在不超过3 nm的最后一个离散时间步，实际位移`2.999688538 nm`。第一次真实`fluid -> solid`发生在step 3595、位移`2.501015275 nm`，一次转换2304个节点。material提交数量、最终material差值、dynamics切换、周期映射和Bouzidi link均正确；无NaN/Inf，rho和Mach稳定。

但是STEP 4沿用的移动控制体积残差在转换时从`-9.28533e-4`跳到`-1.43866e-3`，末态为`-1.62296e-3`，超过冻结标准`|R_geom|<1e-3`。因此程序虽覆盖了0→3 nm允许区间且退出过程正常，验收仍为FAIL；不得继续10 nm。

## 实现与保护范围

- 独立程序：`first_material_conversion_test.cpp`；
- 复用模块：`dynamic_topology_manager.h`；
- 构建目标：`make phase2-first-conversion -j2`；
- OpenLB：`5953d8a-dirty`；最终编译无warning/error；
- STEP 4冻结源码SHA-256仍为`9444c61aab6cc67499211f2724d109923d91d9bc0fe66747446acf2da5e399e2`；
- STEP 5.4源码SHA-256仍为`47cc3defac6437c353eb17b17dbdb0a185eef5e7af27d569d9e9b7f97d6104cb`。

没有修改STEP 4、STEP 5.4、OpenLB、Zou/He压力边界、几何、物性、dt、tau或壁速；没有加入两相、液滴、接触角、润湿或空气。

## A. 首次转换位置

- step：3595；
- 物理时间：`3.595e-8 s`；
- 压头凸台间隙：`72.498984725 nm`；
- 位移：`2.501015275 nm`；
- x范围：`2.5–237.5 nm`；
- y范围：`2.5–237.5 nm`；
- 两个离散z层：
  - `iz=15`、`z=72.5 nm`：凸台底面对应层，1152节点；
  - `iz=35`、`z=172.5 nm`：凹槽顶面对应层，1152节点。

该位置与60/120/60 nm带槽刚体整体下移的解析几何预测一致。

## B. 转换节点数量与material统计

|来源material|转换前数量|本事件转换数|转换后数量|
|---|---:|---:|---:|
|1，内部流体|55,200|2,208|52,992|
|4，低y压力面|1,200|48|1,152|
|5，高y压力面|1,200|48|1,152|
|3，压头固体|32,256|+2,304|34,560|

- fluid→solid总数：2304；
- solid→fluid：0；
- `material3_delta=2304`；
- 事件后到3 nm未出现第二次转换；
- 周期映射material mismatch：0。

提交使用临时material 30后由super-level `rename(30,3)`完成，并显式调用`SuperGeometry::communicate()`。单rank/单cuboid测试实际核对了项目所用x周期core映射；没有进行多rank halo验证。

## C. 转换前后rho

转换前，2304个事件节点通过原BGK/Zou-He momenta得到：

- rho范围：约`[0.994406, 1.109680]`；
- shifted-population直接恢复的总rho：约`2363.04`个格子质量单位。

切换为`NoDynamics`后，OpenLB momenta接口对这些solid cell返回固定`rho=1`、`u=0`；这不是population被重置。按本版本shifted population定义直接计算，事件前后范围和总和完全相同，立即变化量为0。

全体仍活跃fluid节点在完整0→3 nm测试中的rho范围为：

`[0.9868037667, 1.1096799051]`

满足冻结区间`[0.8,1.2]`，未见异常rho增长。

## D. Population处理方式

事务顺序实际执行为：

1. 预测2304个转换节点；
2. 保存node id、物理/格点坐标、old/new material、rho、速度、动量、dynamics RTTI和`f0...f18`；
3. 提交material 1/4/5→30→3并同步geometry；
4. 逐cell切换为与初始solid完全相同的CSE包装`NoDynamics`；
5. 保留事件cell原`f0...f18`，不转移、不清零、不平衡态重构、不归一化；
6. 清除旧q/壁速，重建周期感知Bouzidi link并同步lattice字段；
7. 进入collision/streaming。

2304个节点、19个方向的立即population最大绝对变化为0。`conversion_before_after.csv`保留了事件前后4608条逐cell记录。

该策略验证的是拓扑身份和dynamics事务，不代表被扫液体已经物理地排到出口。

## E. Mach变化

|时刻|最大Mach|
|---|---:|
|step 3594，转换前|`9.463887e-4`|
|step 3595，转换并推进后|`9.466650e-4`|
|0→3 nm全过程最大|`1.050757e-3`|

全过程最大值发生在step 3894、cell `(38,47,14)`、material 5压力面。远低于`0.05`，没有材料转换诱发的Mach尖峰。

## F. 质量残差变化

定义沿用STEP 4：以cut-cell体积分数`alpha(h)`计算`M_geom`，并用两端Zou/He面的有符号宏观质量通量作梯形时间积分。

|时刻|`R_geom/M_geom(0)`|
|---|---:|
|step 3594，转换前|`-9.2853266e-4`|
|step 3595，转换后首次推进|`-1.4386617e-3`|
|3 nm内末态，step 3898|`-1.6229610e-3`|

转换步的额外跳变量约为`-5.10129e-4`。本程序将新solid cell的stored populations原样保留，但`NoDynamics::computeRho()`使用固定rho=1；同时这些cut cells仍具有非零`alpha`。这说明当前`M_geom`宏观momentum接口口径与solid侧保存population的口径在拓扑切换后不再完全一致，是质量残差FAIL的直接待处理项。

本轮没有通过重新分配、密度归一化或修改出口通量掩盖该残差。

## G. 稳定性、同步与退出

|检查|结果|判定|
|---|---:|---|
|完成位移|`2.999688538 nm`|最后一个不超过3 nm的离散步|
|首次转换|2304节点|符合预测|
|dynamics错误|0|PASS|
|periodic material mismatch|0|PASS|
|非法/错误周期solid link|0|PASS|
|NaN/Inf|0|PASS|
|rho|`[0.986804,1.109680]`|PASS|
|最大Mach|`1.05076e-3`|PASS|
|最大`|R_geom|`|`1.62296e-3`|FAIL|

有效运行退出码为3，表示冻结质量标准失败，不是崩溃或非有限值。

## 保留的v1记录

`first_material_conversion_0to3nm_v1_20260909`在step 3595停止。其2304个“dynamics error”来自审计将OpenLB自动CSE包装后的`NoDynamics`与未包装模板typeid直接比较，属于诊断误报；实际after dynamics已经是零动量、无碰撞组合。v2改为与初始material-3 cell的实际RTTI比较，错误数为0。v1目录未覆盖或删除。

v2完成到step 3899，但位移为`3.001385959 nm`，比3 nm多一个离散时间步，故不作为正式范围结果。该目录同样保留。v3在第一个会超过3 nm的step之前停止，没有改变任何物理参数、边界、轨迹或验收标准。

## 输出

正式目录：`output/first_material_conversion_0to3nm_v3_20260909/`

- `topology_events.csv`：2304个事件cell及转换前完整状态；
- `conversion_before_after.csv`：逐cell前后rho/u/dynamics/populations；
- `transaction_phase_log.csv`：每步五阶段状态；
- `topology_prediction.csv`：逐步转换预测；
- `first_conversion_history.csv`：material、link、质量、rho和Mach时序；
- `result.txt`、`run.log`、`run_manifest.txt`。

## 结论与停止点

首次真实material事务已在正确位置完成：geometry material、dynamics和Bouzidi link同步均正常，且没有数值爆炸。但moving-control-volume质量收支未满足`1e-3`，所以STEP 5.5第二阶段综合结论为**FAIL**。

停止在首次转换质量口径/闭合问题；不进入完整10 nm，等待下一步。

Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is **SIM-EC1XT240**.
