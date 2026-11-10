Retaining dimensionless notation, define the original-law discrepancy and the signed corrected discrepancy by

$$
E_i=\frac{K_i^{\rm mod}}{K_i^{\rm ref}}-1,
\qquad
r_i=\frac{F_iK_i^{\rm mod}}{K_i^{\rm ref}}-1,
\tag{4}
$$

Here, $K_i^{\rm ref}$ is the discrete **numerical reference** for the same geometry, direction and grid, and $F_i$ is a multiplicative correction. **Positive values indicate overestimation; negative values indicate underestimation.** Reference reliability, including grid, stopping rules and implementation, is examined separately in Section 3. Equation (4) gives discrepancies relative to that numerical reference, rather than total errors relative to physical reality.

Formula discrepancies are reported as percentages, with the reference grid explicit:

$$
\varepsilon_i(\Delta x)=\left(\frac{K_i^{\rm formula}}{K_{i,\Delta x}^{\rm OpenLB}}-1\right)\times100\%.
$$

Here, $K_i^{\rm formula}$ is the conductance from either the original law or fixed V2. The denominator is the OpenLB discrete value for the same geometry and direction at spacing $\Delta x$. The quantities $E_i$ and $r_i$ in Eq. (4) remain dimensionless ratios; table entries display the percentage discrepancies defined above. Main comparisons use 5 nm references, whereas refinement comparisons use 2.5 nm references and are reported separately.

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

The model-discrepancy ranges for the 36 main principal-direction records at 18 geometries use the 5 nm OpenLB results as discrete references. Refinement comparisons use the reference grid specified for each comparison; flat-wall benchmark errors use the analytical values as references. For the four two-grid geometries, reference-grid changes alter model discrepancies by 0.37–5.39 percentage points. This describes sensitivity at the checked conditions, rather than a discretization-error bound or uncertainty estimate. It does not establish comparable sensitivity for the other 14 geometries.

