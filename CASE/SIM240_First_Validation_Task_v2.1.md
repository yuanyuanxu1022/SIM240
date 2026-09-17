# SIM240 第一阶段 OpenLB 单相流验证与论文基准任务 v2.1

> 状态：冻结执行版（Frozen Protocol）  
> 适用对象：SIM-EC1XT240 固定几何、单相、全充液、低 Reynolds 数输运  
> 本文件是第一阶段唯一任务口径；运行前不得根据预期结果调整定义或验收阈值。

---

## 0. 研究目标、问题与范围

本阶段目标是基于 OpenLB-LBM 建立显式纳米压印周期结构的单相液体输运模型，形成可复现、可比较且可用于论文的水力输运基准。

本阶段回答：

1. OpenLB 对平行板 Poiseuille 流的速度和通量能否达到解析解与网格收敛要求？
2. EX240 沟槽相对于光滑通道是否改变有效输运能力？
3. 观察到的差异来自最大流体高度、流体截面积，还是沟槽拓扑本身？
4. 显式 LBM 能否解析沟槽诱导的速度重构、局部压力扰动和耗散机制？

本阶段不研究：

- 动态压头下压或移动边界；
- FreeSurface、气液界面、接触角、液滴供液与困气；
- 完整工业版图；
- 未经网格验证的大规模参数扫描；
- 纳米尺度滑移、分子层化等非连续介质效应。

本阶段得到的是连续介质、无滑移假设下的固定周期单胞输运响应，不能直接宣称为真实动态压印填充结果。

---

## 1. 第一阶段 Case 与证据链

| Case | 几何 | 主要目的 | 核心输出 |
|---|---|---|---|
| Case01 | 光滑平行板，$H=75\,\mathrm{nm}$ | 解析解与数值方法验证 | $J_{75}$、$K_{75}$、$B_{75}$、解析误差 |
| Case01a | 光滑通道，$H=175\,\mathrm{nm}$ | 最大包络高度对照 | $R_{J,\mathrm{smooth},175}$ |
| Case01b | 光滑通道，$H=125\,\mathrm{nm}$ | 等流体体积/截面积对照 | $R_{J,\mathrm{smooth},125}$ |
| Case02 | EX240 单周期直沟槽，凸台间隙 $h=75\,\mathrm{nm}$ | 沿槽方向拓扑输运 | $R_{J,\mathrm{groove}}$、两种阻力比、局部场 |

证据关系：

- LBM 数值可信性：Case01；
- 最大高度效应：Case01a；
- 等体积/等截面积效应：Case01b；
- 沟槽拓扑效应：Case01a + Case01b + Case02；
- 机制解释：Case02 的速度、局部压力、剪切与耗散分析。

---

## 2. Frozen Simulation Protocol（统一计算协议）

### 2.1 物理参数

所有 Case 固定采用：

$$
\rho_{\mathrm{phys}}=1000\ \mathrm{kg\,m^{-3}},\qquad
\nu_{\mathrm{phys}}=1.0\times10^{-6}\ \mathrm{m^2\,s^{-1}},
$$

$$
\mu_{\mathrm{phys}}=\rho\nu=1.0\times10^{-3}\ \mathrm{Pa\,s}.
$$

流体初始化为格子密度 $\rho_{\mathrm{lat}}=1$、速度 $\mathbf{u}=0$。

### 2.2 坐标、几何和材料

- $x$、$y$ 为面内方向，$z$ 为厚度方向；
- 基底位于 $z=0$；基底和上压头均固定；
- 平面周期尺寸为 $L_x=L_y=240\,\mathrm{nm}$；
- Case02 沟槽轴沿 $+y$；沿 $x$ 的周期结构为 `60 nm mesa + 120 nm groove + 60 nm mesa`；
- 槽深为 $D=100\,\mathrm{nm}$；凸台下方间隙为 $h=75\,\mathrm{nm}$；
- Case02 单胞流体体积对应的参考高度为

$$
H_{\mathrm{ref}}=\frac{V_f}{A_{\mathrm{plan}}}
=75+\frac{120}{240}\times100=125\,\mathrm{nm}.
$$

- material 1：流体；material 2：固定基底；material 3：固定压头；
- 质量、体积、速度积分和通量统计只计 material 1；
- 核心域不存储重复周期端点；overlap 和 padding 不参与物理积分。

### 2.3 LBM 与单位转换

功能网格固定采用：

- lattice：D3Q19；
- collision：ForcedBGK；
- $\Delta x=5\,\mathrm{nm}$；
- $\Delta t=1.0\times10^{-11}\,\mathrm{s}$；
- $\tau=1.7$，$\omega=1/\tau$；
- 单精度禁止；统一使用 `double`；
- 单 MPI rank 完成功能验证；并行扩展必须先通过独立一致性检查。

运动黏度转换必须满足

$$
\nu_{\mathrm{lat}}=\nu_{\mathrm{phys}}\frac{\Delta t}{\Delta x^2},
\qquad
\tau=\frac{\nu_{\mathrm{lat}}}{c_s^2}+\frac12,
\qquad c_s^2=\frac13.
$$

每个 run 必须在 manifest 中记录 OpenLB 版本/commit、源文件 SHA-256、lattice、collision、$\Delta x$、$\Delta t$、$\tau$ 和物理—格子单位转换。

### 2.4 边界与驱动

第一阶段统一使用周期体力驱动，不使用速度入口/压力出口：

- $x/y$ 双周期；
- $z$ 向基底和压头采用固定 halfway bounce-back 无滑移边界；
- Case01、Case01a、Case01b 和 Case02 均沿 $+y$ 施加体加速度；
- 其他体力分量严格为 0；
- 基准体加速度为

$$
a_0=1.0\times10^5\ \mathrm{m\,s^{-2}}.
$$

线性响应检查采用

$$
a\in\{5.0\times10^4,\ 1.0\times10^5,\ 2.0\times10^5\}\ \mathrm{m\,s^{-2}}.
$$

格子体力由

$$
a_{\mathrm{lat}}=a_{\mathrm{phys}}\frac{\Delta t^2}{\Delta x}
$$

换算；$a_0$ 在功能网格上对应 $a_{\mathrm{lat}}=2.0\times10^{-9}$。

周期体力驱动没有入口—出口总压降。等效宏观压强梯度定义为

$$
G=\rho_{\mathrm{phys}}a_{\mathrm{phys}}.
$$

OpenLB 输出的物理压力场仅用于分析单胞内部的局部压力扰动，禁止使用 $p_{\max}-p_{\min}$ 代替总压降或阻力。

如后续需要验证速度入口/压力出口，必须建立独立的开放边界验证任务，不得与本阶段周期结果混算。

### 2.5 网格收敛协议

原计划中的 $\Delta x=10\,\mathrm{nm}$ 不能精确表示 $h=75\,\mathrm{nm}$，会把几何偏移混入网格误差。因此统一网格序列改为：

$$
\Delta x\in\{5.0,\ 2.5,\ 1.25\}\ \mathrm{nm}.
$$

所有尺寸 $60$、$75$、$100$、$120$、$240\,\mathrm{nm}$ 均可被该序列精确表示。采用扩散标度保持 $\tau=1.7$：

| $\Delta x$ | $\Delta t$ | 收敛窗口 | 正式最大步数 |
|---:|---:|---:|---:|
| 5.0 nm | $1.0\times10^{-11}$ s | 1,000 | 30,000 |
| 2.5 nm | $2.5\times10^{-12}$ s | 4,000 | 120,000 |
| 1.25 nm | $6.25\times10^{-13}$ s | 16,000 | 480,000 |

网格收敛只使用 $a=a_0$。Case01、Case01a、Case01b 和 Case02 均必须完成三套网格；两个光滑对照还必须同时报告解析阻力。阻力比采用同网格比值，并对最终比值给出 Richardson 外推或 GCI。不能把 $\Delta x=5\,\mathrm{nm}$ 结果直接称为网格无关结果。

### 2.6 统计量和阻力定义

定义

$$
A_{\mathrm{plan}}=L_xL_y,
\qquad
V_f=\int_{\Omega_f}dV,
\qquad
H_{\mathrm{ref}}=\frac{V_f}{A_{\mathrm{plan}}}.
$$

沿 $y$ 方向的深度积分通量为

$$
J_y=\frac{1}{A_{\mathrm{plan}}}\int_{\Omega_f}u_y\,dV
\qquad [\mathrm{m^2\,s^{-1}}].
$$

输运系数、等效平方长度和主阻力定义为

$$
K_{yy}=\frac{\mu J_y}{\rho a_y}\quad[\mathrm{m^3}],
$$

$$
B_{yy}=\frac{K_{yy}}{H_{\mathrm{ref}}}\quad[\mathrm{m^2}],
$$

$$
R_{J,y}=\frac{\rho a_y}{J_y}=\frac{\mu}{K_{yy}}
\quad[\mathrm{Pa\,s\,m^{-3}}].
$$

对本阶段 $L_x=L_y$ 的周期单胞，亦可报告

$$
Q_y=J_yL_x,
\qquad
\Delta P_{\mathrm{eff}}=\rho a_yL_y,
\qquad
R_y=\frac{\Delta P_{\mathrm{eff}}}{Q_y}=R_{J,y}.
$$

但所有跨 Case 比较以 $J_y$、$K_{yy}$ 和 $R_{J,y}$ 为主，避免在改变域尺寸后误用总流量 $Q$。

两个无歧义阻力比分别为

$$
R^*_{175}=\frac{R_{J,\mathrm{groove}}}{R_{J,\mathrm{smooth},175}},
\qquad
R^*_{125}=\frac{R_{J,\mathrm{groove}}}{R_{J,\mathrm{smooth},125}}.
$$

禁止再使用未注明分母的单一 $R^*$。

### 2.7 Case01 解析解

由于 $x/y$ 均为周期方向，Case01 是无限宽平行板的周期单胞。沿 $y$ 方向体力驱动时

$$
u_y(z)=\frac{\rho a_y}{2\mu}z(H-z),
$$

$$
\bar u_y=\frac{\rho a_yH^2}{12\mu},
\qquad
J_{y,\mathrm{ana}}=\frac{\rho a_yH^3}{12\mu},
$$

$$
K_{yy,\mathrm{ana}}=\frac{H^3}{12},
\qquad
B_{yy,\mathrm{ana}}=\frac{H^2}{12},
\qquad
R_{J,y,\mathrm{ana}}=\frac{12\mu}{H^3}.
$$

数值速度必须在 cell-centred 物理坐标上与解析解比较，不能把格点中心误当作壁面位置。

### 2.8 收敛、稳定性与完成证据

每个正式 run 必须同时满足：

- 最近一个冻结窗口内主通量：`std/abs(mean) <= 1e-6`；
- 最近一个冻结窗口内主通量：`span/abs(mean) <= 5e-6`；
- 两个同方向截面通量相对差 `<= 1e-5`；
- material 1 总质量最大绝对相对漂移 `<= 1e-10`；
- 最大 $|\rho_{\mathrm{lat}}-1|\le 1e-6$；
- 最大 Mach 数 `<= 0.05`；
- 横向交叉通量绝对值 `<= 1e-12 m2/s`；
- material 节点数和材料场在运行前后完全一致；
- 所有统计量无 NaN/Inf；
- 达到上述数值门槛后正常退出，并保存独立退出码 `0`。

“达到收敛窗口”和“进程正常退出”是两项不同证据，必须分别保存。仅有 CSV、结果文件或消失的 PID 不能证明正常退出。

Case01 额外要求：

- $\Delta x=5\,\mathrm{nm}$ 时速度剖面相对 $L_2$ 误差 `<= 2%`；
- $\Delta x=5\,\mathrm{nm}$ 时 $J_y$ 相对解析误差 `<= 2%`；
- 三个驱动力的 $G-J_y$ 线性拟合 $R^2\ge0.999$；
- 三套网格误差总体单调下降；若不单调，必须诊断几何、采样和收敛误差，不能直接外推。

Case02 额外要求：

- 三个驱动力的 $G-J_y$ 线性拟合 $R^2\ge0.999$；
- 三套网格的 $K_{yy}$ 或 $R_{J,y}$ 完成 GCI/外推；
- $R^*_{175}$ 与 $R^*_{125}$ 均报告，不选择性省略不利结果。

---

## 3. 执行顺序与门禁

冻结后的正式运行矩阵共 16 个 run（短测不计入）：

| Case | $\Delta x$ (nm) | $a$ ($\mathrm{m\,s^{-2}}$) | run 数 |
|---|---|---|---:|
| Case01 | 5.0 | $5\times10^4,\ 1\times10^5,\ 2\times10^5$ | 3 |
| Case01 | 2.5、1.25 | $1\times10^5$ | 2 |
| Case01a | 5.0、2.5、1.25 | $1\times10^5$ | 3 |
| Case01b | 5.0、2.5、1.25 | $1\times10^5$ | 3 |
| Case02 | 5.0 | $5\times10^4,\ 1\times10^5,\ 2\times10^5$ | 3 |
| Case02 | 2.5、1.25 | $1\times10^5$ | 2 |
| **合计** |  |  | **16** |

### Gate 0：协议与构建记录

在启动正式计算前完成：

1. 创建独立的第一阶段运行目录，不覆盖历史输出；
2. 固定源文件、OpenLB 版本和编译命令；
3. 写出 `source_manifest.txt` 和源文件 SHA-256；
4. 确认每个 run 使用唯一 run ID 和独立输出目录；
5. 先运行 Case01、$\Delta x=5\,\mathrm{nm}$、$a=a_0$ 的短测。

短测失败时停止，不启动批量计算。

### Gate 1：Case01 数值验证

按顺序执行：

1. $\Delta x=5\,\mathrm{nm}$、$a=a_0$ 正式运行；
2. $\Delta x=5\,\mathrm{nm}$ 的三个驱动力线性响应；
3. $\Delta x=2.5$ 和 $1.25\,\mathrm{nm}$、$a=a_0$ 网格收敛；
4. 输出速度剖面对比、$G-J$ 拟合、误差表和 GCI。

Gate 1 未通过时，不进入结构对照计算。

### Gate 2：Case01a 与 Case01b 对照

在相同物理参数、驱动、网格、周期边界和统计口径下计算：

- $H=175\,\mathrm{nm}$ 最大包络对照；
- $H=125\,\mathrm{nm}$ 等体积/等截面积对照。

两个对照均运行 $\Delta x\in\{5.0,\ 2.5,\ 1.25\}\,\mathrm{nm}$，同时报告数值阻力与平行板解析阻力，并检查误差是否符合 Case01 的趋势。

### Gate 3：Case02 EX240 沿槽输运

按顺序执行：

1. $\Delta x=5\,\mathrm{nm}$、$a=a_0$ 短测；
2. $\Delta x=5\,\mathrm{nm}$ 三个驱动力线性响应；
3. 三套网格的 $a=a_0$ 正式计算；
4. 计算 $J_y$、$K_{yy}$、$B_{yy}$、$R_{J,y}$、$R^*_{175}$ 和 $R^*_{125}$；
5. 输出速度、局部压力、流线、壁面剪切和黏性耗散；
6. 在完成网格检查后解释流线重构、局部速度梯度和阻力来源。

壁面剪切和速度梯度受阶梯边界影响。在相应量完成网格收敛前，只能用于定性解释，不得据此给出强定量结论。

### Gate 4：第一阶段总验收

以下条件全部满足后，第一阶段才可标记 `PASS`：

- Case01 解析验证、线性响应和网格收敛通过；
- Case01a/01b 得到无歧义的光滑参考结果；
- Case02 正常退出、线性响应和网格收敛通过；
- 所有 Case 使用相同的物理参数、边界、驱动和统计定义；
- 每个正式 run 均保存完整日志、CSV、结果、manifest 和退出码；
- 汇总表能够由原始输出重新计算；
- 结论严格限制在固定几何、单相、全充液、连续介质和无滑移范围内。

---

## 4. 文件、表格和图件要求

每个 run 至少保存：

- `run_manifest.txt`：run ID、命令、源文件、哈希、OpenLB 版本、参数和边界；
- `diagnostics.csv`：从初始步到最终步的完整时序；
- `result.txt`：最终统计量、PASS、收敛状态和停止原因；
- `exit_code.txt`：独立保存的实际进程退出码；
- `run.log`：完整标准输出和错误输出；
- `vtkData/`：初始与最终的 material、速度和物理压力场。

第一阶段总表至少包含：

```text
run_id,case,dx_m,dt_s,tau,accel_m_s2,H_ref_m,fluid_nodes,fluid_volume_m3,
steps,normal_exit,converged,max_mass_relative_drift,max_density_deviation,
max_mach,section_flux_relative_difference,Jy_m2_s,Kyy_m3,Byy_m2,
RJ_Pa_s_per_m3,analytic_value,relative_error,Rstar_175,Rstar_125
```

必须形成以下论文图件：

1. Case01 数值/解析速度剖面对比；
2. Case01 与 Case02 的 $G-J$ 线性关系；
3. Case01 和 Case02 的网格收敛/GCI；
4. 四个 Case 的 $K_{yy}$ 或 $R_{J,y}$ 对比；
5. $R^*_{175}$ 与 $R^*_{125}$ 对比；
6. Case02 速度场、流线和局部压力扰动；
7. 全部正式 run 的质量、密度、Mach 和稳态窗口检查。

---

## 5. 后续论文路线

第一阶段通过后才允许进入：

### Case03：横槽方向与输运张量

沿 $+x$ 驱动 EX240，比较

$$
A_R=\frac{R_{J,\perp}}{R_{J,\parallel}},
$$

并逐步扩展到旋转角度和完整平面输运张量。

### Case04：有限阵列/入口效应（独立协议）

严格周期的均匀结构中，单周期解已经由周期边界定义；简单复制为 $N=5,10,20,50$ 不构成独立的 RVE 收敛证据。

如果研究有限阵列尺度，应另建开放边界协议，设置入口/出口缓冲段，计算

$$
r_N=\frac{\Delta P}{Q L_N},
$$

并明确它研究的是入口、出口和有限阵列效应，而不是周期单胞本身的网格收敛。

### Case05：结构参数规律

在 Case02 网格收敛和 Case03 方向验证通过后，再研究

$$
R^*=f(D/H,\ W_g/P,\ P/H).
$$

参数扫描必须预先冻结参数矩阵、无量纲定义和停止准则，不能根据中间结果临时选择工况。

---

## 6. 最终停止点

本任务在 Case01、Case01a、Case01b 和 Case02 全部通过并完成第一阶段报告后停止。

第一阶段完成不代表：

- 动态压印已验证；
- 自由表面或接触角已验证；
- 已得到真实填充时间；
- 已得到宏观模型的最终闭合系数；
- 已证明连续介质无滑移模型在所有纳米尺度条件下都成立。

任何超出上述证据范围的结论必须另建验证任务。

---

# Case执行与论文证据要求（Case Evidence Protocol）

本章节只增加 Case 的论文证据规范，不修改前述 Frozen Protocol、Case 定义、物理参数、数值参数、验收阈值、Gate 逻辑或执行路线。第一阶段仍严格按照

```text
Case01 → Case01a → Case01b → Case02
```

执行。后续 Case 只有在满足前述门禁并建立独立冻结任务后才能启动。

## 1. Scientific Question（科学问题）

每个 Case 在执行前必须写出可检验的科学问题，至少明确：

- 本 Case 回答哪个科学问题；
- 解决论文中的哪个未知问题；
- 与其他 Case 之间的逻辑关系，包括基准、控制、对照、扩展或机制解释关系；
- 自变量、控制变量、主要响应量和可证伪的判断标准；
- 该 Case 能支持什么结论，以及不能支持什么结论。

不得以“运行一个算例”“生成一张云图”代替科学问题。一个 Case 只有在其输出能够区分预先提出的科学假设时，才构成论文证据。

## 2. Required Output Data（输出数据要求）

每个 Case 必须在运行前冻结输出量、单位、统计区域、采样频率、平均方法和误差定义。所有体积、质量、速度和通量积分继续只统计 material 1；overlap、padding 和重复周期端点不得计入物理积分。

### 2.1 宏观输运数据

根据对应 Case 的边界和驱动方式保存：

- 流量 $Q$；
- 平均速度 $U$；
- 有效阻力 $R$；
- 压降 $\Delta P$。

上述符号必须服从前文冻结定义。对于本阶段周期体力驱动 Case：

- 跨 Case 比较的主量仍为 $J_y$、$K_{yy}$、$B_{yy}$ 和 $R_{J,y}$；
- $Q_y=J_yL_x$ 只作为 $L_x=L_y$ 周期单胞的辅助报告量；
- $\Delta P$ 只能报告为等效量 $\Delta P_{\mathrm{eff}}=\rho a_yL_y$；
- 禁止把局部压力场的 $p_{\max}-p_{\min}$ 当作入口—出口压降或用于计算阻力。

对于另行冻结的开放边界 Case，才可按其独立协议报告入口—出口 $Q$、$U$、$R=\Delta P/Q$ 和 $\Delta P$；开放边界结果不得与本阶段周期结果混算。

### 2.2 数值稳定性数据

每个正式 run 必须保存：

- Mach 数及全过程最大值；
- 密度变化及全过程最大值；
- material 1 质量守恒误差及全过程最大绝对相对漂移；
- 主响应量的完整收敛历史；
- 冻结窗口的均值、样本标准差、相对标准差和相对跨度；
- 同方向截面通量一致性、横向交叉通量、材料节点数和有限值检查；
- 收敛判据是否满足与独立进程退出码，两者必须分别保存。

### 2.3 机制数据

根据预先声明的科学问题增加：

- 速度场；
- 压力场；
- 壁面剪切；
- 黏性耗散。

场数据必须同时注明物理单位、坐标方向、截面位置、色标范围、采样时刻和材料掩膜。壁面剪切、速度梯度和黏性耗散等对边界离散敏感的量，在完成相应网格收敛前只能用于定性机制解释。

## 3. Required Figures（论文图要求）

每个 Case 在启动前必须列出最终论文图及其拟支持的结论，不能只保存求解过程截图。根据 Case 目的至少选择以下图件：

- **验证图**：数值速度剖面与解析解对比、误差分布；
- **阻力比较图**：$J$、$K$、$B$ 或 $R_J$ 的同定义比较，并给出参考分母和不确定度；
- **收敛曲线**：主响应量随时间步变化、冻结窗口及阈值；
- **参数关系图**：如 $G-J$ 线性关系、网格误差/GCI 或预先冻结的几何参数关系；
- **流场机制图**：速度、局部压力扰动、流线、壁面剪切或黏性耗散，并与宏观阻力变化建立对应关系。

每张最终图必须具有稳定文件名、坐标轴名称和单位、图例、Case/run ID、数据来源及可复现绘图脚本。图中数值必须由保存的 CSV 或字段文件重新计算，禁止把摘要数值硬编码为绘图输入。

## 4. Required Data Files（数据保存规范）

每个 Case 应建立以下 Case 级结果结构：

```text
results/
├── csv/
│   ├── flow_rate.csv
│   ├── resistance.csv
│   └── convergence.csv
├── fields/
│   ├── velocity/
│   └── pressure/
└── figures/
```

其中：

- `flow_rate.csv` 保存 $Q$、$U$、$J$、截面位置、采样时刻和单位；
- `resistance.csv` 保存驱动量、$J$、$K$、$B$、$R_J$、解析值、误差、阻力比及其明确分母；
- `convergence.csv` 保存时间步历史、冻结窗口统计量、质量误差、密度变化、Mach、截面一致性和收敛标志；
- `fields/velocity/` 和 `fields/pressure/` 保存可后处理的场数据及其元数据；
- `figures/` 只保存能够追溯到上述数据和绘图脚本的最终图件。

所有关键数据必须采用 Python、Origin 或等效工具可直接读取的格式。CSV 必须包含表头、单位或配套 schema，禁止只保存图片而不保存底层数据。

该 Case 级结构是论文证据汇总层，不替代第 4 节已冻结的 run 级文件。每个正式 run 仍必须独立保存 `run_manifest.txt`、`diagnostics.csv`、`result.txt`、`exit_code.txt`、`run.log` 和初始/最终 VTK 字段；Case 级 CSV 必须能由这些原始 run 文件重新生成。

## 5. Paper Contribution Mapping（论文对应关系）

| Case | Scientific purpose | Paper section |
|---|---|---|
| Case01 | LBM numerical validation | Methods + Validation |
| Case01a | Maximum-envelope-height smooth control | Methods + Validation |
| Case01b | Equal-volume/equal-area smooth control | Methods + Validation |
| Case02 | EX240 structural resistance | Results |
| Case03 | Transverse transport and in-plane anisotropy | Results |
| Case05 | Geometry-resistance relationship | Results |
| Case06 | Flow resistance mechanism | Discussion |

映射表只定义潜在论文贡献，不构成 Case 启动授权。Case03 沿用本文第 5 节已经定义的“横槽方向与输运张量”，不能重定义为周期尺度收敛；严格周期单胞的简单复制也不能作为 RVE 收敛证据。Case06 当前仅为论文机制讨论的占位名称，其几何、参数、输出和验收标准尚未冻结，状态为 `TO_BE_DEFINED`，不得在独立协议建立前执行。

## 6. Case 模板

后续新增 Case 必须按照下列模板设计，并在运行前完成评审和冻结：

```markdown
# Case XX Template

## Scientific Question

- Scientific question:
- Unknown addressed in the paper:
- Testable hypothesis:
- Relationship to existing Cases:
- Supported conclusion:
- Explicit evidence boundary:

## Model Definition

- Geometry and coordinate convention:
- Fluid properties:
- Lattice and collision model:
- Resolution and time step:
- Boundary conditions:
- Driving method:
- Initial condition:
- Controlled variables:
- Independent variables:
- Run matrix and unique run IDs:

## Required Outputs

### Data

- Macroscopic transport quantities and units:
- Stability and conservation histories:
- Field quantities and sampling definitions:
- Analytic/reference values and error definitions:
- Required raw files and manifest fields:

### Figures

- Figure identifier and intended paper claim:
- Axes, units, normalization and uncertainty:
- Source data files:
- Reproducible plotting script:

### Tables

- Table identifier and intended paper claim:
- Required columns, units and reference denominators:
- Source run IDs:

## Acceptance Criteria

- Convergence-window thresholds:
- Conservation, density and Mach thresholds:
- Analytic, grid-convergence or GCI thresholds:
- Material/geometry consistency checks:
- Independent normal-exit evidence:
- Failure and stop conditions:

## Paper Contribution

- Target paper section:
- Main evidence supplied by this Case:
- Cases required for comparison:
- Claims enabled after acceptance:
- Claims that remain unsupported:
```

未完整填写上述模板、未冻结验收标准或无法建立数据—图件—论文结论追溯关系的新增 Case，不得进入正式计算。
