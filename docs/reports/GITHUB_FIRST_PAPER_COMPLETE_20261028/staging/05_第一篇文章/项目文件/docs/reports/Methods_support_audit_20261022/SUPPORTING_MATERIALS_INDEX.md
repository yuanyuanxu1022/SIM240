# 方法章支持资料定位索引（本地作者审阅版）

对应稿件：`docs/reports/SIM240_中文稿_导师审阅版_20261022.md`，重点为§2及其直接指向的§3。

本索引是本地证据入口，不是已经发布或完成投稿打包的补充材料。数字、文件存在、原始输出的自报PASS、构建来源及独立验收分别处理。已核项目与缺口详见同目录`REPORT.md`与`support_audit.json`。


## 与配套补充材料的编号对应（2026-10-24）

以下对应只固定编号和定位；本目录原报告及 JSON 核对记录保留为原审计快照，不追溯改写为本轮结果。正文已采用三处限定句，补充材料的作者审阅版本见下表。

| 原索引 | 补充材料 | 内容 | 数据表 |
|---|---|---|---|
| S1 | [S1](../SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-s1) | 几何、采样与运行清单 | 表S1 |
| S2 | [S2](../SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-s2) | 当前数值实现与物性换算 | — |
| S3 | [S3](../SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-s3) | 边界连线与低Mach诊断 | — |
| S4 | [S4](../SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-s4) | 停止条件与统计 | — |
| S5 | [S5](../SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-s5) | 通量、输运系数与参考高度 | — |
| S6 | [S6](../SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-s6) | 局部立方律的一维平均关系 | — |
| S7 | [S7](../SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-s7) | 双网格敏感性 | 表S2 |
| S8 | [S8](../SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-s8) | 周期复制与三驱动力检查 | 表S3 |
| S9 | [S9](../SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-s9) | 平板基准与历史三网格 | 表S4 |
| S10 | [S10](../SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-s10) | 历史构建来源与日志 | — |
| S11 | [S11](../SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#sm-s11) | 方法引文核实边界 | — |

## S1 几何来源、方向与采样组合（§2.1、表1）

- 设计文件：[SIM-EC1XT240.OAS](/home/dell/yuanyuanxu/SIM240/docs/ex240/SIM-EC1XT240.OAS)。本轮SHA256与既有解析记录相同：`209fbd4b907dc591c8786035face94de7df05fd10debf7e73dfc51a186ac0bfc`。
- [版图解析报告](/home/dell/yuanyuanxu/SIM240/docs/ex240/ex240_layout_report.md)§4、§7给出规则区120nm条带宽度、240nm周期；§8讨论宏块接缝。属于设计版图口径，不是加工后尺寸测量；本轮核文件身份与报告，未重新运行OAS解析器。
- [逐运行清单](run_inventory.csv)：按原始result参数核得主地图18种几何、36方向点，以及8加密、2黏度对照、6斜向点；h25仅d25/50/100。原始定位索引为[52行run_id索引](/home/dell/yuanyuanxu/SIM240/docs/reports/第一篇_run_id索引_20261022.csv)。

## S2 当前数值实现与物性换算（§2.1、式1）

- [D2当前源码](/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp)：25–43行物性/尺寸/时间步；137–150行运行参数更新；654行ForcedBGK；704–705行格子加速度；475行computeU；515行体积分除平面面积；802–803行K。
- [当前Makefile](/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/src/Makefile)保存当前编译方式，但不能单独证明所有历史可执行文件的构建方式。
- [OpenLB ForcedBGK定义](/home/dell/openlb/src/dynamics/dynamics.h:224)、[半步力速度修正](/home/dell/openlb/src/dynamics/momenta/elements.h:1601)。只证明当前源树实现，不自动绑定全部历史运行。
- 格子黏度ν*=1/6，设物理ν=1e−6m²/s时，dx5nm对应dt4.1667e−12s、dx2.5nm对应dt1.0417e−12s。两项黏度对照另列，不能将μ15套给36点主地图。

## S3 周期、Bouzidi连线与Mach（§2.1）

原始52份result.txt均记录q_min=q_max=.5；其中正文特指的46份D2主地图/加密/黏度点是其子集。记录的最大Mach跨算例范围为5.69301195e−10至4.06765288e−7。边界审计、precheck结果和独立exit文件定位见run_inventory及support_audit的逐点artifacts字段。

上述是所保存审计/诊断的核对，不是本轮重新执行几何构造或全程局部场诊断。

## S4 停止条件与统计（§2.1、§3.1）

- 当前D2源码FluxWindow：1000样本，样本标准差/均值绝对值、极差/均值绝对值、交叉通量绝对峰值；停止逻辑见约745–795行。
- 36份末窗独立重算证据：[Methods_followup_relstd_20261022.json](/home/dell/yuanyuanxu/SIM240/docs/reports/Methods_followup_relstd_20261022.json)。本轮未重复该全部CSV统计，仅核资料入口；27点余量<1%、9点<0.1%属于该轮已核结果。
- 每点原始diagnostics.csv均存在；停止统计不能单独证明空间精度。

## S5 J、K与参考高度（§2.2、式2）

当前源码measure对流体核心节点累加物理速度×dx³，再除Aplan；K=μJ/(ρa)。几何占空比为.5时，体积/平面面积给出H_ref=h+d/2。与体积平均速度定义对应的κ=K/H_ref，单位m²。

已完成的逐点转换检查与模型比较见[上一轮逐点数据](/home/dell/yuanyuanxu/SIM240/docs/reports/Methods_and_Section4_review_20261022/per_point.csv)及其原始输入哈希；不是独立求解器结果。

## S6 局部模型的文献和推导（§2.3、式3）

Patir–Cheng 1978本地原文：[PDF](/home/dell/yuanyuanxu/SIM240/docs/reports/Jain_citation_audit_20261017/raw/patir1978_JLubrTech_100_12-17.pdf)。本轮实际渲染并检查PDF第4页（印刷页15）式（23）（24）。原式给出

\[
\phi_\perp=\frac{1}{h_0^3\langle H^{-3}\rangle},\qquad
\phi_\parallel=\frac{\langle H^3\rangle}{h_0^3}.
\]

这里以h0区别该文归一化高度与本稿的残余间隙h，H表示局部总间隙。乘回h0³/12，分别得到调和与算术导度。对H=h或h+d各占一半，正好得到本稿式3。该核对支持Reynolds局部模型内的一维平均关系，不证明它等于显式台阶流动，也不从误差符号确定唯一机制。

原始渲染页及提取文本保存在本目录；没有修改源PDF。

## S7 双网格敏感性（§2.3表2、§3.3表4）

四个几何为(25,100)、(50,100)、(125,25)、(125,120)nm，各P/T，粗细共16个数值，其中8个细网格为附加运行。

同目录support_audit.json的refinements从原始K直接计算：K变化使用100(K2.5/K5−1)，模型偏差变化使用E2.5−E5（百分点）。最薄跨槽为−4.43073188%，偏差变化+5.39475470个百分点。这是双网格敏感性，不能直接充当GCI或误差上界。

## S8 周期复制与三驱动力（§2.4）

- [冻结协议](/home/dell/yuanyuanxu/SIM240/CASE/03_grid_convergence/G4_EX240_period_convergence/PERIOD_CONVERGENCE_PROTOCOL.md)§2、4–6；h75/d100、dx2.5nm、Nx2/4/8，每级3力×2方向。
- 本轮采用的原始批次（不启动）：
  - `g4_period_nx2_fields_v1_20261012T001316+0800`
  - `g4_period_nx4_fields_v1_20261012T105719+0800`
  - `g4_period_nx8_fields_v1_20261012T163341+0800`
- 根目录：[G4 results](/home/dell/yuanyuanxu/SIM240/CASE/03_grid_convergence/G4_EX240_period_convergence/results)。每点为`<batch>/runs/nx{N}_{P|T}_a{5e4|1e5|2e5}/steady/`。
- 18份result/manifest/独立exit本轮已读取。R差：2→4两方向0；4→8为8.71496562e−14/3.80797839e−14。K跨度/均值：沿槽最大2.47850560e−8、跨槽最大3.66006070e−8。与正文舍入数字一致。
- 与归档dx2.5nm沿槽基准K相对差6.89448e−14。

范围限于该基准几何和被检力/网格；不能代表36个5nm样点均做了多力检验。本轮未独立重做18点的全部10项门禁或人工质量轨迹放行，不升级Gate。周期复制证明数值不变性，不是物理RVE收敛。

## S9 平板与历史三网格（方法交叉指向§3）

[归档入口](/home/dell/yuanyuanxu/SIM240/CASE/03_grid_convergence/G2_EX240_grid_convergence/archive/g2_grid_20260917T165045+0800)包含SOURCE_MANIFEST、三网格报告与原始runs。实际在`archive/`，不应再指向已过时的`results/g2_grid_...`。

本轮回读9份原始result与独立exit，复算平板三个误差，与0.444%/0.111%/0.0272%一致。历史1.25nm横槽仍为记录PASS=false、独立exit3，不能因可算GCI而抹除。方案C的结果存在、记录PASS=true且独立exit0，但初始manifest仍formal_reference_accepted=false；本轮未恢复或替代正式放行记录。

这些基准证据与G4检查另列，不计入S1中用于D2/D3地图与附加检查的52项运行清单；不能把“52次”理解为整个项目全部计算总数。

## S10 历史构建来源与日志（§2.1、§3.4）

- 52/52 run_manifest保存binary_sha256，分4组（22、22、6、2项）。52份清单均未记录source_sha256、OpenLB提交、compiler或compile_flags字段。当前Makefile/当前源树存在不能补成历史绑定。
- 48份独立run.log可定位；另外4项加密使用[共享批次日志](/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results/dx25_refine4_run_20261018.log)，其中逐项记录precheck/steady退出。四项缺独立run.log不等于缺日志。
- 部分result的case标签将dx2.5简写为dx2；manifest标签、目录、数值dx及共享日志标记可联合定位。保留原文件，不修改历史名称。
- 运行日志中的5953d8a-dirty字符串在当前Makefile中被固定注入，不能独立证明实际OpenLB版本。当前源树的CITATION.cff自标1.9.0，也不能反推所有历史运行使用这一版本。

原审计发现正文“每次运行均保存提交标识、编译配置并可据以复现”超出核实范围；2026-10-24已按REPORT候选句收紧，并指向补充材料S10。历史来源缺口继续保留，没有据此判定已存数值无效。

## S11 方法引文的核实边界

- [4] Patir–Cheng：本地原文指定页公式已核，见S6。
- [7] OpenLB：官方[文献目录](https://www.openlb.net/articles/)可定位该软件论文；当前实现另以源代码核对。软件论文不是历史运行版本记录，本轮未逐页重审该软件论文。
- [9] Guo：APS[官方论文页](https://journals.aps.org/pre/abstract/10.1103/PhysRevE.65.046308)核得题名、作者、2002年与PRE65/046308，并说明其体力处理研究；当前代码的PlainGuo与半步力另有静态实现证据。本轮未核该论文所有公式。
- [8] Bouzidi：DOI访问超时，原文全文本轮未取得；当前OpenLB边界实现及原始q审计可定位，但不将它们冒充论文全文核实。
- [10] GCI：本轮定位归档原始值与历史失败，未重新做全部GCI公式和文献方法逐项审计。

## 公开包状态

本地文件有明确路径，尚不等于已验收的公开支持资料包。当前还需要按正式图表/方法主张筛选文件、给出变量字典、恢复可恢复的历史绑定并标明其余缺口、核清数据权利和发布元数据。本轮没有上传、发布DOI或投稿。

2026-10-23收口注：共享仓库状态由项目最新交接单独记录；本索引未在本轮同步远端，也未对该共享包重新验收。不能将本地路径可用等同于审稿人已能从远端取得这些文件。
