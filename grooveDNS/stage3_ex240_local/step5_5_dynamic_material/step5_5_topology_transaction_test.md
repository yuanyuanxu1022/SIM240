# SIM-EC1XT240 STEP 5.5 第一阶段：动态 material 拓扑事务框架测试

## 判定

**0→1 nm零事件框架测试：PASS；真实material事务：NOT EXERCISED。**

独立程序沿用STEP 4的几何、单位映射、五次平滑轨迹、Zou/He压力边界、moving Bouzidi和验收阈值，完成2467步，实际位移`1.000658284 nm`。全过程没有预测到fluid→solid或solid→fluid节点，因此五阶段事务均按设计执行为no-op。程序无崩溃、无NaN/Inf、无非法link，material保持不变。

由于dx=5 nm下首次离散拓扑阈值约在位移2.5 nm，本轮授权的1 nm范围不能实际检验material提交、`NoDynamics`切换或事件后的population策略。因此不能把本结果称为动态material转换通过，也不能继续10 nm。

## 独立实现

只在`step5_5_dynamic_material/`新增：

- `dynamic_topology_manager.h`：拓扑差分、快照、material提交、dynamics切换、population策略和周期映射审计；
- `topology_transaction_test.cpp`：真实OpenLB短程测试；
- `Makefile`：独立构建目标；
- `output/`：保留运行记录。

冻结文件未覆盖：

|文件|复核SHA-256|
|---|---|
|`../explicit_piston_zouhe_moving_control_volume_longrun.cpp`|`9444c61aab6cc67499211f2724d109923d91d9bc0fe66747446acf2da5e399e2`|
|`../explicit_piston_virtual_link_moving_geometry.cpp`|`47cc3defac6437c353eb17b17dbdb0a185eef5e7af27d569d9e9b7f97d6104cb`|

未修改OpenLB库，没有重复调用`boundary::set()`，没有复制整个lattice，也没有加入两相、液滴、接触角、润湿或空气模型。

## 事务结构

`updatePistonTopology()`每步依次执行：

1. `predictTopologyDelta()`：比较当前material和下一步解析压头区域，先输出fluid→solid及solid→fluid统计；
2. `beginTopologyTransaction()`：对将转换节点保存node id、坐标、旧/新material、rho、速度、动量、dynamics类型和`f0...f18`；
3. `commitMaterialTopology()`：事件节点先标记临时material 30，再通过super-level `rename(30,3)`置geometry通信dirty标志并同步；
4. `assignConvertedDynamics()`：逐事件cell改为`NoDynamics`；
5. `initializeConvertedPopulations()`：第一阶段不转移、不清零、不归一化population，只检查提交前后存储值未被暗改。

solid→fluid已能被预测和记录，但第一阶段明确拒绝提交。Bouzidi处理器仍只注册一次，每步全量刷新q与壁速；x周期邻居继续使用STEP 4已验证的显式core映射。

这里的population“初始化”是一个保守的占位策略，不是已经验证的物理质量闭合。第一次真实转换发生时仍需单独验收。

## 编译

- 命令：`make -j2`
- OpenLB编译标识：`5953d8a-dirty`
- 结果：成功；修正新文件中一处误导缩进后，最终编译无warning/error。
- 可执行文件：`topology_transaction_test`

## 运行记录

### 保留的v1预检失败

run-id `topology_transaction_0to1nm_20260909`在step 1按审计断言停止，退出码3。原因是初版审计错误地把`BlockGeometry::getMaterial(-1,...)`当作周期halo；本版本对core外坐标返回material 0，产生3840个假mismatch。该次实际只推进1步，早期`result.txt`中的`steps_completed=2467`是记录变量错误，不能作为完成证据。失败目录和退出记录均保留。

修复只涉及新诊断代码：按STEP 4实际算法审计x周期映射后的core来源，并记录真实`completed`步数；没有改变几何、物性、轨迹、边界或阈值。

### v2有效测试

- run-id：`topology_transaction_0to1nm_v2_20260909`
- 命令：`mpirun -np 1 ./topology_transaction_test`
- 退出码：0
- 步数：2467
- 物理时间：`2.467e-8 s`
- 目标/实际位移：`1 / 1.000658284 nm`

## 转换和material统计

|量|结果|
|---|---:|
|累计fluid→solid|0|
|累计solid→fluid|0|
|material提交|0|
|dynamics切换|0|
|population策略处理|0|
|周期映射mismatch|0|
|material场变化|否|

实际初态和终态计数相同：

|material|初始|最终|
|---|---:|---:|
|1（内部流体）|55,200|55,200|
|2（固定基底）|2,304|2,304|
|3（压头固体）|32,256|32,256|
|4（低y压力面）|1,200|1,200|
|5（高y压力面）|1,200|1,200|
|流体1+4+5|57,600|57,600|

上述计数与程序的`material_field_changed=false`和既有静态几何逐cell审计一致。由于没有事件，它们不能证明转换后的geometry overlap已经实际同步。

## 数值推进结果

|指标|结果|冻结标准|判定|
|---|---:|---:|---|
|完成0→1 nm|`1.000658284 nm`|达到1 nm|PASS|
|rho范围|`[0.9957544591, 1.0402809330]`|`[0.8,1.2]`|PASS|
|最大Mach|`5.9263706e-4`|`<=0.05`|PASS|
|NaN/Inf|0|0|PASS|
|非法/错误周期固壁link|0|0|PASS|
|fluid cell数|57,600|无事件时不变|PASS|

本轮没有重新定义STEP 4的移动控制体积质量验收；第一阶段目标是事务框架、同步预检和基本推进。真实转换前后的质量闭合尚未执行。

## 输出文件

有效v2目录：`output/topology_transaction_0to1nm_v2_20260909/`

- `topology_prediction.csv`：2467步预测，全部为0/0；
- `transaction_phase_log.csv`：每步五阶段，共12,335条阶段记录；
- `topology_events.csv`：只有表头，证明没有伪造事件；
- `short_run_history.csv`：2467步rho、Mach、link和事务统计；
- `result.txt`、`run.log`、`run_manifest.txt`。

历史v1失败目录：`output/topology_transaction_0to1nm_20260909/`。

## 尚未验证与下一步边界

本轮确认：新模块可编译，五阶段调度在零事件路径上完整执行，真实OpenLB在0→1 nm moving Bouzidi + Zou/He工况下稳定推进。

本轮没有确认：

1. material确实从1/4/5提交为3；
2. 对应cell dynamics确实由BGK/Zou-He切换为`NoDynamics`；
3. 事件后的geometry/periodic overlap同步；
4. 被扫液体的population、质量和动量闭合；
5. 第一次转换后的稳定性。

因此第一阶段只可标记为**框架建立完成、零事件短程PASS**。下一步若获授权，应只运行到第一次约2.5 nm转换并立即做单事件事务审计，不能直接进入完整10 nm。

Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is **SIM-EC1XT240**.
