# SIM-EC1XT240 STEP 5 最终质量审计一致性报告

## 判定

**情况 B：population-consistent 审计仍然 FAIL。** 在完全相同的 0→3 nm 物理演化下，新增的 `R_pop` 全过程最大绝对值为
`1.20808380745e-3`，仍高于冻结门槛 `1e-3`。因此原 `R_geom_old` 的跳变确有显著部分来自
`material -> NoDynamics` 后 `computeRho()` 口径改变，但这并不能解释全部质量收支缺口。

首次 material/dynamics 提交的瞬间，2304 个节点的 stored populations 没有发生任何变化，population-consistent
质量也没有瞬时损失；然而包含转换后的第一次 collision/streaming 的 step 3595 仍产生
`-1.32775889668e-21 kg`（相对初始质量 `-1.84410957873e-4`）的未闭合量。按任务规定，本轮没有加入补偿，
STEP 5 尚不具备进入最终 0→10 nm 验证的条件。

## 审计实现与源码依据

现有 v3 的 `conversion_before_after.csv` 足以核对转换瞬间，却不含转换后所有 `alpha>0` cell 的逐步 stored
populations，因此不能离线恢复完整 `M_pop(t)`。为此新增了纯诊断副本
`step5_5_dynamic_material/mass_audit_consistency_test.cpp`，物理推进、事务、边界、轨迹和参数均沿用 v3；只增加读取和输出，
没有写 lattice 状态。

本机 OpenLB 版本 `5953d8a-dirty` 的实际定义为：

- `/home/dell/openlb/src/dynamics/lbm.h:290-297`：`rho = 1 + sum_i f_i`；
- `/home/dell/openlb/src/dynamics/momenta/elements.h:149-155`：bulk density 调用上述 `lbm::computeRho`；
- 同文件 `128-146`：`OneDensity::compute()` 固定返回 `rho=1`；转换后的 `NoDynamics` 使用这一 momenta 口径。

因此新审计对每个 `alpha_i>0` cell 直接读取实际 stored `f0...f18`：

```text
rho_pop,i = 1 + sum(q=0..18) f_q,i
M_pop(t)  = sum_i alpha_i(h) rho_pop,i rho_phys dx^3
R_pop(t)  = [M_pop(t)-M_pop(0)+m_out,trap(t)] / M_pop(0)
```

边界项没有更改：仍使用 v3/STEP 4 的 Zou/He 两端有符号宏观质量通量及梯形时间积分。
直接循环恢复值与 `lbm<D>::computeRho(cell)` 的全过程最大差为 `1.33227e-15`，验证了实现一致性。

冻结文件未修改：

- STEP 4 SHA-256：`9444c61aab6cc67499211f2724d109923d91d9bc0fe66747446acf2da5e399e2`；
- v3 程序 SHA-256：`ba43135d72f5e09cb9e61537a692a5c690283d69d3cbbe6c6ff494b635102554`；
- topology manager SHA-256：`a267132ce080251a49248894e212da6f1a516149b483fb661c8e7fe4dacffe57`；
- 新审计程序 SHA-256：`b569b6929f338905c3428a793a3c18ee6dece551badb53d8f65b8bdd5ada5cad`。

## 双质量口径时序

初始两种质量完全相同：`M_geom_old(0)=M_pop(0)=7.19999999999e-18 kg`。

|step|`M_geom_old` (kg)|`M_pop` (kg)|old-pop (kg)|累计向外质量 (kg)|`R_geom_old`|`R_pop`|
|---:|---:|---:|---:|---:|---:|---:|
|3594|`7.10417146991e-18`|`7.10480048468e-18`|`-6.29014768839e-22`|`8.91430949598e-20`|`-9.28532655559e-4`|`-8.41169493221e-4`|
|3595|`7.10044076330e-18`|`7.10341494849e-18`|`-2.97418519044e-21`|`8.92008722565e-20`|`-1.43866172754e-3`|`-1.02558045109e-3`|
|3596|`7.10037821340e-18`|`7.10334908929e-18`|`-2.97087588950e-21`|`8.92585714047e-20`|`-1.43933544323e-3`|`-1.02671379191e-3`|
|3898|`7.08107303538e-18`|`7.08406015089e-18`|`-2.98711550253e-21`|`1.07241645695e-19`|`-1.62296096058e-3`|`-1.20808380745e-3`|

`R_pop` 的最大绝对值出现在末态 step 3898。运行完成 3898 步，位移
`2.9996885378 nm`；无 NaN/Inf，rho=`[0.986811639,1.109679905]`，最大 Mach=`1.05075706e-3`，
非法 link=0，periodic mismatch=0，dynamics error=0。退出码 3 表示质量门槛失败，不是程序异常。

## 2304 节点的转换瞬时账本

下表在 step 3595 的相同 `hNew`、同一组 `alpha` 上比较 material/dynamics 提交前与提交后、streaming 前的状态，
因此只隔离读取口径改变，不混入时间推进。

|量|提交前|提交后|立即变化|
|---|---:|---:|---:|
|`sum alpha`|`1151.53216119825`|`1151.53216119825`|0|
|`sum alpha*rho_momenta`|`1180.85523087087`|`1151.53216119825`|`-29.3230696726`|
|`sum alpha*rho_pop`|`1181.04230043420`|`1181.04230043420`|0|
|`sum rho_pop`，未加 alpha|`2363.04425693925`|`2363.04425693925`|0|
|`sum alpha*rho_momenta*rho_phys*dx^3`|`1.47606903859e-19 kg`|`1.43941520150e-19 kg`|`-3.66538370908e-21 kg`|
|`sum alpha*rho_pop*rho_phys*dx^3`|`1.47630287554e-19 kg`|`1.47630287554e-19 kg`|0|
|最大单一 stored population 变化|0|0|0|

因此 step 3595 **不存在 material/dynamics 提交瞬间的真实 stored-population 质量损失**。
`NoDynamics` 的固定 `rho=1` 使旧审计在这一瞬间人为减少 `3.66538370908e-21 kg`，相当于初始质量的
`5.09081070706e-4`。

对实际逐步输出（均在 collide/stream 后）而言：

- `R_geom_old` 从 step 3594 到 3595 跳变 `-5.10129071984e-4`；
- `R_pop` 同期仍跳变 `-1.84410957873e-4`；
- 两种跳变量之差为 `-3.25718114111e-4`，即旧报告所见跳变的 `63.8501%` 来自该步最终状态中的读取口径差异；
- “立即提交”与“推进后采样”的比例不同，是因为 step 3595 的 collision/streaming 和 Bouzidi 随后又改变了
  solid-side stored populations，而 `NoDynamics::computeRho()` 始终固定为 1。

## 未闭合项定位与大小

population-consistent 审计排除了 material 提交时对 stored populations 的删除，但不能消除控制体积收支缺口：

1. 转换前 step 3594 已累计 `R_pop=-8.41169493221e-4`，对应 `-6.05642035118e-21 kg`；
2. step 3594→3595 中，`M_pop` 减少 `1.38553619336e-21 kg`，同期积分向外通量仅增加
   `5.77772966792e-23 kg`，故该事件时间步留下 `-1.32775889668e-21 kg`
   (`-1.84410957873e-4 M_pop(0)`) 的未计量项；
3. step 3595→3898 又累计 `-1.31402416576e-21 kg`
   (`-1.82503356356e-4 M_pop(0)`)；
4. 末态总缺口为 `-8.69820341363e-21 kg`，即 `R_pop=-1.20808380745e-3`。

在本轮允许的只读审计范围内，可将新增缺口定位到**拓扑转换后的控制体积/population 演化与只包含 y 开放面通量的收支之间缺少一项**，而不是 material 提交时直接删除 populations。具体而言，
新 `NoDynamics` cells 仍有非零 `alpha` 和 stored populations，但其后参与 streaming/Bouzidi 的方式已改变；当前边界积分只统计两端
Zou/He 通量，没有单独的拓扑/移动固壁离散交换项。本报告仅给出缺口的实测大小，不把它解释为出口排液，也未实现任何补偿。

## 对四个问题的明确回答

1. **原 `R_geom` 跳变中多少来自 `NoDynamics rho=1`？** 提交瞬时人为变化为
   `-3.66538370908e-21 kg`（`-5.09081070706e-4 M0`）；在 step 3594→3595 的推进后记录中，
   两种残差跳变量之差为 `-3.25718114111e-4 M0`，占旧跳变 `63.8501%`。
2. **population-consistent `R_pop` 最大值？** `max |R_pop|=1.20808380745e-3`，step 3898，FAIL。
3. **step 3595 是否存在真实瞬时质量损失？** material/dynamics 提交瞬间没有，stored populations 和
   `sum alpha*rho_pop` 均严格不变；但完成该步推进后存在 `1.32775889668e-21 kg` 的控制体积收支缺口。
4. **是否具备进入最终 10 nm 验证的条件？** **否。** 采用一致人口质量口径后仍超过 `1e-3`，应停留在
   STEP 5，先解释/闭合转换后缺失的离散拓扑或移动边界质量项；本轮未实施修复。

## 输出与保护

- 新程序：`step5_5_dynamic_material/mass_audit_consistency_test.cpp`；
- 新构建目标：`step5_5_dynamic_material/Makefile` 中 `mass-audit-consistency`；
- 唯一 run-id：`mass_audit_consistency_0to3nm_v1_20260909`；
- 双审计时序：`step5_5_dynamic_material/output/mass_audit_consistency_0to3nm_v1_20260909/first_conversion_history.csv`；
- 事件账本：同目录 `conversion_event_mass_audit.csv`；
- `result.txt`、`run_manifest.txt`、`run.log` 均保存在同目录。

没有修改或覆盖 STEP 4、STEP 5.5 v3、OpenLB 或任何历史结果。没有启动 10 nm、两相、液滴、润湿、空气或参数扫描。

Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is **SIM-EC1XT240**.
