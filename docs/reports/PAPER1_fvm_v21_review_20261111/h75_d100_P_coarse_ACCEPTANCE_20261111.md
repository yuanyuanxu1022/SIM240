# h75_d100_P_coarse 独立验收（2026-11-11 23:2x）

> 结论一句话：**本层证据全部通过（`LOCAL_CHECKS_PASS`，`issues=[]`），但这不是参考资格，也不是任何 PASS/FAIL 判定。**
> 官方 `assess()` 该点仍为 `NOT_ASSESSABLE`。

---

## 1. 运行身份

| 项 | 值 |
|---|---|
| case_id | `h75_d100_P_coarse` |
| run_id | `h75_d100_P_coarse_20261111T231527_172b0354` |
| 独立退出码 | `0` |
| 停止原因 | `native_convergence`（原生收敛，**未用平板例外**） |
| 日志结尾 | `End` 存在 |
| 外迭代 | **2** |
| 末时间 | `2` |
| 末残差 `v` | `2.8305412160253768e-14`（门槛 `1e-10`，余量 3,500 倍） |
| 求解墙钟 | **0.1678 s**（上限 1,800 s） |
| 网格/检查墙钟 | 0.1655 s / 0.2165 s（上限各 120 s） |
| 盘占用 | 8,245,497 B（≈7.9 MB），预算内 |
| release 绑定 | `97ae55ff9dbaad4c2aa58fbe3b3b5dac548f82400631ac5cd1e12c9ef96c13e5` |
| 可执行绑定 | `73b1f633b96f0074abcd30358e83b57790f00c29aef1ef493f08345f3453f352` |
| OpenFOAM | 13（`13-441953dfbb42`），`nProcs : 1` |

### 1.1 “只迭代 2 步”不是漏算——已查明

首轮看到 2 步很可疑，因为 `h75_d100_T_coarse` 用了 **11,403** 步，差 5,700 倍。逐项核对后确认这是**方程类型不同导致的必然差异**：

| | P 方向 | T 方向 |
|---|---|---|
| `equation` | `scalar_Poisson` | `vector_Stokes` |
| 流动形态 | 单方向（平行槽），速度只有一个非零分量 | 横槽，`Ux` 与 `Uz` 同时非零 |
| 求解器 | `DICPCG` 直接解一次线性系统 | `smoothSolver` + `GAMG` 耦合迭代 |
| 日志行为 | 1 次 DICPCG，207 步，残差压到 `7.8930393891804428e-13`；第 2 次初残差已是 `2.83e-14` → 立即判收敛 | 每步 Ux/Uz/p 各解一次，共 11,403 次外迭代 |
| 是否有平板上万步那种“伪收敛”风险 | 无，线性系统一次解到底 | 无，残差单调降到 `1e-11` 以下 |

⇒ **P 方向 2 步 = 正确行为**。这也解释了工期差异（0.17 s vs 205 s）。

---

## 2. 独立复算（不共用读数器算法）

### 2.1 网格构成独立推导

不采用程序里的 `expected_cells`，直接从几何算：

```
x 向：P=240 nm / dx=1.25 nm            = 192 格
z 向：(d+h)=(100+75) nm / 1.25 nm      = 140 格
实心脊（x>120 nm 且 z<100 nm）被挖掉：96 × 80 = 7,680 格
⇒ 192 × 140 − 7,680 = 19,200 格   与实际导出 19,200 行一致
单格体积 = 1.25 nm × 1 nm(Ly) × 1.25 nm = 1.5625e-27 m³
流体体积 = 19,200 × 1.5625e-27 = 3.000000e-23 m³（元数据 3.0e-23 ✓）
```

### 2.2 K 的独立复算

按 `postprocess.py:39-42` 的定义自己实现一遍（`J = Σ v·V / A_plan`，`K = ν·J/a`）：

| | 值 |
|---|---|
| 独立复算 `J` | `9.76608332143614628e-12 m²/s` |
| 独立复算 `K` | `9.76608332143614586e-23 m³` |
| 读数器 `K` | `9.766083321436146e-23 m³` |
| 相对差 | **`0.000e+00`**（浮点末位级一致） |

配套核对：平均速度 `7.81286665714891619e-05 m/s`；`min/max v = 1.427902e-07 / 1.652777e-04`；非有限值 **0**、负值 **0**；场文件 SHA256 `c24a99e8c325c09142dac0d35b6eef8d01576d45fc35ebd87f211d78444a1953`，与回执 `native_field_sha256` 逐位相符。

> 记一笔自己的错：第一次复算我写成 `K = mean_v·ν/a`，结果差 `8×10⁶`。原因是把 `J`（单位宽度流量）当成了平均速度。查询定义 `J = Σv·V/A_plan` 后改正。**这次错在“我”，不在数据。**

---

## 3. 两个诊断量

| 量 | 本层值 | 门槛归属 |
|---|---|---|
| `power_balance_percent` | **0.10566621823656641%** | **coarse 只作诊断**，0.1% 门槛仅约束 fine/tight/flat |
| `section_flux_spread_percent` | `0.0`，附注 `exact y invariance of scalar model; not an independent mass test` | P 的 y 不变通量**不计作独立质量测试** |

依据 `PROTOCOL.md:75`：*“最细 fine 及同网格 tight、平板 flat 要求 … 驱动功与黏性耗散相对差 ≤0.1%；coarse/mid 保存这些诊断，不额外施加最细层 0.1% 门槛。”*

**但要盯住**：0.1057% 已略高于 0.1%。虽然本层不判决，fine/tight 必须自己压到 0.1% 以内。参考 T 的下降趋势（coarse 0.3547% → mid 0.1497% → fine 0.0659% → tight 通过，每级约降 2.3 倍），P 从 0.1057% 起，mid 约 0.045%、fine 约 0.02%，通过的可能性大，但**这是趋势外推，不是保证**。

---

## 4. 与本层参考的 delta（**预演，不是判定**）

```
delta = (K5 / K_coarse − 1) × 100
      = (9.834075958643652e-23 / 9.766083321436146e-23 − 1) × 100
      = +0.6962%
```

`K5` 来自 `comparison_inputs.json`（`h75_d100_P`，OpenLB 5 nm，`result_sha256 a1dc9e60…`）。

**同层级对比**（这是唯一可比的同类量）：

| 点 | K_coarse | delta（对本层参考） |
|---|---:|---:|
| `h75_d100_T` | `4.352084022936e-23` | **+2.2274%** |
| `h75_d100_P` | `9.766083321436146e-23` | **+0.6962%** |

⇒ 同网格、同算法、只差方向，T 超 2% 而 P 只 0.70%。这为“超 2% 是否方向相关”提供了**第一个同条件比较**。

### 4.1 为什么这仍不能写成 PASS

1. **coarse 不是参考。** `d21 ≤ 1%` 这种判据只在有下一级时才能算，本层目前连 `d21` 都没有。
2. **delta 会随加密移动。** T 的四取法是 `+2.2274%（coarse）→ +2.4264%（mid）→ +2.5110%（fine）→ +2.5735%（外推）`，逐级变大。P 的 K 若同样随加密下降，delta 也会升。
3. 定量看风险有多大：要让 P 越过 2%，参考 K 必须比 coarse 低 **>1.278%**。而 T 从 coarse 到 fine 只降了 **0.2767%**（`4.352084e-23 → 4.340042e-23`）。也就是说 P 需要比 T 大 **约 4.6 倍**的加密变化才会翻盘。
4. 但“可能性小”**不等于**“已经通过”。官方 `assess()` 该点 `status = NOT_ASSESSABLE`，这才是当前唯一有效记录。

**禁止的错误推理**：不得把这里的 0.6962% 与论文里“沿槽 +10.30%~+204.85%”“横槽 +8.11%~+54.19%”对比或相减——那些是 **OpenLB/V2 对原式 LC** 的偏差，这里是 **OpenLB 对收敛参考** 的偏差，比较对象完全不同。也不得说“P 方向已验证在 2% 内”。

---

## 5. 全局状态（官方 `assess()` 原样）

```
status                     = INCOMPLETE
execution_status           = PARTIAL
all_planned_records_finished = false
execution_closed           = false
comparison_evaluable       = false
automatic_followup_authorized = false
scientific_gate            = NOT_A_GLOBAL_REFERENCE_QUALIFICATION
selected_six_all_pass      = false
```

| 点 | 状态 |
|---|---|
| `h75_d100_P` | `NOT_ASSESSABLE` |
| `h75_d100_T` | **FAIL**，`delta 2.5110%`，`Kref 4.340041663047474e-23` |
| `h25_d100_T` / `h50_d120_P` / `h125_d120_P` / `h125_d120_T` | `NOT_ASSESSABLE` |

逐算例：`h75_d100_P_coarse` / `T_coarse` / `T_mid` / `T_fine` / 两平板 均 `LOCAL_CHECKS_PASS`；P 的 mid/fine/tight 与 `h25_d100_T`、`h50_d120_P`、`h125_d120_P`、`h125_d120_T` 全部 `NOT_EXECUTED`。

---

## 6. 冻结完整性

| 检查 | 结果 |
|---|---|
| 本地绑定 `sha256`（212 项） | 0 漂移 |
| 外部绑定 `external_sha256`（23 项，`/opt/openfoam13/...` 绝对路径） | 0 漂移 |
| 合计 | **235 项，0 漂移** |
| 清单文件 SHA | `97ae55ff…c13e5`（未变） |
| `numerical_execution_authorized` | `true` |
| `formal_review_status` | `ASTRA_FINAL_STATIC_RECHECK_COMPLETE` |

`reviewed_release_sha256 = f1531d40…c292` 与当前文件 SHA **不等**，已查明是**设计使然**：该值对应 `docs/reports/PAPER1_fvm_v21_review_20261111/release_manifest_before_authorization.json`，其现算哈希正是 `f1531d4091a6279a5db2df5cff75875d279d4ffc981f52ae5502bedd98ffc292`，即“授权位写入之前”的版本。**不是漂移，不得当成异常。**

两个平板 `h75_d0_P_flat` / `h75_d0_T_flat` 仍 `LOCAL_CHECKS_PASS`，`issues=[]`。

---

## 7. 三类证据分开记（不得互相替代）

```
NUMERICAL_GATE : 本层 LOCAL_CHECKS_PASS（收敛/退出码/残差/回执/哈希/复算全过）
RESULT_PASS    : 未判定（缺 mid/fine/tight）
geometry_PASS  : 未判定（本层只证 bounding box 与脊部无占据，非整体几何验收）
```

⇒ 只能表述为：**“P 方向 coarse 层的数值门槛通过”**，不得写成“P 方向验证成功”。

---

## 8. 下一步（未执行）

`h75_d100_P_mid` 已具备接入条件，逐项核对：

| 项 | 值 |
|---|---|
| `dx_nm` | `0.625`（coarse 的一半） |
| `expected_cells` | `76,800` |
| `direction` / `level` | `P` / `mid` |
| `seed_from` | `h75_d100_P_coarse`（回执存在且 `LOCAL_CHECKS_PASS`） |
| 种子源末时刻 | `2`，绑定字段 `2/v` |
| `seed_method` | `mapFields -consistent -mapMethod interpolate`（P 只映射 `v`） |
| `seed_time` / `start_time` | `0.5` / `0.5` |
| `end_time_cap` / 墙钟 | `120000` / `14,400 s` |
| `runtime/` | 不存在（无覆盖/重跑风险） |
| 几何一致性 | `h_nm/d_nm/direction` 与源一致（`run_one.py:107` 会硬校验） |

本报告**未启动** mid，未编译，未 mapFields，未改任何阈值或冻结代码。
