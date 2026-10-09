# G2 Step 3 EX240 网格收敛与不确定度总结

**数据批次**：`g2_grid_20260917T165045+0800`  
**审计日期**：2026-09-18  
**物理问题**：固定间隙 `h=75 nm` 的 EX240 单胞，提取
`K_parallel`、`K_perpendicular` 及各向异性比
`A=K_parallel/K_perpendicular`。  
**执行边界**：本报告只分析已有九点 Step3 结果；不启动 G3、参数扫描、
移动边界或两相计算。

## 1. 结论

G2 Step3 的**收敛形态和不确定度量化均通过**：三个绝对迁移率的三网格
序列单调，Richardson 渐近性检验通过，且 EX240 两个主方向的细网格 GCI
均低于预冻结的 2% 目标。

但是，**G2 Step3 总 Gate 为 FAIL**，不能冻结生产网格或把本批 EX240 值
称为最终定量闭合参数。原因是最细网格横槽方向
`dx=1.25 nm / EX240_perpendicular` 的 material-1 质量误差为
`1.1967043900362632e-10`，超过冻结阈值 `1.0e-10`；程序内 `PASS=false`，
且独立 shell/in-program 退出码均为 3。该失败不能由 GCI PASS 抵消。

因此，本批结果的正确表述是：

```text
geometry_PASS: true for 9/9 prechecks
RESULT_PASS:   true for 8/9 steady points
NUMERICAL_GATE (Step3): FAIL
GCI evidence:  PASS for the three-grid mathematical convergence analysis
production grid: not frozen
```

## 2. 冻结问题与数据完整性

所有点保持固定 EX240 几何：`P=240 nm`，mesa/groove/mesa=`60/120/60 nm`，
沟槽深度 `D=100 nm`，mesa gap `h=75 nm`。物性为
`rho=1000 kg/m3`、`nu=1e-6 m2/s`、`mu=1e-3 Pa s`；采用 D3Q19 `<FORCE>`、
ForcedBGK、`tau=1.0`、精确零速度 Bouzidi、x/y 双周期及
`a=1e5 m/s2`。

网格为 `dx=5.0, 2.5, 1.25 nm`，扩散标度下分别使用
`dt=4.166666666666667e-12, 1.041666666666667e-12,
2.604166666666667e-13 s`。所有九个零步预检均具有
`geometry_PASS=true`、`q_audit_PASS=true`、candidate links=installed links、
`q=0.5`（数值容差内）、fallback=0 和 unresolved links=0。

迁移率定义保持为

$$
K_{\mathrm{eff}}=\frac{\mu J}{\rho a},\qquad
A=\frac{K_{\parallel}}{K_{\perp}}.
$$

## 3. K 收敛与方向比收敛

| dx (nm) | K_smooth (m3) | K_parallel (m3) | K_perpendicular (m3) | K_parallel/K_smooth | K_perpendicular/K_smooth | A=K_parallel/K_perpendicular |
|---:|---:|---:|---:|---:|---:|---:|
| 5.00 | 3.5312498716e-23 | 9.8340759586e-23 | 4.4490220210e-23 | 2.784871 | 1.259900 | 2.210390 |
| 2.50 | 3.5195285780e-23 | 9.7824236970e-23 | 4.3852935121e-23 | 2.779470 | 1.245989 | 2.230734 |
| 1.25 | 3.5165797339e-23 | 9.7643255262e-23 | 4.3586133688e-23 | 2.776654 | 1.239447 | 2.240237 |

两个主方向均随网格加密单调下降；方向比则由 2.210390 单调增加到
2.240237。故该单胞在本固定间隙下的各向异性不是粗网格噪声造成的符号
不确定性：所有网格均有 `K_parallel > K_perpendicular`。但其最终数值仍受
下述 Gate 失败约束。

## 4. Richardson 外推、GCI 与不确定度

采用冻结设置 `r=2`、安全系数 `Fs=1.25`，细/中/粗网格分别为
`1.25/2.5/5.0 nm`。

| 指标 | 表观阶 p | Richardson 外推值 | GCI_fine (%) | GCI_medium (%) | 渐近比 | 数学判定 |
|---|---:|---:|---:|---:|---:|---|
| K_smooth | 1.990910 | 3.5155884849e-23 | 0.035235 | 0.139937 | 0.999162 | PASS |
| K_parallel | 1.512988 | 9.7545638615e-23 | 0.124966 | 0.355994 | 0.998150 | PASS |
| K_perpendicular | 1.256172 | 4.3393998345e-23 | 0.551022 | 1.308170 | 0.993916 | PASS |
| K_parallel/K_smooth | 0.939763 | 2.7735874993 | 0.138053 | 0.264546 | 0.998987 | PASS |
| K_perpendicular/K_smooth | 1.088414 | 1.2336387764 | 0.585744 | 1.238987 | 0.994749 | PASS |
| A=K_parallel/K_perpendicular | 1.098181 | 2.2485661018 | 0.464763 | 0.999224 | 1.004260 | PASS |

冻结判据要求渐近比位于 `[0.95, 1.05]`；所有六个指标均满足。对于论文中
可报告的**候选**细网格离散不确定度，可暂记为：

$$
K_{\parallel}(1.25\ \mathrm{nm})=9.76433\times10^{-23}\ \mathrm{m^3}
\quad (\mathrm{GCI}=0.125\%),
$$

$$
K_{\perp}(1.25\ \mathrm{nm})=4.35861\times10^{-23}\ \mathrm{m^3}
\quad (\mathrm{GCI}=0.551\%),
$$

$$
A(1.25\ \mathrm{nm})=2.24024
\quad (\mathrm{GCI}=0.465\%).
$$

这里的“候选”不可省略：GCI 仅量化已获得的网格离散趋势，不能修复一个
未通过质量门槛的最细网格运行。

## 5. 相对指标稳定性与生产网格含义

三网格总 span 为：`K_parallel/K_smooth=0.295543%`、
`K_perpendicular/K_smooth=1.638304%`、`A=1.340125%`。后两项的总 span
大于 1%，说明不能只凭粗细端范围宣称相对指标“全网格无关”。

若且仅若九点数值门禁全部 PASS，按照冻结选择规则，`dx=2.5 nm` 将是
候选生产网格：它对两项外推绝对迁移率均在 2% 内，且相对于 1.25 nm 的
两个 smooth-normalized mobility 和方向比偏差均在 1% 内。`dx=5 nm` 不应
作为候选，因为横向绝对迁移率相对外推值超过 2%。

但当前 Step3 Gate 为 FAIL，所以上述只是**条件性选择结果**，不是生产
网格决定。正式结论仍为：**production grid = none**。

## 6. PASS/FAIL 审计

| 项目 | 状态 | 依据 |
|---|---|---|
| 九个零步几何/边界预检 | PASS | 9/9 `geometry_PASS`、q audit、link 与 fallback 审计通过 |
| 5.0 nm 三点稳态数值门禁 | PASS | 三点均 `PASS=true` 且独立退出码 0 |
| 2.5 nm 三点稳态数值门禁 | PASS | 三点均 `PASS=true` 且独立退出码 0 |
| 1.25 nm Smooth75 | PASS | `PASS=true`、退出码 0 |
| 1.25 nm EX240 parallel | PASS | `PASS=true`、退出码 0 |
| 1.25 nm EX240 perpendicular | FAIL | mass error `1.196704e-10 > 1e-10`，`PASS=false`、退出码 3 |
| 绝对 K 的 Richardson/GCI | PASS | 三项单调、正表观阶、渐近比通过 |
| 细网格 EX240 GCI <=2% | PASS | parallel 0.124966%，perpendicular 0.551022% |
| G2 Step3 总 Gate | **FAIL** | 九点数值门禁并非全通过 |

注意：最细横向点的质量误差仅比阈值高约 19.7%，而 Mach、密度偏差、
收敛窗口、截面通量差、边界审计和有限性均通过。这说明需要针对质量账本
进行最小化诊断；它不是放宽阈值或把退出码 3 改写为成功的依据。

## 7. 论文使用边界与下一步

目前可在方法/附录中报告：网格序列、主方向均保持正的稳定各向异性、
三网格 Richardson/GCI 指标以及一个明确的最细横向质量 Gate 失败。

目前不可将 `K_parallel`、`K_perpendicular` 或方向比冻结为最终
`K_eff` 闭合参数，也不可基于本批结果启动 G3-h 正式矩阵。

下一步应按顺序进行：

1. 对 `dx=1.25 nm / EX240_perpendicular` 做只针对 material-1 质量账本的
   最小诊断，区分核心 fluid mass、density deviation、overlap/padding 与
   shell/in-program exit 的证据；不改阈值、不修改物理参数。
2. 在原冻结协议下获得一个同时满足独立退出码和质量门槛的最细横向结果，
   重新运行后处理并复核九点 Gate。
3. 仅在 Step3 总 Gate 转为 PASS 后，冻结 `dx=2.5 nm` 的生产选择（若复核
   后仍满足所有条件）；随后才对 G3-h 全高度矩阵做各高度零步预检。

## 8. 数据与图件可追溯性

- 原始九点 `result.txt`、预检、日志和独立退出码：
  `CASE/03_grid_convergence/G2_EX240_grid_convergence/results/g2_grid_20260917T165045+0800/runs/`
- 机器可读汇总：`g2_grid_summary.csv` 与 `g2_richardson_gci.csv`。
- 已生成图件：`Figure_G2_grid_K_parallel`、`Figure_G2_grid_K_perpendicular`、
  `Figure_G2_grid_eta`、`Figure_G2_grid_anisotropy`、`Figure_G2_grid_GCI_summary`
  （PNG/PDF）。
- 本报告的数值逐项从上述原始 `result.txt` 和独立 `exit_code.txt` 复核，
  并与现有后处理 CSV 交叉一致。
