# P8 Bouzidi 原文取得状态与当前边界实现定位

日期：2026-10-27。用户范围：取得真正的 Bouzidi 原文后，按既有合同核对边界插值分支与当前实现；保持新增计算关闭。使用 paper-lookup、PDF、scientific-writing 技能。本文为代理执行的本地资料核对记录，待作者审阅，不是作者最终理论审定。

**本轮结论：未取得满足合同的完整原文，P8 保持 OPEN。当前源码位置和待核项目已整理，但原文—实现对应尚不能关闭。** 原页、式号与实际版本均保留为空，不根据第三方 OCR 或常见公式补造。

## 1 适用合同与接收状态

沿用[最小证据合同](../Primary_text_build_evidence_20261027/MINIMUM_EVIDENCE_CONTRACT.md)的 P8，不改变接收条件。目标文献是 M. Bouzidi、M. Firdaouss、P. Lallemand，*Momentum transfer of a Boltzmann-lattice fluid with boundaries*，*Physics of Fluids* 13(11)，3452–3459，2001，[DOI:10.1063/1.1399290](https://doi.org/10.1063/1.1399290)。作者实验室的[出版清单](https://www.lmssc.cnam.fr/en/publications?page=8)亦列出该身份，但只链接 DOI，没有在该条提供全文附件。

最低接收物仍是连续八页完整原文；如果取得作者稿，必须另记版本。收到后记录本地路径、来源、大小、SHA256、页数，目视身份页、固定壁面公式所在页及尾页，再按原页/式号核对。当前 `accepted_pdf_path/sha256/bytes/pages/version` 均为 null，实读原页为空，见 [contract_receipt.json](contract_receipt.json)。本轮没有可供 PDF 渲染验收的合格 P8 文件。

## 2 本轮取得尝试及其限度

四个直接请求的原始响应、响应头和访问时间保存于 `evidence/`，请求参数、状态及内容哈希见 [public_fetch_log.json](public_fetch_log.json)。

|渠道|本轮实际返回|能支持什么|
|---|---|---|
|Crossref 已保存的出版社 PDF 链接：`https://pubs.aip.org/aip/pof/article-pdf/13/11/3452/19042466/3452_1_online.pdf`|curl 退出 0，HTTP 403，`text/html`，5,563 字节，文件不以 `%PDF-` 开头|请求在传输层完成，但没有取得 PDF；不能记作原文收到|
|HAL 官方 API，题名字段精确短语检索，最多 10 条|HTTP 200，`response.numFound=0`|该指定查询未找到记录；不证明 HAL 或作者存档不存在任何版本|
|Semantic Scholar 按 DOI 查询|HTTP 200，题名/作者/2001 年对应，`isOpenAccess=false`，`openAccessPdf.url` 为空|此索引没有提供可下载开放原文；书目身份不等于全文|
|CNAM 实验室出版清单|HTTP 200，目标条目及 DOI 可定位|独立核身份；目标条目未给全文附件|

浏览工具访问同一 AIP PDF/落地页时还报告重定向至 `aipp.silverchair-cdn.com/article-minimal/453805` 后无法读取；CiNii 目标记录要求浏览器验证，另一个 ResearchGate 线索返回 429。它们均未提供本轮可验收的原文。没有绕过访问限制、代作者联系他人或购买材料。

本轮同时检索了完整题名、DOI、作者组合和 `3452_1_online.pdf` 文件名，并检查 HAL/作者机构等公开线索。搜索中出现的 Scribd 第三方 OCR、其他论文参考文献、学位论文及题名不符的文件均未作为 P8 原件接收。不同文章可能使用相同的首尾页文件名；不靠文件名认定身份。

本地检查覆盖 `/home/dell/下载` 的最新 PDF 列表，并在下载目录、项目 docs 与 `/home/dell/文档` 的 PDF 文件名中搜索 Bouzidi、Momentum、1399290、3452、Firdaouss、Lallemand 等线索，未定位到新原件。之前三篇的实际身份见[已接收记录](../Primary_text_received_20261027/REPORT.md)。本轮没有重新全文扫描所有旧 PDF，也未全机检索，不能写成“本机没有此文”。

## 3 已定位的当前实现事实

本节只描述所查当前 D2 应用源码及 `/home/dell/openlb` 文件。当前 D2 Makefile 指向该 OpenLB 目录，采用 CPU SISD 配置；这不是历史可执行文件确实由这些内容构建的证明。八份源码/配置的完整 SHA、大小和带原行号的片段见 [current_implementation.json](current_implementation.json)。

|合同核对项|当前源码定位|本轮可以确认的范围|原文对应|
|---|---|---|---|
|q 定义及方向|OpenLB `src/boundary/setBouzidiBoundary.h:248–264`|从邻壁流体点向固体点求距离，以 `deltaR*norm(c)` 归一化；字段索引用相反方向存放，不能只按 setter 内局部 `iPop` 名字比较|待原文 q 定义、图及式号|
|较短壁距线性表达式|同文件 `62–69`|有效 q>0 时，q≤0.5 的系数为 `2q` 与 `1−2q`；输入位置为固体侧邻点的 i 分量、本点的 i 分量；写本点的反方向分量|待原文分支条件/分布函数含义|
|较长壁距线性表达式|同文件 `70–71`|q>0.5 的系数为 `1/(2q)` 与 `(2q−1)/(2q)`；第二输入为流体侧邻点的反方向分量|待原文分支条件/取值位置|
|处理时间层|同文件 `305–309`；`src/core/superLattice.hh:663–706`；`blockLattice.hh:316–341`|边界注册于 PostStream；主循环次序为碰撞、传播、PostStream。传播通过分布数组偏移实现；所查默认非反向传播，CPU SISD 的 rotate 实现在 `core/platform/cpu/sisd/column.h:193–204`|原文碰撞前/后记号与各取值时间层仍须逐项对应，未关闭|
|静止壁|D2 `src/d2_groove_error_map.cpp:651–661`；OpenLB 上述文件 `47–80`|材料 2、3 显式安装 `BouzidiPostProcessor`，所查路径为零壁速处理器，不是另一个带壁速修正的处理器|待原文固定边界部分|
|q=0.5|D2 `56,294–303`；OpenLB `68–71`|D2 只把距 0.5 不超过 1e−10 的值吸附为 0.5；有限输入下，将 0.5 代入两套系数，代数上均只留下固体侧邻点的 i 分量|原文端点归属及与其半链反弹描述的对应仍待核|

这里使用“本点/邻点分量”描述源码存储值，没有将它们直接命名为原文的碰撞后分布；两者的对应正是 P8 必须补齐的证据。有限输入下的系数代入是源码代数说明，没有运行数值夹具或求解器，不是精度、稳定性或严格误差界证明。

还需保留两个实现细节，避免后续审查因文字省略而误判：

- 处理器 `68–71` 使用两个布尔条件乘表达式后相加，并非两个短路 `if`。不能把“该项权重为零”写成 C++ 保证“不读取该项输入”。本轮未做运行时访问或异常值传播测试。
- setter `266–295` 对距离非法、求交失败或缺少另一流体邻点存在置 q=0.5 的回退路径；应用 `auditGeometryLinks` 在 q>0.5 时才统计另一流体邻点缺失。后续若判断具体运行的回退情况，必须查其几何/安装记录及适用分支，不能凭安装后 q=0.5 或注释单独认定“从未回退”。本轮不重建几何，不重判历史回退记录。

这些是读代码所得的定位与限定，不构成已发现数值错误的裁定，不改源码，也不要求新增计算。

## 4 仍需补齐的唯一 P8 接收物与接续动作

当前阻塞是这篇 DOI 对应的完整原文文件。可由作者通过出版社/学校图书馆取得，放在 `/home/dell/下载` 或提供实际本地路径；不需要重新取得已收到的 Guo/Celik，也不能用 Dewangan–Datta 2020 年文章替代。

收到后按以下顺序继续，只做资料和源码核对：

1. 核八页连续性、题名/作者/DOI/年卷期及版本，记录来源与文件哈希；渲染并目视指定页。
2. 给本报告六项补原页、式号、符号方向及时间层映射；明确 q=0.5 端点处理是否代数一致。
3. 区分“原文方法—所查当前源码对应”与“历史构建绑定/项目数值精度”。只在证据齐全后关闭前者。若出现需裁决的实质矛盾、假设改变、理论推广或严格误差界审定，再用 GPT-6 Astra｜High 复核。

本轮未进行理论最终冻结，也没有触发上述 Astra 审定。P9/P10 已关闭的指定范围沿用原接收报告，不在本轮重新全量验收。正文[6]的 2018 年原文与四组完整历史构建继续 OPEN。

## 5 文件维护和权限

本轮只新增本目录的取得证据、源码定位、接收状态与报告，并维护两份项目状态/交接。正式稿、补充材料、模型、源码、合同、冻结协议与历史结果不改。修改前状态快照位于 `before/`，差异见 `state_changes.diff`；75 份选定保护文件的本轮前后哈希检查见 [verification.json](verification.json)。该清单包含所查源码、当前正文/补充材料和指定旧证据，不代表对整个工作区或全部历史结果做了重验。

没有编译、PDE 求解、OpenLB 预检运行、真实 N8 提取、拟合、第二项、Git 提交或推送，无新 run_id。旧 N8 为 `D4_N8_diag_v3_1_20261026_v1`；其 `NUMERICAL_GATE=NOT_EVALUATED`、`RESULT_PASS=false`、`geometry_PASS=null` 保持，项目 `reference_qualified=false`、`strict_error_bound_established=false`、`submission_ready=false`、预测 HOLD。历史 FAIL 保持，无运行命令或新增运行授权。

技能流程来源仅用于资料组织，不作为 CFD 方法论据：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065v2](https://arxiv.org/abs/2609.00065v2)，本轮在线核作者/版本。

最终16项资料/完整性检查通过，75份选定保护输入无变化，6条本地报告链接可解析。首次检查时 verification.json 自身尚未落盘，导致唯一自链接检查失败；原记录保留为 verification_initial.json，文件落盘后已补查通过。该过程不涉及原始科学结果或求解。
