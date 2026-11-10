# §2.1单胞周期假设与有限器件边界审读

日期：2026-11-08，Asia/Shanghai。作者授权逐段审读；本轮形成双语候选，不改正式稿、边界设置或冻结协议，不重新证明单胞定理或启动新仿真。

## 原段

> 采用单胞的前提是图案严格重复。对理想、严格周期的图案内部，一个周期单胞即可表示重复区域的流动，这正是单胞缩减计算量的依据。该前提不涵盖完整模具边缘、图案接缝处的过渡区，也不涵盖实际供液条件；本文未对这些情形作任何验证。

## 裁定

原段研究边界基本正确，尤其已经排除了边缘、接缝和实际供液，不应说成现稿把单胞当整片模具。需要补强的不是新计算，而是单胞描述的成立条件：几何严格重复之外，物性、驱动与边界也需匹配，并处于本文所设的固定全充液/稳态低惯性模型范围。用“理想重复图案的局部导度”取代可能被理解为整个有限图案流场的“重复区域的流动”。

## 条件与解释

1. **几何。** 横槽x方向周期P240nm，沿槽y方向在本理想直槽模型内平移不变；h/d/w及壁面条件在复制单胞间相同，h>0提供贯通液层。不能仅因局部槽宽相同，就称不同图案/占空比/槽方向的连接区与规则单胞等价。
2. **加载。** 本文使用均匀体积力驱动并取匹配的周期面，不是给一个有限域配置真实入口/出口或液滴边界。周期边界允许非零平均通量，但不会给出真实供液体积、进液位置或到达时间。连续解释沿用附录E的周期Stokes模型，未在本轮证明高惯性/动态/非周期加载的单胞精确性。
3. **边界与物性。** 固定、全充液、常黏度牛顿液体，静止无滑移壁面，周期面成对匹配。宏观间隙变化、液面推进、非均匀供液并不是当前单胞中的加载；相应过程能否采用此局部系数，需要另行模型与证据，不由本段保证。
4. **沿槽长度。** L_y240nm是计算单胞长度；几何沿y不变，不因此存在另一套物理槽纹波长。上一轮几何候选的这一澄清保持。
5. **尺度。** 对理想周期问题采用一个周期，是模型构型的周期描述。若将系数作为有限器件中的局部闭合，还需检查实际驱动/几何变化尺度与局部模型的相容性；本研究未测定距边缘多远可忽略影响，不给出若干倍P的排除距离或连续适用范围。

## 已有复制检查的角色

按G4冻结协议§1/§4，Nx2/4/8是在原P240nm、w120nm、h75/d100nm及dx2.5nm条件下复制图案，不是把真实槽/凸台宽度与物理周期同时放大。指标R=ρa/J与K采用相同面积归一化；不能混作有限长试样的总压降/总流量阻力。

本轮读取补充表S3及18份保存result，核实Lx=Nx×240nm、Ly240nm、h75/d100/w120/dx2.5及x_y周期，并复核表中K/R；基准a10⁵的R相邻变化复现：2→4均0；4→8沿槽8.714965623221221e−14、横槽3.80797839183066e−14。支持所查复制域/接缝数值一致性，不是RVE物理代表性或全地图精度认证。本轮未复跑几何/质量接受、重读所有诊断或测量真实边界影响。

§2.4已明确该检查不构成RVE证据，建议§2.1只一句回指，不重复上述数字。§2.4开头“若不成立后文全部结果失去意义”较绝对，后续审该节时可改为“这些设置与一致性检查限定后续比较的解释范围”；本轮不改该节。

## 三类有限器件边界

|区域/条件|单胞为何不能直接包含|本文能说到哪层|
|---|---|---|
|模具外缘|几何终止、有限域边界及外部压力/供液不再是无限重复|未计算边缘流场、附加阻力或影响距离|
|图案/宏块接缝|局部宽度、间距、方向或连接几何可能改变|只能描述理想规则区，未评估接缝通量与整体误差|
|实际供液|液滴位置/体积、储液区、进出口和液面随时间变化不由均匀体力单胞给定|K是指定构型的响应系数，不单独决定填充时间或完整模具流量|

这些是模型所排除的情形，不是本轮证明它们一定带来某一方向/幅度的误差；不把未计算写成实际已测的边缘效应。

## 版图证据的具体边界

本轮重读已有docs/ex240/ex240_layout_report.md：设计文件规则区采用240nm微节距，但宏块每50µm衔接，已有报告记载接缝有80nm额外间隙（x方向相邻图形起点320而非240nm，y方向亦有间隔）。这具体说明约1mm版图不能整体当作无例外的240nm微周期阵列。这里只复核报告内容与算术背景，未重新解析OAS、未测加工实物，也未求接缝水力响应。候选不堆入宏块尺寸，以便保持方法正文简洁；必要来源由补充S1承接。

## 中文候选

单胞计算用于表征理想重复图案在均匀驱动下的局部导度。几何沿x严格重复、沿y平移不变，液体在固定间隙内完全充满，固壁静止无滑移；物性与驱动在各单胞间一致，x、y周期面成对匹配。周期复制检查用于核对该设置下的数值一致性（§2.4），不用于确定真实器件的代表性尺度。模具外缘、宏块接缝及实际供液边界不包含在计算域内；这些区域对整体流动和填充过程的影响尚未评价，不能由本单胞结果确定。

## 英文对应候选

The unit-cell calculation characterizes local conductance in an ideal repeating pattern under uniform forcing. The geometry repeats exactly in x and is invariant along y. The fixed gap is fully filled with liquid, solid walls are stationary and no-slip, properties and forcing are identical between cells, and opposing x and y faces are periodically matched. Periodic-replication checks assess numerical consistency in this configuration (§2.4), rather than establishing a representative scale for a real device. Mold edges, boundaries between pattern blocks and actual supply boundaries are outside the computational domain. Their effects on overall flow and filling have not been assessed and cannot be determined from the present unit-cell results.

## 范围与停点

本轮实际读当前中英文单胞段及§2.4、附录E模型条件、当前D2 periodicity/几何定义、补充S8/TableS3、冻结G4协议和设计版图报告。S3实际文件名为Table_S3_periodic_checks.csv；原猜测periodic_forcing名未找到，按正文链接纠正，不将路径猜测当证据缺失。未找到所猜G4G3审计报告路径，不据其作结论，本轮使用已读协议/表/原结果。

来源哈希见source_manifest.json，复制记录字段与算术核对见periodic_evidence_check.json，保护与状态范围见verification.json。使用已读scientific-writing及academic-humanizer；程序性来源沿用§1.2第一段记录中Kassis等Scientific Agent Skills（2026，arXiv:2609.00065），不另添科学引文，无新增外网检索。

本轮仅本目录和两共享状态更新；正式稿、源码/周期边界、协议/门槛、原始数据/旧报告保持，摘要既有合入保持，引言及§2.1候选未合入。无编译/求解/拟合/场处理/原轨迹接受/run_id/Gate/上传，无新长算或边缘仿真授权。原S4 FAIL、reference_qualified=false、strict_error_bound_established=false、submission_ready=false保持。

下一具体动作：审§2.1的物性、松弛参数和时间步换算，检查参数设定顺序及加密时保持的物理量；若用户要求采用，再同步中英文单胞段。
