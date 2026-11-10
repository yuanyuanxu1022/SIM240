# 条件性系数换算示例

状态：准备算术；不是 OpenFOAM 可运行字典，也不是新流动结果。

采用 H=125 nm，且假定该 Darcy 项承担全部平均阻力；不适用于直接叠加到已解析无滑移壁面。

|输入|槽向|Kxx (m³)|Kyy (m³)|Dx (m⁻²)|Dy (m⁻²)|
|---|---|---:|---:|---:|---:|
|original_local_cubic|groove_along_long_y|6.5181587838e-23|2.4088541667e-22|1.9177194687e+15|5.1891891892e+14|
|original_local_cubic|groove_along_short_x|2.4088541667e-22|6.5181587838e-23|5.1891891892e+14|1.9177194687e+15|
|V2_published_rounded|groove_along_long_y|4.5537951696e-23|1.0414014080e-22|2.7449631647e+15|1.2003056559e+15|
|V2_published_rounded|groove_along_short_x|1.0414014080e-22|4.5537951696e-23|1.2003056559e+15|2.7449631647e+15|
|OpenLB_dx5_diagnostic_only|groove_along_long_y|4.4490220210e-23|9.8340759586e-23|2.8096062328e+15|1.2710904464e+15|
|OpenLB_dx5_diagnostic_only|groove_along_short_x|9.8340759586e-23|4.4490220210e-23|1.2710904464e+15|2.8096062328e+15|

V2 因子：沿槽 0.43232231422；跨槽 0.698632132267。

OpenLB 行来自现存两个 5 nm result.txt，只作已见输入诊断；不是显式挤压参照。完整数值及矩阵见 coefficient_examples.json。
原始 run_id：h75_d100_dx5_P、h75_d100_dx5_T；来源哈希见 source_manifest.json。
