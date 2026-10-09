# G2 介尺度输运数据库总结

输入结果根目录：`/home/dell/yuanyuanxu/SIM240/CASE/04_parameter_study/G3_EX240_height_sweep/results`

## 几何与输运参数

该数据库将同一 dx 的 Parallel/Perpendicular 结果配对；`R=1/K`，单位为 `Pa·s/m³`。

| grid_size_nm | gap_height_nm | K_parallel_m3 | K_perpendicular_m3 | R_parallel | R_perpendicular | anisotropy_ratio | mass_gate_status |
|---:|---:|---:|---:|---:|---:|---:|---|
| 2.5 | 75.0 | 9.782423697043172e-23 | 4.3852935121144107e-23 | 1.02224155e+22 | 2.28034907e+22 | 2.23073408 | PASS |

## 已有 OpenLB 输出审计

G2 结果目录中已发现 `result.txt/result_summary.csv`（K_eff、J、几何、质量/Mach/门禁）、`pressure_profile.csv`、`velocity_profile.csv`、`energy_dissipation.csv`、`field_slice.csv` 和 `diagnostics.csv`。压力驱动接口由周期体力 `rho*a` 定义；`energy_dissipation.csv` 是位置剖面，不是全域积分。

## 数值验证

GCI 字段来自原始 `g2_richardson_gci.csv`；质量状态沿用每个 steady 结果的原始 `PASS` 字段，不修改任何门禁。

## 填充预测可用性

这些表可作为固定 h、固定 EX240 RVE 的局部 Darcy/迁移率输入。周期体力驱动对应的有效压力梯度仍需在宏观填充模型中明确，不应把周期场的局部 pressure range 直接当作入口-出口压降。

## 限制

`dx=1.25 nm / EX240_perpendicular` 的质量门禁异常保留为 FAIL；当前 G2 数据库不等于完整瞬态填充模型，也不包含 H_eff(x,y,t) 或全域耗散积分。
