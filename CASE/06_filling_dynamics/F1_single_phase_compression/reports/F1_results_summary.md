# F1 Single-phase hydraulic resistance of periodic EX240 nanogrooves

## 1. Objective

F1 基于 OpenLB LBM 显式建立 EX240 周期纳米沟槽真实几何，比较不同液膜高度下沿槽方向（parallel）与横槽方向（perpendicular）的液压输运，并分析周期沟槽诱导的液压阻力各向异性。

## 2. Numerical model

- **LBM framework:** OpenLB
- **Lattice:** D3Q19
- **Collision model:** Forced BGK
- **Boundary condition:** Bouzidi zero velocity exact boundary
- **Geometry:** `lx=240 nm`, `ly=240 nm`, groove width `=120 nm`, groove depth `=100 nm`
- **Spatial resolution:** `dx=2.5 nm`

## 3. Numerical validation

下表直接整理自 `results/summary/F1_validation.csv`。`q_min` 和 `q_max` 用于检查已安装 Bouzidi 链接的距离范围；`fallback_count` 用于检查非法回退；质量误差和 Mach 数保持原始 CSV 数值。

| case | height_nm | direction | PASS | converged | q_min | q_max | mass_error | Mach | fallback_count |
|---|---:|---|---|---|---:|---:|---:|---:|---:|
| F1-single-phase-h125-P | 125 | parallel | true | true | 0.5 | 0.5 | 0 | 2.0089028958621632e-07 | 0 |
| F1-single-phase-h125-T | 125 | perpendicular | true | true | 0.5 | 0.5 | 1.1845844822105344e-11 | 1.5991816186415166e-07 | 0 |
| F1-single-phase-h50-P | 50 | parallel | true | true | 0.5 | 0.5 | 0 | 9.709542202284989e-08 | 0 |
| F1-single-phase-h50-T | 50 | perpendicular | true | true | 0.5 | 0.5 | 6.0827287409916048e-12 | 3.0932583868950328e-08 | 0 |
| F1-single-phase-h75-P | 75 | parallel | true | true | 0.5 | 0.5 | 0 | 1.1937702206114466e-07 | 0 |
| F1-single-phase-h75-T | 75 | perpendicular | true | true | 0.5 | 0.5 | 8.5299437236265272e-12 | 6.3216788741617051e-08 | 0 |

在这六个记录中，CSV 标记的 `PASS` 和 `converged` 均为 `true`。所有记录的 `q_min=q_max=0.5` 且 `fallback_count=0`，与无非法边界回退的 Bouzidi 链接审计一致。最大质量误差为 `1.1845844822105344e-11`，最大 Mach 数为 `2.0089028958621632e-07`，因此这些记录满足质量守恒和低 Mach 条件。这里的结论限于 CSV 中记录的验证量，不替代独立的网格收敛验证。

## 4. Hydraulic resistance results

下表读取自 `results/summary/F1_resistance_matrix.csv`。`DeltaP` 保留 CSV 中的等效压降数值；`Q`、`Keff`、`R_eff` 和 `Keff/K0` 也均未重新舍入计算。

| height(nm) | direction | Q | DeltaP | Keff | R_eff | Keff/K0 |
|---:|---|---:|---:|---:|---:|---:|
| 50 | parallel | 1.3695052000532383e-18 | 23.999999999999996 | 5.7062716668882141e-23 | 1.7524577489057374e+19 | 5.4780208002126871 |
| 50 | perpendicular | 3.4413811591242159e-19 | 23.999999999999996 | 1.4339090951449549e-23 | 6.9739441492460732e+19 | 1.3765527313391563 |
| 75 | parallel | 2.3477816872903336e-18 | 23.999999999999996 | 9.7824236970431719e-23 | 1.0222415538004869e+19 | 2.7825560738256137 |
| 75 | perpendicular | 1.0524704429933982e-18 | 23.999999999999996 | 4.3852935121144107e-23 | 2.2803490739122389e+19 | 1.2473723767792102 |
| 125 | parallel | 6.377408938526819e-18 | 23.999999999999996 | 2.6572537243855455e-22 | 3.763283840089451e+18 | 1.6326166882624793 |
| 125 | perpendicular | 4.4355339975453695e-18 | 23.999999999999996 | 1.8481391634985746e-22 | 5.4108479414838508e+18 | 1.1354967020535243 |

在三个已记录高度上，parallel 和 perpendicular 的 `R_eff` 都随液膜高度增加而降低，说明较大的液膜间隙对应更高的输运能力。相同高度下，parallel 的流量较大、`Keff` 较高且 `R_eff` 较低；perpendicular 输运受到横向跨越沟槽几何的额外限制。该趋势是这组三高度数据支持的方向性比较，不外推到未计算高度。

## 5. Resistance anisotropy mechanism

下表读取自 `results/summary/F1_anisotropy.csv`。

| height(nm) | R_parallel | R_transverse | R_T/R_P |
|---:|---:|---:|---:|
| 50 | 1.7524577489057374e+19 | 6.9739441492460732e+19 | 3.979521990530565 |
| 75 | 1.022241553800487e+19 | 2.280349073912239e+19 | 2.230734081816928 |
| 125 | 3.763283840089451e+18 | 5.410847941483851e+18 | 1.437799584459523 |

`R_T/R_P` 在 `h=50 nm`、`75 nm` 和 `125 nm` 分别为 `3.979521990530565`、`2.230734081816928` 和 `1.437799584459523`。因此 transverse resistance 在所有已计算高度均大于 parallel resistance，但比值随液膜高度增加而降低。

物理上，沿槽方向的动量输运可以更多地利用连续的沟槽通道；横槽方向需要跨越沟槽—台面交替结构，速度场重排和局部壁面剪切更强，从而产生额外耗散。液膜高度增加后，受壁面约束的相对影响减弱，横向输运与沿槽输运的阻力差异随之缩小。该解释与表中的单调比值变化一致，但仍属于对当前三点数据的物理解释。

## 6. Height dependence

下表读取自 `results/summary/F1_height_effect.csv`。

| height(nm) | direction | R_eff | Keff |
|---:|---|---:|---:|
| 50 | parallel | 1.7524577489057374e+19 | 5.706271666888214e-23 |
| 50 | perpendicular | 6.9739441492460732e+19 | 1.4339090951449549e-23 |
| 75 | parallel | 1.0222415538004879e+19 | 9.782423697043172e-23 |
| 75 | perpendicular | 2.280349073912239e+19 | 4.3852935121144107e-23 |
| 125 | parallel | 3.763283840089451e+18 | 2.6572537243855455e-22 |
| 125 | perpendicular | 5.410847941483851e+18 | 1.8481391634985746e-22 |

从 `h=50 nm` 增加到 `125 nm`，parallel 的 `R_eff` 从 `1.7524577489057374e+19` 降至 `3.763283840089451e+18`，同时 `Keff` 从 `5.7062716668882141e-23` 增至 `2.6572537243855455e-22`；perpendicular 的 `R_eff` 从 `6.9739441492460732e+19` 降至 `5.4108479414838508e+18`，同时 `Keff` 从 `1.4339090951449549e-23` 增至 `1.8481391634985746e-22`。因而较小液膜高度下的约束对横向输运影响更显著；随着高度增加，两种方向的有效输运能力均提高，且方向性差异减弱。这里的比较仅基于三个离散高度，不代表连续幂律拟合。

## 7. Key findings for SIM240

- **Finding 1:** EX240 显式周期沟槽几何在当前数据中表现出可分辨的方向性输运差异。
- **Finding 2:** 三个高度下 transverse resistance 均高于 parallel resistance，`R_T/R_P` 为 `3.979521990530565`、`2.230734081816928` 和 `1.437799584459523`。
- **Finding 3:** 液膜高度增加时，两种方向的 `R_eff` 降低、`Keff` 增加，表明受限空间对液压输运具有明显影响。
- **Finding 4:** 横向阻力随高度增加下降更快，当前三点数据显示沟槽诱导的各向异性逐渐减弱。
- **Finding 5:** 六个记录的 CSV 验证标记和收敛标记均为 `true`，`fallback_count` 为 0，且质量误差与 Mach 数较小；这些结果仍应与独立网格收敛和不确定度分析结合使用。
