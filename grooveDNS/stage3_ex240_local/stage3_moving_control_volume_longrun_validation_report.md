# SIM-EC1XT240 步骤4移动控制体积长程验证报告

> Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is `SIM-EC1XT240`.

## 判定

解析alpha体积验证、封闭M2复核和开放C 2000步均通过。质量门槛仍为`1e-3`，没有调整
物性、壁速、dt、q、压力或轨迹，也没有质量归一化或补偿。2000步位移`0.5792 nm`，距离
预计首次材料转换仍约`1.9208 nm`，材料转换实际为0。

**步骤4可以按“转换前移动控制体积长程门禁”关闭，但仍不允许自动执行步骤5。步骤5只可
进入设计与人工审核，不能在本轮运行单次转换。**

## Alpha与体积验证

alpha是cell的z向控制体积与连续流体区`0 <= z <= z_punch(x,h)`的解析交长除以dx，并
截断到`[0,1]`。x分界与控制体积面重合，因此没有x向部分覆盖。alpha完全由几何决定，
不读取任何质量或残差。

8个指定检查点的alpha积分与解析`V_f`最大绝对差为`2.12304e-33 m^3`，最大相对差为
`2.96239e-13`。几何验证通过后才执行M2和开放C。

## M2封闭moving复核

run-id：`moving_control_volume_M2_closed_2000_v2_20260908`。

|量|结果|
|---|---:|
|完成步数/退出码|2000 / 0|
|位移|`0.5792 nm`|
|最大Mach|`2.63425e-4`|
|rho范围|`[1,1.01985579]`|
|`R_full/M_full(0)`|`4.40597e-3`|
|`R_geom/M_geom(0)`|`-2.58419e-4`|
|最大绝对`R_geom`|`2.58419e-4`|
|非法link/材料转换/材料变化|0 / 0 / 0|

局部rho×alpha的最终残差为`-2.58419e-4`。粗略的`average rho * V_f`残差为
`-2.48047e-4`，两者相差初始质量的`1.03721e-5`。差异来自边界附近rho非均匀；因此生产
诊断使用局部rho加权，而不使用全局平均rho代理。

相较旧full-cell残差，geometry-aware残差降低约17倍并通过冻结门槛。仍残留的
`2.58e-4`可能包含cut-cell用cell中心rho近似的空间误差和moving Bouzidi离散质量交换；
当前证据没有显示超过门槛、无法由移动控制体积解释的净质量源。

## 开放C 2000步结果

run-id：`moving_control_volume_C_open_2000_v2_20260908`。保持Zou/He、moving Bouzidi、x周期、
192条跨周期固壁link修复、无旧f8/f17补丁和原连续轨迹。

|量|结果|
|---|---:|
|完成步数/退出码|2000 / 0|
|最终h/位移|`74.4208 nm` / `0.5792 nm`|
|最大Mach|`4.34610e-4`|
|最大速度|`0.125461 m/s`|
|rho全过程范围|`[0.997560668,1.022618246]`|
|`R_full_macro`|`4.490839e-3`|
|`R_full_population`|`4.488963e-3`|
|`R_geom_macro`|`-1.687520e-4`|
|`R_geom_population`|`-1.706276e-4`|
|最大绝对`R_geom_macro`|`1.687520e-4`|
|累计macro流入/流出|`8.64285e-23` / `2.05252e-20 kg`|
|累计population流入/流出|`9.97413e-17` / `9.97617e-17 kg`|
|非法link/材料转换/材料变化|0 / 0 / 0|

population的incoming/outgoing各自包含相互抵消的平衡population，故单项远大于净通量；
population净流出为`2.04252508e-20 kg`，macro净流出为`2.04387556e-20 kg`，相差
`0.0661%`。两套`R_geom`相差`1.87568e-6`个初始质量，均通过`1e-3`。

开放C用`average rho * V_f`得到的粗略macro残差为`-1.50416e-4`，与局部rho×alpha正式值
相差`1.83358e-5`。局部方法保留切割层的实际rho分布，因此作为正式诊断量。

## f3/f8/f17

历史异常cell`(0,0,14)`的监测值：

|step|f3|f8|f17|
|---:|---:|---:|---:|
|650|`5.86042e-5`|`8.15993e-5`|`-7.59624e-5`|
|1156|`2.96235e-4`|`4.20368e-4`|`-4.05745e-4`|
|2000|`1.31533e-3`|`1.89578e-3`|`-1.85633e-3`|

三者与累计位移的相关系数绝对值分别为`0.999995`、`0.999998`、`0.999988`，符号和幅值
随平滑加载连续变化。全域全过程最大绝对值分别为`0.0013171`、`0.0099010`、`0.0098857`；
没有原LocalPressure方案的反向高速反馈、Mach超限或rho爆发。

## 旧step 1156 FAIL重新分类

新程序在完全相同轨迹的step 1156复现旧指标：

- `R_full_macro=1.0019248004e-3`，与冻结旧CSV一致；
- `R_geom_macro=-3.0469094e-5`；
- `R_geom_population=-3.1229807e-5`；
- 连续扫掠体积`7.4264924e-24 m^3`；
- full-cell平均rho`1.0003479111`。

因此属于选项B：geometry-aware residual已在`1e-3`门槛内。旧记录继续保留为
`OLD FULL-CELL METRIC FAIL`，没有删除或改写；新的证据表明旧验收量不适用于连续移动控制
体积。

## 必答结论

1. alpha按连续压头表面与cell控制体积的解析交长定义。
2. alpha完全由几何独立取得，没有从质量残差拟合。
3. alpha体积积分最大相对误差`2.96239e-13`。
4. M2旧`R_full=4.40597e-3`。
5. M2新`R_geom=-2.58419e-4`。
6. 未发现超过冻结门槛且不能由移动控制体积解释的moving Bouzidi净质量源；残余离散误差
   仍需在未来网格/边界精度验证中量化。
7. 旧step1156的新`R_geom_macro=-3.04691e-5`，在门槛内。
8. 开放C2000的稳定性、rho、两套残差、出口通量和population监测均见上表，全部满足门禁。
9. 原`1e-3`门槛通过，没有放宽。
10. 可以正式关闭步骤4的转换前长程门禁。
11. 可以在人工审核后**设计**步骤5单次材料转换账本；本轮不允许执行步骤5。

## 文件与可复现性

- 独立程序：`explicit_piston_zouhe_moving_control_volume_longrun.cpp`；
- 几何验证：`geometry_volume_fraction_validation.csv`；
- M2/C历史：各v2 run-id内的`moving_control_volume_longrun_history.csv`、`result.txt`、
  `run.log`和`run_record.txt`；
- v1输出完整保留，CSV与v2逐字节相同；v1目录新增`provenance_note.txt`说明源依赖整理。
- 上一轮`explicit_piston_zouhe_mass_drift_diagnosis.cpp`已恢复原SHA-256
  `a9b67e669fbd4f410f09d32b0daf4355862ae74f245f3660f014237b44c77b58`。

没有触发材料转换、完整10 nm、液滴、润湿、空气、网格扫描或扩域。

`STEP 4 MOVING-CONTROL-VOLUME LONG-RUN PASS`

