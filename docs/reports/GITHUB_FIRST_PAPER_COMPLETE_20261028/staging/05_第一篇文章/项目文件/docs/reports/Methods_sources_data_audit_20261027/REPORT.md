# 当前稿方法引文、构建来源与数据访问核对

日期：2026-10-27。作者请求的内部核对，使用citation-management、scientific-writing、peer-review及PDF技能；不代替编辑决定或最终作者批准。当前稿为[正式工作稿](../SIM240_中文稿_导师审阅版_20261022.md)。本轮未改变理论假设、推导范围、数值阈值或严格误差界，没有触发新的Astra理论复核，也未切换实际模型。

**结论：文献[6]的题名问题已订正并补DOI；已明确各方法引文实际核到哪一层；私有共享快照的访问和覆盖范围已核清并写入稿件。完整历史构建来源、[8]/[9]原文逐式支持及[10]发表版的完整版本核对仍未闭合。** 不把无法访问全文说成文献不存在，也不把书目信息正确说成全文支持已经全部通过。

## 1. 方法引文逐项裁定

|编号|实际证据与定位|本轮裁定及正文处理|剩余缺口|
|---|---|---|---|
|[4] Patir–Cheng 1978|既有本地PDF的印刷第15页式23/24，本轮实际查看原页图；正文§2.3局部两高度平均关系|指定一维Reynolds关系有原文支持；保留同深度定义和模型范围限定|不据其证明完整台阶域精确流场、主导耗散或项目空间精度；本轮未重审其全部内容|
|[6] Dewangan–Datta 2018|[Crossref登记](https://api.crossref.org/works/10.1016/j.euromechflu.2018.02.004)及[作者机构出版目录](https://web.iitd.ac.in/~subhra.datta/publications1.html)；原始JSON/HTML已保存|原题名“Semi-analytical solution for flow in a sinusoidal grooved channel”不正确。改为 *Flow through microchannels with topographically patterned wall: A spectral theory for arbitrary groove depths*，70卷73–84页，2018；补DOI 10.1016/j.euromechflu.2018.02.004|未取得全文，不能将任意幅度的具体适用条件标为本轮原文已核。引言改为书目可支持的谱理论/槽深研究描述；没有认定旧幅度说法必然错误|
|[7] OpenLB软件论文|[OpenLB官方目录](https://www.openlb.net/articles/)与Crossref元数据；`ref7_crossref_retry.json`|最终卷页为2021、81、258–288，与正文一致；官网旧条目使用2020年，不据此改成旧年份。软件身份闭合，当前源码另核|软件论文与当前源树都不能反证52项历史运行的库提交/编译身份；未逐页审软件论文|
|[8] Bouzidi–Firdaouss–Lallemand 2001|Crossref中的出版社登记元数据及摘要；13(11)、3452–3459、DOI10.1063/1.1399290|方案身份及反弹结合空间插值有摘要支持；没有发现当前规范书目需要修改。q=.5、无fallback/unresolved属于项目记录证据|AIP PDF请求403；本轮未取得全文，未逐式比对实现。不得写成任意壁距二阶或边界零误差已获证明|
|[9] Guo–Zheng–Shi 2002|Crossref：PRE65(4)、046308、2002；当前OpenLB `dynamics.h:217—228`的ForcedBGK/PlainGuo与`momenta/elements.h:1601—1608`的FORCE/2|书目信息和当前实现说明可核；原正文保留|APS全文接口401；没有逐式核原论文，当前源码与历史二进制的完整来源绑定仍缺|
|[10] Celik等GCI方法|[ASME官网方法文稿](https://www.asme.org/wwwasmeorg/media/resourcefiles/shop/journals/jfenumaccuracy.pdf)；PDF第6—7页（文稿页4—5），步骤3—5及式3—7，已渲染查看；Crossref卷页/DOI及ASME官方引用记录|观测阶、三格、外推值和GCI的定义有直接方法文稿支持；正文保留2008发表版书目，补充材料标明版本边界|官网文稿列Celik/Ghia/Roache/Freitas四位作者；期刊版引用含另外两位作者，不能冒充同一版本的逐页核验。发表版全文尚未取得；方法成立不使本项目历史FAIL转PASS|

当前文稿只改[6]书目；其余方法引文保留各自已核范围。**范围内引用可以使用，不等于每篇方法论文全文与全部项目实现已逐式闭合。** 本轮没有全面复核引言[1]—[3]、[5]或讨论[11]，没有宣称全参考文献终校完成。

原始获取证据在[evidence/](evidence/)：Crossref JSON、作者机构HTML、公开请求结果，以及ASME原文稿/文本和公式页预览。ASME这份文稿为15页组合文件，前2页是编辑准确性说明，后续才是方法文稿；定位不能把PDF页号直接当成发表版页码。当前使用的是原文公式页的视觉核对，未依赖损坏的PDF公式文本提取判断分母。

## 2. 来源说明：哪些能够确认，哪些仍然不能

本轮直接读取补充表S1对应的52份结果、52份运行清单、独立退出记录和日志入口。36主方向、8加密、6斜向、2黏度对照的统计范围保持，不扩充为所有项目运行。

- 52份指定清单仍均有binary_sha256，四组分别22/22/6/2项。
- 同一52份清单均缺source_sha256、generated_source_sha256、openlb_commit、compiler、compile_flags字段。此结论只针对指定清单，不等于断言全文件系统不存在任何其他历史档案。
- 当前D2二进制SHA为`57611b21584c8f32dabd5d4ff240616c65f245930b00a1a40dae5f8d3169f2d6`，与22项记录相符；当前D3二进制SHA为`85cc9dee8db9a245419a3a152efb72fc9958e29b8dac7a356f4667e54fd5bf66`，与6项记录相符。只核字节身份，**没有执行二进制**。
- 当前OpenLB HEAD为`882924a9cfc8dcdf82909e39530789cb6f5ebcc4`；当前D2/D3 Makefile固定注入`5953d8a-dirty`。不能用该字符串证明历史依赖版本，也不能把当前HEAD补写入历史manifest。
- 当前ForcedBGK、PlainGuo及半步力修正的源码位置已读；这属于当前实现证据，不能证明全部历史运行都由该源文件构建。

具体逐运行列表、缺字段计数及现存二进制观察见[provenance.json](provenance.json)。**来源限制尚未关闭；本轮没有通过重新编译、重跑或补写旧清单来制造来源完整性。** 若继续追溯，最少应寻找与原二进制关联的源码快照、编译日志/命令、编译器及依赖提交证据；恢复不了就保留明确限制，是否建立另版可复现基线由后续任务裁定。

## 3. 数据声明：当前实际访问条件与覆盖

GitHub API本轮实际读回：仓库[yuanyuanxu1022/SIM240_code_figures_data](https://github.com/yuanyuanxu1022/SIM240_code_figures_data)为private，默认分支main，远端仍为[f11c0f20f6aaadf6920b95390855ec418cf8ae42](https://github.com/yuanyuanxu1022/SIM240_code_figures_data/commit/f11c0f20f6aaadf6920b95390855ec418cf8ae42)。这确认受限共享，不是公开下载或公开数据存档。

远端固定树未截断，共8637个blob；来源清单声明8591份文件，全部对应路径存在。**清单文件数不等于整个仓库文件数。** 本轮实际读取并以大小、SHA256及Git blob SHA与远端树交叉核对446份选定文件，全部一致；没有重新读取整个8591文件档案，不能称本轮全库逐字节复验。

|与当前稿有关的内容|快照覆盖/本轮核对|对数据声明的含义|
|---|---|---|
|52项D2/D3结果、运行清单、退出记录|逐项在清单和远端树可定位；内容与当前来源一致|这些保存记录在指定私有快照可追溯|
|52项日志入口|逐运行映射一致，其中4项共享批次日志；不把引用次数当作独立日志文件数|日志链可以定位，不应误称4项日志缺失|
|四份主要绘图输入CSV|4/4与当前相同|主要图的数值输入可追溯|
|三份主要绘图脚本|均有旧版；仅1/3与当前字节相同|make_fig4.py及make_fig7_fig8.py的10月27日文字更新未在该固定提交|
|四图共12份PNG/PDF/SVG|全部有旧版；其中6份与当前相同|当前图2与图3的6份更新导出未在该固定提交；不据此指称其原始数值数据不同|
|当前正文与编号方法补充材料|来源清单中未纳入这两份当前文档|仓库不构成当前稿件全部材料的同步版本|
|真实N8原始场/完整运行记录|原发布范围明确排除；本轮没有读取真实N8数组或提取指标|不能把方法资料上传说成N8数值参考已经交付或合格|

覆盖判定使用来源清单的原项目路径和固定远端树条目，配合共享包README明确排除正文的范围说明；没有把它当作全库语义内容复验。每条来源与包内位置见[share_coverage.json](share_coverage.json)，API与各类计数见[availability.json](availability.json)，逐文件字节范围见[package_file_checks.json](package_file_checks.json)。

正文附录C已经写入有日期、固定版本和访问条件的实际说明，最终公开范围/访问方式/持久标识仍待作者确认。不替作者承诺“无条件提供”“合理请求即提供”、公开时间、许可或DOI；本轮没有核准目标期刊政策，也没有将仓库改成公开、创建发布、上传文件或推送提交。

## 4. 小范围文字订正与保护

改动共9处：正文7处（[6]题名/DOI、引言幅度说法收窄、书目注、附录C数据/引文待核行、实际访问说明、D.9记录）；配套方法补充材料2处（S10复核段、S11更新）。逐字记录[editorial_changes.json](editorial_changes.json)，差异[editorial_changes.diff](editorial_changes.diff)，修改前全文在[before/](before/)。

主式（1）—（7）、附录E推导及式（E1）—（E6）、V2系数、8张主数值表、摘要、结果、讨论和结论保持。补充表S1—S4不改；原始结果、源码、历史FAIL、G4锁与合同不改。旧报告的基稿哈希继续作为当时快照证据，不追改旧证书；本轮验证入口为`verification.json`。

## 5. 获取失败、工具修正与未闭合清单

- Crossref首次6项并发请求有3项429，已用间隔后的指定请求补取[7]/[9]；[4]仍以已授权本地原文核对，不把429当论文错误。
- Bouzidi AIP PDF为403，Guo APS全文接口为401，[6]出版社摘要/正文为403；这些失败按[公开访问日志](evidence/public_fetch_log.json)保留，未绕过付费墙或冒充取得全文。OpenLB最初误用/publications/得到404，改用已知官方/articles/核对。
- 独立共享副本采用稀疏检出，首次工具错误地把未展开文件记为本地缺失（8369项），并非远端缺失。初次结果另存`initial_availability.json`、`initial_package_file_checks.json`与`initial_audit_sources.log`。改用远端树、当前相同来源字节及固定Git对象核验446份；按对象逐件触发网络读取的较慢中间检查已停止并优化，只读缓存变化不改变远端内容。最终远端路径检查和所选字节核对全部通过。
- 文档链接检查初次未识别“文件路径:行号”的有效定位格式，误报两条源码链接；修正路径解析后通过，初次JSON/日志另存`verification_initial.json/log`，未为此改动源码或原链接。
- ASME官网文稿与发表版的版本差异如第1节，不能混合作者清单和页码来宣称同版全文已读。本轮没有对已有GCI数值再计算或审定严格误差界。

**仍需补证的最小事项：** [8]/[9]若要声称原论文公式与实现逐式一致，需合法全文及指定公式核对；[10]若要宣称发表版全文核验，需发表版或可靠版本对应证据；[6]若恢复具体幅度适用条件，应先实读原文；历史构建身份需与旧二进制关联的档案；数据最终声明需作者决定实际公开/访问安排并核对目标期刊。现有受限共享的事实已可写明，无需等待这些条目才能如实描述现状。

## 6. 权限、状态与接续

本轮没有新求解run_id。旧N8仍`D4_N8_diag_v3_1_20261026_v1`、ONE_N8_DIAGNOSTIC_ACCEPTED；NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null。`reference_qualified=false`、`strict_error_bound_established=false`、`submission_ready=false`，预测HOLD。本轮无编译、求解、真实N8提取、拟合、保留评分或Git提交推送，没有向他人发消息。

下一具体动作可先补上述缺失原文/历史档案，再据实际访问安排完成作者数据声明和图件嵌入；本报告不启动新数值验证。涉及假设改变、理论实质推广或严格误差界时按项目要求建议GPT-6 Astra｜High复核，建议不等于实际切换。

Skill方法来源：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://arxiv.org/abs/2609.00065)，2026-10-27实际核公开页为v2，未见期刊字段。只列本核对方法来源，不加入论文CFD参考文献。用户自有稿件与本轮明确请求授权内部AI辅助；未向额外检索服务发送稿件、私有数据或审查内容。作者最终核验/署名批准未由本轮工具代替。
