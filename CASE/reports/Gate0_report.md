# Gate0 Report

## 1. Environment

- machine: `dell-OptiPlex-Tower-Plus-7010`; Ubuntu 24.04.4 LTS; Linux 7.0.0-31-generic x86_64; Intel Core i7-13700; 24 logical CPUs
- compiler: `/usr/bin/mpic++` using g++ 13.3.0; Open MPI 4.1.6; C++20
- build system: GNU Make 4.3
- OpenLB path: `/home/dell/openlb`
- OpenLB version: `1.8r1`
- OpenLB commit: `882924a9cfc8dcdf82909e39530789cb6f5ebcc4`
- OpenLB branch: `master`
- project branch: `main`
- project commit: `5953d8a013e40e2402313834098bb37f12a8c487`
- project worktree at inspection: DIRTY; pre-existing tracked deletions and untracked paths were not cleaned, staged, committed, or otherwise modified by Gate 0

Project structure inspected at depth 2:

```text
/home/dell/yuanyuanxu/SIM240/
├── CASE/
│   ├── Case01_Poiseuille/
│   ├── H/
│   ├── SIM240_First_Validation_Task_v2.0.md
│   ├── SIM240_First_Validation_Task_v2.1.md
│   └── SIM240_论文框架_Draft_v1.0(1).md
├── grooveDNS/
│   ├── archive/
│   ├── ex240_homogenization/
│   ├── post/
│   ├── stage1_mass_flux_audit/
│   ├── stage2_blocking_audit/
│   ├── stage3_design_review/
│   ├── stage3_ex240_local/
│   ├── stage3_free_sphere_test/
│   ├── stage3_minimal_test/
│   └── stage3_moving_piston_test/
├── output/
├── SIM240/
└── ZJ/
```

OpenLB is built with GNU Make using the active CPU/MPI configuration. Relevant configuration is C++20, `-O3 -Wall -march=native -mtune=native`, MPI, CPU_SISD, and `double` precision. Required core/static and external libraries were found and the executable's dynamic dependencies resolve.

## 2. Directory

```text
Case01_Poiseuille/
├── source_manifest.md
├── run_config.md
├── src/
│   ├── Makefile
│   └── case01_geometry_check.cpp
├── build/
│   ├── case01_geometry_check
│   ├── case01_geometry_check.d
│   └── case01_geometry_check.o
└── results/
    ├── gate0_geometry_check.txt
    ├── gate0_geometry_check_verify.txt
    └── gate0_geometry_check_exit.txt
```

No existing case source was copied or modified. The new source uses the inspected OpenLB API only as a reference.

## 3. Frozen Protocol Status

- D3Q19: CONFIRMED
- ForcedBGK: CONFIRMED
- Lx = Ly = 240 nm: CONFIRMED
- H = 75 nm: CONFIRMED
- dx = 5 nm: CONFIRMED
- dt = 1.0×10⁻¹¹ s: CONFIRMED
- tau = 1.7: CONFIRMED
- a = 1×10⁵ m/s² in +y: CONFIRMED
- x boundary: periodic, CONFIRMED
- y boundary: periodic, CONFIRMED
- z boundary: fixed halfway bounce-back no-slip walls, CONFIRMED
- physical integrals: material 1 only, CONFIRMED

The earlier Case01 preparation length conflict has been resolved under explicit user instruction: the in-plane domain is now `Lx = Ly = 240 nm`, consistent with the frozen v2.1 periodic-cell definition. The v2.1 document was not modified.

## 4. Case01 Preparation

- independent directory created: YES
- run configuration created: YES
- source manifest created: YES
- compilation successful: YES
- executable generated: YES
- build currently up to date (`make -q` exit 0): YES
- geometry initialization successful: YES
- material distribution successful: YES
- lattice/converter initialization successful: YES
- independent shell exit code recorded: 0
- formal simulation started: NO
- `collideAndStream` calls: 0

Initialization evidence:

```text
nx=48
ny=48
nz_fluid=15
material_1_fluid_nodes=34560
expected_fluid_nodes=34560
material_2_substrate_nodes=2304
material_3_upper_wall_nodes=9216
geometry_pass=true
converter_pass=true
PASS=true
```

Problem status: the 2.4 μm versus 240 nm length discrepancy is RESOLVED. No unresolved Gate 0 geometry, compilation, or initialization issue remains.

## 5. Next Step Recommendation

Gate1 Case01单工况验证。
