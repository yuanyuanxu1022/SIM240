# 论文方法与讨论的"文献对照"写法审查（对着 2026-11-06 文献报告第二节六个模式）

日期：2026-11-06（北京时间）。性质：只读审查 + 措辞建议。**无新计算、无改稿、无门槛修改、无 FAIL 变更。**

审查对象：`docs/reports/PAPER1_literature_closure_20261106/REPORT.md`（六模式归纳）× `docs/reports/SIM240_First_Paper_English_20261028.md`（现行英文稿）。
逐条回原始回执核对：`PAPER1_literature_closure_20261106/api_raw/`。

---

## 0. 一句话结论

**稿件的骨架已经符合文献写法，缺的不是结构，是三样东西：①让 0.17%/0.44% 这两个数字"可读"的那句文献标尺；②两处已经被 C01–C04 推翻的旧句子；③Ryu 2017 与 Cochrane 2018 这两条参考文献本身。** 另外，稿件是 10-28 版，今天闭合的盲测、46 点、两版构建复跑**一条都还没进稿**。

一个反直觉的发现：**稿件正文通篇没有"1% 门槛"**（唯一出现的是"27 个样本在阈值 1% 以内"这种描述)。门槛只活在内部阶段记录（S4）里。也就是说，论文其实已经是文献那种"报告趋势、不设硬门槛"的写法——需要向老师解释的不是"我们为什么不用 1%"，而是"1% 只是内部阶段记录的口径，论文正文从未用它当验收"。

---

## 1. 报告数字的核对结果（逐条回 api_raw）

| 报告里的说法 | 回执核对 | 判定 |
|---|---|---|
| Lauga & Stone 2003 引用 773 | `oa_lauga_stone_work.json` cited_by_count = 773 | ✔ |
| QWS PRE 2003 引用 413 | `oa_qws_pre2003.json` = 413，DOI 10.1103/physreve.68.016306 | ✔ |
| QWS 2003 题名 "Molecular scale contact line hydrodynamics of immiscible flows" | 回执 display_name 逐字一致 | ✔ |
| Sbragaglia & Prosperetti 2007 DOI 10.1063/1.2716438 | Crossref 检索首条即该 DOI，题名一致 | ✔ |
| Sbragaglia"与已有数据及相关数学模型比较" | 摘要原话 "a comparison with available data and related mathematical models is presented" | ✔（降级为摘要级是对的） |
| Taylor & Boning 2009 题名与 rms <2 µm | 摘要原话 "rms errors of less than 2 µm across all processing conditions tested, with absolute topographical heights ranging up to 30 µm" | ✔，见 §2 第 3 条 |
| Reddy & Bonnecaze 2005 无摘要 | Crossref/OpenAlex 均无 abstract 字段，只有题名 DOI | ✔（列缺口正确） |
| DRD 2025 = PRF 10, 094001 | `oa_10_1103_8xz3-2r3b.json`：2025，DOI 10.1103/8xz3-2r3b，题名 "Simulation method of microscale fluid-structure interactions: Diffuse-resistance-domain approach" | ✔ |
| 盲测 10% 判据开跑前冻结 | `check_closure_blindtest_20261106.py` 内 `A_primary_pass_le_10pct`；预测值写在 `run_closure_blindtest_20261106.sh` 头注释 | ✔（可写进论文"预注册"） |

---

## 2. 报告里有 3 处引用细节要改，1 处断言不能这么写

**① "remarkable quantitative agreement" 的出处错了。**
报告把这句话标成 PRE 2003（或"2003＋CICP 2006"那一行）的"摘要原话"。回执显示：
- PRE 2003 摘要原话是 "yields interfacial and velocity profiles **matching** those from the molecular dynamics simulations at the molecular-scale vicinity of the contact line"、"accurately predicted"；
- "**in remarkable quantitative agreement with the MD simulation results down to the molecular scale**" 出自 **CICP 2006**（10.4208/cicp.2006.v1.p1，OpenAlex 引用 127）。

写进论文时只能二选一：引 CICP 2006 说这句，或引 PRE 2003 用 "matching/accurately predicted"。混着写会被审稿人抓到。

**② Ryu 2017 的 10% 被写强了。**
第一轮报告原话是"作者报告最大差异 10%；**这是其特定对照结果，不能直接当 SIM240 容限**"。本轮报告写成"盲测 10% 判据 = **直接对齐** Ryu 2017 的**发表级验收口径**"。这是措辞漂移：Ryu 的 10% 是"填充率（对实验）"的量级，不是"任何模型对任何参考的合格线"。正确写法是**借用同一个容差量级作为事先约定的判据**，并明说量不同、不可转移。

**③ Taylor & Boning 的 rms <2 µm 要带分母。**
同句后半段是"形貌高度最高 30 µm"。2 µm ÷ 30 µm ≈ 6.7%。只写"<2 µm"会让人以为比实际严格得多。引用时写 "rms <2 µm at feature heights up to 30 µm（约 7%）"。

**④ "没有一篇用 ≤1% 硬门槛"这句，不能作为文献事实陈述。**
这是负向断言，样本是"本报告查到的十几篇"。论文里只能写 "in the studies consulted for this work" / "本文所查文献中未见"，不能写 "no study uses..."。

---

## 3. 稿件现状：10-28 版，缺的是今天的成果

| 今天已有的 | 稿件里有没有 |
|---|---|
| 46 个方向点、零反例（上界检验） | 只有 36 点；46 点在 `AI_CONTEXT`，不在稿里 |
| h=100 nm 盲测（+4.39% / −2.03% / 方向比 6.56%） | **没有** |
| 两版构建在 h=75/d=100 上逐位一致 | **没有**（§5.3 仍写"两个程序身份组"，风险按未分离处理） |
| 10% 判据的文献依据（Ryu 2017） | **没有**，Ryu 2017 不在参考文献里 |
| Cochrane 2018（框架出处） | **不在参考文献里**（正文第 7 条链路断了） |

这不是"文献写法"问题，是**稿件版本落后于证据**。文献报告给了补进去的引用依据，但改稿是另一件事（见 §6）。

---

## 4. 六模式 × 稿件逐项对照

| 模式 | 稿件对应位置 | 现状 | 差什么 |
|---|---|---|---|
| ①解析基准 | §3.2 Table 3（h=75：0.444/0.111/0.0272%）＋ S1（h=30：0.173%） | **有，且优于文献** | 没写"文献同级基准通常 2–10%"这句标尺，读者无法判断 0.44% 是好是坏 |
| ②跨方法独立对照 | §2.4 周期/线性/批次互核 | **部分** | 只有"同系数双实现"；独立显式沟槽求解器没有。且 §2.4/§3.4 的现有句子把这件事说成"完全没做过"（已过时，见 §5） |
| ③实验对照 | §5.3 明写"未与实验比较" | **缺，但已诚实声明** | 文献里最普遍的一环；补不补由导师定，论文不能假装有 |
| ④理论内部闭环 | Appendix E 上界（E1–E5） | **有，是最强一环** | 正文没说"这类内部保证在文献里属常规做法"（徐 2015 变分自洽、DRD 2025 无需网格门槛，正是先例） |
| ⑤方法类三段式 | §3 结构：基准 → 网格 → 线性 | 近似符合 | 缺"参数口径指南"式的一小段（tau/dx/dt 怎么选），目前散在补充材料 |
| ⑥适用范围与失败条件 | §5.3 非常充分 | **有，甚至过度防御** | 措辞可以更接近文献的直白度：Dewangan 直接写"方波槽公式发散、不适用"，我们在同类位置写得比它保守得多 |

---

## 5. 两处必须改的旧句子（事实层面已被今天的计算推翻）

**① §2.4 Terminology 段末**

> 现文：An independent-solver comparison would be a numerical cross-check and would not alone establish physical validation; **no such same-geometry comparison has been completed.**

问题：C01/C02 就是同几何（h=75/d=100）、两个不同程序的对算。读者若知道这件事，这句就是错的；若不知道，则浪费了一个已完成的检查。

> 建议：Two implementations of the same average-flow model have been cross-checked at the reference geometry; this establishes implementation consistency, not coefficient accuracy. **A comparison against an independently converged explicit-groove solution has not been completed.**

**② §3.4 末句**

> 现文：**No same-geometry independent-solver or experimental reference is available here.**

> 建议：No same-geometry **groove-resolved** reference and no experimental reference is available here; the cross-implementation check at the reference geometry concerns the reduced model only.

这两处改动的实质：把"独立求解器"拆成"独立实现（已做）"与"独立沟槽分辨解（未做）"。这正好是文献报告模式②的分层，Dewangan 用的是后者，我们不能冒充前者。

---

## 6. 可直接粘贴的三段文献对照文字（英文，含中文对照）

**(a) 放到 §3.2 表 3 之后——给 0.44% 一个标尺**

> The flat-wall error decreases from 0.444% at 5 nm to 0.0272% at 1.25 nm. Analytical benchmarks in lubrication and slip-flow studies are commonly reported at the 2–10% level (e.g. the slip-length comparisons of [LS03] and the finite-element cross-check of [DD20]); the present 0.44% is therefore a benchmark pass rather than an accuracy certificate, and it does not extend to grooved geometries.

中文：平板误差从 5 nm 的 0.444% 降到 1.25 nm 的 0.0272%。润滑与滑移流文献里解析基准通常在 2–10% 量级（如 [LS03] 的滑移长度对照、[DD20] 的有限元交叉核对），故本文 0.44% 属"基准通过"而非"精度证书"，且不外推到沟槽几何。

**(b) 放到 §3.3 或 §5.3——把"不设硬门槛"写成有依据的选择**

> Grid refinement is reported here as a sensitivity trend rather than as a pass/fail threshold. In the studies consulted for this work, refinement is used to show that a conclusion does not depend on resolution [DD20, KR21], with convergence order and grid-convergence indices reported descriptively [CE08]; a fixed percentage change under refinement is not used as an acceptance criterion.

中文：这里把网格加密写成敏感性趋势，而不是通过/不通过门槛。本文所查文献中，加密用来表明结论不依赖分辨率，收敛阶与 GCI 只作描述性报告；未把"加密后变化固定百分比"当作验收判据。

**(c) 若把 h=100 盲测写进稿（§4 末或 §5.3）——10% 的出处与界限**

> The tolerance was fixed before the case was run. A 10% maximum difference has been adopted as a publication-level agreement level when an imprint filling model is compared with experiment [RY17]; that comparison concerns filling ratio against measurement, so the value is used here as a tolerance convention of the same order, not as a transferred validity claim. The present test covers one geometry and does not extend to thin gaps or to dynamic imprinting.

中文：判据在开跑前固定。10% 曾被用作压印填充模型与实验对照的发表级一致量级 [RY17]；该对照是填充率对实测，故此处只借用同一量级的容差约定，不构成"有效性可转移"的主张。本文盲测只覆盖一个几何，不外推到薄隙与动态压印。

**需新增的参考文献条目**

- [LS03] Lauga E., Stone H.A. Effective slip in pressure-driven Stokes flow. *J. Fluid Mech.*, 2003, **489**: 55–77. DOI: 10.1017/S0022112003004695
- [DD20] Dewangan & Datta 2020（稿件已有 [5]，复用即可）
- [KR21] Krause et al. 2021（稿件已有 [7]，复用即可）
- [CE08] Celik et al. 2008（稿件已有 [10]，复用即可）
- [RY17] Ryu J., et al. A modified squeeze equation for predicting the filling ratio of nanoimprint lithography. *Nano Convergence*, 2017, **4**: 14. DOI: 10.1186/s40580-017-0108-z
- [CJ18] Cochrane A., et al. *Int. J. Multiphase Flow*, 2018, **104**: 9–19（框架出处，须补；引用时注意"有限度验证"这句原话出自**作者博士论文**，不是 IJMF 正文，不要把它作为 IJMF 原文引用）

---

## 7. 需要你或导师定的三件事

1. **稿件是否现在补进今天的成果**（盲测、46 点、两版构建、Ryu 引用）？还是等这一轮汇报后统一改稿。
2. **§2.4 / §3.4 那两句是否按 §5 改**？这是纯事实性更正，不涉及主张升格。
3. **Cochrane 2018 的"limited validation"要引原文还是引博士论文**？报告已注明原话出自学位论文；两种引法证据强度不同，需定一次。

---

## 8. 边界

本轮只读审查：没有改稿、没有改门槛、没有新计算。S4 的 1.328387035% FAIL、`reference_qualified=false`、`submission_ready=false` 与全部历史 FAIL 原样保留。
