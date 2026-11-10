# C04：原SDI-v1全部50项数值检查

来源interface_analysis.json。每端23项、跨端4项；几何/身份/有限值前置守卫另执行。这不是50个独立物理验证。

|指标名|二维值|OpenFOAM值|原门槛（≤）|满足|
|---|---:|---:|---:|---|
|linear_normalized_residual|5.65513094094e-13|6.47537684325e-13|1e-12|是|
|linear_true_normalized_residual|5.6557240272e-13|6.47517654852e-13|1e-12|是|
|linear_iterations|90|32|2000|是|
|reported_raw_residual_finite|2.09261789006e-28|2.39581532295e-28|1e+100|是|
|pressure_relative_rms|8.02343469386e-14|1.91643030246e-13|0.001|是|
|pressure_relative_max|2.20490292691e-13|6.24426436483e-13|0.001|是|
|U_relative_L2|7.40123943019e-13|1.25083128546e-12|0.001|是|
|U_relative_mean|0|2.22044604925e-16|0.001|是|
|J_relative_L2|7.40123587953e-13|1.250835395e-12|0.001|是|
|J_relative_mean|2.22044604925e-16|4.4408920985e-16|0.001|是|
|Uy_relative_max|8.01192392196e-13|1.41641273713e-12|1e-08|是|
|Uz_relative_max|0|0|1e-08|是|
|Q_relative|3.37507799486e-14|1.29452004671e-13|0.001|是|
|Q_sign|0|0|0|是|
|K_from_U_relative|0|2.22044604925e-16|0.001|是|
|K_from_Q_relative|3.39728245535e-14|1.29229960066e-13|0.001|是|
|global_mass_relative|3.41129040096e-14|1.32563007638e-13|1e-08|是|
|local_mass_relative|1.80975946987e-11|2.07208915308e-11|1e-08|是|
|side_leakage_relative|0|8.23777180239e-16|1e-08|是|
|face_flux_consistency_relative|4.91850159323e-13|4.83231836142e-13|0.001|是|
|exported_U_face_interpolation_relative|0|4.57080575891e-14|0.001|是|
|energy_relative|3.41129040096e-14|1.29167089661e-13|0.001|是|
|positive_energy_and_power|0|0|0|是|

|跨程序指标|值|原门槛（≤）|满足|
|---|---:|---:|---|
|p_Pa_cross_relative_max|7.34449538224e-13|0.001|是|
|Jx_m2_s_cross_relative_max|4.36428595317e-12|0.001|是|
|Jy_m2_s_cross_relative_max|1.86728460514e-12|0.001|是|
|Q_cross_relative|1.63235575827e-13|0.001|是|

reported_raw_residual_finite为原检查器的有限值辅助守卫，线性验收仍使用1e-12归一化残差；Q_sign与positive_energy_and_power以0表示满足。未舍入值见JSON。
