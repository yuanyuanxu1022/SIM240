# Case01-Bouzidi Source Manifest

## Status

- Case: `Case01-Bouzidi`
- Scope: code integration and 20-step short test only
- Parent evidence retained: `../Case01_Poiseuille/` (not modified)
- Frozen protocol modified: NO
- Formal simulation: NO

## Environment

- Project root: `/home/dell/yuanyuanxu/SIM240`
- OpenLB root: `/home/dell/openlb`
- OpenLB release: `1.8r1`
- OpenLB commit: `882924a9cfc8dcdf82909e39530789cb6f5ebcc4`
- Compiler: `/usr/bin/mpic++` using g++ 13.3.0
- C++ standard: C++20
- Build system: GNU Make

## Source and API

- Entry source: `src/case01_bouzidi_short_test.cpp`
- Build file: `src/Makefile`
- Executable: `build/case01_bouzidi_short_test`
- Boundary API: `/home/dell/openlb/src/boundary/setBouzidiBoundary.h`
- Distance field: `/home/dell/openlb/src/boundary/bouzidiFields.h`
- Reference example: `/home/dell/openlb/examples/laminar/poiseuille3d/case.h`

## Compile flags

```text
-O3 -Wall -march=native -mtune=native -std=c++20
-DOLB_VERSION="5953d8a-dirty" -pthread -DPARALLEL_MODE_MPI
-DPLATFORM_CPU_SISD -DDEFAULT_FLOATING_POINT_TYPE=double
```

## Dependencies

```text
/home/dell/openlb/build/lib/libolbcore.a
/home/dell/openlb/external/lib/libz.a
/home/dell/openlb/external/lib/libtinyxml2.a
pthread
Open MPI
```

## Hashes and run evidence

- Source SHA-256: `26a4c9fde4c0e6c50dd72beb75c64d81065429b4e4fb794ee5785731d3873058`
- Makefile SHA-256: `bb12e5bd31628c27aba043d4d8c61355ac2399dd06d90d1e462339a7bc3dbb35`
- Executable SHA-256: `21069d084e88e0b16ddd5c9f1c44cc98544c09b297a111c2b19f79b974b9f374`
- Compilation exit code: `0`
- Compilation warnings: none emitted
- Short-test run: `results/bouzidi_short20_20260915T230456p0800`
- Short-test shell exit code: `3`
- Steps completed: `20`
- Boundary audit: `FAIL`
- Formal or steady-state result: **NO**

The nonzero short-test exit is retained as diagnostic evidence. No expanded or
steady-state run was started after the boundary audit failed.

## Periodic-link and exact-plane repair

- Updated source SHA-256: `a1f8c7ef10c512ae1791b640bd671ef312b9a107034935ac0c0ebf02ddfa27d1`
- Updated executable SHA-256: `fd646b922bc09c54434dc4b7d4aad1b658d882f25c16e9c2abb6dba9901f2f42`
- Compilation exit code: `0`
- Compilation warnings: none emitted
- Short-test run: `results/bouzidi_boundaryfix_short20_20260915T231339p0800`
- Short-test shell exit code: `0`
- Steps completed: `20`
- Strict boundary audit: `PASS`
- Theoretical/candidate/installed links: `23040/23040/23040`
- Geometric and missing-neighbor fallbacks: `0/0`
- Unresolved boundary anomalies: `0`
- Formal or steady-state result: **NO**
