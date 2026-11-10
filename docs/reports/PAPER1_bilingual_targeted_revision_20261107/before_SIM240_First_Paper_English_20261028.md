# Directional transport discrepancies of the local cubic law in confined rectangular grooves: comparison against 5 nm discrete numerical references

## Abstract

Reduced models of nanoimprint flow commonly use a local cubic law to estimate effective transport through the residual film and grooves. We assess this approximation with lattice Boltzmann calculations of steady, fully filled flow between a planar substrate and a periodically grooved wall.

The period and groove width are 240 and 120 nm. 18 geometries span gaps of 25–125 nm and groove depths of 25–120 nm. Along-groove ($y$) and across-groove ($x$) forcing is applied separately, giving 36 principal-direction samples.

Three results emerge.

**First, the 5 nm discrete results show different depth responses in the two directions.** At a gap of 50 nm, increasing depth from 25 to 120 nm multiplies the along-groove coefficient $K_{yy}$ by 3.55, but the across-groove coefficient $K_{xx}$ by only 1.034. Among the gaps of 50, 75 and 125 nm that cover this depth interval, the relative along-groove gain decreases with gap, but remains approximately 39.2% at 125 nm.

**Second, the local cubic law overestimates transport at all 36 principal-direction samples relative to the 5 nm discrete references.** The overestimates range from +10.30% to +204.85% along the grooves and from +8.11% to +54.19% across them. This is a systematic pattern within the sampled geometries and resolution, rather than a discrepancy confined to a few samples.

**Third, the reference geometry shows discrepancies in both anisotropy and reconstructed flow direction relative to the 5 nm principal values.** At $h=75$ nm and $d=100$ nm, the numerical anisotropy is 2.21, whereas the model gives 3.70, approximately 67% higher. Under the same linear tensor description, the flux directions reconstructed from the two sets of principal values differ by 9.20° for forcing at 45°.

Retrospective evaluation against the 5 nm references, using the published rounded coefficients, gives maximum absolute corrected residuals of 10.5% for the 18 along-groove samples and 18.7% for the 18 across-groove samples. The 15 across-groove samples with $h\ge50$ have a maximum of 6.9%. At the across-groove sample $(h,d)=(25,100)$ nm against the 5 nm reference, the signed discrepancy changes from +16.36% to −18.71%, increasing its absolute value. The correction depends only on $d/w$; the residuals still vary with gap, and their sources have not been separated.

These discrepancy magnitudes and correction residuals are specific to the sampled conditions and 5 nm references; they are neither continuous-solution error bounds nor prediction accuracies for new geometries. Separately, Appendix E uses an energy identity and sectional dissipation inequalities to show that the local cubic law bounds both principal conductances from above in the ideal Stokes model of fixed, fully filled, no-slip periodic straight grooves. This result determines neither the discrepancy magnitudes nor the sign of the anisotropy discrepancy. The quantitative contribution is the sampled directional comparison and the limits of retrospective correction. Model assessment must report $K_{xx}$, $K_{yy}$, their ratio and the scope of the numerical reference evidence together.

**Keywords:** nanoimprint lithography; rectangular grooves; anisotropic transport; lattice Boltzmann method; local cubic law; model discrepancy

---

## 1 Introduction

### 1.1 Motivation

During nanoimprinting, liquid redistributes between a substrate and a patterned mold. Resolving every groove over a large imprint field is impractical. Engineering models therefore use effective transport coefficients, replacing a patterned region with an equivalent uniform gap that carries the same flow under the same pressure difference.

For parallel grooves, a common construction is the local cubic law. Each local height is treated as an independent parallel-plate channel with conductance $h^3/12$; deep and shallow regions are combined by an arithmetic average along the grooves and a harmonic average across them. This construction requires only geometry and no fitted parameters.

The construction does not explicitly resolve transverse velocity coupling near sidewalls or flow through the connections between deep and shallow regions. Its overall transport accuracy requires direct assessment when groove depth is comparable to groove width and a connected liquid layer remains beneath the ribs.

### 1.2 Relation to previous work

Effective transport coefficients for unresolved patterns are established in imprint modeling. Jain et al. used anisotropic transport for flow beneath patterned templates, and subsequent models retained this treatment [1–3]. The average-flow model of Patir and Cheng provides a flow-factor framework whose stripe averages are among the relations examined here [4].

Effective transport tensors in confined grooves have also been studied analytically and numerically. Dewangan and Datta combined spectral analysis with domain perturbation to establish tensor relations and evaluate representative topographies [5]. The same authors studied along-groove flow between a sinusoidal wall and a planar wall. Their full spectral method does not assume small amplitude; separate asymptotic approximations have their own limiting conditions [6]. Groove-induced transport anisotropy is therefore not itself a new finding.

We compare the magnitudes and directional differences of local-cubic-law discrepancies against explicitly resolved numerical principal values, and examine the remaining residuals of an empirical correction. The ideal-Stokes upper bounds are established separately in Appendix E. Positive discrepancy alone is not treated as sufficient evidence of novelty. The comparison uses 5 nm discrete references and informs assessment of a reduced model; it does not establish process-prediction accuracy.

### 1.3 Scope of this study

For rectangular grooves of fixed period and width, we apply along-groove and across-groove forcing separately. The principal values obtained on a 5 nm grid serve as discrete references for the local cubic law under common geometry, flux definitions and fluid properties. We retrospectively evaluate the V2 correction. Refinements at four geometries characterize reference sensitivity, rather than certifying continuous-solution accuracy across the map.

The study concerns fixed gaps, fully filled Newtonian liquid and no-slip walls. **Free surfaces, wetting, trapped gas, real-resist rheology and moving molds are outside its scope.** These require separate models and evidence.

---

## 2 Configuration and comparison methods

### 2.1 Geometry and calculation conditions

The computational domain is one unit cell of periodic straight grooves. The pattern repeats in $x$, and the grooves extend along $y$. Along-groove transport is denoted by $\parallel$, corresponding to $K_{yy}$; across-groove transport is denoted by $\perp$, corresponding to $K_{xx}$.

The period is $P=240$ nm and groove width is $w=120$ nm, with equal groove and rib widths. The rib-to-substrate residual gap is $h$, and the groove roof is at height $h+d$, where $d$ is the groove depth. Liquid fills the entire available volume.

![Figure 1: process context and fully filled computational unit cell](../../figures/paper/Fig1_device_and_unitcell.png)

**Figure 1.** Imprint-process context and computational unit-cell geometry. (a) Process stages: drop dispensing, pressing and filling, then curing and demolding. (b) Unit-cell cross-section, with groove width $w$, depth $d$, gap $h$ and period $P$; the computational domain is fully filled and has no free surface. (c) Plan view and coordinates: grooves extend along $y$, so $K_{yy}$ is along-groove and $K_{xx}$ is across-groove conductance.

Table 1 lists the sampled matrix. **The parameter combinations do not form a complete matrix:** at $h=25$ nm, only $d=25$, $50$ and $100$ nm were computed; $d=75$ and $120$ nm were not.

> Here, coverage refers to sampling of parameter combinations, not the 5 nm computational grid.

**Table 1. Sampled geometries and principal-direction samples.**

| Gap $h$ (nm) | Computed depth $d$ (nm) | Geometries | Principal-direction samples |
|---|---|---:|---:|
| 25 | 25, 50, 100 | 3 | 6 |
| 50 | 25, 50, 75, 100, 120 | 5 | 10 |
| 75 | 25, 50, 75, 100, 120 | 5 | 10 |
| 125 | 25, 50, 75, 100, 120 | 5 | 10 |
| **Total** | — | **18** | **36** |

Calculations use the OpenLB [7] D3Q19 velocity set and a body-force-corrected single-relaxation-time BGK model with $\tau=1$. The force term uses the Guo scheme [9]. Solid walls use Bouzidi–Firdaouss–Lallemand interpolated bounce-back, with wall intersections obtained from the analytical geometry [7,8].

The in-plane dimensions are $L_x=L_y=240$ nm, exactly one pattern period. Boundaries are periodic in $x$ and $y$, with no slip at the substrate and mold. A uniform volume force is imposed with acceleration $a=1\times10^{5}$ m s⁻². The same amplitude is used throughout the main map; the reference-geometry check is described in §2.4. OpenLB `computeU` supplies the macroscopic velocity, including the half-time-step force correction consistent with the Guo scheme. The stopping rule uses a 1000-step flux window: main-flux relative standard deviation $\le10^{-6}$, relative range $\le5\times10^{-6}$, and, for principal-axis forcing, absolute cross-flux $\le10^{-12}$ m²/s. Its scope as a stopping rule, rather than an independent acceptance metric, is discussed in §3.1. Saved manifests contain binary hashes; parameters, results and logs are indexed in [Supplementary Table S1](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md#table-s1). Binding to historical application source, compiler configuration and OpenLB dependencies remains incomplete for some runs; this provenance limitation is retained in [S10](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md#sm-s10).

**The unit-cell reduction assumes an exactly repeating pattern.** One period represents the interior of the ideal periodic pattern and reduces the computational domain. This assumption does not cover mold edges, pattern junctions or actual supply conditions; those configurations have not been verified here.

**Physical viscosity is specified first; physical properties and discretization together determine the time step.** With $\tau=1$, the lattice kinematic viscosity is

$$
\nu^*=c_s^2\left(\tau-\tfrac12\right)=\frac{1}{3}\cdot\frac{1}{2}=\frac{1}{6}.
$$

For physical kinematic viscosity $\nu=1.0\times10^{-6}$ m²/s and spacing $\Delta x=5$ nm, the time step is uniquely determined by

$$
\Delta t=\frac{\left(\tau-\tfrac12\right)\Delta x^{2}}{3\nu}=4.1667\times10^{-12}\ \mathrm{s}
\tag{1}
$$

Taking $\rho=1000$ kg m⁻³ then gives dynamic viscosity $\mu=\rho\nu=1.0\times10^{-3}$ Pa·s.

Density and physical kinematic viscosity are specified first, giving dynamic viscosity through $\mu=\rho\nu$. At those properties, $\tau=1$ and $\Delta x=5$ nm are selected, and Eq. (1) determines the time step. On refinement, the time step follows Eq. (1) to preserve physical viscosity and relaxation parameter. No $\tau$ sensitivity sweep was performed, so relaxation-parameter independence is not claimed.

The main map uses $\Delta x=5$ nm. The smallest gap, $h=25$ nm, has $h/\Delta x=5$, requiring particular attention to resolution. Refining $(h,d)=(25,100)$ nm to 2.5 nm changes the along-groove and across-groove coefficients by approximately −0.386% and −4.431%, normalized by the 5 nm values. We therefore retain 5 nm results as references at a specified discrete resolution and report thin-gap refinement sensitivity separately. Two grids neither determine observed convergence order nor establish grid independence of the full map (§3.3).

Fractional wall distances are determined analytically and checked individually. All 46 analyzed cases (36 main-map, 8 refinement and 2 viscosity checks) satisfy $q_{\min}=q_{\max}=0.5$ within tolerance $10^{-10}$. Wall intersections therefore lie at the midpoints of neighboring-node links, so the Bouzidi rule reduces to its half-way case. This geometry-consistency check alone does not establish zero boundary error. The flat-wall convergence in Section 3 reflects the combined discretization and flux-extraction error; it does not separate those sources or establish accuracy at arbitrary fractional wall distances.

Maximum Mach numbers range from $5.7\times10^{-10}$ to $4.1\times10^{-7}$, about five orders of magnitude below the 0.05 compressibility criterion, placing the flow in an effectively incompressible regime.

Two additional viscosity checks use $\mu=15$ mPa·s and are recorded separately from the main-map properties. The D2/D3 inventory contains 52 runs: 36 principal-direction samples, 8 refinements, 2 viscosity checks and 6 oblique-forcing runs ([S1 and Table S1](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md#sm-s1)). **Run count is not geometry count.** Periodic-replication and multi-force checks are in [S8](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md#sm-s8); historical flat-wall and three-grid benchmarks are in [S9](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md#sm-s9). These are not part of the 52-run inventory. Historical-build provenance is discussed in [S10](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md#sm-s10).

Supporting methods are numbered S1–S11. The [supplementary index](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md#sm-index) and the source manuscript Appendix B map text locations to supporting tables.

### 2.2 Definition of the transport coefficients

Let $A_{\rm plan}$ be the unit-cell plan area and $\Omega$ the fluid region. The depth-integrated flux and coefficient in the forcing direction are

$$
J_i=\frac{1}{A_{\rm plan}}\int_\Omega u_i\,\mathrm dV,
\qquad
K_i=\frac{\mu J_i}{G_i},
\qquad G_i=\rho a_i
\tag{2}
$$

The three steps establish the units.

First, integrate the driven velocity component over the fluid region $\Omega$ to obtain $\int_\Omega u_i\,\mathrm dV$. Second, divide by plan area $A_{\rm plan}$, obtaining flux $J_i$ per unit plan area, in **m²/s**. Third, multiply by dynamic viscosity $\mu$ and divide by equivalent driving gradient $G_i=\rho a_i$, obtaining coefficient $K_i$ in **m³**.

Here, $K_i$ is a **depth-integrated conductance**, rather than permeability. Under linear transport at the same viscosity and forcing, larger $K_i$ means greater flow capacity.

Conversion between the two definitions requires consistent mean-velocity and reference-height conventions:

$$
J_i=H_{\rm ref}\langle u_i\rangle_\Omega,
\qquad
K_i=H_{\rm ref}\,\kappa_i,
\qquad
H_{\rm ref}=h+d/2,
$$

Here, $\langle u_i\rangle_\Omega$ is the fluid-volume-averaged velocity and $\kappa_i$ is conventional permeability in m². **All comparisons here use $K_i$** to avoid additional differences from reference sections. Literature comparisons or conversions to m² must check the other study’s height definition.

### 2.3 Local cubic law and discrepancy definitions

For equal-width stripes, the local cubic law gives

$$
K_{yy}^{\rm mod}=\frac{1}{24}\left[(h+d)^3+h^3\right],
\qquad
K_{xx}^{\rm mod}=\frac{1}{6}\,\frac{(h+d)^3\,h^3}{(h+d)^3+h^3}.
\tag{3}
$$

To construct it, define the shallow- and deep-region parallel-plate conductances as

$$
k_{\rm shallow}=\frac{h^{3}}{12},
\qquad
k_{\rm deep}=\frac{(h+d)^{3}}{12} .
$$

For equal widths, their arithmetic average along the grooves and harmonic average across them give Eq. (3). At $d=0$, both recover the parallel-plate value $h^{3}/12$. With common local heights, boundaries and averaging definitions, these are the one-dimensional Reynolds cell relations [4].

**The construction remains an approximation to be assessed because it treats deep and shallow regions as independent local parallel-plate channels before combining their conductances.** The actual geometry also includes sidewalls and connections between the regions. Transverse viscous interactions and flow redistribution near steps are not explicitly resolved by this combination. Their respective contributions to overall transport have not been separated.

Under the ideal-Stokes assumptions in Appendix E, Eq. (3) also bounds both principal conductances from above. This supplies neither discrepancy magnitudes nor the spatial-accuracy evidence needed for groove-flow references. We compare the local-plate construction against specified discrete references. Quantifying sidewall-shear and step-redistribution contributions requires local-field or dissipation decomposition, which has not been performed; no dominant mechanism is assigned here.

Define relative discrepancy and corrected residual by

$$
E_i=\frac{K_i^{\rm mod}}{K_i^{\rm ref}}-1,
\qquad
r_i=\frac{F_iK_i^{\rm mod}}{K_i^{\rm ref}}-1,
\tag{4}
$$

Here, $K_i^{\rm ref}$ is the discrete **numerical reference** for the same geometry, direction and grid, and $F_i$ is a multiplicative correction. **Positive values indicate overestimation; negative values indicate underestimation.** Reference reliability, including grid, stopping rules and implementation, is examined separately in Section 3. Equation (4) gives discrepancies relative to that numerical reference, rather than total errors relative to physical reality.

**Reference-grid dependence must be specified.** Equation (4) uses $E_i$ with denominator $K_i^{\rm ref}$, which contains discretization error. Changing the reference grid can therefore change the reported discrepancy at the same geometry. For four geometries with two grids, this effect is:

**Table 2. Sensitivity of model discrepancy to the reference grid.**

| Geometry $(h,d)$ (nm) | Direction | $E$ (5 nm reference) | $E$ (2.5 nm reference) | Change (percentage points) |
|---|---|---:|---:|---:|
| (25, 100) | Along | 139.14% | 140.07% | +0.93 |
| (25, 100) | Across | 16.36% | **21.76%** | **+5.39** |
| (50, 100) | Along | 154.24% | 155.57% | +1.33 |
| (50, 100) | Across | 37.14% | 40.10% | +2.96 |
| (125, 25) | Along | 10.30% | 10.67% | +0.37 |
| (125, 25) | Across | 11.68% | 12.48% | +0.80 |
| (125, 120) | Along | 147.77% | 148.78% | +1.01 |
| (125, 120) | Across | 54.19% | 55.46% | +1.27 |

> **Note:** the three-grid historical reference geometry (75,100) is discussed in Section 3 and is not included here.

Unrounded values and change definitions for Table 2 are in [S7 and Table S2](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md#table-s2).

The largest change is in the across-groove component at $(h,d)=(25,100)$: from 16.36% to 21.76%, a difference of 5.39 percentage points, or 33% relative change. It occurs at the thinnest gap. Among these four checked geometries, the along-groove discrepancy changes less with reference grid (≤1.33 percentage points). This observation is not extended to unrefined geometries.

The reported discrepancy intervals therefore use **the 5 nm production grid as reference**. For the four two-grid geometries, reference-grid changes alter model discrepancies by 0.37–5.39 percentage points. This describes sensitivity at the checked conditions, rather than a discretization-error bound or uncertainty estimate. It does not establish comparable sensitivity for the other 14 geometries.

### 2.4 Numerical implementation consistency

Unit-cell periodicity and linear response are prerequisites for the subsequent comparison. We check them separately from model discrepancy.

**Invariance under transverse periodic replication.** The reference geometry $(h,d)=(75,100)$ nm is replicated along $x$ to $N_x=2$, 4 and 8 periods ($N_y=1$). Hydraulic resistance $R$ is compared at common properties, grid and forcing. Both principal directions and all three forcing levels ($5\times10^4$, $1\times10^5$ and $2\times10^5$ m s⁻²) meet the preset gates. Relative resistance differences are **0, identical to recorded precision**, for both directions from $2\to4$ periods; from $4\to8$ periods, they are $8.7\times10^{-14}$ along and $3.8\times10^{-14}$ across the grooves.

**This check has a limited interpretation.** With periodic boundaries and a periodic volume force, a solution over $N_x$ identical periods is a replication of the single-period solution by construction; resistance is mathematically independent of $N_x$. The check therefore tests **periodic-seam implementation and mass auditing in the enlarged domain**. It is not evidence of physical representative-volume convergence. A sufficient numerical unit cell here does not establish that a 240 nm cell represents a real device.

**Linearity with forcing.** The same cases give common coefficients over three forcing levels spanning a factor of four, with maximum relative differences $3.7\times10^{-8}$ ($2.5\times10^{-8}$ along and $3.7\times10^{-8}$ across the grooves). This supports linear response for the reference geometry $(h,d)=(75,100)$ nm on the 2.5 nm grid over the checked force range. Multi-force tests were not performed at all 36 main-map samples on the 5 nm grid; force independence is not claimed to have been verified sample by sample. See [S8 and Table S3](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md#table-s3).

**Cross-check with the main-map reference.** At $N_x=2$, 2.5 nm spacing and $1\times10^5$ m s⁻², the result is $K_{yy}=9.7824236970\times10^{-23}$ m³, agreeing with the archived three-grid baseline at 2.5 nm to relative difference $6.9\times10^{-14}$. This supports agreement between batches at that point, rather than common provenance for every condition.

**Terminology.** We report **numerical verification** of consistency between the implementation, computed solutions and prescribed equations, including analytical benchmarks, grid sensitivity and periodic consistency. Each check has its own coverage and limits. An independent-solver comparison would be a numerical cross-check and would not alone establish physical validation; no such same-geometry comparison has been completed. **Physical validation is outside this study:** the model has not been compared with experimental measurements of the target system. Unless explicitly qualified as physical validation, verification here concerns numerical checks. Conclusions describe discrepancies within this numerical model, rather than its fidelity to real imprint processes.

---

## 3 Scope of confidence in the numerical references

Discrepancy assessment requires an assessment of the reference. This section reports completed checks and their boundaries; no single check is treated as a complete uncertainty budget.

### 3.1 Convergence and conservation criteria

Steady state is assessed over 1000 consecutive flux samples: main-flux relative standard deviation ≤$10^{-6}$ and relative range ≤$5\times10^{-6}$. Principal-axis forcing also requires absolute cross-flux ≤$10^{-12}$ m²/s. Oblique forcing generates a physical cross-flux, so a relative-standard-deviation criterion is used instead. Mass, density, Mach number and boundary-link diagnostics are recorded separately from flux convergence.

All 36 principal-direction samples meet those thresholds. **They are stopping criteria, rather than independent acceptance metrics.** The program exits at the first window satisfying them, so satisfaction at termination follows from the stopping construction.

Define relative margin $m=1-\mathrm{rel\_std}/10^{-6}$. Window relative standard deviations for the 36 samples range from $3.87\times10^{-7}$ to $1.000\times10^{-6}$. **27 samples are within 1% of the threshold**, and 9 within 0.1%, with minimum margin $2.1\times10^{-5}$. This is consistent with termination at the first qualifying window.

**Proximity of a stopping statistic to its threshold establishes neither unreliability nor small numerical error.** It shows termination according to the prescribed rule. Accuracy requires separate evidence from the analytical benchmark (§3.2), refinement (§3.3) and boundary-link audits.

### 3.2 Analytical flat-wall benchmark

For parallel plates separated by 75 nm, the coefficient should recover $K_0=h^3/12$. Table 3 reports three grids. Original results and the historical transverse-flow failure are indexed in [S9 and Table S4](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md#table-s4).

**Table 3. Flat-wall analytical benchmark ($h=75$ nm).**

| Grid $\Delta x$ (nm) | Numerical $K$ (m³) | Analytical $h^3/12$ (m³) | Relative error |
|---:|---:|---:|---:|
| 5 | $3.531250\times10^{-23}$ | $3.515625\times10^{-23}$ | 0.444% |
| 2.5 | $3.519529\times10^{-23}$ | $3.515625\times10^{-23}$ | 0.111% |
| 1.25 | $3.516580\times10^{-23}$ | $3.515625\times10^{-23}$ | 0.0272% |

Halving the spacing reduces the error by approximately a factor of four. This tests total integrated-transport error in the planar configuration, including velocity discretization and quadrature. **It cannot be attributed entirely to bulk or boundary treatment.** Nor does it establish second-order accuracy of interpolated bounce-back at arbitrary fractional wall distances: these calculations use only $q=1/2$.

### 3.3 Grid resolution in grooved geometries

The flat-wall benchmark cannot replace resolution checks for grooves. Four geometries were compared on 5 and 2.5 nm grids (Table 4).

**Table 4. Coefficient changes on halving the spacing, normalized by the 5 nm values.**

| Geometry $(h,d)$ (nm) | $K_{yy}$ change | $K_{xx}$ change |
|---|---:|---:|
| (50, 100) | −0.52% | −2.11% |
| (125, 25) | −0.33% | −0.71% |
| (25, 100) | −0.39% | **−4.43%** |
| (125, 120) | −0.41% | −0.82% |

For these four checked geometries, along-groove changes are all <0.6% in magnitude. Across-groove changes are larger, reaching −4.43% at the thinnest gap. These sensitivity records do not establish the same grid response across the full map.

At a gap of 125 nm, refinements exist at both depths 25 and 120 nm. The across-groove gain changes from 0.9405% with the 5 nm reference to 0.8335% with the 2.5 nm reference; the along-groove gains are 39.1978% and 39.0928%. This supports consistency of the paired trend at the checked resolutions, without providing a continuous-solution error bound.

Two-grid comparisons characterize resolution sensitivity only for the checked geometries. Historical data at h=75 nm and d=100 nm also use 5, 2.5 and 1.25 nm grids. Conditional Richardson extrapolation and GCI based on observed order, together with run limitations, are reported in [S9 and Table S5](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md#table-s5), following [10]. The 1.25 nm transverse record failed the frozen mass gate. We do not use the table to confirm an asymptotic range or extend its fine-grid estimates to every production sample.

### 3.4 Known limitations

Existing output audits checked saved flux, mass, density, convergence and boundary diagnostics. The original 48-run audit and 4 later refinements are recorded separately. The historical finest transverse mass FAIL is retained. Scheme C has saved passing outputs, but the cited independent-release-report path and historical-build binding remain incomplete. **No same-geometry independent-solver or experimental reference is available here.** The evidence supports comparison of saved discrete results, rather than spatial convergence at every sample.

---

## 4 Results

### 4.1 Groove depth affects the two principal directions differently

We first examine geometry responses in the resolved numerical references. At fixed gap, deepening the grooves produces different transport gains in the two directions. Table 5 compares coefficients at depths of 25 and 120 nm.

**Table 5. Coefficient ratios for depth increasing from 25 to 120 nm.**

| Gap $h$ (nm) | Along $K_{yy}$ | Across $K_{xx}$ |
|---:|---:|---:|
| 50 | 3.55 | 1.034 |
| 75 | 2.13 | 1.021 |
| 125 | 1.39 | 1.009 |

Among these three gaps, the relative along-groove gain decreases with gap but remains approximately 39.2% at $h=125$ nm. Across-groove gains are approximately 3.39%, 2.14% and 0.94%, much smaller than their along-groove counterparts. The thinnest, 25 nm gap was not computed at 120 nm depth. Over its sampled 25–100 nm depth range, the maximum-to-minimum across-groove coefficient ratio is 1.037. Additional groove volume therefore does not produce equal transport gains in the two directions.

Parallel and series constructions offer a qualitative picture: along-groove flow uses deep and shallow regions together, whereas across-groove flow passes through alternating regions. These pictures alone do not locate resistance in the resolved flow. Sidewall-shear and step-redistribution contributions have not been separated, so the weak transverse response is not attributed to a demonstrated single mechanism.

![Figure 2: principal conductances and anisotropy of the 5 nm discrete references](../../figures/paper/Fig4_K_and_anisotropy.png)

**Figure 2.** Transport coefficients and anisotropy of the rectangular groove array using 5 nm discrete references. (a) $K_{yy}$ (filled symbols) and $K_{xx}$ (open symbols) against depth, grouped by four gaps. Across the sampled depths at each gap, $K_{xx}$ varies by less than 4%; uncomputed geometries are excluded. At $h=25$ nm, only $d=25$, 50 and 100 nm were sampled. (b) Anisotropy $A=K_{yy}/K_{xx}$ on a logarithmic ordinate; the dotted line marks $A=1$.

### 4.2 The local cubic law overestimates all 36 samples

Pointwise comparison of Eq. (3) against the 5 nm production-grid references gives positive relative discrepancies in both directions at all 18 geometries (Table 6). This result is specific to the sampled conditions and reference resolution.

**Table 6. Ranges of local-cubic-law relative discrepancy.**

| Quantity | Along $K_{yy}$ | Across $K_{xx}$ |
|---|---:|---:|
| Discrepancy range | +10.30% to +204.85% | +8.11% to +54.19% |
| Maximum location | $h=50,d=120$ nm | $h=125,d=120$ nm |
| Minimum location | $h=125,d=25$ nm | $h=25,d=25$ nm |
| Overestimated samples | 18/18 | 18/18 |

The largest along-groove discrepancy occurs at $(h,d)=(50,120)$ nm: the model coefficient is approximately 3.05 times the reference, an overestimate of approximately 204.85%. The largest along-groove discrepancy is about 20 times its smallest, giving a wider range than across the grooves.

Within sampled depth sequences at fixed gap, the along-groove discrepancy increases with $d/w$. At gaps $h=50$, 75 and 125 nm, it decreases with gap at fixed depth. Including $h=25$ nm removes monotonicity at some depths. For example, at $d=100$ nm it rises from 139.14% at $h=25$ nm to 154.24% at $h=50$ nm, before falling to 144.95% and 108.38% at $h=75$ and 125 nm. These data support parameter dependence, but establish neither a unique mechanism nor the exclusion of discretization effects.

![Figure 3: local-cubic-law discrepancy against gap](../../figures/paper/Fig7_error_vs_gap.png)

**Figure 3.** Local-cubic-law discrepancy against gap, grouped by groove depth, relative to 5 nm discrete references. The model and discrepancy definitions are Eqs. (3) and (4). Both ordinates are logarithmic, with different ranges. The figure describes parameter dependence of the discrepancy.

![Figure 4: discrepancy map and explicit unsampled cells](../../figures/paper/Fig8_error_map.png)

**Figure 4.** Local-cubic-law discrepancy over the $d$–$h$ matrix, relative to 5 nm discrete references. Each panel uses its own color scale; color intensity cannot be compared directly between panels. Hatched cells were not computed and **must not be filled or interpolated**.

### 4.3 Unequal directional discrepancies alter anisotropy and reconstructed flow direction

Relative to the reference geometry’s 5 nm principal values, the local model gives different anisotropy and flux direction reconstructed under the same linear tensor relation. Table 7 presents that comparison, rather than experimentally measured flow-direction error.

**Table 7. Anisotropy and reconstructed flow direction at the reference geometry ($h=75$ nm, $d=100$ nm).**

| Quantity | From numerical principal values | From local-model principal values | Difference |
|---|---:|---:|---:|
| Anisotropy $A=K_{yy}/K_{xx}$ | 2.21 | 3.70 | Model overestimate ≈67% |
| Flux angle under 45° forcing $\beta$ | 24.34° | 15.14° | −9.20° |

When forcing angle $\theta$ and flux angle $\beta$ are both measured from the groove axis, the linear tensor description gives

$$
\tan\beta=\frac{K_{xx}}{K_{yy}}\tan\theta .
\tag{5}
$$

At $\theta=45^\circ$, the directions reconstructed from the two sets of principal values differ by −9.20°. Agreement in total flux at one forcing angle therefore does not guarantee directional accuracy; both principal values and their ratio must be checked.

Existing oblique-forcing results at 30°, 45° and 60° test internal consistency of tensor predictions using principal values from the same numerical model. They do not verify the accuracy of the local-cubic-law principal values.

### 4.4 Improvement and local deterioration under empirical correction

We apply multiplicative factors $F_i$ to Eq. (3). The published rounded form of V2 is

$$
F_{yy}^{\rm V2}=\frac{1}{1+1.7685(d/w)^{1.6331}},
\qquad
F_{xx}^{\rm V2}=\frac{1}{1+0.4900(d/w)^{0.6990}}.
\tag{6}
$$

Evaluation using the published coefficients gives a maximum absolute residual of 10.5% over all 18 along-groove samples and 18.7% over all 18 across-groove samples. The 15 across-groove samples with $h\ge50$ give 6.9%. Table 8 compares maxima over matched sample sets.

**Table 8. Discrepancies before and after correction, relative to the 5 nm references.**

| Direction and samples | Original maximum absolute discrepancy | V2 maximum absolute residual |
|---|---:|---:|
| Along, all 18 | 204.85% | 10.5% |
| Across, all 18 | 54.19% | 18.7% |
| Across, $h\ge50$ nm，15 samples | 54.19% | 6.9% |

A reduction in the overall maximum does not imply improvement at every sample. At the across-groove sample $(h,d)=(25,100)$ nm, the signed discrepancy changes from +16.36% to −18.71%, increasing its absolute value by approximately 2.34 percentage points. This is the only principal-direction sample in the 5 nm main map whose absolute discrepancy increases. With the 2.5 nm reference, the corresponding values are +21.76% and −14.94%. The assessment of local improvement therefore depends on the reference grid; correction accuracy and reference accuracy must be distinguished.

V2 depends only on $d/w$, whereas residuals still vary with gap. This variable choice does not capture the full sampled gap response. Contributions from model form, parameter estimation and discrete references have not been separated.

The 9 calibration geometries and 9 extension geometries correspond to two different binary-SHA groups: geometry grouping and program identity coincide completely. Among extension data, d=75 nm lies within the calibration depth range, whereas d=120 nm and h=25 nm extend beyond the calibration depth and gap ranges. Without same-condition comparisons across the two program identities, potential build effects cannot be separated from geometry, model and reference effects on residuals. Extension data were already visible during model-form selection. These residuals therefore remain retrospective descriptions, rather than independent prediction evidence. V1, group-specific residuals and fitting records are retained separately in supporting files and are not mixed with V2.

---

## 5 Discussion

### 5.1 Limits of local-plate averaging and candidate mechanisms

All sampled principal directions show positive discrepancy relative to the discrete references, with different magnitudes in the two directions. The local cubic law therefore overestimates flow capacity under the checked conditions. Global coefficients alone cannot identify which part of the flow dominates the discrepancy.

The along-groove construction averages deep- and shallow-region parallel-plate conductances arithmetically, without resolving transverse viscous coupling or sidewall velocity changes. Sidewall shear and momentum exchange between regions are candidates for further investigation. Their flux or dissipation contributions have not been quantified; the present data do not establish a single drag mechanism explaining the entire overestimate.

The across-groove construction combines local plate resistances in one-dimensional series, while the resolved flow also traverses step connections. Velocity redistribution and viscous dissipation there may affect total resistance. No independent local resistance fractions were measured, and dominance by the narrowest region has not been proved.

Parameter trends also require qualification. In sampled depth sequences at fixed gap, along-groove discrepancy increases with $d/w$. Including the 25 nm gap, however, removes a monotonically decreasing gap dependence at some depths. At $d=100$ nm, the discrepancy rises from 139.14% at $h=25$ nm to 154.24% at $h=50$ nm. A general rule that a particular mechanism strengthens as the gap narrows is therefore not established.

These mechanisms require an independent dissipation decomposition or reference solutions under matching applicability conditions. Related squeeze-flow work on rectangular line gratings reports limitations of simple lubrication models [11], but its loading, filling state and comparison baseline differ. Its force ratios cannot directly explain the present fixed-gap coefficient discrepancies.

### 5.2 Implications for reduced squeeze-flow models

Fixed-gap coefficients are candidate local inputs to a reduced squeeze-flow model. For a square field at one instant, assume spatially uniform principal coefficients, constant viscosity, prescribed closure speed $V=-\dot h>0$, principal-axis coordinates and specified edge pressure. Depth-integrated mass conservation gives

$$
K_{yy}\,p_{\xi\xi}+K_{xx}\,p_{\eta\eta}=-\mu V,
\tag{7}
$$

Coordinates $\xi$ and $\eta$ run along and across the grooves. At common geometry, closure speed and constant ambient edge pressure $p_b$, multiplying both coefficients by the same factor divides the overpressure $p-p_b$ and its area-integrated net load by that factor. Different directional factors generally also change the pressure distribution. Both principal-value and anisotropy discrepancies may therefore affect reduced predictions. This is a conditional model implication; dynamic squeeze flow has not been validated.

Prescribed speed and prescribed load give different outputs. At fixed speed, motion sets the stroke time and coefficient errors primarily affect pressure and load. At fixed load, closure rate depends on resistance and time must be integrated over the changing gap. **A discrepancy at one fixed gap cannot be treated directly as the time error for an entire stroke.**

### 5.3 Applicability and unverified conditions

Responses and discrepancy ranges come from 18 geometries and 36 principal-direction samples at period 240 nm, width 120 nm and equal groove/rib widths. They do not cover other area fractions, groove widths, pattern junctions or arbitrary continuous parameter combinations.

Reported ratios, trends and anisotropy derive from saved 5 nm discrete records. Along-groove and across-groove results at each geometry share a binary, but different geometries belong to two program-identity groups. Pairing within one program does not guarantee cancellation of directional errors, and cross-geometry trends have not excluded build effects.

Among the four refined geometries, the transverse component at the thinnest gap, $(h,d)=(25,100)$ nm, has the largest grid sensitivity (−4.43%, normalized by the 5 nm value). Geometry-specific refinements cannot yet establish a map-wide uncertainty bound.

Correction performance must specify sample set and reference grid. The maximum absolute transverse residual is 18.7% over all 18 samples; 6.9% applies only to the 15 with $h\ge50$. At the thinnest gap and $d=100$ nm, the absolute transverse discrepancy increases from 16.36% to 18.71% against the 5 nm reference, but decreases from 21.76% to 14.94% against the 2.5 nm reference. Overall maxima cannot replace pointwise assessment, and local improvement depends on reference resolution. V2 does not explicitly include gap, although residuals vary with gap. This limits its representation, but does not establish omission of gap as the sole residual source.

The empirical relation and numerical reference have separate limitations. The former requires conditions unused in model selection after the model and scope are frozen. The latter requires grid or independent-reference evidence commensurate with the claimed accuracy. **Neither has been completed over the entire parameter range.**

Free surfaces, wetting, trapped gas, real-resist rheology and moving molds have not been validated. Applying fixed-gap results to those problems requires separate models and evidence.

---

## 6 Conclusions

**1.** In the sampled 5 nm discrete results for fully filled rectangular grooves, deepening the grooves affects along-groove and across-groove transport differently. At a 50 nm gap, increasing depth from 25 to 120 nm multiplies $K_{yy}$ by 3.55 and $K_{xx}$ by only 1.034. Among gaps of 50, 75 and 125 nm covering that interval, the relative along-groove gain decreases with gap but remains approximately 39.2% at 125 nm.

**2.** Relative to the 5 nm discrete references, the local cubic law overestimates all 36 principal-direction samples: +10.30% to +204.85% for $K_{yy}$ and +8.11% to +54.19% for $K_{xx}$. Along-groove discrepancy increases with depth in sampled fixed-gap sequences, but does not decrease monotonically with gap at every depth. These magnitudes and trends are not continuous-domain accuracy guarantees and identify no single dominant mechanism. Appendix E separately proves ideal-Stokes principal-conductance upper bounds, which do not determine these percentages.

**3.** Relative to the reference geometry’s 5 nm principal values, the model overestimates anisotropy by approximately 67%. Under the same linear tensor description, flux directions reconstructed from the two sets of principal values differ by 9.20° for forcing at 45°. These are not experimentally validated or continuous-solution-certified flow-direction errors. Both principal values and their ratio require assessment.

**4.** Retrospective evaluation using published V2 coefficients against 5 nm references gives maximum absolute residuals of 10.5% for 18 along-groove samples and 18.7% for 18 across-groove samples; the 15 transverse samples with $h\ge50$ give 6.9%. At the transverse sample $(25,100)$ nm, the absolute discrepancy increases against the 5 nm reference, and local improvement depends on the reference grid. Residual gap dependence remains. Evaluation must report sample coverage, reference grid and data-use history; the relation cannot be extended as a prediction relation for arbitrary geometries or dynamic imprinting.

---

## Appendix E. Upper-bound property of the local cubic law in the ideal Stokes model

Let the cross-section over one period be $\Omega=\{(x,z):0<x<P,\,0<z<H(x)\}$, with $H(x)$ equal to $h$ in the shallow region and $h+d$ inside the groove, where $h>0$. The geometry is invariant along $y$. Assume fully filled, incompressible Newtonian liquid of constant viscosity, stationary no-slip solid walls and matched periodic faces. Apply a single uniform driving gradient $G\mathbf e_i$, with $G>0$, and impose the Stokes equations. Along-groove forcing, $i=y$, admits a unidirectional scalar field; across-groove forcing, $i=x$, requires a two-dimensional incompressible velocity field.

The cross-section is the open fluid domain bounded by horizontal walls and vertical step walls, with periodic faces identified in pairs. Values of $H$ at the finitely many jumps do not affect the integrals. Velocity is a periodic $H^1$ weak solution with zero solid-wall trace; the across-groove field is weakly incompressible and the pressure perturbation is periodic. Finite-energy solutions at step corners are allowed; classical second derivatives at the corners are not required.

Set $\mathbf U=\mu\mathbf u/G$ and $\Pi=p'/G$, where $p'$ is the periodic pressure perturbation. Here, $\mathbf U$ is a dimensional scaled velocity in m², distinct from closure speed $V$ in Eq. (7). Then

$$
-\Delta\mathbf U+\nabla\Pi=\mathbf e_i,
\qquad\nabla\cdot\mathbf U=0,
\qquad K_i=\frac1P\int_\Omega U_i\,\mathrm dA.
\tag{E1}
$$

Testing the weak formulation with velocity itself eliminates solid-wall boundary terms, cancels periodic terms and removes pressure work through incompressibility, giving

$$
\mathcal D:=\int_\Omega|\nabla\mathbf U|^2\,\mathrm dA
=\int_\Omega U_i\,\mathrm dA=P K_i.
\tag{E2}
$$

Under these boundary and incompressibility conditions, $\int_\Omega|\nabla\mathbf U|^2\,\mathrm dA=2\int_\Omega\mathbf D(\mathbf U):\mathbf D(\mathbf U)\,\mathrm dA$, where $\mathbf D(\mathbf U)=(\nabla\mathbf U+\nabla\mathbf U^T)/2$. This is an integral identity, rather than a pointwise dissipation decomposition.

For almost every $x$, define sectional integral $q_i(x)=\int_0^{H(x)}U_i\,\mathrm dz$. Zero traces at both ends and the auxiliary function $\psi=z[H(x)-z]/2$ give $q_i=\int_0^{H(x)}\psi'\partial_zU_i\,\mathrm dz$. The Cauchy–Schwarz inequality and $\int_0^{H(x)}(\psi')^2\,\mathrm dz=H(x)^3/12$ imply

$$
\int_0^{H(x)}|\partial_zU_i|^2\,\mathrm dz
\ge\frac{12q_i(x)^2}{H(x)^3}.
\tag{E3}
$$

Vertical step walls occupy finitely many $x$ locations and do not affect this almost-everywhere sectional inequality. The complete field still satisfies no slip on those walls.

The energy identity gives $K_i\ge0$. Since $h>0$ provides a fluid layer connected through the period, a nonzero divergence-free test field supported in $0<z<h$ rules out the zero solution, so $K_i>0$.

Along the grooves, $q_y$ may depend on $x$. Integrating Eq. (E3) and applying weighted Cauchy–Schwarz again gives

$$
P K_\parallel=\mathcal D
\ge\frac{12\left(\int_0^Pq_y\,\mathrm dx\right)^2}
{\int_0^PH^3\,\mathrm dx}
=\frac{12(PK_\parallel)^2}{\int_0^PH^3\,\mathrm dx},
\qquad
K_\parallel\le\frac{\langle H^3\rangle}{12}.
\tag{E4}
$$

Extend velocity by zero inside the solid to a periodic strip of fixed height. Zero wall trace and weak incompressibility give a distributionally divergence-free extension. The distributional derivative of sectional integral $q_x$ with respect to $x$ is therefore zero. Thus $q_x$ is constant across steps and the periodic seam, and Eq. (E1) gives $q_x=K_\perp$. Consequently,

$$
P K_\perp=\mathcal D\ge12K_\perp^2\int_0^PH^{-3}\,\mathrm dx,
\qquad
K_\perp\le\frac{1}{12\langle H^{-3}\rangle},
\tag{E5}
$$

Here, $\langle f\rangle=P^{-1}\int_0^P f(x)\,\mathrm dx$. For the equal-width grooves and ribs considered here, the right-hand sides of Eqs. (E4) and (E5) are exactly the two local-cubic-law conductances in Eq. (3), hence

$$
K_{yy}\le K_{yy}^{\rm mod},
\qquad K_{xx}\le K_{xx}^{\rm mod}.
\tag{E6}
$$

These are non-strict upper bounds: the ungrooved parallel-plate case $d=0$ attains equality. They establish the principal-value discrepancy direction within the stated ideal model, but provide neither discrepancy magnitudes nor the sign of the model discrepancy in $K_{yy}/K_{xx}$. Errors of the 5 nm values relative to the continuous solution still require independent numerical-reference evidence. The bounds do not certify local dissipation fractions, V2 prediction accuracy or real-imprint fidelity.

## References

[1] Jain A., Spann A., Cochrane A., Schunk P.R., Bonnecaze R.T. Fluid flow in UV nanoimprint lithography with patterned templates. *Microelectron. Eng.*, 2017, **173**: 62–70. DOI: 10.1016/j.mee.2017.04.001

[2] Ban Y.H., Bonnecaze R.T. Optimal placement of droplets for UV nanoimprint lithography. *J. Vac. Sci. Technol. B*, 2020, **38**(2): 022601. DOI: 10.1116/6.0000030

[3] Ban Y.H., Bonnecaze R.T. Minimizing filling time for ultraviolet nanoimprint lithography with templates with multiple structures. *J. Vac. Sci. Technol. B*, 2021, **39**(1): 012601. DOI: 10.1116/6.0000648

[4] Patir N., Cheng H.S. An average flow model for determining effects of three-dimensional roughness on partial hydrodynamic lubrication. *J. Lubr. Technol.*, 1978, **100**(1): 12–17. DOI: 10.1115/1.3453103

[5] Dewangan M.K., Datta S. Effective permeability tensor of confined flows with wall grooves of arbitrary shape. *J. Fluid Mech.*, 2020, **891**: A12. DOI: 10.1017/jfm.2020.134

[6] Dewangan M.K., Datta S. Flow through microchannels with topographically patterned wall: A spectral theory for arbitrary groove depths. *Eur. J. Mech. B/Fluids*, 2018, **70**: 73–84. DOI: 10.1016/j.euromechflu.2018.02.004

[7] Krause M.J., Kummerländer A., Avis S.J., et al. OpenLB — Open source lattice Boltzmann code. *Comput. Math. Appl.*, 2021, **81**: 258–288. DOI: 10.1016/j.camwa.2020.04.033

[8] Bouzidi M., Firdaouss M., Lallemand P. Momentum transfer of a Boltzmann-lattice fluid with boundaries. *Phys. Fluids*, 2001, **13**(11): 3452–3459. DOI: 10.1063/1.1399290

[9] Guo Z., Zheng C., Shi B. Discrete lattice effects on the forcing term in the lattice Boltzmann method. *Phys. Rev. E*, 2002, **65**(4): 046308. DOI: 10.1103/PhysRevE.65.046308

[10] Celik I.B., Ghia U., Roache P.J., et al. Procedure for estimation and reporting of uncertainty due to discretization in CFD applications. *J. Fluids Eng.*, 2008, **130**(7): 078001. DOI: 10.1115/1.2960953

[11] Teyssèdre H., Gilormini P., Régnier G. Limitations of simple flow models for the simulation of nanoimprint. *Int. Polym. Process.*, 2013, **28**(1): 72–78. DOI: 10.3139/217.2673

> **Reference-version note:** the title, authors, year, volume, pages and DOI of [6] have been checked. Its complete accepted manuscript was received on 2026-10-28 and checked for geometry, along-groove direction, no-slip conditions in the main problem, amplitude conditions and quantity definitions. The full spectral method must be distinguished from small-amplitude and other asymptotic approximations. This paper does not directly verify numerical accuracy for transverse flow in the present rectangular grooves. The received accepted manuscript has not been matched page by page to the journal version of record. Locators and remaining limits are in S11.

---
