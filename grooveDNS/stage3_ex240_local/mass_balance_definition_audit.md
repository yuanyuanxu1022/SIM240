# SIM-EC1XT240 步骤4质量收支定义审计

> Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is `SIM-EC1XT240`.

## 审计对象

审计对象为冻结程序`explicit_piston_zouhe_preconversion_longrun.cpp`、新增独立诊断程序
`explicit_piston_zouhe_mass_drift_diagnosis.cpp`以及本机OpenLB实际源码。诊断保持原Zou/He、
moving Bouzidi、192条跨x周期固壁link修复、单位映射、物性、轨迹和压力值不变；没有材料
转换或质量补偿。

## 现有流体质量 `M_f`

现有实现逐个遍历block的`forCoreSpatialLocations`，只累计材料1、4、5：

\[
M_f=\rho_{phys}\,\Delta x^3\sum_{\text{core},\;m\in\{1,4,5\}}\rho_k.
\]

- 材料1为普通流体，4/5为两端压力边界流体，因此压力边界cell包含在质量中。
- 材料2/3固体不统计。
- `forCoreSpatialLocations`在本机OpenLB `src/core/blockStructure.h:343`只遍历
  `0 <= i_d < core[d]`，不遍历padding/overlap；本次强制单MPI rank，所以不存在MPI重复和
  halo重复累计。
- overlap为3，只用于邻域和通信，不进入质量和通量面积求和。
- 每个被选cell统一使用`dx^3`；没有Bouzidi cut-cell体积分数，也没有按连续壁面位置缩放。
- OpenLB使用shifted population：`src/dynamics/lbm.h:290-297`给出
  `rho = 1 + sum_i f_i`。质量统计调用`cell.computeRho()`，与该存储定义一致。

原SIM-EC1XT240局部几何在转换前共有57,600个流体材料cell，名义全格点体积
`7.2e-21 m^3`。材料标签不变时，这个名义体积恒定，即使连续Bouzidi壁面已经下移。

## 现有宏观出口质量

压力面材料4位于低y端、外法向为-y；材料5位于高y端、外法向为+y。每次统计：

\[
\dot M_{out}^{macro}=
\sum_{m=4}-\rho\rho_{phys}u_y^{phys}\Delta x^2+
\sum_{m=5}+\rho\rho_{phys}u_y^{phys}\Delta x^2.
\]

现有长程程序把正、负部分分成`cumulative_out_mass`和`cumulative_in_mass`，用相邻两个
采样时刻的梯形公式乘`dt`积分。面积为每个压力cell的`dx^2`；材料4/5全平面均统计，
包括靠近固壁的平面cell。x周期端点没有额外复制，core cell只统计一次；单rank下没有MPI
reduction重复。原残差为：

\[
R_{macro}=M_f(t)-M_f(0)+M_{out}^{macro}(0,t)-M_{in}^{macro}(0,t).
\]

## 新增population级通量

新增诊断在collision之后、streaming之前，对材料4/5上跨开放面的D3Q19方向直接求和。
低y端采用`c_y<0`为outgoing，高y端采用`c_y>0`为outgoing：

\[
\Delta M_{out}^{pop}=\rho_{phys}\Delta x^3
\sum_{face,i}s(face,c_{iy})\,[f_i+w_i].
\]

代码显式恢复`F_i=f_i+w_i`。相反方向的权重相等，因此常量偏移在净通量中抵消，但显式
恢复避免把shifted population误作完整分布。该量每个lattice step矩形累加；它与宏观
梯形积分使用不同时间层，因此不预设两者逐位相等。

M1的2000步结果中，宏观累计净质量为`-3.839999997861e-26 kg`，population累计为
`-4.266666662913e-26 kg`；差值`4.266666650516e-27 kg`等于约一个末端稳态step通量。
对应初始质量的population残差为`-8.33336e-9`，远小于原长程`1e-3`量级；宏观残差为
`-2.55e-14`。因此两者不逐位相同，但没有发现能解释原`1e-3`漂移的压力通量漏算。

## 算子级质量快照

新增程序使用本机公开的`lattice.collide()`和`lattice.AndStream()`。OpenLB
`src/core/superLattice.hh:664-709,728-780`显示完整顺序为：PreCollide处理、collision、
PostCollide通信、block streaming、PostStream处理器（含moving Bouzidi）、custom task、
PostPostProcess通信。应用层可安全取得：

1. collision前质量；
2. collision后质量；
3. `AndStream`完成后的质量。

但`AndStream`内部的streaming、Bouzidi PostStream和最终communication不能通过当前公开
调用无侵入逐项暂停。因此报告只把误差定位到这个合并阶段，不伪称已经区分其中每个算子。

## 连续体积与全格点体积

转换前连续几何体积独立计算为：

\[
V_{geom}(t)=V_{geom}(0)-L_xL_y[75\,nm-h(t)],
\qquad V_{geom}(0)=7.2\times10^{-21}\,m^3.
\]

材料cell数和名义lattice体积保持不变。连续扫掠体积只作为诊断列输出，没有直接加入或
扣除任何质量残差，也没有用于使案例“通过”。

