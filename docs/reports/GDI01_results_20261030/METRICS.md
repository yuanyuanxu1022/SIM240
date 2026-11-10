# GDI01 按冻结 GDI-v1 的完整检查表

独立于宿主的冻结检查器为 GDI-1.0.0；检查器未修改。共51项，全部满足：继承SDI的23项、GDI接入守卫20项、与两套C01结果的8项对照。这些项共享输入与物理模型，不能当成51项独立物理验证。

所有数值按机器回执保留。表内限值为上限（≤）；0/0表示该符号、有限性或正耗散检查满足，而不是相对误差。完整结构与原始文件哈希见 [interface_analysis.json](interface_analysis.json)。

## 继承SDI的23项

| 检查器指标 | 实际值 | 冻结上限 | 结果 |
|---|---:|---:|---|
| `linear_normalized_residual` | 7.8572209142561188e-13 | 9.9999999999999998e-13 | PASS |
| `linear_true_normalized_residual` | 7.8600536466083805e-13 | 9.9999999999999998e-13 | PASS |
| `linear_iterations` | 35 | 2000 | PASS |
| `reported_raw_residual_finite` | 3.8251646941859418e-29 | 1e+100 | PASS |
| `pressure_relative_rms` | 1.0477714267661315e-13 | 0.001 | PASS |
| `pressure_relative_max` | 3.5763984366591711e-13 | 0.001 | PASS |
| `U_relative_L2` | 1.4057562520416184e-11 | 0.001 | PASS |
| `U_relative_mean` | 1.404476535071808e-11 | 0.001 | PASS |
| `J_relative_L2` | 1.4057526186897911e-11 | 0.001 | PASS |
| `J_relative_mean` | 1.4044654328415618e-11 | 0.001 | PASS |
| `Uy_relative_max` | 4.8027991900486392e-12 | 1e-08 | PASS |
| `Uz_relative_max` | 1.1692352285618085e-12 | 1e-08 | PASS |
| `Q_relative` | 1.4371837053772651e-11 | 0.001 | PASS |
| `Q_sign` | 0 | 0 | PASS |
| `K_from_U_relative` | 1.404476535071808e-11 | 0.001 | PASS |
| `K_from_Q_relative` | 1.4371837053772651e-11 | 0.001 | PASS |
| `global_mass_relative` | 2.4160104834045461e-13 | 1e-08 | PASS |
| `local_mass_relative` | 1.7501638792359562e-11 | 1e-08 | PASS |
| `side_leakage_relative` | 3.2580861666343884e-13 | 1e-08 | PASS |
| `face_flux_consistency_relative` | 3.647185411923529e-13 | 0.001 | PASS |
| `exported_U_face_interpolation_relative` | 1.0643408775065756e-15 | 0.001 | PASS |
| `energy_relative` | 1.3717569728216223e-11 | 0.001 | PASS |
| `positive_energy_and_power` | 0 | 0 | PASS |

## GDI接入的20项

| 检查器指标 | 实际值 | 冻结上限 | 结果 |
|---|---:|---:|---|
| `actual_model_coefficient_relative` | 1.8215180678270365e-16 | 9.9999999999999998e-13 | PASS |
| `momentum_L2_relative` | 1.4044809671772454e-11 | 1e-10 | PASS |
| `momentum_max_relative` | 1.4052726488130182e-11 | 1e-10 | PASS |
| `delta_U_L2_relative` | 3.2119221565677579e-11 | 1e-10 | PASS |
| `delta_U_max_relative` | 3.2124388248826864e-11 | 1e-10 | PASS |
| `delta_p_max_relative` | 8.8817841970012523e-16 | 1e-10 | PASS |
| `force_independent_consistency` | 0 | 9.9999999999999998e-13 | PASS |
| `source_independent_consistency` | 3.5901936308725289e-16 | 9.9999999999999998e-13 | PASS |
| `diag_independent_consistency` | 2.2204460492503131e-16 | 9.9999999999999998e-13 | PASS |
| `split_independent_consistency` | 3.5901936308725249e-16 | 9.9999999999999998e-13 | PASS |
| `exported_gradient_consistency` | 1.680522882495893e-12 | 1e-10 | PASS |
| `pressure_matrix_residual_vs_conservative_flux` | 3.1589182193245801e-14 | 9.9999999999999998e-13 | PASS |
| `all_pressure_solves_converged` | 0 | 0 | PASS |
| `momentum_L2_relative_history_consistency` | 1.4058256435090594e-15 | 1e-10 | PASS |
| `momentum_max_relative_history_consistency` | 9.2150517431655719e-14 | 1e-10 | PASS |
| `delta_U_L2_relative_history_consistency` | 7.1085833891275816e-26 | 1e-10 | PASS |
| `delta_U_max_relative_history_consistency` | 0 | 1e-10 | PASS |
| `delta_p_max_relative_history_consistency` | 0 | 1e-10 | PASS |
| `force_based_energy_relative` | 1.3717804688516453e-11 | 0.001 | PASS |
| `force_based_positive_energy` | 0 | 0 | PASS |

## 与C01对照的8项

| 检查器指标 | 实际值 | 冻结上限 | 结果 |
|---|---:|---:|---|
| `two_dimensional_p_Pa_cross_relative` | 3.6067445326655917e-13 | 0.001 | PASS |
| `two_dimensional_Jx_m2_s_cross_relative` | 1.6359985707514057e-11 | 0.001 | PASS |
| `two_dimensional_Jy_m2_s_cross_relative` | 5.4088307414341345e-12 | 0.001 | PASS |
| `two_dimensional_Q_cross_relative` | 1.4649363538645403e-11 | 0.001 | PASS |
| `openfoam_p_Pa_cross_relative` | 3.5512333814343339e-13 | 0.001 | PASS |
| `openfoam_Jx_m2_s_cross_relative` | 1.6341276702257688e-11 | 0.001 | PASS |
| `openfoam_Jy_m2_s_cross_relative` | 4.0868552367634941e-12 | 0.001 | PASS |
| `openfoam_Q_cross_relative` | 1.4596497471094268e-11 | 0.001 | PASS |

## 归一化和几何口径

压力误差除以24Pa；速度误差除以解析主速度U*=3.643036135654074e-7m/s；J误差除以J*=4.5537951695675916e-14m²/s；质量、漏流、流量对照除以解析Q*=2.185821681392444e-18m³/s。横向J的解析值为0，故使用主方向J*，不能除以横向0通量。动量残差除以G=1e6Pa/m；压力变化除以24Pa。

全局质量误差为边界有符号通量和的绝对值/Q*；局部质量误差为各单元净通量绝对值之和/Q*；侧漏为y两侧逐面绝对通量和/Q*，不能只让正负漏流抵消。能量误差按|耗散−24Q出口|/|24Q出口|。完整离散定义由绑定的 `analysis/sdi_metrics.py` 和 `analysis/check_results.py` 控制。

`geometry_PASS=true`仅针对512单元的合成平均域、面连通与方向/边界映射（几何容差1e-10）；不是显式沟槽、真实EX240边界或全部历史几何验收。原生p/U/J/phi/phi_U的单位与数值均逐项回读，与CSV一致。

直接算术补核用math.fsum及实际单元体积；局部质量误差为1.7501660644490523e-11，冻结核为1.7501638792359562e-11，差约2.19e-17，来自求和顺序。两者均保持相同1e-8门槛；验收值仍以冻结核为准。见 [independent_raw_audit.json](independent_raw_audit.json)。
