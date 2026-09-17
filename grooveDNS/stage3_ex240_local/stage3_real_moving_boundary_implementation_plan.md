# 阶段三真实 OpenLB 移动压头最小接入方案

日期：2026-09-07  
状态：实现路径审查与下一轮施工清单；本轮未编译、未运行、未建立新的数组原型。

## 1. 起点与范围

基线为已通过的 `static_lattice_integration.cpp`：真实 OpenLB `SuperGeometry<T,3>`、`SuperLattice<T,D3Q19<>>`，x/y周期、z向固定实体，单相全充液零场完成10步推进。静态几何为240 nm单胞，左右各60 nm半凸台、中央120 nm槽、槽深100 nm；测试参数 `h=65 nm`、`dx=5 nm`。

此前 `movingPistonIndicator.h` 已验证五次平滑轨迹，M3验证了独立字段/合成FreeSurface单元的转换与回滚思想，但二者均不是实际lattice动态边界。本方案不重复开发独立数组测试。

本轮只确定真实OpenLB接入路径。没有执行下压，未加入FreeSurface、接触角或液滴，也未修改 `/home/dell/openlb`、阶段一、阶段二或其他阶段三目录。

## 2. 本机OpenLB源码核对结果

本机版本宏为 `5953d8a-dirty`。可直接复用的实际接口包括：

- `CuboidDecomposition::setPeriodicity({true,true,false})`：固定x/y周期；
- `SuperGeometry::rename/set`、`BlockGeometry::set`及`SuperGeometry::communicate()`：修改并同步材料；
- `BlockLattice::defineDynamics(latticeR, ...)`、`dynamics::set`和`boundary::set`：为实际节点配置流体或固壁动力学；
- `setBouzidiBoundary<...,BouzidiVelocityPostProcessor>`：依据解析几何计算 `BOUZIDI_DISTANCE`，在流体边界节点安装PostStream处理器；
- `setBouzidiVelocity(...)`：在实际边界交点计算壁速并写入 `BOUZIDI_VELOCITY`；
- `SuperLattice::communicate()`及stage communicator：同步lattice overlap；
- `setProcessingContext(ProcessingContext::Simulation/Evaluation)`：CPU/GPU数据上下文切换；本机当前测试为CPU_SISD。

源码中的Bouzidi设置器主要按**初始化时的材料和解析indicator**遍历，并向选中节点添加PostStream处理器。未找到一个公开的高层API，可以在每一步同时完成：移动解析表面、撤销旧边界处理器、创建新处理器、改变材料、重建新流体分布函数并同步FreeSurface邻域。因此不能简单地每步再次调用 `setBouzidiBoundary`；这样可能累积旧处理器或留下失效链接。

这表示本机版本尚缺所需的一站式接入，不表示OpenLB绝对无法实现。首选是在当前目录增加一个受限的动态边界适配层；若实验证明必须为核心PostProcessor容器增加“按标签清除/重建”能力，则需另行申请修改 `/home/dell/openlb`，本轮不修改。

静态基线的descriptor是 `D3Q19<>`；Bouzidi移动交点实现必须在新程序中改为包含实际字段的 `D3Q19<descriptors::BOUZIDI_DISTANCE, descriptors::BOUZIDI_VELOCITY>`。这是新独立测试的descriptor变更，不修改静态基准，也不能漏掉后假设字段自然存在。

## 3. 压头的几何运动定义

压头作为一个刚体整体沿z平移，不能只移动凸台底面：

\[
h(t)=h_0+\Delta h\,s(t/T),\qquad
s(\xi)=10\xi^3-15\xi^4+6\xi^5.
\]

在任意时刻：

- 左半凸台底面：`x∈[0,60) nm, z=h(t)`；
- 中央槽顶：`x∈[60,180) nm, z=h(t)+100 nm`；
- 右半凸台底面：`x∈[180,240) nm, z=h(t)`；
- 两个槽侧壁也以相同速度 `u_w=(0,0,dh/dt)` 整体平移；
- x周期缝两侧是同一120 nm凸台的两半，材料、交点和壁速必须周期一致。

现有 `pistonState` 的轨迹形式可以复用，但应新增带槽解析indicator，而不是复用旧的平板条件 `z>=zP`。下一轮文件建议为 `ex240MovingPunchIndicator.h`，提供 `insideSolid(x,y,z,h)`、每条D3Q19链接的解析交点距离和统一刚体壁速。

## 4. 每一项怎样接入真实lattice

| 项目 | 直接使用的OpenLB接口 | 本目录需新增的位置和职责 |
|---|---|---|
| 更新整个压头位置 | 轨迹计算为普通解析函数；`IndicatorF3D`可描述当前表面 | `ex240MovingPunchIndicator.h`：由同一个`h(t)`生成凸台、槽顶、侧壁，禁止各面独立漂移 |
| 实际边界交点 | Bouzidi的 `BOUZIDI_DISTANCE`；初始化接口 `setBouzidiBoundary` | `dynamicBouzidiAdapter.h`：每步重算当前fluid-solid链接的q；无交点设为无效值，并检查`0≤q≤1` |
| 壁速 | `setBouzidiVelocity`和 `BOUZIDI_VELOCITY` 的计算规则 | 适配层按交点写入 `u_w=(0,0,dh/dt)`；固定基底始终为0；输出交点速度与解析速度误差 |
| 节点状态改变 | `BlockGeometry::set`，节点级 `BlockLattice::defineDynamics` | `dynamicMaterialTransaction.h`：只处理旧/新indicator异或集合；fluid→solid与solid→fluid分别列表并原子提交 |
| 动力学切换 | `defineDynamics<BGKdynamics>`、`defineDynamics<BounceBackVelocity/NoDynamics>`或节点级promise | 同一transaction中，在材料提交时同步切换；不得只改material编号 |
| 新释放流体节点 | `defineRhoU`/`iniEquilibrium`可用于初始化，但全域调用不适合每步 | 局部重建：从有效流体邻居外推ρ、u和非平衡部分；没有足够邻居则拒绝该步并回滚 |
| 新覆盖流体节点 | OpenLB没有自动处置其质量的API | A阶段仅核对事件并禁止推进流体解释；B阶段必须把质量/动量转移到出口或FreeSurface邻域后再固化 |
| 几何同步 | `SuperGeometry::communicate()` | 材料提交后立即调用，并核对周期缝与所有rank事件哈希 |
| lattice/overlap同步 | `SuperLattice::communicate()`及相应stage communicator | 分布函数、Bouzidi字段、动力学切换完成后通信；下一轮先单rank，再做2-rank一致性 |
| 邻域与边界处理器 | 初始化时可用`boundary::set`/`setBouzidiBoundary` | 最小适配层预先覆盖整个−10 nm候选带并以q有效性启停，避免每步累积处理器；如无法安全预装，停止并申请库级“清除/重建”接口 |

### 候选带策略

首个−10 nm测试在5 nm网格上只跨越两层节点。初始化时根据 `[h_0-10 nm,h_0]` 的扫掠包络建立候选带：所有可能成为边界流体节点的格点只安装一次自定义PostStream算子。算子每步读取当前 `BOUZIDI_DISTANCE/VELOCITY`；q无效时不执行。这比反复添加OpenLB Bouzidi处理器更容易审计，且不需要修改库核心。

适配器必须直接作用于真实 `BlockLattice` cell和descriptor字段，不允许另建一套“代表lattice”的数组。M3只作为transaction/回滚规则的测试依据。

## 5. 转换在时间推进中的准确位置

建议每一步从状态 `(f^n, geometry^n, h^n)` 到 `n+1` 的顺序固定为：

1. 计算 `h^{n+1}` 和 `u_w^{n+1/2}`，检查单步位移不超过预设上限（建议小于0.25dx；节点跨越事件不得跳层）。
2. 在只读状态下构建新解析indicator、Bouzidi链接和材料异或集合，完成全rank事件计数与容量预检。
3. 对将被覆盖的流体执行经所选物理方案批准的质量/动量处置；任何失败均在碰撞前回滚。
4. 对新释放节点重建分布函数；写材料号并逐节点切换动力学。
5. `geometry.communicate()`，重建/更新q和壁速字段，再执行lattice overlap通信；复核周期缝和邻域。
6. transaction提交后，才调用一次 `collideAndStream()`。
7. 切到Evaluation上下文，记录质量、动量、材料事件、交点、最大速度、ρ范围和NaN/Inf，然后恢复Simulation上下文。

动态更新不能放在stream之后再补做，因为那会让一个时间步使用旧几何但新材料统计。输出必须同时记录“本步碰撞所用的h”和“下一步目标h”，避免时间标签错位。

## 6. 两类验收必须分开

### A：几何和边界真正移动

A只验证几何/数值边界机制：

- 压头所有表面遵循同一 `h(t)`，最终位移−10 nm；
- q、实际交点和壁速随时间改变，不是固定墙上施加加速度；
- 两次5 nm节点跨越的fluid↔solid事件集合与解析扫掠体积一致；
- 材料号、动力学、候选带、周期缝和overlap同步；
- 静止压头对照中事件数为0；移动后旧边界链接失效、新链接生效；
- VTK逐帧显示真实 `SuperGeometry` 与Bouzidi交点共同下移。

A通过只说明边界真正移动，不能宣称液体受压、质量守恒或填槽正确。

### B：液体受压及守恒

B在选定排液/自由表面/可压缩物理模型之后验证：

- 初始液体质量 + 累计入口质量 − 累计出口质量 = 域内液体质量 + 明确的转换账项；
- 被覆盖节点的质量和动量去向可逐事件追踪；
- 新释放节点不会凭空产生质量；
- 密度、速度、压力、界面量有限，局部与全局守恒同时满足；
- 结果对dt、dx和出口位置有敏感性检查。

A通过不能自动判定B通过，M3字段守恒原型通过也不能替代B。

## 7. 体积缩减问题与可选物理闭合

当前固定测试是全充液、x/y周期、基底固定的封闭单胞。压头下降使可用体积减少。若仍保持全充液、无出口、无自由表面，质量只能通过密度升高保存；不能同时假设密度不变并持续下压。

可选闭合只有以下三类：

1. **设置排液出口**：保留x图案周期，但将y±由周期改成参考压力出口/储液边界。实际API可从 `boundary::set<boundary::LocalPressure>(lattice,geometry,material)`开始。该模型代表沿直槽方向连接储液区，不再是y周期单胞；需要验证双出口回流、质量通量和出口距离影响。
2. **保留自由表面**：x/y仍可周期，但初始液体不得全充满，必须留有气体/界面容量接收排液。需要进入后续FreeSurface和材料转换守恒，接触角与气体参考压力仍待确认。
3. **明确研究可压缩响应**：维持封闭全充液，把密度增长/压力波作为研究对象，并给出可接受压缩率和状态方程。标准弱可压LBM不适合把−10/65约15%的几何体积缩减当作小扰动基线，故不推荐作为首例。

周期边界不是出口。不得把消失的体积静默删除，也不得把被覆盖节点质量直接清零。

## 8. 首个−10 nm功能测试建议

推荐把首次实施分成A0和A1，不套用−935 nm：

### A0：无跨节点的连续交点测试

- `h_0`选择与格点错开，位移小于0.5dx；压头解析表面和Bouzidi q连续变化，但材料集合不变。
- 单相均匀液体可用于很短的壁速响应诊断，但不做质量受压结论；同时做 `u_w=0` 对照。
- 验收重点是交点、壁速、无旧链接残留和固定基底零速。

### A1：完整−10 nm、允许两层转换

推荐物理边界：x周期；y−/y+改为等参考密度的LocalPressure开放储液边界；z=0固定壁；带槽压头移动。初始为单相全充液、ρ=1、u=0、无体力。这样被排液体可沿槽方向离开，而不是要求封闭液体保持不变密度。

`h_0`不应默认为已确认终态65 nm。为复用静态基准，可暂以 `h_0=75 nm → h_1=65 nm`作为**功能测试参数**，但必须继续标为非正式压印工况。运动时间应由Mach数、单步位移和出口稳定性共同确定，而不是沿用旧原型默认1 s或宏观−935 nm行程。

A1首先验收几何事件和边界运动；只有出口质量通量纳入账本后才进行B验收。若用户希望严格保留y周期，则A1只能改用带气体容量的FreeSurface初态，不能继续采用全充液不可压解释。

## 9. 下一次实施的文件与构建

仅在 `stage3_ex240_local/` 新增：

- `moving_punch_lattice.cpp`：真实SuperGeometry/SuperLattice主程序和严格run-id；
- `ex240MovingPunchIndicator.h`：带槽刚体解析几何、轨迹和交点；
- `dynamicBouzidiAdapter.h`：候选带算子、q与壁速更新；
- `dynamicMaterialTransaction.h`：真实节点事件、局部分布重建、提交/回滚；
- `movingBoundaryAudit.h`：材料哈希、周期缝、交点、质量/动量和非有限值统计；
- `Makefile`新增 `openlb-moving` 目标，继续通过本机 `/home/dell/openlb/default.mk`，显式限制 `CPP_FILES`，避免链接目录中其他独立main。

建议构建命令形式：

```text
make openlb-moving
```

实际运行应要求全新run-id，并在启动前写参数文件；先执行A0短测，A0通过后才执行A1的−10 nm功能测试。正式输出保存编译命令、OpenLB哈希、源文件哈希、启动命令、逐步CSV、逐帧几何/交点VTK、stdout/stderr、退出码和结束原因。

## 10. 失败与保护策略

- 每次运行写入唯一目录，既有固定几何和失败结果均不覆盖；
- 每一时间步先做transaction快照/事件日志，只有所有rank预检通过才提交；
- 提交前失败：保留旧材料、动力学和分布函数，记录拒绝原因；
- 提交后诊断失败：停止在首次失败步，保存前一有效checkpoint、失败态VTK和事件清单，不自动放宽阈值；
- 若候选带PostProcessor不能安全启停，或节点级动力学无法在现有公开接口下同步，不修改OpenLB库，停止并报告所需的最小库改动（带标签的处理器删除/重建和通信注册）；
- 不进入FreeSurface或正式供液，除非先确认液体去向、接触角和气体处理。

本轮到此停止：没有执行移动压头仿真，也没有把静态 `h=65 nm`升级为正式终态。
