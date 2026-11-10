# Chapter 1 — Introduction（完整草稿 v1.0）

> 目标期刊：Physics of Fluids（二区优先）／Microelectronic Engineering（三区备选）
> 语言：英文（投稿正文语言）
> 日期：2026-10-17；证据口径修订：2026-10-18
> 本轮修订依据：`SIM240_single_phase_audit_20261018/REPORT.md`；核心结论与修正验证台账见 `SIM240_manuscript_revision_20261018/CORE_CLAIMS.md`。仅为待作者确认的工作稿，不代表投稿放行。
> 状态：**可送老师审阅的完整草稿**，非定稿。文中 `[n]` 对应文末参考文献表。
> ⚠ 查新纪律：全文**未使用 "first" / "for the first time" / "no one has"**。任务 C（WoS 被引列表）完成前不得添加此类措辞。

---

## I. INTRODUCTION

### ¶1　工艺背景与瓶颈所在

> **【图 1 已就位】** 本段与 ¶2 对应的装置/单胞示意图已完成：`figures/paper/Fig1_device_and_unitcell.png`（+pdf/svg），图注见 `figures/paper/Fig1_caption_and_record.md`。建议在 ¶1 末或 ¶2 首句处插 **“FIG. 1”** 引用。

Jet-and-flash imprint lithography (J-FIL) forms nanoscale patterns by dispensing picoliter resist droplets onto a substrate, pressing a relief-patterned, UV-transparent template into them, letting the resist fill the template features by capillary and viscous action, and then curing the film under UV light [1]. Because the process reproduces features by mechanical molding rather than optical imaging, its resolution is set by the template and is largely independent of the field size [1]. The step that limits throughput, however, is not the patterning but the filling: in a competitive process the resist must close a field in roughly one second, and this filling step consumes the largest share of the throughput budget [1].

Filling takes place in a geometry with two very different length scales. Laterally, a drop pattern spans millimetres to centimetres; vertically, the gap between the mold protrusions and the substrate closes from micrometres down to a few tens of nanometres, while the grooves themselves remain partly unfilled. Flow therefore occurs simultaneously in a thin annular film under the protrusions and in the deeper grooves between them, and the two paths offer very different resistance. Because the grooves run in one direction, this resistance is strongly directional: the resist spreads readily along the grooves and much more slowly across them. That directionality controls where the liquid front arrives first, how drops merge, and where gas is finally trapped — the origin of the void defects that limit yield [1,2].

### ¶2　介尺度模型与所依赖的闭合关系

Simulating the flow at the scale of a full field while resolving each nanometre feature is not feasible, and it is not necessary: the lateral scale is five orders of magnitude larger than the gap, so the lubrication approximation applies [2,3]. The template pattern is then represented not by resolved geometry but by an effective permeability tensor $\mathbf{K}$ that maps the macroscopic pressure gradient to the depth-integrated flux,
$$
\mathbf{q} = -\frac{\mathbf{K}}{\mu}\nabla_\parallel p , \qquad
\frac{\partial h}{\partial t} + \nabla_\parallel\!\cdot\mathbf{q} = 0 ,
$$
where $\mu$ is the resist viscosity and $\nabla_\parallel$ is the in-plane gradient [2,4]. For a line-and-space pattern the two principal components of $\mathbf{K}$ follow from two elementary rules. Along the grooves the pressure gradient is common to all stripes, so the fluxes add: the cubic conductances are averaged arithmetically. Across the grooves the flux is common and the pressure drops add: the conductances are averaged harmonically. For a pattern of period $P$, groove width $w$ and groove depth $d$, with a residual gap $h$ under the protrusions, these rules give

$$
K_\parallel^{\rm mod}=\frac{1}{24}\left[(h+d)^3+h^3\right],
\qquad
K_\perp^{\rm mod}=\frac{1}{6}\,\frac{(h+d)^3\,h^3}{(h+d)^3+h^3},
\tag{1}
$$

as the transport coefficients per unit width. Equation (1) is the arithmetic–harmonic ("stripe") average, which is mathematically identical to the local cubic law routinely used for patterned channels [3]; the form employed in imprint modeling follows the same construction [2,4].

Equation (1) is attractive precisely because it is closed-form and requires no computation. It is, however, a one-dimensional construction applied to a two-dimensional cross-section, and it therefore discards two things. The arithmetic average treats each stripe as an independent parallel-plate channel, so it omits the shear on the vertical side walls of a groove. The harmonic average treats the protrusion and the groove as two resistors in series, so it omits the additional dissipation where the flow contracts into and expands out of the groove. These neglected spatial variations motivate candidate explanations for closure bias. Their separate quantitative contributions are not established by the present coefficient comparisons.

### ¶3　已核实的模型沿用与本研究的窄问题

The closure has been adopted and extended repeatedly, but always as an input. Jain et al. [2] introduced the anisotropic permeability into a multi-drop spreading model for line-and-space templates; their comparison with experiment was qualitative, aimed at reproducing the observed directionality of spreading rather than at testing the magnitude of $\mathbf{K}$. Ban and Bonnecaze [4] subsequently showed that permeability alone cannot reproduce the measured flow front and added an anisotropic capillary-pressure boundary condition derived from Surface Evolver calculations; their key finding is that both anisotropic permeability and anisotropic capillary pressure are required, and their quantitative checks concern the capillary pressure, not the permeability. The same group later extended the framework to templates carrying several pattern regions [5], where a change of pattern orientation from 0° to 90° is handled by interchanging $k_{xx}$ and $k_{yy}$ — an operation that presumes the tensor transformation law holds.

In the imprint-model studies examined here [2,4,5], the closure supplies the transport coefficients; their application-level comparisons do not by themselves establish the accuracy of its principal values for the present fully filled rectangular unit cell. The literature search remains incomplete, so this observation is not a claim that no previous resolved-flow comparison exists.

The closure itself is not peculiar to imprint modeling. For a one-dimensional profile it is not merely analogous to the pressure flow factor of the average flow model of Patir and Cheng [12]; under the four conditions listed in Sec. II it is the same object, and for a square wave the identity is exact rather than approximate. The resolved calculations evaluate the same functional — mean flux over mean gradient — under a different operator, Stokes rather than Reynolds, so the difference between the two is a property of the approximation and not of the averaging. The accuracy of that model has been examined in tribology for four decades, and the studies divide by what they take as the reference solution. Where the reference is the Reynolds equation itself — as in the original flow-factor determination [12] and in the comparison of averaging schemes for textured contacts [13] — the comparison measures the upscaling error alone, holding fixed the inability of the Reynolds equation to represent the flow at a sharp corner. Where the reference is a resolved Stokes or Navier–Stokes solution, the two errors are measured together; this has been done for longitudinal and transverse roughness in elastohydrodynamic contacts [14], for a single surface defect [6], and for Gaussian random roughness [7]. For rectangular grooves the resolved-flow comparison also exists, but it is stated as a force, not as a transport coefficient. Teyssèdre et al. [15] solved the Stokes problem by finite elements on a rectangular line grating, that is, on the present geometry, for shape ratios up to $h/L=2.4$ spanning the range used here, and found the imprint force to exceed the lubrication estimate by a factor of two to eighty, rising as the gap opens. That ratio and the one reported below are not the same measurement — theirs is a squeeze flow in which the polymer must turn into the cavity, ours a pressure-driven conductance at fixed geometry — but both trace to the corner flow that the lubrication approximation omits. They concluded that simplified flow models cannot be used above $h/L=0.1$, and the same work simulated capillary filling of such a groove with a moving contact line. What that study does not report is the transport tensor itself: neither of its two principal values, nor the ratio between them. Anisotropic filling of rectangular cavities has been observed directly [16], the front advancing faster along the cavity than across it, but it yields no transport coefficient. Models carrying an anisotropic $\mathbf{K}$ do exist [2,4,5], yet none of them examines the values of $k_{xx}$ and $k_{yy}$ themselves; one handles a 90° change of pattern orientation by interchanging the two components [5], an operation that presumes the tensor transformation law rather than testing it. What is absent, therefore, is not the practice of checking an averaged model against a resolved solution, nor the recognition that the averaged model fails at these gaps, but a separately quantified error for each of the two principal coefficients on a sharp-edged geometry at finite gap, and how that error propagates into the squeeze-film pressure and the drainage it drives. An error in the anisotropy ratio alone does not answer that question, because the two components enter the lubrication flux with separate weights along and across the pattern.

It should be emphasized that this is not a criticism of the modeling strategy: replacing several thousand sub-resolution features by an effective tensor is the only tractable route, and the strategy has been productive. The contribution sought here is therefore not the comparison methodology, but the error law for this particular geometry, at the gaps actually traversed during filling, and its correction.

### ¶4　为什么解析路线补不上这一格

One might expect the gap to be filled analytically instead. For smoothly undulating walls such analyses exist and are accurate: spectral and domain-perturbation treatments yield closed-form permeability tensors for grooves of arbitrary depth [8,9], and they recover the classical asymptotic results in the thin- and thick-channel limits. These methods, however, rest on a Fourier representation of the wall shape, and the rectangular profile used in imprint templates is not represented by such a series in a usable way. Its Fourier coefficients decay only as $1/n$, so every spectral sum in which the correction is weighted by a single power of $n$ fails to converge — including $S_1=\sum_n n\coth(nH)\,|g_n|^2$, on which the leading correction depends [8] ($H$ the channel half-gap, $g_n$ the Fourier coefficients of the wall). Dewangan and Datta accordingly state that their approach "does not specialize meaningfully to the rectangular topography, because of its jump discontinuity" [8]. The underlying difficulty is general. In a second-order domain-perturbation analysis of periodic surfaces, an ideal square-groove profile produces Fourier coefficients decaying as $1/m$, whereupon two diagonal entries of the mobility tensor diverge and the predicted slip becomes unbounded; the authors of that analysis conclude that the mobility formula "should not be used for surfaces with corners or vertical slopes", and sharpen this to the requirement that the surface be twice continuously differentiable [10].

This is a statement about a class of asymptotic methods, not a claim that no analytical description of a rectangular groove is possible — particular limits (very shallow corrugations, or the thin-film limit in which the groove merely adds a slip length) remain accessible to analysis. What it does mean is that for the geometry of interest here — grooves of depth comparable to the groove width, under a residual gap of the same order — the cited smooth-profile approximations do not establish the accuracy of the present closure. Explicit-geometry numerical solutions provide one route to assessing it; other analytical or numerical formulations are not excluded. The same conclusion follows from the failure of the slender-gap premise: with $h/P\approx0.31$ at the representative fixed gap, and $d/w$ of order unity, neither the thin-gap nor the shallow-groove asymptote applies.

### ¶5　本文做什么、结论是什么

This paper evaluates the depth-integrated transport tensor for steady, fully filled flow in explicitly represented periodic rectangular grooves. The period is $P=240$ nm and the width is $w=120$ nm. Eighteen sampled geometries span $h=25$–$125$ nm and $d=25$–$120$ nm; they do not form a complete Cartesian grid over those ranges. The error map contains 36 principal-direction calculations. Four refinement runs, two viscosity checks and six oblique-drive runs bring the total to 48, not 48 independent geometries. The existing-output audit found no exceedance of the selected run diagnostics and numerical gates. The analytic parallel-plate benchmark is a separate check, not an exact solution against which every grooved case was validated.

Three conclusions follow within this scope.

(i) *The original closure overestimates both transport components at every sampled geometry.* Relative to the computed coefficients, its errors range from +10.30% to +204.85% along the grooves and from +8.11% to +54.19% across them. At $h=75$ nm and $d=100$ nm, it predicts an anisotropy ratio of 3.70, compared with 2.21 from the resolved calculation. These are observed sample discrepancies, not universal bounds over a continuous parameter domain; the numerical reference retains geometry-dependent discretization uncertainty.

(ii) *Unequal errors in the principal values also affect oblique flow direction.* With the driving angle $\theta$ and flux angle $\beta$ both measured from the groove axis, the linear tensor prediction is $\tan\beta=(K_\perp/K_\parallel)\tan\theta$. At $\theta=45^\circ$ for the reference geometry, the DNS principal values predict $\beta=24.3424^\circ$, whereas the original closure predicts $15.1412^\circ$, a difference of $-9.2012^\circ$. The six oblique-drive simulations test the tensor relation using DNS principal values. They do not validate the original closure values, rotated-wall discretizations, or a moving liquid front.

(iii) *The closure error admits a one-variable correction, but which variable is used decides how far it can be pushed.* A first correction was fitted on a fixed set of nine geometries, $d\in\{25,50,100\}$ nm crossed with $h\in\{50,75,125\}$ nm, taking the volume-equivalent height $H_{\rm ref}=h+d/2$ as the normalizing scale along the grooves and $d/w$ across them,
$$
F_\parallel^{\rm V1}=\frac{1}{1+1.7207\,(d/H_{\rm ref})^{1.8046}},
\qquad
F_\perp^{\rm V1}=\frac{1}{1+0.5276\,(d/w)^{0.8259}}.
\tag{2}
$$
On the withheld depth $d=75$ nm its absolute residual stays within 17% along the grooves and 4% across them. It does not extrapolate. Within each fixed-$d$ column the along-groove residual changes sign and reaches $+28.09\%$ at $h=125$, $d=100$ nm and $+38.58\%$ at $h=125$, $d=120$ nm, and its span across $h$ grows from 14 to 37 percentage points as $d$ increases. The sign is systematic rather than random: at fixed $d$ the correction is too strong at $h=50$ nm and too weak at $h=125$ nm. The cause is the strength with which the variable follows $h$, not its direction. The correction actually required weakens as the gap opens — the factor that removes the error rises by a factor of 1.07 to 1.23 between $h=50$ and $h=125$ nm, depending on $d$ — and $d/H_{\rm ref}$ does fall with $h$, so the two move the same way. They do not move at the same rate. Because the exponent is close to two, the fitted factor rises by 1.23 to 1.69 over the same span, roughly a third faster than required, so the correction is too strong at $h=50$ nm and too weak at $h=125$ nm, and the residual changes sign between them. The along-groove correction therefore depends on $h$ far more steeply than the physics asks it to.

Replacing the along-groove variable by the aspect ratio $d/w$ — already the variable used across the grooves — gives
$$
F_\parallel=\frac{1}{1+1.7685\,(d/w)^{1.6331}},
\qquad
F_\perp=\frac{1}{1+0.4900\,(d/w)^{0.6990}},
\tag{3}
$$
with both coefficient pairs obtained by minimizing the maximum absolute residual on the same nine geometries, since the accuracy quoted below is itself a bound on that quantity. A least-squares fit of the same form returns $a_\parallel=1.8515$, $b_\parallel=1.6260$, $a_\perp=0.5264$, $b_\perp=0.8119$ and widens the bound from 10.5% to 13.1% along and from 6.9% to 9.1% across, so the improvement follows from the change of variable and not from the choice of objective. Within $d/w\le1$ the corrected residual stays within 10.5% along the grooves for $h\ge25$ nm, and within 6.9% across them for $h\ge50$ nm; the across-groove factor is not quoted below $h=50$ nm because at $h=25$ nm its residual reaches $-18.7\%$, the thin film there being dominated by a resistance the aspect ratio does not describe. The withheld depth $d=75$ nm, which enters neither fit, returns $-8.45$ to $+9.33\%$ along and $-1.19$ to $+3.86\%$ across. Equation (3) is the relation used in the remainder of this paper; Eq. (2) is retained only to document how the variable was identified.

Two properties of Eq. (3) must travel with it. First, the change of variable was made after the extension batches had been computed: the coefficients are fitted on the original nine geometries and every other case is a hold-out, but the choice of variable is data-informed, so this is a reproducible model revision rather than a blind prediction, and the script that regenerates every coefficient accompanies the data. Second, the residual dependence on $h$ is reduced and not removed — at fixed $d$ it still spans 6 to 21 percentage points, with the sign reversed (positive at $h=50$, negative at $h=125$). The ranges quoted above are therefore bounds on the sampled geometries, not guarantees over a continuous domain, and extrapolation beyond $h=125$ nm is not supported.

Side-wall shear and flow redistribution near steps remain plausible explanations for directional differences. The coefficient fits and field images do not separate or quantify their contributions; no validated traction partition or energy-balance closure is claimed. Likewise, the two available spot refinements do not provide a full-map uncertainty bound.

### ¶6　范围声明（主动划界）

The results concern a continuous, incompressible, Newtonian liquid with no-slip walls in a fixed, fully filled, ideal periodic geometry. At the reference geometry, increasing viscosity from 1 to 15 mPa s changes the extracted coefficients by −0.000644% and −0.000283% in the parallel and perpendicular directions, respectively, while reducing flux by approximately fifteen-fold. This is a consistency check of the assumed linear transport model, not a validation for all real resists.

Fixed-gap coefficients may supply local inputs to a future slowly varying squeeze-flow model, provided its scale separation, conservation law and boundary conditions are independently justified. The present calculations do not validate dynamic filling, free surfaces, wetting, trapped gas, real-resist slip or rheology, pattern junctions, or other groove widths and duty cycles. The restriction to a single phase is not cosmetic. Once a gas phase occupies part of the void, saturation enters as an independent variable and the transport coefficient ceases to be a property of the geometry alone, becoming a relative permeability that must be calibrated against a saturation curve [11]; the same step introduces a viscosity ratio and a capillary number that the present comparison does not contain. No independent same-geometry solver or experimental comparison is claimed.

The remainder of the paper defines the model and extraction procedure, reports numerical verification with its unresolved provenance limits, presents the sampled closure discrepancies, and derives and bounds an empirical correction whose domain is stated explicitly. Mechanistic interpretation is discussed as a hypothesis rather than a completed dissipation decomposition.

---

## 参考文献（本节实际引用，按出现顺序）

| # | 文献 | DOI | 状态 |
|---|---|---|---|
| [1] | Sreenivasan S.V., *Nanoimprint lithography steppers for volume fabrication of leading-edge semiconductor integrated circuits*, Microsyst. Nanoeng. **3**, 17075 (2017) | 10.1038/micronano.2017.75 | ✅ 已核（Crossref 2026-10-17 复核；**题名曾误写为 "Nanoscale manufacturing enabled by imprint lithography"，已更正**） |
| [2] | Jain A., Spann A., Cochrane A., Schunk P.R., Bonnecaze R.T., *Fluid flow in UV nanoimprint lithography with patterned templates*, Microelectron. Eng. **173**, 62–70 (2017) | 10.1016/j.mee.2017.04.001 | ✅ 全文已核 |
| [3] | Tavakol B., et al., *Extended lubrication theory…*, Proc. R. Soc. A **473**, 20170234 (2017) | 10.1098/rspa.2017.0234 | ✅ 已核（式 8） |
| [4] | Ban Y.H., Bonnecaze R.T., *Optimal placement of droplets for UV nanoimprint lithography*, J. Vac. Sci. Technol. B **38**(2), 022601 (2020) | 10.1116/6.0000030 | ✅ 全文已核（2026-10-17） |
| [5] | Ban Y.H., Bonnecaze R.T., *Minimizing filling time for ultraviolet nanoimprint lithography with templates with multiple structures*, J. Vac. Sci. Technol. B **39**(1), 012601 (2021) | 10.1116/6.0000648 | ✅ 全文已核（2026-10-17） |
| [6] | Brenner G., Al-Zoubi A., Mukinovic M., Schwarze H., Swoboda S., *Numerical simulation of surface roughness effects in laminar lubrication using the lattice-Boltzmann method*, J. Tribol. **129**, 603–610 (2007) | 10.1115/1.2736452 | ⚠ 仅书目+摘要（未取全文） |
| [7] | Pusterhofer M., et al., *A novel approach for modeling surface effects in hydrodynamic lubrication*, Lubricants **6**, 27 (2018) | 10.3390/lubricants6010027 | ✅ 全文已核（式 9/11/12） |
| [8] | Dewangan M.K., Datta S., *Effective permeability tensor of confined flows with wall grooves of arbitrary shape*, J. Fluid Mech. **891**, A12 (2020) | 10.1017/jfm.2020.134 | ✅ 全文已核（2026-10-17） |
| [9] | Dewangan M.K., Datta S., *Flow through microchannels with topographically patterned wall: a spectral theory for arbitrary groove depths*, Eur. J. Mech. B/Fluids **70**, 73–84 (2018) | 10.1016/j.euromechflu.2018.02.004 | ⚠ 仅见摘要（闭源） |
| [10] | Kamrin K., Bazant M.Z., Stone H.A., *Effective slip boundary conditions for arbitrary periodic surfaces: the surface mobility tensor*, J. Fluid Mech. **658**, 409–437 (2010) | 10.1017/s0022112010001801 | ✅ 全文已核（arXiv:0911.1328v2，30 页；**方波反例在 §4.1，C² 判据在 §4.2**） |
| [11] | Cochrane A., Tjiptowidjojo K., Bonnecaze R.T., Schunk P.R., *Multiphase model for nanoimprint lithography*, Int. J. Multiphase Flow **104**, 9–19 (2018) | 10.1016/j.ijmultiphaseflow.2018.03.014 | ✅ 全文已核（2026-10-17） |
| [12] | Patir N., Cheng H.S., *An average flow model for determining effects of three-dimensional roughness on partial hydrodynamic lubrication*, J. Lubr. Technol. **100**(1), 12–17 (1978) | 10.1115/1.3453103 | ✅ **全文已核（2026-10-18，`raw/patir1978_JLubrTech_100_12-17.pdf`）**。第 15 页明写"flow factors, which are obtained by numerical flow simulation"；**式(23) 横向 φ_x=1/[h³E(1/h_T³)]（调和）、式(24) 纵向 φ_x=E(h_T³)/h³（算术）**，两式由"comparing the stochastic Reynolds equations [3,6,8] with the average Reynolds equation"**解析导出**，其数值模拟（在模型轴承上用有限差分求解式(18)的 Reynolds 方程，约 10 个统计等价粗糙面取平均）与之吻合；**故参考解为 Reynolds 方程自身，非 Stokes** |
| [13] | Rom M., König F., Müller S., Jacobs G., *Why homogenization should be the averaging method of choice in hydrodynamic lubrication*, Appl. Eng. Sci. **7**, 100055 (2021) | 10.1016/j.apples.2021.100055 | ✅ 全文已核（OA，21 页；**参考解为细网格 Reynolds，见其 §4.1**） |
| [14] | Lubrecht A.A., ten Napel W.E., Bosma R., *The influence of longitudinal and transverse roughness on the elastohydrodynamic lubrication of circular contacts*, J. Tribol. **110**(3), 421–426 (1988) | 10.1115/1.3261645 | ⚠ 仅见摘要（闭源）；摘要明写"与流量因子法的预测作比较" |
| [15] | Teyssèdre H., Gilormini P., Régnier G., *Limitations of simple flow models for the simulation of nanoimprint*, Int. Polym. Process. **28**(1), 72–78 (2013)；同作者博士论文 *Simulation du procédé de nanoimpression thermique sur silicium revêtu d'un film polymère ultramince*, Arts et Métiers ParisTech, 2013-11-12（该博士论文参考文献表第 [67] 条自记为 **2012**，与 Crossref 的 print 日期 2013-03 不符，在线版 2013-08-22；**以 Crossref 的 2013 为准**） | 10.3139/217.2673 | ✅ **全文已核（博士论文 178 页，`raw/teyssedre2013_PhD_ArtsetMetiers.pdf`，§3.1.4 即该文）**。**几何=矩形截面线栅半周期**（Fig. 3.4）；**参考解=Abaqus 平面应变 Stokes 有限元**；h₀/L=0.8/1.6/2.4，**F/F_L 在 2 至 80 倍之间，间隙越大偏差越大**（初始约 7 倍，接触模顶后由 3 倍跃至 12 倍，完全填充于 h/L≈0.3）；结论"不能对 h/L>0.1 使用简化流动模型"。**只给力，不给 K，无各向异性**；全文 0 次出现 permeability/anisotropy，0 次引用 Patir–Cheng；§4.4.4 另做**带自由表面与移动接触线的毛细填充**仿真 |
| [16] | Wang Q., Hiroshima H., *Anisotropic filling phenomenon of cavities in UV nanoimprint lithography*, J. Vac. Sci. Technol. B **29**(6), 06FC19 (2011) | 10.1116/1.3662889 | ⚠ 仅见摘要（闭源）；实验观测矩形腔沿长度方向收缩更快 |

---

## 写作说明（给老师/自己看的，不进正文）

### 一、六段各自的职能

| 段 | 干什么 | 关键取舍 |
|---|---|---|
| ¶1 | 立场景：填充是瓶颈，且发生在"纳米间隙 + 深槽"的二元尺度里 | 只引 [1] 的工艺数字，且写"在竞争性工艺条件下"，不写成通用规格 |
| ¶2 | 明确局部立方律及其省略的空间变化 | 省略项提示候选解释，不等于已量化机制 |
| ¶3 | 说清"被沿用但未被检验"，并**主动承认这不是批评** | 关键一段。先立"策略合理"，再收窄到"只是定量误差没人给" |
| ¶4 | 回答"为什么不能解析补上" | 这是本轮新增的核心，也是最能挡住"为什么没人做"的一问 |
| ¶5 | 三条结论 + 两个支撑验证 | 数字全部可追溯到 `error_table.csv` / 各 summary.csv |
| ¶6 | 主动划界 | 把"双相不适用"写成**物理理由**（k_r(S)），不是免责声明 |

### 二、措辞纪律自查（对照范围文档 §1）

| 禁止表述 | 草稿中的处理 | 位置 |
|---|---|---|
| ❌ "first" / "for the first time" / "no one has" | **全文零出现**（已逐字检索确认） | — |
| ❌ "沟槽有效渗透率从未被数值验证" | 改为"在该线工作中 K 被作为输入沿用"，并点名 [8] 做过数值评估 | ¶3 |
| ❌ "Jain 公式无人改进" | 明确写 [4][5] 改的是毛细压力、[11] 扩展的是两相 | ¶3、¶6 |
| ❌ "所有解析方法对矩形槽都不可用" | 加限定句："这是关于**一类**渐近方法的陈述，不是说不存在任何解析描述" | ¶4 第 2 句 |
| ❌ 把 Kamrin [10] 说成"压力驱动矩形槽无解" | 只引其"带尖角/垂直壁不适用"的判据，并区分为剪切驱动背景 | ¶4 |
| ✅ 可用窄主张 | ¶3 末句改为"contribution sought here is not the comparison methodology, but the error law…" | ¶3 末 |
| ❌ **"没人用数值校核过润滑理论"**（原计划想写） | **不成立**。[15] 已用 FEM 在 NIL 周期牛顿图案上校核润滑理论对**压印力**的预测 | ¶3 新增段 |
| ✅ 改为 | "校核本身不是空白；空白是**矩形直角槽 + 有限间隙下 K 两个主分量的误差**" | ¶3 末 |
| ❌ "这个闭合是纳米压印特有的" | **不成立**。它就是一维横向形貌下的 Patir–Cheng 压力流量因子 [12] | ¶3 新增段首句 |
| ❌ 把 [13] 当作"已量化闭合误差" | 必须补"其参考解为细网格 Reynolds，Reynolds 近似误差被固定" | ¶3 新增段 |

### 三、本轮核心修订与待核项

- 误差范围来自18几何、36方向工况；48是包含补充检查的运行数。
- 修正关系：**V2 已定稿替换 V1**（2026-10-18，作者批准）。两因子统一用 d/w，域 d/w≤1，域内最大残差 10.5%（沿槽 h≥25）/ 6.9%（跨槽 h≥50），留出 d=75 全部落入。可复现脚本 `analysis_fit_v2.py`。详见 ¶5(iii) 与 `V2_FIT_REPORT.md`。
- 机制归因、全域网格误差界和任意胶体/填充过程推广均未验证。
- 文献元数据的旧“已核”标记是项目历史记录，不代表本轮新的人工作者确认。查新覆盖与全文范围仍须逐项核对；不得将未找到先例写为不存在先例。
- 图1文件已存在，最终排版仍须检查；不再列为“尚未制作”。

### 三·补三　等价性的口径升级：从"谱系"到"恒等 + 四条条件"（2026-10-18 15:40）

**改了什么**：此前 ¶3 写"its two components are the two limiting orientations of the pressure flow factor"——
这是**只讲方向性、没给证明**的写法，正是用户指出的风险：凭方向性认定同一数学对象，审稿人可以一路追问。

**现在**：¶3 改为"under the four conditions listed in Sec. II **it is the same object, and for a square wave
the identity is exact rather than approximate**"；**四条件与代数推导移入第 2 章 §G**（那里本就讨论归一化与误差定义）。

**为什么能这样写**（依据见 `Jain_citation_audit_20261017/LITERATURE_COMPARISON_AND_CLAIM_BOUNDARY_20261018.md` §3）：

| 项 | 结论 |
|---|---|
| PC 的定义 | $\phi_x=\langle q_x\rangle/q_{\rm smooth}$，即同梯度下粗糙面与光滑面的平均流量之比 |
| 换成单位宽度渗透率 | $K^{\rm PC}_x=\phi_x h^3/12$ |
| 等占空比方波 | $K^{\rm PC}_\parallel=\frac{1}{12}\frac{h^3+(h+d)^3}{2}$、$K^{\rm PC}_\perp=\frac{1}{12}\frac{2}{h^{-3}+(h+d)^{-3}}$ |
| 与式(1) 比较 | **代数恒等**；12 档数值核，相对差 **0.00e+00**（双精度） |

**四条条件**（缺一不可，已写入 §G）：① 一维形貌；② Reynolds 在单元内局部成立；③ 单相牛顿、无滑移、无自由面；
④ 两侧同一 $h$ 定义与同一单位宽度归一化。**条件 ② 正是本文要检验的那一条。**

**关键区分（全文立论的基础，必须反复守住）**：
- $K^{\rm PC}$ = 式(1)：**同一泛函，Reynolds 算子**；
- $K^{\rm DNS}$（本文实测）：**同一泛函（平均通量/平均梯度），Stokes 算子**。
⇒ 两者**同定义、不同算子**。故 $E=(K^{\rm Eq.(1)}-K^{\rm DNS})/K^{\rm DNS}$ **精确地**是"Reynolds 导出的流量因子相对 Stokes 解的偏差"，
既不掺平均化误差（PC 已把平均化做完，一维下为恒等），也不掺口径差异（两边同定义）。
**所以本文不是"重新表达一个已知系数"，而是用更忠实的算子重算同一个系数、量出它自身的不确定度。**

**引用编号**：四条件与推导在 §G，¶3 只作前向引用（"Sec. II"），**不新增文献编号**。
$k_{xx},k_{yy}$ 与 [5] 的互换操作，属"应用未检验"，见对照表丁类。

---

### 三·补二　Patir–Cheng 谱系补段（2026-10-18 补，重要）

**为什么加这一段**：查新（TS3/TS4 重跑）发现我们这个闭合在摩擦学里叫 **Patir–Cheng 压力流量因子**，
1988 年就有人做过"纵向 vs 横向粗糙度 + 数值 vs 流量因子"的对比 [14]。
若不主动交代，摩擦学背景的审稿人第一反应就是"这不是新鲜事"，而被动应答会比主动承认吃亏。

**补段的核心结构（四层递进）**：
1. **溯源**：一维横向形貌下，本闭合 = Patir–Cheng 流量因子；沿流算术、横向调和是同一构造的两个极限取向 [12]。
2. **按参考解分类**（这是全段最有力的一句）：
   - 以 **Reynolds 自身**为真值 → 只测**平均化误差**，Reynolds 在直角处的失效被**固定住**（[12] 原始、[13] 同质化对比）；
   - 以 **Stokes/N–S** 为真值 → 两种误差一起测，但几何是 EHL 纹理 [14]、**单缺陷** [6]、**高斯随机粗糙面** [7]，
     **没有一个是周期矩形直角槽 + 有限间隙**。
3. **NIL 侧同理分叉**：[15] 用 FEM 校核润滑理论对**压印力**的预测（有力学结论，无 K）；
   [16] 实验观测到矩形腔各向异性填充（有现象，无系数）。
4. **收束**：缺的不是"校核"这件事，而是**K 两个主分量在填充间隙范围内的误差**。

**这一段顺手解决的两件事**：
- 消掉了原 ¶3 里那句"numerically checking … is itself an established practice [6,7]"——它与新段落重复。
- 给 [11] 找到了正文引用位置（¶6 的双相边界），否则 [11] 会成为悬空引用。

**✅ 已核（2026-10-18，用户提供全文）**：
- **[12] Patir & Cheng 1978 全文已核**（6 页 PDF）。三条关键：
  ① 第 15 页原文"flow factors, which are obtained by numerical **flow simulation**"——**此前引用的二手描述属实**；
  ② **式(23)/(24) 正是调和与算术两条极限**：横向 φ_x=1/[h³E(1/h_T³)]、纵向 φ_x=E(h_T³)/h³，
     且两式由"comparing the stochastic Reynolds equations [3,6,8] with the average Reynolds equation"**解析导出**，
     不是拟合出来的 ⇒ **在本课题的一维槽形下，"沿槽算术/跨槽调和"在 Reynolds 近似内是恒等式**，
     因此式(1) 与 DNS 的差值**全部来自 Reynolds 在直角处失效，与平均化本身无关**（已升级为正式陈述，见三·补三）；
  ③ 其数值模拟求解的是式(18)的 **Reynolds 方程**（有限差分，模型轴承，约 10 个统计等价面取平均），
     **参考解是 Reynolds 自身，不是 Stokes** ⇒ 归入"甲类"，与 [13] 同。
- **[15] Teyssèdre 2013 全文已核**（博士论文 178 页，§3.1.4 即 IPP 那篇）。**这一条改变了我们的定位**：
  几何就是**矩形截面线栅半周期**（Fig. 3.4），参考解是 **Abaqus 平面应变 Stokes 有限元**，
  **h₀/L 覆盖 0.8–2.4，正落在本课题 h/L≈0.2–1.0 的区间内**；
  结论是 **F/F_L 在 2 至 80 倍之间**，并明说"不能对 h/L>0.1 使用简化流动模型"。
  ⇒ **原稿"尚未有人在矩形直角槽 + 有限间隙下做 Stokes 校核"的说法不成立，已删除并改写**（见下）。

**⚠ 仍需补的核**：
- [14] Lubrecht 1988、[16] Wang & Hiroshima 2011 **仍仅见摘要**。
- **[15] 需在正文中注意的边界**：该文给的是**力**，不是输运张量；**二维平面应变**（无法区分沿槽/跨槽）；
  全文 **0 次**出现 permeability / anisotropy，**0 次**引用 Patir–Cheng。
  故它证明"平均化在直角槽有限间隙下失效"这一**物理事实**，但不提供 **K 的两个主分量**。

**因 [15] 全文而做的一处实质改写（2026-10-18）**：
¶3 原句"…but not, in the sources examined here, for periodic rectangular grooves at a finite gap"
**与紧随其后的 [15] 引用自相矛盾**（[15] 做的正是这件事），已删。
改为先承认"[15] 已在本几何上以 Stokes 为参考做了校核"，再收窄到
**"缺的是 K 的两个主分量及其各向异性，而这恰是二维/三维填充计算真正要用的量"**。

**篇幅影响**：引言由 2,090 词增至 **2,419 词**（+329）。若期刊要求压缩，本段可压到约 150 词，
删去第 2 层的三个例子（[14]/[6]/[7]）只保留"[12][13] 以 Reynolds 为真值、[15][16] 在 NIL 侧"两句；
但**第 1 层的溯源与第 4 层的收束必须保留**。

### 三·补　关于 [10] 的引用定位（2026-10-17 补，重要）

**两处原文已逐字核到（arXiv:0911.1328v2 第 8–9 页）**：

- **§4.1** 方波反例原文："Consider a surface of shallow, **square grooves** … |ĥ(m,n)| decays like **|1/m|** … consequently **M̃₁₁ and M̃₂₂ are both infinite**. This prediction for the mobility is clearly erroneous …"
- **§4.2** 判据原文："The approximation M(ǫh) ≈ −ǫ²M̃(h) **should not be used for surfaces with corners or vertical slopes**. … The mobility matrix formula can only be reliably applied to **C² functions** h(x,y)."

**⇒ 最精确的一句是"C² 判据"**：矩形直角槽（分段光滑、含跳变）连 C¹ 都不是，直接落在失效判据内。这比只说"带尖角面"更硬。引言已按此改写。

**⚠ 页码纪律**：arXiv v2 共 30 页，JFM 出版版 409–437（29 页），两版页码不同。**正文引用一律用章节号（§4.1 / §4.2），不写页码**，以免对不上。若期刊要求页码，需在校园网取 JFM 正式 PDF 核对（Cambridge 与 MIT DSpace 的直链本次均未取到 PDF）。

### 四、还差什么才能定稿

- **任务 C（WoS/Scopus 查 Jain 2017 被引列表）** —— 完成后才能决定是否允许任何强化的新颖性表述。当前草稿在无 C 的情况下**已经可以安全使用**。
- **[9] Dewangan 2018 全文** —— 目前只引其"存在任意深度谱理论"这一事实，摘要足够；若正文要具体比较其精度，需全文。
- **FIG. 1（装置示意）** —— 文件已存在，最终稿需核对图注、单位与引用位置。

### 五、篇幅（实测）

正文已按2026-10-18证据审查修订；以下篇幅压缩建议是旧稿记录，旧词数不再代表当前稿。

- **Physics of Fluids**：其引言常见 800–1,500 词，本篇偏长。可接受但建议压到 1,500 以内，删减方案见下。
- **Microelectronic Engineering**：更短，建议压到 1,000–1,200 词。

**若要压到 ~1,400 词，按此顺序删（不影响论证完整性）**：

1. ¶1 第 2 句（"Because the process reproduces features by mechanical molding…"）——工艺常识，可删，−30 词。
2. ¶2 第 1 句后半（"and it is not necessary: the lateral scale is five orders of magnitude larger…"后半）——可并进前句，−20 词。
3. ¶3 第 2 句（"It should be emphasized that this is not a criticism…"整句）——**建议保留**（这句是防守，删了容易被读成攻击前人），若必须删则移到 Discussion。
4. ¶4 第 2 段第 2 句（"particular limits (very shallow corrugations…)"括号举例）——可压成 "particular limits remain accessible to analysis"，−35 词。
5. ¶5 的 (i) 第 2 句（"Across the computed domain…"）——数字可移入 Results，引言只留量级，−25 词。
6. ¶6 第 3 句（"This boundary is not incidental…"）——可压成一句，−40 词。
7. 末段"论文组织"整段——**多数期刊允许删**，−60 词。

合计约 −210 词；若需更多，再删 ¶1 关于缺陷的那句。
