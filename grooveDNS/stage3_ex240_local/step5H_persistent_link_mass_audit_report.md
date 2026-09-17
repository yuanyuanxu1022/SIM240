# SIM-EC1XT240 STEP 5-H persistent moving Bouzidi link mass closure audit

## 判定

**逐 link 审计未能由现有冻结输出完成；不得给出虚构的 link 排名或根因。**

本轮严格遵守“禁止修改代码、只做审计”：只读取 `SIM_EC1XT240_CURRENT_STATE.md`、STEP 5-F v5源码和其既有0→10 nm输出，没有修改程序、Bouzidi公式、q、壁速、参数或阈值，也没有重新运行仿真。

现有结果足以证明误差发生在没有 ownership transition 的 persistent-link 阶段，但不足以把质量变化分配到具体 cell/direction。STEP 5仍为FAIL，不进入10 nm重跑或STEP 6。

## 1. 可用数据与缺失数据

既有 `step5F_history.csv` 每步保存：active-link总数、ownership-transition计数、全局`M_pop`、出口累计通量、残差、rho和Mach。它没有保存：

- 每条persistent link的`q(n)`与`q(n+1)`；
- streaming前后的owner/neighbor populations；
- Bouzidi PostStream覆盖前后的population；
- 每条link的质量贡献。

`link_transition_map.csv`和`link_transition_population_ledger.csv`只记录step 3595的material/ownership事件。step 3596–3918没有对应逐link记录。`run.log`与manifest也不含这些量。

因此任务要求的真实`delta_mass_link`、top100 positive和top100 negative无法离线恢复。全局质量差是所有collision、streaming、Zou/He和Bouzidi作用的合计，不能唯一反演成32,176条link的贡献；任何这样的排名都会是编造。

## 2. step 3595→3918的确定量

|step|位移 (nm)|active links|ownership transition|`R_pop`|水平移动壁代表q|
|---:|---:|---:|---:|---:|---:|
|3595|2.501015275|32,176|11,708 old；11,136 transfer|`-8.361509071e-4`|0.999796945|
|3898|2.999688538|32,176|0|`-9.873767702e-4`|0.900062292|
|3918|3.033696378|32,176|0|`-1.000968626e-3`|0.893260724|

在3596–3918的323步中：

- active-link计数每步均为32,176；
- `transition_old_links/exact_pairs/transferred_links`每步均为0；
- writer conflict、非法link、periodic mismatch和material conversion均为0；
- q连续变化，但没有owner、material或direction变化。

从step 3595到3918：

```text
delta R_pop = -1.64817718942e-4
delta mass  = -1.18668757638e-21 kg   (M0=7.1999999999931e-18 kg)
```

必须注意，step 3595开始时已有`R_pop=-8.3615e-4`。所以step 3918的约`1e-3`累计残差中，约83.5%在本审计区间开始前已经存在；3595→3918阶段新增约16.5%。不能把完整`1e-3 M0`全部归给3595后的persistent links。

## 3. 对三个候选机制的判断

### q连续变化

**与新增残差同时存在，但尚不能证明因果或定位具体link。** 同一批link在此区间将q从约0.9998连续更新到约0.8933，全局残差新增`1.18669e-21 kg`。由于缺少逐算子population，无法区分该量来自Bouzidi写入、moving-control-volume离散积分、Zou/He通量积分或它们之间的时间层不一致。

### q=0.5分支切换

**明确排除为3.033696 nm首次超限原因。** step 3918时q约0.8933；q=0.5直到step 5000、位移5 nm才发生。后者与更晚的误差加速相关，但不在本轮3595→3918范围内，也不是首次越界来源。

### moving-wall correction缺项

**现有数据不足以逐link判定。** 当前`R_corrected`只包含已有定义的wall项，不能从全局残差判断标准moving Bouzidi每条link是否还需要独立交换项。未经逐link Reynolds/control-volume离散推导，不能把观测差直接命名为“缺失壁面质量”。

## 4. 空间集中性

现有冻结输出没有逐link贡献，因此不能可信回答误差集中于水平凸台底面、槽顶还是压力边界附近。

可识别的几何候选集合仅为step 3595建立的11,136条移动壁精确links：方向12有2,304条，方向7、9、15、17各2,208条。该计数不是质量贡献，不能用于top100排序，也不能据此判定压力边界区域是主因。

## 5. 必须回答的三个问题

1. **3.033696 nm首次超限的具体link来源？** 现有数据无法识别。能确定的是：它不对应ownership/material事件，不是q=0.5分支切换，也没有非法或重复writer；超限发生在相同32,176条link持续更新期间。
2. **累计1e-3残差由哪些link贡献？** 无法从冻结输出分解。step 3595→3918只新增`1.64818e-4 M0`（`1.18669e-21 kg`），完整`1e-3`的大部分在step 3595前已累计。没有逐link前后population就不存在可验证的positive/negative top100。
3. **下一步唯一修复点？** 当前还没有证据支持修改物理算法。唯一允许且必要的下一点是，在不改变演化的诊断副本中，于persistent moving-wall links记录同一时间层的`q_old/q_new`、wall velocity、streaming前后population及Bouzidi覆盖值，并同时记录Zou/He边界通量；随后才能判断应修复的是标准Bouzidi PostStream的连续q交接，还是质量审计/通量的时间层。未获得该账本前不应实施补偿或公式修改。

## 6. 停止点

STEP 5-H得到的是明确的**证据不足判定**，而非数值通过：现有输出不能满足逐link top100要求，且“q连续变化造成质量不闭合”尚未被population级数据证明。按本轮禁止修改代码的约束，到此停止；STEP 5不能关闭，不进入STEP 6。

Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is **SIM-EC1XT240**.
