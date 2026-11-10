# Ban & Bonnecaze 2021 期刊版吸收报告（与博士论文第 3 章对照）

**文献**：Yang H. Ban, Roger T. Bonnecaze, *Minimizing filling time for ultraviolet nanoimprint lithography with templates with multiple structures*, **J. Vac. Sci. Technol. B 39(1), 012601 (2021)**. DOI: 10.1116/6.0000648
**获取**：期刊正式版全文 12 页（用户下载，文件名被误存为 `ban2020.pdf`）。归档 `raw/ban2021_JVSTB_39_012601.pdf`。
**投稿/接收/在线**：2020-09-19 投稿 · 2020-11-10 接收 · 2020-12-16 在线 · 2021 年 1/2 月刊
**吸收日期**：2026-10-17
**与博士论文关系**：即博士论文第 3 章（该章首页脚注自认 "**Most of** this chapter has been published in JVST B, ... 39, 012601"）。

---

## 1 一个额外信号：Editor's Pick

期刊版首页标注：

> "**This paper was selected as an Editor's Pick**"

**用途**：说明这篇在编辑层面被认定为重要。引它来支撑"行业在用"是有分量的，不是随便一篇 AIP 论文。

---

## 2 与博士论文第 3 章的差异核对

| 检查项 | 结果 |
|---|---|
| 渗透率公式 | **完全一致**：式 (9)(10) 仍为 $k_{xx},k_{yy}$ 的 Jain 式，**一字未改** |
| 毛细压力边界 | 沿用 Ban 2020 的各向异性边界 |
| 主要内容 | 一致：多图案（平板 + 线槽、正交线槽、不同特征尺寸）区域布滴优化 |
| 第 3 章"most of"的含义 | 期刊版为取舍后的正式版本；未见新增的 K 验证内容，**差异不构成实质影响** |

⇒ **"most of" 的谨慎已核销**：期刊版没有比博士论文第 3 章多出任何关于 K 的内容。之前保留的疑问可以关闭。

---

## 3 本文与我们的三处关键关联

### 3.1 它把"正交图案"当成了真实场景 —— 而它只靠交换分量处理

原文 §III C："Different template orientations"：

> "A template composed of **two regions with orthogonal line space patterns** was also examined … the fluid flow in region 1 is perpendicular to region 2 and vice versa."

处理方式（§II）：

> "For **horizontal** line and space patterns, **kxx and kyy are reversed**."

**⇒ 他们只会处理 0° 和 90° 两种取向，方法是把 $k_{xx}$、$k_{yy}$ 对调（毛细压力项同样对调）。**

**这正好给我们 D3 的工作腾出位置**：
- 他们用"对调"处理 90°，等于**默认**旋转律成立；
- 我们用 DNS 在 **30°/45°/60°** 三个**任意角**上验证了完整旋转律 $K(\theta)=K_\parallel\cos^2\theta+K_\perp\sin^2\theta$ 与偏转角 $\tan\varphi=(K_\perp/K_\parallel)\tan\theta$，6/6 命中（<1e-4%）。

**论文可写**：

> 在多图案模板中，取向从 0° 变为 90° 时，现有做法是交换渗透率张量的两个主分量（Ban & Bonnecaze 2021）。这一做法隐含假定张量旋转律严格成立，但该假定此前仅被使用、未被检验。本文以 DNS 在 30°、45°、60° 三个任意取向上验证该旋转律（6/6，偏差 <1e-4%），从数值上确认了这一交换操作的合法性。

**这段话的分量**：把我们的"张量验证"从"顺带做的额外检查"升级为"**替行业做法提供了它一直缺的前提证明**"。

### 3.2 它再次确认 K 是输入而非被检验对象

全文 `relative permeability` **0 次**，`kr` **0 次**；`permeability` 出现处全为"用平均渗透率描述图案阻力"的引述性质。
渗透率公式在式 (9)(10)，此后**从未与任何真实流动对照**。

### 3.3 它把"多图案"这一真实工况摆上了台面 —— 对我们的修正适用范围是个提醒

他们研究三种模板：
1. 平板 + 线槽混合；
2. **正交**线槽（左竖右横）；
3. 线槽但**特征尺寸不同**（region 1 与 region 2 的 Δh 不同）。

第 3 种尤其要注意：**同一块模板上不同区域 d/h 不同**，而我们两个修正因子 $F_\parallel(d)$、$F_\perp(d)$ 是**逐点几何相关的**，不是全局常数。

**⇒ 对我们的直接含义**：把修正用于多区域模板时，**必须分区各算各的 $F$，不能用一个全局修正因子**。这是适用范围里应当明确的一条（当前 PPT 只写了 h、d/w 范围，未写"分区适用"）。

---

## 4 可引的具体句子（带页码）

| 用途 | 原文 | 位置 |
|---|---|---|
| 证明"行业在多图案场景仍在用该 K" | "…an effective permeability tensor K and is possible to use a lubrication analysis." | §II，p.012601-3 |
| 证明只处理 0°/90° | "For horizontal line and space patterns, **kxx and kyy are reversed**." | §II，p.012601-4 |
| 证明会面对多区域不同特征尺寸 | "…the fluid flow in region 1 is perpendicular to region 2 and vice versa." | §III C，p.012601-7 |
| 结论的核心主张 | "…it is necessary to **distribute the initial amount of resists in the form of droplets according to the template structure and density**." | §IV，p.012601-10 |
| Editor's Pick 佐证 | "This paper was selected as an Editor's Pick" | 首页 |

---

## 5 三篇 Ban/Jain 文献的完整分工（合并视图）

| | Jain 2017 (MEE 173) | Ban 2020 (JVSTB 38) | Ban 2021 (JVSTB 39) |
|---|---|---|---|
| 建立什么 | 有效渗透率张量 $k_{xx},k_{yy}$（含 h_avg） | 各向异性**毛细压力**边界 | 多图案**区域布滴**优化 |
| K 的处理 | **提出公式**，与实验定性比 | 原样沿用 | 原样沿用 |
| 是否验证 K | 否（只与实验定性比较） | 否 | 否 |
| 取向处理 | 0°/90° 交换 | 0°/90° 交换 | 0°/90° 交换 |
| 几何跨度 | 微米→纳米间隙 | H: 1000→10 nm（d/h: 0.1→10） | 同上 |
| 我们的关系 | 被标定的对象 | 提供失效区间证据 | 提供"旋转律被默认"的证据 |

**一页话总结**：这三篇构成一条清晰的四年链条——**公式提出（2017）→ 补界面边界（2020）→ 扩到多图案（2021）→ 但 K 本身始终是输入，从未被检验**。

---

## 6 需要更新到 PPT / 论文的清单

1. **P8（斜槽旋转角）** 可加一句："现有做法在 0°/90° 之间靠交换 $k_{xx},k_{yy}$ 处理，本文验证了任意角下该操作成立。"
2. **P7 适用范围** 可补"**分区适用**"：多区域模板中不同 d/h 需各自修正，不可用单一全局因子。
3. **论文引言** 的"四年链条"表述可以正式写入（比只引 Jain 2017 有力）。
