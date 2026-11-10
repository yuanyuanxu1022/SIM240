# C03：原SDI-v1的全部50项数值检查

来源：interface_analysis.json；两端各23项、跨端4项。结构、几何、身份和有限值守卫另行执行。这不是50个独立物理验证。

|指标名|二维值|OpenFOAM值|原门槛（≤）|满足|
|---|---:|---:|---:|---|
|linear_normalized_residual|6.71284340582e-13|8.21591528901e-13|1e-12|是|
|linear_true_normalized_residual|6.70219769076e-13|8.22680405183e-13|1e-12|是|
|linear_iterations|106|40|2000|是|
|reported_raw_residual_finite|6.71016787179e-29|8.23658727827e-29|1e+100|是|
|pressure_relative_rms|2.49047394837e-14|7.00107278269e-14|0.001|是|
|pressure_relative_max|7.01475914392e-14|2.14643118094e-13|0.001|是|
|U_relative_L2|3.24648100172e-13|6.4626336639e-13|0.001|是|
|U_relative_mean|0|2.22044604925e-16|0.001|是|
|J_relative_L2|3.24650632241e-13|6.46262670067e-13|0.001|是|
|J_relative_mean|0|4.4408920985e-16|0.001|是|
|Uy_relative_max|2.02412003262e-12|5.19572465605e-12|1e-08|是|
|Uz_relative_max|0|0|1e-08|是|
|Q_relative|1.59205981731e-13|1.22568621919e-13|0.001|是|
|Q_sign|0|0|0|是|
|K_from_U_relative|0|2.22044604925e-16|0.001|是|
|K_from_Q_relative|1.59205981731e-13|1.22346577314e-13|0.001|是|
|global_mass_relative|1.67433831857e-13|1.20001811329e-13|1e-08|是|
|local_mass_relative|2.14468426988e-11|2.63246353226e-11|1e-08|是|
|side_leakage_relative|0|3.04435525253e-15|1e-08|是|
|face_flux_consistency_relative|6.2402249652e-13|6.10916341042e-13|0.001|是|
|exported_U_face_interpolation_relative|0|4.05448243129e-14|0.001|是|
|energy_relative|1.59226291079e-13|1.22128206766e-13|0.001|是|
|positive_energy_and_power|0|0|0|是|

|跨程序指标|值|原门槛（≤）|满足|
|---|---:|---:|---|
|p_Pa_cross_relative_max|2.35959400167e-13|0.001|是|
|Jx_m2_s_cross_relative_max|2.1540533763e-12|0.001|是|
|Jy_m2_s_cross_relative_max|5.04473624281e-12|0.001|是|
|Q_cross_relative|3.66877072745e-14|0.001|是|

reported_raw_residual_finite为原检查器的有限值辅助守卫，不代表原始残差的物理误差门槛；线性验收仍使用1e-12归一化残差。Q_sign和positive_energy_and_power以0表示满足。原始未舍入值见JSON。
