# SIM240 文献检索：单相沟槽输运、等效模型及 NIL 储备
检索日期：2026-10-16。用户范围：首篇真单相、显式真实沟槽、压力/体力驱动；界面、润湿、毛细与困气仅作为第二篇储备。

**主要结论：已找到显式数值计算与等效模型比较的先例，也找到直接针对 UV-NIL 线槽模板的各向异性渗透率模型。不能把“首次显式几何 DNS/LBM 对比等效模型”作为已成立的卖点。**

本报告按 D→A→B→C 整理。证据标为【全文核对】【摘要/片段核对】【推导】【未找到】。所有采用的文献结论均经联网检索；没有把仅凭记忆的公式或数值作为依据。部分全文受403、429、超时或付费限制，缺口直接列出。**未实际完成Ai2 Asta独立报告及WoS/Google Scholar人工查新，因此这不是穷尽检索或全球首次证明。**

## 开始比较前必须修正的定义

**真单相、没有界面，与部分填充率α之间还缺一个模型定义。** 全流体区域充满一种液体时，自然基准是α=1。若α<1，必须说明未填区域是什么及液体边缘的边界条件：设为固体会改变流道；规定自由表面仍然需要应力和运动学条件，即使不求气体也不能叫“没有界面”；规定液体截断面则结果依赖该人工边界。相同α还可能对应连续底膜、沿槽液柱或断开的液区，阻力一般不同。

**建议而非替用户定案：先以全充液K∥(h)、K⟂(h)作为首篇基准；若保留α，先冻结液区形状和边界族。** 非专业解释：知道装了几成水还不够，还要知道水连成什么形状、边上是什么。

“真实K”应表述为“给定连续介质模型与边界条件下、经过验证的K”。无滑移、牛顿黏度、刚性壁面等均是假设。固定间隙K不是完整下压过程，也不自动验证纳米尺度物性假设。

## D组：等效输运模型及已有比较

### D0. 单位、几何和公平比较

为防止不同论文都用K却单位不同，本报告用M表示用户的深度积分K：
\[
q_i=Q_i/W=-\frac{M_i}{\mu}\partial_i p,\quad
\bar U_i=q_i/H_{\rm ref}=-\frac{k_i}{\mu}\partial_i p.
\]
【定义/推导】
\[
M_i=H_{\rm ref}k_i,\qquad
\kappa_i=12M_i/H_{\rm ref}^{3},\qquad
R_i=\Delta p/Q_i=\mu\ell/(WM_i).
\]

| 符号 | 含义 | 单位 |
|---|---|---|
| Q、q | 总体积流量、单位投影宽度流量 | m³/s、m²/s |
| W、ℓ、H_ref | 投影宽度、宏观流向长度、明确指定的参考高度 | m |
| μ、p、∂p/∂x | 动力黏度、压力、压力梯度 | Pa·s、Pa、Pa/m |
| M、k、κ | 深度积分迁移率、Darcy渗透率、相对平板系数 | m³、m²、无量纲 |
| R | 总体水力阻力 | Pa·s/m³ |

体力驱动用G=ρa与压力梯度对应；周期单元内p_max−p_min不是宏观压降。所有平均必须用相同投影宽度、参考高度和流体域。非专业解释：先统一“每条通道”和“每单位宽度”的口径，否则所谓误差可能只是量尺不同。

【用户给定】P=240 nm，w=120 nm，d=100 nm，凸台间隙h=75 nm，f=w/P=0.5（无量纲），μ=15 mPa·s=0.015 Pa·s，ρ≈1000 kg/m³。
【推导】h+d=175 nm；平均高度h̄=h+fd=125 nm；h/P=0.3125、(h+d)/P≈0.7292、d/w≈0.8333（均无量纲）。1 nm²=10⁻¹⁸ m²，1 nm³=10⁻²⁷ m³。这里并非显然成立的“膜厚远小于图案尺度”。

### D1. 局部立方律 / Reynolds润滑近似与条纹平均

**1 名称、作者/年份/DOI。** 经典Reynolds框架；选用可核对的现代推导：Tavakol, Froehlicher, Holmes & Stone (2017), *Extended lubrication theory: improved estimates of flow in channels with variable geometry*, Proc. R. Soc. A 473, 20170234，[DOI 10.1098/rspa.2017.0234](https://doi.org/10.1098/rspa.2017.0234)，[作者稿](https://arxiv.org/pdf/1403.2343)。不是说该框架首次提出于2017年。

**2 公式原文。** 【全文及页面核对】作者稿v2，PDF第4页式(8)：
\[
\frac{dP_0}{dX}=-\frac{12}{H(X)^3}.
\]
这是无量纲单位通量形式。以下是【恢复量纲并自行推导】，不是冒称论文原式：
\[
q=-\frac{a^3}{12\mu}\frac{dp}{dx},\quad
M_\parallel^{\rm lub}=\frac{(1-f)h^3+f(h+d)^3}{12},
\]
\[
M_\perp^{\rm lub}=\frac{1}{12[(1-f)/h^3+f/(h+d)^3]}.
\]
推导：沿槽各条带压力梯度相同，流量相加；横槽各段通量相同，压降相加。该算术/调和平均在条纹Reynolds模型内部成立，不是任意三维Stokes流的通用严格界。

**3 符号表。** 原稿X=x/L₀、H=a/h₀、P₀=p₀/(μq₀L₀/h₀³)均无量纲；x、L₀、a、h₀单位m，q₀为m²/s，p₀为Pa。本文h、d、P单位m，f无量纲，M为m³，μ为Pa·s。

**4 前提。** 牛顿、不可压、无滑移、黏性主导；薄而缓变通道，局部抛物线速度；上述条纹式采用全充液、静止壁面、充分周期平均。高阶扩展理论不意味着最低阶公式自动适用于垂直台阶。

**5 定量边界。** 原稿引言以壁面斜率量级约0.1（无量纲）或更小描述常规缓变情形，不是统一误差保证。你的理想台阶局部斜率不有限；h/P=0.3125、高区/P≈0.7292也不是明显薄隙。未找到这组几何下已有百分比误差界。

**6 单位与换算。** 原式无量纲，恢复后M为m³，k=M/H_ref、κ=12M/H_ref³、R=μℓ/(WM)。

**7 复现。** 相同全充液周期沟槽、两静止无滑移固壁、面内周期，分别沿/横槽施加已知体力或压力梯度，取线性稳态、相同投影宽度的q。先在薄且缓变的几何内检查实现，再量化真实矩形槽外推误差。此公式无需DNS拟合参数。

**8 部分填充。** 不自带α<1界面模型；把d换成αd是改变流道，不自动代表部分充液。

**9 两句白话。** 它把流道切成小平板缝，再按并排或串联方式加总。槽边转弯和侧壁作用被简化，需要检查这些省略会造成多大偏差。

【代入给定尺寸的推导预测，绝非OpenLB结果】
\[
M_\parallel^{\rm lub}=[75^3+175^3]/24\ {\rm nm^3}
=2.4088542\times10^{-22}\ {\rm m^3},
\]
\[
M_\perp^{\rm lub}=\{6[75^{-3}+175^{-3}]\}^{-1}\ {\rm nm^3}
=6.5181588\times10^{-23}\ {\rm m^3}.
\]
比值3.6956052（无量纲）；平板75 nm的M为3.515625×10⁻²³ m³。**不能把3.6956写成真实各向异性已验证。**

### D2. Patir–Cheng平均流量因子 / 数值标定均质化

**1 名称、作者/年份/DOI。** Patir & Cheng (1978), *An Average Flow Model for Determining Effects of Three-Dimensional Roughness on Partial Hydrodynamic Lubrication*, J. Lubr. Technol. 100, 12–17，[DOI 10.1115/1.3453103](https://doi.org/10.1115/1.3453103)。原版全文公式页未取得。可核对的后续比较：Pusterhofer et al. (2018), *A Novel Approach for Modeling Surface Effects in Hydrodynamic Lubrication*, Lubricants 6,27，[DOI 10.3390/lubricants6010027](https://doi.org/10.3390/lubricants6010027)，[正式PDF](https://mdpi-res.com/d_attachment/lubricants/lubricants-06-00027/article_deploy/lubricants-06-00027.pdf)。

**2 公式原文。** 【全文及页面核对】Pusterhofer第4页式(9)、(11)、(12)：
\[
\chi_p=\frac{Q_{\rm rough}}{Q_{\rm smooth}^p},\quad
H=h^*/\sigma,\quad
\gamma=\lambda_{0.5,x}/\lambda_{0.5,y}.
\]
式(9)是该文采用并归于de Kraker路线的流量比，**不是Patir1978的式(9)**。【推导】静止壁面压力流对应Mᵢ=χp,ᵢ(h*)³/12。1978原文编号、完整经验系数和分段区间未取得，不伪造“原版拟合式”。

**3 符号表。** χp、H、γ无量纲；Q为m³/s；h*名义间隙、σ粗糙度均方根、λ₀.₅自相关降至一半的相关长度，均为m。这里σ不是表面张力。

**4 前提。** 固定表面形貌，压力流和剪切流贡献分开；经验系数依赖形貌统计和方向。可用周期代表域或统计面积/样本平均，不是所有版本都要求无限规则周期。首篇静止壁面只用压力因子；标题中的partial不能直接理解为槽内体积填充率α。

**5 定量边界。** Pusterhofer比较γ=9和1/9（无量纲）的高斯粗糙面。你的二级高度有【推导】σ=50 nm、h*=125 nm、H=2.5（无量纲），但同样H不等于同样统计形貌；无限直槽的沿槽相关长度也不能照搬有限γ。未找到EX240专属系数或通用误差界。

**6 单位与换算。** χp无量纲；M=χp(h*)³/12(m³)，k=M/H_ref(m²)。原文式(7)使用ν与除以密度的压力记号；不能将Pa压力代入却漏掉ρ。

**7 复现。** 比较既有经验系数需复现原形貌统计、名义间隙和压力边界。真实槽可独立标定两个χp，再检验未参与标定的高度/大尺度流动。由同一DNS反算χp再对回该DNS只证明定义自洽，没有独立预测力。

**8 部分填充。** 上述比值不提供液体饱和度闭合；空化、接触或缺液扩展需另查具体方程。

**9 两句白话。** 它给平板公式乘一个“表面修正系数”。系数用错表面，或者用同一组数据既拟合又检验，都不能证明预测可靠。

### D3. 全润湿起伏壁面的谱/小振幅渗透率张量

**1 名称、作者/年份/DOI。** Dewangan & Datta (2020), *Effective permeability tensor of confined flows with wall grooves of arbitrary shape*, JFM891,A12，[DOI 10.1017/jfm.2020.134](https://doi.org/10.1017/jfm.2020.134)，[出版社全文](https://www.cambridge.org/core/journals/journal-of-fluid-mechanics/article/effective-permeability-tensor-of-confined-flows-with-wall-grooves-of-arbitrary-shape/089D6608B5CF065BAC9B1C4F7D42FBCF)。

**2 公式原文。** 【全文HTML核对】较大H形式(3.11)、(3.21)：
\[
\tilde K_\parallel=(1-6\alpha^2HS_1)+12\alpha^2S_2+e.s.t.(H)+o(\epsilon^2),
\]
\[
\tilde K^\perp=(1-12\alpha^2HS_1)+12\alpha^2S_2+e.s.t.(H)+o(\epsilon^2).
\]
配套(3.9c)、(3.6d)：
\[
S_1=\sum_{n=1}^{\infty}n|g_n|^2,\qquad S_2=\sum_{n=1}^{\infty}|g_n|^2.
\]
任意有限H需回原文(3.8)、(3.18)及定义，不能删掉余项就叫普适精确解。

**3 符号表。** g零均值周期形状、gₙ傅里叶系数、n正整数均无量纲；e起伏幅度、L周期、原文h均值面至平壁距离，均为m。H=2πh/L、ε=2πe/L、原文α=e/h、S₁、S₂、K均无量纲。**原文α不是填充率**。e.s.t.为随H指数减小的项，o为渐近余项，均不代表给定百分比误差。

**4 前提。** 周期一维起伏壁+平壁，全充液，两壁无滑移，稳态Stokes；ε作为小参数，相关形状谱须收敛。不是气垫条纹模型。

**5 定量边界。** 第4节明确用显式FEM比较并讨论依赖H、形状的5%误差范围。尤其指出：**方波gₙ∝1/n使S₁发散，(3.11)/(3.21)无法用于该形状。** 对你的±1二级形状，【推导】e=50 nm、原文h=125 nm、L=240 nm，ε≈1.309、H≈3.272、α=0.4（无量纲）；还有非小参数问题。

**6 单位与换算。** 原文K=Q/Q₀无量纲；k=h²K/12(m²)，M=h³K/12(m³)。这里的h不能误填凸台间隙75 nm。

**7 复现。** 先复现原文平滑波形/三角波、指定H和ε，两方向周期全充液Stokes。实际矩形槽须独立确定圆角/平滑形貌后再判断适用性；不能任意截断发散级数制造“预测值”，也不能用其未承诺的方波域反驳模型。

**8 部分填充。** 不处理物理α<1；原文相对粗糙度α与它无关。

**9 两句白话。** 它把波纹分解成许多简单波，算波纹对阻力的影响。直角台阶会让这套展开失效，标题里的“任意形状”仍有数学限制。

### D4. 薄通道局部滑移与均质化

**1 名称、作者/年份/DOI。** Feuillebois, Bazant & Vinogradova (2009), *Effective slip over superhydrophobic surfaces in thin channels*, PRL102,026001，[DOI 10.1103/PhysRevLett.102.026001](https://doi.org/10.1103/PhysRevLett.102.026001)，[作者稿](https://arxiv.org/pdf/0808.1393)。

**2 公式原文。** 【全文及页面核对】作者稿第2页式(1)、(2)的case I：
\[
\mathbf U=-\frac{k(x,y)}{\mu}\nabla p,\qquad
k(x,y)=\frac{h^2}{12}\left(1+\frac{3\beta(x,y)}{1+\beta(x,y)}\right).
\]
同页“Anisotropic textures”未编号条纹关系：
\[
k_\parallel=\phi_1k_1+\phi_2k_2,\qquad
k_\perp=(\phi_1/k_1+\phi_2/k_2)^{-1}.
\]

**3 符号表。** U深度平均速度(m/s)，p(Pa)，μ(Pa·s)，h平面间隙和b局部Navier滑移长度(m)，β=b/h无量纲；k、k₁,₂为m²；φ₁,₂边界面积分数、无量纲且和为1。

**4 前提。** h≪条纹尺度L，低惯性牛顿流，一壁无滑移、另一壁规定局部滑移；平面液气界面是理想化，不求气体或弯月面演化。条纹平均不是全润湿真实侧壁的直接求解。

**5 定量边界。** h/L≪1，无统一截止保证；case I且b≥0，【推导】h²/12≤k≤h²/3，增强至多4倍（无量纲），只限此平面边界模型。你的h/P=0.3125且没有气垫，不能直接套用。

**6 单位与换算。** k(m²)、M=hk(m³)、κ=12k/h²；b(m)本身不是渗透率。

**7 复现。** 平直薄狭缝，交替规定b₁/b₂，一侧无滑移，周期边界，沿/横条纹压力驱动。真实沟槽要先有独立沟槽→滑移映射并固定参考面，才可评价等效误差。

**8 部分填充。** φ₂是面积比例，不是槽体积填充率；无通用α修正。

**9 两句白话。** 它把表面分成“更滑”和“更不滑”的区域。底下有气垫的滑面，与充满液体且侧壁不滑的槽不是同一种条件。

### D5. 厚通道极限的有限滑移条纹公式

**1 名称、作者/年份/DOI。** Belyaev & Vinogradova (2010), *Effective slip in pressure-driven flow past super-hydrophobic stripes*, JFM652,489–499，[DOI 10.1017/S0022112010000741](https://doi.org/10.1017/S0022112010000741)，[正式排版作者PDF](https://nanofluidics.phys.msu.ru/paper/jfm20102.pdf)。

**2 公式原文。** 【全文核对】期刊第494页式(2.22)：
\[
b_{\rm eff}^{\parallel}=\frac{L}{\pi}
\frac{\ln[\sec(\pi\phi_2/2)]}
{1+\frac{L}{\pi b}\ln[\sec(\pi\phi_2/2)+\tan(\pi\phi_2/2)]}.
\]
第496页式(2.35)：
\[
b_{\rm eff}^{\perp}=\frac{L}{2\pi}
\frac{\ln[\sec(\pi\phi_2/2)]}
{1+\frac{L}{2\pi b}\ln[\sec(\pi\phi_2/2)+\tan(\pi\phi_2/2)]}.
\]

**3 符号表。** L周期、b滑移区局部滑移长度、b_eff有效滑移长度、H通道高度均为m；φ₂为无量纲滑移面积比例。

**4 前提。** 平面无滑移/有限滑移条纹，Stokes压力流，H≫L；相关推导还使用b相对远壁距离足够小的近似。公式与相应数值解比较过，不是任意高度精确式。

**5 定量边界。** H/L≫1；你的平均高度/P≈0.5208不属此极限。固定0<φ₂<1、b/L→∞时，【推导】b_eff,∥/b_eff,⟂→2（无量纲），不表示M比必为2。

**6 单位与换算。** 输出m。若已合法替代成一侧均匀滑移的平板，【一维Stokes推导】kⱼ=H²[1+3bⱼ/(H+bⱼ)]/12，Mⱼ=Hkⱼ。此换算不能挽救将厚通道b直接用于窄缝的错误。

**7 复现。** 平面周期条纹给b或0，另一壁无滑移，增大H/L核查厚通道极限，再比较两方向。气垫模型与真实全充液槽不能未经边界映射直接互判错误。

**8 部分填充。** φ₂不是液体体积分数，无本研究α闭合。

**9 两句白话。** 它给出条纹滑面在两个方向上看起来有多滑。另一面墙靠近后，原来的滑动效果不能照搬。

### D6. 最直接的NIL先例：必须补全文

Jain, Spann, Cochrane, Schunk & Bonnecaze (2017), *Fluid flow in UV nanoimprint lithography with patterned templates*, Microelectronic Engineering173,62–70，[DOI 10.1016/j.mee.2017.04.001](https://doi.org/10.1016/j.mee.2017.04.001)，[出版社摘要及片段](https://www.sciencedirect.com/science/article/pii/S0167931717301296)。

【摘要/章节片段核对】线槽模板的各向异性渗透率、多滴融合和非填充区域是明确主题。**尚未取得渗透率公式编号、完整参数和验证章节，所以不能把D1自行推导式冒充Jain原式，也不能声称已经复现。** 此文应用最贴近，优先级应高于超疏水体系。现有片段不足以判断它已完成与你完全相同的独立三维DNS误差图。
白话：已有人用方向性阻力研究同类压印；要先查清他怎样算阻力，才能说明你补了什么。

### D6补充：同团队公开会议稿，帮助界定争议但不能替代期刊全文

Ban, Jain & Bonnecaze (2018), *Optimizing Filling of Anisotropic Templates in UV Nanoimprint Lithography*，19th International Coating Science and Technology Symposium，稿号ISCST-20180919AM-B-PD4，[会议官网原始6页稿](https://www.iscst.com/wp-content/uploads/2019/01/ban.etal2018.OptimizingFillingAnisotropic.Paper_.ISCST-20180919AM-B-PD4.p.pdf)。**未找到DOI，首页明确标注Unpublished；不能冒充同行评议期刊论文。**

【原文公式，第3页式(2)，已目视核对】
\[
\mathbf u=-\mathbf K\cdot\frac{\nabla p}{\mu}.
\]
u是深度平均速度(m/s)，p压力(Pa)，μ黏度(Pa·s)；据此【量纲推导】这里K是m²口径，而非本项目深度积分的m³口径。第4–5页将部分模型/实验差异与毛细压力边界近似联系起来，提出用Surface Evolver改进；这是作者的解释和后续工作方向，**不是已经独立证明K错误**。这份稿未补齐Jain2017的K闭合公式。

白话：这类压印模型同时需要“流动阻力”和“液面拉力”；算错液面拉力，也能出现与实验不符，不能全归咎于阻力。

继续追查还定位到Jain2016博士论文题名 *Simulation of UV Nanoimprint Lithography on Rigid and Flexible Substrates*；本轮未取得其全文，UT公开机构库检索接口返回403，不引用其公式。该线索仅用于后续找原始资料。

### D7. 是否已有显式几何数值校核等效模型？

**有，证据足以否定宽泛“没人做过”，但不等于这些文献已经覆盖EX240。**

| 原始研究 | 已核实内容 | 限制 |
|---|---|---|
| Dewangan & Datta2020（D3） | 第4节显式FEM Stokes对比解析张量，讨论有限高度、远壁近似和润滑平均差异 | 波形不同，不提供你的现成误差 |
| Dewangan & Datta2018，*Flow through microchannels with topographically patterned wall: A spectral theory for arbitrary groove depths*，Eur. J. Mech. B/Fluids70,73–84，[DOI 10.1016/j.euromechflu.2018.02.004](https://doi.org/10.1016/j.euromechflu.2018.02.004) | [出版社](https://www.sciencedirect.com/science/article/pii/S0997754617305010)介绍沿正弦槽谱解与FEM/近似比较 | 本轮摘要/引言级，不是矩形双方向全验证 |
| Pusterhofer2018（D2） | 图6等比较解析粗糙几何的Navier–Stokes计算与Patir–Cheng系数 | 其设置包括亚网格模型，不能严格称为无模型DNS；表面为高斯粗糙面 |
| Brenner, Al-Zoubi, Mukinovic, Schwarze & Swoboda2007，*Numerical Simulation of Surface Roughness Effects in Laminar Lubrication Using the Lattice-Boltzmann Method*，J.Tribol.129,603–610，[DOI 10.1115/1.2736452](https://doi.org/10.1115/1.2736452) | 书目确认；摘要线索涉及LBM、真实粗糙形貌、流量因子 | 未取得原始全文，不采用具体误差或公式；须追查的LBM先例 |
| Belyaev2010（D5） | 条纹滑移近似对比相应Stokes数值解 | 边界不同，不是全润湿沟槽验证 |

Brenner书目还见Pusterhofer参考文献20和[作者机构出版目录](https://www.itm.tu-clausthal.de/fileadmin/Sites/ITM/Images/Abteilungen/Abteilung_Str%C3%B6mungsmechanik/Forschung/literatur2026-1.pdf)。
白话：比较方法早已有先例，新文章需要新增几何规律、误差边界或物理解释。

### D8. 冲突如何裁决？

D1与D3可在有限间隙给出不同预测；比较应服从相同几何、边界和收敛后的显式解。D4薄通道与D5厚通道不同，不构成互相否定。D2的流量因子定义与特定高斯形貌经验系数也必须区分。气垫滑移与全充液沟槽更不能混成一个物理问题。白话：地图适用的地区不同，不能因为不适合这条路就判它画错了。

**三个关键发现**

1. 显式数值/流量因子比较已有FEM和LBM先例，宽泛“首次”不成立。
2. Jain2017是最贴近NIL的模型，完整公式页是首要缺口。
3. 实际矩形槽并非明显薄隙，谱小扰动还受到垂直台阶限制。

**实际使用过的核心检索词（含题名定向搜索）**：
grooved channel effective permeability tensor no slip fully wetted DNS；
effective permeability tensor confined flows wall grooves arbitrary shape；
Flow through microchannels topographically patterned wall spectral theory arbitrary groove depths；
Patir Cheng flow factors Navier Stokes comparison；
Numerical Simulation Surface Roughness Laminar Lubrication Lattice Boltzmann；
Extended lubrication theory variable geometry；
effective slip superhydrophobic thin channels；
pressure driven flow super hydrophobic stripes；
Fluid flow in UV nanoimprint lithography with patterned templates；
上述题名/DOI与pdf、OSTI组合；Akhilesh Jain dissertation nanoimprint 2016 Texas library；Simulation of UV Nanoimprint Lithography on Rigid and Flexible Substrates；Optimizing Filling of Anisotropic Templates in UV Nanoimprint Lithography。
公开ScienceDirect页面已查，不等于完成其数据库的穷尽人工检索。

**未找到/未完成**：这组EX240几何的已发表完整误差矩阵；Jain2017及Patir1978公式全文；本几何α<1通用闭合；各模型统一误差界；Asta交叉和传统数据库人工查新。


## A组：第二篇毛细、润湿与困气储备

### A1. 不同壁面接触角的驱动条件

Ouali et al. (2013), *Wetting considerations in capillary rise and imbibition in closed square tubes and open rectangular cross-section channels*, Microfluidics and Nanofluidics15,309–326，[DOI 10.1007/s10404-013-1145-5](https://doi.org/10.1007/s10404-013-1145-5)，[作者机构稿](https://irep.ntu.ac.uk/9177/1/213251_Microfluidocs-final%20version-10.1007_s10404-013-1145-5%5B1%5D.pdf)。【原文片段核对】明确用表面自由能处理不同壁面接触角。其一般式的原始页码/编号本轮未完整核实，以下明确为**力平衡推导**，不冒称照抄。

长直封闭矩形通道，宽w、高H；液体沿轴向推进，四壁接触角为θt、θb、θl、θr，从液体侧量。σ表面张力(N/m)，Δp_cap=p_g−p_l为正吸力(Pa)。忽略重力、入口、钉扎与气体压缩。

【推导第1步】沿轴向毛细力为
\[
F_\sigma=\sigma[w(\cos\theta_t+\cos\theta_b)+H(\cos\theta_l+\cos\theta_r)].
\]
【第2步】除以截面积wH：
\[
\Delta p_{\rm cap}=\sigma\left[
\frac{\cos\theta_t+\cos\theta_b}{H}
+\frac{\cos\theta_l+\cos\theta_r}{w}\right].
\]
【第3步】令其为零，解顶壁临界角：
\[
\theta_{t,c}=\arccos[-\cos\theta_b-(H/w)(\cos\theta_l+\cos\theta_r)].
\]
反余弦参数须在[-1,1]；超出时回到不等式判断可吸入区间。四壁同角时净驱动临界为90°；侧壁可忽略的两平板要求cosθt+cosθb>0。**这是该理想通道净驱动条件，不是填充必成功的条件。**

你的Z向入槽并非长直矩形管的轴向吸液；100 nm槽深、175 nm槽区总高和75 nm凸台膜厚不可互换。槽口转角、底板液膜、空气通路需单独分析。
白话：四面墙可能有的拉水、有的阻水，要合起来看；即使有净拉力，也可能在槽口卡住或被空气挡住。

### A2. Concus–Finn条件：角落与整槽填满不同

Concus & Finn (1969), *On the behavior of a capillary surface in a wedge*, PNAS63,292–299，[DOI 10.1073/pnas.63.2.292](https://doi.org/10.1073/pnas.63.2.292)，[原始研究记录](https://pubmed.ncbi.nlm.nih.gov/16591761/)。

【原条件以不冲突符号转写】楔形内夹角β、两壁同一平衡接触角θ：
\[
\theta+\beta/2<90^\circ.
\]
常见原文记号以α表示半角，写成θ+α<90°。用户的θ<90°−α/2仅在α指**完整楔角**时正确；不能同时指填充率。矩形内角β=90°，因此θ<45°，讨论的是理想尖角中的角隅润湿/延伸，**并非θ≥45°就不能填满矩形通道**。有限圆角、两壁异角和接触角滞后的完整修正式本轮未核实，不推测。

白话：液体可能先沿墙角拉出细线；墙角细线出现，与整槽灌满不是一回事。

再给一个【表面能推导】说明几何差别：上方开放、同角矩形槽，假定液柱填满截面且前进时生成宽w的新液气面，
\[
\Delta F/\Delta\ell=\sigma[w-(w+2d)\cos\theta].
\]
需cosθ>w/(w+2d)才降低能量。w=120 nm、d=100 nm时，临界角arccos(120/320)≈67.98°。**此数为开放槽理想模型推导，不能用于本装置Z向入槽，也不与角隅45°条件冲突。**

### A3. Lucas–Washburn标度、NIL建模与Ca

【由黏性阻力和体积守恒推导】
\[
Q=A(k/\mu)(\Delta p/\ell),\quad Q=A\,d\ell/dt
\Rightarrow \ell^2-\ell_0^2=(2k\Delta p/\mu)t.
\]
A为m²，k为m²，ℓ为m，t为s，Δp为Pa，μ为Pa·s。两无滑移平板、间隙a、同接触角、纯毛细且忽略初始长度时：
\[
k=a^2/12,\quad\Delta p=2\sigma\cos\theta/a,\quad
t_{\rm fill}=\frac{3\mu\ell_{\rm fill}^{2}}{\sigma a\cos\theta}.
\]
即时间与长度平方成正比，与间隙和σcosθ成反比。你的Z向深宽比100/120≈0.83（无量纲），不是长管极限；入口和困气可能决定过程。**未给σ和接触角，不估算你的填充秒数。**

可核查原始研究：
- Reddy & Bonnecaze (2005), *Simulation of fluid flow in the step and flash imprint lithography process*, Microelectronic Engineering82,60–70，[DOI 10.1016/j.mee.2005.06.002](https://doi.org/10.1016/j.mee.2005.06.002)。修改润滑/界面推进路线，讨论压印流动；不是本几何的三维DNS。
- Reddy, Schunk & Bonnecaze (2005), *Dynamics of low capillary number interfaces moving through sharp features*, Physics of Fluids17,122104，[DOI 10.1063/1.2140691](https://doi.org/10.1063/1.2140691)。尖角界面推进与困气；本轮核对书目/摘要，不引用未取得的方程或数值阈值。[作者出版清单](https://sites.utexas.edu/bonnecazegroup/publications-2/)可交叉核对两篇。

Ca=μU/σ（无量纲）比较黏性与表面张力，不能单独证明无须外压。还要比较实际局部外压差与毛细压差，并区分模具总载荷/面积与局部液体压差。
白话：细通道吸液会越走越慢；短盲槽若卡住液面或封住空气，简单时间公式就会漏掉关键因素。

### A4. 毛细主导是否无需外压？

【厂家原文】[mr-NIL210官方页](https://microresist.de/en/produkt/mr-nil210-series/)列推荐压印压力 **>100 mbar**。【换算】100 mbar=0.1 bar=10 kPa=10⁴ Pa，用户换算正确。

同厂家[应用资料](https://microresist.de/?jet_download=9111a38432d1913c22efd047b1175e65869795ee)也展示无外加压力案例；[原始材料研究](https://eprints.gla.ac.uk/146077/7/146077.pdf)讨论PDMS模板下的毛细填充。这不必然矛盾：标准推荐与特定示范的贴合、模板和排气条件可能不同。**不能把>100 mbar推成全部J-FIL通用需求，也不能用某个毛细吸液案例否定厂家工艺。**
白话：毛细负责吸进细槽，外压还可能负责贴合、排液和克服不平整；两者可以同时存在。

### A5. 困气与气泡缺陷

| 原始研究 | 已核实意义 | 未核实 |
|---|---|---|
| Liang, Tan, Fu & Chou (2007), *Air bubble formation and dissolution in dispensing nanoimprint lithography*, Nanotechnology18,025303，[DOI 10.1088/0957-4484/18/2/025303](https://doi.org/10.1088/0957-4484/18/2/025303)，[作者机构记录](https://collaborate.princeton.edu/en/publications/air-bubble-formation-and-dissolution-in-dispensing-nanoimprint-li/) | 摘要级：气泡形成与溶解，依赖尺寸、压力、溶解性与膜厚 | 本胶/本几何的临界泡径和秒数 |
| Cochrane, Tjiptowidjojo, Bonnecaze & Schunk (2018), *Multiphase model for nanoimprint lithography*, Int.J.Multiphase Flow104,9–19，[DOI 10.1016/j.ijmultiphaseflow.2018.03.014](https://doi.org/10.1016/j.ijmultiphaseflow.2018.03.014)，[出版社](https://www.sciencedirect.com/science/article/abs/pii/S0301932217305487) | 摘要/片段级：多相降阶模型、气体与溶解；是第二篇相对渗透率思路的线索 | 完整闭合公式及本参数适用性 |

【分析】至少区分前沿合围而无通路、尖角跨越留下口袋、固化前能否溶解。可比较排气/溶解与固化时间，但没有取得通用数值门槛。白话：空气若被封住，只能排出去或溶进胶里；是否来得及要看这两个过程的速度。

**三个关键发现**

1. 非对称润湿需加总各壁贡献，不能只看上模具角度。
2. 45°、开放槽例子的67.98°、同角封闭管90°讨论的是不同几何与现象。
3. 厂家>100 mbar已核实，是否需外压仍应按实际工艺判断。

**实际检索词**：rectangular capillary different contact angles top bottom asymmetric wetting；Wetting considerations capillary rise closed square open rectangular；Concus Finn wedge rectangular corner；nanoimprint Lucas Washburn filling time；mr-NIL210 100 mbar pressure；air bubble formation dissolution dispensing nanoimprint；Multiphase model nanoimprint lithography；Reddy两篇题名和DOI。

**未找到/未完成**：适用于上模具Z向盲槽的单一显式临界角；非对称/圆角Concus–Finn完整修正式；本胶σ、动态接触角、气体溶解度/扩散率；可靠填充时间及气泡阈值。

## B组：XY各向异性与应用

### B1. 有定量铺展数据，但不等于单相K比

Liu et al. (2026), *Geometry-Engineered Microgrooves Broaden the Material Scope for Spontaneous Liquid Spreading*, Small Methods10,e70775，[DOI 10.1002/smtd.70775](https://doi.org/10.1002/smtd.70775)，[原始研究全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC13353881/)。

【原文直接给出】0.5 μL液滴的Lx/Ly；v形槽宽深比约2.0（无量纲），降低本征接触角会增大各向异性。作者把Lx/Ly=20（无量纲）选作“有效定向铺展”的**经验阈值**，对应其条件下大于1 cm的输运距离；图3讨论该判据下临界角约11°。**20不是所有试验的最大实测比值。**

【同文另一组直接给出】槽宽300 μm、深110 μm，1 μL液滴，在0.56 s时，r/v/u三种截面的沿槽长度分别26/22/11 mm。**这是不同截面间的沿槽对比，不是同一液滴的沿/横速度比。**

外推风险：开放、润湿驱动、微米沟槽，与120×100 nm受限全充液不同。数据不能填入你的M比。白话：液滴变成长条既可能因为更容易流，也可能因为更容易润湿，不能只凭长宽比反推阻力。

Ma et al. (2024), *Experiment of droplet anisotropic wetting behavior on micro-grooved PDMS membranes*, Scientific Reports14,28011，[DOI 10.1038/s41598-024-78681-z](https://doi.org/10.1038/s41598-024-78681-z)也是直接实验线索；未完成图中比值逐点提取，不凭目测补数字。

### B2. K张量、h依赖与NIL

单相方向性K见D1、D3；数值标定框架见D2。固定槽深d改变h时，M∥、M⟂由h和h+d共同决定，不能简单都乘同一个h³。**Jain2017已将NIL线槽的各向异性渗透率用于多滴流动**；补全文前不把其公式等同D1。未找到可以无条件代入全部EX240尺寸的已验证经验拟合。
白话：横着跨凸台和顺着槽走，对间隙变化的反应不同；一个平均厚度容易掩盖这种差别。

### B3. 转印/印刷电子

NIL直接先例已找到；**印刷电子/转印中同时具有相同单相K定义、匹配受限边界的专门数据，本轮未核实到**。开放基底润湿研究不能仅因都有沟槽就作为单相验证。
白话：在空气中摊开的墨滴，与两块板间已经充满液体的流动，需要分别解释。

**三个关键发现**

1. 已有定量各向异性铺展，但长宽比不等于压力驱动K比。
2. NIL各向异性渗透率已有直接先例。
3. 当前几何的K仍须本项目独立验证，不能从开放槽实验搬数值。

**实际检索词**：grooved surface droplet anisotropic spreading length ratio parallel perpendicular；micro grooved PDMS anisotropic wetting experiment；Geometry Engineered Microgrooves liquid spreading anisotropy coefficient；grooved surface permeability parallel transverse film thickness；nanoimprint anisotropic permeability patterned templates；anisotropic spreading grooves printed electronics。

**未找到/未完成**：匹配本树脂、尺寸和受限边界的L比/速度比；Ma2024逐点图值；普适“铺展比→K比”换算；匹配单相K定义的印刷电子数据。

## C组：J-FIL工艺背景

### C1. 可核查量级与“8–20 nm”

S.V.Sreenivasan (2017), *Nanoimprint lithography steppers for volume fabrication of leading-edge semiconductor integrated circuits*, Microsystems & Nanoengineering3,17075，[DOI 10.1038/micronano.2017.75](https://doi.org/10.1038/micronano.2017.75)，[出版社全文](https://www.nature.com/articles/micronano201775)。以下为该文当时的报告，不冒称2026设备现状。

| 事项 | 核对结果 | 来源与限制 |
|---|---|---|
| 液滴体积 | pL量级；Jain2017引言也描述few picoliters | 原文量级，未取得通用最小–最大范围 |
| 液滴间距 | 未核实统一数值区间 | 不从示意图、喷头间距推断 |
| 填充时间 | 约1.1 s | “Description of the J-FIL process”：填充及精密对准步骤，非单对液滴的固有融合时间 |
| 残胶厚度RLT | 13–25 nm | 同节，20 nm宽、50 nm高特征的例子；均匀性约3 nm、3σ |
| 8–20 nm | 未核实为通用范围 | 可能存在更薄特定工艺，不能据此写统一规格 |

白话：残胶厚度取决于图案、刻蚀和设备，不能把一个范围当所有压印的标准；h=75 nm也不必等于最终残胶层，应说明所研究的间隙阶段。

### C2. 是否已有多滴融合模型？

**有。** Jain2017出版社章节片段给出9滴、100滴排列模拟（计数，无量纲），在模板间隙缩小过程中研究融合与非填充区域。[出版社原文片段](https://www.sciencedirect.com/science/article/pii/S0167931717301296)。Reddy2005、Cochrane2018提供早期和多相扩展线索。不同研究采用外力、毛细或指定运动，不能统称“纯单相压力下融合”。
白话：多滴融合不是空白，首篇可为这类大尺度模型补充更可靠的局部阻力。

### C3. 缺陷与工艺窗口

| 缺陷 | 需区分的机制/观测 | 单相首篇边界 |
|---|---|---|
| 未填充、薄膜未连通 | 来液量、方向阻力、前沿与融合 | 可给已充液区阻力，不能独自预测界面是否相接 |
| 气泡 | 前沿合围、排气/溶解 | 没有气液界面时不能直接预测 |
| 残胶不均 | 液量分配、图案密度、排液和平整度 | K可进入更大尺度守恒模型，仍需验证 |
| 模板损伤 | 颗粒、接触、脱模 | 不属当前固定壁流体模型 |

Sreenivasan明确讨论大于薄残胶层的硬颗粒可能损坏模板并造成重复缺陷；不由此推算本项目缺陷概率。[来源](https://www.nature.com/articles/micronano201775)。
白话：首篇回答“已有液体容易往哪流”，不能独自回答哪里留气泡或压坏模板。

**三个关键发现**

1. pL量级已核实，统一滴量与间距区间未取得。
2. 1.1 s及13–25 nm都有特定原文条件，不能改写成通用规格。
3. 多滴融合和非填充建模已有先例，局部模型须说清新增价值。

**实际检索词**：J FIL review droplet volume spacing residual layer thickness；Nanoimprint lithography steppers volume fabrication Sreenivasan；nanoimprint 8 nm 20 nm residual layer；droplet size droplet placement gas dissolution throughput defect rate UV nanoimprint；multiple droplets merging patterned template simulation；J FIL bubble non fill template damage process window。

**未找到/未完成**：统一滴量/间距上下限；剥离对准和排气影响后的融合时间范围；8–20 nm为通行RLT的证据；本胶与本几何的工艺窗口。

## 对核心方案的建议：2–3个优先对象与最大风险

**第一：D1局部立方律/条纹Reynolds。** 无拟合、公式透明，同一全充液无滑移条件下能测量被省略的局部流动影响；同时报告假设内验证和矩形槽外推，不只挑已知不适用的条件宣布失败。

**第二：Jain2017的NIL各向异性渗透率闭合。** 应用最贴近，先取得公式页和验证章节。若其K本来就来自显式数值单元，应比较标定范围、平均定义及跨间隙迁移，不将均质化一概视为粗糙近似。

**第三：D2独立标定流量因子/数值均质化。** 用未参与标定的间隙或几何检验预测，服务宏观模型。D3可作平滑/受控圆角的附加理论基准；D4/D5暂不宜作首篇主挑战对象。

**最大风险是比较对象没有定义清楚**：物理边界混比、参考高度与K单位混用、α不足以确定液区、把已存在的方法组合包装成首次。其次，连续无滑移Stokes方程下，几何相似的长度缩放使M随长度三次方缩放【量纲推导】；仅把尺寸改成纳米未必形成新机制。

值得检验的论文问题是：**有限间隙与实际矩形边角如何改变方向性阻力；常用闭合在何种无量纲几何范围偏离经验证显式解；偏差是否能由侧壁剪切、槽内耗散和局部转向解释？** 这是建议，尚未证明新颖性或可发表性。

下一项资料工作：取得Jain2017全文，逐式核对K定义、线槽平均、部分填充与验证；随后补传统数据库引文追踪。明确对照后再冻结计算矩阵。**本轮没有运行OpenLB、没有新增数值验证或Gate放行。**

## 抽检记录与证据边界

- DOI抽检1：10.1016/j.mee.2017.04.001，重定向后HTTP200，落到Elsevier linkinghub的S0167931717301296，与出版社题名匹配。入口可达不等于取得付费全文。
- DOI抽检2：10.1016/j.euromechflu.2018.02.004，重定向后HTTP200，落到S0997754617305010，与出版社题名匹配。
- Tavakol作者稿PDF第4页式(8)：已渲染并目视核对。
- Feuillebois作者稿PDF第2页式(1)(2)：已渲染并目视核对。
- Pusterhofer正式PDF第4页式(9)(11)(12)：已渲染并目视核对。
- Belyaev正式PDF第494页式(2.22)：已渲染并目视核对；第496页式(2.35)从同一PDF文本核对。
- Ban/Jain/Bonnecaze2018会议稿第3页式(2)：已下载、渲染并目视核对；明确非正式期刊全文。
- JFM2020：出版社HTML式号核对，未声称目视核验PDF。
- 部分DOI入口403/502不证明DOI不存在；替代来源已标注。
- Asta独立报告、两套结果交集/差集、WoS/Google Scholar人工查新未完成；不作“全球首次”判断。


