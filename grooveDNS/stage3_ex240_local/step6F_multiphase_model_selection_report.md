# SIM-EC1XT240 STEP 6-F 多相填充模型选择报告

## 结论先行

本机 OpenLB 确实支持三维 Shan–Chen / pseudopotential 多相模型，但**不建议把当前 Shan–Chen 实现直接作为 SIM-EC1XT240 纳米填充的首选路线**。主要原因不是三维或显式几何不可用，而是当前通用 Shan–Chen 耦合在源码中明确标为“without wall interaction”，现有三维示例没有给出复杂固壁上的可指定、可校准接触角闭合。若自行加入壁面伪密度或流固作用力，接触角将成为需要重新标定的模型结果，而不是直接输入的物理边界条件。

**推荐首选：本机已有的三维 well-balanced Cahn–Hilliard 相场模型。** 它已有真实 D3Q19 三维接触角示例、显式 `THETA` 参数、`PHIWETTING`/`BOUNDARY` 字段、专用 `setBouzidiWellBalanced` 固壁接口，并以双 lattice 分别推进 Navier–Stokes 与相场。该路线更贴合当前需求中的“液体—空气—表面张力—指定润湿角—复杂显式固壁”。

这只是源码能力评估，不代表该模型已经在 5 nm 网格、100 nm 槽深和实际材料接触角下通过验证。本轮未修改代码、未编译、未运行仿真，也没有改变 STEP 6-A～6-D 或 FreeSurface 历史结果。

## 版本与检查范围

- 本机 OpenLB 源码目录：`/home/dell/openlb`。
- `rules.mk` 标注发行版为 `1.8r1`；当前 OpenLB 源码仓库 HEAD 为 `882924a9cfc8dcdf82909e39530789cb6f5ebcc4`。
- 既有项目报告中的 `5953d8a-dirty` 来自 OpenLB `rules.mk` 在案例工作目录执行 `git describe`，实际取到了 SIM240 项目仓库版本；它不能单独作为 OpenLB 源码哈希。后续新案例应分别记录 OpenLB HEAD 和案例源码哈希。
- 本轮只读取 `SIM_EC1XT240_CURRENT_STATE.md` 和 OpenLB 的多相源码/示例，没有重新扫描 STEP 5 历史报告。

## 1. Shan–Chen 支持情况

### 1.1 单组分多相 Shan–Chen

本机存在可运行的三维单组分实现：

- `ForcedShanChenBGKdynamics`；
- `ShanChenForcedSingleComponentPostProcessor`；
- `interaction::CarnahanStarling`、`ShanChen94` 等相互作用势/EOS；
- D3Q19 三维 `phaseSeparation3d` 示例；
- `RhoStatistics`、一层 coupling overlap 和明确的 `PreCoupling/Coupling/PostStream` 调度。

源码证据：

- `/home/dell/openlb/examples/multiComponent/phaseSeparation3d/phaseSeparation3d.cpp:39` 定义三维 D3Q19 lattice；
- 同文件 `:103-123` 设置 `ForcedShanChenBGKdynamics`、单组分 Shan–Chen coupling 和 Carnahan–Starling 参数；
- 同文件 `:125-128` 把统计与 coupling 放入 `PostStream` 自定义任务。

该分支可以形成液—汽密度分层，但相平衡密度、界面张力、界面厚度、伪势参数和温度/EOS相互耦合。把宏观液体/空气物性映射到纳米槽不能只复制单相 converter 参数。

### 1.2 双组分 Shan–Chen

本机也支持两套三维 D3Q19 lattice 的双组分模型：

- 两组 `ForcedShanChenBGKdynamics`；
- `PseudopotentialForcedCoupling<interaction::PsiEqualsRho, multicomponent_velocity::ShanChen>`；
- 两组密度、松弛频率、相互作用强度 `G`；
- 三维周期边界和 bounce-back 固壁。

源码证据：`/home/dell/openlb/examples/multiComponent/rayleighTaylor3d/rayleighTaylor3d.cpp:40-56`、`:67-70`、`:153-181`。

该方案显式保存两组分分布，适合不可混溶双组分研究，但界面扩散、两相黏度/密度比和固壁亲和性都要标定。对“液体填充、气体被排开”的物理图景可行，但实现和算力成本高于 FreeSurface，并且当前示例不能证明真实空气/液体高密度比与复杂润湿壁已经稳定。

### 1.3 物理参数化 pseudopotential 分支

`dropletSplashing3d` 提供另一条单 lattice 三维 pseudopotential 路径：

- `MultiphaseForcedBGKdynamics`；
- `PseudopotentialForcedPostProcessor<interaction::Polinomial>`；
- 分别输入液/汽密度、液/汽黏度、表面张力和界面厚度；
- `MultiPhaseUnitConverterFromRelaxationTime`。

源码位置：`/home/dell/openlb/examples/multiComponent/dropletSplashing3d/dropletSplashing3d.cpp:37-45`、`:122-191`。它比经典 EOS Shan–Chen 更直接地暴露物理量，但示例固壁仍仅用普通 bounce-back，没有展示指定接触角。因此它可作为“体相和表面张力”备选，不足以直接解决润湿填槽。

### 1.4 不建议优先采用的高级多组分分支

`airBubbleCoalescence3d` 含三组分、Peng–Robinson VLE、专用 `MultiPhaseUnitConverter` 和大量混合规则参数，且示例注释要求通过源码宏启用第三组分。它证明 OpenLB 有更复杂的三维热力学能力，但对当前首个纳米填充基准过重，参数可辨识性也最差，不建议作为起点。

## 2. 固液润湿与接触角

### 2.1 Shan–Chen 路线的现状

本机通用 `PseudopotentialForcedCoupling` 在
`/home/dell/openlb/src/dynamics/shanChenForcedPostProcessor.h:222-226` 明确标注为：

`Shan Chen coupling without wall interaction`

其核心循环只从相邻 lattice cell 的 `STATISTIC` 密度计算流体间伪势，并在 `:258-280` 写入两组流体力；没有接收固体材料、壁面伪密度、壁面亲和系数或目标接触角参数。旧三维单组分 postprocessor 的头文件也作相同“不含壁面相互作用”说明。

因此，在不新增模型代码的前提下，普通 bounce-back 只保证无穿透/无滑移，**不能等价为已知接触角**。未来若走 Shan–Chen，至少需要应用层增加流固伪势或虚拟壁密度，并通过平壁静滴反算“参数—接触角”关系；锐角/凹角还要单独验证。该校准不能从材料接触角直接推定，也不能沿用 FreeSurface 的 `wall EPSILON=1`。

### 2.2 本机已有的定量接触角路线

`contactAngle3d` 使用 well-balanced Cahn–Hilliard 模型：

- Navier–Stokes lattice：`MultiPhaseIncompressibleBGKdynamics`；
- 相场 lattice：`WellBalancedCahnHilliardBGKdynamics`；
- 耦合：`WellBalancedCahnHilliardPostProcessor<LinearTauViscosity>`；
- 固壁：NS 使用 Bouzidi，相场使用 `setBouzidiWellBalanced`；
- 参数：`THETA`、`INTERFACE_WIDTH`、`SURFACE_TENSION`、液/气密度和松弛时间；
- 字段：`PHIWETTING`、`BOUNDARY`、`CHEM_POTENTIAL`；
- 示例还通过液滴轮廓拟合数值接触角。

源码证据：

- `/home/dell/openlb/examples/multiComponent/contactAngle3d/contactAngle3d.cpp:25-29` 说明三维 well-balanced 接触角模型及低寄生速度/高密度黏度比目标；
- 同文件 `:39-50` 定义两套 D3Q19 lattice；
- 同文件 `:137-175` 设置两种 Bouzidi、润湿统计、两层通信及 `THETA`；
- 同文件 `:228-241` 初始化 `PHIWETTING` 和固体 `BOUNDARY` 字段；
- `/home/dell/openlb/src/dynamics/phaseFieldCoupling.h:799-825` 是实际三维壁面接触角更新，使用 `cos(theta)`、界面宽度和壁法向；
- `/home/dell/openlb/src/boundary/setBouzidiBoundary.h:1077-1118` 是基于 `SuperGeometry` material/indicator 的三维 `setBouzidiWellBalanced` 接口及通信注册。

重要细节：示例把用户角度经过 `pi-theta` 转换后写入 lattice 参数，不能把角度数值机械直传。示例默认界面宽度为4个格点，且示例参数中的液/气 lattice density 都为1；所以它证明了接口和接触角响应，不证明真实液—气密度比已经通过。

## 3. 与 SIM-EC1XT240 显式几何的兼容性

### 可直接复用的部分

- `SuperGeometry` 中的240 nm周期、60/120/60 nm材料布局和100 nm槽深定义；
- 固体 material indicator、解析固壁 indicator、x/y周期设置；
- 固定间隙下的材料数量、周期拼接、有效壁面和VTK检查方法；
- 单相阶段已经验证的物理坐标、core/overlap统计口径。

### 不能直接复用的部分

- 现有 D3Q19 单相 lattice、BGK populations 和 Zou/He/FreeSurface 状态不能原样继承；
- well-balanced 路线需要 NS 与 Cahn–Hilliard 两套 lattice、额外字段、coupling、化学势与两层邻域通信；
- Shan–Chen 双组分也需要两套 lattice 与 `STATISTIC/FORCE/EXTERNAL_FORCE` coupling；
- 现有动态压头 material transaction 与多相界面守恒没有验证，首轮必须保持固定几何。

### 几何风险

轴对齐平面与周期拼接原则上兼容。真正的风险在直角交汇、凸台边缘和沟槽凹角：润湿边界依赖离散法向和邻域相场，平壁接触角示例不能证明边/角节点也给出同一宏观接触角。应逐类审计平面、凸角、凹角、周期seam的边界处理，不得只凭材料图判定兼容。

## 4. 三维计算可行性

### 功能可行

三维能力已有直接源码证据：`phaseSeparation3d`、`rayleighTaylor3d`、`dropletSplashing3d` 和 `contactAngle3d` 均为真实三维案例。周期、bounce-back、Bouzidi、MPI overlap 和 VTK 输出都有对应实现。因此单周期固定间隙的三维验证在软件架构上可行，不需要先改 OpenLB 库。

### 数值与成本限制

- 当前240×240×165 nm、dx=5 nm的量级约为48×48×33个core节点；两套D3Q19 lattice加相场字段在单周期内仍可控，但明显高于单相成本。
- 相场界面若取4–6格点，在dx=5 nm时厚度约20–30 nm，占60 nm凸台半宽和100 nm槽深的显著比例。界面不是几何上“无限薄”的空气—液体面，必须报告这一尺度比。
- dx减半后节点数约增8倍，同时扩散界面和毛细时间尺度使总计算量进一步上升。
- 两相高密度比、低黏度气体、锐角润湿与寄生流的组合是主要稳定性风险。Mach低并不足以证明相场质量、化学势和接触角正确。
- 240 nm图案周期不提供真实排气出口。若x/y均周期且气体显式存在，困气质量将保留在局部域内；这与固定参考压力气相或开放排气是不同物理问题。

因此结论为：**三维单周期固定几何可行；直接扩展到动态压头或大区域尚无依据。**

## 5. 模型对比与选择

|候选|三维支持|表面张力/密度比|接触角|显式固壁|当前适用性|
|---|---|---|---|---|---|
|双组分 Shan–Chen|有，D3Q19示例|通过G、两组密度和松弛率间接控制|当前通用coupling无壁面相互作用；需自建并校准|普通bounce-back可用|备选，不宜首发|
|单组分 Shan–Chen + EOS|有，D3Q19示例|EOS/温度/G耦合，标定复杂|未见当前三维复杂壁定量接口|材料场可接|相分离研究可用，填槽首选性低|
|Polynomial pseudopotential|有，D3Q15示例|直接输入液/汽密度、黏度、sigma、界面宽度|示例未提供指定角度|bounce-back可用|体相基准备选|
|Well-balanced Cahn–Hilliard|有，D3Q19接触角示例|显式rho_l/rho_g、tau_l/tau_g、sigma、界面宽度|显式`THETA`及三维润湿壁处理|Bouzidi + `setBouzidiWellBalanced`|**推荐首选**|
|多组分Peng–Robinson|有三维示例|最完整、参数最多|未形成当前任务的简洁壁面路径|可扩展|当前过度复杂|

## 6. 建议的后续两相填充路线

### Gate 0：独立构建与版本冻结

新建独立 well-balanced Cahn–Hilliard 验证目录，不修改 FreeSurface、STEP 5 或 STEP 6-A～6-D。记录 OpenLB HEAD、案例hash、两套descriptor、operator执行顺序和overlap请求。首轮不用目标几何。

### Gate 1：三维平壁静滴接触角

从本机 `contactAngle3d` 派生一个物理单位案例，固定一组已知目标接触角，不做扫描。验收：相场总量、rho范围、最大寄生Mach、Laplace压差、界面厚度、数值接触角及时间收敛。必须先证明输入角度和测得角度的约定一致。

### Gate 2：三维平界面与自由液滴

分别验证无壁平界面和自由液滴，检查相场质量、压力跳变、表面张力和寄生流。液/气密度及黏度先采用数值上可验证的冻结组合；若不等于实际材料值，应明确为功能基准，不能冒充真实工况。

### Gate 3：简单矩形毛细槽

使用固定平直槽和液池，显式气相，验证接触角驱动方向、Washburn型前沿趋势、液相/气相质量、界面速度和角点行为。此处专门检查 `setBouzidiWellBalanced` 在平面、凸角和凹角的处理。

### Gate 4：直角交汇固定间隙

迁移到已验证的直角交汇几何，只做固定间隙。与STEP 6-D单相路径对照：主槽进入、侧槽分流、低速区、界面滞留和气体连通性。周期域内若无排气路径，应将结果定义为封闭/周期困气基准。

### Gate 5：SIM-EC1XT240 单周期固定间隙

最后迁移到240 nm周期显式结构。输出相场、rho、pressure、velocity、化学势、液/气质量、填充率、接触线和角点局部网格审计。完成至少dx=5 nm功能验证后，必须评估界面宽度相对60/100 nm结构尺寸的影响，才能讨论物理结论。

动态压头不属于以上首轮路线。只有固定几何两相质量和润湿通过后，才重新评估移动material/Bouzidi与相场守恒的联合更新；不能直接把现有单相动态事务套入相场模型。

## 对用户五个问题的直接回答

1. **Shan–Chen支持情况？** 支持单组分、双组分及三维D3Q19案例，也有物理参数化pseudopotential三维分支；软件能力存在。
2. **固液润湿/接触角如何实现？** 当前通用Shan–Chen coupling没有壁面相互作用；需额外流固伪势并标定。现成且更明确的方案是well-balanced Cahn–Hilliard的`THETA + PHIWETTING + setBouzidiWellBalanced`。
3. **与显式几何兼容吗？** 静态`SuperGeometry`、周期和固体indicator可复用；两相lattice与边界必须独立重建。锐角/凹角润湿仍需专门验证。
4. **三维可行吗？** 单周期固定几何在架构和规模上可行；真实密度比、界面厚度、寄生流与排气边界尚未验证。
5. **后续建议？** 选择三维well-balanced Cahn–Hilliard为主线，按“平壁接触角→自由界面/Laplace→矩形毛细槽→直角交汇→SIM-EC1XT240固定间隙”逐门禁推进；Shan–Chen保留为对照/备选，不先开发自定义润湿扩展。

## 停止点

本报告只完成模型选择和实施路线评估。没有继续调整 FreeSurface，没有修改任何现有源码或数值结果，没有运行多相仿真，也没有进入动态压头或扩大区域。

Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is **SIM-EC1XT240**.
