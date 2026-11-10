# OpenFOAM对比方式与实际算例核对

日期：2026-11-04。范围：只读本地源码、协议、已有执行/验收记录与原始输出；新增本报告及核对脚本/回执。没有编译、调用OpenFOAM、网格工具、原检查器或其他求解器，没有新仿真run_id、重跑、授权或下一Gate。

## 结论及前轮更正

本项目已有实际OpenFOAM程序与已完成算例，不能再仅按10月29日远程仓库未确认的历史停点表述。10月30日C01—C04及GDI01已经运行并形成外部验收记录。本轮已读取这些记录、当前源码与协议，并核对保存原始文件哈希和流量；未重新执行全部验收，原接受状态来自原报告。

现有OpenFOAM角色是二维等效方向性总阻力模型的接口/程序核验，不是逐槽解析的独立物理参考。当前不需要为证明程序已接入而重复实现或重跑C01—C04/GDI01。FEniCSx是历史独立参考实现候选之一，并非已经替代OpenFOAM的路线决定。

## 1. 实际程序与路径

- 二维程序：`CASE/interface_static_darcy_v1/two_dimensional/darcy2d.cpp`，以K装配压力系统。
- OpenFOAM压力程序：`CASE/interface_static_darcy_v1/openfoam/application/depthAveragedDarcyFoam.C`，以D装配平均Darcy压力系统；C02—C04分别保存在v1_1、v1_2、v1_3隔离包。
- 模型子类：`CASE/groove_porosity_model_v1/src/grooveDarcy.C`，从几何和原公式/V2生成方向性阻力。
- OpenFOAM动量—压力宿主：`CASE/groove_darcy_static_v1/application/grooveDarcyStaticFoam.C`，通过标准porosityForce调用grooveDarcy，已有GDI01结果。

来源版本按已有执行日志/验收为OpenFOAM Foundation13。源码、已编译产物、实际运行和验收分别由不同证据支持；本轮未重新编译或证明升级/换机器后的可运行性。

共同物理定义为J=−(K/μ)∇p，U=J/H，D=H K⁻¹，且U=−(μD)⁻¹∇p。K单位m³，D单位m⁻²。该总阻力已包含未解析壁面作用，现有程序不再叠加厚度剪切或第二份Darcy阻力。

## 2. 已完成的具体问题

共同几何输入：平台间隙h=75nm、槽深d=100nm、槽宽120nm、周期240nm，占比1/2；平均液体厚度H=h+d/2=125nm。合成平均平面域24×48μm，16×32×1共512单元，z为empty，未逐槽解析。μ=0.001Pa·s，x端表压24/0Pa，y侧无通量，无闭合运动V=0。

|算例|系数及方向|实际run_id|OpenFOAM出口Q / m³·s⁻¹（约）|
|---|---|---|---:|
|C01|V2横槽，槽沿y、驱动+x|SDI_C01_v1_20261030_01|2.18582e-18|
|C02|V2沿槽，槽沿x、驱动+x|SDI_C02_v1_1_20261030_01|4.99873e-18|
|C03|原公式横槽，槽沿y、驱动+x|SDI_C03_v1_2_20261030_01|3.12872e-18|
|C04|原公式沿槽，槽沿x、驱动+x|SDI_C04_v1_3_20261030_01|1.15625e-17|
|GDI01|V2横槽，经grooveDarcy实际动量源接入|GDI01_v1_20261030_01|2.18582e-18|

四个SDI例各有二维/OpenFOAM两端，均有独立退出0和原外部验收；GDI01有真实OpenFOAM求解和外部验收。保存接受均为NUMERICAL_GATE=PASS、RESULT_PASS=true、geometry_PASS=true，但几何仅指synthetic_average_domain_only，physical_validation=NOT_EVALUATED，independent_human_acceptance=false。不能升级为真实沟槽或整个项目PASS。

C01最初检查器的严格零面积分量识别导致NOT_EVALUATED；报告目录的几何识别修正版才得到接受。本轮读取`interface_analysis_geometry_v1_1.json`，保留原失败/未评价记录。各包README的“未启动”属于准备快照，当前完成身份由execution.json和结果报告确定；未覆写原快照。

## 3. 比较结果怎样解释

- C01/C03：原公式与V2横槽输入影响；V2流量较原公式低约30.14%。
- C02/C04：原公式与V2沿槽输入影响；V2流量较原公式低约56.77%。
- C02/C01：V2沿槽/横槽静态流量比约2.28689。
- C04/C03：原公式沿槽/横槽静态流量比约3.69561。
- GDI01/C01：现场几何生成K/D后，经真实阻力源和压力—速度迭代，重现已接受的二维与旧OpenFOAM结果，证明该受限接入链一致。

这些比例是同一平均模型中输入系数的影响，不是独立测量出的真实沟槽方向比。固定压差、恒系数主轴问题的p(x)主要由边界确定，因此几组压力线重合不能用来证明哪组K准确。不要把本组h75/d100的输入比值与URV h60/d80的显式沟槽方向比2.51493混作同条件误差比较。

当前静态流阻为R_Q=Δp/Q（Pa·s/m³），不是挤压阻力R_sq=F_net/V（N·s/m）；本组V=0，后者不适用。

## 4. 明确后续对比方式

保留现有OpenFOAM等效方向性阻力实现，用它承担程序接口与应用输出实现核验；不强制将其改成逐槽求解器。公式准确性由不使用V2作为输入、且通过相应检查的显式沟槽参考判断。当前URV/OpenLB链是正在推进的候选参考，不因换或不换软件自动取得资格。

局部论文下一步仍按现行预声明路线完成S4/S5、参考资格及固定V2与原公式的正式同条件误差比较；本轮不改变其协议或权限。当前S4正式范围/资源审查已完成，但未采用/未授权启动，见`URV_S4_formal_scope_resource_review_20261104_090724/`；不是仍未做范围审查。

若保留挤压应用精度主张，再按已有`GDI01_results_20261030/CLOSURE_NEXT_STEP.md`准备瞬时挤压：统一h/H及闭合速度、四边环境压力、∂tH+div(HU)=0、净载荷口径、网格和资源；原公式/V2分别进入二维模型与OpenFOAM。此层目前仅有接口定义，`common/squeeze_interface.json`记录motion_implemented=false、continuity_implemented=false、simulation_authorized=false。不得把现有24/0Pa静态问题改称挤压验证，也不能把参考K输入同一平均模型当独立挤压参照。

真实逐槽挤压参考还须另定同条件边界与资源，不能直接假定与512单元平均网格同成本。应用与实验物理验证仍未完成；reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD及历史FAIL保持。

## 5. 本轮核对强度与可复查入口

`audit_saved_cases.py`仅使用Python标准库读取保存数据，不导入求解器/主检查器、不调用子进程：

- 读取5例正确身份的完成记录及原接受JSON；核对9个程序退出码和无超时。
- 对原接受绑定的69项原始文件逐项重算SHA256，并核对5份run_manifest哈希，均一致。
- 从每端cells/faces.csv直接复算512单元体积平均Ux和xHigh出口Q；9端共4608单元，完整数值见`case_results.csv`。
- 未重新执行50/51项完整验收、未重新复算全部物理/数值守卫、未重新核验当前动态库。原完整接受由10月30日报告支持；此次是身份、保存证据完整性和关键输出核对。

机器回执：`verification.json`。本报告流程采用scientific-writing技能组织证据，属于AI辅助内部核对，不冒充独立人工科学终审。

主要来源：`docs/reports/SDI_C01_results_20261030/REPORT.md`及其修正版接受；`SDI_C02_results_20261030/REPORT.md`、`SDI_C03_results_20261030/REPORT.md`、`SDI_C04_results_20261030/REPORT.md`；`GDI01_results_20261030/REPORT.md`、`CLOSURE_NEXT_STEP.md`；各CASE的共同协议、实际源码、execution.json及原始场/CSV。
