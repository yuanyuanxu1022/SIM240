# SIM240 输运数据库自动总结

数据库目录：`analysis/transport_parameter_extraction/transport_database`

## 自动发现与提取

数据库记录数：4

字段包含几何、K、R=1/K、方向比、GCI 和质量门禁状态。pressure_gradient 使用周期体力等效定义；energy_dissipation 当前为剖面数据，不是全域积分。

## 数据边界

原始 OpenLB results 只读；本流程不修改 OpenLB、G2/G3 结果或 PASS/FAIL 逻辑。
