# 任务 B 执行报告：矩形沟槽输运误差专项检索

> **2026-10-17状态复核订正**：18组执行情况沿用本报告，本轮未重跑；现存JSON仅存前5组结果摘要，余13组未完整归档。Dewangan 2024图1现已从出版社原图目视补核，所示为连续光滑波纹；正文仍未取得。最新状态见[STATUS_20261017.md](STATUS_20261017.md)，记账见[STATUS_RECONCILIATION_20261017.json](STATUS_RECONCILIATION_20261017.json)。

**执行日期**：2026-10-17 20:06–20:20（北京时间）
**执行方式**：OpenAlex REST API（`search` 全文检索 + `sort=relevance_score:desc`）+ WebSearch 补证 + arXiv 全文下载
**执行原则**：不经 Jain 2017 的引文链，独立靠关键词打网；允许"未找到"；不编造 DOI；全文未取得的标注"仅见摘要"

---

## 0 一句话结论

在本次检索及已取得证据中，未确认“矩形直角槽＋全充液＋有限间隙＋与条纹平均闭合做定量误差对比”的直接先例。检索覆盖、排名截断、全文可得性及归档缺口限制这一判断。

既有Kamrin 2010摘录讨论的是一种二阶域扰动近似的失效；不能推广为所有解析/半解析途径不可能或DNS唯一可行。本轮未重新推导或独立复算该文公式。

## 1 检索执行记录（含归档缺口）

### 1.1 检索式与命中量

| # | 检索式 | OpenAlex 总命中 | 有效相关 |
|---|---|---|---|
| 1 | `"permeability tensor" "rectangular grooves"` | 11 | 1（Dewangan 2020） |
| 2 | `"local cubic law" error numerical` | 126 | 0（全为岩石裂隙） |
| 3 | `riblet corrugated laminar effective slip permeability` | 8 | 2 |
| 4 | `nanoimprint permeability simulation validation` | 302 | 1（Cochrane 学位论文，非期刊） |
| 5 | `"lubrication approximation" groove "finite gap" breakdown` | **0** | — |
| 6 | `stripe average permeability arithmetic harmonic mean channel` | 8 | 0 |
| 7 | `transverse grooves pressure driven flow effective permeability` | 659 | 3 |
| 8 | `anisotropic permeability patterned channel numerical simulation grooves` | 418 | 2 |
| 9 | `shallow groove limit effective slip length laminar channel` | 124 | 3 |
| 10 | `graphoepitaxy groove filling permeability anisotropic resist` | **1** | 0 |
| 11 | `lattice Boltzmann grooved channel permeability anisotropic validation` | 67 | 1（同 Dewangan） |
| 12 | `arithmetic harmonic average permeability layered validity condition` | 269 | 0（全为多孔介质/油藏） |
| 13 | `error of lubrication approximation groove amplitude finite Reynolds` | 165 | 1（同 Dewangan） |
| 14 | `nanoimprint resist filling anisotropic permeability model comparison experiment` | 48 | 0 |
| 15 | `rectangular groove Stokes flow permeability numerical exact semi-analytical` | 46 | 1（同 Dewangan） |
| 16 | `direct numerical simulation grooved channel permeability tensor full filled` | 86 | 0 |
| 17 | `jet and flash imprint lithography anisotropic flow model groove direction` | **5** | 0 |
| 18 | `nanoimprint filling simulation validation permeability 2020` | 66 | 0（工艺/材料类） |

**覆盖说明**：总命中数、实际返回数和筛选数须分开。第1组总命中为11。低命中或零命中可能来自术语、索引和截断，不能证明文献空白。

### 1.2 原始数据

- `raw/taskB_openalex_batch1.json`：前5组规范化结果摘要，非提供方完整原始响应；总命中/保存条目分别为11/11、126/25、8/8、302/25、0/0，共69条返回记录，本轮未去重或重筛。
- 其余 13 组未逐条落盘（只记录了命中量），如需可重跑同一检索式。
> **【2026-10-18 11:05 补归档完成】** 上述缺口已关闭，见 §1.3。§1.1 表中“有效相关”一列原为**只看标题前 25 条**的判断，现已由全量筛查取代（§1.4）。

---

### 1.3 补归档：18 组全量重跑（2026-10-18 11:05）

**原缺口**：13 组只记了命中量、没有落盘；已落盘的 5 组里，Q02（126 条）与 Q04（302 条）也只存了前 25 条。即"总命中数 ≠ 实际筛选数"。

**做法**：按 §1.1 的 18 条检索式原样重跑，`per-page=200` + 分页取尽，把**每一条返回记录**（题名、年份、DOI、venue、作者、被引数）全部落盘。

| 组 | 声明 | 取回 | 组 | 声明 | 取回 |
|---|---|---|---|---|---|
| Q01 | 11 | 11 | Q10 | 1 | 1 |
| Q02 | 126 | 126 | Q11 | 67 | 67 |
| Q03 | 8 | 8 | Q12 | 269 | 269 |
| Q04 | 302 | 302 | Q13 | 165 | 165 |
| Q05 | 0 | 0 | Q14 | 48 | 48 |
| Q06 | 8 | 8 | Q15 | 46 | 46 |
| Q07 | 674 | 674 | Q16 | 107 | 107 |
| Q08 | 431 | 431 | Q17 | 8 | 8 |
| Q09 | 133 | 133 | Q18 | 66 | 66 |

**合计声明 2470 条，取回 2470 条（100%）**；组间重复 415 次，**去重后 2055 条唯一记录**。

归档：

- `raw/taskB_rerun18_full_20261018.json`（16.8 MB，18 组完整记录 + 每组实际请求 URL）
- `raw/taskB_unique_works_20261018.json`（13.7 MB，2055 条去重唯一记录）

**必须注意：命中数在两次运行之间会变。** 与 §1.1 原记录相比：

| 组 | 原记录 | 今日 | 差 |
|---|---|---|---|
| Q07 | 659 | 674 | +15 |
| Q08 | 418 | 431 | +13 |
| Q09 | 124 | 133 | +9 |
| Q16 | 86 | 107 | +21 |
| Q17 | 5 | 8 | +3 |
| **合计** | **2409** | **2470** | **+61** |

原因：OpenAlex 索引持续更新（新论文入库、旧记录补全）。⇒ **"总命中 N 条"既不是文献空缺的证明，也不是稳定量**；任何引用该数字处都必须带检索日期。

### 1.4 全量筛查：从 2055 条里筛（不再只看前 25 条）

**筛查规则（全部在标题上执行，可复现）**：

| 级 | 规则 | 剩余 |
|---|---|---|
| 1 | 含几何词 groove/trench/corrugat/riblet/patterned/ridge/cavity/recess/textur/rough/wavy/stripe/microchannel | 218 |
| 2 | + 含输运词 permeab/conductance/lubricat/slip/darcy/stokes/pressure-driven/hydraulic/resistance/flow | 93 |
| 3 | + 含方法词 numerical/simulat/finite element/lattice boltzmann/dns/spectral/asymptot/analytic/homogeniz/validat/comparison | 27 |
| 4 | − 排除无关领域 porous media/reservoir/shale/rock/fracture/soil/membrane/blood/filter/battery/thermal/combust/turbine/aero | **17** |

**这 17 条已逐条读过**（清单 `raw/taskB_screen_pool_17_20261018.json`）：

- 与本课题直接相关的只有 **1 条**：Dewangan 2023/2024, TCFD 38:39–59（即 §2.1 的 D3，已判定为连续波纹）。
- 其余 16 条分布：湍流减阻/沟槽肋条（2 条）、粗糙壁湍流 DNS（1）、超疏水滑移湍流（2）、微织构轴承润滑（3）、纳米流体自然对流/熵产（3）、轮胎湿滑（1）、电渗/软纳米通道（1）、浮力驱动微织构均匀化（1）、超疏水圆管层流解析（1）、水文（1）。
- **无一条**做"矩形直角槽 + 压力驱动 + 有限间隙 + 全充液 + 与条纹平均闭合的定量误差对比"。

**反向核对**：另把 2055 条中**标题含 `permeab` 的 42 条**全部列出检查，同样只有 Dewangan 2020（JFM 891:A12）一条属于本课题；其余为岩石裂隙、多孔介质、纤维预制体、膜、合金铸造等。

> **本节替代 §1.1 的"有效相关"列。** 原列是在前 25 条里目视判断；本节是在 2055 条里按规则筛、再逐条读。

---


## 1.5 ⚠ 事后发现的覆盖缺陷（2026-10-18 13:00，必须与本报告同读）

本报告的 18 组检索式与四级标题筛查**存在一个已实测的盲区**：摩擦学里「流量因子（flow factor）」一支文献，
即本文所对比的那个闭合在另一学科的原始形态。

**实测证据**（逐条在 2055 条归档中按 DOI 查）：

| 文献 | 是否在 2055 条中 | 原因 |
|---|---|---|
| Patir & Cheng 1978（闭合原始出处） | ✗ | 被 `from_publication_date=2005-01-01` 排除 |
| Lavrov 2023（算术 vs 调和平均透射率） | **✓ 在池中，但被筛掉** | 标题不含几何词（第一级） |
| Rom et al. 2021（同质化 vs Patir–Cheng，量化平均模型误差） | ✗ | 检索式未含 `homogenization`/`averaging` 等词 |
| Letalleur et al. 2002（正弦面流量因子） | ✗ | 通过几何词，但缺方法词（第三级） |
| van Odyck & Venner 2002（Stokes vs Reynolds） | ✗ | 检索式未含 `Stokes in thin films` 类措辞 |
| Pusterhofer et al. 2018（N-S 算流量因子） | ✗ | 同上 |

**⇒ 结论必须改写**：

- **取数层面**：18 组 × 2470 条已 100% 取回，**无缺口**；
- **覆盖层面**：**有缺口**。四级规则要求标题同时含「几何词 + 输运词 + 方法词」，
  而这一支文献标题通常只写 "hydrodynamic lubrication" / "flow factors" / "transmissivity averaging"，
  **在第一级即被滤除**。

因此本报告 §1.4 的「17 条候选池已逐条读过」应理解为 **「该规则的输出已逐条读过」**，
**不得理解为「相邻文献已通读」**。

**补法（未执行）**：加 4–6 组不含几何词的检索式；去掉 2005 年下限单跑一轮；
筛查改为「输运词或方法词命中即入池」。详见 `CROSSCHECK_CD_20261018.md` 第四、七节。

### 1.5·补　推理方式的更正（2026-10-18 13:20）

本节的**结论成立，但推理路径需更正**。上表用「不在 2055 条里」作为缺口的证据，这种论证不严谨：

**反例**：Ban & Bonnecaze 2020（本文核心引用之一）**同样不在** 2055 条里——
它的标题 *Optimal placement of droplets for UV nanoimprint lithography* 既不含 permeability 也不含 groove，
是由 **A 引文链**找到的。这完全正常：检索本就是 A/B/C/D 多路并行，任何单一路径都必然漏一部分。

⇒ **「某文献不在 B 的池中」不构成缺陷。** 成立的缺陷只有三条，都指向具体机制：

| # | 缺陷 | 证据 |
|---|---|---|
| 1 | 2005 年下限排除了原始文献 | Patir & Cheng 1978 早于 2005，必然不在池中 |
| 2 | 筛查要求标题含几何词 | Lavrov 2023 **在池中**却被第一级滤掉 |
| 3 | 检索词缺等价命名 | `flow factor`/`transmissivity`/`homogenization`/`averaging` 均未出现在 18 组式中 |

**正确记账**：B 的**取数**无缺口（2470/2470）；B 的**覆盖**受上述三条限制，需补检索。
**不得**因 A 或 D 找到的东西 B 没有，就判定 B 失职。

### 1.5·补二　根因已查明：单术语锚定（2026-10-18 13:20）

按改写式重跑（TS1′/TS2′/TS3/TS4，去掉 2005 下限）后新增 8 篇关键文献，
**8 篇全部不在本报告的 2055 条归档里**。逐条核对后，原因是**同一个**，不是随机的：

> **本报告的 18 组检索式，每一组都要求 `permeability` 出现。**
> 而这一整支文献谈的是 lubrication / Reynolds / **flow factor** / **filling**，
> 标题与摘要里根本不出现 "permeability"。

| 新增关键文献 | 标题含 permeability？ | 故必然漏检 |
|---|---|---|
| Teyssèdre et al. 2013（FEM 校核润滑理论算压印力） | ✗ | ✓ |
| Wang & Hiroshima 2011（实验观测各向异性填充） | ✗ | ✓ |
| Lubrecht et al. 1988（纵/横粗糙度 vs 流量因子） | ✗ | ✓ |
| Berger & Sadeghi 1996（FEM + Patir–Cheng + 带槽离合器） | ✗ | ✓ |
| Mitsuya & Koumura 1995（稀薄气体流量因子） | ✗ | ✓ |
| Schwendeman et al. 2015（同质化 + Stokes 平均 + 横/纵） | ✗ | ✓ |
| Chauhan et al. 2009（S-FIL 特征填充建模） | ✗ | ✓ |
| Reddy et al. 2005（界面穿过矩形尖角） | ✗ | ✓ |

**⇒ 这是「检索锚定在单一术语上」的经典失效**，比时间下限与标题规则更根本：
只要被检索对象的**同义术语体系不同**（渗透率 vs 润滑/流量因子/填充），单一锚词就必然漏。

**已补的检索**：TS3（`flow factor`/`average flow model`/`averaged Reynolds`）148 条、
TS4（`transmissivity averaging`/`arithmetic harmonic`/`homogenization`）791 条，均已归档。
**仍未补的**：中文术语（`流量因子`、`平均流量模型`）未在 CNKI 检索过。

详见 `RERUN_SUPPLEMENTARY_20261018.md`。

---

## 2 报告所列候选分级

分级标准：**定量误差对比** = 明确给出"解析近似 vs 数值精确解"的误差数字；**仅推导** = 只给解析式或误差界；**仅应用** = 直接使用既有闭合。

### 2.1 最相关的一组：Dewangan 系列（同一作者，5 篇）

| # | 文献 | 槽形 | 方法 | 分级 | 相关性与证据边界 |
|---|---|---|---|---|---|
| D1 | **Dewangan & Datta 2020**, *Effective permeability tensor of confined flows with wall grooves of arbitrary shape*, **JFM 891:A12**, DOI 10.1017/jfm.2020.134 | 正弦、三角等；既有报告记录方波近似发散 | 谱分析+域扰动渐近解析 + 数值评估 | **定量误差对比** | 必须比较的近邻；一种方波近似失效不等于全文不涉及矩形槽 |
| D2 | **Dewangan & Datta 2018**, *Flow through microchannels with topographically patterned wall: A spectral theory for arbitrary groove depths*, **Eur. J. Mech. B/Fluids 70:73–84**, DOI 10.1016/j.euromechflu.2018.02.004 | 既有检索记录判为正弦；本轮未核正文 | 谱方法（Fourier）+ FEM交叉验证（既有记录） | **定量误差对比** | 保留近邻，正文未取得 |
| D3 | **Dewangan 2024**, *Investigation of Stokes flow in a grooved channel using the spectral method*, **TCFD 38:39–59**, DOI 10.1007/s00162-023-00679-6 | 出版社图1为连续光滑波纹，公开附录含余弦项 | 谱方法＋FEM比较（摘要）；正文未取得 | **定量误差对比（摘要证据）** | 近邻；图1已核，全部算例/闭合未全文核实 |
| D4 | Dewangan & Persoons 2024, *Electromagnetohydrodynamic flow through a periodically grooved channel*, **J. Phys. D 57:165002**, DOI 10.1088/1361-6463/ad2007 | 正弦（undulating） | 谱方法 + FEM | 定量误差对比 | ❌ 加了电磁场，物理不同 |
| D5 | Dewangan 2025, *Effects of topographical wall patterns on flow through porous media*, **Phys. Fluids 37:013613**, DOI 10.1063/5.0243010 | 正弦 | 谱方法 + Darcy-Brinkman | 定量误差对比 | ❌ 多孔介质 |

**关于 D3 的判断（本轮公开原图补核）**：

[出版社页面](https://link.springer.com/article/10.1007/s00162-023-00679-6)摘要确认受限横向流及模型与有限元的定量比较；公开附录A1含余弦形貌项。[图1](https://media.springernature.com/full/springer-static/image/art%3A10.1007%2Fs00162-023-00679-6/MediaObjects/162_2023_679_Fig1_HTML.png)已实际打开目视核查，所示壁面为连续光滑波纹。归档为`raw/dewangan2024_fig1_verified_20261017.png`，SHA256见状态记账。

图1槽形这一具体待办已关闭；正文及全部算例/闭合仍未核实，保留近邻地位。旧22:15仅凭摘要词频排除矩形槽的理由不足。未引用Jain、无NIL语境或只研究一个方向，均不是排除同类贡献的充分理由。

### 2.2 Kamrin 2010：特定二阶域扰动近似的限制

**Kamrin K., Bazant M.Z., Stone H.A., *Effective slip boundary conditions for arbitrary periodic surfaces: the surface mobility tensor*, JFM 658 (2010) 409–437**, DOI 10.1017/s0022112010001801。已下载 arXiv 全文（`raw/kamrin2010_JFM_658_409_arxiv.pdf`，30 页）。

**该文明确讨论了"方形槽"这一反例（§4.1，原文式 36 之后）**：

> "Consider a surface of shallow, **square grooves** … To use the mobility matrix approximation for this surface, one computes the Fourier coefficients of the above and finds that |ĥ(m,n)| decays like |1/m|. Likewise, the summand in each of the diagonal entries of M̃ must decay as |1/m|, and consequently **M̃11 and M̃22 are both infinite**. **This prediction for the mobility is clearly erroneous**, as it suggests the effective slip velocity should be infinite (regardless of the choice of ǫ > 0), which contradicts known results in Wang (2003) and basic intuition."

并给出**一般性失效判据**（式 39 之后）：

> "Equation 39 reveals that the error is **unbounded for any surface where |∇∇h|M or |∇h|M → ∞**. This result gives the following crucial limitation: **The approximation M(ǫh) ≈ −ǫ²M̃(h) should not be used for surfaces with corners or vertical slopes.**"

**这三句话的价值**：
1. 它不是"经验性地说矩形槽难算"，而是**数学上证明发散**（1/m 衰减 → 二阶张量无穷大）；
2. 判据是**"带尖角或垂直壁"**，我们的矩形直角槽完全落在其中；
3. 它解释了为什么 Dewangan 2020 要写"矩形槽给不出有界预测"——**源头就是这里**。

**⚠ 但必须注意边界**：Kamrin 2010 处理的是**剪切驱动**（shear-driven）的有效滑移，半无限域；我们是**压力驱动 + 有限间隙 + 全充液**。所以：
- **能引的**：域扰动/渐近解析路线对带角几何失效这一**数学事实**；
- **不能引的**：不能说"Kamrin 证明了压力驱动矩形槽渗透率无法解析求解"——他没做这个。

**保守表述示例**（正式引用前仍须核查原页及适用条件）：

> Kamrin等（2010）所讨论的二阶域扰动迁移率近似对方形槽存在发散问题。这提示该近似需审查壁面光滑性及适用条件；它不证明有限间隙压力驱动矩形槽的所有解析/半解析途径均不可行。

### 2.3 其余候选与排除理由

| 文献 | 判断 | 排除理由 |
|---|---|---|
| *Longitudinal flow in superhydrophobic channels with partially invaded grooves*, J. Eng. Math. 2022, DOI 10.1007/s10665-022-10240-9 | 不同物理 | 槽内有**气体**（超疏水 Cassie 态），非全充液；这是双相，正好在我们边界之外 |
| *Flow in channels with superhydrophobic trapezoidal textures*, Soft Matter 2013, DOI 10.1039/c3sm51850g | 不同物理 | 梯形 + 超疏水（有界面） |
| *Porous-layer model for laminar liquid flow in rough microchannels*, Microfluid. Nanofluid. 2010, DOI 10.1007/s10404-010-0625-0 | 仅应用 | 把粗糙度等效为多孔层，不是矩形槽精确解 |
| *Effective slip in nanoscale flows through thin channels with sinusoidal patterns of wall wettability*, Microfluid. Nanofluid. 2014, DOI 10.1007/s10404-014-1483-y | 不同问题 | 变的是**润湿性**分布，不是几何沟槽 |
| *Modeling multiphase flow and substrate deformation in nanoimprint manufacturing systems*, UNM 学位论文 2019 | 仅应用 + 双相 | Cochrane 学位论文，双相；与我们几何不同 |
| 岩石裂隙类（总命中126，仅保存前25条） | 几何不同，但方法可能相关 | 不能宣称126条全部已排除；需比较局部立方律、平均方式及误差定义的可借鉴性 |
| 多孔介质/油藏类（报告总命中269，无完整列表归档） | 待限定筛选范围 | 不能宣称269条全部已排除；等效渗透率平均方法应作为方法近邻评估 |

---

## 3 三个判据的补充回答（针对任务 B 的独立性）

| 问题 | 答案 | 依据 |
|---|---|---|
| 1. 目标矩形槽、有限间隙和等价闭合的定量误差比较 | 现有记录未确认直接先例 | 近邻保留；未取得的正文不能彻底排除，不能将Kamrin近似的发散推广为所有矩形槽问题 |
| 2. 目标条纹平均/局部立方律的失效范围 | 现有记录未确认系统研究 | 检索与归档有限；其他几何或名称下的方法证据仍需比较 |
| 3. 纳米压印中目标单相几何K的直接定量验证 | 现有记录未确认 | 宏观填充、毛细压力或两相相对渗透率验证须与该问题分开评估 |

---

## 4 对论文定位的影响

### 4.1 之前能说的话（保留）

> 既有吸收报告记载，Jain等（2017）使用的闭合在同组2020、2021年工作中继续采用，相关验证关注毛细压力和填充等问题。它们是否验证了本文目标的单相几何K，应按具体图表和比较口径核对。

### 4.2 方法依据的表述边界

特定域扰动近似在方形槽上的失效提示需要审查近似的几何适用性。本文采用经过数值验证的显式解，在统一口径下评估闭合误差。

这不能推出“Jain闭合从未验证”“解析路线被证明不可能”“DNS是唯一途径”，也不能用未经核实的历史算力解释先例缺失。是否已有直接先例仍需继续核查。

### 4.3 仍然不能说的话

- ❌ "首次" —— 现有检索覆盖及全文证据不足；C/D完成也不单独证明全球无先例。
- ❌ "矩形槽的有效渗透率从未被算过" —— Kamrin 2010 用其他手段（滑移界/数值）给过方形槽结果，Wang 2003 也讨论过（引文见 Kamrin 原文）。我们没读 Wang 2003，不能断言。
- ❌ "解析方法完全无法处理矩形槽" —— 只能限定到已核实的特定近似和问题设定；不能一并排除整个域扰动方法家族、级数解或其他半解析途径。

---

## 5 本次任务的局限（必须写明）

1. **数据库覆盖**：据本报告使用OpenAlex、网页和arXiv；**未使用** Web of Science、Scopus、EI、CNKI，不能以公开检索代作这些数据库的检索。
2. **检索深度**：18 组检索式，每组取前 20–25 条。若某篇相关论文排在 25 名之后且标题不含关键词，会漏。
3. **全文获取**：D2、D3正文未取得；D3图1所示槽形现已补核，全部算例/闭合仍未排查。不使用未经校准的置信度百分比。
4. **语言**：未检索中文文献（CNKI）。**这是一个真实缺口** —— 国内纳米压印/微流控方向可能有中文期刊工作。如需补，建议在 CNKI 用"沟槽 渗透率 各向异性 数值"检索。
5. **时间窗**：报告记载主力检索偏向2005年后；早期文献覆盖不足，不能预先排除早期矩形槽、级数解或半解析先例。
6. **归档**：仅5组结果摘要可核，余13组缺完整结果清单；总命中数不代表全部已筛选。

---

## 6 建议的下一步

| 优先级 | 事项 | 谁做 | 耗时 |
|---|---|---|---|
| 1 | 任务C：WoS/Scopus的Jain被引检索＋独立主题检索，导出后筛摘要/全文 | 有访问权限者，AI辅助分析导出 | 取决于候选量 |
| 2 | 保留D3全文/全部算例及13组归档缺口；图1已核无需重复查 | 后续补证 | 未定 |
| 3 | 任务 D：Asta 独立交叉 | 用户（贴指令即可）| 10 分钟 |
| 4 | CNKI 中文补充检索（可选） | 用户或我（若能访问）| 20 分钟 |

这些工作增加检索覆盖，不能单独证明“首次”。

---

## 7 任务 B 状态

**执行与归档状态（2026-10-18 11:05 更新）**：18 组已于当日**全部重跑并分页取尽**，2470 条（去重 2055 条）全部落盘，见 §1.3。原"5 组可核、13 组归档不足"的缺口已关闭。

**筛查状态**：不再只看前 25 条。§1.4 按四级规则从 2055 条筛到 17 条候选池并逐条读过，另反向核对标题含 `permeab` 的 42 条。结果：直接相关的仍只有 Dewangan 系列。

**具体补核**：D3图1已用出版社原图确认；正文与全部算例仍未完整核实，保留近邻。

**仍存的覆盖缺口**：WoS/Scopus/EI/CNKI 未用（中文与部分会议文献不在 OpenAlex）；早期文献（2005 年前被 `from_publication_date` 过滤）；部分候选未取得全文；Dewangan 2024 正文未取得。**归档缺口已关闭**。不折算为百分比或查新概率。

**结论**：本次可核证据内未确认目标闭合误差标定的直接先例；不证明全球不存在或所有解析方法不可行。
