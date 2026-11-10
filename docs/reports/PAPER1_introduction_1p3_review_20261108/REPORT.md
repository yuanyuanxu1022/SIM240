# §1.3研究问题与工作安排审读

日期：2026-11-08（Asia/Shanghai客户端日期）。用户授权检查与§1.2的重复以及主比较、加密和新增结果的身份。本轮生成候选，正式引言不改；不因前一中断或重复请求推断已合入。

## 当前原文

本文针对固定周期、等宽槽与凸台的全充液矩形沟槽，比较局部立方律与显式沟槽计算得到的两主方向导度，量化其对各向异性及张量重建流向的影响，并在同一离散参考下评价既定经验修正的改善与局限。理想Stokes问题中的主导度上界为原公式提供理论解释，数值比较另行报告偏差幅度及参考网格敏感性。

在固定周期、固定槽宽的矩形沟槽中，分别施加沿槽与跨槽驱动，以5 nm网格得到的两个主值为离散参考，在相同几何、通量定义与物性下比较局部立方律，并回顾性评价V2经验修正的剩余残差。四个几何的加密结果用于报告参考敏感性，不构成全地图连续解精度证书。

研究限定于固定间隙、全充液、牛顿液体、无滑移壁面。**不涉及自由表面、润湿、困气、真实胶流变或移动模具**；这些内容需要另外的模型与证据，本文不对其作任何断言。

## 裁定

原文研究对象、方向比较、V2回顾性及加密只代表敏感性的边界基本正确。主要问题是首两段互相重复且与§1.2收束重复，缺少主集合计数与新增h100的角色说明；不是新增结果尚未存在或尚未进入正文，当前§2.1及§4.4已有相应安排。

### 研究问题

首段改为三项可由本文实际结果回答的问题：双主导度的偏差差异、各向异性比/主值重建平均流向的后果、既定修正的改善及几何/参考敏感性。“重建”保留，不把张量推算角差写为测得的工艺流向误差；不把残差变化写成唯一机制或间隙缺项的证明。几何趋势仍受采样及历史构建来源的正文限制。

### 与§1.2的分工

- §1.2负责已有工作、本文区别及连续上界/离散比较/应用精度的关系。
- §1.3负责问题句、实际计算安排与数据角色。删去在此再次介绍上界性质、解释原公式及重列证据层次的句子；定理仍由§1.2/§2.3/附录E承接，不删除理论贡献。
- 原首两段的“同一参考评价V2、比较双向偏差、报告敏感性”合并，保留其中有必要的研究设计信息。
- 原第三段的物理范围正确。候选在研究对象句中正面明确固定间隙、全充液、牛顿与无滑移；自由表面、润湿、困气、真实胶流变、移动模具未验证的详细披露仍保留§1.2应用边界、方法和§5.4，不扩展主张。
- 小节题名可用“研究问题与研究安排”，英译Research questions and study design；本轮仅候选，不改正式题名。

### 数据身份

|类别|几何与记录|用途|计数/证据边界|
|---|---|---|---|
|主比较|18种几何、36个主方向结果，5nm|原公式/V2主统计；每种沿槽Kyy、横槽Kxx各一|不是36种几何；V2是回顾性评价，不认证独立预测|
|加密|上述4种旧几何、8条2.5nm记录|参考敏感性|不是4种新增几何；主统计不替换为混合网格，不构成全图连续参考资格|
|新增间隙|h100/d100一种新增几何、两方向5nm结果|原公式与固定V2的补充比较，系数不据新增结果重拟合|不并入原36主统计，不认证严格盲测或连续域预测精度|
|构建复现|h75/d100两方向复算，配对历史记录|单几何构建输运复现|不另增比较几何/独立样本，也不认证全部历史构建等价|

本轮由既有已审CSV重新计数：旧44=36主+8加密；新增h100两条后共19几何46条，5nm为38条、2.5nm为8条。h75构建复跑不加入这一计数。与旧边界审计46条及D2/D3清单52条的集合区别保持，详见当前§2.1。候选不重复堆入总46或构建复现的技术细节，方法中的完整数据角色表继续承接。

## 中文候选（题名建议：研究问题与研究安排）

本文围绕三个问题展开：局部立方律对沿槽和横槽导度的偏差有何差异；这些差异如何影响各向异性比及由主值重建的平均通量方向；既定V2修正能改善到何种程度，其剩余偏差如何随几何和参考网格改变。

研究对象为固定间隙、全充液、牛顿液体和无滑移壁面的周期矩形沟槽，周期与槽宽固定，槽与凸台等宽。分别施加沿槽和横槽驱动，主比较采用18种几何的36个主方向导度结果（每种几何沿槽、横槽各一个），网格间距为5 nm，在统一导度定义下评价原公式，并回顾性评价既定V2。

其中4种几何的8条2.5 nm加密结果用于检查参考敏感性；另以h=100 nm、d=100 nm新增几何的两方向5 nm结果，在保持V2系数不变的条件下作补充对照。两类补充结果均与原36个结果的主统计分列。

## 英文对应候选（Research questions and study design）

This study addresses three questions: how local-cubic-law discrepancies differ along and across the grooves; how these differences affect the anisotropy ratio and mean flux direction reconstructed from the principal conductances; and how much the fixed V2 correction improves agreement, including how its remaining discrepancies vary with geometry and reference-grid resolution.

The configuration consists of periodic rectangular grooves at a fixed gap, fully filled with a Newtonian liquid and bounded by no-slip walls. The period and groove width are fixed, with equal groove and rib widths. Along-groove and across-groove forcing are applied separately. The main comparison uses 36 principal-direction conductance results for 18 geometries, with one result in each direction per geometry on a 5 nm grid. A common conductance definition is used to assess the original formula and retrospectively evaluate the fixed V2 correction.

Eight refined results on a 2.5 nm grid for four of these geometries characterize reference sensitivity. Two further results on a 5 nm grid for the additional geometry h=100 nm, d=100 nm provide a supplementary comparison with the V2 coefficients held fixed. Both supplementary sets are reported separately from the original 36-result main statistics.

## 核对范围与停点

实际读取当前中英文§1.2末尾/§1.3/§2.1数据角色表、已审§1.2收束候选、既有新增验收候选和计数记录；直接读取旧44与新六条标量CSV，按几何/网格/方向独立重计集合。此为已有表的角色/计数复核，不重新核验原始收敛轨迹、求解器或全部数值精度。新增验收候选文件的旧“未合入”仅为当时历史状态，当前正文已包含新增比较；本轮未错误退回“h100未入稿”。

来源及保护哈希见source_manifest.json，计数见record_inventory_recount.json，文稿保持与状态范围见verification.json。本轮使用已读scientific-writing/academic-humanizer流程；程序性来源沿用§1.2第一段报告所列Kassis等Scientific Agent Skills（2026，arXiv:2609.00065），不另加正文科学引文。没有新增文献身份或联网检索。

正式中英文引言未合入候选，摘要此前合入保持；原数据/系数/阈值不改。无新数值求解或数值接受、编译/拟合/场处理/run_id/Gate/上传；S4原FAIL、reference_qualified=false、strict_error_bound_established=false、submission_ready=false不变，无新长算授权。

下一具体动作：继续逐部分审§2.1几何定义、坐标方向与间隙参数；若用户明确要求采用引言候选，再同步合入中英文并核整章重复。本轮未执行引言合入或全文终审。
