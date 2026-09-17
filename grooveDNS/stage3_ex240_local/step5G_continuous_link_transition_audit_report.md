# SIM-EC1XT240 STEP 5-G 连续移动阶段 Bouzidi link transition 守恒审计

## 判定

**诊断结论：0→10 nm 的后续失败不是“重复 old-link→new-link ownership transition 未执行”。**

现有 v5 结果显示，step 3595 之后至停止的 1728 个时间步中，逻辑 active-link 集合始终为 32,176 条，material、owner 和 direction 均未再次改变；`transition_old_links`、`exact_transition_pairs`、`transferred_bulk_links`、重复 writer 和非法 link 每步均为 0。程序虽然每步清空并重写 `BOUZIDI_DISTANCE/VELOCITY` 字段，但这只是同一批 link 的连续 `q`/壁速刷新，不是 population ownership 转移。

因此本轮没有修改代码，也没有重新运行仿真。审计使用已有
`step5F_link_transition_0to10nm_v5_20260909` 输出离线完成。

## 1. 实际每步更新路径

`step5F_link_transition_fix.cpp` 的实际顺序是：

1. `beginTopologyTransaction()` 根据新压头位置预测 material 变化；
2. 仅对 `tx.fluidToSolid` 捕获 `OldLinkState`；
3. 提交 material/dynamics/population 事务；
4. `updatePeriodicLinks()` 清除全部旧 `q`/壁速字段，再按当前几何为现有 fluid owner 重写 link；
5. 仅当捕获到旧 ownership link 时建立 `transitionMap` 并执行交接；
6. 无 topology event 时直接执行标准 `lattice.collide(); lattice.AndStream()`。

这意味着：字段层面每步均重新生成 32,176 条 link，但只有 owner/material/direction 改变才需要 STEP 5-F 的 ownership transfer。step 3595 后没有这种变化。

## 2. 连续更新统计

|区间/step|位移 (nm)|old active links|new active links|ownership-transition links|转移 population mass|`R_pop`|
|---|---:|---:|---:|---:|---:|---:|
|3595，首次 material event|2.501015|32,176|32,176|11,708 old；11,136精确配对|`1.36389271676e-21 kg`|`-8.3615091e-4`|
|3596–3898|2.502606–2.999689|每步32,176|每步32,176|每步0|每步0|末态`-9.8737677e-4`|
|3918|3.033696|32,176|32,176|0|0|`-1.0009686e-3`|
|3939|3.069538|32,176|32,176|0|0|`R_corrected=-1.0010478e-3`|
|5000|5.000000|32,176|32,176|0|0|`-1.7384472e-3`|
|5323，停止|5.603942|32,176|32,176|0|0|`-2.6360479e-3`|

完整 post-event 区间共 1728 行；32,176 条 active links 的计数变化次数为0，非零 topology-transition 行数为0，writer conflict、非法 link、periodic mismatch 和 dynamics error 均为0。累计材料转换仍只有 step 3595 的2304节点。

因此不存在以下两种现象：

- old link 在后续某一步失活而没有建立 new ownership link；
- 同一 ownership transition 在后续步骤被重复执行或由多个 writer 写入。

## 3. 质量残差的增长位置

以初始质量 `M0=7.1999999999931e-18 kg` 计：

- step 3595→3898：`R_pop` 累计变化 `-1.51225863e-4`，即 `-1.08882621e-21 kg`；
- step 3898→5323：继续变化 `-1.64867112e-3`，即 `-1.18704321e-20 kg`；
- step 5000→5323：单独贡献 `-8.97600708e-4`，即 `-6.46272510e-21 kg`。

首次 `|R_pop|>=1e-3` 是 step 3918、位移 `3.033696378 nm`；首次
`|R_corrected|>=1e-3` 是 step 3939、位移 `3.069537769 nm`。两个时刻均没有 material 或 link ownership transition。

0→3 nm 在 step 3898 结束时的 `max|R_pop|=9.87376770e-4`，距离门槛仅
`1.2623230e-5`。所以“短程PASS、长程FAIL”的直接原因是已有连续小偏差随运动时间累计，短程终点恰好仍在门槛内；不是3 nm之后突然遗漏了一次 STEP 5-F transfer。

## 4. q 连续变化的证据

首次转换建立的11,136条精确新link在step 3595均有
`q_new=0.999796944965`，涉及方向7、9、12、15、17及其opposite。对水平凸台底面和槽顶，这些同一 owner link 的 q 随位移连续减小：

|step|位移 (nm)|对应水平移动壁link的q|
|---:|---:|---:|
|3595|2.501015|0.999796945|
|3898|2.999689|0.900062292|
|3918|3.033696|0.893260724|
|3939|3.069538|0.886092446|
|5000|5.000000|0.500000000|
|5323|5.603942|0.379211561|

首次残差越界发生在 `q≈0.893`，明显早于 `q=0.5`，所以不能把首个不闭合归因于 Bouzidi 两个插值分支的切换。

但 step 5000 越过 `q=0.5` 后，残差每步下降和 rho 抬升明显加速：`R_pop` 从step 5000的
`-1.73845e-3`降至step 5323的`-2.63605e-3`，同时 `rho_max` 从1.06140升至1.20123。这说明 `q<=0.5` 分支可能放大已经存在的连续闭合偏差，是次级重点，而不是最初来源。现有CSV没有逐步、逐link population before/after，因此不能从这些冻结输出进一步把该加速量分摊到单条link；本报告不虚构这一分解。

## 5. 对四类检查的回答

1. **所有后续link transition是否执行ownership transfer？** step 3595后没有后续ownership transition需要执行。每步只更新相同owner/direction的q与壁速，故transfer计数为0是符合代码定义的，不是遗漏证据。
2. **是否有old link失活而new link未建立？** 在逻辑link身份层面没有：active count恒为32,176，material/owner/direction不变。字段先清后写不等于link ownership失活。
3. **是否有同一link多个writer？** 事件步v5为单一复合writer；后续标准Bouzidi路径记录的writer conflict为0。现有证据没有重复writer。
4. **残差与哪次transition对应？** 不对应任何后续离散transition。首次越界为step 3918；此时距唯一transition已323步。

## 6. 三个最终问题

1. **为什么0→3 nm通过而0→10 nm失败？** 0→3 nm末态只以约`1.26e-5`的裕量低于阈值；同一批persistent links的连续q/壁速更新与标准Bouzidi推进产生的小偏差继续积累，在step 3918越界，并在q跨过0.5后显著加速。
2. **哪一个后续移动阶段首次产生不可接受残差？** step 3918、位移`3.033696378 nm`的`R_pop=-1.000968626e-3`；`R_corrected`于step 3939越界。两者均不是link ownership transition时刻。
3. **下一步唯一修复点？** 不应继续扩展old→new `transitionMap`。唯一应定位的代码路径是**无material事件时，同一owner link由 `q_old` 更新到 `q_new` 后的标准moving-Bouzidi PostStream与alpha移动控制体质量之间的逐link闭合**，重点同时覆盖q约0.9的首次累计偏差和q跨0.5后的加速。任何修复前应先在该persistent-link路径输出逐link `before streaming / after streaming / after Bouzidi` 的质量交换；不得把事件transfer应用到不存在ownership变化的步骤。

## 停止点

STEP 5-G完成的是只读诊断，并明确排除了“连续运动中重复ownership transition遗漏”这一假设。当前仍为**STEP 5 FAIL**；没有修改源码、物理参数或历史结果，没有重新运行仿真，也没有进入STEP 6。

Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is **SIM-EC1XT240**.
