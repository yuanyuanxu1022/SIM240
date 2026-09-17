# SIM-EC1XT240 STEP 5-E link-level population 质量账本报告

## 判定

**剩余事件步缺口已定位到动态拓扑跨格时旧/新 Bouzidi link 的 population 所有权交接。**

step 3595 提交 2304 个 `fluid -> solid` 节点后，11,708 条旧 Bouzidi link 立即失活，另有 11,708 条、位于下一层持久 fluid owner 上的新 link 激活。旧 owner 在本步已切换为 `NoDynamics`，但随后仍参加 block streaming；原样保存的 populations 因 streaming 改变，而失活的旧 link 不再执行 PostStream 闭合。新 Bouzidi link 只闭合新 owner 的 incoming population，不能补回旧 owner/cut-cell 账本中的这部分交换。

受拓扑影响 link 的实际净改量为 `-1.31634149032e-21 kg`，与 STEP 5-C 已确认的事件步剩余缺口 `-1.23380470441e-21 kg` 同号、同量级，覆盖其 `106.69%`；其余非局部/边界项净抵消 `+8.25367859e-23 kg`。这不是非法 link、重复处理、通信覆盖或 Bouzidi 公式计算错误。

本轮只增加诊断和账本，没有修改物理推进，也没有实施修复或启动 10 nm。

## 范围与复现

- 冻结基线：STEP 5.5 v3 的几何、Zou/He、动态 material、`NoDynamics`、Bouzidi、轨迹、`dt/tau` 和 preserve-population 策略；
- 唯一诊断程序：`step5_5_dynamic_material/step5E_link_mass_ledger.cpp`；
- 构建目标：`make step5e-link-ledger -j2`；
- 运行命令：`mpirun -np 1 ./step5E_link_mass_ledger`；
- 正式 run-id：`step5E_link_mass_ledger_3594_3595_v3_20260909`；
- OpenLB：`5953d8a-dirty`；单 MPI rank；
- 程序 SHA-256：`c46e7bc4f19e4361db6920263ce45b59c7dd98229ed25d8985a75dc15034adbe`；
- 完成 step 3594，并只拆分执行 step 3595；退出码 0。

既有逐步输出不包含 streaming/Bouzidi 前后的每条 population，因而无法纯离线完成本账本。本程序只增加最小阶段快照，不回写诊断值，不改变 lattice 演化。

## 实际算子顺序与账本定义

冻结程序先完成 material/dynamics 事务并刷新 `q` 与壁速，然后调用 `lattice.collide(); lattice.AndStream()`。本地 OpenLB 的实际顺序为：

1. collision；
2. block-local streaming；
3. `PostStream` communicator；
4. block `PostStream` postprocessors，其中 moving Bouzidi priority 为 `-1`；
5. `PostPostProcess` communication。

源码依据为 `/home/dell/openlb/src/core/superLattice.hh:728`、`:762`、`:808`。Bouzidi 在 `/home/dell/openlb/src/boundary/setBouzidiBoundary.h:128` 中从 solid-side、boundary owner 和 opposite fluid-side 读取 population，并覆盖 owner 的 opposite population。

对每条 affected link，账本记录 owner、方向、邻居、old/new material、old/new `q`、old/new壁速系数及各阶段 population，并计算：

```text
delta_m_stream = alpha_owner (f_after_stream - f_before_stream) rho_phys dx^3
delta_m_comm   = alpha_owner (f_after_comm   - f_after_stream) rho_phys dx^3
delta_m_Bouzidi= alpha_owner (f_after_Bouzidi- f_after_comm)   rho_phys dx^3
delta_m_link   = delta_m_stream + delta_m_comm + delta_m_Bouzidi
```

另用相同的 PostStream 数据和冻结的 `q_old/u_wall,old` 只读计算“旧 link 若仍执行原 Bouzidi”的反事实闭合量。该量用于定位缺失的 link handoff，不作为质量补偿，也未写回 lattice。

## step 3595 阶段质量分解

|阶段|`M_pop` (kg)|相对上一阶段变化 (kg)|
|---|---:|---:|
|step 3594 状态，`h_old`|`7.10480048468e-18`|0|
|同一 populations 按 `h_new` 重加权|`7.10470653049e-18`|`-9.39541923e-23`|
|material/dynamics 提交后、collision 前|`7.10470653049e-18`|0|
|collision 后|`7.10410091430e-18`|`-6.05616192e-22`|
|streaming 后、通信前|`7.10536088813e-18`|`+1.25997384e-21`|
|PostStream 通信后|`7.10536088813e-18`|0|
|Bouzidi 后|`7.10341494849e-18`|`-1.94593964e-21`|

material/dynamics 提交阶段仍严格不改变 stored populations。通信阶段在本次单 rank/单 cuboid core 账本中的改量为零。

## affected link 汇总

共记录 23,416 条 affected link：

|link 类别|条数|streaming (kg)|实际 Bouzidi (kg)|实际净量 (kg)|旧-link反事实闭合 (kg)|
|---|---:|---:|---:|---:|---:|
|旧 link：active→inactive|11,708|`-1.31919635139e-21`|0|`-1.31919635139e-21`|`+1.32990958611e-21`|
|新 link：inactive→active|11,708|`+5.34487213e-23`|`-5.05938602e-23`|`+2.85486107e-24`|0|
|合计|23,416|`-1.26574763008e-21`|`-5.05938602e-23`|`-1.31634149032e-21`|`+1.32990958611e-21`|

反事实旧闭合量几乎抵消旧 owner 在 streaming 中的 `-1.31920e-21 kg` 改量，而标准新 link 闭合的净效果仅为 `+2.85e-24 kg`。因此问题不是“Bouzidi 总体质量不守恒”，而是边界穿过 lattice plane 时，旧 link 被撤销、新 link 被注册，却没有一次性的离散 population handoff。

### 主导方向

本机 D3Q19 编号来自 `/home/dell/openlb/src/descriptor/definition/common.h`。

|owner direction → written opposite|`c_i`|条数|实际净贡献 (kg)|旧-link反事实闭合 (kg)|
|---|---|---:|---:|---:|
|9 → 18|`(0,-1,+1)`|4,512|`-6.56904066991e-22`|`+6.58151929846e-22`|
|17 → 8|`(0,+1,+1)`|4,512|`-6.56901433852e-22`|`+6.58149296707e-22`|
|12 → 3|`(0,0,+1)`|4,608|`-1.81013259481e-23`|`+1.92245364958e-23`|

两个 y-z 斜向组已贡献 `-1.31380550084e-21 kg`，占全部 affected-link 净负量约 `99.81%`。这也解释了缺口为何集中在移动水平壁面而不是 x-periodic seam。

### 单 link 最大贡献

完整 top-100 见正式输出 CSV。最大绝对值的前几条均是 `q_old≈1.1502345e-4`、提交后 `q_new=-1` 的失活旧 link：

|owner `(ix,iy,iz)`|方向→opposite|solid-side邻居|`delta_m_link` (kg)|反事实旧闭合 (kg)|
|---|---|---|---:|---:|
|`(12,1,35)`|17→8|`(12,2,36)`|`-3.11056184213e-24`|`+3.11277642731e-24`|
|`(35,1,35)`|17→8|`(35,2,36)`|`-3.11056184212e-24`|`+3.11277642731e-24`|
|`(12,46,35)`|9→18|`(12,45,36)`|`-2.91783317668e-24`|`+2.92004776186e-24`|
|`(35,46,35)`|9→18|`(35,45,36)`|`-2.91783317668e-24`|`+2.92004776186e-24`|

top-100 的有符号合计为 `-1.17940228822e-22 kg`；缺口不是由一个坏 cell/link 独占，而是大量同构的拓扑跨格 link 同步累积。

## 根因分类

- **A，link 重复处理：排除。** 重复 Bouzidi target 数为0。
- **B，link 遗漏处理：确认，但仅限事件步的拓扑交接。** 不是静态几何漏 link，而是11,708条旧 link 失活后没有与11,708条新 link做 population handoff。
- **C，`q` 更新时间错误：排除为数值错误。** 旧 owner 的 `q_old≈1.15023e-4`，跨格后下一层 owner 的 `q_new≈0.999797`，与壁面越过 owner plane 的几何一致；问题在离散状态交接，不在 `q` 数值。
- **D，壁速更新时间错误：未见证据。** 账本使用刷新后的冻结轨迹壁速，Bouzidi 公式逐 link 最大误差仅 `6.94e-18`（population单位）。
- **E，streaming 顺序问题：是直接触发机制。** material先提交、旧 link先撤销，随后旧 owner stored populations参与streaming；PostStream时只有新 link可执行，无法闭合已经失活的旧 owner/link。
- **F，明确的其他原因：动态 link 所有权迁移缺少一次性、守恒的 population transition operator。**

因此可称为 **Bouzidi 拓扑切换时序/所有权交接问题**，但不能称为一般 Bouzidi 公式错误。通信、非法 link、重复覆盖、`q` 截断和壁速公式均没有制造该缺口。

## 下一步唯一修复点

下一步只应在 `fluid -> solid` 事务与该事件步 `PostStream` 之间加入一个**事件限定的、link-pair守恒交接算子**：保存每个失活旧 link 的 `q_old`、壁速和必要 populations，将其与空间上对应的新 fluid-owner link 配对，在同一时间层完成旧→新边界状态转移；对这批 crossed links 必须保证交接算子与标准新 Bouzidi 只有一个最终 writer。下一步之后恢复标准 Bouzidi，不应长期保留双处理。

该修复应针对上述离散路径，而不是增加总质量补偿、重构全部转换节点 population、调整参数或修改阈值。实施后先重跑冻结 0→3 nm，验证事件步及全过程 `|R|<1e-3`；本报告未实施该修复。

## 输出与停止点

- 完整逐 link 账本：`step5_5_dynamic_material/output/step5E_link_mass_ledger_3594_3595_v3_20260909/affected_link_mass_ledger.csv`；
- 按 `|delta_m_link|` 排序的 top-100：同目录 `top100_link_mass_contributions.csv`；
- 全局与 affected-region 阶段账本：同目录 `stage_mass_ledger.csv`；
- 数值摘要与复现信息：同目录 `result.txt`、`run_manifest.txt`；
- 早期 v1/v2 诊断目录保留，正式结论使用 v3。

**STEP 5 convergence task 已完成 link-level 根因定位，但尚未实施修复。停止在 STEP 5，不进入 10 nm 或 STEP 6。**

Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is **SIM-EC1XT240**.
