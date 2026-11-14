# Supplementary materials: methods, numerical references and provenance

Companion Chinese manuscript: `SIM240_中文稿_导师审阅版_20261022.md`. The synchronized English manuscript is `SIM240_First_Paper_English_20261028.md`; the English supplement in this directory is `SUPPLEMENTARY_METHODS_EN_20261028.md`.

Numbering version: 2026-10-24; synchronized on 2026-11-13. R1 related work, citation identities and contribution limits are synchronized. WO-1–WO-3 residuals, calibration-set scope and evidence limits are synchronized. S1–S14 and Tables S1–S9 are retained; paired-width conductance-factor and anisotropy diagnostics, Figure S1 and Tables S10–S13 are appended to S14. Existing sources are D2/D3 records, historical benchmarks and completed later controls; S14 uses only known D4 development final states, excludes reserved prediction results and does not replace V2. The checked private code/small-data snapshot remains e05b3f21171ce52a66af41dfe172e79c0a099c20 under `07_第一篇代码数据更新_20261107/`; copies of this manuscript and supplement revision are delivered on the private author branch codex/author-progress-20261112, without public release or submission approval. Reviewer access and final venue formatting remain for the authors to determine.

Recorded PASS, independent exit code, geometry checks, grid evidence and build provenance are reported separately. Supplementary numbering changes neither numerical nor physical acceptance status.

<a id="sm-index"></a>

| Supplement | Content | Manuscript | Data table |
|---|---|---|---|
| S1 | Geometry, sampling and inventory | §2.1、Table 1 | Table S1 |
| S2 | Implementation and units | §2.1、Eq. 1 | — |
| S3 | Boundary links and low Mach | §2.1 | — |
| S4 | Stopping and statistics | §2.1、§3.1 | — |
| S5 | Flux, coefficients and height | §2.2、Eq. 2 | — |
| S6 | Local-law averages | §2.3、Eq. 3 | — |
| S7 | Two-grid sensitivity | §2.3Table 2、§3.3Table 4 | Table S2 |
| S8 | Replication and force checks | §2.4 | Table S3 |
| S9 | Flat-wall and three-grid records | §3.2—3.4 | Table S4、S5 |
| S10 | Build provenance and logs | §2.1、§3.4 | — |
| S11 | Method-citation scope | Method citations | — |
| S12 | Later controls and failure records | §3.3–3.4 | Table S8 |
| S13 | Static averaged-model interfacing | §5.3 | — |
| S14 | Gradient-structure diagnostic for the two-width set | §§2.1, 2.4, 4.3, 5.1, 5.4, 6 | Tables S9–S13; Figure S1 |

<a id="sm-s1"></a>

## S1 Geometry, sampling and run inventory

The regular-region period of 240 nm and stripe width of 120 nm agree with the existing [layout report](/home/dell/yuanyuanxu/SIM240/docs/ex240/ex240_layout_report.md). Design file `SIM-EC1XT240.OAS` has SHA256 `209fbd4b907dc591c8786035face94de7df05fd10debf7e73dfc51a186ac0bfc`. This is design provenance, rather than measurement of fabricated dimensions. Checks on 2026-10-22 to 23 matched file identity to the parsing record; OAS parsing was not rerun.

At h=50, 75 and 125 nm, the main map samples d=25, 50, 75, 100 and 120 nm; at h=25 nm, only d=25, 50 and 100 nm are sampled. Each of 18 geometries has P (along-groove, +y) and T (across-groove, +x) forcing, giving 36 principal-direction samples.

<a id="table-s1"></a>

**Table S1. Run inventory for the D2/D3 map and additional checks (52 runs).**

Complete table: [Table_S1_run_inventory.csv](Table_S1_run_inventory.csv). It contains 36 main-map runs, 8 refinements, 2 viscosity checks and 6 oblique cases. Each row gives geometry, direction, grid, K, original-result path, manifest, log, binary hash and independent exit code.

The 52 runs exclude the periodic-replication/multi-force checks in S8 and the historical flat-wall/three-grid benchmarks in S9. Different evidence inventories can reuse the same physical benchmark; file counts must not be summed as independent new runs.

**Added comparisons and data-use roles.** The main 36, refinement 8 and added-gap 2 records form a 46-record comparison set for 19 geometries. This differs from the 36+8+2 viscosity boundary-audit set in S3. The original 52-row Table S1 and its historical denominator are unchanged.

<a id="table-s6"></a>

**Table S6. Added-gap and single-geometry build comparisons (6 records).**

The [numerical table](Table_S6_added_gap_build_comparison.csv) is a byte-preserving copy of the audited comparison CSV. Four added records comprise two h100 directions and two h75 build-B directions; the other two are historical h75 controls. Only h100 adds a comparison geometry. Original directories and manifest labels are indexed in the [four-case audit](../PAPER1_new_four_cases_acceptance_20261107/REPORT.md); the original `A_blind` label is not blinding certification. Ratio discrepancy uses 100(A_model/A_LB−1)%, giving −6.15% for V2 at h100.

| Data group | Geometry and role | Data-use and identity limits |
|---|---|---|
| 9 coefficient-calibration geometries | h=50/75/125 nm × d=25/50/100 nm; w=120 nm | Used in the coefficient objective; main-map binary 285f67a0… |
| 9 extension geometries | Remaining main-map geometries | Visible during form selection, not independent prediction; main-map binary 57611b21… |
| Added h100 geometry | d=100 nm, two directions, 5 nm | Fixed coefficients without refitting; not certified strictly blinded |
| h75 build reproduction | d=100 nm, two directions, 5 nm | Matching K, stopping steps and stepwise main flux; not map-wide build equivalence |

Full binary hashes and fitting-role sources are in the [claim audit](../PAPER1_claim_final_review_20261105/REPORT.md) and S10. Abbreviations identify groups but do not replace manifests.

V2 was calibrated only on the discrete set $h\in\{50,75,125\}$ nm × $d\in\{25,50,100\}$ nm (nine geometries, $w=120$ nm, 5 nm grid, binary identity 285f67a0…), separately minimizing the maximum absolute relative residual in each direction. This set establishes neither a continuous accuracy domain nor quantitative extrapolation across $h$. The $h=100$, $d=100$ nm point is outside the nine-point set but lies between the 75 and 125 nm gap levels, at the already calibrated depth of 100 nm on the upper depth boundary of the calibration rectangle; this parameter-space interpolation does not guarantee accuracy.

In the sampled series at fixed $d=100$ nm and $w=120$ nm, the along-groove residual drifts systematically with $h$: +5.90% at 75 nm and −2.03% at 100 nm, changing sign between these points. The 7.93-percentage-point change exceeds the batch’s recorded five-percentage-point structural screen, whose FAIL is retained. The discrete points do not locate an exact zero crossing. The required factor $F_i^\Delta=K_i^\Delta/K_i^{LC}$ varies with gap, whereas the V2 multiplicative factor retains only $d/w$; at fixed area fraction, the omitted independent geometric variable in the Stokes scaling is $h/w$. This is a limitation of the single-variable factor’s expressive capacity and cannot be attributed solely to coefficient estimation; the complete $K_i^{V2}=F_i^{V2}K_i^{LC}$ still contains $h$. Both gap results can be taken from binary 57611b21…, excluding a binary switch as the source of this paired drift. However, no same-geometry refinement is available at h100, so a contribution from the discrete reference remains unresolved; variable omission is not established as the sole cause of the residual in the continuous problem.

<a id="sm-s2"></a>

## S2 Current implementation and physical-unit conversion

The [current D2 source](/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp) specifies D3Q19_FORCE, ForcedBGK, τ=1, Lx=Ly=240 nm and uniform acceleration a=10⁵ m/s². Density ρ=1000 kg/m³ and kinematic viscosity ν=10⁻⁶ m²/s give μ=ρν=1 mPa·s. With physical properties fixed, dt=(τ−1/2)dx²/(3ν). Thus dx=5/2.5 nm corresponds to dt≈4.1667e−12/1.0417e−12 s. Two μ=15 mPa·s cases are separate from the main map.

The current OpenLB [ForcedBGK definition](/home/dell/openlb/src/dynamics/dynamics.h:224) uses PlainGuo; [computeU](/home/dell/openlb/src/dynamics/momenta/elements.h:1601) adds FORCE/2. The current Makefile and source tree are implementation evidence, but do not automatically bind every historical binary. See S10.

<a id="sm-s3"></a>

## S3 Boundary links and low-Mach diagnostics

All 46 D2 records in the legacy main-map/refinement/viscosity boundary-audit set (excluding added h100 cases) record q_min=q_max=0.5. The 52 records including 6 oblique cases have the same value. Saved maximum Mach numbers range from 5.69301195e−10 to 4.06765288e−7.

Original boundary_audit and precheck outputs, together with diagnostics-existence records, are indexed in the [existing support audit](/home/dell/yuanyuanxu/SIM240/docs/reports/Methods_support_audit_20261022/support_audit.json). These checks concern saved audit outputs. Supplementary numbering did not reconstruct geometry or recompute local fields over the complete runs. q=0.5 denotes a half-link intersection, not zero boundary error.

<a id="sm-s4"></a>

## S4 Stopping criteria and statistics

D2 uses the final 1000 main-flux samples to calculate sample standard deviation divided by absolute mean, range divided by absolute mean, and the absolute peak cross-flux. Thresholds are 10⁻⁶, 5×10⁻⁶ and 10⁻¹² m²/s, respectively. D3 oblique flow has physical cross-flux and uses its own statistical criteria; the principal-axis absolute cross-flux rule is not transferred to it.

Independent final-window recomputation for 36 samples is in [Methods_followup_relstd_20261022.json](/home/dell/yuanyuanxu/SIM240/docs/reports/Methods_followup_relstd_20261022.json). With relative margin m=1−rel_std/10⁻⁶, 27 samples have margins below 1% and 9 below 0.1%. This is the specified statistical check already performed. Stopping criteria are not proof of spatial accuracy or complete physical acceptance.

<a id="sm-s5"></a>

## S5 Flux, transport coefficient and reference height

Summing physical velocity times dx³ over fluid core nodes and dividing by plan area A_plan gives J in m²/s. Then K=μJ/(ρa), in m³. For equal-width grooves and ribs, the equivalent-volume height is H_ref=h+d/2; hence J=H_ref〈u〉_Ω and conventional permeability κ=K/H_ref, in m².

Table S1 retains original K and result paths. If older results do not print all physical-property fields, recorded τ, dx and dt can check consistency of the ν conversion. Such reverse calculation does not establish missing historical source or build provenance.

<a id="sm-s6"></a>

## S6 One-dimensional averaging in the local cubic law

Reference [4], Patir–Cheng (1978), printed page 15, Eqs. (23) and (24), gives transverse harmonic and longitudinal arithmetic averages of flow factors. To distinguish its normalization height from the present residual gap, write h0 for the former and H for local total height. Multiplying back by h0³/12 gives K_parallel=〈H³〉/12 and K_perp=1/(12〈H⁻³〉). Taking H=h and h+d over equal widths yields manuscript Eq. (3); d=0 recovers h³/12 in both directions.

The specified original pages were rendered and visually checked during the 2026-10-22 to 23 audit; see the [source-check report](/home/dell/yuanyuanxu/SIM240/docs/reports/Methods_support_audit_20261022/REPORT.md). This relation holds within the local Reynolds model. It does not establish the exact resolved step flow or a unique dissipation mechanism. Third-party full texts were not copied into this supplementary directory.

<a id="sm-s7"></a>

## S7 Two-grid sensitivity

<a id="table-s2"></a>

**Table S2. Two-grid comparisons for four geometries and two directions (8 rows).**

Complete table: [Table_S2_refinement.csv](Table_S2_refinement.csv). Geometries are (25,100), (50,100), (125,25) and (125,120) nm. Each row gives K5, K2.5, coefficient change, model discrepancies on both reference grids and their percentage-point difference. Coefficient change is 100(K2.5/K5−1), normalized by the 5 nm value; discrepancy change is E2.5−E5.

The thinnest transverse case changes K by −4.43073188% and model discrepancy by +5.39475470 percentage points. Two grids characterize sensitivity only at checked conditions; they do not determine observed order, GCI or a continuous-domain error bound.

<a id="table-s7"></a>

**Table S7. Two-grid local-law/V2 comparison for transverse flow at h=25 nm, d=100 nm.**

The [complete table](Table_S7_thin_gap_correction.csv) uses the corresponding grid's K as denominator for both the local law and fixed V2.

| Reference grid | Local-law discrepancy | V2 residual | Change in absolute discrepancy |
|---|---:|---:|---|
| 5 nm | +16.36% | −18.71% | Increase |
| 2.5 nm | +21.76% | −14.94% | Decrease |

The local improvement assessment depends on reference resolution; deterioration against the 5 nm reference is not established for the continuous solution. Paired refinements at h125/d25 and d120 support the reported paired trend, so this thin-gap example does not invalidate all parameter trends. A matched refinement at h100 is unavailable; no calculation was added in this revision.

<a id="sm-s8"></a>

## S8 Periodic replication and three-force checks

<a id="table-s3"></a>

**Table S3. Original periodic-replication and multi-force records at the reference geometry (18 rows).**

Complete table: [Table_S3_periodic_checks.csv](Table_S3_periodic_checks.csv). Batches are `g4_period_nx2_fields_v1_20261012T001316+0800`, `g4_period_nx4_fields_v1_20261012T105719+0800` and `g4_period_nx8_fields_v1_20261012T163341+0800`. Each fixes Nx and includes P/T forcing at a=5×10⁴, 10⁵ and 2×10⁵ m/s².

Frozen conditions in the [periodic-domain protocol](/home/dell/yuanyuanxu/SIM240/CASE/03_grid_convergence/G4_EX240_period_convergence/PERIOD_CONVERGENCE_PROTOCOL.md) are h=75 nm, d=100 nm and dx=2.5 nm. At a=10⁵, the relative R differences from 2→4 periods are 0 in both directions; from 4→8 they are 8.71496562e−14 and 3.80797839e−14. The largest within-level K range divided by mean is 2.47850560e−8 along and 3.66006070e−8 across the grooves. The Nx2 along-groove K differs from the historical same-grid baseline by 6.89448e−14 relatively.

These results support linear response over the checked force range and numerical consistency of periodic replication at this reference geometry. They neither establish individual multi-force checks for all 36 main-map samples at 5 nm nor prove physical RVE convergence. Supplementary numbering did not repeat all original numerical gates or manual mass-trajectory acceptance.

<a id="sm-s9"></a>

## S9 Flat-wall benchmark and historical three-grid data

<a id="table-s4"></a>

**Table S4. Original three-grid benchmark values and recorded statuses (9 rows).**

Complete table: [Table_S4_grid_archive.csv](Table_S4_grid_archive.csv). Each grid, 5/2.5/1.25 nm, contains Smooth75, EX240_parallel and EX240_perpendicular; see the [historical archive](/home/dell/yuanyuanxu/SIM240/CASE/03_grid_convergence/G2_EX240_grid_convergence/archive/g2_grid_20260917T165045+0800).

Flat-wall integrated-K errors relative to h³/12 are 0.44444079%, 0.11103511% and 0.02715688%, respectively. The historical 1.25 nm transverse record has PASS=false and independent exit3. This failure is retained; a calculable GCI does not confer acceptance.

Later Scheme C has saved PASS=true and independent exit0, but its initial manifest has formal_reference_accepted=false. This material does not replace the unrecovered formal-release record. Applicability of historical benchmarks and source/build provenance are judged separately.

<a id="table-s5"></a>

**Table S5. Conditional Richardson/GCI estimates for the historical benchmark (6 quantities).**

Complete table: [Table_S5_conditional_gci.csv](Table_S5_conditional_gci.csv). Original three-grid values and statuses are in Table S4. Fine, medium and coarse spacings are 1.25, 2.5 and 5 nm, with $r_{21}=r_{32}=2$ and $F_s=1.25$. The flat-wall gap is 75 nm; the groove reference has $h=75$ nm, $d=100$ nm, period 240 nm and width 120 nm. The original properties are $\rho=1000$ kg/m³, $\mu=1$ mPa·s, $a=10^5$ m/s² and $\tau=1$. The [original protocol](/home/dell/yuanyuanxu/SIM240/CASE/03_grid_convergence/G2_EX240_grid_convergence/STEP3_PROTOCOL.md) contains the complete geometry and parameters. K is in m³. Each eta is directional K divided by same-grid flat-wall K; anisotropy is along-groove K divided by across-groove K. Both are dimensionless. The method follows manuscript reference [19]; original-version checks are bounded in S11.

| Quantity | p | Extrapolated | ea (%) | e_ext (%) | GCI_fine (%) | Depends on failed finest T |
|---|---:|---:|---:|---:|---:|---|
| K_smooth | 1.990910 | 3.515588485e-23 | 0.083855 | 0.028196 | 0.035235 | No |
| K_parallel | 1.512988 | 9.754563861e-23 | 0.185350 | 0.100073 | 0.124966 | No |
| K_perpendicular | 1.256172 | 4.339399834e-23 | 0.612125 | 0.442769 | 0.551022 | Yes, FAIL/exit3 |
| eta_parallel | 0.939763 | 2.773587499 | 0.101409 | 0.110564 | 0.138053 | No |
| eta_perpendicular | 1.088414 | 1.233638776 | 0.527826 | 0.470801 | 0.585744 | Yes, FAIL/exit3 |
| anisotropy | 1.098181 | 2.248566102 | 0.424178 | 0.370433 | 0.464763 | Yes, FAIL/exit3 |

Let $\phi_1$ and $\phi_2$ denote the fine and medium results. Using common notation, define extrapolation $\phi_{\mathrm{ext}}=\phi_1+(\phi_1-\phi_2)/(r^p-1)$, $e_a=|(\phi_1-\phi_2)/\phi_1|$, $e_{\mathrm{ext}}=|(\phi_{\mathrm{ext}}-\phi_1)/\phi_{\mathrm{ext}}|$ and $GCI_{\mathrm{fine}}=F_s e_a/(r^p-1)$. Error and GCI columns are percentages; the CSV retains original three-grid values and full precision.

**Failure disclosed with the estimates:** the historical 1.25 nm transverse relative mass metric is $1.1967043900362632\times10^{-10}$, above frozen threshold $10^{-10}$, with independent exit code 3. K_perpendicular, eta_perpendicular and anisotropy all depend on that failed record. Calculable GCI does not qualify it as an accepted reference or change the historical G2 Step 3 FAIL/INCONCLUSIVE. These estimates neither extend to other geometries nor establish strict full-domain error bounds.

Along-groove and across-groove observed orders are 1.513 and 1.256. An order below the formal order alone establishes neither failure nor an asymptotic range. Once p is fitted from the same three values, the archived adjacent-GCI ratio reduces to the fine/medium result ratio. The historical “asymptotic range confirmed” label is therefore not independent asymptotic-range evidence. Reported GCI values remain conditional estimates for this three-grid chain.

For the same flat-wall benchmark, fine-grid integrated K differs from the analytical value by 0.0271569%. Normalizing both the analytical discrepancy and GCI by the fine-grid value gives 0.0271495% and 0.0352348%, respectively, a ratio of approximately 1.298. This supports only that planar configuration and integrated quantity; it does not establish comparable coverage for grooves or other geometries.

<a id="sm-s10"></a>

## S10 Historical-build provenance and logs

All 52 specified D2/D3 manifests retain binary_sha256, in groups of 22, 22, 6 and 2. Individual checks on 2026-10-22 to 23 found no source_sha256, generated_source_sha256, openlb_commit, compiler or compile_flags fields. The current Makefile contains build settings but cannot alone bind them to every historical binary.

There are 48 individual run.log files. 4 refinements share a [batch log](/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/results/dx25_refine4_run_20261018.log) with per-case precheck and steady exit markers. Some result.case labels abbreviate dx2.5 as dx2. Numerical dx, manifest.case_id, directory and log must be used together; original labels must not be rewritten to manufacture consistency.

The log string 5953d8a-dirty is hard-coded in the current Makefile; the current source-tree CITATION.cff identifies 1.9.0. Neither alone establishes the actual OpenLB version used by each historical run. Traceable parameters, outputs, binary hashes and logs do not mean complete historical source and dependencies have been recovered.

Update on 2026-10-28: 52 records belong to four binary-SHA groups of 22, 22, 6 and 2. Retained D2 and D3 executables match 22 and 6 records, respectively. This establishes executable identity, but not complete association with historical application source, dependency contents and actual compiler/linker commands. Current dependency files, source modification times and OpenLB labels remain supporting clues and are not used to backfill historical fields. Complete build provenance remains open for all four groups. The earlier scope is recorded in the [provenance report](../Methods_sources_data_audit_20261027/REPORT.md) and `provenance.json`; grouping and inference limits are in the [historical-build adjudication](../Historical_build_adjudication_20261028/REPORT.md).

**Added scope on 2026-11-07.** The original 52-row inventory and four identity groups retain their historical scope. Manifests for the four added h100 and h75 build-B cases match the current 57611b21… executable. Both principal conductances, stopping steps and main-flux sequences reproduce the historical h75 records from binary 285f67a0…, but only 30 of 42 paired files are byte-identical; the maximum sectional-flow difference is 3.65927×10⁻³³ m³/s. This does not restore complete historical source, dependency and compiler-command binding. Case audits, file comparisons and manifests are indexed in the [four-case audit](../PAPER1_new_four_cases_acceptance_20261107/REPORT.md).

<a id="sm-s11"></a>

## S11 Scope of method-citation checks

The targeted checks of 2026-11-13 add scopes for [10]–[15]; original methods references [10]–[14] become [16]–[20] by identity. Related-work checks for [7]–[9] from 2026-11-10 are retained, with numbers aligned to the companion manuscript. The 2026-10-28 update of reference [6] and the individual check dates of other entries are retained. These are source-check scopes, rather than a blanket release of project accuracy:

- **[4] Patir–Cheng:** Eqs. (23) and (24) on printed page 15 of the available lawful local full text were visually rechecked. They support harmonic/arithmetic averages within the one-dimensional Reynolds model, not an exact resolved step-domain solution or a unique dissipation mechanism.
- **[5] Dewangan–Datta 2020:** targeted checks of the publisher full text on 2026-11-12 located the square-wave divergence of S1 and the restrictions on Eqs. (3.11), (3.21) and (3.25) at A12-16. Section 4.2, A12-21 explicitly reports inaccurate longitudinal arithmetic and transverse harmonic lubrication predictions, without displaying their curves or tables. A12-22 discusses sidewalls and local gradients. Neither the first directional comparison nor the first sidewall interpretation is claimed here, and the asymptotic expansion is not an error-free reference for the present rectangular steps. Source: https://doi.org/10.1017/jfm.2020.134 .

- **[6] Dewangan–Datta 2018:** the title is *Flow through microchannels with topographically patterned wall: A spectral theory for arbitrary groove depths*, European Journal of Mechanics–B/Fluids 70, 73–84, DOI 10.1016/j.euromechflu.2018.02.004. On 2026-10-28 the complete accepted manuscript was received, comprising 1 publisher cover page and manuscript pages 1–34, with identity matching Crossref. Manuscript pages 4–8, 11–13, 21–24 and 29 were read. The main problem is fully developed, steady, incompressible Newtonian along-groove flow between a sinusoidal wall and a flat wall. Eqs. (1) and (2) use viscous–pressure balance and no slip at both walls. The full spectral method does not require small amplitude; small-amplitude, thick/thin-channel and slip asymptotics have separate limiting assumptions. Its h is period-mean height and a is sinusoidal amplitude, not the present residual gap h and rectangular depth d. Q/Q0 is dimensionless flow relative to a planar channel of the same mean height, rather than K in m³. Page 22 discusses possible loss of exponential spectral convergence for nonsmooth rectangular grooves; page 24 lists transverse flow as future work. It does not certify present rectangular-groove P/T or map-wide accuracy. These specified applicability conditions were checked at accepted-manuscript level. The journal version has not been matched page by page; original examples were not reverified and strict error bounds were not certified. See the [receipt report](../Dewangan2018_received_20261028/REPORT.md).
- **[7] Ng 2017:** *Effective slip for Stokes flow between two grooved walls with an arbitrary phase shift*, Fluid Dynamics Research 49(2), 025516, DOI 10.1088/1873-7005/aa5b58. The [institutional accepted manuscript](../PAPER1_nearest_work_comparison_20261109/sources/round2/Ng2017_accepted.pdf) was read at Section 2, Eqs. (18)–(21) in Section 2.1, Eqs. (41)–(44) in Section 2.2 and related results. Both walls have rectangular grooves with no slip under pressure forcing. Its symmetric mid-plane is not the present no-slip plate, and longitudinal effective slip explicitly excludes cavity flux. Section 1.2 uses it for neighboring-problem and definition comparisons, not a matched flat-wall/grooved-wall numerical reference. The accepted and published versions have not been matched page by page.
- **[8] Mohammadi–Floryan 2013:** the 32-page published paper, printed pages 23–54, DOI 10.1017/jfm.2013.184, is available. Reading has advanced beyond the earlier abstract to targeted assessment of the [local published full text](../PAPER1_nearest_work_comparison_20261109/sources/round2/Mohammadi2013_jfm.pdf). Eqs. (2.1) and (4.5) and Figures 4–5 support the general wall-shape framework, a planar wall and rectangular-groove geometry-reduction tests. Section 4.4.2 defines $EC_h$ by matching friction factor, rather than the present geometric mean height. On 2026-11-10, Figure 6(b), printed page 34, was checked and contains $S=0.08$; $S=0.06$ is therefore not a method-applicability ceiling. The apparent high-wavenumber approach of $EC_h$ to $2-S/2$ was not computationally confirmed in the source and is not an established limit adopted here. Its examples have not been recomputed, a matched accuracy ranking at the present geometry, low-inertia conditions and flux definition has not been established, and it does not prove identity with our mechanism interpretation. See the [full-text audit locators and limits](../PAPER1_MF_fulltext_audit_20261110/SOURCE_NOTES.md).
- **[9] Stroock et al. 2002:** *Patterning Flows Using Grooved Surfaces*, Analytical Chemistry 74(20), 5306–5312, DOI 10.1021/ac0257389. The [author-hosted seven-page published PDF](https://www.gmwgroup.harvard.edu/sites/g/files/omnuum10006/files/gmwgroup/files/822.pdf) is accessible through the PDF reader. Printed page 5307 was reread on 2026-11-10 for the flat-wall/small-amplitude sinusoidal-wall, no-slip pressure-driven configuration and flux definition. Download failures are recorded separately from actual source reading; page-level evidence is not downgraded to an abstract solely because a download failed. The paper supports prior anisotropic-boundary and transverse-flow results, not a matched accuracy reference for arbitrarily deep rectangular steps.
- **[10] Wilkening 2009:** full text arXiv:0706.4103v2 was read, including PDF page 33, Theorem 4.11 and Eqs. (4.110)–(4.112); the HTML rendering numbers the theorem as 18. The two-dimensional periodic height must satisfy the stated regularity and positive lower bound. An ideal jump fails those hypotheses; an undefined ordinary derivative norm cannot simply be assigned a value to claim a computed zero geometry constant. The expansion-error estimate has a different target from the continuous-conductance bounds in Appendix E and does not certify V2. Published DOI: https://doi.org/10.1137/070695447 .
- **[11] Dennis–Fai:** arXiv:2501.18575v4 is used, revised 2026-03-04 under the title *Comparison of Lubrication Theory and Stokes Flow in Corner Geometries with Flow Separation*. The version record was rechecked on 2026-11-13; a corresponding journal version was not confirmed. Checks covered the stationary-wall, fixed-flux step in Section 4.1 (PDF pages 7–10), corner occlusion in Section 4.2 and grid checks in Appendix B, pages 22–23. Reynolds pressure-drop underestimation implies conductance overestimation through linear response; this is a conversion between comparison quantities, not reproduction of K for our geometry. Its code was not downloaded, executed or accepted in this project. Fixed version: https://arxiv.org/abs/2501.18575v4 .
- **[12] Rom et al. 2021:** an institution-hosted 11-page full text was obtained; Sections 2–3, 4.3 and 5 (pages 9–10 for the conclusion) were checked. The reference is a finely resolved Reynolds solution. Symmetric textures can give the same averaged pressure; nonsymmetric coupling, local pressure reconstruction and friction require separate treatment. The source percentages are not our thresholds, and the averaging comparison does not certify the present Stokes conductances. Rom follows the PDF and Crossref author identity, rather than Roma in one institutional entry. DOI: https://doi.org/10.1016/j.apples.2021.100055 .
- **[13] Bayada–Chambat 1989:** Numdam full text was obtained; printed pages 205–207 and the related limiting-model discussion were checked. Limits from three-dimensional Stokes flow depend on relative film-thickness and roughness-period scales. The source retains proof and convergence-assumption limitations for some regimes; it is not cited as an unconditional complete proof for all roughness scales. It supplies model-hierarchy context rather than accuracy certification for our finite-parameter points. Source: https://www.numdam.org/item/M2AN_1989__23_2_205_0/ .
- **[14] Fourt–Arghir 2022:** Crossref identity and the publisher public abstract/introduction excerpts were checked. It compares homogenization and multiscale methods for compressible Reynolds problems, rather than directly recomputing Patir–Cheng against full Stokes flow. The complete PDF was not obtained; all derivations and error tables were not checked. DOI: https://doi.org/10.1016/j.triboint.2021.107251 .
- **[15] Wang 2003:** only registered abstract and metadata were checked. They describe eigenfunction matching for finite-depth rectangular grooves, directional effective slip in shear flow and channel applications. Full text was not obtained. The abstract neither rules out useful channel expressions nor establishes a direct K reference for our flat-wall/grooved-wall, finite-gap, all-no-slip configuration with total-fluid integration. No matched two-direction closed form was obtained in this check; this is not a nonexistence finding. DOI: https://doi.org/10.1063/1.1560925 .

- **[16] OpenLB:** Crossref identifies 2021, volume 81, pages 258–288; the [official software bibliography](https://www.openlb.net/articles/) locates the same DOI. Its older list uses 2020, whereas the final volume/pages are cited as 2021. Software-paper identity does not establish the version used by historical runs.
- **[17] Guo:** on 2026-10-27 the published PRE 65(4), 046308 six-page original, DOI 10.1103/PhysRevE.65.046308, was received. Pages 046308-1–3 were read for force density and Eqs. (15), (17), (19) and (20); last-page identity and continuity were checked separately. Paper force density F=ρg differs from lattice acceleration in FORCE. Current `PlainGuo`/`addExternalForce` uses ρ_lat times acceleration and (1−omega/2); `ForcedMomentum::computeU` adds FORCE/2, corresponding to the force term and half-step velocity. Scope, lines and SHA are in [the original-source receipt](../Primary_text_received_20261027/REPORT.md). This closes only the specified current implementation correspondence, not historical-build provenance or numerical accuracy.
- **[18] Bouzidi:** on 2026-10-27 the user-supplied published PoF 13(11), 3452–3459, DOI 10.1063/1.1399290, was received. The 9-page PDF has 1 cover page and 8 consecutive article pages. Identity and pagination were visually checked. The q/collision/streaming definitions on 3453, Figure 1 on 3454, stationary-wall linear formulas (5a)/(5b), Eq. (7) and stationary-wall applicability were read and compared with current D2/OpenLB q, branches, time levels, zero wall velocity and q=.5. Post-streaming array reads correspond to post-collision values in the paper. The paper assigns q=.5 to the later branch, while the implementation assigns it to the earlier branch; both expressions agree algebraically there. The six specified correspondences were checked for the inspected implementation; see [the receipt](../Bouzidi_P8_received_20261027/REPORT.md) for source lines/SHA, original and scope. This applies to valid wall links, finite inputs and the inspected normal streaming path. It does not qualify runtime fallbacks, historical binaries, arbitrary wall-distance/step second-order accuracy, zero boundary error or strict error bounds.
- **[19] GCI:** on 2026-10-27 the published 2008 JFE 130(7), 078001 four-page original, DOI 10.1115/1.2960953, was received and pages 078001-1–4 read. Its six last-page authors are recorded separately from the existing four-author ASME methods manuscript. Specified checks covered three grids and refinement ratios, steps 3–5/Eqs. (3)–(7), and iterative-error appendix Eqs. (A1)–(A3). In the published version, Eq. (4) uses superscript 21 while Eq. (6) still uses 12 internally, retaining the manuscript’s notation inconsistency; Table S5 defines unified notation separately. The version gap is closed within that scope; see [the source receipt](../Primary_text_received_20261027/REPORT.md). Method provenance does not turn historical mass FAIL into PASS, establish adequate iterative-error control or provide strict map-wide error bounds.

Full text, metadata, current source, saved output, historical builds and scientific acceptance are recorded separately. Missing full text does not mean a paper does not exist. Access records, original page previews and individual decisions are in the [source audit](../Methods_sources_data_audit_20261027/REPORT.md). The [older support audit](../Methods_support_audit_20261022/REPORT.md) retains its historical scope and does not supersede prior certificates. Third-party papers and the evidence of that source-audit round were not published to the shared repository.

<a id="sm-s12"></a>

## S12 Later controls and failure records

<a id="table-s8"></a>

**Table S8. Control-evidence index (not added to the 19-geometry, 46-record comparison set).**

The [machine-readable index](Table_S8_control_evidence.csv) binds sources and scopes. This compiles existing acceptance results without replaying trajectories or issuing new stage acceptance.

| Check | Geometry and grids | Existing evidence and status | Limit for this study |
|---|---|---|---|
| Historical analytical plates | h75, 5/2.5/1.25 nm | K errors 0.44444079/0.11103511/0.02715688%, S9 | Planar integrated quantity only |
| S0 implementation regression (A1 revision) | h75/d100, 5 nm, both directions | New A1 pair accepted; main flux, conductance and legacy-statistic regression checks pass, with mass-statistic supporting evidence; old v1.2 transverse failure retained | Implementation/statistic revision check, not new-geometry prediction or map-wide accuracy |
| S1 plate control | h30, d0, 1.25 nm | Previously accepted; K error about 0.173% | Not groove-resolution evidence |
| S2 regular-geometry grids | h60/d80, 5/2.5/1.25 nm | Along/across medium-to-fine changes 0.203234%/0.744252%; original grid checks pass | Specific control, not a map-wide error bound |
| S3 forcing control | h60/d80, three original force levels | Previously accepted stage | Not a V2 prediction test |
| S4 thin-gap grids | h30/d80, 5/2.5/1.25 nm | Six per-run checks pass; transverse change 1.328387035%>1%, so original S4 stage FAIL; GCI about 0.912232592% does not compensate | Excluded from main statistics; criteria and reference status unchanged |
| Historical fine transverse mass failure | h75/d100, 1.25 nm | Relative mass metric 1.1967043900362632×10⁻¹⁰>10⁻¹⁰, original FAIL/exit3, S9 | Distinct from h30/d80 grid FAIL |
| S4 server build reproduction | h30/d80 transverse, 1.25 nm | Matched K reproduction and saved-data checks support agreement | Does not turn the original S4 grid FAIL into PASS |

S4 medium-to-fine change uses 100|K_medium/K_fine−1|%, distinct from the K5-normalized change in the main-map two-grid table. Neither is a known continuous-solution error bound; division by another geometry's minimum model discrepancy cannot establish a safety factor. S5 has not been executed. Strict reference qualification, map-wide continuous-error bounds and physical validation have not been established. This manuscript compares models against specified discrete records without presenting the control chain as universally passing accuracy evidence.

<a id="sm-s13"></a>

## S13 Static averaged-model interfacing

At h75/d100, w120 and P240 nm, mean thickness 125 nm converts K (m³) to mean velocity and momentum resistance: J=−K∇p/μ, u_bar=J/H_bar and D=H_bar K⁻¹ (m⁻²). C01–C04 each compare a two-dimensional implementation with the OpenFOAM averaged-pressure implementation. GDI01 compares the V2 transverse momentum-source result with the C01 baseline. There are nine saved outlet endpoints, not two endpoints for each of five cases.

The synthetic static domain is 24×48 μm, with 16×32×1 cells, μ=0.001 Pa·s, driving-edge gauge pressures 24/0 Pa and no flux in the other direction. Replacing the local law with V2 reduces transverse/longitudinal outlet flow by 30.14%/56.77%. Summation of the nine original faces.csv records and acceptance/execution binding are indexed in the [claim audit](../PAPER1_claim_final_review_20261105/REPORT.md) and [recomputed outlets](../PAPER1_claim_final_review_20261105/recomputed_outlet9.csv). Equation (8) defines units and groove-attached directions. These checks support the tested static interface, not resolved-groove accuracy, experiments or dynamic-imprint fidelity.

<a id="sm-s14"></a>

## S14 Gradient-structure diagnostic for the two-width set

This section supports Sections 2.1, 2.4 and 5.1 of the main text. The diagnostic set has h75/d120, equal groove and ridge widths, and w60/240 nm (P120/480 nm). Both directions at 5/2.5 nm and the narrow-groove 1.25 nm states give ten target fields; two h75 flat-channel states at 5 nm are postprocessing controls. The 18-geometry, 36-result main map, added gap and supplementary diagnostic set are reported separately.

### S14.1 Definitions and continuous decomposition

We retain the assumptions of Appendix E: a fixed, fully liquid-filled domain; incompressible Newtonian Stokes flow with constant viscosity; stationary no-slip walls; and matched periodic boundaries. The cross-section Ω lies in the xz plane, the groove extends along y, the period is P=2w, and H(x) is h or h+d. Let $\boldsymbol v=\boldsymbol u/J$, with units of m⁻¹, distinct from the closure speed V in the main text and $\boldsymbol U=\mu\boldsymbol u/G$ in Appendix E. Define

\[
R_{\rm grad}=\frac\mu P\int_\Omega |\nabla\boldsymbol v|^2\,dA,
\quad R_i^{LC}=\mu/K_i^{LC},\quad R=G/J.
\]

The continuous Stokes energy balance gives $R_{\rm grad}=R$ under these assumptions. Physical dissipation is $2\mu D:D$, where $D=(\nabla\boldsymbol u+\nabla\boldsymbol u^T)/2$; its integral over the full domain equals the gradient energy, although the local densities generally differ.

For along-groove flow, set $v=u_y/J$ and $b=z(H-z)/(2K_\parallel^{LC})$. Since $P^{-1}\int_\Omega v\,dA=1$, integration by parts in z gives $\int_\Omega \partial_z v\partial_z b\,dA=\int_\Omega (\partial_z b)^2\,dA=P/K_\parallel^{LC}$. Expanding the square gives

\[
R-R_\parallel^{LC}=\frac\mu P\int_\Omega
\left[(\partial_xv)^2+(\partial_zv-\partial_zb)^2\right]dA.\tag{S14.1}
\]

Its second term measures departure of the thickness derivative of the velocity profile and includes changes in both profile shape and local flux allocation.

For across-groove flow, set $v=u_x/J$, $s=u_z/J$, and $c=6z(H-z)/H^3$. Incompressibility and no slip imply $\int_0^{H(x)}v\,dz=1$ for almost every x. This follows from the weak divergence condition after extending the velocity by zero into the solid and therefore includes the steps. Columnwise, $\int \partial_z v\partial_z c\,dz=\int (\partial_z c)^2\,dz=12/H^3$, which gives

\[
R-R_\perp^{LC}=\frac\mu P\int_\Omega
\left[(\partial_zv-\partial_zc)^2+(\partial_xv)^2+
(\partial_xs)^2+(\partial_zs)^2\right]dA.\tag{S14.2}
\]

We report profile-derivative departure, the streamwise gradient of the main velocity, and vertical-velocity gradients as three groups, combining the last two terms into the third group. The incompressibility constraint $\partial_xv=-\partial_zs$ shows that these are neither independent mechanisms nor a unique grouping.

The baselines b and c may be discontinuous in x at steps. The derivation uses only their columnwise z derivatives and does not treat them as admissible velocity fields for the full Stokes problem. The actual velocity retains zero trace on every vertical wall. A finite-energy weak solution suffices; classical second derivatives at the corners are not required. The flat-channel limit d=0 makes the right-hand sides vanish and recovers $K=h^3/12$.

### S14.2 Discrete implementation and limitations

Each final state is normalized using its saved J, with the two near-wall derivative treatments and nodal integration implemented in the diagnostic script. Let s_j be each nonnegative term divided by RLC, S=Σs_j, and E=R/RLC−1 be the driving excess. Shares are defined as 100s_j/S%, and the residual is 100(S−E)/E%. S is not adjusted to equal E. The main-text comparison uses 2.5 nm because it is available for both widths; the 5 nm and narrow-groove 1.25 nm results are retained. This choice does not qualify the comparison as a finest-grid or continuous reference.

The residual of total strain power relative to input power uses a different denominator, Pin, and must not be confused with the excess-resistance residual. For the ten targets under the primary derivative treatment, the former ranges from −0.5803% to +0.00259%; the largest absolute value of the latter is 1.5555% at 5 nm and 0.5336% at 2.5 nm. Only two grids are available for the wide groove, and the historical grid target for the narrow groove was not met. The maximum difference in shares between the two derivative treatments is 0.4252 percentage points; this is not an error bound. Native stress-moment power, both gradient-based power estimates and discrete divergence residuals are retained, rather than selectively reporting the smaller residuals.

Corner neighborhoods are reported for all three radii r/h=1/8, 1/4 and 1/2, together with their volume fractions. Regional power locates dissipation; it is neither the additional resistance omitted by the local model nor an independent causal contribution. No claim of corner dominance is based on a single radius.

### S14.3 Per-run data and provenance

<a id="table-s9"></a>

**Table S9. Per-run gradient diagnostics for the two-width supplementary set (ten target final states, primary derivative treatment).**

[Table_S9_mechanism_diagnostic.csv](Table_S9_mechanism_diagnostic.csv) retains run_id, geometry/period/grid, R/RLC, each positive term/RLC, their sum S, driving excess E, component shares and both residual types at full precision. P denotes along-groove and T across-groove flow. Inapplicable components are blank rather than zero. The alternative derivative treatment and two flat-channel controls remain in the complete diagnostic tables linked below and are excluded from these ten target rows.

Per-run identities and field checks are in [field_checks.csv](../PAPER1_mechanism_offline_20261109/field_checks.csv); native and both reconstructed power estimates in [power_checks.csv](../PAPER1_mechanism_offline_20261109/power_checks.csv); all positive terms and residuals in [positive_excess_diagnostic.csv](../PAPER1_mechanism_offline_20261109/positive_excess_diagnostic.csv); six strain components in [strain_components.csv](../PAPER1_mechanism_offline_20261109/strain_components.csv); and all three spatial-partition radii in [spatial_regions.csv](../PAPER1_mechanism_offline_20261109/spatial_regions.csv). The reader and derivative implementation are in [diagnose_fields.py](../PAPER1_mechanism_offline_20261109/diagnose_fields.py), input hashes in [source_manifest.json](../PAPER1_mechanism_offline_20261109/source_manifest.json), and diagnostic scope in [REPORT.md](../PAPER1_mechanism_offline_20261109/REPORT.md). These are offline diagnostics of known development final states, not new runs or independent prediction tests.


<a id="sm-s14-paired"></a>

### S14.4 Paired-width relations for conductance factors and anisotropy

The paired analysis uses eight existing directional records: two widths, two principal directions and grid spacings of 5 and 2.5 nm, representing two physical geometries. These known development records are not included in the statistics for the original 18 geometries and 36 principal-direction conductances. Tables S10–S13 retain all selected grids and both derivative stencils. Grid resolutions are not treated as independent replicates, and no statistical confidence intervals are constructed.

Define

\[
F_i=\frac{K_i^\Delta}{K_i^{LC}},\qquad
a_i=F_i^{-1},\qquad r_i=a_i-1,\qquad
B=\frac{A_{LC}}{A_\Delta}=\frac{a_\parallel}{a_\perp}
=\frac{1+r_\parallel}{1+r_\perp}.\tag{S14.3}
\]

If both directions share a positive multiplier $c$, their corrected relative discrepancies are $c a_i-1$. Allowing each geometry to use its own most favorable $c$, the smallest attainable maximum absolute relative discrepancy is

\[
c_* =\frac{2}{a_\parallel+a_\perp},\qquad
E_* = \min_{c>0}\max_{i\in\{\parallel,\perp\}}|c a_i-1|
=\frac{|a_\parallel-a_\perp|}{a_\parallel+a_\perp}
=\frac{|B-1|}{B+1}.\tag{S14.4}
\]

At $c_*$, the directional residuals have equal magnitudes and opposite signs. This is an algebraic minimax relation for two positive values, not a new fit, a physical conductance bound or a continuous-solution error bound. It requires the known discrete conductances and is used only as a retrospective diagnostic. It does not constrain V2, which uses separate directional factors. On the 2.5 nm grid, $100E_*$ is 51.08% and 14.38% for the narrow and wide grooves, respectively; the corresponding 5 nm values are 51.31% and 14.79%.

To connect this diagnostic to the gradient decomposition, let $s_{ij}$ be positive term $j$ for direction $i$, divided by that direction's $R_i^{LC}$, and let $S_i=\sum_j s_{ij}$. Retain $b_i=r_i-S_i$. Here $b_i$ is a residual, distinct from the local-plate velocity baseline $b(x,z)$ in Eq. (S14.1). Then

\[
B=\frac{1+S_\parallel+b_\parallel}{1+S_\perp+b_\perp}.\tag{S14.5}
\]

Table S13 uses $b_i=r_i-S_i$, the negative of the existing S14 convention for the positive-term sum minus drive excess; their absolute values agree. This residual is distinct from the total input-power balance. If $b_i$ is omitted and $B$ is reconstructed from positive-term sums alone, its relative differences from the scalar value are −0.24571%/−0.29939% for the narrow/wide grooves at 5 nm and −0.05870%/−0.10723% at 2.5 nm using the primary stencil. The alternative stencil gives −1.29032%/−0.16379% and −0.28858%/+0.01337%, respectively. These quantities come from the same known fields; their numerical agreement is not independent validation or a certification of continuous accuracy.

### S14.5 Paired-width figure and summary tables

<a id="figure-s1"></a>

![Four panels compare groove widths of 60 and 240 nm. In (a), the required conductance factors differ between directions, with a particularly low parallel factor for the narrow groove; corresponding points from the two grids are close. In (b), the local cubic law gives an anisotropy ratio of 4.908 at both widths, compared with approximately 1.589 and 3.674 at 2.5 nm. Panels (c) and (d) use a common vertical scale for directional gradient-excess contributions relative to each direction's own local-plate resistance. Parallel excess in the narrow groove is largest. Stacked positive sums and drive-derived excesses are shown separately rather than forced to coincide. Tables S10–S13 provide the full values and limitations.](figures/Figure_S1_paired_widths_EN.png)

**Figure S1. Directional conductance factors, anisotropy and gradient excess for an unchanged local aperture distribution.** The geometries have $h=75$ nm, $d=120$ nm and equal groove and ridge widths; $w=60/240$ nm corresponds to $P=120/480$ nm. (a) Conductance factors $F_i$ relative to the local cubic law. Circles denote parallel flow and squares transverse flow; open markers denote 5 nm and filled markers 2.5 nm. The dashed line marks $F_i=1$. (b) Anisotropy ratios from the same principal values and the common $A_{LC}$; grid symbols follow (a). Small horizontal offsets within a width category separate symbols and do not represent additional widths. (c,d) Nonnegative gradient-excess contributions for parallel and transverse flow using the primary stencil at 2.5 nm, divided by each direction's own $R_i^{LC}$. Both panels use the same vertical limits. These are dimensionless absolute contributions, not fractions of the positive-term sum; directional groupings differ. Stacked heights show $S_i$, and black diamonds show $r_i=K_i^{LC}/K_i^\Delta-1$, retaining their residual. No interpolation or statistical error bars are shown. Tables S10–S13 provide all values, the alternative stencil and the 5 nm decomposition. The historical narrow-groove grid target remains failed; the wide groove has only two grids. Continuous accuracy and a unique mechanism are not established.

[PDF](figures/Figure_S1_paired_widths_EN.pdf) · [SVG](figures/Figure_S1_paired_widths_EN.svg)

<a id="table-s10"></a>

**Table S10. Conductance factors and anisotropy**

[Table_S10_paired_width_conductance.csv](Table_S10_paired_width_conductance.csv)

| w (nm) | Δx (nm) | F_P | F_T | A_Δ | B=A_LC/A_Δ |
| --- | --- | --- | --- | --- | --- |
| 60 | 5 | 0.19284 | 0.59930 | 1.57930 | 3.10784 |
| 60 | 2.5 | 0.19101 | 0.58994 | 1.58922 | 3.08845 |
| 240 | 5 | 0.58047 | 0.78205 | 3.64311 | 1.34726 |
| 240 | 2.5 | 0.57915 | 0.77365 | 3.67428 | 1.33583 |

F_i=K_i^Δ/K_i^LC, A_Δ=K_P^Δ/K_T^Δ, and A_LC=4.90822394. F is calculated from existing conductances; it is not a newly calibrated V2 factor.

<a id="table-s11"></a>

**Table S11. Auxiliary diagnostic for a common multiplier**

[Table_S11_common_multiplier.csv](Table_S11_common_multiplier.csv)

| w (nm) | Δx (nm) | 100(B−1) (%) | c_* | 100E_* (%) |
| --- | --- | --- | --- | --- |
| 60 | 5 | 210.78 | 0.29178 | 51.31 |
| 60 | 2.5 | 208.85 | 0.28859 | 51.08 |
| 240 | 5 | 34.73 | 0.66635 | 14.79 |
| 240 | 2.5 | 33.58 | 0.66242 | 14.38 |

Each geometry is allowed its own optimal common multiplier: c_*=2/(a_P+a_T), E_*=|a_P−a_T|/(a_P+a_T), a_i=1/F_i. E_* is the smallest attainable maximum absolute relative discrepancy across the two discrete principal conductances. It is neither a physical conductance bound nor a continuous-solution error bound, and does not constrain models with separate directional factors.

<a id="table-s12"></a>

**Table S12. Absolute normalized gradient-excess contributions (2.5 nm, primary stencil)**

[Table_S12_gradient_excess.csv](Table_S12_gradient_excess.csv)

| w (nm) | Direction | Profile departure | Cross-groove gradient | Streamwise gradient | Vertical-velocity gradients | S_i | r_i | b_i=r_i−S_i |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 60 | P | 2.45739 | 1.77488 | — | — | 4.23227 | 4.23524 | +0.00296 |
| 60 | T | 0.62678 | — | 0.01903 | 0.04932 | 0.69514 | 0.69510 | -0.00004 |
| 240 | P | 0.19485 | 0.53205 | — | — | 0.72689 | 0.72666 | -0.00023 |
| 240 | T | 0.18837 | — | 0.03202 | 0.07374 | 0.29414 | 0.29257 | -0.00156 |

Each contribution is divided by its own directional R_i^LC and is dimensionless; it is not divided by the positive-term sum. The parallel profile term also includes changes in flux allocation. Groupings differ between directions. A dash denotes an inapplicable group, not a measured zero. Here r_i=K_i^LC/K_i^Δ−1, S_i is the sum of nonnegative terms, and b_i retains its sign. S_i has not been rescaled to r_i.

<a id="table-s13"></a>

**Table S13. Signed residuals for both grids and derivative stencils**

[Table_S13_gradient_residuals.csv](Table_S13_gradient_residuals.csv)

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

wall_quadratic is the primary stencil and odd_extension is the half-grid odd-extension stencil. The residual here is r_i−S_i, the negative of the existing S14 convention for the positive sum minus drive excess. Their absolute values agree. It is a decomposition residual, not the total input-power balance or a continuous-accuracy measure. The historical narrow-groove grid target remains FAIL; the wide groove has only two grids. These results do not establish grid independence. Full-precision components are in the [complete positive-excess diagnostic](../PAPER1_mechanism_offline_20261109/positive_excess_diagnostic.csv); paired scalar values and run provenance are in the [Table S10 data](Table_S10_paired_width_conductance.csv).

---

<a id="sm-s15-fem"></a>

## S15 Independent finite-element comparison: method, gates and per-point data

This section supports §3.4, §4.5, §5.4 and the fourth conclusion item. It reports a transverse-conductance comparison **listed alongside**, not inside, the main statistics: its references are a separate two-dimensional finite-element discretization, and it is **not** part of the 5 nm OpenLB main set. The result package, the counting-basis review and the adoption review are in `docs/reports/PAPER1_fem_v2_results_20261114/`, `PAPER1_fem_v2_results_review_20261114/` and `PAPER1_fem_v2_adoption_review_20261114/`.

### S15.1 Method

Two two-dimensional problems are solved on the same fixed geometries ($P=240$ nm, $w=120$ nm, equal groove and rib widths, $h$ and $d$ at the sampled values) under the same depth-integrated conductance definition (unit m³):

- along the grooves, the scalar Poisson problem $-\Delta U=1$;
- across the grooves, the incompressible Stokes problem $-\Delta U+\nabla\pi=\mathbf{e}_x$, $\nabla\cdot U=0$.

Quadratic velocity and linear pressure elements (Taylor–Hood triangles) are used; periodic boundaries are imposed by merging degrees of freedom; the pressure null space is removed by a Lagrange multiplier enforcing $\int\pi\,\mathrm{d}A=0$. Three grids of 5.0, 2.5 and 1.25 nm are solved in sequence, with **no retry and no automatic refinement**. Conductances are re-integrated from the saved fields as $K=(10^{-27}/P_{\mathrm{nm}})\int U_{\mathrm{main}}\,\mathrm{d}A$, without reusing the solver's internal integration.

The methodological limits must be read together with the numbers: the finite-element values are themselves discrete approximations; no error bound against the continuous solution is established at any point; and the discretization independence relative to OpenLB is not quantified. Differences between the two are therefore **numerical comparisons only**, not an error adjudication.

### S15.2 Counting basis

| Set | Count |
|---|---|
| Direction comparisons in this section | **36 = 19 along + 17 transverse** |
| With finite-element references | 34 |
| Along-groove references from previously qualified finite volume | 2 ($h=50$, $d=120$ and $h=125$, $d=120$ nm) |
| Paired geometries | 17 |
| Along-groove only | 2 ($h=25$ nm at $d=25$ and 50 nm; no transverse runs, by author decision) |
| Planned slots | 19×2 = 38 (**not** 38 completed comparisons) |

**Relation to the main statistics.** The 36 results of §4.2 are 18 geometries × 2 directions against 5 nm OpenLB references; the 36 here are 19 geometries against finite-element references. Geometry count, reference method and pairing all differ, so the two sets **must not be merged, substituted or averaged together**.

### S15.3 Gates and provenance

Gates were fixed before the runs and recomputed level by level from the saved fields:

| Check | Worst measured | Threshold | Threshold ÷ worst | Worst at |
|---|---:|---:|---:|---|
| coarse→mid conductance change | 0.1925% | 1% | 5.2× | $h=50$, $d=100$ |
| mid→fine conductance change | 0.0910% | 0.5% | 5.5× | $h=50$, $d=100$ |
| Re-assembled direct residual | $1.15773\times10^{-11}$ | $10^{-10}$ | 8.6× | $h=125$, $d=25$ |
| Finest-level power balance | $3.28\times10^{-10}$% | 0.1% | $3.0\times10^{8}$× | — |
| Finest-level section-flux spread | $1.49\times10^{-5}$% | 0.01% | $6.7\times10^{2}$× | — |
| Section vs volume | $1.56\times10^{-6}$% | 0.01% | $6.4\times10^{3}$× | — |
| Non-wall sections | 10 | ≥9 | +1 | all |

**The tightest items are the adjacent-grid changes (5.2×, 5.5×) and the direct residual (8.6×), not "three orders of magnitude on every item".** Adjacent-grid changes are not error bounds on the continuous solution.

All provenance items hold for the 12 runs: release fingerprint unchanged, unique `run_id`, command line and exit code recorded, per-level mesh and field hashes matching the receipts, and verification receipts written once. Runs were made on a server; after transfer, re-checking with another interpreter gave the same fingerprint. That re-check strengthens portability but does not constitute a third discretization. Current status is **candidate reference pending formal adoption**; formal status requires separate sign-off.

### S15.4 Table S14. Discrepancy statistics over the 17 transverse samples

Discrepancies are (method conductance / finite-element comparison − 1) × 100%.

[Table_S14_fem_transverse_summary.csv](Table_S14_fem_transverse_summary.csv)

| Method | Signed mean | Mean absolute | Range | Positive/negative |
|---|---:|---:|---|---:|
| 5 nm OpenLB | +2.7115% | 2.7115% | +1.2632% to +7.2841% | 17/0 |
| Local cubic law | +37.6350% | 37.6350% | +13.0882% to +56.4177% | 17/0 |
| Fixed V2 | +1.8309% | 4.2075% | −12.7835% to +6.4755% | 12/5 |

Reading: OpenLB is higher than the finite-element comparison at all 17 points. V2 reduces the mean absolute discrepancy substantially, but **its signed mean remains +1.83%**, so the remaining discrepancy is of mixed sign and **must not be described as unbiased**. "12 positive, 5 negative" shows only that not all points deviate in the same direction and does not establish the absence of systematic bias. The local-cubic-law mean absolute discrepancy is about 13.9 times the OpenLB/finite-element difference; this is a magnitude comparison on the present sample, not a completed total-error decomposition.

### S15.5 Table S15. Conductances, direction ratios and reconstructed angles over the 17 pairs

$A=K_{\parallel}/K_{\perp}$; $\beta$ is reconstructed through Eq. (5) from the same pair of principal values under 45° forcing and is **not** an independent oblique simulation. The last four columns are (model value / reference value − 1); angles in degrees.

[Table_S15_fem_paired_metrics.csv](Table_S15_fem_paired_metrics.csv)

| Geometry $(h,d)$ (nm) | $K_\perp$ (1e-23 m³) | OpenLB | Local law | V2 | $A_{\rm ref}$ | Local-law $A$ | V2 $A$ | Local-law $\beta$ | V2 $\beta$ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| h25/d100 | 0.2069 | +7.28 | +24.84 | −12.78 | 16.4815 | +92.65 | +19.22 | −1.67 | −0.56 |
| h50/d25 | 1.3735 | +3.16 | +17.01 | +0.55 | 1.3933 | +1.76 | +4.19 | −0.47 | −1.11 |
| h50/d50 | 1.4110 | +3.59 | +31.24 | +3.69 | 2.1447 | +18.02 | +4.95 | −3.44 | −1.04 |
| h50/d75 | 1.4133 | +3.64 | +38.54 | +2.41 | 3.0483 | +45.07 | +7.78 | −5.42 | −1.23 |
| h50/d100 | 1.4133 | +3.65 | +42.14 | −0.70 | 4.0260 | +80.31 | +11.58 | −6.11 | −1.40 |
| h50/d120 | 1.4134 | +3.65 | +43.74 | −3.53 | 4.8385 | +113.55 | +14.93 | −6.15 | −1.48 |
| h75/d25 | 4.2655 | +2.13 | +15.93 | −0.38 | 1.2025 | −0.37 | +2.02 | +0.10 | −0.56 |
| h75/d50 | 4.3373 | +2.50 | +33.32 | +5.33 | 1.5428 | +10.93 | −1.35 | −2.65 | +0.36 |
| h75/d75 | 4.3391 | +2.52 | +44.04 | +6.48 | 1.8968 | +33.45 | −0.85 | −6.24 | +0.20 |
| h75/d100 | 4.3398 | +2.52 | +50.19 | +4.93 | 2.2472 | +64.45 | +1.77 | −8.85 | −0.37 |
| h75/d120 | 4.3403 | +2.52 | +53.28 | +2.87 | 2.5258 | +94.32 | +4.58 | −10.08 | −0.86 |
| h100/d100 | 9.7326 | +1.87 | +52.22 | +6.35 | 1.6874 | +50.01 | −7.17 | −9.10 | +1.90 |
| h125/d25 | 18.2331 | +1.26 | +13.09 | −2.82 | 1.0980 | −1.94 | +0.40 | +0.56 | −0.11 |
| h125/d50 | 18.3527 | +1.46 | +30.00 | +2.70 | 1.2338 | +3.51 | −7.95 | −0.96 | +2.34 |
| h125/d75 | 18.3590 | +1.45 | +42.52 | +5.35 | 1.3461 | +17.75 | −12.52 | −4.36 | +3.73 |
| h125/d100 | 18.3679 | +1.45 | +51.28 | +5.69 | 1.4430 | +38.66 | −14.20 | −8.17 | +4.20 |
| h125/d120 | 18.3711 | +1.45 | +56.42 | +4.98 | 1.5154 | +59.40 | −14.21 | −10.93 | +4.15 |

Mean absolute deviations over the 17 pairs: $A$ falls from **42.7153%** to **7.6281%**; $\beta$ from **5.0155°** to **1.5071°**.

**Local counterexamples that must be retained.** The local-law $A$ is **underestimated** at $h=75$, $d=25$ nm (−0.37%) and $h=125$, $d=25$ nm (−1.94%) and positive at the other 15 pairs; both principal conductances being high does not guarantee that their ratio is high. V2 increases the absolute deviations of both $A$ and $\beta$ at $(50,25)$, $(75,25)$ and $(125,50)$, and decreases them at the other 14. "Overall improvement in $A$ and $\beta$" therefore holds, whereas "pointwise improvement" does not.

### S15.6 Table S16. Depth sensitivity within this sample

Fixed $w=120$ nm and area fraction 0.5.

[Table_S16_fem_depth_sensitivity.csv](Table_S16_fem_depth_sensitivity.csv)

| $h$ (nm) | $K_\perp$ change, $d=25\to120$ | $K_\perp$ change, $d=75\to120$ |
|---|---:|---:|
| 50 | +2.9033% | +0.0061% |
| 75 | +1.7534% | +0.0275% |
| 125 | +0.7570% | +0.0663% |

The three $d=75\to120$ values (0.006%, 0.028%, 0.066%) are **all below the adjacent-grid changes at these points** (0.077%–0.192%), so no precise continuous saturation threshold can be declared. The numbers support "under the sampled conditions the transverse conductance responds weakly to the listed depth changes and the response weakens with depth"; they do **not** support "depth has no effect" or "transverse leakage can only be suppressed by reducing the gap", because groove width, area fraction, groove shape and other adjustable variables were not compared. $K$ has units of m³ and is a depth-integrated conductance; it **should not be relabelled as a permeability in m²**.

### S15.7 Statements this section cannot support

1. "V2 validated" or "V2 established" — this section supplies comparison values only; the V2 coefficients come from prior calibration.
2. Describing all results here as formally qualified references: the new finite-element runs remain candidates, legacy finite-element results retain their limited-use recommendation and provenance limitations, and qualified finite-volume records retain their qualification.
3. "The true error of the OpenLB solver" — the finite-element values are approximations too, and no strict error bound exists.
4. "V2 is unbiased" — the signed mean is +1.83% and the remaining discrepancy is of mixed sign.
5. "The direction ratio is overestimated everywhere" — it is underestimated at two geometries.
6. "Transverse leakage can only be suppressed by reducing the gap" — other adjustable variables were not compared.
7. Merging with, or substituting for, the 36-result main statistics of the paper.

---

<a id="sm-s16-doe"></a>

## S16 Descriptive trend decomposition on the independent reference

This section supports Section 4.6, the closing paragraph of Section 5.1, and the fourth conclusion item. It repeats the trend judgements of Sections 4.2 to 4.4 on the independent reference of Section 4.5, in order to answer whether those trends are a product of the 5 nm lattice reference itself. Source records, recomputation script and checks are in `docs/reports/PAPER1_fem_v2_doe_20261114/`; this round is an offline recomputation, with **no simulation started, resumed or stopped**, no change to the V2 coefficients, frozen gates or historical FAIL decisions, and **no new reference qualification**.

### S16.1 Reference composition and counts

| Item | Content |
|---|---|
| Balanced matrix | $h=50$, 75, 125 nm × $d=25$, 50, 75, 100, 120 nm, **15 geometries** |
| Directional records | **30** (15 along groove + 15 across, both directions complete) |
| Along-groove reference | 13 finite-element values + 2 qualified finite-volume values ($h=50$, $d=120$ and $h=125$, $d=120$ nm) |
| Across-groove reference | 15 finite-element values |
| Test point for the mixed reference | $h=75$, $d=100$ nm (both methods present; 0.032% along, 0.005% across) |
| Single entries excluded from the matrix | $h=25$ nm at $d=25$, 50, 100 nm (the first two have along-groove values only); $h=100$, $d=100$ nm |

Both methods exist under identical conditions at $h=75$, $d=100$ nm and differ by far less than the percentage differences discussed here. This local agreement does not establish interchangeability across all geometries; the source composition must be disclosed, and the set **must not be described as entirely finite element**. No unsampled combination is interpolated.

### S16.2 Decomposition convention

For four responses (the signed along- and across-groove discrepancies of the local-cubic law and of fixed V2) the decomposition is **equal-weight** over the 15 grid points:

- Main-effect sums of squares: $SS_h=5\sum_{h}(\bar y_{h\cdot}-\bar y)^2$ and $SS_d=3\sum_{d}(\bar y_{\cdot d}-\bar y)^2$, where $\bar y_{h\cdot}$ and $\bar y_{\cdot d}$ are marginal means (arithmetic mean over the other variable at a fixed level);
- Interaction residual: $SS_{\rm tot}-SS_h-SS_d$;
- Shares: each sum of squares divided by $SS_{\rm tot}$.

**No $F$-test and no $p$-value are reported.** Each combination has a single deterministic outcome, and the complete two-factor interaction model has 15 cell-mean parameters. It is saturated, with **no independent residual degrees of freedom**. The shares are descriptive, not physical control fractions and not energy partitions.

### S16.3 Table S17 Descriptive shares for the four responses

[Table_S17_doe_shares.csv](Table_S17_doe_shares.csv)

| Response | $h$ share | $d$ share | Interaction residual | Signed grand mean |
|---|---:|---:|---:|---:|
| Local-cubic law, along groove | 5.03% | 93.40% | 1.58% | +94.07% |
| Fixed V2, along groove | 88.98% | 0.60% | 10.43% | +2.41% |
| Local-cubic law, across groove | 2.53% | 93.77% | 3.70% | +37.52% |
| Fixed V2, across groove | 22.19% | 42.54% | 35.27% | +2.50% |

Unrounded values: 5.0252 / 93.3994 / 1.5754, 88.9794 / 0.5955 / 10.4251, 2.5283 / 93.7741 / 3.6976, 22.1897 / 42.5448 / 35.2655; every row sums to 100%. The CSV also lists $SS_{\rm tot}$ for recomputation.

### S16.4 Table S18 Marginal means

[Table_S18_doe_marginals.csv](Table_S18_doe_marginals.csv)

| Response | $h=50$ | $h=75$ | $h=125$ | $d=25$ | $d=50$ | $d=75$ | $d=100$ | $d=120$ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Local-cubic law, along groove | +107.64 | +100.09 | +74.47 | +15.15 | +45.78 | +87.01 | +137.69 | +184.71 |
| Fixed V2, along groove | +9.13 | +5.09 | −7.00 | +1.32 | +2.42 | +2.70 | +2.76 | +2.84 |
| Local-cubic law, across groove | +34.54 | +39.35 | +38.66 | +15.34 | +31.52 | +41.70 | +47.87 | +51.15 |
| Fixed V2, across groove | +0.49 | +3.85 | +3.18 | −0.88 | +3.91 | +4.75 | +3.31 | +1.44 |

Percent, signed. On this fully balanced, equally weighted matrix, the grand mean of the 15 grid points equals both the arithmetic mean of the gap marginal means and the arithmetic mean of the depth marginal means before rounding. Where displayed rounding produces a last-digit difference, the unrounded values govern.

### S16.5 Table S19 Per-point values on the 15-point grid

[Table_S19_doe_grid.csv](Table_S19_doe_grid.csv)

The per-point values support three checks:

1. **The local-cubic-law discrepancy increases strictly monotonically with $d$**: after fixing $h$, all six sequences (three $h$ levels × two directions) are monotonically increasing.
2. **The along-groove V2 residual changes sign between $h=75$ and $h=125$ nm**: all five points at $h=75$ nm are positive (+1.6321 to +7.5876) and all five at $h=125$ nm are negative (−2.4278 to −9.9416). No precise zero crossing is given.
3. **The transverse V2 residual is not monotonic in $d$**: the $d=25$ column is +0.5517, −0.3758, −2.8189; the $d=75$ column is +2.4128, +6.4755, +5.3491; the depth marginal mean, averaged over gaps, is largest at this sampled level, which does not imply that every fixed-gap curve peaks there; the $d=120$ column is −3.5278, +2.8714, +4.9783. The marginal mean at $d=25$ is −0.88%, the only negative level.

### S16.6 Differences from the first round (5 nm reference)

The first round decomposed the signed V2 residuals only, on 18 geometries and 36 records. The two rounds compare as follows:

| Response | First round (5 nm OpenLB reference) | This round (independent reference) |
|---|---|---|
| Fixed V2, along groove | 87.65 / 0.77 / 11.58 | 88.98 / 0.60 / 10.43 |
| Fixed V2, across groove | **40.08 / 30.52 / 29.40** | **22.19 / 42.54 / 35.27** |

Format is $h$ share / $d$ share / interaction residual (%). **Algorithmic consistency is self-evidenced on the old data**: the same script recomputed 87.65 / 0.77 / 11.58 and 40.08 / 30.52 / 29.40 on the old 36 records, agreeing digit for digit with the published values. The full record sets differ, but the share comparison uses the same balanced subset, equal weighting and algorithm in both rounds. The differences above therefore reflect the changed discrepancy response when the numerical comparison is replaced, rather than a change of points in the analyzed matrix.

**The transverse ordering reverses completely**: $h$ moves from the largest term (40.08%) to the smallest (22.19%), $d$ from second to largest (42.54%), and the interaction rises from 29.40% to 35.27%. The transverse signed discrepancy on this matrix contains both main-effect and interaction components, which do not identify a physical controlling parameter; **that particular first-round set of numbers is reference-specific and must not be quoted as fixed fact**, and in particular must not be written as three roughly equal factors or as a physical equipartition.

### S16.7 Statements this section does not support

1. No $F$-test or $p$-value, and no claim of statistical significance.
2. Shares are not physical control fractions, energy partitions or variance contributions.
3. Depth is not the sole or principal physical control parameter. The sampled spans differ (50 to 125 nm against 25 to 120 nm), so the 93% against 5% contrast describes only the direction of variation within this parameter box.
4. No precise zero crossing; only the interval between $h=75$ and $h=125$ nm.
5. No continuous saturation threshold at $d\approx75$ nm, no claim that depth has no effect, and no claim that transverse leakage can only be suppressed by reducing the gap.
6. No extrapolation of the 15-point matrix to the single entries at $h=25$ nm or $h=100$ nm.
7. No statement that all 36 records use a finite-element reference (the composition is 34 finite element plus 2 finite volume).
8. No claim that V2 is independently validated on the strength of these trends. The new finite-element references remain candidates pending formal adoption; legacy finite-element limited-use recommendations and provenance limitations, and existing qualified finite-volume status, are retained separately.

### S16.8 Recomputation

```bash
cd docs/reports/PAPER1_fem_v2_doe_20261114 && python3 build_doe_v2.py
```

Expected: the old basis reproduces 87.65 / 0.77 / 11.58 and 40.08 / 30.52 / 29.40; the 15-point grid carries both directions; each of the four decompositions sums exactly to 100%.
