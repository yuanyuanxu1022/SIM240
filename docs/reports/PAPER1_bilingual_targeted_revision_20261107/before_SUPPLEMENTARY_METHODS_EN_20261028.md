# Supplementary materials: methods, numerical references and provenance

Companion Chinese manuscript: `SIM240_中文稿_导师审阅版_20261022.md`. The synchronized English manuscript is `SIM240_First_Paper_English_20261028.md`; the English supplement in this directory is `SUPPLEMENTARY_METHODS_EN_20261028.md`.

Numbering version: 2026-10-24, with author-adopted Table S5 and qualifications added on 2026-10-27. This author-review document defines S1–S11 and Tables S1–S5. Bilingual review layout was completed on 2026-10-28; final target-journal formatting remains unchecked. Previous private sharing coverage is recorded in `../GITHUB_FIRST_PAPER_COMPLETE_20261028/REPORT.md`; the current bilingual-layout increment has not been uploaded. Data are from existing D2/D3 and historical benchmarks. Separate D4 extension calculations are not included, and the manuscript’s V2 relation is retained.

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

<a id="sm-s1"></a>

## S1 Geometry, sampling and run inventory

The regular-region period of 240 nm and stripe width of 120 nm agree with the existing [layout report](/home/dell/yuanyuanxu/SIM240/docs/ex240/ex240_layout_report.md). Design file `SIM-EC1XT240.OAS` has SHA256 `209fbd4b907dc591c8786035face94de7df05fd10debf7e73dfc51a186ac0bfc`. This is design provenance, rather than measurement of fabricated dimensions. Checks on 2026-10-22 to 23 matched file identity to the parsing record; OAS parsing was not rerun.

At h=50, 75 and 125 nm, the main map samples d=25, 50, 75, 100 and 120 nm; at h=25 nm, only d=25, 50 and 100 nm are sampled. Each of 18 geometries has P (along-groove, +y) and T (across-groove, +x) forcing, giving 36 principal-direction samples.

<a id="table-s1"></a>

**Table S1. Run inventory for the D2/D3 map and additional checks (52 runs).**

Complete table: [Table_S1_run_inventory.csv](Table_S1_run_inventory.csv). It contains 36 main-map runs, 8 refinements, 2 viscosity checks and 6 oblique cases. Each row gives geometry, direction, grid, K, original-result path, manifest, log, binary hash and independent exit code.

The 52 runs exclude the periodic-replication/multi-force checks in S8 and the historical flat-wall/three-grid benchmarks in S9. Different evidence inventories can reuse the same physical benchmark; file counts must not be summed as independent new runs.

<a id="sm-s2"></a>

## S2 Current implementation and physical-unit conversion

The [current D2 source](/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp) specifies D3Q19_FORCE, ForcedBGK, τ=1, Lx=Ly=240 nm and uniform acceleration a=10⁵ m/s². Density ρ=1000 kg/m³ and kinematic viscosity ν=10⁻⁶ m²/s give μ=ρν=1 mPa·s. With physical properties fixed, dt=(τ−1/2)dx²/(3ν). Thus dx=5/2.5 nm corresponds to dt≈4.1667e−12/1.0417e−12 s. Two μ=15 mPa·s cases are separate from the main map.

The current OpenLB [ForcedBGK definition](/home/dell/openlb/src/dynamics/dynamics.h:224) uses PlainGuo; [computeU](/home/dell/openlb/src/dynamics/momenta/elements.h:1601) adds FORCE/2. The current Makefile and source tree are implementation evidence, but do not automatically bind every historical binary. See S10.

<a id="sm-s3"></a>

## S3 Boundary links and low-Mach diagnostics

All 46 D2 main-map, refinement and viscosity cases identified in the manuscript record q_min=q_max=0.5. The 52 records including 6 oblique cases have the same value. Saved maximum Mach numbers range from 5.69301195e−10 to 4.06765288e−7.

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

Complete table: [Table_S5_conditional_gci.csv](Table_S5_conditional_gci.csv). Original three-grid values and statuses are in Table S4. Fine, medium and coarse spacings are 1.25, 2.5 and 5 nm, with $r_{21}=r_{32}=2$ and $F_s=1.25$. The flat-wall gap is 75 nm; the groove reference has $h=75$ nm, $d=100$ nm, period 240 nm and width 120 nm. The original properties are $\rho=1000$ kg/m³, $\mu=1$ mPa·s, $a=10^5$ m/s² and $\tau=1$. The [original protocol](/home/dell/yuanyuanxu/SIM240/CASE/03_grid_convergence/G2_EX240_grid_convergence/STEP3_PROTOCOL.md) contains the complete geometry and parameters. K is in m³. Each eta is directional K divided by same-grid flat-wall K; anisotropy is along-groove K divided by across-groove K. Both are dimensionless. The method follows manuscript reference [10]; original-version checks are bounded in S11.

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

<a id="sm-s11"></a>

## S11 Scope of method-citation checks

Reference [6] was updated on 2026-10-28; other entries retain their individual check dates. Numbers follow the companion manuscript. These are source-check scopes, rather than a blanket release of project accuracy:

- **[4] Patir–Cheng:** Eqs. (23) and (24) on printed page 15 of the available lawful local full text were visually rechecked. They support harmonic/arithmetic averages within the one-dimensional Reynolds model, not an exact resolved step-domain solution or a unique dissipation mechanism.
- **[5] Dewangan–Datta 2020:** a 35-page PDF of JFM 891, A12, DOI 10.1017/jfm.2020.134 was received and its first-page title, authors and abstract identity checked. Its SHA matches the prior download exactly. No new full-text theoretical-applicability adjudication was performed. It is neither [8] Bouzidi nor the 2018 paper [6], and cannot replace either original source.
- **[6] Dewangan–Datta 2018:** the title is *Flow through microchannels with topographically patterned wall: A spectral theory for arbitrary groove depths*, European Journal of Mechanics–B/Fluids 70, 73–84, DOI 10.1016/j.euromechflu.2018.02.004. On 2026-10-28 the complete accepted manuscript was received, comprising 1 publisher cover page and manuscript pages 1–34, with identity matching Crossref. Manuscript pages 4–8, 11–13, 21–24 and 29 were read. The main problem is fully developed, steady, incompressible Newtonian along-groove flow between a sinusoidal wall and a flat wall. Eqs. (1) and (2) use viscous–pressure balance and no slip at both walls. The full spectral method does not require small amplitude; small-amplitude, thick/thin-channel and slip asymptotics have separate limiting assumptions. Its h is period-mean height and a is sinusoidal amplitude, not the present residual gap h and rectangular depth d. Q/Q0 is dimensionless flow relative to a planar channel of the same mean height, rather than K in m³. Page 22 discusses possible loss of exponential spectral convergence for nonsmooth rectangular grooves; page 24 lists transverse flow as future work. It does not certify present rectangular-groove P/T or map-wide accuracy. These specified applicability conditions were checked at accepted-manuscript level. The journal version has not been matched page by page; original examples were not reverified and strict error bounds were not certified. See the [receipt report](../Dewangan2018_received_20261028/REPORT.md).
- **[7] OpenLB:** Crossref identifies 2021, volume 81, pages 258–288; the [official software bibliography](https://www.openlb.net/articles/) locates the same DOI. Its older list uses 2020, whereas the final volume/pages are cited as 2021. Software-paper identity does not establish the version used by historical runs.
- **[8] Bouzidi:** on 2026-10-27 the user-supplied published PoF 13(11), 3452–3459, DOI 10.1063/1.1399290, was received. The 9-page PDF has 1 cover page and 8 consecutive article pages. Identity and pagination were visually checked. The q/collision/streaming definitions on 3453, Figure 1 on 3454, stationary-wall linear formulas (5a)/(5b), Eq. (7) and stationary-wall applicability were read and compared with current D2/OpenLB q, branches, time levels, zero wall velocity and q=.5. Post-streaming array reads correspond to post-collision values in the paper. The paper assigns q=.5 to the later branch, while the implementation assigns it to the earlier branch; both expressions agree algebraically there. The six specified correspondences were checked for the inspected implementation; see [the receipt](../Bouzidi_P8_received_20261027/REPORT.md) for source lines/SHA, original and scope. This applies to valid wall links, finite inputs and the inspected normal streaming path. It does not qualify runtime fallbacks, historical binaries, arbitrary wall-distance/step second-order accuracy, zero boundary error or strict error bounds.
- **[9] Guo:** on 2026-10-27 the published PRE 65(4), 046308 six-page original, DOI 10.1103/PhysRevE.65.046308, was received. Pages 046308-1–3 were read for force density and Eqs. (15), (17), (19) and (20); last-page identity and continuity were checked separately. Paper force density F=ρg differs from lattice acceleration in FORCE. Current `PlainGuo`/`addExternalForce` uses ρ_lat times acceleration and (1−omega/2); `ForcedMomentum::computeU` adds FORCE/2, corresponding to the force term and half-step velocity. Scope, lines and SHA are in [the original-source receipt](../Primary_text_received_20261027/REPORT.md). This closes only the specified current implementation correspondence, not historical-build provenance or numerical accuracy.
- **[10] GCI:** on 2026-10-27 the published 2008 JFE 130(7), 078001 four-page original, DOI 10.1115/1.2960953, was received and pages 078001-1–4 read. Its six last-page authors are recorded separately from the existing four-author ASME methods manuscript. Specified checks covered three grids and refinement ratios, steps 3–5/Eqs. (3)–(7), and iterative-error appendix Eqs. (A1)–(A3). In the published version, Eq. (4) uses superscript 21 while Eq. (6) still uses 12 internally, retaining the manuscript’s notation inconsistency; Table S5 defines unified notation separately. The version gap is closed within that scope; see [the source receipt](../Primary_text_received_20261027/REPORT.md). Method provenance does not turn historical mass FAIL into PASS, establish adequate iterative-error control or provide strict map-wide error bounds.

Full text, metadata, current source, saved output, historical builds and scientific acceptance are recorded separately. Missing full text does not mean a paper does not exist. Access records, original page previews and individual decisions are in the [source audit](../Methods_sources_data_audit_20261027/REPORT.md). The [older support audit](../Methods_support_audit_20261022/REPORT.md) retains its historical scope and does not supersede prior certificates. Third-party papers and the evidence of that source-audit round were not published to the shared repository.
