# G5A 准静态垂向加载—面内排液阻抗数值模型设计

日期：2026-09-21

状态：待用户审阅

适用项目：SIM240 / EX240 单相输运主线

## 1. 目的与研究边界

本设计把同一个纳米压印过程拆分为两个相互连接的研究模块：

1. G2/G3/G4 研究固定间隙下的面内排液能力，提供
   \(K_{\parallel}(h)\) 和 \(K_{\perp}(h)\)；
2. G5A 研究压头沿 \(z\) 方向下压时，面内排液阻力如何转化为压力和垂向载荷。

本设计只实现第二个模块的第一版验证应用：单相、全充液、牛顿、等温、不可压缩极限下的一维准静态挤压阻抗模型（quasi-static squeeze resistance model）。核心输出是挤压阻抗

\[
C_F=\frac{F_z}{V_p}.
\]

这里的“两个模块”是研究层级划分，不是两个先后发生的物理阶段。真实物理链条始终是

\[
z\text{ 向下压}
\rightarrow h(t)\text{ 减小}
\rightarrow p(x,t)\text{ 建立}
\rightarrow x\text{ 向两端排液}.
\]

### 1.1 本设计包含

- 读取现有 G3 高度扫描数据库，不重新运行 OpenLB；
- 在 \(h=50,75,125\ \mathrm{nm}\) 三个离散高度求解准静态压力；
- 比较 Smooth、EX240 parallel 和 EX240 perpendicular；
- 计算压力、出口流量、垂向载荷和归一化挤压阻抗；
- 用解析解和质量闭合验证单一 \(N=401\) 介尺度离散；
- 保留输入数据的固定网格证据边界。

### 1.2 本设计不包含

- OpenLB 核心修改或新的 OpenLB 计算；
- D3Q19 某个离散速度方向上的“向下体力”；
- moving Bouzidi、material 转换或真实移动边界；
- 连续 \(h(t)\) 轨迹、\(K(h)\) 插值或数据范围外外推；
- 气液界面、润湿、毛细压力、困气、非牛顿性或固化；
- 将数值压力迭代解释为物理压力传播时间。

## 2. 坐标与方向约定

- \(z\)：壁法向和压头下压方向；
- \(y\)：EX240 沟槽延伸方向，即 parallel；
- \(x\)：横跨沟槽方向，即 perpendicular；
- 一维条带坐标统一记为 \(s\in[-L/2,L/2]\)，避免把求解器坐标与具体版图方向混淆。

当条带排液方向沿 \(+y\) 时使用 \(K_{\parallel}\)；沿 \(+x\) 时使用 \(K_{\perp}\)。压头速度 \(V_p>0\) 表示向下运动，因此

\[
\frac{dh}{dt}=-V_p.
\]

## 3. 基线几何、物性与边界

第一版采用可解析验证的一维矩形条带：

| 参数 | 符号 | 基线值 |
|---|---:|---:|
| 排液长度 | \(L\) | \(1.0\times10^{-3}\ \mathrm{m}\) |
| 条带宽度 | \(W\) | \(1.0\times10^{-3}\ \mathrm{m}\) |
| 动力黏度 | \(\mu\) | \(1.0\times10^{-3}\ \mathrm{Pa\,s}\) |
| 参考下压速度 | \(V_p\) | \(75\times10^{-9}\ \mathrm{m/s}\) |
| 出口表压 | \(p_{\mathrm{out}}\) | \(0\ \mathrm{Pa}\) |
| 介尺度网格数 | \(N\) | 401 个控制体 |

两个端面均为定压排液边界：

\[
p(-L/2)=p(L/2)=p_{\mathrm{out}}.
\]

这是一维双侧出口条带。其解析系数不能直接套用于圆形压头、二维有限矩形四边排液或单侧出口。

参考速度只用于生成有量纲的压力与载荷。在当前线性模型中，主比较量 \(C_F=F_z/V_p\) 应与参考速度无关。

### 3.1 局部间隙均匀与 K(h) 空间均匀假设

本数值模型依赖两条简化假设，才使一维准静态压力方程在任一高度都保有解析解：

1. **局部间隙均匀**：在任一离散高度 \(h\) 下，压头底面与基板之间的液膜厚度在面内处处等于同一常数 \(h\)。模型忽略压头倾斜、表面粗糙度、基板/压头弹性变形与局部楔形效应，因而排液间隙是平行且厚度均匀的薄膜，其高度只随压头位移（时间）变化、不随条带坐标 \(s\) 变化。

2. **\(K(h)\) 空间均匀**：在任一固定高度 \(h\) 下，迁移率 \(K\) 只依赖 \(h\)，不随条带位置 \(s\) 变化，即 \(K=K(h)\) 为空间常数。因此每个高度从微尺度数据库只取一个标量 \(K\)（并按方向分别取 \(K_{\parallel}\) 与 \(K_{\perp}\)），而不是一个随 \(s\) 变化的场。

这两条假设使第 5 节中空间均匀 \(K\) 的解析解严格成立；它们是本数值模型的输入闭合边界，不用于描述真实薄膜中的厚度不均匀或迁移率空间分布。

## 4. 输入数据与工况矩阵

### 4.1 数据来源

唯一 EX240 输入文件为：

`transport_database/G3_height_resistance.csv`

该文件中的 EX240 迁移率只采用微尺度 OpenLB 网格

\[
\Delta x=2.5\ \mathrm{nm}.
\]

本模型不读取或重新计算 \(\Delta x=5.0\ \mathrm{nm}\) 与 \(1.25\ \mathrm{nm}\) 数据。

使用以下列：

- `height_nm`；
- `K_parallel`；
- `K_perp`；
- `R_parallel`；
- `R_perp`；
- `anisotropy`。

只允许精确读取数据库已有的 50、75、125 nm，不插值、不外推。所有 \(K\) 必须为有限正数。输入审计同时检查

\[
\frac{R K}{\mu}\approx1
\]

以及数据库各向异性与 \(K_{\parallel}/K_{\perp}\) 的一致性；审计用于发现口径错误，不用于重写输入数据。

Smooth 对照由解析关系生成：

\[
K_{\mathrm{smooth}}(h)=\frac{h^3}{12}.
\]

### 4.2 九个主工况

| 高度 | Smooth | EX240 parallel | EX240 perpendicular |
|---:|:---:|:---:|:---:|
| 50 nm | 运行 | 运行 | 运行 |
| 75 nm | 运行 | 运行 | 运行 |
| 125 nm | 运行 | 运行 | 运行 |

每个主工况只在 \(N=401\) 上求解，并与解析解逐项比较。本模型不执行介尺度多分辨率检查，因此不声称 G5A 介尺度网格独立。

## 5. 控制方程与解析解

深度积分面内通量为

\[
q=-\frac{K(h)}{\mu}\frac{dp}{ds}.
\]

一维质量守恒为

\[
\frac{\partial h}{\partial t}+\frac{\partial q}{\partial s}=0.
\]

代入 \(\partial h/\partial t=-V_p\)，得到

\[
\frac{\partial q}{\partial s}=V_p,
\]

以及准静态压力方程

\[
\frac{d}{ds}
\left(
\frac{K}{\mu}\frac{dp}{ds}
\right)=-V_p.
\]

对于空间均匀的 \(K\)，解析解为

\[
p(s)-p_{\mathrm{out}}
=\frac{\mu V_p}{2K}
\left[
\left(\frac{L}{2}\right)^2-s^2
\right].
\]

中心最大压力、垂向载荷和挤压阻抗分别为

\[
p_{\max}-p_{\mathrm{out}}
=\frac{\mu V_pL^2}{8K},
\]

\[
F_z
=W\int_{-L/2}^{L/2}(p-p_{\mathrm{out}})\,ds
=\frac{\mu V_pWL^3}{12K},
\]

\[
C_F=\frac{F_z}{V_p}
=\frac{\mu WL^3}{12K}.
\]

总出口体积流量必须满足

\[
Q_{\mathrm{out,total}}
=W\left(q_R-q_L\right)
=WLV_p.
\]

在相同宏观几何与边界下，方向阻抗比应满足

\[
\frac{C_{F,\perp}}{C_{F,\parallel}}
=\frac{K_{\parallel}}{K_{\perp}}
=\frac{R_{\perp}}{R_{\parallel}}.
\]

## 6. 数值方法

求解器采用一维守恒有限体积离散：

- \(N\) 个等宽控制体，压力位于单元中心；
- 面通量由相邻压力的中心差分计算；
- 两端定压边界采用半单元距离；
- 离散方程直接组装为三对角线性系统；
- 压力求解后从边界面通量计算质量闭合；
- 载荷采用控制体中点积分计算。
• 规范已按你的要求更新：

  - OpenLB 输入仅使用 (\Delta x=2.5,\mathrm{nm})；
  - 不读取或计算 5 nm、1.25 nm；
  - G5A 仅使用 (N=401)；
  - 通过解析解和质量守恒验证；
  - 不声明介尺度网格独立性。

  规范：/home/dell/yuanyuanxu/SIM240/docs/superpowers/specs/2026-09-21-g5a-
  squeeze-resistance-design.md

  修订提交：84a74d4

  请确认修订后的书面规范。确认后我再制定具体实施计划，不会直接启动 OpenLB。
该离散方式使体积守恒可以由面通量直接审计，且不依赖压力后处理差分。所有九个主工况都有解析解，因此不仅 Smooth，两个 EX240 主方向也必须接受相同解析验证。

线性响应附加检查使用 \(0.5V_p\)、\(V_p\)、\(2V_p\)。它不增加新的物理结论，只验证程序中 \(p\) 和 \(F_z\) 对 \(V_p\) 的线性，以及 \(C_F\) 的速度无关性。

## 7. 软件边界与建议目录

新增独立目录：

```text
CASE/05_mesoscale/G5A_squeeze_resistance/
├── README.md
├── config/
│   └── g5a_baseline.json
├── run_g5a.py
├── g5a_solver.py
├── tests/
│   └── test_g5a_solver.py
└── results/
    └── <run_id>/
```

模块职责：

- `g5a_solver.py`：输入校验、有限体积组装、求解、通量与载荷计算；
- `run_g5a.py`：读取配置和 G3 数据库，执行工况矩阵，写出审计文件与图；
- `g5a_baseline.json`：冻结宏观几何、物性、速度、网格和门槛；
- `test_g5a_solver.py`：解析解、边界、质量、线性、非法输入和禁止外推测试；
- `results/<run_id>/`：一次运行的完整本地证据，不默认提交大型结果。

不修改 OpenLB 源码、G2/G3 结果或现有提取脚本。

## 8. 输出与证据链

每次运行保存：

- `run.log`；
- `exit_code.txt`；
- `input_manifest.json`：输入 CSV 路径与 SHA-256、配置、代码版本和运行时间；
- `case_results.csv`：九个工况的 \(K,p_{\max},F_z,C_F,Q\) 及误差；
- `pressure_profiles.csv`：401 网格压力和通量剖面；
- `validation_report.md`：逐门槛 PASS/FAIL；
- `Figure_G5_pressure_profiles.png`；
- `Figure_G5_squeeze_impedance_vs_h.png`；
- `Figure_G5_directional_ratio_vs_h.png`。

静态论文图使用 600 dpi。图和报告必须从本次 CSV 自动生成，不硬编码汇总数值。

`case_results.csv` 至少包含：

```text
run_id,height_nm,model,direction,K_m3,R_input_pa_s_m3,
Vp_m_s,N,pmax_num_Pa,pmax_exact_Pa,pmax_rel_error,
Fz_num_N,Fz_exact_N,Fz_rel_error,
CF_num_N_s_m,CF_exact_N_s_m,
Qout_m3_s,Qdisplaced_m3_s,mass_rel_error,status
```

## 9. 冻结验证门槛

### 9.1 输入门槛

- 数据库文件存在且哈希写入 manifest；
- 三个目标高度均且仅各出现一次；
- 所需字段有限，\(K>0\)，方向标签无歧义；
- 不发生插值或外推；
- \(RK/\mu\) 与 1 的相对差异不超过 \(10^{-10}\)；
- 数据库各向异性与 \(K_{\parallel}/K_{\perp}\) 的相对差异不超过 \(10^{-10}\)。

### 9.2 每个工况数值门槛

在主报告网格 \(N=401\) 上：

- 所有输出为有限值；
- 内部压力不低于出口压力；
- 左右边界压力满足定压条件；
- 压力关于中心对称，相对误差小于 \(10^{-12}\)；
- 最大压力相对解析误差小于 \(10^{-6}\)；
- 载荷相对解析误差小于 \(10^{-4}\)；
- 总出口流量质量相对误差小于 \(10^{-10}\)。

质量相对误差定义为

\[
\varepsilon_m=
\frac{|Q_{\mathrm{out,total}}-WLV_p|}{WLV_p}.
\]

### 9.3 解析一致性和线性门槛

- 三个速度下 \(p_{\max}/V_p\) 和 \(F_z/V_p\) 的最大相对离散小于 \(10^{-10}\)；
- 数值方向阻抗比与 \(K_{\parallel}/K_{\perp}\) 的相对差异小于 \(10^{-4}\)。

任何主工况或强制门槛失败时，`exit_code.txt` 必须为非零，整体不得报告 PASS。

## 10. 状态判定与完成定义

程序分别报告：

- `INPUT_GATE`；
- `NUMERICAL_GATE`；
- `ANALYTIC_GATE`；
- `MASS_GATE`；
- `LINEARITY_GATE`；
- `RESULT_PASS`。

只有九个工况全部生成、所有门槛通过、所有证据文件存在且可读取时，才能写：

> G5A 离散高度准静态挤压阻抗模型在给定输入闭合下完成，并通过解析解、质量闭合和线性响应验证。

但是当前 G3 数据仅来自固定 \(\Delta x=2.5\ \mathrm{nm}\) 的微尺度计算。即使 G5A 的 `RESULT_PASS=true`，也必须同时标注：

```text
INPUT_CLOSURE_STATUS: CANDIDATE_FIXED_GRID
FINAL_GRID_INDEPENDENT_CLOSURE: false
```

因此不得写成“完成了网格无关的真实纳米压印动态模拟”或“证明了普适下压阻力规律”。

## 11. 预期科学比较

主比较量为 \(C_F(h)\)，而不是恒速条件下的总出口流量。因为规定 \(V_p\) 后，总排液量由压头排开的体积决定：

\[
Q_{\mathrm{out,total}}=WLV_p.
\]

结构和方向差异主要表现为维持相同下压速度所需的压力与载荷不同。基于输入数据库，预期

\[
C_{F,\perp}>C_{F,\parallel},
\]

且二者比值随高度增加由数据库给定的阻力各向异性控制。该预期只是输入闭合的数学传播；G5A 的新增价值是把微尺度迁移率转化为具有宏观几何和边界含义的压力、载荷与挤压阻抗，并验证这一传递过程守恒且可复现。

## 12. 后续升级条件

只有本设计通过后，才考虑以下独立升级：

1. 在 \([50,125]\ \mathrm{nm}\) 内建立受约束的 \(K(h)\) 插值并求连续 \(h(t)\)；
2. 扩展为二维有限矩形和完整迁移率张量；
3. 将恒速度和恒载荷作为不同实验分别研究；
4. 在 G6 中以移动边界 OpenLB 作交叉验证；
5. 在独立的 G5B 中加入两相、润湿、毛细和空气排出闭合。

这些升级不属于本次实现范围。
