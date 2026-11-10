# Candidate for discrepancy definitions and Table 2 in Section 2.3 (not merged)

Replace from “Retaining dimensionless notation” to immediately before Section 2.4. Retain the equation number and every existing displayed value. Rename only the corrected-discrepancy symbol r_i to r_i^{corr}, separating it from the excess-resistance r_i in Section 5.1. This is not the formal manuscript.

Retaining dimensionless notation, define the original-law discrepancy and signed corrected discrepancy by

$$
E_i=\frac{K_i^{\rm mod}}{K_i^{\rm ref}}-1,
\qquad
r_i^{\rm corr}=\frac{F_iK_i^{\rm mod}}{K_i^{\rm ref}}-1,
\tag{4}
$$

Here, $K_i^{\rm ref}$ is the OpenLB discrete numerical reference for the same geometry and direction on the specified grid. Comparisons of the original and corrected formulae use the same denominator. When evaluating fixed V2, $F_i$ uses the published coefficients without refitting when the reference grid changes. Positive values indicate overestimation and negative values underestimation. “Improvement” means a smaller absolute relative discrepancy against the same reference, rather than a decrease in the signed value. Reference-grid, stopping-rule and implementation limitations are examined separately in Section 3; Eq. (4) does not represent total error relative to physical reality.

Relative discrepancies are reported as percentages, with the reference grid explicit:

$$
\varepsilon_i(\Delta x)=\left(\frac{K_i^{\rm formula}}{K_{i,\Delta x}^{\rm OpenLB}}-1\right)\times100\%.
$$

Here, $K_i^{\rm formula}$ is the conductance from either the original law or fixed V2. The quantities $E_i$ and $r_i^{\rm corr}$ in Eq. (4) are dimensionless ratios; their percentage forms are $E_i\times100\%$ and $r_i^{\rm corr}\times100\%$. Pointwise improvement requires comparing $|\varepsilon_i^{\rm V2}|$ and $|\varepsilon_i^{\rm mod}|$ at the same $\Delta x$. Main comparisons use 5 nm references and refinements use 2.5 nm references, reported separately. Refinement or additional records do not change the statistical denominator of the original 36 main results.

**Original-law discrepancies depend on the reference grid.** At fixed geometry, the original-law value remains unchanged while the OpenLB denominator in Eq. (4) varies with the grid. Table 2 reports eight directional pairs at four geometries. It examines reference sensitivity of the original-law discrepancy, rather than V2 correction performance.

**Table 2. Reference-grid sensitivity of the original-law relative discrepancy.**

| Geometry $(h,d)$ (nm) | Direction | $\varepsilon_i^{\rm mod}(5\,\mathrm{nm})$ | $\varepsilon_i^{\rm mod}(2.5\,\mathrm{nm})$ | Change (2.5 nm minus 5 nm, percentage points) |
|---|---|---:|---:|---:|
| (25, 100) | Along | 139.14% | 140.07% | +0.93 |
| (25, 100) | Across | 16.36% | **21.76%** | **+5.39** |
| (50, 100) | Along | 154.24% | 155.57% | +1.33 |
| (50, 100) | Across | 37.14% | 40.10% | +2.96 |
| (125, 25) | Along | 10.30% | 10.67% | +0.37 |
| (125, 25) | Across | 11.68% | 12.48% | +0.80 |
| (125, 120) | Along | 147.77% | 148.78% | +1.01 |
| (125, 120) | Across | 54.19% | 55.46% | +1.27 |

> **Note:** the two discrepancy columns use the respective 5 nm and 2.5 nm OpenLB denominators for the same geometry and direction, with the original law unchanged. Changes are differences between percentage discrepancies, reported in percentage points and calculated from unrounded values before rounding; they may therefore differ from subtraction of the displayed entries. The archived three-grid reference geometry (75,100) is discussed in Section 3 and is not included here. Full-precision values and change definitions are in [S7 and Table S2](../SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md#table-s2).

The largest reference-induced change in Table 2 occurs across the grooves at $(h,d)=(25,100)$ nm: the original-law discrepancy increases from 16.36% to 21.76%, a change of 5.39 percentage points. Relative to the discrepancy against the 5 nm reference, this is an increase of approximately 33%; it describes a change in discrepancy, not the grid-induced change in the OpenLB conductance. This maximum occurs at the thinnest gap across the grooves. Among the four checked geometries, along-groove discrepancy changes do not exceed 1.33 percentage points; this observation is not extended to unrefined geometries.

The formula-discrepancy ranges for the 36 main principal-direction records at 18 geometries use the 5 nm production grid as the discrete reference. Refinement comparisons use the grid specified for each comparison; numerical flat-wall benchmarks instead use the analytical solution as reference. For the four two-grid geometries, changing the reference grid changes original-law discrepancies by 0.37–5.39 percentage points. This is reference sensitivity at the checked conditions, rather than a discretization-error bound or uncertainty estimate; it does not establish comparable sensitivity for the other 14 geometries. Local V2 improvement must likewise be assessed separately within each reference grid; the thin-gap example is reported in Section 4.4 and Supplementary Table S7.
