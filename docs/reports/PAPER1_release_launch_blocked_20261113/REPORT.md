# 启动闸门核查：冻结发布在两台机器上都已无法启动（2026-11-13 23:40）

> 起因：用户指示"不用写进老师选项，直接跑 h125/d120 横槽（fine→tight）"。
> 核查结论：**启动不了**，而且不是排期问题——冻结发布的启动自检 `verify_release()` 在两台机器上都过不去；即使过了，h125T fine 在本机也跑不完。
> 本轮**未启动任何仿真、未修改任何冻结件、未生成任何回执**。

## 0. 一句话

冻结发布把"机器相关的二进制"（本机自编译的 OpenFOAM + 系统 libc/libm）写进了指纹；今天 12:21:59 一次系统更新换掉了 libc，本机因此锁死；服务器是另一份编译，天生不符。而 h125T fine 实测需要约 131278 轮，本机要 49 h、服务器要 12.7 h，协议留给它的上限是 12 h 且明文禁止加时。

## 1. 本机：今天的系统更新把指纹改掉了

实测（`source /opt/openfoam13/etc/bashrc` 后直接调用 `run_one.verify_release()`）：

```
VERIFY_FAIL -> OpenFOAM library drift: /usr/lib/x86_64-linux-gnu/libc.so.6
```

证据：

| 项 | 值 |
|---|---|
| 冻结清单写入时间 | 2026-11-12 21:16（`release_manifest.json` mtime） |
| `libc.so.6` inode 变更时刻（ctime） | **2026-11-13 12:21:59** |
| `libm.so.6` inode 变更时刻（ctime） | **2026-11-13 12:21:59** |
| 当前 glibc | 2.39-0ubuntu8.12（包内 mtime 2026-11-06 01:18，≠ 安装时间） |
| 清单记录 vs 当前 | libc `3a15d668…` vs `755a371e…`；libm `fce00b6f…` vs `5dcc4d25…` |
| 其余外部项 | 23 项中 21 项一致，仅这 2 项不符 |
| 内部项 | 212 项**全部一致**（0 不符） |

**影响面不是 h125T，是整个项目**：自今日 12:22 起，本机任何 `run_one.py --execute` 都会在写任何文件之前退出（`verify_release()` 在 `main()` 里位于 `mkdir` 之前），因此**无法再产生任何合规运行**。

**已接受的参考不受影响**：23 份回执的 `source_manifest_sha256` 仍等于当前清单摘要（`97ae55ff9dba…`），22 个 `LOCAL_CHECKS_PASS` 照旧成立。被挡住的只有"新启动"。

`/var/log/apt/history.log`、`/var/log/dpkg.log` 在本机不可读（文件不存在），故无法给出包名与操作者；但 ctime 与哈希双重证据足以定位到"11-13 12:21:59 系统库被替换"。

## 2. 服务器：指纹天生不符，且缺 prepared 树

服务器 `10.103.103.63` 上的 `~/SIM240/transfer/paper1_fvm_stokes_reference_v2/`：

| 项 | 结果 |
|---|---|
| 内部 212 项 | **内容差异 0**；缺失 196 项（全部是 `prepared/**` 与 `.gitignore`） |
| 外部 23 项 | 缺失 0，**不符 10 项**：`blockMesh`、`checkMesh`、`mapFields`、`libOpenFOAM.so`、`libfileFormats.so`、`libfiniteVolume.so`、`libmeshTools.so`、`libsurfMesh.so`、`libtriSurface.so`、`openmpi-system/libPstream.so` |
| glibc | 服务器 2.39-0ubuntu8.9（mtime 2026-09-03），本机 8.12 |
| `formal_review_status` | 服务器清单为 `ASTRA_FINAL_STATIC_RECHECK_COMPLETE`（是拷贝来的本机清单） |

原因很直接：外部表是按**冻结那台机器**的 `ldd` 结果与文件内容生成的，服务器的 OpenFOAM 是**另一份编译**、glibc 也是另一个补丁级，因此物理上不可能同哈希。

推论（重要）：**这份发布只能在冻结它的那台机器上启动**；而资源上限又是按服务器级速度定的。两个条件无法同时满足 —— 这是设计层面的冲突，不是操作失误。

## 3. 即使自检通过，本机也跑不完 h125T fine

| 量 | 数值 | 依据 |
|---|---:|---|
| fine 从 mid 末态到收敛所需轮数 | 131278.5 | 原运行日志 `converged in 131278.5 iterations`（本地 0→31900.5 + 服务器 31900.5→131278.5） |
| 本机速率下界 | ≥1.354 s/轮 | 本地 43200 s 墙钟只推进 31900.5 轮 |
| 本机需要 | **≥49 h** | 131278.5 × 1.354 s |
| 服务器实测速率 | 0.349 s/轮 | 99378 轮 / 34653 s（**当时还并行跑着 h25T**，独占可能更快） |
| 服务器需要 | **≈12.7 h** | 131278.5 × 0.349 s |
| 协议 fine 墙钟上限 | **43200 s（12 h）** | `PROTOCOL.md` §3.1 |
| 协议对超时的规定 | **"墙钟或异常退出拒收，不自动增配"** | `PROTOCOL.md` §3.1；§运行器条款重复"不自动增配" |

即：**本机超 4 倍，服务器超 6%，两边都不在预算内。** §3.1 自己写着"tight 有先触墙钟的风险"，h125/d120 正是这个风险的实证。

tight 更没底：它**从未进到求解器**。本机 `h125_d120_T_tight/runtime/` 只有 2026-11-12 16:24 的一次启动残迹——`log.blockMesh`、`log.checkMesh`（含 `Mesh OK`）、`release_snapshot.json`、`started.json`，其中 `commands` 为空、没有 `log.solver`、没有回执，冻结评估记 `RUN_INCOMPLETE`；服务器侧该目录更只有 `0/ constant/ system/ case.json`。它还需要把 Uz 从 6.95e-11 压到 1e-11（约 7 倍），同样受 43200 s 上限。

附带一个操作细节：因为本机 tight 目录里已经有 `runtime/`，`run_one.py` 会以 `previous evidence exists; no overwrite, resume or retry is authorized` 拒绝启动——**即使指纹问题解决，也必须先有该算例的干净副本**。

## 4. 重冻结不是"改个哈希"：会把 23 份回执全部孤儿化

`postprocess.py:229-232` 原文要求：

```python
if receipt.get('source_manifest_sha256')!=release_sha or receipt.get('executable_sha256')!=executable_sha:
    problems.append('receipt does not match the frozen release and executable')
```

因此一旦换清单摘要：

1. 22 个已通过参考的 `read_case` 全部转为"回执与冻结发布不符"；
2. `run_one.py` 启动前会因 `both current-release flat controls must pass before grooves` 或 `seed source fails independent readback` 直接拒；
3. 要让链重新可用，必须在**新发布**下重跑两块平板 + 各方向各层 —— 不是补一条 tie。

而平板 T 在本机也过不了：解析一致需要约 40000 步，3600 s 上限只够约 6000 步（历史记录 6000 步 −8.943434%，40000 步 +0.013878%）。

**所以"重冻结 + 补跑"实际等于"整链重做"，且必须先有一台能同时满足指纹与墙钟的机器。**

## 5. 只剩三条路（都需人批，我不自行选）

| 方案 | 内容 | 代价 | 需要谁点头 |
|---|---|---|---|
| **A. 出新发布 v2.3** | 外部指纹按"选定执行机"重建；明确 v2.2 的 22 条参考作祖父条款；fine/tight 墙钟是否调整一并裁定 | 需 Astra 批；祖父条款现行代码不支持；调整墙钟需改 `case.json`（属冻结件的正当变更时点） | Astra + 老师 |
| **B. 判结构性拒收** | h125T 无独立参考（§3.1 预警的墙钟风险落地），论文明写该方向无参考、相应主张降一档 | 零算力；横槽合格参考仍只有 h75/d100 一个 | 老师（覆盖口径） |
| **C. 钉死执行环境** | 用容器/固定镜像把 glibc 与 OpenFOAM 固化，在镜像内重冻结并重跑 | 治本，但等于换执行栈，历史参考需在新镜像下重验 | Astra + 老师 |

**我的判断（供参考，不代替决定）**：A 与 C 都要动发布谱系，纸面上最稳的是 B——h125T 缺参考这件事本来就可以如实写成"预算内未取得"，不必为了 6% 的墙钟差去换一次发布身份。若老师坚持要第二组成对主值，则 A 的成本必须接受"整链重跑"。

## 6. 本轮红线执行情况

- 未启动任何仿真；未在服务器或本机创建 `runtime/`、未写 `receipt.json`、未填 `FVM_CLAIM_EVIDENCE.csv`
- 未修改 `release_manifest.json`、`prepared_manifest.json`、任何 `case.json` / `controlDict` / `*.py`
- 未回滚 glibc（回滚系统库风险高于收益，且属环境变更，须批）
- 未改动任何历史 FAIL、旧 36 条统计、三项目级 `false`

## 7. 现在可以立刻做的（不需要等任何人）

1. 把本节结论并入给老师的确认稿（h125 那条从"要 10 小时"改成"当前无法启动 + 两条路"）。
2. 若老师选 B，只需在趋势报告与确认稿里把 h125T 固定为"预算内未取得"，不产生任何新数字。
3. 若老师选 A/C，我可以先把变更清单与偏离申报稿写好（不动冻结件），等 Astra 批了再执行冻结动作。
