# EJMB 五项投稿材料：核查与本地候选（2026-10-19）

状态：submission_ready=false。范围：回应用户指出的五项投稿缺口；核对现有中英文整合工作稿、现有作者指南摘录和出版商现行政策。本轮无新增计算或数值验证，无新 OpenLB run_id；未改正文、源码、冻结协议或原始结果，未上传、发布数据或投稿。

## 1. 证据边界与需要订正的措辞

- 当前英文整合稿第7行明确把利益冲突、数据可用性及 AI 声明列为待补；中英文稿未检出正式 Highlights、Keywords 或上述声明章节。该结论限于这两份稿件和本次针对性文件查找，不证明所有设备或账号从未准备材料。
- EJMB 专属要求沿用 `../EJMB投稿准备_技能清单与官方要求_20261019.md` 的既有摘录：Highlights 初投必需、3–5条且每条≤85字符含空格；关键词1–7个；数据 Option C；声明工具生成 Word；AI声明置于参考文献前。本轮直接访问该刊指南返回403，没有独立重取完整期刊原文；不能把既有摘录说成本轮重新逐项验证的原文。
- Elsevier 通用 Highlights 页面本轮可读，明确3–5条及85字符，并称通常最终文件阶段提交。此与既有 EJMB 摘录的初投时点不同，应按期刊专属指南准备，投稿前再确认；两者均不足以证明“缺少一项必然被学术拒稿”。
- Option C 不是无例外公开：要求存储数据并引用、链接；确实无法共享时须说明原因。不应将普通“可向作者索取”套话当作已经满足本稿要求，也不能编造保密理由。
- DOI不是这段Option C文字额外指定的唯一标识形式，但持久标识与可访问仓库记录有利于可靠引用。Zenodo支持预留DOI；预留不等于已发布、可访问或数据已经验收。
- “所有数据只在本地”未进行外部账号全量核查。本轮只能确认稿件未给出公开数据仓库链接或DOI。

## 2. 已准备的候选文字

`highlights_draft.txt`：4条英语候选；`verification.json`逐条记录含空格字符数，均≤85。主张对应当前英文稿摘要、引言与结论；保持“采样范围”“事后评价”“双网格限制”。本轮只核对已有文字支撑，未重新验收原始数值，待作者批准并转为投稿要求的可编辑文件。通用指南要求Word，当前txt不是最终上传件。

`keywords_draft.txt`：6个关键词候选：Confined flow; Rectangular grooves; Anisotropic transport; Lattice Boltzmann method; Lubrication approximation; Closure error。待与最终标题和摘要统一，不提前声称被期刊接受。

数据声明仅在实际发布、核对内容和访问后才能使用以下句型，方括号必须替换；现在不得粘贴为已完成声明：

> The data and analysis scripts supporting the findings of this study are available in [REPOSITORY] at [PUBLISHED DATASET DOI OR PERSISTENT URL].

需按实际覆盖范围补充公开内容与真实限制，并在正文及参考文献中加入完整数据集引用。仓库记录的作者、题名、年份、版本、持久标识均待落实。

AI声明建议章节名：Declaration of generative AI and AI-assisted technologies in the manuscript preparation process。候选内容如下；方括号及人工核实状态未落实前不进入终稿：

> During manuscript preparation, the authors used [VERIFIED TOOL AND SERVICE NAMES] to assist with drafting, text organization, language revision, and consistency checks. [AFTER COMPLETION OF HUMAN REVIEW: describe the review and verification actually performed and confirm the authors' responsibility for the published content.]

这不是可直接提交的声明。工具清单、实际用途和人工审查仍须作者核实。若AI参与求解器或分析脚本、数据处理、模型开发，应依现行政策另在Methods描述具体环节，不能只写“润色”。现有报告关于“图件修复”的笼统描述不足以确认是脚本排版、数据处理还是生成图像，本轮不作认定。

利益冲突：状态待全体作者提供真实信息。不得代填“无利益冲突”。通讯作者汇总后在Elsevier官方工具填写，按本刊指南取得并上传所需Word文件；本轮未登录、发送验证码、填写或提交工具。

## 3. 数据工作首先做什么

目标是让他人能从公开材料追到论文图表及其依据。以下是本稿的准备建议，不声称期刊逐项强制这些文件：

1. 按最终图表和主张列清单：图表号→处理脚本→输入CSV/result.txt→run_id/配置→来源与哈希。图9/10的数据链仍待核，应先厘清再冻结公开版本。
2. 保留所引用运行的原始结果、关键诊断、完整日志、独立退出码、配置及来源记录；历史FAIL若支撑正文或限制说明，也要能追溯。不能只上传通过的汇总曲线。
3. 收录表格数据、绘图与误差计算脚本、采用的V2公式/参数与适用范围、环境依赖和读取说明。按需提供支撑流场图及积分分析的场文件；是否需要全部时间序列应由复核需要决定，不直接把整个工作仓库上传。
4. 解决现存历史构建来源缺口，无法恢复的条目标明“来源绑定未完全核实”；不能为了发布补造版本或把当前源码当历史运行源码。
5. 整理README和变量表：K为深度积分输运系数、单位m³；K∥沿y、K⊥沿x；m²渗透率换算须说明Href；单位、几何、网格、黏度批次、诊断门槛和已知限制应足以理解数据。
6. 核准作者/单位、公开权利、许可证及第三方代码处理范围后，冻结本地清单并检查哈希；再创建仓库记录、填元数据、上传和发布。发布后实际打开落地页，检查数据下载、版本及DOI解析，再写最终数据声明与文献引用。

当前仅形成准备说明；没有复制、压缩或验收上述数据集，没有登录仓库或预留DOI。对外公开的最后一步需要作者确认具体公开包及元数据。

## 4. 本轮产物与接续

新建本目录READINESS_NOTE.md、highlights_draft.txt、keywords_draft.txt、verification.json。验证为字符计数、关键词数量、原稿哈希保护与针对性文字查找，不是完整投稿预审。

同步 `../SIM240_AI_CONTEXT.md` 和 `../AI_HANDOFF_20261015.md`。下一动作：以最终图表为索引建立数据公开候选清单并核图9/10；作者核实全部AI用途及利益冲突。无长计算、上传或投稿授权。

## 5. 本轮访问的官方依据

- [EJMB Guide for Authors](https://www.sciencedirect.com/journal/european-journal-of-mechanics-b-fluids/publish/guide-for-authors)：本轮403；期刊专属要求来自上述本地既有摘录，待重新取得原文快照。
- [Elsevier Highlights](https://www.elsevier.com/researcher/author/tools-and-resources/highlights)：本轮可读；格式及通用提交时点。
- [Elsevier Research Data Guidelines](https://www.elsevier.com/researcher/author/tools-and-resources/research-data/data-guidelines)：本轮检索到官方Option C完整条目，包含不能共享时说明原因。
- [Elsevier Generative AI Policies](https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals)：本轮可读；工具名称、用途及人工监督的披露；研究过程用途在Methods说明。
- [Elsevier Declaration Tool](https://declarations.elsevier.com/)及[官方利益冲突说明](https://www.elsevier.support/publishing/answer/what-are-conflict-of-interest-statements-funding-source-declarations-author-agreementsdeclarations-and-permission-notes)：本轮检索核对工具用途，不代替本刊Word要求原文核对。
- [Zenodo预留DOI说明](https://help.zenodo.org/docs/deposit/describe-records/reserve-doi/)：本轮可读；可预留，正式发布时注册。
