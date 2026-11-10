# 两篇未取得全文的候选：摘要级证据存档（2026-10-18）

> 用途：这两篇是 A 任务（Jain 2017 引文追踪）清单里**唯一还缺全文**的两篇，均为 Springer 闭源。
> 本文件把**目前实际掌握的原文摘要**整段存下，并逐条标出「已知 / 未知」，
> 以便日后有人引用时**不必凭记忆**，也便于判断是否需要花钱买全文。

## 闭源状态核验（三处一致）

| 来源 | TCFD 38(1):39–59 | Microsyst. Technol. 32(12):195 |
|---|---|---|
| Crossref license | Springer Nature 标准条款（非 OA） | 同 |
| OpenAlex `oa_status` | **closed** | **closed** |
| Unpaywall `is_oa` / `oa_locations` | **false / []** | **false / []** |
| Semantic Scholar `openAccessPdf.status` | **CLOSED**（摘要亦被出版商 elide） | **CLOSED**（同） |

⇒ **无任何合法开放版本**。下表两篇的摘要均来自 **Springer 预览页**，不是二手转述。

---

## 1. Dewangan M.K. (2024)，TCFD **38**(1), 39–59

**Investigation of Stokes flow in a grooved channel using the spectral method**
DOI `10.1007/s00162-023-00679-6`｜投稿 2023-03-25，接收 2023-10-04，在线 2023-11-01，**印刷 2024 年 2 月**（故文献表记 2024）
被引 4（Crossref 计数）

### 摘要原文（Springer 预览页，逐字）

> Pressure-driven Newtonian fluid flow between grooved and flat surfaces is analysed with no-slip boundary conditions at walls. The effect of corrugation on the fluid flow is investigated using the mesh-free spectral method. **The primary aim of the present work is to develop an asymptotic/semi-analytical theory for confined transverse flows to bridge the gap between the limits of thin and thick channels.** The secondary aim is to calculate permeability with reference to the effect of wall corrugation (roughness) without the restriction of pattern amplitude. We performed mathematical modelling and **evaluated the analytical solution for hydraulic permeability with respect to the flat channel**. The Padé approximate is employed to improve the solution accuracy of an asymptotic model. The results elucidate that permeability always follows a decreasing trend with increasing **pattern amplitude** using the spectral approach at the long-wave and short-wave limits. The prediction of the spectral model is more accurate than the asymptotic-based model by **Stroock et al. (Anal Chem 74(20):5306, 2002)** and Padé approximate, regardless of the grooved depth and wavelength of the channel. **The finite-element-based numerical simulation is also used** to understand the usefulness of theoretical models. A very low computational time is required using the mesh-free spectral model as compared to the numerical study. **The agreement between the present model and the fully resolved numerical results is gratifying.** Regarding numerical values, we calculated the relative error for different theoretical models such as an asymptotic model, Padé approximate, and a mesh-free spectral model. **The spectral model always predicts the maximum relative error as less than 3 %, regardless of the large pattern amplitude and wavelength.** In addition, the results of the molecular dynamic (MD) simulations by **Guo et al. (Phys Rev Fluids 1(7):074102, 2016)** and the theoretical model by **Wang (Phys Fluids 15(5):1121, 2003)** are found to be quantitatively compatible with the predictions of effective slip length from the spectral model in the thick channel limit.

作者自报关键词：Effective slip length｜Hydrodynamic permeability｜Micro-patterning｜Padé approximant｜Spectral method｜Stokes flow

### 已知 / 未知

| | 内容 |
|---|---|
| **已知（摘要）** | ① 几何是 **corrugation / pattern amplitude / wavelength** + 对比 **Stroock et al. 2002**（该文的正弦波纹微通道是经典参照）⇒ **连续正弦波纹，非直角矩形槽**；② 方向是 **confined transverse flows**，即**跨槽**；③ 量是 **相对平通道的水力渗透率（无量纲比）**，且**不限制 pattern amplitude**；④ 与 **FE 全解**对比，报**最大相对误差 < 3%**；⑤ 覆盖 thin–thick 过渡区 |
| **未知（需全文）** | ① 是否也给了纵向（沿槽）分量与各向异性比；② 渗透率比的确切函数形式；③ 3% 是"谱方法 vs FE"还是"渐近模型 vs FE"（摘要措辞可两读）；④ 是否提及 Patir–Cheng |
| **分级** | **N（近邻）**。几何不同（正弦 vs 直角），故不构成直接先例 |

### 为什么这条其实对我们有利

它落在**与我们相同的间隙区间**（"thin and thick 之间"，对应我们 $h/w\approx0.21$–$1.04$），
唯一差别是**正弦连续壁 vs 矩形直角壁**。它的结论是**误差 < 3%**；而我们**跨槽**方向（与它同方向）的未修正误差是 **+8.1~+54.2%**（沿槽方向为 +10.3~+204.8%，方向不同，**不可与它直接并排**）。

> **两个数字并排放，"误差来自尖角"这个论点就不需要再论证了。**
> 建议在第 5 章或第 6 章讨论里这样写：
> 对光滑正弦波纹，半解析/渐近模型在全幅度范围、跨槽方向上相对有限元解的误差在 3% 以内 [TCFD]；
> 一旦把波壁换成矩形直角槽，**同方向（跨槽）**误差升至 8.1–54.2%（本文）。
> 差别不在幅度、不在间隙，而在**界面是否连续可微**。

---

## 2. Kuo W.-S., Tseng S.-C., Tsai M.-H. (2026)，Microsyst. Technol. **32**(12), 195

**Front evolution and localized redistribution during confined polymer micro-embossing under different nominal capillary-number conditions**
DOI `10.1007/s00542-026-06175-1`｜上线 **2026-10-16**

### 已知（Springer 预览页摘要 + Highlights）

- **侧视显微实验** + **二维 ANSYS Polyflow** 模拟；
- 材料：**UV 胶** 与一种高黏度对比材料；
- 观察对象：**受限沟槽内的瞬态填充前沿** 与 **局部重分配（localized redistribution）**；
- 变量：**名义毛细数**（不同档）；
- 结论方向：前沿形态的**趋势**，**定量验证有限**；**实验界面变形比模拟更剧烈（模拟低估幅度）**。

### 未知（需全文）

- 是否报告任何渗透率 / 输运系数；
- 是否有与解析闭合（Jain / 条纹平均）的定量对比；
- 沟槽截面形状（矩形？梯形？）。

### 分级

**N（近邻）**。它是**最新实验**，价值在于"连商用软件+实验对照都承认低估界面变形"这一句，
可用来论证**高保真 DNS 的必要性**；但它不给 K，故不威胁本课题。

---

## 结论

| | |
|---|---|
| 是否阻塞写作 | **否**。一篇几何不同（正弦），一篇是实验无 K |
| 是否改变"直接先例 0" | **否** |
| ⚠ 数字对应 | **只能拿跨槽 +8.1~54.2% 与它的 <3% 并排；205% 属沿槽，不可对撞** |
| 是否值得花钱买全文 | **TCFD 那篇值得**（它把我们的对比论证直接坐实）；Kuo 那篇**不急**（摘要够引一句） |
| 建议动作 | 若学校有 Springer 权限，优先下 TCFD；Kuo 可等审稿意见 |
