# S4 单条横槽补证：服务器版准备协议（S4-TGE-SERVER-v1）

状态：**准备阶段，无任何执行授权。** 全部 execution flag 为 false。

## 1. 为什么要有这一版

本机（i7-13700 / 31 GiB / /home/dell）在 2026-11-04 17:16 执行 3＋1 零步审计时，`precheck` 在 8 GiB 单进程地址空间内抛 `std::bad_alloc` 中止（exit −6，10.4 秒，推进 0 步）。节点数对比确认这是容量不足：

| | dx = 1.25 nm | dx = 0.625 nm |
|---|---|---|
| 流体节点 | 2 064 384 | 16 515 072（**8 倍**） |
| 全域格点 | 3 317 760 | 26 542 080 |

服务器 `10.103.102.55`（AMD EPYC 9B14 / 188 GiB / Ubuntu 22.04）有足够内存。但**本机封存不能搬过去**：`preparation_S.json` 之外，本机准备 A 里有 2103 处绝对路径指向 `/home/dell/yuanyuanxu/SIM240`，`canonical()` 要求绝对路径且按路径查哈希。因此本版是**在服务器上重新建立的一份准备**，与 A 是兄弟关系，不是继承关系。

## 2. 与本机准备的差别

| 项目 | 本机 A | 服务器 S |
|---|---|---|
| 输入键 | 绝对路径 | 项目内文件用**相对 ROOT 的路径**；OpenLB 与系统头用绝对路径并登记在 `external_roots` |
| 原生 ELF | `5c3836e9…b07b` | 服务器重编（`-march=native`，EPYC 架构） |
| 正式计划 | 1 个（0.625） | **2 个**（1.25 重跑 + 0.625 补证） |
| 零步计划 | 3 个（0.625） | 3 个（0.625） |
| 地址空间上限 | 8 GiB（已证明不足） | 64 GiB（提案，未采用） |
| 可用内存前置 | 12 GiB | 80 GiB（提案，未采用） |
| 引用本机历史 | 完整父链闭包 | 只引用**内容哈希**（A、1.25 接受记录、网格 FAIL 记录、独立复核） |

## 3. 为什么正式计划有两个

本机 5 / 2.5 / 1.25 nm 三个已接受点是**本机构建**产出的。服务器是新 ELF。若 0.625 用新构建、1.25 用旧构建，网格加密对比就跨了两个构建——本项目有 D2 混构建的前科，不能重犯。

因此在服务器上把 1.25 nm 也重跑一遍，得到同一构建的配对。1.25 nm 在本机耗时 4326 秒，服务器单核更快，预计 1 小时内完成。

## 4. 构建等价判据（在测量之前声明）

- 参照：本机 1.25 nm T 方向已接受结果，`K = 3.471791836744987e-24 m³`，completion SHA `2599a496…de069a`。
- 判据：服务器重跑的 K 与参照的**相对偏差 ≤ 1e-6**。
- 依据：网格判据本身是 1e-2；构建等价取 1e-6，留四个数量级余量。同一份源码、同一配置、同一编译器大版本，差异应远小于此。
- 失败处置：**停。** 两个构建不可互换，0.625 的结果不能与原始 5/2.5 nm 点配对。

该判据写死在 `server_stage.BUILD_EQUIVALENCE_RTOL` 与 `lineage.build_equivalence_criterion` 中，并由 `verify_lineage` 校验其未被改动。

## 5. 资源提案（提案，不是采用，不是授权）

```
1 进程 / 1 线程 / 1 cuboid / overlap 3
单进程地址空间 64 GiB      （本机 8 GiB 已被证明不足）
可用内存前置 80 GiB        （本机 188 GiB，当前可用 126 GiB）
首批空闲磁盘 200 GiB，之后每次 20 GiB（当前空闲 456 GiB）
单次输出上限 16 GiB        （0.625 nm 一帧约 0.85 GB）
每次原生调用 / 读场 各 900 秒
失败即停，不重试、不加时、不加内存
```

**这些数字没有任何实测支撑。** 64 GiB 取"比已知不足的 8 GiB 大得多、又能在 126 GiB 里留出余量"的位置，目的是让零步审计去**测量真实占用**，而不是又一次撞在帽子上。实际峰值必须以带 `/usr/bin/time -v` 的零步回执为准。

## 6. 目录

```
CASE/unseen_v2_reference_S4_tge_server_v1/
  PROTOCOL.md
  scripts/prepare_server_preparation.py   生成封存
  scripts/audit_zero_server.py            零步控制器（默认只读）
  common/server_zero_resources.json       资源提案副本
  evidence/preparation_S.json(+.sha256)   封存
  evidence/build_environment.json         服务器构建捕获
  evidence/ldd_at_preparation.txt
  reference/                              本机历史的内容哈希参照（4 份）
  runs/<run_id>/steady/                   1.25 与 0.625 两个正式输出目录
  audits/<audit_id>/<case>/<mode>/        三个零步输出目录

CASE/unseen_v2_reference_checker_S4_tge_server_v1/
  analysis/server_stage.py                身份/计划/血缘/封存校验
  analysis/zero_evidence_server.py        零步输出与读回校验
  analysis/check_zero_server.py           事后独立复核
  analysis/read_fields.py                 原样沿用本机读取器（未改一字）
  analysis/evidence.py                    原样沿用
  tests/test_preparation.py               15 项软件检查
```

## 7. 科学状态（不得升级）

`NUMERICAL_GATE=NOT_EVALUATED`、`RESULT_PASS=false`、`geometry_PASS=null`、`reference_qualified=false`、`original_S4_stage_accepted=false`、`MODEL_COMPARISON`/`physical_validation=NOT_EVALUATED`、`submission_ready=false`、`next_stage_started=false`。

原 S4 六条 per-run 接受、沿槽 P 网格 PASS、**横槽 T 中细差 1.328387035% > 1% FAIL** 一律保留，不得改写。

## 8. 执行边界

- `AI_may_start_solver=false`、`user_manually_starts=true`。
- 零步入口在创建任何文件或子进程之前，要求一份**独立的新授权**（`AUTHORIZED_S4_TGE_SERVER_ZERO_RELEASE`，固定文件名）+ 已采用的资源决策。
- 准备文档本身不能启动零步分支：`validate_zero_authority` 会因 kind 不符直接拒绝（15 项检查里的第 13 项就在测这个）。
- 正式预算（`formal_solver_wall_cap_seconds` / `formal_checker_cap_seconds`）保持 `null`，等 1.25 重跑给出实测吞吐后再定。
