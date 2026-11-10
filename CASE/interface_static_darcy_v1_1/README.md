# SDI-v1：检查器1.1.0与C02沿槽检查材料

日期：2026-10-30。状态：**C02材料与静态核对已完成，按用户要求暂不启动。** 没有C02压力迭代、流动结果或实际run_id。

## 阅读顺序

1. [C02具体规格](common/C02_SPEC.md)：与C01的区别、解析预期和适用范围。
2. [检查器版本说明](common/CHECKER_CHANGELOG.md)：几何识别修正、支持范围和原有结果复核。
3. [C02输入](common/C02.json)与[解析预期值](common/C02_expected.json)：程序读入值及未来对照值。
4. [静态准备证据](reports/preparation.json)：复用程序/网格的来源、checkMesh、audit-only输出。

新[检查器](analysis/check_results.py)版本为1.1.0，支持已完成的C01/C02、固定主轴x驱动。它从原始输出重算指标，保留全部Sf/phi值；面向量的浮点非主分量按已有归一化几何容差识别。SDI-v1的压力、流量、守恒、耗散和迭代门槛不变。旧C01发布包、原始结果和原检查器未评价记录均保留。

两个求解程序未改源码；已按SHA256核对源码、Make配置及二进制与原C01发布一致，复用其真实编译证据，**本轮未重新编译**。C02仍为512单元、x驱动、两维平均域，正是这两个程序接受的配置。网格同样逐文件复用后在C02路径重新checkMesh。OpenFOAM审计仅装配矩阵并退出，没有调用solve。

状态：source_prepared=true、compile_identity_verified=true（复用已编译程序）、mesh_checked=true、matrix_assembly_audit=true；run_completed=false、NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=null、geometry_PASS=true（仅合成平均域）；physical_validation=NOT_EVALUATED。独立人工科学验收尚无。

新版检查器已用C01已完成数据复核，50项数值检查与前轮分析逐项一致，未重跑C01。15项人造数据功能测试通过，不代表C02计算通过。

`scripts/run_c02.py` 默认只读检查材料完整性，只有显式执行参数才可能运行单例；本轮只调用默认检查。`common/release_manifest.json`记录准备包，不授予启动权限。预留planned_run_id为`SDI_C02_v1_1_20261030_01`，actual_run_id=null。没有创建runs目录、tmux会话、SDI_output或时间1流场。

当前停点：等待用户后续明确启动C02。此处不交付启动命令，不自动进入其他SDI算例、挤压或真实沟槽计算。后续仅在获准启动并完成后，按同一SDI-v1门槛评价C02，并对照C01讨论主值交换。

原[SDI-v1协议](common/PROTOCOL.md)保留制定时的状态文字和阈值，本README及preparation.json描述当前实际完成范围。流程沿用scientific-writing的证据与状态组织；出处见[原协议入口](../../docs/reports/Static_Darcy_interface_protocol_20261030/README.md)。
