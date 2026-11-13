# h125/d120 横槽：接收链核查与「能否补完」的结论

建档：2026-11-13 14:25。性质：**只读核查。本轮没有补任何回执，也没有生成任何冒充运行记录的哈希绑定。**

**先给结论：这条接收链不能用文档补完。** 我此前向用户建议"补回执、写续跑说明，就能让横槽合格参考从 1 个变 2 个"——**这个说法是错的**，原因有三个，且第三个是决定性的。

**没有启动、停止、续跑任何仿真；没有修改母稿、系数、门槛或历史 FAIL；没有授予任何参考资格。**

---

## 1 为什么"补回执"这个动作本身不成立

冻结验收器 `read_case()`（`postprocess.py:197`）对回执的要求不是"有一个 `receipt.json` 文件"，而是**一组只能由求解进程在运行当时写入的绑定**：

| 回执字段 | 用途 | 能否事后重建 |
|---|---|---|
| `run_id` | 运行身份 | 否——事后编号不构成身份 |
| `independent_exit_code` | 独立退出码 | 否——须由包装器在进程退出的那一刻读取 |
| `solver_converged` | 稳态判据是否达到 | 部分（可从日志推断，但不是原始证据） |
| `evidence_sha256` | 证据文件指纹 | 能算，但**算出来只是"我此刻看到的文件"，不是"运行当时输出的文件"** |
| `source_manifest_sha256` / `executable_sha256` | 与冻结 release 和二进制绑定 | 否——事后写入等于声称"当时用的是这个"，无法证明 |
| `release_unchanged` / `disk_budget_met` | 运行期 release 与磁盘检查 | 否——这是运行时的检查结果 |
| `runtime_logs_sha256` | 六个运行记录文件的指纹 | 否 |
| `native_field_sha256` | 末态场逐文件指纹 | 否 |
| `mesh_sha256` | 网格五文件指纹 | 否 |

`postprocess.py:211` 原文写得很直接：**"A CSV and a normal solver End are insufficient runtime provenance."**（只有 CSV 和正常的 `End` 输出，不构成运行溯源。）

这行注释就是为这种情况写的。我如果自己造一份 `receipt.json`、把当前文件的哈希填进去，**做的正是这条注释要防的事**：把"事后清点"伪装成"运行当时留证"。所以本项目不做这个动作——这跟"不给好看的 K"是同一条红线。

## 2 服务器产物实际缺什么

服务器 `~/SIM240/transfer/run/prepared/h125_d120_T_fine/` 现有：

```
0/  0.5/  31900.5/  131278.5/      ← 末态场齐全（U, p, phi, uniform）
case.json  constant/polyMesh/      ← 网格五文件齐全
referenceEvidence/cells.csv        ← 95 MB，齐全
referenceEvidence/x_faces.csv      ← 31 MB，齐全
```

缺的：

- `referenceEvidence/receipt.json` —— **无**
- `runtime/` 整个目录 —— **不存在**（没有 log.blockMesh / log.checkMesh / log.solver / resource.txt / exit_code.txt / release_snapshot.json）
- 日志实际散落在 `~/SIM240/transfer/logs/h125f.{blockMesh,checkMesh,solver,status}`，**在算例目录之外**，且 `status` 只是包装脚本写的两行 `solver exit=0`，不是求解器产出的回执
- 全树 `find -name "receipt*.json" -o -name "exit_code.txt"` **零命中**

也就是说：**服务器这次运行没有走协议化的运行包装**。它是"手工起、日志重定向到别处、算完写证据"的做法。数值是真的，溯源是缺的。

## 3 决定性阻塞：tight 从未运行

这一条比回执更硬。`assess()`（`postprocess.py:328-331`）要求：

```python
if flat_ok and all(r['status']=='LOCAL_CHECKS_PASS' for r in group):   # group = coarse/mid/fine/tight
    k1,k2,k3,kt = [...]
    reference_ok = d21<=1 and d32<=.5 and (d32<=d21 or max(d21,d32)<=.05) and alg<=.05
```

`alg = |K_tight/K_fine − 1|`。**没有 tight，`alg` 无法计算，`reference_ok` 永远不成立。**

核查结果（以冻结 `current_fvm_v21_assessment.json` 为准）：

| 档 | 状态 | 证据 |
|---|---|---|
| coarse | `LOCAL_CHECKS_PASS`，K=1.8401354e-22 | 本地 `referenceEvidence/` |
| mid | `LOCAL_CHECKS_PASS`，K=1.8380637e-22 | 本地 `referenceEvidence/` |
| fine | 冻结评估记 **`EXECUTION_FAILED_OR_NO_EVIDENCE`**（指本地 exit 124 那次）；服务器续跑另有一套无溯源证据 | 本地 receipt 记超时；服务器仅 CSV |
| **tight** | 冻结评估记 **`RUN_INCOMPLETE`**；实际目录只有 `0/ constant/ system/ case.json`，**无 `runtime/`、无 `referenceEvidence/`** | 服务器 `h125_d120_T_tight` |

所以即使回执问题神奇地解决了，**h125 横槽依然不可能取得参考资格，因为最后一档没跑。**

所以即使回执问题神奇地解决了，**h125 横槽依然不可能取得参考资格，因为最后一档没跑。**

## 4 我上一条错在哪

我说了三句话，其中两句不成立：

| 我说过 | 实际 |
|---|---|
| "补回执 + 写续跑说明就能验收" | ✗ 回执不可事后重建（§1），且 tight 未跑（§3） |
| "做完后横槽合格参考从 1 个变 2 个" | ✗ 至少还需要一次 fine 重跑 + 一次 tight 运行 |
| "数值上过了，只是手续没走完" | ✗ 手续不是"补"而是"重做"，因为 provenance 只能运行当时产生 |

第三句错得最要紧：**"手续没走完"听起来像补个章，"provenance 不能事后补"才是实情。** 这两者对工期和老师决策的含义完全不同。

## 5 真要拿到 h125 横槽参考，实际要付什么

order 必须是 fine 在前、tight 在后（tight 的 `seed_from = h125_d120_T_fine`、`seed_time = 0.5`）。

1. **fine 重跑，带完整运行包装**（产出 `runtime/` 六件套 + `referenceEvidence/receipt.json`）
   - 网格 dx = 0.3125 nm、454656 单元，判据 `{p,U,v} ≤ 1e-10`。
   - 上次服务器从 31900.5 起跑了 9 h 37 m；从 0.5 起跑全程按同速率估计约 **10–11 h**（估算，不是承诺）。
   - 不能省：splice 轨迹本身也违反协议（`case.json` 的 `seed_time=0.5` 要求从 0.5 起，不是从 31900.5 起）。
2. **tight 运行**（同网格，判据收紧到 1e-11）
   - 这是唯一未知量。fine 末轮 Ux 9.9996e-11、Uz 6.950e-11、p 1.005e-12；要到 1e-11，Uz 还需压约 7 倍。
   - 这一档正是之前担心"残差地板"的地方。本轮**不下结论**：fine 的残差在末段仍单调下降，与慢收敛相容；但**没有任何实测支持"一定能到 1e-11"**，也不能说"一定到不了"。
   - 墙钟上限 43200 s（12 h）。跑满未达标即 exit 124，又是无回执的一次。
3. 两档都过，才轮到 `alg ≤ 0.05%` 与四档齐全，`assess()` 才可能给出 PASS/FAIL。

**保守口径：h125 横槽不是"补一份文档"，而是"约 10 h + 一次不确定时长的运行，且要用协议化包装重跑"。** 这个成本必须进覆盖决策，不能当成白捡的第二个横槽。

## 6 对覆盖决策的修正

发给老师的确认稿里，我写过"若这条能落地，横槽会有第二个合格参考"。**这句要改成有条件的成本陈述**：

- 现有横槽：**1 个**（h75/d100，一致性 FAIL，但资格合格，可作有效比较）。
- h125 横槽：目前 **0 个**（不可用）。要变成 1 个，需要重跑 fine 并新跑 tight。
- **h50/d120 横槽也不便宜**：它在冻结六方向里**根本没有算例目录**（P 方向四档齐全已合格，T 方向需从 coarse 起建四档）。
- 两者对比（必须说清，否则补算会选错）：

| | h125/d120 T | h50/d120 T |
|---|---|---|
| coarse | 已有，`LOCAL_CHECKS_PASS` | **无，需新建** |
| mid | 已有，`LOCAL_CHECKS_PASS` | **无，需新建** |
| fine | 数值已算完但溯源不足，**需带包装重跑（约 10 h）** | **无，需新建** |
| tight | **从未运行（时长未知，Uz 需再压约 7 倍）** | **无，需新建** |
| 额外风险 | 深槽慢收敛，tight 可能跑满 12 h 未达标 | 需先过判据可达性验证 |

⇒ 结论修正：**"救 h125"不是最便宜的路，但也未必比"新建 h50 T"贵**——前者省了 coarse/mid 两档，代价是深槽 tight 的不确定性；后者是干净的新建四档。这个取舍应由老师定，不由我替他选。

在本轮核查前，我把 h125 横槽说得像"差一份手续"；实际上它和工作量最小的候选点不在同一量级。

## 7 本轮做了什么、没做什么

- **做了**：只读核查两台机器的实际产物、冻结验收器对回执的逐项要求、tight 是否存在；把结论落成这份报告。
- **没做**：没有生成 `receipt.json`；没有把外部日志拷进 `runtime/` 伪装成运行记录；没有为 h125 填 delta 或各向异性比；没有启动任何运行。
- `FVM_CLAIM_EVIDENCE.csv` 中 h125/d120 T 仍为 **NA**，不变。
- 历史 FAIL、旧 36 条统计、三项目级 `false` 均不变。

## 8 如果仍要推进，合法路径只有一条

按协议在服务器上**重新跑 fine（带运行包装）**，再跑 tight。这是唯一能让 h125 横槽拿到资格的路，且必须由用户授权、先定协议、单独启动。

**在那之前，任何"h125 横槽已通过三项数值门槛"的说法，都只能写成"离线复算显示数值自洽，但运行溯源不足、tight 未跑，故不构成参考资格"。** 本报告与 `PAPER1_h125T_server_recheck_20261113/REPORT.md` 的 `NUMERICALLY_CONSISTENT_BUT_NOT_QUALIFIED` 一致，后者仍然有效，只是现在知道"补齐"这步不存在。
