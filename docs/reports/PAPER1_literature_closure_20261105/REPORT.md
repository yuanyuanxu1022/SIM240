# OpenLB与纳米输运/压印论文的闭环方式：定向检索笔记

日期：2026-11-05（北京时间）。性质：AI辅助定向文献核对与路线建议；非系统综述、非最终公式冻结、非计算协议。用户转述老师“不在意误差，查OpenLB文章和徐兴硼等纳米文章，看如何实现闭环”。姓名已由用户更正为“徐新鹏”；已定位相关作者及论文链，见XU_XINPENG_CLOSURE.md。以下五篇为先前定向检索，不冒称徐的论文。

## 判断与范围

老师可能希望把重点从误差门槛讨论转到科学问题—方法—证据—结果用途，这只是解释而非老师原意的确认。已知研究范围仍是固定间隙、全充液、单相矩形沟槽方向性输运。此次只授权文献检索与分析，不启动计算，不改变原门槛或历史FAIL。

“闭环”在本笔记中是对论文证据结构的分析用语，不表示这些作者使用该词，更不表示控制系统的反馈控制。

## 已核对的五篇论文

### E01：Bukreev等（2025），OpenLB纳米孔隙耦合模型

A hybrid Lattice-Boltzmann model for hydro-electrochemical modeling and sensitivity analysis of crystallization potential in nanoporous media. Part I: simulation model. Engineering with Computers 41,4587–4603. DOI:10.1007/s00366-025-02216-x。
来源：https://link.springer.com/article/10.1007/s00366-025-02216-x 。本轮打开完整HTML，重点§4.1–4.3与§5.3。
论文在OpenLB中实现流动、电势、离子输运耦合；先分别与解析解比较，再检查完整电渗耦合，报告约一阶收敛；自动微分灵敏度再与中心有限差分核对。结构为分模块验证→耦合验证→独立算法交叉。不能将其称为实际结晶全过程的实验验证，本文只处理早期过程，不包含孔体积随结晶变化。
借鉴：先让各部分证明各自功能，再核接口，最后展示能回答的科学问题；软件通用验证不能替代SIM240特定几何和物理验证。

### E02：Czelusniak等（2025），OpenLB伪势方法一致性

On the consistency of pseudo-potential lattice Boltzmann methods. Physics of Fluids 37(7). DOI:10.1063/5.0268276。
来源：https://publikationen.bibliothek.kit.edu/1000183417 。本轮核KIT机构记录与摘要；未完成全文逐式检查。期刊日期2025-07-01，机构入库日期2026-07-02，不能混同。
导出方法所逼近的方程，建立参数与物性/SI单位联系，实施平界面、静滴、伽利略不变性、平板两相流基准，报告对所识别方程的二阶收敛。结构为方程→物性→实现→基准。
借鉴其方法验证思路，不引入Paper 1之外的两相任务，不把数值一致性写成真实材料物理验证。

### E03：Dewangan与Datta（2020），最贴近当前方向输运论文

Effective permeability tensor of confined flows with wall grooves of arbitrary shape. Journal of Fluid Mechanics 891,A12. DOI:10.1017/jfm.2020.134。
出版商PDF：https://www.cambridge.org/core/services/aop-cambridge-core/content/view/089D6608B5CF065BAC9B1C4F7D42FBCF/S0022112020001342a.pdf/effective-permeability-tensor-of-confined-flows-with-wall-grooves-of-arbitrary-shape.pdf 。本地已存PDF：docs/reports/Jain_citation_audit_20261017/raw/dewangan2020_JFM_891_A12.pdf。本轮pdftotext读取§4、§4.1、§4.2（文内A12-16及A12-19附近）与图3讨论。
推导有效渗透率张量，用COMSOL显式解析几何的Stokes有限元结果独立比较；§4.2写明网格独立性和横槽三个截面质量守恒核查到四位数字；比较沿槽/横槽与几何变化，展示渐近模型偏差范围。图3–5部分横轴由相对数值预测5%偏差或几何接触先到者限定。5%是该文处理，不是SIM240获批容限。
非常关键：§4.1明确方波槽导致其谱和S1发散，相关式不能用于该方波；不能因题名“arbitrary shape”就套给本项目直角矩形槽。可借鉴证据组织，不能未经推导直接移植公式。
证据结构：理论假设→独立显式槽计算→方向与参数比较→适用范围/失败条件。局部输运研究可形成有限范围的科学闭环，不必自动做完整压印过程。

### E04：Jain等（2017），从方向K接到压印用途

Fluid flow in UV nanoimprint lithography with patterned templates. Microelectronic Engineering 173,62–70. DOI:10.1016/j.mee.2017.04.001。
来源：https://www.sciencedirect.com/science/article/pii/S0167931717301296 。本轮取得出版商摘要/引言/方法与结果预览，随后直接打开403；不声称本轮完成全文图表复核。
用等效各向异性渗透率表示密集线槽图案，模拟液滴铺展/合并与未填充通道，比较布滴方案对填充时间的影响。证据结构：结构→方向输运→过程结果→布滴设计判断。摘要支持改进六角布滴和局部体积匹配建议，不据此声称实验确认或独立标定了沟槽K。
与另篇Jain/Spann/Bonnecaze，JVST B35,011602(2017)、DOI10.1116/1.4971771不同；后者本地原文011602-4称对照Reddy/Bonnecaze既有结果，不能当新实验。

### E05：Ryu等（2017），压印模型对实验

A modified squeeze equation for predicting the filling ratio of nanoimprint lithography. Nano Convergence 4,14. DOI:10.1186/s40580-017-0108-z。
来源：https://pmc.ncbi.nlm.nih.gov/articles/PMC5487822/ 。本轮读取全文方法、实验与结论，重点图4–5。
针对传统挤压方程在工具宽度/膜厚比接近1时速度过估问题修改模型；在不同几何与升压速率下对照实验填充行为/填充率，再讨论厚度与温度趋势。作者报告最大差异10%；这是其特定对照结果，不能直接当SIM240容限。
证据结构：具体旧模型缺陷→修改→可测输出→同条件实验→参数建议。热压印PMMA、非牛顿与本项目物性不同，只借鉴闭环方式。

## 对SIM240的建议（未冻结、未执行）

第一篇最小目标建议：固定间隙下矩形槽的方向阻力规律，以及原公式/V2可用与偏离的原因和条件。用“几何/方向→K与阻力→原公式/V2比较→受控流场或积分耗散证据→适用条件”组织。18几何36方向点保留为回顾性5nm离散样本，不升级为连续域保证或独立预测验证。

机制证据须区分观察与因果：局部速度或耗散峰图仅为线索；需统一驱动/几何对照、积分口径及必要能量收支，才能将局部特征与总阻力联系。可考虑以总输入功率与全域黏性耗散核对为计划，但本轮不推导/冻结新公式，不声称已完成。

应用模型如果取同一套V2系数，二维与OpenFOAM互相吻合证明接入一致，不能独立证明V2准确；与显式解析沟槽参考的比较才针对模型近似。真实填充时间/缺陷预测需要额外界面、边界与过程证据，不属于现有单相结果。

下一动作建议：先根据这五篇画一张“已有图/已有证据/缺少什么”表，再决定论文最终主张；徐新鹏补充文献现见XU_XINPENG_CLOSURE.md。无需把误差阈值选择作为当前文献工作的前置。0.625是否继续取决于后续明确主张与原协议处置，不因这次口头反馈自动判定需要或取消。

## 当前状态和权限

本轮无新增计算或科学验证、无新run_id，无编译、原生审计、求解、重拟合、改阈值、提交或推送。S4 T中细变化1.328387035%>1%、S4_STAGE_ACCEPTED=false、reference_qualified=false、正式MODEL_COMPARISON/physical_validation未评价和submission_ready=false沿用当前记录，并非本轮重新验收。原历史FAIL保留。现有OpenFOAM受控方案仍只是准备阶段。

## 检索与核对可复现性

定向网络检索，访问日2026-11-05，非穷尽检索。查询含“徐兴硼 纳米”“徐兴 纳米压印”“OpenLB permeability validation porous paper”“OpenLB nanoimprint Jain 2017”“Dewangan Datta 2020 10.1017/jfm.2020.134”；另用徐兴蓬/徐兴鹏变体未定位目标作者，不能据此断定作者不存在。本条是澄清前检索记录；用户随后更正为徐新鹏，机构身份和相关论文已在补充笔记定位。

核对层级：E01/E05完整HTML相关节；E03本地出版PDF相关节；E02机构摘要；E04出版商预览。Wiley OpenLB泥岩文页面后续403，未纳入核心结论；若干DOI跳转不可用，已使用上述可访问来源。未声称完成全数据库查新或人工审定。

技能/AI方法：paper-lookup用于定位与记录检索边界，scientific-writing用于证据限定和本笔记。AI生成分析仍需作者核读原文；不替代人的科学裁定。软件方法参考：Kassis,T.;Agarwal,V.;He,Y.;Patel,D.;Brueckner,A.M.(2026), Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents, arXiv:2609.00065，https://doi.org/10.48550/arXiv.2609.00065 （本轮已核arXiv记录；作为辅助方法文献，不是CFD证据）。
