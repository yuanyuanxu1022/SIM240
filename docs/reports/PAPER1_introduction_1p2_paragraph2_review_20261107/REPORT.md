# §1.2第二段审读：Dewangan–Datta的方法、几何与引用作用

日期：2026-11-07。用户授权逐段审读；本轮形成双语候选，不合入正式引言，不重新证明文献定理或复算其算例。

## 当前原段

> 受限沟槽的有效输运张量本身已有解析与数值研究。Dewangan 与 Datta 采用谱分析结合区域摄动，建立了张量关系并对代表形貌作了数值评价 [5]；同一作者还研究了一面正弦起伏壁与一面平壁之间的沿槽流动，其完整谱方法不以小振幅为前提，并另行给出受相应极限条件约束的渐近近似 [6]。这些工作说明"沟槽带来各向异性输运"本身不是新发现。

## 方法性质与裁定

原段关于[6]完整谱方法与渐近式的分层基本正确，应保留；关于[5]应补小形貌幅度与周期之比的渐近条件，并把数值评价具体为与显式有限元Stokes解比较。

| 文献 | 实际方法和问题 | 本文引用作用及边界 |
|---|---|---|
| [5] Dewangan–Datta 2020，JFM891 A12 | 谱表示结合区域摄动，在小形貌幅度/周期比的渐近框架下求纵向、横向主值及张量关系；保留有限通道高度作用。§4.1–4.2以平滑相位调制起伏和三角形槽作理论—显式有限元Stokes解比较 | 是方向性主值、张量描述和理论—数值对照的重要近邻。不能因标题含arbitrary shape，便认为任意非光滑形貌/幅度均有可直接使用的精确解；其近似误差与数值交叉检查不转移为本项目的精度证书 |
| [6] Dewangan–Datta 2018，EJMB70 73–84 | 一面正弦起伏壁、一面平壁，沿槽充分发展流；完整半解析谱解不依赖小振幅展开，另给小幅度、厚/薄通道等极限下的渐近式，与有限元作交叉对照。滑移另有渐近扩展 | 是有限间隙图案壁输运及完整谱解/渐近式分层的重要近邻。主算例为正弦沿槽，不直接提供本文矩形槽两主值；“无小振幅前提”限其几何与物理可容许条件，不等于任意形状/参数/精度 |

谱方法指用一组周期函数表示形貌或速度场；区域摄动指围绕参考平面，用小形貌参数逐阶近似。二者可以组合，并非互相排斥的方法名称，但“用了谱表示”本身不取消摄动的条件。

## 几何限制的精确说法

- [5]的§3令ε=2πe/L为小参数，展开至二阶；e为原文形貌尺度，L为周期。本稿残余间隙h、槽深d与原文符号不直接相等。不是“d/h必须很小”，也不把其数值探索范围当作严格误差保证。
- [5]§4开头明确：方波高度跳变的Fourier系数衰减导致S1发散，影响式（3.11）、（3.21）的渗透率表达式及式（3.25）的有效滑移表达式。此限制属于这些摄动表达式，不能推为矩形槽没有有限Stokes解、所有谱/解析方法均不可用，或显式CFD是唯一途径。
- 三角形形貌连续但有尖角，区别于方波形貌的高度跳变；[5]恰有三角形的有用对照结果。因此不能写“有角就失效”。
- [6]稿内21–22页讨论向其他周期形貌扩展及矩形非光滑性可能损失指数收敛，不是证明矩形槽绝对不能用谱方法。稿内24页将跨槽流动列为后续工作。
- [6]原文h为平均高度、a为正弦振幅，本文h为最小残隙、d为槽深，不可同名代入；原文无量纲流量比与本文m³导度亦须转换。详细定义继续由方法/补充材料说明。

## 近邻研究的引用作用

[5,6]说明有限间隙图案壁的方向性输运、主值和张量框架已有研究基础。不能把“发现沟槽各向异性”“首次对照解析关系与数值解”作为本稿已确立的新颖性。本文可明确其实际工作：在指定矩形槽族和匹配定义下量化局部立方律双向离散偏差、各向异性后果，并评价既定修正；这一工作描述不自动完成全面新颖性或录用判断。几何有差异也不免除与[5,6]的讨论。

当前§1.2第三段已具体说明方波限制，建议本段只写研究范围和方法层次，后段保留具体限制；后续合入时检查重复，不在每段堆同一组免责声明。

## 中文候选

> 受限沟槽的方向性输运及其张量描述已有解析与数值研究。Dewangan 与 Datta 在形貌幅度相对周期较小的渐近框架下，结合谱分析和区域摄动建立两主方向的输运关系，并以显式有限元 Stokes 解评价平滑起伏与三角形沟槽的结果[5]。其较早的研究针对一面正弦起伏壁与一面平壁之间的沿槽流动，采用不以小振幅展开为前提的完整谱方法，并另行给出特定极限下的渐近近似[6]。这些工作为本文评价矩形沟槽中的双向公式偏差提供了理论与数值研究背景。

## 英文对应候选

> Directional transport in confined grooves and its tensor description have been studied analytically and numerically. Dewangan and Datta combined spectral analysis with domain perturbation in an asymptotic framework for small topographic amplitude relative to the period, deriving transport relations for both principal directions and assessing predictions for smooth undulations and triangular grooves against fully resolved finite-element Stokes solutions [5]. Their earlier study considered along-groove flow between a sinusoidally corrugated wall and a planar wall. It used a full spectral method without a small-amplitude expansion and separately derived asymptotic approximations in specific limits [6]. These studies provide theoretical and numerical context for the present assessment of directional formula discrepancies in rectangular grooves.

## 实际核查范围与来源

本轮为作者授权的AI辅助引文与文字检查，不冒称独立人工作者审定或新理论终审。当前稿件与书目[5,6]已读，未改文献身份/编号。

- [5]定向重读本地发表版提取文本 `docs/reports/Primary_text_received_20261027/evidence/NEW_THIRD.txt`：摘要、引言目的、§3的小参数/量纲、§4开头的方波和三角形区分、§4.2有限元设置和§4.5梯形跳变限制。定位：该文本17–31、211–225、340–345、393–405、891–941、1110–1137及1717–1733行。非全文逐式推导复核。
- [5]出版社公开全文初次可打开，后续指定行/查找超时；公开搜索亦返回同一出版社论文/PDF。主要技术判断以本地发表版上述原文定向读取为依据，未把网页超时当成文献不存在。
- [6]定向重读已接收Accepted Manuscript的全文提取 `docs/reports/Dewangan2018_received_20261028/evidence/accepted_manuscript.txt`：摘要、主几何与式（1）–（4）、稿内21–24页结论和形貌扩展段；对照原接收报告的版本及指定条件记录。本轮未重新目视全部页图或将接收稿页码冒称发表版73–84页定位。出版社公开检索返回的摘要/引言与上述方法层次一致。
- 网页仅查询公开文献题名、DOI与出版社URL，未向外部发送稿件或未发表结果；不执行新全文文献检索或新颖性裁定。

公开来源：[5] https://www.cambridge.org/core/journals/journal-of-fluid-mechanics/article/effective-permeability-tensor-of-confined-flows-with-wall-grooves-of-arbitrary-shape/089D6608B5CF065BAC9B1C4F7D42FBCF ；[6] https://www.sciencedirect.com/science/article/pii/S0997754617305010 。[6]接收/版本报告 `docs/reports/Dewangan2018_received_20261028/REPORT.md`。

本轮使用已读scientific-writing与academic-humanizer流程；程序性来源沿用上一段审读报告所列Kassis等Scientific Agent Skills（2026，arXiv:2609.00065），不作为流体物理论据，不另加正文引文。

## 停点

本轮仅新增审读目录及更新两共享状态，正式中英文引言未改，已合入摘要保持。无新增数值计算或验证、求解/编译/拟合/场处理/run_id/Gate/上传；S4原FAIL、reference_qualified=false、strict_error_bound_established=false、submission_ready=false不变。

下一具体动作：按逐段节奏审§1.2第三段的同条件差异、定义换算、方波限制和贡献句，压缩与前两段的重复；若用户要求采用，再同步合入已审中英文候选。无长算命令或新运行授权。
