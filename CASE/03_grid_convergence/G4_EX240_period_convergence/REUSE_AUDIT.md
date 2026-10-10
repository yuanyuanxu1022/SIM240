# G4 Nx=1 基线复用审计（冻结引用）

G4 的 Nx=1 级不重跑稳态；R∥(1)、R⊥(1) 及三驱动力线性证据由以下已冻结批次复用（复用条件与 G2 Step3 REUSE_AUDIT 同口径：源/二进制/协议/参数/边界/统计逐项审计后冻结引用）。

## 冻结引用（SHA-256 实测于 2026-10-10）

| 证据 | 路径 | SHA-256 |
|---|---|---|
| 冻结母版源 | CASE/02_geometry_transport/G2_EX240_single_period_transport/src/g2_ex240_single_period_transport.cpp | 4acd63db67e273f87fed487fa7d1866f18dc82c018aaba1151f44882bd021002 |
| G2-P 稳态（a=1e5） | …/results/g2_ex240_20260917T105523+0800/G2-P/steady/result.txt | 5a6d580631974e22b899e696421dd14ad7abdf21295439559a8c253e629708e5 |
| G2-T 稳态（a=1e5） | …/results/g2_ex240_20260917T105523+0800/G2-T/steady/result.txt | 74aa68823379a9533846aa5ebb8f665b90c82c134e865c964b78aac39ac162d9 |
| 力线性汇总（3 驱动力 × 2 方向） | CASE/05_mechanism_analysis/G2_EX240_force_linearity/results/g2_force_linearity_20260917T120627+0800/g2_force_linearity.csv | 05e2bf5b999f6fd7a9118e5a9b941047f1a062afa32d2b7841c6c919087af517 |

## 冻结基线值

| 方向 | J (m²/s) | K (m³) | R = ρa/J (Pa·s/m³) | 步数 | 门禁 |
|---|---:|---:|---:|---:|---|
| Parallel（沿槽 y） | 9.7824e-12 | 9.7824e-23 | 1.022241553800475e19 | 13863 | 全过 |
| Perpendicular（横槽 x） | 4.3853e-12 | 4.3853e-23 | 2.2803490740984418e19 | 8699 | 全过 |

- 三驱动力线性：R² = 0.9999999999999998；K 最大相对跨度 Parallel 2.48e-8、Perpendicular 3.66e-8（≤1% 门禁）
- 单周期锚值：fluid_nodes = 460800；candidate_links = 130176；q_min = q_max = 0.5
- E(2→1) 计算使用本表 R 值；E(1→2) 在报告中仅报告，不参与收敛判定

## 复用声明

Nx=1 的 6 个稳态点证据按上述 SHA 冻结引用；任何文件内容变化即视为引用失效，须重新审计。Nx=1 仅以 G4 生成器产出 precheck 级证据（几何恒等自检），不跑 steady。
