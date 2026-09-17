# SIM-EC1XT240 STEP 5-F 动态 Bouzidi link topology transition 修复报告

## 最终判定

**STEP 5-F：短程 0→3 nm PASS；最终 0→10 nm FAIL。STEP 5 不能关闭，不允许进入 STEP 6。**

应用层 old→new link 状态交接消除了 step 3595 的瞬时质量缺口，并使冻结的 0→3 nm 双质量门槛同时通过。但相同程序直接运行 0→10 nm 时，`R_pop` 在 step 3918、位移 `3.03370 nm` 再次超过 `1e-3`，`R_corrected` 在 step 3939 超限；运行最终于 step 5323、位移 `5.60394 nm` 因 `rho_max=1.20123>1.2` 停止。此时尚未到第二次 material conversion，因此不能报告完整 10 nm 或多次拓扑转换成功。

本轮没有修改 OpenLB、冻结 STEP 4、动态 material 转换逻辑、`NoDynamics`、转换节点 population 初始化、Zou/He、几何、`dt/tau`、壁速或验收标准。

## 1. 实际 Bouzidi link 生命周期

候选程序中 link 生命周期如下：

1. `updatePeriodicLinks()` 每步先将全部 `BOUZIDI_DISTANCE` 置为 `-1`、`BOUZIDI_VELOCITY` 置为0，再只为当前 fluid owner→solid neighbor 的 link 写入新 `q` 和壁速系数，并同步 `stage::Full` overlap（`step5F_link_transition_fix.cpp:23-66`）。
2. `q` 和壁速分别存储在 descriptor 字段 `BOUZIDI_DISTANCE`、`BOUZIDI_VELOCITY`。
3. 拓扑事务顺序保持冻结实现：预测/快照→material提交→`NoDynamics`切换→preserve population→geometry同步；随后刷新新 link（`:394-426`）。
4. OpenLB 实际推进为 collision→block streaming→PostStream communication→PostStream postprocessors→PostPostProcess communication（`/home/dell/openlb/src/core/superLattice.hh:728-825`）。
5. moving Bouzidi PostStream 读取 owner、solid-side和opposite fluid-side populations，并覆盖 owner 的 opposite population（`/home/dell/openlb/src/boundary/setBouzidiBoundary.h:128-164`）。

因此 step 3595 的原实现会在 material提交后先撤销11,708条旧 owner link，再注册11,708条新 owner link；旧 owner stored populations仍参加 streaming，但失去最后的边界状态交接。

## 2. 最小 transition 实现

独立程序：

`step5_5_dynamic_material/step5F_link_transition_fix.cpp`

新增的应用层结构为：

- `OldLinkState`：保存 old owner、direction/opposite、`q_old`、旧壁速、预期新 owner及新 link状态；
- `TransitionAudit`：统计 old links、精确配对、终止项、重复目标和 writer 冲突；
- `transitionMap`：按 `newOwner = oldOwner-c_i`（x周期映射）寻找相同方向的新 link；
- `collideAndStreamWithTransition()`：只在实际 topology event step 拆分 PostStream，计算旧 link 若完成原闭合时的状态差，并交给持久 bulk owner。

最终 v5 的交接规则为：

1. 非接收 cell 继续由标准新 Bouzidi 负责壁面速度/动量闭合；事件步的接收 cell 临时从标准 PostStream 中排除，再由一次自定义复合处理同时完成保存的新 Bouzidi 闭合与状态交接，避免同一 population 有两个 boundary writer；
2. old-link ownership 差是控制体积零阶状态，不再作为单一方向动量注入；
3. 按 `alpha_old/alpha_receiver` 保持 cut-cell质量，将交接量聚合到接收 bulk cell，并按D3Q19权重加入，净动量为0；
4. 新 owner为 material 1时直接接收；若精确新 link owner为material 4/5 Zou/He压力节点，则转到压力面内侧第一层material 1，避免覆盖 prescribed-rho writer；
5. 没有精确新 link 的572个角点/压力终止项不作任意补偿；
6. 复合处理完成后恢复接收 cell 的新 `q`/壁速字段并执行 PostPostProcess communication；每个事件只执行一次，非事件步完全沿用标准 `collide(); AndStream()`。

本方案没有改变转换节点 stored populations，也没有全域质量归一化或按目标残差补质量。交接值逐 link 来自冻结的 `q_old`、旧壁速及同一 PostStream 时间层的实际 populations。

### 开发中保留的失败记录

- v1：仅让旧 link多执行最后一次闭合，修复量留在solid storage，下一步即丢失；0→3 nm FAIL。
- v2：将link量直接写入单一新incoming population，质量门槛满足但产生人工方向动量，step 3595 `Mach=0.08427`，FAIL。
- v3：采用零阶bulk交接但不处理pressure-owned精确配对，`R_corrected`通过而`max|R_pop|=1.00491e-3`，FAIL。
- v4：pressure-owned状态转入内侧bulk，不写Zou/He cell；0→3 nm通过，但实现顺序仍是标准Bouzidi后附加零阶交接，严格审计下属于两个顺序writer。
- v5：将v4的物理交接保持不变，但把事件步接收cell改为单一复合writer；这是最终候选。

上述运行目录均未覆盖。

## 3. 修复前11,708条旧 link 如何产生缺口

STEP 5-E账本已量化：旧 active→inactive links 在streaming中的净改量为
`-1.31919635139e-21 kg`，但刷新后不再有旧 PostStream writer；反事实旧闭合量为
`+1.32990958611e-21 kg`。新 links 的streaming+Bouzidi净量仅
`+2.85486107e-24 kg`，无法承担旧状态。

方向9→18与17→8两组 y-z 斜向links贡献约99.81%的 affected-link净负量。它是拓扑跨格的离散所有权交接缺失，不是重复link、非法`q`、错误壁速、周期通信或一般Bouzidi公式错误。

v5在首次事件中记录：

- old links：11,708；
- 精确 old→new link配对：11,136；
- 实际转入持久bulk的配对：11,136；
- 明确终止：572；
- 交接质量：`1.36389271676e-21 kg`；
- duplicate old targets：0；
- writer conflicts：0。

## 4. 0→3 nm 冻结验收

run-id：`step5F_link_transition_0to3nm_v5_20260909`，退出码0。

|指标|结果|标准|判定|
|---|---:|---:|---|
|完成位移|`2.999688538 nm`|最后一个不超过3 nm的离散步|PASS|
|首次转换|step 3595，2304节点|解析预测一致|PASS|
|`max |R_pop|`|`9.87376770164e-4`|`<1e-3`|PASS|
|`max |R_corrected|`|`9.74327576793e-4`|`<1e-3`|PASS|
|rho范围|`[0.986556163,1.109679905]`|`[0.8,1.2]`|PASS|
|最大Mach|`0.011684468`|`<=0.05`|PASS|
|NaN/Inf|0|0|PASS|
|非法link|0|0|PASS|
|periodic mismatch/dynamics error|0/0|0/0|PASS|

事件步残差：

|step|`R_pop`|`R_corrected`|
|---:|---:|---:|
|3594|`-8.41169493221e-4`|`-8.41169493221e-4`|
|3595|`-8.36150907098e-4`|`-8.23101713727e-4`|
|3596|`-8.17913345578e-4`|`-8.04864152207e-4`|
|3898|`-9.87376770164e-4`|`-9.74327576793e-4`|

因此首次 topology event 的瞬时跳变已经闭合，且短程演化满足全部冻结标准。

## 5. 直接 0→10 nm 验证

因0→3 nm PASS，按任务要求未增加1 nm或5 nm测试，直接运行同一v5程序：

- run-id：`step5F_link_transition_0to10nm_v5_20260909`；
- 计划步数：10,000；
- 实际完成：5,323步；
- 实际位移：`5.603942196 nm`；
- 退出码3，表示冻结验收失败，不是崩溃。

|指标|结果|标准|判定|
|---|---:|---:|---|
|完成10 nm|否，停于5.604 nm|10 nm|FAIL|
|`max |R_pop|`|`2.63604788993e-3`|`<1e-3`|FAIL|
|`max |R_corrected|`|`2.62299869656e-3`|`<1e-3`|FAIL|
|rho全过程范围|`[0.976850636,1.201229893]`|`[0.8,1.2]`|FAIL|
|最大Mach|`0.0182483294`|`<=0.05`|PASS|
|NaN/Inf|0|0|PASS|
|非法link|0|0|PASS|
|periodic mismatch/dynamics error|0/0|0/0|PASS|
|材料转换累计|2304|截至停止点符合解析几何|PASS|

首次超限顺序：

1. step 3918、位移`3.033696 nm`：`R_pop=-1.00096862604e-3`；
2. step 3939、位移`3.069538 nm`：`R_corrected=-1.00104780831e-3`；
3. step 5083、位移`5.155596 nm`：全过程最大Mach `0.0182483`，仍低于门槛；
4. step 5323、位移`5.603942 nm`：`rho_max=1.201229893`，触发稳定性停止。

第二次离散material转换尚未发生，所以本次失败不能归因于第二个 transition event。结果表明v5在单一writer约束下正确修复了首次事件的瞬时所有权缺口，但在其后的持续运动中，`M_pop +` Zou/He通量账本仍逐步产生负残差；短程3 nm通过不足以证明完整10 nm闭合。

## 6. 代码和输出

- 程序SHA-256：`0d7dac0cf5525c5db7c483c6486ab58b27568ca8b0972c06c4f43534acbade2a`；
- STEP 4冻结SHA-256仍为`9444c61aab6cc67499211f2724d109923d91d9bc0fe66747446acf2da5e399e2`；
- topology manager SHA-256仍为`a267132ce080251a49248894e212da6f1a516149b483fb661c8e7fe4dacffe57`。

两个正式输出目录均包含：

- `step5F_history.csv`：逐步双质量残差、rho、Mach、material和link状态；
- `conversion_events.csv`：转换节点；
- `link_transition_map.csv`：old/new状态与接收优先级；
- `link_transition_population_ledger.csv`：逐link交接量；
- `topology_prediction.csv`、`transaction_phase_log.csv`；
- `result.txt`、`run_manifest.txt`、`run.log`。

正式目录：

- `step5_5_dynamic_material/output/step5F_link_transition_0to3nm_v5_20260909/`；
- `step5_5_dynamic_material/output/step5F_link_transition_0to10nm_v5_20260909/`。

## 7. 三个必须回答的问题

1. **修复前11,708条旧link如何产生缺口？** material提交后旧link先失活；旧owner populations随后streaming，却没有旧→新边界状态交接。新Bouzidi只闭合新owner，导致事件步约`1.23e-21 kg`未闭合。
2. **修复后质量账本是否闭合？** 首次事件及0→3 nm闭合，双残差均小于`1e-3`；完整0→10 nm不闭合，运行在5.604 nm前已出现持续残差和rho上限越界。
3. **STEP 5是否可以关闭并进入STEP 6？** **否。** 完整10 nm未完成，且最终双质量残差均失败。程序退出码0仅适用于短程0→3 nm；最终验证退出码3，不能解释为物理通过。

**停止在 STEP 5。未运行第二次转换之后的运动，未进入液滴、两相、润湿、空气或 STEP 6。**

Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is **SIM-EC1XT240**.
