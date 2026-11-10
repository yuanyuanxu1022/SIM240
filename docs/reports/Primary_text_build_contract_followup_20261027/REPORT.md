# 指定下载目录与历史操作档案的合同接收核对

2026-10-27；承接[最小证据合同v1](../Primary_text_build_evidence_20261027/MINIMUM_EVIDENCE_CONTRACT.md)。用户要求取得缺失原文和对应构建档案后按合同核对，并提供本机路径`/home/dell/下载`。本轮按该路径检查，不启动计算。涉及假设改变、理论实质推广或严格误差界再使用GPT-6 Astra｜High复核的既有要求保持；本轮没有进入这些变更或审定。

**接收核对结果：指定目录内未找到P8、P9、P10的完整原文，也未找到对应历史构建包。** 查到的题名/DOI命中均为其他文献的参考文献条目；不能将它们记为原文已取得。历史操作记录提供了早期读取/检查痕迹，仍未补成完整构建绑定。因此本轮没有可继续逐式核对的新指定原件；没有把“检查完成”写成“证据已经闭合”。

## 1. 用户指定目录：22份PDF实际检查

本轮递归列出该目录的22份PDF，对每份记录完整路径、大小、SHA256、pdfinfo，抽取前两页识别题名，另对全部可抽取正文按指定题名/DOI检索。22/22文本提取退出0。原始逐文件资料：[downloads_pdf_screening.json](evidence/downloads_pdf_screening.json)；全篇命中页及上下文：[downloads_fulltext_matches.json](evidence/downloads_fulltext_matches.json)。这属于指定目录检查，不代表所有硬盘或所有扫描PDF的穷尽证明。

|合同项|实际找到的位置|目视核对结果|接收状态|
|---|---|---|---|
|P8 Bouzidi，10.1063/1.1399290|OpenLB论文PDF第28页，印刷285页；OpenLB 1.5手册PDF/印刷第174页|两处均为参考文献，不含该论文完整方法页|原件未收到；指定边界公式核对未执行|
|P9 Guo，10.1103/PhysRevE.65.046308|OpenLB论文第28页；OpenLB 1.5手册第175页；微混合预印本第23—24页；JTICE论文第11页|均为参考文献或其DOI续行，共6个不同PDF页面中的7条P8/P9目标命中，逐页渲染目视检查|原件未收到；原版力项/速度定义核对未执行|
|P10 Celik，10.1115/1.2960953|22份PDF未检到指定题名或DOI全文命中|未发现期刊发表版；旧ASME四作者文稿仍是另存的既有材料|发表版未收到；版本逐页对应未执行|

六页目视证据： [OpenLB第28页](evidence/openlb_refs_p28.png)、[JTICE第11页](evidence/jtice_refs_p11.png)、[微混合第23页](evidence/micromix_refs_p23.png)、[第24页](evidence/micromix_refs_p24.png)、[手册第174页](evidence/guide_refs_p174.png)、[第175页](evidence/guide_refs_p175.png)。

目录中确有《OpenLB—Open source lattice Boltzmann code》正式论文、OpenLB 1.5手册、Patir–Cheng原文和其他流动文献。这些文件各有用途，但不代替本合同指定的三份原件，也不能用手册Release 1.5推断项目历史二进制版本。本轮未改参考文献编号、正文或补充材料；未把局部来源识别扩写成对这些文献全部内容的终审。

目录内按构建/压缩包扩展名及D2/D3名称查找，并对研究文本作D2/D3及缺失程序哈希的定向检索，未发现对应构建包或命中研究文本，见[downloads_build_screening.json](evidence/downloads_build_screening.json)。未读取账号认证或恢复码文件；不把同目录中的其他文件带入本次研究档案。

## 2. 历史操作记录追溯

为寻找当时的实际编译输出，本轮定向检索Codex的2026-10-14—19日期目录，抽取涉及D2/D3源码/构建/哈希的工具调用及直接配对输出，得到**4份会话中的49条候选调用**。检索脚本[scan_history.py](scan_history.py)只读取历史文本，绝不重放命令。来源会话路径、记录行、时间及观测哈希见[history_search_scope.json](evidence/history_search_scope.json)，目标工具片段见[historical_tool_excerpts.json](evidence/historical_tool_excerpts.json)。该派生材料仅供本机来源审查；本轮没有发布或上传会话材料。

其中可核的事实是：2026-10-16已有D2源代码片段、运行脚本和285f…清单的读取记录；2026-10-19的旧审查已发现历史程序来源缺口，并有一次工具输出记录“170份项目ELF程序/共享文件检查，OLD_BINARY_MATCHES []”，随后列出5761…/85cc…清单。此处是**历史时点的检查记录**，不是本轮重新对170份文件做检查，也不证明今天全机不存在旧副本。先前工具筛选曾有转义问题，故不把较早筛选结果当作穷尽依据。

候选调用主要是读取源码、脚本、manifest和审查材料。没有找到能把当时完整应用源码、OpenLB/链接库内容、真实编译/链接命令和四组输出程序哈希直接串联的记录。旧助手的叙述不作为构建已证明的依据；源码局部摘录也不能恢复完整构建输入。

另对项目相关Claude会话目录定向检索D2/D3名称和两组缺失程序哈希，未命中。该结果仅表示指定关键词/可见JSONL记录未命中，不代表不存在其他工具或其他位置的档案。上轮已核的28项匹配程序、另外24项未匹配程序、四组完整构建均OPEN的结论保持。

## 3. 公开检索补查

本轮继续使用题名/DOI定向公开检索；新查LiterateLB页面只有Bouzidi的DOI书目链接，未发现原文附件。指定GitHub代码查询未找到可接收的P8/P10原文；P9查询出现无关文件，按题名/来源筛掉，没有下载或当作证据。Wayback对既知ASME发表版地址的可用性接口返回429，未继续密集请求，保留[evidence/ref10_wayback_429.html](evidence/ref10_wayback_429.html)的实际HTML响应，没有将.json文件名当作JSON成功。

这些新渠道没有提供可验收原件，新增指定全文为0。上轮已经保存的出版社403、APS连接失败和ASME四作者文稿/发表版边界继续有效；本轮未重复声称取得原件，也未绕过认证或向他人发送索取信息。精确查询记录见[public_lookup.json](public_lookup.json)。

## 4. 当前接收判定和下一具体动作

逐项状态见[contract_receipt.json](contract_receipt.json)。P8/P9仍是“身份已核、原件未收到、指定内容未核”；P10仍是“发表版书目身份已核、发表版原件未收到、与文稿逐页对应未核”。四组历史构建继续OPEN；没有改动合同或降低接收要求。

继续核对所需的最少材料已集中成[MISSING_ITEMS.md](MISSING_ITEMS.md)：三篇完整原件，以及与四组哈希相关的构建档案。若材料本来位于其他位置，沿用原合同只读接收即可；不得用另一次编译/运行补写旧历史。现有参考合格性、严格误差界与投稿状态不因文献目录检查而改变。

验证范围见[verification.json](verification.json)：12项范围检查通过，623份选定既有文件字节保持；包括指定PDF接收记录、六页视觉对应、旧资料保护、合同和正文保持以及状态/交接一致性，非数值验证。首次检查发现状态更新多保留了一段上一轮“当前入口”，已去掉该重复段并确认更早正文完全保持；初次结果保留[verification_initial.json](verification_initial.json)。本轮无新run_id、编译、求解、真实N8提取、拟合、重新评分、第二项或Git提交推送。旧N8仍`D4_N8_diag_v3_1_20261026_v1`、ONE_N8_DIAGNOSTIC_ACCEPTED；NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、reference_qualified=false、strict_error_bound_established=false、submission_ready=false，预测HOLD。

技能方法来源：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://arxiv.org/abs/2609.00065)。本轮重新获取公开记录，作为检索方法来源列入本报告，不加入CFD稿件参考文献。
