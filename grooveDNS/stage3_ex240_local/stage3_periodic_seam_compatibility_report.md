# 阶段三步骤4：pressure—x周期拼接兼容性诊断与第二候选报告

## 最终判定

**FAIL，继续停在步骤4。** 第二候选未满足短程验收，不允许进行约2000步延长
观察，也不允许进入步骤5单次材料转换。

本轮确定了两件不同的事：

1. OpenLB 的 x-periodic population communication 在本测试中顺序和值均正确，
   修复后 `(0,0,13)` 的失稳不依赖 periodic seam；
2. 应用层 q/material 邻居查询确实漏掉跨 seam 固壁链接。周期感知查询恢复了
   192条链接，但 C 的失稳时间和量级基本不变。

因此不能把新的 step209 事件认定为第二个
`LocalPressure × periodic × moving boundary` 根因。它是第一处边界闭合未完全
消除后，沿 z 方向向下传播并在凸台中心压力节点首先越过门槛的结果。

## 保护与新增文件

上一轮四个文件及原B/C结果只读保留，哈希复核未改变：

- `stage3_boundary_intersection_fix_report.md`：`8e396b...f430`；
- `boundary_intersection_d3q19_access_table.md`：`455a23...8b54`；
- `explicit_piston_operator_population_trace.cpp`：`81b788...e4ed`；
- `explicit_piston_boundary_intersection_fix.cpp`：`28fe9b...f69d`。

本轮新增：

- `explicit_piston_periodic_seam_diag.cpp`：逐算子、通信前后和映射来源诊断；
- `explicit_piston_periodic_seam_phase_control.cpp`：120 nm周期相位平移对照；
- `explicit_piston_periodic_seam_fix.cpp`：周期感知q/material最小候选；
- `periodic_seam_d3q19_source_table.md` 及本报告；
- 独立输出目录，未覆盖任何旧结果。

只在本目录 `Makefile` 增加独立目标。OpenLB库、其他阶段、原tmp和第一轮源码
均未修改。

三份新增源码 SHA-256 依次为
`dc083cbdec26fd8129cd25a8ecd23c84ec2dc9fc32a725be2119dcddb49fff6c`、
`cb41081b5d0b3a12b7be6addf01e78c377084fdf27045311f2f77228fbb6ab30`、
`92290ea2f166b92dae49ebf31effdb0d63b05561c0fab335862de28bcd5e26db`；
运行记录中的命令、退出码和结束原因保存在各自输出目录。

## `(0,0,13)` 局部拓扑

`(0,0,13)` 的物理坐标为 `(2.5,2.5,62.5) nm`，material 4，属于低 y
LocalPressure；周期对应 cell 是 `(47,0,13)`，物理坐标
`(237.5,2.5,62.5) nm`。必要邻域包括：

|cell|物理坐标(nm)|material/作用|关系|
|---|---|---|---|
|`(0,0,13)`|(2.5,2.5,62.5)|4 / LocalPressure|新首报警|
|`(47,0,13)`|(237.5,2.5,62.5)|4 / LocalPressure|x周期对应端|
|`(0,1,13)`|(2.5,7.5,62.5)|1 / fluid|y内部来源|
|`(0,0,12)`|(2.5,2.5,57.5)|4 / LocalPressure|z下邻居|
|`(0,0,14)`|(2.5,2.5,67.5)|4 / LocalPressure|z上邻居、原首报警|
|`(0,0,15)`|(2.5,2.5,72.5)|6 / ZouHe压力+Bouzidi|第一处修复交线|
|`(47,0,16)`|(237.5,2.5,77.5)|3 / solid punch|跨x映射固体邻居|

`(0,0,13)` 自身19个q全为-1，Bouzidi PostStream不处理它。完整19方向 raw
来源、周期映射、material、通信前后数值和最终来源见
`periodic_seam_d3q19_source_table.md`及原始CSV。

## OpenLB实际执行与周期数据时间层

本机版本仍为 `5953d8a-dirty`。实测与源码一致：

1. PreCollide communicator/processors；
2. LocalPressure momenta，随后同一 `CombinedRLBdynamics::collide` 内完成全19
   population reconstruction和BGK collision；
3. PostCollide population communicator；
4. block stream；
5. PostStream communicator；
6. moving Bouzidi PostStream；
7. PostPostProcess communicator；
8. statistics/output。

PostCollide 周期通信在 stream **之前**完成。对目标 cell 真正跨 x 的
`f10/f14/f15/f16`，padding通信后与映射端core逐位相等；stream后目标值也相等。
PostStream通信在 Bouzidi **之前**，但目标 cell 无q，两个阶段均不写它。
因此不存在“LocalPressure读了旧周期halo”“periodic覆盖LocalPressure core重构”
或“目标cell被Bouzidi重复处理”的证据。

源码依据仍是本机 `src/core/superLattice.hh`、`src/core/blockLattice.hh`、
`src/communication/blockCommunicationNeighborhood.hh`、
`src/geometry/cuboidDecomposition.hh`、`src/boundary/setBouzidiBoundary.h`、
`src/boundary/localPressure3D.h` 和 `src/dynamics/dynamics.h`。

## 新的第一个偏离population和operator

在 `(0,0,13)`，step209门槛跨越发生于 **streaming之后**：

- collision后 LocalPressure Mach=`0.0471304`；
- stream后 Mach=`0.0505617`；
- 随后的PostStream communication和Bouzidi均不再改变该cell。

对 LocalPressure 实际读取集合，stream造成的最大单population变化是
**f3**，其方向为 `(0,0,-1)`，stream来源为上方 `(0,0,14)`：

|step|stream造成的 Δf3|stream后Mach|
|---:|---:|---:|
|180|-3.89901e-4|0.0065242|
|190|-7.82217e-4|0.0132528|
|200|-1.56877e-3|0.0268425|
|209|-2.93399e-3|0.0505617|

该分量约每10步翻倍，异常增长早于step209门槛。`f8`在LocalPressure法向矩中
带2倍权重，step209的stream变化为`+1.47021e-3`，仍参与反馈；但在这个新cell
上，最先制造本地最大population偏离的阶段是 **streaming**，不是 periodic
communication，也不是该cell上的Bouzidi。

更上游的 `(0,0,14)` 在step209已达Mach=`0.04527`且速度方向相反；其状态通过
f3传给`(0,0,13)`。所以`(0,0,13)`成为新首异常，是因为第一候选压低了
`(0,0,15)`交线cell，却没有消除下面压力节点间的反向放大；加之全局扫描从低
x/低y开始，它首先被报告。周期对应的 `(47,0,13)` 在step209具有同样Mach，
不是一侧halo独有污染。

逐算子完整数据位于：

- `output/periodic_seam_operator_diag_v3baseline_v2_20260907/periodic_seam_operator_trace.csv`；
- `periodic_mapped_population_sources_step200.csv`；
- `periodic_mapped_link_neighbors_step200.csv`。

## 关键周期对照

诊断对照保持 x 周期、moving Bouzidi、LocalPressure、物性、速度轨迹和周期图案
不变，只把图案相位平移120 nm，使周期 seam 从凸台中心移到凹槽中心、凸台中心
移到域内部。结果：

- 仍在step209首次Mach>0.05；
- 最大值随凸台中心移到 `(23/24,0,13)`，不再位于x seam；
- step220 max Mach=`0.113345`，rho仍为有限的`[0.93219,1.05179]`；
- 这是诊断对照，不是生产边界方案。

故新失稳**不依赖x-periodic seam**，不能重新归因到一般周期通信错误。

## 确认的seam实现缺陷与第二候选

虽然population通信正确，原 q 构造直接读取 material-0 x padding，漏掉映射后
为solid的链接。明确例子是 `(0,0,15)` 的方向7和 `(47,0,15)` 的方向15。

第二候选只修改新独立程序中的邻居解析：越过x边界时先把格点索引映射到
`0..47`，再读取material并计算q；Bouzidi仍使用OpenLB周期halo，开放压力边界、
x周期、第一处交线压力闭合、物性、dt和轨迹均不变。没有裁剪、质量归一化、
黏度/时间步调整或材料转换。

结果每步恢复192条solid links，active links由31984增至32176；非法q/link和
错误solid映射均为0。这是有效的几何一致性修复，但不是稳定性修复。

## 三代C比较

|项目|原C|第一候选C v3|第二候选C|
|---|---:|---:|---:|
|首次Mach>0.05|157|209|209|
|首次rho越界|182|236|236|
|首次NaN/Inf|583|650步内无|650步内无|
|650步max Mach|已在583非有限，不适用|9.43345e11|9.40353e11|
|650步rho范围|非有限|[-5.48391e11,4.35299e11]|[-5.38276e11,4.36882e11]|
|最大速度位置|首次非有限`(0,0,9)`|`(47,47,13)`|`(0,0,13)`|
|非法link|0|0|0|
|材料转换|0|0|0|

原C诊断程序没有输出质量/出口通量，不能补造比较值。第一候选和第二候选的
对应量为：

|量|第一候选C v3|第二候选C|
|---|---:|---:|
|初始原始流体质量(kg)|7.20000e-18|7.20000e-18|
|650步原始流体质量(kg)|3.26069e-9|3.49466e-9|
|累计向外质量(kg)|-3.27726e-9|-3.52666e-9|
|最终相对质量收支残差|-2.30229e6|-4.44449e6|

这些最终质量和通量已经受数值爆发污染，不能解释为真实排液。

第二候选局部历史：step209时 `(0,0,13)` 和周期对应 `(47,0,13)` 的Mach均
`0.0524851`；`(0,0,14)`为`0.0464392`；第一处修复cell `(0,0,15)`仅
`0.0015065`。到650步四者均发散，因此第一处问题没有以原形式立即复发，
但整个压力节点链仍不稳定。

## B-650与第二候选C-650

B run-id `boundary_intersection_periodic_link_fix_B650_20260907`：

- PASS，650/650，退出码0；
- Mach=0，rho=[1,1]，速度=0；
- 初末质量相等，出口累计质量=0，质量收支残差=0；
- 非法link=0、材料转换=0、材料场不变。

C run-id `boundary_intersection_periodic_link_fix_C650_20260907`：

- **FAIL**，650/650，退出码3；
- step209首次Mach超限，位置`(0,47,13)`；step236首次rho越界；
- 650步无NaN/Inf，但max Mach=`9.40353e11`，rho严重越界；
- 非法link=0，材料转换=0，材料场不变；
- 质量、出口通量和质量收支均已发散，守恒验收失败。

正常执行到650步不等于物理验证通过。

## 对11个问题的回答与停止范围

1. `(0,0,13)`成为新首异常，是上方`(0,0,14)`异常经f3向下stream传播，且它
   位于等价凸台中心，不是因为x seam。
2. 新的首要偏离population是`f3`；异常增长至少在step180已清楚可见。
3. 在该cell第一个使其偏离并跨门槛的是streaming；周期通信和Bouzidi不写它。
4. 已确定**不依赖**x-periodic seam；相位平移对照仍在step209失败。
5. 第一处`f8/f17`修复对已定位交线有抑制作用，但只可称“局部正确且不充分”，
   不能称步骤4已验证修复。
6. 本轮没有证实第二个seam根因；实际是原压力—移动壁闭合残余沿压力节点传播。
7. 第二候选是周期感知q/material查询；它修正192条漏链，但不消除失稳。
8. B-650 PASS，未退化。
9. 第二版C-650 FAIL。
10. 不满足步骤4短程验收。
11. 不允许进入延长观察。
12. 不允许进入步骤5单次材料转换。

本轮未运行完整10 nm、2000步延长、液滴、润湿、空气或网格扫描，现已停止。
