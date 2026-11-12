# 论文数据代码审查报告（2026-10-17 凌晨）

> 审查方式：① 逐段读源码核对物理口径；② **独立交叉验证**——用不共享任何项目代码的内联公式，从底层 result.txt / summary.csv 重算论文全部数字并逐项比对。

## 1. 审查范围

| 文件 | 角色 | 审查结果 |
|---|---|---|
| `D2_groove_error_map/src/d2_groove_error_map.cpp` | 主求解器（主矩阵+μ+d75） | ✅ 几何/力/K 口径/门禁全部正确 |
| `D3_oblique_groove_tensor_check/src/d3_oblique_groove_tensor_check.cpp` | 斜槽求解器 | ✅ 截面修复与斜向判据在位 |
| `scripts/analyze_matrix.py` | 误差表/弹性/效率分析 | ✅ 公式正确（1 处无害死代码） |
| `scripts/fit_correction.py` | 修正公式拟合 | ✅（M2/M3 单位 bug 已修且不参与最终推荐） |
| `scripts/run_matrix.sh` / `run_mu_check.sh` / `run_d75_validation.sh` | 批次调度 | ⚠ 发现 1 个字段名 bug，已修 |
| `scripts/make_charts.py` | 绘图 | ✅ 数据源已交叉验证 |

## 2. 求解器代码逐项核对（D2 全读 + D3 差异点）

| 检查点 | 结论 |
|---|---|
| 几何：槽 x∈[60,180) nm、凸台高 h、槽内高 h+d、双台阶 | ✅ 与 EX240 协议一致 |
| 流体节点计数：nx·ny·(h/dx) + 槽宽/dx·ny·(d/dx)，全部 5 的倍数无舍入歧义 | ✅ |
| 体力换算：f_lat = a·dt²/dx（ρ 精确约掉） | ✅ 量纲推导正确 |
| K 口径：K = μ·J/(ρa)，J=单位宽度通量 m²/s，K 为 m³ | ✅ 与冻结卡 §5.2 一致；实测 J/K=1e11（μ=1mPa·s 档）与 6.67e9（15mPa·s 档）精确符合 μ/(ρa) |
| Bouzidi 边界 + q=0.5 钳制保证分支一致 | ✅ 边界审计 32448 条全过 |
| 门禁：质量 <1e-10、密度 ≤1e-6、Ma<0.05、窗口 std≤1e-6/span≤5e-6 | ✅ 36 档全绿 |
| 截面一致性（斜向时积法向分量 u_x/u_y，非驱动投影） | ✅ 已修复（D3 首跑抓出的真 bug） |
| D3 斜向判据：axisAligned 用 cross≤1e-12，斜向用 cross 相对 std≤1e-6 | ✅ |

## 3. 本次审查发现并修复的问题

1. **run_matrix.sh 步数字段名不匹配**（真 bug，已修）：脚本读 `completed_steps=`，result.txt 写的是 `steps_completed=`，导致 summary.csv 的 steps 列全 NA。**不影响论文数字**（steps 只是元数据），已修正脚本并用 `rebuild_summary.py` 从 22 档 result.txt 全量回填。
2. 审查过程中我的一次性回填脚本曾把 summary.csv 写坏（只剩表头）——已全量重建并经独立比对确认与 error_table.csv 的 K_dns **逐位一致**，无数据损失。
3. analyze_matrix.py 第 43–44 行有一段死代码（`for i in (-2,-1): pass`），无害，未改动。
4. 历史已修并复验：截面口径 bug（60° 假差异 48%）、μ 参数化 constexpr、fit_correction M2/M3 单位混淆（nm³↔m³，仅影响被弃用的候选，最终推荐的 M4/T2 是比值形式、单位天然约掉）。

## 4. 独立交叉验证结果（核心证据）

不调用任何项目脚本，直接用内联公式从底层数据重算，与论文产物比对（容差=存储精度）：

| 项目 | 数量 | 结果 |
|---|---|---|
| K_dns（DNS 实测值） | 18 个 | ✅ 全部一致 |
| K_model（Jain/局部立方律模型值） | 18 个 | ✅ 全部一致（独立重算算术/调和平均） |
| E_pct（误差百分比） | 18 个 | ✅ 全部一致 |
| A_dns / A_model（各向异性） | 9 几何 ×2 | ✅ 全部一致 |
| H_ref / eta（等体积高度/效率） | 9 几何 ×2 | ✅ 全部一致 |
| S_hat（弹性系数） | 24 个 | ✅ 全部一致 |
| d75 修正预测值 | 6 个 | ✅ 全部一致（相对差 ≤2e-5） |

**真实不一致：0 处。**

## 5. 结论

论文中使用的全部数字（36 档 DNS 数据 → 误差表 → 敏感性 → 效率 → 修正公式 → 留出验证），从求解器代码到分析链路的每一环，均已通过：① 源码逐段核对；② 独立路径重算比对；③ 物理口径自洽检查（J/K 比值 = μ/(ρa) 精确成立；平板极限 0.03–0.44% 历史验证；斜槽张量旋转律 6/6 命中作为 D3 代码的端到端验证）。

**可以放心把这些数字写进论文。** 建议把本报告与 `ACCEPTANCE_AND_ANALYSIS_20261016.md`、`D75_VALIDATION_RESULT_20261017.md` 一起作为论文"数值方法验证"的支撑材料归档。

审查脚本：`scripts/independent_crosscheck.py`、`scripts/rebuild_summary.py`（均可复跑）。
