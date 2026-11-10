# CASE 目录索引

> 本文件是 `CASE/` 的目录地图，用于快速定位各 case 与当前主线。**只做索引，不替代各 case 内的 report/result.txt。**
> 最后更新：2026-10-16。

---

## 0 命名与组织约定（2026-10-16 定）

- **一个 case 一个文件夹**；文件夹按「物理模型」分。
- 同一个物理模型内逐步加复杂度（V1→V2→V3、θ/h 扫描）**不拆文件夹**，用命令行参数 + run-id 区分；**换物理模型才开新文件夹**。
- 命名：**英语、有辨识性、体现 case 特点**，格式 `前缀编号_特点1_特点2`（如 `G2_EX240_single_period_transport`、`D1_nanoimprint_droplet_filling`）；不用纯方法词（如 DNS）做主体。
- 新 case 统一放入 **`CASE/D_series/`**。

## 1 前缀含义

| 前缀 | 含义 |
|---|---|
| `Case01-*` | 早期验证（Bouzidi / Poiseuille 基准） |
| `G*` | Gate 路线（单相输运主线） |
| `F*` | Filling / 压缩动力学 |
| `R2XY_*` | 液滴面内（**旧写法，已弃用**，仅留作参考） |
| `D*` | 液滴主线新框架（当前主线） |

## 2 目录地图

| 目录 | 用途 | 主要 case | 状态线索 |
|---|---|---|---|
| `00_validation/` | Bouzidi / Poiseuille 验证 | `G1_Poiseuille_Bouzidi_Validation` 等 | 已放行（见各自 report） |
| `01_baseline/` | 平壁基准 | `Case01a/1c`、`G2_S0_Smooth75` | — |
| `02_geometry_transport/` | 单周期沟槽输运 | `G2_EX240_single_period_transport` | K∥/K⟂ 已放行 |
| `03_grid_convergence/` | 网格收敛 + 周期收敛 | `G2_EX240_*`、`G4_EX240_period_convergence` | G4 复制不变性已过 |
| `04_parameter_study/` | 参数扫描 | `Case01-R2/R3`、`G3_EX240_height_sweep` | 三高度数据库已出 |
| `05_mechanism_analysis/` | 力线性 | `G2_EX240_force_linearity` | — |
| `05_mesoscale/` | 介尺度挤压模型 | `G5A_squeeze_resistance` | 候选（未最终闭合） |
| `06_filling_dynamics/` | 液膜压缩（几何资产） | `F1_liquid_film_compression` 等 | 沟槽几何可复用 |
| `07_filling_dynamics/` | 动态压缩 | `F2_*`、`F3_z_compression_dynamic` | 含移动边界历史尝试 |
| `08_droplet_inplane/` | 液滴面内（旧写法） | `R2XY_confined_patch` | 短测 FAIL，已弃用 |
| `D_series/` | **液滴主线新框架** | `D1_nanoimprint_droplet_filling` | V1b 进行中 |
| `archive/` | 已归档草稿 | — | 只读 |
| `plans/` | 所有规划文档 | — | 只读 |
| `reports/` | 所有报告 | — | 只读 |
| `H/` | 单相流结果总结 | — | 命名待澄清 |

## 3 当前主线（液滴线，2026-10-15 起）

- **目标**：OpenLB 全程；显式真实沟槽（P=240 nm，槽 120×深 100，一个直沟槽=一个周期，不做 K 等效）；微米级液区（连续液膜中的局部区域，非孤立单滴）。
- **XY/Z 分两条线**：XY 面内铺展与方向流量；Z 入槽（毛细自吸主线，超压为补充）。
- **论文骨架**：微观 DNS 标定 KXX/KYY + 修正系数 → 嵌入宏观模型 → 实验验证。
- **首篇交付**：Q1 面内铺展 + Q2 入槽（都不需要移动边界）；Q3 速率效应后置（R3）。

### 液滴线验证序列

```
R0（相场守恒根因）✅ → E0（自洽初始化）✅ → R1（平壁静滴基准）✅（旧代码）
   → 新框架 D1：V0 骨架 ✅ → V1a 初值对照 ✅ → V1b 平壁静滴复现（进行中）
   → V2 加沟槽 → V3 双接触角 → R2-XY / R2-Z
```

## 4 关键资产（可复用，勿改动）

| 资产 | 位置 | 用途 |
|---|---|---|
| KXX/KYY 数据库（h50/75/125） | `transport_database/`（项目根） | 对照基准，不重算 |
| 沟槽几何 + 逐槽填充率 F_g | `06_filling_dynamics/F1_*` | V2 复用算法 |
| 单位换算 + 成对截面流量 | `02_geometry_transport/G2_*` | R2 复用 |
| 相场 CH + 润湿 + tanh 自洽初值 | `grooveDNS/.../phasefield_minimal_validation/`（旧） | 已迁移到 D1 |

## 5 注意事项

- **禁止删除任何 case 目录或验证报告**——都是不可再生的证据，历史 FAIL 也不得改写。
- 重命名/合并目录会断掉报告里的路径引用，**须专门立项核对后再做**。
- 编译 OpenLB 须先 `export TMPDIR=/home/dell/.wbbuild/tmp`（`/tmp` 仅约 10 M）。
- 长仿真在 tmux 独立会话跑，助手给出命令即停、不轮询。
