# E0：自洽初始化判别实验报告（R0 修复验证）

- 日期：2026-10-15
- 性质：**判别实验**（R0 报告第 6 节的三项短程 run），只动本地 `phasefield_minimal_validation.cpp` 的初始化（新增开关，默认值 = 原行为），不改 OpenLB 上游、不改判定口径、不覆盖历史 run。
- 结论速览：**Fix B1（tanh φ 初值 + Laplace 压力初值）充分有效：laplace 与 contact 两个案例全程最大相场总量漂移分别 3.82e-4 / 3.48e-4，均 < 1e-3 门槛；启动 Mach 压低约一个量级（2.03e-2 → 2.3–2.7e-3）；step 1 的 φ 不再越出 [0,1]。R1 协议可保留全程守恒口径，无需 Fix A 窗口化。** E0-a 同时证明"仅改压力"无效——φ 剖面不自洽是主因（与 R0 诊断一致）。

## 1 实现（Fix B1，两处初值改动 + 两个开关）

新增 `--init-phi smooth|tanh`（默认 smooth = 原行为）与 `--init-pressure zero|laplace`（默认 zero = 原行为），解析校验见 `parse()`；两个新 functor 位于 `phasefield_minimal_validation.cpp`：

- `TanhSpherePhaseF3D`：φ(d) = 0.5·(1+tanh(2d/w))，d 为到球面带符号距离（外正内负），与模型壁面处理器（`src/dynamics/phaseFieldCoupling.h` 的 `IsoPhaseFieldFlatWallTheta` 系）使用的离散平衡剖面**同式同宽**（w=interfaceWidth=4）。
- `LaplacePressureF3D`：p = pIn·(1−φ)，pIn = 2σ/R（格子单位）。tanh 模式与该剖面配套；cos2 模式精确复刻原 `SmoothIndicatorSphere3D` 的 `signedDistanceToPorosity` 剖面（|d|<w/4 内 cos² 过渡）。压力形状始终与 φ 初值自洽（p 经 `defineRhoU`/`iniEquilibrium` 写入 NS 格子）。

其余（几何、动力学、耦合、测量、判定）一字未动。

## 2 运行记录

| run | 命令要点 | 步数 | 完成 |
|---|---|---|---|
| E0-a | laplace，仅 `--init-pressure laplace`（φ 仍 cos²） | 200 | 全程无中断（无 break 触发） |
| E0-b | laplace，`--init-phi tanh --init-pressure laplace` | 200 | 全程无中断 |
| E0-c | contact（含润湿壁面），tanh+laplace | 500 | 全程无中断 |

run-id：`E0a_laplace_R16_pinit_20261015`、`E0b_laplace_R16_tanh_pinit_20261015`、`E0c_contact_R18_theta100_tanh_pinit_20261015`（`output/` 下，含 history.csv / result.txt / run_manifest.txt）。

## 3 结果判读（对照 20260910 原版 FAIL run）

| 指标 | 原版 laplace | E0-a | E0-b | 原版 contact | E0-c |
|---|---|---|---|---|---|
| max_Mach（step 1–50） | 2.03e-2 | 2.68e-2 | **2.65e-3** | 2.03e-2 | **2.26e-3** |
| 全程 max\|漂移\| | 2.395e-3 | 1.724e-3 | **3.82e-4** | 2.107e-3 | **3.48e-4** |
| step 1 φ 范围 | −0.022 / 1.019 | −0.022 / 1.019 | 4.5e-8 / 1.0 | — | 3.0e-8 / 1.0 |
| 接触角弛豫 | — | — | — | 96.8°@6000步 | 88.43°→89.26°（500步内单调升） |
| Δp（laplace）@末步 | — | — | 1.090e-3（预期1.250e-3，−12.8%） | — | — |

判读：

1. **E0-b/E0-c 全程漂移 < 1e-3**（3.82e-4 / 3.48e-4）→ 按 R0 判据，**R1 协议保留全程守恒口径**（Fix B1 充分，Fix A 窗口化不需要）。启动段（前 ~20 步）不再贡献 2e-3 级损失。
2. **E0-a 证明压力改动单独无效**：φ 仍 cos² 时 Mach 不降反升（2.68e-2），全程漂移仍有 1.72e-3。→ 两处不自洽中 **φ 剖面是主导项**，与 R0 证据链（漂移与源项逐点对应）自洽。
3. **tanh 剖面即离散平衡**：step 1 的 φ 严格留在 [0,1]（4.5e-8 / 1.0），对比 cos² 初值 step 1 即越界 ±0.02。启动寄生流压低约 10×。
4. **E0-c 接触角弛豫正常**：500 步内从 88.43° 单调升至 89.26°，方向正确（输入 100°）；原版从同样起点需 6000 步才到 96.8°，E0-c 的 500 步仍在弛豫初期，属预期。含润湿壁面时漂移仍 < 1e-3 → **润湿边界非泄漏源**（与 R0 E2 一致）。
5. **laplace Δp 稳定性**：E0-b 200 步仍处毛细波衰减振荡（末步 −12.8%，阈值 ±15% 之内但未收敛）；正式 R1 为 4000 步，稳定性验收在 R1 正式 run 中判读，E0 不提前下结论。

## 4 结论与下一步

- R0 闭环：相场 CH 路线的守恒 FAIL **通过自洽初始化修复**，无需求解器级改动；三个历史 FAIL 原样保留（E0 新 run 不覆盖、不改写 20260910 判定）。
- 下一步 = **R1 正式 run**：contact 6000 步 + laplace 4000 步，均用 `--init-phi tanh --init-pressure laplace`，按冻结协议门槛验收（接触角误差 ≤5°、Laplace 误差 ≤15%、全程漂移 ≤1e-3、末五次 Δp 稳定性 ≤5%、φ∈[−0.05,1.05]、Mach≤0.05）。预期两项 PASS 后，R2-XY / R2-Z 共用前置即全部打通。
