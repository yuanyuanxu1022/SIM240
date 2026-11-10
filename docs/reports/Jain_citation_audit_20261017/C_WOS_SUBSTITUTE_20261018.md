# 任务 C 的可执行替代：两条 TS 布尔式的移植执行（2026-10-18 13:20）

> ## 一句话声明
>
> **这不是任务 C 的完成，是它的可自动化部分。**
> 任务 C 的原定载体是 **Web of Science / Scopus**（校园网人工检索）。我没有这两个库的访问权限。
> 本报告做的是：把指令里那两条 TS 布尔式**原样移植到 OpenAlex**（改写成等价的 AND 组合，再用脚本复现布尔逻辑），
> 取全、筛尽、逐条分级。
>
> **WoS/Scopus 本身仍未检索，任务 C 仍记为「部分执行」。**

---

## 一、执行方式（可复现）

OpenAlex 的 `title_and_abstract.search` 对空格分隔的多个词是 **AND** 语义，不支持 `OR` 与截词符。
因此把指令中的两条 TS 式按**分配律展开**：

**TS1**：`("permeability" AND ("groove*" OR "corrugat*") AND ("validation" OR "error" OR "numerical"))`
→ 展开为 3 个几何词 × 3 个方法词 = **9 个 AND 查询**（groove / corrugat / trench × validation / error / numerical），合并去重。

**TS2**：`(("nanoimprint" OR "UV-NIL") AND ("permeability" OR "effective transport"))`
→ 展开为 2 × 2 = **4 个 AND 查询**，合并去重。

取数：`per-page=200` + `page=N` 分页取尽；随后在脚本里对 **标题+摘要** 重新施加原始布尔，作为校验。

复现命令示例：

```
GET https://api.openalex.org/works?filter=title_and_abstract.search:permeability%20groove%20numerical
    &per-page=200&page=1&select=id,doi,title,publication_year,primary_location,abstract_inverted_index
```

---

## 二、结果：命中量与噪声构成

| | 检索返回池（去重） | 布尔复现后 | 语义相关 | 直接先例 |
|---|---|---|---|---|
| **TS1** | 264 | **198** | ~19 | **0** |
| **TS2** | 100 | **58** | **2** | **0** |

### 2.1 TS1 的噪声：83% 与本课题无关

| 噪声类目 | 条数 | 占比 |
|---|---|---|
| 岩土/水文（seepage、trench cutoff、aquifer、levee、landfill） | 75 | 38% |
| 水力压裂/储层（shale、reservoir、EOR、coal） | 59 | 30% |
| 生物医学（drug、peptide、protein） | 15 | 8% |
| 电磁/器件（permeable base transistor、waveguide、ferrite） | 13 | 7% |
| **合计噪声** | **162** | **82%** |

**原因**：`permeability` 在英文里同时是"渗透率"和"磁导率"；`groove`/`trench` 在岩土里指"沟槽防渗墙""排水沟"。
这两组词叠加，命中的绝大多数是地下水流与储层工程。

### 2.2 TS2 的噪声：73% 是「透气模具」

| 噪声类目 | 条数 | 占比 |
|---|---|---|
| **gas-permeable template/mold**（透气模具，用于排气减缺陷） | 27 | **47%** |
| 光学/等离子体/超材料（把 NIL 当加工工具） | 15 | 26% |
| **合计噪声** | **42** | **72%** |

**原因**：`nanoimprint + permeability` 几乎全部命中"透气软模"这一支**材料工艺**文献——
那里的 permeable 指**模具本身透气**（让被 trapped gas 逸出），与"多孔介质渗透率"完全无关。

**这是本报告最实用的一条结论**：这两条 TS 式按原样在 WoS 里跑，会得到上百条岩土与模具工艺噪声，
**筛起来耗时间且容易把真正的候选埋掉**。§六给了改写版。

---

## 三、TS1 语义相关的 19 条，逐条分级

三行结论格式：**做了什么 / 与本课题差在哪 / 算不算先例**

### 3.1 唯一需要新引的一篇：Berger, Sadeghi & Krousgrill 1997

> **Berger E.J., Sadeghi F., Krousgrill C.M., "Analytical and Numerical Modeling of Engagement of Rough,
> Permeable, Grooved Wet Clutches", *J. Tribol.* **119**, 143–148 (1997). DOI 10.1115/1.2832450.
> 被引 96。**

| | |
|---|---|
| **做了什么** | 建"粗糙 + 透气 + 带槽"湿式离合器的啮合模型。**表面粗糙度按 Patir & Cheng (1978)**；摩擦材料渗透率按 Natsumeda & Miyoshi (1994)；**沟槽按"一种新的近似"**。把 Reynolds 方程与力平衡化简为膜厚-时间的**一阶单变量微分方程**，用线搜索反解设计点，给出 (F_app, Φ̂, A_red) 参数空间中的**啮合等值面** |
| **与本课题差在哪** | ① 参考解是**平均 Reynolds 方程**，无 DNS；② 沟槽是**平均化框架内的一种近似**，不是两个主方向张量的第一性计算；③ 目标是**啮合时间与设计等值面**，不是 K 的误差；④ 有摩擦材料**自身**的达西渗透率（多孔毡），与"槽形几何 K"是两个量 |
| **算不算先例** | **不算直接先例；是重要的近邻，且必须引用**：它是"把 Patir–Cheng 这一族闭合套到带槽表面上做工程计算"的**谱系起点**，被引 96，做离合器的审稿人一定知道 |

**为什么它重要**：中文侧 CNKI #34（2008 湿式离合器，Patir–Cheng + 矩形槽，只验扭矩）属于这条谱系的下游。
两篇合起来说明：**这一族闭合在摩擦学里被用于带槽表面已近三十年，校验对象始终是整机性能，从未是 K 本身。**

### 3.2 其余 18 条（简明分级）

| 序 | 文献 | 做了什么 | 差在哪 | 分级 |
|---|---|---|---|---|
| 1 | Dewangan & Persoons 2024, *J. Phys. D* **57**, 165002（EMHD 波纹槽道） | 谱方法算**波纹**槽道的 hydraulic permeability，与 **FEM 对比**，报谱法快 150–250 倍；放宽到"大振幅" | 连续波纹（undulating），含 Hartmann 数（MHD），非矩形直角槽 | **N** |
| 2 | Dewangan & Persoons 2024, *JPCS* **2766**, 012172（分层液-液，槽壁） | Fourier 理论 + FEM，算液-液两相在带槽微通道的流量与速度 | **两相**，且 streamwise（沿槽）方向，非跨槽张量 | **N（弱）** |
| 3 | Geng et al. 2026, *J. Laser Appl.* **38**, 012030（V 形微槽均热板） | 理论模型描述槽内液体输运，**有限元验证理论预测**；飞秒激光加工实测毛细行为 | **V 形**、**毛细驱动（有自由面）**、目标是毛细性能非 K 张量 | **N（弱）** |
| 4 | 2019, *Interfacial Phenom. Heat Transf.*（槽面液体吸入与蒸发） | 槽面/多孔层内的毛细吸入速率预测，含蒸发 | 两相（有蒸发界面），非压力驱动单相 | **X** |
| 5 | 2025, *Phys. Fluids*（两波纹曲壁间混合纳米流体） | 边界扰动法解析速度/温度，正弦波纹、变黏度、滑移 | 纳米流体 + MHD + 正弦，边界扰动（小幅值） | **X** |
| 6 | 2001, IMECE（电渗流，带槽微通道 μ-PIV vs 数值） | 实验与谱元法数值对比槽内电渗流速度场 | 电渗驱动（非压力驱动），比的是速度场非 K | **X** |
| 7 | 2005, *J. Tribol.*（多孔轴承 + 人字槽止推板） | 窄槽理论 + 达西定律算多孔轴承静动态特性 | 人字槽、窄槽理论、目标是轴承刚度阻尼 | **X** |
| 8 | 2009, *Tribol. Online*（多片湿式离合器径向/周向槽） | 修正 Reynolds + 传热，算温度与扭矩曲线 | 只到温度/扭矩，无 K | **X** |
| 9 | 2010, *J. Tribol.*（湿式离合器三维热流体，含槽面） | 三维热流体模型，径向槽与华夫槽 | 同上 | **X** |
| 10 | 2019, *Proc. IMechE Part J*（湿式多片离合器啮合，含槽） | **Navier–Stokes** + 接触力学 + 传热，槽区/非槽区区域分解耦合 | 用 N-S 但算的是**整机啮合过程**，槽作为几何细节而非张量；无 K 的误差分析 | **N（弱）** |
| 11 | 1976, AIAA（梯度孔隙热管吸液芯） | 沿轴变孔隙率使渗透率最大化，数值解最优孔隙分布 | 一维轴向优化，非槽形 K | **X** |
| 12 | 2014, *J. Mech. Electr. Eng.*（螺旋密封 + 填料密封，多孔介质建模） | CFD + 多孔介质模型，看渗透率随螺旋角/槽深/间隙变化 | 密封泄漏，非张量 K | **X** |
| 13 | 2018, SPE（API 法兰金属密封） | 接触应力 + 泄漏的解析模型，含表面形貌 | 密封泄漏 | **X** |
| 14 | 2025, *J. Tribol.*（多孔空气轴承，环形供气槽） | 两种流场模型（有/无环形槽），看轴承渗透率与供气压力影响 | 轴承动静特性 | **X** |
| 15 | 2025, *Energies*（环路热管多尺度吸液芯） | 孔隙网络 + 多孔介质，验证模型后算极限热流 | 孔隙网络，非槽形 K | **X** |
| 16 | 2026, *Appl. Therm. Eng.*（润湿梯度槽吸液芯） | 深度渐变微槽产生额外方向驱动力，保高渗透低阻力 | 毛细驱动、梯度润湿，非 K 张量 | **X** |
| 17 | 1994, *J. Phys. D*（波纹界面的电磁波反射） | 周期性波纹界面的反射率 | **磁导率**，与流体无关 | **X**（噪声） |
| 18 | 2024, *J. Phys. Conf. Ser.*（见 #2） | — | — | — |

### 3.3 TS2 的 2 条相关

| 文献 | 做了什么 | 差在哪 | 分级 |
|---|---|---|---|
| **Ban & Bonnecaze 2020**（已知，A 路线已收） | 多滴铺展 + **各向异性毛细压力边界**；文中明言"液滴沿图案方向流得更快，**不仅因为各向异性渗透率**，还因为模板纳米结构" | 补界面边界，不改体内 K，也不校验 K | **N**（既有记录不变） |
| 2016, UT Austin 学位论文（刚性/柔性基板 NIL 仿真） | 液滴铺展仿真，看滴径/布置误差/气体扩散/模板图案对产率与缺陷的影响 | 工程仿真，无 K 标定 | **X** |

**TS1 + TS2 合计直接先例：0。**

---

## 四、一个必须做的自我更正（针对我上一轮的表述）

上一轮我说"7 条相关文献里 6 条不在任务 B 的 2055 条归档里，说明 B 有覆盖缺陷"。

**这个推论方式不严谨，现在修正。**

本轮实测发现：**连 Ban & Bonnecaze 2020 也不在 B 的归档里**。
它是通过 **A 引文链**找到的，而不是 B 的关键词检索——这完全正常，因为它的标题
（*Optimal placement of droplets for UV nanoimprint lithography*）既不含 permeability 也不含 groove。

⇒ **"不在 B 的池里"本身不构成缺陷**。文献检索本来就是多路并行（A 引文链 / B 关键词 / C 人工 / D 独立工具），
任何单一路径都必然漏掉一部分，这正是要设四条路径的原因。

**真正成立的缺陷只有三条，且与"是否在池中"无关**：

| # | 缺陷 | 证据 | 性质 |
|---|---|---|---|
| 1 | **2005 年下限**排除了这一族的原始文献 | Patir & Cheng 1978 不在池中，因其早于 2005 | 检索参数问题 |
| 2 | **筛查规则要求标题含几何词**，滤掉了"平均化方法"类文献 | Lavrov 2023 **在池中**但被第一级滤掉（标题为 *Transmissivity Averaging in Fracture Flow…*） | 筛查规则问题 |
| 3 | **检索词缺少等价命名** | `flow factor`、`transmissivity`、`homogenization`、`averaging` 均未出现在 18 组式中 | 检索词问题 |

**修正后，二者应分开记账**：
- B 的**取数**：2470 条 100% 取回，无缺口；
- B 的**覆盖**：受上述三条限制，需补一轮（补检索词 + 去时间下限 + 改筛查规则）。
- 但**不能**用"A 找到的东西 B 没有"来指责 B。

---

## 五、顺带确认：Dewangan 系列第 4、5 篇仍是连续波纹

本轮新查到两篇 2024 年 **Dewangan & Persoons**（作者从 Datta 换成 Persoons）：

- *J. Phys. D* **57**, 165002（EMHD 波纹槽道）：摘要写 "undulating 2D microchannel"、"corrugation amplitude"、"pattern amplitude and wavelength"、
  "Fourier approach"、"Padé" 类语言；**与 FEM 对比并报 150–250 倍加速**。
- *JPCS* **2766**, 012172（分层液-液）：摘要写 "Fourier theory for a flow along streamwise grooves at the Stokes flow limit" + FEM 对比。

⇒ **该系列五篇（2020 JFM、2018 EJM-B、2023/24 TCFD、2024 JPD、2024 JPCS）全部为连续波纹，无一篇做矩形直角槽。**
但**"全部沿槽"这一句是错的，2026-10-18 14:05 更正**：

> ⚠ **更正：TCFD 38(1):39–59（2024）做的是跨槽方向，不是沿槽。**
> 其摘要原文："The primary aim of the present work is to develop an asymptotic/semi-analytical theory for **confined transverse flows**
> to bridge the gap between the limits of **thin and thick channels**."
> 并明确 "evaluated the analytical solution for **hydraulic permeability with respect to the flat channel**"、
> "permeability always follows a decreasing trend with increasing **pattern amplitude**"、
> "The spectral model always predicts the **maximum relative error as less than 3%**, regardless of the large pattern amplitude and wavelength."
>
> ⇒ 这篇实际上做的是：**正弦（连续）波纹 + 跨槽方向 + 受限通道 + 幅度不受限 + 相对平通道的无量纲渗透率 + 与 FEM 对比的误差量化**。
> **它落在我们 $h/w\approx0.21$–$1.04$ 的同一区间**（"thin and thick 之间"），几何只差在**正弦 vs 直角**。
>
> **这不威胁我们，反而把论点磨利了**：连续波纹上，半解析/渐近模型相对 FE 的误差**<3%**；
> 矩形直角槽上、**同一方向（跨槽）**、修正前，我们测到 **+8.1~+54.2%**。
> **两个数字放在一起（<3% 对 8~54%），"误差来自尖角"就不需要再论证了。**
>
> ⚠ **不要用沿槽的 +10~205% 与它并排**：那篇是 transverse（跨槽），方向不同，对撞即为错配。
这进一步支持我们已定的判断：**连续波纹有成套解析工具，矩形直角槽没有。**

同时这也给了一句可用的正面表述：**解析—数值的定量对比在这一支里是成熟做法**（连 Dewangan 自己都在与 FEM 比、并报加速比），
**所以"拿数值校核解析"不是我们的新颖点；我们把这件事做在矩形直角槽 + 有限间隙上，才是。**

---

## 六、给 WoS / Scopus 的改写版检索式（建议替换指令里的原式）

原式噪声 82% / 72%。建议改成下面的形式（WoS 语法，可直接粘贴）：

**TS1′（替代原 TS1）**
```
TS=(permeability OR "hydraulic conductance")
AND TS=(groove* OR corrugat* OR trench* OR "line and space" OR ridge*)
AND TS=(permeab* NEAR/5 (tensor OR anisotropic OR "two principal" OR "principal direction"))
AND TS=(numerical OR simulation OR "finite element" OR stokes OR "lattice boltzmann")
NOT TS=(aquifer OR levee OR landfill OR "cutoff wall" OR seepage OR subduction OR groundwater OR
        reservoir OR shale OR "hydraulic fracturing" OR drug OR cancer OR peptide)
```

**TS2′（替代原 TS2）**
```
TS=("nanoimprint" OR "UV-NIL" OR "imprint lithography")
AND TS=("filling time" OR "feature filling" OR "residual layer" OR "flow model" OR "effective transport")
NOT TS=("gas permeable" OR "gas-permeable" OR "gas permeable template" OR mold OR template material)
```

**新增 TS3、TS4（补 B 的覆盖缺口，这两条是关键）**
```
TS3: TS=("flow factor" OR "average flow model" OR "averaged Reynolds")
     AND TS=("groove*" OR ridge* OR "rectangular" OR "transverse roughness")
TS4: TS=("transmissivity averaging" OR "arithmetic harmonic" OR homogenization)
     AND TS=(groove* OR channel* OR aperture*) AND TS=(numerical OR comparison OR error)
```
**TS3、TS4 不要加时间下限**——Patir & Cheng 1978、Tripp 1983 都在 2005 年前。

---

## 七、边界（不夸大）

1. **不是 WoS/Scopus**。数据库不同，收录范围不同；OpenAlex 对工程会议与部分 ASME 早期卷的覆盖弱于 WoS。
2. **布尔式是移植，不是等价**。OpenAlex 无截词符，`groove*` 用 `groove` 近似；`corrugat` 的 9 个查询全部返回 0，
   说明 **OpenAlex 未做词干还原**，`corrugated` 可能未被 `corrugat` 命中——这是本次的一个真实漏检风险。
   （TS1 中 Dewangan 的 EMHD 波纹槽道能命中，是因为它同时含 `groove`。）
3. **仍是标题+摘要级判断**。除 Rom 2021（已读全文）、Ban 2020（已有全文）外，其余均只读摘要。
4. **Berger 1997 全文未取得**（ASME 订阅，OA=false）。"沟槽按一种新近似"这一句是摘要原话，
   其近似形式未知，**写入论文前须核全文**。
5. **未检索中文的"流量因子/平均流量模型"**（CNKI 仍只跑过 `沟槽 AND 渗透率`）。
6. **任务 C 仍记为部分执行**；**仍不得写"首次"**。

---

## 八、本轮的净增量（一句话）

> 新增 1 篇必须引用的近邻（**Berger 1997，被引 96**，Patir–Cheng 谱系套用到带槽表面的起点）；
> 确认 Dewangan 系列第 4、5 篇仍为连续波纹；
> 实测出原 TS1/TS2 两条检索式噪声达 **82% / 72%**，并给出四条改写式；
> **直接先例仍为 0**。
