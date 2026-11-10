# 补充材料：研究方法、数值参考与来源记录

配套正文：`SIM240_中文稿_导师审阅版_20261022.md`。

编号版本：2026-10-24；2026-10-27按作者采用范围增补表S5及限定文字。作者审阅稿；本文件确定补充材料S1—S11及表S1—S5的编号与对应内容，尚未完成期刊版式验收或远端发布。所列数据来自既有D2/D3及历史基准，不纳入正在另行开展的D4扩展计算，也不替换正文原有V2修正关系。

记录的PASS、独立退出码、几何检查、网格证据和构建来源分别报告。编号完成不改变数值或物理验收状态。

<a id="sm-index"></a>

| 补充材料 | 内容 | 对应正文 | 数据表 |
|---|---|---|---|
| S1 | 几何、采样与运行清单 | §2.1、表1 | 表S1 |
| S2 | 当前数值实现与物性换算 | §2.1、式1 | — |
| S3 | 边界连线与低Mach诊断 | §2.1 | — |
| S4 | 停止条件与统计 | §2.1、§3.1 | — |
| S5 | 通量、输运系数与参考高度 | §2.2、式2 | — |
| S6 | 局部立方律的一维平均关系 | §2.3、式3 | — |
| S7 | 双网格敏感性 | §2.3表2、§3.3表4 | 表S2 |
| S8 | 周期复制与三驱动力检查 | §2.4 | 表S3 |
| S9 | 平板基准与历史三网格 | §3.2—3.4 | 表S4、S5 |
| S10 | 历史构建来源与日志 | §2.1、§3.4 | — |
| S11 | 方法引文核实边界 | 方法相关引文 | — |

<a id="sm-s1"></a>

## S1 几何、采样与运行清单

规则区的240 nm周期、120 nm条带宽度与现有[版图解析报告](/home/dell/yuanyuanxu/SIM240/docs/ex240/ex240_layout_report.md)相符。设计文件`SIM-EC1XT240.OAS`的SHA256为`209fbd4b907dc591c8786035face94de7df05fd10debf7e73dfc51a186ac0bfc`。这是设计版图来源，不能替代加工后尺寸实测；2026-10-22至23日核对确认文件身份与解析记录一致，未重新运行OAS解析。

主地图在h=50、75、125 nm时各取d=25、50、75、100、120 nm；h=25 nm仅取d=25、50、100 nm。18种几何各施加P（沿槽+y）与T（跨槽+x）驱动，得到36个主方向点。

<a id="table-s1"></a>

**表 S1　D2/D3地图与附加检查逐运行清单（52项）**

完整表：[Table_S1_run_inventory.csv](Table_S1_run_inventory.csv)。其中主地图36项、加密8项、黏度对照2项、斜向6项。表中逐行给出几何、方向、网格、K、原始结果路径、运行清单、日志、二进制哈希及独立退出码。

这52项不包含S8的周期复制/多力检查或S9的历史平板/三网格基准。不同证据清单可能复用同一物理基准，不能把文件条数相加称为独立新运行数。

<a id="sm-s2"></a>

## S2 当前数值实现与物性换算

[当前D2源码](/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp)给出D3Q19_FORCE、ForcedBGK、τ=1、Lx=Ly=240 nm、均匀加速度a=10⁵ m/s²。先设ρ=1000 kg/m³和ν=10⁻⁶ m²/s，由μ=ρν得1 mPa·s。物性固定后，dt=(τ−1/2)dx²/(3ν)，因此dx=5/2.5 nm分别对应dt约4.1667e−12/1.0417e−12 s。两个μ=15 mPa·s工况与主地图分列。

当前OpenLB的[ForcedBGK定义](/home/dell/openlb/src/dynamics/dynamics.h:224)使用PlainGuo；[computeU实现](/home/dell/openlb/src/dynamics/momenta/elements.h:1601)加入FORCE/2。当前Makefile与源树是实现证据，不自动绑定每一历史二进制，来源限制见S10。

<a id="sm-s3"></a>

## S3 边界连线与低Mach诊断

正文特指的46项D2主地图、加密和黏度检查均记录q_min=q_max=0.5。包含6项斜向检查的52项记录也满足同一数值；所保存最大Mach跨工况范围为5.69301195e−10至4.06765288e−7。

原始boundary_audit、precheck结果与diagnostics存在性记录见[既有逐项支持审计](/home/dell/yuanyuanxu/SIM240/docs/reports/Methods_support_audit_20261022/support_audit.json)。这些是已保存审计输出的核对，未在本次编号过程中重建几何或重算全程局部场。q=0.5表示半链长求交情形，不证明边界零误差。

<a id="sm-s4"></a>

## S4 停止条件与统计

D2采用最后1000条主通量样本，计算样本标准差除以均值绝对值、极差除以均值绝对值，以及交叉通量绝对峰值。停止阈值分别为10⁻⁶、5×10⁻⁶与10⁻¹² m²/s。D3斜向存在真实交叉通量，按该算例自己的统计判据处理，不混用主轴绝对交叉通量条件。

36点末窗独立复算见[Methods_followup_relstd_20261022.json](/home/dell/yuanyuanxu/SIM240/docs/reports/Methods_followup_relstd_20261022.json)。以m=1−rel_std/10⁻⁶定义相对余量，27点不足1%、9点不足0.1%。这是已执行的指定统计核对；停止条件本身不是空间精度或完整物理验收证明。

<a id="sm-s5"></a>

## S5 通量、输运系数与参考高度

对流体核心节点累加物理速度乘dx³，再除平面面积A_plan，得到J，单位m²/s；K=μJ/(ρa)，单位m³。等宽槽/凸台的体积等效高度为H_ref=h+d/2，故J=H_ref〈u〉_Ω，通常渗透率κ=K/H_ref，单位m²。

表S1保留原始K与结果路径。较旧结果未逐项打印全部物性字段时，可利用记录的τ、dx、dt检查ν的转换一致性，但不能把这种反算当成缺失的历史源码或构建证明。

<a id="sm-s6"></a>

## S6 局部立方律的一维平均关系

正文文献[4] Patir–Cheng 1978印刷第15页式（23）、（24），分别给出横向调和平均与纵向算术平均流量因子。为避免原文归一化高度与本稿残余间隙混同，以h0表示归一化高度、H表示局部总间隙。乘回h0³/12后，关系为K_parallel=〈H³〉/12，K_perp=1/(12〈H⁻³〉)。H=h与h+d各占一半，即得正文式（3）；d=0时两式均退化为h³/12。

指定原文页已在2026-10-22至23日核对中渲染目视检查，记录见[原文核对报告](/home/dell/yuanyuanxu/SIM240/docs/reports/Methods_support_audit_20261022/REPORT.md)。此关系成立于所用Reynolds局部模型内，不证明显式台阶流动或唯一耗散机制。第三方论文全文未复制进本补充材料目录。

<a id="sm-s7"></a>

## S7 双网格敏感性

<a id="table-s2"></a>

**表 S2　四种几何、两个方向的双网格比较（8行）**

完整表：[Table_S2_refinement.csv](Table_S2_refinement.csv)。几何为(25,100)、(50,100)、(125,25)、(125,120) nm；每行列K5、K2.5、系数变化、两种参考网格的模型偏差及百分点差。K变化定义为100(K2.5/K5−1)，以5 nm值为分母；模型偏差变化为E2.5−E5。

最薄跨槽K变化为−4.43073188%，模型偏差变化为+5.39475470个百分点。两个网格只给出已查条件下的敏感性，不能确定观测阶、GCI或连续参数域误差界。

<a id="sm-s8"></a>

## S8 周期复制与三驱动力检查

<a id="table-s3"></a>

**表 S3　基准几何的周期复制与多力原始记录（18行）**

完整表：[Table_S3_periodic_checks.csv](Table_S3_periodic_checks.csv)。三个批次分别为`g4_period_nx2_fields_v1_20261012T001316+0800`、`g4_period_nx4_fields_v1_20261012T105719+0800`、`g4_period_nx8_fields_v1_20261012T163341+0800`；每批Nx固定，含P/T两方向及a=5×10⁴、10⁵、2×10⁵ m/s²。

冻结条件见[周期域协议](/home/dell/yuanyuanxu/SIM240/CASE/03_grid_convergence/G4_EX240_period_convergence/PERIOD_CONVERGENCE_PROTOCOL.md)：h=75 nm、d=100 nm、dx=2.5 nm。a=10⁵时两方向R的2→4相对差均0，4→8分别8.71496562e−14、3.80797839e−14。每级K的跨度除以均值，沿槽最大2.47850560e−8、跨槽最大3.66006070e−8。Nx2沿槽K与历史同网格基准的相对差为6.89448e−14。

这些证据支持该基准几何在所检力范围内的线性响应和周期复制数值一致性，不表示全部36个5 nm样点各自做过多力检查，也不是物理RVE收敛证明。编号工作没有重做全部原数值门禁或人工质量轨迹放行。

<a id="sm-s9"></a>

## S9 平板基准与历史三网格

<a id="table-s4"></a>

**表 S4　历史三网格基准原始值与原记录状态（9行）**

完整表：[Table_S4_grid_archive.csv](Table_S4_grid_archive.csv)。每个网格5/2.5/1.25 nm包含Smooth75、EX240_parallel、EX240_perpendicular；目录见[历史归档](/home/dell/yuanyuanxu/SIM240/CASE/03_grid_convergence/G2_EX240_grid_convergence/archive/g2_grid_20260917T165045+0800)。

平板积分K相对h³/12的误差依次为0.44444079%、0.11103511%、0.02715688%。历史1.25 nm横槽原记录PASS=false、独立exit3；该失败原样保留，可计算GCI不能使其自动通过。

后续方案C保存有PASS=true与独立exit0，但其初始manifest中formal_reference_accepted=false；本材料不替代未恢复的正式放行记录。历史基准的使用范围与源码/构建来源仍分别判断。

<a id="table-s5"></a>

**表 S5　历史基准的条件性 Richardson/GCI 估计（6项）**

完整数值表：[Table_S5_conditional_gci.csv](Table_S5_conditional_gci.csv)。原始三格值与原记录状态另见表 S4。细、中、粗网格分别为1.25、2.5、5 nm，$r_{21}=r_{32}=2$，$F_s=1.25$。平板间隙为75 nm；沟槽基准为$h=75$ nm、$d=100$ nm、周期240 nm、槽宽120 nm。沿用原协议的$\rho=1000$ kg/m³、$\mu=1$ mPa·s、$a=10^5$ m/s²与$\tau=1$；[原协议](/home/dell/yuanyuanxu/SIM240/CASE/03_grid_convergence/G2_EX240_grid_convergence/STEP3_PROTOCOL.md)保存完整几何及参数。K单位m³；eta方向为该方向K除以同网格平板K，anisotropy为沿槽K除以横槽K，两者无量纲。方法参照配套正文[10]，原文版本核实范围见S11。

| 指标 | p | 外推值 | ea (%) | e_ext (%) | GCI_fine (%) | 依赖历史细T失败点 |
|---|---:|---:|---:|---:|---:|---|
| K_smooth | 1.990910 | 3.515588485e-23 | 0.083855 | 0.028196 | 0.035235 | 否 |
| K_parallel | 1.512988 | 9.754563861e-23 | 0.185350 | 0.100073 | 0.124966 | 否 |
| K_perpendicular | 1.256172 | 4.339399834e-23 | 0.612125 | 0.442769 | 0.551022 | 是，FAIL/exit3 |
| eta_parallel | 0.939763 | 2.773587499 | 0.101409 | 0.110564 | 0.138053 | 否 |
| eta_perpendicular | 1.088414 | 1.233638776 | 0.527826 | 0.470801 | 0.585744 | 是，FAIL/exit3 |
| anisotropy | 1.098181 | 2.248566102 | 0.424178 | 0.370433 | 0.464763 | 是，FAIL/exit3 |

令$\phi_1$、$\phi_2$分别为细格和中格结果，采用统一符号定义外推值$\phi_{\mathrm{ext}}=\phi_1+(\phi_1-\phi_2)/(r^p-1)$，$e_a=|(\phi_1-\phi_2)/\phi_1|$，$e_{\mathrm{ext}}=|(\phi_{\mathrm{ext}}-\phi_1)/\phi_{\mathrm{ext}}|$，$GCI_{\mathrm{fine}}=F_s e_a/(r^p-1)$。表中误差与GCI列均以百分数报告；CSV保留原始三格值与完整精度。

**失败记录随表披露：** 历史1.25 nm横槽运行相对质量指标为$1.1967043900362632\times10^{-10}$，超过冻结阈值$10^{-10}$，独立退出码3。K_perpendicular、eta_perpendicular与anisotropy均依赖该失败点。可计算的GCI不赋予该记录合格参考资格，不改变历史G2 Step 3的FAIL/INCONCLUSIVE判定。所列估计不外推其他几何，也不构成全参数域严格误差界。

沿槽与横槽观测阶分别为1.513和1.256。观测阶低于形式阶本身不足以判定计算不合格，也不能确认渐近性。使用同组三点拟合p后，归档相邻GCI比化为细中结果之比，因此历史“asymptotic range confirmed”标签不作为独立渐近区证据。所报GCI为该三格链的条件性估计。

对同一平板基准，细格积分K相对解析值的偏差为0.0271569%。将解析偏差与GCI统一以细格值归一，二者分别为0.0271495%与0.0352348%，估计幅度约为解析偏差的1.298倍。该比较仅支持此平板配置和积分量，不证明沟槽或其他几何具有相同的误差覆盖。

<a id="sm-s10"></a>

## S10 历史构建来源与日志

52份指定D2/D3运行清单均保存binary_sha256，四组分别22、22、6、2项。2026-10-22至23日逐项检查时，清单没有source_sha256、generated_source_sha256、openlb_commit、compiler或compile_flags字段。当前Makefile有编译配置，不能单独建立它与全部历史二进制的绑定。

48项为独立run.log，4项加密使用同一[批次日志](/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results/dx25_refine4_run_20261018.log)，其中逐项记录precheck和steady退出标记。部分result.case将dx2.5简写为dx2，须结合数值dx、manifest.case_id、目录及日志定位，不能改写原始标签制造一致性。

日志中的5953d8a-dirty字符串在当前Makefile中固定注入；当前源树CITATION.cff自标1.9.0，二者都不能独立证明每个历史运行所用的实际库版本。现有参数、输出、二进制哈希和日志可追溯，不等于完整历史源码与依赖环境已恢复。

2026-10-27复核：上述52份指定运行清单仍缺少这些源码/构建绑定字段，二进制哈希仍分为22/22/6/2四组。本机当前可定位的D2与D3两个二进制分别匹配其中22项与6项运行的记录哈希；这只确认现存二进制的身份，不能证明其历史源码、编译器或依赖版本。当前OpenLB源码快照和Makefile可检查实现，但不能用固定注入的版本字符串补成历史来源证据。核对范围见[本轮来源报告](../Methods_sources_data_audit_20261027/REPORT.md)及`provenance.json`。

<a id="sm-s11"></a>

## S11 方法引文核实边界

2026-10-27更新；文献编号沿用配套正文。以下是来源核对范围，不是对本项目精度的统一放行：

- **[4] Patir–Cheng**：现有合法本地全文的印刷第15页式（23）（24）已再次目视核对，支持一维Reynolds模型内的调和/算术平均关系。不能据此将局部模型视为显式台阶域精确解或唯一耗散机制。
- **[6] Dewangan–Datta 2018**：正式题名为 *Flow through microchannels with topographically patterned wall: A spectral theory for arbitrary groove depths*，European Journal of Mechanics–B/Fluids 70，73–84，DOI 10.1016/j.euromechflu.2018.02.004。Crossref及[作者机构出版目录](https://web.iitd.ac.in/~subhra.datta/publications1.html)一致；本轮未取得全文，书目问题已订正，具体幅度条件不标为已完成全文核验。
- **[7] OpenLB**：Crossref核得2021年、81卷258–288页，[软件官方目录](https://www.openlb.net/articles/)可定位同一DOI；官网旧目录使用2020年条目，按最终卷页采用2021年。软件论文身份不证明各历史运行使用了哪个OpenLB版本。
- **[8] Bouzidi**：Crossref的出版社登记元数据/摘要支持反弹结合空间插值的方案身份，题名、作者、2001年、13(11)卷3452–3459页与DOI相符。AIP全文请求被拒绝，本轮未逐式比较原文与项目实现；q=.5等项目事实由保存记录和当前实现另核，不以摘要保证任意壁距的精度。
- **[9] Guo**：Crossref核对PRE65(4)、046308、2002年及DOI。当前OpenLB的`ForcedBGKdynamics`明确使用`forcing::PlainGuo`，`ForcedMomentum::computeU`加入`FORCE/2`，支持当前实现描述；APS全文接口返回401，本轮未逐式核原文，当前源码也不自动绑定所有历史二进制。
- **[10] GCI**：已取得[ASME官网方法文稿](https://www.asme.org/wwwasmeorg/media/resourcefiles/shop/journals/jfenumaccuracy.pdf)，实际查看PDF第6—7页（文稿页4—5）的步骤3—5及式（3）—（7），支持三格、观测阶、外推值和GCI的定义。该文稿列四位作者，与2008年期刊发表版的书目信息并非同一版，不能冒称逐页核对了期刊发表版。正文保留发表版引文；完整版本对应尚未闭合。方法有依据不使历史质量FAIL转为通过，也不建立全图严格误差界。

全文、元数据、当前源码、保存输出、历史构建与科学验收分别记录；未取得全文不等于文献不存在。完整访问记录、原始页预览及逐项裁定见[本轮核对报告](../Methods_sources_data_audit_20261027/REPORT.md)。本地原始支持记录[旧审计报告](../Methods_support_audit_20261022/REPORT.md)保留当时范围，不覆盖旧证书。第三方文献及本轮证据没有发布到共享仓库。
