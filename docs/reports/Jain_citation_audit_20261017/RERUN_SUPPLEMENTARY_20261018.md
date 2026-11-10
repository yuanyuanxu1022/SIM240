# 补充检索重跑（TS1′ / TS2′ / TS3 / TS4）：结果与三篇必须交代的新文献

**执行时间**：2026-10-18 13:00–13:20
**触发原因**：上一轮实测出原 18 组检索式有三个具体缺陷（2005 年下限、标题须含几何词、缺等价命名）。
本报告是修复后的重跑。

**可复现**：脚本 `CASE/D_series/D2_groove_error_map/rerun_supplementary_queries.py`；
原始返回 `raw/rerun2_TS1p.json`、`rerun2_TS2p.json`、`rerun2_TS3.json`、`rerun2_TS4.json`。

---

## 一、四条检索式与命中量

OpenAlex 的 `title_and_abstract.search` 支持引号短语与 `|`（OR），重复 filter 键即为 AND。
因此 WoS 的 TS 式可近乎直译，**不必再按词组合展开**。全部**不加时间下限**。

| 式 | 含义 | 组数 | 命中 | 取回 |
|---|---|---|---|---|
| **TS1′** | permeability ∨ hydraulic conductance × groove/corrugat/trench/ridge × permeability-tensor/anisotropic × 方法词 | 4 | 31 | **31** |
| **TS2′** | nanoimprint/UV-NIL × filling time/feature filling/effective transport/flow model | 2 | 447 | **447** |
| **TS3** | **flow factor ∨ average flow model ∨ averaged Reynolds** × groove/ridge/rectangular/transverse roughness | 2 | 148 | **148** |
| **TS4** | transmissivity averaging ∨ arithmetic harmonic ∨ homogenization × groove/channel/aperture × numerical/comparison/error | 3 | 791 | **791** |

合计取回 **1417 条**，无取数缺口。

**TS3 是最有价值的一条**：它第一次把「流量因子 / 平均流量模型」这个**等价命名**纳入检索。
在 148 条里，同时含「流量因子语义」+「表面/润滑语义」的有 **70 条**。

---

## 二、三篇必须交代的新文献

### 2.1 ★★★ Teyssèdre, Gilormini & Régnier 2013 —— 最强近邻

> **Teyssèdre H., Gilormini P., Régnier G., "Limitations of Simple Flow Models for the Simulation of
> Nanoimprint", *International Polymer Processing* **28**(1), 72–78 (2013). DOI 10.3139/217.2673.**
> **✅ 2026-10-18 全文已取得**（用户提供作者博士论文 178 页，§3.1.4 即本文；归档 `raw/teyssedre2013_PhD_ArtsetMetiers.pdf`）。HAL 反爬问题因此绕过。**全文核出两处必须更正**（见 `FULLTEXT_VERIFICATION_20261018.md`）：① 几何确为**矩形截面线栅**（Fig. 3.4），参考解为 **Abaqus 平面应变 Stokes 有限元**，**$h_0/L=0.8$–$2.4$ 覆盖本课题区间**，$F/F_L=2$–$80$ 倍；② **该文只给力、不给 K，且为二维平面应变**（无法区分沿槽/跨槽），全文 0 次出现 permeability/anisotropy、0 次引 Patir–Cheng。

摘要原文关键句（逐句引用）：

> "assuming simplified flows may lead to **quite incorrect evaluations of these forces**, **even for simple
> periodic patterns and a Newtonian behavior**."
>
> "The mere use of the **classical result of the lubrication theory** does not account for the range of
> **thickness-to-width ratios** that may be involved, **especially at the beginning of the process**."
>
> "An improved squeeze model includes this effect, **but still underestimates the imprint force**."
>
> "Moreover, **finite element simulations demonstrate limitations of two more elaborate models** that are
> found in the literature."
>
> "two flow modes can be defined, **according to whether or not the polymer touches the mold sidewalls**."

**为什么它是最强近邻**：几何（简单周期图案）、流体（牛顿）、方法（**FEM 校核润滑理论及其改进版**）三项与我们重合。

**但它不是直接先例，四条区别都是实质性的**：

| | Teyssèdre 2013 | 本文 |
|---|---|---|
| **输出量** | **压印力**（imprint force） | **渗透率张量两个主分量** K∥、K⟂ 及其比值 |
| **对"方向性"的处理** | 未区分沿槽/跨槽 | 方向性即主题 |
| **失效判据** | 厚度/宽度比（thickness-to-width） | **深宽比 d/w 与间隙 h** 的完整映射 |
| **两种"模式"** | 聚合物**是否接触模具侧壁**（润湿/接触问题） | **全充液、始终接触**，因此只有一个模式 |

**对我们的三点后果**：

1. **它削弱了一句我们原本想说的话。** 我们此前想论证"矩形槽的解析路线已被证明走不通，所以只能 DNS"。
   Teyssèdre 2013 已经用 FEM 在 NIL 周期图案上做了这件事（虽然算力不算 K）。
   ⇒ **不能写"没人用数值校核过润滑理论"**。正确写法是："**已有人用 FEM 校核润滑理论对压印力的预测，
   但没有人给出方向性渗透率张量的误差**。"
2. **它其实支持我们的机制解释。** 它的"两种流动模式取决于聚合物是否接触侧壁"，
   与我们第 4 章"跨槽输运必须穿过槽口、槽顶是连通液层而非固壁"是同一个物理分岔的两个侧面。
   ⇒ 可以在机制段落里引它作旁证。
3. **它给了一个必须回答的问题**：既然 FEM 校核润滑理论已被做过，你的增量是什么？
   ⇒ 答案：**方向性**。他们的力是标量，我们的 K 是张量；标量误差可以是两个方向误差的加权平均，
   而加权平均会**掩盖方向性**（我们的 K∥ 误差 +10~205%，K⟂ 只有 +8~54%，按流通量加权后会显著变小）。

### 2.2 ★★ Wang & Hiroshima 2011 —— 实验侧的各向异性证据

> **Wang Q., Hiroshima H., "Anisotropic filling phenomenon of cavities in UV nanoimprint lithography",
> *J. Vac. Sci. Technol. B* **29**(6), 06FC19 (2011). DOI 10.1116/1.3662889. 被引 1. 全文未取得。**

摘要原文：

> "we observed a filling phenomenon that **differs from the well-reported isotropic filling**.
> In this newly observed anisotropic filling, a bubble shrinks at different rates **along its length and
> width directions of the rectangular complementary cavities**, with a **higher shrinkage rate along its
> length direction**."
>
> "The first phase of the resist-filling process is **anisotropic**, and the second phase is **isotropic**.
> Total complete filling time thus depends on the cavity dimensions, and the portion of filling time devoted
> to anisotropic filling **depends linearly on the cavity length**."

**为什么重要**：这是**实验直接观测到矩形凹腔的填充是各向异性的，且沿长度方向更快**——
与我们计算的 K∥ > K⟂（比值 1.09–15.45）方向完全一致。

**它不是先例**：纯实验、无模型、无 K、无误差分析。但它是**我们结论的实验旁证**。

> ⚠ **2026-10-18 15:30 更正（措辞范围收窄）**：原写"说明行业默认假设是各向同性"——**该推论过强，已撤回**。
> 原文只说 "differs from the **well-reported** isotropic filling"，即"文献中常被报道的各向同性填充"，
> 这是**对部分既有报道的描述**，不能等同于"整个领域都假设各向同性"。
> 且本文自己的引言已写明 Jain et al. [2] 引入的正是**各向异性**渗透率 $k_{xx},k_{yy}$，
> 若同时声称行业默认各向同性，将**自相矛盾**。
> **可用表述**：部分既有填充模型采用各向同性描述，而矩形腔实验显示实际填充存在显著方向性差异；
> 与此同时，采用各向异性 $\mathbf{K}$ 的模型**也从未检验过 $k_{xx},k_{yy}$ 的数值本身**——这才是本文的缺口。

**建议用法**（一句话，放在引言或讨论）：
> 矩形凹腔的填充在实验上已被观察到沿长度方向快于宽度方向（Wang & Hiroshima 2011），
> 但该工作未给出可传递的输运系数，也未量化各向同性假设的代价。

### 2.3 ★★ Lubrecht, ten Napel & Bosma 1988 —— 方向性粗糙度 vs 流量因子

> **Lubrecht A.A., ten Napel W.E., Bosma R., "The Influence of Longitudinal and Transverse Roughness on
> the Elastohydrodynamic Lubrication of Circular Contacts", *J. Tribol.* **110**, 421–426 (1988).
> DOI 10.1115/1.3261645. 被引 151.**

摘要全文只有四句，最后一句是关键：

> "The results are **compared with predictions from the flow factor method**."

**为什么重要**：标题即"纵向与横向粗糙度"，摘要明写与**流量因子法的预测作比较**——
这是"方向性 + 数值 vs 流量因子"的组合，与我们最接近的一类。

**区别**：EHL（弹性流体动力润滑）、**圆接触**、**滚动/剪切**驱动、粗糙度为纹理（amplitude + wavelength 参数化）而非周期矩形直角槽、输出是膜厚与压力而非 K。
**分级：近邻，不是先例。但它说明"横向 vs 纵向的差异"在摩擦学里 1988 年就被数值研究过——这一点必须在引言承认。**

---

## 三、另外五篇（分级与一句话理由）

| 文献 | 做了什么 | 与本文差在哪 | 分级 |
|---|---|---|---|
| **Schwendeman, Please & Tilley 2015**, *IMA J. Appl. Math.* **80**(1), 177–211, DOI 10.1093/imamat/hxt034 | 可压缩流、滑块与**运动图案粗糙面**之间；两尺度同质化；**系数由图案尺度上的 Stokes 流平均数值确定**；分别给出 **transverse 与 longitudinal** 两种情形（含 no-slip 与 slip） | 可压缩、滑块轴承、同质化（非解析闭合），输出是压力方程系数而非 K 张量；图案为"grooves"但形状未在摘要说明 | **N（较强）** |
| **Berger & Sadeghi & Krousgrill 1996**, *J. Tribol.* **118**, 137–146, DOI 10.1115/1.2837069，被引 115 | **FEM（Galerkin）** 离散修正 Reynolds + 力平衡；粗糙度用 **Patir–Cheng**；微凸体承载用 Greenwood–Williamson；研究载荷、材料渗透率、**槽宽/槽深**对啮合的影响 | 目标为扭矩/压力/啮合时间；槽深结论为"不影响"（在其模型内）；无 K、无 DNS | **N** |
| **Mitsuya & Koumura 1995**, *J. Tribol.* **117**, 430–436, DOI 10.1115/1.2831271 | 平均 Reynolds + 流量因子，因子来自 **Boltzmann 分子自由流**（稀薄气体）；比较纵向/横向/静止横向三种粗糙度 | 稀薄气体、磁头滑块、瞬态响应；非液体、非 K | **N（弱）** |
| **Chauhan, Palmieri & Bonnecaze 2009**, *JVST B* **27**(4), 1926–1932, DOI 10.1116/1.3147212 | S-FIL 特征填充：**被困气体经抗蚀剂扩散**的模型；结论"初始填充受压控制、其余受扩散控制" | 两相（困气 + 溶解），单相不适用；无 K | **X**（但与我们"不碰双相"的边界声明相关） |
| **Reddy, Schunk & Bonnecaze 2005**, *Phys. Fluids* **17**(12), 122104, DOI 10.1063/1.2140691 | 低毛细数界面**穿过矩形尖角特征**的二维模拟；界面在第一个尖角处 pinning、拉伸 | 有自由面（毛细驱动），界面动力学；无 K 张量 | **X**（但"尖角 pinning"是双相延伸时的关键机制，与 Concus–Finn 一条呼应） |

**TS1′/TS2′/TS3/TS4 合计直接先例：仍然为 0。**

---

## 四、一个必须写下的方法学发现：为什么 B 会漏掉这些

上一轮我说"不在 B 的池里不构成缺陷"。**这一轮找到了真正的原因，而且它是可诊断的**：

**本报告新增的 8 篇关键文献，8 篇全部不在 B 的 2055 条归档里。**（逐条按 DOI 核；见 §二、§三）

原因不是随机的，而是**同一个**：

> **B 的 18 组检索式，每一组都要求 `permeability` 出现。**
> 而这一整支文献谈的是 **lubrication / Reynolds / flow factor / filling**，
> 标题与摘要里**根本不出现"permeability"**。

逐条验证：

| 文献 | 标题里有 permeability 吗 | 所以 B 必然漏掉 |
|---|---|---|
| Teyssèdre 2013 | ✗（只有 nanoimprint + flow models） | ✓ |
| Wang & Hiroshima 2011 | ✗（anisotropic filling） | ✓ |
| Lubrecht 1988 | ✗（roughness + EHL） | ✓ |
| Berger & Sadeghi 1996 | ✗（grooved wet clutches） | ✓ |
| Mitsuya 1995 | ✗（flow-modified Reynolds） | ✓ |
| Schwendeman 2013 | ✗（homogenization + patterned rough surface） | ✓ |
| Chauhan 2009 | ✗（feature filling） | ✓ |
| Reddy 2005 | ✗（sharp features） | ✓ |

**⇒ 这是"检索锚定在单一术语上"的经典失效**，比"时间下限"和"标题须含几何词"更根本：
只要被检索对象的**同义术语体系不同**（渗透率 vs 润滑/流量因子/填充），单一锚词就必然漏。

**这就是为什么定理查新必须做「等价命名」这一路**——也解释了 Asta 指令里第 3 个补充问题
（"这个公式还有别的名字吗"）为什么是三条里最关键的。

**记账修法**：B 的**取数**无缺口（2470/2470）；B 的**覆盖**缺口定性为「单术语锚定」，
已由本轮 TS3/TS4 部分补齐（148 + 791 条，已归档）。**建议在论文的方法或补充材料中明确写出四条检索式的术语覆盖**，
而不是笼统说"检索了 OpenAlex"。

---

## 五、边界（逐条，不夸大）

1. **仍不是 WoS / Scopus**。OpenAlex 对 ASME 早期卷、SPE、部分会议论文覆盖弱。
   **本轮三篇关键文献（Teyssèdre、Wang & Hiroshima、Lubrecht）恰好都是这类**，
   说明 WoS 的人工检索仍有独立价值，**任务 C 不能算完成**。
2. ~~**Teyssèdre 2013 全文未取得**~~ → **2026-10-18 已取得全文**（作者博论）并完成核验：
   其几何**就是**矩形直角槽、参考解**就是** Stokes、间隙范围**覆盖**本课题，
   故「本课题无人做过」的说法**不再成立**。原 HAL 反爬情况仅作记录：
   `hal.science/hal-00799731/document`、`.../file/Gilormini-IPP2013.pdf`、landing page 三处
   均返回反爬页面（HTML，非 PDF）；SAM 仓库 `hdl.handle.net/10985/6860` 返回 "Cannot Connect to Server"。
   **分级仅基于摘要**。若它能被取得，**必须重读**——尤其"two more elaborate models"指哪两个、
   以及图案是否为直角矩形。
3. **Wang & Hiroshima 2011、Lubrecht 1988、Berger 1996、Mitsuya 1995、Schwendeman 2013 均只读摘要**（全部闭源）。
4. **TS1′ 只有 31 条**，因为叠加了 4 组 AND（含"permeability tensor|anisotropic|principal direction"），
   属于**高精度低召回**式；不要据此认为该方向文献少。
5. **TS4 的 791 条噪声极大**（`homogenization` 泛用），收紧后仅 18 条、无新增重要文献。
6. **仍未检索中文的「流量因子 / 平均流量模型」**（CNKI 至今只跑过 `沟槽 AND 渗透率` 一组）。
7. **直接先例 0；仍不得写"首次"。**

---

## 五·补　卷页核验说明（2026-10-18 13:20）

本报告初稿有**四处卷期页凭印象写错、一处年份写错**，已全部用 Crossref 逐条核对改正：

| 文献 | 初稿（错） | Crossref 实际 |
|---|---|---|
| Teyssèdre 2013 | 28(**2**) | **28(1), 72–78** |
| Wang & Hiroshima 2011 | 29(6), **06FC05** | 29(6), **06FC19** |
| Reddy 2005 | 17, **122105** | 17(12), **122104** |
| Schwendeman et al. | 无卷页，标 **2013** | **80(1), 177–211**；在线 2013-07-17，**印刷 2015** |
| Chauhan 2009 | 27, 1926 | 27(4), **1926–1932** |

**教训（这是本项目第四次同类错误）**：卷期页与文章号一律现查 Crossref，不凭记忆；
尤其 AIP 的六位文章号（06FC19 / 122104）尾数极易记错，且与相邻文章的号只差个位数。

---

## 六、小结（三句）

1. **新增 3 篇必须交代的近邻**：Teyssèdre 2013（FEM 校核润滑理论算力，最强近邻）、
   Wang & Hiroshima 2011（实验观测各向异性填充，我们结论的旁证）、
   Lubrecht 1988（纵/横粗糙度 vs 流量因子，1988 年就有）。
2. **查清了 B 漏检的根本原因**：18 组检索式全部锚定 `permeability`，
   而这一支文献用 lubrication / flow factor / filling 术语 ⇒ **单术语锚定失效**，
   不是时间下限或标题规则的问题（那两条只是次要因素）。
3. **定位需微调**：不能再说"没人用数值校核过润滑理论"，改说"**没人给出方向性渗透率张量的误差**"。
   直接先例仍为 0。
