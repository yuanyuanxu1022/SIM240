# SIM-EC1XT240 STEP 5-D 转换节点 population 策略验证报告

## 判定

**三种策略均 FAIL，没有一种恢复冻结的移动控制体质量闭合标准。** A、B、C 均完成相同的 0→3 nm、
step 3595 首次 2304 节点 `fluid -> solid` 转换和后续至 step 3898 的推进；三组均无 NaN/Inf、无非法 link、
rho 与 Mach 稳定。但是：

|策略|`max |R_pop|`|`max |R_corrected|`|门槛|判定|
|---|---:|---:|---:|---|
|A：`rho=1,u=0` equilibrium|`1.20588830917e-3`|`1.19283911580e-3`|`<1e-3`|FAIL|
|B：原节点 `rho_pop,u=0` equilibrium|`1.02356607790e-3`|`1.01051688452e-3`|`<1e-3`|FAIL|
|C：持久流体邻居平均 `rho,u=0` equilibrium|`1.16159074806e-3`|`1.14854155469e-3`|`<1e-3`|FAIL|

B 最接近门槛且是唯一在转换瞬间保持逐节点密度及总 stored-population mass 的策略，但仍超出
`1.051688452e-5`。没有放宽门槛，不能进入 10 nm。

## 冻结范围与实现

新增独立程序：`step5_5_dynamic_material/step5D_population_strategy_test.cpp`。它从 STEP 5.5 v3/mass-audit
代码复制，A/B/C 由命令行选择。三组之间唯一的演化差异是转换节点切换为 `NoDynamics` 后、Bouzidi link 刷新前的
`f0...f18` 初始化。

保持不变：

- SIM-EC1XT240 几何、dx、material 转换位置和2304节点计数；
- h(t)、dt、tau、壁速和0→3 nm目标；
- D3Q19 lattice、BGK、moving Bouzidi、Zou/He压力边界及x周期；
- topology commit、dynamics切换、link更新及推进顺序；
- `R_pop` 和 STEP 5-C 的有符号 `M_wall_motion` 修正口径；
- Mach、rho、非法link及`1e-3`质量门槛。

本机 OpenLB `equilibrium<D>::secondOrder` 实现位于
`/home/dell/openlb/src/dynamics/lbm.h:49-70`，并在返回值中减去 lattice weight，符合当前 shifted-population
存储。三种策略均直接用该实现生成19个 equilibrium populations，没有使用未移位的外部公式。

策略定义：

- A：所有转换节点目标 `rho=1,u=(0,0,0)`；
- B：每个节点用转换前 `rho_pop=1+sum(f_i)`，仅把速度置零；
- C：对转换提交后仍为 material 1/4/5 的一链 D3Q19 邻居计算 `rho_pop` 算术平均，速度置零；x邻居按实际周期映射。每个转换节点使用3–9个持久流体邻居。

没有向其他节点分配质量，没有全域归一化、补偿、rho/u裁剪或参数调整。

冻结文件哈希未变：

- STEP 4：`9444c61aab6cc67499211f2724d109923d91d9bc0fe66747446acf2da5e399e2`；
- STEP 5.5 v3程序：`ba43135d72f5e09cb9e61537a692a5c690283d69d3cbbe6c6ff494b635102554`；
- topology manager：`a267132ce080251a49248894e212da6f1a516149b483fb661c8e7fe4dacffe57`；
- STEP 5-D程序：`253d34e29999a5b46db3bfd69ea3c3c0d8d042f30f5ff584a96e5d5a738ca2e7`。

## 转换瞬时 population 与质量账本

共同转换位置为 step 3595、位移 `2.50101527518 nm`，转换节点数均为2304。

|量|A|B|C|
|---|---:|---:|---:|
|目标rho范围|`[1,1]`|`[0.994405814,1.109679905]`|`[0.968245617,1.017972366]`|
|`sum alpha*rho_pop`，转换前|`1181.042300434`|`1181.042300434`|`1181.042300434`|
|`sum alpha*rho_pop`，初始化后|`1151.532161198`|`1181.042300434`|`1159.335098906`|
|alpha加权瞬时质量变化|`-3.68876740449e-21 kg`|`-8.53e-35 kg`|`-2.71340019103e-21 kg`|
|未加alpha的stored质量变化|`-7.38053211741e-21 kg`|0|`-5.42900515573e-21 kg`|
|初始化后最大动量|0|0|0|
|目标rho恢复误差|0|`1.11e-15`|`1.11e-15`|

A 和 C 会在新solid节点的存储层面直接改变质量；这是各自定义的 equilibrium 初始化结果，不是出口排液，也没有被记作补偿。
B 将每个节点原密度投影到零速度 equilibrium，因此转换瞬时总 stored mass 保持到舍入精度，只删除非平衡和动量信息。

三组墙面扫掠项完全相同：`deltaM_wall=-9.39541922710e-23 kg`。

## step 3594/3595/3596 残差

### A：rho=1 equilibrium

|step|`R_pop`|`R_corrected`|
|---:|---:|---:|
|3594|`-8.41169493221e-4`|`-8.41169493221e-4`|
|3595|`-9.97022461551e-4`|`-9.83973268180e-4`|
|3596|`-9.99321615729e-4`|`-9.86272422358e-4`|
|3898|`-1.20588830917e-3`|`-1.19283911580e-3`|

### B：原rho_pop equilibrium

|step|`R_pop`|`R_corrected`|
|---:|---:|---:|
|3594|`-8.41169493221e-4`|`-8.41169493221e-4`|
|3595|`-6.61224399412e-4`|`-6.48175206041e-4`|
|3596|`-6.73091694912e-4`|`-6.60042501541e-4`|
|3898|`-1.02356607790e-3`|`-1.01051688452e-3`|

### C：邻居平均rho equilibrium

|step|`R_pop`|`R_corrected`|
|---:|---:|---:|
|3594|`-8.41169493221e-4`|`-8.41169493221e-4`|
|3595|`-9.07223927268e-4`|`-8.94174733897e-4`|
|3596|`-9.11162535502e-4`|`-8.98113342131e-4`|
|3898|`-1.16159074806e-3`|`-1.14854155469e-3`|

所有最大绝对残差均出现在末态 step 3898，而非以 NaN/Inf 结束。

## 稳定性结果

|检查|A|B|C|冻结要求|
|---|---:|---:|---:|---:|
|完成步数|3898|3898|3898|3898|
|最终位移 (nm)|`2.999688538`|同左|同左|不超过3|
|全程rho范围|`[0.986811639,1.109679905]`|同左|同左|`[0.8,1.2]`|
|全程最大Mach|`1.050757061e-3`|同左|同左|`<=0.05`|
|NaN/Inf|0|0|0|0|
|非法link|0|0|0|0|
|periodic mismatch|0|0|0|0|
|dynamics error|0|0|0|0|
|material转换|2304|2304|2304|2304|

三组 active-fluid rho/Mach 轨迹相同，说明这些初始化主要改变已经转为 `NoDynamics` 的solid-side stored populations；
它们没有在本测试区间引发新的流体稳定性问题。运行正常完成不等于质量验收通过，三个进程均以退出码3记录冻结门槛失败。

## 结论

1. A不能保持转换节点stored mass，且最终质量残差与原保留策略接近，FAIL。
2. C使用邻居平均密度仍删除显著stored mass，最终残差虽优于A但仍FAIL。
3. B在转换瞬时严格保质量并给出三者最小残差，证明“保留rho、删除动量/非平衡”对账本有明显改善；但
   `max|R_corrected|=1.01051688452e-3` 仍超过冻结标准，不能以接近门槛为由判PASS。
4. 因此三种转换节点 equilibrium 初始化均未完整恢复移动控制体质量闭合。剩余误差不能仅归因于转换节点的初始
   populations，还需审计转换后solid-side populations是否应继续计入 `M_pop`、以及其与Bouzidi/streaming的离散交换定义。

**STEP 5-D FAIL；停止，不进入0→10 nm。**

## 输出

- 程序：`step5_5_dynamic_material/step5D_population_strategy_test.cpp`；
- 构建目标：`step5d-population-strategies`；
- A：`step5_5_dynamic_material/output/step5D_strategy_A_0to3nm_v1_20260909/`；
- B：`step5_5_dynamic_material/output/step5D_strategy_B_0to3nm_v1_20260909/`；
- C：`step5_5_dynamic_material/output/step5D_strategy_C_0to3nm_v1_20260909/`。

每个目录包含 `first_conversion_history.csv`、`population_strategy_event_audit.csv`、逐节点转换前后 populations、
`result.txt`、`run_manifest.txt` 和 `run.log`。没有运行10 nm或加入两相、液滴、润湿、空气和参数扫描。

Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is **SIM-EC1XT240**.
