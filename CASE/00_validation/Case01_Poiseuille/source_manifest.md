# Case01 Poiseuille Source Manifest

## Scope

- Gate: Gate 0 plus the explicitly authorized Gate 1 Case01 `dx=5 nm`, `ay=1e5 m/s²` run
- Purpose: retain the Gate 0 initialization check and the isolated Gate 1 formal Case01 entry
- Formal simulation: ONE CASE01 CONDITION COMPLETED; acceptance failed and no additional condition was started
- Existing case source modified or copied: NO
- Capture date: 2026-09-15 (Asia/Shanghai)

## Project Repository

- Project root: `/home/dell/yuanyuanxu/SIM240`
- Git branch: `main`
- Git commit: `5953d8a013e40e2402313834098bb37f12a8c487`
- Remote: `git@github.com:junjieli2/nanrPrint`
- Worktree state at Gate 0 start: DIRTY
- Pre-existing changes: tracked deletions and multiple untracked paths were present before Gate 0; they were not modified, cleaned, staged, or committed by this task

## OpenLB

- OpenLB root: `/home/dell/openlb`
- Header entry point: `/home/dell/openlb/src/olb.h`
- Static core library: `/home/dell/openlb/build/lib/libolbcore.a`
- Release declared by `rules.mk`: `1.8r1`
- Git branch: `master`
- Git commit: `882924a9cfc8dcdf82909e39530789cb6f5ebcc4`
- Git describe: `882924a`
- OpenLB worktree state: tracked files clean; three untracked files present (`config.mk.bak` and two example executables)

## Compiler and Build System

- Build system: GNU Make with an isolated Case01 Makefile reproducing the active OpenLB CPU/MPI configuration
- C++ compiler command: `/usr/bin/mpic++`
- MPI wrapper: Open MPI 4.1.6
- MPI wrapper backend: `g++`
- Compiler: g++ 13.3.0 (`Ubuntu 13.3.0-6ubuntu2~24.04.1`)
- C++ standard: C++20
- Floating-point type: `double`
- Parallel mode compiled: MPI
- Platform: CPU_SISD

Compilation flags:

```text
-O3 -Wall -march=native -mtune=native -std=c++20
-DOLB_VERSION="5953d8a-dirty" -pthread -DPARALLEL_MODE_MPI
-DPLATFORM_CPU_SISD -DDEFAULT_FLOATING_POINT_TYPE=double
```

Include paths:

```text
/home/dell/openlb/src
/home/dell/openlb/external/zlib
/home/dell/openlb/external/tinyxml2
/usr/lib/x86_64-linux-gnu/openmpi/include
/usr/lib/x86_64-linux-gnu/openmpi/include/openmpi
```

Link dependencies:

```text
/home/dell/openlb/build/lib/libolbcore.a
/home/dell/openlb/external/lib/libz.a
/home/dell/openlb/external/lib/libtinyxml2.a
pthread
Open MPI: mpi_cxx, mpi
```

## Machine

- Hostname: `dell-OptiPlex-Tower-Plus-7010`
- Operating system: Ubuntu 24.04.4 LTS
- Kernel: Linux 7.0.0-31-generic x86_64
- CPU: 13th Gen Intel Core i7-13700
- Logical CPUs: 24

## Case Files

- Frozen task document: `/home/dell/yuanyuanxu/SIM240/CASE/SIM240_First_Validation_Task_v2.1.md`
- Run configuration: `/home/dell/yuanyuanxu/SIM240/CASE/Case01_Poiseuille/run_config.md`
- New source: `/home/dell/yuanyuanxu/SIM240/CASE/Case01_Poiseuille/src/case01_geometry_check.cpp`
- Gate 1 source: `/home/dell/yuanyuanxu/SIM240/CASE/Case01_Poiseuille/src/case01_poiseuille.cpp`
- New Makefile: `/home/dell/yuanyuanxu/SIM240/CASE/Case01_Poiseuille/src/Makefile`
- Executable target: `/home/dell/yuanyuanxu/SIM240/CASE/Case01_Poiseuille/build/case01_geometry_check`
- Gate 1 executable: `/home/dell/yuanyuanxu/SIM240/CASE/Case01_Poiseuille/build/case01_poiseuille`

API reference inspected but not copied or modified:

- `/home/dell/yuanyuanxu/SIM240/grooveDNS/stage3_ex240_local/fixed_gap_single_phase/sim_ec1xt240_fixed_gap_dns.cpp`
- `/home/dell/yuanyuanxu/SIM240/grooveDNS/stage3_ex240_local/fixed_gap_single_phase/Makefile`

## Frozen Input and Source SHA-256

```text
24402e16c837e7c0b47d32e48210601089f17c2f3a0a051cac8758dbfbd06e0f  SIM240_First_Validation_Task_v2.1.md
33ef2e8709421ff8820bb4e6dff613ec4c49f385f38945b0cc896348cbdb7e8c  run_config.md
3fb912e0ff30e7d8b22601551c266cda3f0413ae86fa76d6715097ce79ed6e0e  src/case01_geometry_check.cpp
d58fb56fc9c8f282e2bfecddc261716f9586665333deac1e19e2475fd9133f7c  src/case01_poiseuille.cpp
3972c748db80c78abcb55ca8ab7be68d655ec4d36c322e6ba4cd53e5fcd0a153  src/Makefile
```

## Exact Build Commands

```text
make -C /home/dell/yuanyuanxu/SIM240/CASE/Case01_Poiseuille/src all

mpic++ -O3 -Wall -march=native -mtune=native -std=c++20 \
  -DOLB_VERSION="5953d8a-dirty" -pthread -DPARALLEL_MODE_MPI \
  -DPLATFORM_CPU_SISD -DDEFAULT_FLOATING_POINT_TYPE=double \
  -I/home/dell/openlb/src -I/home/dell/openlb/external/zlib \
  -I/home/dell/openlb/external/tinyxml2 -MMD -MP \
  -MF ../build/case01_geometry_check.d \
  -c case01_geometry_check.cpp -o ../build/case01_geometry_check.o

mpic++ ../build/case01_geometry_check.o \
  -o ../build/case01_geometry_check \
  -L/home/dell/openlb/build/lib -lolbcore \
  -L/home/dell/openlb/external/lib -lz -ltinyxml2 -lpthread

mpic++ -O3 -Wall -march=native -mtune=native -std=c++20 \
  -DOLB_VERSION="5953d8a-dirty" -pthread -DPARALLEL_MODE_MPI \
  -DPLATFORM_CPU_SISD -DDEFAULT_FLOATING_POINT_TYPE=double \
  -I/home/dell/openlb/src -I/home/dell/openlb/external/zlib \
  -I/home/dell/openlb/external/tinyxml2 -MMD -MP \
  -MF ../build/case01_poiseuille.d \
  -c case01_poiseuille.cpp -o ../build/case01_poiseuille.o

mpic++ ../build/case01_poiseuille.o \
  -o ../build/case01_poiseuille \
  -L/home/dell/openlb/build/lib -lolbcore \
  -L/home/dell/openlb/external/lib -lz -ltinyxml2 -lpthread
```

## Unknown Fields

- None at manifest creation time.

If compilation changes any source, Makefile, flag, dependency, or path, this manifest must be updated before the corresponding run is accepted.

## Gate 0 Verification Evidence

- Verification time: `2026-09-15T20:49:15+08:00`
- MPI ranks: 1
- `collideAndStream` calls: 0
- Formal simulation started: NO
- Geometry/material/converter check: PASS
- Independent shell exit code: 0
- In-plane domain: `Lx = Ly = 240 nm`
- Fluid material-1 nodes: 34560 (expected: 34560)
- Material-2 substrate nodes: 2304
- Material-3 upper-wall nodes: 9216

Evidence files:

- `/home/dell/yuanyuanxu/SIM240/CASE/Case01_Poiseuille/results/gate0_geometry_check_verify.txt`
- `/home/dell/yuanyuanxu/SIM240/CASE/Case01_Poiseuille/results/gate0_geometry_check_exit.txt`

SHA-256 after verification:

```text
b61ef16f5406da80a3eb7dc168ac95615efbc6aa87e9efa35fc1e1ad5f14ff08  build/case01_geometry_check
3202f634a073fab998f1ddfc2d8247729d845f29059397f7e98acbd5608247c9  results/gate0_geometry_check_verify.txt
c9b48e6015ef7a0af030b7b84c0452a6597d417852987fb4fd26a9099933a0e5  results/gate0_geometry_check_exit.txt
```

## Geometry-Length Resolution

The earlier `L = 2.4 μm` preparation value was replaced by `Lx = Ly = 240 nm` under explicit user instruction. This now matches the frozen v2.1 periodic-cell definition. The frozen v2.1 document itself was not modified.

## Gate 1 Formal Run

- Run ID: `gate1_case01_dx5_a1e5_20260915T210323p0800`
- Output directory: `/home/dell/yuanyuanxu/SIM240/CASE/Case01_Poiseuille/results/gate1_case01_dx5_a1e5_20260915T210323p0800`
- Frozen-window convergence: YES, step 1704
- Acceptance: FAIL
- Independent shell exit code: 3
- Failure criteria: `Jy` relative analytic error and velocity-profile relative L2 error exceeded 2%
- Additional Gate1 runs started: NO
- Case01a, Case01b or Case02 entered: NO

The complete time history, final result, cell-centred velocity profile, initial/final VTK fields, full log, run manifest and independent exit code are stored inside the output directory. See its `validation_report.md` for the threshold-by-threshold decision.
