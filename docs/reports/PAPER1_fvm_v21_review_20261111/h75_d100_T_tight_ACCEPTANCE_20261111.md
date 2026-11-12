# h75_d100_T_tight 独立验收（2b 层 · 代数误差闭环）

- 建档：2026-11-11 22:40（CST）
- 验收对象：`CASE/paper1_fvm_stokes_reference_v2/prepared/h75_d100_T_tight`
- 验收人：外部独立读回，只用 `postprocess.py` 的 `read_case` / `assess`，不以求解器自报为凭
- 结论：**`LOCAL_CHECKS_PASS`，2b 层通过，`reference_accepted = true`，`h75_d100_T` 正式判 `FAIL`（delta = +2.5110% > 2%）**

---

## 1. 运行身份

| 项 | 值 |
|---|---|
| run_id | `h75_d100_T_tight_20261111T212636_3f1bf954` |
| 启动 | 2026-11-11 21:26:36 |
| 停止 | 2026-11-11 22:34:17 |
| 墙钟 | **4,053 s**（1 h 7 min；上限 43,200 s，用 9.4%） |
| 独立退出码 | `0` |
| 迭代步数 | **26,340.5** |
| `actual_stop_reason` | `native_convergence`（**非** iteration_cap） |
| `post_hoc_acceptance` | `accepted` |
| `flat_exception_used` | `False` |
| 种子 | `h75_d100_T_fine` 末时刻 `65970.5` → 映射至 `0.5`，`map_exit_code=0` |
| 源 run_id | `h75_d100_T_fine_20261111T172454_09d491e9` |
| 磁盘 | 270,065,045 B，`disk_budget_met = true` |

末次残差（三重全部达标，门槛 `1e-11`）：

| 分量 | 初残差 | 判定 |
|---|---|---|
| Ux | `9.9991774526396363e-12` | < 1e-11 ✓ |
| Uz | `7.4319982338434457e-12` | < 1e-11 ✓ |
| p | `8.2949873262314988e-14` | < 1e-11 ✓ |

三档残差门槛对比：fine 要求 `1e-10`，tight 要求 `1e-11`，实测 tight 的 Ux 比 fine 的门槛还低一个量级。

## 2. 唯一差异确认

tight 与 fine 的网格、几何、离散格式、边界条件、松弛因子完全相同，**只有两处数值设定不同**：

| 设定 | fine | tight |
|---|---|---|
| `solvers.{v,U,p}.tolerance`（线性容差） | `1e-12` | `1e-13` |
| `SIMPLE.residualControl {p, U}`（残差判据） | `1e-10` | `1e-11` |

`dx_nm = 0.3125`、`expected_cells = 307200`、`ΣV = 3.0000000000000006e-23` 两侧逐位相同。因此 `K_tight` 与 `K_fine` 的差**只能归因于迭代误差**，不可能含离散误差成分。

## 3. 2b 层核心判据

```
K_fine  = 4.3400416630474742e-23 m³
K_tight = 4.3400348250152633e-23 m³
|K_tight/K_fine − 1| = 1.575568e-06 = 0.00015756%
门槛                  = 0.05%
判定                  = PASS（余量 317 倍）
```

**这个数字的含义**：fine 的 K 里，"没解干净"造成的成分只有 **0.00016%**。也就是说 fine 的停手条件（`1e-10`）虽然看起来宽松，但实际残留对 K 的污染小到可以忽略——因为它停在 65,970.5 步时，残差已从 `1e-10` 自然衰减到 `9.998992e-11`，且在此之前已经历了数万步的平滑下降，累积误差没有滞留。

**对 `d32` 的归因分解**：`d32 = 0.082585%` 中，迭代误差只占 `0.00015756 / 0.082585 = 0.19%`，**其余 99.81% 是真正的离散误差**。这坐实了把 `d32` 当作"网格不够细"的度量是站得住的。

## 4. 收敛性与物理自洽（`read_case` 全部通过，`issues = []`）

| 检查 | 实测 | 门槛 |
|---|---|---|
| 功率收支 `|耗散/驱动功率 − 1|` | **0.066068%** | ≤ 0.1% ✓ |
| 截面通量极差 | `1.889e-12%` | ≤ 0.1% ✓ |
| 面通量 vs 体输运 | `3.286e-05%` | ≤ 0.1% ✓ |
| `ΣV` vs 冻结几何体积 | 相对差 < 1e-10 | 硬闸 ✓ |
| 网格 `checkMesh` | `Mesh OK.` | 硬闸 ✓ |
| 回执哈希绑定（2 CSV + 3 场 + 5 网格 + 6 日志） | 全部相符 | 硬闸 ✓ |

**功率收支的三档递减**（跨算例的独立证据，与 2b 层无关但同向）：coarse `0.354743%` → mid `0.149708%` → fine `0.065910%` → tight `0.066068%`。fine 与 tight 相差 `0.0002` 个百分点，说明这一项也已饱和。

`K_tight = 4.3400348250152633e-23`，`J = 4.340034825015264e-12`，`κ = 3.47203e-16`，`Href = 1.25e-7`。

## 5. 正式判定（`assess()` 输出，未经改写）

```json
{
  "point": "h75_d100_T",
  "status": "FAIL",
  "grid_mid_coarse_percent": 0.194278708111717,
  "grid_fine_mid_percent": 0.08258503193038225,
  "algebraic_change_percent": 0.00015755683335783033,
  "reference_accepted": true,
  "delta_K_percent": 2.5110440511747933,
  "Kref_m3": 4.340041663047474e-23,
  "LC_error_percent": 50.186548651859944,
  "V2_error_percent": 4.925148722420958,
  "V2_improved": true
}
```

四项判据逐条：

| 判据 | 门槛 | 实测 | 结果 |
|---|---|---|---|
| `d21`（mid vs coarse） | ≤ 1% | 0.194279% | ✓ |
| `d32`（fine vs mid） | ≤ 0.5% | 0.082585% | ✓ |
| 递减规则 `d32 ≤ d21` | 是 | 0.0826% ≤ 0.1943% | ✓ |
| 代数变化 `alg`（2b 层） | ≤ 0.05% | 0.000158% | ✓ |
| **`delta`（fine vs OpenLB）** | **≤ 2%** | **2.511044%** | **✗ FAIL** |

`reference_accepted = true` 意味着**参考值资格成立**——上限误差已由 2 层（`0.0827%` 保守）与 2b 层（`0.00016%`）双重封顶。因此这次 `FAIL` 是**在参考可信的前提下**判出的，不是"比不了"。

## 6. 结论的科学含义

**`delta = +2.5110%`：在 `h75 / d100 / 沿槽` 这一几何-方向上，5 nm 网格的 OpenLB 记录值比 0.3125 nm 的 FVM 参考值高 2.51%，超过协议规定的 2% 门槛。**

三角不等式下界（把参考自身误差扣掉之后，OpenLB 的偏差不可能小于）：

```
2.5110% − 0.0827% = 2.4283%      （用保守上界 0.082653%）
2.5110% − 0.0609% = 2.4501%      （用等比估计 0.060907%）
2.5110% − 0.0002% = 2.5109%      （若只扣 2b 层迭代误差）
```

即 OpenLB 偏离真值**至少 2.43%**，无论参考取哪个误差估计。这个下界比"差 2.51%"更强，因为它排除了"差异来自参考自身不准"这一可能。

**`delta` 对取法的稳健性**（四个候选 K_FVM 全部超限）：

| 作参考的 K | delta |
|---|---|
| coarse | +2.2274% |
| mid | +2.4264% |
| **fine（官方口径，`postprocess.py:336` 写死 `Kref_m3=k3`）** | **+2.5110%** |
| Richardson 外推 | +2.5735% |

最松的取法（coarse）也有 2.23%，结论不依赖取法。

**同时给出的两个模型误差**（同一参考值）：

- 原式（LC）：`50.1865%`
- V2：`4.9251%`
- `V2_improved = true`

## 7. 边界与未完成事项

1. **本结论只覆盖 1 个点**：`h75_d100_T`。其余 5 个点（`h75_d100_P`、`h25_d100_T`、`h50_d120_P`、`h125_d120_P`、`h125_d120_T`）全部 `NOT_EXECUTED`，`assess()` 顶层 `status = INCOMPLETE`、`execution_status = PARTIAL`、`comparison_evaluable = false`、`scientific_gate = NOT_A_GLOBAL_REFERENCE_QUALIFICATION`。
2. **不得**把本点的 `FAIL` 外推到其他几何或方向，也不得据此改稿。
3. **不得**因本点 `FAIL` 而修改判据、重跑 fine 或重新选 `Kref`。失败不改口径是既定原则（`run_one.py:170` 禁覆盖/续跑/重试）。
4. 其余 5 个点的 tight 均未启动；每个点的 tight 成本约 4,000 s（本点实测），低于 fine 的 12,764 s。
5. `8.94%` 一类历史数字与本次 `2.51%` **不可混用**：前者是 v1 平板 T 未收敛近似的偏差，后者是沟槽真实的求解器间差异。

---

## 附：本轮验收的命令口径（可复现）

```python
import importlib.util, pathlib, hashlib
R = pathlib.Path('CASE/paper1_fvm_stokes_reference_v2').resolve()
spec = importlib.util.spec_from_file_location('pp', R/'postprocess.py')
pp = importlib.util.module_from_spec(spec); spec.loader.exec_module(pp)
rs = hashlib.sha256((R/'release_manifest.json').read_bytes()).hexdigest()
es = hashlib.sha256((R/'bin/paper1StokesReference').read_bytes()).hexdigest()
pp.read_case(R/'prepared'/'h75_d100_T_tight', rs, es)   # 必须是绝对路径
```

**注意**：`read_case` 与 `validate_seed` 用 `str(case)` 拼期望 argv，相对路径会导致 `seed validation: mapping invocation mismatch` 的**假失败**。此坑已踩过一次并记入记忆。
