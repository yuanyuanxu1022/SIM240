# SIM-EC1XT240 STEP 5.5 动态 material 更新前代码审查

## 审查结论

本轮只读检查了项目源码与本机 OpenLB `882924a`，未修改或运行任何现有程序。STEP 4 冻结基线是 `explicit_piston_zouhe_moving_control_volume_longrun.cpp`，其 SHA-256 为 `9444c61aab6cc67499211f2724d109923d91d9bc0fe66747446acf2da5e399e2`，与 `moving_control_volume_run_manifest.txt` 一致。

当前 OpenLB 具备运行时修改 `BlockGeometry` material 和逐 cell 重新指定 dynamics 的底层能力，但没有把“material 修改、population/质量处置、dynamics 切换、边界归属和 overlap 同步”组合成原子化 fluid↔solid 转换的现成接口。对于本项目的单向下压，最小可行路径是：只处理实际跨越节点中心的 `fluid -> solid` 事件；保存事件前账本；将相应 BGK/Zou/He dynamics 改为 `NoDynamics`；同步 material overlap；重新生成全域 Bouzidi q/壁速字段。不能把单纯 `geometry.set()` 或重新调用 `boundary::set()` 当成完整动态拓扑更新。

本审查不证明上述方案已经满足质量守恒；population 和排液账本仍是 STEP 5.5 实施时的主要验收风险。

## A. 当前代码结构

### A.1 STEP 4 冻结版本

|职责|实际位置|说明|
|---|---|---|
|冻结入口程序|`explicit_piston_zouhe_moving_control_volume_longrun.cpp`|通过第1–3行包含 `explicit_piston_boundary_intersection_fix.cpp`，没有独立链接几何模块。|
|几何定义函数|`explicit_piston_boundary_intersection_fix.cpp:62–73`|`punch(x,z,h)`定义带槽压头；`materialAt(r)`以初始 `h=75 nm` 返回基底2、压头3、低/高y压力面4/5和内部流体1。|
|几何实例化/material初始化|`explicit_piston_zouhe_moving_control_volume_longrun.cpp:273–283`|建立 `SuperGeometry(overlap=3)`，逐core cell调用 `g.set(p,materialAt(...))`，随后 `geometry.communicate()`。`geometry_generator.cpp`是早期独立体素/VTI工具，不参与STEP 4运行。|
|dynamics分配|同文件 `285–300`|material 1使用 `BGKdynamics`；开放C的4/5由Zou/He pressure设置；2/3使用 `NoDynamics`；全局注册一次 `BouzidiVelocityPostProcessor`。|
|pressure boundary封装|同文件 `60–68`|`cvSetAllZouHePressure()`对material 4、5调用 `boundary::set<...ZouHePressure...>`。|
|初始化|同文件 `296–306`|定义初始rho/u和平衡population，`lattice.initialize()`，对4/5规定rho=1并通信。|
|压头轨迹|`explicit_piston_boundary_intersection_fix.cpp:42–61`|`hAt()`和`wallSpeed()`使用冻结的五次平滑轨迹；`trajectorySteps=10000`、`dt=1e-11 s`。|
|动态Bouzidi链接|`explicit_piston_zouhe_moving_control_volume_longrun.cpp:14–58`|`cvUpdatePeriodicLinks()`清除并重写 `BOUZIDI_DISTANCE/VELOCITY`，包含x周期映射和192条跨周期固壁link修复。|
|主时间循环|同文件 `323–350`|每步先求h/壁速并更新链接，再 `collide()`，统计population通量，`AndStream()`，最后统计移动控制体积质量和阈值。|

STEP 4 的material图固定于初始75 nm；其通过范围是首次离散material转换之前的连续移动控制体积，不包含运行时拓扑切换。

### A.2 STEP 5.4

|职责|实际位置|说明|
|---|---|---|
|独立程序|`explicit_piston_virtual_link_moving_geometry.cpp`|SHA-256 `47cc3defac6437c353eb17b17dbdb0a185eef5e7af27d569d9e9b7f97d6104cb`。|
|位置/速度更新|包含文件中的 `hAt()`、`wallSpeed()`；调用点为本文件 `380–382`|每步计算目标h和刚体壁速。|
|解析壁与ghost判定|本文件 `14–33`|`cvAnalyticalSolid()`、`cvPhysicalFluidCenter()`及`cvGhostFluidCount()`。|
|Bouzidi link更新|本文件 `35–86`|允许解析固体邻居仍带fluid material，从而形成virtual link/ghost storage。|
|boundary初始设置|本文件 `321–354`|Zou/He只在启动时设置；Bouzidi postprocessor只注册一次。|
|每步refresh调用|本文件 `380–393`|`cvUpdatePeriodicLinks()`之后直接进入collision/streaming；没有重新调用pressure `boundary::set()`，所谓refresh实际是重写q和壁速字段并调用 `lattice.communicate()`。|

STEP 5.4 没有material或dynamics更新。step 3595出现的2304个ghost-storage节点只是应用层解析分类，OpenLB仍把它们作为原流体/压力节点推进。

## B. 本机 OpenLB 能力与最小修改点

### B.1 实际支持范围

|能力|本版本源码依据|结论|
|---|---|---|
|运行时material改变|`src/geometry/blockGeometry.h:125–127`和`blockGeometry.hh:122–138`提供`set()`；`superGeometry.h:155–165`提供多种`rename()`|底层支持。material只是geometry数据，改变它不会自动改变lattice dynamics或population。|
|material overlap同步|`superGeometry.h:199–204`的`communicate()`受`_communicationNeeded`控制；无条件`SuperGeometry::rename(from,to)`在`superGeometry.hh:324–332`会置该标志|支持，但直接调用block `g.set()`不会通知`SuperGeometry`。运行时仅`g.set(); geometry.communicate();`可能因dirty标志未置位而不真正同步，不能照搬现有STEP 5写法。|
|运行时dynamics重新分配|`src/core/blockLattice.h:253–279`公开逐cell `defineDynamics()`；具体实现`blockLattice.h:561–566`调用dynamics map的`set()`并初始化新dynamics|支持逐cell切换，例如fluid/Zou-He → `NoDynamics`。它不负责质量守恒或邻域边界刷新。|
|Zou/He pressure重建|`src/boundary/zouHePressure3D.h:42–63`|三维平面Zou/He只返回dynamics，不创建postprocessor。因此被压头覆盖的material 4/5节点可用`NoDynamics`替换；仍存活的4/5平面节点无需重复注册。|
|Bouzidi动态更新|`src/boundary/setBouzidiBoundary.h:128–164`|`BouzidiVelocityPostProcessor`读取每cell的q/壁速字段；当前程序把该处理器全域注册一次，q<0即不作用。可以每步更新字段，不必重复添加处理器。|
|边界重新初始化/移除|`src/core/blockLattice.h:328–341`只有`has/addPostProcessor`，没有公开remove；CPU per-cell operator的`set(cell,false)`也没有移除分支（`src/core/platform/cpu/sisd/operator.h:357–363`）|不支持通用、安全的“清空并重建局部边界处理器”。重复调用带postprocessor的`boundary::set()`有残留或重复处理风险。本工况可因Zou/He无postprocessor、Bouzidi全域一次注册而绕开。|
|fluid↔solid完整转换|没有发现组合上述操作并处理population/质量的公开原子API|只能在应用层实现并逐项验收；不能声称OpenLB已经提供完整移动拓扑功能。|

### B.2 必须新增的应用层修改点

1. **拓扑差分**：在每步collision之前，用`h_old/h_new`找出刚被解析压头覆盖的core cells，并按旧material 1/4/5分别保存。只允许预测的`fluid -> solid(3)`；10 nm单向下压不实现反向开放节点。
2. **事件前状态与账本**：修改任何material/dynamics前保存19个population、rho、动量、控制体积权重及相邻链接；不得依赖修改后material indicator回找旧节点。
3. **geometry提交与强制同步**：建议先把事件cell写成专用临时material，再调用会可靠置dirty标志的super-level提交/rename并通信；实施前必须用跨x seam事件验证core与overlap一致。不能仅依赖直接block `set()`后的受条件保护`geometry.communicate()`。
4. **dynamics切换**：对事件列表逐cell执行`defineDynamics<NoDynamics>`。旧material 4/5的Zou/He dynamics也必须移除；其余压力面保持原Zou/He。
5. **population处置**：单独实现可审计策略，记录移出moving control volume的质量/动量与出口通量；不能清零、全域归一化或把消失质量伪装成出口流量。STEP 5.1/5.2的失败说明这一步不能由material/dynamics API代替。
6. **链接刷新**：清除所有core cell旧q/壁速，然后沿用STEP 4周期感知算法，仅给新material图中的真实fluid owner生成Bouzidi link；全局postprocessor不重复注册。
7. **lattice同步**：拓扑事件后的population/field和halo同步必须显式验证。`SuperLattice::communicate()`同样受dirty标志保护（`superLattice.hh:843–849`）；直接block cell写入后不能假设调用一定执行。必要时使用公开stage communicator并在单rank x周期seam上做前后值审计，而不是修改OpenLB库。
8. **顺序和断言**：完成geometry、dynamics、状态、q和overlap提交后才能collision。每次事件检查material计数、dynamics RTTI、pressure所有权、q范围、非法/遗漏link及周期映射。

## C. 风险点

1. **质量闭合是首要风险**：material切成solid只解决拓扑身份，不会自动把被扫体积内的液体送到开放y边界。STEP 5.2已表明局部population重分配会制造Mach尖峰和长期质量残差。
2. **直接block写导致halo陈旧**：当前代码模式`g.set()`不会设置`SuperGeometry::_communicationNeeded`；这对x周期seam及overlap=3尤其危险。
3. **边界处理器不可通用撤销**：若未来引入带per-cell postprocessor的压力边界或需要solid→fluid，当前“只换dynamics”的方案不再充分，且不能每步重复`boundary::set()`。
4. **dynamics与material非自动一致**：material 3不保证cell已经是`NoDynamics`；必须逐cell验证。反之亦然。
5. **Bouzidi壁后population依赖**：处理器在q≤0.5时会读取solid侧邻居population，在q>0.5时还读取反向fluid邻居。新solid cell停止collision后，其存储值如何用于插值必须与本版本公式逐link核对。
6. **事件时序**：在streaming后修改一半状态、下一步再补齐会产生混合时间层。拓扑事务应位于一次完整step结束后、下一次collision前一次性完成。
7. **压力面交线**：转换会覆盖旧material 4/5节点并改变相邻压力cell的固壁link，但存活pressure节点仍应保持唯一Zou/He dynamics；不得把pressure boundary重新施加到已成solid的cell。
8. **10 nm包含多次离散层事件**：每一层必须分别提交并记账，不能一次预先把最终10 nm区域全部改solid，否则改变冻结轨迹和排液响应。

## D. 推荐实现顺序

1. 从STEP 4冻结文件复制出新的独立STEP 5.5程序，先记录源文件SHA；不改冻结文件。
2. 实现只读`predictTopologyDelta()`，离线核对每次事件step、材料来源、坐标、数量和x周期对称性；此阶段不推进lattice。
3. 实现`beginTopologyTransaction()`快照和一致性断言，保存旧population、质量、动量、dynamics类型和links。
4. 实现geometry提交及overlap强制同步；先用单个临时事件做material-only预检，逐core/halo比对，不运行10 nm。
5. 加入逐celldynamics切换和RTTI审计，确认1/4/5→3节点全部为`NoDynamics`，未转换节点不变。
6. 加入Bouzidi q/壁速全量刷新；检查192条跨周期link仍正确，且无旧owner残留。
7. 最后接入独立、可审计的population/质量处置，并只跑第一次转换及短观察。若质量或Mach失败，停在单事件，不直接运行10 nm。
8. 只有单事件满足冻结阈值后，才按相同事务依次处理10 nm内后续事件。每次事件前后写manifest/CSV并保留失败现场。

## E. 建议新增函数接口

```cpp
struct TopologyCell {
  int iC;
  LatticeR<3> latticeR;
  Vector<T,3> physicalR;
  int oldMaterial;
  int newMaterial;
};

struct CellStateSnapshot {
  TopologyCell topology;
  std::array<T,D::q> population;
  T rho;
  Vector<T,3> momentum;
  std::string dynamicsType;
};

struct TopologyTransaction {
  int step;
  T hOld;
  T hNew;
  std::vector<CellStateSnapshot> covered;
  T removedControlVolumeMass;
  Vector<T,3> removedMomentum;
};

std::vector<TopologyCell>
predictTopologyDelta(SuperGeometry<T,3>& geometry, T hOld, T hNew);

TopologyTransaction
snapshotTopologyEvent(SuperLattice<T,D>& lattice,
                      SuperGeometry<T,3>& geometry,
                      const std::vector<TopologyCell>& delta,
                      int step, T hOld, T hNew);

void commitMaterialTopology(SuperGeometry<T,3>& geometry,
                            const std::vector<TopologyCell>& delta);

void assignConvertedDynamics(SuperLattice<T,D>& lattice,
                             const std::vector<TopologyCell>& delta);

ConversionBudget
closeConvertedPopulations(SuperLattice<T,D>& lattice,
                          SuperGeometry<T,3>& geometry,
                          const TopologyTransaction& transaction);

LinkAudit refreshMovingBouzidiLinks(SuperLattice<T,D>& lattice,
                                    SuperGeometry<T,3>& geometry,
                                    T h, T wallVelocity);

OverlapAudit synchronizeAndAuditTopology(SuperLattice<T,D>& lattice,
                                         SuperGeometry<T,3>& geometry,
                                         const TopologyTransaction& transaction);

BoundaryAudit auditDynamicOwnership(SuperLattice<T,D>& lattice,
                                    SuperGeometry<T,3>& geometry,
                                    const TopologyTransaction& transaction);
```

`commitMaterialTopology()`、`assignConvertedDynamics()`和`closeConvertedPopulations()`必须保持为三个可分别审计的阶段，但由一个事务驱动；任一断言失败应在进入collision前停止并保存快照。当前下压测试不需要实现solid→fluid接口，也不需要复制整个lattice。

## 停止点

本轮仅新增本审查报告。没有修改STEP 4、STEP 5.4或OpenLB源码，没有编译、没有运行仿真，也没有实施动态material更新。下一步应先完成“单次拓扑事务的material/overlap/dynamics预检”，不能直接宣称可以完成10 nm。

Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is **SIM-EC1XT240**.
