# English candidates for the paired-width evidence (unmerged)

2026-11-10. Working text for author review. Figure W1, Tables W1–W4 and Eqs. (CW1)–(CW3) are local working labels; no formal manuscript numbers have been assigned. Suggested locations are the end of Section 4.3, after the existing directional group descriptions in Section 5.1, and the end of Supplement S14. The original 36-result statistics, V2 relation, abstract, conclusions and Appendix E are retained. The reviewed positioning of references [7]–[9] is retained; no references are added.

## Addition to Section 4.3: anisotropy distortion at an unchanged aperture distribution

To distinguish an overall conductance discrepancy from a distortion of anisotropy, we examine the separately reported two-width development set introduced in Section 2.1. At $h=75$ nm and $d=120$ nm, with equal groove and ridge widths, $w=60$ and 240 nm correspond to periods $P=120$ and 480 nm. The local apertures and their area fractions are unchanged, so Eq. (3) gives the same two principal conductances and the same ratio, $A_{LC}=4.90822$, for both widths. The depth-integrated flux is normalized by projected area. The periodic length along the grooves changes with $P$; checks of the saved final states for invariance in that direction are reported in Supplement S14.

Let $F_i=K_i^\Delta/K_i^{LC}$ denote the conductance multiplier required relative to a specified discrete result. On the 2.5 nm grid, the parallel and transverse factors are 0.19101 and 0.58994 for the narrow groove, and 0.57915 and 0.77365 for the wide groove (Figure W1a). The corresponding discrete anisotropy ratios are 1.58922 and 3.67428; the local cubic law overestimates these ratios by 208.85% and 33.58%, respectively (Figure W1b and Table W1). The 5 nm results retain the same ordering between widths, with values listed in Table W1. This supplementary set is reported separately from the $h=75$ nm, $d=100$ nm baseline geometry in Table 7.

For a given geometry, multiplying both principal conductances by any common positive factor leaves their ratio unchanged. An overall amplitude calibration therefore cannot simultaneously remove both directional discrepancies in this set. This statement does not rule out V2, which uses separate directional factors. The comparison is retrospective and uses known development results against specified discrete references; it does not provide a continuous-solution error guarantee. The smallest residual discrepancy attainable with a common factor is given in the supplementary candidate and Table W2.

## Addition to Section 5.1: absolute normalized excess resistance and anisotropy

The anisotropy discrepancy can be related to the excess resistance of the same geometries. Define $r_i=K_i^{LC}/K_i^\Delta-1$. On the 2.5 nm grid, the parallel and transverse values are 4.23524 and 0.69510 for the narrow groove, and 0.72666 and 0.29257 for the wide groove. They satisfy $A_{LC}/A_\Delta=(1+r_\parallel)/(1+r_\perp)$. Conductance overestimation in both directions therefore does not by itself determine the anisotropy discrepancy; the excess resistance normalized by each direction's own local-plate resistance must also be compared.

Figures W1c and W1d divide the existing nonnegative gradient terms directly by the respective $R_i^{LC}$, without further division by their positive-term sum. For parallel flow, the profile/flux-allocation departure and cross-groove gradient contributions are 2.45739 and 1.77488 in the narrow groove, and 0.19485 and 0.53205 in the wide groove. For transverse flow, the profile departure, streamwise main-velocity gradient and vertical-velocity gradient groups are 0.62678, 0.01903 and 0.04932, and 0.18837, 0.03202 and 0.07374, respectively (Table W3). The directional groupings differ; components shown in the same color are not equivalent independent physical causes.

Writing the positive-term sum as $S_i$ and retaining the discrete residual $b_i=r_i-S_i$ gives $A_{LC}/A_\Delta=(1+S_\parallel+b_\parallel)/(1+S_\perp+b_\perp)$. Stacked heights in the figure represent $S_i$, and diamonds represent $r_i$; they have not been rescaled to coincide. All residuals and the alternative derivative stencil are reported in Table W4. This relation links anisotropy distortion to the gradient structure under the specified decomposition, without assigning independent causal roles to the groups. Varying $w$ at fixed $h,d$ changes both $h/w$ and $d/w$, so the two-width comparison does not identify a unique controlling scale. The historical failure of the narrow-groove grid target and the availability of only two grids for the wide groove remain applicable.

## Addition to Supplement S14: diagnostic relations for conductance factors and anisotropy

The paired analysis uses eight existing directional records: two widths, two principal directions and grid spacings of 5 and 2.5 nm, representing two physical geometries. These known development records are not included in the statistics for the original 18 geometries and 36 principal-direction conductances. Tables W1–W4 retain all selected grids and both derivative stencils. Grid resolutions are not treated as independent replicates, and no statistical confidence intervals are constructed.

Define

\[
F_i=\frac{K_i^\Delta}{K_i^{LC}},\qquad
a_i=F_i^{-1},\qquad r_i=a_i-1,\qquad
B=\frac{A_{LC}}{A_\Delta}=\frac{a_\parallel}{a_\perp}
=\frac{1+r_\parallel}{1+r_\perp}.\tag{CW1}
\]

If both directions share a positive multiplier $c$, their corrected relative discrepancies are $c a_i-1$. Allowing each geometry to use its own most favorable $c$, the smallest attainable maximum absolute relative discrepancy is

\[
c_* =\frac{2}{a_\parallel+a_\perp},\qquad
E_* = \min_{c>0}\max_{i\in\{\parallel,\perp\}}|c a_i-1|
=\frac{|a_\parallel-a_\perp|}{a_\parallel+a_\perp}
=\frac{|B-1|}{B+1}.\tag{CW2}
\]

At $c_*$, the directional residuals have equal magnitudes and opposite signs. This is an algebraic minimax relation for two positive values, not a new fit, a physical conductance bound or a continuous-solution error bound. It requires the known discrete conductances and is used only as a retrospective diagnostic. It does not constrain V2, which uses separate directional factors. On the 2.5 nm grid, $100E_*$ is 51.08% and 14.38% for the narrow and wide grooves, respectively; the corresponding 5 nm values are 51.31% and 14.79%.

To connect this diagnostic to the gradient decomposition, let $s_{ij}$ be positive term $j$ for direction $i$, divided by that direction's $R_i^{LC}$, and let $S_i=\sum_j s_{ij}$. Retain $b_i=r_i-S_i$. Here $b_i$ is a residual, distinct from the local-plate velocity baseline $b(x,z)$ in Eq. (S14.1). Then

\[
B=\frac{1+S_\parallel+b_\parallel}{1+S_\perp+b_\perp}.\tag{CW3}
\]

Table W4 uses $b_i=r_i-S_i$, the negative of the existing S14 convention for the positive-term sum minus drive excess; their absolute values agree. This residual is distinct from the total input-power balance. If $b_i$ is omitted and $B$ is reconstructed from positive-term sums alone, its relative differences from the scalar value are −0.24571%/−0.29939% for the narrow/wide grooves at 5 nm and −0.05870%/−0.10723% at 2.5 nm using the primary stencil. The alternative stencil gives −1.29032%/−0.16379% and −0.28858%/+0.01337%, respectively. These quantities come from the same known fields; their numerical agreement is not independent validation or a certification of continuous accuracy.

## Candidate caption for Figure W1

**Figure W1. Directional conductance factors, anisotropy and gradient excess for an unchanged local aperture distribution.** The geometries have $h=75$ nm, $d=120$ nm and equal groove and ridge widths; $w=60/240$ nm corresponds to $P=120/480$ nm. (a) Conductance factors $F_i$ relative to the local cubic law. Circles denote parallel flow and squares transverse flow; open markers denote 5 nm and filled markers 2.5 nm. The dashed line marks $F_i=1$. (b) Anisotropy ratios from the same principal values and the common $A_{LC}$; grid symbols follow (a). Small horizontal offsets within a width category separate symbols and do not represent additional widths. (c,d) Nonnegative gradient-excess contributions for parallel and transverse flow using the primary stencil at 2.5 nm, divided by each direction's own $R_i^{LC}$. Both panels use the same vertical limits. These are dimensionless absolute contributions, not fractions of the positive-term sum; directional groupings differ. Stacked heights show $S_i$, and black diamonds show $r_i=K_i^{LC}/K_i^\Delta-1$, retaining their residual. No interpolation or statistical error bars are shown. Tables W1–W4 provide all values, the alternative stencil and the 5 nm decomposition. The historical narrow-groove grid target remains failed; the wide groove has only two grids. Continuous accuracy and a unique mechanism are not established.

## Alternative text

Four panels compare groove widths of 60 and 240 nm. In (a), the required conductance factors differ between directions, with a particularly low parallel factor for the narrow groove; corresponding points from the two grids are close. In (b), the local cubic law gives an anisotropy ratio of 4.908 at both widths, compared with approximately 1.589 and 3.674 at 2.5 nm. Panels (c) and (d) use a common vertical scale for directional gradient-excess contributions relative to each direction's own local-plate resistance. Parallel excess in the narrow groove is largest. Stacked positive sums and drive-derived excesses are shown separately rather than forced to coincide. Tables W1–W4 provide the full values and limitations.
