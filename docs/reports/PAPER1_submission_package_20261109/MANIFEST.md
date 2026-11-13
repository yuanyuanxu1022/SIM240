# 第一篇投稿件清单（MANIFEST）

> **这份文件解决一个具体风险**：截稿稿件的**文件名日期**与**内容同步日期**不一致（如中文稿文件名写 20261022，内容已改到 2026-11-10）。只按文件名判断新旧会取错版本，投稿打包或交给他人时会用旧稿。
>
> 本表把「文件 → 内容版本 → 指纹」三者绑定。**清单当前绑定更新：2026-11-13**（本表哈希对应此刻磁盘状态）。
>
> 规则：**任何交付件改动后，必须重算该行 SHA256 并更新本表**；否则本表失效，比没有清单更危险。

---

## 1 主交付件（投稿正文与补充材料）

| # | 文件 | 文件名日期 | 内容版本 | SHA256（前 16 位） | 字节 | 用途 |
|---|---|---|---|---|---|---|
| 1 | `docs/reports/SIM240_中文稿_导师审阅版_20261022.md` | 20261022 | **2026-11-13** | `c43356fef4ee7e93` | 81753 | 中文主稿（导师审阅与内部对照用；不作为投稿正文） |
| 2 | `docs/reports/SIM240_First_Paper_English_20261028.md` | 20261028 | **2026-11-13** | `6f049acce9a22637` | 90149 | **英文主稿（投稿正文基准）** |
| 3 | `docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md` | 20261024 | **2026-11-13** | `b966da7d78f28457` | 45545 | 补充材料（中文） |
| 4 | `docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md` | 20261028 | **2026-11-13** | `7b3d1434c8197847` | 55122 | **补充材料（英文，随投）** |
| 5 | `docs/reports/PAPER1_conclusions_current_20261109.md` | 20261109 | **2026-11-13** | `3068f222759f6c1c` | 17168 | 结论定稿（六条，**唯一结论口径来源**） |

**四个正文/补充文件的文件名日期均早于内容版本**：打包时以“内容版本”及SHA256绑定为准。

---

## 1.1 A范围基础下界定点合入（2026-11-09）

两份正文仅在附录E末尾增加E.1基础下界（新增式E7、E8），并在§5.1末加入一句回指。摘要、五条正文结论、原式E1—E6、科学参考文献及双语补充S1—S14保持；未增加正式图表号。修正版区间图作为独立追溯材料保留。第1、2行哈希与字节数已按本轮实际文件重绑定；完整SHA和合稿检查见 `docs/reports/PAPER1_lower_bound_merge_20261109/output_hashes.json`、`verification.json`。其他历史清单和旧审查哈希保留其快照身份，不据此声称当前文件未变。

本次合稿不改变数值参考资格、既有FAIL或投稿准备状态；不扩大机制或预测主张。独立六条结论文件未改，正文五条结论也未改；其既有组织差异不在本轮重排范围。

**1.1.1 复核后修正（2026-11-09 晚）**：独立复核发现两处新加文本自身的问题并已改：① 新段落百分比由一位小数改为两位（58.17 / 23.84 / 88.85 / 30.63），与表8表注“本表及正文的百分比统一保留两位小数”一致，并注明 88.85 / 30.63 与表8“原始平均绝对偏差”为同一统计量；② 附录E标题由“上界性质”改为“上下界性质”（英文 Upper- and lower-bound properties），使标题与新增E.1内容相符。既有数字、五条正文结论、式E1—E6、摘要与参考文献均未改动。本轮前一轮 SHA（`7ce3ac6b…` / `0554657c…`）保留为历史快照，不再代表当前文件。明细见 `docs/reports/PAPER1_lower_bound_fix_20261109/REPORT.md`。

**1.1.2 汇报 PPT 结论页 5→6 条（2026-11-09 晚）**：PPT 第 11 页原按正文五条结论排，与 `docs/reports/PAPER1_conclusions_current_20261109.md` 的六条不一致（缺“新增间隙与静态接入”）。已补为六条：新增第五条“新增间隙与静态接入”（h=100 nm 对照：原公式 +126.62%/+49.43%、V2 −2.03%/+4.39%、方向比 A −6.15%、静态接入后出口流量降 56.77%/30.14%，均按沿槽/横槽排序，数字全部取自中文稿 L410、L462 已写定值），原第五条“理论上界”并入第六条“理论上界与机制诊断”。卡片高度 1.06→0.855 in 以容纳六条，第 12 页边界页标题同步为“六条结论各自能说到哪一步”。稿件正文与独立结论文件**未改**（正文仍是五条，差异为既有组织差异）。检查：`check_lowerbound_pages.py` 23 项 0 失败，`check_overflow.py` / `check_overlap.py` 通过。明细见 `docs/reports/PPT_论文汇报_20261109/STORY.md`。

**1.1.3 结论定稿文件 §3.1 映射表更正（2026-11-10 上午）**：`docs/reports/PAPER1_conclusions_current_20261109.md` §3.1 的映射表最后一列仍写“汇报 PPT 第 **10** 页（五条）”，存在两处过时：① 页码错——PPT 结论页第 11 页（第 10 页是“问题③ 两个方向是否等幅”）；② 条数错——PPT 已于 11-09 补为六条，表中却仍写“五：无对应（PPT 缺）”“六：五（仅上界，S14 缺）”。本次改为“第 11 页（六条，2026-11-10 核对）”，六行逐条给出对应名称，并把“已知缺口”第 2 条标记为**已关闭**（保留删除线原文，不删记录），注明遗留不一致只剩第 1 条（稿件 §6 仍为五条，属正文重排范围）。**本次只改这一张映射表与其缺口说明，六条结论正文、任何数字、限定语均未动**；正文与补充材料均未改。文件 SHA 由 `91e6eba3e3809046`（13352 字节）变为 `20c9a839f549e224`（13779 字节），第 5 行已重绑定；旧哈希保留为历史快照，不再代表当前文件。另注：`docs/reports/PAPER1_consistency_audit_20261109/CONSISTENCY_AUDIT.md` 第 110 行同样提到“PPT 第 10 页五条”，但那是 11-09 的历史审计结论、当时成立，按历史记录原样保留，**不回改**。

---

## 1.2 纠错v3相关工作与引文编号合入（2026-11-10）

已按 `PAPER1_MF_fulltext_audit_20261110/CANDIDATE_*_v3.md` 同步两正文§1.2、§2.2及两补充S11。新增Ng[7]、Mohammadi–Floryan[8]、Stroock[9]；按实际首次出现顺序，原OpenLB[7]→[10]、Guo[9]→[11]、Bouzidi[8]→[12]、Celik[10]→[13]、Teyssèdre[11]→[14]。全文与补充回指按同一文献身份更新，未另增Tran。原上下界推导、公式/图表编号、摘要、五条正文结论及既有数字保持，结论中原科学引文如有仅随身份改号。没有重复理论复核或新增仿真。

第1—4行SHA及字节数已按本轮实际文件重绑定。当前完整SHA、改前快照、全局引用映射和检查回执见 `docs/reports/PAPER1_v3_literature_merge_20261110/REPORT.md`、`output_hashes.json`、`verification.json`。旧合稿/复核记录保留各自历史快照身份，不作为当前文件哈希；当前投稿资格与既有FAIL不因本轮文字工作改变。

---

## 1.3 成对宽度证据定点合入（2026-11-10）

按已审候选同步两正文§4.3、§5.1及两补充S14，新增补充图S1、表S10—S13与式(S14.3)—(S14.5)。原正文图1—4、表1—8、式1—8和附录E编号不变；科学文献[1]—[14]身份与编号不变。原18几何36条主统计、V2四参数与已知反例、摘要和结论保持。

第1—4行SHA与字节数按实际文件重绑定；新增共享CSV、编号映射和双语图件分别绑定于§2.1和§3.1。合稿记录按**实际落盘文件**指向 `docs/reports/PAPER1_width_evidence_merge_20261110/` 目录：完整SHA与字节数见 `output_hashes.json`（16 个输出件），候选采用审查见 `ADOPTION_REVIEW.md`，逐条可逆改动见 `edits.json`（27 条，含 before/after/reason）及同目录 6 个 `.diff`。旧候选和旧合稿哈希保留历史身份；本轮不重做上下界理论复核、求解、拟合或物理验收，不改变既有FAIL及投稿准备状态。

**§1.3 引用更正（2026-11-10 下午）**：上段原写"见 `PAPER1_width_evidence_merge_20261110/REPORT.md`、`output_hashes.json` 与 `verification.json`"，但该目录内**从未生成** `REPORT.md` 与 `verification.json`——属断链引用，与补充材料§3已披露的"所引用独立放行报告的路径缺口"同类。已改为指向真实存在的 `ADOPTION_REVIEW.md`、`output_hashes.json`、`edits.json` 与 6 个 `.diff`，并删去对不存在的"检查"文件的指称。**本次只改这一句引用与新增本条记录**：§1.3 合稿内容、新增编号、全部数字、四稿哈希与既有 FAIL 状态均未变。更正前本文件 SHA 为 `314c522dc98f62b7`（14576 字节），保留为历史快照，不再代表当前文件。

**§1.3 附注：英文页首日期与快照目录更正（2026-11-10 下午）**：第 2 行英文主稿的**页首注释**原写 "synchronized on 2026-11-09" 且指向旧目录 `PAPER1_mechanism_merge_20261109/`，与其正文实际内容不符——该稿§4.3末、§5.1与补充S14已含 11-10 合入的成对宽度证据（`A_LC=4.90822`、方向比高估 208.85%/33.58%、引 Figure S1 与 Table S10—S13）。本表第 2 行"内容版本"列自始即为 **2026-11-10**，故此为**页首注释滞后于正文**，非内容版本错误。已改为 "synchronized on 2026-11-10"、指向 `PAPER1_width_evidence_merge_20261110/`，并补述三处合入位置与新增编号。英文稿 SHA `454acc6217f3de21`（80672 字节）→ **`98172d18b0163080`（80980 字节）**，增量 308 字节恰为该段文字字节差，正文其余部分与全部数值未变。**本文件在追加本条附注之前**的 SHA 为 `8f153f2e6602a5d0`（15492 字节，字节数与改前相同，因第 2 行替换为等长字符串）；加入本条附注后本文件必然再次变化，**该值不得用于核对当前文件**——当前值以 `output_hashes.json` 第 6 条为准。`output_hashes.json` 第 2、6 条已同步重绑定，全库 16 条校验 0 不一致。

---

## 1.4 投稿稿派生目录（2026-11-10 新建）

**目录**：`docs/reports/PAPER1_submission_manuscript_20261110/`

**解决什么**：中文主稿参考文献后仍带 4 个内部附录（A 图件来源与编号映射、B 正文数字可追溯性、C 投稿前需补齐、D 版本与修订记录）。其中附录 C 是给作者看的待办清单、附录 A 还整段重抄了图 1—4 的图注（L567—573 与正文 L67/330/357/361 逐字相同），整份转 PDF 会出双份图注。这些内容留在母本里正确，但不能随稿投出。

**做法**：新增派生脚本 `build_submission.py`，只对母本做机械变换，母本仍是唯一编辑入口。

| 产物 | 行数 | 字节 | SHA256（前 16 位） | 来源母本 |
|---|---|---|---|---|
| `SIM240_submission_CN.md` | 673 | 73630 | `9471dfa7ace6ee07` | 第 1 行（`c43356fef4ee7e93`，81753 B） |
| `SIM240_submission_EN.md` | 663 | 88546 | `5653963b486a8ad3` | 第 2 行（`6f049acce9a22637`，90149 B） |

**中文稿改动**：删页首内部注（L3—L6）；删附录 A—D 共 74 行（原 L556—L629）；附录 C 里的数据/代码可用性段落（原 L620）提出升为独立小节 `## 数据与代码可用性`，置于结论与参考文献之间；删 §2.1 指向附录 B 的交叉引用；删附录 E 首段的内部复核路径与厂商模型名（原句含 `Appendix_E_final_review_20261028/` 与 "Astra 书面复核"）；4 处图路径与 16 处补充链接按新目录深度加前缀。

**英文稿改动**：删页首 "Author-review working manuscript…" 整段（L3—L4）；删 "and the source manuscript Appendix B"；小节标题改为 `Data and code availability`；删该节末两句作者待办；路径同上。英文稿本来没有附录 A—D。

**未做的两件，理由已记在目录内 `README.md`**：① 附录字母**仍为 E**，未改为 A——式 (E1)—(E8) 有 8 处正文回引、两补充材料各 1 处引用"附录E/Appendix E"、补充材料另有 25 处指向内部审计目录的相对链接，单改正文会造出新不一致；改字母应待补充材料打包时四份同时改。② 补充材料**未复制**到该目录，同上原因。

**校验**：生成后自动检查禁词（`docs/reports`、`PAPER1_`、`Astra`、`Codex`、`author-review`、`导师审阅`、`附录 B/C/D` 等）与相对链接可解析性，当前 0 命中、0 断链。`python3 build_submission.py --check` 可随时确认产物是否仍与母本一致。

**未改**：四份主交付件本体、任何数字/单位/结论、图表与式编号、V2 四参数、既有 FAIL、五条/六条结论组织差异（该组织差异已于同日 §1.5 关闭）。本轮无新求解、新拟合、新提交。

---

## 1.5 结论节五条改六条 + 补 4 处公式回引（2026-11-10 下午）

**起因**：全文终审（`docs/reports/PAPER1_final_review_20261110/REVIEW.md`）记录两项遗留：① 正文 §6 为五条，与 `PAPER1_conclusions_current_20261109.md` 的六条仅分段不同、数字不冲突；② 式（2）（5）（6）（8）有编号定义但正文从未回引。

**做法（甲案）**：§6 只搬段落、**不动任何数字**——原第一条（把"定位＋数据规模＋全部高估＋上界"压在一段）拆为两条（一 定位与数据规模、二 全部高估），原第五条"理论上界"的表述并入第六条"上界与机制诊断"。改后六条与独立结论文件逐条对应，也与汇报 PPT 第 11 页六条一致。中英文同步改，英文条目编号为 **1.**—**6.**。

**补引位置**：式（2）在 §2 计算三步处（"式（2）的计算分三步…"）、式（5）在 §5 线性张量关系处（"同一线性张量关系（式（5））"）、式（6）在 V2 回顾比较处、式（8）在 D 的单位说明处；英文对应 Eq. (2)(5)(6)(8)。现状：两稿式（1）—（8）全部在正文被回引，无"只定义不引用"的编号。

**校验**：中英 §6 数字逐项比对一致，差异仅为条目序号与英文把 "eight" 写成单词、少重复一次 46；派生件已重跑，`python3 build_submission.py --check` 报"一致、0 禁词、0 断链"。

**重绑定**：第 1 行中文稿 `331c60571f663c07`（74615 B）→ `8723fc9fca198b05`（75169 B，+554）；第 2 行英文稿 `98172d18b0163080`（80980 B）→ `5e301dc7d8fba745`（81801 B，+821）；第 5 行结论定稿 `20c9a839f549e224`（13779 B）→ `3b98002f1911a330`（15380 B，+1601，本轮 §3.1 映射表改为"六条→六条逐条对应"并关闭缺口第 1 条）；§1.4 派生件表两行同步改为 `e5136f7e7d9b6546`（67242 B，653 行）与 `ba2ef198e11867b0`（80588 B，643 行）。旧哈希保留为历史快照，不再代表当前文件；本文件自身当前 SHA 以 `output_hashes.json` 第 6 条为准（改本文件必然改变其哈希，故不在正文内写死）。

**未改**：任何数值、单位、图表与式编号、V2 四参数、附录 E 内容、两补充材料、既有 FAIL；未新求解、新拟合，不改变投稿准备状态。

---

## 1.6 V2来源与标定身份澄清（2026-11-10；**其中"建立"措辞已被 §1.7 收窄**）

按本轮授权定点同步两正文、两补充与结论定稿：V2由本研究建立并标定，因子自变量为d/w；标定采用h=50/75/125 nm与d=25/50/100 nm的9种几何，每方向9个5 nm导度结果，分别以最小化最大绝对相对残差拟合两个参数，共四个参数。主集为18种几何、36条主方向结果，不能写成36种几何或全部36条均进入拟合目标。

两正文§1.3明确建立与标定，§4.4补方法、标定集及回顾性身份；摘要、§1.2、新增间隙段与结论中“既定/公布/published”在涉及V2来源处改为本研究所建/固定系数。两补充S2及独立结论文件同口径同步。9种扩展几何在形式选择时已可见，仍不认证独立预测；未声称完全独立原创、理论推导出四参数或全球首创。导师或组内直接前身尚待作者补充，项目内记录不替代贡献者确认。

第1—5行及§1.4派生件表已按实际文件重绑；派生脚本重新生成并通过--check。证据入口：`docs/reports/PAPER1_V2_provenance_revision_20261110/REPORT.md`、`verification.json`、`edits.json`、逐稿diff与改前快照。原公式、V2四参数、既有结果数值、单位、显示公式、图表/参考文献编号和历史FAIL均保留；仅补显已有标定信息，不重新拟合/求解，不改Gate或submission_ready=false。当前完整指纹仍见`PAPER1_width_evidence_merge_20261110/output_hashes.json`；此前各节指纹保留历史快照身份。

---

## 1.7 V2 归属措辞由"建立"收窄为"标定"（2026-11-10 16:50，用户裁定）

**起因**：`PAPER1_V2_downloads_source_audit_20261110/REPORT.md`（下载目录 34 个 PDF／去重 30 份）核查结论：V2 四系数由本项目标定有记录支持，**但函数形式的直接前身未确认**；Jain 2017 式(11)—(13) 是被比较原模型的文献背景（不是 V2 出处），Dewangan–Datta 2020 §4.3 的 Padé 分母型改写属**表达思路前例**，相似但不能认定为借用。故 §1.6 的"建立并标定"断言超出证据（"四系数取自自有数据"推不出"函数形式原创"）。

**改了什么（只改归属措辞与一处引用，零数字）**：

| 位置 | 改前 | 改后 |
|---|---|---|
| 中文摘要 | 本研究**建立并标定**的经验修正（V2）的回顾性评价 | 本研究**标定**的经验修正（V2）在回顾性评价中 |
| 中文 §1.3 | 本研究**建立并标定**一个…V2 | 本研究**采用**…V2，并用 9 种标定几何**标定**其四个系数 |
| 中文 §2.3 | 只引 [4] | 增补"这一组合在纳米压印降阶模型中已有使用 **[1]**"（式(3) 与 Jain 式(11)—(13) 同构造） |
| 中文 §4.4 首句 | 由本研究…**建立并标定** | 四个系数由本研究**标定**，标定集为 9 种几何 |
| 中文 §4.4 次句 | V2 是本研究**建立并标定**的经验关系 | V2 **形式与四个系数在本研究中保持固定** |
| 英文摘要 | correction **developed and calibrated** in this study | correction **calibrated here on nine geometries** |
| 英文 §1.3 | correction **developed** in this study | correction **calibrated** in this study |
| 英文 §2.3 | 只引 [4] | 增补 "already used in reduced-order nanoimprint models **[1]**" |
| 英文 §4.4 两处 | was **developed and calibrated** in this study | four coefficients **were calibrated** in this study／form and coefficients **are held fixed** |
| 英文结论 1 | V2 **developed** in this study | V2 **calibrated** in this study |

**保留不动**：9 几何标定集、每方向 9 个 5 nm 结果、两参数×两方向=四参数、minimax 目标、"标定集含于主比较集"、"回顾性比较，不构成独立预测精度证明"；V2 四参数数值、全部结果数值、单位、图表与式编号、参考文献编号、既有 FAIL。

**重绑**：第 1 行 `7035a548…`/75826 → **`c065a96afb0195bc`/76008**；第 2 行 `9d0e8585…`/82728 → **`2a5c6d8ad119e92f`/82935**；§1.4 派生件 `c281d3a8…`/67899 → **`40b78c4f0c23b5b0`/68081**、`cf2508c2…`/81515 → **`df6dd0444d3cb885`/81722**（`--check` 报一致、0 禁词、0 断链）；`output_hashes.json` 18 条 0 不一致。**两补充材料与结论定稿本次未改**——其现有措辞为"固定V2／固定系数"，本就不含"建立"断言。

**仍开放**：函数形式的直接前身。若作者日后能指认具体文献段落，按"直接采用／改造／一般背景"分别处理引用，届时另记一节。

**§1.7.1 残留动词原形补正（2026-11-10 17:10）**：§1.7 的检索只覆盖了 `developed and calibrated` / `developed in this study` / `建立并标定` 等**过去式与完成式**，漏掉英文 §1.3 贡献句里的**动词原形** `and develop and calibrate a two-direction multiplicative empirical correction, V2`（第 45 行）。该句与中文 §1.3"本研究**采用**…并用 9 种标定几何**标定**其四个系数"口径不一致，仍属"建立"断言。本次改为 `and calibrate a two-direction multiplicative empirical correction, V2, whose factors depend on $d/w$, on nine geometries`（尾部补 "on nine geometries"，与摘要、§4.4 的标定集表述对齐）。**只改这一句，零数字、零编号、零结论变动**。英文稿 `2a5c6d8ad119e92f`/82935 → **`2361c9d6c4ecf326`/82943**（+8 B，恰为 `develop and ` 删除与 `, on nine geometries` 增补的净差）；§1.4 英文派生件 `df6dd0444d3cb885`/81722 → **`8dc1f533cd9f7934`/81730**，中文派生件 `40b78c4f0c23b5b0`/68081 不变（中文母本未动）。`--check` 报一致、0 禁词、0 断链。复核方法已补记：**查过度归属必须同时搜原形 `develop`、名词 `development`、以及 `propose`**，不能只搜过去式。

---

## 1.8 两处证据边界措辞同步（2026-11-10）

按用户本轮授权，仅在中英文正文各改两处：① 当前§3.1诊断记录段（中文第259行，用户所称“§4.3”实际位于§3.1）补明“这些检查的通过不构成导度相对于连续解的误差界”；英文对应“Passing these checks does not establish an error bound for conductance relative to the continuous solution.”。② §4.2标题由“全部36个样点”改为“全部36条5 nm主方向结果”，英文对应“all 36 principal-direction results at 5 nm”。没有改写为所有诊断均已通过，也未改变历史FAIL或收敛门槛。

两投稿派生件已从母本重新生成；第1节两正文行与§1.4派生件行的SHA和字节同时更新。两补充、结论、科学图表/公式/引文/参数与数值结果不变；标题只补显既有5 nm参考身份，不改变36条分母。完整改前快照、逐稿diff、精确编辑记录与校验见`docs/reports/PAPER1_two_scope_wording_fixes_20261110/`。authority及派生README当前指纹一并同步；README原有字节/版本滞后随本轮重生成纠正。此前终审第④项“标题未点明5 nm”已关闭，历史快照正文保留。

无新run_id、编译/求解/拟合/原场处理、Gate放行、Git提交推送、上传或投稿。reference_qualified=false、strict_error_bound_established=false、submission_ready=false与既有FAIL保持。本文件自身指纹以`PAPER1_width_evidence_merge_20261110/output_hashes.json`对应条目为准，不在本文件中自引用当前哈希。

---

## 1.9 中文残留“所建”归属措辞三处补正（2026-11-10）

用户本轮明确授权将中文母稿§1.2 L43、§4.4新增间隙段L426、§6结论一L508的“本研究所建经验修正”全部改为“本研究标定的经验修正”，与摘要及系数标定段一致。此前检索遗漏了“所建”这一同义表达，本轮只作三次精确替换；函数形式直接前身仍未确认，不认领原创。每处增加一个汉字，中文母稿及其派生件各净增9字节；所有数字、参数、公式、图表/引文编号、回顾性限定及历史FAIL保留。

两投稿派生件按原脚本重生成，英文产物与母稿均不变。当前中文母稿与派生件的SHA/字节已同步到本表、authority、README及18项output_hashes；改前快照、三条精确编辑、diff与验证见`docs/reports/PAPER1_V2_suojian_fix_20261110/`。PPT及HTML不属于本轮改动/复验范围，用户报告的实际页码2、9、11（第11页含两处）仅记作接续信息。本轮无新增计算或数值验证、无run_id/编译/求解/拟合/原场处理/新Gate/提交推送/上传/投稿，既有证据边界与submission_ready=false保持。

---

## 2 数据证据件（正文与补充材料引用，不进投稿包但须可追溯）

| # | 文件 | SHA256（前 16 位） | 字节 | 用途 |
|---|---|---|---|---|
| 6 | `docs/reports/SIM240_manuscript_revision_20261018/map36_evidence.csv` | `9fe4324f44dce2b9` | 9416 | 36 条主结果原始 K/ε/V2 残差 + result_path + sha256 |
| 7 | `docs/reports/PAPER1_闭环方案_20261105/bound_check_44_points.csv` | `3f3dcf8f196c5f90` | 8673 | 边界审计点集；h=100/d=100 两条在第 46–47 行 |
| 8 | `docs/reports/SIM240_Supplementary_Methods_20261024/Table_S7_thin_gap_correction.csv` | `38aaf8b3b7a99823` | 231 | 补充表 S7（薄隙 5/2.5 nm 两档偏差并列） |

同目录既有S表：S1运行清单、S2加密、S3周期检查、S4网格归档、S5条件GCI、S6新增间隙构建对照、S8控制证据、S9机制诊断。新增表S10—S13及编号映射见下表；改动时须同步核对。

---

## 2.1 成对宽度共享数据与编号映射（2026-11-10）

| # | 文件 | SHA256（前16位） | 字节 | 用途 |
|---|---|---|---|---|
| 9 | `docs/reports/SIM240_Supplementary_Methods_20261024/Table_S10_paired_width_conductance.csv` | `2d551a7b28ab00e6` | 2876 | 表S10：两网格导度倍率与方向比及run_id来源 |
| 10 | `docs/reports/SIM240_Supplementary_Methods_20261024/Table_S11_common_multiplier.csv` | `fa92c4c71aa8a6ad` | 1133 | 表S11：共同倍率辅助诊断 |
| 11 | `docs/reports/SIM240_Supplementary_Methods_20261024/Table_S12_gradient_excess.csv` | `990fe57864b17523` | 1247 | 表S12：2.5nm主模板绝对梯度差额 |
| 12 | `docs/reports/SIM240_Supplementary_Methods_20261024/Table_S13_gradient_residuals.csv` | `e9877c1dfeeaef1c` | 4343 | 表S13：两网格/两模板梯度差额与带符号余额 |
| 13 | `docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENT_NUMBER_MAP.csv` | `fe4e075f09f1cf72` | 1344 | S1—S14正文/补充交叉索引，S14含图S1及表S9—S13 |

两种语言使用同一组CSV；它们来自既有开发记录与已审离线诊断，不是新增运行。

---

## 3 图件（原4组及补充图S1）

| 图 | PDF SHA256 | 对应正文 |
|---|---|---|
| Figure_G2_K_convergence | `387b99229fff360f` | 网格收敛 |
| Figure_G2_anisotropy | `8e8626fd9ea15224` | 各向异性比 |
| Figure_G2_resistance | `569b2dc8be360e7b` | 水力阻力（导度倒数） |
| Figure_G2_GCI | `399be2d7535ec453` | 细网格 GCI 估计 |

路径：`paper_figures/figures/`；图注：`paper_figures/figure_captions.md`。投稿前需按期刊要求重命名为 Fig1–Fig4，并同步图注编号。

---

## 3.1 补充图S1双语资产（2026-11-10）

| 文件 | SHA256（前16位） | 字节 |
|---|---|---|
| `docs/reports/SIM240_Supplementary_Methods_20261024/figures/Figure_S1_paired_widths_CN.png` | `287525cfb1278b6b` | 282759 |
| `docs/reports/SIM240_Supplementary_Methods_20261024/figures/Figure_S1_paired_widths_CN.pdf` | `44f5be0aadc1c17e` | 77406 |
| `docs/reports/SIM240_Supplementary_Methods_20261024/figures/Figure_S1_paired_widths_CN.svg` | `1bf80d382f3afe7b` | 287027 |
| `docs/reports/SIM240_Supplementary_Methods_20261024/figures/Figure_S1_paired_widths_EN.png` | `5f2404b5e59fb09c` | 299282 |
| `docs/reports/SIM240_Supplementary_Methods_20261024/figures/Figure_S1_paired_widths_EN.pdf` | `71d8915d5b4f31d1` | 57948 |
| `docs/reports/SIM240_Supplementary_Methods_20261024/figures/Figure_S1_paired_widths_EN.svg` | `029e2d006fad3164` | 269953 |

补充文稿中分别引用对应语言PNG，PDF/SVG供导出；图注与正式编号在双语S14。图件与已审候选逐字节相同，未重新处理原场。

---

## 4 非投稿件（存在但不随投，勿混入投稿包）

| 文件 | 说明 |
|---|---|
| `docs/reports/PPT_论文汇报_20261109/论文汇报.pptx` | 导师汇报用，**14 页**（`e07f421a21b26e22`，236430 字节；2026-11-09 晚随附录 E.1 增页重生成，随后结论页由 5 条补为 6 条再生成；中间版 `cc3c2be9e1c7b606`、旧 13 页版 `286ebccae99e7db7` 均退为历史快照）；数字口径与稿件一致，但**不是投稿件** |
| `docs/reports/PAPER1_consistency_audit_20261109/CONSISTENCY_AUDIT.md` | 发布前一致性核查记录（含 P1/P2/P3 判定与 P2 执行结果 §7） |
| `docs/reports/PAPER1_conclusions_current_20261108.md` | 旧五条版结论，**已被 20261109 版取代，勿引用**（文件头有横幅） |
| `docs/reports/SIM240_EJMB_*.md`、`SIM240_PoF定向写作工作稿_20261019.md` | 早期整合稿/定向稿，仅存历史 |

### 4.1 等效缝高派生件（2026-11-09 新增，不进正文）

| 文件 | SHA256（前 16 位） | 说明 |
|---|---|---|
| `docs/reports/PAPER1_equivalent_gap_20261109/EQUIVALENT_GAP_GUIDE.md` | `d91a29228ce24f99` | 主文档：定义、38 条全表、三条读数、使用条件卡片、算例 |
| `docs/reports/PAPER1_equivalent_gap_20261109/equivalent_gap_table.csv` | `9bc51dfebaf5cb11` | 机器可读表（19 几何 × 2 方向） |
| `docs/reports/PAPER1_equivalent_gap_20261109/equivalent_gap.png` | `12c1ec8cd658ec32` | 双栏图：H/h 随 d/w |
| `docs/reports/PAPER1_equivalent_gap_20261109/build_table.py` | — | 生成脚本（含 75 nm 平板校验） |
| `docs/reports/PAPER1_equivalent_gap_20261109/verify_gap.py` | — | 自检：H 反算 K、比值与 ε 互洽，38/38 通过 |

**性质声明**：$H=(12K)^{1/3}$ 是**对已有 K 的单调重标定**，不含新信息、不改任何原有数字。**在该派生目录生成当轮，五个主交付件的哈希均未变**；后续正文与补充修订以本清单第1节当前绑定为准。

---

## 5 投稿前必做：重命名方案（现在不改，打包时一次性执行）

**为什么现在不改**：正文、补充材料、审计报告、PPT 之间存在大量交叉引用路径（如「补充表 S7」「§4.3」），提前改名会打断引用链，且会破坏 git 历史可读性。

**打包时统一改为**（示例，日期取内容版本）：

```
SIM240_Paper1_Manuscript_EN_20261109.md
SIM240_Paper1_Manuscript_CN_20261109.md
SIM240_Paper1_Supplementary_EN_20261109.md
SIM240_Paper1_Figures_20261109.zip
```

改完后：**重算全部 SHA256 → 更新本表第 2 节 → 再把本表一起放进投稿包**。顺序不能反，否则清单里的指纹对应的是旧文件名。

**投稿正文取哪一份**：投出去的正文直接用 §1.4 的两个派生件（`PAPER1_submission_manuscript_20261110/SIM240_submission_CN.md`、`SIM240_submission_EN.md`），不要用 §1 第 1、2 行的母本——母本带内部附录 A—D。重命名时把这两个派生件按上面格式改名，母本留在库里继续作为编辑入口。

---

## 6 怎么核验（一条命令）

```bash
cd /home/dell/yuanyuanxu/SIM240 && sha256sum \
  docs/reports/SIM240_中文稿_导师审阅版_20261022.md \
  docs/reports/SIM240_First_Paper_English_20261028.md \
  docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md \
  docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md \
  docs/reports/PAPER1_conclusions_current_20261109.md | awk '{print substr($1,1,16), $2}'
```

输出前 16 位应与本表第 1 节主交付件逐行一致；不一致说明文件在本表生成后被改过，须判断是新改动（更新本表）还是意外改动（回滚）。

派生件是否仍与母本一致，用脚本自检（不写文件）：

```bash
cd /home/dell/yuanyuanxu/SIM240/docs/reports/PAPER1_submission_manuscript_20261110 && python3 build_submission.py --check
```

输出两行"一致"即说明 §1.4 的投稿稿与当前母本同步；出现"不一致（需重跑）"说明母本已改、派生件过期，重跑 `python3 build_submission.py` 后本表 §1.4 两行哈希需一并更新。

## 1.10 WO-1～WO-3定点修订（2026-11-12）

当前表及派生件指纹已更新；此前各阶段记录为历史快照。未重拟合、未改36点或历史FAIL；h100的离散贡献未排除，严格盲测false保持。

## 1.11 已核文献与贡献措辞定点同步（2026-11-13）

依据已核全文及明确标注的摘要/元数据，更新双语§1.2、§1.3、§5.1、结论首条及补充S11。新增文献[10]—[15]，原方法文献顺延[16]—[20]并保持身份；全文缺口及近邻文献适用限制明示。两摘要、科学数字、公式、结果表、附录E及S14不变，未更换36条主比较的离散参考，不合入R2新数值。投稿派生件由母稿重生成。当前指纹见本清单§1和§1.4；先前各节为历史阶段记录。私有审阅快照及核查见SIM240_code_figures_data的codex/author-progress-20261112分支review/2026-11-13-literature-sync/。此为工作稿同步，非投稿放行或全面新颖性判定。
