# SIM-EC1XT240 STEP 6-G 相场接触角与 Laplace 最小验证报告

## 判定

**STEP 6-G：FAIL。** 本轮在独立基准域内完成了本机 OpenLB 三维 well-balanced Cahn–Hilliard 模型的平壁液滴接触角与周期液滴 Laplace 两项正式测试。两项均运行至冻结终点，无 NaN/Inf，密度、Mach 和相场变量范围没有触发安全停止；接触角末值与输入值接近，Laplace 压差末值也接近理论值。

但两项的相场总量全过程最大相对漂移分别为 `2.1072855e-3` 和 `2.3953222e-3`，均超过预先冻结的 `1e-3`。此外 Laplace 压差末五次采样相对范围为 `7.07545%`，超过 `5%` 稳定性门槛。因此当前配置尚不能判定满足纳米压印填充所需的定量界面守恒与表面张力稳定性；不进入 SIM-EC1XT240 显式结构。

## 实现依据与范围

本轮只新增 `phasefield_minimal_validation/` 和本报告，没有修改 STEP 6-A～6-F、历史程序或 OpenLB 源码。测试不使用 SIM-EC1XT240 几何。

本机 OpenLB 源码 HEAD 为 `882924a9cfc8dcdf82909e39530789cb6f5ebcc4`（release `1.8r1`）。实现以本机示例
`/home/dell/openlb/examples/multiComponent/contactAngle3d/contactAngle3d.cpp` 为依据，使用：

- Navier–Stokes：D3Q19 `MultiPhaseIncompressibleBGKdynamics`；
- 相场：D3Q19 `WellBalancedCahnHilliardBGKdynamics`；
- 耦合：`WellBalancedCahnHilliardPostProcessor<LinearTauViscosity>`；
- 固壁：NS `setBouzidiBoundary`，相场 `setBouzidiWellBalanced`；
- 润湿与化学势：`RhoWettingStatistics`、`ChemPotentialPhaseFieldProcessor`；
- 接触角写入约定：`THETA = pi - theta*pi/180`，与本机示例一致。

时间推进顺序沿用该示例：两个 lattice 的 `collideAndStream`，相场 PreCoupling 通信与处理，ChemPotCalc 处理与通信，随后执行 NS–CH coupling。没有修改库级处理器或调节参数追求通过。

## 冻结参数与判据

共同设置为双 D3Q19 lattice、`tau_liquid=1`、`tau_gas=0.8`、`tau_phase=1`、`rho_liquid=rho_gas=1`、界面宽度 4 格、表面张力 `sigma=0.01` 格子单位和零外力。等密度仅用于隔离算法功能，不代表液体—空气真实密度比，也未建立纳米尺度物理单位映射。

共同正式门槛：运行到规定终点；无 NaN/Inf；`Mach<=0.05`；`rho in [0.8,1.2]`；`phi in [-0.05,1.05]`；相场总量全过程最大相对漂移不超过 `1e-3`。

- 接触角：64×40×64 格，x/z 周期、y 固壁，半径 18 格的液滴接触下壁，输入 `100 deg`，6000 步，VTK 每 500 步；角度误差不超过 5°，末五次角度范围不超过 2°。
- Laplace：64³ 格、三方向周期、半径 16 格球形液滴，4000 步，VTK 每 400 步；末态 `Delta p` 相对 `2 sigma/R` 误差不超过 15%，末五次压差相对范围不超过 5%。

接触角从 z 中心截面的 `phi=0.5` 等值线交点拟合圆，并以离散有效壁面 `y=0.5` 计算。Laplace 压差由 `phi<0.1` 内部区域与 `phi>0.9` 外部区域的平均格子流体压力之差获得。

## 短测试

两个 50 步短测试均完成，未触发非有限值、Mach、rho 或宽松相场安全界限。首次接触角短测错误地套用了正式相场总量门槛，产生退出码 3；该记录保留。随后仅修正短测判定逻辑，使其符合已冻结的“短测只检查初始化与推进”，不改变模型、参数或正式门槛。修正版接触角短测与 Laplace 短测退出码均为 0。

## 平壁液滴接触角结果

run-id：`phasefield_contact_theta100_R18_formal_20260910`，完成 6000 步，程序退出码 3（冻结验收失败，不是崩溃）。

| 指标 | 结果 | 门槛 | 判定 |
|---|---:|---:|---|
| 输入接触角 | 100° | — | — |
| 末态测量接触角 | 96.812342° | 误差≤5° | PASS |
| 末五次角度范围 | 1.651284° | ≤2° | PASS |
| 相场总量最大相对漂移 | `2.1072855e-3` | ≤`1e-3` | **FAIL** |
| 末态相场总量相对漂移 | `-6.7305450e-4` | 辅助量 | — |
| phi 全过程范围 | `[-0.0425699, 1.0257735]` | `[-0.05,1.05]` | PASS |
| rho 全过程范围 | `[1,1]` | `[0.8,1.2]` | PASS |
| 最大 Mach | `0.0237708` | ≤0.05 | PASS |
| NaN/Inf | 无 | 无 | PASS |

接触角由初始几何测得的 88.54°逐步松弛至 96.81°，末态与输入相差 3.19°。这证明当前润湿边界能产生方向正确且定量接近的响应，但相场总量的早期最大漂移使综合验收不能通过。

## Laplace 压力结果

run-id：`phasefield_laplace_R16_sigma001_formal_20260910`，完成 4000 步，程序退出码 3（冻结验收失败，不是崩溃）。

| 指标 | 结果 | 门槛 | 判定 |
|---|---:|---:|---|
| 理论 `2 sigma/R` | `1.25e-3` | — | — |
| 末态测量 `Delta p` | `1.2108871e-3` | — | — |
| 末态 Laplace 相对误差 | 3.12903% | ≤15% | PASS |
| 末五次压差相对范围 | 7.07545% | ≤5% | **FAIL** |
| 相场总量最大相对漂移 | `2.3953222e-3` | ≤`1e-3` | **FAIL** |
| 末态相场总量相对漂移 | `-1.5954504e-3` | 辅助量 | — |
| phi 全过程范围 | `[-0.0401612,1.0252304]` | `[-0.05,1.05]` | PASS |
| rho 全过程范围 | `[1,1]` | `[0.8,1.2]` | PASS |
| 最大 Mach | `0.0276950` | ≤0.05 | PASS |
| 末态 Mach | `4.71695e-6` | 辅助量 | — |
| NaN/Inf | 无 | 无 | PASS |

末态压力幅值符合 Laplace 关系，但采样序列尚未达到冻结的 5% 稳定范围，且相场总量守恒不通过。因此不能仅凭末态 3.13% 压差误差宣称表面张力验证通过。

## 输出文件

独立程序与协议：

- `phasefield_minimal_validation/phasefield_minimal_validation.cpp`，SHA-256 `4571e73e59ae25a0c51dc15a23d1f62674efb28b5617ba0179f2fe2955b305e3`；
- `phasefield_minimal_validation/frozen_protocol.md`；
- `phasefield_minimal_validation/Makefile`。

接触角正式输出目录：`phasefield_minimal_validation/output/phasefield_contact_theta100_R18_formal_20260910/`。其中：

- `parameters.txt`：冻结参数；
- `history.csv`：逐步相场总量、phi/rho范围、速度、Mach、接触角和压力；
- `result.txt`、`run_manifest.txt`、`run.log`：最终判定、命令与运行记录；
- `vtkData/phasefield_contact_angle.pvd` 及配套 VTM/VTI：material、压力、速度、混合密度、phi 和化学势。

Laplace 正式输出目录：`phasefield_minimal_validation/output/phasefield_laplace_R16_sigma001_formal_20260910/`，包含同类参数、逐步结果、manifest、日志，以及 `vtkData/phasefield_laplace.pvd` 和配套 VTM/VTI。

## 结论与停止点

本机 OpenLB 的三维 well-balanced Cahn–Hilliard 实现已完成真实编译和两项最小运行。接触角响应和 Laplace 压力幅值有定量一致性，界面没有数值爆炸；但冻结的相场总量守恒门槛在两项测试中均未满足，Laplace 压差稳定性也未满足。因此 **STEP 6-G 不通过**，当前实现尚不能据此进入 SIM-EC1XT240 纳米压印两相填充。

本轮到此停止。没有参数扫描，没有重新调节 FreeSurface，也没有进入动态压头、扩大区域或目标几何。
