# 第 5 章 草稿（5.A 立论 + 5.B 对比对象 + 5.C 误差传播）

> 本章现有**三节**，各管一件事，顺序不可换：
>
> | 节 | 标题 | 回答的问题 | 性质 | 篇幅 |
> |---|---|---|---|---|
> | **5.A** | The Reynolds closure and the explicitly resolved cross-section | 差异**是什么**、能说到哪一步 | 定性/立论 | 497 词 |
> | **5.B** | Why the stripe average is the primary comparison object | **为什么拿条纹平均去比** | 对比对象的选择 | 683 词 |
> | **5.C** | What the coefficient error does to the process prediction | **错多少、影响什么** | 定量 + 下游 | 1118 词 |
>
> **5.A → 5.B**：先说清楚"差异是 Reynolds 闭合对显式截面流动的差异、机制只作候选"，
> 才能回答"该拿哪个闭合去比"——而不是先假定误差来自某一处。
> **5.B → 5.C**：确认"这个闭合是压印填充实际在用的、且是含过程变量的那一个"，它的误差才值得往下游追。
>
> 5.B 之后、5.C 之前，仍接**误差地图主表**（Sec. IV B）与**修正公式推导**（Eq. 2a → Eq. 2b）。
> 5.C 是本章的收束：把系数误差换算成荷载与排液时间的偏差，并给出修正后的残余。
>
> **本章 EN 合计 2298 词。** 若期刊限制，压缩方案见写作说明 〇·补 ⑤。
>
> ⚠ **2026-10-18 22:5x 按机制审查（`Chapter5_mechanism_audit_20261018/REPORT.md`）整段改写**：
> 原 5.A 标题 *"The error is a property of the corner"* 与"唯一尖角归因"**证据不足，已撤**；
> 5.B 的开放槽定量误差（95%、4–41 倍）与"变号不可修"**已撤**；5.C 的 Sm/Sref 字段、冻结链、
> 修正后时间比、坐标命名**已更正**。逐条对照见「〇·补二」。

---

## EN

### A. The Reynolds closure and the explicitly resolved cross-section

The closure tested here is not an approximation adopted for convenience. For a one-dimensional profile it is an identity of the Reynolds approximation: Patir and Cheng obtained the arithmetic average along the flow and the harmonic average across it by comparing the stochastic Reynolds equation with the averaged one [12], and for a square wave the two reduce to the conductance pair of Eqs. (1). Within that approximation, and for this geometry, the averaging step therefore adds nothing of its own; Eqs. (1) state the exact conductance of a locally parallel flow.

The resolved calculations evaluate the same functional — mean flux divided by mean gradient — under a different operator, Stokes rather than Reynolds. Their ratio is therefore the error of the Reynolds closure itself: not of the averaging, and not of the normalization, since both sides are defined identically and the four conditions under which the identity holds are listed in Sec. II.

What that ratio does not do is locate the error. It is one global number per geometry, and it cannot apportion the discrepancy among the places where the closure departs from the resolved flow. The distinction matters, because a local-cubic-law error does not require a corner. For fully developed flow along a groove, $\mathbf{u}=(0,v(x,z),0)$ at fixed axial gradient $G$, the exact statement is $\mu(v_{xx}+v_{zz})=-G$. The local parallel-plate law retains $v_{zz}$ at each $x$ and drops $v_{xx}$. Substituting the local solution $v=Gz[H(x)-z]/(2\mu)$ leaves a residual $GzH''(x)/2$, which vanishes only where the wall is straight. A smooth but curved wall therefore carries a local-cubic-law error with no discontinuity anywhere, and neither the size nor the spatial distribution of that error is accessible from a global coefficient ratio.

The mechanism is treated as a candidate for this reason. Two features of the data are consistent with the sharp edge contributing. The error is single-signed — the closure overestimates the conductance at every sampled geometry and in both directions — so the sign of the load error is known in advance. And on the same rectangular geometry a resolved Stokes solution gives an imprint force two to eighty times the lubrication estimate at large gaps, falling towards it as the gap closes [15]; that ratio is taken against that study's own Stefan-type lubrication force rather than against Eq. (1), so it locates a failure of lubrication at these gaps without apportioning it. Neither feature separates the sharp edge from wall curvature, from the vertical side walls, or from the in-section redistribution of the axial velocity. Treating "added resistance" and "redistribution" as alternatives would be a false dichotomy in any case, since a redistribution changes the total resistance.

The correction derived below is therefore an empirical correction of the local cubic law. It is written in the groove aspect ratio $d/w$ because that ratio orders the sampled residuals, and it is bounded on the sampled domain rather than offered as a continuous law. It is not derived from a corner argument, and its success is not evidence that the corner is the only source of error.

### B. Why the stripe average is the primary comparison object

More than one one-dimensional reduction is available for a rectangular groove, and the choice among them matters in a process whose gap closes from micrometres to tens of nanometres. Two forms are in use, and they differ in one respect: whether the residual gap enters the reduction at all.

**The stripe average.** The arithmetic and harmonic averages of the cubic conductance, Eqs. (1), are built from $h^3$ over the land and $(h+d)^3$ over the groove. The gap appears in both, at the third power. This is the closure used for line-and-space patterns in imprint modelling [2,4,5].

**The open-groove resistance correlation.** In the heat-pipe literature the permeability of a rectangular groove is written as $K=2\varepsilon r_h^2/(f\,Re)$ with $\varepsilon=w/s$ and $r_h=2w\delta/(w+2\delta)$, the friction–Reynolds product being read from a chart as a function of the aspect ratio $\alpha=w/\delta$. The construction is a one-dimensional duct resistance multiplied by an area fraction; it contains $w$ and $d$ but not $h$. It is standard for wick design, where the liquid runs along the groove under a capillary head and the vapour space above is effectively infinite.

The second form cannot describe the present problem because it does not contain the variable that drives it. In imprint filling the gap is the process variable: it starts at micrometres, passes through the values studied here, and ends at the residual layer thickness. This is a mismatch between the object each closure was built for, not a matter of dimensions — both forms are dimensionally consistent, and the open-groove correlation is correct in its own setting. Nor is it the only other reduction that could be constructed; it is one of the two in use.

That form cannot be compared quantitatively here without a step this work has not taken. The present coefficients are per unit width (m$^3$); converting them to a permeability (m$^2$) requires a reference section, $\kappa = K/L_{\rm ref}$ with $L_{\rm ref}=A_{\rm ref}/W$. Taking the fluid cross-section gives $L_{\rm ref}=H_{\rm ref}=h+d/2$; taking the full cell gives $L_{\rm ref}=P$. The two conventions differ by a factor of order two and must be applied on both sides. The heat-pipe source additionally leaves its porosity, its velocity basis and the definitions behind $f$ and $Re$ to be confirmed. No calibrated error is therefore quoted for that correlation, and Fig. fRe is read as a diagnostic of dependence, not as an error curve.

What survives without that calibration is qualitative and robust. Under either convention the inferred $f\,Re$ at fixed $d$ falls as $h$ increases, by factors of roughly $41$ ($A_{\rm ref}=WP$) or $11$ ($A_{\rm ref}$ fluid) at $d=25$ nm, and $4.1$ or $2.4$ at $d=120$ nm. The magnitude is convention-dependent; the existence of an $h$ dependence at fixed aspect ratio is not. A correlation in the aspect ratio alone cannot represent it.

The stripe average is therefore the primary comparison object for two reasons: it is the closure actually used in imprint filling [2,4,5], and among the two forms examined it is the one that contains the process variable. The comparison in Sec. IV B bounds how far that closure can be pushed. It is not a statement about one-dimensional reduction in general, and it does not establish that only two such reductions exist.

A note on correctability, because it is easily misstated. A multiplicative factor $1/(1+e)$ corrects an error of either sign provided $e>-1$, so the sign of the error is not what decides whether a correction is possible; what decides it is whether the factor can be predicted from the geometry. The sampled closure happens to err in one direction, which makes its correction monotone and convenient, but monotonicity is a convenience and not a requirement.

A final remark bears on the expected discrepancy, not on its derivation. The stripe average applies a local parallel-plate law within each stripe; it does not model the groove as a closed duct with four no-slip walls, and it does not resolve the vertical side walls or the coupling between the axial velocity and the cross-section. The groove mouth opens into a connected layer of thickness $h$, where neither a no-slip nor a free-surface condition applies. Writing the geometry as a duct would be a different model, and the difference between the two is one reason to expect a discrepancy here. It is not evidence about its size.

### C. What the coefficient error does to the process prediction

A coefficient error matters only through what it does downstream. To measure that, the paired coefficients of each geometry at each gap are inserted into a lubrication model of a uniformly closing film, and the model's load and drainage time are compared with those obtained from the discrete reference coefficients. The pairing is strict: both components come from the same geometry and the same gap, and no quantity is assembled from different cases. Throughout this section $K_\parallel$ denotes the along-groove component and $K_\perp$ the across-groove one, matching the project convention; no Cartesian subscript is used, because a rotated frame can silently exchange the two.

Two reduced models are used. The first is axisymmetric with an effective conductance $(K_\parallel+K_\perp)/2$, which makes $p\propto1/(K_\parallel+K_\perp)$ and keeps the algebra checkable by hand. The second solves $K_\parallel p_{\parallel\parallel}+K_\perp p_{\perp\perp}=\mu V$ on a square field with $p=0$ on the boundary, so that the two components enter with separate weights and no averaging is assumed. Their medians agree to 0.1%, so the first is adequate for the load; the second is needed for the sensitivity analysis.

**Uniform closing velocity.** The problem is linear in $V$ and homogeneous of degree $-1$ in $\mathbf{K}$ taken jointly; it is not linear in $1/K_\parallel$ and $1/K_\perp$ separately. Pressure and load therefore scale together only when both components change by the same factor. When they change by different factors the pressure field changes shape, and the peak-pressure ratio departs from the load ratio by up to $0.024$, that is 2.4 percentage points, over the sampled geometries. Over the eighteen geometries the load ratio relative to the discrete reference coefficients ranges from 0.371 to 0.901, a median error of $-38.8\%$. The worst case is $h=50$ nm, $d=120$ nm, where $K_\parallel$ is overestimated by $204.8\%$ and the predicted load retains $37\%$ of the reference value. The closure overestimates the conductance at every sampled point, so the sign of the load error is uniform; as noted above, that is a statement about the sign, not about the mechanism.

**Constant load.** With the load imposed the closing rate follows from the resistance, $V(h)=F/S[\mathbf{K}(h)]$ where $S$ is the load per unit rate, and the drainage time becomes
$$
t=\frac{1}{F}\int_{h_f}^{h_0} S\!\left[\mathbf{K}(h)\right]\mathrm{d}h .
$$
The integral cannot be replaced by a single gap. Along the common stroke $125\to50$ nm the ratio $S_{\rm mod}/S_{\rm ref}$ is not constant: for $d=120$ nm it runs from 0.371 to 0.478, a factor of $1.29$, and the direction of the variation differs between depths. Over the five depths the time ratio ranges from 0.405 to 0.876. Replacing the integral by the value at $h_0$ misplaces the result by 3% at $d=25$ nm and by 18% at $d=120$ nm.

The precision of that statement is limited by the sampling, and the limit should be stated rather than hidden. $K(h)$ is available at only three or four gaps per depth, so the integral depends on how the gaps are joined: a trapezoidal rule on the sampled points and a log-log shape-preserving interpolation differ by up to 0.5 percentage points in the time ratio, which is comparable to the residual after correction. The time results here are quoted to that precision and no further.

**The two loading conditions.** At imposed velocity the time to traverse a given stroke is $(h_0-h_f)/V$ and is exact by construction, whatever the coefficients; the error appears entirely in the pressure and the load. Reporting a time error under imposed velocity would understate the problem, because it is identically zero. Under a constant load the time is the integral above, and its error is a separate quantity.

**Where the load error comes from.** Because the load is homogeneous of degree $-1$ in $\mathbf{K}$, it factorises exactly:
$$
\frac{F_{\rm mod}}{F_{\rm ref}}
=\underbrace{\frac{\hat h(A_{\rm mod})}{\hat h(A_{\rm ref})}}_{\text{anisotropy}}\cdot
\underbrace{\frac{1}{\sqrt{(1+e_\parallel)(1+e_\perp)}}}_{\text{mean conductance}},
$$
with $A=K_\parallel/K_\perp$ and $\hat h$ a function of $A$ alone. The product reproduces the computed ratio to machine precision. The mean-conductance term lies between 0.48 and 0.90 and the anisotropy term between 0.74 and 1.00. This is an algebraic identity within the reduced model. It is not a budget of dissipation, it does not identify which part of the geometry produces the error, and the dominance of the mean term does not show that a one-variable geometric correction is sufficient in general.

**Which component matters.** Homogeneity also fixes the weights, $w_\parallel+w_\perp=1$ with $w_i=-\partial\ln F/\partial\ln K_{ii}$. At $A=1$ they are equal; at $A=4$ the along-groove weight is 0.78 and the across-groove weight 0.22; at $A=15.5$, 0.90 and 0.10. The along-groove component therefore carries more weight whenever $A>1$, which is the case at every sampled geometry, because the liquid drains preferentially along the grooves. Applying the correction to the along-groove coefficient alone leaves a median load error of $-12.2\%$; applying it to the across-groove coefficient alone leaves $-32.9\%$, consistent with the weights. That ordering reflects both the weight and the size of each component's own error, and it must not be read as a ranking of mechanisms.

The weights are not properties of the coefficients. They depend on the field through the single parameter $\Lambda=(L_\parallel/L_\perp)^2(K_\perp/K_\parallel)$, with $L_\parallel$ measured along the grooves. For a field elongated along the grooves the liquid must drain across them and $w_\parallel\to0$; for one elongated across, $w_\parallel\to1$. For a near-square field ($0.8\lesssim L_\parallel/L_\perp\lesssim1.3$) the two orientations differ by at most 0.22 in $w_\parallel$ at $A\approx1$, and by 0.06 at $A\approx15$. Any statement that one component matters more is therefore conditional on the field, and it inverts for a field whose long side runs along the grooves.

**After the correction.** Applying Eq. (2b) to the model coefficients gives a load ratio of 0.937 to 1.051, that is $-6.3\%$ to $+5.1\%$ with a median of $-2.1\%$, and a time ratio of 0.962 to 1.006, that is $-3.8\%$ to $+0.6\%$. The corrected time ratio therefore crosses unity: the correction slightly overestimates the drainage time at the smallest depth and slightly underestimates it elsewhere. Three limitations travel with these numbers. The residual changes sign with gap, at a magnitude small compared with the uncorrected error but not negligible. The across-groove factor is not quoted below $h=50$ nm, so the undeclared $h=25$ nm cell is exposed wherever the field gives $K_\perp$ a large weight — reaching 23% in the load at $L_\parallel/L_\perp\gtrsim10$, a circumstance in which the square-field figure of about 1% would be misleading. And the comparison is against discrete reference coefficients that carry their own discretization uncertainty, not against an exact solution.

**What this does and does not establish.** The calculation measures how a known coefficient error propagates inside a Reynolds-type model. Both reduced models share that model's assumptions — local conductance, pressure-driven flow, no free surface — so the exercise does not test the model itself, and it is not a substitute for a direct simulation of the closing film. It also omits capillarity, a gas phase and a moving contact line. What it establishes is the scale of the consequence within that model: the closure error reduces the predicted load to between 37% and 90% of the reference over the sampled geometries, and the empirical correction brings it within about 6%. Whether that constitutes engineering adequacy depends on the tolerance of the application, which this section does not set.

---

## 中文

### A. Reynolds 闭合与显式截面流动的差异

本文检验的闭合并非为方便而选的近似。对一维形貌，它是 Reynolds 近似下的一条恒等式：Patir 与 Cheng 通过把随机 Reynolds 方程与平均 Reynolds 方程相比对，得到沿流动方向的算术平均与横向的调和平均 [12]；对矩形方波，两式即退化为式(1)的导度对。**在该近似内、对本几何而言，平均这一步本身不添加任何东西**；式(1)给出的是局部平行流动的精确导度。

精细计算求的是**同一个泛函**——平均通量除以平均梯度——只是换了算子：Stokes 而非 Reynolds。因此两者之比**就是 Reynolds 闭合自身的误差**：既不是平均带来的，也不是归一化带来的，因为两侧定义一致，且该恒等成立的四条条件已在第 II 章列出。

**但这个比值不能定位误差。** 它对每个几何只是一个全局数，无法把偏差分摊到闭合偏离真实流动的各个位置上。这一区分要紧，因为**局部立方律的误差并不需要尖角**。沿槽充分发展流取 $\mathbf{u}=(0,v(x,z),0)$、轴向梯度 $G$ 固定时，精确方程为 $\mu(v_{xx}+v_{zz})=-G$；局部平板律在每个 $x$ 处保留 $v_{zz}$、丢掉 $v_{xx}$。代入局部解 $v=Gz[H(x)-z]/(2\mu)$ 后余下 $GzH''(x)/2$，它只在壁面为直线处为零。**因此光滑但弯曲的壁面即使没有任何间断，也带有局部立方律误差**；而该误差的大小与空间分布，都无法从全局系数比中读出。

正因如此，本文把机制当作**候选解释**而非结论。数据有两点与"尖角有贡献"相容：其一，误差同号——闭合在每个采样几何、两个方向上都高估导度，故荷载误差的**符号**可事先知道；其二，在同一矩形几何上以精细 Stokes 解为参考，压印力在大间隙时达润滑估计的 2 至 80 倍，并随间隙关闭回落 [15]——但那个比值是相对该文自身的 Stefan 型润滑力，不是相对式(1)，故它只说明润滑近似在这些间隙上失效，并不分摊原因。**两点都无法把尖角与壁面曲率、竖直侧壁、以及轴向速度在截面内的重分布区分开来。** 而且把"增加阻力"与"重新分配"当作二选一本身就是假二分：重分布会改变总阻力。

因此下文的修正是**对局部立方律的经验修正**。它写成槽的宽高比 $d/w$，因为这个比能整理采样残差的次序；它只在采样域上给出界，不声明为连续律。**它不是从尖角论证推出的，它有效也不证明尖角是唯一误差来源。**

### B. 为什么以条纹平均为主要对比对象

矩形槽的一维简化不止一种，而在间隙由微米关到几十纳米的工艺里，选哪一种并非无关。在用的是两种形式，差别只有一点：**残余间隙到底进不进这个简化**。

**条纹平均。** 立方导度的算术与调和平均（式 1）由凸台下的 $h^3$ 与槽内的 $(h+d)^3$ 构成，间隙在两处都出现，且以三次方进入。压印建模中线宽图案用的就是这个闭合 [2,4,5]。

**开放槽阻力关联式。** 热管文献把矩形槽的渗透率写作 $K=2\varepsilon r_h^2/(f\,Re)$，其中 $\varepsilon=w/s$、$r_h=2w\delta/(w+2\delta)$，摩擦–雷诺数乘积按宽高比 $\alpha=w/\delta$ 查图。其构造是一维槽道阻力乘以面积占比，式中含 $w$ 与 $d$，**不含 $h$**。这是吸液芯设计的通行做法——那里液体在毛细压头下沿槽单向流动，槽顶之上的蒸气空间可视为无限大。

**第二种形式无法描述本文问题，原因在于它不含驱动这一过程的变量。** 压印填充中，间隙本身就是过程变量：由微米起步，经过本文区间，终止于残膜厚度。**这是两种闭合各自适用对象的错配，不是量纲问题**——两式量纲都自洽，开放槽式在其自身场景中也是对的。它也不是唯一可能构造的另一种简化，只是目前在用的两种之一。

**在本文条件下无法对它做定量比较，因为尚缺一步。** 本文系数按单位宽度定义（m$^3$）；换成渗透率（m$^2$）需要参考截面：$\kappa=K/L_{\rm ref}$，$L_{\rm ref}=A_{\rm ref}/W$。取流体截面则 $L_{\rm ref}=H_{\rm ref}=h+d/2$；取整个单胞则 $L_{\rm ref}=P$。两种口径差约一倍，且必须两侧同步采用。热管原式的孔隙率、速度基准以及 $f$ 与 $Re$ 的定义也仍待核对。**故本文不给出该关联式的标定误差**，Fig. fRe 只作依赖性的诊断读，不作误差曲线。

**在此前提下仍成立的是定性的、稳健的部分。** 两种口径下，固定 $d$ 时反推的 $f\,Re$ 都随 $h$ 增大而下降：$d=25$ nm 时约 41 倍（取 $A_{\rm ref}=WP$）或 11 倍（取流体截面），$d=120$ nm 时 4.1 倍或 2.4 倍。**倍数依赖口径，但"固定宽高比下仍存在 $h$ 依赖"这一点不依赖口径**——只含宽高比的关联式无法表示它。

因此条纹平均之作为主要对比对象有两条理由：**它是压印填充实际在用的闭合 [2,4,5]；在所考察的两种形式中，它是含过程变量的那一个。** Sec. IV B 的比较界定的是这个闭合能被推到多远，不是关于一维简化的一般结论，也不表明这样的简化只有两种。

**关于"可修正性"，这里要避免一个常见误述。** 乘性因子 $1/(1+e)$ 在 $e>-1$ 时对**任一符号**的误差都成立，故误差符号并不决定能否修正；决定能否修正的是**这个因子能否由几何预测**。本文采样的闭合恰好同号，使修正是单调的、方便；但单调是便利，不是必要条件。

**最后一点关乎预期的差异，不关乎其推导。** 条纹平均在每条槽内施加局部平板律；它**不是**把槽当作四面无滑移的封闭管，也不解析竖直侧壁，更不解析轴向速度与截面之间的耦合。槽口通向厚度为 $h$ 的连通液层，那里既不适用无滑移、也不适用自由面条件。把几何写成管道是另一个模型，两者之差是在此处预期出现偏差的一个理由，**但不是关于其大小的证据**。

### C. 系数误差对过程预测的影响

系数误差只有在向下游传递之后才有意义。为量出这一点，把每个几何、每个间隙下的**成对**系数代入均速闭合液膜的润滑模型，再将模型的荷载与排液时间同**离散参考系数**所得的对应量相比。配对是严格的：两个分量取自同一几何、同一间隙，任何量都不跨算例拼接。**本节统一用 $K_\parallel$ 表示沿槽分量、$K_\perp$ 表示跨槽分量**，与项目冻结口径一致；不使用笛卡尔下标，因为坐标一转动就会在不知不觉中把两者互换。

用了两个降阶模型。第一个轴对称、取等效导度 $(K_\parallel+K_\perp)/2$，从而使 $p\propto1/(K_\parallel+K_\perp)$，代数可手算核对。第二个在方形场上解 $K_\parallel p_{\parallel\parallel}+K_\perp p_{\perp\perp}=\mu V$、边界 $p=0$，两个分量各带权重进入，不作任何平均。两者中位数相差 0.1%，故第一个用于荷载已足够，第二个是敏感性分析所必需。

**恒速下压。** 问题对 $V$ 线性，对 $\mathbf{K}$ **联合地**是 $-1$ 次齐次；它**不是**分别对 $1/K_\parallel$ 与 $1/K_\perp$ 线性。因此只有两个分量以同一倍率变化时，压力与荷载才同比缩放；两者倍率不同时，压力场会改变形状，峰值压力比与荷载比可以不同——在本文采样几何上两者最多相差 $0.024$，即 2.4 个百分点。相对离散参考系数，十八个几何的荷载比在 0.371 至 0.901 之间，中位误差 $-38.8\%$。最坏一档是 $h=50$ nm、$d=120$ nm：$K_\parallel$ 被高估 $204.8\%$，预测荷载只剩参考值的 $37\%$。闭合在每个采样点都高估导度，故荷载误差**符号一致**；如上所述，这是关于符号的陈述，不是关于机制的陈述。

**恒载。** 给定荷载后闭合速率由阻力决定，$V(h)=F/S[\mathbf{K}(h)]$，$S$ 为单位速率所需荷载，排液时间为
$$
t=\frac{1}{F}\int_{h_f}^{h_0} S\!\left[\mathbf{K}(h)\right]\mathrm{d}h .
$$
**这个积分不能用某一个间隙的值替代。** 在统一行程 $125\to50$ nm 上，比值 $S_{\rm mod}/S_{\rm ref}$ 并非常数：$d=120$ nm 时由 0.371 变到 0.478，幅度 1.29 倍，且变化方向随槽深不同。五个槽深的时间比落在 0.405 至 0.876。把积分换成 $h_0$ 处的值，$d=25$ nm 时偏 3%，$d=120$ nm 时偏 18%。

**这一条的精度受采样限制，应当写明而不是隐去。** 每个槽深只有三到四个间隙点，积分取决于这些点如何连接：在采样点上用梯形法，与用对数–对数保形插值，时间比可差到 0.5 个百分点——与修正后的残差同量级。故本文的时间结果只报到这个精度，不再往下报。

**两种加载工况不可混淆。** 恒速时走完给定行程的时间是 $(h_0-h_f)/V$，按构造精确，与系数无关；误差全部出现在压力与荷载上。若在恒速下报一个时间误差，那它恒为零，会把问题说轻。恒载下时间由上式积分决定，其误差是另一个量。

**荷载误差从哪来。** 因荷载对 $\mathbf{K}$ 是 $-1$ 次齐次，它可以精确分解：
$$
\frac{F_{\rm mod}}{F_{\rm ref}}
=\underbrace{\frac{\hat h(A_{\rm mod})}{\hat h(A_{\rm ref})}}_{\text{各向异性}}\cdot
\underbrace{\frac{1}{\sqrt{(1+e_\parallel)(1+e_\perp)}}}_{\text{平均导度}},
$$
其中 $A=K_\parallel/K_\perp$，$\hat h$ 只依赖 $A$。乘积与实算比值吻合到机器精度。平均导度项落在 0.48–0.90，各向异性项落在 0.74–1.00。**这是降阶模型内部的代数恒等式**：它不是耗散预算，不指出几何的哪一部分产生了误差，平均项占优也不表明"一个几何变量的修正"在一般意义上是充分的。

**哪个分量更重要。** 齐次性同时定住权重：$w_\parallel+w_\perp=1$，$w_i=-\partial\ln F/\partial\ln K_{ii}$。$A=1$ 时两者相等；$A=4$ 时**沿槽**权重 0.78、跨槽 0.22；$A=15.5$ 时为 0.90 与 0.10。**只要 $A>1$——本文每个采样几何都是——沿槽分量权重更大**，因为液体优先沿槽排出。只把修正作用于沿槽分量，荷载中位残差仍有 $-12.2\%$；只作用于跨槽分量，为 $-32.9\%$，与权重次序一致。**这个次序同时反映权重与该分量自身误差的大小，不能读成机制的排序。**

权重不是系数的性质，它通过单一参数 $\Lambda=(L_\parallel/L_\perp)^2(K_\perp/K_\parallel)$ 依赖版图，$L_\parallel$ 沿沟槽方向量。版图沿沟槽拉长时液体必须横穿沟槽排出，$w_\parallel\to0$；沿横向拉长时 $w_\parallel\to1$。对近似方形版图（$0.8\lesssim L_\parallel/L_\perp\lesssim1.3$），两种取向在 $A\approx1$ 时 $w_\parallel$ 相差至多 0.22，在 $A\approx15$ 时相差 0.06。因此"某个分量更重要"的说法都以版图为条件，且当版图长边沿沟槽方向时**结论反转**。

**修正之后。** 把式(2b) 作用于模型系数后，荷载比为 0.937–1.051，即 $-6.3\%$ 至 $+5.1\%$，中位 $-2.1\%$；时间比为 0.962–1.006，即 $-3.8\%$ 至 $+0.6\%$——**修正后的时间比跨过 1**：在最小槽深处略高估排液时间，其余略低估。三点限制随此结论同行：残余随间隙变号，量级远小于未修正误差，但不可忽略；跨槽因子在 $h<50$ nm 不予声明，故凡版图给 $K_\perp$ 较大权重之处，$h=25$ nm 这一未声明格就会暴露——在 $L_\parallel/L_\perp\gtrsim10$ 时荷载偏差达 23%，此时方形场约 1% 的数会有误导性；比较的对象是**带自身离散不确定度的参考系数**，不是精确解。

**这证明了什么、没证明什么。** 本计算度量的是**已知系数误差在 Reynolds 型模型内部如何传播**。两个降阶模型共用该模型的假设——局部导度、压力驱动、无自由面——故这项检验**不检验模型本身**，也不能替代对闭合液膜的直接模拟；它同样不含毛细、气相与移动接触线。它证明的是**模型内后果的量级**：闭合误差把预测荷载压到参考值的 37%–90%，经验修正把它收到约 6% 以内。这是否构成"工程可用"，取决于应用所要求的容差，本节不设定该容差。

---

## 写作说明

### 〇、5.A 的证据基础与数字口径（**2026-10-18 22:50 重写**）

**① 现在 5.A 能说与不能说的**

| 可以说（有依据） | 不能说（已撤） |
|---|---|
| 一维形貌下式(1) 是 Reynolds 近似内的恒等式，四条条件见第 2 章 §G（Patir–Cheng 式23/24） | "所以全部误差唯一来自尖角" |
| 式(1) 与 DNS 之比 = **同一泛函（平均通量/平均梯度）在不同算子下的差**，故是 Reynolds 闭合自身的误差 | "这个差可以分摊到某个位置" |
| 局部立方律在**光滑但弯曲**的壁上也有误差：$\mu(v_{xx}+v_{zz})=-G$ 中丢掉 $v_{xx}$，代入局部解余 $GzH''/2$ | "没有尖角就没有误差" |
| 误差同号 ⇒ **荷载误差的符号**可事先知道 | "同号 ⇒ 尖角净增阻力、未重分配"（假二分） |
| Teyssèdre 的 2–80 倍说明润滑近似在这些间隙失效 | "2–80 倍相对式(1)"（实为相对该文 Stefan 型力） |
| Dewangan 谱模型 <3% 说明**光滑情形可解析处理** | "所以同一光滑面上局部立方律也 <3%"；"两者差别只在可微性" |

**② 5.A 里那个理论推导的性质（必须如实标注）**

本节写出的 $\mu(v_{xx}+v_{zz})=-G$ 与 $GzH''(x)/2$ 是**本文自行推导的候选分析**，
不是 Patir–Cheng 原文结论，也**不是对现有 LBM 场的机制验证**。它的作用只有一个：
说明"没有尖角也可能有误差"，从而支撑"唯一归因"不成立。**不得把它升级为机制证明。**

**③ 三条措辞边界**

| 不能写 | 应写 |
|---|---|
| "误差是尖角造成的" | "机制是候选解释；数据不能把尖角与壁面曲率、侧壁、截面重分布分开" |
| "尖角修正" | "局部立方律的经验修正" |
| "$d/w$ 决定尖角占流动的份额" | "$d/w$ 能整理采样残差的次序" |

**④ 引用与编号**

本节用 [12]（Patir–Cheng）、[15]（Teyssèdre）、[17]（Dewangan 2024 TCFD，摘要级）。
`\tag` 保持 1 / 2a / 2b，与第 1 章一致；跨章引用已在改稿时回源核对（曾被误写为 Eq. 3）。

**⑤ 篇幅**

5.A 现为 497 词。四段结构：恒等 → 比值是什么 → 为什么不能定位 → 候选与经验修正。
**第一段与第三段不可压**：前者是立论，后者是防"唯一归因"的唯一屏障。

---

### 〇·补　5.C 的依据、数字来源与可压缩处（2026-10-18 22:50 重写）

**① 这一节不是推测，是已算完的**

数据与脚本在 `CASE/D_series/D3_squeeze_error_propagation/`：
`squeeze_error_propagation.py`（原表 1–4）、`aspect_ratio_weights.py`（表 5–7）、
`make_table2b_common_stroke.py`（**本轮新加：统一行程的权威表**）、`make_fig9.py`。
**无手填数字。**

**② 本轮更正的三处计算口径（这是审查报告 M14/M15/M18 的根因）**

| 项目 | 原来 | 现在 | 影响 |
|---|---|---|---|
| 积分行程 | $d=25$ 从 25 nm 积起，其余从 50 nm 起 | **统一 125→50 nm** | 时间比与冻结误差全部改变 |
| Sm/Sref 字段 | 存的是**模型 A 导度比的倒数** | 模型 B 的 $S_{\rm mod}/S_{\rm ref}$ | $d=120$ 由 2.10–2.76 改为 **0.371–0.478** |
| 修正因子的作用对象 | 有一处乘在**参考系数**上 | 一律乘在**模型系数**上 | 否则会把误差放大成反号 |

> ⚠ 第三条我犯过**三次**（每次都是"把修正乘在 DNS 值上"）。凡见"修正后误差变大"，先查这一条。

**③ 每个数字的出处（正文只引用这些）**

| 正文数字 | 来源 | 备注 |
|---|---|---|
| 荷载比 0.371–0.901，中位 −38.8% | `make_table2b` 段 A | 与审查报告复算一致 |
| 荷载比修正后 0.937–1.051，中位 −2.1% | 同上 | 落点 −6.3%~+5.1% |
| 峰值/荷载最大差 2.4003 pp | 同上 | 原写"峰值同样"，不准确 |
| 时间比 0.405–0.876 | `make_table2b` 段 B（PCHIP） | 统一行程 |
| 时间比修正后 0.962–1.006 | 同上 | **跨过 1，不是全部低估** |
| 梯形法与插值法差 ≤0.5 pp | 段 B 两口径对照 | 采样限制，已写进正文 |
| $S_{\rm mod}/S_{\rm ref}$（$d=120$）0.371–0.478 | 段 B | 幅度 1.29 倍 |
| 冻结 vs 积分 3%（$d=25$）／18%（$d=120$） | 段 B | 原写 19.1%，为模型 A |
| 均值项 0.48–0.90、形状项 0.74–1.00 | 分解表 | 乘积吻合到机器精度 |
| $w_\perp$ = 0.50 / 0.78 / 0.90 | 见 ④ | **注意分量归属** |
| 只修沿槽 −12.2%／只修跨槽 −32.9% | 本轮复算 | 原写 −33.1/−8.2 且分量标反 |
| $L_\parallel/L_\perp\gtrsim10$ 时 23% | 表 7 | $h=25,d=100$ 那格 |

**④ 一处必须写清的分量归属（原稿标反）**

齐次性给出 $w_\parallel+w_\perp=1$。数值（用定义直接微扰核对，非由 $\hat h$ 代数式推）：
$A=1$ 时各 0.50；$A=4$ 时 $w_\parallel=0.78$、$w_\perp=0.22$；$A=15.5$ 时 0.90 与 0.10。
**即 $A>1$ 时沿槽分量权重更大**——液体优先沿高导度方向排出。

> ⚠ **本轮我在这一点上先改错了再改回**：曾据 $\hat h$ 关系误判 0.78 属跨槽，正文一度写反。
> 用 $w_i=-\partial\ln F/\partial\ln K_{ii}$ 直接微扰复核（$A=4$ 时 $K_\parallel$ 增 1% 使荷载降 0.77%），
> 确认 **0.78 属沿槽**，初稿原本正确。**教训：权重必须用定义法微扰验，不能靠代数式换算。**

**⑤ 三条必须守住的措辞**

| 不能写 | 原因 | 已写成 |
|---|---|---|
| "验证了挤压模型" | 只测误差传播 | "measures how a known coefficient error propagates inside a Reynolds-type model" |
| "沿槽分量更重要"（无条件） | 方形场结果，$R$ 一变即反转；且权重归属原稿标反 | "conditional on the field, and it inverts…" |
| "修正后全部低估 1.3–4.2%" | 修正后时间比跨过 1 | "−3.8% to +0.6%，跨过 1" |
| "把预测荷载减半或加倍" | 本文数据是压到 37%–90%，非"减半" | "reduces the predicted load to 37–90%" |
| "工程可用" | 无用途判据 | "取决于应用容差，本节不设定" |

**⑥ 篇幅与压缩方案**

5.C 现为 **1118 词**（5.A 497、5.B 683，本章 EN 合计 2298）。
比改前（821 词）长，因为补进了采样限制、峰压差、坐标约定与三处更正。若要压缩，按此顺序：

1. "Two reduced models" 的模型 A 细节 → 只留"两模型中位差 0.1%"（省 ~50 词）；
2. $\hat h$ 的定义移入图注（省 ~40 词）；
3. "Where the load error comes from" 可压一半，但**必须保留"这是代数恒等式、不是耗散预算"**。

**不可压缩**：恒速/恒载的区分；修正后时间比跨过 1；$h=25$ 跨槽在细长版图上暴露；
以及"参考系数自带离散不确定度"。

**⑦ 图表**

Fig 9（荷载 / 时间 / 权重 / 修正后）与 Fig 10（权重与误差 vs 长宽比）已生成。
⚠ **Fig 9 与 Fig 10 用的是 $x/y$ 下标**（$x$ 即沿槽），与本节改用的 $K_\parallel/K_\perp$ 不一致。
数值本身正确（$w_x=0.78$ 就是 $w_\parallel=0.78$），**只需统一标签**，不必重算。
另：(b) 面板的时间比按旧行程绘制，与本节 0.405–0.876 相差 <1%，重绘时一并对齐。
**重画前正文不逐面板引用。**

---

### 一、5.B 要解决的问题

此前论文的结构是：引言说"压印建模用 Jain 闭合" → 第 5 章说"该闭合误差 10–205%" → 给修正公式。

**中间有一个洞**：为什么偏偏挑这一个闭合？懂润滑理论或热管的审稿人会立刻问：还有别的一维平均，为什么只比这一个。

5.B 的作用是把"选对比对象"从**默认动作**变成**论证过的选择**，并且**只论证到能论证的为止**。

### 二、2 个论点（原为 3 个，第 3 个已撤）

**① 适用对象错配（不是量纲错配）**

开放槽式的**指定形式里不含 $h$**，而 $h$ 是压印的过程变量。这足以说明该形式不能描述本文问题，
但**不能**说它"量纲不对"——两式量纲都自洽，它在其自身场景中是对的。
原稿写"理由在量纲而非数值"，**该表述不成立，已改**。

**② 反推 $f\,Re$ 显示存在 $h$ 依赖（定性，不给标定误差）**

若开放槽形式成立，固定 $d$ 时 $f\,Re$ 应为常数。反推结果显示它随 $h$ 显著下降，
倍数在两种换算口径下分别为 4.1–41（÷P）与 2.4–11（÷$H_{\rm ref}$）。
**倍数依赖口径，结论"存在 $h$ 依赖"不依赖口径。**

但**不再报 95%、−90%/+322%**：这两个数要求先定 $K^{[m^3]}\to K^{[m^2]}$ 的参考截面，
再核清热管原式的孔隙率、速度基准与 $f,Re$ 定义。这两步本轮都没做完，
故这类数一律撤下，正文只保留"依赖关系"这一层。

**③（已删除）"误差符号决定可修正性"**

原稿写"方向一致地错可以修，方向不一致的错不能修"。**这是错的，已删。**
正确说法：乘性因子 $1/(1+e)$ 在 $e>-1$ 时对任一符号都成立；真正的难点是**能否由几何预测该因子**，
而不是符号。5.B 末尾保留了一段说明，避免读者也这样误判。

### 三、必须守住的五条边界

| 不能写 | 原因 | 应写 |
|---|---|---|
| "热管公式误差 322%" / "最大误差仍达 95%" | 依赖未核的定义与猜测的 $f\,Re$ | 只写"存在 $h$ 依赖"，不报标定误差 |
| "两式量纲不一致" | 两式量纲都自洽 | "该形式的指定对象不含 $h$" |
| "一维简化都不行" | 只考察两种，不能推广 | "所考察的两种中，只有一种含过程变量" |
| "方向一致才能修正" | 数学上不成立 | "能否由几何预测修正因子才是关键" |
| "本文首次指出…" | 未穷尽检索 | "本节表明…" |

### 四、还欠什么

1. **$f\,Re$ 的原始定义未核**（Faghri 1995 / Chi 1976）：孔隙率、速度基准、$f$ 与 $Re$ 的水力长度。
   在核清之前，**任何该式的误差数字不得进正文**。
2. **参考截面口径未定**：$L_{\rm ref}=H_{\rm ref}$ 与 $L_{\rm ref}=P$ 需二者择一并两侧同步。
3. 图 fRe 已就位（`figures/paper/Fig_fRe_collapse.*`），但按第 2 条，正文只能把它当**依赖性诊断**，
   图注不得写成"误差曲线"；且 $d=75/120$ 没有 $h=25$ 数据，**不得写成每条曲线都由 25 扫到 125**。
4. 本节引用 `[2,4,5]`，编号需按最终文献表调整。

### 五、逐条处置：机制审查 20 项 → 本轮改动

审查报告：`Chapter5_mechanism_audit_20261018/REPORT.md`。**M01–M20 逐条对照如下。**

| 编号 | 审查判断 | 本轮处置 |
|---|---|---|
| M01 | 条件恒等成立，可保留 | **保留**；补"限定为该单元问题，不推广" |
| M02 | 唯一机制不成立 | **5.A 整段重写**；新增"比值不能定位误差"一段 |
| M03 | 跨论文比较不能归因 | **删除**"差别只在可微性""幅度与间隙相同"；改为"<3% 只说明光滑情形可解析处理" |
| M04 | 同号不定位耗散 | 删除"尖角增加阻力而非重分配"；改述为"关于符号的陈述，不是关于机制" |
| M05 | Teyssèdre 类比需限定 | 补明 2–80 倍是相对**该文 Stefan 型力**，非式(1) |
| M06 | 经验变量不是机制证明 | 删除"$d/w$ 决定尖角份额"；改"能整理采样残差次序"；"尖角修正"→"局部立方律的经验修正" |
| M07 | 范围夸大 | 改"适用对象错配"；删"唯一含 $h$"；补"不表明只有两种" |
| M08 | 单位与定义缺口 | **撤下** 95% 与 −90/+322%；补参考截面口径与未核定义 |
| M09 | 子命题与文献校核分开 | 同上；删"最宽容""唯一含 $h$" |
| M10 | 变号不可修是错误命题 | **整条删除**；改为"能否由几何预测因子" |
| M11 | 边界模型解释错误 | 删除"四面无滑移矩形管"；改"局部平板律，不解析侧壁与截面耦合" |
| M12 | 数字可复算、措辞需限定 | 保留 0.371–0.901；"真值"→"离散参考系数" |
| M13 | 线性解释错误 | 改"对 $V$ 线性、对 $\mathbf{K}$ 联合 $-1$ 次齐次"；补峰值/荷载差 2.4003 pp |
| M14 | 比值标反且模型混用 | **改** $S_m/S_{\rm ref}$：$d=120$ 为 0.371–0.478（原 2.10–2.76） |
| M15 | 冻结比较混用 A/B | 改为统一行程的模型 B：3%（$d=25$）／18%（$d=120$） |
| M16 | 分解可保留，推论要收 | 保留恒等式；**删**"故一变量修正足够"；注明非耗散预算 |
| M17 | 坐标重命名未交代 | 全节改用 $K_\parallel/K_\perp$；明写"不使用笛卡尔下标" |
| M18 | 修正时间数字未复现 | **重算**：0.962–1.006（−3.8%~+0.6%），**跨过 1** |
| M19 | 限定数据域与参照 | "真值"→"参考值"；删"减半或加倍"；删"工程可用" |
| M20 | 符号约定待补 | 正文统一 $K_\parallel p_{\parallel\parallel}+K_\perp p_{\perp\perp}=\mu V$；量值比不受符号影响 |

**六项做了删改而未加新计算**（M02/M03/M04/M10/M11/M16）：这些是措辞与逻辑问题，删掉即已闭合。
**三项改了数字**（M14/M15/M18）：已用 `make_table2b_common_stroke.py` 重算，输出
`results/table2b_time_common_stroke.csv`，可复核。
**一项涉及图**（M17 的坐标）：正文已改，**图未重画**，见 〇·补 ⑦。

### 六、篇幅

5.B 现为 683 词（改前 643）。净增来自：撤数字后必须补的"为什么不能报这些数"、
以及末尾关于可修正性的更正段。若需压缩，先删"最后一点关乎预期差异"那段（~90 词），
它只是预期，不是论证。
