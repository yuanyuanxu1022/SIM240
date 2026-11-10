# 新下载原文接收与指定方法核对

日期：2026-10-27。沿用`Primary_text_build_evidence_20261027/MINIMUM_EVIDENCE_CONTRACT.md`，只核用户指定`/home/dell/下载`刚新增的三份PDF及对应当前源码，不运行编译、求解、原后处理或真实N8提取，不修改理论假设、公式门槛或历史FAIL。

## 1 接收判定

|合同项/身份|本次文件|实际版本与范围|结论|
|---|---|---|---|
|P9 / 正文[9]|DiscretelatticeeffectsontheforcingterminthelatticeBoltzmannmethod.pdf|Guo、Zheng、Shi，PRE65(4)，046308-1—6，2002；DOI10.1103/PhysRevE.65.046308；六页连续，目视第1—3页公式及第6页尾页|收到、发表版身份已核、合同指定力项/速度与所查当前实现关系已核|
|P10 / 正文[10]|Procedure for Estimation and Reporting of Uncertainty Due to Discretization.pdf|Celik等，JFE130(7)，078001-1—4，2008；DOI10.1115/1.2960953；四页全部目视，六位作者列在末页|收到、发表版身份已核、合同指定步骤/公式及迭代误差附录的版本对应已核|
|额外 / 正文[5]|effective-permeability-tensor-of-confined-flows-with-wall-grooves-of-arbitrary-shape(1).pdf|Dewangan、Datta，JFM891，A12，2020；DOI10.1017/jfm.2020.134，35页；目视首页题名、作者、出版信息及摘要|身份已核；不是P8，也不是正文[6]的2018年论文。本轮不新增其全文理论适用性裁定|
|P8 / 正文[8]|本次三份中没有|Bouzidi/Firdaouss/Lallemand，10.1063/1.1399290，3452—3459|仍OPEN；不把另一篇论文的书目或主题相近文章计为原件|

额外2020年文件与目录中不带`(1)`的既有副本同为911,378字节、SHA256 `e810b629d1159e4b8e2bcfd8f589dc2d649f4648189ce1fcf2129462cb1549fb`，是相同内容副本，不计作新的独立方法证据。

P9 SHA256：`45ee2cd22b7a2c02709b0b2f440d093d3385cb7611e0551c36adb55d822d66db`，92,706字节。P10 SHA256：`8edaafdfa44de3d8acf6729546c78f3d45616b71102b06588b1388a1fa95e6ce`，247,593字节。完整路径、pdfinfo、文件大小、提取退出码见`intake.json`。仅记录用户本地提供的取得路径；P10页边还载有ASME来源与2026-10-27下载日期。未将订阅PDF复制进共享仓库或远端发布。

## 2 P9：原文与当前OpenLB的对应

|原文定位|原文内容与符号|当前实现定位|核对结论|
|---|---|---|---|
|046308-1，式(4)前与式(4)|F=ρg是力密度；LBE加入Δt Fi|D2源码704—708行，FORCE赋值为a_phys dt²/dx乘驱动方向|项目FORCE字段是格子加速度，不能与论文F直接同名等同；格子力密度为ρ_lat乘FORCE|
|046308-2式(17)，046308-3式(19)|ρv=Σei fi+Δt F/2；半步修正用于流体速度|`/home/dell/openlb/src/dynamics/momenta/elements.h:1601—1608`，基础computeU后加FORCE/2|在格子Δt=1且F_lat=ρ_lat a_lat下，速度修正为a_lat/2；对应所查实现|
|046308-3式(20)|Fi=(1−1/(2τ)) wi[(ei−v)/cs²+(ei·v)ei/cs⁴]·F|`/home/dell/openlb/src/dynamics/lbm.h:568—586`：括号的分量形式乘rho(1−omega/2)及wi|omega=1/τ、F_lat=ρ_lat FORCE，项结构、密度因子及松弛系数对应|
|046308-1式(5)、046308-2式(17)与046308-3式(19)—(20)|平衡速度与流体速度采用同一半步修正|`forcing.h:36—68`的PlainGuo以Forced矩计算rho/u，并交给碰撞与力项；`dynamics.h:224—230`绑定BGK和PlainGuo|当前组合路径可定位；D2的`cell.computeU`提取在475行，未另行重复半步加力|
|046308-2式(15)|ν=(τ−1/2)cs²Δt|D2源码43行，dt=(τ−.5)dx²/(3ν_phys)，tau=1|D3Q19格子cs²=1/3时，单位转换相符；不是对全部历史可执行文件的来源证明|

源码均指`CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp`及上述当前OpenLB文件。片段含原行号和内容SHA，见`current_implementation.json`。只核所查通用力项和组合定义；未编译、运行或证明每一后端生成特化与通用函数逐项等价。原文以D2Q9说明并给矩表达，不能把原文中的数值测试当作本项目D3Q19、任意边界或多相问题的独立验证。

关闭范围：P9指定力项、速度、半步修正、松弛因子与密度/格子单位的原文—当前实现对应。保留范围：历史构建绑定、数值参考资格、项目误差及物理验证不随之升级。

## 3 P10：发表版与既有四作者文稿的指定对应

|合同内容|期刊发表版定位|既有ASME文稿定位|对应结果|
|---|---|---|---|
|书目身份|078001-1题名/DOI/130卷，078001-4六作者名单|PDF3页题名为四作者版本|属于不同版本；发表版六人为Celik、Ghia、Roache、Freitas、Coleman、Raad。Crossref本次未给作者字段，作者以实读末页为证，不补造元数据|
|迭代收敛前提|078001-1 Preliminaries|文稿Preliminaries|先检查迭代收敛；残差降3—4数量级仍不一定充分，需参照附录。不能将现存短窗rel_std自动换算为这个残差证据|
|网格与比值|078001-1步骤1—2及078001-2开头|文稿步骤1—2|至少三套系统加密网格；r>1.3为经验建议，不是形式推导|
|p与q(p)|078001-2步骤3，式(3a)—(3c)|文稿PDF6页，式(3a)—(3c)|指定公式及等比q(p)=0说明对应；p与形式阶相符是支持迹象，反向不能直接判不合格；发表版表1也有p=.75示例|
|外推|078001-2步骤4式(4)|文稿PDF7页式(4)|两版均标φ_ext的上标21，外推代数式对应|
|ea、e_ext、GCI|078001-2步骤5式(5)—(7)|文稿PDF7页式(5)—(7)|指定定义及Fs=1.25对应；**发表版式(6)也把式内外推量写为上标12，而式(4)写21**。符号不一致确实保留在发表版，不能声称发表版已修正；现稿统一定义φ_ext的写法可维持|
|迭代误差|078001-3—4附录式(A1)—(A3)|文稿PDF14页式(A.1)—(A.3)|指定估计式与λ接近1时相邻迭代差不可靠的提醒对应；建议迭代误差比离散误差至少小一个数量级。没有新增本项目迭代误差估计或严格界|

两版本的作者、排版、引文编号存在差别，本轮仅关闭合同指定方法内容与版本对应，不称所有文字逐字一致。保留上一轮GCI裁定和表S5：历史比值不能独立确认渐近区；低p不自动判错；历史细T失败仍影响三项。完整方法原文得到补齐，不等于本项目已满足全部方法适用前提。

## 4 文件维护、仍缺与权限

只更新当前补充材料S11的P9/P10来源状态、加入额外[5]副本身份说明，并相应收紧正文附录C“参考文献终校”的剩余清单。正文模型、理论附录、结果、表S1—S5、数值、参数、源码、协议与旧审查报告保持。修改前快照和差异保留在本目录。

仍需：P8 Bouzidi完整8页及指定分支/时间层对应；正文[6]2018年Dewangan–Datta论文全文及具体条件核对；四组历史程序完整构建绑定。后两项不会被本次[5]2020年副本或P9/P10原文替代。没有新增历史构建档案，四组仍OPEN；未重复全盘检索，不宣称材料不存在。

无新run_id、编译、求解、真实N8提取、拟合、第二项或Git提交推送。旧N8 run_id=D4_N8_diag_v3_1_20261026_v1，NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、reference_qualified=false、strict_error_bound_established=false、submission_ready=false，预测HOLD。当前没有长计算启动命令或新增运行许可。

本轮没有假设改变、理论实质推广或严格误差界审定，未触发新的Astra复核；沿用既有Astra审定边界。

## 5 来源及验证

Crossref API按三个DOI逐项读取，完整响应保存`evidence/crossref_*.json`，提取书目信息见`crossref_identity.json`。三个调用均成功；P10作者字段缺失以发表版末页独立核对。APS官方落地页也核得P9身份；ASME DOI浏览访问403不影响已接收本地PDF，JFM DOI浏览失败保留为访问状态，不伪称线上全文读取。未重复下载全文。三份PDF文本提取均exit0，九页原件加一页旧文稿附录共十页已渲染并目视。

按paper-lookup/PDF及scientific-writing技能组织本地证据与来源状态。流程来源仅列本报告，不加入CFD方法引文：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents. [arXiv:2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。本轮在线核作者及版本。

选定保护输入、原件哈希、指定页及状态同步核对见`verification.json`和`protected_inputs.json`。这些是资料/文档核对，不是数值Gate或全部源码的证明。

最终19项检查全部通过，62份选定保护文件（含收到的原件、所查源码与旧表/证据）字节不变，44条本地文档链接可解析。正式稿仅附录C的一项清单改变；补充材料仅S11的三条来源状态改变，S1—S10及表S5说明原样保留。
