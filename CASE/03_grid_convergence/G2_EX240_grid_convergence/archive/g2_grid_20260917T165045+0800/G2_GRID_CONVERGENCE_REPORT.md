# SIM240 G2 Step 3 grid-convergence report

Step 3 status: **FAIL / INCONCLUSIVE**

- nine-run numerical gate: FAIL
- absolute-mobility asymptotic GCI: PASS
- EX240 fine-grid GCI <= 2%: PASS
- recommended production grid: **none: Step 3 gate failed or is inconclusive**
- basis: Production-grid selection is blocked until the Step 3 gate passes.

## Three-grid transport results

| dx (nm) | K_smooth (m3) | K_parallel (m3) | K_perpendicular (m3) | eta_parallel | eta_perpendicular | anisotropy |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 3.5312498715575052e-23 | 9.8340759586436518e-23 | 4.4490220210459354e-23 | 2.78487116923 | 1.25990008718 | 2.21039048854 |
| 2.5 | 3.5195285780093276e-23 | 9.7824236970431719e-23 | 4.3852935121144107e-23 | 2.77946988644 | 1.24598889167 | 2.230734082 |
| 1.25 | 3.5165797338982587e-23 | 9.7643255262490124e-23 | 4.3586133688217411e-23 | 2.7766540972 | 1.23944676323 | 2.24023667621 |

## Richardson and GCI

| Metric | Type | p | extrapolated | GCI fine (%) | GCI medium (%) | asymptotic ratio | Check | Diagnosis |
|---|---|---:|---:|---:|---:|---:|---|---|
| K_smooth | monotonic | 1.99091 | 3.5155884849142972e-23 | 0.0352348 | 0.139937 | 0.999162 | PASS | asymptotic range confirmed |
| K_parallel | monotonic | 1.51299 | 9.7545638614795753e-23 | 0.124966 | 0.355994 | 0.99815 | PASS | asymptotic range confirmed |
| K_perpendicular | monotonic | 1.25617 | 4.3393998344635390e-23 | 0.551022 | 1.30817 | 0.993916 | PASS | asymptotic range confirmed |
| eta_parallel | monotonic | 0.939763 | 2.7735874993026406e+00 | 0.138053 | 0.264546 | 0.998987 | PASS | asymptotic range confirmed |
| eta_perpendicular | monotonic | 1.08841 | 1.2336387764007384e+00 | 0.585744 | 1.23899 | 0.994749 | PASS | asymptotic range confirmed |
| anisotropy | monotonic | 1.09818 | 2.2485661018158467e+00 | 0.464763 | 0.999224 | 1.00426 | PASS | asymptotic range confirmed |

## Relative-metric three-grid spans

- eta_parallel: 0.29554287%
- eta_perpendicular: 1.6383036%
- anisotropy: 1.3401246%

Orders and GCI values marked `n.a.` were intentionally not forced. See the diagnosis column.

## Gate boundaries

This report closes only G2 Step 3. It does not start G3, dynamic-punch, or two-phase work.
