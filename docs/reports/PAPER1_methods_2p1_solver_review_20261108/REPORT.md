# §2.1求解器、体力项及壁面处理审读

日期：2026-11-08（Asia/Shanghai）。范围为作者授权的逐段文字/引用审读；本轮未合入正式稿，不编译或运行求解器，不重判数值Gate或历史构建。

## 裁定

D3Q19、单松弛时间BGK、τ=1、Guo体力项、受力速度半时间步修正以及静止Bouzidi边界的基本描述可保留。需要收紧的是“任意分数距离/曲线与离格壁面保持精度”的泛化措辞，以及以[7]软件论文承载当前自动回归测试细节的引用范围。方法有文献依据、所查当前源码对应、历史运行方法字段及本项目数值精度四层分别记录。

## 逐项依据

|项目|本轮读取依据|允许表述|不能据此声称|
|---|---|---|---|
|OpenLB/D3Q19/BGK|D2 descriptor、set ForcedBGK；当前库ForcedBGK tuple含collision::BGK和forcing::PlainGuo；46保存结果字段|使用所列速度集、碰撞与力项，τ1|软件论文认证全部历史版本或本研究连续精度|
|Guo体力|当前PlainGuo组合、lbm通用addExternalForce的ρ(1−ω/2)、D2 FORCE赋值；本地原文式17/19/20及既有接收报告|加速度a、体力密度ρa；格子FORCE=aΔt²/Δx；computeU含加速度半步修正|把FORCE字段直接等同SI力密度；再手工重复加半步力；由方法选择认证任意几何精度|
|壁面|当前几何求交、材料2/3零壁速BouzidiPostProcessor；当前两分支及本地原文式5a/5b、q半链说明|所用是线性插值分支，q半链时退化为半程反弹|二次插值、全参数二阶、零边界误差或本组对半程反弹有额外精度优势|
|旧46边界集合|TableS1选main36/refinement8/viscosity2，逐个读取result的q_min/q_max、descriptor/collision/τ|保存字段均D3Q19_FORCE、ForcedBGK、τ1及q=.5|新几何h100也已由这一旧集合审过；重新得到geometry_PASS或全部链运行时验收|
|官方基准/回归|本机tests/benchmarks/testPoiseuille3DBGK.cpp的基准与EXPECT_NEAR|有解析基准和回归检查的代码事实|测试已在本轮执行、所有本研究算例通过或软件论文独自支持当前测试实现细节|

## 体力的物理含义

加速度a单位m/s²，体力密度ρa单位N/m³。D2将加速度转换为aΔt²/Δx写入FORCE，库力项再乘格子密度；不能因字段名为FORCE就把它等同论文的力密度F。当前ForcedMomentum::computeU在基础速度上加FORCE/2，D2直接调用computeU，没有再手工重复此项。候选保留半步修正但不把库内部组合展开塞进正文。基准几何驱动线性检查不能扩大为主地图逐点多力验证。

## 壁面与q

q为流体点到墙交点的距离除以该流体—固体链的完整长度。原文方法考虑分数壁面位置，但本组保存的旧46记录均为q_min=q_max=.5，不能把“采用插值格式”本身当成离格优势或精度结果。原文两分支在q=.5代数一致，有限合法输入下退化为半程反弹；其原文端点分支归属与源码不同不影响该端点。插值多项式次数与本研究实际空间收敛阶是不同概念。

本轮不重新证明所有传播/后端路径与原文完全等价，相关指定映射沿用Bouzidi_P8_received与Primary_text_received报告，最新接收报告已经补齐原文指定范围，不能用此前source_audit的历史OPEN状态覆盖。当前源码存在及方法对应不是历史程序完整构建绑定，也不是运行时无回退的证明。现稿后文对q=.5、平板综合误差及任意壁距推广的限制应保留。

## 引用支持范围

- [7] Krause等OpenLB软件论文：软件与方法框架出处，不能单靠它证明本研究使用哪个历史commit或当前测试文件具体行为。官方articles页面本轮可定位同一DOI；其旧目录2020条目不替代最终2021卷页信息。
- [8] Bouzidi–Firdaouss–Lallemand：壁面反弹与插值方法出处。以本地发表版指定段和已核接收报告支持，不借其特定算例精度认证本文D3Q19阶梯全图。
- [9] Guo–Zheng–Shi：力项表示与一致宏观速度定义的出处。本轮APS官方页可核题名、作者、PRE65 046308及摘要；公式层面使用本地发表版提取和当前源码，而非摘要替代。
- 建议删去首段中泛化的“保持边界动量传递精度”，并将官方基准/回归介绍放到第3章数值检查的语境（现有§3.2已承接）。不新增引文身份，书目[7–9]保持。

## 对旧官方测试报告的更正

本轮直接读取当前testPoiseuille3DBGK.cpp：第275等行是EXPECT_NEAR(actual,expected,errorFactor*1e-6)，不是允许实际误差相对期望值相差1–2倍。PAPER1_OpenLB验证惯例对照_20261106/REPORT.md中“因子级偏差”解释不准确，后续不得沿用；原历史报告不覆盖，纠正在本报告与状态入口记录。这里的errorFactor乘一个绝对容差。保留“存在回归检查”的事实，但回归容差也不成为论文的模型精度阈值。未重新计算该报告全部误差表或重新审计所有OpenLB测试。

## 中文候选

求解采用OpenLB[7]，使用D3Q19速度集和单松弛时间BGK碰撞模型，松弛参数为τ=1；体力项按Guo方案[9]离散。静止固壁采用Bouzidi–Firdaouss–Lallemand线性插值反弹格式[8]，壁面链交点由解析几何确定。已有边界审计记录中的壁面分数距离q=0.5，对应该格式的半程反弹情形；审计范围及精度检查见本节后文与第3章。

驱动由空间均匀、时间恒定的体积力施加，加速度幅值a=1×10⁵ m s⁻²，对应体力密度幅值ρa。主比较采用同一幅值，基准几何的驱动检查见§2.4。宏观速度通过OpenLB的computeU提取，包含与Guo方案一致的半时间步力修正[9]。

驱动候选只替换原长段中的驱动力与速度提取子句，不覆盖停止条件、来源追溯和前轮几何/周期候选。原数字、停止阈值及失败披露不删。符号在正式采用时按现稿LaTeX排版，未新增编号公式。

## 英文对应候选

Calculations use OpenLB [7] with the D3Q19 velocity set and a single-relaxation-time BGK collision model at τ=1. The force term is discretized using the Guo scheme [9]. Stationary solid walls use the linear Bouzidi–Firdaouss–Lallemand interpolated bounce-back rule [8], with wall-link intersections determined from the analytical geometry. The saved boundary-audit records have fractional wall distance q=0.5, corresponding to the halfway bounce-back limit of this rule. The audit scope and accuracy checks are described later in this section and in Section 3.

Driving is imposed through a spatially uniform, time-independent body force with acceleration magnitude a=1×10⁵ m s⁻² and corresponding force-density magnitude ρa. The main comparison uses the same magnitude; forcing checks for the reference geometry are described in §2.4. Macroscopic velocity is obtained through OpenLB computeU, including the half-time-step force correction consistent with the Guo scheme [9].

## 来源与核对范围

本轮定向读取当前两稿§2.1、补充S11、D2当前实现及六个库/测试文件、两份接收报告、本地Guo和Bouzidi指定段提取、旧官方验证报告；逐条回读旧46结果的方法字段，未读取诊断轨迹、重跑几何、接受器或新的保留结果。未声称本轮重新目视原PDF全部页，原公式指定页视觉核验来自已归档报告。

公开访问仅使用已发表文献URL，未外发稿件/数据。官方OpenLB目录与APS页可访问，Bouzidi出版社跳转不可访问，未据此否认已有本地发表版。记录见public_source_checks.json。输入身份及保持见source_manifest.json/verification.json，方法字段见saved_method_fields.json；哈希检查不等于数值验证。

使用已读scientific-writing和academic-humanizer，程序性来源沿用§1.2第一段审读报告所列Kassis等Scientific Agent Skills（2026，arXiv:2609.00065），不另加正文科学引文。

## 停点

本轮只新增本目录和更新两共享状态，正式稿/补充/原方法报告/源码/原结果/系数/阈值保持；既有摘要合入保持，引言及§2.1候选尚未合入。无编译/求解/拟合/新场处理/run_id/Gate/上传，无新长算授权。S4原FAIL、reference_qualified=false、strict_error_bound_established=false、submission_ready=false保持。

下一具体动作：审§2.1的停止判据与历史运行可追溯性，区分停止条件和独立数值验收；若用户要求采用，再按子段范围同步中英文，不覆盖同段其他内容。
