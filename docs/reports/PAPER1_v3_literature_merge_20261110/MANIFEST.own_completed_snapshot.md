# 第一篇投稿件清单（MANIFEST）

> **这份文件解决一个具体风险**：截稿稿件的**文件名日期**与**内容同步日期**不一致（如中文稿文件名写 20261022，内容已改到 2026-11-10）。只按文件名判断新旧会取错版本，投稿打包或交给他人时会用旧稿。
>
> 本表把「文件 → 内容版本 → 指纹」三者绑定。**清单当前绑定更新：2026-11-10**（本表哈希对应此刻磁盘状态）。
>
> 规则：**任何交付件改动后，必须重算该行 SHA256 并更新本表**；否则本表失效，比没有清单更危险。

---

## 1 主交付件（投稿正文与补充材料）

| # | 文件 | 文件名日期 | 内容版本 | SHA256（前 16 位） | 字节 | 用途 |
|---|---|---|---|---|---|---|
| 1 | `docs/reports/SIM240_中文稿_导师审阅版_20261022.md` | 20261022 | **2026-11-10** | `245ca379448486fd` | 71620 | 中文主稿（导师审阅与内部对照用；不作为投稿正文） |
| 2 | `docs/reports/SIM240_First_Paper_English_20261028.md` | 20261028 | **2026-11-10** | `c7364b6408640262` | 76586 | **英文主稿（投稿正文基准）** |
| 3 | `docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md` | 20261024 | **2026-11-10** | `a9f4557cb8ecb673` | 32578 | 补充材料（中文） |
| 4 | `docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md` | 20261028 | **2026-11-10** | `ab6228f9bbaa2622` | 39140 | **补充材料（英文，随投）** |
| 5 | `docs/reports/PAPER1_conclusions_current_20261109.md` | 20261109 | 2026-11-09 | `91e6eba3e3809046` | 13352 | 结论定稿（六条，**唯一结论口径来源**） |

**四个正文/补充文件的文件名日期均早于内容版本**：打包时以“内容版本”及SHA256绑定为准。

---

## 1.1 A范围基础下界定点合入（2026-11-09）

两份正文仅在附录E末尾增加E.1基础下界（新增式E7、E8），并在§5.1末加入一句回指。摘要、五条正文结论、原式E1—E6、科学参考文献及双语补充S1—S14保持；未增加正式图表号。修正版区间图作为独立追溯材料保留。第1、2行哈希与字节数已按本轮实际文件重绑定；完整SHA和合稿检查见 `docs/reports/PAPER1_lower_bound_merge_20261109/output_hashes.json`、`verification.json`。其他历史清单和旧审查哈希保留其快照身份，不据此声称当前文件未变。

本次合稿不改变数值参考资格、既有FAIL或投稿准备状态；不扩大机制或预测主张。独立六条结论文件未改，正文五条结论也未改；其既有组织差异不在本轮重排范围。

**1.1.1 复核后修正（2026-11-09 晚）**：独立复核发现两处新加文本自身的问题并已改：① 新段落百分比由一位小数改为两位（58.17 / 23.84 / 88.85 / 30.63），与表8表注“本表及正文的百分比统一保留两位小数”一致，并注明 88.85 / 30.63 与表8“原始平均绝对偏差”为同一统计量；② 附录E标题由“上界性质”改为“上下界性质”（英文 Upper- and lower-bound properties），使标题与新增E.1内容相符。既有数字、五条正文结论、式E1—E6、摘要与参考文献均未改动。本轮前一轮 SHA（`7ce3ac6b…` / `0554657c…`）保留为历史快照，不再代表当前文件。明细见 `docs/reports/PAPER1_lower_bound_fix_20261109/REPORT.md`。

**1.1.2 汇报 PPT 结论页 5→6 条（2026-11-09 晚）**：PPT 第 11 页原按正文五条结论排，与 `docs/reports/PAPER1_conclusions_current_20261109.md` 的六条不一致（缺“新增间隙与静态接入”）。已补为六条：新增第五条“新增间隙与静态接入”（h=100 nm 对照：原公式 +126.62%/+49.43%、V2 −2.03%/+4.39%、方向比 A −6.15%、静态接入后出口流量降 56.77%/30.14%，均按沿槽/横槽排序，数字全部取自中文稿 L410、L462 已写定值），原第五条“理论上界”并入第六条“理论上界与机制诊断”。卡片高度 1.06→0.855 in 以容纳六条，第 12 页边界页标题同步为“六条结论各自能说到哪一步”。稿件正文与独立结论文件**未改**（正文仍是五条，差异为既有组织差异）。检查：`check_lowerbound_pages.py` 23 项 0 失败，`check_overflow.py` / `check_overlap.py` 通过。明细见 `docs/reports/PPT_论文汇报_20261109/STORY.md`。

---

## 1.2 纠错v3相关工作与引文编号合入（2026-11-10）

已按 `PAPER1_MF_fulltext_audit_20261110/CANDIDATE_*_v3.md` 同步两正文§1.2、§2.2及两补充S11。新增Ng[7]、Mohammadi–Floryan[8]、Stroock[9]；按实际首次出现顺序，原OpenLB[7]→[10]、Guo[9]→[11]、Bouzidi[8]→[12]、Celik[10]→[13]、Teyssèdre[11]→[14]。全文与补充回指按同一文献身份更新，未另增Tran。原上下界推导、公式/图表编号、摘要、五条正文结论及既有数字保持，结论中原科学引文如有仅随身份改号。没有重复理论复核或新增仿真。

第1—4行SHA及字节数已按本轮实际文件重绑定。当前完整SHA、改前快照、全局引用映射和检查回执见 `docs/reports/PAPER1_v3_literature_merge_20261110/REPORT.md`、`output_hashes.json`、`verification.json`。旧合稿/复核记录保留各自历史快照身份，不作为当前文件哈希；当前投稿资格与既有FAIL不因本轮文字工作改变。

---

## 2 数据证据件（正文与补充材料引用，不进投稿包但须可追溯）

| # | 文件 | SHA256（前 16 位） | 字节 | 用途 |
|---|---|---|---|---|
| 6 | `docs/reports/SIM240_manuscript_revision_20261018/map36_evidence.csv` | `9fe4324f44dce2b9` | 9416 | 36 条主结果原始 K/ε/V2 残差 + result_path + sha256 |
| 7 | `docs/reports/PAPER1_闭环方案_20261105/bound_check_44_points.csv` | `3f3dcf8f196c5f90` | 8673 | 边界审计点集；h=100/d=100 两条在第 46–47 行 |
| 8 | `docs/reports/SIM240_Supplementary_Methods_20261024/Table_S7_thin_gap_correction.csv` | `38aaf8b3b7a99823` | 231 | 补充表 S7（薄隙 5/2.5 nm 两档偏差并列） |

同目录其余 S 表：S1 运行清单、S2 加密、S3 周期检查、S4 网格归档、S5 条件 GCI、S6 新增间隙构建对照、S8 控制证据、S9 机制诊断——**表体与上表同期**，改动时须同步核对。

---

## 3 图件（4 组，各 PDF + PNG）

| 图 | PDF SHA256 | 对应正文 |
|---|---|---|
| Figure_G2_K_convergence | `387b99229fff360f` | 网格收敛 |
| Figure_G2_anisotropy | `8e8626fd9ea15224` | 各向异性比 |
| Figure_G2_resistance | `569b2dc8be360e7b` | 水力阻力（导度倒数） |
| Figure_G2_GCI | `399be2d7535ec453` | 细网格 GCI 估计 |

路径：`paper_figures/figures/`；图注：`paper_figures/figure_captions.md`。投稿前需按期刊要求重命名为 Fig1–Fig4，并同步图注编号。

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
