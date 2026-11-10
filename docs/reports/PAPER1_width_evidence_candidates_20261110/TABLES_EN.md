# Paired-width evidence tables (unmerged candidates)

W1–W4 are working labels, not formal manuscript numbers. h=75 nm, d=120 nm, with equal groove and ridge widths; w=60/240 nm corresponds to periods P=120/480 nm. Direction P is parallel to the grooves and T is transverse. The grids are numerical resolutions of the same known development geometries, not independent replicates.

## Table W1. Conductance factors and anisotropy

| w (nm) | Δx (nm) | F_P | F_T | A_Δ | B=A_LC/A_Δ |
| --- | --- | --- | --- | --- | --- |
| 60 | 5 | 0.19284 | 0.59930 | 1.57930 | 3.10784 |
| 60 | 2.5 | 0.19101 | 0.58994 | 1.58922 | 3.08845 |
| 240 | 5 | 0.58047 | 0.78205 | 3.64311 | 1.34726 |
| 240 | 2.5 | 0.57915 | 0.77365 | 3.67428 | 1.33583 |

F_i=K_i^Δ/K_i^LC, A_Δ=K_P^Δ/K_T^Δ, and A_LC=4.90822394. F is calculated from existing conductances; it is not a newly calibrated V2 factor.

## Table W2. Auxiliary diagnostic for a common multiplier

| w (nm) | Δx (nm) | 100(B−1) (%) | c_* | 100E_* (%) |
| --- | --- | --- | --- | --- |
| 60 | 5 | 210.78 | 0.29178 | 51.31 |
| 60 | 2.5 | 208.85 | 0.28859 | 51.08 |
| 240 | 5 | 34.73 | 0.66635 | 14.79 |
| 240 | 2.5 | 33.58 | 0.66242 | 14.38 |

Each geometry is allowed its own optimal common multiplier: c_*=2/(a_P+a_T), E_*=|a_P−a_T|/(a_P+a_T), a_i=1/F_i. E_* is the smallest attainable maximum absolute relative discrepancy across the two discrete principal conductances. It is neither a physical conductance bound nor a continuous-solution error bound, and does not constrain models with separate directional factors.

## Table W3. Absolute normalized gradient-excess contributions (2.5 nm, primary stencil)

| w (nm) | Direction | Profile departure | Cross-groove gradient | Streamwise gradient | Vertical-velocity gradients | S_i | r_i | b_i=r_i−S_i |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 60 | P | 2.45739 | 1.77488 | — | — | 4.23227 | 4.23524 | +0.00296 |
| 60 | T | 0.62678 | — | 0.01903 | 0.04932 | 0.69514 | 0.69510 | -0.00004 |
| 240 | P | 0.19485 | 0.53205 | — | — | 0.72689 | 0.72666 | -0.00023 |
| 240 | T | 0.18837 | — | 0.03202 | 0.07374 | 0.29414 | 0.29257 | -0.00156 |

Each contribution is divided by its own directional R_i^LC and is dimensionless; it is not divided by the positive-term sum. The parallel profile term also includes changes in flux allocation. Groupings differ between directions. A dash denotes an inapplicable group, not a measured zero. Here r_i=K_i^LC/K_i^Δ−1, S_i is the sum of nonnegative terms, and b_i retains its sign. S_i has not been rescaled to r_i.

## Table W4. Signed residuals for both grids and derivative stencils

| w (nm) | Δx (nm) | Stencil | Direction | S_i | r_i | b_i=r_i−S_i | 100b_i/r_i (%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 60 | 5 | wall_quadratic | P | 4.16922565 | 4.18575927 | +0.01653362 | +0.39500 |
| 60 | 5 | wall_quadratic | T | 0.66738069 | 0.66860374 | +0.00122305 | +0.18293 |
| 60 | 5 | odd_extension | P | 4.07591319 | 4.18575927 | +0.10984608 | +2.62428 |
| 60 | 5 | odd_extension | T | 0.65460867 | 0.66860374 | +0.01399507 | +2.09318 |
| 60 | 2.5 | wall_quadratic | P | 4.23227131 | 4.23523582 | +0.00296451 | +0.07000 |
| 60 | 2.5 | wall_quadratic | T | 0.69513565 | 0.69510049 | -0.00003516 | -0.00506 |
| 60 | 2.5 | odd_extension | P | 4.20149630 | 4.23523582 | +0.03373952 | +0.79664 |
| 60 | 2.5 | odd_extension | T | 0.68905029 | 0.69510049 | +0.00605019 | +0.87041 |
| 240 | 5 | wall_quadratic | P | 0.72339357 | 0.72272847 | -0.00066510 | -0.09203 |
| 240 | 5 | wall_quadratic | T | 0.28302368 | 0.27868877 | -0.00433491 | -1.55547 |
| 240 | 5 | odd_extension | P | 0.71747023 | 0.72272847 | +0.00525825 | +0.72755 |
| 240 | 5 | odd_extension | T | 0.27687724 | 0.27868877 | +0.00181153 | +0.65002 |
| 240 | 2.5 | wall_quadratic | P | 0.72689436 | 0.72666273 | -0.00023163 | -0.03188 |
| 240 | 2.5 | wall_quadratic | T | 0.29413558 | 0.29257451 | -0.00156107 | -0.53356 |
| 240 | 2.5 | odd_extension | P | 0.72493137 | 0.72666273 | +0.00173136 | +0.23826 |
| 240 | 2.5 | odd_extension | T | 0.29110583 | 0.29257451 | +0.00146868 | +0.50198 |

wall_quadratic is the primary stencil and odd_extension is the half-grid odd-extension stencil. The residual here is r_i−S_i, the negative of the existing S14 convention for the positive sum minus drive excess. Their absolute values agree. It is a decomposition residual, not the total input-power balance or a continuous-accuracy measure. The historical narrow-groove grid target remains FAIL; the wide groove has only two grids. These results do not establish grid independence. Full-precision components and run IDs are in mechanism_link.csv; scalar values are in paired_evidence.csv.
