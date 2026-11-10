# 检查器1.1.0已纳入本地新版本，C02材料已准备，未启动

日期：2026-10-30。用户范围：将几何识别修正纳入新版检查器，准备C02沿槽静态接口材料，暂不启动下一例。**本轮完成本地版本更新和C02静态准备，未启动或重跑任何流动计算。**

材料入口：[CASE/interface_static_darcy_v1_1/README.md](../../../CASE/interface_static_darcy_v1_1/README.md)。C01原目录仍为interface_static_darcy_v1，包含原检查器、封装、失败记录、已有原始运行与报告；未在原目录替换文件。

## 1. 新版检查器与兼容范围

本地新版本为1.1.0，物理协议仍是SDI-v1。检查器将面面积向量的主轴按最大面内分量识别，用原有10⁻¹⁰归一化几何容差识别浮点非主分量；不修改原始Sf或phi，压力/流量0.1%、守恒10⁻⁸和线性残差10⁻¹²等门槛不变。

为后续读取C02，加入C01/C02身份选择和输入身份一致检查，输出checker_version。只接受这两个指定的x驱动案例，不自动扩展到C03、斜向张量或其他网格。新旧差异见checker_1_1_release.diff；新版说明在CASE内common/CHECKER_CHANGELOG.md和checker_version.json。

用原C01已完成数据执行只读复核，原来的两端结果、4个跨端指标、原始输出哈希和PASS状态与前轮修正版逐项完全一致，共50个数值检查；没有重跑C01。证据C01_checker_1_1_regression.json和新CASE的reports/C01_existing_data_regression.json。

15项人造数据测试通过，涵盖原11项及浮点几何识别、真实倾斜拒绝、未准备案例拒绝、C02与C01输入身份混用拒绝。证据新CASE的reports/checker_tests.log/json；测试通过不是C02流动通过。

## 2. C02与C01的物理区别

两例均使用V2系数、24×48μm区域、125nm平均厚度、μ0.001Pa·s、16×32×1网格，x两端过压24Pa/0Pa、y不穿流。C01槽沿y，x驱动对应横槽；C02槽沿x，x驱动对应沿槽。K与D的x/y主值成对交换，其他物理输入和验收门槛不变。

|C02准备量|值|含义|
|---|---:|---|
|Kxx|1.0414014079511954×10⁻²²m³|V2沿槽导度|
|Kyy|4.5537951695675916×10⁻²³m³|V2横槽导度|
|Dxx|1.2003056558749922×10¹⁵m⁻²|H/Kxx，总阻力|
|Dyy|2.7449631646886185×10¹⁵m⁻²|H/Kyy，总阻力|
|解析预期Ux|8.331211263609563×10⁻⁷m/s|尚未求解|
|解析预期Qx|4.998726758165738×10⁻¹⁸m³/s|尚未求解|
|C02/C01解析Q比|2.286886803584717|压力驱动流量比，非挤压阻力比|

两例压力曲线预期相同，仅压力一致不足以检查槽向交换；未来应重点核对流量及由结果恢复的K。完整规格在CASE内common/C02_SPEC.md，精确输入与预期值在common/C02.json和C02_expected.json。没有拟合或扩大V2适用范围。

## 3. 程序复用与静态核对

求解器源码不需修改，C01和C02的512单元、固定x驱动、边界类型均在原实现支持范围内。本轮逐项验证两个C++源码、Make配置和二进制与原发布哈希一致后复制到新版本，绑定真实的原编译记录；**本轮没有重新编译，不能写成新增编译验证。**证据reports/solver_reuse.json、inherited_C01_preparation.json和inherited_C01_release_manifest.json。

五份网格文件逐字节复用；没有重新生成网格。在C02路径下重新运行checkMesh，结果Mesh OK；两端audit-only读取输入，OpenFOAM装配矩阵并确认对称、正对角、维度和512单元，矩阵最小对角项约2.53818×10⁻¹⁹，随后在调用solve之前退出。无压力迭代。

C02的Dxx/Dyy已从实际字典读取并与输入核对；体积约1.44×10⁻¹⁶m³，初始压力为0，K D/H恒等式、C01/C02主值交换和门槛一致性均已检查。证据新CASE的reports/preparation.json及三个静态命令日志。

新版准备包绑定48个文件、21个运行库，默认只读预检查通过。启动脚本仅显式执行参数才可能运行C02；本轮只调用默认模式。没有创建C02的runs目录、SDI_output或时间1场，也未创建tmux会话或交付启动命令。

## 4. 保留记录与当前停点

原C01目录94个文件逐一核对不变；前轮C01报告的已有产物亦核对不变。完整前后校验见preservation_before.json和preservation_after.json。原始checker的NOT_EVALUATED记录、前轮几何修正版及其PASS结论都保留，新版本只增加兼容记录，不覆盖历史失败或原始输出。

当前C02：source_prepared=true、compile_identity_verified=true（复用已编译程序）、mesh_checked=true、matrix_assembly_audit=true、run_completed=false、actual_run_id=null、NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=null、geometry_PASS=true（仅合成平均域）。预留planned_run_id=SDI_C02_v1_1_20261030_01只是名称，不是启动证据。没有独立人工验收或新物理验证。

C01既有静态接口诊断PASS保持；旧D4_N8_diag_v3_1_20261026_v1仍NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null。reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD与历史FAIL保持。

本轮没有运行/重跑C01或C02、拟合、改变科学阈值、推进其他Gate、提交推送或对外发送。下一停点为等待用户后续明确启动C02；按当前要求不提供执行命令、不自动启动。准备就绪与获准运行分别记录。

报告沿用已读scientific-writing技能的来源和状态组织，流程出处见[原协议入口](../Static_Darcy_interface_protocol_20261030/README.md)。本轮为AI准备及本地自动核对，不声称独立人工科学验收。
