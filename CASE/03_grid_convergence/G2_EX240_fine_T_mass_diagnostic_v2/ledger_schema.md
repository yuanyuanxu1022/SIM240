# v2 账本新增字段与解释

基础账本与binary64快照采用 [v1 schema](../G2_EX240_fine_T_mass_diagnostic_v1/ledger_schema.md)。v2保留全部基础字段和二进制布局，追加以下列；不同版本的CSV必须按真实表头读取。

| 字段 | 含义与验收 |
|---|---|
| film_nodes | material1且core z索引1–60，预期2,211,840 |
| recess_nodes | material1且core z索引61–140，预期1,474,560 |
| film_delta, recess_delta | 区域内long-double求和rho−1；相加应与全域delta一致，按浮点精度预算核对 |
| rho_min_id, rho_max_id | 同一rho遍历的极值位置；并列极值保留首次位置；必须以整数解析 |
| nominal_volume_m3 | N*dx³的long-double值；不是原volume_seq或原门禁分母 |

ID=(x*192+y)*145+z；x/y/z为core索引，物理位置为((x+0.5)dx,(y+0.5)dx,(z−0.5)dx)。snapshot mask保存唯一fluid ID。每步显式检查区域计数，密度观测不可遗漏或对同ID重复；不对solid/halo计算物理液体质量。

diagnostic_status新增max_reconstruction_residual与reconstruction_target_met（≤1e-13）。该重构是旧质量误差的算术分解一致性，不能替代独立守恒证据。formal_reference_accepted始终false。

数据完整性还依赖运行外部manifest/SHA与独立exit。高精度账本的全局正常不能排除局部正负变化相消，也不能解除历史FAIL。完整4000步数据必须另行科学审查。
