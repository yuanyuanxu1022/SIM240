# 指定方法原文与历史构建证据追溯

日期：2026-10-27。范围：承接[上轮方法审查](../Methods_sources_data_audit_20261027/REPORT.md)，补查参考文献[8]、[9]原文、[10]发表版及其版本对应，并追溯补充表S1指定52项D2/D3记录的历史构建档案。用户要求涉及假设改变、理论实质推广或严格误差界时使用GPT-6 Astra｜High复核；本轮没有进入这些变更或审定，没有声称切换模型。

**本次只补到部分证据，指定缺口尚未全部关闭。** 新增两份现存运行程序内部的GCC标记/Build ID、四份源码/Makefile与固定共享提交的一致性证据，以及[10]发表版的机构书目记录。没有新取得并逐页验收[8]、[9]或[10]发表版全文；没有恢复四组历史程序的完整源码—依赖—编译绑定。正文、补充方法、公式、数值表、原始记录和历史FAIL保持不变。

## 1. 原文获取与版本证据

逐请求URL、参数、实际状态、响应大小和SHA256见[retrieval_ledger.json](retrieval_ledger.json)。OpenAlex和Semantic Scholar共六份按DOI记录均返回200，解析时核对了返回DOI，未把200或开放获取标签当作取得全文。没有借助作者联系、图书馆账号或私有稿件上传扩大本轮权限。

|条目|本次实得证据|仍未取得的指定证据|判断|
|---|---|---|---|
|[8] Bouzidi–Firdaouss–Lallemand，DOI 10.1063/1.1399290|两索引身份一致；两者均未返回公开PDF地址；HAL按DOI精确检索返回0条|合法完整原文，以及固定壁面插值分支、符号/时间层与项目边界实现的逐项对照|全文缺口保留。HAL 0条只表示这次DOI检索未命中，不代表不存在任何作者版本|
|[9] Guo–Zheng–Shi，DOI 10.1103/PhysRevE.65.046308|两索引身份一致；未返回公开PDF地址。查到作者机构目录及作者个人页面线索|合法完整原文；体力项、速度定义、力密度与加速度约定的原式核验|APS PDF请求TLS连接失败；作者机构页也连接失败，作者个人页面及ResearchGate响应403。没有原版公式页可验收|
|[10] Celik等，DOI 10.1115/1.2960953|OpenAlex/S2给出同一确切发表版PDF地址；取得KFUPM机构目录HTML，citation元数据列六作者、2008/07、130(7)和DOI|发表版PDF或可靠的逐页版本对应；与已存四作者方法文稿对照|机构书目身份补强，全文/版本逐页对应仍开口。出版社PDF403；CiteSeer搜索片段对应的下载URL本机404、web工具403|

[10]的[机构记录](https://pure.kfupm.edu.sa/en/publications/procedure-for-estimation-and-reporting-of-uncertainty-due-to-disc/)及原始HTML，详见[ref10_version_identity.json](ref10_version_identity.json)。该记录把出版时间列为2008/07，另有2022/09/28的online字段，不能拿后者改论文发表年。其原始起止页字段为780011/780014；当前书目继续使用上轮出版社/Crossref已核的文章号078001，不擅自生成另一页码格式。

S2这条记录却列2007年和四作者，不能直接覆盖发表版书目。本次保留原始冲突，并以机构目录和已有ASME官方引用支持六作者发表版的身份；这仍不是全文内容一致证明。已知发表版地址：[ASME PDF](https://asmedigitalcollection.asme.org/fluidsengineering/article-pdf/130/7/078001/5491455/078001_1.pdf)。访问标记为bronze但实际403，开放获取标签和当前访问成功是两个事实。

已存[ASME官网方法文稿PDF](../Methods_sources_data_audit_20261027/evidence/asme_gci_official_manuscript.pdf)本次重渲染并目视核对PDF第3、7页，即文稿第1、5页：题名页确为四作者；方法页含式4—7和细网格GCI式。预览：[题名页](evidence/asme_manuscript_title.png)、[方法页](evidence/asme_manuscript_gci.png)。这属于已有文稿复核，新增发表版全文数仍为0。

版本核对另记录一个具体符号问题：这份文稿式4定义外推量的上标为21，而式6印为12。此处只记录原文排印观察，**不判定或改写理论公式**；后续应核发表版相应位置。本轮不把文稿中的上标混用无说明地转写入正式稿，也不由此重算任何GCI。方法文稿不能替代项目自身网格和参考充分性证据。

第三方搜索片段提供了Bouzidi固定壁面段、Guo半步力及Celik发表版的线索，但未取得相应可验收原件，故没有用OCR片段认定逐式实现已经闭合。下载得到的HTML失败页面已保留HTML/response扩展名；没有以.pdf文件名冒充论文。

## 2. 历史构建：四组程序分别查到什么

依据[表S1](../SIM240_Supplementary_Methods_20261024/Table_S1_run_inventory.csv)的52项指定记录，四组二进制SHA256继续为22/22/6/2。它们不覆盖整个项目所有运行。逐运行分组、现存程序及中间对象文件、源码快照对照和只读命令输出见[build_evidence.json](build_evidence.json)；机器可读待补清单见[binary_group_contract.csv](binary_group_contract.csv)。

|历史程序哈希前缀|对应记录数|本轮发现的匹配程序|新补到的内部标记|完整构建来源|
|---|---:|---|---|---|
|285f67a0aa31…|22|在本轮指定目录/命名搜索中未找到|无|未闭合|
|57611b21584c…|22|当前D2程序，与22项manifest字节哈希一致|GCC (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0；Build ID 55fd43a722cc4bb9405909b696695015e2ee626b|只补内部编译器标记，仍缺当时完整源码/依赖和真实编译命令绑定|
|85cc9dee8db9…|6|当前D3程序，与6项manifest字节哈希一致|同一GCC版本标记；Build ID 361b79f62d6c91b4277a788a204ba05dccf33fa1|同上，未闭合|
|efd24c98efd8…|2|在本轮指定目录/命名搜索中未找到|无|未闭合|

原始输出在evidence/artifact_*_comment.txt、*_notes.txt、*_sections.txt；对应绝对路径和哈希在JSON中逐项列出。**这里的GCC字符串是程序自带的编译器标记，不是完整工具链证明，也不证明所有链接单元都由同一编译器构建。** Build ID用于识别链接产物，不是源码提交号，也不是构建时间。

本次还查到教师材料`SIM240_代码图片数据_20261022/_workspace/CASE/D_series/D2_groove_error_map/build/`中的D2程序：SHA256为`037a7220af61bfc6cdf5e7132a8d8c890c00dc807670cb3895277f2e07495a11`，Build ID为`cc10287c8976f1b9f26f8a9646da5189b03591bb`。它**不匹配指定52项中的任何一组**，没有把它认作22项或2项缺失历史程序的替代品。未执行该程序。

当前D2/D3各保留一份.o对象文件和.d依赖路径清单；两份当前.d各列2728个去重OpenLB路径（按本轮解析口径）。这些路径没有构建时文件内容哈希。现存相关ELF中没有.debug_info或.GCC.command.line节，未从中恢复出精确源码快照或完整编译参数。归档工作目录的.d还使用另一套路径，原文保留，没有据今天的文件内容追补历史依赖。

## 3. 源码快照与Git追溯的限度

两份D2/D3源码和两份Makefile，**4/4**满足：当前SHA256＝教师包文件SHA256＝共享清单声明SHA256，且当前Git blob ID＝共享副本固定提交`f11c0f20f6aaadf6920b95390855ec418cf8ae42`对应tree的blob ID。该判断读取固定Git对象路径，不把稀疏检出未展开当作丢失。

这四条共享路径的可见Git历史指向`076bf7001ab9aeab7508a5a59c43a3a0f907718a`，提交日期2026-10-23。主项目Git对D2/D3目标路径的ls-files/log --all未返回跟踪文件或历史条目；这只说明所查主仓库路径的可见历史不能补这条链，不能据此断言全机不存在备份。相关输出已存evidence/main_*、share_history_*和share_blob_*。

因此可确认“当前保存源码及指定共享快照一致”，不能确认“52项历史运行均由这份源码编译”。当前Makefile的参数和硬编码`5953d8a-dirty`沿用上轮已知事实；当前OpenLB HEAD再读仍为`882924a9cfc8dcdf82909e39530789cb6f5ebcc4`，没有将它写回历史manifest。

搜索范围明确限定为：`/home/dell/yuanyuanxu`下指定D2/D3名称文件（包含被Git忽略的build目录）、项目报告中相关构建/源码记录、现有教师包/工作副本、主仓库及独立共享副本目标路径历史；另列出Documents/文档/Downloads/下载下PDF/压缩包名称候选。不是全磁盘、所有未命名ELF或所有聊天会话的取证。本轮仍未找到可与四组程序绑定的完整历史编译档案。

## 4. 关闭缺口所需的最少材料

[MINIMUM_EVIDENCE_CONTRACT.md](MINIMUM_EVIDENCE_CONTRACT.md)逐项列明接收物、核验方法、可关闭的具体主张和停止条件。该文件仅约束资料核对，不授权计算。

- [8]/[9]：各一份合法完整原文或明确标注的作者版本；记录来源、版本、页数、文件SHA256，目视核对指定方法页，再与保存实现的符号、力和时间层约定对照。
- [10]：发表版四页原件，或能逐页支持同版对应的可靠档案；核对作者/文章号、步骤3—5和相关公式、迭代误差说明，并明确四作者文稿与发表版的差异。
- 四组历史程序：每组至少一套与记录程序哈希有直接关联的构建材料，包含精确应用源码/修改、OpenLB与链接依赖内容、编译器/链接器及实际编译链接参数。已有程序哈希和GCC标记可以复用，不能用当前快照填补未知环节。

如历史档案不可恢复，就明确保留来源限制；将来另版构建只能建立新的可复现基线，不能被记作恢复了旧运行来源。是否新建基线、编译或计算，均不在本轮执行范围。未向作者或其他人发送索取信息，未替作者决定公开访问/数据安排。

## 5. 验证与项目状态

[verification.json](verification.json)的15项范围检查通过，534份去重选定既有输入字节保持；覆盖本轮资料记录、4/4固定源码对象对应、28项程序哈希绑定及另外24项缺口保留。这不是数值或物理验证。首次检查在写出本证书前检查了指向证书自身的链接，误报尚未生成的verification.json；修正检查次序口径，初次结果保留[verification_initial.json](verification_initial.json)。初次网络/解析失败也在retrieval_ledger中保留：HUST连接失败后初次合并摘要脚本因不存在的响应文件报FileNotFoundError；KFUPM响应已成功保存，最终解析独立处理该现存文件。没有把工具失败当作论文或算例失败。

本轮正文和方法补充均未改；状态和交接只替换顶部当前接续段，before/保留修改前入口。无新run_id；旧N8仍`D4_N8_diag_v3_1_20261026_v1`，仅ONE_N8_DIAGNOSTIC_ACCEPTED；NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、reference_qualified=false、strict_error_bound_established=false、submission_ready=false，预测HOLD。没有编译、求解、真实N8提取、拟合、重新评分、下一项或Gate推进、Git提交推送。

下一条具体动作是经合法访问渠道取得[8]/[9]原文和[10]发表版，并按合同核对；历史构建优先寻找22项285f…和2项efd…对应的原程序/当时构建包。若材料不可得，保留本报告明确的可证范围，不宣布“来源已经补齐”。常规资料核验使用GPT-6.1 Sol｜High；涉及假设改变、理论实质推广或严格误差界时再使用GPT-6 Astra｜High复核。

技能方法来源：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://arxiv.org/abs/2609.00065)。本轮已重新获取公开记录，五作者，无期刊/发表DOI字段；仅作为本报告检索方法来源，不加入CFD论文书目。
