# 两篇全文核验报告 — 2026-10-18

> 用户提供 `patir1978.pdf`（6 页）与 `These_HT_compil.pdf`（178 页）。
> 已归档为 `raw/patir1978_JLubrTech_100_12-17.pdf`（sha256 `36651a0e…`）与
> `raw/teyssedre2013_PhD_ArtsetMetiers.pdf`（sha256 `cf1b55a5…`）。
>
> **一句话结论**：第一篇**关闭了一个悬了两轮的"未取得原文"**，并给出一个可直接写进正文的恒等式；
> 第二篇**推翻了引言里的一句话**，并使本课题的定位必须收窄。

---

## 一、Patir & Cheng 1978（[12]）：原文确认，且给出一条更强的说法

### 1.1 三项核实

| 待核 | 结果 |
|---|---|
| "流量因子由数值流动模拟得到"（此前只有二手转述） | **属实**。第 15 页原文：*"flow factors, which are obtained by numerical flow simulation"* |
| 参考解是什么（决定"甲类/乙类"归类） | **Reynolds 方程自身**。其模型问题为式(18)，*"solved for pressure using finite difference methods"*，在"小矩形轴承"单元上，约 10 个统计等价的随机粗糙面取平均，高度分布取高斯 |
| 沿流算术 / 横向调和，是否确为原文结论 | **属实，且比预期更强**（见 1.2） |

### 1.2 关键：式(23)(24) 是解析导出的，不是拟合的

第 15 页（PDF 第 4 页）原文：

$$\phi_x=\frac{1}{h^3E\!\left(\dfrac{1}{h_T^3}\right)}\quad\text{(Transverse)}\tag{23}$$

$$\phi_x=\frac{E(h_T^3)}{h^3}\quad\text{(Longitudinal)}\tag{24}$$

导出方式，原文写明：*"derived by stochastic process theory … obtained by **comparing the stochastic Reynolds equations** [3,6,8] **with the average Reynolds equation** defined in this paper"*。
其后："Simulation results for purely transverse and longitudinal roughness **agree well** with these graphs."
（图 5 中 γ=0 与 γ=∞ 两条曲线的标注为 "obtained from stochastic theory for transverse and longitudinal ridges"。）

**为什么这一条对我们重要**

$$\text{横向}=\frac{1}{E(1/h_T^3)}\ \Longleftrightarrow\ \text{跨槽调和};\qquad \text{纵向}=E(h_T^3)\ \Longleftrightarrow\ \text{沿槽算术}$$

对本课题的一维矩形槽（两个离散高度 $h$ 与 $h+d$、各占一半），这两式**精确退化为**
$K_\perp=2/(h^{-3}+h_g^{-3})/12$ 与 $K_\parallel=(h^3+h_g^3)/2/12$——正是我们式(1)的 $K_\perp$ 与 $K_\parallel$。

⇒ **在 Reynolds（润滑）近似成立的前提下，"沿槽算术 / 跨槽调和"不是一个近似选择，而是一条恒等式。**
因此我们与 DNS 的差值 **+10~205% 全部归因于 Reynolds 方程在直角处失效，与"取平均"这个动作本身无关**。

这句话可以正面写进论文，且比原先"我们沿用了 Jain 的闭合"要强得多：
**它把误差的来源唯一化了。** 建议在第 2 章方法或第 1 章补一句。

> ⚠ 边界：上述恒等式的前提是"界面可用单值高度 $h_T(x,y)$ 描述且速度剖面局部抛物线"。
> 直角槽的角点违反后者，这正是失效的入口；但不能因此说式(23)(24)"错"，只能说其**前提在此不成立**。

---

## 二、Teyssèdre 博士论文（[15]）：**推翻引言里的一句话**

### 2.1 这是什么

《热压印在超薄聚合物膜包覆硅片上的过程模拟》，Arts et Métiers ParisTech，2013-11-12 答辩，178 页。
参考文献表第 [67] 条即那篇 *Int. Polym. Process.* **28**(1), 72–78 的论文，**§3.1.4 就是该文的内容**
（原文："nous avons mené une première étude [67] en comparant les résultats des différents modèles simplifiés … à un calcul numérique utilisant la méthode des éléments finis sous Abaqus"）。

### 2.2 它做的正是我们以为没人做过的事

| 要素 | 该文 | 我们 |
|---|---|---|
| 几何 | **矩形截面线栅半周期**（Fig. 3.4，*"un réseau de lignes simples à section rectangulaire"*） | 矩形截面沟槽一个周期 |
| 参考解 | **Abaqus 平面应变 Stokes 有限元** | OpenLB 三维 DNS |
| 间隙范围 | $h_0/L=0.8,\ 1.6,\ 2.4$；横轴 $h/L$ 扫至约 2.4 | $h/w\approx0.21$–$1.04$ |
| 结果 | **$F/F_L$ 在 2 至 80 倍之间，间隙越大偏差越大**（初始约 7 倍；聚合物接触模顶后由 3 倍跃至 12 倍；完全填充于 $h/L\approx0.3$） | 修正前 +10~205%，修正后 10.5%/6.9% |
| 结论 | *"on ne peut pas utiliser des modèles d'écoulement simplifiés pour étudier les rapports de forme $h/L>0.1$"* | 同类失效，但给出可用的修正 |

**我们原来的句子（已删）**：

> "…this has been done for longitudinal and transverse roughness in elastohydrodynamic contacts [14], for a single surface defect [6], and for Gaussian random roughness [7],
> **but not, in the sources examined here, for periodic rectangular grooves at a finite gap.**"

这句话**与紧随其后的 [15] 引用自相矛盾**（[15] 做的正是这件事），是我此前只读摘要时留下的错误。

### 2.3 它没有做什么（我们剩下的位置）

逐字检索全文（去重音、去断字后统计）：

| 词 | 出现次数 |
|---|---|
| `permeability` / `perméabilité` | **0** |
| `anisotropy` / `anisotrope` | **0** |
| `isotropy` / `isotrope` | **0** |
| `porosity` / `porosité` | **0** |
| `transmissivity` | **0** |
| `Patir`、`Cheng` | **0** |

（对照：`moule` 212 次、`motif` 236 次，说明提取正常，零命中不是假阴性。）

加上结构性的限制：

1. **只给力，不给输运系数**。$F$ 是压印力（挤压流），不是 $\mathbf{K}$。
2. **二维平面应变 / 轴对称**（`déformation plane` 12 次、`axisymétrique` 74 次），
   线栅在平面应变下**本质上一维**，**因此无法区分沿槽与跨槽**——各向异性在它那里不构成变量。
3. **不与 Patir–Cheng 对话**（0 次引用），不知其闭合在摩擦学里的谱系。
4. 无修正公式；结论是"不能用"，我们是"错多少、怎么修"。

### 2.4 因此定位必须这样写（已改入 ¶3）

- **不能说**："矩形直角槽 + 有限间隙下的 Stokes 校核还没人做。" ——**已被做过**。
- **不能说**："没人意识到简化模型在这个区间会失效。" ——**已被量化过**（2–80 倍）。
- **可以说**："该文给出的是力，不是输运张量；没有 K 的两个主分量，也没有二者之比。"

并且必须主动加一句**防止两套数字被对撞**（已加）：
两个比值**不是同一个量**——他们是挤压流中聚合物必须拐进腔内，我们是定几何下的压力驱动通量；
但两者同源于润滑近似所遗漏的**角部流动**。

### 2.5 一个额外发现（对我们 R2-Z 主线有直接影响）

论文 **§4.4.4「Remplissage par capillarité」**（第 82–83 页）**已经做了毛细填充**：

- 几何：周期沟槽模具，**固定不动**，静接触角 **45°**，接触长度 50 nm；
- 方法：**带自由表面与移动三相点**的二维 Stokes 仿真（NanoNem），给了平衡曲率半径 $R$（式 4.17）与平衡压力 $p=-0.16$ MPa；
- 明确列出**该方法不能覆盖的两种情形**：自由面触底（脱附）、自由面碰到竖直侧壁（聚合物断裂）。

**含义**：本课题 R2-Z 的"毛细自吸填充"路线，在**二维、单沟槽、固定模具**上已有先例；
我们的增量在于**三维、多周期、液滴受限液区、以及给出 $F_g(t)$ 与输运张量的关系**。
这一点应写入第 3 章（方法）或第 7 章（范围），**不要在引言里声称"首次模拟毛细填充"**。

---

## 三、文稿改动清单（本轮已执行）

| 位置 | 改动 |
|---|---|
| 第 1 章 ¶3 | 删去"…but not … for periodic rectangular grooves at a finite gap"；改为先承认 [15] 已在本几何上以 Stokes 为参考做过校核（含 2–80 倍、$h/L\le2.4$、毛细填充），再收窄到"缺的是 K 的两主分量及各向异性" |
| 第 1 章 ¶3 | 新增一句区分两种比值（挤压力比 vs 定几何压力驱动通量），共同源于角部流动 |
| 参考文献 [12] | 标为**全文已核**；写入式(23)(24) 与"参考解为 Reynolds 自身" |
| 参考文献 [15] | 标为**全文已核（博士论文）**；写入几何、参考解、2–80 倍、0 次 permeability/anisotropy/Patir |
| 参考文献 [15] | 注明该论文自记年份 2012 与 Crossref 的 2013 冲突，以 Crossref 为准 |
| 写作说明 | "必须补的核"→ 改为"已核（两篇）" + "仍需补（[14]、[16] 摘要级）" |

**词数**：引言 2,397 → **2,509**（+112）。16 条引用全部被正文引用，无悬空。

---

## 四、状态

| | |
|---|---|
| [12] Patir & Cheng 1978 | ✅ 全文已核 |
| [15] Teyssèdre 2013 + 博论 | ✅ 全文已核（**定位已收窄**） |
| [14] Lubrecht 1988 | ⚠ 仍仅摘要（闭源） |
| [16] Wang & Hiroshima 2011 | ⚠ 仍仅摘要（闭源） |
| 直接先例 | **0**（不变） |
| "首次" | **仍不得写** |

**本轮改动的性质**：不是新增证据，而是**用全文纠正了一处由"只读摘要"造成的错误论断**。
这类错误只有拿到全文才能发现，说明"摘要级分级"必须标注为暂定。
