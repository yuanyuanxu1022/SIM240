# F2_dynamic_v3 Phase 1

Phase 1 is an independent copy of `F2_dynamic_v2_motion` for dynamic geometry
state management. It does not implement online material updates, Bouzidi
reinstallation, or modified `collideAndStream`.

## Modules

- `DynamicHeightLaw`: evaluates `h(t)=max(0,h0-compressionVelocity*t)`.
- `DynamicGeometryState`: predicts material labels from `materialAt(position,h)`
  without changing the live OpenLB geometry, and counts fluid/solid cells and
  volumes.
- `DynamicGeometryDiagnostics`: writes `dynamic_geometry.csv` with
  `step,time,height_nm,fluid_volume,solid_volume,changed_cells`.

## Build

```bash
make -C src
```

## Geometry trace test

The trace mode is an offline state-management test. It performs no
`collideAndStream` calls and does not install dynamic Bouzidi links:

```bash
bash scripts/run_geometry_trace.sh 75 0.1 100
```

Arguments are `h0_nm`, `compressionVelocity_m_s`, and number of diagnostic
steps. Results are written to a unique directory under `results/`.

The existing `precheck` and `steady` modes are copied from v2 for provenance,
but Phase 1 does not authorize formal dynamic compression calculations.
