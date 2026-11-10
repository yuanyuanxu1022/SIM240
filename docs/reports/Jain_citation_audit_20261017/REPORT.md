# Jain 2017 后续引文筛查（2026-10-17）

> **2026-10-17 学位论文原页复核补充：** 用户提供 Ban 2021 博士论文，相关第2、3章已经审读并目视核查公式/验证页面；**【2026-10-17 22:15 更新】两篇期刊出版 PDF 均已取得并逐式核对**：`raw/ban2020_JVSTB_38_022601.pdf`（38(2):022601）、`raw/ban2021_JVSTB_39_012601.pdf`（39(1):012601，Editor's Pick）。其式 (8)(9)(10)/(9)(10) 与博士论文第 2/3 章、Jain 2017 **完全一致，一字未改** ⇒ 原"不把学位论文自动称作期刊完整版"的谨慎**可以核销**（见 `BAN2021_JOURNAL_ABSORPTION.md`）。详见[作用与边界核查](../Ban_dissertation_relevance_20261017.md)。Ban仍采用等效方向K，相关章节未见目标的显式矩形槽K误差标定；Fig.2.7检验的是毛细压力。以下早期“仅见摘要”由本补充限定更新；既有吸收笔记中的过强结论以该核查报告§6纠正。Scholar/Asta及Cochrane等缺口不变。


**总评：在本次可核实引文证据中，未发现“全充液单相矩形直角槽的Jain/局部立方律方向输运系数定量误差标定”直接先例。** 这不是全球不存在的结论：Google Scholar的Cited by列表未取得。【**2026-10-17 22:15 更新**】原"七篇候选中只有 Yin2018 取得全文、其余六篇仅摘要"的状态已改变——**Ban 2020、Ban 2021（期刊版）、Cochrane 2018、Dewangan 2020 四篇全文已取得并逐节吸收**（`raw/` 下均有 PDF，各附独立吸收报告），Kamrin 2010 全文（arXiv）亦已取得；尚未取得全文的仅 Kuo 2026（Springer 订阅，摘要已足）与 TCFD 2024 正文（摘要已取得，槽形已判定）。**判据 a/b/c 的证据层级因此由"仅见摘要"整体升为"全文已核"**，但判定结论不变。

## 1 检索覆盖与实际完成度

目标：Jain, A.; Spann, A.; Cochrane, A.; Schunk, P. R.; Bonnecaze, R. T. (2017), *Fluid flow in UV nanoimprint lithography with patterned templates*, Microelectronic Engineering173,62–70，DOI[10.1016/j.mee.2017.04.001](https://doi.org/10.1016/j.mee.2017.04.001)。

| 来源 | 本轮实际情况 | 能代表什么 |
|---|---|---|
| Google Scholar | 精确题名结果页曾返回目标的`cites=14393388769843840999`入口；打开Cited by后触发流量验证/CAPTCHA，未取得可逐条核查的列表 | **未完成用户要求的Scholar Cited by逐条筛查**；不绕验证、不伪装成功 |
| Semantic Scholar | 目标citationCount=9；citations接口取9条、next不存在 | 完整取到该索引当次返回的9条，不等于Scholar全集 |
| OpenCitations | 先count=11，后citations=11 | 11条计数与列表对齐，无分页截断 |
| OpenAlex | 目标实体cited_by_count=11，ID W2605348563；取引文列表429公共预算耗尽 | 未取到列表，不解释为0命中；未注册账号、未新增或使用密钥 |
| Crossref | 目标is-referenced-by-count=11；逐个解析并核对12个候选DOI的参考文献，全部确有目标DOI | 书目身份及引文关系核验；参考文献元数据不等于读过全文 |
| ScienceDirect预览 | 显示Cited by12并列部分题名，未取得完整Scopus列表 | 只作补充线索；其中“Wafer-level composite mold…”在本轮未完整解析，不伪造DOI |

两个已取得列表按DOI去重，共**12篇有DOI的期刊记录＋1篇无DOI会议稿＝13条已解析记录**，交集为7个DOI。ScienceDirect的目标论文页还明确列出1篇无DOI中文论文`Wafer-level composite mold for large-area nanoimprint lithography`；本轮只核到题名、作者、卷页及其出现在Cited by预览中，未取得该文原页/摘要，故作为**第14条题名级线索**单列，不冒充已完整解析。逐条记录与该线索均在[evidence.json](evidence.json)。此外另读同研究系列2019年NNT两页摘要，作为版本补充，不无声计成额外独立期刊研究。不同索引有收录、版本和更新时间差异，不能拼成所谓Scholar官方被引总数。

访问日期以北京时间2026-10-17记；原始接口URL、返回码、完整JSON、可得PDF/HTML及哈希保存在raw与evidence.json。曾报错的期刊2018元数据已有限重试成功；失败不按空结果处理。

## 2 与问题最相关的七篇期刊候选

以下“仅引用/应用”是证据层级内的筛查判断；未取得全文的不能据此彻底排除。无一项已确认满足目标标定a/b。Cochrane2018确有另一类渗透率模型定量验证，单列，避免把“relative permeability”和“anisotropic geometric permeability”混同。**【2026-10-17 更新】Cochrane 2018 全文已下并核实**（`raw/cochrane2018_IJMF_104_9.pdf`，吸收报告 `COCHRANE2018_ABSORPTION.md`）：该文**不做沟槽**，原文明确将“flow into template features”列为未来工作；全文 groove 0 次、rectangular 0 次。其相对渗透率为**随饱和度变化的 k_rα(S)**，靠转变中心与半跨度两参数经能量法/实验标定 ⇒ 双相 K 非纯几何量。原“两相相对渗透率定量模型验证”措辞易被误读为“验证了两相沟槽 K”，引用时须按上述表述。

### 1. Optimal placement of droplets for UV nanoimprint lithography

- **作者：** Yang H. Ban; Roger T. Bonnecaze。
- **年份/期刊：** 2020；Journal of Vacuum Science & Technology B, Nanotechnology and Microelectronics: Materials, Processing, Measurement, and Phenomena，卷38，页码/文号022601。
- **DOI：** [10.1116/6.0000030](https://doi.org/10.1116/6.0000030)，Crossref身份及目标引文关系均已核实。
- **一句话：** 基于细槽结构改进气液界面上的各向异性毛细压力，再做多滴铺展与布滴优化。
- **分类：** **仅引用/应用（模型层毛细边界修正）**；不是已确认的K误差标定。
- **原文/来源依据：** 出版商提交Crossref的摘要明确说明改进对象为capillary pressure boundary conditions；UT作者组论文列表也核实题名与作者。AIP PDF访问403，未取得全文。
- **访问与结论限制（更新）：** 期刊出版PDF未取得；博士论文第2章方法、结果与附录已核。式(2.9)(2.10)沿用等效K，式(2.19)/Fig.2.7验证毛细压力，相关章节未见目标K误差标定。不能因此排除其他期刊版本差异或领域先例。

### 2. Minimizing filling time for ultraviolet nanoimprint lithography with templates with multiple structures

- **作者：** Yang H. Ban; Roger T. Bonnecaze。
- **年份/期刊：** 2021（在线2020-12-16）；Journal of Vacuum Science & Technology B, Nanotechnology and Microelectronics: Materials, Processing, Measurement, and Phenomena，卷39，页码/文号012601。
- **DOI：** [10.1116/6.0000648](https://doi.org/10.1116/6.0000648)，Crossref身份及目标引文关系均已核实。
- **一句话：** 考察不同图案区域交界处的液体迁移与布滴，减少填充时间。
- **分类：** 仅引用/应用；目标K误差标定未确认。
- **原文/来源依据：** 出版商提交Crossref的摘要、卷39/文号012601及引文表。AIP PDF403，未取得全文。
- **访问与结论限制（更新）：** 期刊出版PDF未取得；博士论文第3章相关方法与结果已核，采用式(3.9)(3.10)给定K作多区域填充应用，未见目标的独立K误差标定。期刊卷期年为2021、在线2020，不能当成两篇。

### 3. Multiphase model for nanoimprint lithography

- **作者：** Andrew Cochrane; Kristianto Tjiptowidjojo; Roger T. Bonnecaze; P. Randall Schunk。
- **年份/期刊：** 2018；International Journal of Multiphase Flow，卷104，页码/文号9-19。
- **DOI：** [10.1016/j.ijmultiphaseflow.2018.03.014](https://doi.org/10.1016/j.ijmultiphaseflow.2018.03.014)，Crossref身份及目标引文关系均已核实。
- **一句话：** 以相对渗透率扩展两流体润滑模型，并与其他计算表述和实验流动影像比较，处理困气与溶解。
- **分类：** **仅引用/应用（近邻的两相相对渗透率定量模型验证）**；不是已确认的目标标定。
- **原文/来源依据：** 出版社摘要及§3.1预览指出以能量方法确定相对渗透率参数，并做模型比较。Crossref参考文献含目标；OSTI登记1692156，但本轮全文请求超时。
- **访问与结论限制：** 仅见摘要与章节片段。确有渗透率模型的推导/验证，不能概括为完全没有校核；但这是两相相对渗透率，不是已确认的全充液矩形槽K∥/K⟂相对Jain误差地图。

### 4. Resist Filling Study for UV Nanoimprint Lithography Using Stamps with Various Micro/Nano Ratios

- **作者：** Minqi Yin; Hongwen Sun; Haibin Wang。
- **年份/期刊：** 2018；Micromachines，卷9，页码/文号335。
- **DOI：** [10.3390/mi9070335](https://doi.org/10.3390/mi9070335)，Crossref身份及目标引文关系均已核实。
- **一句话：** 用Simprint进行单特征和芯片尺度混合微/纳米图案填充研究，比较填充程度、压力与残胶层。
- **分类：** 仅引用/应用（全文核对未见目标标定）。
- **原文/来源依据：** PDF第2页§2说明Simprint接触力学扩展框架，并引用Jain等作为流体模拟背景；第6–10页为填充/压力/RLT结果，第12页参考文献25为目标。PDF第2、10页已目视核对。
- **访问与结论限制：** 全文已读。不能把feature-scale一词或多尺度填充对比自动等同于显式Stokes沟槽K标定。

### 5. Cavity filling with shear-thinning liquids

- **作者：** Jyun-Ting Wu; Lorraine F. Francis; Marcio S. Carvalho; Satish Kumar。
- **年份/期刊：** 2020；Physical Review Fluids，卷5，页码/文号054003。
- **DOI：** [10.1103/physrevfluids.5.054003](https://doi.org/10.1103/physrevfluids.5.054003)，Crossref身份及目标引文关系均已核实。
- **一句话：** Galerkin有限元研究剪切变稀液体向梯形腔填充及接触线运动，比较压力梯度与板运动驱动。
- **分类：** 仅引用/相关研究；目标标定未确认。
- **原文/来源依据：** APS官方摘要明确Carreau型流体、梯形腔、移动接触线及有限元方法；Crossref参考文献含目标。APS全文接口本轮401。
- **访问与结论限制：** 仅见摘要。虽用FEM解析局部填充，却未在可读摘要中识别出Jain全充液方向K闭合误差标定。

### 6. Modeling the squeeze flow of droplet over a step

- **作者：** Aryan Mehboudi; Shrawan Singhal; S. V. Sreenivasan。
- **年份/期刊：** 2022；Physics of Fluids，卷34，页码/文号082005。
- **DOI：** [10.1063/5.0098597](https://doi.org/10.1063/5.0098597)，Crossref身份及目标引文关系均已核实。
- **一句话：** 用润滑理论与VOF研究液滴挤压越过台阶，讨论液体向深区重分配及无量纲曲线。
- **分类：** 仅引用/应用；目标标定未确认。
- **原文/来源依据：** 出版商提交Crossref的摘要；参考文献含目标，卷34文号082005。AIP全文PDF403。
- **访问与结论限制：** 仅见摘要。其计算本身使用润滑模型，不能仅凭CFD/VOF标签当作对润滑闭合的独立显式校核。

### 7. Front evolution and localized redistribution during confined polymer micro-embossing under different nominal capillary-number conditions

- **作者：** Wei-Shen Kuo; Shi-Chang Tseng; Meng-Hsun Tsai。
- **年份/期刊：** 2026-10-16上线；Microsystem Technologies，卷32，页码/文号195。
- **DOI：** [10.1007/s00542-026-06175-1](https://doi.org/10.1007/s00542-026-06175-1)，Crossref身份及目标引文关系均已核实。
- **一句话：** 用侧视实验与二维ANSYS Polyflow比较UV胶及高黏比较材料的受限沟槽瞬态前沿和局部重分配。
- **分类：** 仅引用/相关研究（摘要级判断）；全文待核。
- **原文/来源依据：** Springer预览页完整摘要、Highlights、作者及参考文献已读；Crossref核实三作者、Microsystem Technologies卷32文号195及上线日期。页面为subscription preview，PDF入口重定向至预览而非PDF。
- **访问与结论限制：** 仅见摘要与预览。摘要明确研究前沿形态趋势且定量验证有限，未见K张量对Jain误差标定描述；不能因此断言全文绝无相关比较。

## 3 同团队会议材料：最接近“对原模型不满意并改进”的来源

**2018：Yang Ban; Akhilesh Jain; Roger T. Bonnecaze，*Optimizing Filling of Anisotropic Templates in UV Nanoimprint Lithography***，19th International Coating Science and Technology Symposium，ISCST-20180919AM-B-PD4。[会议官方六页原稿](https://www.iscst.com/wp-content/uploads/2019/01/ban.etal2018.OptimizingFillingAnisotropic.Paper_.ISCST-20180919AM-B-PD4.p.pdf)。**未找到DOI；首页标Unpublished，不是期刊正式论文。**

全文依据：第3页式(2)沿用有效渗透率框架；第4页图2将实验/模拟作定性对比，并把差异归因于毛细边界；第4–5页使用Surface Evolver计算界面曲率与毛细压力；第5页结论将该边界改进列为后续工作。第3–5页已目视核对。没有在已读全文中发现单相矩形槽K主值相对Jain的定量误差地图。

**分类：仅引用/应用（已有模型偏差讨论与毛细边界修正），非目标水力K定量标定。** 白话：他们确实发现“铺展形状不够像实验”，但主要修改的是液面拉力的计算，不能当成已经测准沟槽阻力。

**2019：Yang H. Ban; Roger T. Bonnecaze，同题NNT2019会议摘要**，[会议官方两页PDF](https://www.nnt2019.org/documents/uploads/Yang_Ban~2019_06_01_NNT_abstract_0.pdf)。未找到DOI、没有期刊卷页。第1页明确提出方向相关毛细压力，第2页图1为实验/模拟定性形态对比、图2为毛细计算；第1页已目视核对。与2018/2020同研究系列的联系可从作者、题名和内容看到，但没有将三个版本当作三套独立K验证。该摘要不等于2020期刊全文。

## 4 逐条筛查后排除的五篇有DOI记录

不是删掉“看起来不相关”的引文，而是保留其身份和排除理由。它们均通过Crossref参考文献确认引用目标；未取得全文的只在现有证据层级排除，不声称完成全文审计。

| 作者 | 期刊年份/题名 | DOI | 依据与分类 |
|---|---|---|---|
| Hongchao Kang; Ao Liu; Wentao Cai | BIT Numerical Mathematics，2025（在线2024）；*Efficient numerical methods of integrals with products of two Bessel functions and their error analysis* | [10.1007/s10543-024-01045-6](https://doi.org/10.1007/s10543-024-01045-6) | 仅见出版社摘要/参考文献：数值误差针对Bessel积分求积，不是渗透率闭合；期刊2025，在线2024。 |
| Yonglin Yang; Shenghu Ding; Wenshuai Wang; Xu Wang; Xing Li | Computational and Applied Mathematics，2022；*The numerical algorithms of infinite integrals involving products of Bessel functions of arbitrary order* | [10.1007/s40314-022-01816-3](https://doi.org/10.1007/s40314-022-01816-3) | 仅见出版社摘要/参考文献与引文上下文：任意阶Bessel积分算法，NIL是应用背景。 |
| Yung-Jin Weng; Shi-Han Wang | Microelectronic Engineering，2019；*Research and development of the replication process of dynamic tilting magnetic colloid soft mold deforming imprint* | [10.1016/j.mee.2019.01.008](https://doi.org/10.1016/j.mee.2019.01.008) | 仅见索引摘要：磁性胶体软模变形复制研究，未识别目标K校核。 |
| Ke Du; Junjun Ding; Ishan Wathuthanthri; Chang-Hwan Choi | Nanotechnology，2017；*Selective hierarchical patterning of silicon nanostructures via soft nanostencil lithography* | [10.1088/1361-6528/aa8ce8](https://doi.org/10.1088/1361-6528/aa8ce8) | 仅见出版商提交的摘要：纳米模板/刻蚀制备研究，未识别目标K校核。 |
| Xuemei Wang; Juan J. Faria-Briceno; Tito Busani; S. R. J. Brueck | Journal of Vacuum Science & Technology B, Nanotechnology and Microelectronics: Materials, Processing, Measurement, and Phenomena，2019；*Nanoscale details of liquid drops on 1D patterned surfaces revealed by etching* | [10.1116/1.5116703](https://doi.org/10.1116/1.5116703) | 仅见出版商提交的摘要：液滴润湿、刻蚀和Cassie状态实验，不是数值K与闭合比较。 |

另有一条**只到题名级、未并入上述13条已解析记录**的引文线索：Hongbo Lan; L.-L. Guo; Q. Xu; L. Qian，2018，*Wafer-level composite mold for large-area nanoimprint lithography*，Optics and Precision Engineering 26(4), 894–905。ScienceDirect目标页把它列在Cited by预览中；本轮未找到可确认的DOI，也未取得该文摘要/全文，仅可按题名判断为大面积复合模具制造，暂列“仅引用/应用（与K标定无已核证据）”。可核链接：[目标论文的Cited by预览](https://www.sciencedirect.com/science/article/abs/pii/S0167931717301296)；书目信息辅助链接：[EurekaMag记录](https://2fa.eurekamag.com/research/105/067/)。

## 5 对a/b/c三个条件分别回答

- **a：显式矩形槽K与Jain/条纹平均/局部立方律的定量误差比较——本次可得证据未发现。** 本次已补查Ban学位论文第2、3章，未见目标标定；不能把前沿位置/填充时间对照等价成K误差，也不把学位论文称为期刊出版PDF已取得。
- **b：后续修正或适用域讨论——有，但已确认的重点是毛细边界与两相扩展。** Ban学位论文第2、3章继续使用Jain型K；Fig.2.7检验毛细压力。相关章节核查缺口已补，期刊版本页码差异及Cochrane2018全文缺口仍保留。详见[原页复核报告](../Ban_dissertation_relevance_20261017.md)，不再采用“期刊全文完整核实”“全文从未校准”等过强表述。
- **c：各向异性渗透率与真实流动数值对照——有定性形态/实验近邻，没有确认到目标的K主值定量校核。** 2018/2019会议稿的定性对比及多相模型的另一类验证应在引言中承认。

**查新风险：** 本文只追踪一篇论文的已发现后续引文。没有引用Jain而研究等价物理的论文仍可能构成先例；既有Dewangan & Datta2020（DOI10.1017/jfm.2020.134）作为独立近邻不可忽略，不伪装成本次引文列表命中。**【2026-10-17 更新】该文开放获取全文已下并逐节核实**（`raw/dewangan2020_JFM_891_A12.pdf`，吸收报告 `DEWANGAN2020_ABSORPTION.md`）：全文 `Jain`/`nanoimprint` 均 0 次，不引本次追踪目标；其方法为谱分析+域扰动渐近解析（假设 ε≪1），且在 §4.4 明确声明**矩形直角槽因跳变不连续无法给出有界预测**（引 Kamrin et al. 2010）。⇒ 不构成先例威胁，反而为「矩形槽必须用 DNS」提供方法论必要性依据。**Scholar受限、关键全文不全，因此本轮不足以授权“首次”。

**论文可用措辞：** “本文在统一几何、驱动和通量定义下，对全充液矩形沟槽中局部立方律闭合的方向性输运误差作定量评估。”不预设首次，也不预设所有工况均失效。

## 6 实际使用的检索与接口

- Scholar精确题名与DOI查询：`"Fluid flow in UV nanoimprint lithography with patterned templates"`，`10.1016/j.mee.2017.04.001`；结果页提取到`cites=14393388769843840999`，但Cited by页触发流量验证/CAPTCHA，未取得列表。
- web：上述题名加citations/permeability；`Jain 2017 permeability nanoimprint 2020`；候选精确题名、DOI及author/publisher/repository限定；细项请求中未命中或返回噪声不解释为文献不存在。
- Semantic Scholar：`/graph/v1/paper/DOI:10.1016/j.mee.2017.04.001`；随后`/paper/ba3b8b12b561ca5ab0836f963e9651c41afab8e4/citations?...&limit=100&offset=0`，9条、无next。
- OpenCitations：`/index/v2/citation-count/doi:10.1016/j.mee.2017.04.001`，继而`/citations/doi:...`，11条。
- OpenAlex：`/works/https://doi.org/10.1016/j.mee.2017.04.001`身份成功，`/works?filter=cites:W2605348563&per_page=100&cursor=*`预算429；单实体查主要候选的可得位置，取得OSTI线索但全文超时。
- Crossref：`/works/{URL编码DOI}`逐刊解析并检查reference[].DOI。微机器论文一次SSL错误、一次重试成功；不把前次失败当不存在。

未执行WoS或Asta，本轮不将Asta独立交叉标为完成。没有将网络搜索结果中的相关文章、广告或AI摘要当作原文结论。

## 7 辅助流程与项目边界

本轮使用paper-lookup、citation-management及PDF技能作引文获取、元数据核验和原页检查。流程引用：Kassis, T.; Agarwal, V.; He, Y.; Patel, D.; Brueckner, A. M. (2026), *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*, [arXiv2609.00065](https://doi.org/10.48550/arXiv.2609.00065)，当前arXiv记录已在线核实；它只说明工具流程，不是流体物理证据。

本轮不运行/编译OpenLB，不刷新进程或计算日志，不改冻结门槛、模型范围、源码或原始数值结果；run_id不适用。报告、引文筛查与项目状态同步不等于数值Gate放行。

**总评：“Jain型闭合的矩形槽定量误差标定”是否已有先例——未发现（限本次取得的引文与可访问证据；Scholar列表及关键全文仍不完整）。**
