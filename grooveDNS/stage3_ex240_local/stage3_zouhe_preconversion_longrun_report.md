# SIM240阶段三步骤4：Zou/He转换前延长观察报告

## 最终判定

**STEP 4 LONG-RUN FAIL**

长程程序按冻结异常规则在step 1156自动停止，未完成计划的2000步。触发原因不是
NaN/Inf、Mach、rho、非法link或材料转换，而是原始相对质量收支残差达到
`1.0019248003741814e-3`，超过冻结门槛`1e-3`。退出码为3，不能把程序正常保存现场
解释为验证通过。

因此步骤4尚不具备正式验收条件，**不允许进入步骤5单次材料转换账本**。本轮没有运行
完整10 nm、材料转换、液滴、润湿、空气、网格扫描或扩域。

## 首次材料转换预测与轨迹选择

预测严格复用`explicit_piston_10nm.cpp`中的实际`matAt/punch/coverNodes`逻辑，而不是
仅按几何图片估计。初始`h=75 nm`时，凸台下最近流体节点中心为`z=72.5 nm`，下一层
实体节点中心为`z=77.5 nm`。首次fluid→solid发生条件是原流体材料节点在新h下满足
`punch=true`，所以连续阈值为`h=72.5 nm`。

- step 3594：`h=72.50057511724961 nm`，尚未转换；
- 预计首次转换step 3595：`h=72.49898472482263 nm`；
- 对应时间`3.595e-8 s`、位移`2.501015275177366 nm`；
- 对应壁速`-0.1590392436517845 m/s`，格子壁速`-3.18078487303569e-4`。

计划step 2000时原轨迹仅到`h=74.4208 nm`，距阈值仍有`1.9208 nm`，所以按用户规则
无需提前减速或hold，可以持续沿原五次轨迹运动。本次实际在step 1156提前失败并停止，
此时仍距阈值`2.371067840321012 nm`。完整计算见
[`first_conversion_threshold_prediction.txt`](first_conversion_threshold_prediction.txt)。

## 实现和回归

新增独立程序
[`explicit_piston_zouhe_preconversion_longrun.cpp`](explicit_piston_zouhe_preconversion_longrun.cpp)，
没有覆盖第三候选源码或历史输出。它保留：

- Zou/He全压力面、moving Bouzidi和等参考压力开放排液；
- x周期及192条跨周期固壁link修复；
- 原几何、`dx=5 nm`、`dt=1e-11 s`、物性、BGK、单位映射和五次轨迹；
- Mach `<=0.05`、rho `[0.8,1.2]`和质量收支`<=1e-3`门槛；
- 原始质量与两端有符号通量的梯形积分账本。

程序没有旧f8/f17交线材料补丁，也没有任何材料转换、密度归一化、质量补偿或rho/u/q
裁剪。2400个压力节点全部审计为正确的平面±y法向，零法向和其他法向均为0。

编译前两次失败分别来自独立文件入口宏冲突和新文件局部常量遗漏；二者均在独立程序内
修复，第三次无警告编译通过。没有修改OpenLB库。构建命令为：

```text
make openlb-zouhe-preconversion-longrun
```

先运行无补丁650步回归：

```text
mpirun -np 1 ./explicit_piston_zouhe_preconversion_longrun regression
```

run-id为`zouhe_preconversion_nopatch_regression650_20260908`，退出码0。其rho、Mach、
速度和两端通量逐步与此前`Cnopatch-C650`完全相同；质量求和最大差仅
`4.622231866529366e-33 kg`，属于求和顺序舍入。回归最大Mach
`6.1829116816418037e-05`，rho=`[0.99987883917914711,1.0002955951371546]`，最大相对
质量残差`1.9439259979607998e-4`。

随后唯一长程命令为：

```text
mpirun -np 1 ./explicit_piston_zouhe_preconversion_longrun longrun
```

run-id为`zouhe_preconversion_longrun2000_20260908`，请求2000步，实际完成1156步，退出
码3。所有现场、step 0/650/1156材料与速度VTK及最后20步记录均已保留。

## A. 实际运行方式

|项目|实际值|
|---|---:|
|请求/完成step|2000 / 1156|
|moving phase|step 1–1156，共1156步|
|decelerating phase|0步|
|hold phase|0步，未执行|
|停止物理时间|`1.156e-8 s`|
|停止h|`74.871067840321004 nm`|
|实际位移|`0.12893215967899063 nm`|
|停止壁速|`-0.03133341471674702 m/s`|
|距首次转换阈值|`2.371067840321012 nm`|

没有突然停壁作为物理轨迹的一部分；step 1156的停止是验收异常触发后的计算终止。由于
预测允许整个2000步持续运动，本方案原本无需hold。实际未到计划终点，因此hold阶段的
衰减/自增长性质没有得到验证。

## B. 最大/最小指标

|量|结果|
|---|---:|
|max Mach|`1.7544514282122255e-4`，step 1156，cell `(38,0,14)`|
|max速度|`0.050646650217922591 m/s`，step 1156，cell `(38,0,14)`，方向为+y|
|rho范围|`[0.99946159764786402,1.0042447389132079]`|
|最大绝对相对质量残差|`1.0019248003741814e-3`，step 1156|
|停止时raw质量残差|`7.2138585626887823e-21 kg`|
|低y向外通量范围|`[0,5.4771319096775026e-13] kg/s`|
|高y向外通量范围|`[0,5.4771319096775511e-13] kg/s`|
|净向外通量范围|`[0,1.0954263819355054e-12] kg/s`|
|累计流入/流出|`0 / 4.708898992248853e-21 kg`|

两端通量始终同号向外，最大相对不对称仅`1.6867e-12`，所以出口符号和对称性仍有
物理意义。但域内质量从`7.1999999999946862e-18`增至
`7.2025049595651261e-18 kg`，与累计向外量相加后形成超限残差。这里保持了冻结原始
账本，没有从残差中扣除未经验证的移动壁“修正项”。

分段结果为：

|区间|max Mach|max rho偏差|max相对质量残差|净向外通量上限 (kg/s)|
|---|---:|---:|---:|---:|
|step 0–200 初始瞬态|`7.35645e-6`|`9.18292e-6`|`6.08005e-6`|`4.47197e-14`|
|step 201–650 早期移动|`6.18291e-5`|`2.95595e-4`|`1.94393e-4`|`4.20287e-13`|
|step 651–1156 延长移动|`1.75445e-4`|`4.24474e-3`|`1.00192e-3`|`1.09543e-12`|

## C. f3/f8/f17与趋势

历史cell `(0,0,13)`、`(0,0,14)`、`(0,0,15)`和`(0,1,15)`每步均有记录。到停止
时四个cell的最大绝对值为：

- `max|f3|=2.9694830005847124e-4`；
- `max|f8|=4.213896017090142e-4`；
- `max|f17|=4.2407026242083536e-4`。

原LocalPressure的f3/f8/f17反向爆发没有重新出现：截至停止，局部Mach仍仅
`O(1e-4)`，population符号和量级保持Zou/He候选的移动响应。但最后600步中三者均
随不断增大的壁速单调增加，末/初比分别为`7.82`、`7.13`和`8.44`，未达到冻结的
“比值>=10”指数爆发组合条件。

趋势检测同时发现：rho偏差末/初比`22.50`、log-linear `R²=0.9873`、e-folding
`182.0 step`，触发预先冻结的潜在延后增长标志。质量残差最后600步也100%逐步增加，
末/初比`8.07`；虽然未满足指数标志的比值条件，但已实际越过硬门槛。因此不能把当前
结果解释为“只是随加载平稳增长”。Mach和速度的末/初比为`3.71`，未触发指数标志。

## D. 边界与几何

|检查|结果|
|---|---:|
|压力节点/正确平面法向|2400 / 2400|
|零法向/其他法向|0 / 0|
|每步恢复的跨周期固壁link|192|
|非法link最大值|0|
|错误周期实体link最大值|0|
|材料转换|0|
|材料变化节点|0|
|流体节点数|57600，保持不变|

所以本次失败发生在首次材料转换之前，不能归因于节点转换账本、周期link遗漏或材料场
变化。

## E. 最终判定和后续权限

`STEP 4 LONG-RUN FAIL`

未满足的硬条件至少有：未完成2000步、相对质量收支残差超过`1e-3`、rho偏差触发冻结
趋势标志，并且因提前停止没有获得计划窗口或hold证据。Ma、rho绝对范围、有限性、
link和材料条件虽仍合格，不能抵消失败项。

**不允许进入步骤5单次材料转换账本。** 若后续继续，应仍停留在步骤4，首先解释并
验证移动亚格点边界下原始域质量增加与向外通量同时为正所形成的账本残差；不得通过
质量归一化、人工补偿或放宽`1e-3`来改判。

## 交付文件

- 冻结协议：[`preconversion_longrun_frozen_protocol.md`](preconversion_longrun_frozen_protocol.md)
- 转换预测：[`first_conversion_threshold_prediction.txt`](first_conversion_threshold_prediction.txt)
- 独立源码：[`explicit_piston_zouhe_preconversion_longrun.cpp`](explicit_piston_zouhe_preconversion_longrun.cpp)
- 后处理：[`analyze_preconversion_longrun.py`](analyze_preconversion_longrun.py)
- 运行manifest：[`preconversion_longrun_run_manifest.txt`](preconversion_longrun_run_manifest.txt)
- 结果目录：`output/zouhe_preconversion_longrun2000_20260908/`
- 全局历史：`preconversion_longrun_global_history.csv`
- population历史：`preconversion_longrun_population_watch.csv`
- 最后20步现场：`preconversion_longrun_last20_global.csv`和
  `preconversion_longrun_last20_population.csv`
- 趋势与分段统计：`preconversion_longrun_trend_analysis.csv`、
  `preconversion_longrun_phase_summary.csv`
- 最终机器判定：`final_assessment.txt`

