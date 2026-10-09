# G2 EX240 grid-convergence paper summary

## 1. Research objective

G2 verifies hydraulic transport through the explicitly resolved periodic EX240 nanogroove geometry using OpenLB LBM. The analysis compares transport parallel and perpendicular to the groove direction and quantifies sensitivity to `dx=5`, `2.5`, and `1.25 nm` grids.

## 2. Model parameters

The archived results use the recorded G2 configuration: D3Q19 forced lattice, Forced BGK collision, and Bouzidi wall treatment. This archive does not alter or reinterpret the recorded physical parameters.

## 3. Grid verification

`K_parallel` is `9.834075958643652e-23`, `9.782423697043172e-23`, and `9.764325526249012e-23 m^3` at `dx=5`, `2.5`, and `1.25 nm`, respectively. `K_perpendicular` is `4.4490220210459354e-23`, `4.3852935121144107e-23`, and `4.358613368821741e-23 m^3` on the same grids. Both sequences are monotonic under refinement; the perpendicular coefficient has the larger grid sensitivity.

## 4. Richardson and GCI

The recorded Richardson analysis reports apparent orders `p=1.5129876294506368` for `K_parallel` and `p=1.2561724912115397` for `K_perpendicular`. Fine-grid GCI values are `0.12496593778028703%` and `0.5510219860185761%`, respectively. The corresponding medium-grid GCI values are `0.3559935199394659%` and `1.308170066726721%`. The mathematical asymptotic indicators are marked true in the source GCI file.

## 5. Driving-force linearity

No independent multi-force linearity table is present in the supplied G2 grid-convergence directory. Therefore this archive does not claim an R² or force-linearity result; that evidence must be cited from a separate validated dataset if used in a manuscript.

## 6. Directional transport and resistance

The recorded anisotropy `K_parallel/K_perpendicular` is `2.210390488544205`, `2.2307340819991053`, and `2.2402366762089274` for `dx=5`, `2.5`, and `1.25 nm`. Thus the parallel mobility is higher than the perpendicular mobility across the three grids. The reciprocal resistance ratio `R_perpendicular/R_parallel` is the same directional contrast expressed in resistance form.

## 7. Numerical limitations

The `dx=1.25 nm` EX240 perpendicular result has `run_gate_PASS=false`, `exit_code=3`, and recorded mass error `1.1967043900362632e-10`. Its numerical status is preserved in `G2_validation_status.md`; a mathematically valid GCI sequence does not convert this point into a full result PASS. The archive also contains no new grid or force-linearity calculations.

## 8. Input to later G3(h) studies

The archived GCI/cost balance supports using `dx=2.5 nm` as the production candidate for subsequent height-sweep studies, while retaining `dx=1.25 nm` as a reference grid. Endpoint or representative height cases should still be checked at the fine grid before treating a height trend as fully grid independent.
