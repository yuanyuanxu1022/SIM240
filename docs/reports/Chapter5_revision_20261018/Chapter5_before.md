# 第 5 章 草稿（5.A 立论 + 5.B 对比对象 + 5.C 误差传播）

> 本章现有**三节**，各管一件事，顺序不可换：
>
> | 节 | 标题 | 回答的问题 | 性质 | 篇幅 |
> |---|---|---|---|---|
> | **5.A** | The error is a property of the corner, not of the averaging | 误差**从哪来** | 定性/立论 | 394 词 |
> | **5.B** | Why the stripe average, and not another one-dimensional closure | **为什么拿条纹平均去比** | 对比对象的选择 | 643 词 |
> | **5.C** | What the coefficient error does to the process prediction | **错多少、影响什么** | 定量 + 下游 | 821 词 |
>
> **5.A → 5.B**：先说明"误差是尖角造成的"，才能回答"该拿哪个闭合去比"。
> **5.B → 5.C**：确认"这个闭合不是随手挑的"，它的误差才值得往下游追。
>
> 5.B 之后、5.C 之前，仍接**误差地图主表**（Sec. IV B）与**修正公式推导**（Eq. 2 → Eq. 3）。
> 5.C 是本章的收束：把系数误差换算成荷载与排液时间的偏差，并给出修正后的残余。
>
> **本章 EN 合计 1,864 词。** 若期刊限制，压缩方案见写作说明 〇·补 ⑤。

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

**Which component matters.** Homogeneity also fixes the weights, $w_\parallel+w_\perp=1$ with $w_i=-\partial\ln F/\partial\ln K_{ii}$. At $A=1$ they are equal; at $A=4$ the across-groove weight is 0.78 and the along-groove weight 0.22; at $A=15.5$, 0.90 and 0.10. The across-groove component therefore carries more weight whenever $A>1$, which is the case at every sampled geometry. Correcting the along-groove component alone leaves a median load error of $-12.2\%$; correcting the across-groove component alone leaves $-32.9\%$. That ordering reflects both the weight and the size of that component's own error, and it must not be read as a ranking of mechanisms.

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

**哪个分量更重要。** 齐次性同时定住权重：$w_\parallel+w_\perp=1$，$w_i=-\partial\ln F/\partial\ln K_{ii}$。$A=1$ 时两者相等；$A=4$ 时**跨槽**权重 0.78、沿槽 0.22；$A=15.5$ 时为 0.90 与 0.10。**只要 $A>1$——本文每个采样几何都是——跨槽分量权重更大。** 只修正沿槽分量，荷载中位残差仍有 $-12.2\%$；只修正跨槽分量，为 $-32.9\%$。**这个次序同时反映权重与该分量自身误差的大小，不能读成机制的排序。**

权重不是系数的性质，它通过单一参数 $\Lambda=(L_\parallel/L_\perp)^2(K_\perp/K_\parallel)$ 依赖版图，$L_\parallel$ 沿沟槽方向量。版图沿沟槽拉长时液体必须横穿沟槽排出，$w_\parallel\to0$；沿横向拉长时 $w_\parallel\to1$。对近似方形版图（$0.8\lesssim L_\parallel/L_\perp\lesssim1.3$），两种取向在 $A\approx1$ 时 $w_\parallel$ 相差至多 0.22，在 $A\approx15$ 时相差 0.06。因此"某个分量更重要"的说法都以版图为条件，且当版图长边沿沟槽方向时**结论反转**。

**修正之后。** 把式(2b) 作用于模型系数后，荷载比为 0.937–1.051，即 $-6.3\%$ 至 $+5.1\%$，中位 $-2.1\%$；时间比为 0.962–1.006，即 $-3.8\%$ 至 $+0.6\%$——**修正后的时间比跨过 1**：在最小槽深处略高估排液时间，其余略低估。三点限制随此结论同行：残余随间隙变号，量级远小于未修正误差，但不可忽略；跨槽因子在 $h<50$ nm 不予声明，故凡版图给 $K_\perp$ 较大权重之处，$h=25$ nm 这一未声明格就会暴露——在 $L_\parallel/L_\perp\gtrsim10$ 时荷载偏差达 23%，此时方形场约 1% 的数会有误导性；比较的对象是**带自身离散不确定度的参考系数**，不是精确解。

**这证明了什么、没证明什么。** 本计算度量的是**已知系数误差在 Reynolds 型模型内部如何传播**。两个降阶模型共用该模型的假设——局部导度、压力驱动、无自由面——故这项检验**不检验模型本身**，也不能替代对闭合液膜的直接模拟；它同样不含毛细、气相与移动接触线。它证明的是**模型内后果的量级**：闭合误差把预测荷载压到参考值的 37%–90%，经验修正把它收到约 6% 以内。这是否构成"工程可用"，取决于应用所要求的容差，本节不设定该容差。

---

## 写作说明

### 〇、5.A 的证据基础与数字口径（**动笔前必读**）

**① 这一节的三个数字，出处必须分清**

| 数字 | 来源 | 证据级别 |
|---|---|---|
| 跨槽 **+8.1%~+54.2%** | 本文 DNS 误差矩阵（**36 档，每方向 18**），相对条纹平均，**未修正** | 自有数据，可复算 |
| 沿槽 **+10.3%~+204.8%** | 同上 | 自有数据，可复算 |
| 正弦壁 **<3%** | Dewangan 2024, TCFD **38**(1):39–59，**摘要** | ⚠ **摘要级**（Springer 闭源，Unpaywall 无 OA） |

> **⚠⚠ 一处必须守住的对应关系**：TCFD 那篇做的是 **transverse flows（跨槽方向）**。
> 所以与它并排的**只能是跨槽的 +8.1%~+54.2%**，**绝不能用沿槽的 205%**。
> 我在口头说明中一度把两者写成"+10~205% vs <3%"，**那是错配**，切勿带进文稿。
> 205% 属于沿槽，与那篇不同方向、不可直接对撞。

**② 为什么不能说"该文区间与我们相同"**

摘要只写"bridge the gap between the limits of thin and thick channels"，**没有给具体数值区间**；
全文未取得，无法核实。故正文写法是"覆盖薄—厚过渡区，本文间隙正落在该过渡区内"，
**不写"同一区间"、"相同 h/L"之类可被追问的具体断言**。
（若日后取得全文，应补成确数，并把这句话换成可直接比对的形式。）

**③ 为什么这个并置是公平的**

容易被质疑：TCFD 用的是**谱方法**，不是式(1)那样的零阶平均闭合，两者不是同一个东西。
故正文已明写："这一并置比较的是**各自几何下最好的解析处理**，而非两个闭合之间的优劣。"
这个口径的好处是：它问的是"**更好的分析能不能救活一维简化**"——
正弦壁能（<3%），方波不能（几十个百分点），**差别只在连续可微与否**。**这正是我们要的结论。**

**④ 与 Patir–Cheng 原文的对应（已核，2026-10-18）**

其式(23) 横向 $\phi_x=1/[h^3E(1/h_T^3)]$、式(24) 纵向 $\phi_x=E(h_T^3)/h^3$，
由随机 Reynolds 方程与平均 Reynolds 方程**比对解析导出**（非拟合）。
对等占空比方波：$E(h_T^3)=\tfrac12[h^3+(h+d)^3]$、$1/E(1/h_T^3)=2/(h^{-3}+h_g^{-3})$，
**恰为式(1)的 $K_\parallel$ 与 $K_\perp$（差一个 1/12 因子）**。
⇒ 故"只要 Reynolds 近似成立，平均不产生误差"一句**有原文支撑**，不是推论。

**⑤ 必须守住的三条措辞边界**

| 不能写 | 原因 | 应写 |
|---|---|---|
| "正弦壁误差 3%，我们是 205%" | 方向错配（跨槽 vs 沿槽） | "正弦壁 **<3%**，方波**跨槽 8.1–54.2%**" |
| "我们与 TCFD 用同一区间" | 全文未取得，区间无数值 | "覆盖薄—厚过渡区，本文间隙落在其中" |
| "一维平均从根本上不可用" | 只证了方波；正弦壁恰恰可用 | "**方波**上不可用；正因如此，误差归因于尖角" |

**⑤·补　档数口径（2026-10-18 校正）**

本文误差数字来自 `summary.csv`（dx=5，18 档 = 9 P + 9 T）＋ `d75/h25/d120_summary.csv`（各 6 档），
**合计 36 档（每方向 18 档）**。

⚠ **不要写"48 档"**：48 是 `SIM240_论文骨架` 里 D2 **计划**的注册总数
（主矩阵 22 + μ 对照 2 + 斜槽 6 + d75 6 + h25 6 + d120 6），
其中 **μ 对照与斜槽不在上述三个 CSV 中**，未参与本文的误差统计。
**误差统计的 n = 36，不是 48。**

**⑥ 引用编号**

本节用 `[12]`（Patir & Cheng 1978）、`[15]`（Teyssèdre 2013）、`[17]`（Dewangan 2024, TCFD）。
`[17]` 为**新增条目**，第 1 章现有 16 条，合并文献表时顺延即可；
但 `[17]` 目前**只有摘要级证据**，文献表须如实标注（照第 1 章 `[14]`/`[16]` 的写法）。

**⑦ 篇幅**

5.A 英文 **394 词**（实测），中文 **~640 字**。三段结构不能砍：
第一段（恒等式，立论）与第二段（两条几何并置，证据）是核心；
第三段（同号 + 收敛，机制）可压缩一半，但"同号"必须留——
它是"可修正/不可修正"论证（见 5.B 第三条论点）的前置。

---

### 〇·补　5.C 的依据、数字来源与可压缩处（2026-10-18 17:00）

**① 这一节不是推测，是已算完的**

全部数据与脚本在 `CASE/D_series/D3_squeeze_error_propagation/`：
`squeeze_error_propagation.py`（表 1–4）、`aspect_ratio_weights.py`（表 5–7）、`make_fig9.py`（Fig 9）、
报告 `PROPAGATION_REPORT.md` 与 `ASPECT_RATIO_REPORT.md`。**无手填数字**。

**② 每个数字的出处（写进正文的只有这些）**

| 正文数字 | 来源 | 备注 |
|---|---|---|
| 荷载 0.371–0.901，中位 −38.8% | 模型 B，18 组 | 模型 A 中位 −38.9% |
| 峰值 −65.3%–−9.9% | 模型 B | 模型 A 为 −63.7%–−9.9% |
| 时间 0.405–0.875 | 恒载 $125\to50$，模型 B | |
| $S_m/S_D$ 2.10–2.76 | $d=120$ | 这就是"必须积分"的直接证据 |
| 冻结 vs 积分 3.0%/19.1% | $d=25$/$d=120$ | |
| 均值项 0.49–0.90、形状项 0.74–1.00 | 分解表 3 | 乘积与实算吻合到 3 位小数 |
| $w_x$ = 0.50 / 0.78 / 0.90 | $A$=1 / 4 / 15.5 | 齐次性给出 $w_x+w_y=1$ |
| 单换 ±：−33.1% / −8.2% | 表 1 两列 | 中位数 |
| 修正后 0.938–1.051、中位 −1.0% | 表 4 | |
| 时间修正后 0.958–0.987 | 表 4 同链条 | |
| $L_x/L_y\gtrsim10$ 时 23% | 表 7 | $h=25,d=100$ 那格 |

**③ 三处必须守住的措辞**

| 不能写 | 原因 | 已写成 |
|---|---|---|
| "我们验证了挤压模型" | 只测误差传播，不测模型 | "measures how a known coefficient error propagates inside a Reynolds-type model" |
| "沿槽分量更重要"（无条件） | 方形场的性质，$R$ 一变就反转 | "conditional: holds for the square field used here, and it inverts for…" |
| "修正后误差可忽略" | 大间隙端过修（1.051），且 $h=25$ 跨槽未声明 | 两点限制随结论同行 |

**④ 与 5.A / 5.B 的分工（不要重复）**

- 5.A 回答"误差从哪来"（尖角 vs 平均）——**定性**
- 5.B 回答"为什么拿条纹平均去比"——**对比对象的选择**
- 5.C 回答"错多少、影响什么"——**定量 + 下游**
故 5.C 不再论证机制，只引用 5.A 的结论（"方向一致 ⇒ 可修正"）。

**⑤ 篇幅与压缩方案**

5.C 现为 **821 词**（5.A 394、5.B 643，本章 EN 合计 1,864）。
若需压缩，按以下顺序，**都不伤论证**：

1. 删"Two reduced models"那段的模型 A 细节（省 ~60 词）——只保留"两模型中位差 0.1%"这一句；
2. "Where the load error comes from" 的 $\hat h$ 定义可移入图注（省 ~40 词）；
3. "What this does and does not establish" 可压到两句（省 ~50 词），但**不能删**——
   它是防"过度声称"的唯一屏障。

**不可压缩**：恒速/恒载两工况的区分（否则会被读成"时间没错"）、$h=25$ 跨槽暴露那一条（否则是隐藏短板）。

**⑥ 图表**

Fig 9（四面板：荷载 / 时间 / 权重 / 修正后）与 Fig 10（权重 vs 长宽比、误差 vs 长宽比）已生成，
图注见 `CASE/D_series/D3_squeeze_error_propagation/results/`。**5.C 的每一段都可指向某个面板**。

---

### 一、这一节解决什么问题

此前论文的结构是：

1. 引言说"行业用 Jain 闭合"
2. 第 5 章说"这个闭合误差 10–205%"
3. 给修正公式

**中间有一个洞**：为什么偏偏挑这一个闭合？如果审稿人懂热管或润滑理论，会立刻发现还有别的"一维平均"，而论文没解释为什么只比这一个。

补上这一节，把"选对比对象"从**默认动作**变成**论证过的选择**。

### 二、三个论点，逐个说明

**① 只有条纹平均含 $h$（量纲论证，最硬）**

这一条不依赖任何数值，只靠"公式里有没有 $h$"。压印的物理就是 $h$ 在变，不含 $h$ 的模型连描述对象都谈不上。

**② 反推 fRe 证明"不含 $h$"的后果（数据论证）**

如果开放槽形式对，同一 $d$ 下 $f\,Re$ 应恒定。实测差 4–41 倍。这一条的好处是：**它的结论不依赖 $f\,Re$ 图表的原始出处**（换个图表只是整体平移常数），因此证据链很短、很难被反驳。

**③ 误差符号（可修正性论证）**

这一条最容易被忽略，但它是论文**方法论上最重要的一句**：

> 方向一致地错可以修，方向不一致的错不能修。

这直接解释了"为什么本文的贡献是给修正公式，而不是换模型"。

### 三、必须守住的四条边界

| 不能写 | 原因 | 应写 |
|---|---|---|
| "热管公式误差 322%" | 那个数依赖猜来的 $f\,Re=14.5$ | "即使自选最优常数，最大误差仍达 95%" |
| "一维简化都不行" | 只检验了两种，不能推广 | "这两种在此几何下均不适用，原因不同" |
| "热管领域忽略了间隙" | 他们的工况没有间隙变量，不是疏忽 | "该闭合不含 $h$，因其适用场景中 $h$ 不是变量" |
| "本文首次指出…" | 未穷尽检索 | "本节表明…" |

### 四、还需补什么

1. **$f\,Re$ 的原始出处未核**（Faghri 1995 / Chi 1976）。若正文要出现具体数值 14.5，必须先取得原书核对；若只写"典型值约 14"，可引二手综述并注明。
2. **图 fRe 已就位**：`figures/paper/Fig_fRe_collapse.{png,pdf,svg}`，图注见 `Fig_fRe_caption_and_record.md`。
3. 本节引用了 `[2,4,5]`（Jain 2017 / Ban 2020 / Ban 2021），编号需按最终文献表调整。

### 五、篇幅

英文约 640 词，中文约 760 字。若第 5 章篇幅紧张，可压缩第 3 段（量纲论证）与第 6 段（符号论证）各一半，保留第 4、5 段（数据与宽容检验），因为那两段是独有的。
