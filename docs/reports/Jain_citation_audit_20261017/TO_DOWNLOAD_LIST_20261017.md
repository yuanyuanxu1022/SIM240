# 还需下载的论文清单（2026-10-17 核实版）

**核实方式**：Crossref / OpenAlex 实时查询 + 实际下载尝试。不是凭印象。
**判断口径**：只列"下载后能改变论文内容或审稿答复"的论文；纯凑参考文献的不列。

---

## 一、已经拿到，不用再找（7 份）

| # | 文献 | 获取状态 | 存放位置 |
|---|---|---|---|
| 1 | **Ban 2021 博士论文**（154 页，含第 2、3 章） | ✅ 已有 | `~/下载/BAN-DISSERTATION-2021.pdf` |
| 2 | **Ban & Bonnecaze 2020**, JVST B 38(2):022601 | ✅ 已有期刊版 | `~/下载/Ban和Bonnecaze - 2020 - …pdf` |
| 3 | **Dewangan & Datta 2020**, JFM 891:A12 | ✅ **已免费下载**（CC-BY） | `.workbuddy/tmp/dewangan2020.pdf` |
| 4 | Jain et al. 2017, Microelectron. Eng. 173:62-70 | ✅ 已有（项目早期） | 项目文献库 |
| 5 | Ban 2018 ISCST 会议稿（6 页） | ✅ 已有 | `raw/conference2018_pdf.pdf` |
| 6 | Ban 2019 NNT 摘要（2 页） | ✅ 已有 | `raw/conference2019_pdf.pdf` |
| 7 | Yin et al. 2018, Micromachines 9:335 | ✅ 已有全文（OA） | `raw/filling2018_pdf.pdf` |

---

## 二、✅ 已补齐（2026-10-17 18:32 用户完成下载）

| 文献 | 状态 | 归档 |
|---|---|---|
| **Ban 2021 期刊版** JVST B 39(1):012601 | ✅ 已下（文件名被系统存成 `ban2020.pdf`，实为 2021） | `raw/ban2021_JVSTB_39_012601.pdf` |
| **Cochrane et al. 2018** IJMF 104:9–19 | ✅ 已下（下了两份，同文） | `raw/cochrane2018_IJMF_104_9.pdf` |
| Kuo 2026 Microsyst. Technol. 32(12):195 | ⬜ **仍未下**（Springer 闭源，Unpaywall 无 OA；摘要已够用） | — |
| **Dewangan 2024** TCFD 38(1):39–59 | ⬜ **仍未下**（同上三项均确认闭源） | 摘要见 `TWO_MISSING_FULLTEXTS_20261018.md` |

> **2026-10-18 更新**：本清单原先列「还差三篇」，其中 **Ban 2021 期刊版与 Cochrane 2018 已于 10-17 补齐**。
> 现**只剩两篇**，且两篇都**不是卡脖子的**。两篇的摘要原文、闭源核验与「已知/未知」逐条对照，
> 已整理进 **`TWO_MISSING_FULLTEXTS_20261018.md`**。
>
> **⚠ 其中 TCFD 那篇的重要性被低估了**：它是**跨槽方向**（不是沿槽），几何是**正弦连续波纹**，
> 间隙覆盖 thin–thick 过渡区（≈ 我们的区间），结论是**误差 < 3%**。
> ⇒ 与我们矩形直角槽的 **+10~205%** 并排，**"误差来自尖角"这个论点就不证自明**。
> **若学校有 Springer 权限，这两篇里优先下 TCFD。** |

**吸收报告**：`BAN2021_JOURNAL_ABSORPTION.md`、`COCHRANE2018_ABSORPTION.md`

**两条重要核实结论**：

1. **Ban 2021 期刊版与博士论文第 3 章内容一致**，渗透率式 (9)(10) 一字未改 → 此前对"most of this chapter"的谨慎**可以核销**。期刊版另标注 **Editor's Pick**。
2. **Cochrane 2018 根本不做沟槽**：原文明确 "The effects of capillary forces, structural mechanics and **flow into template features are left for future work**"（p.10）。全文 `groove` 0 次、`rectangular` 0 次。它的"K"是**随饱和度变化的相对渗透率 $k_r(S;S_c,\beta)$**，参数靠能量法/实验标定 → **这给"双相 K 不是纯几何量"提供了精确文献依据**，比原先"双相相对渗透率扩展"的表述更准确。

> ⚠ 另有一个 `1-s2.0-S0032386124011807-main.pdf`（32 MB，Polymer 316 (2025) 127844，纳米粒子在不相容聚合物共混物中的迁移与界面穿越**综述**）——与本项目无关，应是误下。

---

## 三、原先的建议下载（3 篇，按优先级）

### 优先级 1 —— Ban & Bonnecaze 2021 期刊版

- **为什么还要下**：博士论文第 3 章首页脚注写的是 "**Most of** this chapter has been published" —— **"大部分"不是"全部"**。期刊版是同行评审的正式版本，且期刊版可能删改过部分讨论。我们要引这篇，最好对着正式版核一遍页码级的表述。
- **信息**：JVST B **39(1): 012601**，DOI **10.1116/6.0000648**
- 链接：<https://doi.org/10.1116/6.0000648>
- **紧急度**：中。论文投稿前补上即可；现在写引言不影响。
- **备注**：您能下 Ban 2020（AIP 同社），这篇应该也能下。

### 优先级 2 —— Cochrane et al. 2018 两相模型

- **为什么要下**：这是"**双相**"那条线的代表作（相对渗透率 + 困气 + 溶解）。我们在论文"适用范围"里写"双相不适用——黏度比与毛细数会改变界面形态"时，需要准确引这篇，不能只凭摘要。
- **信息**：*Multiphase model for nanoimprint lithography*，Int. J. Multiphase Flow **104: 9–19**，DOI **10.1016/j.ijmultiphaseflow.2018.03.014**
- 链接：<https://doi.org/10.1016/j.ijmultiphaseflow.2018.03.014>
- 备用：OSTI 有 DOE 存档版（记录号 1692156，`https://www.osti.gov/biblio/1692156`），但**今天试了三次都是 502，打不开**。
- **紧急度**：中。写"局限与展望"那一节时必须引准。

### 优先级 3 —— Kuo et al. 2026 填充前沿实验

- **为什么要下**：这是**最新**的一篇（2026-10-16 在线，就是昨天），做"受限微沟槽的瞬态填充前沿"——侧视显微成像 + ANSYS Polyflow 模拟。它的结论对我们有用：**实验观察到的界面变形比模拟更剧烈，模拟低估了幅度**。这句话可以用来论证"高保真 DNS 的必要性"（连商用软件 + 实验对照都承认低估）。
- **信息**：*Front evolution and localized redistribution during confined polymer micro-embossing under different nominal capillary-number conditions*，Microsystem Technologies **32: 195**，DOI **10.1007/s00542-026-06175-1**
- 链接：<https://doi.org/10.1007/s00542-026-06175-1>
- 现状：**只有摘要**（已存 `raw/front2026_abstract.txt`），Springer 全文需订阅。
- **紧急度**：中低。摘要已够支撑一句引用；有全文更稳。

---

## 三、评估后判定"不必下"（3 篇，附理由）

| 文献 | 判断 | 理由 |
|---|---|---|
| **PoF 2022**, *Modeling the squeeze flow of droplet over a step*, 34:082005, DOI 10.1063/5.0098597 | 不必 | 讲液滴跨"台阶"的挤压流，与我们几何里的台阶有关，但**目标是液滴整体挤压变形，不是沟槽内渗透率**。且 OpenAlex 标 `closed`（无 OA）。若审稿人提到再补。 |
| **Phys. Rev. Fluids 2020**, *Cavity filling with shear-thinning liquids*, 5:054003 | 不必 | **剪切变稀非牛顿**流体。我们全篇限定牛顿胶，这篇在适用范围之外；引它反而要把边界说复杂。 |
| **Lan et al. 2018**（中文，《光学精密工程》26(4):894-905） | 不必 | 仅题名级线索（大面积复合模具制造），与 K 标定无已核证据。若一定要引，中国知网可查，但不值得花时间。 |

---

## 四、真正的"缺口"不是论文，是一份列表

**Google Scholar 的 "Cited by" 列表**（谁引用了 Jain 2017）。这是查新最后一环，卡在 CAPTCHA 上。

- 为什么关键：它能发现**不引用我们、但做了等价工作**的平行研究。期刊论文下载得再全，也补不上这个。
- 怎么解决（三条路，任选）：
  1. **校园网直连 Google Scholar**，手工翻 Jain 2017 的 Cited by（约 30–60 条），扫标题；
  2. 用 **Web of Science** 的 "Cited Reference Search"，输入 Jain 2017 的 DOI，导出引文列表（学校一般有订阅）；
  3. **Scopus** 的 "View citing documents"，功能同上。
- 工作量：约 30–60 分钟。**这一步做完，才能决定要不要写"首次"。**

---

## 五、一句话总结

**必须下的已经全了**——最关键的三篇（Jain 2017、Ban 2020/2021、Dewangan 2020）都在手上，其中 Dewangan 2020 是今天新下到的免费全文，价值最大（见下）。

**还差三篇，都不是卡脖子的**：Ban 2021 期刊版（补完整性）、Cochrane 2018（写双相局限时引准）、Kuo 2026（最新实验，摘要已够）。

**真正卡脖子的是 Scholar / WoS 那份被引列表**，不是论文。

---

## 附：今天新发现的 Dewangan & Datta 2020 为何重要

**JFM 891:A12，标题：Effective permeability tensor of confined flows with wall grooves of arbitrary shape**（开放获取 CC-BY）

全文检索结果：
- `Jain` **0 次**，`nanoimprint` **0 次** —— 完全不引 Jain，也不知道纳米压印这回事，是从减阻/滑移角研究的独立路线。
- 方法是**谱分析 + 域扰动法**的**渐近解析**，假设图案尺寸/节距比 ε 很小；算的是正弦、三角波两种**光滑/分段线形**形貌。
- **关键一句话（原文 §4.4）**：

> "the domain perturbation approach … **does not specialize meaningfully to the rectangular topography, because of its jump discontinuity** (Kamrin et al. 2010)."

以及：

> "but for **rectangular grooves, the domain perturbation approach of the current model fails to give a bounded prediction**"

**这句话的分量**：JFM 是这个领域最硬的期刊，他们的渐近解析方法**自己承认对矩形槽失效**（因为有跳变不连续）。

⇒ 这给我们的论文提供了**最有力的"为什么必须做 DNS"的文献依据**：不是我们不会解析，是**解析路线在矩形直角槽上被证明走不通**。

⇒ 同时它**不构成先例威胁**：不引 Jain、不做纳米压印、不做矩形槽、不做 DNS。

**建议写进引言**（比只说"没人验证过"强得多）：

> 对沟槽结构的有效渗透率，已有基于谱分析与域扰动法的渐近解析工作（Dewangan & Datta, JFM 2020），但其方法在矩形直角槽上因跳变不连续而失效，作者本人明确指出该形貌无法给出有界预测。因此矩形沟槽的 K 只能由直接数值模拟确定。
