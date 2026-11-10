# 第5章 草稿：闭合差异、对比对象与误差传播

> 2026-10-18局部修订；作者审阅稿，不代表投稿放行。
> 5.A讨论Reynolds闭合与显式截面流动的差异，机制仅作候选；5.B说明主基线与比较定义；5.C报告降阶模型内的系数误差传播。
> 主体保留并行工作流的改写，仅合并机制强度、归一化、符号、数字和来源说明；原稿与并行快照见`Chapter5_revision_20261018/`。
> V2仍为已采纳的数据知情经验修订。首篇保持固定间隙、α=1真单相；不恢复机制收支或新增仿真。

---

## EN

### A. The Reynolds closure and the explicitly resolved cross-section

The closure tested here is not an approximation adopted for convenience. For a one-dimensional profile it is an identity of the Reynolds approximation: Patir and Cheng obtained the arithmetic average along the flow and the harmonic average across it by comparing the stochastic Reynolds equation with the averaged one [12], and for a square wave the two reduce to the conductance pair of Eqs. (1). Within that approximation, and for this geometry, the averaging step therefore adds nothing of its own; Eqs. (1) state the exact conductance of a locally parallel flow.

The resolved calculations and the Reynolds closure use the same definition of transport coefficient: viscosity times mean depth-integrated flux divided by the imposed gradient. Their relative discrepancy is $E_i=K_i^{\rm mod}/K_i^{\rm ref}-1$, where $K_i^{\rm ref}$ denotes the discrete numerical reference. The arithmetic–harmonic averaging step is exact within the stated one-dimensional Reynolds cell model; the comparison therefore tests that local closure against explicitly resolved flow. It does not remove the discretization uncertainty of the numerical reference or locate the discrepancy within the fluid domain.

A global coefficient discrepancy does not identify its spatial origin. For the ideal fully developed Stokes flow along the grooves, $\mathbf u=(0,v(x,z),0)$ and $\mu(v_{xx}+v_{zz})=-G$. The local parallel-plate expression $v=Gz[H(x)-z]/(2\mu)$ drops $v_{xx}$; substitution into the full equation leaves a residual $GzH''(x)/2$. Wherever $H''(x)\ne0$, that expression is not a solution, even if the wall is smooth. This derivation illustrates why a local-cubic-law error need not require a corner. It neither measures the contribution of a particular term in the existing numerical fields nor provides a spatial dissipation budget.

Mechanistic explanations remain hypotheses. The closure overestimates the conductance at every sampled geometry in both directions, but this sign does not identify where the discrepancy arises. Teyssèdre's related rectangular-grating squeeze-flow study [15] reported force ratios of two to eighty relative to its own Stefan-type lubrication estimate, with changes during filling and contact. Those ratios are neither measured relative to Eq. (1) nor obtained from the present fixed, fully filled cell. They establish relevant prior evidence of lubrication-model limitations, rather than a decomposition of the present error into corner, side-wall and velocity-redistribution contributions. Redistribution itself can change resistance, so it is not an alternative to added resistance.

The adopted V2 relation is an empirical correction of the local cubic law. Its dependence on $d/w$ was selected with the extension data available, even though those data were excluded from coefficient estimation. Its reported residuals characterize the stated discrete samples; they are not bounds over a continuous domain or independent final-test results. The fit does not establish that the correction represents a corner contribution or that the physical dependence on $h$ has disappeared.

### B. Why the stripe average is the primary comparison object

The primary comparator is the arithmetic–harmonic closure used in the imprint models examined here [2,4,5]. It is an explicit baseline with the same geometric variables and transport definition after conversion. Other reductions are not excluded, but a quantitative comparison requires their geometry, fill state, boundary conditions and normalization to be matched.

**The stripe average.** The arithmetic and harmonic averages of the cubic conductance, Eqs. (1), are built from $h^3$ over the land and $(h+d)^3$ over the groove. The gap appears in both, at the third power. This is the closure used for line-and-space patterns in imprint modelling [2,4,5].

**Open-groove correlations.** A resistance correlation for an open, partially filled or capillary-fed groove cannot be transferred to a fully filled groove connected to a finite liquid layer merely because both cross-sections are rectangular. The original velocity basis, reference section, porosity, friction-factor convention and interface conditions must be established first. Those definitions have not been verified for the proposed heat-pipe comparator, so no calibrated error or representative friction–Reynolds value is quoted here.

A specified correlation that contains only groove width and depth cannot describe all gap dependence if its remaining inputs are held fixed. That is an applicability and parameter-dependence issue, not a dimensional inconsistency: both expressions may have correct units. It does not prove that the correlation is accurate in its original setting or that no other closure can include the residual gap.

The normalization also requires a definition, not just a change of units. With $J=Q/W$, $\bar U=Q/A_{\rm ref}$ and $J=KG/\mu$, the permeability based on $\bar U$ is $\kappa=K/L_{\rm ref}$, where $L_{\rm ref}=A_{\rm ref}/W$. The fluid-volume average used here gives $L_{\rm ref}=H_{\rm ref}=h+d/2$. Dividing by $P$ would instead define a reference section $WP$; that section is not automatically the available fluid section of this cell. Both sides of any comparison must use the same definition.

For illustration, the archived diagnostic at $d=25$ nm gives a fixed-depth spread of approximately 41.2 when normalized with $P$, and 11.2 with $H_{\rm ref}$; at $d=120$ nm the corresponding spreads are approximately 4.1 and 2.4. These are normalization-dependent transformations of the present coefficients, not measured friction factors or calibrated errors of a heat-pipe model. The $d=75$ and $120$ nm groups have sampled gaps of 50, 75 and 125 nm, and do not include 25 nm. The existing fRe plot is therefore excluded from quantitative model validation pending definition and caption reconciliation.

The stripe average is retained because it has a directly documented imprint-model application and a reproducible definition for the present equal-width pattern. The error map evaluates that baseline under the stated conditions; it does not establish that it is the only possible one-dimensional reduction or that all such reductions fail.

An error of either sign can be removed algebraically by a factor $1/(1+e)$ when $e>-1$. The scientific task is to predict an appropriate factor from geometry with adequate validation. The observed positive closure errors imply factors below unity at those samples; they do not by themselves establish monotonic dependence on any geometric variable.

A final remark bears on the expected discrepancy, not on its derivation. The stripe average applies a local parallel-plate law within each stripe; it does not model the groove as a closed duct with four no-slip walls, and it does not resolve the vertical side walls or the coupling between the axial velocity and the cross-section. The groove mouth opens into a connected layer of thickness $h$, where neither a no-slip nor a free-surface condition applies. Writing the geometry as a duct would be a different model, and the difference between the two is one reason to expect a discrepancy here. It is not evidence about its size.

### C. What the coefficient error does to the process prediction

The application consequence is evaluated by inserting the paired conductances from each geometry and gap into the same reduced squeeze-film model. Each reference prediction uses both principal values from that same discrete cell calculation. Throughout this section $K_\parallel=K_{yy}$ and $K_\perp=K_{xx}$ follow the project coordinates. The propagation scripts rename the along-groove axis as $x$; their variables are mapped to parallel/perpendicular labels here. This coordinate relabelling is not a simulation of rotated groove walls.

Two reduced models are used. Model A is a circular-field calculation with load proportional to $1/(K_\parallel+K_\perp)$. Model B uses a square field and $p=0$ at its perimeter. With positive closing speed $V=-\dot h>0$, its positive-pressure convention is $K_\parallel p_{\xi\xi}+K_\perp p_{\eta\eta}=-\mu V$, where $\xi$ and $\eta$ run along and across the grooves. The archived implementation solves the opposite signed-pressure equation and reports the absolute load; this leaves the magnitude ratios unchanged. The sampled median load ratios are 0.6105 for A and 0.6121 for B, a difference of approximately 0.15 percentage points. Their proximity is an internal comparison, not validation of either physical reduction; model B supplies the results below.

**Uniform closing velocity.** The problem is linear in $V$ and homogeneous of degree $-1$ in $\mathbf{K}$ taken jointly; it is not linear in $1/K_\parallel$ and $1/K_\perp$ separately. A common scaling of both conductances rescales pressure and load by the inverse factor. Unequal changes generally alter the pressure-field shape, and the peak-pressure ratio can then depart from the load ratio by up to $0.024$, that is 2.4 percentage points, over the sampled geometries. Over the eighteen geometries the load ratio relative to the discrete reference coefficients ranges from 0.371 to 0.901, a median error of $-38.8\%$. The worst case is $h=50$ nm, $d=120$ nm, where $K_\parallel$ is overestimated by $204.8\%$ and the predicted load retains $37\%$ of the reference value. The closure overestimates the conductance at every sampled point, so the sign of the load error is uniform; as noted above, that is a statement about the sign, not about the mechanism.

**Constant load.** With the load imposed the closing rate follows from the resistance, $V(h)=F/S[\mathbf{K}(h)]$ where $S$ is the load per unit rate, and the drainage time becomes
$$
t=\frac{1}{F}\int_{h_f}^{h_0} S\!\left[\mathbf{K}(h)\right]\mathrm{d}h .
$$
A single-gap ratio is generally insufficient. For the common stroke $h_0=125$ nm to $h_f=50$ nm, the model-B ratio $S_{\rm mod}/S_{\rm ref}$ ranges from 0.371464 to 0.477857 at $d=120$ nm. Across the five depths, the integrated uncorrected time ratio ranges from 0.404987 to 0.874690. Freezing the model-B ratio at 125 nm instead gives a relative difference from its integrated ratio of approximately 3.03% at $d=25$ nm and 17.99% at $d=120$ nm.

The primary time calculation interpolates each reference conductance $K_i(h)$ in log–log coordinates with shape-preserving cubic interpolation, using all available gaps at that depth, and then evaluates $S[K_\parallel(h),K_\perp(h)]$ at 400 points over 125–50 nm. The adopted V2 factors multiply the model conductances before evaluation of the load. A concurrent supplementary table instead interpolates the already evaluated $S(h)$ using knots restricted to that stroke. It gives corrected time ratios of 0.962185–1.005938, whereas the primary chain gives 0.960996–1.004658; the largest paired difference is approximately 0.00162, or 0.162 percentage points. These different interpolation objects and knot choices are kept separate. Neither spread bounds interpolation uncertainty or the uncertainty in the reference conductances.

**The two loading conditions.** At imposed velocity the time to traverse a given stroke is $(h_0-h_f)/V$ and is exact by construction, whatever the coefficients; the error appears entirely in the pressure and the load. Reporting a time error under imposed velocity would understate the problem, because it is identically zero. Under a constant load the time is the integral above, and its error is a separate quantity.

**Where the load error comes from.** Because the load is homogeneous of degree $-1$ in $\mathbf{K}$, it factorises exactly:
$$
\frac{F_{\rm mod}}{F_{\rm ref}}
=\underbrace{\frac{\hat h(A_{\rm mod})}{\hat h(A_{\rm ref})}}_{\text{anisotropy}}\cdot
\underbrace{\frac{1}{\sqrt{(1+e_\parallel)(1+e_\perp)}}}_{\text{mean conductance}},
$$
with $A=K_\parallel/K_\perp$ and $\hat h$ a function of $A$ alone. The product reproduces the computed ratio to machine precision. The mean-conductance term lies between 0.48 and 0.90 and the anisotropy term between 0.74 and 1.00. This is an algebraic identity within the reduced model. It is not a budget of dissipation, it does not identify which part of the geometry produces the error, and the dominance of the mean term does not show that a one-variable geometric correction is sufficient in general.

**Which component matters.** Homogeneity fixes $w_\parallel+w_\perp=1$, with $w_i=-\partial\ln F/\partial\ln K_i$. For the square field, the weights are equal at $A=1$; at $A=4$ the along-groove weight is approximately 0.78 and the across-groove weight 0.22; at $A=15.5$ they are approximately 0.90 and 0.10. Thus the along-groove component has the larger weight for the sampled square-field cases. Applying V2 only to the model's along-groove coefficient leaves a median load residual of −12.2%; applying it only across the grooves leaves −32.9%. These are partial-correction diagnostics. They are distinct from replacing only one model coefficient while retaining the other reference coefficient, and neither comparison ranks microscopic mechanisms.

The weights are not properties of the coefficients. They depend on the field through the single parameter $\Lambda=(L_\parallel/L_\perp)^2(K_\perp/K_\parallel)$, with $L_\parallel$ measured along the grooves. For a field elongated along the grooves the liquid must drain across them and $w_\parallel\to0$; for one elongated across, $w_\parallel\to1$. For a near-square field ($0.8\lesssim L_\parallel/L_\perp\lesssim1.3$) the two orientations differ by at most 0.22 in $w_\parallel$ at $A\approx1$, and by 0.06 at $A\approx15$. Any statement that one component matters more is therefore conditional on the field, and it inverts for a field whose long side runs along the grooves.

**After the correction.** Applying the adopted V2 relation in Eq. (2b) to the model conductances gives load ratios of 0.937291–1.050836 over the 18 sampled geometries: residuals of approximately −6.27% to +5.08%, with a signed median of −2.12%. For the primary 125–50 nm time chain, the corrected ratio is 0.960996–1.004658, or approximately −3.90% to +0.47%; it crosses unity. These are retrospective reduced-model results, not independent final tests or continuous-domain guarantees. The perpendicular correction has no declared accuracy below $h=50$ nm. Results involving the $h=25$ nm cells therefore remain outside that two-component claim; the archived aspect-ratio example reaches about 23% load residual for a sufficiently elongated field. All reference predictions also retain conductance discretization and interpolation uncertainty.

**What this does and does not establish.** This calculation measures how coefficient discrepancies propagate inside a specified Reynolds-type model. It does not test that reduction against a directly resolved closing film, and it contains no gas phase, capillary front or moving contact line. Within this model and these samples, the original closure gives loads approximately 37%–90% of the predictions based on discrete reference conductances, while V2 reduces the sampled load discrepancy to approximately −6.27% to +5.08%. Engineering adequacy requires an application-specific tolerance and independent evidence; it is not established by these residuals alone.

---

## 中文

### A. Reynolds 闭合与显式截面流动的差异

本文检验的闭合并非为方便而选的近似。对一维形貌，它是 Reynolds 近似下的一条恒等式：Patir 与 Cheng 通过把随机 Reynolds 方程与平均 Reynolds 方程相比对，得到沿流动方向的算术平均与横向的调和平均 [12]；对矩形方波，两式即退化为式(1)的导度对。**在该近似内、对本几何而言，平均这一步本身不添加任何东西**；式(1)给出的是局部平行流动的精确导度。

精细计算与 Reynolds 闭合采用相同的输运系数定义：黏度乘以平均深度积分通量，再除以外加梯度。相对偏差为 $E_i=K_i^{\rm mod}/K_i^{\rm ref}-1$，其中 $K_i^{\rm ref}$ 是离散数值参考值。算术—调和平均在所述一维 Reynolds 单元模型内可精确求出，故此处比较的是该局部闭合与显式流动计算；这既不消除参考解自身的离散误差，也不定位偏差来自流体域的何处。

全局系数偏差不能定位空间来源。理想的沿槽充分发展 Stokes 流取 $\mathbf u=(0,v(x,z),0)$，满足 $\mu(v_{xx}+v_{zz})=-G$。局部平板表达 $v=Gz[H(x)-z]/(2\mu)$ 省略了 $v_{xx}$，代入完整方程会留下残差 $GzH''(x)/2$。当 $H''(x)\ne0$ 时，即使壁面光滑，该表达也不是精确解。这个推导说明局部立方律出现误差并不需要尖角；它既不测量既有数值场中某一项的贡献，也不提供空间耗散收支。

因此机制仍作为候选解释。闭合在所有已采样几何、两个方向上均高估导度，但这个符号不指出偏差发生在哪里。Teyssèdre的相关矩形线栅挤压研究[15]报告了相对其自身 Stefan 型润滑力的2至80倍力比，并涉及填充与接触状态的变化。该比值既非相对本文式(1)，也不是当前固定、全充液单胞的结果；它是润滑模型局限的近邻证据，不是本文角点、侧壁与速度重分布贡献的分解。重分布本身可以改变阻力，两者不能视为二选一。

当前采用的V2是局部立方律的经验修正。虽然扩展数据没有进入系数估计，它们在选择 $d/w$ 变量和模型时已可见。所报残差只描述规定的离散样点，不是连续域上界或独立最终测试；拟合本身也不证明修正代表角点贡献，或物理上的 $h$ 依赖已经消失。

### B. 为什么以条纹平均为主要对比对象

主要对照为本轮所核压印模型采用的算术—调和闭合[2,4,5]。它具有直接应用来源，并可在单位换算后与本项目使用相同的几何变量和输运定义。其他降阶形式并未被排除，但定量比较须先匹配几何、填充状态、边界及归一化。

**条纹平均。** 立方导度的算术与调和平均（式 1）由凸台下的 $h^3$ 与槽内的 $(h+d)^3$ 构成，间隙在两处都出现，且以三次方进入。压印建模中线宽图案用的就是这个闭合 [2,4,5]。

**开放槽关联式。** 面向开放、部分充液或毛细供液槽的阻力关系，不能仅因截面同为矩形就直接移植到全充液、并连接有限液层的槽。首先须核对原式的速度基准、参考截面、孔隙率、摩擦因子惯例和界面条件。当前拟议热管对照的这些定义尚未核清，因此不在此报告其标定误差或代表性摩擦—雷诺数乘积。

若指定关联式只含槽宽和槽深、其余输入保持固定，它就不能描述全部间隙依赖。这是适用对象与参数依赖不匹配，不是量纲不一致：两个表达式都可能具有正确单位。这也不证明该关联式在其原工况中精度如何，更不排除其他闭合引入残余间隙。

归一化也必须依靠定义。由 $J=Q/W$、$\bar U=Q/A_{\rm ref}$ 和 $J=KG/\mu$，基于 $\bar U$ 的渗透率为 $\kappa=K/L_{\rm ref}$，其中 $L_{\rm ref}=A_{\rm ref}/W$。本文的流体体积平均给出 $L_{\rm ref}=H_{\rm ref}=h+d/2$；除以 $P$ 则是另定义一个 $WP$ 的参考截面，不能自动把它称为该单胞的可用流体截面。任何比较的两侧都须使用同一定义。

仅作为口径敏感性示例，归档诊断在 $d=25$ nm 时给出约41.2倍（除以 $P$）或11.2倍（除以 $H_{\rm ref}$）的固定槽深跨度；$d=120$ nm 时对应约4.1倍或2.4倍。这些是当前输运系数在特定归一化下的变换，不是实测摩擦因子或热管模型的标定误差。$d=75$、120 nm两组只有50、75、125 nm间隙，没有25 nm样点。定义和图注核对完成前，现有fRe图不作为定量模型验证证据。

保留条纹平均作为主对照的理由，是它具有明确的压印模型应用来源，并可为当前等宽线槽定义可复核的比较。误差地图检验的是这一特定基线，不意味着它是唯一可能的一维降阶形式，也不意味着所有一维降阶都失败。

乘性因子 $1/(1+e)$ 在 $e>-1$ 时能从代数上纠正任一符号的误差。科学问题是能否由几何预测适当因子，并有充分验证。样点上原闭合的正偏差意味着对应纠偏因子小于1，但不由此推出它对任一几何变量必然单调。

**最后一点关乎预期的差异，不关乎其推导。** 条纹平均在每条槽内施加局部平板律；它**不是**把槽当作四面无滑移的封闭管，也不解析竖直侧壁，更不解析轴向速度与截面之间的耦合。槽口通向厚度为 $h$ 的连通液层，那里既不适用无滑移、也不适用自由面条件。把几何写成管道是另一个模型，两者之差是在此处预期出现偏差的一个理由，**但不是关于其大小的证据**。

### C. 系数误差对过程预测的影响

应用后果通过同一降阶挤压液膜模型评价：每个几何与间隙的两个参考主值均来自同一个离散单胞，不跨算例拼接。本节使用 $K_\parallel=K_{yy}$、$K_\perp=K_{xx}$，与项目坐标一致。传播脚本把沿槽轴另命名为 $x$，这里已映射为沿槽／跨槽标记；坐标重命名不等于模拟了旋转槽壁。

采用两个降阶模型。模型A为圆形场计算，荷载与 $1/(K_\parallel+K_\perp)$ 成正比；模型B为边缘 $p=0$ 的方形场。若闭合速率取 $V=-\dot h>0$，模型B的正压约定为 $K_\parallel p_{\xi\xi}+K_\perp p_{\eta\eta}=-\mu V$，$\xi$、$\eta$ 分别沿槽和跨槽。归档实现解的是相反符号的压力，再取荷载绝对值，故幅值比不变。样点荷载比的中位数A为0.6105、B为0.6121，约差0.15个百分点；两者相近是内部比较，不是对物理降阶的验证。下文数字采用模型B。

**恒速下压。** 问题对 $V$ 线性，对 $\mathbf{K}$ **联合地**是 $-1$ 次齐次；它**不是**分别对 $1/K_\parallel$ 与 $1/K_\perp$ 线性。两个导度共同按同一倍率缩放时，压力与荷载按其倒数缩放；倍率不同时一般会改变压力场形状，峰值压力比与荷载比可以不同——在本文采样几何上两者最多相差 $0.024$，即 2.4 个百分点。相对离散参考系数，十八个几何的荷载比在 0.371 至 0.901 之间，中位误差 $-38.8\%$。最坏一档是 $h=50$ nm、$d=120$ nm：$K_\parallel$ 被高估 $204.8\%$，预测荷载只剩参考值的 $37\%$。闭合在每个采样点都高估导度，故荷载误差**符号一致**；如上所述，这是关于符号的陈述，不是关于机制的陈述。

**恒载。** 给定荷载后闭合速率由阻力决定，$V(h)=F/S[\mathbf{K}(h)]$，$S$ 为单位速率所需荷载，排液时间为
$$
t=\frac{1}{F}\int_{h_f}^{h_0} S\!\left[\mathbf{K}(h)\right]\mathrm{d}h .
$$
一般不能用单一间隙处的比值代替积分。在统一行程 $h_0=125$ nm至 $h_f=50$ nm上，$d=120$ nm的模型B比值 $S_{\rm mod}/S_{\rm ref}$ 为0.371464–0.477857。五个槽深的未修正积分时间比为0.404987–0.874690。若将模型B的比值冻结在125 nm处，相对模型B积分结果的差，$d=25$ nm约为3.03%，$d=120$ nm约为17.99%。

本节时间主链先对各深度全部已知间隙上的参考 $K_i(h)$ 做对数—对数保形三次插值，再在125–50 nm的400个积分点评价 $S[K_\parallel(h),K_\perp(h)]$；V2因子先乘模型导度，再求荷载。并行补充表采用另一做法：先算各样点的 $S(h)$，只用行程内节点插值该阻力。后者的修正时间比为0.962185–1.005938，主链为0.960996–1.004658；最大逐深度差约0.00162，即0.162个百分点。两者改变了插值对象和节点选择，须分开记录；该差值不是插值误差或参考导度不确定度的上界。

**两种加载工况不可混淆。** 恒速时走完给定行程的时间是 $(h_0-h_f)/V$，按构造精确，与系数无关；误差全部出现在压力与荷载上。若在恒速下报一个时间误差，那它恒为零，会把问题说轻。恒载下时间由上式积分决定，其误差是另一个量。

**荷载误差从哪来。** 因荷载对 $\mathbf{K}$ 是 $-1$ 次齐次，它可以精确分解：
$$
\frac{F_{\rm mod}}{F_{\rm ref}}
=\underbrace{\frac{\hat h(A_{\rm mod})}{\hat h(A_{\rm ref})}}_{\text{各向异性}}\cdot
\underbrace{\frac{1}{\sqrt{(1+e_\parallel)(1+e_\perp)}}}_{\text{平均导度}},
$$
其中 $A=K_\parallel/K_\perp$，$\hat h$ 只依赖 $A$。乘积与实算比值吻合到机器精度。平均导度项落在 0.48–0.90，各向异性项落在 0.74–1.00。**这是降阶模型内部的代数恒等式**：它不是耗散预算，不指出几何的哪一部分产生了误差，平均项占优也不表明"一个几何变量的修正"在一般意义上是充分的。

**哪个分量更重要。** 齐次性给出 $w_\parallel+w_\perp=1$，$w_i=-\partial\ln F/\partial\ln K_i$。对方形场，$A=1$时两者相等；$A=4$时沿槽权重约0.78、跨槽约0.22；$A=15.5$时约0.90与0.10。因此在本文方形场样点中沿槽权重较大。只对模型的沿槽系数应用V2，荷载中位残差为−12.2%；只对跨槽应用为−32.9%。这是单方向修正诊断，与“只换一个模型系数、另一个保留参考系数”的检验不同，两者都不能解释为微观机制排序。

权重不是系数的性质，它通过单一参数 $\Lambda=(L_\parallel/L_\perp)^2(K_\perp/K_\parallel)$ 依赖版图，$L_\parallel$ 沿沟槽方向量。版图沿沟槽拉长时液体必须横穿沟槽排出，$w_\parallel\to0$；沿横向拉长时 $w_\parallel\to1$。对近似方形版图（$0.8\lesssim L_\parallel/L_\perp\lesssim1.3$），两种取向在 $A\approx1$ 时 $w_\parallel$ 相差至多 0.22，在 $A\approx15$ 时相差 0.06。因此"某个分量更重要"的说法都以版图为条件，且当版图长边沿沟槽方向时**结论反转**。

**修正之后。** 将式(2b)所采用的V2作用于模型导度，18个样点的荷载比为0.937291–1.050836，即残差约−6.27%至+5.08%，有符号中位数为−2.12%。在125–50 nm时间主链上，修正比值为0.960996–1.004658，即约−3.90%至+0.47%，跨过1。这些都是事后降阶模型样本结果，不是独立最终测试或连续域保证。跨槽修正在 $h<50$ nm没有声明精度，故涉及 $h=25$ nm单元的结果仍在双分量精度声明之外；归档长宽比示例在足够细长场中出现约23%的荷载残差。所有参考预测也保留导度离散和插值不确定度。

**这证明了什么、没证明什么。** 本计算度量系数偏差在指定Reynolds型模型内部的传播，不把该降阶与直接解析的闭合液膜作验证，也不含气相、毛细前沿或移动接触线。在该模型和样点内，原闭合的荷载约为基于离散参考导度预测的37%–90%，V2将样点荷载偏差减小至约−6.27%至+5.08%。是否满足工程需要，仍取决于用途容差和独立证据，不能单靠这些残差认定。

---

## 写作说明（本次局部合并后的当前口径）

### 1. 来源和版本

- 本章按[第5章机制审查](Chapter5_mechanism_audit_20261018/REPORT.md)修订；并行改写已保留快照，当前只合并必要纠错。过程与源哈希见[修订记录](Chapter5_revision_20261018/REVISION_NOTE.md)。
- [12]的条件平均关系与[15]的相关挤压研究保留；[17]仅有摘要/图示级证据，不作光滑/方波控制变量对照。本节无新增文献编号，整稿编号仍须统一。
- 引言当前的V2编号为式(2b)，本章沿用。V2系数、拟合程序和原始系数数据未由本轮修改。

### 2. 数字来源，主链与敏感性不得混用

| 当前数值／结论 | 对应来源与口径 |
|---|---|
| 18几何、36主方向工况 | D2四份汇总CSV，仅5 nm主图数据；不是48种几何 |
| 未修正荷载比0.371464–0.901197 | 审查evidence.json的cases，模型B；中位残差−38.79% |
| 修正荷载比0.937291–1.050836 | 同一18样点；有符号中位残差−2.12%，不是−1.0% |
| 峰压比与荷载比最多差2.4003个百分点 | 同一模型B、不同主值倍率；非统一缩放 |
| d120的Sm/Sref为0.371464–0.477857 | 审查times主链；旧S_ratio字段不是该比值 |
| 冻结B与积分B差3.03%／17.99% | d25／d120，同125→50 nm行程；不是原A链19.1% |
| 时间主链未修正0.404987–0.874690 | 先插值各K，再求S并积分；审查times |
| 时间主链修正0.960996–1.004658 | 同链，约−3.90%至+0.47%，跨过1 |
| 补充S插值修正0.962185–1.005938 | 并行table2b的pchip行；另一对象/节点选择，不替代主链 |
| 均值项约0.48–0.90，形状项约0.74–1.00 | 归档table3，仅模型内代数分解 |
| 方形场A=4时沿槽权重约0.78 | 沿槽/跨槽定义直接微扰；不得写成跨槽0.78 |
| 只修模型沿槽／跨槽的中位荷载残差−12.2%／−32.9% | 本轮对归档成对K和V2作局部代数检查；不是原表中“只替换一个模型分量”的−33.1%／−8.2% |

主链精细小数用于定位与复核，不代表物理预测具有该精度。插值/节点变动产生的数值差不能自动转成严格不确定度界；参考K的全域离散误差尚未界定。连续域、未见几何与最终预测性能不由此放行。

### 3. 机制与比较边界

| 原问题 | 当前处理 | 尚未完成 |
|---|---|---|
| M01–M06：平均恒等式、唯一尖角与d/w归因 | 保留条件关系；机制降为候选；V2标为数据知情经验修订 | 空间牵引/耗散分离，§12.3仍暂缓 |
| M07–M09：两类/唯一模型及开放槽数值 | 主基线按明确来源和相同定义选择；撤正式热管误差数字 | 原式速度、截面、孔隙率、f/Re惯例 |
| M10–M11：变号不可修、四壁管与内部槽口 | 更正逻辑；正偏差不推出几何单调性；内部流体面不等于自由面 | 不自动新增边界模型 |
| M12–M16：荷载、齐次性、Sm与时间链 | 保留可靠样点；分开主链与S插值敏感性；非机制分解 | 模型物理验证与独立预测测试 |
| M17–M20：坐标、修正范围、真实值和符号 | 使用沿槽/跨槽标签；V=−dh/dt>0、正压右端负号；保留样点限制 | 图表标签与完整正文交叉引用待整稿合并 |

### 4. 图表和过程材料

现有fRe图包含尚未核定的归一化和摩擦因子灰带，当前不作为定量验证图，也不因文件存在就标为论文可用图。保留原图、图注和脚本作过程材料，本轮不修改或删除。

Fig9/10及并行新增table2b均保留。作图脚本在本轮准备期间由另一工作流更新；本轮未重画或验收图像，不声称所有面板已与当前时间主链、坐标标签对齐。整稿引用图之前，须核对其实际数据链和图注。

原写作说明和各次并行快照已保存，避免留下“已撤数字仍应写入正文”的相反指导。当前文件是待作者审阅的工作稿；无新OpenLB计算、编译、原始结果验收或Gate放行。
