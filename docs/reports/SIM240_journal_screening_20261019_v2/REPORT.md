# SIM240 当前稿件的二区、三区期刊细筛

核对日期：2026-10-19（北京时间）。性质：作者与导师决策工作稿；不是正式同行评审、录用预测或投稿放行。当前 submission_ready=false。

## 1. 本轮结论

**重点比较 Physics of Fluids（PoF）、Computers & Fluids（C&F）、European Journal of Mechanics – B/Fluids（EJM B）。** PoF 保留为二区优先候选；C&F 与 EJM B 是本轮新增的重点三区候选。Microelectronic Engineering（MEE）保留工程应用备选，但不能继续默认为最稳的三区去向。Tribology Letters 属于需要调整问题落脚点的备选；Theoretical and Computational Fluid Dynamics（TCFD）虽有很接近的沟槽流动论文，当前范围对新物理认识的要求较强，不排在前面。

这是基于当前内容与官网范围的匹配判断，不是录用率排序。六本均未提交；本轮没有联系编辑。

用户补充的费用偏好为“暂不限制，先看适合程度”。项目已记录的时间偏好为争取2027年3—4月前获录用；本轮沿用其规划含义，不保证期限，也不重新认定学校是否接受录用通知。

## 2. 学校口径与分区证据等级

本轮用户截图为汕头大学工学院研究生评奖评优文件的“附件3：科研论文分级标准”。截图明确：SCI 二区对应P3、三区对应P4；SCI按中科院大类分区；论文按发表当年的索引目录与分区确定级别；类型应为Article或Review。截图没有提供完整年份、适用对象或录用通知认定条文，不能据此推断毕业要求。

中国科学院文献情报中心在2026-03-27声明，2026年起不再更新与发布期刊分区表，其他机构发布的表与该中心无关。因此本轮使用**2025年3月升级版中科院大类**作公开初筛参照，不把2026新锐、JCR、CiteScore或SJR分区替代学校口径。学院2027年到底采用什么版本，仍须落实。[官方声明](https://las.cas.cn/news/tzgg/202603/t20260327_8178738.html)

下表所有分区均为**公开转载初筛，尚未取得学校认可的正式归档**。只有“学校认可分区版本+该版本逐刊记录”才能用于最终申报判断。

| 期刊 | ISSN | 2025大类初筛 | 分区来源 |
|---|---|---|---|
| Physics of Fluids | 1070-6631 | 工程技术2区 | [明确区分2025/2026的公开页面](https://www.ifabiao.com/sci/10706631/)；[另一公开页面](https://www.xueshu.com/sci/41757/) |
| Computers & Fluids | 0045-7930 | 工程技术3区 | [2025分区公开转载](https://www.xueshu.com.cn/sci/41001/12.html)；[补充页面](https://www.fabiao.com.cn/sci/00457930/) |
| European Journal of Mechanics – B/Fluids | 0997-7546 | 工程技术3区 | [2025分区公开转载](https://journalcompass.com/journals/european-journal-of-mechanics-b-fluids-09977546.html)；[武汉大学图书馆逐刊入口，页面未明确CAS版次](https://topj.lib.whu.edu.cn/show.asp?cat=sci&id=10453) |
| Tribology Letters | 1023-8883 | 工程技术3区 | [2025分区公开转载](https://www.ablesci.com/journal/detail?id=rRggWp)；[补充页面](https://www.fabiao.com.cn/sci/10238883/) |
| Microelectronic Engineering | 0167-9317 | 工程技术3区 | [2025分区公开转载](https://www.fabiao.com.cn/sci/01679317/) |
| Theoretical and Computational Fluid Dynamics | 0935-4964 | 工程技术3区 | [明确列出2025版的公开转载](https://www.fabiao.com.cn/sci/09354964/) |

商业页面仅提取带年份的大类分区；其营销话术、社区录用率、加急承诺、未经官方核验的速度均未采用。转载页面之间仍可能共享数据源，不能将两页一致当作两份独立官方证据。

## 3. 依据当前稿件，而非宽泛研究方向

已读取当前上下文、路线图、历史摘要、最新交接，现有第一章、第四章、第五章、CORE_CLAIMS和同日PoF候选摘要；也核对既有选刊方案与MEE方案。sim240 MCP本轮工具列表未提供，采用针对性文件读取。

当前首篇是：全充液、固定间隙、牛顿液体、连续介质与无滑移条件下，周期矩形沟槽的沿槽/跨槽输运，以及局部立方律简化模型的误差和经验修正。OpenLB是计算工具；没有新增LBM算法、自由界面、润湿、困气、真实压头运动或实际材料实验验证。

当前记录的主要内容是18种几何、36个主方向工况，原模型对两方向的高估不同，因而影响各向异性和斜向通量。V2为数据知情的事后经验修正，不能写为独立预测验证；最薄间隙仍有显著残差，网格证据只覆盖已检查几何。机制尚不能唯一归因给尖角或某一耗散区域。

这些结论本轮用于选刊定位，**没有重新计算原始数值或独立验收完整日志/退出码**。不升级NUMERICAL_GATE、RESULT_PASS或geometry_PASS。

## 4. 逐刊适配与需要准备的内容

### A. Physics of Fluids：二区优先候选，有条件首投

官网明确接受推进流体物理认识的理论、计算、实验贡献，包含微纳流体力学，不要求所有稿件都做实验。[官方范围](https://pubs.aip.org/aip/pof/pages/about)

对本稿的有利点：问题能表述为“局部简化流动模型在有限间隙与深槽条件下的方向性失真”，两方向误差差别及斜向通量偏差具有流体意义。主要风险是编辑或审稿人认为结果仅为特定参数表及事后拟合，对已有认识的增量不足；现有机制与全域不确定度限制也会被追问。

建议主线：**方向性闭合误差 → 各向异性与流向后果 → 修正及剩余间隙依赖**。先说明为什么结果能帮助理解受限沟槽流动，再讲纳米压印用途。不能把机制空间分解或新增独立点说成官网唯一规定；是否需要这些证据取决于最终核心主张。

相关实例：Dewangan与Persoons，*Effects of topographical wall patterns on flow through porous media*，PoF 37, 013613 (2025)，DOI [10.1063/5.0243010](https://doi.org/10.1063/5.0243010)。[作者所在大学记录](https://pure.ul.ie/en/publications/effects-of-topographical-wall-patterns-on-flow-through-porous-med/)与本轮Crossref元数据相符。该文有多孔介质，不能当作本稿同几何直接验证，也不能据一个实例推断录用可能性。

### B. Computers & Fluids：三区重点候选，当前内容衔接较直接

官网除数值方法外，也接收流动物理的计算分析、新应用、不确定度以及降阶/替代模型研究。因此**未开发新算法不构成自动排除理由**。[官方范围](https://shop.elsevier.com/journals/computers-and-fluids/0045-7930)

对本稿的有利点：显式沟槽数值参考、简化模型对比、方向性误差、网格敏感性及修正范围组成较完整的计算研究链。主要风险是“用成熟软件做一组扫描”本身贡献不足，参考解离散误差与模型误差必须分清，模型比较也应说明为何不是已有工作的重复。

建议主线：**怎样可靠评估简化输运模型 → 原式在两个方向的失准 → 修正能改善什么、不能保证什么**。整理参考解定义、已有网格证据与数据来源；V2保持事后评价定位。需要新预测主张时再冻结独立测试，不因选刊自动补跑。

相关实例：Yang与Wang，*Suitability of body force model for pressure-difference driven flow in porous media*，C&F 265, 105990 (2023)，DOI [10.1016/j.compfluid.2023.105990](https://doi.org/10.1016/j.compfluid.2023.105990)。[出版社摘要](https://www.sciencedirect.com/science/article/pii/S0045793023002153)报告以孔尺度模拟分析模型适用性、误差与结构影响。它支持“模型适用性评估属于该刊可能接纳的研究类型”，并不证明本稿已经达到相同贡献水平；其孔隙结构与本稿周期沟槽不同。

### C. European Journal of Mechanics – B/Fluids：三区重点候选，流动物理读者匹配

官网欢迎理论、计算与实验，要求方法服务于可识别的流体问题并说明结果意义。[官方范围](https://shop.elsevier.com/journals/european-journal-of-mechanics-b-fluids/0997-7546)

对本稿的有利点：受限沟槽、流阻、各向异性及简化理论失准均与读者群直接相关。主要风险是物理认识不足、量纲参数和适用范围没有组织清楚，或相对已有光滑沟槽理论的增量说不清。三区不等于只需格式完整或可容忍数值证据不足。

建议主线：**几何相对尺度如何改变两个方向的阻力，以及为何局部平板近似给出不同偏差**。采用h/w、d/w等已能由现有数据表达的量纲分析，但不把变量重画当成新标度定律。

直接相关实例：Dewangan与Datta，*Flow through microchannels with topographically patterned wall: A spectral theory for arbitrary groove depths*，EJM B 70, 73–84 (2018)，DOI [10.1016/j.euromechflu.2018.02.004](https://doi.org/10.1016/j.euromechflu.2018.02.004)。[出版社检索记录](https://www.sciencedirect.com/science/article/pii/S0997754617305010)和[作者高校出版物表](https://web.iitd.ac.in/~subhra.datta/publications1.html)相符。它研究正弦形壁面沿向流动；本稿矩形台阶的比较应明确差别。2018实例属于研究传统证据，不代表2026编辑偏好或已完成近期同题查新。

### D. Tribology Letters：有条件的三区备选

官网以摩擦、润滑、磨损、黏附等基本问题为中心。[官方范围](https://link.springer.com/journal/11249/aims-and-scope)

相关实例：*Height-Averaged Navier–Stokes Solver for Hydrodynamic Lubrication* (2022)，DOI [10.1007/s11249-022-01576-5](https://link.springer.com/article/10.1007/s11249-022-01576-5)。本轮读取公开摘要与引言，文章研究薄膜模型及与Reynolds类结果的比较；没有把它当成本稿已有独立验证。

本稿若以织构薄膜的方向流量因子、局部Reynolds近似失准及下游压力估算为主线，可建立联系。但当前没有实际滑动摩擦、磨损或接触实验；不能为了改投虚构这些结果。第5章图9/10的数据链仍待既有任务核准，未核准前不能把挤压传播当作已验证完整工艺。需要的调整大于C&F/EJM B，故排其后。

### E. Microelectronic Engineering：纳米压印应用备选，初筛风险需正视

当前官方介绍偏重微纳器件/材料的制造、表征和性能，同时列有光刻与纳米压印。官网对部分模拟研究使用较审慎的表述；这不等于全面禁止流动模拟，但不能继续用早期泛化简介认定稳妥。[现行官方范围](https://shop.elsevier.com/journals/microelectronic-engineering/0167-9317)

直接先例：Jain等，*Fluid flow in UV nanoimprint lithography with patterned templates* (2017)，DOI [10.1016/j.mee.2017.04.001](https://doi.org/10.1016/j.mee.2017.04.001)。本轮Crossref核对题名、期刊和DOI；未重新审其全文。该先例说明应用关联，不能证明九年后当前编辑一定欢迎同类纯数值稿。

若选此刊，应强调**在什么已检查条件下，模板简化输运系数会误导工程估算**，并严格区分固定间隙模型与真实填充过程。任何10%等“工程可接受阈值”需要工程理由或预先定义，不能看完样点后自行添加为通用工艺判据。

### F. Theoretical and Computational Fluid Dynamics：方向相关，暂不优先

官网明确强调新的物理认识，并将单纯调参、代码验证、流动解目录及缺少新物理的工程预测排除在范围之外。对数值离散伪影也有明确控制要求。[官方范围](https://link.springer.com/journal/162/aims-and-scope)

非常相关的实例：Dewangan，*Investigation of Stokes flow in a grooved channel using the spectral method*，38, 39–59 (2024)，2023-11-01先在线发表，DOI [10.1007/s00162-023-00679-6](https://link.springer.com/article/10.1007/s00162-023-00679-6)。本轮读取出版社摘要，涉及横向受限沟槽、模型误差和FEM比较；没有取得全文作公式级审查。主题接近同时意味着需要更明确说明已有工作与本稿的差异，不是可以“照着投”的保证。

当前主要结果仍是误差图和数据知情修正，机制定量分离与独立预测尚有限，因此该刊不作为当前快速投稿主序列。

## 5. 速度、费用与时间安排

| 项目 | 本轮可核实事实 | 可以据此做什么 |
|---|---|---|
| PoF | 官网2025统计：首次决定平均20天、录用平均54天、发表平均83天；Hybrid，可选开放获取 | 说明历史处理速度有参考价值；不能推算本稿必然54天录用 |
| Tribology Letters | 官网当前首次决定中位数4天；Hybrid | 不能解释为4天外审结束或录用；本轮未核得完整录用时长 |
| C&F、EJM B、MEE | ScienceDirect期刊/Insights相关页面403，未核得可靠官方普通稿录用天数 | 标“未核实”，不按社区经验或转载159天等数字排序 |
| EJM B Fast Tracks | 官网介绍两个月从投稿到发表的目标，要求重要原创短稿 | 不套用于当前完整研究稿，也不作为录用保证 |
| 具体费用 | 用户费用暂不限制；本轮未完成逐刊当前APC、税费、协议减免核价 | 不给可能过时的精确金额，不以付费与否推断录用难度 |

来源：[PoF官网](https://pubs.aip.org/aip/pof/pages/about)、[Tribology Letters官网](https://link.springer.com/journal/11249)、[EJM B官网](https://shop.elsevier.com/journals/european-journal-of-mechanics-b-fluids/0997-7546)。首次决定可能包含编辑初筛，不能等同于外审完成。

若仍争取2027年3—4月录用，**本次调研支持尽快完成可信整稿、缩短内部反复改稿时间，不支持为了赶时间连续盲投多刊**。具体首投需看整稿就绪时贡献表达、网格范围和关键图件的状态；目前没有证据证明哪本三区一定比PoF更快或更稳。

## 6. 推荐投稿决策

1. **二区优先**：有条件选择PoF；先确认方向性误差及后果能形成相对先例的清楚增量，不以“首次用OpenLB”或样点数作为创新。
2. **直接以三区为目标**：优先在C&F与EJM B中选。若最终突出模型误差评估、计算核查与修正范围，倾向C&F；若突出几何—阻力—各向异性及物理解读，倾向EJM B。没有可靠依据对两者报录用率。
3. **需要重新落脚应用**：Tribology Letters与MEE分别对应薄膜润滑与压印工程。选其一需要有证据支撑对应读者关心的意义，不只是改标题或删机制。
4. TCFD当前不优先。Journal of Hydrodynamics公开2025大类初筛为3区、官方范围可涵盖相关流动，但本轮没有完成近期接近稿对照，未挤入上述主序列。

这里的顺序是候选比较，不是自动连投计划。只允许单刊在审；投稿、撤稿或联系编辑均未获本轮执行指令。

## 7. 对项目已有选刊文字的定点纠偏

同日旧方案分别偏向PoF与MEE。本报告扩展候选池，保留旧文件而不覆盖其文字。

- “揭错+经验修正不是PoF类型”过于绝对：应以是否推进流体物理判断。
- “投PoF必须先补空间机制分解和独立点”不是已核得的官网固定门槛：本稿的验证需求依赖其最终主张，可选择收紧主张或补足必要证据。
- “三区可以接受某程度解释”及“保证不因格式被秒拒”均不能承诺：分区不替代具体编辑标准与科学质量。
- 五章没有摘要不能推出整个项目没有摘要：同日PoF候选文件已有摘要；当前问题是完整稿尚未整合并经作者确认。
- “找到一篇先例”说明主题/研究类型关联，不证明稿件新颖、当前编辑偏好或必然送审。

## 8. 当前稿件在任何候选刊都需要解决的内容

本轮不重复全面数值审查；从当前文件状态可识别的重点为：

1. 用一张差异表对照Jain2017、Dewangan2018/2020/2024及已有矩形槽研究，明确本稿新增的是哪个方向、哪种定义、什么后果，不声称宽泛首次。
2. 清楚区分离散参考解误差与模型误差，保留最薄间隙双网格、其他几何有限加密及缺失的全域不确定度。
3. V2保留事后数据知情定位；若承诺未见几何预测，必须有相应独立证据。无需为选刊自动启动仿真。
4. 整合五章、候选摘要与结论，核关键图件和引用、图9/10实际输入链及历史构建来源限制；本轮没有将这些销项。

以上是本稿的证据需求，不是为冲分区机械增加多相、实验、机器学习或新算法。

## 9. 检索覆盖、可复现记录及缺口

本轮是目标明确的选刊细筛，不是系统综述或完整查新。网页检索用公开领域词与已发表论文题名，没有将未发表正文或专有数值上传到搜索服务。检索主题覆盖：逐刊2025分区、现行官网范围、代表论文与有限近期实例、官方速度入口。具体题名/查询与网页响应保存在`evidence/journal_*search.json`等文件，官网快照在`official_scopes_snapshot.json`，分区入口在`partition_sources*.json`。

Crossref按6个明确DOI逐条请求`https://api.crossref.org/works/{URL编码DOI}`：5条返回有效work记录并核对DOI/题名/期刊；EJM2018首次curl退出35（TLS连接问题），原始空响应与失败保留，由出版社索引记录和作者高校出版物表交叉确认题名/DOI，不伪称Crossref成功。原始响应与`crossref_ledger.json`保存，不将5条元数据核验称为5篇全文审读。

覆盖缺口：未查WoS/Scopus完整近年目录；未逐刊系统筛选2023—2026所有相近稿；EJM2018、MEE2017和TL2022是较早先例；多数分区为转载；普通稿速度及具体APC有缺口。部分web请求429，部分ScienceDirect页面403，已使用出版社Shop官网或作者高校记录补充，未绕过访问控制。

流程参考：本轮使用paper-lookup的来源与DOI核验方法，以及peer-review的主张—证据与比例原则；本轮不属于编辑委托审稿，未运行正式同行评审intake或声明完成正式评审。工具方法参考已核元数据：Kassis, T.; Agarwal, V.; He, Y.; Patel, D.; Brueckner, A. M. (2026), *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*, [arXiv:2609.00065](https://arxiv.org/abs/2609.00065)。此条仅为流程引用，不进入流体物理贡献论证。

## 10. 交接与执行边界

新增本报告、检索响应、Crossref记录和输入哈希；同步`docs/reports/SIM240_AI_CONTEXT.md`与最新日期文件`docs/reports/AI_HANDOFF_20261015.md`的选刊停点。没有改五章正文、图件、V2、求解器、原始结果、协议或历史FAIL；没有编译、优化器复跑、新OpenLB运行、Gate放行、长算命令或投稿。run_id不适用，未新增长算授权。

下一具体动作：作者/导师先以本轮三本重点候选比较核心叙事；在完整稿就绪前完成已有图件/来源/主张的必要核查。学院确认适用分区版本。需要新数值证据时另行冻结与授权，不自动进入下一Gate。
