# 10.103.103.63 部署记录（yuanyuan 账号）— 更正版

时间：2026-11-11 21:43–21:59（+08:00）。主机 `jn-Super-Server`（`10.103.103.63`）。
**账号更正：本轮部署使用 `yuanyuan`（uid 1001），不是 `jn`（uid 1000）。先前写入 `/home/jn` 的那次属放错位置，见 §6。**
**范围：只做部署与配置一致性验证。未启动任何物理计算、未新建正式准备、未跑零步审计、未改任何科学阈值。**

## 0. 结论

**部署完成，跨机器配置一致性验证通过（18 个字段逐位相同）。`yuanyuan` 账号现具备跑本算例的全部条件。**

| 项目 | 结果 |
|---|---|
| 登录方式 | `yuanyuan@10.103.103.63`，**已装公钥、免密可用** |
| OpenLB 提交 | `882924a9cfc8`（与本机、与 102.55 一致） |
| 算例源码 5 文件 SHA256 | 与本机**逐个相同**（§3） |
| 服务器 ELF | `a168ec7ad5816af9e430a6c82cfa84e5355a33c091f8f7334da04d84a4b9c8bf` |
| 本机 ELF | `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b` |
| 动态库缺失 | **0 个** |
| describe 配置比对 | **18 字段逐位相同**（`diff` 无输出） |
| 磁盘剩余 | 705 GB（`/home` 与 `/` 同一分区） |

ELF 指纹与本机不同属**预期**：`-march=native` 绑死 CPU 架构（本机 i7-13700 vs 服务器 EPYC 7B13），且 `OLB_ROOT` 路径串被编入二进制。这不代表算例逻辑变了——配置比对已证明这点。

## 1. 账号情况（重要）

`10.103.103.63` 上**有两个账号**，此前误判为只有 `jn`：

| 账号 | uid | 组 | shell | 家目录 | sudo |
|---|---|---|---|---|---|
| `jn` | 1000 | jn, adm, cdrom, sudo, … | zsh | `/home/jn`（56 项） | **属于 sudo 组**（但 `sudo -n` 需密码） |
| **`yuanyuan`** | **1001** | **yuanyuan, users** | bash | `/home/yuanyuan`（16 项） | **无** |

- **`jn_personal` 既不是账号也不是目录**：`getent passwd` 无此条目，`find /home -maxdepth 2 -name "*jn_personal*"` 无结果。
- `yuanyuan` 最初公钥被拒（`Permission denied (publickey,password)`）；用密码 `123` 可登录，随后已把本机公钥写入 `~/.ssh/authorized_keys`（原 1 条 → 现 2 条，已用 `grep -qF` 去重）。
- 免密验证：`PASSWORDLESS_OK`。
- **注意**：`yuanyuan` 不在 `sudo` 组。当前一切都在家目录，不需要管理员权限；将来若要装系统级依赖会受阻。

## 2. 传输与编译

| 步骤 | 命令 / 方式 | 结果 |
|---|---|---|
| 传 OpenLB | `rsync -a` 排除 `*.o *.d *.a build/ examples/ doc/ tests/ *.bak` | 24 MB，**2.2 秒** |
| 编译依赖+核心 | `make dependencies -j4 && make core -j4` | **EXIT=0** |
| 传算例源码 | `rsync -a` 排除 `*.o *.d` | 68 KB |
| 编译算例 | `make OLB_ROOT=/home/yuanyuan/openlb` | 通过 |

**为什么必须排除编译产物**：102.55 首次部署时曾把本机 GCC 13.3 编出的 `.o` 传到 GCC 11.4 的服务器，`make` 误判「已编译」直接链接，报 `undefined reference to std::_M_replace_cold`。本次传完即验证服务器上 `*.o/*.d/*.a` 数量为 **0**，从源头避免「假编译」。

**未改任何源文件**：`src/Makefile` 里是 `OLB_ROOT ?= /home/dell/openlb`，用 `make OLB_ROOT=...` 覆盖即可。

## 3. 源码哈希核对

`~/SIM240/CASE/unseen_v2_reference_S1_a1_yy_v1/src/`：

```
90fffcf7ef369f38c4a412d28dcd2bc12e85e061658d517d53719db46e10182c  urv_reference.cpp
0ee76b75e1413c145866a4af561387b8e68cbbc43d3814fd41c8a3bbf71f150f  capture_schedule.h
178b0e1b80d4323414b3d2d75642fbd8475143e1172882fb4f2411b7aa99a889  mass_stats.h
560c5e0a55c16ead6a72d6009c3dcafb9813ca661b180dd03c18475e319f473f  mrp_observer.h
a9c8c75fb796a1611eae4e5934330c30b5280d0afeb9c6e7edb58f2799b57c9c  Makefile
```

与本机 `CASE/unseen_v2_reference_S1_a1_v1/src/` **逐个相同**，也与 102.55 在 20261104 跑通时的记录相同。⇒ 三台机器跑的是同一份算例代码。

## 4. 配置一致性验证（describe）

方法：同一份 `run_config.txt`（`direction=P, dx_nm=1.25, h_nm=30, d_nm=0, w_nm=120, period_nm=240, Ly_nm=240`），只改 `output_directory`，两边各跑 `mode=describe`（**不分配晶格、0 时间步**），比对 `effective_config.txt`。

结果：`diff` **无输出**，20 行（18 个有效字段 + `run_id`/`mode`）逐位相同，包括：

| 字段 | 值 |
|---|---|
| `dx_m` | 1.25e-09 |
| `dt_s` | 2.6041666666666668e-13 |
| `nx`, `ny` | 192, 192 |
| `Lx_m`, `Ly_m` | 2.4000000000000003e-07 |
| `h_m` | 3.0000000000000004e-08 |
| `phi` | 0.5 |
| `nominal_volume_m3` | 1.7280000000000007e-21 |
| `plan_area_m2` | 5.7600000000000015e-14 |
| `window_steps` | 2592 |
| `maximum_steps` | 27648 |

**这证明什么**：几何换算、时间步换算、统计窗设计在两种 CPU 架构上完全一致，编译环境没有引入差异。
**这不证明什么**：`describe` 不建晶格、不做浮点迭代 ⇒ **未**证明浮点运算路径一致、**未**测内存峰值、**未**验证任何物理量。真正的一致性要等零步审计（precheck/initialize）与一次实际算例的 K 值比对。

## 5. 机器规格

| | 103.63 | 102.55 | 用户本机 |
|---|---|---|---|
| CPU | AMD EPYC **7B13** 64C ×2 = 128 线程 | EPYC 9B14 96 线程 | i7-13700 24 线程 |
| 内存 | **503 GB（可用 493 GB）** | 188 GB（可用 129 GB） | 31 GB（可用 17 GB） |
| 磁盘 | 1.9 TB，空 705 GB | 916 GB，空 418 GB | — |
| 部署时负载 | **0.2** | 102（jj 的 Fluent 占满） | 2.2 |
| 编译器 | gcc 13.3.0 | gcc 11.4.0 | gcc 13.3.0 |
| 时区 | **America/New_York（-0500，比北京慢 13 h）** | 北京 | 北京 |

> **时区提醒**：该机时间戳是美东时间，换算北京时间要 **+13 小时**。例如服务器显示 `Nov 11 08:55`，对应北京 `21:55`。

## 6. `/home/jn` 下的旧部署（待清理）

先前误用 `jn` 账号，在 `/home/jn` 留下：

- `~/openlb`（52 MB，已编译）
- `~/SIM240/CASE/unseen_v2_reference_S1_a1_jn_v1`（含已编译二进制 `083bc57b…`）
- `~/xcmp_desc`（describe 验证残留）
- `~/openlb_build.log`

**未删除**——这是他人账号的目录，需用户明确同意后才清理。这些文件约 58 MB，留在那里不影响任何东西。

另：`/home/jn/SIM240/CASE/unseen_v2_reference_S4_tge_jn_v1`（11-05 建立，**非本次创建**）只有 `precheck` 日志与 `steady` 的配置文件，**无 `result_summary.csv`、无 `completion.json`、无 `src/`** ⇒ 11-05 那次 0.625 nm 只做到 precheck 就停了，从未跑完。本次未动该目录。

## 7. 现在能做什么 / 还不能做什么

**已具备**：编译环境、算例可执行、与本机一致的源码、705 GB 磁盘、493 GB 可用内存、128 个空闲核、免密登录。

**未做（需单独授权）**：
1. 新建服务器版正式准备（新 `release_sha256`、输入清单、`build_environment.json`）
2. 零步审计（describe / precheck / initialize + 读场）
3. 性能标定（实测步/秒与峰值内存）
4. 任何正式算例（含 0.625 nm）

**注意**：内存充足**不等于**更快。本算例代码写死单 MPI 进程，128 核只能用 1 个；墙钟取决于单核性能与机器是否被抢占。103.63 当前负载 0.2 是难得的空窗，但**这是共享机器，正式长算前仍应确认使用规矩**。

## 8. 遗留问题

1. **时区差 13 小时**，所有时间戳判断必须换算。
2. **GPU 驱动坏**（`nvidia-smi` 报 `couldn't communicate with the NVIDIA driver`）。本项目纯 CPU，无影响。
3. **OpenLB 版本串显示 `882924a-dirty`**：因排除了 `examples/doc/tests`，`git describe --dirty` 认为文件缺失。算例自身的 `-DOLB_VERSION` 用 `git rev-parse --short=12 HEAD` 生成，仍为 `882924a9cfc8`，与 102.55 一致，**不影响任何数值**。严格来源封存时需在清单注明「dirty 的原因是排除目录」。
4. **`yuanyuan` 无 sudo**：当前不需要，将来装系统包会受阻。
5. **密码仍为 `123`**：共享机器上强度过低，建议改强密码。免密已可用，改密码不影响本流程。
